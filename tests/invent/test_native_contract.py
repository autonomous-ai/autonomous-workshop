import copy
import unittest

from workshop.errors import ContractError
from workshop.invent.native import InventedV2
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    PersonaCatalog,
    PersonaCatalogEntry,
)
from workshop.product.blueprints import ToyBlueprint


def digest(character):
    return character * 64


class InventedV2Test(unittest.TestCase):
    def setUp(self):
        persona = PersonaCatalogEntry(
            inventor_id="bob",
            lane="moving-machines",
            manifest_sha256=digest("a"),
            taste_sha256=digest("b"),
        )
        self.catalog = PersonaCatalog((persona,))
        self.assignment = NativeMatchAssignment(
            wish_sha256=digest("c"),
            persona_catalog_sha256=self.catalog.catalog_sha256,
            selected_inventor_id=persona.inventor_id,
            selected_lane=persona.lane,
            selected_manifest_sha256=persona.manifest_sha256,
            selected_taste_sha256=persona.taste_sha256,
            blueprint_sha256=ToyBlueprint.for_lane(persona.lane).sha256,
            ranking=(
                MatchRankingEntry(
                    persona.inventor_id,
                    "The only materialized persona is also an exact mechanical fit.",
                ),
            ),
        )

    def invented(self, **overrides):
        values = {
            "wish_sha256": self.assignment.wish_sha256,
            "assignment_sha256": self.assignment.assignment_sha256,
            "taste_sha256": self.assignment.selected_taste_sha256,
            "blueprint_sha256": self.assignment.blueprint_sha256,
            "lane": self.assignment.selected_lane,
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
        return InventedV2(**values)

    def test_round_trip_binds_every_input_and_content_hash(self):
        invented = self.invented()
        invented.assert_context(self.assignment)
        self.assertEqual(InventedV2.from_mapping(invented.to_dict()), invented)
        payload = invented.to_dict()
        self.assertEqual(payload["schema_version"], 2)
        self.assertEqual(payload["concept_sha256"], invented.concept_sha256)
        self.assertEqual(payload["research_sha256"], invented.research_sha256)
        self.assertNotIn("score", payload)
        self.assertNotIn("passed", payload)
        self.assertNotIn("target_score", payload)

    def test_rejects_model_gate_fields_and_stale_content_hashes(self):
        scored = self.invented().to_dict()
        scored["score"] = 100
        with self.assertRaisesRegex(ContractError, "fields"):
            InventedV2.from_mapping(scored)

        stale = copy.deepcopy(self.invented().to_dict())
        stale["research"]["open_questions"].append("A new unbound question.")
        with self.assertRaisesRegex(ContractError, "hashes"):
            InventedV2.from_mapping(stale)

    def test_rejects_another_assignment_or_lane(self):
        other = NativeMatchAssignment(
            wish_sha256=digest("d"),
            persona_catalog_sha256=self.catalog.catalog_sha256,
            selected_inventor_id="bob",
            selected_lane="moving-machines",
            selected_manifest_sha256=digest("a"),
            selected_taste_sha256=digest("b"),
            blueprint_sha256=ToyBlueprint.for_lane("moving-machines").sha256,
            ranking=(MatchRankingEntry("bob", "Exact fit."),),
        )
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            self.invented().assert_context(other)

        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            self.invented(lane="little-worlds").assert_context(self.assignment)


if __name__ == "__main__":
    unittest.main()
