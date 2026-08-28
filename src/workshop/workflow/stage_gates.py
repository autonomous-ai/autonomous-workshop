"""Host-owned deterministic gates for native Match and Invent proposals."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Optional

from workshop._validation import (
    copy_json_mapping,
    require_exact_version,
    require_safe_evidence_path,
    require_sha256,
)
from workshop.errors import ContractError, StateConflict
from workshop.invent.native import NativeInvented
from workshop.invent.vault import Vault, VaultError, assert_concept_compatible
from workshop.match.native import NativeMatchAssignment, InventorRoster
from workshop.workflow.agent_run import (
    AGENT_RUN_STAGES,
    AgentArtifact,
    AgentOutcome,
    DeterministicGateReceipt,
)
from workshop.workflow.proposals import (
    AgentOutcomeProposal,
    read_bounded_json_artifact,
)


STAGE_GATE_EVIDENCE_KIND = "autonomous-workshop.stage-gate-evidence"
STAGE_GATE_DECISION_KIND = "autonomous-workshop.stage-gate-decision"
MATCH_GATE_ID = "match.assignment-v3"
INVENT_GATE_ID = "invent.concept-v3"
MATCH_ASSIGNMENT_PATH = "artifacts/match/assignment.json"
INVENTED_PATH = "artifacts/invent/invented.json"
VALIDATOR_VERSION = "2.0.0"
STAGE_SUBJECT_KIND = "autonomous-workshop.stage-gate-subject"
_GATE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
_FORWARD = {
    "match": "invent",
    "invent": "make",
    "make": "playtest",
    "playtest": "release",
    "release": "complete",
}


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("stage gate values must be finite JSON") from exc


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _stage_subject(stage: str, inputs: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        _canonical_json(
            {
                "schema_version": 1,
                "kind": STAGE_SUBJECT_KIND,
                "stage": stage,
                "inputs": dict(inputs),
            }
        )
    ).hexdigest()


def match_gate_subject_sha256(
    *, wish_sha256: str, inventor_roster_sha256: str
) -> str:
    """Derive Match's subject from its complete immutable input vector."""

    require_sha256(wish_sha256, "Match subject Wish sha256")
    require_sha256(inventor_roster_sha256, "Match subject inventor roster sha256")
    return _stage_subject(
        "match",
        {
            "wish_sha256": wish_sha256,
            "inventor_roster_sha256": inventor_roster_sha256,
        },
    )


def invent_gate_subject_sha256(assignment: NativeMatchAssignment) -> str:
    """Derive Invent's subject from every accepted creative input binding."""

    if not isinstance(assignment, NativeMatchAssignment):
        raise ContractError("Invent subject requires a native Match assignment")
    return _stage_subject(
        "invent",
        {
            "wish_sha256": assignment.wish_sha256,
            "assignment_sha256": assignment.assignment_sha256,
            "agent_sha256": assignment.selected_agent_sha256,
            "taste_sha256": assignment.selected_taste_sha256,
            "blueprint_sha256": assignment.blueprint_sha256,
        },
    )


