"""Cheap algebraic validation; geometry gates own solids and meshes."""

import math
import params as p


def validate_parameters() -> None:
    assert math.isclose(p.GEAR_CENTER_DISTANCE, 37.5, abs_tol=1e-9)
    assert p.CARRIER_TEETH / p.PINION_TEETH == 2.0
    assert 36.0 + 280.0 + 36.0 + 8.0 == 360.0
    assert math.isclose(p.OUTER_MOUTH_R - p.INNER_ORBIT_R, 12.0, abs_tol=1e-9)
    peak_dr = math.pi * (p.OUTER_MOUTH_R - p.INNER_ORBIT_R) / (2.0 * math.radians(36.0))
    pressure = math.degrees(math.atan(peak_dr / ((p.OUTER_MOUTH_R + p.INNER_ORBIT_R) / 2.0)))
    assert pressure < 27.0
    assert math.isclose(p.FRAME_MORTISE_T - p.FRAME_TENON_T, 2.0 * p.RUN_CLEAR, abs_tol=1e-9)
    assert math.isclose(p.CARRIER_BORE - p.CENTRAL_AXLE_D, 0.35, abs_tol=1e-9)
    assert math.isclose(p.PINION_FRAME_BORE - p.PINION_SLEEVE_D, 2.0 * p.RUN_CLEAR, abs_tol=1e-9)
    assert math.isclose(p.GRIP_BORE - p.GRIP_POST_D, 2.0 * p.RUN_CLEAR, abs_tol=1e-9)
    assert p.FRAME_R + 1.0 <= p.BASE_W / 2.0
    assert p.OUTER_MOUTH_R + p.MOON_R == 82.0
    assert p.LIP_STANDOFF_R - (p.OUTER_MOUTH_R + p.MOON_R) >= 8.0
    assert p.WALL >= 3.0 * p.NOZZLE
    assert p.GEAR_DECK_Z0 - p.SPOKE_DECK_T >= 1.0
    assert p.FOLLOWER_PATH_R0 - p.FOLLOWER_OVERTRAVEL - p.CARRIER_ACTIVE_R0 > 20.0
    assert p.CARRIER_ACTIVE_R1 - (p.FOLLOWER_PATH_R1 + p.FOLLOWER_OVERTRAVEL + p.FOLLOWER_SLOT_W / 2.0) >= p.FOLLOWER_END_MATERIAL
    slider_outer_at_max = p.FOLLOWER_PATH_R1 - p.FOLLOWER_LOCAL_X + p.SLIDER_LENGTH / 2.0
    assert p.CHANNEL_R1 - slider_outer_at_max >= p.RUN_CLEAR
    assert p.CHANNEL_END_MATERIAL >= 4.0
    assert p.RETAINER_SOLID >= 1.5 and p.CENTRAL_GROOVE_CORE_D >= 6.0
    assert p.CLIP_GROOVE_W - p.CLIP_T >= 2.0 * p.RUN_CLEAR - 1e-9
    assert math.isclose(p.CENTRAL_GROOVE_CORE_D, p.GRIP_GROOVE_CORE_D)
    assert math.isclose(p.SMALL_WASHER_BORE, 8.4, abs_tol=1e-9)


validate_parameters()
