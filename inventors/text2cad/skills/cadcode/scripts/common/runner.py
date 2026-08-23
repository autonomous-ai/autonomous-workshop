"""Sandboxed cadpy-backed runner — invoked once per agent tool call.

The agent runs ``python scripts/cad path/to/model.py`` (or a project dir).
That spawns a fresh subprocess that pre-imports ``cadquery`` + ``cadpy``
(so their lazy deps land before the import allow-list kicks in), enforces
rlimits, installs the import allow-list, and hands the project dir to
``cadpy.generation.generate_step``. cadpy reads ``main.py``, calls the
user's ``gen_step()`` (or back-compat ``result = …``) inside this same
sandbox process, and writes:

  <stem>.step   <stem>.stl   <stem>.step.json

The parent (this module's ``run_sandboxed_sync``) handles wall-clock kills
and JSON unwrapping for the CLI.

Single-file mode: the parent CLI synthesizes a tempdir with the user's
``.py`` copied as ``main.py`` before spawning the worker — cadpy's entry
point assumes a project shape.
"""

from __future__ import annotations

import json
import os
import resource
import subprocess
import sys
from pathlib import Path
from typing import Any


# Modules user code must never import, even if they happen to be in
# sys.modules (because cadquery / cadpy / their transitive deps loaded
# them during warmup). The cache shortcut in _restrict_imports would
# otherwise let user code reach them.
DENIED_ROOT_MODULES = frozenset({
    "subprocess", "shutil", "tempfile", "glob",
    "urllib", "socket", "http", "ssl", "ftplib", "smtplib", "telnetlib",
    "requests", "httpx",
    "ctypes", "mmap",
    "pickle", "marshal", "shelve",
    "multiprocessing", "threading", "_thread", "asyncio",
    "pty", "signal",
    # Note: ``os`` and ``pathlib`` are NOT denied — cadpy needs them at
    # the entry-point level to read main.py and write artifacts, and the
    # pre-warm step puts both in sys.modules before the hook activates.
    # User code that does a fresh ``import os`` still trips the hook
    # below (via the not-in-cache path), since cadpy's prewarm imports
    # leave the modules pre-cached and we add ``os``/``pathlib`` to
    # DENIED_USER_FRESH below to keep them out of user reach.
})


# Modules the user MUST NOT freshly import (in addition to DENIED_ROOT_MODULES).
# These are typically modules cadpy needs internally and pre-warms (so they
# would otherwise slip through the sys.modules cache shortcut), but that
# user-supplied gen_step()/result code should never reach.
DENIED_USER_FRESH = frozenset({
    "os", "pathlib", "io", "subprocess", "shutil", "tempfile",
})


ALLOWED_ROOT_MODULES = frozenset({
    "cadquery", "math", "numpy",
    "__future__",  # `from __future__ import annotations`
    "typing", "dataclasses", "enum", "functools", "itertools",
    "operator", "collections", "copy", "fractions", "decimal",
    "abc", "contextlib", "warnings", "weakref",
    "re", "string", "textwrap", "random",
    "json",
    # cadpy and its transitive deps (pre-warmed before restriction).
    "cadpy",
    "trimesh", "pygltflib", "lxml", "networkx", "scipy",
    "OCP", "ezdxf",
    # Skill-internal helpers — kept here as defense in depth in case import
    # order shifts and the package is loaded after _restrict_imports().
    "common",
    # cadcode's own helper library, shipped at <skill>/cadlib/.
    "cadlib",
    # cadquery lazy deps + internal submodules it imports during ops
    # (CadQuery uses relative imports — those bypass our hook — but some
    # boolean / loft paths trigger fresh top-level imports).
    "vtkmodules", "vtk", "nlopt",
    "multimethod", "pyparsing", "typish", "runtype",
    "path", "pillow", "PIL", "casadi",
    "shapes", "selectors", "occ_impl", "sketch", "cq", "geom",
    "assembly", "exporters", "importers", "cq_compat",
})


