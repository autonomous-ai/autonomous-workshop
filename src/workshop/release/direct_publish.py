"""Stage a CAD project built outside Workshop as a Spark-shaped publication.

A direct publication applies only the host-owned Factory effect of Release to
a project that never ran Wish, Make or Release. This module is the
deterministic half: it reads a CAD project directory or a packed public toy
archive, and writes the same Made tree shape and schema-4 Release carrier that
Spark publishes (ADR 0061), so the unchanged Factory adapter can import,
publish and read it back. It runs no gate, authors no copy beyond what the
caller supplies, and records that no Workshop lifecycle ran. See
``docs/PUBLISH_DIRECT.md``.
"""

from __future__ import annotations

import hashlib
import json
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence

from workshop.artifacts import ArtifactManifest, build_artifact_manifest
from workshop.contributors.manifest import load_manifest
from workshop.contributors.taste import load_taste_header
from workshop.errors import ContractError
from workshop.make.contracts import Made
from workshop.release.native import (
    NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
    NATIVE_RELEASE_PRODUCT_PATH,
    make_output_release_product,
    playtest_omission_record,
)
from workshop.release.public_archive import (
    PUBLIC_ARCHIVE_SCHEMA_VERSION,
    build_public_archive_manifest,
)


DIRECT_PUBLISH_KIND = "workshop.direct-publish"
PUBLIC_TOY_ARCHIVE_KIND = "autonomous-workshop.public-toy-archive"
PUBLIC_TOY_ARCHIVE_SCOPE = "all files except MANIFEST.json and README.md"
# Factory's importer ranks this conventional root name above part solids,
# and the adapter keeps exactly one root STEP in the handoff.
MADE_PRIMARY_PATH = "assembled.step"
MADE_CAD_ROOT = "cad"
MAX_TITLE_CHARACTERS = 300
# The inverse of the toy archive's Made-tree projection.
_ARCHIVE_LAYOUT = (
    ("make/source/cad/", ""),
    ("make/models/cad/", ""),
    ("make/verification/reports/", "measure/"),
    ("make/verification/renders/", "snap/"),
)
_ARCHIVE_METADATA = frozenset(("MANIFEST.json", "README.md", "SANITIZATION.json"))
_WORKSHOP_RUN_MARKERS = ("wish", "match", "invent", "release", "make/made.json", "make/product")
# Reference and concept images are the owner's working material, not a
# listing asset; the Spark carrier likewise never ships Wish references.
_DROPPED_TOP_DIRECTORIES = {"ref": "reference material is not published"}
_DROPPED_DIRECTORIES = frozenset(("__cadgen__", "__pycache__"))
# ADR 0062: STEP is the only geometry format Workshop ships.
_MESH_SUFFIXES = frozenset(
    (".stl", ".3mf", ".glb", ".gltf", ".obj", ".ply", ".amf", ".gcode", ".bgcode")
)
_PRODUCT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_PRINTABLE = re.compile(r"^PRINTABLE\s*=\s*True\s*$", re.MULTILINE)
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_HOST_PATH = re.compile(rb"(?:/Users|/home)/[^/\s\"'<>`)]+/")
_TEXT_SUFFIXES = frozenset((".py", ".md", ".txt", ".json", ".csv", ".toml", ".yaml", ".yml"))
_STEP_SIGNATURE = b"ISO-10303-21"
# A likeness mask from an image-derived verify_project measures 1.0 here and
# a shaded render 0.00-0.18; the toy-archive publish wrapper uses the same line.
MAX_COVER_NEUTRAL_FRACTION = 0.9


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def cover_neutral_fraction(content: bytes) -> float:
    """Share of the cover's pixels that are neutral grey, black or white."""

    import io

    from PIL import Image, ImageChops

    with Image.open(io.BytesIO(content)) as image:
        red, green, blue = image.convert("RGB").split()
    spread = ImageChops.subtract(
        ImageChops.lighter(ImageChops.lighter(red, green), blue),
        ImageChops.darker(ImageChops.darker(red, green), blue),
    )
    histogram = spread.histogram()
    return sum(histogram[:4]) / sum(histogram)


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def readme_summary(content: bytes) -> tuple[Optional[str], Optional[str]]:
    """Return a README's first ``#`` heading and its first prose paragraph."""

    title: Optional[str] = None
    paragraph: list[str] = []
    for line in content.decode("utf-8", "replace").splitlines():
        stripped = line.strip()
        if title is None and stripped.startswith("# "):
            title = stripped[2:].strip()
            continue
        if stripped.startswith("#") or stripped.startswith("!["):
            if paragraph:
                break
            continue
        if not stripped:
            if paragraph:
                break
            continue
        paragraph.append(stripped)
    return title, " ".join(paragraph) or None


