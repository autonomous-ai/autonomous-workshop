"""Racer Mecha v4 numbers (v02 scaled to 250 tall: Y and Z x 250/207, X unchanged) and Stage 3d checks (design-a-toy). Calculates; never draws or builds CAD.

Assembly frame = Display Pose (robot): X toward the figure's left, front is -Y, Z up from the desk.
Every part is a list of boxes / X-cylinders / cuts in the robot pose. Every move of the v2
transformation is a rotation about an axis parallel to X or a translation in Y-Z, so every
check runs on Y-Z sections taken at X planes.

The car is the robot lying on its back: car front is +Z (nose), car top is -Y (cockpit),
the ground is the plane through the lowest wheel points (+Y side).

Against the v02 model this one also follows three contract numbers the v02 model lagged behind
(head post Y 0.5 to 8.5 and neck bore Y 0 to 9 from in-run amendment 1, knee guard up to the post's
top from amend-e), adds the thigh's gabled top and bevels (v4 fix) and a posing sweep of each pinned
pair itself (arm shell / torso, thigh / torso), which the v02 model skipped.

    uv run --with shapely --with numpy python model.py > checks.txt
"""
import math, itertools
from shapely.geometry import box as sbox, Point, Polygon
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
# ---- torso: 57 wide core, shoulder towers jutting over the arms (52 degree wedge underside, rise 18.5 over X 14.5),
#      closed red halo round the cockpit, head pocket in the top, nose hinge at the top of the back
P["torso"] = (B(-35, 35, -15.75, 15.75, 141.25, 229.5)                # broad-chest amendment: core 70 wide (was 57)
              + sym(B(35, 36, -15.75, 15.75, 208.3, 235.5)
                    + B(36, 40, -15.75, 15.75, 209.6, 235.5) + B(40, 43, -15.75, 15.75, 214.7, 235.5))   # towers, stepped wedge
              + sym(CX(35, 36.5, -2.5, 193.25, 7.25))                     # shoulder bosses, 1.5 proud of the side wall
              + sym(CX(10.5, 14.5, 17, 232, 4.25)) + sym(B(10.5, 14.5, 12.75, 17, 224.75, 232))   # nose hinge cheeks
              + sym(B(11, 15, -24.25, -15.75, 170, 216.25)) + B(-15, 15, -24.25, -15.75, 170, 176)
              + B(-15, 15, -24.25, -15.75, 210.25, 216.25)                # halo: a closed loop on the chest (3b: bottom bar up to Z 170)
              + CUT(-10, 10, -15.75, -11.5, 177.25, 209)                  # cockpit opening, 4.25 deep
              + CUT(-10.5, 10.5, -9.75, 10.75, 200.5, 229.5) + CUT(-6.5, 6.5, -15.75, -9.75, 217.5, 229.5)   # head pocket and neck notch
              + CUTX(-10.5, 10.5, 17, 232, 4.75)                          # seat round the nose knuckle
              + CUT(-4.5, 4.5, 0, 10.75, 163.75, 200.5)                   # neck bore
              + sym(CUT(8.5, 19.5, -11, 6, 141.25, 152.25)))              # hip slots
P["head"] = B(-9.5, 9.5, -9.25, 10.25, 227, 250) + B(-4, 4, 0.5, 10.25, 190.75, 227)
# ---- nose: hinged at the top of the back (Y 17, Z 232), lying down the back, front wing behind the thighs
P["nose"] = (CX(-10, 10, 17, 232, 4.25)
             + B(-10, 10, 16.25, 25.25, 219.75, 228.25)                   # root block under the knuckle
             + B(-9, 9, 16.25, 32.5, 170.25, 219.75) + B(-6, 6, 16.25, 29, 143.75, 170.25)   # cone, stepped taper
             + B(-6, 6, 20.5, 25.25, 135.25, 143.75)                      # cone tip, overlapping the wing's upper half
             + B(-42, 42, 25.25, 32.5, 128, 145)                          # front wing plate, 17 tall (final 3b)
             + sym(B(39, 42, 21.75, 32.5, 128, 148.5)))                   # wing endplates, stepped, rising 3.5 above the wing (3b)
# ---- arm shell: one white sleeve from the shoulder to the wrist, top rounded R13.25 about the shoulder axis
# ---- slim amendment (Stage 3b, owner: "too thick"): limb sections reduced toward the images; joints, Z numbers kept.
# ---- arm shell: one white sleeve from the shoulder to the wrist, 26 x 22, top rounded R11 about the shoulder axis
P["arm-shell#1"] = (B(37, 63, -13.5, 8.5, 131.75, 193.25) + CX(37, 63, -2.5, 193.25, 11)
                    + CUT(39.5, 60.5, -10.5, 8.5, 131.75, 183.5))
