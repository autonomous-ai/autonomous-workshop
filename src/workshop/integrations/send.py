"""Workshop 0.3 Sender compatibility over the canonical Runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Optional, Union

from workshop.integrations.shop import (
    DEFAULT_SHOP_API,
    HttpResponse,
    ShopDoor,
    _ShopSender,
)
from workshop.errors import ContractError
from workshop.runtime import SendResult, Stamp, perform_effect, reconcile_effect
from workshop.artifacts import Artifact, inspect_artifact


class Sender(_ShopSender):
    """Compatibility facade; new code calls :class:`Runtime` directly."""

    def __init__(
        self,
        clockwork: Any,
        shop_door: Optional[ShopDoor] = None,
        owner_id: Optional[str] = None,
    ) -> None:
        if shop_door is None and owner_id is None:
            self.store = clockwork
            self.client = None
            self.owner_id = None
            return
        if shop_door is None or owner_id is None:
            raise ContractError(
                "Sender requires both ShopDoor and owner_id for shop sends"
            )
        super().__init__(clockwork, shop_door, owner_id)

    def send(
        self,
        product_id: str,
        packed: Union[Artifact, Path],
        door: Any,
        request: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> SendResult:
        """Compatibility spelling for ``Runtime.perform``."""

        return perform_effect(
            self.store, product_id, packed, door, request, lease_token
        )

    def reconcile(self, send_intent_id: str, door: Any) -> Optional[SendResult]:
        """Compatibility spelling for ``Runtime.reconcile``."""

        return reconcile_effect(self.store, send_intent_id, door)

    def send_draft(
        self,
        product_id: str,
        packed: Union[Artifact, Path],
        listing: Mapping[str, Any],
        lease_token: Optional[str] = None,
        *,
        inventor_name: Optional[str] = None,
    ) -> SendResult:
        if self.client is None or self.owner_id is None:
            raise ContractError("send_draft requires a configured ShopDoor")
        path = packed.path if isinstance(packed, Artifact) else Path(packed)
        inspected = inspect_artifact(path)
        outcome = self.import_draft(
            product_id,
            inspected.path,
            listing,
            lease_token,
            inventor_name=inventor_name,
        )
        return SendResult(outcome.intent_id, stamp=outcome.receipt)

    def send_live(
        self,
        send_intent_id: str,
        price_cents: int,
        lease_token: Optional[str] = None,
    ) -> Stamp:
        if self.client is None or self.owner_id is None:
            raise ContractError("send_live requires a configured ShopDoor")
        return self.publish_live(send_intent_id, price_cents, lease_token)


def inspect_legacy_packet(path: Path) -> Mapping[str, Any]:
    """Project canonical artifact inspection into the legacy packet shape."""

    packed = inspect_artifact(path)
    return {
        "bytes": packed.bytes,
        "entries": packed.entries,
        "packet_sha256": packed.pack_sha256,
        "artifact_sha256": packed.artifact_sha256,
    }
