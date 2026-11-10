#!/usr/bin/env python3
"""Archive ALL routed copper; no placement changes or implicit power fanouts.

Only run after a clean integration check. The generator's --ses path imports
this archive into fresh schematic-derived placement and refills its planes.
"""
import argparse
from collections import defaultdict
from pathlib import Path
import pcbnew


def archive(board, output):
    def scalar(n):
        return str(round(n / 100))

    def point(p):
        return scalar(p.x)+' '+scalar(-p.y)

    nets, vias = defaultdict(list), {}
    for item in board.GetTracks():
        if item.GetClass() == 'PCB_VIA':
            w, d = item.GetWidth(pcbnew.F_Cu), item.GetDrillValue()
            name = f'Via[0-3]_{round(w/1000)}:{round(d/1000)}_um'
            vias[name] = w
            entry = f'(via "{name}" {point(item.GetPosition())})'
        else:
            entry = f'(wire (path {board.GetLayerName(item.GetLayer())} {scalar(item.GetWidth())} {point(item.GetStart())} {point(item.GetEnd())}))'
        nets[item.GetNetname()].append(entry)
    text = '(session Cleaver_rev0.5_complete_copper (base_design Cleaver) (placement (resolution um 10))\n'
    text += '(routes (resolution um 10) (parser (host_cad "KiCad\'s Pcbnew") (host_version 10.0.8))\n(library_out\n'
    for name, width in sorted(vias.items()):
        text += f'(padstack "{name}" '+''.join(f'(shape (circle {layer} {scalar(width)} 0 0))' for layer in ('F.Cu','In1.Cu','In2.Cu','B.Cu'))+' (attach off))\n'
    text += ')\n(network_out\n'
    for net, entries in sorted(nets.items()):
        text += f'(net {net}\n'+'\n'.join(sorted(entries))+')\n'
    output.write_text(text+')))\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    archive(pcbnew.LoadBoard(str(args.board)), args.output)
