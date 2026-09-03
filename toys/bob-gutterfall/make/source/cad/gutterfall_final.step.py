"""Canonical printable entry for the one-piece Gutterfall gargoyle."""
from gutterfall_v7_lib import build_gargoyle

PRINTABLE = True


def gen_step():
    return build_gargoyle()
