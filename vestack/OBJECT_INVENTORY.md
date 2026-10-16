# Object inventory schema: `vestack.object_inventory/1`

The structure returned by `get_object_inventory`. It is the contract between the
Cadwork side (this repository) and the Revit side, which must produce the same
structure from the Revit model so that Claude can compare the two.

Two things carry this structure:

- The **bridge operation** `get_object_inventory` (runs inside Cadwork) returns it
  as described in the sections below.
- The **MCP tool** `get_object_inventory` (`vestack/mcp_controller.py`) returns the
  bridge response unchanged, except when `output_path` is given. Then it writes a
  JSON file and returns a summary; see "Export file".

Design: `docs/superpowers/specs/2026-10-15-object-inventory-design.md`.
Reference output: `tests/data/object_inventory_golden.json`.

## Units and frames

- Lengths in **millimetres**, rounded to 1 mm (integers). Axis vectors are unit
  vectors rounded to 6 decimals.
- Every coordinate is in the **module frame** unless its key ends in `_model`.
- Module frame: origin at the floor corner from which every bottom-floor vertex
  has x >= 0 and y >= 0, at the underside of the floor. **X** runs along the longer
  side of the minimum-area rectangle enclosing the bottom floor in plan; **Z** up;
  **Y** = Z × X (right-handed).
- Of the two frames that satisfy this (180° apart), keep the one whose X axis
  makes less than 90° with the model's +X. When X is within 1e-5 rad of
  perpendicular to the model's +X, X is +Y. When X is within 1e-5 rad of a model
  axis, it is snapped to that axis, so `x_axis_model` then reads exactly 0 and 1.
  The Revit side applies the same rule in its own model axes.
- A model point `P` has module coordinates
  `((P - origin_model) · x_axis_model, (P - origin_model) · y_axis_model, (P - origin_model) · z_axis_model)`.

## Top level

| Key | Meaning |
|---|---|
| `status` | `"ok"`, or `"error"` with a `message`: the scan failed, `element_detail` is not `none`, `envelope` or `vertices`, or (MCP tool only) the bridge did not answer the `ping` sent before the scan, the `output_path` directory does not exist, or the export file could not be written |
| `schema` | `"vestack.object_inventory/1"`; bumped on any incompatible change |
| `source` | `file` (path of the open model, empty if unavailable), `extracted_at` (ISO 8601 with offset, seconds) |
| `modules` | one entry per module found, sorted by module number |
| `unattached_element_count` | number of unattached elements, always present |
| `unattached_element_ids` | elements with no module; joinery with no module, no readable geometry, or whose module has no frame. Sorted. When no module is detailed (no `module_ids`, no `detail_all`), only the first 200 ids are listed; the same cap applies to the summary the MCP tool returns with an export that names no module, while the file lists them all |
| `unattached_element_ids_truncated` | `true` when `unattached_element_ids` lists fewer ids than `unattached_element_count`; always `false` in a detail and in the export file. In the MCP tool's response to an export that names no module, `true` when it dropped ids beyond the first 200 |
| `processing_element_count` | processing elements (group `Usinage`), counted but never in an object |
| `warnings` | e.g. `module M5 not found in the scanned elements` for a requested module |
| `scanned_element_count`, `geometry_read_count`, `skipped_element_ids`, `attribute_numbers` | Cadwork side only: scan statistics |
| `output_path` | MCP tool only, present only with an export: absolute path of the file written |

## Export file

`output_path` is an argument of the MCP tool, not of the bridge operation.

