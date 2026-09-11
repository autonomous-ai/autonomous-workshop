"""Single printable rind, flat bottom on Z zero."""
from veinwake_lib import make_rind
PRINTABLE = True
def gen_step():
    return make_rind("rind")
