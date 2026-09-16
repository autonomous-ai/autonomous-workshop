"""Single-solid delivery leaves; PIP strands must still be printed together.

These addressable leaves do not replace part_chain.step.py's registered
nine-body manufacturing layout. Never reposition PIP members independently
for printing. The main assembly uses the same live leaf builders.
"""
from parts.chains import root, bead
from parts.moving import ribbon
from params import MIST


def delivery_leaf(family):
    if family == 'chain_root':
        return root()
    if family == 'chain_bead':
        return bead()
    if family == 'chain_terminal':
        return bead(terminal=True)
    if family == 'ribbon_mist':
        shape = ribbon()
        shape.color = MIST
        return shape
    raise ValueError(f'Unknown delivery family: {family}')
