#!/usr/bin/env python3
"""stage.py - the game set up to play.

    python3 tests/test_stage.py

Runs under the render interpreter like test_render.py; it re-execs itself if
trimesh is not importable here.
"""
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

if "TEST_STAGE_REEXEC" not in os.environ:
    try:
        import trimesh  # noqa: F401
        import matplotlib  # noqa: F401
    except ModuleNotFoundError:
        import phase2
        py = Path(phase2.RENDER_PY)
        if not py.exists():
            print(f"SKIP tests/test_stage.py: needs trimesh and {py} is missing.")
            raise SystemExit(0)
        os.execve(str(py), [str(py), __file__] + sys.argv[1:],
                  {**os.environ, "TEST_STAGE_REEXEC": "1"})

import numpy as np           # noqa: E402
import trimesh               # noqa: E402
import stage                 # noqa: E402

R = []


def ok(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {detail}"))
    R.append(cond)
    return cond


def main() -> int:
    box = trimesh.creation.box(extents=(20, 10, 6))       # centred on origin

    # `at` is the footprint CENTRE and the BASE, because that is how a person
    # describes putting a piece down: "this one goes here, on the table".
    m = stage.place(box, (100, 50, 8))
    lo, hi = m.bounds
    ok("at is the footprint centre in x and y",
       abs((lo[0] + hi[0]) / 2 - 100) < 1e-6 and abs((lo[1] + hi[1]) / 2 - 50) < 1e-6,
       m.bounds)
    ok("at is the BASE in z, not the centre", abs(lo[2] - 8) < 1e-6, lo)

    # A 90 degree turn swaps the footprint; the base stays the base.
    m = stage.place(box, (0, 0, 0), 90)
    lo, hi = m.bounds
    ok("rot turns the part about Z",
       abs((hi[0] - lo[0]) - 10) < 1e-6 and abs((hi[1] - lo[1]) - 20) < 1e-6,
       (hi - lo))
    ok("a turned part still sits on its base", abs(lo[2]) < 1e-6, lo)

    # tilt is what lets a gate bolt onto a vertical face instead of lying on it.
    m = stage.place(box, (0, 0, 0), 0, 90)
    lo, hi = m.bounds
    ok("tilt stands the part up about X",
       abs((hi[2] - lo[2]) - 10) < 1e-6 and abs((hi[1] - lo[1]) - 6) < 1e-6,
       (hi - lo))

    # place() must never mutate the cached mesh - every instance of a design
    # shares one load, and one in-place transform would drag all of them.
    before = box.bounds.copy()
    stage.place(box, (999, 999, 999), 45, 30)
    ok("place never mutates the cached mesh",
       np.allclose(box.bounds, before), box.bounds)

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "fe_parts").mkdir()
        box.export(d / "fe_parts" / "tile.stl")
        (d / "part_colors.json").write_text(
            json.dumps({"tile.stl": "#123456"}), encoding="utf-8")
        (d / "stage.json").write_text(json.dumps({"items": [
            {"part": "tile", "at": [0, 0, 0]},
            {"part": "tile", "at": [40, 0, 0], "rot": 90},
            {"part": "ghost", "at": [0, 40, 0]},          # no mesh anywhere
        ]}), encoding="utf-8")
        parts = stage.staged(d)
        ok("every item with a mesh is placed", len(parts) == 2, len(parts))
        ok("a part with no fe_parts mesh is skipped, not drawn wrong",
           all(p[0] != "ghost" for p in parts))
        ok("colours come from part_colors.json",
           all(p[2] == "#123456" for p in parts), [p[2] for p in parts])

        # Painter's order is the bug that made 13 of 14 pawns disappear: a wide
        # flat tile averages nearer the camera than the peg standing on it.
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        stage.draw(ax, parts, 34, -62)
        zs = [c.get_zorder() for c in ax.collections]
        ok("every part gets its own zorder", len(set(zs)) == len(zs), zs)
        plt.close(fig)

        (d / "stage.json").unlink()
        try:
            stage.staged(d)
            ok("no stage.json is a hard stop", False, "did not raise")
        except SystemExit:
            ok("no stage.json is a hard stop", True)

    # --- the job, and what the lens is pointed at --------------------------
    import prompts
    import importlib.machinery as _m, importlib.util as _u
    _l = _m.SourceFileLoader("t2g", str(HERE / "text2game"))
    _sp = _u.spec_from_loader("t2g", _l)
    t2g = _u.module_from_spec(_sp); _l.exec_module(t2g)
    ok("stage is a runnable job", "stage" in t2g.JOB_SPECS, sorted(t2g.JOB_SPECS))
    ok("the stage job writes stage.json",
       t2g.JOB_SPECS["stage"][0] == "stage.json", t2g.JOB_SPECS["stage"][0])

    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "gdd.md").write_text("## Setup\n1. Clip them together.\n",
                                  encoding="utf-8")
        (d / "parts_index.json").write_text(json.dumps(
            {"street_tile": {"qty": 4, "bbox": [150, 150, 8]}}), encoding="utf-8")
        (d / "art_direction.md").write_text("| `street_tile` | `#AEB8C2` |\n",
                                            encoding="utf-8")
        t = prompts.stage_layout(d)
        # The sizes are the whole reason a model can place anything: without
        # them "clip four tiles into a square" has no numbers in it.
        ok("the stager is given the measured bboxes",
           "[150, 150, 8]" in t and "street_tile" in t and "qty" in t,
           [x for x in t.splitlines() if "street_tile" in x])
        ok("the stager is told at is the base, not the centre",
           "BASE in z" in t and "z = 0 is the table" in t)

        # The lens judges the staged frame when there is one, and says so.
        (d / "renders").mkdir()
        ok("with no staged frame the lens falls back to the contact sheet",
           "renders/assembled.png" in prompts.coherence(d))
        (d / "renders" / "staged.png").write_bytes(b"x")
        c = prompts.coherence(d)
        ok("with a staged frame the lens judges THAT",
           "renders/staged.png" in c and "renders/assembled.png" not in c)

    # Two printed parts cannot share space. A staged frame that puts them there
    # is a picture of something nobody can build - and the QA judge rejected a
    # frame of MINE for exactly that on 2026-08-21, four visitor pawns placed
    # inside a hut's footprint. It counted "three to four"; the boxes said
    # four. My eye said the frame was fine.
    b = trimesh.creation.box(extents=(20, 20, 20))
    def at(x, y=0):
        return ("p", stage.place(b, (x, y, 0)))
    ok("boxes exactly touching are not a collision",
       stage.overlaps([at(0), at(20)]) == [], stage.overlaps([at(0), at(20)]))
    ok("boxes passing through each other are",
       stage.overlaps([at(0), at(10)]) == [("p", "p")])
    ok("clear of each other is clean", stage.overlaps([at(0), at(60)]) == [])
    ok("every colliding pair is reported, not just the first",
       len(stage.overlaps([at(0), at(8), at(15)])) == 3,
       stage.overlaps([at(0), at(8), at(15)]))
    ok("one piece cannot collide with itself", stage.overlaps([at(0)]) == [])
    # Stacking is legal - a pawn stands ON a tile, sharing exactly one face.
    tile = ("tile", stage.place(trimesh.creation.box(extents=(100, 100, 8)),
                                (0, 0, 0)))
    pawn = ("pawn", stage.place(b, (0, 0, 8)))
    ok("a piece resting on top of another is not a collision",
       stage.overlaps([tile, pawn]) == [], stage.overlaps([tile, pawn]))

    print(f"\n{sum(R)}/{len(R)} passed")
    return 0 if all(R) else 1


if __name__ == "__main__":
    sys.exit(main())
