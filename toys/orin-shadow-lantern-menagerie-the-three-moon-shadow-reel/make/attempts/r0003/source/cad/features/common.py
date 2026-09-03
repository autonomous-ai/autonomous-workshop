"""Shared planar and frame geometry helpers."""

import math

from build123d import Align, Axis, Box, BuildSketch, Circle, Cylinder, Ellipse
from build123d import Plane, Polygon, Pos, RectangleRounded, Rot, SlotOverall
from build123d import chamfer, extrude

from params import (
    FRAME_BASE_CY,
    FRAME_BASE_H,
    FRAME_BASE_W,
    PLANAR_CURVE_FACETS,
    PORTAL_R,
    PORTAL_Y,
)


def sketch_disk(radius: float, height: float):
    with BuildSketch(Plane.XY) as sketch:
        Circle(radius)
    return extrude(sketch.sketch, amount=height)


def sketch_ellipse(rx: float, ry: float, height: float):
    with BuildSketch(Plane.XY) as sketch:
        Ellipse(rx, ry)
    return extrude(sketch.sketch, amount=height)


def sketch_polygon(points: list[tuple[float, float]], height: float):
    with BuildSketch(Plane.XY) as sketch:
        Polygon(*points)
    return extrude(sketch.sketch, amount=height)


def rounded_plate(width: float, height: float, radius: float, thickness: float):
    with BuildSketch(Plane.XY) as sketch:
        RectangleRounded(width, height, radius)
    return extrude(sketch.sketch, amount=thickness)


def faceted_rounded_plate(width: float, height: float, radius: float, thickness: float):
    w, h = width / 2, height / 2
    corners = ((w-radius, h-radius, 0), (-w+radius, h-radius, 90), (-w+radius, -h+radius, 180), (w-radius, -h+radius, 270))
    points = [(cx + radius*math.cos(math.radians(start+step*15)), cy + radius*math.sin(math.radians(start+step*15))) for cx, cy, start in corners for step in range(7)]
    return sketch_polygon(points, thickness)


def bar_between(a: tuple[float, float], b: tuple[float, float], width: float, height: float):
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay)
    angle = math.degrees(math.atan2(by - ay, bx - ax))
    bar = Box(length, width, height, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos((ax + bx) / 2, (ay + by) / 2, 0) * Rot(0, 0, angle) * bar


def capsule(a: tuple[float, float], b: tuple[float, float], width: float, height: float):
    ax, ay = a
    bx, by = b
    length = math.hypot(bx - ax, by - ay) + width
    angle = math.degrees(math.atan2(by - ay, bx - ax))
    with BuildSketch(Plane.XY) as sketch:
        SlotOverall(length, width, rotation=angle)
    return Pos((ax + bx) / 2, (ay + by) / 2, 0) * extrude(sketch.sketch, amount=height)


def fuse_all(shapes):
    result = shapes[0]
    for shape in shapes[1:]:
        result = result.fuse(shape)
    return result


def frame_face(thickness: float, faceted: bool = False):
    disk_points = [
        (
            54.0 * math.cos(2 * math.pi * index / PLANAR_CURVE_FACETS),
            54.0 * math.sin(2 * math.pi * index / PLANAR_CURVE_FACETS),
        )
        for index in range(PLANAR_CURVE_FACETS)
    ]
    face = sketch_polygon(disk_points, thickness) if faceted else sketch_disk(54.0, thickness)
    plate = faceted_rounded_plate if faceted else rounded_plate
    top_cap = Pos(0, 52.0, 0) * plate(50.0, 24.0, 10.0, thickness)
    base = Pos(0, FRAME_BASE_CY, 0) * plate(FRAME_BASE_W, FRAME_BASE_H, 4.0, thickness)
    shield = fuse_all([face, top_cap, base])
    portal_radius = PORTAL_R / math.cos(math.pi / 24) if faceted else PORTAL_R
    portal_points = [(portal_radius * math.cos(2*math.pi*i/24), portal_radius * math.sin(2*math.pi*i/24)) for i in range(24)]
    portal = sketch_polygon(portal_points, thickness + 1.0) if faceted else sketch_disk(PORTAL_R, thickness + 1.0)
    frame = shield.cut(Pos(0, PORTAL_Y, -0.5) * portal)
    return chamfer(frame.faces().sort_by(Axis.Z)[-1].edges(), length=0.8) if faceted else frame


def axis_x_cylinder(x0: float, y: float, z: float, radius: float, length: float):
    return Pos(x0, y, z) * Rot(0, 90, 0) * Cylinder(
        radius, length, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
