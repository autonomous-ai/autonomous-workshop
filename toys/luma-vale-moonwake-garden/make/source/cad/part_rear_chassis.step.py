"""Printable rear chassis, broad rear face on Z=0."""

from moonwake_garden_lib import build_rear_chassis

PRINTABLE = True


def gen_step():
    return build_rear_chassis()
