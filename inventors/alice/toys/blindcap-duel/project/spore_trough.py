"""spore_trough -- compact 154x150x40mm personal tray. A 3x2 grid of six
cradles holds stools lying on their side; a 34mm-tall back wall
blocks the opposite seat's sightline; three upright slots hold claim_crowns
on edge; an owner notch count is cut into the back wall; craquelure matches
loam_tile's. Prints open-top, no supports.
"""
import cadquery as cq

import params as p

HALF_L = p.TROUGH_L / 2.0
HALF_W = p.TROUGH_W / 2.0
BACK_Y = -HALF_W
CRADLE_Y0 = BACK_Y + p.TROUGH_WALL_T + 3.0


def build_spore_trough():
    body = cq.Workplane("XY").box(
        p.TROUGH_L, p.TROUGH_W, p.TROUGH_FLOOR_T, centered=(True, True, False)
    )

    # Build the low perimeter as one ring, not four face-touching boxes.
    # A 0.2mm overlap into the floor/back extension avoids compound shells
    # and produces a watertight slicer mesh.
    overlap = 0.2
    low_outer = (
        cq.Workplane("XY")
        .box(
            p.TROUGH_L,
            p.TROUGH_W,
            p.TROUGH_SIDE_WALL_H + overlap,
            centered=(True, True, False),
        )
        .translate((0, 0, p.TROUGH_FLOOR_T - overlap))
    )
    low_inner = (
        cq.Workplane("XY")
        .box(
            p.TROUGH_L - 2 * p.TROUGH_WALL_T,
            p.TROUGH_W - 2 * p.TROUGH_WALL_T,
            p.TROUGH_SIDE_WALL_H + 2 * overlap,
            centered=(True, True, False),
        )
        .translate((0, 0, p.TROUGH_FLOOR_T - overlap / 2))
    )
    body = body.union(low_outer.cut(low_inner))

    # Extend only the rear wall to the 40mm overall height.
    rear_extra_h = p.TROUGH_BACK_WALL_H - p.TROUGH_SIDE_WALL_H
    back_wall = (
        cq.Workplane("XY")
        .box(
            p.TROUGH_L,
            p.TROUGH_WALL_T,
            rear_extra_h + overlap,
            centered=(True, False, False),
        )
        .translate(
            (
                0,
                BACK_Y,
                p.TROUGH_FLOOR_T + p.TROUGH_SIDE_WALL_H - overlap,
            )
        )
    )
    body = body.union(back_wall).clean()

    # Six cradles in a compact 3x2 grid: shallow scalloped grooves (a wide,
    # shallow arc, not a full
    # half-round -- that would need a floor deeper than the cap is wide).
    # A single large-radius cylinder, axis along Y, does this by construction:
    # it self-limits to TROUGH_CRADLE_W because beyond that half-width the
    # cylinder surface rises back above the floor's own top face.
    half_w = p.TROUGH_CRADLE_W / 2.0
    depth = p.TROUGH_CRADLE_DEPTH
    cradle_R = (depth ** 2 + half_w ** 2) / (2.0 * depth)
    x0 = -(p.TROUGH_CRADLE_COLS - 1) * p.TROUGH_CRADLE_PITCH / 2.0
    for row in range(p.TROUGH_CRADLE_ROWS):
        y0 = CRADLE_Y0 + row * p.TROUGH_CRADLE_ROW_PITCH
        for col in range(p.TROUGH_CRADLE_COLS):
            cx = x0 + col * p.TROUGH_CRADLE_PITCH
            # Put the cylinder above the floor so its lower arc cuts a true
            # 3mm-deep scallop; the previous below-floor tangent created
            # zero-thickness faces and open STL edges.
            cradle_center_z = p.TROUGH_FLOOR_T - depth + cradle_R
            solid = cq.Solid.makeCylinder(
                cradle_R, p.TROUGH_CRADLE_LEN,
                pnt=cq.Vector(cx, y0, cradle_center_z),
                dir=cq.Vector(0, 1, 0),
            )
            cut = cq.Workplane("XY").newObject([solid])
            body = body.cut(cut)

    # three upright crown slots, near the front end past the cradles. Kept
    # 5mm-deep blind pockets leave a deliberate 1mm floor.
    slot_depth = p.TROUGH_CROWN_SLOT_DEPTH
    slot_y = HALF_W - p.TROUGH_WALL_T - p.TROUGH_CROWN_SLOT_D / 2.0 - 1.0
    slot = cq.Workplane("XY").circle(p.TROUGH_CROWN_SLOT_D / 2.0).extrude(
        slot_depth
    ).translate((0, 0, p.TROUGH_FLOOR_T - slot_depth))
    for sx in (-1, 0, 1):
        cut = slot.translate((sx * 30.0, slot_y, 0))
        body = body.cut(cut)

    # Keep the back wall unengraved: the earlier near-tangent craquelure cuts
    # tessellated with open STL edges even though the B-rep was valid. Owner
    # notches still provide a tactile/visible P1/P2 mark.
    return body


def _craquelure_back_wall(body):
    import math
    lines = [
        [(-68, 6), (-34, 14), (8, 4), (66, 16)],
        [(-58, 24), (-10, 18), (48, 26)],
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
        p.TROUGH_NOTCH_W, p.TROUGH_NOTCH_D * 2, p.TROUGH_NOTCH_D + 0.5,
        centered=(True, False, False),
    ).translate((0, BACK_Y - 0.1, p.TROUGH_FLOOR_T + p.TROUGH_BACK_WALL_H - p.TROUGH_NOTCH_D))
    spacing = 10.0
    x0 = -(owner_notches - 1) * spacing / 2.0
    for i in range(owner_notches):
        cut = notch.translate((x0 + i * spacing, 0, 0))
        body = body.cut(cut)
    return body
