"""Development clock-corridor ripup; reroute crossings and run fresh DRC."""
import subprocess
import pcbnew
from shapely.geometry import LineString,Point,box
import route
from generate import ROOT,NAME,xy
file=str(ROOT/(NAME+'.kicad_pcb'))
b=pcbnew.LoadBoard(file);maskboard=pcbnew.LoadBoard(file)
held=list(maskboard.GetTracks());region=box(409,10,418.5,16)
for t in held:
    if t.GetClass()=='PCB_TRACK' and t.GetNetname()!='/XIN' and LineString([xy(t.GetStart()),xy(t.GetEnd())]).intersects(region):maskboard.Remove(t)
net=b.FindNet('/XIN');images,vm=route.masks(maskboard,maskboard.FindNet('/XIN'),.127)
starts={(z,round((416.777-route.X0)/route.STEP),round(12.193/route.STEP)):(416.777-route.X0,12.193) for z in range(4)}
goals={(z,round((411.048-route.X0)/route.STEP),round(14.687/route.STEP)):(411.048-route.X0,14.687) for z in range(4)}
root=route.WORK/'clock-bridge'
root.with_suffix('.maps').write_bytes(b''.join(i.tobytes() for i in images));root.with_suffix('.vias').write_bytes(vm.tobytes())
root.with_suffix('.points').write_text(f'{route.W} {route.H} {len(starts)} {len(goals)}\n'+''.join(f'{z} {x} {y}\n' for z,x,y in list(starts)+list(goals)))
subprocess.run([str(route.WORK/'grid-route'),str(root)],check=True)
path=[tuple(map(int,row.split())) for row in root.with_suffix('.path').read_text().splitlines()[1:]]
old=list(b.GetTracks());ids={t.m_Uuid.AsString() for t in old};route.apply(b,net,.127,path,starts,goals)
new=[t for t in b.GetTracks() if t.m_Uuid.AsString() not in ids];removed=[]
for t in old:
    if t.GetClass()!='PCB_TRACK' or t.GetNetname()=='/XIN':continue
    line=LineString([xy(t.GetStart()),xy(t.GetEnd())]);r=pcbnew.ToMM(t.GetWidth())/2+.13
    for n in new:
        if n.GetClass()=='PCB_VIA':hit=line.distance(Point(*xy(n.GetPosition())))<r+.2
        else:hit=n.GetLayer()==t.GetLayer() and line.distance(LineString([xy(n.GetStart()),xy(n.GetEnd())]))<r+.0635
        if hit:removed.append(t);break
print('Ripup',[(t.GetNetname(),xy(t.GetStart()),xy(t.GetEnd())) for t in removed])
for t in removed:b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(file,b)
