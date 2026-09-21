"""Single printable tooth_3, flat bottom on Z zero."""
from veinwake_lib import make_tooth
PRINTABLE = True
def gen_step():
    return make_tooth("tooth_3")
