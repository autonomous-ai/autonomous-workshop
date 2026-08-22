"""Deterministic release assembly from immutable, adapter-backed artifacts."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping, Sequence

from .fulfillment import (
    FulfillmentValidationError,
    manufacturing_spec_from_manifest,
)
from .loops import validate_output_semantics
from .page_builder import is_printable_cad_artifact_path
from .policy import ReleaseDecision, ReleaseFacts, ReleasePolicy
from .reward import Evidence


class ReleaseAssemblyError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ArtifactSnapshot:
    action: str
    task_id: str
    candidate_version: int
    output_sha256: str
    content_sha256: str
    executor: str
    evidence_class: str
    content: Mapping[str, Any]

    def manifest_entry(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "task_id": self.task_id,
            "candidate_version": self.candidate_version,
            "output_sha256": self.output_sha256,
            "content_sha256": self.content_sha256,
            "executor": self.executor,
            "evidence_class": self.evidence_class,
        }


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def artifact_manifest(artifacts: Iterable[ArtifactSnapshot]) -> tuple[list[dict[str, Any]], str]:
    entries = sorted(
        (artifact.manifest_entry() for artifact in artifacts),
        key=lambda item: (item["candidate_version"], item["action"], item["task_id"]),
    )
    if not entries:
        raise ReleaseAssemblyError("release evidence manifest is empty")
    return entries, canonical_sha256(entries)


def validate_blind_kit(
    content: Mapping[str, Any],
    *,
    expected_candidate_content_sha256: str | None = None,
    expected_rules_sha256: str | None = None,
) -> str:
    """Validate and return the hash of the exact zero-coaching test kit."""

    if not isinstance(content, Mapping):
        raise ReleaseAssemblyError("blind kit content must be an object")
    candidate_hash = _sha(content, "candidate_content_sha256")
    rules_hash = _sha(content, "rules_sha256")
    _match_optional_sha(
        candidate_hash,
        expected_candidate_content_sha256,
        "blind kit candidate content",
    )
    _match_optional_sha(rules_hash, expected_rules_sha256, "blind kit rules")
    rules_pdf_readback = content.get("rules_pdf_readback")
    if not isinstance(rules_pdf_readback, Mapping):
        raise ReleaseAssemblyError(
            "blind kit rules_pdf_readback must be an authenticated immutable object"
        )
    if rules_pdf_readback.get("receipt_source") != "authenticated_artifact_readback":
        raise ReleaseAssemblyError(
            "blind kit PDF needs authenticated_artifact_readback provenance"
        )
    _trimmed_string(
        rules_pdf_readback.get("artifact_id"), "blind kit PDF artifact_id"
    )
    _trimmed_string(rules_pdf_readback.get("authority"), "blind kit PDF authority")
    if rules_pdf_readback.get("media_type") != "application/pdf":
        raise ReleaseAssemblyError("blind kit rules artifact must be application/pdf")
    byte_count = _positive_int(rules_pdf_readback, "byte_count")
    pdf_bytes_sha256 = _sha(rules_pdf_readback, "pdf_bytes_sha256")
    if rules_pdf_readback.get("source_rules_sha256") != rules_hash:
        raise ReleaseAssemblyError(
            "blind kit PDF is not derived from the exact accepted rules"
        )
    expected_pdf_sha256 = compute_rules_pdf_sha256(
        pdf_bytes_sha256=pdf_bytes_sha256,
        source_rules_sha256=rules_hash,
        byte_count=byte_count,
    )
    if _sha(content, "rules_pdf_sha256") != expected_pdf_sha256:
        raise ReleaseAssemblyError(
            "blind kit rules_pdf_sha256 does not match its immutable readback"
        )
    observation_sheet = content.get("observation_sheet")
    if not isinstance(observation_sheet, Mapping) or not observation_sheet:
        raise ReleaseAssemblyError("blind kit observation_sheet must be a non-empty object")
    measures = _trimmed_string_list(
        content.get("preregistered_measures"),
        "blind kit preregistered_measures",
    )
    if len(set(measures)) != len(measures):
        raise ReleaseAssemblyError("blind kit preregistered measures must be unique")
    kit_hash = canonical_sha256(
        {
            "rules_pdf_readback": rules_pdf_readback,
            "rules_pdf_sha256": expected_pdf_sha256,
            "observation_sheet": observation_sheet,
            "preregistered_measures": list(measures),
        }
    )
    if _sha(content, "blind_kit_sha256") != kit_hash:
        raise ReleaseAssemblyError("blind kit hash does not match its exact contents")
    return kit_hash


def compute_rules_pdf_sha256(
    *, pdf_bytes_sha256: str, source_rules_sha256: str, byte_count: int
) -> str:
    """Derive the immutable rules-PDF binding from readback bytes and rules."""

    if not _is_sha256(pdf_bytes_sha256):
        raise ReleaseAssemblyError("pdf_bytes_sha256 must be a SHA-256 digest")
    if not _is_sha256(source_rules_sha256):
        raise ReleaseAssemblyError("source_rules_sha256 must be a SHA-256 digest")
    if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count <= 0:
        raise ReleaseAssemblyError("rules PDF byte_count must be a positive integer")
    return canonical_sha256(
        {
            "schema_version": 1,
            "media_type": "application/pdf",
            "byte_count": byte_count,
            "pdf_bytes_sha256": pdf_bytes_sha256,
            "source_rules_sha256": source_rules_sha256,
        }
    )


def validate_blind_human_evidence(
    content: Mapping[str, Any],
    *,
    expected_candidate_content_sha256: str | None = None,
    expected_rules_sha256: str | None = None,
    expected_blind_kit_sha256: str | None = None,
) -> None:
    """Require independently attributable blind trials bound to one rules kit.

    Provenance uses opaque ids only; customer names, addresses, and other PII do
    not belong in Alice's durable evidence ledger.
    """

    if not isinstance(content, Mapping):
        raise ReleaseAssemblyError("blind human evidence must be an object")
    candidate_hash = _sha(content, "candidate_content_sha256")
    rules_hash = _sha(content, "rules_sha256")
    kit_hash = _sha(content, "blind_kit_sha256")
    _match_optional_sha(
        candidate_hash,
        expected_candidate_content_sha256,
        "blind human candidate content",
    )
    _match_optional_sha(rules_hash, expected_rules_sha256, "blind human rules")
    _match_optional_sha(kit_hash, expected_blind_kit_sha256, "blind human kit")

    group_count = _positive_int(content, "blind_groups")
    minimum_games = _positive_int(content, "minimum_games_per_group")
    _trimmed_string(
        content.get("independent_operator_id"),
        "blind human independent_operator_id",
    )
    group_ids = _trimmed_string_list(content.get("group_ids"), "blind human group_ids")
    if len(group_ids) != group_count or len(set(group_ids)) != len(group_ids):
        raise ReleaseAssemblyError(
            "blind human group_ids must be unique and match blind_groups"
        )
    trial_ids = _trimmed_string_list(content.get("trial_ids"), "blind human trial_ids")
    if len(set(trial_ids)) != len(trial_ids):
        raise ReleaseAssemblyError("blind human trial_ids must be unique")

    consent_rows = content.get("consent_provenance")
    if not isinstance(consent_rows, list) or not consent_rows:
        raise ReleaseAssemblyError("blind human consent_provenance must be non-empty")
    consent_ids: list[str] = []
    for index, row in enumerate(consent_rows):
        if not isinstance(row, Mapping):
            raise ReleaseAssemblyError(
                f"blind human consent_provenance[{index}] must be an object"
            )
        consent_ids.append(
            _trimmed_string(
                row.get("consent_id"),
                f"blind human consent_provenance[{index}].consent_id",
            )
        )
        for key in ("basis", "recorded_at", "custodian"):
            _trimmed_string(
                row.get(key), f"blind human consent_provenance[{index}].{key}"
            )
    if len(set(consent_ids)) != len(consent_ids):
        raise ReleaseAssemblyError("blind human consent ids must be unique")

    trial_rows = content.get("trial_provenance")
    if not isinstance(trial_rows, list) or not trial_rows:
        raise ReleaseAssemblyError("blind human trial_provenance must be non-empty")
    provenance_trial_ids: list[str] = []
    receipt_ids: list[str] = []
    games_by_group = {group_id: 0 for group_id in group_ids}
    for index, row in enumerate(trial_rows):
        if not isinstance(row, Mapping):
            raise ReleaseAssemblyError(
                f"blind human trial_provenance[{index}] must be an object"
            )
        trial_id = _trimmed_string(
            row.get("trial_id"), f"blind human trial_provenance[{index}].trial_id"
        )
        group_id = _trimmed_string(
            row.get("group_id"), f"blind human trial_provenance[{index}].group_id"
        )
        consent_id = _trimmed_string(
            row.get("consent_id"),
            f"blind human trial_provenance[{index}].consent_id",
        )
        _trimmed_string(
            row.get("facilitator_id"),
            f"blind human trial_provenance[{index}].facilitator_id",
        )
        receipt_ids.append(
            _trimmed_string(
                row.get("external_receipt_id"),
                f"blind human trial_provenance[{index}].external_receipt_id",
            )
        )
        if group_id not in games_by_group:
            raise ReleaseAssemblyError("blind human trial names an unknown group_id")
        if consent_id not in consent_ids:
            raise ReleaseAssemblyError("blind human trial names an unknown consent_id")
        for key, expected in (
            ("candidate_content_sha256", candidate_hash),
            ("rules_sha256", rules_hash),
            ("blind_kit_sha256", kit_hash),
        ):
            if row.get(key) != expected:
                raise ReleaseAssemblyError(
                    f"blind human trial provenance {key} lineage mismatch"
                )
        provenance_trial_ids.append(trial_id)
        games_by_group[group_id] += 1
    if len(set(provenance_trial_ids)) != len(provenance_trial_ids):
        raise ReleaseAssemblyError("blind human provenance trial ids must be unique")
    if len(set(receipt_ids)) != len(receipt_ids):
        raise ReleaseAssemblyError("blind human external trial receipts must be unique")
    if set(provenance_trial_ids) != set(trial_ids) or len(provenance_trial_ids) != len(
        trial_ids
    ):
        raise ReleaseAssemblyError(
            "blind human trial_ids must exactly match trial_provenance"
        )
    if any(count < minimum_games for count in games_by_group.values()):
        raise ReleaseAssemblyError(
            "blind human trial provenance does not cover minimum games per group"
        )


def validate_manufacturing_receipt(
    content: Mapping[str, Any], action: str
) -> None:
    """Fail closed unless ``content`` has an authenticated factory readback.

    The inner receipt is deliberately separate from the adapter envelope.  An
    adapter proving that it ran does not prove that a machine completed the
    hash-bound manufacturing job described by its payload.
    """

    supported_actions = {
        "physical.prototype_print",
        "physical.production_run",
    }
    if action not in supported_actions:
        raise ReleaseAssemblyError(
            f"{action} is not a supported manufacturing receipt action"
        )
    if not isinstance(content, Mapping):
        raise ReleaseAssemblyError(f"{action} content must be an object")

    original_operation = _trimmed_string(
        content.get("original_operation"), f"{action} original_operation"
    )
    if original_operation != action:
        raise ReleaseAssemblyError(f"{action} original_operation mismatch")
    operation_key = _trimmed_string(
        content.get("effect_operation_key"), f"{action} effect_operation_key"
    )
    task_input_sha256 = _sha(content, "task_input_sha256")

    receipt = content.get("receipt")
    if not isinstance(receipt, Mapping):
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt must be an object"
        )

    if receipt.get("receipt_source") != "authenticated_manufacturing_readback":
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt is not an authenticated readback"
        )
    if receipt.get("action") != action:
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt action mismatch"
        )
    if receipt.get("operation_key") != operation_key:
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt operation_key mismatch"
        )
    if receipt.get("task_input_sha256") != task_input_sha256:
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt task_input_sha256 mismatch"
        )
    authority = _nonempty_string(receipt, "authority", action)
    authority_tokens = {
        token
        for token in "".join(
            character.casefold() if character.isalnum() else " "
            for character in authority
        ).split()
        if token
    }
    if authority_tokens & {
        "agent",
        "alice",
        "fixture",
        "internal",
        "mock",
        "model",
        "self",
        "simulated",
        "test",
    }:
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt authority must be an external system"
        )

    for key in ("job_id", "run_id", "machine_id", "material_lot"):
        _nonempty_string(receipt, key, action)
    if receipt.get("status") != "completed":
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt status must be 'completed'"
        )
    profile_sha256 = _sha(receipt, "profile_sha256")
    material_spec_sha256 = _sha(receipt, "material_spec_sha256")
    manufacturing_spec_sha256 = _sha(receipt, "manufacturing_spec_sha256")

    if action == "physical.production_run":
        manifest = content.get("production_manifest")
        if not isinstance(manifest, Mapping):
            raise ReleaseAssemblyError(
                "physical.production_run lacks a production_manifest object"
            )
        try:
            manufacturing_spec = manufacturing_spec_from_manifest(manifest)
        except FulfillmentValidationError as exc:
            raise ReleaseAssemblyError(str(exc)) from exc
        for name, observed in (
            ("print_profile_sha256", profile_sha256),
            ("material_spec_sha256", material_spec_sha256),
            ("manufacturing_spec_sha256", manufacturing_spec_sha256),
        ):
            if manufacturing_spec.get(name) != observed:
                raise ReleaseAssemblyError(
                    f"physical.production_run receipt {name} does not match "
                    "the production manifest"
                )

    sample_count = receipt.get("sample_count")
    if (
        isinstance(sample_count, bool)
        or not isinstance(sample_count, int)
        or sample_count <= 0
    ):
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt sample_count must be a positive integer"
        )
    defect_count = receipt.get("defect_count")
    if (
        isinstance(defect_count, bool)
        or not isinstance(defect_count, int)
        or defect_count < 0
        or defect_count > sample_count
    ):
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt defect_count must be between zero and sample_count"
        )
    measured_yield = _unit_float(receipt, "measured_yield")
    expected_yield = (sample_count - defect_count) / sample_count
    if not math.isclose(
        measured_yield, expected_yield, rel_tol=0.0, abs_tol=1e-12
    ):
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt measured_yield does not match its counts"
        )

    for key in (
        "candidate_content_sha256",
        "rules_sha256",
        "rules_file_sha256",
        "project_sha256",
    ):
        expected = _sha(content, key)
        if receipt.get(key) != expected:
            raise ReleaseAssemblyError(
                f"{action} manufacturing receipt {key} lineage mismatch"
            )
    artifact_hashes = content.get("artifact_hashes")
    receipt_artifact_hashes = receipt.get("artifact_hashes")
    if not isinstance(artifact_hashes, Mapping) or not artifact_hashes:
        raise ReleaseAssemblyError(f"{action} artifact_hashes must be a non-empty object")
    for artifact_name, digest in artifact_hashes.items():
        if not isinstance(artifact_name, str) or not artifact_name:
            raise ReleaseAssemblyError(
                f"{action} artifact_hashes keys must be non-empty strings"
            )
        if not _is_sha256(digest):
            raise ReleaseAssemblyError(
                f"{action} artifact_hashes[{artifact_name!r}] must be a lowercase SHA-256 digest"
            )
    _validate_release_artifact_hashes(artifact_hashes, f"{action} artifact_hashes")
    if (
        not isinstance(receipt_artifact_hashes, Mapping)
        or dict(receipt_artifact_hashes) != dict(artifact_hashes)
    ):
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt artifact_hashes lineage mismatch"
        )

    receipt_hash = _sha(receipt, "receipt_sha256")
    receipt_body = {
        key: value for key, value in receipt.items() if key != "receipt_sha256"
    }
    try:
        computed_receipt_hash = canonical_sha256(receipt_body)
    except (TypeError, ValueError) as exc:
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt is not canonically serializable"
        ) from exc
    if receipt_hash != computed_receipt_hash:
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt_sha256 mismatch"
        )

    if action == "physical.production_run":
        print_yield = _unit_float(content, "print_yield")
        if not math.isclose(
            measured_yield, print_yield, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ReleaseAssemblyError(
                "physical.production_run print_yield does not match its manufacturing receipt"
            )


def validate_distinct_manufacturing_receipts(
    prototype: Mapping[str, Any], production: Mapping[str, Any]
) -> None:
    """Reject a prototype receipt replayed as a production validation run."""

    validate_manufacturing_receipt(prototype, "physical.prototype_print")
    validate_manufacturing_receipt(production, "physical.production_run")
    prototype_receipt = prototype["receipt"]
    production_receipt = production["receipt"]
    assert isinstance(prototype_receipt, Mapping)
    assert isinstance(production_receipt, Mapping)
    for key in (
        "job_id",
        "run_id",
        "operation_key",
        "task_input_sha256",
        "receipt_sha256",
    ):
        if prototype_receipt.get(key) == production_receipt.get(key):
            raise ReleaseAssemblyError(
                f"prototype and production manufacturing receipts reuse {key}"
            )


def validate_production_manifest(manifest: Mapping[str, Any]) -> None:
    """Require a complete, customer-usable, manufacturing-bound product packet."""

    if not isinstance(manifest, Mapping):
        raise ReleaseAssemblyError("production manifest must be an object")
    _trimmed_string(manifest.get("candidate_id"), "production manifest candidate_id")
    candidate_version = manifest.get("candidate_version")
    if (
        isinstance(candidate_version, bool)
        or not isinstance(candidate_version, int)
        or candidate_version < 1
    ):
        raise ReleaseAssemblyError(
            "production manifest candidate_version must be a positive integer"
        )
    _sha(manifest, "candidate_content_sha256")
    rules_sha256 = _sha(manifest, "rules_sha256")

    customer = manifest.get("customer")
    if not isinstance(customer, Mapping):
        raise ReleaseAssemblyError("production manifest lacks customer")
    for key in ("title", "description"):
        _trimmed_string(customer.get(key), f"production manifest customer.{key}")
    _positive_range(customer.get("player_count"), "customer.player_count")
    _positive_range(
        customer.get("play_time_minutes"), "customer.play_time_minutes"
    )
    _positive_int(customer, "age_min")
    _trimmed_string_list(
        customer.get("whats_in_box"), "production manifest customer.whats_in_box"
    )

    rules = manifest.get("rules")
    if not isinstance(rules, Mapping):
        raise ReleaseAssemblyError("production manifest lacks rules")
    if rules.get("rules_sha256") != rules_sha256:
        raise ReleaseAssemblyError("production manifest rules section hash mismatch")
    _sha(rules, "rules_file_sha256")
    rules_markdown = rules.get("rules_markdown")
    if not isinstance(rules_markdown, str) or not rules_markdown.strip():
        raise ReleaseAssemblyError(
            "production manifest rules.rules_markdown must be non-empty"
        )

    manufacturing = manifest.get("manufacturing")
    if not isinstance(manufacturing, Mapping):
        raise ReleaseAssemblyError("production manifest lacks manufacturing")
    if manufacturing.get("process") != "3d_print":
        raise ReleaseAssemblyError(
            "production manifest manufacturing.process must be '3d_print'"
        )
    _nonnegative_cents(manufacturing, "landed_cost_cents")
    _sha(manufacturing, "print_profile_sha256")
    _trimmed_string_list(
        manufacturing.get("materials"),
        "production manifest manufacturing.materials",
    )
    packing = manufacturing.get("packing")
    if not isinstance(packing, Mapping):
        raise ReleaseAssemblyError("production manifest lacks manufacturing.packing")
    _trimmed_string(
        packing.get("format"), "production manifest manufacturing.packing.format"
    )
    _positive_int(packing, "component_count")
    vibe_design = manufacturing.get("vibe_design")
    if not isinstance(vibe_design, Mapping):
        raise ReleaseAssemblyError(
            "production manifest lacks manufacturing.vibe_design"
        )
    for key in ("design_id", "slug", "history_id", "project_url"):
        _trimmed_string(
            vibe_design.get(key), f"production manifest vibe_design.{key}"
        )
    for key in (
        "project_sha256",
        "rules_sha256",
        "rules_file_sha256",
    ):
        _sha(vibe_design, key)
    if vibe_design.get("rules_sha256") != rules_sha256:
        raise ReleaseAssemblyError("production manifest Vibe rules hash mismatch")
    artifact_hashes = _validate_release_artifact_hashes(
        vibe_design.get("artifact_hashes"),
        "production manifest manufacturing.vibe_design.artifact_hashes",
    )

    bom = manifest.get("bom")
    if not isinstance(bom, list) or not bom:
        raise ReleaseAssemblyError("production manifest bom must be non-empty")
    part_ids: list[str] = []
    printable_parts = 0
    for index, part in enumerate(bom):
        if not isinstance(part, Mapping):
            raise ReleaseAssemblyError(f"production manifest bom[{index}] must be an object")
        part_ids.append(
            _trimmed_string(
                part.get("part_id"), f"production manifest bom[{index}].part_id"
            )
        )
        for key in ("name", "material", "manufacturing_method"):
            _trimmed_string(
                part.get(key), f"production manifest bom[{index}].{key}"
            )
        _positive_int(part, "quantity")
        artifact_path = _trimmed_string(
            part.get("artifact_path"),
            f"production manifest bom[{index}].artifact_path",
        )
        if artifact_path not in artifact_hashes:
            raise ReleaseAssemblyError(
                f"production manifest bom[{index}] names an unbound artifact"
            )
        if part.get("manufacturing_method") == "3d_print":
            if not is_printable_cad_artifact_path(artifact_path):
                raise ReleaseAssemblyError(
                    f"production manifest bom[{index}] 3d_print part is not a printable CAD artifact"
                )
            printable_parts += 1
    if len(set(part_ids)) != len(part_ids):
        raise ReleaseAssemblyError("production manifest bom part_ids must be unique")
    if printable_parts < 1:
        raise ReleaseAssemblyError(
            "production manifest bom needs at least one 3d_print CAD part"
        )
    printable_artifacts = {
        path for path in artifact_hashes if is_printable_cad_artifact_path(path)
    }
    printable_bom_artifacts = {
        str(part["artifact_path"])
        for part in bom
        if part.get("manufacturing_method") == "3d_print"
    }
    if printable_bom_artifacts != printable_artifacts:
        raise ReleaseAssemblyError(
            "production manifest BOM must cover every and only bound printable artifact"
        )
    try:
        manufacturing_spec_from_manifest(manifest)
    except FulfillmentValidationError as exc:
        raise ReleaseAssemblyError(str(exc)) from exc

    evidence = manifest.get("evidence")
    if not isinstance(evidence, Mapping):
        raise ReleaseAssemblyError("production manifest lacks evidence")
    blind = evidence.get("blind_human")
    if not isinstance(blind, Mapping):
        raise ReleaseAssemblyError("production manifest lacks evidence.blind_human")
    _trimmed_string(
        blind.get("evidence_id"), "production manifest blind evidence_id"
    )
    _positive_int(blind, "sample_size")
    for key in (
        "blind_kit_sha256",
        "trial_ids_sha256",
        "group_ids_sha256",
        "consent_provenance_sha256",
        "trial_provenance_sha256",
    ):
        _sha(blind, key)
    simulation = evidence.get("simulation")
    if not isinstance(simulation, Mapping):
        raise ReleaseAssemblyError("production manifest lacks evidence.simulation")
    simulation_hashes = simulation.get("artifact_content_sha256")
    expected_simulations = {
        "simulation.optimizer",
        "simulation.social",
        "simulation.explorer",
        "simulation.exploit",
    }
    if not isinstance(simulation_hashes, Mapping) or set(simulation_hashes) != expected_simulations:
        raise ReleaseAssemblyError(
            "production manifest simulation evidence must bind all four playtest artifacts"
        )
    for action, digest in simulation_hashes.items():
        if not _is_sha256(digest):
            raise ReleaseAssemblyError(
                f"production manifest simulation evidence {action} hash is invalid"
            )
    prototype = evidence.get("prototype")
    if not isinstance(prototype, Mapping):
        raise ReleaseAssemblyError("production manifest lacks evidence.prototype")
    _sha(prototype, "receipt_sha256")

    disclosures = _trimmed_string_list(
        manifest.get("disclosures"), "production manifest disclosures"
    )
    if len(set(disclosures)) != len(disclosures):
        raise ReleaseAssemblyError("production manifest disclosures must be unique")

    price = manifest.get("price")
    if not isinstance(price, Mapping):
        raise ReleaseAssemblyError("production manifest lacks price")
    price_cents = price.get("price_cents")
    if isinstance(price_cents, bool) or not isinstance(price_cents, int) or price_cents < 100:
        raise ReleaseAssemblyError("production manifest price_cents must be at least 100")
    if price.get("currency") != "USD":
        raise ReleaseAssemblyError("production manifest price currency must be USD")
    listing = manifest.get("listing")
    if not isinstance(listing, Mapping):
        raise ReleaseAssemblyError("production manifest lacks listing")
    _trimmed_string(listing.get("sku"), "production manifest listing.sku")


def assess_release(
    artifacts: Sequence[ArtifactSnapshot],
    *,
    effect_mode: str,
    factory_capabilities: Iterable[str],
    policy: ReleasePolicy | None = None,
) -> dict[str, Any]:
    """Recompute release facts and reward from trusted durable task artifacts."""

    by_action = _unique_latest_actions(artifacts)
    required = {
        "candidate.safety_ip",
        "candidate.rules",
        "rules.lint",
        "rules.adversary",
        "simulation.optimizer",
        "simulation.social",
        "simulation.explorer",
        "simulation.exploit",
        "human.prepare_blind_kit",
        "human.collect_blind_results",
        "physical.create_rich_draft",
        "physical.prototype_print",
        "physical.production_run",
        "market.validate_offer",
        "market.final_safety_ip",
    }
    missing = sorted(required - set(by_action))
    if missing:
        raise ReleaseAssemblyError(
            "release evidence is missing artifacts: " + ", ".join(missing)
        )

    _require_adapter_class(by_action["candidate.safety_ip"], "independent_model")
    _require_adapter_class(by_action["rules.lint"], "deterministic")
    _require_adapter_class(by_action["rules.adversary"], "deterministic")
    for action in (
        "simulation.optimizer",
        "simulation.social",
        "simulation.explorer",
        "simulation.exploit",
    ):
        _require_adapter_class(by_action[action], "simulation")
    _require_adapter_class(by_action["human.collect_blind_results"], "blind_human")
    _require_adapter_class(
        by_action["physical.create_rich_draft"], "publishing_pipeline"
    )
    _require_adapter_class(by_action["physical.production_run"], "manufacturing")
    _require_adapter_class(by_action["physical.prototype_print"], "manufacturing")
    _require_adapter_class(by_action["market.validate_offer"], "market")
    _require_adapter_class(by_action["market.final_safety_ip"], "independent_model")

    safety_initial = by_action["candidate.safety_ip"].content
    safety_final = by_action["market.final_safety_ip"].content
    rules = by_action["rules.lint"].content
    attacks = by_action["rules.adversary"].content
    human = by_action["human.collect_blind_results"].content
    rich_draft = by_action["physical.create_rich_draft"].content
    prototype = by_action["physical.prototype_print"].content
    production = by_action["physical.production_run"].content
    market = by_action["market.validate_offer"].content

    candidate_hash = _sha(by_action["candidate.rules"].content, "candidate_content_sha256")
    rules_hash = _sha(by_action["candidate.rules"].content, "rules_sha256")
    blind_kit_hash = validate_blind_kit(
        by_action["human.prepare_blind_kit"].content,
        expected_candidate_content_sha256=candidate_hash,
        expected_rules_sha256=rules_hash,
    )
    validate_blind_human_evidence(
        human,
        expected_candidate_content_sha256=candidate_hash,
        expected_rules_sha256=rules_hash,
        expected_blind_kit_sha256=blind_kit_hash,
    )
    for action in (
        "simulation.optimizer",
        "simulation.social",
        "simulation.explorer",
        "simulation.exploit",
    ):
        try:
            validate_output_semantics(action, by_action[action].content)
        except ValueError as exc:
            raise ReleaseAssemblyError(str(exc)) from exc
    validate_distinct_manufacturing_receipts(prototype, production)

    production_hash = _sha(production, "production_packet_hash")
    production_reviewed_hash = _sha(production, "reviewed_packet_hash")
    market_reviewed_hash = _sha(market, "reviewed_packet_hash")
    safety_reviewed_hash = _sha(safety_final, "reviewed_packet_hash")
    if len({production_hash, production_reviewed_hash, market_reviewed_hash, safety_reviewed_hash}) != 1:
        raise ReleaseAssemblyError("production, market, and safety packet hashes disagree")
    production_manifest = production.get("production_manifest")
    if not isinstance(production_manifest, Mapping):
        raise ReleaseAssemblyError("production run lacks a production_manifest object")
    if canonical_sha256(production_manifest) != production_hash:
        raise ReleaseAssemblyError("production manifest does not match production_packet_hash")
    validate_production_manifest(production_manifest)
    _require_rich_draft_binding(rich_draft, production_manifest)
    _require_exact_product_lineage(by_action, production_manifest)
    computed_gross_margin = _require_validated_price(
        market, production, production_manifest
    )

    evidence = _reward_evidence(by_action)
    blind_groups = _positive_int(human, "blind_groups")
    games_per_group = _positive_int(human, "minimum_games_per_group")

    facts = ReleaseFacts(
        evidence_integrity=True,
        rules_complete=_true(rules, "rules_complete"),
        terminates=_true(rules, "terminates"),
        critical_exploits=_nonnegative_int(attacks, "critical_exploits"),
        critical_safety_findings=max(
            _nonnegative_int(safety_initial, "critical_safety_findings"),
            _nonnegative_int(safety_final, "critical_safety_findings"),
        ),
        critical_ip_findings=max(
            _nonnegative_int(safety_initial, "critical_ip_findings"),
            _nonnegative_int(safety_final, "critical_ip_findings"),
        ),
        blind_groups=blind_groups,
        minimum_games_per_group=games_per_group,
        designer_hints_required=_nonnegative_int(human, "designer_hints_required"),
        real_print_receipt=True,
        print_yield=_unit_float(production, "print_yield"),
        gross_margin=computed_gross_margin,
        production_packet_hash=production_hash,
        reviewed_packet_hash=market_reviewed_hash,
        factory_capabilities=tuple(sorted(set(factory_capabilities))),
    )
    chosen_policy = policy or ReleasePolicy()
    decision = chosen_policy.assess(facts, evidence, effect_mode=effect_mode)
    manifest, manifest_hash = artifact_manifest(artifacts)
    return {
        "allowed": decision.allowed,
        "policy_hash": decision.policy_hash,
        "effect_mode": decision.effect_mode,
        "failures": list(decision.failures),
        "production_packet_hash": production_hash,
        "reviewed_packet_hash": market_reviewed_hash,
        "production_candidate_version": by_action[
            "physical.production_run"
        ].candidate_version,
        "artifact_manifest": manifest,
        "artifact_manifest_sha256": manifest_hash,
        "release_facts": asdict(facts),
        "reward": _decision_reward(decision),
        "production_manifest": dict(production_manifest),
    }


def build_publication_packet(
    *,
    candidate_id: str,
    candidate_version: int,
    candidate_content_sha256: str,
    release_decision: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the exact production manifest; publication cannot regenerate it."""

    if release_decision.get("allowed") is not True:
        raise ReleaseAssemblyError("release decision does not allow publication")
    if release_decision.get("effect_mode") != "live":
        raise ReleaseAssemblyError("release decision was not evaluated in live mode")
    if release_decision.get("candidate_id") != candidate_id:
        raise ReleaseAssemblyError("release decision candidate_id mismatch")
    release_candidate_version = release_decision.get("candidate_version")
    if (
        isinstance(release_candidate_version, bool)
        or not isinstance(release_candidate_version, int)
        or release_candidate_version != candidate_version - 1
    ):
        raise ReleaseAssemblyError("release decision candidate version mismatch")
    production_hash = _sha(release_decision, "production_packet_hash")
    reviewed_hash = _sha(release_decision, "reviewed_packet_hash")
    if production_hash != reviewed_hash:
        raise ReleaseAssemblyError("release decision packet hashes disagree")
    packet = release_decision.get("production_manifest")
    if not isinstance(packet, Mapping):
        raise ReleaseAssemblyError("release decision lacks the production manifest")
    validate_production_manifest(packet)
    if canonical_sha256(packet) != production_hash:
        raise ReleaseAssemblyError("release production manifest hash mismatch")
    if packet.get("candidate_id") != candidate_id:
        raise ReleaseAssemblyError("production manifest candidate_id mismatch")
    if packet.get("candidate_content_sha256") != candidate_content_sha256:
        raise ReleaseAssemblyError("production manifest candidate content mismatch")
    # The manifest must be the exact earlier candidate version named by the
    # deterministic release receipt; intermediate state transitions may have
    # advanced the lifecycle version without changing product content.
    manifest_version = packet.get("candidate_version")
    released_manifest_version = release_decision.get("production_candidate_version")
    if (
        isinstance(manifest_version, bool)
        or not isinstance(manifest_version, int)
        or isinstance(released_manifest_version, bool)
        or not isinstance(released_manifest_version, int)
        or manifest_version != released_manifest_version
        or manifest_version > candidate_version
    ):
        raise ReleaseAssemblyError("production manifest candidate version mismatch")
    policy_hash = _sha(release_decision, "policy_hash")
    return {
        "publication_packet": dict(packet),
        "packet_hash": production_hash,
        "policy_hash": policy_hash,
        "release_decision": {
            "allowed": True,
            "effect_mode": "live",
            "candidate_id": candidate_id,
            "release_candidate_version": release_decision.get(
                "candidate_version"
            ),
            "publish_candidate_version": candidate_version,
            "policy_hash": policy_hash,
            "production_packet_hash": production_hash,
            "reviewed_packet_hash": reviewed_hash,
            "production_candidate_version": manifest_version,
            "artifact_manifest_sha256": _sha(
                release_decision, "artifact_manifest_sha256"
            ),
        },
    }


