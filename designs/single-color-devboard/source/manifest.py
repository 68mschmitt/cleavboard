#!/usr/bin/env python3
"""Hash the complete handoff, excluding transient UI/cache files and itself."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'SHA256.json'
paths = [p for p in sorted(ROOT.rglob('*')) if p.is_file() and p != output
         and '__pycache__' not in p.parts and not p.name.startswith('~')
         and p.suffix not in {'.pyc', '.kicad_prl', '.lck'}]
output.write_text(json.dumps({str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in paths}, indent=2) + '\n')
print(f'Hashed {len(paths)} handoff files.')
