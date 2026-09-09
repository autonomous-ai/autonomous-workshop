"""Knockseed parameters and solid builder.

Origin: center of the ventral knock face; XY is the bed; +Z is up.
Print stance: knock face at Z=0. Long axis is X; micropyle toward +X.
"""

from __future__ import annotations

from build123d import (
    Align,
    Box,
    Pos,
    Rot,
    Sphere,
    scale,
)
from cadgen.assembly import label_shape
from cadgen import srgb

SEED_LENGTH = 34.6
SEED_WIDTH = 18.4
SEED_HEIGHT = 13.0

RX = 17.3
RY = 9.2
RZ = 7.2
BELLY_LIFT = 5.5
NOSE_X = 15.4
NOSE_RX = 3.4
NOSE_RY = 2.5
NOSE_RZ = 2.5

SEED_COLOR = srgb("#C48A4A")

assert BELLY_LIFT < RZ
assert SEED_LENGTH <= 38.0 and SEED_WIDTH <= 24.0 and SEED_HEIGHT <= 18.0


def build_knockseed():
    hull = Pos(0.0, 0.0, BELLY_LIFT) * scale(Sphere(1.0), (RX, RY, RZ))
    nose = Pos(NOSE_X, 0.0, BELLY_LIFT) * scale(Sphere(1.0), (NOSE_RX, NOSE_RY, NOSE_RZ))
    body = hull + nose
    keep = Box(80.0, 80.0, 40.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = body & keep
    solids = list(body.solids())
    assert len(solids) == 1, f"{len(solids)} solids"
    solid = solids[0]
    assert solid.volume > 0.0
    bbox = solid.bounding_box()
    if abs(float(bbox.min.Z)) > 1e-6:
        solid = Pos(0, 0, -float(bbox.min.Z)) * solid
        bbox = solid.bounding_box()
    assert abs(float(bbox.min.Z)) < 1e-4, f"print datum Z={bbox.min.Z}"
    length = float(bbox.max.X - bbox.min.X)
    width = float(bbox.max.Y - bbox.min.Y)
    height = float(bbox.max.Z - bbox.min.Z)
    assert length <= 38.0 and width <= 24.0 and height <= 18.0, (
        f"envelope miss {length:.2f}x{width:.2f}x{height:.2f}"
    )
    solid.label = "knockseed"
    solid.color = SEED_COLOR
    return label_shape(solid, "knockseed")


def pose_on_belly(solid, tilt_deg: float):
    posed = Rot(tilt_deg, 0, 0) * solid
    bbox = posed.bounding_box()
    return Pos(0, 0, -float(bbox.min.Z)) * posed
