#!/usr/bin/env python3
"""Attach/check the bundled 3D models without regenerating or rerouting the PCB."""
import argparse
import json

import pcbnew

from design import ROOT
from models_3d import update_board_models, update_library_models, validate_models


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='Check only; do not update assignments')
    args = parser.parse_args()
    folder = ROOT
    if not args.check:
        update_library_models(folder/'Cleaver.pretty')
        update_board_models(folder/'Cleaver.kicad_pcb')
    board = pcbnew.LoadBoard(str(folder/'Cleaver.kicad_pcb'))
    print(json.dumps(validate_models(board),indent=2))


if __name__=='__main__':
    main()
