#!/usr/bin/env python3
"""One-time migration: add RP2040-Plus pin-40 VBUS to revision 0.5 copper.

The CLI migrates a revision 0.5 PCB while preserving existing item identities.
Alternatively call upgrade() on rev0.6 placement imported with the old copper.
Normal regeneration uses the checked revision 0.6 routing/Cleaver.ses instead.
"""
import argparse
from pathlib import Path
import pcbnew
from design import MODULE_PINS, MODULE_X, MODULE_Y
from generate_kicad import mm


def upgrade(board):
    module = next(fp for fp in board.GetFootprints() if fp.GetReference() == 'U1')
    pad = module.FindPadByNumber('40')
    assert pad.GetNetname() == '/RAW_USB_5V'
    start = tuple(pcbnew.ToMM(pad.GetPosition()))
    # Land on the existing off-pad TP1 via. 0.6 mm trace, 45-degree entry.
    points = [start, (start[0] - (24.8-start[1]), 24.8), (446,24.8)]
    for a,b in zip(points,points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetStart(mm(*a)); track.SetEnd(mm(*b))
        track.SetWidth(pcbnew.FromMM(.6)); track.SetLayer(pcbnew.F_Cu)
        track.SetNet(pad.GetNet()); board.Add(track)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


def migrate(board):
    """Update a rev0.5 PCB in place, preserving unrelated item identities."""
    assert board.GetTitleBlock().GetRevision() == '0.5'
    footprints = {fp.GetReference():fp for fp in board.GetFootprints()}
    module = footprints['U1']
    assert str(module.GetFPID().GetLibItemName()) == 'YD_RP2040'
    module.SetFPID(pcbnew.LIB_ID('Cleaver', 'Waveshare_RP2040_Plus'))
    module.SetLibDescription('Cleaver verified geometry: Waveshare_RP2040_Plus')
    module.SetValue('Waveshare RP2040-Plus 4MB')
    for n in ('35','37','39'):
        module.FindPadByNumber(n).GetNet().SetNetname(f'unconnected-(U1-{MODULE_PINS[int(n)]}-Pad{n})')
    module.FindPadByNumber('40').SetNet(board.FindNet('/RAW_USB_5V'))
    model = pcbnew.FP_3DMODEL()
    model.m_Filename = '${KIPRJMOD}/Cleaver.3dshapes/Waveshare_RP2040_Plus_Approx.wrl'
    module.Models().clear()
    module.Models().push_back(model)
    shapes = [s for s in module.GraphicalItems() if s.GetClass() == 'PCB_SHAPE']
    assert len(shapes) == 2
    # Existing rectangle order is PCB body, then USB shell.
    for shape,half_w,y0,y1 in [(shapes[0],10.5,25.5,-25.5), (shapes[1],4.475,27.5,19)]:
        shape.SetStart(mm(MODULE_X+y0,MODULE_Y-half_w))
        shape.SetEnd(mm(MODULE_X+y1,MODULE_Y+half_w))
    footprints['TP1'].SetValue('USB VBUS TEST +5V')
    for drawing in board.GetDrawings():
        if drawing.GetClass() != 'PCB_TEXT':
            continue
        if drawing.GetText() == 'TP1 USB 5V TAP +':
            drawing.SetText('TP1 VBUS TEST +')
        elif drawing.GetText() == 'CLEAVER rev0.5 | USB-C | BOTTOM SMT':
            drawing.SetText('CLEAVER rev0.6 | RP2040-PLUS | BOTTOM SMT')
    board.GetTitleBlock().SetTitle('Cleaver - Waveshare RP2040-Plus / 117 keys')
    board.GetTitleBlock().SetDate('2026-11-11')
    board.GetTitleBlock().SetRevision('0.6')
    upgrade(board)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline',type=Path,help='Revision 0.5 PCB')
    parser.add_argument('output',type=Path,help='Revision 0.6 PCB destination, beside its project file')
    args = parser.parse_args()
    # Load under the output filename so KiCad applies the carrier project rules.
    args.output.write_bytes(args.baseline.read_bytes())
    board = pcbnew.LoadBoard(str(args.output))
    migrate(board)
    pcbnew.SaveBoard(str(args.output),board)
