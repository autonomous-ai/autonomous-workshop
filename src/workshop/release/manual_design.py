"""Deterministic evidence boundary for native-authored manual design work."""

from __future__ import annotations

import hashlib
import io
import json
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence

from workshop.artifacts import ArtifactManifest
from workshop.errors import ContractError, StateConflict
from workshop.make.native import NativeMade


MANUAL_DESIGN_EVIDENCE_PATH = "MANUAL-DESIGN.json"
MANUAL_DESIGN_EVIDENCE_KIND = "autonomous-workshop.manual-design-evidence"
MANUAL_DESIGN_EVIDENCE_SCHEMA_VERSION = 1
MAX_MANUAL_DESIGN_EVIDENCE_BYTES = 64 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_VISUAL_SUFFIXES = frozenset(
    (".3mf", ".glb", ".jpeg", ".jpg", ".obj", ".png", ".step", ".stl", ".svg", ".webp")
)
# Host renders are cited under this virtual prefix; their bytes are bound by
# the host's private render record, not by the agent-authored Made manifest.
HOST_RENDER_SOURCE_PREFIX = "renders/"


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant %s" % value)


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("manual design evidence must be finite JSON") from exc


def _bounded_text(value: Any, label: str, *, minimum: int, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not minimum <= len(value) <= maximum
        or any(ord(character) < 32 and character not in "\n\t" for character in value)
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded substantive text" % label)
    return value


def _text_list(
    value: Any,
    label: str,
    *,
    minimum_items: int,
    maximum_items: int,
    minimum_length: int = 2,
    maximum_length: int = 500,
) -> list[str]:
    if (
        isinstance(value, (str, bytes))
        or not isinstance(value, Sequence)
        or not minimum_items <= len(value) <= maximum_items
    ):
        raise ContractError("%s has an invalid item count" % label)
    result = [
        _bounded_text(
            item,
            "%s item" % label,
            minimum=minimum_length,
            maximum=maximum_length,
        )
        for item in value
    ]
    if len({item.casefold() for item in result}) != len(result):
        raise ContractError("%s must not contain duplicates" % label)
    return result


def _mapping(value: Any, label: str, fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != fields:
        raise ContractError("%s fields are invalid" % label)
    return dict(value)


def _read_evidence(package_root: Path) -> tuple[dict[str, Any], bytes]:
    path = package_root / MANUAL_DESIGN_EVIDENCE_PATH
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("Release MANUAL-DESIGN.json is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        or not 1 <= len(content) <= MAX_MANUAL_DESIGN_EVIDENCE_BYTES
    ):
        raise StateConflict("Release MANUAL-DESIGN.json is not a bounded stable file")
    try:
        document = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, RecursionError, json.JSONDecodeError) as exc:
        raise ContractError(
            "Release MANUAL-DESIGN.json must contain strict UTF-8 JSON"
        ) from exc
    if not isinstance(document, dict) or content != _canonical_json(document):
        raise ContractError("Release MANUAL-DESIGN.json must use canonical JSON")
    return document, content


def _stable_regular(path: Path, label: str, maximum: int) -> bytes:
    try:
        before = path.lstat()
        content = path.read_bytes()
        after = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(before.st_mode)
        or (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        or not 1 <= len(content) <= maximum
    ):
        raise StateConflict("%s is not a bounded stable file" % label)
    return content


def _resolve(value: Any) -> Any:
    return value.get_object() if hasattr(value, "get_object") else value


def _font_descriptor_is_embedded(font: Any) -> bool:
    font = _resolve(font)
    if not isinstance(font, Mapping):
        return False
    if str(font.get("/Subtype")) == "/Type3":
        return True
    if str(font.get("/Subtype")) == "/Type0":
        descendants = _resolve(font.get("/DescendantFonts"))
        if isinstance(descendants, Sequence) and descendants:
            return all(_font_descriptor_is_embedded(item) for item in descendants)
        return False
    descriptor = _resolve(font.get("/FontDescriptor"))
    return isinstance(descriptor, Mapping) and any(
        descriptor.get(name) is not None
        for name in ("/FontFile", "/FontFile2", "/FontFile3")
    )


def _pdf_pages_and_embedded_fonts(manual: bytes) -> int:
    try:
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(manual), strict=True)
        pages = list(reader.pages)
    except Exception as exc:
        raise ContractError("Release MANUAL.pdf cannot be inspected for design evidence") from exc
    missing = set()
    observed_fonts = 0
    visited_resources: set[int] = set()

    def inspect_resources(raw: Any) -> None:
        nonlocal observed_fonts
        resources = _resolve(raw)
        if not isinstance(resources, Mapping) or id(resources) in visited_resources:
            return
        visited_resources.add(id(resources))
        fonts = _resolve(resources.get("/Font"))
        if isinstance(fonts, Mapping):
            for resource_name, raw_font in fonts.items():
                observed_fonts += 1
                font = _resolve(raw_font)
                if not _font_descriptor_is_embedded(font):
                    base = (
                        str(font.get("/BaseFont"))
                        if isinstance(font, Mapping)
                        else str(resource_name)
                    )
                    missing.add(base)
        xobjects = _resolve(resources.get("/XObject"))
        if isinstance(xobjects, Mapping):
            for raw_xobject in xobjects.values():
                xobject = _resolve(raw_xobject)
                if isinstance(xobject, Mapping):
                    inspect_resources(xobject.get("/Resources"))

    for page in pages:
        inspect_resources(page.get("/Resources"))
    if not pages or observed_fonts < 1:
        raise ContractError("Release MANUAL.pdf has no inspectable fonts")
    if missing:
        raise ContractError(
            "Release MANUAL.pdf must embed every used font: %s"
            % ", ".join(sorted(missing))
        )
    return len(pages)


