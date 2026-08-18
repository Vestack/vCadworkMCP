"""Tests for the bridge command dispatcher.

Discovery and the response contract are testable outside Cadwork: the dispatcher
is handed stub handler modules instead of the real ones.
"""
import unittest
from typing import Any, Dict

from bridge.dispatcher import CommandDispatcher

STUBS = ("tests.stub_handlers",)
BROKEN = "tests.stub_handlers_unimportable"


def dispatch(operation: str, args: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return CommandDispatcher(STUBS).dispatch(operation, args or {})


class Discovery(unittest.TestCase):
    def test_discovers_handlers_by_naming_convention(self) -> None:
        self.assertIn("stub_ok", CommandDispatcher(STUBS).operations)

    def test_strips_the_handle_prefix_from_the_operation_name(self) -> None:
        self.assertNotIn("handle_stub_ok", CommandDispatcher(STUBS).operations)

    def test_ignores_module_members_that_are_not_handlers(self) -> None:
        self.assertNotIn("not_a_handler", CommandDispatcher(STUBS).operations)

    def test_a_module_that_cannot_be_imported_is_skipped(self) -> None:
        dispatcher = CommandDispatcher(STUBS + (BROKEN,))
        self.assertIn("stub_ok", dispatcher.operations)
        self.assertIn(BROKEN, dispatcher.unavailable_modules)

    def test_the_real_handler_modules_expose_ping(self) -> None:
        # CadworkConnection.test_connection() sends "ping": without it the
        # handshake reports the bridge as unreachable even when it is running.
        self.assertIn("ping", CommandDispatcher().operations)

    def test_the_real_handler_modules_expose_the_element_operations(self) -> None:
        operations = CommandDispatcher().operations
        for operation in ("create_beam", "get_all_element_ids", "get_bounding_box",
                          "get_group_statistics", "get_standard_attributes"):
            self.assertIn(operation, operations)


class ResponseContract(unittest.TestCase):
    def test_passes_the_arguments_through_to_the_handler(self) -> None:
        self.assertEqual(dispatch("stub_ok", {"value": 5})["echo"], 5)

    def test_an_ok_status_and_its_payload_pass_through(self) -> None:
        self.assertEqual(dispatch("stub_ok", {"value": 1}),
                         {"status": "ok", "echo": 1})

    def test_a_success_status_is_normalised_to_ok(self) -> None:
        # The MCP side (BaseController, test_connection) only accepts "ok".
        self.assertEqual(dispatch("stub_success")["status"], "ok")

    def test_normalising_the_status_keeps_the_payload(self) -> None:
        self.assertEqual(dispatch("stub_success")["data"], 42)

    def test_an_error_status_from_the_handler_is_preserved(self) -> None:
        response = dispatch("stub_error")
        self.assertEqual(response["status"], "error")
        self.assertIn("handler said no", response["message"])

    def test_an_exception_becomes_an_error_response(self) -> None:
        response = dispatch("stub_raises")
        self.assertEqual(response["status"], "error")
        self.assertIn("boom", response["message"])

    def test_an_exception_response_names_the_operation(self) -> None:
        self.assertIn("stub_raises", dispatch("stub_raises")["message"])

    def test_a_result_that_is_not_a_dict_is_wrapped(self) -> None:
        self.assertEqual(dispatch("stub_plain_result"),
                         {"status": "ok", "data": [1, 2, 3]})

    def test_a_result_without_a_status_defaults_to_ok(self) -> None:
        response = dispatch("stub_without_status")
        self.assertEqual(response["status"], "ok")
        self.assertEqual(response["element_ids"], [7])


class UnknownOperation(unittest.TestCase):
    def test_an_unknown_operation_is_an_error(self) -> None:
        self.assertEqual(dispatch("no_such_operation")["status"], "error")

    def test_an_unknown_operation_is_named_in_the_message(self) -> None:
        self.assertIn("no_such_operation", dispatch("no_such_operation")["message"])

    def test_an_unknown_operation_lists_the_available_operations(self) -> None:
        response = dispatch("no_such_operation")
        self.assertIn("stub_ok", response["available_operations"])


if __name__ == "__main__":
    unittest.main()
