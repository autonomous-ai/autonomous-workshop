"""Individual flipper left guard base in its specified bed pose."""
from parts.flipper_guard_base import guard_base
PRINTABLE=True

def gen_step():
    return guard_base('left')
