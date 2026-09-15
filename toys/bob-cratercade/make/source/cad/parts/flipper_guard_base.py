"""Deck-rooted local band tray and exact tangent hard stops."""
from math import cos, hypot, radians, sin
from build123d import Align, Axis, Cylinder, Plane, Polygon, Pos, extrude
import params as p
from parts.apron_shell import floor_profile,_extrude


def rotate_xy(point, angle):
    c, s = cos(radians(angle)), sin(radians(angle))
    return (point[0]*c-point[1]*s, point[0]*s+point[1]*c)


def stop_centers():
    a, b = p.FLIPPER_TAIL_JOINT, p.FLIPPER_THUMB
    dx, dy = b[0]-a[0], b[1]-a[1]
    scale = (p.FLIPPER_TAIL_R+p.FLIPPER_STOP_R) / hypot(dx, dy)
    nx, ny = -dy*scale, dx*scale
    point = p.FLIPPER_STOP_TAIL_STATION
    return ((point[0]-nx, point[1]-ny),
            rotate_xy((point[0]+nx, point[1]+ny), p.FLIPPER_TRAVEL))


def guard_base(side="left"):
    outline = p.FLIPPER_RIGHT_GUARD_OUTLINE if side == "right" else p.FLIPPER_GUARD_OUTLINE
    mounts = p.FLIPPER_RIGHT_GUARD_MOUNTS if side == "right" else p.FLIPPER_GUARD_MOUNTS
    px,py=p.FLIPPER_PIVOTS[side]
    shape=Pos(-px,-py,0)*_extrude(floor_profile(side),0,p.FLIPPER_GUARD_BASE_T)
    if side=='right':shape=shape.mirror(Plane.YZ)
    # The thrust pedestal remains separate; the tray never clamps its sidewall.
    shape -= Cylinder(p.FLIPPER_GUARD_PEDESTAL_BORE/2, p.FLIPPER_GUARD_BASE_T,
                      align=(Align.CENTER, Align.CENTER, Align.MIN))
    for point in stop_centers():
        shape += Pos(*point, 0) * Cylinder(p.FLIPPER_STOP_R, p.FLIPPER_STOP_H,
                                         align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Right band makes two turns; neck accepts two 1.5875 mm stacked loops.
    for point in p.FLIPPER_FIXED_ANCHORS[side]:
        shape += Pos(*point, p.FLIPPER_GUARD_BASE_T) * Cylinder(
            p.FLIPPER_POST_R, p.FLIPPER_POST_NECK_Z+p.FLIPPER_POST_NECK_H-p.FLIPPER_GUARD_BASE_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        shape += Pos(*point, p.FLIPPER_POST_NECK_Z+p.FLIPPER_POST_NECK_H) * Cylinder(
            p.FLIPPER_POST_CAP_R, p.FLIPPER_POST_CAP_H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for point in mounts:
        shape += Pos(*point, 0) * Cylinder(p.FLIPPER_GUARD_MOUNT_R, p.FLIPPER_GUARD_BASE_T,
                                         align=(Align.CENTER, Align.CENTER, Align.MIN))
        shape -= Pos(*point, 0) * Cylinder(p.M4_BORE/2, p.FLIPPER_GUARD_BASE_T,
                                         align=(Align.CENTER, Align.CENTER, Align.MIN))
    if side == "right":
        shape = shape.mirror(Plane.YZ)
    assert len(shape.solids()) == 1, "Guard tray must connect both hard-stop roots"
    shape.label = f"flipper_{side}_guard_base"
    return shape
