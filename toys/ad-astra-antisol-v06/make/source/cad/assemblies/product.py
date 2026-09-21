"""Antisol, set up and ready to play.

Assembly is positioning: every shape below is built in its own part module, in
its own print orientation, and placed here.  Each entry is one occurrence --
one production solid, in one filament -- named `<part>_<colour>` so that
whoever loads the printer reads the spool off the filename.
"""

from __future__ import annotations

from build123d import Location, Rot

from cadgen.assembly import AssemblyHelper

import bool3d as X
import params as P
import positions as POS
from colors import filament
from parts.belt import build_belt_cell
from parts.board import build_panel_at_origin, panel_extent
from parts.corona import build_corona_cell
from parts.den import den_bodies
from parts.tray import build_orbit_tray
from parts.world import world_bodies

FILE_NAMES = "abcdefg"
FIELD_TOP = P.BOARD_THICKNESS
POCKET_FLOOR = P.BOARD_THICKNESS - P.POCKET_DEPTH

# Where the two storage trays sit beside the set, clear of the near star.  The
# gap is generous on purpose: at the fixed product viewpoint a tray parked
# close to the far edge crosses the board's rim in projection and cuts through
# a corona tongue, which reads as a part floating over the board.
TRAY_Y = P.BOARD_D / 2.0 + 62.0 + P.TRAY_D / 2.0
TRAY_X = P.TRAY_W / 2.0 + 10.0


def cell_name(file_index: int, rank_index: int) -> str:
    return "%s%d" % (FILE_NAMES[file_index], rank_index + 1)


def _away_from_den(cell, den) -> float:
    """Degrees to turn a corona tile so its tongues point away from the star."""
    dx = cell[0] - den[0]
    dy = cell[1] - den[1]
    if dx < 0:
        return 90.0
    if dx > 0:
        return -90.0
    return 0.0 if dy > 0 else 180.0


def tray_socket_centres() -> list[tuple[float, float]]:
    """The eight socket centres of one tray, in its own local frame."""
    return [
        ((col - (P.TRAY_COLS - 1) / 2.0) * P.TRAY_PITCH,
         (row - (P.TRAY_ROWS - 1) / 2.0) * P.TRAY_PITCH)
        for row in range(P.TRAY_ROWS)
        for col in range(P.TRAY_COLS)
    ]


def _piece_seat(cell_key: tuple[int, int]) -> float:
    """How high a world's bed face sits on the cell it is standing on."""
    if cell_key in P.DEN_CELLS.values():
        return POCKET_FLOOR + P.DEN_SPIGOT_DEPTH + P.DEN_PROUD
    for group in P.TRAP_CELLS.values():
        if cell_key in group:
            return POCKET_FLOOR + P.CORONA_TILE_H
    return FIELD_TOP


