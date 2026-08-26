"""Deterministic Concept contract for the native-agent runtime.

Concept is cognitive work owned by the native agent: it researches the Wish,
decides the design's physical facts, and authors one drawing instruction per
image role.  This module identifies the exact upstream bindings, the brief,
research, drawing-instruction, and descriptor bytes, and the derived Wish
write-back the host is asked to accept, and rehashes the sealed concept tree
against them.  It does not judge whether the design is a good design — see
``workshop.concept.native_gate`` for the structural rule checks a brief must
satisfy before it is sealed.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping

from workshop._validation import bounded_text, copy_json_mapping, require_sha256
from workshop.artifacts import (
    ArtifactEntry,
    ArtifactManifest,
    artifact_manifest_from_mapping,
    build_artifact_manifest,
)
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import NativeMatchAssignment
from workshop.wish import Wish


NATIVE_CONCEPT_KIND = "autonomous-workshop.concept"
DERIVED_WISH_KIND = "autonomous-workshop.concept-derived-wish"
MAX_CONCEPT_JSON_BYTES = 2 * 1024 * 1024
OVERALL_IMAGE_ROLES = ("front", "top", "bottom", "exploded")
PERMITTED_IMAGE_SUFFIXES = frozenset((".png", ".jpg", ".jpeg", ".webp"))


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
        raise ContractError("native Concept values must be finite JSON") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


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


def _strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


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


def _walk_descriptor_entries(node: Any, label: str) -> list[dict[str, Any]]:
    """Flatten a descriptor's nested role tree into its leaf image entries."""

    if isinstance(node, Mapping) and "path" in node:
        return [dict(node)]
    if isinstance(node, Mapping):
        entries: list[dict[str, Any]] = []
        for value in node.values():
            entries.extend(_walk_descriptor_entries(value, label))
        return entries
    raise ContractError("%s is not a valid descriptor tree" % label)


@dataclass(frozen=True)
class DerivedWish:
    """The researched-constraints write-back, sealed inside the concept tree."""

    wish_sha256: str
    product_id: str
    objective: str
    context: Mapping[str, Any]
    constraints: Mapping[str, Any]
    schema_version: int = 1
    kind: str = DERIVED_WISH_KIND
    derived_wish_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("derived Wish schema_version must be 1")
        if self.kind != DERIVED_WISH_KIND:
            raise ContractError("derived Wish kind is invalid")
        require_sha256(self.wish_sha256, "derived Wish routed Wish sha256")
        bounded_text(self.product_id, "derived Wish product_id", 256)
        bounded_text(self.objective, "derived Wish objective", 50_000)
        context = copy_json_mapping(self.context, "derived Wish context")
        constraints = copy_json_mapping(
            self.constraints, "derived Wish constraints", nonempty=True
        )
        object.__setattr__(self, "context", _freeze(context))
        object.__setattr__(self, "constraints", _freeze(constraints))
        object.__setattr__(
            self,
            "derived_wish_sha256",
            _sha256(self._identity_dict()),
        )

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "wish_sha256": self.wish_sha256,
            "product_id": self.product_id,
            "objective": self.objective,
            "context": _thaw(self.context),
            "constraints": _thaw(self.constraints),
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["derived_wish_sha256"] = self.derived_wish_sha256
        return payload

    def assert_context(self, wish: Wish) -> None:
        if not isinstance(wish, Wish):
            raise ContractError("derived Wish context requires the routed Wish")
        if (
            self.product_id != wish.product_id
            or self.objective != wish.objective
            or _thaw(self.context) != dict(wish.context)
        ):
            raise ContractError(
                "derived Wish changed the routed Wish's own words"
            )

    @classmethod
    def from_mapping(cls, value: Any) -> "DerivedWish":
        expected = {
            "schema_version",
            "kind",
            "wish_sha256",
            "product_id",
            "objective",
            "context",
            "constraints",
            "derived_wish_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("derived Wish fields are invalid")
        derived = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            wish_sha256=value["wish_sha256"],
            product_id=value["product_id"],
            objective=value["objective"],
            context=value["context"],
            constraints=value["constraints"],
        )
        if dict(value) != derived.to_dict():
            raise ContractError("derived Wish hashes or canonical identity are invalid")
        return derived


