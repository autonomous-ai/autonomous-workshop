"""Printable crema piston. Thumb disc on the bed, stem up."""

from crema_click_lib import build_crema_piston

PRINTABLE = True


def gen_step():
    return build_crema_piston()
