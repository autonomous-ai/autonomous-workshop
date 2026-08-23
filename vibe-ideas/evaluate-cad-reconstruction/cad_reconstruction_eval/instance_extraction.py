#!/usr/bin/env python3
"""Extract manifest-ready component STLs from assembled STL files."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import numpy as np

from cad_reconstruction_eval.printability_score import _read_stl, _triangle_metrics


def _normal(triangle: np.ndarray) -> np.ndarray:
    a, b, c = triangle
    cross = np.cross(b - a, c - a)
    length = float(np.linalg.norm(cross))
    if length <= 1e-12:
        return np.asarray([0.0, 0.0, 0.0])
    return cross / length


def write_ascii_stl(path: Path, triangles: np.ndarray, solid_name: str = "component") -> None:
    lines = [f"solid {solid_name}"]
    for tri in triangles:
        n = _normal(tri)
        lines.append(f"  facet normal {n[0]:.12g} {n[1]:.12g} {n[2]:.12g}")
        lines.append("    outer loop")
        for vertex in tri:
            lines.append(f"      vertex {vertex[0]:.12g} {vertex[1]:.12g} {vertex[2]:.12g}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append(f"endsolid {solid_name}")
    path.write_text("\n".join(lines) + "\n")


def _vertex_key(vertex: np.ndarray, precision: int) -> tuple[float, float, float]:
    rounded = np.round(vertex.astype(float), precision)
    return (float(rounded[0]), float(rounded[1]), float(rounded[2]))


def connected_triangle_components(triangles: np.ndarray, precision: int = 6) -> list[np.ndarray]:
    """Return triangle-index components connected by shared rounded edges."""
    edge_to_triangles: dict[
        tuple[tuple[float, float, float], tuple[float, float, float]], list[int]
    ] = defaultdict(list)
    for index, tri in enumerate(triangles):
        keys = [_vertex_key(vertex, precision) for vertex in tri]
        for vertex_index in range(3):
            edge = tuple(sorted((keys[vertex_index], keys[(vertex_index + 1) % 3])))
            edge_to_triangles[edge].append(index)

    visited = np.zeros(len(triangles), dtype=bool)
    components: list[np.ndarray] = []
    for start in range(len(triangles)):
        if visited[start]:
            continue
        queue: deque[int] = deque([start])
        visited[start] = True
        indices: list[int] = []
        while queue:
            index = queue.popleft()
            indices.append(index)
            keys = [_vertex_key(vertex, precision) for vertex in triangles[index]]
            for vertex_index in range(3):
                edge = tuple(sorted((keys[vertex_index], keys[(vertex_index + 1) % 3])))
                for neighbor in edge_to_triangles[edge]:
                    if not visited[neighbor]:
                        visited[neighbor] = True
                        queue.append(neighbor)
        components.append(np.asarray(indices, dtype=int))
    return components


def _component_record(name: str, path: Path, triangles: np.ndarray, source_indices: np.ndarray) -> dict[str, Any]:
    metrics = _triangle_metrics(triangles)
    points = triangles.reshape(-1, 3)
    bbox_min = np.min(points, axis=0)
    bbox_max = np.max(points, axis=0)
    return {
        "name": name,
        "path": str(path),
        "triangle_count": int(len(triangles)),
        "source_triangle_indices": [int(i) for i in source_indices.tolist()],
        "surface_area": round(float(metrics["surface_area"]), 6),
        "volume": round(float(metrics["volume"]), 6),
        "bbox_min": [round(float(v), 6) for v in bbox_min],
        "bbox_max": [round(float(v), 6) for v in bbox_max],
    }


def extract_component_stls(
    assembly_stl: str | Path,
    out_dir: str | Path,
    *,
    prefix: str = "component",
    precision: int = 6,
    min_triangles: int = 1,
) -> dict[str, Any]:
    assembly_path = Path(assembly_stl)
    output_dir = Path(out_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    triangles = _read_stl(assembly_path)
    components = connected_triangle_components(triangles, precision=precision)
    components.sort(
        key=lambda indices: (
            -float(_triangle_metrics(triangles[indices])["surface_area"]),
            int(indices[0]) if len(indices) else 0,
        )
    )

    records: list[dict[str, Any]] = []
    parts: dict[str, str] = {}
    for output_index, indices in enumerate(components):
        if len(indices) < min_triangles:
            continue
        name = f"{prefix}_{output_index:03d}"
        path = output_dir / f"{name}.stl"
        component_triangles = triangles[indices]
        write_ascii_stl(path, component_triangles, solid_name=name)
        records.append(_component_record(name, path, component_triangles, indices))
        parts[name] = str(path)

    return {
        "source_assembly": str(assembly_path),
        "output_dir": str(output_dir),
        "precision": precision,
        "source_triangle_count": int(len(triangles)),
        "component_count": len(records),
        "parts": parts,
        "components": records,
        "limitations": [
            "STL component extraction groups triangles by shared vertices only.",
            "It cannot recover semantic instances that are touching, fused, or only present in STEP/CadQuery assembly structure.",
            "Names are size-order component labels, not original CAD part names.",
        ],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Split an assembled STL into connected component STLs.")
    parser.add_argument("assembly_stl", type=Path)
    parser.add_argument("out_dir", type=Path)
    parser.add_argument("--prefix", default="component")
    parser.add_argument("--precision", type=int, default=6)
    parser.add_argument("--min-triangles", type=int, default=1)
    parser.add_argument("--json-out", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    report = extract_component_stls(
        args.assembly_stl,
        args.out_dir,
        prefix=args.prefix,
        precision=args.precision,
        min_triangles=args.min_triangles,
    )
    text = json.dumps(report, indent=2)
    if args.json_out:
        args.json_out.write_text(text)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
