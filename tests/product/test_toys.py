import unittest

from workshop.errors import ContractError
from workshop.product import PLAYTHING_LANES, ToyBlueprint


EXPECTED_CHECKS = {
    "classics-made-yours": (
        "agent-playtest",
        "classic-rules-test",
        "mechanical-test",
        "print-test",
    ),
    "invented-games": (
        "agent-playtest",
        "game-simulation",
        "mechanical-test",
        "print-test",
    ),
    "moving-machines": (
        "agent-playtest",
        "motion-test",
        "mechanical-test",
        "print-test",
    ),
    "holdable-science": (
        "agent-playtest",
        "science-test",
        "mechanical-test",
        "print-test",
    ),
    "little-worlds": (
        "agent-playtest",
        "world-test",
        "mechanical-test",
        "print-test",
    ),
}


class ToyBlueprintTest(unittest.TestCase):
    def test_five_lanes_have_exact_playtest_bindings(self):
        self.assertEqual(PLAYTHING_LANES, tuple(EXPECTED_CHECKS))
        for lane, expected_checks in EXPECTED_CHECKS.items():
            with self.subTest(lane=lane):
                blueprint = ToyBlueprint.for_lane(lane)
                self.assertEqual(
                    blueprint.required_capabilities("playtest"), expected_checks
                )
                self.assertEqual(
                    blueprint.to_dict(),
                    {
                        "schema_version": 1,
                        "kind": "autonomous-workshop.toy-blueprint",
                        "lane": lane,
                        "required_playtest_checks": list(expected_checks),
                    },
                )

    def test_hash_is_stable_and_lane_specific(self):
        hashes = {
            lane: ToyBlueprint.for_lane(lane).sha256 for lane in PLAYTHING_LANES
        }
        self.assertEqual(len(set(hashes.values())), len(PLAYTHING_LANES))
        self.assertEqual(
            hashes,
            {
                "classics-made-yours": "c56fbc7cea6008f8691862cf05ab7c8f5cea3adfee24ad29818a0ac2d903c992",
                "invented-games": "686be8eae857f84283da1ca52204ee756618db056214a19845c4ed325a8b1d8b",
                "moving-machines": "5a1b648bf71afaaab47709fd9e24824a1a9a17cab7b7be9850a00201f4dee30f",
                "holdable-science": "6a3b8f5c84023796d8f14802d545d9d61fdc2ae1de44e5800ce809deb6cdb988",
                "little-worlds": "9e325eb3e966dc66c8bc1e13c145255e4fff2c7075572399551a7663052bfe94",
            },
        )

    def test_unknown_lane_and_non_playtest_query_fail_closed(self):
        with self.assertRaises(ContractError):
            ToyBlueprint.for_lane("organizer")
        with self.assertRaises(ContractError):
            ToyBlueprint.for_lane("little-worlds").required_capabilities("invent")


if __name__ == "__main__":
    unittest.main()
