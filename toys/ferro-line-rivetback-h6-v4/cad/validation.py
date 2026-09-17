"""Import-time algebraic checks, distinct from geometry gates."""

from params import *

# Permit the binary floating-point representation of exact decimal equalities.
assert 1.2 + 1e-9 >= 3 * nozzle
assert 2.0 + 1e-9 >= 5 * nozzle
assert 0.15 <= (small_socket - small_peg) / 2 <= 0.30
assert 0.20 <= (hip_socket - hip_peg) / 2 <= 0.35
assert 0.20 <= (tenon_socket_width - tenon_width) / 2 <= 0.35
assert 0.15 <= (pin_hole - pin_diameter) / 2 <= 0.30
assert foot_width >= 10.0 and foot_length >= 12.0
assert len(leg_roots) == 6
