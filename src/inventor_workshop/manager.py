"""Progressive, Taste-bound routing of one Wish to one inventor.

Discovery reads operational manifests and compact TASTE frontmatter. A pluggable
semantic retriever chooses a small finalist set from TASTE name and description
alone, and only then are the finalists' complete Tastes loaded for semantic
judgment. The manager emits one assignment; it does not poll, schedule, or imply
continuously running inventors.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Protocol, Sequence, Tuple

from .errors import ContractError, ManifestError
from .jobs import Need, WaitingFor
from .make import Wish
from .manifest import InventorManifest, inventor_collection, validate_entrypoints
from .models import require_exact_version, require_sha256
from .taste import Taste, TasteHeader, load_taste, load_taste_header


MAX_MANIFEST_BYTES = 256 * 1024
MAX_CATALOG_INVENTORS = 20_000
MAX_FINALISTS = 64
MAX_PAGE_SIZE = 200
MAX_CARD_DESCRIPTION_CHARS = 512
MAX_IMPLEMENTATION_FILES = 5_000
MAX_IMPLEMENTATION_FILE_BYTES = 8 * 1024 * 1024
MAX_IMPLEMENTATION_BYTES = 64 * 1024 * 1024
_ROUTABLE_STATUSES = frozenset(("active", "experimental"))
_IMPLEMENTATION_TOP_LEVEL_IGNORES = frozenset(
    (
        ".git",
        ".pytest_cache",
        ".workshop",
        "__pycache__",
        "build",
        "dist",
        # These are shared Workshop dependencies, not inventor-owned
        # contribution files. Shared engine/skill release provenance must bind
        # their versions separately instead of following links out of this root.
        "skills",
        # Checked-in and generated product bundles are outputs of contribution
        # code. Creating another toy must not rewrite the Inventor assignment.
        "toys",
    )
)
_IMPLEMENTATION_CACHE_DIRECTORIES = frozenset((".pytest_cache", "__pycache__"))
_IMPLEMENTATION_PACKAGING_SUFFIXES = (".egg-info", ".dist-info")


def _text(value: Any, label: str, maximum: int = 10_000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\r\t" for character in value)
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded, non-empty text" % label)
    return value


def _texts(
    value: Sequence[str], label: str, *, allow_empty: bool = True, maximum: int = 100
) -> Tuple[str, ...]:
    if isinstance(value, (str, bytes, Mapping)):
        raise ContractError("%s must be a sequence of text values" % label)
    try:
        copied = tuple(value)
    except TypeError as exc:
        raise ContractError("%s must be a sequence of text values" % label) from exc
    if not allow_empty and not copied:
        raise ContractError("%s must not be empty" % label)
    if len(copied) > maximum:
        raise ContractError("%s must contain at most %d values" % (label, maximum))
    for item in copied:
        _text(item, label, 4_000)
    return copied


def _sha256_json(value: Mapping[str, Any]) -> str:
    try:
        payload = json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("routing identity must be JSON-safe") from exc
    return hashlib.sha256(payload).hexdigest()


def _judge_receipt(
    identity: Any, version: Any, config_sha256: Any
) -> Dict[str, str]:
    """Validate content-bound judge/model/prompt-policy provenance."""

    identity = _text(identity, "judge_identity", 500)
    if identity != identity.strip() or any(ord(character) < 32 for character in identity):
        raise ContractError("judge_identity must be bounded, single-line text")
    version = require_exact_version(version, "judge_version")
    require_sha256(config_sha256, "judge_config_sha256")
    return {
        "identity": identity,
        "version": version,
        "config_sha256": config_sha256,
    }


def _inspect_regular(
    path: Path, label: str, maximum: int, *, allow_empty: bool = False
) -> os.stat_result:
    try:
        observed = path.lstat()
    except FileNotFoundError:
        raise ManifestError("missing %s: %s" % (label, path))
    except OSError as exc:
        raise ManifestError("cannot inspect %s: %s" % (path, exc)) from exc
    if path.is_symlink() or not stat.S_ISREG(observed.st_mode):
        raise ManifestError("%s must be a regular file: %s" % (label, path))
    minimum = 0 if allow_empty else 1
    if observed.st_size < minimum or observed.st_size > maximum:
        raise ManifestError(
            "%s must contain %d to %d bytes: %s" % (label, minimum, maximum, path)
        )
    return observed


def _read_regular_snapshot(
    path: Path, label: str, maximum: int, *, allow_empty: bool = False
) -> Tuple[bytes, os.stat_result]:
    """Read a bounded regular file and return the exact opened-file metadata."""

    expected = _inspect_regular(path, label, maximum, allow_empty=allow_empty)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ManifestError("cannot safely open %s: %s" % (path, exc)) from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (
            expected.st_dev,
            expected.st_ino,
        ):
            raise ManifestError("%s changed while opening: %s" % (label, path))
        chunks = []
        observed = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, maximum + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > maximum:
                raise ManifestError("%s exceeds %d bytes: %s" % (label, maximum, path))
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ManifestError("%s changed while reading: %s" % (label, path))
        return b"".join(chunks), opened
    finally:
        os.close(descriptor)


def _read_regular_bytes(
    path: Path, label: str, maximum: int, *, allow_empty: bool = False
) -> bytes:
    """Read a bounded regular file without following a raced final symlink."""

    source, _ = _read_regular_snapshot(
        path, label, maximum, allow_empty=allow_empty
    )
    return source


def _load_manifest_snapshot(path: Path) -> Tuple[InventorManifest, str]:
    source = _read_regular_bytes(path, "inventor manifest", MAX_MANIFEST_BYTES)
    try:
        raw = json.loads(source.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ManifestError("cannot read %s: %s" % (path, exc)) from exc
    if not isinstance(raw, Mapping):
        raise ManifestError("%s: top level must be an object" % path)
    return InventorManifest.parse(raw, path), hashlib.sha256(source).hexdigest()


def _ignored_implementation_directory(relative: Path) -> bool:
    if not relative.parts:
        return False
    if len(relative.parts) == 1 and relative.name in _IMPLEMENTATION_TOP_LEVEL_IGNORES:
        return True
    return (
        relative.name in _IMPLEMENTATION_CACHE_DIRECTORIES
        or relative.name.endswith(_IMPLEMENTATION_PACKAGING_SUFFIXES)
    )


def _implementation_sha256(root: Path) -> str:
    """Fingerprint every bounded inventor-owned contribution file.

    Generated Workshop state, product bundles, packaging output, caches, and
    shared Workshop skill links are explicitly outside this identity. Everything
    else—including prompts, configs, assets, tests, and documentation—is bound.
    """

    records = []
    total = 0
    requested = Path(root)
    if requested.is_symlink() or not requested.is_dir():
        raise ManifestError(
            "inventor implementation root must be a regular directory: %s" % requested
        )
    try:
        implementation_root = requested.resolve(strict=True)
    except OSError as exc:
        raise ManifestError(
            "cannot resolve inventor implementation %s: %s" % (requested, exc)
        ) from exc
    try:
        def walk_error(error: OSError) -> None:
            raise ManifestError(
                "cannot enumerate inventor contribution %s: %s"
                % (implementation_root, error)
            ) from error

        walker = os.walk(
            implementation_root,
            topdown=True,
            onerror=walk_error,
            followlinks=False,
        )
        for current_value, directory_names, file_names in walker:
            current = Path(current_value)
            relative_parent = current.relative_to(implementation_root)
            kept_directories = []
            for name in sorted(directory_names):
                relative = relative_parent / name
                if _ignored_implementation_directory(relative):
                    continue
                candidate = current / name
                try:
                    metadata = candidate.lstat()
                except OSError as exc:
                    raise ManifestError(
                        "cannot inspect inventor contribution directory %s: %s"
                        % (candidate, exc)
                    ) from exc
                if stat.S_ISLNK(metadata.st_mode):
                    raise ManifestError(
                        "inventor contribution must not contain symlinks: %s"
                        % candidate
                    )
                if not stat.S_ISDIR(metadata.st_mode):
                    raise ManifestError(
                        "inventor contribution tree contains an unsafe directory: %s"
                        % candidate
                    )
                kept_directories.append(name)
            directory_names[:] = kept_directories

            for name in sorted(file_names):
                path = current / name
                relative = path.relative_to(implementation_root)
                try:
                    listed = path.lstat()
                except OSError as exc:
                    raise ManifestError(
                        "cannot inspect inventor contribution file %s: %s"
                        % (path, exc)
                    ) from exc
                if stat.S_ISLNK(listed.st_mode):
                    raise ManifestError(
                        "inventor contribution must not contain symlinks: %s" % path
                    )
                source, metadata = _read_regular_snapshot(
                    path,
                    "inventor contribution file",
                    MAX_IMPLEMENTATION_FILE_BYTES,
                    allow_empty=True,
                )
                total += len(source)
                if total > MAX_IMPLEMENTATION_BYTES:
                    raise ManifestError(
                        "inventor contribution exceeds %d bytes: %s"
                        % (MAX_IMPLEMENTATION_BYTES, implementation_root)
                    )
                records.append(
                    {
                        "path": relative.as_posix(),
                        "sha256": hashlib.sha256(source).hexdigest(),
                        "executable": bool(metadata.st_mode & stat.S_IXUSR),
                    }
                )
                if len(records) > MAX_IMPLEMENTATION_FILES:
                    raise ManifestError(
                        "inventor contribution exceeds %d files: %s"
                        % (MAX_IMPLEMENTATION_FILES, implementation_root)
                    )
    except OSError as exc:
        raise ManifestError(
            "cannot enumerate inventor contribution %s: %s"
            % (implementation_root, exc)
        ) from exc
    if not records:
        raise ManifestError(
            "inventor contribution has no bounded regular files: %s"
            % implementation_root
        )
    return _sha256_json({"schema_version": 2, "files": records})


def _paired_inventor_directories(collection: Path) -> Tuple[Path, ...]:
    try:
        entries = sorted(collection.iterdir(), key=lambda item: item.name)
    except OSError as exc:
        raise ManifestError("cannot list inventor collection %s: %s" % (collection, exc)) from exc
    pairs = []
    for entry in entries:
        if entry.is_symlink():
            raise ManifestError("inventor collection must not contain symlinks: %s" % entry)
        if not entry.is_dir():
            continue
        manifest_path = entry / "inventor.json"
        taste_path = entry / "TASTE.md"
        has_manifest = manifest_path.exists() or manifest_path.is_symlink()
        has_taste = taste_path.exists() or taste_path.is_symlink()
        if not has_manifest and not has_taste:
            continue
        if has_manifest != has_taste:
            missing = taste_path if has_manifest else manifest_path
            raise ManifestError("inventor folder is missing %s" % missing)
        pairs.append(entry)
        if len(pairs) > MAX_CATALOG_INVENTORS:
            raise ManifestError(
                "inventor catalog exceeds the safe limit of %d" % MAX_CATALOG_INVENTORS
            )
    if not pairs:
        raise ManifestError("inventor collection has no immediate manifests: %s" % collection)
    return tuple(pairs)


@dataclass(frozen=True)
class InventorCard:
    """Compact routing card whose semantic prose comes only from TASTE."""

    inventor_id: str
    name: str
    description: str
    status: str
    source_kind: str
    entrypoint: Sequence[str]
    manifest_path: Path
    manifest_sha256: str
    taste_path: Path
    taste_header_sha256: str
    schema_version: int = 1
    card_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("InventorCard schema_version must be 1")
        _text(self.inventor_id, "InventorCard inventor_id", 64)
        _text(self.name, "InventorCard name", 200)
        _text(self.description, "InventorCard description", MAX_CARD_DESCRIPTION_CHARS)
        _text(self.status, "InventorCard status", 100)
        _text(self.source_kind, "InventorCard source_kind", 100)
        entrypoint = _texts(self.entrypoint, "InventorCard entrypoint", allow_empty=False)
        manifest_path = Path(self.manifest_path)
        taste_path = Path(self.taste_path)
        if (
            not manifest_path.is_absolute()
            or manifest_path.name != "inventor.json"
            or not taste_path.is_absolute()
            or taste_path.name != "TASTE.md"
            or manifest_path.parent != taste_path.parent
            or manifest_path.parent.name != self.inventor_id
        ):
            raise ContractError("InventorCard files must share their id-named folder")
        require_sha256(self.manifest_sha256, "InventorCard manifest_sha256")
        require_sha256(self.taste_header_sha256, "InventorCard taste_header_sha256")
        object.__setattr__(self, "entrypoint", entrypoint)
        object.__setattr__(self, "manifest_path", manifest_path)
        object.__setattr__(self, "taste_path", taste_path)
        object.__setattr__(self, "card_sha256", _sha256_json(self._identity_dict()))

    @classmethod
    def from_sources(
        cls,
        manifest: InventorManifest,
        manifest_sha256: str,
        header: TasteHeader,
    ) -> "InventorCard":
        if header.path != manifest.path.parent / "TASTE.md":
            raise ManifestError("Taste header belongs to a different inventor")
        return cls(
            inventor_id=manifest.inventor_id,
            name=header.name,
            description=header.description,
            status=manifest.status,
            source_kind=str(manifest.source.get("kind")),
            entrypoint=manifest.entrypoint,
            manifest_path=manifest.path,
            manifest_sha256=manifest_sha256,
            taste_path=manifest.path.parent / "TASTE.md",
            taste_header_sha256=header.sha256,
        )

    @property
    def root(self) -> Path:
        return self.manifest_path.parent

    @property
    def routable(self) -> bool:
        return self.status in _ROUTABLE_STATUSES

    def to_routing_dict(self, *, include_description: bool = True) -> Dict[str, Any]:
        payload = {
            "id": self.inventor_id,
            "name": self.name,
            "status": self.status,
            "routable": self.routable,
            "manifest_sha256": self.manifest_sha256,
            "taste_header_sha256": self.taste_header_sha256,
        }
        if include_description:
            payload["description"] = self.description
        else:
            payload["description_omitted"] = True
        return payload

    def _identity_dict(self) -> Dict[str, Any]:
        payload = self.to_routing_dict(include_description=True)
        payload["source_kind"] = self.source_kind
        payload["entrypoint"] = list(self.entrypoint)
        return payload

    def assert_manifest_current(self) -> None:
        source = _read_regular_bytes(
            self.manifest_path, "inventor manifest", MAX_MANIFEST_BYTES
        )
        if hashlib.sha256(source).hexdigest() != self.manifest_sha256:
            raise ManifestError("inventor manifest changed after cataloging: %s" % self.root)

    def assert_catalog_current(self) -> None:
        self.assert_manifest_current()
        header = load_taste_header(self.root)
        if (
            header.sha256 != self.taste_header_sha256
            or header.name != self.name
            or header.description != self.description
        ):
            raise ManifestError("inventor Taste header changed after cataloging: %s" % self.root)

    def assert_entrypoint_current(self) -> None:
        manifest, digest = _load_manifest_snapshot(self.manifest_path)
        if digest != self.manifest_sha256:
            raise ManifestError("inventor manifest changed after cataloging: %s" % self.root)
        problems = validate_entrypoints((manifest,))
        if problems:
            raise ManifestError("; ".join(problems))


@dataclass(frozen=True)
class CatalogPage:
    """One deterministic page for a semantic retriever or external indexer."""

    catalog_sha256: str
    total: int
    cursor: int
    next_cursor: Optional[int]
    cards: Sequence[InventorCard]
    include_descriptions: bool
    schema_version: int = 1
    page_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("CatalogPage schema_version must be 1")
        require_sha256(self.catalog_sha256, "CatalogPage catalog_sha256")
        if type(self.total) is not int or self.total < 1:
            raise ContractError("CatalogPage total must be positive")
        if type(self.cursor) is not int or not 0 <= self.cursor < self.total:
            raise ContractError("CatalogPage cursor is outside the catalog")
        if self.next_cursor is not None and (
            type(self.next_cursor) is not int
            or not self.cursor < self.next_cursor < self.total
        ):
            raise ContractError("CatalogPage next_cursor is invalid")
        if type(self.include_descriptions) is not bool:
            raise ContractError("CatalogPage include_descriptions must be boolean")
        cards = tuple(self.cards)
        if not cards or len(cards) > MAX_PAGE_SIZE or not all(
            isinstance(item, InventorCard) for item in cards
        ):
            raise ContractError("CatalogPage requires 1 to %d cards" % MAX_PAGE_SIZE)
        object.__setattr__(self, "cards", cards)
        object.__setattr__(self, "page_sha256", _sha256_json(self._identity_dict()))

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "catalog_sha256": self.catalog_sha256,
            "total": self.total,
            "cursor": self.cursor,
            "next_cursor": self.next_cursor,
            "include_descriptions": self.include_descriptions,
            "cards": [
                item.to_routing_dict(include_description=self.include_descriptions)
                for item in self.cards
            ],
        }

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["page_sha256"] = self.page_sha256
        return payload


@dataclass(frozen=True)
class InventorCatalog:
    """A bounded snapshot with paged access to compact inventor cards."""

    collection: Path
    cards: Sequence[InventorCard]
    schema_version: int = 1
    catalog_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("InventorCatalog schema_version must be 1")
        collection = Path(self.collection)
        if not collection.is_absolute() or not collection.is_dir() or collection.is_symlink():
            raise ContractError("InventorCatalog collection must be an absolute regular directory")
        cards = tuple(sorted(tuple(self.cards), key=lambda item: item.inventor_id))
        if (
            not cards
            or len(cards) > MAX_CATALOG_INVENTORS
            or not all(isinstance(item, InventorCard) for item in cards)
        ):
            raise ContractError(
                "InventorCatalog requires 1 to %d typed cards" % MAX_CATALOG_INVENTORS
            )
        ids = tuple(item.inventor_id for item in cards)
        if len(ids) != len(set(ids)):
            raise ContractError("InventorCatalog inventor ids must be unique")
        object.__setattr__(self, "collection", collection.resolve(strict=True))
        object.__setattr__(self, "cards", cards)
        object.__setattr__(self, "catalog_sha256", _sha256_json(self._identity_dict()))

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cards": [item._identity_dict() for item in self.cards],
        }

    def receipt(self) -> Dict[str, Any]:
        """Return catalog identity without dumping every card into a prompt."""

        return {
            "schema_version": self.schema_version,
            "catalog_sha256": self.catalog_sha256,
            "total": len(self.cards),
            "max_page_size": MAX_PAGE_SIZE,
        }

    def page(
        self,
        *,
        cursor: int = 0,
        limit: int = 50,
        include_descriptions: bool = True,
    ) -> CatalogPage:
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
            raise ContractError("catalog page limit must be from 1 to %d" % MAX_PAGE_SIZE)
        if type(cursor) is not int or not 0 <= cursor < len(self.cards):
            raise ContractError("catalog page cursor is outside the catalog")
        if type(include_descriptions) is not bool:
            raise ContractError("include_descriptions must be boolean")
        end = min(cursor + limit, len(self.cards))
        return CatalogPage(
            catalog_sha256=self.catalog_sha256,
            total=len(self.cards),
            cursor=cursor,
            next_cursor=end if end < len(self.cards) else None,
            cards=self.cards[cursor:end],
            include_descriptions=include_descriptions,
        )

    def card(self, inventor_id: str) -> InventorCard:
        for item in self.cards:
            if item.inventor_id == inventor_id:
                return item
        raise ContractError("shortlist names unknown inventor %r" % inventor_id)

    def assert_current(self) -> None:
        directories = _paired_inventor_directories(self.collection)
        if tuple(item.name for item in directories) != tuple(item.inventor_id for item in self.cards):
            raise ManifestError("inventor catalog membership changed after discovery")
        for card in self.cards:
            card.assert_catalog_current()
        if self.catalog_sha256 != _sha256_json(self._identity_dict()):
            raise ContractError("InventorCatalog identity changed")


def discover_inventor_catalog(root: Path) -> InventorCatalog:
    """Read immediate manifests and inspect—but do not read—paired Tastes."""

    requested = Path(root)
    if requested.is_symlink():
        raise ManifestError("inventor collection root must not be a symlink: %s" % requested)
    try:
        collection = inventor_collection(requested)
    except (OSError, RuntimeError) as exc:
        raise ManifestError("cannot resolve inventor collection %s: %s" % (requested, exc)) from exc

    cards = []
    manifests = []
    seen = set()
    for entry in _paired_inventor_directories(collection):
        before = entry.lstat()
        manifest, manifest_sha256 = _load_manifest_snapshot(entry / "inventor.json")
        # Discovery reads only the strict skill-like frontmatter. The creative
        # constitution body remains undisclosed until semantic shortlisting.
        header = load_taste_header(entry)
        after = entry.lstat()
        if (
            not stat.S_ISDIR(after.st_mode)
            or (after.st_dev, after.st_ino) != (before.st_dev, before.st_ino)
            or after.st_mtime_ns != before.st_mtime_ns
        ):
            raise ManifestError("inventor folder changed while cataloging: %s" % entry)
        if manifest.inventor_id in seen:
            raise ManifestError("duplicate inventor id %r" % manifest.inventor_id)
        seen.add(manifest.inventor_id)
        manifests.append(manifest)
        cards.append(InventorCard.from_sources(manifest, manifest_sha256, header))

    entrypoint_problems = validate_entrypoints(manifests)
    if entrypoint_problems:
        raise ManifestError("; ".join(entrypoint_problems))
    return InventorCatalog(collection=collection, cards=cards)


@dataclass(frozen=True)
class RoutingContext:
    """One exact Wish plus paged access to a compact catalog snapshot."""

    wish: Wish
    catalog: InventorCatalog
    schema_version: int = 1
    verify_live_catalog: bool = True
    wish_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("RoutingContext schema_version must be 1")
        if not isinstance(self.wish, Wish) or not isinstance(self.catalog, InventorCatalog):
            raise ContractError("RoutingContext requires one Wish and one InventorCatalog")
        if type(self.verify_live_catalog) is not bool:
            raise ContractError("RoutingContext verify_live_catalog must be boolean")
        payload = self.wish.to_dict()
        snapshot = Wish(
            schema_version=payload["schema_version"],
            product_id=payload["product_id"],
            objective=payload["objective"],
            constraints=payload["constraints"],
            context=payload["context"],
        )
        object.__setattr__(self, "wish", snapshot)
        object.__setattr__(self, "wish_sha256", _sha256_json(snapshot.to_dict()))

    def audit_receipt(self) -> Dict[str, Any]:
        """Return public routing identity without private Wish fields or cards."""

        if self.wish_sha256 != _sha256_json(self.wish.to_dict()):
            raise ContractError("Wish changed during inventor routing")
        return {
            "schema_version": self.schema_version,
            "wish_sha256": self.wish_sha256,
            "catalog": self.catalog.receipt(),
            "catalog_validation": (
                "live-files" if self.verify_live_catalog else "versioned-provider"
            ),
        }

    def retrieval_page(
        self,
        *,
        cursor: int = 0,
        limit: int = 50,
        include_descriptions: bool = True,
    ) -> Dict[str, Any]:
        return {
            "request": self.audit_receipt(),
            "page": self.catalog.page(
                cursor=cursor,
                limit=limit,
                include_descriptions=include_descriptions,
            ).to_dict(),
        }

    def assert_current(self) -> None:
        self.assert_snapshot_identity()
        if self.verify_live_catalog:
            self.catalog.assert_current()

    def assert_snapshot_identity(self) -> None:
        if self.wish_sha256 != _sha256_json(self.wish.to_dict()):
            raise ContractError("Wish changed during inventor routing")
        if self.catalog.catalog_sha256 != _sha256_json(self.catalog._identity_dict()):
            raise ContractError("InventorCatalog identity changed")


@dataclass(frozen=True)
class Shortlist:
    """Auditable semantic retrieval result for one Wish and catalog snapshot."""

    wish_sha256: str
    catalog_sha256: str
    inventor_ids: Sequence[str]
    card_sha256s: Sequence[str]
    retriever: str
    retriever_version: str
    rationale: str
    schema_version: int = 1
    shortlist_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Shortlist schema_version must be 1")
        require_sha256(self.wish_sha256, "Shortlist wish_sha256")
        require_sha256(self.catalog_sha256, "Shortlist catalog_sha256")
        ids = _texts(
            self.inventor_ids,
            "Shortlist inventor id",
            allow_empty=False,
            maximum=MAX_FINALISTS,
        )
        if len(ids) != len(set(ids)):
            raise ContractError("Shortlist inventor ids must be unique")
        hashes = _texts(
            self.card_sha256s,
            "Shortlist card sha256",
            allow_empty=False,
            maximum=MAX_FINALISTS,
        )
        if len(hashes) != len(ids):
            raise ContractError("Shortlist requires one card hash per inventor")
        for digest in hashes:
            require_sha256(digest, "Shortlist card sha256")
        _text(self.retriever, "Shortlist retriever", 500)
        _text(self.retriever_version, "Shortlist retriever_version", 500)
        _text(self.rationale, "Shortlist rationale", 12_000)
        object.__setattr__(self, "inventor_ids", ids)
        object.__setattr__(self, "card_sha256s", hashes)
        object.__setattr__(self, "shortlist_sha256", _sha256_json(self._identity_dict()))

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "wish_sha256": self.wish_sha256,
            "catalog_sha256": self.catalog_sha256,
            "cards": [
                {"inventor_id": inventor_id, "card_sha256": digest}
                for inventor_id, digest in zip(self.inventor_ids, self.card_sha256s)
            ],
            "retriever": self.retriever,
            "retriever_version": self.retriever_version,
            "rationale": self.rationale,
        }

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["shortlist_sha256"] = self.shortlist_sha256
        return payload


def create_shortlist(
    context: RoutingContext,
    inventor_ids: Sequence[str],
    *,
    retriever: str,
    retriever_version: str,
    rationale: str,
) -> Shortlist:
    if not isinstance(context, RoutingContext):
        raise ContractError("create_shortlist requires a RoutingContext")
    if isinstance(inventor_ids, (str, bytes, Mapping)):
        raise ContractError("create_shortlist inventor_ids must be a sequence")
    try:
        inventor_ids = tuple(inventor_ids)
    except TypeError as exc:
        raise ContractError("create_shortlist inventor_ids must be a sequence") from exc
    shortlist = Shortlist(
        wish_sha256=context.wish_sha256,
        catalog_sha256=context.catalog.catalog_sha256,
        inventor_ids=inventor_ids,
        card_sha256s=[context.catalog.card(item).card_sha256 for item in inventor_ids],
        retriever=retriever,
        retriever_version=retriever_version,
        rationale=rationale,
    )
    for inventor_id, card_sha256 in zip(
        shortlist.inventor_ids, shortlist.card_sha256s
    ):
        card = context.catalog.card(inventor_id)
        if card.card_sha256 != card_sha256:
            raise ContractError("shortlist contains a stale card for %s" % inventor_id)
        if not card.routable:
            raise ContractError("shortlist includes non-routable inventor %s" % inventor_id)
    return shortlist


def shortlist_all(
    context: RoutingContext,
    *,
    retriever: str,
    retriever_version: str,
    rationale: str,
) -> Shortlist:
    """Explicitly shortlist every routable card when the catalog is small enough."""

    return create_shortlist(
        context,
        [item.inventor_id for item in context.catalog.cards if item.routable],
        retriever=retriever,
        retriever_version=retriever_version,
        rationale=rationale,
    )


class InventorRetriever(Protocol):
    """Application-supplied semantic retrieval over compact paged cards."""

    def __call__(self, context: RoutingContext) -> Shortlist:
        ...


class InventorRetrieverRequired(WaitingFor):
    def __init__(self, context: RoutingContext) -> None:
        self.context = context
        super().__init__(
            Need(
                job="wish",
                capability="semantic-inventor-retriever",
                reason="The inventor catalog requires semantic shortlisting.",
                instructions=(
                    "Use the paged compact catalog or an index bound to its hash; compare "
                    "only each TASTE name and description with this Wish, respect the "
                    "explicit routable flag as non-semantic eligibility, and return a "
                    "typed Shortlist receipt."
                ),
            )
        )


def retrieve_shortlist(
    context: RoutingContext, retriever: Optional[InventorRetriever]
) -> Shortlist:
    if not isinstance(context, RoutingContext):
        raise ContractError("retrieve_shortlist requires a RoutingContext")
    if retriever is None:
        raise InventorRetrieverRequired(context)
    if not callable(retriever):
        raise ContractError("inventor retriever must be callable")
    context.assert_current()
    shortlist = retriever(context)
    context.assert_current()
    if not isinstance(shortlist, Shortlist):
        raise ContractError("inventor retriever must return a Shortlist")
    if (
        shortlist.wish_sha256 != context.wish_sha256
        or shortlist.catalog_sha256 != context.catalog.catalog_sha256
    ):
        raise ContractError("shortlist belongs to a different Wish or catalog snapshot")
    if shortlist.shortlist_sha256 != _sha256_json(shortlist._identity_dict()):
        raise ContractError("Shortlist identity changed")
    for inventor_id, card_sha256 in zip(
        shortlist.inventor_ids, shortlist.card_sha256s
    ):
        card = context.catalog.card(inventor_id)
        if card.card_sha256 != card_sha256:
            raise ContractError("shortlist contains a stale card for %s" % inventor_id)
        if not card.routable:
            raise ContractError("shortlist includes non-routable inventor %s" % inventor_id)
    return shortlist


@dataclass(frozen=True)
class InventorFinalist:
    """A shortlisted card with its complete exact Taste disclosed."""

    card: InventorCard
    taste: Taste
    implementation_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.card, InventorCard) or not isinstance(self.taste, Taste):
            raise ContractError("InventorFinalist requires an InventorCard and Taste")
        if self.taste.path != self.card.taste_path:
            raise ContractError("InventorFinalist Taste belongs to a different inventor")
        if (
            self.taste.header.sha256 != self.card.taste_header_sha256
            or self.taste.name != self.card.name
            or self.taste.description != self.card.description
        ):
            raise ContractError("InventorFinalist full Taste differs from its catalog header")
        require_sha256(
            self.implementation_sha256, "InventorFinalist implementation_sha256"
        )

    @property
    def inventor_id(self) -> str:
        return self.card.inventor_id

    def to_judge_dict(self) -> Dict[str, Any]:
        payload = self.card.to_routing_dict(include_description=True)
        payload["taste"] = self.taste.to_binding()
        payload["implementation_sha256"] = self.implementation_sha256
        return payload

    def assert_current(self) -> None:
        self.card.assert_entrypoint_current()
        current = load_taste(self.card.root)
        if current.sha256 != self.taste.sha256 or current.content != self.taste.content:
            raise ManifestError("finalist Taste changed after shortlisting: %s" % self.card.root)
        if _implementation_sha256(self.card.root) != self.implementation_sha256:
            raise ManifestError(
                "finalist implementation changed after shortlisting: %s" % self.card.root
            )


@dataclass(frozen=True)
class FinalistContext:
    """Full-Taste comparison disclosed only for shortlisted inventors."""

    routing: RoutingContext
    shortlist: Shortlist
    finalists: Sequence[InventorFinalist]
    schema_version: int = 1
    finalists_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("FinalistContext schema_version must be 1")
        if not isinstance(self.routing, RoutingContext) or not isinstance(
            self.shortlist, Shortlist
        ):
            raise ContractError("FinalistContext requires routing and a Shortlist")
        finalists = tuple(self.finalists)
        if not finalists or not all(isinstance(item, InventorFinalist) for item in finalists):
            raise ContractError("FinalistContext requires typed finalists")
        if tuple(item.inventor_id for item in finalists) != tuple(self.shortlist.inventor_ids):
            raise ContractError("FinalistContext must preserve the exact shortlist")
        object.__setattr__(self, "finalists", finalists)
        object.__setattr__(self, "finalists_sha256", _sha256_json(self._identity_dict()))

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "wish_sha256": self.routing.wish_sha256,
            "catalog_sha256": self.routing.catalog.catalog_sha256,
            "shortlist": self.shortlist.to_dict(),
            "finalists": [
                {
                    "inventor_id": item.inventor_id,
                    "manifest_sha256": item.card.manifest_sha256,
                    "taste_sha256": item.taste.sha256,
                    "implementation_sha256": item.implementation_sha256,
                }
                for item in self.finalists
            ],
        }

    def to_judge_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "wish": self.routing.wish.to_dict(),
            "wish_sha256": self.routing.wish_sha256,
            "catalog": self.routing.catalog.receipt(),
            "shortlist": self.shortlist.to_dict(),
            "finalists_sha256": self.finalists_sha256,
            "finalists": [item.to_judge_dict() for item in self.finalists],
        }

    def assert_current(self) -> None:
        if self.routing.wish_sha256 != _sha256_json(self.routing.wish.to_dict()):
            raise ContractError("Wish changed during inventor routing")
        if self.finalists_sha256 != _sha256_json(self._identity_dict()):
            raise ContractError("FinalistContext identity changed")
        for finalist in self.finalists:
            finalist.assert_current()


def load_finalists(context: RoutingContext, shortlist: Shortlist) -> FinalistContext:
    """Load complete Tastes only after a valid semantic shortlist exists."""

    if not isinstance(context, RoutingContext) or not isinstance(shortlist, Shortlist):
        raise ContractError("load_finalists requires routing and a Shortlist")
    if (
        shortlist.wish_sha256 != context.wish_sha256
        or shortlist.catalog_sha256 != context.catalog.catalog_sha256
    ):
        raise ContractError("shortlist belongs to a different Wish or catalog snapshot")
    context.assert_snapshot_identity()
    finalists = []
    for inventor_id, card_sha256 in zip(
        shortlist.inventor_ids, shortlist.card_sha256s
    ):
        card = context.catalog.card(inventor_id)
        if card.card_sha256 != card_sha256:
            raise ContractError("shortlist contains a stale card for %s" % inventor_id)
        if not card.routable:
            raise ContractError("shortlist includes non-routable inventor %s" % inventor_id)
        card.assert_catalog_current()
        finalists.append(
            InventorFinalist(
                card=card,
                taste=load_taste(card.root),
                implementation_sha256=_implementation_sha256(card.root),
            )
        )
    return FinalistContext(routing=context, shortlist=shortlist, finalists=finalists)


@dataclass(frozen=True)
class TasteFit:
    """One semantic assessment of one finalist's complete exact Taste."""

    inventor_id: str
    taste_sha256: str
    score: int
    accepted: bool
    explanation: str
    tensions: Sequence[str] = field(default_factory=tuple)
    schema_version: int = 1

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("TasteFit schema_version must be 1")
        _text(self.inventor_id, "TasteFit inventor_id", 64)
        require_sha256(self.taste_sha256, "TasteFit taste_sha256")
        if type(self.score) is not int or not 0 <= self.score <= 100:
            raise ContractError("TasteFit score must be an integer from 0 to 100")
        if type(self.accepted) is not bool:
            raise ContractError("TasteFit accepted must be a boolean")
        _text(self.explanation, "TasteFit explanation", 8_000)
        tensions = _texts(self.tensions, "TasteFit tension")
        if not self.accepted and not tensions:
            raise ContractError("a rejected TasteFit must explain at least one tension")
        object.__setattr__(self, "tensions", tensions)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "inventor_id": self.inventor_id,
            "taste_sha256": self.taste_sha256,
            "score": self.score,
            "accepted": self.accepted,
            "explanation": self.explanation,
            "tensions": list(self.tensions),
        }


