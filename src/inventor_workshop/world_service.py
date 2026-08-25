"""Manager-owned bindings for private little-world reference services.

The contribution process may receive these frozen values, but it never receives
the service object, a service credential, consent bytes, or reference media.
``WorldInventInputs`` is prepared before Invent.  ``WorldPlaytestEvidence`` is
prepared after Make by an independently configured Manager-side provider.

The values authenticate *what an operator/customer supplied* and what an
external provider measured.  They do not establish legal consent or ownership.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Protocol, Sequence, Tuple

from .errors import ContractError
from .make import Wish
from .models import require_sha256, require_utc_timestamp
from .world_reference_vault import (
    CONSENT_CLAIM_BOUNDARY,
    LOCAL_STORAGE_SECURITY_BOUNDARY,
    SUPPORTED_WORLD_MEDIA_TYPES,
    WorldReferenceDescriptor,
    WorldReferenceScope,
    WorldReferenceService,
)


EXTERNAL_WORLD_SERVICE_BOUNDARY = "external-isolated-service"
WORLD_SERVICE_BOUNDARIES = frozenset(
    (EXTERNAL_WORLD_SERVICE_BOUNDARY, LOCAL_STORAGE_SECURITY_BOUNDARY)
)

_SAFE_ID = re.compile(r"[a-z][a-z0-9-]{1,62}\Z")
_SAFE_ACTOR = re.compile(r"[a-z][a-z0-9._-]{1,127}\Z")
_DISALLOWED_MEASUREMENT_METHODS = frozenset(
    ("ai opinion", "language-model opinion", "model opinion", "self attested")
)


def _canonical_bytes(value: Any, label: str) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("%s must be finite JSON" % label) from exc


def _copy_json(value: Any, label: str) -> Any:
    try:
        return json.loads(_canonical_bytes(value, label).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:  # canonical JSON
        raise ContractError("%s must be JSON" % label) from exc


def _json_sha256(value: Any, label: str) -> str:
    return hashlib.sha256(_canonical_bytes(value, label)).hexdigest()


def _wish_sha256(wish: Wish) -> str:
    if not isinstance(wish, Wish):
        raise ContractError("world service access requires a Wish")
    wish.assert_valid()
    return _json_sha256(wish.to_dict(), "world service Wish")


def _text(value: Any, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded, trimmed, control-free text" % label)
    return value


def _safe_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ContractError("%s must be a canonical lowercase id" % label)
    return value


def _safe_actor(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ACTOR.fullmatch(value) is None:
        raise ContractError("%s must be a canonical provider id" % label)
    return value


def _digest_envelope(value: Any, key: str, label: str) -> Dict[str, str]:
    """Copy one raw-free provider proof digest.

    The credential-bearing Manager-side adapter verifies the real signature or
    authorization before constructing this public envelope.  Keeping only its
    digest prevents opaque provider JSON from smuggling reference media,
    consent text, credentials, or unbounded signatures into the Inventor
    handoff and sealed Playtest evidence.
    """

    if not isinstance(value, Mapping) or set(value) != {key}:
        raise ContractError("%s must contain only %s" % (label, key))
    digest = value.get(key)
    require_sha256(digest, "%s sha256" % label)
    return {key: digest}


@dataclass(frozen=True)
class WorldProviderIdentity:
    """Public identity of a Manager-side descriptor or evidence service."""

    provider_id: str
    version: str
    config_sha256: str
    security_boundary: str = EXTERNAL_WORLD_SERVICE_BOUNDARY

    def __post_init__(self) -> None:
        _safe_actor(self.provider_id, "world provider id")
        _text(self.version, "world provider version", 200)
        require_sha256(self.config_sha256, "world provider config sha256")
        if self.security_boundary not in WORLD_SERVICE_BOUNDARIES:
            raise ContractError("world provider security boundary is unsupported")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "version": self.version,
            "config_sha256": self.config_sha256,
            "security_boundary": self.security_boundary,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "WorldProviderIdentity":
        if not isinstance(value, Mapping) or set(value) != {
            "provider_id",
            "version",
            "config_sha256",
            "security_boundary",
        }:
            raise ContractError("world provider identity is malformed")
        return cls(**dict(value))


@dataclass(frozen=True)
class WorldInventReference:
    """Compact raw-free reference admission passed to shared Invent."""

    scope: WorldReferenceScope
    product_id: str
    wish_sha256: str
    record_sha256: str
    content_sha256: str
    content_bytes: int
    consent_sha256: str
    consent_bytes: int
    media_type: str
    admission_sha256: str
    attestation_key_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.scope, WorldReferenceScope):
            raise ContractError("world Invent reference requires a typed scope")
        _text(self.product_id, "world Invent product id", 256)
        for digest, label in (
            (self.wish_sha256, "world Invent Wish sha256"),
            (self.record_sha256, "world Invent record sha256"),
            (self.content_sha256, "world Invent content sha256"),
            (self.consent_sha256, "world Invent declaration sha256"),
            (self.admission_sha256, "world Invent admission sha256"),
            (self.attestation_key_id, "world Invent attestation key id"),
        ):
            require_sha256(digest, label)
        if self.record_sha256 != self.admission_sha256:
            raise ContractError("world Invent admission differs from its record digest")
        if self.media_type not in SUPPORTED_WORLD_MEDIA_TYPES:
            raise ContractError("world Invent reference media type is unsupported")
        if type(self.content_bytes) is not int or self.content_bytes < 1:
            raise ContractError("world Invent reference byte count is invalid")
        if type(self.consent_bytes) is not int or self.consent_bytes < 1:
            raise ContractError("world Invent declaration byte count is invalid")

    @classmethod
    def from_descriptor(
        cls, descriptor: WorldReferenceDescriptor
    ) -> "WorldInventReference":
        if not isinstance(descriptor, WorldReferenceDescriptor):
            raise ContractError("world descriptor service returned an untyped record")
        receipt = descriptor.receipt
        admission_sha256 = _json_sha256(
            descriptor.admission, "world descriptor admission"
        )
        return cls(
            scope=descriptor.scope,
            product_id=receipt.product_id,
            wish_sha256=receipt.wish_sha256,
            record_sha256=receipt.record_sha256,
            content_sha256=receipt.content_sha256,
            content_bytes=receipt.content_bytes,
            consent_sha256=receipt.consent_sha256,
            consent_bytes=receipt.consent_bytes,
            media_type=receipt.media_type,
            admission_sha256=admission_sha256,
            attestation_key_id=receipt.key_id,
        )

    def invent_contract(self) -> Dict[str, Any]:
        return {
            "reference_id": self.scope.reference_id,
            "subject": self.scope.subject,
            "consent_or_rights_basis": self.scope.rights_basis,
            "allowed_features": list(self.scope.allowed_features),
            "excluded_features": list(self.scope.excluded_features),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scope": self.scope.to_dict(),
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "record_sha256": self.record_sha256,
            "content_sha256": self.content_sha256,
            "content_bytes": self.content_bytes,
            "declaration_sha256": self.consent_sha256,
            "declaration_bytes": self.consent_bytes,
            "media_type": self.media_type,
            "admission_sha256": self.admission_sha256,
            "attestation_key_id": self.attestation_key_id,
            "raw_private_bytes_included": False,
            "claim_boundary": CONSENT_CLAIM_BOUNDARY,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "WorldInventReference":
        expected = {
            "scope",
            "product_id",
            "wish_sha256",
            "record_sha256",
            "content_sha256",
            "content_bytes",
            "declaration_sha256",
            "declaration_bytes",
            "media_type",
            "admission_sha256",
            "attestation_key_id",
            "raw_private_bytes_included",
            "claim_boundary",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("world Invent reference is malformed")
        if (
            value.get("raw_private_bytes_included") is not False
            or value.get("claim_boundary") != CONSENT_CLAIM_BOUNDARY
            or not isinstance(value.get("scope"), Mapping)
        ):
            raise ContractError("world Invent reference overstates its trust boundary")
        return cls(
            scope=WorldReferenceScope(**dict(value["scope"])),
            product_id=value["product_id"],
            wish_sha256=value["wish_sha256"],
            record_sha256=value["record_sha256"],
            content_sha256=value["content_sha256"],
            content_bytes=value["content_bytes"],
            consent_sha256=value["declaration_sha256"],
            consent_bytes=value["declaration_bytes"],
            media_type=value["media_type"],
            admission_sha256=value["admission_sha256"],
            attestation_key_id=value["attestation_key_id"],
        )


@dataclass(frozen=True)
class WorldInventInputs:
    """Exact raw-free service output bound to one saved little-worlds Wish."""

    product_id: str
    wish_sha256: str
    service: WorldProviderIdentity
    references: Sequence[WorldInventReference]
    schema_version: int = 1
    binding_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ContractError("world Invent input schema version is unsupported")
        _text(self.product_id, "world Invent product id", 256)
        require_sha256(self.wish_sha256, "world Invent Wish sha256")
        if not isinstance(self.service, WorldProviderIdentity):
            raise ContractError("world Invent inputs require a service identity")
        references = tuple(self.references)
        if not references or not all(
            isinstance(item, WorldInventReference) for item in references
        ):
            raise ContractError("world Invent inputs require typed references")
        ordered = tuple(sorted(references, key=lambda item: item.scope.reference_id))
        ids = tuple(item.scope.reference_id for item in ordered)
        if len(ids) != len(set(ids)):
            raise ContractError("world Invent reference ids must be unique")
        if any(
            item.product_id != self.product_id
            or item.wish_sha256 != self.wish_sha256
            for item in ordered
        ):
            raise ContractError("world Invent references belong to another Wish")
        reviewers = {item.scope.reviewer_id for item in ordered}
        if len(reviewers) != 1:
            raise ContractError(
                "one world Invent input bundle requires one stable claimed reviewer id"
            )
        object.__setattr__(self, "references", ordered)
        object.__setattr__(
            self,
            "binding_sha256",
            _json_sha256(self._identity_dict(), "world Invent input binding"),
        )

    @property
    def reviewer_id(self) -> str:
        return self.references[0].scope.reviewer_id

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": "world-invent-inputs",
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "service": self.service.to_dict(),
            "references": [item.to_dict() for item in self.references],
        }

    def to_dict(self) -> Dict[str, Any]:
        value = self._identity_dict()
        value["binding_sha256"] = self.binding_sha256
        return value

    @classmethod
    def from_dict(cls, value: Any) -> "WorldInventInputs":
        expected = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "service",
            "references",
            "binding_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("world Invent input bundle is malformed")
        if value.get("kind") != "world-invent-inputs":
            raise ContractError("world Invent input bundle kind is invalid")
        raw_references = value.get("references")
        if not isinstance(raw_references, list):
            raise ContractError("world Invent input references are malformed")
        bundle = cls(
            product_id=value["product_id"],
            wish_sha256=value["wish_sha256"],
            service=WorldProviderIdentity.from_dict(value["service"]),
            references=tuple(
                WorldInventReference.from_dict(item) for item in raw_references
            ),
            schema_version=value["schema_version"],
        )
        if value.get("binding_sha256") != bundle.binding_sha256:
            raise ContractError("world Invent input binding changed")
        return bundle

    def assert_wish(self, wish: Wish) -> None:
        if (
            self.product_id != wish.product_id
            or self.wish_sha256 != _wish_sha256(wish)
        ):
            raise ContractError("world Invent inputs belong to another exact Wish")

    def prompt_value(self) -> Dict[str, Any]:
        """Return only the raw-free fields shared Invent needs."""

        return {
            "binding_sha256": self.binding_sha256,
            "claim_boundary": CONSENT_CLAIM_BOUNDARY,
            "references": [
                {
                    **item.invent_contract(),
                    "content_sha256": item.content_sha256,
                    "declaration_sha256": item.consent_sha256,
                    "admission_sha256": item.admission_sha256,
                }
                for item in self.references
            ],
            "raw_private_bytes_included": False,
        }

    def expected_consent_contracts(self) -> list[Dict[str, Any]]:
        return [item.invent_contract() for item in self.references]

    def assert_lane_contract(self, contract: Any) -> None:
        if not isinstance(contract, Mapping) or set(contract) != {
            "schema_version",
            "lane",
            "consented_references",
            "feature_to_form_map",
        }:
            raise ContractError("little-worlds Invent contract is malformed")
        if contract.get("schema_version") != 1 or contract.get("lane") != "little-worlds":
            raise ContractError("little-worlds Invent contract has a wrong identity")
        if contract.get("consented_references") != self.expected_consent_contracts():
            raise ContractError(
                "Invent consent scope differs from the exact Manager-admitted descriptors"
            )
        mappings = contract.get("feature_to_form_map")
        if not isinstance(mappings, list) or not mappings:
            raise ContractError("little-worlds Invent mappings are missing")
        by_id = {
            item.scope.reference_id: item for item in self.references
        }
        seen = set()
        covered = set()
        for mapping in mappings:
            if not isinstance(mapping, Mapping) or set(mapping) != {
                "reference_id",
                "reference_feature",
                "physical_form",
                "recognition_test",
            }:
                raise ContractError("little-worlds Invent mapping is malformed")
            reference_id = mapping.get("reference_id")
            feature = mapping.get("reference_feature")
            key = (
                reference_id,
                feature,
                mapping.get("recognition_test"),
            )
            reference = by_id.get(reference_id)
            if (
                reference is None
                or feature not in reference.scope.allowed_features
                or feature in reference.scope.excluded_features
                or key in seen
            ):
                raise ContractError(
                    "little-worlds mapping is duplicated or outside admitted scope"
                )
            _text(mapping.get("physical_form"), "world physical form", 2_000)
            _text(mapping.get("recognition_test"), "world recognition test", 2_000)
            seen.add(key)
            covered.add(reference_id)
        if covered != set(by_id):
            raise ContractError("every admitted world reference needs a mapping")


def prepare_world_invent_inputs(
    wish: Wish,
    service: WorldReferenceService,
    identity: WorldProviderIdentity,
) -> WorldInventInputs:
    """Fetch and verify compact descriptors entirely in the Manager process."""

    if not isinstance(identity, WorldProviderIdentity):
        raise ContractError("world descriptor fetch requires a service identity")
    descriptors_method = getattr(service, "descriptors", None)
    verify_method = getattr(service, "verify_admission", None)
    if not callable(descriptors_method) or not callable(verify_method):
        raise ContractError("world descriptor service is incomplete")
    descriptors = descriptors_method(wish)
    if isinstance(descriptors, (str, bytes, Mapping)):
        raise ContractError("world descriptor service returned an invalid sequence")
    try:
        selected = tuple(descriptors)
    except TypeError as exc:
        raise ContractError("world descriptor service returned no sequence") from exc
    if not selected:
        raise ContractError("this little-worlds Wish has no admitted reference descriptors")
    references = []
    for descriptor in selected:
        if not isinstance(descriptor, WorldReferenceDescriptor):
            raise ContractError("world descriptor service returned an untyped record")
        verify_method(
            descriptor.admission,
            wish,
            expected_reference_id=descriptor.scope.reference_id,
        )
        references.append(WorldInventReference.from_descriptor(descriptor))
    bundle = WorldInventInputs(
        wish.product_id,
        _wish_sha256(wish),
        identity,
        tuple(references),
    )
    bundle.assert_wish(wish)
    return bundle


@dataclass(frozen=True)
class WorldEvidenceReference:
    """Raw-free independent-provider attestation for one admitted reference."""

    reference_id: str
    record_sha256: str
    content_sha256: str
    content_bytes: int
    declaration_sha256: str
    declaration_bytes: int
    media_type: str
    scope_authentication_method: str
    observed_at: str
    provider_authorization: Mapping[str, Any]

    def __post_init__(self) -> None:
        _safe_id(self.reference_id, "world evidence reference id")
        for digest, label in (
            (self.record_sha256, "world evidence record sha256"),
            (self.content_sha256, "world evidence content sha256"),
            (self.declaration_sha256, "world evidence declaration sha256"),
        ):
            require_sha256(digest, label)
        if type(self.content_bytes) is not int or self.content_bytes < 1:
            raise ContractError("world evidence reference byte count is invalid")
        if type(self.declaration_bytes) is not int or self.declaration_bytes < 1:
            raise ContractError("world evidence declaration byte count is invalid")
        if self.media_type not in SUPPORTED_WORLD_MEDIA_TYPES:
            raise ContractError("world evidence media type is unsupported")
        method = _text(
            self.scope_authentication_method,
            "world scope authentication method",
            300,
        )
        if method.casefold() in _DISALLOWED_MEASUREMENT_METHODS:
            raise ContractError("model opinion is not world scope authentication")
        require_utc_timestamp(self.observed_at, "world evidence observed_at")
        authorization = _digest_envelope(
            self.provider_authorization,
            "authorization_sha256",
            "world provider authorization",
        )
        object.__setattr__(self, "provider_authorization", authorization)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "record_sha256": self.record_sha256,
            "content_sha256": self.content_sha256,
            "content_bytes": self.content_bytes,
            "declaration_sha256": self.declaration_sha256,
            "declaration_bytes": self.declaration_bytes,
            "media_type": self.media_type,
            "scope_authentication_method": self.scope_authentication_method,
            "observed_at": self.observed_at,
            "provider_authorization": _copy_json(
                self.provider_authorization, "world provider authorization"
            ),
            "raw_private_bytes_included": False,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "WorldEvidenceReference":
        expected = {
            "reference_id",
            "record_sha256",
            "content_sha256",
            "content_bytes",
            "declaration_sha256",
            "declaration_bytes",
            "media_type",
            "scope_authentication_method",
            "observed_at",
            "provider_authorization",
            "raw_private_bytes_included",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("world evidence reference is malformed")
        if value.get("raw_private_bytes_included") is not False:
            raise ContractError("world evidence reference contains private bytes")
        return cls(
            reference_id=value["reference_id"],
            record_sha256=value["record_sha256"],
            content_sha256=value["content_sha256"],
            content_bytes=value["content_bytes"],
            declaration_sha256=value["declaration_sha256"],
            declaration_bytes=value["declaration_bytes"],
            media_type=value["media_type"],
            scope_authentication_method=value["scope_authentication_method"],
            observed_at=value["observed_at"],
            provider_authorization=value["provider_authorization"],
        )


@dataclass(frozen=True)
class WorldEvidenceCase:
    reference_id: str
    reference_feature: str
    recognition_test: str
    reference_sha256: str
    recognized: bool
    scope_safe: bool
    method_class: str

    def __post_init__(self) -> None:
        _safe_id(self.reference_id, "world evidence case reference id")
        _text(self.reference_feature, "world evidence feature", 1_000)
        _text(self.recognition_test, "world evidence recognition test", 2_000)
        require_sha256(self.reference_sha256, "world evidence reference sha256")
        if type(self.recognized) is not bool or type(self.scope_safe) is not bool:
            raise ContractError("world evidence verdicts must be booleans")
        method = _text(self.method_class, "world evidence method", 200)
        if method.casefold() in _DISALLOWED_MEASUREMENT_METHODS:
            raise ContractError("language-model opinion alone is not recognition proof")

    @property
    def passed(self) -> bool:
        return self.recognized and self.scope_safe

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "reference_feature": self.reference_feature,
            "recognition_test": self.recognition_test,
            "reference_sha256": self.reference_sha256,
            "recognized": self.recognized,
            "scope_safe": self.scope_safe,
            "method_class": self.method_class,
            "passed": self.passed,
        }

    @classmethod
    def from_dict(cls, value: Any) -> "WorldEvidenceCase":
        expected = {
            "reference_id",
            "reference_feature",
            "recognition_test",
            "reference_sha256",
            "recognized",
            "scope_safe",
            "method_class",
            "passed",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("world evidence case is malformed")
        case = cls(
            reference_id=value["reference_id"],
            reference_feature=value["reference_feature"],
            recognition_test=value["recognition_test"],
            reference_sha256=value["reference_sha256"],
            recognized=value["recognized"],
            scope_safe=value["scope_safe"],
            method_class=value["method_class"],
        )
        if value.get("passed") is not case.passed:
            raise ContractError("world evidence case pass value is inconsistent")
        return case


@dataclass(frozen=True)
class WorldPlaytestEvidence:
    """Verified raw-free provider output passed back to shared Playtest."""

    product_id: str
    wish_sha256: str
    artifact_sha256: str
    personalization_sha256: str
    invent_inputs_sha256: str
    provider: WorldProviderIdentity
    references: Sequence[WorldEvidenceReference]
    cases: Sequence[WorldEvidenceCase]
    provider_attestation: Mapping[str, Any]
    schema_version: int = 1
    evidence_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 1:
            raise ContractError("world Playtest evidence schema version is unsupported")
        _text(self.product_id, "world evidence product id", 256)
        for digest, label in (
            (self.wish_sha256, "world evidence Wish sha256"),
            (self.artifact_sha256, "world evidence artifact sha256"),
            (self.personalization_sha256, "world evidence personalization sha256"),
            (self.invent_inputs_sha256, "world evidence Invent inputs sha256"),
        ):
            require_sha256(digest, label)
        if not isinstance(self.provider, WorldProviderIdentity):
            raise ContractError("world evidence requires a provider identity")
        if self.provider.security_boundary != EXTERNAL_WORLD_SERVICE_BOUNDARY:
            raise ContractError(
                "world Playtest evidence requires an external isolated provider"
            )
        references = tuple(self.references)
        cases = tuple(self.cases)
        if not references or not all(
            isinstance(item, WorldEvidenceReference) for item in references
        ):
            raise ContractError("world evidence requires typed reference attestations")
        if not cases or not all(isinstance(item, WorldEvidenceCase) for item in cases):
            raise ContractError("world evidence requires typed recognition cases")
        references = tuple(sorted(references, key=lambda item: item.reference_id))
        if len({item.reference_id for item in references}) != len(references):
            raise ContractError("world evidence repeats a reference")
        keys = {
            (item.reference_id, item.reference_feature, item.recognition_test)
            for item in cases
        }
        if len(keys) != len(cases):
            raise ContractError("world evidence repeats a recognition case")
        attestation = _digest_envelope(
            self.provider_attestation,
            "attestation_sha256",
            "world provider attestation",
        )
        object.__setattr__(self, "references", references)
        object.__setattr__(self, "cases", cases)
        object.__setattr__(self, "provider_attestation", attestation)
        object.__setattr__(
            self,
            "evidence_sha256",
            _json_sha256(self._identity_dict(), "world Playtest evidence"),
        )

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": "world-playtest-evidence",
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "artifact_sha256": self.artifact_sha256,
            "personalization_sha256": self.personalization_sha256,
            "invent_inputs_sha256": self.invent_inputs_sha256,
            "provider": self.provider.to_dict(),
            "references": [item.to_dict() for item in self.references],
            "cases": [item.to_dict() for item in self.cases],
            "provider_attestation": _copy_json(
                self.provider_attestation, "world provider attestation"
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        value = self._identity_dict()
        value["evidence_sha256"] = self.evidence_sha256
        return value

    @classmethod
    def from_dict(cls, value: Any) -> "WorldPlaytestEvidence":
        expected = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "artifact_sha256",
            "personalization_sha256",
            "invent_inputs_sha256",
            "provider",
            "references",
            "cases",
            "provider_attestation",
            "evidence_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("world Playtest evidence is malformed")
        if value.get("kind") != "world-playtest-evidence":
            raise ContractError("world Playtest evidence kind is invalid")
        raw_references = value.get("references")
        raw_cases = value.get("cases")
        if not isinstance(raw_references, list) or not isinstance(raw_cases, list):
            raise ContractError("world Playtest evidence records are malformed")
        evidence = cls(
            product_id=value["product_id"],
            wish_sha256=value["wish_sha256"],
            artifact_sha256=value["artifact_sha256"],
            personalization_sha256=value["personalization_sha256"],
            invent_inputs_sha256=value["invent_inputs_sha256"],
            provider=WorldProviderIdentity.from_dict(value["provider"]),
            references=tuple(
                WorldEvidenceReference.from_dict(item) for item in raw_references
            ),
            cases=tuple(WorldEvidenceCase.from_dict(item) for item in raw_cases),
            provider_attestation=value["provider_attestation"],
            schema_version=value["schema_version"],
        )
        if value.get("evidence_sha256") != evidence.evidence_sha256:
            raise ContractError("world Playtest evidence binding changed")
        return evidence

    def assert_context(
        self,
        wish: Wish,
        artifact_sha256: str,
        personalization_map: Mapping[str, Any],
        invent_inputs: WorldInventInputs,
    ) -> None:
        invent_inputs.assert_wish(wish)
        require_sha256(artifact_sha256, "world Playtest artifact sha256")
        invent_inputs.assert_lane_contract(
            {
                "schema_version": 1,
                "lane": "little-worlds",
                **dict(personalization_map),
            }
        )
        if (
            self.product_id != wish.product_id
            or self.wish_sha256 != _wish_sha256(wish)
            or self.artifact_sha256 != artifact_sha256
            or self.personalization_sha256
            != _json_sha256(dict(personalization_map), "world personalization map")
            or self.invent_inputs_sha256 != invent_inputs.binding_sha256
        ):
            raise ContractError("world Playtest evidence belongs to another exact context")
        expected = {item.scope.reference_id: item for item in invent_inputs.references}
        observed = {item.reference_id: item for item in self.references}
        if set(observed) != set(expected):
            raise ContractError("world Playtest evidence omits an admitted reference")
        for reference_id, admitted in expected.items():
            attested = observed[reference_id]
            if (
                attested.record_sha256 != admitted.record_sha256
                or attested.content_sha256 != admitted.content_sha256
                or attested.content_bytes != admitted.content_bytes
                or attested.declaration_sha256 != admitted.consent_sha256
                or attested.declaration_bytes != admitted.consent_bytes
                or attested.media_type != admitted.media_type
            ):
                raise ContractError(
                    "world Playtest evidence differs from the admitted descriptor hashes"
                )
        raw_mappings = personalization_map.get("feature_to_form_map")
        assert isinstance(raw_mappings, list)  # assert_lane_contract established this
        expected_cases = {
            (
                item["reference_id"],
                item["reference_feature"],
                item["recognition_test"],
            )
            for item in raw_mappings
        }
        observed_cases = {
            (item.reference_id, item.reference_feature, item.recognition_test)
            for item in self.cases
        }
        if observed_cases != expected_cases:
            raise ContractError("world evidence does not cover every exact mapping")
        for case in self.cases:
            admitted = expected[case.reference_id]
            if (
                case.reference_sha256 != admitted.content_sha256
                or case.reference_feature not in admitted.scope.allowed_features
                or case.reference_feature in admitted.scope.excluded_features
            ):
                raise ContractError("world evidence case is outside the admitted scope")

    def provider_identity_dict(self) -> Dict[str, Any]:
        """Translate to the existing shared Playtest provider receipt shape."""

        return {
            "identity": self.provider.provider_id,
            "version": self.provider.version,
            "config_sha256": self.provider.config_sha256,
            "method_class": "independent-private-reference-measurement",
            "independent_of_make": True,
        }


class WorldPlaytestService(Protocol):
    """Credential-bearing Manager-side provider; never passed to Inventor code."""

    def evaluate(
        self,
        wish: Wish,
        artifact_sha256: str,
        personalization_map: Mapping[str, Any],
        invent_inputs: WorldInventInputs,
    ) -> WorldPlaytestEvidence:
        ...

    def verify(
        self,
        evidence: WorldPlaytestEvidence,
        wish: Wish,
        artifact_sha256: str,
        personalization_map: Mapping[str, Any],
        invent_inputs: WorldInventInputs,
    ) -> None:
        ...


def prepare_world_playtest_evidence(
    wish: Wish,
    artifact_sha256: str,
    personalization_map: Mapping[str, Any],
    invent_inputs: WorldInventInputs,
    service: WorldPlaytestService,
) -> WorldPlaytestEvidence:
    """Run and authenticate private-reference comparison in the Manager process."""

    evaluate = getattr(service, "evaluate", None)
    verify = getattr(service, "verify", None)
    if not callable(evaluate) or not callable(verify):
        raise ContractError("world Playtest service is incomplete")
    evidence = evaluate(
        wish, artifact_sha256, personalization_map, invent_inputs
    )
    if not isinstance(evidence, WorldPlaytestEvidence):
        raise ContractError("world Playtest service returned untyped evidence")
    evidence.assert_context(
        wish, artifact_sha256, personalization_map, invent_inputs
    )
    verify(evidence, wish, artifact_sha256, personalization_map, invent_inputs)
    evidence.assert_context(
        wish, artifact_sha256, personalization_map, invent_inputs
    )
    return evidence


__all__ = [
    "EXTERNAL_WORLD_SERVICE_BOUNDARY",
    "WORLD_SERVICE_BOUNDARIES",
    "WorldEvidenceCase",
    "WorldEvidenceReference",
    "WorldInventInputs",
    "WorldInventReference",
    "WorldPlaytestEvidence",
    "WorldPlaytestService",
    "WorldProviderIdentity",
    "prepare_world_invent_inputs",
    "prepare_world_playtest_evidence",
]
