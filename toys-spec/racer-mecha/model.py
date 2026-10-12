"""Racer Mecha numbers and Stage 3d checks (design-a-toy). Calculates; never draws or builds CAD.

Assembly frame = Display Pose (robot): X toward the figure's left, front is -Y, Z up from the desk.
Every part is a list of boxes (x0,x1, y0,y1, z0,z1) or cylinders along X/Y in the robot pose.
Each transformation joint is a rotation about an axis parallel to X or Y, or a translation;
"car" is the car-standing pose (the car stood on its tail), reached by these moves.
Sweeps are checked by slicing every pair of parts whose X ranges overlap.

    python3 model.py            # pose tables, sweeps, clearances
"""
import math, itertools
from shapely.geometry import box as sbox, Point
from shapely.affinity import rotate, translate

CLR = 0.5  # minimum clearance between parts that move against each other

def B(x0, x1, y0, y1, z0, z1, mirror=False):
    out = [("box", x0, x1, y0, y1, z0, z1)]
    if mirror:
        out.append(("box", -x1, -x0, y0, y1, z0, z1))
    return out

def CX(x0, x1, y, z, r):  # cylinder along X
    return [("cylx", x0, x1, y, z, r)]

def CUT(x0, x1, y0, y1, z0, z1, mirror=False):  # removed material (bores, slots, cavities)
    out = [("cut", x0, x1, y0, y1, z0, z1)]
    if mirror:
        out.append(("cut", -x1, -x0, y0, y1, z0, z1))
    return out

def CUTX(x0, x1, y, z, r):
    return [("cutx", x0, x1, y, z, r)]

# ---- parts (robot pose); one side for paired parts, instance #1 is +X (figure's left) ----
P = {}
P["torso"] = (B(-26, 26, -13, 13, 99, 154) + B(-26, -10.5, -13, 13, 154, 180) + B(10.5, 26, -13, 13, 154, 180)
              + B(-10.5, 10.5, -13, -10, 154, 180) + B(-10.5, 10.5, 8, 13, 154, 180)          # pocket walls
              + B(14, 26, -13, 13, 180, 192, True)                                              # wheel towers
              + CX(26, 35, -1, 187, 4) + CX(-35, -26, -1, 187, 4)                                 # wheel stub bosses
              + CX(10.5, 16, -14, 180, 3.5) + CX(-16, -10.5, -14, 180, 3.5) + B(10.5, 16, -14, -9, 176.5, 183.5, True)                                            # nose hinge cheeks
              + B(7.5, 12, 13, 27.5, 99, 111, True)                                             # spine hinge cheeks
              + CUT(-7.5, 7.5, 9, 13.5, 99, 106)                                                # spine lane at the lower back
              + B(-9, 9, 13, 20, 125, 152)                                                      # halo over the cockpit
              + CUTX(-10.5, 10.5, -14, 180, 5.5)                                                # nose knuckle seat
              + CUT(-4.5, 4.5, -5.5, 3.5, 122, 156)                                             # neck post bore
              + CUT(6.5, 20.5, -9, 5, 99, 108, True))                                           # hip tongue slots
P["nose"] = (CX(-10, 10, -14, 180, 3.5)                                                           # knuckle
             + B(-10, 10, -33, -19, 128, 176) + B(-6, 6, -30, -19, 110, 128)                    # nose cone (stepped)
             + B(-27, 27, -21, -15, 99, 128) + B(-27, -25, -24, -14, 99, 128) + B(25, 27, -24, -14, 99, 128))
P["head"] = B(-9.5, 9.5, -8.5, 7.5, 178, 200) + B(-4, 4, -5, 3, 146, 178)                      # helmet + neck post
P["arm-shell#1"] = (B(27.5, 47.5, -13, 9, 120, 157)                                               # shell
                    + B(27.5, 47.5, -13, 9, 157, 159) + B(27.5, 47.5, -11, 7, 159, 161)
                    + B(27.5, 47.5, -9, 5, 161, 163)                                             # 45 deg chamfered top (outer staircase)
                    + B(27.5, 30, -13, 9, 118, 120) + B(45, 47.5, -13, 9, 118, 120)              # elbow cheeks
                    + CUT(30, 45, -10, 9, 118, 152.6))                                           # forearm cavity, open at the back and below