class TasteJudge(Protocol):
    def __call__(self, context: FinalistContext) -> Sequence[TasteFit]:
        ...


class TasteJudgeRequired(WaitingFor):
    def __init__(self, context: FinalistContext) -> None:
        self.context = context
        super().__init__(
            Need(
                job="wish",
                capability="semantic-taste-judge",
                reason="Final selection requires the complete exact Taste of every finalist.",
                instructions=(
                    "Compare this Wish with every disclosed finalist Taste and return one "
                    "typed TasteFit per finalist; do not infer a winner from keywords. "
                    "Supply the judge identity, version, and configuration digest that "
                    "binds its model and prompt policy."
                ),
            )
        )


class NoInventorFit(WaitingFor):
    def __init__(self, context: FinalistContext, assessments: Sequence[TasteFit]) -> None:
        self.context = context
        self.assessments = tuple(assessments)
        super().__init__(
            Need(
                job="wish",
                capability="inventor-fit",
                reason="Every shortlisted inventor has a hard Taste tension with this Wish.",
                instructions=(
                    "Clarify the Wish, retrieve different finalists, or add an inventor whose "
                    "human-owned Taste fits. Do not weaken a Taste to force a match."
                ),
            )
        )


@dataclass(frozen=True)
class RoutingDecision:
    """Deterministic finalist ranking bound to every routing input."""

    context: FinalistContext
    selected: InventorFinalist
    ranking: Sequence[TasteFit]
    judge_identity: str
    judge_version: str
    judge_config_sha256: str
    schema_version: int = 1
    decision_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("RoutingDecision schema_version must be 1")
        if not isinstance(self.context, FinalistContext) or not isinstance(
            self.selected, InventorFinalist
        ):
            raise ContractError("RoutingDecision requires finalist context and selection")
        _judge_receipt(
            self.judge_identity,
            self.judge_version,
            self.judge_config_sha256,
        )
        ranking = tuple(self.ranking)
        if not ranking or not all(isinstance(item, TasteFit) for item in ranking):
            raise ContractError("RoutingDecision ranking must use TasteFit records")
        finalists = {item.inventor_id: item for item in self.context.finalists}
        ids = tuple(item.inventor_id for item in ranking)
        if len(ids) != len(set(ids)) or set(ids) != set(finalists):
            raise ContractError("RoutingDecision must rank every finalist exactly once")
        for assessment in ranking:
            if assessment.taste_sha256 != finalists[assessment.inventor_id].taste.sha256:
                raise ContractError("RoutingDecision contains a stale Taste assessment")
        expected = tuple(
            sorted(ranking, key=lambda item: (not item.accepted, -item.score, item.inventor_id))
        )
        if ranking != expected:
            raise ContractError("RoutingDecision ranking is not deterministic")
        if ranking[0].inventor_id != self.selected.inventor_id or not ranking[0].accepted:
            raise ContractError("RoutingDecision selection must lead its ranking")
        context_selected = finalists.get(self.selected.inventor_id)
        if context_selected is None or context_selected.taste.sha256 != self.selected.taste.sha256:
            raise ContractError("RoutingDecision selected inventor is outside its context")
        object.__setattr__(self, "ranking", ranking)
        object.__setattr__(self, "decision_sha256", _sha256_json(self._identity_dict()))

    @property
    def fit(self) -> TasteFit:
        return self.ranking[0]

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "wish": self.context.routing.wish.to_dict(),
            "wish_sha256": self.context.routing.wish_sha256,
            "catalog_sha256": self.context.routing.catalog.catalog_sha256,
            "shortlist": self.context.shortlist.to_dict(),
            "finalists_sha256": self.context.finalists_sha256,
            "judge": _judge_receipt(
                self.judge_identity,
                self.judge_version,
                self.judge_config_sha256,
            ),
            "selected": {
                "inventor_id": self.selected.inventor_id,
                "manifest_sha256": self.selected.card.manifest_sha256,
                "taste_sha256": self.selected.taste.sha256,
                "implementation_sha256": self.selected.implementation_sha256,
                "entrypoint": list(self.selected.card.entrypoint),
            },
            "ranking": [item.to_dict() for item in self.ranking],
        }

    def assert_current(self) -> None:
        self.context.assert_current()
        if self.decision_sha256 != _sha256_json(self._identity_dict()):
            raise ContractError("RoutingDecision identity changed")

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["decision_sha256"] = self.decision_sha256
        payload["shortlist_rationale"] = self.context.shortlist.rationale
        payload["explanation"] = self.fit.explanation
        payload["tensions"] = list(self.fit.tensions)
        return payload

    def audit_receipt(self) -> Dict[str, Any]:
        """Return public provenance without Wish or semantic prose."""

        return {
            "schema_version": self.schema_version,
            "decision_sha256": self.decision_sha256,
            "wish_sha256": self.context.routing.wish_sha256,
            "catalog_sha256": self.context.routing.catalog.catalog_sha256,
            "shortlist": {
                "shortlist_sha256": self.context.shortlist.shortlist_sha256,
                "retriever": self.context.shortlist.retriever,
                "retriever_version": self.context.shortlist.retriever_version,
                "cards": [
                    {"inventor_id": inventor_id, "card_sha256": digest}
                    for inventor_id, digest in zip(
                        self.context.shortlist.inventor_ids,
                        self.context.shortlist.card_sha256s,
                    )
                ],
            },
            "finalists_sha256": self.context.finalists_sha256,
            "judge": _judge_receipt(
                self.judge_identity,
                self.judge_version,
                self.judge_config_sha256,
            ),
            "selected": self._identity_dict()["selected"],
            "ranking": [
                {
                    "inventor_id": item.inventor_id,
                    "taste_sha256": item.taste_sha256,
                    "score": item.score,
                    "accepted": item.accepted,
                }
                for item in self.ranking
            ],
        }


