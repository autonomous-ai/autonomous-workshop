"""Inputs and sealed outputs owned by the Release stage."""

from __future__ import annotations

import json
import urllib.parse
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
from workshop.runtime import Receipt
from workshop.make.contracts import Made
from workshop.playtest.contracts import Playtested
from workshop.product import ToyBlueprint
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
        if self.made.product["lane"] != self.blueprint.lane:
            raise ContractError(
                "ReleaseContext product belongs to a different lane"
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
    """One sealed box insert, factual brief, and authenticated model draft.

    Factory owns customer-facing copy and media. The site receipt binds the
    complete Release tree (facts and paper) to an authenticated private
    draft for the exact product artifact. A verified public receipt remains
    accepted for older/custom writers, but public visibility is not part of the
    shared Release job.
    """

    root: Path
    manifest: ArtifactManifest
    product_artifact_sha256: str
    manual_path: str
    claims: Mapping[str, Any]
    site_receipt: Receipt

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
            or manual.as_posix() != "MANUAL.md"
            or not (root / manual).is_file()
        ):
            raise ContractError(
                "ProductRelease manual_path must be MANUAL.md"
            )
        page_path = root / "product.json"
        if not page_path.is_file():
            raise ContractError("ProductRelease requires an in-root product.json")
        claims = _mapping(self.claims, "ProductRelease claims", nonempty=True)
        _fresh_manifest(root, self.manifest)
        try:
            page_value = json.loads(page_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(
                "ProductRelease product.json must be valid UTF-8 JSON"
            ) from exc
        page = _mapping(
            page_value,
            "ProductRelease product.json",
            nonempty=True,
        )
        if (
            page.get("schema_version") != 2
            or page.get("kind") != "workshop.release-package"
            or page.get("status") != "facts-ready"
        ):
            raise ContractError(
                "ProductRelease product.json must be a sealed factual handoff"
            )
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
        forbidden_page_fields = {"images", "use_case", "story_blocks"} & set(page)
        if forbidden_page_fields:
            raise ContractError(
                "ProductRelease cannot contain creator-owned page copy or media: %s"
                % sorted(forbidden_page_fields)
            )
        enrichment = page.get("factory_enrichment")
        if enrichment != {
            "copy_owner": "factory",
            "media_owner": "factory",
            "status": "pending",
        }:
            raise ContractError(
                "ProductRelease must leave Factory copy and media enrichment pending"
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
        self._assert_site_receipt()
        object.__setattr__(self, "root", root.resolve(strict=True))
        object.__setattr__(self, "claims", claims)

    def _assert_site_receipt(self) -> None:
        """Require remote draft/public readback bound to Make and Release."""

        if not isinstance(self.site_receipt, Receipt):
            raise ContractError("ProductRelease requires a site Receipt")
        self.site_receipt.assert_artifact(self.product_artifact_sha256)
        if not (
            self.site_receipt.is_verified_draft
            or self.site_receipt.is_verified_public
        ):
            raise ContractError(
                "ProductRelease requires an authenticated private draft "
                "or verified public site Receipt"
            )
        page_url = self._site_page_url()
        try:
            parsed_page_url = urllib.parse.urlsplit(page_url or "")
        except ValueError as exc:
            raise ContractError(
                "ProductRelease site Receipt requires a valid canonical page URL"
            ) from exc
        if (
            parsed_page_url.scheme != "https"
            or not parsed_page_url.hostname
            or parsed_page_url.username is not None
            or parsed_page_url.password is not None
        ):
            raise ContractError(
                "ProductRelease site Receipt requires an HTTPS canonical page URL"
            )
        if (
            self.site_receipt.details.get("release_sha256")
            != self.manifest.artifact_sha256
        ):
            raise ContractError(
                "ProductRelease site Receipt describes different facts or paper bytes"
            )

    def _site_page_url(self) -> str:
        """Resolve the customer page without mistaking a project CDN for it."""

        page_url = self.site_receipt.details.get("page_url")
        if isinstance(page_url, str) and page_url:
            return page_url
        # Compatibility for older custom site writers that stored the customer
        # URL directly in ``project_url``.  Real Shop receipts use project_url
        # for the immutable downloadable project and therefore must carry the
        # distinct page_url detail.
        legacy = self.site_receipt.project_url
        try:
            parsed = urllib.parse.urlsplit(legacy or "")
        except ValueError:
            parsed = urllib.parse.SplitResult("", "", "", "", "")
        if (
            isinstance(legacy, str)
            and parsed.hostname == "www.autonomous.ai"
            and parsed.path.startswith("/factory/product/")
        ):
            return legacy
        raise ContractError(
            "ProductRelease site Receipt requires a customer product page URL"
        )

    @classmethod
    def from_root(
        cls,
        root: Path,
        product_artifact_sha256: str,
        manual_path: str,
        claims: Mapping[str, Any],
        site_receipt: Receipt,
    ) -> "ProductRelease":
        resolved = Path(root).resolve(strict=True)
        return cls(
            resolved,
            build_artifact_manifest(resolved, created_at="content-addressed"),
            product_artifact_sha256,
            manual_path,
            claims,
            site_receipt,
        )

    @property
    def release_sha256(self) -> str:
        return self.manifest.artifact_sha256

    @property
    def page_url(self) -> str:
        """Canonical product route; a draft receipt does not claim it is public."""

        return self._site_page_url()

    @property
    def is_public(self) -> bool:
        """Whether the optional later owner transition has verified public proof."""

        return self.site_receipt.is_verified_public

    @property
    def publication_receipt(self) -> Receipt:
        """Compatibility spelling for callers that previously said publication."""

        return self.site_receipt

    def assert_current(self) -> None:
        """Refuse to use output bytes changed after Release completed."""

        _fresh_manifest(self.root, self.manifest)
        self._assert_site_receipt()


__all__ = ["ReleaseContext", "ProductRelease"]
