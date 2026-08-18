"""Vestack modular-construction conventions.

Every threshold and naming rule specific to Vestack lives here. Retune this file
rather than the logic in module_inventory.py, and see README.md for what each
value means in practice. All lengths are millimetres, Cadwork's native unit.
"""
import re
from typing import Pattern, Tuple

# --- Module identity -------------------------------------------------------

# A module id looks like "M139": the letter M followed by exactly three digits.
# Matched anywhere inside a field value, so "Module M139" is recognised too.
MODULE_ID_PATTERN: Pattern[str] = re.compile(r"\bM\d{3}\b")

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
