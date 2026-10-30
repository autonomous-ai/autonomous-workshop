from __future__ import annotations

from typing import Any

from cadgen.analysis import bbox_center, bbox_size, major_planar_face_groups
from cadgen.lookup import build_selector_index


def _coerce_bbox(bbox: object) -> dict[str, object]:
    if not isinstance(bbox, dict):
        raise ValueError("Expected bbox dict with min/max coordinates.")
    if not isinstance(bbox.get("min"), list) or not isinstance(bbox.get("max"), list):
        raise ValueError("BBox dict must include min/max coordinate lists.")
    return bbox


def selector_count(manifest: dict[str, Any], selector_type: str) -> int:
    stats = manifest.get("stats")
    if not isinstance(stats, dict):
        return 0
    if selector_type == "shape":
        return int(stats.get("shapeCount") or 0)
    if selector_type == "face":
        return int(stats.get("faceCount") or 0)
    if selector_type == "edge":
        return int(stats.get("edgeCount") or 0)
    if selector_type == "occurrence":
        return int(stats.get("occurrenceCount") or 0)
    raise ValueError(f"Unsupported selector_type {selector_type!r}")


def geometry_summary_from_manifest(manifest: dict[str, Any]) -> dict[str, object]:
    bbox = _coerce_bbox(manifest.get("bbox"))
    summary: dict[str, object] = {
        "bbox": bbox,
        "center": bbox_center(bbox),
        "size": bbox_size(bbox),
        "occurrenceCount": selector_count(manifest, "occurrence"),
        "shapeCount": selector_count(manifest, "shape"),
        "faceCount": selector_count(manifest, "face"),
        "edgeCount": selector_count(manifest, "edge"),
    }
    try:
        index = build_selector_index(manifest)
    except Exception:  # noqa: BLE001 - a selector-index build failure must not fail the manifest summary
        return summary
    summary["majorPlanes"] = major_planar_face_groups(index)
    return summary
