"""Edge-softening and proportion helpers — the radius language of a part.

These are the *aesthetic* building blocks (see
``references/industrial-design.md``): they give a part one consistent fillet /
chamfer radius instead of a scatter of raw 90° arrises, which is most of what
separates a premium-looking object from a blocky one. They are deliberately thin
wrappers over CadQuery's ``.fillet`` / ``.chamfer`` so the radius *choice* —
the part that carries taste — lives in one place and stays uniform.

Function and printability come first: never soften an edge a load path needs
sharp, never pick a radius that thins a wall below its minimum, and scope the
selector so a fillet can't reach an edge too short to round (OCCT throws, or
worse, makes a sliver). When a blanket ``.fillet`` fails, fillet a named edge
selection instead of every edge.
"""

from __future__ import annotations

import cadquery as cq


def design_radius_for(
    *,
    size: float,
    fraction: float = 0.08,
    minimum: float = 0.6,
    maximum: float = 4.0,
) -> float:
    """A tasteful unified corner/edge radius derived from a part dimension (mm).

    Returns ``fraction`` of ``size`` clamped to ``[minimum, maximum]``. Feed it
    the smallest relevant plan dimension so the radius reads consistent across
    the object rather than guessing a number per edge. ``fraction`` 0.06–0.12 is
    the premium-product band; the clamp keeps tiny parts from vanishing and big
    parts from looking like a pillow.

    >>> design_radius_for(size=80)        # 0.08 * 80 = 6.4 -> clamped to 4.0
    4.0
    >>> design_radius_for(size=20)        # 0.08 * 20
    1.6
    """
    if size <= 0:
        raise ValueError(f"size must be > 0, got {size}")
    if fraction <= 0:
        raise ValueError(f"fraction must be > 0, got {fraction}")
    if minimum < 0 or maximum < minimum:
        raise ValueError(f"need 0 <= minimum <= maximum, got {minimum}, {maximum}")
    return max(minimum, min(maximum, size * fraction))


def soften_edges(
    part: cq.Workplane,
    *,
    radius: float,
    selector: str | None = None,
) -> cq.Workplane:
    """Fillet edges of ``part`` with ONE consistent radius (mm) — the core of a
    unified radius language.

    ``selector`` is a CadQuery string selector (e.g. ``"|Z"`` for vertical
    edges, ``">Z"`` for the top face's edges); ``None`` rounds every edge. Scope
    it: a blanket fillet on a complex body often fails in OCCT where three
    fillets meet at a vertex, and rounding a functional/mating edge is usually
    wrong. Returns a new ``cq.Workplane`` (does not mutate ``part``).

    >>> body = cq.Workplane("XY").box(80, 60, 20)
    >>> body = soften_edges(body, radius=2.0, selector="|Z")   # vertical corners
    """
    if radius <= 0:
        raise ValueError(f"radius must be > 0, got {radius}")
    edges = part.edges(selector) if selector else part.edges()
    return edges.fillet(radius)


def break_edges(
    part: cq.Workplane,
    *,
    size: float,
    selector: str | None = None,
) -> cq.Workplane:
    """Chamfer edges of ``part`` with ONE consistent size (mm) — a crisp bevel
    where a fillet would read soft or where the flat catches a deliberate line
    of light.

    Same selector rules as ``soften_edges``. A chamfer also tames a top-face
    overhang for printing (a 45° break needs no support) where a full fillet
    would. Returns a new ``cq.Workplane`` (does not mutate ``part``).

    >>> body = cq.Workplane("XY").box(80, 60, 20)
    >>> body = break_edges(body, size=1.0, selector=">Z")      # top edge bevel
    """
    if size <= 0:
        raise ValueError(f"size must be > 0, got {size}")
    edges = part.edges(selector) if selector else part.edges()
    return edges.chamfer(size)
