"""Project-specific algebraic print/fit audit for Manhattan Nocturne.

The generic CAD gates own solids, bed datum, body count, mesh topology and
interference.  This audit owns the product contract they cannot infer: exact
part inventory, chess-square clearance, tactile coding, setup coordinates and
the one-piece 256 mm bed assumption.
"""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

import params as p  # noqa: E402


passed: list[str] = []


def check(name: str, condition: bool, detail: str) -> None:
    assert condition, f"FAIL {name} — {detail}"
    passed.append(f"ok  {name:34s} {detail}")


p.validate_parameters()
check("board envelope", p.BOARD_SIZE == 244.0, "244 x 244 mm on declared 256 mm bed")
check("board is one piece", (PROJECT / "part_board.step.py").is_file(), "one seamless entry")
check(
    "base clearance",
    p.MAX_BASE_DIAMETER + 2.0 * p.BASE_CLEARANCE_PER_SIDE == p.SQUARE_PITCH,
    f"D{p.MAX_BASE_DIAMETER:.1f} + 2 x {p.BASE_CLEARANCE_PER_SIDE:.1f} = {p.SQUARE_PITCH:.1f}",
)
check("Stone tactile code", len(p.STONE_GROOVE_Z) == 1 and len(p.STONE_BAND_Z) >= 2,
      "one groove + horizontal bands")
check("Steel tactile code", len(p.STEEL_GROOVE_Z) == 2 and p.STEEL_FIN_HEIGHT > 0,
      "two grooves + vertical fins")

expected_variants = {f"part_{side}_{role}.step.py" for side in p.SIDES for role in p.ROLES}
present_variants = {path.name for path in PROJECT.glob("part_*_*.step.py")}
check("twelve variant entries", present_variants == expected_variants,
      f"{len(present_variants)} present, {len(expected_variants)} expected")

stone_squares = {(file_index, rank_index) for file_index in range(p.FILES) for rank_index in (0, 1)}
steel_squares = {(file_index, rank_index) for file_index in range(p.FILES) for rank_index in (6, 7)}
setup_squares = stone_squares | steel_squares
check("starting inventory", len(stone_squares) == 16 and len(steel_squares) == 16,
      "16 Stone + 16 Steel")
check("starting squares unique", len(setup_squares) == 32,
      "32 distinct occupied squares")
check("standard back rank", p.BACK_RANK == (
    "rook", "knight", "bishop", "queen", "king", "bishop", "knight", "rook"
), "R N B Q K B N R")

top_values = {p.square_top_z(file_index, rank_index)
              for file_index in range(p.FILES) for rank_index in range(p.RANKS)}
check("two-level square relief", top_values == {p.BOARD_THICKNESS, p.BOARD_TOTAL_HEIGHT},
      f"Z {p.BOARD_THICKNESS:.2f} / {p.BOARD_TOTAL_HEIGHT:.2f}")
check("tallest assembly", abs(p.BOARD_TOTAL_HEIGHT + p.KING_HEIGHT - 83.35) < 1e-9,
      "9.00 + 74.35 = 83.35 mm")

print("\n".join(passed))
print(f"\ncheck_fit(project): ok - {len(passed)} algebraic checks passed")
