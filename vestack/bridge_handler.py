"""Bridge adapter for the Vestack module and object inventories.

The only Vestack code that talks to Cadwork. It reads what the model holds, turns
it into ElementSnapshot or ObjectSnapshot values, and hands them to the pure
logic in module_inventory.py and object_inventory.py. Cadwork modules are imported inside the functions, by their
bare names, as every other bridge handler does: at module level they would make
this file unimportable outside Cadwork.

The dispatcher discovers `handle_get_module_inventory` and
`handle_get_object_inventory` through the usual `handle_<operation>` convention,
via bridge.dispatcher.EXTENSION_MODULES.
"""
import unicodedata
from datetime import datetime
from typing import Any, Callable, Collection, Dict, List, Optional, Sequence, Tuple

from . import conventions as cv
from .module_inventory import BBox, ElementSnapshot, build_inventory
from .object_inventory import ObjectSnapshot, build_object_inventory, geometry_needed

# Which Cadwork user attribute plays which role, matched on the attribute name.
ATTRIBUTE_ROLES: Dict[str, Tuple[str, ...]] = {
    "module": cv.MODULE_ATTRIBUTE_NAMES,
    "building": cv.BUILDING_ATTRIBUTE_NAMES,
    "level": cv.LEVEL_ATTRIBUTE_NAMES,
    "complex": cv.COMPLEX_ATTRIBUTE_NAMES,
}


