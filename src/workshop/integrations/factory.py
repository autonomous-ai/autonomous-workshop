"""Credential-isolated Factory transport and explicit publication effects.

This module is the only authenticated Factory boundary. It builds a narrowed,
model-and-page handoff from exact sealed Make and Release bytes, records an
effect intent before network I/O, and accepts success only from authenticated
readback. Customer-page authorship is complete before this adapter runs.
"""

from __future__ import annotations

import hashlib
import io
import json
import mimetypes
import re
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional, Sequence, Tuple

from workshop._validation import require_sha256
from workshop.artifacts import (
    ArtifactManifest,
    assert_packable_content,
    build_artifact_manifest,
    build_pack,
    load_artifact_payload,
)
from workshop.errors import (
    AmbiguousEffectError,
    ContractError,
    EffectError,
    ReceiptError,
    StateConflict,
)
from workshop.make.cad.mesh import inspect_stl_path
from workshop.release.native import (
    DIRECT_RELEASE_PRODUCT_SCHEMA_VERSION,
    FACTORY_CONTENT_BODY_MAX,
    FACTORY_CONTENT_BODY_MIN,
    FACTORY_CONTENT_LABEL_MAX,
    FACTORY_CONTENT_STORY_BLOCKS_MAX,
    LEGACY_RELEASE_PRODUCT_SCHEMA_VERSION,
    MAX_NATIVE_RELEASE_MANUAL_BYTES,
    RELEASE_PRODUCT_SCHEMA_VERSION,
    validate_release_product,
)
from workshop.runtime import EffectIntent, EffectLedger, Receipt


DEFAULT_FACTORY_API = "https://panda-social-api.autonomous.ai/api/v1"
DEFAULT_FACTORY_PAGE_BASE = "https://www.autonomous.ai/factory/product"
DEFAULT_FACTORY_PROJECT_CDN_HOST = "cdn.autonomous.ai"
FACTORY_USER_AGENT = "Mozilla/5.0 (compatible; AutonomousWorkshop/1.0)"
HTTP_TIMEOUT_SECONDS = 120
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
FACTORY_IMPORT_STRING_LIMITS = {
    "title": 300,
    "description": 2_000,
}
FACTORY_RELEASE_PAGE_PATH = "workshop-release-page.json"
FACTORY_RELEASE_LEGACY_MANUAL_PATH = "MANUAL.md"
FACTORY_RELEASE_MANUAL_PATH = FACTORY_RELEASE_LEGACY_MANUAL_PATH
FACTORY_RELEASE_PDF_MANUAL_PATH = "MANUAL.pdf"
FACTORY_RELEASE_MANUAL_PATHS = frozenset(
    (FACTORY_RELEASE_LEGACY_MANUAL_PATH, FACTORY_RELEASE_PDF_MANUAL_PATH)
)
FACTORY_CONTENT_MAPPING = "workshop-release-v3-to-factory-content-v1"
# Factory assigns an omitted import category to its first active category.  The
# current authoritative taxonomy exposes ``toys`` for Toys & Games, so every
# Workshop product declares that stable slug explicitly. If Factory ever
# removes or deactivates it, import rejects before a draft is accepted instead
# of silently classifying a toy under a different first category.
FACTORY_TOY_CATEGORY_SLUG = "toys"
# Only these exact metadata files and CAD/project source types may cross the
# Factory boundary.  This is deliberately an allowlist: a creator-facing file
# must not become uploadable merely because its directory or suffix was not in
# a blacklist.
FACTORY_MODEL_METADATA_PATHS = frozenset(
    (
        "_inventor-artifact.json",
        FACTORY_RELEASE_LEGACY_MANUAL_PATH,
        FACTORY_RELEASE_PDF_MANUAL_PATH,
        "product.json",
        "project.json",
        FACTORY_RELEASE_PAGE_PATH,
        "workshop-product-facts.json",
    )
)
FACTORY_MODEL_GEOMETRY_SUFFIXES = frozenset(
    (
        ".3mf",
        ".brep",
        ".brp",
        ".dxf",
        ".fcstd",
        ".iges",
        ".igs",
        ".scad",
        ".step",
        ".stl",
        ".stp",
        ".x_b",
        ".x_t",
    )
)
FACTORY_MODEL_GENERATOR_SUFFIXES = frozenset((".py",))
FACTORY_FORBIDDEN_MEDIA_SUFFIXES = frozenset(
    (
        ".avi", ".avif", ".bmp", ".gif", ".heic", ".jpeg", ".jpg",
        ".m4v", ".mkv", ".mov", ".mp4", ".png", ".svg", ".tif",
        ".tiff", ".webm", ".webp",
    )
)
FACTORY_MADE_FORBIDDEN_PAGE_FIELDS = frozenset(
    ("attachments", "cinematic", "hero", "images", "story_blocks", "use_case")
)
PROVEN_NO_EFFECT_STATUSES = frozenset(
    (400, 401, 403, 404, 405, 406, 410, 411, 412, 413, 414, 415,
     416, 417, 421, 422, 426, 428, 431, 451)
)
# Factory's import contract additionally guarantees that an infrastructure
# 500 and its edge timeout 524 create no visible design.  Keep this scoped to
# import: the same statuses are not proof of no effect for content or publish.
FACTORY_IMPORT_PROVEN_NO_EFFECT_STATUSES = (
    PROVEN_NO_EFFECT_STATUSES | frozenset((500, 524))
)
_INVENTOR_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_OCCURRENCE_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("Factory values must be finite JSON") from exc


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _manual_path_for_release_product(product: Mapping[str, Any]) -> str:
    schema_version = product.get("schema_version")
    if schema_version == LEGACY_RELEASE_PRODUCT_SCHEMA_VERSION:
        return FACTORY_RELEASE_LEGACY_MANUAL_PATH
    if schema_version in (
        RELEASE_PRODUCT_SCHEMA_VERSION,
        DIRECT_RELEASE_PRODUCT_SCHEMA_VERSION,
    ):
        return FACTORY_RELEASE_PDF_MANUAL_PATH
    raise ContractError("Factory Release product schema has no manual binding")


