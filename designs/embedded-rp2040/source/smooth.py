#!/usr/bin/env python3
"""Clearance-aware octilinear pull-tight of real routing, across the entire PCB.
Preserves terminals, junctions, layer and width. Replaces detours/staircases with
shortest 0/45/90-degree paths, rather than merely merging collinear segments.
Mandatory independent KiCad DRC/continuity check after each saved pass.
"""
import argparse,collections,json,math
from pathlib import Path
import pcbnew
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
from generate import ROOT,NAME,xy,mm

def alternatives(a,b):
    dx,dy=b[0]-a[0],b[1]-a[1];sx=1 if dx>=0 else -1;sy=1 if dy>=0 else -1;d=min(abs(dx),abs(dy))
    for c in [(a[0]+sx*d,a[1]+sy*d),(b[0]-sx*d,b[1]-sy*d)]:
        points=[a]
        if math.dist(a,c)>1e-6 and math.dist(c,b)>1e-6:points.append(c)
        points.append(b);yield points

def run(b,controller_only=False):
    tracks=list(b.GetTracks());segments=[t for t in tracks if t.GetClass()=='PCB_TRACK'];objects=[];geoms=[]
    # (net, layers, shape, clearance). Shapes already include copper/hole radii.
    def obstacle(net,layers,g,clear=.135):objects.append((net,set(layers),g,clear));geoms.append(g)
    layers=[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]
    for t in tracks:
        if t.GetClass()=='PCB_VIA':obstacle(t.GetNetCode(),layers,Point(xy(t.GetPosition())).buffer(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2))
        else:obstacle(t.GetNetCode(),[t.GetLayer()],LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(pcbnew.ToMM(t.GetWidth())/2))
    pads=[];vias=[t for t in tracks if t.GetClass()=='PCB_VIA']
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:
                obstacle(-1,layers,Point(xy(p.GetPosition())).buffer(pcbnew.ToMM(max(p.GetDrillSize().x,p.GetDrillSize().y))/2),.505);continue
            bb=p.GetBoundingBox();g=box(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))
            if p.GetShape()==pcbnew.PAD_SHAPE_CIRCLE:g=Point(xy(p.GetPosition())).buffer(pcbnew.ToMM(p.GetSize().x)/2)
            copper=[l for l in layers if p.IsOnLayer(l)]
            if copper:obstacle(p.GetNetCode(),copper,g);pads.append((p.GetNetCode(),set(copper),g))
        for s in f.GraphicalItems():
            if s.GetLayer()==pcbnew.Edge_Cuts:
                bb=s.GetBoundingBox();obstacle(-1,layers,box(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom())),.505)
        if f.GetReference().startswith('H'):obstacle(-1,layers,Point(xy(f.GetPosition())).buffer(3),.01)
        if f.GetReference().startswith('FID'):obstacle(-1,layers,Point(xy(f.GetPosition())).buffer(1.5),.135)
    tree=STRtree(geoms)
    added=[]
    def clear(points,net,layer,width):
        path=LineString(points);bounds=path.bounds;r=width/2
        if min(bounds[0],bounds[1],452.4375-bounds[2],147.6375-bounds[3])<.505+r:return False
        if layer==pcbnew.In2_Cu:
            for t in segments:
                if t.GetLayer()==pcbnew.B_Cu and t.GetNetname() in ['/USB_N','/USB_P','/USB_DM','/USB_DP','/XIN','/XOUT','/XTAL_OUT'] and path.distance(LineString([xy(t.GetStart()),xy(t.GetEnd())]))<.65+r:return False
        for idx in tree.query(path.buffer(r+.55)):
            other,ls,g,spacing=objects[idx]
            if other==net or layer not in ls:continue
            if path.distance(g)<r+spacing-1e-7:return False
        for other,ls,g,spacing in added:
            if other!=net and layer in ls and path.distance(g)<r+spacing-1e-7:return False
        return True
    groups=collections.defaultdict(list)
    for t in segments:
        if t.GetNetname()=='/COL01' and t.GetLayer()==pcbnew.F_Cu:continue # preserves LED-power zone neck
        if t.GetNetname() in ['/GND','/LED_5V','/USB_N','/USB_P','/USB_DM','/USB_DP','/XIN','/XOUT','/XTAL_OUT']:continue
        if controller_only and not (min(t.GetStart().x,t.GetEnd().x)>pcbnew.FromMM(399) and max(t.GetStart().y,t.GetEnd().y)<pcbnew.FromMM(26)):continue
        groups[t.GetNetCode(),t.GetLayer(),t.GetWidth()].append(t)
    changed=0;removed=0;created=0;saved=0;held=[]
    def pt(v):return v.x,v.y
    for (net,layer,width_nm),group in groups.items():
        width=pcbnew.ToMM(width_nm);adj=collections.defaultdict(list)
        for t in group:
            adj[pt(t.GetStart())].append(t);adj[pt(t.GetEnd())].append(t)
        samepads=[g for n,ls,g in pads if n==net and layer in ls]
        samevias=[(xy(v.GetPosition()),pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))/2) for v in vias if v.GetNetCode()==net]
        protected=set()
        for p,ts in adj.items():
            point=Point(p[0]/1e6,p[1]/1e6)
            if len(ts)!=2 or any(point.distance(g)<width/2+.001 for g in samepads) or any(point.distance(Point(v))<r+width/2+.001 for v,r in samevias):protected.add(p)
        # Keep mid-span electrical junctions, including tiny grid-to-legacy offsets.
        allsame=[t for t in segments if t.GetNetCode()==net and t.GetLayer()==layer]
        for t in group:
            line=LineString([xy(t.GetStart()),xy(t.GetEnd())]);length=line.length
            # A pad may join the middle of a segment, without an endpoint there.
            # Preserve the entire segment in that case so pull-tight cannot open it.
            if any(line.distance(g)<width/2+.001 for g in samepads):
                protected.update([pt(t.GetStart()),pt(t.GetEnd())])
            for p,ts in adj.items():
                if any(o.m_Uuid.AsString()==t.m_Uuid.AsString() for o in ts):continue
                q=Point(p[0]/1e6,p[1]/1e6);d=line.project(q)
                if .001<d<length-.001 and (q.distance(line)<.00001 or (len(ts)!=2 and q.distance(line)<width+.001)):
                    protected.update([pt(t.GetStart()),pt(t.GetEnd()),p])
            for v,r in samevias:
                q=Point(v);d=line.project(q)
                if .001<d<length-.001 and q.distance(line)<r+width/2:protected.update([pt(t.GetStart()),pt(t.GetEnd())])
            for other in allsame:
                if other.GetWidth()==width_nm:continue
                for v in [other.GetStart(),other.GetEnd()]:
                    q=Point(xy(v));d=line.project(q)
                    if -.001<d<length+.001 and q.distance(line)<(width+pcbnew.ToMM(other.GetWidth()))/2+.001:
                        protected.update([pt(t.GetStart()),pt(t.GetEnd())])
        visited=set()
        for start in sorted(protected):
            for first in adj[start]:
                if first.m_Uuid.AsString() in visited:continue
                chain=[];points=[(start[0]/1e6,start[1]/1e6)];at=start;t=first
                while True:
                    uid=t.m_Uuid.AsString()
                    if uid in visited:break
                    visited.add(uid);chain.append(t);end=pt(t.GetEnd()) if pt(t.GetStart())==at else pt(t.GetStart());points.append((end[0]/1e6,end[1]/1e6))
                    if end in protected:break
                    nexts=[o for o in adj[end] if o.m_Uuid.AsString()!=uid]
                    if len(nexts)!=1:break
                    at=end;t=nexts[0]
                if len(chain)<2:continue
                oldlength=sum(math.dist(a,c) for a,c in zip(points,points[1:]));new=[points[0]];i=0
                # Furthest collision-free visible vertex, with at most one 45-degree bend.
                while i<len(points)-1:
                    best=None
                    for j in range(len(points)-1,i,-1):
                        options=[p for p in alternatives(points[i],points[j]) if clear(p,net,layer,width)]
                        if options:
                            best=min(options,key=lambda p:(len(p),sum(math.dist(a,c) for a,c in zip(p,p[1:]))));break
                    if best is None:j=i+1;best=[points[i],points[j]]
                    new.extend(best[1:]);i=j
                # Remove exactly collinear joins introduced at visibility vertices.
                compact=[]
                for p in new:
                    while len(compact)>1:
                        a,c=compact[-2:];cross=(c[0]-a[0])*(p[1]-c[1])-(c[1]-a[1])*(p[0]-c[0])
                        if abs(cross)>1e-8:break
                        compact.pop()
                    compact.append(p)
                newlength=sum(math.dist(a,c) for a,c in zip(compact,compact[1:]))
                if len(compact)-1>=len(chain) or newlength>oldlength+.001:continue
                for t in chain:b.Remove(t);held.append(t)
                for a,c in zip(compact,compact[1:]):
                    t=pcbnew.PCB_TRACK(b);t.SetStart(mm(*a));t.SetEnd(mm(*c));t.SetWidth(width_nm);t.SetLayer(layer);t.SetNetCode(net);b.Add(t)
                    added.append((net,{layer},LineString([a,c]).buffer(width/2),.135))
                changed+=1;removed+=len(chain);created+=len(compact)-1;saved+=oldlength-newlength
    return dict(chains_improved=changed,segments_removed=removed,segments_created=created,length_saved_mm=round(saved,4)),held

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--board',type=Path,default=ROOT/(NAME+'.kicad_pcb'));p.add_argument('--controller-only',action='store_true');a=p.parse_args()
    file=a.board.resolve();b=pcbnew.LoadBoard(str(file));result,held=run(b,a.controller_only);pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(file),b);print(json.dumps(result,indent=2))
