#!/usr/bin/env python3
"""Add clearance-checked controller ground stitching; verify with fresh DRC."""
import json
import pcbnew
from shapely.geometry import Point,LineString,box
from generate import ROOT,NAME,xy,via
b=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
pads=[]
for fp in b.GetFootprints():
    for p in fp.Pads():
        x,y=xy(p.GetPosition())
        if x<395 or y>30:continue
        bb=p.GetBoundingBox()
        g=Point(x,y).buffer(pcbnew.ToMM(p.GetSize().x)/2) if p.GetShape()==pcbnew.PAD_SHAPE_CIRCLE else box(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))
        pads.append(g)
tracks=[]
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':tracks.append((Point(*xy(t.GetPosition())),pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2+.4))
    elif t.GetNetname()!='/GND':tracks.append((LineString([xy(t.GetStart()),xy(t.GetEnd())]),pcbnew.ToMM(t.GetWidth())/2+.4))
added=[]
for x in [400.5+3*i for i in range(17)]:
    for y in [1.5+3*i for i in range(9)]:
        point=Point(x,y)
        if 417<x<425 and 9<y<17:continue
        if any(point.distance(g)<.4 for g in pads):continue
        if any(point.distance(g)<clear for g,clear in tracks):continue
        v=via(b,'GND',x,y);v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
        added.append([x,y]);tracks.append((point,.65))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
(ROOT/'routing/ground-stitching.json').write_text(json.dumps(added,indent=2)+'\n')
print('Added',len(added),'GND stitching vias')
