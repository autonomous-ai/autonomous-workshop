"""Custom Microduck torsion drivetrain; dimensions mm, assembly coordinates.

The root frame must use these cutters and positively fix the separate anchor.
Bonded keys/pins are permanent structure; bearing fits remain unbonded.
"""
from build123d import Box, Cylinder, Cone, Plane, Pos, Rot
import cadfits

DRIVE_Y, DRIVE_Z = -6.0, 10.0
REAR_Y, REAR_Z = 12.0, 6.0
AXLE_D, BAND_BORE_D = 8.4, 5.4
BEARING_D = cadfits.slot_for(AXLE_D, "slip")
KEY_FLAT_RADIUS = 3.9
KEY_FLAT_SOCKET = KEY_FLAT_RADIUS + cadfits.mating_clearance("snug")
BONDED_WHEEL_BORE_D = cadfits.slot_for(AXLE_D, "snug")
PIN_D = 3.2
ROLLER_BORE_D = cadfits.slot_for(PIN_D, "slip")
PIN_SOCKET_D = cadfits.slot_for(PIN_D, "snug")
AXIAL_GAP = cadfits.mating_clearance("slip") * 2
CORD_D = 4.0
CORD_WORKING_SPAN = 81.2
MAX_WINDING_TURNS = 2.0


def x_cylinder(radius, x0, x1, y=DRIVE_Y, z=DRIVE_Z):
    return Pos((x0+x1)/2, y, z) * Rot(0, 90, 0) * Cylinder(radius, x1-x0)


def _finish(shape, label):
    assert len(shape.solids()) == 1, (label, len(shape.solids()))
    shape.label = label
    return shape


def build_rotor():
    """Right wheel, hollow D-keyed shaft and winding knob: one solid."""
    rotor = x_cylinder(AXLE_D/2, -34.7, 42)
    rotor += x_cylinder(10, 29, 35)
    rotor += x_cylinder(8, 38, 42)
    # Outer print transition: radius10 at X35 to radius8 at X38.
    rotor += Pos(36.5, DRIVE_Y, DRIVE_Z)*Rot(0,90,0)*Cone(10,8,3)
    # Negative D-flat permits the shaft to slide through closed frame bores.
    rotor -= Pos(-33, DRIVE_Y+KEY_FLAT_RADIUS+3, DRIVE_Z) * Box(10, 6, 12)
    rotor -= x_cylinder(BAND_BORE_D/2, -39, 45)
    # Expand to a finger-accessible cleat at the outer knob face. Inner
    # 45-degree taper prints inward from the broad bed-side opening.
    rotor -= Pos(34.65,DRIVE_Y,DRIVE_Z)*Rot(0,90,0)*Cone(2.7,6,3.3)
    rotor -= x_cylinder(6,36.3,45)
    rotor += Pos(41, DRIVE_Y, DRIVE_Z) * Box(2, 12.2, 2.4)
    return _finish(rotor, "rotor_right_wheel_winding_knob")


def build_left_drive_wheel():
    wheel = x_cylinder(10, -35, -29)
    socket = x_cylinder(BONDED_WHEEL_BORE_D/2, -36, -28)
    socket -= Pos(-32, DRIVE_Y+KEY_FLAT_SOCKET+3, DRIVE_Z) * Box(10,6,12)
    wheel -= socket
    return _finish(wheel, "left_drive_wheel_bonded_key")


def build_rear_roller(side=1):
    """side=+1 right; side=-1 left. Four-mm wide roller, free bore."""
    roller = x_cylinder(6, 30, 34, REAR_Y, REAR_Z)
    roller -= x_cylinder(ROLLER_BORE_D/2, 29, 35, REAR_Y, REAR_Z)
    if side < 0:
        roller = roller.mirror(Plane.YZ)
    return _finish(roller, "rear_roller_" + ("right" if side>0 else "left"))


def build_rear_pin(side=1):
    """Printed headed pin: bond inner x25..29.6 into frame, keep bore dry."""
    pin = x_cylinder(PIN_D/2, 25, 34+AXIAL_GAP, REAR_Y, REAR_Z)
    pin += x_cylinder(3, 34+AXIAL_GAP, 36+AXIAL_GAP, REAR_Y, REAR_Z)
    if side < 0:
        pin = pin.mirror(Plane.YZ)
    return _finish(pin, "rear_pin_bonded_" + ("right" if side>0 else "left"))


def build_fixed_anchor():
    """External thin lacing eye; upper tab uses a matching 2.2×4.2×8.2 bonded socket."""
    # Two 4.7 mm-high lacing windows accept a single 4 mm cord. The ring
    # avoids a central stem obstructing the wrap; rounded circular outside.
    anchor = x_cylinder(7, -41.2, -39.2, DRIVE_Y, 7.5)
    anchor -= x_cylinder(5.7, -42.2, -38.2, DRIVE_Y, 7.5)
    anchor += Pos(-40.2,DRIVE_Y,7.5)*Box(2,11.6,2)
    anchor += Pos(-40.2,DRIVE_Y,17)*Box(2,4,8)
    return _finish(anchor, "fixed_elastic_anchor_with_bonded_tab")


def drive_frame_cutters():
    """Full revolved envelope, safe at all phases; subtract from solid frame.

    Bearing sleeves end at x+/-28.6; inner wheel faces at +/-29 retain the
    shaft with 0.4mm clearance per end after the left D-key wheel is bonded.
    """
    cutters = x_cylinder(BEARING_D/2, -46, 43)
    # Remove frame from the inner unsupported axle span if desired: using the
    # same diameter throughout preserves the insertion corridor.
    for a,b in ((-70,-28.6),(28.6,70)):
        cutters += x_cylinder(10.4, a, b)
    cutters += x_cylinder(8.4, 37.6, 42.4)
    return cutters


def rear_pin_socket(side=1):
    cutter = x_cylinder(PIN_SOCKET_D/2, 24.6, 29.6, REAR_Y, REAR_Z)
    return cutter if side>0 else cutter.mirror(Plane.YZ)


def rear_wheel_clearance(side=1):
    cutter = x_cylinder(6.4, 29.6, 70, REAR_Y, REAR_Z)
    cutter += x_cylinder(3.4, 34.4, 36.8, REAR_Y, REAR_Z)
    return cutter if side>0 else cutter.mirror(Plane.YZ)


def anchor_tab_socket():
    return Pos(-40.2, DRIVE_Y, 17) * Box(cadfits.slot_for(2,"snug"), cadfits.slot_for(4,"snug"), cadfits.slot_for(8,"snug"))


def print_pose(shape, right_end_down=True):
    """Axial parts upright; translate exact rotated bounds onto build plate.

    Right end down supports rotor's knob and wheel first. Anchor should instead
    be printed with its x=-41.2 planar side down (right_end_down=False).
    """
    result = Rot(0, 90 if right_end_down else -90, 0) * shape
    bb = result.bounding_box()
    return Pos(-(bb.min.X+bb.max.X)/2, -(bb.min.Y+bb.max.Y)/2, -bb.min.Z) * result
