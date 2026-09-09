"""Viewer-parity part groups and colour keys for the Factory listing.

The Factory viewer colours a listing's assembled mesh by *groups* it computes
itself from ``assembled.stl``: triangles joined only across manifold edges
(exactly two incident triangles) form a shell, a shell with no closed edge is
a loose contact facet that takes an owner's colour, and the remaining shells
are numbered densely in triangle order.  Group ``i`` then keys its colour by
the ``i``-th *slide* file, the part meshes under ``<stem>_parts/`` ordered by
the sidecar's ``parts[].index``; a group past the slide list keys by the slot
``<lead>#i``.  The viewer never reads part geometry, so a part whose mesh
splits into several shells, or any sliver shed at a contact face, silently
shifts every colour after it.

This module reproduces that numbering exactly, owns each group with the posed
occurrence geometry the sealed STEP carries, and emits the ``assembly_parts``
entries the shop needs: one per viewer group, keyed the way the viewer
resolves it, coloured as the owner's sealed colour.  Pure Python; bounded.
"""

from __future__ import annotations

import math
import re
import struct
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional, Sequence, Tuple

from workshop.errors import ContractError


MAX_FE_TRIANGLES = 2_000_000
MAX_FE_STL_BYTES = 256 * 1024 * 1024
REAL_PART_MIN_TRIS = 50
BBOX_MARGIN = 0.5
OWNER_SAMPLE_POINTS = 64
_ASCII_VERTEX = re.compile(rb"vertex\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)")
_SAFE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")

Point = Tuple[float, float, float]


class FePartsError(Exception):
    """A bounded reason why viewer groups could not be keyed."""


def read_stl_triangles(content: bytes) -> list[Tuple[Point, Point, Point]]:
    """Return the triangles of binary or ASCII STL bytes, in file order."""

    if not isinstance(content, bytes) or not content:
        raise FePartsError("mesh bytes are empty")
    if len(content) > MAX_FE_STL_BYTES:
        raise FePartsError("mesh exceeds the size bound")
    if len(content) >= 84:
        count = struct.unpack("<I", content[80:84])[0]
        if len(content) == 84 + count * 50:
            if count > MAX_FE_TRIANGLES:
                raise FePartsError("mesh exceeds the triangle bound")
            return [
                (record[0:3], record[3:6], record[6:9])
                for record in struct.iter_unpack("<12x9fH", content[84 : 84 + count * 50])
            ]
    if not content[:512].lstrip().startswith(b"solid"):
        raise FePartsError("mesh is neither binary nor ASCII STL")
    vertices = [tuple(float(item) for item in match) for match in _ASCII_VERTEX.findall(content)]
    triangles = len(vertices) // 3
    if triangles > MAX_FE_TRIANGLES:
        raise FePartsError("mesh exceeds the triangle bound")
    return [
        (vertices[index], vertices[index + 1], vertices[index + 2])
        for index in range(0, triangles * 3, 3)
    ]


Signature = Tuple[float, float, float, float, float]


def _jacobi_eigenvalues(matrix: Sequence[Sequence[float]]) -> Tuple[float, float, float]:
    """Eigenvalues of a symmetric 3x3 matrix, descending (Jacobi rotations)."""

    a = [list(map(float, row)) for row in matrix]
    for _ in range(60):
        p, q, largest = 0, 1, abs(a[0][1])
        for i, j in ((0, 2), (1, 2)):
            if abs(a[i][j]) > largest:
                p, q, largest = i, j, abs(a[i][j])
        if largest < 1e-14:
            break
        theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
        t = (1.0 if theta >= 0 else -1.0) / (abs(theta) + math.sqrt(theta * theta + 1.0))
        c = 1.0 / math.sqrt(t * t + 1.0)
        sn = t * c
        for k in range(3):
            akp, akq = a[k][p], a[k][q]
            a[k][p] = c * akp - sn * akq
            a[k][q] = sn * akp + c * akq
        for k in range(3):
            apk, aqk = a[p][k], a[q][k]
            a[p][k] = c * apk - sn * aqk
            a[q][k] = sn * apk + c * aqk
    values = sorted((a[0][0], a[1][1], a[2][2]), reverse=True)
    return (values[0], values[1], values[2])


