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



FIT_TEST = {"pieces": [{"id": "T1", "name": "Fit slots"}, {"id": "T2", "name": "Fit tab"}],
            "text": "Before you start, press T2 into T1: it goes in firmly and holds."}


def _fit_sheets(fit_test=FIT_TEST, on=0):
    import copy

    sheets = copy.deepcopy(SHEETS)
    sheets[on]["fit_test"] = copy.deepcopy(fit_test)
    return sheets


class FitTestContractTest(unittest.TestCase):
    """ADR 0092 amendment 2026-11-26: a Sheet may declare fit-test pieces
    T1-T99 outside the tree's Parts; no step uses them and no spare counts
    them; they seal and hash with the tree."""

    def _parse(self, block):
        return parse_design_contract(_contract_text(block), catalogues=_catalogues())

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            self._parse(block)
        return str(caught.exception)

    def test_a_fit_test_pair_seals_with_its_sheet(self):
        from workshop.make.kit_tree import tree_digest
        from workshop.wish.assembly_tree import fit_test_pieces

        contract = self._parse(_block(_fit_sheets()))
        tree = contract.to_dict()["assembly_tree"]
        self.assertEqual(tree["sheets"][0]["fit_test"], FIT_TEST)
        self.assertEqual(fit_test_pieces(tree), {"T1": "A1", "T2": "A1"})
        # Hash-bound: the fit test is in the tree's digest like other Sheet content.
        plain = self._parse(_block()).to_dict()["assembly_tree"]
        self.assertNotEqual(tree_digest({"assembly_tree": tree}), tree_digest({"assembly_tree": plain}))

    def test_a_kit_that_ships_no_spares_takes_a_fit_test(self):
        sheets = _fit_sheets()
        sheets[1]["parts"][1]["count"] = 1   # the fixture's spare door
        block = _block(sheets)
        block["assembly_tree"]["spares"] = "none"
        self._parse(block)

    def test_fit_test_ids_cannot_be_part_or_sheet_ids(self):
        for pieces, fragment in (
            ([{"id": "T01-slots", "name": "Slots"}], "must be T and a number, T1 to T99, with no mnemonic"),
            ([{"id": "T0", "name": "Slots"}], "T1 to T99"),
            ([{"id": "T01", "name": "Slots"}], "T1 to T99"),
            ([{"id": "T100", "name": "Slots"}], "T1 to T99"),
            ([{"id": "A1", "name": "Slots"}], "T1 to T99"),
            ([{"id": "T1", "name": "Slots"}, {"id": "T1", "name": "Tab"}], "T1 is already declared"),
            ([{"id": "T1"}], "must be exactly {id, name}"),
            ([], "must list 1 to 8 fit-test pieces"),
        ):
            message = self._refused(_block(_fit_sheets({**FIT_TEST, "pieces": pieces})))
            self.assertIn(fragment, message, pieces)

    def test_a_fit_test_needs_its_instruction(self):
        self.assertIn("fit_test.text must be one short English instruction",
                      self._refused(_block(_fit_sheets({**FIT_TEST, "text": ""}))))
        self.assertIn("fit_test must be exactly {pieces, text}",
                      self._refused(_block(_fit_sheets({"pieces": FIT_TEST["pieces"]}))))

    def test_one_piece_is_declared_on_one_sheet(self):
        sheets = _fit_sheets()
        sheets[1]["fit_test"] = {"pieces": [{"id": "T2", "name": "Tab"}], "text": "Press it in."}
        self.assertIn("fit-test piece T2 is already declared on Sheet", self._refused(_block(sheets)))

    def test_a_fit_test_piece_is_no_part_of_a_sheets_parts(self):
        sheets = _fit_sheets()
        sheets[0]["parts"].append({"id": "T1", "count": 1})
        self.assertIn("'T1' is no printed Part of the tree", self._refused(_block(sheets)))

    def test_no_step_needs_a_fit_test_piece(self):
        # The tree's steps are unchanged: T1 and T2 are in no step, and the
        # contract still seals.
        tree = self._parse(_block(_fit_sheets())).to_dict()["assembly_tree"]
        used = {entry["id"] for step in tree["steps"] for entry in step["inputs"]}
        self.assertFalse({"T1", "T2"} & used)


def _shared(code="B37", **changes):
    """The fixture's carcass and door, both dark-oak panels, as one print."""

    block = _block()
    for part in block["assembly_tree"]["parts"]:
        if part["id"] in ("B01-cabinet-carcass", "B02-cabinet-door"):
            part["print"] = code
            part.update(changes.get(part["id"], {}))
    return block


class PrintCodeContractTest(unittest.TestCase):
    """ADR 0092 amendment 2026-11-26: Parts that are one print may share a
    ``print`` code; they must agree on filament, form, thickness and
    looseness, and the spares-none count is per code."""

    def _parse(self, block):
        return parse_design_contract(_contract_text(block), catalogues=_catalogues())

    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            self._parse(block)
        return str(caught.exception)

    def test_a_shared_print_code_seals_with_the_tree(self):
        from workshop.wish.assembly_tree import print_code, print_groups

        tree = self._parse(_shared()).to_dict()["assembly_tree"]
        self.assertEqual(print_groups(tree), {"B37": ["B01-cabinet-carcass", "B02-cabinet-door"]})
        door = next(p for p in tree["parts"] if p["id"] == "B02-cabinet-door")
        self.assertEqual(print_code("B02-cabinet-door", door), "B37")
        self.assertEqual(print_code("C01-desk-body", {}), "C01-desk-body")

    def test_a_contract_without_print_codes_is_unchanged(self):
        from workshop.wish.assembly_tree import print_groups

        self.assertEqual(print_groups(self._parse(_block()).to_dict()["assembly_tree"]), {})

    def test_a_print_code_is_the_parts_letter_and_two_or_three_digits(self):
        for code in ("B7", "B1234", "C37", "b37", "B37-cap", 37):
            self.assertIn(".print must be a print code: the Part's letter B", self._refused(_shared(code)))
        self._parse(_shared("B370"))

    def test_parts_sharing_a_code_are_one_print(self):
        door = {"B02-cabinet-door": {"form": "solid"}}
        self.assertIn("B01-cabinet-carcass and B02-cabinet-door share print code B37 but differ in form",
                      self._refused(_shared(**door)))
        thick = {"B02-cabinet-door": {"thickness_mm": 3.0, "thickness_reason": "A stiffer door."}}
        self.assertIn("differ in thickness_mm", self._refused(_shared(**thick)))

    def test_a_print_code_is_no_sheet_or_fit_test_id(self):
        block = _shared("B37")
        block["assembly_tree"]["sheets"][1]["id"] = "B37"
        self.assertIn("print code B37 is also a Sheet id", self._refused(block))

    def test_a_kit_that_ships_no_spares_counts_a_shared_print_once(self):
        # The fixture's door Sheet carries one spare door: under one code the
        # print B37 is carried 3 times for 2 uses.
        block = _shared()
        block["assembly_tree"]["spares"] = "none"
        self.assertIn('the Sheets carry 3 x B37, but the toy uses 2 and the kit declares spares "none"',
                      self._refused(block))
        block["assembly_tree"]["sheets"][1]["parts"][1]["count"] = 1
        self._parse(block)


if __name__ == "__main__":
    unittest.main()
