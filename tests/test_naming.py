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

    def test_lower_case_units_are_not_module_ids(self) -> None:
        for value in ("m12", "10 m2", "Isolation 12 m3"):
            self.assertIsNone(parse_module_id(value), value)

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

    def test_a_lower_case_module_prefix_is_not_a_part(self) -> None:
        self.assertIsNone(parse_part("m1-W5"))

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
