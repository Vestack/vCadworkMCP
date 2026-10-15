"""Object inventory: walls, slabs, roofs and openings per module, in module frames.

Pure domain logic, no Cadwork import: it takes ObjectSnapshot values and returns
the vestack.object_inventory/1 structure documented in OBJECT_INVENTORY.md. The
adapter that reads snapshots from a live model is vestack/bridge_handler.py.

Reading vertices is the costly part of a scan (14 ms per element on Cadwork
2026), so the bridge first reads attributes only, asks geometry_needed() which
elements need vertices, then reads those. Elements whose vertices were not read
simply carry an empty tuple.
"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Collection, Dict, List, Optional, Sequence, Set, Tuple

from . import conventions as cv
from .frame import LocalBox, ModuleFrame, Point3, frame_from_floor, union
from .module_inventory import classify
from .naming import (
    PartRef,
    floor_level_hint,
    is_joinery,
    is_processing,
    module_number,
    parse_module_id,
    parse_part,
    wall_body_section,
)

SCHEMA = "vestack.object_inventory/1"
DETAIL_LEVELS: Tuple[str, ...] = ("none", "envelope", "vertices")
SIDES: Tuple[str, ...] = ("-x", "+x", "-y", "+y")


@dataclass
class ObjectSnapshot:
    """What the object inventory needs to know about one Cadwork element."""

    element_id: int
    name: str = ""
    group: str = ""
    subgroup: str = ""
    module_attribute: str = ""
    complex_code: str = ""
    material: str = ""
    vertices: Tuple[Point3, ...] = ()


@dataclass
class _Module:
    module_id: str
    parts: Dict[str, List[ObjectSnapshot]] = field(default_factory=dict)
    part_refs: Dict[str, PartRef] = field(default_factory=dict)
    loose: List[ObjectSnapshot] = field(default_factory=list)
    disagreements: int = 0


# --- helpers ---------------------------------------------------------------

def _mm(value: float) -> int:
    return int(round(value))


def _pt(point: Sequence[float]) -> List[int]:
    return [_mm(c) for c in point]


def _model_bbox(vertices: Sequence[Point3]) -> Tuple[float, float, float, float, float, float]:
    xs, ys, zs = zip(*vertices)
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def element_module(snapshot: ObjectSnapshot) -> Tuple[Optional[str], Optional[PartRef], bool]:
    """Module and part of one element, and whether subgroup and attribute disagree.

    The subgroup wins over the Module attribute, then comes the group. The
    element name is never read: hardware names carry metric threads ("Tige
    filetée M12", "Vis M8 x 120") that read as module ids.
    """
    part = parse_part(snapshot.subgroup)
    from_subgroup = (part.module_id if part and part.module_id
                     else parse_module_id(snapshot.subgroup))
    from_attribute = parse_module_id(snapshot.module_attribute)
    module = from_subgroup or from_attribute or parse_module_id(snapshot.group)
    disagree = bool(from_subgroup and from_attribute and from_subgroup != from_attribute)
    return module, part, disagree


def _object_id(module_id: str, part: PartRef) -> str:
    return f"{module_id}-{part.prefix}{part.number}"


def _part_sort_key(object_id: str) -> Tuple[str, int, str]:
    tail = object_id.split("-", 1)[1]
    letters = tail.rstrip("0123456789")
    digits = tail[len(letters):]
    return (letters.upper(), int(digits) if digits else -1, tail)


def _partition(snapshots: Sequence[ObjectSnapshot]
               ) -> Tuple[Dict[str, _Module], List[ObjectSnapshot], List[int], int]:
    """Split elements into modules, joinery, unattached ids and a processing count."""
    modules: Dict[str, _Module] = {}
    joinery: List[ObjectSnapshot] = []
    unattached: List[int] = []
    processing = 0
    for s in snapshots:
        if is_processing(s.group):
            processing += 1
            continue
        if is_joinery(s.name):
            joinery.append(s)
            continue
        module_id, part, disagree = element_module(s)
        if module_id is None:
            unattached.append(s.element_id)
            continue
        module = modules.setdefault(module_id, _Module(module_id))
        module.disagreements += int(disagree)
        if part is None:
            module.loose.append(s)
        else:
            object_id = _object_id(module_id, part)
            module.parts.setdefault(object_id, []).append(s)
            module.part_refs[object_id] = part
    return modules, joinery, unattached, processing


def _wall_bodies(elements: Sequence[ObjectSnapshot]) -> List[ObjectSnapshot]:
    return [e for e in elements if wall_body_section(e.name) is not None]


def _is_top_hinted(e: ObjectSnapshot) -> bool:
    return floor_level_hint(e.group, e.complex_code) == "top"


def _floor_parts(module: _Module) -> Dict[str, List[ObjectSnapshot]]:
    """Slab parts that may hold the bottom floor: elements hinted "top" left out."""
    parts = {oid: [e for e in els if not _is_top_hinted(e)]
             for oid, els in module.parts.items()
             if module.part_refs[oid].object_type == "slab"}
    return {oid: els for oid, els in parts.items() if els}


def _is_known_prefix(prefix: str) -> bool:
    return prefix.upper() in cv.PART_TYPES or prefix.lower() in cv.NAMED_PARTS


def _unknown_prefixes(module: _Module) -> List[str]:
    return sorted({r.prefix for r in module.part_refs.values() if not _is_known_prefix(r.prefix)})


def geometry_needed(snapshots: Sequence[ObjectSnapshot],
                    module_ids: Optional[Collection[str]] = None,
                    detail_all: bool = False) -> Set[int]:
    """Ids of the elements whose vertices the inventory needs.

    Always: joinery, wall bodies (all wall elements when a wall has no single
    body), slab parts (to find the bottom floor), and every element of a module
    with no slab part that may be its bottom floor (none, or only parts hinted
    "top"). In detailed modules: every element.
    """
    requested = {parse_module_id(m) or m for m in (module_ids or [])}
    modules, joinery, _unattached, _processing = _partition(snapshots)
    needed: Set[int] = {s.element_id for s in joinery}
    for module in modules.values():
        everything = detail_all or module.module_id in requested
        has_floor_part = bool(_floor_parts(module))
        for object_id, elements in module.parts.items():
            object_type = module.part_refs[object_id].object_type
            if everything or not has_floor_part or object_type == "slab":
                needed.update(e.element_id for e in elements)
            elif object_type == "wall":
                bodies = _wall_bodies(elements)
                needed.update(e.element_id for e in (bodies if len(bodies) == 1 else elements))
        if everything or not has_floor_part:
            needed.update(e.element_id for e in module.loose)
    return needed


# --- frame -----------------------------------------------------------------

def _with_vertices(elements: Sequence[ObjectSnapshot]) -> List[ObjectSnapshot]:
    return [e for e in elements if e.vertices]


def _bottom_floor(module: _Module) -> List[ObjectSnapshot]:
    """Elements making the module's bottom floor, possibly none.

    In order: slab-part elements hinted "bottom", else the lowest slab part
    (elements hinted "top" left out), else the lowest loose slabs.
    """
    slab_parts = {oid: _with_vertices(els) for oid, els in _floor_parts(module).items()}
    slab_parts = {oid: els for oid, els in slab_parts.items() if els}
    hinted = [e for els in slab_parts.values() for e in els
              if floor_level_hint(e.group, e.complex_code) == "bottom"]
    if hinted:
        return hinted
    if slab_parts:
        return min(slab_parts.values(),
                   key=lambda els: min(v[2] for e in els for v in e.vertices))
    candidates = [e for e in _with_vertices(module.loose)
                  if classify(_model_bbox(e.vertices)) == "slab"]
    if not candidates:
        return []
    # Anchor on the largest panel near the bottom, so that a small piece lower
    # than the floor (a wet-room recess) does not become the whole floor; keep
    # the slabs starting below the anchor's top. A wall plate resting on the
    # floor starts at that top and stays out.
    boxes = {e.element_id: _model_bbox(e.vertices) for e in candidates}
    lowest = min(b[2] for b in boxes.values())
    near = [e for e in candidates
            if boxes[e.element_id][2] <= lowest + cv.TOP_FLOOR_MIN_CLEARANCE_MM]

    def area_key(e: ObjectSnapshot) -> Tuple[float, int]:
        x0, y0, _z0, x1, y1, _z1 = boxes[e.element_id]
        return (-(x1 - x0) * (y1 - y0), e.element_id)

    anchor_top = boxes[min(near, key=area_key).element_id][5]
    return [e for e in candidates if boxes[e.element_id][2] < anchor_top]


def _module_height(module: _Module, frame: ModuleFrame) -> Optional[float]:
    """Top of the module's elements above the frame origin, None without vertices.

    Only meaningful when every element's vertices were read, as in a detailed
    module: the summary reads too few of them and reports no height.
    """
    tops = [v[2] for els in module.parts.values() for e in els for v in e.vertices]
    tops += [v[2] for e in module.loose for v in e.vertices]
    return max(tops) - frame.origin[2] if tops else None


def _frame_dict(frame: ModuleFrame, height: Optional[float]) -> Dict[str, Any]:
    return {
        "origin_model": _pt(frame.origin),
        "x_axis_model": [round(c, 6) + 0.0 for c in frame.x_axis],
        "y_axis_model": [round(c, 6) + 0.0 for c in frame.y_axis],
        "z_axis_model": [round(c, 6) + 0.0 for c in frame.z_axis],
        "length": _mm(frame.length),
        "width": _mm(frame.width),
        "height": _mm(height) if height is not None else None,
    }


# --- objects ---------------------------------------------------------------

@dataclass
class _Wall:
    object_id: str
    body: LocalBox
    along_x: bool
    start: Point3
    record: Dict[str, Any]


def _wall_geometry(box: LocalBox, frame: ModuleFrame, along: Optional[bool] = None
                   ) -> Tuple[bool, Point3, Point3, float, Optional[str]]:
    """Axis, foot line, thickness and side of a wall box; `along` forces the axis."""
    sx, sy, _sz = box.size
    along_x = sx >= sy if along is None else along
    band = cv.SIDE_BAND_MM
    if along_x:
        mid = (box.lo[1] + box.hi[1]) / 2
        start, end, thickness = (box.lo[0], mid, box.lo[2]), (box.hi[0], mid, box.lo[2]), sy
        side = "-y" if mid <= band else "+y" if mid >= frame.width - band else None
    else:
        mid = (box.lo[0] + box.hi[0]) / 2
        start, end, thickness = (mid, box.lo[1], box.lo[2]), (mid, box.hi[1], box.lo[2]), sx
        side = "-x" if mid <= band else "+x" if mid >= frame.length - band else None
    return along_x, start, end, thickness, side


def _make_wall(object_id: str, elements: Sequence[ObjectSnapshot], frame: ModuleFrame,
               check_union: bool, along: Optional[bool] = None) -> Optional[_Wall]:
    readable = _with_vertices(elements)
    if not readable:
        return None
    warnings: List[str] = []
    bodies = [b for b in _wall_bodies(readable)]
    boxes = {e.element_id: frame.box_of(e.vertices) for e in readable}
    if len(bodies) == 1:
        body_el = bodies[0]
        body = boxes[body_el.element_id]
        wall_type: Optional[str] = body_el.name.strip()
        section = wall_body_section(body_el.name)
    else:
        body = union(list(boxes.values()))
        wall_type, section = None, None
        warnings.append(f"{len(bodies)} wall body elements (MOB<section>): "
                        "envelope taken from the union of the wall's elements")
    if check_union and len(bodies) == 1:
        tol = cv.WALL_BODY_TOLERANCE_MM
        out = sorted(eid for eid, b in boxes.items()
                     if any(body.lo[i] - b.lo[i] > tol or b.hi[i] - body.hi[i] > tol
                            for i in range(3)))
        if out:
            whole = union(list(boxes.values()))
            excess = max(max(body.lo[i] - whole.lo[i], whole.hi[i] - body.hi[i])
                         for i in range(3))
            warnings.append(f"elements stick out of the wall body by up to {_mm(excess)} mm: "
                            f"{out}")
    along_x, start, end, thickness, side = _wall_geometry(body, frame, along)
    record: Dict[str, Any] = {
        "id": object_id,
        "type": "wall",
        "wall_type": wall_type,
        "stud_section": section,
        "side": side,
        "start": _pt(start),
        "end": _pt(end),
        "thickness": _mm(thickness),
        "height": _mm(body.size[2]),
        "openings": [],
        "element_ids": sorted(e.element_id for e in elements),
        "warnings": warnings,
    }
    return _Wall(object_id, body, along_x, start, record)


def _make_box_object(object_id: str, object_type: str, elements: Sequence[ObjectSnapshot],
                     frame: ModuleFrame, part: Optional[str],
                     level: Optional[str] = None) -> Optional[Dict[str, Any]]:
    readable = _with_vertices(elements)
    if not readable:
        return None
    box = union([frame.box_of(e.vertices) for e in readable])
    record: Dict[str, Any] = {"id": object_id, "type": object_type}
    if object_type == "slab":
        record.update({"level": level, "origin": _pt(box.lo), "length": _mm(box.size[0]),
                       "width": _mm(box.size[1]), "thickness": _mm(box.size[2])})
    else:
        record.update({"part": part, "origin": _pt(box.lo), "size": _pt(box.size)})
    record["element_ids"] = sorted(e.element_id for e in elements)
    record["warnings"] = []
    return record


def _slab_level(elements: Sequence[ObjectSnapshot], is_bottom: bool) -> Optional[str]:
    hints = [h for h in (floor_level_hint(e.group, e.complex_code) for e in elements) if h]
    if hints:
        return Counter(hints).most_common(1)[0][0]
    return "bottom" if is_bottom else None


def _element_details(elements: Sequence[ObjectSnapshot], frame: ModuleFrame,
                     level: str) -> List[Dict[str, Any]]:
    details = []
    for e in sorted(_with_vertices(elements), key=lambda e: e.element_id):
        box = frame.box_of(e.vertices)
        item: Dict[str, Any] = {"element_id": e.element_id, "name": e.name,
                                "material": e.material, "origin": _pt(box.lo),
                                "size": _pt(box.size)}
        if level == "vertices":
            item["vertices"] = [_pt(frame.to_local(v)) for v in e.vertices]
        details.append(item)
    return details


# --- geometric fallback ----------------------------------------------------

def _band_side(box: LocalBox, frame: ModuleFrame) -> Optional[str]:
    band = cv.SIDE_BAND_MM
    tests = {"-x": box.hi[0] <= band, "+x": box.lo[0] >= frame.length - band,
             "-y": box.hi[1] <= band, "+y": box.lo[1] >= frame.width - band}
    return next((side for side in SIDES if tests[side]), None)


def _is_upright(box: LocalBox) -> bool:
    """Tall and thin in plan: a wall panel, or a stud, which has no length rule."""
    dx, dy, dz = box.size
    return dz >= cv.WALL_MIN_HEIGHT_MM and min(dx, dy) <= cv.WALL_MAX_THICKNESS_MM


def _gap(lo_a: float, hi_a: float, lo_b: float, hi_b: float) -> float:
    """Distance between two intervals, 0 when they overlap."""
    return max(0.0, max(lo_a, lo_b) - min(hi_a, hi_b))


def _on_plane(a: LocalBox, b: LocalBox, axis: int) -> bool:
    """Whether two upright elements share a wall plane running along `axis`.

    axis 0 is X: their centres are within the plane tolerance in y and their
    x-intervals are at most INTERIOR_WALL_GAP_MM apart. axis 1 swaps x and y.
    """
    across = 1 - axis
    return (abs(a.centre[across] - b.centre[across]) <= cv.INTERIOR_WALL_PLANE_TOLERANCE_MM
            and _gap(a.lo[axis], a.hi[axis], b.lo[axis], b.hi[axis])
            <= cv.INTERIOR_WALL_GAP_MM)


def _components(boxes: Sequence[LocalBox], axis: int) -> List[List[int]]:
    """Indices of the boxes able to stand in a wall along `axis`, grouped by
    _on_plane transitively (union-find).

    An element stands in a wall along X only when its y-size fits a wall
    thickness (WALL_MAX_THICKNESS_MM), and conversely: a panel running along Y
    never joins an X wall, even when its centre happens to lie on that plane.
    """
    across = 1 - axis
    members = [i for i, b in enumerate(boxes) if b.size[across] <= cv.WALL_MAX_THICKNESS_MM]
    parent = {i: i for i in members}

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for n, i in enumerate(members):
        for j in members[n + 1:]:
            if _on_plane(boxes[i], boxes[j], axis):
                parent[find(i)] = find(j)
    groups: Dict[int, List[int]] = {}
    for i in members:
        groups.setdefault(find(i), []).append(i)
    return list(groups.values())


def _interior_walls(upright: Sequence[Tuple[ObjectSnapshot, LocalBox]]
                    ) -> List[Tuple[bool, List[ObjectSnapshot]]]:
    """(along_x, elements) per interior wall, each element in one wall only.

    Components are found per axis, then served greedily, longest extent along
    its own axis first (ties: X before Y, then smallest element id); each takes
    the elements no longer component took. So the corner stud of an L goes to
    the longer branch, and the two branches stay two walls.
    """
    boxes = [b for _e, b in upright]
    ranked: List[Tuple[float, int, int, List[int]]] = []
    for axis in (0, 1):
        for members in _components(boxes, axis):
            extent = (max(boxes[i].hi[axis] for i in members)
                      - min(boxes[i].lo[axis] for i in members))
            first = min(upright[i][0].element_id for i in members)
            ranked.append((-extent, axis, first, members))
    ranked.sort(key=lambda r: (r[0], r[1], r[2]))
    taken: Set[int] = set()
    walls: List[Tuple[bool, List[ObjectSnapshot]]] = []
    for _extent, axis, _first, members in ranked:
        free = [i for i in members if i not in taken]
        if free:
            taken.update(free)
            walls.append((axis == 0, [upright[i][0] for i in free]))
    walls.sort(key=lambda w: min(e.element_id for e in w[1]))
    return walls


def _is_fallback_slab(box: LocalBox) -> bool:
    """Slab-shaped and wider than a wall: plates, though flat, are not slabs."""
    return (classify(box.lo + box.hi) == "slab"
            and min(box.size[0], box.size[1]) > cv.WALL_MAX_THICKNESS_MM)


def _fallback_groups(loose: Sequence[ObjectSnapshot], frame: ModuleFrame, floor_top: float,
                     floor_ids: Set[int]
                     ) -> List[Tuple[str, str, List[ObjectSnapshot], Optional[bool]]]:
    """(kind, label, elements, along_x) groups for elements outside any part subgroup.

    Tried in order per element: part of the bottom floor (floor_ids) -> the
    bottom slab; within SIDE_BAND_MM of a floor edge -> that side's wall
    (plates included); slab-shaped and wider than a wall -> the top slab when
    its underside clears the bottom floor's top (floor_top, local z) by
    TOP_FLOOR_MIN_CLEARANCE_MM, else the bottom slab; upright -> an interior
    wall (see _interior_walls); anything else, interior plates included ->
    other. along_x is set for interior walls only.
    """
    slabs: Dict[str, List[ObjectSnapshot]] = {}
    sides: Dict[str, List[ObjectSnapshot]] = {}
    upright: List[Tuple[ObjectSnapshot, LocalBox]] = []
    others: List[ObjectSnapshot] = []
    for e in _with_vertices(loose):
        box = frame.box_of(e.vertices)
        side = _band_side(box, frame)
        if e.element_id in floor_ids:
            slabs.setdefault("bottom", []).append(e)
        elif side is not None:
            sides.setdefault(side, []).append(e)
        elif _is_fallback_slab(box):
            level = ("top" if box.lo[2] >= floor_top + cv.TOP_FLOOR_MIN_CLEARANCE_MM
                     else "bottom")
            slabs.setdefault(level, []).append(e)
        elif _is_upright(box):
            upright.append((e, box))
        else:
            others.append(e)
    groups: List[Tuple[str, str, List[ObjectSnapshot], Optional[bool]]] = []
    groups += [("slab", level, slabs[level], None) for level in ("bottom", "top")
               if level in slabs]
    groups += [("wall", side, sides[side], None) for side in SIDES if side in sides]
    groups += [("wall", "interior", members, along_x)
               for along_x, members in _interior_walls(upright)]
    if others:
        groups.append(("other", "", others, None))
    return groups


# --- openings --------------------------------------------------------------

def _attach_openings(joinery: Sequence[ObjectSnapshot],
                     walls: Dict[str, List[_Wall]],
                     frames: Dict[str, ModuleFrame]
                     ) -> Tuple[Dict[str, List[Tuple[ObjectSnapshot, LocalBox]]], List[ObjectSnapshot]]:
    """Joinery attached to the wall containing its centre; the rest unattached."""
    attached: Dict[str, List[Tuple[ObjectSnapshot, LocalBox]]] = {}
    orphans: List[ObjectSnapshot] = []
    for j in joinery:
        if not j.vertices:
            orphans.append(j)
            continue
        x0, y0, z0, x1, y1, z1 = _model_bbox(j.vertices)
        centre = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        host: Optional[Tuple[_Wall, ModuleFrame]] = None
        for module_id in sorted(walls, key=module_number):
            frame = frames[module_id]
            local = frame.to_local(centre)
            for wall in walls[module_id]:
                if wall.body.contains(local, cv.JOINERY_CENTRE_TOLERANCE_MM):
                    host = (wall, frame)
                    break
            if host:
                break
        if host is None:
            orphans.append(j)
        else:
            attached.setdefault(host[0].object_id, []).append((j, host[1].box_of(j.vertices)))
    return attached, orphans


def _opening_records(wall: _Wall, items: Sequence[Tuple[ObjectSnapshot, LocalBox]]
                     ) -> List[Dict[str, Any]]:
    axis = 0 if wall.along_x else 1
    rows: List[Dict[str, Any]] = []
    for j, box in items:
        rows.append({
            "name": j.name.strip(),
            "offset": _mm(box.lo[axis] - wall.start[axis]),
            "sill": _mm(box.lo[2] - wall.start[2]),
            "width": _mm(box.size[axis]),
            "height": _mm(box.size[2]),
            "element_ids": [j.element_id],
        })
    rows.sort(key=lambda r: r["offset"])
    for n, row in enumerate(rows, start=1):
        row["id"] = f"{wall.object_id}-O{n}"
    return [{"id": r.pop("id"), **r} for r in rows]


# --- entry point -----------------------------------------------------------

@dataclass
class _GeoGroup:
    """One object of the geometric fallback, with its wall when it is one."""

    object_id: str
    kind: str
    label: str
    elements: List[ObjectSnapshot]
    wall: Optional[_Wall] = None


def _geo_groups(module: _Module, frame: ModuleFrame,
                floor: Sequence[ObjectSnapshot]) -> List[_GeoGroup]:
    """Fallback objects of a detailed module, walls built so they can take openings."""
    floor_top = max(frame.box_of(e.vertices).hi[2] for e in floor)
    floor_ids = {e.element_id for e in floor}
    groups = []
    for n, (kind, label, elements, along_x) in enumerate(
            _fallback_groups(module.loose, frame, floor_top, floor_ids), start=1):
        group = _GeoGroup(f"{module.module_id}-geo{n}", kind, label, elements)
        if kind == "wall":
            group.wall = _make_wall(group.object_id, elements, frame, check_union=False,
                                    along=along_x)
        groups.append(group)
    return groups


def build_object_inventory(snapshots: Sequence[ObjectSnapshot],
                           module_ids: Optional[Collection[str]] = None,
                           detail_all: bool = False,
                           element_detail: str = "none",
                           source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Inventory of objects per module: summary for all, detail where asked.

    Args:
        snapshots: every scanned element; vertices filled where geometry_needed()
            asked for them.
        module_ids: modules to detail (any spelling: "M001" means "M1").
        detail_all: detail every module (used for the JSON file export).
        element_detail: "none", "envelope" or "vertices" for detailed modules.
        source: provenance block copied into the result.
    """
    if element_detail not in DETAIL_LEVELS:
        raise ValueError(f"element_detail must be one of {DETAIL_LEVELS}, got {element_detail!r}")
    requested = {parse_module_id(m) or m for m in (module_ids or [])}
    modules, joinery, unattached, processing = _partition(snapshots)
    warnings = [f"module {m} not found in the scanned elements"
                for m in sorted(requested - set(modules))]

    frames: Dict[str, ModuleFrame] = {}
    floors: Dict[str, List[ObjectSnapshot]] = {}
    module_warnings: Dict[str, List[str]] = {m: [] for m in modules}
    for module_id, module in modules.items():
        floor = _bottom_floor(module)
        frame = frame_from_floor([v for e in floor for v in e.vertices]) if floor else None
        mw = module_warnings[module_id]
        if module.disagreements:
            mw.append(f"{module.disagreements} elements have a Module attribute that "
                      "disagrees with their subgroup; the subgroup was used")
        unknown = _unknown_prefixes(module)
        if unknown:
            mw.append(f"unknown part prefixes reported as other: {', '.join(unknown)}")
        if frame is None:
            mw.append("no bottom floor found: no frame, no objects")
        elif frame.plan_area_ratio < cv.MIN_PLAN_AREA_RATIO:
            mw.append(f"bottom floor fills {frame.plan_area_ratio:.0%} of its enclosing "
                      "rectangle: not rectangular, objects omitted")
        else:
            frames[module_id] = frame
            floors[module_id] = floor

    detailed = {m for m in modules if detail_all or m in requested}
    walls: Dict[str, List[_Wall]] = {}
    for module_id, frame in frames.items():
        module = modules[module_id]
        for object_id, elements in module.parts.items():
            if module.part_refs[object_id].object_type == "wall":
                wall = _make_wall(object_id, elements, frame, module_id in detailed)
                if wall is not None:
                    walls.setdefault(module_id, []).append(wall)
    geo: Dict[str, List[_GeoGroup]] = {}
    geo_walls: Dict[str, List[_Wall]] = {}
    for module_id in sorted(detailed & set(frames), key=module_number):
        geo[module_id] = _geo_groups(modules[module_id], frames[module_id], floors[module_id])
        found = [g.wall for g in geo[module_id] if g.wall is not None]
        if found:
            geo_walls[module_id] = found

    # Subgroup walls first, so a summary counts the same openings as a detail;
    # then the fallback walls of detailed modules take what is left.
    attached, orphans = _attach_openings(joinery, walls, frames)
    geo_attached, orphans = _attach_openings(orphans, geo_walls, frames)
    attached.update(geo_attached)

    orphans_by_module: Dict[str, List[ObjectSnapshot]] = {}
    for j in orphans:
        home, _part, _d = element_module(j)
        if home is not None and home in frames and j.vertices:
            orphans_by_module.setdefault(home, []).append(j)
        else:
            unattached.append(j.element_id)

    entries = []
    for module_id in sorted(modules, key=module_number):
        module = modules[module_id]
        frame = frames.get(module_id)
        is_detailed = module_id in detailed
        entry: Dict[str, Any] = {"module_id": module_id,
                                 "grouping_source": _grouping_source(module),
                                 "frame": None, "counts": {},
                                 "warnings": module_warnings[module_id]}
        if frame is not None:
            entry["frame"] = _frame_dict(frame, _module_height(module, frame)
                                         if is_detailed else None)
        objects, counts = _module_objects(module, frame, walls.get(module_id, []),
                                          geo.get(module_id, []), attached,
                                          orphans_by_module.get(module_id, []),
                                          {e.element_id for e in floors.get(module_id, [])},
                                          is_detailed, element_detail,
                                          module_warnings[module_id])
        entry["counts"] = counts
        if is_detailed:
            entry["objects"] = objects
        else:
            entry["unclassified_element_count"] = len(module.loose)
            # Joinery of this module in no subgroup wall: the detail places it
            # in a fallback wall or reports it as other.
            entry["unplaced_joinery_ids"] = sorted(
                j.element_id for j in orphans_by_module.get(module_id, []))
        entries.append(entry)

    return {
        "status": "ok",
        "schema": SCHEMA,
        "source": dict(source or {}),
        "modules": entries,
        "unattached_element_ids": sorted(unattached),
        "processing_element_count": processing,
        "warnings": warnings,
    }


def _grouping_source(module: _Module) -> Optional[str]:
    """How the module's elements are grouped, the same in summary and detail."""
    if module.parts and module.loose:
        return "subgroup+geometry"
    if module.parts:
        return "subgroup"
    return "geometry" if module.loose else None


def _module_objects(module: _Module, frame: Optional[ModuleFrame], walls: Sequence[_Wall],
                    geo: Sequence[_GeoGroup],
                    attached: Dict[str, List[Tuple[ObjectSnapshot, LocalBox]]],
                    orphans: Sequence[ObjectSnapshot], bottom_ids: Set[int],
                    detailed: bool, element_detail: str,
                    warnings: List[str]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """Objects of one module (detail only) and its counts.

    The summary counts subgroup objects and the openings of subgroup walls; the
    detail adds the fallback objects, their openings, and stray joinery as
    "other". Objects with no readable geometry are omitted with a module warning.
    """
    counts: Counter = Counter(ref.object_type for ref in module.part_refs.values())
    counts["opening"] = sum(len(attached.get(w.object_id, [])) for w in walls)
    counts.setdefault("other", 0)
    objects: List[Dict[str, Any]] = []
    if frame is None or not detailed:
        return objects, dict(counts)
    module_frame = frame

    def add(object_id: str, record: Optional[Dict[str, Any]],
            elements: Sequence[ObjectSnapshot]) -> bool:
        if record is None:
            warnings.append(f"{object_id}: no readable geometry, omitted")
            return False
        if element_detail != "none":
            record["elements"] = _element_details(elements, module_frame, element_detail)
        objects.append(record)
        return True

    wall_by_id = {w.object_id: w for w in walls}
    for object_id in sorted(module.parts, key=_part_sort_key):
        elements = module.parts[object_id]
        ref = module.part_refs[object_id]
        record: Optional[Dict[str, Any]]
        if ref.object_type == "wall":
            wall = wall_by_id.get(object_id)
            record = None
            if wall is not None:
                wall.record["openings"] = _opening_records(wall, attached.get(object_id, []))
                record = wall.record
        elif ref.object_type == "slab":
            is_bottom = any(e.element_id in bottom_ids for e in elements)
            record = _make_box_object(object_id, "slab", elements, frame, ref.prefix,
                                      _slab_level(elements, is_bottom))
        else:
            record = _make_box_object(object_id, ref.object_type, elements, frame, ref.prefix)
        if record is not None and not _is_known_prefix(ref.prefix):
            record["warnings"].append(f"unknown part prefix '{ref.prefix}': reported as other")
        add(object_id, record, elements)

    for group in geo:
        made: Optional[Dict[str, Any]]
        if group.kind == "wall":
            made = None
            if group.wall is not None:
                items = attached.get(group.object_id, [])
                made = group.wall.record
                made["openings"] = _opening_records(group.wall, items)
                made["warnings"].append(f"grouped by geometry ({group.label})")
                counts["opening"] += len(items)
        elif group.kind == "slab":
            made = _make_box_object(group.object_id, "slab", group.elements, frame, None,
                                    group.label)
        else:
            made = _make_box_object(group.object_id, "other", group.elements, frame, None)
        if add(group.object_id, made, group.elements):
            counts[group.kind] += 1

    for j in orphans:
        object_id = f"{module.module_id}-joinery{j.element_id}"
        stray = _make_box_object(object_id, "other", [j], frame, None)
        if stray is not None:
            stray["warnings"].append(f"joinery '{j.name.strip()}' lies in no wall")
            counts["other"] += 1
        add(object_id, stray, [j])
    return objects, dict(counts)
