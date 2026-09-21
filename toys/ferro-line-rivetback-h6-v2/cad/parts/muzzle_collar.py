from build123d import Align, Box, Cylinder, Pos, Rot
from features.forms import color_part
from params import yellow_rgb


def build():
    outer = Rot(-90, 0, 0) * Cylinder(11.0, 7.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    teeth = [
        Pos(0, 3.5, 0)
        * Rot(0, -angle, 0)
        * Pos(11.2, 0, 0)
        * Box(3.2, 7.0, 3.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        for angle in range(0, 360, 45)
    ]
    recess = Pos(0, 5.0, 0) * Rot(-90, 0, 0) * Cylinder(6.2, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return color_part((outer + teeth) - recess, "muzzle_collar", yellow_rgb)
