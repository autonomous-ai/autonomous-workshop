"""Print horn_middle broad seat down; bed Z=0. Geometry gates pending."""
from parts.decor import horn_print
PRINTABLE = True

def gen_step():
    return horn_print('middle')
