"""Single source of dimensional truth for Manhattan Nocturne.

Every manufacturing dimension used by the CAD builders lives here.  Provenance
tags match ``manhattan_nocturne_spec.md``:

* ``[derived]`` follows directly from another controlled dimension.
* ``[assumed]`` is an explicit first-pass design choice awaiting physical QA.
* ``[exploration]`` is an FDM-oriented floor, not a calibrated print claim.
"""

from __future__ import annotations

# --- Board and coordinate contract -----------------------------------------

FILES = 8                                      # [observed] standard chess
RANKS = 8                                      # [observed] standard chess
SQUARE_PITCH = 28.5                            # mm [assumed] spec scale anchor
OUTER_BORDER = 8.0                             # mm [derived] 244 mm envelope
PLAY_SPAN = FILES * SQUARE_PITCH               # mm [derived]
BOARD_SIZE = PLAY_SPAN + 2.0 * OUTER_BORDER    # mm [derived]
BOARD_TOTAL_HEIGHT = 9.00                      # mm [assumed] preserved product envelope
SQUARE_RELIEF = 0.80                           # mm [assumed] four visible 0.20 mm layers
BOARD_THICKNESS = BOARD_TOTAL_HEIGHT - SQUARE_RELIEF  # mm [derived] 8.20 mm dark landing
SQUARE_GRID_LAND = 0.50                        # mm [exploration] avoids non-manifold four-corner steps
PLAY_EDGE_LAND = 1.20                          # mm [exploration] three-line floor at field perimeter
EXPLORATION_LAYER_HEIGHT = 0.20                # mm [assumed] pinned slicer profile
EXPLORATION_NOZZLE_DIAMETER = 0.40             # mm [assumed] pinned slicer profile
BOOLEAN_OVERLAP = 0.08                         # mm [assumed] robust B-rep union
BOOLEAN_OVERSHOOT = 0.50                       # mm [assumed] robust through-cut

# The seven internal file/rank lines continue through the outer border as a
# shallow Manhattan street plan.  Their cutters overshoot only the outside
# edge; they begin at the 8x8 play-field boundary and never score a square.
INTERNAL_GRID_COORDINATES = tuple(              # mm [derived] seven lines per axis
    -PLAY_SPAN / 2.0 + index * SQUARE_PITCH
    for index in range(1, FILES)
)
BORDER_STREET_GROOVE_WIDTH = 1.20              # mm [exploration] three nozzle widths
BORDER_STREET_GROOVE_DEPTH = 0.40              # mm [exploration] two 0.20 mm layers
BORDER_STREET_GROOVE_LENGTH = OUTER_BORDER + BOOLEAN_OVERLAP  # mm [derived]
BORDER_STREET_GROOVE_CENTER = (                 # mm [derived] from board origin
    PLAY_SPAN / 2.0 + BORDER_STREET_GROOVE_LENGTH / 2.0
)

# One Broadway cue stays wholly inside the south border.  Its stepped Manhattan
# path uses only axis-aligned printable walls; the 8.0 x 4.4 mm centreline
# envelope still travels diagonally without creating a sub-nozzle acute wedge.
AVENUE_GROOVE_WIDTH = 1.20                     # mm [exploration] three nozzle widths
AVENUE_GROOVE_DEPTH = 0.40                     # mm [exploration] two layers
AVENUE_GROOVE_CENTER_X = SQUARE_PITCH / 2.0    # mm [derived] midway between file-line grooves
AVENUE_GROOVE_CENTER_Y = -(BOARD_SIZE / 2.0 - OUTER_BORDER / 2.0)  # [derived]
AVENUE_STEP_OFFSETS = (                         # (x, y) mm [assumed] relative to cue centre
    (-4.0, -2.2),
    (-2.0, -2.2),
    (-2.0, -1.1),
    (0.0, -1.1),
    (0.0, 0.0),
    (2.0, 0.0),
    (2.0, 1.1),
    (4.0, 1.1),
    (4.0, 2.2),
)
AVENUE_STEP_POINTS = tuple(                     # (x, y) mm [derived] board coordinates
    (AVENUE_GROOVE_CENTER_X + x, AVENUE_GROOVE_CENTER_Y + y)
    for x, y in AVENUE_STEP_OFFSETS
)
AVENUE_GROOVE_MIN_Y = min(y for _, y in AVENUE_STEP_POINTS) - AVENUE_GROOVE_WIDTH / 2.0
AVENUE_GROOVE_MAX_Y = max(y for _, y in AVENUE_STEP_POINTS) + AVENUE_GROOVE_WIDTH / 2.0


