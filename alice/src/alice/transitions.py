"""Typed evidence required to move a candidate between lifecycle stages."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping

from .policy import validate_transition
from .policy import ReleasePolicy
from .store import CandidateRecord, DurableStore


ALLOWED_SOURCES: dict[tuple[str, str], frozenset[str]] = {
    ("proposed", "researched"): frozenset({"deterministic", "independent_model"}),
    ("researched", "rules_valid"): frozenset({"deterministic"}),
    ("rules_valid", "digitally_playtested"): frozenset({"simulation", "deterministic"}),
    ("digitally_playtested", "human_ready"): frozenset({"deterministic"}),
    ("human_ready", "human_validated"): frozenset({"blind_human"}),
    ("human_validated", "physical_ready"): frozenset({"manufacturing"}),
    ("physical_ready", "production_validated"): frozenset({"manufacturing"}),
    ("production_validated", "publish_ready"): frozenset({"release_policy"}),
    ("publish_ready", "page_ready"): frozenset({"publishing_pipeline"}),
    ("page_ready", "published"): frozenset({"publishing_pipeline"}),
}


@dataclass(frozen=True, slots=True)
class TransitionEvidence:
    evidence_id: str
    source: str
    verified: bool
    receipt: Mapping[str, Any]
    held_out: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "TransitionEvidence":
        evidence_id = value.get("evidence_id")
        source = value.get("source")
        receipt = value.get("receipt")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            raise ValueError("transition evidence_id is required")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("transition evidence source is required")
        if value.get("verified") is not True:
            raise ValueError("transition evidence must be independently verified")
        if not isinstance(receipt, Mapping) or not receipt:
            raise ValueError("transition evidence needs a non-empty receipt")
        return cls(
            evidence_id=evidence_id,
            source=source,
            verified=True,
            receipt=dict(receipt),
            held_out=bool(value.get("held_out", False)),
        )

    @property
    def receipt_sha256(self) -> str:
        return hashlib.sha256(
            json.dumps(self.receipt, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


def advance_with_evidence(
    store: DurableStore,
    candidate_id: str,
    target_state: str,
    evidence: TransitionEvidence,
    *,
    expected_policy_hash: str | None = None,
) -> CandidateRecord:
    candidate = store.get_candidate(candidate_id)
    validate_transition(candidate.state, target_state)
    allowed = ALLOWED_SOURCES.get((candidate.state, target_state))
    if allowed is None:
        raise ValueError(
            f"transition {candidate.state!r} -> {target_state!r} is not an evidence-driven progress step"
        )
    if evidence.source not in allowed:
        raise ValueError(
            f"evidence source {evidence.source!r} cannot unlock "
            f"{candidate.state!r} -> {target_state!r}; expected {sorted(allowed)}"
        )
    if target_state == "human_validated" and not evidence.held_out:
        raise ValueError("human validation must include held-out blind tables")
    manifest, manifest_sha256 = _validate_durable_manifest(
        store,
        candidate,
        target_state,
        evidence,
    )
    _validate_terminal_task_binding(
        store,
        candidate,
        target_state,
        evidence,
        manifest,
    )
    if target_state == "publish_ready":
        if evidence.receipt.get("allowed") is not True:
            raise ValueError("release-policy receipt does not allow publication")
        if evidence.receipt.get("effect_mode") != "live":
            raise ValueError("release-policy receipt was not evaluated in live mode")
        policy_hash = _sha(evidence.receipt.get("policy_hash"), "policy_hash")
        pinned_policy_hash = expected_policy_hash or ReleasePolicy().policy_hash
        if policy_hash != pinned_policy_hash:
            raise ValueError("release-policy receipt does not use the pinned policy hash")
        production_hash = _sha(
            evidence.receipt.get("production_packet_hash"),
            "production_packet_hash",
        )
        reviewed_hash = _sha(
            evidence.receipt.get("reviewed_packet_hash"),
            "reviewed_packet_hash",
        )
        if production_hash != reviewed_hash:
            raise ValueError("release-policy packet hashes do not match")
        release_manifest_hash = _sha(
            evidence.receipt.get("release_artifact_manifest_sha256"),
            "release_artifact_manifest_sha256",
        )
    if target_state in {"page_ready", "published"}:
        for key in ("packet_hash", "page_url", "pipeline_run_id"):
            if not evidence.receipt.get(key):
                raise ValueError(f"publishing-pipeline receipt needs {key}")
        _sha(evidence.receipt.get("packet_hash"), "packet_hash")

    store.add_experience(
        "candidate.transition_evidence",
        {
            "candidate_id": candidate_id,
            "from_state": candidate.state,
            "to_state": target_state,
            "evidence_id": evidence.evidence_id,
            "source": evidence.source,
            "held_out": evidence.held_out,
            "receipt_sha256": evidence.receipt_sha256,
            "receipt": dict(evidence.receipt),
        },
        candidate_id=candidate_id,
        idempotency_key=f"transition-evidence:{candidate_id}:{evidence.evidence_id}",
    )
    accepted_manifests = list(candidate.metadata.get("accepted_manifests", []))
    accepted_manifests.append(
        {
            "from_state": candidate.state,
            "to_state": target_state,
            "candidate_version": candidate.version,
            "manifest_sha256": manifest_sha256,
            "artifacts": manifest,
        }
    )
    metadata_patch: dict[str, Any] = {
        "last_evidence_id": evidence.evidence_id,
        "last_evidence_source": evidence.source,
        "last_receipt_sha256": evidence.receipt_sha256,
        "accepted_artifact_manifest_sha256": manifest_sha256,
        "accepted_manifests": accepted_manifests,
    }
    if target_state == "publish_ready":
        metadata_patch["release_decision"] = {
            "allowed": True,
            "effect_mode": "live",
            "policy_hash": evidence.receipt["policy_hash"],
            "production_packet_hash": evidence.receipt["production_packet_hash"],
            "reviewed_packet_hash": evidence.receipt["reviewed_packet_hash"],
            "artifact_manifest_sha256": release_manifest_hash,
            "production_candidate_version": evidence.receipt.get(
                "production_candidate_version"
            ),
            "production_manifest": evidence.receipt.get("production_manifest"),
            "candidate_id": candidate.id,
            "candidate_version": candidate.version,
            "release_candidate_version": candidate.version,
        }
    if target_state in {"page_ready", "published"}:
        metadata_patch["publication_binding"] = {
            key: evidence.receipt.get(key)
            for key in (
                "packet_hash",
                "page_url",
                "pipeline_run_id",
                "design_id",
                "slug",
                "history_id",
                "published_history_id",
                "policy_hash",
            )
        }
    return store.transition_candidate(
        candidate_id,
        target_state,
        expected_state=candidate.state,
        expected_version=candidate.version,
        metadata_patch=metadata_patch,
    )


def _validate_terminal_task_binding(
    store: DurableStore,
    candidate: CandidateRecord,
    target_state: str,
    evidence: TransitionEvidence,
    manifest: list[dict[str, Any]],
) -> None:
    """Bind privileged transitions to the exact durable terminal task output.

    The transition envelope adds its own artifact manifest, so comparing only
    evidence class is insufficient: an operator-supplied envelope could claim
    ``allowed=true`` while naming a durable denied release. Every privileged
    value is therefore copied from, and compared with, one exact current-
    version terminal task.
    """

    expected_action = {
        "publish_ready": "release.evaluate",
        "page_ready": "publish.invoke_pipeline",
        "published": "publish.verify_page",
    }.get(target_state)
    if expected_action is None:
        return
    entries = [entry for entry in manifest if entry.get("action") == expected_action]
    if len(entries) != 1:
        raise ValueError(
            f"transition to {target_state!r} needs exactly one durable "
            f"{expected_action!r} artifact"
        )
    entry = entries[0]
    if entry.get("candidate_version") != candidate.version:
        raise ValueError("terminal transition artifact is not for the current version")
    task = store.get_task(str(entry["task_id"]))
    content, executor, evidence_class = _task_content(task.result)
    expected_executor = (
        "release_policy" if target_state == "publish_ready" else "adapter"
    )
    expected_class = (
        "release_policy" if target_state == "publish_ready" else "publishing_pipeline"
    )
    if executor != expected_executor or evidence_class != expected_class:
        raise ValueError("terminal transition task has the wrong provenance")
    for key, expected in content.items():
        receipt_key = (
            "release_artifact_manifest_sha256"
            if target_state == "publish_ready" and key == "artifact_manifest_sha256"
            else key
        )
        if evidence.receipt.get(receipt_key) != expected:
            raise ValueError(
                f"transition receipt {receipt_key} does not match durable "
                f"{expected_action} result"
            )


def _validate_durable_manifest(
    store: DurableStore,
    candidate: CandidateRecord,
    target_state: str,
    evidence: TransitionEvidence,
) -> tuple[list[dict[str, Any]], str]:
    receipt = evidence.receipt
    if receipt.get("candidate_id") != candidate.id:
        raise ValueError("transition receipt candidate_id mismatch")
    if receipt.get("candidate_version") != candidate.version:
        raise ValueError("transition receipt candidate_version mismatch")
    if receipt.get("target_state") != target_state:
        raise ValueError("transition receipt target_state mismatch")
    raw_manifest = receipt.get("artifacts")
    if not isinstance(raw_manifest, list) or not raw_manifest:
        raise ValueError("transition receipt needs a non-empty artifact manifest")
    if any(not isinstance(item, Mapping) for item in raw_manifest):
        raise ValueError("transition artifact entries must be objects")
    manifest = [dict(item) for item in raw_manifest]
    manifest_sha256 = _sha(
        receipt.get("artifact_manifest_sha256"), "artifact_manifest_sha256"
    )
    calculated = hashlib.sha256(
        json.dumps(
            manifest,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if calculated != manifest_sha256:
        raise ValueError("transition artifact manifest hash mismatch")

    evidence_classes: set[str] = set()
    executors: set[str] = set()
    task_ids: set[str] = set()
    for entry in manifest:
        task_id = entry.get("task_id")
        if not isinstance(task_id, str) or not task_id or task_id in task_ids:
            raise ValueError("transition artifact task_ids must be unique non-empty strings")
        task_ids.add(task_id)
        task = store.get_task(task_id)
        if task.state != "succeeded" or task.candidate_id != candidate.id:
            raise ValueError("transition artifact is not a succeeded task for this candidate")
        if entry.get("action") != task.kind or entry.get("output_sha256") != task.output_sha256:
            raise ValueError("transition artifact does not match its durable task")
        task_version = task.payload.get("candidate_version")
        if entry.get("candidate_version") != task_version:
            raise ValueError("transition artifact candidate version mismatch")
        content, executor, evidence_class = _task_content(task.result)
        if entry.get("content_sha256") != store.sha256_json(content):
            raise ValueError("transition artifact content hash mismatch")
        if entry.get("executor") != executor or entry.get("evidence_class") != evidence_class:
            raise ValueError("transition artifact provenance mismatch")
        executors.add(executor)
        evidence_classes.add(evidence_class)

    required_class = {
        "independent_model": "independent_model",
        "simulation": "simulation",
        "blind_human": "blind_human",
        "manufacturing": "manufacturing",
        "release_policy": "release_policy",
        "publishing_pipeline": "publishing_pipeline",
    }.get(evidence.source)
    if required_class is not None:
        if required_class not in evidence_classes:
            raise ValueError(
                f"transition source {evidence.source!r} lacks a durable {required_class!r} artifact"
            )
        if evidence.source not in {"release_policy"} and "adapter" not in executors:
            raise ValueError("external transition evidence must come from an adapter")
    return manifest, manifest_sha256


def _task_content(result: Any) -> tuple[Mapping[str, Any], str, str]:
    if not isinstance(result, Mapping):
        raise ValueError("transition artifact task has no structured result")
    executor = result.get("executor")
    if executor == "adapter":
        receipt = result.get("receipt")
        if not isinstance(receipt, Mapping) or receipt.get("status") != "passed":
            raise ValueError("transition adapter receipt is not passed")
        content = receipt.get("payload")
        evidence_class = receipt.get("evidence_class")
    elif executor == "agent":
        response = result.get("response")
        content = response.get("content") if isinstance(response, Mapping) else None
        evidence_class = "same_model"
    elif executor == "release_policy":
        content = result.get("content")
        evidence_class = "release_policy"
    else:
        raise ValueError("transition artifact has an unknown executor")
    if not isinstance(content, Mapping):
        raise ValueError("transition artifact has no content object")
    if not isinstance(evidence_class, str) or not evidence_class:
        raise ValueError("transition artifact has no evidence class")
    return content, str(executor), evidence_class


def _sha(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value.lower() != value
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value
