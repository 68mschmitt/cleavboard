#!/usr/bin/env python3
"""One-time rev0.7 -> rev0.8 badge migration; keep existing routed copper.

Normal regeneration imports routing/Cleaver.ses. This tool takes an explicit
rev0.7 backup, adds the four logo pixels, moves H9 and routes their new nets.
Run check_kicad.py before archiving/exporting the result.
"""
import argparse
from pathlib import Path

import pcbnew

from assembly_parts import fields
from design import ROOT, REVISION, MOUNTING_HOLES, components, read_keys
from generate_kicad import (FP_NAMES, generate_schematic, ident, mm,
                           schematic_nets, write_footprints)
from logo_interface import logo_leds
from upgrade_rev07_routing import escape


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--reports', type=Path, default=Path('/tmp/opencode/cleaver-rev08'))
    args = parser.parse_args()
    args.reports.mkdir(parents=True, exist_ok=True)
    assert args.baseline.resolve() != (ROOT/'Cleaver.kicad_pcb').resolve()
    board = pcbnew.LoadBoard(str(args.baseline))
    assert board.GetTitleBlock().GetRevision() == '0.7'
    keys, leds = read_keys()
    parts = components(keys, leds)
    write_footprints()
    generate_schematic(parts, keys, leds)
    nets = schematic_nets(args.reports)
    netmap = {n.GetNetname(): n for n in board.GetNetInfo().NetsByNetcode().values()}
    for name in sorted(set(nets.values())-set(netmap)):
        net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(net)
        netmap[name] = net
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for part in parts:
        ref = part['ref']
        if ref not in fps:
            fp = pcbnew.FootprintLoad(str(ROOT/'Cleaver.pretty'), part['kind'])
            fp.SetFPID(pcbnew.LIB_ID('Cleaver', FP_NAMES.get(part['kind'], part['kind'])))
            fp.SetReference(ref)
            fp.SetValue(part['value'])
            fp.SetPath(pcbnew.KIID_PATH('/'+ident(ref)))
            fp.SetPosition(mm(part['x'], part['y']))
            board.Add(fp)
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
            fp.Reference().SetVisible(False)
            fp.Value().SetVisible(False)
            for name, value in fields(part).items():
                fp.SetField(name, value)
                fp.GetField(name).SetVisible(False)
            fps[ref] = fp
        for pad in fps[ref].Pads():
            if pad.GetNumber():
                pad.SetNet(netmap[nets[(ref, pad.GetNumber())]])
    # Only this one mounting axis changes, including its all-layer keepout.
    old = fps['H9'].GetPosition()
    delta = mm(*MOUNTING_HOLES[8])-old
    keepouts = [z for z in board.Zones() if z.GetIsRuleArea()
                and z.GetBoundingBox().Contains(old)]
    assert len(keepouts) == 1
    keepouts[0].Move(delta)
    fps['H9'].Move(delta)
    board.GetTitleBlock().SetRevision(REVISION)
    board.GetTitleBlock().SetTitle('Cleaver - socketed RP2040-Plus / RGB badge')
    for item in board.GetDrawings():
        if item.GetClass() == 'PCB_TEXT' and item.GetText().startswith('CLEAVER rev0.7'):
            item.SetText(f'CLEAVER rev{REVISION} | SOCKETED RP2040-PLUS')
    # Reload under the active project to use its actual fabrication rules.
    pcbnew.SaveBoard(str(ROOT/'Cleaver.kicad_pcb'), board)
    board = pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for led in logo_leds():
        print('Power fanout', led['led_ref'], flush=True)
        for ref, numbers in [(led['led_ref'], ('1', '3')), (led['cap_ref'], ('1', '2'))]:
            for number in numbers:
                # Forces a real through-via: GND reaches In1.Cu and LED_5V F.Cu.
                escape(board, fps[ref].FindPadByNumber(number), None, pcbnew.F_Cu, .3)
    previous = fps[leds[-1]['led_ref']].FindPadByNumber('4')
    for led in logo_leds():
        fp = fps[led['led_ref']]
        print('Route', led['led_ref'], flush=True)
        escape(board, fp.FindPadByNumber('2'), tuple(pcbnew.ToMM(previous.GetPosition())), pcbnew.B_Cu, .3)
        previous = fp.FindPadByNumber('4')
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(ROOT/'Cleaver.kicad_pcb'), board)


if __name__ == '__main__':
    main()