# --- Shared piece envelope and printable feature floors --------------------

MAX_BASE_DIAMETER = 22.5                       # mm [derived] adjacent clearance
BASE_RADIUS = MAX_BASE_DIAMETER / 2.0          # mm [derived]
BASE_CLEARANCE_PER_SIDE = (SQUARE_PITCH - MAX_BASE_DIAMETER) / 2.0  # [derived]
MIN_WALL = 1.2                                 # mm [exploration]
MIN_FREE_FEATURE = 2.2                         # mm [exploration]

PEDESTAL_HEIGHT = 17.0                         # mm [assumed]
PEDESTAL_PROFILE = (                           # (radius, z) mm [assumed]
    (0.0, 0.0),
    (BASE_RADIUS, 0.0),
    (BASE_RADIUS, 2.1),
    (10.85, 3.1),
    (10.85, 5.7),
    (9.75, 7.0),
    (7.35, 9.0),
    (6.95, 12.0),
    (6.95, PEDESTAL_HEIGHT),
    (0.0, PEDESTAL_HEIGHT),
)

# Stone: one base groove plus calm horizontal masonry bands.
STONE_GROOVE_Z = (3.65,)                       # mm [assumed]
STONE_BAND_Z = (10.4, 14.1)                    # mm [assumed]
STONE_BAND_RADIUS = 7.55                        # mm [assumed]
STONE_BAND_HEIGHT = 1.20                        # mm [exploration]

# Steel: two tactile channels between three rails, plus vertical structural fins.
STEEL_GROOVE_Z = (3.40, 5.40)                  # mm [derived] centres of two tactile channels
STEEL_FIN_CENTER_RADIUS = 7.25                  # mm [assumed]
STEEL_FIN_RADIAL = 2.20                         # mm [exploration]
STEEL_FIN_TANGENTIAL = 1.60                     # mm [exploration]
STEEL_FIN_START_Z = 8.55                        # mm [assumed]
STEEL_FIN_HEIGHT = 8.15                         # mm [derived]

BASE_GROOVE_MAJOR_RADIUS = 10.95                # mm [assumed]
BASE_GROOVE_MINOR_RADIUS = 0.60                 # mm [exploration]
STEEL_BASE_GROOVE_HEIGHT = 0.80                 # mm [exploration] two-line negative channel
STEEL_BASE_RAIL_Z = (1.80, 3.80, 5.80)          # mm [assumed] starts of three raised rails
STEEL_BASE_RAIL_HEIGHT = 1.20                   # mm [exploration] three nozzle lines
STEEL_BASE_RAIL_RADIUS = BASE_RADIUS            # mm [derived] preserves D22.5 envelope

# Round-2 upper-body language.  Stone projects horizontal masonry terraces;
# Steel projects narrow vertical structural ribs.  The same feature floors are
# reused by every rank so side identity survives above the hand-held base.
UPPER_STONE_TERRACE_HEIGHT = 1.20               # mm [exploration]
UPPER_STONE_TERRACE_PROJECTION = 0.75           # mm [exploration]
UPPER_STEEL_RIB_RADIAL = 2.20                   # mm [exploration]
UPPER_STEEL_RIB_TANGENTIAL = 1.60               # mm [exploration]


# --- Pawn: Manhattan rooftop water tower ----------------------------------

