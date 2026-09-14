"""Return floor section3, flat print pose."""
from assemblies.return_system import print_channel
PRINTABLE=True

def gen_step():
    return print_channel(3,True)
