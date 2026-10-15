"""Tests for the module frame. Pure geometry, no Cadwork."""
import math
import unittest
from typing import List, Sequence, Tuple

from vestack.frame import LocalBox, frame_from_floor, union

Point3 = Tuple[float, float, float]


def box_vertices(x0: float, y0: float, z0: float,
                 x1: float, y1: float, z1: float) -> List[Point3]:
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def rotated(points: Sequence[Point3], degrees: float,
            shift: Point3 = (0.0, 0.0, 0.0)) -> List[Point3]:
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s + shift[0], x * s + y * c + shift[1], z + shift[2])
            for x, y, z in points]


FLOOR = box_vertices(0, 0, 0, 6000, 2500, 220)


class Orientation(unittest.TestCase):
    def assertVector(self, actual: Sequence[float], expected: Sequence[float]) -> None:
        # 0.01 mm: hull points are rounded to 0.001 mm, outputs to 1 mm.
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, delta=0.01)

    def test_an_aligned_floor_gives_the_model_axes(self) -> None:
        frame = frame_from_floor(FLOOR)
        assert frame is not None
        self.assertVector(frame.x_axis, (1, 0, 0))
        self.assertVector(frame.y_axis, (0, 1, 0))
        self.assertVector(frame.z_axis, (0, 0, 1))
        self.assertVector(frame.origin, (0, 0, 0))
        self.assertAlmostEqual(frame.length, 6000)
        self.assertAlmostEqual(frame.width, 2500)

    def test_x_runs_along_the_longer_side(self) -> None:
        frame = frame_from_floor(box_vertices(0, 0, 0, 2500, 6000, 220))
        assert frame is not None
        self.assertVector(frame.x_axis, (0, 1, 0))
        self.assertVector(frame.y_axis, (-1, 0, 0))
        self.assertAlmostEqual(frame.length, 6000)

    def test_a_floor_rotated_by_90_degrees_keeps_x_on_plus_y(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 90, shift=(10000, 5000, 0)))
        assert frame is not None
        self.assertVector(frame.x_axis, (0, 1, 0))
        self.assertVector(frame.origin, (10000, 5000, 0))

    def test_a_floor_rotated_by_37_degrees(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 37, shift=(500, 800, 300)))
        assert frame is not None
        a = math.radians(37)
        self.assertVector(frame.x_axis, (math.cos(a), math.sin(a), 0))
        self.assertVector(frame.origin, (500, 800, 300))
        self.assertAlmostEqual(frame.length, 6000, delta=0.01)
        self.assertAlmostEqual(frame.width, 2500, delta=0.01)

    def test_180_degree_tie_break_keeps_x_within_90_degrees_of_plus_x(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 180 + 37))
        assert frame is not None
        self.assertGreater(frame.x_axis[0], 0)

    def test_every_floor_vertex_has_non_negative_local_coordinates(self) -> None:
        points = rotated(FLOOR, 123, shift=(-4000, 2000, 50))
        frame = frame_from_floor(points)
        assert frame is not None
        for p in points:
            x, y, z = frame.to_local(p)
            self.assertGreaterEqual(x, -1e-6)
            self.assertGreaterEqual(y, -1e-6)
            self.assertGreaterEqual(z, -1e-6)

    def test_to_model_inverts_to_local(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 37, shift=(500, 800, 300)))
        assert frame is not None
        point = (1234.0, -56.0, 789.0)
        self.assertVector(frame.to_local(frame.to_model(point)), point)


class Quality(unittest.TestCase):
    def test_a_rectangle_has_a_plan_area_ratio_of_one(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 37))
        assert frame is not None
        self.assertAlmostEqual(frame.plan_area_ratio, 1.0, places=6)

    def test_an_l_shaped_floor_has_a_low_ratio(self) -> None:
        l_shape = (box_vertices(0, 0, 0, 6000, 1000, 220)
                   + box_vertices(0, 0, 0, 1000, 6000, 220))
        frame = frame_from_floor(l_shape)
        assert frame is not None
        self.assertLess(frame.plan_area_ratio, 0.8)

    def test_degenerate_input_gives_no_frame(self) -> None:
        self.assertIsNone(frame_from_floor([]))
        self.assertIsNone(frame_from_floor([(0, 0, 0), (100, 0, 0), (200, 0, 10)]))


class Boxes(unittest.TestCase):
    def test_box_of_expresses_vertices_in_the_frame(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 90, shift=(10000, 5000, 0)))
        assert frame is not None
        wall = rotated(box_vertices(0, 0, 220, 6000, 200, 2900), 90, shift=(10000, 5000, 0))
        box = frame.box_of(wall)
        for actual, expected in zip(box.lo + box.hi, (0, 0, 220, 6000, 200, 2900)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_union_and_contains(self) -> None:
        box = union([LocalBox((0, 0, 0), (1, 1, 1)), LocalBox((2, -1, 0), (3, 1, 5))])
        self.assertEqual((box.lo, box.hi), ((0, -1, 0), (3, 1, 5)))
        self.assertTrue(box.contains((1.5, 0, 2)))
        self.assertFalse(box.contains((4, 0, 0)))
        self.assertTrue(box.contains((3.05, 0, 0), tolerance=0.1))


if __name__ == "__main__":
    unittest.main()
