"""Antisol - every dimension the set is built from, in one place.

Provenance tags follow the Wish: [observed] is a measured real-world fact or a
value read off the sealed reference images, [inferred] is derived from those by
the stated arithmetic, [assumed] is a build decision this project made.

Coordinate convention
---------------------
Board: origin at the centre of the 7x9 field, +X toward file g, +Y toward rank
9, +Z up out of the play surface.  Field datum (the top of the board) is Z = 0
for board maths and Z = BOARD_THICKNESS for the printed panel, whose bed datum
is Z = 0.

Piece: origin at the centre of the disc's bed face, +Z up.  A Sol world leans
its north pole toward +X, an Anti-Sol world toward -X.
"""

from __future__ import annotations

import math

# ---------------------------------------------------------------- printing --
NOZZLE_MM = 0.4                      # [assumed] the print this is gated at
MIN_WALL_MM = 2 * NOZZLE_MM          # [inferred] 0.80 mm
BED_MM = 200.0                       # [assumed] 200 x 200 bed
OVERHANG_LIMIT_DEG = 45.0            # [assumed] slope from vertical held unaided

# ------------------------------------------------------------------- board --
FILES = 7                            # [observed, Leiden] a-g
RANKS = 9                            # [observed, Leiden] 1-9
CELL_PITCH = 36.00                   # [assumed] one cell
BOARD_BORDER = 8.00                  # [assumed] free border outside the field
BOARD_THICKNESS = 9.00               # [assumed]
FIELD_W = FILES * CELL_PITCH         # 252.00
FIELD_D = RANKS * CELL_PITCH         # 324.00
BOARD_W = FIELD_W + 2 * BOARD_BORDER # 268.00
BOARD_D = FIELD_D + 2 * BOARD_BORDER # 340.00

GROOVE_W = 1.20                      # [inferred] three extrusion widths
GROOVE_D = 0.60                      # [assumed]

POCKET_SIZE = 34.80                  # [assumed] every terrain pocket is this
POCKET_DEPTH = 6.00                  # [assumed]
POCKET_CORNER_R = 1.00               # [assumed]
POCKET_INSET = (CELL_PITCH - POCKET_SIZE) / 2.0   # 0.60 from the cell boundary
POCKET_SEAM_INSET = 1.00             # [inferred] where a pocket edge lands on a
                                     # panel seam, the panel keeps a 1.00 mm
                                     # wall of its own: 0.60 leaves each panel
                                     # half a rib, and half a rib is below the
                                     # printable wall at a 0.4 mm nozzle
RIB_BETWEEN_POCKETS = CELL_PITCH - POCKET_SIZE    # 1.20 mm within one panel
RIB_ACROSS_SEAM = 2 * POCKET_SEAM_INSET           # 2.00 mm across a panel seam

TILE_CLEARANCE = 0.25                # [assumed] per side, tile into pocket
TILE_SIZE = CELL_PITCH - 2 * POCKET_SEAM_INSET - 2 * TILE_CLEARANCE   # 33.50

# panel split: after file c (index 2) and after rank 4 (index 3)
PANEL_FILE_CUT = 3                   # files 0..2 west, 3..6 east
PANEL_RANK_CUT = 4                   # ranks 0..3 south, 4..8 north

# terrain, cells given as (file_index, rank_index)
DEN_CELLS = {"sol": (3, 0), "anti": (3, 8)}                    # [observed, Leiden] d1, d9
TRAP_CELLS = {
    "sol": [(2, 0), (3, 1), (4, 0)],                            # [observed, Leiden] c1, d2, e1
    "anti": [(2, 8), (3, 7), (4, 8)],                           # [observed, Leiden] c9, d8, e9
}
BELT_CELLS = [(f, r) for f in (1, 2, 4, 5) for r in (3, 4, 5)]  # [inferred] b-c, e-f x 4-6

# ------------------------------------------------------------------ pieces --
DISC_D_TOP_SOL = 34.00               # [assumed] Sol flares outward as it rises
DISC_D_BOT_SOL = 33.00
DISC_D_TOP_ANTI = 33.00              # [assumed] Anti-Sol collapses inward
DISC_D_BOT_ANTI = 34.00
DISC_H = 5.00                        # [assumed]
DISC_TOP_ROUND = 0.60                # [assumed]
DISC_NOMINAL_D = 34.00               # the diameter every fit is derived from

GLOBE_SINK = 2.00                    # [assumed] globe sunk into the disc top
SEAT_LATITUDE_DEG = -42.0            # [assumed] where the seat cone springs
SEAT_DRAFT_DEG = 12.0                # [assumed] from vertical, spreading down
RELIEF_DEPTH = 1.20                  # [assumed] how deep a colour inlay runs
                                     # into the globe: three extrusion widths,
                                     # and shallow enough that a marking never
                                     # reaches the other side of a small world

NUMERAL_H = 3.60                     # [assumed] seven-segment digit height
NUMERAL_W = 2.80                     # [assumed]
NUMERAL_STROKE = 1.00                # [assumed]
NUMERAL_Z = 2.20                     # [assumed] centre height on the disc wall
NUMERAL_DEPTH = 0.60                 # [assumed] flush colour inlay depth

