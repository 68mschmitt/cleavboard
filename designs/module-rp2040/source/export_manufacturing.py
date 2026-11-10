#!/usr/bin/env python3
"""Export revision-specific fabrication and underside-assembly deliverables.

Runs the integration checker first. Output origins are lower-left, +X right
and +Y up, top view. Manifest paths are relative to the design directory.
"""
import csv
import hashlib
import json
import subprocess
import zipfile
from collections import defaultdict
from html import escape
from pathlib import Path
import pcbnew
from design import ROOT, BOARD_W, BOARD_H, MOUNTING_HOLES, FIDUCIALS, components, read_keys
from assembly_parts import purchase

OUT = ROOT/'manufacturing/rev0.5'


def write_csv(path, header, rows):
    with path.open('w',newline='') as file:
        writer=csv.writer(file,lineterminator='\n');writer.writerow(header);writer.writerows(rows)


def assembly_rows(board):
    footprints={fp.GetReference():fp for fp in board.GetFootprints()}
    groups=defaultdict(list);placements=[];pad_rows=[]
    for part in components(*read_keys()):
        identity=purchase(part)
        if identity is None:continue
        ref=part['ref'];fp=footprints[ref]
        pads=[p for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD]
        assert pads and all(p.IsOnLayer(pcbnew.B_Cu) and not p.IsOnLayer(pcbnew.F_Cu) for p in pads), ref
        groups[identity].append(ref)
        # The MX footprint origin is the SWITCH, not the socket body. The
        # midpoint between the two socket solder lands is its placement centre.
        if part['kind']=='MX':
            x=sum(pcbnew.ToMM(p.GetPosition().x) for p in pads)/2
            y=sum(pcbnew.ToMM(p.GetPosition().y) for p in pads)/2
        else:
            x,y=pcbnew.ToMM(fp.GetPosition())
        placements.append([ref,f'{x:.6f}',f'{BOARD_H-y:.6f}','bottom',f'{fp.GetOrientationDegrees()%360:.3f}'])
        for pad in pads:
            px,py=pcbnew.ToMM(pad.GetPosition())
            pad_rows.append([ref,pad.GetNumber(),pad.GetNetname(),f'{px:.6f}',f'{BOARD_H-py:.6f}',
                             f'{px-x:.6f}',f'{y-py:.6f}'])
    assert len(placements)==479
    return groups,placements,pad_rows


def drawing(board):
    # Bottom view, mirrored horizontally; labels are readable from the bottom.
    body=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{BOARD_W}mm" height="{BOARD_H}mm" viewBox="0 0 {BOARD_W} {BOARD_H}">',
          f'<rect x="0" y="0" width="{BOARD_W}" height="{BOARD_H}" fill="#fafafa" stroke="black" stroke-width=".1"/>']
    for fp in board.GetFootprints():
        ref=fp.GetReference();x,y=pcbnew.ToMM(fp.GetPosition())
        for pad in fp.Pads():
            if not pad.IsOnLayer(pcbnew.B_Cu):continue
            px,py=pcbnew.ToMM(pad.GetPosition());w,h=pcbnew.ToMM(pad.GetSize())
            px=BOARD_W-px
            color='#cf9d36' if pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD else '#dddddd'
            title=escape(f'{ref}.{pad.GetNumber()} {pad.GetNetname()}')
            body.append(f'<rect x="{px-w/2}" y="{py-h/2}" width="{w}" height="{h}" fill="{color}" stroke="#444" stroke-width=".06"><title>{title}</title></rect>')
        if ref.startswith('SW'):y-=3.81;x-=.635
        if ref.startswith('LED'):
            body.append(f'<rect x="{BOARD_W-x-1.8}" y="{y-1.6}" width="3.6" height="3.2" fill="white" stroke="#d33" stroke-width=".1"/>')
        body.append(f'<text x="{BOARD_W-x}" y="{y-.9}" font-size=".7" text-anchor="middle" fill="#17284a">{escape(ref)}</text>')
    body.append('</svg>')
    return '\n'.join(body)+'\n'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    reports=OUT/'checks'
    subprocess.run(['python3','-B',str(ROOT/'source/check_kicad.py'),'--reports',str(reports)],check=True)
    pcb=ROOT/'Cleaver.kicad_pcb';board=pcbnew.LoadBoard(str(pcb))
    assert pcbnew.ToMM(board.GetDesignSettings().GetAuxOrigin())==(0.0,BOARD_H)
    groups,placements,pads=assembly_rows(board)
    rows=[]
    for (manufacturer,mpn,code,package),refs in groups.items():
        rows.append([mpn,','.join(refs),package,code,manufacturer,len(refs)])
    write_csv(OUT/'BOM-JLCPCB.csv',['Comment','Designator','Footprint','LCSC Part #','Manufacturer','Quantity'],rows)
    write_csv(OUT/'CPL-JLCPCB.csv',['Designator','Mid X','Mid Y','Layer','Rotation'],placements)
    write_csv(OUT/'pad-orientation-reference.csv',['Designator','Pad','Net','X_mm','Y_mm','DX_from_centroid_mm','DY_from_centroid_mm'],pads)
    write_csv(OUT/'fiducials.csv',['Designator','X_mm','Y_mm','Side','Copper_diameter_mm','Mask_opening_mm'],
              [[f'FID{i}',x,BOARD_H-y,'bottom',1,3] for i,(x,y) in enumerate(FIDUCIALS,1)])
    write_csv(OUT/'user-installed.csv',['Item','Quantity','Mounting','Description'],[
        ['U1',1,'top','User supplied YD-RP2040 4MB USB-C module'],
        ['U1 headers',2,'top','1x20 male 2.54mm headers; 17.78mm between rows'],
        ['TP1 wire',1,'bottom pad / top module','Short insulated raw USB VBUS tap wire; strain relieve to case'],
        ['MX switches',117,'top','Plate-mounted MX-compatible switches'],
        ['2u stabilizers',7,'plate','Cherry-style plate mount, 23.8mm stem spacing'],
        ['6.25u stabilizer',1,'plate','Cherry-style plate mount, 100mm stem spacing'],
        ['Mounting screws',len(MOUNTING_HOLES),'case/plate','M2; choose lengths for your printed case; 6mm reserved diameter']])
    (OUT/'assembly-bottom.svg').write_text(drawing(board))
    fab=OUT/'fabrication';fab.mkdir(exist_ok=True)
    subprocess.run(['kicad-cli','pcb','export','gerbers','--use-drill-file-origin','--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,F.Paste,B.Paste,Edge.Cuts',
        '-o',str(fab)+'/',str(pcb)],check=True)
    subprocess.run(['kicad-cli','pcb','export','drill','--drill-origin','plot','--excellon-separate-th',
        '--generate-map','--map-format','pdf','--generate-report','-o',str(fab)+'/',str(pcb)],check=True)
    with zipfile.ZipFile(OUT/'Cleaver-rev0.5-fabrication.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in sorted(fab.iterdir()):z.write(path,path.name)
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in [pcb,ROOT/'Cleaver.kicad_sch',ROOT/'routing/Cleaver.ses',
                        *sorted(OUT.rglob('*'))] if p.is_file() and p.name!='SHA256.json'}
    (OUT/'SHA256.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('Exported 479 bottom placements, 13 purchasing groups, fabrication/drill files and manifest.')


if __name__=='__main__':main()
