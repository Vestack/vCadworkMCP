# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

**vCadworkMCP** (repository `Vestack/vCadworkMCP`, formerly `cadworkMCP`): Vestack's MCP (Model Context Protocol) server that lets an AI assistant drive **Cadwork 3D** (timber-construction CAD). The `v` prefix marks it as a Vestack tool, like vMES; it is not a Cadwork product. Keep "Cadwork" for what refers to Cadwork itself (`import cadwork`, `cwapi3d`, `get_cadwork_axis_info`, "for Cadwork 3D"), and the product name for this project. It is **two processes**, not one:

1. **MCP server** (`main.py`) — runs outside Cadwork, launched by the MCP client (Claude Desktop) over stdio. Exposes 167 `@mcp.tool` definitions.
2. **Bridge** (`cadwork_bridge.py` + `bridge/`) — runs *inside* Cadwork's embedded Python interpreter, started from the Cadwork plugin GUI. Owns a TCP socket server and is the only code allowed to touch the real cadwork API.

They talk **unframed JSON over a raw TCP socket on `127.0.0.1:53002`**. There is no HTTP and no length header: the receiver keeps reading bytes until `json.loads` succeeds (`core/connection.py:_receive_response`, `cadwork_bridge.py:socket_server`).

```
Claude Desktop --stdio--> main.py (@mcp.tool)
                            |
                            v
                     controllers/*.py  (async, socket proxies)
                            |
                    JSON over TCP :53002
                            |
                            v
             cadwork_bridge.py (inside Cadwork)
                            |
                            v
              bridge/dispatcher.py -> bridge/handlers/*.py -> cadwork API
                            |                     |
                            |                     +-> bridge/cadwork_api.py
                            +-> vestack/bridge_handler.py (domain extension)
```

**Operations are discovered by convention.** Any `handle_<operation>(args) -> dict`
in a module listed in `bridge/dispatcher.py:HANDLER_MODULES` becomes the operation
`<operation>`. There is no second table to keep in sync: writing the handler is
what exposes it. Handler modules are imported one by one and a module that fails
to import is recorded in `unavailable_modules` without taking the others down —
`export_handlers` and `import_handlers` do `import cadwork` at module level, so
they need either Cadwork or the `cwapi3d` stubs. `CommandDispatcher().diagnostics()`
reports what was found: **140 operations, no unavailable modules**, with the stubs
installed; 121 without them.

## Critical: the `*_controller` name collision

Cadwork's own Python API modules are named `element_controller`, `attribute_controller`, `geometry_controller`, `utility_controller`, `visualization_controller`, `shop_drawing_controller`, `machine_controller`, `roof_controller` — **the same names as this repo's `controllers/` package**.

- Inside `bridge/handlers/*.py`: `import element_controller as ec` means **the cadwork API**.
- Anywhere else: `from controllers.element_controller import ElementController` means **this repo's socket proxy**.

Never let bridge-side code import from `controllers/`, and never assume `element_controller` means cadwork on the server side. This collision is the direct cause of the breakage below.

## What was repaired, and what is still missing

Until commit `e8a6e46` every operation answered `Processing error`: the
dispatcher built its map from `controllers/*`, so the bridge called its own
socket and returned un-awaited coroutines. Two rules keep it fixed:

- **The dispatcher reads `bridge/handlers/` and `vestack/`, never `controllers/`.**
- **`bridge/controller_manager.py` must not come back.** It resolved
  `'set_group' -> 'attribute_controller'` to this repo's async proxy instead of
  the Cadwork module, with a fallback that rewrote its global map. It is replaced
  by `bridge/cadwork_api.py`: an explicit function-name → Cadwork-module map,
  resolved per call, no fallback. Add an entry there when a handler needs a new
  API function.

**Where the 167 tools go.** 137 reach a bridge operation. 4 are computed in the
MCP server and work without Cadwork: `measure_distance`, `measure_angle`,
`measure_area` (`controllers/measurement_controller.py`) and
`get_cadwork_axis_info` (`main.py`). The remaining **26 are phantoms**: no handler
exists, so they answer `Unknown operation` with the list of valid ones:
`mirror_elements`, `scale_elements`, `stretch_elements`, `split_element`,
`chamfer_edge`, `round_edge`, `intersect_elements`, `subtract_elements`,
`unite_elements`, `project_point_to_element`, `calculate_center_of_mass`,
`get_closest_point_on_element`, `get_element_outline`, `get_section_outline`,
`get_elements_by_color`, `get_elements_by_layer`,
`get_elements_by_dimension_range`, `create_material`, `get_material_properties`,
`list_available_materials`, `export_to_btl`, `export_to_ifc`, `export_to_dxf`,
`export_element_list`, `export_cutting_list`, `export_workshop_drawings`.
They were deliberately left declared as roadmap markers. Implementing one means
writing its `handle_*`; the dispatcher then picks it up with no further wiring.
Conversely, 3 of the 140 operations have no tool (`ping`, `get_model_name`,
`get_version_info`), and 3 controller methods have neither a tool nor a handler
(`get_export_formats`, `set_material_density`, `set_material_thermal_properties`).