PAWN_HEIGHT = 44.0                             # mm [assumed]
PAWN_COLUMN_Z = 16.55                          # mm [derived overlap]
PAWN_COLUMN_STRAIGHT_HEIGHT = 1.65               # mm [exploration] printable pedestal transition
PAWN_COLUMN_TAPER_Z = 18.00                      # mm [derived] 0.20 mm overlap
PAWN_COLUMN_TAPER_HEIGHT = 11.00                 # mm [derived] preserves original z29 top
PAWN_COLUMN_RADIUS_BOTTOM = 6.95                # mm [derived] flush with pedestal crown
PAWN_COLUMN_RADIUS_TOP = 5.10                   # mm [assumed]
PAWN_TANK_Z = 28.45                            # mm [derived overlap]
PAWN_TANK_RADIUS = 7.10                         # mm [assumed]
PAWN_ROOF_Z = 35.70                            # mm [derived overlap]
PAWN_TANK_HEIGHT = PAWN_ROOF_Z - PAWN_TANK_Z   # mm [derived] ends flush at roof spring line
PAWN_ROOF_HEIGHT = 5.55                         # mm [assumed]
PAWN_ROOF_RADIUS_BOTTOM = 7.10                  # mm [derived]
PAWN_ROOF_RADIUS_TOP = 1.85                     # mm [assumed]
PAWN_FINIAL_Z = 40.75                           # mm [derived overlap]
PAWN_FINIAL_HEIGHT = PAWN_HEIGHT - PAWN_FINIAL_Z  # mm [derived]
PAWN_FINIAL_RADIUS = 1.35                       # mm [exploration]
PAWN_STONE_UPPER_BAND_Z = (30.15, 33.25)        # mm [assumed]
PAWN_STONE_UPPER_BAND_RADIUS = 7.70             # mm [assumed]
PAWN_STEEL_UPPER_FIN_Z = 18.00                  # mm [assumed]
PAWN_STEEL_UPPER_FIN_HEIGHT = 18.00             # mm [assumed]
PAWN_STEEL_UPPER_FIN_CENTER_RADIUS = 6.00       # mm [assumed]


# --- Rook: stepped masonry tower and parapet -------------------------------

ROOK_HEIGHT = 57.0                             # mm [assumed]
ROOK_PEDESTAL_CROWN_Z = 16.00                   # mm [derived overlap with pedestal top]
ROOK_PEDESTAL_CROWN_HEIGHT = 2.40               # mm [exploration] supports square footing
ROOK_PEDESTAL_CROWN_RADIUS = 6.95               # mm [derived] flush with pedestal crown
ROOK_FOOTING_TIERS = (                          # (z, square size, height) mm [assumed]
    (15.10, 9.80, 1.20),
    (16.10, 11.70, 1.20),
    (17.10, 13.60, 1.20),
    (18.10, 15.50, 1.20),
)
ROOK_TOWER_Z = 18.90                           # mm [derived] overlaps top footing
ROOK_TOWER_SIZE = 15.5                         # mm [assumed]
ROOK_TOWER_HEIGHT = 24.6                       # mm [derived] preserves z43.5 top
ROOK_SETBACK_Z = 42.90                          # mm [derived overlap]
ROOK_SETBACK_SIZE = 13.2                        # mm [assumed]
ROOK_SETBACK_HEIGHT = 7.4                       # mm [assumed]
ROOK_ROOF_Z = 49.75                             # mm [derived overlap]
ROOK_ROOF_SIZE = 17.0                           # mm [assumed]
ROOK_ROOF_HEIGHT = 2.8                          # mm [exploration]
ROOK_TURRET_SIZE = 4.4                          # mm [exploration]
ROOK_TURRET_Z = 52.0                            # mm [derived overlap]
ROOK_TURRET_HEIGHT = ROOK_HEIGHT - ROOK_TURRET_Z  # mm [derived]
ROOK_TURRET_OFFSET = (ROOK_ROOF_SIZE - ROOK_TURRET_SIZE) / 2.0  # [derived]
ROOK_STONE_TERRACES = (                         # (z, tower size) mm [assumed]
    (28.20, ROOK_TOWER_SIZE),
    (39.60, ROOK_TOWER_SIZE),
    (46.35, ROOK_SETBACK_SIZE),
)
ROOK_STEEL_RIB_TIERS = (                        # (z, height, tower size) mm [derived]
    (18.20, 25.00, ROOK_TOWER_SIZE),
    (43.10, 6.95, ROOK_SETBACK_SIZE),
)


