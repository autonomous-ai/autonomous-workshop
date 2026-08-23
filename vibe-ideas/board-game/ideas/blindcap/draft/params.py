"""All dimensions for blindcap, mm. Every number traces to brief.json /
brief.md. Where the brief itself says a figure is unstated_in_spec, the
comment says so -- draft mode still gives it a real, considered number.
"""
import math

# ---------------------------------------------------------------------
# loam_tile -- board, 4x, one per player. 3x3 grid of sockets at 44mm
# pitch (OWNED here; every stool/pin clearance derives from it).
# ---------------------------------------------------------------------
TILE_SIZE = 132.0          # brief.json bbox_mm
TILE_T = 28.0               # brief.json bbox_mm
SOCKET_PITCH = 44.0         # unstated_in_spec: derived from cap dia + margin
SOCKET_COLS = 3
SOCKET_ROWS = 3

BORE_D = 12.8                # seated_pair(12, 'free') slot side -- loam_tile OWNS this
BORE_DEPTH = 20.0            # unstated_in_spec
COLLAR_OD = 20.0             # brief.json: 2mm collar, 20mm OD
COLLAR_H = 2.0                # brief.json's own stated figure

PROBE_HOLE_D = 5.2            # draft figure: clears the pin's 4mm hex shaft
PROBE_OFFSET = 13.0           # unstated_in_spec: ~10-13mm off socket centre;
                               # kept clear of the 20mm-OD collar (radius 10)
                               # so a proud pin's disc head doesn't graze it
PROBE_ANGLE_DEG = 35.0        # unstated_in_spec: midpoint of 30-40deg range
PROBE_UPPER_BELOW_SHOULDER = 8.0   # brief.json: upper groove band depth below collar top
PROBE_LOWER_BELOW_SHOULDER = 16.0  # brief.json: lower groove band depth below collar top

TILE_CRAQUELURE_RELIEF = 1.4   # brief.json's own stated figure

# dovetail: symmetric-about-midpoint tab/slot pair per edge (self-mating,
# any edge mates any edge -- see loam_tile.py for the CCW-consistent proof).
DOVETAIL_V0 = 10.0            # tab/slot start, distance from edge midpoint
DOVETAIL_V1 = 30.0            # tab/slot end
DOVETAIL_DEPTH = 6.0          # how far the tab protrudes / slot cuts
DOVETAIL_FLARE = 2.0          # tip is this much wider than the root, each side
DOVETAIL_CLEARANCE = 0.4      # slot-side-only, per ergonomics_check.MIN_SEAT_CLEARANCE_MM

# ---------------------------------------------------------------------
# stool_<species>_p<owner> -- 16 names, ALL IDENTICAL above the shoulder
# line (cap, boss, neck, shoulder). This is the load-bearing constraint;
# every one of these numbers is used by every one of the 16 builds.
# ---------------------------------------------------------------------
STOOL_CAP_D = 34.0             # unstated_in_spec, matches bbox_mm[0:2]
STOOL_CAP_T = 8.0               # unstated_in_spec
STOOL_BOSS_D = 16.0             # unstated_in_spec -- claim_crown's bore derives from this
STOOL_BOSS_H = 3.0              # unstated_in_spec
STOOL_NECK_D = 12.0             # unstated_in_spec -- "a finger's height" shadow gap
STOOL_NECK_H = 14.0             # unstated_in_spec
STOOL_SHOULDER_D = 18.0         # unstated_in_spec -- rests on loam_tile's collar
STOOL_SHOULDER_H = 2.0          # unstated_in_spec -- matches COLLAR_H
STOOL_SHANK_D = 12.0            # seated_pair(12, 'free') piece side -- STOOL OWNS this
STOOL_SHANK_H = 22.0            # brief.json: 2mm collar pass-through + 20mm bore

STOOL_H = STOOL_SHANK_H + STOOL_SHOULDER_H + STOOL_NECK_H + STOOL_CAP_T + STOOL_BOSS_H
assert STOOL_H == 49.0, "must match brief.json bbox_mm[2] exactly"

# growth rings, top of cap (brief.json's stated relief_mm)
STOOL_RING_RELIEF = 0.8
STOOL_RING_RADII = (6.0, 10.0, 14.0)   # unstated_in_spec: 3 concentric rings
STOOL_RING_WIDTH = 1.0

# gill ribs, underside of cap brim (brief.json's own stated count/figure)
STOOL_GILL_COUNT = 32
STOOL_GILL_RELIEF = 1.0
STOOL_GILL_INNER_R = STOOL_BOSS_D / 2.0 + 1.0
STOOL_GILL_OUTER_R = STOOL_CAP_D / 2.0 - 1.0
STOOL_GILL_WIDTH = 1.2

