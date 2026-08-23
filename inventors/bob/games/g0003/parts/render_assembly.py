"""Offscreen colour render of the CLEARANCE assembly.

The cad skill renders nothing and this box has no trimesh/pyrender, so this is a
small numpy z-buffer rasteriser: tessellate every child of the assembly
compound, colour it from ``clearance_lib.part_colors()``, project, and shade.

    $BOB_CAD_PY render_assembly.py            # renders/assembled.png
    $BOB_CAD_PY render_assembly.py --views    # + three orthogonal check views

Not a beauty pass — it exists so the build can be looked at, and so the
mid-build geometry checks (§9) have a picture to argue with.
"""

from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.normpath(
    os.path.join(_HERE, "..", "..", "..", "skills", "cad", "scripts")))

TOL = 0.25
ANG_TOL = 0.35
BG = (0.106, 0.118, 0.137)


def _hex(s: str) -> np.ndarray:
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def collect():
    """(vertices, faces, per-face rgb) for the whole assembly, in CAD coords."""
    import importlib.util

    import clearance_lib as lib

    spec = importlib.util.spec_from_file_location(
        "clearance_entry", os.path.join(_HERE, "clearance.step.py"))
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    asm = entry.gen_step()
    colors = lib.part_colors()
    colors["bar_buy_not_print"] = lib.COLORS["bar"]

    V, F, C = [], [], []
    for child in asm.children:
        rgb = _hex(colors.get(child.label, "#9aa0a8"))
        verts, tris = child.tessellate(TOL, ANG_TOL)
        off = sum(len(v) for v in V)
        V.append(np.array([(p.X, p.Y, p.Z) for p in verts], dtype=np.float64))
        t = np.array(tris, dtype=np.int64) + off
        F.append(t)
        C.append(np.repeat(rgb[None, :], len(t), axis=0))
    return np.vstack(V), np.vstack(F), np.vstack(C)


def render(V, F, C, az, el, w=1600, h=1200, path="renders/assembled.png"):
    a, e = math.radians(az), math.radians(el)
    # az/el place the CAMERA; fwd is the looking direction, so depth grows away
    # from the eye and the z-buffer keeps the nearest fragment.
    cam = np.array([math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)])
    fwd = -cam
    right = np.cross([0, 0, 1.0], fwd)
    right /= np.linalg.norm(right)
    up = np.cross(fwd, right)

    P = np.stack([V @ right, V @ up, V @ fwd], axis=1)
    lo, hi = P.min(0), P.max(0)
    ctr = (lo + hi) / 2
    P -= ctr
    span = max(hi[0] - lo[0], (hi[1] - lo[1]) * w / h) * 1.06
    s = w / span
    xs = P[:, 0] * s + w / 2
    ys = h / 2 - P[:, 1] * s
    zs = P[:, 2]

    img = np.tile(np.array(BG), (h, w, 1))
    zbuf = np.full((h, w), np.inf)

    tri = np.stack([xs[F], ys[F], zs[F]], axis=2)          # (n,3,3)
    v3 = V[F]
    n = np.cross(v3[:, 1] - v3[:, 0], v3[:, 2] - v3[:, 0])
    nl = np.linalg.norm(n, axis=1)
    ok = nl > 1e-12
    n[ok] /= nl[ok][:, None]

    # two lights, in camera space, plus a floor bounce
    key = (0.55 * right + 0.35 * up - 0.75 * fwd)
    key /= np.linalg.norm(key)
    fill = (-0.6 * right + 0.25 * up - 0.6 * fwd)
    fill /= np.linalg.norm(fill)
    lam = 0.20 + 0.62 * np.abs(n @ key) + 0.24 * np.abs(n @ fill)
    shade = np.clip(C * lam[:, None], 0, 1)

    order = np.argsort(-tri[:, :, 2].min(axis=1))           # far to near, coarse
    for i in order:
        t = tri[i]
        x0 = max(int(np.floor(t[:, 0].min())), 0)
        x1 = min(int(np.ceil(t[:, 0].max())) + 1, w)
        y0 = max(int(np.floor(t[:, 1].min())), 0)
        y1 = min(int(np.ceil(t[:, 1].max())) + 1, h)
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        d = ((t[1, 1] - t[2, 1]) * (t[0, 0] - t[2, 0])
             + (t[2, 0] - t[1, 0]) * (t[0, 1] - t[2, 1]))
        if abs(d) < 1e-9:
            continue
        l0 = ((t[1, 1] - t[2, 1]) * (gx - t[2, 0])
              + (t[2, 0] - t[1, 0]) * (gy - t[2, 1])) / d
        l1 = ((t[2, 1] - t[0, 1]) * (gx - t[2, 0])
              + (t[0, 0] - t[2, 0]) * (gy - t[2, 1])) / d
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
    print("wrote", path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", action="store_true")
    args = ap.parse_args()

    V, F, C = collect()
    print(f"{len(F)} triangles, {len(V)} vertices")
    render(V, F, C, az=228.0, el=26.0)
    if args.views:
        for name, az, el in (("front", 270.0, 4.0),
                             ("lane", 200.0, 10.0),
                             ("top", 270.0, 88.0)):
            render(V, F, C, az, el, w=1400, h=900,
                   path=f"renders/assembled_{name}.png")


if __name__ == "__main__":
    main()
