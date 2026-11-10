#!/usr/bin/env python3
"""Hash the completed handoff, including independently supplied firmware evidence."""
import datetime,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'validation/manifest.json'
validation=json.loads((ROOT/'validation/validation.json').read_text())
roundtrip=json.loads((ROOT/'validation/roundtrip.json').read_text())
firmware=json.loads((ROOT/'validation/firmware/results.json').read_text())
firmware_matches=all(hashlib.sha256((ROOT/'firmware'/name).read_bytes()).hexdigest()==digest for name,digest in firmware['source_sha256'].items())
files={}
for p in sorted(ROOT.rglob('*')):
    if not p.is_file() or p==target or p.suffix in ['.lck','.kicad_prl','.pyc'] or '__pycache__' in p.parts:continue
    if any(part.endswith('-backups') for part in p.parts):continue
    files[str(p.relative_to(ROOT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
result={'schema_version':1,'revision':'embedded-0.2','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'electrical_checks_pass':validation['electrical_checks_pass'],'roundtrip_pass':roundtrip['pass'],'firmware_compile_inputs_match_independent_build':firmware_matches,'firmware_builds_pass':all(b['success'] for b in firmware['builds'].values()),'fabrication_ready':False,'files':files}
target.write_text(json.dumps(result,indent=2)+'\n')
print('Manifest:',len(files),'files; electrical',result['electrical_checks_pass'],'roundtrip',result['roundtrip_pass'],'firmware inputs',firmware_matches)
assert result['electrical_checks_pass'] and result['roundtrip_pass'] and firmware_matches and result['firmware_builds_pass']
