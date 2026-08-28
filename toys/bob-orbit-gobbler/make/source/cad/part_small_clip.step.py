"""Printable shared snap clip entry; print two."""

from parts.small_clip import build_small_clip
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_small_clip()
