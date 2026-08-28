"""Printable grip entry."""

from parts.grip import build_grip
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_grip()
