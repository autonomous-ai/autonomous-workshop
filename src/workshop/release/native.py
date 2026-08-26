"""Credential-free Release proposal for one native-agent product run.

The native agent may assemble the complete local Release package.  It cannot
authenticate to Factory or turn that package into a :class:`ProductRelease`.
This module binds the exact Made and Playtested inputs to exact package bytes
so the trusted host can construct ``ReleaseContext``, execute its effect
adapter, and only then create the receipt-bearing public contract.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Sequence

from workshop._validation import copy_json_mapping, require_sha256
from workshop.artifacts import (
    ArtifactManifest,
    artifact_manifest_from_mapping,
    build_artifact_manifest,
)
from workshop.errors import ArtifactError, ContractError
from workshop.make.contracts import Made
from workshop.make.native import NativeMade
from workshop.playtest.contracts import Playtested
from workshop.playtest.native import NativePlaytested


NATIVE_RELEASE_KIND = "autonomous-workshop.release"
NATIVE_RELEASE_PATH = "artifacts/release/release.json"
NATIVE_RELEASE_PACKAGE_ROOT = "artifacts/release/package"
NATIVE_RELEASE_MANUAL_PATH = "MANUAL.md"
NATIVE_RELEASE_PRODUCT_PATH = "product.json"
MAX_NATIVE_RELEASE_CONTRACT_BYTES = 2 * 1024 * 1024
MAX_NATIVE_RELEASE_MANUAL_BYTES = 2 * 1024 * 1024
RELEASE_PRODUCT_SCHEMA_VERSION = 3
RELEASE_PRODUCT_STATUS = "page-ready"
FACTORY_CONTENT_LABEL_MAX = 40
FACTORY_CONTENT_BODY_MIN = 180
FACTORY_CONTENT_BODY_MAX = 400
FACTORY_CONTENT_STORY_BLOCKS_MAX = 10
_PAGE_SECTION_FIELDS = frozenset(
    ("headline", "body", "visual_direction", "evidence_refs")
)
_RELEASE_PRODUCT_FIELDS = frozenset(
    (
        "schema_version",
        "kind",
        "status",
        "title",
        "summary",
        "hero",
        "cinematic",
        "use_case",
        "story_blocks",
        "what_arrives",
        "limitations",
        "product_artifact_sha256",
        "playtest_evidence_artifact_sha256",
        "claims",
    )
)
_FORBIDDEN_MEDIA_SUFFIXES = frozenset(
    (
        ".3g2",
        ".3gp",
        ".aac",
        ".avi",
        ".avif",
        ".bmp",
        ".flac",
        ".gif",
        ".heic",
        ".jpeg",
        ".jpg",
        ".m4a",
        ".m4v",
        ".mkv",
        ".mov",
        ".mp4",
        ".mp3",
        ".mpeg",
        ".mpg",
        ".oga",
        ".ogg",
        ".opus",
        ".png",
        ".svg",
        ".tif",
        ".tiff",
        ".wav",
        ".webm",
        ".webp",
    )
)
_FORBIDDEN_EFFECT_FIELDS = frozenset(
    (
        "credentials",
        "factory_receipt",
        "listing_active",
        "page_ready",
        "publication_receipt",
        "published_history_id",
        "site_receipt",
    )
)


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
        raise ContractError("native Release values must be finite JSON") from exc


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _thaw(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant %s" % value)


def _strict_canonical_json(content: bytes, label: str) -> dict[str, Any]:
    try:
        document = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, ValueError, RecursionError, json.JSONDecodeError) as exc:
        raise ContractError("%s must contain strict UTF-8 JSON" % label) from exc
    if not isinstance(document, dict):
        raise ContractError("%s must contain one JSON object" % label)
    if content != _canonical_json(document):
        raise ContractError("%s must use canonical JSON encoding" % label)
    return document


def _safe_relative(value: Any, label: str) -> PurePosixPath:
    candidate = PurePosixPath(value) if isinstance(value, str) else PurePosixPath(".")
    if (
        not isinstance(value, str)
        or not value
        or value in (".", "..")
        or "\\" in value
        or candidate.is_absolute()
        or ".." in candidate.parts
        or candidate.as_posix() != value
    ):
        raise ContractError("%s must be a safe relative POSIX path" % label)
    return candidate


def _canonical_run_root(value: Path) -> Path:
    try:
        requested = Path(value)
    except TypeError as exc:
        raise ContractError("native Release run root must be path-like") from exc
    if not requested.is_absolute() or requested.is_symlink():
        raise ContractError("native Release run root must be an absolute real directory")
    try:
        identity = requested.lstat()
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise ArtifactError("native Release run root is unavailable") from exc
    if (
        requested != resolved
        or not stat.S_ISDIR(identity.st_mode)
        or not requested.is_dir()
    ):
        raise ContractError("native Release run root must be canonical")
    return requested


def _real_directory(root: Path, relative: str, label: str) -> Path:
    safe = _safe_relative(relative, label)
    current = root
    for part in safe.parts:
        current = current / part
        try:
            identity = current.lstat()
        except OSError as exc:
            raise ArtifactError("%s is unavailable" % label) from exc
        if stat.S_ISLNK(identity.st_mode) or not stat.S_ISDIR(identity.st_mode):
            raise ArtifactError("%s must not contain links or non-directories" % label)
    try:
        current.resolve(strict=True).relative_to(root)
    except (OSError, ValueError) as exc:
        raise ArtifactError("%s escapes the native run root" % label) from exc
    return current


def _read_regular(path: Path, label: str, maximum_bytes: int) -> bytes:
    try:
        expected = path.lstat()
    except OSError as exc:
        raise ArtifactError("%s is unavailable" % label) from exc
    if stat.S_ISLNK(expected.st_mode) or not stat.S_ISREG(expected.st_mode):
        raise ArtifactError("%s must be a regular file" % label)
    if not 1 <= expected.st_size <= maximum_bytes:
        raise ArtifactError(
            "%s must be non-empty and at most %d bytes" % (label, maximum_bytes)
        )
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ArtifactError("%s cannot be opened without following links" % label) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ArtifactError("%s changed while opening" % label)
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        if len(content) > maximum_bytes:
            raise ArtifactError("%s exceeds its byte limit" % label)
        if (
            len(content) != opened.st_size
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ArtifactError("%s changed while reading" % label)
        return content
    finally:
        os.close(descriptor)


def _expected_claims(playtested: Playtested) -> dict[str, Any]:
    claims: dict[str, Any] = {}
    for result in playtested.evidence.results:
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
        raise ContractError("native Release requires non-empty Playtest claims")
    return claims


def _page_text(value: Any, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\t" for character in value)
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded substantive text" % label)
    return value


def _page_text_list(
    value: Any,
    label: str,
    *,
    maximum_items: int,
    maximum_item_length: int,
) -> list[str]:
    if (
        not isinstance(value, list)
        or not 1 <= len(value) <= maximum_items
    ):
        raise ContractError("%s must be a non-empty bounded list" % label)
    result = [
        _page_text(item, "%s item" % label, maximum_item_length)
        for item in value
    ]
    if len({item.casefold() for item in result}) != len(result):
        raise ContractError("%s must not contain duplicate items" % label)
    return result


def _page_section(
    value: Any,
    label: str,
    *,
    valid_evidence_refs: frozenset[str],
) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != _PAGE_SECTION_FIELDS:
        raise ContractError("%s fields are invalid" % label)
    refs = value.get("evidence_refs")
    if (
        not isinstance(refs, list)
        or not 1 <= len(refs) <= 32
        or any(not isinstance(ref, str) or ref not in valid_evidence_refs for ref in refs)
        or len(refs) != len(set(refs))
    ):
        raise ContractError("%s evidence_refs are not bound to Made or Playtest" % label)
    return {
        "headline": _page_text(value.get("headline"), "%s headline" % label, 300),
        "body": _page_text(value.get("body"), "%s body" % label, 4_000),
        "visual_direction": _page_text(
            value.get("visual_direction"),
            "%s visual_direction" % label,
            2_000,
        ),
        "evidence_refs": list(refs),
    }


def _factory_content_text(value: str, label: str, minimum: int, maximum: int) -> None:
    if (
        not minimum <= len(value) <= maximum
        or "<" in value
        or ">" in value
    ):
        raise ContractError(
            "%s must fit Factory's exact plain-text display limit of %d-%d "
            "characters" % (label, minimum, maximum)
        )


def _validate_factory_content(product: Mapping[str, Any]) -> None:
    story_blocks = product["story_blocks"]
    if len(story_blocks) > FACTORY_CONTENT_STORY_BLOCKS_MAX:
        raise ContractError(
            "native Release story_blocks must fit Factory's exact limit of at most %d"
            % FACTORY_CONTENT_STORY_BLOCKS_MAX
        )
    sections = [("use_case", product["use_case"])] + [
        ("story_blocks[%d]" % index, block)
        for index, block in enumerate(story_blocks)
    ]
    for label, section in sections:
        _factory_content_text(
            section["headline"],
            "native Release %s headline" % label,
            1,
            FACTORY_CONTENT_LABEL_MAX,
        )
        _factory_content_text(
            section["body"],
            "native Release %s body" % label,
            FACTORY_CONTENT_BODY_MIN,
            FACTORY_CONTENT_BODY_MAX,
        )


def validate_release_product(value: Any) -> dict[str, Any]:
    """Validate the exact Codex-authored customer-page contract.

    The host can prove byte identity and evidence references, not the semantic
    quality of prose.  Every page section therefore names the immutable Made
    product or one of the sealed Playtest checks it relies on.  Factory is not
    a copywriter or media prompt target at this boundary.
    """

    product = copy_json_mapping(value, "native Release product.json", nonempty=True)
    if set(product) != _RELEASE_PRODUCT_FIELDS:
        raise ContractError("native Release product.json fields are invalid")
    if (
        product.get("schema_version") != RELEASE_PRODUCT_SCHEMA_VERSION
        or product.get("kind") != "workshop.release-package"
        or product.get("status") != RELEASE_PRODUCT_STATUS
    ):
        raise ContractError("native Release product.json is not a page-ready package")
    require_sha256(
        product.get("product_artifact_sha256"),
        "native Release product artifact sha256",
    )
    require_sha256(
        product.get("playtest_evidence_artifact_sha256"),
        "native Release Playtest evidence sha256",
    )
    claims = copy_json_mapping(
        product.get("claims"), "native Release claims", nonempty=True
    )
    valid_refs = frozenset(
        {"made:product.json"}
        | {"playtest:%s" % check_id for check_id in claims}
    )
    story_blocks = product.get("story_blocks")
    if not isinstance(story_blocks, list) or not story_blocks:
        raise ContractError("native Release story_blocks must be a non-empty bounded list")
    if len(story_blocks) > FACTORY_CONTENT_STORY_BLOCKS_MAX:
        raise ContractError(
            "native Release story_blocks must fit Factory's exact limit of at most %d"
            % FACTORY_CONTENT_STORY_BLOCKS_MAX
        )
    validated = {
        "schema_version": RELEASE_PRODUCT_SCHEMA_VERSION,
        "kind": "workshop.release-package",
        "status": RELEASE_PRODUCT_STATUS,
        "title": _page_text(product.get("title"), "native Release title", 300),
        "summary": _page_text(product.get("summary"), "native Release summary", 2_000),
        "hero": _page_section(
            product.get("hero"),
            "native Release hero",
            valid_evidence_refs=valid_refs,
        ),
        "cinematic": _page_section(
            product.get("cinematic"),
            "native Release cinematic",
            valid_evidence_refs=valid_refs,
        ),
        "use_case": _page_section(
            product.get("use_case"),
            "native Release use_case",
            valid_evidence_refs=valid_refs,
        ),
        "story_blocks": [
            _page_section(
                block,
                "native Release story_blocks[%d]" % index,
                valid_evidence_refs=valid_refs,
            )
            for index, block in enumerate(story_blocks)
        ],
        "what_arrives": _page_text_list(
            product.get("what_arrives"),
            "native Release what_arrives",
            maximum_items=100,
            maximum_item_length=1_000,
        ),
        "limitations": _page_text_list(
            product.get("limitations"),
            "native Release limitations",
            maximum_items=100,
            maximum_item_length=2_000,
        ),
        "product_artifact_sha256": product["product_artifact_sha256"],
        "playtest_evidence_artifact_sha256": product[
            "playtest_evidence_artifact_sha256"
        ],
        "claims": claims,
    }
    _validate_factory_content(validated)
    return validated


@dataclass(frozen=True)
class NativeReleasePackage:
    """Validated, effect-free inputs for the host's Release adapter."""

    root: Path
    manifest: ArtifactManifest
    manual_path: str
    product: Mapping[str, Any]
    claims: Mapping[str, Any]
    made: Made
    playtested: Playtested

    def __post_init__(self) -> None:
        object.__setattr__(self, "product", _freeze(_thaw(self.product)))
        object.__setattr__(self, "claims", _freeze(_thaw(self.claims)))


