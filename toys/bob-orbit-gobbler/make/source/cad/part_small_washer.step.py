"""Printable shared thrust washer entry; print two."""

from parts.small_washer import build_small_washer
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_small_washer()
