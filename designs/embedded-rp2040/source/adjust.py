"""One-time routing-development placement correction. Archive carries copper."""
import pcbnew
from generate import ROOT,NAME,mm,xy
b=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
fps={f.GetReference():f for f in b.GetFootprints()}
fp=fps['C29'];fp.SetPosition(mm(425.49,11.55));fp.SetOrientationDegrees(90)
held=list(b.GetTracks())
for t in held:
    if t.GetNetname()!='/SWCLK':continue
    if t.GetClass()=='PCB_VIA' and xy(t.GetPosition())==(418.85,14.0):b.Remove(t)
    elif t.GetClass()=='PCB_TRACK' and t.GetLayer()==pcbnew.F_Cu and abs(pcbnew.ToMM(t.GetLength())-1.3)<.0001:b.Remove(t)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
print([(p.GetNumber(),xy(p.GetPosition())) for p in fp.Pads()])
