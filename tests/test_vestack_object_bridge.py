"""Tests for the object inventory's bridge adapter, with Cadwork faked.

As in test_vestack_bridge_handler, the Cadwork API modules are replaced in
sys.modules; the adapter imports them per call, by their bare names.
"""
import sys
import types
import unittest
from typing import Any, Dict, List, Optional, Set
from unittest.mock import patch

from tests.object_fixtures import module_m1
from vestack.bridge_handler import handle_get_object_inventory
from vestack.object_inventory import ObjectSnapshot

# The spike model's attributes: 1 Batiment, 2 Niveau, 3 Module, 5 Complexe.
ATTRIBUTE_NAMES = {1: "Bâtiment (Alt+F1)", 2: "Niveau (Alt+F2)", 3: "Module (Alt+F3)",
                   5: "Complexe (Alt+F5)"}


def fake_cadwork(snapshots: List[ObjectSnapshot], *, fail_vertices: Optional[int] = None,
                 vertex_calls: Optional[Set[int]] = None) -> Dict[str, types.ModuleType]:
    by_id = {s.element_id: s for s in snapshots}

    def module(**functions: Any) -> types.ModuleType:
        fake = types.ModuleType("fake")
        for name, function in functions.items():
            setattr(fake, name, function)
        return fake

    def get_element_vertices(element_id: int) -> List[List[float]]:
        if vertex_calls is not None:
            vertex_calls.add(element_id)
        if element_id == fail_vertices:
            raise RuntimeError("no geometry")
        return [list(v) for v in by_id[element_id].vertices]

    def get_user_attribute(element_id: int, number: int) -> str:
        s = by_id[element_id]
        return {3: s.module_attribute, 5: s.complex_code}.get(number, "")

    return {
        "element_controller": module(
            get_all_identifiable_element_ids=lambda: sorted(by_id),
            get_active_identifiable_element_ids=lambda: sorted(by_id)[:2]),
        "geometry_controller": module(get_element_vertices=get_element_vertices),
        "attribute_controller": module(
            get_user_attribute_name=lambda n: ATTRIBUTE_NAMES.get(n, ""),
            get_user_attribute=get_user_attribute,
            get_name=lambda eid: by_id[eid].name,
            get_group=lambda eid: by_id[eid].group,
            get_subgroup=lambda eid: by_id[eid].subgroup,
            get_element_material_name=lambda eid: by_id[eid].material),
        "utility_controller": module(get_3d_file_path=lambda: "C:/models/copy.3d"),
    }


def run(args: Dict[str, Any], **fake: Any) -> Dict[str, Any]:
    with patch.dict(sys.modules, fake_cadwork(module_m1(37, (500, 800, 0)), **fake)):
        return handle_get_object_inventory(args)


class HandleGetObjectInventory(unittest.TestCase):
    def test_reads_the_model_into_an_inventory(self) -> None:
        response = run({"module_ids": ["M1"]})
        self.assertEqual(response["status"], "ok")
        walls = {o["id"]: o for o in response["modules"][0]["objects"]}
        self.assertEqual(walls["M1-W1"]["openings"][0]["width"], 1455)

    def test_the_complexe_attribute_is_found_by_name(self) -> None:
        self.assertEqual(run({})["attribute_numbers"]["complex"], 5)

    def test_the_summary_reads_only_the_geometry_it_needs(self) -> None:
        calls: Set[int] = set()
        response = run({}, vertex_calls=calls)
        self.assertEqual(calls, {1, 2, 10, 20, 50})
        self.assertEqual(response["geometry_read_count"], 5)

    def test_material_is_read_with_element_detail(self) -> None:
        response = run({"module_ids": ["M1"], "element_detail": "envelope"})
        floor = next(o for o in response["modules"][0]["objects"] if o["id"] == "M1-F1")
        self.assertEqual(floor["elements"][0]["material"], "OSB-9")

    def test_unreadable_geometry_is_reported(self) -> None:
        self.assertEqual(run({"module_ids": ["M1"]}, fail_vertices=12)["skipped_element_ids"], [12])

    def test_the_source_names_the_open_file(self) -> None:
        source = run({})["source"]
        self.assertEqual(source["file"], "C:/models/copy.3d")
        self.assertIn("T", source["extracted_at"])

    def test_an_invalid_detail_level_is_an_error(self) -> None:
        response = run({"element_detail": "all"})
        self.assertEqual(response["status"], "error")
        self.assertIn("element_detail", response["message"])

    def test_an_invalid_detail_level_reads_nothing_from_cadwork(self) -> None:
        calls: Set[int] = set()
        response = run({"element_detail": "all"}, vertex_calls=calls)
        self.assertEqual(response["status"], "error")
        self.assertEqual(calls, set())

    def test_duplicate_element_ids_are_scanned_once(self) -> None:
        response = run({"element_ids": [1, 1, 2, 2]})
        self.assertEqual(response["scanned_element_count"], 2)

    def test_a_cadwork_failure_becomes_an_error_response(self) -> None:
        broken = fake_cadwork(module_m1())
        broken["element_controller"] = types.ModuleType("fake")
        with patch.dict(sys.modules, broken):
            response = handle_get_object_inventory({})
        self.assertEqual(response["status"], "error")

    def test_the_dispatcher_discovers_the_operation(self) -> None:
        from bridge.dispatcher import CommandDispatcher
        self.assertIn("get_object_inventory", CommandDispatcher().operations)


if __name__ == "__main__":
    unittest.main()
