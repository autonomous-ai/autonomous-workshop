"""Inputs and carrier evidence owned by the Deliver stage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping

from workshop._validation import bounded_text, require_sha256, require_utc_timestamp
from workshop.deliver.evidence import validate_delivery_evidence_chain
from workshop.errors import ContractError
from workshop.instructions.contracts import ProductInstructions
from workshop.make.contracts import Made
from workshop.wish import Wish


_CARRIERS = frozenset(("USPS", "UPS", "FedEx"))
_DELIVERY_STATUSES = frozenset(("handed-off", "delivered"))


@dataclass(frozen=True)
class DeliverContext:
    wish: Wish
    made: Made
    instructions: ProductInstructions

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish):
            raise ContractError("DeliverContext requires a Wish")
        if not isinstance(self.made, Made) or not isinstance(
            self.instructions, ProductInstructions
        ):
            raise ContractError(
                "DeliverContext requires Made and ProductInstructions results"
            )
        if self.instructions.product_artifact_sha256 != self.made.artifact_sha256:
            raise ContractError("Deliver Instructions describe different artifact bytes")
        self.assert_current()

    def assert_current(self) -> None:
        """Recheck both exact inputs at every external Deliver boundary."""

        self.made.assert_current()
        self.instructions.assert_current()


@dataclass(frozen=True)
class Delivered:
    """Carrier evidence for the exact approved product and Instructions."""

    product_artifact_sha256: str
    instructions_sha256: str
    carrier: str
    service: str
    tracking_id: str
    status: str
    observed_at: str
    evidence: Mapping[str, Any]

    def __post_init__(self) -> None:
        require_sha256(self.product_artifact_sha256, "Delivered product artifact sha256")
        require_sha256(self.instructions_sha256, "Delivered instructions sha256")
        if self.carrier not in _CARRIERS:
            raise ContractError("Delivered carrier must be USPS, UPS, or FedEx")
        bounded_text(self.service, "Delivered service", 200)
        bounded_text(self.tracking_id, "Delivered tracking_id", 300)
        if self.status not in _DELIVERY_STATUSES:
            raise ContractError("Delivered status must be handed-off or delivered")
        require_utc_timestamp(self.observed_at, "Delivered observed_at")
        evidence = validate_delivery_evidence_chain(
            self.evidence,
            product_artifact_sha256=self.product_artifact_sha256,
            instructions_sha256=self.instructions_sha256,
            carrier=self.carrier,
            service=self.service,
            tracking_id=self.tracking_id,
            status=self.status,
            observed_at=self.observed_at,
        )
        object.__setattr__(self, "evidence", evidence)

    def assert_context(self, context: DeliverContext) -> None:
        if not isinstance(context, DeliverContext):
            raise ContractError("Delivered requires a DeliverContext")
        context.assert_current()
        if (
            self.product_artifact_sha256 != context.made.artifact_sha256
            or self.instructions_sha256 != context.instructions.instructions_sha256
        ):
            raise ContractError(
                "Delivered receipt identifies different product or Instructions bytes"
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "product_artifact_sha256": self.product_artifact_sha256,
            "instructions_sha256": self.instructions_sha256,
            "carrier": self.carrier,
            "service": self.service,
            "tracking_id": self.tracking_id,
            "status": self.status,
            "observed_at": self.observed_at,
            "evidence": dict(self.evidence),
        }


__all__ = ["DeliverContext", "Delivered"]
