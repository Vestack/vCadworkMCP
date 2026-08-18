# 📋 Manual installation — Cadwork MCP Bridge plugin

## 🎯 Copy instructions

### Step 1: find the Cadwork plugin directory
1. Open **Cadwork 3D**
2. Click **Help → Info**
3. Open the **"Userprofile"** folder
4. Navigate to **`3d\API.x64`**

**Typical path:**
```
C:\Users\Public\Documents\cadwork\userprofil_xx\3d\API.x64
```

### Step 2: copy the plugin
1. Copy this **entire `MCPBridge` folder**:
```
C:\cadworkMCP\API.x64\MCPBridge\
```

2. **Paste** it into Cadwork's API.x64 directory:
```
[CADWORK_USERPROFILE]\3d\API.x64\MCPBridge\
```

### Step 3: check the layout
After copying, the structure should look like this:
```
[CADWORK_USERPROFILE]\3d\API.x64\
└── MCPBridge\
    ├── MCPBridge.py          ← the plugin itself (GUI)
    ├── plugin_info.xml       ← plugin metadata
    ├── mcp_home.txt          ← optional: path to your checkout (see below)
    └── README.md             ← this guide
```

The plugin does not contain the bridge code: it imports `cadwork_bridge` from your
checkout of this repository. Tell it where that checkout is, by either setting the
`CADWORK_MCP_HOME` environment variable, or creating `mcp_home.txt` next to
`MCPBridge.py` with the path on its first line:

```
C:\Users\you\Developpements\cadworkMCP
```

Without either it falls back to `C:\cadworkMCP`. The GUI displays the path it
resolved, so a wrong setting is visible before you press Start.

## 🚀 Using the plugin

### 1. Restart Cadwork
- Close **Cadwork 3D** and open it again

### 2. Activate the plugin
- **Window → Plugins** (show the plugin bar)
- The **MCP Bridge** button appears
- **Click** the button to launch the plugin

### 3. Start the bridge
- The **GUI opens** automatically
- Click **"Start Bridge"**
- The status switches to **"Running"**

## 🔗 Connecting the MCP server

Once the plugin has started the bridge, Claude Desktop launches the MCP server on its own (see the main [`README.md`](../../README.md)). To run it by hand for debugging:

```bash
cd C:\cadworkMCP
python main.py
```

External tools such as Claude can then drive Cadwork.

## ⚙️ Plugin features

- ✅ **One-click bridge start**
- ✅ **Status display**
- ✅ **GUI control**
- ✅ **Embedded server** (socket server on port 53002, inside Cadwork's Python interpreter)

## 🛠️ Troubleshooting

### The plugin does not appear
- **Restart Cadwork**
- **Check the plugin bar:** Window → Plugins
- **Check the folder name:** it must be exactly `MCPBridge`

### The bridge does not start
- Is **port 53002** free? (check for another running bridge)
- Are the **Python paths** correct? The bridge expects `C:\cadworkMCP`
- Check the **Cadwork console** for error messages

### The connection fails
- Check your **firewall settings**
- Use **localhost / 127.0.0.1** only
- Note that "Stop Bridge" only clears the status flag; it does not release the socket. Restart Cadwork if the port stays occupied.

## 🎯 That's it

**Three simple steps:**
1. **Copy the folder**
2. **Start the plugin**
3. **Activate the bridge**

Your Cadwork installation is now ready for external tool integration. 🎉
