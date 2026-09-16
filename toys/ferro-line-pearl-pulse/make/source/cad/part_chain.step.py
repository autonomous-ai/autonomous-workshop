"""One genuine print-in-place strand: root plus eight independently free beads."""
from parts.chains import print_module

PRINTABLE = True

def gen_step():
    return print_module()
