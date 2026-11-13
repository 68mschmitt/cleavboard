#!/usr/bin/env python3
"""Generate matching MX/Cherry plate-mount plate and case mounting references.

Requires Shapely >=2. Coordinates are PCB top view, +X right, +Y down.
Stabilizer cutout dimensions follow swill/kad key.go DrawCherryStab:
https://github.com/swill/kad/blob/master/key.go
They are the builder's practical Cherry-compatible cutout, not PCB-mount holes.
"""
import csv
import json
from html import escape
from shapely import Point, box, unary_union
from shapely.affinity import rotate, translate
from design import ROOT, BOARD_W, BOARD_H, MOUNTING_HOLES, read_keys
from logo_interface import APERTURE, square

OUT = ROOT/'mechanical'


def stabilizer_cutout(size):
    spacing = 50 if size == 6.25 else 11.9
    shapes = [box(-spacing+3.375, -2.3, spacing-3.375, 2.3)]
    for sign in (-1, 1):
        x = sign*spacing
        shapes.extend([box(x-3.375,-5.53,x+3.375,6.77),
                       box(x-1.65,6.77,x+1.65,7.97)])
        shapes.append(box(x+3.375,-2.3,x+4.2,.5) if sign>0 else box(x-4.2,-2.3,x-3.375,.5))
    return unary_union(shapes)


def geometry(*, top_capacitor_opening=True):
    keys,_ = read_keys()
    cuts, stabs = [], []
    for key in keys:
        shape = box(-7,-7,7,7)
        size = max(key['w'],key['h'])
        if size >= 2:
            stab = stabilizer_cutout(size)
            if key['h']>key['w']:
                stab = rotate(stab,90,origin=(0,0))
            shape = shape.union(stab)
            stabs.append(dict(ref=key['ref'], legend=key['legend'],
                              size='6.25u' if size==6.25 else '2u',
                              x_mm=key['x'],y_mm=key['y'],
                              rotation_deg=90 if key['h']>key['w'] else 0,
                              stem_spacing_mm=100 if size==6.25 else 23.8))
        cuts.append(translate(shape,key['x'],key['y']))
    # The tall user-installed parts pass through the plate rather than collide
    # with it. The USB/module opening reaches the right and top edges.
    cuts.append(box(398,-1,BOARD_W+1,25.5))
    if top_capacitor_opening:
        cuts.append(Point(377,6).buffer(5,quad_segs=64))
    cuts.append(square(APERTURE))
    for index,(x,y) in enumerate(MOUNTING_HOLES,1):
        reserve = Point(x,y).buffer(3,quad_segs=64)
        for cut in cuts:
            assert not reserve.intersects(cut), f'H{index}: screw/standoff overlaps plate opening'
    holes=[Point(x,y).buffer(1.1,quad_segs=64) for x,y in MOUNTING_HOLES]
    plate=box(0,0,BOARD_W,BOARD_H).difference(unary_union(cuts+holes))
    assert plate.is_valid and plate.geom_type=='Polygon', 'Plate is disconnected or invalid'
    assert len(stabs)==8
    return plate,cuts,stabs


def svg_path(poly):
    return ' '.join('M '+' L '.join(f'{x:.5f} {y:.5f}' for x,y in ring.coords)+' Z'
                    for ring in [poly.exterior,*poly.interiors])


def export_svg(path,poly,width,height,annotations=''):
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" height="{height}mm" viewBox="0 0 {width} {height}">\n'
                    f'<path d="{svg_path(poly)}" fill="none" stroke="black" stroke-width="0.05" fill-rule="evenodd"/>{annotations}</svg>\n')


def export_dxf(path,poly):
    # R12 closed POLYLINE entities; CAD +Y up, origin at PCB upper-left.
    lines=['0','SECTION','2','HEADER','9','$INSUNITS','70','4','0','ENDSEC','0','SECTION','2','ENTITIES']
    for ring in [poly.exterior,*poly.interiors]:
        lines += ['0','POLYLINE','8','CUT','66','1','70','1']
        for x,y in list(ring.coords)[:-1]:
            lines += ['0','VERTEX','8','CUT','10',f'{x:.5f}','20',f'{-y:.5f}','30','0']
        lines += ['0','SEQEND','8','CUT']
    lines += ['0','ENDSEC','0','EOF']
    path.write_text('\n'.join(lines)+'\n')


