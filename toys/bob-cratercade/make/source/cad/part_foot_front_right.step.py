"""Front-right foot with clearance for the launcher root fastener."""
from assemblies.deck import foot_for_print
from assemblies.deck_interfaces import inputs
PRINTABLE = True

def gen_step():
    return foot_for_print(1,**inputs())