A tool without a handler is not necessarily a phantom: check whether its
controller method calls `send_command` before listing it as one.

**How far verification actually goes.** The server starts, reaches its lifespan
handler and sends its `ping` to the bridge. Discovery finds all 140 operations,
and mypy checks every handler call site against the Cadwork 30 stubs. What has
*not* happened: a single operation executed against a live model. The stubs
type-check but do nothing, so passing mypy says the call is well-formed, not that
Cadwork accepts it. Treat the first real call as the verification.

**Other loose ends.** `bridge/handlers/base_handler.py:BaseHandler.safe_call` is
dead code, called from nowhere. `create_auto_container_from_standard` and
`get_container_content_elements` exist on both `controllers/container_controller.py`
and `controllers/element_controller.py:720,741`. `bridge/ARCHITECTURE.md`
describes the abandoned "no handlers layer" refactor — read it as history.

## Hard environment constraints

- **The checkout can live anywhere.** The plugin resolves it at run time:
  `CADWORK_MCP_HOME`, else `mcp_home.txt` next to `MCPBridge.py`, else the legacy
  `C:\cadworkMCP` — first candidate containing `cadwork_bridge.py` wins
  (`API.x64/MCPBridge/MCPBridge.py:resolve_mcp_home`). The GUI shows what it
  resolved. `start.txt` is gone: the plugin imports `cadwork_bridge` directly
  instead of `exec()`-ing a text file.
- Bridge port: the **server** side reads `CW_PORT` (default 53002, `core/server.py`); the **bridge** side hardcodes `53002` (`cadwork_bridge.py`). Changing it means editing both.
- Python: the MCP server runs on the venv's 3.12 (`mypy.ini`; the README's "3.8+"
  is stale), but **bridge-side code runs on Cadwork's embedded interpreter**:
  3.10 for v30 (`EXE_30/Pclib.x64/python310`), 3.14 for 2026. Keep `bridge/`,
  `vestack/` and `cadwork_bridge.py` valid Python 3.10: no `typing.Self`,
  `except*`, `tomllib`. Cadwork provides the real
  `element_controller`, `geometry_controller`, `attribute_controller` and `cadwork`
  modules; the `cwapi3d` package provides stubs of the same names, so those imports
  also resolve outside Cadwork. The stubs type-check but do nothing, so an import
  succeeding proves nothing about a call working.
- `mcp` must stay below 2.0: the 2.x line removed `mcp.server.fastmcp`, which
  `main.py` and `core/server.py` import.
- The bridge is started by hand in Cadwork: **Window → Plugins → MCP Bridge → Start Bridge**. After editing bridge-side files, Stop/Start is not sufficient for already-imported modules — restart Cadwork.
- `stop_bridge()` in the plugin only flips a boolean; it neither closes the socket nor stops the daemon thread.

## Commands

Work in the project virtualenv. Installing the requirements into a global Python
upgrades `starlette`, `pydantic` and `typing_extensions` and will break unrelated
packages there.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

