"""All dimensions for Deep Claim. Edit values here, not inside geometry.

Every number here traces to a brief.json field; see validation.py for the
asserts and brief.json's own `unstated_in_spec` for the handful of numbers
(throat depth, shelf-rim chamfer) the brief left implicit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Params:
    # AI_EDITABLE: dimensions only. Add new fields below as features need them.

    # ---- assay_board: overall slab -------------------------------------
    board_diameter: float = 190.0
    board_thickness: float = 34.0
    bore_count: int = 6
    bore_ring_radius: float = 62.0

    # ---- assay_board: one bore, top to bottom --------------------------
    shelf_dia: float = 34.0
    shelf_depth: float = 6.0
    throat_dia: float = 18.0
    throat_depth: float = 4.0          # not stated in brief.json; picked so
                                        # total bore depth (21mm) clears the
                                        # 34mm slab with 13mm solid beneath.
    floor_dia: float = 22.0
    floor_depth: float = 11.0
    shelf_chamfer: float = 1.0         # 1mm x 45deg lead-in, not in
                                        # idea.json — printability only.

    # ---- assay_board: surface treatment ---------------------------------
    vein_depth: float = 1.0            # 1mm-deep radial vein relief
    vein_width: float = 4.0
    vein_inner_r: float = 20.0
    vein_outer_r: float = 90.0
    collar_depth: float = 0.8          # witness collar around each shelf rim
    collar_width: float = 3.0

    # ---- pucks ------------------------------------------------------------
    disc_large_dia: float = 28.0
    disc_large_height: float = 9.0
    disc_small_dia: float = 14.0
    disc_small_height: float = 8.0

    # ---- ownership studs (identical geometry across all 4 marks; only the
    # count differs) -------------------------------------------------------
    stud_height: float = 1.2
    stud_base_large: float = 3.2
    stud_base_small: float = 2.0
    stud_ring_radius_large: float = 8.0
    stud_ring_radius_small: float = 4.0

    owner_marks: tuple[int, ...] = (3, 4, 5, 6)
    pieces_per_mark: int = 3           # qty of each of {large, small} per mark
