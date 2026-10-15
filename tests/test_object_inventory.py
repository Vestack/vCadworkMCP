"""Tests for the Vestack object inventory. Pure logic, no Cadwork."""
import dataclasses
import unittest
from typing import Any, Dict, List, Set

from tests.object_fixtures import box, element, module_m1
from vestack.object_inventory import (
    ObjectSnapshot,
    build_object_inventory,
    geometry_needed,
)


def module_entry(inventory: Dict[str, Any], module_id: str = "M1") -> Dict[str, Any]:
    return next(m for m in inventory["modules"] if m["module_id"] == module_id)


def objects_by_id(inventory: Dict[str, Any], module_id: str = "M1") -> Dict[str, Dict[str, Any]]:
    return {o["id"]: o for o in module_entry(inventory, module_id)["objects"]}


def detail(snapshots: List[ObjectSnapshot], **kw: Any) -> Dict[str, Any]:
    return build_object_inventory(snapshots, module_ids=["M1"], **kw)


def keep_vertices(snapshots: List[ObjectSnapshot], keep: Set[int]) -> List[ObjectSnapshot]:
    """The snapshots as the bridge delivers them: vertices read for `keep` only."""
    return [dataclasses.replace(s, vertices=s.vertices if s.element_id in keep else ())
            for s in snapshots]


class Summary(unittest.TestCase):
    def test_reports_the_schema_and_the_module(self) -> None:
        inventory = build_object_inventory(module_m1())
        self.assertEqual(inventory["schema"], "vestack.object_inventory/1")
        self.assertEqual([m["module_id"] for m in inventory["modules"]], ["M1"])

    def test_counts_objects_per_type_including_openings(self) -> None:
        counts = module_entry(build_object_inventory(module_m1()))["counts"]
        self.assertEqual(counts, {"slab": 1, "wall": 2, "roof": 1, "other": 1, "opening": 1})

    def test_the_summary_has_a_frame_but_no_objects(self) -> None:
        entry = module_entry(build_object_inventory(module_m1()))
        self.assertNotIn("objects", entry)
        frame = entry["frame"]
        self.assertEqual((frame["length"], frame["width"]), (6000, 2500))
        self.assertEqual(frame["origin_model"], [0, 0, 0])
        # The summary does not read every element's vertices: no height.
        self.assertIsNone(frame["height"])

    def test_the_summary_only_depends_on_the_vertices_it_asks_for(self) -> None:
        snaps = module_m1()
        full = module_entry(build_object_inventory(snaps))
        real = module_entry(build_object_inventory(keep_vertices(snaps, geometry_needed(snaps))))
        for key in ("counts", "warnings", "grouping_source", "unclassified_element_count"):
            self.assertEqual(real[key], full[key], key)
        self.assertEqual(real["frame"], full["frame"])
        self.assertIsNone(real["frame"]["height"])

    def test_the_detail_frame_has_the_module_height(self) -> None:
        snaps = module_m1()
        real = keep_vertices(snaps, geometry_needed(snaps, module_ids=["M1"]))
        self.assertEqual(module_entry(detail(real))["frame"]["height"], 3400)

    def test_a_mixed_module_reports_both_sources_in_the_summary(self) -> None:
        snaps = module_m1() + [element(80, box(2000, 1200, 220, 5000, 1300, 2865),
                                       name="cloison", subgroup="M1")]
        entry = module_entry(build_object_inventory(snaps))
        self.assertEqual(entry["grouping_source"], "subgroup+geometry")

    def test_processing_elements_are_counted_apart(self) -> None:
        self.assertEqual(build_object_inventory(module_m1())["processing_element_count"], 1)

    def test_modules_are_sorted_numerically(self) -> None:
        snaps = module_m1()
        snaps += [element(100 + s.element_id, list(s.vertices), name=s.name, group=s.group,
                          subgroup=s.subgroup.replace("M1-", "M10-"), shift=(0, 10000, 0))
                  for s in module_m1() if s.subgroup.startswith("M1-")]
        snaps += [element(200 + s.element_id, list(s.vertices), name=s.name, group=s.group,
                          subgroup=s.subgroup.replace("M1-", "M2-"), shift=(0, 20000, 0))
                  for s in module_m1() if s.subgroup.startswith("M1-")]
        ids = [m["module_id"] for m in build_object_inventory(snaps)["modules"]]
        self.assertEqual(ids, ["M1", "M2", "M10"])