# rank -> planet, equatorial diameter km [observed, NASA fact sheets],
# globe diameter mm [inferred] = 13.785 * (D / 4879) ** 0.2,
# axial tilt deg [observed].
PLANETS = {
    "mercury": {"rank": 1, "d_km": 4879.0, "globe_d": 13.78, "tilt": 0.03},
    "mars":    {"rank": 2, "d_km": 6779.0, "globe_d": 14.72, "tilt": 25.19},
    "venus":   {"rank": 3, "d_km": 12104.0, "globe_d": 16.53, "tilt": 177.36},
    "earth":   {"rank": 4, "d_km": 12742.0, "globe_d": 16.70, "tilt": 23.44},
    "neptune": {"rank": 5, "d_km": 49244.0, "globe_d": 21.89, "tilt": 28.32},
    "uranus":  {"rank": 6, "d_km": 50724.0, "globe_d": 22.02, "tilt": 97.77},
    "saturn":  {"rank": 7, "d_km": 116460.0, "globe_d": 26.00, "tilt": 26.73},
    "jupiter": {"rank": 8, "d_km": 139820.0, "globe_d": 26.97, "tilt": 3.13},
}
LADDER_CONSTANT = 13.785             # [inferred] set by Saturn's ring ceiling
LADDER_EXPONENT = 0.2                # [inferred] the fifth root

SIDES = ("sol", "anti")


def globe_diameter(planet: str) -> float:
    return PLANETS[planet]["globe_d"]


def globe_radius(planet: str) -> float:
    return globe_diameter(planet) / 2.0


def globe_centre_z(planet: str) -> float:
    """[inferred] 3.00 + globe_D / 2 -- the globe sunk 2.00 mm into a 5.00 disc."""
    return DISC_H - GLOBE_SINK + globe_radius(planet)


def seat_contact_radius(planet: str) -> float:
    return globe_radius(planet) * math.cos(math.radians(SEAT_LATITUDE_DEG))


def seat_contact_z(planet: str) -> float:
    return globe_centre_z(planet) + globe_radius(planet) * math.sin(
        math.radians(SEAT_LATITUDE_DEG)
    )


def seat_land_radius(planet: str) -> float:
    drop = seat_contact_z(planet) - DISC_H
    return seat_contact_radius(planet) + drop * math.tan(math.radians(SEAT_DRAFT_DEG))


def piece_height(planet: str) -> float:
    """[inferred] disc, less the sink, plus the globe."""
    return DISC_H - GLOBE_SINK + globe_diameter(planet)


def lean_sign(side: str) -> float:
    """Sol leans its north pole toward +X, Anti-Sol toward -X."""
    return 1.0 if side == "sol" else -1.0


# ------------------------------------------------------ Saturn's ring system --
RING_INNER_D = 26.00                 # [assumed] tangent to Saturn's equator
RING_OUTER_D = 30.00                 # [inferred] 2.00 mm of projection per side.
                                     # The Wish's own fallback, taken because the
                                     # web under a 3.00 mm projection reads as a
                                     # funnel rather than as a thickened ring
RING_THICKNESS = 1.40                # [assumed]
RING_GLOBE_BITE = 1.00               # [assumed] how far the ring cuts into the globe
RING_WEB_SECTORS = 96                # [assumed] azimuth resolution of the web
RING_WEB_INNER_R = 5.00              # [assumed] keeps the web sectors off the axis
RING_WEB_OVERLAP = 0.45              # [assumed] how far the web reaches up into
                                     # the ring plate, so the two fuse across a
                                     # real overlap rather than a shared face
RING_WEB_DROP = 0.30                 # [assumed] how far the support cone starts
                                     # below the ring's lower outer rim, so the
                                     # web wraps that rim instead of meeting it
                                     # at zero thickness and leaving a sliver of
                                     # bare underside behind
RING_WEB_SLOPE = 1.08                # [assumed] rise per unit run: 47.2 deg from
                                     # horizontal, clear of the 45 deg gate

# ------------------------------------------------------------- belt tile ----
BELT_FLOOR_DROP = 2.00               # [assumed] rubble floor below field datum
BELT_PAD_D = 26.00                   # [assumed] smooth landing pad
BELT_TILE_H = POCKET_DEPTH           # 6.00, top flush with the field
BELT_RUBBLE_SEED = 20260916          # [assumed] deterministic rubble

# ------------------------------------------------------------ den and corona -
DEN_FLANGE = 36.00                   # [assumed] covers the cell edge to edge
DEN_PROUD = 2.20                     # [inferred] the highest ordinary surface.
                                     # 1.30 of drafted skirt plus 0.90 of vertical
                                     # rim: the least that clears both the 45 deg
                                     # overhang gate and the 0.80 mm wall gate
