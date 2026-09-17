from build123d import Align, Box, Plane, Polygon, Pos, extrude, make_face
from features.forms import clipped_prism, color_part
from params import *


def build():
    lower = clipped_prism(hub_width, hub_depth, 11.0, 4.0)
    upper = Pos(0, 0, 11.0) * clipped_prism(20.0, hub_depth, 7.0, 3.0)
    key = Pos(0, -hub_depth / 2 + 4.0, -3.0) * Box(10.0, 8.0, 6.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    # The Y axis is vertical in the part's documented print pose.  Begin two
    # millimetres inside the pedestal, then grow from the supported 20 x 18 mm
    # upper section to the broad 28 mm crown on 45-degree ramps.  This avoids
    # both a face-touching first layer and a cantilevered top strip.
    plan = make_face(Polygon(
        (-10.0, hub_depth / 2 - 2.0),
        (10.0, hub_depth / 2 - 2.0),
        (14.0, hub_depth / 2 + 2.0),
        (14.0, hub_depth / 2 + 12.0),
        (-14.0, hub_depth / 2 + 12.0),
        (-14.0, hub_depth / 2 + 2.0),
    ))
    flared_base = extrude(plan, amount=18.0)
    roof_profile = Plane.YZ * make_face(Polygon(
        (hub_depth / 2 - 2.0, 0.0),
        (hub_depth / 2 + 12.0, 0.0),
        (hub_depth / 2 + 12.0, 21.0),
        (hub_depth / 2 + 1.0, 21.0),
        (hub_depth / 2 - 2.0, 18.0),
    ))
    ramped_roof = Pos(-10.0, 0, 0) * extrude(roof_profile, amount=20.0, dir=(1, 0, 0))
    crown_tower = flared_base + ramped_roof
    # A shallow recess at the forward face clocks the upright triplet.  It is
    # open through the print-top face, while the remaining side shoulders are
    # each 1.2 mm and the cannon land stays continuous behind it.
    sensor_recess = Pos(0, hub_depth / 2 + 10.5, 15.5) * Box(
        25.6,
        3.4,
        11.4,
        align=(Align.CENTER, Align.CENTER, Align.CENTER),
    )
    return color_part((lower + upper + key + crown_tower) - sensor_recess, "hub_pedestal", black_rgb)
