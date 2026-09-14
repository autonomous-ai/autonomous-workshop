"""Four-root 80 mm splice used only at the constrained left Y320 seam."""
from parts.seam_strap import build_strap
PRINTABLE = True


def gen_step():
    return build_strap(short=True)
