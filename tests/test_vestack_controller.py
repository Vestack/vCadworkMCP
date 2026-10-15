"""Tests for the MCP-side object inventory: arguments, timeout, file export.

The socket is replaced by a stub of BaseController.send_command, fed with a real
inventory built from the fixture module.
"""
import asyncio
import json
import os
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

from tests.object_fixtures import module_m1
from vestack.mcp_controller import OBJECT_INVENTORY_TIMEOUT_S, VestackController
from vestack.object_inventory import build_object_inventory

Call = Tuple[str, Dict[str, Any], Optional[float]]


def run(calls: List[Call], **kwargs: Any) -> Dict[str, Any]:
    def fake_send(self: Any, operation: str, args: Optional[Dict[str, Any]] = None,
                  timeout: Optional[float] = None) -> Dict[str, Any]:
        args = args or {}
        calls.append((operation, args, timeout))
        return build_object_inventory(module_m1(), module_ids=args.get("module_ids"),
                                      detail_all=bool(args.get("detail_all")),
                                      element_detail=args.get("element_detail", "none"))

    with patch.object(VestackController, "send_command", fake_send):
        return asyncio.run(VestackController().get_object_inventory(**kwargs))


class Arguments(unittest.TestCase):
    def test_sends_the_operation_with_a_long_timeout(self) -> None:
        calls: List[Call] = []
        run(calls, module_ids=["M1"])
        operation, args, timeout = calls[0]
        self.assertEqual(operation, "get_object_inventory")
        self.assertEqual(args, {"element_detail": "none", "module_ids": ["M1"]})
        self.assertEqual(timeout, OBJECT_INVENTORY_TIMEOUT_S)

    def test_an_invalid_detail_level_is_refused_before_sending(self) -> None:
        calls: List[Call] = []
        response = run(calls, element_detail="all")
        self.assertEqual(response["status"], "error")
        self.assertEqual(calls, [])

    def test_without_output_path_nothing_is_written_and_detail_all_is_not_asked(self) -> None:
        calls: List[Call] = []
        response = run(calls)
        self.assertNotIn("detail_all", calls[0][1])
        self.assertNotIn("output_path", response)


class FileExport(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "inventory.json")

    def test_the_file_holds_every_module_in_detail(self) -> None:
        calls: List[Call] = []
        response = run(calls, output_path=self.path)
        self.assertTrue(calls[0][1]["detail_all"])
        with open(self.path, encoding="utf-8") as stream:
            written = json.load(stream)
        self.assertIn("objects", written["modules"][0])
        self.assertEqual(response["output_path"], os.path.abspath(self.path))

    def test_the_response_stays_a_summary_unless_modules_are_named(self) -> None:
        self.assertNotIn("objects", run([], output_path=self.path)["modules"][0])
        self.assertIn("objects", run([], output_path=self.path, module_ids=["M001"])["modules"][0])

    def test_an_unwritable_path_is_an_error_and_leaves_no_file(self) -> None:
        missing = os.path.join(self.directory, "no-such-dir", "inventory.json")
        response = run([], output_path=missing)
        self.assertEqual(response["status"], "error")
        self.assertFalse(os.path.exists(missing))
        self.assertEqual(os.listdir(self.directory), [])


if __name__ == "__main__":
    unittest.main()
