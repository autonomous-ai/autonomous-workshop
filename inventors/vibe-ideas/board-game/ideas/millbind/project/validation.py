"""Runtime checks on Params before any geometry is built.

Hard asserts on every load-bearing number from idea.json / brief.json (bill
dimensions, the shared tooth/pin geometry every mate derives from, the bill
counts) so a bad edit fails loudly before a render cycle, not silently in a
render nobody looked closely at.
"""
from __future__ import annotations

import math

from params import Params


def functional_warnings(p: Params) -> list[dict]:
    warnings: list[dict] = []
    if p.bore_d <= p.pin_d:
        warnings.append({
            "part": "gear_low", "kind": "functional",
            "detail": "every gear bore must clear the yard_board pin to seat and rotate",
            "severity": "warning",
        })
    if p.gear_high_h != p.pin_h:
        warnings.append({
            "part": "gear_high", "kind": "functional",
            "detail": "a full-engagement piece must span the whole pin height "
                      "or it wobbles instead of standing flush",
            "severity": "warning",
        })
    if not (2.0 * p.root_r < p.pin_pitch < 2.0 * p.outer_r):
        warnings.append({
            "part": "gear_low", "kind": "functional",
            "detail": "adjacent-pin tooth mesh requires root-circle clearance "
                      "and outer-circle overlap at the shared pin pitch",
            "severity": "warning",
        })
    if p.crown_d >= 2.0 * p.outer_r:
        warnings.append({
            "part": "mill_gear_tri", "kind": "functional",
            "detail": "the millstone crown must not overhang the tooth circle "
                      "or it fouls a neighbouring pin",
            "severity": "warning",
        })
    if p.pellet_hole_d <= p.spindle_rod_d:
        warnings.append({
            "part": "grain_pellet", "kind": "functional",
            "detail": "pellet hole must clear the spindle rod to thread on",
            "severity": "warning",
        })
    return warnings