def select_inventor(
    context: FinalistContext,
    judge: Optional[TasteJudge],
    *,
    judge_identity: Optional[str] = None,
    judge_version: Optional[str] = None,
    judge_config_sha256: Optional[str] = None,
) -> RoutingDecision:
    if not isinstance(context, FinalistContext):
        raise ContractError("select_inventor requires a FinalistContext")
    if judge is None:
        if any(
            item is not None
            for item in (judge_identity, judge_version, judge_config_sha256)
        ):
            raise ContractError("judge provenance requires a taste judge")
        raise TasteJudgeRequired(context)
    if not callable(judge):
        raise ContractError("taste judge must be callable")
    provenance = _judge_receipt(
        judge_identity,
        judge_version,
        judge_config_sha256,
    )
    context.assert_current()
    raw = judge(context)
    context.assert_current()
    if isinstance(raw, (str, bytes, Mapping)):
        raise ContractError("taste judge must return TasteFit records")
    try:
        assessments = tuple(raw)
    except TypeError as exc:
        raise ContractError("taste judge must return TasteFit records") from exc
    if not assessments or not all(isinstance(item, TasteFit) for item in assessments):
        raise ContractError("taste judge must return TasteFit records")
    by_id = {item.inventor_id: item for item in assessments}
    if len(by_id) != len(assessments):
        raise ContractError("taste judge returned duplicate finalist assessments")
    finalists = {item.inventor_id: item for item in context.finalists}
    if set(by_id) != set(finalists):
        raise ContractError("taste judge must assess every finalist exactly once")
    for inventor_id, finalist in finalists.items():
        if by_id[inventor_id].taste_sha256 != finalist.taste.sha256:
            raise ContractError("taste judge assessed a stale Taste for %s" % inventor_id)
    ranking = tuple(
        sorted(
            assessments,
            key=lambda item: (not item.accepted, -item.score, item.inventor_id),
        )
    )
    accepted = tuple(item for item in ranking if item.accepted)
    if not accepted:
        raise NoInventorFit(context, ranking)
    return RoutingDecision(
        context,
        finalists[accepted[0].inventor_id],
        ranking,
        provenance["identity"],
        provenance["version"],
        provenance["config_sha256"],
    )


