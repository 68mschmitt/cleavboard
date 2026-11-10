#!/usr/bin/env python3
"""Add short off-pad plane escapes with conservative geometry checks.
Run after --placement, before controller routing. Real KiCad DRC is mandatory.
"""
from generate import *
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
import math
def bounds(p):
    a=p.GetBoundingBox();return box(pcbnew.ToMM(a.GetX()),pcbnew.ToMM(a.GetY()),pcbnew.ToMM(a.GetRight()),pcbnew.ToMM(a.GetBottom()))
def shape(p):
    if p.GetShape()==pcbnew.PAD_SHAPE_CIRCLE:return Point(xy(p.GetPosition())).buffer(pcbnew.ToMM(p.GetSize().x)/2)
    return bounds(p)
def main():
    path=ROOT/(NAME+'.kicad_pcb');b=pcbnew.LoadBoard(str(path));held=list(b.GetTracks())
    for t in held:
        if t.GetNetname() in ['/LED_5V','/LED_RETURN']:b.Remove(t)
    fps={f.GetReference():f for f in b.GetFootprints()}
    # Reflect the silkscreen-library correction in an in-progress board.
    for f in fps.values():
        if f.GetReference().startswith('LED'):
            for s in f.GraphicalItems():
                if s.GetLayer()==pcbnew.B_SilkS:s.SetStart(f.GetPosition()+mm(-2.7,1.15));s.SetEnd(f.GetPosition()+mm(-1.3,1.15))
    holes=[];lands=[];edges=[]
    for f in fps.values():
        if f.GetReference().startswith('H'):holes.append(Point(xy(f.GetPosition())).buffer(3.05))
        for p in f.Pads():
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:holes.append(shape(p).buffer(.25))
            elif p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:lands.append(shape(p).buffer(.1))
        for s in f.GraphicalItems():
            if s.GetLayer()==pcbnew.Edge_Cuts:edges.append(bounds(s).buffer(.5))
    forbidden=unary_union(holes+edges)
    pads=[p for f in fps.values() for p in f.Pads()]
    targets=[(f'RL{i:03d}','2') for i in range(1,118)]+[(f'LED{i:03d}','1') for i in range(1,118)]
    targets += [(r,n) for r in ['U3','C1','C2','Q1','R2','R3','TP2','TP4','TP6'] for n in [p.GetNumber() for p in fps[r].Pads()] if next(p for p in fps[r].Pads() if p.GetNumber()==n).GetNetname() in ['/GND','/LED_5V','/LED_RETURN']]
    results=[]
    for ref,num in targets:
        p=next(p for p in fps[ref].Pads() if p.GetNumber()==num);net=p.GetNetname();a=xy(p.GetPosition());obsall=[];obsb=[]
        for other in pads:
            if other.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:continue
            if other.GetNetname()!=net:
                g=shape(other).buffer(.22);obsall.append(g)
                if other.IsOnLayer(pcbnew.B_Cu):obsb.append(g)
        for t in b.GetTracks():
            if t.GetNetname()==net:continue
            if t.GetClass()=='PCB_VIA':g=Point(xy(t.GetPosition())).buffer(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2+.22)
            else:g=LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(pcbnew.ToMM(t.GetWidth())/2+.22)
            obsall.append(g)
            if t.GetClass()=='PCB_VIA' or t.GetLayer()==pcbnew.B_Cu:obsb.append(g)
        allgeom=unary_union(obsall+[forbidden]+lands);bgeom=unary_union(obsb+[forbidden])
        found=None
        for length in [1.5,1.7,1.9,2.1,2.4,2.8,3.2]:
            directions=[(-1,0),(0,1),(0,-1),(1,0),(-1,1),(-1,-1),(1,1),(1,-1)] if ref.startswith('LED') else [(0,1),(1,0),(0,-1),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]
            for dx,dy in directions:
                c=(a[0]+dx*length,a[1]+dy*length)
                if not (.85<c[0]<W-.85 and .85<c[1]<H-.85):continue
                if Point(c).buffer(.3).intersects(allgeom):continue
                if LineString([a,c]).buffer(.15).intersects(bgeom):continue
                found=c;break
            if found:break
        if found:
            track(b,net[1:],a,found);via(b,net[1:],*found);results.append([ref,num,list(a),list(found)])
        else:print('NO ESCAPE',ref,num,a)
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(path),b)
    (ROOT/'source/fanouts.json').write_text(json.dumps(results,indent=2)+'\n');print('Added',len(results),'plane escapes')
if __name__=='__main__':main()
