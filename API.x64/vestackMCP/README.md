# vestackMCP plugin for Cadwork

Cadwork plugin that starts the vCadworkMCP bridge (a TCP socket server on
`127.0.0.1:53002`) inside Cadwork's Python interpreter. The plugin holds no bridge
code: it imports `cadwork_bridge` from your checkout of this repository.

## Install with install.ps1

From any PowerShell (5 or later), pointing at your checkout:

```powershell
powershell -ExecutionPolicy Bypass -File <checkout>\API.x64\vestackMCP\install.ps1
```

The script:

1. copies `vestackMCP.py`, `plugin_info.xml`, `Icon.png`, `icon.svg` and `README.md`
   into `C:\Users\Public\Documents\cadwork\userprofil_2026\3d\API.x64\vestackMCP`;
2. writes `mcp_home.txt` there, holding the path of your checkout;
3. creates the desktop shortcut **Cadwork 2026 + vestackMCP** (see below).

| Option | Effect |
|---|---|
| `-Profile 30` | Target the Cadwork 30 profile and `EXE_30` instead of 2026 (default `2026`). |
| `-RemoveOld` | Delete the former `...\3d\API.x64\MCPBridge` folder of that profile, and say so. |
| `-NoShortcut` | Install the plugin only. |

It stops with a message, before copying anything, if the profile folder or (without
`-NoShortcut`) `ci_start.exe` is missing. Restart Cadwork afterwards so that it
rescans its plugin folder.

## Manual install (fallback)

1. In Cadwork, **Help → Info → Userprofile**, then open `3d\API.x64`. Typical path:
   `C:\Users\Public\Documents\cadwork\userprofil_xx\3d\API.x64`.
2. Copy this whole `vestackMCP` folder there. The folder name must stay `vestackMCP`,
   identical to the script name `vestackMCP.py`: Cadwork requires it.
3. Tell the plugin where your checkout is, by either setting the `CADWORK_MCP_HOME`
   environment variable, or creating `mcp_home.txt` next to `vestackMCP.py` with the
   path on its first line (UTF-8, no BOM):

   ```
   C:\Users\you\Developpements\cadworkMCP
   ```

   Without either it falls back to `C:\cadworkMCP`. The first candidate that contains
   `cadwork_bridge.py` wins.
4. Restart Cadwork.

## What happens when the plugin runs

The same logic applies to the shortcut and to a manual click (`vestackMCP.py:launch`):

- Nothing listens on port 53002: the bridge starts at once, with no window, and the
  Cadwork console prints `vestackMCP: bridge listening on 53002, from <checkout>`. If it
  cannot start, the console says why (checkout not found, import error, port held by
  another process).
- A bridge already listens: the plugin opens a small status window with Start and Stop
  buttons and the resolved checkout path.

The decision reads the port, not a flag in the script, because Cadwork may run the
script afresh on every click.

Stop only clears the window's status flag. The socket stays bound until Cadwork exits,
so restart Cadwork to release the port or to reload changed bridge code.

## Starting Cadwork with the bridge running

The desktop shortcut **Cadwork 2026 + vestackMCP** runs:

```
"C:\Program Files\cadwork.dir\ci_start.exe" /EXE="C:\Program Files\cadwork.dir\EXE_2026" /PLUGIN=vestackMCP
```

Cadwork's command line runs the plugin right after the file opens (documented at
<https://docs.cadwork.com/projects/cwapi3dpython/en/latest/command_line/>); `/PLUGIN=`
takes the plugin's folder name. The documented form passes a `.3d` file as first
argument: what the shortcut does without one has not yet been verified. To always
open a given model, add its path in quotes at the start of the shortcut's arguments.

Without the shortcut, start Cadwork normally and click **vestackMCP** once in
**Fenêtre → Plugins utilisateur** (French UI).

## Security

Once started, the bridge accepts connections on `127.0.0.1:53002` with no
authentication. Any process on the machine can drive Cadwork through it, writes
included. The port is bound to the loopback interface, so it is not reachable from the
network.

## Connecting the MCP server

Claude Desktop launches the MCP server by itself (see the main
[`README.md`](../../README.md)). To run it by hand for debugging:

```
cd <checkout>
.venv\Scripts\python main.py
```

## Troubleshooting

- **The plugin does not appear**: restart Cadwork, and check that the folder is named
  exactly `vestackMCP` and contains `vestackMCP.py`.
- **The bridge does not start**: read the Cadwork console. Check that port 53002 is
  free and that the checkout path is right (the status window shows the resolved
  path; with the shortcut, the console line does).
- **The connection fails**: use `127.0.0.1` only. A bridge that does not answer while a
  Cadwork command is active answers again once you press Escape.
- **Upgrading from the MCPBridge plugin**: run `install.ps1 -RemoveOld`, or delete
  `...\3d\API.x64\MCPBridge` by hand. Two plugins would try to bind the same port.
