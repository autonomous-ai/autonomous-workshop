from __future__ import annotations

import math
import unittest

from alice.reward import (
    QUALITY_DIMENSIONS,
    Evidence,
    EvidenceSource,
    QualityScores,
    RewardConfig,
    RewardEvaluator,
    evaluate_reward,
    weighted_geometric_quality,
)


def scores(value: float, **overrides: float) -> dict[str, float]:
    result = {dimension: value for dimension in QUALITY_DIMENSIONS}
    result.update(overrides)
    return result


class QualityScoreTests(unittest.TestCase):
    def test_equal_dimensions_have_same_geometric_score(self) -> None:
        self.assertAlmostEqual(weighted_geometric_quality(scores(0.8)), 0.8)

    def test_geometric_score_penalizes_a_single_weak_dimension(self) -> None:
        values = scores(0.9, balance=0.1)
        geometric = weighted_geometric_quality(values)
        arithmetic = sum(
            values[name] * RewardConfig().weights[name] for name in QUALITY_DIMENSIONS
        ) / sum(RewardConfig().weights.values())
        self.assertLess(geometric, arithmetic)

    def test_zero_dimension_makes_geometric_score_zero(self) -> None:
        self.assertEqual(weighted_geometric_quality(scores(0.9, clarity=0.0)), 0.0)

    def test_quality_scores_reject_missing_or_out_of_range_values(self) -> None:
        with self.assertRaises(ValueError):
            QualityScores.from_mapping({"clarity": 0.9})
        with self.assertRaises(ValueError):
            QualityScores.from_mapping(scores(1.1))


