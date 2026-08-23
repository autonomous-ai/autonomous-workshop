"""grain_pellet, sack_spindle, granary_bin -- the score economy."""
from __future__ import annotations

import cadquery as cq

from params import Params


def make_grain_pellet(p: Params) -> cq.Workplane:
    body = cq.Workplane("XY").circle(p.pellet_d / 2.0).extrude(p.pellet_h)
    body = body.faces(">Z").chamfer(1.4)
    hole = (
        cq.Workplane("XY").circle(p.pellet_hole_d / 2.0)
        .extrude(p.pellet_h + 2.0).translate((0, 0, -1.0))
    )
    return body.cut(hole)


def _add_chevron_skirt(body: cq.Workplane, radius: float, z0: float, height: float,
                       depth: float, n: int = 12, tilt_deg: float = 28.0) -> cq.Workplane:
    """1mm chevron water-texture: n alternating-tilt V-groove notches cut
    radially into a cylindrical skirt wall, evenly spaced around it -- the
    same "cut a small feature at angle 0, then rotate around Z" technique
    parts/gears.py uses for teeth.
    """
    groove_w = 2.4
    seg_len = height * 0.85
    mid_z = z0 + height / 2.0
    for i in range(n):
        tilt = tilt_deg if i % 2 == 0 else -tilt_deg
        cutter = (
            cq.Workplane("XY")
            .box(depth * 2.0, groove_w, seg_len)
            .translate((radius - depth, 0, mid_z))
            .rotate((radius, 0, mid_z), (radius, 1, mid_z), tilt)
        )
        cutter = cutter.rotate((0, 0, 0), (0, 0, 1), i * 360.0 / n)
        body = body.cut(cutter)
    return body


def make_sack_spindle(p: Params) -> cq.Workplane:
    base = cq.Workplane("XY").circle(p.spindle_base_d / 2.0).extrude(p.spindle_base_h)
    base = base.faces(">Z").chamfer(1.0)
    base = _add_chevron_skirt(
        base, p.spindle_base_d / 2.0, 0.0, p.spindle_base_h,
        p.spindle_chevron_depth,
    )
    rod = (
        cq.Workplane("XY").circle(p.spindle_rod_d / 2.0)
        .extrude(p.spindle_rod_h).translate((0, 0, p.spindle_base_h))
    )
    return base.union(rod)


def _add_chevron_front(body: cq.Workplane, width: float, z0: float, height: float,
                       depth: float, front_y: float, n: int = 5) -> cq.Workplane:
    """1mm chevron water-texture on the front wall: a zigzag ribbon groove
    (n peaks) cut `depth` into the outward-facing surface at `front_y`."""
    groove_w = 3.0
    amp = min(height * 0.28, (width / n) * 0.55)
    mid_z = z0 + height / 2.0
    seg = width / n
    top, bot = [], []
    for i in range(n + 1):
        xi = -width / 2.0 + i * seg
        zi = mid_z + (amp if i % 2 == 0 else -amp)
        top.append((xi, zi + groove_w / 2.0))
        bot.append((xi, zi - groove_w / 2.0))
    poly_pts = top + list(reversed(bot))
    cutter = (
        cq.Workplane("XZ")
        .polyline(poly_pts).close()
        .extrude(depth, both=True)
        .translate((0, front_y, 0))
    )
    return body.cut(cutter)


def make_granary_bin(p: Params) -> cq.Workplane:
    outer = cq.Workplane("XY").box(
        p.bin_l, p.bin_w, p.bin_h, centered=(True, True, False)
    )
    inner = cq.Workplane("XY").box(
        p.bin_l - 2 * p.bin_wall, p.bin_w - 2 * p.bin_wall,
        p.bin_h - p.bin_wall + 1.0, centered=(True, True, False),
    ).translate((0, 0, p.bin_wall))
    bin_body = outer.cut(inner)

    # Thumb scallop cut into the top rim of one LONG wall (the 70mm-long
    # wall running along X, at y = +bin_w/2).
    scallop = (
        cq.Workplane("XZ")
        .circle(p.bin_scallop_r)
        .extrude(p.bin_wall + 2.0, both=True)
        .translate((0, 0, p.bin_h))
    )
    scallop = scallop.translate((0, p.bin_w / 2.0, 0))
    bin_body = bin_body.cut(scallop)

    # 1mm chevron water-texture on the front (-Y wall, opposite the scallop).
    bin_body = _add_chevron_front(
        bin_body, p.bin_l - 20.0, p.bin_wall, p.bin_h - 2.0 * p.bin_wall,
        p.bin_chevron_depth, -p.bin_w / 2.0,
    )
    return bin_body
