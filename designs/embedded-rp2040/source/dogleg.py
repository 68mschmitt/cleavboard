"""Finish two tightly packed access stems; independent DRC remains mandatory."""
import pcbnew
from shapely.geometry import LineString,Point
from generate import ROOT,NAME,xy,track,via
b=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
held=list(b.GetTracks())
for t in held:
    if t.GetNetname()!='/SWCLK':continue
    if t.GetClass()=='PCB_VIA' and Point(*xy(t.GetPosition())).distance(Point(415,15))<.3:b.Remove(t)
    elif t.GetClass()=='PCB_TRACK' and t.GetLayer()==pcbnew.F_Cu and (xy(t.GetEnd()) in [(416,14),(415,15)]):b.Remove(t)
retired=held
held=list(b.GetTracks())
paths=[('SWCLK',pcbnew.F_Cu,[(417.55,14),(416.1,14),(415.1,15.15)])]
for net,layer,coords in paths:
    path=LineString(coords);endpoint=Point(*coords[-1])
    for t in held:
        if t.GetNetname()=='/'+net:continue
        if t.GetClass()=='PCB_VIA':
            r=pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu))/2;p=Point(*xy(t.GetPosition()))
            if path.distance(p)<r+.0635+.14 or endpoint.distance(p)<r+.2+.14:b.Remove(t)
        else:
            line=LineString([xy(t.GetStart()),xy(t.GetEnd())]);r=pcbnew.ToMM(t.GetWidth())/2
            if (t.GetLayer()==layer and path.distance(line)<r+.0635+.14) or endpoint.distance(line)<r+.2+.14:b.Remove(t)
    for a,c in zip(coords,coords[1:]):track(b,net,a,c,layer,width=.127)
    if net=='SWCLK':
        v=via(b,net,*coords[-1]);v.SetWidth(pcbnew.FromMM(.4));v.SetDrill(pcbnew.FromMM(.2))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
