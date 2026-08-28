"""Printable pinion washer entry."""

from parts.pinion_washer import build_pinion_washer
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_pinion_washer()
