from __future__ import annotations

from dataclasses import replace
from copy import deepcopy
from pathlib import Path
import sys
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alice.adapters import AdapterReceipt  # noqa: E402
from alice.fulfillment import (  # noqa: E402
    FulfillmentValidationError,
    build_fulfillment_intents,
    canonical_sha256,
    confirmed_publication_binding,
    fulfillment_intent_from_payload,
    fulfillment_operation_key,
    manufacturing_spec_from_manifest,
    build_manufacturing_spec_from_manifest,
    validate_print_job_receipts,
    validate_qa_ship_receipts,
)
from alice.store import PublicationRecord  # noqa: E402


PACKET_A = "a" * 64
ARTIFACTS = {"board.3mf": "b" * 64, "pieces.3mf": "c" * 64}
PRINT_PROFILE_SHA256 = "8" * 64
BOM = [
    {
        "part_id": "board",
        "name": "Board",
        "quantity": 1,
        "material": "PLA",
        "manufacturing_method": "3d_print",
        "artifact_path": "board.3mf",
    },
    {
        "part_id": "pieces",
        "name": "Playing pieces",
        "quantity": 16,
        "material": "PLA",
        "manufacturing_method": "3d_print",
        "artifact_path": "pieces.3mf",
    },
]


def add_manufacturing_digests(manifest):
    spec = build_manufacturing_spec_from_manifest(manifest)
    manufacturing = manifest["manufacturing"]
    manufacturing["material_spec_sha256"] = spec["material_spec_sha256"]
    manufacturing["manufacturing_spec_sha256"] = spec[
        "manufacturing_spec_sha256"
    ]
    return spec


def publication(
    *,
    publication_id: str = "publication-1",
    candidate_id: str = "candidate-1",
    sku: str = "ALICE-RIVER-001",
) -> PublicationRecord:
    manifest = {
        "candidate_id": candidate_id,
        "candidate_version": 3,
        "candidate_content_sha256": "d" * 64,
        "listing": {"sku": sku},
        "bom": [dict(line) for line in BOM],
        "manufacturing": {
            "process": "3d_print",
            "print_profile_sha256": PRINT_PROFILE_SHA256,
            "materials": ["PLA"],
            "packing": {"format": "carton", "component_count": 17},
            "vibe_design": {
                "design_id": "design-1",
                "slug": "river-council",
                "history_id": "history-1",
                "project_url": "https://cdn.example/project/",
                "artifact_hashes": dict(ARTIFACTS),
            }
        },
        "price": {"price_cents": 9999, "currency": "USD"},
    }
    add_manufacturing_digests(manifest)
    packet_hash = canonical_sha256(manifest)
    operation_key = f"alice:vibe:{candidate_id}:v5:{packet_hash}"
    request = {
        "schema_version": 1,
        "operation_key": operation_key,
        "candidate_id": candidate_id,
        "candidate_version": 5,
        "candidate_content_sha256": "d" * 64,
        "packet_hash": packet_hash,
        "production_packet_hash": packet_hash,
        "reviewed_packet_hash": packet_hash,
        "policy_hash": "e" * 64,
        "production_candidate_version": 3,
        "production_manifest": manifest,
        "release_decision": {
            "allowed": True,
            "effect_mode": "live",
            "candidate_id": candidate_id,
            "production_packet_hash": packet_hash,
            "reviewed_packet_hash": packet_hash,
        },
        "existing_design": {
            "design_id": "design-1",
            "slug": "river-council",
            "history_id": "history-1",
            "project_url": "https://cdn.example/project/",
            "artifact_hashes": dict(ARTIFACTS),
        },
        "publication": {"price_cents": 9999, "currency": "USD"},
    }
    return PublicationRecord(
        id=publication_id,
        target="vibe_pipeline",
        idempotency_key=operation_key,
        request_sha256=canonical_sha256(request),
        request=request,
        candidate_id=candidate_id,
        state="confirmed",
        remote_design_id="design-1",
        slug="river-council",
        history_id="history-1",
        status="published",
        project_url="https://cdn.example/project/",
        response={
            "stage": "complete",
            "operation_key": operation_key,
            "candidate_id": candidate_id,
            "packet_hash": packet_hash,
            "listing_sku": sku,
            "price_cents": 9999,
            "currency": "USD",
        },
        last_error=None,
        created_at=1.0,
        updated_at=2.0,
    )