@dataclass(frozen=True)
class NativeRelease:
    """One sealed Release package proposed before any authenticated effect."""

    round: int
    made_sha256: str
    playtested_sha256: str
    product_artifact_sha256: str
    playtest_evidence_artifact_sha256: str
    package_root: str
    package_manifest: ArtifactManifest
    manual_path: str
    product_json_path: str
    product_json_sha256: str
    product: Mapping[str, Any]
    schema_version: int = 1
    kind: str = NATIVE_RELEASE_KIND
    release_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("native Release schema_version must be 1")
        if self.kind != NATIVE_RELEASE_KIND:
            raise ContractError("native Release kind is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("native Release round must be from 1 through 100")
        for value, label in (
            (self.made_sha256, "native Release Made sha256"),
            (self.playtested_sha256, "native Release Playtested sha256"),
            (self.product_artifact_sha256, "native Release product sha256"),
            (
                self.playtest_evidence_artifact_sha256,
                "native Release Playtest evidence sha256",
            ),
            (self.product_json_sha256, "native Release product.json sha256"),
        ):
            require_sha256(value, label)
        if self.package_root != NATIVE_RELEASE_PACKAGE_ROOT:
            raise ContractError("native Release package_root is not canonical")
        _safe_relative(self.package_root, "native Release package_root")
        if self.manual_path != NATIVE_RELEASE_MANUAL_PATH:
            raise ContractError("native Release manual_path must be MANUAL.md")
        if self.product_json_path != NATIVE_RELEASE_PRODUCT_PATH:
            raise ContractError("native Release product_json_path must be product.json")
        if not isinstance(self.package_manifest, ArtifactManifest):
            raise ContractError("native Release requires an ArtifactManifest")
        self.package_manifest.assert_valid()
        if self.package_manifest.created_at != "content-addressed":
            raise ContractError("native Release manifest must be content-addressed")
        inventory = {entry.path: entry for entry in self.package_manifest.entries}
        for required in (self.manual_path, self.product_json_path):
            if required not in inventory:
                raise ContractError("native Release manifest lacks %s" % required)
        forbidden_media = sorted(
            path
            for path in inventory
            if PurePosixPath(path).suffix.casefold() in _FORBIDDEN_MEDIA_SUFFIXES
        )
        if forbidden_media:
            raise ContractError(
                "native Release package cannot contain media files: %s"
                % forbidden_media
            )
        if inventory[self.product_json_path].sha256 != self.product_json_sha256:
            raise ContractError("native Release product.json is not bound to its manifest")

        product = validate_release_product(self.product)
        if hashlib.sha256(_canonical_json(product)).hexdigest() != self.product_json_sha256:
            raise ContractError("native Release product.json hash is not canonical")
        if product.get("product_artifact_sha256") != self.product_artifact_sha256:
            raise ContractError("native Release product.json identifies another product")
        if (
            product.get("playtest_evidence_artifact_sha256")
            != self.playtest_evidence_artifact_sha256
        ):
            raise ContractError("native Release product.json identifies other Playtest evidence")
        forbidden_fields = _FORBIDDEN_EFFECT_FIELDS & set(product)
        if forbidden_fields:
            raise ContractError(
                "native Release product.json contains effect proof: %s"
                % sorted(forbidden_fields)
            )
        object.__setattr__(self, "product", _freeze(product))
        object.__setattr__(
            self,
            "release_sha256",
            hashlib.sha256(_canonical_json(self._identity_dict())).hexdigest(),
        )

    @property
    def claims(self) -> Mapping[str, Any]:
        return self.product["claims"]

    @property
    def contract_sha256(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict())).hexdigest()

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "round": self.round,
            "made_sha256": self.made_sha256,
            "playtested_sha256": self.playtested_sha256,
            "product_artifact_sha256": self.product_artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                self.playtest_evidence_artifact_sha256
            ),
            "package_root": self.package_root,
            "package_manifest": self.package_manifest.to_dict(),
            "manual_path": self.manual_path,
            "product_json_path": self.product_json_path,
            "product_json_sha256": self.product_json_sha256,
            "product": _thaw(self.product),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["release_sha256"] = self.release_sha256
        return payload

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeRelease":
        expected = {
            "schema_version",
            "kind",
            "round",
            "made_sha256",
            "playtested_sha256",
            "product_artifact_sha256",
            "playtest_evidence_artifact_sha256",
            "package_root",
            "package_manifest",
            "manual_path",
            "product_json_path",
            "product_json_sha256",
            "product",
            "release_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("native Release fields are invalid")
        release = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            round=value["round"],
            made_sha256=value["made_sha256"],
            playtested_sha256=value["playtested_sha256"],
            product_artifact_sha256=value["product_artifact_sha256"],
            playtest_evidence_artifact_sha256=(
                value["playtest_evidence_artifact_sha256"]
            ),
            package_root=value["package_root"],
            package_manifest=artifact_manifest_from_mapping(value["package_manifest"]),
            manual_path=value["manual_path"],
            product_json_path=value["product_json_path"],
            product_json_sha256=value["product_json_sha256"],
            product=value["product"],
        )
        if dict(value) != release.to_dict():
            raise ContractError("native Release hashes or canonical identity are invalid")
        return release

    def assert_context(self, made: NativeMade, playtested: NativePlaytested) -> None:
        if not isinstance(made, NativeMade) or not isinstance(
            playtested, NativePlaytested
        ):
            raise ContractError("native Release context requires NativeMade and NativePlaytested")
        if (
            playtested.verdict != "pass"
            or self.round != made.round
            or self.round != playtested.round
            or self.made_sha256 != made.made_sha256
            or self.playtested_sha256 != playtested.playtested_sha256
            or self.product_artifact_sha256
            != made.product_manifest.artifact_sha256
            or self.product_artifact_sha256
            != playtested.product_artifact_sha256
            or self.playtest_evidence_artifact_sha256
            != playtested.evidence_manifest.artifact_sha256
        ):
            raise ContractError("native Release belongs to different Workshop inputs")

    def validate_package_tree(
        self,
        run_root: Path,
        made: NativeMade,
        playtested: NativePlaytested,
    ) -> NativeReleasePackage:
        """Rehash Release and upstream trees without performing any effect."""

        self.assert_context(made, playtested)
        root = _canonical_run_root(run_root)
        package_root = _real_directory(
            root, self.package_root, "native Release package tree"
        )
        current = build_artifact_manifest(
            package_root, created_at=self.package_manifest.created_at
        )
        if current.to_dict() != self.package_manifest.to_dict():
            raise ArtifactError("native Release package differs from its manifest")

        manual = _read_regular(
            package_root / self.manual_path,
            "native Release MANUAL.md",
            MAX_NATIVE_RELEASE_MANUAL_BYTES,
        )
        try:
            manual_text = manual.decode("utf-8")
        except UnicodeError as exc:
            raise ContractError("native Release MANUAL.md must be UTF-8") from exc
        if not manual_text.strip():
            raise ContractError("native Release MANUAL.md must be substantive")

        observed_product: dict[str, Any] | None = None
        for entry in self.package_manifest.entries:
            if PurePosixPath(entry.path).suffix.casefold() != ".json":
                continue
            content = _read_regular(
                package_root.joinpath(*PurePosixPath(entry.path).parts),
                "native Release %s" % entry.path,
                MAX_NATIVE_RELEASE_CONTRACT_BYTES,
            )
            document = _strict_canonical_json(
                content, "native Release %s" % entry.path
            )
            if entry.path == self.product_json_path:
                observed_product = document
        if observed_product is None:
            raise ContractError("native Release product.json is unavailable")
        observed_product_sha256 = hashlib.sha256(
            _canonical_json(observed_product)
        ).hexdigest()
        if observed_product_sha256 != self.product_json_sha256:
            raise ArtifactError("native Release product.json hash differs from its bytes")
        if observed_product != _thaw(self.product):
            raise ContractError("native Release proposal differs from product.json")

        canonical_made = made.validate_product_tree(root)
        canonical_playtested = playtested.validate_evidence_tree(root, made)
        if not canonical_playtested.passed:
            raise ContractError("native Release requires passing exact Playtest evidence")
        expected_claims = _expected_claims(canonical_playtested)
        if observed_product["claims"] != expected_claims:
            raise ContractError("native Release claims differ from exact Playtest evidence")
        if observed_product.get("title") != canonical_made.product.get("title"):
            raise ContractError("native Release title differs from the exact Made product")
        unchanged = build_artifact_manifest(
            package_root, created_at=self.package_manifest.created_at
        )
        if unchanged.to_dict() != self.package_manifest.to_dict():
            raise ArtifactError("native Release package changed during validation")
        return NativeReleasePackage(
            root=package_root,
            manifest=self.package_manifest,
            manual_path=self.manual_path,
            product=observed_product,
            claims=expected_claims,
            made=canonical_made,
            playtested=canonical_playtested,
        )


