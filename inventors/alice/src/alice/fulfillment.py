"""Fail-closed, deterministic boundaries for paid-order fulfillment.

This module deliberately performs no I/O.  It turns already-passed adapter
receipts into immutable values only after proving that every order names the
exact confirmed Vibe publication, production packet, SKU, and manufacturing
artifacts that may be printed.  The same immutable identity is then required
on print-job and QA/shipping receipts.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from .adapters import AdapterReceipt
from .store import PublicationRecord


VIBE_PUBLICATION_TARGET = "vibe_pipeline"
DELIVERY_ADAPTER = "delivery"
# Durable receipts written before the vocabulary migration retain this value.
LEGACY_FACTORY_ORDER_ADAPTER = "factory_order"
# Import compatibility for integrations that imported the old constant.
FACTORY_ORDER_ADAPTER = LEGACY_FACTORY_ORDER_ADAPTER
PRINT_FULFILLMENT_ADAPTER = "print_fulfillment"


class FulfillmentValidationError(ValueError):
    """Raised when an order or fulfillment receipt is not exactly bound."""


def canonical_sha256(value: Any) -> str:
    """Return Alice's canonical JSON digest, rejecting non-JSON values."""

    try:
        encoded = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise FulfillmentValidationError("value is not canonical JSON") from exc
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_manufacturing_spec_from_manifest(
    manifest: Mapping[str, Any],
) -> dict[str, Any]:
    """Construct the closed canonical recipe and its two derived digests.

    Stored digest fields are deliberately ignored by this construction helper.
    Call :func:`manufacturing_spec_from_manifest` to validate a persisted
    manifest. List order is canonicalized so equivalent recipes have one id.
    """

    root = _mapping(manifest, "production_manifest")
    manufacturing = _mapping(root.get("manufacturing"), "manufacturing")
    if manufacturing.get("process") != "3d_print":
        raise FulfillmentValidationError(
            "production manifest manufacturing.process must be '3d_print'"
        )
    print_profile_sha256 = _sha256(
        manufacturing.get("print_profile_sha256"),
        "manufacturing.print_profile_sha256",
    )
    raw_materials = manufacturing.get("materials")
    if not isinstance(raw_materials, list) or not raw_materials:
        raise FulfillmentValidationError(
            "manufacturing.materials must be a non-empty array"
        )
    materials = sorted({_text(value, "manufacturing.material") for value in raw_materials})
    if len(materials) != len(raw_materials):
        raise FulfillmentValidationError("manufacturing.materials must be unique")

    raw_bom = root.get("bom")
    if not isinstance(raw_bom, list) or not raw_bom:
        raise FulfillmentValidationError("production manifest bom must be non-empty")
    bom: list[dict[str, Any]] = []
    allowed_bom = {
        "part_id",
        "name",
        "quantity",
        "material",
        "manufacturing_method",
        "artifact_path",
    }
    for index, raw in enumerate(raw_bom):
        line = _mapping(raw, f"bom[{index}]")
        _require_closed_keys(line, allowed_bom, f"bom[{index}]")
        if set(line) != allowed_bom:
            raise FulfillmentValidationError(
                f"bom[{index}] must contain the complete manufacturing recipe"
            )
        material = _text(line.get("material"), f"bom[{index}].material")
        if material not in materials:
            raise FulfillmentValidationError(
                f"bom[{index}].material is not declared in manufacturing.materials"
            )
        method = _text(
            line.get("manufacturing_method"),
            f"bom[{index}].manufacturing_method",
        )
        if method != "3d_print":
            raise FulfillmentValidationError(
                f"bom[{index}].manufacturing_method must be '3d_print'"
            )
        bom.append(
            {
                "part_id": _text(line.get("part_id"), f"bom[{index}].part_id"),
                "name": _text(line.get("name"), f"bom[{index}].name"),
                "quantity": _positive_int(
                    line.get("quantity"), f"bom[{index}].quantity"
                ),
                "material": material,
                "manufacturing_method": method,
                "artifact_path": _text(
                    line.get("artifact_path"), f"bom[{index}].artifact_path"
                ),
            }
        )
    bom.sort(
        key=lambda item: (
            item["part_id"],
            item["artifact_path"],
            item["material"],
            item["manufacturing_method"],
            item["quantity"],
            item["name"],
        )
    )
    if len({line["part_id"] for line in bom}) != len(bom):
        raise FulfillmentValidationError("production manifest bom part_id values must be unique")
    bom_materials = {line["material"] for line in bom}
    if set(materials) != bom_materials:
        raise FulfillmentValidationError(
            "manufacturing.materials must exactly equal unique BOM materials"
        )

    vibe_design = manufacturing.get("vibe_design")
    if isinstance(vibe_design, Mapping):
        artifact_hashes = _artifact_hashes(vibe_design.get("artifact_hashes"), "vibe_design")
        bound_paths = {name for name, _ in artifact_hashes}
        missing_paths = sorted(
            line["artifact_path"] for line in bom if line["artifact_path"] not in bound_paths
        )
        if missing_paths:
            raise FulfillmentValidationError(
                "manufacturing BOM artifact_path is not bound by vibe_design: "
                + ", ".join(missing_paths)
            )

    packing = _mapping(manufacturing.get("packing"), "manufacturing.packing")
    _require_closed_keys(
        packing, {"format", "component_count"}, "manufacturing.packing"
    )
    if set(packing) != {"format", "component_count"}:
        raise FulfillmentValidationError(
            "manufacturing.packing must contain format and component_count"
        )
    packing_spec = {
        "format": _text(packing.get("format"), "manufacturing.packing.format"),
        "component_count": _positive_int(
            packing.get("component_count"),
            "manufacturing.packing.component_count",
        ),
    }
    if packing_spec["component_count"] != sum(line["quantity"] for line in bom):
        raise FulfillmentValidationError(
            "manufacturing.packing component_count must equal BOM quantity"
        )

    material_body = {
        "materials": materials,
        "bom": [
            {
                key: line[key]
                for key in (
                    "part_id",
                    "quantity",
                    "material",
                    "manufacturing_method",
                    "artifact_path",
                )
            }
            for line in bom
        ],
    }
    material_spec_sha256 = canonical_sha256(material_body)
    spec = {
        "process": "3d_print",
        "print_profile_sha256": print_profile_sha256,
        "material_spec_sha256": material_spec_sha256,
        "materials": materials,
        "bom": bom,
        "packing": packing_spec,
    }
    manufacturing_spec_sha256 = canonical_sha256(spec)
    return {**spec, "manufacturing_spec_sha256": manufacturing_spec_sha256}


