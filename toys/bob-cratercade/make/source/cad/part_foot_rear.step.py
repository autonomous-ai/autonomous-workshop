"""rear foot, deck-bearing face on the print bed."""
from assemblies.deck import foot_for_print
from assemblies.deck_interfaces import inputs
PRINTABLE = True

def gen_step():
    return foot_for_print(2,**inputs())
