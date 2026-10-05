#!/usr/bin/env python
"""Content-hashed, parallel cache for expensive per-body builds.

A generator that builds many independent bodies (a station-stack sculpt, a set
of lofted segments, a plate of inlays) pays for every one of them on every
`gen`, one after another, even when only one body changed. Where each body is a
pure function of a small, nameable set of inputs, keep the result instead:

    from cadcache import cached_map

    built = cached_map(
        "features.bodies:build_body",   # module:function, importable from root
        roles,                          # one string per body
        root=PROJECT_DIR,
        inputs=lambda role: repr(TABLES[role]),   # the data this body reads
        sources=[bodies_lib.__file__],            # code it reads besides func's module
    )
    shape, meta = built["head"]

Each result lands in `<root>/.cache/cadcache/<function>/` under a hash of the
function's module source, every file in `sources`, `inputs(item)`, the item,
and the OCP and Python versions. A body whose key exists loads from a binary
BREP (exact doubles, no tessellation) in about a second. The missing ones are
built at the same time, one subprocess each, up to `jobs` (default: all cores
but two), then loaded.

The key is the whole contract. Nothing is keyed on a timestamp or on a file
merely being present, so an edited table or builder cannot return a stale body
- but a dependency left out of `inputs` and `sources` can. Put every file and
every parameter the function reads into the key, or do not cache it. Deleting
`.cache/` rebuilds everything; deleting `__cadgen__/` does not touch it.

`func(item)` returns a shape, or `(shape, meta)` where `meta` is JSON-able
(for example the lobes a builder had to fall back on). Side effects in the
worker process are lost; carry whatever the caller needs back in `meta`.
Results come back as `{item: (shape, meta)}`, meta `None` when there was none.

Parallel bodies are one run, not several: they share one `gen` and one
project, so the "one machine, one CAD run" rule still holds. Each worker is a
full process with its own kernel, so memory is jobs x one body's build.

Importing it: every launcher in `skills/cad/scripts/` puts this directory on
`sys.path`, as for `cadfits`.

Self-check (builds synthetic boxes in a temporary directory):

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/cadcache.py"
"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable, Iterable


def default_jobs() -> int:
    return int(os.environ.get("CADCACHE_JOBS", max(1, (os.cpu_count() or 2) - 2)))


def _module_file(func: str, root: Path) -> Path:
    module = func.split(":", 1)[0]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return Path(importlib.import_module(module).__file__)


def _kernel_version() -> str:
    try:
        import OCP
        # Workshop #102: a body cached from a parallel-Boolean build is not
        # reused by a serial one.
        return getattr(OCP, "__version__", "?") + "+serial-booleans"
    except ImportError:
        return "none"


def cache_key(func: str, item: str, *, root: Path, inputs: Callable[[str], str | bytes],
              sources: Iterable[str | os.PathLike] = ()) -> str:
    h = hashlib.sha256(f"{func}\0{item}\0{_kernel_version()}\0{sys.version_info[:2]}".encode())
    for path in [_module_file(func, root), *sorted(Path(s) for s in sources)]:
        h.update(Path(path).read_bytes())
    data = inputs(item)
    h.update(data if isinstance(data, bytes) else str(data).encode())
    return h.hexdigest()[:16]


def _paths(cache: Path, item: str, key: str) -> tuple[Path, Path]:
    stem = cache / f"{item}-{key}"
    return stem.with_suffix(".brep"), stem.with_suffix(".json")


def _save(shape, meta, brep: Path, record: Path) -> None:
    from OCP.BinTools import BinTools

    brep.parent.mkdir(parents=True, exist_ok=True)
    for old in brep.parent.glob(f"{brep.stem.rsplit('-', 1)[0]}-*"):
        if old.stem.rsplit("-", 1)[0] == brep.stem.rsplit("-", 1)[0]:
            old.unlink()
    record.write_text(json.dumps({"meta": meta}))
    tmp = brep.with_suffix(".tmp")
    BinTools.Write_s(getattr(shape, "wrapped", shape), str(tmp))
    os.replace(tmp, brep)   # the .brep lands last: an entry is cached only once both files are whole


def _load(brep: Path, record: Path):
    """A solid comes back a Solid and anything else a Compound (build123d's `Shape.cast` returns
    None for a compound read from a file)."""
    from build123d import Compound, Solid
    from OCP.BinTools import BinTools
    from OCP.TopAbs import TopAbs_COMPOUND, TopAbs_SOLID
    from OCP.TopoDS import TopoDS, TopoDS_Shape

    shape = TopoDS_Shape()
    if not BinTools.Read_s(shape, str(brep)) or shape.IsNull():
        raise RuntimeError(f"[cadcache] unreadable cache entry {brep}")
    if shape.ShapeType() == TopAbs_SOLID:
        loaded = Solid(TopoDS.Solid_s(shape))
    elif shape.ShapeType() == TopAbs_COMPOUND:
        loaded = Compound(TopoDS.Compound_s(shape))
    else:
        from OCP.BRep import BRep_Builder
        from OCP.TopoDS import TopoDS_Compound
        wrapper, builder = TopoDS_Compound(), BRep_Builder()
        builder.MakeCompound(wrapper)
        builder.Add(wrapper, shape)
        loaded = Compound(wrapper)
    return loaded, json.loads(record.read_text())["meta"]


def _build(root: Path, func: str, item: str, brep: Path, record: Path) -> str | None:
    """Build one item in its own process; the error text if it failed."""
    run = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(root), func,
                          item, str(brep), str(record)], cwd=root, capture_output=True, text=True)
    if run.returncode or not brep.exists():
        return f"{item}: exit {run.returncode}\n{run.stderr[-4000:]}"
    return None


def cached_map(func: str, items: Iterable[str], *, root: str | os.PathLike,
               inputs: Callable[[str], str | bytes], sources: Iterable[str | os.PathLike] = (),
               jobs: int | None = None) -> dict:
    """{item: (shape, meta)}: cached results loaded, the missing ones built in parallel first."""
    root = Path(root).resolve()
    items, sources = list(items), list(sources)
    cache = root / ".cache" / "cadcache" / func.replace(":", ".")
    paths = {i: _paths(cache, i, cache_key(func, i, root=root, inputs=inputs, sources=sources))
             for i in items}
    missing = [i for i in items if not paths[i][0].exists()]
    if missing:
        n = max(1, min(jobs or default_jobs(), len(missing)))
        print(f"[cadcache] {func}: building {len(missing)} of {len(items)} ({n} at a time): "
              f"{' '.join(missing)}", file=sys.stderr, flush=True)
        with ThreadPoolExecutor(n) as pool:
            failed = [f for f in pool.map(lambda i: _build(root, func, i, *paths[i]), missing) if f]
        if failed:
            raise RuntimeError(f"[cadcache] {func}: build failed\n" + "\n".join(failed))
    return {i: _load(*paths[i]) for i in items}


def _worker(root: str, func: str, item: str, brep: str, record: str) -> None:
    # Workshop #102: a body builds with serial Booleans, as `gen` builds the
    # source that asked for it, so one item gives one B-rep.
    cadgen_src = Path(__file__).resolve().parent / "packages" / "cadgen" / "src"
    if cadgen_src.is_dir() and str(cadgen_src) not in sys.path:
        sys.path.insert(0, str(cadgen_src))
    from cadgen.booleans import serial_booleans

    serial_booleans()
    sys.path.insert(0, root)
    module, name = func.split(":", 1)
    result = getattr(importlib.import_module(module), name)(item)
    shape, meta = result if isinstance(result, tuple) else (result, None)
    _save(shape, meta, Path(brep), Path(record))


def _self_check() -> int:
    """Assertions this module has to keep. Run as a script; no test framework."""
    import tempfile

    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"{'ok  ' if ok else 'FAIL'} {label}{('  - ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    body = '''
import os, time
from build123d import Box
SIZES = {"a": 1.0, "b": 2.0, "c": 3.0}
def build(item):
    with open(os.path.join(os.path.dirname(__file__), "calls.log"), "a") as log:
        log.write(item + "\\n")
    if item == "bad":
        raise ValueError("no such body")
    with open(os.path.join(os.path.dirname(__file__), "times.log"), "a") as log:
        log.write(f"{time.time()} ")
        time.sleep(1.0)
        log.write(f"{time.time()}\\n")
    s = SIZES[item]
    return Box(s, s, s), {"size": s}
'''
    with tempfile.TemporaryDirectory(prefix="cadcache-self-check-") as tmp:
        root = Path(tmp)
        (root / "synth_bodies.py").write_text(body)
        sizes = {"a": 1.0, "b": 2.0, "c": 3.0}
        inputs = lambda i: repr(sizes[i])  # noqa: E731
        calls = lambda: (root / "calls.log").read_text().split() if (root / "calls.log").exists() else []  # noqa: E731

        out = cached_map("synth_bodies:build", "abc", root=root, inputs=inputs, jobs=3)
        check("cold run builds every item once", sorted(calls()) == ["a", "b", "c"], str(calls()))
        spans = [tuple(map(float, line.split())) for line in (root / "times.log").read_text().splitlines()]
        check("missing items build at the same time", max(s for s, _ in spans) < min(e for _, e in spans),
              f"{len(spans)} builds, last start {max(s for s, _ in spans) - min(e for _, e in spans):+.2f} s "
              "from the first end")
        check("shape round-trips exactly", abs(out["c"][0].volume - 27.0) < 1e-9, f"{out['c'][0].volume}")
        check("meta round-trips", out["b"][1] == {"size": 2.0}, str(out["b"][1]))

        cached_map("synth_bodies:build", "abc", root=root, inputs=inputs)
        check("warm run builds nothing", len(calls()) == 3, str(calls()))

        sizes["b"] = 2.0000001
        cached_map("synth_bodies:build", "abc", root=root, inputs=inputs)
        check("changed input rebuilds only that item", calls()[3:] == ["b"], str(calls()[3:]))
        check("a rebuilt item leaves one cache entry",
              len(list((root / ".cache" / "cadcache" / "synth_bodies.build").glob("b-*.brep"))) == 1)

        (root / "synth_bodies.py").write_text(body + "\n# edited\n")
        importlib.invalidate_caches()
        cached_map("synth_bodies:build", "abc", root=root, inputs=inputs)
        check("edited builder source rebuilds every item", sorted(calls()[4:]) == ["a", "b", "c"],
              str(calls()[4:]))

        sizes["bad"] = 0.0
        try:
            cached_map("synth_bodies:build", ["bad"], root=root, inputs=inputs)
        except RuntimeError as err:
            check("a failed build raises with the worker's error", "no such body" in str(err))
        else:
            check("a failed build raises with the worker's error", False, "no error raised")

    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        _worker(*sys.argv[2:7])
    else:
        raise SystemExit(_self_check())
