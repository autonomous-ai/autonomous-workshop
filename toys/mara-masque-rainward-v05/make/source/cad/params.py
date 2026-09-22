"""Rainward Bladefire parameters. All dimensions in mm; bed XY, +Z up, underside Z0.

Provenance tags: [specified] fixed by the correction Wish, [preserved] carried
unchanged from the Rainward Flarecrown clone, [inferred] derived from a
preserved or specified value, [assumed] engineering choice recorded in
rainward_spec.md.
"""

# --- board plan, preserved -------------------------------------------------
SUN_R = 90.0                 # [preserved] radius-90 disc perimeter
LANES = 24                   # [preserved]
START_ANGLE = -75.0          # [preserved] lane axis = START_ANGLE + PITCH*(p-1)
PITCH = 15.0                 # [preserved]
RADII = (85.0, 72.0, 59.0, 46.0, 33.0)   # [preserved] five radial stations
LANE_INNER = 26.5            # [specified] tile inside radius
BAR_R = 24.0                 # [preserved] centre bar radius

# --- heights, item 1 -------------------------------------------------------
DECK = 8.0                   # [specified] main deck top above underside Z0
LANE_TOP = 8.8               # [specified] tile top / counter underside layer 1
BAR_TOP = 9.0                # [specified] centre bar planar top, 0.2 above lanes
MARKER_TOP = 9.0             # [specified] capsule marker maximum
GAP_FLOOR = DECK             # [specified] exposed body between tiles at Z8.0
SUN_H = BAR_TOP              # [inferred] overall Sun height 9.0

# --- lane tiles, item 3 ----------------------------------------------------
TILE_T = 2.8                 # [specified] tile thickness
POCKET_FLOOR = 6.0           # [specified] pocket floor Z
TILE_PROUD = LANE_TOP - DECK # [inferred] 0.8 proud of the body
CLEAR = 0.15                 # [specified] plan clearance per side
CHANNEL_W = 0.8              # [preserved] ordinary exposed body ridge
BANK_W = 1.6                 # [preserved] bank boundary exposed body ridge
POCKET_INNER = LANE_INNER - CLEAR    # [inferred] 26.35
TILE_OUTER = SUN_R - CLEAR           # [inferred] 89.85, the tile follows the rim
# The pockets close at RIM_INNER instead of breaking out at the perimeter, so
# the rim stays one continuous ring of body. The skirt troughs cut inward past
# 90, and the ring has to stay thick enough between the deepest trough floor
# (87.10) and the pocket wall; 84.5 leaves 2.6 mm of solid body there. Every
# tile reaches 89.85 on one exact circular arc, so a counter at the 85 mm
# station keeps its flat support; the outer part of each tile is a 1.0 mm
# lapping lip that rests on the ring.
RIM_INNER = 84.5                     # [assumed] pocket outer wall
SEAT_OUTER = RIM_INNER - CLEAR       # [inferred] 84.35, seated part of the tile
RIM_TOP = 7.8                        # [assumed] rim ring top, 0.2 under the deck
LIP_T = LANE_TOP - RIM_TOP           # [inferred] 1.0 mm lapping lip
EDGE_ROUND = 0.15            # [specified] tile exposed top edge rounding
# The body between two pockets is exactly 0.8 mm (1.6 at a bank) where it is
# exposed at Z8.0, and drafts wider under the tiles so it is a wedge rather
# than a 0.8 mm fin standing 2 mm off the pocket floor. The tiles carry the
# matching draft, so the seat keeps its 0.15 mm clearance at the opening.
BOUNDARY_DRAFT = 0.6         # [assumed] extra body per side at the pocket floor

# This revision withdraws the tile bays and the trough clipping the previous
# build carried. The 24 tiles end on one exact continuous circular arc at
# TILE_OUTER: no notch, no scallop, no bay, nothing cut into a tile end. The
# flame lives entirely outside that arc, so no orange flame root is visible
# inside the disc.
TILE_ARC_EXACT = True        # [specified] tile fan ends on one circular arc

# tile underside locating key and its pocket-floor recess
KEY_R = 78.5                 # [assumed] radial centre of the key, moved in
                             # with the pocket wall so the recess stays inside
KEY_OFFSET = 7.0             # [assumed] perpendicular offset from the lane axis
KEY_L = 7.0                  # [assumed] radial length
KEY_W = 1.6                  # [assumed] tangential width
KEY_H = 1.2                  # [assumed] protrusion below the tile underside
KEY_CLEAR = 0.15             # [inferred] recess is larger by this on each side
KEY_RECESS_D = KEY_H + 0.2   # [assumed] 1.4 deep recess, 0.2 bottom clearance

# --- boundary capsule markers, preserved ----------------------------------
MARKER_R = 65.0              # [preserved] radial centre
MARKER_L = 10.0              # [preserved] radial length
MARKER_W = 0.8               # [preserved] width
MARKER_ROUND = 0.3           # [preserved] top roll radius

