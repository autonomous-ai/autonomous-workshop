"""Flat-plate features: rounded squares and the star's hexagonal granulation."""

from __future__ import annotations

from build123d import (
    Pos,
    Rectangle,
    RectangleRounded,
    RegularPolygon,
    Rot,
    Sketch,
    extrude,
)


def rounded_square_sketch(size: float, radius: float, width: float | None = None) -> Sketch:
    """One rounded rectangle, centred on the origin of Plane.XY."""
    depth = size if width is None else width
    if radius <= 0:
        return Rectangle(size, depth)
    return RectangleRounded(size, depth, radius)


def hex_grain_tool(frame: float, clear: float, pitch: float, depth: float, z0: float):
    """Hexagonal granulation cut into the four corners of a square plate.

    Engraved, not raised.  A raised grain half a millimetre tall is thinner
    than the nozzle can hold as a wall; a pocket of the same size leaves the
    plate solid around it and still catches light at the product frame.  The
    grains keep clear of the circle a seated piece stands on, so they live in
    the four corners the disc never covers.
    """
    r = pitch * 0.34
    prism = extrude(RegularPolygon(r, 6), depth + 0.4)
    grains = []
    reach = int(frame / (pitch * 0.866)) + 2
    for row in range(-reach, reach + 1):
        y = row * pitch * 0.866
        for col in range(-reach, reach + 1):
            x = col * pitch + (pitch / 2.0 if row % 2 else 0.0)
            if max(abs(x), abs(y)) > frame / 2.0 - r - 0.35:
                continue
            if (x * x + y * y) ** 0.5 < clear / 2.0 + r:
                continue
            grains.append(Pos(x, y, z0 - depth) * prism)
    if not grains:
        return None
    return grains[0] if len(grains) == 1 else grains[0] + grains[1:]
