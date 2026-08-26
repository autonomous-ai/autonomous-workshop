"""Inputs, feedback, and immutable outputs owned by the Make stage."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

from workshop._validation import bounded_text, copy_json_mapping
from workshop.artifacts.core import ArtifactManifest, build_artifact_manifest
from workshop.errors import ArtifactError, ContractError
from workshop.product import PLAYTHING_LANES, WORKSHOP_JOBS


_SEVERITIES = frozenset(("note", "improve", "block"))


def _fresh_manifest(root: Path, manifest: ArtifactManifest) -> ArtifactManifest:
    current = build_artifact_manifest(root, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ArtifactError("artifact bytes changed after the job completed")
    return current


@dataclass(frozen=True)
class Feedback:
    """One actionable finding that sends the product back through Make."""

    code: str
    area: str
    severity: str
    finding: str
    change: str
    evidence_refs: Sequence[str] = field(default_factory=tuple)
    invalidates: Sequence[str] = ("playtest", "release", "deliver")

    def __post_init__(self) -> None:
        bounded_text(self.code, "feedback code", 200)
        bounded_text(self.area, "feedback area", 200)
        if self.severity not in _SEVERITIES:
            raise ContractError("feedback severity must be note, improve, or block")
        bounded_text(self.finding, "feedback finding")
        bounded_text(self.change, "feedback change")
        refs = tuple(self.evidence_refs)
        invalidates = tuple(self.invalidates)
        if any(not isinstance(item, str) or not item for item in refs):
            raise ContractError("feedback evidence_refs must be non-empty strings")
        if any(item not in WORKSHOP_JOBS for item in invalidates):
            raise ContractError("feedback invalidates an unknown Workshop job")
        object.__setattr__(self, "evidence_refs", refs)
        object.__setattr__(self, "invalidates", invalidates)

    def to_dict(self):
        return {
            "code": self.code,
            "area": self.area,
            "severity": self.severity,
            "finding": self.finding,
            "change": self.change,
            "evidence_refs": list(self.evidence_refs),
            "invalidates": list(self.invalidates),
        }


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
        for key in ("title", "summary", "lane"):
            bounded_text(product.get(key), "Made product %s" % key, 2_000)
        if product["lane"] not in PLAYTHING_LANES:
            raise ContractError("Made product lane must be a Workshop plaything lane")
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


__all__ = ["Feedback", "Made"]
