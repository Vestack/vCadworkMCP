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
