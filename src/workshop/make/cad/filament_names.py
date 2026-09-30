"""The colour vocabulary a sealed occurrence name is allowed to end in.

A multi-part toy is sealed as one production STEP per occurrence, and
whoever loads the printer has to know which spool each of those files wants.
The occurrence name is the only field that travels with the part everywhere --
into ``parts/<name>.step`` and the assembly-package -- so this is where the
spool is said out loud: ``arm_black``,
``leg_dark_brown``, ``canopy_misty_blue``.

The names here are exactly the ones the CAD skill's filament palette stocks
(``make/skills/cad/scripts/cadfilament.py``): 43 distinct colours across the 51
spools of Bambu Lab PLA Lite, PLA Matte and PETG Basic.  Eight names are in
more than one stock, so a name alone does not say which spool -- the *colour*
does not have to be decidable from the name for the name to be useful, and this
module deliberately does not try to decide it.  It answers one question: does this
occurrence name end in a colour somebody can actually buy?

Why the table is repeated here rather than imported: the palette lives inside
the vendored ``cad`` skill tree, which is materialized per run and refreshed by
upstream resyncs, while this module is trusted host substrate that a gate reads
on every Make proposal.  ``tests/make/test_filament_palette.py`` holds the two
tables to the same contents, so a colour retired or stocked upstream fails CI
here rather than drifting silently.

Colour space is not this module's business.  The sealed channels are checked by
``make-part-colours-missing``; the name is checked here, and the two are not
compared -- the palette authors a ``Color`` through ``cadgen.color.srgb`` while
the host and the shop read sealed channels as sRGB, and that reconciliation is
still open.
"""

from __future__ import annotations

from typing import Optional, Tuple


__all__ = [
    "FILAMENT_COLOUR_NAMES",
    "normalise_colour_name",
    "occurrence_colour_name",
]


#: Every colour name the filament palette stocks, in the ``_``-joined form an
#: occurrence name carries.  The union of every stock: a part is named for the
#: colour it prints in, not for the stock it prints from.
FILAMENT_COLOUR_NAMES: Tuple[str, ...] = (
    "apple_green",
    "ash_gray",
    "beige",
    "black",
    "blue",
    "bone_white",
    "caramel",
    "charcoal",
    "cocoa_brown",
    "cyan",
    "dark_beige",
    "dark_blue",
    "dark_brown",
    "dark_chocolate",
    "dark_gray",
    "dark_green",
    "dark_red",
    "desert_tan",
    "grass_green",
    "gray",
    "green",
    "ice_blue",
    "ivory_white",
    "latte_brown",
    "lemon_yellow",
    "lilac_purple",
    "mandarin_orange",
    "marine_blue",
    "misty_blue",
    "nardo_gray",
    "navy_blue",
    "orange",
    "pine_green",
    "plum",
    "red",
    "reflex_blue",
    "sakura_pink",
    "scarlet_red",
    "sky_blue",
    "sunflower_yellow",
    "terracotta",
    "white",
    "yellow",
)

# Longest first, so `arm_navy_blue` reports `navy_blue` rather than the `blue`
# that also ends it, and `leg_dark_gray` reports the spool it means.
_BY_LENGTH: Tuple[str, ...] = tuple(
    sorted(FILAMENT_COLOUR_NAMES, key=lambda name: (-len(name), name))
)


def normalise_colour_name(text: str) -> str:
    """Return a colour name in the ``_``-joined form this module compares.

    Matches ``cadfilament._normalise`` except for the separator it settles on:
    case, hyphens, spaces and repeated separators all collapse, so ``"Dark
    Gray"``, ``"dark-gray"`` and ``"DARK_GRAY"`` are one colour.
    """

    if not isinstance(text, str):
        raise TypeError("a colour name must be text")
    return "_".join(text.replace("-", " ").replace("_", " ").lower().split())


def occurrence_colour_name(name: str) -> Optional[str]:
    """Return the stocked colour an occurrence name ends in, or ``None``.

    The name has to be ``<part>_<colour>`` with a non-empty part half, so
    ``arm_black`` names a colour and a bare ``black`` does not: a part called
    only by its spool says nothing about which part it is.  A hyphen reads as
    the same separator an underscore does, so ``arm-black`` is the same name.
    """

    if not isinstance(name, str):
        return None
    normalised = normalise_colour_name(name)
    for colour in _BY_LENGTH:
        suffix = "_%s" % colour
        if normalised.endswith(suffix) and len(normalised) > len(suffix):
            return colour
    return None
