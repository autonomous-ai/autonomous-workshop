"""Deterministic Make handoff for a native-agent product run.

The selected Manager owns design and CAD creation. The host accepts one exact
product tree whose manifest, facts, upstream bindings, and CAD-verification receipt all
match the bytes on disk.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping

from workshop._validation import copy_json_mapping, require_sha256
from workshop.artifacts import (
    ArtifactManifest,
    artifact_manifest_from_mapping,
    build_artifact_manifest,
)
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.make.contracts import Made
from workshop.match.native import NativeMatchAssignment


NATIVE_MADE_KIND = "autonomous-workshop.made"


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
        raise ContractError("native Made values must be finite JSON") from exc


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


def _strict_json_object(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ArtifactError("%s is unavailable" % label) from exc
    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError("%s must contain strict UTF-8 JSON" % label) from exc
    if not isinstance(value, dict):
        raise ContractError("%s must contain one JSON object" % label)
    return value, content


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


@dataclass(frozen=True)
class NativeMade:
    """One complete, content-addressed Make revision proposed by Codex."""

    round: int
    wish_sha256: str
    assignment_sha256: str
    taste_sha256: str
    blueprint_sha256: str
    invented_sha256: str
    product_root: str
    cad_project_path: str
    product_manifest: ArtifactManifest
    product: Mapping[str, Any]
    product_json_sha256: str
    cad_verification_path: str
    cad_verification_sha256: str
    schema_version: int = 1
    kind: str = NATIVE_MADE_KIND
    made_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("native Made schema_version must be 1")
        if self.kind != NATIVE_MADE_KIND:
            raise ContractError("native Made kind is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("native Made round must be from 1 through 100")
        for value, label in (
            (self.wish_sha256, "native Made Wish sha256"),
            (self.assignment_sha256, "native Made assignment sha256"),
            (self.taste_sha256, "native Made TASTE sha256"),
            (self.blueprint_sha256, "native Made blueprint sha256"),
            (self.invented_sha256, "native Made Invented sha256"),
            (self.product_json_sha256, "native Made product.json sha256"),
            (self.cad_verification_sha256, "native Made CAD verification sha256"),
        ):
            require_sha256(value, label)
        expected_root = "artifacts/make/r%04d/product" % self.round
        if _safe_relative(self.product_root, "native Made product_root").as_posix() != expected_root:
            raise ContractError("native Made product_root is not canonical for its round")
        _safe_relative(self.cad_project_path, "native Made CAD project path")
        _safe_relative(
            self.cad_verification_path, "native Made CAD verification path"
        )
        if not isinstance(self.product_manifest, ArtifactManifest):
            raise ContractError("native Made requires an ArtifactManifest")
        self.product_manifest.assert_valid()
        product = copy_json_mapping(self.product, "native Made product", nonempty=True)
        frozen_product = _freeze(product)
        object.__setattr__(self, "product", frozen_product)
        paths = {entry.path for entry in self.product_manifest.entries}
        if "product.json" not in paths:
            raise ContractError("native Made manifest must contain product.json")
        if self.cad_verification_path not in paths:
            raise ContractError("native Made manifest lacks its CAD verification receipt")
        if not any(path.endswith(".step") for path in paths):
            raise ContractError("native Made manifest must contain a STEP artifact")
        if not any(path.endswith(".stl") for path in paths):
            raise ContractError("native Made manifest must contain a printable STL")
        object.__setattr__(
            self,
            "made_sha256",
            hashlib.sha256(_canonical_json(self._identity_dict())).hexdigest(),
        )

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "round": self.round,
            "wish_sha256": self.wish_sha256,
            "assignment_sha256": self.assignment_sha256,
            "taste_sha256": self.taste_sha256,
            "blueprint_sha256": self.blueprint_sha256,
            "invented_sha256": self.invented_sha256,
            "product_root": self.product_root,
            "cad_project_path": self.cad_project_path,
            "product_manifest": self.product_manifest.to_dict(),
            "product": _thaw(self.product),
            "product_json_sha256": self.product_json_sha256,
            "cad_verification_path": self.cad_verification_path,
            "cad_verification_sha256": self.cad_verification_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["made_sha256"] = self.made_sha256
        return payload

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeMade":
        expected = {
            "schema_version",
            "kind",
            "round",
            "wish_sha256",
            "assignment_sha256",
            "taste_sha256",
            "blueprint_sha256",
            "invented_sha256",
            "product_root",
            "cad_project_path",
            "product_manifest",
            "product",
            "product_json_sha256",
            "cad_verification_path",
            "cad_verification_sha256",
            "made_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("native Made fields are invalid")
        made = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            round=value["round"],
            wish_sha256=value["wish_sha256"],
            assignment_sha256=value["assignment_sha256"],
            taste_sha256=value["taste_sha256"],
            blueprint_sha256=value["blueprint_sha256"],
            invented_sha256=value["invented_sha256"],
            product_root=value["product_root"],
            cad_project_path=value["cad_project_path"],
            product_manifest=artifact_manifest_from_mapping(value["product_manifest"]),
            product=value["product"],
            product_json_sha256=value["product_json_sha256"],
            cad_verification_path=value["cad_verification_path"],
            cad_verification_sha256=value["cad_verification_sha256"],
        )
        if dict(value) != made.to_dict():
            raise ContractError("native Made hashes or canonical identity are invalid")
        return made

    def assert_context(
        self,
        assignment: NativeMatchAssignment,
        invented: NativeInvented,
        *,
        expected_round: int,
    ) -> None:
        if not isinstance(assignment, NativeMatchAssignment) or not isinstance(
            invented, NativeInvented
        ):
            raise ContractError("native Made context requires Match and Invent")
        invented.assert_context(assignment)
        if (
            self.round != expected_round
            or self.wish_sha256 != assignment.wish_sha256
            or self.assignment_sha256 != assignment.assignment_sha256
            or self.taste_sha256 != assignment.selected_taste_sha256
            or self.blueprint_sha256 != assignment.blueprint_sha256
            or self.invented_sha256 != invented.invented_sha256
        ):
            raise ContractError("native Made belongs to different Workshop inputs")

    def validate_product_tree(self, run_root: Path) -> Made:
        """Rehash the exact product tree and return the canonical Made contract."""

        root = Path(run_root).resolve(strict=True)
        relative = _safe_relative(self.product_root, "native Made product_root")
        product_root = root.joinpath(*relative.parts)
        if product_root.is_symlink() or not product_root.is_dir():
            raise ArtifactError("native Made product tree is unavailable")
        current = build_artifact_manifest(
            product_root, created_at=self.product_manifest.created_at
        )
        if current.to_dict() != self.product_manifest.to_dict():
            raise ArtifactError("native Made product tree differs from its manifest")
        page, page_bytes = _strict_json_object(
            product_root / "product.json", "native Made product.json"
        )
        if hashlib.sha256(page_bytes).hexdigest() != self.product_json_sha256:
            raise ArtifactError("native Made product.json hash differs from its bytes")
        if page != _thaw(self.product):
            raise ContractError("native Made product differs from product.json")
        verification = product_root.joinpath(
            *_safe_relative(
                self.cad_verification_path, "native Made CAD verification path"
            ).parts
        )
        try:
            verification_bytes = verification.read_bytes()
        except OSError as exc:
            raise ArtifactError("native Made CAD verification is unavailable") from exc
        if hashlib.sha256(verification_bytes).hexdigest() != self.cad_verification_sha256:
            raise ArtifactError("native Made CAD verification hash differs from its bytes")
        cad_project = product_root.joinpath(
            *_safe_relative(self.cad_project_path, "native Made CAD project path").parts
        )
        if cad_project.is_symlink() or not cad_project.is_dir():
            raise ArtifactError("native Made CAD project is unavailable")
        return Made(product_root, self.product_manifest, page)


__all__ = ["NATIVE_MADE_KIND", "NativeMade"]
