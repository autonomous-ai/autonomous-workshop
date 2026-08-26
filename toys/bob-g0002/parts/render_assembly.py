"""Offscreen colour render of the Re-Pin (g0002) assembly.

The cad skill renders nothing and this box has no trimesh/pyrender, so this is a
small numpy z-buffer rasteriser: tessellate every child of the assembly
compound, colour it from ``repin_lib.part_colors()``, project, and shade.

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



def _mesh(shape):
    """(vertices, faces) for one shape.

    build123d's tessellate() trips over a null triangulation in this OCP build,
    so mesh through the same StlAPI writer the skill's exporter uses and read
    the binary STL back.
    """
    import tempfile

    from OCP.BRepMesh import BRepMesh_IncrementalMesh
    from OCP.StlAPI import StlAPI_Writer

    BRepMesh_IncrementalMesh(shape.wrapped, 0.08, False, 0.3, True)
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as fh:
        path = fh.name
    w = StlAPI_Writer()
    w.ASCIIMode = False
    if not w.Write(shape.wrapped, path):
        raise RuntimeError("StlAPI_Writer failed")
    raw = open(path, "rb").read()
    os.unlink(path)
    n = int.from_bytes(raw[80:84], "little")
    rec = np.frombuffer(raw, dtype=np.uint8, count=50 * n, offset=84).reshape(n, 50)
    tri = rec[:, 12:48].copy().view("<f4").reshape(n, 3, 3).astype(np.float64)
    return tri.reshape(-1, 3), np.arange(3 * n, dtype=np.int64).reshape(n, 3)


def collect():
    """(vertices, faces, per-face rgb) for the whole assembly, in CAD coords."""
    import importlib.util

    import repin_lib as lib

    if PARTS:
        V, F, C = [], [], []
        colors = lib.part_colors()
        dx = 0.0
        for path in PARTS:
            spec = importlib.util.spec_from_file_location("part_entry", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            shape = mod.gen_step()
            pid = os.path.basename(path)[5:-8]
            rgb = _hex(colors.get(pid, colors.get("gp1", "#9aa0a8")))
            bb = shape.bounding_box()
            shape = lib.Pos(dx - bb.min.X, 0, 0) * shape
            dx += (bb.max.X - bb.min.X) + 20.0
            verts, tris = _mesh(shape)
            off = sum(len(v) for v in V)
            V.append(verts)
            F.append(tris + off)
            C.append(np.repeat(rgb[None, :], len(tris), axis=0))
        return np.vstack(V), np.vstack(F), np.vstack(C)

    spec = importlib.util.spec_from_file_location(
        "repin_entry", os.path.join(_HERE, "repin.step.py"))
    entry = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(entry)
    asm = entry.gen_step()
    colors = lib.part_colors()
    for i in range(1, 8):
        colors[f"slug_01_{i}"] = colors["slug_01"]
        colors[f"peg_01_{i}"] = colors["peg_01"]

    V, F, C = [], [], []
    for child in asm.children:
        rgb = _hex(colors.get(child.label, "#9aa0a8"))
        verts, t = _mesh(child)
        off = sum(len(v) for v in V)
        V.append(verts)
        t = t + off
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


PARTS = []


def main():
    global PARTS
    ap = argparse.ArgumentParser()
    ap.add_argument("--views", action="store_true")
    ap.add_argument("--parts", nargs="*", default=[])
    ap.add_argument("--out", default="renders/assembled.png")
    args = ap.parse_args()
    PARTS = args.parts

    V, F, C = collect()
    print(f"{len(F)} triangles, {len(V)} vertices")
    render(V, F, C, az=228.0, el=26.0, path=args.out)
    if args.views:
        for name, az, el in (("front", 270.0, 4.0),
                             ("lane", 200.0, 10.0),
                             ("top", 270.0, 88.0)):
            render(V, F, C, az, el, w=1400, h=900,
                   path=f"renders/assembled_{name}.png")


if __name__ == "__main__":
    main()