def _https_url(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise ContractError("%s must be an absolute HTTPS URL" % label)
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError as exc:
        raise ContractError("%s must be an absolute HTTPS URL" % label) from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be an absolute HTTPS URL" % label)
    return value


def _factory_product_page_url(slug: Any) -> str:
    if not isinstance(slug, str) or not slug or len(slug) > 300:
        raise ReceiptError("Factory product page requires a canonical slug")
    return _https_url(
        DEFAULT_FACTORY_PAGE_BASE + "/" + urllib.parse.quote(slug, safe=""),
        "Factory product page URL",
    )


def _factory_project_file_url(project_url: Any, path: str) -> str:
    """Derive one immutable public file URL from authenticated Factory readback."""

    if path != FACTORY_RELEASE_PDF_MANUAL_PATH:
        raise ContractError("Factory project readback supports only MANUAL.pdf")
    value = _https_url(project_url, "Factory project URL")
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ContractError("Factory project URL is malformed") from exc
    decoded_path = urllib.parse.unquote(parsed.path)
    if (
        parsed.hostname.casefold() != DEFAULT_FACTORY_PROJECT_CDN_HOST
        or port is not None
        or parsed.query
        or parsed.fragment
        or not parsed.path.endswith("/")
        or "\\" in decoded_path
        or any(part in (".", "..") for part in decoded_path.split("/"))
    ):
        raise ReceiptError("Factory project URL is outside the pinned immutable CDN")
    return urllib.parse.urlunsplit(
        (
            "https",
            DEFAULT_FACTORY_PROJECT_CDN_HOST,
            parsed.path + FACTORY_RELEASE_PDF_MANUAL_PATH,
            "",
            "",
        )
    )


def _is_factory_model_path(
    path: str,
    *,
    primary_kind: str,
    primary_path: Optional[str] = None,
) -> bool:
    pure = PurePosixPath(path)
    if (
        pure.is_absolute()
        or pure.as_posix() != path
        or "\\" in path
        or any(part in ("", ".", "..") for part in pure.parts)
    ):
        return False
    if path in FACTORY_MODEL_METADATA_PATHS:
        return True
    lowered = path.casefold()
    if lowered.endswith(".step.json"):
        return True
    suffix = pure.suffix.casefold()
    return suffix in FACTORY_MODEL_GEOMETRY_SUFFIXES or (
        primary_kind == "generator"
        and path == primary_path
        and suffix in FACTORY_MODEL_GENERATOR_SUFFIXES
    )


def _read_json_file(path: Path, label: str) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ContractError("%s must be a sealed regular file" % label)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ContractError("%s is unreadable" % label) from exc
    if not content or len(content) > MAX_RESPONSE_BYTES:
        raise ContractError("%s is empty or exceeds the JSON limit" % label)
    try:
        value = json.loads(content.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ContractError("%s is malformed" % label) from exc
    if not isinstance(value, Mapping):
        raise ContractError("%s must be a JSON object" % label)
    return dict(value)


def _sealed_primary(context: Any) -> Mapping[str, str]:
    context.made.assert_current()
    root = Path(context.made.artifact_root).resolve(strict=True)
    product = _read_json_file(root / "product.json", "Made product.json")
    if _canonical_sha256(product) != _canonical_sha256(context.made.product):
        raise ContractError("Made product facts do not match sealed product.json")

    # Current native Make projects are bound to the Wish by the host checkpoint,
    # Made contract, and passing Playtest; they do not require the legacy
    # root-level project.json metadata file. Preserve compatibility with older
    # products by validating that file when it is present, without fabricating
    # it for a sealed native artifact.
    project_path = root / "project.json"
    if project_path.exists() or project_path.is_symlink():
        project = _read_json_file(project_path, "Made project.json")
        if project.get("id") != context.wish.product_id:
            raise ContractError("sealed project.json id must equal Wish product_id")

    assembled = root / "assembled.stl"
    canonical = root / (context.wish.product_id + ".stl")
    for path in (assembled, canonical):
        if path.is_symlink() or path.exists() and not path.is_file():
            raise ContractError("Factory primary STL must be a sealed regular file")
    if assembled.is_file() and canonical.is_file():
        if assembled.read_bytes() != canonical.read_bytes():
            raise ContractError("root primary STL files diverge")
    selected = assembled if assembled.is_file() else canonical if canonical.is_file() else None
    if selected is not None:
        content = selected.read_bytes()
        if not content:
            raise ContractError("Factory primary STL is empty")
        return {
            "kind": "mesh",
            "path": selected.name,
            "sha256": hashlib.sha256(content).hexdigest(),
        }

    generators = []
    for path in sorted(root.glob("*.py")):
        if path.is_symlink() or not path.is_file():
            raise ContractError("Factory generator must be a sealed regular file")
        content = path.read_bytes()
        if b"def gen_step" in content:
            generators.append((path, content))
    if len(generators) != 1:
        raise ContractError(
            "Made requires one root primary STL or one top-level gen_step generator"
        )
    path, content = generators[0]
    return {
        "kind": "generator",
        "path": path.name,
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _manifest_entry(manifest: ArtifactManifest, path: str):
    return next((entry for entry in manifest.entries if entry.path == path), None)


def _read_bound_file(root: Path, manifest: ArtifactManifest, path: str) -> bytes:
    entry = _manifest_entry(manifest, path)
    if entry is None:
        raise ContractError("Factory handoff references an unsealed file: %s" % path)
    source = root.joinpath(*PurePosixPath(path).parts)
    if source.is_symlink() or not source.is_file():
        raise ContractError("Factory handoff source is not a regular file: %s" % path)
    content = source.read_bytes()
    if len(content) != entry.bytes or hashlib.sha256(content).hexdigest() != entry.sha256:
        raise ContractError("Made file changed before Factory handoff: %s" % path)
    return content


def _inspect_shells(
    root: Path,
    manifest: ArtifactManifest,
    path: str,
    expected: int,
    label: str,
) -> None:
    entry = _manifest_entry(manifest, path)
    if entry is None:
        raise ContractError("Factory %s STL is not sealed" % label)
    try:
        result = inspect_stl_path(
            root.joinpath(*PurePosixPath(path).parts),
            expected_shell_count=expected,
            expected_source_sha256=entry.sha256,
            expected_source_bytes=entry.bytes,
        )
    except OSError as exc:
        raise ContractError("Factory %s STL could not be inspected" % label) from exc
    if result.status != "passed":
        reasons = tuple(result.failure_reasons) + tuple(result.hold_reasons)
        raise ContractError(
            "Factory %s STL shell count failed: expected=%d observed=%s reasons=%s"
            % (label, expected, result.observed_shell_count, ",".join(reasons) or "unknown")
        )


def _occurrence_transport(
    root: Path,
    manifest: ArtifactManifest,
    primary_source: str,
    transport_stem: str,
) -> Optional[Mapping[str, Any]]:
    candidates = (
        "assembled.step.json",
        PurePosixPath(primary_source).stem + ".step.json",
        transport_stem + ".step.json",
    )
    sidecars = [name for name in dict.fromkeys(candidates) if _manifest_entry(manifest, name)]
    if len(sidecars) > 1:
        raise ContractError("Factory handoff requires one occurrence sidecar")
    source_sidecar = sidecars[0] if sidecars else None
    if source_sidecar is None:
        return None
    source_step = source_sidecar[:-5]
    step_entry = _manifest_entry(manifest, source_step)
    if step_entry is None:
        raise ContractError("Factory occurrence sidecar requires its sealed STEP")

    try:
        sidecar: Any = json.loads(
            _read_bound_file(root, manifest, source_sidecar).decode("utf-8")
        )
    except (UnicodeError, ValueError) as exc:
        raise ContractError("Factory occurrence sidecar is malformed") from exc

    has_factory_sidecar = (
        isinstance(sidecar, Mapping)
        and sidecar.get("schemaVersion") == 1
        and sidecar.get("entryKind") == "assembly"
        and sidecar.get("primaryPose") == "assembled"
        and isinstance(sidecar.get("parts"), list)
        and bool(sidecar["parts"])
    )
    if not has_factory_sidecar:
        if not isinstance(sidecar, Mapping):
            raise ContractError("Factory occurrence sidecar is malformed")
        if {"schemaVersion", "entryKind", "primaryPose", "parts"} & set(sidecar):
            # A document that claims any part of Factory's schema must satisfy
            # all of it. Never silently repair a malformed transport contract.
            raise ContractError("Factory occurrence sidecar is malformed")
        if (
            sidecar.get("schema_version") != 1
            or sidecar.get("kind") != "native-cad.assembly-descriptor"
        ):
            # Make stages may own other required JSON documents at this
            # conventional path. They are product artifacts, not an implicit
            # request to expose a multipart transport to Factory.
            return None

        # Native Make may place a richer CAD assembly descriptor beside its
        # STEP. Translate only the exact, fully bound descriptor+inventory
        # shape into Factory's narrow sidecar. The descriptor owns occurrence
        # identity; product inventory owns the printable STL paths.
        product = _read_json_file(root / "product.json", "Made product.json")
        cad = product.get("cad")
        inventory = product.get("inventory")
        native_parts = (
            inventory.get("parts") if isinstance(inventory, Mapping) else None
        )
        native_names = sidecar.get("occurrences")
        occurrence_count = sidecar.get("occurrence_count")
        total_printed_parts = (
            inventory.get("total_printed_parts")
            if isinstance(inventory, Mapping)
            else None
        )
        if (
            sidecar.get("schema_version") != 1
            or not isinstance(cad, Mapping)
            or not isinstance(inventory, Mapping)
            or not isinstance(native_parts, list)
            or not native_parts
            or not isinstance(native_names, list)
            or not native_names
            or not isinstance(occurrence_count, int)
            or isinstance(occurrence_count, bool)
            or not isinstance(total_printed_parts, int)
            or isinstance(total_printed_parts, bool)
            or occurrence_count != len(native_names)
            or occurrence_count != len(native_parts)
            or occurrence_count != total_printed_parts
        ):
            raise ContractError("native Made assembly descriptor is malformed")

        def bound_reference(
            value: Any, label: str, expected_path: Optional[str] = None
        ) -> Tuple[str, int, str]:
            if not isinstance(value, Mapping):
                raise ContractError("%s is malformed" % label)
            path = value.get("path")
            declared_bytes = value.get("bytes")
            if not isinstance(path, str):
                raise ContractError("%s is malformed" % label)
            pure = PurePosixPath(path)
            entry = _manifest_entry(manifest, path)
            declared_sha256 = require_sha256(value.get("sha256"), label + " sha256")
            if (
                pure.is_absolute()
                or pure.as_posix() != path
                or any(item in ("", ".", "..") for item in pure.parts)
                or expected_path is not None
                and path != expected_path
                or entry is None
                or not isinstance(declared_bytes, int)
                or isinstance(declared_bytes, bool)
                or entry.bytes != declared_bytes
                or entry.sha256 != declared_sha256
            ):
                raise ContractError("%s is malformed" % label)
            _read_bound_file(root, manifest, path)
            return path, declared_bytes, declared_sha256

        descriptor_ref = bound_reference(
            cad.get("assembly_descriptor"),
            "Made assembly descriptor reference",
            source_sidecar,
        )
        sidecar_entry = _manifest_entry(manifest, source_sidecar)
        if sidecar_entry is None or descriptor_ref[1:] != (
            sidecar_entry.bytes,
            sidecar_entry.sha256,
        ):
            raise ContractError("Made assembly descriptor reference is malformed")
        assembly_ref = bound_reference(
            sidecar.get("assembly"), "native assembly STEP", source_step
        )
        if assembly_ref != bound_reference(
            cad.get("assembled_step"), "Made assembled STEP", source_step
        ):
            raise ContractError("native assembly STEP bindings differ")
        mesh_ref = bound_reference(
            sidecar.get("mesh"), "native assembly mesh", primary_source
        )
        if mesh_ref != bound_reference(
            cad.get("assembled_stl"), "Made assembled STL", primary_source
        ):
            raise ContractError("native assembly mesh bindings differ")

        derived_parts = []
        derived_names = set()
        source_paths = set()
        for native_name, native_part in zip(native_names, native_parts):
            if not isinstance(native_part, Mapping):
                raise ContractError("Made product inventory part is malformed")
            stl = native_part.get("stl")
            if (
                not isinstance(stl, Mapping)
                or native_part.get("quantity") != 1
                or isinstance(native_part.get("quantity"), bool)
                or not isinstance(native_name, str)
                or not _OCCURRENCE_NAME.fullmatch(native_name)
                or native_name in derived_names
            ):
                raise ContractError("Made product inventory part is malformed")
            source_path, _, _ = bound_reference(
                stl, "Made product inventory STL"
            )
            pure = PurePosixPath(source_path)
            if (
                pure.suffix.casefold() != ".stl"
                or source_path == primary_source
                or source_path in source_paths
            ):
                raise ContractError("Made product inventory STL is malformed")
            derived_names.add(native_name)
            source_paths.add(source_path)
            derived_parts.append({"name": native_name, "stlPath": source_path})
        sidecar = {
            "schemaVersion": 1,
            "entryKind": "assembly",
            "primaryPose": "assembled",
            "parts": derived_parts,
        }

    occurrences = []
    transported_parts = []
    names = set()
    parts_directory = transport_stem + "_parts"
    for order, part in enumerate(sidecar["parts"]):
        if not isinstance(part, Mapping):
            raise ContractError("Factory occurrence sidecar part is malformed")
        name = part.get("name")
        source_path = part.get("stlPath")
        if (
            not isinstance(name, str)
            or not _OCCURRENCE_NAME.fullmatch(name)
            or name in names
            or not isinstance(source_path, str)
        ):
            raise ContractError("Factory occurrence sidecar part is malformed")
        pure = PurePosixPath(source_path)
        if (
            pure.is_absolute()
            or pure.as_posix() != source_path
            or any(item in ("", ".", "..") for item in pure.parts)
            or pure.suffix.casefold() != ".stl"
            or source_path == primary_source
        ):
            raise ContractError("Factory occurrence STL path is unsafe")
        content = _read_bound_file(root, manifest, source_path)
        names.add(name)
        target = "%s/%s.stl" % (parts_directory, name)
        transported = dict(part)
        transported["stlPath"] = target
        transported_parts.append(transported)
        occurrences.append(
            {
                "order": order,
                "name": name,
                "mesh_name": name,
                "part": PurePosixPath(target).name,
                "source_path": source_path,
                "path": target,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    _inspect_shells(root, manifest, primary_source, len(occurrences), "assembly")
    inspected = set()
    for occurrence in occurrences:
        key = (occurrence["source_path"], occurrence["sha256"])
        if key not in inspected:
            _inspect_shells(root, manifest, occurrence["source_path"], 1, "production")
            inspected.add(key)
    transported_sidecar = dict(sidecar)
    transported_sidecar["parts"] = transported_parts
    sidecar_payload = _canonical_json(transported_sidecar) + b"\n"
    return {
        "source_step": source_step,
        "source_sidecar": source_sidecar,
        "step_path": transport_stem + ".step",
        "step_sha256": step_entry.sha256,
        "sidecar_path": transport_stem + ".step.json",
        "sidecar_payload": sidecar_payload,
        "sidecar_sha256": hashlib.sha256(sidecar_payload).hexdigest(),
        "parts_directory": parts_directory,
        "occurrences": tuple(occurrences),
    }


def _validated_occurrence_transport(
    root: Path,
    manifest: ArtifactManifest,
    primary_source: str,
    transport_stem: str,
) -> Optional[Mapping[str, Any]]:
    """Return only a complete, safe occurrence family.

    The sidecar is optional metadata. A malformed, stale, product-specific, or
    otherwise unbound document must not make the sealed root assembly
    unpublishable, nor may any paths from it enter the Factory handoff.
    """

    try:
        return _occurrence_transport(
            root,
            manifest,
            primary_source,
            transport_stem,
        )
    except ContractError:
        return None


def _assert_archive_inventory(content: bytes, project_id: str) -> None:
    """Mirror Factory's root visual and occurrence-family discovery contract."""

    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ContractError("Factory handoff contains duplicate archive paths")
            files = {name for name in names if not name.endswith("/")}
            geometry = {
                name
                for name in files
                if PurePosixPath(name).suffix.casefold()
                in FACTORY_MODEL_GEOMETRY_SUFFIXES
            }
            stls = {
                name
                for name in geometry
                if PurePosixPath(name).suffix.casefold() == ".stl"
            }
            root_visuals = {"assembled.stl", project_id + ".stl"} & stls
            if len(root_visuals) != 1:
                raise ContractError("Factory handoff requires one root primary STL")
            try:
                project = json.loads(archive.read("project.json").decode("utf-8"))
            except (KeyError, UnicodeError, ValueError) as exc:
                raise ContractError("Factory handoff project.json is malformed") from exc
            if (
                not isinstance(project, Mapping)
                or project.get("id") != project_id
                or not isinstance(project.get("name"), str)
                or not project["name"].strip()
            ):
                raise ContractError("Factory handoff project.json is malformed")
            primary_stem = PurePosixPath(next(iter(root_visuals))).stem
            parts_directory = primary_stem + "_parts"
            production = {name for name in stls if name.startswith(parts_directory + "/")}
            if len(stls) == 1:
                if production or geometry != root_visuals:
                    raise ContractError(
                        "single-part Factory handoff geometry is not exact"
                    )
                return
            step_name = primary_stem + ".step"
            sidecar_name = step_name + ".json"
            if not production or step_name not in files or sidecar_name not in files:
                raise ContractError("multipart Factory handoff lacks its occurrence family")
            try:
                sidecar = json.loads(archive.read(sidecar_name).decode("utf-8"))
            except (KeyError, UnicodeError, ValueError) as exc:
                raise ContractError("Factory handoff sidecar is malformed") from exc
            if (
                not isinstance(sidecar, Mapping)
                or sidecar.get("schemaVersion") != 1
                or sidecar.get("entryKind") != "assembly"
                or sidecar.get("primaryPose") != "assembled"
                or not isinstance(sidecar.get("parts"), list)
                or not sidecar["parts"]
            ):
                raise ContractError("Factory handoff sidecar is malformed")
            expected = set()
            occurrence_names = set()
            for item in sidecar["parts"]:
                if not isinstance(item, Mapping):
                    raise ContractError("Factory handoff occurrence is malformed")
                name = item.get("name")
                path = item.get("stlPath")
                canonical = "%s/%s.stl" % (parts_directory, name)
                if (
                    not isinstance(name, str)
                    or not _OCCURRENCE_NAME.fullmatch(name)
                    or name in occurrence_names
                    or path != canonical
                ):
                    raise ContractError("Factory handoff occurrence is malformed")
                occurrence_names.add(name)
                expected.add(canonical)
            expected_geometry = root_visuals | expected | {step_name}
            if (
                production != expected
                or stls != root_visuals | expected
                or geometry != expected_geometry
            ):
                raise ContractError("Factory handoff geometry inventory is not exact")
    except ContractError:
        raise
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError("Factory model handoff is not a readable ZIP") from exc


def _assert_factory_handoff(content: bytes) -> None:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ContractError("Factory model handoff contains duplicate paths")
            if any(name.endswith("/") for name in names):
                raise ContractError("Factory model handoff contains directory entries")
            try:
                facts = json.loads(
                    archive.read("workshop-product-facts.json").decode("utf-8")
                )
            except (KeyError, UnicodeError, ValueError) as exc:
                raise ContractError(
                    "Factory handoff product facts are malformed"
                ) from exc
            primary = facts.get("primary_model") if isinstance(facts, Mapping) else None
            if not isinstance(primary, Mapping):
                raise ContractError("Factory handoff primary model is malformed")
            primary_kind = primary.get("kind")
            primary_path = primary.get("path")
            if (
                primary_kind not in ("mesh", "generator")
                or not isinstance(primary_path, str)
                or not _is_factory_model_path(
                    primary_path,
                    primary_kind=primary_kind,
                    primary_path=primary_path,
                )
                or len(PurePosixPath(primary_path).parts) != 1
                or (
                    primary_kind == "mesh"
                    and PurePosixPath(primary_path).suffix.casefold() != ".stl"
                )
                or (
                    primary_kind == "generator"
                    and PurePosixPath(primary_path).suffix.casefold() != ".py"
                )
            ):
                raise ContractError("Factory handoff primary model is malformed")
            primary_sha256 = require_sha256(
                primary.get("sha256"), "Factory handoff primary model sha256"
            )
            try:
                primary_content = archive.read(primary_path)
            except KeyError as exc:
                raise ContractError("Factory handoff primary model is missing") from exc
            if hashlib.sha256(primary_content).hexdigest() != primary_sha256:
                raise ContractError("Factory handoff primary model hash differs")
            try:
                release_page_content = archive.read(FACTORY_RELEASE_PAGE_PATH)
                release_page = validate_release_product(
                    json.loads(release_page_content.decode("utf-8"))
                )
            except (KeyError, UnicodeError, ValueError) as exc:
                raise ContractError(
                    "Factory handoff Release product facts are malformed"
                ) from exc
            canonical_page = _canonical_json(release_page)
            if release_page_content != canonical_page:
                raise ContractError(
                    "Factory handoff Release product facts are not canonical"
                )
            manual_path = _manual_path_for_release_product(release_page)
            manual = facts.get("manual")
            if (
                not isinstance(manual, Mapping)
                or manual.get("path") != manual_path
            ):
                raise ContractError("Factory handoff manual binding is malformed")
            manual_sha256 = require_sha256(
                manual.get("sha256"), "Factory handoff manual sha256"
            )
            try:
                manual_content = archive.read(manual_path)
            except KeyError as exc:
                raise ContractError(
                    "Factory handoff %s is missing" % manual_path
                ) from exc
            if (
                not manual_content
                or hashlib.sha256(manual_content).hexdigest() != manual_sha256
            ):
                raise ContractError("Factory handoff %s hash differs" % manual_path)
            for name in names:
                if not _is_factory_model_path(
                    name,
                    primary_kind=primary_kind,
                    primary_path=primary_path,
                ):
                    raise ContractError(
                        "Factory model handoff contains non-model output: %s" % name
                    )
            if "product.json" in names:
                try:
                    product = json.loads(archive.read("product.json").decode("utf-8"))
                except (UnicodeError, ValueError) as exc:
                    raise ContractError("Factory handoff product.json is malformed") from exc
                if not isinstance(product, Mapping):
                    raise ContractError("Factory handoff product.json is malformed")
                forbidden = FACTORY_MADE_FORBIDDEN_PAGE_FIELDS & set(product)
                if forbidden:
                    raise ContractError(
                        "Factory handoff Made product.json contains Release page fields: %s"
                        % sorted(forbidden)
                    )
    except ContractError:
        raise
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        raise ContractError("Factory model handoff is not a readable ZIP") from exc


def _build_model_handoff(
    context: Any,
    destination: Path,
    facts: Mapping[str, Any],
    release_page_content: bytes,
    manual_content: bytes,
) -> Mapping[str, Any]:
    """Create the exact model-and-page ZIP that crosses Factory's boundary."""

    context.made.assert_current()
    root = Path(context.made.artifact_root).resolve(strict=True)
    manifest = context.made.artifact_manifest
    if not isinstance(manifest, ArtifactManifest):
        raise ContractError("Factory handoff requires a sealed Made manifest")
    current = build_artifact_manifest(root, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ContractError("Made bytes changed before Factory handoff")
    sealed_primary = _sealed_primary(context)
    primary_source = sealed_primary["path"]
    primary_sha256 = require_sha256(
        sealed_primary["sha256"], "Factory primary model sha256"
    )
    primary_entry = _manifest_entry(manifest, primary_source)
    if primary_entry is None or primary_entry.sha256 != primary_sha256:
        raise ContractError("Factory primary model is not sealed")

    # Keep assembled.stl at the root when Make provides it. Factory's importer
    # ranks that conventional name above all part meshes for the product viewer.
    transport_primary = primary_source
    occurrence = (
        _validated_occurrence_transport(
            root,
            manifest,
            primary_source,
            PurePosixPath(transport_primary).stem,
        )
        if sealed_primary["kind"] == "mesh"
        else None
    )

    primary_model = {
        "kind": sealed_primary["kind"],
        "path": transport_primary,
        "sha256": primary_sha256,
    }
    transport_facts = dict(facts)
    transport_facts["primary_model"] = primary_model
    if occurrence is not None:
        occurrences = occurrence["occurrences"]
        transport_facts["factory_assembly"] = {
            "schema_version": 1,
            "kind": "factory.occurrence-family",
            "step": {
                "path": occurrence["step_path"],
                "sha256": occurrence["step_sha256"],
            },
            "sidecar": {
                "path": occurrence["sidecar_path"],
                "sha256": occurrence["sidecar_sha256"],
            },
            "parts_directory": occurrence["parts_directory"],
            "occurrence_count": len(occurrences),
            "production_stls": [dict(value) for value in occurrences],
        }
    facts_payload = _canonical_json(transport_facts) + b"\n"
    assert_packable_content("workshop-product-facts.json", facts_payload)
    if not isinstance(release_page_content, bytes) or not release_page_content:
        raise ContractError("Factory handoff requires sealed Release page bytes")
    try:
        release_page = json.loads(release_page_content.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise ContractError("Factory handoff Release page bytes are malformed") from exc
    if _canonical_json(validate_release_product(release_page)) != release_page_content:
        raise ContractError("Factory handoff Release page bytes are not canonical")
    assert_packable_content(FACTORY_RELEASE_PAGE_PATH, release_page_content)
    manual_path = _manual_path_for_release_product(release_page)
    if not isinstance(manual_content, bytes) or not manual_content:
        raise ContractError("Factory handoff requires sealed %s bytes" % manual_path)
    manual_sha256 = hashlib.sha256(manual_content).hexdigest()
    manual_binding = facts.get("manual")
    if (
        not isinstance(manual_binding, Mapping)
        or manual_binding.get("path") != manual_path
        or manual_binding.get("sha256") != manual_sha256
    ):
        raise ContractError("Factory handoff manual facts are not exact")
    project_payload = _canonical_json(
        {"id": context.wish.product_id, "name": release_page["title"]}
    ) + b"\n"
    assert_packable_content("project.json", project_payload)
    if manual_path == FACTORY_RELEASE_LEGACY_MANUAL_PATH:
        try:
            manual_content.decode("utf-8")
        except UnicodeError as exc:
            raise ContractError("Factory handoff MANUAL.md must be UTF-8") from exc
    assert_packable_content(manual_path, manual_content)

    # STEP JSON is executable transport metadata from Factory's perspective.
    # Never copy an unvalidated document merely because Make emitted it beside
    # CAD. A validated occurrence family is rewritten below from safe paths.
    skip_paths = {
        entry.path
        for entry in manifest.entries
        if entry.path.casefold().endswith(".step.json")
    }
    if occurrence is not None:
        skip_paths.update(
            path for path in (
                occurrence["source_step"],
                occurrence["source_sidecar"],
                occurrence["step_path"],
                occurrence["sidecar_path"],
            )
            if path is not None
        )
    if sealed_primary["kind"] == "mesh":
        # Valid occurrence parts are rewritten below under their validated
        # names. Keep no alternate CAD, mesh, or slicer-project representation:
        # Factory's fallback estimator counts every such basename as another
        # printable part. Without an occurrence family this deliberately leaves
        # only the root primary STL; with one, the required assembly STEP and
        # declared production STLs are written explicitly below.
        skip_paths.update(
            entry.path
            for entry in manifest.entries
            if PurePosixPath(entry.path).suffix.casefold()
            in FACTORY_MODEL_GEOMETRY_SUFFIXES
            and entry.path != primary_source
        )
    with tempfile.TemporaryDirectory(prefix="workshop-factory-handoff-") as temporary:
        staging = Path(temporary)
        for entry in manifest.entries:
            # Native Make may carry an engineering manual, but Factory must
            # receive the exact customer-facing manual sealed by Release.
            # Factory also requires root project.json for discovery, so the
            # boundary writes one deterministically from sealed Wish+Release.
            if entry.path in FACTORY_RELEASE_MANUAL_PATHS or entry.path == "project.json":
                continue
            if (
                not _is_factory_model_path(
                    entry.path,
                    primary_kind=sealed_primary["kind"],
                    primary_path=primary_source,
                )
                or entry.path in skip_paths
            ):
                continue
            content = _read_bound_file(root, manifest, entry.path)
            relative = PurePosixPath(entry.path)
            if transport_primary != primary_source and entry.path == primary_source:
                continue
            target = staging.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            target.chmod(0o755 if entry.executable else 0o644)
        if transport_primary != primary_source and not (staging / transport_primary).exists():
            target = staging / transport_primary
            target.write_bytes(_read_bound_file(root, manifest, primary_source))
            target.chmod(0o644)
        if occurrence is not None:
            (staging / occurrence["step_path"]).write_bytes(
                _read_bound_file(root, manifest, occurrence["source_step"])
            )
            (staging / occurrence["sidecar_path"]).write_bytes(
                occurrence["sidecar_payload"]
            )
            for item in occurrence["occurrences"]:
                target = staging.joinpath(*PurePosixPath(item["path"]).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(_read_bound_file(root, manifest, item["source_path"]))
                target.chmod(0o644)
        reserved = (
            "workshop-product-facts.json",
            FACTORY_RELEASE_PAGE_PATH,
            FACTORY_RELEASE_LEGACY_MANUAL_PATH,
            FACTORY_RELEASE_PDF_MANUAL_PATH,
            "project.json",
        )
        if any((staging / path).exists() for path in reserved):
            raise ContractError("Made contains a reserved Factory handoff path")
        (staging / "workshop-product-facts.json").write_bytes(facts_payload)
        (staging / FACTORY_RELEASE_PAGE_PATH).write_bytes(release_page_content)
        (staging / manual_path).write_bytes(manual_content)
        (staging / "project.json").write_bytes(project_payload)
        result = dict(build_pack(staging, destination))
    content, pack_sha256, handoff_artifact_sha256 = load_artifact_payload(destination)
    if (
        result.get("pack_sha256") != pack_sha256
        or result.get("artifact_sha256") != handoff_artifact_sha256
    ):
        raise ContractError("Factory handoff Pack changed after construction")
    _assert_factory_handoff(content)
    if sealed_primary["kind"] == "mesh":
        _assert_archive_inventory(content, context.wish.product_id)
    result.update(
        {
            "content": content,
            "primary_model": primary_model,
            "product_facts_sha256": hashlib.sha256(facts_payload).hexdigest(),
            "product_page_sha256": hashlib.sha256(
                release_page_content
            ).hexdigest(),
            "manual_path": manual_path,
            "manual_sha256": manual_sha256,
        }
    )
    return result


@dataclass(frozen=True)
class HttpResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def __post_init__(self) -> None:
        if type(self.status) is not int or not 100 <= self.status <= 599:
            raise ContractError("HTTP response status must be from 100 to 599")
        if not isinstance(self.headers, Mapping) or not isinstance(self.body, bytes):
            raise ContractError("HTTP response headers/body are malformed")
        if len(self.body) > MAX_RESPONSE_BYTES:
            raise EffectError("Factory response exceeds the 2 MB safety limit")


Transport = Callable[
    [str, str, Mapping[str, str], Optional[bytes], int], HttpResponse
]


@dataclass(frozen=True)
class FactoryProjectFileResponse:
    """Bounded response for one immutable public Factory project file."""

    status: int
    headers: Mapping[str, str]
    body: bytes

    def __post_init__(self) -> None:
        if type(self.status) is not int or not 100 <= self.status <= 599:
            raise ContractError(
                "Factory project response status must be from 100 to 599"
            )
        if not isinstance(self.headers, Mapping) or not isinstance(self.body, bytes):
            raise ContractError("Factory project response headers/body are malformed")
        if len(self.body) > MAX_NATIVE_RELEASE_MANUAL_BYTES:
            raise EffectError("Factory project file exceeds the Release manual limit")


ProjectFileTransport = Callable[
    [str, str, Mapping[str, str], Optional[bytes], int], FactoryProjectFileResponse
]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def urllib_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: Optional[bytes],
    timeout: int,
) -> HttpResponse:
    request = urllib.request.Request(url, method=method, data=body)
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            content = response.read(MAX_RESPONSE_BYTES + 1)
            if len(content) > MAX_RESPONSE_BYTES:
                raise EffectError("Factory response exceeds the 2 MB safety limit")
            return HttpResponse(response.status, dict(response.headers), content)
    except urllib.error.HTTPError as exc:
        content = exc.read(MAX_RESPONSE_BYTES + 1)
        if len(content) > MAX_RESPONSE_BYTES:
            raise EffectError("Factory error response exceeds the limit")
        return HttpResponse(exc.code, dict(exc.headers or {}), content)


def urllib_project_file_transport(
    method: str,
    url: str,
    headers: Mapping[str, str],
    body: Optional[bytes],
    timeout: int,
) -> FactoryProjectFileResponse:
    """Read one public immutable project file without following redirects."""

    if method != "GET" or body is not None:
        raise ContractError("Factory project-file transport is read-only")
    request = urllib.request.Request(url, method=method)
    for name, value in headers.items():
        request.add_header(name, value)
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            content = response.read(MAX_NATIVE_RELEASE_MANUAL_BYTES + 1)
            if len(content) > MAX_NATIVE_RELEASE_MANUAL_BYTES:
                raise EffectError("Factory project file exceeds the Release manual limit")
            return FactoryProjectFileResponse(
                response.status, dict(response.headers), content
            )
    except urllib.error.HTTPError as exc:
        content = exc.read(MAX_NATIVE_RELEASE_MANUAL_BYTES + 1)
        if len(content) > MAX_NATIVE_RELEASE_MANUAL_BYTES:
            raise EffectError("Factory project error response exceeds the limit")
        return FactoryProjectFileResponse(
            exc.code, dict(exc.headers or {}), content
        )


def _json_body(response: HttpResponse, label: str = "Factory response") -> Mapping[str, Any]:
    def reject_duplicates(pairs):  # type: ignore[no-untyped-def]
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("duplicate key")
            value[key] = item
        return value

    try:
        value = json.loads(
            response.body.decode("utf-8"), object_pairs_hook=reject_duplicates
        )
    except (UnicodeError, ValueError) as exc:
        raise EffectError("%s is not valid JSON" % label) from exc
    if not isinstance(value, Mapping):
        raise EffectError("%s must be a JSON object" % label)
    return dict(value)


def _api_origin(value: str) -> str:
    try:
        parsed = urllib.parse.urlsplit(value)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ContractError("Factory API base is malformed") from exc
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise ContractError("Factory API base must be a credential-free HTTPS path")
    return "https://%s%s" % (
        parsed.hostname.casefold(),
        ":%d" % port if port else "",
    )


def _safe_filename(filename: str) -> str:
    if (
        not isinstance(filename, str)
        or not filename
        or len(filename) > 255
        or PurePosixPath(filename).name != filename
        or any(ord(character) < 32 or ord(character) == 127 for character in filename)
    ):
        raise ContractError("Factory upload filename must be one safe basename")
    assert_packable_content(filename, b"")
    return filename


def _multipart(
    fields: Sequence[Tuple[str, str]],
    files: Sequence[Tuple[str, str, str, bytes]],
) -> Tuple[bytes, str]:
    boundary = "autonomous-workshop-%s" % uuid.uuid4().hex
    buffer = io.BytesIO()
    marker = ("--%s\r\n" % boundary).encode("ascii")
    for name, value in fields:
        buffer.write(marker)
        buffer.write(
            ('Content-Disposition: form-data; name="%s"\r\n\r\n' % name).encode("utf-8")
        )
        buffer.write(value.encode("utf-8"))
        buffer.write(b"\r\n")
    for name, filename, content_type, content in files:
        buffer.write(marker)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", filename)
        buffer.write(
            (
                'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
                % (name, safe_name)
            ).encode("utf-8")
        )
        buffer.write(("Content-Type: %s\r\n\r\n" % content_type).encode("ascii"))
        buffer.write(content)
        buffer.write(b"\r\n")
    buffer.write(("--%s--\r\n" % boundary).encode("ascii"))
    return buffer.getvalue(), "multipart/form-data; boundary=%s" % boundary


def _normalize_import(metadata: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(metadata, Mapping):
        raise ContractError("Factory import metadata must be an object")
    allowed = {"status", "title", "description", "category", "tags"}
    if set(metadata) - allowed:
        raise ContractError("Factory import metadata contains unknown fields")
    normalized: Dict[str, Any] = {"status": metadata.get("status", "draft")}
    if normalized["status"] != "draft":
        raise ContractError("Factory model import must create a private draft")
    for name, maximum in FACTORY_IMPORT_STRING_LIMITS.items():
        value = metadata.get(name)
        if (
            not isinstance(value, str)
            or not value
            or value != value.strip()
            or len(value) > maximum
        ):
            raise ContractError("Factory import %s is malformed" % name)
        normalized[name] = value
    category = metadata.get("category")
    if category is not None:
        if (
            not isinstance(category, str)
            or not category
            or category != category.strip()
            or len(category) > 100
        ):
            raise ContractError("Factory import category is malformed")
        normalized["category"] = category
    tags = metadata.get("tags")
    if (
        not isinstance(tags, list)
        or len(tags) > 10
        or any(
            not isinstance(tag, str)
            or not tag
            or tag != tag.strip()
            or len(tag) > 40
            for tag in tags
        )
        or len(tags) != len({tag.casefold() for tag in tags})
    ):
        raise ContractError("Factory tags must be unique bounded strings")
    normalized["tags"] = list(tags)
    return normalized


class FactoryClient:
    """Bounded same-origin client using a session-managed bearer transport."""

    def __init__(
        self,
        transport: Transport,
        *,
        api_base: str = DEFAULT_FACTORY_API,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
    ) -> None:
        if not callable(transport):
            raise ContractError("Factory client transport must be callable")
        if _api_origin(api_base) != _api_origin(DEFAULT_FACTORY_API):
            raise ContractError("Factory client API origin is not pinned")
        expected_path = urllib.parse.urlsplit(DEFAULT_FACTORY_API).path.rstrip("/")
        if urllib.parse.urlsplit(api_base).path.rstrip("/") != expected_path:
            raise ContractError("Factory client API path is not pinned")
        if type(timeout_seconds) is not int or timeout_seconds <= 0:
            raise ContractError("Factory timeout must be a positive integer")
        self.api_base = api_base.rstrip("/")
        self.transport = transport
        self.timeout_seconds = timeout_seconds

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[bytes] = None,
        content_type: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> HttpResponse:
        headers = {"Accept": "application/json", "User-Agent": FACTORY_USER_AGENT}
        if content_type is not None:
            headers["Content-Type"] = content_type
        if idempotency_key is not None:
            if not isinstance(idempotency_key, str) or not idempotency_key:
                raise ContractError("Factory idempotency key is malformed")
            headers["Idempotency-Key"] = idempotency_key
        return self.transport(
            method,
            self.api_base + path,
            headers,
            body,
            self.timeout_seconds,
        )

    def import_model(
        self,
        *,
        filename: str,
        content: bytes,
        metadata: Mapping[str, Any],
        idempotency_key: str,
    ) -> HttpResponse:
        filename = _safe_filename(filename)
        if not isinstance(content, bytes) or not content:
            raise ContractError("Factory model ZIP must be non-empty bytes")
        _assert_factory_handoff(content)
        normalized = _normalize_import(metadata)
        fields = [("status", "draft")]
        for name in ("title", "description", "category"):
            if name in normalized:
                fields.append((name, normalized[name]))
        for tag in normalized["tags"] or ("",):
            fields.append(("tags", tag))
        content_type = mimetypes.guess_type(filename)[0] or "application/zip"
        body, multipart_type = _multipart(
            fields, (("file", filename, content_type, content),)
        )
        return self._request(
            "POST",
            "/designs/import",
            body=body,
            content_type=multipart_type,
            idempotency_key=idempotency_key,
        )

    def get_design(self, slug: str) -> HttpResponse:
        if not isinstance(slug, str) or not slug:
            raise ContractError("Factory design slug is required")
        return self._request(
            "GET", "/designs/%s" % urllib.parse.quote(slug, safe="")
        )

    def write_use_case(
        self,
        slug: str,
        content: Mapping[str, Any],
        idempotency_key: str,
    ) -> HttpResponse:
        if not isinstance(slug, str) or not slug:
            raise ContractError("Factory design slug is required")
        if not isinstance(content, Mapping) or set(content) != {
            "label",
            "body",
            "image",
        }:
            raise ContractError("Factory use_case write must be exact")
        return self._request(
            "PATCH",
            "/designs/%s/use-case" % urllib.parse.quote(slug, safe=""),
            body=_canonical_json(dict(content)),
            content_type="application/json",
            idempotency_key=idempotency_key,
        )

    def write_story_blocks(
        self,
        slug: str,
        blocks: Sequence[Mapping[str, Any]],
        idempotency_key: str,
    ) -> HttpResponse:
        if not isinstance(slug, str) or not slug:
            raise ContractError("Factory design slug is required")
        if not isinstance(blocks, (list, tuple)):
            raise ContractError("Factory story_blocks write must be an array")
        return self._request(
            "PUT",
            "/designs/%s/story-blocks" % urllib.parse.quote(slug, safe=""),
            body=_canonical_json({"story_blocks": [dict(block) for block in blocks]}),
            content_type="application/json",
            idempotency_key=idempotency_key,
        )

    def publish(self, slug: str, idempotency_key: str) -> HttpResponse:
        if not isinstance(slug, str) or not slug:
            raise ContractError("Factory design slug is required")
        return self._request(
            "POST",
            "/designs/%s/publish" % urllib.parse.quote(slug, safe=""),
            idempotency_key=idempotency_key,
        )


class FactoryAuthenticationError(EffectError):
    """Factory could not establish an authenticated agent session."""


class FactoryCredentialRejected(FactoryAuthenticationError):
    """Factory rejected a rotated or disabled credential."""


def _secret_text(value: Any, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s is missing or malformed" % label)
    return value


@dataclass(frozen=True, repr=False)
class FactoryAgentCredentials:
    username: str
    password: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "username", _secret_text(self.username, "Factory username", 512))
        object.__setattr__(self, "password", _secret_text(self.password, "Factory password", 4096))

    def __repr__(self) -> str:
        return "FactoryAgentCredentials(username=<redacted>, password=<redacted>)"


def factory_credentials_from_environment(
    environ: Mapping[str, str],
) -> FactoryAgentCredentials:
    """Create the host-owned Workshop service-account credential.

    Factory authentication is independent of the Inventor selected for a
    product run. Inventor provenance is carried by the sealed Release facts;
    authenticated effect ownership is bound separately through Factory's
    returned owner id and the durable receipts.
    """

    if not isinstance(environ, Mapping):
        raise ContractError("Factory credential environment must be a mapping")
    username = environ.get("FACTORY_USERNAME")
    password = environ.get("FACTORY_PASSWORD")
    if username is None and password is None:
        raise ContractError("Factory agent credentials are not configured")
    if not isinstance(username, str) or not isinstance(password, str):
        raise ContractError("Factory username/password must be configured together")
    return FactoryAgentCredentials(username, password)


@dataclass(frozen=True)
class FactoryAgentIdentity:
    owner_id: str
    username: str
    expires_in: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "owner_id", _secret_text(self.owner_id, "Factory owner id", 512))
        object.__setattr__(self, "username", _secret_text(self.username, "Factory account", 512))
        if type(self.expires_in) is not int or not 0 < self.expires_in <= 400 * 24 * 60 * 60:
            raise ContractError("Factory token expiry is malformed")


Sleeper = Callable[[float], None]


class FactoryAgentSession:
    """Mint and cache an in-memory bearer with one bounded 401 refresh."""

    def __init__(
        self,
        credentials: FactoryAgentCredentials,
        *,
        api_base: str = DEFAULT_FACTORY_API,
        transport: Transport = urllib_transport,
        project_file_transport: Optional[ProjectFileTransport] = None,
        timeout_seconds: int = HTTP_TIMEOUT_SECONDS,
        sleeper: Sleeper = time.sleep,
        max_login_rate_retries: int = 2,
    ) -> None:
        if not isinstance(credentials, FactoryAgentCredentials):
            raise ContractError("FactoryAgentSession requires typed credentials")
        if _api_origin(api_base) != _api_origin(DEFAULT_FACTORY_API):
            raise ContractError("Factory agent API origin is not pinned")
        if urllib.parse.urlsplit(api_base).path.rstrip("/") != urllib.parse.urlsplit(DEFAULT_FACTORY_API).path.rstrip("/"):
            raise ContractError("Factory agent API path is not pinned")
        if (
            not callable(transport)
            or not callable(sleeper)
            or (
                project_file_transport is not None
                and not callable(project_file_transport)
            )
        ):
            raise ContractError("Factory session transport/sleeper must be callable")
        if (
            type(timeout_seconds) is not int
            or timeout_seconds <= 0
            or type(max_login_rate_retries) is not int
            or not 0 <= max_login_rate_retries <= 5
        ):
            raise ContractError("Factory session retry configuration is malformed")
        self._credentials = credentials
        self._api_base = api_base.rstrip("/")
        self._api_origin = _api_origin(api_base)
        self._transport = transport
        if project_file_transport is not None:
            self._project_file_transport = project_file_transport
        elif transport is urllib_transport:
            self._project_file_transport = urllib_project_file_transport
        else:
            # Deterministic fakes and caller-owned transports keep one injected
            # network seam. The response is independently widened only up to
            # the already accepted Release-manual byte limit.
            def adapted_project_transport(
                method: str,
                url: str,
                headers: Mapping[str, str],
                body: Optional[bytes],
                timeout: int,
            ) -> FactoryProjectFileResponse:
                response = transport(method, url, headers, body, timeout)
                return FactoryProjectFileResponse(
                    response.status, response.headers, response.body
                )

            self._project_file_transport = adapted_project_transport
        self._timeout_seconds = timeout_seconds
        self._sleeper = sleeper
        self._max_login_rate_retries = max_login_rate_retries
        self._access_token: Optional[str] = None
        self._identity: Optional[FactoryAgentIdentity] = None

    def __repr__(self) -> str:
        return "FactoryAgentSession(authenticated=%s)" % (
            "true" if self._access_token is not None else "false"
        )

    @staticmethod
    def _retry_after(response: HttpResponse) -> float:
        raw = next(
            (
                value for name, value in response.headers.items()
                if isinstance(name, str) and name.casefold() == "retry-after"
            ),
            None,
        )
        try:
            delay = float(raw) if raw is not None else 0.0
        except (TypeError, ValueError):
            delay = 0.0
        if not 0.0 <= delay <= 60.0:
            raise FactoryAuthenticationError("Factory supplied an unsafe Retry-After")
        return delay

    @staticmethod
    def _login_value(response: HttpResponse) -> Tuple[str, FactoryAgentIdentity]:
        try:
            value = _json_body(response, "Factory login response")
            token = _secret_text(value.get("access_token"), "Factory access token", 16_384)
            if value.get("token_type") != "Bearer":
                raise ContractError("Factory token type is malformed")
            user = value.get("user")
            if not isinstance(user, Mapping):
                raise ContractError("Factory login user is malformed")
            identity = FactoryAgentIdentity(
                user.get("id"), user.get("username"), value.get("expires_in")
            )
        except (ContractError, EffectError) as exc:
            raise FactoryAuthenticationError("Factory login response was malformed") from exc
        return token, identity

    def login(self, *, force: bool = False) -> FactoryAgentIdentity:
        if not force and self._access_token is not None and self._identity is not None:
            return self._identity
        body = _canonical_json(
            {"username": self._credentials.username, "password": self._credentials.password}
        )
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": FACTORY_USER_AGENT,
        }
        for attempt in range(self._max_login_rate_retries + 1):
            response = self._transport(
                "POST",
                self._api_base + "/auth/agent/login",
                headers,
                body,
                self._timeout_seconds,
            )
            if response.status == 429 and attempt < self._max_login_rate_retries:
                self._sleeper(self._retry_after(response))
                continue
            if response.status == 401:
                self._access_token = None
                self._identity = None
                raise FactoryCredentialRejected(
                    "Factory rejected the agent credential; rotate or re-issue it"
                )
            if response.status != 200:
                self._access_token = None
                self._identity = None
                raise FactoryAuthenticationError(
                    "Factory agent login returned HTTP %s" % response.status
                )
            token, identity = self._login_value(response)
            if identity.username.casefold() != self._credentials.username.casefold():
                self._access_token = None
                self._identity = None
                raise FactoryCredentialRejected(
                    "Factory login identity did not match the configured "
                    "Workshop service account"
                )
            self._access_token = token
            self._identity = identity
            return identity
        raise FactoryAuthenticationError("Factory agent login remained rate limited")

    def authenticated_transport(
        self,
        method: str,
        url: str,
        headers: Mapping[str, str],
        body: Optional[bytes],
        timeout: int,
    ) -> HttpResponse:
        if _api_origin(url) != self._api_origin:
            raise ContractError("Factory bearer cannot be sent to another origin")
        self.login()
        assert self._access_token is not None

        def send() -> HttpResponse:
            safe: MutableMapping[str, str] = {
                name: value
                for name, value in headers.items()
                if isinstance(name, str) and name.casefold() != "authorization"
            }
            safe["Authorization"] = "Bearer %s" % self._access_token
            return self._transport(method, url, safe, body, timeout)

        response = send()
        if response.status != 401:
            return response
        self._access_token = None
        self._identity = None
        self.login(force=True)
        return send()

    def verify_pdf_manual(
        self, project_url: Any, expected_sha256: Any
    ) -> Mapping[str, str]:
        """Hash-verify the exact public CDN manual without sending a bearer."""

        expected = require_sha256(
            expected_sha256, "Factory expected manual sha256"
        )
        manual_url = _factory_project_file_url(
            project_url, FACTORY_RELEASE_PDF_MANUAL_PATH
        )
        try:
            response = self._project_file_transport(
                "GET",
                manual_url,
                {"Accept": "application/pdf", "User-Agent": FACTORY_USER_AGENT},
                None,
                self._timeout_seconds,
            )
        except (ContractError, EffectError):
            raise
        except Exception as exc:
            raise AmbiguousEffectError(
                "Factory MANUAL.pdf readback is unavailable"
            ) from exc
        response = FactoryProjectFileResponse(
            response.status, response.headers, response.body
        )
        if response.status != 200:
            raise AmbiguousEffectError(
                "Factory MANUAL.pdf readback returned HTTP %s" % response.status
            )
        observed = hashlib.sha256(response.body).hexdigest()
        if not response.body or observed != expected:
            raise ReceiptError(
                "Factory MANUAL.pdf readback differs from the sealed Release"
            )
        return {
            "manual_url": manual_url,
            "manual_readback_sha256": observed,
        }


def _assert_sealed_release(root: Path, manifest: ArtifactManifest) -> Path:
    requested = Path(root)
    if (
        not requested.is_absolute()
        or requested.is_symlink()
        or not requested.is_dir()
        or not isinstance(manifest, ArtifactManifest)
    ):
        raise ContractError("Factory Release requires an absolute sealed directory")
    resolved = requested.resolve(strict=True)
    current = build_artifact_manifest(resolved, created_at=manifest.created_at)
    if current.to_dict() != manifest.to_dict():
        raise ContractError("Release bytes changed after they were sealed")
    forbidden = [
        entry.path
        for entry in manifest.entries
        if PurePosixPath(entry.path).suffix.casefold() in FACTORY_FORBIDDEN_MEDIA_SUFFIXES
    ]
    if forbidden:
        raise ContractError("Release cannot contain creator page media: %s" % forbidden)
    return resolved


def _release_page(root: Path) -> Tuple[Mapping[str, Any], bytes]:
    path = root / "product.json"
    if path.is_symlink() or not path.is_file():
        raise ContractError("Release product.json must be a sealed regular file")
    try:
        content = path.read_bytes()
        raw = json.loads(content.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ContractError("Release product.json is malformed") from exc
    page = validate_release_product(raw)
    if _canonical_json(page) != content:
        raise ContractError("Release product.json must use canonical JSON encoding")
    return page, content


def _release_manual(
    root: Path,
    manifest: ArtifactManifest,
    release_product: Mapping[str, Any],
) -> Tuple[bytes, str, str]:
    manual_path = _manual_path_for_release_product(release_product)
    path = root / manual_path
    entry = _manifest_entry(manifest, manual_path)
    if entry is None or path.is_symlink() or not path.is_file():
        raise ContractError("Release %s must be a sealed regular file" % manual_path)
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise ContractError("Release %s must be readable" % manual_path) from exc
    if manual_path == FACTORY_RELEASE_LEGACY_MANUAL_PATH:
        try:
            content.decode("utf-8")
        except UnicodeError as exc:
            raise ContractError("Release MANUAL.md must be readable UTF-8") from exc
    digest = hashlib.sha256(content).hexdigest()
    if not content or len(content) != entry.bytes or digest != entry.sha256:
        raise ContractError("Release %s differs from its sealed bytes" % manual_path)
    return content, digest, manual_path


def _factory_content_text(
    value: Any,
    label: str,
    *,
    minimum: int,
    maximum: int,
) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not minimum <= len(value) <= maximum
        or "<" in value
        or ">" in value
    ):
        raise ContractError(
            "Factory rich-content API cannot carry exact %s; required plain-text "
            "length is %d-%d characters" % (label, minimum, maximum)
        )
    return value


def _factory_content_copy(page: Mapping[str, Any]) -> Mapping[str, Any]:
    """Project only fields Factory can represent without rewriting Codex copy."""

    use_case = page.get("use_case")
    story_blocks = page.get("story_blocks")
    if not isinstance(use_case, Mapping) or not isinstance(story_blocks, list):
        raise ContractError("Release page lacks exact use_case/story_blocks content")
    if len(story_blocks) > FACTORY_CONTENT_STORY_BLOCKS_MAX:
        raise ContractError(
            "Factory rich-content API cannot carry exact story_blocks; at most %d "
            "blocks are supported" % FACTORY_CONTENT_STORY_BLOCKS_MAX
        )
    copied_blocks = []
    for index, block in enumerate(story_blocks):
        if not isinstance(block, Mapping):
            raise ContractError("Release story_blocks[%d] is malformed" % index)
        copied_blocks.append(
            {
                "lead": _factory_content_text(
                    block.get("headline"),
                    "story_blocks[%d].headline" % index,
                    minimum=1,
                    maximum=FACTORY_CONTENT_LABEL_MAX,
                ),
                "body": _factory_content_text(
                    block.get("body"),
                    "story_blocks[%d].body" % index,
                    minimum=FACTORY_CONTENT_BODY_MIN,
                    maximum=FACTORY_CONTENT_BODY_MAX,
                ),
            }
        )
    return {
        "use_case": {
            "label": _factory_content_text(
                use_case.get("headline"),
                "use_case.headline",
                minimum=1,
                maximum=FACTORY_CONTENT_LABEL_MAX,
            ),
            "body": _factory_content_text(
                use_case.get("body"),
                "use_case.body",
                minimum=FACTORY_CONTENT_BODY_MIN,
                maximum=FACTORY_CONTENT_BODY_MAX,
            ),
        },
        "story_blocks": copied_blocks,
    }


def _factory_content_target(
    page: Mapping[str, Any], cover_url: str
) -> Mapping[str, Any]:
    copied = _factory_content_copy(page)
    use_case = dict(copied["use_case"])
    use_case["image"] = _https_url(cover_url, "Factory use_case cover URL")
    return {
        "use_case": use_case,
        "story_blocks": [dict(block) for block in copied["story_blocks"]],
    }


def _factory_content_state(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or not {
        "use_case",
        "story_blocks",
    }.issubset(value):
        raise ReceiptError(
            "Factory readback does not expose use_case and story_blocks"
        )
    use_case = value.get("use_case")
    blocks = value.get("story_blocks")
    if use_case is not None and not isinstance(use_case, Mapping):
        raise ReceiptError("Factory use_case readback is malformed")
    if not isinstance(blocks, list) or any(
        not isinstance(block, Mapping) for block in blocks
    ):
        raise ReceiptError("Factory story_blocks readback is malformed")
    return {
        "use_case": dict(use_case) if use_case is not None else None,
        "story_blocks": [dict(block) for block in blocks],
    }


def _effect_details(intent: EffectIntent, values: Mapping[str, Any]) -> Mapping[str, Any]:
    return {
        **dict(values),
        "product_id": intent.product_id,
        "effect_request_sha256": intent.request_sha256,
        "effect_idempotency_key": intent.idempotency_key,
        "release_sha256": intent.release_sha256,
        "playtest_evidence_sha256": intent.playtest_evidence_sha256,
        "handoff_artifact_sha256": intent.handoff_artifact_sha256,
    }


def _same_factory_identity(left: Receipt, right: Receipt) -> bool:
    return all(
        getattr(left, name) == getattr(right, name)
        for name in (
            "design_id",
            "slug",
            "owner_id",
            "root_id",
            "current_history_id",
            "project_url",
        )
    )


def _factory_receipt(
    design: Mapping[str, Any],
    intent: EffectIntent,
    details: Mapping[str, Any],
) -> Receipt:
    return Receipt.from_factory_design(
        design,
        payload_sha256=intent.pack_sha256,
        artifact_sha256=intent.product_artifact_sha256,
        details=_effect_details(intent, details),
    )


class FactoryReleaseWriter:
    """Import one exact sealed handoff as an authenticated private draft."""

    def __init__(
        self,
        ledger: EffectLedger,
        inventor_id: str,
        credentials: FactoryAgentCredentials,
        *,
        transport: Transport = urllib_transport,
        project_file_transport: Optional[ProjectFileTransport] = None,
        sleeper: Sleeper = time.sleep,
    ) -> None:
        if not isinstance(ledger, EffectLedger):
            raise ContractError("Factory Release writer requires an EffectLedger")
        if not isinstance(inventor_id, str) or not _INVENTOR_ID.fullmatch(inventor_id):
            raise ContractError("Factory inventor_id must be a canonical slug")
        if not isinstance(credentials, FactoryAgentCredentials):
            raise ContractError("Factory Release writer requires typed credentials")
        self.inventor_id = inventor_id
        self.ledger = ledger
        self.session = FactoryAgentSession(
            credentials,
            transport=transport,
            project_file_transport=project_file_transport,
            sleeper=sleeper,
        )

    def __repr__(self) -> str:
        return "FactoryReleaseWriter(inventor_id=%r, credentials=<redacted>)" % self.inventor_id

    @staticmethod
    def _assert_private_receipt(receipt: Receipt, intent: EffectIntent) -> None:
        receipt.assert_payload(intent.pack_sha256)
        receipt.assert_artifact(intent.product_artifact_sha256)
        if not receipt.is_verified_draft:
            raise ReceiptError("Factory import requires authenticated private readback")
        details = receipt.details
        if details.get("product_id") != intent.product_id:
            raise ReceiptError("Factory Receipt belongs to a different product")
        required_hashes = (
            "release_sha256",
            "playtest_evidence_sha256",
            "handoff_artifact_sha256",
            "product_facts_sha256",
            "primary_model_sha256",
            "product_page_sha256",
            "manual_sha256",
            "effect_request_sha256",
        )
        for name in required_hashes:
            require_sha256(details.get(name), "Factory Receipt %s" % name)
        if details.get("release_sha256") != intent.release_sha256:
            raise ReceiptError("Factory Receipt belongs to different Release bytes")
        if details.get("playtest_evidence_sha256") != intent.playtest_evidence_sha256:
            raise ReceiptError("Factory Receipt belongs to different Playtest evidence")
        if details.get("handoff_artifact_sha256") != intent.handoff_artifact_sha256:
            raise ReceiptError("Factory Receipt belongs to a different handoff tree")
        if details.get("effect_idempotency_key") != intent.idempotency_key:
            raise ReceiptError("Factory Receipt belongs to a different effect")
        if details.get("product_page_sha256") != intent.request.get(
            "product_page_sha256"
        ):
            raise ReceiptError("Factory Receipt belongs to different product-page bytes")
        if details.get("manual_sha256") != intent.request.get("manual_sha256"):
            raise ReceiptError("Factory Receipt belongs to different manual bytes")
        metadata = intent.request.get("metadata")
        requested_category = (
            metadata.get("category") if isinstance(metadata, Mapping) else None
        )
        # Historical receipts from before Workshop declared a category remain
        # readable under their original request. New imports are exact: their
        # authenticated readback must be carried into the durable receipt.
        if requested_category is not None and details.get(
            "factory_category_slug"
        ) != requested_category:
            raise ReceiptError("Factory Receipt belongs to a different category")
        requested_manual_path = intent.request.get("manual_path")
        if requested_manual_path is not None and (
            requested_manual_path != FACTORY_RELEASE_PDF_MANUAL_PATH
            or details.get("manual_path") != requested_manual_path
        ):
            raise ReceiptError("Factory Receipt belongs to a different manual path")
        manual_url = details.get("manual_url")
        manual_readback_sha256 = details.get("manual_readback_sha256")
        if manual_url is not None or manual_readback_sha256 is not None:
            if (
                manual_url
                != _factory_project_file_url(
                    receipt.project_url, FACTORY_RELEASE_PDF_MANUAL_PATH
                )
                or manual_readback_sha256 != details.get("manual_sha256")
            ):
                raise ReceiptError(
                    "Factory Receipt does not preserve exact MANUAL.pdf readback"
                )
        _https_url(details.get("page_url"), "Factory page URL")
        if requested_manual_path is None:
            _https_url(details.get("cover_url"), "Factory cover URL")
        if details.get("content_owner") != "workshop-manager":
            raise ReceiptError("Factory import must preserve Workshop page ownership")

    def _readback_private(
        self,
        client: FactoryClient,
        intent: EffectIntent,
        imported_design: Mapping[str, Any],
        proof: Mapping[str, Any],
    ) -> Tuple[Receipt, Mapping[str, Any]]:
        imported = _factory_receipt(imported_design, intent, proof)
        imported.assert_owner(intent.request.get("owner_id"))
        if not imported.is_verified_draft:
            raise ReceiptError("Factory import did not return a private draft")
        response = client.get_design(imported.slug)
        if response.status != 200:
            raise AmbiguousEffectError(
                "authenticated Factory draft readback returned HTTP %s" % response.status
            )
        observed_design = _json_body(response, "Factory draft readback")
        observed = _factory_receipt(observed_design, intent, proof)
        observed.assert_owner(intent.request.get("owner_id"))
        if not observed.is_verified_draft or not _same_factory_identity(imported, observed):
            raise ReceiptError("Factory readback does not identify the imported draft")
        metadata = intent.request.get("metadata")
        category = observed_design.get("category")
        author = observed_design.get("author")
        imported_covers = imported_design.get("thumbnail_urls")
        observed_covers = observed_design.get("thumbnail_urls")
        pdf_first = (
            intent.request.get("manual_path") == FACTORY_RELEASE_PDF_MANUAL_PATH
        )
        if (
            not isinstance(metadata, Mapping)
            or observed_design.get("origin") != "import"
            or observed_design.get("title") != metadata.get("title")
            or observed_design.get("description") != metadata.get("description")
            or observed_design.get("tags") != metadata.get("tags")
            or (
                "category" in metadata
                and (
                    not isinstance(category, Mapping)
                    or category.get("slug") != metadata.get("category")
                )
            )
            or (
                not pdf_first
                and (
                    not isinstance(imported_covers, list)
                    or not imported_covers
                    or observed_covers != imported_covers
                )
            )
            or not isinstance(author, Mapping)
            or author.get("id") != intent.request.get("owner_id")
        ):
            raise ReceiptError("Factory readback does not preserve the exact import")
        details = dict(observed.details)
        details["page_url"] = _factory_product_page_url(observed.slug)
        requested_category = metadata.get("category")
        if requested_category is not None:
            details["factory_category_slug"] = requested_category
        if pdf_first:
            details.update(
                self.session.verify_pdf_manual(
                    observed.project_url, intent.request.get("manual_sha256")
                )
            )
        else:
            details["cover_url"] = _https_url(
                imported_covers[0], "Factory cover URL"
            )
            details["server_cover_urls"] = [
                _https_url(url, "Factory cover URL") for url in imported_covers
            ]
        final = Receipt.from_dict({**observed.to_dict(), "details": details})
        self._assert_private_receipt(final, intent)
        return final, observed_design

    def _recover_unknown(
        self,
        client: FactoryClient,
        intent: EffectIntent,
        proof: Mapping[str, Any],
    ) -> Receipt:
        imported_design = intent.response
        if imported_design is None:
            # A transport can lose the import response after Factory persisted
            # the request. The Workshop product id is the requested stable slug;
            # use it only as a discovery key, then require the normal owner,
            # category, history, package and manual bindings below. A missing or
            # different design remains unknown and is never blindly retried.
            response = client.get_design(intent.product_id)
            if response.status != 200:
                raise AmbiguousEffectError(
                    "Factory import outcome is unknown and exact slug readback failed"
                )
            try:
                imported_design = _json_body(
                    response, "Factory unknown-import slug readback"
                )
            except (ContractError, EffectError) as exc:
                raise AmbiguousEffectError(
                    "Factory import outcome is unknown and slug readback is invalid"
                ) from exc
        try:
            receipt, observed = self._readback_private(
                client, intent, imported_design, proof
            )
            resolved = self.ledger.resolve_succeeded(
                intent.intent_id,
                receipt,
                {"import": dict(imported_design), "readback": dict(observed)},
            )
        except (ContractError, EffectError, ReceiptError, StateConflict) as exc:
            raise AmbiguousEffectError(
                "Factory import remains unknown; it will not be retried"
            ) from exc
        assert resolved.receipt is not None
        return resolved.receipt

    @staticmethod
    def _assert_content_receipt(
        receipt: Receipt,
        intent: EffectIntent,
        imported: Receipt,
    ) -> None:
        receipt.assert_payload(intent.pack_sha256)
        receipt.assert_artifact(intent.product_artifact_sha256)
        if not receipt.is_verified_draft or not _same_factory_identity(imported, receipt):
            raise ReceiptError(
                "Factory content Receipt does not identify the imported draft"
            )
        details = receipt.details
        for name in (
            "release_sha256",
            "playtest_evidence_sha256",
            "handoff_artifact_sha256",
            "product_page_sha256",
            "manual_sha256",
            "factory_content_sha256",
            "effect_request_sha256",
            "factory_content_effect_request_sha256",
            "import_effect_request_sha256",
        ):
            require_sha256(details.get(name), "Factory content Receipt %s" % name)
        expected = {
            "product_id": intent.product_id,
            "release_sha256": intent.release_sha256,
            "playtest_evidence_sha256": intent.playtest_evidence_sha256,
            "handoff_artifact_sha256": intent.handoff_artifact_sha256,
            "product_page_sha256": intent.request.get("product_page_sha256"),
            "manual_sha256": intent.request.get("manual_sha256"),
            "factory_content_sha256": intent.request.get("factory_content_sha256"),
            "factory_content_effect_request_sha256": intent.request_sha256,
            "import_effect_request_sha256": imported.details.get(
                "effect_request_sha256"
            ),
            "effect_request_sha256": intent.request_sha256,
            "effect_idempotency_key": intent.idempotency_key,
            "factory_content_mapping": FACTORY_CONTENT_MAPPING,
            "content_owner": "workshop-manager",
        }
        if any(details.get(name) != value for name, value in expected.items()):
            raise ReceiptError(
                "Factory content Receipt is not bound to the exact page handoff"
            )
        exact_content = details.get("factory_content")
        if (
            not isinstance(exact_content, Mapping)
            or _canonical_sha256(exact_content)
            != intent.request.get("factory_content_sha256")
            or exact_content != intent.request.get("target")
        ):
            raise ReceiptError(
                "Factory content Receipt does not retain its exact rich content"
            )
        _https_url(details.get("page_url"), "Factory page URL")
        _https_url(details.get("cover_url"), "Factory cover URL")

    def _content_receipt(
        self,
        design: Mapping[str, Any],
        intent: EffectIntent,
        imported: Receipt,
        proof: Mapping[str, Any],
        target: Mapping[str, Any],
    ) -> Receipt:
        if _factory_content_state(design) != target:
            raise ReceiptError(
                "Factory readback does not preserve exact Workshop page content"
            )
        observed = _factory_receipt(design, intent, proof)
        observed.assert_owner(intent.request.get("owner_id"))
        if not observed.is_verified_draft or not _same_factory_identity(imported, observed):
            raise ReceiptError(
                "Factory content readback changed the imported draft identity"
            )
        final = Receipt.from_dict(observed.to_dict())
        self._assert_content_receipt(final, intent, imported)
        return final

    def _content_design(self, client: FactoryClient, slug: str) -> Mapping[str, Any]:
        response = client.get_design(slug)
        if response.status != 200:
            raise AmbiguousEffectError(
                "authenticated Factory content readback returned HTTP %s"
                % response.status
            )
        return _json_body(response, "Factory content readback")

    def _ensure_page_content(
        self,
        client: FactoryClient,
        imported: Receipt,
        page: Mapping[str, Any],
        *,
        product_page_sha256: str,
        manual_sha256: str,
    ) -> Receipt:
        cover_url = _https_url(
            imported.details.get("cover_url"), "Factory imported cover URL"
        )
        target = _factory_content_target(page, cover_url)
        target_sha256 = _canonical_sha256(target)
        request = {
            "schema_version": 1,
            "method": "PATCH+PUT",
            "api_origin": _api_origin(DEFAULT_FACTORY_API),
            "paths": [
                "/designs/%s/use-case"
                % urllib.parse.quote(imported.slug, safe=""),
                "/designs/%s/story-blocks"
                % urllib.parse.quote(imported.slug, safe=""),
            ],
            "owner_id": imported.owner_id,
            "design_id": imported.design_id,
            "slug": imported.slug,
            "root_id": imported.root_id,
            "current_history_id": imported.current_history_id,
            "product_page_sha256": require_sha256(
                product_page_sha256, "Factory content product-page sha256"
            ),
            "manual_sha256": require_sha256(
                manual_sha256, "Factory content manual sha256"
            ),
            "factory_content_sha256": target_sha256,
            "target": target,
        }
        intent = self.ledger.prepare(
            kind="factory-content",
            product_id=imported.details.get("product_id"),
            request=request,
            pack_sha256=imported.payload_sha256,
            handoff_artifact_sha256=imported.details.get(
                "handoff_artifact_sha256"
            ),
            product_artifact_sha256=imported.artifact_sha256,
            release_sha256=imported.details.get("release_sha256"),
            playtest_evidence_sha256=imported.details.get(
                "playtest_evidence_sha256"
            ),
        )
        proof = {
            **dict(imported.details),
            "product_page_sha256": product_page_sha256,
            "manual_sha256": manual_sha256,
            "factory_content_sha256": target_sha256,
            "factory_content": target,
            "factory_content_mapping": FACTORY_CONTENT_MAPPING,
            "factory_content_effect_request_sha256": intent.request_sha256,
            "import_effect_request_sha256": imported.details.get(
                "effect_request_sha256"
            ),
            "content_owner": "workshop-manager",
        }
        if intent.state == "succeeded":
            if intent.receipt is None:
                raise StateConflict("completed Factory content write has no Receipt")
            self._assert_content_receipt(intent.receipt, intent, imported)
            return intent.receipt
        if intent.state == "rejected":
            raise EffectError("Factory previously rejected this exact page content")
        if intent.state == "sending":
            intent = self.ledger.strand_as_unknown(
                intent.intent_id, "host exited while Factory page content was sending"
            )
        if intent.state == "unknown":
            try:
                design = self._content_design(client, imported.slug)
                observed_content = _factory_content_state(design)
                partial_target = {
                    "use_case": target["use_case"],
                    "story_blocks": [],
                }
                if observed_content == partial_target and target["story_blocks"]:
                    # The authenticated readback proves the first mutation
                    # happened and the second did not.  Continuing only the
                    # missing story-block mutation is reconciliation of an
                    # exact partial target, not a blind retry of the combined
                    # effect.  Keep the durable intent unknown until a final
                    # authenticated readback proves the whole target.
                    observed_receipt = _factory_receipt(design, intent, proof)
                    observed_receipt.assert_owner(imported.owner_id)
                    if (
                        not observed_receipt.is_verified_draft
                        or not _same_factory_identity(imported, observed_receipt)
                    ):
                        raise ReceiptError(
                            "Factory partial content readback changed the imported draft identity"
                        )
                    response = client.write_story_blocks(
                        imported.slug,
                        target["story_blocks"],
                        intent.idempotency_key + "-story-blocks",
                    )
                    if response.status != 200:
                        raise AmbiguousEffectError(
                            "Factory partial page-content reconciliation did not complete"
                        )
                    written = _json_body(
                        response, "Factory reconciled story_blocks response"
                    )
                    if _factory_content_state(written) != target:
                        raise ReceiptError(
                            "Factory reconciled story_blocks response did not preserve exact content"
                        )
                    design = self._content_design(client, imported.slug)
                elif observed_content != target:
                    raise StateConflict(
                        "Factory page-content outcome is neither the exact target nor its safe partial state"
                    )
                receipt = self._content_receipt(design, intent, imported, proof, target)
                completed = self.ledger.resolve_succeeded(
                    intent.intent_id, receipt, design
                )
            except (ContractError, EffectError, ReceiptError, StateConflict) as exc:
                raise AmbiguousEffectError(
                    "Factory page-content outcome remains unknown; it will not be retried"
                ) from exc
            assert completed.receipt is not None
            return completed.receipt

        preflight = self._content_design(client, imported.slug)
        preflight_receipt = _factory_receipt(preflight, intent, proof)
        preflight_receipt.assert_owner(imported.owner_id)
        if (
            not preflight_receipt.is_verified_draft
            or not _same_factory_identity(imported, preflight_receipt)
        ):
            raise ReceiptError(
                "Factory page-content preflight changed the imported draft identity"
            )
        preflight_content = _factory_content_state(preflight)
        if preflight_content == target:
            receipt = self._content_receipt(
                preflight, intent, imported, proof, target
            )
            completed = self.ledger.resolve_succeeded(
                intent.intent_id, receipt, preflight
            )
            assert completed.receipt is not None
            return completed.receipt
        if preflight_content != {"use_case": None, "story_blocks": []}:
            raise StateConflict(
                "Factory draft already contains different page content; refusing to overwrite it"
            )

        sending = self.ledger.begin(intent.intent_id)
        assert sending.effect_token is not None
        first_value: Optional[Mapping[str, Any]] = None
        second_value: Optional[Mapping[str, Any]] = None
        try:
            first = client.write_use_case(
                imported.slug,
                target["use_case"],
                sending.idempotency_key + "-use-case",
            )
            if first.status != 200:
                summary = first.body.decode("utf-8", "replace")[:500]
                error = "HTTP %s: %s" % (first.status, summary)
                if first.status in PROVEN_NO_EFFECT_STATUSES:
                    self.ledger.mark_rejected(
                        sending.intent_id, sending.effect_token, error
                    )
                    raise EffectError(
                        "Factory rejected exact use_case content with HTTP %s"
                        % first.status
                    )
                self.ledger.mark_unknown(
                    sending.intent_id, sending.effect_token, error
                )
                raise AmbiguousEffectError(
                    "Factory use_case write returned an ambiguous HTTP status"
                )
            first_value = _json_body(first, "Factory use_case write response")
            if _factory_content_state(first_value) != {
                "use_case": target["use_case"],
                "story_blocks": [],
            }:
                raise ReceiptError(
                    "Factory use_case response did not preserve exact content"
                )

            second = client.write_story_blocks(
                imported.slug,
                target["story_blocks"],
                sending.idempotency_key + "-story-blocks",
            )
            if second.status != 200:
                raise AmbiguousEffectError(
                    "Factory page content is only partially applied after story_blocks returned HTTP %s"
                    % second.status
                )
            second_value = _json_body(
                second, "Factory story_blocks write response"
            )
            if _factory_content_state(second_value) != target:
                raise ReceiptError(
                    "Factory story_blocks response did not preserve exact content"
                )
            observed = self._content_design(client, imported.slug)
            receipt = self._content_receipt(
                observed, sending, imported, proof, target
            )
            completed = self.ledger.mark_succeeded(
                sending.intent_id,
                sending.effect_token,
                receipt,
                {
                    "use_case_write": dict(first_value),
                    "story_blocks_write": dict(second_value),
                    "readback": dict(observed),
                },
            )
        except (AmbiguousEffectError, EffectError) as exc:
            current = self.ledger.get(sending.intent_id)
            if current.state == "sending":
                self.ledger.mark_unknown(
                    sending.intent_id,
                    sending.effect_token,
                    "%s: %s" % (type(exc).__name__, exc),
                    response=second_value or first_value,
                )
            if first_value is not None and not isinstance(
                exc, AmbiguousEffectError
            ):
                raise AmbiguousEffectError(
                    "Factory page content is partially applied and requires authenticated reconciliation"
                ) from exc
            raise
        except Exception as exc:
            current = self.ledger.get(sending.intent_id)
            if current.state == "sending":
                self.ledger.mark_unknown(
                    sending.intent_id,
                    sending.effect_token,
                    "Factory page content lacks conclusive exact readback",
                    response=second_value or first_value,
                )
            raise AmbiguousEffectError(
                "Factory page-content outcome is unknown and will not be blindly retried"
            ) from exc
        assert completed.receipt is not None
        return completed.receipt

    def _complete_release_draft(
        self,
        client: FactoryClient,
        imported: Receipt,
        page: Mapping[str, Any],
        *,
        product_page_sha256: str,
        manual_sha256: str,
    ) -> Receipt:
        if page.get("schema_version") == LEGACY_RELEASE_PRODUCT_SCHEMA_VERSION:
            return self._ensure_page_content(
                client,
                imported,
                page,
                product_page_sha256=product_page_sha256,
                manual_sha256=manual_sha256,
            )
        if page.get("schema_version") not in (
            RELEASE_PRODUCT_SCHEMA_VERSION,
            DIRECT_RELEASE_PRODUCT_SCHEMA_VERSION,
        ):
            raise ContractError("Factory Release product schema is unsupported")
        return imported

    def __call__(
        self,
        context: Any,
        sealed_root: Path,
        sealed_manifest: ArtifactManifest,
    ) -> Receipt:
        if not callable(getattr(context, "assert_current", None)):
            raise ContractError("FactoryReleaseWriter requires a ReleaseContext")
        context.assert_current()
        release_root = _assert_sealed_release(sealed_root, sealed_manifest)
        release_sha256 = require_sha256(
            sealed_manifest.artifact_sha256, "sealed Release sha256"
        )
        page, page_content = _release_page(release_root)
        if page.get("schema_version") == LEGACY_RELEASE_PRODUCT_SCHEMA_VERSION:
            # Preserve the schema-v3 rich-page projection exactly. Schema v4
            # deliberately has no Factory-authored use-case or story content.
            _factory_content_copy(page)
        manual_content, manual_sha256, manual_path = _release_manual(
            release_root, sealed_manifest, page
        )
        product_artifact_sha256 = require_sha256(
            page.get("product_artifact_sha256"), "Release product artifact sha256"
        )
        if product_artifact_sha256 != context.made.artifact_sha256:
            raise ContractError("Release page describes different Made bytes")
        playtest_sha256 = require_sha256(
            page.get("playtest_evidence_artifact_sha256"),
            "Release Playtest evidence sha256",
        )
        if FACTORY_MADE_FORBIDDEN_PAGE_FIELDS & set(context.made.product):
            raise ContractError("Made product facts contain Release page fields")
        identity = self.session.login()
        client = FactoryClient(self.session.authenticated_transport)

        product_facts = {
            "schema_version": 2,
            "kind": "workshop.product-facts",
            "source_artifact_sha256": product_artifact_sha256,
            "release_sha256": release_sha256,
            "playtest_evidence_sha256": playtest_sha256,
            "inventor": {"name": context.taste.name},
            "wish": context.wish.to_dict(),
            "product": dict(context.made.product),
            "release": dict(page),
            "manual": {
                "path": manual_path,
                "sha256": manual_sha256,
            },
        }
        with tempfile.TemporaryDirectory(prefix="workshop-release-effect-") as temporary:
            pack = Path(temporary) / "model-handoff.zip"
            handoff = _build_model_handoff(
                context,
                pack,
                product_facts,
                page_content,
                manual_content,
            )
        primary = handoff["primary_model"]
        # Factory defaults an omitted category to its first active category,
        # which is not a safe classification rule for Workshop products. Send
        # the canonical Toys & Games slug explicitly; an inactive/unknown slug
        # is a proven-no-effect rejection rather than a silent fallback. Prompt
        # remains deliberately omitted: Workshop will not fabricate or collapse
        # the exact Wish into Factory's optional prompt field; the sealed
        # facts/page retain that provenance.
        metadata = _normalize_import(
            {
                "status": "draft",
                "title": page.get("title"),
                "description": page.get("summary"),
                "category": FACTORY_TOY_CATEGORY_SLUG,
                "tags": ["toy"],
            }
        )
        request = {
            "method": "POST",
            "api_origin": _api_origin(DEFAULT_FACTORY_API),
            "path": "/designs/import",
            "filename": "model-handoff.zip",
            "owner_id": identity.owner_id,
            "product_page_sha256": handoff["product_page_sha256"],
            "manual_sha256": handoff["manual_sha256"],
            "metadata": dict(metadata),
        }
        if manual_path == FACTORY_RELEASE_PDF_MANUAL_PATH:
            request["manual_path"] = manual_path
        intent = self.ledger.prepare(
            kind="factory-import",
            product_id=context.wish.product_id,
            request=request,
            pack_sha256=handoff["pack_sha256"],
            handoff_artifact_sha256=handoff["artifact_sha256"],
            product_artifact_sha256=product_artifact_sha256,
            release_sha256=release_sha256,
            playtest_evidence_sha256=playtest_sha256,
        )
        proof = {
            "product_facts_sha256": handoff["product_facts_sha256"],
            "primary_model_path": primary["path"],
            "primary_model_sha256": primary["sha256"],
            "product_page_sha256": handoff["product_page_sha256"],
            "manual_sha256": handoff["manual_sha256"],
            "content_owner": "workshop-manager",
        }
        if manual_path == FACTORY_RELEASE_PDF_MANUAL_PATH:
            proof["manual_path"] = manual_path
        if intent.state == "succeeded":
            if intent.receipt is None:
                raise StateConflict("completed Factory import has no Receipt")
            self._assert_private_receipt(intent.receipt, intent)
            return self._complete_release_draft(
                client,
                intent.receipt,
                page,
                product_page_sha256=handoff["product_page_sha256"],
                manual_sha256=handoff["manual_sha256"],
            )
        if intent.state == "rejected":
            raise EffectError("Factory previously rejected this exact model import")
        if intent.state == "sending":
            intent = self.ledger.strand_as_unknown(
                intent.intent_id, "host exited while Factory import was sending"
            )
        if intent.state == "unknown":
            imported = self._recover_unknown(client, intent, proof)
            return self._complete_release_draft(
                client,
                imported,
                page,
                product_page_sha256=handoff["product_page_sha256"],
                manual_sha256=handoff["manual_sha256"],
            )

        context.assert_current()
        _assert_sealed_release(release_root, sealed_manifest)
        sending = self.ledger.begin(intent.intent_id)
        assert sending.effect_token is not None
        try:
            response = client.import_model(
                filename="model-handoff.zip",
                content=handoff["content"],
                metadata=metadata,
                idempotency_key=sending.idempotency_key,
            )
        except Exception as exc:
            self.ledger.mark_unknown(
                sending.intent_id,
                sending.effect_token,
                "%s: %s" % (type(exc).__name__, exc),
            )
            raise AmbiguousEffectError(
                "Factory import outcome is unknown and will not be blindly retried"
            ) from exc
        if response.status != 201:
            summary = response.body.decode("utf-8", "replace")[:500]
            error = "HTTP %s: %s" % (response.status, summary)
            if response.status in FACTORY_IMPORT_PROVEN_NO_EFFECT_STATUSES:
                self.ledger.mark_rejected(
                    sending.intent_id, sending.effect_token, error
                )
                raise EffectError("Factory rejected model import with HTTP %s" % response.status)
            self.ledger.mark_unknown(sending.intent_id, sending.effect_token, error)
            raise AmbiguousEffectError(
                "Factory import returned an ambiguous HTTP status"
            )
        try:
            imported_design = _json_body(response, "Factory import response")
            context.assert_current()
            _assert_sealed_release(release_root, sealed_manifest)
            receipt, observed = self._readback_private(
                client, sending, imported_design, proof
            )
            completed = self.ledger.mark_succeeded(
                sending.intent_id,
                sending.effect_token,
                receipt,
                {"import": dict(imported_design), "readback": dict(observed)},
            )
        except Exception as exc:
            current = self.ledger.get(sending.intent_id)
            if current.state == "sending":
                response_value = imported_design if "imported_design" in locals() else None
                self.ledger.mark_unknown(
                    sending.intent_id,
                    sending.effect_token,
                    "Factory accepted import but exact readback was unavailable",
                    response=response_value,
                )
            raise AmbiguousEffectError(
                "Factory accepted import but exact readback is not proven"
            ) from exc
        assert completed.receipt is not None
        return self._complete_release_draft(
            client,
            completed.receipt,
            page,
            product_page_sha256=handoff["product_page_sha256"],
            manual_sha256=handoff["manual_sha256"],
        )


class FactoryPublicTransition:
    """Promote one exact private draft under the Wish's Release authority."""

    def __init__(self, ledger: EffectLedger, session: FactoryAgentSession) -> None:
        if not isinstance(ledger, EffectLedger):
            raise ContractError("Factory public transition requires an EffectLedger")
        if not isinstance(session, FactoryAgentSession):
            raise ContractError("Factory public transition requires an agent session")
        self.ledger = ledger
        self.session = session

    def _public_receipt(
        self,
        design: Mapping[str, Any],
        draft: Receipt,
        intent: EffectIntent,
        owner_id: str,
    ) -> Receipt:
        FactoryPublicTransition._assert_exact_content(design, draft)
        FactoryPublicTransition._assert_exact_category(design, draft)
        details = dict(draft.details)
        if FactoryPublicTransition._is_pdf_first(draft):
            details.update(
                self.session.verify_pdf_manual(
                    design.get("project_url"), draft.details.get("manual_sha256")
                )
            )
        receipt = _factory_receipt(design, intent, details)
        receipt.assert_owner(owner_id)
        if not _same_factory_identity(draft, receipt):
            raise ReceiptError("Factory public readback changed the draft identity")
        if not receipt.is_verified_public:
            raise ReceiptError("Factory readback does not prove an active public listing")
        return receipt

    @staticmethod
    def _is_pdf_first(draft: Receipt) -> bool:
        manual_path = draft.details.get("manual_path")
        if manual_path is None:
            return False
        if manual_path != FACTORY_RELEASE_PDF_MANUAL_PATH:
            raise ReceiptError("Factory draft has an unsupported manual path")
        return True

    @staticmethod
    def _assert_exact_content(
        design: Mapping[str, Any], draft: Receipt
    ) -> None:
        if FactoryPublicTransition._is_pdf_first(draft):
            return
        target = draft.details.get("factory_content")
        expected_sha256 = require_sha256(
            draft.details.get("factory_content_sha256"),
            "Factory draft rich-content sha256",
        )
        if (
            not isinstance(target, Mapping)
            or _canonical_sha256(target) != expected_sha256
        ):
            raise ReceiptError(
                "Factory draft does not retain its exact rich-content target"
            )
        if _factory_content_state(design) != target:
            raise StateConflict(
                "Factory page content changed after the exact Workshop handoff"
            )

    @staticmethod
    def _expected_category(draft: Receipt) -> Optional[str]:
        value = draft.details.get("factory_category_slug")
        if value is None:
            # Historical draft receipts did not bind a category. Preserve their
            # original semantics rather than retroactively inventing evidence.
            return None
        if (
            not isinstance(value, str)
            or not value
            or value != value.strip()
            or len(value) > 100
        ):
            raise ReceiptError("Factory draft category is malformed")
        return value

    @staticmethod
    def _assert_exact_category(
        design: Mapping[str, Any], draft: Receipt
    ) -> None:
        expected = FactoryPublicTransition._expected_category(draft)
        if expected is None:
            return
        category = design.get("category")
        if not isinstance(category, Mapping) or category.get("slug") != expected:
            raise StateConflict(
                "Factory category changed after the exact Workshop import"
            )

    @staticmethod
    def _design(client: FactoryClient, slug: str) -> Mapping[str, Any]:
        response = client.get_design(slug)
        if response.status != 200:
            raise AmbiguousEffectError(
                "authenticated Factory readback returned HTTP %s" % response.status
            )
        return _json_body(response, "Factory design readback")

    def publish(self, draft: Receipt) -> Receipt:
        if not isinstance(draft, Receipt) or not draft.is_verified_draft:
            raise ContractError(
                "Factory public transition requires a verified private draft Receipt"
            )
        identity = self.session.login()
        draft.assert_owner(identity.owner_id)
        release_sha256 = require_sha256(
            draft.details.get("release_sha256"), "Factory draft Release sha256"
        )
        playtest_sha256 = require_sha256(
            draft.details.get("playtest_evidence_sha256"),
            "Factory draft Playtest sha256",
        )
        handoff_sha256 = require_sha256(
            draft.details.get("handoff_artifact_sha256"),
            "Factory draft handoff artifact sha256",
        )
        product_page_sha256 = require_sha256(
            draft.details.get("product_page_sha256"),
            "Factory draft product-page sha256",
        )
        manual_sha256 = require_sha256(
            draft.details.get("manual_sha256"),
            "Factory draft manual sha256",
        )
        pdf_first = self._is_pdf_first(draft)
        factory_content_sha256: Optional[str] = None
        if not pdf_first:
            factory_content_sha256 = require_sha256(
                draft.details.get("factory_content_sha256"),
                "Factory draft rich-content sha256",
            )
            if draft.details.get("factory_content_mapping") != FACTORY_CONTENT_MAPPING:
                raise ReceiptError(
                    "Factory draft lacks the exact Workshop rich-content mapping"
                )
            target = draft.details.get("factory_content")
            if (
                not isinstance(target, Mapping)
                or _canonical_sha256(target) != factory_content_sha256
            ):
                raise ReceiptError(
                    "Factory draft lacks its exact Workshop rich-content target"
                )
        product_id = draft.details.get("product_id")
        if not isinstance(product_id, str) or not product_id:
            raise ReceiptError("Factory draft does not identify its Workshop product")
        request = {
            "method": "POST",
            "api_origin": _api_origin(DEFAULT_FACTORY_API),
            "path": "/designs/%s/publish" % urllib.parse.quote(draft.slug, safe=""),
            "owner_id": identity.owner_id,
            "design_id": draft.design_id,
            "slug": draft.slug,
            "root_id": draft.root_id,
            "current_history_id": draft.current_history_id,
            "product_page_sha256": product_page_sha256,
            "manual_sha256": manual_sha256,
        }
        category_slug = self._expected_category(draft)
        if category_slug is not None:
            request["category_slug"] = category_slug
        if pdf_first:
            request["manual_path"] = FACTORY_RELEASE_PDF_MANUAL_PATH
        else:
            request["factory_content_sha256"] = factory_content_sha256
        intent = self.ledger.prepare(
            kind="factory-publish",
            product_id=product_id,
            request=request,
            pack_sha256=draft.payload_sha256,
            handoff_artifact_sha256=handoff_sha256,
            product_artifact_sha256=draft.artifact_sha256,
            release_sha256=release_sha256,
            playtest_evidence_sha256=playtest_sha256,
        )
        if intent.state == "succeeded":
            if intent.receipt is None or not intent.receipt.is_verified_public:
                raise StateConflict("completed Factory publication has no public Receipt")
            if category_slug is not None and intent.receipt.details.get(
                "factory_category_slug"
            ) != category_slug:
                raise StateConflict(
                    "completed Factory publication lacks exact category evidence"
                )
            return intent.receipt
        if intent.state == "rejected":
            raise EffectError("Factory previously rejected this exact publication")
        if intent.state == "sending":
            intent = self.ledger.strand_as_unknown(
                intent.intent_id, "host exited while Factory publication was sending"
            )

        client = FactoryClient(self.session.authenticated_transport)
        try:
            before_design = self._design(client, draft.slug)
            before = _factory_receipt(before_design, intent, draft.details)
            before.assert_owner(identity.owner_id)
            if not _same_factory_identity(draft, before):
                raise ReceiptError("Factory preflight changed the draft identity")
            self._assert_exact_content(before_design, draft)
            self._assert_exact_category(before_design, draft)
            if pdf_first:
                self.session.verify_pdf_manual(
                    before.project_url, manual_sha256
                )
        except (ContractError, EffectError, ReceiptError) as exc:
            raise AmbiguousEffectError("Factory publication preflight is unavailable") from exc
        if before.is_verified_public:
            public = self._public_receipt(
                before_design, draft, intent, identity.owner_id
            )
            completed = self.ledger.resolve_succeeded(
                intent.intent_id, public, before_design
            )
            assert completed.receipt is not None
            return completed.receipt
        if not before.is_verified_draft:
            raise AmbiguousEffectError("Factory preflight does not prove the private draft")
        if intent.state == "unknown":
            raise AmbiguousEffectError(
                "Factory publication remains unknown; a draft readback does not prove absence"
            )

        sending = self.ledger.begin(intent.intent_id)
        assert sending.effect_token is not None
        try:
            response = client.publish(draft.slug, sending.idempotency_key)
        except Exception as exc:
            response = None
            send_error: Optional[Exception] = exc
        else:
            send_error = None
        try:
            after_design = self._design(client, draft.slug)
            after = self._public_receipt(
                after_design, draft, sending, identity.owner_id
            )
        except Exception as readback_error:
            if response is not None and response.status in PROVEN_NO_EFFECT_STATUSES:
                self.ledger.mark_rejected(
                    sending.intent_id,
                    sending.effect_token,
                    "Factory rejected publication with HTTP %s" % response.status,
                )
                raise EffectError(
                    "Factory rejected publication with HTTP %s" % response.status
                ) from readback_error
            self.ledger.mark_unknown(
                sending.intent_id,
                sending.effect_token,
                "Factory publication lacks conclusive authenticated readback",
                response=(
                    {"status": response.status}
                    if response is not None
                    else None
                ),
            )
            raise AmbiguousEffectError(
                "Factory publication outcome is unknown and will not be blindly retried"
            ) from (send_error or readback_error)
        completed = self.ledger.mark_succeeded(
            sending.intent_id,
            sending.effect_token,
            after,
            after_design,
        )
        assert completed.receipt is not None
        return completed.receipt


__all__ = [
    "DEFAULT_FACTORY_API",
    "FACTORY_CONTENT_MAPPING",
    "FACTORY_TOY_CATEGORY_SLUG",
    "FactoryAgentCredentials",
    "FactoryAgentIdentity",
    "FactoryAgentSession",
    "FactoryAuthenticationError",
    "FactoryClient",
    "FactoryCredentialRejected",
    "FactoryPublicTransition",
    "FactoryReleaseWriter",
    "HttpResponse",
    "factory_credentials_from_environment",
    "urllib_transport",
]
