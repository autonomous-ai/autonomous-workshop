"""Independent fit, part-count, revision-invariance and built-geometry audit.

Sections marked BUILT read the exported STEP, never the source that made it.
Two of them are the gates this revision exists to install:

  * the roof's mirror symmetry about x = 0, which is what would have caught the
    yoke offset the previous revision shipped;
  * the board's fit layer, measured pocket by pocket on the built base.
"""
import hashlib
import json
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import periastra_lib as p
from build123d import (Align, Box, Plane, Pos, Rot, import_step, mirror, extrude)

CAD = Path(__file__).resolve().parents[1]
PRODUCT = CAD.parent
TOL = 1e-6
report = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# =============================================================== frozen counters
# The two counters are finished and must come out of this revision byte for byte
# identical to the archive being corrected. If either moves, the build fails here.
FROZEN = {
    'part_sun_counter.step': '262ccc86f6e4c40394e8611fd0f98ee7a7aaf2ec5b3e42fab36d66902afe5f3b',
    'part_moon_counter.step': '588d285baf2e312d81ca39c92ddad82ff83725aa721f5a5789ffb1a0ec50301e',
}
for name, want in FROZEN.items():
    path = CAD/name
    assert path.exists(), f'{name} has not been built; the frozen-counter gate cannot run'
    got = sha(path)
    assert got == want, f'FROZEN COUNTER MOVED: {name} is {got}, must be {want}'
report['frozen_counters'] = {k: v[:16]+'...' for k, v in FROZEN.items()}

# ---- unchanged published base envelope ---------------------------------------
assert (p.BASE, p.HEIGHT, p.WALL) == (190, 24, 3)
assert (p.BOARD, p.CELL, p.ROWS) == (176, 22, 8)
assert (p.OPENING, p.CORNER, p.FLOOR) == (184, 2, 11)
assert (p.LEDGE_TOP, p.LEDGE_DEPTH, p.LEDGE_LENGTH) == (21, 3, 24)
assert p.SILL_TOP == 17 and p.PIER_INNER == 88
assert (p.STAR_RADIUS, p.STAR_X, p.RELIEF, p.STAR_BEVEL) == (3, 22, 0.8, 0.25)
assert p.OPENING/2 - p.LEDGE_DEPTH > p.BOARD/2
assert p.STAR_RADIUS <= (p.OPENING - p.BOARD)/2
assert not hasattr(p, 'RECESS') and not hasattr(p, 'SQUARE_BEVEL') \
    and not hasattr(p, 'SQUARE_CORNER'), 'the replaced recess mechanism is still present'

# ---- unchanged fit, storage and play -----------------------------------------
assert p.ROOF_CLEARANCE == 0.8
assert math.isclose((p.OPENING - p.ROOF_SIZE)/2, 0.8, abs_tol=1e-9)
assert math.isclose(p.ROOF_SIZE, 182.4, abs_tol=1e-9)
assert p.LIFT == 100
assert p.COUNTER_HEIGHT == 7.0
assert p.LEDGE_TOP - p.FLOOR >= 10
# The inlays finish flush, so they consume NONE of the storage void.
assert math.isclose(p.LEDGE_TOP - p.FLOOR, 10.0, abs_tol=1e-9)
assert math.isclose(p.LEDGE_TOP - (p.FLOOR + p.COUNTER_HEIGHT), 3.0, abs_tol=1e-9)
positions = [(c, r) for r in [0, 1, 2, 5, 6, 7] for c in range(8) if (c + r) % 2 == 0]
assert len(set(positions)) == 24 and sum(r < 3 for c, r in positions) == 12
assert all((c + r) % 2 == 0 for c, r in positions)
assert p.CELL - p.COUNTER_DIAMETER >= 2 - 1e-9
assert (p.CELL - p.COUNTER_DIAMETER)/2 >= 1.0 - 1e-9
outer_centre = -p.BOARD/2 + 7.5*p.CELL
assert math.isclose(outer_centre, 77.0, abs_tol=1e-9)
assert outer_centre + p.COUNTER_DIAMETER/2 <= p.BOARD/2 + 1e-9
assert outer_centre + p.COUNTER_DIAMETER/2 <= p.OPENING/2 - p.LEDGE_DEPTH + 1e-9
assert math.hypot(p.CELL, p.CELL) - p.COUNTER_DIAMETER >= 11.0

