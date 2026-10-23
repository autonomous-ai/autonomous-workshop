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
from workshop.make.kit_tree import install_document, tree_digest, verify_made_tree
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
        }
        self.write("measure/tree-report.json", self.report)

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
            "report": "cad/measure/tree-report.json"})

    def test_the_host_and_the_run_local_tool_build_one_install(self):
        self.assertEqual(TOOL.install_document(self.contract, self.catalogue), self.install)
        self.assertEqual(TOOL.tree_digest(self.install), tree_digest(self.install))

    def test_an_earlier_schema_has_no_tree_to_check(self):
        self.assertIsNone(verify_made_tree(self.run_root, self.made(), {"schema_version": 6}, None))

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
