"""Algebraic package and mating checks, before any solid construction."""
import params as p

def validate_parameters():
    assert p.AXLE_BORE > p.AXLE_DIAMETER
    assert abs(p.WHEEL_GAP - p.WHEEL_WIDTH - 2*p.WHEEL_SIDE_AIR) < 1e-9
    assert p.ARCH_INNER - p.WHEEL_RADIUS >= 3
    assert p.ARCH_OUTER - p.ARCH_INNER >= 2*p.NOZZLE
    assert p.SUPPORT_THICKNESS >= 2*p.NOZZLE
    assert p.FRAME_STEER_HOUSING[5] - p.STEER_SLOT[5] >= 2 - 1e-9
    assert p.COCKPIT_STAND_GAP > 2*p.BATTERY_BOUNDS[3]
    assert p.COCKPIT_BAR_BOTTOM == p.COCKPIT_RISER_PROFILE[2][1]
    assert p.FRAME_TANK_BOTTOM == p.BODY_TANK_SECTIONS[0][0]
    assert len(p.AXLE_X) == 2 and p.AXLE_X[0] < p.AXLE_X[1]
validate_parameters()
