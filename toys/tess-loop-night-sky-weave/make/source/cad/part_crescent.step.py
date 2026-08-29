"""One Crescent-family tile in flat print orientation."""

from night_sky_weave_lib import build_tile

PRINTABLE = True


def gen_step():
    return build_tile("crescent")