@dataclass(frozen=True)
class ConceptTree:
    """A rehashed, disk-verified concept ready for the gate's rule checks."""

    root: Path
    manifest: ArtifactManifest
    brief: Mapping[str, Any]
    research: Mapping[str, Any]
    drawing_instructions: Mapping[str, Any]
    descriptor: Mapping[str, Any]
    derived_wish: DerivedWish


@dataclass(frozen=True)
class NativeConcept:
    """One pre-render proposal or host-sealed Concept revision."""

    round: int
    wish_sha256: str
    assignment_sha256: str
    taste_sha256: str
    blueprint_sha256: str
    invented_sha256: str
    concept_root: str
    concept_manifest: ArtifactManifest
    brief: Mapping[str, Any]
    brief_path: str
    brief_sha256: str
    research: Mapping[str, Any]
    research_path: str
    research_sha256: str
    drawing_instructions: Mapping[str, Any]
    drawing_instructions_path: str
    drawing_instructions_sha256: str
    descriptor: Mapping[str, Any]
    descriptor_path: str
    descriptor_sha256: str
    derived_wish: Mapping[str, Any]
    derived_wish_path: str
    derived_wish_sha256_field: str
    schema_version: int = 1
    kind: str = NATIVE_CONCEPT_KIND
    concept_sha256: str = field(init=False)
    images_rendered: bool = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("native Concept schema_version must be 1")
        if self.kind != NATIVE_CONCEPT_KIND:
            raise ContractError("native Concept kind is invalid")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("native Concept round must be from 1 through 100")
        for value, label in (
            (self.wish_sha256, "native Concept Wish sha256"),
            (self.assignment_sha256, "native Concept assignment sha256"),
            (self.taste_sha256, "native Concept TASTE sha256"),
            (self.blueprint_sha256, "native Concept blueprint sha256"),
            (self.invented_sha256, "native Concept Invented sha256"),
            (self.brief_sha256, "native Concept brief sha256"),
            (self.research_sha256, "native Concept research sha256"),
            (
                self.drawing_instructions_sha256,
                "native Concept drawing instructions sha256",
            ),
            (self.descriptor_sha256, "native Concept descriptor sha256"),
            (self.derived_wish_sha256_field, "native Concept derived Wish sha256"),
        ):
            require_sha256(value, label)
        expected_root = "artifacts/concept/r%04d/concept" % self.round
        if (
            _safe_relative(self.concept_root, "native Concept concept_root").as_posix()
            != expected_root
        ):
            raise ContractError("native Concept concept_root is not canonical for its round")
        for path, expected, label in (
            (self.brief_path, "brief.json", "native Concept brief path"),
            (self.research_path, "research.json", "native Concept research path"),
            (
                self.drawing_instructions_path,
                "prompts.json",
                "native Concept drawing instructions path",
            ),
            (self.descriptor_path, "descriptor.json", "native Concept descriptor path"),
            (
                self.derived_wish_path,
                "derived_wish.json",
                "native Concept derived Wish path",
            ),
        ):
            if path != expected:
                raise ContractError("%s must be %s" % (label, expected))
        if not isinstance(self.concept_manifest, ArtifactManifest):
            raise ContractError("native Concept requires an ArtifactManifest")
        self.concept_manifest.assert_valid()
        manifest_paths = {entry.path for entry in self.concept_manifest.entries}
        for path, label in (
            (self.brief_path, "brief.json"),
            (self.research_path, "research.json"),
            (self.drawing_instructions_path, "prompts.json"),
            (self.descriptor_path, "descriptor.json"),
            (self.derived_wish_path, "derived_wish.json"),
        ):
            if path not in manifest_paths:
                raise ContractError(
                    "native Concept manifest lacks its %s" % label
                )
        brief = copy_json_mapping(self.brief, "native Concept brief", nonempty=True)
        research = copy_json_mapping(
            self.research, "native Concept research", nonempty=True
        )
        drawing_instructions = copy_json_mapping(
            self.drawing_instructions,
            "native Concept drawing instructions",
            nonempty=True,
        )
        descriptor = copy_json_mapping(
            self.descriptor, "native Concept descriptor", nonempty=True
        )
        derived_wish = DerivedWish.from_mapping(self.derived_wish)
        image_entries = _walk_descriptor_entries(descriptor, "native Concept descriptor")
        entry_fields = {frozenset(entry) for entry in image_entries}
        if entry_fields == {frozenset(("path",))}:
            images_rendered = False
        elif entry_fields == {frozenset(("path", "sha256"))}:
            images_rendered = True
        else:
            raise ContractError(
                "native Concept descriptor entries must be uniformly pre-render or sealed"
            )
        for entry in image_entries:
            if set(entry) not in ({"path"}, {"path", "sha256"}):
                raise ContractError("native Concept descriptor entry fields are invalid")
            entry_path = _safe_relative(
                entry["path"], "native Concept descriptor image path"
            )
            if entry_path.suffix.casefold() not in PERMITTED_IMAGE_SUFFIXES:
                raise ContractError(
                    "native Concept descriptor image path has a forbidden suffix"
                )
            if images_rendered:
                require_sha256(
                    entry["sha256"], "native Concept descriptor image sha256"
                )
            if images_rendered and entry_path.as_posix() not in manifest_paths:
                raise ContractError(
                    "native Concept descriptor names an image outside its manifest"
                )
            if not images_rendered and entry_path.as_posix() in manifest_paths:
                raise ContractError(
                    "pre-render Concept manifest must not contain rendered images"
                )
        image_paths = [entry["path"] for entry in image_entries]
        if len(image_paths) != len(set(image_paths)):
            raise ContractError("native Concept descriptor images must be distinct files")
        source_paths = {
            self.brief_path,
            self.research_path,
            self.drawing_instructions_path,
            self.descriptor_path,
            self.derived_wish_path,
        }
        if not images_rendered and manifest_paths != source_paths:
            raise ContractError(
                "pre-render Concept manifest must contain exactly its five source documents"
            )
        object.__setattr__(self, "brief", _freeze(brief))
        object.__setattr__(self, "research", _freeze(research))
        object.__setattr__(self, "drawing_instructions", _freeze(drawing_instructions))
        object.__setattr__(self, "descriptor", _freeze(descriptor))
        object.__setattr__(self, "derived_wish", _freeze(derived_wish.to_dict()))
        object.__setattr__(self, "images_rendered", images_rendered)
        object.__setattr__(
            self,
            "concept_sha256",
            _sha256(self._identity_dict()),
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
            "concept_root": self.concept_root,
            "concept_manifest": self.concept_manifest.to_dict(),
            "brief_path": self.brief_path,
            "brief": _thaw(self.brief),
            "brief_sha256": self.brief_sha256,
            "research_path": self.research_path,
            "research": _thaw(self.research),
            "research_sha256": self.research_sha256,
            "drawing_instructions_path": self.drawing_instructions_path,
            "drawing_instructions": _thaw(self.drawing_instructions),
            "drawing_instructions_sha256": self.drawing_instructions_sha256,
            "descriptor_path": self.descriptor_path,
            "descriptor": _thaw(self.descriptor),
            "descriptor_sha256": self.descriptor_sha256,
            "derived_wish_path": self.derived_wish_path,
            "derived_wish": _thaw(self.derived_wish),
            "derived_wish_sha256_field": self.derived_wish_sha256_field,
        }

    def to_dict(self) -> dict[str, Any]:
        payload = self._identity_dict()
        payload["concept_sha256"] = self.concept_sha256
        return payload

    @classmethod
    def from_mapping(cls, value: Any) -> "NativeConcept":
        expected = {
            "schema_version",
            "kind",
            "round",
            "wish_sha256",
            "assignment_sha256",
            "taste_sha256",
            "blueprint_sha256",
            "invented_sha256",
            "concept_root",
            "concept_manifest",
            "brief_path",
            "brief",
            "brief_sha256",
            "research_path",
            "research",
            "research_sha256",
            "drawing_instructions_path",
            "drawing_instructions",
            "drawing_instructions_sha256",
            "descriptor_path",
            "descriptor",
            "descriptor_sha256",
            "derived_wish_path",
            "derived_wish",
            "derived_wish_sha256_field",
            "concept_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("native Concept fields are invalid")
        concept = cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            round=value["round"],
            wish_sha256=value["wish_sha256"],
            assignment_sha256=value["assignment_sha256"],
            taste_sha256=value["taste_sha256"],
            blueprint_sha256=value["blueprint_sha256"],
            invented_sha256=value["invented_sha256"],
            concept_root=value["concept_root"],
            concept_manifest=artifact_manifest_from_mapping(value["concept_manifest"]),
            brief_path=value["brief_path"],
            brief=value["brief"],
            brief_sha256=value["brief_sha256"],
            research_path=value["research_path"],
            research=value["research"],
            research_sha256=value["research_sha256"],
            drawing_instructions_path=value["drawing_instructions_path"],
            drawing_instructions=value["drawing_instructions"],
            drawing_instructions_sha256=value["drawing_instructions_sha256"],
            descriptor_path=value["descriptor_path"],
            descriptor=value["descriptor"],
            descriptor_sha256=value["descriptor_sha256"],
            derived_wish_path=value["derived_wish_path"],
            derived_wish=value["derived_wish"],
            derived_wish_sha256_field=value["derived_wish_sha256_field"],
        )
        if dict(value) != concept.to_dict():
            raise ContractError("native Concept hashes or canonical identity are invalid")
        return concept

    def assert_context(
        self,
        assignment: NativeMatchAssignment,
        invented: NativeInvented,
        wish: Wish,
    ) -> None:
        """Reject a concept detached from the exact accepted upstream inputs."""

        if not isinstance(assignment, NativeMatchAssignment) or not isinstance(
            invented, NativeInvented
        ):
            raise ContractError("native Concept context requires Match and Invent")
        invented.assert_context(assignment)
        if (
            self.wish_sha256 != assignment.wish_sha256
            or self.assignment_sha256 != assignment.assignment_sha256
            or self.taste_sha256 != assignment.selected_taste_sha256
            or self.blueprint_sha256 != assignment.blueprint_sha256
            or self.invented_sha256 != invented.invented_sha256
        ):
            raise ContractError("native Concept belongs to different Workshop inputs")
        DerivedWish.from_mapping(_thaw(self.derived_wish)).assert_context(wish)

    def validate_concept_tree(self, run_root: Path) -> ConceptTree:
        """Rehash the exact concept tree and return its canonical contents."""

        root = Path(run_root).resolve(strict=True)
        relative = _safe_relative(self.concept_root, "native Concept concept_root")
        concept_root = root.joinpath(*relative.parts)
        if concept_root.is_symlink() or not concept_root.is_dir():
            raise ArtifactError("native Concept tree is unavailable")
        current = (
            build_artifact_manifest(
                concept_root, created_at=self.concept_manifest.created_at
            )
            if self.images_rendered
            else _source_manifest(concept_root, self.concept_manifest.created_at)
        )
        if current.to_dict() != self.concept_manifest.to_dict():
            raise ArtifactError("native Concept tree differs from its manifest")

        def _read_bound(path_field: str, sha_field: str, label: str) -> dict[str, Any]:
            relative_path = _safe_relative(getattr(self, path_field), label)
            document, content = _strict_json_object(
                concept_root.joinpath(*relative_path.parts), label
            )
            if hashlib.sha256(content).hexdigest() != getattr(self, sha_field):
                raise ArtifactError("%s hash differs from its bytes" % label)
            return document

        brief = _read_bound("brief_path", "brief_sha256", "native Concept brief.json")
        if brief != _thaw(self.brief):
            raise ContractError("native Concept brief differs from brief.json")
        research = _read_bound(
            "research_path", "research_sha256", "native Concept research.json"
        )
        if research != _thaw(self.research):
            raise ContractError("native Concept research differs from research.json")
        drawing_instructions = _read_bound(
            "drawing_instructions_path",
            "drawing_instructions_sha256",
            "native Concept prompts.json",
        )
        if drawing_instructions != _thaw(self.drawing_instructions):
            raise ContractError(
                "native Concept drawing instructions differ from prompts.json"
            )
        descriptor = _read_bound(
            "descriptor_path", "descriptor_sha256", "native Concept descriptor.json"
        )
        if descriptor != _thaw(self.descriptor):
            raise ContractError("native Concept descriptor differs from descriptor.json")
        derived_wish_document = _read_bound(
            "derived_wish_path",
            "derived_wish_sha256_field",
            "native Concept derived_wish.json",
        )
        derived_wish = DerivedWish.from_mapping(_thaw(self.derived_wish))
        if derived_wish_document != derived_wish.to_dict():
            raise ContractError(
                "native Concept derived Wish differs from derived_wish.json"
            )
        if self.images_rendered:
            for entry in _walk_descriptor_entries(
                descriptor, "native Concept descriptor"
            ):
                entry_path = _safe_relative(entry["path"], "native Concept image path")
                image_bytes = (concept_root.joinpath(*entry_path.parts)).read_bytes()
                if hashlib.sha256(image_bytes).hexdigest() != entry["sha256"]:
                    raise ArtifactError(
                        "native Concept image %s differs from its bytes" % entry["path"]
                    )
        return ConceptTree(
            root=concept_root,
            manifest=self.concept_manifest,
            brief=brief,
            research=research,
            drawing_instructions=drawing_instructions,
            descriptor=descriptor,
            derived_wish=derived_wish,
        )


