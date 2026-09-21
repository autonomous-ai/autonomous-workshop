"""Single printable bubble_4, flat bottom on Z zero."""
from veinwake_lib import make_bubble
PRINTABLE = True
def gen_step():
    return make_bubble("bubble_4")
