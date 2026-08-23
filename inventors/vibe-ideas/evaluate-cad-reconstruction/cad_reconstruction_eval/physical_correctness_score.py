#!/usr/bin/env python3
"""Physical-correctness scoring for reconstructed CAD/STL projects.

The pipeline is condition-driven:
1. An upstream reviewer/LLM writes explicit physical conditions.
2. This module runs deterministic helper checks for those conditions.
3. The scorer combines condition results with baseline Layer 1 geometry checks.

This module intentionally does not judge functional-feature preservation.
"""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from cad_reconstruction_eval.printability_score import (
    PrintabilityAssumptions,
    _read_stl,
    _topology_metrics,
    _triangle_metrics,
)
from cad_reconstruction_eval.usability_score import (
    UsabilityAssumptions,
    _mesh_geometry_report,
    score_usability_project,
)


@dataclass(frozen=True)
class PhysicalCorrectnessAssumptions:
    critical_failure_cap: float = 4.0
    major_failure_penalty: float = 2.0
    minor_failure_penalty: float = 0.8
    inconclusive_penalty: float = 0.3
    max_sample_points: int = 500
    max_sample_triangles: int = 1000
    collision_epsilon_mm: float = 1e-6
    collision_probe_distance_mm: float = 0.1


def _class_for_score(score: float) -> str:
    if score >= 8.0:
        return "easy"
    if score >= 4.0:
        return "hard"
    return "impossible"


def _round_score(score: float) -> float:
    return round(max(0.0, min(10.0, score)), 2)


def _severity_penalty(severity: str, assumptions: PhysicalCorrectnessAssumptions) -> float:
    if severity == "critical":
        return 10.0 - assumptions.critical_failure_cap
    if severity == "major":
        return assumptions.major_failure_penalty
    if severity == "minor":
        return assumptions.minor_failure_penalty
    return assumptions.minor_failure_penalty


def _resolve_part(parts_by_name: dict[str, dict], name: str) -> dict | None:
    return parts_by_name.get(name)


def _load_part_triangles(parts_by_name: dict[str, dict], name: str) -> tuple[np.ndarray | None, str | None]:
    part = _resolve_part(parts_by_name, name)
    if part is None:
        return None, f"missing part: {name}"
    if not part.get("loadable"):
        return None, f"part failed to load: {name}"
    try:
        return _read_stl(Path(part["path"])), None
    except Exception as exc:
        return None, f"failed to load part {name}: {exc}"


def _sample_rows(values: np.ndarray, limit: int) -> np.ndarray:
    if len(values) <= limit:
        return values
    idx = np.linspace(0, len(values) - 1, limit, dtype=int)
    return values[idx]


def _sample_points(triangles: np.ndarray, limit: int) -> np.ndarray:
    points = np.unique(np.round(triangles.reshape(-1, 3), 8), axis=0)
    return _sample_rows(points, limit)


def _sample_triangles(triangles: np.ndarray, limit: int) -> np.ndarray:
    return _sample_rows(triangles, limit)


def _point_triangle_distance(point: np.ndarray, tri: np.ndarray) -> float:
    # Real-Time Collision Detection, Christer Ericson, closest point on triangle.
    a, b, c = tri
    ab = b - a
    ac = c - a
    ap = point - a
    d1 = float(np.dot(ab, ap))
    d2 = float(np.dot(ac, ap))
    if d1 <= 0.0 and d2 <= 0.0:
        return float(np.linalg.norm(point - a))

    bp = point - b
    d3 = float(np.dot(ab, bp))
    d4 = float(np.dot(ac, bp))
    if d3 >= 0.0 and d4 <= d3:
        return float(np.linalg.norm(point - b))

    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return float(np.linalg.norm(point - (a + v * ab)))

    cp = point - c
    d5 = float(np.dot(ab, cp))
    d6 = float(np.dot(ac, cp))
    if d6 >= 0.0 and d5 <= d6:
        return float(np.linalg.norm(point - c))

    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return float(np.linalg.norm(point - (a + w * ac)))

    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        w = (d4 - d3) / ((d4 - d3) + (d5 - d6))
        return float(np.linalg.norm(point - (b + w * (c - b))))

    denom = 1.0 / (va + vb + vc)
    v = vb * denom
    w = vc * denom
    closest = a + ab * v + ac * w
    return float(np.linalg.norm(point - closest))


def _mesh_min_distance(
    a: np.ndarray,
    b: np.ndarray,
    assumptions: PhysicalCorrectnessAssumptions,
) -> float:
    points_a = _sample_points(a, assumptions.max_sample_points)
    points_b = _sample_points(b, assumptions.max_sample_points)
    tris_a = _sample_triangles(a, assumptions.max_sample_triangles)
    tris_b = _sample_triangles(b, assumptions.max_sample_triangles)
    best = float("inf")
    for point in points_a:
        for tri in tris_b:
            best = min(best, _point_triangle_distance(point, tri))
            if best <= assumptions.collision_epsilon_mm:
                return 0.0
    for point in points_b:
        for tri in tris_a:
            best = min(best, _point_triangle_distance(point, tri))
            if best <= assumptions.collision_epsilon_mm:
                return 0.0
    return best


def _ray_intersects_triangle(origin: np.ndarray, direction: np.ndarray, tri: np.ndarray, eps: float = 1e-9) -> bool:
    v0, v1, v2 = tri
    edge1 = v1 - v0
    edge2 = v2 - v0
    h = np.cross(direction, edge2)
    a = float(np.dot(edge1, h))
    if -eps < a < eps:
        return False
    f = 1.0 / a
    s = origin - v0
    u = f * float(np.dot(s, h))
    if u < eps or u > 1.0 - eps:
        return False
    q = np.cross(s, edge1)
    v = f * float(np.dot(direction, q))
    if v < eps or u + v > 1.0 - eps:
        return False
    t = f * float(np.dot(edge2, q))
    return t > eps


def _segment_intersects_triangle(start: np.ndarray, end: np.ndarray, tri: np.ndarray, eps: float = 1e-9) -> bool:
    vector = end - start
    length = float(np.linalg.norm(vector))
    if length <= eps:
        return False
    direction = vector / length
    v0, v1, v2 = tri
    edge1 = v1 - v0
    edge2 = v2 - v0
    h = np.cross(direction, edge2)
    a = float(np.dot(edge1, h))
    if -eps < a < eps:
        return False
    f = 1.0 / a
    s = start - v0
    u = f * float(np.dot(s, h))
    if u < eps or u > 1.0 - eps:
        return False
    q = np.cross(s, edge1)
    v = f * float(np.dot(direction, q))
    if v < eps or u + v > 1.0 - eps:
        return False
    t = f * float(np.dot(edge2, q))
    return eps < t < length - eps


def _triangles_overlapping_segment_bounds(
    triangles: np.ndarray,
    start: np.ndarray,
    end: np.ndarray,
    eps: float = 1e-9,
) -> np.ndarray:
    segment_min = np.minimum(start, end) - eps
    segment_max = np.maximum(start, end) + eps
    tri_min = np.min(triangles, axis=1)
    tri_max = np.max(triangles, axis=1)
    mask = np.all(tri_max >= segment_min, axis=1) & np.all(tri_min <= segment_max, axis=1)
    return triangles[mask]


