"""Mintfin head_front; one physical print, flat bed datum Z=0."""
from parts.head import head_front
PRINTABLE = True
def gen_step():
    shape=head_front()
    # Export the manufactured solid directly, without a singleton Compound.
    solid=shape.solids()[0]
    solid.label=shape.label
    solid.color=shape.color
    return solid
