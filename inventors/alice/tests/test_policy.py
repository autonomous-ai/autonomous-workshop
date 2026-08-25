import unittest

from alice.config import load_config
from alice.policy import (
    REQUIRED_FACTORY_CAPABILITIES,
    ReleaseFacts,
    ReleasePolicy,
    release_policy_from_config,
    validate_transition,
)
from alice.reward import Evidence, QualityScores


GOOD = QualityScores(0.85, 0.82, 0.80, 0.78, 0.80, 0.82, 0.81)


def release_facts(**overrides):
    values = dict(
        evidence_integrity=True,
        rules_complete=True,
        terminates=True,
        blind_groups=3,
        minimum_games_per_group=2,
        real_print_receipt=True,
        print_yield=0.97,
        gross_margin=0.55,
        production_packet_hash="a" * 64,
        reviewed_packet_hash="a" * 64,
        factory_capabilities=(
            "durable_publication_intent",
            "explicit_price",
            "ambiguous_no_retry",
            "page_pipeline_readback",
            "expected_history_cas",
            "exact_sku_currency_binding",
            "server_enrichment_readback",
            "order_to_print_job",
        ),
    )
    values.update(overrides)
    return ReleaseFacts(**values)


def evidence():
    return [
        Evidence("held_out", GOOD, verified=True, sample_size=6, confidence=0.9),
        Evidence("market", GOOD, verified=True, sample_size=3, confidence=0.9),
    ]


class PolicyTests(unittest.TestCase):
    def test_full_evidence_can_auto_publish(self) -> None:
        decision = ReleasePolicy().assess(release_facts(), evidence(), effect_mode="live")
        self.assertTrue(decision.allowed, decision.failures)

    def test_checked_in_policy_requires_explicit_auto_publish_activation(self) -> None:
        decision = release_policy_from_config(load_config()).assess(
            release_facts(), evidence(), effect_mode="live"
        )

        self.assertFalse(decision.allowed)
        self.assertIn("automatic_publication_disabled", decision.failures)

    def test_live_fails_closed_without_backend_capability(self) -> None:
        facts = release_facts(factory_capabilities=("explicit_price",))
        decision = ReleasePolicy().assess(facts, evidence(), effect_mode="live")
        self.assertFalse(decision.allowed)
        self.assertTrue(
            any("durable_publication_intent" in item for item in decision.failures)
        )

    def test_same_model_volume_cannot_unlock_release(self) -> None:
        fake = Evidence("same_model", GOOD, verified=True, sample_size=10_000, confidence=1.0)
        decision = ReleasePolicy().assess(release_facts(), [fake], effect_mode="live")
        self.assertFalse(decision.allowed)
        self.assertIn("quality:no_eligible_independent_evidence", decision.failures)

    def test_exact_packet_must_match(self) -> None:
        decision = ReleasePolicy().assess(
            release_facts(reviewed_packet_hash="b" * 64), evidence(), effect_mode="draft"
        )
        self.assertIn("reviewed_packet_hash_mismatch", decision.failures)

    def test_state_machine_rejects_skipping_human_evidence(self) -> None:
        with self.assertRaises(ValueError):
            validate_transition("rules_valid", "production_validated")

    def test_config_can_add_but_cannot_remove_compiled_live_capabilities(self) -> None:
        config = load_config()
        config["adapters"]["required_live_capabilities"] = ["deployment_specific"]

        policy = release_policy_from_config(config)

        required = set(policy.config.required_factory_capabilities)
        self.assertTrue(REQUIRED_FACTORY_CAPABILITIES.issubset(required))
        self.assertIn("deployment_specific", required)

    def test_config_can_tighten_but_cannot_weaken_compiled_quality_floors(self) -> None:
        config = load_config()
        config["quality"].update(
            {
                "minimum_dimension": 0.0,
                "minimum_quality": 0.0,
                "minimum_confidence": 0.0,
                "minimum_blind_groups": 0,
                "minimum_games_per_group": 0,
                "minimum_print_yield": 0.0,
                "minimum_gross_margin": 0.0,
            }
        )
        config["learning"]["minimum_external_trials"] = 0

        policy = release_policy_from_config(config).config

        self.assertEqual(policy.min_blind_groups, 3)
        self.assertEqual(policy.min_games_per_group, 2)
        self.assertEqual(policy.min_print_yield, 0.95)
        self.assertEqual(policy.min_gross_margin, 0.50)
        self.assertEqual(policy.reward.quality_threshold, 0.72)
        self.assertEqual(policy.reward.min_confidence, 0.70)
        self.assertEqual(policy.reward.min_external_samples, 3)


if __name__ == "__main__":
    unittest.main()
