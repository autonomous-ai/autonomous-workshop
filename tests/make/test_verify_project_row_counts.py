"""ADR 0093 decision 6: a Design Contract has no row limits, so the final
verifier's signature-review preflight takes one entry per sealed row however
many there are. Night Charms Hall stopped on the old cap of 16, which refused
the 22 sealed rows the finalizer required. The 16 stays a guard on the rows
a Workshop Manager writes for itself, outside Contract Mode."""

from __future__ import annotations

import json
import runpy
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


class SignatureReviewRowCountTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.verifier = runpy.run_path(str(SCRIPTS / "verify_project"))
        self.project = self.verifier["_sc_project"](Path(temporary.name).resolve())
        self.path = self.project / self.verifier["SIGNATURE_REVIEW_RELATIVE"]

    def _write(self, review):
        self.path.write_text(json.dumps(review, sort_keys=True, separators=(",", ":")), encoding="utf-8")

    def _review(self, assembly, geometry, source="contract"):
        review = json.loads(self.path.read_text(encoding="utf-8"))
        review["critical_form_requirements"] = [
            {"requirement": "Assembly row %d." % index, "blind_evidence": "Seen %d." % index, "matches": True}
            for index in range(assembly)
        ]
        if source is None:
            return review
        review.update(schema_version=9, requirements_source=source, blind_rereads=[])
        if geometry:
            review["geometry_form_requirements"] = [
                {"requirement": "Part row %d." % index, "geometry": "cabinet", "blind_evidence": "Seen.",
                 "matches": True, "packet_sha256": "a" * 64, "view": "sheet"}
                for index in range(geometry)
            ]
            review["geometry_blind_reads"] = [
                {"geometry": "cabinet", "blind_read": "A cabinet.", "review_rounds": 1}]
        return review

    def test_a_contract_review_takes_more_than_sixteen_rows_of_each_scope(self):
        self._write(self._review(22, 30))
        self.verifier["_required_signature_review"](self.project)

    def test_a_manager_review_keeps_its_limit_of_sixteen(self):
        self._write(self._review(16, 0, source="manager"))
        self.verifier["_required_signature_review"](self.project)
        for source in ("manager", None):
            with self.subTest(source=source):
                self._write(self._review(17, 0, source=source))
                with self.assertRaisesRegex(ValueError, "enumerate critical form requirements"):
                    self.verifier["_required_signature_review"](self.project)

    def test_an_empty_list_still_refuses(self):
        for assembly, geometry, needle in ((0, 1, "critical form"), (1, 0, None)):
            review = self._review(assembly, geometry)
            if needle is None:
                review["geometry_form_requirements"] = []
                review["geometry_blind_reads"] = []
                needle = "geometry form requirements"
            self._write(review)
            with self.subTest(needle=needle), self.assertRaisesRegex(ValueError, needle):
                self.verifier["_required_signature_review"](self.project)


if __name__ == "__main__":
    unittest.main()
