#!/usr/bin/env python3
"""How-to-play video animated from the REAL printed geometry.

    ./howto_anim.py out/<slug>            # writes howto_play.mp4

No image model anywhere in this chain. The i2i route was tried first and its
output could not be used: it invented faceted wall patterns the geometry does
not have and lifted loose pieces out of the hopper that is actually empty, so
the clip advertised a machine nobody would receive. Every frame here is the
exact mesh that gets printed, in the colours part_colors.json locked.

The parts are STAGED here rather than read from assembled.step, because that
file co-locates duplicates: all 12 capacity_pegs share one 10mm cube, all 6
fragment_wedges another. That is fine as an assembly reference and useless as a
picture of play - a peg has to be somewhere a player would put it.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt            # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # noqa: E402
import numpy as np                         # noqa: E402
import trimesh                             # noqa: E402

FPS = 15
FACE_CAP = 4000          # animation, not a hero still: silhouette is what reads
GREY = "#9AA5B1"


def decimate(m, cap: int):
    """trimesh changed this signature: older builds take a face COUNT, newer
    ones a reduction FRACTION and raise on anything outside 0..1. Try both, and
    keep the full mesh rather than fail the render if neither works."""
    if m.faces.shape[0] <= cap:
        return m
    for kwargs in ({"face_count": cap},
                   {"percent": max(0.01, min(0.99, cap / m.faces.shape[0]))}):
        try:
            return m.simplify_quadric_decimation(**kwargs)
        except (TypeError, ValueError):
            continue
    return m


def load_parts(out_dir: Path) -> dict:
    """One decimated instance of each printed design, moved to its own origin."""
    colours = {}
    f = out_dir / "part_colors.json"
    if f.is_file():
        colours = {re.sub(r"\.stl$", "", k): v
                   for k, v in json.loads(f.read_text(encoding="utf-8")).items()}
    out = {}
    for stl in sorted((out_dir / "fe_parts").glob("*.stl")):
        m = trimesh.load(stl, force="mesh")
        m = decimate(m, FACE_CAP)
        m.apply_translation(-m.bounds.mean(axis=0))       # centre on origin
        out[stl.stem] = {"mesh": m, "colour": colours.get(stl.stem, GREY),
                         "size": m.bounds[1] - m.bounds[0]}
    return out


def tris(part, pos, rot_deg=0.0, axis=(0, 1, 0)):
    """Triangles for one instance placed at pos, optionally rotated."""
    m = part["mesh"].copy()
    if rot_deg:
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(rot_deg), axis, [0, 0, 0]))
    m.apply_translation(np.asarray(pos, dtype=float))
    return m.vertices[m.faces], m.face_normals


def ease(t: float) -> float:
    """Smoothstep: linear motion reads as a slide, this reads as a placement."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


