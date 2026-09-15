"""Individual flipper right rotor in its specified bed pose."""
from parts.flipper import print_rotor
PRINTABLE=True

def gen_step():
    return print_rotor('right')
