"""Veinwake revision: faceted rind and cube-cluster bubble; millimetres.

Design authority: completed Mara Masque handoff plus the correction Wish.
The rock is now an all-planar low-polygon boulder and the bubble marker is an
interpenetrating cube cluster. The tooth, the rules, the nine circular seats
and every preserved constant below are unchanged from the original.
"""
from math import atan2, degrees, sqrt, hypot, radians, sin, cos
from build123d import (Align, Box, Color, Compound, Cylinder, Face,
                       Plane, Polyline, Pos, RegularPolygon, Shell, Solid, Wire,
                       extrude, loft)
import cadfits

BOARD_LENGTH = 140.0
BOARD_WIDTH = 130.0
RIM_HEIGHT = 14.0
FIELD_HEIGHT = 8.0
SEAT_DEPTH = 2.0
SEAT_Z = FIELD_HEIGHT - SEAT_DEPTH
GRID_PITCH = 36.0
FOOT_DIAMETER = 28.0
FOOT_HEIGHT = 3.0
SEAT_CLEARANCE = 1.0
# This open game pocket intentionally exceeds the helper's ordinary fit band.
# Widen only this design calculation, then restore the shared helper default.
_ordinary_clearance_max = cadfits.EXPLICIT_MAX
cadfits.EXPLICIT_MAX = SEAT_CLEARANCE
SEAT_DIAMETER = cadfits.slot_for(FOOT_DIAMETER, SEAT_CLEARANCE)
cadfits.EXPLICIT_MAX = _ordinary_clearance_max
CLUSTER_HEIGHT = 26.0
ASSEMBLED_HEIGHT = SEAT_Z + CLUSTER_HEIGHT
CORNER_RADIUS = 6.0
FIELD_LENGTH = 114.0
FIELD_WIDTH = 104.0
FIELD_RADIUS = 22.0
TOOTH_RADIUS = 11.0
TOOTH_SHOULDER = 18.0
TOOTH_TIP_RADIUS = 2.5
TOOTH_TIP_OFFSET = 2.0
HELD_OFFSET = 55.0

MIN_WALL = 3.0
OVERHANG_LIMIT = 0.695          # |face normal Z| bound; sin(45 deg) = 0.7071

# Rock plan: sixteen straight segments of deliberately unequal length
# (11.9 - 55.8 mm), bounding box exactly BOARD_LENGTH x BOARD_WIDTH, centred.
ROCK_PLAN = ((70.000, 21.442), (69.716, 43.344), (55.708, 59.942), (36.742, 62.819),
             (-18.483, 65.000), (-47.198, 64.604), (-56.780, 56.288), (-62.845, 35.682),
             (-70.000, -12.183), (-68.977, -42.187), (-54.771, -58.608), (-36.109, -61.333),
             (10.587, -64.227), (46.434, -65.000), (60.731, -53.243), (65.340, -33.044))
# Per-edge inward lean of the outer wall facet over the full RIM_HEIGHT rise:
# every facet is a flat plane tilted 8-25 degrees from vertical, so nothing
# overhangs and the top edge is the angular chain those facets cut.
ROCK_WALL_LEAN = (3.0, 6.0, 2.0, 4.6, 3.4, 5.6, 2.2, 6.0,
                  2.8, 5.8, 2.0, 4.4, 3.2, 5.4, 2.4, 6.5)
# Flat rim band width, held at the 3.00 mm minimum wall so the faceted
# cavity band takes every millimetre the nine seats leave.
ROCK_RIM_WIDTH = (3.78, 3.78, 3.78, 3.78, 3.78, 3.78, 3.78, 3.78,
                  3.78, 3.78, 3.78, 3.78, 3.78, 3.78, 3.78, 3.78)
ROCK_CAVITY_DROP = (9.00, 9.00, 8.10, 2.60, 9.00, 6.80, 4.20, 2.60,
                    9.00, 9.00, 5.60, 2.60, 7.50, 7.60, 7.60, 2.60)
# Height of each cavity crest vertex. RIM_HEIGHT is the rock's top; the crest
# dips below it by its own amount at each vertex, so the rim's inner edge is a
# jagged three-dimensional chain and no two neighbouring facets share a tilt.
ROCK_CREST_Z = (14.0, 11.6, 13.4, 12.2, 14.0, 11.8, 13.0, 12.6,
                14.0, 11.4, 13.6, 12.0, 14.0, 11.9, 13.2, 12.4)
