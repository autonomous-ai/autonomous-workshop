"""Printable sector rotor, broad face on Z=0."""

from moonwake_garden_lib import build_sector_rotor

PRINTABLE = True


def gen_step():
    return build_sector_rotor()
