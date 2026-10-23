"""ADR 0091: a schema 6 Design Contract declares its Print Sheets."""

import copy
import json
import unittest

from workshop.errors import ContractError
from workshop.wish.design_contract import parse_design_contract
from tests.wish.test_design_contract import _contract_text, _guide_block


def _print_section():
    return {
        "stocks": {
            "paper": {"name": "matte couche 120 gsm", "caliper_mm": 0.10},
            "sticker": {"name": "paper decal", "caliper_mm": 0.15},
            "card": {"name": "Ivory 300 gsm", "caliper_mm": 0.45},
            "film": {"name": "laser OHP film 100 um", "caliper_mm": 0.10},
        },
        "art": [
            {"file": "print-01-night-sky.png", "shows": "A starry night sky.",
             "source": "https://ambientcg.com/view?id=NightSky001", "licence": "CC0-1.0"},
            {"file": "print-02-spell-book.png", "shows": "A red spell book's cover, spine and back."},
            {"file": "print-03-globe-gores.png", "shows": "Twelve joined antique map gores."},
            {"file": "print-04-open-pages.png", "shows": "Six pages of handwritten charms."},
            {"file": "print-05-cloud.png", "shows": "A grey cloud silhouette."},
            {"file": "print-06-notice.png", "shows": "A notice reading 'No flying in class'."},
            {"file": "print-07-glass.png", "shows": "Clear glazing with a frosted border."},
        ],
        "pieces": [
            {"id": "sky", "art": "print-01-night-sky.png", "stock": "paper", "way": "flat",
             "on": "spine-housing", "where": "The recess behind the lancets.", "size_mm": [40, 60]},
            {"id": "spell-book", "art": "print-02-spell-book.png", "stock": "paper", "way": "wrap",
             "on": "heart-core", "where": "The book block on the desk.", "block_mm": [14, 10, 4],
             "around": "cover", "count": 2},
            {"id": "globe", "art": "print-03-globe-gores.png", "stock": "paper", "way": "sphere",
             "on": "heart-core", "where": "The globe ball.", "diameter_mm": 25, "gores": 12},
            {"id": "open-book", "art": "print-04-open-pages.png", "stock": "paper", "way": "fold",
             "on": "wing#1", "where": "The open book's cover board.", "page_mm": [12, 16], "pages": 6},
            {"id": "cloud", "art": "print-05-cloud.png", "stock": "card", "way": "stand",
             "on": "spine-housing", "where": "The slot behind the window.", "size_mm": [50, 20],
             "outline": "oval", "slot_mm": 30},
            {"id": "notice", "art": "print-06-notice.png", "stock": "sticker", "way": "sticker",
             "on": "wing", "where": "The flat panel on the wing.", "size_mm": [10, 14]},
            {"id": "glass", "art": "print-07-glass.png", "stock": "film", "way": "flat",
             "on": "spine-housing", "where": "The window frame's rebate.", "size_mm": [20, 30]},
        ],
    }


def _print_block(guides=True, **overrides):
    block = _guide_block()
    block["schema_version"] = 6
    if not guides:
        del block["guides"]
    block["print"] = _print_section()
    block.update(overrides)
    return block


