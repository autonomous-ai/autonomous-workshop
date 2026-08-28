"""Printable base entry."""

from parts.base import build_base
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_base()