# The closed box's perimeter reveal. Side walls drop to z17, the roof plate
# underside seats at z21, so the reveal is 4.0 mm tall. A 7.0 mm counter cannot
# pass it; a 2.0 mm inlay can. Both numbers are carried into GEOMETRY-NOTES.md as
# one disclosed limitation the host deferred.
reveal = p.LEDGE_TOP - p.SILL_TOP
assert math.isclose(reveal, 4.0, abs_tol=1e-9)
assert reveal < p.COUNTER_HEIGHT - 1e-9, (reveal, p.COUNTER_HEIGHT)
assert reveal < p.COUNTER_DIAMETER - 1e-9
assert p.INLAY_THICK < reveal, 'disclosed: a loose inlay is thinner than the open reveal'
report['reveal_mm'] = reveal

# ---- roof: plate, drum, rotation ring, exact hemisphere, slit -----------------
assert (p.PLATE, p.ROOF_CORNER) == (3.0, 1.2)
drum_top = p.PLATE + p.DRUM_HEIGHT
apex = drum_top + p.DOME_RISE
assert p.DRUM_RADIUS == 75.0 and p.DRUM_HEIGHT == 11.7
assert math.isclose(p.DRUM_HEIGHT, 14.0*150/180, abs_tol=0.04)
assert math.isclose(drum_top, 14.7, abs_tol=1e-9)
assert math.isclose(p.LEDGE_TOP + p.PLATE, 24.0, abs_tol=1e-9)
assert math.isclose(p.LEDGE_TOP + drum_top, 35.7, abs_tol=1e-9)
assert p.DOME_SPHERE_RADIUS == p.DOME_BASE_RADIUS == p.DOME_RISE == 75.0
assert math.isclose(p.LEDGE_TOP + apex, 110.7, abs_tol=1e-9)
assert math.isclose(p.DRUM_RADIUS, p.DOME_BASE_RADIUS, abs_tol=1e-9)
assert math.isclose(2*p.DOME_BASE_RADIUS, 150.0, abs_tol=1e-9)
assert (p.RING_WIDTH, p.RING_DEPTH, p.RING_BELOW_TOP) == (2.0, 1.0, 4.0)
assert math.isclose(math.degrees(math.atan2(p.RING_RELIEF, p.RING_DEPTH)), 50.0, abs_tol=0.5)
assert drum_top - p.RING_BELOW_TOP == 10.7
assert p.SLIT_WIDTH == 30.0 and p.SLIT_FAR_RUN == 30.0
assert math.isclose(p.SLIT_FAR_Y,
                    p.DOME_SPHERE_RADIUS*math.sin(p.SLIT_FAR_RUN/p.DOME_SPHERE_RADIUS), abs_tol=1e-9)
assert math.isclose(math.degrees(p.SLIT_FAR_RUN/p.DOME_SPHERE_RADIUS), 22.9, abs_tol=0.05)
assert 0 < p.SLIT_FAR_Y < p.DOME_BASE_RADIUS
assert math.isclose(p.ROOF_SIZE/2 - p.DOME_BASE_RADIUS, 16.2, abs_tol=1e-9)

