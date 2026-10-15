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
| `status` | `"ok"`, or `"error"` with a `message`: the scan failed, `element_detail` is not `none`, `envelope` or `vertices`, or (MCP tool only) the export file could not be written |
| `schema` | `"vestack.object_inventory/1"`; bumped on any incompatible change |
| `source` | `file` (path of the open model, empty if unavailable), `extracted_at` (ISO 8601 with offset, seconds) |
| `modules` | one entry per module found, sorted by module number |
| `unattached_element_count` | number of unattached elements, always present |
| `unattached_element_ids` | elements with no module; joinery with no module, no readable geometry, or whose module has no frame. Sorted. When no module is detailed and there is no export (no `module_ids`, no `detail_all`), only the first 200 ids are listed |
| `unattached_element_ids_truncated` | `true` when `unattached_element_ids` lists fewer ids than `unattached_element_count`; always `false` in a detail or an export |
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
and nothing is written. The path is resolved on the machine running the MCP server
(a relative path against that process's working directory).

Without `output_path`, nothing is written.

With an export, the tool's response is the same structure as the file, with these
differences:

- `objects` (and so `elements`) is dropped from every module except those named in
  `module_ids` (any spelling, `M001` means `M1`), which keep it;
- `output_path` is added.

Because every module was read in detail, that summary carries the detail `counts`
(geometry-grouped objects included) and, for a module with a frame, `frame.height`, and its modules have no
`unclassified_element_count` or `unplaced_joinery_ids`. It lists every unattached
id, as the file does (`unattached_element_ids_truncated` is `false`).

## Module entry

| Key | Meaning |
|---|---|
| `module_id` | canonical id: `M` + number without leading zeros (`M001` → `M1`). Only an upper-case `M` is read: `m1` is not a module id. An element's module is read from its subgroup, then its `Module` attribute, then its group; never from its name, where `Tige filetée M12` is a thread size. |
| `grouping_source` | `"subgroup"`, `"geometry"`, `"subgroup+geometry"`, or `null` |
| `frame` | `origin_model`, `x_axis_model`, `y_axis_model`, `z_axis_model`, `length` (along X), `width` (along Y), `height` (top of the module's elements above the origin). `null` when there is no bottom floor, or it fills less than 80% of its enclosing rectangle. `height` is `null` in summarised modules: only detailed modules compute it. |
| `counts` | objects per type: `wall`, `slab`, `roof`, `parapet`, `other`, `opening`. `opening` and `other` are always present, other types only when they occur. Subgroup parts count even when their geometry was not readable. In a summarised module, `counts` cover subgroup parts and the openings of subgroup walls only: a module with `grouping_source` `"geometry"` shows zero counts in a summary and its real counts in the detail. |
| `warnings` | module-level problems, never dropped silently. Includes `unknown part prefixes reported as other: <prefixes>`; `<n> elements have a Module attribute that disagrees with their subgroup; the subgroup was used`; `no bottom floor found: no frame, no objects`; `bottom floor fills <n>% of its enclosing rectangle: not rectangular, objects omitted`; and, in detailed modules, `<id>: no readable geometry, omitted` for each object dropped. |
| `objects` | detailed modules only; empty when the module has no usable frame |
| `unclassified_element_count` | summarised modules only: elements left to the geometric fallback |
| `unplaced_joinery_ids` | summarised modules only: joinery of this module, with readable geometry, not attached to a subgroup wall. The detail places it in a fallback wall or reports it as `other`. |

## Objects

Every object has `id`, `type`, `element_ids` (sorted) and `warnings`. Object
`warnings` carry the object's own problems: a wall body count (`<n> wall body
elements (MOB<section>)...`), elements sticking out of the wall body, `grouped by
geometry (<label>)`, `unknown part prefix '<prefix>': reported as other`, and
`joinery '<name>' lies in no wall`.

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
without readable vertices take no part. Each element goes to the first rule that
fits:

1. Element of the bottom floor: the bottom slab.
2. Box entirely within `SIDE_BAND_MM` (400 mm) of a floor edge (tested in the order
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

| Key | Meaning |
|---|---|
| `id` | `<wall id>-O<n>`, numbered by increasing `offset` |
| `name` | joinery name, e.g. `"MEX type B"` |
| `offset` | from the wall's `start`, along the wall, to the opening's near edge |
| `sill` | from the wall's foot to the bottom of the opening |
| `width`, `height` | of the joinery box; `width` runs along the wall |
| `element_ids` | the joinery element id, as a list |

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
