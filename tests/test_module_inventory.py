"""Tests for the Vestack module inventory domain logic.

These run without Cadwork: vestack.module_inventory is pure and takes snapshots.
"""
import unittest
from typing import Any, Dict, List, Optional

from vestack.module_inventory import (
    BBox,
    ElementSnapshot,
    build_inventory,
    detect_id_source,
)

# One module, in millimetres: 6500 x 3200 footprint, 220 mm slabs, 200 mm walls.
FLOOR = (0.0, 0.0, 0.0, 6500.0, 3200.0, 220.0)
CEILING = (0.0, 0.0, 2950.0, 6500.0, 3200.0, 3170.0)
WALL_MINUS_Y = (0.0, 0.0, 220.0, 6500.0, 200.0, 2950.0)
WALL_PLUS_Y = (0.0, 3000.0, 220.0, 6500.0, 3200.0, 2950.0)
WALL_MINUS_X = (0.0, 0.0, 220.0, 200.0, 3200.0, 2950.0)
WALL_PLUS_X = (6300.0, 0.0, 220.0, 6500.0, 3200.0, 2950.0)


def snap(element_id: int, bbox: BBox, *, subgroup: str = "", group: str = "",
         name: str = "", volume_mm3: Optional[float] = None,
         user_attributes: Optional[Dict[int, str]] = None,
         building: str = "", level: str = "") -> ElementSnapshot:
    """Build one snapshot, defaulting the volume to the bounding box volume."""
    if volume_mm3 is None:
        volume_mm3 = (bbox[3] - bbox[0]) * (bbox[4] - bbox[1]) * (bbox[5] - bbox[2])
    return ElementSnapshot(
        element_id=element_id,
        bbox=bbox,
        name=name,
        group=group,
        subgroup=subgroup,
        volume_mm3=volume_mm3,
        user_attributes=dict(user_attributes or {}),
        building=building,
        level=level,
    )


def closed_module(module_id: str = "M001", first_id: int = 1,
                  **field: Any) -> List[ElementSnapshot]:
    """Bottom floor + top floor + four walls, all carrying the module id."""
    boxes = [FLOOR, CEILING, WALL_MINUS_Y, WALL_PLUS_Y, WALL_MINUS_X, WALL_PLUS_X]
    key = field or {"subgroup": module_id}
    return [snap(first_id + i, b, **key) for i, b in enumerate(boxes)]


def only(inventory: Dict[str, Any]) -> Dict[str, Any]:
    """The single module of a one-module inventory."""
    modules: List[Dict[str, Any]] = inventory["modules"]
    assert len(modules) == 1, f"expected 1 module, got {len(modules)}"
    return modules[0]


class DetectIdSource(unittest.TestCase):
    def test_detects_module_id_in_subgroup(self) -> None:
        self.assertEqual(detect_id_source(closed_module(subgroup="M001")), "subgroup")

    def test_detects_module_id_in_group(self) -> None:
        self.assertEqual(detect_id_source(closed_module(group="M001")), "group")

    def test_detects_module_id_in_name(self) -> None:
        self.assertEqual(detect_id_source(closed_module(name="M001")), "name")

    def test_returns_none_when_no_field_holds_a_module_id(self) -> None:
        self.assertIsNone(detect_id_source(closed_module(group="Etage 1")))

    def test_detects_module_id_in_a_user_attribute(self) -> None:
        snaps = closed_module(user_attributes={3: "M139"})
        self.assertEqual(detect_id_source(snaps), "user_attribute_3")

    def test_a_user_attribute_holding_a_level_is_not_taken_for_the_module_id(self) -> None:
        snaps = closed_module(user_attributes={2: "RDC", 3: "M139"})
        self.assertEqual(detect_id_source(snaps), "user_attribute_3")

    def test_prefers_the_field_matching_the_most_elements(self) -> None:
        # Every element carries the id in its subgroup; only one also has it in its name.
        snaps = closed_module(subgroup="M001")
        snaps[0] = snap(snaps[0].element_id, FLOOR, subgroup="M001", name="M001")
        self.assertEqual(detect_id_source(snaps), "subgroup")


