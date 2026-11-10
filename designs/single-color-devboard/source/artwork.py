#!/usr/bin/env python3
"""Place the shared 34mm Taviana Tactical top-silkscreen artwork."""
from pathlib import Path
import uuid
import pcbnew

ROOT = Path(__file__).resolve().parents[1]
NAME = 'TavianaTactical_34mm'


def add(board):
    for old in list(board.GetFootprints()):
        if old.GetReference() == 'LOGO1':
            if str(old.GetFPID().GetLibItemName()) != NAME:
                raise ValueError('LOGO1 already used by an unfamiliar footprint')
            board.Remove(old)
    logo = pcbnew.FootprintLoad(str(ROOT / 'Cleaver-White.pretty'), NAME)
    logo.SetFPID(pcbnew.LIB_ID('Cleaver-White', NAME))
    logo.SetReference('LOGO1')
    logo.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(199), pcbnew.FromMM(122)))
    board.Add(logo)
    logo.SetLocked(True)
    for i, item in enumerate([logo, *logo.GetFields(), *logo.GraphicalItems()]):
        item.SetUuid(pcbnew.KIID(str(uuid.uuid5(uuid.NAMESPACE_URL, f'cleaver:tavi:Cleaver-White:{i}'))))


if __name__ == '__main__':
    file = ROOT / 'Cleaver-White.kicad_pcb'
    board = pcbnew.LoadBoard(str(file))
    add(board)
    pcbnew.SaveBoard(str(file), board)
    print('Added top silkscreen: 34mm wide at (199, 122)mm')