@dataclass(frozen=True)
class StageGateEvidence:
    """Deterministic evidence created by the host, never by the native agent."""

    stage: str
    gate_id: str
    validator_version: str
    passed: bool
    checkpoint_sha256: str
    subject_sha256: str
    outcome_sha256: str
    artifact_path: str
    artifact_sha256: str
    checks: Mapping[str, Any]
    schema_version: int = 1
    kind: str = STAGE_GATE_EVIDENCE_KIND
    evidence_sha256: str = field(init=False)
    _checks_json: bytes = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("stage gate evidence schema_version must be 1")
        if self.kind != STAGE_GATE_EVIDENCE_KIND:
            raise ContractError("stage gate evidence kind is invalid")
        if self.stage not in AGENT_RUN_STAGES:
            raise ContractError("stage gate evidence stage is invalid")
        if not isinstance(self.gate_id, str) or _GATE_ID.fullmatch(self.gate_id) is None:
            raise ContractError("stage gate evidence gate_id is invalid")
        require_exact_version(self.validator_version, "stage gate validator version")
        if type(self.passed) is not bool:
            raise ContractError("stage gate evidence passed must be boolean")
        require_sha256(self.checkpoint_sha256, "stage gate checkpoint sha256")
        require_sha256(self.subject_sha256, "stage gate subject sha256")
        require_sha256(self.outcome_sha256, "stage gate outcome sha256")
        require_safe_evidence_path(self.artifact_path, "stage gate artifact path")
        require_sha256(self.artifact_sha256, "stage gate artifact sha256")
        checks = copy_json_mapping(self.checks, "stage gate checks", nonempty=True)
        checks_json = _canonical_json(checks)
        object.__setattr__(self, "checks", _freeze_json(checks))
        object.__setattr__(self, "_checks_json", checks_json)
        object.__setattr__(
            self,
            "evidence_sha256",
            hashlib.sha256(_canonical_json(self._identity_dict())).hexdigest(),
        )

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "stage": self.stage,
            "gate_id": self.gate_id,
            "validator_version": self.validator_version,
            "passed": self.passed,
            "checkpoint_sha256": self.checkpoint_sha256,
            "subject_sha256": self.subject_sha256,
            "outcome_sha256": self.outcome_sha256,
            "artifact_path": self.artifact_path,
            "artifact_sha256": self.artifact_sha256,
            "checks": json.loads(self._checks_json.decode("utf-8")),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["evidence_sha256"] = self.evidence_sha256
        return payload

    @classmethod
    def from_mapping(cls, value: Any) -> "StageGateEvidence":
        expected = {
            "schema_version",
            "kind",
            "stage",
            "gate_id",
            "validator_version",
            "passed",
            "checkpoint_sha256",
            "subject_sha256",
            "outcome_sha256",
            "artifact_path",
            "artifact_sha256",
            "checks",
            "evidence_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("stage gate evidence fields are invalid")
        evidence = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            stage=value["stage"],
            gate_id=value["gate_id"],
            validator_version=value["validator_version"],
            passed=value["passed"],
            checkpoint_sha256=value["checkpoint_sha256"],
            subject_sha256=value["subject_sha256"],
            outcome_sha256=value["outcome_sha256"],
            artifact_path=value["artifact_path"],
            artifact_sha256=value["artifact_sha256"],
            checks=value["checks"],
        )
        if dict(value) != evidence.to_dict():
            raise ContractError("stage gate evidence sha256 is invalid")
        return evidence


@dataclass(frozen=True)
class StageGateDecision:
    """The host decision and the only lifecycle transition it can authorize."""

    evidence: StageGateEvidence
    transition: Optional[str]
    schema_version: int = 1
    kind: str = STAGE_GATE_DECISION_KIND

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("stage gate decision schema_version must be 1")
        if self.kind != STAGE_GATE_DECISION_KIND:
            raise ContractError("stage gate decision kind is invalid")
        if not isinstance(self.evidence, StageGateEvidence):
            raise ContractError("stage gate decision requires host evidence")
        expected = _FORWARD.get(self.evidence.stage)
        if self.evidence.stage == "playtest" and not self.evidence.passed:
            if self.transition not in ("make", "invent"):
                raise ContractError(
                    "failed Playtest gate must return explicit feedback to Make or Invent"
                )
        elif self.evidence.passed:
            if self.evidence.stage == "make" and self.transition in (
                "playtest",
                "release",
            ):
                return
            if self.evidence.stage == "release" and self.transition in (
                "complete",
                "deliver",
            ):
                # ``deliver`` is accepted only to read and finish a run whose
                # immutable pre-terminal-Release finalizer still proposes that
                # historical transition. New runs complete at Release.
                return
            if expected is None or self.transition != expected:
                raise ContractError("passed stage gate has an invalid transition")
        elif self.transition is not None:
            raise ContractError("failed stage gate cannot authorize a transition")

    @property
    def passed(self) -> bool:
        return self.evidence.passed

    @property
    def receipt(self) -> DeterministicGateReceipt:
        return DeterministicGateReceipt(
            stage=self.evidence.stage,
            gate_id=self.evidence.gate_id,
            passed=self.evidence.passed,
            subject_sha256=self.evidence.subject_sha256,
            outcome_sha256=self.evidence.outcome_sha256,
            evidence_sha256=self.evidence.evidence_sha256,
        )

    @property
    def sha256(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict())).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "transition": self.transition,
            "evidence": self.evidence.to_dict(),
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "StageGateDecision":
        expected = {"schema_version", "kind", "transition", "evidence"}
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("stage gate decision fields are invalid")
        decision = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            transition=value["transition"],
            evidence=StageGateEvidence.from_mapping(value["evidence"]),
        )
        if dict(value) != decision.to_dict():
            raise ContractError("stage gate decision is invalid")
        return decision