def _require_rich_draft_binding(
    rich_draft: Mapping[str, Any],
    production_manifest: Mapping[str, Any],
) -> None:
    """Bind the manufactured packet to the exact existing rich-page draft."""

    if rich_draft.get("status") != "draft":
        raise ReleaseAssemblyError("rich-page evidence is not a private draft")
    manufacturing = production_manifest.get("manufacturing")
    vibe_design = (
        manufacturing.get("vibe_design")
        if isinstance(manufacturing, Mapping)
        else None
    )
    if not isinstance(vibe_design, Mapping):
        raise ReleaseAssemblyError(
            "production manifest lacks manufacturing.vibe_design"
        )
    if production_manifest.get("candidate_id") != rich_draft.get("candidate_id"):
        raise ReleaseAssemblyError("rich-page draft candidate_id mismatch")
    draft_version = rich_draft.get("candidate_version")
    production_version = production_manifest.get("candidate_version")
    if (
        isinstance(draft_version, bool)
        or not isinstance(draft_version, int)
        or isinstance(production_version, bool)
        or not isinstance(production_version, int)
        or production_version != draft_version + 1
    ):
        raise ReleaseAssemblyError(
            "production manifest is not the lifecycle version after the rich-page draft"
        )
    for key in (
        "design_id",
        "slug",
        "history_id",
        "project_url",
        "project_sha256",
    ):
        value = rich_draft.get(key)
        if not isinstance(value, str) or not value:
            raise ReleaseAssemblyError(f"rich-page draft lacks {key}")
        if vibe_design.get(key) != value:
            raise ReleaseAssemblyError(
                f"production manifest vibe_design {key} mismatch"
            )
    draft_hashes = rich_draft.get("artifact_hashes")
    if not isinstance(draft_hashes, Mapping) or not draft_hashes:
        raise ReleaseAssemblyError("rich-page draft lacks artifact_hashes")
    if dict(vibe_design.get("artifact_hashes") or {}) != dict(draft_hashes):
        raise ReleaseAssemblyError(
            "production manifest vibe_design artifact_hashes mismatch"
        )


