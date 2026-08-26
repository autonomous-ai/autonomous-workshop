"""Atomically create one native Inventor bundle."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Optional

from workshop.contributors.extensions import fingerprint_extension_skill
from workshop.errors import ContractError, StateConflict


# The generated ``<id>-inventor`` skill name must stay within Codex's 63-char
# skill-name contract.
_ID = re.compile(r"^(?=.{2,54}$)[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def _display_text(value: Optional[str], label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ContractError("inventor %s must be a string" % label)
    normalized = value.strip()
    if (
        not normalized
        or len(normalized) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in normalized)
    ):
        raise ContractError(
            "inventor %s must be one control-free line of at most %d characters"
            % (label, maximum)
        )
    return normalized


def _generated_taste(name: str, description: str) -> str:
    return """---
name: {name_header}
description: {description_header}
---
# {name}'s Taste

This is {name}'s human-owned creative constitution. The native Workshop agent
receives these exact bytes after Match. It may propose changes from verified
outcomes, but it must not silently rewrite what this Inventor values.

## North star

Create {description}. Let the exact Wish and this Taste determine the product
form; do not force every request through one catalog category. The result should
invite play, surprise, and return visits. Nothing may be merely useful: a useful
Wish receives the playful version.

## The product bar

The finished object must answer: **why couldn't someone have bought this before
this Wish?** The Wish must materially shape its geometry, mechanism, rules,
secret, or little world. Reject generic figurines, stock-like trinkets, and
anything that is effectively the same object for everyone.

## Starting preferences

- Cool beats cute. Charm is welcome only when the idea is specific and surprising.
- Give every object one clear signature interaction, character, or secret.
- Prefer a recognizable silhouette and satisfying physical behavior over ornament.
- Make the first delightful moment easy to discover without coaching.
- Treat printability, assembly, safety, and truthful presentation as part of beauty.
- Let artifact-bound Playtest evidence improve the product without averaging away
  this Inventor's point of view.

## Define before autonomous release

- Which three qualities should make this Inventor's work recognizable without a logo?
- Which familiar themes, shapes, mechanics, or gimmicks are instant rejects?
- What should a person feel in the first ten seconds and on the tenth play?
- What physical and human evidence is strong enough to justify a Taste proposal?
""".format(
        name=name,
        name_header=json.dumps(name, ensure_ascii=False),
        description=description,
        description_header=json.dumps(description, ensure_ascii=False),
    )


def _inventor_skill(inventor_id: str, name: str) -> str:
    skill_name = "%s-inventor" % inventor_id
    return """---
name: {skill_name}
description: Apply {name}'s selected-Inventor method to an exact Wish inside one Workshop run.
---

# {name} Inventor

Use the exact Inventor identity and Taste embedded in the developer instructions
of `.codex/agents/{inventor_id}.toml` as the creative constitution. Do not
rediscover or substitute identity from another file. Read the current
`STAGE.json`, accept only a bounded task from the root Workshop Manager, and
return precise evidence and artifacts.

