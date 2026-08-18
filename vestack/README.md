# Vestack domain extension

Everything in this package is specific to Vestack modular construction. The rest
of the repository is a generic Cadwork MCP server and does not depend on it.

## What a module is

A module is a rectangular box: a **bottom floor**, usually a **top floor**, and up
to **eight walls** (long sides get split into several panels). Some modules are
left **open** on one or more sides so that adjoining modules form a larger room.

Each module carries a unique id of the form `M139` — the letter `M` and three
digits. In the Cadwork template it lives in a **user attribute named "Module"**,
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
