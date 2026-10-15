# Object inventory: Cadwork side of the Revit consistency check

Date: 15/10/2026. Status: design approved in conversation, spec under review.

## Context and goal

vCadworkMCP has three planned work packages, each separate:

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
discarded), its material, and the Module and Complexe attributes. Vertices are
kept so that every element can be re-expressed in its module frame. Local axes
are not needed: a floor subgroup holds dozens of elements (OSB, joists, I-joists)
and no single floor panel, so the frame is derived from the floor's vertices.

## The tool

```
get_object_inventory(
    element_ids: list[int] | None = None,   # scan these only
    active_only: bool = False,              # scan the current selection
    module_ids: list[str] | None = None,    # detail these modules
    element_detail: str = "none",           # "none" | "envelope" | "vertices"
    output_path: str | None = None,         # write the full inventory here
)
```

- `element_detail` applies to detailed modules only. `"envelope"` adds, under
  each object, its elements with their envelope in the module frame;
  `"vertices"` adds their vertices too. See "Drilling down to raw geometry".

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
only for elements of the requested modules and for joinery elements (which are
attached by geometry, whatever their module). Reading attributes model-wide
alone takes about 48 s on a 50 940-element model, beyond the 30 s socket
timeout of `core/connection.py`: `send_command` gains a per-call timeout, set to
15 min for this tool.

## Output format: `vestack.object_inventory/1`

One schema for the response and the file. Lengths in millimetres, rounded to
1 mm, expressed in the module frame unless the key ends in `_model`.

```json
{
  "status": "ok",
  "schema": "vestack.object_inventory/1",
  "source": {"file": "...", "extracted_at": "2026-10-15T14:02:00+02:00"},
  "modules": [{
    "module_id": "M1",
    "grouping_source": "subgroup",
    "frame": {
      "origin_model": [12450, 3200, 0],
      "x_axis_model": [0, 1, 0],
      "y_axis_model": [-1, 0, 0],
      "z_axis_model": [0, 0, 1],
      "length": 11980, "width": 3980, "height": 3150
    },
    "counts": {"wall": 6, "slab": 2, "opening": 3, "other": 0},
    "objects": [{
      "id": "M1-W5",
      "type": "wall",
      "wall_type": "MOB200", "stud_section": 200,
      "side": "-y",
      "start": [0, 0, 0], "end": [3645, 0, 0],
      "thickness": 212, "height": 2645,
      "openings": [{"id": "M1-W5-O1", "name": "MEX type B", "offset": 345, "sill": 90, "width": 1455, "height": 2315,
                    "element_ids": [10240]}],
      "element_ids": [10231, 10232],
      "warnings": []
    }, {
      "id": "M1-F1", "type": "slab", "level": "bottom",
      "origin": [0, 0, 0], "length": 11980, "width": 3980, "thickness": 250,
      "element_ids": [10101]
    }],
    "warnings": []
  }],
  "skipped_element_ids": []
}
```

`objects` is present only for detailed modules. Field meanings:

- `id` is the part subgroup (`M1-W5`) when the object was grouped by subgroup,
  and a generated `<module>-geo<n>` under the geometric fallback
  (`M1-geo1`); a stray joinery element reported as `other` is
  `<module>-joinery<element id>`.
- **wall**: `start`/`end` are the wall axis at its foot, at mid-thickness, as a
  Revit wall's location line. `wall_type` and `stud_section` come from the
  wall's `MOB<section>` body element, `null` without one. `side` is the footprint edge it stands on
  (`-x`, `+x`, `-y`, `+y` in the module frame), or `null` for an interior wall.
- **opening**: attached to its wall. `offset` runs from the wall's `start` along
  the wall axis to the opening's near edge; `sill` from the wall's foot.
- **slab**: `level` is `bottom` or `top`; `origin` is its min corner in the
  module frame.
- **roof** (`TF`, `C`, `T`), **parapet** (`A`), **other**: an envelope
  (`origin`, `size`), the `part` prefix when known, and `element_ids`.
- `element_ids` on every object let Claude have the modeller select the
  elements behind a discrepancy.
- `frame.origin_model` and the three `*_axis_model` unit vectors map the module
  frame to model coordinates and back: a model point `P` has module coordinates
  `((P - origin) · x, (P - origin) · y, (P - origin) · z)`. All three axes are
  given so the transform never has to be reconstructed.
- `extracted_at` is ISO 8601 in the file (machine-readable); French date format
  applies only to text shown to people.