# ---- telescope: size held exactly, yoke re-centred ----------------------------
assert p.TUBE_RADIUS*2 == 15.0 and p.TUBE_BORE_RADIUS*2 == 7.0
assert p.TUBE_RADIUS - p.TUBE_BORE_RADIUS == 4.0
assert p.TUBE_BORE_DEPTH >= 12.0
assert p.TUBE_LENGTH == 45.0 and p.TUBE_ELEVATION == 35.0
assert p.TUBE_BACK[0] == 0.0
axis, up = p.tube_axis()
front = p.tube_point(p.TUBE_LENGTH)
centre = (0.0, drum_top)
muzzle_radius = math.hypot(front[0] - centre[0], front[1] - centre[1])
clearance = muzzle_radius - p.DOME_SPHERE_RADIUS
assert clearance >= p.MUZZLE_CLEARANCE_MIN, clearance
back_radius = math.hypot(p.TUBE_BACK[1], p.TUBE_BACK[2] - drum_top)
assert back_radius < p.DOME_SPHERE_RADIUS
top_z = front[1] + p.TUBE_RADIUS*up[1]
assert top_z <= apex - 1e-9, top_z
reach = min(p.tube_point(s, n)[0] for s in (0.0, p.TUBE_LENGTH) for n in (-p.TUBE_RADIUS, p.TUBE_RADIUS))
assert abs(reach) <= p.ROOF_SIZE/2 - 5.0, reach
assert p.ARM_THICK == 4.0 and p.ARM_INNER_X == 5.0
assert p.ARM_INNER_X + p.ARM_THICK < p.SLIT_WIDTH/2
air = p.SLIT_WIDTH/2 - (p.ARM_INNER_X + p.ARM_THICK)
assert math.isclose(air, 6.0, abs_tol=1e-9), air
assert p.ARM_INNER_X < p.TUBE_RADIUS
assert p.ARM_RISE > p.TUBE_RADIUS
for y, z in p.arm_profile()[:2]:
    assert p.PIER_Y[0] <= y <= p.PIER_Y[1] and z == p.PIER_TOP
assert p.PIER_TOP > drum_top - p.RING_WIDTH
assert p.PIER_Y[0] < p.TUBE_BACK[1] < p.PIER_Y[1]
assert all(abs(y) < p.DRUM_RADIUS for y in p.PIER_Y)

# ---- counters: one disc, two identical raised faces, kings by stacking -------
assert (p.COUNTER_DIAMETER, p.COUNTER_HEIGHT, p.COUNTER_CHAMFER) == (20.0, 7.0, 1.0)
assert p.FACE_DIAMETER == 18.0 and p.RIM_WIDTH == 2.0 and p.FIELD_DIAMETER == 14.0
assert p.FIELD_DEPTH == 1.5 and p.SYMBOL_DIAMETER == 12.5
assert math.isclose(p.SYMBOL_CLEAR, 0.75, abs_tol=1e-9)
assert math.isclose(p.WEB, 4.0, abs_tol=1e-9)
assert p.ISLAND_BEVEL == 0.3
assert 2*p.COUNTER_HEIGHT == 14.0

assert math.isclose(p.SUN_RAY_INNER, 4.25, abs_tol=1e-9)
assert math.isclose(p.SUN_RAY_OUTER, 6.25, abs_tol=1e-9)
assert p.SUN_RAY_COUNT == 8 and p.SUN_RAY_GAP == 1.0
assert p.SUN_RAY_TIP_WIDTH > p.SUN_RAY_INNER_WIDTH
assert (p.SUN_RAY_INNER_WIDTH, p.SUN_RAY_TIP_WIDTH) == (1.8, 2.2)
corner = math.atan2(p.SUN_RAY_TIP_WIDTH/2, p.SUN_RAY_OUTER)
assert 2*corner < math.radians(360/p.SUN_RAY_COUNT)
assert p.SUN_BALL_DIAMETER/2 + p.SUN_RAY_GAP == p.SUN_RAY_INNER

