"""Printable Lunar Relay base, bed datum Z=0."""

from moon_relay_lib import print_pose_base

PRINTABLE = True


def gen_step():
    return print_pose_base()
