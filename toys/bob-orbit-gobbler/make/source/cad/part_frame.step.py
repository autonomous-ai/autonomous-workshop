"""Printable frame entry."""

from parts.frame import build_frame
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_frame()