R, r, d = p.MOON_OUTER_DIAMETER/2, p.MOON_BITE_DIAMETER/2, p.MOON_BITE_OFFSET
assert r < R
cross_x = (d*d + R*R - r*r)/(2*d)
cross_y = math.sqrt(R*R - cross_x*cross_x)
assert math.isclose(cross_x, 2.78, abs_tol=0.01), cross_x
assert math.isclose(cross_y, 5.60, abs_tol=0.01), cross_y
assert math.isclose(2*cross_y, 11.20, abs_tol=0.02)
assert math.isclose(R + d - r, 3.50, abs_tol=1e-9)
lens = (R*R*math.acos((d*d + R*R - r*r)/(2*d*R)) + r*r*math.acos((d*d + r*r - R*R)/(2*d*r))
        - 0.5*math.sqrt((-d+r+R)*(d+r-R)*(d-r+R)*(d+r+R)))
survives = (math.pi*R*R - lens)/(math.pi*R*R)
assert math.isclose(survives, 0.38, abs_tol=0.01), survives
wrap = 360 - 2*math.degrees(math.atan2(cross_y, cross_x))
assert math.isclose(wrap, 233.0, abs_tol=1.0), wrap


def waist(deg):
    t = math.radians(deg)
    return R - (d*math.cos(t) + math.sqrt(r*r - (d*math.sin(t))**2))


for deg, want in ((150, 3.30), (120, 2.65), (100, 1.90)):
    assert math.isclose(waist(deg), want, abs_tol=0.02), (deg, waist(deg))
assert R <= p.SYMBOL_DIAMETER/2 + 1e-9
import numpy as np
from shapely.geometry import Polygon as ShPolygon
_wire = p.moon_symbol().faces()[0].outer_wire()
_poly = ShPolygon([(v.X, v.Y) for v in (_wire @ (i/4000) for i in range(4000))])
_pts = np.asarray(_poly.exterior.coords)
_tip = _pts[_pts[:, 1] > 2.0][np.argmax(_pts[_pts[:, 1] > 2.0][:, 0])]
built_wrap = 360 - 2*math.degrees(math.atan2(_tip[1], _tip[0]))
built_area = p.moon_symbol().area/(math.pi*R*R)
nose = 2*p.MOON_TIP_FILLET*math.cos(math.radians(27.1/2))
assert p.MOON_TIP_FILLET > 0
assert _tip[0] >= 1.0, _tip
assert built_wrap >= 200.0, built_wrap
assert 0.355 <= built_area <= 0.390, built_area
assert nose >= 2*0.4, nose
assert nose > 2*p.ISLAND_BEVEL, nose

for _forked in (False, True):
    _a = p.build_counter(_forked)
    _b = Pos(0, 0, p.COUNTER_HEIGHT)*Rot(X=180)*p.build_counter(_forked)
    _residue = (_a - _b).volume + (_b - _a).volume
    assert _residue < 1e-6 * _a.volume, (_forked, _residue, _a.volume)

# ======================================================= BUILT: roof (section A)
# Everything below reads part_roof.step, not the source that made it.
roof_step = CAD/'part_roof.step'
assert roof_step.exists(), 'part_roof.step has not been built'
roof = import_step(roof_step)
roof_volume = roof.volume

# A1. THE SYMMETRY GATE. This is the test that would have caught the shipped
# defect: both yoke arms were displaced by exactly ARM_THICK, and every frame in
# the evidence set was oblique enough to hide it. Cut the roof against its own
# mirror image about x = 0 and measure what is left over.
roof_mirror = mirror(roof, about=Plane.YZ)
asym_one_way = (roof - roof_mirror).volume
asym_total = asym_one_way + (roof_mirror - roof).volume
assert asym_one_way < 1.0, f'roof is not mirror-symmetric about x=0: {asym_one_way:.3f} mm3'
assert asym_total < 1.0, f'roof is not mirror-symmetric about x=0: {asym_total:.3f} mm3'
report['roof_volume_mm3'] = round(roof_volume, 1)
report['roof_asymmetric_volume_mm3'] = round(asym_one_way, 4)
report['roof_asymmetric_percent'] = round(100*asym_one_way/roof_volume, 4)

