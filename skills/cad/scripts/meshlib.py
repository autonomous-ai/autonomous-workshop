#!/usr/bin/env python3
"""Triangle-soup primitives shared by `check_mesh` and `repair_mesh`.

The gate and the repair have to agree about what a vertex is. A weld tolerance
that differs by a decade between them turns a repaired mesh straight back into a
failing one, and the disagreement is invisible -- both sides report a number and
neither is obviously wrong. So the loader, the weld, the edge table and the
defect counts live here once, next to `cadfits.py`, and both CLIs import them.

Everything here is triangle soup in millimetres. No build123d and no OCP: these
read the STL that goes to the slicer, not the source that produced it. That is
the whole point of the pair -- `check_fit` reads the source, this reads the
artifact, and they disagree exactly when the export is stale.

Depends on numpy and scipy (connected components); the hole fill in
`repair_mesh` additionally needs shapely.

    python skills/cad/scripts/meshlib.py        # self-check
"""

from __future__ import annotations

import struct
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

WELD_TOL = 1e-6          # mm; vertices closer than this are the same vertex
SLIVER_HEIGHT = 1e-6     # mm; a triangle thinner than this is numerically a line


# --------------------------------------------------------------------------
# io
# --------------------------------------------------------------------------

def load_stl(path):
    """Return an (N, 3, 3) triangle vertex array from a binary or ASCII STL."""
    with open(path, "rb") as fh:
        head = fh.read(84)
        if head[:5] == b"solid" and b"facet" in fh.read(512):
            fh.seek(0)
            verts = [
                [float(x) for x in line.split()[1:4]]
                for line in fh.read().decode("utf-8", "replace").splitlines()
                if line.strip().startswith("vertex")
            ]
            return np.asarray(verts, dtype=np.float64).reshape(-1, 3, 3)
        count = struct.unpack("<I", head[80:84])[0]
        raw = np.frombuffer(fh.read(count * 50), dtype=np.uint8)
    if raw.size != count * 50:
        sys.exit(f"truncated STL: header claims {count} triangles")
    tri = raw.reshape(count, 50)[:, 12:48].copy().view("<f4")
    return tri.reshape(count, 3, 3).astype(np.float64)


def write_stl(path, verts, faces, header="repair_mesh"):
    """Write a binary STL, recomputing every facet normal from the winding.

    The normal is derived rather than carried through, because a repair that
    reverses a patch has to reverse its normal with it, and a stale normal is
    the one defect no downstream check looks at.
    """
    tris = verts[faces]
    normals = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    normals = np.divide(normals, lengths, out=np.zeros_like(normals), where=lengths > 0)
    payload = np.concatenate([normals[:, None, :], tris], axis=1).astype("<f4")
    record = np.zeros((len(faces), 50), dtype=np.uint8)
    record[:, :48] = payload.reshape(len(faces), 12).view(np.uint8)
    with open(path, "wb") as fh:
        fh.write(header.encode("ascii", "replace")[:80].ljust(80, b"\0"))
        fh.write(struct.pack("<I", len(faces)))
        fh.write(record.tobytes())


# --------------------------------------------------------------------------
# topology
# --------------------------------------------------------------------------

def weld(tris, tol=WELD_TOL):
    """Snap vertices to a tolerance grid and return (verts, faces)."""
    flat = tris.reshape(-1, 3)
    keys = np.round(flat / tol).astype(np.int64)
    _, first, inverse = np.unique(keys, axis=0, return_index=True, return_inverse=True)
    return flat[first], inverse.reshape(-1, 3)


def components(size, pairs):
    """Connected-component label per node over an undirected edge list."""
    if len(pairs) == 0:
        return np.arange(size)
    data = np.ones(len(pairs), dtype=np.int8)
    graph = coo_matrix((data, (pairs[:, 0], pairs[:, 1])), shape=(size, size))
    return connected_components(graph, directed=False)[1]


def edge_table(faces):
    """Undirected edges, their face counts, and the directed edges behind them.

    Directed edge `3 * f + s` is the edge leaving slot `s` of face `f`, so a
    directed index doubles as a *corner* index -- which is what the umbrella
    split below needs and what an edge dictionary cannot give you.
    """
    directed = np.stack(
        [faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]], axis=1
    ).reshape(-1, 2)
    undirected = np.sort(directed, axis=1)
    keys, inverse, counts = np.unique(
        undirected, axis=0, return_inverse=True, return_counts=True
    )
    return keys, inverse.reshape(-1), counts, directed


