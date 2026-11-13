#!/usr/bin/env python3
"""Independently check the badge migration against an explicit rev0.7 backup."""
import argparse
import hashlib
import json
from pathlib import Path

import pcbnew

from check_rev07_migration import pad_record
from design import ROOT


def copper_record(item):
    via = item.GetClass() == 'PCB_VIA'
    return (item.GetClass(), item.GetNetname(), item.GetLayer(),
            tuple(item.GetStart()), tuple(item.GetEnd()),
            item.GetWidth(pcbnew.F_Cu) if via else item.GetWidth(),
            item.GetDrillValue() if via else None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT/'manufacturing/rev0.8/checks/migration.json')
    args = parser.parse_args()
    pcb = ROOT/'Cleaver.kicad_pcb'
    old, new = pcbnew.LoadBoard(str(args.baseline)), pcbnew.LoadBoard(str(pcb))
    assert old.GetTitleBlock().GetRevision() == '0.7'
    assert new.GetTitleBlock().GetRevision() == '0.8'
    assert json.loads(args.baseline.with_suffix('.kicad_pro').read_text()) == json.loads((ROOT/'Cleaver.kicad_pro').read_text())
    before = {f.GetReference(): f for f in old.GetFootprints()}
    after = {f.GetReference(): f for f in new.GetFootprints()}
    added = {f'LED{i}' for i in range(118, 122)} | {f'C{i}' for i in range(218, 222)}
    assert set(after)-set(before) == added and not set(before)-set(after)
    for ref, fp in before.items():
        other = after[ref]
        assert fp.m_Uuid.AsString() == other.m_Uuid.AsString(), ref
        assert fp.GetValue() == other.GetValue() and fp.GetFPID() == other.GetFPID(), ref
        if ref == 'H9':
            assert tuple(pcbnew.ToMM(fp.GetPosition())) == (220., 138.)
            assert tuple(pcbnew.ToMM(other.GetPosition())) == (250., 138.)
            continue
        assert tuple(fp.GetPosition()) == tuple(other.GetPosition()), ref
        for pad in fp.Pads():
            # Unnumbered holes can repeat; compare all records below instead.
            if ref == 'LED112' and pad.GetNumber() == '4':
                actual = pad_record(other.FindPadByNumber('4'))
                expected = list(pad_record(pad))
                assert expected[6].startswith('unconnected-')
                expected[6] = '/RGB_117'
                assert tuple(expected) == actual
        if ref == 'LED112':
            assert sorted(pad_record(p) for p in fp.Pads() if p.GetNumber() != '4') == sorted(
                pad_record(p) for p in other.Pads() if p.GetNumber() != '4')
        else:
            assert sorted(pad_record(p) for p in fp.Pads()) == sorted(pad_record(p) for p in other.Pads()), ref
    original = {t.m_Uuid.AsString(): copper_record(t) for t in old.GetTracks()}
    current = {t.m_Uuid.AsString(): copper_record(t) for t in new.GetTracks()}
    assert all(current.get(uid) == geometry for uid, geometry in original.items()), 'Existing routed copper changed'
    result = dict(baseline_revision='0.7', revision='0.8',
                  baseline_pcb_sha256=hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                  pcb_sha256=hashlib.sha256(pcb.read_bytes()).hexdigest(),
                  project_rules_settings_and_exclusions_unchanged=True,
                  existing_copper_items_exactly_retained=len(original),
                  added_copper_items=len(current)-len(original),
                  unchanged_footprints_and_pad_nets=len(before)-2,
                  moved_mount=dict(reference='H9', before_mm=[220,138], after_mm=[250,138]),
                  changed_key_led_pin='LED112.4: no-connect -> RGB_117', new_references=sorted(added),
                  tracks=sum(t.GetClass() == 'PCB_TRACK' for t in new.GetTracks()),
                  vias=sum(t.GetClass() == 'PCB_VIA' for t in new.GetTracks()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
