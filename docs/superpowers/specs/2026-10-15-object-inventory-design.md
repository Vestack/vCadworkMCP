# Object inventory: Cadwork side of the Revit consistency check

Date: 15/10/2026. Status: design approved in conversation, spec under review.

## Context and goal

cadworkMCP has three planned work packages, each separate:

1. **Positions** (this spec): let Claude check that the elements of a Cadwork
   model are the same as in the Revit model of the same project.
2. GCode generated from the model, replacing today's WUP export then conversion.
3. A design-office assistant.

Package 1 is split across two MCP servers. A Revit MCP exists in another
repository and needs completing; it is out of scope here. **This spec covers the
Cadwork side only**: extracting, from a live Cadwork model, a list of objects
(walls, slabs, openings) described by their envelope, in a neutral format that
the Revit side can reproduce. Claude compares the two lists itself: the
differences to find (a wall split in two on one side, an opening shifted on the
other) need the generalisation of an LLM more than a fixed-rule comparator.

Facts this design rests on, as stated by the user:

- Every element present on both sides is to be compared, at **object-envelope**
  level: one Revit wall corresponds to the set of Cadwork elements (studs,
  plates, sheathing) that make up that wall.
- The Cadwork model is drawn from 2D plans. **No identifier is shared** with
  Revit, so matching is geometric.
- Comparison happens **per module**, in a frame local to each module, which
  removes any dependency on the two models sharing a global origin.
- A Cadwork file holds a **whole building**, modules at their real position, in
  varying orientations.
- The design office works on **Cadwork 2026** in production.

## Scope

In scope: one read-only MCP tool, `get_object_inventory`, its bridge operation,
the pure logic behind it, an optional JSON file export, and the schema document
the Revit side implements.

Out of scope: the Revit MCP, the comparison itself, any write to the Cadwork
model, and packages 2 and 3.

## Architecture

```
get_object_inventory            main.py, @mcp.tool
        |
vestack/mcp_controller.py       send_command("get_object_inventory", args)
        |                       writes the JSON file when output_path is given
        |  TCP 53002
vestack/bridge_handler.py       reads the model: attributes, vertices, local axes
        |                       builds snapshots (plain values, no Cadwork objects)
vestack/object_inventory.py     PURE: modules -> module frame -> grouping ->
        |                       envelopes -> warnings
vestack/conventions.py          grouping key, thresholds, tolerances
```

Everything stays in `vestack/`, following the rule in `vestack/README.md`:
domain logic there, pure modules free of Cadwork imports, the bridge adapter
importing Cadwork inside its functions only.

**Reuse, not duplication.** Module identification (`detect_id_source`,
`extract_module_id`), element classification (`classify`) and the side-band
logic of `open_sides` come from `vestack/module_inventory.py`. Functions both
inventories need move to a shared place if they must change; the existing
`get_module_inventory` keeps its behaviour and its tests.

**Snapshots gain geometry.** `ElementSnapshot` holds an axis-aligned bounding box
in model axes only. The object inventory needs, per element, its **vertices**
(already read by `element_bbox` through `gc.get_element_vertices`, then
discarded) and, for floor panels, the **local axes** (`gc.get_xl`, `gc.get_yl`,
`gc.get_zl`, as used in `bridge/handlers/element_handlers.py`). Vertices are kept
so that every element can be re-expressed in its module frame.

## The tool

```
get_object_inventory(
    element_ids: list[int] | None = None,   # scan these only
    active_only: bool = False,              # scan the current selection
    module_ids: list[str] | None = None,    # detail these modules
    output_path: str | None = None,         # write the full inventory here
)
```

- No `module_ids`: the response is the **summary** for every module found: its
  frame, object counts per type, warnings.
- With `module_ids`: the response adds the **detail** (every object) of those
  modules only.
- With `output_path`: the controller requests the full detail of every module,
  writes it as JSON to that path, and returns the summary plus the path. The
  file is written by the MCP server, never by the bridge, which stays read-only.
  The file is written only when `output_path` is given explicitly.

