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
check(
    "board envelope",
    p.BOARD_SIZE == 244.0 and p.BOARD_TOTAL_HEIGHT == 9.0,
    "244 x 244 x 9.00 mm on declared 256 mm bed",
)
check("board is one piece", (PROJECT / "part_board.step.py").is_file(), "one seamless entry")
check(
    "four-layer relief",
    p.SQUARE_RELIEF == 0.80 and p.BOARD_THICKNESS == 8.20
    and p.SQUARE_RELIEF / p.EXPLORATION_LAYER_HEIGHT == 4.0,
    "32 light pads rise 0.80 mm over the continuous Z8.20 dark base",
)
light_pad_count = sum(
    p.is_light_square(file_index, rank_index)
    for file_index in range(p.FILES)
    for rank_index in range(p.RANKS)
)
check(
    "isolated light pads",
    light_pad_count == 32
    and p.LIGHT_PAD_LOWER_SIZE < p.SQUARE_PITCH
    and p.LIGHT_PAD_EMBED >= p.BOOLEAN_OVERLAP,
    f"{light_pad_count} pads; {p.LIGHT_PAD_LOWER_SIZE:.2f} mm lower footprint; "
    f"{p.LIGHT_PAD_EMBED:.2f} mm base overlap",
)
light_landing_margin = (p.LIGHT_PAD_TOP_SIZE - p.MAX_BASE_DIAMETER) / 2.0
check(
    "light-square landing",
    light_landing_margin >= p.MIN_WALL,
    f"{p.LIGHT_PAD_TOP_SIZE:.2f} mm top leaves {light_landing_margin:.2f} mm around D{p.MAX_BASE_DIAMETER:.1f}",
)
check(
    "pad shading slope",
    (p.LIGHT_PAD_LOWER_SIZE - p.LIGHT_PAD_TOP_SIZE) / 2.0 + 1e-9 >= p.MIN_WALL,
    f"{(p.LIGHT_PAD_LOWER_SIZE - p.LIGHT_PAD_TOP_SIZE) / 2.0:.2f} mm native sloped-face run",
)
check(
    "border street plan",
    len(p.INTERNAL_GRID_COORDINATES) == 7
    and p.BORDER_STREET_GROOVE_TOP_WIDTH == 2.00
    and p.BORDER_STREET_GROOVE_BOTTOM_WIDTH == 1.20
    and p.BORDER_STREET_GROOVE_DEPTH == 0.80,
    "seven sloped file/rank dashes per edge; 2.00→1.20 mm x 0.80 mm",
)
broadway_inner_margin = -p.PLAY_SPAN / 2.0 - p.AVENUE_GROOVE_MAX_Y
broadway_outer_margin = p.AVENUE_GROOVE_MIN_Y + p.BOARD_SIZE / 2.0
check(
    "Broadway border margin",
    min(broadway_inner_margin, broadway_outer_margin) >= 1.20,
    f"{min(broadway_inner_margin, broadway_outer_margin):.2f} mm minimum to either edge",
)
check(
    "Broadway street clearance",
    min(abs(p.AVENUE_GROOVE_CENTER_X - coordinate) for coordinate in p.INTERNAL_GRID_COORDINATES)
    - p.AVENUE_HALF_EXTENT_X
    >= 10.0,
    f"true {p.AVENUE_ANGLE_DEG:.0f}° diagonal centred between file streets",
)
check(
    "base clearance",
    p.MAX_BASE_DIAMETER + 2.0 * p.BASE_CLEARANCE_PER_SIDE == p.SQUARE_PITCH,
    f"D{p.MAX_BASE_DIAMETER:.1f} + 2 x {p.BASE_CLEARANCE_PER_SIDE:.1f} = {p.SQUARE_PITCH:.1f}",
)
dark_landing_margin = (p.SQUARE_PITCH - p.MAX_BASE_DIAMETER) / 2.0
check(
    "dark landing margin",
    dark_landing_margin >= 3.00,
    f"{dark_landing_margin:.2f} mm per side around D{p.MAX_BASE_DIAMETER:.1f} base",
)
check("Stone tactile code", len(p.STONE_GROOVE_Z) == 1 and len(p.STONE_BAND_Z) >= 2,
      "one groove + horizontal bands")
check("Steel tactile code", len(p.STEEL_GROOVE_Z) == 2 and p.STEEL_FIN_HEIGHT > 0,
      "two grooves + vertical fins")
check(
    "Steel groove wall floor",
    p.STEEL_BASE_GROOVE_HEIGHT >= 0.80
    and p.STEEL_BASE_RAIL_HEIGHT >= 1.20
    and len(p.STEEL_BASE_RAIL_Z) == 3,
    "two 0.80 mm channels between three 1.20 mm raised rails",
)

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