def manufacturing_spec_from_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and return the immutable recipe stored in a release manifest."""

    spec = build_manufacturing_spec_from_manifest(manifest)
    manufacturing = _mapping(
        _mapping(manifest, "production_manifest").get("manufacturing"),
        "manufacturing",
    )
    for name in ("material_spec_sha256", "manufacturing_spec_sha256"):
        if manufacturing.get(name) != spec[name]:
            raise FulfillmentValidationError(
                f"manufacturing.{name} does not match canonical recipe"
            )
    return spec


def fulfillment_operation_key(order_id: str) -> str:
    """Return the one non-PII idempotency key used for an order's lifecycle."""

    _text(order_id, "order_id")
    return f"alice:fulfillment:v1:{hashlib.sha256(order_id.encode('utf-8')).hexdigest()}"


@dataclass(frozen=True, slots=True)
class PublicationBinding:
    publication_id: str
    publication_operation_key: str
    candidate_id: str
    candidate_version: int
    design_id: str
    slug: str
    history_id: str
    project_url: str
    packet_hash: str
    sku: str
    price_cents: int
    currency: str
    print_profile_sha256: str
    material_spec_sha256: str
    manufacturing_spec_sha256: str
    manufacturing_spec_json: str
    artifact_hashes: tuple[tuple[str, str], ...]

    @property
    def artifact_hash_map(self) -> dict[str, str]:
        return dict(self.artifact_hashes)

    @property
    def manufacturing_spec(self) -> dict[str, Any]:
        return json.loads(self.manufacturing_spec_json)

    def as_payload(self) -> dict[str, Any]:
        return {
            "publication_id": self.publication_id,
            "publication_operation_key": self.publication_operation_key,
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "design_id": self.design_id,
            "slug": self.slug,
            "history_id": self.history_id,
            "project_url": self.project_url,
            "packet_hash": self.packet_hash,
            "sku": self.sku,
            "price_cents": self.price_cents,
            "currency": self.currency,
            "print_profile_sha256": self.print_profile_sha256,
            "material_spec_sha256": self.material_spec_sha256,
            "manufacturing_spec_sha256": self.manufacturing_spec_sha256,
            "manufacturing_spec": self.manufacturing_spec,
            "artifact_hashes": self.artifact_hash_map,
        }


@dataclass(frozen=True, slots=True)
class FulfillmentIntent:
    order_id: str
    operation_key: str
    publication: PublicationBinding
    quantity: int
    shipping_reference: str
    source_order_sha256: str

    @property
    def intent_sha256(self) -> str:
        return canonical_sha256(self.as_payload(include_digest=False))

    def as_payload(self, *, include_digest: bool = True) -> dict[str, Any]:
        value = {
            "schema_version": 1,
            "order_id": self.order_id,
            "operation_key": self.operation_key,
            "publication": self.publication.as_payload(),
            "quantity": self.quantity,
            "shipping_reference": self.shipping_reference,
            "source_order_sha256": self.source_order_sha256,
        }
        if include_digest:
            value["intent_sha256"] = self.intent_sha256
        return value


@dataclass(frozen=True, slots=True)
class PrintJobReceipt:
    order_id: str
    operation_key: str
    intent_sha256: str
    packet_hash: str
    sku: str
    quantity: int
    job_id: str
    print_profile_sha256: str
    material_spec_sha256: str
    manufacturing_spec_sha256: str
    manufacturing_spec_json: str
    artifact_hashes: tuple[tuple[str, str], ...]
    receipt_sha256: str

    @property
    def artifact_hash_map(self) -> dict[str, str]:
        return dict(self.artifact_hashes)

    @property
    def manufacturing_spec(self) -> dict[str, Any]:
        return json.loads(self.manufacturing_spec_json)

    def as_payload(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "operation_key": self.operation_key,
            "intent_sha256": self.intent_sha256,
            "packet_hash": self.packet_hash,
            "sku": self.sku,
            "quantity": self.quantity,
            "job_id": self.job_id,
            "print_profile_sha256": self.print_profile_sha256,
            "material_spec_sha256": self.material_spec_sha256,
            "manufacturing_spec_sha256": self.manufacturing_spec_sha256,
            "manufacturing_spec": self.manufacturing_spec,
            "artifact_hashes": self.artifact_hash_map,
            "receipt_sha256": self.receipt_sha256,
        }


@dataclass(frozen=True, slots=True)
class ShipmentReceipt:
    order_id: str
    operation_key: str
    intent_sha256: str
    packet_hash: str
    sku: str
    quantity: int
    job_id: str
    print_receipt_sha256: str
    print_profile_sha256: str
    material_spec_sha256: str
    manufacturing_spec_sha256: str
    manufacturing_spec_json: str
    artifact_hashes: tuple[tuple[str, str], ...]
    carrier: str
    tracking_number: str
    tracking_url: str
    qa_authority: str
    qa_run_id: str
    qa_protocol_id: str
    qa_result: str
    defect_evidence_sha256: str
    qa_receipt_sha256: str
    receipt_sha256: str

    @property
    def artifact_hash_map(self) -> dict[str, str]:
        return dict(self.artifact_hashes)

    @property
    def manufacturing_spec(self) -> dict[str, Any]:
        return json.loads(self.manufacturing_spec_json)

    def as_payload(self) -> dict[str, Any]:
        return {
            "order_id": self.order_id,
            "operation_key": self.operation_key,
            "intent_sha256": self.intent_sha256,
            "packet_hash": self.packet_hash,
            "sku": self.sku,
            "quantity": self.quantity,
            "job_id": self.job_id,
            "print_receipt_sha256": self.print_receipt_sha256,
            "print_profile_sha256": self.print_profile_sha256,
            "material_spec_sha256": self.material_spec_sha256,
            "manufacturing_spec_sha256": self.manufacturing_spec_sha256,
            "manufacturing_spec": self.manufacturing_spec,
            "artifact_hashes": self.artifact_hash_map,
            "qa_passed": True,
            "qa": {
                "receipt_source": "authenticated_external_qa_readback",
                "authority": self.qa_authority,
                "run_id": self.qa_run_id,
                "protocol_id": self.qa_protocol_id,
                "result": self.qa_result,
                "defect_evidence_sha256": self.defect_evidence_sha256,
                "order_id": self.order_id,
                "operation_key": self.operation_key,
                "intent_sha256": self.intent_sha256,
                "packet_hash": self.packet_hash,
                "sku": self.sku,
                "quantity": self.quantity,
                "job_id": self.job_id,
                "print_receipt_sha256": self.print_receipt_sha256,
                "print_profile_sha256": self.print_profile_sha256,
                "material_spec_sha256": self.material_spec_sha256,
                "manufacturing_spec_sha256": self.manufacturing_spec_sha256,
                "manufacturing_spec": self.manufacturing_spec,
                "artifact_hashes": self.artifact_hash_map,
                "receipt_sha256": self.qa_receipt_sha256,
            },
            "status": "shipped",
            "tracking": {
                "carrier": self.carrier,
                "tracking_number": self.tracking_number,
                "tracking_url": self.tracking_url,
            },
            "receipt_sha256": self.receipt_sha256,
        }


