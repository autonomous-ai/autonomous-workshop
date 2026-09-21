from build123d import Align, Box, Polygon, Pos, extrude, make_face
from features.forms import clipped_prism, color_part, yz_prism
from params import *


def build(name):
    depth = plate_depths[name]
    body = clipped_prism(plate_width, depth, plate_height, 8.0)
    # Raised armor panels ramp in along Y.  Y becomes the vertical print axis,
    # so these generous transition lengths keep every underside above 45 deg.
    base_z = plate_height - 0.2
    dorsal_depth = depth - 5.0
    dorsal = yz_prism([
        (-dorsal_depth / 2, base_z),
        (-dorsal_depth / 2 + 4.5, base_z + 2.6),
        (dorsal_depth / 2 - 4.5, base_z + 2.6),
        (dorsal_depth / 2, base_z),
    ], plate_width * 0.47)
    cheek_depth = depth - 10.0
    cheeks = [Pos(x, 0, 0) * yz_prism([
        (-cheek_depth / 2, base_z),
        (-cheek_depth / 2 + 3.0, base_z + 1.6),
        (cheek_depth / 2 - 3.0, base_z + 1.6),
        (cheek_depth / 2, base_z),
    ], 18.0) for x in (-31.0, 31.0)]
    body = body + [dorsal, *cheeks]

    # Open-top trenches create readable panel breaks without unsupported roofs.
    trenches = [
        Pos(x, 0, plate_height - 0.45)
        * Box(2.0, depth - 4.0, 1.4, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        for x in (-21.5, 21.5)
    ]
    vent_recesses = [
        Pos(x, y, plate_height - 0.35)
        * Box(7.0, 2.2, 1.2, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        for x in (-31.0, 31.0)
        for y in (-depth * 0.20, depth * 0.20)
    ]
    body = body - trenches - vent_recesses
    mount_y = -depth / 2 + small_peg * 0.36
    pegs = [Pos(x, mount_y, -small_peg_length / 2) * Box(small_peg, small_peg * 0.72, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (-plate_peg_x, plate_peg_x)]
    body = body + pegs
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
