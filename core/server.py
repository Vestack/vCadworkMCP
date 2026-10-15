"""
MCP Server setup and configuration
"""
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any
from mcp.server.fastmcp import FastMCP
from .connection import initialize_connection, get_connection
from .logging import setup_logging, log_info, log_warning

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server lifecycle"""
    # Setup logging
    setup_logging()
    log_info("Starting vCadworkMCP server...")
    
    # Initialize connection
    host = "127.0.0.1"
    port = int(os.environ.get("CW_PORT", 53002))
    connection = initialize_connection(host, port)
    
    # Test connection
    handshake_ok = connection.test_connection()
    if handshake_ok:
        log_info("Connection to Cadwork established successfully")
    else:
        log_warning("Could not establish connection to Cadwork")
    
    yield {"cadwork_connected": handshake_ok}
    
    # Cleanup
    log_info("Shutting down vCadworkMCP server...")

SERVER_NAME = "vCadworkMCP"
SERVER_VERSION = "0.2.0"


def create_mcp_server() -> FastMCP:
    """Create and configure MCP server.

    FastMCP takes neither `version` nor `description`; passing them raised a
    TypeError, so the server could not start at all. The version now travels in
    the instructions, which is what the client actually gets to read.
    """
    return FastMCP(
        SERVER_NAME,
        instructions=(
            f"Cadwork 3D integration v{SERVER_VERSION}, over the MCP Bridge "
            "plugin running inside Cadwork. All lengths are millimetres."
        ),
        lifespan=server_lifespan,
    )
