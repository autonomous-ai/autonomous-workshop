"""Runtime checks on Params before any geometry is built.

Draft-mode scope: hard asserts on every load-bearing number from
idea.json / brief.json (bill dimensions, the identical-tile-family
constraint, the shared-ring counts) so a bad edit fails loudly before a
render cycle, not silently in a render nobody looked closely at.
"""
from __future__ import annotations

from params import Params


def functional_warnings(p: Params) -> list[dict]:
    warnings: list[dict] = []
    if p.disc_bore_dia <= p.axle_dia:
        warnings.append({
            "part": "mask_disc_a", "kind": "functional",
            "detail": "disc bore must clear the plinth axle to rotate freely",
            "severity": "warning",
        })
    if p.window_dia <= p.tile_dia:
        warnings.append({
            "part": "mask_disc_a", "kind": "functional",
            "detail": "window must be wider than a tile to pinch it out",
            "severity": "warning",
        })
    return warnings


def validate_params(p: Params) -> None:
    # ---- plinth_ring: owns well diameter / depth / axle diameter --------
    assert p.plinth_dia == 216.0, "plinth_ring diameter is a stated figure"
    assert p.plinth_drum_h == 30.0
    assert p.axle_dia == 24.0
    assert p.axle_rise == 40.0
    assert p.well_dia == 24.0
    assert p.well_depth == 6.0
    assert p.well_count == 10
    assert p.well_ring_r == 80.0
    assert set(p.zenith_indices) == {0, 4, 7}
    assert p.well_dia < p.plinth_dia

    # ---- mask discs: derive bore clearance from the plinth's axle, never
    # restate it independently ------------------------------------------
    assert p.disc_dia == p.plinth_dia, "discs share the plinth's outer diameter"
    assert p.disc_bore_dia - p.axle_dia == 1.0, "0.5mm/side bore clearance on the plinth's axle"
    assert p.window_dia == 38.0
    assert len(p.disc_a_windows) == 6 and len(p.disc_b_windows) == 6 and len(p.disc_c_windows) == 6
    assert p.grip_tab_len == 16.0

    # ---- tiles: identical bbox across all three families -----------------
    assert p.tile_dia == 22.0
    assert p.tile_thickness == 6.0
    assert p.knob_dia == 10.0
    assert p.knob_h == 9.0
    assert p.tile_thickness + p.knob_h == 15.0, "stated 15mm resting height"
    assert p.relief_h == 1.2
    assert p.relief_pocket_r < p.tile_dia / 2.0, "a rim must survive around the relief pocket"
    assert p.tile_counts == {"star_tile": 12, "moon_tile": 10, "void_tile": 8}

    # ---- well/tile fit: both stated independently, never seated_pair'd --
    assert p.well_dia - p.tile_dia == 2.0, "1.0mm/side clearance, both numbers stated"
    # The tile's 6mm body sinks fully into the 6mm-deep well (its top face
    # flush with the ledge the mask discs rest on -- well_depth ==
    # tile_thickness), so the ENTIRE 9mm knob height stands proud above
    # that ledge. `knob_h - well_depth` (the old assertion here) wrongly
    # treats the well as burying part of the KNOB; what it actually buries
    # is the BODY, which is exactly as deep as the well, leaving zero of
    # the knob buried. The true protrusion a resting knob presents to a
    # disc sitting on the ledge is tile_thickness + knob_h - well_depth.
    knob_protrusion_above_ledge = p.tile_thickness + p.knob_h - p.well_depth
    assert knob_protrusion_above_ledge == 9.0, (
        "true resting-knob protrusion above the disc-resting ledge "
        "(6mm body fully buried by the 6mm well, so the full 9mm knob is proud)"
    )
    # mask_disc_a's underside relief must clear that FULL protrusion or a
    # resting knob under any non-window track material jams the disc --
    # "TURN THE SKY" (rotate a mask disc) cannot be performed.
    #
    # AMENDMENT (brief.json top-level `amendments`, arbitrated): the old
    # disc_rim_h (9.0mm) equalled the knob's full 9mm protrusion exactly,
    # so a compliant 9mm-deep relief cut would remove 100% of the track
    # annulus's material at that radius -- severing the ring connecting the
    # disc's bore/hub to its outer rim, not merely under-relieving it. The
    # owner-approved fix raises disc_rim_h to 11.0mm (mask_disc_a/b/c's
    # rim-band height) so a correctly-sized 9mm cut leaves a real remaining
    # wall instead. parts/mask_disc.py builds mask_disc_a's track annulus
    # to this disc_rim_h thickness (not the shorter disc_track_h all three
    # discs otherwise share) specifically so the cut below has that
    # material to work with -- see `_disc_blank`'s docstring.
    assert p.disc_rim_h == 11.0, "AMENDED rim-band height, see brief.json amendments"
    assert p.disc_a_undercut_h >= knob_protrusion_above_ledge, (
        f"mask_disc_a's underside relief ({p.disc_a_undercut_h}mm) must clear the full "
        f"{knob_protrusion_above_ledge}mm a resting knob stands proud of the ledge"
    )
    disc_a_remaining_wall = p.disc_rim_h - p.disc_a_undercut_h
    assert disc_a_remaining_wall >= 1.6, (
        f"mask_disc_a's track annulus must keep a >=1.6mm (print_plan.min_wall_mm) "
        f"remaining wall after the relief cut; got {disc_a_remaining_wall}mm "
        f"(disc_rim_h {p.disc_rim_h}mm - disc_a_undercut_h {p.disc_a_undercut_h}mm)"
    )

    # ---- reserve_column ---------------------------------------------------
    # AMENDED (brief.json top-level amendments, 2nd entry, arbitrated):
    # column_h raised 150.0 -> 306.0mm -- the true height a 24mm bore needs
    # to hold all 20 reserve tiles at their physically-forced 15mm knob-up
    # pitch (6mm body + 9mm knob, no nesting possible; see the tile-family
    # asserts above). 306mm now exceeds the 251mm bed z-limit as a single
    # print, so parts/reserve_column.py builds TWO printed segments
    # (make_reserve_column_lower / _upper) joined by a spigot/socket seam
    # instead of one solid -- see the segment-height asserts below.
    assert p.column_h == 306.0, "AMENDED column height, see brief.json amendments"
    assert p.column_bore_dia - p.tile_dia == 2.0, "shares the tile-diameter clearance"
    assert p.column_slot_w == 9.0
    assert p.column_reserve_tiles == 20
    # Tiles stack knob-up inside the bore; nothing is "buried" here (unlike
    # the well/knob case above), so the true non-interpenetrating pitch is
    # simply one tile's full resting height, body + knob -- the same
    # constraint assemblies/product.py's own placement math already uses
    # (tile_thickness + knob_h directly).
    true_stack_pitch = p.tile_thickness + p.knob_h
    usable_column_h = p.column_h - 2.0 * p.column_top_chamfer
    max_tiles_in_bore = int(usable_column_h // true_stack_pitch)
    assert usable_column_h >= p.column_reserve_tiles * true_stack_pitch, (
        f"reserve_column's {usable_column_h}mm usable bore holds only "
        f"{max_tiles_in_bore} tiles at the true {true_stack_pitch}mm knob-up "
        f"pitch, short of the {p.column_reserve_tiles} setup requires"
    )

    # ---- reserve_column: two-segment print split (NEW, this amendment) ----
    # Segment heights are DERIVED from column_h and column_seg_lower_h, never
    # independently restated, so they can never drift out of sync with the
    # amended total. The lower segment's PRINTED height includes the tenon
    # boss proud of its nominal taper top; the upper segment's PRINTED
    # height is its nominal taper span alone (the socket is a pocket, not
    # added height). Both must individually clear the 251mm bed z-limit
    # (gate.py's usable bed, BED_Z_MM 256 - BED_MARGIN_MM 5) -- the entire
    # reason this part was split in the first place.
    assert p.column_seg_lower_h == 180.0, "brief-suggested lower segment height"
    upper_h = p.column_h - p.column_seg_lower_h
    assert upper_h == 126.0, "brief-suggested cap segment height (306 - 180)"
    lower_printed_h = p.column_seg_lower_h + p.column_tenon_h
    upper_printed_h = upper_h
    BED_USABLE_Z_MM = 251.0
    assert lower_printed_h <= BED_USABLE_Z_MM, (
        f"reserve_column_lower's printed height ({lower_printed_h}mm, "
        f"including its {p.column_tenon_h}mm tenon boss) must fit the "
        f"{BED_USABLE_Z_MM}mm usable bed"
    )
    assert upper_printed_h <= BED_USABLE_Z_MM, (
        f"reserve_column_upper's printed height ({upper_printed_h}mm) must "
        f"fit the {BED_USABLE_Z_MM}mm usable bed"
    )
    # The spigot register is sized off the column's own taper width at the
    # seam (parts/reserve_column.py's _width_at), never an independent
    # number, so it cannot mismatch the two segments' actual cross-sections.
    # Assert here only that the derived boss geometry leaves a real wall
    # around the 24mm bore (print_plan.min_wall_mm = 1.6mm) once the bore is
    # cut through it -- the narrowest point in either segment.
    seam_width = p.column_base + (p.column_shaft - p.column_base) * (
        p.column_seg_lower_h / p.column_h)
    tenon_w = seam_width - 2.0 * p.column_tenon_offset
    tenon_wall = (tenon_w - p.column_bore_dia) / 2.0
    assert tenon_wall >= 1.6, (
        f"reserve_column's spigot boss ({tenon_w:.1f}mm square) must keep a "
        f">=1.6mm wall around the 24mm bore; got {tenon_wall:.2f}mm"
    )

    # ---- score_rail ---------------------------------------------------
    assert p.rail_len == 130.0 and p.rail_w == 30.0 and p.rail_h == 20.0
    assert p.rail_slot_w == 6.6 and p.rail_slot_depth == 11.0
    assert abs((p.rail_slot_w - p.tile_thickness) - 0.6) < 1e-6, "0.3mm/side, tight but stated as-is"
    assert p.rail_slot_depth == p.tile_dia / 2.0, "a standing tile sinks exactly its radius"

    # ---- FDM printability sanity ----------------------------------------
    assert p.disc_dia + p.grip_tab_len == 232.0, "232mm bbox: rim + one grip-tab projection"
    assert p.disc_dia + p.grip_tab_len <= 246.0, "widest mask disc still fits the 246mm bed"
    assert p.plinth_drum_h + p.axle_rise <= 251.0

    # ---- mask disc stack (interfaces 4/5, AMENDED) -----------------------
    # Full 3-disc standalone stack height grows 27mm -> 33mm with the rim
    # amendment (assemblies/product.py stacks each disc disc_rim_h apart);
    # bore-engagement depth (3 discs x disc_track_h) stays the axle's
    # stated 18mm either way, per brief.json interfaces[3]'s explicit note
    # that this split is unaffected by the rim-height amendment.
    assert 3 * p.disc_rim_h == 33.0, "amended 3-disc stack height"
    assert 3 * p.disc_track_h == 18.0, "bore engagement unaffected by the rim amendment"
    assert 3 * p.disc_track_h <= p.axle_rise, "engagement must fit the 40mm axle"