def adapter_receipt(adapter: str, evidence_class: str, payload) -> AdapterReceipt:
    return AdapterReceipt(
        adapter=adapter,
        run_id=f"run-{adapter}",
        status="passed",
        evidence_class=evidence_class,
        payload=payload,
        input_sha256="f" * 64,
    )


def order(record: PublicationRecord, *, order_id="order-1", quantity=1):
    publication_price = record.request["publication"]
    price_cents = publication_price["price_cents"]
    return {
        "order_id": order_id,
        "payment_status": "paid",
        "publication_id": record.id,
        "packet_hash": record.request["packet_hash"],
        "sku": record.request["production_manifest"]["listing"]["sku"],
        "quantity": quantity,
        "currency": publication_price["currency"],
        "unit_price_cents": price_cents,
        "product_subtotal_cents": price_cents * quantity,
        "amount_paid_cents": price_cents * quantity,
        "shipping_reference": f"address-token-{order_id}",
    }


def order_result(orders):
    return adapter_receipt("delivery", "market", {"orders": orders})


def print_job(intent, *, job_id=None):
    return {
        "status": "created",
        "order_id": intent.order_id,
        "operation_key": intent.operation_key,
        "intent_sha256": intent.intent_sha256,
        "packet_hash": intent.publication.packet_hash,
        "sku": intent.publication.sku,
        "quantity": intent.quantity,
        "job_id": job_id or f"print-{intent.order_id}",
        "print_profile_sha256": intent.publication.print_profile_sha256,
        "material_spec_sha256": intent.publication.material_spec_sha256,
        "manufacturing_spec_sha256": intent.publication.manufacturing_spec_sha256,
        "manufacturing_spec": intent.publication.manufacturing_spec,
        "artifact_hashes": intent.publication.artifact_hash_map,
    }


def shipment(intent, printed):
    qa = {
        "receipt_source": "authenticated_external_qa_readback",
        "authority": "factory-qa.example",
        "run_id": f"qa-run-{intent.order_id}",
        "protocol_id": "final-inspection-v1",
        "result": "passed",
        "defect_evidence_sha256": "9" * 64,
        "order_id": intent.order_id,
        "operation_key": intent.operation_key,
        "intent_sha256": intent.intent_sha256,
        "packet_hash": intent.publication.packet_hash,
        "sku": intent.publication.sku,
        "quantity": intent.quantity,
        "job_id": printed.job_id,
        "print_receipt_sha256": printed.receipt_sha256,
        "print_profile_sha256": intent.publication.print_profile_sha256,
        "material_spec_sha256": intent.publication.material_spec_sha256,
        "manufacturing_spec_sha256": intent.publication.manufacturing_spec_sha256,
        "manufacturing_spec": intent.publication.manufacturing_spec,
        "artifact_hashes": intent.publication.artifact_hash_map,
    }
    qa["receipt_sha256"] = canonical_sha256(qa)
    return {
        "status": "shipped",
        "qa_passed": True,
        "order_id": intent.order_id,
        "operation_key": intent.operation_key,
        "intent_sha256": intent.intent_sha256,
        "packet_hash": intent.publication.packet_hash,
        "sku": intent.publication.sku,
        "quantity": intent.quantity,
        "job_id": printed.job_id,
        "print_receipt_sha256": printed.receipt_sha256,
        "print_profile_sha256": intent.publication.print_profile_sha256,
        "material_spec_sha256": intent.publication.material_spec_sha256,
        "manufacturing_spec_sha256": intent.publication.manufacturing_spec_sha256,
        "manufacturing_spec": intent.publication.manufacturing_spec,
        "artifact_hashes": intent.publication.artifact_hash_map,
        "qa": qa,
        "tracking": {
            "carrier": "UPS",
            "tracking_number": f"TRACK-{intent.order_id}",
            "tracking_url": f"https://tracking.example/{intent.order_id}",
        },
    }