def _require_validated_price(
    market: Mapping[str, Any],
    production: Mapping[str, Any],
    production_manifest: Mapping[str, Any],
) -> float:
    price = production_manifest.get("price")
    if not isinstance(price, Mapping):
        raise ReleaseAssemblyError("production manifest lacks price")
    price_cents = market.get("price_cents")
    currency = market.get("currency")
    if (
        isinstance(price_cents, bool)
        or not isinstance(price_cents, int)
        or price_cents < 100
    ):
        raise ReleaseAssemblyError("market validation lacks a valid price_cents")
    if not isinstance(currency, str) or not currency:
        raise ReleaseAssemblyError("market validation lacks currency")
    if currency != "USD" or price.get("currency") != "USD":
        raise ReleaseAssemblyError("Factory publication price must be USD")
    if price_cents > 1_000_000:
        raise ReleaseAssemblyError("Factory publication price exceeds Vibe maximum")
    if price.get("price_cents") != price_cents or price.get("currency") != currency:
        raise ReleaseAssemblyError(
            "production manifest price does not match market validation"
        )
    listing = production_manifest.get("listing")
    sku = listing.get("sku") if isinstance(listing, Mapping) else None
    if (
        not isinstance(sku, str)
        or not sku
        or len(sku) > 128
        or any(ord(character) < 33 or ord(character) > 126 for character in sku)
    ):
        raise ReleaseAssemblyError(
            "production manifest listing.sku must be printable non-space ASCII"
        )
    manufacturing = production_manifest.get("manufacturing")
    if not isinstance(manufacturing, Mapping):
        raise ReleaseAssemblyError("production manifest lacks manufacturing")
    landed_cost_cents = _nonnegative_cents(production, "landed_cost_cents")
    if manufacturing.get("landed_cost_cents") != landed_cost_cents:
        raise ReleaseAssemblyError(
            "production manifest landed cost does not match production receipt"
        )
    if market.get("landed_cost_cents") != landed_cost_cents:
        raise ReleaseAssemblyError(
            "market validation landed cost does not match production"
        )
    fees_cents = _nonnegative_cents(market, "fees_cents")
    shipping_subsidy_cents = _nonnegative_cents(
        market, "shipping_subsidy_cents"
    )
    total_cost = landed_cost_cents + fees_cents + shipping_subsidy_cents
    if total_cost > price_cents:
        raise ReleaseAssemblyError("validated offer has negative gross margin")
    computed = (price_cents - total_cost) / price_cents
    claimed = _unit_float(market, "gross_margin")
    if abs(claimed - computed) > 0.001:
        raise ReleaseAssemblyError(
            "reported gross_margin does not match canonical cents-based costs"
        )
    return computed


