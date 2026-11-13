#!/usr/bin/env python3
"""Build the current tilted tray, removable key bezel and PCB/plate spacers.

Reads, but never writes, the saved PCB and existing switch plate. Requires
FreeCAD, KiCad pcbnew, Shapely >=2.1, NumPy and Trimesh. STL files are oriented
for printing; STEP/FCStd files contain the assembled, desk-flat geometry.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
from pathlib import Path
import tempfile

import numpy as np
import pcbnew
import shapely
from shapely import Point, box, unary_union
from shapely.affinity import affine_transform
import trimesh

from build_3d_models import freecad
from design import BOARD_H, BOARD_W, MODULE_X, MODULE_Y, MOUNTING_HOLES, ROOT, U, read_keys, REVISION, CONTROLLER_SOCKETS
from generate_mechanical import geometry, svg_path
from generate_top_plate import top_surface, validate_pcb

OUT = ROOT/f'mechanical/rev{REVISION}/case'
PCB_THICKNESS = 1.6
PLATE_TOP = 5.0
PLATE_THICKNESS = 1.5
SPACER_HEIGHT = PLATE_TOP-PLATE_THICKNESS
STANDOFF_DIAMETER = 6.0


@dataclass(frozen=True)
class Parameters:
    typing_angle_deg: float = 5.0
    pcb_edge_clearance_mm: float = .25
    wall_mm: float = 6.5
    floor_mm: float = 2.8
    front_under_pcb_clearance_mm: float = 6.0
    outer_corner_radius_mm: float = 4.0
    cover_underside_above_pcb_mm: float = 8.4
    cover_thickness_mm: float = 2.4
    cover_lip_depth_mm: float = 2.0
    cover_lip_wall_mm: float = 1.0
    cover_lip_inner_offset_mm: float = .5
    cover_lip_clearance_mm: float = .25
    key_aperture_extra_per_side_mm: float = .15
    insert_bore_mm: float = 3.0
    insert_pocket_depth_mm: float = 4.5
    cover_insert_pocket_depth_mm: float = 5.0
    cover_screw_clearance_mm: float = 2.2
    cover_head_recess_diameter_mm: float = 4.2
    cover_head_recess_depth_mm: float = 1.0
    usb_opening_width_mm: float = 16.0
    usb_opening_height_mm: float = 7.2
    usb_center_above_pcb_mm: float = 5.74
    socket_support_gap_mm: float = .7

    @property
    def margin(self):
        return self.pcb_edge_clearance_mm+self.wall_mm

    @property
    def cover_top(self):
        return self.cover_underside_above_pcb_mm+self.cover_thickness_mm

    @property
    def front_pcb_top(self):
        return (self.floor_mm+self.front_under_pcb_clearance_mm
                +PCB_THICKNESS*math.cos(math.radians(self.typing_angle_deg)))

    @property
    def lip_outer_offset(self):
        return self.cover_lip_inner_offset_mm+self.cover_lip_wall_mm

    @property
    def rebate_offset(self):
        return self.lip_outer_offset+self.cover_lip_clearance_mm

    @property
    def cover_screw_offset(self):
        return (self.margin+self.rebate_offset)/2

    def validate(self):
        assert all(math.isfinite(v) and v > 0 for v in asdict(self).values())
        assert 2 <= self.typing_angle_deg <= 10, 'Supported typing angle is 2–10 degrees'
        assert self.cover_underside_above_pcb_mm >= 8.4, 'Socketed module needs its headroom'
        assert .7 <= self.socket_support_gap_mm <= 1.0, 'Unshimmed backstops must clear the full socket height tolerance'
        assert self.cover_lip_inner_offset_mm > self.pcb_edge_clearance_mm
        rim = self.margin-self.rebate_offset
        assert rim >= max(self.insert_bore_mm+2, self.cover_head_recess_diameter_mm+.6), 'Insufficient material around rim inserts/heads'
        assert self.insert_bore_mm < STANDOFF_DIAMETER-2
        assert self.front_under_pcb_clearance_mm > self.insert_pocket_depth_mm+1
        assert self.cover_thickness_mm-self.cover_head_recess_depth_mm >= 1.2
        assert self.cover_top-(self.usb_center_above_pcb_mm+self.usb_opening_height_mm/2) >= 1.4


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cover_screws(p):
    return [(x, y) for y in (-p.cover_screw_offset, BOARD_H+p.cover_screw_offset)
            for x in (10, 145, 300, BOARD_W-10)]


def outlines(p):
    """Plan geometry in PCB top-view coordinates (+Y towards the user)."""
    m, r = p.margin, p.outer_corner_radius_mm
    outer = box(-m+r, -m+r, BOARD_W+m-r, BOARD_H+m-r).buffer(r, quad_segs=16)
    pocket = box(-p.pcb_edge_clearance_mm, -p.pcb_edge_clearance_mm,
                 BOARD_W+p.pcb_edge_clearance_mm, BOARD_H+p.pcb_edge_clearance_mm)
    keys, _ = read_keys()
    e = p.key_aperture_extra_per_side_mm
    # Unite neighbours: no fragile ~0.5 mm webs between individual keycaps.
    apertures = unary_union([box(k['x']-k['w']*U/2-e, k['y']-k['h']*U/2-e,
                                k['x']+k['w']*U/2+e, k['y']+k['h']*U/2+e) for k in keys])
    deck = outer.difference(apertures)
    assert deck.is_valid and deck.geom_type == 'Polygon', 'Disconnected bezel'
    return outer, pocket, apertures, deck


def prism(poly, z, height):
    """Extrude a Shapely PCB-view polygon into CAD X right, Y rearwards."""
    app, part = freecad()
    if poly.geom_type == 'MultiPolygon':
        return part.makeCompound([prism(item, z, height) for item in poly.geoms])
    wires = [part.makePolygon([app.Vector(x, BOARD_H-y, z) for x, y in ring.coords])
             for ring in [poly.exterior, *poly.interiors]]
    face = part.makeFace(wires, 'Part::FaceMakerBullseye')
    # The Y reflection reverses a polygon's winding; make a positive solid.
    if face.normalAt(0, 0).z < 0:
        face.reverse()
    return face.extrude(app.Vector(0, 0, height))


def cylinder(x, y, z, diameter, height):
    app, part = freecad()
    return part.makeCylinder(diameter/2, height, app.Vector(x, BOARD_H-y, z))


def assembled(shape, p):
    app, _ = freecad()
    shape = shape.copy()
    shape.rotate(app.Vector(), app.Vector(1, 0, 0), p.typing_angle_deg)
    shape.translate(app.Vector(0, 0, p.front_pcb_top))
    return shape


def world_point(x, pcb_y, z, p):
    angle = math.radians(p.typing_angle_deg)
    y = BOARD_H-pcb_y
    return [x, y*math.cos(angle)-z*math.sin(angle),
            p.front_pcb_top+y*math.sin(angle)+z*math.cos(angle)]


def usb_tool(p):
    """Side-facing rectangular plug tunnel, shared by tray and cover lip/deck.

    Width is measured along the PCB's Y axis, height normal to the PCB. Keeping
    the tunnel square-cornered maximizes clearance for the cable overmould.
    """
    return prism(box(BOARD_W-3, MODULE_Y-p.usb_opening_width_mm/2,
                     BOARD_W+p.margin+2, MODULE_Y+p.usb_opening_width_mm/2),
                 p.usb_center_above_pcb_mm-p.usb_opening_height_mm/2,
                 p.usb_opening_height_mm)


def build(p):
    p.validate()
    app, part = freecad()
    outer, pocket, apertures, deck = outlines(p)
    ztop = p.cover_underside_above_pcb_mm
    # Make the whole stack in PCB coordinates, then trim its bottom against a
    # horizontal desk plane. Standoff bores remain NORMAL to the tilted PCB.
    above_floor = part.makeBox(600, 300, 100, app.Vector(-50, -50, p.floor_mm))
    above_desk = part.makeBox(600, 300, 100, app.Vector(-50, -50, 0))
    outer_solid = assembled(prism(outer, -60, ztop+60), p).common(above_desk)
    cavity = assembled(prism(pocket, -60, ztop+65), p).common(above_floor)
    tray = outer_solid.cut(cavity)

    # Printed 6 mm OD bosses, each terminating exactly at the PCB underside.
    boss_clip = part.makeBox(600, 300, 100, app.Vector(-50, -50, p.floor_mm-.3))
    bosses = [assembled(cylinder(x, y, -60, STANDOFF_DIAMETER, 60-PCB_THICKNESS), p)
              .common(boss_clip) for x, y in MOUNTING_HOLES]
    # The 40 SMT contacts must not carry the full insertion load (up to 80N
    # from Harwin's 2N/contact maximum). Backstops sit 0.70mm below nominal
    # bottoms, clearing the full +/-0.50mm height tolerance. Select shims
    # for a MEASURED 0.1–0.3mm gap; never preload a socket.
    supports = [assembled(prism(box(MODULE_X-25.2,y-1.1,MODULE_X+25.2,y+1.1),
                                  -60,60-PCB_THICKNESS-7.5-p.socket_support_gap_mm),p).common(boss_clip)
                for _,y,_ in CONTROLLER_SOCKETS]
    tray = tray.multiFuse(bosses+supports)
    insert_holes = [cylinder(x, y, -PCB_THICKNESS-p.insert_pocket_depth_mm,
                             p.insert_bore_mm, p.insert_pocket_depth_mm+.1)
                    for x, y in MOUNTING_HOLES]
    insert_holes += [cylinder(x, y, ztop-p.cover_insert_pocket_depth_mm,
                              p.insert_bore_mm, p.cover_insert_pocket_depth_mm+.1)
                     for x, y in cover_screws(p)]
    tray = tray.cut(assembled(part.makeCompound(insert_holes), p))

    rebate = box(-p.rebate_offset, -p.rebate_offset,
                 BOARD_W+p.rebate_offset, BOARD_H+p.rebate_offset)
    tray = tray.cut(assembled(prism(rebate, ztop-p.cover_lip_depth_mm-.2,
                                   p.cover_lip_depth_mm+1), p))
    tray = tray.cut(assembled(usb_tool(p), p)).removeSplitter()

    lip_out, lip_in = p.lip_outer_offset, p.cover_lip_inner_offset_mm
    lip = box(-lip_out, -lip_out, BOARD_W+lip_out, BOARD_H+lip_out).difference(
        box(-lip_in, -lip_in, BOARD_W+lip_in, BOARD_H+lip_in))
    cover = prism(deck, ztop, p.cover_thickness_mm).fuse(
        prism(lip, ztop-p.cover_lip_depth_mm, p.cover_lip_depth_mm))
    screw_cuts = []
    for x, y in cover_screws(p):
        screw_cuts.extend([
            cylinder(x, y, ztop-.1, p.cover_screw_clearance_mm, p.cover_thickness_mm+.2),
            cylinder(x, y, p.cover_top-p.cover_head_recess_depth_mm,
                     p.cover_head_recess_diameter_mm, p.cover_head_recess_depth_mm+.1)])
    cover = cover.cut(part.makeCompound(screw_cuts)).cut(usb_tool(p)).removeSplitter()
    spacer = cylinder(0, 0, 0, STANDOFF_DIAMETER, SPACER_HEIGHT).cut(
        cylinder(0, 0, -.1, 2.2, SPACER_HEIGHT+.2))
    for label, shape in [('tray', tray), ('cover', cover), ('spacer', spacer)]:
        assert not shape.isNull() and shape.isValid() and len(shape.Solids) == 1, label
        assert shape.Volume > 0, label
    return dict(tray=tray, cover=cover, spacer=spacer, apertures=apertures, deck=deck)


def validate_source(p, plate):
    source = ROOT/'Cleaver.kicad_pcb'
    result = validate_pcb(source, plate)
    board = pcbnew.LoadBoard(str(source))
    assert math.isclose(pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()), PCB_THICKNESS)
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    assert np.allclose(pcbnew.ToMM(fps['C5'].GetPosition()), [377, 6], rtol=0, atol=1e-6)
    assert np.allclose(pcbnew.ToMM(fps['U1'].GetPosition()), [MODULE_X, MODULE_Y], rtol=0, atol=1e-6)
    assert math.isclose(fps['U1'].GetOrientationDegrees(), -90), 'USB orientation changed'
    saved_plate = trimesh.load_mesh(ROOT/f'mechanical/rev{REVISION}/Cleaver-top-plate-rev{REVISION}.stl')
    assert saved_plate.is_watertight and saved_plate.is_volume, 'Invalid existing plate STL'
    assert np.allclose(saved_plate.extents, [BOARD_W, BOARD_H, PLATE_THICKNESS], rtol=0, atol=2e-5)
    actual_plate = affine_transform(top_surface(saved_plate, PLATE_THICKNESS),
                                    [1, 0, 0, -1, 0, BOARD_H])
    assert actual_plate.boundary.hausdorff_distance(plate.boundary) < 2e-5, 'Existing plate STL is stale'
    assert actual_plate.symmetric_difference(plate).area < plate.length*2e-5
    result.update(pcb_thickness_mm=PCB_THICKNESS, capacitor_position_matches=True,
                  controller_position_and_orientation_match=True, existing_plate_stl_matches=True)
    return result


def validate_fit(p, shapes, plate):
    app, part = freecad()
    tray, cover = shapes['tray'], assembled(shapes['cover'], p)
    pcb = assembled(prism(box(0, 0, BOARD_W, BOARD_H), -PCB_THICKNESS, PCB_THICKNESS), p)
    plate_shape = assembled(prism(plate.simplify(.005, preserve_topology=True),
                                  SPACER_HEIGHT, PLATE_THICKNESS), p)
    overlaps = {}
    for label, a, b in [('tray_pcb', tray, pcb), ('tray_plate', tray, plate_shape),
                         ('cover_pcb', cover, pcb), ('cover_plate', cover, plate_shape),
                         ('tray_cover', tray, cover)]:
        volume = a.common(b).Volume
        assert volume < 1e-6, f'{label}: interference {volume} mm³'
        overlaps[label] = round(volume, 8)

    # A 10 mm maximum capacitor plus 1 mm service clearance, over its WHOLE body.
    cap_keepout = assembled(prism(box(371, .5, 383, 11.5), -12.6, 11), p)
    assert tray.common(cap_keepout).Volume < 1e-6, 'C5 clearance is less than 11 mm'
    # Male header insulators seat on the TOP carrier surface. The long posts
    # enter the underside sockets. Include 0.56mm allowance above the former
    # nominal 7.64mm module envelope for seating and package variation.
    module = prism(box(MODULE_X-25.5, MODULE_Y-10.5, MODULE_X+25.5, MODULE_Y+10.5), 0, 8.2)
    shell = prism(box(MODULE_X+19, MODULE_Y-4.475, MODULE_X+27.5, MODULE_Y+4.475), 4.14, 3.2)
    controller = assembled(module.fuse(shell), p)
    assert tray.common(controller).Volume < 1e-6, 'Controller/USB intersects tray'
    assert cover.common(controller).Volume < 1e-6, 'Controller/USB intersects cover'
    socket_checks=[]
    for ref,y,_ in CONTROLLER_SOCKETS:
        socket = assembled(prism(box(MODULE_X-25.65,y-2.125,MODULE_X+25.65,y+2.125),
                                     -PCB_THICKNESS-8.0,8.0),p)
        assert tray.common(socket).Volume < 1e-6, f'{ref}: socket intersects tray/backstop'
        assert cover.common(socket).Volume < 1e-6, f'{ref}: socket intersects cover'
        face=assembled(prism(box(MODULE_X-25,y-1,MODULE_X+25,y+1),
                                 -PCB_THICKNESS-7.5-p.socket_support_gap_mm-.1,.05),p)
        assert abs(tray.common(face).Volume-face.Volume)<1e-6, f'{ref}: insertion backstop missing'
        socket_checks.append(dict(reference=ref, maximum_envelope_mm=[51.3,4.25,8.0],
                                  nominal_unshimmed_backstop_gap_mm=p.socket_support_gap_mm,
                                  minimum_unshimmed_backstop_gap_mm=round(p.socket_support_gap_mm-.5,4),
                                  shim_options_mm=[.2,.4,.6,.8,1.0], measured_target_gap_mm=[.1,.3],
                                  backstop_present=True))
    tunnel = assembled(usb_tool(p), p)
    assert tray.common(tunnel).Volume < 1e-6 and cover.common(tunnel).Volume < 1e-6

    keys, _ = read_keys()
    for key in keys:
        # Conservative standard-cap envelope: pitch minus 1 mm, all the way
        # from PCB to above the cover (contains the full 4 mm vertical travel).
        swept = box(key['x']-(key['w']*U-1)/2, key['y']-(key['h']*U-1)/2,
                    key['x']+(key['w']*U-1)/2, key['y']+(key['h']*U-1)/2)
        assert shapes['apertures'].covers(swept), key['ref']
        assert shapes['deck'].intersection(swept).area < 1e-8, key['ref']

    mounts = []
    for index, (x, y) in enumerate(MOUNTING_HOLES, 1):
        # At 0.1 mm below the support face: bore is empty, surrounding ring is solid.
        bore = assembled(cylinder(x, y, -PCB_THICKNESS-.1, p.insert_bore_mm-.05, .05), p)
        ring = cylinder(x, y, -PCB_THICKNESS-.1, STANDOFF_DIAMETER-.05, .05).cut(
            cylinder(x, y, -PCB_THICKNESS-.11, p.insert_bore_mm+.05, .1))
        ring = assembled(ring, p)
        assert tray.common(bore).Volume < 1e-6, f'H{index}: insert bore blocked'
        assert abs(tray.common(ring).Volume-ring.Volume) < 1e-6, f'H{index}: boss absent'
        mounts.append(dict(reference=f'H{index}', pcb_xy_mm=[x, y],
                           support_face_center_assembly_mm=world_point(x, y, -PCB_THICKNESS, p)))
    # Measure clear height normal to the PCB, against the actual horizontal floor.
    theta = math.radians(p.typing_angle_deg)
    cap_min_depth = min((world_point(x, y, -PCB_THICKNESS, p)[2]-p.floor_mm)/math.cos(theta)
                        for x in (371, 383) for y in (.5, 11.5))
    return dict(intersection_volumes_mm3=overlaps, mounting_standoffs=mounts,
                standoff_outer_diameter_mm=STANDOFF_DIAMETER,
                standoff_axes_normal_to_pcb=True, keycap_sweeps_clear=117,
                keycap_envelope='each KLE width/height times 19.05 mm minus 1 mm; vertical swept prism',
                key_aperture_clusters=len(shapes['apertures'].geoms),
                minimum_c5_clear_depth_normal_to_pcb_mm=round(cap_min_depth, 4),
                c5_11mm_keepout_clear=True, controller_socketed_envelope_clear=True,
                controller_sockets=socket_checks,
                usb_tunnel_clear=True, pcb_plate_edge_clearance_per_side_mm=p.pcb_edge_clearance_mm,
                cover_lip_clearance_per_side_mm=p.cover_lip_clearance_mm)


def print_shape(shape, *, face_down=False):
    app, _ = freecad()
    result = shape.copy()
    if face_down:
        result.rotate(app.Vector(), app.Vector(1, 0, 0), 180)
    bounds = result.BoundBox
    shift = [-bounds.XMin, -bounds.YMin, -bounds.ZMin]
    result.translate(app.Vector(*shift))
    return result, shift


def export_part(out, name, shape, *, face_down=False):
    printable, shift = print_shape(shape, face_down=face_down)
    step = out/(name+'.step')
    shape.exportStep(str(step))
    # MeshPart's angular limit also prevents coarse triangulation of small bores.
    import MeshPart
    mesh = MeshPart.meshFromShape(Shape=printable, LinearDeflection=.025,
                                  AngularDeflection=.12, Relative=False)
    # Force binary STL via Trimesh (FreeCAD's STL preference can be user-specific).
    points, faces = mesh.Topology
    triangulated = trimesh.Trimesh(vertices=np.array([[v.x, v.y, v.z] for v in points]),
                                   faces=np.array(faces), process=True)
    # A tessellated circle need not have vertices at its analytic extrema.
    # Normalize the actual mesh as well (usually a sub-0.002 mm correction).
    mesh_shift = -triangulated.bounds[0]
    triangulated.apply_translation(mesh_shift)
    triangulated.export(out/(name+'.stl'))
    loaded = trimesh.load_mesh(out/(name+'.stl'))
    assert loaded.is_watertight and loaded.is_winding_consistent and loaded.is_volume, name
    assert loaded.body_count == 1 and np.all(loaded.area_faces > 1e-10), name
    assert np.allclose(loaded.bounds[0], [0, 0, 0], atol=2e-5, rtol=0), name
    assert abs(loaded.volume-shape.Volume)/shape.Volume < .002, name
    # Round-trip the CAD export too, not just its mesh.
    _, part = freecad()
    restored = part.read(str(step))
    assert restored.isValid() and len(restored.Solids) == 1, name
    assert math.isclose(restored.Volume, shape.Volume, rel_tol=1e-7), name
    return dict(file=name+'.stl', step_file=step.name,
                size_mm=[round(float(v), 4) for v in loaded.extents],
                triangles=len(loaded.faces), connected_bodies=loaded.body_count,
                watertight=True, consistent_winding=True, positive_volume=True,
                cad_volume_mm3=round(shape.Volume, 4), stl_volume_mm3=round(float(loaded.volume), 4),
                step_roundtrip_valid=True, stl_face_down=face_down,
                stl_translation_after_optional_x_flip_mm=shift,
                stl_additional_mesh_translation_mm=mesh_shift.tolist(),
                sha256=digest(out/(name+'.stl')), step_sha256=digest(step))


def save_assembly(out, p, shapes, plate):
    app, part = freecad()
    doc = app.newDocument('CleaverCaseRev07')
    objects = []

    def add(name, label, shape, color, transparency=0):
        obj = doc.addObject('PartDesign::Feature', name)
        obj.Label, obj.Shape = label, shape
        obj.addProperty('App::PropertyString', 'Role').Role = label
        if obj.ViewObject is not None:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.Transparency = transparency
        objects.append(obj)
        return obj

    base = add('Tray', f'PRINT: base tray — {p.typing_angle_deg:g} degree typing angle', shapes['tray'], (.16, .20, .25))
    for key, value in asdict(p).items():
        base.addProperty('App::PropertyFloat', key, 'Generation parameters')
        setattr(base, key, value)
    base.addProperty('App::PropertyString', 'ParameterEditing').ParameterEditing = (
        'Informational snapshot. Edit parameters.json and rerun source/generate_case.py to rebuild.')
    add('Cover', 'PRINT: removable key bezel (assembled)', assembled(shapes['cover'], p), (.75, .78, .81))
    pcb = box(0, 0, BOARD_W, BOARD_H).difference(unary_union(
        [Point(x, y).buffer(1.1, quad_segs=16) for x, y in MOUNTING_HOLES]))
    add('PCBEnvelope', 'REFERENCE ONLY: PCB envelope + mounting holes',
        assembled(prism(pcb, -PCB_THICKNESS, PCB_THICKNESS), p), (.07, .40, .22))
    add('SwitchPlate', f'REFERENCE: rev{REVISION} 1.5 mm switch/stabilizer plate',
        assembled(prism(plate.simplify(.005, preserve_topology=True), SPACER_HEIGHT, PLATE_THICKNESS), p),
        (.43, .46, .50))
    spacers = []
    for x, y in MOUNTING_HOLES:
        spacer = shapes['spacer'].copy()
        spacer.translate(app.Vector(x, -y, 0))
        spacers.append(assembled(spacer, p))
    add('PlateSpacers', 'PRINT 11: 3.5 mm PCB-to-plate spacers', part.makeCompound(spacers), (.70, .51, .18))
    module = prism(box(MODULE_X-25.5, MODULE_Y-10.5, MODULE_X+25.5, MODULE_Y+10.5), 2.54, 5.1)
    shell = prism(box(MODULE_X+19, MODULE_Y-4.475, MODULE_X+27.5, MODULE_Y+4.475), 4.14, 3.2)
    add('ControllerEnvelope', 'REFERENCE ONLY: socketed controller and USB envelope',
        assembled(module.fuse(shell), p), (.12, .27, .60))
    for ref,y,_ in CONTROLLER_SOCKETS:
        add(ref, f'REFERENCE: {ref} underside Harwin M20-7862042',
            assembled(prism(box(MODULE_X-25.5,y-1.25,MODULE_X+25.5,y+1.25),-9.1,7.5),p),(.04,.04,.05))
    add('C5Envelope', 'REFERENCE ONLY: C5 maximum 10 mm underside height',
        assembled(cylinder(377, 6, -11.6, 10.3, 10), p), (.45, .45, .48))
    keys, _ = read_keys()
    caps = [prism(box(k['x']-(k['w']*U-1)/2, k['y']-(k['h']*U-1)/2,
                      k['x']+(k['w']*U-1)/2, k['y']+(k['h']*U-1)/2), 13, 7)
            for k in keys]
    add('KeycapEnvelopes', 'REFERENCE ONLY: 117 approximate keycaps (not for printing)',
        assembled(part.makeCompound(caps), p), (.31, .35, .39))
    doc.recompute()
    # Avoid creating timestamped FCBak files in this generated artifact folder.
    with tempfile.TemporaryDirectory(prefix='.case-export-', dir=out) as directory:
        saved = Path(directory)/f'Cleaver-case-assembly-rev{REVISION}.FCStd'
        doc.saveAs(str(saved))
        saved.replace(out/saved.name)
    part.export(objects, str(out/f'Cleaver-case-assembly-rev{REVISION}.step'))
    app.closeDocument(doc.Name)


def preview(out, p, shapes):
    """Lightweight, true-plan CAD drawing; no external rendering dependencies."""
    outer, _, _, _ = outlines(p)
    m = p.margin
    head = f'<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="870" viewBox="{-m-8} {-m-18} {BOARD_W+2*m+16} 335">'
    content = [head, '<rect x="-20" y="-30" width="510" height="390" fill="#f5f7fa"/>',
               '<g font-family="sans-serif" fill="#243244">',
               f'<text x="0" y="-13" font-size="6">Cleaver rev{REVISION} — socket supports / removable bezel</text>',
               f'<path d="{svg_path(shapes["deck"])}" fill="#aebac6" stroke="#34465a" stroke-width=".4" fill-rule="evenodd"/>']
    for x, y in cover_screws(p):
        content.append(f'<circle cx="{x}" cy="{y}" r="2.1" fill="#34465a"/>')
    content.extend(['<g transform="translate(0 168)">',
                    f'<path d="{svg_path(outer)}" fill="#e0e7ee" stroke="#34465a" stroke-width=".5"/>',
                    f'<rect width="{BOARD_W}" height="{BOARD_H}" fill="none" stroke="#548567" stroke-width=".4" stroke-dasharray="2 1"/>'])
    for i, (x, y) in enumerate(MOUNTING_HOLES, 1):
        content.extend([f'<circle cx="{x}" cy="{y}" r="3" fill="#bb985b" stroke="#735820" stroke-width=".25"/>',
                        f'<circle cx="{x}" cy="{y}" r="{p.insert_bore_mm/2}" fill="#f5f7fa"/>',
                        f'<text x="{x+4 if x<BOARD_W-20 else x-14}" y="{y+1}" font-size="3">H{i}</text>'])
    content.extend([f'<rect x="{BOARD_W-3}" y="{MODULE_Y-p.usb_opening_width_mm/2}" width="{p.margin+3}" height="{p.usb_opening_width_mm}" fill="#659fc1"/>',
                    '<circle cx="377" cy="6" r="5.5" fill="none" stroke="#b66b53" stroke-width=".4"/>',
                    '<text x="0" y="158" font-size="4">11 x 6 mm standoffs / 5 degree tilt / right-side USB-C / 0.25 mm edge clearance per side</text>',
                    '</g></g></svg>'])
    (out/'case-plan.svg').write_text('\n'.join(content)+'\n')


def render_preview(out, p, records):
    """Optional actual-mesh preview, with explicitly approximate reference caps."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except ImportError:
        return
    rotation = trimesh.transformations.rotation_matrix(math.radians(p.typing_angle_deg), [1, 0, 0])

    def cad_mesh(record, tilt=False):
        mesh = trimesh.load_mesh(out/record['file'])
        mesh.apply_translation(-np.array(record['stl_additional_mesh_translation_mm']))
        mesh.apply_translation(-np.array(record['stl_translation_after_optional_x_flip_mm']))
        if record['stl_face_down']:
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        if tilt:
            mesh.apply_transform(rotation)
            mesh.apply_translation([0, 0, p.front_pcb_top])
        return mesh

    base, cover = cad_mesh(records[0]), cad_mesh(records[1], tilt=True)
    plate = trimesh.load_mesh(ROOT/f'mechanical/rev{REVISION}/Cleaver-top-plate-rev{REVISION}.stl')
    plate.apply_translation([0, 0, SPACER_HEIGHT])
    plate.apply_transform(rotation)
    plate.apply_translation([0, 0, p.front_pcb_top])
    keys, _ = read_keys()
    caps = []
    for key in keys:
        mesh = trimesh.creation.box([key['w']*U-1, key['h']*U-1, 7])
        mesh.apply_translation([key['x'], BOARD_H-key['y'], 16.5])
        mesh.apply_transform(rotation)
        mesh.apply_translation([0, 0, p.front_pcb_top])
        caps.append(mesh)
    caps = trimesh.util.concatenate(caps)
    fig = plt.figure(figsize=(16, 10), facecolor='#f4f6f9')
    views = [[(base, [.31, .40, .50])],
             [(base, [.31, .40, .50]), (plate, [.40, .45, .49]),
              (cover, [.72, .78, .83]), (caps, [.24, .29, .35])]]
    for index, objects in enumerate(views, 1):
        ax = fig.add_subplot(2, 1, index, projection='3d')
        ax.set_facecolor('#f4f6f9')
        triangles, colors = [], []
        light = np.array([-.3, -.5, 1.0])
        light /= np.linalg.norm(light)
        elevation, azimuth = math.radians(42), math.radians(-68)
        view = np.array([math.cos(elevation)*math.cos(azimuth),
                         math.cos(elevation)*math.sin(azimuth), math.sin(elevation)])
        for mesh, color in objects:
            # Back-face culling avoids painter-sort artifacts from large floor
            # triangles on the hidden underside of the enclosure.
            visible = mesh.face_normals@view > 0
            triangles.extend(mesh.triangles[visible])
            brightness = .55+.45*np.clip(mesh.face_normals[visible]@light, 0, 1)
            colors.extend(brightness[:, None]*np.array(color))
        ax.add_collection3d(Poly3DCollection(triangles, facecolors=colors, edgecolors='none',
                                            antialiaseds=False, clip_on=False))
        ax.set(xlim=(-15, BOARD_W+15), ylim=(-15, BOARD_H+15), zlim=(0, 47))
        ax.set_box_aspect((BOARD_W+30, BOARD_H+30, 70), zoom=1.55)
        ax.view_init(elev=42, azim=-68)
        ax.set_axis_off()
        ax.set_title('Base interior — 11 PCB standoffs' if index == 1 else
                     'Assembled — separate cover with 117 keycap clearances', loc='left',
                     fontsize=16, color='#273747', pad=-6)
    fig.text(.05, .03, f'Rev {REVISION}  /  {p.typing_angle_deg:g}° rear-raised  /  right-side USB-C  /  reference keycaps are simplified envelopes',
             fontsize=11, color='#526375')
    fig.subplots_adjust(left=.03, right=.97, top=.94, bottom=.06, hspace=.04)
    fig.savefig(out/'assembly-preview.png', dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parameters', type=Path, default=OUT/'parameters.json')
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    p = Parameters(**json.loads(args.parameters.read_text()))
    p.validate()
    source, plate_file = ROOT/'Cleaver.kicad_pcb', ROOT/f'mechanical/rev{REVISION}/Cleaver-top-plate-rev{REVISION}.stl'
    original_hashes = {path: digest(path) for path in (source, plate_file)}
    plate, _, _ = geometry(top_capacitor_opening=False)
    source_checks = validate_source(p, plate)
    shapes = build(p)
    fit = validate_fit(p, shapes, plate)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    parts = [export_part(out, f'Cleaver-case-base-rev{REVISION}', shapes['tray']),
             export_part(out, f'Cleaver-case-top-cover-rev{REVISION}', shapes['cover'], face_down=True),
             export_part(out, 'PCB-to-plate-spacer-3.5mm', shapes['spacer'])]
    # Real rear-right assembly section, not a generic tolerance block. One PCB
    # boss (H5), USB tunnel, locating lip and one cover screw are retained.
    crop = box(BOARD_W-65, -p.margin-1, BOARD_W+p.margin+1, 33)
    coupon_tray = shapes['tray'].common(assembled(prism(crop, -60, 100), p)).removeSplitter()
    coupon_cover = shapes['cover'].common(prism(crop, -20, 60)).removeSplitter()
    parts.extend([export_part(out, 'USB-and-seat-fit-coupon-base', coupon_tray),
                   export_part(out, 'USB-and-seat-fit-coupon-cover', coupon_cover, face_down=True)])
    for thickness in (.2,.4,.6,.8,1.0):
        shim=prism(box(0,0,49.6,2.0),0,thickness)
        parts.append(export_part(out,f'controller-socket-shim-{thickness:.1f}mm',shim))
    save_assembly(out, p, shapes, plate)
    preview(out, p, shapes)
    render_preview(out, p, parts)
    assert all(digest(path) == before for path, before in original_hashes.items()), 'An input was modified'
    app, part = freecad()
    report = dict(revision=REVISION, source_pcb='../../../Cleaver.kicad_pcb',
                  source_sha256=original_hashes[source],
                  matching_plate=f'../Cleaver-top-plate-rev{REVISION}.stl',
                  matching_plate_sha256=original_hashes[plate_file], parameters=asdict(p),
                  source_checks=source_checks, fit_checks=fit,
                  stack_mm=dict(pcb_underside=-1.6, pcb_top=0, plate_bottom=3.5, plate_top=5,
                                cover_underside=p.cover_underside_above_pcb_mm, cover_top=p.cover_top),
                  pcb_front_to_rear_rise_mm=round(BOARD_H*math.sin(math.radians(p.typing_angle_deg)), 4),
                  cover_screws_pcb_xy_mm=cover_screws(p), spacer_quantity=11,
                  insert_quantity=19, pcb_screw='11 x M2x10 mm', cover_screw='8 x M2x6 mm',
                  intended_insert='M2, approximately 3.2 mm OD x 4 mm long; 3.0 mm pilot MUST be coupon-tested',
                  physical_fit_tested=False,
                  assumptions=['U1 male insulators seat on carrier; 8.13mm posts into underside Harwin sockets',
                               'Backstops have 0.70mm nominal unshimmed gap; select shims for measured 0.1–0.3mm clearance before mating',
                               'Standard MX keycap plan size: KLE pitch minus 1 mm',
                               'USB shell projection and height are approximate; test actual cable/module',
                               'Hardware, switch/stabilizer clip fit, material stiffness and shrinkage require physical testing'],
                  coordinates=f'CAD/assembly: PCB (x,y,z) -> (x,147.6375-y,z), then rotate +{p.typing_angle_deg:g} degrees about X and raise PCB front; STL parts independently normalized to bed',
                  tools=dict(freecad='.'.join(app.Version()[:3]), occ=part.OCC_VERSION,
                             kicad=pcbnew.Version(), shapely=shapely.__version__, trimesh=trimesh.__version__),
                  parts=parts)
    (out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    for item in parts:
        print(f'{item["file"]}: {item["size_mm"]} mm; one watertight body')
    print(f'11 PCB standoffs; 117 keycap sweeps clear; C5 clear depth {fit["minimum_c5_clear_depth_normal_to_pcb_mm"]} mm')


if __name__ == '__main__':
    main()