DEN_SPIGOT = TILE_SIZE               # 33.50, the same body the pockets take
DEN_SPIGOT_DEPTH = POCKET_DEPTH      # 6.00
DEN_CHAMFER = (DEN_FLANGE - DEN_SPIGOT) / 2.0   # 0.85 of horizontal run
DEN_CHAMFER_RISE = 1.30              # [inferred] 48.1 deg from horizontal
DEN_GRAIN_DEPTH = 0.40               # [inferred] hex granulation, engraved into
                                     # the four corners rather than raised: a
                                     # 0.50 mm relief on a 0.85 mm frame is under
                                     # the printable wall at a 0.4 mm nozzle
DEN_GRAIN_PITCH = 2.20               # [assumed]

FLARE_BASE_D = 6.00                  # [inferred] narrow enough that the whole
                                     # base stands on the flange, so no part of
                                     # a flame has to be cut back to a roof
FLARE_HEIGHT = 18.00                 # [assumed] above field datum
FLARE_TIP_R = 0.75                   # [assumed]
FLARE_LEAN_DEG = 12.0                # [assumed] outward from vertical
FLARE_SUPPORT_SLOPE = 1.08           # [assumed] the 45 deg roof the overhanging
                                     # part of a flare base is cut back to
FLARE_DIAGONAL = 20.80               # [inferred] 0.87 mm clear of the den's own
                                     # seated disc, and 0.29 mm inside the
                                     # flange corner, so the base is wholly
                                     # supported

CORONA_TILE = TILE_SIZE              # 33.50 -- every terrain pocket is the same,
                                     # so the corona floor is the same tile as the belt
CORONA_TILE_H = 3.00                 # [assumed] leaves a 3.00 mm well
CORONA_ENGRAVE_D = 0.40              # [assumed] flame tongues cut into the face
CORONA_ENGRAVE_COUNT = 16            # [inferred] as many tongues as stay apart
CORONA_ENGRAVE_INNER = 6.50          # [inferred] where the tongues start
CORONA_ENGRAVE_EYE_D = 9.00          # [assumed] the star they radiate from
CORONA_TONGUE_BASE_D = 5.00          # [inferred] fits the tile and clears the disc
CORONA_TONGUE_H = 4.00               # [assumed] above field datum
CORONA_TONGUE_TIP_R = 0.60           # [assumed]
CORONA_TONGUE_DIAGONAL = 20.20       # [inferred] 0.70 clear of the seated disc,
                                     # 0.37 inside the tile edge
CORONA_WELL_DROP = 3.00              # [assumed] how far a trapped world sits down

# ----------------------------------------------------------------- storage --
TRAY_W = 164.00                      # [assumed]
TRAY_D = 88.00                       # [assumed]
TRAY_H = 6.00                        # [assumed]
TRAY_SOCKET_D = 34.40                # [inferred] Ø34.00 disc + 0.20 per side
TRAY_SOCKET_DEPTH = 3.50             # [assumed]
TRAY_PITCH = 38.00                   # [assumed]
TRAY_COLS = 4
TRAY_ROWS = 2

# --------------------------------------------------------------- filaments --
# sRGB hex exactly as the Bambu Lab PLA Lite catalogue publishes it.  The shop
# reads the sealed Color() channels as sRGB, so they are authored unconverted.
FILAMENT_HEX = {
    "beige": "#F7E6DE",
    "black": "#000000",
    "blue": "#004EA8",
    "cocoa_brown": "#8E3C06",
    "cyan": "#00FFFF",
    "dark_gray": "#6F6E6D",
    "gray": "#9FA19F",
    "green": "#00BB31",
    "orange": "#FF671F",
    "red": "#FF0000",
    "sunflower_yellow": "#FFB549",
    "white": "#FFFEF7",
    "yellow": "#FFD834",
}

DISC_COLOUR = {"sol": "white", "anti": "black"}
NUMERAL_COLOUR = {"sol": "black", "anti": "white"}
DEN_PLUG_COLOUR = {"sol": "sunflower_yellow", "anti": "black"}
FLAME_COLOUR = {"sol": "orange", "anti": "cyan"}

GLOBE_COLOUR = {
    "mercury": "gray",
    "mars": "red",
    "venus": "beige",
    "earth": "blue",
    "neptune": "blue",
    "uranus": "cyan",
    "saturn": "yellow",
    "jupiter": "orange",
}

BOARD_COLOUR = "dark_gray"
BELT_COLOUR = "cocoa_brown"
TRAY_COLOUR = "gray"

# ------------------------------------------------------------ opening setup --
# [inferred] the standard layout; the Leiden page does not fix it.
SOL_SETUP = {
    "saturn": (0, 0), "uranus": (6, 0),
    "earth": (1, 1), "mars": (5, 1),
    "mercury": (0, 2), "neptune": (2, 2), "venus": (4, 2), "jupiter": (6, 2),
}
ANTI_SETUP = {name: (FILES - 1 - f, RANKS - 1 - r) for name, (f, r) in SOL_SETUP.items()}


def cell_centre(file_index: int, rank_index: int) -> tuple[float, float]:
    """Board-frame XY of one cell centre."""
    x = -FIELD_W / 2.0 + CELL_PITCH * (file_index + 0.5)
    y = -FIELD_D / 2.0 + CELL_PITCH * (rank_index + 0.5)
    return x, y
