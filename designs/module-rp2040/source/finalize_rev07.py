#!/usr/bin/env python3
"""Finish the one-time socket migration without changing fabrication rules.

Restore layer joins whose old vias conflict with new socket lands, enforce
rectangular via-drill/solder-land margins, relocate silk, and trim only dangling
ends identified by fresh KiCad DRC. Normal regeneration uses the checked SES.
"""
import argparse
from collections import defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import sys

import pcbnew
from shapely import LineString, Point

from clean_routing import Obstacles, candidates, pad_shape, xy
from design import ROOT
from generate_kicad import mm

LAYERS=(pcbnew.F_Cu,pcbnew.In2_Cu,pcbnew.B_Cu)


def restore_via(board,original,present):
    net=board.FindNet(original.GetNetname());old=xy(original.GetPosition())
    radius=original.GetWidth(pcbnew.F_Cu)/2e6
    contacts=[]
    for item in board.GetTracks():
        if item.GetClass()!='PCB_TRACK' or item.GetNetname()!=original.GetNetname():continue
        line=LineString([xy(item.GetStart()),xy(item.GetEnd())])
        if line.distance(Point(old))>radius+item.GetWidth()/2e6+.00001:continue
        point=line.interpolate(line.project(Point(old)))
        contacts.append((item.GetLayer(),tuple(point.coords[0]),item.GetWidth()/1e6))
    if not contacts:return False
    lands=[p.GetBoundingBox() for f in board.GetFootprints() for p in f.Pads()
           if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
    for box in lands:box.Inflate(original.GetDrillValue()//2+pcbnew.FromMM(.055))
    obstacle={l:Obstacles(board,net.GetNetCode(),l,original.GetWidth(pcbnew.F_Cu)/1e6) for l in LAYERS}
    track_obstacles={(l,w):Obstacles(board,net.GetNetCode(),l,w) for l,_,w in contacts}
    offsets=sorted(itertools.product(range(-15,16),repeat=2),key=lambda p:(p[0]**2+p[1]**2,p))
    for dx,dy in offsets:
        point=(round(old[0]+dx*.1,6),round(old[1]+dy*.1,6))
        if any(box.Contains(mm(*point)) for box in lands):continue
        if not all(obstacle[l].clear(point,(point[0]+.000001,point[1])) for l in LAYERS):continue
        paths=[]
        for layer,start,width in contacts:
            path=next((p for p in candidates(start,point)
                       if all(track_obstacles[(layer,width)].clear(a,b) for a,b in zip(p,p[1:]))),None)
            if path is None:break
            paths.append((layer,width,path))
        else:
            if present:
                via=original
            else:
                via=pcbnew.PCB_VIA(board);via.SetWidth(original.GetWidth(pcbnew.F_Cu))
                via.SetDrill(original.GetDrillValue());via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
                via.SetNet(net);board.Add(via)
            via.SetPosition(mm(*point))
            for layer,width,path in paths:
                for a,b in zip(path,path[1:]):
                    if math.dist(a,b)<.00001:continue
                    track=pcbnew.PCB_TRACK(board);track.SetStart(mm(*a));track.SetEnd(mm(*b))
                    track.SetWidth(pcbnew.FromMM(width));track.SetLayer(layer);track.SetNet(net);board.Add(track)
            print('Via join',original.GetNetname(),old,'->',point,flush=True)
            return True
    if present:raise RuntimeError(f'Cannot move solder-adjacent via at {old}')
    return False  # old vias inside new NPTHs were intentionally replaced


def trim_dangling(board,track):
    """Keep the span of real contacts; never delete a multi-branch trunk."""
    line=LineString([xy(track.GetStart()),xy(track.GetEnd())]);stations=[]
    for item in board.GetTracks():
        if (item.GetClass()!='PCB_TRACK' or item.GetNetCode()!=track.GetNetCode()
                or item.GetLayer()!=track.GetLayer() or item.m_Uuid.AsString()==track.m_Uuid.AsString()):continue
        common=line.intersection(LineString([xy(item.GetStart()),xy(item.GetEnd())]))
        if not common.is_empty:stations.append(line.project(common.centroid))
    if len(stations)>=2 and max(stations)-min(stations)>.0001 and (
            min(stations)>.00001 or line.length-max(stations)>.00001):
        track.SetStart(mm(*line.interpolate(min(stations)).coords[0]))
        track.SetEnd(mm(*line.interpolate(max(stations)).coords[0]))
        return
    if trim_dangling_chain(board,track):return
    stations=[]
    width=track.GetWidth()/1e6
    if line.length<.5:
        # These are redundant end slivers of the replaced local escape, not
        # useful trunks. Fresh DRC below must still show zero missing nets.
        board.Remove(track);return
    for item in board.GetTracks():
        if item.m_Uuid.AsString()==track.m_Uuid.AsString() or item.GetNetCode()!=track.GetNetCode():continue
        if item.GetClass()=='PCB_VIA':
            point=Point(xy(item.GetPosition()))
            if line.distance(point)<=width/2+item.GetWidth(pcbnew.F_Cu)/2e6+.00001:
                stations.append(line.project(point))
        elif item.GetLayer()==track.GetLayer():
            other=LineString([xy(item.GetStart()),xy(item.GetEnd())])
            contact=line.intersection(other.buffer(width/2+item.GetWidth()/2e6+.00001))
            if not contact.is_empty:
                stations.append(line.project(contact.centroid))
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH or pad.GetNetCode()!=track.GetNetCode() or not pad.IsOnLayer(track.GetLayer()):continue
            if line.intersects(pad_shape(pad).buffer(width/2+.00001)):
                stations.append(line.project(Point(xy(pad.GetPosition()))))
    if len(stations)<2 or max(stations)-min(stations)<.0001:
        board.Remove(track);return
    track.SetStart(mm(*line.interpolate(min(stations)).coords[0]))
    track.SetEnd(mm(*line.interpolate(max(stations)).coords[0]))


def trim_dangling_chain(board,track):
    """Prune a whole segmented dead end, stopping at its first real junction."""
    tracks=[t for t in board.GetTracks() if t.GetClass()=='PCB_TRACK'
            and t.GetNetCode()==track.GetNetCode() and t.GetLayer()==track.GetLayer()]
    graph=defaultdict(list)
    def key(p):return (p.x,p.y)
    for item in tracks:
        for point in (item.GetStart(),item.GetEnd()):graph[key(point)].append(item)
    terminals=[p for p in (track.GetStart(),track.GetEnd()) if len(graph[key(p)])==1]
    if not terminals:return False
    pads=[p for f in board.GetFootprints() for p in f.Pads()
          if p.GetNetCode()==track.GetNetCode() and p.IsOnLayer(track.GetLayer())
          and p.GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH]
    vias=[t for t in board.GetTracks() if t.GetClass()=='PCB_VIA' and t.GetNetCode()==track.GetNetCode()]
    def terminal_contact(point):
        q=Point(xy(point))
        return (any(pad_shape(p).distance(q)<track.GetWidth()/2e6 for p in pads)
                or any(q.distance(Point(xy(v.GetPosition())))<(v.GetWidth(pcbnew.F_Cu)+track.GetWidth())/2e6 for v in vias))
    start=next((p for p in terminals if not terminal_contact(p)),None)
    if start is None:return False
    end=key(start);chain=[];seen=set()
    while True:
        options=[t for t in graph[end] if t.m_Uuid.AsString() not in seen]
        if len(options)!=1:break
        item=options[0];seen.add(item.m_Uuid.AsString())
        a=item.GetStart() if key(item.GetStart())==end else item.GetEnd()
        b=item.GetEnd() if key(item.GetStart())==end else item.GetStart()
        # This one-time migration must never prune unrelated legacy routing.
        if not all(398<=p.x/1e6<=452.4375 and 0<=p.y/1e6<=29 for p in (a,b)):break
        chain.append((item,LineString([xy(a),xy(b)])))
        end=key(b)
        if len(graph[end])!=2 or terminal_contact(b):break
    if not chain:return False
    chain_ids={t.m_Uuid.AsString() for t,_ in chain}
    other=[LineString([xy(t.GetStart()),xy(t.GetEnd())]) for t in tracks
           if t.m_Uuid.AsString() not in chain_ids]
    # Centreline intersections identify exact T/cross junctions; pad/via
    # projections identify terminal contacts. Copper overlap alone is not
    # used to leave another uncentred dangling endpoint.
    for index,(item,line) in enumerate(chain):
        contacts=[]
        for shape in other:
            common=line.intersection(shape)
            if not common.is_empty:contacts.append(line.project(common.centroid))
        for pad in pads:
            if line.intersects(pad_shape(pad)):
                contacts.append(line.project(Point(xy(pad.GetPosition()))))
        for via in vias:
            q=Point(xy(via.GetPosition()))
            if line.distance(q)<=via.GetWidth(pcbnew.F_Cu)/2e6:
                contacts.append(line.project(q))
        if not contacts:continue
        distance=min(contacts)
        for previous,_ in chain[:index]:board.Remove(previous)
        if line.length-distance<.00001:board.Remove(item)
        else:
            item.SetStart(mm(*line.interpolate(distance).coords[0]))
            item.SetEnd(mm(*line.coords[-1]))
        print('Trim segmented branch',track.GetNetname(),index,'segments to junction',flush=True)
        return True
    return False


def prepare(board,baseline):
    # Retry-safe: retain legacy identities and eliminate only duplicate NEW
    # copper (e.g. an interrupted migration's already-restored via join).
    legacy={t.m_Uuid.AsString() for t in baseline.GetTracks()}
    groups={}
    for item in board.GetTracks():
        if item.GetClass()=='PCB_VIA':
            key=('via',item.GetNetname(),xy(item.GetPosition()),item.GetWidth(pcbnew.F_Cu),item.GetDrillValue())
        else:
            key=('track',item.GetNetname(),item.GetLayer(),item.GetWidth(),tuple(sorted((xy(item.GetStart()),xy(item.GetEnd())))))
        groups.setdefault(key,[]).append(item)
    for items in groups.values():
        if len(items)<2:continue
        retained=[t for t in items if t.m_Uuid.AsString() in legacy]
        if not retained:retained=[min(items,key=lambda t:t.m_Uuid.AsString())]
        keep={t.m_Uuid.AsString() for t in retained}
        for item in items:
            if item.m_Uuid.AsString() not in keep:board.Remove(item)
    fps={f.GetReference():f for f in board.GetFootprints()}
    for ref,y in [('J1',8),('J2',18.5)]:
        fp=fps[ref];fp.Reference().SetPosition(mm(425.7675,y))
        for text in fp.GraphicalItems():
            if text.GetClass()=='PCB_TEXT' and text.GetText()=='1 / USB':
                text.SetTextSize(mm(.8,.8));text.SetTextThickness(pcbnew.FromMM(.12))
    for text in board.GetDrawings():
        if text.GetClass()=='PCB_TEXT' and text.GetText()=='TP1 VBUS TEST +':text.SetPosition(mm(442,28.7))
    ids={t.m_Uuid.AsString() for t in board.GetTracks()}
    for old in baseline.GetTracks():
        if old.GetClass()!='PCB_VIA' or old.m_Uuid.AsString() in ids:continue
        # Recognize joins restored by earlier versions of this one-time tool.
        nearby=[v for v in board.GetTracks() if v.GetClass()=='PCB_VIA' and v.GetNetname()==old.GetNetname()
                and math.dist(xy(v.GetPosition()),xy(old.GetPosition()))<1.5]
        if nearby and old.GetNetname() in ('/COL04','/RAW_USB_5V'):
            continue
        else:restore_via(board,old,False)
    smd=[p for f in board.GetFootprints() for p in f.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
    for via in list(board.GetTracks()):
        if via.GetClass()!='PCB_VIA':continue
        bad=False
        for pad in smd:
            if pad.GetNetCode()!=via.GetNetCode():continue
            box=pad.GetBoundingBox();box.Inflate(via.GetDrillValue()//2+pcbnew.FromMM(.05))
            bad |= box.Contains(via.GetPosition())
        if bad:restore_via(board,via,True)
    path=ROOT/'Cleaver.kicad_pcb'
    pcbnew.SaveBoard(str(path),board)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline',type=Path)
    parser.add_argument('--prepare',action='store_true',help=argparse.SUPPRESS)
    parser.add_argument('--prune',type=Path,help=argparse.SUPPRESS)
    parser.add_argument('--fill',action='store_true',help=argparse.SUPPRESS)
    args=parser.parse_args()
    path=ROOT/'Cleaver.kicad_pcb'
    if args.prepare or args.prune or args.fill:
        board=pcbnew.LoadBoard(str(path))
        if args.prepare:
            prepare(board,pcbnew.LoadBoard(str(args.baseline)))
            return
        if args.prune:
            data=json.loads(args.prune.read_text())
            ids={v['items'][0]['uuid'] for v in data['violations'] if v['type']=='track_dangling'}
            targets=[t for t in board.GetTracks() if t.m_Uuid.AsString() in ids]
            for track in targets:trim_dangling(board,track)
        if args.fill:pcbnew.ZONE_FILLER(board).Fill(board.Zones())
        pcbnew.SaveBoard(str(path),board)
        return
    # Isolate each edit/fill pass. Long-lived KiCad 10 / Python 3.14 SWIG
    # processes can invalidate wrapper types after repeated zone rebuilds.
    child=[sys.executable,'-B',str(Path(__file__).resolve()),str(args.baseline)]
    subprocess.run(child+['--prepare'],check=True)
    report=Path('/tmp/opencode/cleaver-rev07-finalize-drc.json')
    previous_hash=None
    for iteration in range(20):
        subprocess.run(['kicad-cli','pcb','drc','--format','json','--refill-zones','--all-track-errors',
                        '--schematic-parity','--severity-all','-o',str(report),str(path)],check=True)
        data=json.loads(report.read_text())
        dangling={v['items'][0]['uuid'] for v in data['violations'] if v['type']=='track_dangling'}
        if not dangling:
            assert not data['violations'] and not data['unconnected_items'] and not data['schematic_parity'], report
            subprocess.run(child+['--fill'],check=True)
            print('PASS: final socket routing, all-severity DRC and schematic parity')
            return
        print('Trim dangling ends:',len(dangling),flush=True)
        assert not data['unconnected_items'], 'Pruning must not break any physical net'
        subprocess.run(child+['--prune',str(report)],check=True)
        current_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        if current_hash==previous_hash:raise RuntimeError('No routing progress; inspect DRC instead of repeating')
        previous_hash=current_hash
    raise RuntimeError('Dangling-track cleanup did not converge; inspect DRC')


if __name__=='__main__':main()
