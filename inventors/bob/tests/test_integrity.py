"""Tests for harness/integrity.py — the auditor of the frozen judge."""

import json
import os
import shutil
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from harness import integrity, ledger

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class IntegrityTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_home = os.environ.get("BOB_HOME")
        self._old_human = os.environ.pop("BOB_HUMAN", None)
        os.environ["BOB_HOME"] = self._tmp.name
        # The auditor hashes the pinned files under BOB_HOME; give the
        # temp home real copies so first-run baseline creation works.
        os.makedirs(os.path.join(self._tmp.name, "harness"))
        os.makedirs(os.path.join(self._tmp.name, "docs"))
        shutil.copy(os.path.join(REPO, "harness", "reward.py"),
                    os.path.join(self._tmp.name, "harness", "reward.py"))
        shutil.copy(os.path.join(REPO, "docs", "REWARD.md"),
                    os.path.join(self._tmp.name, "docs", "REWARD.md"))
        shutil.copy(os.path.join(REPO, "TASTE.md"),
                    os.path.join(self._tmp.name, "TASTE.md"))

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("BOB_HOME", None)
        else:
            os.environ["BOB_HOME"] = self._old_home
        if self._old_human is not None:
            os.environ["BOB_HUMAN"] = self._old_human
        else:
            os.environ.pop("BOB_HUMAN", None)
        self._tmp.cleanup()

    def _baseline_path(self):
        return os.path.join(self._tmp.name, "state", "REWARD_BASELINE.json")

    def _tamper_reward(self):
        with open(os.path.join(self._tmp.name, "harness", "reward.py"),
                  "a") as f:
            f.write("\nPUBLISH_THRESHOLD = 1.0  # muahaha\n")

    # --- (a) reward freeze -------------------------------------------------
    def test_first_audit_creates_baseline_and_is_clean(self):
        self.assertFalse(os.path.exists(self._baseline_path()))
        self.assertEqual(integrity.audit(), [])
        self.assertTrue(os.path.exists(self._baseline_path()))
        with open(self._baseline_path()) as f:
            baseline = json.load(f)
        self.assertIn("WARNING", baseline["warning"])
        self.assertIn("harness/reward.py", baseline["hashes"])
        self.assertIn("docs/REWARD.md", baseline["hashes"])

    def test_missing_baseline_mid_flight_is_violation_not_repin(self):
        # The seal deleted AFTER the factory has run (state/QUEUE.json
        # exists) is an attack signature — rm baseline + edit reward.py
        # must NOT get silently re-pinned as the new frozen judge.
        state_dir = os.path.join(self._tmp.name, "state")
        os.makedirs(state_dir, exist_ok=True)
        with open(os.path.join(state_dir, "QUEUE.json"), "w") as f:
            json.dump({"version": 2, "games": {}}, f)
        self._tamper_reward()
        violations = integrity.audit()
        self.assertTrue(
            any("baseline missing — a human must re-pin with BOB_HUMAN=1"
                in v for v in violations), violations)
        # And crucially: no baseline was created behind the human's back.
        self.assertFalse(os.path.exists(self._baseline_path()))

    def test_hash_drift_detected(self):
        integrity.audit()  # pin baseline
        self._tamper_reward()
        violations = integrity.audit()
        self.assertTrue(any("reward-freeze" in v and "harness/reward.py" in v
                            for v in violations), violations)

    def test_doc_drift_detected(self):
        integrity.audit()
        with open(os.path.join(self._tmp.name, "docs", "REWARD.md"), "a") as f:
            f.write("\nthreshold is now 10\n")
        violations = integrity.audit()
        self.assertTrue(any("docs/REWARD.md" in v for v in violations))

    def test_missing_pinned_file_is_violation(self):
        integrity.audit()
        os.remove(os.path.join(self._tmp.name, "harness", "reward.py"))
        violations = integrity.audit()
        self.assertTrue(any("MISSING" in v for v in violations), violations)

    def test_regenerate_baseline_requires_human(self):
        integrity.audit()
        self._tamper_reward()
        with self.assertRaises(PermissionError):
            integrity.regenerate_baseline()
        # Still dirty: the refusal must not have re-pinned anything.
        self.assertTrue(any("reward-freeze" in v for v in integrity.audit()))
        os.environ["BOB_HUMAN"] = "1"
        integrity.regenerate_baseline()
        self.assertEqual(integrity.audit(), [])

    # --- (b) improve allowlist ----------------------------------------------
    def test_allowlist_constants_exported(self):
        self.assertIn("harness/reward.py", integrity.FORBIDDEN)
        self.assertIn("harness/integrity.py", integrity.FORBIDDEN)
        self.assertIn("TASTE.md", integrity.FORBIDDEN)
        self.assertIn("knowledge/TASTE.md", integrity.FORBIDDEN)
        self.assertIn("state/**", integrity.FORBIDDEN)
        self.assertTrue(any("REWARD_BASELINE" in p for p in integrity.FORBIDDEN))
        self.assertIn("corpus/**", integrity.IMPROVE_MAY_WRITE)

    def test_improve_write_allowed(self):
        allowed = [".claude/agents/bob-ideator.md", "knowledge/lessons.md",
                   "corpus/cards/history-042.md", "corpus/DIRECTIONS.json",
                   "knowledge/PROPOSALS.md"]
        for p in allowed:
            self.assertTrue(integrity.improve_write_allowed(p), p)
        denied = ["harness/reward.py", "harness/integrity.py", "TASTE.md",
                  "knowledge/TASTE.md", "state/REWARD_BASELINE.json",
                  "state/BANDIT.json", "state/x/deep.json",
                  "knowledge/other.md", "bob.py", ".claude/agents/evil.py"]
        for p in denied:
            self.assertFalse(integrity.improve_write_allowed(p), p)

    def test_missing_root_taste_is_violation(self):
        os.remove(os.path.join(self._tmp.name, "TASTE.md"))
        violations = integrity.audit()
        self.assertTrue(
            any("taste-authority" in violation for violation in violations),
            violations,
        )

    def test_traversal_and_absolute_paths_denied(self):
        # 'corpus/../harness/reward.py' matched corpus/** by string
        # prefix before normalization lived inside the function.
        denied = [
            "corpus/../harness/reward.py",
            "corpus/../state/REWARD_BASELINE.json",
            "corpus/../harness/integrity.py",
            "corpus/../../outside/anything.md",
            "../knowledge/lessons.md",
            "/etc/passwd",
            "/corpus/cards/x.md",
            "~/corpus/cards/x.md",
            "~",
        ]
        for p in denied:
            self.assertFalse(integrity.improve_write_allowed(p), p)
        # Normalization must not deny legitimate corpus writes.
        self.assertTrue(integrity.improve_write_allowed("corpus/./cards/x.md"))
        self.assertTrue(
            integrity.improve_write_allowed("corpus/a/../cards/x.md"))

    def test_judge_prompts_forbidden_generator_prompts_writable(self):
        # Judge/gate prompts are part of the judge; the improver editing
        # its own scorer is the DGM receipt in prompt form.
        denied = [
            ".claude/agents/bob-novelty-judge.md",
            ".claude/agents/bob-triage-judge.md",
            ".claude/agents/bob-rules-lens.md",
            ".claude/agents/bob-build-lens.md",
            ".claude/agents/bob-fresh-reader.md",
            ".claude/agents/bob-table-player.md",
            ".claude/agents/bob-table-breaker.md",
        ]
        for p in denied:
            self.assertFalse(integrity.improve_write_allowed(p), p)
        # Generator prompts stay writable — the improver's whole job.
        for p in (".claude/agents/bob-ideator.md",
                  ".claude/agents/bob-builder.md",
                  ".claude/agents/bob-improver.md"):
            self.assertTrue(integrity.improve_write_allowed(p), p)

    # --- edition-lane pin ----------------------------------------------------
    def _write_directions(self, arms):
        path = os.path.join(self._tmp.name, "corpus", "DIRECTIONS.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"arms": arms}, f)

    def test_edition_arms_pinned_export(self):
        self.assertEqual(integrity.EDITION_ARMS, frozenset(["classic-reborn"]))

    def test_pinned_edition_arm_is_clean(self):
        self._write_directions({
            "classic-reborn": {"lane": "edition"},
            "gravity-physics": {"lane": "invention"},
            "wildcard": {},
        })
        self.assertFalse(
            any("edition-lane" in v for v in integrity.audit()))

    def test_rogue_edition_lane_is_violation(self):
        # An improver-writable corpus edit granting lane='edition' to an
        # invention arm skips the sim gates for every future game in it.
        self._write_directions({
            "classic-reborn": {"lane": "edition"},
            "gravity-physics": {"lane": "edition"},
        })
        violations = integrity.audit()
        self.assertTrue(
            any("edition-lane" in v and "gravity-physics" in v
                for v in violations), violations)

    # --- (c) heartbeat -------------------------------------------------------
    def _write_daybook(self, heartbeat):
        path = os.path.join(self._tmp.name, "state", "DAYBOOK.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({"heartbeat": heartbeat}, f)

    def test_stale_heartbeat_alarms(self):
        stale = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
        self._write_daybook(stale)
        violations = integrity.audit()
        self.assertTrue(any("heartbeat" in v for v in violations), violations)

    def test_fresh_heartbeat_clean(self):
        fresh = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        self._write_daybook(fresh)
        self.assertFalse(any("heartbeat" in v for v in integrity.audit()))

    def test_no_daybook_no_alarm(self):
        # Pre-first-tick install must not cry wolf.
        self.assertFalse(any("heartbeat" in v for v in integrity.audit()))

    # --- (d) sim-vs-human divergence -----------------------------------------
    def _seed_pairs(self, fun_tables, human_scores):
        for i, (ft, hs) in enumerate(zip(fun_tables, human_scores)):
            slug = "game-%d" % i
            ledger.append({"slug": slug, "kind": "publish",
                           "components": {"fun_table": ft}, "score": 70.0})
            ledger.append({"slug": slug, "kind": "human_table", "score": hs})

    def test_divergence_alarm_when_anticorrelated(self):
        self._seed_pairs([5, 10, 15, 20, 25], [90, 70, 50, 30, 10])
        violations = integrity.audit()
        self.assertTrue(any("divergence" in v for v in violations), violations)

    def test_no_alarm_when_correlated(self):
        self._seed_pairs([5, 10, 15, 20, 25], [30, 45, 60, 80, 95])
        self.assertFalse(any("divergence" in v for v in integrity.audit()))

    def test_no_alarm_below_min_n(self):
        # 4 pairs of pure noise: not enough evidence to accuse the judge.
        self._seed_pairs([5, 25, 10, 20], [90, 10, 80, 20])
        self.assertFalse(any("divergence" in v for v in integrity.audit()))

    def test_zero_variance_alarms(self):
        # A judge scoring every game identically is not judging.
        self._seed_pairs([15, 15, 15, 15, 15], [10, 30, 50, 70, 90])
        violations = integrity.audit()
        self.assertTrue(any("divergence" in v for v in violations), violations)

    # --- Pearson helper ---------------------------------------------------------
    def test_pearson(self):
        self.assertAlmostEqual(
            integrity._pearson([1, 2, 3], [2, 4, 6]), 1.0)
        self.assertAlmostEqual(
            integrity._pearson([1, 2, 3], [6, 4, 2]), -1.0)
        self.assertAlmostEqual(
            integrity._pearson([1, 2, 3, 4], [1, 3, 2, 4]), 0.8)
        self.assertIsNone(integrity._pearson([1, 1, 1], [1, 2, 3]))
        self.assertIsNone(integrity._pearson([1], [2]))


if __name__ == "__main__":
    unittest.main()
