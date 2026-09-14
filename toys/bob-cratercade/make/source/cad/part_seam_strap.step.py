"""Identical flat-bed deck seam strap, locating pins upward."""
from parts.seam_strap import build_strap
PRINTABLE = True

def gen_step():
    return build_strap()
