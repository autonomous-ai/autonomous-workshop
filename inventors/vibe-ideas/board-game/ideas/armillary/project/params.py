"""All dimensions for Armillary. Every number here traces to idea.json /
brief.json; see spec.md for the pointer. Geometry code never hardcodes a
number that belongs here.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Params:
    # AI_EDITABLE: dimensions only.

    # ---- plinth_ring -------------------------------------------------
    plinth_dia: float = 216.0
    plinth_drum_h: float = 30.0
    plinth_skirt_chamfer: float = 8.0
    axle_dia: float = 24.0
    axle_rise: float = 40.0

    well_ring_r: float = 80.0
    well_count: int = 10
    well_dia: float = 24.0
    well_depth: float = 6.0
    zenith_indices: tuple = (0, 4, 7)
    zenith_collar_h: float = 1.2
    zenith_collar_inner_r: float = 13.0
    zenith_collar_outer_r: float = 17.0

    index_groove_dia: float = 3.0
    index_groove_depth: float = 1.2
    constellation_relief_depth: float = 1.2

    # ---- mask_disc_a/b/c ----------------------------------------------
    disc_dia: float = 216.0
    disc_track_h: float = 6.0          # window-track band thickness (b/c
                                        # profile, and the bore-engagement
                                        # depth all three discs share on the
                                        # axle -- unaffected by the rim-band
                                        # amendment; see interfaces 4/5)
    disc_rim_h: float = 11.0           # outer rim band thickness (stiffener)
                                        # AMENDED from 9.0 -> 11.0 (see
                                        # brief.json's top-level amendments):
                                        # the +2mm gives mask_disc_a's
                                        # underside relief undercut (below) a
                                        # compliant remaining wall instead of
                                        # removing the track band entirely.
    disc_rim_band_w: float = 10.0      # radial width of the outer rim band
    disc_bore_dia: float = 25.0        # rides plinth's 24mm axle, 0.5mm/side
    window_dia: float = 38.0
    grip_tab_len: float = 16.0         # projection past the rim
    disc_a_windows: tuple = (0, 1, 2, 3, 4, 6)
    disc_b_windows: tuple = (0, 1, 2, 3, 6, 7)
    disc_c_windows: tuple = (0, 1, 3, 5, 6, 8)
    # Relief so a resting tile's knob never fouls disc_a while rotating:
    # must clear the FULL knob protrusion above the ledge (tile_thickness +
    # knob_h - well_depth = 9.0mm; see validation.py), not a partial
    # estimate. mask_disc_a's track annulus is built to disc_rim_h (not the
    # shorter disc_track_h) precisely so this 9mm-deep cut leaves a real
    # (disc_rim_h - disc_a_undercut_h = 2.0mm) remaining wall instead of
    # severing the ring that connects the disc's hub to its outer rim.
    disc_a_undercut_h: float = 9.0
    witness_notch_w: float = 4.0
    witness_notch_depth: float = 3.0

    # ---- tiles (star_tile / moon_tile / void_tile) --------------------
    # LOAD-BEARING: outline, thickness, rim and back are shared bit-for-bit
    # by all three families. Only the face relief motif differs.
    tile_dia: float = 22.0
    tile_thickness: float = 6.0
    knob_dia: float = 10.0
    knob_h: float = 9.0
    relief_h: float = 1.2
    relief_pocket_r: float = 9.0       # < tile_r(11) so a 2mm rim survives untouched
    tile_counts: dict = field(default_factory=lambda: {
        "star_tile": 12, "moon_tile": 10, "void_tile": 8,
    })

    # ---- reserve_column -------------------------------------------------
    # AMENDED (see brief.json's top-level amendments, 2nd entry): 150 -> 306mm
    # -- the true height a 24mm bore needs to hold all 20 reserve tiles at
    # their physically-forced 15mm knob-up pitch (20*15 + 6mm chamfer
    # allowance = 306). This exceeds the 251mm bed z-limit as one print, so
    # the column is now built as TWO printed segments (make_reserve_column_
    # lower / _upper in parts/reserve_column.py) joined by a square spigot/
    # socket register seam -- see column_seg_lower_h / column_tenon_*
    # below. Neither printed segment restates column_h; both derive their
    # own height from it (see validate_params).
    column_base: float = 70.0
    column_shaft: float = 46.0
    column_h: float = 306.0
    column_bore_dia: float = 24.0
    column_slot_w: float = 9.0
    column_top_chamfer: float = 3.0
    column_reserve_tiles: int = 20     # 30 total minus 10 seeded into wells

    # ---- reserve_column: two-segment print split (NEW, this amendment) ----
    # Nominal seam height (in the assembled column's own Z frame, 0 at the
    # 70mm base): the brief suggests ~180mm lower / ~126mm cap, both
    # comfortably under the 251mm bed limit even after the tenon boss is
    # added on top of the lower segment. The upper segment's own height is
    # DERIVED (column_h - column_seg_lower_h), never restated.
    column_seg_lower_h: float = 180.0
    # Square spigot register: a reduced-cross-section boss on the lower
    # segment's cut top face nests into a matching blind socket in the upper
    # segment's bottom face. Sized off the column's own taper width at the
    # seam (derived in parts/reserve_column.py), never an independent
    # number, so the register can never mismatch the two segments' actual
    # cross-sections. The 24mm bore and 9mm slot both run straight through
    # the tenon and socket unmodified -- the register only touches the OUTER
    # wall, never the tile channel.
    column_tenon_h: float = 8.0            # boss height / socket depth
    column_tenon_offset: float = 2.5       # boss inset per side from the
                                            # nominal taper width at the seam
    column_tenon_clearance: float = 0.3    # socket oversize per side vs the
                                            # boss (a snug register, glued)

    # ---- score_rail (x4, one per seat) ---------------------------------
    rail_len: float = 130.0
    rail_w: float = 30.0
    rail_h: float = 20.0
    rail_slot_w: float = 6.6
    rail_slot_depth: float = 11.0
    rail_slot_len: float = 108.0
    rail_zenith_step_h: float = 4.0
    rail_finial_r: float = 8.0
    rail_finial_len: float = 10.0
