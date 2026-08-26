"""Typed, content-bound evidence for the physical Deliver stage.

Deliver is an external boundary.  A truthy dictionary is not evidence that a
part was printed, inspected, packed, or accepted by a carrier.  These records
give every configured production adapter one exact envelope and bind the four
receipts into an ordered chain for the approved product and Release.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Dict, Mapping, Sequence, Tuple

from workshop.errors import ContractError
from workshop._validation import require_exact_version, require_sha256, require_utc_timestamp


DELIVERY_EVIDENCE_KIND = "workshop.delivery-evidence-receipt"
DELIVERY_EVIDENCE_STAGES = ("print", "qa", "packing", "carrier")
_CARRIERS = frozenset(("USPS", "UPS", "FedEx"))
_DELIVERY_STATUSES = frozenset(("handed-off", "delivered"))
_COMMON_FIELDS = frozenset(
    (
        "schema_version",
        "kind",
        "stage",
        "provider",
        "provider_version",
        "provider_config_sha256",
        "receipt_id",
        "product_artifact_sha256",
        "release_sha256",
        "observed_at",
        "details",
        "receipt_sha256",
    )
)
_DETAIL_FIELDS = {
    "print": frozenset(
        ("job_id", "status", "quantity", "material", "output_lot_id")
    ),
    "qa": frozenset(
        ("inspection_id", "status", "print_receipt_sha256", "checks")
    ),
    "packing": frozenset(
        (
            "package_id",
            "status",
            "print_receipt_sha256",
            "qa_receipt_sha256",
            "contents_count",
        )
    ),
    "carrier": frozenset(
        (
            "carrier",
            "service",
            "tracking_id",
            "status",
            "package_id",
            "packing_receipt_sha256",
            "acceptance_scan_id",
        )
    ),
}


def _text(value: Any, label: str, maximum: int = 2_000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded, single-line text" % label)
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
        raise ContractError("Deliver evidence must contain finite JSON") from exc


def _digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _instant(value: str) -> datetime:
    require_utc_timestamp(value, "Deliver evidence observed_at")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


def _detail_copy(value: Any, stage: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _DETAIL_FIELDS[stage]:
        raise ContractError("%s Deliver receipt details are malformed" % stage)
    try:
        copied = json.loads(_canonical_json(value).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:  # pragma: no cover
        raise ContractError("Deliver receipt details are malformed") from exc
    assert isinstance(copied, dict)
    return copied


@dataclass(frozen=True)
class DeliveryEvidenceReceipt:
    """One provider-attested physical event in the Deliver evidence chain."""

    stage: str
    provider: str
    provider_version: str
    provider_config_sha256: str
    receipt_id: str
    product_artifact_sha256: str
    release_sha256: str
    observed_at: str
    details: Mapping[str, Any]
    schema_version: int = 1
    kind: str = DELIVERY_EVIDENCE_KIND
    receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Deliver evidence schema_version must be 1")
        if self.kind != DELIVERY_EVIDENCE_KIND:
            raise ContractError("Deliver evidence kind is invalid")
        if self.stage not in DELIVERY_EVIDENCE_STAGES:
            raise ContractError("Deliver evidence stage is invalid")
        _text(self.provider, "Deliver evidence provider", 300)
        require_exact_version(
            self.provider_version, "Deliver evidence provider_version"
        )
        require_sha256(
            self.provider_config_sha256, "Deliver evidence provider config sha256"
        )
        _text(self.receipt_id, "Deliver evidence receipt_id", 512)
        require_sha256(
            self.product_artifact_sha256, "Deliver evidence product artifact sha256"
        )
        require_sha256(
            self.release_sha256, "Deliver evidence Release sha256"
        )
        require_utc_timestamp(self.observed_at, "Deliver evidence observed_at")
        details = _detail_copy(self.details, self.stage)
        self._validate_details(details)
        object.__setattr__(self, "details", details)
        object.__setattr__(self, "receipt_sha256", _digest(self._identity_dict()))

    def _validate_details(self, details: Mapping[str, Any]) -> None:
        if self.stage == "print":
            _text(details["job_id"], "print job_id", 512)
            if details["status"] != "completed":
                raise ContractError("print Deliver receipt status must be completed")
            if type(details["quantity"]) is not int or details["quantity"] < 1:
                raise ContractError("print Deliver receipt quantity must be positive")
            _text(details["material"], "print material", 300)
            _text(details["output_lot_id"], "print output_lot_id", 512)
        elif self.stage == "qa":
            _text(details["inspection_id"], "QA inspection_id", 512)
            if details["status"] != "passed":
                raise ContractError("QA Deliver receipt status must be passed")
            require_sha256(details["print_receipt_sha256"], "QA print receipt sha256")
            checks = details["checks"]
            if (
                not isinstance(checks, list)
                or not checks
                or len(checks) > 100
                or len(checks) != len(set(checks))
            ):
                raise ContractError("QA Deliver receipt requires unique passed checks")
            for check in checks:
                _text(check, "QA passed check", 300)
        elif self.stage == "packing":
            _text(details["package_id"], "packing package_id", 512)
            if details["status"] != "sealed":
                raise ContractError("packing Deliver receipt status must be sealed")
            require_sha256(
                details["print_receipt_sha256"], "packing print receipt sha256"
            )
            require_sha256(
                details["qa_receipt_sha256"], "packing QA receipt sha256"
            )
            if (
                type(details["contents_count"]) is not int
                or details["contents_count"] < 2
            ):
                raise ContractError(
                    "packing Deliver receipt must contain product and Release"
                )
        else:
            if details["carrier"] not in _CARRIERS:
                raise ContractError("carrier Deliver receipt uses an unsupported carrier")
            _text(details["service"], "carrier service", 200)
            _text(details["tracking_id"], "carrier tracking_id", 300)
            if details["status"] not in _DELIVERY_STATUSES:
                raise ContractError("carrier Deliver receipt status is not a handoff")
            _text(details["package_id"], "carrier package_id", 512)
            require_sha256(
                details["packing_receipt_sha256"],
                "carrier packing receipt sha256",
            )
            _text(details["acceptance_scan_id"], "carrier acceptance_scan_id", 512)

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "stage": self.stage,
            "provider": self.provider,
            "provider_version": self.provider_version,
            "provider_config_sha256": self.provider_config_sha256,
            "receipt_id": self.receipt_id,
            "product_artifact_sha256": self.product_artifact_sha256,
            "release_sha256": self.release_sha256,
            "observed_at": self.observed_at,
            "details": dict(self.details),
        }

    def to_dict(self) -> Dict[str, Any]:
        value = self._identity_dict()
        value["receipt_sha256"] = self.receipt_sha256
        return value

    @classmethod
    def from_dict(cls, value: Any) -> "DeliveryEvidenceReceipt":
        if not isinstance(value, Mapping) or set(value) != _COMMON_FIELDS:
            raise ContractError("Deliver evidence receipt envelope is malformed")
        receipt = cls(
            stage=value["stage"],
            provider=value["provider"],
            provider_version=value["provider_version"],
            provider_config_sha256=value["provider_config_sha256"],
            receipt_id=value["receipt_id"],
            product_artifact_sha256=value["product_artifact_sha256"],
            release_sha256=value["release_sha256"],
            observed_at=value["observed_at"],
            details=value["details"],
            schema_version=value["schema_version"],
            kind=value["kind"],
        )
        if value["receipt_sha256"] != receipt.receipt_sha256:
            raise ContractError("Deliver evidence receipt identity is inconsistent")
        return receipt


def validate_delivery_evidence_chain(
    evidence: Any,
    *,
    product_artifact_sha256: str,
    release_sha256: str,
    carrier: str,
    service: str,
    tracking_id: str,
    status: str,
    observed_at: str,
) -> Dict[str, Any]:
    """Parse and correlate all four physical receipts, returning canonical JSON."""

    names = (
        "print_receipt",
        "qa_receipt",
        "packing_receipt",
        "carrier_receipt",
    )
    if not isinstance(evidence, Mapping) or set(evidence) != set(names):
        raise ContractError("Delivered evidence requires exactly all four receipts")
    receipts = tuple(DeliveryEvidenceReceipt.from_dict(evidence[name]) for name in names)
    if tuple(item.stage for item in receipts) != DELIVERY_EVIDENCE_STAGES:
        raise ContractError("Delivered evidence receipts are in the wrong stages")
    for receipt in receipts:
        if (
            receipt.product_artifact_sha256 != product_artifact_sha256
            or receipt.release_sha256 != release_sha256
        ):
            raise ContractError(
                "Deliver evidence identifies different product or Release bytes"
            )
    if any(
        later < earlier
        for earlier, later in zip(
            (_instant(item.observed_at) for item in receipts),
            (_instant(item.observed_at) for item in receipts[1:]),
        )
    ):
        raise ContractError("Deliver evidence receipts are not chronological")
    printed, qa, packed, handed_off = receipts
    if qa.details["print_receipt_sha256"] != printed.receipt_sha256:
        raise ContractError("QA receipt is not bound to the exact print receipt")
    if (
        packed.details["print_receipt_sha256"] != printed.receipt_sha256
        or packed.details["qa_receipt_sha256"] != qa.receipt_sha256
    ):
        raise ContractError("packing receipt is not bound to exact print and QA")
    if (
        handed_off.details["packing_receipt_sha256"] != packed.receipt_sha256
        or handed_off.details["package_id"] != packed.details["package_id"]
    ):
        raise ContractError("carrier receipt is not bound to the exact sealed package")
    carrier_details = handed_off.details
    if (
        carrier_details["carrier"] != carrier
        or carrier_details["service"] != service
        or carrier_details["tracking_id"] != tracking_id
        or carrier_details["status"] != status
        or handed_off.observed_at != observed_at
    ):
        raise ContractError("carrier receipt differs from the Delivered record")
    return {name: receipt.to_dict() for name, receipt in zip(names, receipts)}


__all__ = [
    "DELIVERY_EVIDENCE_KIND",
    "DELIVERY_EVIDENCE_STAGES",
    "DeliveryEvidenceReceipt",
    "validate_delivery_evidence_chain",
]
