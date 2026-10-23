"""ADR 0091 decision 6: a deterministic tool lays every Print Piece out on A4
Print Sheets and checks the layout half of the Print Sheet gate."""
from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import tempfile
import unittest

from PIL import Image

from tests.wish.test_print_sheets import _print_section

TOOL = (Path(__file__).resolve().parents[2]
        / "src/workshop/make/skills/print-details/scripts/print_sheets.py")


def _contract(section=None):
    return {"schema_version": 6, "title": "Test Nook", "print": section or _print_section()}


class PrintSheetLayoutTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tool = runpy.run_path(str(TOOL))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.art = self.root / "art"
        self.art.mkdir()

    def write_art(self, contract, dpi=320, skip=()):
        """Art for every piece at ``dpi``, shaped like the piece."""

        stocks = contract["print"]["stocks"]
        for piece in contract["print"]["pieces"]:
            if piece["art"] in skip:
                continue
            shape = self.tool["piece_shape"](piece, stocks)
            size = (math.ceil(shape["width"] / 25.4 * dpi), math.ceil(shape["height"] / 25.4 * dpi))
            Image.new("RGB", size, "red").save(self.art / piece["art"])

    def run_tool(self, contract, *extra, out="out"):
        path = self.root / "contract.json"
        path.write_text(json.dumps(contract))
        code = self.tool["main"](["--contract", str(path), "--art", str(self.art),
                                  "-o", str(self.root / out), *extra])
        report = json.loads((self.root / out / "print-sheets.json").read_text())
        return code, report

    # -- shapes ----------------------------------------------------------------

    def test_each_way_has_the_flat_size_its_declared_sizes_give(self):
        stocks = _print_section()["stocks"]
        pieces = {piece["id"]: piece for piece in _print_section()["pieces"]}
        shape = self.tool["piece_shape"]
        sky = shape(pieces["sky"], stocks)
        self.assertEqual((sky["width"], sky["height"]), (40.0, 60.0))
        # A cover wraps front, spine and back: two folds, each adding the
        # paper's caliper.
        book = shape(pieces["spell-book"], stocks)
        self.assertAlmostEqual(book["width"], 2 * 10 + 4 + 2 * 0.10)
        self.assertEqual(book["height"], 14.0)
        self.assertEqual(len(book["folds"]), 2)
        band = shape(dict(pieces["spell-book"], around="band"), stocks)
        self.assertAlmostEqual(band["width"], 2 * 10 + 2 * 4 + 4 * 0.10 + 5.0)
        self.assertEqual(len(band["folds"]), 4)
        globe = shape(pieces["globe"], stocks)
        self.assertAlmostEqual(globe["width"], math.pi * 25)
        self.assertAlmostEqual(globe["height"], math.pi * 25 / 2)
        self.assertEqual(globe["edges"], [])
        pages = shape(pieces["open-book"], stocks)
        self.assertEqual((pages["width"], pages["height"]), (72.0, 16.0))
        self.assertEqual(len(pages["folds"]), 5)
        cloud = shape(pieces["cloud"], stocks)
        self.assertEqual((cloud["width"], cloud["height"]), (50.0, 25.0))
        self.assertTrue(all(0 <= x <= 50.0 + 1e-9 and 0 <= y <= 25.0 + 1e-9
                            for x, y in cloud["outline"]))

    # -- the layout --------------------------------------------------------------

    def test_a_good_contract_passes_and_writes_every_sheet(self):
        contract = _contract()
        self.write_art(contract)
        code, report = self.run_tool(contract)
        self.assertEqual(code, 0, report["failures"])
        self.assertTrue(report["passed"])
        self.assertEqual([sheet["sheet"] for sheet in report["sheets"]],
                         ["paper-1", "sticker-1", "card-1", "film-1"])
        labels = [p["label"] for sheet in report["sheets"] for p in sheet["pieces"]]
        self.assertIn("spell-book 1/2", labels)
        self.assertIn("spell-book 2/2", labels)
        self.assertEqual(len(labels), 8)
        out = self.root / "out"
        self.assertEqual(report["previews"], ["sheet-paper-1.png", "sheet-sticker-1.png",
                                              "sheet-card-1.png", "sheet-film-1.png"])
        for name in report["previews"]:
            self.assertTrue((out / name).is_file())
        pdf = (out / "print-sheets.pdf").read_bytes()
        self.assertEqual(report["pdf"]["sha256"], hashlib.sha256(pdf).hexdigest())
        with Image.open(out / "sheet-paper-1.png") as preview:
            self.assertEqual(preview.size, (827, 1170))  # A4 at 100 dpi, rounded up

    def test_the_same_inputs_give_the_same_bytes(self):
        contract = _contract()
        self.write_art(contract)
        self.run_tool(contract, out="a")
        self.run_tool(contract, out="b")
        for path in sorted((self.root / "a").iterdir()):
            self.assertEqual(path.read_bytes(), (self.root / "b" / path.name).read_bytes(), path.name)

    def test_pieces_fill_further_pages_and_never_overlap(self):
        section = _print_section()
        section["pieces"][0]["count"] = 20  # twenty 40 x 60 mm skies, 16 to a page
        contract = _contract(section)
        self.write_art(contract)
        code, report = self.run_tool(contract, "--check")
        self.assertEqual(code, 0, report["failures"])
        paper = [sheet for sheet in report["sheets"] if sheet["stock"] == "paper"]
        self.assertEqual([sheet["sheet"] for sheet in paper], ["paper-1", "paper-2"])
        for sheet in report["sheets"]:
            boxes = [(p["x_mm"], p["y_mm"], p["x_mm"] + (p["size_mm"][1] if p["rotated"] else p["size_mm"][0]),
                      p["y_mm"] + (p["size_mm"][0] if p["rotated"] else p["size_mm"][1]))
                     for p in sheet["pieces"]]
            for index, a in enumerate(boxes):
                self.assertGreaterEqual(a[0], 10.0 - 1e-6)
                self.assertLessEqual(a[2], 200.0 + 1e-6)
                for b in boxes[index + 1:]:
                    self.assertTrue(a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])
        self.assertFalse((self.root / "out" / "print-sheets.pdf").exists())

    def test_a_long_piece_turns_a_quarter_turn_to_fit(self):
        section = _print_section()
        section["pieces"][3]["pages"] = 16  # 16 x 12 = 192 mm, wider than 190
        contract = _contract(section)
        self.write_art(contract)
        code, report = self.run_tool(contract, "--check")
        self.assertEqual(code, 0, report["failures"])
        placed = [p for s in report["sheets"] for p in s["pieces"] if p["id"] == "open-book"][0]
        self.assertTrue(placed["rotated"])

    # -- failures ----------------------------------------------------------------

    def test_every_layout_failure_is_named(self):
        section = _print_section()
        section["pieces"][3]["page_mm"] = [20, 16]
        section["pieces"][3]["pages"] = 15  # 300 mm: fits no A4 sheet either way
        contract = _contract(section)
        self.write_art(contract, skip=("print-06-notice.png",))
        Image.new("RGB", (40, 60), "red").save(self.art / "print-01-night-sky.png")  # 25 dpi
        Image.new("RGB", (900, 900), "red").save(self.art / "print-07-glass.png")  # square
        code, report = self.run_tool(contract)
        self.assertEqual(code, 1)
        failures = "\n".join(report["failures"])
        self.assertIn("open-book does not fit on an A4 sheet", failures)
        self.assertIn("notice: art print-06-notice.png is missing", failures)
        self.assertIn("sky: art print-01-night-sky.png prints at 25 dpi, under 300", failures)
        self.assertIn("glass: art print-07-glass.png is 900x900 px, the wrong shape", failures)
        # The files are still written, so the failure can be seen.
        self.assertTrue((self.root / "out" / "print-sheets.pdf").is_file())

    def test_a_cut_edge_under_the_scissors_limit_fails(self):
        section = _print_section()
        section["pieces"][4]["slot_mm"] = 4
        contract = _contract(section)
        self.write_art(contract)
        code, report = self.run_tool(contract, "--check")
        self.assertEqual(code, 1)
        self.assertIn("cloud has a 4.0 mm edge, under the 5 mm scissors limit", report["failures"])

    def test_unusable_input_exits_2(self):
        path = self.root / "contract.md"
        path.write_text("# No block\n")
        self.assertEqual(self.tool["main"](["--contract", str(path), "--art", str(self.art),
                                            "-o", str(self.root / "out")]), 2)
        path.write_text("```design-contract\n%s\n```\n" % json.dumps({"schema_version": 5}))
        self.assertEqual(self.tool["main"](["--contract", str(path), "--art", str(self.art),
                                            "-o", str(self.root / "out")]), 2)

    def test_a_contract_md_and_a_wish_json_are_read_alike(self):
        contract = _contract()
        self.write_art(contract)
        md = self.root / "CONTRACT.md"
        md.write_text("# Nook\n\n```design-contract\n%s\n```\n" % json.dumps(contract))
        wish = self.root / "WISH.json"
        wish.write_text(json.dumps({"context": {"design_contract": copy.deepcopy(contract)}}))
        for source, out in ((md, "md"), (wish, "wish")):
            code = self.tool["main"](["--contract", str(source), "--art", str(self.art),
                                      "-o", str(self.root / out), "--check"])
            self.assertEqual(code, 0)
        self.assertEqual((self.root / "md" / "print-sheets.json").read_bytes(),
                         (self.root / "wish" / "print-sheets.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
