#!/usr/bin/env python3
"""Mechanical rev0.10: underside screws and captured badge for the rev0.9 PCB.

Run with the same KiCad/FreeCAD Python environment as generate_case.py.
PCB, switch plate and electronics release identifiers remain independent.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path

from shapely import Point, box
import trimesh

import generate_case as legacy
from generate_case import (
    BOARD_H, BOARD_W, CONTROLLER_SOCKETS, FLANGE, INSERT, APERTURE, LIGHT_BORE,
    LOGO_X, LOGO_Y, MODULE_X, MOUNTING_HOLES, PCB_THICKNESS, PLATE_H,
    PLATE_TOP, PLATE_THICKNESS, SPACER_HEIGHT, STANDOFF_DIAMETER, ROOT,
    assembled, badge_shapes, cylinder, digest, export_part, freecad, geometry,
    prism, rectangle, save_assembly, svg_path, usb_tool, validate_fit,
    validate_source, world_point, write_badge_template,
)
from design import read_keys
from generate_case import REVISION as PCB_REVISION, SOURCE_PCB

MECHANICAL_REVISION = '0.10'
OUT = ROOT/f'mechanical/rev{MECHANICAL_REVISION}/case'


@dataclass(frozen=True)
class Parameters(legacy.Parameters):
    typing_angle_deg: float = 3.0
    floor_mm: float = 2.2
    front_under_pcb_clearance_mm: float = 5.6
    end_wall_extra_mm: float = 2.0
    boss_width_mm: float = 12.0
    boss_depth_mm: float = 6.0
    boss_drop_mm: float = 5.0
    boss_root_extra_mm: float = 2.0
    boss_socket_clearance_mm: float = .25
    underside_head_bore_mm: float = 4.6
    screw_grip_mm: float = 4.5
    screw_length_mm: float = 8.0
    blind_insert_depth_mm: float = 4.5
    front_bevel_width_mm: float = 2.0
    front_bevel_height_mm: float = 1.2
    gasket_recess_mm: float = .4
    gasket_stock_mm: float = .8

    @property
    def end_margin(self):
        return self.margin+self.end_wall_extra_mm

    @property
    def cover_screw_offset(self):
        return 4.5

    @property
    def boss_bottom(self):
        return self.cover_underside_above_pcb_mm-self.boss_drop_mm

    @property
    def head_seat(self):
        return self.boss_bottom-self.screw_grip_mm

    @property
    def gasket_gap(self):
        return .2+self.gasket_recess_mm

    def validate(self):
        super().validate()
        assert self.floor_mm >= 2.2
        assert self.boss_depth_mm/2-1.6 >= 1.4, 'Insert needs at least 1.4 mm radial plastic'
        assert self.end_margin-self.cover_screw_offset-self.boss_depth_mm/2-self.boss_socket_clearance_mm >= 1
        assert self.cover_screw_offset-self.boss_depth_mm/2-self.boss_socket_clearance_mm > self.pcb_edge_clearance_mm
        assert self.cover_top-self.boss_bottom-self.blind_insert_depth_mm >= 2.4
        assert 3 <= self.screw_length_mm-self.screw_grip_mm <= 3.8
        assert self.blind_insert_depth_mm >= 4.3
        assert self.cover_thickness_mm-self.gasket_recess_mm >= 1.8
        assert .15 <= 1-self.gasket_gap/self.gasket_stock_mm <= .35
        assert self.cover_thickness_mm-self.front_bevel_height_mm >= 1.2


def cover_screws(p):
    return legacy.cover_screws(p)


def outlines(p):
    _, pocket, apertures, _ = legacy.outlines(p)
    m, e, r = p.margin, p.end_margin, p.outer_corner_radius_mm
    outer = box(-m+r, -e+r, BOARD_W+m-r, PLATE_H+e-r).buffer(r, quad_segs=16)
    deck = outer.difference(apertures.union(rectangle(APERTURE)))
    assert deck.is_valid and deck.geom_type == 'Polygon'
    return outer, pocket, apertures, deck


def boss_plan(x, y, p):
    r = .8
    return box(x-p.boss_width_mm/2+r, y-p.boss_depth_mm/2+r,
               x+p.boss_width_mm/2-r, y+p.boss_depth_mm/2-r).buffer(r, quad_segs=12)


def boss_shape(x, y, p):
    """Rounded pillar with two 45-degree root ribs, printed upward from the lid."""
    app, part = freecad()
    pillar = prism(boss_plan(x, y, p), p.boss_bottom, p.boss_drop_mm)
    for sign in (-1, 1):
        inner = x+sign*(p.boss_width_mm/2-1)
        outer = x+sign*(p.boss_width_mm/2+p.boss_root_extra_mm)
        ztop = p.cover_underside_above_pcb_mm
        points = [app.Vector(inner, BOARD_H-y-2, ztop-3),
                  app.Vector(outer, BOARD_H-y-2, ztop),
                  app.Vector(inner, BOARD_H-y-2, ztop)]
        rib = part.Face(part.makePolygon(points+[points[0]])).extrude(app.Vector(0, 4, 0))
        pillar = pillar.fuse(rib)
    return pillar.removeSplitter()


def boss_socket(x, y, p):
    # A rounded rectangular pocket encloses pillar AND root ribs. Its floor is
    # the axial hard stop; the rest of the perimeter remains the cover seat.
    r = .8
    half = p.boss_width_mm/2+p.boss_root_extra_mm
    plan = box(x-half+r, y-p.boss_depth_mm/2+r,
               x+half-r, y+p.boss_depth_mm/2-r).buffer(r, quad_segs=12)
    plan = plan.buffer(p.boss_socket_clearance_mm, quad_segs=12)
    return prism(plan, p.boss_bottom, p.boss_drop_mm+.1)


def bevel_tool(p):
    app, part = freecad()
    front = PLATE_H+p.end_margin
    # Triangular section removes only the outer front lip, not the full bezel.
    points = [app.Vector(-p.margin-1, BOARD_H-front+p.front_bevel_width_mm, p.cover_top),
              app.Vector(-p.margin-1, BOARD_H-front-1,
                         p.cover_top-p.front_bevel_height_mm*(1+1/p.front_bevel_width_mm)),
              app.Vector(-p.margin-1, BOARD_H-front-1, p.cover_top+1),
              app.Vector(-p.margin-1, BOARD_H-front+p.front_bevel_width_mm, p.cover_top+1)]
    return part.Face(part.makePolygon(points+[points[0]])).extrude(app.Vector(BOARD_W+2*p.margin+2, 0, 0))


def gasket_plan():
    return rectangle(FLANGE).difference(rectangle(APERTURE))


def badge_rails(p):
    """Side and front shoulders surround the flange; rear stays clear of keys."""
    left, rear, right, front = rectangle(FLANGE).bounds
    rails = [
        box(left-1.4, rear+1, left-.2, front-1),
        box(right+.2, rear+1, right+1.4, front-1),
        box(left+2, front+.2, right-2, front+1.4),
    ]
    return [prism(poly, p.cover_underside_above_pcb_mm-1, 1) for poly in rails]


def build(p, *, mounts=MOUNTING_HOLES, mount_top=-PCB_THICKNESS, usb_opening=None):
    p.validate()
    app, part = freecad()
    outer, pocket, apertures, deck = outlines(p)
    ztop = p.cover_underside_above_pcb_mm
    above_floor = part.makeBox(600, 300, 100, app.Vector(-50, -50, p.floor_mm))
    above_desk = part.makeBox(600, 300, 100, app.Vector(-50, -50, 0))
    tray = assembled(prism(outer, -60, ztop+60), p).common(above_desk)
    tray = tray.cut(assembled(prism(pocket, -60, ztop+65), p).common(above_floor))
    boss_clip = part.makeBox(600, 300, 100, app.Vector(-50, -50, p.floor_mm-.3))
    bosses = [assembled(cylinder(x, y, -60, STANDOFF_DIAMETER, 60+mount_top), p).common(boss_clip)
              for x, y in mounts]
    supports = [assembled(prism(box(MODULE_X-25.2, y-1.1, MODULE_X+25.2, y+1.1),
                               -60, 60-PCB_THICKNESS-7.5-p.socket_support_gap_mm), p).common(boss_clip)
                for _, y, _ in CONTROLLER_SOCKETS]
    tray = tray.multiFuse(bosses+supports)
    holes = [cylinder(x, y, mount_top-p.insert_pocket_depth_mm,
                      p.insert_bore_mm, p.insert_pocket_depth_mm+.1) for x, y in mounts]
    rebate = box(-p.rebate_offset, -p.rebate_offset,
                 BOARD_W+p.rebate_offset, PLATE_H+p.rebate_offset)
    holes.append(prism(rebate, ztop-p.cover_lip_depth_mm-.2, p.cover_lip_depth_mm+1))
    sockets = [boss_socket(x, y, p) for x, y in cover_screws(p)]
    holes.extend(sockets)
    for x, y in cover_screws(p):
        holes.extend([
            cylinder(x, y, -60, p.underside_head_bore_mm, 60+p.head_seat),
            cylinder(x, y, p.head_seat-.1, p.cover_screw_clearance_mm, p.screw_grip_mm+.2),
        ])
    usb_opening = usb_tool(p) if usb_opening is None else usb_opening
    holes.append(usb_opening)
    tray = tray.cut(assembled(part.makeCompound(holes), p)).removeSplitter()

    lip = box(-p.lip_outer_offset, -p.lip_outer_offset,
              BOARD_W+p.lip_outer_offset, PLATE_H+p.lip_outer_offset).difference(
                  box(-p.cover_lip_inner_offset_mm, -p.cover_lip_inner_offset_mm,
                      BOARD_W+p.cover_lip_inner_offset_mm, PLATE_H+p.cover_lip_inner_offset_mm))
    locating_lip = prism(lip, ztop-p.cover_lip_depth_mm, p.cover_lip_depth_mm)
    locating_lip = locating_lip.cut(part.makeCompound(sockets))
    cover = prism(deck, ztop, p.cover_thickness_mm).fuse(locating_lip)
    cover = cover.multiFuse([boss_shape(x, y, p) for x, y in cover_screws(p)]+badge_rails(p))
    blind_bores = [cylinder(x, y, p.boss_bottom-.1, p.insert_bore_mm,
                            p.blind_insert_depth_mm+.1) for x, y in cover_screws(p)]
    # 0.4 mm recess plus the existing 0.2 mm flange gap compresses 0.8 mm foam
    # to 0.6 mm. Preload flows through the well to the switch plate, not LEDs.
    gasket_pocket = prism(rectangle((FLANGE[0]+.4, FLANGE[1]+.4)), ztop-.01,
                          p.gasket_recess_mm+.01)
    cover = cover.cut(part.makeCompound(blind_bores+[gasket_pocket, usb_opening, bevel_tool(p)])).removeSplitter()
    carrier, insert = badge_shapes(p)
    spacer = cylinder(0, 0, 0, STANDOFF_DIAMETER, SPACER_HEIGHT).cut(cylinder(0, 0, -.1, 2.2, SPACER_HEIGHT+.2))
    gasket = prism(gasket_plan(), ztop-.2, p.gasket_gap)
    shapes = dict(tray=tray, cover=cover, spacer=spacer, apertures=apertures, deck=deck,
                  logo_carrier=carrier, logo_insert=insert, logo_gasket=gasket)
    for label in ('tray', 'cover', 'spacer', 'logo_carrier', 'logo_insert', 'logo_gasket'):
        shape = shapes[label]
        assert not shape.isNull() and shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 0, label
    return shapes


def height_comparison(p):
    old = legacy.Parameters()
    keys, _ = read_keys()
    home = next(key for key in keys if key['legend'] == 'A')

    def heights(params, end_margin, bevel):
        return dict(
            front_edge_mm=world_point(BOARD_W/2, PLATE_H+end_margin, params.cover_top-bevel, params)[2],
            front_bezel_full_height_mm=world_point(BOARD_W/2, PLATE_H, params.cover_top, params)[2],
            home_row_pcb_top_mm=world_point(home['x'], home['y'], 0, params)[2],
            home_row_keycap_reference_top_mm=world_point(home['x'], home['y'], 20, params)[2],
            rear_cover_top_mm=world_point(BOARD_W/2, -end_margin, params.cover_top, params)[2],
        )
    before = heights(old, old.margin, 0)
    after = heights(p, p.end_margin, p.front_bevel_height_mm)
    return dict(baseline_revision='0.9', datum='bare case bottom, no feet; keycap reference Z=20, not a measured cap',
                home_row_reference_pcb_xy_mm=[home['x'], home['y']],
                before={k: round(v, 4) for k, v in before.items()},
                after={k: round(v, 4) for k, v in after.items()},
                reduction={k: round(before[k]-after[k], 4) for k in before})


def validate_service_fit(p, shapes, plate):
    fit = validate_fit(p, shapes, plate)
    app, part = freecad()
    tray, cover = shapes['tray'], shapes['cover']
    hardware = []
    outer, pocket, _, _ = outlines(p)
    hardware_shapes = []
    for i, (x, y) in enumerate(cover_screws(p), 1):
        bore = cylinder(x, y, p.boss_bottom-.01, p.insert_bore_mm-.05, p.blind_insert_depth_mm)
        assert cover.common(bore).Volume < 1e-6, f'C{i}: blind bore obstructed'
        # Independently probe the continuous exterior roof above each insert.
        roof = cylinder(x, y, p.cover_top-.2, 4, .1)
        assert abs(cover.common(roof).Volume-roof.Volume) < 1e-6, f'C{i}: visible top hole'
        ring = prism(boss_plan(x, y, p).buffer(-.1), p.boss_bottom-.1, .05).cut(
            cylinder(x, y, p.boss_bottom-.2, p.cover_screw_clearance_mm+.1, .3))
        ring = assembled(ring, p)
        assert abs(tray.common(ring).Volume-ring.Volume) < 1e-6, f'C{i}: hard stop absent'
        screw = cylinder(x, y, p.head_seat, 2, p.screw_length_mm).fuse(
            cylinder(x, y, p.head_seat-2, 3.8, 2))
        assert cover.common(screw).Volume < 1e-6
        assert tray.common(assembled(screw, p)).Volume < 1e-6
        insert = cylinder(x, y, p.boss_bottom, 3.2, 4).cut(
            cylinder(x, y, p.boss_bottom-.1, 2.1, 4.2))
        hardware_shapes.extend([screw, insert])
        # Clearance for a straight slim driver all the way out through the bottom.
        driver = assembled(cylinder(x, y, -60, 4.4, 60+p.head_seat-.01), p)
        assert tray.common(driver).Volume < 1e-6
        edge = min(outer.boundary.distance(Point(x, y)), pocket.distance(Point(x, y)))
        hardware.append(dict(reference=f'C{i}', pcb_xy_mm=[x, y], screw='M2 x 8 socket head',
                             screw_axis='normal to PCB, 3 degrees from vertical at default settings',
                             head_seat_z_pcb_mm=p.head_seat, head_height_max_mm=2,
                             head_diameter_max_mm=3.8, straight_driver_max_mm=4.4,
                             thread_engagement_mm=p.screw_length_mm-p.screw_grip_mm,
                             blind_bore_tip_clearance_mm=p.blind_insert_depth_mm-(p.screw_length_mm-p.screw_grip_mm),
                             bottom_head_recess_min_edge_material_mm=round(edge-p.underside_head_bore_mm/2, 4),
                             hard_stop_present=True, top_unpierced=True, driver_path_clear=True))
    shapes['cover_hardware'] = part.makeCompound(hardware_shapes)
    # Check actual solids, including new rails and pillars, against every full
    # keycap sweep rather than relying on the 2D deck alone.
    keys, _ = read_keys()
    for key in keys:
        swept = box(key['x']-(key['w']*19.05-1)/2, key['y']-(key['h']*19.05-1)/2,
                    key['x']+(key['w']*19.05-1)/2, key['y']+(key['h']*19.05-1)/2)
        assert cover.common(prism(swept, 0, 30)).Volume < 1e-6, key['ref']
    gasket = shapes['logo_gasket']
    plate_shape = prism(plate.simplify(.005, preserve_topology=True), SPACER_HEIGHT, PLATE_THICKNESS)
    for label, shape in [('cover', cover), ('well', shapes['logo_carrier']),
                         ('insert', shapes['logo_insert']), ('plate', plate_shape)]:
        assert gasket.common(shape).Volume < 1e-6, f'gasket/{label}'
    # Contact patches establish the mechanical preload path without assuming
    # that an arbitrary stiff gasket will compress at a safe force.
    contact = gasket_plan().buffer(-.05)
    below = prism(contact, p.cover_underside_above_pcb_mm-.25, .04)
    above = prism(contact, p.cover_underside_above_pcb_mm+p.gasket_recess_mm+.01, .04)
    assert abs(shapes['logo_insert'].common(below).Volume-below.Volume) < 1e-6
    assert abs(cover.common(above).Volume-above.Volume) < 1e-6
    fit.update(bottom_fasteners=hardware, actual_cover_solid_key_sweeps_clear=117,
               height_comparison=height_comparison(p),
               logo_gasket=dict(stock_thickness_mm=p.gasket_stock_mm, installed_gap_mm=p.gasket_gap,
                                nominal_compression_percent=round(100*(1-p.gasket_gap/p.gasket_stock_mm), 2),
                                load_path='cover -> soft foam -> insert flange -> opaque well -> switch plate',
                                shoulder_clearance_mm=.2, physical_preload_and_rattle_tested=False))
    fit['logo']['removal'] = 'Remove eight underside screws, lift cover, lift gasket and badge from well'
    fit['logo']['retaining_flange_vertical_clearance_mm'] = .2
    fit['logo']['retaining_flange_clearance_taken_up_by_gasket'] = True
    return fit


def export_coupons(out, p, shapes, plate):
    parts = []
    # Rear-right real section retains a cover fastener, H5, both socket supports
    # and USB. Also export the corresponding real plate section.
    crop = box(BOARD_W-65, -p.end_margin-1, BOARD_W+p.margin+1, 33)
    crops = [('USB-and-seat-fit-coupon', crop)]
    # Front screw, joint, axial stop, insert and lower front-edge bevel.
    crops.append(('Front-fastener-fit-coupon', box(130, PLATE_H-5, 160, PLATE_H+p.end_margin+1)))
    for name, section in crops:
        parts.append(export_part(out, name+'-base',
                                 shapes['tray'].common(assembled(prism(section, -60, 100), p)).removeSplitter()))
        parts.append(export_part(out, name+'-cover',
                                 shapes['cover'].common(prism(section, -20, 60)).removeSplitter(), face_down=True))
    parts.append(export_part(out, 'USB-and-seat-fit-coupon-plate',
                             prism(plate.intersection(crop), SPACER_HEIGHT, PLATE_THICKNESS)))
    # A plate with integral 3.4 mm gauge rails seats the cover at the exact
    # installed height, so the FULL badge/gasket stack can be tested on a desk.
    crop = box(LOGO_X-FLANGE[0]/2-4, LOGO_Y-APERTURE[1]/2-1,
               LOGO_X+FLANGE[0]/2+4, PLATE_H+p.end_margin+1)
    parts.append(export_part(out, 'Logo-fit-coupon-cover',
                             shapes['cover'].common(prism(crop, -20, 60)).removeSplitter(), face_down=True))
    coupon_plate = prism(plate.intersection(crop), SPACER_HEIGHT, PLATE_THICKNESS)
    for sign in (-1, 1):
        x = LOGO_X+sign*(FLANGE[0]/2+2.7)
        rail = box(x-.5, LOGO_Y-8, x+.5, LOGO_Y+8)
        coupon_plate = coupon_plate.fuse(prism(rail, PLATE_TOP,
                                               p.cover_underside_above_pcb_mm-PLATE_TOP))
    coupon_plate = coupon_plate.removeSplitter()
    assert coupon_plate.common(shapes['cover']).Volume < 1e-6
    parts.append(export_part(out, 'Logo-fit-coupon-plate-with-height-gauges', coupon_plate))
    # Matching longitudinal side-wall sections give a continuous profile gauge
    # without the disconnected islands of a section through the key openings.
    section = box(-p.margin-1, -p.end_margin-1, -.3, PLATE_H+p.end_margin+1)
    parts.append(export_part(out, 'Lower-profile-section-base',
                             shapes['tray'].common(assembled(prism(section, -60, 100), p)).removeSplitter()))
    parts.append(export_part(out, 'Lower-profile-section-cover',
                             shapes['cover'].common(prism(section, -20, 60)).removeSplitter(), face_down=True))
    return parts


def drawings(out, p, shapes, fit):
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="560" viewBox="-17 -30 490 225">',
             '<rect x="-17" y="-30" width="490" height="225" fill="#f5f7fa"/>',
             '<g font-family="sans-serif" fill="#243244">',
             '<text x="0" y="-16" font-size="7">Cleaver mechanical rev0.10 / PCB rev0.9</text>',
             f'<path d="{svg_path(shapes["deck"])}" fill="#aebac6" stroke="#34465a" stroke-width=".4" fill-rule="evenodd"/>',
             f'<path d="{svg_path(rectangle(INSERT))}" fill="#6ad4e8" stroke="#247d91" stroke-width=".3"/>']
    for i, (x, y) in enumerate(cover_screws(p), 1):
        lines.append(f'<path d="{svg_path(boss_plan(x,y,p))}" fill="none" stroke="#34465a" stroke-width=".35" stroke-dasharray="1 1"/>')
        lines.append(f'<text x="{x+9}" y="{y+1}" font-size="3">C{i}</text>')
    lines.extend(['<text x="0" y="181" font-size="4">Dashed: hidden underside fasteners / solid top / 3 degree tilt / front-edge bevel</text>',
                  '</g></svg>'])
    (out/'case-plan.svg').write_text('\n'.join(lines)+'\n')
    # True dimensions at 1 SVG unit = 1 mm; printable foam cutting pattern.
    (out/'Logo-gasket-cut-template.svg').write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="63.8mm" height="38.4mm" viewBox="0 0 63.8 38.4">\n'
        '<path d="M5 5h53.8v28.4H5Z M6.3 6.3h51.2v25.8H6.3Z" fill="none" stroke="black" stroke-width=".1"/>\n'
        '</svg>\n')
    # Dimensioned section diagrams; these describe the actual nominal stack.
    (out/'assembly-sections.svg').write_text(f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="620" viewBox="0 0 240 124">
<rect width="240" height="124" fill="#f5f7fa"/>
<g font-family="sans-serif" fill="#243244" font-size="3">
<text x="8" y="8" font-size="5">rev0.10 assembly sections — dimensions normal to PCB (mm)</text>
<text x="8" y="17" font-size="4">Cover fastener / schematic section</text>
<path d="M10 22h66v7H10Z M28 29h30v15H28Z" fill="#aebac6"/>
<path d="M10 30h16v16h34V30h16v44H10Z" fill="#d8c29c"/>
<rect x="38" y="32" width="10" height="12" fill="#aa8247"/>
<path d="M40 35h6v25h4v6H36v-6h4Z" fill="#56616c"/>
<path d="M36 66v10 M50 66v10" stroke="#56616c" stroke-width=".3"/>
<text x="80" y="26">Continuous 2.4 mm exterior</text>
<text x="80" y="34">M2 insert: OD ~3.2 x 4</text>
<text x="80" y="41">Blind pilot: diameter 3.0 x 4.5</text>
<text x="80" y="48">Boss meets hard stop at Z={p.boss_bottom:g}</text>
<text x="80" y="55">Grip 4.5 / engagement 3.5</text>
<text x="80" y="62">M2 x 8 socket-head screw</text>
<text x="80" y="69">Flat seat Z={p.head_seat:g}; bore diameter 4.6</text>
<text x="8" y="86" font-size="4">Badge stack / section through retaining flange</text>
<rect x="10" y="92" width="66" height="5" fill="#aebac6"/>
<rect x="22" y="97" width="42" height="3" fill="#666"/>
<rect x="22" y="100" width="42" height="4" fill="#6ad4e8"/>
<rect x="22" y="104" width="42" height="9" fill="#333"/>
<rect x="10" y="113" width="66" height="4" fill="#c7ba98"/>
<text x="80" y="95">Cover underside 8.4; recess roof 8.8</text>
<text x="80" y="102">Soft foam: 0.8 stock -&gt; 0.6 installed</text>
<text x="80" y="109">Badge flange Z=7.4–8.2; well top 7.4</text>
<text x="80" y="116">Plate top 5.0; well bottom 0.8 above PCB</text>
</g></svg>
''')
    heights = fit['height_comparison']
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="350" viewBox="-15 -50 230 75">',
             '<rect x="-15" y="-50" width="230" height="75" fill="#f5f7fa"/>',
             '<g font-family="sans-serif" font-size="3.5" fill="#243244">',
             '<text x="-8" y="-42" font-size="5">Bare-case profile comparison / actual CAD heights</text>']
    for label, params, margin, bevel, color in [
        ('rev0.9 / 5 degrees', legacy.Parameters(), legacy.Parameters().margin, 0, '#b66b53'),
        ('rev0.10 / 3 degrees', p, p.end_margin, p.front_bevel_height_mm, '#247d91'),
    ]:
        rear = world_point(0, -margin, params.cover_top, params)
        front = world_point(0, PLATE_H+margin, params.cover_top-bevel, params)
        transition = world_point(0, PLATE_H+margin-(p.front_bevel_width_mm if bevel else 0),
                                 params.cover_top, params)
        # Y=0 is PCB front; view horizontal axis points rearwards.
        lines.append(f'<path d="M{front[1]:.4f} 0 V{-front[2]:.4f} L{transition[1]:.4f} {-transition[2]:.4f} L{rear[1]:.4f} {-rear[2]:.4f} V0Z" fill="none" stroke="{color}" stroke-width=".5"/>')
    lines.extend([f'<text x="0" y="10">Front edge {heights["before"]["front_edge_mm"]:.2f} → {heights["after"]["front_edge_mm"]:.2f} mm</text>',
                  f'<text x="0" y="17">Home-row reference key top {heights["before"]["home_row_keycap_reference_top_mm"]:.2f} → {heights["after"]["home_row_keycap_reference_top_mm"]:.2f} mm (same caps)</text>',
                  '<text x="145" y="10" fill="#b66b53">rev0.9 / 5°</text>',
                  '<text x="145" y="17" fill="#247d91">rev0.10 / 3°</text>', '</g></svg>'])
    (out/'height-comparison.svg').write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parameters', type=Path, default=OUT/'parameters.json')
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    p = Parameters(**json.loads(args.parameters.read_text())) if args.parameters.is_file() else Parameters()
    p.validate()
    pcb = SOURCE_PCB
    plate_file = ROOT/f'mechanical/rev{PCB_REVISION}/Cleaver-top-plate-rev{PCB_REVISION}.stl'
    hashes = {path: digest(path) for path in (pcb, plate_file)}
    plate, _, _ = geometry(top_capacitor_opening=False)
    source_checks = validate_source(p, plate)
    print('Building mechanical rev0.10 for PCB rev0.9', flush=True)
    shapes = build(p)
    fit = validate_service_fit(p, shapes, plate)
    print('CAD fit, hardware, badge and key sweeps passed; exporting', flush=True)
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    (out/'parameters.json').write_text(json.dumps(asdict(p), indent=2)+'\n')
    parts = [
        export_part(out, f'Cleaver-case-base-rev{MECHANICAL_REVISION}', shapes['tray']),
        export_part(out, f'Cleaver-case-top-cover-rev{MECHANICAL_REVISION}', shapes['cover'], face_down=True),
        export_part(out, 'PCB-to-plate-spacer-3.5mm', shapes['spacer']),
        export_part(out, 'Logo-light-well', shapes['logo_carrier'], face_down=True),
        export_part(out, 'Logo-insert-blank', shapes['logo_insert'], face_down=True),
        export_part(out, 'Logo-gasket-cutting-pattern-0.8mm', prism(gasket_plan(), 0, p.gasket_stock_mm)),
    ]
    parts.extend(export_coupons(out, p, shapes, plate))
    for thickness in (.2, .4, .6, .8, 1.0):
        parts.append(export_part(out, f'controller-socket-shim-{thickness:.1f}mm',
                                 prism(box(0, 0, 49.6, 2), 0, thickness)))
    write_badge_template(out, p)
    save_assembly(out, p, shapes, plate, mechanical_revision=MECHANICAL_REVISION,
                  generator_script='source/generate_case_service.py')
    drawings(out, p, shapes, fit)
    assert all(digest(path) == before for path, before in hashes.items()), 'Input changed'
    app, part = freecad()
    report = dict(
        mechanical_revision=MECHANICAL_REVISION, compatible_pcb_revision=PCB_REVISION,
        source_pcb='../../../source/baselines/rev0.9/Cleaver.kicad_pcb', source_sha256=hashes[pcb],
        matching_plate=f'../../rev{PCB_REVISION}/{plate_file.name}', matching_plate_sha256=hashes[plate_file],
        parameters=asdict(p), source_checks=source_checks, fit_checks=fit,
        hardware=dict(pcb_screws='11 x M2 x 10', cover_screws='8 x M2 x 8 socket head',
                      inserts='19 x M2, approximately OD 3.2 x 4 mm (11 base, 8 cover)',
                      foam='one 0.8 mm soft silicone-foam frame; cut SVG at 100 percent',
                      spacer_quantity=11),
        physical_fit_tested=False,
        physical_checks=['insert fit and pullout / repeated assembly', 'badge preload and rattle',
                         'floor stiffness and print warping', 'switch/stabilizer clips and real keycaps',
                         'actual module/socket/USB cable fit and support shims'],
        tools=dict(freecad='.'.join(app.Version()[:3]), occ=part.OCC_VERSION,
                   kicad=legacy.pcbnew.Version(), shapely=legacy.shapely.__version__, trimesh=trimesh.__version__),
        source_files={str(path.relative_to(ROOT)): digest(path) for path in (
            Path(__file__), ROOT/'source/generate_case.py', ROOT/'source/generate_mechanical.py',
            ROOT/'source/generate_top_plate.py', ROOT/'source/logo_interface.py',
            ROOT/'source/design.py', ROOT/'source/build_3d_models.py')},
        coordinates='Base is desk-flat; cover/badge STEP uses PCB coordinates; assembly STEP/FCStd transforms all parts; STL individually bed-oriented',
        parts=parts,
    )
    report['assembly_sha256'] = {path.name: digest(path) for path in (
        out/f'Cleaver-case-assembly-rev{MECHANICAL_REVISION}.step',
        out/f'Cleaver-case-assembly-rev{MECHANICAL_REVISION}.FCStd')}
    (out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    for record in parts:
        print(f'{record["file"]}: {record["size_mm"]} mm; one watertight body')
    print(json.dumps(fit['height_comparison'], indent=2))


if __name__ == '__main__':
    main()
