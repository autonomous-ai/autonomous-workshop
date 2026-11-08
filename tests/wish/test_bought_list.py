"""ADR 0095 amendment (2026-11-07): a contract's Bought Parts block seals the
pins, springs, glue and board price Release bills as Factory extras."""

import json
import unittest

from workshop.errors import ContractError
from workshop.wish.bought_list import strip_bought_block
from workshop.wish.design_contract import parse_design_contract, prose_sections
from workshop.wish.seed import seed_contract_sha256
from tests.wish.test_design_contract import _PROSE, _contract_text
from tests.wish import test_electrical
from tests.wish.test_electrical import _mac_usb, _mac_usb_catalogues, _schema10

PINS = {"bought": "steel-pin-1.5x29.5", "count": 10}
SPRINGS = {"bought": "spring-compression-6x0.5x20-stainless", "count": 4}
GLUE = {"bought": "glue", "count": 1}
BOARD = {"unit_price_cents": 400, "estimate": True, "source": "owner, 2026-11-07"}


def _powered(board=True):
    electrical = _mac_usb()
    if board:
        board = test_electrical.FactoryBoardTest
        electrical["pcba"] = {"parts": board._board(None), "bounds_mm": board.BOUNDS}
    return _schema10(electrical)


def _bought_block(value):
    return "\n```bought-parts\n%s\n```\n" % json.dumps(value)


def _text(value, block=None):
    return _contract_text(_powered() if block is None else block, prose=_PROSE) + _bought_block(value)


class BoughtBlockTest(unittest.TestCase):
    def _parse(self, text):
        return parse_design_contract(text, catalogues=_mac_usb_catalogues())

    def _refused(self, text):
        with self.assertRaises(ContractError) as caught:
            self._parse(text)
        return str(caught.exception)

    def test_the_block_seals_its_parts_their_prices_and_the_board_price(self):
        value = {"parts": [PINS, SPRINGS, GLUE], "pcba": BOARD}
        contract = self._parse(_text(value))
        self.assertEqual(contract.to_dict()["bought_parts"], value)
        snapshot = contract.kit_catalogue()
        for part in ("steel-pin-1.5x29.5", "spring-compression-6x0.5x20-stainless", "glue"):
            self.assertIn(part, snapshot["bought_parts"])
            self.assertNotIn("unit_price_cents", snapshot["bought_parts"][part])
        self.assertEqual(snapshot["unit_prices"]["steel-pin-1.5x29.5"], 6)
        self.assertEqual(snapshot["unit_prices"]["spring-compression-6x0.5x20-stainless"], 12)
        self.assertEqual(snapshot["unit_prices"]["glue"], 32)
        self.assertEqual(snapshot["unit_prices"]["usb-c-receptacle-power"], 6)

    def test_a_contract_without_the_block_is_unchanged(self):
        contract = self._parse(_contract_text(_powered(), prose=_PROSE))
        self.assertNotIn("bought_parts", contract.to_dict())
        self.assertNotIn("unit_prices", contract.kit_catalogue())

    def test_the_block_is_no_prose_and_leaves_the_proof_hash_alone(self):
        plain = _contract_text(_powered(), prose=_PROSE)
        priced = plain + _bought_block({"parts": [GLUE], "pcba": BOARD})
        self.assertEqual(strip_bought_block(priced), plain)
        self.assertEqual(seed_contract_sha256(priced), seed_contract_sha256(plain))
        self.assertEqual(prose_sections(priced), prose_sections(plain))
        self.assertNotEqual(seed_contract_sha256(plain + "\nA changed sentence.\n"), seed_contract_sha256(plain))

    def test_each_part_is_one_catalogue_entry_the_circuit_does_not_count(self):
        for parts, message in (
            ([{"bought": "unobtainium", "count": 1}], "names 'unobtainium', which is no Bought Part"),
            ([GLUE, GLUE], "names glue twice"),
            ([{"bought": "wire-28awg", "count": 1}], "wire-28awg, which the electrical section already counts"),
            ([{"bought": "glue", "count": 0}], "count must be 1 to 999"),
            ([{"bought": "glue", "count": True}], "count must be 1 to 999"),
            ([{"bought": "glue"}], "must be exactly {bought, count}"),
            ([], "parts must be a non-empty list"),
        ):
            self.assertIn(message, self._refused(_text({"parts": parts})))

    def test_the_board_price_needs_a_board_a_price_and_its_source(self):
        self.assertIn("prices a factory-assembled board the electrical section does not name",
                      self._refused(_text({"pcba": BOARD}, block=_powered(board=False))))
        for board, message in (
            (dict(BOARD, unit_price_cents=0), "unit_price_cents must be what one board costs"),
            (dict(BOARD, unit_price_cents=4.0), "unit_price_cents must be what one board costs"),
            (dict(BOARD, estimate="yes"), "estimate must be true or false"),
            (dict(BOARD, source=" "), "source must say who gave the price"),
            ({"unit_price_cents": 400}, "pcba must be exactly {unit_price_cents, estimate, source}"),
        ):
            self.assertIn(message, self._refused(_text({"pcba": board})))

    def test_the_block_is_one_object_on_a_schema_10_contract(self):
        self.assertIn("must be an object with parts, pcba or both", self._refused(_text({"glue": 1})))
        self.assertIn("does not parse as JSON",
                      self._refused(_contract_text(_powered(), prose=_PROSE) + "\n```bought-parts\n{\n```\n"))
        twice = _text({"parts": [GLUE]}) + _bought_block({"parts": [PINS]})
        self.assertIn("at most one bought-parts block", self._refused(twice))
        old = _powered()
        old["schema_version"] = 9
        del old["electrical"]
        self.assertIn("needs schema_version 10 or later", self._refused(_text({"parts": [GLUE]}, block=old)))


if __name__ == "__main__":
    unittest.main()
