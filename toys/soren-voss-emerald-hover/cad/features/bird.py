"""Two solid sagittal hummingbird halves; exposed mechanism belly keepout.

Construction is one station loft with a buried bill root, fused eye emboss,
and fixed rear foot. Each manufacturing leaf is one positive-volume solid.
Global x lateral, y forward, z up. Print transform sends outward x to +Z.
"""
from functools import lru_cache
from build123d import (Align, Axis, Box, Color, Plane, Pos, Rot, Sphere, Ellipse,
                      Polygon, extrude, loft)
import params as P


def _station_loft(stations):
    sections = [Plane(origin=(0, y, z), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
                * Ellipse(width, height) for y, z, width, height in stations]
    return loft(sections)


@lru_cache(maxsize=1)
def _whole_bird():
    body = _station_loft(P.BODY_STATIONS)
    bill = _station_loft(P.BILL_STATIONS)
    foot = Pos(*P.FOOT_MIN) * Box(*P.FOOT_SIZE, align=(Align.MIN,)*3)
    eye_r = Pos(*P.EYE_CENTER) * Sphere(P.EYE_RADIUS)
    eye_l = eye_r.mirror(Plane.YZ)
    body = body + [bill, foot, eye_r, eye_l]
    belly = Pos(*P.KEEPOUT_MIN) * Box(*P.KEEPOUT_SIZE, align=(Align.MIN,)*3)
    notch = Pos(0, 0, P.TAIL_NOTCH_BOTTOM) * extrude(
        Polygon(*P.TAIL_NOTCH_POINTS, align=None),
        amount=P.TAIL_NOTCH_HEIGHT, dir=(0, 0, 1))
    body = body - [belly, notch]
    assert len(body.solids()) == 1 and body.volume > 0 and body.is_valid
    return body


def bird_half(side=1, print_pose=False):
    """side +1 right, -1 left; assembly pose is already global coordinates."""
    width, depth, height = P.SPLIT_BOX_SIZE
    box = Pos(side * width / 2, *P.SPLIT_BOX_CENTER_YZ) * Box(width, depth, height)
    half = (_whole_bird() & box).solids()[0]
    assert len(half.solids()) == 1 and half.volume > 0 and half.is_valid
    half.label = 'bird_right' if side > 0 else 'bird_left'
    half.color = Color(*P.EMERALD)
    # Face colors describe finish zones while retaining one manufacturing body.
    for face in half.faces():
        c = face.center()
        if c.Y < P.TAIL_COLOR_END_Y or (
                c.Y > P.THROAT_COLOR_MIN_Y and c.Z < P.THROAT_COLOR_MAX_Z):
            face.color = Color(*P.VIOLET)
        elif c.Y > P.BILL_COLOR_START_Y:
            face.color = Color(*P.DARK_BILL)
        elif ((abs(c.X)-P.EYE_CENTER[0])**2 +
              (c.Y-P.EYE_CENTER[1])**2 + (c.Z-P.EYE_CENTER[2])**2) < P.EYE_RADIUS**2:
            face.color = Color(*P.EYE_COLOR)
    if print_pose:
        # x'=-side*(z-80), y'=y+28, z'=side*x. Flat sagittal plane is z'=0.
        half = Pos(0, P.PRINT_ORIGIN_Y, 0) * Rot(0, -side*P.RIGHT_ANGLE, 0) * Pos(
            0, 0, -P.PRINT_ORIGIN_Z) * half
    return half