@dataclass(frozen=True)
class InventorAssignment:
    """One content-addressed handoff, never a standing schedule."""

    decision: RoutingDecision
    playtest_rounds: int
    entrypoint: Sequence[str]
    assignment_sha256: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("InventorAssignment schema_version must be 1")
        if not isinstance(self.decision, RoutingDecision):
            raise ContractError("InventorAssignment requires a RoutingDecision")
        if type(self.playtest_rounds) is not int or not 1 <= self.playtest_rounds <= 100:
            raise ContractError("playtest_rounds must be a trusted integer from 1 to 100")
        entrypoint = _texts(self.entrypoint, "InventorAssignment entrypoint", allow_empty=False)
        if entrypoint != tuple(self.decision.selected.card.entrypoint):
            raise ContractError("InventorAssignment entrypoint must match the selected inventor")
        require_sha256(self.assignment_sha256, "InventorAssignment assignment_sha256")
        object.__setattr__(self, "entrypoint", entrypoint)
        if self.assignment_sha256 != _sha256_json(self._identity_dict()):
            raise ContractError("InventorAssignment identity is inconsistent")

    @property
    def wish(self) -> Wish:
        return self.decision.context.routing.wish

    @property
    def inventor_id(self) -> str:
        return self.decision.selected.inventor_id

    @property
    def taste_sha256(self) -> str:
        return self.decision.selected.taste.sha256

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": "one-shot",
            "decision": self.decision.to_dict(),
            "entrypoint": list(self.entrypoint),
            "playtest_rounds": self.playtest_rounds,
        }

    def assert_current(self) -> None:
        self.decision.assert_current()
        if self.assignment_sha256 != _sha256_json(self._identity_dict()):
            raise ContractError("InventorAssignment identity changed")

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["assignment_sha256"] = self.assignment_sha256
        return payload

    def audit_receipt(self) -> Dict[str, Any]:
        """Return a public one-shot receipt without private Wish or judge prose."""

        return {
            "schema_version": self.schema_version,
            "kind": "one-shot",
            "assignment_sha256": self.assignment_sha256,
            "decision": self.decision.audit_receipt(),
            "entrypoint": list(self.entrypoint),
            "playtest_rounds": self.playtest_rounds,
        }


