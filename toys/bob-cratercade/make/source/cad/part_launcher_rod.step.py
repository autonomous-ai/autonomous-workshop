"""Individual launcher rod in its specified bed pose."""
from parts.launcher_rod import print_shape
PRINTABLE=True

def gen_step():
    return print_shape()
