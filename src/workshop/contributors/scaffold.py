"""Create a lean persona for the shared native Workshop agent."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional

from workshop.errors import ContractError, StateConflict
from workshop.product import PLAYTHING_LANES


_ID = re.compile(r"^(?=.{2,63}$)[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")

# Accepted only for old callers. New callers choose an explicit plaything lane.
_LEGACY_TEMPLATES = {
    "board-game": "invented-games",
    "physical-product": "moving-machines",
    "custom": "little-worlds",
}

_LANE_GUIDANCE = {
    "classics-made-yours": (
        "Begin with a public-domain or properly licensed classic whose rules are "
        "already known. The invention is the Wish-shaped physical set—its pieces, "
        "board, materials, story, and personal details—not unnecessary rules churn."
    ),
    "invented-games": (
        "Invented games are experimental rules craft. Make the rules complete and "
        "executable, then Playtest at least 1,000 seeded games with optimizing, "
        "social, exploratory, and adversarial AI players. Customer reactions arrive "
        "after Deliver as Reviews and may improve a future Make."
    ),
    "moving-machines": (
        "Make motion the magic: one legible mechanism should invite a hand, reward "
        "repetition, and feel better in the exact printed object than in a render."
    ),
    "holdable-science": (
        "Turn a real mathematical or scientific phenomenon into something a person "
        "can hold, manipulate, and understand through physical cause and effect."
    ),
    "little-worlds": (
        "Build a specific character, scene, vehicle, or tiny world whose geometry "
        "carries the person's Wish instead of resembling a generic collectible."
    ),
}


def _display_text(value: str, label: str, maximum: int) -> str:
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


def _files(
    inventor_id: str,
    name: str,
    description: str,
    lane: str,
    *,
    taste_content: Optional[str] = None,
) -> Dict[str, str]:
    manifest = {
        "schema_version": 6,
        "id": inventor_id,
        "status": "experimental",
        "capabilities": [lane],
        "source": {"kind": "local"},
    }
    generated_taste = """---
name: {name_header}
description: {description_header}
---
# {name}'s Taste

This is {name}'s human-owned creative constitution for the **{lane}** lane.
The native Workshop agent reads these exact bytes after Match. It may propose
changes from verified outcomes, but it must not silently rewrite what this
inventor values.

## North star

Create {description} for grown-ups (14+) that invite play, surprise, and return
visits. Nothing may be merely useful: a useful Wish receives the playful version.

## The product bar

The finished object must answer: **why couldn't someone have bought this before
this Wish?** The Wish must materially shape its geometry, mechanism, rules,
secret, or little world. Reject generic figurines, stock-like trinkets, and
anything that is effectively the same object for everyone.

## Lane promise

{lane_guidance}

## Starting preferences

- Cool beats cute. Charm is welcome only when the idea is specific and surprising.
- Give every object one clear signature interaction, character, or secret.
- Prefer a recognizable silhouette and satisfying physical behavior over ornament.
- Make the first delightful moment easy to discover without coaching.
- Treat printability, assembly, safety, and truthful presentation as part of beauty.
- Let artifact-bound Playtest evidence improve the product without averaging away
  this inventor's point of view.

## Define before autonomous release

- Which three qualities should make this inventor's work recognizable without a logo?
- Which familiar themes, shapes, mechanics, or gimmicks are instant rejects?
- What should a person feel in the first ten seconds and on the tenth play?
- What physical and human evidence is strong enough to justify a Taste proposal?
""".format(
        name=name,
        name_header=json.dumps(name, ensure_ascii=False),
        description=description,
        description_header=json.dumps(description, ensure_ascii=False),
        lane=lane,
        lane_guidance=_LANE_GUIDANCE[lane],
    )
    return {
        "inventor.json": json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        "TASTE.md": generated_taste if taste_content is None else taste_content,
    }


def scaffold_inventor(
    root: Path,
    inventor_id: str,
    name: str,
    niche: str,
    *,
    lane: Optional[str] = None,
    level: str = "taste-only",
    template: Optional[str] = None,
) -> Path:
    """Compatibility wrapper for the former ``workshop new`` command."""

    Path(root).mkdir(parents=True, exist_ok=True)
    return create_inventor(
        root,
        inventor_id,
        name,
        niche,
        lane=lane,
        level=level,
        template=template,
        run_checks=False,
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
    lane: Optional[str] = None,
    level: str = "taste-only",
    template: Optional[str] = None,
    taste_path: Optional[Path] = None,
    run_checks: bool = True,
) -> Path:
    """Atomically add one validated native persona to an inventor collection.

    A persona is data, not a Python worker: the published folder contains only
    ``inventor.json`` and exact ``TASTE.md`` bytes. ``run_checks`` remains as a
    compatibility argument, but all validation is static and executes no
    contribution code.
    """

    requested_root = Path(root)
    if requested_root.is_symlink():
        raise ContractError("inventor collection must not be a symlink: %s" % requested_root)
    try:
        root = requested_root.resolve(strict=True)
    except OSError as exc:
        raise ContractError(
            "inventor collection must already exist: %s" % requested_root
        ) from exc
    if not root.is_dir():
        raise ContractError("inventor collection must be a directory: %s" % root)
    if not _ID.fullmatch(inventor_id):
        raise ContractError("inventor id must match %s" % _ID.pattern)
    if type(run_checks) is not bool:
        raise ContractError("run_checks must be a boolean")

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
    if template is not None:
        if template not in _LEGACY_TEMPLATES:
            raise ContractError(
                "legacy inventor template must be one of %s"
                % sorted(_LEGACY_TEMPLATES)
            )
        legacy_lane = _LEGACY_TEMPLATES[template]
        if lane is not None and lane != legacy_lane:
            raise ContractError("--lane conflicts with legacy --template")
        lane = legacy_lane
    if lane not in PLAYTHING_LANES:
        raise ContractError(
            "inventor lane must be one of %s" % ", ".join(PLAYTHING_LANES)
        )
    if level != "taste-only":
        raise ContractError(
            "native inventor personas customize only TASTE.md; put reusable "
            "deterministic tools in the Workshop stage that owns them"
        )

    destination = root / inventor_id
    if destination.exists():
        raise StateConflict("inventor folder already exists: %s" % destination)

    has_existing_persona = any(
        child.is_symlink()
        or (
            child.is_dir()
            and (
                (child / "inventor.json").exists()
                or (child / "TASTE.md").exists()
            )
        )
        for child in root.iterdir()
    )
    if has_existing_persona:
        from workshop.contributors.contribution import validate_inventor_collection

        validate_inventor_collection(root)

    staging_root = Path(tempfile.mkdtemp(prefix=".%s." % inventor_id, dir=str(root)))
    temporary = staging_root / inventor_id
    temporary.mkdir(mode=0o755)
    try:
        for relative, content in _files(
            inventor_id,
            name,
            description,
            lane,
            taste_content=(source_taste.content if source_taste is not None else None),
        ).items():
            target = temporary / relative
            if relative == "TASTE.md":
                target.write_bytes(content.encode("utf-8"))
            else:
                target.write_text(content, encoding="utf-8")

        from workshop.contributors.contribution import (
            run_declared_checks,
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
                    "created inventor did not preserve the existing TASTE.md exactly"
                )
        if not problems and run_checks:
            problems = run_declared_checks(manifest)
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


__all__ = [
    "create_inventor",
    "prepare_inventor_collection",
    "scaffold_inventor",
]
