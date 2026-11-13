#!/usr/bin/env python3
"""Migrate rev0.6 copper to J1/J2; retain copper outside the socket escapes.

Uses clearance-aware octilinear local routing, NOT relaxed DRC exclusions.
Run the full checker before accepting the result or archiving its copper.
Normal subsequent generation imports routing/Cleaver.ses directly.
"""
import argparse
import csv
import heapq
import itertools
import json
import math
from pathlib import Path
import tempfile
import subprocess
import sys

import pcbnew
from shapely import LineString, Point, STRtree, unary_union

from archive_routing import archive
from assembly_parts import fields
from clean_routing import Obstacles, candidates, compact, pad_shape, xy
from design import ROOT, components, read_keys
from generate_kicad import (FP_NAMES, generate_board, generate_schematic, mm,
                           schematic_nets, update_netclasses, write_footprints)

LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)


def already_connected(board, pad, target, target_layer):
    """Flood actual same-net copper, including mid-segment joins and vias."""
    shapes=[]; layers=[]; bridges={}
    for item in board.GetTracks():
        if item.GetNetCode()!=pad.GetNetCode():continue
        if item.GetClass()=='PCB_VIA':
            shape=Point(xy(item.GetPosition())).buffer(item.GetWidth(pcbnew.F_Cu)/2e6+.00001)
            group=[]
            for layer in LAYERS:
                group.append(len(shapes));shapes.append(shape);layers.append(layer)
            for index in group:bridges[index]=group
        else:
            shapes.append(LineString([xy(item.GetStart()),xy(item.GetEnd())]).buffer(item.GetWidth()/2e6+.00001))
            layers.append(item.GetLayer())
    start_shape=pad_shape(pad).buffer(.00001)
    shapes.append(start_shape);layers.append(pcbnew.B_Cu)
    trees={l:STRtree([s if layers[i]==l else Point() for i,s in enumerate(shapes)]) for l in LAYERS}
    visited={len(shapes)-1};queue=list(visited)
    while queue:
        i=queue.pop()
        if layers[i]==target_layer and shapes[i].distance(Point(target))<.00002:return True
        for j in [*trees[layers[i]].query(shapes[i],predicate='intersects'), *bridges.get(i,[])]:
            j=int(j)
            if j not in visited:visited.add(j);queue.append(j)
    return False


