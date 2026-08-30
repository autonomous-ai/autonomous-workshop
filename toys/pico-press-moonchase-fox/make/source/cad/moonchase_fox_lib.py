"""Parametric one-piece Moonchase Fox geometry."""

from build123d import (
    Align,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterArc,
    Ellipse,
    Kind,
    Locations,
    Mode,
    Pos,
    Rectangle,
    Side,
    extrude,
    make_face,
    offset,
)

# Manufacturing and envelope parameters [assumed from palm-sized Wish].
DEPTH = 24.0
TRACK_RADIUS = 45.0
TRACK_CENTER_X = -6.0
TRACK_CENTER_Y = 45.0
TAIL_CAP_Y = 50.0

# Anatomical masses [inferred fox silhouette].
BODY_CENTER = (-13.47, 34.0)
BODY_RADII = (31.0, 23.0)
CHEST_CENTER = (8.53, 39.0)
CHEST_RADII = (21.0, 20.0)
HEAD_CENTER = (15.53, 52.0)
HEAD_RADII = (18.0, 15.0)
MUZZLE_CENTER = (29.53, 47.0)
MUZZLE_RADII = (13.0, 8.0)

# Symbolic feature [Wish/inferred].
MOON_CENTER = (1.0, 38.0)
MOON_ARC_RADIUS = 12.5
MOON_SLOT_RADIUS = 3.5


def _validate_parameters() -> None:
    assert DEPTH >= 20.0
    assert TRACK_CENTER_Y == TRACK_RADIUS  # lowest track point is y=0
    assert MOON_SLOT_RADIUS >= 3.0


def _base_silhouette():
    """Build the connected XY silhouette and extrude it in the flat print stance."""
    with BuildPart() as base:
        with BuildSketch():
            with Locations((TRACK_CENTER_X, TRACK_CENTER_Y)):
                Ellipse(TRACK_RADIUS, TRACK_RADIUS)
            with Locations((TRACK_CENTER_X, 0.0)):
                Rectangle(
                    2.0 * TRACK_RADIUS,
                    TAIL_CAP_Y,
                    align=(Align.CENTER, Align.MIN),
                    mode=Mode.INTERSECT,
                )
        extrude(amount=DEPTH)
        with BuildSketch():
            with Locations((-31.5, 49.0)):
                Ellipse(18.0, 23.0, rotation=-12.0)
            with Locations(BODY_CENTER):
                Ellipse(*BODY_RADII)
            with Locations(CHEST_CENTER):
                Ellipse(*CHEST_RADII)
            with Locations(HEAD_CENTER):
                Ellipse(*HEAD_RADII)
            with Locations(MUZZLE_CENTER):
                Ellipse(*MUZZLE_RADII)
            with Locations((7.0, 66.0)):
                Ellipse(5.2, 12.0, rotation=-12.0)
            with Locations((21.0, 65.5)):
                Ellipse(5.0, 11.5, rotation=15.0)
        extrude(amount=DEPTH)
    return base.part


def _crescent_window():
    # Rounded C-slot: a 240-degree arc offset equally on both sides. It reads as
    # a crescent with right-pointing horns but has finite, semicircular ends
    # rather than zero-thickness circle-intersection cusps.
    with BuildLine() as moon_path:
        CenterArc(MOON_CENTER, MOON_ARC_RADIUS, 60.0, 240.0)
    moon_outline = offset(
        moon_path.line,
        amount=MOON_SLOT_RADIUS,
        side=Side.BOTH,
        kind=Kind.ARC,
        closed=True,
    )
    moon_face = make_face(moon_outline)
    return Pos(0.0, 0.0, -1.0) * extrude(moon_face, amount=DEPTH + 2.0)


def build_fox():
    _validate_parameters()
    fox = (_base_silhouette() - _crescent_window()).clean()
    fox = fox.clean()
    assert len(fox.solids()) == 1, (
        f"{len(fox.solids())} disconnected solids: tail/body junction lost overlap"
    )
    return fox