# --- Knight: angular bridge-tower / horse silhouette ----------------------

KNIGHT_HEIGHT = 59.0                           # mm [assumed]
KNIGHT_DEPTH = 11.0                            # mm [assumed]
KNIGHT_FACE_EDGE_FILLET = 0.80                  # mm [exploration] printable end-face roundover
KNIGHT_PROFILE = (                             # (x, z) mm [assumed]
    (-6.2, 15.7),
    (-6.2, 33.5),
    (-4.8, 43.5),
    (-2.7, 52.5),
    (-1.8, 57.0),
    (-1.8, KNIGHT_HEIGHT),
    (0.8, KNIGHT_HEIGHT),
    (0.8, 56.0),
    (1.6, 54.0),
    (7.6, 51.0),
    (8.1, 46.0),
    (4.1, 43.8),
    (2.5, 37.6),
    (5.1, 28.8),
    (6.2, 15.7),
)
KNIGHT_ARCH_WIDTH = 4.6                        # mm [exploration]
KNIGHT_ARCH_HEIGHT = 8.0                       # mm [exploration]
KNIGHT_ARCH_Z = 18.2                           # mm [assumed]
KNIGHT_ARCH_CENTER_X = 0.0                     # mm [derived symmetry]
KNIGHT_FOOTING_FLARE_Z = 12.00                 # mm [derived] begins on D13.9 pedestal crown
KNIGHT_FOOTING_SHOULDER_Z = 15.30              # mm [exploration] reaches full radius before profile root
KNIGHT_FOOTING_TOP_Z = 18.00                   # mm [derived] preserves the established footing top
KNIGHT_FOOTING_FLARE_RADIUS_BOTTOM = 6.95       # mm [derived] flush with pedestal crown
KNIGHT_FOOTING_RADIUS = 9.20                   # mm [derived] > profile corner by 0.9 mm
KNIGHT_STONE_FACE_BANDS = (                     # (z, x width) mm [assumed]
    (29.60, 9.50),
    (39.80, 12.40),                             # full masonry terrace across sloped profile
)
KNIGHT_STEEL_RIB_X = -1.80                     # mm [assumed] continuous neck land
KNIGHT_STEEL_RIB_Z = 24.50                     # mm [assumed]
KNIGHT_STEEL_RIB_HEIGHT = 28.00                 # mm [assumed]


# --- Bishop: stepped skyscraper with diagonal avenue crown ----------------