P["forearm#1"] = B(30.5, 44.5, -9.5, 5.5, 97, 124) + CX(30.5, 44.5, -2, 124, 7.5)       # knuckle rounded about the elbow pin
P["thigh#1"] = B(0.5, 27, -13, 9, 77.5, 92) + B(0.5, 27, -10, 6, 92, 95) + B(7, 20, -6, 2, 95, 102) + CX(7, 20, -2, 102, 4) + CUT(7, 20, -8.5, 4.5, 77.5, 85) + CUT(0.5, 27, 0, 9, 77.5, 87)                           # + tongue into hip slot
P["shin#1"] = B(0.5, 27, -13, 9, 27, 72) + B(0.5, 27, -9, 5, 72, 76) + B(7.5, 19.5, -6, 2, 76, 80.5) + CX(7.5, 19.5, -2, 80.5, 4) + B(0.5, 27, -13, 9, 0, 27) + B(7.5, 27, 9, 14, 0, 27) + CX(27, 35, -1, 51, 4)  # shin, boot, stub
P["spine"] = (CX(-7, 7, 22.5, 105, 6) + B(-7, 7, 22, 35.5, 105, 205)                           # knuckle + boom
              + B(-35, 35, 12, 17, 205, 221) + B(-35, -32, 10, 22, 201, 221) + B(32, 35, 10, 22, 201, 221))
P["wheel#1"] = CX(35.5, 51.5, -1, 187, 18)   # front, on the torso tower
P["wheel#3"] = CX(35.5, 51.5, -1, 51, 18)    # rear, on shin#1

def mirror_part(prims):
    out = []
    for p in prims:
        if p[0] == "box":
            out.append(("box", -p[2], -p[1]) + p[3:])
        elif p[0] == "cylx":
            out.append(("cylx", -p[2], -p[1]) + p[3:])
        elif p[0] == "cyly":
            out.append(("cyly", -p[2], -p[1], p[3], p[4], -p[5], p[6], p[7]))
        elif p[0] in ("cut", "cutx"):
            out.append((p[0], -p[2], -p[1]) + p[3:])
    return out

for a, b in [("arm-shell#1", "arm-shell#2"), ("forearm#1", "forearm#2"), ("thigh#1", "thigh#2"),
             ("shin#1", "shin#2"), ("wheel#1", "wheel#2"), ("wheel#3", "wheel#4")]:
    P[b] = mirror_part(P[a])

# ---- moves from robot pose to car-standing pose ----
# ("rx", (y, z) axis point, deg) rotates about +X;  ("ry", (x, z), deg) about +Y;  ("t", (dx, dy, dz))
MOVES = {
    "nose": ("rx", (-14, 180), -180),
    "head": ("t", (0, 0, -22)),
    "forearm#1": ("rx", (-2, 124), 180),
    "forearm#2": ("rx", (-2, 124), 180),
    "spine": ("rx", (22.5, 105), -180),
}
POSING = {  # posing ranges checked from the Display Pose
    "arm-shell#1": ("rx", (-2, 157), -90), "arm-shell#2": ("rx", (-2, 157), -90),
    "thigh#1": ("rx", (-2, 102), -20), "thigh#2": ("rx", (-2, 102), -20),
}

def section_yz(prims, x):
    """Y-Z section of a part at plane X=x (robot pose)."""
    from shapely.ops import unary_union
    polys, cuts = [], []
    for p in prims:
        if p[0] == "cut" and p[1] <= x <= p[2]:
            cuts.append(sbox(p[3], p[5], p[4], p[6]))
        elif p[0] == "cutx" and p[1] <= x <= p[2]:
            cuts.append(Point(p[3], p[4]).buffer(p[5], 32))
    for p in prims:
        if p[0] == "box" and p[1] <= x <= p[2]:
            polys.append(sbox(p[3], p[5], p[4], p[6]))
        elif p[0] == "cylx" and p[1] <= x <= p[2]:
            polys.append(Point(p[3], p[4]).buffer(p[5], 32))
        elif p[0] == "cyly" and p[1] <= x <= p[2]:
            _, x0, x1, y0, y1, cx, cz, r = p
            if abs(x - cx) <= r:
                h = math.sqrt(r * r - (x - cx) ** 2)
                polys.append(sbox(y0, cz, y1, cz + h))
    return unary_union(polys).difference(unary_union(cuts))

