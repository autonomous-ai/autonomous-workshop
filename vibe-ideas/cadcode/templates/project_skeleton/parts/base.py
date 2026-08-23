"""Open-top base, built with its print-bed datum at local Z=0."""

from __future__ import annotations

import cadquery as cq

from cadlib.enclosure import hollow_box
from params import Params


def make_base(p: Params) -> cq.Workplane:
    # hollow_box is centered on Z; shift it so the printable bottom datum is 0.
    return hollow_box(
        length=p.width,
        width=p.depth,
        height=p.height,
        wall=p.wall,
        corner_radius=p.corner_radius,
    ).translate((0, 0, p.height / 2))
