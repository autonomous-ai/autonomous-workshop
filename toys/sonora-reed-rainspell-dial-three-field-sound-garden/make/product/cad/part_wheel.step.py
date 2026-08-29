from parts.wheel import build_wheel
import validation  # noqa: F401

PRINTABLE = True


def gen_step():
    # The cage-bottom datum is on the bed; skirt and guide walls grow upward.
    return build_wheel()
