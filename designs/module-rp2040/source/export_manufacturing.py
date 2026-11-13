#!/usr/bin/env python3
"""Export revision-specific fabrication and underside-assembly deliverables.

Runs the integration checker first. Output origins are lower-left, +X right
and +Y up, top view. Manifest paths are relative to the design directory.
"""
import csv
import hashlib
import json
import subprocess
import sys
import zipfile
from collections import defaultdict
from html import escape
from pathlib import Path
import pcbnew
from design import ROOT, BOARD_W, BOARD_H, MOUNTING_HOLES, FIDUCIALS, components, read_keys, REVISION
from assembly_parts import purchase
from socket_interface import write_outputs as write_interface

OUT = ROOT/f'manufacturing/rev{REVISION}'
# JLCPCB catalog zero-angle corrections from placement review. Positive offsets
# are counterclockwise. These affect the CPL only, never PCB/pad geometry.
JLC_ROTATION_OFFSETS = {'SN74LV1T125DBVR':90, 'CPG151101S11-16':180}


def write_csv(path, header, rows):
    with path.open('w',newline='') as file:
        writer=csv.writer(file,lineterminator='\n');writer.writerow(header);writer.writerows(rows)


def assembly_rows(board):
    footprints={fp.GetReference():fp for fp in board.GetFootprints()}
    groups=defaultdict(list);placements=[];pad_rows=[]
    for part in components(*read_keys()):
        identity=purchase(part)
        if identity is None:continue
        ref=part['ref'];fp=footprints[ref]
        pads=[p for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
        assert pads and all(p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) for p in pads), ref
        groups[identity].append(ref)
        # The MX footprint origin is the SWITCH, not the socket body. The
        # midpoint between the two socket solder lands is its placement centre.
        if part['kind']=='MX':
            x=sum(pcbnew.ToMM(p.GetPosition().x) for p in pads)/2
            y=sum(pcbnew.ToMM(p.GetPosition().y) for p in pads)/2
        else:
            x,y=pcbnew.ToMM(fp.GetPosition())
        rotation=(fp.GetOrientationDegrees()+JLC_ROTATION_OFFSETS.get(identity[1],0))%360
        placements.append([ref,f'{x:.6f}',f'{BOARD_H-y:.6f}','bottom',f'{rotation:.3f}'])
        for pad in pads:
            px,py=pcbnew.ToMM(pad.GetPosition())
            pad_rows.append([ref,pad.GetNumber(),pad.GetNetname(),f'{px:.6f}',f'{BOARD_H-py:.6f}',
                             f'{px-x:.6f}',f'{y-py:.6f}'])
    assert len(placements)==489
    return groups,placements,pad_rows


