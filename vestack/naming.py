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
