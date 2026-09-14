"""One flat-base printed return guide right."""
import params as p
from parts import return_guide
PRINTABLE=True

def gen_step():
    return return_guide.print_shape("right")
