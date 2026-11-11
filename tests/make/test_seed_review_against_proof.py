"""Workshop ADR 0102: a visible seed deviation is reviewed against the
Approved Proof, never against a Reference Image.

Contract:
- In a seeded run that froze the review (MAKE-OPTIONS schema 5), a component
  round the approval does not lock composes, at each Reference Camera, the
  Approved Proof's Component (its sealed approved STEP, placed by the
  approved source's ``assembly_pose``) beside the changed Component in its
  Display Pose. The packet has ``basis: "approved-proof"``, binds the
  approved STEP and renders by sha256, and binds no Reference Image; no
  reference image is composed. The print-stance sheet is unchanged.
- The review of such a packet answers ``matches_approved`` and lists each
  difference as ``{feature, approved, model}``; it records the basis and the
  packet hash. A camera mismatch, a Reference Conflict, a reference-shaped
  review, an agreeing review with ``matches_approved`` false and a
  disagreement without differences are refused. Shape Rounds count as before.
- A seeded run that did not freeze the review, and an unseeded run, keep the
  packet against the references.
- A missing or changed approved STEP leaves the round with a visual error,
  and a changed approved render makes the packet stale.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

from tests.make import test_make_round as make_round_tests

WORKER = ("--worker-nonce", "ab" * 16)
APPROVED_SOURCE = (
    "def gen_step():\n    return 'approved body'\n\n"
    "def assembly_pose(shape, pose):\n    return ('approved-pose', shape, pose)\n"
)
OVER = {"passed": False, "parts": [], "missing": [], "extra": []}
DIFFERS = [{"feature": "tail", "approved": "tail curls up to the ear", "model": "tail lies flat"}]


class ApprovedProofReviewTest(unittest.TestCase):
    _run_root = make_round_tests.SealedReferenceTest._run_root
    _fake_run = make_round_tests.SealedReferenceTest._fake_run
    _main = make_round_tests.SealedReferenceTest._main
    REFS = make_round_tests.ReferenceCameraRoundTest.REFS
    POSED = make_round_tests.ReferenceCameraRoundTest.POSED
    _contract = make_round_tests.ReferenceCameraRoundTest._contract

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = self._run_root(temporary.name, self.REFS, context=self._contract())
        self.run = self.project.parents[4]
        seed = self.run / "seed"
        (seed / "approved").mkdir(parents=True)
        (seed / "part_body.step.py").write_text(APPROVED_SOURCE)
        (seed / "approved/part_body.step").write_bytes(b"approved STEP bytes")
        self.approved = {"identity": "approved-identity", "carry_key": "kA", "contract_rows": "rows",
                         "approved_step": "approved/part_body.step",
                         "step_sha256": hashlib.sha256(b"approved STEP bytes").hexdigest()}
        self._edits = 0

    def _module(self, frozen=True):
        module = make_round_tests.load_module()
        module.seed_approval = lambda project: {"components": {"body": self.approved}}
        module.seed_diff = mock.Mock(return_value=OVER)
        module.seed_reviews_against_proof = lambda: frozen
        return module

    def _round(self, module, calls=None, edit=True):
        if edit:
            self._edits += 1
            (self.project / "part_body.step.py").write_text(self.POSED % self._edits)
        calls = [] if calls is None else calls
        code = self._main(module, self.project, ["--component", "part_body.step.py", *WORKER], calls)
        state = json.loads((self.project / "measure/component-rounds/body/make-round-state.json").read_text())
        summary = json.loads((self.project / ("measure/component-rounds/body/r%04d/summary.json"
                                              % state["round"])).read_text())
        return code, summary

    def _review(self, module, summary, **changes):
        review = {"round": summary["round"], "packet_sha256": summary["visual"]["packet_sha256"],
                  "reviewer": "fresh-reviewer-subagent", "agrees": True, "matches_plan": True,
                  "matches_approved": True, "reason": "Same shape as approved; the vent the gate needed.",
                  **changes}
        review = {key: value for key, value in review.items() if value is not None}
        path = self.project / "measure/review.json"
        path.write_text(json.dumps(review))
        return module.record_review(self.project, path, "part_body.step.py")

    def test_the_packet_compares_the_approved_component_and_shows_no_reference(self):
        module, calls = self._module(), []
        composed = []
        original = module.compose_comparison
        module.compose_comparison = lambda left, right, target, caption: (
            composed.append((Path(left), Path(right), caption)), original(left, right, target, caption))
        code, summary = self._round(module, calls)
        self.assertEqual((code, summary["phase"], summary["visual"]["status"]), (1, "awaiting-review", "pending"))
        renders = [c for c in calls if Path(c[1]).name == "render_review"]
        stance, posed, approved = renders
        # The print-stance sheet stays as it is.
        self.assertEqual(Path(stance[2]).name, "part_body.step.py")
        self.assertIn("--sheet", stance)
        self.assertEqual(Path(posed[2]).name, "display_pose_body.step.py")
        self.assertEqual(Path(approved[2]).name, "approved_pose_body.step.py")
        self.assertIn("--view=90,15", approved)
        self.assertEqual(Path(approved[approved.index("-o") + 1]).name, "approved-proof")
        out = Path(summary["out"])
        ((left, right, caption),) = composed
        self.assertEqual(left, out / "visual/approved-proof/az90_el15.png")
        self.assertEqual(right, out / "visual/display-pose/az90_el15.png")
        self.assertIn("approved Proof | changed Component", caption)
        packet = json.loads(Path(summary["visual"]["packet"]).read_text())
        self.assertEqual(packet["basis"], "approved-proof")
        self.assertEqual(packet["references"], {})
        self.assertEqual(packet["approved"]["step_sha256"], self.approved["step_sha256"])
        self.assertEqual(Path(packet["approved"]["source"]).name, "part_body.step.py")
        self.assertEqual([Path(p).name for p in packet["approved"]["renders"]], ["az90_el15.png"])
        self.assertEqual([item["label"] for item in packet["comparisons"].values()], ["geometry:body"])
        self.assertNotIn("wish-references", json.dumps(packet))
        self.assertIn("Approved Proof", summary["visual"]["detail"])

    def test_the_approved_entry_poses_the_sealed_step_with_the_approved_source(self):
        module, calls = self._module(), []
        self._round(module, calls)
        entry = Path([c for c in calls if Path(c[1]).name == "render_review"][2][2])
        fake = types.ModuleType("build123d")
        fake.import_step = lambda path: ("imported", Path(path).name)
        with mock.patch.dict(sys.modules, {"build123d": fake}):
            built = make_round_tests.runpy_entry(entry)["gen_step"]()
        self.assertEqual(built, ("approved-pose", ("imported", "part_body.step"), None))

    def test_an_agreeing_review_locks_and_records_its_basis(self):
        module = self._module()
        _, summary = self._round(module)
        summary = self._review(module, summary)
        self.assertTrue(summary["ok"])
        self.assertIsNotNone(summary["locked"])
        review = summary["review"]
        self.assertEqual((review["basis"], review["matches_approved"], review["matches_reference"]),
                         ("approved-proof", True, None))
        self.assertEqual(review["packet_sha256"], summary["visual"]["packet_sha256"])
        self.assertIn("judged against the Approved Proof", module.render_summary(summary))

    def test_a_disagreement_lists_differences_from_the_approved_render_and_counts_a_shape_round(self):
        module = self._module()
        _, summary = self._round(module)
        summary = self._review(module, summary, agrees=False, matches_approved=False,
                               reason="The tail changed.", differences=DIFFERS)
        self.assertFalse(summary["ok"])
        worker = json.loads((Path(summary["out"]) / "review.json").read_text())
        self.assertEqual(worker["differences"], DIFFERS)
        self.assertIn("differs tail: approved tail curls up", module.render_summary(summary))
        _, summary = self._round(module)
        self.assertEqual(summary["shape_rounds"], 1)

    def test_refused_reviews(self):
        cases = [
            ("camera mismatch or a Reference Conflict",
             dict(camera_mismatch={"file": "ref-02-body.png", "reference": "a", "model": "b"})),
            ("camera mismatch or a Reference Conflict",
             dict(reference_conflicts=[{"file": "ref-02-body.png", "reference": "a", "contract": "b"}])),
            ("matches_approved", dict(matches_approved=None, matches_reference=True)),
            ("matches_plan and matches_approved true", dict(matches_approved=False)),
            ("must list how the model differs from the Approved Proof", dict(agrees=False, matches_approved=False)),
            ("feature, approved and model",
             dict(agrees=False, matches_approved=False,
                  differences=[{"feature": "tail", "reference": "curled", "model": "flat"}])),
        ]
        module = self._module()
        _, summary = self._round(module)
        for fragment, changes in cases:
            with self.subTest(fragment), self.assertRaisesRegex(ValueError, fragment):
                self._review(module, summary, **changes)

    def test_a_run_that_did_not_freeze_the_review_keeps_the_reference_packet(self):
        module, calls = self._module(frozen=False), []
        _, summary = self._round(module, calls)
        packet = json.loads(Path(summary["visual"]["packet"]).read_text())
        self.assertNotIn("basis", packet)
        self.assertEqual([Path(p).name for p in packet["references"]], ["ref-02-body.png"])
        self.assertEqual(len([c for c in calls if Path(c[1]).name == "render_review"]), 2)

    def test_a_missing_or_changed_approved_step_is_a_visual_error(self):
        (self.run / "seed/approved/part_body.step").write_bytes(b"other bytes")
        module = self._module()
        _, summary = self._round(module)
        self.assertEqual(summary["visual"]["status"], "error")
        self.assertIn("approved STEP", summary["visual"]["detail"])

    def test_a_changed_approved_render_makes_the_packet_stale(self):
        module = self._module()
        _, summary = self._round(module)
        render = Path(summary["out"]) / "visual/approved-proof/az90_el15.png"
        render.write_bytes(make_round_tests.png(b"other"))
        with self.assertRaisesRegex(ValueError, "stale images"):
            self._review(module, summary)


if __name__ == "__main__":
    unittest.main()


class ContractImageReviewTest(ApprovedProofReviewTest):
    """ADR 0103: with a schema 4 seal the contract's own reference, sealed by
    the run as the approved Proof render, is the approved side. Nothing is
    rendered from the approved STEP in the run."""

    def _record(self, **changes):
        path = self.run / "wish-references/ref-02-body.png"
        return {"file": "ref-02-body.png", "kind": "reference", "shows": "geometry:body", "camera": [90, 15],
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), **changes}

    def _module(self, frozen=True, record=None):
        module = super()._module(frozen)
        images = [record if record is not None else self._record()]
        module.seed_approval = lambda project: {"components": {"body": self.approved}, "contract_images": images}
        return module

    def test_the_packet_shows_the_sealed_contract_reference_as_the_approved_side(self):
        module, calls = self._module(), []
        _, summary = self._round(module, calls)
        self.assertEqual(summary["visual"]["status"], "pending")
        renders = [c for c in calls if Path(c[1]).name == "render_review"]
        self.assertEqual([Path(c[2]).name for c in renders], ["part_body.step.py", "display_pose_body.step.py"])
        packet = json.loads(Path(summary["visual"]["packet"]).read_text())
        record = self._record()
        self.assertEqual((packet["basis"], packet["references"]), ("approved-proof", {}))
        self.assertEqual(packet["approved"]["contract_images"], {"ref-02-body.png": record["sha256"]})
        self.assertEqual(list(packet["approved"]["renders"].values()), [record["sha256"]])
        self.assertNotIn("step_sha256", packet["approved"])
        summary = self._review(module, summary)
        self.assertEqual(summary["review"]["basis"], "approved-proof")

    def test_a_reference_that_is_not_the_sealed_render_is_a_visual_error(self):
        for name, record in (("other bytes", self._record(sha256="9" * 64)),
                             ("no render of the Component", self._record(shows="geometry:lid"))):
            with self.subTest(name):
                module = self._module(record=record)
                _, summary = self._round(module)
                self.assertEqual(summary["visual"]["status"], "error")

    # The STEP-rendered approved side does not apply to a schema 4 seal.
    test_the_approved_entry_poses_the_sealed_step_with_the_approved_source = None
    test_a_missing_or_changed_approved_step_is_a_visual_error = None
    test_the_packet_compares_the_approved_component_and_shows_no_reference = None
