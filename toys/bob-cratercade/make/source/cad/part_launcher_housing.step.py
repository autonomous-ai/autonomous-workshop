"""Individual launcher housing in its specified bed pose."""
from parts.launcher_housing import print_shape
PRINTABLE=True

def gen_step():
    return print_shape()
