#!/usr/bin/env python3
"""Compare all tracks/vias at SES archive resolution, ignoring IDs and ordering."""
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import pcbnew


def geometry(path):
    board = pcbnew.LoadBoard(str(path))
    def point(p):
        return round(p.x / 100), round(p.y / 100)
    items = []
    for item in board.GetTracks():
        if item.GetClass() == 'PCB_VIA':
            items.append(('via', item.GetNetname(), point(item.GetPosition()),
                          item.GetWidth(pcbnew.F_Cu), item.GetDrillValue(),
                          int(item.TopLayer()), int(item.BottomLayer())))
        else:
            assert item.GetClass() == 'PCB_TRACK'
            items.append(('track', item.GetNetname(), int(item.GetLayer()),
                          round(item.GetWidth() / 100),
                          tuple(sorted([point(item.GetStart()), point(item.GetEnd())]))))
    return Counter(items)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before', type=Path)
    parser.add_argument('after', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    before, after = geometry(args.before), geometry(args.after)
    result = dict(passed=before == after, resolution_mm=.0001,
                  before_items=sum(before.values()), after_items=sum(after.values()),
                  missing_items=sum((before-after).values()), added_items=sum((after-before).values()),
                  scope='All track/via net names, layers, endpoints, widths and via drills; zones independently refilled and DRC checked',
                  before_sha256=hashlib.sha256(args.before.read_bytes()).hexdigest(),
                  after_sha256=hashlib.sha256(args.after.read_bytes()).hexdigest())
    args.report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    assert result['passed'], 'Routing changed'
