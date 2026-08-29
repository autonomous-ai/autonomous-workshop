#!/usr/bin/env python3
"""Deterministically reconcile the root Make package with CAD evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


PRODUCT_ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load(relative: str):
    with (PRODUCT_ROOT / relative).open("r", encoding="utf-8") as source:
        return json.load(source)


def main() -> None:
    required = (
        "product.json",
        "assembled.step",
        "assembled.step.json",
        "assembled.stl",
    )
    assert all((PRODUCT_ROOT / path).is_file() for path in required)

    product = load("product.json")
    verification = load("assembled.step.json")
    audit = load("cad_project/measure/acoustic_geometry.json")

    assert product["status"] == "digitally-verified-print-ready"
    assert product["physical_test_status"] == "not-run"
    assert product["sound_claim_status"] == "calculated-intent-only"
    assert len(product["printed_parts"]) == 6
    for part in product["printed_parts"]:
        assert (PRODUCT_ROOT / part["step"]).is_file()
        assert (PRODUCT_ROOT / part["stl"]).is_file()

    assembly = verification["assembly"]
    assert verification["status"] == "pass"
    assert verification["final_pipeline"]["status"] == "pass"
    assert verification["final_pipeline"]["print_ready_claim"] is True
    assert sha256(PRODUCT_ROOT / assembly["step_path"]) == assembly["step_sha256"]
    assert sha256(PRODUCT_ROOT / assembly["stl_path"]) == assembly["stl_sha256"]
    assert sha256(PRODUCT_ROOT / "cad_project/rainspell_dial.step") == assembly["step_sha256"]
    assert sha256(PRODUCT_ROOT / "cad_project/rainspell_dial.stl") == assembly["stl_sha256"]

    report = PRODUCT_ROOT / verification["final_pipeline"]["report_path"]
    assert sha256(report) == verification["final_pipeline"]["report_sha256"]
    assert "Result: **PASS** (exit 0)" in report.read_text(encoding="utf-8")
    acoustic_check = next(
        check for check in verification["checks"] if check["id"] == "wish-specific-geometry"
    )
    assert sha256(PRODUCT_ROOT / acoustic_check["path"]) == acoustic_check["sha256"]
    reproducibility_check = next(
        check
        for check in verification["checks"]
        if check["id"] == "declared-output-reproducibility"
    )
    assert (
        sha256(PRODUCT_ROOT / reproducibility_check["path"])
        == reproducibility_check["sha256"]
    )
    assert product["evidence"]["declared_output_reproducibility"] == reproducibility_check["path"]
    assert audit["assembly_step_sha256"] == assembly["step_sha256"]
    assert audit["event_count"] == 46
    assert all(chamber["difference_mm3"] == 0.0 for chamber in audit["chambers"].values())

    print("PASS root package hashes, reproducible outputs, six part paths, final pipeline, and 46-event audit")


if __name__ == "__main__":
    main()
