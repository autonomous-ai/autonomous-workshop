"""Durable Workshop state and external-effect execution.

``Runtime`` is the one internal service an inventor needs.  It owns state,
leases, budgets, and a transactional outbox.  External services stay ordinary
adapters: the runtime records an intent before calling one, refuses blind
retries after an ambiguous outcome, and accepts success only with an
artifact-bound :class:`~inventor_workshop.models.Receipt`.

The current SQLite column names retain their pre-0.4 ``send``/``door``/``stamp``
spellings so existing inventor databases remain readable.  Those names are a
storage compatibility detail, not additional Workshop concepts.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Union

from .errors import AmbiguousSendError, ContractError, StateConflict
from .models import Receipt, SendResult, require_json_mapping
from .pack import Artifact, inspect_artifact
from .store import InventorStore


def _copy_request(request: Mapping[str, Any]) -> Dict[str, Any]:
    require_json_mapping(request, "adapter request")
    return json.loads(
        json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    )


def _adapter_name(adapter: Any) -> str:
    name = getattr(adapter, "name", None)
    if (
        not isinstance(name, str)
        or not name.strip()
        or len(name) > 256
        or any(ord(character) < 32 or ord(character) == 127 for character in name)
    ):
        raise ContractError("adapter requires a bounded non-empty name")
    return name


def _adapter_operation(adapter: Any) -> Callable[..., Any]:
    operation = getattr(adapter, "execute", None)
    if callable(operation):
        return operation
    # Compatibility for Workshop 0.3 Doors.  New adapters implement execute().
    operation = getattr(adapter, "send", None)
    if not callable(operation):
        operation = getattr(adapter, "deliver", None)
    if not callable(operation):
        raise ContractError("adapter must implement execute()")
    return operation


def _hold_unknown(
    store: InventorStore,
    intent_id: str,
    effect_token: str,
    error: Exception,
) -> None:
    summary = "%s: %s" % (type(error).__name__, error)
    summary = " ".join(summary.split())[:4000] or "unknown adapter failure"
    try:
        store.mark_send_unknown(intent_id, effect_token, summary)
    except Exception:
        # A concurrent state change or database failure must never license a
        # blind retry.  The caller still receives an ambiguity error.
        pass


def _perform(
    store: InventorStore,
    product_id: str,
    artifact: Union[Artifact, Path],
    adapter: Any,
    request: Mapping[str, Any],
    lease_token: Optional[str] = None,
) -> SendResult:
    """Compatibility-shaped result for one record-before-effect operation."""

    path = artifact.path if isinstance(artifact, Artifact) else Path(artifact)
    inspected = inspect_artifact(path)
    copied_request = _copy_request(request)
    name = _adapter_name(adapter)
    operation = _adapter_operation(adapter)
    intent = store.prepare_send(
        product_id,
        inspected.payload_sha256,
        inspected.artifact_sha256,
        name,
        copied_request,
        lease_token,
    )
    if intent["state"] == "succeeded":
        return SendResult(intent["id"], receipt=Receipt.from_dict(intent["stamp"]))
    begun = store.begin_send(intent["id"], lease_token)
    effect_token = begun["effect_token"]
    try:
        receipt = operation(inspected, copied_request, effect_token)
        if not isinstance(receipt, Receipt):
            raise ContractError("adapter must return a Receipt")
        receipt.assert_payload(inspected.payload_sha256)
        receipt.assert_artifact(inspected.artifact_sha256)
        if receipt.adapter != name:
            raise ContractError("adapter returned a Receipt for another adapter")
    except Exception as exc:
        _hold_unknown(store, intent["id"], effect_token, exc)
        raise AmbiguousSendError(
            "external effect outcome is unknown; reconcile intent %s before retry"
            % intent["id"]
        ) from exc
    try:
        completed = store.mark_send_succeeded(intent["id"], effect_token, receipt)
    except Exception as exc:
        _hold_unknown(store, intent["id"], effect_token, exc)
        raise AmbiguousSendError(
            "external effect completed but its durable outcome is unknown for intent %s"
            % intent["id"]
        ) from exc
    return SendResult(
        completed["id"], receipt=Receipt.from_dict(completed["stamp"])
    )


def _reconcile(
    store: InventorStore,
    intent_id: str,
    adapter: Any,
    *,
    canonical_intent: bool = False,
) -> Optional[SendResult]:
    intent = store.get_send_intent(intent_id)
    if intent["state"] == "succeeded":
        return SendResult(intent["id"], receipt=Receipt.from_dict(intent["stamp"]))
    if intent["state"] != "unknown":
        raise StateConflict(
            "effect intent %s is %s, expected unknown"
            % (intent_id, intent["state"])
        )
    if _adapter_name(adapter) != intent["door_name"]:
        raise ContractError("reconciliation adapter does not match the effect intent")
    operation = getattr(adapter, "reconcile", None)
    if not callable(operation):
        raise ContractError("adapter must implement reconcile()")
    try:
        receipt = operation(
            _canonical_effect(intent) if canonical_intent else dict(intent)
        )
    except Exception as exc:
        raise AmbiguousSendError(
            "effect intent %s remains unknown after reconciliation failed"
            % intent_id
        ) from exc
    if receipt is None:
        store.resolve_send_no_effect(intent_id)
        return None
    if not isinstance(receipt, Receipt):
        raise AmbiguousSendError(
            "effect intent %s remains unknown: adapter returned no valid proof"
            % intent_id
        )
    try:
        resolved = store.resolve_send_succeeded(intent_id, receipt)
    except Exception as exc:
        raise AmbiguousSendError(
            "effect intent %s remains unknown: Receipt did not match" % intent_id
        ) from exc
    return SendResult(resolved["id"], receipt=Receipt.from_dict(resolved["stamp"]))


def _canonical_effect(record: Mapping[str, Any]) -> Dict[str, Any]:
    """Present a legacy persisted row using the small runtime vocabulary."""

    raw_receipt = record.get("stamp")
    return {
        "id": record["id"],
        "product_id": record["product_id"],
        "payload_sha256": record["pack_sha256"],
        "artifact_sha256": record["artifact_sha256"],
        "adapter": record["door_name"],
        "state": record["state"],
        "request": record["request"],
        "effect_token": record.get("effect_token"),
        "receipt": (
            Receipt.from_dict(raw_receipt) if raw_receipt is not None else None
        ),
        "error": record.get("error"),
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
    }


class Runtime(InventorStore):
    """One inventor's durable state, budgets, leases, and external effects."""

    def perform(
        self,
        product_id: str,
        artifact: Union[Artifact, Path],
        adapter: Any,
        request: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> Receipt:
        """Perform one exact artifact effect and return authenticated proof."""

        return _perform(
            self, product_id, artifact, adapter, request, lease_token
        ).receipt

    def reconcile(self, intent_id: str, adapter: Any) -> Optional[Receipt]:
        """Resolve an ambiguous effect using adapter-authenticated readback."""

        result = _reconcile(self, intent_id, adapter, canonical_intent=True)
        return result.receipt if result is not None else None

    def effect(self, intent_id: str) -> Dict[str, Any]:
        """Read one effect record without exposing legacy storage names."""

        return _canonical_effect(self.get_send_intent(intent_id))

    def latest_effect(
        self, product_id: str, adapter: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Read the newest effect record for a product and optional adapter."""

        record = self.latest_send_intent(product_id, adapter)
        return _canonical_effect(record) if record is not None else None


__all__ = ["Runtime"]
