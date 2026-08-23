"""All dimensions for Millbind. Every number here traces to idea.json /
brief.json; see spec.md for the pointer, and validation.py for the asserts.
Geometry code (parts/, features/, assemblies/) never hardcodes a number that
belongs here.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Params:
    # AI_EDITABLE: dimensions only.

    # ---- yard_board: OWNS pin diameter, pin height, pin spacing ----------
    board_vertex_r: float = 115.0      # 230mm corner-to-corner / 2
    slab_t: float = 12.0               # board floor thickness
    pin_d: float = 8.0                 # OWNED here; every bore derives from it
    pin_h: float = 30.0                # OWNED here
    pin_pitch: float = 30.0            # OWNED here == every gear pitch circle dia
    sill_d: float = 14.0               # pin_d + 6mm raised sill ring
    sill_h: float = 1.2
    rib_h: float = 1.0                 # plank rib relief (the shallower of the
                                        # board's two reliefs -> the bill's relief_mm)
    board_skirt_chamfer: float = 3.0
    n_rings: int = 3                   # centre + ring1(6) + ring2(12) + ring3(18) = 37

    # ---- shared gear tooth form: every gear/millstone/crank cuts this ------
    module: float = 2.5
    teeth: int = 12
    pitch_r: float = 15.0              # module * teeth / 2
    addendum: float = 2.5              # == module
    dedendum: float = 3.125            # == 1.25 * module
    outer_r: float = 17.5              # pitch_r + addendum -> 35mm OD
    root_r: float = 11.875             # pitch_r - dedendum -> 23.75mm root disk
    bore_d: float = 8.6                # shared bore, every full/partial-height piece

    # ---- gear_low ------------------------------------------------------
    gear_low_h: float = 10.0           # engages only the bottom 10mm of a 30mm pin

    # ---- gear_high -------------------------------------------------------
    gear_high_h: float = 30.0          # spans the FULL pin, no stub exposed
    gear_high_column_d: float = 16.0   # unstated in idea.json; own choice
    gear_high_teeth_h: float = 10.0    # top tooth band

    # ---- gear_tandem / millstone-barrel / crank-barrel share this barrel --
    barrel_h: float = 30.0             # full pin height
    barrel_rim: float = 1.0            # untoothed lead-in rim, top + bottom

    # ---- millstone crown/hub (mill_gear_tri/square/penta/hex) -----------
    # Repair (round 2): 34mm was the brief-writer's own free choice within
    # idea.json's qualitative "crown does not overhang the tooth circle"
    # rule (satisfied at 34 < 35mm) -- but it silently ignored the OTHER
    # binding constraint, the 30mm pin_pitch shared with every gear. Two
    # millstones on neighbouring yard pins put their crown radii and their
    # neighbour's 17.5mm tooth-OD envelope in collision unless
    # crown_r + outer_r <= pin_pitch, i.e. crown_d <= 2*(pin_pitch-outer_r)
    # = 25.0mm -- and every other piece (crank/gear_high/gear_tandem/
    # gear_low) needs that same radial clearance to travel axially past a
    # neighbouring millstone to seat or lift off its own pin. 22.0mm keeps
    # 1.5mm of real radial margin below the 25.0mm limit (see validate()'s
    # new crown-vs-pin-pitch assert) while staying 13mm inside the 35mm
    # tooth OD, so both constraints hold with margin, not at the boundary.
    crown_d: float = 22.0
    crown_h: float = 6.0
    crown_furrow_depth: float = 1.2
    # hub_across_flats: the worst-case (triangular) hub's circumradius
    # equals hub_across_flats exactly (see validate()'s hub_circumradius_tri
    # derivation), so it must stay under the new, smaller crown_d/2=11.0mm
    # radius or the hub overhangs the crown disc beneath it (was fine at
    # the old 34mm crown -- 16mm circumradius inside a 17mm crown radius --
    # but a hard overhang/support defect at the new 11mm crown radius).
    # 9.0mm keeps a 2.0mm margin inside the new crown radius.
    hub_across_flats: float = 9.0
    hub_h: float = 12.0

    # ---- crank_gear ------------------------------------------------------
    crank_cap_h: float = 3.0
    crank_knob_d: float = 14.0
    crank_knob_standoff: float = 22.0
    crank_arm_offset: float = 21.0     # knob-centre from the gear axis
    crank_arrow_relief: float = 1.2

    # Repair (round 1): the cap/arm/knob used to sit directly on top of the
    # 30mm-tall barrel (z=30..55), which put the 28.9mm knob-sweep radius
    # into the same z-band (30..48) as a neighbouring millstone's 34mm crown
    # (r=17mm, z30..36) and hex hub (r=16mm, z36..48) at the 30mm pin pitch
    # -- a mandatory game position (a millstone meshing straight into the
    # crank is an explicit legal placement in idea.json's own DIRECTION
    # rule) -- and it also cantilevered the arm 10.5mm into open air with
    # nothing below it (printability failure). Fix: carry the cap/arm/knob
    # on a solid riser that (a) stays radially inside the 30mm pin pitch
    # minus the millstone's crown/hub radii while it passes through their
    # 30..48mm z-band, so it never fouls a meshed millstone, and (b) never
    # steps its own radius out faster than 45deg from vertical, so every
    # stage is carried by solid material below it, no supports needed.
    # crank_knob_d/crank_knob_standoff/crank_arm_offset/crank_cap_h (all
    # idea.json-derived or already-fixed sizes) are unchanged by this fix.
    crank_riser1_h: float = 19.0       # barrel top (z=30) to z=49 -- 1mm
                                        # above the 48mm millstone envelope,
                                        # held at the barrel's own root_r
                                        # (11.875mm) the whole way, well
                                        # inside the 30mm-pitch clearance
                                        # against a meshed millstone's crown
                                        # (17mm) or hub (<=16mm)
    crank_riser2_h: float = 6.0        # z=49..55: widens root_r (11.875mm)
                                        # to the cap's outer_r (17.5mm);
                                        # dx=5.625mm over dz=6mm, <45deg,
                                        # entirely above the millstone
                                        # envelope so radius is unconstrained
    crank_gusset_rise_h: float = 11.0  # cap top (z=58) to knob base (z=69):
                                        # a solid triangular gusset from the
                                        # cap's edge (17.5mm) out to the
                                        # knob's outer edge (28mm); dx=10.5mm
                                        # over dz=11mm, <45deg outboard face,
                                        # so the knob's whole footprint is
                                        # carried by solid material below it

    # ---- grain_pellet ------------------------------------------------------
    pellet_d: float = 15.0
    pellet_h: float = 5.0
    pellet_hole_d: float = 9.0

    # ---- sack_spindle ------------------------------------------------------
    spindle_base_d: float = 40.0
    spindle_base_h: float = 8.0        # unstated in idea.json; own choice
    spindle_rod_d: float = 8.5
    spindle_rod_h: float = 62.0
    spindle_capacity: int = 12

    # ---- granary_bin ------------------------------------------------------
    bin_l: float = 70.0
    bin_w: float = 50.0
    bin_h: float = 25.0
    bin_wall: float = 3.0
    bin_scallop_r: float = 12.0
    bin_chevron_depth: float = 1.0     # brief's stated relief_mm for granary_bin

    # chevron water-texture relief, shared depth figure -> both bill lines
    # state relief_mm = 1.0mm for sack_spindle and granary_bin
    spindle_chevron_depth: float = 1.0  # brief's stated relief_mm for sack_spindle

    # ---- bill counts -------------------------------------------------------
    n_gear_low: int = 14
    n_gear_high: int = 7
    n_gear_tandem: int = 3
    n_grain_pellet: int = 28
    n_sack_spindle: int = 4
    mill_gear_flats: dict = field(default_factory=lambda: {
        "mill_gear_tri": 3, "mill_gear_square": 4,
        "mill_gear_penta": 5, "mill_gear_hex": 6,
    })

    # ---- derived, read-only convenience (never re-typed by callers) -------
    @property
    def gear_high_h_total(self) -> float:
        return self.gear_high_h

    @property
    def millstone_h(self) -> float:
        return self.barrel_h + self.crown_h + self.hub_h   # 48mm

    @property
    def crank_h(self) -> float:
        return (
            self.barrel_h + self.crank_riser1_h + self.crank_riser2_h
            + self.crank_cap_h + self.crank_gusset_rise_h
            + self.crank_knob_standoff
        )  # 91mm -- see crank_riser*/crank_gusset_rise_h notes above

    @property
    def spindle_h(self) -> float:
        return self.spindle_base_h + self.spindle_rod_h   # 70mm

    @property
    def barrel_teeth_z0(self) -> float:
        return self.barrel_rim

    @property
    def barrel_teeth_z1(self) -> float:
        return self.barrel_h - self.barrel_rim