def _point_inside_mesh(point: np.ndarray, triangles: np.ndarray) -> bool:
    direction = np.asarray([1.0, 0.3713906764, 0.1135923668], dtype=float)
    direction = direction / np.linalg.norm(direction)
    count = 0
    shifted = point + np.asarray([1e-7, -2e-7, 3e-7], dtype=float)
    for tri in triangles:
        if _ray_intersects_triangle(shifted, direction, tri):
            count += 1
    return count % 2 == 1


def _meshes_collide(
    a: np.ndarray,
    b: np.ndarray,
    assumptions: PhysicalCorrectnessAssumptions,
) -> bool:
    if _mesh_min_distance(a, b, assumptions) > assumptions.collision_probe_distance_mm:
        return False
    tris_a = _sample_triangles(a, assumptions.max_sample_triangles)
    tris_b = _sample_triangles(b, assumptions.max_sample_triangles)
    for point in _sample_points(a, assumptions.max_sample_points):
        if _point_inside_mesh(point, tris_b):
            return True
    for point in _sample_points(b, assumptions.max_sample_points):
        if _point_inside_mesh(point, tris_a):
            return True
    return False


def _load_two_named_parts(
    condition: dict,
    parts_by_name: dict[str, dict],
    key_a: str = "part_a",
    key_b: str = "part_b",
) -> tuple[str | None, str | None, np.ndarray | None, np.ndarray | None, dict | None]:
    inputs = condition.get("inputs", {})
    name_a = inputs.get(key_a)
    name_b = inputs.get(key_b)
    if not name_a or not name_b:
        return None, None, None, None, _condition_result(
            condition, "inconclusive", f"{condition.get('check')} requires {key_a} and {key_b}"
        )
    tri_a, err_a = _load_part_triangles(parts_by_name, name_a)
    tri_b, err_b = _load_part_triangles(parts_by_name, name_b)
    errors = [err for err in (err_a, err_b) if err]
    if errors:
        return name_a, name_b, None, None, _condition_result(condition, "inconclusive", "; ".join(errors))
    return name_a, name_b, tri_a, tri_b, None


def _normalize_vector(values: Any) -> tuple[np.ndarray | None, str | None]:
    try:
        vector = np.asarray(values, dtype=float)
    except Exception:
        return None, "vector must be numeric"
    if vector.shape != (3,):
        return None, "vector must be [x, y, z]"
    length = float(np.linalg.norm(vector))
    if length <= 1e-12:
        return None, "vector must be non-zero"
    return vector / length, None


def _parse_vector(values: Any, label: str) -> tuple[np.ndarray | None, str | None]:
    try:
        vector = np.asarray(values, dtype=float)
    except Exception:
        return None, f"{label} must be numeric"
    if vector.shape != (3,):
        return None, f"{label} must be [x, y, z]"
    return vector, None


def _mesh_centroid(triangles: np.ndarray) -> np.ndarray:
    return np.mean(triangles.reshape(-1, 3), axis=0)


def _rotate_points(points: np.ndarray, axis_point: np.ndarray, axis_direction: np.ndarray, angle_deg: float) -> np.ndarray:
    theta = np.deg2rad(angle_deg)
    rel = points - axis_point
    k = axis_direction / np.linalg.norm(axis_direction)
    cos_t = np.cos(theta)
    sin_t = np.sin(theta)
    return (
        axis_point
        + rel * cos_t
        + np.cross(k, rel) * sin_t
        + k * np.sum(rel * k, axis=-1, keepdims=True) * (1.0 - cos_t)
    )


def _rotate_triangles(
    triangles: np.ndarray,
    axis_point: np.ndarray,
    axis_direction: np.ndarray,
    angle_deg: float,
) -> np.ndarray:
    flat = triangles.reshape(-1, 3)
    rotated = _rotate_points(flat, axis_point, axis_direction, angle_deg)
    return rotated.reshape(triangles.shape)


def _line_to_line_distance(point_a: np.ndarray, direction_a: np.ndarray, point_b: np.ndarray, direction_b: np.ndarray) -> float:
    cross = np.cross(direction_a, direction_b)
    denom = float(np.linalg.norm(cross))
    delta = point_b - point_a
    if denom <= 1e-12:
        return float(np.linalg.norm(np.cross(delta, direction_a)))
    return abs(float(np.dot(delta, cross / denom)))


def _regular_polygon_vertices(across_flats: float, sides: int) -> np.ndarray:
    """2D vertices of a regular N-gon with the given across-flats width.

    Uses the same angular reference (first vertex at 90 deg, CCW) as the
    hex-prism/hex-pocket/hex-hole builders in this project's ``parts/`` and
    ``features/`` modules, so a peg/hole pair built with matching formulas is
    correctly represented as aligned at rotation 0.
    """
    r = across_flats / (2.0 * np.cos(np.pi / sides))
    angles = np.pi / 2.0 + np.arange(sides) * (2.0 * np.pi / sides)
    return np.stack([r * np.cos(angles), r * np.sin(angles)], axis=1)


def _point_in_convex_polygon(point: np.ndarray, polygon: np.ndarray, eps: float = 1e-9) -> bool:
    n = len(polygon)
    for i in range(n):
        a = polygon[i]
        b = polygon[(i + 1) % n]
        edge = b - a
        to_point = point - a
        cross = edge[0] * to_point[1] - edge[1] * to_point[0]
        if cross < -eps:
            return False
    return True

def _polygon_shaft_max_rotation_deg(
    peg_across_flats: float,
    hole_across_flats: float,
    sides: int,
    direction: float,
) -> float:
    """Largest angle (in ``direction``, degrees) the peg can rotate about a
    shared center from the aligned pose before any peg vertex leaves the
    (convex) hole polygon. Returns 0.0 if the peg does not fit even aligned.

    A regular N-gon peg inside a regular N-gon hole repeats every
    ``360/sides`` degrees, and by construction (both shapes share the same
    angular reference) the worst-case, most-interfering angle within one
    period is exactly halfway between two successive aligned positions
    (``180/sides`` degrees). If the peg still fits there, it clears every
    angle and can rotate indefinitely (a true bearing fit); this is reported
    as unbounded (represented as 360.0 degrees, i.e. continuous rotation).
    Otherwise the boundary is found by binary search over ``[0, 180/sides]``.
    """
    peg = _regular_polygon_vertices(peg_across_flats, sides)
    hole = _regular_polygon_vertices(hole_across_flats, sides)
    half_period_deg = 180.0 / sides

    def all_inside(angle_deg: float) -> bool:
        theta = np.deg2rad(angle_deg * direction)
        c, s = np.cos(theta), np.sin(theta)
        rot = np.array([[c, -s], [s, c]])
        rotated = peg @ rot.T
        return all(_point_in_convex_polygon(v, hole) for v in rotated)

    if not all_inside(0.0):
        return 0.0
    if all_inside(half_period_deg):
        # Peg clears the worst-case (half-period) angle: unbounded rotation.
        return 360.0
    lo, hi = 0.0, half_period_deg
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if all_inside(mid):
            lo = mid
        else:
            hi = mid
    return lo


