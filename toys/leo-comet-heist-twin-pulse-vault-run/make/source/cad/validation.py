"""Fail-fast sealed-concept and manufacturing assertions."""

import math
from params import *


def validate_parameters() -> None:
    assert math.isclose(2 * TRAY_W - LAP_W, ASSEMBLED_TRAY_W)
    assert FIELD_W == 390.0 and FIELD_D == 170.0
    assert TRAY_W <= PRINT_BED[0] and TRAY_D <= PRINT_BED[1]
    assert FLOOR_T >= 3 * NOZZLE and WALL_T >= 3 * NOZZLE
    assert PORTAL_W == 84.0 and math.isclose(2 * LEG_W + PORTAL_W, GATE_SPAN)
    assert PIVOT_Z - (PADDLE_RADIUS + PADDLE_H / 2.0) == 3.0
    assert TRUNNION_D + 2 * 0.30 == SEAT_D
    assert 0.30 <= AXIAL_CLEARANCE_EACH <= 0.40
    assert BRIDGE_SLIDE == 6.0
    assert FOOT_VERTICAL_CLEARANCE == 0.25
    assert RETAINING_SHOULDER_T == 2.5
    assert COMET_D == 30.0 and COMET_T == 5.5
    assert MAG_WELL_D - COMET_D == 2.0
    assert sum(VAULT_MOUTHS) + 2 * VAULT_DIVIDER_T == 127.6
    assert VAULT_SCORES == (4, 2, 6)
    assert -GATE_X - (-195.0) == 145.0
    assert GATE_X + 195.0 == 245.0
    assert PACKED_ENVELOPE == (210.0, 190.0, 52.0)
