"""Project-specific dimension, fit, and kinematic audit."""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[1]
sys.path.insert(0, str(PROJECT))

import moon_relay_lib as m

cadfits = m.cadfits


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return math.isclose(a, b, abs_tol=tol)


def main() -> None:
    assert close(m.BORE_ACROSS_FLATS, cadfits.slot_for(m.AXLE_D, "free"))
    assert close(m.KEYWAY_W, cadfits.slot_for(m.KEY_TAB_W, "free"))
    assert close(m.KEYWAY_H, cadfits.slot_for(m.KEY_TAB_T, "free"))
    assert close((m.CHEEK_INNER_GAP - m.ROCKER_DEPTH) / 2.0, 0.5)
    assert close(m.GUARD_GAP, 2.0)
    assert m.GUARD_WALL >= 2.0

    angle = math.radians(m.ROCKER_MAX_ANGLE_DEG)
    one_side_rise = m.MOON_CENTER_X * math.sin(angle)
    rise_difference = 2.0 * one_side_rise
    outer_reach = (m.MOON_CENTER_X + m.MOON_RADIUS) * math.sin(angle)
    lower_face = (m.ROCKER_T / 2.0) * math.cos(angle)
    floor_clearance = m.PIVOT_Z - outer_reach - lower_face - m.BASE_T
    assert rise_difference >= 8.0
    assert floor_clearance >= 0.75

    locked_engagement = (m.KEY_TAB_W - m.DIAMOND_DIAGONAL) / 2.0
    unlocked_per_side_clearance = (m.KEYWAY_W - m.KEY_TAB_W) / 2.0
    assert locked_engagement >= 1.5
    assert close(unlocked_per_side_clearance, cadfits.mating_clearance("free"))

    for label, shape in (
        ("lunar_base", m.print_pose_base()),
        ("moon_rocker", m.print_pose_rocker()),
        ("quarter_turn_axle", m.print_pose_axle()),
    ):
        bounds = shape.bounding_box()
        assert len(shape.solids()) == 1, label
        assert close(bounds.min.Z, 0.0), (label, bounds.min.Z)
        assert shape.volume > 0.0, label

    assembly_bounds = m.make_assembly().bounding_box()
    assert close(assembly_bounds.size.X, m.BASE_W)
    assert close(assembly_bounds.size.Y, m.BASE_D)
    assert assembly_bounds.size.Z <= m.BASE_H
    print(
        "PASS lunar-relay spec: "
        f"rise_difference={rise_difference:.3f} mm, "
        f"floor_clearance={floor_clearance:.3f} mm, "
        f"locked_engagement={locked_engagement:.3f} mm"
    )


if __name__ == "__main__":
    main()