WALL_CLOCK_TIMEOUT_S = 30      # bumped from 15 — complex parts need more
CPU_TIMEOUT_S = 20
MEMORY_LIMIT_BYTES = 3 * 1024 * 1024 * 1024  # 3 GiB (bumped from 1 GiB —
# the currently-resolved cadquery/OCP build's own import footprint
# (`import cadquery` alone, via `cadquery.occ_impl.geom` pulling several
# OCP/OCCT native submodules) already reserves ~1.1-1.3 GiB of virtual
# address space before any user code runs. Under the old 1 GiB cap,
# setrlimit(RLIMIT_AS) was applied *after* that baseline was already over
# budget, so the first allocation-needing operation (any boolean/fillet)
# either hung indefinitely (multi-threaded OCCT thread-pool startup
# stalling on a failed allocation) or segfaulted/raised
# Standard_OutOfMemory well before any real work was done — reproduced
# with a trivial two-box fuse, independent of model complexity. 3 GiB
# leaves headroom above that baseline while still bounding genuine
# runaways; the wall-clock and CPU caps remain the primary guard.
OUTPUT_FILE_LIMIT_BYTES = 256 * 1024 * 1024  # 256 MiB — fine multi-solid meshes
# (e.g. a 57-link chain ~1.8M triangles) legitimately exceed 100 MiB; the
# wall-clock + CPU caps remain the real runaway guards, and an over-cap write is
# turned into a clean "raise --mesh-tolerance" error (see in_subprocess_main).


# -- Subprocess (in-process) entrypoint -------------------------------------


def _enforce_rlimits(wall_clock_s: float = WALL_CLOCK_TIMEOUT_S) -> None:
    # RLIMIT_CPU counts CPU-seconds summed across ALL threads. OCCT meshing
    # (STL/GLB tessellation) runs parallel across every core, so a legitimate
    # multi-solid export burns ~ncores CPU-seconds per wall-second — a 57-solid
    # necklace spent ~16 CPU-s on STL alone in ~3s wall. A flat 20s CPU cap
    # therefore SIGXCPU-kills honest parts in a handful of wall-seconds, and
    # raising --wall-clock-s can't help because it never reached this limit.
    # Budget the CPU cap as the wall deadline × cores so the parent's
    # wall-clock timeout is the real deadline; this stays a runaway backstop.
    ncores = os.cpu_count() or 1
    cpu_limit = max(CPU_TIMEOUT_S, int(wall_clock_s * ncores))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES,) * 2)
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    except (ValueError, OSError):
        pass
    try:
        resource.setrlimit(resource.RLIMIT_FSIZE, (OUTPUT_FILE_LIMIT_BYTES,) * 2)
    except (ValueError, OSError):
        pass


