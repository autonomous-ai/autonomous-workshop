"""ADR 0096: the host checks a seeded Make against its Approved Proof.

Contract: `verify_made_seed` returns no deviation for a Component whose
latest round is the approved B-rep and whose delivered STEP is within
proof_diff tolerance of the approved one; it returns a deviation (within or
over tolerance, locked by the approval or a Component Review) for any other
Component. It refuses a Component that was not made or has no latest round,
an "exact" seed lock whose identity is not the approved one, an approved
identity whose STEP is over tolerance, and a seed lock over tolerance; a
proof_diff that cannot run counts as over tolerance."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from workshop.errors import ContractError
from workshop.make.seed_check import verify_made_seed

APPROVED = {"body": {"identity": "A", "carry_key": "kA", "approved_step": "approved/part_body.step"}}


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

    def _verify(self, **compare):
        return verify_made_seed(self.project, self.run_root, APPROVED, compare=self._compare(**compare))

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
