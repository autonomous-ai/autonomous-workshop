"""Exact-product production and carrier handoff for Deliver."""

from __future__ import annotations

from typing import Callable, Optional

from .errors import ContractError
from .jobs import DeliverContext, Delivered, Need, WaitingFor


class DefaultDeliver:
    """Validate one configured production-and-shipping implementation.

    A label alone is never a delivery receipt.  The configured implementation
    must bind printing, QA, packing, and USPS/UPS/FedEx evidence to the exact
    approved product and Docs hashes.
    """

    def __init__(
        self,
        fulfiller: Optional[Callable[[DeliverContext], Delivered]] = None,
    ) -> None:
        self.fulfiller = fulfiller

    def __call__(self, context: DeliverContext) -> Delivered:
        if not isinstance(context, DeliverContext):
            raise ContractError("DefaultDeliver requires a DeliverContext")
        context.assert_current()
        if self.fulfiller is None:
            raise WaitingFor(
                Need(
                    "deliver",
                    "production-and-shipping",
                    "The toy and its Docs are approved, but no real print/QA/packing/carrier implementation is configured.",
                    "Configure the shared production bench and USPS, UPS, or FedEx handoff; preserve receipts for the exact artifact hashes.",
                )
            )
        receipt = self.fulfiller(context)
        if not isinstance(receipt, Delivered):
            raise ContractError("Deliver fulfiller must return Delivered evidence")
        receipt.assert_context(context)
        return receipt


__all__ = ["DefaultDeliver"]