The schema is documented in `vestack/OBJECT_INVENTORY.md`: the contract handed
to the Revit repository. Any incompatible change bumps the version suffix.

## Module frame

Computed from the module's bottom floor: the `F` subgroup whose group is
`Plancher bas` (or Complexe `PB-…`), else the lowest slab as `module_inventory`
finds it today:

1. **Orientation** from the minimum-area rectangle enclosing the bottom
   floor's vertices in plan (convex hull, then one candidate rectangle per hull
   edge): **X** along the rectangle's longer side; **Z** vertical; **Y**
   completes a right-handed frame. The hull area over the rectangle area is the
   plan-area ratio checked in rule 4.
2. **Origin** at the floor corner such that every floor vertex has x ≥ 0 and
   y ≥ 0; z at the underside of the floor.
3. **180° tie-break**: two frames satisfy rules 1 and 2. Keep the one whose X
   axis makes less than 90° with the model's +X; when both make 90° (within 1e-5 rad), keep
   the one whose X axis is +Y. The Revit side applies the same rule in its own model axes. If the
   building is rotated differently in Revit, a whole module shows up mirrored;
   `x_axis_model` lets Claude recognise that as one flip, not as dozens of
   discrepancies.
4. A floor that cannot be found, or whose plan area is well below its
   oriented footprint (`MIN_PLAN_AREA_RATIO`), yields a module **warning** and
   no objects. A wrong figure is never reported silently.

Expressing elements in this frame also removes the current limitation of
`module_inventory`, whose axis-aligned boxes overstate rotated modules.

## Vestack modelling conventions (observed in the spike)

Observed on `250513_AUX_STR_EXE_IndB.3d` (50 940 elements), Cadwork 2026. The
prefix meanings were inferred from groups, element names and the "Complexe"
attribute, as asked by the user; `W` and `F` were stated by the user.

**Module id.** Upper-case `M` followed by 1 to 4 digits, then end of
text or a separator (`-`, `_`, space). Leading zeros are dropped when
normalising, so `M001` and `M1` are the same module. Observed: `M1`, `M17`,
`M001`, `M007`, `M0`, `M15_W1`. Labels such as "Module standard R+1" or
"Module Façade Nord", also found in the Module attribute, are not ids: a digit
must follow the `M`. Lower-case `m` does not match, so "10 m2" in an element
name does not read as a module. This rule replaces `MODULE_ID_PATTERN` (`M\d{3}`), under
which `get_module_inventory` finds **no module at all** in this model.

**Where the id is read, in order:** the subgroup prefix, then the Module user
attribute, then the group. The element name is never read: hardware names carry
metric threads ("Tige filetée M12", "Boulon M16", "Vis M8 x 120") that would read
as modules M12, M16, M8. When subgroup and attribute
disagree (243 elements in the spike model), the subgroup wins and the module
carries a warning with the number of disagreeing elements.

**Part subgroups** are `<module id><separator><prefix><number?>`:

| Prefix | Object | Evidence |
|---|---|---|
| `W` | wall | group `MOB`, Complexe `OB-AUX-0x`; stated by the user |
| `F` | floor slab | groups `Plancher bas` / `Plancher haut`, Complexe `PB-…` / `PH-…`; stated by the user. Bottom or top is read from the group or Complexe, not the number |
| `TF` | cold roof (toiture froide) | group `Toiture froide`, trusses and purlins |
| `C` | cold-roof box (caisson) | group `Toiture froide`, elements named "Caisson toiture froide" |
| `T` | roof of a crowning module | group `Module de couronnement`, Complexe `CH-AUX-01` |
| `A` | parapet (acrotère) | group `Module de couronnement`, Complexe `AC-AUX-01`, elements named "Acrotères" |
| `Poteaux`, `Porteuses`, `fourrure` | posts, bearers, furring | named subgroups, no number; reported as `other` |

Prefixes live in `conventions.py`; an unknown prefix yields `other` and a
warning, never a dropped element.

**Wall body element.** Each wall subgroup holds exactly one element named after
the wall type, `MOB<section>` (wood-frame wall, stud section in mm: `MOB95`,
`MOB145`, `MOB200`), in 133 of 135 walls (one has none, one has two). Its
bounding box equals the union of the wall's elements in 4 walls out of 6
sampled; in the other 2 one element sticks out by 146 mm.

