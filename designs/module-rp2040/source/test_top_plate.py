"""Top-plate alignment, stabilizer clearance and serialized STL regressions."""
import hashlib
import importlib.util
import json
import unittest
from unittest.mock import patch

import pcbnew

from design import ROOT, BOARD_W, BOARD_H, REVISION

HAS_MESH_TOOLS = all(importlib.util.find_spec(name) is not None
                     for name in ['numpy', 'scipy', 'shapely', 'trimesh'])
if HAS_MESH_TOOLS:
    import numpy as np
    import trimesh
    from shapely import Point, Polygon, box
    from generate_mechanical import geometry
    from generate_top_plate import OUT, THICKNESS, fit_coupon, top_surface, validate_pcb


@unittest.skipUnless(HAS_MESH_TOOLS, 'Top-plate tests require Shapely >=2.1, NumPy, SciPy and Trimesh')
class TopPlateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = ROOT/'Cleaver.kicad_pcb'
        cls.board = pcbnew.LoadBoard(str(cls.source))
        cls.plate, _, cls.stabs = geometry(top_capacitor_opening=False)
        cls.report = json.loads((OUT/'validation.json').read_text())
        cls.mesh = trimesh.load_mesh(OUT/f'Cleaver-top-plate-rev{REVISION}.stl')
        cls.surface = top_surface(cls.mesh, THICKNESS)
        cls.openings = [Polygon(ring) for ring in cls.surface.interiors]

    def test_saved_pcb_alignment_and_revision(self):
        checks = validate_pcb(self.source, self.plate)
        self.assertEqual(checks['revision'], REVISION)
        self.assertEqual(checks['switch_centres_matched'], 117)
        self.assertEqual(len(checks['mounting_holes']), 11)
        self.assertTrue(checks['controller_body_clear'])
        self.assertEqual(self.report['source_sha256'], hashlib.sha256(self.source.read_bytes()).hexdigest())

    def test_rejects_moved_switch(self):
        board = pcbnew.LoadBoard(str(self.source))
        switch = next(fp for fp in board.GetFootprints() if fp.GetReference() == 'SW102')
        switch.Move(pcbnew.VECTOR2I(pcbnew.FromMM(.1), 0))
        with patch('generate_top_plate.pcbnew.LoadBoard', return_value=board):
            with self.assertRaisesRegex(AssertionError, 'SW102: switch centre changed'):
                validate_pcb(self.source, self.plate)

    def test_rejects_wrong_mounting_drill(self):
        board = pcbnew.LoadBoard(str(self.source))
        mount = next(fp for fp in board.GetFootprints() if fp.GetReference() == 'H1')
        list(mount.Pads())[0].SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(2.5), pcbnew.FromMM(2.5)))
        with patch('generate_top_plate.pcbnew.LoadBoard', return_value=board):
            with self.assertRaisesRegex(AssertionError, 'H1'):
                validate_pcb(self.source, self.plate)

    def test_legacy_plate_geometry_preserved(self):
        legacy, _, _ = geometry()
        cap = Point(377, 6).buffer(5, quad_segs=64)
        self.assertLess(legacy.difference(self.plate).area, 1e-8)
        self.assertLess(self.plate.difference(legacy).symmetric_difference(cap).area, 1e-8)
        self.assertTrue(self.plate.covers(Point(377, 6)))

    def test_serialized_switch_openings_match_all_pcb_centres(self):
        switches = [fp for fp in self.board.GetFootprints() if fp.GetReference().startswith('SW')]
        self.assertEqual(len(switches), 117)
        stabilized = {stab['ref'] for stab in self.stabs}
        for switch in switches:
            x, pcb_y = pcbnew.ToMM(switch.GetPosition())
            y = BOARD_H-pcb_y
            openings = [hole for hole in self.openings if hole.contains(Point(x, y))]
            self.assertEqual(len(openings), 1, switch.GetReference())
            self.assertTrue(openings[0].covers(box(x-6.9999, y-6.9999, x+6.9999, y+6.9999)))
            if switch.GetReference() not in stabilized:
                np.testing.assert_allclose(openings[0].bounds, [x-7, y-7, x+7, y+7], rtol=0, atol=2e-5)

    def test_serialized_mounts_are_2_2mm_through_holes(self):
        bottom = top_surface(self.mesh, 0)
        self.assertTrue(bottom.equals(self.surface), 'Top and bottom openings differ')
        mounts = [fp for fp in self.board.GetFootprints()
                  if fp.GetReference().startswith('H') and fp.GetReference()[1:].isdigit()]
        self.assertEqual(len(mounts), 11)
        for mount in mounts:
            pad = list(mount.Pads())[0]
            x, pcb_y = pcbnew.ToMM(pad.GetPosition())
            y = BOARD_H-pcb_y
            holes = [hole for hole in self.openings if hole.contains(Point(x, y))]
            self.assertEqual(len(holes), 1, mount.GetReference())
            np.testing.assert_allclose(holes[0].bounds, [x-1.1, y-1.1, x+1.1, y+1.1], rtol=0, atol=2e-5)
            self.assertAlmostEqual(holes[0].area, Point(0, 0).buffer(1.1, quad_segs=64).area, places=4)

    def test_stabilizer_stems_latches_and_wire_clearance(self):
        expected = {'SW031': (23.8, 0), 'SW060': (23.8, 90), 'SW074': (23.8, 0),
                    'SW079': (23.8, 0), 'SW090': (23.8, 0), 'SW097': (23.8, 90),
                    'SW102': (100, 0), 'SW110': (23.8, 0)}
        self.assertEqual({stab['ref'] for stab in self.stabs}, set(expected))
        for stab in self.stabs:
            spacing, rotation = expected[stab['ref']]
            self.assertEqual((stab['stem_spacing_mm'], stab['rotation_deg']), (spacing, rotation))
            x, y = stab['x_mm'], stab['y_mm']
            hole = next(h for h in self.openings if h.contains(Point(x, BOARD_H-y)))
            samples = [(0, 0), (spacing/4, 0), (-spacing/4, 0)]
            for sign in [-1, 1]:
                samples.extend([(sign*spacing/2, -5.5), (sign*spacing/2, 7.9),
                                (sign*(spacing/2+3.7), -1)])
            for u, v in samples:
                dx, dy = (-v, u) if rotation == 90 else (u, v)
                self.assertTrue(hole.contains(Point(x+dx, BOARD_H-y-dy)), stab['ref'])

    def test_controller_notch_and_no_obsolete_capacitor_hole(self):
        self.assertFalse(self.surface.intersects(box(398.01, BOARD_H-25.49, BOARD_W, BOARD_H)))
        self.assertTrue(self.surface.covers(Point(377, BOARD_H-6)))
        self.assertEqual(len(self.surface.interiors), 128)
        self.assertEqual(self.mesh.euler_number, 2-2*128)

    def test_all_stls_and_report_agree(self):
        expected_sizes = [[BOARD_W, BOARD_H, THICKNESS], [40, 24, THICKNESS], [120, 24, THICKNESS]]
        self.assertEqual(len(self.report['parts']), 3)
        for part, size in zip(self.report['parts'], expected_sizes):
            path = OUT/part['file']
            mesh = trimesh.load_mesh(path)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), part['sha256'])
            np.testing.assert_allclose(mesh.extents, size, rtol=0, atol=2e-5)
            self.assertTrue(mesh.is_watertight and mesh.is_volume and mesh.is_winding_consistent)
            self.assertEqual(mesh.body_count, 1)
            self.assertEqual(len(mesh.faces), part['triangles'])
            self.assertEqual(mesh.euler_number, 2-2*part['through_openings'])
            self.assertAlmostEqual(mesh.volume, part['volume_mm3'], places=4)
        for size in [2, 6.25]:
            coupon = fit_coupon(size)
            self.assertEqual(len(coupon.interiors), 2)
            self.assertTrue(coupon.is_valid and coupon.geom_type == 'Polygon')


if __name__ == '__main__':
    unittest.main()
