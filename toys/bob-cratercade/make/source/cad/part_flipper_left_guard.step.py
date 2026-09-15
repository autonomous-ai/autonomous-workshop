"""Individual flipper left guard in its specified bed pose."""
from parts.flipper_guard import print_guard
PRINTABLE=True

def gen_step():
    return print_guard('left')
