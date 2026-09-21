from build123d import Align, Cone, Cylinder, Polygon, Pos, extrude, make_face
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
    hex_points = (
        (2.2, 0.0),
        (1.1, 1.9053),
        (-1.1, 1.9053),
        (-2.2, 0.0),
        (-1.1, -1.9053),
        (1.1, -1.9053),
    )
    hex_recess = Pos(0, 0, pin_length / 2 + 2.6) * extrude(
        make_face(Polygon(*hex_points)), amount=2.0, dir=(0, 0, 1)
    )
    return color_part((shaft + transition + head) - hex_recess, "joint_lock_pin", steel_rgb)
