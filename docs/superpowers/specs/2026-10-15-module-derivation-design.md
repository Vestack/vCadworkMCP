# Module derivation demo: copy M1 as M201, 300 mm shorter

Date: 15/10/2026. Status: design approved in conversation, spec under review.

## Goal

A **capability demo**, on a **copy of the .3d file**, with no manufacturing
commitment: Claude, through vCadworkMCP, copies module M1 of
`250513_AUX_STR_EXE_IndB.3d`, places the copy beside the building, renames it
M201 following the Vestack conventions, and shortens it by 300 mm at its far
end. It is the first use of the bridge's write path on a live model.

Decisions taken with the user:

- Purpose: demo of capability. No design-office rule is applied (stud or joist
  re-spacing, panel joints, drillings pitch). Nothing here is a validated
  structural opinion; a real variant would go through the BE.
- The 300 mm are removed **at the end**: the far end wall moves back.
- M201 sits **beside the building**, 5 m beyond its footprint, same orientation.
- The bottom-bar tabs ("onglets") are reproduced if they are scenes.

Out of scope: the production model, re-spacing, BTL/production numbering,
automatic numbering refresh, any module other than the copy.

## Facts this rests on

From the research of 15/10/2026 (`scratchpad/m201-research.md`: cwapi3d
stubs v30 and 33, Cadwork 2026 SDK headers, spike data) and the object
inventory spec:

- M1 has 1 001 elements by its Module attribute, 483 by its subgroup prefix.
  Subgroup `M1-W1` also holds 64 `tasseau_mex` of modules M2, M3, M8 to M11;
  29 `MEX` joinery without subgroup carry Module = M1 although M1 has three walls
  with an opening. Neither field alone delimits the module: geometry does.
- Exposed and usable: `copy_elements(element_ids, copy_vector)` (returns the new
  ids), `move_element`, `delete_elements`, `set_subgroup`, `set_name`.
- Broken: `set_user_attribute` passes one int where the API takes a list of ids
  (`attribute_controller.set_user_attribute(element_id_list, number, value)`).
- Missing: scenes (`scene_controller.get_scene_list`, `get_elements_from_scene`,
  `add_scene`, `add_elements_to_scene`), and facet stretching
  (`geometry_controller.stretch_facet(element_id, facet_index, distance) -> bool`,
  Cadwork 2026 only; facet indices are renumbered after each successful stretch,
  so a facet is located by its normal through `get_element_facets`, whose
  `facet_list` gives `count()`, `get_normal_vector(i)`,
  `get_distance_to_origin(i)`).
- No transaction or documented undo through the bridge. The only safe rollback
  is deleting the copy's ids, which requires that nothing but the copy is ever
  written.

## Procedure

Every write targets ids returned by the copy. M1 is never written.

0. **Preconditions.** The user opens a copy of the model saved under a new
   name, restarts Cadwork if bridge code changed, starts the bridge. Claude
   checks the file name with `get_3d_file_path` and that no module `M201`
   exists (`get_object_inventory` summary).
1. **Plan the copy** (read-only tool `plan_module_copy`): the perimeter of M1
   and the copy vector. Claude shows counts per subgroup family, the excluded
   elements and the vector; the user says go.
2. **Copy**: `copy_elements(perimeter, vector)`. The returned ids are written
   down; they are the only ids written to afterwards.
3. **Rename** (tool `rename_module`, on the copy's ids): subgroups `M1-*`
   become `M201-*`, Module attribute `M1` becomes `M201`, an element named
   exactly `M1` becomes `M201`. Descriptive subgroups (`Usinage …`, `Pliages`,
   `Connecteurs intermodulaire`) are kept.
4. **Plan the shortening** (read-only tool `plan_module_shortening`, on M201):
   the actions per element and the conflicts. If any conflict exists, stop.
   Otherwise Claude shows the counts; the user says go.
5. **Shorten**: `move_element(move_ids, vector)`, `delete_elements(delete_ids)`,
   `stretch_elements_end(stretch_ids, direction, -300)`.
6. **Scene**: if step 0's scene read shows one scene per module ("M (n)"),
   create the scene for M201 with its elements (`add_scene_with_elements`).
7. **Verify**: `get_object_inventory(module_ids=["M1", "M201"])`: M201's
   length is M1's minus 300 mm, same walls and openings, M1 unchanged.
8. **Rollback, if needed**: `delete_elements(copy ids)`.

## Perimeter of a module (`plan_module_copy`)

Candidates: elements whose module, by `object_inventory.element_module`
(subgroup first), is the source module, **or** whose Module attribute is the
source module. Kept: candidates whose bounding-box centre lies inside the
source module's envelope, expressed in its frame and enlarged by
`DERIVATION_ENVELOPE_TOLERANCE_MM` (150 mm) on every side. The envelope is the
union of the module's subgroup objects (`object_inventory` detail). Processing
elements (group `Usinage`) follow the same rule: they are geometry too.

Output: `perimeter_ids`, the counts per subgroup family, `excluded` (candidates
outside the envelope, with their name, subgroup and Module attribute), the
module frame, and `copy_vector`.

**Copy vector.** Along the model's +X (not the module frame's), so that the
copy lands beside the building whatever the module's orientation:
`dx = building_max_x + DERIVATION_GAP_MM - module_min_x`, `dy = dz = 0`, with
`DERIVATION_GAP_MM` = 5000. `building_max_x` is the maximum model x over the
footprint corners of every module frame in the inventory summary (frames are
read for every module; vertices are not), and `module_min_x` the minimum model
x of the perimeter's vertices. Another side can be passed as `side` (`+x`,
`-x`, `+y`, `-y`), with the symmetric formula.

