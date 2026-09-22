"""Booleans that check their own arithmetic, one solid pair at a time.

Three measured behaviours of this kernel drive every line here.

* A compound used as the subject or the tool of a cut or an intersection is
  answered wrongly rather than slowly: a ball cut by a five-ball compound came
  back as 2.5 mm3 of a 1371 mm3 sphere, one valid solid, no warning.
* Cutting with a THIN CURVED SHELL fails outright -- ``Sphere(10) - (shell &
  ball)`` raises ``Null TopoDS_Shape`` on two valid operands.  A shell may be a
  result here, never a tool.
* Even solid-on-solid, some pairs come back wrong.  Two of Mercury's five
  albedo blobs removed 45.7 mm3 and 18.3 mm3 where the true lens is 21.5 and
  7.0, and the matching intersections under-reported by the same amount.

The third one is why every operation below is a SPLIT: the inside and the
outside are both computed, and ``inside + outside == subject`` is checked
before either is believed.  When it does not hold the tool is nudged by a
micron and the pair is tried again -- a displacement three orders of magnitude
under one layer, which moves a colour boundary by nothing and moves the
kernel off the configuration it could not resolve.  Fusing is sound, so unions
stay on the plain operator.
"""

from __future__ import annotations

from build123d import Compound, Pos, Rot, scale as _scale

MIN_SOLID_MM3 = 0.02
_NUDGES = ((0.0, 0.0, 0.0), (0.0013, 0.0007, 0.0011), (-0.0021, 0.0017, -0.0009),
           (0.0034, -0.0029, 0.0023))
_TURNS = ((0.0, 0.0, 90.0), (0.0, 0.0, 180.0), (0.0, 0.0, 270.0),
          (0.0, 90.0, 0.0), (0.0, -90.0, 0.0), (90.0, 0.0, 0.0), (0.0, 0.0, 37.0))
_SCALES = (0.9985, 1.0015, 0.997, 1.003, 0.994, 1.006)
_TOLERANCE = 1e-3


def parts(shape, floor: float = 1e-9) -> list:
    """The solids of a shape (or of a list of shapes), largest first."""
    if shape is None:
        return []
    if isinstance(shape, (list, tuple)):
        out = []
        for item in shape:
            out.extend(parts(item, floor))
        return out
    try:
        found = list(shape.solids())
    except (AttributeError, ValueError):
        return []
    return sorted(
        (solid for solid in found if solid.volume > floor),
        key=lambda solid: -solid.volume,
    )


def shape(pieces):
    """One shape from a list of disjoint solids, or None."""
    kept = [piece for piece in parts(pieces) if piece.volume > MIN_SOLID_MM3]
    if not kept:
        return None
    if len(kept) == 1:
        return kept[0]
    return Compound(children=kept)


def union(*shapes, disjoint: bool = False):
    """Fuse, checked against what a union can possibly weigh.

    A union is never heavier than the sum of its parts and never lighter than
    its heaviest part.  When the callers know the parts do not overlap, the
    two bounds close on one number and the check is exact.  A fuse that lands
    outside the bounds has gone wrong -- measured here at +391 mm3 and then
    -1825 mm3 while welding Earth's drylands onto its globe -- and the pieces
    are handed back side by side rather than shipped as a body that is quietly
    missing part of itself.
    """
    pieces = parts(list(shapes))
    if not pieces:
        return None
    total = sum(piece.volume for piece in pieces)
    floor = total if disjoint else max(piece.volume for piece in pieces)
    result = pieces[0]
    for other in pieces[1:]:
        result = result + other
    got = volume(result)
    if got > total * (1.0 + 1e-3) + 1e-6 or got < floor * (1.0 - 1e-3) - 1e-6:
        return shape(pieces)
    return result


def _overlaps(one, other, slack: float = 1e-6) -> bool:
    a, b = one.bounding_box(), other.bounding_box()
    return (
        a.min.X <= b.max.X + slack and b.min.X <= a.max.X + slack
        and a.min.Y <= b.max.Y + slack and b.min.Y <= a.max.Y + slack
        and a.min.Z <= b.max.Z + slack and b.min.Z <= a.max.Z + slack
    )


def _same_shape(one, other) -> bool:
    """Is `other` the same solid as `one`, only turned?"""
    if abs(one.volume - other.volume) > max(1e-6 * one.volume, 1e-9):
        return False
    a, b = one.bounding_box(), other.bounding_box()
    span = max(a.size.X, a.size.Y, a.size.Z, 1.0)
    return all(
        abs(getattr(a.min, axis) - getattr(b.min, axis)) <= 1e-6 * span
        and abs(getattr(a.max, axis) - getattr(b.max, axis)) <= 1e-6 * span
        for axis in ("X", "Y", "Z")
    )


def _alternates(tool):
    """The same tool, with its revolved seam somewhere else.

    A revolved primitive carries a seam at its own local +X, and a boolean
    whose seam lands inside the material it is cutting is answered wrongly.
    Turning a ball or an axisymmetric cylinder about its own centre moves that
    seam without moving one micron of surface -- and the check above is what
    proves the turn was shape-preserving before it is used.
    """
    yield tool
    centre = tool.bounding_box().center()
    back = Pos(-centre.X, -centre.Y, -centre.Z)
    forward = Pos(centre.X, centre.Y, centre.Z)
    for turn in _TURNS:
        try:
            turned = forward * Rot(*turn) * back * tool
        except (ValueError, RuntimeError):
            continue
        if _same_shape(tool, turned):
            yield turned
    # Last resort: the same tool a thousandth larger or smaller.  A marking
    # boundary that moves by a micron is not a design change; a boolean the
    # kernel cannot resolve at one exact size usually resolves at another.
    for factor in _SCALES:
        try:
            yield forward * _scale(back * tool, by=factor)
        except (ValueError, RuntimeError):
            continue


