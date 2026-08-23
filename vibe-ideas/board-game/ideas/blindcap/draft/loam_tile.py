"""loam_tile -- 132x132x28mm slab, 3x3 grid of stool sockets at 44mm pitch
(the ONE shared position list, reused for bore + collar + probe holes),
dovetailed on all four edges so any edge mates any edge. Prints top-face
up: bottom stays flat and unbroken.
"""
import math

import cadquery as cq

import params as p

HALF = p.TILE_SIZE / 2.0

# CCW-consistent per-edge local frame: each edge's local coordinate v runs
# from -HALF to +HALF walking counter-clockwise around the tile perimeter.
# A profile that is POINT-symmetric about v=0 (protrusion(-v) = -protrusion(v))
# self-mates with a translated copy of the same tile on ANY edge, in ANY
# rotation -- because two adjacent regions, each walked CCW around its own
# boundary, traverse their SHARED edge in opposite senses. That is the
# geometric fact "a central tab flanked by two half-slots" is reaching for;
# this is the exact, provably-self-mating version of it.
_EDGES = {
    # name: (outward_unit, v_to_xy)
    "+X": ((1, 0), lambda u, v: (HALF + u, v)),
    "+Y": ((0, 1), lambda u, v: (-v, HALF + u)),
    "-X": ((-1, 0), lambda u, v: (-HALF - u, -v)),
    "-Y": ((0, -1), lambda u, v: (v, -HALF - u)),
}


def _add_dovetail(tile, edge):
    # male tab: root at v in [V0, V1], flares wider at the tip
    tab_pts = [
        _EDGES[edge][1](0, p.DOVETAIL_V0),
        _EDGES[edge][1](0, p.DOVETAIL_V1),
        _EDGES[edge][1](p.DOVETAIL_DEPTH, p.DOVETAIL_V1 + p.DOVETAIL_FLARE),
        _EDGES[edge][1](p.DOVETAIL_DEPTH, p.DOVETAIL_V0 - p.DOVETAIL_FLARE),
    ]
    tab = (
        cq.Workplane("XY").polyline(tab_pts).close().extrude(p.TILE_T)
    )
    tile = tile.union(tab)

    # female slot: mirrored v-range [-V1, -V0], cut inward, with clearance
    c = p.DOVETAIL_CLEARANCE
    v0, v1 = -p.DOVETAIL_V1 - c, -p.DOVETAIL_V0 + c
    slot_pts = [
        _EDGES[edge][1](0, v0),
        _EDGES[edge][1](0, v1),
        _EDGES[edge][1](p.DOVETAIL_DEPTH + c, v1 - (p.DOVETAIL_FLARE + c)),
        _EDGES[edge][1](p.DOVETAIL_DEPTH + c, v0 + (p.DOVETAIL_FLARE + c)),
    ]
    slot = (
        cq.Workplane("XY").polyline(slot_pts).close().extrude(p.TILE_T)
    )
    tile = tile.cut(slot)
    return tile


def _segment_cutter(p0, p1, width, depth, z_top):
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy)
    if length < 1e-6:
        return None
    angle = math.degrees(math.atan2(dy, dx))
    mx, my = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    box = cq.Workplane("XY").box(
        length + width, width, depth, centered=(True, True, False)
    )
    box = box.rotate((0, 0, 0), (0, 0, 1), angle)
    box = box.translate((mx, my, z_top - depth))
    return box


def _craquelure(tile):
    """Shallow engraved crack lines, TILE_CRAQUELURE_RELIEF deep -- built as
    a chain of thin segment boxes (a "capsule" stroke) rather than an
    offset2D wire, so it stays robust across CadQuery versions.
    """
    lines = [
        [(-50, -50), (-20, -30), (10, -45), (45, -20)],
        [(-45, 40), (-15, 20), (20, 35), (48, 15)],
        [(-55, 0), (-25, 10), (5, -5), (35, 5), (55, -10)],
    ]
    for pts in lines:
        for p0, p1 in zip(pts, pts[1:]):
            cutter = _segment_cutter(p0, p1, 1.2, p.TILE_CRAQUELURE_RELIEF, p.TILE_T)
            if cutter is not None:
                tile = tile.cut(cutter)
    return tile


def build_loam_tile(socket_positions):
    """socket_positions: the ONE shared_positions(3,3,44) list, reused here
    for the bore, the collar AND the two probe-hole entry points per socket.
    """
    tile = cq.Workplane("XY").box(
        p.TILE_SIZE, p.TILE_SIZE, p.TILE_T,
        centered=(True, True, False),
    )

    for edge in _EDGES:
        tile = _add_dovetail(tile, edge)

    top_z = p.TILE_T
    bore_cutter = cq.Workplane("XY").circle(p.BORE_D / 2.0).extrude(p.BORE_DEPTH)
    collar_ring = (
        cq.Workplane("XY").circle(p.COLLAR_OD / 2.0).extrude(p.COLLAR_H)
        .cut(cq.Workplane("XY").circle(p.BORE_D / 2.0).extrude(p.COLLAR_H + 0.2))
    )

    azimuths = (45.0, 225.0)  # two probe holes per socket, opposite corners
    drops = (p.PROBE_UPPER_BELOW_SHOULDER - p.COLLAR_H,
             p.PROBE_LOWER_BELOW_SHOULDER - p.COLLAR_H)

    for (cx, cy, _z) in socket_positions:
        bore = bore_cutter.translate((cx, cy, top_z - p.BORE_DEPTH))
        tile = tile.cut(bore)
        collar = collar_ring.translate((cx, cy, top_z))
        tile = tile.union(collar)

        for az, drop in zip(azimuths, drops):
            ex = cx + p.PROBE_OFFSET * math.cos(math.radians(az))
            ey = cy + p.PROBE_OFFSET * math.sin(math.radians(az))
            hole = _oriented_hole(ex, ey, top_z, az, cx, cy, drop)
            tile = tile.cut(hole)

    tile = _craquelure(tile)
    return tile


def _oriented_hole(ex, ey, ez, entry_az_deg, cx, cy, drop_mm):
    ang = math.radians(p.PROBE_ANGLE_DEG)
    # reach at least the groove-band depth AND the full PROBE_CHANNEL_LEN a
    # staged/admitted pin needs to travel without hitting un-cut material
    # (see params.py's own note on why these two must share one number).
    length = max(drop_mm / math.cos(ang), p.PROBE_CHANNEL_LEN)
    # horizontal direction: from entry point toward socket centre
    hx, hy = cx - ex, cy - ey
    hn = math.hypot(hx, hy)
    hx, hy = hx / hn, hy / hn
    dx = math.sin(ang) * hx
    dy = math.sin(ang) * hy
    dz = -math.cos(ang)
    solid = cq.Solid.makeCylinder(
        p.PROBE_HOLE_D / 2.0, length,
        pnt=cq.Vector(ex, ey, ez),
        dir=cq.Vector(dx, dy, dz),
    )
    return cq.Workplane("XY").newObject([solid])
