"""ADR 0092: before Make is accepted the host checks a schema 7 kit's
Assembly Tree gates on the exact sealed bytes, without rebuilding geometry."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import types
import unittest

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ContractError
from workshop.make.kit_tree import install_document, not_printed, tree_digest, verify_made_tree
from workshop.wish.design_contract import parse_design_contract
from tests.make.test_kit_tree import kit_tree as TOOL, sealed_block
from tests.wish.test_assembly_tree import _catalogues
from tests.wish.test_design_contract import _contract_text

PRODUCT = "artifacts/make/r0001/product"


class MadeKitTreeTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.cad = self.run_root / PRODUCT / "cad"
        (self.cad / "tree").mkdir(parents=True)
        (self.cad / "measure").mkdir()
        parsed = parse_design_contract(_contract_text(sealed_block()), catalogues=_catalogues())
        self.contract, self.catalogue = parsed.to_dict(), parsed.kit_catalogue()
        self.install = install_document(self.contract, self.catalogue)
        self.write("tree/kit.json", self.install)
        self.report = {
            "kind": "kit-tree-report", "scope": "final", "verdict": "PASS", "defects": [], "failures": [],
            "tree_sha256": tree_digest(self.install), "routes": [],
            "conditions": [{"id": "S07-furniture", "check": "assembly_sequence",
                            "inputs": {"steps": [{"id": "a"}, {"id": "b"}, {"id": "c"}]}}],
            "leaves": {"printed": ["A01-case-shell", "B01-cabinet-carcass", "B02-cabinet-door",
                                   "C01-desk-body", "D01-inkwell"],
                       "bought": ["P01-hinge-pin", "P02-jar", "P03-ball-led", "P04-battery-box"],
                       "pieces": ["M01-spine-strip", "M02-desk-book"]},
            "not_printed": TOOL.not_printed(TOOL.Plan(self.install)),
        }
        self.write("measure/tree-report.json", self.report)
        self.listed = TOOL.not_printed_document(self.install)
        self.write("measure/not-printed.json", self.listed)

    def write(self, relative, document):
        (self.cad / relative).write_text(json.dumps(document, indent=1, sort_keys=True) + "\n")

    def made(self):
        manifest = build_artifact_manifest(self.run_root / PRODUCT, created_at="content-addressed")
        return types.SimpleNamespace(product_root=PRODUCT, cad_project_path="cad", product_manifest=manifest)

    def check(self, contract=None, catalogue=None):
        return verify_made_tree(self.run_root, self.made(), contract or self.contract,
                                self.catalogue if catalogue is None else catalogue)

    def refused(self, **kwargs):
        with self.assertRaises(ContractError) as caught:
            self.check(**kwargs)
        return str(caught.exception)

    def test_a_passing_tree_is_accepted_and_counted(self):
        self.assertEqual(self.check(), {
            "printed_parts": 5, "bought_parts": 4, "print_pieces": 2,
            "insertions_across_components": 3, "lead_routes_across_components": 0,
            "report": "cad/measure/tree-report.json",
            "not_printed": {"path": "cad/measure/not-printed.json", "colour": "#ff00ff", "bodies": [
                {"body": "P01-hinge-pin#1", "bought": "steel-pin-1.5x29.5"},
                {"body": "P02-jar#1", "bought": "clear-jar-6x7"},
                {"body": "P03-ball-led#1", "bought": "led-3v-cool-white"},
                {"body": "P04-battery-box#1", "bought": "battery-box-2aa-switch"}]}})

    def test_the_host_and_the_run_local_tool_list_one_set_of_bought_bodies(self):
        self.assertEqual(not_printed(self.contract, self.catalogue), TOOL.not_printed(TOOL.Plan(self.install)))

    def test_a_missing_or_wrong_not_printed_list_is_refused(self):
        for change in ({"bodies": self.listed["bodies"][1:]}, {"colour": "#112233"},
                       {"tree_sha256": "0" * 64}):
            self.write("measure/not-printed.json", {**self.listed, **change})
            self.assertIn("not the sealed tree's list of Bought Part bodies", self.refused())
        self.write("measure/not-printed.json", self.listed)
        self.write("measure/tree-report.json", {**self.report, "not_printed": []})
        self.assertIn("not the sealed tree's list", self.refused())
        self.write("measure/tree-report.json", self.report)
        (self.cad / "measure" / "not-printed.json").unlink()
        self.assertIn("wrote no measure/not-printed.json", self.refused())

    def test_the_toy_archive_ships_the_not_printed_list_beside_the_models(self):
        from workshop.release.public_archive import _copy_made_tree

        (self.cad / "part_cabinet.step").write_text("ISO-10303-21;\n")
        written = {}
        made = self.made()
        made.cad_verification_path = "cad/measure/none.json"
        _copy_made_tree(lambda path, content: written.__setitem__(path, content), self.run_root, made)
        self.assertIn("make/models/cad/part_cabinet.step", written)
        listed = json.loads(written["make/models/cad/not-printed.json"])
        self.assertEqual(listed["bodies"][0]["bought"], "steel-pin-1.5x29.5")
        self.assertNotIn("make/verification/reports/not-printed.json", written)

    def test_the_receipt_lists_the_bodies_not_printed(self):
        from contextlib import redirect_stdout
        from io import StringIO

        from cli.main import _print_native_receipt
        from tests.cli.test_cli import native_receipt

        receipt = {**native_receipt(status="complete", stage="release"), "kit_tree": self.check()}
        stdout = StringIO()
        with redirect_stdout(stdout):
            _print_native_receipt(receipt, verb="wish")
        self.assertIn("Not printed (bought, #ff00ff in the STEP): P01-hinge-pin#1 (steel-pin-1.5x29.5), "
                      "P02-jar#1 (clear-jar-6x7)", stdout.getvalue())

    def test_the_host_and_the_run_local_tool_build_one_install(self):
        self.assertEqual(TOOL.install_document(self.contract, self.catalogue), self.install)
        self.assertEqual(TOOL.tree_digest(self.install), tree_digest(self.install))

    def test_an_earlier_schema_has_no_tree_to_check(self):
        self.assertIsNone(verify_made_tree(self.run_root, self.made(), {"schema_version": 6}, None))
        # ADR 0093: a schema 8 toy without a tree is no kit; a schema 8 kit is checked.
        self.assertIsNone(verify_made_tree(self.run_root, self.made(), {"schema_version": 8}, None))
        kit = dict(self.contract, schema_version=8)
        with self.assertRaisesRegex(Exception, "kit_catalogue"):
            verify_made_tree(self.run_root, self.made(), kit, None)

    def test_an_install_that_is_not_the_sealed_tree_is_refused(self):
        edited = copy.deepcopy(self.install)
        edited["catalogue"]["filaments"]["navy"]["hex"] = "#000000"
        self.write("tree/kit.json", edited)
        self.assertIn("not the sealed Design Contract's Assembly Tree", self.refused())
        (self.cad / "tree" / "kit.json").unlink()
        self.assertIn("lacks its installed Assembly Tree", self.refused())

    def test_a_missing_failed_or_partial_report_is_refused(self):
        self.assertIn("seals no kit_catalogue", self.refused(catalogue="none"))
        for change, needle in (
            ({"verdict": "FAIL", "failures": ["S07-furniture: blocked"]}, "did not pass: S07-furniture"),
            ({"verdict": "DEFECT", "defects": [{"detail": "no door"}]}, "did not pass: no door"),
            ({"scope": "assembly"}, "not a final kit tree report"),
            ({"tree_sha256": "0" * 64}, "another Assembly Tree"),
            ({"leaves": {"printed": [], "bought": [], "pieces": []}}, "every leaf"),
            ({"slips": [{"kind": "missing", "part": "B02-cabinet-door", "detail": "x"}]}, "labelling slip"),
        ):
            self.write("measure/tree-report.json", {**self.report, **change})
            self.assertIn(needle, self.refused())
        (self.cad / "measure" / "tree-report.json").unlink()
        self.assertIn("wrote no measure/tree-report.json", self.refused())

    def test_a_tree_defect_on_record_is_never_accepted(self):
        self.write("measure/tree-defects.json", {"tree_sha256": tree_digest(self.install),
                                                  "need": "Tree defect: missing B02-cabinet-door"})
        self.assertIn("missing B02-cabinet-door", self.refused())
        # One of an earlier tree, since amended, does not stop this one.
        self.write("measure/tree-defects.json", {"tree_sha256": "f" * 64, "need": "old"})
        self.assertIsNotNone(self.check())


if __name__ == "__main__":
    unittest.main()
