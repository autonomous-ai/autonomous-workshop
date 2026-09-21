"""Complete ten-part inventory in a legal full-board draw."""
from veinwake_lib import make_assembly
PRINTABLE = False
def gen_step():
    return make_assembly('draw')
