"""Printable moon entry."""

from parts.moon import build_moon
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_moon()