def _restrict_imports(extra_allowed: frozenset[str] | None = None) -> None:
    """Install an import hook that rejects modules outside the allow-list.

    ``extra_allowed`` are module roots that live inside the user's project
    directory (e.g., ``params``, ``parts``, ``features``, ``assemblies``)
    — discovered at runtime so multi-file projects work.

    A module that is already in ``sys.modules`` is normally allowed — these
    were pre-warmed before restriction. Exception: modules listed in
    ``DENIED_USER_FRESH`` are blocked when imported by user code, even if
    pre-warmed, by looking at the import frame's __name__. Practically we
    enforce that simply by tagging the calling globals: user code lives in
    the synthetic ``__cadcode_model__`` module (named via the cadpy
    runtime), while cadpy lives in ``cadpy.*`` packages.
    """
    import builtins
    real_import = builtins.__import__
    allow_set = ALLOWED_ROOT_MODULES | (extra_allowed or frozenset())

    def _caller_is_user_code(globals_: dict | None) -> bool:
        if not globals_:
            return False
        name = globals_.get("__name__", "") or ""
        # cadpy invokes user code in a module named after the user's project;
        # in practice that's either "__cadcode_model__" (our convention) or
        # the user's main.py module name. cadpy's own internals live under
        # the "cadpy" / "cadpy.*" package namespace.
        if name.startswith("cadpy"):
            return False
        if name.startswith("cadquery") or name.startswith("OCP"):
            return False
        if name.startswith("trimesh") or name.startswith("pygltflib"):
            return False
        if name.startswith("common") or name.startswith("cadlib"):
            return False
        # Treat anything else (project-defined modules, the synthetic main
        # module, etc.) as user code.
        return True

    def restricted(name, globals=None, locals=None, fromlist=(), level=0):
        root = name.split(".")[0]
        if root in DENIED_ROOT_MODULES:
            raise ImportError(
                f"import of {root!r} is not allowed in CADCode sandbox"
            )
        if root in DENIED_USER_FRESH and _caller_is_user_code(globals):
            raise ImportError(
                f"import of {root!r} is not allowed in CADCode sandbox"
            )
        if root in sys.modules:
            return real_import(name, globals, locals, fromlist, level)
        if root not in allow_set:
            raise ImportError(
                f"import of {root!r} is not allowed in CADCode sandbox"
            )
        return real_import(name, globals, locals, fromlist, level)

    builtins.__import__ = restricted


def _discover_project_modules(project_dir: Path) -> frozenset[str]:
    """Find package + module roots that live directly under ``project_dir``.

    A subdirectory counts as a package if it has ``__init__.py``. A top-level
    ``.py`` file counts as a module. ``main.py`` is excluded — it's the
    entrypoint, not something to be imported.
    """
    roots: set[str] = set()
    if not project_dir.is_dir():
        return frozenset()
    for p in project_dir.iterdir():
        if p.is_dir() and (p / "__init__.py").exists():
            roots.add(p.name)
        elif p.is_file() and p.suffix == ".py" and p.stem != "main":
            roots.add(p.stem)
    return frozenset(roots)


def _drain_oversized_outputs(out_dir: Path) -> list[str]:
    """Remove and name any artifact pinned at the RLIMIT_FSIZE cap.

    A write killed by RLIMIT_FSIZE leaves a truncated file at exactly the cap
    (the kernel refuses to grow it further). A successful export is strictly
    smaller, so ``size >= cap`` uniquely flags the corrupt partials we must
    discard rather than hand back as a valid mesh.
    """
    removed: list[str] = []
    try:
        for p in out_dir.iterdir():
            try:
                if p.is_file() and p.stat().st_size >= OUTPUT_FILE_LIMIT_BYTES:
                    p.unlink()
                    removed.append(p.name)
            except OSError:
                pass
    except OSError:
        pass
    return removed


