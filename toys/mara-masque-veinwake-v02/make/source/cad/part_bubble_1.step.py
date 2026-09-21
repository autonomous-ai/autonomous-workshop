"""Single printable bubble_1, flat bottom on Z zero."""
from veinwake_lib import make_bubble
PRINTABLE = True
def gen_step():
    return make_bubble("bubble_1")