def _render_sources(value: Any) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ContractError("manual design render sources must be a mapping")
    sources: dict[str, str] = {}
    for path, digest in value.items():
        if (
            not isinstance(path, str)
            or not path.startswith(HOST_RENDER_SOURCE_PREFIX)
            or not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
        ):
            raise ContractError("manual design render sources are invalid")
        sources[path] = digest
    return sources


def validate_manual_design_evidence(
    package_root: Path,
    *,
    manual: bytes,
    made: NativeMade,
    render_sources: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    """Validate exact creative-process evidence without judging aesthetics.

    ``render_sources`` maps ``renders/<name>.png`` to the sha256 the host's
    private render record binds and re-verified on disk; a manual may cite
    those beside sealed Made bytes.
    """

    if not isinstance(made, NativeMade):
        raise ContractError("manual design evidence requires typed Made input")
    host_renders = _render_sources(render_sources)
    root = Path(package_root).resolve(strict=True)
    document, unused_content = _read_evidence(root)
    del unused_content
    evidence = _mapping(
        document,
        "Release manual design evidence",
        {
            "schema_version",
            "kind",
            "manual_sha256",
            "design_mode",
            "creative_brief",
            "product_visuals",
            "review",
        },
    )
    if (
        evidence["schema_version"] != MANUAL_DESIGN_EVIDENCE_SCHEMA_VERSION
        or evidence["kind"] != MANUAL_DESIGN_EVIDENCE_KIND
        or evidence["design_mode"] != "bespoke"
        or not isinstance(evidence["manual_sha256"], str)
        or _SHA256.fullmatch(evidence["manual_sha256"]) is None
        or evidence["manual_sha256"] != hashlib.sha256(manual).hexdigest()
    ):
        raise ContractError("Release manual design evidence identity is invalid")

    brief = _mapping(
        evidence["creative_brief"],
        "Release manual creative brief",
        {
            "emotional_promise",
            "physical_format",
            "format_rationale",
            "visual_motif",
            "palette",
            "typography",
            "teaching_arc",
        },
    )
    for field, minimum, maximum in (
        ("emotional_promise", 20, 500),
        ("physical_format", 3, 200),
        ("format_rationale", 20, 1_000),
        ("visual_motif", 20, 500),
    ):
        _bounded_text(
            brief[field],
            "Release manual creative brief %s" % field,
            minimum=minimum,
            maximum=maximum,
        )
    _text_list(brief["palette"], "Release manual palette", minimum_items=3, maximum_items=8)
    _text_list(
        brief["typography"],
        "Release manual typography",
        minimum_items=2,
        maximum_items=6,
    )
    _text_list(
        brief["teaching_arc"],
        "Release manual teaching arc",
        minimum_items=3,
        maximum_items=12,
        minimum_length=8,
    )

    page_count = _pdf_pages_and_embedded_fonts(manual)
    visuals = evidence["product_visuals"]
    if isinstance(visuals, (str, bytes)) or not isinstance(visuals, Sequence) or not visuals:
        raise ContractError("Release manual requires product-derived visuals")
    made_entries = {entry.path: entry for entry in made.product_manifest.entries}
    covered_pages = set()
    seen_visuals = set()
    for item in visuals:
        visual = _mapping(
            item,
            "Release manual product visual",
            {"source_path", "source_sha256", "pages"},
        )
        source = visual["source_path"]
        pure = PurePosixPath(source) if isinstance(source, str) else PurePosixPath(".")
        entry = made_entries.get(source)
        if isinstance(source, str) and source.startswith(HOST_RENDER_SOURCE_PREFIX):
            if (
                pure.suffix.casefold() != ".png"
                or len(pure.parts) != 2
                or host_renders.get(source) != visual["source_sha256"]
                or source in seen_visuals
            ):
                raise ContractError(
                    "Release manual visual differs from the host's bound render"
                )
        elif (
            not isinstance(source, str)
            or not source
            or pure.is_absolute()
            or ".." in pure.parts
            or pure.as_posix() != source
            or pure.suffix.casefold() not in _VISUAL_SUFFIXES
            or entry is None
            or visual["source_sha256"] != entry.sha256
            or source in seen_visuals
        ):
            raise ContractError("Release manual visual differs from sealed Made bytes")
        pages = visual["pages"]
        if (
            isinstance(pages, (str, bytes))
            or not isinstance(pages, Sequence)
            or not pages
            or any(type(page) is not int or not 1 <= page <= page_count for page in pages)
            or list(pages) != sorted(set(pages))
        ):
            raise ContractError("Release manual visual page references are invalid")
        seen_visuals.add(source)
        covered_pages.update(pages)
    if 1 not in covered_pages:
        raise ContractError("Release manual cover must use an exact product visual")

    review = _mapping(
        evidence["review"],
        "Release manual review",
        {
            "page_count",
            "color_pages",
            "grayscale_pages",
            "first_time_owner_pass",
            "independent_reviewer",
            "findings",
            "resolved_changes",
            "status",
        },
    )
    expected_pages = list(range(1, page_count + 1))
    if (
        review["page_count"] != page_count
        or review["color_pages"] != expected_pages
        or review["grayscale_pages"] != expected_pages
        or review["first_time_owner_pass"] is not True
        or review["independent_reviewer"] != "native-subagent"
        or review["status"] != "approved"
    ):
        raise ContractError("Release manual review is incomplete")
    _text_list(
        review["findings"],
        "Release manual review findings",
        minimum_items=1,
        maximum_items=20,
        minimum_length=8,
        maximum_length=1_000,
    )
    _text_list(
        review["resolved_changes"],
        "Release manual resolved changes",
        minimum_items=1,
        maximum_items=20,
        minimum_length=8,
        maximum_length=1_000,
    )
    return evidence


def validate_bound_manual_design_evidence(
    package_root: Path,
    *,
    package_manifest: ArtifactManifest,
    manual_path: str,
    made: NativeMade,
    render_sources: Optional[Mapping[str, str]] = None,
) -> dict[str, Any]:
    """Recheck that evidence and manual are exact sealed Release bytes."""

    if not isinstance(package_manifest, ArtifactManifest):
        raise ContractError("manual design evidence requires a typed package manifest")
    entries = {entry.path: entry for entry in package_manifest.entries}
    evidence_entry = entries.get(MANUAL_DESIGN_EVIDENCE_PATH)
    manual_entry = entries.get(manual_path)
    if evidence_entry is None or manual_entry is None:
        raise ContractError("Release package lacks required manual design evidence")
    root = Path(package_root).resolve(strict=True)
    manual = _stable_regular(root / manual_path, "Release MANUAL.pdf", 16 * 1024 * 1024)
    evidence = _stable_regular(
        root / MANUAL_DESIGN_EVIDENCE_PATH,
        "Release MANUAL-DESIGN.json",
        MAX_MANUAL_DESIGN_EVIDENCE_BYTES,
    )
    for content, entry, label in (
        (manual, manual_entry, "Release MANUAL.pdf"),
        (evidence, evidence_entry, "Release MANUAL-DESIGN.json"),
    ):
        if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
            raise StateConflict("%s differs from its sealed manifest" % label)
    return validate_manual_design_evidence(
        root, manual=manual, made=made, render_sources=render_sources
    )


__all__ = [
    "HOST_RENDER_SOURCE_PREFIX",
    "MANUAL_DESIGN_EVIDENCE_KIND",
    "MANUAL_DESIGN_EVIDENCE_PATH",
    "MANUAL_DESIGN_EVIDENCE_SCHEMA_VERSION",
    "MAX_MANUAL_DESIGN_EVIDENCE_BYTES",
    "validate_bound_manual_design_evidence",
    "validate_manual_design_evidence",
]
