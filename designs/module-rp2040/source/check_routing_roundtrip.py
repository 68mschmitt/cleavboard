#!/usr/bin/env python3
"""Regenerate in an isolated project copy and compare all archived copper.

The active design is never regenerated or overwritten by this check.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pcbnew

from archive_routing import archive
from design import ROOT, REVISION


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports',type=Path,default=ROOT/f'manufacturing/rev{REVISION}/checks/roundtrip')
    args=parser.parse_args();args.reports=args.reports.resolve()
    args.reports.mkdir(parents=True,exist_ok=True)
    pcb=ROOT/'Cleaver.kicad_pcb';session=ROOT/'routing/Cleaver.ses'
    before=digest(pcb)
    with tempfile.TemporaryDirectory(prefix='cleaver-roundtrip-',dir='/tmp/opencode') as folder:
        project=Path(folder)/'designs/module-rp2040';project.mkdir(parents=True)
        for name in ('source','Cleaver.pretty','Cleaver.3dshapes','routing','firmware'):
            shutil.copytree(ROOT/name,project/name,ignore=shutil.ignore_patterns('__pycache__'))
        (project/'manufacturing').mkdir()
        for path in ROOT.glob('*.kicad_*'):
            if path.suffix!='.kicad_prl':shutil.copy2(path,project/path.name)
        shutil.copytree(ROOT.parents[1]/'assets/layout',Path(folder)/'assets/layout')
        subprocess.run([sys.executable,'-B',str(project/'source/generate_kicad.py'),
                        '--ses',str(project/'routing/Cleaver.ses'),
                        '--reports',str(args.reports/'generation')],check=True)
        subprocess.run([sys.executable,'-B',str(project/'source/check_kicad.py'),
                        '--reports',str(args.reports/'regenerated')],check=True)
        # A fresh process avoids retaining KiCad's generation SWIG objects.
        rebuilt=args.reports/'regenerated.ses'
        subprocess.run([sys.executable,'-B',str(project/'source/archive_routing.py'),
                        str(project/'Cleaver.kicad_pcb'),str(rebuilt)],check=True)
        active=args.reports/'active.ses'
        archive(pcbnew.LoadBoard(str(pcb)),active)
        assert active.read_bytes()==session.read_bytes(), 'Active archive is stale'
        assert active.read_bytes()==rebuilt.read_bytes(), 'Regenerated copper differs'
        for path in (ROOT/'firmware').rglob('*'):
            if path.is_file():
                regenerated=project/'firmware'/path.relative_to(ROOT/'firmware')
                assert path.read_bytes()==regenerated.read_bytes(), f'Firmware drift: {path.name}'
    assert digest(pcb)==before, 'Round-trip check modified the active PCB'
    result=dict(revision=REVISION,pcb_sha256=before,session_sha256=digest(session),
                canonical_copper_exact_match=True,archive_coordinate_resolution_mm=.0001,
                regenerated_erc_violations=0,regenerated_drc_violations=0,
                regenerated_unconnected_items=0,regenerated_parity_issues=0,
                firmware_unchanged=True,active_pcb_unchanged=True)
    (args.reports/'roundtrip.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS: isolated fresh generation, exact canonical copper, unchanged firmware, ERC/DRC/parity')


if __name__=='__main__':main()