# A2. Slice the roof on a horizontal plane at three heights inside the slit and
# below the tube. Only the two yoke arms occupy the slit at these heights.
SLICE_Z = (18.0, 25.0, 32.0)
ARM_SPANS = []
for z in SLICE_Z:
    window = Pos(0, -52.5, z)*Box(2*14.99, 155.0, 0.4,
                                  align=(Align.CENTER, Align.CENTER, Align.CENTER))
    lumps = sorted((s.bounding_box().min.X, s.bounding_box().max.X)
                   for s in (roof & window).solids())
    assert len(lumps) == 2, f'z={z}: expected exactly two arm lumps inside the slit, got {lumps}'
    (a0, a1), (b0, b1) = lumps
    assert math.isclose(a0, -9.0, abs_tol=0.01) and math.isclose(a1, -5.0, abs_tol=0.01), (z, lumps)
    assert math.isclose(b0, +5.0, abs_tol=0.01) and math.isclose(b1, +9.0, abs_tol=0.01), (z, lumps)
    # clear air to each slit wall, equal on both sides; clear gap between the arms
    assert math.isclose(p.SLIT_WIDTH/2 + a0, 6.0, abs_tol=0.01)
    assert math.isclose(p.SLIT_WIDTH/2 - b1, 6.0, abs_tol=0.01)
    assert math.isclose(b0 - a1, 10.0, abs_tol=0.01)
    assert math.isclose(a1 + b0, 0.0, abs_tol=0.01)          # the gap is centred on x = 0
    ARM_SPANS.append((z, (round(a0, 4), round(a1, 4)), (round(b0, 4), round(b1, 4))))
# both arms overlap the tube's own x range and are therefore fused to it
assert p.ARM_INNER_X < p.TUBE_RADIUS
arm_tube_overlap = p.TUBE_RADIUS - p.ARM_INNER_X
assert arm_tube_overlap > 0
report['arm_spans'] = ARM_SPANS
report['arm_tube_overlap_mm'] = arm_tube_overlap

# ======================================================= BUILT: board (section B)
base_step = CAD/'part_base.step'
inlay_step = CAD/'part_inlay.step'
assert base_step.exists() and inlay_step.exists(), 'base/inlay STEP not built'
base = import_step(base_step)
inlay = import_step(inlay_step)

# B1. The inlay itself: 21.5 across against a 22.0 pocket, 2.0 thick, four plan
# corner chamfers of 1.0, bed-oriented.
ib = inlay.bounding_box()
assert len(inlay.solids()) == 1
assert math.isclose(ib.min.Z, 0.0, abs_tol=TOL)
assert math.isclose(ib.size.X, p.INLAY_SIZE, abs_tol=1e-6), ib.size.X
assert math.isclose(ib.size.Y, p.INLAY_SIZE, abs_tol=1e-6), ib.size.Y
assert math.isclose(ib.size.Z, p.INLAY_THICK, abs_tol=1e-6), ib.size.Z
expect_area = p.INLAY_SIZE**2 - 4*0.5*p.INLAY_CHAMFER**2
assert math.isclose(inlay.volume, expect_area*p.INLAY_THICK, rel_tol=1e-9), inlay.volume
assert math.isclose(p.INLAY_CLEARANCE, 0.25, abs_tol=1e-9)
assert math.isclose(p.POCKET_SIZE, 22.0, abs_tol=1e-9)

