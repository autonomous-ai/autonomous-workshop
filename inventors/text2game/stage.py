#!/usr/bin/env python3
"""The game SET UP to play, not the parts laid out to look at.

    ./stage.py out/<slug>              # -> renders/staged.png
    ./stage.py out/<slug> --spin 8     # 8 frames around the table

`assembled.stl` holds every part at whatever coordinate the build agent left it
at, which is an assembly reference and not a picture of play. coach-party
2026-08-20: four street tiles never clipped into a square, four huts in a row
beside them instead of mounted on them, the coach parked off on its own. The
coherence lens read that render and returned 3/10 - "the four grey quadrants do
not close into a square, the teal huts trail away in a loose row" - and it was
right about every word.

howto_anim.py already knew this ("a peg has to be somewhere a player would put
it") and solved it by hard-coding overcommit's part ids, so nothing else could
use it. This is the same idea with the layout pulled out into data:

    out/<slug>/stage.json
    {"items": [{"part": "street_tile", "at": [-75, -75, 0]},
               {"part": "through_hut", "at": [-75, -115, 8], "rot": 0},
               ...]}

`at` is the part's FOOTPRINT CENTRE and its BASE - x and y are centred, z is the
bottom face - because that is how a person describes putting a piece down. `rot`
is degrees about Z, `tilt` degrees about X for anything that stands up or bolts
onto a vertical face. Coordinates are millimetres in the same frame as the
components' target_bbox_mm, so the numbers in `## Setup` translate directly.

Colours come from part_colors.json, exactly as the assembled render does, so a
staged frame and a lens frame can never disagree about what colour anything is.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                              # noqa: E402
from mpl_toolkits.mplot3d.art3d import Poly3DCollection      # noqa: E402
import numpy as np                                           # noqa: E402
import trimesh                                               # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_assembly as ra                                 # noqa: E402

GREY = "#9AA5B1"
VIEW = (48, -62)          # low enough to read the huts' walls and the coach
FACE_CAP = 60000


def mesh_for(out_dir: Path, pid: str):
    """One clean mesh per design id, from the FE export.

    fe_parts/ holds exactly one file per DESIGN - assembled_parts/ holds one per
    INSTANCE, at assembly coordinates, which is the thing this file exists to
    ignore.
    """
    f = out_dir / "fe_parts" / f"{pid}.stl"
    if not f.is_file():
        return None
    m = trimesh.load(f, force="mesh")
    return ra.decimate(m, FACE_CAP) if m.faces.shape[0] > FACE_CAP else m


def place(m, at, rot_deg=0.0, tilt_deg=0.0):
    """Copy of `m` tilted about X, turned about Z, then moved so `at` is its
    footprint centre and its base. Never mutates the cached mesh.

    `tilt` exists because not every part sits flat on a table: precedent's court
    is a VERTICAL slab and four of its nine gates bolt into sockets on that
    face. With Z-rotation alone they lie down like tiles on the floor, which is
    a picture of a machine nobody receives - and the whole point of staging from
    the rules is to stop drawing those.
    """
    m = m.copy()
    if tilt_deg:
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(tilt_deg), (1, 0, 0)))
    if rot_deg:
        m.apply_transform(trimesh.transformations.rotation_matrix(
            np.radians(rot_deg), (0, 0, 1)))
    lo, hi = m.bounds
    m.apply_translation([at[0] - (lo[0] + hi[0]) / 2,
                         at[1] - (lo[1] + hi[1]) / 2,
                         at[2] - lo[2]])
    return m


def overlaps(placed: list, slack: float = 0.5) -> list:
    """Pairs of placed pieces whose boxes interpenetrate. [(id_a, id_b), ...]

    Two printed parts cannot occupy the same space, so a staged frame that puts
    them there is a picture of something nobody can build - the exact defect
    the QA judge rejects generated video for. It rejected a frame of MINE for
    it on 2026-08-21: four visitor pawns placed inside a hut's footprint, which
    read as "pawns stacked on the hut's roof slope". The judge counted three to
    four; the boxes said four. My eye said the frame was fine.

    `slack` forgives a touching face - pieces are MEANT to sit against each
    other - and catches anything that actually goes through.
    """
    bad = []
    for i, (pid_a, ma) in enumerate(placed):
        a = ma.bounds
        for pid_b, mb in placed[i + 1:]:
            b = mb.bounds
            if all(a[0][k] < b[1][k] - slack and b[0][k] < a[1][k] - slack
                   for k in range(3)):
                bad.append((pid_a, pid_b))
    return bad


def staged(out_dir: Path) -> list:
    """[(part_id, mesh, colour)] for every item in stage.json."""
    f = out_dir / "stage.json"
    if not f.is_file():
        raise SystemExit(f"no {f} - nothing says how this game is set up")
    spec = json.loads(f.read_text(encoding="utf-8"))
    colours = ra.part_colours(out_dir)
    cache, out, missing_mesh, missing_colour = {}, [], set(), set()
    for it in spec.get("items", []):
        pid = it["part"]
        if pid not in cache:
            cache[pid] = mesh_for(out_dir, pid)
        if cache[pid] is None:
            missing_mesh.add(pid)
            continue
        if pid not in colours:
            missing_colour.add(pid)
        out.append((pid, place(cache[pid], it["at"], it.get("rot", 0),
                               it.get("tilt", 0)),
                    colours.get(pid, GREY)))
    # Both of these are the "palette did not survive" failure wearing a
    # different hat, so neither gets to be silent.
    if missing_mesh:
        print(f"  WARNING: no fe_parts mesh for {sorted(missing_mesh)} - "
              f"NOT DRAWN, the staged frame is incomplete", flush=True)
    if missing_colour:
        print(f"  WARNING: no colour for {sorted(missing_colour)} - drawn grey",
              flush=True)
    clash = overlaps([(pid, m) for pid, m, _ in out])
    if clash:
        pairs = ", ".join(f"{a}/{b}" for a, b in clash[:6])
        print(f"  WARNING: {len(clash)} pair(s) of parts INTERPENETRATE - "
              f"{pairs}{' ...' if len(clash) > 6 else ''}. Two printed parts "
              f"cannot share space; this frame shows something nobody can "
              f"build.", flush=True)
    return out


def draw(ax, parts, elev, azim):
    allv = np.vstack([m.vertices for _, m, _ in parts])
    lo, hi = allv.min(axis=0), allv.max(axis=0)
    mid, span = (lo + hi) / 2, (hi - lo).max() / 2 * 0.58

    # Painter's order, computed here rather than left to mplot3d. It depth-sorts
    # whole COLLECTIONS by their mean z, so a 150mm street tile averages nearer
    # the camera than the 16mm pawn standing on top of it and gets painted over
    # it. Measured: 13 of 14 pawns vanished under the tiles while their meshes
    # sat at exactly the right coordinates - the staging was right and the
    # drawing threw it away.
    e, a = np.radians(elev), np.radians(azim)
    eye = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])
    order = sorted(range(len(parts)),
                   key=lambda i: float(parts[i][1].vertices.mean(axis=0) @ eye))

    for z, i in enumerate(order):
        _, m, colour = parts[i]
        n = m.face_normals @ np.array([0.35, 0.45, 0.82])
        shade = 0.62 + 0.38 * np.clip(n, 0, 1)
        rgb = np.array([int(colour[j:j + 2], 16) / 255 for j in (1, 3, 5)])
        pc = Poly3DCollection(m.vertices[m.faces],
                              facecolors=shade[:, None] * rgb,
                              linewidths=0, alpha=1.0)
        # Pin the whole collection's depth to the value computed above, so
        # mplot3d sorts each PART as a unit instead of re-deriving a mean that
        # puts a wide flat tile in front of what is standing on it.
        pc.set_sort_zpos(z)
        pc.set_zorder(z + 1)
        ax.add_collection3d(pc)
    ax.set_xlim(mid[0] - span, mid[0] + span)
    ax.set_ylim(mid[1] - span, mid[1] + span)
    # The table is the floor of the shot: sit the box on the bottom of the
    # z range instead of centring it, or half the frame is empty air.
    ax.set_zlim(lo[2] - span * 0.15, lo[2] + span * 1.85)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def render(out_dir: Path, spin: int = 0) -> Path:
    parts = staged(out_dir)
    if not parts:
        raise SystemExit("stage.json produced nothing to draw")
    dst_dir = out_dir / "renders"
    dst_dir.mkdir(exist_ok=True)
    if spin:
        for i in range(spin):
            fig = plt.figure(figsize=(16, 9), facecolor="#12151A")
            ax = fig.add_subplot(111, projection="3d", facecolor="#12151A")
            draw(ax, parts, VIEW[0], VIEW[1] + 360 * i / spin)
            fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
            fig.savefig(dst_dir / f"staged_{i:02d}.png", dpi=90,
                        facecolor="#12151A")
            plt.close(fig)
        print(f"  {len(parts)} pieces -> {dst_dir}/staged_*.png ({spin} frames)",
              flush=True)
        return dst_dir / "staged_00.png"
    fig = plt.figure(figsize=(16, 9), facecolor="#12151A")
    ax = fig.add_subplot(111, projection="3d", facecolor="#12151A")
    draw(ax, parts, *VIEW)
    dst = dst_dir / "staged.png"
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.savefig(dst, dpi=90, facecolor="#12151A")
    plt.close(fig)
    print(f"  {len(parts)} pieces -> {dst}", flush=True)
    return dst


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    n = 0
    if "--spin" in sys.argv:
        n = int(sys.argv[sys.argv.index("--spin") + 1])
    render(Path(sys.argv[1]).resolve(), n)
