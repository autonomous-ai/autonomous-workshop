#!/usr/bin/env python3
"""Project-scale printability scoring.

This module estimates print success risk. It is deliberately conservative and
dependency-light: STL analysis uses the Python standard library plus numpy.
CadQuery is only needed for the optional project-export path.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import struct
import sys
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class PrintabilityAssumptions:
    build_volume_mm: tuple[float, float, float] = (220.0, 220.0, 250.0)
    overhang_angle_deg: float = 45.0
    bed_epsilon_mm: float = 0.05
    min_bed_contact_area_mm2: float = 25.0
    tiny_component_area_fraction: float = 0.001
    high_triangle_count: int = 500_000
    severe_bad_boundary_surface_ratio: float = 0.50
    severe_bad_edge_count: int = 32


def _class_for_score(score: float) -> str:
    if score >= 8.0:
        return "easy"
    if score >= 4.0:
        return "hard"
    return "impossible"


def _round_score(value: float) -> float:
    return round(max(0.0, min(10.0, value)), 2)


def _read_stl(path: Path) -> np.ndarray:
    data = path.read_bytes()
    if not data:
        raise ValueError("file is empty")

    triangles = _try_read_ascii_stl(data)
    if triangles is not None:
        return triangles
    return _read_binary_stl(data)


def _try_read_ascii_stl(data: bytes) -> np.ndarray | None:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if "vertex" not in text or "facet" not in text:
        return None

    vertices: list[list[float]] = []
    triangles: list[list[list[float]]] = []
    for line in text.splitlines():
        fields = line.strip().split()
        if len(fields) == 4 and fields[0].lower() == "vertex":
            vertices.append([float(fields[1]), float(fields[2]), float(fields[3])])
            if len(vertices) == 3:
                triangles.append(vertices)
                vertices = []
    if not triangles:
        raise ValueError("ASCII STL has no triangles")
    return np.asarray(triangles, dtype=float)


def _read_binary_stl(data: bytes) -> np.ndarray:
    if len(data) < 84:
        raise ValueError("binary STL is too short")
    count = struct.unpack_from("<I", data, 80)[0]
    expected = 84 + count * 50
    if len(data) < expected:
        raise ValueError(f"binary STL is truncated: expected {expected} bytes, got {len(data)}")

    triangles = np.empty((count, 3, 3), dtype=float)
    offset = 84
    for i in range(count):
        values = struct.unpack_from("<12fH", data, offset)
        triangles[i] = [
            [values[3], values[4], values[5]],
            [values[6], values[7], values[8]],
            [values[9], values[10], values[11]],
        ]
        offset += 50
    return triangles


def _triangle_metrics(triangles: np.ndarray) -> dict:
    a = triangles[:, 0, :]
    b = triangles[:, 1, :]
    c = triangles[:, 2, :]
    cross = np.cross(b - a, c - a)
    double_area = np.linalg.norm(cross, axis=1)
    areas = double_area * 0.5
    normals = np.zeros_like(cross)
    nondegenerate = double_area > 1e-12
    normals[nondegenerate] = cross[nondegenerate] / double_area[nondegenerate, None]
    volume = abs(float(np.sum(np.einsum("ij,ij->i", a, np.cross(b, c))) / 6.0))
    return {
        "areas": areas,
        "normals": normals,
        "surface_area": float(np.sum(areas)),
        "volume": volume,
        "degenerate_triangles": int(np.size(areas) - np.count_nonzero(nondegenerate)),
    }


def _orientation_candidates() -> list[tuple[str, np.ndarray]]:
    return [
        ("z_min", np.array([0.0, 0.0, 1.0])),
        ("z_max", np.array([0.0, 0.0, -1.0])),
        ("x_min", np.array([1.0, 0.0, 0.0])),
        ("x_max", np.array([-1.0, 0.0, 0.0])),
        ("y_min", np.array([0.0, 1.0, 0.0])),
        ("y_max", np.array([0.0, -1.0, 0.0])),
    ]


def _orientation_metrics(
    triangles: np.ndarray,
    areas: np.ndarray,
    normals: np.ndarray,
    total_area: float,
    assumptions: PrintabilityAssumptions,
) -> dict:
    overhang_cos = math.cos(math.radians(180.0 - assumptions.overhang_angle_deg))
    best: dict | None = None
    for name, up_axis in _orientation_candidates():
        heights = np.tensordot(triangles, up_axis, axes=([2], [0]))
        min_h = float(np.min(heights))
        bottom = np.all(np.abs(heights - min_h) <= assumptions.bed_epsilon_mm, axis=1)
        normal_up = normals @ up_axis
        bed_area = float(np.sum(areas[bottom & (normal_up < -0.9)]))
        centroids_h = np.mean(heights, axis=1)
        unsupported = (normal_up < overhang_cos) & (centroids_h > min_h + assumptions.bed_epsilon_mm)
        overhang_area = float(np.sum(areas[unsupported]))
        overhang_fraction = overhang_area / total_area if total_area > 0 else 0.0

        # Prefer orientations that reduce support burden, then improve bed
        # contact. This is intentionally coarse but avoids punishing parts for
        # arbitrary exported pose.
        rank = (overhang_fraction, -bed_area)
        candidate = {
            "name": name,
            "rank": rank,
            "bed_area": bed_area,
            "overhang_area": overhang_area,
            "overhang_fraction": overhang_fraction,
        }
        if best is None or candidate["rank"] < best["rank"]:
            best = candidate

    assert best is not None
    return best


def _vertex_key(v: np.ndarray) -> tuple[float, float, float]:
    return (round(float(v[0]), 6), round(float(v[1]), 6), round(float(v[2]), 6))


def _topology_metrics(
    triangles: np.ndarray,
    areas: np.ndarray,
    assumptions: PrintabilityAssumptions,
) -> dict:
    edge_to_triangles: dict[tuple[tuple[float, float, float], tuple[float, float, float]], list[int]] = {}
    for i, tri in enumerate(triangles):
        keys = [_vertex_key(v) for v in tri]
        for j in range(3):
            e = tuple(sorted((keys[j], keys[(j + 1) % 3])))
            edge_to_triangles.setdefault(e, []).append(i)

    bad_edges = 0
    bad_edge_length = 0.0
    for edge, refs in edge_to_triangles.items():
        if len(refs) != 2:
            bad_edges += 1
            a = np.asarray(edge[0], dtype=float)
            b = np.asarray(edge[1], dtype=float)
            bad_edge_length += float(np.linalg.norm(b - a))
    watertight = bad_edges == 0

    parent = list(range(len(triangles)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for refs in edge_to_triangles.values():
        if len(refs) >= 2:
            base = refs[0]
            for other in refs[1:]:
                union(base, other)

    comps: dict[int, list[int]] = {}
    for i in range(len(triangles)):
        comps.setdefault(find(i), []).append(i)
    component_areas = sorted((float(np.sum(areas[idxs])) for idxs in comps.values()), reverse=True)
    total_area = float(np.sum(areas))
    tiny_threshold = total_area * assumptions.tiny_component_area_fraction
    tiny_components = sum(1 for area in component_areas[1:] if area <= tiny_threshold)
    return {
        "watertight": watertight,
        "bad_edge_count": bad_edges,
        "bad_edge_length_mm": bad_edge_length,
        "connected_components": len(component_areas),
        "component_areas": component_areas,
        "tiny_components": tiny_components,
    }


def _score_mesh(
    path: Path,
    triangles: np.ndarray,
    assumptions: PrintabilityAssumptions,
) -> dict:
    hard_failures: list[str] = []
    risk_factors: list[str] = []
    score = 10.0
    cap = 10.0

    if triangles.size == 0:
        hard_failures.append("mesh has no triangles")
        return _mesh_report(path, 0.0, hard_failures, risk_factors, {"triangle_count": 0}, assumptions)
    if not np.isfinite(triangles).all():
        hard_failures.append("mesh contains non-finite coordinates")
        return _mesh_report(path, 0.0, hard_failures, risk_factors, {"triangle_count": int(len(triangles))}, assumptions)

    tri = _triangle_metrics(triangles)
    topo = _topology_metrics(triangles, tri["areas"], assumptions)
    mins = np.min(triangles.reshape(-1, 3), axis=0)
    maxs = np.max(triangles.reshape(-1, 3), axis=0)
    extents = maxs - mins
    triangle_count = int(len(triangles))

    metrics = {
        "triangle_count": triangle_count,
        "bbox_min": [round(float(x), 4) for x in mins],
        "bbox_max": [round(float(x), 4) for x in maxs],
        "bbox_size": [round(float(x), 4) for x in extents],
        "surface_area_mm2": round(tri["surface_area"], 4),
        "volume_mm3": round(tri["volume"], 4),
        "degenerate_triangles": tri["degenerate_triangles"],
        **{k: v for k, v in topo.items() if k != "component_areas"},
    }

    if np.any(extents <= 1e-9):
        hard_failures.append("mesh has zero thickness in at least one axis")
        cap = min(cap, 3.0)
    if not topo["watertight"]:
        bad_length = float(topo["bad_edge_length_mm"])
        bad_ratio = bad_length / math.sqrt(tri["surface_area"]) if tri["surface_area"] > 0 else 0.0
        metrics["bad_edge_length_mm"] = round(bad_length, 4)
        metrics["bad_boundary_surface_ratio"] = round(bad_ratio, 6)
        if (
            bad_ratio >= assumptions.severe_bad_boundary_surface_ratio
            or int(topo["bad_edge_count"]) >= assumptions.severe_bad_edge_count
        ):
            hard_failures.append("mesh has severe open/non-manifold boundaries")
            cap = min(cap, 4.0)
        else:
            risk_factors.append("mesh has minor non-watertight edges")
    if tri["volume"] <= 1e-9:
        hard_failures.append("mesh has zero enclosed volume")
        cap = min(cap, 3.0)
    if tri["degenerate_triangles"]:
        risk_factors.append(f"{tri['degenerate_triangles']} degenerate triangles")
        score -= min(1.5, 0.05 * tri["degenerate_triangles"])
    if topo["connected_components"] > 1:
        risk_factors.append(f"{topo['connected_components']} disconnected mesh components")
        score -= min(2.5, 0.4 * (topo["connected_components"] - 1))
    if topo["tiny_components"]:
        risk_factors.append(f"{topo['tiny_components']} tiny disconnected components")
        score -= min(2.0, 0.5 * topo["tiny_components"])

    orientation = _orientation_metrics(
        triangles,
        tri["areas"],
        tri["normals"],
        tri["surface_area"],
        assumptions,
    )
    bed_area = orientation["bed_area"]
    metrics["selected_orientation"] = orientation["name"]
    metrics["bed_contact_area_mm2"] = round(bed_area, 4)
    if bed_area < assumptions.min_bed_contact_area_mm2:
        risk_factors.append(
            f"low bed contact area ({bed_area:.2f} mm^2 < {assumptions.min_bed_contact_area_mm2:.2f} mm^2)"
        )
        score -= 2.0

    overhang_area = orientation["overhang_area"]
    overhang_fraction = orientation["overhang_fraction"]
    metrics["unsupported_overhang_area_mm2"] = round(overhang_area, 4)
    metrics["unsupported_overhang_fraction"] = round(overhang_fraction, 6)
    if overhang_fraction > 0.25:
        risk_factors.append(f"high unsupported overhang area ({overhang_fraction:.1%} of surface)")
        score -= min(3.0, overhang_fraction * 6.0)
    elif overhang_fraction > 0.10:
        risk_factors.append(f"moderate unsupported overhang area ({overhang_fraction:.1%} of surface)")
        score -= 0.8

    if triangle_count > assumptions.high_triangle_count:
        risk_factors.append(f"very high triangle count ({triangle_count})")
        score -= 0.8

    score = min(score, cap)
    return _mesh_report(path, _round_score(score), hard_failures, risk_factors, metrics, assumptions)


def _mesh_report(
    path: Path,
    score: float,
    hard_failures: list[str],
    risk_factors: list[str],
    metrics: dict,
    assumptions: PrintabilityAssumptions,
) -> dict:
    return {
        "path": str(path),
        "score": _round_score(score),
        "class": _class_for_score(score),
        "hard_failures": hard_failures,
        "risk_factors": risk_factors,
        "metrics": metrics,
        "assumptions": asdict(assumptions),
    }


def score_mesh_file(
    path: str | os.PathLike,
    assumptions: PrintabilityAssumptions | None = None,
) -> dict:
    assumptions = assumptions or PrintabilityAssumptions()
    p = Path(path)
    try:
        triangles = _read_stl(p)
        return _score_mesh(p, triangles, assumptions)
    except Exception as exc:
        return _mesh_report(
            p,
            0.0,
            [f"failed to load STL: {exc}"],
            [],
            {"triangle_count": 0},
            assumptions,
        )


def _project_report(
    assembly_report: dict | None,
    part_reports: list[dict],
    assumptions: PrintabilityAssumptions,
) -> dict:
    hard_failures: list[str] = []
    risk_factors: list[str] = []
    scores: list[float] = []

    if assembly_report is not None:
        scores.append(float(assembly_report["score"]))
        hard_failures.extend(assembly_report["hard_failures"])
        risk_factors.extend(f"assembly: {r}" for r in assembly_report["risk_factors"])
    else:
        risk_factors.append("no assembly STL supplied")

    if part_reports:
        part_scores = [float(p["score"]) for p in part_reports]
        scores.extend(part_scores)
        if any(
            "mesh has severe open/non-manifold boundaries" in p["hard_failures"]
            for p in part_reports
        ):
            hard_failures.append("one or more parts have severe open/non-manifold boundaries")
        for i, part in enumerate(part_reports):
            for failure in part["hard_failures"]:
                hard_failures.append(f"part {i}: {failure}")
            for risk in part["risk_factors"]:
                risk_factors.append(f"part {i}: {risk}")

    if not scores:
        score = 0.0
        hard_failures.append("no assembly or part STL files supplied")
    else:
        worst = min(scores)
        avg = sum(scores) / len(scores)
        score = 0.7 * worst + 0.3 * avg

    if part_reports and assembly_report is not None:
        assembly_components = assembly_report["metrics"].get("connected_components")
        if assembly_components is not None and assembly_components != len(part_reports):
            risk_factors.append(
                f"assembly has {assembly_components} connected components but {len(part_reports)} part files were supplied"
            )
            score -= 0.7

    cap = 10.0
    if any("failed to load STL" in f for f in hard_failures):
        cap = min(cap, 1.0)
    if any("zero enclosed volume" in f or "zero thickness" in f for f in hard_failures):
        cap = min(cap, 3.0)
    if any("severe open/non-manifold boundaries" in f for f in hard_failures):
        cap = min(cap, 4.0)

    score = _round_score(min(score, cap))
    return {
        "score": score,
        "class": _class_for_score(score),
        "hard_failures": list(dict.fromkeys(hard_failures)),
        "risk_factors": list(dict.fromkeys(risk_factors)),
        "assembly": assembly_report,
        "parts": part_reports,
        "assumptions": asdict(assumptions),
    }


def score_project(
    assembly: str | os.PathLike | None = None,
    parts: Iterable[str | os.PathLike] | None = None,
    assumptions: PrintabilityAssumptions | None = None,
) -> dict:
    assumptions = assumptions or PrintabilityAssumptions()
    assembly_report = score_mesh_file(assembly, assumptions) if assembly else None
    part_reports = [score_mesh_file(p, assumptions) for p in (parts or [])]
    return _project_report(assembly_report, part_reports, assumptions)


def score_manifest(path: str | os.PathLike, assumptions: PrintabilityAssumptions | None = None) -> dict:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text())
    root = manifest_path.parent
    assembly = data.get("assembly")
    parts = data.get("parts", [])
    assembly_path = root / assembly if assembly else None
    part_paths = [root / p for p in parts]
    return score_project(assembly_path, part_paths, assumptions)


def score_cadquery_project(
    project_dir: str | os.PathLike,
    assumptions: PrintabilityAssumptions | None = None,
    tolerance: float = 0.1,
    angular: float = 0.2,
) -> dict:
    assumptions = assumptions or PrintabilityAssumptions()
    try:
        import cadquery as cq
    except ImportError as exc:
        raise RuntimeError("cadquery is required for --cadquery-project") from exc

    project = Path(project_dir).resolve()
    if str(project) not in sys.path:
        sys.path.insert(0, str(project))
    for module in ("params", "main", "validation"):
        sys.modules.pop(module, None)
    gen_step = __import__("main").gen_step
    shape = gen_step()
    if isinstance(shape, dict):
        if "shape" not in shape:
            raise RuntimeError("cadquery project gen_step() returned a dict without a 'shape' key")
        shape = shape["shape"]
    if isinstance(shape, cq.Assembly):
        compound = shape.toCompound()
    elif isinstance(shape, cq.Workplane):
        compound = shape.val()
    else:
        compound = shape
    solids = compound.Solids()

    with tempfile.TemporaryDirectory(prefix="printability_") as tmp:
        tmp_path = Path(tmp)
        assembly = tmp_path / "assembly.stl"
        cq.exporters.export(cq.Workplane(obj=compound), str(assembly), tolerance=tolerance, angularTolerance=angular)
        parts = []
        for i, solid in enumerate(solids):
            part = tmp_path / f"part_{i}.stl"
            cq.exporters.export(cq.Workplane(obj=solid), str(part), tolerance=tolerance, angularTolerance=angular)
            parts.append(part)
        report = score_project(assembly, parts, assumptions)
        report["source_project"] = str(project)
        return report


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score project-scale STL printability.")
    parser.add_argument("--assembly", help="assembled STL path")
    parser.add_argument("--parts", nargs="*", default=None, help="separate part STL paths")
    parser.add_argument("--manifest", help="JSON manifest with assembly and parts")
    parser.add_argument("--cadquery-project", help="CadQuery project directory with main.py/gen_step()")
    parser.add_argument("--build-volume", default="220,220,250", help="build volume in mm as X,Y,Z")
    parser.add_argument("--json-out", help="optional output JSON path")
    return parser


def _assumptions_from_args(args: argparse.Namespace) -> PrintabilityAssumptions:
    try:
        dims = tuple(float(x) for x in args.build_volume.split(","))
    except ValueError as exc:
        raise SystemExit("--build-volume must be formatted as X,Y,Z") from exc
    if len(dims) != 3:
        raise SystemExit("--build-volume must contain exactly three numbers")
    return PrintabilityAssumptions(build_volume_mm=dims)  # type: ignore[arg-type]


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    assumptions = _assumptions_from_args(args)
    modes = [bool(args.manifest), bool(args.cadquery_project), bool(args.assembly or args.parts)]
    if sum(modes) != 1:
        parser.error("choose exactly one input mode: --manifest, --cadquery-project, or --assembly/--parts")

    if args.manifest:
        report = score_manifest(args.manifest, assumptions)
    elif args.cadquery_project:
        try:
            report = score_cadquery_project(args.cadquery_project, assumptions)
        except RuntimeError as exc:
            parser.exit(2, f"error: {exc}\n")
    else:
        report = score_project(args.assembly, args.parts or [], assumptions)

    text = json.dumps(report, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
