"""Authenticated Shop Door transport and durable Shop send fencing."""

from __future__ import annotations

import io
import hashlib
import json
import mimetypes
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path
from pathlib import PurePosixPath
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from .artifacts import (
    ArtifactManifest,
    assert_packable_content,
    build_artifact_manifest,
    build_pack,
)
from .attribution import attribute_product_description
from .pack import _load_pack, _validate_pack_bytes
from .errors import (
    AmbiguousPublishError,
    ContractError,
    PublishError,
    ReceiptError,
    StateConflict,
)
from .models import PublicationOutcome, PublicationReceipt, require_sha256
from .store import InventorStore

DEFAULT_SHOP_API = "https://panda-social-api.autonomous.ai/api/v1"
DEFAULT_SHOP_PAGE_BASE = "https://www.autonomous.ai/factory/product"
SHOP_USER_AGENT = "Mozilla/5.0 (compatible; AutonomousWorkshop/1.0)"
HTTP_TIMEOUT_SECONDS = 120
Transport = Callable[[str, str, Mapping[str, str], Optional[bytes], int], "HttpResponse"]

# Only response classes that prove the server rejected the request before
# applying it may reopen a non-idempotent effect.  Redirects, timeouts,
# conflicts, throttling, and unexpected success statuses remain ambiguous.
PROVEN_NO_EFFECT_STATUSES = frozenset(
    (400, 401, 403, 404, 405, 406, 410, 411, 412, 413, 414, 415, 416, 417, 421, 422, 426, 428, 431, 451)
)
SHOP_LISTING_STRING_LIMITS = {
    "title": 300,
    "description": 2_000,
    "category": 100,
    "prompt": 50_000,
    "license": 60,
}
FACTORY_STORY_PROMPT_LIMIT = SHOP_LISTING_STRING_LIMITS["prompt"]
WORKSHOP_SHOP_LISTING_FIELDS = frozenset(
    (
        "_workshop_artifact_sha256",
        "_workshop_handoff_artifact_sha256",
        "_workshop_instructions_sha256",
        "_workshop_playtest_evidence_sha256",
        "_workshop_owner_id",
        "_workshop_api_origin",
    )
)
LEGACY_SHOP_LISTING_FIELDS = frozenset(
    (
        "_foundation_artifact_sha256",
        "_foundation_owner_id",
        "_foundation_api_origin",
        "_core_artifact_sha256",
        "_core_owner_id",
        "_core_api_origin",
    )
)
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
SHOP_CATEGORY_BY_LANE = {
    "classics-made-yours": "toys",
    "invented-games": "toys",
    "moving-machines": "toys",
    "holdable-science": "toys",
    "little-worlds": "toys",
}
# These trees are useful while Making and Playtesting, but they are not part of
# the model handoff.  In particular, the Factory importer treats PNGs below a
# ``review``/``*_review``/``renders`` directory as authoritative covers.  A
# local inspection render must never pre-empt Factory's server-owned product
# media pipeline.
SHOP_MODEL_HANDOFF_EXCLUDED_DIRS = frozenset(
    (
        "attachments",
        "gallery",
        "images",
        "marketing",
        "marketing-media",
        "measure",
        "media",
        "page",
        "page-copy",
        "previews",
        "product-media",
        "review",
        "renders",
        "story-blocks",
        "thumbnails",
        "use-case",
        "validation",
    )
)
SHOP_INSTRUCTIONS_FORBIDDEN_MEDIA_SUFFIXES = frozenset(
    (
        ".avi",
        ".avif",
        ".bmp",
        ".gif",
        ".heic",
        ".jpeg",
        ".jpg",
        ".m4v",
        ".mkv",
        ".mov",
        ".mp4",
        ".png",
        ".svg",
        ".tif",
        ".tiff",
        ".webm",
        ".webp",
    )
)
FACTORY_OUTPUT_FIELD_NAMES = frozenset(
    ("attachments", "images", "story_blocks", "use_case")
)


def _canonical_sha256(value: Any) -> str:
    try:
        payload = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("Shop request must contain finite JSON values") from exc
    return hashlib.sha256(payload).hexdigest()


