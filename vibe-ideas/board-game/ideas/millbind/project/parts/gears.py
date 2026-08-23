"""Shared gear-tooth geometry: every gear, millstone and the crank cut the
SAME 12-tooth/30mm-pitch/35mm-OD profile (params.py owns the numbers) --
built once here (`build_barrel`, `bore_through`) and reused by
parts/millstone.py and parts/crank.py, never re-derived per part.

Also owns the three supply-gear parts: gear_low, gear_high, gear_tandem.
"""
from __future__ import annotations

import math

import cadquery as cq

from params import Params


def _tooth_solid(p: Params, z0: float, z1: float) -> cq.Workplane:
    """One trapezoidal tooth, extruded from z0 to z1, centred on +X."""
    tooth_w_at_pitch = math.pi * p.module / 2.0
    half_tooth_arc = math.atan2(tooth_w_at_pitch / 2.0, p.pitch_r)
    root_half = half_tooth_arc * 1.3
    tip_half = half_tooth_arc * 0.45
    pts = [
        (p.root_r * math.cos(-root_half), p.root_r * math.sin(-root_half)),
        (p.outer_r * math.cos(-tip_half), p.outer_r * math.sin(-tip_half)),
        (p.outer_r * math.cos(tip_half), p.outer_r * math.sin(tip_half)),
        (p.root_r * math.cos(root_half), p.root_r * math.sin(root_half)),
    ]
    return (
        cq.Workplane("XY")
        .polyline(pts)
        .close()
        .extrude(z1 - z0)
        .translate((0, 0, z0))
    )


def build_barrel(p: Params, total_h: float, teeth_z0: float, teeth_z1: float) -> cq.Workplane:
    """A root-disk barrel of `root_r`, standing `total_h` tall from z=0, with
    the shared tooth ring cut into the [teeth_z0, teeth_z1] band. Outside
    that band the barrel is a plain root-diameter cylinder -- an untoothed
    rim, or the base a caller stacks other features onto.
    """
    body = cq.Workplane("XY").circle(p.root_r).extrude(total_h)
    for i in range(p.teeth):
        angle = i * 360.0 / p.teeth
        body = body.union(_tooth_solid(p, teeth_z0, teeth_z1).rotate(
            (0, 0, 0), (0, 0, 1), angle))
    return body


def bore_through(p: Params, body: cq.Workplane, total_h: float) -> cq.Workplane:
    cutter = (
        cq.Workplane("XY").circle(p.bore_d / 2.0)
        .extrude(total_h + 2.0)
        .translate((0, 0, -1.0))
    )
    return body.cut(cutter)


def _lightening_holes(body: cq.Workplane, p: Params, total_h: float, n: int = 3,
                      hole_d: float = 4.0) -> cq.Workplane:
    """Round grip holes in the web, between the bore and the root circle."""
    r = (p.bore_d / 2.0 + p.root_r) / 2.0
    for i in range(n):
        angle = math.radians(i * 360.0 / n)
        x, y = r * math.cos(angle), r * math.sin(angle)
        cutter = (
            cq.Workplane("XY").circle(hole_d / 2.0)
            .extrude(total_h + 2.0)
            .translate((x, y, -1.0))
        )
        body = body.cut(cutter)
    return body


def make_gear_low(p: Params) -> cq.Workplane:
    """Squat toothed puck, teeth start right at the floor. Engages only the
    bottom `gear_low_h` of a `pin_h`-tall pin (partial engagement)."""
    body = build_barrel(p, p.gear_low_h, 0.0, p.gear_low_h)
    body = bore_through(p, body, p.gear_low_h)
    body = _lightening_holes(body, p, p.gear_low_h)
    return body


def make_gear_high(p: Params) -> cq.Workplane:
    """Lamppost: smooth column below, tooth ring at the top. Spans the full
    pin height (full engagement)."""
    column_h = p.gear_high_h - p.gear_high_teeth_h
    column = (
        cq.Workplane("XY").circle(p.gear_high_column_d / 2.0).extrude(column_h)
    )
    teeth_section = build_barrel(
        p, p.gear_high_teeth_h, 0.0, p.gear_high_teeth_h
    ).translate((0, 0, column_h))
    body = column.union(teeth_section)
    body = bore_through(p, body, p.gear_high_h)
    return body


def make_gear_tandem(p: Params) -> cq.Workplane:
    """Full barrel of teeth the whole pin height (full engagement), 1mm
    untoothed lead-in rim top/bottom -- the only supply piece that meshes
    with both tooth tiers."""
    body = build_barrel(p, p.barrel_h, p.barrel_teeth_z0, p.barrel_teeth_z1)
    body = bore_through(p, body, p.barrel_h)
    return body
