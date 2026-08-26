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

_FACTORY_ENRICHMENT_PENDING = {
    "copy_owner": "factory",
    "media_owner": "factory",
    "status": "pending",
}
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


@dataclass(frozen=True)
class NativeReleasePackage:
    """Validated, effect-free inputs for the host's Release adapter."""

    root: Path
    manifest: ArtifactManifest
    manual_path: str
    product: Mapping[str, Any]
    claims: Mapping[str, Any]
    factory_enrichment: Mapping[str, Any]
    made: Made
    playtested: Playtested

    def __post_init__(self) -> None:
        object.__setattr__(self, "product", _freeze(_thaw(self.product)))
        object.__setattr__(self, "claims", _freeze(_thaw(self.claims)))
        object.__setattr__(
            self,
            "factory_enrichment",
            _freeze(_thaw(self.factory_enrichment)),
        )


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

        product = copy_json_mapping(
            self.product, "native Release product.json", nonempty=True
        )
        if hashlib.sha256(_canonical_json(product)).hexdigest() != self.product_json_sha256:
            raise ContractError("native Release product.json hash is not canonical")
        if (
            product.get("schema_version") != 2
            or product.get("kind") != "workshop.release-package"
            or product.get("status") != "facts-ready"
        ):
            raise ContractError("native Release product.json is not a factual package")
        for key in ("title", "summary", "lane"):
            value = product.get(key)
            if (
                not isinstance(value, str)
                or not value.strip()
                or len(value) > 2_000
            ):
                raise ContractError(
                    "native Release product.json %s must be factual text" % key
                )
        if product.get("product_artifact_sha256") != self.product_artifact_sha256:
            raise ContractError("native Release product.json identifies another product")
        if (
            product.get("playtest_evidence_artifact_sha256")
            != self.playtest_evidence_artifact_sha256
        ):
            raise ContractError("native Release product.json identifies other Playtest evidence")
        claims = copy_json_mapping(
            product.get("claims"), "native Release claims", nonempty=True
        )
        if product.get("factory_enrichment") != _FACTORY_ENRICHMENT_PENDING:
            raise ContractError("native Release must leave Factory enrichment pending")
        forbidden_fields = (
            {"images", "story_blocks", "use_case"}
            | _FORBIDDEN_EFFECT_FIELDS
        ) & set(product)
        if forbidden_fields:
            raise ContractError(
                "native Release product.json contains media or effect proof: %s"
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
    def factory_enrichment(self) -> Mapping[str, Any]:
        return self.product["factory_enrichment"]

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
        if observed_product.get("lane") != canonical_made.product.get("lane"):
            raise ContractError("native Release lane differs from the exact Made product")

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
            factory_enrichment=_FACTORY_ENRICHMENT_PENDING,
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
    "MAX_NATIVE_RELEASE_CONTRACT_BYTES",
    "MAX_NATIVE_RELEASE_MANUAL_BYTES",
    "NATIVE_RELEASE_KIND",
    "NATIVE_RELEASE_MANUAL_PATH",
    "NATIVE_RELEASE_PACKAGE_ROOT",
    "NATIVE_RELEASE_PATH",
    "NATIVE_RELEASE_PRODUCT_PATH",
    "NativeRelease",
    "NativeReleasePackage",
    "read_native_release",
]