**Joinery.** Openings are explicit elements named `MEX type A`, `MEX type B`,
`MEX type D`, `MEX couloir`: a plain 8-vertex box. Most of them (535 of the
`MEX` group) have **no subgroup**; only 33 sit in a wall subgroup, and the one in
`M1-W5` is in group `MOB`, not `MEX`. They are therefore recognised by **name**,
and attached to walls by **geometry**. `MEX` accessories (Joue, Bavette,
Larmier, Habillage sous face) are not openings.

**Outside the part convention:** 16 931 elements have no subgroup; processings
(`Usinage …`, 14 477 elements in group `Usinage`), networks (`ELEC`, `MEP`) and
connectors have descriptive subgroups; some subgroups lack the module
(`W1`: 479, `F1`: 661) or the part (`M17`: 695).

## Grouping elements into objects

A chain of strategies tried in order per module. The strategy actually used is
reported in `grouping_source` (`subgroup` or `geometry`).

1. **Subgroup** (default): elements whose subgroup parses as a part subgroup
   form one object per subgroup, typed from its prefix. A subgroup without a
   module takes it from the Module attribute, or is reported unattached. A
   subgroup reduced to the module id (`M17`) goes through the fallback.
   Processing-only elements (group `Usinage`) are excluded from envelopes.
2. **Geometric fallback**, for modules or elements the subgroup does not cover:
   - exterior walls: elements lying within `SIDE_BAND_MM` (400 mm) of a floor
     edge form the wall of that side;
   - slabs: horizontal bands at the bottom and at the top of the module
     (`TOP_FLOOR_MIN_CLEARANCE_MM`);
   - interior walls: remaining vertical elements, clustered by shared plane and
     contiguity;
   - the rest becomes `other`.

**Wall envelope.** When a wall has one `MOB<section>` element, the wall's
`start`, `end`, `thickness` and `height` come from that element, and the wall
reports `wall_type` (`MOB200`) and `stud_section` (200). The union of all the
wall's elements is computed too; if it exceeds the body by more than a
tolerance in `conventions.py`, the wall carries a warning naming the
protruding elements. Without exactly one body element, the union is used and
the wall is warned.

**Openings.** A joinery element (name matching the `MEX` patterns in
`conventions.py`) is attached to the wall whose body box contains its centre,
in the module frame, whatever its subgroup. Its box gives `offset`, `sill`,
`width` and `height`. A joinery element contained in no wall is reported as
`other` with a warning. A wall with no attached joinery simply has an empty
`openings` list: the spike showed openings are always modelled as joinery
elements, so the `openings not detected` warning is dropped.

A long side split into several panels yields one wall per subgroup, and one per
side by geometric fallback. Such cutting differences are left to Claude's
comparison rather than normalised here.

## Drilling down to raw geometry

The inventory is a summary of the model, not a replacement for it. When an
object's envelope does not explain a discrepancy (a sloped wall, an opening
found as a processing, a module the grouping got wrong), Claude must be able to
go back to the elements themselves, through the same MCP server, without a new
export. Three levels, from cheapest to most detailed:

1. **Element detail in the module frame**: `get_object_inventory(module_ids=[...],
   element_detail="envelope" | "vertices")`. Under each object, an `elements`
   list gives `element_id`, `name`, `material`, and the element's
   envelope (`origin`, `size`) or vertices **already expressed in the module
   frame**, so they compare directly with the Revit side. This is the
   recommended level: no coordinate arithmetic is left to Claude.
2. **Raw element geometry in model coordinates**, through the existing
   read-only tools, using the `element_ids` every object carries:
   `get_element_info` (name, group, material, p1/p2/p3, local axes),
   `get_element_vertices`, `get_element_facets`, `get_bounding_box`,
   `get_element_length`/`width`/`height`, `get_minimum_distance_between_elements`.
   The `frame` block converts these coordinates to the module frame.
3. **Selection in Cadwork**: the modeller selects what Claude points at by
   `element_ids`, then Claude reads it with `get_active_element_ids`. This is
   also how the grouping is corrected when it put an element in the wrong object.

The `cadwork-model` skill documents this drill-down order: inventory summary,
then module detail, then element detail, then raw tools.

## Errors and warnings

- Failures return `{"status": "error", "message": ...}`; a stopped bridge gives
  `Connection failed`, as for every other tool.
- A problematic module (no floor, non-rectangular floor, empty grouping) never
  fails the inventory: it carries its `warnings` and the rest is exported.