_CONCEPT_SOURCE_PATHS = (
    "brief.json",
    "derived_wish.json",
    "descriptor.json",
    "prompts.json",
    "research.json",
)


def _source_manifest(concept_root: Path, created_at: str) -> ArtifactManifest:
    """Hash only the five agent-authored pre-render Concept documents."""

    entries: list[ArtifactEntry] = []
    for relative in _CONCEPT_SOURCE_PATHS:
        path = concept_root / relative
        try:
            identity = path.lstat()
            content = path.read_bytes()
            after = path.lstat()
        except OSError as exc:
            raise ArtifactError(
                "native Concept source file is unavailable: %s" % relative
            ) from exc
        if (
            path.is_symlink()
            or not stat.S_ISREG(identity.st_mode)
            or (identity.st_dev, identity.st_ino, identity.st_mtime_ns, identity.st_size)
            != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        ):
            raise ArtifactError(
                "native Concept source file changed while hashing: %s" % relative
            )
        entries.append(
            ArtifactEntry(
                path=relative,
                bytes=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                executable=bool(identity.st_mode & stat.S_IXUSR),
            )
        )
    entries.sort(key=lambda entry: entry.path)
    artifact_sha256 = hashlib.sha256(
        _canonical_json([asdict(entry) for entry in entries])
    ).hexdigest()
    return ArtifactManifest(
        schema_version=1,
        artifact_sha256=artifact_sha256,
        entries=tuple(entries),
        total_bytes=sum(entry.bytes for entry in entries),
        created_at=created_at,
    )


