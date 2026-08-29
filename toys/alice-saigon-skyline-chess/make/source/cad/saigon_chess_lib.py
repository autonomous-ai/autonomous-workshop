"""Parametric geometry for Saigon Skyline Chess.

All dimensions are millimetres. Printable parts are centred on XY with their
lowest face on Z=0. The architectural miniatures are original low-detail
silhouette studies, not measured replicas.
"""

from __future__ import annotations

from build123d import Align, Box, Compound, Cone, Cylinder, Location


# Board and printer contract [assumed from a common 220 mm FDM bed].
BED_X = 220.0
BED_Y = 220.0
BOARD_SIZE = 208.0
GRID_SIZE = 200.0
SQUARE = 25.0
BOARD_BASE_H = 3.2
SQUARE_RELIEF = 0.4
RELIEF_GAP = 0.8
BORDER = 4.0

# Shared piece hierarchy [assumed for a compact display/play edition].
BASE_D = 18.0
ROUND_BASE_R = BASE_D / 2.0
BASE_H = 3.0
UPPER_BASE_D = 14.8
UPPER_BASE_R = UPPER_BASE_D / 2.0
UPPER_BASE_H = 2.2
BODY_Z = BASE_H + UPPER_BASE_H - 0.4
TARGET_HEIGHTS = {
    "pawn": 28.0,
    "rook": 34.0,
    "knight": 38.0,
    "bishop": 43.0,
    "queen": 49.0,
    "king": 55.0,
}
BACK_RANK = ("rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook")

RIVER = "river"
GRID = "grid"
SIDES = (RIVER, GRID)
KINDS = ("pawn", "rook", "knight", "bishop", "queen", "king")


def _z(shape, z: float):
    return Location((0, 0, z)) * shape


def _xyz(shape, x: float, y: float, z: float):
    return Location((x, y, z)) * shape