def occurrences(position: str = "opening", with_trays: bool = True) -> list[dict]:
    """Every occurrence of the set: name, filament, local solid, placement.

    `with_trays` drops the two storage trays and leaves captured worlds off the
    set entirely.  The state sheet uses that view: with the trays in frame a
    captured world only moves from one side of the picture to the other, and
    three positions of one game come out too alike for the sheet's own
    difference check to tell them apart.
    """
    layout = POS.POSITIONS[position]
    items: list[dict] = []

    def place(stem, colour, shape, location):
        """One occurrence per single solid, named for the spool that prints it.

        A colour region that is several disjoint bodies -- Mercury's albedo
        patches, a digit's separate strokes, Mars's two polar caps -- becomes
        one numbered occurrence each.  Handed over as a compound instead, the
        assembly package names the children itself as `part_o1.32.1`, which is
        neither a part name nor a colour anybody can load.
        """
        solids = X.parts(shape)
        if not solids:
            raise ValueError("%s has no solid to place" % stem)
        if len(solids) == 1:
            items.append({"name": "%s_%s" % (stem, colour), "colour": colour,
                          "shape": solids[0], "location": location})
            return
        for index, solid in enumerate(solids, 1):
            items.append({"name": "%s%d_%s" % (stem, index, colour), "colour": colour,
                          "shape": solid, "location": location})

    # --- the board ------------------------------------------------------
    for panel in ("southwest", "southeast", "northwest", "northeast"):
        x0, x1, y0, y1 = panel_extent(panel)
        place(
            "panel_%s" % panel,
            P.BOARD_COLOUR,
            build_panel_at_origin(panel),
            Location(((x0 + x1) / 2.0, (y0 + y1) / 2.0, 0.0)),
        )

    # --- the asteroid belt ----------------------------------------------
    belt = build_belt_cell()
    for cell in P.BELT_CELLS:
        x, y = P.cell_centre(*cell)
        place(
            "belt_%s" % cell_name(*cell),
            P.BELT_COLOUR,
            belt,
            Location((x, y, POCKET_FLOOR)),
        )

    # --- the stars and their coronas ------------------------------------
    star = den_bodies()
    corona = build_corona_cell()
    for side in P.SIDES:
        den = P.DEN_CELLS[side]
        x, y = P.cell_centre(*den)
        turn = 0.0 if side == "sol" else 180.0
        for role, colour in (
            ("star", P.DEN_PLUG_COLOUR[side]),
            ("flare", P.FLAME_COLOUR[side]),
        ):
            place(
                "den_%s_%s" % (side, role),
                colour,
                star[role],
                Location((x, y, POCKET_FLOOR)) * Rot(0, 0, turn),
            )
        for cell in P.TRAP_CELLS[side]:
            cx, cy = P.cell_centre(*cell)
            colour = P.FLAME_COLOUR[side]
            place(
                "corona_%s" % cell_name(*cell),
                colour,
                corona,
                Location((cx, cy, POCKET_FLOOR)) * Rot(0, 0, _away_from_den(cell, den)),
            )

    # --- storage ---------------------------------------------------------
    tray_origin = {}
    if with_trays:
        tray = build_orbit_tray()
        for side, sign in (("sol", -1.0), ("anti", 1.0)):
            tray_origin[side] = (sign * TRAY_X, TRAY_Y)
            place(
                "tray_%s" % side,
                P.TRAY_COLOUR,
                tray,
                Location((sign * TRAY_X, TRAY_Y, 0.0)),
            )

    # --- the sixteen worlds ---------------------------------------------
    sockets = tray_socket_centres()
    for side in P.SIDES:
        taken = list(layout.get("taken_%s" % side, []))
        standing = {name: where for name, where in layout[side].items() if where}
        for planet in P.PLANETS:
            bodies = world_bodies(planet, side)
            if planet in standing:
                spot = POS.cell(standing[planet])
                x, y = P.cell_centre(*spot)
                at = Location((x, y, _piece_seat(spot)))
            elif planet in taken and with_trays:
                index = taken.index(planet)
                ox, oy = tray_origin[side]
                sx, sy = sockets[index]
                at = Location((ox + sx, oy + sy, P.TRAY_H - P.TRAY_SOCKET_DEPTH))
            else:
                continue
            for role, (colour, shape) in bodies.items():
                place("%s_%s_%s" % (planet, side, role), colour, shape, at)
    return items


def product_compound(position: str = "opening", with_trays: bool = True):
    """The whole set in one exact position, as one labelled assembly."""
    asm = AssemblyHelper("antisol")
    for item in occurrences(position, with_trays):
        asm.add(
            item["location"] * item["shape"],
            item["name"],
            color=filament(item["colour"]),
        )
    return asm.compound()


def triptych(names=("opening", "midgame", "endgame"), gap: float = 60.0):
    """The same set in three exact positions, side by side in one frame.

    Rendered as three separate pictures the boards are each framed to their own
    extent, so the same terrain lands at a different size and place in every
    panel and the set reads as though the tiles had moved between them. Placed
    in one frame they share one camera, and the only thing that changes across
    the three is which worlds are still standing.
    """
    asm = AssemblyHelper("antisol_states")
    step = P.BOARD_W + gap
    for index, name in enumerate(names):
        offset = (index - (len(names) - 1) / 2.0) * step
        for item in occurrences(name, with_trays=False):
            asm.add(
                Location((offset, 0, 0)) * item["location"] * item["shape"],
                "%s_%s" % (name, item["name"]),
                color=filament(item["colour"]),
            )
    return asm.compound()
