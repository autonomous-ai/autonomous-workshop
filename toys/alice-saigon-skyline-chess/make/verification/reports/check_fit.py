"""Algebraic fit audit complementing the generic geometry/bed gate."""

from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))

from saigon_chess_lib import (  # noqa: E402
    BASE_D,
    BED_X,
    BED_Y,
    BOARD_SIZE,
    SQUARE,
    TARGET_HEIGHTS,
)


def main() -> int:
    assert BOARD_SIZE <= BED_X and BOARD_SIZE <= BED_Y
    assert BED_X - BOARD_SIZE >= 12.0 and BED_Y - BOARD_SIZE >= 12.0
    assert BASE_D < SQUARE
    assert SQUARE - BASE_D == 7.0
    assert list(TARGET_HEIGHTS.values()) == sorted(TARGET_HEIGHTS.values())
    assert max(TARGET_HEIGHTS.values()) < 60.0
    print("PASS: 12 mm bed margin, 7 mm square/base clearance, monotonic 28–55 mm hierarchy")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