# B2. SEAT: the inlay top must contain a 20.0 mm circle, so a counter seats flat
# on it and never bridges a chamfer. Measured as a boolean, not as arithmetic.
seat_cylinder = extrude(p.Circle(p.COUNTER_DIAMETER/2), amount=p.INLAY_THICK)
spill = seat_cylinder - inlay
assert spill.volume < 1e-6, f'the inlay top does not contain a 20.0 mm circle: {spill.volume}'
chamfer_line = (p.INLAY_SIZE - p.INLAY_CHAMFER)/math.sqrt(2)
assert chamfer_line > p.COUNTER_DIAMETER/2, chamfer_line
report['seat'] = {'inlay_flat_half_width_mm': p.INLAY_SIZE/2,
                  'chamfer_line_from_centre_mm': round(chamfer_line, 4),
                  'counter_radius_mm': p.COUNTER_DIAMETER/2}

# B3. Exactly 32 pockets, one per dark cell, at the centres the board grid
# defines, each with the 22.0 chamfered plan mouth and nothing else voided.
# Compared as a boolean residue against the exact expected void at mid-depth.
dark = p.dark_cells()
assert len(dark) == 32 and all((c + r) % 2 == 0 for c, r in dark)
assert sum(1 for c, r in dark if r == 0 and c == 0) == 1        # a1 is dark
assert not any(c == 7 and r == 0 for c, r in dark)              # h1 is light
mid_z = p.BACKING + p.POCKET_DEPTH/2
slab = Pos(0, 0, mid_z)*Box(p.BOARD, p.BOARD, 0.4,
                            align=(Align.CENTER, Align.CENTER, Align.CENTER))
expected = None
for c, r in dark:
    x, y = p.cell_centre(c, r)
    prism = Pos(x, y, p.BACKING)*extrude(p.chamfered_square(p.POCKET_SIZE, p.INLAY_CHAMFER),
                                         amount=p.POCKET_DEPTH)
    expected = prism if expected is None else expected + prism
expected_void = expected & slab
actual_void = slab - base
residue = (actual_void - expected_void).volume + (expected_void - actual_void).volume
assert residue < 1e-4, f'board void at z={mid_z} does not match 32 chamfered pockets: {residue}'
report['pocket_void_residue_mm3'] = round(residue, 6)

# B4. Every pocket is BLIND with continuous backing, and every pocket floor and
# board floor is where the fit layer says. Measured with a probe column per cell.
floor_z, pocket_floor_z = set(), set()
for r in range(p.ROWS):
    for c in range(p.ROWS):
        x, y = p.cell_centre(c, r)
        column = Pos(x, y, 0)*Box(1.0, 1.0, p.HEIGHT, align=(Align.CENTER, Align.CENTER, Align.MIN))
        void = column - base
        top_of_solid = void.bounding_box().min.Z
        (pocket_floor_z if (c + r) % 2 == 0 else floor_z).add(round(top_of_solid, 6))
assert floor_z == {p.FLOOR}, floor_z
assert pocket_floor_z == {p.BACKING}, pocket_floor_z
backing = min(pocket_floor_z)
assert backing >= 2.4, backing
below = Pos(0, 0, 0)*Box(p.BOARD, p.BOARD, p.BACKING, align=(Align.CENTER, Align.CENTER, Align.MIN))
assert (below - base).volume < 1e-6, 'the backing under the board is not continuous'
depth = p.FLOOR - backing
assert math.isclose(depth, p.POCKET_DEPTH, abs_tol=1e-6), depth
flush_error = abs((backing + ib.size.Z) - p.FLOOR)
assert flush_error <= 0.05, flush_error
report['fit_layer'] = {'pocket_opening_mm': p.POCKET_SIZE, 'inlay_mm': round(ib.size.X, 4),
                       'clearance_per_side_mm': round((p.POCKET_SIZE - ib.size.X)/2, 4),
                       'pocket_depth_mm': round(depth, 6),
                       'inlay_thickness_mm': round(ib.size.Z, 6),
                       'backing_floor_mm': round(backing, 6),
                       'flush_error_mm': round(flush_error, 6)}

