"""Locate the exact product-run constitution and workflow skill.

Repository builder instructions are deliberately not part of this asset set.
Source checkouts use the canonical ``.agents`` files directly; built wheels
carry a byte-for-byte snapshot under ``workshop.runtime._agent_assets``.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

from workshop.errors import ContractError


PRODUCT_RUN_CONSTITUTION = Path(".agents/product-run/AGENTS.md")
PRODUCT_RUN_SKILL = Path(".agents/product-run/.agents/skills/autonomous-workshop")
MAX_PRODUCT_RUN_INSTRUCTION_FILES = 128
MAX_PRODUCT_RUN_INSTRUCTION_BYTES = 2 * 1024 * 1024
_INVENTOR_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")
_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


@dataclass(frozen=True)
class ProductRunAgentAssets:
    """Validated product-run instruction sources."""

    constitution: Path
    skill_root: Path
    sha256: str
    source: str


def _taste_discovery_fields(taste_bytes: bytes) -> tuple[str, str]:
    if (
        not isinstance(taste_bytes, bytes)
        or not 1 <= len(taste_bytes) <= MAX_PRODUCT_RUN_INSTRUCTION_BYTES
    ):
        raise ContractError("Inventor Taste bytes must be non-empty and bounded")
    try:
        lines = taste_bytes.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ContractError("Inventor Taste bytes must be UTF-8") from exc
    if len(lines) < 4 or lines[0] != "---" or lines[3] != "---":
        raise ContractError(
            "Inventor Taste must begin with exact name and description frontmatter"
        )
    values: dict[str, str] = {}
    for expected, line in zip(("name", "description"), lines[1:3]):
        key, separator, raw = line.partition(":")
        if not separator or key != expected:
            raise ContractError(
                "Inventor Taste frontmatter must contain name then description"
            )
        scalar = raw.strip()
        if scalar.startswith('"'):
            try:
                value = json.loads(scalar)
            except ValueError as exc:
                raise ContractError(
                    "Inventor Taste frontmatter contains invalid quoted text"
                ) from exc
        else:
            if not scalar or scalar[0] in "'|>&*!{}[]":
                raise ContractError(
                    "Inventor Taste frontmatter must use bounded plain or JSON text"
                )
            value = scalar
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > 1024
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
            or '"""' in value
        ):
            raise ContractError(
                "Inventor Taste discovery text must be bounded and control-free"
            )
        values[key] = value.strip()
    return values["name"], values["description"]


def inventor_custom_agent_bytes(
    inventor_id: str,
    taste_bytes: bytes,
    *,
    skill_names: Sequence[str],
) -> bytes:
    """Return the canonical minimal project-scoped Codex Inventor TOML.

    The custom agent inherits the parent Codex model, tools, sandbox, and
    approvals.  It receives only a discoverable name and bounded instructions
    to read the exact host-materialized roster and skill bytes.
    """

    if (
        not isinstance(inventor_id, str)
        or _INVENTOR_ID.fullmatch(inventor_id) is None
    ):
        raise ContractError("Inventor id is not a valid Codex custom-agent name")
    if isinstance(skill_names, (str, bytes)):
        raise ContractError("Inventor skill names must be a sequence")
    names = tuple(skill_names)
    if (
        not 1 <= len(names) <= 8
        or names != tuple(sorted(names))
        or len(names) != len(set(names))
        or any(
            not isinstance(name, str) or _SKILL_NAME.fullmatch(name) is None
            for name in names
        )
        or "%s-inventor" % inventor_id not in names
    ):
        raise ContractError(
            "Inventor skills must be sorted, unique, and include <id>-inventor"
        )
    name, taste_description = _taste_discovery_fields(taste_bytes)
    description = "%s: %s" % (name, taste_description)
    primary = "%s-inventor" % inventor_id
    instruction_lines = [
        "You are %s, an Autonomous Workshop Inventor and a standard native Codex subagent."
        % name,
        "Handle only the bounded candidate or selected-Inventor task delegated by the root Workshop Manager.",
        "Before acting, read catalog/inventors/%s/inventor.json, catalog/inventors/%s/TASTE.md, and .agents/skills/%s/SKILL.md."
        % (inventor_id, inventor_id, primary),
    ]
    additional = tuple(skill_name for skill_name in names if skill_name != primary)
    if additional:
        instruction_lines.append(
            "Also read the additional declared Inventor skills: %s."
            % ", ".join(
                ".agents/skills/%s/SKILL.md" % skill_name
                for skill_name in additional
            )
        )
    instruction_lines.extend(
        (
            "Treat the exact Taste bytes as creative judgment and the Inventor skill as your specialist method.",
            "Use shared Workshop skills when their domains apply; do not duplicate their tools.",
            "Return evidence, artifacts, tradeoffs, and unresolved tensions to the Manager.",
            "You are not the Workshop Manager: do not orchestrate other agents or the Workshop lifecycle.",
            "Do not advance lifecycle gates or invoke the stage finalizer.",
            "Do not perform external effects.",
        )
    )
    instructions = "\n".join(instruction_lines)
    if len(description) > 1024 or len(instructions) > 8192:
        raise ContractError("custom Inventor agent text exceeds its limit")
    return (
        "name = %s\n" % json.dumps(inventor_id, ensure_ascii=False)
        + "description = %s\n" % json.dumps(description, ensure_ascii=False)
        + "developer_instructions = %s\n"
        % json.dumps(instructions, ensure_ascii=False)
    ).encode("utf-8")


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
