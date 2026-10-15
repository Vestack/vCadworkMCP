# Object inventory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only `get_object_inventory` MCP tool that lists, per Vestack module, its walls, slabs, roofs and openings with their envelopes in a module-local frame, so Claude can compare a Cadwork model with its Revit counterpart.

**Architecture:** Pure logic in `vestack/` (naming rules, module frame, object inventory) takes snapshots and returns the `vestack.object_inventory/1` structure. The bridge adapter reads attributes for every element, asks the pure logic which elements need vertices, reads only those, then builds the inventory. The MCP controller adds a long per-call timeout and an optional atomic JSON export.

**Tech Stack:** Python 3.12 (server, venv) / 3.10 and 3.14 (bridge, inside Cadwork v30 and 2026), `unittest`, `mypy`, `mcp<2` (FastMCP). No new dependency.

**Spec:** `docs/superpowers/specs/2026-10-15-object-inventory-design.md`

## Global Constraints

- Bridge-side code (`vestack/`, `bridge/`) stays valid **Python 3.10**: no `typing.Self`, `except*`, `tomllib`, no `X | Y` at runtime outside annotations.
- Every handler imports Cadwork modules (`attribute_controller`, `geometry_controller`, `element_controller`, `utility_controller`) **inside its functions**, never at module level, or the tests stop being runnable.
- Pure modules (`naming.py`, `frame.py`, `object_inventory.py`, `module_inventory.py`) import nothing from Cadwork.
- Lengths in millimetres, rounded to 1 mm in outputs; ISO 8601 for `extracted_at`.
- Schema id `vestack.object_inventory/1`; any incompatible change bumps it and regenerates the golden file.
- Module id rule: `M` + 1 to 4 digits, then end of text or `-`, `_`, space; canonical form drops leading zeros (`M001` → `M1`).
- Read-only toward Cadwork: no write operation anywhere in this plan.
- Code, comments and docstrings in English. Match each file's existing style.
- Run everything from the repository root in the project venv: `.venv\Scripts\python -m unittest discover -s tests -t .` (78 tests before this plan, 168 after) and `.venv\Scripts\python -m mypy .` (baseline: 13 errors in 4 files, all pre-existing; it must stay at 13).
- Commit after every task, on the current branch, message ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **A real model where the floor subgroup also holds the floor's edge beams or the facade cladding** (elements wider than the slab): the frame then grows past the floor. Expected: the frame still follows the floor's long side, and the excess shows up as a slab envelope larger than the walls, not as a crash. Pinned by the live check in Task 9 (compare `frame.length`/`width` with the walls' extents).
2. **Joinery straddling two walls at a module corner, or set in a wall of the neighbouring module**: the centre test picks the first containing wall in module order. Expected: attached to exactly one wall, never duplicated. Pinned by `test_joinery_without_subgroup_is_attached_to_its_wall` plus the uniqueness assertion added in Task 3, Step 1 (`test_each_joinery_is_attached_once`).
3. **A whole-building export on a large model**: about 50 s of attribute reads plus vertex reads; the 900 s timeout must hold and the file must be complete or absent. Pinned by `test_an_unwritable_path_is_an_error_and_leaves_no_file` (Task 7) and timed in Task 9.
4. **Cadwork busy in an active command during a scan**: the call times out; expected message tells the user to press Escape. Pinned by `test_the_controller_passes_the_timeout_and_suggests_escape` (Task 6).
5. **Module ids spelled differently across fields** (`M001` in the attribute, `M1` in the subgroup): expected one module `M1`, no disagreement warning. Pinned by `test_zero_padded_attribute_agrees_with_subgroup` added in Task 3, Step 1.

---

### Task 1: Naming rules

Relaxes the module id rule (the live model uses `M1`…`M24`, which `M\d{3}` misses entirely) and adds the part-subgroup, wall-body and joinery rules observed in the spike. `get_module_inventory` adopts the new id rule.

**Files:**
- Modify: `vestack/conventions.py` (replace whole file)
- Create: `vestack/naming.py`
- Modify: `vestack/module_inventory.py` (`extract_module_id`)
- Modify: `tests/test_module_inventory.py:113,172` (canonical ids)
- Test: `tests/test_naming.py`

**Interfaces:**
- Produces: `PartRef(module_id: Optional[str], prefix: str, number: str, object_type: str)` (frozen dataclass); `parse_module_id(value: str) -> Optional[str]`; `module_number(module_id: str) -> int`; `part_object_type(prefix: str) -> str`; `parse_part(subgroup: str) -> Optional[PartRef]`; `wall_body_section(name: str) -> Optional[int]`; `is_joinery(name: str) -> bool`; `is_processing(group: str) -> bool`; `floor_level_hint(group: str, complex_code: str) -> Optional[str]`. New constants in `conventions`: `PART_TYPES`, `PART_SUBGROUP_PATTERN`, `BARE_PART_PATTERN`, `WALL_BODY_NAME_PATTERN`, `WALL_BODY_TOLERANCE_MM`, `JOINERY_NAME_PATTERN`, `JOINERY_CENTRE_TOLERANCE_MM`, `PROCESSING_GROUPS`, `BOTTOM_FLOOR_GROUPS`, `TOP_FLOOR_GROUPS`, `BOTTOM_FLOOR_COMPLEX_PREFIX`, `TOP_FLOOR_COMPLEX_PREFIX`, `COMPLEX_ATTRIBUTE_NAMES`, `INTERIOR_WALL_PLANE_TOLERANCE_MM`.

- [ ] **Step 1: Write the failing test** — create `tests/test_naming.py`:

```python
"""Tests for the Vestack naming rules, observed on a Cadwork 2026 model."""
import unittest

from vestack.naming import (
    PartRef,
    floor_level_hint,
    is_joinery,
    is_processing,
    module_number,
    parse_module_id,
    parse_part,
    wall_body_section,
)


class ModuleIds(unittest.TestCase):
    def test_one_to_four_digits_are_accepted(self) -> None:
        for raw in ("M1", "M17", "M139", "M1234"):
            self.assertEqual(parse_module_id(raw), raw)

    def test_leading_zeros_are_dropped(self) -> None:
        self.assertEqual(parse_module_id("M001"), "M1")
        self.assertEqual(parse_module_id("M007"), "M7")

    def test_the_id_is_found_before_a_separator(self) -> None:
        self.assertEqual(parse_module_id("M1-W5"), "M1")
        self.assertEqual(parse_module_id("M15_W1"), "M15")
        self.assertEqual(parse_module_id("M8 Poteaux"), "M8")

    def test_the_id_is_found_inside_a_longer_value(self) -> None:
        self.assertEqual(parse_module_id("Module M139"), "M139")

    def test_lower_case_is_accepted(self) -> None:
        self.assertEqual(parse_module_id("m12"), "M12")

    def test_labels_without_a_digit_after_the_m_are_rejected(self) -> None:
        for label in ("Module standard R+1", "Module Façade Nord", "MOB200",
                      "MEX type B", "MFP 12 mm", ""):
            self.assertIsNone(parse_module_id(label), label)

    def test_five_digits_are_rejected(self) -> None:
        self.assertIsNone(parse_module_id("M12345"))

    def test_module_number_sorts_numerically(self) -> None:
        self.assertEqual(sorted(["M10", "M2", "M1"], key=module_number), ["M1", "M2", "M10"])


class PartSubgroups(unittest.TestCase):
    def test_a_wall_subgroup(self) -> None:
        self.assertEqual(parse_part("M1-W5"), PartRef("M1", "W", "5", "wall"))

    def test_every_known_prefix_maps_to_its_object(self) -> None:
        expected = {"M2-F1": "slab", "M16-TF0": "roof", "M16-C1": "roof",
                    "M15-T2": "roof", "M15-A8": "parapet"}
        for subgroup, object_type in expected.items():
            part = parse_part(subgroup)
            assert part is not None, subgroup
            self.assertEqual(part.object_type, object_type, subgroup)

    def test_an_unknown_named_part_is_other(self) -> None:
        self.assertEqual(parse_part("M8-Poteaux"), PartRef("M8", "Poteaux", "", "other"))

    def test_underscore_separator_and_zero_padded_module(self) -> None:
        self.assertEqual(parse_part("M015_W1"), PartRef("M15", "W", "1", "wall"))

    def test_a_bare_part_has_no_module(self) -> None:
        self.assertEqual(parse_part("W1"), PartRef(None, "W", "1", "wall"))
        self.assertEqual(parse_part("F2"), PartRef(None, "F", "2", "slab"))

    def test_descriptive_subgroups_are_not_parts(self) -> None:
        for subgroup in ("Pliages", "Usinage PH - Perçage rive", "Jonction module",
                         "M17", "ELEC PMR", ""):
            self.assertIsNone(parse_part(subgroup), subgroup)


class ElementRoles(unittest.TestCase):
    def test_wall_body_names_give_the_stud_section(self) -> None:
        self.assertEqual(wall_body_section("MOB200"), 200)
        self.assertEqual(wall_body_section("MOB95"), 95)
        self.assertIsNone(wall_body_section("montant"))
        self.assertIsNone(wall_body_section("MOB"))

    def test_joinery_names(self) -> None:
        for name in ("MEX type A", "MEX type B", "MEX type D", "MEX couloir"):
            self.assertTrue(is_joinery(name), name)
        for name in ("Joue", "Bavette", "MEX", "MEXtype A", "montant"):
            self.assertFalse(is_joinery(name), name)

    def test_processing_groups(self) -> None:
        self.assertTrue(is_processing("Usinage"))
        self.assertFalse(is_processing("MOB"))

    def test_floor_level_from_group_then_complexe(self) -> None:
        self.assertEqual(floor_level_hint("Plancher bas", ""), "bottom")
        self.assertEqual(floor_level_hint("Plancher haut", ""), "top")
        self.assertEqual(floor_level_hint("", "PB-AUX-01"), "bottom")
        self.assertEqual(floor_level_hint("", "PH-AUX-02"), "top")
        self.assertIsNone(floor_level_hint("MOB", "OB-AUX-01"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_naming -v`
Expected: ERROR, `ModuleNotFoundError: No module named 'vestack.naming'`.

- [ ] **Step 3: Replace `vestack/conventions.py`** with:

```python
"""Vestack modular-construction conventions.

Every threshold and naming rule specific to Vestack lives here. Retune this file
rather than the logic in module_inventory.py, and see README.md for what each
value means in practice. All lengths are millimetres, Cadwork's native unit.
"""
import re
from typing import Dict, Pattern, Tuple

# --- Module identity -------------------------------------------------------

# A module id is the letter M, then 1 to 4 digits, then the end of the text or a
# separator ("-", "_", space). Observed: M1, M17, M001, M15_W1, M139. Leading
# zeros are dropped when normalising, so M001 and M1 are the same module. A digit
# must follow the M, which keeps labels such as "Module standard R+1" out.
MODULE_ID_PATTERN: Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9])M(\d{1,4})(?=$|[-_ ])", re.IGNORECASE)

# Cadwork user attributes carrying the module context. Matched against the
# attribute *name* (case- and accent-insensitive, substring match) rather than
# its number, because numbering varies between Cadwork user profiles.
MODULE_ATTRIBUTE_NAMES: Tuple[str, ...] = ("module",)
BUILDING_ATTRIBUTE_NAMES: Tuple[str, ...] = ("batiment", "building", "gebaude")
LEVEL_ATTRIBUTE_NAMES: Tuple[str, ...] = ("niveau", "level", "etage", "geschoss")

# How many user attribute numbers to scan when looking for those names.
USER_ATTRIBUTE_SCAN_LIMIT: int = 20

# Non-attribute fields that may hold the module id, in order of preference.
PLAIN_ID_FIELDS: Tuple[str, ...] = ("subgroup", "group", "name")

# --- Geometry classification ----------------------------------------------

# A slab (floor or ceiling panel) is thinnest along Z, and thin relative to its
# own smallest horizontal dimension. The ratio keeps sticks out: a 120x120 beam
# is thinnest along Z too, but its thickness equals its width.
SLAB_MAX_THICKNESS_RATIO: float = 0.5

# A wall stands tall, stays thin in plan, and runs for some length. The length
# rule separates walls from posts, which would otherwise look like short walls.
WALL_MIN_HEIGHT_MM: float = 1000.0
WALL_MAX_THICKNESS_MM: float = 600.0
WALL_MIN_LENGTH_MM: float = 1000.0

# A slab this far above the top of the bottom floor is the module's top floor.
TOP_FLOOR_MIN_CLEARANCE_MM: float = 500.0

# --- Open-side detection ---------------------------------------------------

# How far from a floor edge a wall may sit and still count as standing on it.
SIDE_BAND_MM: float = 400.0

# Fraction of a floor edge a wall must span before that edge counts as closed.
# Below it the side is reported open: that is how open modules, built to join
# into a large room, are told apart from closed ones.
MIN_SIDE_COVERAGE: float = 0.5

# --- Data-quality checks ---------------------------------------------------

# A floor's plan area, recovered from its volume, divided by its bounding-box
# footprint. Well below 1.0 means the floor is rotated in plan or not
# rectangular, so its bounding box overstates the module's dimensions.
MIN_PLAN_AREA_RATIO: float = 0.8

# --- Part subgroups (object inventory) --------------------------------------

# Prefix of a part subgroup such as "M1-W5" -> the object it makes. Read off
# the model 250513_AUX_STR_EXE_IndB.3d: W and F stated by the modeller, the
# others inferred from groups, element names and the Complexe attribute. Any
# other prefix ("Poteaux", "Porteuses", "fourrure") makes an "other" object.
PART_TYPES: Dict[str, str] = {
    "W": "wall",
    "F": "slab",
    "TF": "roof",      # toiture froide
    "C": "roof",       # caisson de toiture froide
    "T": "roof",       # toiture du module de couronnement
    "A": "parapet",    # acrotere
}

# "<module id><separator><letters><number?>", e.g. M1-W5, M16-TF0, M8-Poteaux.
PART_SUBGROUP_PATTERN: Pattern[str] = re.compile(
    r"^\s*M(\d{1,4})[-_ ]([A-Za-z]+)(\d*)\s*$", re.IGNORECASE)

# A part subgroup missing its module, e.g. "W1". Known prefixes only, so that
# descriptive subgroups such as "Pliages" are not mistaken for parts.
BARE_PART_PATTERN: Pattern[str] = re.compile(r"^\s*(TF|W|F|C|T|A)(\d+)\s*$")

# The element carrying a wall's envelope is named after the wall type: "MOB"
# (mur ossature bois) followed by the stud section in mm, e.g. MOB200.
WALL_BODY_NAME_PATTERN: Pattern[str] = re.compile(r"^\s*MOB\s*(\d+)\s*$", re.IGNORECASE)

# How far the union of a wall's elements may exceed its body before a warning.
WALL_BODY_TOLERANCE_MM: float = 20.0

# Joinery (openings): "MEX type A", "MEX type B", "MEX type D", "MEX couloir".
# MEX accessories (Joue, Bavette, Larmier, Habillage) do not match.
JOINERY_NAME_PATTERN: Pattern[str] = re.compile(
    r"^\s*MEX\s+(type\b|couloir\b)", re.IGNORECASE)

# How far outside a wall body a joinery centre may lie and still belong to it.
JOINERY_CENTRE_TOLERANCE_MM: float = 50.0

# Groups whose elements are processings (drillings, notches): no envelope.
PROCESSING_GROUPS: Tuple[str, ...] = ("usinage",)

# Floor level hints, from the group (lower-cased) or the Complexe code.
BOTTOM_FLOOR_GROUPS: Tuple[str, ...] = ("plancher bas",)
TOP_FLOOR_GROUPS: Tuple[str, ...] = ("plancher haut",)
BOTTOM_FLOOR_COMPLEX_PREFIX: str = "PB-"
TOP_FLOOR_COMPLEX_PREFIX: str = "PH-"

# The Cadwork user attribute holding the Complexe code, matched by name.
COMPLEX_ATTRIBUTE_NAMES: Tuple[str, ...] = ("complexe", "complex")

# Geometric fallback: vertical elements whose mid-planes lie within this
# distance of each other form one interior wall.
INTERIOR_WALL_PLANE_TOLERANCE_MM: float = 100.0
```

- [ ] **Step 4: Create `vestack/naming.py`:**

```python
"""Vestack naming rules: module ids, part subgroups, wall bodies, joinery.

Pure functions over strings, no Cadwork import. The patterns themselves live in
conventions.py; this module only interprets them.
"""
from dataclasses import dataclass
from typing import Optional

from . import conventions as cv


@dataclass(frozen=True)
class PartRef:
    """What a part subgroup such as "M1-W5" says about its elements."""

    module_id: Optional[str]  # canonical ("M1"), None for a bare part ("W1")
    prefix: str               # as written: "W", "TF", "Poteaux"
    number: str               # "" when the subgroup carries no number
    object_type: str          # "wall", "slab", "roof", "parapet" or "other"


def parse_module_id(value: str) -> Optional[str]:
    """Canonical module id found in a field value: "M001" -> "M1", else None."""
    match = cv.MODULE_ID_PATTERN.search(value or "")
    return f"M{int(match.group(1))}" if match else None


def module_number(module_id: str) -> int:
    """Numeric part of a canonical module id, for sorting M2 before M10."""
    return int(module_id[1:])


def part_object_type(prefix: str) -> str:
    """Object type a part prefix makes: "W" -> "wall", unknown -> "other"."""
    return cv.PART_TYPES.get(prefix.upper(), "other")


def parse_part(subgroup: str) -> Optional[PartRef]:
    """Read a part subgroup ("M1-W5", "M8-Poteaux", bare "W1"), else None."""
    text = subgroup or ""
    match = cv.PART_SUBGROUP_PATTERN.match(text)
    if match:
        digits, prefix, number = match.groups()
        return PartRef(f"M{int(digits)}", prefix, number, part_object_type(prefix))
    match = cv.BARE_PART_PATTERN.match(text)
    if match:
        prefix, number = match.groups()
        return PartRef(None, prefix, number, part_object_type(prefix))
    return None


def wall_body_section(name: str) -> Optional[int]:
    """Stud section of a wall body element ("MOB200" -> 200), else None."""
    match = cv.WALL_BODY_NAME_PATTERN.match(name or "")
    return int(match.group(1)) if match else None


def is_joinery(name: str) -> bool:
    """Whether an element is a joinery item that makes an opening."""
    return bool(cv.JOINERY_NAME_PATTERN.match(name or ""))


def is_processing(group: str) -> bool:
    """Whether an element is a processing (drilling, notch), not a solid part."""
    return (group or "").strip().lower() in cv.PROCESSING_GROUPS


def floor_level_hint(group: str, complex_code: str) -> Optional[str]:
    """"bottom" or "top" when the group or Complexe code says so, else None."""
    lowered = (group or "").strip().lower()
    if lowered in cv.BOTTOM_FLOOR_GROUPS:
        return "bottom"
    if lowered in cv.TOP_FLOOR_GROUPS:
        return "top"
    code = (complex_code or "").strip().upper()
    if code.startswith(cv.BOTTOM_FLOOR_COMPLEX_PREFIX):
        return "bottom"
    if code.startswith(cv.TOP_FLOOR_COMPLEX_PREFIX):
        return "top"
    return None
```

- [ ] **Step 5: Make `module_inventory` use the new rule, and update the two tests that asserted zero-padded ids:**

```diff
--- a/vestack/module_inventory.py
+++ b/vestack/module_inventory.py
@@ -13,6 +13,7 @@
 from typing import Any, Dict, List, Optional, Sequence, Tuple
 
 from . import conventions as cv
+from .naming import parse_module_id
 
 # (x_min, y_min, z_min, x_max, y_max, z_max), in millimetres.
 BBox = Tuple[float, float, float, float, float, float]
@@ -50,9 +51,8 @@
 
 
 def extract_module_id(value: str) -> Optional[str]:
-    """Pull an "M139"-style module id out of a field value."""
-    match = cv.MODULE_ID_PATTERN.search(value or "")
-    return match.group(0) if match else None
+    """Pull a module id out of a field value, in canonical form ("M001" -> "M1")."""
+    return parse_module_id(value)
 
 
 def candidate_id_sources(snapshots: Sequence[ElementSnapshot]) -> List[str]:
```

```diff
--- a/tests/test_module_inventory.py
+++ b/tests/test_module_inventory.py
@@ -110,7 +110,7 @@
     def test_module_id_and_source_are_reported(self) -> None:
         inventory = build_inventory(closed_module("M042"))
         self.assertEqual(inventory["id_source"], "subgroup")
-        self.assertEqual(only(inventory)["module_id"], "M042")
+        self.assertEqual(only(inventory)["module_id"], "M42")
 
 
 class ElementRoles(unittest.TestCase):
@@ -169,7 +169,7 @@
     def test_modules_are_sorted_by_id(self) -> None:
         snaps = closed_module("M002", first_id=1) + closed_module("M001", first_id=100)
         inventory = build_inventory(snaps)
-        self.assertEqual([m["module_id"] for m in inventory["modules"]], ["M001", "M002"])
+        self.assertEqual([m["module_id"] for m in inventory["modules"]], ["M1", "M2"])
 
     def test_module_count_and_total_footprint_are_reported(self) -> None:
         snaps = closed_module("M001", first_id=1) + closed_module("M002", first_id=100)
```

- [ ] **Step 6: Run the tests**

Run: `.venv\Scripts\python -m unittest discover -s tests -t .`
Expected: `Ran 96 tests`, `OK`.

- [ ] **Step 7: Commit**

```bash
git add vestack/conventions.py vestack/naming.py vestack/module_inventory.py tests/test_naming.py tests/test_module_inventory.py
git commit -m "feat(vestack): relax the module id rule and add part naming rules"
```

---

### Task 2: Module frame

Derives a module's local frame from its bottom floor's vertices: minimum-area enclosing rectangle in plan, X along its longer side, 180° tie-break toward the model's +X.

**Files:**
- Create: `vestack/frame.py`
- Test: `tests/test_frame.py`

**Interfaces:**
- Produces: `Point3 = Tuple[float, float, float]`; `LocalBox(lo: Point3, hi: Point3)` with `.size`, `.centre`, `.contains(point, tolerance=0.0)`; `union(boxes: Sequence[LocalBox]) -> LocalBox`; `ModuleFrame(origin, x_axis, y_axis, z_axis, length, width, plan_area_ratio)` with `.to_local(p)`, `.to_model(p)`, `.box_of(vertices) -> LocalBox`; `frame_from_floor(vertices: Sequence[Point3]) -> Optional[ModuleFrame]`; also `convex_hull`, `polygon_area`, `min_area_rectangle`.

- [ ] **Step 1: Write the failing test** — create `tests/test_frame.py`:

```python
"""Tests for the module frame. Pure geometry, no Cadwork."""
import math
import unittest
from typing import List, Sequence, Tuple

from vestack.frame import LocalBox, frame_from_floor, union

Point3 = Tuple[float, float, float]


def box_vertices(x0: float, y0: float, z0: float,
                 x1: float, y1: float, z1: float) -> List[Point3]:
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def rotated(points: Sequence[Point3], degrees: float,
            shift: Point3 = (0.0, 0.0, 0.0)) -> List[Point3]:
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s + shift[0], x * s + y * c + shift[1], z + shift[2])
            for x, y, z in points]


FLOOR = box_vertices(0, 0, 0, 6000, 2500, 220)


class Orientation(unittest.TestCase):
    def assertVector(self, actual: Sequence[float], expected: Sequence[float]) -> None:
        # 0.01 mm: hull points are rounded to 0.001 mm, outputs to 1 mm.
        for a, e in zip(actual, expected):
            self.assertAlmostEqual(a, e, delta=0.01)

    def test_an_aligned_floor_gives_the_model_axes(self) -> None:
        frame = frame_from_floor(FLOOR)
        assert frame is not None
        self.assertVector(frame.x_axis, (1, 0, 0))
        self.assertVector(frame.y_axis, (0, 1, 0))
        self.assertVector(frame.z_axis, (0, 0, 1))
        self.assertVector(frame.origin, (0, 0, 0))
        self.assertAlmostEqual(frame.length, 6000)
        self.assertAlmostEqual(frame.width, 2500)

    def test_x_runs_along_the_longer_side(self) -> None:
        frame = frame_from_floor(box_vertices(0, 0, 0, 2500, 6000, 220))
        assert frame is not None
        self.assertVector(frame.x_axis, (0, 1, 0))
        self.assertVector(frame.y_axis, (-1, 0, 0))
        self.assertAlmostEqual(frame.length, 6000)

    def test_a_floor_rotated_by_90_degrees_keeps_x_on_plus_y(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 90, shift=(10000, 5000, 0)))
        assert frame is not None
        self.assertVector(frame.x_axis, (0, 1, 0))
        self.assertVector(frame.origin, (10000, 5000, 0))

    def test_a_floor_rotated_by_37_degrees(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 37, shift=(500, 800, 300)))
        assert frame is not None
        a = math.radians(37)
        self.assertVector(frame.x_axis, (math.cos(a), math.sin(a), 0))
        self.assertVector(frame.origin, (500, 800, 300))
        self.assertAlmostEqual(frame.length, 6000, delta=0.01)
        self.assertAlmostEqual(frame.width, 2500, delta=0.01)

    def test_180_degree_tie_break_keeps_x_within_90_degrees_of_plus_x(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 180 + 37))
        assert frame is not None
        self.assertGreater(frame.x_axis[0], 0)

    def test_every_floor_vertex_has_non_negative_local_coordinates(self) -> None:
        points = rotated(FLOOR, 123, shift=(-4000, 2000, 50))
        frame = frame_from_floor(points)
        assert frame is not None
        for p in points:
            x, y, z = frame.to_local(p)
            self.assertGreaterEqual(x, -1e-6)
            self.assertGreaterEqual(y, -1e-6)
            self.assertGreaterEqual(z, -1e-6)

    def test_to_model_inverts_to_local(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 37, shift=(500, 800, 300)))
        assert frame is not None
        point = (1234.0, -56.0, 789.0)
        self.assertVector(frame.to_local(frame.to_model(point)), point)


class Quality(unittest.TestCase):
    def test_a_rectangle_has_a_plan_area_ratio_of_one(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 37))
        assert frame is not None
        self.assertAlmostEqual(frame.plan_area_ratio, 1.0, places=6)

    def test_an_l_shaped_floor_has_a_low_ratio(self) -> None:
        l_shape = (box_vertices(0, 0, 0, 6000, 1000, 220)
                   + box_vertices(0, 0, 0, 1000, 6000, 220))
        frame = frame_from_floor(l_shape)
        assert frame is not None
        self.assertLess(frame.plan_area_ratio, 0.8)

    def test_degenerate_input_gives_no_frame(self) -> None:
        self.assertIsNone(frame_from_floor([]))
        self.assertIsNone(frame_from_floor([(0, 0, 0), (100, 0, 0), (200, 0, 10)]))


class Boxes(unittest.TestCase):
    def test_box_of_expresses_vertices_in_the_frame(self) -> None:
        frame = frame_from_floor(rotated(FLOOR, 90, shift=(10000, 5000, 0)))
        assert frame is not None
        wall = rotated(box_vertices(0, 0, 220, 6000, 200, 2900), 90, shift=(10000, 5000, 0))
        box = frame.box_of(wall)
        for actual, expected in zip(box.lo + box.hi, (0, 0, 220, 6000, 200, 2900)):
            self.assertAlmostEqual(actual, expected, places=6)

    def test_union_and_contains(self) -> None:
        box = union([LocalBox((0, 0, 0), (1, 1, 1)), LocalBox((2, -1, 0), (3, 1, 5))])
        self.assertEqual((box.lo, box.hi), ((0, -1, 0), (3, 1, 5)))
        self.assertTrue(box.contains((1.5, 0, 2)))
        self.assertFalse(box.contains((4, 0, 0)))
        self.assertTrue(box.contains((3.05, 0, 0), tolerance=0.1))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_frame -v`
Expected: ERROR, `No module named 'vestack.frame'`.

- [ ] **Step 3: Create `vestack/frame.py`:**

```python
"""Module frame: a right-handed frame local to one module.

Pure geometry, no Cadwork import. The frame comes from the bottom floor's
vertices: X runs along the longer side of the minimum-area rectangle that
encloses them in plan, Z is vertical, Y completes the frame. The origin is the
floor corner from which every floor vertex has x >= 0 and y >= 0, at the
underside of the floor. Lengths are millimetres.
"""
import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

Point2 = Tuple[float, float]
Point3 = Tuple[float, float, float]

_EPS = 1e-9


def _dot(a: Point3, b: Point3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


@dataclass(frozen=True)
class LocalBox:
    """Axis-aligned box in a module frame."""

    lo: Point3
    hi: Point3

    @property
    def size(self) -> Point3:
        return (self.hi[0] - self.lo[0], self.hi[1] - self.lo[1], self.hi[2] - self.lo[2])

    @property
    def centre(self) -> Point3:
        return ((self.lo[0] + self.hi[0]) / 2, (self.lo[1] + self.hi[1]) / 2,
                (self.lo[2] + self.hi[2]) / 2)

    def contains(self, point: Point3, tolerance: float = 0.0) -> bool:
        return all(self.lo[i] - tolerance <= point[i] <= self.hi[i] + tolerance
                   for i in range(3))


def union(boxes: Sequence[LocalBox]) -> LocalBox:
    """Smallest box containing every given box."""
    return LocalBox(
        (min(b.lo[0] for b in boxes), min(b.lo[1] for b in boxes), min(b.lo[2] for b in boxes)),
        (max(b.hi[0] for b in boxes), max(b.hi[1] for b in boxes), max(b.hi[2] for b in boxes)),
    )


@dataclass(frozen=True)
class ModuleFrame:
    """A module's local frame, expressed in model coordinates."""

    origin: Point3
    x_axis: Point3
    y_axis: Point3
    z_axis: Point3
    length: float           # floor extent along X
    width: float            # floor extent along Y
    plan_area_ratio: float  # floor hull area / enclosing rectangle area

    def to_local(self, point: Point3) -> Point3:
        d = (point[0] - self.origin[0], point[1] - self.origin[1], point[2] - self.origin[2])
        return (_dot(d, self.x_axis), _dot(d, self.y_axis), _dot(d, self.z_axis))

    def to_model(self, point: Point3) -> Point3:
        x, y, z = point
        o, ax, ay, az = self.origin, self.x_axis, self.y_axis, self.z_axis
        return (o[0] + x * ax[0] + y * ay[0] + z * az[0],
                o[1] + x * ax[1] + y * ay[1] + z * az[1],
                o[2] + x * ax[2] + y * ay[2] + z * az[2])

    def box_of(self, vertices: Sequence[Point3]) -> LocalBox:
        """Bounding box, in this frame, of vertices given in model coordinates."""
        local = [self.to_local(v) for v in vertices]
        xs, ys, zs = zip(*local)
        return LocalBox((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs)))


def _cross(o: Point2, a: Point2, b: Point2) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def convex_hull(points: Sequence[Point2]) -> List[Point2]:
    """Convex hull, counter-clockwise (Andrew's monotone chain)."""
    pts = sorted({(round(x, 3), round(y, 3)) for x, y in points})
    if len(pts) <= 2:
        return pts
    lower: List[Point2] = []
    for p in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], p) <= _EPS:
            lower.pop()
        lower.append(p)
    upper: List[Point2] = []
    for p in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], p) <= _EPS:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def polygon_area(polygon: Sequence[Point2]) -> float:
    """Area of a simple polygon (shoelace formula)."""
    n = len(polygon)
    twice = sum(polygon[i][0] * polygon[(i + 1) % n][1]
                - polygon[(i + 1) % n][0] * polygon[i][1] for i in range(n))
    return abs(twice) / 2.0


def min_area_rectangle(hull: Sequence[Point2]) -> Optional[Tuple[Point2, float, float]]:
    """Direction and extents of the minimum-area rectangle enclosing a hull.

    One rectangle side lies along a hull edge, so trying each edge suffices.
    Returns (unit direction of that side, extent along it, extent across it).
    """
    best: Optional[Tuple[Point2, float, float]] = None
    best_area = math.inf
    n = len(hull)
    for i in range(n):
        ex, ey = hull[(i + 1) % n][0] - hull[i][0], hull[(i + 1) % n][1] - hull[i][1]
        edge = math.hypot(ex, ey)
        if edge < _EPS:
            continue
        ux, uy = ex / edge, ey / edge
        us = [px * ux + py * uy for px, py in hull]
        vs = [-px * uy + py * ux for px, py in hull]
        du, dv = max(us) - min(us), max(vs) - min(vs)
        if du * dv < best_area - _EPS:
            best, best_area = ((ux, uy), du, dv), du * dv
    return best


def frame_from_floor(vertices: Sequence[Point3]) -> Optional[ModuleFrame]:
    """Module frame from the bottom floor's vertices, or None if degenerate."""
    hull = convex_hull([(p[0], p[1]) for p in vertices])
    if len(hull) < 3:
        return None
    rectangle = min_area_rectangle(hull)
    if rectangle is None:
        return None
    (ux, uy), du, dv = rectangle
    xd = (ux, uy) if du >= dv else (-uy, ux)
    # 180-degree tie-break: X within 90 degrees of the model's +X; when exactly
    # perpendicular to it, X is +Y.
    if xd[0] < -_EPS or (abs(xd[0]) <= _EPS and xd[1] < 0):
        xd = (-xd[0], -xd[1])
    if abs(xd[0]) <= _EPS:
        xd = (0.0, 1.0 if xd[1] > 0 else -1.0)
    if abs(xd[1]) <= _EPS:
        xd = (1.0 if xd[0] > 0 else -1.0, 0.0)
    x_axis: Point3 = (xd[0], xd[1], 0.0)
    y_axis: Point3 = (-xd[1] + 0.0, xd[0], 0.0)
    z_axis: Point3 = (0.0, 0.0, 1.0)

    us = [p[0] * x_axis[0] + p[1] * x_axis[1] for p in vertices]
    vs = [p[0] * y_axis[0] + p[1] * y_axis[1] for p in vertices]
    u0, v0 = min(us), min(vs)
    origin: Point3 = (u0 * x_axis[0] + v0 * y_axis[0],
                      u0 * x_axis[1] + v0 * y_axis[1],
                      min(p[2] for p in vertices))
    length, width = max(us) - u0, max(vs) - v0
    area = length * width
    ratio = polygon_area(hull) / area if area > _EPS else 0.0
    return ModuleFrame(origin, x_axis, y_axis, z_axis, length, width, ratio)
```

- [ ] **Step 4: Run the tests**

Run: `.venv\Scripts\python -m unittest tests.test_frame -v`
Expected: 12 tests, `OK`. Tolerances are 0.01 mm because hull points are rounded to 0.001 mm.

- [ ] **Step 5: Commit**

```bash
git add vestack/frame.py tests/test_frame.py
git commit -m "feat(vestack): derive a module frame from the bottom floor's vertices"
```

---

### Task 3: Object inventory

The pure core: splits elements into modules (subgroup first, then the Module attribute), builds one object per part subgroup, takes wall envelopes from the `MOB<section>` body, attaches `MEX` joinery to the wall containing its centre, groups the rest by geometry, and returns summary or detail. Also says which elements need vertices (`geometry_needed`), so the bridge reads as few as possible.

**Files:**
- Create: `vestack/object_inventory.py`
- Create: `tests/object_fixtures.py` (shared by Tasks 3, 4, 5, 7)
- Test: `tests/test_object_inventory.py`

**Interfaces:**
- Consumes: Task 1 (`naming`, `conventions`), Task 2 (`frame`), `module_inventory.classify(bbox) -> str`.
- Produces: `ObjectSnapshot(element_id: int, name="", group="", subgroup="", module_attribute="", complex_code="", material="", vertices: Tuple[Point3, ...] = ())` (mutable dataclass: the bridge fills `vertices` and `material` in place); `SCHEMA = "vestack.object_inventory/1"`; `DETAIL_LEVELS = ("none", "envelope", "vertices")`; `element_module(s) -> Tuple[Optional[str], Optional[PartRef], bool]`; `geometry_needed(snapshots, module_ids=None, detail_all=False) -> Set[int]`; `build_object_inventory(snapshots, module_ids=None, detail_all=False, element_detail="none", source=None) -> Dict[str, Any]` (raises `ValueError` on a bad `element_detail`). Fixtures: `box(x0, y0, z0, x1, y1, z1)`, `element(...)`, `module_m1(degrees=0.0, shift=(0, 0, 0))`.

- [ ] **Step 1: Write the fixtures and the failing tests** — create `tests/object_fixtures.py`:

```python
"""A small Vestack module as ObjectSnapshot values, shaped like the spike model.

Module M1, 6000 x 2500 mm: a two-panel bottom floor (subgroup M1-F1, group
"Plancher bas"), wall M1-W1 along -y with its MOB200 body and studs, wall M1-W2
along +x with a MOB145 body, a cold-roof part M1-TF0, a posts part M1-Poteaux,
a joinery item in W1 that has no subgroup (as most MEX elements do), and a
drilling in group "Usinage". Everything can be rotated and shifted in plan.
"""
import math
from typing import List, Sequence, Tuple

from vestack.object_inventory import ObjectSnapshot

Point3 = Tuple[float, float, float]


def box(x0: float, y0: float, z0: float, x1: float, y1: float, z1: float) -> List[Point3]:
    return [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]


def place(points: Sequence[Point3], degrees: float, shift: Point3) -> Tuple[Point3, ...]:
    a = math.radians(degrees)
    c, s = math.cos(a), math.sin(a)
    return tuple((x * c - y * s + shift[0], x * s + y * c + shift[1], z + shift[2])
                 for x, y, z in points)


def element(element_id: int, vertices: List[Point3], *, name: str = "", group: str = "",
            subgroup: str = "", module: str = "", complex_code: str = "",
            material: str = "", degrees: float = 0.0,
            shift: Point3 = (0.0, 0.0, 0.0)) -> ObjectSnapshot:
    return ObjectSnapshot(element_id=element_id, name=name, group=group, subgroup=subgroup,
                          module_attribute=module, complex_code=complex_code,
                          material=material, vertices=place(vertices, degrees, shift))


def module_m1(degrees: float = 0.0, shift: Point3 = (0.0, 0.0, 0.0)) -> List[ObjectSnapshot]:
    def e(element_id: int, vertices: List[Point3], **kw: str) -> ObjectSnapshot:
        return element(element_id, vertices, degrees=degrees, shift=shift, module="M1", **kw)

    return [
        e(1, box(0, 0, 0, 3000, 2500, 220), name="OSB 9mm", group="Plancher bas",
          subgroup="M1-F1", complex_code="PB-AUX-01", material="OSB-9"),
        e(2, box(3000, 0, 0, 6000, 2500, 220), name="OSB 9mm", group="Plancher bas",
          subgroup="M1-F1", complex_code="PB-AUX-01", material="OSB-9"),
        e(10, box(0, 0, 220, 6000, 212, 2865), name="MOB200", group="MOB", subgroup="M1-W1"),
        e(11, box(0, 6, 220, 45, 206, 2865), name="montant", group="MOB", subgroup="M1-W1",
          material="C24"),
        e(12, box(955, 6, 220, 1000, 206, 2865), name="montant", group="MOB", subgroup="M1-W1",
          material="C24"),
        e(20, box(5855, 212, 220, 6000, 2288, 2865), name="MOB145", group="MOB",
          subgroup="M1-W2"),
        e(30, box(0, 0, 2865, 6000, 2500, 3400), name="fermette", group="Toiture froide",
          subgroup="M1-TF0"),
        e(40, box(2900, 1150, 220, 3100, 1350, 2865), name="poteau", group="MOB",
          subgroup="M1-Poteaux"),
        element(50, box(1000, 0, 310, 2455, 212, 2625), name="MEX type B", group="MEX",
                degrees=degrees, shift=shift),
        e(60, box(100, 0, 0, 110, 10, 10), name="perçage Ø4", group="Usinage",
          subgroup="Usinage PB - Perçages rive"),
    ]
```

Then create `tests/test_object_inventory.py`:

```python
"""Tests for the Vestack object inventory. Pure logic, no Cadwork."""
import unittest
from typing import Any, Dict, List

from tests.object_fixtures import box, element, module_m1
from vestack.object_inventory import (
    ObjectSnapshot,
    build_object_inventory,
    geometry_needed,
)


def module_entry(inventory: Dict[str, Any], module_id: str = "M1") -> Dict[str, Any]:
    return next(m for m in inventory["modules"] if m["module_id"] == module_id)


def objects_by_id(inventory: Dict[str, Any], module_id: str = "M1") -> Dict[str, Dict[str, Any]]:
    return {o["id"]: o for o in module_entry(inventory, module_id)["objects"]}


def detail(snapshots: List[ObjectSnapshot], **kw: Any) -> Dict[str, Any]:
    return build_object_inventory(snapshots, module_ids=["M1"], **kw)


class Summary(unittest.TestCase):
    def test_reports_the_schema_and_the_module(self) -> None:
        inventory = build_object_inventory(module_m1())
        self.assertEqual(inventory["schema"], "vestack.object_inventory/1")
        self.assertEqual([m["module_id"] for m in inventory["modules"]], ["M1"])

    def test_counts_objects_per_type_including_openings(self) -> None:
        counts = module_entry(build_object_inventory(module_m1()))["counts"]
        self.assertEqual(counts, {"slab": 1, "wall": 2, "roof": 1, "other": 1, "opening": 1})

    def test_the_summary_has_a_frame_but_no_objects(self) -> None:
        entry = module_entry(build_object_inventory(module_m1()))
        self.assertNotIn("objects", entry)
        frame = entry["frame"]
        self.assertEqual((frame["length"], frame["width"]), (6000, 2500))
        self.assertEqual(frame["origin_model"], [0, 0, 0])
        self.assertEqual(frame["height"], 3400)

    def test_processing_elements_are_counted_apart(self) -> None:
        self.assertEqual(build_object_inventory(module_m1())["processing_element_count"], 1)

    def test_modules_are_sorted_numerically(self) -> None:
        snaps = module_m1()
        snaps += [element(100 + s.element_id, list(s.vertices), name=s.name, group=s.group,
                          subgroup=s.subgroup.replace("M1-", "M10-"), shift=(0, 10000, 0))
                  for s in module_m1() if s.subgroup.startswith("M1-")]
        snaps += [element(200 + s.element_id, list(s.vertices), name=s.name, group=s.group,
                          subgroup=s.subgroup.replace("M1-", "M2-"), shift=(0, 20000, 0))
                  for s in module_m1() if s.subgroup.startswith("M1-")]
        ids = [m["module_id"] for m in build_object_inventory(snaps)["modules"]]
        self.assertEqual(ids, ["M1", "M2", "M10"])


class Walls(unittest.TestCase):
    def test_wall_axis_thickness_and_height_come_from_the_body(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W1"]
        self.assertEqual(wall["start"], [0, 106, 220])
        self.assertEqual(wall["end"], [6000, 106, 220])
        self.assertEqual((wall["thickness"], wall["height"]), (212, 2645))
        self.assertEqual(wall["side"], "-y")

    def test_wall_type_and_stud_section(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W1"]
        self.assertEqual((wall["wall_type"], wall["stud_section"]), ("MOB200", 200))

    def test_a_wall_along_y_on_the_far_edge(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W2"]
        self.assertEqual(wall["side"], "+x")
        self.assertEqual((wall["start"], wall["end"]), ([5928, 212, 220], [5928, 2288, 220]))
        self.assertEqual(wall["thickness"], 145)

    def test_the_wall_lists_all_its_elements(self) -> None:
        wall = objects_by_id(detail(module_m1()))["M1-W1"]
        self.assertEqual(wall["element_ids"], [10, 11, 12])

    def test_an_element_sticking_out_of_the_body_is_warned(self) -> None:
        snaps = module_m1() + [element(13, box(0, 212, 220, 600, 358, 2865), name="Joue",
                                       group="MOB", subgroup="M1-W1")]
        wall = objects_by_id(detail(snaps))["M1-W1"]
        self.assertTrue(any("146 mm" in w and "[13]" in w for w in wall["warnings"]),
                        wall["warnings"])

    def test_a_wall_without_body_uses_the_union_and_is_warned(self) -> None:
        snaps = [s for s in module_m1() if s.element_id != 10]
        wall = objects_by_id(detail(snaps))["M1-W1"]
        self.assertIsNone(wall["wall_type"])
        self.assertEqual(wall["start"], [0, 106, 220])
        self.assertTrue(any("0 wall body" in w for w in wall["warnings"]))

    def test_two_bodies_are_warned(self) -> None:
        snaps = module_m1() + [element(14, box(0, 0, 220, 6000, 212, 2865), name="MOB200",
                                       group="MOB", subgroup="M1-W1")]
        wall = objects_by_id(detail(snaps))["M1-W1"]
        self.assertTrue(any("2 wall body" in w for w in wall["warnings"]))


class RotatedModules(unittest.TestCase):
    def test_local_results_do_not_depend_on_the_module_placement(self) -> None:
        reference = objects_by_id(detail(module_m1()))
        for degrees, shift in ((90, (10000, 5000, 0)), (37, (500, -800, 300)), (-60, (0, 0, 0))):
            rotated = objects_by_id(detail(module_m1(degrees, shift)))
            for object_id in ("M1-W1", "M1-W2"):
                for key in ("start", "end", "thickness", "height", "side", "openings"):
                    self.assertEqual(rotated[object_id][key], reference[object_id][key],
                                     f"{object_id}.{key} at {degrees} degrees")

    def test_a_module_turned_beyond_90_degrees_is_seen_from_the_other_end(self) -> None:
        # The 180-degree tie-break keeps X within 90 degrees of the model's +X, so
        # a module placed at 217 degrees gets the frame of one placed at 37: its
        # -y wall is reported on +y. Claude reads that off x_axis_model.
        wall = objects_by_id(detail(module_m1(217, (0, 0, 0))))["M1-W1"]
        self.assertEqual(wall["side"], "+y")

    def test_the_frame_reports_its_axes_in_model_coordinates(self) -> None:
        frame = module_entry(build_object_inventory(module_m1(90, (10000, 5000, 0))))["frame"]
        self.assertEqual(frame["x_axis_model"], [0.0, 1.0, 0.0])
        self.assertEqual(frame["y_axis_model"], [-1.0, 0.0, 0.0])
        self.assertEqual(frame["origin_model"], [10000, 5000, 0])


class Slabs(unittest.TestCase):
    def test_the_bottom_floor_is_one_object_over_its_panels(self) -> None:
        slab = objects_by_id(detail(module_m1()))["M1-F1"]
        self.assertEqual(slab["level"], "bottom")
        self.assertEqual((slab["length"], slab["width"], slab["thickness"]), (6000, 2500, 220))
        self.assertEqual(slab["element_ids"], [1, 2])

    def test_roof_and_named_parts_keep_their_prefix(self) -> None:
        objects = objects_by_id(detail(module_m1()))
        self.assertEqual((objects["M1-TF0"]["type"], objects["M1-TF0"]["part"]), ("roof", "TF"))
        self.assertEqual((objects["M1-Poteaux"]["type"], objects["M1-Poteaux"]["part"]),
                         ("other", "Poteaux"))


class Openings(unittest.TestCase):
    def test_joinery_without_subgroup_is_attached_to_its_wall(self) -> None:
        openings = objects_by_id(detail(module_m1()))["M1-W1"]["openings"]
        self.assertEqual(openings, [{"id": "M1-W1-O1", "name": "MEX type B", "offset": 1000,
                                     "sill": 90, "width": 1455, "height": 2315,
                                     "element_ids": [50]}])

    def test_each_joinery_is_attached_once(self) -> None:
        # Two modules whose walls overlap: the joinery fits both, lands in one.
        twin = [element(100 + s.element_id, list(s.vertices), name=s.name, group=s.group,
                        subgroup=s.subgroup.replace("M1-", "M2-"))
                for s in module_m1() if s.subgroup.startswith("M1-")]
        inventory = build_object_inventory(module_m1() + twin, detail_all=True)
        hosts = [o["id"] for m in inventory["modules"] for o in m["objects"]
                 for opening in o.get("openings", []) if 50 in opening["element_ids"]]
        self.assertEqual(hosts, ["M1-W1"])

    def test_joinery_in_no_wall_is_an_other_object_with_a_warning(self) -> None:
        stray = element(51, box(2000, 1000, 500, 2500, 1100, 1500), name="MEX type A",
                        module="M1")
        objects = objects_by_id(detail(module_m1() + [stray]))
        record = objects["M1-joinery51"]
        self.assertEqual(record["type"], "other")
        self.assertTrue(any("lies in no wall" in w for w in record["warnings"]))

    def test_joinery_with_no_module_and_no_wall_is_unattached(self) -> None:
        stray = element(52, box(90000, 0, 0, 90100, 100, 100), name="MEX type A")
        self.assertIn(52, build_object_inventory(module_m1() + [stray])["unattached_element_ids"])


class ModuleAssignment(unittest.TestCase):
    def test_a_disagreeing_module_attribute_is_warned_and_the_subgroup_wins(self) -> None:
        snaps = module_m1()
        snaps[3] = element(11, box(0, 6, 220, 45, 206, 2865), name="montant", group="MOB",
                           subgroup="M1-W1", module="M2")
        entry = module_entry(build_object_inventory(snaps))
        self.assertTrue(any("1 elements have a Module attribute" in w for w in entry["warnings"]))
        self.assertEqual([m["module_id"] for m in build_object_inventory(snaps)["modules"]], ["M1"])

    def test_zero_padded_attribute_agrees_with_subgroup(self) -> None:
        snaps = module_m1()
        snaps[3] = element(11, box(0, 6, 220, 45, 206, 2865), name="montant", group="MOB",
                           subgroup="M1-W1", module="M001")
        entry = module_entry(build_object_inventory(snaps))
        self.assertFalse(any("Module attribute" in w for w in entry["warnings"]))

    def test_a_bare_part_takes_its_module_from_the_attribute(self) -> None:
        snaps = module_m1() + [element(15, box(1500, 6, 220, 1545, 206, 2865), name="montant",
                                       group="MOB", subgroup="W1", module="M1")]
        self.assertIn(15, objects_by_id(detail(snaps))["M1-W1"]["element_ids"])

    def test_an_element_without_any_module_is_unattached(self) -> None:
        stray = element(70, box(0, 0, 0, 10, 10, 10), name="Connecteur", group="Jonction")
        self.assertIn(70, build_object_inventory(module_m1() + [stray])["unattached_element_ids"])

    def test_requesting_an_unknown_module_is_warned(self) -> None:
        inventory = build_object_inventory(module_m1(), module_ids=["M9"])
        self.assertIn("module M9 not found in the scanned elements", inventory["warnings"])

    def test_module_ids_are_matched_in_any_spelling(self) -> None:
        inventory = build_object_inventory(module_m1(), module_ids=["M001"])
        self.assertIn("objects", module_entry(inventory))


class GeometricFallback(unittest.TestCase):
    def loose_module(self) -> List[ObjectSnapshot]:
        """Module M2 with no part subgroup: only the Module attribute."""
        return [
            element(1, box(0, 0, 0, 6000, 2500, 220), name="OSB", module="M2"),
            element(2, box(500, 0, 220, 545, 200, 2865), name="montant", module="M2"),
            element(3, box(2000, 0, 220, 2045, 200, 2865), name="montant", module="M2"),
            element(4, box(0, 1200, 220, 4000, 1300, 2865), name="cloison", module="M2"),
            element(5, box(3000, 900, 400, 3200, 1000, 600), name="boitier", module="M2"),
        ]

    def test_the_summary_counts_unclassified_elements(self) -> None:
        entry = module_entry(build_object_inventory(self.loose_module()), "M2")
        self.assertEqual(entry["unclassified_element_count"], 5)
        self.assertEqual(entry["grouping_source"], "geometry")

    def test_the_detail_groups_by_geometry(self) -> None:
        entry = module_entry(build_object_inventory(self.loose_module(), module_ids=["M2"]), "M2")
        kinds = [(o["type"], o.get("side"), o.get("level")) for o in entry["objects"]]
        self.assertEqual(kinds, [("slab", None, "bottom"), ("wall", "-y", None),
                                 ("wall", None, None), ("other", None, None)])
        self.assertEqual(entry["objects"][1]["element_ids"], [2, 3])

    def test_a_corner_element_goes_to_the_first_side_in_order(self) -> None:
        snaps = self.loose_module() + [element(6, box(0, 0, 220, 45, 200, 2865),
                                               name="montant", module="M2")]
        entry = module_entry(build_object_inventory(snaps, module_ids=["M2"]), "M2")
        corner_wall = next(o for o in entry["objects"] if 6 in o["element_ids"])
        self.assertEqual(corner_wall["side"], "-x")

    def test_a_module_reduced_to_its_id_in_the_subgroup_mixes_both_sources(self) -> None:
        snaps = module_m1() + [element(80, box(2000, 1200, 220, 5000, 1300, 2865),
                                       name="cloison", subgroup="M1")]
        entry = module_entry(detail(snaps))
        self.assertEqual(entry["grouping_source"], "subgroup+geometry")
        self.assertIn(80, entry["objects"][-1]["element_ids"])


class Warnings(unittest.TestCase):
    def test_a_module_without_floor_has_no_frame(self) -> None:
        snaps = [s for s in module_m1() if s.subgroup != "M1-F1"]
        snaps = [s for s in snaps if s.subgroup != "M1-TF0"]
        entry = module_entry(detail(snaps))
        self.assertIsNone(entry["frame"])
        self.assertEqual(entry["objects"], [])
        self.assertIn("no bottom floor found: no frame, no objects", entry["warnings"])

    def test_an_l_shaped_floor_is_warned_and_objects_omitted(self) -> None:
        snaps = [s for s in module_m1() if s.subgroup != "M1-F1"]
        snaps += [element(1, box(0, 0, 0, 6000, 1000, 220), group="Plancher bas",
                          subgroup="M1-F1"),
                  element(2, box(0, 0, 0, 1000, 6000, 220), group="Plancher bas",
                          subgroup="M1-F1")]
        entry = module_entry(detail(snaps))
        self.assertEqual(entry["objects"], [])
        self.assertTrue(any("not rectangular" in w for w in entry["warnings"]))


class ElementDetail(unittest.TestCase):
    def test_envelope_detail_lists_elements_in_the_module_frame(self) -> None:
        wall = objects_by_id(detail(module_m1(90, (10000, 5000, 0)),
                                    element_detail="envelope"))["M1-W1"]
        stud = next(e for e in wall["elements"] if e["element_id"] == 12)
        self.assertEqual(stud, {"element_id": 12, "name": "montant", "material": "C24",
                                "origin": [955, 6, 220], "size": [45, 200, 2645]})

    def test_vertices_detail_adds_local_vertices(self) -> None:
        wall = objects_by_id(detail(module_m1(37, (500, 800, 0)),
                                    element_detail="vertices"))["M1-W1"]
        stud = next(e for e in wall["elements"] if e["element_id"] == 12)
        self.assertIn([955, 6, 220], stud["vertices"])
        self.assertEqual(len(stud["vertices"]), 8)

    def test_no_detail_by_default(self) -> None:
        self.assertNotIn("elements", objects_by_id(detail(module_m1()))["M1-W1"])

    def test_an_invalid_level_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            build_object_inventory(module_m1(), element_detail="all")


class GeometryNeeded(unittest.TestCase):
    def test_the_summary_needs_floors_bodies_and_joinery_only(self) -> None:
        self.assertEqual(geometry_needed(module_m1()), {1, 2, 10, 20, 50})

    def test_a_wall_without_single_body_needs_all_its_elements(self) -> None:
        snaps = [s for s in module_m1() if s.element_id != 10]
        self.assertTrue({11, 12} <= geometry_needed(snaps))

    def test_a_detailed_module_needs_every_element_but_processings(self) -> None:
        self.assertEqual(geometry_needed(module_m1(), module_ids=["M1"]),
                         {1, 2, 10, 11, 12, 20, 30, 40, 50})

    def test_a_module_without_slab_part_needs_everything(self) -> None:
        snaps = [element(1, box(0, 0, 0, 10, 10, 10), module="M3"),
                 element(2, box(0, 0, 0, 10, 10, 10), subgroup="M3-W1")]
        self.assertEqual(geometry_needed(snaps), {1, 2})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv\Scripts\python -m unittest tests.test_object_inventory -v`
Expected: ERROR, `No module named 'vestack.object_inventory'`.

- [ ] **Step 3: Create `vestack/object_inventory.py`:**

```python
"""Object inventory: walls, slabs, roofs and openings per module, in module frames.

Pure domain logic, no Cadwork import: it takes ObjectSnapshot values and returns
the vestack.object_inventory/1 structure documented in OBJECT_INVENTORY.md. The
adapter that reads snapshots from a live model is vestack/bridge_handler.py.

Reading vertices is the costly part of a scan (14 ms per element on Cadwork
2026), so the bridge first reads attributes only, asks geometry_needed() which
elements need vertices, then reads those. Elements whose vertices were not read
simply carry an empty tuple.
"""
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Collection, Dict, List, Optional, Sequence, Set, Tuple

from . import conventions as cv
from .frame import LocalBox, ModuleFrame, Point3, frame_from_floor, union
from .module_inventory import classify
from .naming import (
    PartRef,
    floor_level_hint,
    is_joinery,
    is_processing,
    module_number,
    parse_module_id,
    parse_part,
    wall_body_section,
)

SCHEMA = "vestack.object_inventory/1"
DETAIL_LEVELS: Tuple[str, ...] = ("none", "envelope", "vertices")
SIDES: Tuple[str, ...] = ("-x", "+x", "-y", "+y")


@dataclass
class ObjectSnapshot:
    """What the object inventory needs to know about one Cadwork element."""

    element_id: int
    name: str = ""
    group: str = ""
    subgroup: str = ""
    module_attribute: str = ""
    complex_code: str = ""
    material: str = ""
    vertices: Tuple[Point3, ...] = ()


@dataclass
class _Module:
    module_id: str
    parts: Dict[str, List[ObjectSnapshot]] = field(default_factory=dict)
    part_refs: Dict[str, PartRef] = field(default_factory=dict)
    loose: List[ObjectSnapshot] = field(default_factory=list)
    disagreements: int = 0


# --- helpers ---------------------------------------------------------------

def _mm(value: float) -> int:
    return int(round(value))


def _pt(point: Sequence[float]) -> List[int]:
    return [_mm(c) for c in point]


def _model_bbox(vertices: Sequence[Point3]) -> Tuple[float, float, float, float, float, float]:
    xs, ys, zs = zip(*vertices)
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def element_module(snapshot: ObjectSnapshot) -> Tuple[Optional[str], Optional[PartRef], bool]:
    """Module and part of one element, and whether subgroup and attribute disagree.

    The subgroup wins over the Module attribute, then come group and name.
    """
    part = parse_part(snapshot.subgroup)
    from_subgroup = (part.module_id if part and part.module_id
                     else parse_module_id(snapshot.subgroup))
    from_attribute = parse_module_id(snapshot.module_attribute)
    module = (from_subgroup or from_attribute or parse_module_id(snapshot.group)
              or parse_module_id(snapshot.name))
    disagree = bool(from_subgroup and from_attribute and from_subgroup != from_attribute)
    return module, part, disagree


def _object_id(module_id: str, part: PartRef) -> str:
    return f"{module_id}-{part.prefix}{part.number}"


def _part_sort_key(object_id: str) -> Tuple[str, int, str]:
    tail = object_id.split("-", 1)[1]
    letters = tail.rstrip("0123456789")
    digits = tail[len(letters):]
    return (letters.upper(), int(digits) if digits else -1, tail)


def _partition(snapshots: Sequence[ObjectSnapshot]
               ) -> Tuple[Dict[str, _Module], List[ObjectSnapshot], List[int], int]:
    """Split elements into modules, joinery, unattached ids and a processing count."""
    modules: Dict[str, _Module] = {}
    joinery: List[ObjectSnapshot] = []
    unattached: List[int] = []
    processing = 0
    for s in snapshots:
        if is_processing(s.group):
            processing += 1
            continue
        if is_joinery(s.name):
            joinery.append(s)
            continue
        module_id, part, disagree = element_module(s)
        if module_id is None:
            unattached.append(s.element_id)
            continue
        module = modules.setdefault(module_id, _Module(module_id))
        module.disagreements += int(disagree)
        if part is None:
            module.loose.append(s)
        else:
            object_id = _object_id(module_id, part)
            module.parts.setdefault(object_id, []).append(s)
            module.part_refs[object_id] = part
    return modules, joinery, unattached, processing


def _wall_bodies(elements: Sequence[ObjectSnapshot]) -> List[ObjectSnapshot]:
    return [e for e in elements if wall_body_section(e.name) is not None]


def geometry_needed(snapshots: Sequence[ObjectSnapshot],
                    module_ids: Optional[Collection[str]] = None,
                    detail_all: bool = False) -> Set[int]:
    """Ids of the elements whose vertices the inventory needs.

    Always: joinery, wall bodies (all wall elements when a wall has no single
    body), slab parts (to find the bottom floor), and every element of a module
    with no slab part. In detailed modules: every element.
    """
    requested = {parse_module_id(m) or m for m in (module_ids or [])}
    modules, joinery, _unattached, _processing = _partition(snapshots)
    needed: Set[int] = {s.element_id for s in joinery}
    for module in modules.values():
        everything = detail_all or module.module_id in requested
        has_slab_part = any(r.object_type == "slab" for r in module.part_refs.values())
        for object_id, elements in module.parts.items():
            object_type = module.part_refs[object_id].object_type
            if everything or not has_slab_part or object_type == "slab":
                needed.update(e.element_id for e in elements)
            elif object_type == "wall":
                bodies = _wall_bodies(elements)
                needed.update(e.element_id for e in (bodies if len(bodies) == 1 else elements))
        if everything or not has_slab_part:
            needed.update(e.element_id for e in module.loose)
    return needed


# --- frame -----------------------------------------------------------------

def _with_vertices(elements: Sequence[ObjectSnapshot]) -> List[ObjectSnapshot]:
    return [e for e in elements if e.vertices]


def _bottom_floor(module: _Module) -> List[ObjectSnapshot]:
    """Elements making the module's bottom floor, possibly none."""
    slab_parts = {oid: _with_vertices(els) for oid, els in module.parts.items()
                  if module.part_refs[oid].object_type == "slab"}
    slab_parts = {oid: els for oid, els in slab_parts.items() if els}
    hinted = [e for els in slab_parts.values() for e in els
              if floor_level_hint(e.group, e.complex_code) == "bottom"]
    if hinted:
        return hinted
    if slab_parts:
        return min(slab_parts.values(),
                   key=lambda els: min(v[2] for e in els for v in e.vertices))
    candidates = [e for e in _with_vertices(module.loose)
                  if classify(_model_bbox(e.vertices)) == "slab"]
    if not candidates:
        return []
    lowest = min(_model_bbox(e.vertices)[2] for e in candidates)
    return [e for e in candidates
            if _model_bbox(e.vertices)[2] < lowest + cv.TOP_FLOOR_MIN_CLEARANCE_MM]


def _frame_dict(frame: ModuleFrame, height: Optional[float]) -> Dict[str, Any]:
    return {
        "origin_model": _pt(frame.origin),
        "x_axis_model": [round(c, 6) + 0.0 for c in frame.x_axis],
        "y_axis_model": [round(c, 6) + 0.0 for c in frame.y_axis],
        "z_axis_model": [round(c, 6) + 0.0 for c in frame.z_axis],
        "length": _mm(frame.length),
        "width": _mm(frame.width),
        "height": _mm(height) if height is not None else None,
    }


# --- objects ---------------------------------------------------------------

@dataclass
class _Wall:
    object_id: str
    body: LocalBox
    along_x: bool
    start: Point3
    record: Dict[str, Any]


def _wall_geometry(box: LocalBox, frame: ModuleFrame) -> Tuple[bool, Point3, Point3, float, Optional[str]]:
    sx, sy, _sz = box.size
    along_x = sx >= sy
    band = cv.SIDE_BAND_MM
    if along_x:
        mid = (box.lo[1] + box.hi[1]) / 2
        start, end, thickness = (box.lo[0], mid, box.lo[2]), (box.hi[0], mid, box.lo[2]), sy
        side = "-y" if mid <= band else "+y" if mid >= frame.width - band else None
    else:
        mid = (box.lo[0] + box.hi[0]) / 2
        start, end, thickness = (mid, box.lo[1], box.lo[2]), (mid, box.hi[1], box.lo[2]), sx
        side = "-x" if mid <= band else "+x" if mid >= frame.length - band else None
    return along_x, start, end, thickness, side


def _make_wall(object_id: str, elements: Sequence[ObjectSnapshot], frame: ModuleFrame,
               check_union: bool) -> Optional[_Wall]:
    readable = _with_vertices(elements)
    if not readable:
        return None
    warnings: List[str] = []
    bodies = [b for b in _wall_bodies(readable)]
    boxes = {e.element_id: frame.box_of(e.vertices) for e in readable}
    if len(bodies) == 1:
        body_el = bodies[0]
        body = boxes[body_el.element_id]
        wall_type: Optional[str] = body_el.name.strip()
        section = wall_body_section(body_el.name)
    else:
        body = union(list(boxes.values()))
        wall_type, section = None, None
        warnings.append(f"{len(bodies)} wall body elements (MOB<section>): "
                        "envelope taken from the union of the wall's elements")
    if check_union and len(bodies) == 1:
        tol = cv.WALL_BODY_TOLERANCE_MM
        out = sorted(eid for eid, b in boxes.items()
                     if any(body.lo[i] - b.lo[i] > tol or b.hi[i] - body.hi[i] > tol
                            for i in range(3)))
        if out:
            whole = union(list(boxes.values()))
            excess = max(max(body.lo[i] - whole.lo[i], whole.hi[i] - body.hi[i])
                         for i in range(3))
            warnings.append(f"elements stick out of the wall body by up to {_mm(excess)} mm: "
                            f"{out}")
    along_x, start, end, thickness, side = _wall_geometry(body, frame)
    record: Dict[str, Any] = {
        "id": object_id,
        "type": "wall",
        "wall_type": wall_type,
        "stud_section": section,
        "side": side,
        "start": _pt(start),
        "end": _pt(end),
        "thickness": _mm(thickness),
        "height": _mm(body.size[2]),
        "openings": [],
        "element_ids": sorted(e.element_id for e in elements),
        "warnings": warnings,
    }
    return _Wall(object_id, body, along_x, start, record)


def _make_box_object(object_id: str, object_type: str, elements: Sequence[ObjectSnapshot],
                     frame: ModuleFrame, part: Optional[str],
                     level: Optional[str] = None) -> Optional[Dict[str, Any]]:
    readable = _with_vertices(elements)
    if not readable:
        return None
    box = union([frame.box_of(e.vertices) for e in readable])
    record: Dict[str, Any] = {"id": object_id, "type": object_type}
    if object_type == "slab":
        record.update({"level": level, "origin": _pt(box.lo), "length": _mm(box.size[0]),
                       "width": _mm(box.size[1]), "thickness": _mm(box.size[2])})
    else:
        record.update({"part": part, "origin": _pt(box.lo), "size": _pt(box.size)})
    record["element_ids"] = sorted(e.element_id for e in elements)
    record["warnings"] = []
    return record


def _slab_level(elements: Sequence[ObjectSnapshot], is_bottom: bool) -> Optional[str]:
    hints = [h for h in (floor_level_hint(e.group, e.complex_code) for e in elements) if h]
    if hints:
        return Counter(hints).most_common(1)[0][0]
    return "bottom" if is_bottom else None


def _element_details(elements: Sequence[ObjectSnapshot], frame: ModuleFrame,
                     level: str) -> List[Dict[str, Any]]:
    details = []
    for e in sorted(_with_vertices(elements), key=lambda e: e.element_id):
        box = frame.box_of(e.vertices)
        item: Dict[str, Any] = {"element_id": e.element_id, "name": e.name,
                                "material": e.material, "origin": _pt(box.lo),
                                "size": _pt(box.size)}
        if level == "vertices":
            item["vertices"] = [_pt(frame.to_local(v)) for v in e.vertices]
        details.append(item)
    return details


# --- geometric fallback ----------------------------------------------------

def _band_side(box: LocalBox, frame: ModuleFrame) -> Optional[str]:
    band = cv.SIDE_BAND_MM
    tests = {"-x": box.hi[0] <= band, "+x": box.lo[0] >= frame.length - band,
             "-y": box.hi[1] <= band, "+y": box.lo[1] >= frame.width - band}
    return next((side for side in SIDES if tests[side]), None)


def _fallback_groups(loose: Sequence[ObjectSnapshot], frame: ModuleFrame
                     ) -> List[Tuple[str, str, List[ObjectSnapshot]]]:
    """(kind, label, elements) groups for elements outside any part subgroup."""
    slabs: Dict[str, List[ObjectSnapshot]] = {}
    sides: Dict[str, List[ObjectSnapshot]] = {}
    clusters: List[Tuple[bool, float, List[ObjectSnapshot]]] = []
    others: List[ObjectSnapshot] = []
    for e in _with_vertices(loose):
        box = frame.box_of(e.vertices)
        kind = classify(box.lo + box.hi)
        if kind == "slab":
            level = "bottom" if box.lo[2] < cv.TOP_FLOOR_MIN_CLEARANCE_MM else "top"
            slabs.setdefault(level, []).append(e)
            continue
        side = _band_side(box, frame)
        if side is not None:
            sides.setdefault(side, []).append(e)
        elif kind == "wall":
            along_x = box.size[0] >= box.size[1]
            plane = box.centre[1] if along_x else box.centre[0]
            for c_axis, c_plane, members in clusters:
                if c_axis == along_x and abs(c_plane - plane) <= cv.INTERIOR_WALL_PLANE_TOLERANCE_MM:
                    members.append(e)
                    break
            else:
                clusters.append((along_x, plane, [e]))
        else:
            others.append(e)
    groups: List[Tuple[str, str, List[ObjectSnapshot]]] = []
    groups += [("slab", level, slabs[level]) for level in ("bottom", "top") if level in slabs]
    groups += [("wall", side, sides[side]) for side in SIDES if side in sides]
    groups += [("wall", "interior", members) for _a, _p, members in clusters]
    if others:
        groups.append(("other", "", others))
    return groups


# --- openings --------------------------------------------------------------

def _attach_openings(joinery: Sequence[ObjectSnapshot],
                     walls: Dict[str, List[_Wall]],
                     frames: Dict[str, ModuleFrame]
                     ) -> Tuple[Dict[str, List[Tuple[ObjectSnapshot, LocalBox]]], List[ObjectSnapshot]]:
    """Joinery attached to the wall containing its centre; the rest unattached."""
    attached: Dict[str, List[Tuple[ObjectSnapshot, LocalBox]]] = {}
    orphans: List[ObjectSnapshot] = []
    for j in joinery:
        if not j.vertices:
            orphans.append(j)
            continue
        x0, y0, z0, x1, y1, z1 = _model_bbox(j.vertices)
        centre = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        host: Optional[Tuple[_Wall, ModuleFrame]] = None
        for module_id in sorted(walls, key=module_number):
            frame = frames[module_id]
            local = frame.to_local(centre)
            for wall in walls[module_id]:
                if wall.body.contains(local, cv.JOINERY_CENTRE_TOLERANCE_MM):
                    host = (wall, frame)
                    break
            if host:
                break
        if host is None:
            orphans.append(j)
        else:
            attached.setdefault(host[0].object_id, []).append((j, host[1].box_of(j.vertices)))
    return attached, orphans


def _opening_records(wall: _Wall, items: Sequence[Tuple[ObjectSnapshot, LocalBox]]
                     ) -> List[Dict[str, Any]]:
    axis = 0 if wall.along_x else 1
    rows: List[Dict[str, Any]] = []
    for j, box in items:
        rows.append({
            "name": j.name.strip(),
            "offset": _mm(box.lo[axis] - wall.start[axis]),
            "sill": _mm(box.lo[2] - wall.start[2]),
            "width": _mm(box.size[axis]),
            "height": _mm(box.size[2]),
            "element_ids": [j.element_id],
        })
    rows.sort(key=lambda r: r["offset"])
    for n, row in enumerate(rows, start=1):
        row["id"] = f"{wall.object_id}-O{n}"
    return [{"id": r.pop("id"), **r} for r in rows]


# --- entry point -----------------------------------------------------------

def build_object_inventory(snapshots: Sequence[ObjectSnapshot],
                           module_ids: Optional[Collection[str]] = None,
                           detail_all: bool = False,
                           element_detail: str = "none",
                           source: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Inventory of objects per module: summary for all, detail where asked.

    Args:
        snapshots: every scanned element; vertices filled where geometry_needed()
            asked for them.
        module_ids: modules to detail (any spelling: "M001" means "M1").
        detail_all: detail every module (used for the JSON file export).
        element_detail: "none", "envelope" or "vertices" for detailed modules.
        source: provenance block copied into the result.
    """
    if element_detail not in DETAIL_LEVELS:
        raise ValueError(f"element_detail must be one of {DETAIL_LEVELS}, got {element_detail!r}")
    requested = {parse_module_id(m) or m for m in (module_ids or [])}
    modules, joinery, unattached, processing = _partition(snapshots)
    warnings = [f"module {m} not found in the scanned elements"
                for m in sorted(requested - set(modules))]

    frames: Dict[str, ModuleFrame] = {}
    bottoms: Dict[str, Set[int]] = {}
    module_warnings: Dict[str, List[str]] = {m: [] for m in modules}
    for module_id, module in modules.items():
        floor = _bottom_floor(module)
        frame = frame_from_floor([v for e in floor for v in e.vertices]) if floor else None
        mw = module_warnings[module_id]
        if module.disagreements:
            mw.append(f"{module.disagreements} elements have a Module attribute that "
                      "disagrees with their subgroup; the subgroup was used")
        if frame is None:
            mw.append("no bottom floor found: no frame, no objects")
        elif frame.plan_area_ratio < cv.MIN_PLAN_AREA_RATIO:
            mw.append(f"bottom floor fills {frame.plan_area_ratio:.0%} of its enclosing "
                      "rectangle: not rectangular, objects omitted")
        else:
            frames[module_id] = frame
            bottoms[module_id] = {e.element_id for e in floor}

    detailed = {m for m in modules if detail_all or m in requested}
    walls: Dict[str, List[_Wall]] = {}
    for module_id, frame in frames.items():
        module = modules[module_id]
        for object_id, elements in module.parts.items():
            if module.part_refs[object_id].object_type == "wall":
                wall = _make_wall(object_id, elements, frame, module_id in detailed)
                if wall is not None:
                    walls.setdefault(module_id, []).append(wall)
    attached, orphans = _attach_openings(joinery, walls, frames)

    orphans_by_module: Dict[str, List[ObjectSnapshot]] = {}
    for j in orphans:
        home, _part, _d = element_module(j)
        if home is not None and home in frames and j.vertices:
            orphans_by_module.setdefault(home, []).append(j)
        else:
            unattached.append(j.element_id)

    entries = []
    for module_id in sorted(modules, key=module_number):
        module = modules[module_id]
        frame = frames.get(module_id)
        entry: Dict[str, Any] = {"module_id": module_id, "grouping_source": None,
                                 "frame": None, "counts": {}, "warnings": module_warnings[module_id]}
        if frame is not None:
            heights = [v[2] for els in module.parts.values() for e in els for v in e.vertices]
            heights += [v[2] for e in module.loose for v in e.vertices]
            entry["frame"] = _frame_dict(frame, max(heights) - frame.origin[2] if heights else None)
        objects = _module_objects(module, frame, walls.get(module_id, []), attached,
                                  orphans_by_module.get(module_id, []),
                                  bottoms.get(module_id, set()),
                                  module_id in detailed, element_detail)
        entry["grouping_source"] = objects["grouping_source"]
        entry["counts"] = objects["counts"]
        if module_id in detailed:
            entry["objects"] = objects["objects"] if frame is not None else []
        else:
            entry["unclassified_element_count"] = len(module.loose)
        entries.append(entry)

    return {
        "status": "ok",
        "schema": SCHEMA,
        "source": dict(source or {}),
        "modules": entries,
        "unattached_element_ids": sorted(unattached),
        "processing_element_count": processing,
        "warnings": warnings,
    }


def _module_objects(module: _Module, frame: Optional[ModuleFrame], walls: Sequence[_Wall],
                    attached: Dict[str, List[Tuple[ObjectSnapshot, LocalBox]]],
                    orphans: Sequence[ObjectSnapshot], bottom_ids: Set[int],
                    detailed: bool, element_detail: str) -> Dict[str, Any]:
    """Objects of one module (detail), with counts and grouping source."""
    counts: Counter = Counter()
    for object_id, ref in module.part_refs.items():
        counts[ref.object_type] += 1
    counts["opening"] = sum(len(attached.get(w.object_id, [])) for w in walls)
    counts["other"] += len(orphans)
    source: Optional[str] = ("subgroup" if module.parts
                             else "geometry" if module.loose else None)
    objects: List[Dict[str, Any]] = []
    if frame is None or not detailed:
        return {"objects": objects, "counts": dict(counts), "grouping_source": source}

    wall_by_id = {w.object_id: w for w in walls}
    for object_id in sorted(module.parts, key=_part_sort_key):
        elements = module.parts[object_id]
        ref = module.part_refs[object_id]
        record: Optional[Dict[str, Any]]
        if ref.object_type == "wall":
            wall = wall_by_id.get(object_id)
            record = None
            if wall is not None:
                wall.record["openings"] = _opening_records(wall, attached.get(object_id, []))
                record = wall.record
        elif ref.object_type == "slab":
            is_bottom = any(e.element_id in bottom_ids for e in elements)
            record = _make_box_object(object_id, "slab", elements, frame, ref.prefix,
                                      _slab_level(elements, is_bottom))
        else:
            record = _make_box_object(object_id, ref.object_type, elements, frame, ref.prefix)
        if record is None:
            continue
        if element_detail != "none":
            record["elements"] = _element_details(elements, frame, element_detail)
        objects.append(record)

    fallback = _fallback_groups(module.loose, frame)
    if fallback:
        source = "subgroup+geometry" if module.parts else "geometry"
    for n, (kind, label, elements) in enumerate(fallback, start=1):
        object_id = f"{module.module_id}-geo{n}"
        made: Optional[Dict[str, Any]]
        if kind == "wall":
            geo_wall = _make_wall(object_id, elements, frame, check_union=False)
            made = geo_wall.record if geo_wall else None
            if made is not None:
                made["warnings"].append(f"grouped by geometry ({label})")
        elif kind == "slab":
            made = _make_box_object(object_id, "slab", elements, frame, None, label)
        else:
            made = _make_box_object(object_id, "other", elements, frame, None)
        if made is None:
            continue
        if element_detail != "none":
            made["elements"] = _element_details(elements, frame, element_detail)
        objects.append(made)
        counts[kind] += 1

    for j in orphans:
        stray = _make_box_object(f"{module.module_id}-joinery{j.element_id}", "other",
                                 [j], frame, None)
        if stray is not None:
            stray["warnings"].append(f"joinery '{j.name.strip()}' lies in no wall")
            objects.append(stray)
    return {"objects": objects, "counts": dict(counts), "grouping_source": source}
```

- [ ] **Step 4: Run the tests**

Run: `.venv\Scripts\python -m unittest tests.test_object_inventory -v`
Expected: 41 tests, `OK`.

- [ ] **Step 5: Check types and the 3.10 floor**

Run: `.venv\Scripts\python -m mypy .`
Expected: `Found 13 errors in 4 files` (the baseline; none in `vestack/`).

- [ ] **Step 6: Commit**

```bash
git add vestack/object_inventory.py tests/object_fixtures.py tests/test_object_inventory.py
git commit -m "feat(vestack): build the object inventory from part subgroups and geometry"
```

---

### Task 4: Schema contract

Pins the output format with a golden file and documents it for the Revit side.

**Files:**
- Create: `tests/test_object_inventory_schema.py`
- Create: `tests/data/object_inventory_golden.json` (generated)
- Create: `vestack/OBJECT_INVENTORY.md`

**Interfaces:**
- Consumes: Task 3 (`build_object_inventory`, `module_m1`).
- Produces: the documented contract `vestack.object_inventory/1`.

- [ ] **Step 1: Write the test** — create `tests/test_object_inventory_schema.py`:

```python
"""Golden file pinning schema vestack.object_inventory/1.

The Revit side implements this format, so any change to it must be deliberate.
After an intended change, regenerate and review the diff:

    .venv\\Scripts\\python -m tests.test_object_inventory_schema --regenerate
"""
import json
import pathlib
import sys
import unittest
from typing import Any, Dict

from tests.object_fixtures import module_m1
from vestack.object_inventory import build_object_inventory

GOLDEN = pathlib.Path(__file__).parent / "data" / "object_inventory_golden.json"
SOURCE = {"file": "fixture.3d", "extracted_at": "2026-10-15T14:02:00+02:00"}


def current() -> Dict[str, Any]:
    inventory = build_object_inventory(module_m1(37, (500, 800, 0)), module_ids=["M1"],
                                       element_detail="envelope", source=SOURCE)
    round_tripped: Dict[str, Any] = json.loads(json.dumps(inventory))
    return round_tripped


class Golden(unittest.TestCase):
    def test_the_output_matches_the_golden_file(self) -> None:
        self.assertEqual(current(), json.loads(GOLDEN.read_text(encoding="utf-8")))


if __name__ == "__main__":
    if "--regenerate" in sys.argv:
        GOLDEN.parent.mkdir(exist_ok=True)
        GOLDEN.write_text(json.dumps(current(), ensure_ascii=False, indent=1) + "\n",
                          encoding="utf-8")
        print(f"wrote {GOLDEN}")
    else:
        unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_object_inventory_schema -v`
Expected: ERROR, `FileNotFoundError` on `tests\data\object_inventory_golden.json`.

- [ ] **Step 3: Generate the golden file and review it**

Run: `.venv\Scripts\python -m tests.test_object_inventory_schema --regenerate`
Expected: `wrote ...tests\data\object_inventory_golden.json` (about 300 lines). Open it and check, before committing: `schema` is `vestack.object_inventory/1`; module `M1` has `frame.length` 6000, `width` 2500, `height` 3400, `origin_model` `[500, 800, 0]`, `x_axis_model` `[0.798636, 0.601815, 0.0]`; object `M1-W1` has `start` `[0, 106, 220]`, `end` `[6000, 106, 220]`, `thickness` 212, `wall_type` `MOB200`, one opening with `offset` 1000, `sill` 90, `width` 1455, `height` 2315; every object carries `elements` with `material`.

- [ ] **Step 4: Write the contract** — create `vestack/OBJECT_INVENTORY.md`:

```markdown
# Object inventory schema: `vestack.object_inventory/1`

What `get_object_inventory` returns, and what the file written with
`output_path` contains. It is the contract between the Cadwork side
(this repository) and the Revit side, which must produce the same structure
from the Revit model so that Claude can compare the two.

Design: `docs/superpowers/specs/2026-10-15-object-inventory-design.md`.
Reference output: `tests/data/object_inventory_golden.json`.

## Units and frames

- Lengths in **millimetres**, rounded to 1 mm (integers).
- Every coordinate is in the **module frame** unless its key ends in `_model`.
- Module frame: origin at a corner of the module's bottom floor, at its
  underside; **X** along the longer side of the minimum-area rectangle enclosing
  the bottom floor in plan; **Z** up; **Y** = Z × X (right-handed).
- Of the two frames that satisfy this (180° apart), keep the one whose X axis
  makes less than 90° with the model's +X; when both make exactly 90°, keep
  X = +Y. The Revit side applies the same rule in its own model axes.
- A model point `P` has module coordinates
  `((P - origin_model) · x_axis_model, (P - origin_model) · y_axis_model, (P - origin_model) · z_axis_model)`.

## Top level

| Key | Meaning |
|---|---|
| `status` | `"ok"`, or `"error"` with a `message` |
| `schema` | `"vestack.object_inventory/1"`; bumped on any incompatible change |
| `source` | `file` (path of the model), `extracted_at` (ISO 8601) |
| `modules` | one entry per module, sorted by module number |
| `unattached_element_ids` | elements with no module and no wall to sit in |
| `processing_element_count` | processing elements (group `Usinage`), never in an object |
| `warnings` | e.g. a requested module that was not found |
| `scanned_element_count`, `geometry_read_count`, `skipped_element_ids`, `attribute_numbers` | Cadwork side only: scan statistics |

## Module entry

| Key | Meaning |
|---|---|
| `module_id` | canonical id: `M` + number without leading zeros (`M001` → `M1`) |
| `grouping_source` | `"subgroup"`, `"geometry"`, `"subgroup+geometry"`, or `null` |
| `frame` | `origin_model`, `x_axis_model`, `y_axis_model`, `z_axis_model`, `length`, `width`, `height`; `null` without a usable bottom floor |
| `counts` | objects per type: `wall`, `slab`, `roof`, `parapet`, `other`, `opening` |
| `warnings` | module-level problems; never dropped silently |
| `objects` | detailed modules only |
| `unclassified_element_count` | summarised modules only: elements left to the geometric fallback |

## Objects

Every object has `id`, `type`, `element_ids` and `warnings`. `id` is the part
subgroup (`M1-W5`) when the object comes from one, `M1-geo<n>` when grouped by
geometry, `M1-joinery<element id>` for joinery lying in no wall.

**wall**

| Key | Meaning |
|---|---|
| `start`, `end` | wall axis at its foot, at mid-thickness; `start` is the end with the smaller coordinate along the wall |
| `thickness`, `height` | of the wall body |
| `side` | footprint edge it stands on: `-x`, `+x`, `-y`, `+y`, or `null` for an interior wall |
| `wall_type`, `stud_section` | from the `MOB<section>` body element (`"MOB200"`, `200`); `null` without one |
| `openings` | see below |

**opening** (inside a wall's `openings`)

| Key | Meaning |
|---|---|
| `id` | `<wall id>-O<n>`, numbered by increasing `offset` |
| `name` | joinery name, e.g. `"MEX type B"` |
| `offset` | from the wall's `start`, along the wall, to the opening's near edge |
| `sill` | from the wall's foot to the bottom of the opening |
| `width`, `height` | of the joinery box |

**slab**: `level` (`"bottom"`, `"top"` or `null`), `origin` (min corner),
`length` (along X), `width` (along Y), `thickness`.

**roof**, **parapet**, **other**: `part` (the subgroup prefix, e.g. `"TF"`,
`"Poteaux"`, or `null`), `origin` (min corner), `size` (`[x, y, z]`).

## Element detail

With `element_detail="envelope"` or `"vertices"`, each object of a detailed
module carries `elements`: `element_id`, `name`, `material`, `origin`, `size`
(the element's box in the module frame), plus `vertices` (module frame) for
`"vertices"`. The element type is omitted until its Cadwork 2026 API is
confirmed.
```

- [ ] **Step 5: Run the test**

Run: `.venv\Scripts\python -m unittest tests.test_object_inventory_schema -v`
Expected: 1 test, `OK`.

- [ ] **Step 6: Commit**

```bash
git add tests/test_object_inventory_schema.py tests/data/object_inventory_golden.json vestack/OBJECT_INVENTORY.md
git commit -m "docs(vestack): pin and document the object inventory schema"
```

---

### Task 5: Bridge adapter

Reads the model in two passes (attributes for every element, vertices only where `geometry_needed` says) and exposes the operation `get_object_inventory`. The dispatcher discovers it by name; no registration to edit.

**Files:**
- Modify: `vestack/bridge_handler.py` (docstring, imports, `ATTRIBUTE_ROLES`, new functions at the end)
- Test: `tests/test_vestack_object_bridge.py`

**Interfaces:**
- Consumes: Task 3 (`ObjectSnapshot`, `geometry_needed`, `build_object_inventory`); existing `_safe_str`, `_coordinates`, `_element_ids_to_scan`, `resolve_attribute_numbers`.
- Produces: `read_object_attributes(element_ids, attribute_numbers) -> List[ObjectSnapshot]`; `read_object_geometry(snapshots, needed, with_material) -> List[int]`; `handle_get_object_inventory(args) -> Dict[str, Any]` taking `element_ids`, `active_only`, `module_ids`, `detail_all`, `element_detail`; `ATTRIBUTE_ROLES["complex"]`.
- Cadwork calls used, all verified live on Cadwork 2026 (15/10/2026): `ac.get_name`, `ac.get_group`, `ac.get_subgroup`, `ac.get_user_attribute`, `ac.get_user_attribute_name`, `ac.get_element_material_name`, `gc.get_element_vertices`, `ec.get_all_identifiable_element_ids`, `ec.get_active_identifiable_element_ids`, `uc.get_3d_file_path`.

- [ ] **Step 1: Write the failing test** — create `tests/test_vestack_object_bridge.py`:

```python
"""Tests for the object inventory's bridge adapter, with Cadwork faked.

As in test_vestack_bridge_handler, the Cadwork API modules are replaced in
sys.modules; the adapter imports them per call, by their bare names.
"""
import sys
import types
import unittest
from typing import Any, Dict, List, Optional, Set
from unittest.mock import patch

from tests.object_fixtures import module_m1
from vestack.bridge_handler import handle_get_object_inventory
from vestack.object_inventory import ObjectSnapshot

# The spike model's attributes: 1 Batiment, 2 Niveau, 3 Module, 5 Complexe.
ATTRIBUTE_NAMES = {1: "Bâtiment (Alt+F1)", 2: "Niveau (Alt+F2)", 3: "Module (Alt+F3)",
                   5: "Complexe (Alt+F5)"}


def fake_cadwork(snapshots: List[ObjectSnapshot], *, fail_vertices: Optional[int] = None,
                 vertex_calls: Optional[Set[int]] = None) -> Dict[str, types.ModuleType]:
    by_id = {s.element_id: s for s in snapshots}

    def module(**functions: Any) -> types.ModuleType:
        fake = types.ModuleType("fake")
        for name, function in functions.items():
            setattr(fake, name, function)
        return fake

    def get_element_vertices(element_id: int) -> List[List[float]]:
        if vertex_calls is not None:
            vertex_calls.add(element_id)
        if element_id == fail_vertices:
            raise RuntimeError("no geometry")
        return [list(v) for v in by_id[element_id].vertices]

    def get_user_attribute(element_id: int, number: int) -> str:
        s = by_id[element_id]
        return {3: s.module_attribute, 5: s.complex_code}.get(number, "")

    return {
        "element_controller": module(
            get_all_identifiable_element_ids=lambda: sorted(by_id),
            get_active_identifiable_element_ids=lambda: sorted(by_id)[:2]),
        "geometry_controller": module(get_element_vertices=get_element_vertices),
        "attribute_controller": module(
            get_user_attribute_name=lambda n: ATTRIBUTE_NAMES.get(n, ""),
            get_user_attribute=get_user_attribute,
            get_name=lambda eid: by_id[eid].name,
            get_group=lambda eid: by_id[eid].group,
            get_subgroup=lambda eid: by_id[eid].subgroup,
            get_element_material_name=lambda eid: by_id[eid].material),
        "utility_controller": module(get_3d_file_path=lambda: "C:/models/copy.3d"),
    }


def run(args: Dict[str, Any], **fake: Any) -> Dict[str, Any]:
    with patch.dict(sys.modules, fake_cadwork(module_m1(37, (500, 800, 0)), **fake)):
        return handle_get_object_inventory(args)


class HandleGetObjectInventory(unittest.TestCase):
    def test_reads_the_model_into_an_inventory(self) -> None:
        response = run({"module_ids": ["M1"]})
        self.assertEqual(response["status"], "ok")
        walls = {o["id"]: o for o in response["modules"][0]["objects"]}
        self.assertEqual(walls["M1-W1"]["openings"][0]["width"], 1455)

    def test_the_complexe_attribute_is_found_by_name(self) -> None:
        self.assertEqual(run({})["attribute_numbers"]["complex"], 5)

    def test_the_summary_reads_only_the_geometry_it_needs(self) -> None:
        calls: Set[int] = set()
        response = run({}, vertex_calls=calls)
        self.assertEqual(calls, {1, 2, 10, 20, 50})
        self.assertEqual(response["geometry_read_count"], 5)

    def test_material_is_read_with_element_detail(self) -> None:
        response = run({"module_ids": ["M1"], "element_detail": "envelope"})
        floor = next(o for o in response["modules"][0]["objects"] if o["id"] == "M1-F1")
        self.assertEqual(floor["elements"][0]["material"], "OSB-9")

    def test_unreadable_geometry_is_reported(self) -> None:
        self.assertEqual(run({"module_ids": ["M1"]}, fail_vertices=12)["skipped_element_ids"], [12])

    def test_the_source_names_the_open_file(self) -> None:
        source = run({})["source"]
        self.assertEqual(source["file"], "C:/models/copy.3d")
        self.assertIn("T", source["extracted_at"])

    def test_an_invalid_detail_level_is_an_error(self) -> None:
        response = run({"element_detail": "all"})
        self.assertEqual(response["status"], "error")
        self.assertIn("element_detail", response["message"])

    def test_a_cadwork_failure_becomes_an_error_response(self) -> None:
        broken = fake_cadwork(module_m1())
        broken["element_controller"] = types.ModuleType("fake")
        with patch.dict(sys.modules, broken):
            response = handle_get_object_inventory({})
        self.assertEqual(response["status"], "error")

    def test_the_dispatcher_discovers_the_operation(self) -> None:
        from bridge.dispatcher import CommandDispatcher
        self.assertIn("get_object_inventory", CommandDispatcher().operations)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_vestack_object_bridge -v`
Expected: ERROR, `cannot import name 'handle_get_object_inventory'`.

- [ ] **Step 3: Extend `vestack/bridge_handler.py`:**

```diff
--- a/vestack/bridge_handler.py
+++ b/vestack/bridge_handler.py
@@ -1,25 +1,29 @@
-"""Bridge adapter for the Vestack module inventory.
+"""Bridge adapter for the Vestack module and object inventories.
 
 The only Vestack code that talks to Cadwork. It reads what the model holds, turns
-it into ElementSnapshot values, and hands them to the pure logic in
-module_inventory.py. Cadwork modules are imported inside the functions, by their
+it into ElementSnapshot or ObjectSnapshot values, and hands them to the pure
+logic in module_inventory.py and object_inventory.py. Cadwork modules are imported inside the functions, by their
 bare names, as every other bridge handler does: at module level they would make
 this file unimportable outside Cadwork.
 
-The dispatcher discovers `handle_get_module_inventory` through the usual
-`handle_<operation>` convention, via bridge.dispatcher.EXTENSION_MODULES.
+The dispatcher discovers `handle_get_module_inventory` and
+`handle_get_object_inventory` through the usual `handle_<operation>` convention,
+via bridge.dispatcher.EXTENSION_MODULES.
 """
 import unicodedata
-from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
+from datetime import datetime
+from typing import Any, Callable, Collection, Dict, List, Optional, Sequence, Tuple
 
 from . import conventions as cv
 from .module_inventory import BBox, ElementSnapshot, build_inventory
+from .object_inventory import ObjectSnapshot, build_object_inventory, geometry_needed
 
 # Which Cadwork user attribute plays which role, matched on the attribute name.
 ATTRIBUTE_ROLES: Dict[str, Tuple[str, ...]] = {
     "module": cv.MODULE_ATTRIBUTE_NAMES,
     "building": cv.BUILDING_ATTRIBUTE_NAMES,
     "level": cv.LEVEL_ATTRIBUTE_NAMES,
+    "complex": cv.COMPLEX_ATTRIBUTE_NAMES,
 }
 
 
@@ -181,3 +185,111 @@
             "status": "error",
             "message": f"get_module_inventory failed: {type(exc).__name__}: {exc}",
         }
+
+
+# --- object inventory ------------------------------------------------------
+
+def read_object_attributes(element_ids: Sequence[int],
+                           attribute_numbers: Dict[str, int]) -> List[ObjectSnapshot]:
+    """First pass: names, groups, subgroups, Module and Complexe, no geometry.
+
+    Cheap compared with vertices (about 1 ms per element on Cadwork 2026), so it
+    runs over every scanned element to find the modules and their parts.
+    """
+    import attribute_controller as ac
+
+    module_number = attribute_numbers.get("module")
+    complex_number = attribute_numbers.get("complex")
+
+    def user_attribute(number: Optional[int], element_id: int) -> str:
+        if number is None:
+            return ""
+        return _safe_str(lambda eid: ac.get_user_attribute(eid, number), element_id)
+
+    return [ObjectSnapshot(element_id=element_id,
+                           name=_safe_str(ac.get_name, element_id),
+                           group=_safe_str(ac.get_group, element_id),
+                           subgroup=_safe_str(ac.get_subgroup, element_id),
+                           module_attribute=user_attribute(module_number, element_id),
+                           complex_code=user_attribute(complex_number, element_id))
+            for element_id in element_ids]
+
+
+def read_object_geometry(snapshots: Sequence[ObjectSnapshot], needed: Collection[int],
+                         with_material: bool) -> List[int]:
+    """Second pass: vertices (and material) of the elements that need them.
+
+    Fills the snapshots in place. Returns the ids whose geometry could not be read.
+    """
+    import attribute_controller as ac
+    import geometry_controller as gc
+
+    skipped: List[int] = []
+    for snapshot in snapshots:
+        if snapshot.element_id not in needed:
+            continue
+        try:
+            vertices = tuple(_coordinates(v) for v in
+                             (gc.get_element_vertices(snapshot.element_id) or []))
+        except Exception:
+            vertices = ()
+        if not vertices:
+            skipped.append(snapshot.element_id)
+            continue
+        snapshot.vertices = vertices
+        if with_material:
+            snapshot.material = _safe_str(ac.get_element_material_name, snapshot.element_id)
+    return skipped
+
+
+def _source() -> Dict[str, Any]:
+    """Provenance of the inventory: the open file and the extraction time."""
+    try:
+        import utility_controller as uc
+        path = str(uc.get_3d_file_path() or "")
+    except Exception:
+        path = ""
+    return {"file": path,
+            "extracted_at": datetime.now().astimezone().isoformat(timespec="seconds")}
+
+
+def handle_get_object_inventory(args: Dict[str, Any]) -> Dict[str, Any]:
+    """Walls, slabs, roofs and openings per module, in each module's own frame.
+
+    Args (all optional):
+        element_ids / active_only: restrict the scan, as for get_module_inventory.
+        module_ids: modules to detail; the others are summarised.
+        detail_all: detail every module (the controller sets it for file export).
+        element_detail: "none", "envelope" or "vertices", for detailed modules.
+
+    Attributes are read for every scanned element, vertices only where the
+    inventory needs them (see object_inventory.geometry_needed).
+    """
+    try:
+        element_ids = _element_ids_to_scan(args)
+        module_ids = [str(m) for m in (args.get("module_ids") or [])]
+        detail_all = bool(args.get("detail_all"))
+        element_detail = str(args.get("element_detail") or "none")
+
+        attribute_numbers = resolve_attribute_numbers()
+        snapshots = read_object_attributes(element_ids, attribute_numbers)
+        needed = geometry_needed(snapshots, module_ids, detail_all)
+        skipped = read_object_geometry(snapshots, needed,
+                                       with_material=element_detail != "none")
+
+        inventory = build_object_inventory(snapshots, module_ids, detail_all,
+                                           element_detail, _source())
+        inventory.update({
+            "scanned_element_count": len(snapshots),
+            "geometry_read_count": len(needed) - len(skipped),
+            "skipped_element_ids": sorted(skipped),
+            "attribute_numbers": attribute_numbers,
+        })
+        return inventory
+    except ValueError as exc:
+        return {"status": "error", "message": f"get_object_inventory: {exc}"}
+    except Exception as exc:
+        return {
+            "status": "error",
+            "message": f"get_object_inventory failed: {type(exc).__name__}: {exc}",
+        }
```

- [ ] **Step 4: Run the tests**

Run: `.venv\Scripts\python -m unittest discover -s tests -t .`
Expected: all pass, including the existing `test_vestack_bridge_handler` (the extra `complex` role does not change the module inventory).

- [ ] **Step 5: Commit**

```bash
git add vestack/bridge_handler.py tests/test_vestack_object_bridge.py
git commit -m "feat(vestack): read the model for the object inventory in two passes"
```

---

### Task 6: Per-call socket timeout

A model-wide attribute read takes about 48 s, beyond the fixed 30 s socket timeout, so calls need their own timeout. The timeout message also says what the spike found: Cadwork stalls the bridge during an active command until Escape.

**Files:**
- Modify: `core/connection.py` (`CadworkConnection.send_command`)
- Modify: `controllers/base_controller.py` (`BaseController.send_command`)
- Test: `tests/test_connection_timeout.py`

**Interfaces:**
- Produces: `CadworkConnection.send_command(operation, args=None, timeout: Optional[float] = None)`; `BaseController.send_command(operation, args=None, timeout: Optional[float] = None)`. Omitting `timeout` keeps `SOCKET_TIMEOUT` (30 s): no other caller changes.

- [ ] **Step 1: Write the failing test** — create `tests/test_connection_timeout.py`:

```python
"""Per-call timeout on the bridge socket, against a bridge that never answers.

That is what Cadwork 2026 does while a Cadwork command is active: it accepts the
connection, then stays silent until the modeller presses Escape.
"""
import socket
import threading
import time
import unittest
from typing import List
from unittest.mock import patch

from controllers.base_controller import BaseController
from core.connection import CadworkConnection


class SilentBridge:
    """Accepts connections on an ephemeral port and never replies."""

    def __init__(self) -> None:
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("127.0.0.1", 0))
        self.server.listen(5)
        self.port = self.server.getsockname()[1]
        self.held: List[socket.socket] = []
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self) -> None:
        while True:
            try:
                conn, _ = self.server.accept()
            except OSError:
                return
            self.held.append(conn)

    def close(self) -> None:
        for conn in self.held:
            conn.close()
        self.server.close()


class PerCallTimeout(unittest.TestCase):
    def setUp(self) -> None:
        self.bridge = SilentBridge()
        self.addCleanup(self.bridge.close)

    def test_the_connection_honours_a_per_call_timeout(self) -> None:
        connection = CadworkConnection("127.0.0.1", self.bridge.port)
        started = time.monotonic()
        with self.assertRaises(TimeoutError):
            connection.send_command("ping", {}, timeout=0.3)
        self.assertLess(time.monotonic() - started, 5.0)

    def test_the_controller_passes_the_timeout_and_suggests_escape(self) -> None:
        connection = CadworkConnection("127.0.0.1", self.bridge.port)
        with patch("controllers.base_controller.get_connection", return_value=connection):
            response = BaseController("Test").send_command("ping", {}, timeout=0.3)
        self.assertEqual(response["status"], "error")
        self.assertIn("press Escape", response["message"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv\Scripts\python -m unittest tests.test_connection_timeout -v`
Expected: ERROR, `send_command() got an unexpected keyword argument 'timeout'`.

- [ ] **Step 3: Add the parameter:**

```diff
--- a/core/connection.py
+++ b/core/connection.py
@@ -17,8 +17,12 @@
         self.host = host
         self.port = port
     
-    def send_command(self, operation: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
-        """Send command to Cadwork and return response"""
+    def send_command(self, operation: str, args: Optional[Dict[str, Any]] = None,
+                     timeout: Optional[float] = None) -> Dict[str, Any]:
+        """Send command to Cadwork and return response.
+
+        timeout: seconds to wait for the bridge, SOCKET_TIMEOUT when omitted.
+        """
         command = {
             "operation": operation,
             "args": args or {}
@@ -30,7 +34,7 @@
         try:
             # Create and configure socket
             sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
-            sock.settimeout(SOCKET_TIMEOUT)
+            sock.settimeout(timeout or SOCKET_TIMEOUT)
             sock.connect((self.host, self.port))
             
             # Send command
```

```diff
--- a/controllers/base_controller.py
+++ b/controllers/base_controller.py
@@ -11,11 +11,12 @@
     def __init__(self, controller_name: str):
         self.controller_name = controller_name
     
-    def send_command(self, operation: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
+    def send_command(self, operation: str, args: Optional[Dict[str, Any]] = None,
+                     timeout: Optional[float] = None) -> Dict[str, Any]:
         """Send command to Cadwork and handle common error cases"""
         try:
             connection = get_connection()
-            response = connection.send_command(operation, args or {})
+            response = connection.send_command(operation, args or {}, timeout=timeout)
             
             if response.get("status") == "ok":
                 log_info(f"{self.controller_name}: {operation} completed successfully")
@@ -29,7 +30,11 @@
             return {"status": "error", "message": f"Connection failed: {e}"}
         except TimeoutError as e:
             log_error(f"{self.controller_name}: Timeout error - {e}")
-            return {"status": "error", "message": f"Operation timed out: {e}"}
+            # Observed on Cadwork 2026: the bridge does not answer while a
+            # Cadwork command is active, until the modeller presses Escape.
+            return {"status": "error", "message": (
+                f"Operation timed out: {e}. If Cadwork is in an active command, "
+                "press Escape in Cadwork, then retry.")}
         except Exception as e:
             log_error(f"{self.controller_name}: Unexpected error - {e}")
             return {"status": "error", "message": f"Unexpected error: {e}"}
```

- [ ] **Step 4: Run the tests**

Run: `.venv\Scripts\python -m unittest discover -s tests -t .`
Expected: all pass; `test_connection_timeout` takes under 1 s.

- [ ] **Step 5: Commit**

```bash
git add core/connection.py controllers/base_controller.py tests/test_connection_timeout.py
git commit -m "feat(core): per-call socket timeout, and point timeouts at Escape"
```

---

### Task 7: MCP controller, file export and tool

**Files:**
- Modify: `vestack/mcp_controller.py`
- Modify: `main.py` (new tool after `get_module_inventory`)
- Modify: `tests/test_server.py` (tool registration)
- Test: `tests/test_vestack_controller.py`

**Interfaces:**
- Consumes: Task 6 (`send_command(..., timeout=...)`), Task 1 (`parse_module_id`), the bridge operation from Task 5.
- Produces: `OBJECT_INVENTORY_TIMEOUT_S = 900.0`; `write_inventory_file(inventory, output_path) -> str` (atomic, raises `OSError`); `summarise(inventory, keep) -> Dict`; `VestackController.get_object_inventory(element_ids=None, active_only=False, module_ids=None, element_detail="none", output_path=None)`; MCP tool `get_object_inventory` with the same parameters.

- [ ] **Step 1: Write the failing tests** — create `tests/test_vestack_controller.py`:

```python
"""Tests for the MCP-side object inventory: arguments, timeout, file export.

The socket is replaced by a stub of BaseController.send_command, fed with a real
inventory built from the fixture module.
"""
import asyncio
import json
import os
import tempfile
import unittest
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

from tests.object_fixtures import module_m1
from vestack.mcp_controller import OBJECT_INVENTORY_TIMEOUT_S, VestackController
from vestack.object_inventory import build_object_inventory

Call = Tuple[str, Dict[str, Any], Optional[float]]


def run(calls: List[Call], **kwargs: Any) -> Dict[str, Any]:
    def fake_send(self: Any, operation: str, args: Optional[Dict[str, Any]] = None,
                  timeout: Optional[float] = None) -> Dict[str, Any]:
        args = args or {}
        calls.append((operation, args, timeout))
        return build_object_inventory(module_m1(), module_ids=args.get("module_ids"),
                                      detail_all=bool(args.get("detail_all")),
                                      element_detail=args.get("element_detail", "none"))

    with patch.object(VestackController, "send_command", fake_send):
        return asyncio.run(VestackController().get_object_inventory(**kwargs))


class Arguments(unittest.TestCase):
    def test_sends_the_operation_with_a_long_timeout(self) -> None:
        calls: List[Call] = []
        run(calls, module_ids=["M1"])
        operation, args, timeout = calls[0]
        self.assertEqual(operation, "get_object_inventory")
        self.assertEqual(args, {"element_detail": "none", "module_ids": ["M1"]})
        self.assertEqual(timeout, OBJECT_INVENTORY_TIMEOUT_S)

    def test_an_invalid_detail_level_is_refused_before_sending(self) -> None:
        calls: List[Call] = []
        response = run(calls, element_detail="all")
        self.assertEqual(response["status"], "error")
        self.assertEqual(calls, [])

    def test_without_output_path_nothing_is_written_and_detail_all_is_not_asked(self) -> None:
        calls: List[Call] = []
        response = run(calls)
        self.assertNotIn("detail_all", calls[0][1])
        self.assertNotIn("output_path", response)


class FileExport(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.mkdtemp()
        self.path = os.path.join(self.directory, "inventory.json")

    def test_the_file_holds_every_module_in_detail(self) -> None:
        calls: List[Call] = []
        response = run(calls, output_path=self.path)
        self.assertTrue(calls[0][1]["detail_all"])
        with open(self.path, encoding="utf-8") as stream:
            written = json.load(stream)
        self.assertIn("objects", written["modules"][0])
        self.assertEqual(response["output_path"], os.path.abspath(self.path))

    def test_the_response_stays_a_summary_unless_modules_are_named(self) -> None:
        self.assertNotIn("objects", run([], output_path=self.path)["modules"][0])
        self.assertIn("objects", run([], output_path=self.path, module_ids=["M001"])["modules"][0])

    def test_an_unwritable_path_is_an_error_and_leaves_no_file(self) -> None:
        missing = os.path.join(self.directory, "no-such-dir", "inventory.json")
        response = run([], output_path=missing)
        self.assertEqual(response["status"], "error")
        self.assertFalse(os.path.exists(missing))
        self.assertEqual(os.listdir(self.directory), [])


if __name__ == "__main__":
    unittest.main()
```

and add the registration test:

```diff
--- a/tests/test_server.py
+++ b/tests/test_server.py
@@ -46,6 +46,11 @@
         names = {tool.name for tool in asyncio.run(main.mcp.list_tools())}
         self.assertIn("get_module_inventory", names)
 
+    def test_the_object_inventory_tool_is_registered(self) -> None:
+        import main
+        names = {tool.name for tool in asyncio.run(main.mcp.list_tools())}
+        self.assertIn("get_object_inventory", names)
+
     def test_every_tool_has_a_description(self) -> None:
         import main
         undescribed = [t.name for t in asyncio.run(main.mcp.list_tools())
```

- [ ] **Step 2: Run them to verify they fail**

Run: `.venv\Scripts\python -m unittest tests.test_vestack_controller tests.test_server -v`
Expected: ERROR, `cannot import name 'OBJECT_INVENTORY_TIMEOUT_S'`; `test_the_object_inventory_tool_is_registered` FAIL.

- [ ] **Step 3: Extend the controller:**

```diff
--- a/vestack/mcp_controller.py
+++ b/vestack/mcp_controller.py
@@ -4,9 +4,50 @@
 one command over the socket to the bridge. The dependency runs one way only —
 Vestack builds on the generic core, the core knows nothing about Vestack.
 """
-from typing import Any, Dict, List, Optional
+import json
+import os
+import tempfile
+from typing import Any, Collection, Dict, List, Optional
 
 from controllers.base_controller import BaseController
+from vestack.naming import parse_module_id
+
+# Reading attributes alone takes about 48 s on a 50 940-element model under
+# Cadwork 2026, beyond the default socket timeout; a full export takes minutes.
+OBJECT_INVENTORY_TIMEOUT_S: float = 900.0
+
+ELEMENT_DETAIL_LEVELS = ("none", "envelope", "vertices")
+
+
+def write_inventory_file(inventory: Dict[str, Any], output_path: str) -> str:
+    """Write the inventory as JSON, atomically: no partial file on failure.
+
+    Returns the absolute path written. Raises OSError when it cannot be written.
+    """
+    target = os.path.abspath(output_path)
+    directory = os.path.dirname(target)
+    handle, temporary = tempfile.mkstemp(prefix=".object_inventory_", suffix=".json",
+                                         dir=directory)
+    try:
+        with os.fdopen(handle, "w", encoding="utf-8") as stream:
+            json.dump(inventory, stream, ensure_ascii=False, indent=1)
+        os.replace(temporary, target)
+    except BaseException:
+        if os.path.exists(temporary):
+            os.remove(temporary)
+        raise
+    return target
+
+
+def summarise(inventory: Dict[str, Any], keep: Collection[str]) -> Dict[str, Any]:
+    """Copy of a fully detailed inventory keeping objects only for `keep` modules."""
+    modules = []
+    for entry in inventory.get("modules", []):
+        if entry["module_id"] in keep:
+            modules.append(entry)
+        else:
+            modules.append({k: v for k, v in entry.items() if k != "objects"})
+    return {**inventory, "modules": modules}
 
 
 class VestackController(BaseController):
@@ -30,3 +71,38 @@
             args["id_source"] = id_source
 
         return self.send_command("get_module_inventory", args)
+
+    async def get_object_inventory(self,
+                                   element_ids: Optional[List[int]] = None,
+                                   active_only: bool = False,
+                                   module_ids: Optional[List[str]] = None,
+                                   element_detail: str = "none",
+                                   output_path: Optional[str] = None) -> Dict[str, Any]:
+        """Objects per module in module frames; optionally the full JSON export."""
+        if element_detail not in ELEMENT_DETAIL_LEVELS:
+            return {"status": "error",
+                    "message": f"element_detail must be one of {ELEMENT_DETAIL_LEVELS}"}
+
+        args: Dict[str, Any] = {"element_detail": element_detail}
+        if element_ids:
+            args["element_ids"] = [self.validate_element_id(e) for e in element_ids]
+        if active_only:
+            args["active_only"] = True
+        if module_ids:
+            args["module_ids"] = [str(m) for m in module_ids]
+        if output_path:
+            args["detail_all"] = True
+
+        response = self.send_command("get_object_inventory", args,
+                                     timeout=OBJECT_INVENTORY_TIMEOUT_S)
+        if response.get("status") != "ok" or not output_path:
+            return response
+
+        try:
+            written = write_inventory_file(response, output_path)
+        except OSError as exc:
+            return {"status": "error",
+                    "message": f"could not write the inventory to {output_path}: {exc}"}
+
+        keep = {parse_module_id(m) or m for m in (module_ids or [])}
+        return {**summarise(response, keep), "output_path": written}
```

- [ ] **Step 4: Declare the tool in `main.py`:**

```diff
--- a/main.py
+++ b/main.py
@@ -1470,6 +1470,33 @@
                                active_only: bool = False,
                                id_source: Optional[str] = None) -> Dict[str, Any]:
     return await vestack_ctrl.get_module_inventory(element_ids, active_only, id_source)
+
+
+@mcp.tool(
+    name="get_object_inventory",
+    description=(
+        "Lists the objects of each Vestack module - walls, slabs, roofs, parapets, "
+        "openings - with their envelopes in MILLIMETRES, in a frame local to each "
+        "module (origin at a bottom-floor corner, X along its longer side, Z up), "
+        "for comparison with the Revit model. Walls come from part subgroups "
+        "(M1-W5 = module 1, wall 5) and their MOB<section> body element; openings "
+        "are MEX joinery attached to the wall containing them. Without module_ids "
+        "it returns a summary per module (frame, counts, warnings); pass "
+        "module_ids=['M1'] for that module's objects, and element_detail="
+        "'envelope' or 'vertices' to also get each element in the module frame. "
+        "output_path writes the full inventory (every module, every object) as "
+        "JSON and still returns the summary. Reads attributes of the whole model "
+        "(about 1 min on a large building) and vertices only where needed. "
+        "Schema: vestack/OBJECT_INVENTORY.md."
+    )
+)
+async def get_object_inventory(element_ids: Optional[List[int]] = None,
+                               active_only: bool = False,
+                               module_ids: Optional[List[str]] = None,
+                               element_detail: str = "none",
+                               output_path: Optional[str] = None) -> Dict[str, Any]:
+    return await vestack_ctrl.get_object_inventory(element_ids, active_only, module_ids,
+                                                   element_detail, output_path)
 
 
 if __name__ == "__main__":
```

- [ ] **Step 5: Run everything**

Run: `.venv\Scripts\python -m unittest discover -s tests -t .`
Expected: `Ran 168 tests`, `OK`.
Run: `.venv\Scripts\python -m mypy .`
Expected: `Found 13 errors in 4 files`.

- [ ] **Step 6: Commit**

```bash
git add vestack/mcp_controller.py main.py tests/test_vestack_controller.py tests/test_server.py
git commit -m "feat(vestack): expose get_object_inventory with an optional JSON export"
```

---

### Task 8: Documentation

**Files:**
- Modify: `vestack/README.md`
- Modify: `.claude/skills/cadwork-model/SKILL.md`
- Modify: `.claude/skills/cadwork-model/tool-inventory.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: `vestack/README.md`** — in "What a module is", replace the sentence stating the id is "the letter `M` and three digits" with:

```markdown
Each module carries an id of the form `M1`, `M17` or `M139`: the letter `M`
and 1 to 4 digits. Leading zeros are dropped, so `M001` is `M1`.
```

Then add, before "## Known limitations":

```markdown
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

| File | Role | Imports Cadwork |
|---|---|---|
| `naming.py` | module ids, part subgroups, wall bodies, joinery | no |
| `frame.py` | module frame from the bottom floor | no |
| `object_inventory.py` | the logic: modules, objects, openings, fallback | no |
| `OBJECT_INVENTORY.md` | the output schema, for the Revit side | - |
```

- [ ] **Step 2: `.claude/skills/cadwork-model/SKILL.md`** — in "Lane 1 — read the model", after item 2 (Modules), insert:

```markdown
3. **Objects, to compare with Revit:** `get_object_inventory` without
   `module_ids` first: one summary per module (frame, counts, warnings), about a
   minute on a large building. Then `module_ids=["M1"]` for the walls, slabs and
   openings of the modules worth checking. Drill down only as far as needed:
   `element_detail="envelope"` (each element in the module frame), then the raw
   tools (`get_element_info`, `get_element_vertices`) on an object's
   `element_ids`, then ask the modeller to select them in Cadwork. Report the
   module warnings and any `unattached_element_ids`; never drop them.
```

and renumber the following items (Counts becomes 4, One element becomes 5).

- [ ] **Step 3: `.claude/skills/cadwork-model/tool-inventory.md`** — under "## Vestack (domain extension)", add `- \`get_object_inventory\`` after `- \`get_module_inventory\``, and change the header counts to `**168 tools declared**, **141 handlers**: 138 tools reach a handler, 4 are computed in the MCP server without Cadwork, **26 are not implemented**.`

- [ ] **Step 4: `CLAUDE.md`** — in "Domain extensions", after the sentence on `vestack/README.md`, add:

```markdown
The object inventory (`get_object_inventory`, schema in
`vestack/OBJECT_INVENTORY.md`) is the Cadwork half of the Revit consistency
check; `docs/superpowers/specs/2026-10-15-object-inventory-design.md` records
the Vestack modelling conventions it relies on.
```

and in "What was repaired": in the paragraph starting **Where the 167 tools go.**, change `167` to `168` and `137 reach a bridge operation` to `138 reach a bridge operation`, and `3 of the 140 operations` to `3 of the 141 operations`; in "What this project is", change `Exposes 167` to `Exposes 168`; in "How far verification actually goes", replace the sentence about `MODULE_ID_PATTERN` not matching with: `` `MODULE_ID_PATTERN` accepts `M` + 1 to 4 digits since the object inventory work. ``; in "Commands", update the test count comment to `# 168 tests, no Cadwork needed`.

- [ ] **Step 5: Check the counts you just wrote against the code**

Run: `.venv\Scripts\python -c "from bridge.dispatcher import CommandDispatcher; print(len(CommandDispatcher().operations))"`
Expected: `141`.

- [ ] **Step 6: Commit**

```bash
git add vestack/README.md .claude/skills/cadwork-model/SKILL.md .claude/skills/cadwork-model/tool-inventory.md CLAUDE.md
git commit -m "docs: document the object inventory and its drill-down"
```

---

### Task 9: Live verification on Cadwork 2026 (read-only, with the user)

Not automatable: needs Cadwork 2026, a model copy and the user. No write tool is called.

- [ ] **Step 1: Prepare.** Ask the user to open a **copy** of `250513_AUX_STR_EXE_IndB.3d` in Cadwork 2026, restart Cadwork if bridge code changed since it started (already-imported modules are not reloaded), then start the bridge: Fenêtre → Plugins utilisateur → Controle du Pont MCP → Start Bridge. Preflight with `get_3d_file_path` and confirm the path is the copy.
- [ ] **Step 2: Summary.** Call `get_object_inventory()` (no arguments). Record the elapsed time. Expected: 24 or so modules `M1`…`M24`, each with a frame; counts per module plausible (walls 4 to 8, one or two slabs); report every module warning verbatim.
- [ ] **Step 3: Detail of M1.** Call `get_object_inventory(module_ids=["M1"])`. Expected for `M1-W5`, from the spike's raw reads: `wall_type` `MOB200`, `thickness` 212, wall length (`end` − `start`) 3645, `height` 2645, one opening `MEX type B` with `width` 1455, `height` 2315, `sill` 90. A mismatch is a finding: stop, report it with both values, do not adjust thresholds without the user.
- [ ] **Step 4: Export.** Call `get_object_inventory(output_path="<scratchpad>\\object_inventory_M1-M24.json")`. Record the elapsed time; check the file opens and holds every module with `objects`.
- [ ] **Step 5: Record.** Add the timings and any finding to the spec's "Spike results" section and to `CLAUDE.md` ("How far verification actually goes": add `get_object_inventory` to the operations run live). Commit:

```bash
git add docs/superpowers/specs/2026-10-15-object-inventory-design.md CLAUDE.md
git commit -m "docs: record the first live run of get_object_inventory"
```