def fulfillment_intent_from_payload(value: Mapping[str, Any]) -> FulfillmentIntent:
    """Rehydrate and verify an immutable intent stored in a task payload."""

    raw = _mapping(value, "fulfillment_intent")
    publication = _mapping(raw.get("publication"), "fulfillment_intent.publication")
    manufacturing_spec, manufacturing_spec_json = _manufacturing_spec_payload(
        publication.get("manufacturing_spec"), "fulfillment_intent.publication"
    )
    binding = PublicationBinding(
        publication_id=_text(publication.get("publication_id"), "publication_id"),
        publication_operation_key=_text(
            publication.get("publication_operation_key"),
            "publication_operation_key",
        ),
        candidate_id=_text(publication.get("candidate_id"), "candidate_id"),
        candidate_version=_positive_int(
            publication.get("candidate_version"), "candidate_version"
        ),
        design_id=_text(publication.get("design_id"), "design_id"),
        slug=_text(publication.get("slug"), "slug"),
        history_id=_text(publication.get("history_id"), "history_id"),
        project_url=_url(publication.get("project_url"), "project_url"),
        packet_hash=_sha256(publication.get("packet_hash"), "packet_hash"),
        sku=_sku(publication.get("sku"), "sku"),
        price_cents=_positive_int(publication.get("price_cents"), "price_cents"),
        currency=_currency(publication.get("currency"), "currency"),
        print_profile_sha256=_sha256(
            publication.get("print_profile_sha256"), "print_profile_sha256"
        ),
        material_spec_sha256=_sha256(
            publication.get("material_spec_sha256"), "material_spec_sha256"
        ),
        manufacturing_spec_sha256=_sha256(
            publication.get("manufacturing_spec_sha256"),
            "manufacturing_spec_sha256",
        ),
        manufacturing_spec_json=manufacturing_spec_json,
        artifact_hashes=_artifact_hashes(
            publication.get("artifact_hashes"), "publication"
        ),
    )
    if binding.currency != "USD":
        raise FulfillmentValidationError(
            "fulfillment intent publication currency must be USD"
        )
    for name in (
        "print_profile_sha256",
        "material_spec_sha256",
        "manufacturing_spec_sha256",
    ):
        if getattr(binding, name) != manufacturing_spec.get(name):
            raise FulfillmentValidationError(
                f"fulfillment intent publication {name} mismatch"
            )
    intent = FulfillmentIntent(
        order_id=_text(raw.get("order_id"), "order_id"),
        operation_key=_text(raw.get("operation_key"), "operation_key"),
        publication=binding,
        quantity=_positive_int(raw.get("quantity"), "quantity"),
        shipping_reference=_text(
            raw.get("shipping_reference"), "shipping_reference"
        ),
        source_order_sha256=_sha256(
            raw.get("source_order_sha256"), "source_order_sha256"
        ),
    )
    if intent.operation_key != fulfillment_operation_key(intent.order_id):
        raise FulfillmentValidationError("fulfillment operation_key mismatch")
    if raw.get("intent_sha256") != intent.intent_sha256:
        raise FulfillmentValidationError("fulfillment intent_sha256 mismatch")
    return intent


def print_job_receipt_from_payload(value: Mapping[str, Any]) -> PrintJobReceipt:
    """Rehydrate a previously validated immutable print-job receipt."""

    raw = _mapping(value, "print_job_receipt")
    manufacturing_spec, manufacturing_spec_json = _manufacturing_spec_payload(
        raw.get("manufacturing_spec"), "print_job_receipt"
    )
    receipt = PrintJobReceipt(
        order_id=_text(raw.get("order_id"), "order_id"),
        operation_key=_text(raw.get("operation_key"), "operation_key"),
        intent_sha256=_sha256(raw.get("intent_sha256"), "intent_sha256"),
        packet_hash=_sha256(raw.get("packet_hash"), "packet_hash"),
        sku=_sku(raw.get("sku"), "sku"),
        quantity=_positive_int(raw.get("quantity"), "quantity"),
        job_id=_text(raw.get("job_id"), "job_id"),
        print_profile_sha256=_sha256(
            raw.get("print_profile_sha256"), "print_profile_sha256"
        ),
        material_spec_sha256=_sha256(
            raw.get("material_spec_sha256"), "material_spec_sha256"
        ),
        manufacturing_spec_sha256=_sha256(
            raw.get("manufacturing_spec_sha256"), "manufacturing_spec_sha256"
        ),
        manufacturing_spec_json=manufacturing_spec_json,
        artifact_hashes=_artifact_hashes(raw.get("artifact_hashes"), "print_job"),
        receipt_sha256=_sha256(raw.get("receipt_sha256"), "receipt_sha256"),
    )
    for name in (
        "print_profile_sha256",
        "material_spec_sha256",
        "manufacturing_spec_sha256",
    ):
        if getattr(receipt, name) != manufacturing_spec.get(name):
            raise FulfillmentValidationError(f"print-job {name} mismatch")
    _require_spec_artifact_paths(
        manufacturing_spec, receipt.artifact_hashes, "print-job receipt"
    )
    material = {
        "status": "created",
        **{
            key: item
            for key, item in receipt.as_payload().items()
            if key != "receipt_sha256"
        },
    }
    if canonical_sha256(material) != receipt.receipt_sha256:
        raise FulfillmentValidationError("print-job receipt_sha256 mismatch")
    return receipt


