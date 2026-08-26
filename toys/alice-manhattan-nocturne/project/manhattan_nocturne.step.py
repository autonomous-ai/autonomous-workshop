"""Manhattan Nocturne in the exact standard starting position.

The board plus 32 individually labeled piece occurrences make 33 assembly
children.  Geometry stays in part-local print coordinates in the shared
library; this entry owns placement only.
"""

from build123d import Location
from cadgen.assembly import AssemblyHelper

import manhattan_nocturne_lib as lib
import params as p


def _piece_occurrence(asm, cache, side, role, file_index, rank_index):
    file_name = chr(ord("a") + file_index)
    rank_name = str(rank_index + 1)
    x, y = p.square_center(file_index, rank_index)
    z = p.square_top_z(file_index, rank_index)
    cache_key = (side, role)
    if cache_key not in cache:
        cache[cache_key] = lib.build_piece(side, role)
    placed = Location((x, y, z)) * cache[cache_key]
    asm.add(
        placed,
        f"{side}_{role}_{file_name}{rank_name}",
        color=lib.part_color(side),
    )


def gen_step():
    p.validate_parameters()
    asm = AssemblyHelper("manhattan_nocturne")
    asm.add(lib.build_board(), "board", color=lib.board_color())
    cache = {}

    # Stone: ranks 1 and 2, viewed from the south edge.
    for file_index, role in enumerate(p.BACK_RANK):
        _piece_occurrence(asm, cache, "stone", role, file_index, 0)
        _piece_occurrence(asm, cache, "stone", "pawn", file_index, 1)

    # Steel: ranks 8 and 7, mirrored by chess rank but not by piece geometry.
    for file_index, role in enumerate(p.BACK_RANK):
        _piece_occurrence(asm, cache, "steel", role, file_index, 7)
        _piece_occurrence(asm, cache, "steel", "pawn", file_index, 6)

    assert len(asm.children) == 33, "board + 32 chess pieces must be labeled"
    return asm.compound(label="manhattan_nocturne")
