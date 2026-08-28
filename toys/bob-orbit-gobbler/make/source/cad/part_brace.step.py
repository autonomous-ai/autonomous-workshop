"""Printable brace entry."""

from parts.brace import build_brace
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_brace()