def _check_hex_shaft_rotational_clearance(condition: dict) -> dict:
    """Deterministic 2D proxy for a regular-polygon (hex by default) shaft
    rotating inside a matching regular-polygon hole/pocket of the same
    angular orientation reference, e.g. a hex axle inside a hex through-hole
    or hex hub pocket.

    This is a narrow, local, analytic helper (no mesh sampling): it computes
    the exact free-rotation window from across-flats dimensions using convex
    polygon containment, and is not subject to STL triangle-subsampling
    limitations that make mesh-based rotation_motion_collision unreliable
    for small features buried in a large obstacle mesh (e.g. a hex hole in a
    big base plate).

    Limitations: assumes the peg and hole share a common rotation axis and
    the same angular reference used at rotation 0 (true for this project's
    hex features, which all reuse the same ``pi/2 + i*pi/3`` formula). It
    does not model chamfers/lead-ins, print-tolerance variation, or
    out-of-plane tilt.
    """
    inputs = condition.get("inputs", {})
    try:
        peg_af = float(inputs["peg_across_flats_mm"])
        hole_af = float(inputs["hole_across_flats_mm"])
    except Exception:
        return _condition_result(
            condition, "inconclusive",
            "hex_shaft_rotational_clearance requires numeric peg_across_flats_mm and hole_across_flats_mm",
        )
    sides = int(inputs.get("sides", 6))
    if sides < 3:
        return _condition_result(condition, "inconclusive", "sides must be >= 3")
    if hole_af <= 0 or peg_af <= 0:
        return _condition_result(condition, "inconclusive", "across-flats values must be > 0")

    plus_deg = _polygon_shaft_max_rotation_deg(peg_af, hole_af, sides, direction=1.0)
    minus_deg = _polygon_shaft_max_rotation_deg(peg_af, hole_af, sides, direction=-1.0)
    continuous = plus_deg >= 360.0 or minus_deg >= 360.0
    total_deg = 360.0 if continuous else plus_deg + minus_deg

    thresholds = condition.get("thresholds", {})
    min_total = thresholds.get("min_total_rotation_deg")
    max_total = thresholds.get("max_total_rotation_deg")
    passed = True
    if min_total is not None:
        passed = passed and total_deg >= float(min_total)
    if max_total is not None:
        passed = passed and total_deg <= float(max_total)
    if min_total is None and max_total is None:
        passed = total_deg >= 360.0

    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"free rotation window +{plus_deg:.3f} deg / -{minus_deg:.3f} deg "
        f"(total {total_deg:.3f} deg) for a {sides}-gon peg (AF={peg_af} mm) "
        f"in a {sides}-gon hole (AF={hole_af} mm)",
        {
            "peg_across_flats_mm": peg_af,
            "hole_across_flats_mm": hole_af,
            "sides": sides,
            "free_rotation_plus_deg": round(float(plus_deg), 4),
            "free_rotation_minus_deg": round(float(minus_deg), 4),
            "free_rotation_total_deg": round(float(total_deg), 4),
            "continuous_rotation_capable": continuous,
            "min_total_rotation_deg": float(min_total) if min_total is not None else None,
            "max_total_rotation_deg": float(max_total) if max_total is not None else None,
            "proxy_limitation": (
                "analytic 2D cross-section proxy assuming a shared axis and matching angular "
                "reference; does not model chamfers/lead-ins, print tolerance, or axial tilt"
            ),
        },
    )


def _check_part_component_count(condition: dict, parts_by_name: dict[str, dict]) -> dict:
    name = condition.get("inputs", {}).get("part")
    if not name:
        return _condition_result(condition, "inconclusive", "part_component_count requires part")
    triangles, error = _load_part_triangles(parts_by_name, name)
    if error:
        return _condition_result(condition, "inconclusive", error)
    assert triangles is not None
    tri = _triangle_metrics(triangles)
    topo = _topology_metrics(triangles, tri["areas"], PrintabilityAssumptions())
    expected = int(condition.get("thresholds", {}).get("expected_components", 1))
    actual = int(topo["connected_components"])
    status = "pass" if actual == expected else "fail"
    return _condition_result(
        condition,
        status,
        f"part {name} connected components {actual} {'==' if status == 'pass' else '!='} expected {expected}",
        {"part": name, "actual_components": actual, "expected_components": expected},
    )


