"""Deterministic shape diff against an Approved Proof (ADR 0096 decision 2b).

``proof_diff`` compares a built STEP with the Approved Proof's STEP, Part by
Part, and reads nothing but bytes. Per Part it measures:

- volume;
- the axis-aligned bounding box, in the frame the STEP was written in;
- the two-way Boolean difference: material only in A plus material only in
  B, so a change that adds and removes the same amount still counts.

A Part passes when (owner, 2026-11-02):

- ``|V_b - V_a| / V_a <= 1%``;
- every bounding-box side length differs by at most 0.1 mm (and, with
  ``align="none"``, every minimum corner coordinate too, so a moved Part in
  the Display Pose fails);
- the two-way difference is at most 1% of the larger volume.

Every Part also reports its surface deviation: the largest distance from
either surface to the other, sampled at tessellation vertices. It fails a
Part only when a limit is given (``--surface-limit``), pending the owner's
decision; on the K4 keycap set the three criteria above pass the v01 face
drift (Grumpy two-way 0.77%) that the surface deviation shows as 0.6 mm.

When the Boolean cannot be computed (an exception, a non-finite or
impossible volume, or a result that breaks ``A - B = only_A - only_B``), the Part reports ``boolean: "failed"`` and is judged on
volume and bounding box alone; the report says so. This is a byte
comparison with a fixed tolerance, not an engineering judgement: it never
renders, never scores likeness, and never asks a model anything.

Parts are the STEP's labelled solids (a kit Component writes one body per
Part id). A STEP whose solids carry no label is one Part named after the
file. Two directories compare their ``part_*.step`` files by name.

CLI::

    python -m workshop.make.proof_diff APPROVED BUILT [--align bbox|none] [--json OUT]

Exit 0 when every Part passes, 1 when any Part is over tolerance or a Part
or file is missing on either side, 2 when an input cannot be read.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

SCHEMA_VERSION = 1
TOOL = "proof_diff"
VOLUME_TOLERANCE = 0.01
BBOX_TOLERANCE_MM = 0.1
TWO_WAY_TOLERANCE = 0.01
# Measured and reported on every Part. It is a pass criterion only when a
# limit is set: ADR 0096 as accepted names three criteria, and the K4 v01
# face case (see tests) shows they miss a visible engraving change that this
# measure catches. The owner decides whether it becomes the fourth.
SURFACE_TOLERANCE_MM: float | None = None
_MAX_SURFACE_POINTS = 20000
_IDENTITY_SLACK = 0.005
# Names the STEP writer gives a shape nobody labelled.
_DEFAULT_LABELS = frozenset({"COMPOUND", "COMPSOLID", "SOLID", "SHELL"})
ALIGN_MODES = ("bbox", "none")
_VOLUME_EPS = 1e-6


class ProofDiffError(ValueError):
    """An input could not be read as STEP Parts."""


@dataclass(frozen=True)
class Tolerance:
    volume: float = VOLUME_TOLERANCE
    bbox_mm: float = BBOX_TOLERANCE_MM
    two_way: float = TWO_WAY_TOLERANCE
    surface_mm: float | None = SURFACE_TOLERANCE_MM


@dataclass
class PartDiff:
    part: str
    volume_a: float
    volume_b: float
    volume_delta: float
    bbox_a: list[float]
    bbox_b: list[float]
    bbox_side_delta_mm: float
    bbox_corner_delta_mm: float | None
    only_a: float | None
    only_b: float | None
    two_way: float | None
    boolean: str
    surface_deviation_mm: float | None
    passed: bool
    reasons: list[str] = field(default_factory=list)


# --------------------------------------------------------------------- reading


def _import_step(path: Path):
    import build123d as bd  # deferred: the CLI's --help must not load OCP

    if not path.is_file():
        raise ProofDiffError(f"{path}: no such STEP file")
    try:
        shape = bd.import_step(str(path))
    except Exception as exc:  # OCP raises many types
        raise ProofDiffError(f"{path}: not a readable STEP file ({type(exc).__name__})") from exc
    return shape


def read_parts(path: Path) -> dict[str, Any]:
    """Return ``{part name: solid-or-compound}`` for one STEP file."""

    import build123d as bd

    shape = _import_step(path)
    if not list(shape.solids()):
        raise ProofDiffError(f"{path}: holds no solid")
    # Labels live on the import tree's nodes; ``shape.solids()`` returns
    # fresh wrappers without them. A labelled Solid, or a labelled leaf
    # Compound of solids, is one Part.
    labelled: dict[str, list[Any]] = {}
    unlabelled: list[Any] = []

    def walk(node) -> None:
        children = list(getattr(node, "children", ()) or ())
        if children:
            for child in children:
                walk(child)
            return
        node_solids = list(node.solids())
        if not node_solids:
            return
        label = (node.label or "").strip()
        if label and label.upper() not in _DEFAULT_LABELS:
            labelled.setdefault(label, []).extend(node_solids)
        else:
            unlabelled.extend(node_solids)

    walk(shape)
    parts: dict[str, Any] = {}
    for label, group in labelled.items():
        parts[label] = group[0] if len(group) == 1 else bd.Compound(group)
    if unlabelled:
        name = path.name.removesuffix(".step")
        if name in parts:
            name = f"{name}:unlabelled"
        parts[name] = unlabelled[0] if len(unlabelled) == 1 else bd.Compound(unlabelled)
    return parts


# ------------------------------------------------------------------- measuring


def _bbox(shape) -> list[float]:
    box = shape.bounding_box()
    return [box.min.X, box.min.Y, box.min.Z, box.max.X, box.max.Y, box.max.Z]


def _sides(box: Sequence[float]) -> list[float]:
    return [box[3] - box[0], box[4] - box[1], box[5] - box[2]]


def _translate_min_corner(shape, source_box: Sequence[float], target_box: Sequence[float]):
    import build123d as bd

    offset = bd.Vector(
        target_box[0] - source_box[0],
        target_box[1] - source_box[1],
        target_box[2] - source_box[2],
    )
    return shape.moved(bd.Location(offset))


def _surface_points(shape, tolerance: float = 0.02) -> list[Any]:
    vertices, _ = shape.tessellate(tolerance, 0.2)
    if len(vertices) > _MAX_SURFACE_POINTS:
        step = math.ceil(len(vertices) / _MAX_SURFACE_POINTS)
        vertices = vertices[::step]
    return vertices


def _one_sided_deviation(points: Sequence[Any], target) -> float:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
    from OCP.BRepExtrema import BRepExtrema_DistShapeShape
    from OCP.gp import gp_Pnt

    distance = BRepExtrema_DistShapeShape()
    distance.LoadS1(target.wrapped)
    worst = 0.0
    for point in points:
        distance.LoadS2(BRepBuilderAPI_MakeVertex(gp_Pnt(point.X, point.Y, point.Z)).Vertex())
        distance.Perform()
        if not distance.IsDone():
            raise ArithmeticError("distance not computed")
        worst = max(worst, distance.Value())
    return worst


def surface_deviation(a, b) -> float:
    """Largest distance from either Part's surface to the other's (mm).

    Points are the tessellation vertices of each surface; distances go to the
    other Part's faces, not its solid, so a point inside still measures.
    """

    import build123d as bd

    shell_a = bd.Compound(a.faces())
    shell_b = bd.Compound(b.faces())
    return max(
        _one_sided_deviation(_surface_points(a), shell_b),
        _one_sided_deviation(_surface_points(b), shell_a),
    )


def _default_boolean(a, b) -> tuple[float, float]:
    only_a = a.cut(b).volume
    only_b = b.cut(a).volume
    return only_a, only_b


def diff_part(
    name: str,
    a,
    b,
    *,
    align: str = "bbox",
    tolerance: Tolerance = Tolerance(),
    boolean: Callable[[Any, Any], tuple[float, float]] = _default_boolean,
    surface: Callable[[Any, Any], float] = surface_deviation,
) -> PartDiff:
    if align not in ALIGN_MODES:
        raise ProofDiffError(f"align must be one of {ALIGN_MODES}, not {align!r}")
    volume_a = float(a.volume)
    volume_b = float(b.volume)
    box_a = _bbox(a)
    box_b = _bbox(b)
    reasons: list[str] = []

    if volume_a <= _VOLUME_EPS:
        raise ProofDiffError(f"{name}: approved Part has no volume")
    volume_delta = abs(volume_b - volume_a) / volume_a
    if volume_delta > tolerance.volume:
        reasons.append(f"volume differs by {volume_delta:.2%} (limit {tolerance.volume:.0%})")

    side_delta = max(abs(x - y) for x, y in zip(_sides(box_a), _sides(box_b)))
    if side_delta > tolerance.bbox_mm:
        reasons.append(
            f"bounding-box side differs by {side_delta:.3f} mm (limit {tolerance.bbox_mm} mm)"
        )
    corner_delta: float | None = None
    if align == "none":
        corner_delta = max(abs(box_a[i] - box_b[i]) for i in range(3))
        if corner_delta > tolerance.bbox_mm:
            reasons.append(
                f"position differs by {corner_delta:.3f} mm (limit {tolerance.bbox_mm} mm)"
            )

    b_aligned = _translate_min_corner(b, box_b, box_a) if align == "bbox" else b
    only_a: float | None
    only_b: float | None
    two_way: float | None
    status = "ok"
    try:
        only_a, only_b = boolean(a, b_aligned)
        only_a = float(only_a)
        only_b = float(only_b)
        bad = (
            not math.isfinite(only_a)
            or not math.isfinite(only_b)
            or only_a < -_VOLUME_EPS
            or only_b < -_VOLUME_EPS
            or only_a > volume_a * (1 + 1e-6) + _VOLUME_EPS
            or only_b > volume_b * (1 + 1e-6) + _VOLUME_EPS
            # A - B = only_a - only_b exactly; a kernel failure that returns
            # one operand unchanged breaks this identity (K4's faceted wink).
            or abs((only_a - only_b) - (volume_a - volume_b))
            > _IDENTITY_SLACK * max(volume_a, volume_b) + _VOLUME_EPS
        )
        if bad:
            raise ArithmeticError("impossible Boolean volume")
    except Exception:
        only_a = only_b = two_way = None
        status = "failed"
    else:
        only_a = max(only_a, 0.0)
        only_b = max(only_b, 0.0)
        two_way = (only_a + only_b) / max(volume_a, volume_b)
        if two_way > tolerance.two_way:
            reasons.append(
                f"two-way difference is {two_way:.2%} of volume (limit {tolerance.two_way:.0%})"
            )
    deviation: float | None
    try:
        deviation = float(surface(a, b_aligned))
        if not math.isfinite(deviation):
            raise ArithmeticError("non-finite deviation")
    except Exception:
        deviation = None
        if tolerance.surface_mm is not None:
            reasons.append("surface deviation could not be measured")
    else:
        if tolerance.surface_mm is not None and deviation > tolerance.surface_mm:
            reasons.append(
                f"surface deviates by {deviation:.3f} mm (limit {tolerance.surface_mm} mm)"
            )
    return PartDiff(
        part=name,
        volume_a=volume_a,
        volume_b=volume_b,
        volume_delta=volume_delta,
        bbox_a=box_a,
        bbox_b=box_b,
        bbox_side_delta_mm=side_delta,
        bbox_corner_delta_mm=corner_delta,
        only_a=only_a,
        only_b=only_b,
        two_way=two_way,
        boolean=status,
        surface_deviation_mm=deviation,
        passed=not reasons,
        reasons=reasons,
    )


# ------------------------------------------------------------------ comparing


def _step_files(directory: Path) -> dict[str, Path]:
    files = {p.name: p for p in sorted(directory.glob("part_*.step")) if p.is_file()}
    if not files:
        raise ProofDiffError(f"{directory}: holds no part_*.step file")
    return files


def _pairs(approved: Path, built: Path) -> tuple[list[tuple[str, Path, Path]], list[str], list[str]]:
    if approved.is_dir() != built.is_dir():
        raise ProofDiffError("compare two STEP files or two directories, not one of each")
    if not approved.is_dir():
        return [(approved.name, approved, built)], [], []
    a = _step_files(approved)
    b = _step_files(built)
    pairs = [(name, a[name], b[name]) for name in sorted(a.keys() & b.keys())]
    return pairs, sorted(a.keys() - b.keys()), sorted(b.keys() - a.keys())


def compare(
    approved: Path,
    built: Path,
    *,
    align: str = "bbox",
    tolerance: Tolerance = Tolerance(),
    boolean: Callable[[Any, Any], tuple[float, float]] = _default_boolean,
    surface: Callable[[Any, Any], float] = surface_deviation,
) -> dict[str, Any]:
    """Compare an approved STEP (or directory) with a built one; return the report."""

    approved = Path(approved)
    built = Path(built)
    pairs, missing_files, extra_files = _pairs(approved, built)
    parts: list[dict[str, Any]] = []
    missing_parts: list[str] = [f"{name}" for name in missing_files]
    extra_parts: list[str] = [f"{name}" for name in extra_files]
    for file_name, a_path, b_path in pairs:
        a_parts = read_parts(a_path)
        b_parts = read_parts(b_path)
        prefix = f"{file_name}/" if approved.is_dir() else ""
        if len(a_parts) == 1 and len(b_parts) == 1:
            # A one-Part Component: its label is naming, not shape.
            (only_name,) = a_parts
            b_parts = {only_name: next(iter(b_parts.values()))}
        for name in sorted(a_parts.keys() - b_parts.keys()):
            missing_parts.append(prefix + name)
        for name in sorted(b_parts.keys() - a_parts.keys()):
            extra_parts.append(prefix + name)
        for name in sorted(a_parts.keys() & b_parts.keys()):
            result = diff_part(
                prefix + name,
                a_parts[name],
                b_parts[name],
                align=align,
                tolerance=tolerance,
                boolean=boolean,
                surface=surface,
            )
            parts.append(asdict(result))
    passed = all(p["passed"] for p in parts) and not missing_parts and not extra_parts
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": TOOL,
        "approved": str(approved),
        "built": str(built),
        "align": align,
        "tolerance": asdict(tolerance),
        "passed": passed,
        "boolean_failed": sorted(p["part"] for p in parts if p["boolean"] == "failed"),
        "missing": missing_parts,
        "extra": extra_parts,
        "parts": parts,
    }


def summary_lines(report: Mapping[str, Any]) -> Iterable[str]:
    for part in report["parts"]:
        two_way = "boolean failed" if part["two_way"] is None else f"two-way {part['two_way']:.2%}"
        surf = part["surface_deviation_mm"]
        two_way += ", surface n/a" if surf is None else f", surface {surf:.3f} mm"
        verdict = "PASS" if part["passed"] else "FAIL"
        yield (
            f"{verdict} {part['part']}: dV {part['volume_delta']:.2%}, "
            f"box {part['bbox_side_delta_mm']:.3f} mm, {two_way}"
            + (f" — {'; '.join(part['reasons'])}" if part["reasons"] else "")
        )
    for name in report["missing"]:
        yield f"FAIL {name}: missing from the built side"
    for name in report["extra"]:
        yield f"FAIL {name}: not in the Approved Proof"
    yield "passed" if report["passed"] else "over tolerance"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="proof_diff", description=__doc__.split("\n\n")[0])
    parser.add_argument("approved", type=Path, help="the Approved Proof's STEP file or directory")
    parser.add_argument("built", type=Path, help="the built STEP file or directory")
    parser.add_argument(
        "--align",
        choices=ALIGN_MODES,
        default="bbox",
        help="bbox (print stance: align minimum corners before the Boolean) or "
        "none (Display Pose: position counts)",
    )
    parser.add_argument("--json", type=Path, help="write the report here")
    parser.add_argument(
        "--surface-limit",
        type=float,
        default=SURFACE_TOLERANCE_MM,
        metavar="MM",
        help="also fail a Part whose surface deviates by more than MM (default: report only)",
    )
    args = parser.parse_args(argv)
    try:
        report = compare(
            args.approved,
            args.built,
            align=args.align,
            tolerance=Tolerance(surface_mm=args.surface_limit),
        )
    except ProofDiffError as exc:
        print(f"proof_diff: {exc}", file=sys.stderr)
        return 2
    for line in summary_lines(report):
        print(line)
    if args.json:
        args.json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if report["passed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
