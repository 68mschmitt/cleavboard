#!/usr/bin/env python3
"""Read-only check that the original tracked hardware design is unchanged."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
BASELINE = "8b0f52aa4cf324d2eb17dd09f180e6ee596c49ad"
PATHS = (
    "kicad/",
    "mechanical/",
    "manufacturing/",
    "scripts/",
    "plate-2026-11-07T22_24_25.197Z/",
    "Cleaver-gerbers.zip",
    ":(exclude)kicad/.history",
    ":(exclude,glob)kicad/~*.lck",
)


def main():
    result = subprocess.run(
        [
            "git", "diff", "--no-ext-diff", "--no-textconv",
            "--ignore-submodules=all", "--exit-code", "--name-status",
            BASELINE, "--", *PATHS,
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode == 0:
        print("PASS: original tracked design files match the preserved baseline.")
        print("The pre-existing kicad/.history working tree and transient editor locks are excluded.")
    elif result.returncode == 1:
        print("FAIL: original tracked design files differ from the baseline.", file=sys.stderr)
    else:
        print("ERROR: Git could not verify the preserved baseline.", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
