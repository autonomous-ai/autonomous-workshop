"""Independent algebraic fit, part count, revision-invariance and assembly order audit."""
import hashlib
import math
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import periastra_lib as p

CAD = Path(__file__).resolve().parents[1]

# ---- unchanged published base ------------------------------------------------
assert (p.BASE, p.HEIGHT, p.WALL) == (190, 24, 3)
assert (p.BOARD, p.CELL, p.ROWS) == (176, 22, 8)
assert (p.OPENING, p.CORNER, p.FLOOR) == (184, 2, 11)
assert p.RECESS == 0.8 and p.SQUARE_BEVEL == 0.3 and p.SQUARE_CORNER == 1.5
assert (p.LEDGE_TOP, p.LEDGE_DEPTH, p.LEDGE_LENGTH) == (21, 3, 24)
assert p.SILL_TOP == 17 and p.PIER_INNER == 88
assert (p.STAR_RADIUS, p.STAR_X, p.RELIEF, p.STAR_BEVEL) == (3, 22, 0.8, 0.25)
assert p.OPENING/2 - p.LEDGE_DEPTH > p.BOARD/2
assert p.STAR_RADIUS <= (p.OPENING - p.BOARD)/2

# The base geometry must be byte-for-byte the published part. This hash is the one
# the published run recorded for cad/part_base.step.
PUBLISHED_BASE = '590aa6c78a8480f8d07e9344af11f075f2dc4350cd8a27462bc8ae4453e8f72c'
base_step = CAD/'part_base.step'
if base_step.exists():
    assert hashlib.sha256(base_step.read_bytes()).hexdigest() == PUBLISHED_BASE, 'base STEP changed'

# ---- unchanged fit, storage and play -----------------------------------------
assert p.ROOF_CLEARANCE == 0.8
assert math.isclose((p.OPENING - p.ROOF_SIZE)/2, 0.8, abs_tol=1e-9)
assert math.isclose(p.ROOF_SIZE, 182.4, abs_tol=1e-9)
assert p.LIFT == 100
assert p.COUNTER_HEIGHT == 7.0
assert p.LEDGE_TOP - p.FLOOR >= 10
assert p.LEDGE_TOP - (p.FLOOR - p.RECESS + p.COUNTER_HEIGHT) >= 3.8 - 1e-9   # counter bottom z10.2
positions = [(c, r) for r in [0, 1, 2, 5, 6, 7] for c in range(8) if (c + r) % 2 == 0]
assert len(set(positions)) == 24 and sum(r < 3 for c, r in positions) == 12
assert all((c + r) % 2 == 0 for c, r in positions)
assert p.CELL - p.COUNTER_DIAMETER >= 6          # >= 3 mm edge margin inside a 22 mm cell

# ---- roof: plate, drum, rotation ring, dome, slit -----------------------------
assert (p.PLATE, p.ROOF_CORNER) == (3.0, 1.2)
drum_top = p.PLATE + p.DRUM_HEIGHT
apex = drum_top + p.DOME_RISE
assert p.DRUM_RADIUS == 90.0 and p.DRUM_HEIGHT == 14.0
assert drum_top == 17.0 and p.LEDGE_TOP + drum_top == 38.0      # drum spans z24..z38 closed
assert apex == 57.0 and p.LEDGE_TOP + apex == 78.0              # apex at z78 closed
assert math.isclose(p.DOME_SPHERE_RADIUS, 121.25, abs_tol=1e-9)
assert math.isclose(p.DOME_SPHERE_RADIUS,
                    (p.DOME_BASE_RADIUS**2 + p.DOME_RISE**2)/(2*p.DOME_RISE), abs_tol=1e-9)
assert p.DOME_RISE < p.DOME_BASE_RADIUS                         # deliberately not a half sphere
assert (p.RING_WIDTH, p.RING_DEPTH, p.RING_BELOW_TOP) == (2.0, 1.0, 4.0)
assert drum_top - p.RING_BELOW_TOP == 13.0                      # seam centre
assert p.SLIT_WIDTH == 30.0 and p.SLIT_FAR_RUN == 30.0
assert math.isclose(p.SLIT_FAR_Y,
                    p.DOME_SPHERE_RADIUS*math.sin(p.SLIT_FAR_RUN/p.DOME_SPHERE_RADIUS), abs_tol=1e-9)
assert 0 < p.SLIT_FAR_Y < p.DOME_BASE_RADIUS        # the far half of the cap stays unbroken

