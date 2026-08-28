"""Printable garden mask, broad rear face on Z=0 and relief upward."""

from moonwake_garden_lib import build_front_garden_mask

PRINTABLE = True


def gen_step():
    return build_front_garden_mask()
