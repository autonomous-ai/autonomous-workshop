"""Racer Mecha v2 numbers and Stage 3d checks (design-a-toy). Calculates; never draws or builds CAD.

Assembly frame = Display Pose (robot): X toward the figure's left, front is -Y, Z up from the desk.
Every part is a list of boxes / X-cylinders / cuts in the robot pose. Every move of the v2
transformation is a rotation about an axis parallel to X or a translation in Y-Z, so every
check runs on Y-Z sections taken at X planes.

The car is the robot lying on its back: car front is +Z (nose), car top is -Y (cockpit),
the ground is the plane through the lowest wheel points (+Y side).

    uv run --with shapely --with numpy python model.py > checks.txt
"""
import math, itertools
from shapely.geometry import box as sbox, Point
from shapely.affinity import rotate, translate
from shapely.ops import unary_union

CLR = 0.5

def B(x0, x1, y0, y1, z0, z1):
    return [("box", x0, x1, y0, y1, z0, z1)]

def CX(x0, x1, y, z, r):
    return [("cylx", x0, x1, y, z, r)]

def CUT(x0, x1, y0, y1, z0, z1):
    return [("cut", x0, x1, y0, y1, z0, z1)]

def CUTX(x0, x1, y, z, r):
    return [("cutx", x0, x1, y, z, r)]

def M(prims):  # mirror about X = 0
    return [(p[0], -p[2], -p[1]) + tuple(p[3:]) for p in prims]

def sym(prims):
    return prims + M(prims)

P = {}
# ---- torso (v3, drawn from the approved livery robot): 57 wide core, shoulder towers jutting over the arms,
#      closed red halo round the cockpit, head pocket in the top, nose hinge at the top of the back
P["torso"] = (B(-28.5, 28.5, -13, 13, 117, 190)
              + sym(B(28.5, 33.9, -13, 13, 164.5, 195) + B(33.9, 36, -13, 13, 171.5, 195)
                    + B(36, 40, -13, 13, 174.1, 195) + B(40, 43, -13, 13, 179.2, 195))   # shoulder towers: 52 degree wedge underside over the arms
              + sym(CX(28.5, 33.5, -2, 160, 5))                           # shoulder bosses
              + sym(CX(10.5, 14.5, 14, 192, 3.5)) + sym(B(10.5, 14.5, 10.5, 14, 186, 192))   # nose hinge cheeks
              + sym(B(11, 15, -20, -13, 132, 179)) + B(-15, 15, -20, -13, 132, 137)
              + B(-15, 15, -20, -13, 174, 179)                            # halo: a closed loop on the chest
              + CUT(-10, 10, -13, -9.5, 138, 173)                         # cockpit opening, 3.5 deep
              + CUT(-10.5, 10.5, -8, 9, 166, 190) + CUT(-6.5, 6.5, -13, -8, 180, 190)   # head pocket and neck notch
              + CUTX(-10.5, 10.5, 14, 192, 4.0)                           # seat round the nose knuckle
              + CUT(-4.5, 4.5, -1, 8, 135.5, 166)                         # neck bore
              + sym(CUT(8.5, 19.5, -9, 5, 117, 126)))                     # hip slots
P["head"] = B(-9.5, 9.5, -7.5, 8.5, 188, 207) + B(-4, 4, -0.5, 7.5, 158, 188)
# ---- nose: hinged at the top of the back (Y 14, Z 192), lying down the back, front wing behind the thighs
P["nose"] = (CX(-10, 10, 14, 192, 3.5)
             + B(-10, 10, 13.5, 21, 182, 189)                             # root block under the knuckle
             + B(-9, 9, 13.5, 27, 141, 182) + B(-6, 6, 13.5, 24, 119, 141)   # cone, stepped taper
             + B(-6, 6, 17, 21, 112, 119)                                 # cone tip, overlapping the wing's upper half
             + B(-42, 42, 21, 27, 106, 119)                               # front wing plate
             + sym(B(39, 42, 18, 27, 106, 119)))                          # wing endplates
