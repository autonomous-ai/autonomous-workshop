"""Box-ready Instructions and a verified private draft for an approved product."""

from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from typing import Any, Callable, Dict, Mapping, Optional, Sequence

from .artifacts import ArtifactEntry, ArtifactManifest, build_artifact_manifest
from .attribution import attribute_product_description
from .errors import AmbiguousEffectError, ContractError, EffectError
from .jobs import InstructionsContext, Need, ProductInstructions, WaitingFor
from .models import Receipt


REQUIRED_PRODUCT_IMAGES = ("hero", "play", "detail", "parts", "box")
INSTRUCTIONS_MANIFEST_FILENAME = "instructions-manifest.json"
_IMAGE_SUFFIXES = frozenset((".png", ".jpg", ".jpeg", ".webp"))
InstructionsSiteWriter = Callable[
    [InstructionsContext, Path, ArtifactManifest], Receipt
]


def _manifest_from_dict(value: Any) -> ArtifactManifest:
    """Rebuild a sealed manifest without trusting untyped persisted JSON."""

    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "artifact_sha256",
        "total_bytes",
        "created_at",
        "entries",
    }:
        raise ContractError("Instructions manifest is malformed")
    raw_entries = value.get("entries")
    if not isinstance(raw_entries, list):
        raise ContractError("Instructions manifest entries are malformed")
    entries = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping) or set(raw_entry) != {
            "path",
            "bytes",
            "sha256",
            "executable",
        }:
            raise ContractError("Instructions manifest entry is malformed")
        entries.append(
            ArtifactEntry(
                raw_entry["path"],
                raw_entry["bytes"],
                raw_entry["sha256"],
                raw_entry["executable"],
            )
        )
    return ArtifactManifest(
        value["schema_version"],
        value["artifact_sha256"],
        tuple(entries),
        value["total_bytes"],
        value["created_at"],
    )


def _manifest_path(root: Path) -> Path:
    # Workshop uses a directory literally named ``instructions``, yielding the
    # stable public filename ``instructions-manifest.json``.  Named test or
    # custom workspaces remain independent siblings instead of sharing a seal.
    return root.parent / (root.name + "-manifest.json")


