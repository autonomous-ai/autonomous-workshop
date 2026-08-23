"""The lower half of the enclosure — hollow shell with screw bosses."""

from __future__ import annotations

import cadquery as cq

from params import Params


def make_base(p: Params) -> cq.Workplane:
    # Feature pipeline: each step takes (part, p) and returns a part.
    part = _outer_shell(p)
    part = _hollow_inside(part, p)
    part = _add_screw_bosses(part, p)
    return part


def _outer_shell(p: Params) -> cq.Workplane:
    return (
        cq.Workplane("XY")
        .box(p.width, p.depth, p.height)
        .edges("|Z")
        .fillet(p.corner_radius)
    )


def _hollow_inside(part: cq.Workplane, p: Params) -> cq.Workplane:
    return part.faces(">Z").shell(-p.wall)


def _add_screw_bosses(part: cq.Workplane, p: Params) -> cq.Workplane:
    points = [
        (-p.width / 2 + p.screw_margin, -p.depth / 2 + p.screw_margin),
        ( p.width / 2 - p.screw_margin, -p.depth / 2 + p.screw_margin),
        (-p.width / 2 + p.screw_margin,  p.depth / 2 - p.screw_margin),
        ( p.width / 2 - p.screw_margin,  p.depth / 2 - p.screw_margin),
    ]
    return (
        part
        .faces("<Z[1]")  # the floor inside the shell
        .workplane()
        .pushPoints(points)
        .circle(p.screw_boss_diameter / 2)
        .extrude(p.height - p.wall - 1.0)
        .faces(">Z")
        .workplane()
        .pushPoints(points)
        .hole(p.screw_diameter)
    )