This keeps a whole building out of Claude's context: Claude reads the summary,
picks the modules worth checking, then asks for their detail. The file is the
exhaustive, reproducible record of what was compared.

Cost: one vertex query per scanned element, as today. With `module_ids`,
attributes are read for every scanned element (to find the modules), vertices
only for elements of the requested modules. The full export of a building stays
slow; its duration is measured during the spike.

## Output format: `vestack.object_inventory/1`

One schema for the response and the file. Lengths in millimetres, rounded to
1 mm, expressed in the module frame unless the key ends in `_model`.

```json
{
  "status": "ok",
  "schema": "vestack.object_inventory/1",
  "source": {"file": "...", "cadwork_version": "...", "extracted_at": "2026-10-15T14:02:00+02:00"},
  "modules": [{
    "module_id": "M139",
    "grouping_source": "subgroup",
    "frame": {
      "origin_model": [12450, 3200, 0],
      "x_axis_model": [0, 1, 0],
      "length": 11980, "width": 3980, "height": 3150
    },
    "counts": {"wall": 6, "slab": 2, "opening": 3, "other": 0},
    "objects": [{
      "id": "M139-W1",
      "type": "wall",
      "side": "-y",
      "start": [0, 0, 0], "end": [11980, 0, 0],
      "thickness": 220, "height": 2900,
      "openings": [{"id": "M139-W1-O1", "offset": 1200, "sill": 900, "width": 1000, "height": 1250}],
      "element_ids": [10231, 10232],
      "warnings": []
    }, {
      "id": "M139-S1", "type": "slab", "level": "bottom",
      "origin": [0, 0, 0], "length": 11980, "width": 3980, "thickness": 250,
      "element_ids": [10101]
    }],
    "warnings": []
  }],
  "skipped_element_ids": []
}
```

`objects` is present only for detailed modules. Field meanings:

- **wall**: `start`/`end` are the wall axis at its foot, at mid-thickness, as a
  Revit wall's location line. `side` is the footprint edge it stands on
  (`-x`, `+x`, `-y`, `+y` in the module frame), or `null` for an interior wall.
- **opening**: attached to its wall. `offset` runs from the wall's `start` along
  the wall axis to the opening's near edge; `sill` from the wall's foot.
- **slab**: `level` is `bottom` or `top`; `origin` is its min corner in the
  module frame.
- **other**: an envelope (`origin`, `size`) and its `element_ids`.
- `element_ids` on every object let Claude have the modeller select the
  elements behind a discrepancy.
- `frame.origin_model` and `x_axis_model` map the module frame back to model
  coordinates.
- `extracted_at` is ISO 8601 in the file (machine-readable); French date format
  applies only to text shown to people.

The schema is documented in `vestack/OBJECT_INVENTORY.md`: the contract handed
to the Revit repository. Any incompatible change bumps the version suffix.

## Module frame

Computed from the module's bottom floor, which `module_inventory` already finds:

1. **Orientation** from the floor panel's local axes: **X** along its longer
   side, projected onto the horizontal plane; **Z** vertical; **Y** completes a
   right-handed frame.
2. **Origin** at the floor corner such that every floor vertex has x ≥ 0 and
   y ≥ 0; z at the underside of the floor.
3. **180° tie-break**: two frames satisfy rules 1 and 2. Keep the one whose X
   axis makes less than 90° with the model's +X; when both make exactly 90°, keep
   the one whose X axis is +Y. The Revit side applies the same rule in its own model axes. If the
   building is rotated differently in Revit, a whole module shows up mirrored;
   `x_axis_model` lets Claude recognise that as one flip, not as dozens of
   discrepancies.
4. A floor that cannot be found, or whose plan area is well below its
   oriented footprint (`MIN_PLAN_AREA_RATIO`), yields a module **warning** and
   no objects. A wrong figure is never reported silently.

Expressing elements in this frame also removes the current limitation of
`module_inventory`, whose axis-aligned boxes overstate rotated modules.

## Grouping elements into objects

A chain of strategies, configured in `conventions.py`, tried in order per module.
The strategy actually used is reported in `grouping_source`.

