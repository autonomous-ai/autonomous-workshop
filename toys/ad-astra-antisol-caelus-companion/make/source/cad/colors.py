"""Filament colour, sealed the way the shop reads it.

The occurrence name says which spool prints a part; the sealed ``Color``
channels say what the listing shows.  The host and the shop read those channels
as sRGB, so the hex the catalogue publishes goes in unconverted.
"""

from __future__ import annotations

from build123d import Color

from params import FILAMENT_HEX


def filament(name: str, alpha: float = 1.0) -> Color:
    """A ``Color`` whose channels are the catalogue sRGB hex, 0..1."""
    try:
        hex_value = FILAMENT_HEX[name]
    except KeyError as exc:
        raise ValueError(
            "%r is not a stocked filament; choose one of: %s"
            % (name, ", ".join(sorted(FILAMENT_HEX)))
        ) from exc
    red = int(hex_value[1:3], 16) / 255.0
    green = int(hex_value[3:5], 16) / 255.0
    blue = int(hex_value[5:7], 16) / 255.0
    return Color(red, green, blue, alpha)


def paint(shape, name: str):
    """Seal a filament colour on one leaf shape and return it."""
    shape.color = filament(name)
    return shape
