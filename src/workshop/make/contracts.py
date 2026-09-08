"""Immutable outputs owned by the Make stage."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from workshop._validation import copy_json_mapping
from workshop.artifacts.core import ArtifactManifest, build_artifact_manifest
from workshop.errors import ArtifactError, ContractError


# Customer-facing copy (Make and Release title and summary) is what a buyer
# reads.  Workshop-internal vocabulary must never leak into it; the rule is
# deterministic whole-word matching, mirrored by the run-local finalizer.
CUSTOMER_COPY_BANNED_WORDS = (
    # Case-sensitive: these read as Workshop nouns only when capitalized;
    # lowercase "wish", "taste", and "inventor" are ordinary customer words.
    "Wish",
    "Taste",
    "Inventor",
)
CUSTOMER_COPY_BANNED_WORDS_ANY_CASE = (
    # No ordinary customer sentence needs these in any case.
    "playtest",
    "finalizer",
)
# Goal, Make, Release, Spark, Forge, Quest, artifact, and gate stay guidance
# only: published toys legitimately use them ("Starling Gate", "a spark of
# light"), so a deterministic ban would reject truthful customer copy.
CUSTOMER_COPY_BANNED_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:%s|(?i:%s))(?![A-Za-z0-9])"
    % (
        "|".join(re.escape(word) for word in CUSTOMER_COPY_BANNED_WORDS),
        "|".join(re.escape(word) for word in CUSTOMER_COPY_BANNED_WORDS_ANY_CASE),
    )
)
MAX_CUSTOMER_TITLE_CHARS = 300
MAX_CUSTOMER_SUMMARY_CHARS = 2_000


def customer_copy_text(value: Any, label: str, maximum: int) -> str:
    """Validate customer-facing text with the one rule Make and Release share.

    Stripped, no carriage returns, at most ``maximum`` characters, and free of
    Workshop-internal vocabulary, so a sealed Made title can always be
    released byte-for-byte.
    """

    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\n\t" for character in value)
        or any(ord(character) == 127 for character in value)
    ):
        raise ContractError(
            "%s must be bounded substantive text of at most %d characters "
            "without leading or trailing whitespace or carriage returns "
            "(customer-copy)" % (label, maximum)
        )
    leaked = CUSTOMER_COPY_BANNED_RE.search(value)
    if leaked is not None:
        raise ContractError(
            "%s must not contain Workshop-internal vocabulary; found %r "
            "(customer-copy)" % (label, leaked.group(0))
        )
    return value


def validate_product_copy(product: Mapping[str, Any], label: str) -> None:
    """Apply the customer-copy rule to a product's title and summary."""

    customer_copy_text(product.get("title"), "%s title" % label, MAX_CUSTOMER_TITLE_CHARS)
    customer_copy_text(
        product.get("summary"), "%s summary" % label, MAX_CUSTOMER_SUMMARY_CHARS
    )


def _fresh_manifest(root: Path, manifest: ArtifactManifest) -> ArtifactManifest:
    current = build_artifact_manifest(root, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ArtifactError("artifact bytes changed after the job completed")
    return current


@dataclass(frozen=True)
class Made:
    """One immutable toy or game revision returned by Make."""

    artifact_root: Path
    artifact_manifest: ArtifactManifest
    product: Mapping[str, Any]

    def __post_init__(self) -> None:
        root = Path(self.artifact_root)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise ContractError("Made artifact_root must be an absolute regular directory")
        if not isinstance(self.artifact_manifest, ArtifactManifest):
            raise ContractError("Made requires an ArtifactManifest")
        product = copy_json_mapping(self.product, "Made product", nonempty=True)
        validate_product_copy(product, "Made product")
        _fresh_manifest(root, self.artifact_manifest)
        object.__setattr__(self, "artifact_root", root.resolve(strict=True))
        object.__setattr__(self, "product", product)

    @classmethod
    def from_root(cls, artifact_root: Path, product: Mapping[str, Any]) -> "Made":
        root = Path(artifact_root).resolve(strict=True)
        return cls(
            root,
            build_artifact_manifest(root, created_at="content-addressed"),
            product,
        )

    @property
    def artifact_sha256(self) -> str:
        return self.artifact_manifest.artifact_sha256

    def assert_current(self) -> None:
        _fresh_manifest(self.artifact_root, self.artifact_manifest)


__all__ = [
    "CUSTOMER_COPY_BANNED_WORDS",
    "CUSTOMER_COPY_BANNED_WORDS_ANY_CASE",
    "MAX_CUSTOMER_SUMMARY_CHARS",
    "MAX_CUSTOMER_TITLE_CHARS",
    "Made",
    "customer_copy_text",
    "validate_product_copy",
]