def _require_exact_product_lineage(
    by_action: Mapping[str, ArtifactSnapshot],
    production_manifest: Mapping[str, Any],
) -> None:
    candidate_hash = _sha(production_manifest, "candidate_content_sha256")
    rules_artifact = by_action["candidate.rules"].content
    rule_document = {
        key: rules_artifact.get(key)
        for key in (
            "setup",
            "turn",
            "legal_actions",
            "end",
            "scoring",
            "ties",
            "rules_markdown",
        )
    }
    rules_hash = canonical_sha256(rule_document)
    if rules_artifact.get("rules_sha256") != rules_hash:
        raise ReleaseAssemblyError("candidate.rules rules_sha256 mismatch")
    if rules_artifact.get("candidate_content_sha256") != candidate_hash:
        raise ReleaseAssemblyError("candidate.rules candidate content mismatch")
    if production_manifest.get("rules_sha256") != rules_hash:
        raise ReleaseAssemblyError("production manifest rules_sha256 mismatch")
    manifest_rules = production_manifest.get("rules")
    if not isinstance(manifest_rules, Mapping):
        raise ReleaseAssemblyError("production manifest lacks rules")
    if manifest_rules.get("rules_sha256") != rules_hash:
        raise ReleaseAssemblyError("production manifest rules section hash mismatch")
    if manifest_rules.get("rules_markdown") != rules_artifact.get("rules_markdown"):
        raise ReleaseAssemblyError(
            "production manifest does not contain the exact accepted rules_markdown"
        )

    for action in (
        "rules.lint",
        "rules.adversary",
        "simulation.optimizer",
        "simulation.social",
        "simulation.explorer",
        "simulation.exploit",
        "human.prepare_blind_kit",
        "human.collect_blind_results",
        "physical.create_rich_draft",
        "physical.prototype_print",
        "physical.production_run",
        "market.validate_offer",
        "market.final_safety_ip",
    ):
        content = by_action[action].content
        if content.get("candidate_content_sha256") != candidate_hash:
            raise ReleaseAssemblyError(f"{action} candidate content mismatch")
        if content.get("rules_sha256") != rules_hash:
            raise ReleaseAssemblyError(f"{action} rules hash mismatch")

    blind_kit = by_action["human.prepare_blind_kit"].content
    kit_hash = validate_blind_kit(
        blind_kit,
        expected_candidate_content_sha256=candidate_hash,
        expected_rules_sha256=rules_hash,
    )
    human = by_action["human.collect_blind_results"].content
    validate_blind_human_evidence(
        human,
        expected_candidate_content_sha256=candidate_hash,
        expected_rules_sha256=rules_hash,
        expected_blind_kit_sha256=kit_hash,
    )

    rich = by_action["physical.create_rich_draft"].content
    prototype = by_action["physical.prototype_print"].content
    production = by_action["physical.production_run"].content
    market = by_action["market.validate_offer"].content
    manufacturing = production_manifest.get("manufacturing")
    design = (
        manufacturing.get("vibe_design")
        if isinstance(manufacturing, Mapping)
        else None
    )
    if not isinstance(design, Mapping):
        raise ReleaseAssemblyError("production manifest lacks Vibe design lineage")
    expected_artifacts = _validate_release_artifact_hashes(
        rich.get("artifact_hashes"), "rich-page artifact_hashes"
    )
    for key in ("rules_file_sha256", "project_sha256", "artifact_hashes"):
        expected = rich.get(key)
        if not expected:
            raise ReleaseAssemblyError(f"rich-page draft lacks {key}")
        if (
            prototype.get(key) != expected
            or production.get(key) != expected
            or market.get(key) != expected
            or design.get(key) != expected
        ):
            raise ReleaseAssemblyError(
                f"prototype, production, market, and rich draft {key} disagree"
            )
    if design.get("rules_sha256") != rules_hash:
        raise ReleaseAssemblyError("production manifest Vibe rules hash mismatch")
    if manifest_rules.get("rules_file_sha256") != rich.get("rules_file_sha256"):
        raise ReleaseAssemblyError(
            "production manifest rules file does not match the rich draft"
        )
    if dict(expected_artifacts) != dict(design.get("artifact_hashes") or {}):
        raise ReleaseAssemblyError(
            "production manifest printable artifacts do not match the rich draft"
        )

    manifest_evidence = production_manifest.get("evidence")
    assert isinstance(manifest_evidence, Mapping)
    blind_evidence = manifest_evidence.get("blind_human")
    assert isinstance(blind_evidence, Mapping)
    reward_items = human.get("reward_evidence")
    if not isinstance(reward_items, list) or len(reward_items) != 1:
        raise ReleaseAssemblyError(
            "blind human evidence must contain one reward aggregate"
        )
    reward_item = reward_items[0]
    if not isinstance(reward_item, Mapping):
        raise ReleaseAssemblyError("blind human reward evidence must be an object")
    expected_blind_evidence = {
        "evidence_id": reward_item.get("evidence_id"),
        "sample_size": len(human.get("trial_ids") or []),
        "blind_kit_sha256": kit_hash,
        "trial_ids_sha256": canonical_sha256(human.get("trial_ids")),
        "group_ids_sha256": canonical_sha256(human.get("group_ids")),
        "consent_provenance_sha256": canonical_sha256(
            human.get("consent_provenance")
        ),
        "trial_provenance_sha256": canonical_sha256(
            human.get("trial_provenance")
        ),
    }
    for key, expected in expected_blind_evidence.items():
        if blind_evidence.get(key) != expected:
            raise ReleaseAssemblyError(
                f"production manifest blind-human evidence {key} mismatch"
            )
    simulation_evidence = manifest_evidence.get("simulation")
    assert isinstance(simulation_evidence, Mapping)
    expected_simulation_hashes = {
        action: by_action[action].content_sha256
        for action in (
            "simulation.optimizer",
            "simulation.social",
            "simulation.explorer",
            "simulation.exploit",
        )
    }
    if dict(simulation_evidence.get("artifact_content_sha256") or {}) != expected_simulation_hashes:
        raise ReleaseAssemblyError(
            "production manifest simulation evidence lineage mismatch"
        )
    prototype_evidence = manifest_evidence.get("prototype")
    assert isinstance(prototype_evidence, Mapping)
    prototype_receipt = prototype.get("receipt")
    assert isinstance(prototype_receipt, Mapping)
    if prototype_evidence.get("receipt_sha256") != prototype_receipt.get(
        "receipt_sha256"
    ):
        raise ReleaseAssemblyError(
            "production manifest prototype evidence receipt mismatch"
        )


