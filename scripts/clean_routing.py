#!/usr/bin/env python3
"""Simplify Cleaver routing into clearance-checked straight/45-degree runs.

Requires KiCad Python and Shapely >=2. Preserves widths, layers, vias, pads and
branch contacts. Writes a candidate board; run the full KiCad checker before
accepting it or updating the complete-copper routing archive. Filled zones are
rebuilt, not treated as immutable obstacles.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path

import pcbnew
from shapely import LineString, Point, STRtree, box

from design import BOARD_H, BOARD_W, MOUNTING_HOLES

LAYERS = (pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu)
CLEARANCE = .205  # 0.2 mm design minimum plus numerical allowance.


def xy(point):
    return (point.x / 1e6, point.y / 1e6)


def bounds(item):
    rect = item.GetBoundingBox()
    return box(rect.GetX()/1e6, rect.GetY()/1e6,
               rect.GetRight()/1e6, rect.GetBottom()/1e6)


def pad_shape(pad):
    if pad.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
        return Point(xy(pad.GetPosition())).buffer(pad.GetSize().x/2e6, quad_segs=32)
    # A conservative envelope also covers roundrect and oval pads.
    return bounds(pad)


def runs(tracks, anchors):
    """Maximal same-width chains ending at every branch or anchored contact."""
    adjacent = defaultdict(list)
    for index, track in enumerate(tracks):
        for p in (track.GetStart(), track.GetEnd()):
            adjacent[(p.x, p.y)].append(index)
    stops = set(anchors)
    for p, edges in adjacent.items():
        if len(edges) != 2 or tracks[edges[0]].GetWidth() != tracks[edges[1]].GetWidth():
            stops.add(p)
    visited = set()
    result = []
    for index, track in enumerate(tracks):
        if index in visited:
            continue
        ends = [(p.x, p.y) for p in (track.GetStart(), track.GetEnd())]
        # First traverse from a known stop; pure cycles are retained unchanged.
        if not any(p in stops for p in ends):
            continue
        start = next(p for p in ends if p in stops)
        points, edges, current = [start], [], index
        while current not in visited:
            visited.add(current); edges.append(current)
            t = tracks[current]
            a, b = (t.GetStart().x, t.GetStart().y), (t.GetEnd().x, t.GetEnd().y)
            end = b if a == points[-1] else a
            points.append(end)
            if end in stops:
                break
            current = next(i for i in adjacent[end] if i != current)
        result.append((edges, [(x/1e6, y/1e6) for x, y in points]))
    return result


def anchored_runs(tracks, contacts):
    """Protect pad/via landings and contacts between independent chains."""
    anchors = set()
    lines = [LineString([xy(t.GetStart()), xy(t.GetEnd())]) for t in tracks]
    tree = STRtree(lines)
    def anchor(index):
        for p in (tracks[index].GetStart(), tracks[index].GetEnd()):
            anchors.add((p.x, p.y))
    for shape in contacts:
        for index in tree.query(shape, predicate='dwithin', distance=.31):
            radius = tracks[index].GetWidth()/2e6 + .0001
            if shape.distance(lines[index]) <= radius:
                ends = [p for p in (tracks[index].GetStart(), tracks[index].GetEnd())
                        if shape.distance(Point(xy(p))) <= radius]
                if ends:
                    anchors.update((p.x, p.y) for p in ends)
                else:
                    anchor(int(index))
    initial = runs(tracks, anchors)
    owners = {edge: group for group, (edges, _) in enumerate(initial) for edge in edges}
    for i, line in enumerate(lines):
        for j in tree.query(line, predicate='dwithin', distance=.61):
            j = int(j)
            if j <= i or (i in owners and owners[i] == owners.get(j)):
                continue
            if line.distance(lines[j]) > (tracks[i].GetWidth()+tracks[j].GetWidth())/2e6 + .0001:
                continue
            a = {xy(tracks[i].GetStart()), xy(tracks[i].GetEnd())}
            b = {xy(tracks[j].GetStart()), xy(tracks[j].GetEnd())}
            if not a & b:
                anchor(i); anchor(j)
    return runs(tracks, anchors)


class Obstacles:
    def __init__(self, board, net, layer, width):
        shapes, margins = [], []
        def add(shape, margin):
            shapes.append(shape); margins.append(margin + width/2)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH:
                    add(Point(xy(pad.GetPosition())), pad.GetDrillSize().x/2e6 + .255)
                elif pad.GetNetCode() != net:
                    if pad.IsOnLayer(layer):
                        # Fiducials have a 3 mm mask opening around 1 mm copper.
                        # Keep unrelated traces outside the exposed aperture.
                        margin = 1.1 if fp.GetReference().startswith('FID') else CLEARANCE
                        add(pad_shape(pad), margin)
                    elif pad.GetDrillSize().x:
                        add(Point(xy(pad.GetPosition())), pad.GetDrillSize().x/2e6 + .255)
            for item in fp.GraphicalItems():
                if item.GetLayer() == pcbnew.Edge_Cuts:
                    add(bounds(item), .505)
        for item in board.GetTracks():
            if item.GetNetCode() == net:
                continue
            if item.GetClass() == 'PCB_VIA':
                add(Point(xy(item.GetPosition())), item.GetWidth(pcbnew.F_Cu)/2e6 + CLEARANCE)
            elif item.GetLayer() == layer:
                add(LineString([xy(item.GetStart()), xy(item.GetEnd())]), item.GetWidth()/2e6 + CLEARANCE)
        for x, y in MOUNTING_HOLES:
            add(Point(x, y), 3.005)
        self.shapes, self.margins = shapes, margins
        self.tree = STRtree(shapes)
        self.maximum = max(margins)
        self.edge = .505 + width/2
        self.cache = {}

    def clear(self, a, b):
        key = tuple(sorted((a, b)))
        if key in self.cache:
            return self.cache[key]
        if a == b:
            return True
        if any(x < self.edge or x > BOARD_W-self.edge or y < self.edge or y > BOARD_H-self.edge for x, y in (a, b)):
            return False
        line = LineString([a, b])
        result = all(line.distance(self.shapes[i]) >= self.margins[i]
                     for i in self.tree.query(line, predicate='dwithin', distance=self.maximum))
        self.cache[key] = result
        return result


def compact(points):
    result = []
    for p in points:
        p = tuple(round(v, 6) for v in p)
        if result and p == result[-1]:
            continue
        while len(result) >= 2:
            a, b = result[-2:]
            u, v = (b[0]-a[0], b[1]-a[1]), (p[0]-b[0], p[1]-b[1])
            if abs(u[0]*v[1]-u[1]*v[0]) > 1e-7 or u[0]*v[0]+u[1]*v[1] < 0:
                break
            result.pop()
        result.append(p)
    return result


def candidates(a, b):
    """Both shortest octilinear elbows; no arbitrary-angle shortcuts."""
    dx, dy = b[0]-a[0], b[1]-a[1]
    d = min(abs(dx), abs(dy))
    sx, sy = (1 if dx >= 0 else -1), (1 if dy >= 0 else -1)
    yield compact([a, (a[0]+sx*d, a[1]+sy*d), b])
    yield compact([a, (b[0]-sx*d, b[1]-sy*d), b])


def cost(path):
    total = 0
    for a, b in zip(path, path[1:]):
        length = math.dist(a, b)
        total += length + .8 + max(0, .5-length)
    for a, b, c in zip(path, path[1:], path[2:]):
        u, v = (b[0]-a[0], b[1]-a[1]), (c[0]-b[0], c[1]-b[1])
        dot = (u[0]*v[0]+u[1]*v[1])/(math.hypot(*u)*math.hypot(*v))
        if dot < .7:  # Discourage 90-degree and acute inside corners.
            total += 2*(1-dot)
    return total


def simplify(points, obstacle):
    # Dynamic programming over original vertices. Each edge can be replaced by
    # either octilinear elbow. Original copper is always a valid fallback.
    best = [None]*len(points)
    best[0] = [points[0]]
    for j in range(1, len(points)):
        path = compact(best[j-1] + [points[j]])
        score = cost(path)
        for i in range(j-1):
            for middle in candidates(points[i], points[j]):
                candidate = compact(best[i][:-1] + middle)
                value = cost(candidate)
                if value >= score - 1e-5:
                    continue
                if all(obstacle.clear(a, b) for a, b in zip(middle, middle[1:])):
                    path, score = candidate, value
        best[j] = path
    return best[-1]


def metrics(board):
    tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']
    return dict(track_segments=len(tracks), vias=sum(t.GetClass()=='PCB_VIA' for t in board.GetTracks()),
                track_length_mm=round(sum(t.GetLength() for t in tracks)/1e6, 3),
                segments_under_0_3_mm=sum(t.GetLength()<300000 for t in tracks))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    board = pcbnew.LoadBoard(str(args.input.resolve()))
    before = metrics(board)
    changed = 0
    nets = sorted({t.GetNetCode() for t in board.GetTracks()})
    removed = []  # Keep SWIG wrappers alive until the end of this process.
    for net in nets:
        for layer in LAYERS:
            tracks = [t for t in board.GetTracks() if t.GetClass()=='PCB_TRACK' and t.GetNetCode()==net and t.GetLayer()==layer]
            if not tracks:
                continue
            contacts = [pad_shape(p) for fp in board.GetFootprints() for p in fp.Pads()
                        if p.GetNetCode()==net and p.IsOnLayer(layer)]
            contacts += [Point(xy(t.GetPosition())).buffer(t.GetWidth(layer)/2e6, quad_segs=32)
                         for t in board.GetTracks() if t.GetClass()=='PCB_VIA' and t.GetNetCode()==net]
            obstacles = {}
            for edges, points in anchored_runs(tracks, contacts):
                if len(edges) < 2:
                    continue
                width = tracks[edges[0]].GetWidth()
                if width not in obstacles:
                    obstacles[width] = Obstacles(board, net, layer, width/1e6)
                new = simplify(points, obstacles[width])
                if cost(new) >= cost(points)-1e-5:
                    continue
                for index in edges:
                    board.Remove(tracks[index]); removed.append(tracks[index])
                for a, b in zip(new, new[1:]):
                    t = pcbnew.PCB_TRACK(board)
                    t.SetStart(pcbnew.VECTOR2I(round(a[0]*1e6), round(a[1]*1e6)))
                    t.SetEnd(pcbnew.VECTOR2I(round(b[0]*1e6), round(b[1]*1e6)))
                    t.SetLayer(layer); t.SetWidth(width); t.SetNetCode(net)
                    board.Add(t)
                changed += 1
        print(f'Net {net}: {changed} runs simplified', flush=True)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(str(args.output.resolve()), board)
    report = dict(before=before, after=metrics(board), simplified_runs=changed,
                  acceptance='Candidate only; full KiCad ERC/DRC/parity checks required')
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
