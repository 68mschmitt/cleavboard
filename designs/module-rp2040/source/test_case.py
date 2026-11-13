"""Read-only regressions for the current printed case and its CAD exports."""
import importlib.util
import json
import math
import unittest
from unittest.mock import patch

import pcbnew

from design import BOARD_H, BOARD_W, MOUNTING_HOLES, ROOT, read_keys, REVISION

HAS_CASE_TOOLS = all(importlib.util.find_spec(name) is not None
                     for name in ['numpy', 'scipy', 'shapely', 'trimesh'])
if HAS_CASE_TOOLS:
    import numpy as np
    import trimesh
    from shapely import Point, Polygon, box, unary_union
    from shapely.affinity import affine_transform
    from build_3d_models import freecad
    from generate_case import (OUT, Parameters, assembled, cover_screws, digest,
                               outlines, prism, validate_source, world_point)
    from generate_mechanical import geometry
    from generate_top_plate import top_surface


@unittest.skipUnless(HAS_CASE_TOOLS, 'Case tests require Shapely >=2.1, NumPy, SciPy and Trimesh')
class CaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUT/'validation.json').read_text())
        cls.p = Parameters(**json.loads((OUT/'parameters.json').read_text()))
        cls.records = {item['file']: item for item in cls.report['parts']}

    def unprinted(self, name):
        """Undo exactly the documented STL bed orientation/translation."""
        item = self.records[name]
        mesh = trimesh.load_mesh(OUT/name)
        mesh.apply_translation(-np.array(item['stl_additional_mesh_translation_mm']))
        mesh.apply_translation(-np.array(item['stl_translation_after_optional_x_flip_mm']))
        if item['stl_face_down']:
            mesh.apply_transform(trimesh.transformations.rotation_matrix(math.pi, [1, 0, 0]))
        return mesh

    def pcb_coordinates(self, mesh):
        mesh.apply_translation([0, 0, -self.p.front_pcb_top])
        mesh.apply_transform(trimesh.transformations.rotation_matrix(
            -math.radians(self.p.typing_angle_deg), [1, 0, 0]))
        return mesh

    def test_parameters_source_and_matching_plate(self):
        self.p.validate()
        self.assertEqual(self.report['parameters'], json.loads((OUT/'parameters.json').read_text()))
        self.assertEqual(self.report['source_sha256'], digest(ROOT/'Cleaver.kicad_pcb'))
        self.assertEqual(self.report['matching_plate_sha256'],
                         digest(ROOT/f'mechanical/rev{REVISION}/Cleaver-top-plate-rev{REVISION}.stl'))
        plate, _, _ = geometry(top_capacitor_opening=False)
        checks = validate_source(self.p, plate)
        self.assertTrue(checks['existing_plate_stl_matches'])
        self.assertEqual(len(checks['mounting_holes']), 11)

    def test_rejects_changed_capacitor_location(self):
        board = pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb'))
        cap = next(fp for fp in board.GetFootprints() if fp.GetReference() == 'C5')
        cap.Move(pcbnew.VECTOR2I(pcbnew.FromMM(.1), 0))
        plate, _, _ = geometry(top_capacitor_opening=False)
        with patch('generate_case.pcbnew.LoadBoard', return_value=board):
            with self.assertRaises(AssertionError):
                validate_source(self.p, plate)

    def test_serialized_standoffs_match_all_pcb_holes(self):
        mesh = self.pcb_coordinates(self.unprinted(f'Cleaver-case-base-rev{REVISION}.stl'))
        material = top_surface(mesh, -1.6)
        self.assertEqual(material.geom_type, 'MultiPolygon')
        self.assertEqual(len(material.geoms), 11)
        for x, y in MOUNTING_HOLES:
            expected = Point(x, BOARD_H-y).buffer(3, quad_segs=64).difference(
                Point(x, BOARD_H-y).buffer(self.p.insert_bore_mm/2, quad_segs=64))
            found = [poly for poly in material.geoms if poly.distance(Point(x, BOARD_H-y)) < 1.6]
            self.assertEqual(len(found), 1, (x, y))
            self.assertEqual(len(found[0].interiors), 1)
            self.assertLess(found[0].symmetric_difference(expected).area, .08)
            np.testing.assert_allclose(found[0].bounds, expected.bounds, rtol=0, atol=.005)

    def test_case_floor_is_flat_and_unpierced(self):
        mesh = self.unprinted(f'Cleaver-case-base-rev{REVISION}.stl')
        floor = top_surface(mesh, 0)
        self.assertTrue(floor.is_valid)
        self.assertEqual(floor.geom_type, 'Polygon')
        self.assertEqual(len(floor.interiors), 0, 'Insert pockets must not break through the floor')
        self.assertGreater(floor.area, BOARD_W*BOARD_H)

    def test_cover_serialized_material_and_all_keycap_apertures(self):
        mesh = self.unprinted(f'Cleaver-case-top-cover-rev{REVISION}.stl')
        actual = affine_transform(top_surface(mesh, self.p.cover_top), [1, 0, 0, -1, 0, BOARD_H])
        _, _, apertures, deck = outlines(self.p)
        holes = unary_union([Point(x, y).buffer(self.p.cover_head_recess_diameter_mm/2,
                                               quad_segs=64) for x, y in cover_screws(self.p)])
        expected = deck.difference(holes)
        self.assertEqual(actual.geom_type, 'Polygon')
        self.assertEqual(len(actual.interiors), 20)  # 12 key clusters + 8 cover screws
        self.assertLess(actual.symmetric_difference(expected).area, .15)
        self.assertLess(actual.boundary.hausdorff_distance(expected.boundary), .005)
        keys, _ = read_keys()
        for key in keys:
            swept = box(key['x']-(key['w']*19.05-1)/2, key['y']-(key['h']*19.05-1)/2,
                        key['x']+(key['w']*19.05-1)/2, key['y']+(key['h']*19.05-1)/2)
            self.assertTrue(apertures.covers(swept), key['ref'])
            self.assertLess(actual.intersection(swept).area, 1e-8, key['ref'])
        for blank in [(4, 4), (377, 6), (425, 13), (313, 70), (365, 138)]:
            self.assertTrue(actual.covers(Point(*blank)), f'Uncovered blank PCB area {blank}')

    def test_cad_no_interference_and_usb_opening(self):
        try:
            _, part = freecad()
        except ImportError:
            self.skipTest('CAD collision checks require FreeCAD')
        base = part.read(str(OUT/f'Cleaver-case-base-rev{REVISION}.step'))
        cover = assembled(part.read(str(OUT/f'Cleaver-case-top-cover-rev{REVISION}.step')), self.p)
        self.assertLess(base.common(cover).Volume, 1e-6)
        # Independently construct a plug gauge in the documented side opening.
        gauge = prism(box(BOARD_W-2.9, 13.39-7.9, BOARD_W+self.p.margin+.5, 13.39+7.9),
                      5.74-3.5, 7.0)
        gauge = assembled(gauge, self.p)
        self.assertLess(base.common(gauge).Volume, 1e-6)
        self.assertLess(cover.common(gauge).Volume, 1e-6)
        cap = assembled(prism(box(371, .5, 383, 11.5), -12.6, 11), self.p)
        self.assertLess(base.common(cap).Volume, 1e-6)

    def test_back_is_higher_and_bores_follow_pcb_normal(self):
        rear = world_point(0, 0, 0, self.p)
        front = world_point(0, BOARD_H, 0, self.p)
        self.assertGreater(rear[2], front[2])
        self.assertAlmostEqual(math.degrees(math.atan2(rear[2]-front[2], rear[1]-front[1])), 5)
        axis = np.array(world_point(0, 0, 1, self.p))-np.array(rear)
        np.testing.assert_allclose(axis, [0, -math.sin(math.radians(5)), math.cos(math.radians(5))])
        self.assertGreater(self.report['fit_checks']['minimum_c5_clear_depth_normal_to_pcb_mm'], 11)

    def test_all_exported_stls_are_single_watertight_parts(self):
        self.assertEqual(len(self.records), 10)
        for name, item in self.records.items():
            mesh = trimesh.load_mesh(OUT/name)
            self.assertEqual(digest(OUT/name), item['sha256'])
            self.assertEqual(digest(OUT/item['step_file']), item['step_sha256'])
            self.assertTrue(mesh.is_watertight and mesh.is_winding_consistent and mesh.is_volume, name)
            self.assertEqual(mesh.body_count, 1, name)
            self.assertTrue(np.all(mesh.area_faces > 1e-10), name)
            np.testing.assert_allclose(mesh.bounds[0], [0, 0, 0], rtol=0, atol=2e-5)
            np.testing.assert_allclose(mesh.extents, item['size_mm'], rtol=0, atol=.0001)
            self.assertLess(abs(mesh.volume-item['cad_volume_mm3'])/mesh.volume, .002)
        for name in [f'Cleaver-case-assembly-rev{REVISION}.FCStd', f'Cleaver-case-assembly-rev{REVISION}.step', 'case-plan.svg']:
            self.assertTrue((OUT/name).is_file(), name)

    def test_socket_backstops_and_clearance_recorded(self):
        checks=self.report['fit_checks']
        self.assertTrue(checks['controller_socketed_envelope_clear'])
        self.assertEqual({s['reference'] for s in checks['controller_sockets']},{'J1','J2'})
        self.assertTrue(all(s['backstop_present'] and s['nominal_unshimmed_backstop_gap_mm']==.7
                            and s['minimum_unshimmed_backstop_gap_mm']>=.19
                            for s in checks['controller_sockets']))


if __name__ == '__main__':
    unittest.main()
