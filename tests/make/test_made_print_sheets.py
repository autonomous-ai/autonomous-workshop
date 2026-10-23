"""ADR 0091: before Make is accepted the host checks the Print Sheets on the
exact sealed bytes, without rebuilding geometry, and Release ships them."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import runpy
import tempfile
import types
import unittest

from PIL import Image

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.print_sheets import verify_made_print_sheets
from tests.make.test_print_sheets_layout import TOOL as LAYOUT_TOOL
from tests.wish.test_print_sheets import _print_section

PRODUCT = "artifacts/make/r0001/product"


class MadePrintSheetsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.layout = runpy.run_path(str(LAYOUT_TOOL))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.cad = self.run_root / PRODUCT / "cad"
        (self.cad / "print" / "art").mkdir(parents=True)
        self.section = _print_section()
        self.contract = {"title": "Nook", "print": self.section}
        (self.cad / "print" / "pieces.json").write_text(json.dumps(self.contract, indent=2, sort_keys=True))
        self.sealed = {}
        for piece in self.section["pieces"]:
            shape = self.layout["piece_shape"](piece, self.section["stocks"])
            size = (math.ceil(shape["width"] / 25.4 * 310), math.ceil(shape["height"] / 25.4 * 310))
            path = self.cad / "print" / "art" / piece["art"]
            Image.new("RGB", size, "red").save(path)
            self.sealed[piece["art"]] = hashlib.sha256(path.read_bytes()).hexdigest()
        code = self.layout["main"](["--contract", str(self.cad / "print" / "pieces.json"),
                                    "--art", str(self.cad / "print" / "art"),
                                    "-o", str(self.cad / "print" / "sheets")])
        self.assertEqual(code, 0)

    def made(self):
        manifest = build_artifact_manifest(self.run_root / PRODUCT, created_at="content-addressed")
        return types.SimpleNamespace(product_root=PRODUCT, cad_project_path="cad",
                                     product_manifest=manifest)

    def check(self, contract=None, sealed=None):
        return verify_made_print_sheets(self.run_root, self.made(), contract or self.contract,
                                        self.sealed if sealed is None else sealed)

    def test_the_laid_out_sheets_are_accepted_and_listed(self):
        sheets = self.check()
        self.assertEqual([sheet["sheet"] for sheet in sheets], ["paper-1", "sticker-1", "card-1", "film-1"])
        pdf = (self.cad / "print" / "sheets" / "print-sheets.pdf").read_bytes()
        self.assertEqual({sheet["pdf_sha256"] for sheet in sheets}, {hashlib.sha256(pdf).hexdigest()})
        self.assertEqual(sheets[0]["preview"], "print/sheets/sheet-paper-1.png")
        self.assertEqual(sum(sheet["pieces"] for sheet in sheets), 8)
        json.dumps(sheets)  # plain JSON for the gate receipt (issue #123)

    def test_a_toy_without_print_sheets_checks_nothing(self):
        self.assertEqual(verify_made_print_sheets(self.run_root, self.made(), {"title": "x"}, {}), [])
        self.assertEqual(verify_made_print_sheets(self.run_root, self.made(), None, {}), [])

    def test_an_install_that_is_not_the_sealed_contract_is_refused(self):
        changed = json.loads(json.dumps(self.contract))
        changed["print"]["pieces"][0]["size_mm"] = [41, 60]
        with self.assertRaisesRegex(ContractError, "not the sealed Design Contract's print section"):
            self.check(contract=changed)
        with self.assertRaisesRegex(ContractError, "print art print-01-night-sky.png is not the file"):
            self.check(sealed={**self.sealed, "print-01-night-sky.png": "0" * 64})

    def test_a_failed_or_incomplete_layout_is_refused(self):
        report_path = self.cad / "print" / "sheets" / "print-sheets.json"
        report = json.loads(report_path.read_text())
        report["sheets"][0]["pieces"] = report["sheets"][0]["pieces"][1:]
        report_path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ContractError, "do not place every piece once: missing globe"):
            self.check()
        report["passed"], report["failures"] = False, ["sky does not fit on an A4 sheet"]
        report_path.write_text(json.dumps(report))
        with self.assertRaisesRegex(ContractError, "did not lay out: sky does not fit"):
            self.check()
        (self.cad / "print" / "sheets" / "print-sheets.pdf").unlink()
        report_path.unlink()
        with self.assertRaisesRegex(ContractError, "lacks its Print Sheet file print/sheets/print-sheets.json"):
            self.check()

    def test_a_file_changed_after_the_manifest_is_refused(self):
        made = self.made()
        (self.cad / "print" / "sheets" / "print-sheets.pdf").write_bytes(b"%PDF changed")
        with self.assertRaisesRegex(ContractError, "differs from the Made manifest"):
            verify_made_print_sheets(self.run_root, made, self.contract, self.sealed)

    def test_the_toy_archive_ships_the_sheets_beside_the_models(self):
        from workshop.release.public_archive import _copy_made_tree

        written = {}
        made = self.made()
        made.product_manifest.entries  # noqa: B018 - the tree the archive copies
        made.cad_verification_path = "cad/measure/none.json"
        _copy_made_tree(lambda path, content: written.__setitem__(path, content), self.run_root, made)
        self.assertIn("make/print/sheets/print-sheets.pdf", written)
        self.assertIn("make/print/pieces.json", written)
        self.assertIn("make/print/art/print-01-night-sky.png", written)
        self.assertFalse(any(path.startswith("make/source/cad/print/") for path in written))


class HostHelpersTest(unittest.TestCase):
    def test_the_sealed_art_and_the_accepted_sheets_are_read_back(self):
        from workshop.workflow.native_run import _print_sheet_history, _sealed_print_art

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wish = json.dumps({"references": [
                {"name": "ref-01-a.png", "sha256": "1" * 64},
                {"name": "guide-01-b.png", "sha256": "2" * 64},
                {"name": "print-01-sky.png", "sha256": "3" * 64}]})
            (root / "WISH.json").write_text(wish)
            digest = hashlib.sha256(wish.encode()).hexdigest()
            self.assertEqual(_sealed_print_art(root, digest), {"print-01-sky.png": "3" * 64})
            host = root / "host"
            self.assertEqual(_print_sheet_history(host), [])
            (host / "gates").mkdir(parents=True)
            sheets = [{"sheet": "paper-1", "stock": "paper", "pieces": 3}]
            (host / "gates" / "0002-make.json").write_text(
                json.dumps({"evidence": {"checks": {"print_sheets": sheets}}}))
            self.assertEqual(_print_sheet_history(host), sheets)


class ReceiptPrintTest(unittest.TestCase):
    def test_the_receipt_lists_each_sheet(self):
        from contextlib import redirect_stdout
        from io import StringIO

        from cli.main import _print_native_receipt
        from tests.cli.test_cli import native_receipt

        receipt = {**native_receipt(status="complete", stage="release"), "print_sheets": [
            {"sheet": "paper-1", "stock": "paper", "pieces": 9, "preview": "print/sheets/sheet-paper-1.png",
             "pdf": "print/sheets/print-sheets.pdf", "pdf_sha256": "0" * 64}]}
        stdout = StringIO()
        with redirect_stdout(stdout):
            _print_native_receipt(receipt, verb="wish")
        self.assertIn("Print Sheet: paper-1 (paper), 9 piece(s) — print/sheets/print-sheets.pdf",
                      stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
