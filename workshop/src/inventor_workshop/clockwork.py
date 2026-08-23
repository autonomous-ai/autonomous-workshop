"""Durable Workflow machinery: state, transitions, leases, budgets, and inspection."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

from .cad import CadReleaseBundle
from .errors import ContractError, StampError, TransitionError
from .inspection import Inspection
from .lifecycle import GatePolicy, Pipeline, PipelineSpec, _default_gate_policy
from .models import Stamp
from .store import InventorStore


class Clockwork(InventorStore):
    """The Workshop's durable state and effect-fencing store."""


InspectionPolicy = GatePolicy


class WorkflowSpec(PipelineSpec):
    """Canonical backstage graph; inventors may supply a stricter workflow."""

    @classmethod
    def _direct(cls, profile: str, inspection_ids: tuple[str, ...]) -> "WorkflowSpec":
        stages = ("make", "inspect", "pack", "send", "parked", "killed")
        edges = {
            "make": ("inspect", "parked", "killed"),
            "inspect": ("pack", "make", "parked", "killed"),
            "pack": ("send", "killed"),
            "send": (),
            "parked": ("make", "inspect", "pack", "killed"),
            "killed": (),
        }
        return cls(
            initial_stage="make",
            stages=stages,
            edges=edges,
            required_gates={"inspect": inspection_ids},
            gate_policies={
                name: _default_gate_policy(profile, name)
                for name in inspection_ids
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
    """Canonical lifecycle that accepts artifact-bound Inspection evidence."""

    def advance(
        self,
        clockwork: Clockwork,
        product_id: str,
        to_stage: str,
        expected_revision: int,
        *,
        inspection: Optional[Inspection] = None,
        artifact_sha256: Optional[str] = None,
        cad_release: Optional[CadReleaseBundle] = None,
        stamp: Optional[Stamp] = None,
        pack_sha256: Optional[str] = None,
        send_intent_id: Optional[str] = None,
        expected_shop_owner_id: Optional[str] = None,
        lease_token: Optional[str] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        product = clockwork.get_product(product_id)
        if (
            product["stage"] in ("inspect", "pack")
            and artifact_sha256 is not None
            and artifact_sha256 != product.get("artifact_sha256")
        ):
            raise TransitionError(
                "artifact bytes cannot change after Inspect; return to Make"
            )
        required = self._required.get(to_stage, set())
        if required and not isinstance(inspection, Inspection):
            raise TransitionError(
                "canonical Workflow transitions with checks require an Inspection"
            )
        if inspection is not None:
            inspection.assert_valid()
            inspection.require(required)
            if cad_release is None:
                cad_release = inspection.cad_release
            elif (
                inspection.cad_release is not None
                and cad_release != inspection.cad_release
            ):
                raise TransitionError(
                    "CAD release differs from the artifact-bound Inspection"
                )
            selected = artifact_sha256 or inspection.artifact_sha256
            if selected != inspection.artifact_sha256:
                raise TransitionError(
                    "Inspection belongs to different artifact bytes"
                )
            artifact_sha256 = selected
            results = inspection.results
        else:
            results = ()
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
        return super().advance(
            clockwork,
            product_id,
            to_stage,
            expected_revision,
            artifact_sha256=artifact_sha256,
            gates=results,
            cad_release=cad_release,
            receipt=stamp,
            publication_packet_sha256=pack_sha256,
            publication_intent_id=send_intent_id,
            expected_owner_id=expected_shop_owner_id,
            lease_token=lease_token,
            note=note,
        )