def _assert_shop_importable_pack(content: bytes) -> None:
    """Mirror the Shop's shallow design discovery before bearer-bound HTTP.

    Workshop Packs contain the Made artifact at archive root.  The deployed
    importer recognizes that root only when it has a top-level Python source
    containing ``def gen_step``, or a usable ``project.json`` plus a root
    primary model named ``assembled.stl`` (preferred by Factory) or
    ``<project-id>.stl``. Checking the exact sealed Pack prevents both rejected
    imports and accidental selection of a small nested part. Critically, this
    guard never patches un-Playtested bytes into the archive after Make.
    """

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = set(archive.namelist())
            top_level_generator = False
            for name in sorted(names):
                if not name.casefold().endswith(".py"):
                    continue
                if b"def gen_step" not in archive.read(name):
                    continue
                if "/" in name:
                    raise ContractError(
                        "Shop import would narrow this artifact to nested generator %s"
                        % name
                    )
                top_level_generator = True
            if top_level_generator:
                return
            if "project.json" in names:
                try:
                    project = json.loads(
                        archive.read("project.json").decode("utf-8")
                    )
                except (UnicodeDecodeError, ValueError):
                    project = None
                if isinstance(project, Mapping):
                    project_id = project.get("id")
                    if (
                        isinstance(project_id, str)
                        and re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", project_id)
                        and (
                            "assembled.stl" in names
                            or (project_id + ".stl") in names
                        )
                    ):
                        return
    except (KeyError, OSError, UnicodeDecodeError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError("Shop importability check could not read the sealed Pack") from exc
    raise ContractError(
        "Shop import requires a top-level *.py defining gen_step, or a valid "
        "root project.json with root assembled.stl (preferred) or <slug>.stl "
        "in the sealed Made artifact"
    )


def _factory_story_value(
    value: Any, label: str, limit: int
) -> Optional[str]:
    """Render one verified fact within a per-section, whole-value cap."""

    if value is None or value == "" or value == [] or value == {}:
        return None
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if len(text) <= limit:
            return text
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        marker = " … [truncated; full value sha256=%s]" % digest
        if len(marker) >= limit:
            raise ContractError("Factory story prompt %s cap is too small" % label)
        return text[: limit - len(marker)].rstrip() + marker
    try:
        rendered = json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(
            "Factory story prompt %s must contain finite JSON facts" % label
        ) from exc
    if len(rendered) <= limit:
        return rendered
    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    summary: Dict[str, Any] = {
        "_workshop_full_source": "workshop-product-facts.json",
        "_workshop_source_sha256": digest,
        "_workshop_truncated": True,
    }
    if isinstance(value, Mapping):
        summary["top_level_keys"] = sorted(str(key) for key in value)[:32]
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        summary["item_count"] = len(value)
    bounded = json.dumps(
        summary,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    if len(bounded) > limit:
        raise ContractError("Factory story prompt %s cap is too small" % label)
    return bounded


def _factory_story_prompt(context: Any, page: Mapping[str, Any]) -> str:
    """Build bounded factual input for Factory-owned copy and media generation.

    This prompt is not page copy. It carries only selected, verified Make,
    Wish, Taste, and Instructions facts; the complete canonical record remains
    in ``workshop-product-facts.json``. The inventor credit is always retained
    even if an unusually large optional story section must be truncated.
    """

    product = context.made.product
    if not isinstance(product, Mapping):
        raise ContractError("Factory story prompt requires Made product facts")
    inventor_name = getattr(context.taste, "name", None)
    if (
        not isinstance(inventor_name, str)
        or not inventor_name.strip()
        or inventor_name != inventor_name.strip()
    ):
        raise ContractError("Factory story prompt requires the exact inventor name")
    credit = "By %s." % inventor_name
    use_facts = {
        key: value
        for key, value in (
            ("product_instructions", product.get("instructions")),
            ("product_rules", product.get("rules")),
            ("box_how_to_play", page.get("how_to_play")),
            ("box_how_to_use", page.get("how_to_use")),
        )
        if value not in (None, "", [], {})
    }
    # Caps sum well below the 50k API maximum. Story and art direction are
    # intentionally early and receive the largest structured allocations.
    facts = (
        ("Wish", context.wish.objective, 3_000),
        ("Product title", product.get("title"), 400),
        ("Story", product.get("story"), 7_000),
        ("Art direction", product.get("art_direction"), 7_000),
        ("Product lane", product.get("lane"), 150),
        ("Product summary", product.get("summary"), 2_500),
        ("Product description", product.get("description"), 5_000),
        ("What arrives", product.get("components"), 3_000),
        ("Design facts", product.get("design"), 4_500),
        ("Specifications", product.get("specifications"), 3_500),
        ("Instructions and rules", use_facts, 5_000),
        ("Limitations", product.get("limitations"), 2_500),
    )
    sections = [
        "FACTORY STORY INPUT — verified facts, not pre-authored page copy.",
        (
            "Generate the customer-facing story, images, and video from the exact "
            "primary model and these facts. Do not treat AI Playtest as a physical "
            "print, delivery, customer review, or human endorsement."
        ),
    ]
    for label, value, limit in facts:
        rendered = _factory_story_value(value, label, limit)
        if rendered is not None:
            sections.append("%s:\n%s" % (label, rendered))
    tail = "\n\nInventor attribution (retain exactly): %s" % credit
    body = "\n\n".join(sections).strip()
    prompt = body + tail
    if not prompt or prompt != prompt.strip() or len(prompt) > FACTORY_STORY_PROMPT_LIMIT:
        raise ContractError("Factory story prompt is not safely bounded")
    return prompt


def _sealed_factory_primary(context: Any) -> Mapping[str, str]:
    """Bind Factory facts and selected primary model to the sealed Made tree."""

    context.made.assert_current()
    root = Path(context.made.artifact_root).resolve(strict=True)
    product_path = root / "product.json"
    project_path = root / "project.json"
    for path, label in (
        (product_path, "Made product.json"),
        (project_path, "Made project.json"),
    ):
        if path.is_symlink() or not path.is_file():
            raise ContractError("%s must be a sealed regular file" % label)
        if path.stat().st_size <= 0 or path.stat().st_size > MAX_RESPONSE_BYTES:
            raise ContractError("%s is empty or exceeds the JSON limit" % label)
    try:
        sealed_product = _json_body(HttpResponse(200, {}, product_path.read_bytes()))
        project = _json_body(HttpResponse(200, {}, project_path.read_bytes()))
    except (OSError, PublishError) as exc:
        raise ContractError("sealed Made Factory metadata is malformed") from exc
    if _canonical_sha256(sealed_product) != _canonical_sha256(context.made.product):
        raise ContractError(
            "Made product facts do not match sealed artifact/product.json"
        )
    if project.get("id") != context.wish.product_id:
        raise ContractError("sealed project.json id must equal Wish product_id")

    top_generators = []
    for path in sorted(root.glob("*.py")):
        if path.is_symlink() or not path.is_file():
            raise ContractError("Factory primary generator must be a regular file")
        content = path.read_bytes()
        if b"def gen_step" in content:
            top_generators.append((path, content))
    if top_generators:
        if len(top_generators) != 1:
            raise ContractError("Factory handoff must select one top-level gen_step")
        path, content = top_generators[0]
        return {
            "kind": "generator",
            "path": path.name,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    assembled = root / "assembled.stl"
    canonical = root / (context.wish.product_id + ".stl")
    candidates = [path for path in (assembled, canonical) if path.is_file()]
    if not candidates:
        raise ContractError(
            "project-marker Made artifact requires root assembled.stl or <slug>.stl"
        )
    if any(path.is_symlink() for path in candidates):
        raise ContractError("Factory primary STL must be a sealed regular file")
    if assembled.is_file() and canonical.is_file():
        if assembled.read_bytes() != canonical.read_bytes():
            raise ContractError(
                "root assembled.stl and <slug>.stl diverge; Factory would prefer assembled.stl"
            )
    selected = assembled if assembled.is_file() else canonical
    content = selected.read_bytes()
    if not content:
        raise ContractError("Factory primary STL is empty")
    return {
        "kind": "mesh",
        "path": selected.name,
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _model_handoff_excludes(manifest: ArtifactManifest) -> Tuple[str, ...]:
    """Return exact Make-relative trees omitted from Factory's model handoff.

    The source Make remains immutable and keeps its complete inspection record.
    Only the transport Pack is narrowed.  ``build_pack`` writes a fresh
    content-addressed inventory for that subset, while the durable publication
    request records both the source Make identity and the handoff identity.
    """

    if not isinstance(manifest, ArtifactManifest):
        raise ContractError("Factory model handoff requires a Made manifest")
    excluded = set()
    for entry in manifest.entries:
        parts = PurePosixPath(entry.path).parts
        for position, part in enumerate(parts[:-1]):
            lowered = part.casefold()
            if (
                lowered in SHOP_MODEL_HANDOFF_EXCLUDED_DIRS
                or lowered.endswith("_review")
            ):
                excluded.add("/".join(parts[: position + 1]))
                break
    return tuple(sorted(excluded))


def _assert_model_only_handoff(content: bytes) -> None:
    """Prove a handoff cannot supply creator-owned page media anywhere."""

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            for name in archive.namelist():
                path = PurePosixPath(name)
                directories = tuple(part.casefold() for part in path.parts[:-1])
                if any(
                    directory in SHOP_MODEL_HANDOFF_EXCLUDED_DIRS
                    or directory.endswith("_review")
                    for directory in directories
                ):
                    raise ContractError(
                        "Factory model handoff contains creator page-output tree: %s"
                        % name
                    )
                if PurePosixPath(name).suffix.casefold() in (
                    SHOP_INSTRUCTIONS_FORBIDDEN_MEDIA_SUFFIXES
                ):
                    raise ContractError(
                        "Factory model handoff contains local page media: %s" % name
                    )
            if "product.json" in archive.namelist():
                try:
                    product = json.loads(
                        archive.read("product.json").decode("utf-8")
                    )
                except (UnicodeError, ValueError) as exc:
                    raise ContractError(
                        "Factory model handoff product.json is malformed"
                    ) from exc
                if isinstance(product, Mapping):
                    forbidden = FACTORY_OUTPUT_FIELD_NAMES & set(product)
                    if forbidden:
                        raise ContractError(
                            "Factory model handoff product.json contains creator output: %s"
                            % sorted(forbidden)
                        )
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError("Factory model handoff is not a readable Pack") from exc


def _build_model_handoff_pack(
    root: Path,
    manifest: ArtifactManifest,
    destination: Path,
    facts: Mapping[str, Any],
) -> Mapping[str, Any]:
    """Build a canonical transport Pack without local page/inspection media."""

    root = Path(root).resolve(strict=True)
    if build_artifact_manifest(root, created_at=manifest.created_at).to_dict() != manifest.to_dict():
        raise ContractError("Made bytes changed before Factory model handoff")
    facts_payload = (
        json.dumps(
            facts,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )
    assert_packable_content("workshop-product-facts.json", facts_payload)
    excluded = set(_model_handoff_excludes(manifest))

    def excluded_entry(path: str) -> bool:
        parts = PurePosixPath(path).parts
        return any("/".join(parts[:position]) in excluded for position in range(1, len(parts)))

    with tempfile.TemporaryDirectory(prefix="workshop-model-handoff-") as directory:
        staging = Path(directory)
        for entry in manifest.entries:
            if excluded_entry(entry.path):
                continue
            source = root.joinpath(*PurePosixPath(entry.path).parts)
            content = source.read_bytes()
            if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
                raise ContractError(
                    "Made file changed while building Factory handoff: %s" % entry.path
                )
            target = staging.joinpath(*PurePosixPath(entry.path).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            target.chmod(0o755 if entry.executable else 0o644)
        facts_path = staging / "workshop-product-facts.json"
        if facts_path.exists():
            raise ContractError("Made artifact reserves workshop-product-facts.json")
        facts_path.write_bytes(facts_payload)
        result = dict(build_pack(staging, destination))
    result["product_facts_sha256"] = hashlib.sha256(facts_payload).hexdigest()
    return result


def _https_url(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise ContractError("%s must be an absolute HTTPS URL" % label)
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as exc:
        raise ContractError("%s must be an absolute HTTPS URL" % label) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be an absolute HTTPS URL" % label)
    return value


def _factory_enrichment_readback(design: Mapping[str, Any]) -> Mapping[str, Any]:
    """Validate and expose mutable copy/media that Factory generated.

    These fields are observations only. They are deliberately not compared to
    Workshop's factual import seed because Factory owns their enrichment.
    """

    title = design.get("title")
    description = design.get("description")
    if not isinstance(title, str) or not title.strip():
        raise ReceiptError("Factory enrichment readback has no title")
    if not isinstance(description, str) or not description.strip():
        raise ReceiptError("Factory enrichment readback has no description")
    covers = design.get("thumbnail_urls")
    if not isinstance(covers, list) or not covers:
        raise ReceiptError("Factory enrichment readback has no server cover")
    try:
        cover_urls = [
            _https_url(url, "Factory-generated cover URL") for url in covers
        ]
    except ContractError as exc:
        raise ReceiptError("Factory enrichment cover readback is malformed") from exc
    raw_attachments = design.get("attachments") or []
    if not isinstance(raw_attachments, list):
        raise ReceiptError("Factory enrichment attachments are malformed")
    attachments = []
    for item in raw_attachments:
        if (
            not isinstance(item, Mapping)
            or item.get("kind") not in ("image", "video")
        ):
            raise ReceiptError("Factory enrichment attachment is malformed")
        try:
            url = _https_url(
                item.get("url"), "Factory-generated attachment URL"
            )
        except ContractError as exc:
            raise ReceiptError("Factory enrichment attachment is malformed") from exc
        attachments.append({"kind": item["kind"], "url": url})
    use_case = design.get("use_case")
    story_blocks = design.get("story_blocks")
    if use_case is not None and not isinstance(use_case, Mapping):
        raise ReceiptError("Factory enrichment use_case is malformed")
    if story_blocks is not None and not isinstance(story_blocks, list):
        raise ReceiptError("Factory enrichment story_blocks are malformed")
    return {
        "title": title,
        "description": description,
        "cover_urls": cover_urls,
        "attachments": attachments,
        "has_use_case": use_case is not None,
        "story_block_count": len(story_blocks or []),
    }


def _shop_product_page_url(slug: Any) -> str:
    """Return the customer page, never the immutable project CDN directory."""

    if not isinstance(slug, str) or not slug or len(slug) > 300:
        raise ReceiptError("Shop product page requires a canonical slug")
    return _https_url(
        DEFAULT_SHOP_PAGE_BASE + "/" + urllib.parse.quote(slug, safe=""),
        "Shop product page URL",
    )


def _shop_category_for_lane(lane: Any) -> str:
    """Translate Workshop lanes into the Shop's stable public taxonomy."""

    if not isinstance(lane, str) or lane not in SHOP_CATEGORY_BY_LANE:
        raise ContractError("product page lane has no Shop category mapping")
    return SHOP_CATEGORY_BY_LANE[lane]


def _design_with_normalized_currency(design: Mapping[str, Any]) -> Mapping[str, Any]:
    """Accept the deployed API's lowercase ``usd`` without weakening currency proof."""

    copied = dict(design)
    listing = copied.get("listing")
    if isinstance(listing, Mapping):
        normalized_listing = dict(listing)
        currency = normalized_listing.get("currency")
        if isinstance(currency, str) and currency.casefold() == "usd":
            normalized_listing["currency"] = "USD"
        copied["listing"] = normalized_listing
    return copied


def _receipt_with_details(
    receipt: PublicationReceipt, details: Mapping[str, Any]
) -> PublicationReceipt:
    value = receipt.to_dict()
    merged = dict(value.get("details") or {})
    merged.update(dict(details))
    value["details"] = merged
    return PublicationReceipt.from_dict(value)


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Authenticated API calls never forward a bearer through a redirect."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def __post_init__(self) -> None:
        if (
            not isinstance(self.status, int)
            or isinstance(self.status, bool)
            or not 100 <= self.status <= 599
        ):
            raise ContractError("HTTP response status must be an integer from 100 to 599")
        if not isinstance(self.headers, Mapping):
            raise ContractError("HTTP response headers must be a mapping")
        if not isinstance(self.body, bytes):
            raise ContractError("HTTP response body must be bytes")
        if len(self.body) > MAX_RESPONSE_BYTES:
            raise PublishError("Shop response exceeds the 2 MB safety limit")


def urllib_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: Optional[bytes],
    timeout: int,
) -> HttpResponse:
    request = urllib.request.Request(url, method=method, data=body)
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
            if len(content) > MAX_RESPONSE_BYTES:
                raise PublishError("Shop response exceeds the 2 MB safety limit")
            return HttpResponse(response.status, dict(response.headers), content)
    except urllib.error.HTTPError as exc:
        content = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(content) > MAX_RESPONSE_BYTES:
            raise PublishError("Shop error response exceeds the 2 MB safety limit")
        return HttpResponse(exc.code, dict(exc.headers or {}), content)


def _json_body(response: HttpResponse) -> Mapping[str, Any]:
    def reject_duplicate_keys(pairs):  # type: ignore[no-untyped-def]
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate JSON key %r" % key)
            value[key] = item
        return value

    try:
        value = json.loads(
            response.body.decode("utf-8"), object_pairs_hook=reject_duplicate_keys
        )
    except (UnicodeDecodeError, ValueError) as exc:
        raise PublishError(
            "Shop Door returned invalid JSON (HTTP %s): %s"
            % (response.status, exc)
        )
    if not isinstance(value, Mapping):
        raise PublishError("Shop Door returned a non-object JSON response")
    return value


def _normalize_shop_listing(
    metadata: Mapping[str, Any],
    *,
    allow_workshop_fields: bool = False,
    inventor_name: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ContractError("Shop listing must be an object")
    if not all(isinstance(name, str) for name in metadata):
        raise ContractError("Shop listing field names must be strings")
    allowed = set(SHOP_LISTING_STRING_LIMITS) | {"tags", "status"}
    if allow_workshop_fields:
        allowed |= set(WORKSHOP_SHOP_LISTING_FIELDS)
        allowed |= set(LEGACY_SHOP_LISTING_FIELDS)
    unknown = set(metadata) - allowed
    if unknown:
        raise ContractError("unknown Shop listing fields: %s" % sorted(unknown))
    normalized: Dict[str, Any] = {"status": metadata.get("status", "draft")}
    if normalized["status"] != "draft":
        raise ContractError("Workshop import always requires status=draft")
    for name, limit in SHOP_LISTING_STRING_LIMITS.items():
        value = metadata.get(name)
        if value is None:
            continue
        if name == "description" and inventor_name is not None:
            value = attribute_product_description(value, inventor_name)
        if (
            not isinstance(value, str)
            or value != value.strip()
            or not value
            or len(value) > limit
        ):
            raise ContractError(
                "Shop listing %s must be a trimmed non-empty string of at most %d characters"
                % (name, limit)
            )
        normalized[name] = value
    if "title" not in normalized:
        raise ContractError("Shop listing title is required")
    tags = metadata.get("tags")
    if tags is None:
        tags = []
    if (
        not isinstance(tags, list)
        or len(tags) > 10
        or any(
            not isinstance(tag, str)
            or tag != tag.strip()
            or not tag
            or len(tag) > 40
            for tag in tags
        )
        or len(tags) != len({tag.casefold() for tag in tags})
    ):
        raise ContractError(
            "Shop listing tags must be at most 10 case-insensitively unique "
            "trimmed strings of at most 40 characters"
        )
    normalized["tags"] = list(tags)
    assert_packable_content(
        "publication-metadata.json",
        json.dumps(
            normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8"),
    )
    return normalized


def _origin(url: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(url)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ContractError("Shop Door API base is malformed") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ContractError(
            "Shop Door API base must be an HTTPS origin/path without credentials or query"
        )
    return "https://%s%s" % (parsed.hostname.lower(), ":%d" % port if port else "")


def _validate_upload_filename(filename: str) -> str:
    if (
        not isinstance(filename, str)
        or not filename
        or len(filename) > 255
        or PurePosixPath(filename).name != filename
        or any(ord(character) < 32 or ord(character) == 127 for character in filename)
    ):
        raise ContractError("Shop upload filename must be one safe basename")
    assert_packable_content(filename, b"")
    return filename


def _multipart(
    fields: Sequence[Tuple[str, str]], files: Sequence[Tuple[str, str, str, bytes]]
) -> Tuple[bytes, str]:
    boundary = "inventor-workshop-%s" % uuid.uuid4().hex
    buffer = io.BytesIO()
    marker = ("--%s\r\n" % boundary).encode("ascii")
    for name, value in fields:
        buffer.write(marker)
        buffer.write(
            ('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode("utf-8")
        )
        buffer.write(value.encode("utf-8"))
        buffer.write(b"\r\n")
    for name, filename, content_type, content in files:
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
        buffer.write(marker)
        buffer.write(
            (
                'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                % (name, safe_name)
            ).encode("utf-8")
        )
        buffer.write(("Content-Type: %s\r\n\r\n" % content_type).encode("ascii"))
        buffer.write(content)
        buffer.write(b"\r\n")
    buffer.write(("--%s--\r\n" % boundary).encode("ascii"))
    return buffer.getvalue(), "multipart/form-data; boundary=%s" % boundary


class ShopDoor:
    """Authenticated Door into the optional product Shop."""

    name = "shop"

    def __init__(
        self,
        token: str,
        api_base: str = DEFAULT_SHOP_API,
        transport: Transport = urllib_transport,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
        allowed_origins: Optional[Sequence[str]] = None,
    ) -> None:
        if not isinstance(token, str) or not token or "\r" in token or "\n" in token:
            raise ContractError("Shop Door bearer token is required")
        origin = _origin(api_base)
        if isinstance(allowed_origins, (str, bytes)):
            raise ContractError(
                "Shop Door allowed_origins must be a sequence of HTTPS origins"
            )
        allowed = {
            _origin(item) for item in (allowed_origins or (DEFAULT_SHOP_API,))
        }
        if origin not in allowed:
            raise ContractError(
                "Shop Door API origin %s is not pinned in allowed_origins" % origin
            )
        self._token = token
        self.api_base = api_base.rstrip("/")
        self.api_origin = origin
        self.transport = transport
        if (
            not isinstance(timeout_seconds, int)
            or isinstance(timeout_seconds, bool)
            or timeout_seconds <= 0
        ):
            raise ContractError("Shop Door timeout_seconds must be a positive integer")
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
    ) -> HttpResponse:
        # Cloudflare rejects urllib's implicit ``Python-urllib/*`` signature
        # before the request reaches the Shop API (Error 1010).  Give every
        # shared Shop request a stable, honest Workshop identity instead.
        headers = {
            "Authorization": "Bearer %s" % self._token,
            "Accept": "application/json",
            "User-Agent": SHOP_USER_AGENT,
        }
        if content_type:
            headers["Content-Type"] = content_type
        return self.transport(
            method,
            self.api_base + path,
            headers,
            body,
            self.timeout_seconds,
        )

    def import_design(
        self,
        packet: Path,
        metadata: Mapping[str, Any],
        *,
        thumbnail: Optional[Mapping[str, Any]] = None,
    ) -> HttpResponse:
        if thumbnail is not None:
            raise ContractError(
                "Workshop model imports cannot supply thumbnails; Factory owns page media"
            )
        packet = Path(packet)
        content = _load_pack(packet)[0]
        return self.import_design_bytes(packet.name, content, metadata)

    def import_design_bytes(
        self,
        filename: str,
        content: bytes,
        metadata: Mapping[str, Any],
        *,
        thumbnail: Optional[Mapping[str, Any]] = None,
    ) -> HttpResponse:
        if thumbnail is not None:
            raise ContractError(
                "Workshop model imports cannot supply thumbnails; Factory owns page media"
            )
        filename = _validate_upload_filename(filename)
        content = _validate_pack_bytes(content)[0]
        _assert_shop_importable_pack(content)
        _assert_model_only_handoff(content)
        metadata = _normalize_shop_listing(
            metadata, allow_workshop_fields=True
        )
        fields = [("status", "draft")]
        for name in ("title", "description", "category", "prompt", "license"):
            if metadata.get(name) is not None:
                fields.append((name, str(metadata[name])))
        tags = metadata["tags"]
        if tags:
            for tag in tags:
                fields.append(("tags", str(tag)))
        else:
            # The backend distinguishes an absent tag field (derive defaults)
            # from a present empty field (the exact requested empty set).
            fields.append(("tags", ""))
        content_type = mimetypes.guess_type(filename)[0] or "application/zip"
        files = [("file", filename, content_type, content)]
        body, multipart_type = _multipart(fields, files)
        return self._request("POST", "/designs/import", body, multipart_type)

    def get_design(self, slug: str) -> HttpResponse:
        return self._request("GET", "/designs/%s" % urllib.parse.quote(slug, safe=""))

    def upload_file_bytes(
        self,
        filename: str,
        content: bytes,
        content_type: Optional[str] = None,
    ) -> HttpResponse:
        del filename, content, content_type
        raise ContractError(
            "Workshop cannot upload product-page media; Factory owns generated media"
        )

    def patch_use_case(
        self, slug: str, use_case: Mapping[str, Any]
    ) -> HttpResponse:
        del slug, use_case
        raise ContractError(
            "Workshop cannot write use_case copy; Factory owns generated page copy"
        )

    def put_story_blocks(
        self, slug: str, story_blocks: Sequence[Mapping[str, Any]]
    ) -> HttpResponse:
        del slug, story_blocks
        raise ContractError(
            "Workshop cannot write story_blocks copy; Factory owns generated page copy"
        )

    def publish(
        self,
        slug: str,
        price_cents: Optional[int] = None,
        *,
        title: Optional[str] = None,
        attachments: Sequence[Mapping[str, Any]] = (),
    ) -> HttpResponse:
        if price_cents is not None and (
            not isinstance(price_cents, int)
            or isinstance(price_cents, bool)
            or not 100 <= price_cents <= 1_000_000
        ):
            raise ContractError(
                "price_cents must be an integer in the Shop Door's 100..1000000 range"
            )
        if title is not None:
            raise ContractError(
                "Workshop cannot replace Factory page titles; Factory owns generated copy"
            )
        if isinstance(attachments, (str, bytes)) or not isinstance(
            attachments, Sequence
        ):
            raise ContractError("Shop publish attachments must be an empty sequence")
        if len(attachments):
            raise ContractError(
                "Workshop cannot attach creator media; Factory owns generated media"
            )
        request: Dict[str, Any] = {}
        if price_cents is not None:
            request["listing"] = {"price_cents": price_cents}
        path = "/designs/%s/publish" % urllib.parse.quote(slug, safe="")
        if not request:
            return self._request("POST", path)
        body = json.dumps(
            request,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return self._request(
            "POST", path, body, "application/json"
        )

    def unpublish(self, slug: str) -> HttpResponse:
        return self._request(
            "POST",
            "/designs/%s/unpublish" % urllib.parse.quote(slug, safe=""),
            b"{}",
            "application/json",
        )


class _ShopSender:
    """Durable Shop sender; every remote effect is recorded before sending."""

    def __init__(self, store: InventorStore, client: ShopDoor, owner_id: str) -> None:
        if not isinstance(owner_id, str) or not owner_id:
            raise ContractError("Shop owner_id is required")
        self.store = store
        self.client = client
        self.owner_id = owner_id

    def import_draft(
        self,
        product_id: str,
        packet: Path,
        metadata: Mapping[str, Any],
        lease_token: Optional[str] = None,
        *,
        inventor_name: Optional[str] = None,
        instructions_sha256: Optional[str] = None,
        playtest_evidence_sha256: Optional[str] = None,
        thumbnail: Optional[Mapping[str, Any]] = None,
        source_artifact_sha256: Optional[str] = None,
        model_only_handoff: bool = False,
    ) -> PublicationOutcome:
        if thumbnail is not None:
            raise ContractError(
                "Workshop draft publication cannot supply thumbnails; "
                "Factory owns generated media"
            )
        packet = Path(packet)
        metadata = _normalize_shop_listing(
            metadata, inventor_name=inventor_name
        )
        packet_bytes, packet_sha, handoff_artifact_sha = _load_pack(packet)
        _assert_shop_importable_pack(packet_bytes)
        # There is no creator-media mode.  Every shared publication entry point
        # enforces the same model-only boundary, including legacy Launchpad and
        # Sender aliases that do not pass ``model_only_handoff=True``.
        _assert_model_only_handoff(packet_bytes)
        artifact_sha = (
            require_sha256(source_artifact_sha256, "source Made artifact sha256")
            if source_artifact_sha256 is not None
            else handoff_artifact_sha
        )
        _validate_upload_filename(packet.name)
        product = self.store.get_product(product_id)
        if not product.get("artifact_sha256"):
            raise ContractError("product must bind exact artifact bytes before publication")
        if product["artifact_sha256"] != artifact_sha:
            raise ContractError(
                "Pack artifact does not match the product's selected artifact"
            )
        request = dict(metadata)
        request["_workshop_artifact_sha256"] = artifact_sha
        if source_artifact_sha256 is not None or model_only_handoff:
            request["_workshop_handoff_artifact_sha256"] = handoff_artifact_sha
        request["_workshop_owner_id"] = self.owner_id
        request["_workshop_api_origin"] = self.client.api_origin
        if instructions_sha256 is not None:
            request["_workshop_instructions_sha256"] = require_sha256(
                instructions_sha256, "Instructions sha256"
            )
        if playtest_evidence_sha256 is not None:
            request["_workshop_playtest_evidence_sha256"] = require_sha256(
                playtest_evidence_sha256, "Playtest evidence sha256"
            )
        intent = self.store.prepare_publish(
            product_id,
            packet_sha,
            request,
            remote_slug_hint=None,
            lease_token=lease_token,
        )
        if intent["state"] in ("succeeded", "live"):
            receipt = PublicationReceipt.from_dict(intent["receipt"])
            receipt.assert_owner(self.owner_id)
            receipt.assert_artifact(artifact_sha)
            return PublicationOutcome(intent["id"], receipt)
        if intent["state"] == "live_unknown":
            receipt = self.reconcile_live(intent["id"])
            receipt.assert_artifact(artifact_sha)
            return PublicationOutcome(intent["id"], receipt)
        intent = self.store.begin_publish(intent["id"], lease_token=lease_token)
        effect_token = intent["effect_token"]
        try:
            response = self.client.import_design_bytes(
                packet.name,
                packet_bytes,
                intent["request"],
            )
        except Exception as exc:
            self.store.mark_publish_unknown(
                intent["id"], effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise AmbiguousPublishError(
                "Shop import outcome is unknown; intent %s must be reconciled before retry"
                % intent["id"]
            ) from exc
        if response.status != 201:
            summary = response.body.decode("utf-8", "replace")[:500]
            if response.status in PROVEN_NO_EFFECT_STATUSES:
                self.store.mark_publish_rejected(
                    intent["id"],
                    effect_token,
                    "HTTP %s: %s" % (response.status, summary),
                )
                raise PublishError(
                    "Shop Door rejected import (HTTP %s): %s" % (response.status, summary)
                )
            self.store.mark_publish_unknown(
                intent["id"],
                effect_token,
                "HTTP %s: %s" % (response.status, summary),
            )
            raise AmbiguousPublishError(
                "Shop Door import returned HTTP %s; reconcile intent %s before retry"
                % (response.status, intent["id"])
            )
        try:
            design = _json_body(response)
            receipt = PublicationReceipt.from_design(design, packet_sha, artifact_sha)
            receipt.assert_owner(self.owner_id)
            if receipt.status != "draft":
                raise ReceiptError("Shop Door did not return the required draft state")
            self.store.mark_publish_succeeded(
                intent["id"], effect_token, receipt, response=design
            )
            return PublicationOutcome(intent["id"], receipt)
        except Exception as exc:
            try:
                current = self.store.get_publish_intent(intent["id"])
                if current["state"] == "sending":
                    self.store.mark_publish_unknown(
                        intent["id"],
                        effect_token,
                        "201 response did not produce a valid draft receipt",
                    )
            except Exception:
                pass
            raise AmbiguousPublishError(
                "Shop Door accepted import but no valid Stamp was recorded; reconcile intent %s"
                % intent["id"]
            ) from exc

    def reconcile_import(self, intent_id: str, remote_slug: str) -> PublicationReceipt:
        """Fail closed until the Shop Door exposes remote content identity."""
        del remote_slug
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] != "unknown":
            raise PublishError("intent %s is not awaiting import reconciliation" % intent_id)
        raise AmbiguousPublishError(
            "Shop Door readback does not expose a Pack/tree hash, so a slug cannot prove "
            "which bytes created intent %s; backend idempotency support is required"
            % intent_id
        )

    def publish_live(
        self,
        intent_id: str,
        price_cents: Optional[int] = None,
        lease_token: Optional[str] = None,
        *,
        title: Optional[str] = None,
        attachments: Sequence[Mapping[str, Any]] = (),
        proof: Optional[Mapping[str, Any]] = None,
    ) -> PublicationReceipt:
        if price_cents is not None and (
            not isinstance(price_cents, int)
            or isinstance(price_cents, bool)
            or not 100 <= price_cents <= 1_000_000
        ):
            raise ContractError(
                "price_cents must be an integer in the Shop Door's 100..1000000 range"
            )
        if title is not None:
            raise ContractError(
                "Workshop cannot replace Factory page titles; Factory owns generated copy"
            )
        if isinstance(attachments, (str, bytes)) or not isinstance(
            attachments, Sequence
        ):
            raise ContractError("Shop publish attachments must be an empty sequence")
        if len(attachments):
            raise ContractError(
                "Workshop cannot attach creator media; Factory owns generated media"
            )
        # Build the complete request before checking for a completed intent so
        # replay means exact idempotency, never silent acceptance of a new price,
        # attachment set or proof under an old receipt.
        live_request: Dict[str, Any] = {
            "api_origin": self.client.api_origin,
            "owner_id": self.owner_id,
        }
        if price_cents is not None:
            live_request["listing"] = {"price_cents": price_cents}
        if proof is not None:
            live_request["proof"] = dict(proof)
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] == "live":
            persisted_request = intent.get("live_request")
            if (
                not isinstance(persisted_request, Mapping)
                or _canonical_sha256(persisted_request)
                != _canonical_sha256(live_request)
            ):
                raise StateConflict(
                    "live Shop request changed under a completed intent"
                )
            return PublicationReceipt.from_dict(intent["receipt"])
        if intent["state"] != "succeeded":
            raise AmbiguousPublishError(
                "intent %s is %s, not a proven draft" % (intent_id, intent["state"])
            )
        draft = PublicationReceipt.from_dict(intent["receipt"])
        draft.assert_owner(self.owner_id)
        # Persist an intermediate state before the second non-idempotent-facing effect.
        intent = self.store.begin_live(intent_id, live_request, lease_token=lease_token)
        effect_token = intent["effect_token"]
        try:
            persisted = intent["live_request"]
            listing = persisted.get("listing")
            response = self.client.publish(
                draft.slug,
                listing.get("price_cents") if isinstance(listing, Mapping) else None,
            )
        except Exception as exc:
            self.store.mark_live_unknown(
                intent_id, effect_token, "%s: %s" % (type(exc).__name__, exc)
            )
            raise AmbiguousPublishError(
                "publish outcome is unknown; reconcile intent %s before retry" % intent_id
            ) from exc
        if response.status not in (200, 201):
            summary = response.body.decode("utf-8", "replace")[:500]
            if response.status in PROVEN_NO_EFFECT_STATUSES:
                self.store.restore_draft_after_publish_rejection(
                    intent_id,
                    effect_token,
                    "HTTP %s: %s" % (response.status, summary),
                )
                raise PublishError(
                    "Shop Door rejected publication (HTTP %s): %s"
                    % (response.status, summary)
                )
            self.store.mark_live_unknown(
                intent_id, effect_token, "HTTP %s: %s" % (response.status, summary)
            )
            raise AmbiguousPublishError(
                "publish outcome is unknown; reconcile intent %s" % intent_id
            )
        return self._readback_live(intent_id, draft, effect_token=effect_token)

    def reconcile_live(self, intent_id: str) -> PublicationReceipt:
        intent = self.store.get_publish_intent(intent_id)
        if intent["state"] != "live_unknown":
            raise PublishError("intent %s is not awaiting live reconciliation" % intent_id)
        draft = PublicationReceipt.from_dict(intent["receipt"])
        return self._readback_live(intent_id, draft, reconciling=True)

    def _readback_live(
        self,
        intent_id: str,
        draft: PublicationReceipt,
        reconciling: bool = False,
        effect_token: Optional[str] = None,
    ) -> PublicationReceipt:
        try:
            response = self.client.get_design(draft.slug)
        except Exception as exc:
            if not reconciling:
                self.store.mark_live_unknown(
                    intent_id, effect_token, "readback failed: %s" % exc
                )
            raise AmbiguousPublishError("public readback failed for intent %s" % intent_id) from exc
        if response.status != 200:
            if not reconciling:
                self.store.mark_live_unknown(
                    intent_id, effect_token, "readback HTTP %s" % response.status
                )
            raise AmbiguousPublishError("public readback returned HTTP %s" % response.status)
        try:
            design = _json_body(response)
            receipt = PublicationReceipt.from_design(
                _design_with_normalized_currency(design),
                draft.packet_sha256,
                draft.artifact_sha256,
            )
            receipt.assert_owner(self.owner_id)
            intent = self.store.get_publish_intent(intent_id)
            live_request = intent.get("live_request")
            if not isinstance(live_request, Mapping):
                raise ReceiptError("publish intent lacks its persisted live request")
            listing_request = live_request.get("listing")
            if listing_request is not None and not isinstance(listing_request, Mapping):
                raise ReceiptError("publish intent has a malformed listing request")
            if isinstance(listing_request, Mapping):
                receipt.assert_listing(listing_request.get("price_cents"))
            if live_request.get("attachments") is not None:
                raise ReceiptError(
                    "Workshop public request must not contain creator media"
                )
            observed_attachments = design.get("attachments") or []
            if not isinstance(observed_attachments, list):
                raise ReceiptError("public readback attachments are malformed")
            for item in observed_attachments:
                if (
                    not isinstance(item, Mapping)
                    or item.get("kind") not in ("image", "video")
                ):
                    raise ReceiptError("public readback attachment is malformed")
                _https_url(item.get("url"), "Factory-generated attachment URL")
            forbidden_effects = {
                effect.get("kind")
                for effect in self.store.shop_effects_for_publish_intent(intent_id)
                if effect.get("kind") in ("media-upload", "use-case", "story-blocks")
            }
            if forbidden_effects:
                raise ReceiptError(
                    "Workshop publication contains forbidden creator media or page-copy effects"
                )
            if (
                receipt.design_id != draft.design_id
                or receipt.root_id != draft.root_id
                or receipt.current_history_id != draft.current_history_id
                or receipt.slug != draft.slug
                or receipt.project_url != draft.project_url
            ):
                raise ReceiptError("public readback does not identify the exact draft history")
            proof = live_request.get("proof")
            if isinstance(proof, Mapping):
                receipt = _receipt_with_details(receipt, proof)
        except Exception as exc:
            if not reconciling:
                try:
                    current = self.store.get_publish_intent(intent_id)
                    if current["state"] == "publishing":
                        self.store.mark_live_unknown(
                            intent_id,
                            effect_token,
                            "public readback was malformed or identified different bytes",
                        )
                except Exception:
                    pass
            raise AmbiguousPublishError(
                "public readback did not produce a trustworthy receipt for intent %s"
                % intent_id
            ) from exc
        if not receipt.is_verified_public:
            if not reconciling:
                self.store.mark_live_unknown(
                    intent_id,
                    effect_token,
                    "readback did not prove current version public",
                )
            raise AmbiguousPublishError(
                "one draft readback cannot prove a publish effect failed; intent remains unknown"
            )
        if reconciling:
            self.store.resolve_live_as_public(intent_id, receipt)
        else:
            self.store.mark_publish_live(intent_id, effect_token, receipt)
        return receipt


class ShopInstructionsWriter:
    """Shared model handoff inherited by every inventor.

    ``DefaultInstructions`` seals the box paper and factual product handoff, then
    calls this object as ``writer(context, root, manifest)``.  This adapter
    imports a model-only subset of the exact Made artifact as a private draft.
    It deliberately does not upload local marketing images or write product-page
    copy: Factory owns that later enrichment.  The returned authenticated
    readback is bound to the source Make, the narrowed handoff Pack, the factual
    product record, Playtest, and Instructions.  Its enrichment state remains
    ``pending``; a draft import is not proof that Factory produced final images,
    copy, or video.  This adapter never makes the page public.
    """

    def __init__(
        self,
        store: InventorStore,
        client: ShopDoor,
        owner_id: str,
        *,
        price_cents: Optional[int] = None,
    ) -> None:
        if price_cents is not None:
            raise ContractError(
                "Shop Instructions creates a private draft; price_cents belongs "
                "to the separate owner-controlled public transition"
            )
        self.store = store
        self.client = client
        self.owner_id = owner_id
        self._sender = _ShopSender(store, client, owner_id)

    @staticmethod
    def _assert_sealed(root: Path, manifest: ArtifactManifest) -> Path:
        requested = Path(root)
        if (
            not requested.is_absolute()
            or requested.is_symlink()
            or not requested.is_dir()
            or not isinstance(manifest, ArtifactManifest)
        ):
            raise ContractError(
                "Shop Instructions require an absolute sealed Instructions directory"
            )
        resolved = requested.resolve(strict=True)
        current = build_artifact_manifest(resolved, created_at=manifest.created_at)
        if current.to_dict() != manifest.to_dict():
            raise ContractError("Instructions bytes changed after they were sealed")
        forbidden_media = [
            entry.path
            for entry in manifest.entries
            if PurePosixPath(entry.path).suffix.casefold()
            in SHOP_INSTRUCTIONS_FORBIDDEN_MEDIA_SUFFIXES
        ]
        if forbidden_media:
            raise ContractError(
                "Shop Instructions cannot contain creator page media: %s"
                % forbidden_media
            )
        return resolved

    @staticmethod
    def _read_page(root: Path) -> Mapping[str, Any]:
        path = root / "product.json"
        if path.is_symlink() or not path.is_file():
            raise ContractError("sealed Instructions require product.json")
        content = path.read_bytes()
        page = _json_body(HttpResponse(200, {}, content))
        required = {
            "schema_version",
            "kind",
            "status",
            "title",
            "summary",
            "lane",
            "product_artifact_sha256",
            "playtest_evidence_artifact_sha256",
        }
        if not required <= set(page):
            raise ContractError("sealed product.json is missing required page fields")
        if (
            page.get("schema_version") != 2
            or page.get("kind") != "workshop.instructions-facts"
            or page.get("status") != "facts-ready"
        ):
            raise ContractError("sealed product.json is not a factual Instructions handoff")
        forbidden = {"images", "use_case", "story_blocks"} & set(page)
        if forbidden:
            raise ContractError(
                "sealed product.json cannot contain creator page copy or media: %s"
                % sorted(forbidden)
            )
        if page.get("factory_enrichment") != {
            "copy_owner": "factory",
            "media_owner": "factory",
            "status": "pending",
        }:
            raise ContractError("sealed product.json must leave Factory enrichment pending")
        return page

    @staticmethod
    def _assert_instructions_draft_receipt(
        receipt: PublicationReceipt,
        artifact_sha256: str,
        instructions_sha256: str,
    ) -> None:
        receipt.assert_artifact(artifact_sha256)
        if not receipt.is_verified_draft:
            raise ReceiptError("Instructions require authenticated private Shop draft readback")
        _https_url(receipt.details.get("page_url"), "Shop product page URL")
        _https_url(receipt.details.get("cover_url"), "Shop draft cover URL")
        if receipt.details.get("instructions_sha256") != instructions_sha256:
            raise ReceiptError("Shop receipt is not bound to the sealed Instructions bytes")
        require_sha256(
            receipt.details.get("playtest_evidence_sha256"),
            "Shop draft Playtest evidence sha256",
        )
        require_sha256(
            receipt.details.get("handoff_artifact_sha256"),
            "Shop model handoff artifact sha256",
        )
        require_sha256(
            receipt.details.get("product_facts_sha256"),
            "Shop product facts sha256",
        )
        primary_path = receipt.details.get("primary_model_path")
        if (
            not isinstance(primary_path, str)
            or not primary_path
            or PurePosixPath(primary_path).name != primary_path
        ):
            raise ReceiptError("Shop primary model path is malformed")
        require_sha256(
            receipt.details.get("primary_model_sha256"),
            "Shop primary model sha256",
        )
        if (
            receipt.details.get("enrichment_status") != "pending"
            or receipt.details.get("page_ready") is not False
        ):
            raise ReceiptError(
                "model import cannot claim Factory page enrichment is complete"
            )

    def _readback_draft(
        self,
        intent_id: str,
        imported: PublicationReceipt,
        proof: Mapping[str, Any],
        lease_token: Optional[str],
    ) -> PublicationReceipt:
        """Prove the model draft still identifies the exact imported handoff."""

        try:
            response = self.client.get_design(imported.slug)
        except Exception as exc:
            raise AmbiguousPublishError(
                "authenticated Instructions draft readback failed"
            ) from exc
        if response.status != 200:
            raise AmbiguousPublishError(
                "authenticated Instructions draft readback returned HTTP %s"
                % response.status
            )
        try:
            design = _json_body(response)
            receipt = PublicationReceipt.from_design(
                _design_with_normalized_currency(design),
                imported.packet_sha256,
                imported.artifact_sha256,
            )
            receipt.assert_owner(self.owner_id)
            if not receipt.is_verified_draft:
                raise ReceiptError("Shop readback no longer identifies a private draft")
            identity_fields = (
                "design_id",
                "slug",
                "owner_id",
                "root_id",
                "current_history_id",
                "project_url",
            )
            if any(
                getattr(receipt, field) != getattr(imported, field)
                for field in identity_fields
            ):
                raise ReceiptError(
                    "Shop readback does not identify the imported draft history"
                )
            intent = self.store.get_publish_intent(intent_id)
            request = intent.get("request")
            import_response = intent.get("response")
            imported_covers = (
                import_response.get("thumbnail_urls")
                if isinstance(import_response, Mapping)
                else None
            )
            observed_covers = design.get("thumbnail_urls")
            category = design.get("category")
            author = design.get("author")
            if (
                not isinstance(request, Mapping)
                or design.get("origin") != "import"
                or design.get("tags") != request.get("tags")
                or not isinstance(category, Mapping)
                or category.get("slug") != request.get("category")
                or not isinstance(imported_covers, list)
                or not imported_covers
                or observed_covers != imported_covers
                or imported_covers[0] != proof.get("cover_url")
                or (
                    isinstance(author, Mapping)
                    and author.get("id") is not None
                    and author.get("id") != self.owner_id
                )
            ):
                raise ReceiptError(
                    "Shop draft readback does not preserve the sealed Instructions import"
                )
            forbidden_effects = {
                effect.get("kind")
                for effect in self.store.shop_effects_for_publish_intent(intent_id)
                if effect.get("kind") in ("media-upload", "use-case", "story-blocks")
            }
            if forbidden_effects:
                raise ReceiptError(
                    "Factory-owned enrichment cannot contain Workshop page effects"
                )
            receipt = _receipt_with_details(receipt, proof)
            persisted = self.store.mark_instructions_draft_ready(
                intent_id, receipt, lease_token
            )
            return PublicationReceipt.from_dict(persisted["receipt"])
        except (ContractError, PublishError, ReceiptError, StateConflict) as exc:
            raise AmbiguousPublishError(
                "authenticated Shop readback did not prove the exact Instructions draft"
            ) from exc

    def __call__(
        self,
        context: Any,
        sealed_root: Path,
        sealed_manifest: ArtifactManifest,
    ) -> PublicationReceipt:
        if not callable(getattr(context, "assert_current", None)):
            raise ContractError("ShopInstructionsWriter requires an InstructionsContext")
        context.assert_current()
        root = self._assert_sealed(sealed_root, sealed_manifest)
        instructions_sha256 = require_sha256(
            sealed_manifest.artifact_sha256, "sealed Instructions sha256"
        )
        page = self._read_page(root)
        artifact_sha256 = require_sha256(
            page.get("product_artifact_sha256"), "product page artifact sha256"
        )
        if artifact_sha256 != context.made.artifact_sha256:
            raise ContractError("product page describes different Made bytes")
        playtest_sha256 = require_sha256(
            page.get("playtest_evidence_artifact_sha256"),
            "product page Playtest evidence sha256",
        )
        title = page.get("title")
        summary = page.get("summary")
        lane = page.get("lane")
        if not all(isinstance(value, str) and value.strip() for value in (title, summary, lane)):
            raise ContractError("product page title, summary, and lane are required")
        product_id = context.wish.product_id
        inventor_name = context.taste.name
        lease_token = getattr(context, "lease_token", None)
        forbidden_product_fields = FACTORY_OUTPUT_FIELD_NAMES & set(
            context.made.product
        )
        if forbidden_product_fields:
            raise ContractError(
                "Made product facts cannot contain creator-owned Factory output: %s"
                % sorted(forbidden_product_fields)
            )
        primary_model = _sealed_factory_primary(context)
        product_facts = {
            "schema_version": 2,
            "kind": "workshop.product-facts",
            "source_artifact_sha256": artifact_sha256,
            "instructions_sha256": instructions_sha256,
            "playtest_evidence_sha256": playtest_sha256,
            "inventor": {"name": inventor_name},
            "wish": context.wish.to_dict(),
            "product": dict(context.made.product),
            "primary_model": dict(primary_model),
            # This is a story/facts input, never pre-authored page output. It
            # gives Factory the verified rules, components, limitations, and
            # Playtest claims it needs to generate accurate copy and imagery.
            "instructions": dict(page),
        }

        def assert_current() -> None:
            context.assert_current()
            self._assert_sealed(root, sealed_manifest)

        with tempfile.TemporaryDirectory(prefix="workshop-instructions-") as directory:
            packet = Path(directory) / "model-handoff.zip"
            handoff = _build_model_handoff_pack(
                context.made.artifact_root,
                context.made.artifact_manifest,
                packet,
                product_facts,
            )
            assert_current()
            outcome = self._sender.import_draft(
                product_id,
                packet,
                {
                    "title": title,
                    "description": summary,
                    "category": _shop_category_for_lane(lane),
                    "prompt": _factory_story_prompt(context, page),
                    "tags": ["toy", lane],
                },
                inventor_name=inventor_name,
                instructions_sha256=instructions_sha256,
                playtest_evidence_sha256=playtest_sha256,
                source_artifact_sha256=artifact_sha256,
                model_only_handoff=True,
                lease_token=lease_token,
            )
        if outcome.receipt.details.get("instructions_sha256") is not None:
            self._assert_instructions_draft_receipt(
                outcome.receipt, artifact_sha256, instructions_sha256
            )
            return outcome.receipt
        if outcome.receipt.status != "draft":
            raise StateConflict(
                "Shop Instructions cannot reuse an intent already made public"
            )
        persisted_intent = self.store.get_publish_intent(outcome.intent_id)
        import_response = persisted_intent.get("response")
        cover_urls = (
            import_response.get("thumbnail_urls")
            if isinstance(import_response, Mapping)
            else None
        )
        if not isinstance(cover_urls, list) or not cover_urls:
            raise AmbiguousPublishError(
                "Shop import did not prove the sealed hero became the draft cover"
            )
        cover_url = _https_url(cover_urls[0], "Shop draft cover URL")
        proof = {
            "instructions_sha256": instructions_sha256,
            "playtest_evidence_sha256": playtest_sha256,
            "page_url": _shop_product_page_url(outcome.receipt.slug),
            "cover_url": cover_url,
            "server_cover_urls": list(cover_urls),
            "handoff_artifact_sha256": handoff["artifact_sha256"],
            "product_facts_sha256": handoff["product_facts_sha256"],
            "primary_model_path": primary_model["path"],
            "primary_model_sha256": primary_model["sha256"],
            "content_brief_sha256": _canonical_sha256(page),
            "enrichment_status": "pending",
            "page_ready": False,
        }
        assert_current()
        receipt = self._readback_draft(
            outcome.intent_id,
            outcome.receipt,
            proof,
            lease_token,
        )
        self._assert_instructions_draft_receipt(
            receipt, artifact_sha256, instructions_sha256
        )
        return receipt
