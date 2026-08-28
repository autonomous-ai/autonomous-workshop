"""Printable captive axle, upright on its broad head."""

from moon_relay_lib import print_pose_axle

PRINTABLE = True


def gen_step():
    return print_pose_axle()
