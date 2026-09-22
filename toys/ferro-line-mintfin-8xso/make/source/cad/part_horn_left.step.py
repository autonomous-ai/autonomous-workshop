"""Print horn_left broad seat down; bed Z=0. Geometry gates pending."""
from parts.decor import horn_print
PRINTABLE = True

def gen_step():
    return horn_print('pair',-1)
