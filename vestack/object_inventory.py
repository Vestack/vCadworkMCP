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

    The subgroup wins over the Module attribute, then come group and name.
    """
    part = parse_part(snapshot.subgroup)
    from_subgroup = (part.module_id if part and part.module_id
                     else parse_module_id(snapshot.subgroup))
    from_attribute = parse_module_id(snapshot.module_attribute)
    module = (from_subgroup or from_attribute or parse_module_id(snapshot.group)
              or parse_module_id(snapshot.name))
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


def geometry_needed(snapshots: Sequence[ObjectSnapshot],
                    module_ids: Optional[Collection[str]] = None,
                    detail_all: bool = False) -> Set[int]:
    """Ids of the elements whose vertices the inventory needs.

    Always: joinery, wall bodies (all wall elements when a wall has no single
    body), slab parts (to find the bottom floor), and every element of a module
    with no slab part. In detailed modules: every element.
    """
    requested = {parse_module_id(m) or m for m in (module_ids or [])}
    modules, joinery, _unattached, _processing = _partition(snapshots)
    needed: Set[int] = {s.element_id for s in joinery}
    for module in modules.values():
        everything = detail_all or module.module_id in requested
        has_slab_part = any(r.object_type == "slab" for r in module.part_refs.values())
        for object_id, elements in module.parts.items():
            object_type = module.part_refs[object_id].object_type
            if everything or not has_slab_part or object_type == "slab":
                needed.update(e.element_id for e in elements)
            elif object_type == "wall":
                bodies = _wall_bodies(elements)
                needed.update(e.element_id for e in (bodies if len(bodies) == 1 else elements))
        if everything or not has_slab_part:
            needed.update(e.element_id for e in module.loose)
    return needed


# --- frame -----------------------------------------------------------------

def _with_vertices(elements: Sequence[ObjectSnapshot]) -> List[ObjectSnapshot]:
    return [e for e in elements if e.vertices]


def _bottom_floor(module: _Module) -> List[ObjectSnapshot]:
    """Elements making the module's bottom floor, possibly none."""
    slab_parts = {oid: _with_vertices(els) for oid, els in module.parts.items()
                  if module.part_refs[oid].object_type == "slab"}
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
    lowest = min(_model_bbox(e.vertices)[2] for e in candidates)
    return [e for e in candidates
            if _model_bbox(e.vertices)[2] < lowest + cv.TOP_FLOOR_MIN_CLEARANCE_MM]


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


def _wall_geometry(box: LocalBox, frame: ModuleFrame) -> Tuple[bool, Point3, Point3, float, Optional[str]]:
    sx, sy, _sz = box.size
    along_x = sx >= sy
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
               check_union: bool) -> Optional[_Wall]:
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
    along_x, start, end, thickness, side = _wall_geometry(body, frame)
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


