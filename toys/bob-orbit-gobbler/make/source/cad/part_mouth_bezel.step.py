"""Printable mouth bezel entry."""

from parts.mouth_bezel import build_mouth_bezel
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_mouth_bezel()