def _ready_artifact(
    proposal: AgentOutcomeProposal,
    *,
    stage: str,
    transition: str,
    canonical_path: str,
) -> AgentArtifact:
    if not isinstance(proposal, AgentOutcomeProposal):
        raise ContractError("stage gate requires an AgentOutcomeProposal")
    outcome = proposal.outcome
    if not isinstance(outcome, AgentOutcome):  # defensive for non-dataclass callers
        raise ContractError("stage gate proposal lacks a typed AgentOutcome")
    if (
        outcome.stage != stage
        or outcome.status != "ready"
        or outcome.proposed_transition != transition
        or outcome.needs
        or len(outcome.artifacts) != 1
    ):
        raise ContractError("%s outcome is not a single ready forward proposal" % stage)
    artifact = outcome.artifacts[0]
    if artifact.path != canonical_path:
        raise ContractError(
            "%s outcome must reference exactly %s" % (stage, canonical_path)
        )
    return artifact


def _artifact_document(
    run_root: Any, artifact: AgentArtifact, *, label: str
) -> Mapping[str, Any]:
    document, content = read_bounded_json_artifact(
        run_root, artifact.path, label=label
    )
    observed = hashlib.sha256(content).hexdigest()
    if observed != artifact.sha256:
        raise StateConflict("%s bytes do not match the proposed artifact sha256" % label)
    return document


def evaluate_match_stage(
    proposal: AgentOutcomeProposal,
    *,
    run_root: Any,
    expected_checkpoint_sha256: str,
    wish_sha256: str,
    roster: InventorRoster,
) -> StageGateDecision:
    """Validate the one canonical native Match assignment and derive a receipt."""

    require_sha256(expected_checkpoint_sha256, "expected Match checkpoint sha256")
    require_sha256(wish_sha256, "expected Match Wish sha256")
    if not isinstance(roster, InventorRoster):
        raise ContractError("Match gate requires a InventorRoster")
    if proposal.checkpoint_sha256 != expected_checkpoint_sha256:
        raise StateConflict("Match proposal belongs to another checkpoint")
    expected_subject = match_gate_subject_sha256(
        wish_sha256=wish_sha256,
        inventor_roster_sha256=roster.roster_sha256,
    )
    if proposal.subject_sha256 != expected_subject:
        raise StateConflict("Match proposal subject is not the full Match input vector")
    artifact = _ready_artifact(
        proposal,
        stage="match",
        transition="invent",
        canonical_path=MATCH_ASSIGNMENT_PATH,
    )
    assignment = NativeMatchAssignment.from_mapping(
        _artifact_document(run_root, artifact, label="native Match assignment")
    )
    assignment.assert_context(wish_sha256=wish_sha256, roster=roster)
    evidence = StageGateEvidence(
        stage="match",
        gate_id=MATCH_GATE_ID,
        validator_version=VALIDATOR_VERSION,
        passed=True,
        checkpoint_sha256=proposal.checkpoint_sha256,
        subject_sha256=proposal.subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "assignment_sha256": assignment.assignment_sha256,
            "blueprint_sha256": assignment.blueprint_sha256,
            "roster_sha256": roster.roster_sha256,
            "ranking_covers_roster": True,
            "selected_custom_agent_bound": True,
            "selected_agent_sha256": assignment.selected_agent_sha256,
            "selected_source_manifest_sha256": (
                assignment.selected_source_manifest_sha256
            ),
            "selected_taste_sha256": assignment.selected_taste_sha256,
            "wish_bound": True,
        },
    )
    return StageGateDecision(evidence=evidence, transition="invent")


