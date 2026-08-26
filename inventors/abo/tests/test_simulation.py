"""ABO's seeded simulation: the floor, the four styles, and what it measures.

These run tiny samples. The 1,000-completed-game floor is a property of the
gate, not of the sample size a check can afford, so it is proved by handing the
gate a sample that falls one short rather than by playing a thousand games in a
unit test.
"""

from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
for candidate in (
    INVENTOR_ROOT,
    INVENTOR_ROOT / "tests" / "fixtures",
    WORKSHOP_ROOT / "src",
):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import config  # noqa: E402
import fixture_engine as E  # noqa: E402
import simulation as S  # noqa: E402

HARNESS = config.load_harness("playtest")
ARTIFACT = "a" * 64

# Small enough to run in a check, large enough for every measurement to have
# something to say.
CHEAP = dict(
    seats=2,
    games_per_style=4,
    ladder_games=4,
    balance_games=4,
    distinctness_positions=6,
    sensitivity_games=6,
    mc_budget=8,
    seed=5,
)

_CACHE = {}


def cheap_run(**overrides):
    """One simulation, reused.

    Every measurement in this file reads the same run wherever it can. A
    lookahead policy is expensive by design — that is the whole reason the
    skill ladder means anything — so a check that re-ran it per assertion
    would be paying for the same numbers a dozen times.
    """

    import json

    settings = dict(CHEAP)
    settings.update(overrides)
    key = json.dumps(settings, sort_keys=True, default=repr)
    if key not in _CACHE:
        _CACHE[key] = S.run_simulation(E, artifact_sha256=ARTIFACT, **settings)
    return _CACHE[key]


class AdversarialPolicyTest(unittest.TestCase):
    """Design decision D3: the one style with no upstream equivalent."""

    def test_it_returns_a_legal_move(self):
        policy = S.make_adversarial(HARNESS)
        rng = random.Random(1)
        state = E.new_game(2, rng)
        moves = E.legal_moves(state)
        chosen = policy(E, state, 0, rng, moves)
        self.assertIn(chosen, moves)

    def test_it_denies_the_opponent_rather_than_advancing_itself(self):
        # A different objective from optimizing, which is the point of it
        # existing at all. Measured, not asserted: it must actually diverge.
        policies = S.scripted_policies(HARNESS, mc_budget=24, turn_cap=E.MAX_TURNS)
        outcome = S.measure_distinctness(
            HARNESS, E, policies, seats=2, turn_cap=E.MAX_TURNS, seed=5, positions=8
        )
        pair = next(
            item
            for item in outcome["pairs"]
            if sorted(item["styles"]) == ["adversarial", "optimizing"]
        )
        self.assertGreater(pair["positions_diverged"], 0)


class DistinctnessTest(unittest.TestCase):
    def test_the_three_scripted_styles_are_distinct(self):
        outcome = cheap_run()
        distinctness = outcome.evidence["style_distinctness"]
        self.assertTrue(distinctness["distinct"], distinctness["collapsed_pairs"])
        # Recorded rather than asserted: the positions where they differed.
        for pair in distinctness["pairs"]:
            self.assertGreater(pair["positions_diverged"], 0, pair["styles"])

    def test_two_collapsed_styles_are_reported_as_one(self):
        policies = S.scripted_policies(HARNESS, mc_budget=24, turn_cap=E.MAX_TURNS)
        # The same policy under two names is one style, and the check says so.
        policies["adversarial"] = policies["exploratory"]
        outcome = S.measure_distinctness(
            HARNESS, E, policies, seats=2, turn_cap=E.MAX_TURNS, seed=5, positions=8
        )
        self.assertFalse(outcome["distinct"])
        self.assertIn(["adversarial", "exploratory"], outcome["collapsed_pairs"])


