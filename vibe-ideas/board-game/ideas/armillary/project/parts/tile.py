"""star_tile / moon_tile / void_tile — ONE shared blank, three face motifs.

LOAD-BEARING (idea.json + brief.json): outline (22mm round), thickness
(6mm), rim and back (10mm/9mm knurled knob) are bit-for-bit identical across
all three families. The only geometry allowed to differ is the 1.2mm face
relief, and even that lives inside a shared recessed pocket so the tile's
outer envelope never changes: a thin (2mm) untouched rim survives at the
tile's edge on every family, and the relief motif is a boss that returns to
flush with that same rim plane — never higher, never lower. A face-down
tile is therefore unreadable by outline, weight, or touch at the rim,
exactly as the hidden-information mechanic requires.

The face carrying the relief is the tile's BOTTOM (z=0 plane); the knurled
knob is the BACK, on top. Tiles are placed knob-up / relief-down in the
wells, which is also their stated print orientation.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params


def _tile_blank(p: Params) -> cq.Workplane:
    body = cq.Workplane("XY").circle(p.tile_dia / 2.0).extrude(p.tile_thickness)
    knob = (
        cq.Workplane("XY")
        .workplane(offset=p.tile_thickness)
        .circle(p.knob_dia / 2.0)
        .extrude(p.knob_h)
    )
    tile = body.union(knob)
    # Knurling on the knob — a light ring of shallow vertical flutes, the
    # only texture the back carries (idea.json's surface_treatment).
    flutes = 16
    for i in range(flutes):
        ang = math.radians(i * 360.0 / flutes)
        fx = (p.knob_dia / 2.0 - 0.2) * math.cos(ang)
        fy = (p.knob_dia / 2.0 - 0.2) * math.sin(ang)
        flute = (
            cq.Workplane("XY")
            .workplane(offset=p.tile_thickness)
            .circle(0.5)
            .extrude(p.knob_h)
            .translate((fx, fy, 0))
        )
        tile = tile.cut(flute)
    return tile


def _relief_pocket(p: Params) -> cq.Workplane:
    return cq.Workplane("XY").circle(p.relief_pocket_r).extrude(p.relief_h)


def _star_motif(p: Params) -> cq.Workplane:
    outer_r, inner_r, points = 8.0, 3.2, 5
    pts = []
    for i in range(points * 2):
        rad = outer_r if i % 2 == 0 else inner_r
        ang = math.radians(i * 360.0 / (points * 2) - 90.0)
        pts.append((rad * math.cos(ang), rad * math.sin(ang)))
    return cq.Workplane("XY").polyline(pts).close().extrude(p.relief_h)


def _moon_motif(p: Params) -> cq.Workplane:
    big = cq.Workplane("XY").circle(7.0).extrude(p.relief_h)
    small = cq.Workplane("XY").circle(6.2).translate((3.6, 0, 0)).extrude(p.relief_h)
    return big.cut(small)


def _void_motif(p: Params) -> cq.Workplane:
    disc = cq.Workplane("XY").circle(3.5).extrude(p.relief_h)
    ring = cq.Workplane("XY").circle(8.0).circle(5.6).extrude(p.relief_h)
    teeth = 10
    for i in range(teeth):
        ang = math.radians(i * 360.0 / teeth)
        nx = 6.8 * math.cos(ang)
        ny = 6.8 * math.sin(ang)
        notch = cq.Workplane("XY").box(1.6, 3.2, p.relief_h + 0.4).translate((nx, ny, p.relief_h / 2.0))
        notch = notch.rotate((nx, ny, 0), (nx, ny, 1), math.degrees(ang))
        ring = ring.cut(notch)
    return disc.union(ring)


_MOTIFS = {"star": _star_motif, "moon": _moon_motif, "void": _void_motif}


def make_tile(p: Params, motif: str) -> cq.Workplane:
    tile = _tile_blank(p)
    tile = tile.cut(_relief_pocket(p))
    tile = tile.union(_MOTIFS[motif](p))
    return tile


def make_star_tile(p: Params) -> cq.Workplane:
    return make_tile(p, "star")


def make_moon_tile(p: Params) -> cq.Workplane:
    return make_tile(p, "moon")


def make_void_tile(p: Params) -> cq.Workplane:
    return make_tile(p, "void")