class Scene:
    """A staged table: every instance is (part_id, position, rotation)."""

    def __init__(self, parts: dict):
        self.p = parts
        self.items = []

    def add(self, pid, pos, rot=0.0, axis=(0, 1, 0), colour=None):
        self.items.append((pid, np.asarray(pos, float), rot, axis, colour))
        return self

    def draw(self, ax, light=np.array([0.35, 0.45, 0.82])):
        for pid, pos, rot, axis, colour in self.items:
            part = self.p[pid]
            t, n = tris(part, pos, rot, axis)
            shade = 0.62 + 0.38 * np.clip(n @ light, 0, 1)
            c = colour or part["colour"]
            rgb = np.array([int(c[j:j + 2], 16) / 255 for j in (1, 3, 5)])
            ax.add_collection3d(Poly3DCollection(
                t, facecolors=shade[:, None] * rgb, linewidths=0))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    out_dir = Path(sys.argv[1]).resolve()
    P = load_parts(out_dir)
    need = ("capacity_tray", "task_hopper", "bid_box", "capacity_peg",
            "task_slug", "fragment_wedge", "eviction_lever")
    missing = [n for n in need if n not in P]
    if missing:
        raise SystemExit(f"ABORT: missing parts {missing}")

    tray_h = P["capacity_tray"]["size"][2]
    hop_h = P["task_hopper"]["size"][2]
    peg_h = P["capacity_peg"]["size"][2]
    box_w = P["bid_box"]["size"][0]

    # Staged layout: tray flat, hopper behind it, four bid boxes along the front
    # edge where a player would actually reach them.
    # 0.62 * box_w put four 75mm boxes 46mm apart and they overlapped into one
    # purple slab. They sit on the TABLE, not on the 158mm tray, so they get
    # their real width plus a gap.
    BOX_Y = -105.0
    gap = box_w * 1.08
    boxes = [(-1.5 * gap + i * gap, BOX_Y, 16.0) for i in range(4)]
    HOP = (0.0, 34.0, tray_h / 2 + hop_h / 2 - 4)
    SOCKETS = [(-52 + i * 26, 40.0, tray_h) for i in range(5)]

    frames_dir = out_dir / "_anim"
    frames_dir.mkdir(exist_ok=True)
    for old in frames_dir.glob("*.png"):
        old.unlink()

    BEATS = [
        ("OVERCOMMIT — ca ban chung MOT co may", 2.6),
        ("1. Moi nguoi BI MAT bo 0-3 chot vao hop cua minh", 3.4),
        ("Cam ban bac con so", 1.6),
        ("2. Mot nhiem vu roi tu pheu — khong ai biet truoc", 3.0),
        ("3. Mo tat ca cung luc — cong tong so chot", 2.6),
        ("4. Vuot nguong qua tai -> don bay nghieng", 3.0),
        ("Ben nang hon bi HAT — nhung chot do MAT", 2.4),
        ("Va MOT o bi bit VINH VIEN", 3.0),
        ("May tuan sau nho hon tuan nay", 2.6),
    ]
    total = sum(d for _, d in BEATS)
    n_frames = int(total * FPS)
    print(f"  {len(BEATS)} beats, {total:.0f}s, {n_frames} frames @ {FPS}fps",
          flush=True)

    # camera: slow continuous orbit so the object always reads as 3D
    for i in range(n_frames):
        t = i / FPS
        acc, beat, bt = 0.0, BEATS[0][0], 0.0
        for text, dur in BEATS:
            if t < acc + dur:
                beat, bt = text, (t - acc) / dur
                break
            acc += dur
        b = [x[0] for x in BEATS].index(beat)

        s = Scene(P)
        s.add("capacity_tray", (0, 0, tray_h / 2))
        s.add("task_hopper", HOP)
        s.add("eviction_lever", (0, -20, tray_h + 6),
              rot=(-16 * ease((bt - 0.35) / 0.4) if b == 5 else
                   -16 if b >= 6 else 0), axis=(1, 0, 0))

        # bid boxes, and the pegs a player commits into the nearest one
        for bi, bp in enumerate(boxes):
            s.add("bid_box", bp)
        if b >= 1:
            drop = ease(bt) if b == 1 else 1.0
            for k in range(3):
                bx, by, bz = boxes[1]
                s.add("capacity_peg",
                      (bx - box_w * 0.22 + k * box_w * 0.22, by,
                       bz + 26 * (1 - drop) + peg_h))
        # the dispensed task slug
        if b >= 3:
            f = ease(bt) if b == 3 else 1.0
            s.add("task_slug", (HOP[0], HOP[1] - 34,
                                HOP[2] + hop_h / 2 - (hop_h + 20) * f))
        # the wedge that plugs a socket, forever
        if b >= 7:
            f = ease(bt) if b == 7 else 1.0
            sx, sy, sz = SOCKETS[2]
            s.add("fragment_wedge", (sx, sy, sz + 40 * (1 - f) + 11))
        if b >= 8:
            for k in (0, 1):
                sx, sy, sz = SOCKETS[k]
                s.add("fragment_wedge", (sx, sy, sz + 11))

        fig = plt.figure(figsize=(12.8, 7.2), facecolor="#12151A")
        ax = fig.add_subplot(111, projection="3d", facecolor="#12151A")
        s.draw(ax)
        # Frame the actual scene rather than a cube: four boxes spread ~245mm
        # wide while the machine is only ~190mm tall, and a 1:1:1 aspect over a
        # 300-unit cube left the object small in a field of background.
        XR, Y0, Y1, Z1 = 165.0, -165.0, 115.0, 205.0
        ax.set_xlim(-XR, XR)
        ax.set_ylim(Y0, Y1)
        ax.set_zlim(-10, Z1)
        ax.set_box_aspect((2 * XR, Y1 - Y0, Z1 + 10))
        ax.view_init(elev=24, azim=-58 + 20 * np.sin(t * 0.22))
        ax.set_axis_off()
        fig.text(0.5, 0.055, beat, ha="center", color="#E8E6E1", fontsize=19)
        fig.subplots_adjust(left=-0.06, right=1.06, top=1.12, bottom=0.02)
        fig.savefig(frames_dir / f"f{i:05d}.png", dpi=100, facecolor="#12151A")
        plt.close(fig)
        if i % 30 == 0:
            print(f"    frame {i}/{n_frames}", flush=True)

    dst = out_dir / "howto_play.mp4"
    r = subprocess.run(["ffmpeg", "-y", "-framerate", str(FPS),
                        "-i", str(frames_dir / "f%05d.png"),
                        "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", str(dst)],
                       capture_output=True, text=True, timeout=1800)
    if r.returncode != 0:
        raise SystemExit(f"ffmpeg failed: {r.stderr[-400:]}")
    print(f"  -> {dst} ({dst.stat().st_size // 1024}KB)", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
