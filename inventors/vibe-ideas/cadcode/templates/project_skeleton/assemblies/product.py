"""Positioning of the separately printable base and cover.

Assembly positioning lives here, NOT in the part files. Parts are placed
in their own local coordinate frame; a named ``cq.Assembly`` places them in
the product frame without boolean-unioning the two physical parts.
"""

from __future__ import annotations

import cadquery as cq

from params import Params
from parts.base import make_base
from parts.cover import make_cover


def make_assembly(p: Params) -> cq.Assembly:
    assembly = cq.Assembly()
    assembly.add(make_base(p), name="base", color=cq.Color(0.80, 0.82, 0.85))
    # Both parts use an explicit Z=0 bottom/underside datum. The base rim is
    # therefore exactly Z=p.height; no half-height correction is hidden here.
    assembly.add(
        make_cover(p),
        name="cover",
        loc=cq.Location((0, 0, p.height)),
        color=cq.Color(0.30, 0.55, 0.90),
    )
    return assembly
