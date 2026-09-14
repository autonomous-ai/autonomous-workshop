"""Individual flipper pedestal in its specified bed pose."""
from parts.flipper_pedestal import pedestal
PRINTABLE=True

def gen_step():
    return pedestal()