P["forearm#1"] = (B(40, 60, -10, 5, 102.75, 140) + CX(40, 60, -2.5, 140, 7.5)
                  + B(40, 60, -11.5, -10, 102.75, 120))                # curled hand 1.5 proud of the guard (fist fix)
# ---- thigh: an 18 x 19 sleeve open at the bottom; the shin's post slides 19.25 up into it. Its top over the cavity is a
#      low gable falling 20 degrees from Z 138.75 beside the tongue to 137.84 at the cavity's edges; the walls end at
#      135.75, their top outer edges bevelled 1 at 52 degrees; the cavity's ceiling edges bevelled 1.5 at 52 degrees.
#      Gable and bevels are drawn as steps lying inside them.
P["thigh#1"] = (B(7.5, 25.5, -12, 7, 108.5, 135.75)
                + B(7.5, 25.5, -9.5, 4.5, 135.75, 137.84) + B(7.5, 25.5, -8.25, 3.25, 137.84, 138.3) + B(7.5, 25.5, -7, 2, 138.3, 138.75)
                + B(9, 19, -7, 2, 138.75, 145) + CX(9, 19, -2.5, 145, 4.5)
                + CUT(7.5, 25.5, -12, -11, 134.47, 135.75) + CUT(7.5, 25.5, 6, 7, 134.47, 135.75)   # wall top bevels
                + CUT(10, 23, -9.5, 4.5, 108.5, 133.85) + CUT(10, 23, -8, 3, 133.85, 135.75))   # cavity, ceiling edges bevelled
# ---- shin: cuff 27.5 x 22, block 18 flush under the thigh (owner 2026-10-18), post 12 x 13 with the knee-slide dowel, knee guard in front of the post up to its top, ankle tongue below
P["shin#1"] = (B(7, 34.5, -12.5, 9.5, 32, 54.25) + B(7.5, 25.5, -12.5, 9.5, 54.25, 88.75) + B(10.5, 22.5, -9, 4, 88.75, 114.1) + B(10.5, 22.5, -7.5, 2.5, 114.1, 116)   # post, top edges bevelled 1.5
               + B(7.5, 25.5, -14.25, -12.5, 88.75, 116) + CX(25.5, 34.5, 2.5, 76, 4.75)
               + B(14, 28, -0.25, 9.25, 14.75, 32) + CX(14, 28, 4.5, 14.75, 4.75))
# ---- v5 boot (owner 2026-10-17, "cách 2"): a wedge as in the overall image. The rear-wing plate lies on the toe slope,
#      its hinge low at the toe; the car's rear wing keeps its height (hinge Z + plate length = 50.75).
ZH, TH = 12.0, 30.0                      # wing hinge height and the plate's slope, degrees
LP = 50.75 - ZH                          # hinge centre to the blade's back face, along the plate
_c, _s = math.cos(math.radians(TH)), math.sin(math.radians(TH))
def _w(y, z): return (y * _c - z * _s, y * _s + z * _c)      # flat wing frame -> robot pose, relative to the hinge
_zc = (32 - ZH - LP * _s) / _c           # the blade leans forward; its back face at the cuff's bottom (Z 32)
YH = -46.5                               # contract value; the blade's back face clears the cuff's front-bottom edge
YH_MAX = -12.5 - 0.5 / _c - _w(LP, _zc)[0] # the hinge furthest back that keeps 0.5 square to that face
def _H(y, z): a = _w(y, z); return (YH + a[0], ZH + a[1])
def POLY(x0, x1, pts): return [("polyx", x0, x1, tuple(pts))]
def CUTPOLY(x0, x1, pts): return [("cutpolyx", x0, x1, tuple(pts))]
# blade back face offset 0.5, up to the boot top Z 31.5
_k = (31.5 - _H(LP + 0.5, -4.75)[1]) / _c
_heel = [(4.5 + 16.75 * math.cos(math.radians(a)), 14.75 + 16.75 * math.sin(math.radians(a))) for a in range(90, 56, -4)] + [(13.75, 28.71)]
BOOT_PROFILE = ([(YH - 4.25, 0), (13.75, 0)] + _heel[::-1] + [(4.5, 31.5), _H(LP + 0.5, -4.75 + _k), _H(LP + 0.5, -4.75), _H(0, -4.75), (YH - 4.25, ZH)])
P["boot#1"] = (POLY(8, 40, BOOT_PROFILE) + CX(8, 11.5, YH, ZH, 4.25) + CX(36.5, 40, YH, ZH, 4.25)   # lugs rounded about the hinge
               + CUTX(11.5, 36.5, YH, ZH, 4.75)                                                    # knuckle clearance
               + CUT(13.5, 28.5, -0.75, 14.25, 9.5, 32))                                          # tongue slot
