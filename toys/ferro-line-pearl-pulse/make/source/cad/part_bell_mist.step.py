"""One registered material region of the crown-down co-printed bell."""
from parts.bell import bell
PRINTABLE = True

def gen_step():
    return bell('mist', print_orientation=True)