def section_xz(prims, y):
    from shapely.ops import unary_union
    polys, cuts = [], []
    for p in prims:
        if p[0] == "cut" and p[3] <= y <= p[4]:
            cuts.append(sbox(p[1], p[5], p[2], p[6]))
        elif p[0] == "cutx" and abs(y - p[3]) <= p[5]:
            h = math.sqrt(p[5] ** 2 - (y - p[3]) ** 2)
            cuts.append(sbox(p[1], p[4] - h, p[2], p[4] + h))
    for p in prims:
        if p[0] == "box" and p[3] <= y <= p[4]:
            polys.append(sbox(p[1], p[5], p[2], p[6]))
        elif p[0] == "cylx" and abs(y - p[3]) <= p[5]:
            h = math.sqrt(p[5] ** 2 - (y - p[3]) ** 2)
            polys.append(sbox(p[1], p[4] - h, p[2], p[4] + h))
        elif p[0] == "cyly" and p[3] <= y <= p[4]:
            polys.append(Point(p[5], p[6]).buffer(p[7], 32).intersection(sbox(p[1], p[6], p[2], p[6] + p[7])))
    return unary_union(polys).difference(unary_union(cuts))

def xr(prims):
    lo = min(p[1] for p in prims if not p[0].startswith("cut")); hi = max(p[2] for p in prims if not p[0].startswith("cut"))
    return lo, hi

def moved_yz(name, frac, x):
    s = section_yz(P[name], x)
    m = MOVES.get(name)
    if not m: return s
    if m[0] == "rx": return rotate(s, m[2] * frac, origin=m[1])
    if m[0] == "t": return translate(s, m[1][1] * frac, m[1][2] * frac)
    return s

def gap_yz(a, b, fa, fb):
    lo = max(xr(P[a])[0], xr(P[b])[0]); hi = min(xr(P[a])[1], xr(P[b])[1])
    if lo > hi: return None
    best = 1e9
    for i in range(9):
        x = lo + (hi - lo) * i / 8
        sa, sb = moved_yz(a, fa, x), moved_yz(b, fb, x)
        if sa.is_empty or sb.is_empty: continue
        best = min(best, -sb.intersection(sa).area if sa.intersects(sb) and sa.intersection(sb).area > 1e-6 else sa.distance(sb))
    return None if best == 1e9 else best

def sweep(mover, others, steps=36):
    worst = (1e9, None, None)
    for k in range(steps + 1):
        f = k / steps
        for o in others:
            if o == mover: continue
            fo = f if o in MOVES and MOVES[o][0] != "ry" and o in SIMUL.get(mover, ()) else 0
            g = gap_yz(mover, o, f, fo)
            if g is not None and g < worst[0]:
                worst = (g, o, round(f * 100))
    return worst

def sweep_y(mover, axis, deg, others, steps=36):
    """Rotation about Y: check in X-Z sections over the mover's Y range."""
    ys = [p for p in P[mover] if p[0] == "box"]
    y0 = min(p[3] for p in ys); y1 = max(p[4] for p in ys)
    worst = (1e9, None, None)
    for k in range(steps + 1):
        f = k / steps
        for o in others:
            if o == mover: continue
            for i in range(7):
                y = y0 + (y1 - y0) * i / 6
                sa = rotate(section_xz(P[mover], y), deg * f, origin=axis)  # CCW in (x, z): + swings a part below the axis toward +X
                sb = section_xz(P[o], y)
                if sa.is_empty or sb.is_empty: continue
                g = -sa.intersection(sb).area if sa.intersection(sb).area > 1e-6 else sa.distance(sb)
                if g < worst[0]: worst = (g, o, round(f * 100))
    return worst

SIMUL = {"nose": ("head",), "head": ("nose",)}

