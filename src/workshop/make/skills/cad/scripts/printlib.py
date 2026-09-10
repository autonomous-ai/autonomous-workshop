#!/usr/bin/env python3
"""Printable-entry discovery and source->mesh tessellation.

`check_fit` and the mesh gates (`check_mesh`, `check_overhang`,
`check_thickness`, `repair_mesh`) must agree on two things, or they quietly
check different models:

    which entries are print targets     PRINTABLE, part_* vs combined, the
                                        single-assembly fallback
    what mesh those entries produce     the tessellation the gates measure

Both answers live here once and every gate imports them, for the same reason
`meshlib` owns the weld tolerance: two nearly-identical answers is worse than
one, because neither side looks wrong on its own.

This repository writes STEP and nothing else, so there is no mesh artifact to
read. The gates build the entry from source and tessellate the B-rep here. That
costs the old pair's staleness check -- when the gates read an exported STL,
`check_fit` reading source and `check_mesh` reading the artifact disagreed
exactly when the export was stale -- but with no artifact to go stale there is
nothing left for that pair to catch. What the mesh gates still answer is what
they always answered: whether the solid, at slicing resolution, is watertight,
manifold, thick enough for the nozzle, and supportable.

Tessellation deviation matters. `BRepMesh` discretises a shared edge once and
both adjacent faces use that discretisation, so a sound solid tessellates to a
watertight mesh; a mesh gate failing watertightness on a source-fed mesh is
reporting a real defect in the solid, not a tessellation artifact.

    python "$CAD_SKILL_ROOT/scripts/printlib.py"        # self-check
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PACKAGES_DIR = SCRIPTS_DIR / "packages"
CADPY_SRC_DIR = PACKAGES_DIR / "cadgen" / "src"
for _runtime_path in (SCRIPTS_DIR, PACKAGES_DIR, CADPY_SRC_DIR):
    _text = str(_runtime_path)
    if _runtime_path.is_dir() and _text not in sys.path:
        sys.path.insert(0, _text)

ENTRY_SUFFIX = ".step.py"
PART_PREFIX = "part_"

# Tessellation defaults. 0.02 mm chord deviation is well under a 0.4 mm nozzle
# and under the 0.05 mm thickness resolution the thickness gate works at, so the
# mesh is not the limiting factor in any measurement a gate reports.
MESH_DEVIATION = 0.02      # mm; max chord distance from the true surface
MESH_ANGULAR = 0.2         # rad; max normal deviation across one triangle

IGNORED_DIR_NAMES = {
    "__cadgen__",
    "__pycache__",
    ".cache",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "measure",
    "node_modules",
    "ref",
    "skills",
    "snaps",
}

# Built at runtime for the same reason as check_layout's marker: cadgen's
# discovery scan treats any worktree file carrying these bytes as a generator
# candidate, and would log a spurious "invalid CAD source" on every gen run.
GEN_FUNC = "gen_" + "step"


def declared_printable(path: Path) -> bool | None:
    """Read an optional module-level ``PRINTABLE = bool`` without importing CAD."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        value = None
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "PRINTABLE"
            for target in node.targets
        ):
            value = node.value
        elif (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PRINTABLE"
        ):
            value = node.value
        if value is not None:
            if isinstance(value, ast.Constant) and isinstance(value.value, bool):
                return value.value
            raise ValueError(f"{path}: PRINTABLE must be the literal True or False")
    return None


