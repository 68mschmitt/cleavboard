"""Apply labels to a development board once; normal generator includes them."""
import pcbnew
from generate import ROOT,NAME,labels
b=pcbnew.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
if not any(d.GetClass()=='PCB_TEXT' and 'CLEAVER-EMBEDDED' in d.GetText() for d in b.GetDrawings()):labels(b)
pcbnew.SaveBoard(str(ROOT/(NAME+'.kicad_pcb')),b)