def main():
    OUT.mkdir(exist_ok=True)
    plate,cuts,stabs=geometry()
    export_svg(OUT/'Cleaver-plate.svg',plate,BOARD_W,BOARD_H)
    export_dxf(OUT/'Cleaver-plate.dxf',plate)
    labels=''
    for i,(x,y) in enumerate(MOUNTING_HOLES,1):
        side=1 if x<BOARD_W/2 else -1
        anchor='start' if side==1 else 'end'
        labels+=f'<circle cx="{x}" cy="{y}" r="3" fill="none" stroke="#2266bb" stroke-width=".15"/>'
        labels+=f'<text x="{x+side*3.5}" y="{y}" text-anchor="{anchor}" font-size="1.8" fill="#2266bb">H{i}</text>'
    export_svg(OUT/'mounting-plan.svg',plate,BOARD_W,BOARD_H,labels)
    with (OUT/'mounting-holes.csv').open('w',newline='') as f:
        writer=csv.writer(f,lineterminator='\n')
        writer.writerow(['reference','x_mm','y_mm','drill_mm','reserved_diameter_mm'])
        for i,(x,y) in enumerate(MOUNTING_HOLES,1):writer.writerow([f'H{i}',x,y,2.2,6])
    with (OUT/'stabilizers.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(stabs[0]),lineterminator='\n');writer.writeheader();writer.writerows(stabs)
    rings=[list(r.coords)[:-1] for r in [plate.exterior,*plate.interiors]]
    points=[];paths=[]
    for ring in rings:
        paths.append(list(range(len(points),len(points)+len(ring))))
        points.extend([[round(x,5),round(-y,5)] for x,y in ring])
    (OUT/'Cleaver-plate.scad').write_text('// Nominal clip-in plate. Units mm; PCB top view, Y up.\n'
        '// Plate top sits nominally 5 mm above PCB top. Print a fit coupon first.\n'
        'plate_thickness = 1.5;\nlinear_extrude(height=plate_thickness)\n'
        f'polygon(points={json.dumps(points)}, paths={json.dumps(paths)}, convexity=10);\n')
    (OUT/'mounting-reference.scad').write_text('// Import into your case design. PCB top is Z=0, bottom Z=-1.6.\n'
        '// XY origin is upper-left; Y is negative toward the keyboard front.\n'
        f'pcb_size = [{BOARD_W}, {BOARD_H}, 1.6];\n'
        f'mounts = {json.dumps([[x,-y] for x,y in MOUNTING_HOLES])};\n'
        'module mounting_axes(height=20) { for(p=mounts) translate([p[0],p[1],-10]) cylinder(d=2.2,h=height,$fn=48); }\n'
        'module standoff_envelopes(height=3.5) { for(p=mounts) translate([p[0],p[1],0]) cylinder(d=6,h=height,$fn=48); }\n'
        'mounting_axes();\n')
    # Small combined switch/stabilizer coupon for checking printed tolerances.
    coupon=box(-20,-12,20,12).difference(box(-7,-7,7,7).union(stabilizer_cutout(2)))
    coupon=translate(coupon,20,12)
    export_svg(OUT/'stabilizer-fit-coupon.svg',coupon,40,24)
    export_dxf(OUT/'stabilizer-fit-coupon.dxf',coupon)
    (OUT/'stabilizer-fit-coupon.scad').write_text('linear_extrude(height=1.5) import("stabilizer-fit-coupon.svg");\n')
    (OUT/'validation.json').write_text(json.dumps(dict(mounting_holes=len(MOUNTING_HOLES),
        plate_connected=True,plate_geometry_valid=True,stabilizers=stabs,
        plate_thickness_mm=1.5,pcb_to_plate_top_nominal_mm=5),indent=2)+'\n')
    print('Generated connected plate, 11 matching mounting holes, 8 stabilizers and fit coupon.')


if __name__=='__main__':main()
