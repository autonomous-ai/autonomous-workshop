"""Inputs and sealed outputs owned by the Release stage."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop._validation import (
    bounded_text as _text,
    copy_json_mapping as _mapping,
    require_sha256,
)
from workshop.artifacts.core import ArtifactManifest, build_artifact_manifest
from workshop.contributors import Taste
from workshop.errors import ArtifactError, ContractError
from workshop.make.contracts import Made
from workshop.playtest.contracts import Playtested
from workshop.product import ToyBlueprint
from workshop.release.native import (
    MAX_NATIVE_RELEASE_MANUAL_BYTES,
    validate_release_pdf_manual,
    validate_release_product,
)
from workshop.wish import Wish


_FORBIDDEN_RELEASE_MEDIA_SUFFIXES = frozenset(
    (
        ".avi", ".avif", ".bmp", ".gif", ".heic", ".jpeg", ".jpg",
        ".m4v", ".mkv", ".mov", ".mp4", ".png", ".svg", ".tif",
        ".tiff", ".webm", ".webp",
    )
)


def _fresh_manifest(root: Path, manifest: ArtifactManifest) -> ArtifactManifest:
    current = build_artifact_manifest(root, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ArtifactError("artifact bytes changed after the job completed")
    return current


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
        raise ContractError("ProductRelease product.json must be finite JSON") from exc


@dataclass(frozen=True)
class ReleaseContext:
    wish: Wish
    taste: Taste
    blueprint: ToyBlueprint
    made: Made
    playtested: Playtested
    workspace: Path
    lease_token: Optional[str] = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish) or not isinstance(self.taste, Taste):
            raise ContractError("ReleaseContext requires a Wish and Taste")
        if not isinstance(self.blueprint, ToyBlueprint):
            raise ContractError("ReleaseContext requires a ToyBlueprint")
        if not isinstance(self.made, Made) or not isinstance(self.playtested, Playtested):
            raise ContractError(
                "ReleaseContext requires Made and Playtested results"
            )
        if not self.playtested.passed:
            raise ContractError("Release cannot begin before Playtest passes")
        root = Path(self.workspace)
        if not root.is_absolute():
            raise ContractError("ReleaseContext workspace must be absolute")
        if self.lease_token is not None and (
            not isinstance(self.lease_token, str)
            or not self.lease_token
            or len(self.lease_token) > 512
            or any(ord(character) < 33 or ord(character) == 127 for character in self.lease_token)
        ):
            raise ContractError("ReleaseContext lease token is malformed")
        object.__setattr__(self, "workspace", root)
        self.assert_current()

    def assert_current(self) -> None:
        """Recheck that Release still describes the exact Playtested Make."""

        self.made.assert_current()
        self.playtested.assert_artifact(self.made.artifact_sha256)


@dataclass(frozen=True)
class ProductRelease:
    """One locally verified and sealed customer Release package.

    This contract deliberately stops at exact local bytes.  A Factory draft or
    public page is optional host-owned enrichment with its own durable receipt;
    it is not part of Release acceptance.
    """

    root: Path
    manifest: ArtifactManifest
    product_artifact_sha256: str
    manual_path: str
    claims: Mapping[str, Any]

    def __post_init__(self) -> None:
        root = Path(self.root)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise ContractError(
                "ProductRelease root must be an absolute regular directory"
            )
        if not isinstance(self.manifest, ArtifactManifest):
            raise ContractError("ProductRelease requires an ArtifactManifest")
        require_sha256(
            self.product_artifact_sha256,
            "ProductRelease product artifact sha256",
        )
        _text(
            self.manual_path,
            "ProductRelease manual_path",
            1_000,
        )
        manual = Path(self.manual_path)
        if (
            manual.is_absolute()
            or ".." in manual.parts
            or manual.as_posix() not in ("MANUAL.md", "MANUAL.pdf")
            or not (root / manual).is_file()
        ):
            raise ContractError(
                "ProductRelease manual_path must be MANUAL.md or MANUAL.pdf"
            )
        page_path = root / "product.json"
        if not page_path.is_file():
            raise ContractError("ProductRelease requires an in-root product.json")
        claims = _mapping(self.claims, "ProductRelease claims", nonempty=True)
        _fresh_manifest(root, self.manifest)
        try:
            page_content = page_path.read_bytes()
            page_value = json.loads(page_content.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(
                "ProductRelease product.json must be valid UTF-8 JSON"
            ) from exc
        if page_content != _canonical_json(page_value):
            raise ContractError(
                "ProductRelease product.json must use canonical JSON encoding"
            )
        release_schema_version = 1 if manual.as_posix() == "MANUAL.md" else 2
        page = validate_release_product(
            page_value,
            release_schema_version=release_schema_version,
        )
        if manual.as_posix() == "MANUAL.pdf":
            try:
                manual_content = (root / manual).read_bytes()
            except OSError as exc:
                raise ContractError("ProductRelease MANUAL.pdf is unreadable") from exc
            if not 1 <= len(manual_content) <= MAX_NATIVE_RELEASE_MANUAL_BYTES:
                raise ContractError(
                    "ProductRelease MANUAL.pdf must be non-empty and bounded"
                )
            validate_release_pdf_manual(manual_content)
        if page.get("product_artifact_sha256") != self.product_artifact_sha256:
            raise ContractError(
                "ProductRelease product.json describes different product bytes"
            )
        page_claims = _mapping(
            page.get("claims"),
            "ProductRelease product.json claims",
            nonempty=True,
        )
        if page_claims != claims:
            raise ContractError(
                "ProductRelease claims differ from the sealed product facts"
            )
        forbidden_media = [
            entry.path
            for entry in self.manifest.entries
            if Path(entry.path).suffix.casefold()
            in _FORBIDDEN_RELEASE_MEDIA_SUFFIXES
        ]
        if forbidden_media:
            raise ContractError(
                "ProductRelease cannot seal local page media: %s"
                % forbidden_media
            )
        _fresh_manifest(root, self.manifest)
        object.__setattr__(self, "root", root.resolve(strict=True))
        object.__setattr__(self, "claims", claims)

    @classmethod
    def from_root(
        cls,
        root: Path,
        product_artifact_sha256: str,
        manual_path: str,
        claims: Mapping[str, Any],
    ) -> "ProductRelease":
        resolved = Path(root).resolve(strict=True)
        return cls(
            resolved,
            build_artifact_manifest(resolved, created_at="content-addressed"),
            product_artifact_sha256,
            manual_path,
            claims,
        )

    @property
    def release_sha256(self) -> str:
        return self.manifest.artifact_sha256

    def assert_current(self) -> None:
        """Refuse to use output bytes changed after Release completed."""

        _fresh_manifest(self.root, self.manifest)


__all__ = ["ReleaseContext", "ProductRelease"]