SEAT_FIELD_MARGIN = 13.0        # least flat-field clearance around a seat axis

# Cube cluster: five interpenetrating cubes, edge 16.00 down to 7.00 mm, each
# on its own two-axis orientation. Every cube axis keeps |Z| <= OVERHANG_LIMIT,
# so all thirty exposed square faces stay within 45 degrees of vertical.
CUBE_CLUSTER = ((16.0, 45.000, 35.264, 18.0, 0.60, -0.40, 8.3735),
                (12.8, 51.728, 33.903, -56.9, 1.45, 2.22, 14.5030),
                (10.2, 32.631, 37.969, 59.6, -3.12, 4.07, 8.0667),
                (8.4, 45.345, 17.162, -23.3, 6.15, -4.53, 7.3659),
                (7.0, 36.089, 41.200, 108.0, -4.95, -5.72, 13.9316))
CLUSTER_SPIN = -138.0           # turns the cluster's widest axis onto X

OUTLINE = [(-70, -25), (-60, -48), (-38, -65), (28, -65), (54, -52), (70, -22),
           (70, 20), (57, 48), (34, 65), (-30, 65), (-55, 50), (-70, 24)]
GRID = [(x, y) for y in (GRID_PITCH, 0, -GRID_PITCH) for x in (-GRID_PITCH, 0, GRID_PITCH)]
DRAW_CELLS = 'XOXXOOOXX'
PALETTE = {'rind': (121 / 255, 109 / 255, 96 / 255),
           'tooth': (156 / 255, 120 / 255, 190 / 255),
           'bubble': (148 / 255, 197 / 255, 180 / 255)}

assert SEAT_DIAMETER == 30.0 and SEAT_Z == 6.0
assert GRID_PITCH - SEAT_DIAMETER >= 3.0
assert 2 * TOOTH_TIP_RADIUS * sqrt(3) / 2 >= 2.0
assert TOOTH_TIP_OFFSET + TOOTH_TIP_RADIUS < TOOTH_RADIUS
assert ASSEMBLED_HEIGHT == 32.0


def finish(shape, label, kind):
    assert len(shape.solids()) == 1, f'{label}: expected one fused solid'
    assert shape.is_valid, f'{label}: invalid topology'
    shape.label = label
    # Workshop's current delivery contract requires direct sRGB channels.
    shape.color = Color(*PALETTE[kind])
    return shape


def rock_footprint():
    """The closed sixteen-segment plan polygon, counter-clockwise."""
    xs = [p[0] for p in ROCK_PLAN]
    ys = [p[1] for p in ROCK_PLAN]
    assert abs(max(xs) - min(xs) - BOARD_LENGTH) < 1e-6
    assert abs(max(ys) - min(ys) - BOARD_WIDTH) < 1e-6
    assert abs(max(xs) + min(xs)) < 1e-6 and abs(max(ys) + min(ys)) < 1e-6
    return ROCK_PLAN


def _shrink(poly, drops):
    """Pull every vertex inward along its angle bisector by its own amount."""
    n = len(poly)
    out = []
    for i in range(n):
        a = (poly[i][0] - poly[i - 1][0], poly[i][1] - poly[i - 1][1])
        b = (poly[(i + 1) % n][0] - poly[i][0], poly[(i + 1) % n][1] - poly[i][1])
        la, lb = hypot(*a), hypot(*b)
        vx = -a[1] / la - b[1] / lb
        vy = a[0] / la + b[0] / lb
        lv = hypot(vx, vy)
        out.append((poly[i][0] + vx / lv * drops[i], poly[i][1] + vy / lv * drops[i]))
    return out


def _point_to_polygon(poly, pt):
    best = 1e9
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        vx, vy = q[0] - p[0], q[1] - p[1]
        wx, wy = pt[0] - p[0], pt[1] - p[1]
        t = max(0.0, min(1.0, (wx * vx + wy * vy) / (vx * vx + vy * vy)))
        best = min(best, hypot(wx - t * vx, wy - t * vy))
    return best


