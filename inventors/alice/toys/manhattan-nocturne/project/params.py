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
BOARD_THICKNESS = 8.65                         # mm [assumed]
SQUARE_RELIEF = 0.35                           # mm [assumed]
SQUARE_GRID_LAND = 0.50                        # mm [exploration] avoids non-manifold four-corner steps
BOARD_TOTAL_HEIGHT = BOARD_THICKNESS + SQUARE_RELIEF  # mm [derived]
BOOLEAN_OVERLAP = 0.08                         # mm [assumed] robust B-rep union
BOOLEAN_OVERSHOOT = 0.50                       # mm [assumed] robust through-cut
AVENUE_GROOVE_LENGTH = 11.0                    # mm [assumed] one Broadway cue
AVENUE_GROOVE_WIDTH = 1.15                     # mm [exploration]
AVENUE_GROOVE_DEPTH = 0.30                     # mm [exploration]
AVENUE_GROOVE_ANGLE_DEG = 32.0                 # deg [assumed] art direction
AVENUE_GROOVE_CENTER_Y = -(BOARD_SIZE / 2.0 - OUTER_BORDER / 2.0)  # [derived]


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
STONE_BAND_HEIGHT = 0.90                        # mm [exploration]

# Steel: two base grooves plus four vertical structural fins.
STEEL_GROOVE_Z = (2.85, 5.55)                  # mm [assumed]
STEEL_FIN_CENTER_RADIUS = 7.25                  # mm [assumed]
STEEL_FIN_RADIAL = 2.20                         # mm [exploration]
STEEL_FIN_TANGENTIAL = 1.45                     # mm [exploration]
STEEL_FIN_START_Z = 8.55                        # mm [assumed]
STEEL_FIN_HEIGHT = 8.15                         # mm [derived]

BASE_GROOVE_MAJOR_RADIUS = 10.95                # mm [assumed]
BASE_GROOVE_MINOR_RADIUS = 0.60                 # mm [exploration]


# --- Pawn: Manhattan rooftop water tower ----------------------------------

PAWN_HEIGHT = 44.0                             # mm [assumed]
PAWN_COLUMN_Z = 16.55                          # mm [derived overlap]
PAWN_COLUMN_HEIGHT = 12.45                      # mm [assumed]
PAWN_COLUMN_RADIUS_BOTTOM = 6.55                # mm [assumed]
PAWN_COLUMN_RADIUS_TOP = 5.10                   # mm [assumed]
PAWN_TANK_Z = 28.45                            # mm [derived overlap]
PAWN_TANK_HEIGHT = 7.80                         # mm [assumed]
PAWN_TANK_RADIUS = 7.10                         # mm [assumed]
PAWN_ROOF_Z = 35.70                            # mm [derived overlap]
PAWN_ROOF_HEIGHT = 5.55                         # mm [assumed]
PAWN_ROOF_RADIUS_BOTTOM = 7.10                  # mm [derived]
PAWN_ROOF_RADIUS_TOP = 1.85                     # mm [assumed]
PAWN_FINIAL_Z = 40.75                           # mm [derived overlap]
PAWN_FINIAL_HEIGHT = PAWN_HEIGHT - PAWN_FINIAL_Z  # mm [derived]
PAWN_FINIAL_RADIUS = 1.35                       # mm [exploration]


# --- Rook: stepped masonry tower and parapet -------------------------------

ROOK_HEIGHT = 57.0                             # mm [assumed]
ROOK_TOWER_Z = 16.50                           # mm [derived overlap]
ROOK_TOWER_SIZE = 15.5                         # mm [assumed]
ROOK_TOWER_HEIGHT = 27.0                        # mm [assumed]
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


# --- Knight: angular bridge-tower / horse silhouette ----------------------

