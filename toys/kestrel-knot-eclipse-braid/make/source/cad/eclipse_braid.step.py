"""Build entry for the complete print-in-place Eclipse Braid assembly."""

from eclipse_braid_lib import make_assembly


PRINTABLE = True


def gen_step():
    return make_assembly()