def in_subprocess_main(
    project_dir: str,
    out_dir: str,
    stem: str,
    mesh_tolerance: float = 0.05,
    angular_tolerance: float = 3.0,
    wall_clock_s: float = WALL_CLOCK_TIMEOUT_S,
) -> int:
    """Entry point invoked inside the subprocess.

    Pre-imports happen first (so the allow-list does not need to enumerate
    every transitive cadpy/CadQuery dep), then rlimits, then the import
    restriction, then we hand the project off to cadpy.

    ``project_dir`` must contain a ``main.py`` that defines either
    ``gen_step()`` returning a cq.Workplane/Shape/Assembly, or the legacy
    ``result = <shape>`` module-scope assignment. cadpy accepts both.
    """
    import traceback

    # 1. Pre-import cadquery so its lazy chain is fully loaded.
    import cadquery as _cq  # noqa: F401
    _cq.exporters  # noqa: B018
    _cq.Workplane("XY").box(1, 1, 1)

    # 2. Pre-import cadpy. This lives at <skill>/scripts/packages/cadpy/
    #    after the vendor step (build-skill-runtimes.sh). During development
    #    the path may be empty and the import resolves to a sibling install
    #    or a test-time stub (see tests/conftest.py).
    _skill_root = Path(__file__).resolve().parents[2]
    _packages_dir = _skill_root / "scripts" / "packages"
    if str(_packages_dir) not in sys.path:
        sys.path.insert(0, str(_packages_dir))
    # The real ``cadpy.generation.generate_step`` wrapper landed with
    # Track A's follow-up. Tests still inject a faster in-process stub
    # via ``CADCODE_TEST_CADPY_PATH`` (see tests/conftest.py) to avoid
    # paying for the full OCCT STEP export on every assertion.
    import cadpy  # noqa: F401
    import cadpy.generation as _cadpy_gen  # noqa: F401

    # 3. Make the skill's own cadlib package importable. The runner lives at
    #    <skill>/scripts/common/runner.py, so the skill root is parents[2].
    if str(_skill_root) not in sys.path:
        sys.path.insert(0, str(_skill_root))
    # Pre-warm cadlib so its transitive deps are loaded before the import
    # restriction kicks in.
    try:
        import cadlib  # noqa: F401
    except Exception:
        pass

    # 4. Pre-warm common stdlib bits the user (and cadpy) may need.
    import dataclasses  # noqa: F401
    import typing  # noqa: F401
    import enum  # noqa: F401
    import functools  # noqa: F401
    import itertools  # noqa: F401
    import collections  # noqa: F401
    import contextlib  # noqa: F401
    import io  # noqa: F401
    import re  # noqa: F401
    import json as _json  # noqa: F401
    import warnings  # noqa: F401
    import abc  # noqa: F401
    import copy  # noqa: F401
    import math  # noqa: F401
    import operator  # noqa: F401
    # cadpy needs these for IO + traceback formatting:
    import os as _os  # noqa: F401
    import pathlib as _pathlib  # noqa: F401
    import hashlib as _hashlib  # noqa: F401

    project_dir_p = Path(project_dir)
    out_dir_p = Path(out_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    output_path = out_dir_p / f"{stem}.step"

    # 5. Project mode: discover sibling modules + packages and put them on
    #    sys.path so cadpy's main.py exec can import them.
    extra = _discover_project_modules(project_dir_p)
    if extra:
        if str(project_dir_p) not in sys.path:
            sys.path.insert(0, str(project_dir_p))

    # 6. Lock down the sandbox. After this, fresh imports outside the
    #    allow-list (plus project-local modules) will fail.
    _enforce_rlimits(wall_clock_s)
    _restrict_imports(extra)

    # 7. Hand off to cadpy. cadpy reads main.py, calls gen_step()/picks up
    #    `result`, exports STEP + STL + metadata, and returns a result dict.
    try:
        result = _cadpy_gen.generate_step(
            project_dir=project_dir_p,
            output_path=output_path,
            mesh_tolerance=float(mesh_tolerance),
            # --angular-tolerance is a degrees-facing CLI flag (see cad/cli.py),
            # but cadpy/OCCT BRepMesh_IncrementalMesh expects radians. Convert
            # here at the single handoff both the direct and render-subprocess
            # paths funnel through. Without this, the default 3.0 was consumed
            # as 3 radians (~172deg) => no angular refinement => faceted holes.
            mesh_angular_tolerance=math.radians(float(angular_tolerance)),
        )
    except Exception as e:
        # cadpy raises GenerationError subclasses (see
        # cadpy.generation.GenerationError / ShapeValidationError /
        # ExportError / GeneratorRuntimeError / ProjectShapeError). We
        # surface them uniformly into the JSON contract §3 error shape.
        code = "EXPORT_ERROR"
        # SyntaxError/ImportError can propagate from user code before the
        # GenerationError wrapping kicks in (importlib raises them
        # directly), so check those first.
        if isinstance(e, SyntaxError):
            code = "SYNTAX_ERROR"
        elif isinstance(e, ImportError):
            code = "RUNTIME_ERROR"
        elif isinstance(e, getattr(_cadpy_gen, "ShapeValidationError", ())):
            code = "VALIDATION_FAILED"
        elif isinstance(e, getattr(_cadpy_gen, "ProjectShapeError", ())):
            code = "VALIDATION_FAILED"
        elif isinstance(e, getattr(_cadpy_gen, "GeneratorRuntimeError", ())):
            code = "RUNTIME_ERROR"
        elif isinstance(e, getattr(_cadpy_gen, "ExportError", ())):
            code = "EXPORT_ERROR"
        elif isinstance(e, getattr(_cadpy_gen, "GenerationError", ())):
            code = "EXPORT_ERROR"
        elif isinstance(e, (TypeError, ValueError)):
            code = "VALIDATION_FAILED"
        # RLIMIT_FSIZE aborts an STL/GLB write mid-stream, leaving a truncated
        # file at the cap and a cryptic low-level "failed to write" message.
        # Discard the partial and surface an actionable error instead.
        oversized = _drain_oversized_outputs(out_dir_p)
        if oversized:
            cap_mib = OUTPUT_FILE_LIMIT_BYTES // (1024 * 1024)
            message = (
                f"mesh too large: output ({', '.join(sorted(oversized))}) hit "
                f"the {cap_mib} MiB sandbox file cap and was discarded. The part "
                f"tessellates too finely — raise --mesh-tolerance (current "
                f"{mesh_tolerance} mm) and/or --angular-tolerance to cut the "
                f"triangle count."
            )
        else:
            message = f"{type(e).__name__}: {e}"
        _emit({
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "traceback": traceback.format_exc(limit=6),
            },
        })
        return 1

    payload = _build_success_payload(result, output_path, out_dir_p, stem)
    _emit(payload)
    return 0


