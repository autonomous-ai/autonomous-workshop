"""Kinematic placement — close a linkage loop so shared joints coincide.

Static placement (``cadlib`` elsewhere, ``references/assembly.md``) positions a
part by a chosen translation/rotation. A *mechanism* is different: two or more
parts share a moving joint, and the only correct pose is the one where that
joint is a **single point both parts reach**. Eyeballing an angle for each part
independently (the classic "splay the leg 30°, tilt the rocker 45°") leaves the
shared pin in two different places → the parts never touch → a
``disconnected_bodies`` warning and a tangle in the preview.

The discipline (see ``references/kinematic-placement.md``):

1. build each link in its own local frame with its joint points at known coords;
2. anchor the *fixed* pins from params (crank axis, ground pivots);
3. **solve** the moving joint with :func:`solve_fourbar` (or
   :func:`circle_intersections`) — never guess the angle;
4. **place** each link by its two joints with :func:`place_two_point`;
5. verify ``len(union.solids().vals()) == 1`` — one connected solid.

Working plane: :func:`solve_fourbar` is 2-D. Pick the plane the mechanism moves
in (a fore-aft "sagittal" X–Z plane for a walker), solve in those two coords,
then lift the solved point back into 3-D for :func:`place_two_point`, which is
fully 3-D and handles the out-of-plane offset (e.g. each leg's Y station).

Convention, matching the rest of ``cadlib``:

- keyword-only arguments;
- :func:`place_two_point` returns a new ``cq.Workplane`` (does not mutate);
- ``ValueError`` on an unreachable / inconsistent spec, so the failure points at
  the link lengths, not at OCCT five frames deep.
"""

from __future__ import annotations

import math

import cadquery as cq

Point2 = "tuple[float, float]"
Point3 = "tuple[float, float, float]"


