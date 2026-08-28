"""Printable follower axle entry."""

from parts.follower_axle import build_follower_axle
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_follower_axle()
