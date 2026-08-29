"""Fast algebraic validation run before any B-rep construction."""

from __future__ import annotations

import math

import params as p


def validate_parameters() -> None:
    assert 3 * (p.FIELD_SPAN_DEG + p.PARTITION_GAP_DEG) == 360.0
    assert len(p.RAIN_ANGLES) == len(p.RAIN_HEIGHTS) == len(p.RAIN_ARCS) == 17
    assert len(p.FROG_ANGLES) == len(p.FROG_HEIGHTS) == len(p.FROG_ARCS) == 9
    assert len(p.CRICKET_ANGLES) == len(p.CRICKET_HEIGHTS) == len(p.CRICKET_ARCS) == 20
    assert len(p.RAIN_ANGLES) + len(p.FROG_ANGLES) + len(p.CRICKET_ANGLES) == 46
    assert math.isclose(p.DECK_BOTTOM_Z + p.DECK_THICKNESS, p.DECK_TOP_Z)
    assert math.isclose(p.CAGE_BOTTOM_Z - (p.DECK_TOP_Z + max(p.FROG_HEIGHTS)), 0.65)
    assert math.isclose(p.CAP_SHOULDER_Z - p.WHEEL_HUB_TOP_Z, p.WHEEL_ENDPLAY)
    assert math.isclose(p.PLECTRUM_ASSEMBLY_Z + p.PLECTRUM_HEAD_TOP + p.FOLLOWER_TRAVEL, 51.65)
    assert p.PLECTRUM_STEM_RADIUS < p.GUIDE_BORE_RADIUS < p.PLECTRUM_FLANGE_RADIUS
    assert math.isclose((p.GUIDE_BORE_RADIUS - p.PLECTRUM_STEM_RADIUS) * 2.0, 0.5)
    assert math.isclose((p.WHEEL_BORE_RADIUS - p.JOURNAL_RADIUS) * 2.0, 0.5)
    assert math.isclose(p.GUARD_INNER_RADIUS - p.WHEEL_SKIRT_OUTER_RADIUS, 0.8)
    assert math.isclose(p.GUARD_INNER_RADIUS - (p.FOLLOWER_CENTER_RADIUS + p.CAGE_RADIUS), 1.8)
    assert p.PRODUCT_RADIUS * 2 == 120.0
    assert p.PRODUCT_HEIGHT == 52.0


validate_parameters()
