"""Printable follower roller entry."""

from parts.follower_roller import build_follower_roller
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_follower_roller()
