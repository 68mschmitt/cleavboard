#!/usr/bin/env python3
"""Archive all current copper with nanometre-precision Specctra coordinates."""
import json
from collections import defaultdict
import pcbnew
from generate import ROOT,NAME,REVISION
b=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
def coord(p):return f'{p.x} {-p.y}'
def q(s):return json.dumps(s)
def vname(v):return f'Via[0-3]_{round(pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))*1000)}:{round(pcbnew.ToMM(v.GetDrillValue())*1000)}_um'
groups=defaultdict(list);vias={};options=[]
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        name=vname(t);vias[name]=t.GetWidth(pcbnew.F_Cu)
        entry=f'(via {q(name)} {coord(t.GetPosition())})'
        options.append(dict(x=t.GetPosition().x,y=t.GetPosition().y,net=t.GetNetname(),front=int(t.GetFrontTentingMode()),back=int(t.GetBackTentingMode())))
    else:
        assert t.GetClass()=='PCB_TRACK'
        entry=f'(wire (path {b.GetLayerName(t.GetLayer())} {t.GetWidth()} {coord(t.GetStart())} {coord(t.GetEnd())}))'
    groups[t.GetNetname()].append(entry)
text=f'(session {NAME}_{REVISION}_complete_copper\n (base_design {NAME})\n (placement (resolution um 1000))\n (was_is)\n (routes (resolution um 1000)\n (parser (host_cad "KiCad") (host_version "10.0.8"))\n (library_out\n'
for name,size in sorted(vias.items()):text+=f'(padstack {q(name)} '+''.join(f'(shape (circle {layer} {size} 0 0))' for layer in ['F.Cu','In1.Cu','In2.Cu','B.Cu'])+' (attach off))\n'
text+=')\n (network_out\n'
for net,entries in sorted(groups.items()):text+=f'(net {q(net)}\n'+'\n'.join(entries)+')\n'
text+=')))\n'
(ROOT/'routing'/f'{NAME}.ses').write_text(text)
(ROOT/'routing/via-options.json').write_text(json.dumps(options,indent=2)+'\n')
print('Archived',sum(map(len,groups.values())),'copper items on',len(groups),'nets')
