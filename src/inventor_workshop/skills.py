"""Deterministic discovery and identity for Workshop agent skills."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import sysconfig
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ._package_data import packaged_data_root
from .errors import ContractError
from .models import require_sha256


_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,127}$")
_IGNORED_DIRECTORIES = frozenset((".git", "__pycache__", ".mypy_cache", ".pytest_cache"))
_IGNORED_FILES = frozenset((".DS_Store",))
_IGNORED_SUFFIXES = (".pyc", ".pyo")
MAX_SKILL_FILES = 10_000
MAX_SKILL_BYTES = 512 * 1024 * 1024


@dataclass(frozen=True)
class SkillFile:
    path: str
    bytes: int
    sha256: str
    executable: bool

    def __post_init__(self) -> None:
        self.assert_valid()

    def assert_valid(self) -> None:
        candidate = Path(self.path) if isinstance(self.path, str) else Path(".")
        if (
            not isinstance(self.path, str)
            or not self.path
            or any(ord(character) < 32 or ord(character) == 127 for character in self.path)
            or "\\" in self.path
            or candidate.is_absolute()
            or ".." in candidate.parts
            or candidate.as_posix() != self.path
        ):
            raise ContractError("skill file path must be a safe relative POSIX path")
        if type(self.bytes) is not int or self.bytes < 0:
            raise ContractError("skill file byte count must be a non-negative integer")
        require_sha256(self.sha256, "skill file sha256")
        if type(self.executable) is not bool:
            raise ContractError("skill file executable must be boolean")


@dataclass(frozen=True)
class SkillFingerprint:
    """A source-tree identity independent of timestamps and host paths."""

    schema_version: int
    name: str
    root: Path
    sha256: str
    files: Tuple[SkillFile, ...]
    total_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root))
        object.__setattr__(self, "files", tuple(self.files))
        self.assert_valid()

    def assert_valid(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("skill fingerprint schema_version must be 1")
        if not isinstance(self.name, str) or not _SKILL_NAME.fullmatch(self.name):
            raise ContractError("skill name must match %s" % _SKILL_NAME.pattern)
        if not self.root.is_absolute():
            raise ContractError("skill root must be absolute")
        if (
            not self.files
            or len(self.files) > MAX_SKILL_FILES
            or not all(isinstance(item, SkillFile) for item in self.files)
        ):
            raise ContractError("skill fingerprint requires typed files")
        for item in self.files:
            item.assert_valid()
        paths = [item.path for item in self.files]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ContractError("skill files must be unique and sorted")
        if "SKILL.md" not in paths:
            raise ContractError("skill tree must contain a root SKILL.md")
        if (
            type(self.total_bytes) is not int
            or self.total_bytes > MAX_SKILL_BYTES
            or self.total_bytes != sum(item.bytes for item in self.files)
        ):
            raise ContractError("skill total_bytes is inconsistent")
        require_sha256(self.sha256, "skill tree sha256")
        if _tree_sha256(self.files) != self.sha256:
            raise ContractError("skill tree identity is inconsistent")

    def to_dict(self) -> Dict[str, Any]:
        self.assert_valid()
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "sha256": self.sha256,
            "files": len(self.files),
            "total_bytes": self.total_bytes,
        }


def _tree_sha256(files: Tuple[SkillFile, ...]) -> str:
    document = [asdict(item) for item in files]
    payload = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _hash_regular_file(root: Path, relative: Path) -> SkillFile:
    path = root / relative
    try:
        expected = path.lstat()
    except OSError as exc:
        raise ContractError("cannot inspect skill file %s: %s" % (relative, exc)) from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ContractError("skill entry is not a regular file: %s" % relative.as_posix())
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("cannot safely open skill file %s: %s" % (relative, exc)) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (expected.st_dev, expected.st_ino):
            raise ContractError("skill file changed while opening: %s" % relative.as_posix())
        digest = hashlib.sha256()
        observed = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            observed += len(chunk)
            if observed > MAX_SKILL_BYTES:
                raise ContractError("skill tree exceeds the byte limit")
            digest.update(chunk)
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("skill file changed while hashing: %s" % relative.as_posix())
        return SkillFile(
            path=relative.as_posix(),
            bytes=observed,
            sha256=digest.hexdigest(),
            executable=bool(after.st_mode & stat.S_IXUSR),
        )
    finally:
        os.close(descriptor)


def resolve_skills_root(explicit_root: Optional[Path] = None) -> Path:
    """Resolve exactly one skill root without searching ambient working directories.

    Editable checkouts use the repository-root ``skills`` directory adjacent to this package's
    ``src`` directory. Installed distributions use their versioned shared-data
    tree. An explicit root remains available for pinned deployments.
    """

    if explicit_root is None:
        package = Path(__file__).resolve().parent
        source = package.parent
        source_candidate = source.parent / "skills"
        packaged_candidate = packaged_data_root("skills", Path(__file__))
        legacy_installed_candidate = (
            Path(sysconfig.get_path("data"))
            / "share"
            / "inventor-workshop"
            / "skills"
        )
        if packaged_candidate is not None:
            candidate = packaged_candidate
        elif source.name == "src" and source_candidate.is_dir():
            candidate = source_candidate
        else:
            candidate = legacy_installed_candidate
    else:
        candidate = Path(explicit_root)
        if not candidate.is_absolute():
            raise ContractError("an explicit skills root must be absolute")
    try:
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ContractError(
            "cannot resolve Workshop skills root %s" % candidate
        ) from exc
    if not resolved.is_dir():
        raise ContractError("Workshop skills root is not a directory: %s" % resolved)
    return resolved


def fingerprint_skill_tree(skill_root: Path) -> SkillFingerprint:
    """Hash paths, bytes, executable bits, and file hashes in canonical order."""

    requested = Path(skill_root)
    if requested.is_symlink():
        raise ContractError("skill root must not be a symlink: %s" % requested)
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("cannot resolve skill root %s: %s" % (requested, exc)) from exc
    if not root.is_dir() or not _SKILL_NAME.fullmatch(root.name):
        raise ContractError("skill root must be a named directory")
    skill_md = root / "SKILL.md"
    if skill_md.is_symlink() or not skill_md.is_file():
        raise ContractError("skill root lacks a regular SKILL.md: %s" % root)

    relatives: List[Path] = []
    for directory, dirnames, filenames in os.walk(str(root), followlinks=False):
        base = Path(directory)
        kept = []
        for dirname in sorted(dirnames):
            child = base / dirname
            if dirname in _IGNORED_DIRECTORIES:
                continue
            if child.is_symlink():
                raise ContractError(
                    "skill tree contains a symlink: %s" % child.relative_to(root).as_posix()
                )
            kept.append(dirname)
        dirnames[:] = kept
        for filename in sorted(filenames):
            if filename in _IGNORED_FILES or filename.endswith(_IGNORED_SUFFIXES):
                continue
            relative = (base / filename).relative_to(root)
            relatives.append(relative)
    relatives.sort(key=lambda item: item.as_posix())
    if not relatives or len(relatives) > MAX_SKILL_FILES:
        raise ContractError("skill tree has an invalid file count")
    files = tuple(_hash_regular_file(root, relative) for relative in relatives)
    total = sum(item.bytes for item in files)
    if total > MAX_SKILL_BYTES:
        raise ContractError("skill tree exceeds the byte limit")
    return SkillFingerprint(1, root.name, root, _tree_sha256(files), files, total)


def discover_skills(explicit_root: Optional[Path] = None) -> Tuple[SkillFingerprint, ...]:
    """Discover immediate skill directories in deterministic name order."""

    root = resolve_skills_root(explicit_root)
    skills = []
    for candidate in sorted(root.iterdir(), key=lambda item: item.name):
        if candidate.name in _IGNORED_DIRECTORIES:
            continue
        if candidate.is_symlink():
            raise ContractError("skills root contains a symlink: %s" % candidate)
        if candidate.is_dir() and (candidate / "SKILL.md").is_file():
            skills.append(fingerprint_skill_tree(candidate))
    if not skills:
        raise ContractError("Workshop skills root contains no skills: %s" % root)
    names = [skill.name for skill in skills]
    if len(names) != len(set(names)):
        raise ContractError("Workshop skills root contains duplicate names")
    return tuple(skills)