def _check_part_collision(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    name_a, name_b, tri_a, tri_b, error = _load_two_named_parts(condition, parts_by_name)
    if error is not None:
        return error
    assert name_a is not None and name_b is not None and tri_a is not None and tri_b is not None
    collides = _meshes_collide(tri_a, tri_b, assumptions)
    return _condition_result(
        condition,
        "fail" if collides else "pass",
        f"sampled mesh collision {'detected' if collides else 'not detected'}",
        {"part_a": name_a, "part_b": name_b, "collides": collides},
    )


def _filter_triangles_above_z(triangles: np.ndarray, min_z: float) -> np.ndarray:
    """Drop triangles with any vertex below min_z. Falls back to the
    unfiltered set if the filter would empty it out, rather than measuring
    against nothing."""
    if triangles.size == 0:
        return triangles
    keep = np.all(triangles[:, :, 2] >= min_z, axis=1)
    filtered = triangles[keep]
    return filtered if filtered.size else triangles


def _check_part_clearance(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    name_a, name_b, tri_a, tri_b, error = _load_two_named_parts(condition, parts_by_name)
    if error is not None:
        return error
    assert name_a is not None and name_b is not None and tri_a is not None and tri_b is not None
    # Optional: when a check needs one specific sub-region of a part that is
    # only available as a whole-body proxy (e.g. a well's side wall, when the
    # wall has no separately-extractable body from the floor it shares with),
    # `min_z_mm` excludes geometry below that height from both meshes before
    # measuring, so floor contact doesn't get conflated with wall clearance.
    min_z = condition.get("inputs", {}).get("min_z_mm")
    if min_z is not None:
        tri_a = _filter_triangles_above_z(tri_a, float(min_z))
        tri_b = _filter_triangles_above_z(tri_b, float(min_z))
    distance = _mesh_min_distance(tri_a, tri_b, assumptions)
    thresholds = condition.get("thresholds", {})
    min_clearance = float(thresholds.get("min_clearance_mm", 0.0))
    max_clearance = thresholds.get("max_clearance_mm")
    max_clearance = float(max_clearance) if max_clearance is not None else None
    passed = distance >= min_clearance and (max_clearance is None or distance <= max_clearance)
    if max_clearance is None:
        detail = f"minimum distance {distance:.4f} mm {'>=' if passed else '<'} minimum clearance {min_clearance:.4f} mm"
    else:
        detail = (
            f"minimum distance {distance:.4f} mm "
            f"{'within' if passed else 'outside'} clearance range {min_clearance:.4f}..{max_clearance:.4f} mm"
        )
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        detail,
        {
            "part_a": name_a,
            "part_b": name_b,
            "min_distance_mm": round(float(distance), 6),
            "min_clearance_mm": min_clearance,
            "max_clearance_mm": max_clearance,
        },
    )


def _check_part_contact(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    name_a, name_b, tri_a, tri_b, error = _load_two_named_parts(condition, parts_by_name)
    if error is not None:
        return error
    assert name_a is not None and name_b is not None and tri_a is not None and tri_b is not None
    distance = _mesh_min_distance(tri_a, tri_b, assumptions)
    max_contact = float(condition.get("thresholds", {}).get("max_contact_distance_mm", 0.1))
    passed = distance <= max_contact
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"minimum distance {distance:.4f} mm {'<=' if passed else '>'} contact threshold {max_contact:.4f} mm",
        {
            "part_a": name_a,
            "part_b": name_b,
            "min_distance_mm": round(float(distance), 6),
            "max_contact_distance_mm": max_contact,
        },
    )


def _check_linear_motion_collision(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    name_a, name_b, tri_a, tri_b, error = _load_two_named_parts(
        condition, parts_by_name, key_a="moving_part", key_b="obstacle_part"
    )
    if error is not None:
        return error
    assert name_a is not None and name_b is not None and tri_a is not None and tri_b is not None
    inputs = condition.get("inputs", {})
    try:
        translation = np.asarray(inputs.get("translation"), dtype=float)
    except Exception:
        return _condition_result(condition, "inconclusive", "linear_motion_collision requires numeric translation")
    if translation.shape != (3,):
        return _condition_result(condition, "inconclusive", "linear_motion_collision translation must be [x, y, z]")
    steps = int(inputs.get("steps", 8))
    if steps < 1:
        return _condition_result(condition, "inconclusive", "linear_motion_collision steps must be >= 1")

    for step in range(steps + 1):
        moved = tri_a + (translation * (step / steps))
        if _meshes_collide(moved, tri_b, assumptions):
            return _condition_result(
                condition,
                "fail",
                f"sampled motion path collides at step {step}/{steps}",
                {
                    "moving_part": name_a,
                    "obstacle_part": name_b,
                    "collides": True,
                    "first_collision_step": step,
                    "steps": steps,
                    "translation": [float(x) for x in translation],
                },
            )
    return _condition_result(
        condition,
        "pass",
        f"no sampled collision across {steps} linear motion steps",
        {
            "moving_part": name_a,
            "obstacle_part": name_b,
            "collides": False,
            "steps": steps,
            "translation": [float(x) for x in translation],
        },
    )


def _linear_motion_steps(condition: dict) -> tuple[np.ndarray | None, int | None, dict | None]:
    inputs = condition.get("inputs", {})
    translation, error = _parse_vector(inputs.get("translation"), "linear_motion translation")
    if error:
        return None, None, _condition_result(condition, "inconclusive", error)
    steps = int(inputs.get("steps", 8))
    if steps < 1:
        return None, None, _condition_result(condition, "inconclusive", "linear motion steps must be >= 1")
    return translation, steps, None


def _check_linear_motion_clearance(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    name_a, name_b, tri_a, tri_b, error = _load_two_named_parts(
        condition, parts_by_name, key_a="moving_part", key_b="obstacle_part"
    )
    if error is not None:
        return error
    translation, steps, step_error = _linear_motion_steps(condition)
    if step_error is not None:
        return step_error
    assert name_a is not None and name_b is not None and tri_a is not None and tri_b is not None
    assert translation is not None and steps is not None
    min_clearance = float(condition.get("thresholds", {}).get("min_clearance_mm", 0.0))
    best = float("inf")
    best_step = 0
    for step in range(steps + 1):
        moved = tri_a + (translation * (step / steps))
        distance = _mesh_min_distance(moved, tri_b, assumptions)
        if distance < best:
            best = distance
            best_step = step
    passed = best >= min_clearance
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"minimum path clearance {best:.4f} mm {'>=' if passed else '<'} required {min_clearance:.4f} mm",
        {
            "moving_part": name_a,
            "obstacle_part": name_b,
            "minimum_path_clearance_mm": round(float(best), 6),
            "minimum_clearance_step": best_step,
            "min_clearance_mm": min_clearance,
            "steps": steps,
            "translation": [float(x) for x in translation],
        },
    )


def _rotation_inputs(condition: dict) -> tuple[np.ndarray | None, np.ndarray | None, float | None, float | None, int | None, dict | None]:
    inputs = condition.get("inputs", {})
    axis_point, point_error = _parse_vector(inputs.get("axis_point"), "axis_point")
    if point_error:
        return None, None, None, None, None, _condition_result(condition, "inconclusive", point_error)
    axis_direction, dir_error = _normalize_vector(inputs.get("axis_direction"))
    if dir_error:
        return None, None, None, None, None, _condition_result(condition, "inconclusive", f"axis_direction {dir_error}")
    try:
        start = float(inputs.get("angle_start_deg", 0.0))
        end = float(inputs.get("angle_end_deg"))
    except Exception:
        return None, None, None, None, None, _condition_result(
            condition, "inconclusive", "rotation motion requires numeric angle_end_deg"
        )
    steps = int(inputs.get("steps", 8))
    if steps < 1:
        return None, None, None, None, None, _condition_result(condition, "inconclusive", "rotation motion steps must be >= 1")
    return axis_point, axis_direction, start, end, steps, None


def _check_rotation_motion_collision(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    name_a, name_b, tri_a, tri_b, error = _load_two_named_parts(
        condition, parts_by_name, key_a="moving_part", key_b="obstacle_part"
    )
    if error is not None:
        return error
    axis_point, axis_direction, start, end, steps, input_error = _rotation_inputs(condition)
    if input_error is not None:
        return input_error
    assert name_a is not None and name_b is not None and tri_a is not None and tri_b is not None
    assert axis_point is not None and axis_direction is not None and start is not None and end is not None and steps is not None
    for step in range(steps + 1):
        angle = start + (end - start) * (step / steps)
        moved = _rotate_triangles(tri_a, axis_point, axis_direction, angle)
        if _meshes_collide(moved, tri_b, assumptions):
            return _condition_result(
                condition,
                "fail",
                f"sampled rotation path collides at step {step}/{steps}",
                {
                    "moving_part": name_a,
                    "obstacle_part": name_b,
                    "collides": True,
                    "first_collision_step": step,
                    "first_collision_angle_deg": round(float(angle), 6),
                    "steps": steps,
                },
            )
    return _condition_result(
        condition,
        "pass",
        f"no sampled collision across {steps} rotation steps",
        {"moving_part": name_a, "obstacle_part": name_b, "collides": False, "steps": steps},
    )


def _check_axis_alignment(condition: dict) -> dict:
    inputs = condition.get("inputs", {})
    axis_a = inputs.get("axis_a", {})
    axis_b = inputs.get("axis_b", {})
    point_a, err = _parse_vector(axis_a.get("point"), "axis_a.point")
    if err:
        return _condition_result(condition, "inconclusive", err)
    point_b, err = _parse_vector(axis_b.get("point"), "axis_b.point")
    if err:
        return _condition_result(condition, "inconclusive", err)
    direction_a, err = _normalize_vector(axis_a.get("direction"))
    if err:
        return _condition_result(condition, "inconclusive", f"axis_a.direction {err}")
    direction_b, err = _normalize_vector(axis_b.get("direction"))
    if err:
        return _condition_result(condition, "inconclusive", f"axis_b.direction {err}")
    assert point_a is not None and point_b is not None and direction_a is not None and direction_b is not None
    dot = abs(float(np.clip(np.dot(direction_a, direction_b), -1.0, 1.0)))
    angle = float(np.degrees(np.arccos(dot)))
    offset = _line_to_line_distance(point_a, direction_a, point_b, direction_b)
    thresholds = condition.get("thresholds", {})
    max_offset = float(thresholds.get("max_axis_offset_mm", 0.5))
    max_angle = float(thresholds.get("max_angle_deg", 2.0))
    passed = offset <= max_offset and angle <= max_angle
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"axis offset {offset:.4f} mm, angle {angle:.4f} deg",
        {
            "axis_offset_mm": round(offset, 6),
            "axis_angle_deg": round(angle, 6),
            "max_axis_offset_mm": max_offset,
            "max_angle_deg": max_angle,
        },
    )


def _check_relative_pose(
    condition: dict,
    parts_by_name: dict[str, dict],
) -> dict:
    name_a, name_b, tri_a, tri_b, error = _load_two_named_parts(condition, parts_by_name)
    if error is not None:
        return error
    axis, axis_error = _normalize_vector(condition.get("inputs", {}).get("axis"))
    if axis_error:
        return _condition_result(condition, "inconclusive", f"axis {axis_error}")
    assert name_a is not None and name_b is not None and tri_a is not None and tri_b is not None and axis is not None
    centroid_a = _mesh_centroid(tri_a)
    centroid_b = _mesh_centroid(tri_b)
    delta = float(np.dot(centroid_b - centroid_a, axis))
    thresholds = condition.get("thresholds", {})
    min_delta = thresholds.get("min_delta_mm")
    max_delta = thresholds.get("max_delta_mm")
    passed = True
    if min_delta is not None:
        passed = passed and delta >= float(min_delta)
    if max_delta is not None:
        passed = passed and delta <= float(max_delta)
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"centroid delta along axis {delta:.4f} mm",
        {
            "part_a": name_a,
            "part_b": name_b,
            "centroid_delta_along_axis_mm": round(delta, 6),
            "min_delta_mm": float(min_delta) if min_delta is not None else None,
            "max_delta_mm": float(max_delta) if max_delta is not None else None,
        },
    )


def _check_opening_presence(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    inputs = condition.get("inputs", {})
    name = inputs.get("part")
    if not name:
        return _condition_result(condition, "inconclusive", "opening_presence requires part")
    triangles, error = _load_part_triangles(parts_by_name, name)
    if error:
        return _condition_result(condition, "inconclusive", error)
    start, error = _parse_vector(inputs.get("segment_start"), "segment_start")
    if error:
        return _condition_result(condition, "inconclusive", error)
    end, error = _parse_vector(inputs.get("segment_end"), "segment_end")
    if error:
        return _condition_result(condition, "inconclusive", error)
    assert triangles is not None and start is not None and end is not None
    samples = int(inputs.get("samples", 11))
    if samples < 2:
        return _condition_result(condition, "inconclusive", "opening_presence samples must be >= 2")
    max_inside = int(condition.get("thresholds", {}).get("max_inside_samples", 0))
    sample_tris = _sample_triangles(triangles, assumptions.max_sample_triangles)
    inside_count = 0
    for i in range(samples):
        point = start + (end - start) * (i / (samples - 1))
        if _point_inside_mesh(point, sample_tris):
            inside_count += 1
    passed = inside_count <= max_inside
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"opening segment has {inside_count} inside samples, allowed {max_inside}",
        {
            "part": name,
            "inside_sample_count": inside_count,
            "max_inside_samples": max_inside,
            "samples": samples,
        },
    )


def _check_vent_opening_proxy(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    inputs = condition.get("inputs", {})
    name = inputs.get("part")
    if not name:
        return _condition_result(condition, "inconclusive", "vent_opening_proxy requires part")
    triangles, error = _load_part_triangles(parts_by_name, name)
    if error:
        return _condition_result(condition, "inconclusive", error)
    rays = inputs.get("rays")
    if not isinstance(rays, list) or not rays:
        return _condition_result(condition, "inconclusive", "vent_opening_proxy requires non-empty rays")
    assert triangles is not None

    thresholds = condition.get("thresholds", {})
    max_intersections = int(thresholds.get("max_intersections_per_clear_ray", 0))
    min_clear_rays = thresholds.get("min_clear_rays")
    min_clear_fraction = thresholds.get("min_clear_fraction")
    if min_clear_rays is None and min_clear_fraction is None:
        min_clear_fraction = 0.5

    sample_tris = _sample_triangles(triangles, assumptions.max_sample_triangles)
    ray_results: list[dict[str, Any]] = []
    clear_count = 0
    for index, ray in enumerate(rays):
        if not isinstance(ray, dict):
            return _condition_result(condition, "inconclusive", f"ray {index} must be an object")
        start, start_error = _parse_vector(ray.get("start"), f"rays[{index}].start")
        if start_error:
            return _condition_result(condition, "inconclusive", start_error)
        end, end_error = _parse_vector(ray.get("end"), f"rays[{index}].end")
        if end_error:
            return _condition_result(condition, "inconclusive", end_error)
        assert start is not None and end is not None
        intersections = sum(1 for tri in sample_tris if _segment_intersects_triangle(start, end, tri))
        is_clear = intersections <= max_intersections
        if is_clear:
            clear_count += 1
        ray_results.append(
            {
                "index": index,
                "intersection_count": int(intersections),
                "clear": is_clear,
            }
        )

    clear_fraction = clear_count / len(rays)
    passed = True
    if min_clear_rays is not None:
        passed = passed and clear_count >= int(min_clear_rays)
    if min_clear_fraction is not None:
        passed = passed and clear_fraction >= float(min_clear_fraction)
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"vent proxy found {clear_count}/{len(rays)} clear rays",
        {
            "part": name,
            "clear_ray_count": clear_count,
            "total_rays": len(rays),
            "clear_fraction": round(float(clear_fraction), 6),
            "min_clear_rays": int(min_clear_rays) if min_clear_rays is not None else None,
            "min_clear_fraction": float(min_clear_fraction) if min_clear_fraction is not None else None,
            "max_intersections_per_clear_ray": max_intersections,
            "rays": ray_results,
            "proxy_limitation": "samples explicit straight rays through expected openings; it does not measure full open area or validate grille shape",
        },
    )


def _check_clear_path_proxy(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    inputs = condition.get("inputs", {})
    name = inputs.get("part")
    if not name:
        return _condition_result(condition, "inconclusive", "clear_path_proxy requires part")
    triangles, error = _load_part_triangles(parts_by_name, name)
    if error:
        return _condition_result(condition, "inconclusive", error)
    paths = inputs.get("paths", inputs.get("rays", inputs.get("segments")))
    if not isinstance(paths, list) or not paths:
        return _condition_result(condition, "inconclusive", "clear_path_proxy requires non-empty paths")
    assert triangles is not None

    thresholds = condition.get("thresholds", {})
    max_intersections = int(
        thresholds.get(
            "max_intersections_per_clear_path",
            thresholds.get("max_intersections_per_clear_ray", 0),
        )
    )
    min_clear_paths = thresholds.get("min_clear_paths", thresholds.get("min_clear_rays"))
    min_clear_fraction = thresholds.get("min_clear_fraction")
    if min_clear_paths is None and min_clear_fraction is None:
        min_clear_fraction = 1.0

    path_results: list[dict[str, Any]] = []
    clear_count = 0
    candidate_counts: list[int] = []
    for index, path in enumerate(paths):
        if not isinstance(path, dict):
            return _condition_result(condition, "inconclusive", f"path {index} must be an object")
        start, start_error = _parse_vector(path.get("start"), f"paths[{index}].start")
        if start_error:
            return _condition_result(condition, "inconclusive", start_error)
        end, end_error = _parse_vector(path.get("end"), f"paths[{index}].end")
        if end_error:
            return _condition_result(condition, "inconclusive", end_error)
        assert start is not None and end is not None
        candidate_tris = _triangles_overlapping_segment_bounds(triangles, start, end)
        candidate_counts.append(int(len(candidate_tris)))
        intersections = sum(1 for tri in candidate_tris if _segment_intersects_triangle(start, end, tri))
        is_clear = intersections <= max_intersections
        if is_clear:
            clear_count += 1
        path_results.append(
            {
                "index": index,
                "intersection_count": int(intersections),
                "candidate_triangle_count": int(len(candidate_tris)),
                "clear": is_clear,
            }
        )

    clear_fraction = clear_count / len(paths)
    passed = True
    if min_clear_paths is not None:
        passed = passed and clear_count >= int(min_clear_paths)
    if min_clear_fraction is not None:
        passed = passed and clear_fraction >= float(min_clear_fraction)
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"clear path proxy found {clear_count}/{len(paths)} clear paths",
        {
            "part": name,
            "clear_path_count": clear_count,
            "total_paths": len(paths),
            "clear_fraction": round(float(clear_fraction), 6),
            "min_clear_paths": int(min_clear_paths) if min_clear_paths is not None else None,
            "min_clear_fraction": float(min_clear_fraction) if min_clear_fraction is not None else None,
            "max_intersections_per_clear_path": max_intersections,
            "candidate_triangle_count_min": min(candidate_counts) if candidate_counts else None,
            "candidate_triangle_count_max": max(candidate_counts) if candidate_counts else None,
            "total_triangle_count": int(len(triangles)),
            "paths": path_results,
            "proxy_limitation": "samples explicit straight paths through expected holes, slots, or windows; it does not measure opening diameter, area, shape fidelity, or downstream usability",
        },
    )


def _check_vent_grid_open_area_proxy(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    inputs = condition.get("inputs", {})
    name = inputs.get("part")
    if not name:
        return _condition_result(condition, "inconclusive", "vent_grid_open_area_proxy requires part")
    triangles, error = _load_part_triangles(parts_by_name, name)
    if error:
        return _condition_result(condition, "inconclusive", error)
    origin, error = _parse_vector(inputs.get("grid_origin"), "grid_origin")
    if error:
        return _condition_result(condition, "inconclusive", error)
    u_vector, error = _parse_vector(inputs.get("u_vector"), "u_vector")
    if error:
        return _condition_result(condition, "inconclusive", error)
    v_vector, error = _parse_vector(inputs.get("v_vector"), "v_vector")
    if error:
        return _condition_result(condition, "inconclusive", error)
    direction, error = _normalize_vector(inputs.get("ray_direction"))
    if error:
        return _condition_result(condition, "inconclusive", f"ray_direction {error}")
    try:
        ray_length = float(inputs.get("ray_length_mm"))
    except Exception:
        return _condition_result(condition, "inconclusive", "vent_grid_open_area_proxy requires numeric ray_length_mm")
    if ray_length <= 0.0:
        return _condition_result(condition, "inconclusive", "ray_length_mm must be > 0")
    rows = int(inputs.get("rows", 5))
    cols = int(inputs.get("cols", 5))
    if rows < 1 or cols < 1:
        return _condition_result(condition, "inconclusive", "rows and cols must be >= 1")
    if rows * cols > assumptions.max_sample_points:
        return _condition_result(
            condition,
            "inconclusive",
            f"vent grid has {rows * cols} rays, above max_sample_points {assumptions.max_sample_points}",
        )

    assert triangles is not None and origin is not None and u_vector is not None and v_vector is not None and direction is not None
    thresholds = condition.get("thresholds", {})
    max_intersections = int(thresholds.get("max_intersections_per_clear_ray", 0))
    min_clear_rays = thresholds.get("min_clear_rays")
    min_clear_fraction = thresholds.get("min_clear_fraction")
    if min_clear_rays is None and min_clear_fraction is None:
        min_clear_fraction = 0.25

    sample_tris = triangles
    clear_count = 0
    intersection_counts: list[int] = []
    for row in range(rows):
        v_scale = 0.0 if rows == 1 else row / (rows - 1)
        for col in range(cols):
            u_scale = 0.0 if cols == 1 else col / (cols - 1)
            start = origin + u_vector * u_scale + v_vector * v_scale
            end = start + direction * ray_length
            intersections = sum(1 for tri in sample_tris if _segment_intersects_triangle(start, end, tri))
            intersection_counts.append(int(intersections))
            if intersections <= max_intersections:
                clear_count += 1

    total = rows * cols
    clear_fraction = clear_count / total
    passed = True
    if min_clear_rays is not None:
        passed = passed and clear_count >= int(min_clear_rays)
    if min_clear_fraction is not None:
        passed = passed and clear_fraction >= float(min_clear_fraction)
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"vent grid proxy found {clear_count}/{total} clear rays",
        {
            "part": name,
            "clear_ray_count": clear_count,
            "total_rays": total,
            "clear_fraction": round(float(clear_fraction), 6),
            "rows": rows,
            "cols": cols,
            "min_clear_rays": int(min_clear_rays) if min_clear_rays is not None else None,
            "min_clear_fraction": float(min_clear_fraction) if min_clear_fraction is not None else None,
            "max_intersections_per_clear_ray": max_intersections,
            "intersection_count_min": min(intersection_counts) if intersection_counts else None,
            "intersection_count_max": max(intersection_counts) if intersection_counts else None,
            "proxy_limitation": "samples a rectangular grid of straight rays through an expected vent field; it estimates representative open paths, not exact open area, hole count, or airflow",
        },
    )


def _check_feature_count(condition: dict, parts_by_name: dict[str, dict]) -> dict:
    inputs = condition.get("inputs", {})
    if "features" in inputs:
        names = [name for name in inputs.get("features", []) if name in parts_by_name]
    elif "part_name_prefix" in inputs:
        prefix = str(inputs["part_name_prefix"])
        names = [name for name in parts_by_name if name.startswith(prefix)]
    else:
        return _condition_result(condition, "inconclusive", "feature_count requires features or part_name_prefix")
    thresholds = condition.get("thresholds", {})
    expected = thresholds.get("expected_count")
    min_count = thresholds.get("min_count", expected)
    max_count = thresholds.get("max_count", expected)
    actual = len(names)
    passed = True
    if min_count is not None:
        passed = passed and actual >= int(min_count)
    if max_count is not None:
        passed = passed and actual <= int(max_count)
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"feature count {actual}",
        {
            "actual_count": actual,
            "matched_features": sorted(names),
            "expected_count": int(expected) if expected is not None else None,
            "min_count": int(min_count) if min_count is not None else None,
            "max_count": int(max_count) if max_count is not None else None,
        },
    )


