#!/usr/bin/env python3
"""Prune/trim dangling copper with a fresh connectivity/DRC rollback per edit.
A dangling track may carry a live mid-span junction: never delete it blindly.
"""
import json,subprocess
import pcbnew
from shapely.geometry import Point,LineString,box
from generate import ROOT,NAME,xy,mm
file=ROOT/(NAME+'.kicad_pcb');report=ROOT/'validation/drc.json'
lifetimes=[]
def load():
    b=pcbnew.LoadBoard(str(file));items=list(b.GetTracks());lifetimes.append((b,items));return b,items
def drc():
    subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',str(report),str(file)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    return json.loads(report.read_text())
def good(r):return not r['unconnected_items'] and not r['schematic_parity'] and all(v['type'] in ['track_dangling','via_dangling'] for v in r['violations'])
r=json.loads(report.read_text());assert good(r)
for iteration in range(30):
    ids={i['uuid'] for v in r['violations'] for i in v['items']};progress=0
    for uid in ids:
        backup=file.read_bytes();previous=report.read_bytes()
        b,held=load();t=next((t for t in held if t.m_Uuid.AsString()==uid),None)
        if t is None:continue
        b.Remove(t);pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(file),b);trial=drc()
        if good(trial):r=trial;progress+=1;continue
        file.write_bytes(backup);report.write_bytes(previous)
        if t.GetClass()!='PCB_TRACK':continue
        b,held2=load();t=next(t for t in held2 if t.m_Uuid.AsString()==uid)
        line=LineString([xy(t.GetStart()),xy(t.GetEnd())]);contacts=[]
        for o in held2:
            if o.m_Uuid.AsString()==uid or o.GetNetCode()!=t.GetNetCode():continue
            if o.GetClass()=='PCB_VIA':g=Point(*xy(o.GetPosition())).buffer(pcbnew.ToMM(o.GetWidth(pcbnew.F_Cu))/2)
            elif o.GetLayer()==t.GetLayer():g=LineString([xy(o.GetStart()),xy(o.GetEnd())]).buffer(pcbnew.ToMM(o.GetWidth())/2)
            else:continue
            inter=line.intersection(g)
            if not inter.is_empty:
                for part in inter.geoms if hasattr(inter,'geoms') else [inter]:contacts.extend(line.project(Point(c)) for c in part.coords)
        for f in b.GetFootprints():
            for p in f.Pads():
                if p.GetNetCode()!=t.GetNetCode() or not p.IsOnLayer(t.GetLayer()):continue
                bb=p.GetBoundingBox();inter=line.intersection(box(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom())))
                if not inter.is_empty:
                    for part in inter.geoms if hasattr(inter,'geoms') else [inter]:contacts.extend(line.project(Point(c)) for c in part.coords)
        if not contacts:continue
        lo,hi=min(contacts),max(contacts)
        if hi-lo<.04:continue
        # End inside the connecting copper, not merely tangent to its boundary.
        t.SetStart(mm(*line.interpolate(lo+.01).coords[0]));t.SetEnd(mm(*line.interpolate(hi-.01).coords[0]))
        pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(file),b);trial=drc()
        if good(trial) and len(trial['violations'])<len(r['violations']):r=trial;progress+=1
        else:file.write_bytes(backup);report.write_bytes(previous)
    print('Prune pass',iteration,'accepted',progress,'remaining',len(r['violations']),flush=True)
    if not progress or not r['violations']:break
