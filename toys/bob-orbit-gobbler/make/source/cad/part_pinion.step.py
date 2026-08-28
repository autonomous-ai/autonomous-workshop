"""Printable pinion entry."""

from parts.pinion import build_pinion
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_pinion()
