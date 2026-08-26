#!/usr/bin/env python3
"""Local algebraic interface audit; generic geometry gates build the solids."""
from fixture_lib import CHANNEL_Y, SIDE_CLEARANCE, SLIDER_Y


assert CHANNEL_Y - SLIDER_Y == 2.0 * SIDE_CLEARANCE
assert SIDE_CLEARANCE >= 1.0
print("FIT PASS slider channel clearance")
