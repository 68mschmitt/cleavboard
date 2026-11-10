#!/usr/bin/env python3
"""Compare original baseline files with their relocated working-tree contents."""

from pathlib import Path
import subprocess
import sys

from repository_paths import current_path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = "8b0f52aa4cf324d2eb17dd09f180e6ee596c49ad"
PATHS = (
    "kicad/",
    "mechanical/",
    "manufacturing/",
    "scripts/",
    "plate-2026-11-07T22_24_25.197Z/",
    "Cleaver-gerbers.zip",
)


def local_state(path):
    p = Path(path)
    return ('.history' in p.parts or '__pycache__' in p.parts
            or p.suffix in {'.kicad_prl', '.lck', '.pyc'}
            or any(part.endswith('-backups') for part in p.parts))


def main():
    try:
        entries = subprocess.check_output(
            ['git', 'ls-tree', '-r', '-z', BASELINE, '--', *PATHS], cwd=ROOT,
        ).decode().split('\0')
        changed = []
        expected = set()
        for entry in filter(None, entries):
            metadata, old = entry.split('\t', 1)
            _, kind, digest = metadata.split()
            if kind != 'blob' or local_state(old):
                continue
            name = current_path(old)
            expected.add(name)
            path = ROOT / name
            if not path.is_file():
                changed.append(('D', name))
                continue
            actual = subprocess.check_output(
                ['git', 'hash-object', '--stdin'], input=path.read_bytes(), cwd=ROOT,
            ).decode().strip()
            if actual != digest:
                changed.append(('M', name))
        candidates = subprocess.check_output(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z'], cwd=ROOT,
        ).decode().split('\0')
        prefixes = ('designs/module-rp2040/', 'assets/layout/')
        for name in sorted(set(filter(None, candidates))):
            if (name.startswith(prefixes) and name not in expected
                    and not local_state(name) and (ROOT / name).is_file()):
                changed.append(('A', name))
    except subprocess.CalledProcessError:
        print('ERROR: Git could not read the historical baseline.', file=sys.stderr)
        return 2
    for status, name in changed:
        print(f'{status}\t{name}')
    if changed:
        print(f'{len(changed)} differences from the historical baseline (paths translated).')
        return 1
    print('PASS: original design files match the historical baseline (paths translated).')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
