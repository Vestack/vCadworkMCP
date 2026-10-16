# vestackMCP plugin

Cadwork plugin that starts the vCadworkMCP bridge inside Cadwork.

## Files
- `vestackMCP/vestackMCP.py` - the plugin: starts the bridge on launch, or opens a small start/stop window if the bridge already listens
- `vestackMCP/plugin_info.xml` - plugin metadata
- `vestackMCP/install.ps1` - installer for a Cadwork user profile
- `vestackMCP/README.md` - installation and usage guide

## Installation
Run the installer from this checkout (PowerShell 5 or later):

```powershell
powershell -ExecutionPolicy Bypass -File API.x64\vestackMCP\install.ps1
```

It copies the plugin into the Cadwork 2026 user profile (`-Profile 30` for Cadwork 30),
writes `mcp_home.txt` with the path of this checkout, and creates the desktop shortcut
**Cadwork 2026 + vestackMCP** (`-NoShortcut` to skip it). `-RemoveOld` deletes the
former `MCPBridge` plugin folder of that profile.

Manual fallback: copy the `vestackMCP` folder into the profile's `3d\API.x64`
directory, then set the `CADWORK_MCP_HOME` environment variable to the checkout path,
or create `mcp_home.txt` next to `vestackMCP.py` containing that path on its first
line. Without either, the plugin falls back to `C:\cadworkMCP`. The folder name must
stay `vestackMCP`, the same as the script name.

## Usage
1. Start Cadwork with the **Cadwork 2026 + vestackMCP** shortcut, or start it normally and
   click **vestackMCP** in the user-plugin panel (Fenêtre → Plugins utilisateur in the
   French UI).
2. If nothing listens on port 53002, the plugin imports `cadwork_bridge` from the
   checkout, starts its socket server with no window, and prints
   `vestackMCP: bridge listening on 53002, from <checkout>` in the Cadwork console
   once it has connected to the port to confirm it is listening.
3. If the bridge already listens, a click opens the status window with Start and Stop.
4. Stop only clears the status flag; the socket stays bound until Cadwork exits.
   Restart Cadwork to release the port or to reload changed bridge code.

Once started, any local process can send commands to Cadwork through
`127.0.0.1:53002`, writes included. The port is not reachable from the network.
Details: [`vestackMCP/README.md`](vestackMCP/README.md).