## Shortening at the end (`plan_module_shortening`)

In the module frame, with `L` the frame length, the end is the `+x` end by
default (`end="-x"` mirrors everything). Let `t` be the thickness of the end
wall: the subgroup wall whose `side` is the end side (if none, `t = 0` and a
warning). The removed slab is `[a, b]` with `b = L - t` and `a = b - amount`.
Each element of the module, from its local box `[x0, x1]` (tolerance
`DERIVATION_TOLERANCE_MM`, 1 mm):

| Position | Action |
|---|---|
| `x0 >= b` | **move** by `-amount` along the frame's X (model vector reported) |
| `x0 >= a` and `x1 <= b` | **delete** |
| `x0 < a` and `x1 > a` | **stretch** its `+X` face by `-amount`, if `x1 >= b`; by `-(x1 - a)` otherwise |
| `x1 <= a` | **keep** |
| `a < x0 < b` and `x1 > b` | **conflict** (starts inside the slab and leaves it) |

Joinery (`MEX …`) or a chevêtre / lintel element (name starting with
`montant_chevetre`, `linteau`, `montant_linteau`) in **delete** or **conflict**
is a **conflict**: an opening crosses the slab. Any conflict stops the
procedure before any write; the plan lists them.

Stretching moves the element's face whose normal is closest to the frame's +X
(cosine above 0.999), the outermost one if several. The bridge re-reads the
facets before each stretch.

Output: `slab` (`a`, `b`, in frame and model coordinates), `move`, `delete`,
`stretch` (ids and distances), `keep_count`, `conflicts`, `move_vector_model`,
`stretch_direction_model`, and warnings.

## Bridge additions

All in `vestack/bridge_handler.py` or a new `vestack/derivation_handlers.py`
added to `EXTENSION_MODULES`, with controller methods and MCP tools, per the
repository's three-place rule:

- `plan_module_copy(module_id, side="+x")` and
  `plan_module_shortening(module_id, amount=300, end="+x")`: read-only; the
  logic lives in a pure module `vestack/module_derivation.py`.
- `rename_module(element_ids, old_module, new_module)`: write; subgroup prefix,
  Module attribute, element named exactly the old id.
- `stretch_elements_end(element_ids, direction, distance)`: write; per element,
  locate the face by its normal, `gc.stretch_facet`, report failures per id.
- `get_scenes()` (read: names and element counts) and
  `add_scene_with_elements(name, element_ids)` (write).
- Fix `set_user_attribute` (and `clear_user_attribute`) to pass a list of ids.

Write tools follow the `cadwork-model` skill's Lane 2: saved copy, ids shown,
go-ahead, verify after. The skill gets a "Derive a module" procedure.

## Testing

Pure logic (`module_derivation.py`) on fabricated modules: perimeter with
foreign elements inside a subgroup and attributed elements outside the
envelope; copy vector for each side; each row of the action table at the slab
boundaries (with the 1 mm tolerance); conflicts for joinery and lintels;
`end="-x"`; a module without end wall. Bridge handlers with Cadwork faked in
`sys.modules`: rename on a mixed set, stretch locating the face by normal and
re-reading facets after each stretch, stretch failure reported per id, scenes.
The live demo (Task "live") is the verification of the write path.

## Risks

- First live writes ever: `copy_elements`, `set_subgroup`, `stretch_facet` have
  never run through this bridge. The demo runs only on a file copy.
- `copy_elements` behaviour for processings, joins and connectors is
  undocumented; the verify step reads the result, and the rollback deletes the
  copy.
- `stretch_facet` is absent from the pinned v30 stubs: mypy cannot check it;
  the handler resolves it with `getattr` and reports its absence.
