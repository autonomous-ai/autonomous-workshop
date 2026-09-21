"""Anti-Sol of Jupiter -- rank 8, one printed part in several filaments.

Bed datum Z = 0 is the disc's bed face.  The globe leans its north pole toward
-X at the planet's true obliquity, which is the ownership cue; the disc's wall
tapers inward as it rises, which confirms it.
"""

from parts.world import build_world

PRINTABLE = True


def gen_step():
    return build_world("jupiter", "anti")
