import params as p
"""crosshead: one manufactured solid in support-free print pose."""
from parts.crosshead import crosshead
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True
def gen_step():
    validate_parameters()
    return on_bed(crosshead(), p.PRINT_ROTATIONS["crosshead"])
