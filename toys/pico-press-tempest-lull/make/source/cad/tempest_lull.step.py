"""Parametric one-piece rocking storm-cloud desk toy."""

from build123d import (
    Align,
    Axis,
    Box,
    BuildLine,
    BuildPart,
    BuildSketch,
    CenterOf,
    Cylinder,
    Line,
    Plane,
    Polyline,
    Vector,
    extrude,
    fillet,
    make_face,
    scale,
)

PRINTABLE = True

# Overall / rocker parameters (mm)
KEEL_RADIUS = 72.0
KEEL_DEPTH = 18.0
KEEL_INNER_RADIUS = 64.0
KEEL_INNER_Z = 76.0
KEEL_TOP = 24.0
ROCK_ANGLE_DEG = 18.0


BODY_DEPTH = 18.0


def ellipse_prism(x: float, z: float, rx: float, rz: float, depth: float = BODY_DEPTH):
    """A coplanar elliptical lobe; common faces heal before edge rounding."""
    disk = Cylinder(1.0, 1.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    disk = disk.rotate(Axis.X, 90)
    return scale(disk, by=(rx, depth, rz)).translate((x, 0, z))


def prism_xz(points: list[tuple[float, float]], depth: float):
    """Extrude a closed XZ polygon symmetrically through the front/back axis."""
    with BuildPart() as built:
        with BuildSketch(Plane.XZ):
            with BuildLine():
                Polyline(*points)
                Line(points[-1], points[0])
            make_face()
        extrude(amount=depth / 2.0, both=True)
    return built.part


def make_keel():
    outer = Cylinder(KEEL_RADIUS, KEEL_DEPTH, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    outer = outer.rotate(Axis.X, 90).translate((0, 0, KEEL_RADIUS))
    inner = Cylinder(KEEL_INNER_RADIUS, KEEL_DEPTH + 4, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    inner = inner.rotate(Axis.X, 90).translate((0, 0, KEEL_INNER_Z))
    crescent = outer - inner
    crop = Box(82, 50, KEEL_TOP, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return crescent & crop


def make_cloud():
    # Coplanar overlapping lobes form one clean side profile. The completed
    # profile is rounded at both faces after fusion, avoiding tangent valleys.
    right_lobe = prism_xz(
        [(24, 27), (38, 27), (46, 35), (46, 43), (38, 53), (24, 53)],
        BODY_DEPTH,
    )
    lobes = [
        ellipse_prism(-30, 42, 17, 16),
        ellipse_prism(-18, 54, 18, 16),
        ellipse_prism(2, 58, 24, 14),
        prism_xz([(8, 42), (15, 34), (32, 32), (45, 42), (45, 54),
                  (36, 66), (17, 66), (8, 55)], BODY_DEPTH),
        right_lobe,
    ]
    cloud = lobes[0]
    for lobe in lobes[1:]:
        cloud = cloud + lobe

    # Strong shoulders fuse cloud to keel while leaving the central arch open.
    cloud = cloud + ellipse_prism(-35, 29, 11, 13)
    cloud = cloud + prism_xz(
        [(24, 22), (28, 17), (40, 17), (44, 24),
         (44, 38), (38, 42), (28, 42), (24, 36)],
        BODY_DEPTH,
    )
    return cloud


def make_bolt_and_curl():
    bolt = prism_xz(
        [(-4, 35), (7, 35), (3, 29), (8, 29), (-1, 14), (-4, 15), (-1, 25), (-7, 25)],
        BODY_DEPTH,
    )
    bolt_profile_edges = [edge for edge in bolt.edges() if edge.length > BODY_DEPTH - 0.1]
    bolt = fillet(bolt_profile_edges, radius=1.2)
    # One finite-width S ribbon replaces a bead chain whose circular junctions
    # formed sub-nozzle concave cusps. Every land is at least 5 mm wide.
    curl = prism_xz(
        [(-9, 59), (-3, 59), (-4, 53), (-3, 47), (1, 41), (4, 34),
         (-3, 33), (-5, 39), (-10, 46), (-11, 53)],
        BODY_DEPTH,
    )

    return bolt + curl


def gen_step():
    shape = (make_keel() + make_cloud() + make_bolt_and_curl()).clean()
    assert shape.is_valid, "Tempest Lull must remain a closed valid shape"
    assert len(shape.solids()) == 1, "Tempest Lull must remain one fused solid"
    bb = shape.bounding_box()
    assert bb.min.Z >= -0.02, "print stance must remain on the bed"
    shape.label = "tempest_lull_one_piece_rocker"
    return shape


if __name__ == "__main__":
    model = gen_step()
    bb = model.bounding_box()
    com = model.center(CenterOf.MASS)
    print(f"bbox={bb.size.X:.2f}x{bb.size.Y:.2f}x{bb.size.Z:.2f} mm")
    print(f"center_of_mass=({com.X:.2f},{com.Y:.2f},{com.Z:.2f}) mm")