def _split_pair(piece, tool):
    """(inside, outside) for one solid against one solid, or None if unsound."""
    whole = piece.volume
    for alternate in _alternates(tool):
        for nudge in _NUDGES:
            moved = alternate if nudge == (0.0, 0.0, 0.0) else Pos(*nudge) * alternate
            try:
                inside = parts(piece.intersect(moved))
                outside = parts(piece.cut(moved))
            except (ValueError, RuntimeError):
                continue
            total = sum(item.volume for item in inside) + sum(
                item.volume for item in outside
            )
            if abs(total - whole) <= max(_TOLERANCE * whole, 1e-6):
                return inside, outside
    return None


#: Pairs this module could not resolve and had to leave uncut.  Nothing is
#: lost when that happens -- the piece stays on the `outside` side and the
#: partition still adds up -- but a marking ends up a fragment smaller than it
#: was drawn, so the count is reported rather than swallowed.
REFUSED: list[tuple[float, float]] = []


def split(subject, tool, strict: bool = False):
    """(inside, outside) of `subject` against `tool`, as two lists of solids.

    The two halves always add back up to `subject`, which is the whole point:
    callers partition a globe by splitting it region by region, so a boolean
    the kernel will not answer costs a marking a fragment and never costs the
    part a hole.  `tool`'s solids must be disjoint from one another, which
    every caller here guarantees by fusing before it cuts.
    """
    tools = parts(tool)
    inside: list = []
    outside: list = []
    for piece in parts(subject):
        current = [piece]
        for other in tools:
            nxt = []
            for item in current:
                if not _overlaps(item, other):
                    nxt.append(item)
                    continue
                answer = _split_pair(item, other)
                if answer is None:
                    if strict:
                        raise RuntimeError(
                            "boolean split refused: %.3f mm3 against %.3f mm3"
                            % (item.volume, other.volume)
                        )
                    REFUSED.append((item.volume, other.volume))
                    nxt.append(item)
                    continue
                got_in, got_out = answer
                inside.extend(got_in)
                nxt.extend(got_out)
            current = nxt
            if not current:
                break
        outside.extend(current)
    return inside, outside


def try_split(piece, tool):
    """(inside, outside) for one solid against one tool, or None if unsound."""
    inside: list = []
    outside: list = [piece]
    for other in parts(tool):
        nxt = []
        for item in outside:
            if not _overlaps(item, other):
                nxt.append(item)
                continue
            answer = _split_pair(item, other)
            if answer is None:
                return None
            got_in, got_out = answer
            inside.extend(got_in)
            nxt.extend(got_out)
        outside = nxt
    return inside, outside


def meet(subject, tool):
    return split(subject, tool)[0]


def cut(subject, tool):
    return split(subject, tool)[1]


def volume(anything) -> float:
    return sum(piece.volume for piece in parts(anything))


def invalid_topology(anything) -> bool | None:
    """Does ``BRepCheck_Analyzer`` reject this solid?

    A different question from `self_intersecting`, and one this module learned
    to ask the hard way: Earth's Eurasia lens came back with no self-crossing
    and no lost volume, and `inspect validate` still reported it
    ``invalidTopology``.  A body whose faces do not pass through one another
    can still carry a wire or a vertex the analyzer refuses, and the final
    gate asks the analyzer.  Run with the same ``True`` flag the gate uses, so
    the answer here and the answer there are the same answer.

    Returns None when the checker could not run at all, which must never be
    read as a pass.
    """
    try:
        from OCP.BRepCheck import BRepCheck_Analyzer
    except ImportError:                                   # pragma: no cover
        return None
    for piece in parts(anything):
        try:
            if not BRepCheck_Analyzer(piece.wrapped, True).IsValid():
                return True
        except Exception:                                 # pragma: no cover
            return None
    return False


def self_intersecting(anything) -> bool | None:
    """Does this solid's own boundary cross itself?

    ``BRepCheck_Analyzer`` says nothing about this: a shape whose faces are
    each individually sound, closed and correctly oriented can still have two
    of those faces passing through one another, and the topology checker
    returns True for it.  Only the Boolean self-check sees it, and the final
    ``inspect validate`` gate runs exactly this test -- so a repair loop that
    does not run it is guessing.

    Keyed on the ``BOPAlgo_SelfIntersect`` status and not on ``IsValid()``,
    because ``IsValid()`` is also False for unrelated Boolean faults.  Returns
    None when the checker could not run at all, which must never be read as a
    pass.
    """
    try:
        from OCP.BOPAlgo import BOPAlgo_CheckStatus
        from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
    except ImportError:                                   # pragma: no cover
        return None
    for piece in parts(anything):
        try:
            checker = BRepAlgoAPI_Check(piece.wrapped, True, True)
            if checker.IsValid():
                continue
            if any(
                result.GetCheckStatus() == BOPAlgo_CheckStatus.BOPAlgo_SelfIntersect
                for result in checker.Result()
            ):
                return True
        except Exception:                                 # pragma: no cover
            return None
    return False
