"""Strict physical-delivery receipt fixtures shared by Workshop tests."""

from workshop.deliver.evidence import DeliveryEvidenceReceipt


def fixture_delivery_evidence(
    product_artifact_sha256,
    instructions_sha256,
    *,
    carrier="USPS",
    service="Priority Mail",
    tracking_id="9400100000000000000000",
    status="handed-off",
    observed_at="2026-08-23T12:00:00+00:00",
):
    common = {
        "provider": "fixture-fulfillment-bench",
        "provider_version": "1.0.0",
        "provider_config_sha256": "d" * 64,
        "product_artifact_sha256": product_artifact_sha256,
        "instructions_sha256": instructions_sha256,
        "observed_at": observed_at,
    }
    printed = DeliveryEvidenceReceipt(
        stage="print",
        receipt_id="print-receipt-1",
        details={
            "job_id": "print-1",
            "status": "completed",
            "quantity": 1,
            "material": "PLA",
            "output_lot_id": "lot-1",
        },
        **common,
    )
    qa = DeliveryEvidenceReceipt(
        stage="qa",
        receipt_id="qa-receipt-1",
        details={
            "inspection_id": "qa-1",
            "status": "passed",
            "print_receipt_sha256": printed.receipt_sha256,
            "checks": ["exact-product", "fit", "finish", "safety"],
        },
        **common,
    )
    packed = DeliveryEvidenceReceipt(
        stage="packing",
        receipt_id="packing-receipt-1",
        details={
            "package_id": "box-1",
            "status": "sealed",
            "print_receipt_sha256": printed.receipt_sha256,
            "qa_receipt_sha256": qa.receipt_sha256,
            "contents_count": 2,
        },
        **common,
    )
    handed_off = DeliveryEvidenceReceipt(
        stage="carrier",
        receipt_id="carrier-receipt-1",
        details={
            "carrier": carrier,
            "service": service,
            "tracking_id": tracking_id,
            "status": status,
            "package_id": "box-1",
            "packing_receipt_sha256": packed.receipt_sha256,
            "acceptance_scan_id": "scan-1",
        },
        **common,
    )
    return {
        "print_receipt": printed.to_dict(),
        "qa_receipt": qa.to_dict(),
        "packing_receipt": packed.to_dict(),
        "carrier_receipt": handed_off.to_dict(),
    }
