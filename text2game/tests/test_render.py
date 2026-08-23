#!/usr/bin/env python3
"""Helpers behind the renders and the how-to animation.

    uv run --python 3.12 --with trimesh --with matplotlib --with numpy \
        python3 tests/test_render.py

Not plain python3: these modules import matplotlib and trimesh, which live in
the uv environment the render scripts themselves run under, not in system
python.

Small surface, but every case here is a bug that actually shipped: a colour
lookup that silently drew the whole machine grey, and a decimation call whose
signature changed under us and killed the render outright.
"""
import importlib.machinery
import os
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

# Run under plain python3 this file died on `ModuleNotFoundError: matplotlib`,
# which in a sweep over tests/ reads exactly like a broken pipeline rather than
# the wrong interpreter. The render scripts already know which python they run
# under - phase2.RENDER_PY - so borrow it and re-exec once.
if "TEST_RENDER_REEXEC" not in os.environ:
    try:
        import matplotlib  # noqa: F401
        import trimesh  # noqa: F401
    except ModuleNotFoundError:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        import phase2
        py = Path(phase2.RENDER_PY)
        if not py.exists():
            print(f"SKIP tests/test_render.py: needs trimesh+matplotlib and "
                  f"{py} does not exist. See this file's docstring.")
            raise SystemExit(0)
        os.execve(str(py), [str(py), __file__] + sys.argv[1:],
                  {**os.environ, "TEST_RENDER_REEXEC": "1"})

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))


def load(name):
    spec = importlib.util.spec_from_loader(
        name, importlib.machinery.SourceFileLoader(name, str(HERE / f"{name}.py")))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def ok(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + ("" if cond else f"  <- {detail}"))
    return bool(cond)


class FakeMesh:
    """Just enough of a trimesh for the decimate() fallback logic."""

    def __init__(self, n, accepts):
        import numpy as np
        self.faces = np.zeros((n, 3), dtype=int)
        self.accepts = accepts
        self.calls = []

    def simplify_quadric_decimation(self, **kw):
        self.calls.append(kw)
        if set(kw) != {self.accepts}:
            raise TypeError("unexpected kwarg")
        if self.accepts == "percent" and not 0 < kw["percent"] < 1:
            raise ValueError("percent must be between 0 and 1")
        return "decimated"


def main() -> int:
    r = []
    ra = load("render_assembly")
    ha = load("howto_anim")

    print("part colour lookup accepts both key styles")
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        # publish.py re-keys this same file to <id>.stl so fe_colors can match
        # the uploaded siblings; before this fix the renderer then drew every
        # part grey and only its own warning caught it.
        (d / "part_colors.json").write_text(json.dumps(
            {"capacity_tray.stl": "#29333D", "task_hopper": "#465765",
             "bad": "not-a-colour"}))
        got = ra.part_colours(d)
        r.append(ok("suffixed key resolves", got.get("capacity_tray") == "#29333D", got))
        r.append(ok("bare key resolves", got.get("task_hopper") == "#465765", got))
        r.append(ok("non-colour dropped", "bad" not in got, got))
        r.append(ok("missing file is empty, not a crash",
                    ra.part_colours(Path(t) / "nope") == {}))

    print("\ninstance suffix is not a different part")
    for stem, base in (("bid_box_3", "bid_box"), ("capacity_tray", "capacity_tray"),
                       ("task_slug_12", "task_slug")):
        r.append(ok(stem, ra.base_name(stem) == base, ra.base_name(stem)))

    print("\ndecimate survives either trimesh signature")
    for accepts in ("face_count", "percent"):
        m = FakeMesh(50_000, accepts)
        r.append(ok(f"{accepts} build", ha.decimate(m, 4000) == "decimated", m.calls))
    m = FakeMesh(50_000, "nothing-works")
    r.append(ok("neither works -> full mesh, not a dead render",
                ha.decimate(m, 4000) is m))
    m = FakeMesh(100, "face_count")
    r.append(ok("under the cap is untouched", ha.decimate(m, 4000) is m and not m.calls))

    print("\nease() - placement, not a slide")
    r.append(ok("clamped low", ha.ease(-1) == 0.0))
    r.append(ok("clamped high", ha.ease(2) == 1.0))
    r.append(ok("midpoint", abs(ha.ease(0.5) - 0.5) < 1e-9))

    print(f"\n{sum(r)}/{len(r)} passed")
    return 0 if all(r) else 1


if __name__ == "__main__":
    sys.exit(main())