1. **Field key**: elements of a module sharing the same value of a configured
   field (group, subgroup or a user attribute) form one object. Its type follows
   from the group's envelope in the module frame: thin and vertical is a wall,
   thin and horizontal a slab, anything else `other`. **Which field is the
   default is decided by the spike.** An empty or missing key falls through.
2. **Geometric fallback**:
   - exterior walls: elements lying within `SIDE_BAND_MM` (400 mm) of a floor
     edge form the wall of that side;
   - slabs: horizontal bands at the bottom and at the top of the module
     (`TOP_FLOOR_MIN_CLEARANCE_MM`);
   - interior walls: remaining vertical elements, clustered by shared plane and
     contiguity;
   - the rest becomes `other`.
3. **Openings**: version 1 detects explicit elements only (joinery elements
   lying inside a wall). If none is found on a wall, the wall carries the
   warning `openings not detected` rather than an empty list that would read as
   a solid wall. **Whether openings must also be read from processings or from
   gaps between studs is decided by the spike.**

A long side split into several panels yields one wall by geometric fallback and
possibly several by field key. Such cutting differences are left to Claude's
comparison rather than normalised here.

## Errors and warnings

- Failures return `{"status": "error", "message": ...}`; a stopped bridge gives
  `Connection failed`, as for every other tool.
- A problematic module (no floor, non-rectangular floor, empty grouping) never
  fails the inventory: it carries its `warnings` and the rest is exported.
- Elements without readable geometry go to `skipped_element_ids`.
- `output_path` that cannot be written returns an error and no partial file.

## Compatibility

- Bridge-side code (`vestack/`, `bridge/`) stays valid **Python 3.10** (Cadwork
  v30) and must run on **Python 3.14** (Cadwork 2026, used in production).
- The `cwapi3d` pin stays on v30: PyPI has no 33.x stubs. Every Cadwork API
  function called by the new code is checked against the current cwapi3d
  documentation before use, and against the live 2026 model during the spike.
- **Unverified**: the bridge has probably never run under Cadwork 2026. The
  only compiled file in the 2026 profile is `MCPBridge.cpython-312.pyc`, likely
  produced by the repository's 3.12 virtualenv rather than by Cadwork.

## Testing

All runnable outside Cadwork, in the existing `unittest` suite:

- `object_inventory` on fabricated snapshots: aligned module; module rotated by
  90° and by 37°; the 180° tie-break, including the exact-90° case; L-shaped
  floor (warning, no objects); field-key grouping; side-band fallback; interior
  wall; opening attached to its wall with correct `offset` and `sill`; open side;
  `openings not detected` warning.
- A golden JSON file pinning schema `vestack.object_inventory/1`.
- Controller: file written only with `output_path`; summary versus detail;
  `module_ids` filter; unwritable path returns an error and leaves no file.
- Bridge adapter, with fake Cadwork modules injected into `sys.modules` as the
  existing Vestack adapter tests do: vertices and local axes reach the snapshots.
- Discovery: `get_object_inventory` appears in
  `CommandDispatcher().diagnostics()`.
- Existing `get_module_inventory` tests still pass unchanged.

## Spike (first task of the plan)

Read-only, on a **copy** of a representative Vestack model, in **Cadwork 2026**,
through this MCP server registered in Claude Code. Select one complete wall,
then two neighbouring walls; read `get_element_info`, `get_user_attributes`,
`list_defined_user_attributes` and `get_module_inventory` on each selection. No
write tool is called. It settles:

1. the default grouping key (a field constant within a wall and different
   between two walls), or the absence of one;
2. how openings exist in the model;
3. how long reading a building takes;
4. whether the bridge runs under Python 3.14.

Work that does not depend on these answers (module frame, geometric fallback,
schema, controller, file export) can proceed before the spike.

## Documentation to update

- `vestack/OBJECT_INVENTORY.md` (new): the schema, for the Revit side.
- `vestack/README.md`: the new inventory, its files and limitations.
- `.claude/skills/cadwork-model/tool-inventory.md` and `SKILL.md`: the new tool
  and how to use summary versus detail.
- `CLAUDE.md`: production runs on Cadwork 2026; the new tool and its operation.
