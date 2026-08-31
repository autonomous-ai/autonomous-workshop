"""Route-aware Concept contracts.

The records in this module identify authored Concept source and already-present
image bytes.  They are deliberately independent of Workshop lifecycle, runtime,
credential, integration, and effect modules.
"""

from __future__ import annotations

import hashlib
import json
import stat
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

from workshop._validation import bounded_text, copy_json_mapping, require_sha256
from workshop.artifacts import ArtifactEntry, ArtifactManifest, artifact_manifest_from_mapping
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.match.native import NativeMatchAssignment
from workshop.wish import Wish

from .native import DerivedWish, OVERALL_IMAGE_ROLES, PERMITTED_IMAGE_SUFFIXES


CONCEPT_PROVENANCE_KIND = "autonomous-workshop.concept-provenance"
PRE_RENDER_CONCEPT_KIND = "autonomous-workshop.concept-pre-render"
SEALED_CONCEPT_KIND = "autonomous-workshop.concept-sealed"
CONCEPT_ORIGINS = frozenset(("invent", "spark-make"))
MAX_CONCEPT_FILE_BYTES = 2 * 1024 * 1024
MAX_CONCEPT_IMAGE_BYTES = 24 * 1024 * 1024
SOURCE_PATHS = (
    "brief.json",
    "derived_wish.json",
    "descriptor.json",
    "prompts.json",
    "research.json",
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
        raise ContractError("Concept v2 values must be finite JSON") from exc


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
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
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


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON number: %s" % value)


def _read_regular(path: Path, label: str, maximum: int = MAX_CONCEPT_FILE_BYTES) -> bytes:
    try:
        before = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(before.st_mode):
            raise ArtifactError("%s must be a regular file" % label)
        if before.st_size > maximum:
            raise ArtifactError("%s exceeds the %d-byte limit" % (label, maximum))
        content = path.read_bytes()
        after = path.lstat()
    except ArtifactError:
        raise
    except OSError as exc:
        raise ArtifactError("%s is unavailable" % label) from exc
    if (
        (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size)
        != (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size)
        or len(content) != before.st_size
    ):
        raise ArtifactError("%s changed while being read" % label)
    return content


def _read_json(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    content = _read_regular(path, label)
    try:
        value = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError("%s must contain strict finite UTF-8 JSON" % label) from exc
    if not isinstance(value, dict):
        raise ContractError("%s must contain one JSON object" % label)
    return value, content


def _manifest(entries: list[ArtifactEntry], created_at: str) -> ArtifactManifest:
    ordered = tuple(sorted(entries, key=lambda entry: entry.path))
    identity = [asdict(entry) for entry in ordered]
    return ArtifactManifest(
        schema_version=1,
        artifact_sha256=hashlib.sha256(_canonical_json(identity)).hexdigest(),
        entries=ordered,
        total_bytes=sum(entry.bytes for entry in ordered),
        created_at=created_at,
    )


def _entry(path: str, content: bytes, mode: int = 0) -> ArtifactEntry:
    return ArtifactEntry(
        path=path,
        bytes=len(content),
        sha256=hashlib.sha256(content).hexdigest(),
        executable=bool(mode & stat.S_IXUSR),
    )


def _descriptor_entries(node: Any, label: str) -> list[dict[str, Any]]:
    if isinstance(node, Mapping) and "path" in node:
        return [dict(node)]
    if isinstance(node, Mapping):
        found: list[dict[str, Any]] = []
        for child in node.values():
            found.extend(_descriptor_entries(child, label))
        return found
    raise ContractError("%s is not a descriptor tree" % label)


def _component_keys(brief: Mapping[str, Any]) -> set[str]:
    components = brief.get("components")
    if (
        isinstance(components, (str, bytes))
        or not isinstance(components, Sequence)
        or not components
    ):
        raise ContractError("Concept brief must name at least one component")
    keys: set[str] = set()
    for component in components:
        if not isinstance(component, Mapping) or not isinstance(component.get("key"), str):
            raise ContractError("Concept brief component key is invalid")
        if component["key"] in keys:
            raise ContractError("Concept brief component keys must be unique")
        keys.add(component["key"])
    return keys


def _validate_descriptor(
    descriptor: Mapping[str, Any], brief: Mapping[str, Any], *, sealed: bool
) -> None:
    expected_top = set(OVERALL_IMAGE_ROLES) | {"components"}
    if set(descriptor) != expected_top:
        raise ContractError("Concept descriptor roles are incomplete or unknown")
    components = descriptor.get("components")
    if not isinstance(components, Mapping) or set(components) != _component_keys(brief):
        raise ContractError("Concept descriptor component roles are incomplete or unknown")
    entries = _descriptor_entries(descriptor, "Concept descriptor")
    expected_fields = {"path", "sha256"} if sealed else {"path"}
    paths: list[str] = []
    for item in entries:
        if set(item) != expected_fields:
            state = "sealed" if sealed else "pre-render"
            raise ContractError("Concept %s descriptor leaf fields are invalid" % state)
        relative = _safe_relative(item["path"], "Concept descriptor image path")
        if relative.suffix.casefold() not in PERMITTED_IMAGE_SUFFIXES:
            raise ContractError("Concept descriptor image suffix is forbidden")
        if sealed:
            require_sha256(item["sha256"], "Concept descriptor image sha256")
        paths.append(relative.as_posix())
    if len(paths) != len(set(paths)):
        raise ContractError("Concept descriptor image paths must be distinct")


@dataclass(frozen=True)
class ConceptProvenance:
    origin: str
    wish_sha256: str
    product_id: str
    objective: str
    context: Mapping[str, Any]
    assignment_sha256: str
    taste_sha256: str
    blueprint_sha256: str
    invented_sha256: str
    creative_source_path: str
    creative_source_sha256: str
    round: int
    standing_concept_sha256: Optional[str] = None
    revision_input_sha256: Optional[str] = None
    schema_version: int = 2
    kind: str = CONCEPT_PROVENANCE_KIND
    provenance_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 2 or type(self.schema_version) is not int:
            raise ContractError("Concept provenance schema_version must be 2")
        if self.kind != CONCEPT_PROVENANCE_KIND:
            raise ContractError("Concept provenance kind is invalid")
        if self.origin not in CONCEPT_ORIGINS:
            raise ContractError("Concept provenance origin must be invent or spark-make")
        if type(self.round) is not int or not 1 <= self.round <= 100:
            raise ContractError("Concept provenance round must be from 1 through 100")
        for value, label in (
            (self.wish_sha256, "Concept provenance Wish sha256"),
            (self.assignment_sha256, "Concept provenance assignment sha256"),
            (self.taste_sha256, "Concept provenance TASTE sha256"),
            (self.blueprint_sha256, "Concept provenance blueprint sha256"),
            (self.invented_sha256, "Concept provenance Invented sha256"),
            (self.creative_source_sha256, "Concept provenance creative-source sha256"),
        ):
            require_sha256(value, label)
        bounded_text(self.product_id, "Concept provenance product_id", 256)
        bounded_text(self.objective, "Concept provenance objective", 50_000)
        context = copy_json_mapping(self.context, "Concept provenance context")
        _safe_relative(self.creative_source_path, "Concept provenance creative-source path")
        revision_values = (self.standing_concept_sha256, self.revision_input_sha256)
        if self.round == 1 and any(value is not None for value in revision_values):
            raise ContractError("initial Concept provenance must not name revision inputs")
        if self.round > 1 and any(value is None for value in revision_values):
            raise ContractError("revised Concept provenance requires standing Concept and revision input")
        for value, label in zip(
            revision_values,
            ("standing Concept sha256", "revision input sha256"),
        ):
            if value is not None:
                require_sha256(value, "Concept provenance %s" % label)
        object.__setattr__(self, "context", _freeze(dict(context)))
        object.__setattr__(self, "provenance_sha256", _sha256(self._identity_dict()))

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "origin": self.origin,
            "wish_sha256": self.wish_sha256,
            "product_id": self.product_id,
            "objective": self.objective,
            "context": _thaw(self.context),
            "assignment_sha256": self.assignment_sha256,
            "taste_sha256": self.taste_sha256,
            "blueprint_sha256": self.blueprint_sha256,
            "invented_sha256": self.invented_sha256,
            "creative_source_path": self.creative_source_path,
            "creative_source_sha256": self.creative_source_sha256,
            "round": self.round,
            "standing_concept_sha256": self.standing_concept_sha256,
            "revision_input_sha256": self.revision_input_sha256,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self._identity_dict()
        result["provenance_sha256"] = self.provenance_sha256
        return result

    @classmethod
    def from_mapping(cls, value: Any) -> "ConceptProvenance":
        if not isinstance(value, Mapping):
            raise ContractError("Concept provenance must be an object")
        fields = set(cls.__dataclass_fields__) - {"provenance_sha256"}
        if set(value) != fields | {"provenance_sha256"}:
            raise ContractError("Concept provenance fields are invalid")
        created = cls(**{key: value[key] for key in fields})
        if dict(value) != created.to_dict():
            raise ContractError("Concept provenance identity is not canonical")
        return created


@dataclass(frozen=True)
class ConceptExpectedContext:
    origin: str
    wish: Wish
    wish_sha256: str
    assignment: NativeMatchAssignment
    invented: NativeInvented
    creative_source_path: str
    creative_source_sha256: str
    round: int
    standing_concept_sha256: Optional[str] = None
    revision_input_sha256: Optional[str] = None

    def assert_provenance(self, provenance: ConceptProvenance, run_root: Path) -> None:
        if not isinstance(provenance, ConceptProvenance):
            raise ContractError("expected Concept context requires v2 provenance")
        if not isinstance(self.wish, Wish):
            raise ContractError("expected Concept context requires the routed Wish")
        if not isinstance(self.assignment, NativeMatchAssignment):
            raise ContractError("expected Concept context requires the assignment")
        if not isinstance(self.invented, NativeInvented):
            raise ContractError("expected Concept context requires the Invented contract")
        self.invented.assert_context(self.assignment)
        expected = {
            "origin": self.origin,
            "wish_sha256": self.wish_sha256,
            "product_id": self.wish.product_id,
            "objective": self.wish.objective,
            "context": dict(self.wish.context),
            "assignment_sha256": self.assignment.assignment_sha256,
            "taste_sha256": self.assignment.selected_taste_sha256,
            "blueprint_sha256": self.assignment.blueprint_sha256,
            "invented_sha256": self.invented.invented_sha256,
            "creative_source_path": self.creative_source_path,
            "creative_source_sha256": self.creative_source_sha256,
            "round": self.round,
            "standing_concept_sha256": self.standing_concept_sha256,
            "revision_input_sha256": self.revision_input_sha256,
        }
        actual = provenance._identity_dict()
        for name, expected_value in expected.items():
            if actual[name] != expected_value:
                raise ContractError("Concept provenance %s differs from expected context" % name)
        root = Path(run_root).resolve(strict=True)
        relative = _safe_relative(self.creative_source_path, "expected creative-source path")
        content = _read_regular(root.joinpath(*relative.parts), "Concept creative-source")
        if hashlib.sha256(content).hexdigest() != self.creative_source_sha256:
            raise ArtifactError("Concept creative-source sha256 differs from its bytes")
        try:
            source = json.loads(
                content.decode("utf-8"),
                object_pairs_hook=_strict_object,
                parse_constant=_reject_constant,
            )
        except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise ContractError("Concept creative-source must be strict finite UTF-8 JSON") from exc
        expected_source = {
            "selected_inventor_id": self.assignment.selected_inventor_id,
            "ranking": [item.to_dict() for item in self.assignment.ranking],
            "concept": self.invented.to_dict()["concept"],
            "research": self.invented.to_dict()["research"],
        }
        if not isinstance(source, Mapping):
            raise ContractError("Concept creative-source must be an object")
        if set(source) != set(expected_source):
            raise ContractError("Concept creative-source fields differ from accepted provenance")
        for name, expected_value in expected_source.items():
            if source.get(name) != expected_value:
                raise ContractError("Concept creative-source %s differs from accepted provenance" % name)


@dataclass(frozen=True)
class PreRenderConcept:
    root: Path
    provenance: ConceptProvenance
    source_manifest: ArtifactManifest
    brief: Mapping[str, Any]
    research: Mapping[str, Any]
    drawing_instructions: Mapping[str, Any]
    descriptor: Mapping[str, Any]
    derived_wish: DerivedWish
    schema_version: int = 2
    kind: str = PRE_RENDER_CONCEPT_KIND
    concept_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 2 or type(self.schema_version) is not int:
            raise ContractError("pre-render Concept schema_version must be 2")
        if self.kind != PRE_RENDER_CONCEPT_KIND:
            raise ContractError("pre-render Concept kind is invalid")
        if not isinstance(self.provenance, ConceptProvenance):
            raise ContractError("pre-render Concept requires v2 provenance")
        if not isinstance(self.source_manifest, ArtifactManifest):
            raise ContractError("pre-render Concept requires a source manifest")
        self.source_manifest.assert_valid()
        if {entry.path for entry in self.source_manifest.entries} != set(SOURCE_PATHS):
            raise ContractError("pre-render Concept manifest must contain exactly its source files")
        expected_root = "artifacts/concept/r%04d/concept" % self.provenance.round
        if self.root.as_posix().rstrip("/").endswith(expected_root) is False:
            raise ContractError("pre-render Concept root is not canonical for its round")
        brief = copy_json_mapping(self.brief, "pre-render Concept brief", nonempty=True)
        research = copy_json_mapping(self.research, "pre-render Concept research", nonempty=True)
        prompts = copy_json_mapping(
            self.drawing_instructions, "pre-render Concept drawing instructions", nonempty=True
        )
        descriptor = copy_json_mapping(
            self.descriptor, "pre-render Concept descriptor", nonempty=True
        )
        if not isinstance(self.derived_wish, DerivedWish):
            raise ContractError("pre-render Concept requires a DerivedWish")
        _validate_descriptor(descriptor, brief, sealed=False)
        object.__setattr__(self, "brief", _freeze(dict(brief)))
        object.__setattr__(self, "research", _freeze(dict(research)))
        object.__setattr__(self, "drawing_instructions", _freeze(dict(prompts)))
        object.__setattr__(self, "descriptor", _freeze(dict(descriptor)))
        object.__setattr__(self, "concept_sha256", _sha256(self._identity_dict()))

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "provenance": self.provenance.to_dict(),
            "source_manifest": self.source_manifest.to_dict(),
            "brief": _thaw(self.brief),
            "research": _thaw(self.research),
            "drawing_instructions": _thaw(self.drawing_instructions),
            "descriptor": _thaw(self.descriptor),
            "derived_wish": self.derived_wish.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        result = self._identity_dict()
        result["concept_sha256"] = self.concept_sha256
        return result

    def assert_context(self, expected: ConceptExpectedContext, run_root: Path) -> None:
        expected.assert_provenance(self.provenance, run_root)
        self.derived_wish.assert_context(expected.wish)
        if self.derived_wish.wish_sha256 != expected.wish_sha256:
            raise ContractError("derived Wish routed Wish sha256 differs from expected context")

    def validate_tree(self) -> "PreRenderConcept":
        loaded = load_pre_render_concept(self.root.parents[3], self.provenance)
        if loaded.to_dict() != self.to_dict():
            raise ArtifactError("pre-render Concept source tree differs from its identity")
        return self

    @classmethod
    def from_mapping(cls, value: Any, *, root: Path) -> "PreRenderConcept":
        expected = {
            "schema_version", "kind", "provenance", "source_manifest", "brief",
            "research", "drawing_instructions", "descriptor", "derived_wish",
            "concept_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("pre-render Concept fields are invalid")
        created = cls(
            root=Path(root),
            schema_version=value["schema_version"],
            kind=value["kind"],
            provenance=ConceptProvenance.from_mapping(value["provenance"]),
            source_manifest=artifact_manifest_from_mapping(value["source_manifest"]),
            brief=value["brief"],
            research=value["research"],
            drawing_instructions=value["drawing_instructions"],
            descriptor=value["descriptor"],
            derived_wish=DerivedWish.from_mapping(value["derived_wish"]),
        )
        if dict(value) != created.to_dict():
            raise ContractError("pre-render Concept identity is not canonical")
        return created


@dataclass(frozen=True)
class SealedConcept:
    source: PreRenderConcept
    descriptor: Mapping[str, Any]
    image_manifest: ArtifactManifest
    schema_version: int = 2
    kind: str = SEALED_CONCEPT_KIND
    concept_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != 2 or type(self.schema_version) is not int:
            raise ContractError("sealed Concept schema_version must be 2")
        if self.kind != SEALED_CONCEPT_KIND:
            raise ContractError("sealed Concept kind is invalid")
        if not isinstance(self.source, PreRenderConcept):
            raise ContractError("sealed Concept requires pre-render source")
        descriptor = copy_json_mapping(self.descriptor, "sealed Concept descriptor", nonempty=True)
        _validate_descriptor(descriptor, self.source.brief, sealed=True)
        if not isinstance(self.image_manifest, ArtifactManifest):
            raise ContractError("sealed Concept requires an image manifest")
        self.image_manifest.assert_valid()
        descriptor_paths = {entry["path"] for entry in _descriptor_entries(descriptor, "sealed Concept descriptor")}
        if {entry.path for entry in self.image_manifest.entries} != descriptor_paths:
            raise ContractError("sealed Concept image manifest roles are incomplete or extra")
        hashes = {entry.path: entry.sha256 for entry in self.image_manifest.entries}
        for entry in _descriptor_entries(descriptor, "sealed Concept descriptor"):
            if hashes[entry["path"]] != entry["sha256"]:
                raise ContractError("sealed Concept descriptor hash differs from image manifest")
        object.__setattr__(self, "descriptor", _freeze(dict(descriptor)))
        object.__setattr__(self, "concept_sha256", _sha256(self._identity_dict()))

    @property
    def provenance(self) -> ConceptProvenance:
        return self.source.provenance

    @property
    def root(self) -> Path:
        return self.source.root

    @property
    def brief(self) -> Mapping[str, Any]:
        return self.source.brief

    @property
    def research(self) -> Mapping[str, Any]:
        return self.source.research

    @property
    def drawing_instructions(self) -> Mapping[str, Any]:
        return self.source.drawing_instructions

    @property
    def derived_wish(self) -> DerivedWish:
        return self.source.derived_wish

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "source": self.source.to_dict(),
            "descriptor": _thaw(self.descriptor),
            "image_manifest": self.image_manifest.to_dict(),
        }

    def to_dict(self) -> dict[str, Any]:
        result = self._identity_dict()
        result["concept_sha256"] = self.concept_sha256
        return result

    def validate_tree(self) -> "SealedConcept":
        self.source.validate_tree()
        rebuilt = seal_pre_render_concept(self.source)
        if rebuilt.to_dict() != self.to_dict():
            raise ArtifactError("sealed Concept tree differs from its identity")
        return self

    @classmethod
    def from_mapping(cls, value: Any, *, root: Path) -> "SealedConcept":
        expected = {"schema_version", "kind", "source", "descriptor", "image_manifest", "concept_sha256"}
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("sealed Concept fields are invalid")
        source = PreRenderConcept.from_mapping(value["source"], root=root)
        created = cls(
            source=source,
            descriptor=value["descriptor"],
            image_manifest=artifact_manifest_from_mapping(value["image_manifest"]),
            schema_version=value["schema_version"],
            kind=value["kind"],
        )
        if dict(value) != created.to_dict():
            raise ContractError("sealed Concept identity is not canonical")
        return created


def load_pre_render_concept(
    run_root: Path,
    provenance: ConceptProvenance,
    *,
    created_at: str = "content-addressed",
) -> PreRenderConcept:
    root = Path(run_root).resolve(strict=True)
    relative = PurePosixPath("artifacts/concept/r%04d/concept" % provenance.round)
    concept_root = root.joinpath(*relative.parts)
    try:
        identity = concept_root.lstat()
    except OSError as exc:
        raise ArtifactError("pre-render Concept root is unavailable") from exc
    if concept_root.is_symlink() or not stat.S_ISDIR(identity.st_mode):
        raise ArtifactError("pre-render Concept root must be a real directory")
    documents: dict[str, dict[str, Any]] = {}
    entries: list[ArtifactEntry] = []
    for relative_path in SOURCE_PATHS:
        path = concept_root / relative_path
        document, content = _read_json(path, "Concept %s" % relative_path)
        documents[relative_path] = document
        entries.append(_entry(relative_path, content, path.lstat().st_mode))
    derived = DerivedWish.from_mapping(documents["derived_wish.json"])
    return PreRenderConcept(
        root=concept_root,
        provenance=provenance,
        source_manifest=_manifest(entries, created_at),
        brief=documents["brief.json"],
        research=documents["research.json"],
        drawing_instructions=documents["prompts.json"],
        descriptor=documents["descriptor.json"],
        derived_wish=derived,
    )


def _seal_descriptor(
    node: Any, root: Path, entries: list[ArtifactEntry]
) -> Any:
    if isinstance(node, Mapping) and set(node) == {"path"}:
        relative = _safe_relative(node["path"], "Concept image path")
        path = root.joinpath(*relative.parts)
        content = _read_regular(
            path,
            "Concept image %s" % relative.as_posix(),
            maximum=MAX_CONCEPT_IMAGE_BYTES,
        )
        entry = _entry(relative.as_posix(), content, path.lstat().st_mode)
        entries.append(entry)
        return {"path": entry.path, "sha256": entry.sha256}
    if isinstance(node, Mapping):
        return {key: _seal_descriptor(value, root, entries) for key, value in node.items()}
    raise ContractError("pre-render Concept descriptor is not a path-only tree")


def seal_pre_render_concept(source: PreRenderConcept) -> SealedConcept:
    """Return a sealed exact-byte value without writing or invoking an effect."""

    if not isinstance(source, PreRenderConcept):
        raise ContractError("Concept sealing requires pre-render source")
    source.validate_tree()
    entries: list[ArtifactEntry] = []
    descriptor = _seal_descriptor(source.descriptor, source.root, entries)
    return SealedConcept(
        source=source,
        descriptor=descriptor,
        image_manifest=_manifest(entries, source.source_manifest.created_at),
    )


__all__ = [
    "CONCEPT_ORIGINS",
    "CONCEPT_PROVENANCE_KIND",
    "MAX_CONCEPT_FILE_BYTES", "MAX_CONCEPT_IMAGE_BYTES",
    "PRE_RENDER_CONCEPT_KIND",
    "SEALED_CONCEPT_KIND",
    "ConceptExpectedContext",
    "ConceptProvenance",
    "PreRenderConcept",
    "SealedConcept",
    "load_pre_render_concept",
    "seal_pre_render_concept",
]