def _build_success_payload(
    cadpy_result: Any,
    output_path: Path,
    out_dir: Path,
    stem: str,
) -> dict[str, Any]:
    """Normalize cadpy's generate_step return into contract §3 CadcodeResult.

    cadpy's return shape is expected to look like::

        {
          "step_path":     Path,
          "stl_path":      Path,
          "metadata_path": Path,
          "is_solid":      bool,
          "volume_mm3":    float,
          "bbox":          {"min": (..), "max": (..)},
        }

    During development (stubbed cadpy), the result may be a partial dict or
    ``None``; we infer the artifact paths from the filesystem layout in
    those cases.
    """
    payload: dict[str, Any] = {"ok": True}

    # Inferred paths — used when cadpy returns nothing useful (stub path).
    inferred = {
        "step_path": out_dir / f"{stem}.step",
        "metadata_path": out_dir / f"{stem}.step.json",
        "stl_path": out_dir / f"{stem}.stl",
    }

    src: dict[str, Any] = {}
    if isinstance(cadpy_result, dict):
        src = cadpy_result

    for key in ("step_path", "metadata_path", "stl_path"):
        v = src.get(key)
        if v is None:
            # Fall back to filesystem inference: only include paths that
            # actually exist on disk.
            cand = inferred[key]
            if cand.exists():
                payload[key] = str(cand)
        else:
            payload[key] = str(v)

    for fact in ("is_solid", "volume_mm3", "bbox"):
        if fact in src:
            payload[fact] = src[fact]

    # Per-part STLs for assemblies — echoed so callers know each part's file.
    # Absent (or empty) for single-solid projects; kept additive.
    if src.get("parts"):
        payload["parts"] = [
            {"name": str(p.get("name", "")), "stl_path": str(p.get("stl_path", ""))}
            for p in src["parts"]
        ]

    # Deterministic geometry warnings (floating bodies, slivers, invalid
    # B-reps). Additive; absent/empty when the geometry is clean.
    if src.get("warnings"):
        payload["warnings"] = [
            {
                "part": str(w.get("part", "")),
                "kind": str(w.get("kind", "")),
                "detail": str(w.get("detail", "")),
                "severity": str(w.get("severity", "warning")),
            }
            for w in src["warnings"]
        ]

    # Echo the tolerance flags so callers can verify wiring (back-compat
    # with the old runner contract — kept additive).
    if "mesh_tolerance" in src:
        payload["mesh_tolerance"] = src["mesh_tolerance"]
    if "mesh_angular_tolerance" in src:
        payload["angular_tolerance"] = src["mesh_angular_tolerance"]
    return payload