# --- counters, preserved ---------------------------------------------------
DROP_H, DROP_L, DROP_W = 4.0, 12.0, 8.0      # [preserved] 12 x 8 x 4 envelope
COUNTERS_PER_SIDE = 15                        # [preserved]

# --- corona rim, item 2 --------------------------------------------------
# One continuous skirt of flame. The body has no plain circular edge left: its
# whole outer boundary is tongue flanks and the V/U troughs between them, and
# consecutive tongues share their root points, so the flame is one band of
# material rather than separate slivers standing off the disc.
CORONA_TOP = DECK            # [specified] flush with the deck top at Z8.0
CORONA_MAX_R = 96.40         # [inferred] tallest tongue; the hero crest alone
                             # reaches 96.70 and the envelope stays under 194

# (root angle deg, trough floor radius mm, trough floor half-arc deg).
# A trough that cuts inside radius 89.95 also notches the tile lip above it, so
# every one of those sits on a lane boundary ray, where no counter at the
# outermost station has any footprint. The nine deep troughs are spaced 30, 60,
# 45, 30, 45, 13.5, 16.5, 60, 30 and 30 degrees apart, which is neither a gear
# nor a clock face; the rest are jittered off every regular subdivision.
CORONA_TROUGHS = (
    (7.076, 87.10, 1.00),
    (22.897, 87.10, 1.00),
    (29.601, 91.05, 0.25),
    (37.444, 87.33, 1.00),
    (45.933, 91.40, 0.25),
    (52.555, 87.88, 1.00),
    (60.165, 91.34, 0.25),
    (67.306, 87.37, 1.00),
    (82.549, 88.73, 1.00),
    (89.079, 91.13, 0.25),
    (97.915, 88.22, 1.00),
    (105.644, 91.17, 0.25),
    (112.902, 87.73, 1.00),
    (119.755, 91.22, 0.25),
    (127.189, 87.35, 1.00),
    (142.214, 87.28, 1.00),
    (149.880, 91.13, 0.25),
    (157.510, 88.37, 1.00),
    (172.794, 88.17, 1.00),
    (179.929, 90.85, 0.25),
    (187.866, 88.72, 1.00),
    (202.872, 87.25, 1.00),
    (209.681, 90.91, 0.25),
    (217.832, 87.35, 1.00),
    (232.171, 87.80, 1.00),
    (239.009, 91.17, 0.25),
    (247.710, 87.41, 1.00),
    (262.989, 88.15, 1.00),
    (269.500, 90.10, 0.25),
    (277.826, 90.15, 0.25),
    (285.500, 90.20, 0.25),
    (292.193, 88.44, 1.00),
    (300.069, 90.70, 0.25),
    (307.023, 88.74, 1.00),
    (322.293, 88.12, 1.00),
    (330.730, 90.90, 0.25),
    (337.365, 87.71, 1.00),
    (352.265, 88.38, 1.00),
)
# Tip radius of the tongue that runs from trough i to trough i+1. No two are
# equal, the sequence is neither sorted, mirrored nor periodic at any shift,
# and the low run is the stretch the hero arch vaults over.
CORONA_TIPS = (
    96.18, 96.30, 96.40, 96.40, 96.40, 94.55, 96.40, 96.40,
    93.72, 94.04, 96.40, 94.00, 93.38, 96.40, 96.40, 96.40,
    94.23, 96.40, 92.95, 95.10, 96.40, 96.40, 96.40, 96.40,
    96.40, 96.40, 96.40, 96.40, 92.45, 92.55, 96.36, 96.36,
    93.48, 96.40, 96.40, 96.40, 95.11, 96.34,
)
CORONA_COUNT = len(CORONA_TROUGHS)   # [inferred] 38 tongues, 38 troughs
CORONA_NOTCH_LIMIT = 89.95   # [assumed] below this a trough notches a tile lip
CORONA_NOTCH_WINDOW = 1.5    # [assumed] deg such a trough keeps to a boundary,
                             # measured so its notch never reaches a counter

CORONA_TIP_FRAC = 0.26       # [assumed] tip cap radius as a share of the rise
CORONA_TIP_MIN = 0.75        # [specified] 1.8 mm across the thinnest tip, well
                             # over the 1.3 mm the Wish sets as the floor: the
                             # instruction is to thin the tongue, not sharpen it
CORONA_TIP_MAX = 0.95        # [assumed] a blade end, not a needle and not a knob
CORONA_TIP_SHARE = 0.22      # [assumed] cap radius ceiling, share of the root

