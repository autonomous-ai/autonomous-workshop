"""All dimensions for millbind, mm. Every number here traces to brief.json."""
import math

# --- yard_board -------------------------------------------------------
BOARD_VERTEX_R = 115.0        # corner-to-corner 230mm / 2
SLAB_T = 12.0                 # board floor thickness
PIN_D = 8.0                   # yard_board OWNS this
PIN_H = 30.0                  # yard_board OWNS this
PIN_PITCH = 30.0              # yard_board OWNS this == every gear pitch circle
SILL_D = PIN_D + 6.0          # 14mm raised sill ring around the 18 outer pins
SILL_H = 1.2
RIB_H = 1.0                   # plank rib relief (the shallower of the two -> relief_mm)
BOARD_SKIRT_CHAMFER = 3.0

# --- shared gear tooth form (every gear/millstone/crank shares this) --
MODULE = 2.5
TEETH = 12
PITCH_R = MODULE * TEETH / 2.0          # 15.0
ADDENDUM = MODULE                        # 2.5
DEDENDUM = 1.25 * MODULE                 # 3.125
OUTER_R = PITCH_R + ADDENDUM             # 17.5 -> 35mm OD
ROOT_R = PITCH_R - DEDENDUM              # 11.875 -> 23.75mm root disk
BORE_D = 8.6

# --- gear_low -----------------------------------------------------------
GEAR_LOW_H = 10.0

# --- gear_high ------------------------------------------------------------
GEAR_HIGH_H = 30.0
GEAR_HIGH_COLUMN_D = 16.0
GEAR_HIGH_TEETH_H = 10.0     # top band

# --- gear_tandem / millstone-barrel / crank-barrel share this full barrel
BARREL_H = 30.0
BARREL_RIM = 1.0             # untoothed lead-in rim top+bottom
BARREL_TEETH_Z0 = BARREL_RIM
BARREL_TEETH_Z1 = BARREL_H - BARREL_RIM

# --- millstone crown/hub --------------------------------------------------
CROWN_D = 34.0
CROWN_H = 6.0
CROWN_FURROW_DEPTH = 1.2
HUB_ACROSS_FLATS = 16.0
HUB_H = 12.0
MILLSTONE_H = BARREL_H + CROWN_H + HUB_H   # 48

# --- crank_gear -------------------------------------------------------
CRANK_CAP_H = 3.0
CRANK_KNOB_D = 14.0
CRANK_KNOB_STANDOFF = 22.0
CRANK_ARM_OFFSET = 21.0       # knob-centre from gear axis
CRANK_H = BARREL_H + CRANK_CAP_H + CRANK_KNOB_STANDOFF   # 55
CRANK_ARROW_RELIEF = 1.2

# --- grain_pellet -------------------------------------------------------
PELLET_D = 15.0
PELLET_H = 5.0
PELLET_HOLE_D = 9.0

# --- sack_spindle -------------------------------------------------------
SPINDLE_BASE_D = 40.0
SPINDLE_BASE_H = 8.0
SPINDLE_ROD_D = 8.5
SPINDLE_ROD_H = 62.0
SPINDLE_H = SPINDLE_BASE_H + SPINDLE_ROD_H   # 70
SPINDLE_CAPACITY = 12

# --- granary_bin ----------------------------------------------------------
BIN_L = 70.0
BIN_W = 50.0
BIN_H = 25.0
BIN_WALL = 3.0
BIN_SCALLOP_R = 12.0

# --- counts (bill) --------------------------------------------------------
N_GEAR_LOW = 14
N_GEAR_HIGH = 7
N_GEAR_TANDEM = 3
N_GRAIN_PELLET = 28
N_SACK_SPINDLE = 4


def hex_lattice_positions(pitch: float, max_ring: int = 3):
    """37-point triangular lattice: centre + rings of 6/12/18, EXACTLY once.

    Returns list of (x, y, ring) so callers can pick out the 18 outer
    "yard pins" (ring == max_ring) that get sills, vs the 19 inner pins
    that don't. Reused for pin cutting, sill placement and rib layout —
    never regenerated.
    """
    directions = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

    def axial_to_xy(q, r):
        x = pitch * (q + r / 2.0)
        y = pitch * (r * math.sqrt(3) / 2.0)
        return (x, y)

    pts = [(0.0, 0.0, 0)]
    for k in range(1, max_ring + 1):
        q, r = directions[4][0] * k, directions[4][1] * k
        ring = []
        for i in range(6):
            for _ in range(k):
                ring.append((q, r))
                q += directions[i][0]
                r += directions[i][1]
        for (qq, rr) in ring:
            x, y = axial_to_xy(qq, rr)
            pts.append((x, y, k))
    return pts