# ---- arm shell: one white sleeve from the shoulder to the wrist, top rounded about the shoulder axis
P["arm-shell#1"] = (B(34, 62, -13, 9, 109, 160) + CX(34, 62, -2, 160, 11)
                    + CUT(36.5, 59.5, -10.5, 9, 109, 152))
P["forearm#1"] = B(37, 59, -9.5, 5.5, 85, 116) + CX(37, 59, -2, 116, 7.5)
# ---- thigh: a sleeve open at the bottom; the shin's post slides 16 up into it
P["thigh#1"] = (B(5.5, 28, -13, 9, 90, 112.5) + B(5.5, 28, -10, 6, 112.5, 115)
                + B(9, 19, -5.7, 1.7, 115, 120) + CX(9, 19, -2, 120, 3.7)
                + CUT(8, 25.5, -10.5, 6.5, 90, 112.5))
# ---- shin: flared cuff, block, top post with the knee-slide dowel, knee guard in front of the post, ankle tongue below
P["shin#1"] = (B(3, 34.5, -13, 9, 26.5, 45) + B(3.5, 31.5, -13, 9, 45, 73.5) + B(8.5, 25, -10, 6, 73.5, 96)
               + B(5.5, 28, -15, -13.5, 73.5, 89.5) + CX(31.5, 34.5, 2, 63, 4)
               + B(14, 28, -0.25, 7.75, 12.25, 26.5) + CX(14, 28, 3.75, 12.25, 4))
# ---- boot: long foot set outboard of the shin, toe 17 ahead of the shin; slot for the ankle tongue
P["boot#1"] = (B(11, 43, -30, 3.75, 0, 26) + B(11, 43, 3.75, 11.5, 0, 12.25)
               + CX(11, 43, 3.75, 12.25, 7.75)                            # heel top rounded R7.75 about the ankle
               + B(11, 14.5, -30, -26.5, 26, 33) + CX(11, 14.5, -26.5, 29.5, 3.5)
               + B(39.5, 43, -30, -26.5, 26, 33) + CX(39.5, 43, -26.5, 29.5, 3.5)   # wing-hinge lugs
               + CUT(14.5, 39.5, -30, -13.5, 25.5, 26) + CUT(11, 43, -23, -13.5, 25.5, 26)   # instep 0.5 under the wing
               + CUT(13.5, 28.5, -0.75, 12, 7.75, 26.5))                  # tongue slot
# ---- rear wing half: knuckle between the toe lugs, plate on the instep, blade overhanging inboard to the centre line
P["wing#1"] = (CX(15, 39, -26.5, 29.5, 3.5) + B(15, 39, -26.5, -14, 26, 29)
               + B(0.75, 43, -17, -14, 26, 36))
P["front-wheel#1"] = CX(43.5, 59.5, 3, 189, 16)
P["rear-wheel#1"] = CX(35, 47, 2, 63, 17)

for n in list(P):
    if n.endswith("#1"):
        P[n[:-2] + "#2"] = M(P[n])

def section(prims, x):
    polys, cuts = [], []
    for p in prims:
        if p[1] <= x <= p[2]:
            if p[0] == "box": polys.append(sbox(p[3], p[5], p[4], p[6]))
            elif p[0] == "cylx": polys.append(Point(p[3], p[4]).buffer(p[5], 48))
            elif p[0] == "cut": cuts.append(sbox(p[3], p[5], p[4], p[6]))
            elif p[0] == "cutx": cuts.append(Point(p[3], p[4]).buffer(p[5], 48))
    return unary_union(polys).difference(unary_union(cuts))

def xr(prims):
    s = [p for p in prims if not p[0].startswith("cut")]
    return min(p[1] for p in s), max(p[2] for p in s)

