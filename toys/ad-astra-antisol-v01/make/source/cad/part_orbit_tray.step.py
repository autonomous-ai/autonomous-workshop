"""One storage tray -- eight identical sockets, one per world.

Every socket is identical because every disc is identical.
"""

from parts.tray import build_orbit_tray

PRINTABLE = True


def gen_step():
    return build_orbit_tray()
