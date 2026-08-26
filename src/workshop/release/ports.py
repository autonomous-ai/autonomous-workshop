"""Publication port declared by Release and implemented by integrations."""

from __future__ import annotations

from pathlib import Path
from typing import Mapping, Optional, Protocol

from workshop.runtime import PublicationOutcome, PublicationReceipt


class LaunchPort(Protocol):
    """Import, verify, and publish exact Release-owned product bytes."""

    def import_draft(
        self,
        product_id: str,
        packet: Path,
        metadata: Mapping[str, object],
        lease_token: Optional[str] = None,
        *,
        inventor_name: Optional[str] = None,
    ) -> PublicationOutcome:
        ...

    def reconcile_import(self, intent_id: str, remote_slug: str) -> PublicationReceipt:
        ...

    def publish_live(
        self,
        intent_id: str,
        price_cents: int,
        lease_token: Optional[str] = None,
    ) -> PublicationReceipt:
        ...

    def reconcile_live(self, intent_id: str) -> PublicationReceipt:
        ...


__all__ = ["LaunchPort"]
