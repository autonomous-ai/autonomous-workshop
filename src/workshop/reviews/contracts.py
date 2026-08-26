"""Authenticated human feedback contract owned by Reviews."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from workshop._validation import bounded_text, require_sha256, require_utc_timestamp
from workshop.deliver.contracts import Delivered
from workshop.errors import ContractError


@dataclass(frozen=True)
class CustomerReview:
    """Human feedback received after the exact toy has been delivered.

    Reviews are deliberately separate from Playtest. Playtest is an AI-agent
    simulation inside the Make loop; a Review is a real customer's observation
    of a shipped product. It can guide a later revision, but it never rewrites
    the evidence or bytes of the product that customer received.
    """

    review_id: str
    product_artifact_sha256: str
    release_sha256: str
    delivery_tracking_id: str
    rating: int
    feedback: str
    observed_at: str

    def __post_init__(self) -> None:
        bounded_text(self.review_id, "CustomerReview review_id", 256)
        require_sha256(
            self.product_artifact_sha256,
            "CustomerReview product artifact sha256",
        )
        require_sha256(
            self.release_sha256,
            "CustomerReview release sha256",
        )
        bounded_text(
            self.delivery_tracking_id,
            "CustomerReview delivery_tracking_id",
            300,
        )
        if type(self.rating) is not int or not 1 <= self.rating <= 5:
            raise ContractError("CustomerReview rating must be an integer from 1 to 5")
        bounded_text(self.feedback, "CustomerReview feedback", 20_000)
        require_utc_timestamp(self.observed_at, "CustomerReview observed_at")

    def assert_delivery(self, delivered: Delivered) -> None:
        if not isinstance(delivered, Delivered):
            raise ContractError("CustomerReview requires a Delivered result")
        if (
            self.product_artifact_sha256 != delivered.product_artifact_sha256
            or self.release_sha256 != delivered.release_sha256
            or self.delivery_tracking_id != delivered.tracking_id
        ):
            raise ContractError(
                "CustomerReview belongs to a different product, Release, or delivery"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "review_id": self.review_id,
            "product_artifact_sha256": self.product_artifact_sha256,
            "release_sha256": self.release_sha256,
            "delivery_tracking_id": self.delivery_tracking_id,
            "rating": self.rating,
            "feedback": self.feedback,
            "observed_at": self.observed_at,
        }


__all__ = ["CustomerReview"]
