#!/usr/bin/env python3
"""Promote roomy 0.4/0.2mm vias to ordinary 0.5/0.3mm, with real DRC rollback.
Requires a clean connected board. Dense MCU escapes retain the smaller geometry.
"""
import json,subprocess
import pcbnew
from generate import ROOT,NAME,xy
p=ROOT/(NAME+'.kicad_pcb');rp=ROOT/'validation/drc.json';backup=p.read_bytes();initial=rp.read_bytes();r=json.loads(initial)
assert not any(r[k] for k in ['violations','unconnected_items','schematic_parity'])
b=pcbnew.LoadBoard(str(p));candidates={}
for t in b.GetTracks():
    if t.GetClass()!='PCB_VIA' or t.GetDrillValue()!=pcbnew.FromMM(.2):continue
    x,y=xy(t.GetPosition())
    if 423.5<x<433 and 6<y<16:continue
    candidates[t.m_Uuid.AsString()]=t;t.SetWidth(pcbnew.FromMM(.5));t.SetDrill(pcbnew.FromMM(.3))
attempted=len(candidates);reverted=set()
while True:
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(p),b)
    subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',str(rp),str(p)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    r=json.loads(rp.read_text())
    if not any(r[k] for k in ['violations','unconnected_items','schematic_parity']):break
    bad={i['uuid'] for v in r['violations']+r['unconnected_items'] for i in v['items'] if i['uuid'] in candidates and i['uuid'] not in reverted}
    if not bad:
        p.write_bytes(backup);rp.write_bytes(initial);raise RuntimeError('Unattributed DRC regression; restored board')
    for uid in bad:
        t=candidates[uid];t.SetWidth(pcbnew.FromMM(.4));t.SetDrill(pcbnew.FromMM(.2));reverted.add(uid)
result={'attempted':attempted,'promoted_to_0_5mm_land_0_3mm_drill':attempted-len(reverted),'retained_small_for_clearance':len(reverted),'drc':0,'unconnected':0}
(ROOT/'validation/ordinary-vias.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
