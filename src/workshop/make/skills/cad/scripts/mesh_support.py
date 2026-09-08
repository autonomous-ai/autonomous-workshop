"""Deterministic support queries on horizontal sections of a closed STL mesh."""
import numpy as np


def _cross(a, b):
    return a[..., 0] * b[..., 1] - a[..., 1] * b[..., 0]


def _line_support(point, direction, ends, normals, reach, tolerance):
    a, b = ends[:, 0], ends[:, 1]
    edge = b - a
    den = _cross(direction, edge)
    usable = np.abs(den) > 1e-12
    if not usable.any():
        return False, np.inf
    a, edge, den, normals = a[usable], edge[usable], den[usable], normals[usable]
    delta = a - point
    t = _cross(delta, edge) / den
    u = _cross(delta, direction) / den
    hit = (u >= -1e-9) & (u <= 1 + 1e-9)
    positions = t[hit]
    signs = np.sign(normals[hit] @ direction)
    if not len(positions):
        return False, np.inf
    order = np.argsort(positions)
    positions, signs = positions[order], signs[order]
    heads = np.flatnonzero(np.r_[True, np.diff(positions) > tolerance])
    low, high = np.minimum.reduceat(signs, heads), np.maximum.reduceat(signs, heads)
    keep = (low == high) & (low != 0)
    positions, signs = positions[heads][keep], low[keep]
    if not len(positions):
        return False, np.inf
    after = np.cumsum(-signs)
    before = np.r_[0, after[:-1]]
    left = np.flatnonzero(positions < -tolerance)
    if np.any(np.abs(positions) <= tolerance) or (len(left) and after[left[-1]] != 0):
        return True, 0.
    entries = positions[(before == 0) & (after != 0)]
    exits = positions[(before != 0) & (after == 0)]
    lo = np.max(exits[exits < -tolerance], initial=-np.inf)
    hi = np.min(entries[entries > tolerance], initial=np.inf)
    span = hi - lo
    return bool(np.isfinite(span) and span <= reach + tolerance), float(span)


def support_at_layer(verts, faces, points, layer, allowance, bridge, tolerance=1e-6):
    """Classify points against the preceding layer's true material boundary.

    Besides X/Y, test the ray toward the nearest boundary point. This adds
    a geometry-derived direction for rotated slots without an angular grid.
    It is a bounded direction strategy, not a complete optimal bridge search.
    """
    tri = verts[faces]
    a, b = tri, np.roll(tri, -1, axis=1)
    dz = b[:, :, 2] - a[:, :, 2]
    normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])[:, :2]
    lower, upper = np.minimum(a[:, :, 2], b[:, :, 2]), np.maximum(a[:, :, 2], b[:, :, 2])
    distances = np.full(len(points), np.inf)
    near = np.zeros(len(points), dtype=bool)
    bridged = np.zeros(len(points), dtype=bool)
    spans = np.full(len(points), np.inf)
    batch = max(1, min(128, 500_000 // max(1, len(tri))))
    for start in range(0, len(points), batch):
        sample = points[start:start + batch]
        z = sample[:, None, None, 2] - layer
        # Slice just below a boundary: material ending at that plane can
        # support the next layer; material starting there is not below it.
        hit = (z > lower) & (z <= upper) & (np.abs(dz) > 1e-12)
        t = np.divide(z - a[:, :, 2], dz, out=np.zeros_like(hit, dtype=float), where=np.abs(dz) > 1e-12)
        xy = a[None, :, :, :2] + t[:, :, :, None] * (b - a)[None, :, :, :2]
        for row, point in enumerate(sample):
            live = np.flatnonzero(hit[row].sum(axis=1) == 2)
            if not len(live):
                continue
            ends = xy[row, live][hit[row, live]].reshape(-1, 2, 2)
            p0, p1 = ends[:, 0], ends[:, 1]
            delta = p1 - p0
            length2 = np.einsum('ij,ij->i', delta, delta)
            fraction = np.divide(np.einsum('ij,ij->i', point[:2] - p0, delta), length2,
                                 out=np.zeros(len(delta)), where=length2 > 1e-20)
            closest = p0 + np.clip(fraction, 0, 1)[:, None] * delta
            vectors = closest - point[:2]
            norms = np.linalg.norm(vectors, axis=1)
            nearest = int(np.argmin(norms))
            index = start + row
            distances[index] = norms[nearest]
            if norms[nearest] <= allowance + tolerance:
                near[index] = True
                spans[index] = 0
                continue
            directions = [np.array([1., 0.]), np.array([0., 1.]), vectors[nearest] / norms[nearest]]
            for direction in directions:
                ok, span = _line_support(point[:2], direction, ends, normals[live], bridge, tolerance)
                if ok:
                    spans[index] = min(spans[index], span)
                    if span == 0:
                        near[index] = True
                        bridged[index] = False
                        break
                    bridged[index] = True
    return near, bridged, spans, distances
