"""The star -- the one component allowed to break the legibility floor.

Printed spigot-down: the flange's underside is drafted off the spigot at 48
degrees from horizontal, and each flame stands wholly on the flange top, so
nothing about this part is cantilevered and no face needs support.
"""

from parts.den import build_den_plug

PRINTABLE = True


def gen_step():
    return build_den_plug()