def _vault_checks(vault: Optional[Vault], concept: Mapping[str, Any]) -> dict[str, Any]:
    """Re-apply the run-local design vault rules to a sealed Invent concept.

    With a vault snapshot every mechanism resolves or is declared novel, and no
    declared conflict or unmet requirement survives.  Without one (a run that
    predates the vault) the gate is unchanged.
    """

    if vault is None:
        return {"design_vault_sha256": None, "vault_leads": 0}
    try:
        binding = assert_concept_compatible(vault, concept)
    except VaultError as exc:
        raise ContractError("Invent concept is refused by the design vault: %s" % exc) from exc
    return {"design_vault_sha256": vault.sha256, "vault_leads": len(binding["leads"])}


def evaluate_invent_stage(
    proposal: AgentOutcomeProposal,
    *,
    run_root: Any,
    expected_checkpoint_sha256: str,
    assignment: NativeMatchAssignment,
    expected_subject_sha256: Optional[str] = None,
    expected_artifact_path: str = INVENTED_PATH,
    vault: Optional[Vault] = None,
) -> StageGateDecision:
    """Validate Invented against the accepted Match assignment and the vault."""

    if not isinstance(assignment, NativeMatchAssignment):
        raise ContractError("Invent gate requires a native Match assignment")
    require_sha256(expected_checkpoint_sha256, "expected Invent checkpoint sha256")
    if proposal.checkpoint_sha256 != expected_checkpoint_sha256:
        raise StateConflict("Invent proposal belongs to another checkpoint")
    subject_sha256 = (
        invent_gate_subject_sha256(assignment)
        if expected_subject_sha256 is None
        else require_sha256(
            expected_subject_sha256, "expected Invent subject sha256"
        )
    )
    if proposal.subject_sha256 != subject_sha256:
        raise StateConflict("Invent proposal subject is not the full Invent input vector")
    if not isinstance(expected_artifact_path, str) or not expected_artifact_path:
        raise ContractError("expected Invent artifact path is invalid")
    outcome = proposal.outcome
    source_path = (
        PurePosixPath(expected_artifact_path).parent / "source.json"
    ).as_posix()
    paths = tuple(item.path for item in outcome.artifacts)
    if (
        outcome.stage != "invent"
        or outcome.status != "ready"
        or outcome.proposed_transition != "make"
        or outcome.needs
        or paths not in ((expected_artifact_path,), (expected_artifact_path, source_path))
    ):
        raise ContractError("invent outcome is not an exact ready forward proposal")
    artifact = outcome.artifacts[0]
    invented = NativeInvented.from_mapping(
        _artifact_document(run_root, artifact, label="Invented artifact")
    )
    invented.assert_context(assignment)
    vault_checks = _vault_checks(vault, invented.concept)
    source_artifact = outcome.artifacts[1] if len(outcome.artifacts) == 2 else None
    if source_artifact is not None:
        source = _artifact_document(
            run_root, source_artifact, label="Invent authored source"
        )
        if (
            set(source) != {"concept", "research"}
            or source["concept"] != invented.to_dict()["concept"]
            or source["research"] != invented.to_dict()["research"]
        ):
            raise ContractError("Invent source differs from its sealed contract")
    evidence = StageGateEvidence(
        stage="invent",
        gate_id=INVENT_GATE_ID,
        validator_version=VALIDATOR_VERSION,
        passed=True,
        checkpoint_sha256=proposal.checkpoint_sha256,
        subject_sha256=proposal.subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "assignment_sha256": assignment.assignment_sha256,
            "blueprint_sha256": invented.blueprint_sha256,
            "concept_sha256": invented.concept_sha256,
            "research_sha256": invented.research_sha256,
            "source_artifact_sha256": (
                source_artifact.sha256 if source_artifact is not None else None
            ),
            "source_bound": source_artifact is not None,
            "taste_sha256": invented.taste_sha256,
            "wish_bound": True,
            **vault_checks,
        },
    )
    return StageGateDecision(evidence=evidence, transition="make")


