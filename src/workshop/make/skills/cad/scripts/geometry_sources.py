#!/usr/bin/env python3
"""Geometry Sources: the files of a CAD Project whose bytes decide a shape.

Each Component's source, the Shared Helpers it imports and the project
parameters it reads through them. A check on a shape goes stale only when
these change; measurements, audits, notes, samples and renders in the same
project never make it stale (Workshop issue #110, CONTEXT.md).

This is the one definition. The motion evidence (`motion_presentation.py`),
`make_round` (component packets, the assembly packet and `--interface`
checks) and `verify_project`'s sweep reuse all read it.

Imports are read from the source with `ast`, never executed: a Component
binds the project modules its `import` statements reach, directly or through
another such module, and nothing else.

    python geometry_sources.py <project-dir>      # prints the map as JSON
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from typing import Callable, Iterable

ENTRY_SUFFIX = ".step.py"
PART_PREFIX = "part_"
# Directories that hold no geometry entry: evidence, audits, notes, renders,
# references, the Shared Helper samples, caches. A module under one of them
# is still a Geometry Source when an entry imports it.
NON_GEOMETRY_DIRS = frozenset({
    "measure", "notes", "snap", "review", "ref", "rounds", "samples", "wiki",
    "__cadgen__", "__pycache__", ".cache", ".git", ".venv",
})


def file_hash(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _module_files(project: Path, base: Path, dotted: str, level: int) -> list[Path]:
    """The project files ``import`` of ``dotted`` at relative ``level`` from a
    module in ``base`` executes: each package's ``__init__.py`` and the module
    itself. A name outside the project (cadgen, the standard library) has none."""

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
    return [path for path in files if project in path.resolve().parents]


def imported_modules(project: Path, source: Path) -> list[Path]:
    """Every project-local module ``source`` imports, directly or through
    another such module, resolved, without ``source`` itself."""

    project = Path(project).resolve()
    source = Path(source).resolve()
    found: dict[Path, None] = {}
    pending = [source]
    seen = set()
    while pending:
        module = pending.pop()
        if module in seen:
            continue
        seen.add(module)
        try:
            tree = ast.parse(module.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError, ValueError):
            continue
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Import):
                targets = [(alias.name, 0) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                stem = node.module or ""
                targets = [(stem, node.level)]
                # ``from features import forms`` may name a submodule.
                targets += [((stem + "." if stem else "") + alias.name, node.level)
                            for alias in node.names if alias.name != "*"]
            for dotted, level in targets:
                for path in _module_files(project, module.parent, dotted, level):
                    resolved = path.resolve()
                    if resolved != source and resolved not in found:
                        found[resolved] = None
                        pending.append(resolved)
    return sorted(found)


def imported_helpers(project: Path, source: Path) -> dict[str, str]:
    """Project-relative path -> sha256 of every Shared Helper ``source``
    imports (ADR 0081)."""

    project = Path(project).resolve()
    return {path.relative_to(project).as_posix(): file_hash(path) for path in imported_modules(project, source)}


def entries(project: Path) -> list[Path]:
    """Every generator entry (``*.step.py``) of the project outside the
    directories that hold no geometry."""

    project = Path(project).resolve()
    return [path for path in sorted(project.rglob("*" + ENTRY_SUFFIX))
            if path.is_file() and not any(part in NON_GEOMETRY_DIRS
                                          for part in path.relative_to(project).parts[:-1])]


def geometry_source_paths(project: Path, roots: Iterable[Path] | None = None) -> list[str]:
    """Project-relative paths of the Geometry Sources of ``roots`` (default:
    every entry): each root and every project module it imports."""

    project = Path(project).resolve()
    found: set[Path] = set()
    for root in (entries(project) if roots is None else roots):
        root = Path(root)
        root = (root if root.is_absolute() else project / root).resolve()
        if not root.is_file():
            continue
        found.add(root)
        found.update(imported_modules(project, root))
    return sorted(path.relative_to(project).as_posix() for path in found if project in path.parents)


def geometry_sources(project: Path, roots: Iterable[Path] | None = None,
                     digest: Callable[[Path, str], str] | None = None) -> dict[str, str]:
    """Project-relative path -> sha256 of the Geometry Sources of ``roots``
    (default: the whole project's entries). ``digest(project, relative)``
    replaces the plain file hash, for a caller with its own safe reader."""

    project = Path(project).resolve()
    read = digest or (lambda base, relative: file_hash(base / relative))
    return {relative: read(project, relative) for relative in geometry_source_paths(project, roots)}


def component_geometry_sources(project: Path, role: str) -> dict[str, str]:
    """One Component's Geometry Sources: ``part_<role>.step.py`` and the
    Shared Helpers it imports. Empty when the source does not exist."""

    project = Path(project).resolve()
    return geometry_sources(project, [project / (PART_PREFIX + role + ENTRY_SUFFIX)])


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: geometry_sources.py <project-dir>", file=sys.stderr)
        return 2
    print(json.dumps(geometry_sources(Path(args[0])), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