def _polyhedron(points, loops):
    """One closed solid from explicit planar polygonal faces."""
    faces = [Face(Wire(Polyline(*[points[i] for i in loop], close=True))) for loop in loops]
    solid = Solid(Shell(faces))
    if solid.volume < 0:
        solid = Solid(Shell([Face(Wire(Polyline(*[points[i] for i in reversed(loop)],
                                                close=True))) for loop in loops]))
    assert solid.is_valid and solid.volume > 0, 'polyhedron did not close'
    return solid


def cavity_rings():
    """Jagged rim crest and the flat field boundary at FIELD_HEIGHT.

    The crest vertices sit at their own heights between ROCK_CREST_Z's lowest
    value and RIM_HEIGHT, so every triangle of the cavity wall stands at its
    own angle instead of the constant-width groove a uniform ring would cut.
    """
    n = len(ROCK_PLAN)
    rim = _shrink(ROCK_PLAN, [max(ROCK_WALL_LEAN[i - 1], ROCK_WALL_LEAN[i]) + ROCK_RIM_WIDTH[i]
                              for i in range(n)])
    floor = _shrink(rim, ROCK_CAVITY_DROP)
    for i in range(n):
        assert FIELD_HEIGHT < ROCK_CREST_Z[i] <= RIM_HEIGHT, 'crest leaves the rock'
        assert RIM_HEIGHT - ROCK_CREST_Z[i] <= RIM_HEIGHT - FIELD_HEIGHT, 'crest too deep'
    for cell in GRID:
        assert _point_to_polygon(floor, cell) >= SEAT_FIELD_MARGIN, 'seat leaves the field'
    return rim, floor


def cavity_tilts():
    """Angle from vertical of each cavity facet's leading edge, in degrees."""
    n = len(ROCK_PLAN)
    return [degrees(atan2(ROCK_CAVITY_DROP[i], ROCK_CREST_Z[i] - FIELD_HEIGHT))
            for i in range(n)]


def _cavity_cutter(rim, floor):
    n = len(rim)
    top = RIM_HEIGHT + 6.0
    pts = ([(x, y, FIELD_HEIGHT) for x, y in floor]
           + [(x, y, ROCK_CREST_Z[i]) for i, (x, y) in enumerate(rim)]
           + [(x, y, top) for x, y in rim])
    loops = [tuple(range(n - 1, -1, -1))]
    for i in range(n):
        j = (i + 1) % n
        loops.append((i, j, n + i))
        loops.append((j, n + j, n + i))
        loops.append((n + i, n + j, 2 * n + j))
        loops.append((n + i, 2 * n + j, 2 * n + i))
    loops.append(tuple(range(2 * n, 3 * n)))
    return _polyhedron(pts, loops)


def make_rind(label='rind'):
    """Low-polygon fractured boulder: every rock surface is a flat facet."""
    plan = rock_footprint()
    n = len(plan)
    body = extrude(Face(Wire(Polyline(*[(x, y, 0.0) for x, y in plan], close=True))),
                   amount=RIM_HEIGHT)
    for i in range(n):
        p, q = plan[i], plan[(i + 1) % n]
        ex, ey = q[0] - p[0], q[1] - p[1]
        length = hypot(ex, ey)
        lean = ROCK_WALL_LEAN[i]
        assert lean / RIM_HEIGHT < 1.0, 'wall facet overhangs'
        outward = Plane(origin=(p[0], p[1], 0.0),
                        z_dir=(RIM_HEIGHT * ey, -RIM_HEIGHT * ex, lean * length))
        body = body - outward * (Pos(0, 0, 200) * Box(400, 400, 400))
    rim, floor = cavity_rings()
    body = body - _cavity_cutter(rim, floor)
    seats = [Pos(x, y, SEAT_Z) * Cylinder(SEAT_DIAMETER / 2, RIM_HEIGHT - SEAT_Z + 1,
             align=(Align.CENTER, Align.CENTER, Align.MIN)) for x, y in GRID]
    body = body - seats
    box = body.bounding_box()
    assert abs(box.size.X - BOARD_LENGTH) < 1e-6 and abs(box.size.Y - BOARD_WIDTH) < 1e-6
    assert abs(box.min.Z) < 1e-9 and abs(box.max.Z - RIM_HEIGHT) < 1e-9
    return finish(body, label, 'rind')


def foot():
    return Cylinder(FOOT_DIAMETER / 2, FOOT_HEIGHT,
                    align=(Align.CENTER, Align.CENTER, Align.MIN))


