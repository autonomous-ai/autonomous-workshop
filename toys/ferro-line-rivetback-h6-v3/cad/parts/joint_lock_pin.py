from build123d import Align, Box, Cylinder, Pos
from features.forms import color_part
from params import black_rgb, pin_diameter, pin_length


def build():
    shaft = Cylinder(pin_diameter / 2, pin_length, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    head = Pos(0, 0, pin_length / 2 + 1.0) * Box(8.0, 6.0, 2.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return color_part(shaft + head, "joint_lock_pin", black_rgb)
