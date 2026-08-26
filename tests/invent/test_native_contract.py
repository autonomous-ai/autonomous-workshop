import copy
import unittest

from workshop.errors import ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.product.blueprints import ToyBlueprint


def digest(character):
    return character * 64


class InventedContractTest(unittest.TestCase):
    def setUp(self):
        inventor = InventorRosterEntry(
            inventor_id="bob",
            agent_path=".codex/agents/bob.toml",
            agent_sha256=digest("a"),
            source_manifest_sha256=digest("b"),
            taste_sha256=digest("0"),
        )
        self.roster = InventorRoster((inventor,))
        self.assignment = NativeMatchAssignment(
            wish_sha256=digest("c"),
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id=inventor.inventor_id,
            selected_agent_path=inventor.agent_path,
            selected_agent_sha256=inventor.agent_sha256,
            selected_source_manifest_sha256=inventor.source_manifest_sha256,
            selected_taste_sha256=inventor.taste_sha256,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(
                MatchRankingEntry(
                    inventor.inventor_id,
                    "The only materialized inventor is also an exact mechanical fit.",
                ),
            ),
        )

    def invented(self, **overrides):
        values = {
            "wish_sha256": self.assignment.wish_sha256,
            "assignment_sha256": self.assignment.assignment_sha256,
            "taste_sha256": self.assignment.selected_taste_sha256,
            "blueprint_sha256": self.assignment.blueprint_sha256,
            "concept": {
                "title": "Moonstep Orrery",
                "summary": "A hand-wound walker turns the Wish into a visible lunar gait.",
                "signature_decision": "The phase offset is both mechanism and story.",
            },
            "research": {
                "sources": [
                    {
                        "url": "https://example.test/kinematics",
                        "claim": "A crank can translate rotary input into periodic motion.",
                    }
                ],
                "open_questions": ["Verify torque and pinch clearance during Make."],
            },
        }
        values.update(overrides)
        return NativeInvented(**values)

    def test_round_trip_binds_every_input_and_content_hash(self):
        invented = self.invented()
        invented.assert_context(self.assignment)
        self.assertEqual(NativeInvented.from_mapping(invented.to_dict()), invented)
        payload = invented.to_dict()
        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(payload["concept_sha256"], invented.concept_sha256)
        self.assertEqual(payload["research_sha256"], invented.research_sha256)
        self.assertEqual(
            payload["research"]["sources"][0]["url"],
            "https://example.test/kinematics",
        )
        self.assertNotIn("lane", payload)
        self.assertNotIn("score", payload)
        self.assertNotIn("passed", payload)
        self.assertNotIn("target_score", payload)

    def test_rejects_model_gate_fields_and_stale_content_hashes(self):
        scored = self.invented().to_dict()
        scored["score"] = 100
        with self.assertRaisesRegex(ContractError, "fields"):
            NativeInvented.from_mapping(scored)

        stale = copy.deepcopy(self.invented().to_dict())
        stale["research"]["open_questions"].append("A new unbound question.")
        with self.assertRaisesRegex(ContractError, "hashes"):
            NativeInvented.from_mapping(stale)

    def test_rejects_another_assignment_and_legacy_lane_field(self):
        other = NativeMatchAssignment(
            wish_sha256=digest("d"),
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="bob",
            selected_agent_path=".codex/agents/bob.toml",
            selected_agent_sha256=digest("a"),
            selected_source_manifest_sha256=digest("b"),
            selected_taste_sha256=digest("0"),
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(MatchRankingEntry("bob", "Exact fit."),),
        )
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            self.invented().assert_context(other)

        legacy = self.invented().to_dict()
        legacy["lane"] = "moving-machines"
        with self.assertRaisesRegex(ContractError, "fields"):
            NativeInvented.from_mapping(legacy)


if __name__ == "__main__":
    unittest.main()
