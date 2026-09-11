"""Combined assembly — view only. Print from part_* entries."""

from crema_click_lib import assembled

PRINTABLE = False


def gen_step():
    return assembled(0.0)
