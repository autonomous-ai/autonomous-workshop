"""Printable lunar slider entry."""

from parts.lunar_slider import build_lunar_slider
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_lunar_slider()
