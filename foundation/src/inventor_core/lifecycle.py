"""Explicit lifecycle graphs with artifact-bound gates and publish receipts."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Set

from .cad import CadReleaseBundle
from .errors import ContractError, ReceiptError, TransitionError
from .models import (
    GateResult,
    PublicationReceipt,
    require_exact_version,
    require_sha256,
    utc_now,
)
from .store import InventorStore


@dataclass(frozen=True)
class GatePolicy:
    gate_id: str
    evaluator: str
    evaluator_version: str
    config_sha256: str
    max_age_seconds: Optional[int] = None
    max_future_skew_seconds: int = 300

    def __post_init__(self) -> None:
        if not self.gate_id or not self.evaluator:
            raise ContractError("gate policy requires an id and evaluator")
        require_exact_version(self.evaluator_version, "gate policy evaluator_version")
        require_sha256(self.config_sha256, "gate policy config_sha256")
        if self.max_age_seconds is not None and (
            not isinstance(self.max_age_seconds, int)
            or isinstance(self.max_age_seconds, bool)
            or self.max_age_seconds <= 0
        ):
            raise ContractError("gate policy max_age_seconds must be a positive integer or null")
        if (
            not isinstance(self.max_future_skew_seconds, int)
            or isinstance(self.max_future_skew_seconds, bool)
            or self.max_future_skew_seconds < 0
            or self.max_future_skew_seconds > 3600
        ):
            raise ContractError(
                "gate policy max_future_skew_seconds must be an integer from 0 to 3600"
            )


def _board_gate_policy(gate_id: str) -> GatePolicy:
    evaluator = "inventor-core.%s" % gate_id
    version = "1"
    freshness = {
        "novelty": 7 * 24 * 60 * 60,
        "playtest": 30 * 24 * 60 * 60,
    }.get(gate_id)
    config = hashlib.sha256(
        (
            "board-game-gate-policy-v2:%s:max-age=%s:future-skew=300"
            % (gate_id, freshness)
        ).encode("utf-8")
    ).hexdigest()
    return GatePolicy(gate_id, evaluator, version, config, freshness)


@dataclass(frozen=True)
class PipelineSpec:
    initial_stage: str
    stages: Sequence[str]
    edges: Mapping[str, Iterable[str]]
    required_gates: Mapping[str, Iterable[str]]
    gate_policies: Mapping[str, GatePolicy]

    def __post_init__(self) -> None:
        stage_set = set(self.stages)
        if not self.stages or len(stage_set) != len(self.stages):
            raise ContractError("pipeline stages must be non-empty and unique")
        if self.initial_stage not in stage_set:
            raise ContractError("pipeline initial_stage is not in stages")
        if set(self.edges) != stage_set:
            raise ContractError("pipeline edges must define every stage")
        for source, targets in self.edges.items():
            unknown = set(targets) - stage_set
            if unknown:
                raise ContractError("%s has unknown targets %s" % (source, sorted(unknown)))
        if set(self.required_gates) - stage_set:
            raise ContractError("required_gates names an unknown target stage")
        required_gate_ids = {
            gate for gates in self.required_gates.values() for gate in gates
        }
        if not required_gate_ids <= set(self.gate_policies):
            raise ContractError(
                "gate_policies must define every required gate id"
            )
        if any(key != policy.gate_id for key, policy in self.gate_policies.items()):
            raise ContractError("gate_policies keys must match their gate ids")

    @classmethod
    def board_game(cls) -> "PipelineSpec":
        """A reusable default; niche inventors may supply a stricter graph."""
        stages = (
            "idea",
            "researched",
            "rules",
            "simulated",
            "built",
            "validated",
            "reviewed",
            "draft",
            "live",
            "parked",
            "killed",
        )
        forward = {
            "idea": {"researched"},
            "researched": {"rules"},
            "rules": {"simulated", "rules"},
            "simulated": {"built", "rules"},
            "built": {"validated", "built"},
            "validated": {"reviewed", "built", "rules"},
            "reviewed": {"draft", "built", "rules"},
            "draft": {"live"},
            "live": set(),
            "parked": set(stages) - {"parked", "live"},
            "killed": set(),
        }
        for stage in stages:
            if stage not in ("live", "parked", "killed", "draft"):
                forward[stage] = set(forward[stage]) | {"parked", "killed"}
        forward["draft"] = {"live", "killed"}
        required_gates = {
            "simulated": ("rules-lint",),
            "validated": ("rules-lint", "cad", "printability"),
            "reviewed": (
                "rules-lint", "cad", "printability", "playtest", "novelty"
            ),
            "draft": (
                "rules-lint", "cad", "printability", "playtest", "novelty"
            ),
        }
        gate_ids = {gate for gates in required_gates.values() for gate in gates}
        return cls(
            initial_stage="idea",
            stages=stages,
            edges=forward,
            required_gates=required_gates,
            gate_policies={gate: _board_gate_policy(gate) for gate in gate_ids},
        )


class Pipeline:
    """Policy layer over the store's revision-fenced transition primitive."""

    def __init__(self, spec: PipelineSpec) -> None:
        self.spec = spec
        self._edges = {stage: set(targets) for stage, targets in spec.edges.items()}
        self._required = {
            stage: set(gates) for stage, gates in spec.required_gates.items()
        }
        self._gate_policies = dict(spec.gate_policies)

    def register(
        self,
        store: InventorStore,
        product_id: str,
        metadata: Optional[Mapping[str, Any]] = None,
        artifact_sha256: Optional[str] = None,
    ) -> Dict[str, Any]:
        return store.register_product(
            product_id, self.spec.initial_stage, metadata, artifact_sha256
        )

    def advance(
        self,
        store: InventorStore,
        product_id: str,
        to_stage: str,
        expected_revision: int,
        artifact_sha256: Optional[str] = None,
        gates: Iterable[GateResult] = (),
        cad_release: Optional[CadReleaseBundle] = None,
        receipt: Optional[PublicationReceipt] = None,
        publication_packet_sha256: Optional[str] = None,
        publication_intent_id: Optional[str] = None,
        expected_owner_id: Optional[str] = None,
        lease_token: Optional[str] = None,
        note: str = "",
    ) -> Dict[str, Any]:
        product = store.get_product(product_id)
        source = product["stage"]
        legal_targets = set(self._edges.get(source, set()))
        if source == "parked":
            events = store.events(product_id)
            parked_from = events[-1]["from_stage"] if events else None
            legal_targets = {stage for stage in (parked_from, "killed") if stage}
        if to_stage not in legal_targets:
            raise TransitionError(
                "illegal transition %s -> %s; legal targets: %s"
                % (source, to_stage, sorted(legal_targets))
            )
        next_artifact = artifact_sha256 or product.get("artifact_sha256")
        if source == "draft" and next_artifact != product.get("artifact_sha256"):
            raise TransitionError("artifact bytes cannot change during draft-to-live publication")
        required = self._required.get(to_stage, set())
        by_id: Dict[str, GateResult] = {}
        for gate in gates:
            if not isinstance(gate, GateResult):
                raise TransitionError("gate results must use the Foundation GateResult contract")
            try:
                gate.assert_valid()
            except ContractError as exc:
                raise TransitionError("gate %s is malformed" % gate.gate_id) from exc
            if gate.gate_id in by_id:
                raise TransitionError("duplicate gate result %r" % gate.gate_id)
            by_id[gate.gate_id] = gate
        missing = required - set(by_id)
        if missing:
            raise TransitionError("transition to %s lacks gates: %s" % (to_stage, sorted(missing)))
        if required and not next_artifact:
            raise TransitionError("gated transition requires an artifact identity")
        if "cad" in required:
            if cad_release is None:
                raise TransitionError(
                    "CAD-gated transition requires a validated CadReleaseBundle"
                )
            cad_release.assert_artifact(next_artifact)
            cad_gate = by_id["cad"]
            if (
                cad_gate.evidence.get("cad_release_sha256") != cad_release.sha256
                or cad_gate.evidence_sha256 != cad_release.sha256
            ):
                raise TransitionError("CAD gate does not bind the validated release bundle")
        for gate_id, gate in by_id.items():
            policy = self._gate_policies.get(gate_id)
            if policy is None:
                raise TransitionError("gate %s has no pinned evaluator policy" % gate_id)
            if not gate.passed:
                raise TransitionError("gate %s did not pass" % gate_id)
            if gate.artifact_sha256 != next_artifact:
                raise TransitionError("gate %s belongs to different artifact bytes" % gate_id)
            if (
                gate.evaluator != policy.evaluator
                or gate.evaluator_version != policy.evaluator_version
                or gate.config_sha256 != policy.config_sha256
            ):
                raise TransitionError("gate %s evaluator version/config drift" % gate_id)
            observed = datetime.fromisoformat(
                gate.observed_at.replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            now = datetime.fromisoformat(
                utc_now().replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            if observed > now + timedelta(seconds=policy.max_future_skew_seconds):
                raise TransitionError("gate %s is dated in the future" % gate_id)
            if (
                policy.max_age_seconds is not None
                and observed < now - timedelta(seconds=policy.max_age_seconds)
            ):
                raise TransitionError("gate %s evidence is stale" % gate_id)

        if to_stage in ("draft", "live"):
            if (
                receipt is None
                or publication_packet_sha256 is None
                or publication_intent_id is None
                or not expected_owner_id
            ):
                raise TransitionError(
                    "%s requires a durable Panda intent, receipt, packet identity, "
                    "and expected owner" % to_stage
                )
            require_sha256(publication_packet_sha256, "publication packet_sha256")
            receipt.assert_packet(publication_packet_sha256)
            receipt.assert_artifact(next_artifact)
            receipt.assert_owner(expected_owner_id)
            try:
                publication_intent = store.get_publish_intent(publication_intent_id)
            except KeyError as exc:
                raise TransitionError("publication intent does not exist") from exc
            expected_intent_state = "succeeded" if to_stage == "draft" else "live"
            if (
                publication_intent.get("product_id") != product_id
                or publication_intent.get("state") != expected_intent_state
                or publication_intent.get("packet_sha256")
                != publication_packet_sha256
                or publication_intent.get("receipt") != receipt.to_dict()
            ):
                raise TransitionError(
                    "%s receipt is not the exact durable outbox result" % to_stage
                )
            if to_stage == "draft" and receipt.status != "draft":
                raise TransitionError("draft transition requires draft readback")
            if to_stage == "live" and not receipt.is_verified_public:
                raise TransitionError(
                    "live requires public readback where published_history_id equals current_history_id"
                )
            if to_stage == "live":
                prior_events = store.events(product_id)
                prior_payload = prior_events[-1]["payload"] if prior_events else {}
                prior_raw = prior_payload.get("publication_receipt")
                prior_packet = prior_payload.get("publication_packet_sha256")
                prior_intent = prior_payload.get("publication_intent_id")
                if (
                    not isinstance(prior_raw, Mapping)
                    or prior_packet != publication_packet_sha256
                    or prior_intent != publication_intent_id
                ):
                    raise TransitionError("live lacks continuity with a recorded draft receipt")
                try:
                    prior = PublicationReceipt(**prior_raw)
                except (TypeError, ValueError, ContractError, ReceiptError) as exc:
                    raise TransitionError("recorded draft receipt is malformed") from exc
                if prior.status != "draft":
                    raise TransitionError("recorded publication receipt is not a draft")
                prior.assert_owner(expected_owner_id)
                if (
                    prior.packet_sha256 != receipt.packet_sha256
                    or prior.artifact_sha256 != receipt.artifact_sha256
                    or prior.design_id != receipt.design_id
                    or prior.root_id != receipt.root_id
                    or prior.slug != receipt.slug
                    or prior.current_history_id != receipt.current_history_id
                    or prior.project_url != receipt.project_url
                ):
                    raise TransitionError("live receipt does not identify the recorded draft")

        payload: Dict[str, Any] = {
            "note": note,
            "gates": [gate.to_dict() for gate in sorted(by_id.values(), key=lambda item: item.gate_id)],
        }
        if receipt:
            payload["publication_receipt"] = receipt.to_dict()
        if publication_packet_sha256:
            payload["publication_packet_sha256"] = publication_packet_sha256
        if publication_intent_id:
            payload["publication_intent_id"] = publication_intent_id
        return store._transition(
            product_id,
            source,
            to_stage,
            expected_revision,
            next_artifact,
            payload,
            lease_token,
        )
