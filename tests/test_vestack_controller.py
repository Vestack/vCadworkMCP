"""Tests for the MCP-side object inventory: arguments, timeout, file export.

The socket is replaced by a stub of BaseController.send_command: it answers
"ping" with {"status": "ok"} and "get_object_inventory" with a real inventory
built from the fixture module.
"""
import asyncio
import json
import os
import shutil
import tempfile
import threading
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

from tests.object_fixtures import module_m1
from vestack.mcp_controller import OBJECT_INVENTORY_TIMEOUT_S, VestackController
from vestack.object_inventory import build_object_inventory

Call = Tuple[str, Dict[str, Any], Optional[float]]


PONG: Dict[str, Any] = {"status": "ok"}


def run(calls: List[Call], ping: Optional[Dict[str, Any]] = None,
        threads: Optional[List[int]] = None, **kwargs: Any) -> Dict[str, Any]:
    def fake_send(self: Any, operation: str, args: Optional[Dict[str, Any]] = None,
                  timeout: Optional[float] = None) -> Dict[str, Any]:
        args = args or {}
        calls.append((operation, args, timeout))
        if threads is not None:
            threads.append(threading.get_ident())
        if operation == "ping":
            return PONG if ping is None else ping
        return build_object_inventory(module_m1(), module_ids=args.get("module_ids"),
                                      detail_all=bool(args.get("detail_all")),
                                      element_detail=args.get("element_detail", "none"))

    with patch.object(VestackController, "send_command", fake_send):
        return asyncio.run(VestackController().get_object_inventory(**kwargs))


def inventory_call(calls: List[Call]) -> Call:
    """The get_object_inventory call, which follows the ping."""
    operations = [c[0] for c in calls]
    if operations != ["ping", "get_object_inventory"]:
        raise AssertionError(f"expected a ping then the inventory, got {operations}")
    return calls[1]


class Arguments(unittest.TestCase):
    def test_sends_the_operation_with_a_long_timeout(self) -> None:
        calls: List[Call] = []
        run(calls, module_ids=["M1"])
        operation, args, timeout = inventory_call(calls)
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
        self.assertNotIn("detail_all", inventory_call(calls)[1])
        self.assertNotIn("output_path", response)


class Preflight(unittest.TestCase):
    """Quick checks before the long call, which can take minutes."""

    def test_the_bridge_is_pinged_with_the_default_timeout_first(self) -> None:
        calls: List[Call] = []
        run(calls)
        self.assertEqual(calls[0], ("ping", {}, None))

    def test_a_failing_ping_stops_before_the_inventory_is_asked(self) -> None:
        calls: List[Call] = []
        failure = {"status": "error", "message": "Operation timed out: press Escape"}
        response = run(calls, ping=failure)
        self.assertEqual(response, failure)
        self.assertEqual([c[0] for c in calls], ["ping"])

    def test_a_missing_output_directory_is_refused_before_contacting_the_bridge(self) -> None:
        directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, directory, True)
        missing = os.path.join(directory, "no-such-dir")
        calls: List[Call] = []
        response = run(calls, output_path=os.path.join(missing, "inventory.json"))
        self.assertEqual(response, {"status": "error", "message":
                                    f"output_path directory does not exist: {missing}"})
        self.assertEqual(calls, [])

    def test_the_socket_calls_run_off_the_event_loop_thread(self) -> None:
        threads: List[int] = []
        run([], threads=threads)
        self.assertEqual(len(threads), 2)
        self.assertNotIn(threading.get_ident(), threads)


class FileExport(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.directory, True)
        self.path = os.path.join(self.directory, "inventory.json")

    def test_the_file_holds_every_module_in_detail(self) -> None:
        calls: List[Call] = []
        response = run(calls, output_path=self.path)
        self.assertTrue(inventory_call(calls)[1]["detail_all"])
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

    def test_an_unserialisable_inventory_is_an_error_and_leaves_no_file(self) -> None:
        with patch("vestack.mcp_controller.json.dump", side_effect=TypeError("not JSON")):
            response = run([], output_path=self.path)
        self.assertEqual(response["status"], "error")
        self.assertIn("not JSON", response["message"])
        self.assertEqual(os.listdir(self.directory), [])

    def test_a_failed_replace_leaves_no_temporary_file(self) -> None:
        taken = os.path.join(self.directory, "taken")
        os.mkdir(taken)
        response = run([], output_path=taken)
        self.assertEqual(response["status"], "error")
        self.assertEqual(os.listdir(self.directory), ["taken"])


if __name__ == "__main__":
    unittest.main()