class FulfillmentIntentTests(unittest.TestCase):
    def test_builds_stable_sorted_immutable_intents_from_passed_receipt(self) -> None:
        first = publication()
        second = publication(
            publication_id="publication-2",
            candidate_id="candidate-2",
            sku="ALICE-MOON-002",
        )
        raw_second = order(second, order_id="order-2", quantity=2)
        raw_second["amount_paid_cents"] += 1_250
        raw_first = order(first, order_id="order-1")

        intents = build_fulfillment_intents(
            order_result([raw_second, raw_first]), [second, first]
        )

        self.assertEqual([item.order_id for item in intents], ["order-1", "order-2"])
        self.assertEqual(
            intents[0].operation_key, fulfillment_operation_key("order-1")
        )
        self.assertNotIn("order-1", intents[0].operation_key)
        self.assertEqual(intents[0].source_order_sha256, canonical_sha256(raw_first))
        self.assertEqual(intents[0].publication.artifact_hash_map, ARTIFACTS)
        self.assertEqual(intents[0].publication.price_cents, 9999)
        self.assertEqual(intents[0].publication.currency, "USD")
        self.assertEqual(intents[1].quantity, 2)
        self.assertEqual(
            intents[0].intent_sha256,
            canonical_sha256(intents[0].as_payload(include_digest=False)),
        )
        self.assertEqual(
            intents[0].as_payload()["intent_sha256"], intents[0].intent_sha256
        )
        self.assertEqual(
            fulfillment_intent_from_payload(intents[0].as_payload()), intents[0]
        )

    def test_rehydrated_intent_rejects_non_usd_publication_currency(self) -> None:
        record = publication()
        intent = build_fulfillment_intents(order_result([order(record)]), [record])[0]
        payload = intent.as_payload()
        payload["publication"]["currency"] = "EUR"
        payload["intent_sha256"] = canonical_sha256(
            {key: value for key, value in payload.items() if key != "intent_sha256"}
        )

        with self.assertRaisesRegex(FulfillmentValidationError, "must be USD"):
            fulfillment_intent_from_payload(payload)

    def test_rehydrated_intent_rejects_changed_manufacturing_recipe(self) -> None:
        record = publication()
        intent = build_fulfillment_intents(order_result([order(record)]), [record])[0]
        payload = intent.as_payload()
        payload["publication"]["manufacturing_spec"]["packing"][
            "component_count"
        ] = 99
        payload["intent_sha256"] = canonical_sha256(
            {key: value for key, value in payload.items() if key != "intent_sha256"}
        )
        with self.assertRaisesRegex(FulfillmentValidationError, "packing|recipe"):
            fulfillment_intent_from_payload(payload)

    def test_accepts_durable_engine_result_and_deduplicates_exact_replay(self) -> None:
        record = publication()
        raw = order(record)
        receipt = order_result([raw, dict(raw)])
        durable_result = {
            "executor": "adapter",
            "receipt": {
                "adapter": receipt.adapter,
                "run_id": receipt.run_id,
                "status": receipt.status,
                "evidence_class": receipt.evidence_class,
                "payload": receipt.payload,
                "input_sha256": receipt.input_sha256,
            },
        }

        intents = build_fulfillment_intents(durable_result, [record])

        self.assertEqual(len(intents), 1)

    def test_rejects_unpassed_wrong_or_unwrapped_adapter_content(self) -> None:
        record = publication()
        raw_payload = {"orders": [order(record)]}
        bad_values = [
            raw_payload,
            adapter_receipt("wrong", "market", raw_payload),
            adapter_receipt("factory_order", "external", raw_payload),
            replace(order_result([order(record)]), status="failed"),
            {"executor": "agent", "receipt": {}},
        ]
        for value in bad_values:
            with self.subTest(value=value):
                with self.assertRaises(FulfillmentValidationError):
                    build_fulfillment_intents(value, [record])

    def test_rejects_empty_or_malformed_order_batch(self) -> None:
        record = publication()
        for value in (None, {}, ["not-an-order"]):
            with self.subTest(value=value):
                with self.assertRaises(FulfillmentValidationError):
                    build_fulfillment_intents(
                        order_result(value), [record]
                    )

    def test_empty_paid_order_poll_is_a_normal_noop(self) -> None:
        self.assertEqual(build_fulfillment_intents(order_result([]), []), ())

    def test_legacy_factory_order_receipt_remains_readable(self) -> None:
        self.assertEqual(
            build_fulfillment_intents(
                adapter_receipt("factory_order", "market", {"orders": []}),
                [],
            ),
            (),
        )

    def test_rejects_every_invalid_required_order_field(self) -> None:
        record = publication()
        base = order(record)
        changes = {
            "order_id": "",
            "payment_status": "authorized",
            "publication_id": None,
            "packet_hash": "bad",
            "sku": "bad sku",
            "quantity": 0,
            "currency": None,
            "unit_price_cents": True,
            "product_subtotal_cents": "9999",
            "amount_paid_cents": 0,
            "shipping_reference": " ",
        }
        for name, bad in changes.items():
            with self.subTest(name=name):
                raw = dict(base)
                raw[name] = bad
                with self.assertRaises(FulfillmentValidationError):
                    build_fulfillment_intents(order_result([raw]), [record])

    def test_rejects_wrong_currency_price_subtotal_or_underpayment(self) -> None:
        record = publication()
        base = order(record, quantity=2)
        changes = {
            "currency": "EUR",
            "unit_price_cents": 10_000,
            "product_subtotal_cents": 19_997,
            "amount_paid_cents": 19_997,
        }
        for name, bad in changes.items():
            with self.subTest(name=name):
                raw = dict(base)
                raw[name] = bad
                with self.assertRaises(FulfillmentValidationError):
                    build_fulfillment_intents(order_result([raw]), [record])

    def test_rejects_raw_customer_pii_and_unknown_adapter_fields(self) -> None:
        record = publication()
        raw = dict(order(record), shipping_address="123 Private Street")
        with self.assertRaisesRegex(FulfillmentValidationError, "unsupported fields"):
            build_fulfillment_intents(order_result([raw]), [record])
        receipt = adapter_receipt(
            "factory_order",
            "market",
            {"orders": [order(record)], "customer_email": "private@example.com"},
        )
        with self.assertRaisesRegex(FulfillmentValidationError, "unsupported fields"):
            build_fulfillment_intents(receipt, [record])

    def test_rejects_conflicting_duplicate_order(self) -> None:
        record = publication()
        left = order(record)
        right = dict(left, quantity=2)
        with self.assertRaisesRegex(FulfillmentValidationError, "conflicting"):
            build_fulfillment_intents(order_result([left, right]), [record])
        redundant_identity = dict(left, candidate_id=record.candidate_id)
        changed_identity = dict(left, candidate_id="wrong-candidate")
        with self.assertRaisesRegex(FulfillmentValidationError, "conflicting"):
            build_fulfillment_intents(
                order_result([redundant_identity, changed_identity]), [record]
            )

    def test_rejects_unknown_publication_packet_sku_or_identity_mismatch(self) -> None:
        record = publication()
        changes = {
            "publication_id": "missing",
            "packet_hash": "0" * 64,
            "sku": "OTHER-SKU",
            "candidate_id": "wrong-candidate",
            "design_id": "wrong-design",
            "history_id": "wrong-history",
        }
        for name, bad in changes.items():
            with self.subTest(name=name):
                raw = dict(order(record))
                raw[name] = bad
                with self.assertRaises(FulfillmentValidationError):
                    build_fulfillment_intents(order_result([raw]), [record])


