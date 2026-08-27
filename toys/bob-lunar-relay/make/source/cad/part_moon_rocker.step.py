"""Printable monolithic moon rocker, broad face on the bed."""

from moon_relay_lib import print_pose_rocker

PRINTABLE = True


def gen_step():
    return print_pose_rocker()