def _plain(text: str) -> str:
    """Lowercase, accent-free form of a label, so "Bâtiment" matches "batiment"."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).strip().lower()


def _safe_str(read: Callable[[int], Any], element_id: int) -> str:
    """Read one optional string from Cadwork, treating any failure as absent."""
    try:
        value = read(element_id)
    except Exception:
        return ""
    return str(value) if value else ""


def resolve_attribute_numbers(
        scan_limit: int = cv.USER_ATTRIBUTE_SCAN_LIMIT) -> Dict[str, int]:
    """Find which user attribute numbers hold the module, building and level.

    Cadwork numbers user attributes per user profile, so the number is looked up
    from the attribute's name rather than hard-coded. Roles that no attribute
    claims are simply absent from the result.
    """
    import attribute_controller as ac

    found: Dict[str, int] = {}
    for number in range(1, scan_limit + 1):
        label = _plain(_safe_str(ac.get_user_attribute_name, number))
        if not label:
            continue
        for role, needles in ATTRIBUTE_ROLES.items():
            if role not in found and any(needle in label for needle in needles):
                found[role] = number
    return found


def _coordinates(vertex: Any) -> Tuple[float, float, float]:
    """Read one vertex, given either as cadwork.point_3d or as a sequence."""
    if hasattr(vertex, "x"):
        return (float(vertex.x), float(vertex.y), float(vertex.z))
    return (float(vertex[0]), float(vertex[1]), float(vertex[2]))


def element_bbox(element_id: int) -> Optional[BBox]:
    """Axis-aligned bounding box of one element, from its vertices.

    Cadwork's geometry_controller has no bounding-box getter, so the box is
    computed here. Being axis-aligned, it overstates an element rotated in plan;
    module_inventory flags floors where that happens.
    """
    import geometry_controller as gc

    points = [_coordinates(v) for v in (gc.get_element_vertices(element_id) or [])]
    if not points:
        return None
    xs, ys, zs = zip(*points)
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def collect_snapshots(element_ids: Sequence[int],
                      attribute_numbers: Dict[str, int]
                      ) -> Tuple[List[ElementSnapshot], List[int]]:
    """Read the model into snapshots.

    Returns the snapshots and the ids of elements whose geometry could not be
    read: containers and processing-only elements have no vertices.
    """
    import attribute_controller as ac
    import geometry_controller as gc

    module_number = attribute_numbers.get("module")
    building_number = attribute_numbers.get("building")
    level_number = attribute_numbers.get("level")

    snapshots: List[ElementSnapshot] = []
    skipped: List[int] = []

    for element_id in element_ids:
        try:
            bbox = element_bbox(element_id)
        except Exception:
            bbox = None
        if bbox is None:
            skipped.append(element_id)
            continue

        user_attributes: Dict[int, str] = {}
        if module_number is not None:
            try:
                user_attributes[module_number] = str(
                    ac.get_user_attribute(element_id, module_number) or "")
            except Exception:
                user_attributes[module_number] = ""

        try:
            volume: Optional[float] = float(gc.get_volume(element_id))
        except Exception:
            volume = None

        snapshots.append(ElementSnapshot(
            element_id=element_id,
            bbox=bbox,
            name=_safe_str(ac.get_name, element_id),
            group=_safe_str(ac.get_group, element_id),
            subgroup=_safe_str(ac.get_subgroup, element_id),
            volume_mm3=volume,
            user_attributes=user_attributes,
            building=(_safe_str(lambda eid: ac.get_user_attribute(eid, building_number),
                                element_id) if building_number else ""),
            level=(_safe_str(lambda eid: ac.get_user_attribute(eid, level_number),
                             element_id) if level_number else ""),
        ))

    return snapshots, skipped


def _element_ids_to_scan(args: Dict[str, Any]) -> List[int]:
    """Which elements the inventory covers: an explicit list, the selection, or all."""
    explicit = args.get("element_ids")
    if explicit:
        return [int(element_id) for element_id in explicit]

    import element_controller as ec

    if args.get("active_only"):
        return list(ec.get_active_identifiable_element_ids())
    return list(ec.get_all_identifiable_element_ids())


def handle_get_module_inventory(args: Dict[str, Any]) -> Dict[str, Any]:
    """List the Vestack modules of the model with their dimensions.

    Args (all optional):
        element_ids: restrict the scan to these elements.
        active_only: restrict the scan to the current selection.
        id_source: field holding the module id ("subgroup", "user_attribute_3",
            ...), when auto-detection should be bypassed.

    Reading geometry costs one vertex query per element, so scanning a whole
    building is slow; pass element_ids or active_only where possible.
    """
    try:
        element_ids = _element_ids_to_scan(args)
        attribute_numbers = resolve_attribute_numbers()
        snapshots, skipped = collect_snapshots(element_ids, attribute_numbers)

        inventory = build_inventory(snapshots, id_source=args.get("id_source"))
        inventory.update({
            "scanned_element_count": len(snapshots),
            "skipped_element_ids": skipped,
            "attribute_numbers": attribute_numbers,
        })
        return inventory
    except Exception as exc:
        return {
            "status": "error",
            "message": f"get_module_inventory failed: {type(exc).__name__}: {exc}",
        }


# --- object inventory ------------------------------------------------------

def read_object_attributes(element_ids: Sequence[int],
                           attribute_numbers: Dict[str, int]) -> List[ObjectSnapshot]:
    """First pass: names, groups, subgroups, Module and Complexe, no geometry.

    Cheap compared with vertices (about 1 ms per element on Cadwork 2026), so it
    runs over every scanned element to find the modules and their parts.
    """
    import attribute_controller as ac

    module_number = attribute_numbers.get("module")
    complex_number = attribute_numbers.get("complex")

    def user_attribute(number: Optional[int], element_id: int) -> str:
        if number is None:
            return ""
        return _safe_str(lambda eid: ac.get_user_attribute(eid, number), element_id)

    return [ObjectSnapshot(element_id=element_id,
                           name=_safe_str(ac.get_name, element_id),
                           group=_safe_str(ac.get_group, element_id),
                           subgroup=_safe_str(ac.get_subgroup, element_id),
                           module_attribute=user_attribute(module_number, element_id),
                           complex_code=user_attribute(complex_number, element_id))
            for element_id in element_ids]


def read_object_geometry(snapshots: Sequence[ObjectSnapshot], needed: Collection[int],
                         with_material: bool) -> List[int]:
    """Second pass: vertices (and material) of the elements that need them.

    Fills the snapshots in place. Returns the ids whose geometry could not be read.
    """
    import attribute_controller as ac
    import geometry_controller as gc

    skipped: List[int] = []
    for snapshot in snapshots:
        if snapshot.element_id not in needed:
            continue
        try:
            vertices = tuple(_coordinates(v) for v in
                             (gc.get_element_vertices(snapshot.element_id) or []))
        except Exception:
            vertices = ()
        if not vertices:
            skipped.append(snapshot.element_id)
            continue
        snapshot.vertices = vertices
        if with_material:
            snapshot.material = _safe_str(ac.get_element_material_name, snapshot.element_id)
    return skipped


def _source() -> Dict[str, Any]:
    """Provenance of the inventory: the open file and the extraction time."""
    try:
        import utility_controller as uc
        path = str(uc.get_3d_file_path() or "")
    except Exception:
        path = ""
    return {"file": path,
            "extracted_at": datetime.now().astimezone().isoformat(timespec="seconds")}


def handle_get_object_inventory(args: Dict[str, Any]) -> Dict[str, Any]:
    """Walls, slabs, roofs and openings per module, in each module's own frame.

    Args (all optional):
        element_ids / active_only: restrict the scan, as for get_module_inventory.
        module_ids: modules to detail; the others are summarised.
        detail_all: detail every module (the controller sets it for file export).
        element_detail: "none", "envelope" or "vertices", for detailed modules.

    Attributes are read for every scanned element, vertices only where the
    inventory needs them (see object_inventory.geometry_needed).
    """
    try:
        element_ids = _element_ids_to_scan(args)
        module_ids = [str(m) for m in (args.get("module_ids") or [])]
        detail_all = bool(args.get("detail_all"))
        element_detail = str(args.get("element_detail") or "none")

        attribute_numbers = resolve_attribute_numbers()
        snapshots = read_object_attributes(element_ids, attribute_numbers)
        needed = geometry_needed(snapshots, module_ids, detail_all)
        skipped = read_object_geometry(snapshots, needed,
                                       with_material=element_detail != "none")

        inventory = build_object_inventory(snapshots, module_ids, detail_all,
                                           element_detail, _source())
        inventory.update({
            "scanned_element_count": len(snapshots),
            "geometry_read_count": len(needed) - len(skipped),
            "skipped_element_ids": sorted(skipped),
            "attribute_numbers": attribute_numbers,
        })
        return inventory
    except ValueError as exc:
        return {"status": "error", "message": f"get_object_inventory: {exc}"}
    except Exception as exc:
        return {
            "status": "error",
            "message": f"get_object_inventory failed: {type(exc).__name__}: {exc}",
        }