def _nonnegative_cents(value: Mapping[str, Any], key: str) -> int:
    result = value.get(key)
    if isinstance(result, bool) or not isinstance(result, int) or result < 0:
        raise ReleaseAssemblyError(f"{key} must be non-negative integer cents")
    return result


def _unique_latest_actions(
    artifacts: Sequence[ArtifactSnapshot],
) -> dict[str, ArtifactSnapshot]:
    ordered = sorted(
        artifacts,
        key=lambda artifact: (artifact.candidate_version, artifact.task_id),
    )
    result: dict[str, ArtifactSnapshot] = {}
    for artifact in ordered:
        result[artifact.action] = artifact
    return result


def _require_adapter_class(artifact: ArtifactSnapshot, expected: str) -> None:
    if artifact.executor != "adapter" or artifact.evidence_class != expected:
        raise ReleaseAssemblyError(
            f"{artifact.action} needs a passed {expected!r} adapter receipt"
        )


def _reward_evidence(by_action: Mapping[str, ArtifactSnapshot]) -> list[Evidence]:
    accepted_sources = {
        "human.collect_blind_results": {"held_out", "blind_human"},
        "physical.production_run": {"manufacturing"},
        "market.validate_offer": {"market"},
    }
    evidence: list[Evidence] = []
    seen: set[str] = set()
    for action, sources in accepted_sources.items():
        raw_items = by_action[action].content.get("reward_evidence")
        if not isinstance(raw_items, list) or not raw_items:
            raise ReleaseAssemblyError(f"{action} needs reward_evidence")
        if len(raw_items) != 1:
            raise ReleaseAssemblyError(
                f"{action} must provide one non-overlapping reward_evidence aggregate"
            )
        for raw in raw_items:
            if not isinstance(raw, Mapping):
                raise ReleaseAssemblyError("reward evidence entries must be objects")
            source = raw.get("source")
            if source not in sources:
                raise ReleaseAssemblyError(
                    f"{action} cannot assert reward source {source!r}"
                )
            evidence_id = raw.get("evidence_id")
            if not isinstance(evidence_id, str) or not evidence_id:
                raise ReleaseAssemblyError("reward evidence needs evidence_id")
            if evidence_id in seen:
                raise ReleaseAssemblyError("reward evidence ids must be unique")
            seen.add(evidence_id)
            for flag in (
                "verified",
                "surrogate",
                "same_model",
                "same_model_surrogate",
            ):
                if not isinstance(raw.get(flag), bool):
                    raise ReleaseAssemblyError(
                        f"reward evidence {evidence_id!r} needs explicit boolean {flag}"
                    )
            evaluator_id = raw.get("evaluator_id")
            if not isinstance(evaluator_id, str) or not evaluator_id.strip():
                raise ReleaseAssemblyError(
                    f"reward evidence {evidence_id!r} needs evaluator_id provenance"
                )
            candidate_model_id = raw.get("candidate_model_id")
            if candidate_model_id is not None and (
                not isinstance(candidate_model_id, str)
                or not candidate_model_id.strip()
            ):
                raise ReleaseAssemblyError(
                    f"reward evidence {evidence_id!r} candidate_model_id is invalid"
                )
            if action == "human.collect_blind_results":
                trial_ids = by_action[action].content.get("trial_ids")
                if not isinstance(trial_ids, list) or raw.get("sample_size") != len(
                    trial_ids
                ):
                    raise ReleaseAssemblyError(
                        "blind-human reward sample_size must equal its unique trial_ids"
                    )
            try:
                evidence.append(
                    Evidence(
                        source=source,
                        scores=raw.get("scores", {}),
                        verified=raw["verified"],
                        sample_size=raw.get("sample_size", 1),
                        confidence=raw.get("confidence", 1.0),
                        surrogate=raw["surrogate"],
                        same_model=raw["same_model"],
                        same_model_surrogate=raw["same_model_surrogate"],
                        evidence_id=evidence_id,
                        evaluator_id=evaluator_id,
                        candidate_model_id=candidate_model_id,
                    )
                )
            except (TypeError, ValueError) as exc:
                raise ReleaseAssemblyError(
                    f"invalid reward evidence {evidence_id!r}: {exc}"
                ) from exc
    return evidence