@dataclass(frozen=True)
class DirectSource:
    """One project's publishable files, keyed by their CAD-project path."""

    kind: str
    root: Path
    files: Mapping[str, Path]
    dropped: tuple[tuple[str, str], ...]
    readme: Optional[bytes]
    archive_sha256: Optional[str] = None
    publication: Optional[Mapping[str, Any]] = None

    def host_path_files(self) -> list[str]:
        """Text files that still name a machine's home directory."""

        return [
            path for path, source in sorted(self.files.items())
            if PurePosixPath(path).suffix.casefold() in _TEXT_SUFFIXES
            and _HOST_PATH.search(source.read_bytes())
        ]

    def entry_step(self) -> str:
        """Name the one ``PRINTABLE = True`` entry's STEP, or refuse."""

        printable = sorted(
            path[: -len(".py")]
            for path, source in self.files.items()
            if "/" not in path
            and path.endswith(".step.py")
            and _PRINTABLE.search(source.read_text(encoding="utf-8", errors="replace"))
        )
        if len(printable) != 1:
            raise ContractError(
                "pass --primary-step: %d top-level entries declare PRINTABLE = True (%s)"
                % (len(printable), ", ".join(printable) or "none")
            )
        return printable[0]


def _classify(relative: str) -> Optional[str]:
    """Return why a CAD-project file stays local, or None to keep it."""

    pure = PurePosixPath(relative)
    if any(part.startswith(".") for part in pure.parts):
        raise ContractError("hidden file in the project: %s" % relative)
    if pure.suffix.casefold() in _MESH_SUFFIXES:
        raise ContractError(
            "mesh output is not publishable (STEP only, ADR 0062): %s" % relative
        )
    if len(pure.parts) > 1 and pure.parts[0] in _DROPPED_TOP_DIRECTORIES:
        return _DROPPED_TOP_DIRECTORIES[pure.parts[0]]
    if _DROPPED_DIRECTORIES & {part.casefold() for part in pure.parts[:-1]}:
        return "derived cache"
    return None


def _regular_files(root: Path) -> list[tuple[str, Path]]:
    files = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ContractError("symlink in the project: %s" % relative)
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise ContractError("special file in the project: %s" % relative)
        files.append((relative, path))
    return files


def _select(pairs: Sequence[tuple[str, Path]]) -> tuple[dict[str, Path], list[tuple[str, str]]]:
    kept: dict[str, Path] = {}
    dropped: list[tuple[str, str]] = []
    for relative, path in pairs:
        reason = _classify(relative)
        if reason is not None:
            dropped.append((relative, reason))
        elif relative in kept:
            raise ContractError("two archive files map to one project path: %s" % relative)
        else:
            kept[relative] = path
    return kept, dropped


def load_cad_project(root: Path) -> DirectSource:
    """Read a CAD project in its own layout (``snap/``, ``measure/``, sources)."""

    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ContractError("--cad-dir must be a directory")
    files, dropped = _select(_regular_files(root))
    readme = files.get("README.md")
    return DirectSource(
        kind="cad-project",
        root=root,
        files=files,
        dropped=tuple(dropped),
        readme=readme.read_bytes() if readme is not None else None,
    )


