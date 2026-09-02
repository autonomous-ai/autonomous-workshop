import unittest
import tempfile
import hashlib
from types import SimpleNamespace
from dataclasses import replace
from pathlib import Path
from unittest import mock

from workshop.errors import ContractError, StateConflict
from workshop.match.native import InventorRoster, InventorRosterEntry
from workshop.workflow.agent_run import AgentRunCheckpoint
from workshop.workflow.agent_run import AgentArtifact
from workshop.workflow.effort import (
    EFFORT_ROUTE_CAPABILITY_PATH,
    INVENT_CONCEPT_CAPABILITY_PATH,
    INVENT_CONCEPT_V2_CAPABILITY_PATH,
)
from workshop.workflow.native_run import (
    _invent_concept_paths,
    _prepare_effort_stage_input,
)
from workshop.make.revision import MAKE_INVENT_REVISION_CAPABILITY_PATH


class InventConceptPacketProtocolTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run_root = Path(self.temporary.name).resolve()

    def _checkpoint(self, effort="forge", *, marked=True, simplified=False, round_index=1):
        inputs = {EFFORT_ROUTE_CAPABILITY_PATH: "a" * 64}
        if marked:
            inputs[
                INVENT_CONCEPT_V2_CAPABILITY_PATH
                if simplified else INVENT_CONCEPT_CAPABILITY_PATH
            ] = "b" * 64
        return AgentRunCheckpoint(
            product_id="invent-concept-packet",
            stage="invent",
            status="active",
            revision=0,
            round_index=round_index,
            max_rounds=4,
            wish_sha256="c" * 64,
            run_root_sha256="d" * 64,
            host_state_root_sha256="e" * 64,
            checkpoint_sha256="f" * 64,
            input_sha256s=inputs,
            inventor_roster=(),
            stage_artifacts={},
            invalidated_stages=(),
            effort=effort,
        )

    def _roster(self):
        return InventorRoster(
            (
                InventorRosterEntry(
                    "alice",
                    ".codex/agents/alice.toml",
                    "1" * 64,
                    "2" * 64,
                    "3" * 64,
                ),
            )
        )

    def test_marked_initial_invent_packet_binds_canonical_concept_paths(self):
        checkpoint = self._checkpoint()
        subject, packet, context = _prepare_effort_stage_input(
            mock.Mock(run_root=self.run_root),
            checkpoint,
            roster=self._roster(),
            cad_gate_rejection=None,
            make_proposal_rejection=None,
            playtest_proposal_rejection=None,
        )
        inputs = packet["inputs"]
        self.assertRegex(subject, r"^[0-9a-f]{64}$")
        self.assertEqual(
            inputs["invent_concept_capability"],
            {"path": INVENT_CONCEPT_CAPABILITY_PATH, "sha256": "b" * 64},
        )
        self.assertEqual(inputs["concept_root"], "artifacts/concept/r0001/concept")
        self.assertEqual(
            inputs["concept_pre_render_path"],
            "artifacts/concept/r0001/pre-render.json",
        )
        self.assertEqual(
            inputs["concept_sealed_path"],
            "artifacts/concept/r0001/sealed.json",
        )
        self.assertEqual(
            inputs["concept_effect_path"],
            "artifacts/concept/r0001/effect.json",
        )
        self.assertEqual(inputs["concept_round"], 1)
        self.assertIsNone(inputs["standing_concept_sha256"])
        self.assertIsNone(inputs["revision_input_sha256"])
        self.assertIs(context["invent_concept"], True)

    def test_unmarked_invent_packet_keeps_legacy_shape(self):
        unused_subject, packet, context = _prepare_effort_stage_input(
            mock.Mock(run_root=self.run_root),
            self._checkpoint(marked=False),
            roster=self._roster(),
            cad_gate_rejection=None,
            make_proposal_rejection=None,
            playtest_proposal_rejection=None,
        )
        inputs = packet["inputs"]
        self.assertNotIn("concept_root", inputs)
        self.assertNotIn("invent_concept", context)

    def test_simplified_packet_binds_visual_plan_without_changing_route(self):
        subject, packet, context = _prepare_effort_stage_input(
            mock.Mock(run_root=self.run_root),
            self._checkpoint(simplified=True), roster=self._roster(),
            cad_gate_rejection=None, make_proposal_rejection=None,
            playtest_proposal_rejection=None,
        )
        self.assertRegex(subject, r"^[0-9a-f]{64}$")
        self.assertEqual(packet["next_transition"], "make")
        self.assertEqual(packet["inputs"]["visual_plan_path"], "artifacts/invent/visual-plan.json")
        self.assertEqual(packet["inputs"]["invent_concept_capability"]["path"], INVENT_CONCEPT_V2_CAPABILITY_PATH)
        self.assertEqual(context["invent_concept_version"], 2)

    def test_checkpoint_cannot_mix_frozen_v1_and_v2_markers(self):
        checkpoint = self._checkpoint(simplified=True)
        checkpoint = replace(
            checkpoint,
            input_sha256s={
                **dict(checkpoint.input_sha256s),
                INVENT_CONCEPT_CAPABILITY_PATH: "9" * 64,
            },
        )
        with self.assertRaisesRegex(StateConflict, "ambiguous"):
            _prepare_effort_stage_input(
                mock.Mock(run_root=self.run_root), checkpoint,
                roster=self._roster(), cad_gate_rejection=None,
                make_proposal_rejection=None,
                playtest_proposal_rejection=None,
            )

    def test_concept_paths_are_round_scoped_and_bounded(self):
        self.assertEqual(
            _invent_concept_paths(2),
            (
                "artifacts/concept/r0002/concept",
                "artifacts/concept/r0002/pre-render.json",
                "artifacts/concept/r0002/sealed.json",
                "artifacts/concept/r0002/effect.json",
            ),
        )
        for invalid in (0, 101, "1", None):
            with self.subTest(invalid=invalid), self.assertRaises(ContractError):
                _invent_concept_paths(invalid)

    def test_revised_marked_packet_binds_standing_concept_effect_and_revision(self):
        sealed_bytes = b"sealed-contract"
        assignment_artifact = AgentArtifact(
            "artifacts/invent/assignment.json", "1" * 64
        )
        invented_artifact = AgentArtifact(
            "artifacts/invent/invented.json", "2" * 64
        )
        sealed_artifact = AgentArtifact(
            "artifacts/concept/r0001/sealed.json",
            hashlib.sha256(sealed_bytes).hexdigest(),
        )
        effect_artifact = AgentArtifact(
            "artifacts/concept/r0001/effect.json", "4" * 64
        )
        revision_artifact = AgentArtifact(
            "artifacts/make/r0001/invent-revision-request.json", "5" * 64
        )
        checkpoint = self._checkpoint(round_index=2)
        checkpoint = replace(
            checkpoint,
            input_sha256s={
                **dict(checkpoint.input_sha256s),
                MAKE_INVENT_REVISION_CAPABILITY_PATH: "6" * 64,
            },
            stage_artifacts={
                "invent": (
                    assignment_artifact, invented_artifact,
                    sealed_artifact, effect_artifact,
                ),
                "make": (revision_artifact,),
            },
            invalidated_stages=("invent", "make", "release"),
        )
        assignment = SimpleNamespace(
            assignment_sha256="7" * 64,
            to_dict=lambda: {"assignment": True},
        )
        invented = SimpleNamespace(
            invented_sha256="8" * 64,
            to_dict=lambda: {"invented": True},
        )
        revision = SimpleNamespace(
            revision_request_sha256="9" * 64,
            feedback_sha256="a" * 64,
            feedback=(SimpleNamespace(to_dict=lambda: {"feedback": True}),),
            assert_context=lambda *args, **kwargs: None,
            validate_evidence_tree=lambda *args, **kwargs: None,
            to_dict=lambda: {"revision": True},
        )
        sealed = SimpleNamespace(
            concept_sha256="b" * 64,
            validate_tree=lambda: None,
        )
        effect = SimpleNamespace(
            sealed_concept_sha256="b" * 64,
            concept_effect_sha256="c" * 64,
        )
        def read_contract(unused_root, unused_artifact, contract_type, **unused):
            return effect if contract_type.__name__ == "ConceptEffectEvidence" else revision
        with mock.patch(
            "workshop.workflow.native_run._routed_creative_context",
            return_value=(
                assignment, invented, assignment_artifact, invented_artifact,
                SimpleNamespace(),
            ),
        ), mock.patch(
            "workshop.workflow.native_run.read_bounded_json_artifact",
            return_value=({}, sealed_bytes),
        ), mock.patch(
            "workshop.workflow.native_run.SealedConcept.from_mapping",
            return_value=sealed,
        ), mock.patch(
            "workshop.workflow.native_run._read_contract",
            side_effect=read_contract,
        ):
            subject, packet, context = _prepare_effort_stage_input(
                mock.Mock(run_root=self.run_root),
                checkpoint,
                roster=self._roster(),
                cad_gate_rejection=None,
                make_proposal_rejection=None,
                playtest_proposal_rejection=None,
            )
        inputs = packet["inputs"]
        self.assertRegex(subject, r"^[0-9a-f]{64}$")
        self.assertEqual(inputs["concept_round"], 2)
        self.assertEqual(inputs["standing_concept_sha256"], "b" * 64)
        self.assertEqual(inputs["revision_input_sha256"], "9" * 64)
        self.assertEqual(
            inputs["prior_concept_artifact"], sealed_artifact.to_dict()
        )
        self.assertEqual(
            inputs["prior_concept_effect_artifact"], effect_artifact.to_dict()
        )
        self.assertEqual(context["standing_concept_sha256"], "b" * 64)


if __name__ == "__main__":
    unittest.main()
