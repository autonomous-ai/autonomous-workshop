"""Runtime checks on Params before any geometry is built.

Every brief.json number gets an assert here — see brief.json's `parts` and
`interfaces` arrays for where each value comes from. The two hard-fought
inequalities (34mm shelf > 28mm disc_large > 18mm throat > 14mm disc_small)
are the deterministic size-gate the whole game depends on; everything else
is either printability or the ergonomics/witness surface treatment.
"""

from __future__ import annotations

import math

from params import Params

MIN_FIT_CLEARANCE_MM = 0.4  # cadlib.fits "free" per-side clearance


def functional_warnings(p: Params) -> list[dict]:
    """No captive/moving components here; the size-gate itself is a hard
    assert (an ungated puck is not a draft, it's a different game)."""
    return []


def validate_params(p: Params) -> None:
    # ---- brief.json literal numbers -------------------------------------
    assert p.board_diameter == 190.0, "assay_board diameter must match brief"
    assert p.board_thickness == 34.0, "assay_board thickness must match brief"
    assert p.bore_count == 6, "brief calls for six bores"
    assert p.bore_ring_radius == 62.0, "bore ring radius must match brief"

    assert p.shelf_dia == 34.0, "shelf chamber diameter must match brief"
    assert p.shelf_depth == 6.0, "shelf chamber depth (firmed from ~12mm, see brief.json unstated_in_spec)"
    assert p.throat_dia == 18.0, "throat diameter must match brief"
    assert p.floor_dia == 22.0, "floor chamber diameter must match brief"
    assert p.floor_depth == 11.0, "floor chamber depth must match brief"

    assert p.disc_large_dia == 28.0, "disc_large diameter must match brief"
    assert p.disc_large_height == 9.0, "disc_large height must match brief"
    assert p.disc_small_dia == 14.0, "disc_small diameter must match brief"
    assert p.disc_small_height == 8.0, "disc_small height must match brief"

    assert p.stud_height == 1.2, "ownership studs must stand 1.2mm proud per idea.json"
    assert p.vein_depth == 1.0, "radial vein relief must be 1mm deep per idea.json"
    assert p.collar_depth == 0.8, "witness collar must be 0.8mm deep per idea.json"

    assert tuple(p.owner_marks) == (3, 4, 5, 6), "four owner marks, 3/4/5/6 studs"
    assert p.pieces_per_mark == 3, "each player starts with exactly 3 of each puck size"

    # ---- the deterministic size gate --------------------------------------
    # A disc_large must catch the shelf and must NEVER pass the throat.
    assert p.disc_large_dia < p.shelf_dia - 2 * MIN_FIT_CLEARANCE_MM, (
        "disc_large must drop into the shelf chamber with clearance"
    )
    assert p.disc_large_dia > p.throat_dia, (
        "disc_large must be too wide for the throat -- this is the catch"
    )
    # A disc_small must always pass the throat and never catch on the shelf.
    assert p.disc_small_dia < p.throat_dia - 2 * MIN_FIT_CLEARANCE_MM, (
        "disc_small must clear the throat with margin -- this is the pass-through"
    )
    assert p.disc_small_dia < p.floor_dia - 2 * MIN_FIT_CLEARANCE_MM, (
        "disc_small must fit inside the floor chamber with clearance"
    )

    # ---- bore depth stays inside the slab (measured down from the top
    # face, so against the FULL thickness, not the half) ---------------------
    total_bore_depth = p.shelf_depth + p.throat_depth + p.floor_depth
    assert total_bore_depth < p.board_thickness, (
        "bore stack must not punch through the board's bottom face"
    )
    floor_margin = p.board_thickness - total_bore_depth
    assert floor_margin == 13.0, (
        f"solid slab beneath the floor chamber must match brief.md's 13mm: got {floor_margin}mm"
    )

    # ---- adjacent bores don't intersect -------------------------------------
    chord = 2 * p.bore_ring_radius * math.sin(math.pi / p.bore_count)
    rim_gap = chord - p.shelf_dia
    assert rim_gap > 10.0, f"adjacent shelf rims too close: {rim_gap}mm of stone between them"

    # ---- studs stay on the puck, don't crowd its edge -----------------------
    assert p.stud_ring_radius_large + p.stud_base_large / 2.0 < p.disc_large_dia / 2.0 - 1.0, (
        "disc_large studs must stay clear of the puck's edge"
    )
    assert p.stud_ring_radius_small + p.stud_base_small / 2.0 < p.disc_small_dia / 2.0 - 1.0, (
        "disc_small studs must stay clear of the puck's edge"
    )
    max_marks = max(p.owner_marks)
    stud_arc_large = 2 * math.pi * p.stud_ring_radius_large / max_marks
    stud_arc_small = 2 * math.pi * p.stud_ring_radius_small / max_marks
    assert stud_arc_large > p.stud_base_large, "large-puck studs would overlap at 6 studs"
    assert stud_arc_small > p.stud_base_small, "small-puck studs would overlap at 6 studs"

    # ---- printability -------------------------------------------------------
    assert p.shelf_chamfer > 0 and p.shelf_chamfer < p.shelf_depth, (
        "shelf chamfer must be a modest lead-in, not consume the whole shelf"
    )
    assert p.vein_outer_r < p.board_diameter / 2.0, "vein relief must stay inside the board"
    assert p.vein_inner_r < p.vein_outer_r, "vein relief needs a positive radial span"
