"""Tests for building the MCP server.

These need the mcp package, so run them from the project virtualenv. They are
skipped, not failed, on an interpreter without it: the rest of the suite
deliberately needs nothing beyond the standard library.
"""
import asyncio
import unittest

try:
    from mcp.server.fastmcp import FastMCP
    HAVE_MCP = True
except ImportError:
    HAVE_MCP = False


@unittest.skipUnless(HAVE_MCP, "the mcp package is not installed in this interpreter")
class CreateMcpServer(unittest.TestCase):
    def test_builds_a_server(self) -> None:
        from core.server import create_mcp_server
        self.assertIsInstance(create_mcp_server(), FastMCP)

    def test_the_server_is_named_for_cadwork(self) -> None:
        from core.server import create_mcp_server
        self.assertEqual(create_mcp_server().name, "vCadworkMCP")

    def test_exposes_the_object_the_http_transport_passes_to_uvicorn(self) -> None:
        # main.py used to hand uvicorn a non-existent `mcp.app`.
        from core.server import create_mcp_server
        self.assertTrue(hasattr(create_mcp_server(), "streamable_http_app"))


@unittest.skipUnless(HAVE_MCP, "the mcp package is not installed in this interpreter")
class ToolRegistration(unittest.TestCase):
    """Importing main runs every @mcp.tool declaration."""

    def test_the_generic_tools_are_registered(self) -> None:
        import main
        names = {tool.name for tool in asyncio.run(main.mcp.list_tools())}
        for expected in ("create_beam", "move_element", "get_all_element_ids",
                         "get_element_info", "get_group_statistics"):
            self.assertIn(expected, names)

    def test_the_vestack_tool_is_registered(self) -> None:
        import main
        names = {tool.name for tool in asyncio.run(main.mcp.list_tools())}
        self.assertIn("get_module_inventory", names)

    def test_the_object_inventory_tool_is_registered(self) -> None:
        import main
        names = {tool.name for tool in asyncio.run(main.mcp.list_tools())}
        self.assertIn("get_object_inventory", names)

    def test_every_tool_has_a_description(self) -> None:
        import main
        undescribed = [t.name for t in asyncio.run(main.mcp.list_tools())
                       if not (t.description or "").strip()]
        self.assertEqual(undescribed, [])


if __name__ == "__main__":
    unittest.main()
