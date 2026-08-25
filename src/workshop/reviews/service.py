"""Authenticated, order-bound customer Reviews for delivered products."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Mapping, Protocol, TYPE_CHECKING

from workshop.errors import ContractError
from workshop._validation import require_exact_version, require_sha256, require_utc_timestamp

if TYPE_CHECKING:
    from workshop.deliver.contracts import Delivered
    from workshop.reviews.contracts import CustomerReview


REVIEW_AUTHENTICATION_KIND = "workshop.customer-review-authentication"
_FIELDS = frozenset(
    (
        "schema_version",
        "kind",
        "authentication_id",
        "provider",
        "provider_version",
        "provider_config_sha256",
        "order_id",
        "reviewer_id",
        "review_id",
        "review_sha256",
        "product_artifact_sha256",
        "instructions_sha256",
        "delivery_tracking_id",
        "authenticated_at",
        "authentication_sha256",
    )
)


def _text(value: Any, label: str, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be a bounded identifier" % label)
    return value


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Review authentication must contain finite JSON") from exc


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _instant(value: str) -> datetime:
    require_utc_timestamp(value, "Review authentication timestamp")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


def review_sha256(review: "CustomerReview") -> str:
    from workshop.reviews.contracts import CustomerReview

    if not isinstance(review, CustomerReview):
        raise ContractError("Review authentication requires a CustomerReview")
    return _sha256(review.to_dict())


@dataclass(frozen=True)
class ReviewAuthentication:
    """Trusted provider proof that one reviewer owns one delivered order."""

    authentication_id: str
    provider: str
    provider_version: str
    provider_config_sha256: str
    order_id: str
    reviewer_id: str
    review_id: str
    review_sha256: str
    product_artifact_sha256: str
    instructions_sha256: str
    delivery_tracking_id: str
    authenticated_at: str
    schema_version: int = 1
    kind: str = REVIEW_AUTHENTICATION_KIND
    authentication_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Review authentication schema_version must be 1")
        if self.kind != REVIEW_AUTHENTICATION_KIND:
            raise ContractError("Review authentication kind is invalid")
        _text(self.authentication_id, "Review authentication_id")
        _text(self.provider, "Review authentication provider", 300)
        require_exact_version(
            self.provider_version, "Review authentication provider_version"
        )
        require_sha256(
            self.provider_config_sha256,
            "Review authentication provider config sha256",
        )
        _text(self.order_id, "Review order_id")
        _text(self.reviewer_id, "Review reviewer_id")
        _text(self.review_id, "Review review_id", 256)
        require_sha256(self.review_sha256, "authenticated Review sha256")
        require_sha256(
            self.product_artifact_sha256,
            "Review authentication product artifact sha256",
        )
        require_sha256(
            self.instructions_sha256,
            "Review authentication Instructions sha256",
        )
        _text(self.delivery_tracking_id, "Review delivery_tracking_id", 300)
        require_utc_timestamp(
            self.authenticated_at, "Review authentication authenticated_at"
        )
        object.__setattr__(
            self, "authentication_sha256", _sha256(self._identity_dict())
        )

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "authentication_id": self.authentication_id,
            "provider": self.provider,
            "provider_version": self.provider_version,
            "provider_config_sha256": self.provider_config_sha256,
            "order_id": self.order_id,
            "reviewer_id": self.reviewer_id,
            "review_id": self.review_id,
            "review_sha256": self.review_sha256,
            "product_artifact_sha256": self.product_artifact_sha256,
            "instructions_sha256": self.instructions_sha256,
            "delivery_tracking_id": self.delivery_tracking_id,
            "authenticated_at": self.authenticated_at,
        }

    def to_dict(self) -> Dict[str, Any]:
        value = self._identity_dict()
        value["authentication_sha256"] = self.authentication_sha256
        return value

    @classmethod
    def from_dict(cls, value: Any) -> "ReviewAuthentication":
        if not isinstance(value, Mapping) or set(value) != _FIELDS:
            raise ContractError("Review authentication receipt is malformed")
        authentication = cls(
            authentication_id=value["authentication_id"],
            provider=value["provider"],
            provider_version=value["provider_version"],
            provider_config_sha256=value["provider_config_sha256"],
            order_id=value["order_id"],
            reviewer_id=value["reviewer_id"],
            review_id=value["review_id"],
            review_sha256=value["review_sha256"],
            product_artifact_sha256=value["product_artifact_sha256"],
            instructions_sha256=value["instructions_sha256"],
            delivery_tracking_id=value["delivery_tracking_id"],
            authenticated_at=value["authenticated_at"],
            schema_version=value["schema_version"],
            kind=value["kind"],
        )
        if value["authentication_sha256"] != authentication.authentication_sha256:
            raise ContractError("Review authentication identity is inconsistent")
        return authentication

    def assert_review(
        self, review: "CustomerReview", delivered: "Delivered"
    ) -> None:
        from workshop.deliver.contracts import Delivered
        from workshop.reviews.contracts import CustomerReview

        if not isinstance(review, CustomerReview) or not isinstance(delivered, Delivered):
            raise ContractError(
                "Review authentication requires typed Review and Deliver records"
            )
        review.assert_delivery(delivered)
        if (
            self.review_id != review.review_id
            or self.review_sha256 != review_sha256(review)
            or self.product_artifact_sha256 != review.product_artifact_sha256
            or self.instructions_sha256 != review.instructions_sha256
            or self.delivery_tracking_id != review.delivery_tracking_id
        ):
            raise ContractError(
                "Review authentication belongs to different feedback or delivery"
            )
        if _instant(self.authenticated_at) < max(
            _instant(delivered.observed_at), _instant(review.observed_at)
        ):
            raise ContractError(
                "Review authentication cannot predate delivery or feedback"
            )


class ReviewAuthenticator(Protocol):
    def __call__(
        self, delivered: "Delivered", review: "CustomerReview"
    ) -> ReviewAuthentication:
        ...


__all__ = [
    "REVIEW_AUTHENTICATION_KIND",
    "ReviewAuthentication",
    "ReviewAuthenticator",
    "review_sha256",
]
