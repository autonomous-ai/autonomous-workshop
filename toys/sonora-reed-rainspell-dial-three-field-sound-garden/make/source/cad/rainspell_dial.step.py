"""View-only combined Rainspell Dial assembly."""

from assemblies.product import build_product
import validation  # noqa: F401

PRINTABLE = False


def gen_step():
    return build_product()