def load_public_toy_archive(root: Path) -> DirectSource:
    """Verify a packed toy archive against its manifest and map it back.

    Only the ``make/`` projection a CAD-project pack writes is accepted; an
    archive projected from a Workshop run already has its own Release and is
    published through ``workshop publish``, not here.
    """

    root = Path(root).resolve(strict=True)
    try:
        document = json.loads((root / "MANIFEST.json").read_bytes())
    except (OSError, ValueError) as exc:
        raise ContractError("archive MANIFEST.json is unreadable") from exc
    if (
        not isinstance(document, Mapping)
        or document.get("kind") != PUBLIC_TOY_ARCHIVE_KIND
        or document.get("schema_version") != PUBLIC_ARCHIVE_SCHEMA_VERSION
        or document.get("scope") != PUBLIC_TOY_ARCHIVE_SCOPE
    ):
        raise ContractError("not a schema 4 public toy archive")
    observed = build_public_archive_manifest(root).to_dict()
    if observed != document.get("artifact_manifest"):
        recorded = {
            entry.get("path"): entry
            for entry in (document.get("artifact_manifest") or {}).get("entries", [])
            if isinstance(entry, Mapping)
        }
        current = {entry["path"]: entry for entry in observed["entries"]}
        changed = sorted(
            path for path in recorded.keys() | current.keys()
            if recorded.get(path) != current.get(path)
        )
        raise ContractError(
            "archive differs from its MANIFEST.json: %s" % ", ".join(map(str, changed[:20]))
        )
    for marker in _WORKSHOP_RUN_MARKERS:
        if (root / marker).exists():
            raise ContractError(
                "archive was projected from a Workshop run (%s); publish it with "
                "`workshop publish`" % marker
            )
    publication = None
    pairs: list[tuple[str, Path]] = []
    for entry in observed["entries"]:
        path = entry["path"]
        if path in _ARCHIVE_METADATA:
            continue
        if path == "publication/PUBLICATION.json":
            try:
                publication = json.loads((root / path).read_bytes())
            except ValueError as exc:
                raise ContractError("archive publication record is malformed") from exc
            continue
        mapped = next(
            (target + path[len(prefix):] for prefix, target in _ARCHIVE_LAYOUT if path.startswith(prefix)),
            None,
        )
        if mapped is None:
            raise ContractError("archive file outside the CAD projection: %s" % path)
        pairs.append((mapped, root / path))
    files, dropped = _select(sorted(pairs))
    readme = files.get("README.md")
    return DirectSource(
        kind="public-toy-archive",
        root=root,
        files=files,
        dropped=tuple(dropped),
        readme=readme.read_bytes() if readme is not None else None,
        archive_sha256=observed["artifact_sha256"],
        publication=publication if isinstance(publication, Mapping) else None,
    )


def inventor_name(inventors_root: Path, inventor_id: str) -> str:
    """Resolve a roster Inventor's display name; the id must exist."""

    if not isinstance(inventor_id, str) or _PRODUCT_ID.fullmatch(inventor_id) is None:
        raise ContractError("--inventor must be a canonical inventor id")
    folder = Path(inventors_root) / inventor_id
    if not (folder / "inventor.json").is_file():
        raise ContractError("no Inventor %r under %s" % (inventor_id, inventors_root))
    if load_manifest(folder / "inventor.json").inventor_id != inventor_id:
        raise ContractError("inventor.json id differs from its folder %s" % inventor_id)
    return load_taste_header(folder).name


@dataclass(frozen=True)
class DirectPublishProvenance:
    """Stands where a Wish would: what was published, and that nothing ran.

    ``FactoryReleaseWriter`` records ``to_dict()`` as the ``wish`` member of
    ``workshop-product-facts.json``. A direct publication has no Wish, so the
    record says so instead of inventing one.
    """

    product_id: str
    source_kind: str
    source_name: str
    source_artifact_sha256: Optional[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "kind": DIRECT_PUBLISH_KIND,
            "product_id": self.product_id,
            "wish": None,
            "workshop_lifecycle": "not-run",
            "source": {
                "kind": self.source_kind,
                "name": self.source_name,
                "artifact_sha256": self.source_artifact_sha256,
            },
        }


@dataclass(frozen=True)
class _InventorName:
    name: str


@dataclass(frozen=True)
class DirectPublishContext:
    """The context ``FactoryReleaseWriter`` reads, for a direct publication."""

    made: Made
    wish: DirectPublishProvenance
    taste: _InventorName
    public_title: Optional[str] = None
    token_usage: Optional[Mapping[str, Any]] = None
    cover_render: Optional[bytes] = None

    def assert_current(self) -> None:
        self.made.assert_current()


@dataclass(frozen=True)
class DirectPublication:
    """A staged Made tree and sealed Release carrier, ready for the adapter."""

    context: DirectPublishContext
    release_root: Path
    release_manifest: ArtifactManifest
    page: Mapping[str, Any]
    primary_source: str
    cover_path: str


def _write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)
    path.chmod(0o644)


def _text_list(values: Sequence[str], label: str) -> list[str]:
    result = []
    for value in values:
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ContractError("%s entries must be non-empty trimmed text" % label)
        result.append(value)
    return result