# B5. BRIDGE: at each diagonal junction two chamfered pocket corners face each
# other. Measured on the built base at mid-pocket depth, across the junction.
junction = (p.cell_centre(0, 0)[0] + p.CELL/2, p.cell_centre(0, 0)[1] + p.CELL/2)
PROBE_W, PROBE_H = 0.02, 0.2
probe = Pos(junction[0], junction[1], mid_z)*Rot(Z=45)*Box(
    6.0, PROBE_W, PROBE_H, align=(Align.CENTER, Align.CENTER, Align.CENTER))
# The probe crosses the junction along the bridge's own direction, so the
# intersection is an exact PROBE_W x PROBE_H prism whose length is the bridge.
bridge = (base & probe).volume/(PROBE_W*PROBE_H)
assert math.isclose(bridge, p.BRIDGE, abs_tol=0.01), (bridge, p.BRIDGE)
assert bridge >= 2*0.4, bridge          # two extrusion widths at a 0.4 mm nozzle
report['bridge_mm'] = round(bridge, 4)
report['bridge_disclosed_below_3mm_rule'] = bridge < 3.0

# B6. The base tessellates to a closed, manifold, consistently wound mesh.
verts, tris = base.tessellate(0.02)
keyed = {}
index = []
for v in verts:
    key = (round(v.X, 6), round(v.Y, 6), round(v.Z, 6))
    index.append(keyed.setdefault(key, len(keyed)))
edges = {}
for a, b, c in tris:
    ia, ib_, ic = index[a], index[b], index[c]
    if len({ia, ib_, ic}) < 3:
        continue                        # degenerate triangle carries no edge
    for u, v in ((ia, ib_), (ib_, ic), (ic, ia)):
        edges[(u, v)] = edges.get((u, v), 0) + 1
bad_direction = [e for e, n in edges.items() if n != 1]
open_edges = [e for e in edges if (e[1], e[0]) not in edges]
assert not bad_direction, f'base mesh is non-manifold: {len(bad_direction)} repeated directed edges'
assert not open_edges, f'base mesh is not closed: {len(open_edges)} boundary edges'
report['base_mesh'] = {'triangles': len(tris), 'vertices': len(keyed),
                       'closed': True, 'manifold': True}

# B7. VOID: the inlays finish flush, so the storage void is untouched. Measured
# on the built base: board floor to the top of the roof-seat ledges.
ledge_x = p.OPENING/2 - p.LEDGE_DEPTH/2
ledge_column = Pos(ledge_x, ledge_x, 0)*Box(1.0, 1.0, p.HEIGHT,
                                            align=(Align.CENTER, Align.CENTER, Align.MIN))
ledge_top = round((ledge_column - base).bounding_box().min.Z, 6)
assert ledge_top == p.LEDGE_TOP, ledge_top
sill_column = Pos(0, p.BASE/2 - p.WALL/2, 0)*Box(1.0, 1.0, p.HEIGHT,
                                                 align=(Align.CENTER, Align.CENTER, Align.MIN))
sill_top = round((sill_column - base).bounding_box().min.Z, 6)
assert sill_top == p.SILL_TOP, sill_top
counter_h = import_step(CAD/'part_sun_counter.step').bounding_box().size.Z
void = ledge_top - p.FLOOR
assert math.isclose(void, 10.0, abs_tol=1e-6), void
assert math.isclose(counter_h, 7.0, abs_tol=1e-6), counter_h
assert math.isclose(void - counter_h, 3.0, abs_tol=1e-6)
assert math.isclose(ledge_top - sill_top, reveal, abs_tol=1e-6)
report['void'] = {'floor_z': p.FLOOR, 'ledge_top_z': ledge_top, 'void_mm': round(void, 6),
                  'counter_mm': round(counter_h, 6), 'clear_mm': round(void - counter_h, 6)}

