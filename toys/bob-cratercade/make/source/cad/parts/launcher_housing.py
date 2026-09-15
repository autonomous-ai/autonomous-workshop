"""Single printed guide cradle and guarded band pocket, rooted through deck.

Original guide48..56 would collide with the retracted head. Guide34..42
preserves full18 travel, faceY66 and band postY70. The single removable anchor
uses130/136/142 positions: three simultaneous mushroom collars would overlap.
"""
from math import sqrt
from build123d import Align, Box, Cone, Cylinder, Pos, RegularPolygon, extrude
import params as p


def _rect(x, y, z):
    return Pos(sum(x) / 2, sum(y) / 2, sum(z) / 2) * Box(x[1] - x[0], y[1] - y[0], z[1] - z[0])


def _bore(x, y, z0, z1):
    return Pos(x, y, z0) * Cylinder(p.M4_BORE / 2, z1 - z0, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _hex_access(x, y, top, direction):
    bottom = top - p.NUT_T - p.LAUNCH_NUT_SEAT_CLEAR
    # Guide nuts present a flat to the rod, preserving a0.95mm solid wall.
    # Root rotates the corresponding qualified hardware by the same angle.
    rotation = p.LAUNCH_GUIDE_NUT_ROTATION if direction in ("south", "north") else 0
    profile = RegularPolygon(p.NUT_POCKET_AF / sqrt(3), 6, rotation=rotation)
    pocket = Pos(x, y, bottom) * extrude(profile, amount=top - bottom)
    half = p.NUT_POCKET_AF / 2
    if direction == "south":
        path = _rect((x - half, x + half), (p.LAUNCH_BASE_Y[0] - p.LAUNCH_CUT_OVER, y), (bottom, top))
    elif direction == "north":
        path = _rect((x - half, x + half), (y, p.LAUNCH_HOUSING_Y[1] + p.LAUNCH_CUT_OVER), (bottom, top))
    else:
        path = _rect((p.LAUNCH_POCKET_X[0] - p.LAUNCH_CUT_OVER, x), (y - half, y + half), (bottom, top))
    return pocket + path


def build():
    floor = _rect(p.LAUNCH_BASE_X, p.LAUNCH_BASE_Y, (0, p.LAUNCH_BASE_T))
    xlo = p.LAUNCH_X - p.LAUNCH_GUIDE_SIDE / 2
    xhi = p.LAUNCH_X + p.LAUNCH_GUIDE_SIDE / 2
    left = _rect((p.LAUNCH_HOUSING_X[0], xlo), p.LAUNCH_HOUSING_Y, (0, p.LAUNCH_GUIDE_TOP))
    right = _rect((xhi, p.LAUNCH_HOUSING_X[1]), p.LAUNCH_HOUSING_Y, (0, p.LAUNCH_GUIDE_TOP))
    body = floor + left + right
    slot = _rect(p.LAUNCH_SLOT_X, p.LAUNCH_SLOT_Y, (p.LAUNCH_BASE_T, p.LAUNCH_GUIDE_TOP + p.LAUNCH_CUT_OVER))
    body -= slot
    for index, (x, y) in enumerate(p.LAUNCH_GUIDE_BOLTS):
        body -= _bore(x, y, -p.LAUNCH_CUT_OVER, p.LAUNCH_GUIDE_TOP + p.LAUNCH_CUT_OVER)
        body -= _hex_access(x, y, p.LAUNCH_GUIDE_NUT_TOP, "south" if index == 0 else "north")
    pocket = _rect(p.LAUNCH_POCKET_X, p.LAUNCH_POCKET_Y, (0, p.LAUNCH_GUARD_BOTTOM))
    pocket -= _rect((p.LAUNCH_POCKET_X[0] + p.LAUNCH_WALL, p.LAUNCH_POCKET_X[1] - p.LAUNCH_WALL), (p.LAUNCH_POCKET_Y[0] + p.LAUNCH_WALL, p.LAUNCH_POCKET_Y[1] - p.LAUNCH_WALL), (p.LAUNCH_POCKET_FLOOR, p.LAUNCH_GUARD_BOTTOM + p.LAUNCH_CUT_OVER))
    # The guard supplies this portal's roof, so service removal opens a true
    # vertical insertion path for the rigid crosshead.
    pocket -= _rect((p.LAUNCH_POCKET_X[1] - p.LAUNCH_WALL - p.LAUNCH_CUT_OVER, p.LAUNCH_POCKET_X[1] + p.LAUNCH_CUT_OVER), p.LAUNCH_TUNNEL_Y, (p.LAUNCH_TUNNEL_Z[0], p.LAUNCH_GUARD_BOTTOM + p.LAUNCH_CUT_OVER))
    body += pocket
    for x, y in p.LAUNCH_GUARD_BOLTS:
        # Flat column sides leave full-thickness jambs at the side-loaded
        # nut slots; circular sides formerly left fragile tangent feathers.
        body += _rect((x - p.LAUNCH_GUARD_COLUMN_R, x + p.LAUNCH_GUARD_COLUMN_R), (y - p.LAUNCH_GUARD_COLUMN_R, y + p.LAUNCH_GUARD_COLUMN_R), (0, p.LAUNCH_GUARD_BOTTOM))
        body -= _bore(x, y, -p.LAUNCH_CUT_OVER, p.LAUNCH_GUARD_BOTTOM + p.LAUNCH_CUT_OVER)
        body -= _hex_access(x, y, p.LAUNCH_GUARD_NUT_TOP, "west")
    body += _rect(p.LAUNCH_REAR_MOUNT_X, p.LAUNCH_REAR_MOUNT_Y, (0, p.LAUNCH_BASE_T))
    for x, y in p.LAUNCH_MOUNT_POINTS:
        body += Pos(x, y, 0) * Cylinder(p.LAUNCH_MOUNT_R, p.LAUNCH_MOUNT_Z, align=(Align.CENTER, Align.CENTER, Align.MIN))
        body -= _bore(x, y, -p.LAUNCH_CUT_OVER, p.LAUNCH_MOUNT_Z + p.LAUNCH_CUT_OVER)
        body -= Pos(x, y, p.LAUNCH_MOUNT_Z - p.LAUNCH_CSK_DEPTH) * Cone(p.M4_BORE / 2, p.CSK_RECESS_D / 2, p.LAUNCH_CSK_DEPTH, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for y in p.LAUNCH_ANCHOR_Y:
        body -= _bore(p.LAUNCH_BAND_X, y + p.LAUNCH_ANCHOR_BOLT_OFFSET, -p.LAUNCH_CUT_OVER, p.LAUNCH_POCKET_FLOOR + p.LAUNCH_CUT_OVER)
    return body


def print_shape():
    shape = build()
    box = shape.bounding_box()
    return Pos(-box.min.X, -box.min.Y, 0) * shape