def confirmed_publication_binding(record: PublicationRecord) -> PublicationBinding:
    """Prove a store publication is the exact complete Vibe release to fulfill."""

    if not isinstance(record, PublicationRecord):
        raise FulfillmentValidationError("publication must be a PublicationRecord")
    if record.target != VIBE_PUBLICATION_TARGET:
        raise FulfillmentValidationError("publication is not a Vibe publication")
    if record.state != "confirmed" or record.status != "published":
        raise FulfillmentValidationError("publication is not confirmed and published")
    for name in (
        "id",
        "idempotency_key",
        "candidate_id",
        "remote_design_id",
        "slug",
        "history_id",
        "project_url",
    ):
        _text(getattr(record, name), f"publication.{name}")
    assert record.candidate_id is not None
    assert record.remote_design_id is not None
    assert record.slug is not None
    assert record.history_id is not None
    assert record.project_url is not None
    _url(record.project_url, "publication.project_url")

    request = _mapping(record.request, "publication.request")
    if canonical_sha256(request) != _sha256(
        record.request_sha256, "publication.request_sha256"
    ):
        raise FulfillmentValidationError("publication request hash mismatch")
    if request.get("operation_key") != record.idempotency_key:
        raise FulfillmentValidationError("publication operation key mismatch")
    if request.get("candidate_id") != record.candidate_id:
        raise FulfillmentValidationError("publication candidate_id mismatch")
    candidate_version = _positive_int(
        request.get("candidate_version"), "publication candidate_version"
    )

    packet_hash = _sha256(request.get("packet_hash"), "publication packet_hash")
    if _sha256(
        request.get("production_packet_hash"), "production_packet_hash"
    ) != packet_hash or _sha256(
        request.get("reviewed_packet_hash"), "reviewed_packet_hash"
    ) != packet_hash:
        raise FulfillmentValidationError("publication packet hashes disagree")
    manifest = _mapping(
        request.get("production_manifest"), "publication production_manifest"
    )
    if canonical_sha256(manifest) != packet_hash:
        raise FulfillmentValidationError("publication manifest does not match packet_hash")
    if manifest.get("candidate_id") != record.candidate_id:
        raise FulfillmentValidationError("production manifest candidate_id mismatch")

    release = _mapping(request.get("release_decision"), "release_decision")
    if release.get("allowed") is not True or release.get("effect_mode") != "live":
        raise FulfillmentValidationError("publication release was not allowed in live mode")
    for name in ("production_packet_hash", "reviewed_packet_hash"):
        if _sha256(release.get(name), f"release_decision.{name}") != packet_hash:
            raise FulfillmentValidationError(f"release decision {name} mismatch")

    existing = _mapping(request.get("existing_design"), "existing_design")
    manufacturing = _mapping(manifest.get("manufacturing"), "manufacturing")
    manufacturing_spec = manufacturing_spec_from_manifest(manifest)
    manufacturing_spec_json = json.dumps(
        manufacturing_spec,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    manifest_design = _mapping(
        manufacturing.get("vibe_design"), "manufacturing.vibe_design"
    )
    for name, expected in (
        ("design_id", record.remote_design_id),
        ("slug", record.slug),
        ("history_id", record.history_id),
        ("project_url", record.project_url),
    ):
        if existing.get(name) != expected or manifest_design.get(name) != expected:
            raise FulfillmentValidationError(f"publication {name} binding mismatch")
    artifacts = _artifact_hashes(existing.get("artifact_hashes"), "existing_design")
    if _artifact_hashes(
        manifest_design.get("artifact_hashes"), "manufacturing.vibe_design"
    ) != artifacts:
        raise FulfillmentValidationError("publication artifact hashes disagree")

    response = _mapping(record.response, "publication.response")
    if response.get("stage") != "complete":
        raise FulfillmentValidationError("publication response is not complete")
    for name, expected in (
        ("operation_key", record.idempotency_key),
        ("candidate_id", record.candidate_id),
        ("packet_hash", packet_hash),
    ):
        if response.get(name) != expected:
            raise FulfillmentValidationError(f"publication response {name} mismatch")

    sku = _publication_sku(manifest, request, response)
    price_cents, currency = _publication_price(manifest, request, response)
    return PublicationBinding(
        publication_id=record.id,
        publication_operation_key=record.idempotency_key,
        candidate_id=record.candidate_id,
        candidate_version=candidate_version,
        design_id=record.remote_design_id,
        slug=record.slug,
        history_id=record.history_id,
        project_url=record.project_url,
        packet_hash=packet_hash,
        sku=sku,
        price_cents=price_cents,
        currency=currency,
        print_profile_sha256=manufacturing_spec["print_profile_sha256"],
        material_spec_sha256=manufacturing_spec["material_spec_sha256"],
        manufacturing_spec_sha256=manufacturing_spec[
            "manufacturing_spec_sha256"
        ],
        manufacturing_spec_json=manufacturing_spec_json,
        artifact_hashes=artifacts,
    )


def build_fulfillment_intents(
    delivery_result: AdapterReceipt | Mapping[str, Any],
    publications: Iterable[PublicationRecord],
) -> tuple[FulfillmentIntent, ...]:
    """Convert a passed Delivery result into one intent per paid order."""

    payload = _passed_adapter_payload(
        delivery_result,
        adapter=DELIVERY_ADAPTER,
        legacy_adapters=(LEGACY_FACTORY_ORDER_ADAPTER,),
        evidence_class="market",
    )
    orders_value = payload.get("orders")
    _require_closed_keys(payload, {"orders"}, "Delivery payload")
    if not isinstance(orders_value, list) or any(
        not isinstance(item, Mapping) for item in orders_value
    ):
        raise FulfillmentValidationError("orders must be an array of objects")
    if not orders_value:
        return ()
    orders = list(orders_value)
    publication_index = _publication_index(publications)
    normalized_by_order: dict[str, dict[str, Any]] = {}
    intents_by_order: dict[str, FulfillmentIntent] = {}
    for raw in orders:
        normalized = _normalize_paid_order(raw)
        order_id = normalized["order_id"]
        prior = normalized_by_order.get(order_id)
        if prior is not None:
            if prior != normalized:
                raise FulfillmentValidationError(
                    f"order {order_id!r} is duplicated with conflicting content"
                )
            continue
        normalized_by_order[order_id] = normalized

        publication_id = normalized["publication_id"]
        record = publication_index.get(publication_id)
        if record is None:
            raise FulfillmentValidationError(
                f"order {order_id!r} names an unknown publication"
            )
        binding = confirmed_publication_binding(record)
        if normalized["packet_hash"] != binding.packet_hash:
            raise FulfillmentValidationError(
                f"order {order_id!r} packet_hash does not match its publication"
            )
        if normalized["sku"] != binding.sku:
            raise FulfillmentValidationError(
                f"order {order_id!r} SKU does not match its publication"
            )
        if normalized["currency"] != "USD":
            raise FulfillmentValidationError(
                f"order {order_id!r} currency must be USD"
            )
        if normalized["currency"] != binding.currency:
            raise FulfillmentValidationError(
                f"order {order_id!r} currency does not match its publication"
            )
        if normalized["unit_price_cents"] != binding.price_cents:
            raise FulfillmentValidationError(
                f"order {order_id!r} unit price does not match its publication"
            )
        expected_subtotal = binding.price_cents * normalized["quantity"]
        if normalized["product_subtotal_cents"] != expected_subtotal:
            raise FulfillmentValidationError(
                f"order {order_id!r} product subtotal does not equal unit price "
                "times quantity"
            )
        if normalized["amount_paid_cents"] < expected_subtotal:
            raise FulfillmentValidationError(
                f"order {order_id!r} amount paid is below its product subtotal"
            )
        for name, expected in (
            ("candidate_id", binding.candidate_id),
            ("design_id", binding.design_id),
            ("history_id", binding.history_id),
        ):
            value = normalized.get(name)
            if value is not None and value != expected:
                raise FulfillmentValidationError(
                    f"order {order_id!r} optional {name} binding mismatches"
                )
        intents_by_order[order_id] = FulfillmentIntent(
            order_id=order_id,
            operation_key=fulfillment_operation_key(order_id),
            publication=binding,
            quantity=normalized["quantity"],
            shipping_reference=normalized["shipping_reference"],
            source_order_sha256=canonical_sha256(normalized),
        )
    return tuple(intents_by_order[key] for key in sorted(intents_by_order))


def validate_print_job_receipts(
    intents: Sequence[FulfillmentIntent],
    print_result: AdapterReceipt | Mapping[str, Any],
) -> tuple[PrintJobReceipt, ...]:
    """Validate a passed print adapter's complete receipt set."""

    intent_index = _intent_index(intents)
    payload = _passed_adapter_payload(
        print_result,
        adapter=PRINT_FULFILLMENT_ADAPTER,
        evidence_class="manufacturing",
    )
    raw_receipts = _nonempty_object_list(payload.get("print_jobs"), "print_jobs")
    _require_closed_keys(payload, {"print_jobs"}, "print-fulfillment payload")
    receipts: dict[str, PrintJobReceipt] = {}
    normalized: dict[str, Mapping[str, Any]] = {}
    used_job_ids: dict[str, str] = {}
    for raw in raw_receipts:
        order_id = _text(raw.get("order_id"), "print_job.order_id")
        prior = normalized.get(order_id)
        if prior is not None:
            if prior != raw:
                raise FulfillmentValidationError(
                    f"print receipt for {order_id!r} conflicts with its duplicate"
                )
            continue
        normalized[order_id] = dict(raw)
        intent = intent_index.get(order_id)
        if intent is None:
            raise FulfillmentValidationError(
                f"print receipt names unexpected order {order_id!r}"
            )
        receipt = _validate_print_job(intent, raw)
        other = used_job_ids.get(receipt.job_id)
        if other is not None and other != order_id:
            raise FulfillmentValidationError("a print job_id is shared by multiple orders")
        used_job_ids[receipt.job_id] = order_id
        receipts[order_id] = receipt
    _require_exact_orders(intent_index, receipts, "print receipts")
    return tuple(receipts[key] for key in sorted(receipts))


def validate_qa_ship_receipts(
    intents: Sequence[FulfillmentIntent],
    print_receipts: Sequence[PrintJobReceipt],
    shipment_result: AdapterReceipt | Mapping[str, Any],
) -> tuple[ShipmentReceipt, ...]:
    """Validate passed QA/ship receipts against intents and print receipts."""

    intent_index = _intent_index(intents)
    print_index = _print_receipt_index(print_receipts)
    _require_exact_orders(intent_index, print_index, "print receipts")
    payload = _passed_adapter_payload(
        shipment_result,
        adapter=PRINT_FULFILLMENT_ADAPTER,
        evidence_class="manufacturing",
    )
    raw_receipts = _nonempty_object_list(payload.get("shipments"), "shipments")
    _require_closed_keys(payload, {"shipments"}, "shipment payload")
    receipts: dict[str, ShipmentReceipt] = {}
    normalized: dict[str, Mapping[str, Any]] = {}
    for raw in raw_receipts:
        order_id = _text(raw.get("order_id"), "shipment.order_id")
        prior = normalized.get(order_id)
        if prior is not None:
            if prior != raw:
                raise FulfillmentValidationError(
                    f"shipment for {order_id!r} conflicts with its duplicate"
                )
            continue
        normalized[order_id] = dict(raw)
        intent = intent_index.get(order_id)
        if intent is None:
            raise FulfillmentValidationError(
                f"shipment names unexpected order {order_id!r}"
            )
        receipts[order_id] = _validate_shipment(
            intent, print_index[order_id], raw
        )
    _require_exact_orders(intent_index, receipts, "shipment receipts")
    return tuple(receipts[key] for key in sorted(receipts))


def _passed_adapter_payload(
    value: AdapterReceipt | Mapping[str, Any],
    *,
    adapter: str,
    legacy_adapters: tuple[str, ...] = (),
    evidence_class: str,
) -> Mapping[str, Any]:
    if isinstance(value, AdapterReceipt):
        receipt: Mapping[str, Any] = {
            "adapter": value.adapter,
            "run_id": value.run_id,
            "status": value.status,
            "evidence_class": value.evidence_class,
            "payload": value.payload,
            "input_sha256": value.input_sha256,
        }
    elif isinstance(value, Mapping):
        if "executor" in value:
            if value.get("executor") != "adapter":
                raise FulfillmentValidationError("fulfillment result is not adapter-backed")
            receipt_value = value.get("receipt")
            receipt = _mapping(receipt_value, "adapter receipt")
        else:
            receipt = value
    else:
        raise FulfillmentValidationError("adapter result must be an adapter receipt")
    if receipt.get("adapter") not in {adapter, *legacy_adapters}:
        raise FulfillmentValidationError(f"expected passed {adapter!r} adapter receipt")
    if receipt.get("status") != "passed":
        raise FulfillmentValidationError("adapter receipt status is not passed")
    if receipt.get("evidence_class") != evidence_class:
        raise FulfillmentValidationError(
            f"adapter receipt evidence class is not {evidence_class!r}"
        )
    _text(receipt.get("run_id"), "adapter receipt run_id")
    _sha256(receipt.get("input_sha256"), "adapter receipt input_sha256")
    return _mapping(receipt.get("payload"), "adapter receipt payload")


def _publication_index(
    publications: Iterable[PublicationRecord],
) -> dict[str, PublicationRecord]:
    result: dict[str, PublicationRecord] = {}
    try:
        values = list(publications)
    except TypeError as exc:
        raise FulfillmentValidationError("publications must be iterable") from exc
    for record in values:
        if not isinstance(record, PublicationRecord):
            raise FulfillmentValidationError("publications contain a non-record value")
        existing = result.get(record.id)
        if existing is not None and existing != record:
            raise FulfillmentValidationError(
                f"publication {record.id!r} has conflicting duplicate records"
            )
        result[record.id] = record
    return result


def _normalize_paid_order(raw: Mapping[str, Any]) -> dict[str, Any]:
    _require_closed_keys(
        raw,
        {
            "order_id",
            "payment_status",
            "publication_id",
            "packet_hash",
            "sku",
            "quantity",
            "currency",
            "unit_price_cents",
            "product_subtotal_cents",
            "amount_paid_cents",
            "shipping_reference",
            "candidate_id",
            "design_id",
            "history_id",
        },
        "paid order",
    )
    order_id = _text(raw.get("order_id"), "order.order_id")
    if raw.get("payment_status") != "paid":
        raise FulfillmentValidationError(f"order {order_id!r} is not paid")
    result = {
        "order_id": order_id,
        "payment_status": "paid",
        "publication_id": _text(raw.get("publication_id"), "order.publication_id"),
        "packet_hash": _sha256(raw.get("packet_hash"), "order.packet_hash"),
        "sku": _sku(raw.get("sku"), "order.sku"),
        "quantity": _positive_int(raw.get("quantity"), "order.quantity"),
        "currency": _currency(raw.get("currency"), "order.currency"),
        "unit_price_cents": _positive_int(
            raw.get("unit_price_cents"), "order.unit_price_cents"
        ),
        "product_subtotal_cents": _positive_int(
            raw.get("product_subtotal_cents"), "order.product_subtotal_cents"
        ),
        "amount_paid_cents": _positive_int(
            raw.get("amount_paid_cents"), "order.amount_paid_cents"
        ),
        "shipping_reference": _text(
            raw.get("shipping_reference"), "order.shipping_reference"
        ),
    }
    # Optional redundant identities become part of the immutable order digest
    # when supplied.  This also makes a replay that changes one of them a hard
    # duplicate conflict instead of silently discarding the altered value.
    for name in ("candidate_id", "design_id", "history_id"):
        if name in raw:
            result[name] = _text(raw.get(name), f"order.{name}")
    return result


def _validate_print_job(
    intent: FulfillmentIntent, raw: Mapping[str, Any]
) -> PrintJobReceipt:
    _require_closed_keys(
        raw,
        {
            "status",
            "order_id",
            "operation_key",
            "intent_sha256",
            "packet_hash",
            "sku",
            "quantity",
            "job_id",
            "print_profile_sha256",
            "material_spec_sha256",
            "manufacturing_spec_sha256",
            "manufacturing_spec",
            "artifact_hashes",
        },
        "print job",
    )
    if raw.get("status") != "created":
        raise FulfillmentValidationError("print job status must be 'created'")
    _require_intent_binding(intent, raw, "print job")
    job_id = _text(raw.get("job_id"), "print_job.job_id")
    artifacts = _artifact_hashes(raw.get("artifact_hashes"), "print_job")
    if artifacts != intent.publication.artifact_hashes:
        raise FulfillmentValidationError("print job artifact hashes mismatch")
    manufacturing_spec, manufacturing_spec_json = _manufacturing_spec_payload(
        raw.get("manufacturing_spec"), "print_job"
    )
    if manufacturing_spec != intent.publication.manufacturing_spec:
        raise FulfillmentValidationError("print job manufacturing_spec mismatch")
    _require_spec_artifact_paths(manufacturing_spec, artifacts, "print job")
    receipt_body = dict(raw)
    return PrintJobReceipt(
        order_id=intent.order_id,
        operation_key=intent.operation_key,
        intent_sha256=intent.intent_sha256,
        packet_hash=intent.publication.packet_hash,
        sku=intent.publication.sku,
        quantity=intent.quantity,
        job_id=job_id,
        print_profile_sha256=intent.publication.print_profile_sha256,
        material_spec_sha256=intent.publication.material_spec_sha256,
        manufacturing_spec_sha256=intent.publication.manufacturing_spec_sha256,
        manufacturing_spec_json=manufacturing_spec_json,
        artifact_hashes=artifacts,
        receipt_sha256=canonical_sha256(receipt_body),
    )


def _validate_shipment(
    intent: FulfillmentIntent,
    print_receipt: PrintJobReceipt,
    raw: Mapping[str, Any],
) -> ShipmentReceipt:
    _require_closed_keys(
        raw,
        {
            "status",
            "qa_passed",
            "order_id",
            "operation_key",
            "intent_sha256",
            "packet_hash",
            "sku",
            "quantity",
            "job_id",
            "print_receipt_sha256",
            "print_profile_sha256",
            "material_spec_sha256",
            "manufacturing_spec_sha256",
            "manufacturing_spec",
            "artifact_hashes",
            "qa",
            "tracking",
        },
        "shipment",
    )
    if raw.get("status") != "shipped":
        raise FulfillmentValidationError("shipment status must be 'shipped'")
    if raw.get("qa_passed") is not True:
        raise FulfillmentValidationError("shipment requires qa_passed=true")
    _require_intent_binding(intent, raw, "shipment")
    if raw.get("job_id") != print_receipt.job_id:
        raise FulfillmentValidationError("shipment print job_id mismatch")
    if raw.get("print_receipt_sha256") != print_receipt.receipt_sha256:
        raise FulfillmentValidationError("shipment print receipt hash mismatch")
    manufacturing_spec, manufacturing_spec_json = _manufacturing_spec_payload(
        raw.get("manufacturing_spec"), "shipment"
    )
    if (
        manufacturing_spec != intent.publication.manufacturing_spec
        or manufacturing_spec != print_receipt.manufacturing_spec
    ):
        raise FulfillmentValidationError("shipment manufacturing_spec mismatch")
    artifacts = _artifact_hashes(raw.get("artifact_hashes"), "shipment")
    if (
        artifacts != intent.publication.artifact_hashes
        or artifacts != print_receipt.artifact_hashes
    ):
        raise FulfillmentValidationError("shipment artifact hashes mismatch")
    _require_spec_artifact_paths(manufacturing_spec, artifacts, "shipment")
    qa = _validate_qa_receipt(intent, print_receipt, raw.get("qa"))
    tracking = _mapping(raw.get("tracking"), "shipment.tracking")
    _require_closed_keys(
        tracking,
        {"carrier", "tracking_number", "tracking_url"},
        "shipment tracking",
    )
    carrier = _text(tracking.get("carrier"), "tracking.carrier")
    tracking_number = _text(
        tracking.get("tracking_number"), "tracking.tracking_number"
    )
    tracking_url = _url(tracking.get("tracking_url"), "tracking.tracking_url")
    return ShipmentReceipt(
        order_id=intent.order_id,
        operation_key=intent.operation_key,
        intent_sha256=intent.intent_sha256,
        packet_hash=intent.publication.packet_hash,
        sku=intent.publication.sku,
        quantity=intent.quantity,
        job_id=print_receipt.job_id,
        print_receipt_sha256=print_receipt.receipt_sha256,
        print_profile_sha256=intent.publication.print_profile_sha256,
        material_spec_sha256=intent.publication.material_spec_sha256,
        manufacturing_spec_sha256=intent.publication.manufacturing_spec_sha256,
        manufacturing_spec_json=manufacturing_spec_json,
        artifact_hashes=artifacts,
        carrier=carrier,
        tracking_number=tracking_number,
        tracking_url=tracking_url,
        qa_authority=qa["authority"],
        qa_run_id=qa["run_id"],
        qa_protocol_id=qa["protocol_id"],
        qa_result=qa["result"],
        defect_evidence_sha256=qa["defect_evidence_sha256"],
        qa_receipt_sha256=qa["receipt_sha256"],
        receipt_sha256=canonical_sha256(raw),
    )


def _validate_qa_receipt(
    intent: FulfillmentIntent,
    print_receipt: PrintJobReceipt,
    value: Any,
) -> dict[str, str]:
    qa = _mapping(value, "shipment.qa")
    allowed = {
        "receipt_source",
        "authority",
        "run_id",
        "protocol_id",
        "result",
        "defect_evidence_sha256",
        "order_id",
        "operation_key",
        "intent_sha256",
        "packet_hash",
        "sku",
        "quantity",
        "job_id",
        "print_receipt_sha256",
        "print_profile_sha256",
        "material_spec_sha256",
        "manufacturing_spec_sha256",
        "manufacturing_spec",
        "artifact_hashes",
        "receipt_sha256",
    }
    _require_closed_keys(qa, allowed, "shipment QA receipt")
    if qa.get("receipt_source") != "authenticated_external_qa_readback":
        raise FulfillmentValidationError(
            "shipment QA receipt is not an authenticated external readback"
        )
    authority = _external_authority(qa.get("authority"), "shipment.qa.authority")
    run_id = _text(qa.get("run_id"), "shipment.qa.run_id")
    protocol_id = _text(qa.get("protocol_id"), "shipment.qa.protocol_id")
    if qa.get("result") != "passed":
        raise FulfillmentValidationError("shipment QA result must be 'passed'")
    defect_evidence_sha256 = _sha256(
        qa.get("defect_evidence_sha256"),
        "shipment.qa.defect_evidence_sha256",
    )
    for name, expected in (
        ("order_id", intent.order_id),
        ("operation_key", intent.operation_key),
        ("intent_sha256", intent.intent_sha256),
        ("packet_hash", intent.publication.packet_hash),
        ("sku", intent.publication.sku),
        ("quantity", intent.quantity),
        ("job_id", print_receipt.job_id),
        ("print_receipt_sha256", print_receipt.receipt_sha256),
        ("print_profile_sha256", intent.publication.print_profile_sha256),
        ("material_spec_sha256", intent.publication.material_spec_sha256),
        (
            "manufacturing_spec_sha256",
            intent.publication.manufacturing_spec_sha256,
        ),
    ):
        if qa.get(name) != expected:
            raise FulfillmentValidationError(f"shipment QA {name} mismatch")
    if _artifact_hashes(qa.get("artifact_hashes"), "shipment.qa") != (
        intent.publication.artifact_hashes
    ):
        raise FulfillmentValidationError("shipment QA artifact hashes mismatch")
    qa_spec, _ = _manufacturing_spec_payload(qa.get("manufacturing_spec"), "shipment.qa")
    if (
        qa_spec != intent.publication.manufacturing_spec
        or qa_spec != print_receipt.manufacturing_spec
    ):
        raise FulfillmentValidationError("shipment QA manufacturing_spec mismatch")
    _require_spec_artifact_paths(
        qa_spec, intent.publication.artifact_hashes, "shipment QA"
    )
    receipt_sha256 = _sha256(
        qa.get("receipt_sha256"), "shipment.qa.receipt_sha256"
    )
    receipt_body = dict(qa)
    receipt_body.pop("receipt_sha256")
    if canonical_sha256(receipt_body) != receipt_sha256:
        raise FulfillmentValidationError("shipment QA receipt_sha256 mismatch")
    return {
        "authority": authority,
        "run_id": run_id,
        "protocol_id": protocol_id,
        "result": "passed",
        "defect_evidence_sha256": defect_evidence_sha256,
        "receipt_sha256": receipt_sha256,
    }


def _require_intent_binding(
    intent: FulfillmentIntent, raw: Mapping[str, Any], label: str
) -> None:
    for name, expected in (
        ("order_id", intent.order_id),
        ("operation_key", intent.operation_key),
        ("intent_sha256", intent.intent_sha256),
        ("packet_hash", intent.publication.packet_hash),
        ("sku", intent.publication.sku),
        ("quantity", intent.quantity),
        ("print_profile_sha256", intent.publication.print_profile_sha256),
        ("material_spec_sha256", intent.publication.material_spec_sha256),
        (
            "manufacturing_spec_sha256",
            intent.publication.manufacturing_spec_sha256,
        ),
    ):
        if raw.get(name) != expected:
            raise FulfillmentValidationError(f"{label} {name} mismatch")


def _intent_index(
    intents: Sequence[FulfillmentIntent],
) -> dict[str, FulfillmentIntent]:
    if not isinstance(intents, Sequence) or isinstance(intents, (str, bytes)) or not intents:
        raise FulfillmentValidationError("fulfillment intents must be a non-empty sequence")
    result: dict[str, FulfillmentIntent] = {}
    for intent in intents:
        if not isinstance(intent, FulfillmentIntent):
            raise FulfillmentValidationError("fulfillment intents contain an invalid value")
        prior = result.get(intent.order_id)
        if prior is not None and prior != intent:
            raise FulfillmentValidationError(
                f"fulfillment intent {intent.order_id!r} conflicts with its duplicate"
            )
        result[intent.order_id] = intent
    return result


def _print_receipt_index(
    receipts: Sequence[PrintJobReceipt],
) -> dict[str, PrintJobReceipt]:
    if not isinstance(receipts, Sequence) or isinstance(receipts, (str, bytes)) or not receipts:
        raise FulfillmentValidationError("print receipts must be a non-empty sequence")
    result: dict[str, PrintJobReceipt] = {}
    for receipt in receipts:
        if not isinstance(receipt, PrintJobReceipt):
            raise FulfillmentValidationError("print receipts contain an invalid value")
        prior = result.get(receipt.order_id)
        if prior is not None and prior != receipt:
            raise FulfillmentValidationError(
                f"print receipt {receipt.order_id!r} conflicts with its duplicate"
            )
        result[receipt.order_id] = receipt
    return result


def _require_exact_orders(
    expected: Mapping[str, Any], actual: Mapping[str, Any], label: str
) -> None:
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    if missing or extra:
        raise FulfillmentValidationError(
            f"{label} do not exactly cover intents; missing={missing}, extra={extra}"
        )


def _publication_sku(
    manifest: Mapping[str, Any],
    request: Mapping[str, Any],
    response: Mapping[str, Any],
) -> str:
    candidates: list[tuple[str, Any]] = []
    for parent_name, parent in (
        ("production_manifest.listing", manifest.get("listing")),
        ("production_manifest.fulfillment", manifest.get("fulfillment")),
        ("publication.request", request.get("publication")),
        ("publication.response.listing", response.get("listing")),
    ):
        if isinstance(parent, Mapping) and "sku" in parent:
            candidates.append((f"{parent_name}.sku", parent.get("sku")))
    for name, parent in (
        ("production_manifest.sku", manifest),
        ("publication.response.sku", response),
        ("publication.response.listing_sku", response),
    ):
        key = name.rsplit(".", 1)[-1]
        if key in parent:
            candidates.append((name, parent.get(key)))
    if not candidates:
        raise FulfillmentValidationError(
            "confirmed publication does not persist its exact SKU"
        )
    values = {_sku(value, name) for name, value in candidates}
    if len(values) != 1:
        raise FulfillmentValidationError("confirmed publication SKU values disagree")
    return values.pop()


def _publication_price(
    manifest: Mapping[str, Any],
    request: Mapping[str, Any],
    response: Mapping[str, Any],
) -> tuple[int, str]:
    sources = (
        (
            "production_manifest.price",
            _mapping(manifest.get("price"), "production_manifest.price"),
        ),
        (
            "publication.request.publication",
            _mapping(request.get("publication"), "publication.request.publication"),
        ),
        ("publication.response", response),
    )
    prices = {
        _positive_int(source.get("price_cents"), f"{name}.price_cents")
        for name, source in sources
    }
    currencies = {
        _currency(source.get("currency"), f"{name}.currency")
        for name, source in sources
    }
    if len(prices) != 1:
        raise FulfillmentValidationError(
            "confirmed publication price_cents values disagree"
        )
    if len(currencies) != 1:
        raise FulfillmentValidationError(
            "confirmed publication currency values disagree"
        )
    currency = currencies.pop()
    if currency != "USD":
        raise FulfillmentValidationError("confirmed publication currency must be USD")
    return prices.pop(), currency


def _manufacturing_spec_payload(
    value: Any, label: str
) -> tuple[dict[str, Any], str]:
    spec = _mapping(value, f"{label}.manufacturing_spec")
    allowed = {
        "process",
        "print_profile_sha256",
        "material_spec_sha256",
        "manufacturing_spec_sha256",
        "materials",
        "bom",
        "packing",
    }
    _require_closed_keys(spec, allowed, f"{label}.manufacturing_spec")
    if set(spec) != allowed:
        raise FulfillmentValidationError(
            f"{label}.manufacturing_spec is incomplete"
        )
    canonical = manufacturing_spec_from_manifest(
        {
            "bom": spec.get("bom"),
            "manufacturing": {
                "process": spec.get("process"),
                "print_profile_sha256": spec.get("print_profile_sha256"),
                "material_spec_sha256": spec.get("material_spec_sha256"),
                "manufacturing_spec_sha256": spec.get(
                    "manufacturing_spec_sha256"
                ),
                "materials": spec.get("materials"),
                "packing": spec.get("packing"),
            },
        }
    )
    if dict(spec) != canonical:
        raise FulfillmentValidationError(
            f"{label}.manufacturing_spec is not canonical"
        )
    encoded = json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return canonical, encoded


def _require_spec_artifact_paths(
    spec: Mapping[str, Any],
    artifact_hashes: Sequence[tuple[str, str]],
    label: str,
) -> None:
    bom = spec.get("bom")
    if not isinstance(bom, list):
        raise FulfillmentValidationError(f"{label} manufacturing BOM is invalid")
    bound_paths = {name for name, _ in artifact_hashes}
    missing = sorted(
        str(line.get("artifact_path"))
        for line in bom
        if isinstance(line, Mapping) and line.get("artifact_path") not in bound_paths
    )
    if missing:
        raise FulfillmentValidationError(
            f"{label} manufacturing artifact paths are unbound: " + ", ".join(missing)
        )


def _artifact_hashes(value: Any, label: str) -> tuple[tuple[str, str], ...]:
    mapping = _mapping(value, f"{label}.artifact_hashes")
    if not mapping:
        raise FulfillmentValidationError(f"{label}.artifact_hashes must not be empty")
    result: list[tuple[str, str]] = []
    for name, digest in mapping.items():
        clean_name = _text(name, f"{label}.artifact_hashes key")
        result.append((clean_name, _sha256(digest, f"{label}.artifact_hashes[{clean_name!r}]")))
    result.sort()
    return tuple(result)


def _nonempty_object_list(value: Any, name: str) -> list[Mapping[str, Any]]:
    if not isinstance(value, list) or not value:
        raise FulfillmentValidationError(f"{name} must be a non-empty array")
    if any(not isinstance(item, Mapping) for item in value):
        raise FulfillmentValidationError(f"{name} entries must be objects")
    return list(value)


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise FulfillmentValidationError(f"{name} must be an object")
    return value


def _require_closed_keys(
    value: Mapping[str, Any], allowed: set[str], name: str
) -> None:
    unknown = sorted(
        str(key) for key in value.keys() if not isinstance(key, str) or key not in allowed
    )
    if unknown:
        raise FulfillmentValidationError(
            f"{name} contains unsupported fields: {', '.join(unknown)}"
        )


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise FulfillmentValidationError(f"{name} must be a non-empty trimmed string")
    if len(value) > 2_000 or any(ord(ch) < 32 or ord(ch) == 127 for ch in value):
        raise FulfillmentValidationError(f"{name} contains invalid characters")
    return value


def _external_authority(value: Any, name: str) -> str:
    authority = _text(value, name)
    tokens = {
        token
        for token in "".join(
            character.casefold() if character.isalnum() else " "
            for character in authority
        ).split()
        if token
    }
    if tokens & {
        "agent",
        "alice",
        "fixture",
        "internal",
        "mock",
        "model",
        "self",
        "simulated",
        "test",
    }:
        raise FulfillmentValidationError(
            f"{name} must identify an external QA authority"
        )
    return authority


def _sku(value: Any, name: str) -> str:
    result = _text(value, name)
    if len(result) > 128 or any(ord(ch) < 33 or ord(ch) > 126 for ch in result):
        raise FulfillmentValidationError(
            f"{name} must be printable non-space ASCII"
        )
    return result


def _currency(value: Any, name: str) -> str:
    result = _text(value, name)
    if (
        len(result) != 3
        or not result.isascii()
        or not result.isalpha()
        or not result.isupper()
    ):
        raise FulfillmentValidationError(
            f"{name} must be a three-letter uppercase currency code"
        )
    return result


def _sha256(value: Any, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value.lower() != value
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise FulfillmentValidationError(
            f"{name} must be a lowercase SHA-256 digest"
        )
    return value


def _positive_int(value: Any, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise FulfillmentValidationError(f"{name} must be a positive integer")
    return value


def _url(value: Any, name: str) -> str:
    result = _text(value, name)
    if not result.startswith("https://"):
        raise FulfillmentValidationError(f"{name} must use HTTPS")
    return result


__all__ = [
    "DELIVERY_ADAPTER",
    "LEGACY_FACTORY_ORDER_ADAPTER",
    "FACTORY_ORDER_ADAPTER",
    "PRINT_FULFILLMENT_ADAPTER",
    "VIBE_PUBLICATION_TARGET",
    "FulfillmentIntent",
    "FulfillmentValidationError",
    "PrintJobReceipt",
    "PublicationBinding",
    "ShipmentReceipt",
    "build_fulfillment_intents",
    "build_manufacturing_spec_from_manifest",
    "canonical_sha256",
    "confirmed_publication_binding",
    "fulfillment_operation_key",
    "fulfillment_intent_from_payload",
    "manufacturing_spec_from_manifest",
    "print_job_receipt_from_payload",
    "validate_print_job_receipts",
    "validate_qa_ship_receipts",
]
