"""One flat-base printed launch divider upper."""
import params as p
from parts import launch_divider
PRINTABLE=True

def gen_step():
    return launch_divider.print_shape(1)
