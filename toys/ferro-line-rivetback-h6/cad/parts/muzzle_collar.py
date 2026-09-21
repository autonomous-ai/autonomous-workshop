from build123d import Align, Cylinder, Pos, Rot
from features.forms import color_part
from params import yellow_rgb


def build():
    outer = Rot(-90, 0, 0) * Cylinder(11.0, 7.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    recess = Pos(0, 5.0, 0) * Rot(-90, 0, 0) * Cylinder(6.2, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return color_part(outer - recess, "muzzle_collar", yellow_rgb)
