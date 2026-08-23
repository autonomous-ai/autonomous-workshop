from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from alice.learning import (
    ContextualThompsonBandit,
    OutcomeEvidence,
    canonical_context,
)


class ContextTests(unittest.TestCase):
    def test_context_keys_are_order_independent(self) -> None:
        first = {"players": 4, "tags": ["fast", "social"]}
        second = {"tags": ["fast", "social"], "players": 4}
        self.assertEqual(canonical_context(first), canonical_context(second))

    def test_non_json_context_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonical_context({"bad": {1, 2, 3}})


class EvidenceGatedLearningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.learner = ContextualThompsonBandit(["shorten_rules", "add_combo"], seed=7)
        self.context = {"players": 2, "session": "prototype"}

    def test_unverified_outcome_does_not_update(self) -> None:
        before = self.learner.posterior("add_combo", self.context)
        accepted = self.learner.update(
            "add_combo",
            True,
            self.context,
            evidence_source="held_out",
            verified=False,
        )
        self.assertFalse(accepted)
        self.assertEqual(self.learner.posterior("add_combo", self.context), before)
        self.assertEqual(self.learner.last_update.reason, "unverified_outcome")

    def test_same_model_surrogate_never_updates_even_if_claimed_held_out(self) -> None:
        before = self.learner.posterior("add_combo", self.context)
        accepted = self.learner.update(
            "add_combo",
            1.0,
            self.context,
            evidence_source="held_out",
            verified=True,
            same_model_surrogate=True,
            weight=1_000_000,
        )
        self.assertFalse(accepted)
        self.assertEqual(self.learner.posterior("add_combo", self.context), before)
        self.assertEqual(self.learner.accepted_updates, 0)
        self.assertEqual(self.learner.rejected_updates, 1)
        self.assertEqual(self.learner.last_update.reason, "same_model_outcome")

    def test_matching_evaluator_and_candidate_ids_never_update(self) -> None:
        accepted = self.learner.update(
            "shorten_rules",
            True,
            self.context,
            evidence=OutcomeEvidence(
                "external",
                verified=True,
                evaluator_id="model-a",
                candidate_model_id="model-a",
            ),
        )
        self.assertFalse(accepted)
        self.assertEqual(self.learner.last_update.reason, "same_model_outcome")

    def test_verified_held_out_and_external_outcomes_update_beta_posterior(self) -> None:
        self.assertTrue(
            self.learner.update(
                "add_combo",
                True,
                self.context,
                evidence_source="held_out",
                verified=True,
                weight=2.0,
                event_id="held-1",
            )
        )
        self.assertTrue(
            self.learner.update(
                "add_combo",
                0.25,
                self.context,
                evidence_source="external",
                verified=True,
                weight=4.0,
                event_id="ext-1",
            )
        )
        posterior = self.learner.posterior("add_combo", self.context)
        self.assertAlmostEqual(posterior.alpha, 1.0 + 2.0 + 1.0)
        self.assertAlmostEqual(posterior.beta, 1.0 + 3.0)
        self.assertEqual(posterior.observations, 2)
        self.assertAlmostEqual(posterior.accepted_weight, 6.0)
        self.assertEqual(self.learner.accepted_updates, 2)

    def test_verified_human_manufacturing_and_market_sources_are_outcomes(self) -> None:
        for index, source in enumerate(("blind_human", "manufacturing", "market")):
            self.assertTrue(
                self.learner.update(
                    "add_combo",
                    True,
                    self.context,
                    evidence_source=source,
                    verified=True,
                    event_id=f"real-{index}",
                )
            )
        self.assertEqual(self.learner.posterior("add_combo", self.context).observations, 3)

    def test_simulation_and_independent_model_scores_do_not_train_policy(self) -> None:
        for source in ("simulation", "independent_model"):
            self.assertFalse(
                self.learner.update(
                    "add_combo",
                    True,
                    self.context,
                    evidence_source=source,
                    verified=True,
                )
            )
        self.assertEqual(self.learner.posterior("add_combo", self.context).observations, 0)

    def test_duplicate_verified_event_is_not_counted_twice(self) -> None:
        kwargs = {
            "evidence_source": "external",
            "verified": True,
            "event_id": "playtest-42",
        }
        self.assertTrue(self.learner.update("add_combo", True, self.context, **kwargs))
        once = self.learner.posterior("add_combo", self.context)
        self.assertFalse(self.learner.update("add_combo", True, self.context, **kwargs))
        self.assertEqual(self.learner.posterior("add_combo", self.context), once)
        self.assertEqual(self.learner.last_update.reason, "duplicate_event")

    def test_missing_evidence_metadata_fails_closed(self) -> None:
        self.assertFalse(self.learner.update("add_combo", True, self.context))
        self.assertEqual(self.learner.last_update.reason, "missing_evidence_source")

    def test_contexts_learn_independently(self) -> None:
        two_player = {"players": 2}
        four_player = {"players": 4}
        self.learner.update(
            "add_combo",
            True,
            two_player,
            evidence_source="held_out",
            verified=True,
        )
        self.assertGreater(self.learner.posterior_mean("add_combo", two_player), 0.5)
        self.assertEqual(self.learner.posterior_mean("add_combo", four_player), 0.5)

    def test_audit_log_records_rejected_and_accepted_observations(self) -> None:
        self.learner.update("add_combo", True, self.context)
        self.learner.update(
            "add_combo", True, self.context, evidence_source="external", verified=True
        )
        audit = self.learner.audit_log
        self.assertEqual(len(audit), 2)
        self.assertFalse(audit[0]["accepted"])
        self.assertTrue(audit[1]["accepted"])
        self.assertEqual(audit[0]["posterior_before"], audit[0]["posterior_after"])


