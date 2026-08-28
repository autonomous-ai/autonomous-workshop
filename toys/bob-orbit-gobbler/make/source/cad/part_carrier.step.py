"""Printable carrier entry."""

from parts.carrier import build_carrier
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_carrier()
