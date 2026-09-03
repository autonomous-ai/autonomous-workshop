"""Parametric Pearlturn geometry. All dimensions are millimetres."""
from math import cos, radians, sin
from build123d import Align, Box, Cylinder, Axis, Location, Vector, Compound

# Envelope and print constants.
SHELL_W = 92.0
SHELL_D = 30.0
SHELL_H = 42.0
LIP_T = 9.0
REAR_WEB_W = 14.0
PEARL_D = 24.0
PEARL_R = PEARL_D / 2.0
PEARL_LEN = 22.0
AXIAL_CLEARANCE = (SHELL_D - PEARL_LEN) / 2.0
POCKET_R = 12.7
# Keep the rear pocket cut clear of the structural spine by more than two
# nozzle widths; this removes the otherwise knife-thin crescent at the web.
POCKET_X = 16.0
POCKET_Z = 17.5
LOW_PEARL_X = 16.0
# The drum bottoms on the pocket, rather than the flat lower rail.
LOW_PEARL_Z = POCKET_Z - POCKET_R + PEARL_R
VAULT_DEG = 65.0


def _rounded_box(length, width, height, at):
    shape = Box(length, width, height, align=(Align.MIN, Align.MIN, Align.MIN))
    shape = Location(Vector(*at)) * shape
    try:
        shape = shape.fillet(1.6, shape.edges())
    except Exception:
        pass
    return shape


def build_shell():
    """One rigid open-mouth clam body in its low print/model pose."""
    # Keep the load-bearing lower rail square: rounding its underside where a
    # circular saddle opens above it creates a microscopic tangent crescent.
    lower = Box(SHELL_W, SHELL_D, LIP_T, align=(Align.MIN, Align.MIN, Align.MIN))
    lower = Location(Vector(-SHELL_W/2, -SHELL_D/2, 0)) * lower
    upper = _rounded_box(SHELL_W - 8, SHELL_D, LIP_T, (-SHELL_W/2 + 4, -SHELL_D/2, SHELL_H - LIP_T))
    rear = _rounded_box(REAR_WEB_W, SHELL_D, SHELL_H - 8, (-SHELL_W/2, -SHELL_D/2, 4))
    body = lower.fuse(upper).fuse(rear)

    # Open terminal saddles remain exposed through the full depth.
    for cx in (-POCKET_X, POCKET_X):
        cutter = Cylinder(POCKET_R, SHELL_D + 4).rotate(Axis.X, -90)
        cutter = Location(Vector(cx, -SHELL_D/2 - 2, POCKET_Z)) * cutter
        body = body.cut(cutter)

    assert len(body.solids()) == 1
    return body


def build_pearl():
    pearl = Cylinder(PEARL_R, PEARL_LEN).rotate(Axis.X, -90)
    pearl = Location(Vector(LOW_PEARL_X, -PEARL_LEN/2, LOW_PEARL_Z)) * pearl
    try:
        pearl = pearl.fillet(1.5, pearl.edges())
    except Exception:
        pass
    assert len(pearl.solids()) == 1
    return pearl


def build_assembly(shell_angle=0.0):
    shell = build_shell()
    if shell_angle:
        # Rotate the clam, then translate its opposite (left) open saddle onto
        # the loose drum.  This is the exact second stable endpoint: the shell
        # has vaulted 65 degrees while the pearl has transferred lips.
        shell = shell.rotate(Axis.Y, shell_angle)
        a = radians(shell_angle)
        pocket_x = -POCKET_X * cos(a) + POCKET_Z * sin(a)
        pocket_z = POCKET_X * sin(a) + POCKET_Z * cos(a)
        shell = Location(Vector(LOW_PEARL_X - pocket_x, 0,
                                LOW_PEARL_Z - pocket_z)) * shell
    pearl = build_pearl()
    assembly = Compound(children=[shell, pearl])
    # Ground the complete state without changing the shell/pearl relationship.
    min_z = assembly.bounding_box().min.Z
    if min_z < 0:
        assembly = Location(Vector(0, 0, -min_z)) * assembly
    return assembly


def validate_parameters():
    assert SHELL_W == 92.0 and SHELL_D == 30.0
    assert PEARL_D == 24.0 and PEARL_LEN == 22.0
    assert AXIAL_CLEARANCE == 4.0
    assert abs((POCKET_R - PEARL_R) - 0.7) < 1e-9
    assert LIP_T >= 3.2 and REAR_WEB_W >= 8.0
    assert VAULT_DEG == 65.0

validate_parameters()