def _check_cylindrical_fit(condition: dict) -> dict:
    inputs = condition.get("inputs", {})
    try:
        pin_diameter = float(inputs.get("pin_diameter_mm"))
        hole_diameter = float(inputs.get("hole_diameter_mm"))
    except Exception:
        return _condition_result(condition, "inconclusive", "cylindrical_fit requires numeric pin_diameter_mm and hole_diameter_mm")
    clearance = hole_diameter - pin_diameter
    thresholds = condition.get("thresholds", {})
    min_clearance = float(thresholds.get("min_diameter_clearance_mm", 0.0))
    max_clearance = thresholds.get("max_diameter_clearance_mm")
    max_clearance = float(max_clearance) if max_clearance is not None else None
    passed = clearance >= min_clearance and (max_clearance is None or clearance <= max_clearance)
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"diameter clearance {clearance:.4f} mm",
        {
            "pin_diameter_mm": pin_diameter,
            "hole_diameter_mm": hole_diameter,
            "diameter_clearance_mm": round(clearance, 6),
            "min_diameter_clearance_mm": min_clearance,
            "max_diameter_clearance_mm": max_clearance,
        },
    )


def _check_spherical_fit(condition: dict) -> dict:
    inputs = condition.get("inputs", {})
    try:
        if "ball_diameter_mm" in inputs:
            ball_radius = float(inputs["ball_diameter_mm"]) / 2.0
        else:
            ball_radius = float(inputs.get("ball_radius_mm"))
        if "socket_diameter_mm" in inputs:
            socket_radius = float(inputs["socket_diameter_mm"]) / 2.0
        else:
            socket_radius = float(inputs.get("socket_radius_mm"))
    except Exception:
        return _condition_result(
            condition,
            "inconclusive",
            "spherical_fit requires ball_radius_mm/socket_radius_mm or ball_diameter_mm/socket_diameter_mm",
        )
    radial_clearance = socket_radius - ball_radius
    thresholds = condition.get("thresholds", {})
    min_clearance = float(thresholds.get("min_radial_clearance_mm", 0.0))
    max_clearance = thresholds.get("max_radial_clearance_mm")
    max_clearance = float(max_clearance) if max_clearance is not None else None
    passed = radial_clearance >= min_clearance and (max_clearance is None or radial_clearance <= max_clearance)
    return _condition_result(
        condition,
        "pass" if passed else "fail",
        f"radial clearance {radial_clearance:.4f} mm",
        {
            "ball_radius_mm": ball_radius,
            "socket_radius_mm": socket_radius,
            "radial_clearance_mm": round(radial_clearance, 6),
            "diameter_clearance_mm": round(radial_clearance * 2.0, 6),
            "min_radial_clearance_mm": min_clearance,
            "max_radial_clearance_mm": max_clearance,
            "proxy_limitation": "checks only explicit ball/socket size compatibility; it does not validate socket mouth geometry, snap compliance, retention force, or swept articulation clearance",
        },
    )


