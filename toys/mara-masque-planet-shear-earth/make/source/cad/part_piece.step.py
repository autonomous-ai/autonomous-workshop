"""The Planet Shear rank-4 piece as the one body that gets printed.

Disc face on the bed at Z=0.  The colour groups in the assembly entry union
back to exactly this solid; this entry is what the print gates measure.
"""
import planet_shear_lib as lib

PRINTABLE = True


def gen_step():
    solid = lib.build_piece()
    solid.label = "planet_shear_rank_four"
    return solid
