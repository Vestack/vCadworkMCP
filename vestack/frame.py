"""Module frame: a right-handed frame local to one module.

Pure geometry, no Cadwork import. The frame comes from the bottom floor's
vertices: X runs along the longer side of the minimum-area rectangle that
encloses them in plan, Z is vertical, Y completes the frame. The origin is the
floor corner from which every floor vertex has x >= 0 and y >= 0, at the
underside of the floor. Lengths are millimetres.
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]

_EPS = 1e-9
# Tolerance for the 90-degree tie-break, in radians: about 0.06 mm over 6 m,
# above the 0.001 mm hull rounding noise and below modelling precision.
_ANGLE_EPS = 1e-5


def _dot(a: Point3, b: Point3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@dataclass(frozen=True)
class LocalBox:
    """Axis-aligned box in a module frame."""

    lo: Point3
    hi: Point3

    @property
    def size(self) -> Point3:
        return (self.hi[0] - self.lo[0], self.hi[1] - self.lo[1], self.hi[2] - self.lo[2])

    @property
    def centre(self) -> Point3:
        return ((self.lo[0] + self.hi[0]) / 2, (self.lo[1] + self.hi[1]) / 2,
                (self.lo[2] + self.hi[2]) / 2)

    def contains(self, point: Point3, tolerance: float = 0.0) -> bool:
        return all(self.lo[i] - tolerance <= point[i] <= self.hi[i] + tolerance
                   for i in range(3))


def union(boxes: Sequence[LocalBox]) -> LocalBox:
    """Smallest box containing every given box."""
    return LocalBox(
        (min(b.lo[0] for b in boxes), min(b.lo[1] for b in boxes), min(b.lo[2] for b in boxes)),
        (max(b.hi[0] for b in boxes), max(b.hi[1] for b in boxes), max(b.hi[2] for b in boxes)),
    )


@dataclass(frozen=True)
class ModuleFrame:
    """A module's local frame, expressed in model coordinates."""

    origin: Point3
    x_axis: Point3
    y_axis: Point3
    z_axis: Point3
    length: float           # floor extent along X
    width: float            # floor extent along Y
    plan_area_ratio: float  # floor hull area / enclosing rectangle area

    def to_local(self, point: Point3) -> Point3:
        d = (point[0] - self.origin[0], point[1] - self.origin[1], point[2] - self.origin[2])
        return (_dot(d, self.x_axis), _dot(d, self.y_axis), _dot(d, self.z_axis))

    def to_model(self, point: Point3) -> Point3:
        x, y, z = point
        o, ax, ay, az = self.origin, self.x_axis, self.y_axis, self.z_axis
        return (o[0] + x * ax[0] + y * ay[0] + z * az[0],
                o[1] + x * ax[1] + y * ay[1] + z * az[1],
                o[2] + x * ax[2] + y * ay[2] + z * az[2])

    def box_of(self, vertices: Sequence[Point3]) -> LocalBox:
        """Bounding box, in this frame, of vertices given in model coordinates."""
        local = [self.to_local(v) for v in vertices]
        xs, ys, zs = zip(*local)
        return LocalBox((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def _cross(o: Point2, a: Point2, b: Point2) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: Sequence[Point2]) -> List[Point2]:
    """Convex hull, counter-clockwise (Andrew's monotone chain)."""
    pts = sorted({(round(x, 3), round(y, 3)) for x, y in points})
    if len(pts) <= 2:
        return pts
    lower: List[Point2] = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= _EPS:
            lower.pop()
        lower.append(p)
    upper: List[Point2] = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= _EPS:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def polygon_area(polygon: Sequence[Point2]) -> float:
    """Area of a simple polygon (shoelace formula)."""
    n = len(polygon)
    twice = sum(polygon[i][0] * polygon[(i + 1) % n][1]
                - polygon[(i + 1) % n][0] * polygon[i][1] for i in range(n))
    return abs(twice) / 2.0


def min_area_rectangle(hull: Sequence[Point2]) -> Optional[Tuple[Point2, float, float]]:
    """Direction and extents of the minimum-area rectangle enclosing a hull.

    One rectangle side lies along a hull edge, so trying each edge suffices.
    Returns (unit direction of that side, extent along it, extent across it).
    """
    best: Optional[Tuple[Point2, float, float]] = None
    best_area = math.inf
    n = len(hull)
    for i in range(n):
        ex, ey = hull[(i + 1) % n][0] - hull[i][0], hull[(i + 1) % n][1] - hull[i][1]
        edge = math.hypot(ex, ey)
        if edge < _EPS:
            continue
        ux, uy = ex / edge, ey / edge
        us = [px * ux + py * uy for px, py in hull]
        vs = [-px * uy + py * ux for px, py in hull]
        du, dv = max(us) - min(us), max(vs) - min(vs)
        if du * dv < best_area - _EPS:
            best, best_area = ((ux, uy), du, dv), du * dv
    return best


def frame_from_floor(vertices: Sequence[Point3]) -> Optional[ModuleFrame]:
    """Module frame from the bottom floor's vertices, or None if degenerate."""
    hull = convex_hull([(p[0], p[1]) for p in vertices])
    if len(hull) < 3:
        return None
    rectangle = min_area_rectangle(hull)
    if rectangle is None:
        return None
    (ux, uy), du, dv = rectangle
    xd = (ux, uy) if du >= dv else (-uy, ux)
    # 180-degree tie-break: X within 90 degrees of the model's +X; when
    # perpendicular to it within _ANGLE_EPS, X is +Y.
    if xd[0] < -_ANGLE_EPS or (abs(xd[0]) <= _ANGLE_EPS and xd[1] < 0):
        xd = (-xd[0], -xd[1])
    if abs(xd[0]) <= _ANGLE_EPS:
        xd = (0.0, 1.0 if xd[1] > 0 else -1.0)
    if abs(xd[1]) <= _ANGLE_EPS:
        xd = (1.0 if xd[0] > 0 else -1.0, 0.0)
    x_axis: Point3 = (xd[0], xd[1], 0.0)
    y_axis: Point3 = (-xd[1] + 0.0, xd[0], 0.0)
    z_axis: Point3 = (0.0, 0.0, 1.0)

    us = [p[0] * x_axis[0] + p[1] * x_axis[1] for p in vertices]
    vs = [p[0] * y_axis[0] + p[1] * y_axis[1] for p in vertices]
    u0, v0 = min(us), min(vs)
    origin: Point3 = (u0 * x_axis[0] + v0 * y_axis[0],
                      u0 * x_axis[1] + v0 * y_axis[1],
                      min(p[2] for p in vertices))
    length, width = max(us) - u0, max(vs) - v0
    area = length * width
    ratio = polygon_area(hull) / area if area > _EPS else 0.0
    return ModuleFrame(origin, x_axis, y_axis, z_axis, length, width, ratio)