.venv\Scripts\python -m unittest discover -s tests -t .   # 78 tests, no Cadwork needed
.venv\Scripts\python -m unittest tests.test_module_inventory        # one module
.venv\Scripts\python -m unittest tests.test_dispatcher.Discovery.test_the_real_handler_modules_expose_ping
.venv\Scripts\python -m mypy .         # baseline: 13 errors in 4 files (all pre-existing)
.venv\Scripts\python main.py           # MCP server, stdio
.venv\Scripts\python main.py --transport http --port 8001
```

**The mypy baseline depends on the `cwapi3d` version.** The stubs define the
Cadwork API the handlers are checked against, so the pin must match the Cadwork
version you target:

- **v30 (2024)**: what `cwapi3d==30.693.0` pins. Handlers check clean (13 errors,
  all pre-existing).
- **33.0 "2026 BETA"**, in `EXE_2026` with its own `userprofil_2026`: no 33.x
  stubs on PyPI. Its embedded interpreter is **Python 3.14**
  (`EXE_2026/Pclib.x64/python314`), so bridge-side code runs there, not on the
  3.12 that `mypy.ini` declares.
- **32.x as an upgrade checklist**: the same code reports 97 errors, 56 of them
  "module has no attribute", i.e. what Cadwork 32 renamed or removed.

```powershell
.venv\Scripts\python -m pip install "cwapi3d==32.443.10"
.venv\Scripts\python -m mypy .    # then reinstall the pin from requirements.txt
```

**Wiring Claude Desktop.** `claude_desktop_config.json` is a template: replace
`PATH-TO-YOUR-CHECKOUT` with the checkout path. Its `command` points at the
virtualenv's interpreter; a bare `python` would run the server on the global
Python, without the pinned dependencies.

The suite runs **outside Cadwork** by stubbing it: `tests/stub_handlers*.py` stand in
for handler modules, and the Vestack adapter tests inject fake
`element_controller` / `geometry_controller` / `attribute_controller` modules into
`sys.modules`. That works only because every handler imports the Cadwork modules
*inside* its functions — keep it that way, or the tests stop being runnable.

Note `-t .`: the top-level directory must be the repo root for `bridge` and
`vestack` to be importable. The older test suite the README advertises (37/37,
25/25, …) was deleted in commit `8e01527` and is unrelated to these.

The root-level `validation_*.txt` files are historical batch-validation logs from earlier development (written in German), not runnable checks.

## Adding or changing a tool

One operation lives in **three** places, and all three must agree on the operation
name and the argument keys:

1. `bridge/handlers/<area>_handlers.py` — `handle_<operation>(args)`, the real
   Cadwork API call. Naming it this way is what registers it; the dispatcher needs
   no edit.
2. `controllers/<area>_controller.py` — an `async def` method that validates input
   and calls `self.send_command("<operation>", args)`.
3. `main.py` — an `@mcp.tool(name=..., description=...)` wrapper delegating to that
   controller.

Argument names are the wire contract: handlers read them with `args.get("...")`, so
renaming a controller parameter silently breaks the call. Two modules must not
define the same `handle_<operation>`; the first registration wins and the loser is
listed in `CommandDispatcher.collisions`.

## Domain extensions

Vestack-specific logic lives in `vestack/` and nothing generic depends on it. The
generic code references it exactly twice: `EXTENSION_MODULES` in
`bridge/dispatcher.py`, and the `get_module_inventory` tool plus its controller
import in `main.py`. `vestack/README.md` documents the modular conventions (module
id `M139` in a user attribute named "Module", dimensions derived from the bottom
floor, open-side detection) and how to remove the package. Keep new domain logic
there rather than in `bridge/handlers/`, and keep `vestack/module_inventory.py`
free of Cadwork imports so it stays unit-testable.

## Conventions

- MCP tools and controller methods are `async`; handlers are plain synchronous functions.
- Every return is `Dict[str, Any]`; failures come back as `{"status": "error", "message": ...}` instead of raising across the socket.
- Naming differs per layer: `controllers/` uses plain Python names, `bridge/handlers/` uses a prefix style (`aParams` for arguments, `lElementId` for locals). Match the file you are editing.
- All comments and docstrings in English.
- **Units are millimetres** throughout (cadwork's native unit); volume and weight conversions are explicit in `geometry_handlers.py`.
- Beam/panel geometry follows `config/cadwork_axis_config.py`: `p1`→`p2` is the longitudinal axis, `width` is the cross-section along X, `height` along Y. Vertical beams **must** vary Z between `p1` and `p2` — `create_beam` in `main.py` post-checks this and attaches an `axis_warning`. For panels, omitting `p3` when `p1`/`p2` are colinear yields a degenerate line, so pass `p3`.
- Several "advanced" tools (visual filters, assembly animation, walkthrough) are explicit placeholders in `visualization_handlers.py`.
- Code and docs are English, but `config/cadwork_axis_config.py:STANDARD_MATERIALS` deliberately maps to **German** cadwork material names (`SPRUCE → Fichte`, `LARCH → Lärche`). Material names are locale-dependent data, not text to translate — a French or English Cadwork profile will use different strings, so material filters written against these values are not portable.

## Aligning with the cadwork developer documentation

The authoritative reference is the cwapi3d Python documentation, <https://docs.cadwork.com/projects/cwapi3dpython/en/latest/> (sources: <https://github.com/cwapi3d/cwapi3dpython>). Check signatures there before adding or repairing a handler — this repo has drifted from it:

- `element_controller.create_auto_container_from_standard(element_id_list, output_name, standard_element_name)` takes **three** arguments upstream; this repo's controller passes two.
- `get_bounding_box` does not exist in cwapi3d's `geometry_controller` (upstream has `create_bounding_box_global/local`, which *create* elements). `geometry_handlers.handle_get_bounding_box` probes names with `hasattr` and falls back to min/max over `get_element_vertices` — that fallback is the path that actually runs.
- Group and subgroup reads go through `attribute_controller.get_group(element_id)` / `get_subgroup(element_id)`. Upstream has no "list the elements of a group" call, so `handle_get_elements_in_group` scans `ec.get_all_identifiable_element_ids()` and filters. The `*_statistics` handlers do the same — they are O(all elements) full-model scans.

## Documentation map

- `README.md` — English, canonical. Function counts and completion percentages are aspirational; see the phantom-tool list above.
- `README_DE.md` — the original German README, kept for reference only.
- `vestack/README.md` — the Vestack modular conventions and how to remove the extension.
- `bridge/ARCHITECTURE.md` — the abandoned "no handlers layer" refactor. History.
- `API.x64/MCPBridge/README.md` — installing the Cadwork plugin into the user profile's `3d\API.x64` directory.
- `.claude/skills/cadwork-model/SKILL.md` — how to drive a live model through the MCP: preflight, read-only inventory, and the guarded procedure for modifying elements.