class PublicationBindingTests(unittest.TestCase):
    def test_extracts_exact_confirmed_binding_price_and_sku_sources(self) -> None:
        binding = confirmed_publication_binding(publication())
        self.assertEqual(
            binding.packet_hash,
            canonical_sha256(publication().request["production_manifest"]),
        )
        self.assertEqual(binding.sku, "ALICE-RIVER-001")
        self.assertEqual(binding.price_cents, 9999)
        self.assertEqual(binding.currency, "USD")
        self.assertEqual(binding.print_profile_sha256, PRINT_PROFILE_SHA256)
        self.assertEqual(
            binding.manufacturing_spec_sha256,
            binding.manufacturing_spec["manufacturing_spec_sha256"],
        )
        self.assertEqual(
            binding.material_spec_sha256,
            binding.manufacturing_spec["material_spec_sha256"],
        )
        self.assertEqual(binding.artifact_hash_map, ARTIFACTS)

    def test_construction_helper_canonicalizes_and_validates_complete_recipe(self) -> None:
        manifest = deepcopy(publication().request["production_manifest"])
        expected = manufacturing_spec_from_manifest(manifest)
        manifest["bom"].reverse()
        manufacturing = manifest["manufacturing"]
        manufacturing.pop("material_spec_sha256")
        manufacturing.pop("manufacturing_spec_sha256")
        constructed = build_manufacturing_spec_from_manifest(manifest)
        self.assertEqual(constructed, expected)

        extra_material = deepcopy(manifest)
        extra_material["manufacturing"]["materials"].append("PETG")
        with self.assertRaisesRegex(FulfillmentValidationError, "exactly equal"):
            build_manufacturing_spec_from_manifest(extra_material)

        missing_artifact = deepcopy(manifest)
        missing_artifact["bom"][0]["artifact_path"] = "unbound.3mf"
        with self.assertRaisesRegex(FulfillmentValidationError, "not bound"):
            build_manufacturing_spec_from_manifest(missing_artifact)

    def test_publication_fails_closed_on_missing_or_changed_recipe_digests(self) -> None:
        base = publication()

        def rebound(manifest):
            packet_hash = canonical_sha256(manifest)
            request = {
                **base.request,
                "packet_hash": packet_hash,
                "production_packet_hash": packet_hash,
                "reviewed_packet_hash": packet_hash,
                "production_manifest": manifest,
                "release_decision": {
                    **base.request["release_decision"],
                    "production_packet_hash": packet_hash,
                    "reviewed_packet_hash": packet_hash,
                },
            }
            return replace(
                base,
                request=request,
                request_sha256=canonical_sha256(request),
                response={**base.response, "packet_hash": packet_hash},
            )

        cases = []
        for name in (
            "print_profile_sha256",
            "material_spec_sha256",
            "manufacturing_spec_sha256",
        ):
            missing = deepcopy(base.request["production_manifest"])
            missing["manufacturing"].pop(name)
            cases.append(rebound(missing))
            changed = deepcopy(base.request["production_manifest"])
            changed["manufacturing"][name] = "0" * 64
            cases.append(rebound(changed))
        for changed in cases:
            with self.subTest(changed=changed.request["production_manifest"]):
                with self.assertRaises(FulfillmentValidationError):
                    confirmed_publication_binding(changed)

    def test_rejects_nonconfirmed_nonpublished_or_wrong_target(self) -> None:
        base = publication()
        for changed in (
            replace(base, state="in_flight"),
            replace(base, status="draft"),
            replace(base, target="other"),
        ):
            with self.subTest(changed=changed):
                with self.assertRaises(FulfillmentValidationError):
                    confirmed_publication_binding(changed)

    def test_rejects_tampered_request_or_incomplete_response(self) -> None:
        base = publication()
        tampered_request = dict(base.request, candidate_id="wrong")
        cases = (
            replace(base, request=tampered_request),
            replace(base, response=dict(base.response, stage="public_waiting")),
            replace(base, response=dict(base.response, packet_hash="0" * 64)),
        )
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaises(FulfillmentValidationError):
                    confirmed_publication_binding(changed)

    def test_rejects_conflicting_or_missing_sku(self) -> None:
        base = publication()
        conflict = replace(base, response=dict(base.response, listing_sku="OTHER"))
        manifest = dict(base.request["production_manifest"])
        manifest.pop("listing")
        packet_hash = canonical_sha256(manifest)
        request = dict(
            base.request,
            packet_hash=packet_hash,
            production_packet_hash=packet_hash,
            reviewed_packet_hash=packet_hash,
            production_manifest=manifest,
            release_decision={
                **base.request["release_decision"],
                "production_packet_hash": packet_hash,
                "reviewed_packet_hash": packet_hash,
            },
        )
        response = dict(base.response, packet_hash=packet_hash)
        response.pop("listing_sku")
        missing = replace(
            base,
            idempotency_key="new-operation",
            request={**request, "operation_key": "new-operation"},
            response={**response, "operation_key": "new-operation"},
        )
        missing = replace(missing, request_sha256=canonical_sha256(missing.request))
        for changed in (conflict, missing):
            with self.subTest(changed=changed):
                with self.assertRaises(FulfillmentValidationError):
                    confirmed_publication_binding(changed)

    def test_rejects_conflicting_or_missing_publication_price_sources(self) -> None:
        base = publication()

        request_price_conflict = {
            **base.request,
            "publication": {"price_cents": 10_999, "currency": "USD"},
        }
        request_price_conflict = replace(
            base,
            request=request_price_conflict,
            request_sha256=canonical_sha256(request_price_conflict),
        )

        request_currency_missing = {
            **base.request,
            "publication": {"price_cents": 9999},
        }
        request_currency_missing = replace(
            base,
            request=request_currency_missing,
            request_sha256=canonical_sha256(request_currency_missing),
        )

        manifest = {
            **base.request["production_manifest"],
            "price": {"price_cents": 10_999, "currency": "USD"},
        }
        packet_hash = canonical_sha256(manifest)
        manifest_price_conflict_request = {
            **base.request,
            "packet_hash": packet_hash,
            "production_packet_hash": packet_hash,
            "reviewed_packet_hash": packet_hash,
            "production_manifest": manifest,
            "release_decision": {
                **base.request["release_decision"],
                "production_packet_hash": packet_hash,
                "reviewed_packet_hash": packet_hash,
            },
        }
        manifest_price_conflict = replace(
            base,
            request=manifest_price_conflict_request,
            request_sha256=canonical_sha256(manifest_price_conflict_request),
            response={**base.response, "packet_hash": packet_hash},
        )

        cases = (
            replace(base, response={**base.response, "price_cents": 10_999}),
            replace(base, response={**base.response, "currency": "EUR"}),
            request_price_conflict,
            request_currency_missing,
            manifest_price_conflict,
        )
        for changed in cases:
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(
                    FulfillmentValidationError, "price|currency"
                ):
                    confirmed_publication_binding(changed)

    def test_rejects_manifest_design_and_artifact_tampering_even_when_rehashed(self) -> None:
        base = publication()
        manifest = dict(base.request["production_manifest"])
        manufacturing = dict(manifest["manufacturing"])
        design = dict(manufacturing["vibe_design"])
        design["artifact_hashes"] = {"board.3mf": "9" * 64}
        manufacturing["vibe_design"] = design
        manifest["manufacturing"] = manufacturing
        packet_hash = canonical_sha256(manifest)
        request = {
            **base.request,
            "packet_hash": packet_hash,
            "production_packet_hash": packet_hash,
            "reviewed_packet_hash": packet_hash,
            "production_manifest": manifest,
            "release_decision": {
                **base.request["release_decision"],
                "production_packet_hash": packet_hash,
                "reviewed_packet_hash": packet_hash,
            },
        }
        changed = replace(
            base,
            request=request,
            request_sha256=canonical_sha256(request),
            response=dict(base.response, packet_hash=packet_hash),
        )
        with self.assertRaisesRegex(FulfillmentValidationError, "artifact"):
            confirmed_publication_binding(changed)


class FulfillmentReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.first_publication = publication()
        self.second_publication = publication(
            publication_id="publication-2",
            candidate_id="candidate-2",
            sku="ALICE-MOON-002",
        )
        self.intents = build_fulfillment_intents(
            order_result(
                [
                    order(self.first_publication, order_id="order-1"),
                    order(self.second_publication, order_id="order-2", quantity=2),
                ]
            ),
            [self.first_publication, self.second_publication],
        )

    def print_result(self, values):
        return adapter_receipt(
            "print_fulfillment", "manufacturing", {"print_jobs": values}
        )

    def shipment_result(self, values):
        return adapter_receipt(
            "print_fulfillment", "manufacturing", {"shipments": values}
        )

    def test_print_receipts_bind_every_intent_and_are_deterministic(self) -> None:
        raw = [print_job(self.intents[1]), print_job(self.intents[0])]
        receipts = validate_print_job_receipts(self.intents, self.print_result(raw))

        self.assertEqual([value.order_id for value in receipts], ["order-1", "order-2"])
        self.assertEqual(receipts[0].artifact_hash_map, ARTIFACTS)
        self.assertEqual(receipts[0].receipt_sha256, canonical_sha256(raw[1]))

    def test_print_receipts_reject_each_broken_binding_and_artifact(self) -> None:
        first = print_job(self.intents[0])
        second = print_job(self.intents[1])
        changes = {
            "status": "queued",
            "operation_key": "wrong",
            "intent_sha256": "0" * 64,
            "packet_hash": "0" * 64,
            "sku": "OTHER",
            "quantity": 99,
            "job_id": "",
            "print_profile_sha256": "0" * 64,
            "material_spec_sha256": "0" * 64,
            "manufacturing_spec_sha256": "0" * 64,
            "manufacturing_spec": {},
            "artifact_hashes": {"board.3mf": "b" * 64},
        }
        for name, bad in changes.items():
            with self.subTest(name=name):
                changed = dict(first)
                changed[name] = bad
                with self.assertRaises(FulfillmentValidationError):
                    validate_print_job_receipts(
                        self.intents, self.print_result([changed, second])
                    )

    def test_print_receipts_reject_missing_unexpected_conflicting_and_reused_jobs(self) -> None:
        first = print_job(self.intents[0])
        second = print_job(self.intents[1])
        conflict = dict(first, quantity=2)
        unexpected = dict(first, order_id="order-x")
        reused = dict(second, job_id=first["job_id"])
        cases = ([first], [first, unexpected], [first, conflict, second], [first, reused])
        for values in cases:
            with self.subTest(values=values):
                with self.assertRaises(FulfillmentValidationError):
                    validate_print_job_receipts(self.intents, self.print_result(values))

    def test_print_receipts_require_passed_manufacturing_adapter(self) -> None:
        payload = {"print_jobs": [print_job(value) for value in self.intents]}
        for result in (
            adapter_receipt("factory_order", "manufacturing", payload),
            adapter_receipt("print_fulfillment", "market", payload),
            replace(
                adapter_receipt("print_fulfillment", "manufacturing", payload),
                status="partial",
            ),
        ):
            with self.subTest(result=result):
                with self.assertRaises(FulfillmentValidationError):
                    validate_print_job_receipts(self.intents, result)

    def test_qa_ship_receipts_bind_print_job_artifacts_and_tracking(self) -> None:
        printed = validate_print_job_receipts(
            self.intents,
            self.print_result([print_job(value) for value in self.intents]),
        )
        raw = [
            shipment(self.intents[1], printed[1]),
            shipment(self.intents[0], printed[0]),
        ]
        shipped = validate_qa_ship_receipts(
            self.intents, printed, self.shipment_result(raw)
        )

        self.assertEqual([value.order_id for value in shipped], ["order-1", "order-2"])
        self.assertEqual(shipped[0].job_id, printed[0].job_id)
        self.assertEqual(shipped[0].print_receipt_sha256, printed[0].receipt_sha256)
        self.assertEqual(shipped[0].carrier, "UPS")
        self.assertEqual(shipped[0].qa_authority, "factory-qa.example")
        self.assertEqual(shipped[0].qa_result, "passed")
        self.assertEqual(shipped[0].defect_evidence_sha256, "9" * 64)
        self.assertTrue(shipped[0].tracking_url.startswith("https://"))

    def test_qa_ship_receipts_reject_every_broken_binding_qa_and_tracking_field(self) -> None:
        printed = validate_print_job_receipts(
            self.intents,
            self.print_result([print_job(value) for value in self.intents]),
        )
        first = shipment(self.intents[0], printed[0])
        second = shipment(self.intents[1], printed[1])
        simple_changes = {
            "status": "packed",
            "qa_passed": False,
            "operation_key": "wrong",
            "intent_sha256": "0" * 64,
            "packet_hash": "0" * 64,
            "sku": "OTHER",
            "quantity": 9,
            "job_id": "wrong-job",
            "print_receipt_sha256": "0" * 64,
            "print_profile_sha256": "0" * 64,
            "material_spec_sha256": "0" * 64,
            "manufacturing_spec_sha256": "0" * 64,
            "manufacturing_spec": {},
            "artifact_hashes": {"board.3mf": "b" * 64},
            "qa": {},
        }
        for name, bad in simple_changes.items():
            with self.subTest(name=name):
                changed = dict(first)
                changed[name] = bad
                with self.assertRaises(FulfillmentValidationError):
                    validate_qa_ship_receipts(
                        self.intents,
                        printed,
                        self.shipment_result([changed, second]),
                    )
        qa_changes = {
            "receipt_source": "self_attested",
            "authority": "Alice internal agent",
            "run_id": "",
            "protocol_id": "",
            "result": "failed",
            "defect_evidence_sha256": "bad",
            "order_id": "other-order",
            "operation_key": "wrong",
            "intent_sha256": "0" * 64,
            "packet_hash": "0" * 64,
            "sku": "OTHER",
            "quantity": 99,
            "job_id": "wrong-job",
            "print_receipt_sha256": "0" * 64,
            "print_profile_sha256": "0" * 64,
            "material_spec_sha256": "0" * 64,
            "manufacturing_spec_sha256": "0" * 64,
            "manufacturing_spec": {},
            "artifact_hashes": {"board.3mf": "b" * 64},
            "receipt_sha256": "0" * 64,
        }
        for name, bad in qa_changes.items():
            with self.subTest(qa=name):
                changed = dict(first)
                qa = dict(first["qa"])
                qa[name] = bad
                if name != "receipt_sha256":
                    qa.pop("receipt_sha256", None)
                    qa["receipt_sha256"] = canonical_sha256(qa)
                changed["qa"] = qa
                with self.assertRaises(FulfillmentValidationError):
                    validate_qa_ship_receipts(
                        self.intents,
                        printed,
                        self.shipment_result([changed, second]),
                    )
        for name, bad in (
            ("carrier", ""),
            ("tracking_number", ""),
            ("tracking_url", "not-a-url"),
        ):
            with self.subTest(tracking=name):
                changed = dict(first)
                changed["tracking"] = dict(first["tracking"], **{name: bad})
                with self.assertRaises(FulfillmentValidationError):
                    validate_qa_ship_receipts(
                        self.intents,
                        printed,
                        self.shipment_result([changed, second]),
                    )

    def test_qa_ship_requires_exact_sets_and_passed_adapter(self) -> None:
        printed = validate_print_job_receipts(
            self.intents,
            self.print_result([print_job(value) for value in self.intents]),
        )
        first = shipment(self.intents[0], printed[0])
        second = shipment(self.intents[1], printed[1])
        conflict = dict(first, qa_passed=False)
        bad_adapter = adapter_receipt(
            "factory_order", "manufacturing", {"shipments": [first, second]}
        )
        cases = (
            (printed, self.shipment_result([first])),
            (printed, self.shipment_result([first, conflict, second])),
            (printed, bad_adapter),
            (printed[:1], self.shipment_result([first, second])),
        )
        for print_values, result in cases:
            with self.subTest(result=result):
                with self.assertRaises(FulfillmentValidationError):
                    validate_qa_ship_receipts(self.intents, print_values, result)


if __name__ == "__main__":
    unittest.main()
