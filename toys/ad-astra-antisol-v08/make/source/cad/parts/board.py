"""The field, cut into four panels.

The board is flat and the grid is cut into it: cells are drawn by engraved
lines, not by wells.  A piece stands on the board; it does not sink into it.
Depth is reserved for terrain -- trap, den, belt -- where a change of level is
the rule being shown.

Every terrain pocket on this board is the same 34.80 x 34.80 x 6.00 hole; only
what drops into it differs.  The grid groove is omitted on a pocket's own
boundaries, because the pocket rim is that cell's line, and because two
adjacent belt pockets are already parted by a 1.20 mm rib that a groove would
cut away.
"""

from __future__ import annotations

from build123d import Plane, Pos, Rectangle, extrude

import params as P
from features import rounded_square_sketch

# Panel name -> (file range, rank range) as half-open index ranges.
PANELS = {
    "southwest": (range(0, P.PANEL_FILE_CUT), range(0, P.PANEL_RANK_CUT)),
    "southeast": (range(P.PANEL_FILE_CUT, P.FILES), range(0, P.PANEL_RANK_CUT)),
    "northwest": (range(0, P.PANEL_FILE_CUT), range(P.PANEL_RANK_CUT, P.RANKS)),
    "northeast": (range(P.PANEL_FILE_CUT, P.FILES), range(P.PANEL_RANK_CUT, P.RANKS)),
}


def terrain_cells() -> dict[tuple[int, int], str]:
    """Every cell that is a pocket rather than flat land."""
    cells: dict[tuple[int, int], str] = {}
    for side, cell in P.DEN_CELLS.items():
        cells[cell] = "den"
    for side, group in P.TRAP_CELLS.items():
        for cell in group:
            cells[cell] = "trap"
    for cell in P.BELT_CELLS:
        cells[cell] = "belt"
    return cells


def _is_land(file_index: int, rank_index: int, terrain) -> bool:
    if not (0 <= file_index < P.FILES and 0 <= rank_index < P.RANKS):
        return False
    return (file_index, rank_index) not in terrain


def panel_extent(name: str) -> tuple[float, float, float, float]:
    """(x0, x1, y0, y1) of one panel in board coordinates."""
    files, ranks = PANELS[name]
    x0 = -P.BOARD_W / 2.0 if files.start == 0 else -P.FIELD_W / 2.0 + P.CELL_PITCH * files.start
    x1 = P.BOARD_W / 2.0 if files.stop == P.FILES else -P.FIELD_W / 2.0 + P.CELL_PITCH * files.stop
    y0 = -P.BOARD_D / 2.0 if ranks.start == 0 else -P.FIELD_D / 2.0 + P.CELL_PITCH * ranks.start
    y1 = P.BOARD_D / 2.0 if ranks.stop == P.RANKS else -P.FIELD_D / 2.0 + P.CELL_PITCH * ranks.stop
    return x0, x1, y0, y1


def _groove_sketch(terrain):
    """Every grid line, as one fused 2D sketch in board coordinates."""
    half = P.GROOVE_W / 2.0
    pieces = []
    for k in range(P.FILES + 1):
        x = -P.FIELD_W / 2.0 + P.CELL_PITCH * k
        for r in range(P.RANKS):
            left = _is_land(k - 1, r, terrain)
            right = _is_land(k, r, terrain)
            if k == 0:
                keep = right
            elif k == P.FILES:
                keep = left
            else:
                keep = left and right
            if not keep:
                continue
            _, y = P.cell_centre(0, r)
            pieces.append(Pos(x, y) * Rectangle(P.GROOVE_W, P.CELL_PITCH))
    for m in range(P.RANKS + 1):
        y = -P.FIELD_D / 2.0 + P.CELL_PITCH * m
        for f in range(P.FILES):
            below = _is_land(f, m - 1, terrain)
            above = _is_land(f, m, terrain)
            if m == 0:
                keep = above
            elif m == P.RANKS:
                keep = below
            else:
                keep = below and above
            if not keep:
                continue
            x, _ = P.cell_centre(f, 0)
            pieces.append(Pos(x, y) * Rectangle(P.CELL_PITCH, P.GROOVE_W))
    return pieces[0] + pieces[1:]


SEAM_X = -P.FIELD_W / 2.0 + P.CELL_PITCH * P.PANEL_FILE_CUT
SEAM_Y = -P.FIELD_D / 2.0 + P.CELL_PITCH * P.PANEL_RANK_CUT


def _inset(edge: float, seam: float) -> float:
    """How far a pocket edge is pulled in from its own cell boundary."""
    on_seam = abs(edge - seam) < 1e-6
    return P.POCKET_SEAM_INSET if on_seam else P.POCKET_INSET


def pocket_rect(f: int, r: int) -> tuple[float, float, float, float]:
    """(centre x, centre y, width, depth) of one terrain pocket."""
    x, y = P.cell_centre(f, r)
    half = P.CELL_PITCH / 2.0
    left = _inset(x - half, SEAM_X)
    right = _inset(x + half, SEAM_X)
    down = _inset(y - half, SEAM_Y)
    up = _inset(y + half, SEAM_Y)
    return (
        x + (left - right) / 2.0,
        y + (down - up) / 2.0,
        P.CELL_PITCH - left - right,
        P.CELL_PITCH - down - up,
    )


def _pocket_sketch(terrain):
    """Every terrain pocket, as one fused 2D sketch in board coordinates.

    A pocket edge that lands on a panel seam is pulled in further than one
    that does not: the two panels together still part their pockets by a rib,
    but each panel now owns a wall thick enough to print on its own.
    """
    pieces = []
    for (f, r) in sorted(terrain):
        cx, cy, width, depth = pocket_rect(f, r)
        pieces.append(
            Pos(cx, cy) * rounded_square_sketch(width, P.POCKET_CORNER_R, depth)
        )
    return pieces[0] + pieces[1:]


def build_panel(name: str):
    """One printed panel, bed datum Z = 0, play surface at Z = BOARD_THICKNESS."""
    x0, x1, y0, y1 = panel_extent(name)
    slab = Pos((x0 + x1) / 2.0, (y0 + y1) / 2.0, 0) * extrude(
        Rectangle(x1 - x0, y1 - y0), P.BOARD_THICKNESS
    )

    terrain = terrain_cells()
    grooves = Pos(0, 0, P.BOARD_THICKNESS - P.GROOVE_D) * extrude(
        _groove_sketch(terrain), P.GROOVE_D + 1.0
    )
    pockets = Pos(0, 0, P.BOARD_THICKNESS - P.POCKET_DEPTH) * extrude(
        _pocket_sketch(terrain), P.POCKET_DEPTH + 1.0
    )

    panel = slab - [grooves, pockets]
    panel.label = "panel_%s" % name
    return panel


def build_panel_at_origin(name: str):
    """The same panel moved so its own bed footprint is centred on the origin."""
    x0, x1, y0, y1 = panel_extent(name)
    return Pos(-(x0 + x1) / 2.0, -(y0 + y1) / 2.0, 0) * build_panel(name)