# ---- the transformation, robot -> car; ("t", (dy, dz)), ("r", (y, z), deg), ("rA"/"rB", None, deg)
ANKLE = (3.75, 12.25)
HINGE_A = (-26.5, 29.5)     # boot frame, robot pose
SLIDE = 16
STAGES = [
    ("head down 22", {"head": [("t", (0, -22))]}),
    ("nose flips 180 over the top", {"nose": [("r", (14, 192), 180)]}),
    ("forearms fold 180 into the shells", {f"forearm{s}": [("r", (-2, 116), 180)] for s in ("#1", "#2")}),
    ("boots fold 90 at the ankles", {f"{p}{s}": [("r", ANKLE, 90)] for s in ("#1", "#2") for p in ("boot", "wing")}),
    ("shins slide 16 up into the thighs", {f"{p}{s}": [("t", (0, SLIDE))] for s in ("#1", "#2") for p in ("shin", "boot", "wing", "rear-wheel")}),
    ("rear-wing halves stand 90 on hinge A", {f"wing{s}": [("rA", None, 90)] for s in ("#1", "#2")}),
]

def rot_pt(pt, origin, deg):
    a = math.radians(deg); y, z = pt[0] - origin[0], pt[1] - origin[1]
    return (origin[0] + y * math.cos(a) - z * math.sin(a), origin[1] + y * math.sin(a) + z * math.cos(a))

def hinge_points():
    """Hinge A in assembly coordinates once the boot has folded and slid."""
    a = rot_pt(HINGE_A, ANKLE, 90); return (a[0], a[1] + SLIDE)

def apply(g, op, f):
    kind, arg = op[0], op[1]
    if kind == "t": return translate(g, arg[0] * f, arg[1] * f)
    if kind == "r": return rotate(g, op[2] * f, origin=arg)
    return rotate(g, op[2] * f, origin=hinge_points())

def at(name, x, stage, f):
    g = section(P[name], x)
    if g.is_empty: return g
    for i, (_, moves) in enumerate(STAGES):
        if i > stage: break
        for op in moves.get(name, []):
            g = apply(g, op, 1.0 if i < stage else f)
    return g

def gap(a, b, x, stage, f):
    sa, sb = at(a, x, stage, f), at(b, x, stage, f)
    if sa.is_empty or sb.is_empty: return None
    ov = sa.intersection(sb).area
    return -ov if ov > 1e-6 else sa.distance(sb)

def pair_gap(a, b, stage, f, n=11):
    lo = max(xr(P[a])[0], xr(P[b])[0]); hi = min(xr(P[a])[1], xr(P[b])[1])
    if lo > hi: return None
    best = None
    for i in range(n):
        g = gap(a, b, lo + (hi - lo) * i / (n - 1), stage, f)
        if g is not None and (best is None or g < best): best = g
    return best

# Pairs joined by a pin or a slide; their running clearances are reported separately
JOINED = {frozenset(p) for p in [
    ("torso", "nose"), ("torso", "head"), ("thigh#1", "shin#1"), ("thigh#2", "shin#2"), ("shin#1", "boot#1"), ("shin#2", "boot#2"),
    ("boot#1", "wing#1"), ("boot#2", "wing#2"),
    ("torso", "thigh#1"), ("torso", "thigh#2"), ("torso", "arm-shell#1"), ("torso", "arm-shell#2"),
    ("arm-shell#1", "forearm#1"), ("arm-shell#2", "forearm#2"), ("torso", "front-wheel#1"), ("torso", "front-wheel#2"),
    ("shin#1", "rear-wheel#1"), ("shin#2", "rear-wheel#2")]}

def report_sweeps(steps=12):
    names = list(P)
    print("Transformation sweeps, robot to car, stage by stage; worst gap mm (<0 = overlap area); joined pairs listed below")
    for i, (label, moves) in enumerate(STAGES):
        worst = (1e9, "", "", 0)
        for k in range(steps + 1):
            f = k / steps
            for a in moves:
                for b in names:
                    if b == a or (b in moves and b < a) or frozenset((a, b)) in JOINED: continue
                    g = pair_gap(a, b, i, f, 7)
                    if g is not None and g < worst[0]: worst = (g, a, b, round(f * 100))
        print(f"  {i + 1}. {label:36s} worst {worst[0]:6.2f}  {worst[1]} vs {worst[2]} at {worst[3]}%")

def report_joined():
    print("Joined pairs: worst gap over every stage (a pin or slide contact by design shows as about 0)")
    for pr in sorted(JOINED, key=sorted):
        a, b = sorted(pr)
        worst = 1e9
        for i in range(len(STAGES)):
            for f in (0, 0.25, 0.5, 0.75, 1):
                g = pair_gap(a, b, i, f, 9)
                if g is not None: worst = min(worst, g)
        print(f"  {a:14s} / {b:14s} {worst:6.2f}")

