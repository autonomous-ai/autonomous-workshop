"""The seven-segment numeral that carries a world's rank.

Rank has three independent channels in this set -- globe diameter, surface
markings, and this numeral.  The numeral is the one that needs no comparison
against a neighbouring piece, so it has to be unambiguous at a glance, and it
is repeated at 0 and 180 degrees so both seated players read it without
touching a piece.
"""

from __future__ import annotations

from build123d import Pos, Rectangle, Sketch

# a top, b upper-right, c lower-right, d bottom, e lower-left, f upper-left,
# g middle.
_DIGITS = {
    1: "bc",
    2: "abdeg",
    3: "abcdg",
    4: "bcfg",
    5: "acdfg",
    6: "acdefg",
    7: "abc",
    8: "abcdefg",
}


def seven_segment_sketch(digit: int, height: float, width: float, stroke: float) -> Sketch:
    """One digit as a fused 2D sketch, centred on the origin of Plane.XY."""
    segments = _DIGITS[digit]
    bar_x = width / 2.0 - stroke / 2.0          # centre of a vertical stroke
    bar_y = height / 2.0 - stroke / 2.0         # centre of the top/bottom stroke
    run = width - stroke                        # length of a horizontal stroke
    rise = height / 2.0 - stroke                # length of a vertical stroke
    mid = height / 4.0                          # centre of a vertical stroke

    pieces = []
    if "a" in segments:
        pieces.append(Pos(0, bar_y) * Rectangle(run, stroke))
    if "g" in segments:
        pieces.append(Pos(0, 0) * Rectangle(run, stroke))
    if "d" in segments:
        pieces.append(Pos(0, -bar_y) * Rectangle(run, stroke))
    if "f" in segments:
        pieces.append(Pos(-bar_x, mid) * Rectangle(stroke, rise))
    if "b" in segments:
        pieces.append(Pos(bar_x, mid) * Rectangle(stroke, rise))
    if "e" in segments:
        pieces.append(Pos(-bar_x, -mid) * Rectangle(stroke, rise))
    if "c" in segments:
        pieces.append(Pos(bar_x, -mid) * Rectangle(stroke, rise))

    return pieces[0] if len(pieces) == 1 else pieces[0] + pieces[1:]
