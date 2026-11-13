#!/usr/bin/env python3
"""Export the revision 0.6 switch/stabilizer plate and fit coupons as STL.

Requires KiCad's pcbnew, Shapely >=2.1 (GEOS >=3.10), numpy, scipy and trimesh.
Checks the saved PCB without writing it; preserves historical mechanical exports.
"""
import hashlib
import json

import numpy as np
import pcbnew
import shapely
import trimesh
from shapely import Point, Polygon, box, constrained_delaunay_triangles, unary_union
from shapely.affinity import affine_transform, translate

from design import ROOT, BOARD_W, BOARD_H, MOUNTING_HOLES, read_keys, REVISION
from generate_mechanical import export_svg, geometry, stabilizer_cutout

OUT = ROOT/f'mechanical/rev{REVISION}'
THICKNESS = 1.5


def validate_pcb(path, plate):
    """Reject a stale plate definition rather than silently misaligning hardware."""
    board = pcbnew.LoadBoard(str(path))
    assert board.GetTitleBlock().GetRevision() == REVISION, f'Expected revision {REVISION} PCB'
    outlines = pcbnew.SHAPE_POLY_SET()
    assert board.GetBoardPolygonOutlines(outlines, False), 'Invalid PCB outline'
    assert outlines.OutlineCount() == 1, 'Expected one PCB outline'
    chain = outlines.Outline(0)
    outline = Polygon([tuple(pcbnew.ToMM(chain.CPoint(i))) for i in range(chain.PointCount())])
    assert outline.equals(box(0, 0, BOARD_W, BOARD_H)), 'PCB outline changed'

    footprints = {fp.GetReference(): fp for fp in board.GetFootprints()}
    keys, _ = read_keys()
    assert {ref for ref in footprints if ref.startswith('SW')} == {k['ref'] for k in keys}
    for key in keys:
        fp = footprints[key['ref']]
        assert np.allclose(pcbnew.ToMM(fp.GetPosition()), [key['x'], key['y']],
                           rtol=0, atol=1e-6), f"{key['ref']}: switch centre changed"
        assert fp.GetOrientationDegrees() == 0, f"{key['ref']}: switch rotation changed"

    expected_mounts = {f'H{i}' for i in range(1, len(MOUNTING_HOLES)+1)}
    assert {ref for ref in footprints if ref.startswith('H') and ref[1:].isdigit()} == expected_mounts
    mounts = []
    for index, (x, y) in enumerate(MOUNTING_HOLES, 1):
        ref = f'H{index}'
        pads = list(footprints[ref].Pads())
        assert len(pads) == 1, f'{ref}: unexpected mounting footprint'
        pad = pads[0]
        assert pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH, f'{ref}: not an NPTH'
        assert np.allclose(pcbnew.ToMM(pad.GetPosition()), [x, y], rtol=0, atol=1e-6), ref
        assert np.allclose(pcbnew.ToMM(pad.GetDrillSize()), [2.2, 2.2], rtol=0, atol=1e-6), ref
        mounts.append(dict(reference=ref, x_mm=x, y_mm=y, drill_mm=2.2))

    assert footprints['C5'].GetLayer() == pcbnew.B_Cu, 'C5 is no longer underneath'
    controller = footprints['U1']
    assert controller.GetLayer() == pcbnew.F_Cu
    body_checks = 0
    for graphic in controller.GraphicalItems():
        if graphic.GetLayer() == pcbnew.F_Fab and graphic.GetClass() == 'PCB_SHAPE':
            bounds = graphic.GetBoundingBox()
            x0, y0 = pcbnew.ToMM(bounds.GetPosition())
            x1, y1 = pcbnew.ToMM(bounds.GetEnd())
            assert not plate.intersects(box(x0, y0, x1, y1)), 'Plate overlaps controller/USB body'
            body_checks += 1
    assert body_checks >= 2, 'Missing controller/USB body geometry'
    return dict(revision=REVISION, outline_matches=True, switch_centres_matched=len(keys),
                mounting_holes=mounts, controller_body_clear=True, capacitor_on_underside=True)


def fit_coupon(size):
    width = 120 if size == 6.25 else 40
    opening = box(-7, -7, 7, 7).union(stabilizer_cutout(size))
    # Include an M2 clearance hole to test the printer's hole compensation too.
    opening = opening.union(Point(-width/2+3, -9).buffer(1.1, quad_segs=64))
    coupon = box(-width/2, -12, width/2, 12).difference(opening)
    assert coupon.is_valid and coupon.geom_type == 'Polygon' and len(coupon.interiors) == 2
    return translate(coupon, width/2, 12)


