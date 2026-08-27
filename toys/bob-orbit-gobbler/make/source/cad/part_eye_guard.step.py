"""Printable eye guard entry."""

from parts.eye_guard import build_eye_guard
from validation import validate_parameters

PRINTABLE = True


def gen_step():
    validate_parameters()
    return build_eye_guard()
