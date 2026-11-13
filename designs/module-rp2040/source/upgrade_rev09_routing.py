#!/usr/bin/env python3
"""Resize the rev0.8 badge, retaining all pre-badge routed copper by UUID.

Pass explicit rev0.8 and rev0.7 PCB backups. Only the eight badge components,
H9 and badge routing move. Normal regeneration uses the new complete SES.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew

from check_rev08_migration import copper_record
from design import ROOT, REVISION, MOUNTING_HOLES, components, read_keys
from generate_kicad import generate_firmware, generate_schematic, mm, write_bom
from logo_interface import logo_leds
from upgrade_rev07_routing import escape


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('key_routing_baseline', type=Path)
    parser.add_argument('--reports', type=Path, default=ROOT/'manufacturing/rev0.9/checks')
    args = parser.parse_args()
    project = ROOT/'Cleaver.kicad_pro'
    project_bytes = project.read_bytes()
    board = pcbnew.LoadBoard(str(args.baseline))
    original = pcbnew.LoadBoard(str(args.key_routing_baseline))
    assert board.GetTitleBlock().GetRevision() == '0.8' and REVISION == '0.9'
    assert original.GetTitleBlock().GetRevision() == '0.7'
    original_copper = {t.m_Uuid.AsString(): copper_record(t) for t in original.GetTracks()}
    current = {t.m_Uuid.AsString(): copper_record(t) for t in board.GetTracks()}
    assert all(current.get(uid) == record for uid, record in original_copper.items())
    removed = 0
    # Keep SWIG wrappers alive until the board has been serialized/reloaded.
    tracks = list(board.GetTracks())
    for track in tracks:
        if track.m_Uuid.AsString() not in original_copper:
            board.Remove(track)
            removed += 1
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    before = {ref: tuple(pcbnew.ToMM(fp.GetPosition())) for ref, fp in fps.items()}
    moved = []
    for led in logo_leds():
        for ref, position in [(led['led_ref'], (led['x'], led['y'])),
                              (led['cap_ref'], (led['cap_x'], led['cap_y']))]:
            fps[ref].SetPosition(mm(*position))
            moved.append(ref)
    old = fps['H9'].GetPosition()
    delta = mm(*MOUNTING_HOLES[8])-old
    keepouts = [z for z in board.Zones() if z.GetIsRuleArea() and z.GetBoundingBox().Contains(old)]
    assert len(keepouts) == 1
    keepouts[0].Move(delta)
    fps['H9'].Move(delta)
    moved.append('H9')
    board.GetTitleBlock().SetRevision(REVISION)
    board.GetTitleBlock().SetTitle('Cleaver - socketed RP2040-Plus / 2 x 1 inch RGB badge')
    for drawing in board.GetDrawings():
        if drawing.GetClass() == 'PCB_TEXT' and drawing.GetText().startswith('CLEAVER rev0.8'):
            drawing.SetText(f'CLEAVER rev{REVISION} | SOCKETED RP2040-PLUS')
    keys, leds = read_keys()
    parts = components(keys, leds)
    generate_schematic(parts, keys, leds)
    generate_firmware(keys, leds)
    write_bom(parts)
    pcb = ROOT/'Cleaver.kicad_pcb'
    pcbnew.SaveBoard(str(pcb), board)
    # Loading a differently named backup can rename top-level sheet metadata.
    project.write_bytes(project_bytes)
    placed_board = board
    board = pcbnew.LoadBoard(str(pcb))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    for led in logo_leds():
        print('Power fanout', led['led_ref'], flush=True)
        for ref, numbers in [(led['led_ref'], ('1', '3')), (led['cap_ref'], ('1', '2'))]:
            for number in numbers:
                escape(board, fps[ref].FindPadByNumber(number), None, pcbnew.F_Cu, .3)
    previous = fps[leds[-1]['led_ref']].FindPadByNumber('4')
    for led in logo_leds():
        fp = fps[led['led_ref']]
        print('Route', led['led_ref'], flush=True)
        escape(board, fp.FindPadByNumber('2'), tuple(pcbnew.ToMM(previous.GetPosition())), pcbnew.B_Cu, .3)
        previous = fp.FindPadByNumber('4')
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(pcb), board)
    project.write_bytes(project_bytes)
    after = {t.m_Uuid.AsString(): copper_record(t) for t in board.GetTracks()}
    assert all(after.get(uid) == record for uid, record in original_copper.items())
    assert all(tuple(pcbnew.ToMM(fp.GetPosition())) == before[ref] for ref, fp in fps.items() if ref not in moved)
    args.reports.mkdir(parents=True, exist_ok=True)
    result = dict(revision=REVISION, baseline_revision='0.8',
                  baseline_pcb_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                  key_routing_baseline_sha256=hashlib.sha256(args.key_routing_baseline.read_bytes()).hexdigest(),
                  pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
                  retained_pre_badge_copper_items=len(original_copper), removed_old_badge_copper_items=removed,
                  added_badge_copper_items=len(after)-len(original_copper),
                  unchanged_footprint_positions=len(fps)-len(moved),
                  moved_positions={ref: dict(before_mm=before[ref], after_mm=pcbnew.ToMM(fps[ref].GetPosition())) for ref in moved})
    (args.reports/'migration.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