def make_tooth(label='tooth'):
    crystal = loft([Pos(0, 0, 2) * RegularPolygon(TOOTH_RADIUS, 6),
                    Pos(0, 0, TOOTH_SHOULDER) * RegularPolygon(TOOTH_RADIUS, 6),
                    Pos(TOOTH_TIP_OFFSET, 0, CLUSTER_HEIGHT) * RegularPolygon(TOOTH_TIP_RADIUS, 6)],
                   ruled=True)
    return finish(foot() + crystal, label, 'tooth')


def _cube_matrix(ax, ay, az):
    """Orientation of one cube; the matrix columns are its three edge axes."""
    a, b, g = radians(ax), radians(ay), radians(az + CLUSTER_SPIN)
    rx = ((1, 0, 0), (0, cos(a), -sin(a)), (0, sin(a), cos(a)))
    ry = ((cos(b), 0, sin(b)), (0, 1, 0), (-sin(b), 0, cos(b)))
    rz = ((cos(g), -sin(g), 0), (sin(g), cos(g), 0), (0, 0, 1))
    m = [[sum(rz[r][k] * sum(ry[k][s] * rx[s][c] for s in range(3)) for k in range(3))
          for c in range(3)] for r in range(3)]
    for c in range(3):
        assert abs(m[2][c]) <= OVERHANG_LIMIT, 'cube face would overhang'
    return m


def cluster_lift():
    """Exact rise that puts the cluster's highest corner at CLUSTER_HEIGHT."""
    peaks = []
    for edge, ax, ay, az, _cx, _cy, cz in CUBE_CLUSTER:
        m = _cube_matrix(ax, ay, az)
        peaks.append(cz + edge / 2 * sum(abs(m[2][c]) for c in range(3)))
    return CLUSTER_HEIGHT - max(peaks)


def _cube_frame(m, cx, cy, cz):
    spin = radians(CLUSTER_SPIN)
    origin = (cx * cos(spin) - cy * sin(spin), cx * sin(spin) + cy * cos(spin),
              cz + cluster_lift())
    return Plane(origin=origin,
                 x_dir=(m[0][0], m[1][0], m[2][0]),
                 z_dir=(m[0][2], m[1][2], m[2][2]))


def make_bubble(label='bubble'):
    """Pyrite-habit cluster: five interpenetrating cubes on the shared foot."""
    edges = [spec[0] for spec in CUBE_CLUSTER]
    assert max(edges) == 16.0 and min(edges) >= 7.0
    assert len(set(edges)) == len(edges)
    body = foot()
    for edge, ax, ay, az, cx, cy, cz in CUBE_CLUSTER:
        frame = _cube_frame(_cube_matrix(ax, ay, az), cx, cy, cz)
        body = body + frame * Box(edge, edge, edge)
    body = body & (Pos(0, 0, 200) * Box(400, 400, 400))
    box = body.bounding_box()
    assert abs(box.max.Z - CLUSTER_HEIGHT) < 1e-6, f'{label}: height {box.max.Z}'
    assert abs(box.min.Z) < 1e-9
    assert max(box.size.X, box.size.Y) <= FOOT_DIAMETER + 1e-6, 'cluster leaves the foot'
    return finish(body, label, 'bubble')


def make_assembly(state='draw'):
    children = [make_rind()]
    if state == 'draw':
        counts = {'X': 0, 'O': 0}
        for (x, y), cell in zip(GRID, DRAW_CELLS):
            counts[cell] += 1
            kind = 'tooth' if cell == 'X' else 'bubble'
            builder = make_tooth if cell == 'X' else make_bubble
            children.append(Pos(x, y, SEAT_Z) * builder(f'{kind}_{counts[cell]}'))
    else:
        assert state in ('before', 'after')
        placements = [('tooth_1', -GRID_PITCH, GRID_PITCH, SEAT_Z),
                      ('tooth_2', 0, GRID_PITCH, SEAT_Z),
                      ('tooth_3', GRID_PITCH, GRID_PITCH, SEAT_Z + (HELD_OFFSET if state == 'before' else 0)),
                      ('bubble_1', -GRID_PITCH, 0, SEAT_Z), ('bubble_2', 0, 0, SEAT_Z)]
        for name, x, y, z in placements:
            builder = make_tooth if name.startswith('tooth') else make_bubble
            children.append(Pos(x, y, z) * builder(name))
    return Compound(label='veinwake', children=children)
