"""Canonical proof returned by authenticated external-effect readback."""

from __future__ import annotations

import urllib.parse
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Mapping, Optional

from workshop._validation import (
    require_json_mapping,
    require_sha256,
    require_utc_timestamp,
    utc_now,
)
from workshop.errors import ReceiptError


def _bounded_text(value: Any, label: str, *, maximum: int = 4096) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ReceiptError("Receipt %s must be bounded non-empty text" % label)
    return value


def _optional_text(value: Any, label: str) -> Optional[str]:
    if value is None:
        return None
    return _bounded_text(value, label)


@dataclass(frozen=True)
class Receipt:
    """Authenticated provider readback bound to exact local artifact bytes.

    ``payload_sha256`` identifies the exact serialized payload sent through the
    adapter. ``artifact_sha256`` identifies the source product tree. Provider
    identifiers are observations from authenticated readback; they are not
    accepted as proof when the payload or artifact bindings differ.
    """

    payload_sha256: str
    artifact_sha256: str
    adapter: str
    status: str
    observed_at: str
    reference: str
    details: Mapping[str, Any] = field(default_factory=dict)
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

    def __post_init__(self) -> None:
        require_sha256(self.payload_sha256, "Receipt payload_sha256")
        require_sha256(self.artifact_sha256, "Receipt artifact_sha256")
        for name in ("adapter", "status", "reference"):
            object.__setattr__(self, name, _bounded_text(getattr(self, name), name))
        require_utc_timestamp(self.observed_at, "Receipt observed_at")
        require_json_mapping(self.details, "Receipt details")
        object.__setattr__(self, "details", dict(self.details))
        for name in (
            "design_id",
            "slug",
            "owner_id",
            "root_id",
            "current_history_id",
            "published_history_id",
            "listing_currency",
            "listing_sku",
        ):
            object.__setattr__(self, name, _optional_text(getattr(self, name), name))
        if self.project_url is not None:
            project_url = _bounded_text(self.project_url, "project_url")
            try:
                parsed = urllib.parse.urlsplit(project_url)
            except ValueError as exc:
                raise ReceiptError("Receipt project_url is malformed") from exc
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.query
                or parsed.fragment
            ):
                raise ReceiptError("Receipt project_url must be an absolute HTTPS URL")
        if self.listing_active is not None and type(self.listing_active) is not bool:
            raise ReceiptError("Receipt listing_active must be boolean or null")
        if self.listing_price_cents is not None and (
            type(self.listing_price_cents) is not int
            or not 100 <= self.listing_price_cents <= 1_000_000
        ):
            raise ReceiptError("Receipt listing_price_cents is outside the Factory range")

    @classmethod
    def create(
        cls,
        *,
        payload_sha256: str,
        artifact_sha256: str,
        adapter: str,
        status: str,
        reference: str,
        details: Optional[Mapping[str, Any]] = None,
        observed_at: Optional[str] = None,
    ) -> "Receipt":
        return cls(
            payload_sha256=payload_sha256,
            artifact_sha256=artifact_sha256,
            adapter=adapter,
            status=status,
            observed_at=observed_at or utc_now(),
            reference=reference,
            details=details or {},
        )

    @classmethod
    def from_factory_design(
        cls,
        design: Mapping[str, Any],
        *,
        payload_sha256: str,
        artifact_sha256: str,
        observed_at: Optional[str] = None,
        details: Optional[Mapping[str, Any]] = None,
    ) -> "Receipt":
        if not isinstance(design, Mapping):
            raise ReceiptError("Factory design readback must be an object")
        author = design.get("author")
        if not isinstance(author, Mapping):
            author = {}
        listing = design.get("listing")
        if not isinstance(listing, Mapping):
            listing = {}
        currency = listing.get("currency")
        if isinstance(currency, str) and currency.casefold() == "usd":
            currency = "USD"
        return cls(
            payload_sha256=payload_sha256,
            artifact_sha256=artifact_sha256,
            adapter="factory",
            status=design.get("status"),
            observed_at=observed_at or utc_now(),
            reference=design.get("id"),
            details=details or {"kind": "factory-design"},
            design_id=design.get("id"),
            slug=design.get("slug"),
            owner_id=design.get("owner_id") or author.get("id"),
            root_id=design.get("root_id"),
            current_history_id=design.get("current_history_id"),
            project_url=design.get("project_url"),
            published_history_id=design.get("published_history_id"),
            listing_active=listing.get("active"),
            listing_price_cents=listing.get("price_cents"),
            listing_currency=currency,
            listing_sku=listing.get("sku"),
        )

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]) -> "Receipt":
        if not isinstance(value, Mapping):
            raise ReceiptError("Receipt record must be an object")
        try:
            return cls(**dict(value))
        except TypeError as exc:
            raise ReceiptError("Receipt record contains unknown or missing fields") from exc

    @property
    def is_verified_draft(self) -> bool:
        return (
            self.adapter == "factory"
            and self.status == "draft"
            and self.published_history_id is None
            and self.listing_active is not True
            and all(
                isinstance(value, str) and bool(value)
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
            self.adapter == "factory"
            and self.status == "public"
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
                "Receipt does not prove an active USD listing at the requested price"
            )

    def assert_owner(self, expected_owner_id: str) -> None:
        if self.owner_id != expected_owner_id:
            raise ReceiptError(
                "Receipt owner %r does not match Factory account %r"
                % (self.owner_id, expected_owner_id)
            )

    def assert_payload(self, expected_sha256: str) -> None:
        require_sha256(expected_sha256, "expected payload sha256")
        if self.payload_sha256 != expected_sha256:
            raise ReceiptError("Receipt belongs to different payload bytes")

    def assert_artifact(self, expected_sha256: str) -> None:
        require_sha256(expected_sha256, "expected artifact sha256")
        if self.artifact_sha256 != expected_sha256:
            raise ReceiptError("Receipt belongs to different product bytes")

    def to_dict(self) -> Dict[str, Any]:
        self.__post_init__()
        return asdict(self)


__all__ = ["Receipt"]
