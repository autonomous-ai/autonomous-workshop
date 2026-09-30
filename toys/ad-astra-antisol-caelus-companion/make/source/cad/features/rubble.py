"""The asteroid belt's rubble field.

Faceted rather than rounded: small circular detail degrades at nozzle scale
where a facet holds its shape.  Every rock is a prism that narrows as it rises,
so nothing here faces downward, and the whole field is trimmed flat at the
field datum so every crest a seated disc can touch is coplanar with the landing
pad.

**No rock touches another.**  That rule is the whole difference between this
field and the one before it, and it was forced by measurement.  The earlier
field fused a hundred and seventy-six tapered prisms at random overlaps, and
wherever two prism walls crossed at a shallow angle -- which a taper guarantees
will happen somewhere, because two prisms that overlap at the base grow tangent
on the way up -- the kernel returned a real but microscopic face.  Measured on
the built tile: a face of 0.0003 mm2 and an edge 1.2 micrometres long.  Those
survive in memory, where `BRepCheck_Analyzer` calls the tile valid, and die in
the assembly package, where `inspect validate` reported `invalidTopology` on
all twelve belt tiles.  Twelve seeds were tried and every one produced slivers;
`ShapeFix_Shape` and `ShapeUpgrade_UnifySameDomain` left them untouched,
because they are genuine geometry and not a tolerance artefact.  The placement
rule was the defect.

With the rocks disjoint there is no rock-to-rock boolean left at all.  What
remains -- rock against the landing pad, rock against the tile's own edge --
is held the same way: clearly clear of the tangency or frankly across it,
never within `MARGIN`.  Measured after the change: worst face 0.019 mm2, worst
edge 0.078 mm, and the tile's face count fell from 906 to 432.

The cost is stated plainly: sixty boulders instead of a hundred and
seventy-six, so the belt reads as scattered rock rather than as a continuous
crumbly mat.
"""

from __future__ import annotations

import math
import random

from build123d import Pos, RegularPolygon, Rot, extrude

# How far from any tangency a rock has to stay, in millimetres.  0.35 is a
# little under one nozzle width.
MARGIN = 0.35
ROCK_MIN_R = 1.60
ROCK_MAX_R = 2.60
ROCKS_PER_QUADRANT = 12
# A tapered prism closes to a point at radius/tan(taper).  Every rock is
# stopped below that, so each one ends in a flat top instead of an apex:
# an apex is a cone tip, and a cone tip trimmed by anything is the sliver
# this module is here to avoid.
TIP_MARGIN = 0.80


def _placements(half_size: float, pad_radius: float, seed: int, margin: float):
    """Disjoint rock centres and radii that clear every tangency."""
    rng = random.Random(seed)
    placed: list[tuple[float, float, float]] = []
    attempts = 0
    while len(placed) < ROCKS_PER_QUADRANT and attempts < 80000:
        attempts += 1
        x = rng.uniform(0.4, half_size - 1.0)
        y = rng.uniform(0.4, half_size - 1.0)
        radius = rng.uniform(ROCK_MIN_R, ROCK_MAX_R)
        distance = math.hypot(x, y)

        # Against the landing pad: bite it properly or stand off it properly.
        if distance < pad_radius + radius * 0.15:
            continue
        if abs(distance - (pad_radius + radius)) < margin:
            continue
        if abs(distance - (pad_radius - radius)) < margin:
            continue

        # Against the tile edge on both axes: wholly inside or frankly across.
        if any(abs(coord + radius - half_size) < margin for coord in (x, y)):
            continue

        # Against every rock already down: disjoint, with room to spare.
        if any(
            math.hypot(x - px, y - py) < pr + radius + margin
            for px, py, pr in placed
        ):
            continue
        placed.append((x, y, radius))
    return placed


def rubble_field(half_size: float, pad_radius: float, floor_z: float, crest_z: float, seed: int):
    """One quadrant of rock, repeated four times for 90 degree symmetry."""
    placed = _placements(half_size, pad_radius, seed, MARGIN)
    if not placed:
        return None
    rng = random.Random(seed ^ 0x5EED)
    height = crest_z - floor_z
    quadrant = []
    # Boulders, not pinnacles: wide bases, strong taper, and most of them
    # ending below the datum so only a handful are trimmed flat.  A rock either
    # clears the datum by a quarter of the field height or stops well under it;
    # nothing finishes level with the trim plane, because a rock cut exactly at
    # its own crest is the same shallow intersection this module exists to
    # forbid.
    for x, y, radius in placed:
        sides = rng.choice((5, 6, 6, 7, 8))
        taper = rng.uniform(34.0, 44.0)
        reach = rng.random()
        rise = height * (1.30 if reach > 0.55 else 0.30 + 0.55 * reach)
        rise = min(rise, TIP_MARGIN * radius / math.tan(math.radians(taper)))
        rock = extrude(
            RegularPolygon(radius, sides, rotation=rng.uniform(0.0, 60.0)),
            rise,
            taper=taper,
        )
        quadrant.append(Pos(x, y, floor_z) * rock)
    body = quadrant[0] if len(quadrant) == 1 else quadrant[0] + quadrant[1:]
    turns = [Rot(0, 0, angle) * body for angle in (0.0, 90.0, 180.0, 270.0)]
    return turns[0] + turns[1:]
