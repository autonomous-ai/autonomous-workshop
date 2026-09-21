from build123d import Align, Box, Polygon, Pos, extrude, make_face
from features.forms import clipped_prism, color_part, yz_prism
from params import *


def build(name):
    depth = plate_depths[name]
    if name == "fore":
        plan = make_face(Polygon(
            (-30.0, -depth / 2), (30.0, -depth / 2),
            (32.0, 5.0), (23.0, depth / 2), (17.0, depth / 2),
            (17.0, -6.0), (-17.0, -6.0),
            (-17.0, depth / 2), (-23.0, depth / 2), (-32.0, 5.0),
        ))
    elif name == "center":
        plan = make_face(Polygon(
            (-24.0, -depth / 2), (24.0, -depth / 2),
            (30.0, -5.0), (30.0, 7.0), (20.0, depth / 2),
            (-20.0, depth / 2), (-30.0, 7.0), (-30.0, -5.0),
        ))
    else:
        plan = make_face(Polygon(
            (-17.0, -depth / 2), (17.0, -depth / 2),
            (25.0, -3.0), (26.0, depth / 2),
            (-26.0, depth / 2), (-25.0, -3.0),
        ))
    body = extrude(plan, amount=plate_height)

    # Raised center spine uses print-safe ramps along local Y.
    base_z = plate_height - 0.2
    dorsal_depth = depth - 3.0
    dorsal_width = 24.0 if name == "aft" else 20.0
    dorsal_height = 3.2 if name == "aft" else 2.2
    dorsal = yz_prism([
        (-dorsal_depth / 2, base_z),
        (-dorsal_depth / 2 + 4.5, base_z + dorsal_height),
        (dorsal_depth / 2 - 4.5, base_z + dorsal_height),
        (dorsal_depth / 2, base_z),
    ], dorsal_width)
    if name != "fore":
        body = body + dorsal

    # Twin swept dorsal blades reproduce the reference's insect-like crown.
    if name == "aft":
        blades = [Pos(x, 0, 0) * yz_prism([
            (-depth / 2 + 1.0, base_z),
            (depth / 2 - 2.0, base_z),
            (depth / 2 - 4.0, base_z + height),
            (depth / 2 - 5.5, base_z + height),
        ], 2.6) for x, height in ((-8.0, 16.0), (8.0, 19.0))]
        body = body + blades

    panel_slots = [
        Pos(x, -1.0, plate_height - 0.5) * Box(
            1.8, depth - 8.0, 1.4,
            align=(Align.CENTER, Align.CENTER, Align.CENTER),
        ) for x in (-12.5, 12.5)
    ]
    body = body - panel_slots
    mount_y = -depth / 2 + small_peg * 0.36
    pegs = [Pos(x, mount_y, -small_peg_length / 2) * Box(small_peg, small_peg * 0.72, small_peg_length, align=(Align.CENTER, Align.CENTER, Align.CENTER)) for x in (-plate_peg_x, plate_peg_x)]
    body = body + pegs
    return color_part(body, f"carapace_{name}", yellow_rgb)
