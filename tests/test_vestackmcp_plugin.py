"""Tests for the Cadwork plugin in API.x64/vestackMCP/.

The plugin imports Cadwork's `utility_controller` and lives outside the package
tree, so it is loaded by path with a fake `utility_controller` injected into
sys.modules first. No tkinter window is ever opened: the window is an injected
callable.
"""
import importlib.util
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

PLUGIN_PATH = Path(__file__).resolve().parent.parent / "API.x64" / "vestackMCP" / "vestackMCP.py"


def load_plugin() -> tuple[Any, List[str]]:
    """Load the plugin file under a private name; return it and its console log."""
    console: List[str] = []
    fake_uc = types.ModuleType("utility_controller")
    fake_uc.print_to_console = console.append  # type: ignore[attr-defined]
    with patch.dict(sys.modules, {"utility_controller": fake_uc}):
        spec = importlib.util.spec_from_file_location("vestackMCP_under_test", PLUGIN_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module, console


class Launch(unittest.TestCase):
    def setUp(self) -> None:
        self.plugin, _ = load_plugin()
        self.calls: List[str] = []

    def run_launch(self, listening: bool, started: bool = True) -> str:
        def start() -> bool:
            self.calls.append("start")
            return started

        def show_window() -> None:
            self.calls.append("window")

        return str(self.plugin.launch(lambda: listening, start, show_window))

    def test_starts_the_bridge_without_a_window_when_nothing_listens(self) -> None:
        self.assertEqual(self.run_launch(listening=False), "started")
        self.assertEqual(self.calls, ["start"])

    def test_shows_the_window_when_the_bridge_already_listens(self) -> None:
        self.assertEqual(self.run_launch(listening=True), "window")
        self.assertEqual(self.calls, ["window"])

    def test_reports_failure_and_opens_no_window_when_the_start_fails(self) -> None:
        self.assertEqual(self.run_launch(listening=False, started=False), "failed")
        self.assertEqual(self.calls, ["start"])

    def test_decides_from_the_port_not_from_the_module_flag(self) -> None:
        # A fresh run of the script has bridge_running False even though the
        # bridge from an earlier click still listens.
        self.plugin.bridge_running = False
        self.assertEqual(self.run_launch(listening=True), "window")


class StartBridge(unittest.TestCase):
    """start_bridge with a fake cadwork_bridge module and a stubbed port check."""

    def setUp(self) -> None:
        self.plugin, self.console = load_plugin()
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        Path(self.home.name, "cadwork_bridge.py").write_text("")
        self.plugin.LEGACY_HOME = self.home.name
        # resolve_mcp_home reads mcp_home.txt next to the plugin: point it at
        # a directory without one.
        self.plugin.__file__ = os.path.join(self.home.name, "vestackMCP.py")
        env = patch.dict(os.environ, {"CADWORK_MCP_HOME": ""})
        env.start()
        self.addCleanup(env.stop)

    def start(self, bridge_main: Any, listening: bool) -> bool:
        fake_bridge = types.ModuleType("cadwork_bridge")
        fake_bridge.main = bridge_main  # type: ignore[attr-defined]
        with patch.dict(sys.modules, {"cadwork_bridge": fake_bridge}), \
                patch.object(self.plugin, "is_listening", lambda *a, **k: listening):
            return bool(self.plugin.start_bridge())

    def test_prints_where_the_bridge_listens_and_from_which_checkout(self) -> None:
        self.assertTrue(self.start(lambda: None, listening=True))
        self.assertEqual(
            self.console,
            [f"vestackMCP: bridge listening on 53002, from {self.home.name}"])

    def test_prints_the_exception_when_the_bridge_module_fails(self) -> None:
        def broken() -> None:
            raise RuntimeError("boom")

        self.assertFalse(self.start(broken, listening=False))
        self.assertEqual(len(self.console), 1)
        self.assertIn("vestackMCP: failed to start bridge", self.console[0])
        self.assertIn("boom", self.console[0])

    def test_prints_a_hint_when_the_port_never_comes_up(self) -> None:
        self.assertFalse(self.start(lambda: None, listening=False))
        self.assertEqual(len(self.console), 1)
        self.assertIn("did not come up on port 53002", self.console[0])


class ResolveMcpHome(unittest.TestCase):
    def setUp(self) -> None:
        self.plugin, self.console = load_plugin()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.checkout = os.path.join(self.tmp.name, "checkout")
        os.makedirs(self.checkout)
        Path(self.checkout, "cadwork_bridge.py").write_text("")
        self.plugin_dir = os.path.join(self.tmp.name, "plugin")
        os.makedirs(self.plugin_dir)
        self.plugin.__file__ = os.path.join(self.plugin_dir, "vestackMCP.py")
        self.plugin.LEGACY_HOME = os.path.join(self.tmp.name, "no-legacy")

    def resolve(self, env: Dict[str, str]) -> str:
        with patch.dict(os.environ, env):
            return str(self.plugin.resolve_mcp_home())

    def test_finds_the_checkout_from_mcp_home_txt(self) -> None:
        Path(self.plugin_dir, "mcp_home.txt").write_text(f"# comment\n{self.checkout}\n")
        self.assertEqual(self.resolve({"CADWORK_MCP_HOME": ""}), self.checkout)

    def test_finds_the_checkout_from_the_environment_variable(self) -> None:
        self.assertEqual(self.resolve({"CADWORK_MCP_HOME": self.checkout}), self.checkout)

    def test_a_stale_environment_variable_does_not_shadow_mcp_home_txt(self) -> None:
        Path(self.plugin_dir, "mcp_home.txt").write_text(self.checkout)
        stale = os.path.join(self.tmp.name, "stale")
        self.assertEqual(self.resolve({"CADWORK_MCP_HOME": stale}), self.checkout)

    def test_raises_a_message_naming_the_plugin_script_when_nothing_is_found(self) -> None:
        with self.assertRaises(FileNotFoundError) as caught:
            self.resolve({"CADWORK_MCP_HOME": ""})
        self.assertIn("vestackMCP.py", str(caught.exception))
        self.assertNotIn("MCPBridge", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
