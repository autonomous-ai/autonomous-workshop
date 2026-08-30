"""Printable combined entry for the monolithic Moonchase Fox."""

from moonchase_fox_lib import build_fox

PRINTABLE = True


def gen_step():
    return build_fox()

