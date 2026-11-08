"""ADR 0095 amendment (2026-11-07): the Bought Parts a Release bills come
from what the Wish sealed, never from the model's bodies."""

import copy
import unittest

from workshop.errors import ContractError
from workshop.release.bought_extras import factory_extra_materials, sealed_bought_lines

CONTRACT = {
    "electrical": {
        "parts": [
            {"id": "usb", "role": "source", "external": True},
            {"id": "usb-c", "bought": "usb-c-receptacle-power", "role": "inlet"},
            {"id": "led-1", "bought": "led-2835-warm-2200k", "role": "load"},
            {"id": "led-2", "bought": "led-2835-warm-2200k", "role": "load", "count": 2},
        ],
        "pcba": {"parts": ["usb-c", "led-1"], "bounds_mm": [[0, 0, 0], [1, 1, 1]]},
    },
    "bought_parts": {
        "parts": [{"bought": "steel-pin-1.5x29.5", "count": 10},
                  {"bought": "spring-compression-6x0.5x20-stainless", "count": 4},
                  {"bought": "glue", "count": 1}],
        "pcba": {"unit_price_cents": 400, "estimate": True, "source": "owner, 2026-11-07"},
    },
}
CATALOGUE = {
    "bought_parts": {"usb-c-receptacle-power": {"name": "USB-C receptacle"}, "glue": {"name": "Glue"}},
    "unit_prices": {"usb-c-receptacle-power": 6, "led-2835-warm-2200k": 2, "steel-pin-1.5x29.5": 6,
                    "spring-compression-6x0.5x20-stainless": 12, "glue": 32},
}


class SealedBoughtLinesTest(unittest.TestCase):
    def test_every_listed_part_is_billed_including_those_with_no_body(self):
        lines = sealed_bought_lines(CONTRACT, CATALOGUE)
        self.assertEqual([(line["part"], line["count"], line["unit_price_cents"]) for line in lines], [
            ("led-2835-warm-2200k", 2, 2),
            ("steel-pin-1.5x29.5", 10, 6),
            ("spring-compression-6x0.5x20-stainless", 4, 12),
            ("glue", 1, 32),
            ("pcba", 1, 400),
        ])
        self.assertNotIn("usb", [line["part"] for line in lines], "the buyer's charger is not bought")
        self.assertEqual(lines[-1]["price_source"], "contract")
        self.assertEqual((lines[-1]["estimate"], lines[-1]["source"]), (True, "owner, 2026-11-07"))
        self.assertEqual(lines[0]["name"], "led-2835-warm-2200k", "an entry without a name bills its id")
        billed = factory_extra_materials(lines)
        self.assertEqual(sum(line["unit_price_cents"] * line["count"] for line in billed),
                         4 + 60 + 48 + 32 + 400)

    def test_a_priced_board_includes_the_parts_the_section_places_on_it(self):
        # Owner, 2026-11-08: usb-c and led-1 are in pcba.parts, so the board's
        # price covers them. led-2 shares led-1's catalogue entry but is off
        # the board, so it alone is billed under that entry.
        lines = sealed_bought_lines(CONTRACT, CATALOGUE)
        parts = {line["part"]: line for line in lines}
        self.assertNotIn("usb-c-receptacle-power", parts)
        self.assertEqual(parts["led-2835-warm-2200k"]["count"], 2)
        self.assertEqual(parts["pcba"]["includes"], ["led-1", "usb-c"])

    def test_an_unpriced_board_bills_its_parts_and_refuses_for_itself(self):
        contract = copy.deepcopy(CONTRACT)
        del contract["bought_parts"]["pcba"]
        lines = sealed_bought_lines(contract, CATALOGUE)
        self.assertEqual([(line["part"], line["count"]) for line in lines][:2],
                         [("usb-c-receptacle-power", 1), ("led-2835-warm-2200k", 3)])
        self.assertNotIn("includes", lines[-1])
        with self.assertRaisesRegex(ContractError, "no sealed price.*: pcba"):
            factory_extra_materials(lines)

    def test_a_part_or_board_without_a_sealed_price_is_refused_by_name(self):
        contract = copy.deepcopy(CONTRACT)
        del contract["bought_parts"]["pcba"]
        catalogue = copy.deepcopy(CATALOGUE)
        del catalogue["unit_prices"]["glue"]
        with self.assertRaisesRegex(ContractError, "no sealed price.*: glue, pcba"):
            factory_extra_materials(sealed_bought_lines(contract, catalogue))

    def test_a_run_that_sealed_no_bought_parts_bills_nothing(self):
        for contract in (None, {}, {"geometries": []}):
            self.assertIsNone(sealed_bought_lines(contract, None))


if __name__ == "__main__":
    unittest.main()
