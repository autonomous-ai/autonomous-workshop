"""Parametric one-piece Mooncoil Dragon talisman, millimetres."""

from build123d import BuildLine, BuildSketch, Cylinder, Box, Plane, Polyline, Line, extrude, make_face

PRINTABLE = True
DEPTH = 16.0


def _prism(points, depth=DEPTH):
    with BuildSketch(Plane.XY) as sketch:
        with BuildLine():
            Polyline(*points)
            Line(points[-1], points[0])
        make_face()
    face = sketch.sketch.faces()[0]
    # Fillet feasible corners independently: some tightly concave boolean
    # junctions cannot accept the radius, while the exposed acute tips can.
    for x, y in points:
        vertex = min(face.vertices(), key=lambda v: (v.X - x) ** 2 + (v.Y - y) ** 2)
        try:
            face = face.fillet_2d(0.6, [vertex])
        except Exception:
            pass
    return extrude(face, amount=depth)


def gen_step():
    # Clockwise outer silhouette. Two support facets are the long lower edge and
    # the lower-right diagonal; the intervening contour is the rocking cam.
    outline = [
        (-45, -29), (-13, -29), (1, -27), (14, -22), (25, -14),
        (34, -3), (41, 10), (45, 24), (41, 35),
        # lowered dragon head, horn and blunt snout
        (34, 39), (31.5, 43.8), (29, 42), (22, 45), (24, 36),
        (34, 32), (37, 27), (33, 23), (25, 22), (20, 18),
        # back of neck into three large sleeping-dragon spines
        (14, 26), (8, 34), (2, 43), (-3, 35), (-11.3, 44.2), (-12.1, 44.8), (-12.7, 44.0),
        (-14, 34), (-24.2, 40.3), (-25.0, 40.6), (-25.2, 39.7), (-24, 31),
        (-35.2, 33.3), (-36.0, 33.6), (-36.2, 32.7), (-32, 25),
        (-43, 21), (-37, 14), (-48, 7), (-40, 1), (-49.2, -7.3), (-49.3, -8.2), (-48.4, -8.3),
        (-39, -12), (-48, -20)
    ]
    body = _prism(outline)

    # Crescent aperture: subtract the large disk and restore an offset inner
    # disk. Its axis is deliberately diagonal in dragon pose.
    # Keep the cut a full millimetre inside the spine at (-3, 35); exact
    # tangency there would create a zero-width, non-manifold printable edge.
    moon_cut = Cylinder(30.0, DEPTH + 2).translate((-3, 4, DEPTH / 2))
    moon_fill = Cylinder(18.0, DEPTH).translate((11, 12, DEPTH / 2))
    moon_bridge = Box(16, 10, DEPTH).translate((28, 14, DEPTH / 2))
    spine_bridge = Box(14, 14, DEPTH).translate((6, 31, DEPTH / 2))
    shape = body - moon_cut + moon_fill + moon_bridge + spine_bridge

    # Broad folded-wing shoulder, attached to the restored inner moon mass.
    wing = _prism([(-18, 5), (-2, 26), (12, 20), (1, 7), (11, -6), (-5, -2)])
    shape = shape + wing

    # Castle rises from a broad plinth that crosses the lower moon boundary.
    plinth = Box(40, 12, DEPTH).translate((-3, -23, DEPTH / 2))
    castle_root = Box(9, 22, DEPTH).translate((-7, -26, DEPTH / 2))
    keep = Box(9, 18, DEPTH).translate((-7, -18, DEPTH / 2))
    left_tower = Box(7, 13, DEPTH).translate((-16, -18, DEPTH / 2))
    right_tower = Box(7, 13, DEPTH).translate((5, -18, DEPTH / 2))
    roof_l = _prism([(-18, -13), (-13.0, -6.6), (-12.0, -6.6), (-7, -13)])
    roof_k = _prism([(-8, -10), (-3.0, -2.7), (-2.0, -2.7), (3, -10)])
    roof_r = _prism([(3, -13), (8.0, -6.6), (9.0, -6.6), (14, -13)])
    shape = shape + plinth + castle_root + keep + left_tower + right_tower + roof_l + roof_k + roof_r

    assert len(shape.solids()) == 1, "The talisman must remain one printable solid"
    return shape
