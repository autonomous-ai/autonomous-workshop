"""The trap tile, alone and in its ring, for the frames that show it flat.

The owner's second pass takes the two raised tongues off every corona tile, so
the evidence this correction needs is the evidence a flat tile can give: the
tile from straight above, where the engraving is the whole picture; the tile
from a low angle, where a raised feature would show against the sky and none
does; the same two with a world standing in the well, because "what does a trap
read as with a piece on it" is the question the removal risks; and one star with
its three traps in one frame, so the star's flames and the flat traps can be
seen together.

Nothing here is a print target and nothing is turned or modified.  This places
the exact solids `parts/corona.py` and `parts/den.py` build at the exact heights
`assemblies/product.py` gives them.

    "$WORKSHOP_PYTHON" corona_views.py <scratch> <cad-skill-scripts-dir> <out-dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import Location, Rot, export_step

from cadgen.assembly import AssemblyHelper

import params as P
from assemblies.product import POCKET_FLOOR, cell_name
from colors import filament
from parts.corona import build_corona_cell
from parts.den import den_bodies
from parts.world import world_bodies
from world_views import FRAME_SIZE, _renderer, _tessellate

#: Straight down the tile, and a low raking angle.  The low one is the frame a
#: raised feature could not hide from: at 8 degrees of elevation anything
#: standing above the tile's top face breaks its silhouette against the
#: background.
TOP_VIEW = (-90.0, 90.0)
LOW_VIEW = (-55.0, 8.0)

#: The frame the whole set is photographed at, for the den-and-traps picture.
DEN_VIEW = (-55.0, 22.0)

#: Which world stands in the well.  A trapped world is the other army's, so an
#: Anti-Sol piece stands in a Sol trap; Earth because it is the world a reader
#: recognises fastest and is mid-ladder, so the well is neither swamped nor
#: rattling.
SEATED = ("earth", "anti")

#: Which star's ring is photographed.  Sol: the orange trap tiles and the
#: sunflower_yellow plinth are the set's own focal point.
DEN_SIDE = "sol"

CORONA_SEAT = POCKET_FLOOR + P.CORONA_TILE_H


def _add(asm, shape, name: str, colour: str, at=None):
    asm.add(shape if at is None else at * shape, name, color=filament(colour))


def tile_assembly(seated: bool):
    """One trap tile at its own place in the pocket, with or without a world."""
    asm = AssemblyHelper("corona_seated" if seated else "corona_alone")
    colour = P.FLAME_COLOUR[DEN_SIDE]
    _add(asm, build_corona_cell(), "corona_%s" % colour, colour,
         Location((0, 0, POCKET_FLOOR)))
    if seated:
        planet, side = SEATED
        at = Location((0, 0, CORONA_SEAT))
        for role, (body_colour, shape) in world_bodies(planet, side).items():
            _add(asm, shape, "%s_%s_%s_%s" % (planet, side, role, body_colour),
                 body_colour, at)
    return asm.compound()


def den_assembly():
    """One star and its three traps, at their real board positions."""
    asm = AssemblyHelper("den_and_traps")
    den = P.DEN_CELLS[DEN_SIDE]
    dx, dy = P.cell_centre(*den)
    star = den_bodies()
    turn = 0.0 if DEN_SIDE == "sol" else 180.0
    for role, colour in (("star", P.DEN_PLUG_COLOUR[DEN_SIDE]),
                         ("flare", P.FLAME_COLOUR[DEN_SIDE])):
        _add(asm, star[role], "den_%s_%s_%s" % (DEN_SIDE, role, colour), colour,
             Location((dx, dy, POCKET_FLOOR)) * Rot(0, 0, turn))
    tile = build_corona_cell()
    colour = P.FLAME_COLOUR[DEN_SIDE]
    for cell in P.TRAP_CELLS[DEN_SIDE]:
        cx, cy = P.cell_centre(*cell)
        _add(asm, tile, "corona_%s_%s" % (cell_name(*cell), colour), colour,
             Location((cx, cy, POCKET_FLOOR)))
    return asm.compound()


#: (file stem, builder, view).  Four tile frames and one den frame.
SHOTS = (
    ("corona-cell-top", lambda: tile_assembly(False), TOP_VIEW),
    ("corona-cell-low", lambda: tile_assembly(False), LOW_VIEW),
    ("corona-cell-seated-top", lambda: tile_assembly(True), TOP_VIEW),
    ("corona-cell-seated-low", lambda: tile_assembly(True), LOW_VIEW),
    ("den-and-traps", den_assembly, DEN_VIEW),
)


def write_and_render(scratch: Path, scripts: Path, target: Path) -> list[Path]:
    render_review = _renderer(scripts)
    scratch.mkdir(parents=True, exist_ok=True)
    target.mkdir(parents=True, exist_ok=True)
    written = []
    built = {}
    for stem, builder, view in SHOTS:
        source = scratch / ("%s.step" % stem)
        if stem not in built:
            export_step(builder(), str(source))
            built[stem] = source
        _src, shape = render_review.build_shape(source)
        out = target / ("%s.png" % stem)
        render_review.render(
            _tessellate(render_review, shape), view[0], view[1],
            FRAME_SIZE, 0.06).save(out)
        written.append(out)
    return written


if __name__ == "__main__":
    for item in write_and_render(Path(sys.argv[1]), Path(sys.argv[2]),
                                 Path(sys.argv[3])):
        print(item)
