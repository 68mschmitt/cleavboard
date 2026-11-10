"""Place an off-land stitching via on the isolated ESD ground region."""
import pcbnew
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from generate import ROOT,NAME,xy,mm,via
b=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
f=next(z.GetFilledPolysList(z.GetLayer()) for z in b.Zones() if z.GetNetname()=='/GND' and z.GetLayer()==pcbnew.F_Cu)
g=next(z.GetFilledPolysList(z.GetLayer()) for z in b.Zones() if z.GetNetname()=='/GND' and z.GetLayer()==pcbnew.In1_Cu)
obs=[];region=box(433,10,441,16)
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb=p.GetBoundingBox();shape=box(pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))
        if shape.intersects(region):obs.append(shape.buffer(.34))
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':shape=Point(*xy(t.GetPosition())).buffer(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2+.34)
    elif t.GetNetname()!='/GND':shape=LineString([xy(t.GetStart()),xy(t.GetEnd())]).buffer(pcbnew.ToMM(t.GetWidth())/2+.34)
    else:continue
    if shape.intersects(region):obs.append(shape)
blocked=unary_union(obs)
candidates=[]
for ix in range(80):
    for iy in range(80):
        x,y=434+ix*.05,11+iy*.05;p=Point(x,y)
        if p.intersects(blocked) or not f.Contains(mm(x,y)) or not g.Contains(mm(x,y),0):continue
        candidates.append(((x-437.3625)**2+(y-13)**2,x,y))
assert candidates,'No clearance-safe ESD ground stitching site'
_,x,y=min(candidates);v=via(b,'GND',x,y);v.SetWidth(pcbnew.FromMM(.4));v.SetDrill(pcbnew.FromMM(.2));v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED);v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
print('ESD GND stitching',x,y)