def stage_direct_publication(
    source: DirectSource,
    workspace: Path,
    *,
    product_id: str,
    inventor_display_name: str,
    primary_step: str,
    title: str,
    summary: str,
    what_arrives: Sequence[str] = (),
    limitations: Sequence[str] = (),
) -> DirectPublication:
    """Write ``made/`` and ``release/`` under an empty private ``workspace``.

    The Made tree is ``product.json`` (title, summary and any owner-supplied
    lists), the primary STEP as ``assembled.step`` and every kept project file
    under ``cad/``. The carrier is derived exactly as Spark derives it.
    """

    workspace = Path(workspace)
    if not workspace.is_absolute() or not workspace.is_dir() or any(workspace.iterdir()):
        raise ContractError("direct publication workspace must be an empty absolute directory")
    if _PRODUCT_ID.fullmatch(product_id or "") is None:
        raise ContractError("--product-id must be a lowercase kebab-case slug")
    for label, value in (("title", title), ("summary", summary)):
        if not isinstance(value, str) or not value.strip() or value != value.strip():
            raise ContractError("%s must be non-empty trimmed text" % label)
    if len(title) > MAX_TITLE_CHARACTERS:
        raise ContractError("title exceeds %d characters" % MAX_TITLE_CHARACTERS)
    if "/" in primary_step or not primary_step.endswith(".step"):
        raise ContractError("--primary-step must name a top-level .step file")
    primary = source.files.get(primary_step)
    if primary is None:
        raise ContractError("primary model %s is not in the project" % primary_step)
    primary_content = primary.read_bytes()
    if not primary_content.startswith(_STEP_SIGNATURE):
        raise ContractError("primary model %s is not a STEP file" % primary_step)
    cover = source.files.get("snap/iso.png")
    cover_content = cover.read_bytes() if cover is not None else b""
    if not cover_content.startswith(_PNG_SIGNATURE):
        raise ContractError("Factory needs snap/iso.png as the cover, and it must be a PNG")
    neutral = cover_neutral_fraction(cover_content)
    if neutral > MAX_COVER_NEUTRAL_FRACTION:
        raise ContractError(
            "snap/iso.png is a black-and-white likeness mask (%.0f%% neutral grey), "
            "not a shaded hero; render the cover again" % (neutral * 100)
        )
    covers = [path for path in source.files if PurePosixPath(path).parts[-2:] == ("snap", "iso.png")]
    if covers != ["snap/iso.png"]:
        raise ContractError("exactly one snap/iso.png may ship; found %s" % ", ".join(covers))

    facts: dict[str, Any] = {"title": title, "summary": summary}
    for name, values in (("what_arrives", what_arrives), ("limitations", limitations)):
        if values:
            facts[name] = _text_list(values, name)
    made_root = workspace / "made"
    made_root.mkdir()
    _write(made_root / "product.json", _canonical_json(facts) + b"\n")
    _write(made_root / MADE_PRIMARY_PATH, primary_content)
    for relative, path in sorted(source.files.items()):
        _write(made_root / MADE_CAD_ROOT / relative, path.read_bytes())
    made = Made.from_root(made_root, facts)

    entries = made.artifact_manifest.entries
    readmes = sorted(
        (entry for entry in entries if entry.bytes > 0 and PurePosixPath(entry.path).name == "README.md"),
        key=lambda entry: (entry.path != "README.md", entry.path),
    )
    document = readmes[0] if readmes else None
    page = make_output_release_product(
        facts,
        product_artifact_sha256=made.artifact_sha256,
        source_document=None if document is None else {
            "source_path": document.path, "sha256": document.sha256,
        },
    )
    release_root = workspace / "release"
    release_root.mkdir()
    _write(release_root / NATIVE_RELEASE_PRODUCT_PATH, _canonical_json(page))
    _write(
        release_root / NATIVE_RELEASE_PLAYTEST_OMISSION_PATH,
        _canonical_json(playtest_omission_record()),
    )
    if document is not None:
        content = (made_root / document.path).read_bytes()
        if hashlib.sha256(content).hexdigest() != document.sha256:
            raise ContractError("Made README changed while staging")
        _write(release_root / "README.md", content)

    context = DirectPublishContext(
        made=made,
        wish=DirectPublishProvenance(
            product_id=product_id,
            source_kind=source.kind,
            source_name=source.root.name,
            source_artifact_sha256=source.archive_sha256,
        ),
        taste=_InventorName(inventor_display_name),
    )
    return DirectPublication(
        context=context,
        release_root=release_root.resolve(strict=True),
        release_manifest=build_artifact_manifest(release_root, created_at="content-addressed"),
        page=page,
        primary_source=primary_step,
        cover_path=MADE_CAD_ROOT + "/snap/iso.png",
    )


__all__ = [
    "DIRECT_PUBLISH_KIND",
    "DirectPublication",
    "DirectPublishContext",
    "DirectPublishProvenance",
    "DirectSource",
    "MAX_COVER_NEUTRAL_FRACTION",
    "cover_neutral_fraction",
    "inventor_name",
    "load_cad_project",
    "load_public_toy_archive",
    "readme_summary",
    "slugify",
    "stage_direct_publication",
]
