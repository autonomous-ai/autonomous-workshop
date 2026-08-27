"""Printable crank arm entry."""

from parts.crank_arm import build_crank_arm
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_crank_arm()