def report_static():
    print("Display Pose: unjoined pairs closer than 0.5")
    for a, b in itertools.combinations(list(P), 2):
        if frozenset((a, b)) in JOINED: continue
        g = pair_gap(a, b, 0, 0)
        if g is not None and g < CLR: print(f"  {a} / {b}: {g:.2f}")

def report_car():
    last = len(STAGES) - 1
    print("Car pose: unjoined pairs closer than 0.5")
    for a, b in itertools.combinations(list(P), 2):
        if frozenset((a, b)) in JOINED: continue
        g = pair_gap(a, b, last, 1)
        if g is not None and g < CLR: print(f"  {a} / {b}: {g:.2f}")
    print("Car on the ground (car down is +Y; ground = lowest wheel point):")
    low, ymin, zmin, zmax = {}, 1e9, 1e9, -1e9
    for n in P:
        lo, hi = xr(P[n]); bs = [at(n, lo + (hi - lo) * i / 12, last, 1).bounds for i in range(13)]
        bs = [b for b in bs if b]
        low[n] = max(b[2] for b in bs); ymin = min(ymin, min(b[0] for b in bs))
        zmin = min(zmin, min(b[1] for b in bs)); zmax = max(zmax, max(b[3] for b in bs))
    ground = max(low[w] for w in P if "wheel" in w)
    for n, v in sorted(low.items(), key=lambda kv: -kv[1]):
        print(f"  {n:14s} lowest Y {v:6.2f}  clearance {ground - v:5.2f}")
    print(f"  car length along Z {zmin:.1f} .. {zmax:.1f} = {zmax - zmin:.1f}; height {ground - ymin:.1f} (top Y {ymin:.1f})")
    a = hinge_points()
    print(f"  hinge A in the car at Y {a[0]:.2f}, Z {a[1]:.2f}")

def report_posing():
    print("Posing sweeps from the Display Pose (0.5 needed)")
    leg = ["thigh#1", "shin#1", "boot#1", "wing#1", "rear-wheel#1"]
    tests = [("shoulder#1 forward 90", ["arm-shell#1", "forearm#1"], (-2, 160), -90),
             ("shoulder#1 back 5", ["arm-shell#1", "forearm#1"], (-2, 160), 5),
             ("hip#1 forward 20", leg, (-2, 120), -20),
             ("hip#1 back 20", leg, (-2, 120), 20)]
    for label, group, ax, deg in tests:
        worst = (1e9, "")
        for k in range(13):
            f = k / 12
            for o in P:
                if o in group: continue
                for gname in group:
                    if frozenset((o, gname)) in JOINED: continue
                    lo = max(xr(P[gname])[0], xr(P[o])[0]); hi = min(xr(P[gname])[1], xr(P[o])[1])
                    if lo > hi: continue
                    for i in range(7):
                        x = lo + (hi - lo) * i / 6
                        sa = rotate(section(P[gname], x), deg * f, origin=ax); sb = section(P[o], x)
                        if sa.is_empty or sb.is_empty: continue
                        ov = sa.intersection(sb).area; g = -ov if ov > 1e-6 else sa.distance(sb)
                        if g < worst[0]: worst = (g, f"{gname} vs {o}")
        print(f"  {label:22s} worst {worst[0]:6.2f}  {worst[1]}")

def report_balance():
    cy = m = 0
    for n in P:
        lo, hi = xr(P[n])
        for i in range(12):
            s = section(P[n], lo + (hi - lo) * (i + 0.5) / 12)
            if not s.is_empty:
                a = s.area * (hi - lo) / 12; m += a; cy += a * s.centroid.x
    print(f"Robot balance: centre of mass Y {cy / m:.1f}; boots stand on Y -30 (toe) .. 11.5 (heel)")

if __name__ == "__main__":
    report_static()
    report_sweeps()
    report_car()
    report_joined()
    report_posing()
    report_balance()
