"""View-only combined Orbit Gobbler assembly."""

from assemblies.product import build_product
from validation import validate_parameters

PRINTABLE = False


def gen_step():
    validate_parameters()
    return build_product()
