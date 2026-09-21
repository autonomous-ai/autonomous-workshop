"""Rainward Emberfan parameters. All dimensions in mm; bed XY, +Z up, underside Z0.

Provenance tags: [specified] fixed by the correction Wish, [carried] restated by
the Wish as a measured value of the build being corrected and reproduced here,
[inferred] derived from a specified or carried value, [assumed] engineering
choice recorded in rainward_spec.md.

The correction makes exactly two changes to the crown. The hero arch is gone:
there is no closed loop, arch, ribbon or handle anywhere on the part, and
ordinary flames continue the rhythm where it stood. And the flames now stand
apart: the disc keeps its own circular edge unbroken all the way round, each
flame is rooted on its own arc of that circle, and between every pair of
flames a valley of open background runs down to the circle itself. The
zero-gap rule every brief since the second correction carried is withdrawn.
"""
from math import cos, pi, radians, sin

# --- board plan ------------------------------------------------------------
SUN_R = 79.70                # [carried] disc radius; the flame base circle
LANES = 24                   # [carried]
START_ANGLE = -75.0          # [carried] lane axis = START_ANGLE + PITCH*(p-1)
PITCH = 15.0                 # [carried]
RADII = (74.0, 63.5, 53.0, 42.5, 32.0)   # [carried] five counter stations
LANE_INNER = 26.5            # [carried] tile inside radius
BAR_R = 24.0                 # [carried] centre bar radius

# --- heights ---------------------------------------------------------------
DECK = 5.4                   # [carried] main deck top above underside Z0
LANE_TOP = 6.0               # [carried] tile top
BAR_TOP = 6.2                # [carried] centre bar planar top, 0.2 above tiles
GAP_FLOOR = DECK             # [inferred] exposed body between tiles at Z5.4
SUN_H = BAR_TOP              # [inferred] overall Sun height 6.2

# --- lane tiles ------------------------------------------------------------
TILE_T = 2.2                 # [carried] tile thickness
POCKET_FLOOR = LANE_TOP - TILE_T     # [carried] 3.8 mm of solid body beneath
TILE_PROUD = LANE_TOP - DECK         # [inferred] 0.6 proud of the body
CLEAR = 0.15                 # [carried] plan clearance per side
CHANNEL_W = 0.70             # [carried] constant orange margin between tiles
BANK_W = 0.70                # [carried] the same at the four bank boundaries
POCKET_INNER = LANE_INNER - CLEAR    # [inferred] 26.35
TILE_OUTER = SUN_R - CLEAR           # [carried] 79.55, one exact arc on all 24
# The pockets stop at RIM_INNER so the rim stays one continuous ring of body
# carrying the whole flame base circle. The outer part of each tile is a 1.0 mm
# lapping lip that rests on that ring and reaches the exact 79.55 arc.
RIM_INNER = 76.60                    # [assumed] pocket outer wall
SEAT_OUTER = RIM_INNER - CLEAR       # [inferred] 76.45, seated part of the tile
RIM_TOP = LANE_TOP - 1.0             # [assumed] 5.0, ring top under the lip
LIP_T = LANE_TOP - RIM_TOP           # [inferred] 1.0 mm lapping lip
EDGE_ROUND = 0.15            # [carried] tile exposed top edge rounding
# The body between two pockets is exactly 0.70 mm where it is exposed at Z5.4,
# and drafts wider under the tiles so it is a wedge rather than a fin. The
# tiles carry the matching draft, so the seat keeps its clearance at the mouth.
BOUNDARY_DRAFT = 0.60        # [assumed] extra body per side at the pocket floor

# The 24 tiles end on one exact continuous circular arc at TILE_OUTER: no
# notch, no scallop, no bay, nothing cut into a tile end. Every flame lives
# entirely outside the disc's own edge circle, so no orange flame root is
# visible inside the fan.
TILE_ARC_EXACT = True        # [carried] tile fan ends on one circular arc

# tile underside locating key and its pocket-floor recess
KEY_R = 68.0                 # [assumed] radial centre of the key
KEY_OFFSET = 6.0             # [assumed] perpendicular offset from the lane axis
KEY_L = 6.0                  # [assumed] radial length
KEY_W = 1.6                  # [assumed] tangential width
KEY_H = 0.8                  # [assumed] protrusion below the tile underside
KEY_CLEAR = 0.15             # [inferred] recess is larger by this on each side
KEY_RECESS_D = KEY_H + 0.2   # [assumed] 1.0 deep recess, 0.2 bottom clearance