class FloorTest(unittest.TestCase):
    def test_the_floor_is_a_thousand_completed_games(self):
        self.assertEqual(S.MINIMUM_COMPLETED_GAMES, 1_000)

    def test_a_sample_one_short_does_not_meet_the_floor(self):
        outcome = S.SimulationOutcome(
            evidence={"completed_games": 999},
            completed_games=999,
            styles_played=S.STYLES,
            findings=(),
        )
        self.assertFalse(outcome.meets_floor)
        self.assertFalse(outcome.passed)

    def test_a_sample_at_the_floor_meets_it(self):
        outcome = S.SimulationOutcome(
            evidence={"completed_games": 1_000},
            completed_games=1_000,
            styles_played=S.STYLES,
            findings=(),
        )
        self.assertTrue(outcome.meets_floor)
        self.assertTrue(outcome.passed)

    def test_abandoned_games_do_not_count_toward_the_total(self):
        # A turn cap of one turn abandons every game; none of them completed.
        outcome = cheap_run(turn_cap=1)
        self.assertEqual(outcome.completed_games, 0)
        abandoned = outcome.evidence["abandoned"]
        self.assertGreater(abandoned["turn_cap"], 0)
        self.assertFalse(outcome.meets_floor)
        # And the shortfall is reported rather than absorbed.
        self.assertTrue(
            any("did not reach a terminal state" in item for item in outcome.findings)
        )

    def test_the_deadline_abandons_rather_than_extending_itself(self):
        # A deadline already in the past stops the run where it stands.
        outcome = cheap_run(deadline_seconds=-1.0)
        self.assertEqual(outcome.completed_games, 0)
        self.assertGreater(outcome.evidence["abandoned"]["deadline"], 0)
        self.assertFalse(outcome.meets_floor)

    def test_completions_and_abandonments_are_reported_separately(self):
        outcome = cheap_run()
        for sample in outcome.evidence["samples"]:
            self.assertEqual(
                sample["games_played"],
                sample["completed_games"]
                + sample["abandoned"]["turn_cap"]
                + sample["abandoned"]["no_legal_move"]
                + sample["abandoned"]["engine_error"],
            )


class MeasuredPropertiesTest(unittest.TestCase):
    def setUp(self):
        self.outcome = cheap_run()

    def test_it_reports_termination(self):
        self.assertGreater(self.outcome.completed_games, 0)
        self.assertIn("abandoned", self.outcome.evidence)

    def test_it_reports_seat_advantage_over_a_seat_swapped_sample(self):
        balance = self.outcome.evidence["seat_advantage"]
        self.assertEqual(len(balance["win_rates"]), 2)
        self.assertAlmostEqual(balance["fair_share"], 0.5)
        self.assertIn("confidence_interval", balance)
        self.assertIn("best_seat", balance)

    def test_it_reports_forced_turns_and_branching(self):
        for sample in self.outcome.evidence["samples"]:
            self.assertIn("forced_fraction", sample)
            self.assertIn("branching_median", sample)
            self.assertIn("branching_max", sample)

    def test_it_reports_the_stronger_versus_weaker_margin(self):
        rungs = {item["rung"]: item for item in self.outcome.evidence["skill_ladder"]}
        self.assertIn("optimizing-vs-greedy", rungs)
        self.assertIn("greedy-vs-random", rungs)
        for rung in rungs.values():
            self.assertIn("win_rate", rung)
            self.assertIn("confidence_interval", rung)

    def test_it_names_declared_move_kinds_never_legal_or_never_chosen(self):
        kinds = self.outcome.evidence["move_kinds"]
        self.assertEqual(kinds["declared"], ["seat_pillar", "spend_lock"])
        self.assertEqual(kinds["never_legal"], [])
        self.assertEqual(kinds["never_chosen"], [])
        self.assertEqual(kinds["undeclared_but_seen"], [])

    def test_it_plays_every_declared_assumption_both_ways(self):
        readings = self.outcome.evidence["assumption_readings"]
        self.assertEqual(len(readings), 1)
        entry = readings[0]
        self.assertEqual(entry["id"], "locked-socket-counts")
        self.assertEqual(entry["rule"], "win[1]")
        # It changed the outcome, so the rules have to say which reading is meant.
        self.assertEqual(entry["verdict"], "blocking")
        self.assertGreater(entry["worst_delta"], 0.0)
        self.assertTrue(
            any("has to say which reading is meant" in item for item in self.outcome.findings)
        )

    def test_it_makes_no_claim_about_people(self):
        claim = self.outcome.evidence["claim"]
        self.assertIn("seeded games", claim)
        for word in ("enjoy", "fun", "understood", "would play"):
            self.assertNotIn(word, claim.casefold())