Contribute specialist judgment across Match, Invent, Make, Playtest, and
Release as requested. Use shared Workshop skills for reusable CAD and other
domain tooling. Do not invoke the stage finalizer, advance a lifecycle gate,
launch another orchestrator, perform external effects, or claim evidence that
was not produced for the exact artifact under review.
""".format(
        skill_name=skill_name,
        inventor_id=inventor_id,
        name=name,
    )


def prepare_inventor_collection(root: Path) -> Path:
    """Return ``inventors/`` for creation, bootstrapping it when needed."""

    requested = Path(root)
    if requested.is_symlink():
        raise ContractError("inventor creation root must not be a symlink: %s" % requested)
    try:
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError(
            "inventor creation root must already exist: %s" % requested
        ) from exc
    if not resolved.is_dir():
        raise ContractError("inventor creation root must be a directory: %s" % resolved)
    collection = resolved if resolved.name == "inventors" else resolved / "inventors"
    if collection.is_symlink():
        raise ContractError("inventors collection must not be a symlink: %s" % collection)
    if collection.exists() and not collection.is_dir():
        raise ContractError("inventors collection must be a directory: %s" % collection)
    collection.mkdir(mode=0o755, exist_ok=True)
    return collection.resolve(strict=True)


def create_inventor(
    root: Path,
    inventor_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    *,
    taste_path: Optional[Path] = None,
) -> Path:
    """Atomically add ``TASTE.md``, a native skill, and their v8 manifest."""

    requested_root = Path(root)
    if requested_root.is_symlink():
        raise ContractError("inventor collection must not be a symlink: %s" % requested_root)
    try:
        collection = requested_root.resolve(strict=True)
    except OSError as exc:
        raise ContractError(
            "inventor collection must already exist: %s" % requested_root
        ) from exc
    if not collection.is_dir():
        raise ContractError("inventor collection must be a directory: %s" % collection)
    if _ID.fullmatch(inventor_id) is None:
        raise ContractError("inventor id must match %s" % _ID.pattern)

    source_taste = None
    if taste_path is not None:
        requested_taste = Path(taste_path)
        if requested_taste.name != "TASTE.md" or requested_taste.is_symlink():
            raise ContractError(
                "existing Taste must be a regular file named TASTE.md: %s"
                % requested_taste
            )
        try:
            resolved_taste = requested_taste.resolve(strict=True)
        except OSError as exc:
            raise ContractError(
                "cannot resolve existing TASTE.md: %s" % requested_taste
            ) from exc
        from workshop.contributors.taste import load_taste

        source_taste = load_taste(resolved_taste.parent)
        if source_taste.path != resolved_taste:
            raise ContractError(
                "existing Taste must be the root TASTE.md in its folder: %s"
                % requested_taste
            )
        if name is not None and _display_text(name, "name", 200) != source_taste.name:
            raise ContractError(
                "inventor name conflicts with the name in the existing TASTE.md"
            )
        if (
            description is not None
            and _display_text(description, "description", 500)
            != source_taste.description
        ):
            raise ContractError(
                "inventor description conflicts with the description in the existing TASTE.md"
            )
        name = source_taste.name
        description = source_taste.description

    name = _display_text(name, "name", 200)
    description = _display_text(description, "description", 500)

    destination = collection / inventor_id
    if destination.exists() or destination.is_symlink():
        raise StateConflict("inventor folder already exists: %s" % destination)

    has_existing_inventor = any(
        child.is_symlink()
        or (
            child.is_dir()
            and (
                (child / "inventor.json").exists()
                or (child / "TASTE.md").exists()
            )
        )
        for child in collection.iterdir()
    )
    if has_existing_inventor:
        from workshop.contributors.contribution import validate_inventor_collection

        validate_inventor_collection(collection)

    staging_root = Path(
        tempfile.mkdtemp(prefix=".%s." % inventor_id, dir=str(collection))
    )
    temporary = staging_root / inventor_id
    temporary.mkdir(mode=0o755)
    try:
        taste_content = (
            source_taste.content
            if source_taste is not None
            else _generated_taste(name, description)
        )
        (temporary / "TASTE.md").write_bytes(taste_content.encode("utf-8"))

        skill_name = "%s-inventor" % inventor_id
        skill_root = temporary / "skills" / skill_name
        skill_root.mkdir(parents=True, mode=0o755)
        (skill_root / "SKILL.md").write_text(
            _inventor_skill(inventor_id, name), encoding="utf-8"
        )
        fingerprint = fingerprint_extension_skill(
            skill_root.resolve(strict=True), expected_name=skill_name
        )
        manifest_document = {
            "schema_version": 8,
            "id": inventor_id,
            "status": "experimental",
            "source": {"kind": "local"},
            "extensions": [
                {
                    "kind": "codex-skill",
                    "name": skill_name,
                    "path": "skills/%s" % skill_name,
                    "artifact_sha256": fingerprint.artifact_sha256,
                }
            ],
        }
        (temporary / "inventor.json").write_text(
            json.dumps(manifest_document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        from workshop.contributors.contribution import (
            validate_contribution,
            validate_inventor_collection,
        )
        from workshop.contributors.manifest import load_manifest
        from workshop.contributors.taste import load_taste

        manifest = load_manifest(temporary / "inventor.json")
        problems = validate_contribution(manifest)
        generated_taste = load_taste(temporary)
        if source_taste is not None:
            try:
                source_taste.assert_current()
            except ContractError as exc:
                raise ContractError(
                    "existing TASTE.md changed during Inventor creation; retry"
                ) from exc
            if (
                generated_taste.sha256 != source_taste.sha256
                or generated_taste.content != source_taste.content
            ):
                raise ContractError(
                    "created Inventor did not preserve the existing TASTE.md exactly"
                )
        if problems:
            raise ContractError(
                "inventor creation failed validation: %s" % "; ".join(problems)
            )

        validate_inventor_collection(staging_root, required_routable_id=inventor_id)
        if source_taste is not None:
            try:
                source_taste.assert_current()
            except ContractError as exc:
                raise ContractError(
                    "existing TASTE.md changed during Inventor creation; retry"
                ) from exc
        os.replace(str(temporary), str(destination))
    finally:
        if staging_root.exists():
            shutil.rmtree(str(staging_root))
    return destination


__all__ = ["create_inventor", "prepare_inventor_collection"]
