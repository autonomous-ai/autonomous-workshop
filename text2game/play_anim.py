#!/usr/bin/env python3
"""A how-to video that cannot lie, because no image model is in the chain.

    ./play_anim.py out/<slug>            # -> howto_play_anim.mp4

The photoreal route was gated on 2026-08-21 and failed 3 of 3 beats. Not on
polish - on the thing each beat existed to teach. Beat 2's villager was never
spent, its hut grew no rear door and no return pan, and a visitor ended up
merged into a solid wall. Beat 1 spilled nine or ten pawns where the rules
spill five, and grew them. Beat 3 pinched the church and lifted it out of its
socket. howto_anim.py wrote that failure down a month before I repeated it:
"the clip advertised a machine nobody would receive".

So: every frame here is the printed mesh, in the locked colours, tweened
between board states written from the rules. Five pawns is five pawns because
five is how many are in the list. Nothing can breed, morph or grow.

    out/<slug>/howto_steps.json
    {"fps": 12, "steps": [
        {"caption": "...", "move": 1.2, "hold": 1.0, "items": [<stage items>]},
        ...]}

An item may carry `"hidden": true`, meaning it is inside a closed container
and therefore not drawn. That is not a trick: a pawn loaded in the coach is not
visible in real life either, and the alternative - giving it coordinates inside
the coach's SOLID mesh - is what the QA gate rejected this file's first output
for, with six pawns reading as clipped through a roof and a side wall. Exactly
the failure the photoreal route was rejected for a few hours earlier.

Each step is a COMPLETE board state in stage.json's shape. Between two steps,
the k-th instance of each part tweens from its old place to its new one, so a
piece that moves is the same piece arriving somewhere - not one vanishing and
another appearing. Instances with no counterpart simply appear or leave at the
boundary, which is what a piece returning to the box actually does.

It looks like a technical render, because it is one. That is the trade: it
cannot be mistaken for a photograph, and it cannot show you a part that does
not exist.
"""
import json
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection      # noqa: E402
import numpy as np                                           # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_assembly as ra                                 # noqa: E402
import stage                                                 # noqa: E402

FACE_CAP = 4000        # animation: silhouette is what reads, not micro-detail
VIEW = (48, -62)
SIZE = (1280, 720)
GREY = "#9AA5B1"


