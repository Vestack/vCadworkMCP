# MCP Bridge Plugin

Cadwork plugin that starts the MCP bridge inside Cadwork.

## Files
- `MCPBridge.py` - the plugin, with a small start/stop GUI
- `plugin_info.xml` - plugin metadata
- `MCPBridge/README.md` - installation guide

## Installation
Copy the `MCPBridge` folder into your Cadwork user profile's `3d\API.x64`
directory, then tell it where this repository is, by either:

- setting the `CADWORK_MCP_HOME` environment variable to the checkout path, or
- creating `mcp_home.txt` next to `MCPBridge.py`, containing that path on its
  first line.

Without either, the plugin falls back to `C:\cadworkMCP`. The GUI displays the
path it resolved, so a wrong setting is visible before you press Start.

## Usage
1. Start Cadwork
2. Window → Plugins → MCP Bridge
3. "Start Bridge" - the plugin imports `cadwork_bridge` from the checkout and
   starts its socket server on port 53002, then connects to it to confirm it is
   really listening before reporting success
4. "Stop Bridge" only clears the status flag; the socket stays bound until
   Cadwork exits. Restart Cadwork to release the port or to reload changed
   bridge code.
