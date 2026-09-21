from build123d import Align, Box, Polygon, Pos, extrude, make_face
from features.forms import color_part
from params import *


def build(name):
    depth = plate_depths[name]
    if name == "fore":
        plan = make_face(Polygon(
            (-22.0, -depth / 2), (22.0, -depth / 2),
            (30.0, -10.0), (31.0, -2.0), (26.0, 7.0),
            (15.0, 14.0), (5.0, depth / 2 + 2.0), (0.0, depth / 2 + 8.0),
            (-5.0, depth / 2 + 2.0), (-15.0, 14.0), (-26.0, 7.0),
            (-31.0, -2.0), (-30.0, -10.0),
        ))
    elif name == "center":
        plan = make_face(Polygon(
            (-25.0, -depth / 2), (25.0, -depth / 2),
            (31.0, -7.0), (32.0, 5.0), (24.0, depth / 2),
            (-24.0, depth / 2), (-32.0, 5.0), (-31.0, -7.0),
        ))
    else:
        plan = make_face(Polygon(
            (-17.0, -depth / 2), (17.0, -depth / 2),
            (23.0, -9.0), (27.0, 1.0), (25.0, depth / 2),
            (-25.0, depth / 2), (-27.0, 1.0), (-23.0, -9.0),
        ))
    body = extrude(plan, amount=plate_height + 1.0)

    panel_slots = [
        Pos(x, -1.0, plate_height - 0.5) * Box(
            1.8, max(10.0, depth - 12.0), 1.0,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ) for x in (-12.5, 12.5)
    ]
    dorsal_mount_y = -depth / 2 + dorsal_key / 2
    dorsal_peg = Pos(0, dorsal_mount_y, plate_height + 0.8) * Box(
        dorsal_key, dorsal_key, 1.8,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    body = body - panel_slots
    mount_y = -depth / 2 + small_peg * 0.36
    pegs = [Pos(x, mount_y, -small_peg_length / 2) * Box(small_peg, small_peg * 0.72, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (-plate_peg_x, plate_peg_x)]
    body = body + pegs + dorsal_peg
    return color_part(body, f"carapace_{name}", yellow_rgb)