def _box(x: float, y: float, z: float):
    return Box(x, y, z, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _cyl(radius: float, height: float):
    return Cylinder(radius, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _cone(r1: float, r2: float, height: float):
    return Cone(r1, r2, height, align=(Align.CENTER, Align.CENTER, Align.MIN))


def make_base(side: str):
    """Two tactile team languages: Saigon River rings or city-grid steps."""
    if side == RIVER:
        return _cyl(ROUND_BASE_R, BASE_H) + _z(_cyl(UPPER_BASE_R, UPPER_BASE_H), BASE_H - 0.4)
    if side == GRID:
        return _box(BASE_D, BASE_D, BASE_H) + _z(_box(UPPER_BASE_D, UPPER_BASE_D, UPPER_BASE_H), BASE_H - 0.4)
    raise ValueError(f"unknown side: {side}")


def make_king(side: str):
    """Landmark 81: bundled setbacks and a tall central spire."""
    shape = make_base(side)
    shape += _z(_box(8.0, 8.0, 34.2), BODY_Z)
    for x, y, h in ((-3.2, 0, 29.0), (3.2, 0, 25.0), (0, -3.2, 22.0), (0, 3.2, 18.0)):
        shape += _xyz(_box(4.6, 4.6, h), x, y, BODY_Z)
    shape += _z(_box(6.6, 6.6, 6.2), 38.2)
    shape += _z(_cone(2.3, 1.15, 11.0), 44.0)
    return _finish(shape, f"king_landmark81:{side}", TARGET_HEIGHTS["king"])


def make_queen(side: str):
    """Bitexco Financial Tower: tapered lotus tower and side sky deck."""
    shape = make_base(side)
    shape += _z(_cone(5.3, 3.4, 34.2), BODY_Z)
    shape += _z(_cyl(3.5, 4.2), 38.2)
    shape += _z(_cone(3.0, 0.8, 6.6), 42.4)
    # The outer pier rises continuously from the upper plinth into the deck,
    # turning the landmark's cantilever cue into a support-friendly bridge.
    shape += _xyz(_box(2.4, 2.6, 24.8), 6.0, 0, BODY_Z)
    shape += _xyz(_cyl(2.4, 3.2), 6.6, 0, 28.8)
    shape = shape.clean()
    return _finish(shape, f"queen_bitexco:{side}", TARGET_HEIGHTS["queen"])


def make_bishop(side: str):
    """Notre-Dame Cathedral Basilica: paired towers and twin spires."""
    shape = make_base(side)
    shape += _z(_box(10.0, 7.0, 22.0), BODY_Z)
    for x in (-3.2, 3.2):
        shape += _xyz(_box(4.8, 4.8, 20.0), x, 0, BODY_Z)
        shape += _xyz(_cone(2.2, 0.7, 37.9), x, 0, BODY_Z)
    shape += _xyz(_box(4.0, 1.2, 5.0), 0, -3.8, 17.0)
    return _finish(shape, f"bishop_notre_dame:{side}", TARGET_HEIGHTS["bishop"])


def make_knight(side: str):
    """Independence Palace: long modernist slab, front canopy, flag mast."""
    shape = make_base(side)
    shape += _z(_box(12.0, 8.0, 14.2), BODY_Z)
    shape += _z(_box(15.0, 10.0, 2.0), 18.4)
    shape += _z(_cone(4.2, 0.9, 18.2), 19.8)
    shape += _xyz(_box(8.0, 4.0, 1.6), 0, -5.4, 15.2)
    for x in (-3.0, 3.0):
        shape += _xyz(_box(1.4, 1.4, 10.8), x, -5.8, BODY_Z)
    return _finish(shape, f"knight_independence_palace:{side}", TARGET_HEIGHTS["knight"])


def make_rook(side: str):
    """Bến Thành Market: broad hall, three-faced clock tower, roof finial."""
    shape = make_base(side)
    shape += _z(_box(11.5, 10.0, 10.0), BODY_Z - 0.8)
    shape += _z(_box(6.0, 6.0, 13.2), 13.2)
    shape += _xyz(_box(4.2, 1.6, 4.2), 0, -3.3, 19.0)
    shape += _z(_cone(2.8, 0.75, 19.3), 13.2)
    shape += _z(_cyl(0.7, 1.8), 32.2)
    return _finish(shape, f"rook_ben_thanh:{side}", TARGET_HEIGHTS["rook"])


def make_pawn(side: str):
    """Saigon Central Post Office: long hall, arched roof, clock cupola."""
    shape = make_base(side)
    shape += _z(_box(10.0, 7.0, 10.5), BODY_Z)
    roof = Location((0, 0, 14.2), (90, 0, 0)) * Cylinder(
        4.8, 6.4, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    shape += roof
    shape += _z(_box(3.6, 3.6, 5.8), 18.3)
    shape += _z(_cone(1.7, 0.6, 9.7), 18.3)
    return _finish(shape, f"pawn_central_post_office:{side}", TARGET_HEIGHTS["pawn"])


BUILDERS = {
    "king": make_king,
    "queen": make_queen,
    "bishop": make_bishop,
    "knight": make_knight,
    "rook": make_rook,
    "pawn": make_pawn,
}


def _finish(shape, label: str, target_height: float):
    solids = list(shape.solids())
    assert len(solids) == 1, f"{label} must be one printable solid, got {len(solids)}"
    bounds = shape.bounding_box()
    assert abs(bounds.min.Z) < 1e-6
    assert bounds.size.X <= BASE_D + 1e-6 and bounds.size.Y <= BASE_D + 1e-6
    assert abs(bounds.max.Z - target_height) <= 0.6, (label, bounds.max.Z, target_height)
    shape.label = label
    return shape


def make_piece(kind: str, side: str):
    if kind not in BUILDERS:
        raise ValueError(f"unknown kind: {kind}")
    return BUILDERS[kind](side)


def make_board():
    """One-piece relief board; raised squares overlap the base by 0.2 mm."""
    board = _box(BOARD_SIZE, BOARD_SIZE, BOARD_BASE_H)
    x0 = -GRID_SIZE / 2.0 + SQUARE / 2.0
    y0 = x0
    for rank in range(8):
        for file_index in range(8):
            if (rank + file_index) % 2 == 0:
                tile = _box(SQUARE - RELIEF_GAP, SQUARE - RELIEF_GAP, SQUARE_RELIEF + 0.2)
                board += _xyz(tile, x0 + file_index * SQUARE, y0 + rank * SQUARE, BOARD_BASE_H - 0.2)
    for x, y, sx, sy in (
        (-(GRID_SIZE + BORDER) / 2, 0, BORDER, BOARD_SIZE),
        ((GRID_SIZE + BORDER) / 2, 0, BORDER, BOARD_SIZE),
        (0, -(GRID_SIZE + BORDER) / 2, GRID_SIZE, BORDER),
        (0, (GRID_SIZE + BORDER) / 2, GRID_SIZE, BORDER),
    ):
        board += _xyz(_box(sx, sy, 1.0), x, y, BOARD_BASE_H - 0.2)
    assert len(board.solids()) == 1
    board.label = "relief_chessboard"
    return board


def square_surface(file_index: int, rank: int) -> float:
    return BOARD_BASE_H + (SQUARE_RELIEF if (file_index + rank) % 2 == 0 else 0.0)


def make_play_assembly():
    """Labelled uncoloured opening layout; the combined model is view-only."""
    children = []
    board = make_board()
    children.append(board)
    origin = -GRID_SIZE / 2.0 + SQUARE / 2.0
    inventory = []
    for side, back_rank, pawn_rank, back_order in (
        (RIVER, 0, 1, BACK_RANK),
        (GRID, 7, 6, tuple(reversed(BACK_RANK))),
    ):
        for file_index, kind in enumerate(back_order):
            piece = make_piece(kind, side)
            x = origin + file_index * SQUARE
            y = origin + back_rank * SQUARE
            z = square_surface(file_index, back_rank)
            # The local knight canopy points toward -Y. Rotate River knights so
            # both armies' directional façades face inward toward the opponent.
            orientation = (0, 0, 180) if side == RIVER and kind == "knight" else (0, 0, 0)
            placed = Location((x, y, z), orientation) * piece
            placed.label = f"{side}:{kind}:back:{file_index + 1}"
            children.append(placed)
            inventory.append((side, kind))
        for file_index in range(8):
            piece = make_pawn(side)
            x = origin + file_index * SQUARE
            y = origin + pawn_rank * SQUARE
            z = square_surface(file_index, pawn_rank)
            placed = Location((x, y, z)) * piece
            placed.label = f"{side}:pawn:{file_index + 1}"
            children.append(placed)
            inventory.append((side, "pawn"))
    assert len(children) == 33
    assert len(inventory) == 32
    return Compound(children=children, label="saigon_skyline_chess")
