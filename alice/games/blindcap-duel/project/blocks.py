"""Golden blocks for board-game geometry. Human-approved; PR only.

Composition over invention: BUILD is told to reach for these first and
hand-roll only what they do not cover. cadlib already owns the generic
vocabulary (grid_points, slot_for/peg_for, add_dovetail_slot,
add_press_fit_pocket, soften_edges); this module is only the board-game
specific layer, and only for patterns this project has EVIDENCE for.

Every block here traces to a recorded outcome, named in its docstring. A block
with no evidence behind it is a guess with a nice interface, and the one thing
15 turns of history is good for is telling us which guesses were wrong.
"""
from __future__ import annotations

import cadquery as cq

from cadlib.fits import peg_for, slot_for

# A fingertip needs roughly this much to hook a piece out of a recess. Same
# number as ergonomics_check.FINGER_ROOM_MM — they describe one hand.
FINGER_NOTCH_MM = 12.0

# Bambu Lab P2S usable bed, matching gate.py. A tile bigger than this is not a
# tile, it is a second gate failure waiting to happen.
MAX_TILE_MM = 246.0


def shared_positions(cols: int, rows: int, pitch: float,
                     z: float = 0.0) -> list[tuple[float, float, float]]:
    """The one position list that every layer must be built from.

    Evidence: turn 14 (`cross_positions()`) and turn 15 (`small_centers()`)
    both scored their only clean structural passes by generating a pattern
    once and reusing it for the holes AND the pieces that sit in them, making
    alignment correct by construction rather than by two coordinate lists that
    happen to agree. Both turns' write-ups called this out independently; it
    is the most reliable habit in the record.

    Call this once, then feed the SAME list to `cut_wells` and
    `add_piece_family`. Never restate the coordinates.
    """
    x0 = -(cols - 1) * pitch / 2.0
    y0 = -(rows - 1) * pitch / 2.0
    return [(x0 + c * pitch, y0 + r * pitch, z)
            for r in range(rows) for c in range(cols)]


def cut_wells(board, positions, diameter: float, depth: float,
              top_z: float, notch: bool = True):
    """Cut a seat at every position, each with a thumb scallop at its rim.

    Evidence: turn 15's Sluice Row put 7mm seed-weights on the floor of 26mm
    wide, 16mm deep wells — 9mm below the rim with 3mm of room around them.
    Every geometric check passed and the piece is not retrievable by hand.
    A plain cylindrical pocket is the default shape everyone reaches for and
    it is the shape that fails, so the notch is on by default here: you have
    to ask for the broken version.
    """
    for x, y, _ in positions:
        cutter = cq.Workplane("XY").cylinder(depth, diameter / 2.0).translate(
            (x, y, top_z - depth / 2.0))
        board = board.cut(cutter)
        if notch:
            scallop = cq.Workplane("XY").cylinder(
                depth, FINGER_NOTCH_MM / 2.0).translate(
                (x + diameter / 2.0, y, top_z - depth / 2.0))
            board = board.cut(scallop)
    return board


def add_piece_family(asm: cq.Assembly, shape, positions, name: str,
                     lift: float = 0.0) -> cq.Assembly:
    """Place N copies of one shape as SEPARATELY NAMED assembly children.

    Evidence: this is the failure that ended turns 11-15. 48 loose tiles laid
    out beside a board came back as one continuous mat; 65 pieces collapsed
    into a single solid with the grid merely engraved on its lid. Named
    children are what make the pieces exist as pieces — gate.py's bill check
    counts exactly these names, so a family added through this function is
    countable by construction.

    Never `union()` pieces that the rules require to be loose.
    """
    for i, (x, y, z) in enumerate(positions, 1):
        asm.add(shape, name=f"{name}_{i:02d}",
                loc=cq.Location(cq.Vector(x, y, z + lift)))
    return asm


def seated_pair(piece_mm: float, fit: str = "free") -> tuple[float, float]:
    """The piece's own size in, both halves of the mate out: (piece_d, seat_d).

    The nominal is the PIECE, because the piece is the thing the rules talk
    about ("a 20mm disc"); the seat is derived from it and never stated
    independently.

    Evidence: turn 14 shipped an internal contradiction — the component list
    said a 10mm peg while the fit threshold implied 11.4mm — and the writer
    had to arbitrate between two numbers that should never have been two
    numbers. Turn 14's Twin Deck Solitaire, which did work, derived both
    halves from one value and passed 64/64.

    Default fit is `free` (0.40mm per side): a board game piece is handled
    hundreds of times and must drop in, not be pressed in. That is the same
    0.40mm ergonomics_check.MIN_SEAT_CLEARANCE_MM requires — one number, two
    places that must not disagree.

    Note what this function must NOT do: call peg_for AND slot_for on the same
    nominal. That yields a male at nominal-2c and a female at nominal+2c, so
    the real gap is 4c — double the intended fit, from code whose whole
    purpose is to stop exactly that kind of drift. It shipped that way here
    for one commit; the testbench caught it.
    """
    return piece_mm, slot_for(piece_mm, fit)


def tiled_board(width: float, depth: float, thickness: float,
                max_tile: float = MAX_TILE_MM) -> list[dict]:
    """Split a board too big for the bed into printable interlocking tiles.

    Not evidence from a failure but from a constraint: the P2S bed caps any
    piece at 246mm, and turn 15's board was 366mm. Every large board from here
    on is a tiled board, so the split belongs in one reviewed place rather
    than being re-derived per idea.

    Returns tile descriptors {name, w, d, x, y}; the caller cuts the joins
    with cadlib.mechanical.add_dovetail_slot and adds each tile to the
    assembly under its own name so gate.py can count them.
    """
    cols = max(1, -(-int(width) // int(max_tile)))
    rows = max(1, -(-int(depth) // int(max_tile)))
    tw, td = width / cols, depth / rows
    tiles = []
    for r in range(rows):
        for c in range(cols):
            tiles.append({
                "name": f"board_tile_{r * cols + c + 1:02d}",
                "w": tw, "d": td, "t": thickness,
                "x": -width / 2 + tw * (c + 0.5),
                "y": -depth / 2 + td * (r + 0.5),
            })
    return tiles