class PublicationGateTests(unittest.TestCase):
    def test_blind_human_batch_satisfies_held_out_and_external_counts(self) -> None:
        assessment = evaluate_reward(
            Evidence("blind_human", scores(0.82), verified=True, sample_size=6)
        )
        self.assertTrue(assessment.publish)
        self.assertEqual(assessment.eligible_samples, 6)
        self.assertEqual(assessment.held_out_samples, 6)
        self.assertEqual(assessment.external_samples, 6)

    def test_verified_held_out_and_external_evidence_can_publish(self) -> None:
        assessment = evaluate_reward(
            [
                Evidence("held_out", scores(0.82), verified=True, sample_size=20),
                Evidence("external", scores(0.78), verified=True, sample_size=10),
            ]
        )
        self.assertTrue(assessment.publication_allowed)
        self.assertIsNone(assessment.failed_gate)
        self.assertEqual(assessment.failure_reasons, ())
        self.assertGreater(assessment.reward, 0.0)
        self.assertEqual(assessment.held_out_samples, 20)
        self.assertEqual(assessment.external_samples, 10)

    def test_same_model_surrogate_alone_can_never_publish(self) -> None:
        assessment = evaluate_reward(
            Evidence(
                EvidenceSource.SAME_MODEL_SURROGATE,
                scores(1.0),
                verified=True,
                sample_size=1_000_000,
                confidence=1.0,
            )
        )
        self.assertFalse(assessment.publication_allowed)
        self.assertEqual(assessment.failed_gate, "independent_evidence")
        self.assertEqual(assessment.quality_score, 0.0)
        self.assertEqual(assessment.confidence, 0.0)
        self.assertEqual(assessment.reward, 0.0)
        self.assertIn("no_eligible_independent_evidence", assessment.failure_codes)
        self.assertIn("same_model", assessment.warnings[0])

    def test_simulation_is_routing_evidence_not_release_evidence(self) -> None:
        assessment = evaluate_reward(
            Evidence("simulation", scores(1.0), verified=True, sample_size=1_000)
        )
        self.assertFalse(assessment.publish)
        self.assertEqual(assessment.eligible_samples, 0)
        self.assertIn("no_eligible_independent_evidence", assessment.failure_codes)

    def test_massive_surrogate_batch_cannot_rescue_weak_independent_data(self) -> None:
        weak = scores(0.9, balance=0.3)
        assessment = evaluate_reward(
            [
                Evidence("held_out", weak, verified=True, sample_size=6),
                Evidence("external", weak, verified=True, sample_size=3),
                Evidence(
                    "held_out",
                    scores(1.0),
                    verified=True,
                    sample_size=10_000_000,
                    same_model_surrogate=True,
                ),
            ]
        )
        self.assertFalse(assessment.publish)
        self.assertAlmostEqual(assessment.dimension_scores["balance"], 0.3)
        self.assertEqual(assessment.eligible_samples, 9)
        self.assertEqual(assessment.excluded_evidence, 1)
        self.assertIn("balance_below_floor", assessment.failure_codes)
        self.assertEqual(assessment.reward, 0.0)

    def test_massive_factory_domains_cannot_wash_out_failed_blind_human_quality(self) -> None:
        weak_human = scores(0.9, fun_replay=0.2)
        assessment = evaluate_reward(
            [
                Evidence(
                    "blind_human", weak_human, verified=True, sample_size=6
                ),
                Evidence(
                    "manufacturing", scores(1.0), verified=True, sample_size=10_000_000
                ),
                Evidence(
                    "market", scores(1.0), verified=True, sample_size=10_000_000
                ),
            ]
        )

        self.assertFalse(assessment.publish)
        self.assertAlmostEqual(
            assessment.source_domain_scores["blind_human"]["fun_replay"], 0.2
        )
        self.assertIn("blind_human_fun_replay_below_floor", assessment.failure_codes)

    def test_same_source_score_weight_is_capped(self) -> None:
        config = RewardConfig(
            dimension_floors={dimension: 0.1 for dimension in QUALITY_DIMENSIONS},
            quality_threshold=0.1,
            max_score_weight_per_batch=8,
        )
        assessment = evaluate_reward(
            [
                Evidence("held_out", scores(0.2), verified=True, sample_size=8),
                Evidence("held_out", scores(1.0), verified=True, sample_size=1_000_000),
                Evidence("external", scores(0.8), verified=True, sample_size=3),
            ],
            config,
        )

        self.assertAlmostEqual(
            assessment.source_domain_scores["held_out"]["clarity"], 0.6
        )

    def test_surrogate_cannot_fill_a_missing_independent_dimension(self) -> None:
        partial = scores(0.8)
        del partial["economics_market"]
        assessment = evaluate_reward(
            [
                Evidence("held_out", partial, verified=True, sample_size=6),
                Evidence("external", partial, verified=True, sample_size=3),
                Evidence("surrogate", scores(1.0), verified=True, sample_size=100),
            ]
        )
        self.assertFalse(assessment.can_publish)
        self.assertEqual(assessment.failed_gate, "metric_coverage")
        self.assertIn("missing_quality_dimensions", assessment.failure_codes)
        self.assertNotIn("economics_market", assessment.dimension_scores)

    def test_unverified_external_batch_does_not_meet_external_requirement(self) -> None:
        assessment = evaluate_reward(
            [
                Evidence("held_out", scores(0.9), verified=True, sample_size=6),
                Evidence("external", scores(0.9), verified=False, sample_size=50),
            ]
        )
        self.assertFalse(assessment.publish)
        self.assertEqual(assessment.external_samples, 0)
        self.assertEqual(assessment.failed_gate, "evidence_requirements")
        self.assertIn("insufficient_external_evidence", assessment.failure_codes)

    def test_matching_model_id_is_excluded_even_if_claimed_external(self) -> None:
        assessment = evaluate_reward(
            [
                Evidence("held_out", scores(0.9), verified=True, sample_size=6),
                Evidence(
                    "external",
                    scores(1.0),
                    verified=True,
                    evaluator_id="alice-model-v7",
                    candidate_model_id="alice-model-v7",
                ),
            ]
        )
        self.assertFalse(assessment.publish)
        self.assertEqual(assessment.external_samples, 0)
        self.assertIn("insufficient_external_evidence", assessment.failure_codes)

    def test_hard_floor_is_lexicographic_and_cannot_be_averaged_away(self) -> None:
        config = RewardConfig(
            dimension_floors={dimension: 0.4 for dimension in QUALITY_DIMENSIONS},
            quality_threshold=0.6,
        )
        # The aggregate remains over 0.6, but clarity misses its 0.4 hard floor.
        poor_clarity = scores(1.0, clarity=0.39)
        assessment = evaluate_reward(
            [
                Evidence("held_out", poor_clarity, verified=True, sample_size=6),
                Evidence("external", poor_clarity, verified=True, sample_size=3),
            ],
            config,
        )
        self.assertGreater(assessment.quality_score, config.quality_threshold)
        self.assertFalse(assessment.publish)
        self.assertEqual(assessment.failed_gate, "dimension_floors")
        self.assertEqual(assessment.reward, 0.0)

    def test_confidence_is_a_hard_gate_with_explicit_reason(self) -> None:
        assessment = RewardEvaluator().evaluate(
            [
                Evidence(
                    "held_out", scores(0.95), verified=True, sample_size=6, confidence=0.5
                ),
                Evidence(
                    "external", scores(0.95), verified=True, sample_size=3, confidence=0.5
                ),
            ]
        )
        self.assertFalse(assessment.publish)
        self.assertEqual(assessment.failed_gate, "confidence")
        self.assertIn("confidence_below_threshold", assessment.failure_codes)
        self.assertTrue(any("0.500" in reason for reason in assessment.failure_reasons))

    def test_reward_vector_begins_with_ordered_gate_bits(self) -> None:
        assessment = evaluate_reward([])
        gate_bits = assessment.reward_vector[: len(assessment.gate_results)]
        self.assertEqual(gate_bits, tuple(float(gate.passed) for gate in assessment.gate_results))
        self.assertEqual(assessment.reward, 0.0)


if __name__ == "__main__":
    unittest.main()