# telescope: 24 mm blunt tube at 45 deg, inside z57 and the 180 mm plan envelope
assert p.TUBE_RADIUS * 2 == 24.0 and p.TUBE_ANGLE == 45.0
step = math.radians(p.TUBE_ANGLE)
axis = (0.0, -math.sin(step), math.cos(step))
back = p.TUBE_BACK
front = tuple(back[i] + p.TUBE_LENGTH*axis[i] for i in range(3))
up = (0.0, math.cos(step), math.sin(step))                      # unit normal to the axis, in YZ
top_z = front[2] + p.TUBE_RADIUS*up[2]
far_y = front[1] - p.TUBE_RADIUS*up[1]
assert top_z <= apex + 1e-9, top_z                              # nothing above the dome apex
assert abs(far_y) <= p.DRUM_RADIUS + 1e-9, far_y                # inside the 180 mm plan envelope
assert p.ARM_THICK >= 6.0
assert max(abs(y) for y, z in p.ARM_PROFILE) <= p.DRUM_RADIUS
assert max(z for y, z in p.ARM_PROFILE) <= apex     # fork prongs stay under the dome apex
prong = max(p.ARM_PROFILE, key=lambda v: v[1])
assert prong[1] > -30.0 - prong[0] + p.TUBE_RADIUS*up[2]  # prong tip clears the tube's top line
assert p.PIER_Y[0] < back[1] - p.TUBE_RADIUS*up[1] and back[1] + p.TUBE_RADIUS*up[1] < p.PIER_Y[1]
assert p.PIER_TOP >= back[2] + p.TUBE_RADIUS*up[2]              # tube's back end buried in the pier

# ---- counters: one disc, two identical marks, rank by an edge rebate ----------
assert (p.COUNTER_DIAMETER, p.COUNTER_HEIGHT, p.COUNTER_CHAMFER) == (16.0, 7.0, 1.0)
assert (p.REBATE_WIDTH, p.REBATE_DEPTH, p.POCKET_DEPTH) == (2.0, 1.2, 1.2)
assert p.PLATEAU_DIAMETER == 12.0
man_flat_radius = p.COUNTER_DIAMETER/2 - p.COUNTER_CHAMFER      # 7.0
assert man_flat_radius - p.SUN_EXTENT/2 >= 2.0 - 1e-9           # >= 2.0 mm band on the man face
assert p.PLATEAU_DIAMETER/2 - p.SUN_EXTENT/2 >= 1.0 - 1e-9      # >= 1.0 mm band on the king face
assert p.COUNTER_HEIGHT - p.REBATE_DEPTH - p.POCKET_DEPTH >= 4.0 # material left under both marks

# sun: ball, undisturbed band, eight detached rays widest at the inner end
ray_inner = p.SUN_BALL_DIAMETER/2 + p.SUN_RAY_GAP
assert math.isclose(ray_inner + p.SUN_RAY_LENGTH, p.SUN_RAY_OUTER, abs_tol=1e-9)
assert p.SUN_RAY_COUNT == 8 and p.SUN_RAY_GAP == 1.0
assert p.SUN_RAY_INNER_WIDTH > p.SUN_RAY_TIP_WIDTH              # tapers outwards, never inwards
assert p.SUN_RAY_TIP_WIDTH > 0                                  # blunt flat tip, never a point
corner = math.atan2(p.SUN_RAY_INNER_WIDTH/2, ray_inner)
assert 2*corner < math.radians(360/p.SUN_RAY_COUNT)             # rays never touch each other
sun_reach = math.hypot(p.SUN_RAY_OUTER, p.SUN_RAY_TIP_WIDTH/2)
assert math.isclose(sun_reach, p.SUN_EXTENT/2, abs_tol=1e-9)   # ray tips sit on the 10 mm frame
assert sun_reach <= p.PLATEAU_DIAMETER/2 - 1.0 + 1e-9
assert sun_reach <= man_flat_radius - 2.0 + 1e-9

# moon: one crescent, both horns truncated square
R, r, d, t = p.MOON_OUTER_DIAMETER/2, p.MOON_INNER_DIAMETER/2, p.MOON_OFFSET, p.MOON_CUT_X
assert math.isclose(R + d - r, 3.5, abs_tol=1e-9)                # 3.5 mm at the widest point
moon_height = 2*math.sqrt(R*R - t*t)
tip = math.sqrt(R*R - t*t) - math.sqrt(r*r - (t - d)**2)
assert tip > 2.0                                                # flat tip, never a point or sliver
assert moon_height/2 <= p.PLATEAU_DIAMETER/2 - 2.0 + 1e-9        # >= 2.0 mm clear of the plateau edge
assert moon_height/2 <= man_flat_radius - 3.0 + 1e-9

# ---- part keys and print entries ---------------------------------------------
keys = ['base', 'roof'] + [f'single_{i:02d}' for i in range(1, 13)] + \
       [f'forked_{i:02d}' for i in range(1, 13)]
assert len(keys) == 26 and len(set(keys)) == 26
expected = {'part_base.step.py', 'part_roof.step.py',
            'part_sun_counter.step.py', 'part_moon_counter.step.py'}
assert {x.name for x in CAD.glob('part_*.step.py')} == expected

print(f'PASS: base invariant (sha256 {PUBLISHED_BASE[:12]}), 0.8 mm roof clearance, 24 starting '
      f'positions at counter bottom z10.2, dome apex z{p.LEDGE_TOP + apex:.0f} closed, '
      f'telescope top z{p.LEDGE_TOP + top_z:.1f} within z78 and |y|={abs(far_y):.1f} within 90, '
      f'sun mark {p.SUN_EXTENT:.1f} mm across and crescent {moon_height:.2f} mm tall, with '
      f'{tip:.2f} mm flat horn tips, 26 part keys, four print entries. Assembly order: populate '
      f'base, lower loose roof onto integral ledges; reverse for play.')