def iter_printable_entries(root: Path) -> dict[Path, list[Path]]:
    """Yield actual print targets, grouped by their project directory."""
    entries_by_dir: dict[Path, list[Path]] = {}
    for path in sorted(root.rglob("*" + ENTRY_SUFFIX)):
        rel_parts = path.relative_to(root).parts[:-1]
        if any(part in IGNORED_DIR_NAMES for part in rel_parts):
            continue
        if GEN_FUNC not in path.read_text(encoding="utf-8", errors="replace"):
            continue
        entries_by_dir.setdefault(path.parent, []).append(path)

    by_dir: dict[Path, list[Path]] = {}
    for project, entries in entries_by_dir.items():
        parts = [path for path in entries if path.name.startswith(PART_PREFIX)]
        assemblies = [path for path in entries if not path.name.startswith(PART_PREFIX)]
        selected = [path for path in parts if declared_printable(path) is not False]
        if parts:
            selected.extend(
                path for path in assemblies if declared_printable(path) is True
            )
        elif len(assemblies) == 1 and declared_printable(assemblies[0]) is not False:
            selected.append(assemblies[0])
        if selected:
            by_dir[project] = sorted(selected)
    return by_dir


def explicit_entries(root: Path, raw_entries: list[str]) -> dict[Path, list[Path]]:
    """Resolve explicitly selected printable entries beneath ``root``."""
    by_dir: dict[Path, list[Path]] = {}
    cwd = Path.cwd().resolve()
    for raw in raw_entries:
        candidate = Path(raw)
        if not candidate.is_absolute():
            from_cwd = (cwd / candidate).resolve()
            candidate = from_cwd if from_cwd.is_file() else (root / candidate).resolve()
        else:
            candidate = candidate.resolve()
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError(f"entry must stay inside {root}: {candidate}") from error
        if not candidate.is_file() or not candidate.name.endswith(ENTRY_SUFFIX):
            raise ValueError(f"not a *{ENTRY_SUFFIX} entry: {candidate}")
        if GEN_FUNC not in candidate.read_text(encoding="utf-8", errors="replace"):
            raise ValueError(f"{candidate} defines no {GEN_FUNC}()")
        if declared_printable(candidate) is False:
            raise ValueError(f"{candidate} declares PRINTABLE = False")
        by_dir.setdefault(candidate.parent, []).append(candidate)
    return by_dir


@contextlib.contextmanager
def project_on_path(project: Path):
    """Put a project directory on sys.path for the duration of a build.

    An entry imports its `*_lib` sibling by bare name, and a generator may defer
    that import until it is called, so the path has to stay in place across the
    build and not only across the import. Removed again only if it was inserted
    here, so a caller managing the path around its own loop keeps it.
    """
    text = str(project)
    inserted = text not in sys.path
    if inserted:
        sys.path.insert(0, text)
    try:
        yield
    finally:
        if inserted:
            with contextlib.suppress(ValueError):
                sys.path.remove(text)


def load_entry(path: Path, namespace: str):
    """Import one entry generator with its project directory on sys.path."""
    module_name = f"_printlib_{namespace}_{path.name.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(module_name, None)
        raise
    return module


def purge_project_modules(project: Path) -> None:
    """Drop every module imported from this project so the next one is clean."""
    project_text = str(project)
    for name, module in list(sys.modules.items()):
        origin = getattr(module, "__file__", None)
        if origin and str(Path(origin).resolve()).startswith(project_text):
            sys.modules.pop(name, None)


def build_entry(path: Path, namespace: str):
    """Build one entry and return its shape, with generator stdout swallowed."""
    sink = io.StringIO()
    with project_on_path(path.parent), contextlib.redirect_stdout(sink):
        module = load_entry(path, namespace)
        builder = getattr(module, GEN_FUNC, None)
        if builder is None:
            raise AttributeError(f"{path.name} defines no {GEN_FUNC}()")
        shape = builder()
    if shape is None:
        raise ValueError(f"{path.name} {GEN_FUNC}() returned None")
    return shape


def tessellate(shape, *, deviation: float = MESH_DEVIATION,
               angular: float = MESH_ANGULAR):
    """Return an (N, 3, 3) triangle-soup array for a built shape, in mm.

    The soup layout, not an indexed mesh, because `meshlib.weld` owns the
    vertex identity question and every gate goes through it.
    """
    import numpy as np

    vectors, triangles = shape.tessellate(deviation, angular)
    if not triangles:
        raise ValueError("tessellation produced no triangles")
    points = np.asarray(
        [[vector.X, vector.Y, vector.Z] for vector in vectors], dtype=np.float64
    )
    faces = np.asarray(triangles, dtype=np.int64)
    return points[faces]


