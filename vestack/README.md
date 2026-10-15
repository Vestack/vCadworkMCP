# Vestack domain extension

Everything in this package is specific to Vestack modular construction. The rest
of the repository is a generic Cadwork MCP server and does not depend on it.

## What a module is

A module is a rectangular box: a **bottom floor**, usually a **top floor**, and up
to **eight walls** (long sides get split into several panels). Some modules are
left **open** on one or more sides so that adjoining modules form a larger room.

Each module carries an id of the form `M1`, `M17` or `M139`: the upper-case
letter `M` and 1 to 4 digits. Leading zeros are dropped, so `M001` is `M1`. A
lower-case `m` does not match, so "10 m2" in an element name is not a module. In
the Cadwork template the id lives in a **user attribute named "Module"**,
alongside `Bâtiment` and `Niveau`:

| Attribute | Name | Example |
|---|---|---|
| 1 | Bâtiment | `Maisons 25-26` |
| 2 | Niveau | `RDC` |
| 3 | Module | `M139` |

Attribute *numbers* differ between Cadwork user profiles, so they are resolved
from the attribute *name* at run time (accent- and case-insensitive). When no
attribute is named "Module", the id is looked for in the subgroup, the group and
the element name instead, and the field actually used is reported as `id_source`.

## How the dimensions are derived

From the **bottom floor**, which every module has, open or not:

- `length` = longer side of the floor's footprint, `width` = the shorter one
- `height` = the module envelope, lowest point to highest
- `footprint_area_m2` = the floor footprint in m²

Walls are then matched against the four edges of that footprint. An edge with no
wall spanning at least half its length is reported in `open_sides` as `-x`, `+x`,
`-y` or `+y` — model axes, not compass directions.

Elements are sorted into `slab`, `wall` and `other` from their bounding-box
proportions alone, so no naming convention is required on the elements
themselves. Thresholds live in `conventions.py`.

## Files

| File | Role | Imports Cadwork |
|---|---|---|
| `conventions.py` | the id pattern, attribute names and every threshold | no |
| `module_inventory.py` | the logic: grouping, roles, dimensions, warnings | no |
| `bridge_handler.py` | reads the live model, builds snapshots | yes, inside functions |
| `mcp_controller.py` | MCP-side proxy over the socket | no |

`module_inventory.py` is pure, which is why `tests/test_module_inventory.py` runs
without Cadwork. Retune behaviour in `conventions.py` before touching the logic.

## Object inventory

`get_object_inventory` goes one level below the module: walls, slabs, roofs,
parapets and openings, each with its envelope in a frame local to the module
(origin at a bottom-floor corner, X along its longer side). It is the Cadwork
half of the Revit consistency check; the schema is in `OBJECT_INVENTORY.md`.

Objects come from **part subgroups** `M<n>-<prefix><k>` (`M1-W5` = module 1,
wall 5; prefixes in `conventions.PART_TYPES`). A wall's envelope comes from its
`MOB<section>` body element. Openings are `MEX` joinery elements, attached to
the wall containing them whatever their subgroup. Elements outside any part
subgroup are grouped by geometry (side bands, slab bands, interior planes).

Without `module_ids`, the response holds one summary per module: the frame
without its height, and counts of subgroup objects only. Naming modules in
`module_ids` adds their objects, and the geometric fallback runs at that level
of detail. `OBJECT_INVENTORY.md` has the full contract.

| File | Role | Imports Cadwork |
|---|---|---|
| `naming.py` | module ids, part subgroups, wall bodies, joinery | no |
| `frame.py` | module frame from the bottom floor | no |
| `object_inventory.py` | the logic: modules, objects, openings, fallback | no |
| `OBJECT_INVENTORY.md` | the output schema, for the Revit side | - |

## Known limitations

- **Bounding boxes are axis-aligned.** A module rotated in plan gets an inflated
  footprint. The inventory detects this by comparing the floor's real plan area
  (recovered from its volume) with its bounding box, and warns instead of
  reporting a wrong figure silently.
- **Cost.** One vertex query per element, so scanning a whole building is slow.
  Pass `element_ids`, or `active_only` to cover the current selection.
- Elements with no vertices (containers, processing-only elements) are skipped
  and listed in `skipped_element_ids`.

## Removing the extension

1. delete this package,
2. remove `"vestack.bridge_handler"` from `EXTENSION_MODULES` in `bridge/dispatcher.py`,
3. remove the `VestackController` import, its instance and the
   `get_module_inventory` tool from `main.py`.

Nothing else references it.
