"""Offscreen colour hero render for Metes and Bounds (STL assembly spread).

Pure numpy z-buffer rasteriser (no pyrender). Loads the built STLs from build/,
arranges them on a virtual table, and writes hero.png + a couple of check views.

    $HOME/.cadcode-venv/bin/python render_hero.py
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.normpath(os.path.join(_HERE, "..", "build"))
OUT = os.path.dirname(_HERE)

BG = (0.09, 0.10, 0.12)
TABLE = (0.35, 0.33, 0.30)


def _hex(s: str) -> np.ndarray:
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def load_stl(name: str):
    import trimesh
    m = trimesh.load(os.path.join(BUILD, name))
    # keep only the largest connected body to drop stray slivers
    bodies = m.split(only_watertight=False)
    if bodies and not isinstance(bodies, list):
        bodies = [bodies]
    bodies = sorted([b for b in bodies if len(b.faces)], key=lambda b: b.volume, reverse=True)
    big = bodies[0]
    return np.array(big.vertices, dtype=np.float64), np.array(big.faces, dtype=np.int64)


# --- transform helpers -----------------------------------------------------
def translate(V, x=0.0, y=0.0, z=0.0):
    return V + np.array([x, y, z])


def rot_z(V, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    R = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.0]])
    return V @ R.T


def flatten_on(V, target_top=0.0):
    """Project every vertex onto z=target_top (squash) for a graphic stack look."""
    V = V.copy()
    V[:, 2] = target_top
    return V


# --- accumulate ------------------------------------------------------------
def collect(load_only):
    """Returns (V, F, C) in world coords; color keyed by part family."""
    import importlib.util
    parts = {}
    parts["board"] = dict(color=0x9AA0A8, stl="survey_board_7x7.stl")
    parts["rule"] = dict(color=0xE8C779, stl="folding_rule_10seg.stl")
    parts["rail"] = dict(color=0x8FB8DE, stl="score_rail.stl")
    parts["round"] = dict(color=0xDE8FB8, stl="round_peg.stl")
    for p in range(1, 5):
        parts[f"peg{p}"] = dict(color=0x9CD39A if p < 3 else 0xF0A868, stl=f"score_peg_p{p}.stl")
    holes = {}
    # stake families
    stake_colors = {1: "E06C6C", 2: "6CA8E0", 3: "7BD389", 4: "E0D06C"}

    mesh = {}
    if load_only:
        return parts, mesh
    for name in [
        "survey_board_7x7", "folding_rule_10seg", "score_rail", "round_peg",
        "score_peg_p1", "score_peg_p2", "score_peg_p3", "score_peg_p4"]:
        mesh[name] = load_stl(f"{name}.stl")

    V, F, C = [], [], []

    def add(Vv, Ff, rgb):
        off = sum(len(v) for v in V)
        V.append(Vv)
        F.append(Ff + off)
        C.append(np.repeat(np.array(rgb, dtype=np.float64)[None, :], len(Ff), axis=0))

    # === BOARD: flat on the table, centred at origin ===
    bv, bf = mesh["survey_board_7x7"]
    # bring its top face to z=0, center on x/y
    bv = bv - bv.mean(axis=0)
    bv[:, 2] -= bv[:, 2].min()
    bv[:, 2] -= bv[:, 2].max()          # flop so top face up at z=0
    add(bv, bf, _hex("9AA0A8"))

    # === RULE: laid flat, beside the board (left), in a gentle S ===
    rv, rf = mesh["folding_rule_10seg"]
    rv = rv - rv.mean(axis=0)
    rv[:, 2] -= rv[:, 2].min()
    rv[:, 2] -= rv[:, 2].max()          # printed upside down; show top up
    rv = rot_z(rv, -8)
    rv = translate(rv, x=-128.0, y=0.0)
    add(rv, rf, _hex("E8C779"))

    # === SCORE RAIL: right side, below the board ===
    lv, lf = mesh["score_rail"]
    lv = lv - lv.mean(axis=0)
    lv[:, 2] -= lv[:, 2].min()
    lv[:, 2] -= lv[:, 2].max()
    lv = rot_z(lv, 20)
    lv = translate(lv, x=+128.0, y=-70.0)
    add(lv, lf, _hex("8FB8DE"))

    # === score pegs: little cluster next to the rail ===
    for p in range(1, 5):
        pv, pf = mesh[f"score_peg_p{p}"]
        pv = pv - pv.mean(axis=0)
        pv[:, 2] -= pv[:, 2].min()
        pv[:, 2] -= pv[:, 2].max()
        pv = translate(pv, x=+170.0 + p * 9.0, y=-18.0)
        add(pv, pf, _hex("9CD39A" if p < 3 else "F0A868"))

    # === round peg ===
    gv, gf = mesh["round_peg"]
    gv = gv - gv.mean(axis=0)
    gv[:, 2] -= gv[:, 2].min()
    gv[:, 2] -= gv[:, 2].max()
    gv = translate(gv, x=+205.0, y=-40.0)
    add(gv, gf, _hex("DE8FB8"))

    # === stakes: 4 colour groups arranged around the board ===
    import glob
    for p in range(1, 5):
        rgb = _hex(stake_colors[p])
        # six stakes for this player, fanned in a small circle near the board
        files = sorted(glob.glob(os.path.join(BUILD, f"stake_p{p}_?.stl")))
        for i, fp in enumerate(files[:6]):
            sv, sf = load_stl(os.path.basename(fp))
            sv = sv - sv.mean(axis=0)
            sv[:, 2] -= sv[:, 2].min()
            sv[:, 2] -= sv[:, 2].max()
            ang = math.radians(p * 70 + i * 60)
            r = 60.0
            x = -40.0 + r * math.cos(ang)
            y = -120.0 + r * math.sin(ang) * 0.8
            sv = translate(sv, x=x, y=y, z=0.0)
            add(sv, sf, rgb)

    return np.vstack(V), np.vstack(F), np.vstack(C)


def render(V, F, C, az, el, w=2000, h=1500, path="hero.png"):
    a, e = math.radians(az), math.radians(el)
    cam = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    fwd = -cam
    right = np.cross([0, 0, 1.0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)

    P = np.stack([V @ right, V @ up, V @ fwd], axis=1)
    extent = P.min(0), P.max(0)
    ctr = (extent[0] + extent[1]) / 2
    P -= ctr
    span = max(extent[1][0] - extent[0][0], (extent[1][1] - extent[0][1]) * w / h) * 1.12
    s = w / span
    xs = P[:, 0] * s + w / 2
    ys = h / 2 - P[:, 1] * s
    zs = P[:, 2]

    # floor: a soft ground plane under everything
    midz = ctr[2]
    floor_lo, floor_hi = P[:, 0:2].min(0), P[:, 0:2].max(0)
    pad = 0.25 * s
    img = np.tile(np.array(BG), (h, w, 1))
    # keep it simple: no floor, table colour emerges from BG shadows

    zbuf = np.full((h, w), np.inf)
    tri = np.stack([xs[F], ys[F], zs[F]], axis=2)
    v3 = V[F]
    n = np.cross(v3[:, 1] - v3[:, 0], v3[:, 2] - v3[:, 0])
    nl = np.linalg.norm(n, axis=1)
    ok = nl > 1e-12
    n[ok] /= nl[ok][:, None]

    key = (0.55 * right + 0.35 * up - 0.75 * fwd); key /= np.linalg.norm(key)
    fill = (-0.6 * right + 0.25 * up - 0.6 * fwd); fill /= np.linalg.norm(fill)
    lam = 0.20 + 0.62 * np.abs(n @ key) + 0.24 * np.abs(n @ fill)
    shade = np.clip(C * lam[:, None], 0, 1)

    order = np.argsort(-tri[:, :, 2].min(axis=1))
    for i in order:
        t = tri[i]
        x0 = max(int(np.floor(t[:, 0].min())), 0); x1 = min(int(np.ceil(t[:, 0].max())) + 1, w)
        y0 = max(int(np.floor(t[:, 1].min())), 0); y1 = min(int(np.ceil(t[:, 1].max())) + 1, h)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        d = ((t[1, 1] - t[2, 1]) * (t[0, 0] - t[2, 0]) + (t[2, 0] - t[1, 0]) * (t[0, 1] - t[2, 1]))
        if abs(d) < 1e-9:
            continue
        l0 = ((t[1, 1] - t[2, 1]) * (gx - t[2, 0]) + (t[2, 0] - t[1, 0]) * (gy - t[2, 1])) / d
        l1 = ((t[2, 1] - t[0, 1]) * (gx - t[2, 0]) + (t[0, 0] - t[2, 0]) * (gy - t[2, 1])) / d
        l2 = 1.0 - l0 - l1
        m = (l0 >= 0) & (l1 >= 0) & (l2 >= 0)
        if not m.any():
            continue
        z = l0 * t[0, 2] + l1 * t[1, 2] + l2 * t[2, 2]
        sub = zbuf[y0:y1, x0:x1]
        hit = m & (z < sub)
        if not hit.any():
            continue
        sub[hit] = z[hit]
        img[y0:y1, x0:x1][hit] = shade[i]

    import PIL.Image
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    PIL.Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(path)
    print("wrote", path, "(", len(F), "triangles )")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hero-only", action="store_true")
    args = ap.parse_args()
    V, F, C = collect(load_only=args.hero_only)
    if args.hero_only:
        print("dry run ok")
        return
    print(f"{len(F)} triangles, {len(V)} vertices")
    render(V, F, C, az=228.0, el=30.0, path=os.path.join(OUT, "render", "hero.png"))
    render(V, F, C, az=270.0, el=70.0, w=1600, h=1200, path=os.path.join(OUT, "render", "hero_top.png"))


if __name__ == "__main__":
    main()
