#!/usr/bin/env python3
"""Independently compare the rev0.7 carrier with its frozen rev0.6 input."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

import pcbnew
from shapely import LineString, Point, box, unary_union

from design import ROOT


def pad_record(p):
    return (p.GetNumber(),p.GetAttribute(),p.GetShape(),tuple(pcbnew.ToMM(p.GetPosition())),
            tuple(pcbnew.ToMM(p.GetSize())),tuple(pcbnew.ToMM(p.GetDrillSize())),
            p.GetNetname(),tuple(p.GetLayerSet().Seq()))


def copper(board):
    groups=defaultdict(list)
    for item in board.GetTracks():
        if item.GetClass()=='PCB_VIA':
            key=(item.GetNetname(),'via',item.GetWidth(pcbnew.F_Cu),item.GetDrillValue())
            shape=Point(tuple(pcbnew.ToMM(item.GetPosition())))
        else:
            key=(item.GetNetname(),board.GetLayerName(item.GetLayer()),item.GetWidth())
            shape=LineString([tuple(pcbnew.ToMM(item.GetStart())),tuple(pcbnew.ToMM(item.GetEnd()))])
        groups[key].append(shape)
    return {key:unary_union(shapes) for key,shapes in groups.items()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline',type=Path)
    parser.add_argument('--output',type=Path,default=ROOT/'manufacturing/rev0.7/checks/migration.json')
    args=parser.parse_args()
    old=pcbnew.LoadBoard(str(args.baseline));new=pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
    baseline_project=args.baseline.with_suffix('.kicad_pro')
    assert baseline_project.is_file(), 'Provide the frozen project rules beside the baseline PCB'
    assert json.loads(baseline_project.read_text())==json.loads((ROOT/'Cleaver.kicad_pro').read_text()), 'Project rules/settings changed'
    assert old.GetTitleBlock().GetRevision()=='0.6' and new.GetTitleBlock().GetRevision()=='0.7'
    before={f.GetReference():f for f in old.GetFootprints()};after={f.GetReference():f for f in new.GetFootprints()}
    assert set(after)-set(before)=={'J1','J2'} and not set(before)-set(after)
    for ref,fp in before.items():
        if ref=='U1':continue
        other=after[ref]
        assert fp.m_Uuid.AsString()==other.m_Uuid.AsString(), (ref,'footprint identity changed')
        assert sorted(pad_record(p) for p in fp.Pads())==sorted(pad_record(p) for p in other.Pads()), (ref,'pads/nets changed')
        assert fp.GetValue()==other.GetValue(),ref
        assert fp.GetFPID().GetLibItemName()==other.GetFPID().GetLibItemName(),ref
        assert fp.GetFPID().GetLibNickname()==other.GetFPID().GetLibNickname(),ref
        assert tuple(pcbnew.ToMM(fp.GetPosition()))==tuple(pcbnew.ToMM(other.GetPosition())),ref
    # No trace/via additions, removals or width changes outside the controller
    # adaptation area. Compare unions, not UUIDs or arbitrary segment splits.
    region=box(398,0,452.4375,29)
    a,b=copper(old),copper(new)
    for key in set(a)|set(b):
        left=a.get(key,Point()).difference(region)
        right=b.get(key,Point()).difference(region)
        if key[1]=='via':
            assert left.difference(right.buffer(.0002)).is_empty and right.difference(left.buffer(.0002)).is_empty, (key,'via changed outside controller')
            continue
        assert left.difference(right.buffer(.0002)).is_empty or left.difference(right.buffer(.0002)).length<.0002, (key,'copper removed outside controller')
        assert right.difference(left.buffer(.0002)).is_empty or right.difference(left.buffer(.0002)).length<.0002, (key,'copper added outside controller')
    original_ids={t.m_Uuid.AsString() for t in old.GetTracks()}
    retained=sum(t.m_Uuid.AsString() in original_ids for t in new.GetTracks())
    result=dict(baseline_revision='0.6',revision='0.7',
                baseline_pcb_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                pcb_sha256=hashlib.sha256((ROOT/'Cleaver.kicad_pcb').read_bytes()).hexdigest(),
                unchanged_noncontroller_footprints=len(before)-1,new_factory_references=['J1','J2'],
                project_settings_rules_and_exclusions_unchanged=True,
                retained_copper_item_identities=retained,
                tracks=sum(t.GetClass()=='PCB_TRACK' for t in new.GetTracks()),
                vias=sum(t.GetClass()=='PCB_VIA' for t in new.GetTracks()),
                copper_outside_controller_unchanged=True,controller_area_pcb_xy_mm=[398,0,452.4375,29],
                geometric_comparison_tolerance_mm=.0002)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