# ---- rear wing half: knuckle between the toe lugs, plate on the slope, blade square to the plate
P["wing#1"] = (CX(12, 36, YH, ZH, 4.25)
               + POLY(12, 36, [_H(0, -4.25), _H(LP, -4.25), _H(LP, -0.75), _H(0, -0.75)])
               + POLY(0.75, 40, [_H(LP - 3.5, -4.25), _H(LP, -4.25), _H(LP, 7.75), _H(LP - 3.5, 7.75)]))
P["front-wheel#1"] = CX(43.5, 59.5, 3.5, 228.25, 19.5)
P["rear-wheel#1"] = CX(35, 47, 2.5, 76, 20.5)

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
            elif p[0] == "polyx": polys.append(Polygon(p[3]))
            elif p[0] == "cutpolyx": cuts.append(Polygon(p[3]))
    return unary_union(polys).difference(unary_union(cuts))

def xr(prims):
    s = [p for p in prims if not p[0].startswith("cut")]
    return min(p[1] for p in s), max(p[2] for p in s)

# ---- the transformation, robot -> car; ("t", (dy, dz)), ("r", (y, z), deg), ("rA"/"rB", None, deg)
ANKLE = (4.5, 14.75)
HINGE_A = (YH, ZH)         # boot frame, robot pose
SLIDE = 19.25
HEAD = 26.5
STAGES = [
    ("head down 26.5", {"head": [("t", (0, -HEAD))]}),
    ("nose flips 180 over the top", {"nose": [("r", (17, 232), 180)]}),
    ("forearms fold 180 into the shells", {f"forearm{s}": [("r", (-2.5, 140), 180)] for s in ("#1", "#2")}),
    ("boots fold 90 at the ankles", {f"{p}{s}": [("r", ANKLE, 90)] for s in ("#1", "#2") for p in ("boot", "wing")}),
    ("shins slide 19.25 up into the thighs", {f"{p}{s}": [("t", (0, SLIDE))] for s in ("#1", "#2") for p in ("shin", "boot", "wing", "rear-wheel")}),
    ("rear-wing halves stand on hinge A", {f"wing{s}": [("rA", None, 90 - TH)] for s in ("#1", "#2")}),
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
    tests = [("shoulder#1 forward 90", ["arm-shell#1", "forearm#1"], (-2.5, 193.25), -90),
             ("shoulder#1 back 5", ["arm-shell#1", "forearm#1"], (-2.5, 193.25), 5),
             ("hip#1 forward 20", leg, (-2.5, 145), -20),
             ("hip#1 back 20", leg, (-2.5, 145), 20)]
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
    print("Posing sweeps, the pinned pair itself (0.5 needed away from the pin)")
    for label, part, ax, deg in [("shoulder#1 forward 90", "arm-shell#1", (-2.5, 193.25), -90), ("shoulder#1 back 5", "arm-shell#1", (-2.5, 193.25), 5),
                                 ("hip#1 forward 20", "thigh#1", (-2.5, 145), -20), ("hip#1 back 20", "thigh#1", (-2.5, 145), 20)]:
        worst = 1e9
        lo = max(xr(P[part])[0], xr(P["torso"])[0]); hi = min(xr(P[part])[1], xr(P["torso"])[1])
        for k in range(13):
            for i in range(23):
                x = lo + (hi - lo) * i / 22
                sa = rotate(section(P[part], x), deg * k / 12, origin=ax); sb = section(P["torso"], x)
                if sa.is_empty or sb.is_empty: continue
                ov = sa.intersection(sb).area; worst = min(worst, -ov if ov > 1e-6 else sa.distance(sb))
        print(f"  {label:22s} worst {worst:6.2f}  {part} vs torso")

def report_balance():
    cy = m = 0
    for n in P:
        lo, hi = xr(P[n])
        for i in range(12):
            s = section(P[n], lo + (hi - lo) * (i + 0.5) / 12)
            if not s.is_empty:
                a = s.area * (hi - lo) / 12; m += a; cy += a * s.centroid.x
    print(f"Robot balance: centre of mass Y {cy / m:.1f}; boots stand on Y {YH - 4.25:.2f} (toe) .. 13.75 (heel)")
    print(f"Hinge Y may be at most {YH_MAX:.2f}. Wing hinge Y {YH:.2f}, Z {ZH}; plate {LP} at {TH} deg; blade top Z {_H(LP, 7.75)[1]:.2f}, foot Z {_H(LP, -4.25)[1]:.2f}; boot length {13.75 - YH + 4.25:.2f}")

if __name__ == "__main__":
    report_static()
    report_sweeps()
    report_car()
    report_joined()
    report_posing()
    report_balance()