class SelectionTests(unittest.TestCase):
    def test_same_seed_produces_same_thompson_sequence(self) -> None:
        first = ContextualThompsonBandit(["a", "b", "c"], seed=123)
        second = ContextualThompsonBandit(["a", "b", "c"], seed=123)
        contexts = [{"round": index % 2} for index in range(40)]
        first_actions = [first.choose_action(context) for context in contexts]
        second_actions = [second.choose_action(context) for context in contexts]
        self.assertEqual(first_actions, second_actions)

    def test_exploit_uses_posterior_mean_without_randomness(self) -> None:
        learner = ContextualThompsonBandit(["control", "candidate"], seed=3)
        for event in range(5):
            learner.update(
                "candidate",
                True,
                evidence_source="external",
                verified=True,
                event_id=f"win-{event}",
            )
            learner.update(
                "control",
                False,
                evidence_source="held_out",
                verified=True,
                event_id=f"loss-{event}",
            )
        self.assertEqual(learner.choose_action(explore=False), "candidate")
        self.assertEqual(learner.last_selection.mode, "exploit")

    def test_forced_and_randomized_control_are_explicit(self) -> None:
        learner = ContextualThompsonBandit(
            ["baseline", "change"],
            seed=4,
            control_action="baseline",
            control_rate=1.0,
        )
        randomized = learner.recommend()
        self.assertEqual(randomized.action, "baseline")
        self.assertEqual(randomized.mode, "randomized_control")
        forced = learner.recommend(force_control=True)
        self.assertEqual(forced.action, "baseline")
        self.assertEqual(forced.mode, "forced_control")

    def test_full_epsilon_supports_seeded_uniform_exploration(self) -> None:
        first = ContextualThompsonBandit(["a", "b", "c"], seed=9, exploration_rate=1.0)
        second = ContextualThompsonBandit(["a", "b", "c"], seed=9, epsilon=1.0)
        sequence_a = [first.recommend() for _ in range(20)]
        sequence_b = [second.recommend() for _ in range(20)]
        self.assertEqual([item.action for item in sequence_a], [item.action for item in sequence_b])
        self.assertEqual({item.mode for item in sequence_a}, {"epsilon"})


class PersistenceTests(unittest.TestCase):
    def build_learner(self) -> ContextualThompsonBandit:
        learner = ContextualThompsonBandit(
            ["baseline", "clarify", "rebalance"],
            seed=2026,
            alpha_prior=1.5,
            beta_prior=2.0,
            exploration_rate=0.15,
            control_action="baseline",
            control_rate=0.1,
        )
        for index in range(8):
            context = {"players": 2 + index % 3, "complexity": "medium"}
            learner.choose_action(context)
            learner.update(
                "clarify",
                index % 3 != 0,
                context,
                evidence_source="external" if index % 2 else "held_out",
                verified=True,
                event_id=f"verified-{index}",
            )
        learner.update(
            "rebalance",
            True,
            {"players": 4, "complexity": "medium"},
            evidence_source="surrogate",
            verified=True,
        )
        return learner

    def test_json_roundtrip_preserves_state_and_future_random_sequence(self) -> None:
        original = self.build_learner()
        payload = original.to_json()
        json.loads(payload)  # prove it is ordinary JSON, not a Python pickle
        restored = ContextualThompsonBandit.from_json(payload)
        self.assertEqual(restored.to_state(), original.to_state())

        future_contexts = [{"players": count, "complexity": "medium"} for count in (2, 4, 3, 2, 4)]
        expected = [original.choose_action(context) for context in future_contexts]
        actual = [restored.choose_action(context) for context in future_contexts]
        self.assertEqual(actual, expected)
        self.assertEqual(restored.to_state(), original.to_state())

    def test_file_roundtrip(self) -> None:
        original = self.build_learner()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "learner.json"
            original.save(path)
            restored = ContextualThompsonBandit.load(path)
        self.assertEqual(restored.to_state(), original.to_state())

    def test_unknown_state_version_is_rejected(self) -> None:
        state = self.build_learner().to_state()
        state["state_version"] = 999
        with self.assertRaises(ValueError):
            ContextualThompsonBandit.from_state(state)


if __name__ == "__main__":
    unittest.main()