def _fallback_groups(loose: Sequence[ObjectSnapshot], frame: ModuleFrame
                     ) -> List[Tuple[str, str, List[ObjectSnapshot]]]:
    """(kind, label, elements) groups for elements outside any part subgroup."""
    slabs: Dict[str, List[ObjectSnapshot]] = {}
    sides: Dict[str, List[ObjectSnapshot]] = {}
    clusters: List[Tuple[bool, float, List[ObjectSnapshot]]] = []
    others: List[ObjectSnapshot] = []
    for e in _with_vertices(loose):
        box = frame.box_of(e.vertices)
        kind = classify(box.lo + box.hi)
        if kind == "slab":
            level = "bottom" if box.lo[2] < cv.TOP_FLOOR_MIN_CLEARANCE_MM else "top"
            slabs.setdefault(level, []).append(e)
            continue
        side = _band_side(box, frame)
        if side is not None:
            sides.setdefault(side, []).append(e)
        elif kind == "wall":
            along_x = box.size[0] >= box.size[1]
            plane = box.centre[1] if along_x else box.centre[0]
            for c_axis, c_plane, members in clusters:
                if c_axis == along_x and abs(c_plane - plane) <= cv.INTERIOR_WALL_PLANE_TOLERANCE_MM:
                    members.append(e)
                    break
            else:
                clusters.append((along_x, plane, [e]))
        else:
            others.append(e)
    groups: List[Tuple[str, str, List[ObjectSnapshot]]] = []
    groups += [("slab", level, slabs[level]) for level in ("bottom", "top") if level in slabs]
    groups += [("wall", side, sides[side]) for side in SIDES if side in sides]
    groups += [("wall", "interior", members) for _a, _p, members in clusters]
    if others:
        groups.append(("other", "", others))
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
    bottoms: Dict[str, Set[int]] = {}
    module_warnings: Dict[str, List[str]] = {m: [] for m in modules}
    for module_id, module in modules.items():
        floor = _bottom_floor(module)
        frame = frame_from_floor([v for e in floor for v in e.vertices]) if floor else None
        mw = module_warnings[module_id]
        if module.disagreements:
            mw.append(f"{module.disagreements} elements have a Module attribute that "
                      "disagrees with their subgroup; the subgroup was used")
        if frame is None:
            mw.append("no bottom floor found: no frame, no objects")
        elif frame.plan_area_ratio < cv.MIN_PLAN_AREA_RATIO:
            mw.append(f"bottom floor fills {frame.plan_area_ratio:.0%} of its enclosing "
                      "rectangle: not rectangular, objects omitted")
        else:
            frames[module_id] = frame
            bottoms[module_id] = {e.element_id for e in floor}

    detailed = {m for m in modules if detail_all or m in requested}
    walls: Dict[str, List[_Wall]] = {}
    for module_id, frame in frames.items():
        module = modules[module_id]
        for object_id, elements in module.parts.items():
            if module.part_refs[object_id].object_type == "wall":
                wall = _make_wall(object_id, elements, frame, module_id in detailed)
                if wall is not None:
                    walls.setdefault(module_id, []).append(wall)
    attached, orphans = _attach_openings(joinery, walls, frames)

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
        entry: Dict[str, Any] = {"module_id": module_id, "grouping_source": None,
                                 "frame": None, "counts": {}, "warnings": module_warnings[module_id]}
        if frame is not None:
            heights = [v[2] for els in module.parts.values() for e in els for v in e.vertices]
            heights += [v[2] for e in module.loose for v in e.vertices]
            entry["frame"] = _frame_dict(frame, max(heights) - frame.origin[2] if heights else None)
        objects = _module_objects(module, frame, walls.get(module_id, []), attached,
                                  orphans_by_module.get(module_id, []),
                                  bottoms.get(module_id, set()),
                                  module_id in detailed, element_detail)
        entry["grouping_source"] = objects["grouping_source"]
        entry["counts"] = objects["counts"]
        if module_id in detailed:
            entry["objects"] = objects["objects"] if frame is not None else []
        else:
            entry["unclassified_element_count"] = len(module.loose)
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


def _module_objects(module: _Module, frame: Optional[ModuleFrame], walls: Sequence[_Wall],
                    attached: Dict[str, List[Tuple[ObjectSnapshot, LocalBox]]],
                    orphans: Sequence[ObjectSnapshot], bottom_ids: Set[int],
                    detailed: bool, element_detail: str) -> Dict[str, Any]:
    """Objects of one module (detail), with counts and grouping source."""
    counts: Counter = Counter()
    for object_id, ref in module.part_refs.items():
        counts[ref.object_type] += 1
    counts["opening"] = sum(len(attached.get(w.object_id, [])) for w in walls)
    counts["other"] += len(orphans)
    source: Optional[str] = ("subgroup" if module.parts
                             else "geometry" if module.loose else None)
    objects: List[Dict[str, Any]] = []
    if frame is None or not detailed:
        return {"objects": objects, "counts": dict(counts), "grouping_source": source}

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
        if record is None:
            continue
        if element_detail != "none":
            record["elements"] = _element_details(elements, frame, element_detail)
        objects.append(record)

    fallback = _fallback_groups(module.loose, frame)
    if fallback:
        source = "subgroup+geometry" if module.parts else "geometry"
    for n, (kind, label, elements) in enumerate(fallback, start=1):
        object_id = f"{module.module_id}-geo{n}"
        made: Optional[Dict[str, Any]]
        if kind == "wall":
            geo_wall = _make_wall(object_id, elements, frame, check_union=False)
            made = geo_wall.record if geo_wall else None
            if made is not None:
                made["warnings"].append(f"grouped by geometry ({label})")
        elif kind == "slab":
            made = _make_box_object(object_id, "slab", elements, frame, None, label)
        else:
            made = _make_box_object(object_id, "other", elements, frame, None)
        if made is None:
            continue
        if element_detail != "none":
            made["elements"] = _element_details(elements, frame, element_detail)
        objects.append(made)
        counts[kind] += 1

    for j in orphans:
        stray = _make_box_object(f"{module.module_id}-joinery{j.element_id}", "other",
                                 [j], frame, None)
        if stray is not None:
            stray["warnings"].append(f"joinery '{j.name.strip()}' lies in no wall")
            objects.append(stray)
    return {"objects": objects, "counts": dict(counts), "grouping_source": source}
