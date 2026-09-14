"""Individual flipper sleeve in its specified bed pose."""
from parts.flipper_sleeve import print_sleeve
PRINTABLE=True

def gen_step():
    return print_sleeve()
