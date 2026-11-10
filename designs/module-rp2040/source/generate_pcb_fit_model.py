#!/usr/bin/env python3
"""Export four interlocking, actual-thickness PCB sections for a 235 mm bed.

Requires KiCad 10's pcbnew, Shapely >=2.1, numpy and trimesh.
Reads the saved board's Edge.Cuts and component drills; omits electrical vias.
"""
import argparse
import hashlib
import json
import numpy as np
import pcbnew
import trimesh
from shapely import Point, Polygon, box, constrained_delaunay_triangles, unary_union
from shapely.affinity import affine_transform

from design import ROOT
from generate_mechanical import svg_path


def ring_coordinates(chain):
    return [tuple(pcbnew.ToMM(chain.CPoint(i))) for i in range(chain.PointCount())]


def pcb_geometry(path):
    board = pcbnew.LoadBoard(str(path))
    outlines = pcbnew.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(outlines, False), 'Invalid PCB outline'
    assert outlines.OutlineCount() == 1, 'Expected one connected PCB'
    outer = Polygon(ring_coordinates(outlines.Outline(0)))
    cuts = [Polygon(ring_coordinates(outlines.Hole(0, i)))
            for i in range(outlines.HoleCount(0))]
    counts = dict(edge_cut_windows=len(cuts), nonplated_drills=0, plated_component_drills=0)
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            dx, dy = pcbnew.ToMM(pad.GetDrillSize())
            if not dx:
                continue
            assert abs(dx-dy) < 1e-6, 'Update generator for non-circular component drills'
            cuts.append(Point(*pcbnew.ToMM(pad.GetPosition())).buffer(dx/2, quad_segs=16))
            kind = 'nonplated_drills' if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH else 'plated_component_drills'
            counts[kind] += 1
    holes = unary_union(cuts)
    shape = outer.difference(holes)
    assert shape.is_valid and shape.geom_type == 'Polygon'
    assert len(shape.interiors) == len(cuts), 'Unexpected touching/overlapping openings'
    counts['omitted_electrical_vias'] = sum(t.GetClass() == 'PCB_VIA' for t in board.GetTracks())
    return shape, outer, holes, pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()), counts


def puzzle_tab(x, y, direction):
    """7 mm round head on a 4 mm neck, extending 8 mm across the seam."""
    head = Point(x+direction*4.5, y).buffer(3.5, quad_segs=32)
    ends = sorted([x-direction, x+direction*4.5])
    return head.union(box(ends[0], y-2, ends[1], y+2))


def split_geometry(shape, outer, holes, gap):
    width, height = outer.bounds[2:]
    assert np.allclose(outer.bounds, [0, 0, 452.4375, 147.6375]), 'Revisit seam for changed PCB outline'
    x = width/2
    # Three seams follow gaps between switch columns. Two opposed puzzle tabs
    # per seam sit between rows. Every functional hole stays on a single piece.
    paths = [
        [(119, 0), (119, 46.5), (109.5, 49), (109.5, 66),
         (114.3, 69), (114.3, 85), (123.825, 88), (123.825, 103),
         (119, 106), (119, height)],
        [(x, 0), (x, 27), (233.5, 29), (233.5, 46.5),
         (224, 49), (224, 66), (228.5, 69), (228.5, 85),
         (238, 88), (238, 103), (236, 106), (236, 123),
         (x, 127), (x, height)],
        [(333.375, 0), (333.375, height)],
    ]
    partitions, seams, seam_reports = [], [], []
    for index, points in enumerate(paths, 1):
        sx = points[0][0]
        partition = Polygon([(0, 0), *points, (0, height)])
        partition = partition.union(puzzle_tab(sx, 23.8, 1))
        partition = partition.difference(puzzle_tab(sx, 132, -1))
        seam = partition.boundary.intersection(outer.difference(partition).boundary)
        assert seam.distance(holes) >= gap+1, f'Joint {index} is too close to an existing hole'
        if partitions:
            assert partitions[-1].difference(partition).area < 1e-8, 'Seams cross'
        partitions.append(partition)
        seams.append(seam)
        seam_reports.append(dict(
            between_parts=[index, index+1],
            tab_centers_pcb_xy_mm=[[sx+4.5, 23.8], [sx-4.5, 132]],
            minimum_nominal_seam_to_hole_mm=round(seam.distance(holes), 6)))

    pieces = []
    for index in range(4):
        piece = shape.intersection(partitions[index]) if index < 3 else shape
        # Offset only the mating boundary; preserve external outline/hole sizes.
        # All pieces retain their assembled positions until STL export.
        if index:
            piece = piece.difference(partitions[index-1].buffer(gap, quad_segs=32, join_style='round'))
        assert piece.geom_type == 'Polygon' and piece.is_valid, 'Disconnected PCB section'
        for earlier in pieces:
            assert earlier.intersection(piece).area < 1e-8
        if pieces:
            assert abs(pieces[-1].distance(piece)-gap) < 1e-4
        pieces.append(piece)
    assert sum(len(p.interiors) for p in pieces) == len(shape.interiors), 'Seam cut an existing hole'
    assembled = unary_union(pieces)
    assert np.allclose(assembled.bounds, shape.bounds), 'Finished dimensions changed'
    missing = shape.difference(assembled)
    allowed_gap = unary_union(seams).buffer(gap+1e-5, quad_segs=128)
    assert missing.difference(allowed_gap).area < 1e-6, 'Material lost outside joint clearance'
    return pieces, dict(
        gap_mm=gap, nominal_tab_head_diameter_mm=7, nominal_tab_neck_width_mm=4,
        nominal_tab_projection_mm=8, seams=seam_reports,
        clearance_removed_area_mm2=round(missing.area, 6),
        existing_openings_preserved=len(shape.interiors), overlap_area_mm2=0,
    )