def evaluate_routed_invent_stage(
    proposal: AgentOutcomeProposal,
    *,
    run_root: Any,
    expected_checkpoint_sha256: str,
    expected_subject_sha256: str,
    wish_sha256: str,
    roster: InventorRoster,
    assignment_artifact_path: str,
    invented_artifact_path: str,
    vault: Optional[Vault] = None,
) -> StageGateDecision:
    """Validate combined selection + invention from one routed Invent turn."""

    require_sha256(expected_checkpoint_sha256, "expected Invent checkpoint sha256")
    require_sha256(expected_subject_sha256, "expected Invent subject sha256")
    require_sha256(wish_sha256, "expected Invent Wish sha256")
    if not isinstance(roster, InventorRoster):
        raise ContractError("routed Invent gate requires an InventorRoster")
    if (
        proposal.checkpoint_sha256 != expected_checkpoint_sha256
        or proposal.subject_sha256 != expected_subject_sha256
    ):
        raise StateConflict("routed Invent proposal belongs to another stage subject")
    outcome = proposal.outcome
    source_artifact_path = (
        PurePosixPath(invented_artifact_path).parent / "source.json"
    ).as_posix()
    if (
        outcome.stage != "invent"
        or outcome.status != "ready"
        or outcome.proposed_transition != "make"
        or outcome.needs
        or tuple(item.path for item in outcome.artifacts)
        != (invented_artifact_path, assignment_artifact_path, source_artifact_path)
    ):
        raise ContractError(
            "routed Invent outcome must contain its exact Invented, assignment, and source artifacts"
        )
    invented_artifact, assignment_artifact, source_artifact = outcome.artifacts
    assignment = NativeMatchAssignment.from_mapping(
        _artifact_document(
            run_root, assignment_artifact, label="routed native Match assignment"
        )
    )
    assignment.assert_context(wish_sha256=wish_sha256, roster=roster)
    invented = NativeInvented.from_mapping(
        _artifact_document(run_root, invented_artifact, label="routed Invented artifact")
    )
    invented.assert_context(assignment)
    vault_checks = _vault_checks(vault, invented.concept)
    source = _artifact_document(
        run_root, source_artifact, label="routed Invent authored source"
    )
    expected_source_fields = {
        "selected_inventor_id",
        "ranking",
        "concept",
        "research",
    }
    if (
        set(source) != expected_source_fields
        or source["selected_inventor_id"] != assignment.selected_inventor_id
        or source["ranking"] != [item.to_dict() for item in assignment.ranking]
        or source["concept"] != invented.to_dict()["concept"]
        or source["research"] != invented.to_dict()["research"]
    ):
        raise ContractError("routed Invent source differs from its sealed contracts")
    evidence = StageGateEvidence(
        stage="invent",
        gate_id="invent.routed-concept-v1",
        validator_version=VALIDATOR_VERSION,
        passed=True,
        checkpoint_sha256=proposal.checkpoint_sha256,
        subject_sha256=proposal.subject_sha256,
        outcome_sha256=outcome.sha256,
        artifact_path=invented_artifact.path,
        artifact_sha256=invented_artifact.sha256,
        checks={
            "assignment_artifact_sha256": assignment_artifact.sha256,
            "assignment_sha256": assignment.assignment_sha256,
            "blueprint_sha256": invented.blueprint_sha256,
            "concept_sha256": invented.concept_sha256,
            "research_sha256": invented.research_sha256,
            "source_artifact_sha256": source_artifact.sha256,
            "roster_sha256": roster.roster_sha256,
            "selected_custom_agent_bound": True,
            "source_bound": True,
            "selected_taste_sha256": assignment.selected_taste_sha256,
            "wish_bound": True,
            **vault_checks,
        },
    )
    return StageGateDecision(evidence=evidence, transition="make")


__all__ = [
    "INVENTED_PATH",
    "INVENT_GATE_ID",
    "MATCH_ASSIGNMENT_PATH",
    "MATCH_GATE_ID",
    "STAGE_GATE_DECISION_KIND",
    "STAGE_GATE_EVIDENCE_KIND",
    "STAGE_SUBJECT_KIND",
    "StageGateDecision",
    "StageGateEvidence",
    "VALIDATOR_VERSION",
    "evaluate_invent_stage",
    "evaluate_routed_invent_stage",
    "evaluate_match_stage",
    "invent_gate_subject_sha256",
    "match_gate_subject_sha256",
]
