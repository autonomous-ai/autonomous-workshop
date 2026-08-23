"""Durably send Packs through qualified external Doors."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Optional, Union

from .shop import (
    DEFAULT_SHOP_API,
    HttpResponse,
    ShopDoor,
    _ShopSender,
)
from .errors import AmbiguousSendError, ContractError, StateConflict
from .models import SendResult, Stamp
from .models import require_json_mapping
from .pack import PackedArtifact, inspect_pack


class Sender(_ShopSender):
    """Durable outbox and reconciliation for Packs crossing a Door."""

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
        packed: Union[PackedArtifact, Path],
        door: Any,
        request: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> SendResult:
        """Durably send one exact Pack through a generic or Delivery Door.

        Clockwork records and fences the effect before the Door executes. Any
        exception after execution begins leaves the intent ``unknown`` and a
        blind retry is refused until :meth:`reconcile` proves the outcome.
        """

        path = packed.path if isinstance(packed, PackedArtifact) else Path(packed)
        inspected = inspect_pack(path)
        require_json_mapping(request, "Send request")
        copied_request = json.loads(
            json.dumps(
                request,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
        )
        door_name = getattr(door, "name", None)
        if (
            not isinstance(door_name, str)
            or not door_name.strip()
            or any(ord(character) < 32 or ord(character) == 127 for character in door_name)
        ):
            raise ContractError("Send Door requires a bounded non-empty name")
        operation = getattr(door, "send", None)
        if not callable(operation):
            operation = getattr(door, "deliver", None)
        if not callable(operation):
            raise ContractError("Send Door must implement send() or deliver()")
        intent = self.store.prepare_send(
            product_id,
            inspected.pack_sha256,
            inspected.artifact_sha256,
            door_name,
            copied_request,
            lease_token,
        )
        if intent["state"] == "succeeded":
            return SendResult(intent["id"], stamp=Stamp.from_dict(intent["stamp"]))
        begun = self.store.begin_send(intent["id"], lease_token)
        effect_token = begun["effect_token"]
        try:
            stamp = operation(inspected, copied_request, effect_token)
            if not isinstance(stamp, Stamp):
                raise ContractError("Send Door must return a Stamp")
            stamp.assert_pack(inspected.pack_sha256)
            stamp.assert_artifact(inspected.artifact_sha256)
            if stamp.door != door_name:
                raise ContractError("Send Door returned a Stamp for a different Door")
        except Exception as exc:
            self._hold_unknown(intent["id"], effect_token, exc)
            raise AmbiguousSendError(
                "send outcome is unknown; reconcile intent %s before retry"
                % intent["id"]
            ) from exc
        try:
            completed = self.store.mark_send_succeeded(
                intent["id"], effect_token, stamp
            )
        except Exception as exc:
            self._hold_unknown(intent["id"], effect_token, exc)
            raise AmbiguousSendError(
                "send succeeded remotely but its durable outcome is unknown for intent %s"
                % intent["id"]
            ) from exc
        return SendResult(
            completed["id"], stamp=Stamp.from_dict(completed["stamp"])
        )

    def reconcile(self, send_intent_id: str, door: Any) -> Optional[SendResult]:
        """Resolve an unknown effect from Door-authenticated readback.

        A returned Stamp proves success. ``None`` is an explicit Door proof
        that no effect occurred and resets the intent to ``planned``; callers
        may then invoke :meth:`send` again.
        """

        intent = self.store.get_send_intent(send_intent_id)
        if intent["state"] == "succeeded":
            return SendResult(intent["id"], stamp=Stamp.from_dict(intent["stamp"]))
        if intent["state"] != "unknown":
            raise StateConflict(
                "send intent %s is %s, expected unknown"
                % (send_intent_id, intent["state"])
            )
        door_name = getattr(door, "name", None)
        if door_name != intent["door_name"]:
            raise ContractError("reconciliation Door does not match the send intent")
        operation = getattr(door, "reconcile", None)
        if not callable(operation):
            raise ContractError("Send Door must implement reconcile()")
        try:
            stamp = operation(dict(intent))
        except Exception as exc:
            raise AmbiguousSendError(
                "send intent %s remains unknown after reconciliation failed"
                % send_intent_id
            ) from exc
        if stamp is None:
            self.store.resolve_send_no_effect(send_intent_id)
            return None
        if not isinstance(stamp, Stamp):
            raise AmbiguousSendError(
                "send intent %s remains unknown: Door returned no valid proof"
                % send_intent_id
            )
        try:
            resolved = self.store.resolve_send_succeeded(send_intent_id, stamp)
        except Exception as exc:
            raise AmbiguousSendError(
                "send intent %s remains unknown: Stamp did not match"
                % send_intent_id
            ) from exc
        return SendResult(resolved["id"], stamp=Stamp.from_dict(resolved["stamp"]))

    def _hold_unknown(
        self, intent_id: str, effect_token: str, error: Exception
    ) -> None:
        summary = "%s: %s" % (type(error).__name__, error)
        summary = " ".join(summary.split())[:4000] or "unknown Door failure"
        try:
            self.store.mark_send_unknown(intent_id, effect_token, summary)
        except Exception:
            # The caller still receives an ambiguity error. A concurrent state
            # change or database failure must never license a blind retry.
            pass

    def send_draft(
        self,
        product_id: str,
        packed: Union[PackedArtifact, Path],
        listing: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> SendResult:
        if self.client is None or self.owner_id is None:
            raise ContractError("send_draft requires a configured ShopDoor")
        path = packed.path if isinstance(packed, PackedArtifact) else Path(packed)
        inspected = inspect_pack(path)
        outcome = self.import_draft(product_id, inspected.path, listing, lease_token)
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
    """Compatibility helper; canonical callers use :func:`inspect_pack`."""

    packed = inspect_pack(path)
    return {
        "bytes": packed.bytes,
        "entries": packed.entries,
        "packet_sha256": packed.pack_sha256,
        "artifact_sha256": packed.artifact_sha256,
    }
