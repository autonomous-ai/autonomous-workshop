"""Sol of Venus -- rank 3, one printed part in several filaments.

Bed datum Z = 0 is the disc's bed face.  The globe leans its north pole toward
+X at the planet's true obliquity, which is the ownership cue; the disc's wall
flares outward as it rises, which confirms it.
"""

from parts.world import build_world

PRINTABLE = True


def gen_step():
    return build_world("venus", "sol")
