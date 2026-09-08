"""Immutable outputs owned by the Make stage."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional

from workshop._validation import bounded_text, copy_json_mapping
from workshop.artifacts.core import ArtifactManifest, build_artifact_manifest
from workshop.errors import ArtifactError, ContractError


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
    cad_project_path: Optional[str] = None

    def __post_init__(self) -> None:
        root = Path(self.artifact_root)
        if not root.is_absolute() or root.is_symlink() or not root.is_dir():
            raise ContractError("Made artifact_root must be an absolute regular directory")
        if not isinstance(self.artifact_manifest, ArtifactManifest):
            raise ContractError("Made requires an ArtifactManifest")
        product = copy_json_mapping(self.product, "Made product", nonempty=True)
        for key in ("title", "summary"):
            bounded_text(product.get(key), "Made product %s" % key, 2_000)
        if self.cad_project_path is not None:
            if not isinstance(self.cad_project_path, str):
                raise ContractError("Made cad_project_path must be a safe relative path")
            project = PurePosixPath(self.cad_project_path)
            if (
                not self.cad_project_path
                or project.is_absolute()
                or project.as_posix() != self.cad_project_path
                or "\\" in self.cad_project_path
                or any(part in ("", ".", "..") for part in project.parts)
            ):
                raise ContractError("Made cad_project_path must be a safe relative path")
            project_root = root.joinpath(*project.parts)
            if project_root.is_symlink() or not project_root.is_dir():
                raise ContractError(
                    "Made cad_project_path must identify a regular directory"
                )
        _fresh_manifest(root, self.artifact_manifest)
        object.__setattr__(self, "artifact_root", root.resolve(strict=True))
        object.__setattr__(self, "product", product)

    @classmethod
    def from_root(
        cls,
        artifact_root: Path,
        product: Mapping[str, Any],
        *,
        cad_project_path: Optional[str] = None,
    ) -> "Made":
        root = Path(artifact_root).resolve(strict=True)
        return cls(
            root,
            build_artifact_manifest(root, created_at="content-addressed"),
            product,
            cad_project_path,
        )

    @property
    def artifact_sha256(self) -> str:
        return self.artifact_manifest.artifact_sha256

    def assert_current(self) -> None:
        _fresh_manifest(self.artifact_root, self.artifact_manifest)


__all__ = ["Made"]
