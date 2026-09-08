"""Host recovery for finalized proposals the protocol refuses.

A proposal the host cannot apply -- a backward edge on the final
Invent-Make-Playtest round, a Release contract the host rejects -- used to
leave ``agent-outcome.json`` in place so every resume re-read and re-refused
the same bytes.  These tests pin the durable failed outcome that replaces the
wedge, and that the gate decision persisted before the refusal survives.
"""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.errors import ContractError, StateConflict, TransitionError
from workshop.workflow.agent_run import (
    AgentArtifact,
    AgentOutcome,
    AgentRun,
    DeterministicGateReceipt,
)
from workshop.workflow.native_run import (
    _agent_outcome_exists,
    _process_agent_outcome_inner,
)
from workshop.workflow.proposals import AgentOutcomeProposal
from workshop.workflow.stage_gates import StageGateDecision, StageGateEvidence


EVIDENCE_SHA256 = "e" * 64
SUBJECT_SHA256 = "5" * 64


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


class RefusedProposalRecoveryTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        constitution = self.root / "source" / ".agents" / "product-run" / "AGENTS.md"
        constitution.parent.mkdir(parents=True)
        constitution.write_bytes(b"# Product run constitution\n")
        skill = self.root / "skill"
        skill.mkdir()
        (skill / "SKILL.md").write_bytes(b"# Workshop skill\n")
        (skill / "references").mkdir()
        (skill / "references" / "make-playtest.md").write_bytes(b"exact gate guidance\n")
        (skill / "references" / "release-terminal-v1.md").write_bytes(
            b"terminal Release capability\n"
        )
        self.constitution = constitution
        self.skill = skill
        self.product_id = "wish-refusal-1"
        self.run = self._create()

    def _create(self, name="run", **arguments):
        return AgentRun.create(
            self.root / name,
            host_state_root=self.root / (name + "-host-state"),
            product_id=self.product_id,
            wish_bytes=_canonical(
                {
                    "schema_version": 1,
                    "product_id": self.product_id,
                    "objective": "Make a clockwork moon.",
                    "constraints": {},
                    "context": {"source": "refused-proposal-test"},
                }
            ),
            product_run_constitution_source=self.constitution,
            skill_root=self.skill,
            max_rounds=1,
            **arguments,
        )

    # -- helpers ---------------------------------------------------------

    def artifact(self, stage, name, content):
        relative = "artifacts/%s/%s" % (stage, name)
        path = self.run.run_root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return AgentArtifact(relative, hashlib.sha256(content).hexdigest())

    def advance(self, stage, transition):
        outcome = AgentOutcome(
            stage=stage,
            status="ready",
            artifacts=(
                self.artifact(stage, stage + ".json", b'{"stage":"%s"}\n' % stage.encode()),
            ),
            proposed_transition=transition,
        )
        gate = DeterministicGateReceipt(
            stage=stage,
            gate_id=stage + "-deterministic-gate",
            passed=True,
            subject_sha256=self.run.expected_gate_subject_sha256(),
            outcome_sha256=outcome.sha256,
            evidence_sha256=EVIDENCE_SHA256,
        )
        return self.run.apply_outcome(outcome, gate=gate)

    def write_proposal(self, outcome):
        checkpoint = self.run.snapshot()
        proposal = AgentOutcomeProposal(
            checkpoint_sha256=checkpoint.checkpoint_sha256,
            subject_sha256=SUBJECT_SHA256,
            outcome=outcome,
        )
        (self.run.run_root / "agent-outcome.json").write_bytes(
            _canonical(proposal.to_dict())
        )
        return proposal

    def decision(self, checkpoint, proposal, *, passed, transition):
        artifact = proposal.outcome.artifacts[0]
        evidence = StageGateEvidence(
            stage=checkpoint.stage,
            gate_id="%s.test-gate" % checkpoint.stage,
            validator_version="1.0.0",
            passed=passed,
            checkpoint_sha256=checkpoint.checkpoint_sha256,
            subject_sha256=SUBJECT_SHA256,
            outcome_sha256=proposal.outcome.sha256,
            artifact_path=artifact.path,
            artifact_sha256=artifact.sha256,
            checks={"fixture": True},
        )
        return StageGateDecision(evidence=evidence, transition=transition)

    def process(self, context):
        checkpoint = self.run.snapshot()
        return _process_agent_outcome_inner(
            self.run,
            checkpoint,
            subject_sha256=SUBJECT_SHA256,
            context=context,
            pending_proposal=None,
            timing_observer=None,
        )

    def reach_playtest(self):
        for stage, transition in (
            ("wish", "match"),
            ("match", "invent"),
            ("invent", "make"),
            ("make", "playtest"),
        ):
            self.advance(stage, transition)

    # -- tests -----------------------------------------------------------

    def test_final_round_playtest_backward_edge_fails_durably(self):
        self.reach_playtest()
        checkpoint = self.run.snapshot()
        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("playtest", 1))
        self.assertEqual(checkpoint.max_rounds, 1)
        outcome = AgentOutcome(
            stage="playtest",
            status="ready",
            artifacts=(
                self.artifact(
                    "playtest", "r0001/playtested.json", b'{"verdict":"improve"}\n'
                ),
            ),
            proposed_transition="make",
        )
        proposal = self.write_proposal(outcome)
        decision = self.decision(checkpoint, proposal, passed=False, transition="make")
        recorded = []
        with mock.patch(
            "workshop.workflow.native_run._evaluate_playtest_stage",
            return_value=(decision, ()),
        ), mock.patch(
            "workshop.workflow.native_run._record_playtest_evidence",
            side_effect=lambda *arguments: recorded.append(arguments),
        ):
            updated = self.process({})

        # The refusal is durable and truthful ...
        self.assertEqual(updated.status, "failed")
        self.assertEqual(updated.stage, "playtest")
        self.assertEqual(updated.round_index, 1)
        self.assertEqual(len(updated.needs), 1)
        self.assertIn("refused the finalized playtest transition to make", updated.needs[0])
        self.assertIn("round budget is exhausted", updated.needs[0])
        self.assertIn("final round", updated.needs[0])
        # ... the gate decision and Playtest evidence banked before it remain ...
        gates = sorted((self.run.host_state_root / "gates").glob("*-playtest.json"))
        self.assertEqual(len(gates), 1)
        self.assertEqual(
            json.loads(gates[0].read_bytes())["evidence"]["outcome_sha256"],
            proposal.outcome.sha256,
        )
        self.assertEqual(len(recorded), 1)
        # ... and the stale proposal is gone so a resume cannot loop on it.
        self.assertFalse(_agent_outcome_exists(self.run.run_root))
        self.assertEqual(self.run.snapshot().status, "failed")
        with self.assertRaises(TransitionError):
            self.run.validate_outcome(outcome)

    def test_final_round_make_invent_revision_fails_durably(self):
        # A capable Forge run: the Make->Invent edge exists, but not on the
        # final round.
        references = self.skill / "references"
        (references / "effort-routes-v1.md").write_bytes(b"effort routes\n")
        (references / "make-invent-revision-v1.md").write_bytes(
            b"Make Invent revision capability\n"
        )
        self.run = self._create("forge-run", effort="forge")
        for stage, transition in (("wish", "invent"), ("invent", "make")):
            self.advance(stage, transition)
        checkpoint = self.run.snapshot()
        self.assertEqual((checkpoint.stage, checkpoint.round_index), ("make", 1))
        request = self.artifact(
            "make", "r0001/invent-revision-request.json", b'{"feedback":[]}\n'
        )
        source = self.artifact(
            "make", "r0001/invent-revision-source.json", b'{"feedback":[]}\n'
        )
        outcome = AgentOutcome(
            stage="make",
            status="ready",
            artifacts=(request, source),
            proposed_transition="invent",
        )
        self.write_proposal(outcome)

        updated = self.process(
            {"make_invent_revision_allowed": True, "make_transition": "release"}
        )

        self.assertEqual(updated.status, "failed")
        self.assertEqual(updated.stage, "make")
        self.assertIn("refused the finalized Make->Invent revision", updated.needs[0])
        self.assertIn("round budget is exhausted", updated.needs[0])
        self.assertFalse(_agent_outcome_exists(self.run.run_root))
        self.assertEqual(self.run.snapshot().status, "failed")

    def test_release_contract_rejection_fails_durably_with_the_host_reason(self):
        self.reach_playtest()
        self.advance("playtest", "release")
        checkpoint = self.run.snapshot()
        self.assertEqual(checkpoint.stage, "release")
        outcome = AgentOutcome(
            stage="release",
            status="ready",
            artifacts=(
                self.artifact("release", "release.json", b'{"release":true}\n'),
            ),
            proposed_transition="complete",
        )
        self.write_proposal(outcome)
        context = {"terminal_transition": "complete"}

        with mock.patch(
            "workshop.workflow.native_run._evaluate_release_stage",
            side_effect=ContractError(
                "native Release title differs from the exact Made product"
            ),
        ):
            updated = self.process(context)

        self.assertEqual(updated.status, "failed")
        self.assertEqual(updated.stage, "release")
        self.assertIn("rejected the sealed Release contract", updated.needs[0])
        self.assertIn("title differs from the exact Made product", updated.needs[0])
        self.assertFalse(_agent_outcome_exists(self.run.run_root))
        self.assertEqual(self.run.snapshot().status, "failed")

    def test_release_state_conflict_remains_fatal(self):
        # A host state conflict is still fatal, never converted into an
        # agent-facing failure.
        self.reach_playtest()
        self.advance("playtest", "release")
        outcome = AgentOutcome(
            stage="release",
            status="ready",
            artifacts=(
                self.artifact("release", "release.json", b'{"release":true}\n'),
            ),
            proposed_transition="complete",
        )
        self.write_proposal(outcome)
        with mock.patch(
            "workshop.workflow.native_run._evaluate_release_stage",
            side_effect=StateConflict("native run lacks its frozen Release transition"),
        ):
            with self.assertRaisesRegex(StateConflict, "frozen Release transition"):
                self.process({"terminal_transition": "complete"})
        self.assertTrue(_agent_outcome_exists(self.run.run_root))
        self.assertEqual(self.run.snapshot().status, "active")

    def test_host_need_text_is_bounded_single_line(self):
        from workshop.workflow.native_run import _host_need_text

        self.assertEqual(_host_need_text("  a\x00b\r\nc  "), "a b  c")
        self.assertEqual(_host_need_text(""), "the host refused the finalized proposal")
        long = _host_need_text("x" * 5_000)
        self.assertEqual(len(long), 1_024)
        self.assertTrue(long.endswith("..."))
        AgentOutcome(stage="release", status="failed", needs=(long,))


if __name__ == "__main__":
    unittest.main()
