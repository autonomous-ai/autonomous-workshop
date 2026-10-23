"""ADR 0092 decision 9: before Make is accepted the host checks a schema 7
kit's Manual on the exact sealed bytes, without rebuilding geometry, and
Release ships it beside the models."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import types
import unittest

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.kit_manual import verify_made_manual
from workshop.make.kit_tree import install_document
from workshop.wish.design_contract import parse_design_contract
from tests.make.test_kit_manual import COMPANY, kit_manual, meshes_for
from tests.make.test_kit_tree import sealed_block
from tests.wish.test_assembly_tree import _catalogues
from tests.wish.test_design_contract import _contract_text

PRODUCT = "artifacts/make/r0001/product"


class MadeKitManualTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.cad = self.run_root / PRODUCT / "cad"
        self.cad.mkdir(parents=True)
        parsed = parse_design_contract(_contract_text(sealed_block()), catalogues=_catalogues())
        self.contract, self.catalogue = parsed.to_dict(), parsed.kit_catalogue()
        kit = install_document(self.contract, self.catalogue)
        _document, code = kit_manual.write_manual(self.cad, kit, COMPANY, meshes_for(kit))
        self.assertEqual(code, 0)
        self.report_path = self.cad / "manual" / "manual.json"
        self.report = json.loads(self.report_path.read_text())

    def made(self):
        manifest = build_artifact_manifest(self.run_root / PRODUCT, created_at="content-addressed")
        return types.SimpleNamespace(product_root=PRODUCT, cad_project_path="cad", product_manifest=manifest)

    def check(self, contract=None, catalogue=None):
        return verify_made_manual(self.run_root, self.made(), contract or self.contract,
                                  self.catalogue if catalogue is None else catalogue)

    def refused(self, **kwargs):
        with self.assertRaises(ContractError) as caught:
            self.check(**kwargs)
        return str(caught.exception)

    def rewrite(self, report):
        self.report_path.write_text(json.dumps(report))

    def test_the_written_manual_is_accepted(self):
        account = self.check()
        self.assertEqual(account["pdf"], "cad/manual/manual.pdf")
        self.assertEqual(account["pdf_sha256"], self.report["pdf"]["sha256"])
        self.assertEqual(account["sections"], 5)
        self.assertEqual(account["check_steps"], 1)
        self.assertEqual(account["not_printed"], 4)
        self.assertTrue(account["after_sales_confirmed"])
        json.dumps(account)

    def test_a_manual_that_does_not_list_the_bought_bodies_as_not_printed_is_refused(self):
        # Q29: the Manual names every Bought Part body as bought, not printed.
        self.rewrite({**self.report, "not_printed": self.report["not_printed"][1:]})
        self.assertIn("every Bought Part body as bought, not printed", self.refused())
        del self.report["not_printed"]
        self.rewrite(self.report)
        self.assertIn("every Bought Part body as bought, not printed", self.refused())

    def test_an_earlier_contract_checks_nothing(self):
        self.assertIsNone(verify_made_manual(self.run_root, self.made(), dict(self.contract, schema_version=6), None))
        self.assertIn("seals no kit_catalogue", self.refused(catalogue="x"))

    def test_a_missing_or_failed_manual_is_refused(self):
        self.report["passed"], self.report["failures"] = False, ["S03-hang-door has no instruction"]
        self.rewrite(self.report)
        self.assertIn("was not written: S03-hang-door has no instruction", self.refused())
        self.report_path.unlink()
        self.assertIn("lacks its kit Manual file manual/manual.json", self.refused())

    def test_a_manual_of_another_tree_is_refused(self):
        changed = json.loads(json.dumps(self.contract))
        changed["assembly_tree"]["steps"][0]["text"] = "Press the jar in."
        self.assertIn("another Assembly Tree", self.refused(contract=changed))

    def test_a_leaf_missing_or_listed_twice_is_refused(self):
        sections = self.report["sections"]
        sections[1]["materials"]["bought"].append({"id": "P02-jar", "count": 1})
        self.rewrite(self.report)
        self.assertIn("extra or repeated P02-jar", self.refused())
        sections[1]["materials"]["bought"].pop()
        sections[0]["materials"]["printed"].pop(0)
        self.rewrite(self.report)
        self.assertIn("missing B01-cabinet-carcass", self.refused())

    def test_a_step_or_check_step_left_out_is_refused(self):
        self.report["sections"][3]["steps"] = []
        self.rewrite(self.report)
        self.assertIn("every Assembly Step exactly once", self.refused())
        self.setUp()
        self.report["checks"] = []
        self.rewrite(self.report)
        self.assertIn("every Check Step first", self.refused())

    def test_a_pdf_that_is_not_the_named_one_is_refused(self):
        (self.cad / "manual" / "manual.pdf").write_bytes(b"%PDF-1.4 other")
        self.assertIn("not the one its report names", self.refused())
        made = self.made()
        (self.cad / "manual" / "manual.pdf").write_bytes(b"%PDF-1.4 changed again")
        with self.assertRaisesRegex(ContractError, "differs from the Made manifest"):
            verify_made_manual(self.run_root, made, self.contract, self.catalogue)

    def test_the_toy_archive_ships_the_manual_beside_the_models(self):
        from workshop.release.public_archive import _copy_made_tree

        written = {}
        made = self.made()
        made.cad_verification_path = "cad/measure/none.json"
        _copy_made_tree(lambda path, content: written.__setitem__(path, content), self.run_root, made)
        self.assertIn("make/manual/manual.pdf", written)
        self.assertIn("make/manual/manual.json", written)
        self.assertFalse(any(path.startswith("make/source/cad/manual/") for path in written))


class HostHelpersTest(unittest.TestCase):
    def test_the_accepted_manual_is_read_back_for_the_receipt(self):
        from workshop.workflow.native_run import _kit_manual_history

        with tempfile.TemporaryDirectory() as temporary:
            host = Path(temporary) / "host"
            self.assertEqual(_kit_manual_history(host), [])
            (host / "gates").mkdir(parents=True)
            manual = {"pdf": "cad/manual/manual.pdf", "pages": 9}
            (host / "gates" / "0002-make.json").write_text(
                json.dumps({"evidence": {"checks": {"kit_manual": [manual]}}}))
            self.assertEqual(_kit_manual_history(host), [manual])


class ReceiptManualTest(unittest.TestCase):
    def test_the_receipt_names_the_manual_and_an_unconfirmed_contact(self):
        from contextlib import redirect_stdout
        from io import StringIO

        from cli.main import _print_native_receipt
        from tests.cli.test_cli import native_receipt

        receipt = {**native_receipt(status="complete", stage="release"), "kit_manual": {
            "pdf": "cad/manual/manual.pdf", "pdf_sha256": "0" * 64, "pages": 9, "sections": 5,
            "check_steps": 1, "after_sales_confirmed": False}}
        stdout = StringIO()
        with redirect_stdout(stdout):
            _print_native_receipt(receipt, verb="wish")
        self.assertIn("Kit Manual: cad/manual/manual.pdf, 9 page(s), 5 section(s), 1 Check Step(s); "
                      "after-sales contact UNCONFIRMED", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
