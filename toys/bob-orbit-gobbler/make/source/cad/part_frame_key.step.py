"""Printable frame key entry."""

from parts.frame_key import build_frame_key
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_frame_key()
