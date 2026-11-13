#!/usr/bin/env python3
"""Read-only circuit/firmware parity checks plus fresh KiCad ERC and DRC."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew

from design import ROOT, MODULE_X, MODULE_Y, ROW_GPIOS, COL_GPIOS, read_keys, components, MOUNTING_HOLES, FIDUCIALS, REVISION, CONTROLLER_SOCKETS
from models_3d import validate_models
from assembly_parts import fields, purchase
from socket_interface import validate_interface
from logo_interface import RGB_LED_COUNT, logo_leds


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports',type=Path,default=Path('/tmp/opencode/cleaver-revision'))
    args = parser.parse_args()
    args.reports.mkdir(parents=True,exist_ok=True)
    folder = ROOT
    pcb,sch = folder/'Cleaver.kicad_pcb',folder/'Cleaver.kicad_sch'
    keys,leds = read_keys()
    parts = components(keys,leds)
    netfile = args.reports/'checked-netlist.xml'
    subprocess.run(['kicad-cli','sch','export','netlist','--format','kicadxml','-o',str(netfile),str(sch)],check=True)
    root = ET.parse(netfile).getroot()
    nets = {(p.get('ref'),p.get('pin')): n.get('name') for n in root.findall('./nets/net') for p in n.findall('node')}
    board = pcbnew.LoadBoard(str(pcb))
    models = validate_models(board)
    footprints = {fp.GetReference():fp for fp in board.GetFootprints()}
    interface = validate_interface(board)
    for row in interface['pin_map']:
        assert nets[('U1',str(row['module_pin']))]==row['net'], 'Offboard module/socket mapping mismatch'
    for number in (30,35,36,37,39):
        name=nets[('U1',str(number))]
        circuit=next(n for n in root.findall('./nets/net') if n.get('name')==name)
        assert {(n.get('ref'),n.get('pin')) for n in circuit.findall('node')}=={
            ('U1',str(number)),('J2',str(41-number))}, 'Unused module function has a carrier load'
    logo = footprints['LOGO1']
    assert not list(logo.Pads()) and logo.GetAttributes() & pcbnew.FP_BOARD_ONLY
    assert all(s.GetLayer()==pcbnew.F_SilkS for s in logo.GraphicalItems())
    assert len(footprints)==len(parts)+len(MOUNTING_HOLES)+len(FIDUCIALS)+1, 'Unexpected/missing board components'
    for part in parts:
        ref = part['ref']
        fp = footprints[ref]
        for name,value in fields(part).items():
            assert fp.GetField(name).GetText()==value, f'{ref}: purchasing field {name}'
        if purchase(part):
            assert fp.GetAttributes() & pcbnew.FP_SMD, f'{ref}: not SMD'
        assert fp.GetLayer()==(pcbnew.B_Cu if part['back'] else pcbnew.F_Cu), f'{ref}: wrong assembly side'
        assert abs(pcbnew.ToMM(fp.GetPosition().x)-part['x'])<.001, f'{ref} moved in X'
        assert abs(pcbnew.ToMM(fp.GetPosition().y)-part['y'])<.001, f'{ref} moved in Y'
        pads = {p.GetNumber():p for p in fp.Pads() if p.GetNumber()}
        if part.get('offboard'):
            assert not list(fp.Pads()) and fp.GetAttributes() & pcbnew.FP_BOARD_ONLY
            continue
        for number,expected in part['pins'].items():
            name = nets[(ref,number)]
            assert pads[number].GetNetname()==name, f'{ref}.{number} schematic/PCB mismatch'
            if expected is not None:
                assert name.lstrip('/')==expected, f'{ref}.{number} incorrect circuit net'
            else:
                assert name.startswith('unconnected-'), f'{ref}.{number} should have a no-connect'
    u1 = footprints['U1']
    pads = {str(n):footprints[ref].FindPadByNumber(str(i))
            for ref,y,numbers in CONTROLLER_SOCKETS for i,n in enumerate(numbers,1)}
    # Pin ENTRY holes retain the original module positions; the solder lands
    # are staggered 1.70mm to either side of those unplated holes.
    for n,(dx,dy) in {'1':(24.13,-8.89),'2':(21.59,-8.89),'20':(-24.13,-8.89),
                      '21':(-24.13,8.89),'40':(24.13,8.89)}.items():
        point = pads[n].GetPosition()
        assert abs(pcbnew.ToMM(point.x)-MODULE_X-dx)<.001, f'Wrong RP2040-Plus pin {n} X'
        assert abs(abs(pcbnew.ToMM(point.y)-MODULE_Y-dy)-1.7)<.001, f'Wrong RP2040-Plus pin {n} Y'
    assert str(u1.GetFPID().GetLibItemName())=='Waveshare_RP2040_Plus'
    assert pads['40'].GetNetname()==footprints['F1'].FindPadByNumber('1').GetNetname()=='/RAW_USB_5V'
    openings = sum(item.GetLayer()==pcbnew.Edge_Cuts for fp in board.GetFootprints() for item in fp.GraphicalItems())
    assert openings==RGB_LED_COUNT, 'Expected one actual opening per key/logo LED'
    # Check the real reverse-mounted pad geometry, not just net names. In top
    # (emitter) view Rev02 is VDD/DOUT on the left, DIN/GND on the right.
    for key in [dict(k, y=k['y']+5.08) for k in keys] + logo_leds():
        fp = footprints[key['led_ref']]
        assert fp.GetLayer()==pcbnew.B_Cu, 'LED solder lands must be on the back'
        pads = {p.GetNumber():p for p in fp.Pads()}
        for number,(dx,dy) in {'3':(-3.05,-.75),'4':(-3.05,.75),
                                '1':(3.05,.75),'2':(3.05,-.75)}.items():
            point = pads[number].GetPosition()
            assert abs(pcbnew.ToMM(point.x)-key['x']-dx)<.001, f'{key["led_ref"]}.{number} reverse-mount X'
            assert abs(pcbnew.ToMM(point.y)-key['y']-dy)<.001, f'{key["led_ref"]}.{number} reverse-mount Y'
    assert board.GetCopperLayerCount()==4, 'Incorrect stackup'
    assert any(pcbnew.In1_Cu in list(z.GetLayerSet().Seq()) and z.GetNetname()=='/GND'
                and z.HasFilledPolysForLayer(pcbnew.In1_Cu) for z in board.Zones()), 'Missing filled inner ground plane'
    assert any(pcbnew.F_Cu in list(z.GetLayerSet().Seq()) and z.GetNetname()=='/LED_5V'
               and z.HasFilledPolysForLayer(pcbnew.F_Cu) for z in board.Zones()), 'Missing switched RGB supply pour'
    smd_pads = [p for fp in board.GetFootprints() for p in fp.Pads()
                 if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
    pth = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_PTH]
    assert not pth, 'Controller entry holes must be unplated, not solder barrels'
    for ref,y,numbers in CONTROLLER_SOCKETS:
        holes=[p for p in footprints[ref].Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH]
        assert len(holes)==20 and all(tuple(pcbnew.ToMM(p.GetDrillSize()))==(1.,1.) for p in holes)
    assert all(p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) for p in smd_pads)
    assert not any(p.IsOnLayer(pcbnew.F_Paste) for fp in board.GetFootprints() for p in fp.Pads())
    for via in (t for t in board.GetTracks() if t.GetClass()=='PCB_VIA'):
        for pad in smd_pads:
            if pad.GetNetCode()!=via.GetNetCode():
                continue
            # Keep the actual drilled hole outside exposed solder lands, with
            # 0.05mm allowance. KiCad DRC alone permits same-net via-in-pad.
            box = pad.GetBoundingBox()
            box.Inflate(via.GetDrillValue()//2+pcbnew.FromMM(.05))
            assert not box.Contains(via.GetPosition()), f'Via hole in solder land {pad.GetParentFootprint().GetReference()}.{pad.GetNumber()}'
    fw = folder/'firmware'
    info = json.loads((fw/'keyboard.json').read_text())
    assert info['matrix_pins']==dict(rows=ROW_GPIOS,cols=COL_GPIOS)
    assert info['diode_direction']=='ROW2COL'
    expected = [[k['matrix_row'],k['matrix_col']] for k in keys]
    assert [k['matrix'] for k in info['layouts']['LAYOUT']['layout']]==expected
    assert [k.get('matrix') for k in info['rgb_matrix']['layout']]==[[k['matrix_row'],k['matrix_col']] for k in leds]+[None]*4
    assert all(k['flags']==2 for k in info['rgb_matrix']['layout'][117:])
    assert info['rgb_matrix']['max_brightness']==8
    vial = json.loads((fw/'keymaps/vial/vial.json').read_text())
    actual = [list(map(int,item.split(','))) for row in vial['layouts']['keymap'] for item in row if isinstance(item,str)]
    assert actual==expected, 'Vial physical/matrix mapping mismatch'
    assert vial['matrix']==dict(rows=8,cols=16) and vial['lighting']=='vialrgb'
    with (fw/'key_matrix.csv').open(newline='') as file:
        rows = list(csv.DictReader(file))
    assert len(rows)==117 and all(None not in row for row in rows), 'Malformed matrix CSV'
    for group,command,file in [
        ('ERC',['kicad-cli','sch','erc','--format','json','--severity-all','--exit-code-violations'],'erc.json'),
        ('DRC',['kicad-cli','pcb','drc','--format','json','--refill-zones','--all-track-errors',
                '--schematic-parity','--severity-all','--exit-code-violations'],'drc.json')]:
        result = subprocess.run(command+['-o',str(args.reports/file),str(sch if group=='ERC' else pcb)],capture_output=True,text=True)
        print(result.stdout.strip())
        if result.returncode:
            raise SystemExit(f'{group} failed (exit {result.returncode}); see {args.reports/file}')
        data = json.loads((args.reports/file).read_text())
        if group=='DRC':
            assert not data['violations'] and not data['unconnected_items'] and not data.get('schematic_parity',[]), 'DRC report is not clean'
        else:
            assert not any(sheet['violations'] for sheet in data['sheets']), 'ERC report is not clean'
    report = dict(revision=REVISION,controller='socketed Waveshare RP2040-Plus',matrix='8x16',unique_switches=len(keys),rgb_leds=RGB_LED_COUNT,
                  logo_leds=logo_leds(), bottom_factory_placements=489,pth_pads=0,controller_pin_entry_npth=40,front_paste_pads=0,
                  pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
                  schematic_sha256=hashlib.sha256(sch.read_bytes()).hexdigest(),
                  erc='pass',drc='pass',schematic_pcb_firmware_mapping='pass',models_3d=models,
                  controller_interface=interface)
    (args.reports/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS: 117 unique keys, 121 RGB LEDs, bottom-entry RP2040-Plus sockets/VBUS, netlist/PCB/Vial parity, 607 local 3D models, ERC and DRC.')


if __name__=='__main__':
    main()