BISHOP_HEIGHT = 61.0                           # mm [assumed]
BISHOP_TOWER_Z = 16.55                         # mm [derived overlap]
BISHOP_TOWER_SIZE = 13.40                       # mm [assumed]
BISHOP_TOWER_HEIGHT = 18.00                     # mm [assumed]
BISHOP_SETBACK_ONE_Z = 34.00                    # mm [derived overlap]
BISHOP_SETBACK_ONE_SIZE = 11.20                 # mm [assumed]
BISHOP_SETBACK_ONE_HEIGHT = 11.20               # mm [assumed]
BISHOP_SETBACK_TWO_Z = 44.65                    # mm [derived overlap]
BISHOP_SETBACK_TWO_SIZE = 8.80                  # mm [assumed]
BISHOP_SETBACK_TWO_HEIGHT = 7.50                # mm [assumed]
BISHOP_CROWN_Z = 51.55                          # mm [derived overlap]
BISHOP_CROWN_SIZE = 11.80                       # mm [assumed]
BISHOP_CROWN_HEIGHT = 2.20                      # mm [exploration]
BISHOP_SPIRE_LOWER_Z = 53.20                     # mm [derived overlap]
BISHOP_SPIRE_LOWER_SIZE = 10.40                  # mm [assumed] lower avenue tower
BISHOP_SPIRE_LOWER_HEIGHT = 2.60                 # mm [assumed]
BISHOP_SPIRE_MID_Z = 55.60                       # mm [derived] 0.20 mm overlap
BISHOP_SPIRE_MID_SIZE = 8.20                     # mm [assumed] first crown setback
BISHOP_SPIRE_MID_HEIGHT = 2.60                   # mm [assumed]
BISHOP_SPIRE_TOP_Z = 58.00                       # mm [derived] 0.20 mm overlap
BISHOP_SPIRE_TOP_SIZE = 6.80                     # mm [assumed] printable twin-prong crown
BISHOP_SPIRE_TOP_HEIGHT = BISHOP_HEIGHT - BISHOP_SPIRE_TOP_Z  # mm [derived]
BISHOP_SLOT_WIDTH = 2.20                        # mm [exploration]
BISHOP_SLOT_DEPTH = 16.0                        # mm [derived through-cut]
BISHOP_SLOT_BOTTOM_LEFT_Z = 53.60                # mm [assumed] diagonal avenue floor
BISHOP_SLOT_BOTTOM_RIGHT_Z = 55.00               # mm [assumed] diagonal avenue floor
BISHOP_SLOT_TOP_Z = BISHOP_HEIGHT + 0.50         # mm [derived] open-top through cut
BISHOP_STONE_TERRACES = (                       # (z, tower size) mm [assumed]
    (28.80, BISHOP_TOWER_SIZE),
    (33.75, BISHOP_TOWER_SIZE),
    (43.75, BISHOP_SETBACK_ONE_SIZE),
    (50.80, BISHOP_SETBACK_TWO_SIZE),
)
BISHOP_STEEL_RIB_TIERS = (                      # (z, height, tower size) mm [derived]
    (17.00, 17.20, BISHOP_TOWER_SIZE),
    (34.20, 10.70, BISHOP_SETBACK_ONE_SIZE),
    (44.85, 7.00, BISHOP_SETBACK_TWO_SIZE),
)


# --- Queen: broad four-sided Art Deco fan crown ---------------------------

QUEEN_HEIGHT = 68.0                            # mm [assumed]
QUEEN_TOWER_Z = 16.55                          # mm [derived overlap]
QUEEN_TOWER_SIZE = 14.20                        # mm [assumed]
QUEEN_TOWER_HEIGHT = 18.20                      # mm [assumed]
QUEEN_SETBACK_Z = 34.20                         # mm [derived overlap]
QUEEN_SETBACK_SIZE = 11.80                      # mm [assumed]
QUEEN_SETBACK_HEIGHT = 11.00                    # mm [assumed]
QUEEN_CROWN_BASE_Z = 44.60                      # mm [derived overlap]
QUEEN_CROWN_BASE_SIZE = 9.60                    # mm [assumed]
QUEEN_CROWN_BASE_HEIGHT = 4.00                  # mm [assumed]
QUEEN_FAN_THICKNESS = 4.40                      # mm [exploration]
QUEEN_FAN_ROTATION_DEG = 90.0                   # deg [derived] four-sided crown
QUEEN_FAN_PROFILE = (                           # (x, z) mm [assumed]
    (-4.40, 47.60),
    (-7.00, 53.00),
    (-9.60, 58.00),
    (-9.60, 61.00),
    (-6.80, 61.00),
    (-6.80, 63.50),
    (-3.40, 63.50),
    (-3.40, 66.00),
    (-1.20, QUEEN_HEIGHT),
    (1.20, QUEEN_HEIGHT),
    (3.40, 66.00),
    (3.40, 63.50),
    (6.80, 63.50),
    (6.80, 61.00),
    (9.60, 61.00),
    (9.60, 58.00),
    (7.00, 53.00),
    (4.40, 47.60),
)
QUEEN_STONE_TERRACES = (                        # (z, tower size) mm [assumed]
    (28.80, QUEEN_TOWER_SIZE),
    (34.00, QUEEN_TOWER_SIZE),
    (43.80, QUEEN_SETBACK_SIZE),
)
QUEEN_STEEL_RIB_TIERS = (                       # (z, height, tower size) mm [derived]
    (17.00, 17.40, QUEEN_TOWER_SIZE),
    (34.40, 10.55, QUEEN_SETBACK_SIZE),
)


