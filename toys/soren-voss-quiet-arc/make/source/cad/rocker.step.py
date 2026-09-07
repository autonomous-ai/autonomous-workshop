from build123d import Compound
from rocker_lib import rocker_rest
PRINTABLE = False

def gen_step():
    return Compound(label='Quiet Arc', children=[rocker_rest()])
