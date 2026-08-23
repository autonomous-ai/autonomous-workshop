"""Tests for harness/bandit.py — Thompson sampling with weekly discount."""

import json
import os
import random
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone

from harness import bandit

DIRECTIONS = {
    "comment": "test fixture",
    "arms": {
        "gravity-physics": {"hook": "physics referees"},
        "classic-reborn": {
            "hook": "editions of classics",
            "prior_note": ("Seed this arm's Beta prior at alpha=3,beta=2 "
                           "(2 real sales before Bob existed)."),
            "lane": "edition",
        },
        "wildcard": {"hook": "exploration reserve",
                     "prior_note": "Always present; never removed."},
    },
}


class BanditTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_home = os.environ.get("BOB_HOME")
        os.environ["BOB_HOME"] = self._tmp.name
        self._write_directions(DIRECTIONS)

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("BOB_HOME", None)
        else:
            os.environ["BOB_HOME"] = self._old_home
        self._tmp.cleanup()

    def _write_directions(self, data):
        path = os.path.join(self._tmp.name, "corpus", "DIRECTIONS.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f)

    def _state_path(self):
        return os.path.join(self._tmp.name, "state", "BANDIT.json")

    # --- prior seeding ---------------------------------------------------
    def test_prior_seeding_from_prior_note(self):
        arms = bandit.arms()
        # classic-reborn carries the 2-sales receipt: Beta(3,2).
        self.assertAlmostEqual(arms["classic-reborn"]["alpha"], 3.0)
        self.assertAlmostEqual(arms["classic-reborn"]["beta"], 2.0)
        # everything else starts uninformative.
        self.assertAlmostEqual(arms["gravity-physics"]["alpha"], 1.0)
        self.assertAlmostEqual(arms["gravity-physics"]["beta"], 1.0)
        self.assertAlmostEqual(arms["wildcard"]["alpha"], 1.0)

    def test_corpus_edit_never_resets_posterior(self):
        bandit.update("gravity-physics", 1.0)
        before = bandit.arms()["gravity-physics"]["alpha"]
        self._write_directions(DIRECTIONS)  # corpus rewritten
        after = bandit.arms()["gravity-physics"]["alpha"]
        self.assertAlmostEqual(before, after, places=3)

    # --- wildcard guarantee ------------------------------------------------
    def test_wildcard_present_even_without_directions_file(self):
        os.remove(os.path.join(self._tmp.name, "corpus", "DIRECTIONS.json"))
        arms = bandit.arms()
        self.assertIn("wildcard", arms)
        self.assertEqual(bandit.pick(), "wildcard")  # only arm left

    def test_wildcard_added_if_corpus_omits_it(self):
        self._write_directions({"arms": {"gravity-physics": {}}})
        self.assertIn("wildcard", bandit.arms())

    # --- discount math -----------------------------------------------------
    def test_two_week_discount(self):
        # Beta(3,2) two weeks stale: evidence above the (1,1) floor
        # decays by 0.9^2 = 0.81 -> effective (2.62, 1.81).
        two_weeks_ago = (datetime.now(timezone.utc)
                         - timedelta(weeks=2)).isoformat()
        os.makedirs(os.path.dirname(self._state_path()), exist_ok=True)
        with open(self._state_path(), "w") as f:
            json.dump({"arms": {"classic-reborn": {
                "alpha": 3.0, "beta": 2.0, "pulls": 0,
                "reward_sum": 0.0, "last": two_weeks_ago}},
                "total_pulls": 0}, f)
        arm = bandit.arms()["classic-reborn"]
        self.assertAlmostEqual(arm["effective_alpha"], 1.0 + 2.0 * 0.81, delta=0.01)
        self.assertAlmostEqual(arm["effective_beta"], 1.0 + 1.0 * 0.81, delta=0.01)
        # Stored counts untouched by reads (decay materializes on update).
        self.assertAlmostEqual(arm["alpha"], 3.0)

    def test_update_materializes_decay_then_adds(self):
        two_weeks_ago = (datetime.now(timezone.utc)
                         - timedelta(weeks=2)).isoformat()
        os.makedirs(os.path.dirname(self._state_path()), exist_ok=True)
        with open(self._state_path(), "w") as f:
            json.dump({"arms": {"classic-reborn": {
                "alpha": 3.0, "beta": 2.0, "pulls": 0,
                "reward_sum": 0.0, "last": two_weeks_ago}},
                "total_pulls": 0}, f)
        bandit.update("classic-reborn", 1.0)
        arm = bandit.arms()["classic-reborn"]
        self.assertAlmostEqual(arm["alpha"], 2.62 + 1.0, delta=0.01)
        self.assertAlmostEqual(arm["beta"], 1.81 + 0.0, delta=0.01)

    # --- update ------------------------------------------------------------
    def test_update_win_and_loss(self):
        bandit.update("wildcard", 1.0)
        arm = bandit.arms()["wildcard"]
        self.assertAlmostEqual(arm["alpha"], 2.0, places=3)
        self.assertAlmostEqual(arm["beta"], 1.0, places=3)
        self.assertEqual(arm["pulls"], 1)
        bandit.update("wildcard", 0.0)
        arm = bandit.arms()["wildcard"]
        self.assertAlmostEqual(arm["alpha"], 2.0, places=3)
        self.assertAlmostEqual(arm["beta"], 2.0, places=3)
        self.assertEqual(arm["pulls"], 2)

    def test_update_clamps_reward(self):
        bandit.update("wildcard", 7.0)   # clamped to 1
        bandit.update("wildcard", -3.0)  # clamped to 0
        arm = bandit.arms()["wildcard"]
        self.assertAlmostEqual(arm["alpha"], 2.0, places=3)
        self.assertAlmostEqual(arm["beta"], 2.0, places=3)
        self.assertAlmostEqual(arm["reward_sum"], 1.0, places=3)

    def test_update_unknown_arm_refused(self):
        with self.assertRaises(ValueError):
            bandit.update("no-such-arm", 0.5)

    # --- retro bonus ---------------------------------------------------------
    def test_retro_bonus_is_alpha_only_no_pull(self):
        # A sale can never look like a loss: alpha-only, no beta, no pull.
        before = bandit.arms()["classic-reborn"]
        bandit.retro_bonus("classic-reborn", 0.05)
        after = bandit.arms()["classic-reborn"]
        self.assertAlmostEqual(after["alpha"], before["alpha"] + 0.05, places=3)
        self.assertAlmostEqual(after["beta"], before["beta"], places=3)
        self.assertEqual(after["pulls"], before["pulls"])

    def test_retro_bonus_unknown_arm_refused(self):
        with self.assertRaises(ValueError):
            bandit.retro_bonus("no-such-arm", 0.1)

    # --- pick ----------------------------------------------------------------
    def test_pick_returns_known_arm(self):
        random.seed(7)
        self.assertIn(bandit.pick(), bandit.arms())

    def test_pick_prefers_overwhelming_evidence(self):
        # Thompson with Beta(5000,1) vs Beta(1,5000): the posterior draws
        # essentially cannot cross, so the favored arm wins.
        os.makedirs(os.path.dirname(self._state_path()), exist_ok=True)
        now = datetime.now(timezone.utc).isoformat()
        with open(self._state_path(), "w") as f:
            json.dump({"arms": {
                "favored": {"alpha": 5000.0, "beta": 1.0, "pulls": 0,
                            "reward_sum": 0.0, "last": now},
                "starved": {"alpha": 1.0, "beta": 5000.0, "pulls": 0,
                            "reward_sum": 0.0, "last": now}},
                "total_pulls": 0}, f)
        os.remove(os.path.join(self._tmp.name, "corpus", "DIRECTIONS.json"))
        random.seed(42)
        picks = set(bandit.pick() for _ in range(20))
        self.assertEqual(picks, {"favored"})

    def test_pick_persists_seeded_state(self):
        random.seed(1)
        bandit.pick()
        self.assertTrue(os.path.exists(self._state_path()))
        with open(self._state_path()) as f:
            state = json.load(f)
        self.assertIn("classic-reborn", state["arms"])

    # --- concurrency: the clobber fix ------------------------------------
    def test_pick_does_not_rewrite_state_when_nothing_seeded(self):
        # The clobber bug: pick() unconditionally saved its loaded
        # snapshot, erasing any update() that landed in between. With all
        # arms already seeded, pick() must not write the file at all.
        random.seed(3)
        bandit.pick()  # first pick seeds and persists every arm
        bandit.update("gravity-physics", 1.0)  # the observation at risk
        with open(self._state_path(), "rb") as f:
            before = f.read()
        random.seed(4)
        bandit.pick()
        with open(self._state_path(), "rb") as f:
            after = f.read()
        self.assertEqual(before, after)  # the reward survived the pick
        self.assertAlmostEqual(
            json.loads(after)["arms"]["gravity-physics"]["alpha"],
            2.0, places=3)

    def test_lock_serializes_concurrent_update(self):
        # update() must queue behind the bandit lock, not interleave.
        bandit.update("wildcard", 1.0)  # alpha 1->2, creates the file
        done = []
        def worker():
            bandit.update("wildcard", 1.0)
            done.append(True)
        with bandit._locked():
            t = threading.Thread(target=worker)
            t.start()
            time.sleep(0.3)
            self.assertEqual(done, [])  # blocked while we hold the lock
        t.join(timeout=10)
        self.assertEqual(done, [True])
        # Both observations landed: 1 + 1 + 1 (decay over ms ~ 0).
        self.assertAlmostEqual(
            bandit.arms()["wildcard"]["alpha"], 3.0, places=2)


if __name__ == "__main__":
    unittest.main()