def mesh_signature(triangles: Sequence[Tuple[Point, Point, Point]]) -> Signature:
    """A rotation- and translation-invariant shape signature.

    Absolute enclosed volume, surface area, and the three principal extents
    of the area-weighted triangle centroids.  Two exports of the same solid,
    in any pose, agree to within tessellation noise; different parts do not.
    """

    volume = 0.0
    area_total = 0.0
    weighted = [0.0, 0.0, 0.0]
    centroids = []
    for a, b, c in triangles:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        area = 0.5 * math.sqrt(nx * nx + ny * ny + nz * nz)
        volume += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
        centroid = ((a[0] + b[0] + c[0]) / 3.0, (a[1] + b[1] + c[1]) / 3.0, (a[2] + b[2] + c[2]) / 3.0)
        centroids.append((centroid, area))
        area_total += area
        for axis in range(3):
            weighted[axis] += centroid[axis] * area
    if area_total <= 0:
        return (abs(volume), 0.0, 0.0, 0.0, 0.0)
    mean = [value / area_total for value in weighted]
    cov = [[0.0] * 3 for _ in range(3)]
    for centroid, area in centroids:
        d = [centroid[axis] - mean[axis] for axis in range(3)]
        for i in range(3):
            for j in range(3):
                cov[i][j] += area * d[i] * d[j]
    cov = [[value / area_total for value in row] for row in cov]
    e1, e2, e3 = _jacobi_eigenvalues(cov)
    return (abs(volume), area_total, math.sqrt(max(e1, 0.0)), math.sqrt(max(e2, 0.0)), math.sqrt(max(e3, 0.0)))


def signature_distance(left: Signature, right: Signature) -> float:
    """Sum of absolute log ratios; 0 for identical shapes."""

    total = 0.0
    for a, b in zip(left, right):
        total += abs(math.log((a + 1e-6) / (b + 1e-6)))
    return total


@dataclass(frozen=True)
class FeGroup:
    """One viewer part group: its number, size, centroid, extent, and shape."""

    order: int
    triangles: int
    centroid: Point
    bbox_min: Point
    bbox_max: Point
    sample: Tuple[Point, ...]
    signature: Signature = (0.0, 0.0, 0.0, 0.0, 0.0)

    @property
    def is_real(self) -> bool:
        return self.triangles >= REAL_PART_MIN_TRIS


@dataclass(frozen=True)
class FeGroups:
    groups: Tuple[FeGroup, ...]
    shells: int
    loose_shells: int
    triangles: int

    @property
    def count(self) -> int:
        return len(self.groups)


def _weld_key(point: Point) -> Tuple[int, int, int]:
    # The viewer welds on the same 1e-4 grid three.js's mergeVertices uses.
    return (round(point[0] * 1e4), round(point[1] * 1e4), round(point[2] * 1e4))


