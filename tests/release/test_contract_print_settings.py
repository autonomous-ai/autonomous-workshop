"""B24: which sealed words state a toy's print material."""

import unittest

from workshop.errors import ContractError
from workshop.release.public_example import contract_infill_percent, contract_print_settings


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


BEAVER = (
    "Workshop prints with a 0.4 mm nozzle in PETG; no part may need support.\n"
    "Print settings (owner's cost choice): 8% infill in every part, and 2 walls on\n"
    "the base, the body and the tail."
)


class ContractInfillPercentTest(unittest.TestCase):
    def test_the_beaver_contracts_infill(self):
        self.assertEqual(
            contract_infill_percent(_contract(("Print stances and details", BEAVER))), 8
        )

    def test_one_infill_stated_twice_is_one_infill(self):
        text = "Print at 12 % Infill. The base too: 12% infill."
        self.assertEqual(contract_infill_percent(_contract(("Print rules", text))), 12)

    def test_no_infill_is_the_factory_default(self):
        self.assertIsNone(contract_infill_percent(None))
        self.assertIsNone(contract_infill_percent({"requirements": []}))
        self.assertIsNone(
            contract_infill_percent(_contract(("Print stances", "Workshop prints in PLA.")))
        )

    def test_an_infill_named_outside_a_print_section_is_not_the_print_infill(self):
        contract = _contract(("Body", "The hollow body saves the 20% infill a solid one needs."))
        self.assertIsNone(contract_infill_percent(contract))

    def test_two_infills_are_refused(self):
        text = "8% infill in the base; 20% infill in the arms."
        with self.assertRaisesRegex(ContractError, "8% and 20%"):
            contract_infill_percent(_contract(("Print rules", text)))

    def test_an_infill_factory_cannot_print_is_refused(self):
        for text in ("Print at 4% infill.", "Print at 8.5% infill.", "Print at 120% infill."):
            with self.subTest(text=text), self.assertRaises(ContractError):
                contract_infill_percent(_contract(("Print rules", text)))


if __name__ == "__main__":
    unittest.main()
