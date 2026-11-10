#!/usr/bin/env python3
"""Optional local rip-up/escape repair; requires a fresh DRC afterwards.
Adds off-land access vias to selected fine-pitch pads, removing obstructing
controller tracks only. Used during route development, not normal regeneration.
"""
import math,json,sys
from pathlib import Path
import pcbnew
from shapely.geometry import LineString,Point,box
from generate import ROOT,NAME,mm,xy,track,via
board=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
fps={f.GetReference():f for f in board.GetFootprints()}
pads=[p for f in fps.values() for p in f.Pads()]
def geom(p):
    x,y=xy(p.GetPosition())
    if p.GetShape()==pcbnew.PAD_SHAPE_CIRCLE:return Point(x,y).buffer(pcbnew.ToMM(p.GetSize().x)/2)
    b=p.GetBoundingBox();return box(pcbnew.ToMM(b.GetX()),pcbnew.ToMM(b.GetY()),pcbnew.ToMM(b.GetRight()),pcbnew.ToMM(b.GetBottom()))
padgeo=[(p,geom(p)) for p in pads]
protected={tuple(xy(p.GetPosition())) for p in fps['U1'].Pads() if p.GetNumber()}
held=[];log=[]
selection=[s.split(':') for s in sys.argv[1:]] or [('U1','2'),('U1','13'),('U1','16'),('U1','24'),('C28','1'),('C29','1'),('J1','A7')]
for ref,num in selection:
    pad=next(p for p in fps[ref].Pads() if p.GetNumber()==num);start=xy(pad.GetPosition());net=pad.GetNetname();layer=fps[ref].GetLayer()
    candidates=[]
    tracks=list(board.GetTracks())
    nearby=[(p,g) for p,g in padgeo if g.distance(Point(*start))<5]
    for angle in ([135] if ref=='R14' and num=='1' else [225] if ref=='C22' and num=='2' else [180] if ref=='U1' and num=='16' else [270] if ref=='U1' and num=='4' else range(0,360,5)):
        for step in range(15,51):
            r=step*.05;end=(round(start[0]+r*math.cos(math.radians(angle)),3),round(start[1]+r*math.sin(math.radians(angle)),3))
            line=LineString([start,end]);point=Point(*end)
            if any(t.GetClass()=='PCB_VIA' and t.GetNetname()==net and point.distance(Point(*xy(t.GetPosition())))<pcbnew.ToMM(t.GetDrillValue())/2+.1+.25 for t in tracks):continue
            if any((p.GetNetname()!=net and p.IsOnLayer(layer) and line.distance(g)<.0635+.13) or point.distance(g)<(.23 if p.GetNetname()==net else .34) for p,g in nearby):continue
            removed=[];score=r*.1;bad=False
            for t in tracks:
                if t.GetNetname()==net:continue
                if t.GetClass()=='PCB_VIA':
                    g=Point(*xy(t.GetPosition()));radius=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2
                    clash=line.distance(g)<radius+.0635+.13 or point.distance(g)<radius+.34
                    if clash:removed.append(t);score+=20
                else:
                    g=LineString([xy(t.GetStart()),xy(t.GetEnd())]);radius=pcbnew.ToMM(t.GetWidth())/2
                    clash=(t.GetLayer()==layer and line.distance(g)<radius+.0635+.13) or point.distance(g)<radius+.34
                    if clash:
                        if tuple(xy(t.GetStart())) in protected or tuple(xy(t.GetEnd())) in protected:bad=True;break
                        removed.append(t);score+=1+g.length*.02
            if not bad:candidates.append((score,end,removed))
    if not candidates:log.append(dict(ref=ref,pin=num,result='no safe escape'));continue
    score,end,removed=min(candidates,key=lambda c:c[0])
    for t in removed:board.Remove(t);held.append(t)
    track(board,net.lstrip('/'),start,end,layer,width=.127)
    v=via(board,net.lstrip('/'),*end);v.SetWidth(pcbnew.FromMM(.4));v.SetDrill(pcbnew.FromMM(.2))
    log.append(dict(ref=ref,pin=num,net=net,start=start,end=end,removed=len(removed),score=score))
for z in board.Zones():
    if not z.GetIsRuleArea():z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),board)
(ROOT/'routing/escape-repairs.json').write_text(json.dumps(log,indent=2)+'\n')
print(json.dumps(log,indent=2))
