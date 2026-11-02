"""ADR 0096: a seeded run carries its assembly review from the Approved Proof.

Contract:
- `make_round --carry-assembly-review` composes `snap/SIGNATURE-REVIEW.json`
  schema 11 from the sealed `CRITIC.json` only when the critic agreed (or the
  owner approved its open lines) and every Component's latest round has a
  carry basis: the approved B-rep locked as exact, a change within
  `proof_diff` tolerance locked by the approval, or a change an agreeing
  in-run Component Review locked (the partial carry). When every basis is
  exact the assembly identity must be the approved one. It records each
  Component's basis, identity and round. It refuses an unlocked or
  disagreeing Component, a Component Acceptance, a critic that is not the sealed one, a critic
  that disagreed with no approved open lines, a deviation, a Component the
  approval does not hold, a missing snap image and a bad concept hash; it
  applies only in a seeded run, takes no round options and is root-only.
- `verify_project` accepts the schema 10 and 11 shapes, refuses a bad basis and refuses a wrong field set,
  identity, an unapproved disagreement and stale images.
- The finalizer binds it to the frozen seed and refuses it in an unseeded
  run, against another approval, after a deviation with no basis, against
  bases that are not the latest rounds', with edited verdicts or another
  concept.
- A carried review needs the motion judged by its own independent critic.
- The host check refuses a carried assembly review whose bases do not cover
  a deviation it measured: within tolerance needs `within-tolerance` or
  `component-review`, over tolerance needs `component-review`.
- Unseeded and frozen runs keep the blind review: schemas 8 and 9 are
  validated as before by the existing tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import runpy
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.make import test_make_round as make_round_tests
from tests.make import test_make_round_guard as guard_tests
from workshop.errors import ContractError
from workshop.make.make_round_guard import decide
from workshop.make.seed_check import verify_made_seed

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "src/workshop/make/skills/cad/scripts"
FINALIZER = ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"
CONCEPT = "c" * 64
IDENTITIES = {"body": "A" * 64, "lid": "B" * 64}


def _assembly(identities):
    return hashlib.sha256(json.dumps(identities, sort_keys=True).encode()).hexdigest()


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


class _SeededProject:
    """A seeded run root with a CAD project whose Components are approved."""

    def __init__(self, base: Path, *, verdict="agree", rows=None, open_lines=False):
        self.run = base / "run"
        self.project = self.run / "product/cad"
        (self.project / "snap").mkdir(parents=True)
        (self.project / "measure").mkdir()
        self.critic = {"schema_version": 1, "round": 3, "verdict": verdict, "compares": [],
                       "checklist": [], "close_looks": [],
                       "requirements": rows if rows is not None else [{"id": "R1", "verdict": "agree", "note": ""}]}
        seed = self.run / "seed"
        seed.mkdir()
        (seed / "CRITIC.json").write_text(json.dumps(self.critic), encoding="utf-8")
        self.approval = {
            "schema_version": 1, "assembly_identity": _assembly(IDENTITIES),
            "components": {role: {"identity": identity, "carry_key": "k" + role,
                                  "approved_step": "approved/part_%s.step" % role}
                           for role, identity in IDENTITIES.items()},
            "critic": {"sha256": hashlib.sha256((seed / "CRITIC.json").read_bytes()).hexdigest(),
                       "verdict": verdict, "open_lines_approved": open_lines},
        }
        self.write_approval()
        for role, identity in IDENTITIES.items():
            (self.project / ("part_%s.step.py" % role)).write_text("# part\n", encoding="utf-8")
            self.round(role, identity)
        (self.project / "snap/iso.png").write_bytes(b"iso")
        (self.project / "snap/signature.png").write_bytes(b"signature")
        scripts = self.run / ".agents/skills/cad/scripts"
        scripts.mkdir(parents=True)
        shutil.copyfile(SCRIPTS / "motion_policy.py", scripts / "motion_policy.py")

    def write_approval(self):
        path = self.run / "seed/APPROVAL.json"
        path.write_text(json.dumps(self.approval, indent=2, sort_keys=True), encoding="utf-8")
        self.approval_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        self.options(seeded=True)

    def options(self, *, seeded):
        options = {"schema_version": 2, "check_motion": False, "carry_unchanged": False}
        if seeded:
            options = {"schema_version": 3, "check_motion": False,
                       "seed": {"approval_sha256": self.approval_sha256, "manifest_sha256": "d" * 64}}
        (self.run / "MAKE-OPTIONS.json").write_text(json.dumps(options), encoding="utf-8")

    def round(self, role, identity, seed="exact", number=1):
        rounds = self.project / "measure/component-rounds" / role
        (rounds / ("r%04d" % number)).mkdir(parents=True, exist_ok=True)
        (rounds / "make-round-state.json").write_text(json.dumps({"round": number}), encoding="utf-8")
        review = {"agrees": True, "carried_from": "seed-approval", "seed": seed} if seed else None
        self.summary(role, number, {"identity": identity, "review": review})

    def reviewed(self, role, identity, number, *, agrees=True, accepted=False):
        """An in-run Component Review of a repaired Component (ADR 0077)."""
        summary = {"identity": identity, "checks_ok": True,
                   "review": {"reviewer": "agent-1", "agrees": agrees, "reason": "r", "round": number}}
        if accepted:
            summary["accepted"] = {"reviewer": "agent-1", "reason": "r", "shape_rounds": 5}
        self.summary(role, number, summary)

    def summary(self, role, number, summary):
        rounds = self.project / "measure/component-rounds" / role
        (rounds / ("r%04d" % number)).mkdir(parents=True, exist_ok=True)
        (rounds / "make-round-state.json").write_text(json.dumps({"round": number}), encoding="utf-8")
        (rounds / ("r%04d" % number) / "summary.json").write_text(json.dumps(summary), encoding="utf-8")

    def critic_bytes(self):
        return (self.run / "seed/CRITIC.json").read_bytes()


class CarryComposerTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.m = make_round_tests.load_module()

    def _compose(self, seeded):
        return self.m.assembly_carry_review(seeded.project, seeded.approval, seeded.approval_sha256,
                                            seeded.critic_bytes(), CONCEPT)

    def test_an_exact_seeded_assembly_carries_the_critic(self):
        seeded = _SeededProject(self.base)
        (seeded.project / "measure/thickness-body.md").write_text("t", encoding="utf-8")
        (seeded.project / "measure/overhang-body.md").write_text("o", encoding="utf-8")
        review = self._compose(seeded)
        self.assertEqual(review["schema_version"], 11)
        self.assertEqual(review["components"], {role: {"basis": "exact", "identity": identity, "round": 1}
                                                for role, identity in IDENTITIES.items()})
        self.assertEqual((review["carried_from"], review["reviewer"]), ("seed-approval", "the owner (Approved Proof)"))
        self.assertEqual(review["assembly_identity"], seeded.approval["assembly_identity"])
        self.assertEqual(review["approval_sha256"], seeded.approval_sha256)
        self.assertEqual(review["requirements"], [{"id": "R1", "verdict": "agree", "note": ""}])
        self.assertEqual(review["critic_round"], 3)
        self.assertEqual(sorted(review["print_gate_sha256s"]), ["measure/overhang-body.md", "measure/thickness-body.md"])
        self.assertEqual(review["iso_sha256"], hashlib.sha256(b"iso").hexdigest())

    def test_open_lines_the_owner_approved_carry(self):
        rows = [{"id": "R1", "verdict": "differences", "note": "tail 2 mm short"}]
        seeded = _SeededProject(self.base, verdict="differences", rows=rows, open_lines=True)
        review = self._compose(seeded)
        self.assertTrue(review["open_lines_approved"])
        self.assertEqual(review["requirements"], rows)

    def test_what_does_not_carry(self):
        def disagreed(seeded):
            seeded.approval["critic"]["open_lines_approved"] = False
            seeded.critic["verdict"] = "differences"
            (seeded.run / "seed/CRITIC.json").write_text(json.dumps(seeded.critic), encoding="utf-8")
            seeded.approval["critic"]["sha256"] = hashlib.sha256(seeded.critic_bytes()).hexdigest()

        def row_differs(seeded):
            seeded.critic["requirements"][0]["verdict"] = "differences"
            (seeded.run / "seed/CRITIC.json").write_text(json.dumps(seeded.critic), encoding="utf-8")
            seeded.approval["critic"]["sha256"] = hashlib.sha256(seeded.critic_bytes()).hexdigest()

        cases = {
            "not the critic the approval sealed": lambda s: s.approval["critic"].update(sha256="0" * 64),
            "did not agree": disagreed,
            "left a requirement with differences": row_differs,
            "lid's latest round is neither": lambda s: s.round("lid", "C" * 64, seed="exact"),
            "locked by the approval as exact": lambda s: s.round("lid", IDENTITIES["lid"], seed=None),
            "an agreeing Component": lambda s: s.reviewed("lid", "C" * 64, 2, agrees=False),
            "Component Review locked": lambda s: s.reviewed("lid", "C" * 64, 2, accepted=True),
            "Components are not the approved ones": lambda s: (s.project / "part_extra.step.py").write_text("x"),
            "assembly identity": lambda s: s.approval.update(assembly_identity="0" * 64),
            "snap/signature.png": lambda s: (s.project / "snap/signature.png").unlink(),
        }
        for fragment, change in cases.items():
            with self.subTest(fragment):
                seeded = _SeededProject(self.base / fragment.replace("/", "_"))
                change(seeded)
                with self.assertRaisesRegex(ValueError, fragment):
                    self._compose(seeded)
        seeded = _SeededProject(self.base / "concept")
        with self.assertRaisesRegex(ValueError, "concept hash"):
            self.m.assembly_carry_review(seeded.project, seeded.approval, seeded.approval_sha256,
                                         seeded.critic_bytes(), "nope")

    def test_a_partial_carry_records_each_changed_basis(self):
        # B1: the beaver's deadlock -- body repaired in-run under its own
        # Component Review, lid repaired within tolerance; the rest exact.
        seeded = _SeededProject(self.base)
        seeded.round("lid", "C" * 64, seed="within-tolerance", number=2)
        seeded.reviewed("body", "D" * 64, 3)
        review = self._compose(seeded)
        self.assertEqual(review["components"], {
            "body": {"basis": "component-review", "identity": "D" * 64, "round": 3},
            "lid": {"basis": "within-tolerance", "identity": "C" * 64, "round": 2}})
        self.assertEqual(review["assembly_identity"], _assembly({"body": "D" * 64, "lid": "C" * 64}))
        self.assertNotEqual(review["assembly_identity"], seeded.approval["assembly_identity"])
        # The assembly identity binds only an all-exact assembly to the approval.
        seeded.approval["assembly_identity"] = "0" * 64
        self.assertEqual(self._compose(seeded)["components"]["lid"]["basis"], "within-tolerance")

    def test_the_mode_takes_only_its_options_and_needs_a_seeded_run(self):
        project = self.base / "cad"
        project.mkdir()
        for extra in (["--component", "part_body.step.py"], ["--full"], []):
            with self.subTest(extra=extra), self.assertRaises(SystemExit):
                args = [str(project), "--carry-assembly-review", *extra]
                if extra:
                    args += ["--concept-sha256", CONCEPT]
                self.m.main(args)
        with self.assertRaises(SystemExit):
            self.m.main([str(project), "--concept-sha256", CONCEPT])
        self.assertEqual(self.m.main([str(project), "--carry-assembly-review", "--concept-sha256", CONCEPT]), 2)

    def test_only_the_root_carries(self):
        command = guard_tests.SCRIPT + " cad --carry-assembly-review --concept-sha256 " + CONCEPT
        self.assertIsNone(decide(guard_tests._event(command), issue=guard_tests._Issuer(), seeded=True))
        for agent_type in ("component-worker", "component-reviewer"):
            output = decide(guard_tests._event(command, agent_type), issue=guard_tests._Issuer(), seeded=True)
            self.assertEqual(guard_tests._decision(output), "deny")


class VerifierShapeTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.verifier = runpy.run_path(str(SCRIPTS / "verify_project"))
        self.project = self.verifier["_sc_project"](Path(temporary.name).resolve())
        self.path = self.project / self.verifier["SIGNATURE_REVIEW_RELATIVE"]

    def _review(self, **changes):
        review = {
            "schema_version": 10, "kind": "autonomous-workshop.signature-experience-review",
            "carried_from": "seed-approval", "reviewer": "the owner (Approved Proof)",
            "concept_sha256": CONCEPT, "approval_sha256": "a" * 64, "critic_sha256": "b" * 64,
            "assembly_identity": "e" * 64, "critic_round": 2, "critic_verdict": "agree",
            "open_lines_approved": False, "requirements": [{"id": "R1", "verdict": "agree", "note": ""}],
            "print_gate_sha256s": {},
            "iso_sha256": hashlib.sha256((self.project / "snap/iso.png").read_bytes()).hexdigest(),
            "signature_sha256": hashlib.sha256((self.project / "snap/signature.png").read_bytes()).hexdigest(),
        }
        review.update(changes)
        self.path.write_bytes(_canonical(review))

    def test_a_carried_review_passes_the_preflight(self):
        self._review()
        self.verifier["_required_signature_review"](self.project)
        self._review(schema_version=11, components={
            "body": {"basis": "component-review", "identity": "d" * 64, "round": 3},
            "lid": {"basis": "exact", "identity": "e" * 64, "round": 1}})
        self.verifier["_required_signature_review"](self.project)
        self._review(critic_verdict="differences", open_lines_approved=True,
                     requirements=[{"id": "R1", "verdict": "differences", "note": "open"}])
        self.verifier["_required_signature_review"](self.project)

    def test_refusals(self):
        cases = {
            "do not match schema 10": dict(blind_held_read="x"),
            "do not match schema 11": dict(schema_version=11),
            "identity is invalid": dict(carried_from="r0003"),
            "critic that agreed": dict(critic_verdict="differences"),
            "requirement with differences": dict(requirements=[{"id": "R1", "verdict": "differences", "note": ""}]),
            "stale for snap/iso.png": dict(iso_sha256="0" * 64),
            "approval_sha256 is invalid": dict(approval_sha256="nope"),
        }
        for fragment, changes in cases.items():
            with self.subTest(fragment):
                self._review(**changes)
                with self.assertRaisesRegex(ValueError, fragment):
                    self.verifier["_required_signature_review"](self.project)

    def test_schema_11_refuses_a_bad_basis(self):
        good = {"basis": "exact", "identity": "e" * 64, "round": 1}
        for name, entry in {"basis": dict(good, basis="owner-said-so"), "identity": dict(good, identity=""),
                            "round": dict(good, round=0), "fields": dict(good, extra=1)}.items():
            with self.subTest(name):
                self._review(schema_version=11, components={"body": entry})
                with self.assertRaises(ValueError):
                    self.verifier["_required_signature_review"](self.project)
        self._review(schema_version=11, components={})
        with self.assertRaises(ValueError):
            self.verifier["_required_signature_review"](self.project)


class FinalizerBindingTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        spec = importlib.util.spec_from_file_location("stage_proposal_seed_carry_test", FINALIZER)
        self.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.tool)
        self.m = make_round_tests.load_module()

    def _check(self, seeded, review=None, concept=CONCEPT, content=None):
        review = review if review is not None else self.m.assembly_carry_review(
            seeded.project, seeded.approval, seeded.approval_sha256, seeded.critic_bytes(), CONCEPT)
        content = content if content is not None else _canonical(review)
        (seeded.project / "snap/SIGNATURE-REVIEW.json").write_bytes(content)
        self.tool._validate_carried_signature_review(
            seeded.run, review=review, content=content,
            review_relative=self.tool.PurePosixPath("product/cad/snap/SIGNATURE-REVIEW.json"),
            concept_sha256=concept)

    def test_the_composed_review_binds_to_the_seed(self):
        self._check(_SeededProject(self.base / "ok"))

    def test_a_partial_carry_binds_to_the_seed(self):
        seeded = _SeededProject(self.base / "partial")
        seeded.round("lid", "C" * 64, seed="within-tolerance", number=2)
        seeded.reviewed("body", "D" * 64, 3)
        self._check(seeded)

    def test_refusals(self):
        def composed(seeded):
            return self.m.assembly_carry_review(seeded.project, seeded.approval, seeded.approval_sha256,
                                                seeded.critic_bytes(), CONCEPT)

        seeded = _SeededProject(self.base / "unseeded")
        review = composed(seeded)
        seeded.options(seeded=False)
        with self.assertRaisesRegex(self.tool.ProposalError, "was not seeded"):
            self._check(seeded, review)

        seeded = _SeededProject(self.base / "other-approval")
        review = composed(seeded)
        seeded.approval["date"] = "2026-11-02"
        seeded.write_approval()
        with self.assertRaisesRegex(self.tool.ProposalError, "approval MAKE-OPTIONS.json froze"):
            self._check(seeded, review)

        seeded = _SeededProject(self.base / "deviation")
        review = composed(seeded)
        seeded.round("lid", "C" * 64, seed="within-tolerance", number=2)
        with self.assertRaisesRegex(self.tool.ProposalError, "assembly identity|not the latest rounds"):
            self._check(seeded, review)

        seeded = _SeededProject(self.base / "unreviewed")
        review = composed(seeded)
        seeded.reviewed("lid", "C" * 64, 2, agrees=False)
        with self.assertRaisesRegex(self.tool.ProposalError, "lid deviates from the Approved Proof"):
            self._check(seeded, review)

        seeded = _SeededProject(self.base / "schema10")
        seeded.reviewed("lid", "C" * 64, 2)
        review = composed(seeded)
        review.pop("components")
        review["schema_version"] = 10
        with self.assertRaisesRegex(self.tool.ProposalError, "lid deviates from the Approved Proof"):
            self._check(seeded, review)

        seeded = _SeededProject(self.base / "bases")
        seeded.reviewed("lid", "C" * 64, 2)
        review = composed(seeded)
        review["components"]["lid"]["basis"] = "within-tolerance"
        with self.assertRaisesRegex(self.tool.ProposalError, "not the latest rounds"):
            self._check(seeded, review)

        seeded = _SeededProject(self.base / "edited")
        review = dict(composed(seeded), requirements=[])
        with self.assertRaisesRegex(self.tool.ProposalError, "not the sealed critic's verdict"):
            self._check(seeded, review)

        seeded = _SeededProject(self.base / "concept")
        with self.assertRaisesRegex(self.tool.ProposalError, "identity is invalid"):
            self._check(seeded, concept="f" * 64)

        seeded = _SeededProject(self.base / "pretty")
        review = composed(seeded)
        with self.assertRaisesRegex(self.tool.ProposalError, "canonical JSON"):
            self._check(seeded, review, content=json.dumps(review, indent=1).encode())


class MotionAndHostTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)

    def test_a_carried_review_needs_its_own_motion_critic(self):
        motion = runpy.run_path(str(SCRIPTS / "motion_presentation.py"))
        project = self.base / "cad"
        (project / "snap").mkdir(parents=True)
        evidence = b"{}"
        signature = {"carried_from": "seed-approval", "reviewer": "the owner (Approved Proof)",
                     "concept_sha256": CONCEPT}

        def review(reviewer, rounds=1):
            value = {"schema_version": 1, "evidence_sha256": hashlib.sha256(evidence).hexdigest(),
                     "concept_sha256": CONCEPT, "reviewer": reviewer, "review_rounds": rounds,
                     "blind_motion_read": "it rocks", "motion_matches_wish": True,
                     "simulation_not_physical_test": True}
            (project / "snap/MOTION-REVIEW.json").write_bytes(_canonical(value))

        review("motion critic")
        motion["_check_review"](project, signature, evidence)
        review("the owner (Approved Proof)")
        with self.assertRaisesRegex(ValueError, "independent critic"):
            motion["_check_review"](project, signature, evidence)
        # A blind signature review keeps its rule: the same critic and rounds.
        review("motion critic", rounds=2)
        with self.assertRaisesRegex(ValueError, "differs from the signature review"):
            motion["_check_review"](project, {"concept_sha256": CONCEPT, "reviewer": "motion critic",
                                              "review_rounds": 1}, evidence)

    def test_the_host_refuses_a_carried_review_after_a_deviation(self):
        run = self.base / "run"
        project = run / "artifacts/make/r0001/product/cad"
        rounds = project / "measure/component-rounds/body/r0001"
        rounds.mkdir(parents=True)
        (project / "snap").mkdir()
        (project / "part_body.step").write_bytes(b"made")
        (rounds.parent / "make-round-state.json").write_text(json.dumps({"round": 1}))
        (rounds / "summary.json").write_text(json.dumps(
            {"identity": "B", "review": {"carried_from": "seed-approval", "seed": "within-tolerance"}}))
        approved = {"body": {"identity": "A", "approved_step": "approved/part_body.step"}}

        def compare(approved_step, built):
            return {"passed": True, "parts": [], "missing": [], "extra": []}

        self.assertEqual(len(verify_made_seed(project, run, approved, compare=compare)), 1)
        signature = project / "snap/SIGNATURE-REVIEW.json"
        signature.write_text(json.dumps({"carried_from": "seed-approval"}))
        with self.assertRaisesRegex(ContractError, "carried from the Approved Proof, but body deviated"):
            verify_made_seed(project, run, approved, compare=compare)

        def carried(basis):
            signature.write_text(json.dumps({"schema_version": 11, "carried_from": "seed-approval",
                                             "components": {"body": {"basis": basis, "identity": "B",
                                                                     "round": 1}}}))

        for basis in ("within-tolerance", "component-review"):
            carried(basis)
            self.assertEqual(len(verify_made_seed(project, run, approved, compare=compare)), 1)
        carried("exact")
        with self.assertRaisesRegex(ContractError, "body deviated with no basis"):
            verify_made_seed(project, run, approved, compare=compare)

        # Over tolerance, only the Component's own review carries it.
        (rounds / "summary.json").write_text(json.dumps(
            {"identity": "B", "review": {"agrees": True, "reviewer": "agent-1", "round": 1}}))

        def over(approved_step, built):
            return {"passed": False, "parts": [], "missing": [], "extra": []}

        carried("within-tolerance")
        with self.assertRaisesRegex(ContractError, "body deviated with no basis"):
            verify_made_seed(project, run, approved, compare=over)
        carried("component-review")
        [deviation] = verify_made_seed(project, run, approved, compare=over)
        self.assertEqual((deviation["within_tolerance"], deviation["locked_by"]), (False, "component-review"))


if __name__ == "__main__":
    unittest.main()
