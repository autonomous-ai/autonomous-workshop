"""Complete35-part starting inventory, with two loose spare queens beside board."""
from tidal_states import build_state
PRINTABLE = False
def gen_step():
    return build_state('initial')