class PrintSheetsContractTest(unittest.TestCase):
    def _refused(self, block):
        with self.assertRaises(ContractError) as caught:
            parse_design_contract(_contract_text(block))
        return str(caught.exception)

    def test_a_schema_6_contract_seals_its_print_section_verbatim(self):
        block = _print_block()
        contract = parse_design_contract(_contract_text(block))
        self.assertEqual(contract.schema_version, 6)
        self.assertEqual(contract.to_dict()["print"], block["print"])
        self.assertEqual(contract.print_sheets.art_files[0], "print-01-night-sky.png")
        self.assertEqual(len(contract.print_sheets.pieces), 7)
        # Schema 6 keeps the cameras, the Interface text and the guides.
        self.assertEqual(contract.references[0].camera, (-60.0, 20.0))
        self.assertTrue(all(item.text for item in contract.interfaces))
        self.assertEqual(len(contract.guides), 2)
        # Print art is never a reference: the label table is unchanged.
        self.assertNotIn("print-01-night-sky.png", contract.reference_labels())

    def test_guides_are_optional_from_schema_6(self):
        contract = parse_design_contract(_contract_text(_print_block(guides=False)))
        self.assertIsNone(contract.guides)
        self.assertNotIn("guides", contract.to_dict())
        block = _print_block()
        block["guides"] = []
        self.assertIn("guides must be a non-empty list", self._refused(block))

    def test_schema_6_needs_the_print_section_and_earlier_schemas_refuse_it(self):
        block = _print_block()
        del block["print"]
        self.assertIn("print must be an object", self._refused(block))
        block = _guide_block()
        block["print"] = _print_section()
        self.assertIn("print needs schema_version 6", self._refused(block))

    def test_every_bad_entry_is_refused_naming_it(self):
        def piece(index, **changes):
            def change(section):
                section["pieces"][index].update(changes)
                for key, value in changes.items():
                    if value is None:
                        del section["pieces"][index][key]
            return change

        def art(index, **changes):
            def change(section):
                section["art"][index].update(changes)
                for key, value in changes.items():
                    if value is None:
                        del section["art"][index][key]
            return change

        cases = {
            "print.stocks.ink is not a stock": lambda s: s["stocks"].update(ink={"name": "x", "caliper_mm": 0.1}),
            "print.stocks.paper.caliper_mm must be a thickness": lambda s: s["stocks"]["paper"].update(caliper_mm=2),
            "print.stocks.card must be exactly": lambda s: s["stocks"]["card"].update(gsm=300),
            "print.art[1].file must be numbered print-02": art(1, file="print-03-spell-book.png"),
            "print.art[0].file must look like print-NN": art(0, file="ref-01-sky.png"),
            "print.art[0].licence must be CC0-1.0": art(0, licence="CC-BY-4.0"),
            "print.art[0] needs both source and licence": art(0, licence=None),
            "print.art[0].source must be the http(s) link": art(0, source="ambientcg"),
            "print.art[1].shows must say": art(1, shows=" "),
            "print.pieces[0].way must be one of": piece(0, way="paint"),
            "print.pieces[0]: a flat piece does not take gores": piece(0, gores=8),
            "print.pieces[0].size_mm has an edge under 5 mm": piece(0, size_mm=[4, 60]),
            "print.pieces[0].size_mm must be [width, height]": piece(0, size_mm=[40]),
            "print.pieces[0]: a flat piece is cut from paper or film, not card": piece(0, stock="card"),
            "print.pieces[5]: a sticker piece is cut from sticker, not paper": piece(5, stock="paper"),
            "print.pieces[1].block_mm height is under 5 mm": piece(1, block_mm=[4, 10, 4]),
            "print.pieces[1].around must be cover": piece(1, around="spiral"),
            "print.pieces[1].count must be a whole number": piece(1, count=0),
            "print.pieces[2].diameter_mm must be at least 25 mm": piece(2, diameter_mm=20),
            "print.pieces[2].gores must be a whole number from 8 to 24": piece(2, gores=6),
            "print.pieces[3].pages must be a whole number from 2 to 32": piece(3, pages=1),
            "print.pieces[3].on names instance 'wing#3'": piece(3, on="wing#3"),
            "print.pieces[4].slot_mm is longer than the card is wide": piece(4, slot_mm=60),
            "print.pieces[4].outline must be rect or oval": piece(4, outline="star"),
            "print.pieces[6].on names a Unique Geometry that does not exist": piece(6, on="door"),
            "print.pieces[6].where must say": piece(6, where=""),
            "print.pieces[6].art must be a file print.art lists": piece(6, art="print-09-x.png"),
            "print.pieces[6].id repeats an earlier piece id": piece(6, id="sky"),
            "print.pieces[6].stock must be a stock print.stocks declares": piece(6, stock="vinyl"),
        }
        for expected, change in cases.items():
            with self.subTest(expected=expected):
                block = _print_block()
                change(block["print"])
                self.assertIn(expected, self._refused(block))

    def test_unused_stock_and_art_are_refused(self):
        block = _print_block()
        block["print"]["pieces"] = [p for p in block["print"]["pieces"] if p["stock"] != "film"]
        message = self._refused(block)
        self.assertIn("print.stocks.film is declared but no piece is cut from it", message)
        self.assertIn("print.art print-07-glass.png is used by no piece", message)

    def test_check_print_art_names_wants_the_contracts_files_in_order(self):
        contract = parse_design_contract(_contract_text(_print_block()))
        files = list(contract.print_sheets.art_files)
        contract.check_print_art_names(files)
        with self.assertRaisesRegex(ContractError, "lists 7 print art image\\(s\\) but 6 were given"):
            contract.check_print_art_names(files[:-1])
        swapped = [files[1], files[0]] + files[2:]
        with self.assertRaisesRegex(ContractError, "print art 1 seals as print-02"):
            contract.check_print_art_names(swapped)
        earlier = parse_design_contract(_contract_text(_guide_block()))
        earlier.check_print_art_names([])
        with self.assertRaisesRegex(ContractError, "lists 0 print art"):
            earlier.check_print_art_names(files[:1])

    def test_the_sealed_section_round_trips_through_json(self):
        block = _print_block()
        contract = parse_design_contract(_contract_text(block))
        again = parse_design_contract(_contract_text(copy.deepcopy(contract.to_dict())))
        self.assertEqual(json.dumps(again.to_dict(), sort_keys=True),
                         json.dumps(contract.to_dict(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()
