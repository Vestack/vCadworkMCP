"""Module inventory for Vestack modular buildings.

Pure domain logic: it takes element snapshots and returns an inventory. Nothing
here imports Cadwork, so it can be unit-tested outside Cadwork. The adapter that
reads the snapshots from a live model is vestack/bridge_handler.py.

A module is a rectangular box: a bottom floor, often a top floor, and up to eight
walls. Its dimensions are derived from the bottom floor, which is present even in
open modules (those left wall-less on one or more sides to form a larger room).
"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from . import conventions as cv
from .naming import module_number, parse_module_id

# (x_min, y_min, z_min, x_max, y_max, z_max), in millimetres.
BBox = Tuple[float, float, float, float, float, float]

SIDES: Tuple[str, ...] = ("-x", "+x", "-y", "+y")


@dataclass
class ElementSnapshot:
    """What the inventory needs to know about one Cadwork element."""

    element_id: int
    bbox: BBox
    name: str = ""
    group: str = ""
    subgroup: str = ""
    volume_mm3: Optional[float] = None
    user_attributes: Dict[int, str] = field(default_factory=dict)
    building: str = ""
    level: str = ""


def extents(bbox: BBox) -> Tuple[float, float, float]:
    """Size of a bounding box along X, Y and Z."""
    return (bbox[3] - bbox[0], bbox[4] - bbox[1], bbox[5] - bbox[2])


def field_value(snapshot: ElementSnapshot, source: str) -> str:
    """Read one id-carrying field, named either "group" or "user_attribute_3"."""
    if source.startswith("user_attribute_"):
        number = int(source.rsplit("_", 1)[1])
        return snapshot.user_attributes.get(number, "")
    value = getattr(snapshot, source, "")
    return value if isinstance(value, str) else ""


def extract_module_id(value: str) -> Optional[str]:
    """Pull a module id out of a field value, in canonical form ("M001" -> "M1")."""
    return parse_module_id(value)


def candidate_id_sources(snapshots: Sequence[ElementSnapshot]) -> List[str]:
    """Fields that could hold the module id, in order of preference."""
    numbers = sorted({n for s in snapshots for n in s.user_attributes})
    return list(cv.PLAIN_ID_FIELDS) + [f"user_attribute_{n}" for n in numbers]


def detect_id_source(snapshots: Sequence[ElementSnapshot]) -> Optional[str]:
    """Find which field carries the module id, by counting matches.

    Returns the field name, or None when no field holds a module id anywhere.
    Ties go to the earliest candidate, so a plain field beats a user attribute.
    """
    best_source: Optional[str] = None
    best_count = 0
    for source in candidate_id_sources(snapshots):
        count = sum(1 for s in snapshots if extract_module_id(field_value(s, source)))
        if count > best_count:
            best_source, best_count = source, count
    return best_source


def classify(bbox: BBox) -> str:
    """Sort one element into "slab", "wall" or "other" from its shape alone."""
    dx, dy, dz = extents(bbox)
    thickness, middle, _longest = sorted((dx, dy, dz))

    if dz == thickness and dz <= cv.SLAB_MAX_THICKNESS_RATIO * middle:
        return "slab"

    plan_thickness, plan_length = min(dx, dy), max(dx, dy)
    if (dz >= cv.WALL_MIN_HEIGHT_MM
            and plan_thickness <= cv.WALL_MAX_THICKNESS_MM
            and plan_length >= cv.WALL_MIN_LENGTH_MM):
        return "wall"

    return "other"


def _overlap(low_a: float, high_a: float, low_b: float, high_b: float) -> float:
    """Length shared by two intervals."""
    return max(0.0, min(high_a, high_b) - max(low_a, low_b))


def _closes_side(wall: BBox, floor: BBox, side: str) -> bool:
    """Whether a wall stands along one edge of the floor and spans enough of it."""
    fx0, fy0, _fz0, fx1, fy1, _fz1 = floor
    wx0, wy0, _wz0, wx1, wy1, _wz1 = wall

    if side == "-x":
        on_edge = wx0 <= fx0 + cv.SIDE_BAND_MM
        covered, length = _overlap(wy0, wy1, fy0, fy1), fy1 - fy0
    elif side == "+x":
        on_edge = wx1 >= fx1 - cv.SIDE_BAND_MM
        covered, length = _overlap(wy0, wy1, fy0, fy1), fy1 - fy0
    elif side == "-y":
        on_edge = wy0 <= fy0 + cv.SIDE_BAND_MM
        covered, length = _overlap(wx0, wx1, fx0, fx1), fx1 - fx0
    else:  # "+y"
        on_edge = wy1 >= fy1 - cv.SIDE_BAND_MM
        covered, length = _overlap(wx0, wx1, fx0, fx1), fx1 - fx0

    if not on_edge or length <= 0:
        return False
    return covered / length >= cv.MIN_SIDE_COVERAGE


def open_sides(floor: BBox, walls: Sequence[BBox]) -> List[str]:
    """Edges of the floor that no wall closes."""
    return [side for side in SIDES
            if not any(_closes_side(w, floor, side) for w in walls)]


def _plan_area_ratio(snapshot: ElementSnapshot) -> Optional[float]:
    """Real plan area of a slab over its bounding-box footprint, when knowable."""
    dx, dy, dz = extents(snapshot.bbox)
    if snapshot.volume_mm3 is None or dz <= 0 or dx * dy <= 0:
        return None
    return (snapshot.volume_mm3 / dz) / (dx * dy)


def _majority(values: Sequence[str]) -> str:
    """Most frequent non-empty value, or an empty string."""
    present = [v for v in values if v]
    return Counter(present).most_common(1)[0][0] if present else ""


def _slab_summary(snapshot: ElementSnapshot) -> Dict[str, Any]:
    return {
        "element_id": snapshot.element_id,
        "thickness_mm": extents(snapshot.bbox)[2],
    }


def _build_module(module_id: str, snapshots: Sequence[ElementSnapshot]) -> Dict[str, Any]:
    """Assemble the report for one module."""
    roles = {s.element_id: classify(s.bbox) for s in snapshots}
    slabs = [s for s in snapshots if roles[s.element_id] == "slab"]
    walls = [s for s in snapshots if roles[s.element_id] == "wall"]
    others = [s for s in snapshots if roles[s.element_id] == "other"]

    warnings: List[str] = []
    bottom = min(slabs, key=lambda s: s.bbox[2]) if slabs else None

    top: Optional[ElementSnapshot] = None
    if bottom is not None:
        above = [s for s in slabs
                 if s.bbox[2] >= bottom.bbox[5] + cv.TOP_FLOOR_MIN_CLEARANCE_MM]
        top = max(above, key=lambda s: s.bbox[2]) if above else None

    dimensions: Optional[Dict[str, float]] = None
    footprint_m2: Optional[float] = None
    origin: Optional[List[float]] = None
    sides_open: List[str] = []

    if bottom is None:
        warnings.append("no bottom floor found: dimensions cannot be derived")
    else:
        dx, dy, _dz = extents(bottom.bbox)
        dimensions = {
            "length": max(dx, dy),
            "width": min(dx, dy),
            "height": (max(s.bbox[5] for s in snapshots)
                       - min(s.bbox[2] for s in snapshots)),
        }
        footprint_m2 = round(dx * dy / 1_000_000.0, 3)
        origin = [bottom.bbox[0], bottom.bbox[1], bottom.bbox[2]]
        sides_open = open_sides(bottom.bbox, [w.bbox for w in walls])

        ratio = _plan_area_ratio(bottom)
        if ratio is not None and ratio < cv.MIN_PLAN_AREA_RATIO:
            warnings.append(
                f"bottom floor plan area is {ratio:.0%} of its bounding box: "
                "the floor is rotated in plan or not rectangular, so the "
                "dimensions below overstate the module"
            )

    for label, values in (("buildings", [s.building for s in snapshots]),
                          ("levels", [s.level for s in snapshots])):
        distinct = sorted({v for v in values if v})
        if len(distinct) > 1:
            warnings.append(f"elements span several {label}: {', '.join(distinct)}")

    return {
        "module_id": module_id,
        "building": _majority([s.building for s in snapshots]),
        "level": _majority([s.level for s in snapshots]),
        "element_count": len(snapshots),
        "element_ids": sorted(s.element_id for s in snapshots),
        "dimensions_mm": dimensions,
        "footprint_area_m2": footprint_m2,
        "origin_mm": origin,
        "bottom_floor": _slab_summary(bottom) if bottom else None,
        "top_floor": _slab_summary(top) if top else None,
        "has_top_floor": top is not None,
        "walls": {
            "count": len(walls),
            "open_sides": sides_open,
            "closed_sides": [s for s in SIDES if s not in sides_open],
        },
        "other_count": len(others),
        "warnings": warnings,
    }


def build_inventory(snapshots: Sequence[ElementSnapshot],
                    id_source: Optional[str] = None) -> Dict[str, Any]:
    """Group elements into modules and report each module's dimensions.

    Args:
        snapshots: one entry per element considered.
        id_source: field holding the module id ("subgroup", "user_attribute_3",
            ...). Detected from the snapshots when omitted.

    Returns:
        Inventory dict: modules sorted by id, plus totals and warnings.
    """
    warnings: List[str] = []
    source = id_source or detect_id_source(snapshots)
    if source is None and snapshots:
        warnings.append(
            "no module id found in any field: expected an "
            f"{cv.MODULE_ID_PATTERN.pattern} value in a group, subgroup, name "
            "or user attribute"
        )

    grouped: Dict[str, List[ElementSnapshot]] = {}
    unassigned = 0
    for snapshot in snapshots:
        module_id = extract_module_id(field_value(snapshot, source)) if source else None
        if module_id is None:
            unassigned += 1
        else:
            grouped.setdefault(module_id, []).append(snapshot)

    modules = [_build_module(mid, grouped[mid]) for mid in sorted(grouped, key=module_number)]

    return {
        "status": "ok",
        "id_source": source,
        "module_count": len(modules),
        "modules": modules,
        "unassigned_element_count": unassigned,
        "totals": {
            "footprint_area_m2": round(
                sum(m["footprint_area_m2"] or 0.0 for m in modules), 3),
            "element_count": sum(m["element_count"] for m in modules),
        },
        "warnings": warnings,
    }
