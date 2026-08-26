import copy
import unittest

from workshop.errors import ContractError
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    PersonaCatalog,
    PersonaCatalogEntry,
)
from workshop.product.blueprints import ToyBlueprint


def digest(character):
    return character * 64


class NativeMatchAssignmentTest(unittest.TestCase):
    def setUp(self):
        self.wish_sha256 = digest("f")
        self.alice = PersonaCatalogEntry(
            inventor_id="alice",
            lane="classics-made-yours",
            manifest_sha256=digest("a"),
            taste_sha256=digest("b"),
        )
        self.bob = PersonaCatalogEntry(
            inventor_id="bob",
            lane="moving-machines",
            manifest_sha256=digest("c"),
            taste_sha256=digest("d"),
        )
        self.catalog = PersonaCatalog((self.bob, self.alice))

    def assignment(self):
        return NativeMatchAssignment(
            wish_sha256=self.wish_sha256,
            persona_catalog_sha256=self.catalog.catalog_sha256,
            selected_inventor_id="bob",
            selected_lane="moving-machines",
            selected_manifest_sha256=self.bob.manifest_sha256,
            selected_taste_sha256=self.bob.taste_sha256,
            blueprint_sha256=ToyBlueprint.for_lane("moving-machines").sha256,
            ranking=(
                MatchRankingEntry(
                    "bob",
                    "Bob's mechanical taste is the closest structural fit for the Wish.",
                ),
                MatchRankingEntry(
                    "alice",
                    "Alice remains viable, but her classic-edition lane is less direct.",
                ),
            ),
        )

    def test_catalog_and_assignment_are_canonical_and_content_bound(self):
        self.assertEqual(
            [item.inventor_id for item in self.catalog.personas], ["alice", "bob"]
        )
        self.assertEqual(
            PersonaCatalog.from_mapping(self.catalog.to_dict()), self.catalog
        )

        assignment = self.assignment()
        assignment.assert_context(
            wish_sha256=self.wish_sha256, catalog=self.catalog
        )
        self.assertEqual(
            NativeMatchAssignment.from_mapping(assignment.to_dict()), assignment
        )
        self.assertEqual(assignment.ranked_inventor_ids, ("bob", "alice"))
        self.assertEqual(
            assignment.blueprint_sha256,
            ToyBlueprint.for_lane(assignment.selected_lane).sha256,
        )
        payload = assignment.to_dict()
        self.assertNotIn("score", payload)
        self.assertNotIn("entrypoint", payload)
        self.assertEqual(
            set(payload["ranking"][0]), {"inventor_id", "rationale"}
        )

    def test_catalog_rejects_noncanonical_or_executable_persona_fields(self):
        unsorted = self.catalog.to_dict()
        unsorted["personas"].reverse()
        with self.assertRaisesRegex(ContractError, "canonical"):
            PersonaCatalog.from_mapping(unsorted)

        executable = self.catalog.to_dict()
        executable["personas"][0]["entrypoint"] = "python -m alice"
        with self.assertRaisesRegex(ContractError, "entry fields"):
            PersonaCatalog.from_mapping(executable)

    def test_assignment_rejects_scores_stale_hashes_and_partial_rankings(self):
        payload = self.assignment().to_dict()
        payload["model_score"] = 99
        with self.assertRaisesRegex(ContractError, "fields"):
            NativeMatchAssignment.from_mapping(payload)

        stale = self.assignment().to_dict()
        stale["ranking"][0]["rationale"] = "Different reasoning."
        with self.assertRaisesRegex(ContractError, "sha256"):
            NativeMatchAssignment.from_mapping(stale)

        partial = NativeMatchAssignment(
            wish_sha256=self.wish_sha256,
            persona_catalog_sha256=self.catalog.catalog_sha256,
            selected_inventor_id="bob",
            selected_lane="moving-machines",
            selected_manifest_sha256=self.bob.manifest_sha256,
            selected_taste_sha256=self.bob.taste_sha256,
            blueprint_sha256=ToyBlueprint.for_lane("moving-machines").sha256,
            ranking=(MatchRankingEntry("bob", "Best fit."),),
        )
        with self.assertRaisesRegex(ContractError, "every catalog persona"):
            partial.assert_context(
                wish_sha256=self.wish_sha256, catalog=self.catalog
            )

    def test_assignment_rejects_forged_selection_and_blueprint(self):
        forged = copy.deepcopy(self.assignment().to_dict())
        forged["selected_manifest_sha256"] = digest("e")
        forged.pop("assignment_sha256")
        rebuilt = NativeMatchAssignment(
            wish_sha256=forged["wish_sha256"],
            persona_catalog_sha256=forged["persona_catalog_sha256"],
            selected_inventor_id=forged["selected_inventor_id"],
            selected_lane=forged["selected_lane"],
            selected_manifest_sha256=forged["selected_manifest_sha256"],
            selected_taste_sha256=forged["selected_taste_sha256"],
            blueprint_sha256=forged["blueprint_sha256"],
            ranking=tuple(
                MatchRankingEntry.from_mapping(item) for item in forged["ranking"]
            ),
        )
        with self.assertRaisesRegex(ContractError, "immutable persona"):
            rebuilt.assert_context(
                wish_sha256=self.wish_sha256, catalog=self.catalog
            )

        with self.assertRaisesRegex(ContractError, "derived"):
            NativeMatchAssignment(
                wish_sha256=self.wish_sha256,
                persona_catalog_sha256=self.catalog.catalog_sha256,
                selected_inventor_id="bob",
                selected_lane="moving-machines",
                selected_manifest_sha256=self.bob.manifest_sha256,
                selected_taste_sha256=self.bob.taste_sha256,
                blueprint_sha256=digest("e"),
                ranking=(MatchRankingEntry("bob", "Best fit."),),
            )


if __name__ == "__main__":
    unittest.main()
