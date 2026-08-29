from parts.rib_deck import build_rib_deck
import validation  # noqa: F401

PRINTABLE = True


def gen_step():
    return build_rib_deck()