class ModuleDimensions(unittest.TestCase):
    def test_dimensions_come_from_the_bottom_floor(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertEqual(module["dimensions_mm"]["length"], 6500.0)
        self.assertEqual(module["dimensions_mm"]["width"], 3200.0)

    def test_floor_thickness_is_the_bottom_floor_depth(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertEqual(module["bottom_floor"]["thickness_mm"], 220.0)

    def test_height_spans_the_whole_module_envelope(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertEqual(module["dimensions_mm"]["height"], 3170.0)

    def test_footprint_area_is_reported_in_square_metres(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertAlmostEqual(module["footprint_area_m2"], 20.8, places=2)

    def test_origin_is_the_bottom_floor_minimum_corner(self) -> None:
        shifted: BBox = (12000.0, 0.0, 0.0, 18500.0, 3200.0, 220.0)
        module = only(build_inventory([snap(1, shifted, subgroup="M007")]))
        self.assertEqual(module["origin_mm"], [12000.0, 0.0, 0.0])

    def test_module_id_and_source_are_reported(self) -> None:
        inventory = build_inventory(closed_module("M042"))
        self.assertEqual(inventory["id_source"], "subgroup")
        self.assertEqual(only(inventory)["module_id"], "M042")


class ElementRoles(unittest.TestCase):
    def test_top_floor_is_detected_when_present(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertTrue(module["has_top_floor"])

    def test_top_floor_is_absent_when_the_module_is_open_on_top(self) -> None:
        snaps = [s for s in closed_module() if s.bbox != CEILING]
        module = only(build_inventory(snaps))
        self.assertFalse(module["has_top_floor"])
        self.assertIsNone(module["top_floor"])

    def test_walls_are_counted(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertEqual(module["walls"]["count"], 4)

    def test_element_count_covers_every_element_of_the_module(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertEqual(module["element_count"], 6)

    def test_a_beam_inside_the_module_is_classified_as_other(self) -> None:
        beam = (500.0, 500.0, 300.0, 4000.0, 620.0, 420.0)
        snaps = closed_module() + [snap(99, beam, subgroup="M001")]
        module = only(build_inventory(snaps))
        self.assertEqual(module["other_count"], 1)
        self.assertEqual(module["walls"]["count"], 4)


class OpenModules(unittest.TestCase):
    def test_a_closed_module_has_no_open_side(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertEqual(module["walls"]["open_sides"], [])

    def test_a_missing_wall_is_reported_as_an_open_side(self) -> None:
        snaps = [s for s in closed_module() if s.bbox != WALL_PLUS_Y]
        module = only(build_inventory(snaps))
        self.assertEqual(module["walls"]["open_sides"], ["+y"])

    def test_a_module_open_on_two_sides(self) -> None:
        dropped = (WALL_PLUS_Y, WALL_MINUS_X)
        snaps = [s for s in closed_module() if s.bbox not in dropped]
        module = only(build_inventory(snaps))
        self.assertEqual(module["walls"]["open_sides"], ["-x", "+y"])

    def test_a_short_wall_does_not_close_a_side(self) -> None:
        # A 1 m stub along -y cannot count as closing a 6.5 m side.
        stub = (0.0, 0.0, 220.0, 1000.0, 200.0, 2950.0)
        snaps = [s for s in closed_module() if s.bbox != WALL_MINUS_Y]
        snaps.append(snap(50, stub, subgroup="M001"))
        module = only(build_inventory(snaps))
        self.assertEqual(module["walls"]["open_sides"], ["-y"])


class SeveralModules(unittest.TestCase):
    def test_modules_are_sorted_by_id(self) -> None:
        snaps = closed_module("M002", first_id=1) + closed_module("M001", first_id=100)
        inventory = build_inventory(snaps)
        self.assertEqual([m["module_id"] for m in inventory["modules"]], ["M001", "M002"])

    def test_module_count_and_total_footprint_are_reported(self) -> None:
        snaps = closed_module("M001", first_id=1) + closed_module("M002", first_id=100)
        inventory = build_inventory(snaps)
        self.assertEqual(inventory["module_count"], 2)
        self.assertAlmostEqual(inventory["totals"]["footprint_area_m2"], 41.6, places=2)


class Warnings(unittest.TestCase):
    def test_a_module_without_a_bottom_floor_is_flagged(self) -> None:
        snaps = [s for s in closed_module() if s.bbox not in (FLOOR, CEILING)]
        module = only(build_inventory(snaps))
        self.assertIsNone(module["dimensions_mm"])
        self.assertTrue(any("no bottom floor" in w for w in module["warnings"]))

    def test_elements_without_a_module_id_are_counted_as_unassigned(self) -> None:
        snaps = closed_module() + [snap(500, FLOOR, subgroup="Divers")]
        inventory = build_inventory(snaps)
        self.assertEqual(inventory["unassigned_element_count"], 1)

    def test_a_floor_whose_plan_area_belies_its_bounding_box_is_flagged(self) -> None:
        # A slab rotated in plan: real plan area 2000x2000, bounding box 5000x5000.
        rotated = (0.0, 0.0, 0.0, 5000.0, 5000.0, 220.0)
        snaps = [snap(1, rotated, subgroup="M001", volume_mm3=220.0 * 2000.0 * 2000.0)]
        module = only(build_inventory(snaps))
        self.assertTrue(any("plan area" in w for w in module["warnings"]))

    def test_a_rectangular_floor_is_not_flagged(self) -> None:
        module = only(build_inventory(closed_module()))
        self.assertEqual(module["warnings"], [])


class BuildingContext(unittest.TestCase):
    """Attributes 1 and 2 of the Vestack template: "Batiment" and "Niveau"."""

    def test_building_and_level_are_reported_per_module(self) -> None:
        snaps = closed_module(user_attributes={3: "M139"})
        snaps = [snap(s.element_id, s.bbox, user_attributes=s.user_attributes,
                      building="Maisons 25-26", level="RDC") for s in snaps]
        module = only(build_inventory(snaps))
        self.assertEqual(module["building"], "Maisons 25-26")
        self.assertEqual(module["level"], "RDC")

    def test_a_module_spread_over_two_levels_is_flagged(self) -> None:
        snaps = [snap(1, FLOOR, user_attributes={3: "M139"}, level="RDC"),
                 snap(2, CEILING, user_attributes={3: "M139"}, level="R+1")]
        module = only(build_inventory(snaps))
        self.assertTrue(any("level" in w for w in module["warnings"]))


class ExplicitIdSource(unittest.TestCase):
    def test_an_explicit_id_source_overrides_detection(self) -> None:
        snaps = [snap(1, FLOOR, subgroup="M001", group="M999")]
        inventory = build_inventory(snaps, id_source="group")
        self.assertEqual(inventory["id_source"], "group")
        self.assertEqual(only(inventory)["module_id"], "M999")

    def test_an_empty_model_yields_an_empty_inventory(self) -> None:
        inventory = build_inventory([])
        self.assertEqual(inventory["module_count"], 0)
        self.assertEqual(inventory["modules"], [])


if __name__ == "__main__":
    unittest.main()