def export_piece(path, polygon, height, bed, brim):
    x0, y0, x1, y1 = polygon.bounds
    # CAD top view: X right and Y up. Each STL sits flat on Z=0, at its own origin.
    local = affine_transform(polygon, [1, 0, 0, -1, -x0, y1])
    # Constrained triangulation preserves the many aligned hole boundaries.
    # Earcut can create topological pinches here despite matching area/volume.
    triangles = constrained_delaunay_triangles(local)
    xy = np.asarray([list(t.exterior.coords)[:3] for t in triangles.geoms])
    vertices, indices = np.unique(xy.reshape(-1, 2), axis=0, return_inverse=True)
    mesh = trimesh.creation.extrude_triangulation(vertices, indices.reshape(-1, 3), height)
    mesh.export(path)
    # Check the actual serialized STL, including float32 round-trip precision.
    printed = trimesh.load_mesh(path)
    assert printed.is_watertight and printed.is_winding_consistent and printed.is_volume
    assert np.all(printed.area_faces > 1e-10), 'Degenerate STL triangles'
    assert np.isclose(printed.volume, polygon.area*height, rtol=2e-6), 'Incorrect extruded volume'
    assert printed.euler_number == 2-2*len(polygon.interiors), 'STL opening topology changed'
    assert np.allclose(printed.bounds[0], [0, 0, 0], atol=1e-5)
    assert np.allclose(printed.extents, [x1-x0, y1-y0, height], atol=2e-5)
    assert all(float(size)+2*brim <= bed for size in printed.extents[:2]), 'Section does not fit print bed'
    return dict(file=path.name, size_mm=[round(float(v), 5) for v in printed.extents],
                assembled_translation_mm=[x0, 0, 0], triangles=len(printed.faces),
                through_openings=len(polygon.interiors), watertight=True,
                consistent_winding=True, positive_volume=True,
                volume_mm3=round(float(printed.volume), 4),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def preview(path, pieces, width, height):
    # Top-view overview. Neither this drawing nor the STLs are horizontally mirrored.
    paths = ''.join(f'<path d="{svg_path(p)}" fill="{color}" stroke="#263238" '
                    'stroke-width="0.12" fill-rule="evenodd"/>'
                    for p, color in zip(pieces, ['#98c9e8', '#edc58f', '#a9d6b0', '#c9b4e4']))
    labels = ''.join(f'<text x="{(p.bounds[0]+p.bounds[2])/2}" y="130" '
                     f'font-family="sans-serif" font-size="5" text-anchor="middle" '
                     f'fill="#263238">{i}</text>' for i, p in enumerate(pieces, 1))
    path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}mm" '
                   f'height="{height}mm" viewBox="0 0 {width} {height}">'
                   '<title>Cleaver PCB fit model: four numbered sections, left to right; top view</title>'
                   '<rect width="100%" height="100%" fill="white"/>'
                   f'{paths}{labels}</svg>\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gap', type=float, default=.2, help='Mating-edge clearance in mm (default 0.2)')
    parser.add_argument('--bed', type=float, default=235, help='Square print bed side in mm (default 235)')
    parser.add_argument('--brim', type=float, default=5, help='Reserve this much bed space on each side')
    args = parser.parse_args()
    assert 0 < args.gap <= .5 and args.bed > 0 and args.brim >= 0
    source = ROOT/'Cleaver.kicad_pcb'
    out = ROOT/'mechanical/pcb-fit-model'
    out.mkdir(parents=True, exist_ok=True)
    shape, outer, holes, thickness, counts = pcb_geometry(source)
    pieces, joint = split_geometry(shape, outer, holes, args.gap)
    names = ['1-left', '2-middle-left', '3-middle-right', '4-right']
    result = [export_piece(out/f'Cleaver-PCB-{name}.stl', p, thickness, args.bed, args.brim)
              for name, p in zip(names, pieces)]
    width, height = outer.bounds[2:]
    preview(out/'assembly-preview.svg', pieces, width, height)
    report = dict(source_pcb='Cleaver.kicad_pcb',
                  source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  assembled_size_mm=[width, height, thickness],
                  bed_mm=[args.bed, args.bed], brim_allowance_each_side_mm=args.brim,
                  source_features=counts, joint=joint, parts=result)
    (out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    for part in result:
        print(f'{part["file"]}: {part["size_mm"]} mm, watertight, {part["through_openings"]} holes')
    print(f'Assembled size: {width} x {height} x {thickness} mm; gap: {args.gap} mm')


if __name__ == '__main__':
    main()
