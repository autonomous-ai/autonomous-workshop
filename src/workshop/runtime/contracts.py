"""Runtime-owned proof contracts for durable external effects.

Adapters create these values, but the runtime owns their validation and
persistence contract. Keeping the proof vocabulary here prevents durable
state from depending on any concrete integration package.
"""

from __future__ import annotations

import urllib.parse
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional

from workshop._validation import (
    require_json_mapping,
    require_sha256,
    require_utc_timestamp,
    utc_now,
)
from workshop.errors import ContractError, ReceiptError


_UNSET = object()


@dataclass(frozen=True, init=False)
class Receipt:
    """Authenticated external readback bound to exact Artifact bytes.

    A local flag, successful HTTP status, or model-authored message is not a
    receipt. ``is_verified_public`` additionally requires the shop adapter to
    report that the exact current history entry is the published history entry.

    Persisted Workshop 0.3 records use ``pack_sha256`` and ``door``.  Those
    fields stay stable on disk; ``payload_sha256`` and ``adapter`` are the
    canonical code-facing spellings.
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
        payload_sha256: Any = _UNSET,
        door: Any = _UNSET,
        adapter: Any = _UNSET,
        reference: Any = _UNSET,
        details: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Create a Receipt while accepting persisted v0.2/v0.3 records."""

        if pack_sha256 is _UNSET:
            pack_sha256 = (
                payload_sha256 if payload_sha256 is not _UNSET else packet_sha256
            )
        for alias, value in (
            ("packet_sha256", packet_sha256),
            ("payload_sha256", payload_sha256),
        ):
            if value is not _UNSET and pack_sha256 != value:
                raise ReceiptError(
                    "Receipt has conflicting pack_sha256 and %s" % alias
                )
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
            door = adapter if adapter is not _UNSET else (
                "shop" if legacy_shop else _UNSET
            )
        elif adapter is not _UNSET and door != adapter:
            raise ReceiptError("Receipt has conflicting door and adapter")
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

    @property
    def payload_sha256(self) -> str:
        """Identity of the exact serialized bytes observed externally."""

        return self.pack_sha256

    @property
    def adapter(self) -> str:
        """Implementation that produced this authenticated readback."""

        return self.door

    def __post_init__(self) -> None:
        require_sha256(self.pack_sha256, "Receipt payload_sha256")
        require_sha256(self.artifact_sha256, "Receipt artifact_sha256")
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
                raise ReceiptError("Receipt %s must be a bounded non-empty string" % field_name)
        require_json_mapping(self.details, "Receipt details")
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
                raise ReceiptError("Receipt %s must be a string or null" % field_name)
        if self.published_history_id is not None and (
            not isinstance(self.published_history_id, str)
            or not self.published_history_id.strip()
        ):
            raise ReceiptError("receipt published_history_id must be a string or null")
        if self.project_url is not None:
            try:
                project = urllib.parse.urlsplit(self.project_url)
            except (TypeError, ValueError) as exc:
                raise ReceiptError("Receipt project_url is malformed") from exc
            if (
                any(ord(character) < 32 or ord(character) == 127 for character in self.project_url)
                or project.scheme != "https"
                or not project.hostname
                or project.username is not None
                or project.password is not None
                or project.query
                or project.fragment
            ):
                raise ReceiptError("Receipt project_url must be an absolute HTTPS URL")
        require_utc_timestamp(self.observed_at, "receipt observed_at")
        if self.listing_active is not None and not isinstance(self.listing_active, bool):
            raise ReceiptError("receipt listing_active must be boolean or null")
        if self.listing_price_cents is not None and (
            not isinstance(self.listing_price_cents, int)
            or isinstance(self.listing_price_cents, bool)
            or not 100 <= self.listing_price_cents <= 1_000_000
        ):
            raise ReceiptError("Receipt listing_price_cents is outside the shop range")
        for field_name in ("listing_currency", "listing_sku"):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ReceiptError("receipt %s must be a non-empty string or null" % field_name)

    @classmethod
    def create(
        cls,
        pack_sha256: Any = _UNSET,
        artifact_sha256: Any = _UNSET,
        door: Any = _UNSET,
        status: Any = _UNSET,
        reference: Any = _UNSET,
        details: Optional[Mapping[str, Any]] = None,
        observed_at: Optional[str] = None,
        *,
        payload_sha256: Any = _UNSET,
        adapter: Any = _UNSET,
    ) -> "Receipt":
        """Create an authenticated Receipt for an exact serialized Artifact."""

        return cls(
            pack_sha256=pack_sha256,
            payload_sha256=payload_sha256,
            artifact_sha256=artifact_sha256,
            status=status,
            observed_at=observed_at or utc_now(),
            door=door,
            adapter=adapter,
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
    ) -> "Receipt":
        if pack_sha256 is _UNSET:
            pack_sha256 = packet_sha256
        elif packet_sha256 is not _UNSET and pack_sha256 != packet_sha256:
            raise ReceiptError("Receipt has conflicting pack_sha256 and packet_sha256")
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
            listing_currency=(
                listing.get("currency").upper()
                if isinstance(listing.get("currency"), str)
                else listing.get("currency")
            ),
            listing_sku=listing.get("sku"),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Receipt":
        """Read canonical or persisted v0.2/v0.3 Receipt data."""

        if not isinstance(value, Mapping):
            raise ReceiptError("Receipt record must be an object")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ReceiptError("Receipt record contains unknown fields") from exc

    @property
    def is_verified_draft(self) -> bool:
        """Whether authenticated Shop readback proves one private draft.

        A draft is deliberately weaker than :attr:`is_verified_public`: it has
        no active listing and makes no claim that a customer can see the page.
        It is nevertheless a real remote result, not a local ``status`` flag,
        because the Shop adapter must identify the owner, design, immutable
        history, canonical slug, and uploaded project directory.
        """

        return (
            self.door == "shop"
            and self.status == "draft"
            and self.published_history_id is None
            and self.listing_active is not True
            and all(
                isinstance(value, str) and bool(value.strip())
                for value in (
                    self.design_id,
                    self.slug,
                    self.owner_id,
                    self.root_id,
                    self.current_history_id,
                    self.project_url,
                )
            )
        )

    @property
    def is_verified_public(self) -> bool:
        return (
            self.status == "public"
            and self.published_history_id is not None
            and self.published_history_id == self.current_history_id
            and self.listing_active is True
            and self.listing_price_cents is not None
            and isinstance(self.listing_currency, str)
            and self.listing_currency.upper() == "USD"
            and bool(self.listing_sku)
        )

    def assert_listing(self, expected_price_cents: int) -> None:
        if (
            self.listing_active is not True
            or self.listing_price_cents != expected_price_cents
            or not isinstance(self.listing_currency, str)
            or self.listing_currency.upper() != "USD"
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

    def assert_payload(self, expected_sha256: str) -> None:
        """Require this Receipt to describe the exact serialized bytes."""

        require_sha256(expected_sha256, "expected payload sha256")
        if self.pack_sha256 != expected_sha256:
            raise ReceiptError("receipt belongs to different artifact bytes")

    def assert_pack(self, expected_sha256: str) -> None:
        """Compatibility spelling for :meth:`assert_payload`."""

        self.assert_payload(expected_sha256)

    def assert_packet(self, expected_sha256: str) -> None:
        """Compatibility spelling for :meth:`assert_pack`."""

        self.assert_pack(expected_sha256)

    def assert_artifact(self, expected_sha256: str) -> None:
        if self.artifact_sha256 != expected_sha256:
            raise ReceiptError("receipt manifest belongs to different product bytes")

    def to_dict(self) -> Dict[str, Any]:
        """Return the persisted Workshop 0.3-compatible representation."""

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

    def to_receipt_dict(self) -> Dict[str, Any]:
        """Return the canonical provider-facing Receipt representation."""

        value = self.to_dict()
        value["payload_sha256"] = value.pop("pack_sha256")
        value["adapter"] = value.pop("door")
        return value


# Compatibility name for Workshop 0.3 and older.
Stamp = Receipt


@dataclass(frozen=True, init=False)
class SendResult:
    """Compatibility result pairing an outbox identity with a Receipt."""

    intent_id: str
    stamp: Receipt

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
    def receipt(self) -> Receipt:
        """Compatibility spelling used by Workshop 0.2 and older."""

        return self.stamp

    def __post_init__(self) -> None:
        if not isinstance(self.intent_id, str) or not self.intent_id:
            raise ContractError("publication outcome intent_id is required")
        if not isinstance(self.stamp, Receipt):
            raise ContractError("SendResult stamp must be a Receipt")

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
            stamp = Receipt.from_dict(stamp) if isinstance(stamp, Mapping) else stamp
        if receipt is not _UNSET:
            receipt = Receipt.from_dict(receipt) if isinstance(receipt, Mapping) else receipt
        return cls(value.get("intent_id"), stamp=stamp, receipt=receipt)

    def to_dict(self) -> Dict[str, Any]:
        self.__post_init__()
        return {"intent_id": self.intent_id, "stamp": self.stamp.to_dict()}


# Compatibility names for code written before Workshop 0.4. These are true
# aliases so receipts created through either vocabulary are the same contract.
PublicationReceipt = Receipt
PublicationOutcome = SendResult


__all__ = [
    "Receipt",
]