# ---- part keys, print entries and the delivered package ----------------------
keys = ['base', 'roof'] + [f'inlay_{i:02d}' for i in range(1, 33)] + \
       [f'single_{i:02d}' for i in range(1, 13)] + [f'forked_{i:02d}' for i in range(1, 13)]
assert len(keys) == 58 and len(set(keys)) == 58
expected_entries = {'part_base.step.py', 'part_roof.step.py', 'part_inlay.step.py',
                    'part_sun_counter.step.py', 'part_moon_counter.step.py'}
assert {x.name for x in CAD.glob('part_*.step.py')} == expected_entries

package = PRODUCT/'assembled.step.json'
if package.exists():
    occurrences = json.loads(package.read_text())['occurrences']
    assert [o['name'] for o in occurrences] == keys, 'delivered occurrence names/order moved'
    placed = {}
    for occurrence in occurrences:
        if occurrence['name'].startswith('inlay_'):
            t = occurrence['transform']
            placed[occurrence['name']] = (round(t[3], 6), round(t[7], 6), round(t[11], 6))
    assert len(placed) == 32
    want = {f'inlay_{n:02d}': (p.cell_centre(c, r)[0], p.cell_centre(c, r)[1], p.BACKING)
            for n, (c, r) in enumerate(dark, start=1)}
    assert placed == want, 'inlays are not seated at the dark-cell centres'
    report['delivered_occurrences'] = len(occurrences)

(CAD/'measure/fit-audit.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')

print(
    f"PASS: frozen counters unchanged (sun {FROZEN['part_sun_counter.step'][:12]}, "
    f"moon {FROZEN['part_moon_counter.step'][:12]}); BUILT roof mirror-symmetric about x=0 at "
    f"{asym_one_way:.4f} mm3 of {roof_volume:.1f} mm3 ({100*asym_one_way/roof_volume:.4f} %), "
    f"yoke arms measured at x -9.000..-5.000 and +5.000..+9.000 on slices z="
    f"{', '.join(str(z) for z in SLICE_Z)}, {air:.1f} mm of clear air to each slit wall and a "
    f"{10.0:.1f} mm gap centred on x=0, each arm overlapping the tube by {arm_tube_overlap:.1f} mm; "
    f"BUILT board fit layer: 32 blind pockets {p.POCKET_SIZE:.1f} mm deep {depth:.1f} mm on "
    f"{backing:.1f} mm of continuous backing, {ib.size.X:.1f} mm inlays at "
    f"{(p.POCKET_SIZE-ib.size.X)/2:.2f} mm per side finishing flush within {flush_error:.3f} mm, "
    f"inlay top containing a {p.COUNTER_DIAMETER:.1f} mm circle ({chamfer_line:.2f} mm chamfer line "
    f"against a {p.COUNTER_DIAMETER/2:.2f} mm radius), diagonal bridge {bridge:.3f} mm, base mesh "
    f"closed and manifold ({len(tris)} triangles); storage void {void:.1f} mm against a "
    f"{counter_h:.1f} mm counter = {void-counter_h:.1f} mm clear, perimeter reveal {reveal:.1f} mm; "
    f"exact hemisphere {2*p.DOME_BASE_RADIUS:.0f} mm across with apex z{p.LEDGE_TOP + apex:.1f} "
    f"closed, telescope muzzle {clearance:.2f} mm clear of the dome; crescent {100*built_area:.1f} % "
    f"of its outer disc, {built_wrap:.0f} deg of wrap, tips at x=+{_tip[0]:.2f}, "
    f"{p.MOON_TIP_FILLET} mm noses ({nose:.2f} mm across); counters stack to "
    f"{2*p.COUNTER_HEIGHT:.1f} mm (boolean residue {_residue:.2e} mm3); 58 part keys, five print "
    f"entries. Assembly order: seat the 32 inlays, populate the board, lower the loose roof onto "
    f"the integral ledges; reverse for play. Kings are crowned by stacking a second counter of the "
    f"same colour.")
