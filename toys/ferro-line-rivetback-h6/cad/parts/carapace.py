from build123d import Align, Box, Polygon, Pos, extrude, make_face
from features.forms import clipped_prism, color_part
from params import *


def build(name):
    depth = plate_depths[name]
    body = clipped_prism(plate_width, depth, plate_height, 8.0)
    ridge = Pos(0, 0, plate_height) * Box(plate_width * 0.48, depth, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    mount_y = -depth / 2 + small_peg * 0.36
    pegs = [Pos(x, mount_y, -small_peg_length / 2) * Box(small_peg, small_peg * 0.72, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (-plate_peg_x, plate_peg_x)]
    body = body + ridge + pegs
    if name == "fore":
        # The rear-open keyway admits the crown at full width, then closes on
        # two 45-degree faces in the part's Y-up print pose.  The resulting V
        # avoids a horizontal slot roof while retaining one connected plate.
        keyway = Pos(0, 0, -4.0) * extrude(make_face(Polygon(
            (-14.5, -depth / 2),
            (14.5, -depth / 2),
            (14.5, -depth / 2 + 16.0),
            (0.0, -depth / 2 + 31.0),
            (-14.5, -depth / 2 + 16.0),
        )), amount=plate_height + 8.0)
        body = body - keyway
    if name == "center":
        body = body - Pos(0, hub_center_y, plate_height / 2) * Box(31.0, 33.0, plate_height + 8.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return color_part(body, f"carapace_{name}", yellow_rgb)