if __name__ == "__main__":
    allp = list(P)
    print("Transformation sweeps, robot pose (0%) to car-standing (100%); gap mm (<0 = overlap area)")
    for m in ["nose", "head", "spine", "forearm#1", "forearm#2"]:
        g = sweep(m, allp)
        print(f"  {m:10s} worst {g[0]:7.2f} vs {g[1]} at {g[2]}%")
    for m, deg in [("forearm#1", 90), ("forearm#2", 90)]:   # elbow posing: forearm bends forward
        MOVES["_p"] = ("rx", (-2, 124), deg); P["_p"] = P[m]
        g = sweep("_p", [o for o in allp if o != m]); del MOVES["_p"], P["_p"]
        print(f"  {m:12s} elbow forward {deg} deg worst {g[0]:7.2f} vs {g[1]} at {g[2]}%")
    print("Posing sweeps from the Display Pose")
    for m, (k, ax, deg) in POSING.items():
        side = m[-2:]
        if m.startswith("arm-shell"):
            g = None
            for d in (deg, 30):
                P["_p"] = P[m] + P["forearm" + side]; MOVES["_p"] = ("rx", ax, d)
                gg = sweep("_p", [o for o in allp if o not in (m, "forearm" + side)]); del MOVES["_p"]
                print(f"  {m:12s} shoulder {'forward' if d < 0 else 'back'} {abs(d)} deg worst {gg[0]:7.2f} vs {gg[1]}")
            del P["_p"]; continue
        else:
            wheel = "wheel#3" if side == "#1" else "wheel#4"
            P["_p"] = P[m] + P["shin" + side] + P[wheel]
            MOVES["_p"] = ("rx", ax, deg)
            g = sweep("_p", [o for o in allp if o not in (m, "shin" + side, wheel)]); del MOVES["_p"]
        del P["_p"]
        print(f"  {m:12s} {deg:+4d} deg worst {g[0]:7.2f} vs {g[1]} at {g[2]}%")
    print("Static clearances in the Display Pose (pairs closer than 0.5 that are not joined)")
    for a, b in itertools.combinations(allp, 2):
        g = gap_yz(a, b, 0, 0)
        if g is not None and g < CLR:
            print(f"  {a} / {b}: {g:.2f}")

def car_section(name, x):
    return moved_yz(name, 1.0, x)

def report_car():
    print("Car-standing pose: pairs closer than 0.5 (all moves applied)")
    for a, b in itertools.combinations(list(P), 2):
        lo = max(xr(P[a])[0], xr(P[b])[0]); hi = min(xr(P[a])[1], xr(P[b])[1])
        if lo > hi: continue
        g = 1e9
        for i in range(9):
            x = lo + (hi - lo) * i / 8
            sa, sb = car_section(a, x), car_section(b, x)
            if sa.is_empty or sb.is_empty: continue
            ov = sa.intersection(sb).area
            g = min(g, -ov if ov > 1e-6 else sa.distance(sb))
        if g < CLR: print(f"  {a} / {b}: {g:.2f}")
    print("Car on the ground (ground plane is the lowest wheel point; car 'down' is -Y):")
    low = {}
    for n in P:
        lo, hi = xr(P[n])
        ys = [car_section(n, lo + (hi - lo) * i / 12).bounds for i in range(13)]
        ys = [b[0] for b in ys if b]
        low[n] = min(ys)
    ground = min(low[w] for w in ("wheel#1", "wheel#2", "wheel#3", "wheel#4"))
    for n, v in sorted(low.items(), key=lambda kv: kv[1]):
        print(f"  {n:12s} lowest Y {v:7.2f}  clearance {v - ground:5.2f}")
    zs = []
    for n in P:
        lo, hi = xr(P[n])
        for i in range(13):
            b = car_section(n, lo + (hi - lo) * i / 12).bounds
            if b: zs += [b[1], b[3]]
    print(f"  car length along Z {min(zs):.1f} .. {max(zs):.1f} = {max(zs) - min(zs):.1f}")

def report_balance():
    vol = {}; cy = 0; M = 0
    for n in P:
        lo, hi = xr(P[n]); a = 0; m = 0
        for i in range(12):
            x = lo + (hi - lo) * (i + 0.5) / 12
            s = section_yz(P[n], x)
            if s.is_empty: continue
            a += s.area * (hi - lo) / 12; m += s.area * (hi - lo) / 12 * s.centroid.x
        M += a; cy += m
    print(f"Robot balance: centre of mass Y {cy / M:.1f}; feet stand on Y -13 .. 9 (heel to 14 outboard of the spine lane)")

if __name__ == "__main__":
    report_car(); report_balance()

if __name__ == "__main__":
    print("Leg posing sweeps")
    allp = [n for n in P]
    for side, w in (("#1", "wheel#3"), ("#2", "wheel#4")):
        P["_p"] = P["thigh" + side] + P["shin" + side] + P[w]; MOVES["_p"] = ("rx", (-2, 102), 20)
        g = sweep("_p", [o for o in allp if o not in ("thigh" + side, "shin" + side, w, "_p")])
        print(f"  hip{side} back 20 deg worst {g[0]:.2f} vs {g[1]}")
        P["_p"] = P["shin" + side] + P[w]; MOVES["_p"] = ("rx", (-2, 80.5), 45)
        g = sweep("_p", [o for o in allp if o not in ("shin" + side, w, "_p")])
        print(f"  knee{side} back 45 deg worst {g[0]:.2f} vs {g[1]}")
        del P["_p"], MOVES["_p"]
