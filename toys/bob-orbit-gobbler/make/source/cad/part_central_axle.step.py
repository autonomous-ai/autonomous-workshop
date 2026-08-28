"""Printable central axle entry."""

from parts.central_axle import build_central_axle
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_central_axle()