def circle_intersections(
    *,
    c0: tuple[float, float],
    r0: float,
    c1: tuple[float, float],
    r1: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """The two points where circle ``(c0, r0)`` meets circle ``(c1, r1)``.

    This is the kernel of every two-link loop closure: a coupler of length
    ``r0`` pinned at ``c0`` and a rocker of length ``r1`` pinned at ``c1`` can
    only meet where their circles cross. Returns both intersection points; the
    caller (or :func:`solve_fourbar`) picks the branch.

    All coordinates are in one 2-D working plane (mm). Raises ``ValueError``
    when the circles cannot cross — the spec is wrong, not the math:

    - ``dist(c0, c1) > r0 + r1`` → links too short to reach (loop won't close);
    - ``dist(c0, c1) < |r0 - r1|`` → one circle sits inside the other;
    - ``c0 == c1`` → coincident centres (degenerate).

    Example::

        a, b = circle_intersections(c0=(8, -13), r0=20, c1=(-16, -13), r1=20)
    """
    if r0 <= 0 or r1 <= 0:
        raise ValueError(f"radii must be positive, got r0={r0}, r1={r1}")
    (x0, y0), (x1, y1) = c0, c1
    dx, dy = x1 - x0, y1 - y0
    d = math.hypot(dx, dy)
    if d == 0.0:
        raise ValueError("circle centres coincide — no unique linkage solution")
    if d > r0 + r1 + 1e-9:
        raise ValueError(
            f"links cannot reach: centre distance {d:.3f} > r0+r1 {r0 + r1:.3f}. "
            "Lengthen a link or move the pivots closer."
        )
    if d < abs(r0 - r1) - 1e-9:
        raise ValueError(
            f"one circle is inside the other: centre distance {d:.3f} < "
            f"|r0-r1| {abs(r0 - r1):.3f}. The loop cannot close."
        )
    # Distance from c0 to the foot of the radical line, then the half-chord.
    a = (r0 * r0 - r1 * r1 + d * d) / (2.0 * d)
    h2 = r0 * r0 - a * a
    h = math.sqrt(max(0.0, h2))
    # Foot point along c0->c1.
    ux, uy = dx / d, dy / d
    fx, fy = x0 + a * ux, y0 + a * uy
    # Perpendicular (90° CCW of the c0->c1 unit vector).
    px, py = -uy, ux
    left = (fx + h * px, fy + h * py)
    right = (fx - h * px, fy - h * py)
    return left, right


def solve_fourbar(
    *,
    crank_pin: tuple[float, float],
    ground_pivot: tuple[float, float],
    coupler: float,
    rocker: float,
    branch: str = "left",
) -> tuple[float, float]:
    """Solve the moving joint **C** of a four-bar so both links reach it.

    A four-bar leg (Hoeken, Klann, Jansen, …) has two anchored pins — the
    **crank pin** ``B`` (the eccentric/journal the coupler eye wraps) and the
    **ground pivot** ``D`` (the fixed post the rocker swings on) — joined by the
    coupler (``B→C``, length ``coupler``) and the rocker (``D→C``, length
    ``rocker``). For a given crank angle, ``B`` and ``D`` are fixed, so ``C`` is
    just where the two link circles cross. This returns that single ``C`` — the
    one point **both** the leg and the rocker must be placed to meet at.

    All coords are in the mechanism's 2-D working plane (e.g. X–Z for a walker;
    map the plane's two axes to the tuple's two entries). ``branch`` selects the
    elbow: ``"left"`` (default) or ``"right"`` of the ``B→D`` direction. If the
    foot ends up on the wrong side, flip the branch — don't re-tilt a link.

    Raises ``ValueError`` (via :func:`circle_intersections`) when the link
    lengths can't span ``B``–``D``.

    Example — one ladybug-style station (X=u, Z=v), crank at phase 0::

        C = solve_fourbar(
            crank_pin=(8.0, -13.0),     # eccentric journal in X–Z
            ground_pivot=(-16.0, -13.0),# chassis D-post
            coupler=20.0, rocker=20.0, branch="right",
        )
        # then place the leg by (B, C) and the rocker by (D, C); they meet at C.
    """
    if branch not in ("left", "right"):
        raise ValueError(f"branch must be 'left' or 'right', got {branch!r}")
    left, right = circle_intersections(
        c0=crank_pin, r0=coupler, c1=ground_pivot, r1=rocker
    )
    return left if branch == "left" else right


def place_two_point(
    part: cq.Workplane,
    *,
    p0_local: tuple[float, float, float],
    p1_local: tuple[float, float, float],
    p0_world: tuple[float, float, float],
    p1_world: tuple[float, float, float],
    roll_deg: float = 0.0,
) -> cq.Workplane:
    """Place ``part`` so two of its local points land on two world points.

    The rigid-body way to pose a link: instead of guessing a rotation, name two
    reference points on the part — typically its two joint centres
    (``p0_local`` = the eye at the part's origin, ``p1_local`` = the far pin) —
    and the two world points they must occupy (``p0_world``, ``p1_world``, e.g.
    the solved ``B`` and ``C``). The part is translated and rotated so
    ``p0_local`` → ``p0_world`` exactly and its ``p0→p1`` axis aims at
    ``p1_world``. ``roll_deg`` spins the part about that axis (to orient its
    width/thickness — e.g. point a foot peg sideways). Returns a new
    ``cq.Workplane``; ``part`` is not mutated.

    Because a printed link is rigid, ``|p1_local - p0_local|`` must equal
    ``|p1_world - p0_world|`` (the solved span). A mismatch beyond ~1% means the
    part's pin spacing and the solved joint distance disagree — a spec bug —
    and raises ``ValueError`` rather than silently leaving ``p1`` off its pin.

    Example — place a coupler-leg built along local +X (eye at origin, C-pin at
    ``(coupler, 0, 0)``) onto solved world points ``B`` and ``C``::

        leg = place_two_point(
            leg, p0_local=(0, 0, 0), p1_local=(coupler, 0, 0),
            p0_world=B_world, p1_world=C_world,
        )
    """
    lv = cq.Vector(*p1_local) - cq.Vector(*p0_local)
    wv = cq.Vector(*p1_world) - cq.Vector(*p0_world)
    ll, wl = lv.Length, wv.Length
    if ll < 1e-9:
        raise ValueError("p0_local and p1_local coincide — need two distinct points")
    if wl < 1e-9:
        raise ValueError("p0_world and p1_world coincide — no direction to aim at")
    if abs(ll - wl) > max(0.01, 0.01 * wl):
        raise ValueError(
            f"rigid-link mismatch: local span {ll:.3f} mm != world span "
            f"{wl:.3f} mm. The part's pin spacing and the solved joint distance "
            "disagree — fix the link length or the loop solution."
        )

    # 1) bring p0_local to the origin
    out = part.translate((-p0_local[0], -p0_local[1], -p0_local[2]))

    # 2) rotate local axis -> world axis, about an axis through the origin
    lu = lv.multiply(1.0 / ll)
    wu = wv.multiply(1.0 / wl)
    axis = lu.cross(wu)
    if axis.Length < 1e-9:
        # parallel or antiparallel
        if lu.dot(wu) < 0:
            # 180°: spin about any axis perpendicular to lu
            perp = lu.cross(cq.Vector(0, 0, 1))
            if perp.Length < 1e-9:
                perp = lu.cross(cq.Vector(1, 0, 0))
            out = out.rotate((0, 0, 0), perp.toTuple(), 180.0)
    else:
        angle = math.degrees(math.acos(max(-1.0, min(1.0, lu.dot(wu)))))
        out = out.rotate((0, 0, 0), axis.toTuple(), angle)

    # 3) optional roll about the (now world-aligned) axis through the origin
    if roll_deg:
        out = out.rotate((0, 0, 0), wu.toTuple(), roll_deg)

    # 4) translate origin -> p0_world
    return out.translate(tuple(p0_world))
