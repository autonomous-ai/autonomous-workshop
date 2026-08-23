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
_UNSET = object()


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
class InspectionResult:
    """A deterministic or external verdict bound to exact artifact bytes."""

    inspection_id: str
    passed: bool
    artifact_sha256: str
    evidence: Mapping[str, Any]
    evaluator: str
    evaluator_version: str
    config_sha256: str
    evidence_ref: str
    evidence_sha256: str
    observed_at: str

    @property
    def gate_id(self) -> str:
        """Compatibility spelling used by Workshop 0.2 and older."""

        return self.inspection_id

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        if not self.inspection_id or not isinstance(self.inspection_id, str):
            raise ContractError("inspection_id must be a non-empty string")
        if not isinstance(self.passed, bool):
            raise ContractError("inspection passed must be boolean")
        require_sha256(self.artifact_sha256, "inspection artifact_sha256")
        if (
            not isinstance(self.evaluator, str)
            or not self.evaluator
            or self.evaluator.casefold() in {"self-report", "trust-me"}
        ):
            raise ContractError("inspection evaluator must be named")
        require_exact_version(self.evaluator_version, "inspection evaluator_version")
        require_sha256(self.config_sha256, "gate config_sha256")
        require_safe_evidence_path(self.evidence_ref, "inspection evidence_ref")
        require_sha256(self.evidence_sha256, "inspection evidence_sha256")
        require_utc_timestamp(self.observed_at, "inspection observed_at")
        if not self.evidence:
            raise ContractError("inspection evidence must be a non-empty object")
        require_json_mapping(self.evidence, "inspection evidence")

    @classmethod
    def create(
        cls,
        inspection_id: str,
        passed: bool,
        artifact_sha256: str,
        evidence: Mapping[str, Any],
        evaluator: str,
        evaluator_version: str,
        config_sha256: str,
        evidence_ref: str,
        evidence_sha256: str,
    ) -> "InspectionResult":
        return cls(
            inspection_id,
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


@dataclass(frozen=True, init=False)
class Stamp:
    """Authenticated Door readback bound to the exact Pack that was sent.

    A local flag, successful HTTP status, or model-authored message is not a
    stamp. ``is_verified_public`` additionally requires the Shop Door to report that
    the exact current history entry is the published history entry.
    """

    pack_sha256: str
    artifact_sha256: str
    door: str
    status: str
    observed_at: str
    reference: str
    details: Mapping[str, Any]
    design_id: Optional[str] = None
    slug: Optional[str] = None
    owner_id: Optional[str] = None
    root_id: Optional[str] = None
    current_history_id: Optional[str] = None
    project_url: Optional[str] = None
    published_history_id: Optional[str] = None
    listing_active: Optional[bool] = None
    listing_price_cents: Optional[int] = None
    listing_currency: Optional[str] = None
    listing_sku: Optional[str] = None

    def __init__(
        self,
        pack_sha256: Any = _UNSET,
        artifact_sha256: Any = _UNSET,
        design_id: Any = _UNSET,
        slug: Any = _UNSET,
        owner_id: Any = _UNSET,
        root_id: Any = _UNSET,
        current_history_id: Any = _UNSET,
        status: Any = _UNSET,
        project_url: Any = _UNSET,
        observed_at: Any = _UNSET,
        published_history_id: Optional[str] = None,
        listing_active: Optional[bool] = None,
        listing_price_cents: Optional[int] = None,
        listing_currency: Optional[str] = None,
        listing_sku: Optional[str] = None,
        *,
        packet_sha256: Any = _UNSET,
        door: Any = _UNSET,
        reference: Any = _UNSET,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Create a Door-neutral Stamp while accepting v0.2 shop records."""

        if pack_sha256 is _UNSET:
            pack_sha256 = packet_sha256
        elif packet_sha256 is not _UNSET and pack_sha256 != packet_sha256:
            raise ReceiptError("Stamp has conflicting pack_sha256 and packet_sha256")
        legacy_shop = any(
            value is not _UNSET
            for value in (
                design_id,
                slug,
                owner_id,
                root_id,
                current_history_id,
                project_url,
            )
        )
        if door is _UNSET:
            door = "shop" if legacy_shop else _UNSET
        if reference is _UNSET and legacy_shop:
            reference = design_id
        for field_name, value in (
            ("design_id", design_id),
            ("slug", slug),
            ("owner_id", owner_id),
            ("root_id", root_id),
            ("current_history_id", current_history_id),
            ("project_url", project_url),
        ):
            if value is _UNSET:
                locals_value = None
            else:
                locals_value = value
            object.__setattr__(self, field_name, locals_value)
        copied_details = dict(details) if isinstance(details, Mapping) else details
        if details is None:
            copied_details = {}
        for name, value in (
            ("pack_sha256", pack_sha256),
            ("artifact_sha256", artifact_sha256),
            ("door", door),
            ("status", status),
            ("observed_at", observed_at),
            ("reference", reference),
            ("details", copied_details),
            ("published_history_id", published_history_id),
            ("listing_active", listing_active),
            ("listing_price_cents", listing_price_cents),
            ("listing_currency", listing_currency),
            ("listing_sku", listing_sku),
        ):
            object.__setattr__(self, name, value)
        self.__post_init__()

    @property
    def packet_sha256(self) -> str:
        """Compatibility spelling used by Workshop 0.2 and older."""

        return self.pack_sha256

    def __post_init__(self) -> None:
        require_sha256(self.pack_sha256, "Stamp pack_sha256")
        require_sha256(self.artifact_sha256, "Stamp artifact_sha256")
        for field_name in (
            "door",
            "status",
            "observed_at",
            "reference",
        ):
            value = getattr(self, field_name)
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > 4096
                or any(ord(character) < 32 or ord(character) == 127 for character in value)
            ):
                raise ReceiptError("Stamp %s must be a bounded non-empty string" % field_name)
        require_json_mapping(self.details, "Stamp details")
        for field_name in (
            "design_id",
            "slug",
            "owner_id",
            "root_id",
            "current_history_id",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ReceiptError("Stamp %s must be a string or null" % field_name)
        if self.published_history_id is not None and (
            not isinstance(self.published_history_id, str)
            or not self.published_history_id.strip()
        ):
            raise ReceiptError("receipt published_history_id must be a string or null")
        if self.project_url is not None:
            try:
                project = urllib.parse.urlsplit(self.project_url)
            except (TypeError, ValueError) as exc:
                raise ReceiptError("Stamp project_url is malformed") from exc
            if (
                any(ord(character) < 32 or ord(character) == 127 for character in self.project_url)
                or project.scheme != "https"
                or not project.hostname
                or project.username is not None
                or project.password is not None
                or project.query
                or project.fragment
            ):
                raise ReceiptError("Stamp project_url must be an absolute HTTPS URL")
        require_utc_timestamp(self.observed_at, "receipt observed_at")
        if self.listing_active is not None and not isinstance(self.listing_active, bool):
            raise ReceiptError("receipt listing_active must be boolean or null")
        if self.listing_price_cents is not None and (
            not isinstance(self.listing_price_cents, int)
            or isinstance(self.listing_price_cents, bool)
            or not 100 <= self.listing_price_cents <= 1_000_000
        ):
            raise ReceiptError("Stamp listing_price_cents is outside the Shop Door range")
        for field_name in ("listing_currency", "listing_sku"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ReceiptError("receipt %s must be a non-empty string or null" % field_name)

    @classmethod
    def create(
        cls,
        pack_sha256: str,
        artifact_sha256: str,
        door: str,
        status: str,
        reference: str,
        details: Optional[Mapping[str, Any]] = None,
        observed_at: Optional[str] = None,
    ) -> "Stamp":
        """Create a Door-neutral stamp with the canonical Workshop fields."""

        return cls(
            pack_sha256=pack_sha256,
            artifact_sha256=artifact_sha256,
            status=status,
            observed_at=observed_at or utc_now(),
            door=door,
            reference=reference,
            details=details,
        )

    @classmethod
    def from_design(
        cls,
        design: Mapping[str, Any],
        pack_sha256: Any = _UNSET,
        artifact_sha256: Any = _UNSET,
        observed_at: Optional[str] = None,
        *,
        packet_sha256: Any = _UNSET,
    ) -> "Stamp":
        if pack_sha256 is _UNSET:
            pack_sha256 = packet_sha256
        elif packet_sha256 is not _UNSET and pack_sha256 != packet_sha256:
            raise ReceiptError("Stamp has conflicting pack_sha256 and packet_sha256")
        author = design.get("author")
        if not isinstance(author, Mapping):
            author = {}
        owner_id = design.get("owner_id") or author.get("id")
        listing = design.get("listing")
        if not isinstance(listing, Mapping):
            listing = {}
        return cls(
            pack_sha256=pack_sha256,
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
            door="shop",
            reference=design.get("id"),
            details={"kind": "shop-design"},
            listing_active=listing.get("active"),
            listing_price_cents=listing.get("price_cents"),
            listing_currency=listing.get("currency"),
            listing_sku=listing.get("sku"),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Stamp":
        """Read canonical or v0.2 persisted Stamp data."""

        if not isinstance(value, Mapping):
            raise ReceiptError("Stamp record must be an object")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ReceiptError("Stamp record contains unknown fields") from exc

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

    def assert_pack(self, expected_sha256: str) -> None:
        require_sha256(expected_sha256, "expected Pack sha256")
        if self.pack_sha256 != expected_sha256:
            raise ReceiptError("receipt belongs to different artifact bytes")

    def assert_packet(self, expected_sha256: str) -> None:
        """Compatibility spelling for :meth:`assert_pack`."""

        self.assert_pack(expected_sha256)

    def assert_artifact(self, expected_sha256: str) -> None:
        if self.artifact_sha256 != expected_sha256:
            raise ReceiptError("receipt manifest belongs to different product bytes")

    def to_dict(self) -> Dict[str, Any]:
        self.__post_init__()
        return {
            "pack_sha256": self.pack_sha256,
            "artifact_sha256": self.artifact_sha256,
            "door": self.door,
            "status": self.status,
            "observed_at": self.observed_at,
            "reference": self.reference,
            "details": dict(self.details),
            "design_id": self.design_id,
            "slug": self.slug,
            "owner_id": self.owner_id,
            "root_id": self.root_id,
            "current_history_id": self.current_history_id,
            "project_url": self.project_url,
            "published_history_id": self.published_history_id,
            "listing_active": self.listing_active,
            "listing_price_cents": self.listing_price_cents,
            "listing_currency": self.listing_currency,
            "listing_sku": self.listing_sku,
        }


@dataclass(frozen=True, init=False)
class SendResult:
    """Local outbox identity paired with its authenticated remote Stamp."""

    intent_id: str
    stamp: Stamp

    def __init__(
        self,
        intent_id: str,
        stamp: Any = _UNSET,
        *,
        receipt: Any = _UNSET,
    ) -> None:
        if stamp is _UNSET:
            stamp = receipt
        elif receipt is not _UNSET and stamp != receipt:
            raise ContractError("SendResult has conflicting stamp and receipt")
        object.__setattr__(self, "intent_id", intent_id)
        object.__setattr__(self, "stamp", stamp)
        self.__post_init__()

    @property
    def receipt(self) -> Stamp:
        """Compatibility spelling used by Workshop 0.2 and older."""

        return self.stamp

    def __post_init__(self) -> None:
        if not isinstance(self.intent_id, str) or not self.intent_id:
            raise ContractError("publication outcome intent_id is required")
        if not isinstance(self.stamp, Stamp):
            raise ContractError("SendResult stamp must be a Stamp")

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "SendResult":
        """Read canonical or v0.2 persisted SendResult data."""

        if not isinstance(value, Mapping):
            raise ContractError("SendResult record must be an object")
        unknown = set(value) - {"intent_id", "stamp", "receipt"}
        if unknown:
            raise ContractError("SendResult record contains unknown fields")
        stamp = value.get("stamp", _UNSET)
        receipt = value.get("receipt", _UNSET)
        if stamp is not _UNSET:
            stamp = Stamp.from_dict(stamp) if isinstance(stamp, Mapping) else stamp
        if receipt is not _UNSET:
            receipt = Stamp.from_dict(receipt) if isinstance(receipt, Mapping) else receipt
        return cls(value.get("intent_id"), stamp=stamp, receipt=receipt)

    def to_dict(self) -> Dict[str, Any]:
        self.__post_init__()
        return {"intent_id": self.intent_id, "stamp": self.stamp.to_dict()}


# Compatibility names for code written before Workshop 0.3.
GateResult = InspectionResult
PublicationReceipt = Stamp
PublicationOutcome = SendResult
