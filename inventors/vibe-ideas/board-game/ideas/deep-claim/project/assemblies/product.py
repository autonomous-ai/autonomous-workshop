"""Places every physical part as a separately named cq.Assembly child.

Demo/hero state: three broad pucks seated and sealing shelves, two slim
pucks resting on open floors, one bore left empty -- matching idea.json's
own hero_shot prose ("three bores plugged ... two bores showing a slim
puck ... one bore untouched and empty"). Every other loose puck (19 of the
24) is laid out in four owner clusters beyond the board's rim so the full
component count stays visible and separately named.
"""

from __future__ import annotations

import cadquery as cq

from blocks import add_piece_family
from cadlib.layout import circle_points
from params import Params
from parts import assay_board, disc_large, disc_small

# Bore index -> (piece_type, mark) seated there for the demo render. Index 0
# is deliberately left out of this map (idea.json's hero_shot: "one bore
# untouched and empty").
_DEMO_SEATS: dict[int, tuple[str, int]] = {
    1: ("large", 3),
    2: ("large", 4),
    3: ("large", 5),
    4: ("small", 6),
    5: ("small", 3),
}


def make_assembly(p: Params) -> cq.Assembly:
    asm = cq.Assembly(name="deep_claim")

    board_shape = assay_board.build(p)
    asm.add(board_shape, name="assay_board", color=cq.Color(0.55, 0.52, 0.48))

    top_z = p.board_thickness / 2.0
    large_seat_z = top_z - p.shelf_depth
    small_seat_z = top_z - p.shelf_depth - p.throat_depth - p.floor_depth
    # SAME position list used to cut the board's bores (assay_board.build)
    # and to seat the demo pucks below -- never restated.
    positions = assay_board.bore_positions(p)

    # One shape per (type, mark) -- built once, placed up to 3 times each.
    large_shapes = {m: disc_large.build(p, m) for m in p.owner_marks}
    small_shapes = {m: disc_small.build(p, m) for m in p.owner_marks}

    seated_count = {(kind, m): 0 for m in p.owner_marks for kind in ("large", "small")}
    for kind, mark in _DEMO_SEATS.values():
        seated_count[(kind, mark)] += 1

    family_positions: dict[tuple[str, int], list[tuple[float, float, float]]] = {
        key: [] for key in seated_count
    }
    for idx, (x, y) in enumerate(positions):
        if idx in _DEMO_SEATS:
            kind, mark = _DEMO_SEATS[idx]
            z = large_seat_z if kind == "large" else small_seat_z
            family_positions[(kind, mark)].append((x, y, z))

    # ---- supply clusters: one per owner mark, laid out beyond the board's
    # rim so every remaining loose puck is visible and separately named ----
    supply_radius = p.board_diameter / 2.0 + 55.0
    anchors = circle_points(n=len(p.owner_marks), radius=supply_radius, start_deg=45.0)
    row_offset = 11.0
    col_pitch = 34.0

    for (ax, ay), mark in zip(anchors, p.owner_marks):
        for kind, row_y in (("large", row_offset), ("small", -row_offset)):
            remaining = p.pieces_per_mark - seated_count[(kind, mark)]
            x0 = -(remaining - 1) * col_pitch / 2.0
            for i in range(remaining):
                family_positions[(kind, mark)].append(
                    (ax + x0 + i * col_pitch, ay + row_y, 0.0)
                )

    for mark in p.owner_marks:
        add_piece_family(
            asm, large_shapes[mark], family_positions[("large", mark)],
            name=f"disc_large_mark{mark}",
        )
        add_piece_family(
            asm, small_shapes[mark], family_positions[("small", mark)],
            name=f"disc_small_mark{mark}",
        )

    return asm
