#!/usr/bin/env python3
"""Export real KiCad schematic/copper/fabrication and centroid-correct assembly."""
from pathlib import Path
import csv,json,hashlib,subprocess,zipfile
from collections import defaultdict
import pcbnew
import cairosvg
from PIL import Image
from pypdf import PdfReader,PdfWriter
from pypdf.generic import RectangleObject
from generate import ROOT,NAME,W,H
from sourcing import SELECTED
# New identities verified 2026-11-10; unchanged IDs also inherit rev0.4 sourcing.
PARTS={
 'MX':tuple(SELECTED['MX'][k] for k in ['Manufacturer','MPN','LCSC Part #','package','Source']),
 'D_SOD123':('Semtech','1N4148W','C81598','SOD-123','https://www.lcsc.com/product-detail/C81598.html'),
 'WhiteLED':tuple(SELECTED['WhiteLED'][k] for k in ['Manufacturer','MPN','LCSC Part #','package','Source']),
 '3.9k 1%':('UNI-ROYAL','0805W8F3901T5E','C17614','0805 1%','https://www.lcsc.com/product-detail/C17614.html'),
 '330R 1%':('UNI-ROYAL','0805W8F3300T5E','C17630','0805 1%','https://www.lcsc.com/product-detail/C17630.html'),
 '100k 1%':('UNI-ROYAL','0805W8F1003T5E','C149504','0805 1%','https://www.lcsc.com/product-detail/C149504.html'),
 'PTC_1206':('Littelfuse','1206L020YR','C207035','1206','https://www.lcsc.com/product-detail/C207035.html'),
 'TPS2553':('Texas Instruments','TPS2553DBVR','C55266','SOT-23-6','https://www.lcsc.com/product-detail/C55266.html'),
 'NMOS':('Alpha & Omega Semiconductor','AO3400A','C20917','SOT-23','https://www.lcsc.com/product-detail/C20917.html'),
 '1uF 50V X7R':('Samsung Electro-Mechanics','CL21B105KBFNNNE','C28323','0805','https://www.lcsc.com/product-detail/C28323.html'),
 '22uF 10V X5R':('Samsung Electro-Mechanics','CL21A226MPQNNNE','C29277','0805','https://www.lcsc.com/product-detail/C29277.html'),
}
def write_csv(path,header,rows):
    with path.open('w',newline='') as f:w=csv.writer(f,lineterminator='\n');w.writerow(header);w.writerows(rows)
