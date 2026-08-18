"""Tests for the Vestack bridge adapter.

The adapter is the only Vestack code that touches Cadwork. Here the Cadwork API
modules are replaced by fakes in sys.modules, which works because the adapter
imports them per call, by their bare names, exactly as the other handlers do.
"""
import sys
import types
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

from vestack.bridge_handler import (
    collect_snapshots,
    element_bbox,
    handle_get_module_inventory,
    resolve_attribute_numbers,
)

BBox = Tuple[float, float, float, float, float, float]

FLOOR: BBox = (0.0, 0.0, 0.0, 6500.0, 3200.0, 220.0)
CEILING: BBox = (0.0, 0.0, 2950.0, 6500.0, 3200.0, 3170.0)
WALL: BBox = (0.0, 0.0, 220.0, 6500.0, 200.0, 2950.0)

# The Vestack template as seen in Cadwork: 1 Batiment, 2 Niveau, 3 Module.
ATTRIBUTE_NAMES = {1: "Bâtiment", 2: "Niveau", 3: "Module", 4: "ID Material."}


class Point:
    """Stands in for cadwork.point_3d, which exposes x/y/z."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x, self.y, self.z = x, y, z


def corners(bbox: BBox, as_point: bool = True) -> List[Any]:
    x0, y0, z0, x1, y1, z1 = bbox
    out = []
    for x in (x0, x1):
        for y in (y0, y1):
            for z in (z0, z1):
                out.append(Point(x, y, z) if as_point else [x, y, z])
    return out


def module(**functions: Any) -> types.ModuleType:
    fake = types.ModuleType("fake")
    for name, function in functions.items():
        setattr(fake, name, function)
    return fake


def fake_model(boxes: Dict[int, BBox], attributes: Dict[int, Dict[int, str]],
               *, vertices_fail: Optional[int] = None) -> Dict[str, types.ModuleType]:
    """Fake element / geometry / attribute controllers for a small model."""

    def get_element_vertices(element_id: int) -> List[Any]:
        if element_id == vertices_fail:
            raise RuntimeError("no geometry for this element")
        return corners(boxes[element_id])

    def get_volume(element_id: int) -> float:
        x0, y0, z0, x1, y1, z1 = boxes[element_id]
        return (x1 - x0) * (y1 - y0) * (z1 - z0)

    return {
        "element_controller": module(
            get_all_identifiable_element_ids=lambda: sorted(boxes),
            get_active_identifiable_element_ids=lambda: sorted(boxes)[:1],
        ),
        "geometry_controller": module(
            get_element_vertices=get_element_vertices,
            get_volume=get_volume,
        ),
        "attribute_controller": module(
            get_user_attribute_name=lambda n: ATTRIBUTE_NAMES.get(n, ""),
            get_user_attribute=lambda eid, n: attributes.get(eid, {}).get(n, ""),
            get_name=lambda eid: "",
            get_group=lambda eid: "",
            get_subgroup=lambda eid: "",
        ),
    }


ONE_MODULE = {1: FLOOR, 2: CEILING, 3: WALL}
ONE_MODULE_ATTRS = {
    eid: {1: "Maisons 25-26", 2: "RDC", 3: "M139"} for eid in ONE_MODULE
}


class ResolveAttributeNumbers(unittest.TestCase):
    def test_finds_the_module_attribute_by_its_name(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            self.assertEqual(resolve_attribute_numbers()["module"], 3)

    def test_matching_ignores_accents_and_case(self) -> None:
        # The Cadwork attribute is named "Batiment" with a circumflex.
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            self.assertEqual(resolve_attribute_numbers()["building"], 1)

    def test_finds_the_level_attribute(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            self.assertEqual(resolve_attribute_numbers()["level"], 2)

    def test_an_unrelated_attribute_is_not_claimed(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            self.assertNotIn(4, resolve_attribute_numbers().values())

    def test_reports_nothing_when_no_attribute_carries_a_known_name(self) -> None:
        model = fake_model(ONE_MODULE, ONE_MODULE_ATTRS)
        model["attribute_controller"] = module(get_user_attribute_name=lambda n: "")
        with patch.dict(sys.modules, model):
            self.assertEqual(resolve_attribute_numbers(), {})


class ElementBoundingBox(unittest.TestCase):
    def test_is_built_from_the_element_vertices(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            self.assertEqual(element_bbox(1), FLOOR)

    def test_accepts_vertices_given_as_plain_sequences(self) -> None:
        model = fake_model(ONE_MODULE, ONE_MODULE_ATTRS)
        model["geometry_controller"] = module(
            get_element_vertices=lambda eid: corners(FLOOR, as_point=False),
            get_volume=lambda eid: 0.0,
        )
        with patch.dict(sys.modules, model):
            self.assertEqual(element_bbox(1), FLOOR)


class CollectSnapshots(unittest.TestCase):
    def test_carries_the_module_building_and_level_attributes(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            snapshots, _skipped = collect_snapshots([1], {"module": 3, "building": 1, "level": 2})
        self.assertEqual(snapshots[0].user_attributes[3], "M139")
        self.assertEqual(snapshots[0].building, "Maisons 25-26")
        self.assertEqual(snapshots[0].level, "RDC")

    def test_records_the_volume_so_rotated_floors_can_be_detected(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            snapshots, _skipped = collect_snapshots([1], {})
        self.assertEqual(snapshots[0].volume_mm3, 6500.0 * 3200.0 * 220.0)

    def test_an_element_without_readable_geometry_is_skipped(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS, vertices_fail=2)):
            snapshots, skipped = collect_snapshots([1, 2, 3], {"module": 3})
        self.assertEqual([s.element_id for s in snapshots], [1, 3])
        self.assertEqual(skipped, [2])


class HandleGetModuleInventory(unittest.TestCase):
    def test_reports_the_module_found_in_the_model(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            response = handle_get_module_inventory({})
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["module_count"], 1)
        self.assertEqual(response["modules"][0]["module_id"], "M139")

    def test_derives_the_dimensions_from_the_bottom_floor(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            response = handle_get_module_inventory({})
        dimensions = response["modules"][0]["dimensions_mm"]
        self.assertEqual((dimensions["length"], dimensions["width"]), (6500.0, 3200.0))

    def test_reports_the_user_attribute_it_read_the_id_from(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            response = handle_get_module_inventory({})
        self.assertEqual(response["id_source"], "user_attribute_3")

    def test_reports_the_building_and_level(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            response = handle_get_module_inventory({})
        self.assertEqual(response["modules"][0]["building"], "Maisons 25-26")
        self.assertEqual(response["modules"][0]["level"], "RDC")

    def test_an_explicit_element_id_list_limits_the_scan(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS)):
            response = handle_get_module_inventory({"element_ids": [1]})
        self.assertEqual(response["scanned_element_count"], 1)

    def test_skipped_elements_are_reported(self) -> None:
        with patch.dict(sys.modules, fake_model(ONE_MODULE, ONE_MODULE_ATTRS, vertices_fail=2)):
            response = handle_get_module_inventory({})
        self.assertEqual(response["skipped_element_ids"], [2])

    def test_a_cadwork_failure_becomes_an_error_response(self) -> None:
        broken = fake_model(ONE_MODULE, ONE_MODULE_ATTRS)
        broken["element_controller"] = module()  # no id-listing function at all
        with patch.dict(sys.modules, broken):
            response = handle_get_module_inventory({})
        self.assertEqual(response["status"], "error")


if __name__ == "__main__":
    unittest.main()
