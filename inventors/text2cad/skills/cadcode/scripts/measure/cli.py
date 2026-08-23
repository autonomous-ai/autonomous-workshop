"""``python scripts/measure <model.step>`` — measure a STEP without meshing it.

Answers the questions a build, review or repair session otherwise answers by
loading STLs into trimesh: what parts are in this model, how big is each one,
where does it sit, what colour did the source give it, and do two of them clash
or float apart.

Reading the B-rep instead of a mesh is exact (no mesh tolerance in the number),
costs no mesh memory — a 14-part all-at-once trimesh load once grew to 14.8GB
and the kernel OOM-killed the whole pipeline — and names each part the way the
STEP file labels it, so a measurement can be quoted against the brief's
``## Parts`` row by name.

    python scripts/measure model.step                # every part
    python scripts/measure model.step --part grip    # parts matching 'grip'
    python scripts/measure model.step --gaps         # pairwise clearance/overlap

Compact JSON on stdout: ``{"ok": true, "parts": [...], "pairs": [...]}``.
Every length is mm, every volume mm^3. Exit 0 on success, 2 on a bad input.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
PACKAGES_DIR = SCRIPTS_DIR / "packages"
for _p in (str(SCRIPTS_DIR), str(PACKAGES_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

STEP_SUFFIXES = {".step", ".stp"}

# Pairs whose bounding boxes are further apart than this never reach the exact
# (expensive) distance solver: parts that far apart are not mating, and a
# 14-part model is 91 pairs. Raise it with --near to inspect a loose fit.
DEFAULT_NEAR_MM = 5.0


def _round3(value: float) -> float:
    return round(float(value), 3)


def _bbox_gap(box_a: dict, box_b: dict) -> float:
    """Distance between two axis-aligned boxes (0.0 when they overlap).

    A lower bound on the true surface-to-surface distance, so it is safe to
    skip the solver for pairs whose boxes are already too far apart.
    """
    total = 0.0
    for axis in range(3):
        delta = max(
            box_a["min"][axis] - box_b["max"][axis],
            box_b["min"][axis] - box_a["max"][axis],
            0.0,
        )
        total += delta * delta
    return total**0.5


def _min_distance(shape_a: object, shape_b: object) -> float | None:
    """Exact minimum surface-to-surface distance (mm), or None if OCCT fails."""
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape

    try:
        solver = BRepExtrema_DistShapeShape(shape_a, shape_b)
        if not solver.IsDone():
            solver.Perform()
        if not solver.IsDone():
            return None
        return float(solver.Value())
    except Exception:
        return None


def _color_hex(rgba: object) -> str | None:
    """cadpy's ColorRGBA (r, g, b, a floats 0-1) → '#rrggbb'."""
    try:
        r, g, b = (float(c) for c in tuple(rgba)[:3])  # type: ignore[arg-type]
    except Exception:
        return None
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in (r, g, b))


def _collect(step_path: Path, name_filter: str | None) -> tuple[list[dict], list[tuple]]:
    """Return (part records, (name, shape, bbox) triples for the gap pass)."""
    from cadpy.checks import _shape_volume
    from cadpy.step_scene import (
        _bbox_from_shape,
        load_step_scene,
        occurrence_selector_id,
        scene_leaf_occurrences,
        scene_occurrence_shape,
    )

    scene = load_step_scene(step_path)
    needle = (name_filter or "").strip().lower()

    parts: list[dict] = []
    placed: list[tuple] = []
    for index, node in enumerate(scene_leaf_occurrences(scene)):
        name = node.name or node.source_name or f"part{index + 1}"
        if needle and needle not in name.lower():
            continue
        record: dict = {"ref": occurrence_selector_id(node), "name": name}
        if node.prototype_key is None or node.prototype_key not in scene.prototype_shapes:
            # A label with no geometry behind it: report it rather than drop it,
            # since a part missing from the export is exactly what a review is
            # trying to find.
            record["error"] = "occurrence has no prototype shape"
            parts.append(record)
            continue
        shape = scene_occurrence_shape(scene, node)
        box = _bbox_from_shape(shape)
        color = node.color or scene.prototype_colors.get(node.prototype_key)
        record.update(
            volume_mm3=_round3(_shape_volume(shape)),
            size=[_round3(v) for v in box["size"]],
            center=[_round3(v) for v in box["center"]],
            min=[_round3(v) for v in box["min"]],
            max=[_round3(v) for v in box["max"]],
            color=_color_hex(color) if color is not None else None,
        )
        parts.append(record)
        placed.append((name, shape, box))
    return parts, placed


def _pairs(placed: list[tuple], near_mm: float) -> list[dict]:
    """Clearance and overlap for every pair whose boxes are within near_mm."""
    import itertools

    from cadpy.checks import intersection_volume

    rows: list[dict] = []
    for (name_a, shape_a, box_a), (name_b, shape_b, box_b) in itertools.combinations(placed, 2):
        gap_bound = _bbox_gap(box_a, box_b)
        if gap_bound > near_mm:
            continue
        overlap = intersection_volume(shape_a, shape_b)
        row = {"a": name_a, "b": name_b, "overlap_mm3": _round3(overlap)}
        distance = _min_distance(shape_a, shape_b)
        # An overlapping pair has zero surface distance by definition, so the
        # solver's answer there is 0.0 and says nothing; the overlap volume is
        # the informative number.
        row["gap_mm"] = _round3(distance) if distance is not None else None
        rows.append(row)
    return rows


def _fail(message: str, code: str = "VALIDATION_FAILED") -> int:
    print(json.dumps({"ok": False, "error": {"code": code, "message": message}}))
    return 2


def main(argv: Sequence[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="scripts/measure",
        description=(
            "Measure an exported STEP: per-part name, bounding box, volume and "
            "colour from the B-rep, plus pairwise clearance and overlap."
        ),
    )
    p.add_argument("input", type=Path, help="Path to a .step/.stp file.")
    p.add_argument(
        "--part",
        default=None,
        help="Only report parts whose STEP label contains this (case-insensitive).",
    )
    p.add_argument(
        "--gaps",
        action="store_true",
        help="Also report, for every nearby pair, the minimum gap and overlap volume.",
    )
    p.add_argument(
        "--near",
        type=float,
        default=DEFAULT_NEAR_MM,
        help=f"Pair distance cutoff for --gaps, mm (default {DEFAULT_NEAR_MM}).",
    )
    args = p.parse_args(list(argv) if argv is not None else None)

    step_path = args.input.expanduser()
    if not step_path.is_file():
        return _fail(f"input not found: {step_path}")
    if step_path.suffix.lower() not in STEP_SUFFIXES:
        return _fail(
            f"{step_path.name} is not a STEP file — measure reads .step/.stp "
            "(the B-rep), not meshes. Export the STEP first."
        )

    try:
        parts, placed = _collect(step_path.resolve(), args.part)
    except MemoryError:
        return _fail("ran out of address space loading the STEP", "MEMORY_LIMIT")
    except Exception as exc:  # noqa: BLE001 — surface the reason, never traceback
        return _fail(f"{type(exc).__name__}: {exc}", "STEP_LOAD_FAILED")

    payload: dict = {"ok": True, "step": str(step_path), "parts": parts}
    if args.gaps:
        try:
            payload["pairs"] = _pairs(placed, args.near)
        except MemoryError:
            return _fail("ran out of address space measuring pairs", "MEMORY_LIMIT")
        except Exception as exc:  # noqa: BLE001
            return _fail(f"{type(exc).__name__}: {exc}", "PAIR_MEASURE_FAILED")
    print(json.dumps(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