# owner bite -- N square notches cut into the brim edge (brief.json's own
# stated figures, used directly)
BITE_W = 3.0
BITE_D = 2.5
BITE_SPACING_DEG = 26.0        # unstated_in_spec: even spacing, countable at a glance
BITE_START_DEG = 90.0          # unstated_in_spec: start away from dovetail axis in renders

# species groove bands on the buried shank (brief.json states depth/chamfer
# instruction; unstated_in_spec: axial placement/width)
GROOVE_DEPTH = 3.0              # brief.json's own stated figure
GROOVE_WIDTH = 4.0              # unstated_in_spec
GROOVE_CHAMFER = 0.8            # unstated_in_spec: small lead-in per idea.json's instruction
# both measured "below the shoulder line" == below z = STOOL_SHANK_H (shank top)
GROOVE_UPPER_CENTER_BELOW = 8.0   # brief.json's own stated figure
GROOVE_LOWER_CENTER_BELOW = 16.0  # brief.json's own stated figure

SPECIES_GROOVES = {
    "deadhead": (),
    "bracket": ("upper",),
    "inkcap": ("lower",),
    "hollow": ("upper", "lower"),
}

# bill: species -> {owner -> qty}. 4 species x 4 owners = 16 names, 24 pieces
# total, matching brief.md's own count.
STOOL_QTY = {
    "deadhead": 2,
    "bracket": 2,
    "inkcap": 1,
    "hollow": 1,
}

# ---------------------------------------------------------------------
# claim_crown -- 12x (3 per player x 4). unstated_in_spec: OD/thickness.
# ---------------------------------------------------------------------
CROWN_OD = 24.0
CROWN_T = 3.0
CROWN_ID = 16.8                 # seated_pair(16, 'free') slot side -- stool boss OWNS 16mm
CROWN_TOOTH_COUNT = 6           # brief.json's own stated figure
CROWN_TOOTH_H = 3.0             # brief.json's own stated figure
CROWN_HOLE_D = 3.0              # brief.json's own stated figure
N_CROWN = 12

# ---------------------------------------------------------------------
# probe_pin -- 16x, shared supply. unstated_in_spec: every dimension here.
# ---------------------------------------------------------------------
PIN_LEN = 34.0
PIN_HEAD_D = 10.0
PIN_HEAD_T = 3.0
PIN_KNURL_RELIEF = 0.9          # brief.json's own stated figure, used as relief_mm
PIN_HEX_ACROSS_FLATS = 4.0
PIN_TIP_H = 3.0
PIN_SHAFT_H = PIN_LEN - PIN_HEAD_T - PIN_TIP_H
N_PIN = 16
PIN_PROUD_BLOCKED_MM = 22.0     # "a clear thumb's width" -- unstated_in_spec
PIN_PROUD_ADMITTED_MM = 3.0     # "almost to the brim's shadow" -- unstated_in_spec

# the physical channel a probe hole must clear, along its own tilted axis,
# for the ADMITTED pin (head resting flush, shaft+tip fully submerged) to
# travel without colliding with un-cut tile material. Owned here once and
# reused by both loam_tile's own hole cut and main.py's staged pin poses,
# so the two can never silently disagree (see blocks.py's seated_pair note
# on why a mating dimension must never be restated independently).
PROBE_CHANNEL_LEN = PIN_LEN - PIN_HEAD_T + 2.0

# ---------------------------------------------------------------------
# spore_trough -- 4x, one per player. unstated_in_spec: overall envelope,
# cradle pitch, crown-slot size.
# ---------------------------------------------------------------------
TROUGH_L = 230.0
TROUGH_W = 90.0
TROUGH_H = 40.0
TROUGH_FLOOR_T = 6.0
TROUGH_BACK_WALL_H = 34.0       # brief.json: matches the cap's own diameter
TROUGH_SIDE_WALL_H = 10.0
TROUGH_WALL_T = 3.0
TROUGH_CRADLE_PITCH = 36.0      # unstated_in_spec
TROUGH_CRADLE_COUNT = 6
TROUGH_CRADLE_W = STOOL_CAP_D + 0.8   # seated_pair-style, stool cap OWNS this
TROUGH_CRADLE_LEN = STOOL_H            # a stool lying on its side, full length
TROUGH_CRADLE_DEPTH = 6.0              # unstated_in_spec: shallow scallop, not a
                                        # full half-round (that would need a
                                        # 17.4mm-deep floor for a 34.8mm-wide cap)
TROUGH_CRAQUELURE_RELIEF = 1.4  # brief.json: "same craquelure" as loam_tile
TROUGH_NOTCH_W = BITE_W          # brief.json: reuses the stool's own bite figure
TROUGH_NOTCH_D = BITE_D
TROUGH_CROWN_SLOT_D = CROWN_OD + 1.0   # unstated_in_spec: OD + clearance
TROUGH_CROWN_SLOT_DEPTH = 8.0          # unstated_in_spec
N_TROUGH = 4
