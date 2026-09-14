"""Deck tile 0,0; actual canonical assembly cuts, playing face on bed."""
from assemblies.deck import tile_for_print
from assemblies.deck_interfaces import inputs
PRINTABLE = True

def gen_step():
    return tile_for_print(0,0,**inputs())
