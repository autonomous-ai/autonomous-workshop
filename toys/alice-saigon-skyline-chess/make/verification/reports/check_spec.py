"""Project-specific deterministic audit for dimensions, inventory, and side language."""

from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from saigon_chess_lib import (  # noqa: E402
    BASE_D,
    BOARD_SIZE,
    BUILDERS,
    GRID_SIZE,
    KINDS,
    SIDES,
    SQUARE,
    TARGET_HEIGHTS,
    make_board,
    make_piece,
    make_play_assembly,
)


def main() -> int:
    assert BOARD_SIZE == 208.0
    assert GRID_SIZE == 8 * SQUARE == 200.0
    board = make_board()
    bb = board.bounding_box()
    assert len(board.solids()) == 1
    assert abs(bb.size.X - 208.0) < 1e-6 and abs(bb.size.Y - 208.0) < 1e-6
    assert 3.2 <= bb.size.Z <= 4.2
    assert set(BUILDERS) == set(KINDS)
    for side in SIDES:
        for kind in KINDS:
            part = make_piece(kind, side)
            bounds = part.bounding_box()
            assert len(part.solids()) == 1
            assert bounds.size.X <= BASE_D + 1e-6
            assert bounds.size.Y <= BASE_D + 1e-6
            assert abs(bounds.max.Z - TARGET_HEIGHTS[kind]) <= 0.6
    assembly = make_play_assembly()
    assert len(assembly.children) == 33
    assert len(assembly.solids()) == 33
    river_knights = [child for child in assembly.children if child.label.startswith("river:knight")]
    grid_knights = [child for child in assembly.children if child.label.startswith("grid:knight")]
    assert len(river_knights) == len(grid_knights) == 2
    # The directional upper-body mass follows each supported canopy inward.
    assert all(child.center().Y > -87.5 for child in river_knights)
    assert all(child.center().Y < 87.5 for child in grid_knights)
    print("PASS: 208 mm board, 25 mm squares, 12 unique piece variants, 32-piece opening inventory, inward-facing knights")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
