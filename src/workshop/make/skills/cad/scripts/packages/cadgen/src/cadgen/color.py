"""Colour helpers for build123d part authoring.

A build123d ``Color``'s channels are **sRGB display values**: ``Color(r, g, b)``
reads them as sRGB, and the STEP writer stores them unchanged in
``COLOUR_RGB``. Every STEP viewer (FreeCAD and anything else on OpenCascade,
web viewers, slicers, the shop) shows those values as the colour on screen. So
``part.color = srgb("#5A3A22")`` is ``Color(0x5A/255, 0x3A/255, 0x22/255)``, and
the STEP opens as ``#5A3A22`` everywhere::

    from cadgen.color import srgb

    part.color = srgb("#2E3742")        # the hex you picked in a design tool
    glass.color = srgb("#38414D", 0.42) # with alpha

Renderers that light in linear light convert with :func:`linear_channels`, and
glTF ``baseColorFactor`` (linear by definition) is taken from the STEP as
OpenCascade decodes it.

Until 2026-11-05 this module handed ``Color`` *linear* channels, so a STEP made
then holds every colour darkened twice: dark oak ``#5A3A22`` was written as
``(0.102, 0.042, 0.016)`` and opened as ``#1A0B04`` outside Workshop. Such a
colour is recognisable exactly: each channel is ``srgb_to_linear(k / 255)`` for
a byte ``k``. :func:`is_legacy_linear` detects it, and :func:`display_channels`
and :func:`linear_channels` read it as it was meant, so older sealed STEPs and
frozen runs still show their colours.

Note also that colour set on a *group* compound never reaches the renderer --
only leaf occurrences carry colour into the render package. Style every leaf.
"""

from __future__ import annotations

from typing import Sequence

__all__ = [
    "srgb",
    "srgb_to_linear",
    "linear_to_srgb",
    "is_legacy_linear",
    "display_channels",
    "linear_channels",
]

# OpenCascade keeps a colour in float32 and build123d rounds it to 7 digits,
# so a legacy channel strays up to 5e-8 from its byte's linear value; no
# k/255 lies within 1.04e-6 of one.
_LEGACY_TOLERANCE = 2e-7


def srgb_to_linear(channel: float) -> float:
    """Convert one 0..1 sRGB channel to linear RGB."""
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def linear_to_srgb(channel: float) -> float:
    """Inverse of :func:`srgb_to_linear`."""
    if channel <= 0.0031308:
        return channel * 12.92
    return 1.055 * (channel ** (1 / 2.4)) - 0.055


_LINEAR_BYTES = tuple(srgb_to_linear(k / 255.0) for k in range(256))


def _linear_byte(value: float) -> bool:
    # The table rises monotonically, so the nearest entry is one of two.
    low, high = 0, 255
    while low < high:
        middle = (low + high) // 2
        if _LINEAR_BYTES[middle] < value:
            low = middle + 1
        else:
            high = middle
    return any(
        abs(_LINEAR_BYTES[k] - value) <= _LEGACY_TOLERANCE
        for k in (low - 1, low)
        if 0 <= k <= 255
    )


def is_legacy_linear(rgb: Sequence[float]) -> bool:
    """True for a colour the pre-2026-11-05 helpers wrote as linear channels.

    Each channel is exactly a byte's linear value and at least one is neither
    0 nor 1 (where sRGB and linear agree). A colour typed by hand or read from
    an sRGB hex never matches.
    """
    channels = [float(value) for value in tuple(rgb)[:3]]
    if len(channels) != 3:
        return False
    if all(value in (0.0, 1.0) for value in channels):
        return False
    return all(_linear_byte(value) for value in channels)


def display_channels(rgb: Sequence[float]) -> tuple[float, float, float]:
    """The sRGB channels a colour displays as (a legacy linear colour encoded)."""
    channels = tuple(min(1.0, max(0.0, float(value))) for value in tuple(rgb)[:3])
    if is_legacy_linear(channels):
        return tuple(linear_to_srgb(value) for value in channels)
    return channels


def linear_channels(rgb: Sequence[float]) -> tuple[float, float, float]:
    """The linear-light channels of a colour, for lighting or glTF."""
    channels = tuple(min(1.0, max(0.0, float(value))) for value in tuple(rgb)[:3])
    if is_legacy_linear(channels):
        return channels
    return tuple(srgb_to_linear(value) for value in channels)


def _parse_hex(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) != 6:
        raise ValueError(f"expected a #rgb or #rrggbb colour, got {value!r}")
    try:
        return int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16)
    except ValueError as exc:
        raise ValueError(f"expected a hex colour, got {value!r}") from exc


def srgb(value: str, alpha: float = 1.0):
    """Build a build123d ``Color`` from the sRGB hex you want to SEE on screen.

    ``value`` is ``#rgb`` or ``#rrggbb``. ``alpha`` is 0..1.
    """
    from build123d import Color

    red, green, blue = _parse_hex(value)
    return Color(red / 255.0, green / 255.0, blue / 255.0, alpha)