# --- King: neo-Gothic setback stack with printable beacon cross ------------

KING_HEIGHT = 74.35                            # mm [derived] 83.35 mm assembly
KING_TOWER_Z = 15.80                           # mm [derived] 1.20 mm embedded footing in pedestal
KING_TOWER_SIZE = 14.40                         # mm [assumed]
KING_TOWER_TOP_Z = 35.55                        # mm [derived] preserves established tower silhouette
KING_TOWER_HEIGHT = KING_TOWER_TOP_Z - KING_TOWER_Z  # mm [derived]
KING_SETBACK_ONE_Z = 35.00                      # mm [derived overlap]
KING_SETBACK_ONE_SIZE = 11.80                   # mm [assumed]
KING_SETBACK_ONE_HEIGHT = 12.00                 # mm [assumed]
KING_SETBACK_TWO_Z = 46.40                      # mm [derived overlap]
KING_SETBACK_TWO_SIZE = 9.40                    # mm [assumed]
KING_SETBACK_TWO_HEIGHT = 9.50                  # mm [assumed]
KING_SPIRE_PLINTH_Z = 54.90                     # mm [derived overlap with second setback]
KING_SPIRE_PLINTH_SIZE = 11.80                  # mm [exploration] 1.20 mm printable crown projection
KING_SPIRE_PLINTH_HEIGHT = 1.40                 # mm [exploration] printable crown ledge
KING_SPIRE_Z = 55.30                            # mm [derived overlap]
KING_SPIRE_HEIGHT = 9.50                        # mm [assumed]
KING_SPIRE_RADIUS_BOTTOM = 5.20                 # mm [assumed]
KING_SPIRE_RADIUS_TOP = 2.20                    # mm [exploration]
KING_CROSS_Z = 64.00                           # mm [derived overlap]
KING_CROSS_THICKNESS = 3.20                     # mm [exploration]
KING_CROSS_VERTICAL_HEIGHT = KING_HEIGHT - KING_CROSS_Z  # mm [derived]
KING_CROSS_ARM_WIDTH = 10.40                    # mm [assumed]
KING_CROSS_ARM_HEIGHT = 3.20                    # mm [exploration]
KING_CROSS_ARM_CENTER_Z = 69.20                 # mm [assumed]
KING_STONE_TERRACES = (                         # (z, tower size) mm [assumed]
    (29.20, KING_TOWER_SIZE),
    (34.80, KING_TOWER_SIZE),
    (46.20, KING_SETBACK_ONE_SIZE),
    (55.00, KING_SETBACK_TWO_SIZE),
)
KING_STEEL_RIB_TIERS = (                        # (z, height, tower size) mm [derived]
    (17.00, 18.20, KING_TOWER_SIZE),
    (35.20, 11.50, KING_SETBACK_ONE_SIZE),
    (46.60, 8.95, KING_SETBACK_TWO_SIZE),
)


# --- Presentation and assembly --------------------------------------------

