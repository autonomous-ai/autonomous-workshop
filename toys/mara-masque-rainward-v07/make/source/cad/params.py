"""Rainward Sunflare parameters. All dimensions in mm; bed XY, +Z up, underside Z0.

Provenance tags: [specified] fixed by the correction Wish, [carried] restated by
the Wish as a measured value of the build being corrected and reproduced here,
[inferred] derived from a specified or carried value, [assumed] engineering
choice recorded in rainward_spec.md.

The board is unchanged. This correction makes exactly three changes, all to the
corona, and all aimed at one defect: two blind critics read the last rim as a
rosette, a medallion, a pinwheel disc, and never once reached for sun, flame or
fire. Forty-eight thin same-handed tendrils on a plate read as rotation.

1. Thirty-two flames instead of forty-eight, so a root can be twice as wide and
   the valley beside it stays as wide as a root.
2. A tongue, not a fin: the half width now holds through the lower half and then
   narrows hard into a 2.00 to 2.60 mm cap, a quarter to a third of the base.
3. Mixed handedness: fourteen of the thirty-two flames curl the other way, in
   runs of one to three, so the fringe flicks rather than spins.

Everything the last two corrections reached is carried: separate tongues on one
unbroken base circle, a valley for every root, no closed loop, and the whole
tile fan, counter, stack, colour and rules geometry untouched.
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
CORONA_COUNT = 32            # [specified] down from 48: at 48 a fat root and an
                             # open valley cannot both exist on this circle

CORONA_ROOT_JITTER = 0.6180339887498949    # [assumed] irrational walks; no two
CORONA_GAP_JITTER = 0.4142135623730951     # neighbours share a value and the
CORONA_LENGTH_JITTER = 0.7320508075688772  # sequences never repeat round the
CORONA_TURN_JITTER = 0.7548776662466927    # ring
CORONA_TIP_Z_JITTER = 0.2360679774997897
CORONA_SENSE_JITTER = 0.4083269131959844   # [assumed] frac(sqrt(117)/2), the
                             # walk that lays out the handedness runs; a fresh
                             # irrational so the sign sequence is not locked in
                             # phase with the root, gap, length or turn walks.
                             # Chosen over frac(sqrt(19)/2) after an independent
                             # blind critic read the first build's rim as "a
                             # consistent counterclockwise sweep ... like a
                             # pinwheel" despite a measured 14/18 split. A
                             # flame's visible rake scales with its length, so
                             # only the eight tall flames are legible at a
                             # glance, and under the old constant those eight
                             # fell into same-sign pairs, + + - - + + - -: a
                             # clean period-4 sweep in exactly the flames the
                             # eye reads. This constant is the conforming walk
                             # that most breaks that pairing -- six of the eight
                             # tall neighbours now differ, in the irregular
                             # order + - - + - - + - -- while keeping the same
                             # generator, the same run caps, the same 0.4375
                             # minority share and the same runs of one to three.
                             # Walks that alternate all eight were rejected:
                             # they collapse to a near-strict zigzag, which is
                             # the pattern the Wish forbids in the other
                             # direction.

# A flame's root arc is at most 55 per cent of the arc from its own root to the
# next, and the valley between two flames is never a bare stretch of base
# circle longer than either flame's own root. Root widths therefore stay close
# to one another; the variety the eye reads is in length, tip and curl. These
# three numbers are unchanged, so the one-to-one root-to-valley rhythm the last
# blind critic measured survives the count change intact: at 32 the root-to-root
# pitch is 15.649 mm instead of 10.433 mm and both the root and the valley grow
# by the same half again.
CORONA_ROOT_SPREAD = 0.05    # [carried] +/- share on the mean root arc
CORONA_GAP_LO = 0.940        # [carried] valley as a share of the smaller of the
CORONA_GAP_HI = 0.995        # two roots it separates
CORONA_ROOT_FRACTION_MAX = 0.55   # [specified] root arc over root-to-root arc

# Lengths span more than four to one. The tall flames are eight of thirty-two
# -- one in four -- and their spacing round the ring is 3, 5, 4, 3, 6, 4, 3, 4
# flames, which is neither periodic nor mirrored and is never every fourth.
CORONA_TALL = (0, 3, 8, 12, 15, 21, 25, 28)                        # [assumed]
CORONA_SHORT = (1, 5, 7, 10, 14, 17, 19, 23, 27, 30)               # [assumed]
CORONA_RISE_TALL = (13.60, 17.00)   # [inferred] tallest reaches CORONA_MAX_R
CORONA_RISE_MID = (6.60, 11.20)     # [assumed]
CORONA_RISE_SHORT = (4.15, 6.00)    # [inferred] 17.00 / 4.15 = 4.096 to one

# --- flame shape: the curve the third blind critic named and approved ------
# "The curvature is continuous along the entire length: there is no straight
# shaft followed by a hook at the tip; each one bends from root to tip in one
# smooth arc, like a comma or a breaking wave." That curve is not redesigned.
# Only its sign now varies from flame to flame.
CORONA_TURN_MIN = 37.0       # [carried] least tip-to-root tangent change, deg
CORONA_TURN_MAX = 44.0       # [carried] most
CORONA_TURN_EXP = 1.15       # [carried] heading = turn * t**exp, so the inner
                             # half carries 0.5**1.15 = 0.4502 of the turn

# [specified] A tongue, not a fin. The previous build shed its width immediately
# above the root -- half width fell as (1 - t)**1.50, which is steepest at the
# root and flattest at the tip, so the outer third ran out as a near-parallel
# filament at the cap width. The profile is turned round: the half width now
# falls as 1 - t**CORONA_TAPER_EXP, flat where the flame leaves the base circle
# and steepest as it arrives, which is a lick that holds most of its width
# through the lower half and then narrows hard into the point. Measured at half
# a flame's length the width is 0.73 of the root width, against the Wish floor
# of 0.45 and about 0.35 in the build being corrected.
CORONA_TAPER_EXP = 1.50      # [assumed] exponent of the reversed taper
CORONA_SPINE_SAMPLES = 48    # [assumed] integration steps along one spine

CORONA_TIP_MIN = 1.00        # [specified] 2.00 mm across the thinnest tip cap
CORONA_TIP_MAX = 1.30        # [specified] 2.60 mm across the widest
# The cap runs the other way from the length: a tall lick narrows to the 2.00
# cap and a short one ends as a 2.60 rounded nub. A long flame ending in the
# widest cap reads as an oar, not as fire. Against an 8.05 mm mean root that is
# a tip a quarter to a third of the base, which is what reads as a point. The
# earlier brief's "treat 2.10 mm as the floor, not the target" is withdrawn by
# this Wish: it was one-sided and drove the caps to 4.10 mm, which read as
# thumbs. The needle test still has to pass, and does -- every tip is a rounded
# cap at least 2.00 mm across on a flame at least 3.20 mm tall in Z, and none
# of them terminates in an actual point.
CORONA_MIN_CLEARANCE = 0.80  # [specified] narrowest air gap between two flames

# [specified] Mixed handedness. Every flame has turned the same way since the
# second correction, on the stated grounds that one handedness keeps the part
# printable. That reasoning is withdrawn by this Wish and it was wrong: the
# corona lies flat in the print plane and a flame's curvature is entirely in
# plan, in X and Y. The 45-degree rule governs Z only, so curving one flame one
# way and its neighbour the other costs nothing in overhang, support or
# bridging, and the part stays a single flat plan piece.
#
# CORONA_SENSE[i] is +1 when flame i curls toward the neighbour it faces at the
# end of its own root arc -- the sense every flame had -- and -1 for the mirror
# of that flame about its own radial midline. The mirror keeps the root chord,
# the root arc, the turn magnitude, the taper, the cap and the ramp exactly;
# only the sign changes.
CORONA_SENSE_MAJOR_RUN = 3   # [specified] runs of one to three, never strictly
CORONA_SENSE_MINOR_RUN = 2   # alternating and never repeating round the ring
CORONA_SENSE_FLIPS = ()      # [assumed] indices flipped out of the walk because
                             # a converging pair could not hold
                             # CORONA_MIN_CLEARANCE. Empty: the narrowest air
                             # gap between any two flames is 7.275 mm, at the
                             # root of a parallel pair, nine times the 0.80 mm
                             # floor, so no pair needed flipping. The Wish's
                             # "flip one of them rather than shortening either"
                             # is implemented here and was not needed.

# The top falls as the flame runs outward: one plane per flame, from the deck
# height at the root to that flame's own tip height. Nothing is taken off the
# underside, so every flame sits flat on the bed and no face overhangs.
CORONA_TIP_Z_MIN = 3.20      # [carried] lowest tip height, Wish floor 3.0
CORONA_TIP_Z_MAX = 4.30      # [carried] highest
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
    """(root start deg, root end deg, tip radius mm) for every flame.

    The ring is started half of the closing valley past zero degrees, so the
    bare base circle - not a flame root endpoint - covers the cylinder's own
    seam at angle zero. With a root endpoint sitting exactly on that seam the
    kernel has to merge two vertices a femtometre apart, and it resolves that
    tie differently from run to run: the exported STEP then alternated between
    two byte orderings that differed only in the last bit of six coordinates.
    The offset is a constant rotation of the whole corona, so no measured root
    arc, valley, rise, turn, cap or clearance changes.
    """
    arcs = _root_arcs()
    rises = _rises()
    out = []
    angle = arcs[-1][1] / 2.0
    for i, (width, gap) in enumerate(arcs):
        out.append((angle, angle + width, SUN_R + rises[i]))
        angle += width + gap
    return tuple(out)


CORONA_PLAN = _plan()


def _sense_runs():
    """Run lengths of one handedness, alternating, closing the ring.

    The walk lays out runs of one to three flames. A majority run may be one,
    two or three long and a minority run one or two, which is what puts the
    minority at roughly three sevenths of the ring rather than half of it. An
    odd number of runs would leave the first and last run sharing a sign and
    merging across the seam into a run longer than three, so the longest run is
    split in two; both halves are still inside the limit and the ring closes on
    opposite signs.
    """
    runs = []
    total = 0
    step = 0
    major = True
    while total < CORONA_COUNT:
        limit = CORONA_SENSE_MAJOR_RUN if major else CORONA_SENSE_MINOR_RUN
        length = 1 + int(limit * _frac(CORONA_SENSE_JITTER, step))
        runs.append(min(length, CORONA_COUNT - total))
        total += runs[-1]
        step += 1
        major = not major
    if len(runs) % 2:
        longest = max(range(len(runs)), key=lambda i: (runs[i], -i))
        half = runs[longest] // 2
        runs[longest:longest + 1] = [half, runs[longest] - half]
    return tuple(runs)


def _senses():
    """+1 or -1 for every flame: which way that flame curls in plan.

    +1 is the sense every flame in the build being corrected had -- curling
    toward the neighbour it faces at the end of its own root arc. -1 is the
    mirror of that flame about its own radial midline.
    """
    out = []
    for index, length in enumerate(_sense_runs()):
        out += [1 if index % 2 == 0 else -1] * length
    for index in CORONA_SENSE_FLIPS:
        out[index % CORONA_COUNT] = -out[index % CORONA_COUNT]
    return tuple(out)


CORONA_SENSE_RUNS = _sense_runs()
CORONA_SENSE = _senses()

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
