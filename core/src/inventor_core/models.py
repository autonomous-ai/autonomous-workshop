"""Small immutable evidence objects used across inventor implementations."""

from __future__ import annotations

import json
import re
import urllib.parse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Dict, Mapping, Optional

from .errors import ContractError, ReceiptError

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXACT_VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
MAX_EVIDENCE_JSON_BYTES = 2 * 1024 * 1024


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_utc_timestamp(value: str, label: str = "timestamp") -> str:
    if not isinstance(value, str):
        raise ContractError("%s must be an ISO-8601 UTC timestamp" % label)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("%s must be an ISO-8601 UTC timestamp" % label) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ContractError("%s must include an explicit UTC offset" % label)
    return value


def require_exact_version(value: str, label: str = "version") -> str:
    floating = {
        "latest",
        "main",
        "master",
        "head",
        "dev",
        "development",
        "unknown",
        "snapshot",
        "x",
    }
    if (
        not isinstance(value, str)
        or not _EXACT_VERSION.fullmatch(value)
        or not any(character.isdigit() for character in value)
        or any(
            segment in floating
            for segment in re.split(r"[._+-]", value.casefold())
        )
    ):
        raise ContractError("%s must be an exact, non-floating version" % label)
    return value


def require_safe_evidence_path(value: str, label: str = "evidence_ref") -> str:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or not candidate.parts
        or value in (".", "..")
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe relative POSIX path" % label)
    return value


def require_sha256(value: str, label: str = "sha256") -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise ContractError("%s must be 64 lowercase hexadecimal characters" % label)
    return value


