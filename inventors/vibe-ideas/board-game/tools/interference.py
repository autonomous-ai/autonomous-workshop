#!/usr/bin/env python3
"""interference.py — do two separate pieces try to occupy the same space?

    python3 board-game/tools/interference.py <assembled.stl> [--parts-dir DIR]

The gate measures each part on its own: is it one closed body, does it fit the
bed, will it print. None of that can see the defect where two parts that are
never booleaned together are nevertheless modelled overlapping — a disc whose
underside eats the knob of a tile resting in its well, a pin longer than the
hole it seats in. Nothing errors, because nothing was ever unioned; the parts
are placed by coordinate and the overlap is simply drawn.

This module answers that one question, for every pair, with a number.

WHY VOLUME AND NOT DISTANCE OR VERTEX-CONTAINMENT

Two solids that legitimately touch — a disc resting flush on a ledge, a tile
seated in a well whose floor it sits on — have a surface-to-surface distance of
exactly 0. So does a solid buried 9mm inside another. Distance cannot tell
"seated correctly" from "jammed", and on Armillary it reported 0.000mm for all
twenty legitimate contacts.

Vertex-containment ("is any vertex of A inside B") is worse than useless here:
it is structurally blind to a peg passing through a plate, which is the single
most common interference in a board game (knob in well, pin in hole, tab in
slot). A cylinder's vertices all sit on its two end rings; when it passes
through a plate those rings are above and below the material, so no vertex of
either solid is inside the other. Measured on Armillary: mask_disc_a buries
210mm3 of four seated tiles' knobs, and vertex-containment found 0 of 500
sampled points inside.

Interference VOLUME separates the two cleanly, because coincident faces enclose
no volume. Measured on Armillary: all twenty legitimate contacts came out at
0.0mm3, the four real jams at 210-253mm3. Three orders of magnitude of margin
is what makes a threshold honest rather than tuned.

HOW

1. broad phase   Split the ASSEMBLED mesh into connected components — that is
                 the only geometry that carries assembly pose. Per-part STLs
                 are each in their own local frame and cannot be compared to
                 each other at all. Then keep only pairs whose padded AABBs
                 overlap. AABB non-overlap is a conservative PROOF of
                 non-collision, so this prunes without ever hiding a real
                 finding: on Armillary 741 pairs drop to 56.

                 Note this is the opposite direction from the bbox-overlap
                 antipattern: bbox overlap is not evidence of a defect and is
                 never reported as one. It is only ever used to skip work.

2. narrow phase  Sample the box where the two AABBs overlap and count the
                 points interior to BOTH meshes, by ray-parity. Volume is
                 (points in both / points sampled) * box volume.

3. motion        Steps 1-2 judge ONE pose: the arrangement the assembly happened
                 to be exported in. That pose is not evidence about any other,
                 and a builder naturally exports a legal one. Armillary is the
                 worked example: turn mask_disc_a half an index step and all ten
                 tiles jam instead of four, and no still frame shows it.

                 So a project may declare its moving parts in `motion.json`, and
                 each is swept through its stated range against everything else:

                   {"motions": [
                     {"part": "mask_disc_a", "kind": "rotation",
                      "axis_point": [0,0,0], "axis_direction": [0,0,1],
                      "range_deg": [0,360], "steps": 20}]}

                 `kind` is "rotation" or "linear" (which takes a `vector`). What
                 is declared is the AXIS and the RANGE — design facts, written
                 in the brief before any geometry existed. It never declares
                 which position is the bad one: predicting that is the job being
                 automated, and a builder who could predict it would have fixed
                 it instead. Findings say whether the pair was clean at rest,
                 because "clean at rest, buried at 30deg" is exactly the finding
                 a single pose cannot produce.

                 A project that declares nothing is swept nowhere. Nothing here
                 can tell that a game HAS moving parts — that has to come from
                 the brief, and does not yet.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Thresholds — code tier, same rule as gate.py: PR only, never tuned at runtime.
# ---------------------------------------------------------------------------

# Tessellation noise floor. Two curved faces meeting flush are approximated by
# flat triangles that criss-cross each other by a fraction of a chord, which
# encloses a tiny but non-zero volume. Same reasoning and same number as
# gate.py's MIN_BODY_VOLUME_MM3, which rejects sliver bodies for the identical
# reason. Measured legitimate contacts on Armillary sit at 0.0mm3, and the real
# defects at 210mm3+, so nothing in between has been observed to need tuning.
INTERFERENCE_VOLUME_MM3 = 20.0

# Padding on each AABB before the overlap test. Two parts designed to touch can
# land a hair apart through float error; widening the broad phase keeps them in
# the narrow phase, where the volume measure correctly reports 0 rather than
# being silently pruned as "far apart". Cheap: on Armillary this admitted one
# extra pair out of 741.
BROAD_PHASE_MARGIN_MM = 0.5

# Sampling budget per pair. The measure's sensitivity is the cell volume, so it
# is pinned to the threshold rather than to a point count: cells must be small
# enough that a defect at the threshold still lands several of them.
CELLS_PER_THRESHOLD_VOLUME = 8
MAX_GRID_POINTS = 200_000
MIN_GRID_POINTS = 512


# ---------------------------------------------------------------------------
# Placed components
# ---------------------------------------------------------------------------

def load_placed_components(assembled_stl: Path, min_volume_mm3: float = 20.0) -> list:
    """Connected components of the assembled mesh, in assembly pose.

    Splitting the assembled export is what makes this work without any change
    to cadcode: loose pieces are never booleaned, so each is already its own
    mesh island, carrying the transform the assembly placed it with.

    The volume floor drops tessellation slivers, which would otherwise become
    phantom "parts" that interfere with everything near them.
    """
    import trimesh

    mesh = trimesh.load(str(assembled_stl), force="mesh")
    pieces = mesh.split(only_watertight=False)
    if not len(pieces):
        pieces = [mesh]
    return [p for p in pieces if abs(p.volume) >= min_volume_mm3]


def name_components(components: list, part_volumes: dict[str, float] | None) -> list[str]:
    """Label each placed component with the part name it is an instance of.

    Volume is invariant under the rigid transforms an assembly applies, so it
    identifies which part a component is an instance of without needing the
    transform itself. Identical pieces share a volume and so share a name with
    an instance index, which is correct — they are interchangeable.

    Falls back to positional labels when no part volumes are available; the
    findings are still true, just harder to read.
    """
    labels: list[str] = []
    used: dict[str, int] = {}
    for index, comp in enumerate(components):
        name = None
        if part_volumes:
            vol = abs(comp.volume)
            matches = sorted(
                {n for n, v in part_volumes.items()
                 if abs(v - vol) <= max(1e-3 * max(v, vol), 1e-6)}
            )
            if len(matches) == 1:
                name = matches[0]
            elif len(matches) > 1:
                # Same volume, several names: a family of interchangeable pieces
                # (star_tile_01..12). Collapse to the family stem rather than
                # listing all twelve — which piece of the family it is carries no
                # information, since they are identical by design.
                stems = sorted({re.sub(r"_\d+$", "", n) for n in matches})
                name = stems[0] if len(stems) == 1 else "|".join(stems)
        if name is None:
            name = f"component_{index:03d}"
        used[name] = used.get(name, 0) + 1
        labels.append(name if used[name] == 1 else f"{name}#{used[name]}")
    return labels


def part_volumes_from_stls(part_stls: dict[str, Path]) -> dict[str, float]:
    import trimesh

    out: dict[str, float] = {}
    for name, path in part_stls.items():
        try:
            out[name] = abs(trimesh.load(str(path), force="mesh").volume)
        except Exception:
            continue
    return out


# ---------------------------------------------------------------------------
# Broad phase
# ---------------------------------------------------------------------------

def aabb_overlaps(a, b, margin_mm: float = BROAD_PHASE_MARGIN_MM) -> bool:
    """Conservative: True whenever the padded boxes touch.

    False here is a proof that the meshes cannot intersect, which is the only
    reason it is safe to skip the narrow phase on it.
    """
    amin, amax = a.bounds
    bmin, bmax = b.bounds
    for axis in range(3):
        if amin[axis] - margin_mm > bmax[axis] or bmin[axis] - margin_mm > amax[axis]:
            return False
    return True


def candidate_pairs(components: list, margin_mm: float = BROAD_PHASE_MARGIN_MM) -> list[tuple[int, int]]:
    pairs = []
    for i in range(len(components)):
        for j in range(i + 1, len(components)):
            if aabb_overlaps(components[i], components[j], margin_mm):
                pairs.append((i, j))
    return pairs


# ---------------------------------------------------------------------------
# Narrow phase
# ---------------------------------------------------------------------------

class _ZRayIndex:
    """Point-in-mesh by counting surface crossings on a ray straight up (+Z).

    Written out rather than delegated to `trimesh.contains` because that path
    needs `rtree`, which is not installed in this repo's venv.

    The reason for the XY bucket index rather than a plain loop over triangles:
    testing every point against every triangle is what makes the naive version
    unaffordable. Measured on Armillary, the three plinth-versus-disc pairs
    alone cost 86 of 102 seconds, because a disc's footprint covers the whole
    board, so the shared box is large, and the resolution the threshold demands
    turns that into ~176k sample points, each tested against the plinth's 3994
    triangles. Bucketing the triangles by their XY footprint cuts the candidates
    per point down to the handful that actually sit above it.

    +Z exactly, rather than the skewed direction a general-purpose intersector
    would pick, is what allows the index: the ray does not move in XY as it
    rises, so a point's candidate set is exactly one bucket. A triangle standing
    exactly vertical projects to zero XY area and is skipped, which is correct —
    a vertical wall does not cross a vertical ray anywhere but in its own plane.
    """

    __slots__ = ("tris", "origin", "step", "cells", "buckets", "empty")

    def __init__(self, mesh, cells: int = 64):
        import numpy as np

        tris = np.asarray(mesh.triangles, dtype=float)
        self.tris = tris
        self.empty = not len(tris)
        if self.empty:
            self.buckets = {}
            return

        bounds_lo = tris[:, :, :2].reshape(-1, 2).min(axis=0)
        bounds_hi = tris[:, :, :2].reshape(-1, 2).max(axis=0)
        self.origin = bounds_lo
        self.cells = cells
        self.step = np.maximum((bounds_hi - bounds_lo) / cells, 1e-9)

        tri_lo = tris[:, :, :2].min(axis=1)
        tri_hi = tris[:, :, :2].max(axis=1)
        cell_lo = np.clip(((tri_lo - self.origin) / self.step).astype(int), 0, cells - 1)
        cell_hi = np.clip(((tri_hi - self.origin) / self.step).astype(int), 0, cells - 1)

        buckets: dict[int, list[int]] = {}
        for index in range(len(tris)):
            for ix in range(cell_lo[index, 0], cell_hi[index, 0] + 1):
                for iy in range(cell_lo[index, 1], cell_hi[index, 1] + 1):
                    buckets.setdefault(ix * cells + iy, []).append(index)
        self.buckets = {key: np.asarray(v, dtype=int) for key, v in buckets.items()}

    def contains(self, points):
        import numpy as np

        out = np.zeros(len(points), dtype=bool)
        if self.empty or not len(points):
            return out

        keys = np.clip(((points[:, :2] - self.origin) / self.step).astype(int),
                       0, self.cells - 1)
        flat = keys[:, 0] * self.cells + keys[:, 1]

        for key in np.unique(flat):
            candidates = self.buckets.get(int(key))
            if candidates is None:
                continue
            sel = np.flatnonzero(flat == key)
            block = points[sel]
            tris = self.tris[candidates]

            ax, ay, az = tris[:, 0, 0], tris[:, 0, 1], tris[:, 0, 2]
            bx, by, bz = tris[:, 1, 0], tris[:, 1, 1], tris[:, 1, 2]
            cx, cy, cz = tris[:, 2, 0], tris[:, 2, 1], tris[:, 2, 2]

            # Signed XY area; zero means the triangle stands vertical.
            denom = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            live = np.abs(denom) > 1e-12
            if not live.any():
                continue

            px = block[:, 0][:, None]
            py = block[:, 1][:, None]
            pz = block[:, 2][:, None]

            with np.errstate(divide="ignore", invalid="ignore"):
                inv = np.where(live, 1.0 / denom, 0.0)[None, :]
                w0 = ((bx - px) * (cy - py) - (by - py) * (cx - px)) * inv
                w1 = ((cx - px) * (ay - py) - (cy - py) * (ax - px)) * inv
            w2 = 1.0 - w0 - w1

            tol = -1e-9
            hit_xy = live[None, :] & (w0 >= tol) & (w1 >= tol) & (w2 >= tol)
            z_hit = w0 * az[None, :] + w1 * bz[None, :] + w2 * cz[None, :]
            crossings = (hit_xy & (z_hit > pz + 1e-9)).sum(axis=1)
            out[sel] = (crossings % 2) == 1

        return out


def _points_inside(points, mesh, _cache: dict = {}):
    """Cached wrapper: one index per mesh, reused across every pair it appears in."""
    key = id(mesh)
    index = _cache.get(key)
    if index is None:
        index = _ZRayIndex(mesh)
        _cache[key] = index
    return index.contains(points)


def _transform_points(points, matrix):
    import numpy as np

    if matrix is None:
        return points
    return points @ np.asarray(matrix)[:3, :3].T + np.asarray(matrix)[:3, 3]


def _transformed_bounds(mesh, matrix):
    """Exact AABB of the mesh after the transform, from its own vertices.

    Transforming the eight corners of the existing AABB instead would be
    conservative but loose, and a looser box only wastes sample points.
    """
    import numpy as np

    if matrix is None:
        return mesh.bounds
    moved = _transform_points(np.asarray(mesh.vertices, dtype=float), matrix)
    return np.array([moved.min(axis=0), moved.max(axis=0)])


def _overlap_box(a, b, a_matrix=None):
    import numpy as np

    a_bounds = _transformed_bounds(a, a_matrix)
    lo = np.maximum(a_bounds[0], b.bounds[0])
    hi = np.minimum(a_bounds[1], b.bounds[1])
    if np.any(hi <= lo):
        return None, None
    return lo, hi


def interference_volume_mm3(a, b, threshold_mm3: float = INTERFERENCE_VOLUME_MM3,
                            a_matrix=None) -> dict:
    """Volume the two solids both claim, by sampling the box they share.

    Resolution is derived from the threshold, not fixed: cells are sized so a
    defect right at the threshold still lands CELLS_PER_THRESHOLD_VOLUME of
    them. `resolution_mm3` is reported so a reader can see the sensitivity that
    produced the number instead of trusting it blind — and `resolution_capped`
    says when the box was too large to hold that resolution inside the point
    budget, which makes the reported volume a lower bound.
    """
    import numpy as np

    lo, hi = _overlap_box(a, b, a_matrix)
    if lo is None:
        return {"volume_mm3": 0.0, "sampled": 0, "resolution_mm3": None,
                "resolution_capped": False, "note": "no AABB overlap"}

    extents = hi - lo
    box_volume = float(np.prod(extents))

    # The shared volume cannot exceed the box that contains it, so a box smaller
    # than the threshold can never produce a finding and is not worth sampling.
    # This is also what makes near-degenerate boxes cheap: two flats that meet
    # at a grazing angle leave a slab microns thick and hundreds of mm wide,
    # which the static pass never sees (exactly coincident planes give a
    # zero-extent box, caught above) but a rotation sweep produces constantly.
    if box_volume <= threshold_mm3:
        return {"volume_mm3": 0.0, "sampled": 0,
                "resolution_mm3": None, "resolution_capped": False,
                "note": "shared box smaller than the threshold"}

    target_cell = threshold_mm3 / CELLS_PER_THRESHOLD_VOLUME
    wanted = box_volume / target_cell if target_cell > 0 else MIN_GRID_POINTS
    total = int(min(MAX_GRID_POINTS, max(MIN_GRID_POINTS, wanted)))
    capped = wanted > MAX_GRID_POINTS

    # Split the budget across axes in proportion to extent, so cells stay
    # roughly cubic and a thin overlap slab is not sampled with one layer.
    scale = (total / box_volume) ** (1.0 / 3.0) if box_volume > 0 else 1.0
    counts = [max(2, int(round(e * scale))) for e in extents]

    # Then enforce the budget on the PRODUCT, which is what actually costs.
    # Sizing each axis independently and flooring it at 2 lets an anisotropic
    # box run away: 215 x 215 x 1e-9 asks for billions of points from a budget
    # of 512. Measured before this clamp existed: 16.7GB resident and the
    # process killed, on Armillary's own discs the moment they were swept.
    # Shrink proportionally first — halving the longest axis to fix a 3%
    # overshoot would throw away half the resolution for nothing — and keep the
    # halving loop only as the backstop for boxes so anisotropic that the
    # proportional pass cannot get under the budget.
    product = counts[0] * counts[1] * counts[2]
    if product > total:
        shrink = (total / product) ** (1.0 / 3.0)
        counts = [max(2, int(count * shrink)) for count in counts]
    while counts[0] * counts[1] * counts[2] > total:
        axis = max(range(3), key=lambda i: counts[i])
        if counts[axis] <= 2:
            break
        counts[axis] = max(2, counts[axis] // 2)

    axes = [lo[i] + (np.arange(counts[i]) + 0.5) * (extents[i] / counts[i]) for i in range(3)]
    grid = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
    cell_volume = box_volume / len(grid)

    # A moving part is never re-meshed. Asking "is this world point inside the
    # MOVED solid" is the same question as "is the point pulled back through
    # the motion inside the solid where it was built", so the sweep maps the
    # sample points instead — which keeps A's spatial index built once and
    # valid at every step, rather than rebuilding it per angle.
    probe = grid if a_matrix is None else _transform_points(grid, np.linalg.inv(a_matrix))
    in_a = _points_inside(probe, a)
    if not in_a.any():
        return {"volume_mm3": 0.0, "sampled": int(len(grid)),
                "resolution_mm3": round(cell_volume, 4),
                "resolution_capped": capped, "note": ""}
    in_both = _points_inside(grid[in_a], b)

    return {"volume_mm3": round(float(in_both.sum()) * cell_volume, 2),
            "sampled": int(len(grid)),
            "resolution_mm3": round(cell_volume, 4),
            "resolution_capped": capped,
            "note": ""}


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------

def _motion_steps(motion: dict) -> list[tuple[str, object]]:
    """(label, 4x4 matrix) for each sampled position along a declared motion.

    What a motion declares is the AXIS and the RANGE — design facts, stated in
    the brief long before any geometry exists ("the disc turns in 36deg index
    steps"). It deliberately does NOT declare which position is the bad one:
    predicting that is the whole job being automated, and a builder who could
    predict it would have fixed it instead.
    """
    import numpy as np
    import trimesh

    kind = str(motion.get("kind", "rotation")).lower()
    steps = int(motion.get("steps", 12))
    if steps < 1:
        raise ValueError("a motion needs at least one step")

    if kind == "rotation":
        point = np.asarray(motion.get("axis_point", [0.0, 0.0, 0.0]), dtype=float)
        direction = np.asarray(motion.get("axis_direction", [0.0, 0.0, 1.0]), dtype=float)
        if np.linalg.norm(direction) <= 1e-12:
            raise ValueError("axis_direction must be non-zero")
        start, end = [float(v) for v in motion.get("range_deg", [0.0, 360.0])]
        out = []
        for index in range(steps + 1):
            angle = start + (end - start) * (index / steps)
            matrix = trimesh.transformations.rotation_matrix(
                np.deg2rad(angle), direction, point)
            out.append((f"{angle:.1f}deg", matrix))
        return out

    if kind == "linear":
        vector = np.asarray(motion.get("vector", [0.0, 0.0, 0.0]), dtype=float)
        out = []
        for index in range(steps + 1):
            fraction = index / steps
            matrix = np.eye(4)
            matrix[:3, 3] = vector * fraction
            out.append((f"{fraction * float(np.linalg.norm(vector)):.1f}mm", matrix))
        return out

    raise ValueError(f"unknown motion kind: {kind!r}")


def load_motions(path: Path) -> list[dict]:
    """Read a project's motion.json. Absent is not an error on its own — most
    parts of most games do not move — but see `unswept_moving_parts` for why
    absence cannot be allowed to mean "nothing moves"."""
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    motions = data.get("motions", data) if isinstance(data, dict) else data
    return [m for m in motions if isinstance(m, dict)]


# Interface kinds in a brief that describe a part moving against another, as
# opposed to the static fit that `seats` / `joins` / `stacks` describe.
MOVING_INTERFACE_KINDS = ("turns", "slides")


def moving_parts_from_brief(brief: dict | None) -> list[str]:
    """Parts the BRIEF says move.

    This is what closes the loop. Sweeping is driven by motion.json, which the
    builder writes — and a builder who forgets it gets a silent pass, because
    nothing in the geometry says "this was meant to turn". The brief does say
    so, upstream of any build, so it is the thing that can require the sweep to
    have happened.

    Same shape as the rule that a brief with interfaces and no fit_checks.py
    has verified nothing: the declaration that something must be checked lives
    with the design, not with the person who would rather not check it.
    """
    out: list[str] = []
    for interface in ((brief or {}).get("interfaces") or []):
        if str(interface.get("kind", "")).lower() not in MOVING_INTERFACE_KINDS:
            continue
        name = interface.get("piece") or interface.get("a")
        if name:
            out.append(str(name))
    return sorted(set(out))


def unswept_moving_parts(brief: dict | None, motions: list[dict] | None) -> list[str]:
    """Parts the brief says move that no declared motion sweeps."""
    declared = {str(m.get("part", "")) for m in (motions or [])}
    return [p for p in moving_parts_from_brief(brief) if p not in declared]


def _resolve_part(names: list[str], wanted: str) -> int | None:
    if wanted in names:
        return names.index(wanted)
    prefixed = [i for i, n in enumerate(names) if n.split("#")[0] == wanted]
    return prefixed[0] if len(prefixed) == 1 else None


def sweep_motion(components: list, names: list[str], motion: dict,
                 threshold_mm3: float = INTERFERENCE_VOLUME_MM3,
                 margin_mm: float = BROAD_PHASE_MARGIN_MM) -> list[dict]:
    """Move one part through its declared range; measure it against the rest.

    Reports the WORST position per pair, and whether the pair was clean at the
    first sampled position — because "clean at rest, buried at 30deg" is the
    finding the static pass structurally cannot produce, and saying so is what
    stops it being read as a duplicate of one.
    """
    moving = _resolve_part(names, str(motion.get("part", "")))
    if moving is None:
        raise KeyError(f"motion names part {motion.get('part')!r}, which is not "
                       f"one of the placed components")

    steps = _motion_steps(motion)
    worst: dict[int, dict] = {}

    for position, (label, matrix) in enumerate(steps):
        bounds = _transformed_bounds(components[moving], matrix)
        for other in range(len(components)):
            if other == moving:
                continue
            if not components[other].is_watertight or not components[moving].is_watertight:
                continue
            other_bounds = components[other].bounds
            if any(bounds[0][axis] - margin_mm > other_bounds[1][axis]
                   or other_bounds[0][axis] - margin_mm > bounds[1][axis]
                   for axis in range(3)):
                continue
            result = interference_volume_mm3(components[moving], components[other],
                                             threshold_mm3, a_matrix=matrix)
            volume = result["volume_mm3"]
            record = worst.get(other)
            if record is None:
                record = {"a": names[moving], "b": names[other],
                          "volume_mm3": 0.0, "at": None,
                          "clear_at_first_position": True,
                          "resolution_mm3": result["resolution_mm3"],
                          "resolution_capped": result["resolution_capped"]}
                worst[other] = record
            if position == 0 and volume > threshold_mm3:
                record["clear_at_first_position"] = False
            if volume > record["volume_mm3"]:
                record.update(volume_mm3=volume, at=label,
                              resolution_mm3=result["resolution_mm3"],
                              resolution_capped=result["resolution_capped"])

    return [r for r in worst.values() if r["volume_mm3"] > 0.0]


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def check_interference(
    assembled_stl: Path,
    part_stls: dict[str, Path] | None = None,
    expected_components: int | None = None,
    threshold_mm3: float = INTERFERENCE_VOLUME_MM3,
    margin_mm: float = BROAD_PHASE_MARGIN_MM,
    motions: list[dict] | None = None,
) -> dict:
    """Every placed pair, measured. Returns a report; the caller decides.

    `expected_components` guards the one way this check can quietly measure
    nothing: if two parts are modelled with welded coincident vertices they
    split as ONE component, and a pair that does not exist cannot be found to
    interfere. A count mismatch is therefore reported as an explicit
    inconclusive, never as a pass.
    """
    report: dict = {
        "assembled_stl": str(assembled_stl),
        "threshold_mm3": threshold_mm3,
        "broad_phase_margin_mm": margin_mm,
        "findings": [],
        "inconclusive": [],
    }

    components = load_placed_components(assembled_stl)
    report["placed_components"] = len(components)
    if len(components) < 2:
        report["note"] = "fewer than two placed components — nothing to compare"
        return report

    names = name_components(components, part_volumes_from_stls(part_stls or {}))
    report["component_names"] = names

    if expected_components is not None:
        report["expected_components"] = expected_components
        if len(components) != expected_components:
            report["inconclusive"].append(
                f"assembled mesh split into {len(components)} components but the bill "
                f"expects {expected_components} placed pieces — pairs among any welded "
                f"or fused pieces cannot be tested, so this pass is incomplete")

    open_shells = [names[i] for i, c in enumerate(components) if not c.is_watertight]
    if open_shells:
        report["inconclusive"].append(
            f"not closed, cannot test by ray parity: {', '.join(sorted(open_shells)[:8])}")

    pairs = candidate_pairs(components, margin_mm)
    report["pairs_total"] = len(components) * (len(components) - 1) // 2
    report["pairs_tested"] = len(pairs)
    report["pairs_pruned"] = report["pairs_total"] - len(pairs)

    measured = []
    for i, j in pairs:
        if not components[i].is_watertight or not components[j].is_watertight:
            continue
        result = interference_volume_mm3(components[i], components[j], threshold_mm3)
        if result["volume_mm3"] <= 0.0:
            continue
        measured.append({"a": names[i], "b": names[j], **result})

    measured.sort(key=lambda m: -m["volume_mm3"])
    report["measured_overlaps"] = measured
    report["findings"] = [
        f"interference:{m['a']} x {m['b']}: {m['volume_mm3']}mm3 of shared volume "
        f"(threshold {threshold_mm3}mm3, resolution {m['resolution_mm3']}mm3"
        + (", lower bound" if m["resolution_capped"] else "") + ")"
        for m in measured if m["volume_mm3"] > threshold_mm3
    ]

    # Declared motions. A part that moves is only as good as its worst
    # position, and the pose it happened to be exported in is not evidence
    # about any of the others.
    swept: list[dict] = []
    report["motions_declared"] = len(motions or [])
    for motion in (motions or []):
        try:
            swept.extend(sweep_motion(components, names, motion, threshold_mm3, margin_mm))
        except Exception as exc:
            report["inconclusive"].append(
                f"motion {motion.get('part', '?')}: not swept: {type(exc).__name__}: {exc}")
    swept.sort(key=lambda m: -m["volume_mm3"])
    report["swept_overlaps"] = swept
    report["findings"] += [
        f"motion:{m['a']} x {m['b']}: {m['volume_mm3']}mm3 of shared volume at "
        f"{m['at']}"
        + (" (clear at rest — no single pose could have caught this)"
           if m["clear_at_first_position"] else "")
        + f" (threshold {threshold_mm3}mm3, resolution {m['resolution_mm3']}mm3"
        + (", lower bound" if m["resolution_capped"] else "") + ")"
        for m in swept if m["volume_mm3"] > threshold_mm3
    ]

    report["pass"] = not report["findings"]
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("assembled", type=Path, help="assembled STL, in assembly pose")
    ap.add_argument("--parts-dir", type=Path,
                    help="directory of per-part STLs, used only to name findings")
    ap.add_argument("--expected-components", type=int)
    ap.add_argument("--threshold-mm3", type=float, default=INTERFERENCE_VOLUME_MM3)
    ap.add_argument("--motions", type=Path,
                    help="motion.json declaring which parts move, and how")
    ap.add_argument("--json-out", type=Path)
    args = ap.parse_args()

    part_stls: dict[str, Path] = {}
    if args.parts_dir and args.parts_dir.is_dir():
        part_stls = {p.stem: p for p in sorted(args.parts_dir.glob("*.stl"))}

    report = check_interference(
        args.assembled, part_stls,
        expected_components=args.expected_components,
        threshold_mm3=args.threshold_mm3,
        motions=load_motions(args.motions) if args.motions else None,
    )
    text = json.dumps(report, indent=2)
    if args.json_out:
        args.json_out.write_text(text, encoding="utf-8")

    print(f"{report['placed_components']} placed components, "
          f"{report['pairs_tested']}/{report['pairs_total']} pairs tested "
          f"({report['pairs_pruned']} pruned by AABB), "
          f"{report.get('motions_declared', 0)} motion(s) declared")
    for note in report["inconclusive"]:
        print(f"  INCONCLUSIVE: {note}")
    for m in report.get("measured_overlaps", []):
        mark = "FAIL" if m["volume_mm3"] > report["threshold_mm3"] else "noise"
        print(f"  [{mark}] static  {m['a']} x {m['b']}: {m['volume_mm3']}mm3 "
              f"(resolution {m['resolution_mm3']}mm3)")
    for m in report.get("swept_overlaps", []):
        mark = "FAIL" if m["volume_mm3"] > report["threshold_mm3"] else "noise"
        rest = " CLEAR AT REST" if m["clear_at_first_position"] else ""
        print(f"  [{mark}] motion  {m['a']} x {m['b']}: {m['volume_mm3']}mm3 "
              f"at {m['at']}{rest} (resolution {m['resolution_mm3']}mm3)")
    print("INTERFERENCE PASS" if report.get("pass") else "INTERFERENCE FAIL")
    return 0 if report.get("pass") else 1


if __name__ == "__main__":
    sys.exit(main())
