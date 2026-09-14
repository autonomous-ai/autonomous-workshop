"""97 independent monolithic items, standard setup and64 offboard replacements."""
from states import build_scene
PRINTABLE = False

def gen_step():
    return build_scene('inventory')