def _emit(payload: dict) -> None:
    sys.stdout.write(json.dumps(payload, default=str) + "\n")
    sys.stdout.flush()


# -- Parent-side helper -----------------------------------------------------


def run_sandboxed_sync(
    project_dir: Path,
    out_dir: Path,
    stem: str,
    *,
    wall_clock_s: float = WALL_CLOCK_TIMEOUT_S,
    mesh_tolerance: float = 0.05,
    angular_tolerance: float = 3.0,
) -> dict[str, Any]:
    """Spawn the worker subprocess and return the parsed JSON result.

    ``project_dir`` MUST be a directory containing ``main.py`` — the CLI is
    responsible for normalizing a single-file input into that shape.

    Always returns a dict — never raises — so the agent's downstream code
    can decode and react.
    """
    scripts_dir = Path(__file__).resolve().parents[1]  # skills/cadcode/scripts
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", "/tmp"),
        "PYTHONUNBUFFERED": "1",
        "PYTHONPATH": str(scripts_dir),
    }
    # Propagate the test-stub override path so tests can inject a
    # bare-bones cadpy without touching the real PyPI package.
    if "CADCODE_TEST_CADPY_PATH" in os.environ:
        env["CADCODE_TEST_CADPY_PATH"] = os.environ["CADCODE_TEST_CADPY_PATH"]

    cmd = [
        sys.executable,
        "-c",
        (
            "import sys, os; "
            # Tests inject a fast in-process stub cadpy via this env var
            # (see skills/cadcode/tests/conftest.py); the production
            # runtime uses the vendored copy at scripts/packages/cadpy/.
            "_p = os.environ.get('CADCODE_TEST_CADPY_PATH'); "
            "_p and sys.path.insert(0, _p); "
            "from common.runner import in_subprocess_main; "
            "sys.exit(in_subprocess_main(sys.argv[1], sys.argv[2], sys.argv[3], "
            "float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6])))"
        ),
        str(project_dir),
        str(out_dir),
        stem,
        str(mesh_tolerance),
        str(angular_tolerance),
        str(wall_clock_s),
    ]

    try:
        proc = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=wall_clock_s,
        )
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error": {
                "code": "SANDBOX_TIMEOUT",
                "message": (
                    f"sandbox timeout after {wall_clock_s}s — model may be "
                    "in an infinite loop or running a very expensive boolean. "
                    "Simplify."
                ),
            },
            "timed_out": True,
            "stdout": (e.stdout or "")[-2000:] if isinstance(e.stdout, str) else "",
            "stderr": (e.stderr or "")[-2000:] if isinstance(e.stderr, str) else "",
        }

    stdout = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if not stdout:
        # Likely killed by rlimit (SIGXCPU on Linux/macOS).
        return {
            "ok": False,
            "error": {
                "code": "SANDBOX_TIMEOUT",
                "message": "worker produced no output (likely CPU rlimit kill)",
            },
            "stderr": stderr[-2000:],
        }

    last_line = stdout.splitlines()[-1]
    try:
        payload = json.loads(last_line)
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": {
                "code": "RUNTIME_ERROR",
                "message": "worker emitted non-JSON output",
            },
            "stdout": stdout[-2000:],
            "stderr": stderr[-2000:],
        }
    return payload
