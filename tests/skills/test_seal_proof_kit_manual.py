"""ADR 0104 decision 5: an Approved Proof may seal the kit Manual the owner
approved.

Contract: ``seal_proof.py seal --kit-manual PDF`` copies the PDF to
``approved/kit-manual.pdf``, into the seed manifest, and records
``kit_manual: {file, sha256}``; it refuses a non-kit contract, a file that
is no PDF, and a re-seal that would drop a sealed Manual. ``validate_seed``
returns the record and refuses one that is not the sealed file or belongs to
no kit."""

from __future__ import annotations

import json
import unittest

from tests.skills import test_seal_proof as seal_tests
from workshop.errors import ContractError
from workshop.wish.seed import manifest_sha256, validate_seed

PDF = b"%PDF-1.7\nowner-approved manual\n%%EOF\n"
KIT = {"assembly_tree": {"parts": [], "steps": []}}


class KitManualSealTest(unittest.TestCase):
    setUp = seal_tests.SealProofTest.setUp
    _record = seal_tests.SealProofTest._record
    _seal = seal_tests.SealProofTest._seal

    def seal_with(self, content=PDF, kit=True):
        self.design_contract = dict(KIT) if kit else {}
        manual = self.design / "MANUAL.pdf"
        manual.write_bytes(content)
        return self._seal("--kit-manual", str(manual))

    def approval(self):
        return json.loads((self.proof / "APPROVAL.json").read_text())

    def test_the_owner_approved_manual_is_sealed_and_validates(self):
        self.assertEqual(self.seal_with(), 0, self.stderr)
        approval = self.approval()
        digest = seal_tests.sha(self.proof / "approved/kit-manual.pdf")
        self.assertEqual(approval["kit_manual"], {"file": "approved/kit-manual.pdf", "sha256": digest})
        self.assertEqual(approval["manifest"]["approved/kit-manual.pdf"], digest)
        self.assertEqual((self.proof / "approved/kit-manual.pdf").read_bytes(), PDF)
        seed = validate_seed(self.proof, ("body",), seal_tests.sha(self.contract), KIT)
        self.assertEqual(seed.kit_manual, approval["kit_manual"])

    def test_a_seal_without_one_records_none(self):
        self.assertEqual(self._seal(), 0, self.stderr)
        self.assertNotIn("kit_manual", self.approval())
        self.assertIsNone(validate_seed(self.proof, ("body",), seal_tests.sha(self.contract)).kit_manual)

    def test_a_non_kit_and_a_non_pdf_are_refused(self):
        self.assertEqual(self.seal_with(kit=False), 1)
        self.assertIn("is for a kit", self.stderr)
        self.assertEqual(self.seal_with(content=b"<html>"), 1)
        self.assertIn("is not a PDF", self.stderr)
        self.assertFalse((self.proof / "approved/kit-manual.pdf").exists())

    def test_a_reseal_keeps_the_manual_only_when_given_again(self):
        self.assertEqual(self.seal_with(), 0, self.stderr)
        self.assertEqual(self._seal(), 1)
        self.assertIn("pass --kit-manual", self.stderr)
        self.assertEqual(self.approval()["kit_manual"]["file"], "approved/kit-manual.pdf")
        self.assertEqual(self.seal_with(), 0, self.stderr)

    def test_validate_seed_refuses_a_manual_that_is_not_the_sealed_one(self):
        self.assertEqual(self.seal_with(), 0, self.stderr)
        path = self.proof / "APPROVAL.json"
        good = self.approval()
        cases = {
            "another hash": (lambda a: a["kit_manual"].update(sha256="0" * 64), KIT, "not the sealed"),
            "another file": (lambda a: a["kit_manual"].update(file="approved/part_body.step"), KIT,
                             "not the sealed"),
            "extra keys": (lambda a: a["kit_manual"].update(pages=4), KIT, "is not {file, sha256}"),
            "no kit": (lambda a: None, {}, "contract is no kit"),
        }
        for label, (change, contract, words) in cases.items():
            with self.subTest(label):
                approval = json.loads(json.dumps(good))
                change(approval)
                approval["manifest_sha256"] = manifest_sha256(approval["manifest"])
                path.write_text(json.dumps(approval))
                with self.assertRaises(ContractError) as caught:
                    validate_seed(self.proof, ("body",), seal_tests.sha(self.contract), contract)
                self.assertIn(words, str(caught.exception))


if __name__ == "__main__":
    unittest.main()