# --- tongue shape: early taper, outer-half curl, falling top ---------------
# A tongue is a swept blade, not an extruded triangle. Its spine leaves the
# root chord along that chord's outward normal and turns steadily one way; its
# width comes off early, so the outer half is already slender while the root
# stays the full width of the chord it shares with both neighbours.
CORONA_TURN_MIN = 38.0       # [specified] least tip-to-root tangent change, deg
CORONA_TURN_MAX = 44.5       # [specified] most; the Wish allows 25 to 45
CORONA_TURN_EXP = 2.4        # [specified] heading = turn * t**exp, so the outer
                             # half alone carries 1 - 0.5**exp = 0.75 of the
                             # turn, comfortably over the 20 deg floor
CORONA_TURN_JITTER = 0.7548776662  # [assumed] irrational step; no two adjacent
                             # tongues turn by the same amount and the sequence
                             # never repeats round the ring
CORONA_TAPER_EXP = 4.2       # [assumed] the surplus half width over the tip
                             # falls as (1 - t)**exp: a quarter of it is left at
                             # mid length, so the outer half is slender while
                             # the root keeps the full chord it shares
CORONA_SPINE_SAMPLES = 48    # [assumed] integration steps along one spine

# The top falls as the tongue runs outward. The root keeps the deck height and
# the underside stays flat on the bed, so no material is taken from below and
# nothing cantilevers over air. The fall is one plane per tongue, which leaves
# a straight crisp crease where it meets each vertical flank.
CORONA_TIP_Z_MIN = 3.52      # [specified] lowest tip height, Wish floor 3.5
CORONA_TIP_Z_MAX = 4.25      # [specified] highest tip height, Wish ceiling 5.0
CORONA_TIP_Z_JITTER = 0.6180339887  # [assumed] irrational step; tip heights
                             # vary tongue to tongue round the ring
CORONA_HOLD_R = 0.0          # [specified] no hold: the fall starts at the root
                             # chord itself, so the ramp runs the tongue's whole
                             # length and is the face the eye sees, instead of a
                             # short steep bevel on top of a full-height wall
RIM_COLLAR_R = TILE_OUTER + CLEAR   # [inferred] 90.0; the body is restored to
                             # RIM_TOP out to here, so every tile lip keeps a
                             # continuous ring under it even though the flame
                             # above it is already falling
CORONA_HOLD_MAX_FRAC = 0.55  # [assumed] the hold never eats more than this
                             # share of a tongue, so every tongue has a ramp
CORONA_SAMPLES = 18          # [assumed] flank samples used by the plan audits

# The hero: one closed loop that leaves the skirt and rejoins it. Its two legs
# plant in two trough floors and dive into the body; the skirt runs on
# underneath it, and the window between the arch and the three short tongues it
# vaults is the closed magnetic loop. The tongues under the arch are the short
# end of the length range, which is what leaves room for the window.
HERO_START = 268.500         # [assumed] first leg, planted in the crown
HERO_SPAN = 18.000           # [assumed] span, leg to leg
HERO_FOOT_R = 84.6           # [assumed] spine radius where each leg is rooted
HERO_APEX_R = 97.45          # [assumed] crest spine radius; the crest is the
                             # one place the rim reaches 99.00, so the hero is
                             # unmistakably the tallest thing on the board
HERO_HALF = 1.55             # [assumed] band half thickness, 3.1 mm across
HERO_DOME = 0.30             # [assumed] <1 gives steep legs under a domed crest,
                             # so the loop reads as an arch rather than a staple
HERO_SKEW = 1.12             # [assumed] >1 leans the crest the way tongues sweep
HERO_ROOT_CAP = 9.5          # [assumed] deepest inward reach of a leg
HERO_SAMPLES = 280

# --- sealed sRGB surface colours ------------------------------------------
# Five values that must stay separable in greyscale, ordered light to dark:
# beige counter > yellow tile > orange body > cocoa tile > dark brown counter.
SUN_COLOR = (1.00, 0.66, 0.18)        # [preserved] mid sun-orange body
LANE_LIGHT_COLOR = (1.00, 0.83, 0.10) # [specified] lighter than the body
LANE_DARK_COLOR = (0.60, 0.39, 0.20)  # [specified] darker than the body
SINGLE_COLOR = (0.97, 0.94, 0.82)     # [preserved] cream counter
FORK_COLOR = (0.24, 0.16, 0.12)       # [preserved] dark brown counter

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
INITIAL_A = {24: 2, 13: 5, 8: 3, 6: 5}      # [preserved]
INITIAL_B = {1: 2, 12: 5, 17: 3, 19: 5}     # [preserved]
BEFORE_A = {24: 2, 13: 4, 8: 2, 7: 2, 6: 5}  # [preserved] illustration pose
BEFORE_B = {1: 1, 2: 1, 12: 4, 17: 3, 18: 1, 19: 5}

POCKET_OUTER = RIM_INNER      # [inferred] the pocket stops at the rim ring

# --- flank fitting ---------------------------------------------------------
CORONA_FLANK_TOL = 0.05      # [assumed] mm a fitted flank Bezier may miss the
                             # analytic flank before it is split again
