#!/usr/bin/env python3
"""Fast independent arithmetic audit; geometry gates remain separate."""

import json
import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from params import *  # noqa: E402,F403
from validation import validate_parameters  # noqa: E402

validate_parameters()

neutral_gap = (PORTAL_W - PADDLE_W) / 2.0
stop_shift = PADDLE_RADIUS * math.sin(math.radians(SWING_LIMIT_DEG))
closed_gap = neutral_gap - stop_shift
open_gap = neutral_gap + stop_shift
assert math.isclose(neutral_gap, 35.0)
assert 10.0 < closed_gap < COMET_D / 2.0
assert open_gap > COMET_D
assert 2 * TRAY_W - LAP_W == 410.0
assert 2 * MAGAZINE_X + MAG_W == 486.0
assert 2 * (KEY_Y + KEY_W / 2) == 190.0
assert GATE_H + FLOOR_T == 68.0
assert len(TRAY_B_COMET_X) * len(TRAY_B_COMET_Y) == 12
assert max(14.0 + MANUAL_PROXY[2], 2 * (COMET_T + RELIEF_H + 0.3), MAG_H) <= 40.0

print(json.dumps({
    "ok": True,
    "instance_count": 24,
    "deployed_envelope_mm": [486.0, 190.0, 68.0],
    "packed_envelope_mm": list(PACKED_ENVELOPE),
    "neutral_side_gap_mm": neutral_gap,
    "nominal_stop_shift_mm": round(stop_shift, 3),
    "nominal_closed_gap_mm": round(closed_gap, 3),
    "nominal_open_gap_mm": round(open_gap, 3),
    "physical_claims_proven": False
}, sort_keys=True))
