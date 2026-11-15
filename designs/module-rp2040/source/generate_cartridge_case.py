#!/usr/bin/env python3
"""Rev0.11 cartridge case, integral-boss switch plate and replaceable USB bezel.

Run upgrade_rev11_mounting.py first. This generator reads the active PCB without
modifying it. --usb-only exports a fitted bezel from measured opening offsets.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import json
import math
from pathlib import Path
import tempfile

import numpy as np
import pcbnew
from shapely import Point, box, unary_union
import trimesh

from design import BOARD_H, BOARD_W, CONTROLLER_SOCKETS, MODULE_X, MODULE_Y, ROOT, REVISION, read_keys
import generate_case as common
import generate_case_service as service
from generate_case import assembled, cylinder, digest, export_part as export_cad_part, freecad, prism, world_point
from coupon_labels import label_coupon
from generate_mechanical import PLATE_H, geometry, svg_path, export_dxf, export_svg
from generate_top_plate import validate_pcb, fit_coupon, export_stl
from logo_interface import APERTURE, FLANGE, INSERT, LOGO_X, LOGO_Y, rectangle, logo_leds
from mounting_interface import (
    BASE_POSTS, PCB_ATTACHMENTS, mounting_specs, PLATE_BOSS_DIAMETER,
    PLATE_BOSS_ROOT_DIAMETER, SHORT_INSERT_PILOT_DEPTH, SHORT_INSERT_LENGTH,
)

OUT = ROOT/f'mechanical/rev{REVISION}/case'
PLATE_OUT = OUT.parent
PLATE_BOTTOM, PLATE_TOP = 3.5, 5.0


def print_group(name):
    """Keep fit fixtures and measuring aids separate from installed parts."""
    if 'coupon' in name.lower() or name in (
        'Controller-insertion-support-jig', 'USB-bezel-blank',
        'Logo-gasket-cutting-pattern-0.8mm',
    ):
        return 'test-prints'
    return 'final-prints'


def export_part(out, name, shape, **options):
    group = print_group(name)
    folder = out/group
    folder.mkdir(parents=True, exist_ok=True)
    label = None
    if group == 'test-prints':
        shape, label = label_coupon(name, shape)
    record = export_cad_part(folder, name, shape, **options)
    if label:
        record['fit_label'] = label
    for field in ('file', 'step_file'):
        record[field] = f'{group}/{record[field]}'
    return record


@dataclass(frozen=True)
class Parameters(service.Parameters):
    usb_bezel_center_y_mm: float = 14.5
    usb_bezel_width_mm: float = 24.0
    usb_bezel_flange_width_mm: float = 28.0
    usb_bezel_depth_mm: float = 2.0
    usb_bezel_flange_depth_mm: float = 1.8
    usb_bezel_bottom_mm: float = -2.0
    usb_bezel_flange_bottom_mm: float = -1.0
    usb_bezel_clearance_mm: float = .25
    usb_port_y_offset_mm: float = 0.0
    usb_port_z_offset_mm: float = 0.0

    def validate(self):
        # Legacy's positivity rule predates signed offsets and datums.
        shared = {name: getattr(self, name) for name in service.Parameters.__dataclass_fields__}
        # The old fixed tunnel's roof rule does not apply to a replaceable side
        # insert. Validate its real opening/webs below, including measured Z.
        shared.update(usb_opening_width_mm=16, usb_opening_height_mm=7.2, usb_center_above_pcb_mm=5.74)
        service.Parameters(**shared).validate()
        assert all(math.isfinite(v) for v in asdict(self).values())
        assert self.usb_opening_width_mm > 0 and self.usb_opening_height_mm > 0
        assert 0 < self.usb_bezel_depth_mm < self.wall_mm
        assert self.usb_bezel_flange_depth_mm >= 1.5
        assert self.usb_bezel_flange_width_mm-self.usb_bezel_width_mm >= 4
        assert .15 <= self.usb_bezel_clearance_mm <= .35
        assert self.usb_bezel_bottom_mm < self.usb_bezel_flange_bottom_mm < 0
        cy, cz = self.port_center
        half = self.usb_bezel_width_mm/2
        assert self.usb_bezel_center_y_mm-half+1 <= cy-self.usb_opening_width_mm/2
        assert cy+self.usb_opening_width_mm/2 <= self.usb_bezel_center_y_mm+half-1
        assert self.usb_bezel_bottom_mm+1 <= cz-self.usb_opening_height_mm/2
        assert cz+self.usb_opening_height_mm/2 <= self.cover_top-1, 'Opening leaves less than 1 mm top web'

    @property
    def port_center(self):
        return MODULE_Y+self.usb_port_y_offset_mm, self.usb_center_above_pcb_mm+self.usb_port_z_offset_mm


def side_block(x0, x1, center_y, width, z0, z1):
    return prism(box(x0, center_y-width/2, x1, center_y+width/2), z0, z1-z0)


def usb_parts(p):
    """Drop-in T-section bezel; tray slots guide it and cover captures its ears."""
    outer = BOARD_W+p.margin
    cy = p.usb_bezel_center_y_mm
    body = side_block(outer-p.usb_bezel_depth_mm, outer, cy, p.usb_bezel_width_mm,
                      p.usb_bezel_bottom_mm, p.cover_top)
    flange = side_block(outer-p.usb_bezel_depth_mm-p.usb_bezel_flange_depth_mm,
                        outer-p.usb_bezel_depth_mm, cy, p.usb_bezel_flange_width_mm,
                        p.usb_bezel_flange_bottom_mm, p.cover_underside_above_pcb_mm)
    blank = body.fuse(flange).removeSplitter()
    port_y, port_z = p.port_center
    port = side_block(BOARD_W-3, outer+2, port_y, p.usb_opening_width_mm,
                      port_z-p.usb_opening_height_mm/2, port_z+p.usb_opening_height_mm/2)
    insert = blank.cut(port).removeSplitter()
    clearance = p.usb_bezel_clearance_mm
    window = side_block(BOARD_W-3, outer+2, cy, p.usb_bezel_width_mm+2*clearance,
                        p.usb_bezel_bottom_mm-clearance, p.cover_top+1)
    grooves = side_block(outer-p.usb_bezel_depth_mm-p.usb_bezel_flange_depth_mm-clearance,
                         outer-p.usb_bezel_depth_mm+clearance, cy,
                         p.usb_bezel_flange_width_mm+2*clearance,
                         p.usb_bezel_flange_bottom_mm, p.cover_underside_above_pcb_mm+.1)
    return dict(usb_bezel=insert, usb_blank=blank, usb_window=window,
                usb_grooves=grooves, usb_port=port)


def pcb_shape():
    drills = unary_union([Point(s['x'], s['y']).buffer(s['drill_mm']/2, quad_segs=64)
                          for s in mounting_specs()])
    return prism(box(0, 0, BOARD_W, BOARD_H).difference(drills), -1.6, 1.6)


def plate_shape(plan):
    app, part = freecad()
    plate = prism(plan, PLATE_BOTTOM, PLATE_TOP-PLATE_BOTTOM)
    for x, y in PCB_ATTACHMENTS:
        boss = cylinder(x, y, 0, PLATE_BOSS_DIAMETER, PLATE_BOTTOM)
        root = part.makeCone(PLATE_BOSS_DIAMETER/2, PLATE_BOSS_ROOT_DIAMETER/2, .6,
                             app.Vector(x, BOARD_H-y, PLATE_BOTTOM-.6))
        plate = plate.fuse(boss.fuse(root))
    pilots = [cylinder(x, y, -.1, 3, SHORT_INSERT_PILOT_DEPTH+.1) for x, y in PCB_ATTACHMENTS]
    return plate.cut(part.makeCompound(pilots)).removeSplitter()


def support_jig():
    """Bench-only cradle: two rails bear directly against socket plastic."""
    body = prism(box(0, 0, 55, 24), 0, 2)
    for y in (3.11, 20.89):
        body = body.fuse(prism(box(2.7, y-1, 52.3, y+1), 2, 3))
    return body.removeSplitter()


def build(p):
    p.validate()
    usb = usb_parts(p)
    shapes = service.build(p, mounts=BASE_POSTS, mount_top=PLATE_BOTTOM, usb_opening=usb['usb_window'])
    # Open-top grooves stop the flange at Z=-1; the cover captures it at Z=8.4.
    shapes['tray'] = shapes['tray'].cut(assembled(usb['usb_grooves'], p))
    # Extra clearance at plate level, with three dedicated left/rear datum tabs.
    # All PCB pass-through holes remain loose fits around the tall posts.
    relief = prism(box(-.75, -.75, BOARD_W+.75, PLATE_H+.75).difference(
        box(-p.pcb_edge_clearance_mm, -p.pcb_edge_clearance_mm,
            BOARD_W+p.pcb_edge_clearance_mm, PLATE_H+p.pcb_edge_clearance_mm)), 1, PLATE_BOTTOM-1)
    shapes['tray'] = shapes['tray'].cut(assembled(relief, p))
    datums = [box(-.9, 42, -.15, 50), box(-.9, 96, -.15, 104), box(90, -.9, 98, -.15)]
    for datum in datums:
        shapes['tray'] = shapes['tray'].fuse(assembled(prism(datum, 1.5, 2), p))
    shapes['tray'] = shapes['tray'].removeSplitter()
    plan, cuts, stabs = geometry(top_capacitor_opening=False)
    shapes.update(usb, plate=plate_shape(plan), pcb=pcb_shape(), socket_jig=support_jig())
    for name in ('tray', 'cover', 'plate', 'pcb', 'usb_bezel', 'usb_blank', 'socket_jig',
                 'logo_carrier', 'logo_insert', 'logo_gasket'):
        shape = shapes[name]
        assert shape.isValid() and len(shape.Solids) == 1 and shape.Volume > 0, name
    return shapes, plan, stabs


def hardware(p):
    _, part = freecad()
    plate_screws, pcb_screws, cover_screws, inserts, washers = [], [], [], [], []
    for x, y in BASE_POSTS:
        # M2x5 from above: 1.5 mm plate grip / 3.5 mm engagement.
        plate_screws.append(cylinder(x, y, 0, 2, 5).fuse(cylinder(x, y, 5, 3.8, 2)))
        inserts.append(cylinder(x, y, -.5, 3.2, 4).cut(cylinder(x, y, -.6, 2.1, 4.2)))
    for x, y in PCB_ATTACHMENTS:
        # M2x4 from underneath, with a 0.3 mm insulating washer: 2.1 mm engagement.
        pcb_screws.append(cylinder(x, y, -1.9, 2, 4).fuse(cylinder(x, y, -3.9, 3.8, 2)))
        washers.append(cylinder(x, y, -1.9, 5, .3).cut(cylinder(x, y, -2, 2.2, .5)))
        inserts.append(cylinder(x, y, 0, 3.2, SHORT_INSERT_LENGTH).cut(
            cylinder(x, y, -.1, 2.1, SHORT_INSERT_LENGTH+.2)))
    for x, y in service.cover_screws(p):
        cover_screws.append(cylinder(x, y, p.head_seat, 2, 8).fuse(
            cylinder(x, y, p.head_seat-2, 3.8, 2)))
        inserts.append(cylinder(x, y, p.boss_bottom, 3.2, 4).cut(cylinder(x, y, p.boss_bottom-.1, 2.1, 4.2)))
    return {name: part.makeCompound(values) for name, values in (
        ('plate_screws', plate_screws), ('pcb_screws', pcb_screws),
        ('cover_screws', cover_screws), ('inserts', inserts), ('washers', washers))}


def validate(p, shapes, plan):
    app, part = freecad()
    checks = validate_pcb(ROOT/'Cleaver.kicad_pcb', plan)
    tray = shapes['tray']
    obstacles = {name: assembled(shapes[name], p) for name in (
        'cover', 'plate', 'pcb', 'usb_bezel', 'logo_carrier', 'logo_insert', 'logo_gasket')}
    obstacles['tray'] = tray
    intersections = {}
    names = list(obstacles)
    for i, name in enumerate(names):
        for other in names[i+1:]:
            volume = obstacles[name].common(obstacles[other]).Volume
            assert volume < 1e-6, (name, other, volume)
            intersections[f'{name}/{other}'] = round(volume, 8)
    # Every fastener is checked in final assembled coordinates.
    screws = hardware(p)
    for name in ('plate_screws', 'pcb_screws', 'cover_screws', 'washers'):
        gauge = assembled(screws[name], p)
        for obstacle_name, obstacle in obstacles.items():
            assert gauge.common(obstacle).Volume < 1e-6, (name, obstacle_name)
    shapes.update(screws)
    for x, y in BASE_POSTS:
        support = cylinder(x, y, PLATE_BOTTOM-.1, 5.9, .05).cut(cylinder(x, y, PLATE_BOTTOM-.2, 3.1, .3))
        support = assembled(support, p)
        assert abs(tray.common(support).Volume-support.Volume) < 1e-6, 'Missing tall post shoulder'
        driver = cylinder(x, y, 7, 4.4, 30)
        for name in ('plate', 'pcb', 'usb_bezel'):
            assert driver.common(shapes[name]).Volume < 1e-6, ('plate screw access', name)
    for x, y in PCB_ATTACHMENTS:
        ring = cylinder(x, y, .05, 6.2, .05).cut(cylinder(x, y, -.1, 3.1, .3))
        assert abs(shapes['plate'].common(ring).Volume-ring.Volume) < 1e-6
        pilot = cylinder(x, y, -.01, 2.95, 2.8)
        assert shapes['plate'].common(pilot).Volume < 1e-6
        driver = cylinder(x, y, -35, 4.4, 31)
        for name in ('plate', 'pcb'):
            assert driver.common(shapes[name]).Volume < 1e-6, ('underside access', name)
    for x, y in service.cover_screws(p):
        assert tray.common(assembled(cylinder(x, y, -60, 4.4, 60+p.head_seat-.01), p)).Volume < 1e-6
        roof = cylinder(x, y, p.cover_top-.2, 4, .1)
        assert abs(shapes['cover'].common(roof).Volume-roof.Volume) < 1e-6
    # Assembly path: lift along the PCB normal, not the desk vertical.
    cartridge = part.makeCompound([shapes[n] for n in ('plate', 'pcb', 'pcb_screws', 'washers')])
    for lift in (.05, .5, 2, 5, 10, 25):
        moved = cartridge.copy()
        moved.translate(app.Vector(0, 0, lift))
        assert tray.common(assembled(moved, p)).Volume < 1e-6, ('cartridge insertion path', lift)
    # Insert is replaced with cover off; module/PCB can remain installed.
    for lift in (.05, .5, 2, 5, 12, 25):
        moved = shapes['usb_bezel'].copy()
        moved.translate(app.Vector(0, 0, lift))
        assert tray.common(assembled(moved, p)).Volume < 1e-6, ('bezel drop-in path', lift)
    # Prove capture after closing: ears stop upward travel; T flange prevents
    # outward withdrawal; side rails/outer wall prevent inward displacement.
    for axis, distance in [((0, 0, 1), .5), ((1, 0, 0), 1), ((-1, 0, 0), 1)]:
        moved = shapes['usb_bezel'].copy()
        moved.translate(app.Vector(*[v*distance for v in axis]))
        assert sum(obstacle.common(assembled(moved, p)).Volume for obstacle in (
            tray, obstacles['cover'])) > .1, 'USB bezel not positively captured'
    module = prism(box(MODULE_X-25.5, MODULE_Y-10.5, MODULE_X+25.5, MODULE_Y+10.5), 0, 8.2)
    shell = prism(box(MODULE_X+19, MODULE_Y-4.475, MODULE_X+27.5, MODULE_Y+4.475), 4.14, 3.2)
    controller = module.fuse(shell)
    for label in ('cover', 'plate', 'usb_bezel'):
        assert shapes[label].common(controller).Volume < 1e-6, label
    assert tray.common(assembled(controller, p)).Volume < 1e-6
    for ref, y, _ in CONTROLLER_SOCKETS:
        socket = prism(box(MODULE_X-25.65, y-2.125, MODULE_X+25.65, y+2.125), -9.6, 8)
        assert tray.common(assembled(socket, p)).Volume < 1e-6, ref
    c5 = prism(box(371, .5, 383, 11.5), -12.6, 11)
    assert tray.common(assembled(c5, p)).Volume < 1e-6
    assert shapes['usb_bezel'].common(shapes['usb_port']).Volume < 1e-6
    assert tray.common(assembled(shapes['usb_port'], p)).Volume < 1e-6
    assert shapes['cover'].common(shapes['usb_port']).Volume < 1e-6
    for key in read_keys()[0]:
        swept = box(key['x']-(key['w']*19.05-1)/2, key['y']-(key['h']*19.05-1)/2,
                    key['x']+(key['w']*19.05-1)/2, key['y']+(key['h']*19.05-1)/2)
        assert shapes['cover'].common(prism(swept, 0, 30)).Volume < 1e-6, key['ref']
        assert shapes['plate_screws'].common(prism(swept, 5, 25)).Volume < 1e-6, key['ref']
        # Lower switch/socket envelopes exclude the drilled post openings by
        # selecting actual 14 x 14 switch footprints.
        switch = prism(box(key['x']-7, key['y']-7, key['x']+7, key['y']+7), -5.6, 4)
        assert tray.common(assembled(switch, p)).Volume < 1e-6, key['ref']
    for led in logo_leds():
        beam = prism(box(led['x']-1.8, led['y']-1.6, led['x']+1.8, led['y']+1.6), .4, p.cover_top-1.4)
        for name in ('plate', 'cover', 'logo_carrier', 'logo_insert', 'logo_gasket'):
            assert shapes[name].common(beam).Volume < 1e-6, (led['led_ref'], name)
    return dict(source_checks=checks, intersection_volumes_mm3=intersections,
                base_posts=12, pcb_to_plate_bosses=12, pass_through_radial_clearance_mm=.5,
                pcb_to_plate_gap_mm=3.5, plate_screw_engagement_mm=3.5,
                pcb_screw_engagement_with_washer_mm=2.1,
                short_insert_tip_clearance_mm=.7,
                cartridge_insertion_axis='PCB normal', cartridge_lift_checks_mm=[.05, .5, 2, 5, 10, 25],
                usb_insert_replacement_with_pcb_installed=True, usb_insert_positive_capture=True,
                usb_port_center_pcb_yz_mm=list(p.port_center), usb_port_size_mm=[p.usb_opening_width_mm, p.usb_opening_height_mm],
                controller_and_socket_envelopes_clear=True, c5_11mm_keepout_clear=True,
                keycap_sweeps_clear=117, plate_screw_heads_clear_of_key_sweeps=True,
                four_logo_optical_paths_clear=True, height_comparison=service.height_comparison(p))


def save_assembly(out, p, shapes):
    app, part = freecad()
    doc = app.newDocument('CleaverCartridgeRev011')
    objects = []
    names = [
        ('tray', 'PRINT: base / 12 pass-through plate-support posts', (.16, .20, .25), False),
        ('cover', 'PRINT: removable outer cover / underside screws', (.75, .78, .81), True),
        ('plate', 'PRINT: switch plate / 12 downward PCB bosses', (.58, .6, .63), True),
        ('pcb', 'REFERENCE: rev0.11 PCB / two hole families', (.07, .40, .22), True),
        ('usb_bezel', 'PRINT: replaceable USB bezel / nominal opening', (.25, .3, .34), True),
        ('logo_carrier', 'PRINT OPAQUE: plate-supported logo well', (.08, .08, .08), True),
        ('logo_insert', 'PRINT TRANSLUCENT: removable badge', (.25, .75, .95), True),
        ('logo_gasket', 'CUT FOAM: badge gasket, compressed', (.35, .35, .35), True),
        ('plate_screws', 'HARDWARE: 12 M2x5 plate-to-base screws', (.6, .6, .62), True),
        ('pcb_screws', 'HARDWARE: 12 M2x4 PCB-to-plate screws', (.6, .6, .62), True),
        ('washers', 'HARDWARE: 12 insulating washers OD5 x 0.3', (.7, .7, .7), True),
        ('cover_screws', 'HARDWARE: 8 M2x8 underside cover screws', (.6, .6, .62), True),
        ('inserts', 'HARDWARE: heat-set inserts (nominal interference fit)', (.65, .48, .2), True),
    ]
    for name, label, color, tilt in names:
        obj = doc.addObject('PartDesign::Feature', name)
        obj.Label = label
        obj.Shape = assembled(shapes[name], p) if tilt else shapes[name]
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = color
        objects.append(obj)
    objects[0].addProperty('App::PropertyString', 'Regeneration').Regeneration = 'source/generate_cartridge_case.py --parameters parameters.json'
    doc.recompute()
    with tempfile.TemporaryDirectory(prefix='.assembly-', dir=out) as directory:
        path = Path(directory)/f'Cleaver-case-assembly-rev{REVISION}.FCStd'
        doc.saveAs(str(path))
        path.replace(out/path.name)
    part.export(objects, str(out/f'Cleaver-case-assembly-rev{REVISION}.step'))
    app.closeDocument(doc.Name)


def export_coupons(out, p, shapes):
    records = []
    # This actual slice contains H2 pass-through and H14 underside attachment.
    crop = box(68, 15, 119, 30)
    for label, name in [('base', 'tray'), ('plate', 'plate'), ('dummy-PCB', 'pcb')]:
        tool = prism(crop, -60, 100)
        if name == 'tray':
            tool = assembled(tool, p)
        shape = shapes[name].common(tool).removeSplitter()
        records.append(export_part(out, 'Cartridge-stack-coupon-'+label, shape, face_down=name=='plate'))
    crop = box(BOARD_W-65, -p.end_margin-1, BOARD_W+p.margin+1, 40)
    for label, name in [('base', 'tray'), ('cover', 'cover')]:
        tool = prism(crop, -60, 100)
        if name == 'tray':
            tool = assembled(tool, p)
        records.append(export_part(out, 'USB-bezel-fit-coupon-'+label,
                                   shapes[name].common(tool).removeSplitter(), face_down=name=='cover'))
    # Generate cover-fastener and complete badge fixtures from this revision.
    section = box(130, PLATE_H-5, 160, PLATE_H+p.end_margin+1)
    for label, name in [('base', 'tray'), ('cover', 'cover')]:
        tool = prism(section, -60, 100)
        if name == 'tray':
            tool = assembled(tool, p)
        records.append(export_part(out, 'Front-fastener-fit-coupon-'+label,
                                   shapes[name].common(tool).removeSplitter(), face_down=name=='cover'))
    section = box(LOGO_X-FLANGE[0]/2-4, LOGO_Y-APERTURE[1]/2-1,
                  LOGO_X+FLANGE[0]/2+4, PLATE_H+p.end_margin+1)
    records.append(export_part(out, 'Logo-fit-coupon-cover',
                               shapes['cover'].common(prism(section, -20, 60)).removeSplitter(), face_down=True))
    badge_plate = shapes['plate'].common(prism(section, -20, 60))
    for sign in (-1, 1):
        x = LOGO_X+sign*(FLANGE[0]/2+2.7)
        badge_plate = badge_plate.fuse(prism(box(x-.5, LOGO_Y-8, x+.5, LOGO_Y+8), 5, 3.4))
    records.append(export_part(out, 'Logo-fit-coupon-plate-with-height-gauges', badge_plate.removeSplitter()))
    return records


def write_drawings(out, p, shapes, plan):
    from html import escape
    _, _, _, deck = service.outlines(p)
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="530" viewBox="-16 -28 490 215">',
             '<rect x="-16" y="-28" width="490" height="215" fill="#f5f7fa"/>',
             '<g font-family="sans-serif" fill="#243244">',
             '<text x="0" y="-16" font-size="7">Cleaver rev0.11 / removable PCB + switch-plate cartridge</text>',
             f'<path d="{svg_path(plan)}" fill="#d6dde4" stroke="#34465a" stroke-width=".25" fill-rule="evenodd"/>']
    for spec in mounting_specs():
        x, y = spec['x'], spec['y']
        color = '#247d91' if spec['role']=='base_post_pass_through' else '#b26335'
        radius = spec['drill_mm']/2
        lines += [f'<circle cx="{x}" cy="{y}" r="{radius}" fill="none" stroke="{color}" stroke-width=".5"/>',
                  f'<text x="{x+4}" y="{y+1}" font-size="2.8" fill="{color}">{spec["reference"]}</text>']
    lines += ['<text x="0" y="170" font-size="4" fill="#247d91">H1–H12: PCB diameter 7 / base posts diameter 6 / plate screws from above</text>',
              '<text x="0" y="179" font-size="4" fill="#b26335">H13–H24: PCB diameter 2.2 / screws from below into short plate inserts</text>', '</g></svg>']
    (out/'mounting-plan.svg').write_text('\n'.join(lines)+'\n')
    (out/'assembly-sections.svg').write_text('''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="650" viewBox="0 0 240 130">
<rect width="240" height="130" fill="#f5f7fa"/>
<g font-family="sans-serif" fill="#243244" font-size="3.4">
<text x="8" y="9" font-size="5">rev0.11 cartridge sections / schematic, dimensions normal to PCB</text>
<text x="8" y="20" font-size="4">1. PCB screws upward into plate bosses</text>
<rect x="12" y="28" width="65" height="6" fill="#aebac6"/>
<rect x="32" y="34" width="25" height="14" fill="#aebac6"/>
<rect x="39" y="38" width="11" height="10" fill="#aa8247"/>
<rect x="12" y="48" width="65" height="6" fill="#59976b"/>
<path d="M42 40h5v16h5v7H37v-7h5Z" fill="#56616c"/>
<text x="85" y="32">Switch plate Z=3.5–5.0, thickness 1.5</text>
<text x="85" y="40">Integral boss Z=0–3.5 / short M2 insert length 2.5</text>
<text x="85" y="48">PCB top Z=0 / underside -1.6 / hole diameter 2.2</text>
<text x="85" y="56">M2 x 4 + 0.3 washer / engagement 2.1</text>
<text x="8" y="77" font-size="4">2. Cartridge drops over base posts; plate screws down</text>
<rect x="12" y="84" width="65" height="6" fill="#aebac6"/>
<path d="M12 105h18v6H12Z M59 105h18v6H59Z" fill="#59976b"/>
<rect x="33" y="90" width="23" height="30" fill="#d8c29c"/>
<rect x="39" y="90" width="11" height="16" fill="#aa8247"/>
<path d="M37 78h15v6h-5v20h-5V84h-5Z" fill="#56616c"/>
<text x="85" y="88">M2 x 5 through plate diameter 2.8 / engagement 3.5</text>
<text x="85" y="97">Post top Z=3.5 bears directly on plate</text>
<text x="85" y="106">Base post diameter 6 passes through PCB diameter 7</text>
<text x="85" y="115">PCB is not clamped by this screw / 0.5 radial clearance</text>
</g></svg>
''')
    cy, cz = p.port_center
    (out/'final-prints/USB-bezel-template.scad').write_text(f'''// Millimetres. Printed outer face down; assembled PCB +Y is toward the user.
// Positive dy moves the opening toward the keyboard front; positive dz raises it.
// Set blank=true to print a closed measuring/drilling blank.
dy={p.usb_port_y_offset_mm}; dz={p.usb_port_z_offset_mm}; opening_w={p.usb_opening_width_mm}; opening_h={p.usb_opening_height_mm}; blank=false;
outer_w={p.usb_bezel_width_mm}; flange_w={p.usb_bezel_flange_width_mm};
outer_bottom={p.usb_bezel_bottom_mm}; outer_top={p.cover_top};
center_y={p.usb_bezel_center_y_mm}; nominal_y={MODULE_Y}; nominal_z={p.usb_center_above_pcb_mm};
assert(nominal_y+dy-opening_w/2 >= center_y-outer_w/2+1);
assert(nominal_y+dy+opening_w/2 <= center_y+outer_w/2-1);
assert(nominal_z+dz-opening_h/2 >= outer_bottom+1);
assert(nominal_z+dz+opening_h/2 <= outer_top-1);
difference() {{
  union() {{
    translate([(flange_w-outer_w)/2,0,0]) cube([outer_w,outer_top-outer_bottom,{p.usb_bezel_depth_mm}]);
    translate([0,{p.usb_bezel_flange_bottom_mm-p.usb_bezel_bottom_mm},{p.usb_bezel_depth_mm}])
      cube([flange_w,{p.cover_underside_above_pcb_mm-p.usb_bezel_flange_bottom_mm},{p.usb_bezel_flange_depth_mm}]);
  }}
  if(!blank) translate([flange_w/2+nominal_y-center_y+dy-opening_w/2,nominal_z+dz-outer_bottom-opening_h/2,-1])
    cube([opening_w,opening_h,10]);
}}
''')
    (out/'USB-measurement.json').write_text(json.dumps(dict(
        coordinates='PCB top-view Y toward user, Z normal to PCB; measure opening center after assembly',
        nominal_center_yz_mm=[MODULE_Y, p.usb_center_above_pcb_mm],
        selected_center_yz_mm=[cy, cz], opening_mm=[p.usb_opening_width_mm, p.usb_opening_height_mm],
        offset_formula='offset = measured center - nominal center',
        minimum_edge_web_mm=1, minimum_capture_ear_overlap_mm=1.75,
        physical_measurement_complete=False), indent=2)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parameters', type=Path, default=OUT/'parameters.json')
    parser.add_argument('--output', type=Path, default=OUT)
    parser.add_argument('--usb-only', action='store_true')
    parser.add_argument('--usb-y-offset', type=float)
    parser.add_argument('--usb-z-offset', type=float)
    parser.add_argument('--usb-width', type=float)
    parser.add_argument('--usb-height', type=float)
    args = parser.parse_args()
    p = Parameters(**json.loads(args.parameters.read_text())) if args.parameters.is_file() else Parameters()
    overrides = {field: value for field, value in (
        ('usb_port_y_offset_mm', args.usb_y_offset), ('usb_port_z_offset_mm', args.usb_z_offset),
        ('usb_opening_width_mm', args.usb_width), ('usb_opening_height_mm', args.usb_height)) if value is not None}
    p = replace(p, **overrides)
    p.validate()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)
    if args.usb_only:
        pieces = usb_parts(p)
        record = export_part(out, 'USB-bezel-fitted', pieces['usb_bezel'], print_rotation=[0, 1, 0, 90])
        (out/'USB-bezel-fitted.json').write_text(json.dumps(dict(parameters=asdict(p), part=record), indent=2)+'\n')
        print(f'Exported fitted USB bezel: center {p.port_center}, opening {p.usb_opening_width_mm} x {p.usb_opening_height_mm} mm')
        return
    pcb = ROOT/'Cleaver.kicad_pcb'
    before = digest(pcb)
    print('Build rev0.11 cartridge case / 24 mounting locations / removable USB bezel', flush=True)
    shapes, plan, stabs = build(p)
    fit = validate(p, shapes, plan)
    print('Assembly, insertion paths, screws, USB capture and electrical envelopes clear', flush=True)
    (out/'parameters.json').write_text(json.dumps(asdict(p), indent=2)+'\n')
    parts = []
    for filename, name, face_down in [
        (f'Cleaver-case-base-rev{REVISION}', 'tray', False),
        (f'Cleaver-case-top-cover-rev{REVISION}', 'cover', True),
        (f'Cleaver-switch-plate-rev{REVISION}', 'plate', True),
        ('Logo-light-well', 'logo_carrier', True), ('Logo-insert-blank', 'logo_insert', True),
        ('Controller-insertion-support-jig', 'socket_jig', False),
    ]:
        parts.append(export_part(out, filename, shapes[name], face_down=face_down))
    for filename, name in [('USB-bezel-nominal', 'usb_bezel'), ('USB-bezel-blank', 'usb_blank')]:
        parts.append(export_part(out, filename, shapes[name], print_rotation=[0, 1, 0, 90]))
    parts.append(export_part(out, 'Logo-gasket-cutting-pattern-0.8mm',
                             prism(service.gasket_plan(), 0, p.gasket_stock_mm)))
    parts.extend(export_coupons(out, p, shapes))
    for thickness in (.2, .4, .6, .8, 1):
        parts.append(export_part(out, f'controller-socket-shim-{thickness:.1f}mm', prism(box(0, 0, 49.6, 2), 0, thickness)))
    # Preserve the clip-validation coupons, including the 6.25u spacebar.
    for size, label in [(2, '2u'), (6.25, '6.25u')]:
        parts.append(export_part(out, 'Stabilizer-fit-coupon-'+label, prism(fit_coupon(size), 0, 1.5)))
    common.write_badge_template(out/'final-prints', p)
    (out/'final-prints/Logo-gasket-cut-template.svg').write_text((ROOT/'mechanical/rev0.10/case/Logo-gasket-cut-template.svg').read_text())
    save_assembly(out, p, shapes)
    write_drawings(out, p, shapes, plan)
    export_svg(out/'Switch-plate-plan-reference.svg', plan, BOARD_W, PLATE_H)
    export_dxf(out/'Switch-plate-plan-reference.dxf', plan)
    assert digest(pcb) == before
    source_paths = [Path(__file__), ROOT/'source/coupon_labels.py', ROOT/'source/mounting_interface.py', ROOT/'source/generate_case.py',
                    ROOT/'source/generate_case_service.py', ROOT/'source/generate_mechanical.py',
                    ROOT/'source/generate_top_plate.py', ROOT/'source/design.py']
    report = dict(revision=REVISION, source_pcb='../../../Cleaver.kicad_pcb', source_sha256=before,
                  parameters=asdict(p), mounting_sites=mounting_specs(), fit_checks=fit, stabilizers=stabs,
                  hardware=dict(plate_to_base='12 x M2x5 socket head', pcb_to_plate='12 x M2x4 socket head',
                                cover='8 x M2x8 socket head', washers='12 x insulating OD5 / ID2.2 / thickness 0.3',
                                long_inserts='20 x M2 OD3.2 x 4 (12 base + 8 cover)',
                                short_inserts='12 x M2 OD3.2 x 2.5 (plate bosses)',
                                loose_pcb_plate_spacers=0),
                  source_files={str(path.relative_to(ROOT)): digest(path) for path in source_paths},
                  physical_fit_tested=False,
                  coordinates='PCB top Z=0, plate 3.5..5; STEP base desk-flat, other parts PCB-frame; assembly all desk-flat; STL bed-oriented per record',
                  tools=dict(freecad='.'.join(freecad()[0].Version()[:3]), kicad=pcbnew.Version(), trimesh=trimesh.__version__),
                  parts=parts,
                  assembly_sha256={path.name: digest(path) for path in (
                      out/f'Cleaver-case-assembly-rev{REVISION}.FCStd', out/f'Cleaver-case-assembly-rev{REVISION}.step')})
    (out/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(f'{len(parts)} STL/STEP pairs: watertight, single solids, CAD round trips passed.')


if __name__ == '__main__':
    main()