def sliver_metrics(verts, faces):
    """Per-face (area, height), where height is the shortest altitude.

    Area alone does not separate a sliver from a small triangle: a needle 0.15 mm
    long and a nanometre wide has an area a thousand times larger than a true
    zero, and passes any threshold set near zero. Its *height* is what is
    degenerate, so that is what gets measured.
    """
    a, b, c = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    area = 0.5 * np.linalg.norm(np.cross(b - a, c - a), axis=1)
    longest = np.maximum.reduce([
        np.linalg.norm(b - a, axis=1),
        np.linalg.norm(c - b, axis=1),
        np.linalg.norm(a - c, axis=1),
    ])
    height = np.divide(2.0 * area, longest, out=np.zeros_like(area), where=longest > 0)
    return area, height, longest


def vertex_umbrellas(faces, counts, inverse):
    """Group each vertex's incident corners into umbrellas.

    Two faces share an umbrella at a vertex only when the edge they share *at
    that vertex* is manifold. A bowtie is exactly the case where they do not:
    two cones of material meeting at a point, joined by nothing a slicer can
    walk across.

    Returns an (3F,) label array over corner indices, so corners of the same
    vertex carrying different labels are different umbrellas.
    """
    order = np.argsort(inverse, kind="stable")
    starts = np.cumsum(counts) - counts
    manifold = np.flatnonzero(counts == 2)
    first, second = order[starts[manifold]], order[starts[manifold] + 1]

    def partner(edge_index):
        """The corner at the far end of a directed edge, in its own face."""
        return 3 * (edge_index // 3) + (edge_index % 3 + 1) % 3

    # A directed edge index *is* the corner at its tail. The two faces of a
    # manifold edge normally traverse it in opposite directions, so pairing
    # tail-to-tail would join corners at *different* ends of the edge. Pair by
    # vertex identity instead, which also survives an inconsistent winding.
    corner_vertex = faces.reshape(-1)
    aligned = corner_vertex[first] == corner_vertex[second]
    tails = np.stack([first, np.where(aligned, second, partner(second))], axis=1)
    heads = np.stack([partner(first), np.where(aligned, partner(second), second)], axis=1)
    return components(3 * len(faces), np.concatenate([tails, heads]))


def boundary_directed(counts, inverse, directed):
    """The directed traversal of every edge only one face uses."""
    order = np.argsort(inverse, kind="stable")
    starts = np.cumsum(counts) - counts
    return directed[order[starts[counts == 1]]]


def summarize(verts, faces, sliver_height=SLIVER_HEIGHT):
    """Every number `check_mesh` reports and `repair_mesh` compares against."""
    area, height, longest = sliver_metrics(verts, faces)
    slivers = height <= sliver_height
    kept = faces[~slivers]

    def edge_counts(subject):
        if len(subject) == 0:
            return 0, 0, 0, 0
        keys, inverse, counts, directed = edge_table(subject)
        forward = (directed[:, 0] < directed[:, 1]).astype(np.float64)
        per_edge = np.bincount(inverse, weights=forward, minlength=len(keys))
        flipped = int(((counts == 2) & (per_edge != 1)).sum())
        return (int((counts == 1).sum()), int((counts > 2).sum()),
                flipped, int(counts.max()))

    boundary, nonmanifold, flipped, max_shared = edge_counts(kept)
    boundary_all = edge_counts(faces)[0]

    pinched = 0
    loops = 0
    boundary_z = None
    if len(kept):
        keys, inverse, counts, directed = edge_table(kept)
        labels = vertex_umbrellas(kept, counts, inverse)
        corner_vert = kept.reshape(-1)
        pairs = np.unique(np.stack([corner_vert, labels], axis=1), axis=0)
        _, per_vertex = np.unique(pairs[:, 0], return_counts=True)
        pinched = int((per_vertex > 1).sum())

        edges = boundary_directed(counts, inverse, directed)
        if len(edges):
            touched = np.unique(edges)
            labels = components(len(verts), edges)
            loops = len(np.unique(labels[touched]))
            boundary_z = (float(verts[touched, 2].min()), float(verts[touched, 2].max()))

    v0, v1, v2 = verts[kept[:, 0]], verts[kept[:, 1]], verts[kept[:, 2]]
    volume = float(np.einsum("ij,ij->i", v0, np.cross(v1, v2)).sum() / 6.0) if len(kept) else 0.0

    shells = 0
    if len(kept):
        pairs = np.concatenate([kept[:, [0, 1]], kept[:, [1, 2]]])
        labels = components(len(verts), pairs)
        shells = len(np.unique(labels[np.unique(kept)]))

    lo, hi = (verts.min(axis=0), verts.max(axis=0)) if len(verts) else (np.zeros(3), np.zeros(3))
    return {
        "triangles": int(len(faces)),
        "vertices": int(len(verts)),
        "slivers": int(slivers.sum()),
        "sliver_longest_edge": float(longest[slivers].max()) if slivers.any() else 0.0,
        "boundary": boundary,
        "boundary_with_slivers": boundary_all,
        "boundary_loops": loops,
        "boundary_z": boundary_z,
        "nonmanifold_edges": nonmanifold,
        "max_faces_per_edge": max_shared,
        "pinched_vertices": pinched,
        "flipped": flipped,
        "volume": volume,
        "shells": shells,
        "size": (hi - lo),
        "tiny": int((area[~slivers] < 0.8 ** 2).sum()),
    }


# --------------------------------------------------------------------------
# volume sampling
# --------------------------------------------------------------------------

# Cells, above which `voxel_pitch` coarsens rather than letting the machine
# swap. The binding cost is not the mask -- it is scipy's exact distance
# transform, which is float64 and allocates several intermediates on top.
# Measured end to end through `check_thickness`: 11.3 M cells peaked at 1.09 GB
# resident, and 35 M at 3.2 GB. That is ~96 bytes per cell, not the 8 the output
# array alone suggests, so budget by measurement rather than by dtype.
VOXEL_BUDGET = 12_000_000


# Offsets that keep grid sample points off round coordinates; see `voxelize`.
GRID_SKEW = np.array([2.1373, 2.2191, 2.3117])


def grid_dims(verts, pitch):
    """The grid `voxelize` will build at this pitch. Shared so the two agree."""
    lo = verts.min(axis=0) - pitch * GRID_SKEW
    return np.maximum(
        np.ceil((verts.max(axis=0) + 2 * pitch - lo) / pitch).astype(np.int64), 1)


def voxel_pitch(verts, target, budget=VOXEL_BUDGET):
    """The finest pitch at or above `target` that keeps the grid affordable.

    Solved by stepping rather than by one closed-form scale: the padding is a
    fixed number of *cells*, so it grows the grid by a few percent per axis at
    any pitch, and a formula that ignores it lands just over the budget on
    exactly the parts that are close to it.
    """
    pitch = float(target)
    for _ in range(64):
        if float(np.prod(grid_dims(verts, pitch))) <= budget:
            return pitch
        pitch *= 1.05
    return pitch


def voxelize(verts, faces, pitch):
    """Inside/outside mask on a regular grid, and the grid's origin.

    A cell is inside when the point at its centre is inside the closed surface.
    Every triangle covering an XY column's centre drops a crossing into that
    column; the crossings are then sorted by z and accumulated as a **winding
    number** rather than a parity. Parity is the usual shortcut and it is wrong
    for exactly the models this is aimed at: a hollowed part has an inner shell
    inside the outer one, and parity reads the material between them as air on
    every other span.

    A ray grazing a vertical face contributes nothing, which is correct -- the
    ray is parallel to it. Grazing a horizontal face is the one case this shares
    with every scanline fill: the two triangles either side of a silhouette edge
    both fire, and the winding sum absorbs it.
    """
    # Offset the grid off any round coordinate. A part is routinely built on
    # whole millimetres, so an unjittered grid puts sample points exactly on its
    # faces, where an inclusive point-in-triangle test counts the column at both
    # walls: a 20 mm cube at 0.5 mm came out 41 x 41 x 40 rather than 40 cubed,
    # a flat 5% over. The offsets differ per axis so a diagonal cannot realign.
    lo = verts.min(axis=0) - pitch * GRID_SKEW
    nx, ny, nz = (int(d) for d in grid_dims(verts, pitch))
    if nx * ny * nz > VOXEL_BUDGET:
        raise MemoryError(f"grid {nx}x{ny}x{nz} exceeds the voxel budget; coarsen")

    tri = verts[faces]
    lox = np.clip(np.ceil((tri[:, :, 0].min(axis=1) - lo[0]) / pitch - 0.5), 0, nx - 1)
    hix = np.clip(np.floor((tri[:, :, 0].max(axis=1) - lo[0]) / pitch + 0.5), 0, nx - 1)
    loy = np.clip(np.ceil((tri[:, :, 1].min(axis=1) - lo[1]) / pitch - 0.5), 0, ny - 1)
    hiy = np.clip(np.floor((tri[:, :, 1].max(axis=1) - lo[1]) / pitch + 0.5), 0, ny - 1)
    lox, hix, loy, hiy = (a.astype(np.int64) for a in (lox, hix, loy, hiy))
    wide = np.maximum(hix - lox + 1, 0)
    tall = np.maximum(hiy - loy + 1, 0)
    per_face = wide * tall
    total = int(per_face.sum())
    if total > 4 * VOXEL_BUDGET:
        raise MemoryError(f"{total} triangle-column pairs exceeds the budget; coarsen")

    face_id = np.repeat(np.arange(len(faces)), per_face)
    heads = np.concatenate([[0], np.cumsum(per_face)[:-1]])
    local = np.arange(total) - np.repeat(heads, per_face)
    ix = lox[face_id] + local % wide[face_id]
    iy = loy[face_id] + local // wide[face_id]

    a, b, c = tri[face_id, 0], tri[face_id, 1], tri[face_id, 2]
    ab, ac = b - a, c - a
    twice_area = ab[:, 0] * ac[:, 1] - ab[:, 1] * ac[:, 0]
    usable = np.abs(twice_area) > 1e-12
    px = (lo[0] + ix * pitch) - a[:, 0]
    py = (lo[1] + iy * pitch) - a[:, 1]
    with np.errstate(divide="ignore", invalid="ignore"):
        u = np.where(usable, (px * ac[:, 1] - py * ac[:, 0]) / twice_area, -1.0)
        v = np.where(usable, (ab[:, 0] * py - ab[:, 1] * px) / twice_area, -1.0)
    hit = (u >= 0) & (v >= 0) & (u + v <= 1)
    if not hit.any():
        return np.zeros((nx, ny, nz), dtype=bool), lo

    column = (ix[hit] * ny + iy[hit]).astype(np.int64)
    crossing = a[hit, 2] + u[hit] * ab[hit, 2] + v[hit] * ac[hit, 2]
    winding = np.sign(twice_area[hit]).astype(np.int64)

    order = np.lexsort((crossing, column))
    column, crossing, winding = column[order], crossing[order], winding[order]
    running = np.cumsum(winding)
    starts = np.flatnonzero(np.r_[True, column[1:] != column[:-1]])
    before = np.where(starts > 0, running[starts - 1], 0)
    depth = running - np.repeat(before, np.diff(np.r_[starts, len(column)]))

    follows = np.r_[column[1:] == column[:-1], False]
    span = (depth != 0) & follows
    if not span.any():
        return np.zeros((nx, ny, nz), dtype=bool), lo
    enter = crossing[span]
    leave = np.r_[crossing[1:], crossing[-1]][span]
    k0 = np.clip(np.ceil((enter - lo[2]) / pitch), 0, nz).astype(np.int64)
    k1 = np.clip(np.ceil((leave - lo[2]) / pitch), 0, nz).astype(np.int64)
    cols = column[span]

    # Difference array, then one cumulative sum along z. int32 rather than the
    # int64 `bincount` would hand back: at these grid sizes that pair of arrays
    # is the difference between a run that fits in memory and one that does not.
    stride = nz + 1
    edges = np.zeros(nx * ny * stride, dtype=np.int32)
    np.add.at(edges, cols * stride + k0, 1)
    np.add.at(edges, cols * stride + k1, -1)
    np.cumsum(edges.reshape(nx * ny, stride), axis=1, out=edges.reshape(nx * ny, stride))
    filled = edges.reshape(nx * ny, stride)[:, :nz] > 0
    del edges
    return np.ascontiguousarray(filled.reshape(nx, ny, nz)), lo


def _self_check():
    """A unit cube, then the same cube with each defect class introduced."""
    box = np.array([
        [[0, 0, 0], [1, 1, 0], [1, 0, 0]], [[0, 0, 0], [0, 1, 0], [1, 1, 0]],
        [[0, 0, 1], [1, 0, 1], [1, 1, 1]], [[0, 0, 1], [1, 1, 1], [0, 1, 1]],
        [[0, 0, 0], [1, 0, 0], [1, 0, 1]], [[0, 0, 0], [1, 0, 1], [0, 0, 1]],
        [[0, 1, 0], [0, 1, 1], [1, 1, 1]], [[0, 1, 0], [1, 1, 1], [1, 1, 0]],
        [[0, 0, 0], [0, 0, 1], [0, 1, 1]], [[0, 0, 0], [0, 1, 1], [0, 1, 0]],
        [[1, 0, 0], [1, 1, 0], [1, 1, 1]], [[1, 0, 0], [1, 1, 1], [1, 0, 1]],
    ], dtype=np.float64)
    verts, faces = weld(box)
    clean = summarize(verts, faces)
    assert clean["boundary"] == 0, clean
    assert clean["nonmanifold_edges"] == 0, clean
    assert clean["flipped"] == 0, clean
    assert clean["shells"] == 1, clean
    assert abs(clean["volume"] - 1.0) < 1e-9, clean

    holed = summarize(verts, faces[:-1])
    assert holed["boundary"] == 3, holed
    assert holed["boundary_loops"] == 1, holed

    assert clean["pinched_vertices"] == 0, clean

    # Two coplanar patches meeting at a T-junction, stitched by a zero-height
    # sliver. This is the case that makes the sliver count and the boundary
    # count one question: dropping the sliver opens the three edges it held.
    stitched = np.array([
        [[0, 0, 0], [1, 0, 0], [0, 1, 0]], [[1, 0, 0], [1, 1, 0], [0, 1, 0]],
        [[0, 0, 0], [0, -1, 0], [0.5, 0, 0]], [[0.5, 0, 0], [0, -1, 0], [1, -1, 0]],
        [[0.5, 0, 0], [1, -1, 0], [1, 0, 0]],
        [[0, 0, 0], [0.5, 0, 0], [1, 0, 0]],          # the sliver
    ], dtype=np.float64)
    sv, sf = weld(stitched)
    tee = summarize(sv, sf)
    assert tee["slivers"] == 1, tee
    assert tee["boundary"] - tee["boundary_with_slivers"] == 3, tee

    # A bowtie: two square pyramids joined at one apex vertex and nowhere else.
    def pyramid(cx, cy, sign):
        base = [(cx - 1, cy - 1), (cx + 1, cy - 1), (cx + 1, cy + 1), (cx - 1, cy + 1)]
        apex = (0.0, 0.0, 0.0)
        tris = [[apex, (*base[i], sign), (*base[(i + 1) % 4], sign)] for i in range(4)]
        tris.append([(*base[0], sign), (*base[2], sign), (*base[1], sign)])
        tris.append([(*base[0], sign), (*base[3], sign), (*base[2], sign)])
        return tris

    bow = np.array(pyramid(-1, -1, -1.0) + pyramid(1, 1, 1.0), dtype=np.float64)
    bv, bf = weld(bow)
    tie = summarize(bv, bf)
    assert tie["pinched_vertices"] == 1, tie

    # Voxelisation against a shape whose volume is known exactly, then against
    # the same shape hollowed -- the nested-shell case parity gets backwards.
    big = np.array([[[x * 20 for x in p] for p in t] for t in box], dtype=np.float64)
    bigv, bigf = weld(big)
    grid, _origin = voxelize(bigv, bigf, 0.5)
    assert abs(grid.sum() * 0.125 - 8000.0) / 8000.0 < 0.005, grid.sum() * 0.125

    inner = np.array([[[4 + x * 12 for x in p] for p in t] for t in box], dtype=np.float64)
    shell = np.concatenate([big, inner[:, ::-1]])          # inner shell, reversed
    sv, sf = weld(shell)
    grid, _origin = voxelize(sv, sf, 0.5)
    want = 20.0 ** 3 - 12.0 ** 3
    assert abs(grid.sum() * 0.125 - want) / want < 0.01, grid.sum() * 0.125
    print("meshlib self-check: ok")


if __name__ == "__main__":
    _self_check()
