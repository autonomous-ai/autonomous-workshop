"""Thread and job limits for every CAD tool and the processes it starts.

Stdlib only and cheap to import: every CAD entry imports it before numpy,
build123d or OCP. Unpinned, one CAD process on the 64-core Workshop host
holds about 127 threads at import (OpenBLAS and OpenMP pools, one thread
per core each) and about 30 more once OCCT meshes in parallel. Twenty such
processes at once fill the user cgroup's task limit (pids.max 9830), and
whatever else runs there, the agents among them, dies on a failed thread
start.

``pin()`` gives this process, and so every child that inherits its
environment, one BLAS/OpenMP thread and an OCCT pool of
``WORKSHOP_OCC_THREADS`` (default 1), except where the caller already set
the variable. Thread counts change no result: each tool computes the same
geometry and verdicts serially.

``default_jobs()`` is how many CAD processes a tool runs at once: the free
task headroom of this process's cgroups divided by what one job holds, at
least 1 and at most 8 (or a smaller ceiling the caller gives). A tool's
``*_JOBS`` environment variable still overrides it.
"""

from __future__ import annotations

import os
from pathlib import Path

# The variables the numeric libraries read once, when they load.
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
# OCCT's default thread pool (BRepMesh, boolean and section parallelism).
OCC_THREADS_ENV = "WORKSHOP_OCC_THREADS"
OCC_THREADS_DEFAULT = "1"
# The tasks one pinned CAD job holds, observed (ADR 0106 measurement,
# 2026-11-19): a pinned gen holds 1 thread at import and up to its OCCT
# pool while it builds; a make_round or verify_project parent holds a few
# more and its pipe readers. Rounded up for the processes a job starts.
JOB_TASKS = 16
JOBS_CEILING = 8
CGROUP_ROOT = Path("/sys/fs/cgroup")


def pin_environ(environ=None):
    """Set every thread variable the caller left unset; returns the mapping."""

    environ = os.environ if environ is None else environ
    for key, value in THREAD_ENV.items():
        environ.setdefault(key, value)
    environ.setdefault(OCC_THREADS_ENV, OCC_THREADS_DEFAULT)
    return environ


def child_env(base=None) -> dict:
    """A copy of ``base`` (default: this process's environment), pinned."""

    return pin_environ(dict(os.environ if base is None else base))


def occ_threads() -> int:
    try:
        return max(1, int(os.environ.get(OCC_THREADS_ENV, OCC_THREADS_DEFAULT)))
    except ValueError:
        return int(OCC_THREADS_DEFAULT)


def pin_occ() -> bool:
    """Size OCCT's default thread pool before anything first uses it.
    False when OCP is not installed or the pool already exists."""

    try:
        from OCP.OSD import OSD_ThreadPool
    except Exception:  # noqa: BLE001 - a tool without OCP has no pool
        return False
    wanted = occ_threads()
    pool = OSD_ThreadPool.DefaultPool_s(wanted)
    return pool.NbThreads() == wanted


def pin(occ: bool = True) -> None:
    """Pin this process and its children; with ``occ``, OCCT's pool too.
    Call it before numpy, build123d or OCP is imported."""

    pin_environ()
    if occ:
        pin_occ()


def _read(path: Path):
    try:
        return path.read_text(encoding="ascii").strip()
    except OSError:
        return None


def cgroup_dirs(proc_cgroup: Path = Path("/proc/self/cgroup"), root: Path = CGROUP_ROOT) -> list:
    """This process's cgroup v2 directory and its ancestors, innermost first."""

    text = _read(proc_cgroup)
    if not text:
        return []
    for line in text.splitlines():
        hierarchy, _controllers, path = (line.split(":", 2) + ["", ""])[:3]
        if hierarchy == "0":
            here = root / path.lstrip("/")
            return [here, *[parent for parent in here.parents if parent == root or root in parent.parents]]
    return []


def pids_headroom(dirs=None):
    """The fewest tasks any enclosing cgroup can still start
    (``pids.max - pids.current``), or None when no limit is readable."""

    headroom = None
    for directory in cgroup_dirs() if dirs is None else dirs:
        limit, current = _read(Path(directory) / "pids.max"), _read(Path(directory) / "pids.current")
        if limit is None or current is None or limit == "max":
            continue
        try:
            free = int(limit) - int(current)
        except ValueError:
            continue
        headroom = free if headroom is None else min(headroom, free)
    return headroom


def default_jobs(env_name: str | None = None, *, ceiling: int = JOBS_CEILING, per_job: int = JOB_TASKS,
                 headroom=None, cpus=None) -> int:
    """How many CAD jobs run at once. ``env_name`` set in the environment
    wins (a whole number of at least 1, else ValueError); otherwise the
    free task headroom over ``per_job``, from 1 to ``ceiling``; without a
    readable limit, the cores less two, up to ``ceiling``."""

    if env_name is not None:
        value = os.environ.get(env_name)
        if value is not None:
            try:
                jobs = int(value)
            except ValueError:
                raise ValueError(f"{env_name} must be a whole number") from None
            if jobs < 1:
                raise ValueError(f"{env_name} must be at least 1")
            return jobs
    free = pids_headroom() if headroom is None else headroom
    if free is None:
        return max(1, min(ceiling, (cpus if cpus is not None else (os.cpu_count() or 2)) - 2))
    return max(1, min(ceiling, free // max(1, per_job)))


def load(path=None):
    """This module from a tool outside ``cad/scripts`` (make_round, the kit
    tools, seal_proof, the seeded batch), by file path, never by sys.path."""

    import importlib.util
    import sys

    if "cadthreads" in sys.modules:
        return sys.modules["cadthreads"]
    location = Path(path) if path is not None else Path(__file__)
    spec = importlib.util.spec_from_file_location("cadthreads", location)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules["cadthreads"] = module
    return module