def create_assignment(
    decision: RoutingDecision, *, playtest_rounds: int
) -> InventorAssignment:
    if not isinstance(decision, RoutingDecision):
        raise ContractError("create_assignment requires a RoutingDecision")
    if type(playtest_rounds) is not int or not 1 <= playtest_rounds <= 100:
        raise ContractError("playtest_rounds must be a trusted integer from 1 to 100")
    decision.assert_current()
    entrypoint = tuple(decision.selected.card.entrypoint)
    identity = {
        "schema_version": 1,
        "kind": "one-shot",
        "decision": decision.to_dict(),
        "entrypoint": list(entrypoint),
        "playtest_rounds": playtest_rounds,
    }
    return InventorAssignment(
        decision=decision,
        playtest_rounds=playtest_rounds,
        entrypoint=entrypoint,
        assignment_sha256=_sha256_json(identity),
    )


OneShotEntrypoint = Callable[[InventorAssignment], Any]


def dispatch_assignment(
    assignment: InventorAssignment, entrypoint: OneShotEntrypoint
) -> Any:
    if not isinstance(assignment, InventorAssignment):
        raise ContractError("dispatch_assignment requires an InventorAssignment")
    if not callable(entrypoint):
        raise ContractError("assignment entrypoint must be callable")
    assignment.assert_current()
    return entrypoint(assignment)


