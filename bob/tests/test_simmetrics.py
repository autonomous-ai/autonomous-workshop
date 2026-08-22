"""Tests for loops/simmetrics.py — the instrument is only worth having if it
separates the known-good anchor from the known-broken one (the Millbind /
Deep Claim bar: a threshold that cannot separate them is decoration)."""

import importlib.util
import os
import unittest

from loops import simmetrics

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENGINES = os.path.join(_ROOT, "tests", "fixtures", "engines")


def _load_fixture(name):
    path = os.path.join(_ENGINES, name + ".py")
    spec = importlib.util.spec_from_file_location("fixture_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GoodGameTest(unittest.TestCase):
    """The known-good anchor must pass every floor."""

    @classmethod
    def setUpClass(cls):
        cls.engine = _load_fixture("goodgame")
        # 600 games: enough that the seat-spread gates measure the game, not
        # the sample (spread noise sigma ~0.03 at n=600; gate is 0.10).
        # Verified to pass on seeds 0..7 — the seed here is pinned for
        # reproducibility, not cherry-picked past a failure.
        cls.report = simmetrics.simulate(cls.engine, 2, n_games=600, seed=0)

    def test_all_floors_pass(self):
        self.assertTrue(
            self.report["verdicts"]["all_pass"],
            "known-good anchor failed floors: %r" % self.report["verdicts"])

    def test_gavel_five_shape(self):
        gavel = self.report["gavel"]
        for key in ("balance", "decisiveness", "completion", "agency"):
            self.assertIsNotNone(gavel[key], key)
            self.assertGreaterEqual(gavel[key], 0.0, key)
            self.assertLessEqual(gavel[key], 1.0, key)
        # Coverage is unmeasurable under the boardless engine contract:
        # None (skipped), never a silent 1.0.
        self.assertIsNone(gavel["coverage"])
        self.assertGreater(gavel["harmonic_mean"], 0.9)

    def test_skill_staircase_is_monotone_with_real_gaps(self):
        edges = self.report["ladder"]["edges"]
        self.assertGreaterEqual(edges["greedy>random"], simmetrics.MIN_SKILL_EDGE)
        self.assertGreaterEqual(edges["lookahead1>greedy"], simmetrics.MIN_SKILL_EDGE)
        self.assertGreaterEqual(edges["lookahead1>random"], simmetrics.MIN_SKILL_EDGE)

    def test_seat_fairness_at_strongest_rung(self):
        self.assertLessEqual(
            self.report["ladder"]["strongest_seat_spread"],
            simmetrics.MAX_SEAT_EDGE)

    def test_branching_and_agency(self):
        self.assertEqual(self.report["branching"]["median"], 3.0)
        self.assertEqual(self.report["branching"]["forced_fraction"], 0.0)

    def test_browne_tier_present_and_sane(self):
        browne = self.report["browne"]
        self.assertGreater(browne["lead_changes_mean"], 0.0)
        self.assertGreater(browne["drama"], 0.0)
        self.assertGreaterEqual(browne["late_uncertainty"], 0.0)
        self.assertLessEqual(browne["late_uncertainty"], 1.0)
        self.assertGreater(browne["killer_scarcity"], 0.5)
        duration = browne["duration"]
        self.assertGreater(duration["median"], 0)
        self.assertGreaterEqual(duration["false_start_share"], 0.0)
        self.assertLess(duration["false_start_share"], 0.05)

    def test_report_carries_thresholds_for_the_record(self):
        self.assertEqual(self.report["thresholds"]["MAX_SEAT_EDGE"],
                         simmetrics.MAX_SEAT_EDGE)


class BadGameTest(unittest.TestCase):
    """The known-broken anchor (first mover always wins, fake choices) must
    fail on seat bias and skill ladder — the two defects it was built with —
    and must NOT fail on the dimensions it was built healthy (branching,
    completion): a fixture that fails for the wrong reason proves nothing."""

    @classmethod
    def setUpClass(cls):
        cls.engine = _load_fixture("badgame")
        cls.report = simmetrics.simulate(cls.engine, 2, n_games=200, seed=0)

    def test_fails_seat_bias(self):
        self.assertFalse(self.report["verdicts"]["seat_bias_ok"])
        self.assertFalse(self.report["verdicts"]["balance_ok"])

    def test_fails_skill_ladder(self):
        self.assertFalse(self.report["verdicts"]["skill_ladder_ok"])
        # No policy can beat any other in a game with fake choices: every
        # edge sits at the chance baseline.
        for edge in self.report["ladder"]["edges"].values():
            self.assertLess(edge, simmetrics.MIN_SKILL_EDGE)

    def test_fails_runaway(self):
        # Seat 0 wins 100% of mirror games — the >=85% runaway wall (G3).
        self.assertFalse(self.report["verdicts"]["runaway_ok"])
        self.assertEqual(
            self.report["ladder"]["runaway_max_seat_winrate"], 1.0)

    def test_fails_for_the_right_reasons_only(self):
        verdicts = self.report["verdicts"]
        self.assertTrue(verdicts["completion_ok"])
        self.assertTrue(verdicts["decisiveness_ok"])
        self.assertTrue(verdicts["branching_ok"])
        self.assertTrue(verdicts["forced_ok"])
        self.assertFalse(verdicts["all_pass"])


class DeterminismTest(unittest.TestCase):
    def test_same_seed_same_report(self):
        engine = _load_fixture("goodgame")
        first = simmetrics.simulate(engine, 2, n_games=120, seed=42)
        second = simmetrics.simulate(engine, 2, n_games=120, seed=42)
        self.assertEqual(first, second)


class ApiGuardTest(unittest.TestCase):
    def test_unknown_policy_rejected(self):
        engine = _load_fixture("goodgame")
        with self.assertRaises(ValueError):
            simmetrics.simulate(engine, 2, n_games=10, seed=0,
                                policies=("random", "mcts9000"))

    def test_bad_player_count_rejected(self):
        engine = _load_fixture("goodgame")
        with self.assertRaises(ValueError):
            simmetrics.simulate(engine, 0, n_games=10, seed=0)


class HarmonicMeanTest(unittest.TestCase):
    """None-safety is load-bearing: coverage is None on every boardless
    engine, and skipping must differ from zeroing."""

    def test_none_values_are_skipped_not_zeroed(self):
        self.assertEqual(simmetrics._harmonic_mean([1.0, 1.0, None]), 1.0)

    def test_any_zero_tanks_the_mean(self):
        self.assertEqual(simmetrics._harmonic_mean([1.0, 0.0, None]), 0.0)

    def test_all_none_is_none(self):
        self.assertIsNone(simmetrics._harmonic_mean([None, None]))


class _NeverEndingEngine:
    """An ordinary agent bug: a game that never terminates under random
    play. Before the short-circuit this cost the full battery at a
    4x PROBE_MOVE_CAP move cap — hours of compute for a completion FAIL
    the probe already knew (review 2026-08-22)."""

    ASSUMPTIONS = []
    IDEA_SHA = "never-ends-fixture"

    @staticmethod
    def new_game(n_players, seed):
        return 0

    @staticmethod
    def player_to_move(state):
        return state % 2

    @staticmethod
    def legal_moves(state):
        return [0, 1, 2]

    @staticmethod
    def apply(state, move):
        return state + 1

    @staticmethod
    def is_over(state):
        return False

    @staticmethod
    def winners(state):
        return []

    @staticmethod
    def scores(state):
        return [0.0, 0.0]

    @staticmethod
    def observation(state, seat):
        return "endless"


class ShortCircuitTest(unittest.TestCase):
    """Zero probe terminations must skip the main battery and ladder and
    emit a failing, shape-compatible report — fail-closed, cheap."""

    @classmethod
    def setUpClass(cls):
        cls.report = simmetrics.simulate(_NeverEndingEngine, 2,
                                         n_games=60, seed=0)

    def test_fails_closed_without_running_the_battery(self):
        report = self.report
        self.assertFalse(report["verdicts"]["all_pass"])
        self.assertFalse(report["verdicts"]["completion_ok"])
        self.assertIsNone(report["gavel"]["harmonic_mean"])
        # The battery and ladder never ran: no matrix, no edges, no mirrors.
        self.assertEqual(report["ladder"]["matrix"], {})
        self.assertEqual(report["ladder"]["edges"], {})
        self.assertEqual(report["ladder"]["mirror_seat_winrates"], {})
        self.assertIn("short_circuit", report["notes"])

    def test_every_verdict_present_and_false(self):
        # Consumers iterate the verdict keys (invent's failed-gates list),
        # so the short-circuit report must carry the full set.
        expected = {"balance_ok", "decisiveness_ok", "completion_ok",
                    "seat_bias_ok", "skill_ladder_ok", "runaway_ok",
                    "forced_ok", "branching_ok", "all_pass"}
        self.assertEqual(set(self.report["verdicts"]), expected)
        self.assertFalse(any(self.report["verdicts"].values()))

    def test_consumer_fields_survive(self):
        # tablerun._move_cap reads move_cap; reward reads gavel/ladder.
        self.assertGreaterEqual(self.report["move_cap"],
                                simmetrics.MIN_MOVE_CAP)
        self.assertEqual(self.report["probe_completion"], 0.0)
        self.assertIn("thresholds", self.report)


if __name__ == "__main__":
    unittest.main()
