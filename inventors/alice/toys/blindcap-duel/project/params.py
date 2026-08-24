"""All dimensions for Blindcap: Duel, mm. Every number traces to brief.json /
brief.md. Where the brief itself says a figure is unstated_in_spec, the
comment says so -- draft mode still gives it a real, considered number.
"""
import math

# ---------------------------------------------------------------------
# loam_tile -- board, 2x total. 3x3 grid of sockets at 44mm
# pitch (OWNED here; every stool/pin clearance derives from it).
# ---------------------------------------------------------------------
TILE_SIZE = 132.0          # brief.json bbox_mm
TILE_T = 28.0               # brief.json bbox_mm
SOCKET_PITCH = 44.0         # unstated_in_spec: derived from cap dia + margin
SOCKET_COLS = 3
SOCKET_ROWS = 3

BORE_D = 21.8                # 0.4mm diametral nominal; coupon required
BORE_DEPTH = 20.0            # unstated_in_spec
BORE_KEY_FLAT_Y = -6.2       # deep rear D-flat; 0.2mm keyed-face allowance
COLLAR_OD = 28.0
COLLAR_H = 2.0                # brief.json's own stated figure

PROBE_HOLE_D = 6.8            # 1.09mm radial clearance around 4.62mm hex envelope
PROBE_COUNTERBORE_D = 12.4    # sloped exterior head seat, ending at channel mouth
PROBE_COUNTERBORE_LEN = 16.0  # open sloped withdrawal relief for the low disc head
PROBE_ANGLE_DEG = 70.0        # from vertical (20deg downward from horizontal)
PROBE_BITS = ("A", "B")
# Two side-by-side, strictly parallel channels. Their shared axis runs along
# the 45-degree gap between orthogonal grid neighbours; the centre lines stay
# 12.6mm apart and never cross. Each mouth is 6.3mm to one side of a common
# radius-14.3mm diagonal datum.
_DIAG = math.sqrt(0.5)
_MOUTH_DATUM_R = 15.3
_CHANNEL_HALF_SPACING = 6.3
PROBE_MOUTHS_XY = (
    ((_MOUTH_DATUM_R - _CHANNEL_HALF_SPACING) * _DIAG,
     (_MOUTH_DATUM_R + _CHANNEL_HALF_SPACING) * _DIAG),
    ((_MOUTH_DATUM_R + _CHANNEL_HALF_SPACING) * _DIAG,
     (_MOUTH_DATUM_R - _CHANNEL_HALF_SPACING) * _DIAG),
)
PROBE_INWARD_XY = ((-_DIAG, -_DIAG), (-_DIAG, -_DIAG))
PROBE_MARK_R = 1.0
PROBE_MARK_H = 0.8
PROBE_MARKS_XY = {
    "A": ((-1.7, 20.0),),
    "B": ((20.0, -1.7), (20.0, 1.7)),
}

TILE_CRAQUELURE_RELIEF = 1.4   # brief.json's own stated figure

# dovetail: symmetric-about-midpoint tab/slot pair per edge (self-mating,
# any edge mates any edge -- see loam_tile.py for the CCW-consistent proof).
DOVETAIL_V0 = 10.0            # tab/slot start, distance from edge midpoint
DOVETAIL_V1 = 30.0            # tab/slot end
DOVETAIL_DEPTH = 6.0          # how far the tab protrudes / slot cuts
DOVETAIL_FLARE = 2.0          # tip is this much wider than the root, each side
DOVETAIL_CLEARANCE = 0.4      # per-side slot allowance; validate with coupon before production

# ---------------------------------------------------------------------
# stool_<species>_p<owner> -- 8 names (4 species x P1/P2), ALL IDENTICAL
# above the shoulder line. This is the load-bearing constraint.
# ---------------------------------------------------------------------
STOOL_CAP_D = 34.0             # unstated_in_spec, matches bbox_mm[0:2]
STOOL_CAP_T = 8.0               # unstated_in_spec
STOOL_CAP_SUPPORT_H = 12.0      # printable pedestal from shoulder to cap
STOOL_BOSS_D = 16.0             # unstated_in_spec -- claim_crown's bore derives from this
STOOL_BOSS_H = 3.0              # unstated_in_spec
STOOL_NECK_D = 12.0             # unstated_in_spec -- "a finger's height" shadow gap
STOOL_NECK_H = 12.0             # unstated_in_spec
STOOL_SHOULDER_D = 26.0         # rests on 28mm-OD keyed socket collar
STOOL_SHOULDER_H = 4.0          # printable taper; shoulder+neck remains 16mm
STOOL_SHANK_D = 21.4
STOOL_KEY_FLAT_Y = -6.0         # deep D-flat tightly limits azimuthal play
STOOL_SHANK_H = 22.0            # brief.json: 2mm collar pass-through + 20mm bore

STOOL_H = STOOL_SHANK_H + STOOL_SHOULDER_H + STOOL_NECK_H + STOOL_CAP_T + STOOL_BOSS_H
assert STOOL_H == 49.0, "must match brief.json bbox_mm[2] exactly"

# growth rings, top of cap (brief.json's stated relief_mm)
STOOL_RING_RELIEF = 0.8
STOOL_RING_RADII = (9.0, 12.0, 15.0)
STOOL_RING_WIDTH = 1.0

# gill ribs, underside of cap brim (brief.json's own stated count/figure)
STOOL_GILL_COUNT = 32
STOOL_GILL_RELIEF = 1.0
STOOL_GILL_INNER_R = STOOL_NECK_D / 2.0 - 0.5
STOOL_GILL_OUTER_R = STOOL_CAP_D / 2.0 - 1.0
STOOL_GILL_WIDTH = 1.2

