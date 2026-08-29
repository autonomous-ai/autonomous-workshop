"""Printable cloud receiver, blind pockets facing upward."""

from storm_reveal_lib import cloud_print_pose

PRINTABLE = True
SOURCE_REVISION = "r4-deterministic-monochrome-step"


def gen_step():
    return cloud_print_pose()
