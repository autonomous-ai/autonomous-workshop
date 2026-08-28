"""Printable pinion key entry."""

from parts.pinion_key import build_pinion_key
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_pinion_key()
