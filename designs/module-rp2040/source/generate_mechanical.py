#!/usr/bin/env python3
"""Generate matching MX/Cherry plate-mount plate and case mounting references.

Requires Shapely >=2. Coordinates are PCB top view, +X right, +Y down.
Stabilizer cutout dimensions follow swill/kad key.go DrawCherryStab:
https://github.com/swill/kad/blob/master/key.go
They are the builder's practical Cherry-compatible cutout, not PCB-mount holes.
"""
from shapely import Point, box, unary_union
from shapely.affinity import rotate, translate
from design import ROOT, BOARD_W, BOARD_H, read_keys
from logo_interface import APERTURE, FRONT_EXTENSION, rectangle
from mounting_interface import BASE_POSTS, PLATE_SCREW_DRILL

OUT = ROOT/'mechanical'
PLATE_H = BOARD_H+FRONT_EXTENSION


def stabilizer_cutout(size):
    spacing = 50 if size == 6.25 else 11.9
    shapes = [box(-spacing+3.375, -2.3, spacing-3.375, 2.3)]
    for sign in (-1, 1):
        x = sign*spacing
        shapes.extend([box(x-3.375,-5.53,x+3.375,6.77),
                       box(x-1.65,6.77,x+1.65,7.97)])
        shapes.append(box(x+3.375,-2.3,x+4.2,.5) if sign>0 else box(x-4.2,-2.3,x-3.375,.5))
    return unary_union(shapes)


def geometry(*, top_capacitor_opening=True, mounts=None, mounting_drill=None):
    mounts = BASE_POSTS if mounts is None else mounts
    mounting_drill = PLATE_SCREW_DRILL if mounting_drill is None else mounting_drill
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
    cuts.append(rectangle(APERTURE))
    for index,(x,y) in enumerate(mounts,1):
        reserve = Point(x,y).buffer(3,quad_segs=64)
        for cut in cuts:
            assert not reserve.intersects(cut), f'H{index}: screw/standoff overlaps plate opening'
    holes=[Point(x,y).buffer(mounting_drill/2,quad_segs=64) for x,y in mounts]
    plate=box(0,0,BOARD_W,PLATE_H).difference(unary_union(cuts+holes))
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
    from generate_cartridge_case import main as cartridge_main
    cartridge_main()


if __name__=='__main__':main()
