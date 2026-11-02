"""ADR 0096 phase 3: a seeded run's component rounds are locked by the
owner's approval of the Proof, and only exact ones may be the root's.

Contract:
- `round_policy` with a `seed` locks a passing, never-reviewed Component
  that equals the approved one (identity and carry key), or whose
  proof_diff is within tolerance under the same rows, with
  `carried_from: "seed-approval"`. A failed round, a deviation over (or not
  measured against) tolerance, rows that differ and a Component a reviewer
  disagreed with are not locked by the seed. A Shared Helper change after a
  seed lock unlocks it as after any review. An unlocked seed-locked
  Component whose repair stays within tolerance under the same rows locks
  on the approval again; one over tolerance waits for its review.
- The guard hook issues the root of a seeded run a `--seed-nonce` for a
  component round, a worker a `--worker-nonce` as before, and denies the
  root of an unseeded run and a caller-supplied seed nonce.
- The host accepts a root round under a seed nonce only when it is exactly
  the approved Component, refuses a deviation, a reused seed nonce and a
  seed nonce in an unseeded run."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests.make import test_make_round as make_round_tests
from tests.make import test_make_round_guard as guard_tests
from tests.make import test_role_guard as role_tests
from workshop.errors import ContractError
from workshop.make.make_round_guard import decide
from workshop.make.role_guard import install_make_round_guard, verify_component_round_nonces

SEED = {"identity": "A", "carry_key": "kA", "contract_rows": "rows", "within": None}
ROOT_NONCE = "ef" * 16


class SeedPolicyTest(unittest.TestCase):
    def setUp(self):
        self.m = make_round_tests.load_module()

    def _round(self, previous=None, **new):
        values = {"identity": "A", "helpers": {"features/joints.py": "1"}, "checks_ok": True, "round": 1,
                  "carry_key": "kA", "contract_rows": "rows", "seed": dict(SEED)}
        values.update(new)
        return self.m.round_policy(previous or {"phase": self.m.OPEN}, values)

    def test_the_approved_component_is_locked_by_the_approval(self):
        outcome = self._round()
        self.assertEqual(outcome["state"]["phase"], self.m.LOCKED)
        carried = outcome["carried"]
        self.assertEqual((carried["carried_from"], carried["review"]["seed"]), ("seed-approval", "exact"))
        self.assertEqual(self.m.carried_label(carried), "the Approved Proof")
        # A rerun of the same B-rep carries the approval forward.
        again = self._round(outcome["state"], round=2)
        self.assertEqual(again["carried"]["carried_from"], "seed-approval")
        self.assertEqual(again["state"]["phase"], self.m.LOCKED)

    def test_a_deviation_within_tolerance_under_the_same_rows_is_locked_with_its_diff(self):
        diff = {"passed": True, "parts": []}
        outcome = self._round(identity="B", carry_key="kB", seed=dict(SEED, within=True, diff=diff))
        self.assertEqual(outcome["state"]["phase"], self.m.LOCKED)
        self.assertEqual(outcome["carried"]["review"]["seed"], "within-tolerance")
        self.assertEqual(outcome["carried"]["seed_diff"], diff)

    def test_what_the_seed_does_not_lock(self):
        cases = {
            "failed": dict(checks_ok=False),
            "over tolerance": dict(identity="B", carry_key="kB", seed=dict(SEED, within=False)),
            "not measured": dict(identity="B", carry_key="kB", seed=dict(SEED, within=None)),
            "rows differ": dict(identity="B", carry_key="kB", contract_rows="other",
                                seed=dict(SEED, within=True)),
            "carry key differs only in its rows": dict(carry_key="kA-rows"),
            "unseeded": dict(seed=None),
        }
        for name, new in cases.items():
            with self.subTest(name):
                outcome = self._round(**new)
                self.assertIsNone(outcome["carried"])
                self.assertIn(outcome["state"]["phase"], (self.m.OPEN, self.m.AWAITING))

    def test_a_reviewer_disagreement_is_not_overruled_by_the_seed(self):
        disagreed = {"phase": self.m.DISAGREED, "identity": "B", "round": 2, "shape_rounds": 0,
                     "reviewed": {"round": 2, "identity": "B", "carry_key": "kB", "agrees": False,
                                  "imported_helpers": {}}}
        outcome = self._round(disagreed, round=3)
        self.assertTrue(outcome["shape_round"])
        self.assertIsNone(outcome["carried"])
        self.assertEqual(outcome["state"]["phase"], self.m.AWAITING)

    def test_a_shared_helper_change_unlocks_a_seed_lock(self):
        locked = self._round()["state"]
        outcome = self._round(locked, identity="C", carry_key="kC", helpers={"features/joints.py": "2"},
                              round=2)
        self.assertTrue(outcome["admit"])
        self.assertEqual(outcome["unlocks"], [{"kind": "shared-helper", "paths": ["features/joints.py"]}])
        self.assertEqual(outcome["state"]["phase"], self.m.AWAITING)

    def test_an_unlocked_seed_component_repaired_within_tolerance_relocks_on_the_approval(self):
        # ADR 0096 pilot B1: a repair the assembly unlock admitted that stays
        # within proof_diff tolerance needs no Component Review.
        locked = self._round()["state"]
        unlocked = dict(locked, unlocks=[{"kind": "verification", "assembly_round": 4}])
        diff = {"passed": True, "parts": []}
        outcome = self._round(unlocked, identity="C", carry_key="kC", round=2,
                              seed=dict(SEED, within=True, diff=diff))
        self.assertTrue(outcome["admit"])
        self.assertFalse(outcome["shape_round"])
        self.assertEqual(outcome["state"]["phase"], self.m.LOCKED)
        self.assertEqual(outcome["state"]["unlocks"], [])
        self.assertEqual((outcome["carried"]["review"]["seed"], outcome["carried"]["seed_diff"]),
                         ("within-tolerance", diff))
        # Over tolerance, or a lock no approval made, it waits for its review.
        over = self._round(unlocked, identity="C", carry_key="kC", round=2, seed=dict(SEED, within=False))
        self.assertEqual((over["carried"], over["state"]["phase"]), (None, self.m.AWAITING))
        reviewed = dict(unlocked, reviewed=dict(locked["reviewed"], carried_from=None))
        review = self._round(reviewed, identity="C", carry_key="kC", round=2, seed=dict(SEED, within=True))
        self.assertEqual((review["carried"], review["state"]["phase"]), (None, self.m.AWAITING))

    def test_a_locked_seed_component_refuses_a_change(self):
        locked = self._round()["state"]
        refused = self._round(locked, identity="C", carry_key="kC", round=2)
        self.assertFalse(refused["admit"])
        self.assertIn("locked", refused["refusal"])

    def test_the_summary_names_the_approved_proof(self):
        review = {**self._round()["carried"]["review"], "carried_from": "seed-approval"}
        summary = {"round": 1, "scope": "component:body", "project": "p", "entry": "part_body.step.py",
                   "parts": ["body"], "changed": [], "checked": [], "out": "o", "checks_ok": True, "ok": True,
                   "build": {}, "print": {}, "visual": {"status": "carried", "findings": [], "detail": "x"},
                   "review": review}
        text = self.m.render_summary(summary)
        self.assertIn("review AGREES (carried from the Approved Proof) by the owner (Approved Proof)", text)


class SeedHookTest(unittest.TestCase):
    def test_the_root_of_a_seeded_run_gets_a_seed_nonce(self):
        issuer = guard_tests._Issuer()
        output = decide(guard_tests._event(guard_tests.COMPONENT), issue=issuer, seeded=True)
        self.assertEqual(guard_tests._decision(output), "allow")
        nonce = issuer.issued[0][0]
        self.assertEqual(issuer.issued, [(nonce, "part_wing.step.py", None)])
        self.assertIn("--seed-nonce %s cad --component" % nonce,
                      output["hookSpecificOutput"]["updatedInput"]["command"])

    def test_a_worker_still_gets_a_worker_nonce_and_others_are_denied(self):
        issuer = guard_tests._Issuer()
        output = decide(guard_tests._event(guard_tests.COMPONENT, "component-worker"), issue=issuer, seeded=True)
        self.assertIn("--worker-nonce", output["hookSpecificOutput"]["updatedInput"]["command"])
        for agent_type in ("rowan-vale", "component-reviewer"):
            output = decide(guard_tests._event(guard_tests.COMPONENT, agent_type), issue=guard_tests._Issuer(),
                            seeded=True)
            self.assertEqual(guard_tests._decision(output), "deny")
        output = decide(guard_tests._event(guard_tests.COMPONENT), issue=guard_tests._Issuer())
        self.assertEqual(guard_tests._decision(output), "deny")

    def test_a_caller_supplied_seed_nonce_is_refused(self):
        output = decide(guard_tests._event(guard_tests.COMPONENT + " --seed-nonce " + "0" * 32),
                        issue=guard_tests._Issuer(), seeded=True)
        self.assertEqual(guard_tests._decision(output), "deny")

    def test_seeded_run_reads_the_frozen_options(self):
        from workshop.make.make_round_guard import seeded_run

        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "WISH.json").write_text("{}")
            (root / "STAGE.json").write_text("{}")
            event = {"cwd": str(root)}
            self.assertFalse(seeded_run(event))
            (root / "MAKE-OPTIONS.json").write_text('{"schema_version":1,"check_motion":false}')
            self.assertFalse(seeded_run(event))
            (root / "MAKE-OPTIONS.json").write_text(json.dumps({"schema_version": 3, "check_motion": False,
                                                                 "seed": {"approval_sha256": "a" * 64}}))
            self.assertTrue(seeded_run(event))


class SeedNonceHostTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.host = root / "host"
        self.host.mkdir()
        install_make_round_guard(self.host)
        self.run_root = root / "run"
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)
        role_tests._issue(self.host, ROOT_NONCE, "part_wing.step.py", agent_type=None)
        self.components = {"wing": {"identity": "A", "carry_key": "kA"}}

    def _summary(self, round_index=1, **extra):
        values = {"identity": "A", "carry_key": "kA", "phase": "locked", "seed_nonce": ROOT_NONCE,
                  "review": {"agrees": True, "seed": "exact", "carried_from": "seed-approval"}}
        values.update(extra)
        return role_tests._summary(self.project, "wing", round_index, None, **values)

    def _verify(self, components="seeded"):
        verify_component_round_nonces(self.project, self.host, run_root=self.run_root,
                                      seed_components=self.components if components == "seeded" else components)

    def test_an_exact_root_round_is_accepted(self):
        self._summary()
        self._verify()

    def test_a_root_deviation_is_refused(self):
        for extra in ({"identity": "B"}, {"carry_key": "kB"}, {"phase": "awaiting-review"},
                      {"review": {"agrees": True, "seed": "within-tolerance", "carried_from": "seed-approval"}},
                      {"review": None}):
            with self.subTest(extra=sorted(extra)):
                self._summary(**extra)
                with self.assertRaisesRegex(ContractError, "not the Approved Proof's Component"):
                    self._verify()

    def test_a_reused_seed_nonce_is_refused(self):
        self._summary(1)
        self._summary(2)
        with self.assertRaisesRegex(ContractError, "reuses the seed nonce"):
            self._verify()

    def test_an_unseeded_run_refuses_a_root_round(self):
        self._summary()
        with self.assertRaisesRegex(ContractError, "not run by a component-worker"):
            self._verify(components=None)

    def test_a_seed_nonce_for_another_component_is_refused(self):
        role_tests._issue(self.host, "12" * 16, "part_tail.step.py", agent_type=None)
        self._summary(seed_nonce="12" * 16)
        with self.assertRaisesRegex(ContractError, "not run by a component-worker"):
            self._verify()


if __name__ == "__main__":
    unittest.main()


class SeededComponentRoundTest(unittest.TestCase):
    """A component round in a run whose seed approval make_round reads."""

    _run_root = make_round_tests.SealedReferenceTest._run_root
    _fake_run = make_round_tests.SealedReferenceTest._fake_run
    _main = make_round_tests.SealedReferenceTest._main
    _contract_root = make_round_tests.ContractComponentReviewTest._contract_root
    _component = make_round_tests.ContractComponentReviewTest._component
    REFS = make_round_tests.ContractComponentReviewTest.REFS
    CONTRACT = make_round_tests.ContractComponentReviewTest.CONTRACT

    def _approved(self):
        """The identity, carry key and rows of the first build, from an unseeded project."""
        with tempfile.TemporaryDirectory() as tmp:
            self._edits = 0
            _, summary = self._component(make_round_tests.load_module(), self._contract_root(tmp), [])
        self._edits = 0
        return {"identity": summary["identity"], "carry_key": summary["carry_key"],
                "contract_rows": summary["contract_rows"], "approved_step": "approved/part_body.step"}

    def _seeded(self, approved, diff=None):
        from unittest import mock

        module = make_round_tests.load_module()
        module.seed_approval = lambda project: {"components": {"body": approved}}
        if diff is not None:
            module.seed_diff = mock.Mock(return_value=diff)
        return module

    def test_the_approved_component_is_locked_without_a_review(self):
        approved = self._approved()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module = self._seeded(approved)
            code, summary = self._component(module, project, [], extra=("--seed-nonce", ROOT_NONCE))
            self.assertEqual(code, 0)
            self.assertEqual((summary["phase"], summary["ok"], summary["visual"]["status"]),
                             ("locked", True, "carried"))
            self.assertEqual((summary["review"]["carried_from"], summary["review"]["seed"]), ("seed-approval", "exact"))
            self.assertEqual(summary["seed"], {"identity": approved["identity"], "exact": True, "within": None})
            self.assertEqual(summary["seed_nonce"], ROOT_NONCE)
            self.assertIn("Approved Proof", module.render_summary(summary))

    def test_a_root_deviation_is_refused_and_leaves_nothing(self):
        approved = self._approved()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            self._edits = 5  # another source: another B-rep
            module = self._seeded(approved, diff={"passed": True, "parts": [], "missing": [], "extra": []})
            code = self._main(module, project, ["--component", "part_body.step.py", "--seed-nonce", ROOT_NONCE],
                              [], None)
            self.assertEqual(code, 2)
            self.assertIn("component-worker's round", self.stderr)
            self.assertFalse((project / "measure/component-rounds/body/r0001").exists())
            self.assertFalse((project / "measure/component-rounds/body/make-round-state.json").exists())

    def test_a_worker_deviation_within_tolerance_is_locked_with_its_diff(self):
        approved = self._approved()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            self._edits = 5
            diff = {"passed": True, "parts": [], "missing": [], "extra": []}
            module = self._seeded(approved, diff=diff)
            code, summary = self._component(module, project, [], extra=("--worker-nonce", "ab" * 16))
            self.assertEqual((code, summary["phase"]), (0, "locked"))
            self.assertEqual(summary["review"]["seed"], "within-tolerance")
            self.assertEqual(summary["seed"]["diff"], diff)

    def test_a_worker_deviation_over_tolerance_awaits_its_review(self):
        approved = self._approved()
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            self._edits = 5
            module = self._seeded(approved, diff={"passed": False, "parts": [], "missing": [], "extra": []})
            code, summary = self._component(module, project, [], extra=("--worker-nonce", "ab" * 16))
            self.assertEqual((code, summary["phase"], summary["review"]), (1, "awaiting-review", None))
            self.assertIs(summary["seed"]["within"], False)
            self.assertEqual(summary["visual"]["status"], "pending")

    def test_a_seed_nonce_outside_a_seeded_run_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module = make_round_tests.load_module()
            code = self._main(module, project, ["--component", "part_body.step.py", "--seed-nonce", ROOT_NONCE],
                              [], None)
            self.assertEqual(code, 2)
            self.assertIn("only in a seeded run", self.stderr)
