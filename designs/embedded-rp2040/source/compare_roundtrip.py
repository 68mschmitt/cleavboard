#!/usr/bin/env python3
"""Compare completed PCB geometry with a regenerated PCB, ignoring UUIDs.
Usage: python3 -B source/compare_roundtrip.py /path/to/completed-backup.kicad_pcb
"""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
import pcbnew
from generate import ROOT,NAME
def point(p):return p.x,p.y
def copper(b):
    result=[]
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA':result.append(('via',t.GetNetname(),point(t.GetPosition()),t.GetWidth(pcbnew.F_Cu),t.GetDrillValue(),int(t.GetFrontTentingMode()),int(t.GetBackTentingMode())))
        else:result.append(('track',t.GetNetname(),b.GetLayerName(t.GetLayer()),t.GetWidth(),*sorted([point(t.GetStart()),point(t.GetEnd())])))
    return Counter(result)
def footprints(b):
    return {f.GetReference():(f.GetValue(),str(f.GetFPID().GetLibItemName()),point(f.GetPosition()),f.GetOrientationDegrees(),f.GetLayer(),sorted((p.GetNumber(),p.GetNetname(),point(p.GetPosition()),point(p.GetSize()),point(p.GetDrillSize()),p.GetOrientationDegrees(),tuple(p.GetLayerSet().Seq())) for p in f.Pads())) for f in b.GetFootprints()}
def edges(b):
    return Counter((int(s.GetShape()),point(s.GetStart()),point(s.GetEnd()),s.GetWidth()) for s in b.GetDrawings() if s.GetLayer()==pcbnew.Edge_Cuts)
oldfile=Path(sys.argv[1]).resolve();newfile=ROOT/(NAME+'.kicad_pcb')
old=pcbnew.LoadBoard(str(oldfile));new=pcbnew.LoadBoard(str(newfile))
a,z=copper(old),copper(new)
r=dict(copper_geometry_equal=a==z,footprint_pad_geometry_and_nets_equal=footprints(old)==footprints(new),outline_equal=edges(old)==edges(new),before_copper_items=sum(a.values()),after_copper_items=sum(z.values()),missing_copper_items=sum((a-z).values()),extra_copper_items=sum((z-a).values()),before_sha256=hashlib.sha256(oldfile.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(newfile.read_bytes()).hexdigest(),archive_sha256=hashlib.sha256((ROOT/'routing'/f'{NAME}.ses').read_bytes()).hexdigest())
r['pass']=all(r[k] for k in ['copper_geometry_equal','footprint_pad_geometry_and_nets_equal','outline_equal'])
(ROOT/'validation/roundtrip.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
sys.exit(0 if r['pass'] else 1)
