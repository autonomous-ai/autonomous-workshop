from build123d import Align, Box, Cylinder, Pos, Rot
from features.forms import color_part
from params import yellow_rgb


def build():
    outer = Rot(-90, 0, 0) * Cylinder(9.5, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    teeth = [
        Pos(0, 3.0, 0)
        * Rot(0, -angle, 0)
        * Pos(9.7, 0, 0)
        * Box(2.8, 6.0, 2.6, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        for angle in range(0, 360, 45)
    ]
    recess = Pos(0, 4.0, 0) * Rot(-90, 0, 0) * Cylinder(5.5, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return color_part((outer + teeth) - recess, "muzzle_collar", yellow_rgb)
