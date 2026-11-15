"""Independent checks of serialized mechanical rev0.10 parts and hardware paths."""
import json
import math
import unittest
import hashlib
import zipfile

import numpy as np
from shapely import Point, box
from shapely.affinity import affine_transform
import trimesh

from build_3d_models import freecad
from design import BOARD_H, BOARD_W, ROOT
from generate_case import assembled, cylinder, digest, prism, world_point, SOURCE_PCB
from generate_case_service import OUT, Parameters
from generate_top_plate import top_surface


class ServiceCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUT/'validation.json').read_text())
        cls.p = Parameters(**json.loads((OUT/'parameters.json').read_text()))
        cls.records = {record['file']: record for record in cls.report['parts']}
        _, part = freecad()
        cls.base = part.read(str(OUT/'Cleaver-case-base-rev0.10.step'))
        cls.cover = part.read(str(OUT/'Cleaver-case-top-cover-rev0.10.step'))
        cls.well = part.read(str(OUT/'Logo-light-well.step'))
        cls.badge = part.read(str(OUT/'Logo-insert-blank.step'))

    def unprinted(self, name):
        record = self.records[name]
        mesh = trimesh.load_mesh(OUT/name)
        mesh.apply_translation(-np.array(record['stl_additional_mesh_translation_mm']))
        mesh.apply_translation(-np.array(record['stl_translation_after_optional_x_flip_mm']))
        if record['stl_face_down']:
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        return mesh

    def test_release_provenance_and_export_integrity(self):
        self.assertEqual(self.report['compatible_pcb_revision'], '0.9')
        self.assertEqual(self.report['source_sha256'], digest(SOURCE_PCB))
        self.assertEqual(self.report['matching_plate_sha256'],
                         digest(ROOT/'mechanical/rev0.9/Cleaver-top-plate-rev0.9.stl'))
        # Rev0.10 is now a historical release. Its source snapshot, rather than
        # today's evolving shared helpers, must match its recorded provenance.
        with zipfile.ZipFile(OUT.parent/'generator-snapshot.zip') as snapshot:
            for filename, expected in self.report['source_files'].items():
                self.assertEqual(hashlib.sha256(snapshot.read(filename)).hexdigest(), expected, filename)
        for name, record in self.records.items():
            self.assertEqual(digest(OUT/name), record['sha256'], name)
            self.assertEqual(digest(OUT/record['step_file']), record['step_sha256'])
            mesh = trimesh.load_mesh(OUT/name)
            self.assertTrue(mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume, name)
            self.assertEqual(mesh.body_count, 1, name)
            np.testing.assert_allclose(mesh.bounds[0], [0, 0, 0], rtol=0, atol=2e-5)
        for filename, expected in self.report['assembly_sha256'].items():
            self.assertEqual(digest(OUT/filename), expected)

    def test_top_has_only_key_and_badge_openings(self):
        mesh = self.unprinted('Cleaver-case-top-cover-rev0.10.stl')
        face = affine_transform(top_surface(mesh, 10.8), [1, 0, 0, -1, 0, BOARD_H])
        self.assertEqual(face.geom_type, 'Polygon')
        self.assertEqual(len(face.interiors), 13)  # 12 key clusters + badge, no screws
        for y in (-4.5, 160.1375):
            for x in (10, 145, 300, BOARD_W-10):
                self.assertTrue(face.covers(Point(x, y).buffer(2)), (x, y))

    def test_bottom_access_screw_seats_and_roof(self):
        # Independent hardware envelope from the drawing/BOM, not generator
        # screw construction. All dimensions normal to the PCB.
        p = self.p
        for y in (-4.5, 160.1375):
            for x in (10, 145, 300, BOARD_W-10):
                head = cylinder(x, y, -3.1, 3.8, 2)
                shank = cylinder(x, y, -1.1, 2, 8)
                hardware = head.fuse(shank)
                self.assertLess(self.base.common(assembled(hardware, p)).Volume, 1e-6)
                self.assertLess(self.cover.common(hardware).Volume, 1e-6)
                seat = cylinder(x, y, -1.1, 3.7, .05).cut(cylinder(x, y, -1.2, 2.3, .3))
                seat = assembled(seat, p)
                self.assertAlmostEqual(self.base.common(seat).Volume, seat.Volume, places=6)
                driver = assembled(cylinder(x, y, -45, 4.4, 41.8), p)
                self.assertLess(self.base.common(driver).Volume, 1e-6)
                roof = cylinder(x, y, 8.0, 2.8, 2.7)
                self.assertAlmostEqual(self.cover.common(roof).Volume, roof.Volume, places=6)

    def test_assembled_solids_and_badge_stack_gauge(self):
        self.assertLess(self.base.common(assembled(self.cover, self.p)).Volume, 1e-6)
        self.assertLess(self.cover.common(self.well).Volume, 1e-6)
        self.assertLess(self.cover.common(self.badge).Volume, 1e-6)
        _, part = freecad()
        coupon = part.read(str(OUT/'Logo-fit-coupon-plate-with-height-gauges.step'))
        cover = part.read(str(OUT/'Logo-fit-coupon-cover.step'))
        self.assertAlmostEqual(coupon.BoundBox.ZMax, 8.4)
        for component in (cover, self.well, self.badge):
            self.assertLess(coupon.common(component).Volume, 1e-6)
        # 0.8 mm loose foam becomes a 0.6 mm gasket in the installed section.
        foam = part.read(str(OUT/'Logo-gasket-cutting-pattern-0.8mm.step'))
        self.assertAlmostEqual(foam.BoundBox.ZLength, .8)
        self.assertAlmostEqual(self.report['fit_checks']['logo_gasket']['installed_gap_mm'], .6)
        self.assertEqual(self.report['fit_checks']['logo_gasket']['nominal_compression_percent'], 25)

    def test_lower_floor_keeps_component_clearance(self):
        p = self.p
        # Conservative 4 mm underside switch/socket envelope at all switches.
        # The new cover pillars are outside the PCB and do not consume this space.
        from design import read_keys
        keys, _ = read_keys()
        for key in keys:
            envelope = prism(box(key['x']-7, key['y']-7, key['x']+7, key['y']+7), -5.6, 4)
            self.assertLess(self.base.common(assembled(envelope, p)).Volume, 1e-6, key['ref'])
        c5 = assembled(prism(box(371, .5, 383, 11.5), -12.6, 11), p)
        self.assertLess(self.base.common(c5).Volume, 1e-6)
        usb = assembled(prism(box(BOARD_W-2.9, 5.49, BOARD_W+7, 21.29), 2.24, 7), p)
        self.assertLess(self.base.common(usb).Volume, 1e-6)
        self.assertLess(assembled(self.cover, p).common(usb).Volume, 1e-6)

    def test_measured_height_reductions(self):
        comparison = self.report['fit_checks']['height_comparison']
        self.assertGreater(comparison['reduction']['front_edge_mm'], 1)
        self.assertGreater(comparison['reduction']['home_row_keycap_reference_top_mm'], 2)
        self.assertGreater(comparison['reduction']['rear_cover_top_mm'], 5)
        # Measure the physical cover after transforming its exported STEP.
        cover = assembled(self.cover, self.p)
        self.assertAlmostEqual(cover.BoundBox.ZMax, comparison['after']['rear_cover_top_mm'], places=3)
        self.assertAlmostEqual(self.base.BoundBox.XLength, 465.9375, places=4)
        # OCC's conservative box for trimmed tilted cylinders can extend below
        # the real solid. Probe material below the desk rather than that box.
        app, part = freecad()
        below_desk = part.makeBox(600, 300, 10, app.Vector(-50, -50, -10.00001))
        self.assertLess(self.base.common(below_desk).Volume, 1e-6)
        mesh = self.unprinted('Cleaver-case-base-rev0.10.stl')
        self.assertAlmostEqual(mesh.bounds[0, 2], 0, places=5)
        rear = world_point(0, 0, 0, self.p)
        front = world_point(0, BOARD_H, 0, self.p)
        self.assertAlmostEqual(math.degrees(math.atan2(rear[2]-front[2], rear[1]-front[1])), 3)


if __name__ == '__main__':
    unittest.main()
