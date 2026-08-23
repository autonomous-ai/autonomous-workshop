"""Point generators for placing features (holes, posts, magnets, etc).

All functions return ``list[tuple[float, float]]`` of XY coordinates.
Use with ``.pushPoints(points)`` or pass to ``mounting.add_screw_post``,
``cutouts.add_magnet_pocket``, etc.
"""

from __future__ import annotations

import math


def four_corner_points(
    *, length: float, width: float, margin: float
) -> list[tuple[float, float]]:
    """Four points, one inset ``margin`` mm from each corner of a
    ``length × width`` rectangle centered on the origin.

    Use for screw bosses, magnet pockets at corners, etc.

    >>> four_corner_points(length=80, width=60, margin=5)
    [(35.0, 25.0), (-35.0, 25.0), (-35.0, -25.0), (35.0, -25.0)]
    """
    if margin * 2 >= min(length, width):
        raise ValueError(
            f"margin {margin} too large for {length}x{width} rectangle"
        )
    x = length / 2 - margin
    y = width / 2 - margin
    return [(x, y), (-x, y), (-x, -y), (x, -y)]


def grid_points(
    *, n_x: int, n_y: int, pitch_x: float, pitch_y: float | None = None
) -> list[tuple[float, float]]:
    """``n_x × n_y`` regular grid, centered on the origin.

    >>> grid_points(n_x=2, n_y=2, pitch_x=10)
    [(-5.0, -5.0), (5.0, -5.0), (-5.0, 5.0), (5.0, 5.0)]
    """
    if n_x < 1 or n_y < 1:
        raise ValueError(f"n_x and n_y must be >= 1, got {n_x}, {n_y}")
    py = pitch_y if pitch_y is not None else pitch_x
    x0 = -(n_x - 1) * pitch_x / 2
    y0 = -(n_y - 1) * py / 2
    return [
        (x0 + i * pitch_x, y0 + j * py)
        for j in range(n_y)
        for i in range(n_x)
    ]


def circle_points(
    *, n: int, radius: float, start_deg: float = 0.0
) -> list[tuple[float, float]]:
    """``n`` points evenly spaced on a circle of given ``radius`` around the
    origin. ``start_deg`` rotates the whole pattern.

    >>> pts = circle_points(n=4, radius=10)
    >>> [(round(x, 3), round(y, 3)) for (x, y) in pts]
    [(10.0, 0.0), (0.0, 10.0), (-10.0, 0.0), (-0.0, -10.0)]
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    out: list[tuple[float, float]] = []
    for i in range(n):
        a = math.radians(start_deg + i * 360 / n)
        out.append((radius * math.cos(a), radius * math.sin(a)))
    return out
