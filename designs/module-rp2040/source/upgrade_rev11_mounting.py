#!/usr/bin/env python3
"""Rebuild rev0.11 mounting from the frozen rev0.9 board, preserving routed copper.

No autorouting or electrical placement changes. Existing planes are refilled
around the new all-layer hardware keepouts. Run check_kicad.py after migration.
"""
import hashlib
import json
import math
from pathlib import Path

import pcbnew
from shapely import Point, LineString, box, unary_union

from archive_routing import archive
from check_rev08_migration import copper_record
from design import ROOT, REVISION, components, read_keys
from generate_kicad import add_mechanics, generate_schematic, prepare_dsn, write_footprints
from generate_mechanical import geometry
from mounting_interface import mounting_specs

BASELINE = ROOT/'source/baselines/rev0.9/Cleaver.kicad_pcb'
REPORTS = ROOT/f'manufacturing/rev{REVISION}/checks'


def electrical_footprints(board):
    return {
        fp.GetReference(): dict(
            uuid=fp.m_Uuid.AsString(), position=list(pcbnew.ToMM(fp.GetPosition())),
            angle=fp.GetOrientationDegrees(), value=fp.GetValue(),
            pads=[dict(number=pad.GetNumber(), net=pad.GetNetname(),
                       position=list(pcbnew.ToMM(pad.GetPosition())),
                       size=list(pcbnew.ToMM(pad.GetSize())),
                       drill=list(pcbnew.ToMM(pad.GetDrillSize()))) for pad in fp.Pads()])
        for fp in board.GetFootprints() if not (
            fp.GetReference().startswith('H') and fp.GetReference()[1:].isdigit())
    }


def mounting_clearances(board):
    """Conservative material envelopes; filled planes are handled by KiCad DRC."""
    copper, bodies = [], []
    for item in board.GetTracks():
        if item.GetClass() == 'PCB_VIA':
            shape = Point(*pcbnew.ToMM(item.GetPosition())).buffer(pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu))/2)
        else:
            shape = LineString([pcbnew.ToMM(item.GetStart()), pcbnew.ToMM(item.GetEnd())]).buffer(pcbnew.ToMM(item.GetWidth())/2)
        copper.append(shape)
    for fp in board.GetFootprints():
        if fp.GetReference().startswith('H') or fp.GetReference() == 'LOGO1':
            continue
        for pad in fp.Pads():
            bounds = pad.GetBoundingBox()
            copper.append(box(*pcbnew.ToMM(bounds.GetPosition()), *pcbnew.ToMM(bounds.GetEnd())))
        for graphic in fp.GraphicalItems():
            if graphic.GetClass() == 'PCB_SHAPE' and graphic.GetLayer() in (pcbnew.F_Fab, pcbnew.B_Fab, pcbnew.Edge_Cuts):
                bounds = graphic.GetBoundingBox()
                bodies.append(box(*pcbnew.ToMM(bounds.GetPosition()), *pcbnew.ToMM(bounds.GetEnd())))
    copper, bodies = unary_union(copper), unary_union(bodies)
    _, cuts, _ = geometry(top_capacitor_opening=False)
    openings = unary_union(cuts)
    result = []
    for spec in mounting_specs():
        point = Point(spec['x'], spec['y'])
        copper_distance = copper.distance(point)
        body_distance = bodies.distance(point)
        assert copper_distance > spec['reserve_radius_mm']+.1, spec
        assert body_distance > spec['reserve_radius_mm']+.1, spec
        assert openings.distance(point) > 3.8+.2, spec
        result.append(dict(**spec,
                           copper_to_hole_edge_mm=round(copper_distance-spec['drill_mm']/2, 4),
                           copper_to_hardware_keepout_mm=round(copper_distance-spec['reserve_radius_mm'], 4),
                           physical_body_to_keepout_mm=round(body_distance-spec['reserve_radius_mm'], 4),
                           plate_opening_to_root_mm=round(openings.distance(point)-3.8, 4)))
    return result


def main():
    assert REVISION == '0.11'
    project = ROOT/'Cleaver.kicad_pro'
    project_bytes = project.read_bytes()
    board = pcbnew.LoadBoard(str(BASELINE))
    assert board.GetTitleBlock().GetRevision() == '0.9'
    before_copper = {item.m_Uuid.AsString(): copper_record(item) for item in board.GetTracks()}
    before_footprints = electrical_footprints(board)
    checks = mounting_clearances(board)
    # Keep SWIG wrappers alive until serialization.
    removed = [fp for fp in board.GetFootprints() if fp.GetReference().startswith('H') and fp.GetReference()[1:].isdigit()]
    zones = [zone for zone in board.Zones() if zone.GetIsRuleArea()]
    assert len(removed) == len(zones) == 11
    for item in removed+zones:
        board.Remove(item)
    write_footprints()
    add_mechanics(board, include_fiducials=False)
    board.GetTitleBlock().SetRevision(REVISION)
    board.GetTitleBlock().SetDate('2026-11-15')
    board.GetTitleBlock().SetTitle('Cleaver - removable PCB/plate cartridge / replaceable USB bezel')
    for text in board.GetDrawings():
        if text.GetClass() == 'PCB_TEXT' and text.GetText().startswith('CLEAVER rev0.9'):
            text.SetText(f'CLEAVER rev{REVISION} | SOCKETED RP2040-PLUS')
    keys, leds = read_keys()
    generate_schematic(components(keys, leds), keys, leds)
    target = ROOT/'Cleaver.kicad_pcb'
    pcbnew.SaveBoard(str(target), board)
    project.write_bytes(project_bytes)
    # Reload under the active project's fabrication/netclass settings.
    source_board = board
    board = pcbnew.LoadBoard(str(target))
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(target), board)
    project.write_bytes(project_bytes)
    assert before_copper == {item.m_Uuid.AsString(): copper_record(item) for item in board.GetTracks()}
    assert before_footprints == electrical_footprints(board)
    archive(board, ROOT/'routing/Cleaver.ses')
    assert pcbnew.ExportSpecctraDSN(board, str(ROOT/'routing/Cleaver.dsn'))
    prepare_dsn(ROOT/'routing/Cleaver.dsn')
    REPORTS.mkdir(parents=True, exist_ok=True)
    report = dict(revision=REVISION, baseline='source/baselines/rev0.9/Cleaver.kicad_pcb',
                  baseline_sha256=hashlib.sha256(BASELINE.read_bytes()).hexdigest(),
                  pcb_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
                  old_mounts_removed=11, pass_through_holes=12, pcb_attachment_holes=12,
                  unchanged_tracks_and_vias=len(before_copper),
                  unchanged_electrical_and_artwork_footprints=len(before_footprints),
                  unchanged_project_settings=True, site_clearances=checks)
    (REPORTS/'mounting-migration.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'Rev0.11: 12 x 7 mm pass-through holes + 12 x 2.2 mm PCB attachment holes; {len(before_copper)} copper items preserved.')


if __name__ == '__main__':
    main()