def run(args):subprocess.run(['kicad-cli']+list(map(str,args)),check=True)
def main():
    result=json.loads((ROOT/'validation/validation.json').read_text());assert result['electrical_checks_pass']
    for name,digest in result['hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, 'Run fresh check.py'
    pcb=ROOT/(NAME+'.kicad_pcb');b=pcbnew.LoadBoard(str(pcb));fps={f.GetReference():f for f in b.GetFootprints()}
    out=ROOT/'manufacturing';review=ROOT/'review';groups=defaultdict(list);cpl=[];padrows=[];bom=[]
    parts=json.loads((ROOT/'source/components.json').read_text())
    for p in parts:
        if p['kind'] in ['YD_RP2040','TestPad']:continue
        ref=p['ref'];identity=PARTS.get(p['kind']) or PARTS[p['value']];groups[identity].append(ref);f=fps[ref]
        pads=[p for p in f.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
        assert pads and all(p.IsOnLayer(pcbnew.B_Cu) and p.IsOnLayer(pcbnew.B_Paste) for p in pads)
        if p['kind']=='MX':x,y=[sum(getattr(p.GetPosition(),axis) for p in pads)/len(pads)/1e6 for axis in ['x','y']]
        else:x,y=f.GetPosition().x/1e6,f.GetPosition().y/1e6
        cpl.append([ref,f'{x:.6f}',f'{H-y:.6f}','bottom',f'{f.GetOrientationDegrees()%360:.3f}'])
        for pad in pads:
            px,py=pad.GetPosition().x/1e6,pad.GetPosition().y/1e6
            padrows.append([ref,pad.GetNumber(),pad.GetNetname(),f'{px:.6f}',f'{H-py:.6f}',f'{px-x:.6f}',f'{y-py:.6f}'])
        bom.append([ref,p['value'],*identity[:4],'bottom',f'{x:.6f}',f'{y:.6f}',identity[4]])
    assert len(cpl)==476
    write_csv(ROOT/'manufacturing/BOM.csv',['Reference','Value','Manufacturer','MPN','LCSC Part #','Package','Assembly Side','X_top_view_mm','Y_down_mm','Source'],bom)
    write_csv(out/'BOM-JLCPCB.csv',['Comment','Designator','Footprint','LCSC Part #','Manufacturer','Quantity'],[[mpn,','.join(refs),package,code,mfr,len(refs)] for (mfr,mpn,code,package,url),refs in groups.items()])
    write_csv(out/'CPL-JLCPCB.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],cpl)
    write_csv(out/'pad-orientation-reference.csv',['Designator','Pad','Net','X_mm','Y_mm','DX_from_centroid_mm','DY_from_centroid_mm'],padrows)
    write_csv(out/'owner-installed.csv',['Item','Quantity','Mounting','Description'],[['U1',1,'top','YD-RP2040 4MB USB-C DWEII/VCC-GND module'],['U1 headers',2,'top','1x20 2.54mm male headers, 17.78mm row spacing'],['MX switches',117,'plate','Clip into plate and hot-swap sockets; no solder'],['2u stabilizers',7,'plate','Cherry-style plate mount'],['6.25u stabilizer',1,'plate','Cherry-style plate mount'],['M2 mounting hardware',11,'case','2.2mm holes; 6mm diameter reserved']])
    write_csv(out/'mounting-holes.csv',['Reference','X_mm','Y_down_mm','NPTH_diameter_mm'],[[f.GetReference(),f.GetPosition().x/1e6,f.GetPosition().y/1e6,2.2] for f in fps.values() if f.GetReference().startswith('H')])
    write_csv(out/'fiducials.csv',['Reference','X_mm','Y_up_mm','Side'],[[f.GetReference(),f.GetPosition().x/1e6,H-f.GetPosition().y/1e6,'bottom'] for f in fps.values() if f.GetReference().startswith('FID')])
    (ROOT/'docs').mkdir(exist_ok=True)
    pdf=ROOT/'docs'/(NAME+'-schematic.pdf');run(['sch','export','pdf','-o',pdf,ROOT/(NAME+'.kicad_sch')])
    # Crop the authentic KiCad export into easily printable detail pages.
    writer=PdfWriter()
    for left,top,right,bottom in [(10,295,600,515),(10,10,600,285),(615,10,1180,265),(615,265,1180,495)]:
        page=PdfReader(pdf).pages[0];sx=float(page.mediabox.width)/1189;sy=float(page.mediabox.height)/594
        page.cropbox=RectangleObject([left*sx,(594-bottom)*sy,right*sx,(594-top)*sy]);writer.add_page(page)
    with (ROOT/'docs'/(NAME+'-schematic-details.pdf')).open('wb') as f:writer.write(f)
    for name,layers,mirror in [('top-copper','F.Cu,F.Silkscreen,Edge.Cuts',False),('bottom-copper','B.Cu,B.Silkscreen,Edge.Cuts',True),('ground-plane','In1.Cu,Edge.Cuts',False),('return-plane','In2.Cu,Edge.Cuts',False),('bottom-assembly','B.Fab,B.Silkscreen,Edge.Cuts',True)]:
        svg=review/(name+'.svg');run(['pcb','export','svg','--layers',layers,'--page-size-mode','2','--exclude-drawing-sheet','--mode-single',*(['--mirror'] if mirror else []),'-o',svg,pcb])
        cairosvg.svg2png(url=str(svg),write_to=str(review/(name+'.png')),output_width=6000,background_color='#ffffff')
    # Detailed raster crops from the real KiCad copper plot, never redrawn artwork.
    image=Image.open(review/'bottom-copper.png');s=image.width/W
    image.crop((0,0,round(85*s),round(33*s))).save(review/'controller-bottom-detail.png')
    image.crop((round((W-75)*s),round(28*s),round((W-20)*s),round(70*s))).save(review/'key-cells-bottom-detail.png')
    fab=out/'fabrication';fab.mkdir(exist_ok=True)
    run(['pcb','export','gerbers','--use-drill-file-origin','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts','-o',str(fab)+'/',pcb])
    run(['pcb','export','drill','--drill-origin','plot','--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report','-o',str(fab)+'/',pcb])
    with zipfile.ZipFile(out/(NAME+'-white-0.1-prototype.zip'),'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(fab.iterdir()):z.write(p,p.name)
    paths=[ROOT/(NAME+e) for e in ['.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru']]+[p for p in out.rglob('*') if p.is_file() and p.name!='SHA256.json']
    (out/'SHA256.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},indent=2)+'\n')
    print('Exported 476 bottom placements; real KiCad copper, schematic, Gerbers and drills.')
if __name__=='__main__':main()
