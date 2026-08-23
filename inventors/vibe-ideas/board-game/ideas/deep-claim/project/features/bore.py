"""The two-stage assay bore: one axisymmetric revolve profile per bore, so
shelf, throat, floor chamber, and the shelf's lead-in chamfer all come out
of a single watertight cut instead of three separately-booleaned cylinders
that could drift out of sync.
"""

from __future__ import annotations

import cadquery as cq

from params import Params


def bore_cutter(p: Params, top_z: float) -> cq.Workplane:
    """One bore's cutting solid, centered on the board's own Z axis.

    ``top_z`` is the board's top face height in the board's local frame
    (board centered on Z, so top_z = board_thickness / 2). Translate the
    result to a bore's (x, y) center and `.cut()` it from the board blank.

    Profile, top to bottom (see brief.md's bore table):
        chamfer flat -> down the 45deg lead-in -> shelf chamber wall ->
        step to throat -> throat wall -> step to floor chamber ->
        floor chamber wall -> closed bottom.
    """
    shelf_r = p.shelf_dia / 2.0
    throat_r = p.throat_dia / 2.0
    floor_r = p.floor_dia / 2.0
    chamfer = p.shelf_chamfer

    z_chamfer_bottom = top_z - chamfer
    z_shelf_floor = top_z - p.shelf_depth
    z_throat_floor = z_shelf_floor - p.throat_depth
    z_floor_bottom = z_throat_floor - p.floor_depth

    profile = (
        cq.Workplane("XZ")
        .moveTo(0, top_z)
        .lineTo(shelf_r + chamfer, top_z)
        .lineTo(shelf_r, z_chamfer_bottom)
        .lineTo(shelf_r, z_shelf_floor)
        .lineTo(throat_r, z_shelf_floor)
        .lineTo(throat_r, z_throat_floor)
        .lineTo(floor_r, z_throat_floor)
        .lineTo(floor_r, z_floor_bottom)
        .lineTo(0, z_floor_bottom)
        .close()
    )
    # Default revolve axis on an "XZ" workplane is the plane's local Y axis,
    # which is the board's global Z axis -- exactly the bore's own axis.
    return profile.revolve(360)
