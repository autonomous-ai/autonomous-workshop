"""Small robust primitives; all dimensions are supplied by callers."""

from build123d import Align, Box, Circle, Color, Cylinder, Plane, Polygon, Pos, Rot, make_face, extrude


def color_part(shape, label, rgb):
    shape.label = label
    shape.color = Color(*rgb)
    return shape


def bed_on_z(shape, rotation=(0.0, 0.0, 0.0)):
    oriented = Rot(*rotation) * shape
    z_min = oriented.bounding_box().min.Z
    return Pos(0, 0, -z_min) * oriented


def clipped_prism(width, depth, height, cut):
    points = [
        (-width / 2 + cut, -depth / 2),
        (width / 2 - cut, -depth / 2),
        (width / 2, -depth / 2 + cut),
        (width / 2, depth / 2 - cut),
        (width / 2 - cut, depth / 2),
        (-width / 2 + cut, depth / 2),
        (-width / 2, depth / 2 - cut),
        (-width / 2, -depth / 2 + cut),
    ]
    return extrude(make_face(Polygon(*points)), amount=height)


def xz_prism(points, width):
    profile = Plane.XZ * make_face(Polygon(*points))
    return Pos(0, -width / 2, 0) * extrude(profile, amount=width, dir=(0, 1, 0))


def keyed_box_peg(length, width, height):
    # A non-square rectangular section is intrinsically keyed.  Keeping the
    # tenon monolithic avoids the nozzle-width knife edge created by a small
    # tangential fin while still preventing a 90-degree assembly mistake.
    return Box(length, width, height, align=(Align.MIN, Align.CENTER, Align.CENTER))


def flat_crescent(outer_radius, inner_radius, thickness):
    ring = make_face(Circle(outer_radius)) - make_face(Circle(inner_radius))
    clip = Pos(outer_radius * 0.45, 0, 0) * Box(
        outer_radius * 1.15,
        outer_radius * 1.65,
        thickness,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return extrude(ring, amount=thickness) & clip
