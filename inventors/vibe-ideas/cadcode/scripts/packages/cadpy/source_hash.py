from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path

from cadpy import catalog


_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_SKIPPED_PATH_PARTS = {
    "__pycache__",
    ".cache",
    ".eggs",
    ".env",
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".svn",
    ".tox",
    ".venv",
    "build",
    "dist",
    "env",
    "node_modules",
    "site-packages",
    "venv",
}


@dataclass(frozen=True)
class SourceFileHash:
    path: str
    hash: str


@dataclass(frozen=True)
class PythonSourceHash:
    digest: str
    files: tuple[SourceFileHash, ...]
    source_path: str
    source_hash: str

    @property
    def source_fingerprint(self) -> str:
        return self.digest


def python_source_hash(script_path: Path) -> PythonSourceHash:
    """Hash a generator script plus local Python imports discovered statically."""
    resolved_script = script_path.expanduser().resolve()
    files: dict[Path, str] = {}
    queue: list[Path] = [resolved_script]
    seen: set[Path] = set()
    search_paths = _generator_search_paths(resolved_script)
    allowed_roots = tuple(path.resolve() for path in search_paths)

    while queue:
        current = queue.pop(0).resolve()
        if current in seen or not _trackable_python_file(current, allowed_roots):
            continue
        seen.add(current)
        file_hash = _sha256_file(current)
        files[current] = file_hash
        for dependency in _python_import_dependencies(current, search_paths, allowed_roots):
            if dependency not in seen:
                queue.append(dependency)

    source_manifest_path = _manifest_path(resolved_script)
    manifest_files = tuple(
        SourceFileHash(path=_manifest_path(path), hash=file_hash)
        for path, file_hash in sorted(files.items(), key=lambda item: _manifest_path(item[0]))
    )
    digest = hashlib.sha256()
    for file in manifest_files:
        digest.update(file.path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file.hash.encode("ascii"))
        digest.update(b"\0")
    return PythonSourceHash(
        digest=digest.hexdigest(),
        files=manifest_files,
        source_path=source_manifest_path,
        source_hash=files.get(resolved_script, ""),
    )


def _generator_search_paths(script_path: Path) -> list[Path]:
    repo_root = catalog.REPO_ROOT.resolve()
    cad_root = catalog.CAD_ROOT.resolve()
    search_paths = [
        repo_root,
        cad_root,
        _PACKAGE_ROOT.resolve(),
        (repo_root / "skills" / "cad" / "scripts").resolve(),
        script_path.parent.resolve(),
    ]
    for parent in script_path.parents:
        if parent == repo_root.parent:
            break
        if (
            (parent / "STEP" / "__init__.py").is_file()
            or (parent / "robot_common" / "__init__.py").is_file()
        ):
            search_paths.append(parent.resolve())
    return _dedupe_paths(search_paths)


def _manifest_roots() -> tuple[Path, ...]:
    return tuple(_dedupe_paths([
        catalog.CAD_ROOT.resolve(),
        catalog.REPO_ROOT.resolve(),
        _PACKAGE_ROOT.resolve(),
    ]))


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    result: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def _trackable_python_file(path: Path, allowed_roots: tuple[Path, ...]) -> bool:
    if path.suffix != ".py" or not path.is_file():
        return False
    if any(part in _SKIPPED_PATH_PARTS for part in path.parts):
        return False
    return any(_is_relative_to(path, root) for root in allowed_roots)


def _python_import_dependencies(
    file_path: Path,
    search_paths: list[Path],
    allowed_roots: tuple[Path, ...],
) -> tuple[Path, ...]:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return ()

    dependencies: set[Path] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies.update(_resolve_module(str(alias.name or ""), search_paths, allowed_roots))
        elif isinstance(node, ast.ImportFrom):
            dependencies.update(_resolve_import_from(node, file_path, search_paths, allowed_roots))
    return tuple(sorted(dependencies))


def _resolve_import_from(
    node: ast.ImportFrom,
    file_path: Path,
    search_paths: list[Path],
    allowed_roots: tuple[Path, ...],
) -> set[Path]:
    module_name = str(node.module or "")
    dependencies: set[Path] = set()
    if int(node.level or 0) > 0:
        base_dir = file_path.parent
        for _ in range(max(0, int(node.level or 0) - 1)):
            base_dir = base_dir.parent
        dependencies.update(_resolve_module_from_directory(base_dir, module_name, allowed_roots))
        for alias in node.names:
            alias_name = str(alias.name or "")
            if alias_name == "*":
                continue
            child_name = f"{module_name}.{alias_name}" if module_name else alias_name
            dependencies.update(_resolve_module_from_directory(base_dir, child_name, allowed_roots))
        return dependencies

    dependencies.update(_resolve_module(module_name, search_paths, allowed_roots))
    for alias in node.names:
        alias_name = str(alias.name or "")
        if alias_name == "*":
            continue
        child_name = f"{module_name}.{alias_name}" if module_name else alias_name
        dependencies.update(_resolve_module(child_name, search_paths, allowed_roots))
    return dependencies


def _resolve_module(
    module_name: str,
    search_paths: list[Path],
    allowed_roots: tuple[Path, ...],
) -> set[Path]:
    dependencies: set[Path] = set()
    if not module_name:
        return dependencies
    for base_dir in search_paths:
        dependencies.update(_resolve_module_from_directory(base_dir, module_name, allowed_roots))
    return dependencies


def _resolve_module_from_directory(
    base_dir: Path,
    module_name: str,
    allowed_roots: tuple[Path, ...],
) -> set[Path]:
    parts = [part for part in module_name.split(".") if part]
    if not parts:
        return set()
    module_dir = base_dir.joinpath(*parts)
    leaf_module = module_dir.with_suffix(".py")
    if _trackable_python_file(leaf_module, allowed_roots):
        return _package_init_files(base_dir, parts[:-1], allowed_roots) | {leaf_module.resolve()}
    package_init = module_dir / "__init__.py"
    if _trackable_python_file(package_init, allowed_roots):
        return _package_init_files(base_dir, parts, allowed_roots)
    return set()


def _package_init_files(base_dir: Path, package_parts: list[str], allowed_roots: tuple[Path, ...]) -> set[Path]:
    files: set[Path] = set()
    for index in range(1, len(package_parts) + 1):
        init_path = base_dir.joinpath(*package_parts[:index]) / "__init__.py"
        if _trackable_python_file(init_path, allowed_roots):
            files.add(init_path.resolve())
    return files


def _manifest_path(path: Path) -> str:
    resolved = path.resolve()
    for root in _manifest_roots():
        try:
            return resolved.relative_to(root).as_posix()
        except ValueError:
            continue
    return resolved.as_posix()


def _resolve_manifest_path(manifest_path: str) -> Path:
    path = Path(manifest_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    for root in _manifest_roots():
        candidate = (root / path).resolve()
        if candidate.is_file():
            return candidate
    return (catalog.CAD_ROOT / path).resolve()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False
