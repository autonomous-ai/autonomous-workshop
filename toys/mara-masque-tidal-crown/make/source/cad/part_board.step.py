"""Single spiral platter, flat bed datum."""
from tidal_lib import board
PRINTABLE = True
def gen_step():
    return board()
# Revision2: explicit positive-Z outline winding.
# Revision3: visible alternating face colors and broad corner land.
# Revision4: sloped tactile recess walls visible from top.