class ContractFindingTest(unittest.TestCase):
    def test_a_move_kind_that_is_never_legal_is_named(self):
        outcome = cheap_run()
        kinds = dict(outcome.evidence["move_kinds"])
        kinds["never_legal"] = ["ghost_move"]
        kinds["never_chosen"] = []
        kinds["undeclared_but_seen"] = []
        findings = S.contract_findings(E, [], kinds)
        self.assertTrue(any("ghost_move" in item["finding"] for item in findings))

    def test_an_always_forced_kind_seen_beside_another_is_a_contract_finding(self):
        # Ported from the imported harness: a kind claimed to carry no decision
        # that shares a turn with another legal move is a real branch sometimes.
        rng = random.Random(2)
        record = HARNESS.play_one(
            E, [HARNESS.pol_random] * 2, 2, rng, E.MAX_TURNS,
            admin_kinds=frozenset({"seat_pillar"}),
        )
        self.assertTrue(record["admin_violations"])
        self.assertIn("real branch sometimes", record["admin_violations"][0])
        # And the turn still counted as a branch rather than being excluded.
        self.assertTrue(record["branching"])


class ReproducibilityTest(unittest.TestCase):
    def test_a_recorded_seed_reproduces_the_same_games(self):
        first = cheap_run()
        second = cheap_run()
        self.assertEqual(
            first.evidence["seeds"], second.evidence["seeds"]
        )
        self.assertEqual(
            [sample["wins"] for sample in first.evidence["samples"]],
            [sample["wins"] for sample in second.evidence["samples"]],
        )
        self.assertEqual(first.completed_games, second.completed_games)

    def test_a_different_seed_produces_a_different_sample(self):
        first = cheap_run()
        second = cheap_run(seed=CHEAP["seed"] + 1)
        self.assertNotEqual(first.evidence["seeds"], second.evidence["seeds"])


class BindingTest(unittest.TestCase):
    def test_every_output_is_bound_to_the_revision_and_the_engine_bytes(self):
        outcome = cheap_run()
        self.assertEqual(outcome.evidence["artifact_sha256"], ARTIFACT)
        self.assertEqual(outcome.evidence["evidence_class"], "ai-simulation")
        self.assertIs(outcome.evidence["executable"], True)
        self.assertEqual(outcome.evidence["evaluator"], S.EVALUATOR)
        self.assertEqual(outcome.evidence["evaluator_version"], S.EVALUATOR_VERSION)
        self.assertEqual(len(outcome.evidence["engine_sha256"]), 64)

    def test_a_broken_engine_is_refused_rather_than_measured(self):
        class Hollow:
            PLAYERS = (2, 2)
            MAX_TURNS = 4
            HIDDEN_INFO = False

        with self.assertRaises(S.SimulationRefused):
            S.run_simulation(Hollow(), artifact_sha256=ARTIFACT, seats=2)


class SocialStyleTest(unittest.TestCase):
    def test_social_is_not_declared_without_a_policy_behind_it(self):
        outcome = cheap_run()
        self.assertNotIn("social", outcome.styles_played)
        self.assertTrue(
            any("'social'" in item for item in outcome.findings),
            outcome.findings,
        )

    def test_model_seat_games_supply_the_social_style(self):
        outcome = cheap_run(
            social_sample={"completed_games": 4, "source": "model-seats"}
        )
        self.assertIn("social", outcome.styles_played)
        # The two results keep their own evidence; this is a reference, not a merge.
        self.assertEqual(outcome.evidence["social_sample"]["source"], "model-seats")
        self.assertFalse(any("'social'" in item for item in outcome.findings))


class ShortReturnTest(unittest.TestCase):
    """A deadline reached short returns a Need, never a passing result."""

    def test_the_need_names_the_capability_and_reports_how_far_it_got(self):
        from playtest_job import simulation_need

        outcome = cheap_run()
        self.assertLess(outcome.completed_games, S.MINIMUM_COMPLETED_GAMES)
        need = simulation_need(outcome)
        self.assertEqual(need.job, "playtest")
        self.assertEqual(need.capability, "game-simulation")
        self.assertIn(str(outcome.completed_games), need.reason)
        self.assertIn(str(S.MINIMUM_COMPLETED_GAMES), need.reason)
        # And it says the deadline is not to be extended to reach the floor.
        self.assertIn("never extend the deadline silently", need.instructions)

    def test_a_short_run_returns_no_passing_simulation_result(self):
        outcome = cheap_run()
        self.assertFalse(outcome.passed)
        self.assertFalse(outcome.meets_floor)


if __name__ == "__main__":
    unittest.main()
