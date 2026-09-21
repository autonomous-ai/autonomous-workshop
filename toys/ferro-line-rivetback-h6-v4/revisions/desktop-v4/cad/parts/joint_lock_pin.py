from build123d import Align, Cone, Cylinder, Pos
from features.forms import color_part
from params import pin_diameter, pin_length, steel_rgb


def build():
    shaft = Cylinder(pin_diameter / 2, pin_length, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    transition = Pos(0, 0, pin_length / 2) * Cone(
        pin_diameter / 2, 4.0, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    head = Pos(0, 0, pin_length / 2 + 1.0) * Cylinder(
        4.0, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    hex_recess = Pos(0, 0, pin_length / 2 + 2.8) * Cylinder(
        2.2, 2.0, 6, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return color_part((shaft + transition + head) - hex_recess, "joint_lock_pin", steel_rgb)
