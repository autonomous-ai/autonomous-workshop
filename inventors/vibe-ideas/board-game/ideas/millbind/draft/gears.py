"""Shared gear-tooth geometry: every gear, millstone and the crank cut the
SAME 12-tooth/30mm-pitch/35mm-OD profile (params.py owns the numbers) —
built once here, never re-derived per part.
"""
import math

import cadquery as cq

import params as p


def _tooth_solid(z0: float, z1: float) -> cq.Workplane:
    """One trapezoidal tooth, extruded from z0 to z1, centred on +X."""
    tooth_w_at_pitch = math.pi * p.MODULE / 2.0
    half_tooth_arc = math.atan2(tooth_w_at_pitch / 2.0, p.PITCH_R)
    root_half = half_tooth_arc * 1.3
    tip_half = half_tooth_arc * 0.45
    pts = [
        (p.ROOT_R * math.cos(-root_half), p.ROOT_R * math.sin(-root_half)),
        (p.OUTER_R * math.cos(-tip_half), p.OUTER_R * math.sin(-tip_half)),
        (p.OUTER_R * math.cos(tip_half), p.OUTER_R * math.sin(tip_half)),
        (p.ROOT_R * math.cos(root_half), p.ROOT_R * math.sin(root_half)),
    ]
    return (
        cq.Workplane("XY")
        .polyline(pts)
        .close()
        .extrude(z1 - z0)
        .translate((0, 0, z0))
    )


def build_barrel(total_h: float, teeth_z0: float, teeth_z1: float) -> cq.Workplane:
    """A root-disk barrel of ROOT_R, standing total_h tall from z=0, with
    the shared tooth ring cut into the [teeth_z0, teeth_z1] band. Outside
    that band the barrel is a plain root-diameter cylinder (an untoothed
    rim, or the base a caller stacks other features onto).
    """
    body = cq.Workplane("XY").circle(p.ROOT_R).extrude(total_h)
    for i in range(p.TEETH):
        angle = i * 360.0 / p.TEETH
        body = body.union(_tooth_solid(teeth_z0, teeth_z1).rotate(
            (0, 0, 0), (0, 0, 1), angle))
    return body


def bore_through(body: cq.Workplane, total_h: float) -> cq.Workplane:
    cutter = (
        cq.Workplane("XY").circle(p.BORE_D / 2.0)
        .extrude(total_h + 2.0)
        .translate((0, 0, -1.0))
    )
    return body.cut(cutter)


def lightening_holes(body: cq.Workplane, total_h: float, n: int = 3,
                      hole_d: float = 4.0) -> cq.Workplane:
    """Round grip holes in the web, between the bore and the root circle."""
    r = (p.BORE_D / 2.0 + p.ROOT_R) / 2.0
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


def build_gear_low() -> cq.Workplane:
    """Squat toothed puck, teeth start right at the floor."""
    body = build_barrel(p.GEAR_LOW_H, 0.0, p.GEAR_LOW_H)
    body = bore_through(body, p.GEAR_LOW_H)
    body = lightening_holes(body, p.GEAR_LOW_H)
    return body


def build_gear_high() -> cq.Workplane:
    """Lamppost: smooth column below, tooth ring at the top."""
    column_h = p.GEAR_HIGH_H - p.GEAR_HIGH_TEETH_H
    column = (
        cq.Workplane("XY").circle(p.GEAR_HIGH_COLUMN_D / 2.0).extrude(column_h)
    )
    teeth_section = build_barrel(
        p.GEAR_HIGH_TEETH_H, 0.0, p.GEAR_HIGH_TEETH_H
    ).translate((0, 0, column_h))
    body = column.union(teeth_section)
    body = bore_through(body, p.GEAR_HIGH_H)
    return body


def build_gear_tandem() -> cq.Workplane:
    """Full barrel of teeth the whole pin height, 1mm lead-in rim top/bottom."""
    body = build_barrel(p.BARREL_H, p.BARREL_TEETH_Z0, p.BARREL_TEETH_Z1)
    body = bore_through(body, p.BARREL_H)
    return body
