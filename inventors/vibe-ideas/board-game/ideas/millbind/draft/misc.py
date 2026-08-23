"""grain_pellet, sack_spindle, granary_bin -- the score economy."""
import cadquery as cq

import params as p


def build_grain_pellet() -> cq.Workplane:
    body = cq.Workplane("XY").circle(p.PELLET_D / 2.0).extrude(p.PELLET_H)
    body = body.faces(">Z").chamfer(1.4)
    hole = (
        cq.Workplane("XY").circle(p.PELLET_HOLE_D / 2.0)
        .extrude(p.PELLET_H + 2.0).translate((0, 0, -1.0))
    )
    return body.cut(hole)


def build_sack_spindle() -> cq.Workplane:
    base = cq.Workplane("XY").circle(p.SPINDLE_BASE_D / 2.0).extrude(p.SPINDLE_BASE_H)
    base = base.faces(">Z").chamfer(1.0)
    rod = (
        cq.Workplane("XY").circle(p.SPINDLE_ROD_D / 2.0)
        .extrude(p.SPINDLE_ROD_H).translate((0, 0, p.SPINDLE_BASE_H))
    )
    return base.union(rod)


def build_granary_bin() -> cq.Workplane:
    outer = cq.Workplane("XY").box(
        p.BIN_L, p.BIN_W, p.BIN_H, centered=(True, True, False)
    )
    inner = cq.Workplane("XY").box(
        p.BIN_L - 2 * p.BIN_WALL, p.BIN_W - 2 * p.BIN_WALL,
        p.BIN_H - p.BIN_WALL + 1.0, centered=(True, True, False),
    ).translate((0, 0, p.BIN_WALL))
    bin_body = outer.cut(inner)

    # Thumb scallop cut into the top rim of one LONG wall (the 70mm-long
    # wall running along X, at y = +BIN_W/2).
    scallop = (
        cq.Workplane("XZ")
        .circle(p.BIN_SCALLOP_R)
        .extrude(p.BIN_WALL + 2.0, both=True)
        .translate((0, 0, p.BIN_H))
    )
    scallop = scallop.translate((0, p.BIN_W / 2.0, 0))
    bin_body = bin_body.cut(scallop)
    return bin_body