def _decision_reward(decision: ReleaseDecision) -> dict[str, Any]:
    reward = decision.reward
    return {
        "publication_allowed": reward.publication_allowed,
        "quality_score": reward.quality_score,
        "confidence": reward.confidence,
        "dimension_scores": dict(reward.dimension_scores),
        "source_domain_scores": {
            source: dict(scores)
            for source, scores in reward.source_domain_scores.items()
        },
        "eligible_samples": reward.eligible_samples,
        "held_out_samples": reward.held_out_samples,
        "external_samples": reward.external_samples,
        "excluded_evidence": reward.excluded_evidence,
        "failure_codes": list(reward.failure_codes),
        "warnings": list(reward.warnings),
    }


def _sha(value: Mapping[str, Any], key: str) -> str:
    result = value.get(key)
    if not _is_sha256(result):
        raise ReleaseAssemblyError(f"{key} must be a lowercase SHA-256 digest")
    return result


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and value.lower() == value
        and all(character in "0123456789abcdef" for character in value)
    )


def _match_optional_sha(actual: str, expected: str | None, label: str) -> None:
    if expected is None:
        return
    if not _is_sha256(expected):
        raise ReleaseAssemblyError(f"expected {label} must be a lowercase SHA-256 digest")
    if actual != expected:
        raise ReleaseAssemblyError(f"{label} hash mismatch")


