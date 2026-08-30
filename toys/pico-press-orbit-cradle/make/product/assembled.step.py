"""Parametric one-piece Orbit Cradle rocking moon."""

from math import cos, pi, sin

from build123d import Face, Location, Vector, Wire, extrude


OUTER_RADIUS = 42.0
INNER_RADIUS = 31.0
INNER_OFFSET_X = 14.0
DEPTH = 18.0
STAR_CENTER = (7.0, -1.0)
STAR_OUTER_RADIUS = 10.5
STAR_INNER_RADIUS = 4.8
BRIDGE_WIDTH = 4.2
HORN_PAD_RADIUS = 4.0


def _star_face() -> Face:
    """Build a smooth five-lobed star with no sub-nozzle knife points."""
    points = []
    for index in range(100):
        angle = 2.0 * pi * index / 100.0
        lobe = (1.0 + sin(5.0 * angle)) / 2.0
        radius = STAR_INNER_RADIUS + (
            STAR_OUTER_RADIUS - STAR_INNER_RADIUS
        ) * lobe**3
        points.append(
            Vector(
                STAR_CENTER[0] + radius * cos(angle),
                STAR_CENTER[1] + radius * sin(angle),
            )
        )
    return Face(Wire.make_polygon(points, close=True))


def gen_step():
    outer = Face(Wire.make_circle(OUTER_RADIUS))
    inner = Face(
        Wire.make_circle(INNER_RADIUS).moved(Location((INNER_OFFSET_X, 0, 0)))
    )
    crescent_face = outer - inner
    moon = extrude(crescent_face, amount=DEPTH)

    # The two mathematical circle intersections would taper to zero. Rounded
    # horn pads preserve the crescent read while keeping each end printable.
    horn_x = (
        OUTER_RADIUS**2 - INNER_RADIUS**2 + INNER_OFFSET_X**2
    ) / (2.0 * INNER_OFFSET_X)
    horn_y = (OUTER_RADIUS**2 - horn_x**2) ** 0.5
    for y_position in (-horn_y, horn_y):
        horn_face = Face(
            Wire.make_circle(HORN_PAD_RADIUS).moved(
                Location((horn_x, y_position, 0))
            )
        )
        moon = moon.fuse(extrude(horn_face, amount=DEPTH))

    star = extrude(_star_face(), amount=DEPTH)
    # A broad, visibly deliberate beam joins the star's left valley to the
    # crescent's inner wall. It overlaps both solids for one continuous body.
    from build123d import Box
    bridge = Box(20.0, BRIDGE_WIDTH, DEPTH).moved(
        Location((-9.5, STAR_CENTER[1], DEPTH / 2.0))
    )
    body = moon.fuse(star, bridge)

    body.label = "orbit_cradle_one_piece"
    assert len(body.solids()) == 1, "Orbit Cradle must remain one fused solid"
    return body
