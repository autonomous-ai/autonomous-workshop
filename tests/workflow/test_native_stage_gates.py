import copy
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.errors import ArtifactError, ContractError, StateConflict
from workshop.invent.native import NativeInvented
from workshop.match.native import (
    InventorRoster,
    InventorRosterEntry,
    MatchRankingEntry,
    NativeMatchAssignment,
)
from workshop.product.blueprints import ToyBlueprint
from workshop.wish import Wish
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome
from workshop.workflow.proposals import (
    AgentOutcomeProposal,
    MAX_AGENT_OUTCOME_PROPOSAL_BYTES,
    read_agent_outcome_proposal,
)
from workshop.workflow.stage_gates import (
    INVENTED_PATH,
    INVENT_GATE_ID,
    MATCH_ASSIGNMENT_PATH,
    MATCH_GATE_ID,
    StageGateEvidence,
    concept_gate_subject_sha256,
    evaluate_concept_stage,
    evaluate_invent_stage,
    evaluate_match_stage,
    invent_gate_subject_sha256,
    match_gate_subject_sha256,
)


def canonical_json(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def digest(character):
    return character * 64


class NativeStageGateTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.run_root = self.root / "run"
        self.run_root.mkdir()
        self.wish_sha256 = digest("f")
        self.checkpoint_sha256 = digest("e")
        alice = InventorRosterEntry(
            inventor_id="alice",
            agent_path=".codex/agents/alice.toml",
            agent_sha256=digest("a"),
            source_manifest_sha256=digest("1"),
            taste_sha256=digest("b"),
        )
        bob = InventorRosterEntry(
            inventor_id="bob",
            agent_path=".codex/agents/bob.toml",
            agent_sha256=digest("c"),
            source_manifest_sha256=digest("2"),
            taste_sha256=digest("d"),
        )
        self.roster = InventorRoster((alice, bob))
        self.assignment = NativeMatchAssignment(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
            selected_inventor_id="bob",
            selected_agent_path=bob.agent_path,
            selected_agent_sha256=bob.agent_sha256,
            selected_source_manifest_sha256=bob.source_manifest_sha256,
            selected_taste_sha256=bob.taste_sha256,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(
                MatchRankingEntry(
                    "bob", "The mechanism-first specialist is the closest structural fit."
                ),
                MatchRankingEntry(
                    "alice", "The classic-game specialist is valid but less direct."
                ),
            ),
        )

    def artifact(self, relative, document):
        content = canonical_json(document)
        path = self.run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return AgentArtifact(relative, hashlib.sha256(content).hexdigest())

    def ready_proposal(self, stage, transition, artifact, subject, checkpoint=None):
        return AgentOutcomeProposal(
            checkpoint_sha256=checkpoint or self.checkpoint_sha256,
            subject_sha256=subject,
            outcome=AgentOutcome(
                stage=stage,
                status="ready",
                artifacts=(artifact,),
                proposed_transition=transition,
            ),
        )

    def write_proposal(self, proposal):
        (self.run_root / "agent-outcome.json").write_bytes(
            canonical_json(proposal.to_dict())
        )

    def test_strict_reader_binds_checkpoint_and_full_subject(self):
        artifact = self.artifact(MATCH_ASSIGNMENT_PATH, self.assignment.to_dict())
        subject = match_gate_subject_sha256(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
        )
        proposal = self.ready_proposal("match", "invent", artifact, subject)
        self.write_proposal(proposal)

        observed = read_agent_outcome_proposal(
            self.run_root,
            expected_checkpoint_sha256=self.checkpoint_sha256,
            expected_subject_sha256=subject,
        )
        self.assertEqual(observed, proposal)
        with self.assertRaisesRegex(StateConflict, "another checkpoint"):
            read_agent_outcome_proposal(
                self.run_root,
                expected_checkpoint_sha256=digest("0"),
                expected_subject_sha256=subject,
            )
        with self.assertRaisesRegex(StateConflict, "another gate subject"):
            read_agent_outcome_proposal(
                self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                expected_subject_sha256=digest("1"),
            )

    def test_reader_rejects_duplicate_keys_symlinks_and_oversize_files(self):
        artifact = self.artifact(MATCH_ASSIGNMENT_PATH, self.assignment.to_dict())
        subject = match_gate_subject_sha256(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
        )
        proposal = self.ready_proposal("match", "invent", artifact, subject)
        encoded = canonical_json(proposal.to_dict())
        duplicate = encoded.replace(
            b'"kind":', b'"kind":"duplicate","kind":', 1
        )
        (self.run_root / "agent-outcome.json").write_bytes(duplicate)
        with self.assertRaisesRegex(ContractError, "strict UTF-8 JSON"):
            read_agent_outcome_proposal(
                self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                expected_subject_sha256=subject,
            )

        outcome_path = self.run_root / "agent-outcome.json"
        outcome_path.unlink()
        real = self.root / "outside-agent-outcome.json"
        real.write_bytes(encoded)
        os.symlink(real, outcome_path)
        with self.assertRaisesRegex(ArtifactError, "without following links"):
            read_agent_outcome_proposal(
                self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                expected_subject_sha256=subject,
            )

        outcome_path.unlink()
        outcome_path.write_bytes(b"{" + b" " * MAX_AGENT_OUTCOME_PROPOSAL_BYTES + b"}")
        with self.assertRaisesRegex(ArtifactError, "at most"):
            read_agent_outcome_proposal(
                self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                expected_subject_sha256=subject,
            )

    def test_match_and_invent_gates_derive_host_receipts(self):
        match_artifact = self.artifact(
            MATCH_ASSIGNMENT_PATH, self.assignment.to_dict()
        )
        match_subject = match_gate_subject_sha256(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
        )
        match_proposal = self.ready_proposal(
            "match", "invent", match_artifact, match_subject
        )
        match_decision = evaluate_match_stage(
            match_proposal,
            run_root=self.run_root,
            expected_checkpoint_sha256=self.checkpoint_sha256,
            wish_sha256=self.wish_sha256,
            roster=self.roster,
        )
        self.assertTrue(match_decision.passed)
        self.assertEqual(match_decision.transition, "invent")
        self.assertEqual(match_decision.receipt.gate_id, MATCH_GATE_ID)
        self.assertEqual(match_decision.receipt.subject_sha256, match_subject)
        self.assertEqual(
            StageGateEvidence.from_mapping(match_decision.evidence.to_dict()),
            match_decision.evidence,
        )

        invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={
                "title": "Moonstep Orrery",
                "summary": "A wound crank turns the Wish into a visible lunar gait.",
            },
            research={
                "sources": [
                    {
                        "url": "https://example.test/cranks",
                        "claim": "Cranks translate rotary motion into periodic travel.",
                    }
                ]
            },
        )
        invent_artifact = self.artifact(INVENTED_PATH, invented.to_dict())
        invent_subject = invent_gate_subject_sha256(self.assignment)
        invent_proposal = self.ready_proposal(
            "invent",
            "concept",
            invent_artifact,
            invent_subject,
            checkpoint=digest("9"),
        )
        invent_decision = evaluate_invent_stage(
            invent_proposal,
            run_root=self.run_root,
            expected_checkpoint_sha256=digest("9"),
            assignment=self.assignment,
        )
        self.assertTrue(invent_decision.passed)
        self.assertEqual(invent_decision.transition, "concept")
        self.assertEqual(invent_decision.receipt.gate_id, INVENT_GATE_ID)
        self.assertEqual(invent_decision.receipt.subject_sha256, invent_subject)
        self.assertEqual(
            invent_decision.evidence.checks["concept_sha256"],
            invented.concept_sha256,
        )

    def test_subjects_are_domain_separated_complete_input_vectors(self):
        match_subject = match_gate_subject_sha256(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
        )
        different_roster = InventorRoster(
            self.roster.inventors
            + (
                InventorRosterEntry(
                    "eve",
                    ".codex/agents/eve.toml",
                    digest("3"),
                    digest("4"),
                    digest("5"),
                ),
            )
        )
        self.assertNotEqual(
            match_subject,
            match_gate_subject_sha256(
                wish_sha256=self.wish_sha256,
                inventor_roster_sha256=different_roster.roster_sha256,
            ),
        )
        self.assertNotEqual(match_subject, invent_gate_subject_sha256(self.assignment))

        changed_payload = copy.deepcopy(self.assignment.to_dict())
        changed_payload["ranking"][0]["rationale"] = "A changed bound rationale."
        changed_payload.pop("assignment_sha256")
        changed = NativeMatchAssignment(
            wish_sha256=changed_payload["wish_sha256"],
            inventor_roster_sha256=changed_payload["inventor_roster_sha256"],
            selected_inventor_id=changed_payload["selected_inventor_id"],
            selected_agent_path=changed_payload["selected_agent_path"],
            selected_agent_sha256=changed_payload["selected_agent_sha256"],
            selected_source_manifest_sha256=changed_payload[
                "selected_source_manifest_sha256"
            ],
            selected_taste_sha256=changed_payload["selected_taste_sha256"],
            blueprint_sha256=changed_payload["blueprint_sha256"],
            ranking=tuple(
                MatchRankingEntry.from_mapping(item)
                for item in changed_payload["ranking"]
            ),
        )
        self.assertNotEqual(
            invent_gate_subject_sha256(self.assignment),
            invent_gate_subject_sha256(changed),
        )

    def test_gates_reject_wrong_paths_subjects_and_changed_bytes(self):
        subject = match_gate_subject_sha256(
            wish_sha256=self.wish_sha256,
            inventor_roster_sha256=self.roster.roster_sha256,
        )
        wrong_path = self.artifact(
            "artifacts/match/other.json", self.assignment.to_dict()
        )
        with self.assertRaisesRegex(ContractError, "reference exactly"):
            evaluate_match_stage(
                self.ready_proposal("match", "invent", wrong_path, subject),
                run_root=self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                wish_sha256=self.wish_sha256,
                roster=self.roster,
            )

        artifact = self.artifact(MATCH_ASSIGNMENT_PATH, self.assignment.to_dict())
        with self.assertRaisesRegex(StateConflict, "another checkpoint"):
            evaluate_match_stage(
                self.ready_proposal("match", "invent", artifact, subject),
                run_root=self.run_root,
                expected_checkpoint_sha256=digest("2"),
                wish_sha256=self.wish_sha256,
                roster=self.roster,
            )

        with self.assertRaisesRegex(StateConflict, "input vector"):
            evaluate_match_stage(
                self.ready_proposal("match", "invent", artifact, digest("0")),
                run_root=self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                wish_sha256=self.wish_sha256,
                roster=self.roster,
            )

        (self.run_root / MATCH_ASSIGNMENT_PATH).write_bytes(b"{}")
        with self.assertRaisesRegex(StateConflict, "artifact sha256"):
            evaluate_match_stage(
                self.ready_proposal("match", "invent", artifact, subject),
                run_root=self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                wish_sha256=self.wish_sha256,
                roster=self.roster,
            )

    def test_concept_gate_rejects_contract_from_an_earlier_round(self):
        invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={
                "title": "Moonstep Orrery",
                "summary": "A wound crank turns the Wish into a visible lunar gait.",
            },
            research={"sources": []},
        )
        subject = concept_gate_subject_sha256(
            self.assignment,
            invented,
            round=2,
            standing_concept_sha256=digest("3"),
            feedback_sha256=digest("4"),
        )
        artifact = self.artifact(
            "artifacts/concept/r0002/concept.json",
            {"copied_from": "round-one"},
        )
        proposal = self.ready_proposal(
            "concept", "make", artifact, subject
        )
        stale_concept = mock.Mock(round=1, images_rendered=False)
        stale_concept.assert_context = mock.Mock()
        image_effect = mock.Mock()

        with mock.patch(
            "workshop.workflow.stage_gates.NativeConcept.from_mapping",
            return_value=stale_concept,
        ), self.assertRaisesRegex(ContractError, "different Workshop round"):
            evaluate_concept_stage(
                proposal,
                run_root=self.run_root,
                expected_checkpoint_sha256=self.checkpoint_sha256,
                assignment=self.assignment,
                invented=invented,
                wish=Wish.create("moonstep", "Build a mechanical lunar toy"),
                round=2,
                standing_concept_sha256=digest("3"),
                feedback_sha256=digest("4"),
                execute_image_effect=image_effect,
            )

        stale_concept.assert_context.assert_not_called()
        image_effect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
