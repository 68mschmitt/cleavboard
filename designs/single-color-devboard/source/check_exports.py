#!/usr/bin/env python3
"""Independently check exported assembly, archive and firmware against sources."""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json
import zipfile
import pcbnew

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(name):
    with (ROOT / name).open(newline='') as file:
        return list(csv.DictReader(file))


def main():
    board = pcbnew.LoadBoard(str(ROOT / 'Cleaver-White.kicad_pcb'))
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    # Derive purchased parts from copper pads, independently of components.json.
    expected = {ref for ref, f in fps.items()
                if any(p.IsOnLayer(pcbnew.B_Paste) for p in f.Pads())}
    cpl = rows('manufacturing/CPL-JLCPCB.csv')
    bom = rows('manufacturing/BOM.csv')
    grouped = rows('manufacturing/BOM-JLCPCB.csv')
    assert len(expected) == len(cpl) == len(bom) == 476
    assert Counter(r['Designator'] for r in cpl) == Counter({r: 1 for r in expected})
    assert Counter(r['Reference'] for r in bom) == Counter({r: 1 for r in expected})
    assert Counter(ref for r in grouped for ref in r['Designator'].split(',')) == Counter({r: 1 for r in expected})
    assert all(int(r['Quantity']) == len(r['Designator'].split(',')) for r in grouped)
    assert 'U1' not in expected
    height = 147.6375
    for r in cpl:
        ref = r['Designator']
        f = fps[ref]
        assert r['Layer'] == 'bottom'
        if ref.startswith('SW'):
            # Documented mechanical offset, not exporter's pad-average method.
            x = f.GetPosition().x / 1e6 - .635
            y = f.GetPosition().y / 1e6 - 3.81
        else:
            x, y = f.GetPosition().x / 1e6, f.GetPosition().y / 1e6
        assert abs(float(r['Mid X']) - x) < 1e-6, ref
        assert abs(float(r['Mid Y']) - (height - y)) < 1e-6, ref
        assert abs(float(r['Rotation']) - f.GetOrientationDegrees() % 360) < .001, ref
    pads = rows('manufacturing/pad-orientation-reference.csv')
    actual = {(r, p.GetNumber()): p for r in expected for p in fps[r].Pads()
              if p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD}
    assert len(pads) == len(actual)
    assert {(r['Designator'], r['Pad']) for r in pads} == set(actual)
    centroids = {r['Designator']: (float(r['Mid X']), float(r['Mid Y'])) for r in cpl}
    for r in pads:
        pad = actual[(r['Designator'], r['Pad'])]
        x, y = pad.GetPosition().x / 1e6, height - pad.GetPosition().y / 1e6
        cx, cy = centroids[r['Designator']]
        assert r['Net'] == pad.GetNetname()
        for key, value in [('X_mm', x), ('Y_mm', y), ('DX_from_centroid_mm', x-cx), ('DY_from_centroid_mm', y-cy)]:
            assert abs(float(r[key]) - value) < 1e-6, (r['Designator'], key)
    for r in bom:
        assert r['Assembly Side'] == 'bottom'
        if r['Reference'].startswith('LED'):
            assert r['Manufacturer'] == 'BrtLed' and r['MPN'] == 'BL-HZ333H-L21-TRE' and r['LCSC Part #'] == 'C5123487'
        if r['Reference'].startswith('SW'):
            assert r['Manufacturer'] == 'HanElectricity' and r['MPN'] == 'CPG151101S11-16' and r['LCSC Part #'] == 'C41430893'
        if r['Reference'].startswith(('SW','LED')):
            f=fps[r['Reference']]
            assert f.GetFieldText('LCSC Part #')==r['LCSC Part #'] and f.GetValue()==r['MPN']
    for prefix,code,mpn in [('SW','C41430893','CPG151101S11-16'),('LED','C5123487','BL-HZ333H-L21-TRE')]:
        row=next(r for r in grouped if r['LCSC Part #']==code)
        assert row['Comment']==mpn and int(row['Quantity'])==117
        assert set(row['Designator'].split(','))=={f'{prefix}{i:03d}' for i in range(1,118)}
    for filename in ['validation/validation.json', 'manufacturing/SHA256.json']:
        data = json.loads((ROOT / filename).read_text())
        for name, sha in data.get('hashes', data).items():
            assert digest(ROOT / name) == sha, name
    fab = ROOT / 'manufacturing/fabrication'
    with zipfile.ZipFile(ROOT / 'manufacturing/Cleaver-White-white-0.1-prototype.zip') as archive:
        assert set(archive.namelist()) == {p.name for p in fab.iterdir() if p.is_file()}
        for name in archive.namelist():
            assert archive.read(name) == (fab / name).read_bytes(), name
    fw = ROOT / 'firmware'
    provenance = json.loads((fw / 'build/provenance.json').read_text())
    for name, sha in provenance['source_sha256'].items():
        assert digest(fw / name) == sha, name
    for keymap in ['default', 'vial']:
        path = fw / f'build/cleaver_white_{keymap}.uf2'
        assert digest(path) == provenance[keymap]['sha256']
        assert path.stat().st_size == provenance[keymap]['bytes']
    result = dict(passed=True, placements=len(cpl), socket_centroids=117,
                  pad_references=len(pads), owner_module_excluded=True,
                  manufacturing_hashes_match=True, fabrication_zip_matches=True,
                  firmware_sources_and_binaries_match=True)
    (ROOT / 'validation/exports.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
