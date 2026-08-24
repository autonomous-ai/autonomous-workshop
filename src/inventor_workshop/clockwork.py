"""The Make -> Playtest -> done workflow and Clockwork compatibility API."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .cad import CadReleaseBundle
from .errors import ContractError, StampError, TransitionError
from .lifecycle import GatePolicy, Pipeline, PipelineSpec, _default_gate_policy
from .models import Stamp
from .pack import PackedArtifact
from .playtest import Playtest
from .runtime import Runtime


# Compatibility name used through Workshop 0.3.  There is one implementation:
# new inventors construct Runtime directly.
Clockwork = Runtime


PlaytestPolicy = GatePolicy
InspectionPolicy = PlaytestPolicy


class WorkflowSpec(PipelineSpec):
    """Canonical small graph; inventors may supply a stricter workflow."""

    @classmethod
    def _direct(cls, profile: str, playtest_ids: tuple[str, ...]) -> "WorkflowSpec":
        stages = ("make", "playtest", "done")
        edges = {
            "make": ("playtest",),
            "playtest": ("make", "done"),
            "done": (),
        }
        return cls(
            initial_stage="make",
            stages=stages,
            edges=edges,
            required_gates={"playtest": playtest_ids},
            gate_policies={
                name: _default_gate_policy(profile, name)
                for name in playtest_ids
            },
        )

    @classmethod
    def board_game(cls) -> "WorkflowSpec":
        return cls._direct(
            "board-game",
            ("rules-lint", "cad", "printability", "playtest", "novelty"),
        )

    @classmethod
    def physical_product(cls) -> "WorkflowSpec":
        return cls._direct(
            "physical-product",
            ("cad", "printability", "safety", "form", "novelty"),
        )

    @classmethod
    def custom(cls) -> "WorkflowSpec":
        return cls._direct("custom", ("quality", "safety"))


class Workflow(Pipeline):
    """Canonical lifecycle that accepts artifact-bound Playtest feedback."""

    def advance(
        self,
        clockwork: Clockwork,
        product_id: str,
        to_stage: str,
        expected_revision: int,
        *,
        playtest: Optional[Playtest] = None,
        inspection: Optional[Playtest] = None,
        packed: Optional[PackedArtifact] = None,
        artifact_sha256: Optional[str] = None,
        cad_release: Optional[CadReleaseBundle] = None,
        stamp: Optional[Stamp] = None,
        pack_sha256: Optional[str] = None,
        send_intent_id: Optional[str] = None,
        expected_shop_owner_id: Optional[str] = None,
        lease_token: Optional[str] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        if playtest is None:
            playtest = inspection
        elif inspection is not None and playtest != inspection:
            raise TransitionError(
                "Workflow received conflicting playtest and inspection evidence"
            )
        product = clockwork.get_product(product_id)
        required = self._required.get(to_stage, set())
        if required and not isinstance(playtest, Playtest):
            evidence_name = "Inspection" if to_stage == "inspect" else "Playtest"
            raise TransitionError(
                "canonical Workflow transitions with checks require a %s"
                % evidence_name
            )
        inspection_evidence_sha256 = None
        if playtest is not None:
            playtest.assert_valid()
            playtest.require(required)
            inspection_evidence_sha256 = playtest.evidence_artifact_sha256
            if cad_release is None:
                cad_release = playtest.cad_release
            elif (
                playtest.cad_release is not None
                and cad_release != playtest.cad_release
            ):
                raise TransitionError(
                    "CAD release differs from the artifact-bound Playtest"
                )
            selected = artifact_sha256 or playtest.artifact_sha256
            if selected != playtest.artifact_sha256:
                raise TransitionError(
                    "Playtest belongs to different artifact bytes"
                )
            artifact_sha256 = selected
            results = playtest.results
        else:
            results = ()
        # Playtest can supply the artifact identity when the caller omits
        # ``artifact_sha256``. Derive that effective identity before applying
        # the post-Playtest immutability fence; otherwise feedback for B could
        # silently replace the product's already accepted artifact A.
        if (
            product["stage"] in ("playtest", "inspect", "pack", "done")
            and artifact_sha256 is not None
            and artifact_sha256 != product.get("artifact_sha256")
        ):
            completed_stage = (
                "Inspect" if product["stage"] == "inspect" else "Playtest"
            )
            raise TransitionError(
                "artifact bytes cannot change after %s; return to Make"
                % completed_stage
            )
        event_pack_sha256 = pack_sha256
        if to_stage == "pack":
            if not isinstance(packed, PackedArtifact):
                raise TransitionError(
                    "Pack transition requires a validated PackedArtifact"
                )
            try:
                packed.assert_valid()
            except ContractError as exc:
                raise TransitionError("PackedArtifact is malformed") from exc
            selected_artifact = artifact_sha256 or product.get("artifact_sha256")
            if selected_artifact is None:
                raise TransitionError(
                    "Pack transition requires an existing artifact identity"
                )
            if packed.artifact_sha256 != selected_artifact:
                raise TransitionError(
                    "PackedArtifact belongs to different artifact bytes"
                )
            if pack_sha256 is not None and pack_sha256 != packed.pack_sha256:
                raise TransitionError(
                    "pack_sha256 differs from the structured PackedArtifact"
                )
            artifact_sha256 = selected_artifact
            event_pack_sha256 = packed.pack_sha256
        elif packed is not None:
            raise TransitionError(
                "PackedArtifact is accepted only for a transition to Pack"
            )
        if to_stage == "send":
            if stamp is None or pack_sha256 is None or send_intent_id is None:
                raise TransitionError(
                    "Send requires a durable send intent, exact Pack identity, and Stamp"
                )
            selected_artifact = artifact_sha256 or product.get("artifact_sha256")
            try:
                stamp.assert_pack(pack_sha256)
                stamp.assert_artifact(selected_artifact)
                intent = clockwork.get_send_intent(send_intent_id)
                durable_stamp = Stamp.from_dict(intent.get("stamp"))
            except (KeyError, ContractError, StampError, TypeError, ValueError) as exc:
                raise TransitionError("Send intent or Stamp is malformed") from exc
            if (
                intent.get("product_id") != product_id
                or intent.get("state") != "succeeded"
                or intent.get("pack_sha256") != pack_sha256
                or intent.get("artifact_sha256") != selected_artifact
                or durable_stamp != stamp
            ):
                raise TransitionError(
                    "Stamp is not the exact durable Sender result for this product"
                )
            events = clockwork.events(product_id)
            prior_event = events[-1] if events else None
            prior_payload = (
                prior_event.get("payload", {})
                if prior_event is not None
                else {}
            )
            recorded_pack_sha256 = (
                prior_payload.get("pack_sha256")
                if isinstance(prior_payload, Mapping)
                else None
            )
            if (
                prior_event is not None
                and prior_event.get("kind") == "transition"
                and prior_event.get("to_stage") == "pack"
                # Pre-0.3 in-flight rows can have a Pack event without this
                # field. New typed Pack transitions always record it.
                and recorded_pack_sha256 is not None
                and recorded_pack_sha256 != pack_sha256
            ):
                raise TransitionError(
                    "Send Pack differs from the Pack recorded by Clockwork"
                )
        return super().advance(
            clockwork,
            product_id,
            to_stage,
            expected_revision,
            artifact_sha256=artifact_sha256,
            gates=results,
            cad_release=cad_release,
            receipt=stamp,
            publication_packet_sha256=event_pack_sha256,
            publication_intent_id=send_intent_id,
            expected_owner_id=expected_shop_owner_id,
            lease_token=lease_token,
            note=note,
            inspection_evidence_sha256=inspection_evidence_sha256,
        )