STONE_RGB = (0.72, 0.66, 0.55)                 # [assumed] warm limestone
STEEL_RGB = (0.25, 0.31, 0.36)                 # [assumed] blue gunmetal
BOARD_RGB = (0.10, 0.11, 0.13)                 # [assumed] charcoal night
BACK_RANK = ("rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook")
SIDES = ("stone", "steel")
ROLES = ("pawn", "rook", "knight", "bishop", "queen", "king")


def square_center(file_index: int, rank_index: int) -> tuple[float, float]:
    """Return a standard square center with a1 at the southwest corner."""

    x = (file_index - (FILES - 1) / 2.0) * SQUARE_PITCH
    y = (rank_index - (RANKS - 1) / 2.0) * SQUARE_PITCH
    return x, y


def square_recess_axis(index: int) -> tuple[float, float]:
    """Return centre and span for one recessed-square axis.

    The nominal 0.50 mm land remains unchanged between play squares.  At the
    outside edge of the 8x8 field, a recessed square keeps a full three-line
    1.20 mm top land instead of splitting the nominal land into a 0.25 mm
    sliver.  This avoids an unprintable exposed corner without changing pitch.
    """

    center = (index - (FILES - 1) / 2.0) * SQUARE_PITCH
    lower = center - (SQUARE_PITCH - SQUARE_GRID_LAND) / 2.0
    upper = center + (SQUARE_PITCH - SQUARE_GRID_LAND) / 2.0
    if index == 0:
        lower = -PLAY_SPAN / 2.0 + PLAY_EDGE_LAND
    elif index == FILES - 1:
        upper = PLAY_SPAN / 2.0 - PLAY_EDGE_LAND
    return (lower + upper) / 2.0, upper - lower


def square_top_z(file_index: int, rank_index: int) -> float:
    """a1 is dark/recessed; h1 is light/raised, as standard chess requires."""

    is_light = (file_index + rank_index) % 2 == 1
    return BOARD_THICKNESS + (SQUARE_RELIEF if is_light else 0.0)