def _trimmed_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ReleaseAssemblyError(f"{label} must be a non-empty trimmed string")
    return value


def _trimmed_string_list(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ReleaseAssemblyError(f"{label} must be a non-empty array")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_trimmed_string(item, f"{label}[{index}]"))
    return tuple(result)


def _positive_int(value: Mapping[str, Any], key: str) -> int:
    result = value.get(key)
    if isinstance(result, bool) or not isinstance(result, int) or result <= 0:
        raise ReleaseAssemblyError(f"{key} must be a positive integer")
    return result


def _positive_range(value: Any, label: str) -> tuple[int, int]:
    if not isinstance(value, Mapping):
        raise ReleaseAssemblyError(f"{label} must be an object")
    minimum = _positive_int(value, "min")
    maximum = _positive_int(value, "max")
    if minimum > maximum:
        raise ReleaseAssemblyError(f"{label} min must not exceed max")
    return minimum, maximum


def _validate_release_artifact_hashes(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, Mapping) or not value:
        raise ReleaseAssemblyError(f"{label} must be a non-empty object")
    result: dict[str, str] = {}
    for path, digest in value.items():
        if not isinstance(path, str) or not path or path != path.strip():
            raise ReleaseAssemblyError(f"{label} paths must be non-empty strings")
        if path.startswith("/") or ".." in path.split("/"):
            raise ReleaseAssemblyError(f"{label} contains an unsafe artifact path")
        if not _is_sha256(digest):
            raise ReleaseAssemblyError(f"{label}[{path!r}] must be a SHA-256 digest")
        result[path] = digest
    if not any(is_printable_cad_artifact_path(path) for path in result):
        raise ReleaseAssemblyError(
            f"{label} needs at least one printable .stl, .3mf, or .obj artifact"
        )
    return result


