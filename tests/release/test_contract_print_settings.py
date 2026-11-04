"""B24: which sealed words state a toy's print material."""

import unittest

from workshop.errors import ContractError
from workshop.release.public_example import contract_print_settings


def _contract(*sections):
    return {"prose": [{"heading": heading, "text": text} for heading, text in sections]}


class ContractPrintSettingsTest(unittest.TestCase):
    def test_a_decimal_and_a_line_wrap_do_not_cut_the_sentence(self):
        text = "Workshop prints with a 0.4 mm\nnozzle in PETG; no part needs support. Infill is 8%."
        self.assertEqual(
            contract_print_settings(_contract(("Print stances and details", text))),
            "Workshop prints with a 0.4 mm nozzle in PETG; no part needs support.",
        )

    def test_a_toy_of_two_materials_keeps_both_sentences_in_order(self):
        text = "The chamber is translucent PETG, for heat. Plain text here. All other parts are PLA."
        self.assertEqual(
            contract_print_settings(_contract(("Print rules and stances", text))),
            "The chamber is translucent PETG, for heat. All other parts are PLA.",
        )

    def test_a_material_named_outside_a_print_section_is_not_the_print_material(self):
        contract = _contract(("Light path", "PETG softens far above the lamp's heat."))
        self.assertIsNone(contract_print_settings(contract))

    def test_a_word_containing_a_material_is_not_a_material(self):
        contract = _contract(("Print stances", "The PLATE lies flat. ABSOLUTELY no support."))
        self.assertIsNone(contract_print_settings(contract))

    def test_no_contract_or_no_prose_has_none(self):
        self.assertIsNone(contract_print_settings(None))
        self.assertIsNone(contract_print_settings({"requirements": []}))

    def test_a_print_section_without_text_is_refused(self):
        with self.assertRaises(ContractError):
            contract_print_settings({"prose": [{"heading": "Print stances", "text": 3}]})


if __name__ == "__main__":
    unittest.main()
