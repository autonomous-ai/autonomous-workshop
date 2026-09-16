"""Combined entry: the rank-4 piece split into its finished colour groups.

Every occurrence is one region of the single printed body and one solid, named
for the shop and for the concept's component ledger.  The union of the
occurrences is exactly `part_piece.step.py`; nothing here is a separately
printed part.
"""
from cadgen.assembly import AssemblyHelper

import planet_shear_lib as lib

RELIEF_COLOURS = {
    "land_": lib.LAND_GREEN,
    "dryland_": lib.DRYLAND_TAN,
    "polar_": lib.ICE_WHITE,
}


def _colour_for(name):
    for prefix, colour in RELIEF_COLOURS.items():
        if name.startswith(prefix):
            return colour
    raise KeyError("no sealed colour for occurrence %s" % name)


def _add(asm, shape, name, colour):
    solids = shape.solids()
    if len(solids) != 1:
        raise ValueError("%s holds %d solids; an occurrence is one body" % (name, len(solids)))
    solid = solids[0]
    solid.label = name
    asm.add(solid, name, color=colour)


def gen_step():
    lib.check_parameters()
    asm = AssemblyHelper("planet_shear_rank_four")
    _add(asm, lib.build_base(), "disc_base", lib.DISC_BLUE)
    _add(asm, lib.build_seat(), "ocean_seat", lib.OCEAN_BLUE)
    _add(asm, lib.build_ocean(), "ocean_globe", lib.OCEAN_BLUE)
    for name, solid in lib.build_relief().items():
        _add(asm, solid, name, _colour_for(name))
    return asm.compound()