def _pair_distance(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
    pair: list[str],
) -> tuple[float | None, str | None]:
    if len(pair) != 2:
        return None, f"contact pair must contain exactly two part names: {pair}"
    tri_a, err_a = _load_part_triangles(parts_by_name, pair[0])
    tri_b, err_b = _load_part_triangles(parts_by_name, pair[1])
    if err_a or err_b:
        return None, "; ".join(err for err in (err_a, err_b) if err)
    assert tri_a is not None and tri_b is not None
    return _mesh_min_distance(tri_a, tri_b, assumptions), None


def _check_contact_graph(
    condition: dict,
    parts_by_name: dict[str, dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    inputs = condition.get("inputs", {})
    expected = inputs.get("expected_contacts", [])
    forbidden = inputs.get("forbidden_contacts", [])
    thresholds = condition.get("thresholds", {})
    max_contact = float(thresholds.get("max_contact_distance_mm", 0.1))
    min_forbidden = float(thresholds.get("min_forbidden_clearance_mm", max_contact))
    edge_results: list[dict] = []
    failed: list[dict] = []

    for pair in expected:
        distance, error = _pair_distance(condition, parts_by_name, assumptions, pair)
        if error:
            return _condition_result(condition, "inconclusive", error)
        assert distance is not None
        ok = distance <= max_contact
        result = {
            "kind": "expected",
            "parts": pair,
            "distance_mm": round(float(distance), 6),
            "passed": ok,
        }
        edge_results.append(result)
        if not ok:
            failed.append(result)

    for pair in forbidden:
        distance, error = _pair_distance(condition, parts_by_name, assumptions, pair)
        if error:
            return _condition_result(condition, "inconclusive", error)
        assert distance is not None
        ok = distance >= min_forbidden
        result = {
            "kind": "forbidden",
            "parts": pair,
            "distance_mm": round(float(distance), 6),
            "passed": ok,
        }
        edge_results.append(result)
        if not ok:
            failed.append(result)

    return _condition_result(
        condition,
        "pass" if not failed else "fail",
        f"contact graph checked {len(edge_results)} edges, {len(failed)} failed",
        {
            "edges": edge_results,
            "failed_edges": failed,
            "max_contact_distance_mm": max_contact,
            "min_forbidden_clearance_mm": min_forbidden,
        },
    )


def _check_assembly_component_count(condition: dict, assembly_report: dict | None, part_reports: list[dict]) -> dict:
    if assembly_report is None:
        return _condition_result(condition, "inconclusive", "no assembly STL supplied")
    if not assembly_report.get("loadable"):
        return _condition_result(condition, "inconclusive", "assembly STL failed to load")

    expected = condition.get("thresholds", {}).get("expected_components")
    if expected is None:
        expected = len(part_reports)
    actual = int(assembly_report["metrics"]["connected_components"])
    status = "pass" if actual == int(expected) else "fail"
    return _condition_result(
        condition,
        status,
        f"assembly connected components {actual} {'==' if status == 'pass' else '!='} expected {expected}",
        {"actual_components": actual, "expected_components": int(expected)},
    )


def _condition_result(
    condition: dict,
    status: str,
    detail: str,
    measurements: dict[str, Any] | None = None,
) -> dict:
    return {
        "id": condition.get("id", "unnamed_condition"),
        "category": condition.get("category", "physical_correctness"),
        "severity": condition.get("severity", "major"),
        "check": condition.get("check", "unknown"),
        "status": status,
        "description": condition.get("description", ""),
        "detail": detail,
        "measurements": measurements or {},
    }


def _check_assembly_sequence(
    condition: dict,
    assembly_report: dict | None,
    parts_by_name: dict[str, dict],
    part_reports: list[dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    steps = condition.get("inputs", {}).get("steps", [])
    if not isinstance(steps, list) or not steps:
        return _condition_result(condition, "inconclusive", "assembly_sequence requires a non-empty steps list")

    step_results: list[dict] = []
    failed_steps: list[str] = []
    inconclusive_steps: list[str] = []
    for index, step in enumerate(steps):
        if not isinstance(step, dict):
            return _condition_result(condition, "inconclusive", f"assembly_sequence step {index} must be an object")
        subcondition = {
            "id": step.get("id", f"step_{index}"),
            "category": step.get("category", condition.get("category", "motion_path")),
            "severity": step.get("severity", condition.get("severity", "major")),
            "description": step.get("description", ""),
            "check": step.get("check"),
            "inputs": step.get("inputs", {}),
            "thresholds": step.get("thresholds", {}),
        }
        result = _run_condition(subcondition, assembly_report, parts_by_name, part_reports, assumptions)
        step_results.append(result)
        if result["status"] == "fail":
            failed_steps.append(result["id"])
        elif result["status"] == "inconclusive":
            inconclusive_steps.append(result["id"])

    if failed_steps:
        status = "fail"
        detail = f"assembly sequence failed at step(s): {', '.join(failed_steps)}"
    elif inconclusive_steps:
        status = "inconclusive"
        detail = f"assembly sequence inconclusive at step(s): {', '.join(inconclusive_steps)}"
    else:
        status = "pass"
        detail = f"assembly sequence passed {len(step_results)} steps"
    return _condition_result(
        condition,
        status,
        detail,
        {
            "step_results": step_results,
            "failed_steps": failed_steps,
            "inconclusive_steps": inconclusive_steps,
        },
    )


def _run_condition(
    condition: dict,
    assembly_report: dict | None,
    parts_by_name: dict[str, dict],
    part_reports: list[dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    check = condition.get("check")
    if check == "assembly_component_count":
        return _check_assembly_component_count(condition, assembly_report, part_reports)
    if check == "part_collision":
        return _check_part_collision(condition, parts_by_name, assumptions)
    if check == "part_clearance":
        return _check_part_clearance(condition, parts_by_name, assumptions)
    if check == "part_contact":
        return _check_part_contact(condition, parts_by_name, assumptions)
    if check == "linear_motion_collision":
        return _check_linear_motion_collision(condition, parts_by_name, assumptions)
    if check == "part_component_count":
        return _check_part_component_count(condition, parts_by_name)
    if check == "linear_motion_clearance":
        return _check_linear_motion_clearance(condition, parts_by_name, assumptions)
    if check == "rotation_motion_collision":
        return _check_rotation_motion_collision(condition, parts_by_name, assumptions)
    if check == "axis_alignment":
        return _check_axis_alignment(condition)
    if check == "relative_pose":
        return _check_relative_pose(condition, parts_by_name)
    if check == "opening_presence":
        return _check_opening_presence(condition, parts_by_name, assumptions)
    if check == "clear_path_proxy":
        return _check_clear_path_proxy(condition, parts_by_name, assumptions)
    if check == "vent_opening_proxy":
        return _check_vent_opening_proxy(condition, parts_by_name, assumptions)
    if check == "vent_grid_open_area_proxy":
        return _check_vent_grid_open_area_proxy(condition, parts_by_name, assumptions)
    if check == "feature_count":
        return _check_feature_count(condition, parts_by_name)
    if check == "cylindrical_fit":
        return _check_cylindrical_fit(condition)
    if check == "spherical_fit":
        return _check_spherical_fit(condition)
    if check == "contact_graph":
        return _check_contact_graph(condition, parts_by_name, assumptions)
    if check == "assembly_sequence":
        return _check_assembly_sequence(condition, assembly_report, parts_by_name, part_reports, assumptions)
    if check == "hex_shaft_rotational_clearance":
        return _check_hex_shaft_rotational_clearance(condition)
    return _condition_result(condition, "inconclusive", f"unsupported check: {check}")


def _combine_scores(
    baseline: dict,
    condition_results: list[dict],
    assumptions: PhysicalCorrectnessAssumptions,
) -> dict:
    score = float(baseline["score"])
    hard_failures = list(baseline["hard_failures"])
    risk_factors = list(baseline["risk_factors"])
    cap = 10.0

    for result in condition_results:
        severity = result["severity"]
        cid = result["id"]
        if result["status"] == "fail":
            if severity == "critical":
                cap = min(cap, assumptions.critical_failure_cap)
                hard_failures.append(f"critical condition failed: {cid}")
                score = min(score, assumptions.critical_failure_cap)
            else:
                risk_factors.append(f"{severity} condition failed: {cid}")
                score -= _severity_penalty(severity, assumptions)
        elif result["status"] == "inconclusive":
            risk_factors.append(f"condition inconclusive: {cid}")
            score -= assumptions.inconclusive_penalty

    score = _round_score(min(score, cap))
    return {
        "score": score,
        "class": _class_for_score(score),
        "hard_failures": list(dict.fromkeys(hard_failures)),
        "risk_factors": list(dict.fromkeys(risk_factors)),
    }


def score_physical_correctness_project(
    assembly: str | os.PathLike | None = None,
    parts: Iterable[str | os.PathLike] | dict[str, str | os.PathLike] | None = None,
    conditions: list[dict] | None = None,
    assumptions: PhysicalCorrectnessAssumptions | None = None,
) -> dict:
    assumptions = assumptions or PhysicalCorrectnessAssumptions()
    if isinstance(parts, dict):
        part_items = list(parts.items())
        part_paths = [path for _, path in part_items]
        part_names = [name for name, _ in part_items]
    else:
        part_paths = list(parts or [])
        part_names = [Path(path).stem for path in part_paths]

    baseline = score_usability_project(
        assembly=assembly,
        parts=part_paths,
        assumptions=UsabilityAssumptions(),
    )
    part_reports = baseline["parts"]
    parts_by_name = {name: report for name, report in zip(part_names, part_reports)}
    condition_results = [
        _run_condition(condition, baseline["assembly"], parts_by_name, part_reports, assumptions)
        for condition in (conditions or [])
    ]
    combined = _combine_scores(baseline, condition_results, assumptions)
    return {
        **combined,
        "metrics": baseline["metrics"],
        "condition_results": condition_results,
        "assembly": baseline["assembly"],
        "parts": part_reports,
        "part_names": part_names,
        "assumptions": {
            "physical_correctness": asdict(assumptions),
            "layer1_geometry": baseline["assumptions"],
        },
    }


def score_condition_manifest(
    path: str | os.PathLike,
    assumptions: PhysicalCorrectnessAssumptions | None = None,
) -> dict:
    manifest_path = Path(path)
    data = json.loads(manifest_path.read_text())
    root = manifest_path.parent
    assembly = data.get("assembly")
    assembly_path = root / assembly if assembly else None
    raw_parts = data.get("parts", {})
    if isinstance(raw_parts, dict):
        parts = {name: root / rel for name, rel in raw_parts.items()}
    else:
        parts = [root / rel for rel in raw_parts]
    return score_physical_correctness_project(
        assembly=assembly_path,
        parts=parts,
        conditions=data.get("conditions", []),
        assumptions=assumptions,
    )


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Score project physical correctness.")
    parser.add_argument("--assembly", help="assembled STL path")
    parser.add_argument("--parts", nargs="*", default=None, help="separate part STL paths")
    parser.add_argument("--condition-manifest", help="JSON condition manifest")
    parser.add_argument("--json-out", help="optional output JSON path")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if bool(args.condition_manifest) == bool(args.assembly or args.parts):
        parser.error("choose exactly one input mode: --condition-manifest or --assembly/--parts")

    if args.condition_manifest:
        report = score_condition_manifest(args.condition_manifest)
    else:
        report = score_physical_correctness_project(args.assembly, args.parts or [])

    text = json.dumps(report, indent=2)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