With `output_path`, the MCP controller asks the bridge for every module in detail
(`detail_all`). The file therefore holds `objects` for every module, with
`elements` at the requested `element_detail`. It has the structure of the bridge
response, scan statistics included, without the `output_path` key. It is JSON,
UTF-8, indented by one space, written atomically: a temporary file in the target
directory, then `os.replace`. When the write fails, the tool returns
`status: "error"` with a message and leaves no partial file; a file already at that
path stays as it was. When the scan itself fails, the error response is returned
and nothing is written. Before the scan, the tool checks that the directory of
`output_path` exists (`output_path directory does not exist: <dir>` otherwise)
without contacting the bridge. Every call, export or not, first pings the bridge
with the default socket timeout (30 s) and returns the ping's error without
scanning when it fails, typically while a Cadwork command is active. The path is
resolved on the machine running the MCP server
(a relative path against that process's working directory).

Without `output_path`, nothing is written.

With an export, the tool's response is the same structure as the file, with these
differences:

- `objects` (and so `elements`) is dropped from every module except those named in
  `module_ids` (any spelling, `M001` means `M1`), which keep it;
- `output_path` is added.

Because every module was read in detail, that summary carries the detail `counts`
(geometry-grouped objects included) and, for a module with a frame, `frame.height`, and its modules have no
`unclassified_element_count` or `unplaced_joinery_ids`. Unattached ids follow the
summary rule: when `module_ids` names no module present in the inventory, the response
lists the first 200 (sorted) and sets `unattached_element_ids_truncated` to `true` if
it dropped any; otherwise it lists them all, as the file does. The file always lists
every id.

## Module entry

| Key | Meaning |
|---|---|
| `module_id` | canonical id: `M` + number without leading zeros (`M001` → `M1`). Only an upper-case `M` is read: `m1` is not a module id. An element's module is read from its subgroup, then its `Module` attribute, then its group; never from its name, where `Tige filetée M12` is a thread size. |
| `grouping_source` | `"subgroup"`, `"geometry"`, `"subgroup+geometry"`, or `null`; read on every element attributed to the module, those outside its envelope included, so that a summary and a detail report the same value |
| `frame` | `origin_model`, `x_axis_model`, `y_axis_model`, `z_axis_model`, `length` (along X), `width` (along Y), `height` (top of the module's elements above the origin, elements outside the envelope left out). `null` when there is no bottom floor, or it fills less than 80% of its enclosing rectangle. `height` is `null` in summarised modules: only detailed modules compute it. |
| `counts` | objects per type: `wall`, `slab`, `roof`, `parapet`, `other`, `opening`. `opening` and `other` are always present, other types only when they occur. Subgroup parts count even when their geometry was not readable or every element lies outside the envelope. In a summarised module, `counts` cover subgroup parts and the openings of subgroup walls only: a module with `grouping_source` `"geometry"` shows zero counts in a summary and its real counts in the detail. |
| `warnings` | module-level problems, never dropped silently. Includes `unknown part prefixes reported as other: <prefixes>`; `<n> elements have a Module attribute that disagrees with their subgroup; the subgroup was used`; `no bottom floor found: no frame, no objects`; `bottom floor fills <n>% of its enclosing rectangle: not rectangular, objects omitted`; `<n> elements attributed to <module> lie outside its envelope and were left out`; and, in detailed modules, `<id>: no readable geometry, omitted` or `<id>: every element lies outside the module envelope, omitted` for each object dropped. |
| `outside_element_count` | present when the module has a frame: number of its elements found outside its envelope (see "Module envelope") |
| `outside_element_ids` | present when the module has a frame: those elements, sorted, the first 200 only, in a summary, a detail and the export file alike |
| `outside_element_ids_truncated` | present when the module has a frame: `true` when `outside_element_ids` lists fewer ids than `outside_element_count` |
| `objects` | detailed modules only; empty when the module has no usable frame |
| `unclassified_element_count` | summarised modules only: elements left to the geometric fallback, those found outside the envelope excluded |
| `unplaced_joinery_ids` | summarised modules only: joinery of this module, with readable geometry, not attached to a subgroup wall. The detail places it in a fallback wall or reports it as `other`. |

## Module envelope

A module's envelope is its bottom floor's footprint in plan, `[0, length] x [0,
width]` in the module frame, enlarged by `MODULE_ENVELOPE_TOLERANCE_MM` (150 mm) on
every side, at any height. It is the perimeter rule of the module-derivation spec.
An element attributed to the module, in a part subgroup or loose, whose box
centre lies outside the envelope is left out of the module: of its objects, its
geometric fallback, its walls (and so the openings they take) and its
`frame.height`. It is listed in `outside_element_ids` and counted in
`outside_element_count`, with the module warning above. Typical cases: a batten of
another module filed in this module's wall subgroup, or a loose element whose
`Module` attribute names this module but which lies elsewhere in the building.

Only an element whose vertices were read can be tested; the others stay in the
module as before. A detailed module reads every element, so its outside list is
complete. A summary reads only bottom floors, wall bodies and joinery (plus every
element of a module with no usable floor part), so its outside list covers those
elements only, and an element found outside in the detail can still count in the
summary's `unclassified_element_count`.

## Objects

Every object has `id`, `type`, `element_ids` (sorted) and `warnings`. Object
`warnings` carry the object's own problems: a wall body count (`<n> wall body
elements (MOB<section>)...`), elements sticking out of the wall body (`elements
stick out of the wall body by up to <n> mm: [<ids>]`), `grouped by
geometry (<label>)`, `unknown part prefix '<prefix>': reported as other`, and
`joinery '<name>' lies in no wall`.

A warning that embeds an id list shows at most the first 10 ids, sorted; a longer
list ends with `... (<N> in total)`, e.g. `[13, 14, ..., 22] ... (15 in total)`
with the ten ids written out.

`id` is:
- `<module id>-<prefix as written><number as written>` for subgroup parts, with the
  module id in canonical form: the subgroup `M001-W05` gives `M1-W05`. A bare
  subgroup such as `W1` takes its module from the `Module` attribute (then from the
  element's group, never its name), so `W1` of module 1 gives `M1-W1`;
- `M1-geo<n>` for geometric fallback groups. `n` counts the groups that exist in
  that module from 1, in this order: bottom slab, top slab, side walls (`-x`, `+x`,
  `-y`, `+y`), interior walls (by smallest element id), other;
- `M1-joinery<element id>` for joinery lying in no wall.

Objects are listed in this order: subgroup parts (by prefix, case-insensitive,
then by number), geometric fallback groups (by `n`), stray joinery (in the order
the elements were scanned).

### Geometric fallback

Elements of a module outside any part subgroup are grouped by geometry, in detailed
modules only; a summary counts them as `unclassified_element_count`. Elements
without readable vertices, and those outside the module envelope, take no part.
Each element goes to the first rule that
fits:

1. Element of the bottom floor: the bottom slab.
2. Box entirely within `SIDE_BAND_MM` (400 mm) of a floor edge, on either side of
   it (for `-x`: `x >= -400` and `x <= 400` over the whole box; tested in the order
   `-x`, `+x`, `-y`, `+y`): the wall of that side, plates included.
3. Slab-shaped (thinnest along Z, thickness at most half the middle dimension) and
   with a plan width, the smaller of its X and Y sizes, above
   `WALL_MAX_THICKNESS_MM` (600 mm): the top slab when its underside is at least
   `TOP_FLOOR_MIN_CLEARANCE_MM` (500 mm) above the top of the bottom floor, else the
   bottom slab.
4. Upright, that is height at least `WALL_MIN_HEIGHT_MM` (1000 mm) and smaller plan
   side at most `WALL_MAX_THICKNESS_MM`: an interior wall.
5. Anything else, interior plates included: `other` (one object).

Interior walls are built per axis (X or Y). On axis X, only upright elements whose
Y size is at most `WALL_MAX_THICKNESS_MM` can join, and conversely for Y. Two such
elements share a wall plane when their box centres lie within
`INTERIOR_WALL_PLANE_TOLERANCE_MM` (100 mm) across the wall and the gap between
their extents along the wall is at most `INTERIOR_WALL_GAP_MM` (600 mm; 0 when they
overlap). The relation is closed transitively. An element can qualify for both
axes. The groups found on both axes are then served longest extent first (ties: X
before Y, then smallest element id), and each takes the elements the longer groups
left. Each element belongs to one wall; an L-shaped corner goes to the longer
branch.

A fallback wall has no single body: `wall_type` and `stud_section` are `null`, with
the wall body count warning, unless exactly one of its elements is named
`MOB<section>`.

**wall**

| Key | Meaning |
|---|---|
| `start`, `end` | wall axis at its foot, at mid-thickness; `start` is the end with the smaller coordinate along the wall |
| `thickness`, `height` | of the wall body (the union of the wall's elements when it has no single body) |
| `side` | footprint edge it stands on, from the wall's mid-thickness line: `-x`, `+x` for a wall running along Y, `-y`, `+y` for a wall running along X. `null` when that line lies more than `SIDE_BAND_MM` (400 mm) from both edges parallel to the wall. A fallback interior wall gets a side by the same test, so one whose line lies within the band has one. |
| `wall_type`, `stud_section` | from the single `MOB<section>` body element: `wall_type` is its name with surrounding spaces stripped, `stud_section` the section as an integer (`"MOB200"` and `200`). The name pattern accepts `MOB 200` and any case, so `wall_type` can keep an inner space or lower case. Both `null` when the wall has no body element or more than one (a warning gives the count). |
| `openings` | see below |

**opening** (inside a wall's `openings`)

A joinery element (name `MEX type ...` or `MEX couloir`) belongs to the wall whose
body contains its box centre, within `JOINERY_CENTRE_TOLERANCE_MM` (50 mm).
Adjacent modules share wall planes, so a centre can fit a wall of each: the walls
of the joinery's own module (subgroup, then `Module` attribute, then group) are
tried first, then those of the other modules in numeric order. Subgroup walls of
every module are tried before the fallback walls of detailed modules.

A window or door is drawn as several joinery elements of one name (frame, sash,
glazing, about twelve for a `MEX type B`). On one wall, joinery elements with the
same name (surrounding spaces stripped) whose boxes touch or overlap, within
`JOINERY_CENTRE_TOLERANCE_MM` (50 mm) on every axis, make one opening. The relation
is closed transitively. Two windows of the same name further apart than 50 mm stay
two openings; overlapping elements of different names stay apart. `counts.opening`
counts openings, not joinery elements.

| Key | Meaning |
|---|---|
| `id` | `<wall id>-O<n>`, numbered by increasing `offset`, then by smallest element id |
| `name` | joinery name with surrounding spaces stripped, e.g. `"MEX type B"` |
| `offset` | from the wall's `start`, along the wall, to the opening's near edge |
| `sill` | from the wall's foot to the bottom of the opening |
| `width`, `height` | of the union of the opening's joinery boxes; `width` runs along the wall |
| `element_ids` | every joinery element of the opening, sorted |

**slab**: `level` (`"bottom"` or `"top"` from the group or Complexe code, `PB-` /
`PH-`; otherwise `"bottom"` for the bottom floor, else `null`; a fallback slab
always has the level of its group), `origin` (min corner), `length` (along X),
`width` (along Y), `thickness`.

**roof**, **parapet**, **other**: `part` (the subgroup prefix as written, e.g.
`"TF"`, `"Poteaux"`; `null` for fallback objects and stray joinery), `origin`
(min corner), `size` (`[x, y, z]`).

## Element detail

With `element_detail="envelope"` or `"vertices"`, each object of a detailed
module carries `elements`: `element_id`, `name`, `material` (empty when the
element has none), `origin`, `size` (the element's box in the module frame), plus
`vertices` (module frame) for `"vertices"`. Elements without readable vertices are
left out. With `"none"` there is no `elements` key. The element type is omitted
until its Cadwork 2026 API is confirmed.
