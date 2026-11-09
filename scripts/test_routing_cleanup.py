"""Route simplification must respect obstacles and mid-segment junctions."""
import importlib.util
import unittest

import pcbnew

HAS_SHAPELY = importlib.util.find_spec('shapely') is not None
if HAS_SHAPELY:
    from shapely import Point
    from clean_routing import anchored_runs, candidates, simplify


@unittest.skipUnless(HAS_SHAPELY, 'Routing cleanup tests require Shapely >=2')
class RoutingCleanupTests(unittest.TestCase):
    def setUp(self):
        self.board = pcbnew.BOARD()

    def track(self, a, b):
        t = pcbnew.PCB_TRACK(self.board)
        t.SetStart(pcbnew.VECTOR2I(round(a[0]*1e6), round(a[1]*1e6)))
        t.SetEnd(pcbnew.VECTOR2I(round(b[0]*1e6), round(b[1]*1e6)))
        t.SetWidth(200000)
        self.board.Add(t)
        return t

    def test_mid_segment_branch_is_preserved(self):
        tracks = [self.track((0, 0), (10, 0)), self.track((10, 0), (15, 5)),
                  self.track((5, 0), (5, 3))]
        chains = anchored_runs(tracks, [])
        self.assertIn(([0], [(0., 0.), (10., 0.)]), chains)
        self.assertFalse(any(0 in edges and 1 in edges for edges, _ in chains))

    def test_via_landing_inside_track_is_preserved(self):
        tracks = [self.track((0, 0), (10, 0)), self.track((10, 0), (15, 5))]
        chains = anchored_runs(tracks, [Point(5, 0).buffer(.3)])
        self.assertFalse(any(0 in edges and 1 in edges for edges, _ in chains))

    def test_only_octilinear_shortcuts(self):
        for path in candidates((1.123, 2.456), (17.89, 9.876)):
            self.assertEqual(path[0], (1.123, 2.456))
            self.assertEqual(path[-1], (17.89, 9.876))
            for a, b in zip(path, path[1:]):
                dx, dy = abs(b[0]-a[0]), abs(b[1]-a[1])
                self.assertTrue(dx < 1e-6 or dy < 1e-6 or abs(dx-dy) < 1e-6)

    def test_blocked_shortcut_keeps_detour(self):
        from shapely import LineString, box
        obstacle = box(3, -1, 7, 2)
        class Clearance:
            def clear(self, a, b):
                return LineString([a, b]).distance(obstacle) > .3
        original = [(0, 0), (0, 3), (2, 3), (8, 3), (10, 3), (10, 0)]
        result = simplify(original, Clearance())
        self.assertEqual(result[0], original[0])
        self.assertEqual(result[-1], original[-1])
        self.assertLess(len(result), len(original))
        for a, b in zip(result, result[1:]):
            self.assertGreater(LineString([a, b]).distance(obstacle), .3)


if __name__ == '__main__':
    unittest.main()