def _write_manifest_once(root: Path, manifest: ArtifactManifest) -> None:
    """Durably seal Instructions before any externally visible site effect."""

    path = _manifest_path(root)
    if path.exists() or path.is_symlink():
        raise ContractError("Instructions manifest seal already exists")
    payload = json.dumps(
        manifest.to_dict(), indent=2, sort_keys=True, ensure_ascii=False
    ) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=".%s." % path.name, dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        # link(2) gives the seal create-if-absent semantics that replace(2)
        # cannot: another process can never replace an existing identity.
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ContractError("Instructions manifest seal already exists") from exc
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def sealed_instructions_manifest(root: Path) -> ArtifactManifest:
    """Load the immutable seal and prove the current tree is byte-for-byte exact."""

    root = Path(root)
    path = _manifest_path(root)
    if path.is_symlink() or not path.is_file():
        raise ContractError("sealed Instructions tree is missing its manifest")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Instructions manifest must be valid UTF-8 JSON") from exc
    manifest = _manifest_from_dict(value)
    current = build_artifact_manifest(root, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ContractError("sealed Instructions bytes changed while waiting")
    return manifest


def _site_paragraph(*parts: Any) -> str:
    """Build bounded plain copy for the site's curated product sections."""

    text = " ".join(
        " ".join(str(part).split())
        for part in parts
        if isinstance(part, str) and part.strip()
    ).strip()
    fillers = (
        "The images on this page stay tied to the exact approved design.",
        "AI players simulated the product and returned evidence-bound feedback before this page was written.",
        "Printing, hands-on quality checks, packing, and shipping remain part of Deliver.",
    )
    for sentence in fillers:
        if len(text) >= 180:
            break
        text = (text + " " + sentence).strip()
    if len(text) > 400:
        shortened = text[:399]
        boundary = shortened.rfind(" ")
        if boundary >= 180:
            shortened = shortened[:boundary]
        text = shortened.rstrip(" ,;:-") + "."
    if not 180 <= len(text) <= 400:
        raise ContractError("Instructions could not form bounded site copy")
    return text


def _safe_relative_file(root: Path, value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError("Instructions media %s must be a relative path" % label)
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or "\\" in value:
        raise ContractError(
            "Instructions media %s must stay inside the Instructions workspace" % label
        )
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError(
            "Instructions media %s is missing or outside the workspace" % label
        ) from exc
    if not resolved.is_file() or resolved.suffix.casefold() not in _IMAGE_SUFFIXES:
        raise ContractError(
            "Instructions media %s must be a PNG, JPEG, or WebP file" % label
        )
    return relative.as_posix()


def evidence_claims(context: InstructionsContext) -> Dict[str, Any]:
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
        raise ContractError("Instructions require non-empty Playtest evidence")
    return claims


class DefaultInstructions:
    """Build the box insert and save its product page as one Shop draft.

    The optional ``media_maker`` writes fixed-view product images into the given
    Instructions workspace and returns relative paths keyed by
    :data:`REQUIRED_PRODUCT_IMAGES`.  Keeping image generation behind this one
    callback lets every inventor share the page contract while the Workshop chooses
    render/image providers centrally.

    ``site_writer`` receives the unchanged context, the sealed Instructions root,
    and its content-addressed manifest.  It must create and enrich a private page
    draft, then return an authenticated :class:`~inventor_workshop.models.Receipt`
    from owner readback.  The Receipt details must include
    ``instructions_sha256`` equal to the supplied manifest's artifact hash.  This
    single binding covers product.json, INSTRUCTIONS.md, every fixed-view image,
    and the Playtest evidence identity recorded in product.json.
    """

    def __init__(
        self,
        media_maker: Optional[Callable[[InstructionsContext], Mapping[str, str]]] = None,
        site_writer: Optional[InstructionsSiteWriter] = None,
    ) -> None:
        self.media_maker = media_maker
        self.site_writer = site_writer

    def __call__(self, context: InstructionsContext) -> ProductInstructions:
        if not isinstance(context, InstructionsContext):
            raise ContractError(
                "DefaultInstructions requires an InstructionsContext"
            )
        context.assert_current()
        needs = []
        if self.media_maker is None:
            needs.append(
                Need(
                    "instructions",
                    "product-images",
                    "The product passed Playtest, but a truthful beautiful page "
                    "needs fixed-view renders.",
                    "Configure the shared Instructions renderer/image provider; "
                    "do not substitute concept art for product proof.",
                )
            )
        if self.site_writer is None:
            needs.append(
                Need(
                    "instructions",
                    "site-page",
                    "Instructions includes the product page, and it is not complete "
                    "until its private draft is proven in the Shop.",
                    "Configure the shared Instructions site writer with authenticated "
                    "draft readback; do not treat local files or an HTTP success as proof.",
                )
            )
        if needs:
            raise WaitingFor(*needs)
        # Narrow Optional callback types after the truthful capability check.
        assert self.media_maker is not None
        assert self.site_writer is not None
        root = context.workspace
        if root.exists():
            if root.is_symlink() or not root.is_dir() or any(root.iterdir()):
                raise ContractError("Instructions workspace must be fresh and empty")
        else:
            root.mkdir(parents=True, mode=0o700)
        raw_media = self.media_maker(context)
        # Rendering may be remote or long-running.  Refuse its output if the
        # product changed while those views were being made.
        context.assert_current()
        if not isinstance(raw_media, Mapping):
            raise ContractError("Instructions media maker must return a path mapping")
        media = {
            name: _safe_relative_file(root, raw_media.get(name), name)
            for name in REQUIRED_PRODUCT_IMAGES
        }
        if len(set(media.values())) != len(REQUIRED_PRODUCT_IMAGES):
            raise ContractError(
                "Instructions require a distinct file for every fixed image view"
            )
        claims = evidence_claims(context)
        title = str(context.made.product["title"])
        summary = attribute_product_description(
            context.made.product["summary"], context.taste.name
        )
        tabletop = context.blueprint.lane in (
            "classics-made-yours",
            "invented-games",
        )
        instructions_kind = "rulebook" if tabletop else "instructions"
        use_key = "how_to_play" if tabletop else "how_to_use"
        use_heading = "How to play" if tabletop else "How to use"
        fallback = (
            "Follow the included setup, turn, scoring, and end-of-game rules."
            if tabletop
            else "Follow the included setup, operation, and interaction instructions."
        )
        instructions = context.made.product.get("instructions", fallback)
        component_copy = ", ".join(
            str(item) for item in context.made.product.get("components", [])
        ) or "the exact parts listed in the product manifest"
        limitation_copy = " ".join(
            str(item) for item in context.made.product.get("limitations", [])
        )
        page = {
            "schema_version": 1,
            # This is desired content state, not evidence that the remote draft
            # exists.  The authenticated site Receipt below is the sole proof.
            "status": "ready",
            "title": title,
            "summary": summary,
            "lane": context.blueprint.lane,
            "audience": "grown-ups, 14 and up",
            "wish": context.wish.objective,
            "instructions_kind": instructions_kind,
            use_key: str(instructions),
            "what_arrives": context.made.product.get("components", []),
            "images": media,
            "product_artifact_sha256": context.made.artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                context.playtested.evidence.evidence_artifact_sha256
            ),
            "claims": claims,
            "limitations": context.made.product.get("limitations", []),
            "use_case": {
                "label": "Made from your wish",
                "body": _site_paragraph(
                    str(context.made.product["summary"]),
                    "It turns one person's request into this exact plaything instead of decorating a generic download.",
                ),
                "image": "hero",
            },
            "story_blocks": [
                {
                    "lead": use_heading,
                    "body": _site_paragraph(
                        str(instructions),
                        "The play image shows the intended interaction; detail and parts views show how the approved design is put together.",
                    ),
                    "hero_image": "play",
                    "pair_images": ["detail", "parts"],
                },
                {
                    "lead": "What arrives",
                    "body": _site_paragraph(
                        "The box contains %s." % component_copy,
                        limitation_copy,
                    ),
                    "hero_image": "box",
                    "pair_images": [],
                },
            ],
        }
        (root / "product.json").write_text(
            json.dumps(page, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        component_lines: Sequence[str]
        components = page["what_arrives"]
        if isinstance(components, list) and components:
            component_lines = tuple("- %s" % item for item in components)
        else:
            component_lines = ("- See the exact product manifest.",)
        limitations = page["limitations"]
        if isinstance(limitations, list) and limitations:
            limitation_lines = tuple("- %s" % item for item in limitations)
        else:
            limitation_lines = ("- Follow the material and age guidance on the box.",)
        markdown = "\n".join(
            (
                "# %s" % title,
                "",
                summary,
                "",
                "## %s" % use_heading,
                "",
                str(instructions),
                "",
                "## What's in the box",
                "",
                *component_lines,
                "",
                "## Care and safety",
                "",
                *limitation_lines,
                "",
            )
        )
        (root / "INSTRUCTIONS.md").write_text(markdown, encoding="utf-8")
        manifest = build_artifact_manifest(root, created_at="content-addressed")
        _write_manifest_once(root, manifest)
        context.assert_current()
        site_receipt = self._write_site(context, root, manifest)
        return ProductInstructions.from_root(
            root,
            context.made.artifact_sha256,
            "INSTRUCTIONS.md",
            claims,
            site_receipt,
        )

    def resume(self, context: InstructionsContext) -> ProductInstructions:
        """Resume only the site portion of one already sealed Instructions job.

        Media, copy, and paper instructions are intentionally never regenerated.
        The Workshop event log binds the manifest identity before this method is
        called; this method independently rechecks both that seal and its exact
        Made/Playtested context before retrying the idempotent site writer.
        """

        if not isinstance(context, InstructionsContext):
            raise ContractError(
                "DefaultInstructions.resume requires an InstructionsContext"
            )
        context.assert_current()
        if self.site_writer is None:
            raise WaitingFor(
                Need(
                    "instructions",
                    "site-page",
                    "The sealed Instructions page still has no configured site writer.",
                    "Configure the shared Instructions site writer with authenticated readback, then resume this exact job.",
                )
            )
        root = context.workspace
        if root.is_symlink() or not root.is_dir() or not any(root.iterdir()):
            raise ContractError("resumed Instructions require a non-empty sealed tree")
        manifest = sealed_instructions_manifest(root)
        try:
            page_value = json.loads((root / "product.json").read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(
                "sealed Instructions product.json must be valid UTF-8 JSON"
            ) from exc
        if not isinstance(page_value, Mapping):
            raise ContractError("sealed Instructions product.json must be an object")
        claims = evidence_claims(context)
        expected_summary = attribute_product_description(
            context.made.product["summary"], context.taste.name
        )
        expected = {
            "title": str(context.made.product["title"]),
            "summary": expected_summary,
            "lane": context.blueprint.lane,
            "wish": context.wish.objective,
            "product_artifact_sha256": context.made.artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                context.playtested.evidence.evidence_artifact_sha256
            ),
            "claims": claims,
        }
        if any(page_value.get(key) != value for key, value in expected.items()):
            raise ContractError(
                "sealed Instructions tree belongs to a different Wish, Taste, Make, or Playtest"
            )
        site_receipt = self._write_site(context, root, manifest)
        return ProductInstructions.from_root(
            root,
            context.made.artifact_sha256,
            "INSTRUCTIONS.md",
            claims,
            site_receipt,
        )

    def _write_site(
        self,
        context: InstructionsContext,
        root: Path,
        manifest: ArtifactManifest,
    ) -> Receipt:
        """Run the durable site writer and translate retry states truthfully."""

        assert self.site_writer is not None
        context.assert_current()
        try:
            site_receipt = self.site_writer(context, root, manifest)
        except WaitingFor:
            raise
        except AmbiguousEffectError as exc:
            raise WaitingFor(
                Need(
                    "instructions",
                    "site-reconciliation",
                    "The site may have accepted part or all of this exact Instructions page, so retrying could duplicate it.",
                    "Reconcile the recorded site intent with authenticated readback, then resume this same Instructions job.",
                )
            ) from exc
        except EffectError as exc:
            raise WaitingFor(
                Need(
                    "instructions",
                    "site-page",
                    "The site rejected this exact Instructions page before a verified private draft was recorded.",
                    "Correct the site account, copy, media, or draft input and resume this same Instructions job.",
                )
            ) from exc
        context.assert_current()
        if not isinstance(site_receipt, Receipt):
            raise ContractError(
                "Instructions site writer must return an authenticated Receipt"
            )
        return site_receipt


__all__ = [
    "DefaultInstructions",
    "INSTRUCTIONS_MANIFEST_FILENAME",
    "InstructionsSiteWriter",
    "REQUIRED_PRODUCT_IMAGES",
    "evidence_claims",
    "sealed_instructions_manifest",
]
