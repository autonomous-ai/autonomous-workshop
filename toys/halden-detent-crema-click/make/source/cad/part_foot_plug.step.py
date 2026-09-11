"""Printable foot plug. Outer desk face on the bed."""

from crema_click_lib import build_foot_plug

PRINTABLE = True


def gen_step():
    return build_foot_plug()