# --- bank boundary markers -------------------------------------------------
# The constant 0.70 mm orange margin leaves no boundary wide enough to carry
# the raised capsule the clone put out among the lanes: a 0.70 mm fin standing
# proud of the deck would be a wall under the checked minimum. The four bank
# boundaries are therefore marked on the centre bar's own top face, as short
# engraved radial ticks on the 24/1, 6/7, 12/13 and 18/19 rays. Cut rather
# than raised, so the bar stays a flat unobstructed landing for drop.
MARKER_R = 20.2              # [assumed] radial centre of the tick
MARKER_L = 6.4               # [assumed] overall radial length
MARKER_W = 2.0               # [assumed] width across the groove mouth
MARKER_DEPTH = 0.7           # [assumed] depth of the V below the bar top
MARKER_OUTER = MARKER_R + MARKER_L / 2.0   # [inferred] 23.40, inside the bar

# --- counters --------------------------------------------------------------
DROP_H, DROP_L, DROP_W = 4.5, 10.0, 7.0   # [carried] 10 x 7 x 4.5 envelope
COUNTERS_PER_SIDE = 15                    # [carried]

# --- corona: separate flames on one unbroken base circle -------------------
CORONA_TOP = DECK            # [carried] flame root height 5.4
CORONA_BASE_R = SUN_R        # [specified] the disc's own circular edge
CORONA_MAX_R = 96.70         # [carried] tallest flame tip radius
CORONA_COUNT = 48            # [assumed] flames round the ring

CORONA_ROOT_JITTER = 0.6180339887498949    # [assumed] irrational walks; no two
CORONA_GAP_JITTER = 0.4142135623730951     # neighbours share a value and the
CORONA_LENGTH_JITTER = 0.7320508075688772  # sequences never repeat round the
CORONA_TURN_JITTER = 0.7548776662466927    # ring
CORONA_TIP_Z_JITTER = 0.2360679774997897

# A flame's root arc is at most 55 per cent of the arc from its own root to the
# next, and the valley between two flames is never a bare stretch of base
# circle longer than either flame's own root. Root widths therefore stay close
# to one another; the variety the eye reads is in length, tip and curl.
CORONA_ROOT_SPREAD = 0.05    # [assumed] +/- share on the mean root arc
CORONA_GAP_LO = 0.940        # [assumed] valley as a share of the smaller of the
CORONA_GAP_HI = 0.995        # two roots it separates
CORONA_ROOT_FRACTION_MAX = 0.55   # [specified] root arc over root-to-root arc

# Lengths span more than four to one. The tall flames are twelve of forty-eight
# -- one in four -- and their spacing round the ring is 3, 5, 4, 3, 6, 4, 3, 5,
# 4, 3, 4, 4 flames, which is neither periodic nor mirrored.
CORONA_TALL = (0, 3, 8, 12, 15, 21, 25, 28, 33, 37, 40, 44)      # [assumed]
CORONA_SHORT = (1, 5, 7, 10, 14, 17, 19, 23, 27, 30, 34, 39, 42, 46)  # [assumed]
CORONA_RISE_TALL = (13.60, 17.00)   # [inferred] tallest reaches CORONA_MAX_R
CORONA_RISE_MID = (6.60, 11.20)     # [assumed]
CORONA_RISE_SHORT = (4.15, 6.00)    # [inferred] 17.00 / 4.15 = 4.096 to one

# --- flame shape: the curve the third blind critic named and approved ------
# "The curvature is continuous along the entire length: there is no straight
# shaft followed by a hook at the tip; each one bends from root to tip in one
# smooth arc, like a comma or a breaking wave." That curve is not redesigned.
CORONA_TURN_MIN = 37.0       # [carried] least tip-to-root tangent change, deg
CORONA_TURN_MAX = 44.0       # [carried] most
CORONA_TURN_EXP = 1.15       # [carried] heading = turn * t**exp, so the inner
                             # half carries 0.5**1.15 = 0.4502 of the turn
CORONA_TAPER_EXP = 1.50      # [assumed] half width falls from the root chord to
                             # the tip cap as (1 - t)**exp: a lick of flame,
                             # broad at the base and blunt at the point
CORONA_SPINE_SAMPLES = 48    # [assumed] integration steps along one spine

CORONA_TIP_MIN = 1.30        # [carried] 2.60 mm across the thinnest tip cap
CORONA_TIP_MAX = 2.05        # [carried] 4.10 mm across the widest
# The cap runs the other way from the length: a tall lick narrows to the 2.60
# cap and a short one ends as a 4.10 rounded nub. A long flame ending in the
# widest cap reads as an oar, not as fire; every tip is still blunt and
# rounded off and none of them terminates in an actual point.
CORONA_MIN_CLEARANCE = 0.80  # [assumed] narrowest air gap between two flames

