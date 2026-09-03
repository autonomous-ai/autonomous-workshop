"""Front and rear shell builders."""

import math

from build123d import Align, Axis, Box, Cylinder, Pos, Rot, chamfer

from features.common import bar_between, frame_face, fuse_all, sketch_polygon
from params import *


def rear_bearing_support(shell):
    for side in (-1.0, 1.0):
        x = side * STAND_HINGE_X
        rib = bar_between((side * 48.0, -47.0), (x, STAND_HINGE_Y), 6.0, REAR_FACE_T)
        support_h = STAND_HINGE_Z - REAR_INNER_Z + BEARING_SOCKET_R + 1.05
        flange = Pos(x, STAND_HINGE_Y, 0) * Box(
            BEARING_BLOCK_W + 1.0, BEARING_BLOCK_H + 4.0, REAR_FACE_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        flange = chamfer(
            flange.faces().sort_by(Axis.Z)[-1].edges(), length=1.5,
        )
        cheek = Pos(x, STAND_HINGE_Y, REAR_FACE_T) * Box(
            BEARING_BLOCK_W, BEARING_BLOCK_H,
            support_h - REAR_FACE_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        # Extend each open socket mouth 0.5 mm beyond the cheek face while
        # retaining the authored 1.0 mm blind wall at the opposite end.
        socket_x0 = (
            x - BEARING_BLOCK_W / 2 - 0.5
            if side > 0 else x - BEARING_BLOCK_W / 2 + 1.0
        )
        socket = Pos(socket_x0, STAND_HINGE_Y, STAND_HINGE_Z - REAR_INNER_Z) * Box(
            BEARING_BLOCK_W - 0.5, BEARING_SOCKET_R * 2, BEARING_SOCKET_R * 2,
            align=(Align.MIN, Align.CENTER, Align.CENTER),
        )
        shell = shell.fuse(rib, flange, cheek).cut(socket)
    return shell


def make_front_shell(*, compressed_latches: bool = False, compressed_detent: bool = False):
    shell = frame_face(SHELL_FACE_T, faceted=True)
    spindle = Pos(0, 0, SHELL_FACE_T) * Cylinder(
        SPINDLE_D / 2, SPINDLE_LEN,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    shell = shell.fuse(spindle)
    for x, y in HOOK_POSITIONS:
        stem = Pos(x, y, SHELL_FACE_T) * Box(
            HOOK_W, HOOK_H, HOOK_STEM_LEN,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        barb_w = HOOK_LEAD_W if compressed_latches else HOOK_BARB_W
        barb_shift = (barb_w - HOOK_W) / 2
        barb = Box(
            barb_w, HOOK_BARB_H, HOOK_BARB_T,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        if not compressed_latches:
            ramp_edges = [
                edge for edge in barb.edges()
                if edge.center().X > barb_w / 2 - 0.01
                and edge.center().Z > HOOK_BARB_T - 0.01
            ]
            barb = chamfer(ramp_edges, length=HOOK_LEAD_CHAMFER)
        barb = Pos(x + barb_shift, y, SHELL_FACE_T + HOOK_STEM_LEN) * barb
        shell = shell.fuse(stem, barb)
    for x in (-3.7, 3.7):
        shell = shell.cut(Pos(x, -50.0, -0.1) * Box(
            1.4, 16.0, SHELL_FACE_T + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ))
    shell = shell.cut(Pos(0, -59.0, -0.1) * Box(
        8.8, 2.0, SHELL_FACE_T + 0.2,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ))
    leaf_edges = [edge for edge in shell.edges() if abs(edge.center().Z-SHELL_FACE_T) < 0.01 and abs(edge.center().X) < 5.0 and -58.5 < edge.center().Y < -41.5]
    shell = chamfer(leaf_edges, length=0.4)
    nose_h = AXIAL_GAP if compressed_detent else DETENT_NOSE_H
    nose = Cylinder(DETENT_NOSE_R, nose_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    if not compressed_detent:
        tip_edges = [edge for edge in nose.edges() if edge.center().Z > DETENT_NOSE_H - 0.01]
        nose = chamfer(tip_edges, length=DETENT_NOSE_CHAMFER)
    shell = shell.fuse(Pos(0, -52.5, SHELL_FACE_T) * nose)
    # A through-cut arrow sits clear of the detent leaf and points at the
    # matching right-rim double-V.  Backlighting and the chromatic render both
    # preserve this much more strongly than a shallow same-colour recess.
    home_pointer = fuse_all([
        Pos(42.5, 0, -0.1) * Box(
            9.0, 4.0, SHELL_FACE_T + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ),
        Pos(0, 0, -0.1) * sketch_polygon(
            [(46.0, -7.0), (51.5, 0.0), (46.0, 7.0)], SHELL_FACE_T + 0.2
        ),
    ])
    shell = shell.cut(home_pointer)
    shell.label = "front_shell"
    assert len(shell.solids()) == 1
    return shell


def make_rear_shell():
    shell = rear_bearing_support(frame_face(REAR_FACE_T, faceted=True))
    bore_apothem = SPINDLE_BORE_D / 2
    bore_radius = bore_apothem / math.cos(math.pi / 24)
    bore_points = [
        (math.cos(2 * math.pi * index / 24) * bore_radius,
         math.sin(2 * math.pi * index / 24) * bore_radius)
        for index in range(24)
    ]
    shell = shell.cut(Pos(0, 0, -0.5) * sketch_polygon(bore_points, 2.0))
    for x, y in HOOK_POSITIONS:
        shell = shell.cut(Pos(x, y, -0.5) * Box(
            HOOK_SLOT_W, HOOK_SLOT_H, REAR_FACE_T + 1.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ))
    for angle in (0, 90, 180, 270):
        rad = math.radians(angle)
        tick = Pos(
            math.cos(rad) * 26.0, PORTAL_Y + math.sin(rad) * 26.0, REAR_FACE_T,
        ) * Rot(0, 0, angle) * Box(
            5.0, 2.2, 0.8, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        shell = shell.fuse(tick)
    for x in (-PORTAL_R + 1.5, PORTAL_R - 1.5):
        shell = shell.fuse(Pos(x, PORTAL_Y, 0) * Box(
            3.0, 5.0, REAR_FACE_T + 0.2,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ))
    # Six raised tactile tiles form an unambiguous arrow without removing wall
    # material.  Their 1.6 mm relief remains visible in one-colour prints.
    for x, y in ((0.0, -9.0), (0.0, -4.0), (0.0, 1.0),
                 (-4.5, 1.5), (0.0, 5.0), (4.5, 1.5)):
        shell = shell.fuse(Pos(x, y, REAR_FACE_T) * Box(
            5.0, 5.0, 1.6,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        ))
    for x in (-40.0, 40.0):
        shell = shell.fuse(Pos(x, -36.0, 0) * Box(
            6.0, 2.0, 4.8, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ))
    shell.label = "rear_shell"
    assert len(shell.solids()) == 1
    return shell
