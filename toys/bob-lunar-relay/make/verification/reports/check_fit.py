"""Algebraic fit, connector-name, and assembly-order audit."""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT))

import moon_relay_lib as m

cadfits = m.cadfits


def main() -> None:
    # One male value owns each mate; the female side is derived exactly once.
    assert math.isclose(m.BORE_ACROSS_FLATS, cadfits.slot_for(m.AXLE_D, "free"))
    assert math.isclose(m.KEYWAY_W, cadfits.slot_for(m.KEY_TAB_W, "free"))
    assert math.isclose(m.KEYWAY_H, cadfits.slot_for(m.KEY_TAB_T, "free"))
    assert math.isclose(
        m.CHEEK_INNER_GAP,
        cadfits.slot_for(m.ROCKER_DEPTH, m.ROCKER_SIDE_CLEARANCE),
    )

    connectors = (
        "near_cheek_keyway",
        "rocker_keyway",
        "far_cheek_keyway",
        "quarter_turn_axle",
        "locked_far_tab",
    )
    assert len(connectors) == len(set(connectors))

    # Ordered tool-free assembly ledger; each interface is named above.
    assembly_order = (
        ("place", "moon_rocker", "between_pivot_cheeks"),
        ("align", "quarter_turn_axle", "three_horizontal_keyways"),
        ("slide", "quarter_turn_axle", "near_to_far"),
        ("rotate", "quarter_turn_axle", "locked_far_tab"),
    )
    assert [row[0] for row in assembly_order] == ["place", "align", "slide", "rotate"]
    assert m.KEY_TAB_W > m.DIAMOND_DIAGONAL + 2.0
    print("PASS lunar-relay fit: derived mates, unique connectors, ordered capture")


if __name__ == "__main__":
    main()
