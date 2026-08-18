"""Tests for the router that reaches the Cadwork API modules.

Inside Cadwork, `import attribute_controller` is the Cadwork API. Outside it, the
tests put fake modules of the same names into sys.modules, which is why the
router must resolve them per call rather than caching them at import time.
"""
import sys
import types
import unittest
from typing import Any, Callable, Dict
from unittest.mock import patch

from bridge.cadwork_api import UnknownCadworkFunction, call_cadwork_function


def fake_module(**functions: Callable[..., Any]) -> types.ModuleType:
    module = types.ModuleType("fake_cadwork_module")
    for name, function in functions.items():
        setattr(module, name, function)
    return module


def with_modules(**modules: types.ModuleType) -> Any:
    return patch.dict(sys.modules, modules)


class Routing(unittest.TestCase):
    def test_routes_an_attribute_function_to_the_attribute_controller(self) -> None:
        calls: Dict[str, Any] = {}
        module = fake_module(set_group=lambda ids, group: calls.update(ids=ids, group=group))
        with with_modules(attribute_controller=module):
            call_cadwork_function("set_group", [1, 2], "M139")
        self.assertEqual(calls, {"ids": [1, 2], "group": "M139"})

    def test_routes_a_visualization_function_to_the_visualization_controller(self) -> None:
        module = fake_module(set_color=lambda ids, color: "coloured")
        with with_modules(visualization_controller=module):
            self.assertEqual(call_cadwork_function("set_color", [1], 5), "coloured")

    def test_returns_what_the_cadwork_function_returns(self) -> None:
        module = fake_module(get_group=lambda element_id: "M139")
        with with_modules(attribute_controller=module):
            self.assertEqual(call_cadwork_function("get_group", 42), "M139")

    def test_an_unmapped_function_name_is_rejected(self) -> None:
        with self.assertRaises(UnknownCadworkFunction) as caught:
            call_cadwork_function("summon_a_unicorn", 1)
        self.assertIn("summon_a_unicorn", str(caught.exception))

    def test_a_function_missing_from_the_cadwork_module_is_reported(self) -> None:
        with with_modules(attribute_controller=fake_module()):
            with self.assertRaises(UnknownCadworkFunction) as caught:
                call_cadwork_function("set_group", [1], "M139")
        message = str(caught.exception)
        self.assertIn("set_group", message)
        self.assertIn("attribute_controller", message)


if __name__ == "__main__":
    unittest.main()
