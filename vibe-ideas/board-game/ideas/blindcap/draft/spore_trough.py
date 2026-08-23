"""spore_trough -- boat-shaped personal tray, 230x90x40mm. Six cradles hold
stools lying on their side (shanks toward the owner); a 34mm-tall back wall
blocks the opposite seat's sightline; three upright slots hold claim_crowns
on edge; an owner notch count is cut into the back wall; craquelure matches
loam_tile's. Prints open-top, no supports.
"""
import cadquery as cq

import params as p

HALF_L = p.TROUGH_L / 2.0
HALF_W = p.TROUGH_W / 2.0
BACK_Y = -HALF_W
CRADLE_Y0 = BACK_Y + p.TROUGH_WALL_T + 3.0          # cradles start just off the back wall
CRADLE_Y_MID = CRADLE_Y0 + p.TROUGH_CRADLE_LEN / 2.0


def build_spore_trough():
    body = cq.Workplane("XY").box(
        p.TROUGH_L, p.TROUGH_W, p.TROUGH_FLOOR_T, centered=(True, True, False)
    )

    # back wall (tall, blocks the opposite seat's sightline)
    back_wall = cq.Workplane("XY").box(
        p.TROUGH_L, p.TROUGH_WALL_T, p.TROUGH_BACK_WALL_H, centered=(True, False, False)
    ).translate((0, BACK_Y, p.TROUGH_FLOOR_T))
    body = body.union(back_wall)

    # front + side walls, lower
    front_wall = cq.Workplane("XY").box(
        p.TROUGH_L, p.TROUGH_WALL_T, p.TROUGH_SIDE_WALL_H, centered=(True, False, False)
    ).translate((0, HALF_W - p.TROUGH_WALL_T, p.TROUGH_FLOOR_T))
    body = body.union(front_wall)
    for sx in (-1, 1):
        side_wall = cq.Workplane("XY").box(
            p.TROUGH_WALL_T, p.TROUGH_W, p.TROUGH_SIDE_WALL_H, centered=(False, False, False)
        ).translate((sx * HALF_L - (p.TROUGH_WALL_T if sx > 0 else 0), -HALF_W, p.TROUGH_FLOOR_T))
        body = body.union(side_wall)

    # six cradles: shallow scalloped grooves (a wide, shallow arc, not a full
    # half-round -- that would need a floor deeper than the cap is wide).
    # A single large-radius cylinder, axis along Y, does this by construction:
    # it self-limits to TROUGH_CRADLE_W because beyond that half-width the
    # cylinder surface rises back above the floor's own top face.
    half_w = p.TROUGH_CRADLE_W / 2.0
    depth = p.TROUGH_CRADLE_DEPTH
    cradle_R = (depth ** 2 + half_w ** 2) / (2.0 * depth)
    n = p.TROUGH_CRADLE_COUNT
    x0 = -(n - 1) * p.TROUGH_CRADLE_PITCH / 2.0
    for i in range(n):
        cx = x0 + i * p.TROUGH_CRADLE_PITCH
        solid = cq.Solid.makeCylinder(
            cradle_R, p.TROUGH_CRADLE_LEN,
            pnt=cq.Vector(cx, CRADLE_Y0, p.TROUGH_FLOOR_T - cradle_R),
            dir=cq.Vector(0, 1, 0),
        )
        cut = cq.Workplane("XY").newObject([solid])
        body = body.cut(cut)

    # three upright crown slots, near the front end past the cradles. Kept
    # a hair shallower than the floor's own thickness so it stays a blind
    # pocket (the crown must stand IN it, not fall through) -- the brief's
    # own 8mm figure and the floor's own 6mm are in genuine tension here;
    # see spore_trough's own notes for the crown's shallow-slot logic.
    slot_depth = min(p.TROUGH_CROWN_SLOT_DEPTH, p.TROUGH_FLOOR_T - 1.0)
    slot_y = CRADLE_Y0 + p.TROUGH_CRADLE_LEN + (HALF_W - (CRADLE_Y0 + p.TROUGH_CRADLE_LEN)) / 2.0
    slot = cq.Workplane("XY").circle(p.TROUGH_CROWN_SLOT_D / 2.0).extrude(
        slot_depth
    ).translate((0, 0, p.TROUGH_FLOOR_T - slot_depth))
    for sx in (-1, 0, 1):
        cut = slot.translate((sx * 30.0, slot_y, 0))
        body = body.cut(cut)

    # craquelure on the outer back wall face; owner notches are applied
    # separately by build_spore_trough_with_owner (per-player count).
    body = _craquelure_back_wall(body)

    return body


def _craquelure_back_wall(body):
    import math
    lines = [
        [(-90, 6), (-40, 14), (10, 4), (60, 16)],
        [(-60, 24), (-10, 18), (40, 26)],
    ]
    z0 = p.TROUGH_FLOOR_T
    for pts in lines:
        for (x0, z0o), (x1, z1o) in zip(pts, pts[1:]):
            length = ((x1 - x0) ** 2 + (z1o - z0o) ** 2) ** 0.5
            if length < 1e-6:
                continue
            angle = math.degrees(math.atan2(z1o - z0o, x1 - x0))
            mx, mz = (x0 + x1) / 2.0, z0 + (z0o + z1o) / 2.0
            box = cq.Workplane("XZ").box(
                length + 1.2, 1.2, p.TROUGH_CRAQUELURE_RELIEF, centered=(True, True, False)
            )
            box = box.rotate((0, 0, 0), (0, 0, 1), angle)
            box = box.translate((mx, BACK_Y - 0.05, mz))
            body = body.cut(box)
    return body


def build_spore_trough_with_owner(owner_notches):
    body = build_spore_trough()
    r = p.TROUGH_NOTCH_D
    notch = cq.Workplane("XY").box(
        p.TROUGH_NOTCH_W, p.TROUGH_NOTCH_D * 2, p.TROUGH_NOTCH_D,
        centered=(True, False, False),
    ).translate((0, BACK_Y - 0.1, p.TROUGH_FLOOR_T + p.TROUGH_BACK_WALL_H - p.TROUGH_NOTCH_D))
    spacing = 10.0
    x0 = -(owner_notches - 1) * spacing / 2.0
    for i in range(owner_notches):
        cut = notch.translate((x0 + i * spacing, 0, 0))
        body = body.cut(cut)
    return body
