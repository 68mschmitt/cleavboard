#!/usr/bin/env python3
"""Render the complete rev0.6 hardware assembly using Blender/Cycles.

Run with Blender's Python, not KiCad's Python. See case/renderings/README.md
for the read-only KiCad GLB export and the reproducible render command.
All CAD dimensions are retained; cap profiles/finishes and hardware are visual
approximations, not new fabrication models. No electrical/CAD inputs are edited.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from design import BOARD_H, BOARD_W, INPUT, MOUNTING_HOLES, ROOT, U, read_keys

CASE = ROOT/'mechanical/rev0.6/case'
MM = .001


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def color(hex_color):
    values = [int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4)]
    return tuple(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in values)


def material(name, hex_color, roughness=.5, metallic=0, texture=False):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color(hex_color), 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = mat.diffuse_color
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    if texture:
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        noise = nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 1800
        noise.inputs['Detail'].default_value = 2
        bump = nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .12
        bump.inputs['Distance'].default_value = .000035
        links.new(noise.outputs['Fac'], bump.inputs['Height'])
        links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def collection(name):
    item = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(item)
    return item


def move_to(obj, target):
    for coll in list(obj.users_collection):
        coll.objects.unlink(obj)
    target.objects.link(obj)


def empty(name, target, parent=None):
    obj = bpy.data.objects.new(name, None)
    target.objects.link(obj)
    obj.parent = parent
    return obj


def mesh_object(name, vertices_mm, faces, mat, target, parent=None):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([tuple(v*MM for v in point) for point in vertices_mm], [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.parent = parent
    if mat is not None:
        mesh.materials.append(mat)
    return obj


def tube(name, x, y, bottom, height, radius, inner_radius, mat, target, parent, n=48):
    verts = []
    for z, r in [(bottom, radius), (bottom+height, radius),
                 (bottom+height, inner_radius), (bottom, inner_radius)]:
        verts.extend([(x+r*math.cos(i*math.tau/n), y+r*math.sin(i*math.tau/n), z) for i in range(n)])
    faces = []
    for j in range(4):
        for i in range(n):
            faces.append((j*n+i, j*n+(i+1)%n, ((j+1)%4)*n+(i+1)%n, ((j+1)%4)*n+i))
    return mesh_object(name, verts, faces, mat, target, parent)


def box_object(name, center, size, mat, target, parent, bevel=.0):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = Vector(size)*MM
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.location = Vector(center)*MM
    obj.parent = parent
    obj.data.materials.append(mat)
    move_to(obj, target)
    if bevel:
        mod = obj.modifiers.new('Soft manufactured edges', 'BEVEL')
        mod.width, mod.segments = bevel*MM, 3
    return obj


def import_print_part(filename, report, target, parent, mat):
    item = next(item for item in report['parts'] if item['file'] == filename)
    path = CASE/filename
    assert sha(path) == item['sha256'], f'Stale case validation: {filename}'
    bpy.ops.wm.stl_import(filepath=str(path), forward_axis='Y', up_axis='Z')
    obj = bpy.context.object
    obj.name = filename.removesuffix('.stl')
    # Undo independent print-bed shifts and cover face-down orientation BEFORE
    # applying the same assembly transform as the PCB and switch plate.
    shift = Vector(item['stl_translation_after_optional_x_flip_mm'])
    shift += Vector(item['stl_additional_mesh_translation_mm'])
    flip = Matrix.Rotation(math.pi, 3, 'X') if item['stl_face_down'] else Matrix.Identity(3)
    for vertex in obj.data.vertices:
        vertex.co = (flip@(vertex.co-shift))*MM
    obj.parent = parent
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    move_to(obj, target)
    return obj


def import_pcb(path, target, stack):
    existing = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path), loglevel=40)
    added = set(bpy.data.objects)-existing
    bpy.context.view_layer.update()
    meshes = [obj for obj in added if obj.type == 'MESH']
    # KiCad exports in metres: X right, Y negative towards the user, nominal PCB
    # bottom at Z=0 and component mounting plane at Z=+1.6 mm.
    board = [obj for obj in meshes if obj.dimensions.x > BOARD_W*MM-1e-5
             and obj.dimensions.y > BOARD_H*MM-1e-5
             and .0014 < obj.dimensions.z < .0016]
    assert len(board) == 1, 'Unexpected GLB coordinate system / PCB body'
    bounds = [board[0].matrix_world@Vector(corner) for corner in board[0].bound_box]
    assert abs(min(p.x for p in bounds)) < 1e-6
    assert abs(min(p.y for p in bounds)+BOARD_H*MM) < 1e-6
    assert abs(max(p.y for p in bounds)) < 1e-6
    assert abs(max(p.x for p in bounds)-BOARD_W*MM) < 1e-6
    anchor = empty('KiCad PCB coordinates → PCB-top assembly datum', target, stack)
    anchor.location = (0, BOARD_H*MM, -1.6*MM)
    roots = [obj for obj in added if obj.parent not in added]
    for obj in roots:
        world = obj.matrix_world.copy()
        obj.parent = anchor
        obj.matrix_local = world
    for obj in added:
        move_to(obj, target)
    # The saved rev0.6 board has 597 component-model instances + 6 PCB meshes.
    assert len(meshes) == 603, f'Missing PCB/component models: {len(meshes)} meshes'
    switch_assemblies = [obj for obj in added if obj.name.startswith('SW') and obj.type == 'EMPTY']
    return dict(meshes=len(meshes), model_instances=597, populated_footprints=480,
                switch_models=117, switch_socket_models=117,
                source_glb_sha256=sha(path), switch_assembly_nodes=len(switch_assemblies))


def rounded_ring(w, h, radius, count=8):
    points = []
    for cx, cy, start in [(w/2-radius, h/2-radius, 0), (-w/2+radius, h/2-radius, 90),
                           (-w/2+radius, -h/2+radius, 180), (w/2-radius, -h/2+radius, 270)]:
        for i in range(count):
            theta = math.radians(start+i*90/count)
            points.append((cx+radius*math.cos(theta), cy+radius*math.sin(theta)))
    return points


def keycap_mesh(width, height, top):
    """Generic sculpted MX cap, hollow skirt and lightly dished rounded top."""
    w, h = width*U-1, height*U-1
    upper_w, upper_h = w-2.8, h-2.8
    rings = []
    for rw, rh, rad, z in [(w, h, 1.0, 9.4), (w, h, 1.1, 10.1),
                            (upper_w+.4, upper_h+.4, 1.2, top-.55),
                            (upper_w, upper_h, 1.15, top)]:
        rings.append([(x, y, z) for x, y in rounded_ring(rw, rh, rad)])
    for amount in [.78, .53, .28, .08]:
        rings.append([(x*amount, y*amount, top-.7*(1-amount*amount))
                      for x, y in rounded_ring(upper_w, upper_h, 1.15)])
    n = len(rings[0])
    verts = [v for ring in rings for v in ring]
    faces = []
    for j in range(len(rings)-1):
        for i in range(n):
            faces.append((j*n+i, j*n+(i+1)%n, (j+1)*n+(i+1)%n, (j+1)*n+i))
    faces.append(tuple(range((len(rings)-1)*n, len(rings)*n)))
    # Inside skirt is intentionally open; a recessed ceiling closes its top.
    start = len(verts)
    verts += [(x, y, 9.4) for x, y in rounded_ring(w-2, h-2, .5)]
    verts += [(x, y, top-1.3) for x, y in rounded_ring(upper_w-1, upper_h-1, .5)]
    for i in range(n):
        nxt = (i+1)%n
        faces.append((i, start+i, start+nxt, nxt))
        faces.append((start+i, start+n+i, start+n+nxt, start+nxt))
    faces.append(tuple(reversed(range(start+n, start+2*n))))
    return verts, faces


def original_legends():
    result = []
    for row in json.loads((INPUT/'keyboard-layout.json').read_text()):
        options = {}
        for item in row:
            if isinstance(item, dict):
                options.update(item)
            else:
                if not options.get('d', False):
                    result.append(item)
                options = {}
    assert len(result) == 117
    return result


def add_caps(target, stack, mats):
    keys, _ = read_keys()
    font_path = Path('/usr/share/fonts/TTF/DejaVuSans.ttf')
    font = bpy.data.fonts.load(str(font_path)) if font_path.is_file() else None
    cache, labels = {}, []
    for key, legend in zip(keys, original_legends()):
        top = [21.6, 20.6, 19.6, 19.0, 19.6, 20.6, 20.6][key['kle_row']]
        red = key['legend'] == 'Esc' or key['kle_row'] == 6
        macro = key['legend'].startswith('M') and key['legend'][1:].isdigit()
        grey = (macro or max(key['w'], key['h']) > 1 or key['kle_row'] == 0
                or key['legend'] in ['Insert', 'Home', 'PgUp', 'Delete', 'End', 'PgDn',
                                     'Num Lock', '↑', '←', '↓', '→']) and not red
        cap_mat = mats['red'] if red else mats['grey'] if grey else mats['ivory']
        lookup = (key['w'], key['h'], top, cap_mat.name)
        if lookup not in cache:
            verts, faces = keycap_mesh(key['w'], key['h'], top)
            obj = mesh_object('Keycap '+key['ref'], verts, faces, cap_mat, target, stack)
            for polygon in obj.data.polygons:
                polygon.use_smooth = True
            cache[lookup] = obj.data
        else:
            obj = bpy.data.objects.new('Keycap '+key['ref'], cache[lookup])
            target.objects.link(obj)
            obj.parent = stack
        obj.location = (key['x']*MM, (BOARD_H-key['y'])*MM, 0)
        obj['switch_reference'], obj['legend'] = key['ref'], key['legend']
        if not legend:
            continue
        text = bpy.data.curves.new('Legend '+key['ref'], 'FONT')
        text.body = legend
        text.align_x, text.align_y = 'CENTER', 'CENTER'
        text.space_line = .9
        longest = max(len(line) for line in text.body.splitlines())
        text.size = (6.2 if longest <= 2 else 4.6 if longest <= 5 else 3.3)*MM
        text.extrude = .006*MM
        text.resolution_u = 8
        if font is not None:
            text.font = font
        label = bpy.data.objects.new('Legend '+key['ref'], text)
        target.objects.link(label)
        label.parent = stack
        label.location = (key['x']*MM, (BOARD_H-key['y'])*MM, 0)
        text.materials.append(mats['white_ink'] if red else mats['ink'])
        labels.append((label.name, obj.data))
    # Conform every glyph vertex to its actual dished key surface. Flat floating
    # text otherwise gets buried at the outer edges of long legends.
    bpy.ops.object.select_all(action='DESELECT')
    for name, _ in labels:
        bpy.data.objects[name].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[labels[0][0]]
    bpy.ops.object.convert(target='MESH')
    trees = {}
    for name, cap_mesh in labels:
        if cap_mesh.name not in trees:
            trees[cap_mesh.name] = BVHTree.FromPolygons(
                [vertex.co for vertex in cap_mesh.vertices],
                [list(poly.vertices) for poly in cap_mesh.polygons])
        tree = trees[cap_mesh.name]
        glyph = bpy.data.objects[name]
        for vertex in glyph.data.vertices:
            hit, _, _, _ = tree.ray_cast(Vector((vertex.co.x, vertex.co.y, .04)), Vector((0, 0, -1)))
            assert hit is not None, f'Legend extends beyond cap: {name}'
            vertex.co.z += hit.z+.02*MM
        glyph.data.update()
    return dict(keycaps=117, legends=len(labels), profile='Generic rounded/dished sculpted MX, not a purchased keycap specification')


def add_hardware(report, target, stack, mats):
    # All support and fastener positions come from the case/PCB mounting table.
    for i, (x, pcb_y) in enumerate(MOUNTING_HOLES, 1):
        y = BOARD_H-pcb_y
        tube(f'H{i} brass M2 insert', x, y, -5.6, 4, 1.6, 1.0, mats['brass'], target, stack)
        tube(f'H{i} 3.5 mm spacer', x, y, 0, 3.5, 3, 1.1, mats['case'], target, stack)
        tube(f'H{i} M2x10 screw shaft', x, y, -5, 10, 1, .0, mats['steel'], target, stack)
        tube(f'H{i} M2 screw head', x, y, 5, 1.2, 1.9, .65, mats['steel'], target, stack)
        tube(f'H{i} dark hex socket', x, y, 5.05, .2, .65, 0, mats['ink'], target, stack, n=6)
    ztop = report['stack_mm']['cover_underside']
    for i, (x, pcb_y) in enumerate(report['cover_screws_pcb_xy_mm'], 1):
        y = BOARD_H-pcb_y
        tube(f'Cover insert {i}', x, y, ztop-4, 4, 1.6, 1, mats['brass'], target, stack)
        tube(f'Cover M2x6 shaft {i}', x, y, 3.8, 6, 1, 0, mats['steel'], target, stack)
        tube(f'Cover M2 head {i}', x, y, 9.8, 1.3, 1.9, .65, mats['steel'], target, stack)
        tube(f'Cover hex socket {i}', x, y, 9.85, .2, .65, 0, mats['ink'], target, stack, n=6)
    stabs = json.loads((CASE.parent/'validation.json').read_text())['stabilizers']
    for stab in stabs:
        holder = empty('Stabilizer '+stab['ref'], target, stack)
        holder.location = (stab['x_mm']*MM, (BOARD_H-stab['y_mm'])*MM, 0)
        holder.rotation_euler.z = math.radians(-stab['rotation_deg'])
        half = stab['stem_spacing_mm']/2
        for sign in (-1, 1):
            box_object('Plate-mount stabilizer housing', (sign*half, 0, 4), (6.5, 10.8, 5),
                       mats['stab'], target, holder, bevel=.4)
            box_object('Stabilizer stem', (sign*half, 0, 9.1), (3.5, 3.5, 5.2),
                       mats['grey'], target, holder, bevel=.2)
        wire = bpy.data.curves.new('Stabilizer steel wire', 'CURVE')
        wire.dimensions, wire.bevel_depth, wire.bevel_resolution = '3D', .6*MM, 3
        spline = wire.splines.new('POLY')
        points = [(-half, 0, 3), (-half, -5.5, 2.3), (half, -5.5, 2.3), (half, 0, 3)]
        spline.points.add(len(points)-1)
        for point, pos in zip(spline.points, points):
            point.co = (*[v*MM for v in pos], 1)
        wire.materials.append(mats['steel'])
        obj = bpy.data.objects.new('Stabilizer wire '+stab['ref'], wire)
        target.objects.link(obj)
        obj.parent = holder
    return dict(pcb_to_plate_spacers=11, pcb_screws=11, cover_screws=8,
                heat_set_inserts=19, plate_mount_stabilizers=8)


def aim(obj, point):
    obj.rotation_euler = (Vector(point)-obj.location).to_track_quat('-Z', 'Y').to_euler()


def studio(target):
    floor = material('Warm neutral studio surface', 'dddcd7', roughness=.75)
    box_object('Studio floor', (0, 0, -1.0), (2500, 2500, 2), floor, target, None)
    for name, position, power, size, tint in [
        ('Large softbox', (-.25, -.3, .6), 85, .6, (1, .94, .86)),
        ('Right fill', (.45, -.15, .35), 45, .5, (.86, .92, 1)),
        ('Rear rim', (-.1, .4, .5), 110, .5, (1, 1, 1))]:
        light = bpy.data.lights.new(name, 'AREA')
        light.energy, light.shape, light.size, light.color = power, 'DISK', size, tint
        obj = bpy.data.objects.new(name, light)
        target.objects.link(obj)
        obj.location = position
        aim(obj, (0, 0, .02))
    camera = bpy.data.cameras.new('Assembled product camera')
    camera.type, camera.ortho_scale, camera.clip_start, camera.clip_end = 'ORTHO', .59, .01, 10
    obj = bpy.data.objects.new('Assembled product camera', camera)
    target.objects.link(obj)
    obj.location = (.32, -.7, .68)
    aim(obj, (0, 0, .018))
    bpy.context.scene.camera = obj
    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs['Color'].default_value = (.65, .69, .76, 1)
    world.node_tree.nodes['Background'].inputs['Strength'].default_value = .35


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pcb', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=CASE/'renderings')
    parser.add_argument('--draft', action='store_true')
    parser.add_argument('--save-scene', type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    report = json.loads((CASE/'validation.json').read_text())
    p = report['parameters']
    assert sha(ROOT/'Cleaver.kicad_pcb') == report['source_sha256'], 'Case references a stale PCB'
    inputs = [ROOT/'Cleaver.kicad_pcb', CASE/'parameters.json', CASE/'validation.json',
              CASE.parent/'Cleaver-top-plate-rev0.6.stl']
    input_hashes = {str(path.relative_to(ROOT)): sha(path) for path in inputs}
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    enclosure, electronics = collection('01 — exact printed enclosure'), collection('02 — actual populated rev0.6 PCB')
    cap_collection, hardware = collection('03 — 117 visual keycaps and legends'), collection('04 — assembly hardware')
    environment = collection('05 — studio and camera')
    center = empty('Assembly desk datum', enclosure)
    center.location = (-BOARD_W*MM/2, -BOARD_H*MM/2, 0)
    stack = empty('5 degree PCB plane', enclosure, center)
    theta = math.radians(p['typing_angle_deg'])
    stack.location.z = (p['floor_mm']+p['front_under_pcb_clearance_mm']+1.6*math.cos(theta))*MM
    stack.rotation_euler.x = theta
    mats = dict(case=material('Charcoal matte printed case', '252c34', .48, texture=True),
                ivory=material('Warm white PBT caps', 'e8e3d8', .57, texture=True),
                grey=material('Stone grey PBT modifiers', 'a9adb0', .56, texture=True),
                red=material('Oxblood accent PBT caps', '954d4a', .54, texture=True),
                ink=material('Charcoal legends and sockets', '15191e', .7),
                white_ink=material('Ivory accent legends', 'f2ede5', .65),
                plate=material('Satin switch plate', '414b54', .4, metallic=.45),
                brass=material('Brass inserts', 'bb8d39', .3, metallic=.8),
                steel=material('Stainless hardware', '969da3', .25, metallic=.85),
                stab=material('Black stabilizer nylon', '28292b', .45))
    base = import_print_part('Cleaver-case-base-rev0.6.stl', report, enclosure, center, mats['case'])
    cover = import_print_part('Cleaver-case-top-cover-rev0.6.stl', report, enclosure, stack, mats['case'])
    # Tiny render-only edge rounds catch the light without changing saved CAD.
    for obj in (base, cover):
        bevel = obj.modifiers.new('Render-only edge highlight', 'BEVEL')
        bevel.width, bevel.segments, bevel.limit_method = .10*MM, 2, 'ANGLE'
    pcb_counts = import_pcb(args.pcb, electronics, stack)
    bpy.ops.wm.stl_import(filepath=str(CASE.parent/'Cleaver-top-plate-rev0.6.stl'), forward_axis='Y', up_axis='Z')
    plate = bpy.context.object
    plate.name = 'Exact 1.5 mm rev0.6 switch plate'
    for vertex in plate.data.vertices:
        vertex.co *= MM
    plate.parent = stack
    plate.location.z = 3.5*MM
    plate.data.materials.append(mats['plate'])
    move_to(plate, enclosure)
    cap_counts = add_caps(cap_collection, stack, mats)
    hardware_counts = add_hardware(report, hardware, stack, mats)
    studio(environment)
    scene = bpy.context.scene
    scene.unit_settings.system, scene.unit_settings.scale_length = 'METRIC', 1
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 24 if args.draft else 128
    scene.cycles.use_denoising = True
    scene.cycles.adaptive_threshold = .025 if args.draft else .012
    scene.cycles.max_bounces = 8
    scene.render.resolution_x, scene.render.resolution_y = (1600, 1000) if args.draft else (3000, 1875)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format, scene.render.image_settings.color_mode = 'PNG', 'RGBA'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = -3
    scene.render.film_transparent = False
    args.output.mkdir(parents=True, exist_ok=True)
    output = args.output/('Cleaver-rev0.6-assembled-draft.png' if args.draft else 'Cleaver-rev0.6-assembled.png')
    scene.render.filepath = str(output)
    if args.save_scene:
        args.save_scene.parent.mkdir(parents=True, exist_ok=True)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(args.save_scene), compress=True)
    print('ASSEMBLY CONTENTS:', json.dumps(dict(pcb=pcb_counts, caps=cap_counts, hardware=hardware_counts)), flush=True)
    bpy.ops.render.render(write_still=True)
    assert all(sha(ROOT/path) == before for path, before in input_hashes.items()), 'A CAD input changed'
    metadata = dict(render=output.name, blender=bpy.app.version_string, engine='Cycles CPU',
                    resolution_px=[scene.render.resolution_x, scene.render.resolution_y],
                    samples=scene.cycles.samples, exact_cad_inputs_sha256=input_hashes,
                    geometry=dict(pcb=pcb_counts, caps=cap_counts, hardware=hardware_counts),
                    appearance='Illustrative charcoal enclosure, ivory/stone keycaps and muted red accents; unpowered RGB',
                    limitations=['Keycap profiles and materials are illustrative, not purchased-part CAD',
                                 'Stabilizers and threaded hardware are visual approximations',
                                 'Bundled PCB component model approximations still apply',
                                 'Internal parts are present in the scene but normally hidden by the opaque closed case'],
                    image_sha256=sha(output))
    (args.output/(output.stem+'.json')).write_text(json.dumps(metadata, indent=2)+'\n')
    print('Saved assembled render:', output, flush=True)


if __name__ == '__main__':
    main()