def validate_params(p: Params) -> None:
    # ---- yard_board: OWNS pin diameter, pin height, pin spacing -----------
    assert p.board_vertex_r * 2.0 == 230.0, "230mm corner-to-corner, stated directly"
    flat_to_flat = p.board_vertex_r * 2.0 * math.sqrt(3) / 2.0
    assert abs(flat_to_flat - 200.0) < 1.0, "199.2mm computed flat-to-flat, rounded to 200mm"
    assert p.slab_t == 12.0
    assert p.pin_h == 30.0
    assert p.slab_t + p.pin_h == 42.0, "42mm stated overall board height, 12mm slab + 30mm pin"
    assert p.pin_d == 8.0
    assert p.pin_pitch == 30.0, "pin spacing == every gear's pitch-circle diameter"
    assert p.sill_d == p.pin_d + 6.0 == 14.0, "1.2mm sill ring is 3mm wider radius each side"
    assert p.sill_h == 1.2
    assert p.rib_h == 1.0, "the shallower of the board's two reliefs (vs 1.2mm sill)"
    assert p.board_skirt_chamfer == 3.0

    n_pins = 1 + sum(6 * k for k in range(1, p.n_rings + 1))
    assert n_pins == 37, "centre + ring6 + ring12 + ring18 == 37 pins"
    assert p.n_rings == 3
    n_yard_pins = 6 * p.n_rings  # the outermost ring only
    assert n_yard_pins == 18, "only the 18 outer-ring pins carry the sill"

    # ---- shared gear-tooth form: every gear/millstone/crank cuts this -----
    assert p.module == 2.5
    assert p.teeth == 12
    assert p.pitch_r == p.module * p.teeth / 2.0 == 15.0
    assert p.addendum == p.module == 2.5
    assert p.dedendum == 1.25 * p.module == 3.125
    assert p.outer_r == p.pitch_r + p.addendum == 17.5, "35mm OD, stated directly"
    assert abs(p.root_r - (p.pitch_r - p.dedendum)) < 1e-9 and abs(p.root_r - 11.875) < 1e-9
    assert p.bore_d == 8.6, "shared bore, every full/partial-height piece"

    # ---- gear_low: 35 x 35 x 10mm, partial engagement ----------------------
    assert p.gear_low_h == 10.0
    assert 2.0 * p.outer_r == 35.0, "gear_low bbox x/y"
    assert p.pin_h - p.gear_low_h == 20.0, "20mm of bare pin exposed above a seated gear_low"

    # ---- gear_high: 35 x 35 x 30mm, full engagement ------------------------
    assert p.gear_high_h == 30.0 == p.pin_h, "spans the full pin, no stub exposed"
    assert p.gear_high_column_d > p.bore_d, "column must leave wall around the shared bore"
    assert p.gear_high_teeth_h == 10.0

    # ---- gear_tandem / millstone-barrel / crank-barrel share this barrel --
    assert p.barrel_h == 30.0 == p.pin_h, "full pin height"
    assert p.barrel_rim == 1.0
    assert p.barrel_h - 2.0 * p.barrel_rim == 28.0, "~28mm face, the rest is untoothed lead-in"

    # ---- millstones: 35 x 35 x 48mm -----------------------------------------
    # (round-2 repair: crown_d dropped 34.0 -> 22.0mm -- 34mm satisfied
    # idea.json's qualitative "crown does not overhang the tooth circle"
    # rule in isolation but ignored the 30mm pin_pitch shared with every
    # gear; see params.py's crown_d note and the crown-vs-pin-pitch assert
    # below)
    assert p.crown_d == 22.0
    assert p.crown_d < 2.0 * p.outer_r, "crown must not overhang the 35mm tooth circle"
    # The binding constraint: a millstone's crown must also clear a
    # neighbouring pin's own tooth-OD envelope at the shared 30mm pitch, or
    # (a) two millstones on adjacent yard pins interpenetrate and (b)
    # nothing can travel axially past a meshed millstone to seat/lift off
    # the neighbouring pin. crown_r + outer_r <= pin_pitch is the boundary;
    # kept with >=1mm of real radial margin below it, not sitting on it.
    crown_pin_pitch_limit = 2.0 * (p.pin_pitch - p.outer_r)
    assert crown_pin_pitch_limit == 25.0
    assert p.crown_d <= crown_pin_pitch_limit - 2.0, (
        "crown must clear a neighbouring pin's tooth-OD envelope at the "
        "30mm pin pitch, with >=1mm of real radial margin below the limit"
    )
    assert p.crown_h == 6.0
    assert p.crown_furrow_depth == 1.2
    # hub_across_flats: worst-case (triangular) hub circumradius must stay
    # under the (now smaller) crown radius or the hub overhangs the crown
    # disc beneath it -- see the hub_circumradius_tri assert below.
    assert p.hub_across_flats == 9.0
    assert p.hub_h == 12.0
    assert p.millstone_h == p.barrel_h + p.crown_h + p.hub_h == 48.0
    assert p.mill_gear_flats == {
        "mill_gear_tri": 3, "mill_gear_square": 4,
        "mill_gear_penta": 5, "mill_gear_hex": 6,
    }

    # ---- crank_gear: 46 x 35 x 91mm -----------------------------------------
    # (round-1 repair: cap/arm/knob riser-mounted above the millstone
    # envelope -- see params.py's crank_riser*/crank_gusset_rise_h notes)
    assert p.crank_cap_h == 3.0
    assert p.crank_knob_d == 14.0
    assert p.crank_knob_standoff == 22.0
    assert p.crank_arm_offset == 21.0
    assert p.crank_h == (
        p.barrel_h + p.crank_riser1_h + p.crank_riser2_h + p.crank_cap_h
        + p.crank_gusset_rise_h + p.crank_knob_standoff
    ) == 91.0
    crank_footprint_x = p.outer_r + p.crank_arm_offset + p.crank_knob_d / 2.0
    assert abs(crank_footprint_x - 45.5) < 1e-9, "17.5mm barrel radius + 21mm arm + 7mm knob radius"
    assert abs(crank_footprint_x - 46.0) < 1.0, "brief's stated 46mm x bbox, rounded"
    assert p.crank_arrow_relief == 1.2

    # crank riser1 must clear the 48mm millstone envelope (with margin)
    # before the crank's cap/arm/knob are allowed to widen back out, since
    # a millstone meshing straight into the crank's yard pin is an explicit
    # legal placement (idea.json's DIRECTION rule) at the 30mm pin pitch.
    assert p.barrel_h + p.crank_riser1_h >= p.millstone_h + 1.0, (
        "riser1 must clear the millstone's full 48mm height with margin "
        "before the crank cap/arm/knob widen past the barrel's root_r"
    )
    # While riser1 is inside the millstone's 30..48mm z-band, it is held at
    # the barrel's own root_r (11.875mm) -- check that radius clears a
    # meshed millstone's crown (17mm) and worst-case (triangular) hub
    # circumradius (16mm) at the shared 30mm pin pitch, both with margin.
    hub_circumradius_tri = (p.hub_across_flats / 2.0) / math.cos(math.pi / 3.0)
    assert abs(hub_circumradius_tri - 9.0) < 1e-9
    assert p.root_r + p.crown_d / 2.0 < p.pin_pitch, "riser vs crown clearance"
    assert p.root_r + hub_circumradius_tri < p.pin_pitch, "riser vs hub clearance"
    # The hub must not overhang the (now smaller) crown disc it sits on --
    # a hard unsupported-overhang defect, not just a clearance one.
    assert hub_circumradius_tri < p.crown_d / 2.0, "hub must not overhang its own crown disc"

    # Both riser stages must taper no steeper than 45deg from vertical (the
    # print_plan's own stated limit) so every stage is carried by solid
    # material below it and self-supports without print supports.
    assert (p.outer_r - p.root_r) <= p.crank_riser2_h, "riser2 outboard face <=45deg"
    gusset_dx = (p.crank_arm_offset + p.crank_knob_d / 2.0) - p.outer_r
    assert abs(gusset_dx - 10.5) < 1e-9, "10.5mm cap-edge-to-knob-edge reach"
    assert gusset_dx <= p.crank_gusset_rise_h, "arm gusset outboard face <=45deg"

    # ---- grain_pellet: 15 x 15 x 5mm -----------------------------------------
    assert p.pellet_d == 15.0
    assert p.pellet_h == 5.0
    assert p.pellet_hole_d == 9.0

    # ---- sack_spindle: 40 x 40 x 70mm -----------------------------------------
    assert p.spindle_base_d == 40.0
    assert p.spindle_base_h == 8.0, "unstated in idea.json; own structural choice"
    assert p.spindle_rod_d == 8.5
    assert p.spindle_rod_h == 62.0
    assert p.spindle_h == p.spindle_base_h + p.spindle_rod_h == 70.0
    assert p.spindle_capacity == 12
    assert p.spindle_capacity * p.pellet_h == 60.0, "12 pellets x 5mm"
    thumbnail_clear = p.spindle_rod_h - p.spindle_capacity * p.pellet_h
    assert thumbnail_clear == 2.0, "stated 2mm of rod left clear for a thumbnail pinch"
    assert p.spindle_chevron_depth == 1.0

    # ---- granary_bin: 70 x 50 x 25mm -----------------------------------------
    assert p.bin_l == 70.0
    assert p.bin_w == 50.0
    assert p.bin_h == 25.0
    assert p.bin_wall == 3.0
    assert p.bin_scallop_r == 12.0
    assert p.bin_chevron_depth == 1.0

    # ---- interfaces (brief.json's `## Interfaces`) ---------------------------
    # Pin/bore, partial engagement (gear_low <-> yard_board): 0.3mm/side, both
    # numbers idea.json's own explicit figures, kept as stated even though
    # flagged tighter than this pipeline's usual 0.4mm minimum.
    clearance_partial = (p.bore_d - p.pin_d) / 2.0
    assert abs(clearance_partial - 0.3) < 1e-9

    # Pin/bore, full engagement -- every full-height piece shares the same
    # bore/pin pair, so the same 0.3mm/side clearance applies uniformly.
    assert p.gear_high_h == p.barrel_h == p.millstone_h - p.crown_h - p.hub_h == p.pin_h

    # Tooth-to-tooth mesh: adjacent pins mesh correctly by construction
    # because the pin pitch equals the shared pitch-circle diameter, and the
    # tooth profile actually spans the pitch circle (root < pitch < outer).
    assert p.pin_pitch == 2.0 * p.pitch_r == 30.0
    assert p.root_r < p.pitch_r < p.outer_r
    assert 2.0 * p.root_r < p.pin_pitch < 2.0 * p.outer_r, (
        "meshing at the true 30mm pin pitch: dedendum clearance at the root, "
        "addendum overlap at the tip"
    )

    # Rod/hole, threaded stack (grain_pellet <-> sack_spindle): 0.25mm/side,
    # both idea.json's own explicit figures, flagged tight but kept as-is.
    clearance_pellet = (p.pellet_hole_d - p.spindle_rod_d) / 2.0
    assert abs(clearance_pellet - 0.25) < 1e-9

    # ---- bill counts ---------------------------------------------------------
    assert p.n_gear_low == 14
    assert p.n_gear_high == 7
    assert p.n_gear_tandem == 3
    assert p.n_grain_pellet == 28
    assert p.n_sack_spindle == 4

    # ---- FDM printability sanity ----------------------------------------------
    assert p.board_vertex_r * 2.0 <= 246.0, "hex board fits the 246mm bed"
    assert flat_to_flat <= 246.0
    assert p.slab_t + p.pin_h <= 251.0
    assert p.crank_h <= 251.0
    assert p.millstone_h <= 251.0
