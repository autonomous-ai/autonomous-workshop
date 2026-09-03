import unittest

from workshop.product import BASELINE_PLAYTEST_CHECKS, ToyBlueprint
from workshop.product.blueprints import (
    SCORE_DIMENSIONS,
    SCORE_FLOOR,
    SCORE_MINIMUM_READS,
)


EXPECTED_CHECKS = (
    "agent-playtest",
    "mechanical-check",
    "printability-check",
)


class ToyBlueprintTest(unittest.TestCase):
    def test_open_ended_blueprint_has_one_exact_host_baseline(self):
        self.assertEqual(BASELINE_PLAYTEST_CHECKS, EXPECTED_CHECKS)
        blueprint = ToyBlueprint()
        self.assertEqual(
            blueprint.required_playtest_checks(), EXPECTED_CHECKS
        )
        self.assertEqual(
            blueprint.to_dict(),
            {
                "schema_version": 2,
                "kind": "autonomous-workshop.toy-blueprint",
                "required_playtest_checks": list(EXPECTED_CHECKS),
            },
        )
        self.assertNotIn("lane", blueprint.to_dict())

    def test_hash_is_stable_and_universal(self):
        self.assertEqual(ToyBlueprint(), ToyBlueprint())
        self.assertEqual(
            ToyBlueprint().sha256,
            "0137a4b232bfb2bdee48b161a3a1d3d547dfeac102f19755ba4a3de7174107ea",
        )

    def test_score_dimensions_are_evidence_rules_outside_the_bound_hash(self):
        blueprint = ToyBlueprint()
        self.assertEqual(
            blueprint.score_dimensions(),
            ("wish_fit", "play", "legibility", "build_confidence"),
        )
        self.assertEqual(blueprint.score_dimensions(), SCORE_DIMENSIONS)
        self.assertEqual(blueprint.score_floor(), SCORE_FLOOR)
        self.assertEqual(blueprint.score_minimum_reads(), SCORE_MINIMUM_READS)
        self.assertNotIn("score_dimensions", blueprint.to_dict())

    def test_legacy_generic_check_api_is_absent(self):
        self.assertFalse(hasattr(ToyBlueprint(), "required_checks"))


if __name__ == "__main__":
    unittest.main()
