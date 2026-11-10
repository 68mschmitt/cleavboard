#!/usr/bin/env python3
"""Read-only routing/assembly metrics from actual KiCad PCB geometry.

Compare with --baseline to quantify routing changes. Counts are diagnostic:
fewer segments alone do not prove cleaner routing, and these metrics do not
replace visual inspection, DRC, connectivity, or signal-integrity review.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

import pcbnew


def inspect(path):
    board = pcbnew.LoadBoard(str(path))
    layers = defaultdict(lambda: Counter(segments=0, vias=0, length_mm=0,
                                        non_45_segments=0, sub_0_2mm_segments=0))
    endpoints = defaultdict(list)
    by_net = defaultdict(lambda: Counter(segments=0, vias=0, length_mm=0))
    top_smd, top_paste, bottom_smd_refs = [], [], set()
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                if pad.IsOnLayer(pcbnew.F_Cu):
                    top_smd.append(f"{fp.GetReference()}.{pad.GetNumber()}")
                if pad.IsOnLayer(pcbnew.B_Cu) and not fp.GetReference().startswith('TP'):
                    bottom_smd_refs.add(fp.GetReference())
            if pad.IsOnLayer(pcbnew.F_Paste):
                top_paste.append(f"{fp.GetReference()}.{pad.GetNumber()}")
    unsupported = Counter()
    vias = 0
    for item in board.GetTracks():
        net = item.GetNetname()
        if item.GetClass() == 'PCB_VIA':
            vias += 1
            by_net[net]['vias'] += 1
            continue
        if item.GetClass() != 'PCB_TRACK':
            unsupported[item.GetClass()] += 1
            continue
        layer = board.GetLayerName(item.GetLayer())
        a, b = item.GetStart(), item.GetEnd()
        dx, dy = b.x - a.x, b.y - a.y
        length = math.hypot(dx, dy) / 1e6
        layers[layer]['segments'] += 1
        layers[layer]['length_mm'] += length
        # 1 um coordinate tolerance avoids classifying serialization rounding
        # as an intentional arbitrary-angle route.
        if min(abs(dx), abs(dy), abs(abs(dx) - abs(dy))) > 1000:
            layers[layer]['non_45_segments'] += 1
        if length < .2:
            layers[layer]['sub_0_2mm_segments'] += 1
        by_net[net]['segments'] += 1
        by_net[net]['length_mm'] += length
        if dx or dy:
            key = (net, layer, item.GetWidth())
            endpoints[(*key, a.x, a.y)].append((dx, dy))
            endpoints[(*key, b.x, b.y)].append((-dx, -dy))
    bends, collinear = 0, 0
    for vectors in endpoints.values():
        if len(vectors) != 2:
            continue
        (ax, ay), (bx, by) = vectors
        sine = abs(ax * by - ay * bx) / (math.hypot(ax, ay) * math.hypot(bx, by))
        if sine < 1e-5 and ax * bx + ay * by < 0:
            collinear += 1
        else:
            bends += 1
    total = sum(layers.values(), Counter())
    total['vias'] = vias
    total['degree_two_bends'] = bends
    total['collinear_split_points'] = collinear
    for stats in [total, *layers.values(), *by_net.values()]:
        stats['length_mm'] = round(stats['length_mm'], 3)
    return {
        'pcb_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        'total': dict(total),
        'layers': dict(sorted(layers.items())),
        'nets': dict(sorted(by_net.items())),
        'assembly': {'bottom_smd_component_count': len(bottom_smd_refs),
                     'top_smd_pads': sorted(top_smd), 'top_paste_pads': sorted(top_paste)},
        'unmeasured_copper_types': dict(unsupported),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = {'current': inspect(args.board.resolve())}
    if args.baseline:
        result['baseline'] = inspect(args.baseline.resolve())
        result['delta'] = {
            key: round(result['current']['total'].get(key, 0) - value, 3)
            for key, value in result['baseline']['total'].items()
        }
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value if key == 'delta' else {
        'total': value['total'], 'assembly': {
            'bottom_smd_component_count': value['assembly']['bottom_smd_component_count'],
            'top_smd_pad_count': len(value['assembly']['top_smd_pads']),
            'top_paste_pad_count': len(value['assembly']['top_paste_pads']),
        },
    } for key, value in result.items()}, indent=2))


if __name__ == '__main__':
    main()