def require_json_mapping(
    value: Mapping[str, Any], label: str, maximum_bytes: int = MAX_EVIDENCE_JSON_BYTES
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("%s must be an object" % label)

    def normalize(item: Any, depth: int = 0, active: Optional[set] = None) -> Any:
        if depth > 64:
            raise ContractError("%s exceeds the JSON nesting limit" % label)
        active = active if active is not None else set()
        if item is None or isinstance(item, (str, bool, int)):
            return item
        if isinstance(item, float):
            if item != item or item in (float("inf"), float("-inf")):
                raise ContractError("%s must contain only finite JSON numbers" % label)
            return item
        if isinstance(item, Mapping):
            if not all(isinstance(key, str) for key in item):
                raise ContractError("%s object keys must be strings" % label)
            identity = id(item)
            if identity in active:
                raise ContractError("%s must not contain cycles" % label)
            active.add(identity)
            try:
                return {
                    key: normalize(nested, depth + 1, active)
                    for key, nested in item.items()
                }
            finally:
                active.remove(identity)
        if isinstance(item, (list, tuple)):
            identity = id(item)
            if identity in active:
                raise ContractError("%s must not contain cycles" % label)
            active.add(identity)
            try:
                return [normalize(nested, depth + 1, active) for nested in item]
            finally:
                active.remove(identity)
        raise ContractError("%s contains a non-JSON value" % label)

    normalized = normalize(value)
    payload = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    if len(payload) > maximum_bytes:
        raise ContractError("%s exceeds the %d-byte limit" % (label, maximum_bytes))
    return value


@dataclass(frozen=True)
class GateResult:
    """A deterministic or external verdict bound to exact artifact bytes."""

    gate_id: str
    passed: bool
    artifact_sha256: str
    evidence: Mapping[str, Any]
    evaluator: str
    evaluator_version: str
    config_sha256: str
    evidence_ref: str
    evidence_sha256: str
    observed_at: str

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if not self.gate_id or not isinstance(self.gate_id, str):
            raise ContractError("gate_id must be a non-empty string")
        if not isinstance(self.passed, bool):
            raise ContractError("gate passed must be boolean")
        require_sha256(self.artifact_sha256, "gate artifact_sha256")
        if (
            not isinstance(self.evaluator, str)
            or not self.evaluator
            or self.evaluator.casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("gate evaluator must be named")
        require_exact_version(self.evaluator_version, "gate evaluator_version")
        require_sha256(self.config_sha256, "gate config_sha256")
        require_safe_evidence_path(self.evidence_ref, "gate evidence_ref")
        require_sha256(self.evidence_sha256, "gate evidence_sha256")
        require_utc_timestamp(self.observed_at, "gate observed_at")
        if not self.evidence:
            raise ContractError("gate evidence must be a non-empty object")
        require_json_mapping(self.evidence, "gate evidence")

    @classmethod
    def create(
        cls,
        gate_id: str,
        passed: bool,
        artifact_sha256: str,
        evidence: Mapping[str, Any],
        evaluator: str,
        evaluator_version: str,
        config_sha256: str,
        evidence_ref: str,
        evidence_sha256: str,
    ) -> "GateResult":
        return cls(
            gate_id,
            passed,
            artifact_sha256,
            evidence,
            evaluator,
            evaluator_version,
            config_sha256,
            evidence_ref,
            evidence_sha256,
            utc_now(),
        )

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return asdict(self)


@dataclass(frozen=True)
class PublicationReceipt:
    """Authenticated Panda readback bound to the packet that was uploaded.

    A local flag, successful HTTP status, or model-authored message is not a
    receipt.  `is_verified_public` additionally requires Panda to report that
    the exact current history entry is the published history entry.
    """

    packet_sha256: str
    artifact_sha256: str
    design_id: str
    slug: str
    owner_id: str
    root_id: str
    current_history_id: str
    status: str
    project_url: str
    observed_at: str
    published_history_id: Optional[str] = None
    listing_active: Optional[bool] = None
    listing_price_cents: Optional[int] = None
    listing_currency: Optional[str] = None
    listing_sku: Optional[str] = None

    def __post_init__(self) -> None:
        require_sha256(self.packet_sha256, "receipt packet_sha256")
        require_sha256(self.artifact_sha256, "receipt artifact_sha256")
        for field_name in (
            "design_id",
            "slug",
            "owner_id",
            "root_id",
            "current_history_id",
            "status",
            "project_url",
            "observed_at",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ReceiptError("receipt %s is required" % field_name)
        if self.published_history_id is not None and (
            not isinstance(self.published_history_id, str)
            or not self.published_history_id.strip()
        ):
            raise ReceiptError("receipt published_history_id must be a string or null")
        if self.status not in ("draft", "public"):
            raise ReceiptError("receipt status must be draft or public")
        try:
            project = urllib.parse.urlsplit(self.project_url)
        except ValueError as exc:
            raise ReceiptError("receipt project_url is malformed") from exc
        if (
            any(ord(character) < 32 or ord(character) == 127 for character in self.project_url)
            or project.scheme != "https"
            or not project.hostname
            or project.username is not None
            or project.password is not None
            or project.query
            or project.fragment
        ):
            raise ReceiptError("receipt project_url must be an absolute HTTPS URL")
        require_utc_timestamp(self.observed_at, "receipt observed_at")
        if self.listing_active is not None and not isinstance(self.listing_active, bool):
            raise ReceiptError("receipt listing_active must be boolean or null")
        if self.listing_price_cents is not None and (
            not isinstance(self.listing_price_cents, int)
            or isinstance(self.listing_price_cents, bool)
            or not 100 <= self.listing_price_cents <= 1_000_000
        ):
            raise ReceiptError("receipt listing_price_cents is outside Panda's range")
        for field_name in ("listing_currency", "listing_sku"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ReceiptError("receipt %s must be a non-empty string or null" % field_name)

    @classmethod
    def from_design(
        cls,
        design: Mapping[str, Any],
        packet_sha256: str,
        artifact_sha256: str,
        observed_at: Optional[str] = None,
    ) -> "PublicationReceipt":
        author = design.get("author")
        if not isinstance(author, Mapping):
            author = {}
        owner_id = design.get("owner_id") or author.get("id")
        listing = design.get("listing")
        if not isinstance(listing, Mapping):
            listing = {}
        return cls(
            packet_sha256=packet_sha256,
            artifact_sha256=artifact_sha256,
            design_id=design.get("id"),
            slug=design.get("slug"),
            owner_id=owner_id,
            root_id=design.get("root_id"),
            current_history_id=design.get("current_history_id"),
            published_history_id=design.get("published_history_id"),
            status=design.get("status"),
            project_url=design.get("project_url"),
            observed_at=observed_at or utc_now(),
            listing_active=listing.get("active"),
            listing_price_cents=listing.get("price_cents"),
            listing_currency=listing.get("currency"),
            listing_sku=listing.get("sku"),
        )

    @property
    def is_verified_public(self) -> bool:
        return (
            self.status == "public"
            and self.published_history_id is not None
            and self.published_history_id == self.current_history_id
            and self.listing_active is True
            and self.listing_price_cents is not None
            and self.listing_currency == "USD"
            and bool(self.listing_sku)
        )

    def assert_listing(self, expected_price_cents: int) -> None:
        if (
            self.listing_active is not True
            or self.listing_price_cents != expected_price_cents
            or self.listing_currency != "USD"
            or not self.listing_sku
        ):
            raise ReceiptError(
                "receipt does not prove an active USD listing at the requested price"
            )

    def assert_owner(self, expected_owner_id: str) -> None:
        if self.owner_id != expected_owner_id:
            raise ReceiptError(
                "receipt owner %r does not match inventor account %r"
                % (self.owner_id, expected_owner_id)
            )

    def assert_packet(self, expected_sha256: str) -> None:
        if self.packet_sha256 != expected_sha256:
            raise ReceiptError("receipt belongs to different artifact bytes")

    def assert_artifact(self, expected_sha256: str) -> None:
        if self.artifact_sha256 != expected_sha256:
            raise ReceiptError("receipt manifest belongs to different product bytes")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PublicationOutcome:
    """Local outbox identity paired with its authenticated remote receipt."""

    intent_id: str
    receipt: PublicationReceipt

    def __post_init__(self) -> None:
        if not isinstance(self.intent_id, str) or not self.intent_id:
            raise ContractError("publication outcome intent_id is required")
        if not isinstance(self.receipt, PublicationReceipt):
            raise ContractError("publication outcome receipt must be a PublicationReceipt")
