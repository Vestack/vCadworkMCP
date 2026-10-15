---
name: cadwork-model
description: Use when working with a live Cadwork 3D model through this repository's MCP server - listing Vestack modules and their dimensions, counting or filtering elements, inspecting geometry, or moving an element such as a window. Also use when an MCP call answers "Unknown operation" or the bridge looks unreachable.
---

# Cadwork model access

## Overview

Two lanes, not interchangeable. Reading a model is free and repeatable. Changing
one is neither: **this MCP has no undo**, and the modeller's Cadwork undo stack
does not cover what the bridge did. The inverse operation, computed from
coordinates you wrote down first, is the only way back.

All lengths are **millimetres** (Cadwork's native unit). Report areas in m² and
volumes in m³, and state the unit on every figure.

## Preflight, both lanes

Call `get_3d_file_path` once (not `get_project_data`, broken under Cadwork
2026). It names the open file, which also tells you whether it is a copy.

- **Connection refused**: the bridge is not running. Ask the user to open the
  user-plugin panel (Fenêtre → Plugins utilisateur), click **Controle du Pont
  MCP**, then **Start Bridge** (port 53002).
- **Timeout**: the bridge is running but Cadwork is in an active command. Ask
  the user to press **Escape** in Cadwork, then retry once.

Do not retry more than once otherwise: a dead bridge fails identically every
time.

## Lane 1 — read the model

1. **Scope first.** Ask the modeller to select the elements in Cadwork, then
   `get_active_element_ids`. Whole-model reads (`get_all_element_ids`) trigger one
   Cadwork API call per element downstream and are slow on a building.
2. **Modules:** `get_module_inventory` with `active_only: true`, or an explicit
   `element_ids`. Read the response before summarising it:
   - `id_source` — where the `M139`-style id was actually found
     (`user_attribute_3` in the Vestack template). **If it is null**, no module id
     exists in the scanned elements; say that, rather than reporting "0 modules"
     as a fact about the building.
   - `open_sides` — `-x`, `+x`, `-y`, `+y`: model axes, not compass directions. A
     non-empty list means the module is open on those sides.
   - `warnings` — a floor rotated in plan or not rectangular means the reported
     dimensions are overstated. Pass the warning on; never quietly drop it.
   - `skipped_element_ids` — no readable geometry, excluded from every count.
3. **Counts and statistics:** `get_element_count_by_type`, `get_group_statistics`,
   `get_material_statistics`, `get_elements_by_type`. The type filter accepts
   beam, panel, drilling, node, line, surface, volume, container, auxiliary,
   text_object, dimension, architectural — **there is no window type**.
4. **One element in detail:** `get_element_info` returns name, group, subgroup,
   comment, material, the points p1/p2/p3 and the local axes in a single call.

## Lane 2 — change the model

**Every modification follows these steps, in order. None is optional, including
for a single-element test.**

1. **Saved?** Have the user confirm the model is saved. `get_3d_file_path` names
   the file you are about to modify.
2. **Target by selection, never by guess.** The modeller selects the element in
   Cadwork → `get_active_element_ids` → `get_element_info` on each id → show the
   user the name, group and material you got back and confirm it is the intended
   element before touching it.
3. **Record the before state.** `get_element_info` already gives you p1/p2/p3.
   Put those numbers in your reply. They are the only undo data that will exist.
4. **State the operation, get a go-ahead:** the exact ids and the exact vector in
   millimetres.
5. **Execute**, e.g. `move_element(element_ids=[1234], move_vector=[0, -150, 0])`.
6. **Verify:** `get_element_info` again — the delta must equal the vector you
   sent. Then `refresh_display`. If the delta is wrong, stop and report it; do not
   patch it with a second move.
7. **Undo** is the same call with the negated vector, from the recorded values.

Several elements in one batch: `disable_auto_display_refresh` first, then
`enable_auto_display_refresh` and `refresh_display` at the end.

### Red flags — stop

| About to | Instead |
|---|---|
| Call a write tool without p1/p2/p3 recorded | Record them. There is no undo. |
| Decide which element is "the window" from a name or type search | Ask for a selection in Cadwork. No window element type exists. |
| Retry a failed write to see if it takes this time | Read the state first: a partial write may already have landed. |
| Call `delete_elements`, `invert_model`, `apply_global_scale` or `join_elements` "to test" | Model-wide or irreversible. Test on a copy of the file. |
| Move a whole group because moving one element worked | The approved scope is the scope. A new scope needs a new go-ahead. |

| Excuse | Reality |
|---|---|
| "It's a 10 mm test move, I'll just move it back" | Moving back needs the original coordinates. Without them you are guessing. |
| "The user asked me to test moving a window, so I'll pick one" | Picking wrong modifies production geometry. A selection costs one message. |
| "`status: ok` means it worked" | It means the bridge accepted the call. Verify the geometry actually changed. |
| "I'll record the before state after the move" | After the move the before state is gone. |

## When a call fails

- **`Unknown operation: X`** — no handler exists; X is one of the tools declared
  but never implemented. Do not retry or rephrase. Check `tool-inventory.md`, then
  tell the user it is not implemented.
- **`Connection failed` / timeout** — bridge down, see Preflight.
- **`status: error` with an API message** — Cadwork itself refused. Report the
  message verbatim; it usually names the constraint.

See `tool-inventory.md` for what works, what is declared but missing, and what is
dangerous.