- Elements without readable geometry go to `skipped_element_ids`.
- `output_path` that cannot be written returns an error and no partial file.
- **The bridge does not answer while a Cadwork command is active** (observed in
  the spike: even `ping` timed out until the modeller pressed Escape). A timeout
  is reported as "Cadwork may be in an active command: press Escape", not as a
  dead bridge.

## Compatibility

- Bridge-side code (`vestack/`, `bridge/`) stays valid **Python 3.10** (Cadwork
  v30) and must run on **Python 3.14** (Cadwork 2026, used in production).
- The `cwapi3d` pin stays on v30: PyPI has no 33.x stubs. Every Cadwork API
  function called by the new code is checked against the current cwapi3d
  documentation before use, then against a live 2026 model.
- **Verified in the spike**: the plugin loads and the bridge runs under
  Cadwork 2026 (Python 3.14). Read calls used by the inventory work:
  `get_all_element_ids`, `get_active_element_ids`, `get_standard_attributes`,
  `get_user_attributes`, `list_defined_user_attributes`, `get_element_info`,
  `get_element_vertices`, `get_3d_file_path`.
- **Broken under 2026**, found in the spike: `get_project_data` (the 2026
  function takes a `str` argument the handler does not pass),
  `get_version_info` (`utility_controller.get_cadwork_version_info` is gone),
  `get_element_type` (`element_controller.get_element_type` is gone). The
  inventory must not depend on them. `element_detail` therefore omits the
  element type until its 2026 replacement is confirmed in the cwapi3d
  documentation.

## Testing

All runnable outside Cadwork, in the existing `unittest` suite:

- `object_inventory` on fabricated snapshots: aligned module; module rotated by
  90° and by 37°; the 180° tie-break, including the exact-90° case; L-shaped
  floor (warning, no objects); subgroup grouping for every prefix in the table;
  unknown prefix; subgroup without module; subgroup reduced to the module;
  side-band fallback; interior wall; wall body from its `MOB` element, union
  overshoot warning, zero or two body elements; joinery without subgroup
  attached to its wall by geometry, with correct `offset` and `sill`; joinery in
  no wall; open side.
- Module ids: `M1`, `M17`, `M001` = `M1`, `M15_W1`, `M139`; "Module standard
  R+1" rejected; subgroup and attribute disagreeing.
- Element detail: on a rotated module, element envelopes and vertices in the
  module frame match the model coordinates transformed with the `frame` block;
  an object's envelope equals the union of its elements' envelopes.
- A golden JSON file pinning schema `vestack.object_inventory/1`.
- Controller: file written only with `output_path`; summary versus detail;
  `module_ids` filter; unwritable path returns an error and leaves no file.
- Bridge adapter, with fake Cadwork modules injected into `sys.modules` as the
  existing Vestack adapter tests do: vertices and local axes reach the snapshots.
- Discovery: `get_object_inventory` appears in
  `CommandDispatcher().diagnostics()`.
- `get_module_inventory` adopts the relaxed module id rule and reports ids in
  canonical form (`M001` becomes `M1`): its tests asserting zero-padded ids are
  updated accordingly, the others pass unchanged.

## Spike results (15/10/2026)

Read-only, on a copy of `250513_AUX_STR_EXE_IndB.3d` in Cadwork 2026, through a
throwaway client speaking the bridge protocol (the MCP tools were not loaded in
that session). No write operation was sent.

1. **Grouping key: the subgroup.** The wall the modeller selected (39 elements)
   is exactly subgroup `M1-W5` (39 elements). Conventions: see "Vestack
   modelling conventions".
2. **Openings: explicit joinery elements**, mostly outside wall subgroups; see
   above.
3. **Timing**: element ids 0,1 s; name/group/subgroup/comment for all 50 940
   elements 44 s; four user attributes 3,7 s; vertices 14 ms per element
   (measured on 39), i.e. about 17 s for a module of 1 200 elements and about
   12 min for the whole model (extrapolated). Hence per-module detail, with
   attributes read model-wide and vertices only where needed.
4. **Python 3.14**: the bridge runs; three handlers are broken by API changes
   (see Compatibility).

## Documentation to update

- `vestack/OBJECT_INVENTORY.md` (new): the schema, for the Revit side.
- `vestack/README.md`: the new inventory, its files and limitations.
- `.claude/skills/cadwork-model/tool-inventory.md` and `SKILL.md`: the new tool
  and the drill-down order (summary, module detail, element detail, raw tools).
- `CLAUDE.md`: production runs on Cadwork 2026; the new tool and its operation.
