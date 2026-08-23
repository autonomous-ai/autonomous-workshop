"""Positioning + union of base and cover into a single solid for export.

Assembly positioning lives here, NOT in the part files. Parts are placed
in their own local coordinate frame; we move them into final position.
"""

from __future__ import annotations

import cadquery as cq

from params import Params
from parts.base import make_base
from parts.cover import make_cover


def make_assembly(p: Params) -> cq.Workplane:
    base = make_base(p)
    cover = make_cover(p).translate((0, 0, p.height + p.lid_gap))
    return base.union(cover)
