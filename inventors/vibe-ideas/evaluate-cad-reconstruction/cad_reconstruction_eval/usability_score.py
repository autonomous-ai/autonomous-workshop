#!/usr/bin/env python3
"""Geometry-only project physical-usability scoring.

Layer 1 deliberately avoids source intent. It checks whether supplied STL
parts can plausibly coexist as a project: part inventory, assembled component
count, and basic mesh loadability.

This module is kept as a compatibility layer for the earlier
``score_usability.py`` entry point. New code should import
``cad_reconstruction_eval.physical_correctness_score``.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np

from cad_reconstruction_eval.printability_score import (
    PrintabilityAssumptions,
    _class_for_score,
    _read_stl,
    _round_score,
    _topology_metrics,
    _triangle_metrics,
)


@dataclass(frozen=True)
class UsabilityAssumptions:
    component_count_mismatch_penalty: float = 1.0
    missing_parts_component_penalty: float = 0.5
    max_missing_parts_component_penalty: float = 2.0


def _mesh_geometry_report(path: str | os.PathLike) -> dict:
    p = Path(path)
    try:
        triangles = _read_stl(p)
    except Exception as exc:
        return {
            "path": str(p),
            "loadable": False,
            "hard_failures": [f"failed to load STL: {exc}"],
            "metrics": {"triangle_count": 0},
        }

    tri = _triangle_metrics(triangles)
    topo = _topology_metrics(triangles, tri["areas"], PrintabilityAssumptions())
    points = triangles.reshape(-1, 3)
    mins = np.min(points, axis=0)
    maxs = np.max(points, axis=0)
    extents = maxs - mins
    return {
        "path": str(p),
        "loadable": True,
        "hard_failures": [],
        "metrics": {
            "triangle_count": int(len(triangles)),
            "bbox_min": [round(float(x), 4) for x in mins],
            "bbox_max": [round(float(x), 4) for x in maxs],
            "bbox_size": [round(float(x), 4) for x in extents],
            "bbox_volume_mm3": round(_bbox_volume(mins, maxs), 4),
            "surface_area_mm2": round(float(tri["surface_area"]), 4),
            "volume_mm3": round(float(tri["volume"]), 4),
            "connected_components": topo["connected_components"],
            "watertight": topo["watertight"],
            "bad_edge_count": topo["bad_edge_count"],
        },
    }


def _bbox_volume(mins: np.ndarray, maxs: np.ndarray) -> float:
    extents = np.maximum(maxs - mins, 0.0)
    return float(np.prod(extents))


def _is_assembly_proxy_part(assembly: str | os.PathLike | None, parts: list[str | os.PathLike]) -> bool:
    if assembly is None or len(parts) != 1:
        return False
    try:
        return Path(assembly).resolve() == Path(parts[0]).resolve()
    except OSError:
        return False


def score_usability_project(
    assembly: str | os.PathLike | None = None,
    parts: Iterable[str | os.PathLike] | None = None,
    assumptions: UsabilityAssumptions | None = None,
) -> dict:
    assumptions = assumptions or UsabilityAssumptions()
    part_paths = list(parts or [])
    assembly_report = _mesh_geometry_report(assembly) if assembly else None
    part_reports = [_mesh_geometry_report(p) for p in part_paths]

    hard_failures: list[str] = []
    risk_factors: list[str] = []
    score = 10.0

    if assembly_report is None and not part_reports:
        hard_failures.append("no assembly or part STL files supplied")
        score = 0.0

    if assembly_report is None:
        risk_factors.append("no assembly STL supplied")
        score -= 0.5
    elif not assembly_report["loadable"]:
        hard_failures.extend(assembly_report["hard_failures"])
        score = min(score, 1.0)

    for i, part in enumerate(part_reports):
        if not part["loadable"]:
            hard_failures.extend(f"part {i}: {failure}" for failure in part["hard_failures"])
            score = min(score, 1.0)

    if assembly_report is not None and assembly_report.get("loadable") and part_reports:
        assembly_components = int(assembly_report["metrics"]["connected_components"])
        if assembly_components != len(part_reports) and not _is_assembly_proxy_part(assembly, part_paths):
            risk_factors.append(
                f"assembly has {assembly_components} connected components but {len(part_reports)} part files were supplied"
            )
            score -= assumptions.component_count_mismatch_penalty
    elif assembly_report is not None and assembly_report.get("loadable"):
        assembly_components = int(assembly_report["metrics"]["connected_components"])
        if assembly_components > 1:
            risk_factors.append(
                f"assembly has {assembly_components} disconnected components but no separate part STLs were supplied"
            )
            score -= min(
                assumptions.max_missing_parts_component_penalty,
                assumptions.missing_parts_component_penalty * (assembly_components - 1),
            )

    score = _round_score(score)
    metrics = {
        "part_count": len(part_reports),
    }

    return {
        "score": score,
        "class": _class_for_score(score),
        "hard_failures": list(dict.fromkeys(hard_failures)),
        "risk_factors": list(dict.fromkeys(risk_factors)),
        "metrics": metrics,
        "assembly": assembly_report,
        "parts": part_reports,
        "assumptions": asdict(assumptions),
    }


def score_usability_manifest(
    path: str | os.PathLike,
    assumptions: UsabilityAssumptions | None = None,
) -> dict:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text())
    root = manifest_path.parent
    assembly = data.get("assembly")
    parts = data.get("parts", [])
    assembly_path = root / assembly if assembly else None
    part_paths = [root / p for p in parts]
    return score_usability_project(assembly_path, part_paths, assumptions)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score Layer 1 geometry-only project usability.")
    parser.add_argument("--assembly", help="assembled STL path")
    parser.add_argument("--parts", nargs="*", default=None, help="separate part STL paths")
    parser.add_argument("--manifest", help="JSON manifest with assembly and parts")
    parser.add_argument("--json-out", help="optional output JSON path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if bool(args.manifest) == bool(args.assembly or args.parts):
        parser.error("choose exactly one input mode: --manifest or --assembly/--parts")

    if args.manifest:
        report = score_usability_manifest(args.manifest)
    else:
        report = score_usability_project(args.assembly, args.parts or [])

    text = json.dumps(report, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
