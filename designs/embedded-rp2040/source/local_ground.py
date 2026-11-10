#!/usr/bin/env python3
"""Give bottom controller ground pads short returns to adjacent ground planes.
Uses ordinary off-pad masked vias, conservative geometry and mandatory real DRC.
"""
import json,math,subprocess
from pathlib import Path
import pcbnew
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
from generate import ROOT,NAME,xy,mm,track,via
from smooth import alternatives
p=ROOT/(NAME+'.kicad_pcb');rp=ROOT/'validation/drc.json';backup=p.read_bytes();initial=rp.read_bytes()
b=pcbnew.LoadBoard(str(p));tracks=list(b.GetTracks());pads=[p for f in b.GetFootprints() for p in f.Pads()];obstacles=[];holes=[];solder=[]
def bbox(item):
    bb=item.GetBoundingBox();return box(*[pcbnew.ToMM(v) for v in [bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom()]])
for pad in pads:
    g=bbox(pad)
    if pad.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH:holes.append(g)
    elif pad.IsOnLayer(pcbnew.B_Cu) and pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD:solder.append(g)
    if pad.GetNetname()!='/GND':obstacles.append((g,pad.IsOnLayer(pcbnew.B_Cu)))
for t in tracks:
    if t.GetClass()=='PCB_VIA':g=Point(xy(t.GetPosition())).buffer(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2)
    else:g=LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(pcbnew.ToMM(t.GetWidth())/2)
    if t.GetNetname()!='/GND':obstacles.append((g,t.GetClass()=='PCB_VIA' or t.GetLayer()==pcbnew.B_Cu))
ground=[t for t in tracks if t.GetClass()=='PCB_VIA' and t.GetNetname()=='/GND'];new=[];leads=[];unserved=[]
otree=STRtree([g for g,_ in obstacles]);htree=STRtree(holes);stree=STRtree(solder)
existing_segments={tuple(sorted((xy(t.GetStart()),xy(t.GetEnd())))) for t in tracks if t.GetClass()=='PCB_TRACK' and t.GetNetname()=='/GND' and t.GetLayer()==pcbnew.B_Cu}
def clearpath(points,width=.2):
    g=LineString(points)
    return all(not obstacles[i][1] or g.distance(obstacles[i][0])>=width/2+.135 for i in otree.query(g.buffer(.65))) and all(g.distance(holes[i])>=width/2+.505 for i in htree.query(g.buffer(.65)))
def clearvia(c,small=False):
    q=Point(c)
    r=.2 if small else .25;dr=.1 if small else .15
    return all(q.distance(obstacles[i][0])>=r+.135 for i in otree.query(q.buffer(.8))) and all(q.distance(holes[i])>=r+.505 for i in htree.query(q.buffer(.8))) and all(q.distance(solder[i])>=dr+.2 for i in stree.query(q.buffer(.5))) and all(q.distance(Point(xy(v.GetPosition())))>=dr+pcbnew.ToMM(v.GetDrillValue())/2+.26 for v in ground)
for f in b.GetFootprints():
    x,y=xy(f.GetPosition())
    if not (399<x<452 and y<26):continue
    for pad in f.Pads():
        if pad.GetNetname()!='/GND' or pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD or pad.GetNumber()=='57':continue
        a=xy(pad.GetPosition());chosen=None;width=.2
        for v in sorted(ground,key=lambda v:math.dist(a,xy(v.GetPosition()))):
            c=xy(v.GetPosition())
            if math.dist(a,c)>1.5:break
            for path in alternatives(a,c):
                if clearpath(path):chosen=path;break
            if chosen:break
        if chosen is None:
            candidates=[(a[0]+dx*d,a[1]+dy*d) for d in [.7,.8,.9,1,1.1,1.2,1.3,1.4] for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)] if math.hypot(dx*d,dy*d)<=1.5]
            candidates+=sorted([(round(a[0]+dx*.1,6),round(a[1]+dy*.1,6)) for dx in range(-15,16) for dy in range(-15,16) if .6<math.hypot(dx*.1,dy*.1)<=1.5],key=lambda c:math.dist(a,c))
            for small in [False,True]:
                width=.127 if small else .2
                for c in candidates:
                    if not clearvia(c,small):continue
                    for path in alternatives(a,c):
                        if clearpath(path,width):chosen=path;break
                    if chosen:
                        v=via(b,'GND',*c)
                        if small:v.SetWidth(pcbnew.FromMM(.4));v.SetDrill(pcbnew.FromMM(.2))
                        v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED);ground.append(v);new.append({'position':c,'drill_mm':.2 if small else .3});break
                if chosen:break
        if chosen:
            for a,c in zip(chosen,chosen[1:]):
                key=tuple(sorted((tuple(round(v,6) for v in a),tuple(round(v,6) for v in c))))
                if math.dist(a,c)>.001 and key not in existing_segments:track(b,'GND',a,c,pcbnew.B_Cu,width);existing_segments.add(key)
            leads.append(f'{f.GetReference()}.{pad.GetNumber()}')
        else:unserved.append(f'{f.GetReference()}.{pad.GetNumber()}')
held=[]
for t in tracks:
    if t.GetClass()!='PCB_TRACK' or t.GetNetname()!='/GND':continue
    a,c=xy(t.GetStart()),xy(t.GetEnd())
    if min(a[0],c[0])<399 or max(a[1],c[1])>=26 or t.GetLength()<=pcbnew.FromMM(1.6):continue
    if t.GetWidth()>=pcbnew.FromMM(.4) and min(a[0],c[0])>425 and max(a[0],c[0])<431 and max(a[1],c[1])<12:continue
    held.append(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(p),b)
subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',str(rp),str(p)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
r=json.loads(rp.read_text());result={'new_ground_vias':new,'short_ground_returns':leads,'no_clear_short_return':unserved,'unconnected':len(r['unconnected_items']),'violations':len(r['violations'])}
Path('/tmp/opencode/cleaver-embedded/local-ground-development.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if r['unconnected_items'] or r['schematic_parity'] or any(v['type'] not in ['track_dangling','via_dangling'] for v in r['violations']):
    p.write_bytes(backup);rp.write_bytes(initial);raise RuntimeError('Ground edit needs adjustment; restored board')
removed=0
for t in held:
    b.Remove(t);pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(p),b)
    subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',str(rp),str(p)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    r=json.loads(rp.read_text())
    if r['unconnected_items'] or r['schematic_parity'] or any(v['type'] not in ['track_dangling','via_dangling'] for v in r['violations']):b.Add(t)
    else:removed+=1
    print('Ground route removal',removed,'/',len(held),flush=True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(p),b)
subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',str(rp),str(p)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
r=json.loads(rp.read_text());result.update(long_ground_segments_removed=removed,unconnected=len(r['unconnected_items']),violations=len(r['violations']))
Path('/tmp/opencode/cleaver-embedded/local-ground-development.json').write_text(json.dumps(result,indent=2)+'\n')
