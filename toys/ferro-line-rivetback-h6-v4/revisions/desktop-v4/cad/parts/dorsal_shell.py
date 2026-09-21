from build123d import Align, Box, Polygon, Pos, extrude, make_face

from features.forms import color_part, yz_prism
from params import dorsal_key, dorsal_socket, plate_depths, yellow_rgb


def build(name):
    depth = plate_depths[name]
    if name == "fore":
        profile = [
            (-depth / 2 + 1.0, 0.0), (-depth / 2 + 1.0, 4.0), (-11.0, 6.0),
            (-2.0, 15.0), (5.0, 16.0), (14.0, 8.0),
            (depth / 2 + 4.0, 2.0), (depth / 2 + 4.0, 0.0),
        ]
        width = 44.0
        footprint = [
            (-16.0, -depth / 2 + 1.0), (16.0, -depth / 2 + 1.0),
            (22.0, -10.0), (22.0, 11.0), (14.0, 17.0),
            (5.0, depth / 2 + 4.0), (-5.0, depth / 2 + 4.0),
            (-14.0, 17.0), (-22.0, 11.0), (-22.0, -10.0),
        ]
    elif name == "center":
        profile = [
            (-depth / 2 + 1.0, 0.0), (-depth / 2 + 1.0, 4.0), (-5.0, 8.0),
            (3.0, 16.0), (7.0, 16.0),
            (depth / 2 - 1.0, 2.0), (depth / 2 - 1.0, 0.0),
        ]
        width = 48.0
        footprint = [
            (-18.0, -depth / 2 + 1.0), (18.0, -depth / 2 + 1.0),
            (24.0, -7.0), (24.0, 7.0), (18.0, depth / 2 - 1.0),
            (-18.0, depth / 2 - 1.0), (-24.0, 7.0), (-24.0, -7.0),
        ]
    else:
        profile = [
            (-depth / 2 + 1.0, 0.0), (-depth / 2 + 1.0, 4.0), (-9.0, 5.0),
            (-3.0, 11.0), (2.0, 15.0), (8.0, 15.0),
            (depth / 2 - 1.0, 2.0), (depth / 2 - 1.0, 0.0),
        ]
        width = 42.0
        footprint = [
            (-15.0, -depth / 2 + 1.0), (15.0, -depth / 2 + 1.0),
            (21.0, -8.0), (21.0, 9.0), (14.0, depth / 2 - 1.0),
            (-14.0, depth / 2 - 1.0), (-21.0, 9.0), (-21.0, -8.0),
        ]

    shell = yz_prism(profile, width)
    plan_mask = extrude(make_face(Polygon(*footprint)), amount=40.0)
    shell = shell & plan_mask
    # The downward-open socket lets this secondary armor print on its broad,
    # flat underside while the matching peg grows from the base plate's bed edge.
    key_center_y = -depth / 2 + dorsal_key / 2
    socket = Pos(0, key_center_y, 1.05) * Box(
        dorsal_socket, dorsal_socket, 2.1,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    shell = shell - socket

    if name == "aft":
        blades = [Pos(x, 0, 0) * yz_prism([
            (-depth / 2 + 1.0, 2.0),
            (depth / 2 - 2.0, 2.0),
            (depth / 2 - 4.0, 2.0 + height),
            (depth / 2 - 5.5, 2.0 + height),
        ], 2.4) for x, height in ((-10.0, 20.0), (10.0, 23.0))]
        shell = shell + blades

    return color_part(shell, f"dorsal_{name}", yellow_rgb)
