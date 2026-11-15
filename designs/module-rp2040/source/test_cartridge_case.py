"""Rev0.11 serialized cartridge, drill families, USB capture and measured insert."""
import csv
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pcbnew
import trimesh
from shapely import Point, Polygon, box

from build_3d_models import freecad
from check_rev08_migration import copper_record
from design import ROOT, BOARD_H, BOARD_W, read_keys
from generate_case import assembled, cylinder, digest, prism
from generate_cartridge_case import OUT, Parameters, usb_parts
from generate_top_plate import top_surface, validate_pcb
from generate_mechanical import geometry
from mounting_interface import BASE_POSTS, PCB_ATTACHMENTS


class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUT/'validation.json').read_text())
        cls.p = Parameters(**json.loads((OUT/'parameters.json').read_text()))
        cls.board = pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
        _, part = freecad()
        cls.base = part.read(str(OUT/'final-prints/Cleaver-case-base-rev0.11.step'))
        cls.plate = part.read(str(OUT/'final-prints/Cleaver-switch-plate-rev0.11.step'))
        cls.cover = part.read(str(OUT/'final-prints/Cleaver-case-top-cover-rev0.11.step'))
        cls.bezel = part.read(str(OUT/'final-prints/USB-bezel-nominal.step'))
        cls.records = {Path(item['file']).name: item for item in cls.report['parts']}

    def unprinted(self, name):
        item = self.records[name]
        mesh = trimesh.load_mesh(OUT/item['file'])
        mesh.apply_translation(-np.array(item['stl_additional_mesh_translation_mm']))
        mesh.apply_translation(-np.array(item['stl_translation_after_optional_x_flip_mm']))
        if item['stl_face_down']:
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        rotation = item.get('stl_rotation_axis_angle')
        if rotation:
            mesh.apply_transform(trimesh.transformations.rotation_matrix(-math.radians(rotation[3]), rotation[:3]))
        return mesh

    def test_two_distinct_drill_families_and_no_old_mounts(self):
        fps = {fp.GetReference(): fp for fp in self.board.GetFootprints()}
        mounts = [fp for ref, fp in fps.items() if ref.startswith('H') and ref[1:].isdigit()]
        self.assertEqual(len(mounts), 24)
        self.assertEqual(self.board.GetTitleBlock().GetRevision(), '0.11')
        for i, xy in enumerate(BASE_POSTS+PCB_ATTACHMENTS, 1):
            fp = fps[f'H{i}']
            pad = list(fp.Pads())[0]
            self.assertEqual(tuple(pcbnew.ToMM(fp.GetPosition())), xy)
            self.assertEqual(pad.GetAttribute(), pcbnew.PAD_ATTRIB_NPTH)
            self.assertEqual(tuple(pcbnew.ToMM(pad.GetDrillSize())), (7., 7.) if i <= 12 else (2.2, 2.2))
        with (ROOT/'manufacturing/rev0.11/mounting-holes.csv').open() as file:
            rows = list(csv.DictReader(file))
        self.assertEqual(len(rows), 24)
        self.assertEqual(sum(float(row['drill_mm']) == 7 for row in rows), 12)
        self.assertEqual(sum(float(row['drill_mm']) == 2.2 for row in rows), 12)

    def test_all_routed_copper_and_electrical_pads_retained(self):
        baseline = pcbnew.LoadBoard(str(ROOT/'source/baselines/rev0.9/Cleaver.kicad_pcb'))
        for board in (baseline, self.board):
            self.assertEqual(len(list(board.GetTracks())), 5528)
        self.assertEqual({item.m_Uuid.AsString(): copper_record(item) for item in baseline.GetTracks()},
                         {item.m_Uuid.AsString(): copper_record(item) for item in self.board.GetTracks()})
        def electrical(board):
            return {(fp.GetReference(), pad.GetNumber(), tuple(pcbnew.ToMM(pad.GetPosition()))): pad.GetNetname()
                    for fp in board.GetFootprints() if not fp.GetReference().startswith('H') for pad in fp.Pads()}
        self.assertEqual(electrical(baseline), electrical(self.board))

    def test_saved_plate_has_upward_mount_holes_and_blind_downward_bosses(self):
        self.assertAlmostEqual(self.plate.BoundBox.ZMin, 0)
        self.assertAlmostEqual(self.plate.BoundBox.ZMax, 5)
        surface = top_surface(self.unprinted('Cleaver-switch-plate-rev0.11.stl'), 5)
        holes = [Polygon(ring) for ring in surface.interiors]
        for x, y in BASE_POSTS:
            hole = next(h for h in holes if h.contains(Point(x, BOARD_H-y)))
            np.testing.assert_allclose(hole.bounds, [x-1.4, BOARD_H-y-1.4, x+1.4, BOARD_H-y+1.4], atol=.005, rtol=0)
            top_ring = cylinder(x, y, 3.4, 5.9, .05).cut(cylinder(x, y, 3.3, 3.1, .3))
            top_ring = assembled(top_ring, self.p)
            self.assertAlmostEqual(self.base.common(top_ring).Volume, top_ring.Volume, places=6)
        for x, y in PCB_ATTACHMENTS:
            pilot = cylinder(x, y, -.01, 2.95, 2.8)
            self.assertLess(self.plate.common(pilot).Volume, 1e-6)
            blind_roof = cylinder(x, y, 2.9, 2.8, 2)
            self.assertAlmostEqual(self.plate.common(blind_roof).Volume, blind_roof.Volume, places=6)
            self.assertTrue(surface.covers(Point(x, BOARD_H-y).buffer(2)))
        self.assertEqual(len(holes), 130)

    def test_all_switch_and_stabilizer_openings_match_saved_plate(self):
        # Compare the entire serialized top face to the independently generated
        # 2D clip profile, including every stabilizer notch and wire clearance.
        from shapely.affinity import affine_transform
        plan, _, stabs = geometry(top_capacitor_opening=False)
        face = top_surface(self.unprinted('Cleaver-switch-plate-rev0.11.stl'), 5)
        face = affine_transform(face, [1, 0, 0, -1, 0, BOARD_H])
        self.assertLess(face.symmetric_difference(plan).area, .1)
        self.assertLess(face.boundary.hausdorff_distance(plan.boundary), .005)
        self.assertEqual(len(stabs), 8)
        self.assertEqual(validate_pcb(ROOT/'Cleaver.kicad_pcb', plan)['switch_centres_matched'], 117)

    def test_assembly_clearance_and_actual_screw_directions(self):
        for x, y in BASE_POSTS:
            screw = cylinder(x, y, 0, 2, 5).fuse(cylinder(x, y, 5, 3.8, 2))
            self.assertLess(self.plate.common(screw).Volume, 1e-6)
            self.assertLess(self.base.common(assembled(screw, self.p)).Volume, 1e-6)
        for x, y in PCB_ATTACHMENTS:
            screw = cylinder(x, y, -1.9, 2, 4).fuse(cylinder(x, y, -3.9, 3.8, 2))
            self.assertLess(self.plate.common(screw).Volume, 1e-6)
            self.assertLess(self.base.common(assembled(screw, self.p)).Volume, 1e-6)
        self.assertLess(self.base.common(assembled(self.plate, self.p)).Volume, 1e-6)
        self.assertLess(self.cover.common(self.plate).Volume, 1e-6)

    def test_usb_insert_is_removable_with_cover_off_and_captured_when_closed(self):
        app, _ = freecad()
        self.assertLess(self.base.common(assembled(self.bezel, self.p)).Volume, 1e-6)
        self.assertLess(self.cover.common(self.bezel).Volume, 1e-6)
        for height in (.1, 1, 4, 15):
            lifted = self.bezel.copy()
            lifted.translate(app.Vector(0, 0, height))
            self.assertLess(self.base.common(assembled(lifted, self.p)).Volume, 1e-6)
        lifted = self.bezel.copy()
        lifted.translate(app.Vector(0, 0, .5))
        self.assertGreater(self.cover.common(lifted).Volume, .1)
        for dx in (-1, 1):
            shifted = self.bezel.copy()
            shifted.translate(app.Vector(dx, 0, 0))
            self.assertGreater(self.base.common(assembled(shifted, self.p)).Volume, .1)

    def test_measured_usb_bezel_cli_and_invalid_opening_rejected(self):
        with tempfile.TemporaryDirectory(dir='/tmp/opencode', prefix='cleaver-usb-') as temp:
            subprocess.run([sys.executable, '-B', str(ROOT/'source/generate_cartridge_case.py'),
                            '--usb-only', '--usb-y-offset', '.6', '--usb-z-offset', '-.4',
                            '--usb-height', '8',
                            '--output', temp], check=True, capture_output=True)
            _, part = freecad()
            fitted = part.read(str(Path(temp)/'final-prints/USB-bezel-fitted.step'))
            # Independent gauge at measured center Y=13.99, Z=5.34.
            opening = prism(box(BOARD_W+2.8, 13.99-7.99, BOARD_W+7, 13.99+7.99), 5.34-3.99, 7.98)
            self.assertLess(fitted.common(opening).Volume, 1e-6)
            self.assertLess(self.base.common(assembled(fitted, self.p)).Volume, 1e-6)
            self.assertLess(self.cover.common(fitted).Volume, 1e-6)
            self.assertTrue(trimesh.load_mesh(Path(temp)/'final-prints/USB-bezel-fitted.stl').is_watertight)
        for invalid in (dict(usb_port_y_offset_mm=20), dict(usb_port_z_offset_mm=10)):
            with self.assertRaises(AssertionError):
                Parameters(**invalid).validate()

    def test_stack_coupon_supports_both_assembly_stages(self):
        _, part = freecad()
        base = part.read(str(OUT/'test-prints/Cartridge-stack-coupon-base.step'))
        plate = part.read(str(OUT/'test-prints/Cartridge-stack-coupon-plate.step'))
        pcb = part.read(str(OUT/'test-prints/Cartridge-stack-coupon-dummy-PCB.step'))
        self.assertAlmostEqual(pcb.BoundBox.ZMin, -1.6)
        self.assertAlmostEqual(pcb.BoundBox.ZMax, .6)  # raised ID on external tab
        self.assertAlmostEqual(plate.BoundBox.ZMin, 0)
        self.assertAlmostEqual(plate.BoundBox.ZMax, 5)
        self.assertLess(plate.common(pcb).Volume, 1e-6)
        self.assertLess(base.common(assembled(pcb, self.p)).Volume, 1e-6)
        self.assertLess(base.common(assembled(plate, self.p)).Volume, 1e-6)

    def test_exports_provenance_and_clean_electrical_checks(self):
        self.assertEqual(self.report['source_sha256'], digest(ROOT/'Cleaver.kicad_pcb'))
        for name, expected in self.report['source_files'].items():
            self.assertEqual(digest(ROOT/name), expected, name)
        for name, record in self.records.items():
            mesh = trimesh.load_mesh(OUT/record['file'])
            self.assertEqual(digest(OUT/record['file']), record['sha256'], name)
            self.assertEqual(digest(OUT/record['step_file']), record['step_sha256'])
            self.assertTrue(mesh.is_volume and mesh.is_watertight and mesh.is_winding_consistent, name)
            self.assertEqual(mesh.body_count, 1)
            np.testing.assert_allclose(mesh.bounds[0], [0, 0, 0], atol=2e-5)
            self.assertLess(abs(mesh.volume-record['cad_volume_mm3'])/mesh.volume, .002)
        for name, expected in self.report['assembly_sha256'].items():
            self.assertEqual(digest(OUT/name), expected)
        checks = ROOT/'manufacturing/rev0.11/checks'
        drc = json.loads((checks/'drc.json').read_text())
        self.assertFalse(drc['violations'] or drc['unconnected_items'] or drc.get('schematic_parity', []))
        erc = json.loads((checks/'erc.json').read_text())
        self.assertFalse(any(sheet['violations'] for sheet in erc['sheets']))

    def test_labeled_fit_sets_remain_clear_when_assembled(self):
        from coupon_labels import LABELS
        app, part = freecad()
        groups = {}
        local = {}
        for name, (code, *_) in LABELS.items():
            record = self.records[name+'.stl']
            self.assertEqual(record['fit_label']['id'], code)
            shape = part.read(str(OUT/record['step_file']))
            self.assertTrue(shape.isValid())
            self.assertEqual(len(shape.Solids), 1)
            local[code] = shape
            if code[0] in 'ABCD' and code != 'D3':
                if not name.endswith('-base'):
                    shape = assembled(shape, self.p)
                groups.setdefault(code[0], []).append((code, shape))
        for members in groups.values():
            for i, (code, shape) in enumerate(members):
                for other_code, other in members[i+1:]:
                    self.assertLess(shape.common(other).Volume, 1e-6,
                                    f'{code}/{other_code}: label/tab obstructs fit')
        # Labels must also leave the insertion/removal paths open.
        for lift in (.1, 1, 5, 15):
            for moving, base in [('A2', 'A1'), ('A3', 'A1'), ('B3', 'B1')]:
                lifted = local[moving].copy()
                lifted.translate(app.Vector(0, 0, lift))
                self.assertLess(local[base].common(assembled(lifted, self.p)).Volume,
                                1e-6, f'{moving}: tab blocks removal at {lift} mm')

    def test_usb_blank_body_and_label_tab_share_print_bed(self):
        record = self.records['USB-bezel-blank.stl']
        mesh = trimesh.load_mesh(OUT/record['file'])
        bottom = ((np.abs(mesh.triangles[:, :, 2]).max(axis=1) < 1e-5)
                  & (mesh.face_normals[:, 2] < -.99))
        # Entire 24 x 12.8 outer face plus the 12 x 7 label extension must
        # contact the bed, rather than standing the body on the label tab.
        self.assertAlmostEqual(mesh.area_faces[bottom].sum(), 24*12.8+12*7, places=2)


if __name__ == '__main__':
    unittest.main()
