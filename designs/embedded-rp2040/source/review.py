#!/usr/bin/env python3
"""Actual KiCad copper SVG plots, raster previews and geometric routing metrics.
Zones are hidden in a temporary plotting copy so traces remain inspectable.
All layers use the same unmirrored board coordinates for before/after comparison.
"""
import argparse,collections,hashlib,json,math,subprocess
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('board',type=Path);parser.add_argument('label');args=parser.parse_args()
out=ROOT/'review'/args.label;out.mkdir(parents=True,exist_ok=True)
b=pcbnew.LoadBoard(str(args.board.resolve()))
def metrics(items):
    tracks=[t for t in items if t.GetClass()=='PCB_TRACK'];vias=[t for t in items if t.GetClass()=='PCB_VIA'];non45=0;endpoints=collections.defaultdict(list)
    for t in tracks:
        p,q=t.GetStart(),t.GetEnd()
        dx,dy=q.x-p.x,q.y-p.y
        non45+=min(abs(dx),abs(dy),abs(abs(dx)-abs(dy)))>1000 # 1um tolerance
        if dx or dy:
            key=t.GetNetname(),t.GetLayer(),t.GetWidth();endpoints[(*key,p.x,p.y)].append((dx,dy));endpoints[(*key,q.x,q.y)].append((-dx,-dy))
    bends=collinear=0
    for vectors in endpoints.values():
        if len(vectors)!=2:continue
        (ax,ay),(bx,by)=vectors;sine=abs(ax*by-ay*bx)/(math.hypot(ax,ay)*math.hypot(bx,by))
        if sine<1e-5 and ax*bx+ay*by<0:collinear+=1
        else:bends+=1
    return dict(segments=len(tracks),vias=len(vias),length_mm=round(sum(pcbnew.ToMM(t.GetLength()) for t in tracks),3),segments_under_0_1mm=sum(t.GetLength()<pcbnew.FromMM(.1) for t in tracks),segments_under_0_2mm=sum(t.GetLength()<pcbnew.FromMM(.2) for t in tracks),non_45_degree_segments=non45,degree_two_bends=bends,collinear_split_points=collinear)
items=list(b.GetTracks());m={'all':metrics(items),'keyboard_outside_controller':metrics([t for t in items if not(t.GetPosition().x>pcbnew.FromMM(399) and t.GetPosition().y<pcbnew.FromMM(26))]),'layers':{b.GetLayerName(l):metrics([t for t in items if t.GetLayer()==l]) for l in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu]},'nets':{n:metrics([t for t in items if t.GetNetname()==n]) for n in sorted({t.GetNetname() for t in items})}}
m['pcb_sha256']=hashlib.sha256(args.board.read_bytes()).hexdigest();(out/'metrics.json').write_text(json.dumps(m,indent=2)+'\n')
held=list(b.Zones())
for z in held:
    if not z.GetIsRuleArea():b.Remove(z)
tmp=Path('/tmp/opencode/cleaver-embedded-review');tmp.mkdir(exist_ok=True);file=tmp/(args.label+'.kicad_pcb');pcbnew.SaveBoard(str(file),b)
for layer in ['F.Cu','In1.Cu','In2.Cu','B.Cu','B.Assembly']:
    svg=out/(layer+'.svg')
    plot_layers='B.Cu,B.Fab,B.CrtYd' if layer=='B.Assembly' else layer
    subprocess.run(['kicad-cli','pcb','export','svg','--mode-single','--layers',plot_layers+',Edge.Cuts','--fit-page-to-board','--exclude-drawing-sheet','-o',str(svg),str(file)],check=True)
    subprocess.run(['rsvg-convert','-w','3000','-o',str(out/(layer+'.png')),str(svg)],check=True)
    # SVG viewBox crop retains KiCad geometry and vector quality.
    import xml.etree.ElementTree as ET
    for crop,(x,y,w,h,pixels) in {'controller':(399,0,54,27,2160),'fan-in':(350,0,103,52,2472)}.items():
        root=ET.parse(svg).getroot();vb=list(map(float,root.attrib['viewBox'].split()));width=float(root.attrib['width'].removesuffix('mm'));scale=vb[2]/width
        root.set('viewBox',f'{x*scale} {y*scale} {w*scale} {h*scale}');root.set('width',f'{w*4}mm');root.set('height',f'{h*4}mm')
        cropped=out/(layer+'-'+crop+'.svg');ET.ElementTree(root).write(cropped,encoding='utf-8',xml_declaration=True)
        subprocess.run(['rsvg-convert','-w',str(pixels),'-o',str(out/(layer+'-'+crop+'.png')),str(cropped)],check=True)
print(json.dumps(m['all'],indent=2))
