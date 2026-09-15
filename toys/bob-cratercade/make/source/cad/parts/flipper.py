"""One rigid capsule blade, dogleg thumb tail and return-band mushroom.

Local origin is the pivot; Z follows the deck datum. Left geometry is defined
at its rest pose. Right geometry is an exact mirror, not a second mechanism.
"""
from math import atan2, degrees, hypot
from build123d import Align, Axis, Circle, Cylinder, Plane, Polygon, Pos, extrude
import params as p


def _capsule(a, b, radius, z, height):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length = hypot(dx, dy)
    nx, ny = -dy * radius / length, dx * radius / length
    profile = Polygon((a[0]+nx, a[1]+ny), (b[0]+nx, b[1]+ny),
                      (b[0]-nx, b[1]-ny), (a[0]-nx, a[1]-ny), align=None)
    profile = profile + Pos(*a) * Circle(radius) + Pos(*b) * Circle(radius)
    return Pos(0, 0, z) * extrude(profile, amount=height, dir=(0, 0, 1))


def rotor(side="left"):
    root, tip, length = p.FLIPPER_ROOT_R, p.FLIPPER_TIP_R, p.FLIPPER_BLADE_L
    profile = Polygon((0, root), (length, tip), (length, -tip), (0, -root), align=None)
    profile = profile + Circle(root) + Pos(length, 0) * Circle(tip)
    blade = Pos(0, 0, p.FLIPPER_ROTOR_Z) * extrude(profile, amount=p.FLIPPER_ROTOR_T, dir=(0, 0, 1))
    blade = blade.rotate(Axis.Z, p.FLIPPER_BLADE_REST)
    shape = blade + _capsule((0, 0), p.FLIPPER_TAIL_JOINT, p.FLIPPER_TAIL_R,
                             p.FLIPPER_ROTOR_Z, p.FLIPPER_ROTOR_T)
    shape += _capsule(p.FLIPPER_TAIL_JOINT, p.FLIPPER_THUMB, p.FLIPPER_TAIL_R,
                      p.FLIPPER_ROTOR_Z, p.FLIPPER_ROTOR_T)
    shape += Pos(*p.FLIPPER_THUMB, p.FLIPPER_ROTOR_Z) * Cylinder(
        p.FLIPPER_THUMB_R, p.FLIPPER_ROTOR_T + p.FLIPPER_THUMB_EXTRA,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    for x in p.FLIPPER_TEXTURE_X:
        shape += Pos(p.FLIPPER_THUMB[0] + x, p.FLIPPER_THUMB[1],
                     p.FLIPPER_ROTOR_Z + p.FLIPPER_ROTOR_T + p.FLIPPER_THUMB_EXTRA) * Cylinder(
            p.FLIPPER_TEXTURE_R, p.FLIPPER_TEXTURE_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape += Pos(*p.FLIPPER_TAIL_JOINT, p.FLIPPER_POST_NECK_Z) * Cylinder(
        p.FLIPPER_POST_R, p.FLIPPER_POST_NECK_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape += Pos(*p.FLIPPER_TAIL_JOINT, p.FLIPPER_POST_NECK_Z + p.FLIPPER_POST_NECK_H) * Cylinder(
        p.FLIPPER_POST_CAP_R, p.FLIPPER_POST_CAP_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    shape -= Pos(0, 0, p.FLIPPER_ROTOR_Z - p.FLIPPER_CUT_MARGIN) * Cylinder(
        p.FLIPPER_ROTOR_BORE / 2, p.FLIPPER_ROTOR_T + 2*p.FLIPPER_CUT_MARGIN,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    if side == "right":
        shape = shape.mirror(Plane.YZ)
    assert len(shape.solids()) == 1, "Rotor must be one load-carrying solid"
    shape.label = f"flipper_{side}_rotor"
    return shape


def print_rotor(side="left"):
    return Pos(0, 0, -p.FLIPPER_ROTOR_Z) * rotor(side)