def entry_mesh(path: Path, namespace: str, *, deviation: float = MESH_DEVIATION,
               angular: float = MESH_ANGULAR):
    """Build one printable entry from source and tessellate it in one step."""
    return tessellate(build_entry(path, namespace), deviation=deviation,
                      angular=angular)


def resolve_single_entry(target: str) -> Path:
    """Resolve a CLI target to exactly one printable entry.

    The mesh gates stay single-subject on purpose: a project prints one part at
    a time and each is sliced on its own, so one report per part is the honest
    unit. `verify_project` owns the sweep across parts. A directory is accepted
    only when it leaves no choice to guess at.
    """
    path = Path(target).resolve()
    if path.is_file():
        if not path.name.endswith(ENTRY_SUFFIX):
            raise SystemExit(f"not a *{ENTRY_SUFFIX} entry: {path}")
        if GEN_FUNC not in path.read_text(encoding="utf-8", errors="replace"):
            raise SystemExit(f"{path} defines no {GEN_FUNC}()")
        if declared_printable(path) is False:
            raise SystemExit(f"{path} declares PRINTABLE = False")
        return path
    if not path.is_dir():
        raise SystemExit(f"no such entry or project directory: {path}")

    found = iter_printable_entries(path).get(path, [])
    if not found:
        raise SystemExit(f"{path}: no printable entries")
    if len(found) > 1:
        listed = "\n  ".join(entry.name for entry in found)
        raise SystemExit(
            f"{path} has {len(found)} printable entries; name the one to check:\n"
            f"  {listed}"
        )
    return found[0]


def entry_role(path: Path) -> str:
    """The short name a report uses for an entry: `part_base.step.py` -> `base`."""
    role = path.name.removesuffix(ENTRY_SUFFIX)
    return role.removeprefix(PART_PREFIX) if role.startswith(PART_PREFIX) else role


def _self_check() -> int:
    import numpy as np
    from build123d import Box, Cylinder

    from meshlib import summarize, weld

    ok = True

    shape = Box(20, 10, 5) - Cylinder(3, 10)
    soup = tessellate(shape)
    verts, faces = weld(soup)
    metrics = summarize(verts, faces)
    watertight = (
        metrics["boundary"] == 0
        and metrics["nonmanifold_edges"] == 0
        and metrics["flipped"] == 0
        and metrics["shells"] == 1
    )
    print(f"{'ok  ' if watertight else 'FAIL'} a sound solid tessellates watertight, "
          f"manifold and consistently wound")
    ok &= watertight

    # The mesh has to measure the solid, not merely be sound: a deviation that
    # is too coarse silently shrinks a bored part and every downstream
    # measurement inherits the error.
    error = abs(metrics["volume"] - shape.volume) / shape.volume
    close = error < 1e-3
    print(f"{'ok  ' if close else 'FAIL'} tessellated volume within 0.1% of exact "
          f"({error * 100:.3f}%)")
    ok &= close

    box = np.asarray([20.0, 10.0, 5.0])
    exact_size = np.allclose(metrics["size"], box, atol=1e-6)
    print(f"{'ok  ' if exact_size else 'FAIL'} planar extents survive tessellation exactly")
    ok &= exact_size

    # build123d raises on a genuinely empty shape, so the guard here only
    # catches a shape that tessellates to nothing without complaining. Test it
    # with a stub rather than pretending a real shape reaches that state.
    class _NoTriangles:
        def tessellate(self, deviation, angular):
            return [], []

    empty = False
    try:
        tessellate(_NoTriangles())
    except ValueError:
        empty = True
    print(f"{'ok  ' if empty else 'FAIL'} a shape that tessellates to no triangles "
          f"raises instead of returning an empty mesh")
    ok &= empty

    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(_self_check())
