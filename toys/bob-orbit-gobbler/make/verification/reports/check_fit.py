#!/usr/bin/env python3
"""Project-specific fit and connector ledger audit; geometry gates own solids."""

import math
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
import params as p


def main() -> int:
    checks = {
        "frame-tenon running clearance": math.isclose(p.FRAME_MORTISE_W - p.FRAME_TENON_W, 2.0 * p.RUN_CLEAR),
        "central axle running clearance": math.isclose(p.CARRIER_BORE - p.CENTRAL_AXLE_D, 0.35),
        "pinion sleeve frame clearance": math.isclose(p.PINION_FRAME_BORE - p.PINION_SLEEVE_D, 2.0 * p.RUN_CLEAR),
        "grip post running clearance": math.isclose(p.GRIP_BORE - p.GRIP_POST_D, 2.0 * p.RUN_CLEAR),
        "slider base clearance": math.isclose(p.CHANNEL_BASE_W - p.SLIDER_BASE_W, 0.60),
        "slider throat clearance": math.isclose(p.CHANNEL_THROAT_W - p.SLIDER_THROAT_W, 0.60),
        "slider outer overtravel clearance": p.CHANNEL_R1 - (p.FOLLOWER_PATH_R1 - p.FOLLOWER_LOCAL_X + p.SLIDER_LENGTH / 2.0) >= p.RUN_CLEAR,
        "channel solid outer cap": p.CHANNEL_END_MATERIAL >= 4.0,
        "carrier deck axial separation": p.GEAR_DECK_Z0 - p.SPOKE_DECK_T >= 2.0,
        "bezel to moon axial clearance": p.MOON_FRONT_Y - (p.LIP_FRONT_Y + p.LIP_T) >= 1.5,
        "follower outer end material": p.CARRIER_ACTIVE_R1 - (p.FOLLOWER_PATH_R1 + p.FOLLOWER_OVERTRAVEL + p.FOLLOWER_SLOT_W / 2.0) >= p.FOLLOWER_END_MATERIAL,
        "retainer solid end": p.RETAINER_SOLID >= 1.5,
        "retainer groove core": p.CENTRAL_GROOVE_CORE_D >= 6.0,
        "snap clip axial clearance": p.CLIP_GROOVE_W - p.CLIP_T >= 2.0 * p.RUN_CLEAR - 1e-9,
        "bezel post slip fit": math.isclose(p.FRAME_PILOT_D - p.BEZEL_POST_D, 2.0 * p.RUN_CLEAR),
    }
    failed = [name for name, ok in checks.items() if not ok]
    for name, ok in checks.items():
        print(f"{'ok' if ok else 'FAIL'} fit: {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
