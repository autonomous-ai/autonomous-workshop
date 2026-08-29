"""Combined play configuration; view-only, not one physical print."""

from saigon_chess_lib import make_play_assembly

PRINTABLE = False


def gen_step():
    return make_play_assembly()