class WorkshopManager:
    """Request-scoped facade for catalog, shortlist, judgment, and assignment."""

    def __init__(
        self,
        root: Optional[Path] = None,
        retriever: Optional[InventorRetriever] = None,
        judge: Optional[TasteJudge] = None,
        catalog_provider: Optional[Callable[[], InventorCatalog]] = None,
        *,
        judge_identity: Optional[str] = None,
        judge_version: Optional[str] = None,
        judge_config_sha256: Optional[str] = None,
    ) -> None:
        if (root is None) == (catalog_provider is None):
            raise ContractError("WorkshopManager requires exactly one root or catalog_provider")
        if catalog_provider is not None and not callable(catalog_provider):
            raise ContractError("catalog_provider must be callable")
        provenance_values = (judge_identity, judge_version, judge_config_sha256)
        if judge is None:
            if any(item is not None for item in provenance_values):
                raise ContractError("judge provenance requires a taste judge")
        else:
            if not callable(judge):
                raise ContractError("taste judge must be callable")
            _judge_receipt(*provenance_values)
        self.root = Path(root) if root is not None else None
        self.catalog_provider = catalog_provider
        self.retriever = retriever
        self.judge = judge
        self.judge_identity = judge_identity
        self.judge_version = judge_version
        self.judge_config_sha256 = judge_config_sha256

    def prepare(self, wish: Wish) -> RoutingContext:
        if not isinstance(wish, Wish):
            raise ContractError("WorkshopManager requires exactly one typed Wish")
        catalog = (
            discover_inventor_catalog(self.root)
            if self.root is not None
            else self.catalog_provider()
        )
        if not isinstance(catalog, InventorCatalog):
            raise ContractError("catalog_provider must return an InventorCatalog")
        return RoutingContext(
            wish=wish,
            catalog=catalog,
            verify_live_catalog=self.root is not None,
        )

    def shortlist(self, context: RoutingContext) -> Shortlist:
        return retrieve_shortlist(context, self.retriever)

    def finalists(self, context: RoutingContext, shortlist: Shortlist) -> FinalistContext:
        return load_finalists(context, shortlist)

    def route(self, wish: Wish) -> RoutingDecision:
        context = self.prepare(wish)
        shortlist = self.shortlist(context)
        finalists = self.finalists(context, shortlist)
        return select_inventor(
            finalists,
            self.judge,
            judge_identity=self.judge_identity,
            judge_version=self.judge_version,
            judge_config_sha256=self.judge_config_sha256,
        )

    def assign(self, wish: Wish, *, playtest_rounds: int) -> InventorAssignment:
        return create_assignment(self.route(wish), playtest_rounds=playtest_rounds)


__all__ = [
    "CatalogPage",
    "FinalistContext",
    "InventorAssignment",
    "InventorCard",
    "InventorCatalog",
    "InventorFinalist",
    "InventorRetriever",
    "InventorRetrieverRequired",
    "NoInventorFit",
    "RoutingContext",
    "RoutingDecision",
    "Shortlist",
    "TasteFit",
    "TasteJudge",
    "TasteJudgeRequired",
    "WorkshopManager",
    "create_assignment",
    "create_shortlist",
    "discover_inventor_catalog",
    "dispatch_assignment",
    "load_finalists",
    "retrieve_shortlist",
    "select_inventor",
    "shortlist_all",
]
