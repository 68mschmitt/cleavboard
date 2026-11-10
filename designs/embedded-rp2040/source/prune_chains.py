"""Optional fast removal of serial dangling tracks; rollback on any open net."""
import json,subprocess
from collections import defaultdict
import pcbnew
from generate import ROOT,NAME
file=ROOT/(NAME+'.kicad_pcb');rp=ROOT/'validation/drc.json';lifetimes=[]
initial=json.loads(rp.read_text())
assert not initial['unconnected_items']
for violation in initial['violations']:
    if violation['type']!='track_dangling':continue
    backup=file.read_bytes();report=rp.read_bytes();b=pcbnew.LoadBoard(str(file));tracks=list(b.GetTracks());lifetimes.append((b,tracks))
    byid={t.m_Uuid.AsString():t for t in tracks};seed=violation['items'][0]['uuid']
    if seed not in byid:continue
    endpoints=defaultdict(list)
    def key(t,q):return t.GetNetCode(),t.GetLayer(),q.x,q.y
    for t in tracks:
        if t.GetClass()=='PCB_TRACK':endpoints[key(t,t.GetStart())].append(t);endpoints[key(t,t.GetEnd())].append(t)
    ids={seed};todo=[seed]
    while todo:
        t=byid[todo.pop()]
        for q in [t.GetStart(),t.GetEnd()]:
            adjacent=endpoints[key(t,q)]
            if len(adjacent)==2:
                for o in adjacent:
                    uid=o.m_Uuid.AsString()
                    if uid not in ids:ids.add(uid);todo.append(uid)
    for uid in ids:b.Remove(byid[uid])
    pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(file),b)
    subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all','--all-track-errors','--schematic-parity','--refill-zones','-o',str(rp),str(file)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    r=json.loads(rp.read_text());good=not r['unconnected_items'] and not r['schematic_parity'] and all(v['type'] in ['track_dangling','via_dangling'] for v in r['violations'])
    print(byid[seed].GetNetname(),len(ids),'accepted' if good else 'rolled back',flush=True)
    if not good:file.write_bytes(backup);rp.write_bytes(report)