def validate_parameters() -> None:
    """Fail before geometry when the dimensional contract drifts."""

    assert abs(BOARD_SIZE - 244.0) < 1e-9
    assert BOARD_SIZE <= 256.0
    assert abs(BOARD_TOTAL_HEIGHT - 9.0) < 1e-9
    assert abs(BOARD_THICKNESS - 8.2) < 1e-9
    assert abs(SQUARE_RELIEF / EXPLORATION_LAYER_HEIGHT - 4.0) < 1e-9
    assert PLAY_EDGE_LAND + 1e-9 >= 3.0 * EXPLORATION_NOZZLE_DIAMETER
    assert len(INTERNAL_GRID_COORDINATES) == FILES - 1
    assert BORDER_STREET_GROOVE_WIDTH + 1e-9 >= 3.0 * EXPLORATION_NOZZLE_DIAMETER
    assert abs(
        BORDER_STREET_GROOVE_CENTER - BORDER_STREET_GROOVE_LENGTH / 2.0
        - PLAY_SPAN / 2.0
    ) < 1e-9
    assert AVENUE_GROOVE_MAX_Y <= -PLAY_SPAN / 2.0
    assert AVENUE_GROOVE_MIN_Y >= -BOARD_SIZE / 2.0
    assert min(abs(AVENUE_GROOVE_CENTER_X - coordinate) for coordinate in INTERNAL_GRID_COORDINATES) >= 10.0
    assert all(
        abs(x1 - x0) < 1e-9 or abs(y1 - y0) < 1e-9
        for (x0, y0), (x1, y1) in zip(AVENUE_STEP_POINTS, AVENUE_STEP_POINTS[1:])
    )
    assert MAX_BASE_DIAMETER <= SQUARE_PITCH - 2.0 * BASE_CLEARANCE_PER_SIDE + 1e-9
    assert BASE_CLEARANCE_PER_SIDE >= 3.0
    assert MIN_FREE_FEATURE >= MIN_WALL
    assert PAWN_HEIGHT < ROOK_HEIGHT < BISHOP_HEIGHT < QUEEN_HEIGHT < KING_HEIGHT
    assert PAWN_COLUMN_STRAIGHT_HEIGHT >= MIN_WALL
    assert PAWN_COLUMN_Z + PAWN_COLUMN_STRAIGHT_HEIGHT > PAWN_COLUMN_TAPER_Z
    assert abs(PAWN_TANK_Z + PAWN_TANK_HEIGHT - PAWN_ROOF_Z) < 1e-9
    assert abs(PAWN_TANK_RADIUS - PAWN_ROOF_RADIUS_BOTTOM) < 1e-9
    assert PAWN_ROOF_Z + PAWN_ROOF_HEIGHT > PAWN_FINIAL_Z
    assert ROOK_PEDESTAL_CROWN_HEIGHT >= MIN_WALL
    assert all(height >= MIN_WALL for _, _, height in ROOK_FOOTING_TIERS)
    assert ROOK_FOOTING_TIERS[0][1] * 2.0**0.5 <= 2.0 * 6.95 + 1e-9
    assert abs(ROOK_TOWER_Z + ROOK_TOWER_HEIGHT - 43.5) < 1e-9
    assert KNIGHT_FOOTING_FLARE_RADIUS_BOTTOM == 6.95
    assert KNIGHT_FOOTING_FLARE_Z < KNIGHT_FOOTING_SHOULDER_Z
    assert KNIGHT_FOOTING_SHOULDER_Z < min(z for _, z in KNIGHT_PROFILE)
    assert KNIGHT_FOOTING_TOP_Z > min(z for _, z in KNIGHT_PROFILE)
    assert KNIGHT_HEIGHT < BISHOP_HEIGHT
    assert abs(BISHOP_SPIRE_TOP_Z + BISHOP_SPIRE_TOP_HEIGHT - BISHOP_HEIGHT) < 1e-9
    assert BISHOP_SPIRE_LOWER_Z + BISHOP_SPIRE_LOWER_HEIGHT > BISHOP_SPIRE_MID_Z
    assert BISHOP_SPIRE_MID_Z + BISHOP_SPIRE_MID_HEIGHT > BISHOP_SPIRE_TOP_Z
    assert (BISHOP_SPIRE_TOP_SIZE - BISHOP_SLOT_WIDTH) / 2.0 >= MIN_FREE_FEATURE - 1e-9
    assert PEDESTAL_HEIGHT - KING_TOWER_Z + 1e-9 >= MIN_WALL
    assert abs(KING_TOWER_Z + KING_TOWER_HEIGHT - KING_TOWER_TOP_Z) < 1e-9
    assert KING_SPIRE_PLINTH_SIZE >= 2.0 * KING_SPIRE_RADIUS_BOTTOM
    assert (KING_SPIRE_PLINTH_SIZE - KING_SETBACK_TWO_SIZE) / 2.0 >= MIN_WALL
    assert KING_SPIRE_PLINTH_HEIGHT >= MIN_WALL
    assert abs(BOARD_TOTAL_HEIGHT + KING_HEIGHT - 83.35) < 1e-9
    assert len(BACK_RANK) == FILES
    assert set(BACK_RANK) == {"rook", "knight", "bishop", "queen", "king"}
    assert len(STONE_GROOVE_Z) == 1
    assert len(STEEL_GROOVE_Z) == 2
    assert len(STEEL_BASE_RAIL_Z) == len(STEEL_GROOVE_Z) + 1
    assert abs(STEEL_BASE_RAIL_Z[0] + STEEL_BASE_RAIL_HEIGHT
               + STEEL_BASE_GROOVE_HEIGHT / 2.0 - STEEL_GROOVE_Z[0]) < 1e-9
    assert abs(STEEL_BASE_RAIL_Z[1] + STEEL_BASE_RAIL_HEIGHT
               + STEEL_BASE_GROOVE_HEIGHT / 2.0 - STEEL_GROOVE_Z[1]) < 1e-9


validate_parameters()