def drawing(board):
    # Bottom view, mirrored horizontally; labels are readable from the bottom.
    body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{BOARD_W}mm" height="{BOARD_H}mm" viewBox="0 0 {BOARD_W} {BOARD_H}">',
          f'<rect x="0" y="0" width="{BOARD_W}" height="{BOARD_H}" fill="#fafafa" stroke="black" stroke-width=".1"/>']
    for fp in board.GetFootprints():
        ref=fp.GetReference();x,y=pcbnew.ToMM(fp.GetPosition())
        for pad in fp.Pads():
            if not pad.IsOnLayer(pcbnew.B_Cu):continue
            px,py=pcbnew.ToMM(pad.GetPosition());w,h=pcbnew.ToMM(pad.GetSize())
            px=BOARD_W-px
            color='#cf9d36' if pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD else '#dddddd'
            title=escape(f'{ref}.{pad.GetNumber()} {pad.GetNetname()}')
            body.append(f'<rect x="{px-w/2}" y="{py-h/2}" width="{w}" height="{h}" fill="{color}" stroke="#444" stroke-width=".06"><title>{title}</title></rect>')
        if ref.startswith('SW'):y-=3.81;x-=.635
        if ref.startswith('LED'):
            body.append(f'<rect x="{BOARD_W-x-1.8}" y="{y-1.6}" width="3.6" height="3.2" fill="white" stroke="#d33" stroke-width=".1"/>')
        body.append(f'<text x="{BOARD_W-x}" y="{y-.9}" font-size=".7" text-anchor="middle" fill="#17284a">{escape(ref)}</text>')
    body.append('</svg>')
    return '\n'.join(body)+'\n'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reports=OUT/'checks'
    subprocess.run([sys.executable,'-B',str(ROOT/'source/check_kicad.py'),'--reports',str(reports)],check=True)
    pcb=ROOT/'Cleaver.kicad_pcb';board=pcbnew.LoadBoard(str(pcb))
    assert pcbnew.ToMM(board.GetDesignSettings().GetAuxOrigin())==(0.0,BOARD_H)
    groups,placements,pads=assembly_rows(board)
    write_interface(board,OUT)
    rows=[]
    for (manufacturer,mpn,code,package),refs in groups.items():
        rows.append([mpn,','.join(refs),package,code,manufacturer,len(refs)])
    write_csv(OUT/'BOM-JLCPCB.csv',['Comment','Designator','Footprint','LCSC Part #','Manufacturer','Quantity'],rows)
    write_csv(OUT/'CPL-JLCPCB.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],placements)
    write_csv(OUT/'pad-orientation-reference.csv',['Designator','Pad','Net','X_mm','Y_mm','DX_from_centroid_mm','DY_from_centroid_mm'],pads)
    write_csv(OUT/'fiducials.csv',['Designator','X_mm','Y_mm','Side','Copper_diameter_mm','Mask_opening_mm'],
              [[f'FID{i}',x,BOARD_H-y,'bottom',1,3] for i,(x,y) in enumerate(FIDUCIALS,1)])
    write_csv(OUT/'mounting-holes.csv', ['reference','pcb_x_mm','pcb_y_mm','drill_mm','reserved_diameter_mm'],
              [[f'H{i}',x,y,2.2,6] for i,(x,y) in enumerate(MOUNTING_HOLES,1)])
    write_csv(OUT/'user-installed.csv',['Item','Quantity','Mounting','Description'],[
        ['U1',1,'top plug-in','Waveshare RP2040-Plus 4MB USB-C bare module SKU 20290; pre-headered 20808 NOT qualified'],
        ['U1 headers',2,'solder to module ONLY','Samtec TSW-120-14-G-S; 8.13mm gold posts DOWN, 2.79mm tails through module; 17.78mm row spacing'],
        ['MX switches',117,'top','Plate-mounted MX-compatible switches'],
        ['2u stabilizers',7,'plate','Cherry-style plate mount, 23.8mm stem spacing'],
        ['6.25u stabilizer',1,'plate','Cherry-style plate mount, 100mm stem spacing'],
        ['Mounting screws',len(MOUNTING_HOLES),'case/plate','M2; choose lengths for your printed case; 6mm reserved diameter'],
        ['Logo light well',1,'plate opening',f'Opaque print; mechanical/rev{REVISION}/case/Logo-light-well.stl'],
        ['Logo insert',1,'captured beneath cover','Translucent print or custom two-color badge; 50.8x25.4mm body / 53.8x28.4mm flange']])
    (OUT/'assembly-bottom.svg').write_text(drawing(board))
    fab=OUT/'fabrication';fab.mkdir(exist_ok=True)
    subprocess.run(['kicad-cli','pcb','export','gerbers','--use-drill-file-origin','--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts',
        '-o',str(fab)+'/',str(pcb)],check=True)
    subprocess.run(['kicad-cli','pcb','export','drill','--drill-origin','plot','--excellon-separate-th',
        '--generate-map','--map-format','pdf','--generate-report','-o',str(fab)+'/',str(pcb)],check=True)
    with zipfile.ZipFile(OUT/f'Cleaver-rev{REVISION}-fabrication.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(fab.iterdir()):z.write(path,path.name)
    inputs=[pcb,ROOT/'Cleaver.kicad_sch',ROOT/'Cleaver.kicad_pro',ROOT/'routing/Cleaver.ses',
            ROOT/'VALIDATION.md',ROOT/'README.md',ROOT/'LOGO.md',ROOT/'routing/README.md',
            ROOT/'manufacturing/BOM.csv', *sorted((ROOT/'firmware').rglob('*')),
            ROOT/'Cleaver.pretty/Harwin_M20_7862042.kicad_mod',ROOT/'Cleaver.pretty/Waveshare_RP2040_Plus.kicad_mod',
            ROOT/'references/CONTROLLER-SOCKETS-0.7.md',ROOT/'references/Harwin-M20-786.pdf',
            ROOT/'references/Samtec-TSW.pdf',ROOT/'references/JLCPCB-2026-11-12.json',
            ROOT/'references/JLCPCB-2026-11-10.json',ROOT/'references/COMPONENT-REVIEW.md',
            ROOT/'Cleaver.3dshapes/generated-rev07.json',
            *sorted((ROOT/'source').glob('*.py')),
            *sorted((ROOT/f'mechanical/rev{REVISION}').rglob('*'))]
    for name in ('Harwin_M20_7862042','Waveshare_RP2040_Plus_Socketed'):
        inputs += [ROOT/'Cleaver.3dshapes'/f'{name}.{suffix}' for suffix in ('wrl','step')]
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [*inputs,
                         *sorted(OUT.rglob('*'))] if p.is_file() and p.name!='SHA256.json'}
    (OUT/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Exported 489 bottom placements, 14 purchasing groups, fabrication/drill files and manifest.')


if __name__=='__main__':main()
