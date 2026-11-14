"""ADR 0104 decision 1: a kit tree may declare its FDM Sheets.

Contract: ``assembly_tree.sheets`` lists ``{id, filament, parts: [{id,
count}]}``; a Sheet id is its filament's Part letter and a number; it
carries only printed, non-loose Parts of that filament; over all Sheets a
Part's count covers the toy's; every printed Part is on a Sheet or states
``loose_reason``; ``small_reason`` is short text. A tree without Sheets is
unchanged."""

import unittest

from workshop.errors import ContractError
from workshop.wish.design_contract import parse_design_contract
from tests.wish.test_assembly_tree import _catalogues, _tree_block
from tests.wish.test_design_contract import _contract_text

SHEETS = [
    {"id": "A1", "filament": "navy", "parts": [{"id": "A01-case-shell", "count": 1}]},
    {"id": "B1", "filament": "dark-oak", "parts": [{"id": "B01-cabinet-carcass", "count": 1},
                                                   {"id": "B02-cabinet-door", "count": 2}]},
    {"id": "C1", "filament": "oak", "parts": [{"id": "C01-desk-body", "count": 2}]},
]


def _block(sheets=SHEETS, loose_inkwell=True):
    import copy

    block = _tree_block()
    tree = block["assembly_tree"]
    tree["sheets"] = copy.deepcopy(sheets)
    if loose_inkwell:
        next(p for p in tree["parts"] if p["id"] == "D01-inkwell")["loose_reason"] = "A round pot."
    return block


class KitSheetsContractTest(unittest.TestCase):
    def _parse(self, block):
        return parse_design_contract(_contract_text(block), catalogues=_catalogues())

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            self._parse(block)
        return str(caught.exception)

    def test_sheets_seal_with_the_tree(self):
        contract = self._parse(_block())
        self.assertEqual(contract.to_dict()["assembly_tree"]["sheets"], SHEETS)

    def test_a_tree_without_sheets_is_unchanged(self):
        self._parse(_tree_block())

    def test_every_printed_part_is_on_a_sheet_or_loose(self):
        self.assertIn("D01-inkwell is on no Sheet: put it on a Sheet of dark-blue, or state its loose_reason",
                      self._refused(_block(loose_inkwell=False)))

    def test_the_sheets_cover_the_toy(self):
        sheets = [dict(s) for s in SHEETS]
        sheets[2] = {"id": "C1", "filament": "oak", "parts": [{"id": "C01-desk-body", "count": 1}]}
        self.assertIn("the Sheets carry 1 x C01-desk-body, but the toy uses 2", self._refused(_block(sheets)))

    def test_a_sheet_is_one_filaments_plate(self):
        for sheets, fragment in (
            (SHEETS + [{"id": "A2", "filament": "navy", "parts": [{"id": "C01-desk-body", "count": 1}]}],
             "C01-desk-body is oak, letter C; Sheet A2 is navy"),
            ([{**SHEETS[0], "id": "B9"}] + SHEETS[1:], "Sheet B9 is navy"),
            (SHEETS + [{"id": "D1", "filament": "dark-blue", "parts": [{"id": "D01-inkwell", "count": 1}]}],
             "D01-inkwell states loose_reason, so it is on no Sheet"),
            (SHEETS + [{"id": "E1", "filament": "navy", "parts": [{"id": "P01-hinge-pin", "count": 1}]}],
             "'P01-hinge-pin' is no printed Part"),
            (SHEETS + [dict(SHEETS[0])], "A1 names two Sheets"),
            ([{**SHEETS[0], "id": "a1"}] + SHEETS[1:], "must be its filament's Part letter and a number"),
            ([{**SHEETS[0], "parts": [{"id": "A01-case-shell", "count": 0}]}] + SHEETS[1:], "positive integer"),
            ([{**SHEETS[0], "extra": 1}] + SHEETS[1:], "must be exactly {id, filament, parts}"),
            ([], "must be a non-empty list"),
        ):
            self.assertIn(fragment, self._refused(_block(sheets)), sheets)

    def test_a_small_reason_is_short_text(self):
        block = _block()
        part = next(p for p in block["assembly_tree"]["parts"] if p["id"] == "B02-cabinet-door")
        part["small_reason"] = "A thin door glued flat in its frame."
        self._parse(block)
        for bad in ("", "x" * 301, 2):
            part["small_reason"] = bad
            self.assertIn("small_reason must say", self._refused(block))


if __name__ == "__main__":
    unittest.main()
