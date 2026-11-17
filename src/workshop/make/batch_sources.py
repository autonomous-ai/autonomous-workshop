"""What a seeded batch step's reuse key binds of a CAD project's sources.

A batch step that builds or gates geometry is reused only while every byte
that could decide its shapes is unchanged (ADR 0098 amendment 2026-11-17).
The CAD skill's Geometry Sources (``geometry_sources.py``) follow ``import``
statements only, so a part file that loads its modules with
``importlib.import_module`` or ``spec_from_file_location`` (the Amsterdam
kit's ``kitparts.py`` loads ``base4``, ``houses4``, ``quays4`` and the
``published/`` parts that way) binds none of them, and a change to one was
reused over. This closure is wider and never narrower:

- every project module a root reaches by ``import``, directly or through
  another project module, each package's ``__init__.py`` included;
- when any module of that closure loads code dynamically (``import_module``,
  ``__import__``, ``spec_from_file_location``, ``run_path``, ``exec`` and
  their kin), every Python file of the project outside the directories that
  hold no source, since any of them may be what it loads;
- every data file of the project outside those directories (``kitmap.json``,
  ``tree/kit.json``, ``print/pieces.json``), since a module may read one.

Outputs, evidence and documents are never bound: ``measure/``, ``snap/``,
``manual/``, ``approved/``, caches, STEP and image files, Markdown, and the
Proof's review records. A change there never reruns a gate.

Imports are read with ``ast``, never executed.
"""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path
from typing import Iterable, Optional

ENTRY_SUFFIX = ".step.py"
PART_PREFIX = "part_"
# Directories that hold no source: evidence, outputs, reviews, caches. The
# CAD skill's NON_GEOMETRY_DIRS plus what the seal and final verification
# write (approved/, design-refs/, manual/).
NO_SOURCE_DIRS = frozenset({
    "measure", "notes", "snap", "review", "ref", "rounds", "samples", "wiki",
    "__cadgen__", "__pycache__", ".cache", ".git", ".venv",
    "approved", "design-refs", "manual",
})
# Files that are outputs or documents, never sources.
NO_SOURCE_SUFFIXES = frozenset({
    ".md", ".step", ".stp", ".stl", ".3mf", ".glb", ".gltf", ".obj", ".png", ".jpg", ".jpeg",
    ".webp", ".svg", ".pdf", ".html", ".log", ".pyc", ".lock",
})
# The Proof's review and approval records: what the owner and critics said,
# not what builds a shape.
NO_SOURCE_NAMES = frozenset({"APPROVAL.json", "CRITIC.json", "SEED-PRODUCT.json"})
# Calls that load code a static read cannot follow.
DYNAMIC_LOADS = frozenset({
    "import_module", "__import__", "spec_from_file_location", "module_from_spec", "exec_module",
    "run_path", "run_module", "exec", "load_source", "SourceFileLoader", "reload",
})


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _is_source_path(project: Path, path: Path) -> bool:
    relative = path.relative_to(project)
    if any(part in NO_SOURCE_DIRS or part.startswith(".") for part in relative.parts[:-1]):
        return False
    name = relative.name
    return not (name.startswith(".") or name in NO_SOURCE_NAMES or path.suffix.lower() in NO_SOURCE_SUFFIXES
                or name.endswith(".step.json"))


def project_files(project: Path) -> list:
    """Every source-candidate file of the project, resolved, sorted."""

    project = Path(project).resolve()
    return sorted(path.resolve() for path in project.rglob("*")
                  if path.is_file() and _is_source_path(project, path))


def _module_files(project: Path, base: Path, dotted: str, level: int) -> list:
    root = project if level == 0 else base
    for _ in range(max(0, level - 1)):
        root = root.parent
    files = []
    parts = [part for part in dotted.split(".") if part]
    for index, part in enumerate(parts):
        root = root / part
        if (root / "__init__.py").is_file():
            files.append(root / "__init__.py")
        elif index == len(parts) - 1 and root.with_suffix(".py").is_file():
            files.append(root.with_suffix(".py"))
        elif not root.is_dir():
            break
    return [path.resolve() for path in files if project in path.resolve().parents]


def _loads_dynamically(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else None
            if name in DYNAMIC_LOADS:
                return True
    return False


def module_closure(project: Path, roots: Iterable[Path]) -> tuple:
    """``(modules, dynamic)``: every project module the roots reach by
    ``import`` (the roots included), and whether any of them loads code
    dynamically. A file that does not parse counts as dynamic: what it would
    load cannot be read."""

    project = Path(project).resolve()
    found: dict = {}
    pending = [Path(root).resolve() for root in roots if Path(root).is_file()]
    dynamic = False
    while pending:
        module = pending.pop()
        if module in found:
            continue
        found[module] = None
        try:
            tree = ast.parse(module.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError, ValueError):
            dynamic = True
            continue
        dynamic = dynamic or _loads_dynamically(tree)
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [(alias.name, 0) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                stem = node.module or ""
                targets = [(stem, node.level)]
                targets += [((stem + "." if stem else "") + alias.name, node.level)
                            for alias in node.names if alias.name != "*"]
            for dotted, level in targets:
                for path in _module_files(project, module.parent, dotted, level):
                    if path not in found:
                        pending.append(path)
    return sorted(found), dynamic


def entries(project: Path) -> list:
    project = Path(project).resolve()
    return [path for path in sorted(project.rglob("*" + ENTRY_SUFFIX))
            if path.is_file() and not any(part in NO_SOURCE_DIRS for part in path.relative_to(project).parts[:-1])]


def source_closure(project: Path, role: Optional[str] = None) -> dict:
    """Project-relative path -> sha256 of every file that could decide the
    shapes of ``part_<role>.step.py`` (``role`` None: of every entry)."""

    project = Path(project).resolve()
    roots = entries(project) if role is None else [project / (PART_PREFIX + role + ENTRY_SUFFIX)]
    modules, dynamic = module_closure(project, roots)
    files = project_files(project)
    chosen = set(modules)
    chosen.update(path for path in files if path.suffix != ".py" or dynamic)
    return {path.relative_to(project).as_posix(): _sha256(path)
            for path in sorted(chosen) if project in path.parents and path.is_file()}


__all__ = ["DYNAMIC_LOADS", "NO_SOURCE_DIRS", "module_closure", "project_files", "source_closure"]
