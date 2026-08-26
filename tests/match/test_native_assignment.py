import copy
import unittest

from workshop.errors import ContractError
from workshop.match.native import (
    MatchRankingEntry,
    NativeMatchAssignment,
    InventorRoster,
    InventorRosterEntry,
)
from workshop.product.blueprints import ToyBlueprint


def digest(character):
    return character * 64


class NativeMatchAssignmentTest(unittest.TestCase):
    def setUp(self):
        self.wish_sha256 = digest("f")
        self.alice = InventorRosterEntry(
            inventor_id="alice",
            agent_path=".codex/agents/alice.toml",
            agent_sha256=digest("a"),
            source_manifest_sha256=digest("b"),
            taste_sha256=digest("c"),
        )
        self.bob = InventorRosterEntry(
            inventor_id="bob",
            agent_path=".codex/agents/bob.toml",
            agent_sha256=digest("d"),
            source_manifest_sha256=digest("e"),
            taste_sha256=digest("0"),
        )
        self.roster = InventorRoster((self.bob, self.alice))

    def assignment(self):
        return NativeMatchAssignment(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="bob",
            selected_agent_path=self.bob.agent_path,
            selected_agent_sha256=self.bob.agent_sha256,
            selected_source_manifest_sha256=self.bob.source_manifest_sha256,
            selected_taste_sha256=self.bob.taste_sha256,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(
                MatchRankingEntry(
                    "bob",
                    "Bob's mechanical taste is the closest structural fit for the Wish.",
                ),
                MatchRankingEntry(
                    "alice",
                    "Alice remains viable, but Bob's taste is a more direct fit.",
                ),
            ),
        )

    def test_roster_and_assignment_are_canonical_and_content_bound(self):
        self.assertEqual(
            [item.inventor_id for item in self.roster.inventors], ["alice", "bob"]
        )
        self.assertEqual(
            InventorRoster.from_mapping(self.roster.to_dict()), self.roster
        )

        assignment = self.assignment()
        assignment.assert_context(
            wish_sha256=self.wish_sha256, roster=self.roster
        )
        self.assertEqual(
            NativeMatchAssignment.from_mapping(assignment.to_dict()), assignment
        )
        self.assertEqual(assignment.ranked_inventor_ids, ("bob", "alice"))
        self.assertEqual(
            assignment.blueprint_sha256,
            ToyBlueprint().sha256,
        )
        payload = assignment.to_dict()
        self.assertNotIn("score", payload)
        self.assertNotIn("entrypoint", payload)
        self.assertNotIn("lane", payload)
        self.assertEqual(payload["schema_version"], 3)
        self.assertEqual(
            set(payload["ranking"][0]), {"inventor_id", "rationale"}
        )

    def test_roster_rejects_noncanonical_or_executable_inventor_fields(self):
        unsorted = self.roster.to_dict()
        unsorted["inventors"].reverse()
        with self.assertRaisesRegex(ContractError, "canonical"):
            InventorRoster.from_mapping(unsorted)

        executable = self.roster.to_dict()
        executable["inventors"][0]["entrypoint"] = "python -m alice"
        with self.assertRaisesRegex(ContractError, "entry fields"):
            InventorRoster.from_mapping(executable)

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
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="bob",
            selected_agent_path=self.bob.agent_path,
            selected_agent_sha256=self.bob.agent_sha256,
            selected_source_manifest_sha256=self.bob.source_manifest_sha256,
            selected_taste_sha256=self.bob.taste_sha256,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(MatchRankingEntry("bob", "Best fit."),),
        )
        with self.assertRaisesRegex(ContractError, "every roster inventor"):
            partial.assert_context(
                wish_sha256=self.wish_sha256, roster=self.roster
            )

    def test_assignment_rejects_forged_selection_and_blueprint(self):
        forged = copy.deepcopy(self.assignment().to_dict())
        forged["selected_agent_sha256"] = digest("1")
        forged.pop("assignment_sha256")
        rebuilt = NativeMatchAssignment(
            wish_sha256=forged["wish_sha256"],
            inventor_roster_sha256=forged["inventor_roster_sha256"],
            selected_inventor_id=forged["selected_inventor_id"],
            selected_agent_path=forged["selected_agent_path"],
            selected_agent_sha256=forged["selected_agent_sha256"],
            selected_source_manifest_sha256=forged[
                "selected_source_manifest_sha256"
            ],
            selected_taste_sha256=forged["selected_taste_sha256"],
            blueprint_sha256=forged["blueprint_sha256"],
            ranking=tuple(
                MatchRankingEntry.from_mapping(item) for item in forged["ranking"]
            ),
        )
        with self.assertRaisesRegex(ContractError, "immutable inventor"):
            rebuilt.assert_context(
                wish_sha256=self.wish_sha256, roster=self.roster
            )

        with self.assertRaisesRegex(ContractError, "open-ended Workshop baseline"):
            NativeMatchAssignment(
                wish_sha256=self.wish_sha256,
                inventor_roster_sha256=self.roster.roster_sha256,
                selected_inventor_id="bob",
                selected_agent_path=self.bob.agent_path,
                selected_agent_sha256=self.bob.agent_sha256,
                selected_source_manifest_sha256=self.bob.source_manifest_sha256,
                selected_taste_sha256=self.bob.taste_sha256,
                blueprint_sha256=digest("e"),
                ranking=(MatchRankingEntry("bob", "Best fit."),),
            )


if __name__ == "__main__":
    unittest.main()