# owner bite -- N square notches cut into the brim edge (brief.json's own
# stated figures, used directly)
BITE_W = 3.0
BITE_D = 2.5
BITE_SPACING_DEG = 26.0        # unstated_in_spec: even spacing, countable at a glance
BITE_START_DEG = 90.0          # unstated_in_spec: start away from dovetail axis in renders

# Species bits are diagonal through-tunnels in a keyed buried shank. The
# matching tile channels are collinear; absent tunnels fail closed at the
# front wall. Parallel A/B paths never cross.
SPECIES_TUNNELS = {
    "deadhead": (),
    "bracket": ("A",),
    "inkcap": ("B",),
    "hollow": ("A", "B"),
}

# bill: each of two players gets 2 deadhead, 2 bracket, 1 inkcap, 1 hollow.
STOOL_QTY = {
    "deadhead": 2,
    "bracket": 2,
    "inkcap": 1,
    "hollow": 1,
}

# ---------------------------------------------------------------------
# claim_crown -- 6x (3 per player x 2). unstated_in_spec: OD/thickness.
# ---------------------------------------------------------------------
CROWN_OD = 24.0
CROWN_T = 3.0
CROWN_ID = 16.8                 # seated_pair(16, 'free') slot side -- stool boss OWNS 16mm
CROWN_TOOTH_COUNT = 6           # brief.json's own stated figure
CROWN_TOOTH_H = 3.0             # brief.json's own stated figure
CROWN_HOLE_D = 3.0              # brief.json's own stated figure
N_CROWN = 6

# ---------------------------------------------------------------------
# probe_pin -- 6x (3 marked per player). unstated_in_spec: dimensions here.
# ---------------------------------------------------------------------
PIN_LEN = 34.0
PIN_HEAD_D = 10.0
PIN_HEAD_T = 3.0
PIN_KNURL_RELIEF = 0.9          # brief.json's own stated figure, used as relief_mm
PIN_HEX_ACROSS_FLATS = 4.0
PIN_TIP_H = 3.0
PIN_TIP_R = 0.9               # robust FDM-safe blunt tip (never a needle point)
PIN_OWNER_HOLE_D = 1.6
PIN_OWNER_HOLE_R = 2.9
PIN_SHAFT_H = PIN_LEN - PIN_HEAD_T - PIN_TIP_H
N_PIN = 6
PIN_PROUD_BLOCKED_MM = 27.628906 # midpoint of 27.632812-clear / 27.625-contact
PIN_PROUD_ADMITTED_MM = 3.0     # "almost to the brim's shadow" -- unstated_in_spec

# the physical channel a probe hole must clear, along its own tilted axis,
# for the ADMITTED pin (head resting flush, shaft+tip fully submerged) to
# travel without colliding with un-cut tile material. Owned here once and
# reused by both loam_tile's own hole cut and main.py's staged pin poses,
# so the two can never silently disagree (see blocks.py's seated_pair note
# on why a mating dimension must never be restated independently).
PROBE_CHANNEL_LEN = PIN_LEN - PIN_HEAD_T  # 31mm blind stop => exactly 3mm proud

# ---------------------------------------------------------------------
# spore_trough -- 2x, one per player. A compact 3x2 layout keeps both axes
# below 160mm for common FDM beds.
# ---------------------------------------------------------------------
TROUGH_L = 154.0
TROUGH_W = 150.0
TROUGH_H = 40.0
TROUGH_FLOOR_T = 6.0
TROUGH_BACK_WALL_H = 34.0       # brief.json: matches the cap's own diameter
TROUGH_SIDE_WALL_H = 10.0
TROUGH_WALL_T = 3.0
TROUGH_CRADLE_PITCH = 40.0      # X pitch, 3 columns
TROUGH_CRADLE_ROW_PITCH = 55.0  # Y pitch, 2 rows
TROUGH_CRADLE_COLS = 3
TROUGH_CRADLE_ROWS = 2
TROUGH_CRADLE_COUNT = 6
TROUGH_CRADLE_W = STOOL_CAP_D + 0.8   # seated_pair-style, stool cap OWNS this
TROUGH_CRADLE_LEN = STOOL_H            # a stool lying on its side, full length
TROUGH_CRADLE_DEPTH = 3.0              # leaves a 3mm floor under each scallop
                                        # full half-round (that would need a
                                        # 17.4mm-deep floor for a 34.8mm-wide cap)
TROUGH_CRAQUELURE_RELIEF = 1.4  # brief.json: "same craquelure" as loam_tile
TROUGH_NOTCH_W = BITE_W          # brief.json: reuses the stool's own bite figure
TROUGH_NOTCH_D = BITE_D
TROUGH_CROWN_SLOT_D = CROWN_OD + 1.0   # unstated_in_spec: OD + clearance
TROUGH_CROWN_SLOT_DEPTH = 5.0          # modeled blind pocket; leaves 1mm floor
N_TROUGH = 2

# Canonical assembly reference poses. Stool origin is its shank tip; when
# seated into a 20mm bore under a 2mm collar, its origin is 8mm above the
# tile base. The crown's base rests on the cap top while its bore surrounds
# the 3mm boss: z=8+(49-3)=54mm.
SEATED_STOOL_Z = TILE_T + COLLAR_H - STOOL_SHANK_H
SEATED_CROWN_Z = SEATED_STOOL_Z + STOOL_H - STOOL_BOSS_H
assert SEATED_STOOL_Z == 8.0
assert SEATED_CROWN_Z == 54.0