KNIGHT_HEIGHT = 59.0                           # mm [assumed]
KNIGHT_DEPTH = 11.0                            # mm [assumed]
KNIGHT_PROFILE = (                             # (x, z) mm [assumed]
    (-6.2, 15.7),
    (-6.2, 33.5),
    (-4.8, 43.5),
    (-2.7, 52.5),
    (-0.6, KNIGHT_HEIGHT),
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


# --- Bishop: slender tower with diagonal light canyon ---------------------

BISHOP_HEIGHT = 61.0                           # mm [assumed]
BISHOP_TOWER_Z = 16.55                         # mm [derived overlap]
BISHOP_TOWER_HEIGHT = 24.0                      # mm [assumed]
BISHOP_TOWER_RADIUS_BOTTOM = 6.75               # mm [assumed]
BISHOP_TOWER_RADIUS_TOP = 4.40                  # mm [assumed]
BISHOP_CROWN_Z = 39.95                         # mm [derived overlap]
BISHOP_CROWN_HEIGHT = 3.20                      # mm [assumed]
BISHOP_CROWN_RADIUS = 6.55                      # mm [assumed]
BISHOP_SPIRE_Z = 42.55                         # mm [derived overlap]
BISHOP_SPIRE_HEIGHT = BISHOP_HEIGHT - BISHOP_SPIRE_Z  # mm [derived]
BISHOP_SPIRE_RADIUS_BOTTOM = 5.85               # mm [assumed]
BISHOP_SPIRE_RADIUS_TOP = 1.45                  # mm [exploration]
BISHOP_SLOT_WIDTH = 1.70                        # mm [exploration]
BISHOP_SLOT_DEPTH = 16.0                        # mm [derived through-cut]
BISHOP_SLOT_HEIGHT = 10.5                       # mm [assumed]
BISHOP_SLOT_CENTER_Z = 53.2                     # mm [assumed]
BISHOP_SLOT_ANGLE_DEG = -31.0                   # deg [assumed]


# --- Queen: broad illuminated crown ---------------------------------------

QUEEN_HEIGHT = 68.0                            # mm [assumed]
QUEEN_TOWER_Z = 16.55                          # mm [derived overlap]
QUEEN_TOWER_HEIGHT = 27.8                       # mm [assumed]
QUEEN_TOWER_RADIUS_BOTTOM = 7.05                # mm [assumed]
QUEEN_TOWER_RADIUS_TOP = 4.90                   # mm [assumed]
QUEEN_CROWN_Z = 43.75                           # mm [derived overlap]
QUEEN_CROWN_HEIGHT = 4.20                       # mm [assumed]
QUEEN_CROWN_RADIUS = 8.10                       # mm [assumed]
QUEEN_SPIRE_Z = 47.35                           # mm [derived overlap]
QUEEN_SPIRE_HEIGHT = 16.85                      # mm [assumed]
QUEEN_SPIRE_RADIUS_BOTTOM = 6.45                # mm [assumed]
QUEEN_SPIRE_RADIUS_TOP = 1.85                   # mm [exploration]
QUEEN_ORB_RADIUS = 2.15                         # mm [exploration]
QUEEN_ORB_CENTER_Z = QUEEN_HEIGHT - QUEEN_ORB_RADIUS  # mm [derived]


# --- King: tallest setback tower with restrained beacon cross -------------

KING_HEIGHT = 74.35                            # mm [derived] 83.35 mm assembly
KING_TOWER_Z = 16.55                           # mm [derived overlap]
KING_TOWER_HEIGHT = 30.4                        # mm [assumed]
KING_TOWER_RADIUS_BOTTOM = 7.20                 # mm [assumed]
KING_TOWER_RADIUS_TOP = 5.00                    # mm [assumed]
KING_CROWN_Z = 46.35                            # mm [derived overlap]
KING_CROWN_HEIGHT = 4.40                        # mm [assumed]
KING_CROWN_RADIUS = 7.30                        # mm [assumed]
KING_SPIRE_Z = 50.15                           # mm [derived overlap]
KING_SPIRE_HEIGHT = 13.25                       # mm [assumed]
KING_SPIRE_RADIUS_BOTTOM = 5.90                 # mm [assumed]
KING_SPIRE_RADIUS_TOP = 2.00                    # mm [exploration]
KING_CROSS_Z = 62.80                           # mm [derived overlap]
KING_CROSS_THICKNESS = 2.80                     # mm [exploration]
KING_CROSS_VERTICAL_HEIGHT = KING_HEIGHT - KING_CROSS_Z  # mm [derived]
KING_CROSS_ARM_WIDTH = 9.20                     # mm [assumed]
KING_CROSS_ARM_HEIGHT = 2.80                    # mm [exploration]
KING_CROSS_ARM_CENTER_Z = 68.75                 # mm [assumed]


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


def square_top_z(file_index: int, rank_index: int) -> float:
    """a1 is dark/recessed; h1 is light/raised, as standard chess requires."""

    is_light = (file_index + rank_index) % 2 == 1
    return BOARD_THICKNESS + (SQUARE_RELIEF if is_light else 0.0)


def validate_parameters() -> None:
    """Fail before geometry when the dimensional contract drifts."""

    assert abs(BOARD_SIZE - 244.0) < 1e-9
    assert BOARD_SIZE <= 256.0
    assert MAX_BASE_DIAMETER <= SQUARE_PITCH - 2.0 * BASE_CLEARANCE_PER_SIDE + 1e-9
    assert BASE_CLEARANCE_PER_SIDE >= 3.0
    assert MIN_FREE_FEATURE >= MIN_WALL
    assert PAWN_HEIGHT < ROOK_HEIGHT < BISHOP_HEIGHT < QUEEN_HEIGHT < KING_HEIGHT
    assert KNIGHT_HEIGHT < BISHOP_HEIGHT
    assert abs(BOARD_TOTAL_HEIGHT + KING_HEIGHT - 83.35) < 1e-9
    assert len(BACK_RANK) == FILES
    assert set(BACK_RANK) == {"rook", "knight", "bishop", "queen", "king"}
    assert len(STONE_GROOVE_Z) == 1
    assert len(STEEL_GROOVE_Z) == 2


validate_parameters()
