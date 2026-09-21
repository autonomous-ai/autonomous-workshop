from build123d import Align, Box, Cylinder, Pos, Rot
from features.forms import color_part
from params import yellow_rgb


def build():
    rings = [
        Pos(x, 0, 0) * Rot(-90, 0, 0) * Cylinder(
            4.4, 3.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ) for x in (-13.0, 13.0)
    ]
    bores = [
        Pos(x, 2.0, 0) * Rot(-90, 0, 0) * Cylinder(
            2.2, 5.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ) for x in (-13.0, 13.0)
    ]
    bridge = Pos(0, -1.4, 0) * Box(
        29.0, 2.8, 3.2, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    return color_part((bridge + rings) - bores, "sensor_insert", yellow_rgb)