def read_native_release(run_root: Path) -> NativeRelease:
    """Read the one canonical ``artifacts/release/release.json`` proposal."""

    root = _canonical_run_root(run_root)
    parent = _real_directory(
        root,
        PurePosixPath(NATIVE_RELEASE_PATH).parent.as_posix(),
        "native Release contract parent",
    )
    content = _read_regular(
        parent / PurePosixPath(NATIVE_RELEASE_PATH).name,
        "native Release contract",
        MAX_NATIVE_RELEASE_CONTRACT_BYTES,
    )
    return NativeRelease.from_mapping(
        _strict_canonical_json(content, "native Release contract")
    )


__all__ = [
    "FACTORY_CONTENT_BODY_MAX",
    "FACTORY_CONTENT_BODY_MIN",
    "FACTORY_CONTENT_LABEL_MAX",
    "FACTORY_CONTENT_STORY_BLOCKS_MAX",
    "MAX_NATIVE_RELEASE_CONTRACT_BYTES",
    "MAX_NATIVE_RELEASE_MANUAL_BYTES",
    "NATIVE_RELEASE_KIND",
    "NATIVE_RELEASE_MANUAL_PATH",
    "NATIVE_RELEASE_PACKAGE_ROOT",
    "NATIVE_RELEASE_PATH",
    "NATIVE_RELEASE_PRODUCT_PATH",
    "RELEASE_PRODUCT_SCHEMA_VERSION",
    "RELEASE_PRODUCT_STATUS",
    "NativeRelease",
    "NativeReleasePackage",
    "read_native_release",
    "validate_release_product",
]
