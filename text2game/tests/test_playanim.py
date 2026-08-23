#!/usr/bin/env python3
"""The tween. This is the half that can silently tell a lie.

    python3 tests/test_playanim.py

The whole claim of play_anim.py is that the count is conserved by construction
and that a piece which moves is the same piece arriving somewhere. Both of
those live in tween(), so both get pinned here.
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

if "TEST_PLAYANIM_REEXEC" not in os.environ:
    try:
        import trimesh  # noqa: F401
        import matplotlib  # noqa: F401
    except ModuleNotFoundError:
        import phase2
        py = Path(phase2.RENDER_PY)
        if not py.exists():
            print(f"SKIP tests/test_playanim.py: needs trimesh and {py} is missing.")
            raise SystemExit(0)
        os.execve(str(py), [str(py), __file__] + sys.argv[1:],
                  {**os.environ, "TEST_PLAYANIM_REEXEC": "1"})

import play_anim as pa  # noqa: E402

R = []


def ok(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {detail}"))
    R.append(cond)


def item(pid, x, y, z=0, rot=0):
    return {"part": pid, "at": [x, y, z], "rot": rot}


def main() -> int:
    ok("ease is pinned at both ends",
       pa.ease(0) == 0 and pa.ease(1) == 1 and abs(pa.ease(0.5) - 0.5) < 1e-9)
    ok("ease clamps outside 0..1", pa.ease(-3) == 0 and pa.ease(9) == 1)

    a = [item("pawn", 0, 0), item("pawn", 10, 0), item("tile", 0, 0)]
    b = [item("pawn", 0, 100), item("pawn", 10, 0), item("tile", 0, 0)]

    for u in (0.0, 0.25, 0.5, 0.75, 1.0):
        mid = pa.tween(a, b, u)
        ok(f"count is conserved at u={u}", len(mid) == len(a) == 3, len(mid))

    mid = pa.tween(a, b, 0.5)
    moved = [i for i in mid if i["part"] == "pawn"]
    # The FIRST pawn is the one that moves. If the tween matched by proximity
    # it would pair the moving pawn with the stationary one and the two would
    # swap identities halfway - and on this board one specific pawn is the
    # OLDEST OCCUPANT of a hut, so swapping them is a different game.
    ok("the k-th instance tweens to the k-th, not to the nearest",
       abs(moved[0]["at"][1] - 50) < 1e-6 and abs(moved[1]["at"][1]) < 1e-6,
       [m["at"] for m in moved])
    ok("a stationary piece does not drift",
       [i for i in mid if i["part"] == "tile"][0]["at"] == [0, 0, 0])

    # Endpoints must be exact, or a piece arrives 0.3mm off and the next step
    # tweens from the wrong place.
    ok("u=1 lands exactly on the destination",
       [i["at"] for i in pa.tween(a, b, 1.0) if i["part"] == "pawn"]
       == [[0, 100, 0], [10, 0, 0]])

    # Counts that differ between steps: a piece returning to the box.
    fewer = [item("pawn", 0, 0), item("tile", 0, 0)]
    ok("a piece with no counterpart still draws until the cut",
       len(pa.tween(a, fewer, 0.5)) == 3, len(pa.tween(a, fewer, 0.5)))
    ok("and is gone once the step lands",
       len([i for i in pa.tween(a, fewer, 1.0) if i["part"] == "pawn"]) == 2)
    ok("a piece arriving from nowhere is in place, not sliding from origin",
       [i["at"] for i in pa.tween(fewer, a, 0.5) if i["part"] == "pawn"][1]
       == [10, 0, 0])

    ok("rot is interpolated too",
       abs([i for i in pa.tween([item("g", 0, 0, 0, 0)],
                                [item("g", 0, 0, 0, 90)], 0.5)][0]["rot"] - 45) < 1e-6)

    # by_part must keep authoring order, because k-th-to-k-th is only stable
    # if k means the same thing in both states.
    order = pa.by_part([item("a", 1, 0), item("b", 0, 0), item("a", 2, 0)])
    ok("by_part preserves the order pieces were written in",
       [i["at"][0] for i in order["a"]] == [1, 2], order)

    # A piece inside a closed container is not drawn - giving it coordinates
    # inside the container's SOLID mesh is what the QA gate rejected this
    # file's first output for: six pawns reading as clipped through a hut roof
    # and a coach side wall, which is the same defect the photoreal route was
    # rejected for hours earlier.
    hid = [dict(item("pawn", 0, 0), hidden=True)]
    vis = [item("pawn", 0, 100)]
    ok("hidden at both ends stays hidden",
       pa.tween(hid, hid, 0.5)[0]["hidden"] is True)
    ok("a piece leaving the container is visible the instant it moves",
       pa.tween(hid, vis, 0.01)[0]["hidden"] is False,
       pa.tween(hid, vis, 0.01)[0])
    ok("and it still tweens from inside, not from nowhere",
       0 < pa.tween(hid, vis, 0.5)[0]["at"][1] < 100,
       pa.tween(hid, vis, 0.5)[0]["at"])
    ok("a piece going back into the container is visible until it lands",
       pa.tween(vis, hid, 0.5)[0]["hidden"] is False)

    print(f"\n{sum(R)}/{len(R)} passed")
    return 0 if all(R) else 1


if __name__ == "__main__":
    sys.exit(main())
