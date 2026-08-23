"""reserve_column — the tile silo: a tapered square obelisk with a full-
height read slot, so the remaining stack height is a game clock readable
across the table.

AMENDED (brief.json top-level amendments, 2nd entry): column_h grew 150 ->
306mm and now exceeds the 251mm bed z-limit as a single print, so this
module builds TWO printed segments (`make_reserve_column_lower` /
`make_reserve_column_upper`) instead of one solid. Both segments are cut
from the SAME taper-width function and the SAME bore/slot cutters (never
two independently-stated profiles), so the 24mm bore and 9mm read-slot are
guaranteed to line up flush across the seam by construction, not by two
numbers that happen to agree today.

The two segments register on each other with a square spigot boss (on the
lower segment's top) nesting into a matching blind socket (in the upper
segment's bottom). The boss/socket sizing is DERIVED from the column's own
taper-width function at the seam height, so it can never drift out of sync
with the taper. The bore and slot both cut straight through the boss/socket
band unmodified -- the register only narrows the OUTER wall, never the tile
channel, so a tile or a finger never meets a step or ridge at the joint.
"""
from __future__ import annotations

import cadquery as cq

from params import Params


def _width_at(p: Params, z: float) -> float:
    """The column's own square cross-section width at height z (0 at the
    70mm base, column_h at the 46mm shaft tip) -- linear taper, the single
    source both segments and the tenon/socket register read from."""
    t = max(0.0, min(1.0, z / p.column_h))
    return p.column_base + (p.column_shaft - p.column_base) * t


def _bore_cutter(p: Params, length: float) -> cq.Workplane:
    """The 24mm tile bore, generous length so a boolean cut always clears
    both ends of whichever segment it's applied to."""
    return (
        cq.Workplane("XY")
        .circle(p.column_bore_dia / 2.0)
        .extrude(length + 4.0)
        .translate((0, 0, -2.0))
    )


def _slot_cutter(p: Params, length: float) -> cq.Workplane:
    """The 9mm-wide full-height read/finger slot, running from the bore
    center out past the widest possible edge (column_base, always >= the
    local taper width) so it fully crosses the outer wall at every height in
    either segment."""
    return (
        cq.Workplane("XY")
        .box(p.column_base, p.column_slot_w, length + 4.0, centered=(False, True, False))
        .translate((0, 0, -2.0))
    )


def _tapered_shell(p: Params, z0: float, z1: float) -> cq.Workplane:
    """A plain square-loft shell from the column's own taper width at z0 to
    its width at z1, standing on the print bed at local z=0 (== world z0)."""
    w0, w1 = _width_at(p, z0), _width_at(p, z1)
    return (
        cq.Workplane("XY")
        .rect(w0, w0)
        .workplane(offset=z1 - z0)
        .rect(w1, w1)
        .loft()
    )


def make_reserve_column_lower(p: Params) -> cq.Workplane:
    """0 .. column_seg_lower_h of the taper, plus a square spigot boss
    proud of the cut top face that registers into the upper segment's
    socket. Prints standing on its own 70mm base -- self-supporting, same
    orientation the single-piece column always used."""
    seam_z = p.column_seg_lower_h
    body = _tapered_shell(p, 0.0, seam_z)

    tenon_w = _width_at(p, seam_z) - 2.0 * p.column_tenon_offset
    tenon = (
        cq.Workplane("XY")
        .rect(tenon_w, tenon_w)
        .extrude(p.column_tenon_h)
        .translate((0, 0, seam_z))
    )
    body = body.union(tenon)

    total_h = seam_z + p.column_tenon_h
    body = body.cut(_bore_cutter(p, total_h))
    body = body.cut(_slot_cutter(p, total_h))
    return body


def make_reserve_column_upper(p: Params) -> cq.Workplane:
    """column_seg_lower_h .. column_h of the taper (local frame, 0 at the
    seam), with a blind socket in its bottom face sized to receive the
    lower segment's tenon (nominal tenon width + clearance/side). Prints
    standing on its own (wider) cut end -- the taper only gets narrower
    going up, so this orientation is self-supporting the same way the
    original single-piece column was."""
    seam_z = p.column_seg_lower_h
    upper_h = p.column_h - seam_z
    body = _tapered_shell(p, seam_z, p.column_h)

    tenon_w = _width_at(p, seam_z) - 2.0 * p.column_tenon_offset
    socket_w = tenon_w + 2.0 * p.column_tenon_clearance
    socket = (
        cq.Workplane("XY")
        .rect(socket_w, socket_w)
        .extrude(p.column_tenon_h + 0.5)
        .translate((0, 0, -0.5))
    )
    body = body.cut(socket)

    body = body.cut(_bore_cutter(p, upper_h))
    body = body.cut(_slot_cutter(p, upper_h))

    # Chamfered top mouth so a tile funnels in -- only the very top of the
    # full 306mm stack needs this, so only the upper segment carries it.
    try:
        body = body.faces(">Z").chamfer(p.column_top_chamfer)
    except Exception:
        pass  # cosmetic only -- the bore + slot already open the top cleanly

    return body
