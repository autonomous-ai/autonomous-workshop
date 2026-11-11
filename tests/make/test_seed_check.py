"""ADR 0096: the host checks a seeded Make against its Approved Proof.

Contract: `verify_made_seed` returns no deviation for a Component whose
latest round is the approved B-rep and whose delivered STEP is within
proof_diff tolerance of the approved one; it returns a deviation (within or
over tolerance, locked by the approval or a Component Review) for any other
Component. It refuses a Component that was not made or has no latest round,
an "exact" seed lock whose identity is not the approved one, an approved
identity whose STEP is over tolerance, and a seed lock over tolerance; a
proof_diff that cannot run counts as over tolerance.

ADR 0102: with ``review_basis="approved-proof"`` a deviation locked by a
Component Review needs a review with that basis whose packet, read from its
round by sha256, compares with the sealed approved STEP and binds no
Reference Image; a review against the references is refused. Without it the
earlier review stands."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.make.seed_check import verify_made_seed

APPROVED = {"body": {"identity": "A", "carry_key": "kA", "approved_step": "approved/part_body.step",
                    "step_sha256": "5" * 64}}


class SeedCheckTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name)
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)
        (self.project / "part_body.step").write_bytes(b"made")
        self.calls = []

    def _round(self, identity="A", review=None):
        root = self.project / "measure/component-rounds/body"
        (root / "r0001").mkdir(parents=True, exist_ok=True)
        (root / "make-round-state.json").write_text(json.dumps({"round": 1}))
        (root / "r0001/summary.json").write_text(json.dumps({"identity": identity, "review": review}))

    def _compare(self, passed=True, error=None):
        def compare(approved, built):
            self.calls.append((approved, built))
            if error is not None:
                raise error
            return {"passed": passed, "parts": [{"part": "body", "passed": passed, "volume_delta": 0.002,
                                                 "bbox_side_delta_mm": 0.01, "two_way": 0.003,
                                                 "surface_deviation_mm": 0.02, "reasons": []}],
                    "missing": [], "extra": []}
        return compare

    def _verify(self, review_basis=None, **compare):
        return verify_made_seed(self.project, self.run_root, APPROVED, compare=self._compare(**compare),
                                review_basis=review_basis)

    def _packet(self, round_index=1, **changes):
        """A reviewed round's visual packet; its sha256."""
        packet = {"schema_version": 3, "sources": {}, "images": {}, "references": {},
                  "comparisons": {"/x/compare-00.png": {"label": "geometry:body", "sha256": "1" * 64}},
                  "basis": "approved-proof",
                  "approved": {"step": "/run/seed/approved/part_body.step", "step_sha256": "5" * 64,
                               "source": "/run/seed/part_body.step.py", "source_sha256": "6" * 64,
                               "renders": {}}}
        packet.update(changes)
        content = json.dumps(packet).encode()
        path = self.project / ("measure/component-rounds/body/r%04d/visual-packet.json" % round_index)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return hashlib.sha256(content).hexdigest()

    def _proof_review(self, digest, **changes):
        return {"agrees": True, "reviewer": "abc", "basis": "approved-proof", "round": 1,
                "packet_sha256": digest, "matches_approved": True, **changes}

    def test_a_deviation_reviewed_against_the_approved_proof_is_accepted(self):
        self._round(identity="C", review=self._proof_review(self._packet()))
        (deviation,) = self._verify(review_basis="approved-proof", passed=False)
        self.assertEqual((deviation["within_tolerance"], deviation["locked_by"]), (False, "component-review"))
        # A review carried to a later rerun reads the packet of the round it judged.
        self._round(identity="C", review=dict(self._proof_review(self._packet()), carried_from=1))
        self.assertEqual(len(self._verify(review_basis="approved-proof", passed=False)), 1)

    def test_a_review_not_against_the_approved_proof_is_refused(self):
        # Each case writes its own packet when it runs.
        cases = [
            ("not taken against the Approved Proof", lambda: {
                "agrees": True, "reviewer": "abc", "round": 1, "packet_sha256": self._packet(),
                "matches_reference": True}),
            ("names no round and packet", lambda: self._proof_review(self._packet(), round=None)),
            ("judged changed", lambda: self._proof_review((self._packet(), "0" * 64)[1])),
            ("does not compare it with the Approved Proof", lambda: self._proof_review(self._packet(basis=None))),
            ("does not compare it with the Approved Proof",
             lambda: self._proof_review(self._packet(comparisons={}))),
            ("shows a Reference Image", lambda: self._proof_review(
                self._packet(references={"/run/wish-references/ref-02-body.png": "2" * 64}))),
            ("not of the sealed approved STEP",
             lambda: self._proof_review(self._packet(approved={"step_sha256": "9" * 64}))),
            ("judged is missing", lambda: self._proof_review(self._packet(), round=7)),
        ]
        for fragment, review in cases:
            with self.subTest(fragment):
                self._round(identity="C", review=review())
                with self.assertRaisesRegex(ContractError, fragment):
                    self._verify(review_basis="approved-proof", passed=False)
        # A within-tolerance deviation locked by a review needs the basis too.
        self._round(identity="C", review=cases[0][1]())
        with self.assertRaisesRegex(ContractError, "not taken against the Approved Proof"):
            self._verify(review_basis="approved-proof", passed=True)

    def test_a_run_seeded_before_adr_0102_keeps_its_review_against_references(self):
        self._round(identity="C", review={"agrees": True, "reviewer": "abc", "matches_reference": True})
        self.assertEqual(len(self._verify(passed=False)), 1)
        # A seed lock within tolerance needs no review in either run.
        self._round(identity="B", review=self._seed("within-tolerance"))
        self.assertEqual(len(self._verify(review_basis="approved-proof")), 1)
        with self.assertRaisesRegex(ContractError, "unknown review basis"):
            self._verify(review_basis="references")

    def _seed(self, how):
        return {"agrees": True, "seed": how, "carried_from": "seed-approval"}

    def test_the_approved_component_has_no_deviation(self):
        self._round(review=self._seed("exact"))
        self.assertEqual(self._verify(), [])
        self.assertEqual(self.calls, [(self.run_root / "seed/approved/part_body.step",
                                       self.project / "part_body.step")])

    def test_deviations_are_returned(self):
        self._round(identity="B", review=self._seed("within-tolerance"))
        (deviation,) = self._verify()
        self.assertEqual((deviation["component"], deviation["within_tolerance"], deviation["locked_by"]),
                         ("body", True, "seed-approval"))
        self.assertEqual(deviation["parts"][0]["volume_delta"], 0.002)
        self.assertNotIn("reasons", deviation["parts"][0])
        self._round(identity="C", review={"agrees": True, "reviewer": "abc"})
        (deviation,) = self._verify(passed=False)
        self.assertEqual((deviation["within_tolerance"], deviation["locked_by"]), (False, "component-review"))

    def test_refusals(self):
        cases = [
            ("identity is not the approved one", dict(identity="B", review=self._seed("exact")), {}),
            ("though its round reports the approved B-rep", dict(review=None), dict(passed=False)),
            ("without its Component Review", dict(identity="B", review=self._seed("within-tolerance")),
             dict(passed=False)),
            ("without its Component Review", dict(identity="B", review=self._seed("within-tolerance")),
             dict(error=RuntimeError("no OCP"))),
        ]
        for fragment, round_values, compare in cases:
            with self.subTest(fragment):
                self._round(**round_values)
                with self.assertRaisesRegex(ContractError, fragment):
                    self._verify(**compare)

    def test_a_comparison_that_could_not_run_is_named(self):
        """Issue #231: the approved Component's STEP compared in a host that
        cannot import the CAD kernel; the refusal names that, not a shape."""
        self._round(review=self._seed("exact"))
        error = ImportError("pyexpat: undefined symbol XML_SetAllocTrackerActivationThreshold")
        with self.assertRaisesRegex(ContractError, r"could not compare them \(ImportError: pyexpat"):
            self._verify(error=error)
        self._round(identity="B", review=self._seed("within-tolerance"))
        with self.assertRaisesRegex(ContractError, r"Component Review; the host could not compare"):
            self._verify(error=error)
        with self.assertRaises(ContractError) as refused:
            self._verify(passed=False)
        self.assertNotIn("could not compare", str(refused.exception))

    def test_an_unmade_or_unrounded_component_is_refused(self):
        with self.assertRaisesRegex(ContractError, "no readable latest component round"):
            self._verify()
        (self.project / "part_body.step").unlink()
        with self.assertRaisesRegex(ContractError, "was not made"):
            self._verify()

    def test_an_unmeasured_reviewed_deviation_is_recorded_over_tolerance(self):
        self._round(identity="B", review={"agrees": True, "reviewer": "abc"})
        (deviation,) = self._verify(error=RuntimeError("no OCP"))
        self.assertFalse(deviation["within_tolerance"])
        self.assertIn("no OCP", deviation["error"])


if __name__ == "__main__":
    unittest.main()