def escape(board, pad, target, target_layer, width):
    """Route pad to one severed legacy landing on a local 0.1mm, 3-layer grid."""
    to_plane=target is None
    if not to_plane and already_connected(board,pad,target,target_layer):return
    net = pad.GetNet()
    obstacle = {l:Obstacles(board, net.GetNetCode(), l, width) for l in LAYERS}
    via_width = .8 if width == .6 else .6
    via_obstacle = {l:Obstacles(board, net.GetNetCode(), l, via_width) for l in LAYERS}
    solder_lands = [pad_shape(p) for f in board.GetFootprints() for p in f.Pads()
                    if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
    drill_radius=.2 if width==.6 else .15
    solder_tree=STRtree([s.buffer(drill_radius+.055,join_style='mitre') for s in solder_lands])
    # np hole is directly above/below its staggered pad.
    px,py = xy(pad.GetPosition())
    origin = (px, py-round((py-pad.GetParentFootprint().GetPosition().y/1e6)/1.7)*1.7)
    def point(node):return (round(origin[0]+node[0]*.1,6),round(origin[1]+node[1]*.1,6))
    start = (0,round((py-origin[1])*10),pcbnew.B_Cu)
    endpoints = {}
    tx,ty = (0,0) if to_plane else (round((target[i]-origin[i])*10) for i in (0,1))
    for dx,dy in ([] if to_plane else itertools.product(range(-2,3),repeat=2)):
        node = (tx+dx,ty+dy,target_layer)
        for path in candidates(point(node),target):
            if all(obstacle[target_layer].clear(a,b) for a,b in zip(path,path[1:])):
                endpoints[node]=path
                break
    assert to_plane or endpoints, f'No grid access to {target} {board.GetLayerName(target_layer)}'
    def heuristic(node):return 0 if to_plane else math.dist(point(node),target)
    costs={start:0}; previous={}; queue=[(heuristic(start),0,start)]
    via_cache={}
    while queue:
        _,cost,node=heapq.heappop(queue)
        if cost!=costs[node]:continue
        if (to_plane and node[2]==pcbnew.F_Cu) or node in endpoints:break
        a=point(node)
        moves=[(node[0]+dx,node[1]+dy,node[2])
               for dx,dy in itertools.product((-1,0,1),repeat=2) if dx or dy]
        moves += [(node[0],node[1],l) for l in LAYERS if l!=node[2]]
        for nxt in moves:
            b=point(nxt)
            if abs(nxt[0])>max(65,abs(tx)+20) or abs(nxt[1])>max(65,abs(ty)+20):continue
            if nxt[2]!=node[2]:
                key=nxt[:2]
                if key not in via_cache:
                    # A plated escape via is distinct from the unplated pin
                    # entry. Its drill stays outside ALL exposed solder lands.
                    via_cache[key]=(all(via_obstacle[l].clear(a,(a[0]+.000001,a[1])) for l in LAYERS)
                        and not len(solder_tree.query(Point(a),predicate='intersects')))
                if not via_cache[key]:continue
                step=2.0
            else:
                if not obstacle[node[2]].clear(a,b):continue
                step=math.dist(a,b)
            score=cost+step
            if score+1e-8>=costs.get(nxt,float('inf')):continue
            costs[nxt]=score; previous[nxt]=node
            heapq.heappush(queue,(score+heuristic(nxt),score,nxt))
    else:
        raise RuntimeError(f'No local route: {pad.GetParentFootprint().GetReference()}.{pad.GetNumber()} -> {target}')
    route=[node]
    while route[-1]!=start:route.append(previous[route[-1]])
    route.reverse()
    segments=[]; chunk=[point(route[0])]; layer=start[2]
    for a,b in zip(route,route[1:]):
        if a[2]!=b[2]:
            segments.append((layer,compact(chunk)));chunk=[point(b)];layer=b[2]
            via=pcbnew.PCB_VIA(board);via.SetPosition(mm(*point(b)))
            via.SetWidth(pcbnew.FromMM(via_width));via.SetDrill(pcbnew.FromMM(.4 if width==.6 else .3))
            via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetNet(net);board.Add(via)
        else:chunk.append(point(b))
    segments.append((layer,compact(chunk+endpoints.get(node,[point(node)])[1:])))
    for layer,path in segments:
        for a,b in zip(path,path[1:]):
            track=pcbnew.PCB_TRACK(board);track.SetStart(mm(*a));track.SetEnd(mm(*b))
            track.SetLayer(layer);track.SetWidth(pcbnew.FromMM(width));track.SetNet(net);board.Add(track)


def migrate(board):
    sockets=[f for f in board.GetFootprints() if f.GetReference() in ('J1','J2')]
    holes=[Point(xy(p.GetPosition())) for f in sockets for p in f.Pads()
           if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH]
    pads=[p for f in sockets for p in f.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
    ports=[];removed=0
    # Clip every affected segment against the REAL hole and new land pattern;
    # do not assume the old PTH endpoint is still an electrical connection.
    for item in list(board.GetTracks()):
        via=item.GetClass()=='PCB_VIA'
        width=pcbnew.ToMM(item.GetWidth(pcbnew.F_Cu) if via else item.GetWidth())
        cuts=[h.buffer(.5+.275+width/2,quad_segs=32) for h in holes]
        if via or item.GetLayer()==pcbnew.B_Cu:
            cuts += [pad_shape(p).buffer(.225+width/2,quad_segs=8) for p in pads if p.GetNetCode()!=item.GetNetCode()]
        cut=unary_union(cuts)
        if via:
            if cut.intersects(Point(xy(item.GetPosition()))):board.Remove(item);removed+=1
            continue
        line=LineString([xy(item.GetStart()),xy(item.GetEnd())])
        if not line.intersects(cut):continue
        board.Remove(item);removed+=1
        remaining=line.difference(cut)
        pieces=[] if remaining.is_empty else [remaining] if remaining.geom_type=='LineString' else list(remaining.geoms)
        for piece in pieces:
            a,b=piece.coords[0],piece.coords[-1]
            if math.dist(a,b)<.0002:continue
            track=pcbnew.PCB_TRACK(board);track.SetStart(mm(*a));track.SetEnd(mm(*b))
            track.SetWidth(pcbnew.FromMM(width));track.SetLayer(item.GetLayer());track.SetNet(item.GetNet());board.Add(track)
            for point in (a,b):
                if min(math.dist(point,xy(item.GetStart())),math.dist(point,xy(item.GetEnd())))>.0001:
                    ports.append((item.GetNetname(),point,item.GetLayer(),width))
    # Remove duplicate cut ports (legacy micro-segments sometimes coincide).
    unique={ (n,round(p[0],5),round(p[1],5),l):(n,p,l,w) for n,p,l,w in ports }
    for net,target,layer,width in sorted(unique.values()):
        matching=[p for p in pads if p.GetNetname()==net]
        assert matching, f'Unexpected unrelated copper affected: {net}'
        pad=min(matching,key=lambda p:math.dist(xy(p.GetPosition()),target))
        print('Escape',net,tuple(round(v,4) for v in target),board.GetLayerName(layer),flush=True)
        escape(board,pad,target,layer,width)
    pcbnew.SaveBoard('/tmp/opencode/cleaver-rev07-signal-escapes.kicad_pcb',board)
    # Each ground socket needs real inner-plane access. The old PTH barrels
    # no longer exist. Reaching ANY free F.Cu grid point forces a through-via.
    for pad in pads:
        if pad.GetNetname()!='/GND':continue
        escape(board,pad,None,pcbnew.F_Cu,.3)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    return dict(removed_copper_items=removed,severed_ports=len(unique))


def retain_baseline_items(baseline, generated, nets):
    """Keep unrelated footprints, drawings and copper UUIDs from rev0.6."""
    fps={f.GetReference():f for f in baseline.GetFootprints()}
    # Rename the old no-connect nets before removing U1's plated pads.
    for pad in fps['U1'].Pads():
        expected=nets[('U1',pad.GetNumber())]
        if pad.GetNetname()!=expected:
            assert pad.GetNetname().startswith('unconnected-(U1-')
            pad.GetNet().SetNetname(expected)
    netmap={p.GetNetname():p.GetNet() for f in baseline.GetFootprints() for p in f.Pads() if p.GetNumber()}
    baseline.Remove(fps['U1'])
    for fp in generated.GetFootprints():
        if fp.GetReference() not in ('U1','J1','J2'):continue
        duplicate=pcbnew.Cast_to_FOOTPRINT(fp.Duplicate(False))
        duplicate.SetParent(baseline)
        baseline.Add(duplicate)
        for pad in duplicate.Pads():
            if pad.GetNumber():pad.SetNet(netmap[nets[(fp.GetReference(),pad.GetNumber())]])
    baseline.GetTitleBlock().SetRevision('0.7')
    baseline.GetTitleBlock().SetDate('2026-11-12')
    baseline.GetTitleBlock().SetTitle('Cleaver - socketed RP2040-Plus / 117 keys')
    for drawing in baseline.GetDrawings():
        if drawing.GetClass()=='PCB_TEXT' and drawing.GetText()=='CLEAVER rev0.6 | RP2040-PLUS | BOTTOM SMT':
            drawing.SetText('CLEAVER rev0.7 | SOCKETED RP2040-PLUS')
    return baseline


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline',type=Path)
    args=parser.parse_args()
    baseline=pcbnew.LoadBoard(str(args.baseline))
    assert baseline.GetTitleBlock().GetRevision()=='0.6'
    with tempfile.TemporaryDirectory(dir='/tmp/opencode',prefix='cleaver-rev07-') as temp:
        report=Path(temp)
        archive(baseline,report/'baseline.ses')
        keys,leds=read_keys();parts=components(keys,leds)
        write_footprints();update_netclasses();generate_schematic(parts,keys,leds)
        nets=schematic_nets(report)
        generate_board(parts,keys,nets,report,report/'baseline.ses')
    generated=pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
    # Reload the baseline under the project's path to apply the same rules.
    (ROOT/'Cleaver.kicad_pcb').write_bytes(args.baseline.read_bytes())
    board=retain_baseline_items(pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb')),generated,nets)
    result=migrate(board)
    pcbnew.SaveBoard(str(ROOT/'Cleaver.kicad_pcb'),board)
    subprocess.run([sys.executable,'-B',str(ROOT/'source/finalize_rev07.py'),str(args.baseline)],check=True)
    with (ROOT/'manufacturing/BOM.csv').open('w',newline='') as file:
        writer=csv.writer(file,lineterminator='\n')
        writer.writerow(['reference','value','footprint','x_mm','y_mm','side','Manufacturer','MPN','LCSC','Key'])
        for p in parts:
            data=fields(p)
            writer.writerow([p['ref'],p['value'],FP_NAMES.get(p['kind'],p['kind']),p['x'],p['y'],'B' if p['back'] else 'F',
                             *[data.get(k,'') for k in ('Manufacturer','MPN','LCSC','Key')]])
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