def _seal_descriptor(node: Any, concept_root: Path) -> Any:
    if isinstance(node, Mapping) and set(node) == {"path"}:
        relative = _safe_relative(node["path"], "native Concept image path")
        path = concept_root.joinpath(*relative.parts)
        try:
            identity = path.lstat()
            content = path.read_bytes()
            after = path.lstat()
        except OSError as exc:
            raise ArtifactError(
                "native Concept rendered image is unavailable: %s" % relative.as_posix()
            ) from exc
        if (
            path.is_symlink()
            or not stat.S_ISREG(identity.st_mode)
            or (identity.st_dev, identity.st_ino, identity.st_mtime_ns, identity.st_size)
            != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        ):
            raise ArtifactError(
                "native Concept rendered image changed while hashing: %s"
                % relative.as_posix()
            )
        return {
            "path": relative.as_posix(),
            "sha256": hashlib.sha256(content).hexdigest(),
        }
    if isinstance(node, Mapping):
        return {
            key: _seal_descriptor(value, concept_root) for key, value in node.items()
        }
    raise ContractError("native Concept descriptor is not a valid descriptor tree")


def seal_rendered_concept(concept: NativeConcept, run_root: Path) -> NativeConcept:
    """Bind host-rendered image bytes and return the downstream Concept contract."""

    if not isinstance(concept, NativeConcept) or concept.images_rendered:
        raise ContractError("Concept image sealing requires a pre-render proposal")
    tree = concept.validate_concept_tree(run_root)
    descriptor = _seal_descriptor(tree.descriptor, tree.root)
    descriptor_bytes = _canonical_json(descriptor) + b"\n"
    descriptor_path = tree.root / concept.descriptor_path
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % descriptor_path.name,
        suffix=".tmp",
        dir=str(descriptor_path.parent),
    )
    temporary = Path(temporary_name)
    try:
        written = 0
        while written < len(descriptor_bytes):
            written += os.write(file_descriptor, descriptor_bytes[written:])
        os.fsync(file_descriptor)
        os.close(file_descriptor)
        file_descriptor = -1
        os.replace(temporary, descriptor_path)
    finally:
        if file_descriptor >= 0:
            os.close(file_descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    manifest = build_artifact_manifest(tree.root, created_at="content-addressed")
    sealed = NativeConcept(
        round=concept.round,
        wish_sha256=concept.wish_sha256,
        assignment_sha256=concept.assignment_sha256,
        taste_sha256=concept.taste_sha256,
        blueprint_sha256=concept.blueprint_sha256,
        invented_sha256=concept.invented_sha256,
        concept_root=concept.concept_root,
        concept_manifest=manifest,
        brief=_thaw(concept.brief),
        brief_path=concept.brief_path,
        brief_sha256=concept.brief_sha256,
        research=_thaw(concept.research),
        research_path=concept.research_path,
        research_sha256=concept.research_sha256,
        drawing_instructions=_thaw(concept.drawing_instructions),
        drawing_instructions_path=concept.drawing_instructions_path,
        drawing_instructions_sha256=concept.drawing_instructions_sha256,
        descriptor=descriptor,
        descriptor_path=concept.descriptor_path,
        descriptor_sha256=hashlib.sha256(descriptor_bytes).hexdigest(),
        derived_wish=_thaw(concept.derived_wish),
        derived_wish_path=concept.derived_wish_path,
        derived_wish_sha256_field=concept.derived_wish_sha256_field,
    )
    sealed.validate_concept_tree(run_root)
    return sealed


__all__ = [
    "DERIVED_WISH_KIND",
    "MAX_CONCEPT_JSON_BYTES",
    "NATIVE_CONCEPT_KIND",
    "OVERALL_IMAGE_ROLES",
    "PERMITTED_IMAGE_SUFFIXES",
    "ConceptTree",
    "DerivedWish",
    "NativeConcept",
    "seal_rendered_concept",
]