def fe_part_groups(triangles: Sequence[Tuple[Point, Point, Point]]) -> FeGroups:
    """Number the viewer's part groups of one assembled mesh.

    Shells join only across manifold edges; a shell with no closed edge is a
    loose facet owned by the shell it faces (reversed-winding vote, falling
    back to the nearest real shell in triangle order); real shells are
    numbered densely in shell order, loose shells take their owner's number.
    """

    count = len(triangles)
    if count == 0:
        raise FePartsError("mesh has no triangles")
    if count > MAX_FE_TRIANGLES:
        raise FePartsError("mesh exceeds the triangle bound")
    vertex_ids: dict[Tuple[int, int, int], int] = {}
    vid = [0] * (count * 3)
    for index, triangle in enumerate(triangles):
        for corner in range(3):
            key = _weld_key(triangle[corner])
            identifier = vertex_ids.get(key)
            if identifier is None:
                identifier = len(vertex_ids)
                vertex_ids[key] = identifier
            vid[index * 3 + corner] = identifier
    # Undirected edge -> (incident count, first triangle).
    edge_count: dict[Tuple[int, int], int] = {}
    edge_first: dict[Tuple[int, int], int] = {}
    for index in range(count):
        base = index * 3
        for corner in range(3):
            a = vid[base + corner]
            b = vid[base + (corner + 1) % 3]
            key = (a, b) if a < b else (b, a)
            edge_count[key] = min(255, edge_count.get(key, 0) + 1)
            edge_first.setdefault(key, index)
    parent = list(range(count))

    def find(item: int) -> int:
        root = item
        while parent[root] != root:
            root = parent[root]
        while parent[item] != root:
            parent[item], item = root, parent[item]
        return root

    for index in range(count):
        base = index * 3
        for corner in range(3):
            a = vid[base + corner]
            b = vid[base + (corner + 1) % 3]
            key = (a, b) if a < b else (b, a)
            if edge_count[key] != 2:
                continue
            first = edge_first[key]
            if first != index:
                root_a, root_b = find(index), find(first)
                if root_a != root_b:
                    parent[root_a] = root_b
    shell_of_root: dict[int, int] = {}
    label = [0] * count
    for index in range(count):
        root = find(index)
        shell = shell_of_root.get(root)
        if shell is None:
            shell = len(shell_of_root)
            shell_of_root[root] = shell
        label[index] = shell
    shells = max(1, len(shell_of_root))
    closed = [0] * shells
    for index in range(count):
        base = index * 3
        for corner in range(3):
            a = vid[base + corner]
            b = vid[base + (corner + 1) % 3]
            key = (a, b) if a < b else (b, a)
            if edge_count[key] == 2:
                closed[label[index]] += 1
    loose = [value // 2 == 0 for value in closed]
    loose_count = sum(loose)
    if loose_count == shells:
        loose = [False] * shells
        loose_count = 0
    owner = list(range(shells))
    if 0 < loose_count < shells:
        wanted: dict[Tuple[int, int], int] = {}
        for index in range(count):
            shell = label[index]
            if not loose[shell]:
                continue
            base = index * 3
            for corner in range(3):
                a = vid[base + corner]
                b = vid[base + (corner + 1) % 3]
                wanted[(b, a)] = shell
        votes: dict[Tuple[int, int], int] = {}
        for index in range(count):
            shell = label[index]
            if loose[shell]:
                continue
            base = index * 3
            for corner in range(3):
                a = vid[base + corner]
                b = vid[base + (corner + 1) % 3]
                facet = wanted.get((a, b))
                if facet is None:
                    continue
                votes[(facet, shell)] = votes.get((facet, shell), 0) + 1
        best = [-1] * shells
        best_votes = [0] * shells
        for (facet, shell), tally in sorted(votes.items()):
            if tally <= best_votes[facet]:
                continue
            best_votes[facet] = tally
            best[facet] = shell
        far = 1 << 62
        prev_shell = [-1] * shells
        prev_dist = [far] * shells
        next_shell = [-1] * shells
        next_dist = [far] * shells
        last_shell, last_at = -1, 0
        for index in range(count):
            shell = label[index]
            if not loose[shell]:
                last_shell, last_at = shell, index
            elif prev_shell[shell] == -1 and last_shell != -1:
                prev_shell[shell], prev_dist[shell] = last_shell, index - last_at
        last_shell, last_at = -1, 0
        for index in range(count - 1, -1, -1):
            shell = label[index]
            if not loose[shell]:
                last_shell, last_at = shell, index
            elif next_shell[shell] == -1 and last_shell != -1:
                next_shell[shell], next_dist[shell] = last_shell, last_at - index
        for shell in range(shells):
            if not loose[shell] or best[shell] != -1:
                continue
            before, after = prev_shell[shell], next_shell[shell]
            if before == -1:
                best[shell] = after
            elif after == -1:
                best[shell] = before
            else:
                best[shell] = before if prev_dist[shell] <= next_dist[shell] else after
        for shell in range(shells):
            if loose[shell] and best[shell] != -1:
                owner[shell] = best[shell]
    part_of_shell = [-1] * shells
    part_count = 0
    for shell in range(shells):
        if not loose[shell]:
            part_of_shell[shell] = part_count
            part_count += 1
    for shell in range(shells):
        if loose[shell]:
            part_of_shell[shell] = part_of_shell[owner[shell]]
    grouped: list[list[Tuple[Point, Point, Point]]] = [[] for _ in range(part_count)]
    sums = [[0.0, 0.0, 0.0] for _ in range(part_count)]
    sizes = [0] * part_count
    lows = [[math.inf] * 3 for _ in range(part_count)]
    highs = [[-math.inf] * 3 for _ in range(part_count)]
    samples: list[list[Point]] = [[] for _ in range(part_count)]
    for index, triangle in enumerate(triangles):
        part = part_of_shell[label[index]]
        grouped[part].append(triangle)
        sizes[part] += 1
        total = sums[part]
        low = lows[part]
        high = highs[part]
        for axis in range(3):
            total[axis] += (triangle[0][axis] + triangle[1][axis] + triangle[2][axis]) / 3.0
        for vertex in triangle:
            for axis in range(3):
                if vertex[axis] < low[axis]:
                    low[axis] = vertex[axis]
                if vertex[axis] > high[axis]:
                    high[axis] = vertex[axis]
        if len(samples[part]) < OWNER_SAMPLE_POINTS and (index % 7 == 0 or sizes[part] <= OWNER_SAMPLE_POINTS):
            samples[part].append(triangle[0])
    groups = tuple(
        FeGroup(
            order=part,
            triangles=sizes[part],
            centroid=tuple(value / max(1, sizes[part]) for value in sums[part]),
            bbox_min=tuple(lows[part]),
            bbox_max=tuple(highs[part]),
            sample=tuple(samples[part]),
            signature=mesh_signature(grouped[part]),
        )
        for part in range(part_count)
    )
    return FeGroups(groups=groups, shells=shells, loose_shells=loose_count, triangles=count)


@dataclass(frozen=True)
class PartShape:
    """The sealed production mesh of one occurrence: whole and per shell."""

    name: str
    whole: Signature
    shells: Tuple[Signature, ...]

    def distance(self, signature: Signature) -> float:
        candidates = (self.whole, *self.shells)
        return min(signature_distance(signature, candidate) for candidate in candidates)


def part_shapes(meshes: Mapping[str, bytes]) -> dict[str, PartShape]:
    """Signatures of every sealed production mesh, whole and per shell."""

    result: dict[str, PartShape] = {}
    for name, content in meshes.items():
        triangles = read_stl_triangles(content)
        whole = mesh_signature(triangles)
        groups = fe_part_groups(triangles)
        shells = tuple(group.signature for group in groups.groups) if groups.count > 1 else ()
        result[name] = PartShape(name=name, whole=whole, shells=shells)
    return result


@dataclass(frozen=True)
class PosedOccurrence:
    """One sealed occurrence in its assembled pose: name, extent, and points."""

    name: str
    bbox_min: Point
    bbox_max: Point
    points: Tuple[Point, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or _SAFE_NAME.fullmatch(self.name) is None:
            raise ContractError("posed occurrence name is unsafe")
        if len(self.bbox_min) != 3 or len(self.bbox_max) != 3 or not self.points:
            raise ContractError("posed occurrence geometry is empty")
        if any(
            not math.isfinite(value)
            for point in (self.bbox_min, self.bbox_max, *self.points)
            for value in point
        ):
            raise ContractError("posed occurrence geometry is not finite")

    def contains(self, point: Point, margin: float = BBOX_MARGIN) -> bool:
        return all(
            self.bbox_min[axis] - margin <= point[axis] <= self.bbox_max[axis] + margin
            for axis in range(3)
        )

    def extent_overlap(self, low: Point, high: Point) -> float:
        """Intersection-over-union of axis-aligned extents, 0 when disjoint."""

        inter = 1.0
        union = 1.0
        for axis in range(3):
            a0, a1 = self.bbox_min[axis], self.bbox_max[axis]
            b0, b1 = low[axis], high[axis]
            overlap = max(0.0, min(a1, b1) - max(a0, b0))
            span_a = max(a1 - a0, 1e-6)
            span_b = max(b1 - b0, 1e-6)
            inter *= overlap
            union *= max(span_a, span_b, (max(a1, b1) - min(a0, b0)))
        return inter / union if union > 0 else 0.0

    def fits(self, group: "FeGroup", margin: float = BBOX_MARGIN) -> bool:
        """Whether the group's extent lies inside this occurrence's extent."""

        return all(
            self.bbox_min[axis] - margin <= group.bbox_min[axis]
            and group.bbox_max[axis] <= self.bbox_max[axis] + margin
            for axis in range(3)
        )

    def mean_distance(self, sample: Sequence[Point]) -> float:
        total = 0.0
        for point in sample:
            best = math.inf
            for candidate in self.points:
                distance = (
                    (candidate[0] - point[0]) ** 2
                    + (candidate[1] - point[1]) ** 2
                    + (candidate[2] - point[2]) ** 2
                )
                if distance < best:
                    best = distance
            total += math.sqrt(best)
        return total / max(1, len(sample))


def _score(group: FeGroup, occurrence: PosedOccurrence) -> float:
    """Higher is a better owner: extent overlap first, then proximity."""

    overlap = occurrence.extent_overlap(group.bbox_min, group.bbox_max)
    inside = 1.0 if occurrence.contains(group.centroid) else 0.0
    distance = occurrence.mean_distance(group.sample)
    return overlap * 4.0 + inside + 1.0 / (1.0 + distance)


SIGNATURE_MATCH = 0.35


def _centroid_distance(group: FeGroup, occurrence: PosedOccurrence) -> float:
    centre = tuple(
        (occurrence.bbox_min[axis] + occurrence.bbox_max[axis]) / 2.0 for axis in range(3)
    )
    return math.sqrt(sum((group.centroid[axis] - centre[axis]) ** 2 for axis in range(3)))


def own_groups(
    groups: FeGroups,
    occurrences: Sequence[PosedOccurrence],
    shapes: Optional[Mapping[str, PartShape]] = None,
) -> Tuple[Optional[str], ...]:
    """Assign every viewer group to the sealed occurrence it belongs to.

    Three passes.  Shape first: a group whose signature matches a production
    mesh (whole or one of its shells) belongs to that part; identical
    instances are told apart by posed proximity, and a whole-part match is
    claimed once per instance.  Coverage next: an occurrence that still owns
    nothing claims the best unowned group inside its posed extent, so a part
    whose only geometry is a sliver keeps it.  Position last: every remaining
    group, split pieces and slivers, goes to the best-scoring occurrence whose
    extent contains it, or the best overall when none does.
    """

    if not occurrences:
        return tuple(None for _ in groups.groups)
    names = [item.name for item in occurrences]
    if len(set(names)) != len(names):
        raise FePartsError("posed occurrence names must be unique")
    count = len(occurrences)
    scores = [[_score(group, occurrence) for occurrence in occurrences] for group in groups.groups]
    fits = [[occurrence.fits(group) for occurrence in occurrences] for group in groups.groups]
    owners: list[Optional[str]] = [None] * groups.count
    owned_any: set[int] = set()
    whole_claimed: set[int] = set()
    if shapes:
        matches = []
        for g, group in enumerate(groups.groups):
            if not group.is_real:
                continue
            for o, name in enumerate(names):
                shape = shapes.get(name)
                if shape is None:
                    continue
                whole = signature_distance(group.signature, shape.whole)
                partial = min(
                    (signature_distance(group.signature, item) for item in shape.shells),
                    default=math.inf,
                )
                distance = min(whole, partial)
                if distance > SIGNATURE_MATCH:
                    continue
                matches.append(
                    (
                        distance + 0.01 * _centroid_distance(group, occurrences[o]),
                        g,
                        o,
                        whole <= partial,
                    )
                )
        for _, g, o, is_whole in sorted(matches):
            if owners[g] is not None or (is_whole and o in whole_claimed):
                continue
            owners[g] = names[o]
            owned_any.add(o)
            if is_whole:
                whole_claimed.add(o)
    pairs = sorted(
        (
            (scores[g][o], groups.groups[g].triangles, g, o)
            for g in range(groups.count)
            for o in range(count)
            if fits[g][o] and owners[g] is None
        ),
        reverse=True,
    )
    for _, _, g, o in pairs:
        if owners[g] is not None or o in owned_any:
            continue
        owners[g] = names[o]
        owned_any.add(o)
    for g in range(groups.count):
        if owners[g] is not None:
            continue
        fitting = [o for o in range(count) if fits[g][o]]
        pool = fitting or list(range(count))
        owners[g] = names[max(pool, key=lambda o: scores[g][o])]
    return tuple(owners)


@dataclass(frozen=True)
class PartKey:
    """One ``assembly_parts`` entry the viewer resolves for group ``order``."""

    order: int
    part: str
    mesh_name: str
    owner: str
    triangles: int
    color: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        entry = {
            "order": self.order,
            "part": self.part,
            "mesh_name": self.mesh_name,
            "owner": self.owner,
            "triangles": self.triangles,
        }
        if self.color is not None:
            entry["color"] = self.color
        return entry


@dataclass(frozen=True)
class PartKeying:
    """Every viewer group keyed and owned; the shop's colour table in full."""

    lead: str
    slides: Tuple[str, ...]
    groups: FeGroups
    keys: Tuple[PartKey, ...]
    unowned_occurrences: Tuple[str, ...] = field(default=())

    @property
    def complete(self) -> bool:
        return not self.unowned_occurrences and all(key.owner for key in self.keys)

    def coloured(self) -> Tuple[PartKey, ...]:
        return tuple(key for key in self.keys if key.color is not None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "lead": self.lead,
            "slides": list(self.slides),
            "shells": self.groups.shells,
            "loose_shells": self.groups.loose_shells,
            "group_count": self.groups.count,
            "keys": [key.to_dict() for key in self.keys],
            "unowned_occurrences": list(self.unowned_occurrences),
        }


def slide_key(lead: str, slides: Sequence[str], order: int, group_count: int = 1) -> str:
    """The filename the viewer keys group ``order`` by.

    A single-mesh design with exactly one group keys by the lead file itself;
    every other group past the slide list keys by the ``<lead>#i`` slot.
    """

    if order < len(slides):
        return slides[order]
    if not slides and group_count == 1 and order == 0:
        return lead
    return "%s#%d" % (lead, order)


def key_parts(
    assembled_stl: bytes,
    occurrences: Sequence[PosedOccurrence],
    *,
    lead: str = "assembled.stl",
    slide_order: Sequence[str],
    colours: Optional[Mapping[str, str]] = None,
    part_meshes: Optional[Mapping[str, bytes]] = None,
) -> PartKeying:
    """Key every viewer group of ``assembled_stl`` for the shop.

    ``slide_order`` lists occurrence names in the sidecar's ``parts[]`` order;
    slide ``i`` is ``<name>.stl``.  ``colours`` maps occurrence names to sealed
    ``#rrggbb`` values.  ``part_meshes`` maps occurrence names to their sealed
    production STL bytes, the shape identity that anchors ownership.
    """

    groups = fe_part_groups(read_stl_triangles(assembled_stl))
    slides = tuple("%s.stl" % name for name in slide_order)
    shapes = part_shapes(part_meshes) if part_meshes else None
    owners = own_groups(groups, occurrences, shapes)
    palette = dict(colours or {})
    keys = []
    for group, owner in zip(groups.groups, owners):
        owner_name = owner or ""
        keys.append(
            PartKey(
                order=group.order,
                part=slide_key(lead, slides, group.order, groups.count),
                mesh_name=owner_name if group.is_real else owner_name + "_sliver",
                owner=owner_name,
                triangles=group.triangles,
                color=palette.get(owner_name) if owner_name else None,
            )
        )
    owned = {key.owner for key in keys if key.owner}
    unowned = tuple(name for name in slide_order if name not in owned)
    return PartKeying(
        lead=lead,
        slides=slides,
        groups=groups,
        keys=tuple(keys),
        unowned_occurrences=unowned,
    )


__all__ = [
    "BBOX_MARGIN",
    "FeGroup",
    "FeGroups",
    "FePartsError",
    "MAX_FE_TRIANGLES",
    "PartKey",
    "PartKeying",
    "PartShape",
    "PosedOccurrence",
    "REAL_PART_MIN_TRIS",
    "SIGNATURE_MATCH",
    "fe_part_groups",
    "key_parts",
    "mesh_signature",
    "own_groups",
    "part_shapes",
    "read_stl_triangles",
    "signature_distance",
    "slide_key",
]
