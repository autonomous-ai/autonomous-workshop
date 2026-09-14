"""Hopper right, qualified print pose."""
from parts.hopper import print_shape
PRINTABLE=True

def gen_step():
    return print_shape('right')
