# Object inventory schema: `vestack.object_inventory/1`

What the bridge operation `get_object_inventory` returns. It is the contract
between the Cadwork side (this repository) and the Revit side, which must produce
the same structure from the Revit model so that Claude can compare the two.

The JSON file written with `output_path` is specified in the design spec but is
not in this revision: the controller that writes it is still to come. The file
will hold the same structure.

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
  perpendicular to the model's +X, X is +Y.
- A model point `P` has module coordinates
  `((P - origin_model) · x_axis_model, (P - origin_model) · y_axis_model, (P - origin_model) · z_axis_model)`.

## Top level

| Key | Meaning |
|---|---|
| `status` | `"ok"`, or `"error"` with a `message` when the scan fails |
| `schema` | `"vestack.object_inventory/1"`; bumped on any incompatible change |
| `source` | `file` (path of the open model, empty if unavailable), `extracted_at` (ISO 8601 with offset, seconds) |
| `modules` | one entry per module found, sorted by module number |
| `unattached_element_ids` | elements with no module; joinery with no module, no readable geometry, or whose module has no frame |
| `processing_element_count` | processing elements (group `Usinage`), counted but never in an object |
| `warnings` | e.g. `module M5 not found in the scanned elements` for a requested module |
| `scanned_element_count`, `geometry_read_count`, `skipped_element_ids`, `attribute_numbers` | Cadwork side only: scan statistics |

## Module entry

| Key | Meaning |
|---|---|
| `module_id` | canonical id: `M` + number without leading zeros (`M001` → `M1`). Only an upper-case `M` is read: `m1` is not a module id. |
| `grouping_source` | `"subgroup"`, `"geometry"`, `"subgroup+geometry"`, or `null` |
| `frame` | `origin_model`, `x_axis_model`, `y_axis_model`, `z_axis_model`, `length` (along X), `width` (along Y), `height` (top of the module's elements above the origin). `null` when there is no bottom floor, or it fills less than 80% of its enclosing rectangle. `height` is `null` in summarised modules: only detailed modules compute it. |
| `counts` | objects per type: `wall`, `slab`, `roof`, `parapet`, `other`, `opening`. `opening` and `other` are always present, other types only when they occur. Subgroup parts count even when their geometry was not readable. |
| `warnings` | module-level problems, never dropped silently. Includes `unknown part prefixes reported as other: <prefixes>`; `<n> elements have a Module attribute that disagrees with their subgroup; the subgroup was used`; `no bottom floor found: no frame, no objects`; `bottom floor fills <n>% of its enclosing rectangle: not rectangular, objects omitted`; and, in detailed modules, `<id>: no readable geometry, omitted` for each object dropped. |
| `objects` | detailed modules only |
| `unclassified_element_count` | summarised modules only: elements left to the geometric fallback |
| `unplaced_joinery_ids` | summarised modules only: joinery of this module, with readable geometry, not attached to a subgroup wall. The detail places it in a fallback wall or reports it as `other`. |

## Objects

Every object has `id`, `type`, `element_ids` (sorted) and `warnings`. Object
`warnings` carry the object's own problems: a wall body count (`<n> wall body
elements (MOB<section>)...`), elements sticking out of the wall body, `grouped by
geometry (<label>)`, `unknown part prefix '<prefix>': reported as other`, and
`joinery '<name>' lies in no wall`.

`id` is:
- the part subgroup (`M1-W5`) for subgroup parts;
- `M1-geo<n>` for geometric fallback groups. `n` counts that module's fallback
  groups from 1, in this order: bottom slab, top slab, side walls (`-x`, `+x`,
  `-y`, `+y`), interior walls, other;
- `M1-joinery<element id>` for joinery lying in no wall.

Interior fallback walls are grouped per axis (X or Y). Upright elements (height at
least `WALL_MIN_HEIGHT_MM`, 1000 mm; thickness at most `WALL_MAX_THICKNESS_MM`,
600 mm) form one wall when their mid-planes lie within
`INTERIOR_WALL_PLANE_TOLERANCE_MM` (100 mm) of each other and the gaps between
them along the wall are at most `INTERIOR_WALL_GAP_MM` (600 mm). Each element
belongs to one wall; an L-shaped corner goes to the longer branch.

**wall**

| Key | Meaning |
|---|---|
| `start`, `end` | wall axis at its foot, at mid-thickness; `start` is the end with the smaller coordinate along the wall |
| `thickness`, `height` | of the wall body (the union of the wall's elements when it has no single body) |
| `side` | footprint edge it stands on: `-x`, `+x`, `-y`, `+y`. `null` when the wall's mid-thickness line lies more than `SIDE_BAND_MM` (400 mm) from every edge, which is the case for interior walls. |
| `wall_type`, `stud_section` | from the single `MOB<section>` body element: `"MOB200"` and `200`. Both `null` when the wall has no body element or more than one (a warning gives the count). |
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
`PH-`; otherwise `"bottom"` for the bottom floor, else `null`), `origin` (min
corner), `length` (along X), `width` (along Y), `thickness`.

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