class Walls(unittest.TestCase):
    def test_wall_axis_thickness_and_height_come_from_the_body(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W1"]
        self.assertEqual(wall["start"], [0, 106, 220])
        self.assertEqual(wall["end"], [6000, 106, 220])
        self.assertEqual((wall["thickness"], wall["height"]), (212, 2645))
        self.assertEqual(wall["side"], "-y")

    def test_wall_type_and_stud_section(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W1"]
        self.assertEqual((wall["wall_type"], wall["stud_section"]), ("MOB200", 200))

    def test_a_wall_along_y_on_the_far_edge(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W2"]
        self.assertEqual(wall["side"], "+x")
        self.assertEqual((wall["start"], wall["end"]), ([5928, 212, 220], [5928, 2288, 220]))
        self.assertEqual(wall["thickness"], 145)

    def test_the_wall_lists_all_its_elements(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W1"]
        self.assertEqual(wall["element_ids"], [10, 11, 12])

    def test_an_element_sticking_out_of_the_body_is_warned(self) -> None:
        snaps = module_m1() + [element(13, box(0, 212, 220, 600, 358, 2865), name="Joue",
                                       group="MOB", subgroup="M1-W1")]
        wall = objects_by_id(detail(snaps))["M1-W1"]
        self.assertTrue(any("146 mm" in w and "[13]" in w for w in wall["warnings"]),
                        wall["warnings"])

    def test_a_wall_without_body_uses_the_union_and_is_warned(self) -> None:
        snaps = [s for s in module_m1() if s.element_id != 10]
        wall = objects_by_id(detail(snaps))["M1-W1"]
        self.assertIsNone(wall["wall_type"])
        self.assertEqual(wall["start"], [0, 106, 220])
        self.assertTrue(any("0 wall body" in w for w in wall["warnings"]))

    def test_two_bodies_are_warned(self) -> None:
        snaps = module_m1() + [element(14, box(0, 0, 220, 6000, 212, 2865), name="MOB200",
                                       group="MOB", subgroup="M1-W1")]
        wall = objects_by_id(detail(snaps))["M1-W1"]
        self.assertTrue(any("2 wall body" in w for w in wall["warnings"]))


class RotatedModules(unittest.TestCase):
    def test_local_results_do_not_depend_on_the_module_placement(self) -> None:
        reference = objects_by_id(detail(module_m1()))
        for degrees, shift in ((90, (10000, 5000, 0)), (37, (500, -800, 300)), (-60, (0, 0, 0))):
            rotated = objects_by_id(detail(module_m1(degrees, shift)))
            for object_id in ("M1-W1", "M1-W2"):
                for key in ("start", "end", "thickness", "height", "side", "openings"):
                    self.assertEqual(rotated[object_id][key], reference[object_id][key],
                                     f"{object_id}.{key} at {degrees} degrees")

    def test_a_module_turned_beyond_90_degrees_is_seen_from_the_other_end(self) -> None:
        # The 180-degree tie-break keeps X within 90 degrees of the model's +X, so
        # a module placed at 217 degrees gets the frame of one placed at 37: its
        # -y wall is reported on +y. Claude reads that off x_axis_model.
        wall = objects_by_id(detail(module_m1(217, (0, 0, 0))))["M1-W1"]
        self.assertEqual(wall["side"], "+y")

    def test_the_frame_reports_its_axes_in_model_coordinates(self) -> None:
        frame = module_entry(build_object_inventory(module_m1(90, (10000, 5000, 0))))["frame"]
        self.assertEqual(frame["x_axis_model"], [0.0, 1.0, 0.0])
        self.assertEqual(frame["y_axis_model"], [-1.0, 0.0, 0.0])
        self.assertEqual(frame["origin_model"], [10000, 5000, 0])


class Slabs(unittest.TestCase):
    def test_the_bottom_floor_is_one_object_over_its_panels(self) -> None:
        slab = objects_by_id(detail(module_m1()))["M1-F1"]
        self.assertEqual(slab["level"], "bottom")
        self.assertEqual((slab["length"], slab["width"], slab["thickness"]), (6000, 2500, 220))
        self.assertEqual(slab["element_ids"], [1, 2])

    def test_roof_and_named_parts_keep_their_prefix(self) -> None:
        objects = objects_by_id(detail(module_m1()))
        self.assertEqual((objects["M1-TF0"]["type"], objects["M1-TF0"]["part"]), ("roof", "TF"))
        self.assertEqual((objects["M1-Poteaux"]["type"], objects["M1-Poteaux"]["part"]),
                         ("other", "Poteaux"))
        self.assertEqual(objects["M1-Poteaux"]["warnings"], [])

    def test_an_unknown_prefix_is_other_and_warned(self) -> None:
        snaps = module_m1() + [
            element(90, box(100, 100, 300, 200, 200, 400), subgroup="M1-Zz3"),
            element(91, box(300, 100, 300, 400, 200, 400), subgroup="M1-Qq"),
            element(92, box(500, 100, 300, 600, 200, 400), subgroup="M1-Zz4")]
        inventory = detail(snaps)
        record = objects_by_id(inventory)["M1-Zz3"]
        self.assertEqual(record["type"], "other")
        self.assertIn("unknown part prefix 'Zz': reported as other", record["warnings"])
        expected = "unknown part prefixes reported as other: Qq, Zz"
        self.assertIn(expected, module_entry(inventory)["warnings"])
        self.assertIn(expected, module_entry(build_object_inventory(snaps))["warnings"])
        self.assertFalse(any("unknown" in w for w in module_entry(detail(module_m1()))["warnings"]))


class Openings(unittest.TestCase):
    def test_joinery_without_subgroup_is_attached_to_its_wall(self) -> None:
        openings = objects_by_id(detail(module_m1()))["M1-W1"]["openings"]
        self.assertEqual(openings, [{"id": "M1-W1-O1", "name": "MEX type B", "offset": 1000,
                                     "sill": 90, "width": 1455, "height": 2315,
                                     "element_ids": [50]}])

    def test_each_joinery_is_attached_once(self) -> None:
        # Two modules whose walls overlap: the joinery fits both, lands in one.
        twin = [element(100 + s.element_id, list(s.vertices), name=s.name, group=s.group,
                        subgroup=s.subgroup.replace("M1-", "M2-"))
                for s in module_m1() if s.subgroup.startswith("M1-")]
        inventory = build_object_inventory(module_m1() + twin, detail_all=True)
        hosts = [o["id"] for m in inventory["modules"] for o in m["objects"]
                 for opening in o.get("openings", []) if 50 in opening["element_ids"]]
        self.assertEqual(hosts, ["M1-W1"])

    def test_joinery_in_no_wall_is_an_other_object_with_a_warning(self) -> None:
        stray = element(51, box(2000, 1000, 500, 2500, 1100, 1500), name="MEX type A",
                        module="M1")
        objects = objects_by_id(detail(module_m1() + [stray]))
        record = objects["M1-joinery51"]
        self.assertEqual(record["type"], "other")
        self.assertTrue(any("lies in no wall" in w for w in record["warnings"]))

    def test_joinery_with_no_module_and_no_wall_is_unattached(self) -> None:
        stray = element(52, box(90000, 0, 0, 90100, 100, 100), name="MEX type A")
        self.assertIn(52, build_object_inventory(module_m1() + [stray])["unattached_element_ids"])

    def geometry_module(self) -> List[ObjectSnapshot]:
        """Module M2 without subgroups, a -y wall holding two joinery items."""
        return [
            element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M2"),
            element(2, box(500, 0, 220, 545, 200, 2865), name="montant", module="M2"),
            element(3, box(5000, 0, 220, 5045, 200, 2865), name="montant", module="M2"),
            element(4, box(0, 0, 220, 6000, 15, 2865), name="OSB mur", module="M2"),
            element(50, box(1000, 0, 310, 2455, 200, 2625), name="MEX type B", module="M2"),
            element(51, box(3000, 0, 310, 4455, 200, 2625), name="MEX type B"),
        ]

    def test_joinery_is_attached_to_a_geometry_wall(self) -> None:
        inventory = build_object_inventory(self.geometry_module(), module_ids=["M2"])
        entry = module_entry(inventory, "M2")
        wall = next(o for o in entry["objects"] if o["type"] == "wall")
        self.assertEqual([(o["id"], o["offset"], o["element_ids"]) for o in wall["openings"]],
                         [("M2-geo2-O1", 1000, [50]), ("M2-geo2-O2", 3000, [51])])
        self.assertFalse(any("joinery" in o["id"] for o in entry["objects"]))
        self.assertEqual(entry["counts"]["opening"], 2)
        self.assertNotIn(51, inventory["unattached_element_ids"])

    def test_the_summary_does_not_count_joinery_it_cannot_place_as_other(self) -> None:
        entry = module_entry(build_object_inventory(self.geometry_module()), "M2")
        self.assertEqual(entry["counts"].get("other", 0), 0)


class ModuleAssignment(unittest.TestCase):
    def test_a_disagreeing_module_attribute_is_warned_and_the_subgroup_wins(self) -> None:
        snaps = module_m1()
        snaps[3] = element(11, box(0, 6, 220, 45, 206, 2865), name="montant", group="MOB",
                           subgroup="M1-W1", module="M2")
        entry = module_entry(build_object_inventory(snaps))
        self.assertTrue(any("1 elements have a Module attribute" in w for w in entry["warnings"]))
        self.assertEqual([m["module_id"] for m in build_object_inventory(snaps)["modules"]], ["M1"])

    def test_zero_padded_attribute_agrees_with_subgroup(self) -> None:
        snaps = module_m1()
        snaps[3] = element(11, box(0, 6, 220, 45, 206, 2865), name="montant", group="MOB",
                           subgroup="M1-W1", module="M001")
        entry = module_entry(build_object_inventory(snaps))
        self.assertFalse(any("Module attribute" in w for w in entry["warnings"]))

    def test_a_bare_part_takes_its_module_from_the_attribute(self) -> None:
        snaps = module_m1() + [element(15, box(1500, 6, 220, 1545, 206, 2865), name="montant",
                                       group="MOB", subgroup="W1", module="M1")]
        self.assertIn(15, objects_by_id(detail(snaps))["M1-W1"]["element_ids"])

    def test_an_element_without_any_module_is_unattached(self) -> None:
        stray = element(70, box(0, 0, 0, 10, 10, 10), name="Connecteur", group="Jonction")
        self.assertIn(70, build_object_inventory(module_m1() + [stray])["unattached_element_ids"])

    def test_requesting_an_unknown_module_is_warned(self) -> None:
        inventory = build_object_inventory(module_m1(), module_ids=["M9"])
        self.assertIn("module M9 not found in the scanned elements", inventory["warnings"])

    def test_module_ids_are_matched_in_any_spelling(self) -> None:
        inventory = build_object_inventory(module_m1(), module_ids=["M001"])
        self.assertIn("objects", module_entry(inventory))


class GeometricFallback(unittest.TestCase):
    def loose_module(self) -> List[ObjectSnapshot]:
        """Module M2 with no part subgroup: only the Module attribute."""
        return [
            element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M2"),
            element(2, box(500, 0, 220, 545, 200, 2865), name="montant", module="M2"),
            element(3, box(2000, 0, 220, 2045, 200, 2865), name="montant", module="M2"),
            element(4, box(0, 1200, 220, 4000, 1300, 2865), name="cloison", module="M2"),
            element(5, box(3000, 900, 400, 3200, 1000, 600), name="boitier", module="M2"),
        ]

    def test_the_summary_counts_unclassified_elements(self) -> None:
        entry = module_entry(build_object_inventory(self.loose_module()), "M2")
        self.assertEqual(entry["unclassified_element_count"], 5)
        self.assertEqual(entry["grouping_source"], "geometry")

    def test_the_detail_groups_by_geometry(self) -> None:
        entry = module_entry(build_object_inventory(self.loose_module(), module_ids=["M2"]), "M2")
        kinds = [(o["type"], o.get("side"), o.get("level")) for o in entry["objects"]]
        self.assertEqual(kinds, [("slab", None, "bottom"), ("wall", "-y", None),
                                 ("wall", None, None), ("other", None, None)])
        self.assertEqual(entry["objects"][1]["element_ids"], [2, 3])

    def test_a_corner_element_goes_to_the_first_side_in_order(self) -> None:
        snaps = self.loose_module() + [element(6, box(0, 0, 220, 45, 200, 2865),
                                               name="montant", module="M2")]
        entry = module_entry(build_object_inventory(snaps, module_ids=["M2"]), "M2")
        corner_wall = next(o for o in entry["objects"] if 6 in o["element_ids"])
        self.assertEqual(corner_wall["side"], "-x")

    def test_a_module_reduced_to_its_id_in_the_subgroup_mixes_both_sources(self) -> None:
        snaps = module_m1() + [element(80, box(2000, 1200, 220, 5000, 1300, 2865),
                                       name="cloison", subgroup="M1")]
        entry = module_entry(detail(snaps))
        self.assertEqual(entry["grouping_source"], "subgroup+geometry")
        self.assertIn(80, entry["objects"][-1]["element_ids"])

    def framed_module(self) -> List[ObjectSnapshot]:
        """Module M2 without subgroups: a floor and a -y wall with its plates."""
        return [
            element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M2"),
            element(2, box(0, 0, 220, 6000, 200, 265), name="lisse basse", module="M2"),
            element(3, box(0, 0, 2820, 6000, 200, 2865), name="lisse haute", module="M2"),
            element(4, box(500, 0, 265, 545, 200, 2820), name="montant", module="M2"),
            element(5, box(2000, 0, 265, 2045, 200, 2820), name="montant", module="M2"),
            element(6, box(0, 0, 265, 6000, 15, 2820), name="OSB mur", module="M2"),
        ]

    def test_wall_plates_belong_to_their_side_wall(self) -> None:
        entry = module_entry(build_object_inventory(self.framed_module(), module_ids=["M2"]),
                             "M2")
        kinds = [(o["type"], o.get("side"), o.get("level"), o["element_ids"])
                 for o in entry["objects"]]
        self.assertEqual(kinds, [("slab", None, "bottom", [1]),
                                 ("wall", "-y", None, [2, 3, 4, 5, 6])])
        self.assertEqual(module_entry(build_object_inventory(self.framed_module(),
                                                             module_ids=["M2"]), "M2")
                         ["frame"]["height"], 2865)

    def test_the_top_slab_threshold_is_measured_above_the_bottom_floor(self) -> None:
        snaps = [element(1, box(0, 0, 0, 6000, 2500, 400), name="plancher", module="M2"),
                 element(2, box(1000, 1000, 700, 3000, 2000, 745), name="dalle", module="M2"),
                 element(3, box(500, 500, 2865, 5500, 2000, 3085), name="plafond",
                         module="M2")]
        entry = module_entry(build_object_inventory(snaps, module_ids=["M2"]), "M2")
        levels = {o["level"]: o["element_ids"] for o in entry["objects"]}
        self.assertEqual(levels, {"bottom": [1, 2], "top": [3]})

    def test_collinear_partitions_far_apart_are_two_walls(self) -> None:
        snaps = [element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M3"),
                 element(2, box(500, 1200, 220, 2000, 1300, 2865), name="cloison A",
                         module="M3"),
                 element(3, box(4000, 1200, 220, 5500, 1300, 2865), name="cloison B",
                         module="M3")]
        entry = module_entry(build_object_inventory(snaps, module_ids=["M3"]), "M3")
        walls = [(o["element_ids"], o["start"], o["end"]) for o in entry["objects"]
                 if o["type"] == "wall"]
        self.assertEqual(walls, [([2], [500, 1250, 220], [2000, 1250, 220]),
                                 ([3], [4000, 1250, 220], [5500, 1250, 220])])

    def test_a_partition_of_studs_is_one_interior_wall(self) -> None:
        snaps = [element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M3")]
        snaps += [element(10 + n, box(3000, y, 220, 3100, y + 45, 2865), name="montant",
                          module="M3") for n, y in enumerate((500, 1100, 1700))]
        entry = module_entry(build_object_inventory(snaps, module_ids=["M3"]), "M3")
        walls = [o for o in entry["objects"] if o["type"] == "wall"]
        self.assertEqual(len(walls), 1)
        self.assertEqual(walls[0]["element_ids"], [10, 11, 12])
        self.assertEqual((walls[0]["start"], walls[0]["end"], walls[0]["side"]),
                         ([3050, 500, 220], [3050, 1745, 220], None))
        self.assertFalse(any(o["type"] == "other" for o in entry["objects"]))

    def test_interior_walls_do_not_depend_on_the_element_order(self) -> None:
        # Each element shares a plane with its neighbour, not with the far one.
        snaps = [element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M3"),
                 element(2, box(1000, 1200, 220, 2000, 1300, 2865), module="M3"),
                 element(3, box(1500, 1280, 220, 2500, 1380, 2865), module="M3"),
                 element(4, box(2000, 1360, 220, 3000, 1460, 2865), module="M3")]
        for order in (snaps, snaps[:1] + snaps[:0:-1]):
            entry = module_entry(build_object_inventory(order, module_ids=["M3"]), "M3")
            walls = [o["element_ids"] for o in entry["objects"] if o["type"] == "wall"]
            self.assertEqual(walls, [[2, 3, 4]])


class Warnings(unittest.TestCase):
    def test_a_module_without_floor_has_no_frame(self) -> None:
        snaps = [s for s in module_m1() if s.subgroup != "M1-F1"]
        snaps = [s for s in snaps if s.subgroup != "M1-TF0"]
        entry = module_entry(detail(snaps))
        self.assertIsNone(entry["frame"])
        self.assertEqual(entry["objects"], [])
        self.assertIn("no bottom floor found: no frame, no objects", entry["warnings"])

    def test_an_l_shaped_floor_is_warned_and_objects_omitted(self) -> None:
        snaps = [s for s in module_m1() if s.subgroup != "M1-F1"]
        snaps += [element(1, box(0, 0, 0, 6000, 1000, 220), group="Plancher bas",
                          subgroup="M1-F1"),
                  element(2, box(0, 0, 0, 1000, 6000, 220), group="Plancher bas",
                          subgroup="M1-F1")]
        entry = module_entry(detail(snaps))
        self.assertEqual(entry["objects"], [])
        self.assertTrue(any("not rectangular" in w for w in entry["warnings"]))

    def test_an_object_without_readable_geometry_is_warned(self) -> None:
        snaps = keep_vertices(module_m1(), {1, 2, 10, 11, 12, 30, 40, 50})
        entry = module_entry(detail(snaps))
        self.assertNotIn("M1-W2", [o["id"] for o in entry["objects"]])
        self.assertIn("M1-W2: no readable geometry, omitted", entry["warnings"])

    def top_floor_module(self) -> List[ObjectSnapshot]:
        """Module M4: a top-floor part, a wall part and a loose bottom floor."""
        return [element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M4"),
                element(2, box(0, 0, 2865, 6000, 2500, 3100), group="Plancher haut",
                        subgroup="M4-F2"),
                element(3, box(0, 0, 220, 6000, 212, 2865), name="MOB200", subgroup="M4-W1")]

    def test_a_top_floor_part_is_not_taken_for_the_bottom_floor(self) -> None:
        snaps = self.top_floor_module()
        real = keep_vertices(snaps, geometry_needed(snaps))
        self.assertEqual(module_entry(build_object_inventory(real), "M4")["frame"]["origin_model"],
                         [0, 0, 0])
        entry = module_entry(build_object_inventory(snaps, module_ids=["M4"]), "M4")
        slab = next(o for o in entry["objects"] if o["id"] == "M4-F2")
        self.assertEqual((slab["level"], slab["origin"]), ("top", [0, 0, 2865]))


class ElementDetail(unittest.TestCase):
    def test_envelope_detail_lists_elements_in_the_module_frame(self) -> None:
        wall = objects_by_id(detail(module_m1(90, (10000, 5000, 0)),
                                    element_detail="envelope"))["M1-W1"]
        stud = next(e for e in wall["elements"] if e["element_id"] == 12)
        self.assertEqual(stud, {"element_id": 12, "name": "montant", "material": "C24",
                                "origin": [955, 6, 220], "size": [45, 200, 2645]})

    def test_vertices_detail_adds_local_vertices(self) -> None:
        wall = objects_by_id(detail(module_m1(37, (500, 800, 0)),
                                    element_detail="vertices"))["M1-W1"]
        stud = next(e for e in wall["elements"] if e["element_id"] == 12)
        self.assertIn([955, 6, 220], stud["vertices"])
        self.assertEqual(len(stud["vertices"]), 8)

    def test_no_detail_by_default(self) -> None:
        self.assertNotIn("elements", objects_by_id(detail(module_m1()))["M1-W1"])

    def test_an_invalid_level_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            build_object_inventory(module_m1(), element_detail="all")


class GeometryNeeded(unittest.TestCase):
    def test_the_summary_needs_floors_bodies_and_joinery_only(self) -> None:
        self.assertEqual(geometry_needed(module_m1()), {1, 2, 10, 20, 50})

    def test_a_wall_without_single_body_needs_all_its_elements(self) -> None:
        snaps = [s for s in module_m1() if s.element_id != 10]
        self.assertTrue({11, 12} <= geometry_needed(snaps))

    def test_a_detailed_module_needs_every_element_but_processings(self) -> None:
        self.assertEqual(geometry_needed(module_m1(), module_ids=["M1"]),
                         {1, 2, 10, 11, 12, 20, 30, 40, 50})

    def test_a_module_without_slab_part_needs_everything(self) -> None:
        snaps = [element(1, box(0, 0, 0, 10, 10, 10), module="M3"),
                 element(2, box(0, 0, 0, 10, 10, 10), subgroup="M3-W1")]
        self.assertEqual(geometry_needed(snaps), {1, 2})

    def test_a_module_with_only_a_top_floor_part_needs_everything(self) -> None:
        snaps = [element(1, box(0, 0, 0, 10, 10, 10), module="M4"),
                 element(2, box(0, 0, 0, 10, 10, 10), group="Plancher haut", subgroup="M4-F2"),
                 element(3, box(0, 0, 0, 10, 10, 10), name="MOB200", subgroup="M4-W1")]
        self.assertEqual(geometry_needed(snaps), {1, 2, 3})


if __name__ == "__main__":
    unittest.main()
