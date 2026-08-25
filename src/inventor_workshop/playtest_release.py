"""Workshop-owned release semantics for every Playtest implementation.

The Playtest worker is replaceable; the release bar is not.  A result name,
``passed=true``, or an AI-authored sentence cannot authorize Instructions.  This
module validates exact evidence documents and capability-specific measurements
against the sealed Make and Playtest manifests before the Workshop advances.

Custom adapters may embed :class:`CapabilityReleaseProof` under
``evidence["release_proof"]``.  The shared Playtest's existing exact print and
motion receipt shapes are also understood, so adapters do not have to share an
implementation class in order to satisfy the common contract.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .artifacts import MAX_FILE_BYTES, build_artifact_manifest
from .errors import ContractError
from .jobs import Made, Need, Playtested
from .models import (
    MAX_EVIDENCE_JSON_BYTES,
    PlaytestResult,
    require_exact_version,
    require_json_mapping,
    require_safe_evidence_path,
    require_sha256,
    require_utc_timestamp,
)
from .toys import ToyBlueprint


_ROLE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SCOPES = frozenset(("product", "playtest"))
_RELEASE_PROOF_CLASSES = {
    "mechanical-test": "computed-mechanical-proof",
    "print-test": "exact-slicer-proof",
    "motion-test": "kinematic-motion-proof",
    "classic-rules-test": "classic-rule-conformance-proof",
    "science-test": "source-bound-science-proof",
    "world-test": "reference-bound-world-proof",
    "game-simulation": "seeded-game-analysis-proof",
}
_PROOF_CAPABILITIES = frozenset(_RELEASE_PROOF_CLASSES)
_GAME_STYLES = frozenset(("optimizing", "social", "exploratory", "adversarial"))
_RELEASE_RECEIPT_KIND = "workshop.capability-release-receipt"
_RECEIPT_ROLES = {
    "mechanical-test": frozenset(("mechanical-receipt",)),
    "print-test": frozenset(("slicer-receipt",)),
    "motion-test": frozenset(("motion-receipt",)),
    "classic-rules-test": frozenset(("reference-rules", "game-traces")),
    "science-test": frozenset(("science-sources", "comprehension-traces")),
    "world-test": frozenset(
        ("consent-record", "reference-material", "likeness-traces")
    ),
}
_DISALLOWED_PROVIDER_METHODS = frozenset(
    ("language-model-opinion", "model-opinion", "self-report", "trust-me")
)


def _plain_json(value: Any, label: str) -> Any:
    require_json_mapping({"value": value}, label)
    try:
        return json.loads(
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("%s must be finite JSON" % label) from exc


def _nonempty_text(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 2_048
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded non-empty text" % label)
    return value


def _json_sha256(value: Any) -> str:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("release receipt contains non-canonical JSON") from exc
    return hashlib.sha256(payload).hexdigest()


def _json_text(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("release receipt contains non-canonical JSON") from exc


def _provider_identity(value: Any, label: str) -> Dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {
        "name",
        "version",
        "config_sha256",
        "method_class",
    }:
        raise ContractError("%s provider identity is incomplete" % label)
    name = _nonempty_text(value.get("name"), "%s provider name" % label)
    version = require_exact_version(
        value.get("version"), "%s provider version" % label
    )
    config = require_sha256(
        value.get("config_sha256"), "%s provider config sha256" % label
    )
    method = _nonempty_text(
        value.get("method_class"), "%s provider method class" % label
    )
    if method.casefold() in _DISALLOWED_PROVIDER_METHODS:
        raise ContractError("a language-model opinion alone is not release proof")
    return {
        "name": name,
        "version": version,
        "config_sha256": config,
        "method_class": method,
    }


def _receipt_payload(
    receipts: Mapping[str, Mapping[str, Any]], role: str
) -> Mapping[str, Any]:
    document = receipts.get(role)
    payload = document.get("payload") if isinstance(document, Mapping) else None
    if not isinstance(payload, Mapping) or not payload:
        raise ContractError("%s receipt payload is missing" % role)
    return payload


@dataclass(frozen=True)
class ReleaseProofSource:
    """One exact product or Playtest file used by a release proof."""

    role: str
    scope: str
    path: str
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.role, str) or not _ROLE.fullmatch(self.role):
            raise ContractError("release proof source role is invalid")
        if self.scope not in _SCOPES:
            raise ContractError("release proof source scope must be product or playtest")
        require_safe_evidence_path(self.path, "release proof source path")
        require_sha256(self.sha256, "release proof source sha256")

    @classmethod
    def from_dict(cls, value: Any) -> "ReleaseProofSource":
        if not isinstance(value, Mapping) or set(value) != {
            "role",
            "scope",
            "path",
            "sha256",
        }:
            raise ContractError("release proof source fields are invalid")
        return cls(value["role"], value["scope"], value["path"], value["sha256"])

    def to_dict(self) -> Dict[str, str]:
        return {
            "role": self.role,
            "scope": self.scope,
            "path": self.path,
            "sha256": self.sha256,
        }


@dataclass(frozen=True)
class CapabilityReleaseProof:
    """Engine-neutral, exact-byte proof supplied by a Playtest adapter."""

    capability: str
    artifact_sha256: str
    proof_class: str
    sources: Sequence[ReleaseProofSource]
    measurements: Mapping[str, Any]
    schema_version: int = 1

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("release proof schema_version must be 1")
        if self.capability not in _PROOF_CAPABILITIES:
            raise ContractError("release proof capability is not a release capability")
        if self.proof_class != _RELEASE_PROOF_CLASSES[self.capability]:
            raise ContractError("release proof class does not match its capability")
        require_sha256(self.artifact_sha256, "release proof artifact sha256")
        if (
            isinstance(self.sources, (str, bytes, Mapping))
            or not isinstance(self.sources, Sequence)
            or not self.sources
            or len(self.sources) > 256
            or not all(isinstance(item, ReleaseProofSource) for item in self.sources)
        ):
            raise ContractError("release proof requires typed bounded sources")
        source_identities = [(item.scope, item.path) for item in self.sources]
        if len(source_identities) != len(set(source_identities)):
            raise ContractError(
                "one release proof file cannot be relabelled as multiple sources"
            )
        if not isinstance(self.measurements, Mapping) or not self.measurements:
            raise ContractError("release proof measurements must be a non-empty object")
        measurements = _plain_json(dict(self.measurements), "release proof measurements")
        object.__setattr__(self, "sources", tuple(self.sources))
        object.__setattr__(self, "measurements", measurements)

    @classmethod
    def from_dict(cls, value: Any) -> "CapabilityReleaseProof":
        if not isinstance(value, Mapping) or set(value) != {
            "schema_version",
            "capability",
            "artifact_sha256",
            "proof_class",
            "sources",
            "measurements",
        }:
            raise ContractError("release proof fields are invalid")
        raw_sources = value["sources"]
        if isinstance(raw_sources, (str, bytes, Mapping)) or not isinstance(
            raw_sources, Sequence
        ):
            raise ContractError("release proof sources must be a sequence")
        return cls(
            capability=value["capability"],
            artifact_sha256=value["artifact_sha256"],
            proof_class=value["proof_class"],
            sources=tuple(ReleaseProofSource.from_dict(item) for item in raw_sources),
            measurements=value["measurements"],
            schema_version=value["schema_version"],
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "capability": self.capability,
            "artifact_sha256": self.artifact_sha256,
            "proof_class": self.proof_class,
            "sources": [item.to_dict() for item in self.sources],
            "measurements": _plain_json(
                dict(self.measurements), "release proof measurements"
            ),
        }


def _int_measurement(
    measurements: Mapping[str, Any],
    name: str,
    *,
    minimum: Optional[int] = None,
    maximum: Optional[int] = None,
) -> int:
    value = measurements.get(name)
    if type(value) is not int:
        raise ContractError("release proof %s must be an integer" % name)
    if minimum is not None and value < minimum:
        raise ContractError("release proof %s is below its minimum" % name)
    if maximum is not None and value > maximum:
        raise ContractError("release proof %s exceeds its maximum" % name)
    return value


def _true_measurement(measurements: Mapping[str, Any], name: str) -> None:
    if measurements.get(name) is not True:
        raise ContractError("release proof requires %s=true" % name)


def _roles(
    proof: CapabilityReleaseProof, role: str, *, scope: Optional[str] = None
) -> Tuple[ReleaseProofSource, ...]:
    selected = tuple(
        source
        for source in proof.sources
        if source.role == role and (scope is None or source.scope == scope)
    )
    if not selected:
        raise ContractError("release proof lacks %s source" % role)
    return selected


def _one_role(
    proof: CapabilityReleaseProof, role: str, *, scope: Optional[str] = None
) -> ReleaseProofSource:
    selected = _roles(proof, role, scope=scope)
    if len(selected) != 1:
        raise ContractError("release proof requires exactly one %s source" % role)
    return selected[0]


def _validate_mechanical(proof: CapabilityReleaseProof) -> None:
    step = _one_role(proof, "step-model", scope="product")
    _one_role(proof, "mechanical-receipt", scope="playtest")
    if Path(step.path).suffix.casefold() not in {".step", ".stp"}:
        raise ContractError("mechanical proof step-model must be STEP")
    measurements = proof.measurements
    _true_measurement(measurements, "brep_valid")
    for name in (
        "interference_cases",
        "fit_cases",
        "assembly_paths_tested",
        "motion_cases",
        "load_cases",
        "failure_modes_tested",
    ):
        _int_measurement(measurements, name, minimum=1)
    for name in (
        "forbidden_intersections",
        "fit_failures",
        "assembly_failures",
        "motion_failures",
        "load_failures",
        "unresolved_critical_failures",
    ):
        _int_measurement(measurements, name, minimum=0, maximum=0)


def _expected_part_stls(product_inventory: Mapping[str, str]) -> Tuple[str, ...]:
    all_stls = tuple(
        sorted(path for path in product_inventory if path.casefold().endswith(".stl"))
    )
    parts = tuple(
        path
        for path in all_stls
        if Path(path).name.casefold().startswith("part_")
    )
    if parts:
        return parts
    excluded = ("assembled", "product", "print-plate", "print_plate")
    return tuple(
        path
        for path in all_stls
        if not any(token in Path(path).stem.casefold() for token in excluded)
    )


def _validate_slicer_measurements(
    measurements: Mapping[str, Any], product_inventory: Mapping[str, str]
) -> None:
    _nonempty_text(measurements.get("slicer"), "release proof slicer")
    require_exact_version(
        measurements.get("slicer_version"), "release proof slicer version"
    )
    profiles = measurements.get("profiles")
    if (
        not isinstance(profiles, Mapping)
        or len(profiles) < 3
        or not all(isinstance(role, str) and role for role in profiles)
    ):
        raise ContractError("print proof requires at least three named profiles")
    for digest in profiles.values():
        if isinstance(digest, Mapping):
            digest = digest.get("sha256")
        require_sha256(digest, "print profile sha256")
    parts = measurements.get("parts")
    if not isinstance(parts, list) or not parts:
        raise ContractError("print proof requires per-part slicer receipts")
    expected = _expected_part_stls(product_inventory)
    if not expected:
        raise ContractError("print proof has no sealed per-part STL inventory")
    observed = []
    for part in parts:
        if not isinstance(part, Mapping):
            raise ContractError("print proof part receipt must be an object")
        input_ref = part.get("input_ref")
        if not isinstance(input_ref, str) or input_ref in observed:
            raise ContractError("print proof part refs must be unique paths")
        observed.append(input_ref)
        if product_inventory.get(input_ref) != part.get("input_sha256"):
            raise ContractError("print proof part input is not the sealed STL")
        output_sha256 = part.get("gcode_sha256", part.get("output_sha256"))
        require_sha256(output_sha256, "print proof G-code sha256")
        if "gcode_bytes" in part:
            _int_measurement(part, "gcode_bytes", minimum=1)
        if "returncode" in part:
            _int_measurement(part, "returncode", minimum=0, maximum=0)
    if tuple(sorted(observed)) != expected:
        raise ContractError("print proof did not slice every sealed per-part STL")
    _int_measurement(measurements, "slicer_errors", minimum=0, maximum=0)


def _validate_print(
    proof: CapabilityReleaseProof,
    product_inventory: Mapping[str, str],
    evidence_root: Path,
) -> None:
    part_sources = _roles(proof, "print-part", scope="product")
    _one_role(proof, "slicer-receipt", scope="playtest")
    expected = _expected_part_stls(product_inventory)
    if tuple(sorted(source.path for source in part_sources)) != expected:
        raise ContractError("print proof sources omit a sealed per-part STL")
    _validate_slicer_measurements(proof.measurements, product_inventory)

    # Engine-neutral/custom print proofs must seal the actual profiles and
    # G-code.  A digest typed into a JSON measurement is not evidence that
    # those bytes ever existed.  The shared inline Prusa receipt remains a
    # separate, already byte-producing trusted path below.
    profile_sources = _roles(proof, "slicer-profile", scope="playtest")
    gcode_sources = _roles(proof, "gcode-output", scope="playtest")
    profiles = proof.measurements["profiles"]
    if len(profile_sources) < 3 or len(profile_sources) != len(profiles):
        raise ContractError("print proof must seal every named slicer profile")
    expected_profiles = {source.path: source.sha256 for source in profile_sources}
    observed_profiles = {}
    for role, profile in profiles.items():
        if not isinstance(profile, Mapping) or set(profile) != {"path", "sha256"}:
            raise ContractError("custom print profile must name sealed profile bytes")
        path = profile["path"]
        digest = profile["sha256"]
        if not isinstance(path, str) or path in observed_profiles:
            raise ContractError("custom print profile paths must be unique")
        require_sha256(digest, "print profile sha256")
        if expected_profiles.get(path) != digest:
            raise ContractError("custom print profile is not sealed Playtest evidence")
        observed_profiles[path] = digest
        _load_source_bytes(
            evidence_root,
            ReleaseProofSource("slicer-profile", "playtest", path, digest),
            "print profile %s" % role,
        )
    if observed_profiles != expected_profiles:
        raise ContractError("print proof profile measurements omit sealed bytes")

    expected_gcode = {source.path: source.sha256 for source in gcode_sources}
    observed_gcode = {}
    for part in proof.measurements["parts"]:
        ref = part.get("gcode_ref")
        digest = part.get("gcode_sha256", part.get("output_sha256"))
        if not isinstance(ref, str) or ref in observed_gcode:
            raise ContractError("custom print part must name unique sealed G-code")
        if expected_gcode.get(ref) != digest:
            raise ContractError("custom print G-code is not sealed Playtest evidence")
        payload = _load_source_bytes(
            evidence_root,
            ReleaseProofSource("gcode-output", "playtest", ref, digest),
            "print G-code",
            maximum_bytes=MAX_FILE_BYTES,
        )
        if len(payload) != part.get("gcode_bytes"):
            raise ContractError("custom print G-code byte count is not exact")
        header = payload[: 64 * 1024].lower()
        if (
            proof.measurements["slicer"].encode("utf-8").lower() not in header
            or proof.measurements["slicer_version"].encode("ascii") not in header
            or re.search(rb"(?m)^[GMT][0-9]+(?:\s|$)", payload[: 64 * 1024]) is None
        ):
            raise ContractError("custom print output is not identified slicer G-code")
        observed_gcode[ref] = digest
    if observed_gcode != expected_gcode or len(observed_gcode) != len(expected):
        raise ContractError("print proof must seal one G-code output per part")


def _validate_motion(proof: CapabilityReleaseProof) -> None:
    step = _one_role(proof, "step-model", scope="product")
    _one_role(proof, "motion-receipt", scope="playtest")
    if Path(step.path).suffix.casefold() not in {".step", ".stp"}:
        raise ContractError("motion proof step-model must be STEP")
    measurements = proof.measurements
    _int_measurement(measurements, "states_tested", minimum=2)
    _true_measurement(measurements, "continuous_sweep")
    for name in (
        "tolerance_cases_tested",
        "load_cases_tested",
        "orientations_tested",
        "wear_cycles",
        "misuse_cases_tested",
    ):
        _int_measurement(measurements, name, minimum=1)
    for name in ("collisions", "stalls", "failures"):
        _int_measurement(measurements, name, minimum=0, maximum=0)


def _validate_classic(proof: CapabilityReleaseProof) -> None:
    _one_role(proof, "edition-rules", scope="product")
    _one_role(proof, "reference-rules", scope="playtest")
    _one_role(proof, "game-traces", scope="playtest")
    measurements = proof.measurements
    _int_measurement(measurements, "seeded_games", minimum=1)
    _int_measurement(measurements, "rule_conformance_cases", minimum=1)
    _int_measurement(measurements, "rule_mismatches", minimum=0, maximum=0)
    _int_measurement(measurements, "role_legibility_cases", minimum=1)
    _int_measurement(measurements, "role_legibility_failures", minimum=0, maximum=0)


def _validate_science(proof: CapabilityReleaseProof) -> None:
    _one_role(proof, "source-model", scope="product")
    _one_role(proof, "science-sources", scope="playtest")
    _one_role(proof, "comprehension-traces", scope="playtest")
    measurements = proof.measurements
    _int_measurement(measurements, "accuracy_cases", minimum=1)
    _int_measurement(measurements, "accuracy_failures", minimum=0, maximum=0)
    _int_measurement(measurements, "simplifications_checked", minimum=1)
    _int_measurement(measurements, "dishonest_simplifications", minimum=0, maximum=0)
    _int_measurement(measurements, "comprehension_traces", minimum=1)
    _int_measurement(measurements, "comprehension_failures", minimum=0, maximum=0)


def _validate_world(proof: CapabilityReleaseProof) -> None:
    _one_role(proof, "personalization-map", scope="product")
    _one_role(proof, "consent-record", scope="playtest")
    _one_role(proof, "reference-material", scope="playtest")
    _one_role(proof, "likeness-traces", scope="playtest")
    measurements = proof.measurements
    _true_measurement(measurements, "consent_verified")
    _int_measurement(measurements, "personalization_features", minimum=1)
    _int_measurement(measurements, "likeness_cases", minimum=1)
    _int_measurement(measurements, "recognition_failures", minimum=0, maximum=0)
    _int_measurement(measurements, "consent_violations", minimum=0, maximum=0)


def _load_source_bytes(
    root: Path,
    source: ReleaseProofSource,
    label: str,
    *,
    maximum_bytes: int = MAX_EVIDENCE_JSON_BYTES,
) -> bytes:
    path = root / source.path
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
        if path.is_symlink() or not resolved.is_file():
            raise OSError("not a regular file")
        payload = resolved.read_bytes()
    except (OSError, ValueError) as exc:
        raise ContractError("%s source is missing or unsafe" % label) from exc
    if not payload or len(payload) > maximum_bytes:
        raise ContractError("%s source is empty or oversized" % label)
    if hashlib.sha256(payload).hexdigest() != source.sha256:
        raise ContractError("%s source bytes changed" % label)
    return payload


def _load_json_file(root: Path, source: ReleaseProofSource, label: str) -> Any:
    payload = _load_source_bytes(root, source, label)
    try:
        return json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("%s source must be valid UTF-8 JSON" % label) from exc


def _receipt_dependency_hashes(
    proof: CapabilityReleaseProof,
) -> Dict[str, str]:
    receipt_roles = _RECEIPT_ROLES.get(proof.capability, frozenset())
    return {
        "%s:%s" % (source.scope, source.path): source.sha256
        for source in proof.sources
        if source.role not in receipt_roles
    }


def _validate_legacy_shared_mechanical_receipt(
    document: Any,
    proof: CapabilityReleaseProof,
    product_inventory: Mapping[str, str],
) -> bool:
    """Accept the Workshop's already-sealed mechanical receipt.

    This is not a permissive legacy JSON shape.  Its kind has one fixed
    capability and proof class, and its exact source and measurement maps are
    checked here.  Custom adapters should emit the engine-neutral envelope.
    """

    if not isinstance(document, Mapping) or document.get("kind") != (
        "workshop.digital-mechanical-simulation"
    ):
        return False
    if (
        proof.capability != "mechanical-test"
        or proof.proof_class != "computed-mechanical-proof"
        or document.get("schema_version") != 1
        or document.get("artifact_sha256") != proof.artifact_sha256
        or document.get("measurements") != dict(proof.measurements)
        or not isinstance(document.get("source_sha256"), Mapping)
        or not isinstance(document.get("plan"), Mapping)
        or not document["plan"]
        or not isinstance(document.get("fit_cases"), list)
        or not isinstance(document.get("assembly_motion_manifest"), Mapping)
        or not isinstance(document.get("assembly_motion_result"), Mapping)
        or not isinstance(document.get("load_cases"), list)
        or not isinstance(document.get("not_proven"), list)
        or not _nonempty_text(document.get("claim_scope"), "mechanical claim scope")
    ):
        raise ContractError("shared mechanical receipt is incomplete or mismatched")
    source_sha256 = document["source_sha256"]
    if not source_sha256 or any(
        not isinstance(path, str) or product_inventory.get(path) != digest
        for path, digest in source_sha256.items()
    ):
        raise ContractError("shared mechanical receipt does not bind sealed sources")
    for source in proof.sources:
        if source.scope == "product" and source_sha256.get(source.path) != source.sha256:
            raise ContractError("shared mechanical receipt omits a proof source")
    return True


def _validate_release_receipts(
    proof: CapabilityReleaseProof,
    *,
    product_inventory: Mapping[str, str],
    evidence_root: Path,
) -> Mapping[str, Mapping[str, Any]]:
    """Parse and correlate every Playtest receipt in a custom release proof."""

    expected_roles = _RECEIPT_ROLES.get(proof.capability)
    if expected_roles is None:
        return {}
    for role in expected_roles:
        _one_role(proof, role, scope="playtest")
    allowed_non_receipts = (
        frozenset(("slicer-profile", "gcode-output"))
        if proof.capability == "print-test"
        else frozenset()
    )
    for source in proof.sources:
        if (
            source.scope == "playtest"
            and source.role not in expected_roles
            and source.role not in allowed_non_receipts
        ):
            raise ContractError("release proof contains an unparsed Playtest source")

    expected_dependencies = _receipt_dependency_hashes(proof)
    documents: Dict[str, Mapping[str, Any]] = {}
    for role in sorted(expected_roles):
        source = _one_role(proof, role, scope="playtest")
        document = _load_json_file(evidence_root, source, "%s receipt" % role)
        if (
            role == "mechanical-receipt"
            and _validate_legacy_shared_mechanical_receipt(
                document, proof, product_inventory
            )
        ):
            documents[role] = document
            continue
        if not isinstance(document, Mapping) or set(document) != {
            "schema_version",
            "kind",
            "artifact_sha256",
            "capability",
            "proof_class",
            "role",
            "source_sha256",
            "measurements",
            "payload",
        }:
            raise ContractError("%s is not a canonical release receipt" % role)
        if (
            document.get("schema_version") != 1
            or document.get("kind") != _RELEASE_RECEIPT_KIND
            or document.get("artifact_sha256") != proof.artifact_sha256
            or document.get("capability") != proof.capability
            or document.get("proof_class") != proof.proof_class
            or document.get("role") != role
            or document.get("source_sha256") != expected_dependencies
            or document.get("measurements") != dict(proof.measurements)
            or not isinstance(document.get("payload"), Mapping)
            or not document["payload"]
        ):
            raise ContractError("%s does not match its exact release proof" % role)
        documents[role] = document
    return documents


def _product_json_for_role(
    proof: CapabilityReleaseProof,
    product_root: Path,
    role: str,
    label: str,
) -> Mapping[str, Any]:
    source = _one_role(proof, role, scope="product")
    document = _load_json_file(product_root, source, label)
    if not isinstance(document, Mapping):
        raise ContractError("%s must be a JSON object" % label)
    return document


def _validate_classic_receipt_semantics(
    proof: CapabilityReleaseProof,
    receipts: Mapping[str, Mapping[str, Any]],
    product_root: Path,
) -> None:
    reference = _receipt_payload(receipts, "reference-rules")
    traces = _receipt_payload(receipts, "game-traces")
    provider = _provider_identity(reference.get("provider"), "classic")
    if _provider_identity(traces.get("provider"), "classic traces") != provider:
        raise ContractError("classic receipts name different providers")

    rules_model = reference.get("rules_model")
    if not isinstance(rules_model, Mapping) or not rules_model:
        raise ContractError("classic receipt lacks a structured reference rules model")
    if reference.get("rules_model_sha256") != _json_sha256(rules_model):
        raise ContractError("classic reference rules bytes do not match their hash")
    comparison = reference.get("comparison")
    if not isinstance(comparison, Mapping) or not comparison:
        raise ContractError("classic receipt lacks an exact edition comparison")

    edition = _product_json_for_role(
        proof, product_root, "edition-rules", "classic edition rules"
    )
    if "known_game" in edition and comparison.get("declaration_known_game") != edition.get(
        "known_game"
    ):
        raise ContractError("classic comparison names another edition game")
    if "rules_reference" in edition and comparison.get("rules_reference") != edition.get(
        "rules_reference"
    ):
        raise ContractError("classic comparison names another rules reference")
    if comparison.get("no_rule_mutation_fields") is not True:
        raise ContractError("classic edition comparison did not preserve the rules")

    conformance = reference.get("conformance_cases")
    if not isinstance(conformance, list) or not conformance:
        raise ContractError("classic receipt lacks rule conformance cases")
    case_ids = set()
    conformance_failures = 0
    for case in conformance:
        if (
            not isinstance(case, Mapping)
            or set(case) != {"case_id", "passed", "source"}
            or not isinstance(case.get("case_id"), str)
            or not case["case_id"]
            or case["case_id"] in case_ids
            or type(case.get("passed")) is not bool
            or not isinstance(case.get("source"), str)
            or not case["source"]
        ):
            raise ContractError("classic conformance case is incomplete")
        case_ids.add(case["case_id"])
        conformance_failures += not case["passed"]

    games = traces.get("games")
    if not isinstance(games, list) or not games:
        raise ContractError("classic receipt lacks seeded game traces")
    seeds = set()
    trace_mismatches = 0
    for game in games:
        if (
            not isinstance(game, Mapping)
            or type(game.get("seed")) is not int
            or game["seed"] < 0
            or game["seed"] in seeds
            or game.get("completed") is not True
            or type(game.get("rule_mismatches")) is not int
            or game["rule_mismatches"] < 0
        ):
            raise ContractError("classic game trace is incomplete or duplicated")
        seeds.add(game["seed"])
        trace_mismatches += game["rule_mismatches"]

    role_cases = traces.get("role_cases")
    if not isinstance(role_cases, list) or not role_cases:
        raise ContractError("classic receipt lacks CAD-bound physical role cases")
    product_sources = {
        source.path: source.sha256
        for source in proof.sources
        if source.scope == "product"
    }
    part_ids = set()
    geometry_hashes = set()
    for case in role_cases:
        if not isinstance(case, Mapping) or set(case) != {
            "part_id",
            "geometry",
            "geometry_sha256",
            "step_path",
            "step_sha256",
            "stl_path",
            "stl_sha256",
            "exact_body_bound",
        }:
            raise ContractError("classic physical role case is incomplete")
        part_id = case.get("part_id")
        geometry = case.get("geometry")
        if (
            not isinstance(part_id, str)
            or not part_id
            or part_id in part_ids
            or not isinstance(geometry, Mapping)
            or set(geometry) != {"shape", "size_mm"}
            or geometry.get("shape") not in ("box", "cylinder")
            or not isinstance(geometry.get("size_mm"), Mapping)
            or set(geometry["size_mm"]) != {"x", "y", "z"}
            or any(
                not isinstance(geometry["size_mm"].get(axis), (int, float))
                or isinstance(geometry["size_mm"].get(axis), bool)
                or not 0 < float(geometry["size_mm"][axis]) <= 1_000
                for axis in ("x", "y", "z")
            )
            or case.get("geometry_sha256") != _json_sha256(geometry)
            or not isinstance(case.get("step_path"), str)
            or Path(case["step_path"]).suffix.casefold() not in (".step", ".stp")
            or product_sources.get(case["step_path"]) != case.get("step_sha256")
            or not isinstance(case.get("stl_path"), str)
            or Path(case["stl_path"]).suffix.casefold() != ".stl"
            or product_sources.get(case["stl_path"]) != case.get("stl_sha256")
            or case.get("exact_body_bound") is not True
        ):
            raise ContractError("classic physical role case is not bound to exact CAD")
        part_ids.add(part_id)
        geometry_hashes.add(case["geometry_sha256"])
    if traces.get("distinct_geometry_signatures") != len(geometry_hashes):
        raise ContractError("classic role signature counter was not replayed")
    role_failures = 0 if len(geometry_hashes) >= 2 else 1
    measurements = proof.measurements
    if (
        measurements.get("seeded_games") != len(games)
        or measurements.get("rule_conformance_cases") != len(conformance)
        or measurements.get("rule_mismatches")
        != conformance_failures + trace_mismatches
        or measurements.get("role_legibility_cases") != len(role_cases)
        or measurements.get("role_legibility_failures") != role_failures
    ):
        raise ContractError("classic measurements do not match replayed receipt cases")


def _science_contract(
    document: Mapping[str, Any],
) -> Tuple[Mapping[str, Any], list, Optional[Mapping[str, Any]]]:
    plan = document.get("digital_test_plan")
    lane_contract = plan.get("invent_lane_contract") if isinstance(plan, Mapping) else None
    if isinstance(lane_contract, Mapping):
        source_model = lane_contract.get("source_model")
        simplifications = lane_contract.get("simplifications")
        scale = lane_contract.get("scale")
    else:
        source_model = document.get("source_model", document)
        simplifications = document.get("simplifications")
        scale = document.get("scale")
    if not isinstance(source_model, Mapping) or not isinstance(simplifications, list):
        raise ContractError("science product source lacks its exact model and simplifications")
    if scale is not None and not isinstance(scale, Mapping):
        raise ContractError("science product scale must be a JSON object")
    return source_model, simplifications, scale


def _validate_science_receipt_semantics(
    proof: CapabilityReleaseProof,
    receipts: Mapping[str, Mapping[str, Any]],
    product_root: Path,
) -> None:
    source_payload = _receipt_payload(receipts, "science-sources")
    trace_payload = _receipt_payload(receipts, "comprehension-traces")
    provider = _provider_identity(source_payload.get("provider"), "science")
    if _provider_identity(trace_payload.get("provider"), "science traces") != provider:
        raise ContractError("science receipts name different providers")
    product_document = _product_json_for_role(
        proof, product_root, "source-model", "science source model"
    )
    source_model, simplifications, scale = _science_contract(product_document)
    if source_payload.get("source_model_sha256") != _json_sha256(source_model):
        raise ContractError("science receipt belongs to another source model")
    required_ids = source_model.get("source_ids")
    if (
        not isinstance(required_ids, list)
        or not required_ids
        or len(required_ids) != len(set(required_ids))
        or not all(isinstance(item, str) and item for item in required_ids)
    ):
        raise ContractError("science source model lacks unique source ids")
    required_ids_set = set(required_ids)

    sources = source_payload.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ContractError("science receipt lacks exact public source bytes")
    observed_ids = set()
    source_bytes_by_id: Dict[str, bytes] = {}
    for source in sources:
        if not isinstance(source, Mapping) or set(source) != {
            "source_id",
            "title",
            "publisher",
            "url",
            "retrieved_at",
            "media_type",
            "content_sha256",
            "content_bytes",
            "content_encoding",
            "content_base64",
        }:
            raise ContractError("science source receipt is incomplete")
        source_id = source.get("source_id")
        try:
            parsed = urllib.parse.urlsplit(source.get("url"))
            content = base64.b64decode(source.get("content_base64"), validate=True)
        except (TypeError, ValueError, binascii.Error) as exc:
            raise ContractError("science source bytes or URL are invalid") from exc
        if (
            not isinstance(source_id, str)
            or not source_id
            or source_id in observed_ids
            or source_id not in required_ids_set
            or not _nonempty_text(source.get("title"), "science source title")
            or not _nonempty_text(source.get("publisher"), "science source publisher")
            or parsed.scheme != "https"
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or source.get("content_encoding") != "base64"
            or not content
            or len(content) != source.get("content_bytes")
            or hashlib.sha256(content).hexdigest() != source.get("content_sha256")
        ):
            raise ContractError("science source is not exact public evidence")
        require_utc_timestamp(source.get("retrieved_at"), "science source retrieved_at")
        observed_ids.add(source_id)
        source_bytes_by_id[source_id] = content
    if observed_ids != required_ids_set:
        raise ContractError("science receipt omits a source named by Invent")

    accuracy = source_payload.get("accuracy_cases")
    if not isinstance(accuracy, list) or not accuracy:
        raise ContractError("science receipt lacks accuracy comparison cases")
    accuracy_ids = set()
    accuracy_failures = 0
    for case in accuracy:
        if not isinstance(case, Mapping) or set(case) != {
            "case_id",
            "source_ids",
            "product_field",
            "expected",
            "observed",
            "source_excerpt",
            "source_excerpt_sha256",
            "passed",
        }:
            raise ContractError("science accuracy case is incomplete")
        case_id = case.get("case_id")
        case_sources = case.get("source_ids")
        field = case.get("product_field")
        actual = (
            source_model.get(field)
            if field in ("phenomenon", "model")
            else _json_text(scale)
            if field == "scale" and scale is not None
            else None
        )
        excerpt = case.get("source_excerpt")
        passed = (
            isinstance(actual, str)
            and case.get("expected") == excerpt
            and case.get("observed") == actual
            and case.get("expected") == case.get("observed")
        )
        if (
            not isinstance(case_id, str)
            or not case_id
            or case_id in accuracy_ids
            or not isinstance(case_sources, list)
            or not case_sources
            or not set(case_sources) <= required_ids_set
            or not isinstance(excerpt, str)
            or not excerpt
            or case.get("source_excerpt_sha256")
            != hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
            or not any(
                excerpt.encode("utf-8") in source_bytes_by_id[source_id]
                for source_id in case_sources
            )
            or case.get("passed") is not passed
        ):
            raise ContractError("science accuracy case is not product/source-bound")
        accuracy_ids.add(case_id)
        accuracy_failures += not passed

    checks = source_payload.get("simplification_checks")
    if not isinstance(checks, list) or not checks:
        raise ContractError("science receipt lacks simplification checks")
    expected_hashes = {_json_sha256(item) for item in simplifications if isinstance(item, Mapping)}
    simplification_by_hash = {
        _json_sha256(item): item
        for item in simplifications
        if isinstance(item, Mapping)
    }
    observed_hashes = set()
    dishonest = 0
    for check in checks:
        if not isinstance(check, Mapping) or set(check) != {
            "simplification_sha256",
            "source_ids",
            "disclosed_limit_present",
            "source_supported",
            "source_excerpt",
            "source_excerpt_sha256",
            "passed",
        }:
            raise ContractError("science simplification check is incomplete")
        digest = check.get("simplification_sha256")
        sources_for_check = check.get("source_ids")
        excerpt = check.get("source_excerpt")
        exact_simplification = simplification_by_hash.get(digest)
        passed = (
            check.get("disclosed_limit_present") is True
            and check.get("source_supported") is True
        )
        if (
            digest not in expected_hashes
            or digest in observed_hashes
            or not isinstance(sources_for_check, list)
            or not sources_for_check
            or not set(sources_for_check) <= required_ids_set
            or not isinstance(excerpt, str)
            or not excerpt
            or not isinstance(exact_simplification, Mapping)
            or str(exact_simplification.get("simplification")) not in excerpt
            or str(exact_simplification.get("disclosed_limit")) not in excerpt
            or check.get("source_excerpt_sha256")
            != hashlib.sha256(excerpt.encode("utf-8")).hexdigest()
            or not any(
                excerpt.encode("utf-8") in source_bytes_by_id[source_id]
                for source_id in sources_for_check
            )
            or check.get("passed") is not passed
        ):
            raise ContractError("science simplification check is not source-bound")
        observed_hashes.add(digest)
        dishonest += not passed
    if observed_hashes != expected_hashes:
        raise ContractError("science receipt omits an exact simplification")

    traces = trace_payload.get("traces")
    if not isinstance(traces, list) or not traces:
        raise ContractError("science receipt lacks comprehension traces")
    seeds = set()
    comprehension_failures = 0
    for trace in traces:
        if not isinstance(trace, Mapping) or set(trace) != {
            "seed",
            "expected_concepts",
            "observed_concepts",
            "passed",
        }:
            raise ContractError("science comprehension trace is incomplete")
        seed = trace.get("seed")
        expected = trace.get("expected_concepts")
        observed = trace.get("observed_concepts")
        passed = isinstance(expected, list) and isinstance(observed, list) and bool(expected) and set(
            expected
        ) <= set(observed)
        if (
            type(seed) is not int
            or seed < 0
            or seed in seeds
            or not isinstance(expected, list)
            or not all(isinstance(item, str) and item for item in expected)
            or len(expected) != len(set(expected))
            or not isinstance(observed, list)
            or not all(isinstance(item, str) and item for item in observed)
            or len(observed) != len(set(observed))
            or trace.get("passed") is not passed
        ):
            raise ContractError("science comprehension trace is not replayable")
        seeds.add(seed)
        comprehension_failures += not passed
    measurements = proof.measurements
    if (
        measurements.get("accuracy_cases") != len(accuracy)
        or measurements.get("accuracy_failures") != accuracy_failures
        or measurements.get("simplifications_checked") != len(checks)
        or measurements.get("dishonest_simplifications") != dishonest
        or measurements.get("comprehension_traces") != len(traces)
        or measurements.get("comprehension_failures") != comprehension_failures
    ):
        raise ContractError("science measurements do not match replayed source cases")


def _world_contract(document: Mapping[str, Any]) -> Tuple[list, list]:
    plan = document.get("digital_test_plan")
    lane_contract = plan.get("invent_lane_contract") if isinstance(plan, Mapping) else None
    selected = lane_contract if isinstance(lane_contract, Mapping) else document
    references = selected.get("consented_references")
    mappings = selected.get("feature_to_form_map")
    if not isinstance(references, list) or not isinstance(mappings, list):
        raise ContractError("world product source lacks consent and personalization maps")
    return references, mappings


def _validate_world_receipt_semantics(
    proof: CapabilityReleaseProof,
    receipts: Mapping[str, Mapping[str, Any]],
    product_root: Path,
) -> None:
    consent_payload = _receipt_payload(receipts, "consent-record")
    reference_payload = _receipt_payload(receipts, "reference-material")
    likeness_payload = _receipt_payload(receipts, "likeness-traces")
    attestation = _provider_identity(consent_payload.get("attestation"), "world")
    if (
        _provider_identity(reference_payload.get("attestation"), "world reference")
        != attestation
        or _provider_identity(likeness_payload.get("attestation"), "world likeness")
        != attestation
    ):
        raise ContractError("world receipts name different trusted providers")
    if (
        consent_payload.get("raw_consent_bytes_sealed") is not False
        or reference_payload.get("raw_private_bytes_sealed") is not False
        or "not public-replayable"
        not in str(consent_payload.get("attestation_scope", ""))
        or "not public-replayable"
        not in str(reference_payload.get("attestation_scope", ""))
    ):
        raise ContractError("world receipts misstate their private attestation boundary")
    product_document = _product_json_for_role(
        proof, product_root, "personalization-map", "world personalization map"
    )
    expected_references, expected_mappings = _world_contract(product_document)
    expected_by_id = {
        item.get("reference_id"): item
        for item in expected_references
        if isinstance(item, Mapping) and isinstance(item.get("reference_id"), str)
    }
    if len(expected_by_id) != len(expected_references) or not expected_by_id:
        raise ContractError("world product references are incomplete or duplicated")

    records = consent_payload.get("records")
    if not isinstance(records, list) or not records:
        raise ContractError("world receipt lacks consent attestations")
    consent_by_id = {}
    for record in records:
        if not isinstance(record, Mapping) or set(record) != {
            "reference_id",
            "subject",
            "rights_basis",
            "allowed_features",
            "excluded_features",
            "verification_method",
            "verified_at",
            "consent_sha256",
            "consent_bytes",
        }:
            raise ContractError("world consent attestation is incomplete")
        reference_id = record.get("reference_id")
        expected = expected_by_id.get(reference_id)
        if (
            expected is None
            or reference_id in consent_by_id
            or record.get("subject") != expected.get("subject")
            or record.get("rights_basis") != expected.get("consent_or_rights_basis")
            or record.get("allowed_features") != expected.get("allowed_features")
            or record.get("excluded_features") != expected.get("excluded_features")
            or not _nonempty_text(
                record.get("verification_method"), "world consent verification method"
            )
            or type(record.get("consent_bytes")) is not int
            or record["consent_bytes"] < 1
        ):
            raise ContractError("world consent attestation differs from exact Invent scope")
        require_sha256(record.get("consent_sha256"), "world consent sha256")
        require_utc_timestamp(record.get("verified_at"), "world consent verified_at")
        consent_by_id[reference_id] = record
    if set(consent_by_id) != set(expected_by_id):
        raise ContractError("world consent attestation omits a reference")

    references = reference_payload.get("references")
    if not isinstance(references, list) or not references:
        raise ContractError("world receipt lacks private reference attestations")
    material_by_id = {}
    for reference in references:
        if not isinstance(reference, Mapping) or set(reference) != {
            "reference_id",
            "media_type",
            "content_sha256",
            "content_bytes",
            "private_bytes_sealed",
        }:
            raise ContractError("world reference attestation is incomplete")
        reference_id = reference.get("reference_id")
        if (
            reference_id not in expected_by_id
            or reference_id in material_by_id
            or not isinstance(reference.get("media_type"), str)
            or "/" not in reference["media_type"]
            or type(reference.get("content_bytes")) is not int
            or reference["content_bytes"] < 1
            or reference.get("private_bytes_sealed") is not False
        ):
            raise ContractError("world reference attestation is invalid")
        require_sha256(reference.get("content_sha256"), "world reference sha256")
        material_by_id[reference_id] = reference
    if set(material_by_id) != set(expected_by_id):
        raise ContractError("world reference attestation omits an authorized reference")

    cases = likeness_payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ContractError("world receipt lacks likeness cases")
    expected_cases = {
        (
            item.get("reference_id"),
            item.get("reference_feature"),
            item.get("recognition_test"),
        )
        for item in expected_mappings
        if isinstance(item, Mapping)
    }
    if len(expected_cases) != len(expected_mappings) or not expected_cases:
        raise ContractError("world personalization cases are incomplete or duplicated")
    observed_cases = set()
    recognition_failures = 0
    consent_violations = 0
    for case in cases:
        if not isinstance(case, Mapping) or set(case) != {
            "reference_id",
            "reference_feature",
            "recognition_test",
            "reference_sha256",
            "recognized",
            "consent_safe",
            "method_class",
            "passed",
        }:
            raise ContractError("world likeness case is incomplete")
        identity = (
            case.get("reference_id"),
            case.get("reference_feature"),
            case.get("recognition_test"),
        )
        material = material_by_id.get(case.get("reference_id"))
        consent = consent_by_id.get(case.get("reference_id"))
        passed = case.get("recognized") is True and case.get("consent_safe") is True
        if (
            identity not in expected_cases
            or identity in observed_cases
            or material is None
            or consent is None
            or case.get("reference_sha256") != material.get("content_sha256")
            or case.get("reference_feature") not in consent.get("allowed_features", ())
            or case.get("reference_feature") in consent.get("excluded_features", ())
            or not _nonempty_text(case.get("method_class"), "world likeness method")
            or str(case["method_class"]).casefold() in _DISALLOWED_PROVIDER_METHODS
            or type(case.get("recognized")) is not bool
            or type(case.get("consent_safe")) is not bool
            or case.get("passed") is not passed
        ):
            raise ContractError("world likeness case is not consent/reference-bound")
        observed_cases.add(identity)
        recognition_failures += not case["recognized"]
        consent_violations += not case["consent_safe"]
    if observed_cases != expected_cases:
        raise ContractError("world likeness receipt omits a personalization mapping")
    measurements = proof.measurements
    if (
        measurements.get("consent_verified") is not True
        or measurements.get("personalization_features") != len(expected_cases)
        or measurements.get("likeness_cases") != len(cases)
        or measurements.get("recognition_failures") != recognition_failures
        or measurements.get("consent_violations") != consent_violations
    ):
        raise ContractError("world measurements do not match replayed attestation cases")


def _validate_lane_receipt_semantics(
    proof: CapabilityReleaseProof,
    receipts: Mapping[str, Mapping[str, Any]],
    product_root: Path,
) -> None:
    if proof.capability == "classic-rules-test":
        _validate_classic_receipt_semantics(proof, receipts, product_root)
    elif proof.capability == "science-test":
        _validate_science_receipt_semantics(proof, receipts, product_root)
    elif proof.capability == "world-test":
        _validate_world_receipt_semantics(proof, receipts, product_root)


def _validate_game(
    proof: CapabilityReleaseProof,
    *,
    product_root: Path,
    evidence_root: Path,
) -> None:
    simulator = _one_role(proof, "simulator-source", scope="product")
    rules = _one_role(proof, "game-rules", scope="product")
    traces = _one_role(proof, "game-traces", scope="playtest")
    analysis = _one_role(proof, "game-analysis", scope="playtest")
    if Path(simulator.path).suffix.casefold() != ".py":
        raise ContractError("game simulator source must be sealed Python")
    _load_json_file(product_root, rules, "game rules")
    trace_document = _load_json_file(evidence_root, traces, "game traces")
    analysis_document = _load_json_file(evidence_root, analysis, "game analysis")
    measurements = proof.measurements
    requested = _int_measurement(measurements, "requested_games", minimum=1_000)
    completed = _int_measurement(measurements, "completed_games", minimum=1_000)
    if completed != requested:
        raise ContractError("game proof must complete every requested game")
    for name in ("balance_cases", "exploit_cases", "choice_cases", "flow_cases"):
        _int_measurement(measurements, name, minimum=1)
    for name in (
        "balance_failures",
        "exploits_found",
        "degenerate_choices",
        "flow_failures",
    ):
        _int_measurement(measurements, name, minimum=0, maximum=0)
    if (
        not isinstance(trace_document, Mapping)
        or trace_document.get("artifact_sha256") != proof.artifact_sha256
        or not isinstance(trace_document.get("games"), list)
        or len(trace_document["games"]) != requested
    ):
        raise ContractError("game trace document is not bound to every requested game")
    seen_seeds = set()
    observed_styles = set()
    for game in trace_document["games"]:
        if (
            not isinstance(game, Mapping)
            or type(game.get("seed")) is not int
            or game["seed"] in seen_seeds
            or game.get("completed") is not True
            or type(game.get("turns")) is not int
            or game["turns"] < 1
            or not isinstance(game.get("player_styles"), list)
            or not game["player_styles"]
            or not isinstance(game.get("issues"), list)
            or game["issues"]
        ):
            raise ContractError("game proof contains an incomplete or invalid trace")
        seen_seeds.add(game["seed"])
        observed_styles.update(game["player_styles"])
    if not _GAME_STYLES <= observed_styles:
        raise ContractError("game proof lacks all four player styles")
    if (
        not isinstance(analysis_document, Mapping)
        or analysis_document.get("artifact_sha256") != proof.artifact_sha256
        or analysis_document.get("measurements") != dict(measurements)
    ):
        raise ContractError("game analysis is not bound to the measured release proof")


_PROOF_VALIDATORS = {
    "mechanical-test": _validate_mechanical,
    "motion-test": _validate_motion,
    "classic-rules-test": _validate_classic,
    "science-test": _validate_science,
    "world-test": _validate_world,
}


def _validate_proof_sources(
    proof: CapabilityReleaseProof,
    *,
    product_inventory: Mapping[str, str],
    evidence_inventory: Mapping[str, str],
    result_ref: str,
) -> None:
    for source in proof.sources:
        inventory = product_inventory if source.scope == "product" else evidence_inventory
        if inventory.get(source.path) != source.sha256:
            raise ContractError("release proof cites missing or hash-mismatched bytes")
        if source.scope == "playtest" and source.path == result_ref:
            raise ContractError("release proof cannot cite its own result as independent proof")


def _validate_inline_print(
    evidence: Mapping[str, Any],
    artifact_sha256: str,
    product_inventory: Mapping[str, str],
) -> None:
    check = evidence.get("deterministic_check")
    if not isinstance(check, Mapping):
        raise ContractError("print-test lacks an exact slicer release proof")
    if (
        check.get("artifact_sha256") != artifact_sha256
        or check.get("capability") != "print-test"
        or check.get("passed") is not True
        or check.get("method_class") != "deterministic-exact-slicer-profile"
    ):
        raise ContractError("print-test deterministic receipt is not a passed exact slicer run")
    require_exact_version(check.get("checker_version"), "print checker version")
    require_sha256(check.get("config_sha256"), "print checker config sha256")
    metrics = check.get("metrics")
    if not isinstance(metrics, Mapping):
        raise ContractError("print-test slicer measurements are missing")
    receipt = metrics.get("slicer_receipt")
    if not isinstance(receipt, Mapping):
        raise ContractError("print-test slicer receipt is missing")
    receipt_sha256 = hashlib.sha256(
        json.dumps(
            dict(receipt),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()
    if metrics.get("slicer_receipt_sha256") != receipt_sha256:
        raise ContractError("print-test slicer receipt hash is invalid")
    normalized = {
        "slicer": receipt.get("slicer"),
        "slicer_version": receipt.get("slicer_version"),
        "profiles": receipt.get("profiles"),
        "parts": receipt.get("parts"),
        "slicer_errors": metrics.get("slicer_errors"),
    }
    _validate_slicer_measurements(normalized, product_inventory)


def _validate_inline_motion(
    evidence: Mapping[str, Any],
    artifact_sha256: str,
    product_inventory: Mapping[str, str],
) -> None:
    check = evidence.get("deterministic_check")
    if not isinstance(check, Mapping):
        raise ContractError("motion-test lacks a kinematic release proof")
    metrics = check.get("metrics")
    source_refs = check.get("source_refs")
    if (
        check.get("artifact_sha256") != artifact_sha256
        or check.get("capability") != "motion-test"
        or check.get("passed") is not True
        or check.get("method_class") != "deterministic-kinematic-simulation"
        or not isinstance(metrics, Mapping)
        or not isinstance(source_refs, list)
    ):
        raise ContractError("motion-test deterministic receipt is incomplete")
    require_exact_version(check.get("checker_version"), "motion checker version")
    require_sha256(check.get("config_sha256"), "motion checker config sha256")
    receipt_ref = metrics.get("motion_receipt_ref")
    if (
        not isinstance(receipt_ref, str)
        or receipt_ref not in source_refs
        or product_inventory.get(receipt_ref) != metrics.get("motion_receipt_sha256")
    ):
        raise ContractError("motion-test receipt is not bound to the sealed product")
    _int_measurement(metrics, "states_tested", minimum=2)
    _true_measurement(metrics, "continuous_sweep")
    for name in (
        "tolerance_cases_tested",
        "load_cases_tested",
        "orientations_tested",
        "wear_cycles",
        "misuse_cases_tested",
    ):
        _int_measurement(metrics, name, minimum=1)
    for name in ("collisions", "stalls", "failures"):
        _int_measurement(metrics, name, minimum=0, maximum=0)


def _validate_result_document(
    result: PlaytestResult, evidence_root: Path
) -> None:
    path = evidence_root / result.evidence_ref
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(evidence_root.resolve(strict=True))
        if path.is_symlink() or not resolved.is_file():
            raise OSError("not a regular evidence file")
        payload = resolved.read_bytes()
    except (OSError, ValueError) as exc:
        raise ContractError("Playtest result evidence file is missing or unsafe") from exc
    if not payload or len(payload) > MAX_EVIDENCE_JSON_BYTES:
        raise ContractError("Playtest result evidence file is empty or oversized")
    if hashlib.sha256(payload).hexdigest() != result.evidence_sha256:
        raise ContractError("Playtest result evidence bytes changed")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Playtest result evidence must be UTF-8 JSON") from exc
    expected = _plain_json(dict(result.evidence), "Playtest result evidence")
    if document != expected:
        raise ContractError("PlaytestResult evidence differs from its sealed evidence file")


def _validate_capability_result(
    capability: str,
    result: PlaytestResult,
    *,
    made: Made,
    product_inventory: Mapping[str, str],
    evidence_inventory: Mapping[str, str],
    evidence_root: Path,
) -> None:
    evidence = result.evidence
    if evidence.get("evidence_class") != "ai-simulation":
        raise ContractError("Playtest release evidence must be AI simulation")
    if evidence.get("artifact_sha256") != made.artifact_sha256:
        raise ContractError("Playtest evidence does not name the exact Make bytes")
    roles = evidence.get("agent_roles")
    if (
        not isinstance(roles, list)
        or len(roles) < 2
        or not all(isinstance(role, str) and role.strip() for role in roles)
        or len(roles) != len(set(roles))
    ):
        raise ContractError("Playtest release evidence needs distinct AI-player roles")
    _validate_result_document(result, evidence_root)
    if capability not in _PROOF_CAPABILITIES:
        return

    raw_proof = evidence.get("release_proof")
    if raw_proof is None and capability == "print-test":
        _validate_inline_print(evidence, made.artifact_sha256, product_inventory)
        return
    if raw_proof is None and capability == "motion-test":
        _validate_inline_motion(evidence, made.artifact_sha256, product_inventory)
        return
    proof = CapabilityReleaseProof.from_dict(raw_proof)
    if proof.capability != capability or proof.artifact_sha256 != made.artifact_sha256:
        raise ContractError("release proof belongs to another capability or artifact")
    _validate_proof_sources(
        proof,
        product_inventory=product_inventory,
        evidence_inventory=evidence_inventory,
        result_ref=result.evidence_ref,
    )
    receipt_documents = _validate_release_receipts(
        proof,
        product_inventory=product_inventory,
        evidence_root=evidence_root,
    )
    _validate_lane_receipt_semantics(
        proof,
        receipt_documents,
        made.artifact_root,
    )
    if capability == "print-test":
        _validate_print(
            proof,
            product_inventory,
            evidence_root,
        )
    elif capability == "game-simulation":
        _validate_game(
            proof,
            product_root=made.artifact_root,
            evidence_root=evidence_root,
        )
    else:
        _PROOF_VALIDATORS[capability](proof)


def _need(capability: str) -> Need:
    purpose = {
        "mechanical-test": "computed B-rep, interference, fit, assembly, motion, load, and failure evidence",
        "print-test": "an exact slicer receipt for every sealed printable part and pinned profiles",
        "motion-test": "kinematic evidence across tolerances, orientations, loads, wear, stalls, and misuse",
        "classic-rules-test": "reference-bound rule conformance and seeded classic-game traces",
        "science-test": "source-bound accuracy, simplification, and comprehension evidence",
        "world-test": "consent-, reference-, and personalization-bound likeness evidence",
        "game-simulation": "1,000 complete seeded traces plus balance, exploit, choice, and flow analysis",
        "agent-playtest": "artifact-bound evidence from at least two distinct AI-player roles",
    }.get(capability, "artifact-bound evidence matching the Workshop capability contract")
    return Need(
        "playtest",
        capability,
        "The passed %s result does not contain %s." % (capability, purpose),
        "Return exact-byte-bound Playtest evidence and a valid release_proof for %s; a result name or model score alone cannot authorize Instructions."
        % capability,
    )


def playtest_release_needs(
    blueprint: ToyBlueprint,
    made: Made,
    playtested: Playtested,
    evidence_root: Path,
) -> Tuple[Need, ...]:
    """Return every missing common release proof before Instructions.

    This function is deliberately worker-agnostic.  It validates the sealed
    output, not whether it came from the shared or a custom Playtest callable.
    """

    if not isinstance(blueprint, ToyBlueprint):
        raise ContractError("Playtest release policy requires a ToyBlueprint")
    if not isinstance(made, Made) or not isinstance(playtested, Playtested):
        raise ContractError("Playtest release policy requires Made and Playtested")
    made.assert_current()
    playtested.assert_artifact(made.artifact_sha256)
    selected_root = Path(evidence_root)
    if not selected_root.is_absolute() or selected_root.is_symlink():
        raise ContractError("Playtest evidence root must be an absolute regular directory")
    try:
        selected_root = selected_root.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Playtest evidence root is missing") from exc
    if not selected_root.is_dir():
        raise ContractError("Playtest evidence root must be a directory")
    evidence_manifest = playtested.evidence.evidence_manifest
    current = build_artifact_manifest(
        selected_root, created_at=evidence_manifest.created_at
    )
    if current.to_dict() != evidence_manifest.to_dict():
        raise ContractError("Playtest evidence bytes changed before release policy")

    product_inventory = {
        entry.path: entry.sha256 for entry in made.artifact_manifest.entries
    }
    evidence_inventory = {
        entry.path: entry.sha256 for entry in evidence_manifest.entries
    }
    by_id = {result.playtest_id: result for result in playtested.evidence.results}
    needs = []
    for capability in blueprint.required_capabilities("playtest"):
        result = by_id.get(capability)
        if result is None or not result.passed:
            needs.append(_need(capability))
            continue
        try:
            _validate_capability_result(
                capability,
                result,
                made=made,
                product_inventory=product_inventory,
                evidence_inventory=evidence_inventory,
                evidence_root=selected_root,
            )
        except (ContractError, KeyError, TypeError, ValueError):
            needs.append(_need(capability))
    return tuple(needs)


__all__ = [
    "CapabilityReleaseProof",
    "ReleaseProofSource",
    "playtest_release_needs",
]