def top_surface(mesh, height):
    """Recover the actual serialized STL's XY material, including every opening."""
    triangles = mesh.triangles
    top = triangles[np.all(np.isclose(triangles[:, :, 2], height), axis=1)]
    return unary_union([Polygon(triangle[:, :2]) for triangle in top])


def export_stl(path, polygon):
    x0, y0, x1, y1 = polygon.bounds
    # View from above: X right, Y up; not horizontally mirrored. Z=0 is print bed.
    local = affine_transform(polygon, [1, 0, 0, -1, -x0, y1])
    triangles = constrained_delaunay_triangles(local)
    xy = np.asarray([list(t.exterior.coords)[:3] for t in triangles.geoms])
    vertices, indices = np.unique(xy.reshape(-1, 2), axis=0, return_inverse=True)
    mesh = trimesh.creation.extrude_triangulation(vertices, indices.reshape(-1, 3), THICKNESS)
    mesh.export(path)

    # Verify the binary STL after float32 serialization, not just the source mesh.
    printed = trimesh.load_mesh(path)
    assert printed.is_watertight and printed.is_winding_consistent and printed.is_volume
    assert printed.body_count == 1, 'Disconnected STL'
    assert np.all(printed.area_faces > 1e-10), 'Degenerate STL triangles'
    assert np.isclose(printed.volume, polygon.area*THICKNESS, rtol=2e-6)
    assert printed.euler_number == 2-2*len(polygon.interiors), 'STL opening topology changed'
    assert np.allclose(printed.bounds[0], [0, 0, 0], rtol=0, atol=1e-5)
    assert np.allclose(printed.extents, [x1-x0, y1-y0, THICKNESS], rtol=0, atol=2e-5)
    surface = top_surface(printed, THICKNESS)
    assert surface.geom_type == 'Polygon' and surface.is_valid
    assert len(surface.interiors) == len(polygon.interiors)
    error = surface.symmetric_difference(local).area
    deviation = surface.boundary.hausdorff_distance(local.boundary)
    assert deviation < 2e-5, 'Serialized STL changed cutout positions or dimensions'
    assert error < local.length*2e-5, 'Serialized STL changed the intended XY material'
    return dict(file=path.name, size_mm=[round(float(v), 5) for v in printed.extents],
                triangles=len(printed.faces), through_openings=len(surface.interiors),
                connected_bodies=1, watertight=True, consistent_winding=True,
                positive_volume=True, volume_mm3=round(float(printed.volume), 4),
                xy_roundtrip_difference_mm2=round(error, 8),
                xy_max_boundary_deviation_mm=round(deviation, 8),
                sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def main():
    source = ROOT/'Cleaver.kicad_pcb'
    # The historical plate has a top capacitor hole. Rev0.6 C5 is below the PCB.
    plate, cuts, stabs = geometry(top_capacitor_opening=False)
    checks = validate_pcb(source, plate)
    assert len(cuts) == 118 and len(plate.interiors) == 128
    OUT.mkdir(parents=True, exist_ok=True)
    parts = [export_stl(OUT/f'Cleaver-top-plate-rev{REVISION}.stl', plate)]
    export_svg(OUT/f'Cleaver-top-plate-rev{REVISION}.svg', plate, BOARD_W, BOARD_H)
    for size, label in [(2, '2u'), (6.25, '6.25u')]:
        coupon = fit_coupon(size)
        parts.append(export_stl(OUT/f'stabilizer-fit-coupon-{label}.stl', coupon))
    report = dict(
        source_pcb='../../Cleaver.kicad_pcb',
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        source_checks=checks, switch_opening_mm=[14, 14],
        plate_thickness_mm=THICKNESS, pcb_to_plate_top_nominal_mm=5,
        pcb_to_plate_underside_nominal_mm=3.5, hardware_reserved_diameter_mm=6,
        stabilizer_type='Cherry-compatible plate-mount', stabilizers=stabs,
        controller_notch_pcb_xy_mm=[398, 0, BOARD_W, 25.5],
        obsolete_top_capacitor_opening=False,
        stl_coordinates='millimetres; X right, Y up, Z=0 underside; PCB (x,y) maps to (x,147.6375-y)',
        physical_fit_tested=False,
        tools=dict(kicad=pcbnew.Version(), shapely=shapely.__version__,
                   geos=shapely.geos_version_string, trimesh=trimesh.__version__),
        parts=parts)
    (OUT/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    for part in parts:
        print(f'{part["file"]}: {part["size_mm"]} mm, watertight, {part["through_openings"]} openings')
    print(f'Matched rev{REVISION} PCB: 117 switches, 11 M2 through-holes, 7 x 2u + 1 x 6.25u stabilizers.')


if __name__ == '__main__':
    main()
