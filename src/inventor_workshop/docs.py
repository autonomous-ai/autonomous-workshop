"""Truthful product-page Docs for an approved toy or board game."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from .errors import ContractError
from .jobs import DocsContext, Need, ProductDocs, WaitingFor


REQUIRED_PRODUCT_IMAGES = ("hero", "play", "detail", "parts", "box")
_IMAGE_SUFFIXES = frozenset((".png", ".jpg", ".jpeg", ".webp"))


def _safe_relative_file(root: Path, value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError("Docs media %s must be a relative path" % label)
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or "\\" in value:
        raise ContractError("Docs media %s must stay inside the Docs workspace" % label)
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError("Docs media %s is missing or outside the workspace" % label) from exc
    if not resolved.is_file() or resolved.suffix.casefold() not in _IMAGE_SUFFIXES:
        raise ContractError("Docs media %s must be a PNG, JPEG, or WebP file" % label)
    return relative.as_posix()


def evidence_claims(context: DocsContext) -> Dict[str, Any]:
    """Expose exactly what Playtest proved; never upgrade evidence in copy."""

    claims: Dict[str, Any] = {}
    for result in context.playtested.evidence.results:
        evidence_class = result.evidence.get("evidence_class", "unspecified")
        raw_claims = result.evidence.get("claims", [])
        if isinstance(raw_claims, str):
            raw_claims = [raw_claims]
        if not isinstance(raw_claims, list) or not all(
            isinstance(item, str) and item.strip() for item in raw_claims
        ):
            raw_claims = []
        claims[result.playtest_id] = {
            "passed": result.passed,
            "evidence_class": evidence_class,
            "claims": raw_claims,
            "evidence_ref": result.evidence_ref,
            "evidence_sha256": result.evidence_sha256,
            "evaluator": result.evaluator,
            "evaluator_version": result.evaluator_version,
        }
    if not claims:
        raise ContractError("Docs require non-empty Playtest evidence")
    return claims


class DefaultDocs:
    """Build a complete private page from exact artifacts and generated media.

    The optional ``media_maker`` writes fixed-view product images into the given
    Docs workspace and returns relative paths keyed by
    :data:`REQUIRED_PRODUCT_IMAGES`.  Keeping image generation behind this one
    callback lets every elf share the page contract while the Workshop chooses
    render/image providers centrally.
    """

    def __init__(
        self,
        media_maker: Optional[Callable[[DocsContext], Mapping[str, str]]] = None,
    ) -> None:
        self.media_maker = media_maker

    def __call__(self, context: DocsContext) -> ProductDocs:
        if not isinstance(context, DocsContext):
            raise ContractError("DefaultDocs requires a DocsContext")
        context.assert_current()
        if self.media_maker is None:
            raise WaitingFor(
                Need(
                    "docs",
                    "product-images",
                    "The product passed Playtest, but a truthful beautiful page needs fixed-view renders.",
                    "Configure the shared Docs renderer/image provider; do not substitute concept art for product proof.",
                )
            )
        root = context.workspace
        if root.exists():
            if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
                raise ContractError("Docs workspace must be fresh and empty")
        else:
            root.mkdir(parents=True, mode=0o700)
        raw_media = self.media_maker(context)
        # Rendering may be remote or long-running.  Refuse its output if the
        # product changed while those views were being made.
        context.assert_current()
        if not isinstance(raw_media, Mapping):
            raise ContractError("Docs media maker must return a path mapping")
        media = {
            name: _safe_relative_file(root, raw_media.get(name), name)
            for name in REQUIRED_PRODUCT_IMAGES
        }
        if len(set(media.values())) != len(REQUIRED_PRODUCT_IMAGES):
            raise ContractError("Docs require a distinct file for every fixed image view")
        claims = evidence_claims(context)
        title = str(context.made.product["title"])
        summary = str(context.made.product["summary"])
        instructions = context.made.product.get(
            "instructions",
            "Use the included rules or interaction guide for this plaything.",
        )
        page = {
            "schema_version": 1,
            "status": "private",
            "title": title,
            "summary": summary,
            "lane": context.blueprint.lane,
            "audience": "grown-ups, 14 and up",
            "wish": context.wish.objective,
            "how_to_play": str(instructions),
            "what_arrives": context.made.product.get("components", []),
            "images": media,
            "product_artifact_sha256": context.made.artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                context.playtested.evidence.evidence_artifact_sha256
            ),
            "claims": claims,
            "limitations": context.made.product.get("limitations", []),
        }
        (root / "product.json").write_text(
            json.dumps(page, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        claim_lines = []
        for name, record in sorted(claims.items()):
            stated = ", ".join(record["claims"]) or "no public claim"
            claim_lines.append(
                "- %s (%s): %s" % (name, record["evidence_class"], stated)
            )
        component_lines: Sequence[str]
        components = page["what_arrives"]
        if isinstance(components, list) and components:
            component_lines = tuple("- %s" % item for item in components)
        else:
            component_lines = ("- See the exact product manifest.",)
        markdown = "\n".join(
            (
                "# %s" % title,
                "",
                summary,
                "",
                "## How to play",
                "",
                str(instructions),
                "",
                "## What arrives",
                "",
                *component_lines,
                "",
                "## What Playtest actually proved",
                "",
                *claim_lines,
                "",
                "This is a private Workshop draft until its exact product and page "
                "are approved for Deliver.",
                "",
            )
        )
        (root / "README.md").write_text(markdown, encoding="utf-8")
        return ProductDocs.from_root(
            root,
            context.made.artifact_sha256,
            "product.json",
            claims,
        )


__all__ = [
    "DefaultDocs",
    "REQUIRED_PRODUCT_IMAGES",
    "evidence_claims",
]