def ease(t: float) -> float:
    """Smoothstep. Linear reads as a slide; this reads as a placement."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def by_part(items: list) -> dict:
    """{part_id: [item, ...]} preserving the order they were written in."""
    out = {}
    for it in items:
        out.setdefault(it["part"], []).append(it)
    return out


def tween(a: list, b: list, u: float) -> list:
    """Board state u of the way from a to b, matching k-th instance to k-th.

    A piece that MOVES has to be the same piece arriving somewhere. Matching by
    position instead would let two pawns swap identities mid-slide, and on a
    board where one pawn is the oldest occupant that is a different game.
    """
    ga, gb = by_part(a), by_part(b)
    out = []
    for pid in dict.fromkeys(list(ga) + list(gb)):
        la, lb = ga.get(pid, []), gb.get(pid, [])
        for k in range(max(len(la), len(lb))):
            if k >= len(lb):                 # leaving: hold until the cut
                out.append(la[k])
                continue
            if k >= len(la):                 # arriving: in place from the cut
                out.append(lb[k])
                continue
            p, q = la[k], lb[k]
            e = ease(u)
            out.append({
                "part": pid,
                "at": [p["at"][i] + (q["at"][i] - p["at"][i]) * e
                       for i in range(3)],
                "rot": p.get("rot", 0) + (q.get("rot", 0) - p.get("rot", 0)) * e,
                "tilt": p.get("tilt", 0) + (q.get("tilt", 0) - p.get("tilt", 0)) * e,
                # Hidden only while it is hidden at BOTH ends. A piece coming
                # out of a closed container is visible from the instant it
                # starts moving, which is what coming out looks like.
                "hidden": bool(p.get("hidden")) and bool(q.get("hidden")),
            })
    return out


def meshes(out_dir: Path, ids) -> dict:
    cache = {}
    for pid in ids:
        m = stage.mesh_for(out_dir, pid)
        if m is None:
            print(f"  WARNING: no fe_parts mesh for {pid} - NOT DRAWN",
                  flush=True)
            continue
        cache[pid] = ra.decimate(m, FACE_CAP) if m.faces.shape[0] > FACE_CAP else m
    return cache


def bounds_of(steps: list, cache: dict, colours: dict):
    """One camera box for the whole clip, so nothing jumps scale between steps."""
    pts = []
    for st in steps:
        for it in st["items"]:
            if it["part"] in cache and not it.get("hidden"):
                pts.append(stage.place(cache[it["part"]], it["at"],
                                       it.get("rot", 0), it.get("tilt", 0)).bounds)
    allb = np.vstack(pts)
    return allb.min(axis=0), allb.max(axis=0)


def draw_state(ax, items, cache, colours, lo, hi):
    items = [it for it in items if not it.get("hidden")]
    parts = [(it["part"],
              stage.place(cache[it["part"]], it["at"], it.get("rot", 0),
                          it.get("tilt", 0)),
              colours.get(it["part"], GREY))
             for it in items if it["part"] in cache]
    e, a = np.radians(VIEW[0]), np.radians(VIEW[1])
    eye = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    order = sorted(range(len(parts)),
                   key=lambda i: float(parts[i][1].vertices.mean(axis=0) @ eye))
    for z, i in enumerate(order):
        _, m, colour = parts[i]
        n = m.face_normals @ np.array([0.35, 0.45, 0.82])
        shade = 0.62 + 0.38 * np.clip(n, 0, 1)
        rgb = np.array([int(colour[j:j + 2], 16) / 255 for j in (1, 3, 5)])
        pc = Poly3DCollection(m.vertices[m.faces],
                              facecolors=shade[:, None] * rgb, linewidths=0)
        pc.set_sort_zpos(z)
        pc.set_zorder(z + 1)
        ax.add_collection3d(pc)
    # Box aspect from the REAL extents, not a cube. A 300mm board 175mm tall
    # inside a cubic box spends most of the frame on empty air above it, and
    # the pawns - which are 16mm - end up too small to follow. Padding is a
    # fixed margin so the numbers stay comparable between steps.
    pad = 14.0
    mid = (lo + hi) / 2
    d = np.maximum(hi - lo, 1.0) + 2 * pad
    ax.set_xlim(mid[0] - d[0] / 2, mid[0] + d[0] / 2)
    ax.set_ylim(mid[1] - d[1] / 2, mid[1] + d[1] / 2)
    ax.set_zlim(lo[2] - pad, hi[2] + pad)
    ax.set_box_aspect((d[0], d[1], d[2]))
    ax.view_init(elev=VIEW[0], azim=VIEW[1])
    ax.set_axis_off()


def render(out_dir: Path) -> Path:
    spec_f = out_dir / "howto_steps.json"
    if not spec_f.is_file():
        raise SystemExit(f"no {spec_f} - nothing says what the steps are")
    spec = json.loads(spec_f.read_text(encoding="utf-8"))
    steps, fps = spec["steps"], int(spec.get("fps", 12))
    colours = ra.part_colours(out_dir)
    ids = {it["part"] for st in steps for it in st["items"]}
    cache = meshes(out_dir, ids)
    if not cache:
        raise SystemExit("no meshes to draw")
    for i, st in enumerate(steps):
        placed = [(it["part"],
                   stage.place(cache[it["part"]], it["at"], it.get("rot", 0),
                               it.get("tilt", 0)))
                  for it in st["items"]
                  if it["part"] in cache and not it.get("hidden")]
        clash = stage.overlaps(placed)
        if clash:
            print(f"  WARNING: step {i + 1} has {len(clash)} interpenetrating "
                  f"pair(s): {', '.join(f'{a}/{b}' for a, b in clash[:6])}",
                  flush=True)
    lo, hi = bounds_of(steps, cache, colours)

    frames = out_dir / ".anim"
    frames.mkdir(exist_ok=True)
    for f in frames.glob("*.png"):
        f.unlink()

    n, caps = 0, []
    for i, st in enumerate(steps):
        hold = int(round(float(st.get("hold", 1.0)) * fps))
        move = int(round(float(st.get("move", 1.2)) * fps)) if i else 0
        prev = steps[i - 1]["items"] if i else st["items"]
        for k in range(move):
            items = tween(prev, st["items"], (k + 1) / move)
            _one(frames, n, items, cache, colours, lo, hi); caps.append(st["caption"]); n += 1
        for _ in range(hold):
            _one(frames, n, st["items"], cache, colours, lo, hi); caps.append(st["caption"]); n += 1
        print(f"  step {i + 1}/{len(steps)}: {n} frames", flush=True)

    (frames / "captions.json").write_text(json.dumps(caps), encoding="utf-8")
    dst = out_dir / "howto_play_anim.mp4"
    _encode(frames, caps, fps, dst)
    for f in frames.glob("*.png"):
        f.unlink()
    print(f"  {n} frames, {n / fps:.1f}s -> {dst}", flush=True)
    return dst


def _one(frames: Path, n: int, items, cache, colours, lo, hi) -> None:
    fig = plt.figure(figsize=(SIZE[0] / 100, SIZE[1] / 100), dpi=100,
                     facecolor="#12151A")
    ax = fig.add_subplot(111, projection="3d", facecolor="#12151A")
    draw_state(ax, items, cache, colours, lo, hi)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(frames / f"f{n:05d}.png", facecolor="#12151A")
    plt.close(fig)


def _encode(frames: Path, caps: list, fps: int, dst: Path) -> None:
    """Frames -> mp4, with each frame's own caption burnt on.

    Per-frame rather than per-clip because the steps have different lengths and
    a drawtext enable= expression per step is a wall of escaping that breaks the
    first time a caption contains a comma.
    """
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    from PIL import Image, ImageChops, ImageDraw, ImageFont

    # Crop to what is actually drawn, ONE box across every frame so the shot
    # never jumps. mplot3d sizes its axes from the 3D extents, and coach-party's
    # extents are 419mm wide because the coach parks 120mm off the side of a
    # 300mm board - so the board itself ends up small in a 16:9 frame while
    # most of the picture is empty backdrop. This is a 2D fix for a 3D framing
    # problem and it works whatever the next game's proportions turn out to be.
    box = None
    for i in range(0, len(caps), max(1, len(caps) // 20)):
        f = frames / f"f{i:05d}.png"
        if not f.is_file():
            continue
        im = Image.open(f).convert("RGB")
        bg = Image.new("RGB", im.size, "#12151A")
        b = ImageChops.difference(im, bg).convert("L").point(
            lambda v: 255 if v > 8 else 0).getbbox()
        if b:
            box = b if box is None else (min(box[0], b[0]), min(box[1], b[1]),
                                         max(box[2], b[2]), max(box[3], b[3]))
    if box:
        pad = 24
        x0, y0, x1, y1 = box
        w, h = x1 - x0, y1 - y0
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        # Grow to 16:9 around the content, then clamp inside the frame.
        want_w = max(w + 2 * pad, (h + 2 * pad) * SIZE[0] / SIZE[1])
        want_h = want_w * SIZE[1] / SIZE[0]
        x0 = max(0, int(cx - want_w / 2)); x1 = min(SIZE[0], int(cx + want_w / 2))
        y0 = max(0, int(cy - want_h / 2)); y1 = min(SIZE[1], int(cy + want_h / 2))
        box = (x0, y0, x1, y1)

    for i, cap in enumerate(caps):
        f = frames / f"f{i:05d}.png"
        if not f.is_file():
            continue
        im = Image.open(f).convert("RGB")
        if box:
            im = im.crop(box).resize(SIZE, Image.LANCZOS)
        d = ImageDraw.Draw(im)
        size = max(16, min(30, int((SIZE[0] - 88) / (0.6 * max(len(cap), 1)))))
        try:
            fnt = ImageFont.truetype(font, size)
        except OSError:
            fnt = ImageFont.load_default()
        d.rectangle([0, im.size[1] - 84, im.size[0], im.size[1]], fill="#111417")
        w = d.textlength(cap, font=fnt)
        d.text(((im.size[0] - w) / 2, im.size[1] - 58), cap, font=fnt,
               fill="#F2EFE6")
        im.save(f)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", str(fps),
                    "-i", str(frames / "f%05d.png"), "-c:v", "libx264",
                    "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    str(dst)], check=True, timeout=1800)


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        raise SystemExit(0 if len(sys.argv) > 1 else 2)
    render(Path(sys.argv[1]).resolve())
