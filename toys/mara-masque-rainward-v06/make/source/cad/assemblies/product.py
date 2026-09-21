"""Placement of the Sun, its twenty-four lane tiles and the thirty counters."""
from math import sqrt

from build123d import *

import params as P
from parts.body import sun_body
from parts.counter import counter, counter_label
from parts.tile import lane_tile, tile_label
from profiles import theta, xy

# Preserved illustration geometry: the hit victim travels the same distance.
BAR_HIT_R = P.RADII[0] - sqrt(70.0 ** 2 - (P.BAR_TOP - P.LANE_TOP) ** 2)


def piece_poses(state="setup"):
    """Preserved counter placement: five radial stations, three aligned layers."""
    if state == "board":
        return {}
    a, b = ((P.INITIAL_A, P.INITIAL_B) if state == "setup"
            else (P.BEFORE_A, P.BEFORE_B))
    out = {}
    for kind, counts in (("single", a), ("fork", b)):
        index = 0
        for point, n in sorted(counts.items()):
            for j in range(n):
                index += 1
                x, y = xy(P.RADII[j % 5], theta(point))
                out[counter_label(kind, index)] = (
                    kind, point, (x, y, P.LANE_TOP + (j // 5) * P.DROP_H), theta(point))
    if state == "after":
        attacker = next(k for k, v in out.items() if v[0] == "single" and v[1] == 7)
        victim = next(k for k, v in out.items() if v[0] == "fork" and v[1] == 1)
        out[attacker] = ("single", 1, out[victim][2], theta(1))
        out[victim] = ("fork", 0, (*xy(BAR_HIT_R, theta(1)), P.BAR_TOP), theta(1))
    assert len(out) == 2 * P.COUNTERS_PER_SIDE
    return out


def _tone(shape, neutral):
    if neutral:
        shape.color = Color(*P.NEUTRAL_COLOR)
    return shape


def assembly(state="setup", neutral=False):
    """The complete set: fifty-five separate solids, nothing fused together.

    `state="board"` returns the Sun and its twenty-four tiles with no counters;
    that is the single-material evidence view for counting lanes and banks.
    """
    children = []

    body = sun_body().moved(Location())
    body.label = sun_body().label
    body.color = sun_body().color
    children.append(_tone(body, neutral))

    for point in range(1, P.LANES + 1):
        tile = lane_tile(point).moved(Location())
        tile.label = tile_label(point)
        tile.color = lane_tile(point).color
        children.append(_tone(tile, neutral))

    for name, (kind, _point, position, angle) in piece_poses(state).items():
        piece = Pos(*position) * Rot(Z=angle) * counter(kind)
        piece.label = name
        piece.color = counter(kind).color
        children.append(_tone(piece, neutral))

    expected = 1 + P.LANES + (0 if state == "board" else 2 * P.COUNTERS_PER_SIDE)
    assert len(children) == expected
    return Compound(label="rainward_emberfan", children=children)
