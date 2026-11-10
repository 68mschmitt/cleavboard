#!/usr/bin/env python3
"""One-time rev0.4 copper migration after generating rev0.5 placement.

Normal regeneration uses routing/Cleaver.ses; this records the local reroute.
The input is a rev0.5 board populated with the old complete-copper archive.
"""
from pathlib import Path
import pcbnew
from design import ROOT
from generate_kicad import mm


def upgrade(board):
    def track(net,a,b,layer=pcbnew.B_Cu,width=.6):
        item=pcbnew.PCB_TRACK(board)
        item.SetStart(mm(*a));item.SetEnd(mm(*b));item.SetLayer(layer)
        item.SetWidth(pcbnew.FromMM(width));item.SetNet(board.FindNet('/'+net));board.Add(item)

    def via(net,x,y):
        item=pcbnew.PCB_VIA(board);item.SetPosition(mm(x,y))
        item.SetWidth(pcbnew.FromMM(.7));item.SetDrill(pcbnew.FromMM(.3))
        item.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);item.SetNet(board.FindNet('/'+net))
        item.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED)
        item.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED);board.Add(item)

    removed=0
    for item in list(board.GetTracks()):
        if item.GetNetname()=='/ROW1' and item.GetClass()=='PCB_TRACK' and (
                tuple(pcbnew.ToMM(item.GetStart())) in [(371.2,18.5),(382.8,6.9)]):
            board.Remove(item);removed+=1
    assert removed==2, 'Expected the two legacy ROW1 segments next to C5'
    row = [(371.2,18.5),(381.9,7.8),(384.7,7.8),(385.6,6.9),(394.2,6.9)]
    for a,b in zip(row,row[1:]):
        track('ROW1',a,b,width=.2)
    # Off-land via connections: no via-in-pad processing is required.
    track('LED_5V',(373,6),(375.8,6));via('LED_5V',375.8,6)
    track('LED_5V',(375.8,6),(375.25,6),pcbnew.In2_Cu)
    track('GND',(381,6),(384,6));via('GND',384,6)
    track('RAW_USB_5V',(446,27),(446,24.8),pcbnew.F_Cu)
    track('RAW_USB_5V',(446,27),(446,24.8));via('RAW_USB_5V',446,24.8)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())


if __name__=='__main__':
    path=ROOT/'kicad/Cleaver.kicad_pcb'
    board=pcbnew.LoadBoard(str(path));upgrade(board);pcbnew.SaveBoard(str(path),board)
