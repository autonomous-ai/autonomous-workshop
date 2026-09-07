"""Combined view, not a print plate; each part entry prints separately."""
from crosscurrent_lib import assemble
PRINTABLE = False
def gen_step():
    return assemble()