def _nonempty_string(
    value: Mapping[str, Any], key: str, action: str
) -> str:
    result = value.get(key)
    if (
        not isinstance(result, str)
        or not result.strip()
        or result != result.strip()
    ):
        raise ReleaseAssemblyError(
            f"{action} manufacturing receipt {key} must be a non-empty trimmed string"
        )
    return result


def _true(value: Mapping[str, Any], key: str) -> bool:
    if value.get(key) is not True:
        return False
    return True


def _nonnegative_int(value: Mapping[str, Any], key: str) -> int:
    result = value.get(key)
    if isinstance(result, bool) or not isinstance(result, int) or result < 0:
        raise ReleaseAssemblyError(f"{key} must be a non-negative integer")
    return result


def _unit_float(value: Mapping[str, Any], key: str) -> float:
    result = value.get(key)
    if isinstance(result, bool) or not isinstance(result, (int, float)):
        raise ReleaseAssemblyError(f"{key} must be a number between zero and one")
    number = float(result)
    if not 0.0 <= number <= 1.0:
        raise ReleaseAssemblyError(f"{key} must be a number between zero and one")
    return number


__all__ = [
    "ArtifactSnapshot",
    "ReleaseAssemblyError",
    "artifact_manifest",
    "assess_release",
    "build_publication_packet",
    "canonical_sha256",
    "compute_rules_pdf_sha256",
    "validate_blind_human_evidence",
    "validate_blind_kit",
    "validate_distinct_manufacturing_receipts",
    "validate_manufacturing_receipt",
    "validate_production_manifest",
]
