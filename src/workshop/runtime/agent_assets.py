"""Locate the exact product-run constitution and workflow skill.

Repository builder instructions are deliberately not part of this asset set.
Source checkouts use the canonical ``.agents`` files directly; built wheels
carry a byte-for-byte snapshot under ``workshop.runtime._agent_assets``.
"""

from __future__ import annotations

import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from workshop.errors import ContractError


PRODUCT_RUN_CONSTITUTION = Path(".agents/product-run/AGENTS.md")
PRODUCT_RUN_SKILL = Path(".agents/skills/autonomous-workshop")
MAX_PRODUCT_RUN_INSTRUCTION_FILES = 128
MAX_PRODUCT_RUN_INSTRUCTION_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class ProductRunAgentAssets:
    """Validated product-run instruction sources."""

    constitution: Path
    skill_root: Path
    sha256: str
    source: str


def _regular_bytes(path: Path, *, label: str) -> bytes:
    try:
        before = path.lstat()
    except OSError as exc:
        raise ContractError("%s is missing" % label) from exc
    if path.is_symlink() or not stat.S_ISREG(before.st_mode):
        raise ContractError("%s must be a regular file" % label)
    if not 0 <= before.st_size <= MAX_PRODUCT_RUN_INSTRUCTION_BYTES:
        raise ContractError("%s exceeds its byte limit" % label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("%s cannot be read safely" % label) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)
        ):
            raise ContractError("%s changed while opening" % label)
        chunks = []
        remaining = MAX_PRODUCT_RUN_INSTRUCTION_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(content) > MAX_PRODUCT_RUN_INSTRUCTION_BYTES
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("%s changed while reading" % label)
        return content
    finally:
        os.close(descriptor)


def _validate_asset_root(root: Path, *, source: str) -> ProductRunAgentAssets:
    if root.is_symlink():
        raise ContractError("product-run agent asset root must not be a symlink")
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ContractError("product-run agent asset root is missing") from exc
    if not resolved.is_dir():
        raise ContractError("product-run agent asset root must be a directory")

    constitution = resolved / PRODUCT_RUN_CONSTITUTION
    skill_root = resolved / PRODUCT_RUN_SKILL
    constitution_bytes = _regular_bytes(
        constitution, label="product-run constitution"
    )
    if skill_root.is_symlink() or not skill_root.is_dir():
        raise ContractError("product-run skill root must be a real directory")
    if not (skill_root / "SKILL.md").is_file():
        raise ContractError("product-run skill must contain SKILL.md")

    digest = hashlib.sha256()
    total = len(constitution_bytes)
    count = 1
    digest.update(PRODUCT_RUN_CONSTITUTION.as_posix().encode("utf-8") + b"\0")
    digest.update(len(constitution_bytes).to_bytes(8, "big"))
    digest.update(constitution_bytes)
    for entry in sorted(skill_root.rglob("*"), key=lambda item: item.as_posix()):
        if entry.is_symlink():
            raise ContractError("product-run skill must not contain symlinks")
        if entry.is_dir():
            continue
        relative = entry.relative_to(resolved)
        content = _regular_bytes(entry, label=relative.as_posix())
        count += 1
        total += len(content)
        if count > MAX_PRODUCT_RUN_INSTRUCTION_FILES:
            raise ContractError("product-run instructions contain too many files")
        if total > MAX_PRODUCT_RUN_INSTRUCTION_BYTES:
            raise ContractError("product-run instructions exceed their byte limit")
        digest.update(relative.as_posix().encode("utf-8") + b"\0")
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return ProductRunAgentAssets(
        constitution=constitution,
        skill_root=skill_root,
        sha256=digest.hexdigest(),
        source=source,
    )


def product_run_agent_assets(
    repository_root: Optional[Path] = None,
    *,
    package_file: Optional[Path] = None,
) -> ProductRunAgentAssets:
    """Return source-checkout assets or the installed wheel snapshot.

    Passing ``repository_root`` is explicit and fail-closed. Without it, the
    source checkout is preferred only when both canonical product-run inputs
    exist beside this module's repository. Installed copies use the packaged
    snapshot and never fall back to a root builder ``AGENTS.md``.
    """

    if repository_root is not None:
        return _validate_asset_root(Path(repository_root), source="repository")

    module = Path(package_file or __file__).resolve()
    package_runtime = module.parent
    if len(package_runtime.parents) >= 3:
        source_root = package_runtime.parents[2]
        if (
            (source_root / PRODUCT_RUN_CONSTITUTION).is_file()
            and (source_root / PRODUCT_RUN_SKILL / "SKILL.md").is_file()
        ):
            return _validate_asset_root(source_root, source="repository")

    packaged_root = package_runtime / "_agent_assets"
    return _validate_asset_root(packaged_root, source="package")