# The top falls as the flame runs outward: one plane per flame, from the deck
# height at the root to that flame's own tip height. Nothing is taken off the
# underside, so every flame sits flat on the bed and no face overhangs.
CORONA_TIP_Z_MIN = 3.20      # [carried] lowest tip height, Wish floor 3.0
CORONA_TIP_Z_MAX = 4.30      # [assumed] highest
CORONA_SAMPLES = 24          # [assumed] flank samples used by the plan audits
CORONA_FLANK_TOL = 0.05      # [assumed] mm a fitted flank Bezier may miss the
                             # analytic flank before it is split again


def _frac(step, index):
    """A repeatable irrational walk over [0, 1)."""
    return (step * (index + 1)) % 1.0


def _root_arcs():
    """Root arc and following valley arc for every flame, in degrees.

    Built so that both of the Wish's separation clauses hold by construction:
    a valley is never wider than either root it separates, and a root is never
    more than 55 per cent of the arc from its own root to the next.
    """
    widths = [1.0 + CORONA_ROOT_SPREAD * (2.0 * _frac(CORONA_ROOT_JITTER, i) - 1.0)
              for i in range(CORONA_COUNT)]
    gaps = []
    for i in range(CORONA_COUNT):
        share = CORONA_GAP_LO + (CORONA_GAP_HI - CORONA_GAP_LO) * _frac(
            CORONA_GAP_JITTER, i)
        gaps.append(share * min(widths[i], widths[(i + 1) % CORONA_COUNT]))
    scale = 360.0 / sum(w + g for w, g in zip(widths, gaps))
    return [(w * scale, g * scale) for w, g in zip(widths, gaps)]


def _rises():
    """Radial rise of every flame above the base circle, in mm."""
    out = []
    for i in range(CORONA_COUNT):
        if i in CORONA_TALL:
            lo, hi = CORONA_RISE_TALL
        elif i in CORONA_SHORT:
            lo, hi = CORONA_RISE_SHORT
        else:
            lo, hi = CORONA_RISE_MID
        out.append(lo + (hi - lo) * _frac(CORONA_LENGTH_JITTER, i))
    tall = max(CORONA_TALL, key=lambda i: out[i])
    out[tall] = CORONA_RISE_TALL[1]
    short = min(CORONA_SHORT, key=lambda i: out[i])
    out[short] = CORONA_RISE_SHORT[0]
    return out


def _plan():
    """(root start deg, root end deg, tip radius mm) for every flame."""
    arcs = _root_arcs()
    rises = _rises()
    out = []
    angle = 0.0
    for i, (width, gap) in enumerate(arcs):
        out.append((angle, angle + width, SUN_R + rises[i]))
        angle += width + gap
    return tuple(out)


CORONA_PLAN = _plan()

# --- sealed sRGB surface colours ------------------------------------------
# Three oranges with the body between the two lane tones in greyscale, and two
# counter tones outside both: beige counter > yellow tile > orange body >
# cocoa tile > dark brown counter.
SUN_COLOR = (1.000, 0.404, 0.122)     # [carried] #FF671F body
LANE_LIGHT_COLOR = (1.000, 0.710, 0.286)  # [carried] #FFB549 light lane
LANE_DARK_COLOR = (0.557, 0.235, 0.024)   # [carried] #8E3C06 dark lane
SINGLE_COLOR = (0.97, 0.94, 0.82)     # [carried] cream counter
FORK_COLOR = (0.24, 0.16, 0.12)       # [carried] dark brown counter

SUN_FILAMENT = "orange"
LANE_LIGHT_FILAMENT = "yellow"
LANE_DARK_FILAMENT = "cocoa_brown"
SINGLE_FILAMENT = "beige"
FORK_FILAMENT = "dark_brown"

NEUTRAL_COLOR = (0.78, 0.78, 0.78)    # single-material evidence view only

# --- print declarations ----------------------------------------------------
NOZZLE = 0.4
BED = (200.0, 200.0, 200.0)

# --- preserved setup and demonstration states ------------------------------
INITIAL_A = {24: 2, 13: 5, 8: 3, 6: 5}      # [carried]
INITIAL_B = {1: 2, 12: 5, 17: 3, 19: 5}     # [carried]
BEFORE_A = {24: 2, 13: 4, 8: 2, 7: 2, 6: 5}  # [carried] illustration pose
BEFORE_B = {1: 1, 2: 1, 12: 4, 17: 3, 18: 1, 19: 5}

POCKET_OUTER = RIM_INNER      # [inferred] the pocket stops at the rim ring
