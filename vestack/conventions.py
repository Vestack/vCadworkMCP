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
# Upper-case M only: lower-case units such as "10 m2" in element names must not read as module ids.
MODULE_ID_PATTERN: Pattern[str] = re.compile(
    r"(?<![A-Za-z0-9])M(\d{1,4})(?=$|[-_ ])")

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
    r"^\s*M(\d{1,4})[-_ ]([A-Za-z]+)(\d*)\s*$")

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
