#!/usr/bin/env python3
"""Seal authored stage work into native Workshop proposal contracts.

This script runs with Workshop's trusted Python dependencies from an isolated
product workspace where the host has materialized an immutable
``STAGE.json`` with exactly these top-level fields::

    schema_version, kind, product_id, stage, checkpoint_sha256,
    subject_sha256, next_transition, round, max_rounds, inputs

The tool does not plan, research, judge, repair, or advance a gate.  It only
validates explicit authored inputs, hashes exact run-local bytes, reproduces
the native contract identities, and atomically writes the contract plus the
untrusted ``agent-outcome.json`` proposal for the host to validate.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import io
import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Optional, Sequence


STAGE_KIND = "autonomous-workshop.stage-input"
OUTCOME_KIND = "autonomous-workshop.agent-outcome-proposal"
INVENTOR_ROSTER_KIND = "autonomous-workshop.inventor-roster"
MATCH_KIND = "autonomous-workshop.match-assignment"
INVENTED_KIND = "autonomous-workshop.invented"
MADE_KIND = "autonomous-workshop.made"
MAKE_INVENT_REVISION_KIND = "autonomous-workshop.make-invent-revision"
PLAYTESTED_KIND = "autonomous-workshop.playtested"
RELEASE_KIND = "autonomous-workshop.release"

STAGES = ("match", "invent", "make", "playtest", "release")
JOBS = ("wish", "invent", "make", "playtest", "release")
PLAYTEST_MAKE_INVALIDATES = ("playtest", "release")
PLAYTEST_INVENT_INVALIDATES = (
    "invent",
    "make",
    "playtest",
    "release",
)
PLAYTEST_FEEDBACK_INVALIDATES = frozenset(PLAYTEST_INVENT_INVALIDATES)
MAKE_INVENT_REVISION_INVALIDATES = PLAYTEST_INVENT_INVALIDATES
FORWARD = {
    "match": "invent",
    "invent": "make",
    "make": "release",
    "playtest": "release",
    "release": "complete",
}
STAGE_FIELDS = {
    "schema_version",
    "kind",
    "product_id",
    "stage",
    "checkpoint_sha256",
    "subject_sha256",
    "next_transition",
    "round",
    "max_rounds",
    "inputs",
}

MATCH_PATH = "artifacts/match/assignment.json"
INVENT_PATH = "artifacts/invent/invented.json"

MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_STAGE_BYTES = 4 * 1024 * 1024
MAX_OUTCOME_BYTES = 128 * 1024
MAX_CONTRACT_BYTES = 16 * 1024 * 1024
MAX_RELEASE_CONTRACT_BYTES = 2 * 1024 * 1024
MAX_RELEASE_MANUAL_BYTES = 16 * 1024 * 1024
MAX_MANUAL_DESIGN_EVIDENCE_BYTES = 64 * 1024
MAX_RELEASE_PDF_VALIDATOR_OUTPUT_BYTES = 4 * 1024
RELEASE_PDF_VALIDATION_TIMEOUT_SECONDS = 15
MAX_FILE_BYTES = 95 * 1024 * 1024
MAX_TREE_BYTES = 512 * 1024 * 1024
MAX_TREE_ENTRIES = 4096
MAX_INVENTORS = 256
MAX_AGENT_NEED_CHARS = 1_024

EXCLUDED_DIRS = frozenset(
    (
        ".git",
        ".claude",
        ".idea",
        ".vscode",
        "__cadgen__",
        "__macosx",
        "__pycache__",
        "inputs",
        "transcripts",
    )
)
EXCLUDED_FILES = frozenset(
    (
        ".ds_store",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "_inventor-artifact.json",
        "_tree.json",
        "auth.json",
        "catalog-auth.json",
        "credential.json",
        "credentials.json",
        "id_ecdsa",
        "id_ed25519",
        "id_rsa",
        "panda-auth.json",
        "portal-auth.json",
        "access-token.json",
        "refresh-token.json",
        "token",
        "token.json",
        "token.txt",
        "tokens.json",
        "conversation_transcript.txt",
    )
)
EXCLUDED_SUFFIXES = (
    ".backup",
    ".bak",
    ".db",
    ".db-journal",
    ".db-shm",
    ".db-wal",
    ".jsonl",
    ".key",
    ".pem",
    ".pyc",
    ".p12",
    ".pfx",
    ".sqlite",
    ".sqlite-shm",
    ".sqlite-wal",
    ".sqlite-journal",
    ".sqlite3",
    ".sqlite3-shm",
    ".sqlite3-wal",
    ".sqlite3-journal",
)
EXCLUDED_PREFIXES = (".env", "auth.", "credential.", "credentials.", "secrets.")
ARTIFACT_DEBRIS_SUFFIXES = (
    ".backup",
    ".bak",
    ".orig",
    ".rej",
    ".swn",
    ".swo",
    ".swp",
    "~",
)

SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
INVENTOR_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PRODUCT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
CHECK_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")

# Invent concept contract (Invented schema 4).  Schema 3 is the legacy shape
# that only bound `title` and `summary`; sealed runs that predate the contract
# keep resuming on it.  New Invent finalizations always emit schema 4.
INVENTED_SCHEMA_VERSIONS = (3, 4, 5)
BUILD_GROUP_FIELDS = frozenset(("group", "parts", "exit_criteria"))
MAX_BUILD_GROUPS = 16
MAKE_GROUP_KIND = "autonomous-workshop.make-group"
PARTS_DIRECTORY = "parts"
GROUPS_DIRECTORY = "groups"
CONCEPT_CONTRACT_FIELDS = frozenset(
    ("title", "summary", "interaction", "envelope_mm", "mechanisms", "components")
)
COMPONENT_CONTRACT_FIELDS = frozenset(
    (
        "key",
        "name",
        "form",
        "duty",
        "dimensions_mm",
        "placement",
        "interfaces",
        "mates_with",
        "signature",
    )
)
DIMENSION_KEYS = ("length_mm", "width_mm", "height_mm")
HEDGED_COMPONENT_FIELDS = ("form", "duty", "placement", "interfaces")
MAX_CONCEPT_COMPONENTS = 64
MAX_CONCEPT_MECHANISMS = 16
MAX_DIMENSION_MM = 2000.0
CONCEPT_SLUG_RE = re.compile(r"^[a-z][a-z0-9_-]{0,62}$")
# A physical description that hedges a quantity is a wish, not a contract.
NUMERIC_HEDGE_RE = re.compile(
    r"(?i)\b(?:roughly|about|approximately|around|circa)\s+\d|~\s*\d"
)
QUANTITY_HEDGE_RE = re.compile(
    r"(?i)\b(?:some|several|a few|a number of|a couple of|multiple|various|"
    r"enough|as needed|or so)\b"
)
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
MANUAL_DESIGN_EVIDENCE_PATH = "MANUAL-DESIGN.json"
MANUAL_DESIGN_EVIDENCE_KIND = "autonomous-workshop.manual-design-evidence"
MANUAL_VISUAL_SUFFIXES = frozenset(
    (".3mf", ".glb", ".jpeg", ".jpg", ".obj", ".png", ".step", ".stl", ".svg", ".webp")
)

FORBIDDEN_RELEASE_MEDIA_SUFFIXES = frozenset(
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
        ".mp3",
        ".mp4",
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
MANUAL_RELEASE_PRODUCT_FIELDS = frozenset(
    (
        "schema_version",
        "kind",
        "status",
        "title",
        "summary",
        "what_arrives",
        "limitations",
        "product_artifact_sha256",
        "playtest_evidence_artifact_sha256",
        "claims",
    )
)
DIRECT_RELEASE_PRODUCT_FIELDS = frozenset(
    (*MANUAL_RELEASE_PRODUCT_FIELDS, "playtest_status")
)
PLAYTEST_OMISSION_PATH = "PLAYTEST-NOT-RUN.json"
PLAYTEST_OMISSION_KIND = "autonomous-workshop.playtest-omission"
PLAYTEST_OMISSION_STATUS = "not-run"
class ProposalError(Exception):
    """One deterministic proposal input is invalid or unsafe."""


def canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ProposalError("value must be bounded finite JSON") from exc


def json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise ValueError("non-finite JSON number: %s" % value)


def _validate_json(value: Any, label: str, *, maximum: int = MAX_JSON_BYTES) -> None:
    def walk(item: Any, depth: int = 0) -> None:
        if depth > 64:
            raise ProposalError("%s exceeds the JSON nesting limit" % label)
        if item is None or isinstance(item, (str, bool, int)):
            return
        if isinstance(item, float):
            if not math.isfinite(item):
                raise ProposalError("%s contains a non-finite number" % label)
            return
        if isinstance(item, dict):
            if not all(isinstance(key, str) for key in item):
                raise ProposalError("%s object keys must be strings" % label)
            for nested in item.values():
                walk(nested, depth + 1)
            return
        if isinstance(item, list):
            for nested in item:
                walk(nested, depth + 1)
            return
        raise ProposalError("%s contains a non-JSON value" % label)

    walk(value)
    if len(canonical_json(value)) > maximum:
        raise ProposalError("%s exceeds its byte limit" % label)


def _mapping(value: Any, label: str, *, nonempty: bool = False) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProposalError("%s must be an object" % label)
    _validate_json(value, label)
    if nonempty and not value:
        raise ProposalError("%s must not be empty" % label)
    return value


def _array(value: Any, label: str, *, nonempty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        raise ProposalError("%s must be an array" % label)
    if nonempty and not value:
        raise ProposalError("%s must not be empty" % label)
    return value


def _fields(value: Any, expected: set[str], label: str) -> dict[str, Any]:
    selected = _mapping(value, label)
    if set(selected) != expected:
        raise ProposalError("%s fields are invalid" % label)
    return selected


def _required_fields(
    value: Any, required: set[str], label: str
) -> dict[str, Any]:
    selected = _mapping(value, label)
    missing = required - set(selected)
    if missing:
        raise ProposalError("%s is missing required fields" % label)
    return selected


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
        raise ProposalError("%s must be a lowercase SHA-256" % label)
    return value


def _positive_int(value: Any, label: str, maximum: int = 100) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ProposalError("%s must be an integer from 1 through %d" % (label, maximum))
    return value


def _bounded_text(value: Any, label: str, maximum: int = 10_000) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(
            ord(character) < 32 and character not in "\n\r\t"
            for character in value
        )
        or any(ord(character) == 127 for character in value)
    ):
        raise ProposalError("%s must be bounded non-empty text" % label)
    return value


def _agent_need(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > MAX_AGENT_NEED_CHARS
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ProposalError("%s must be bounded single-line text" % label)
    return value


def _inventor_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or INVENTOR_RE.fullmatch(value) is None:
        raise ProposalError("%s must be a lowercase path-safe id" % label)
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
        raise ProposalError("%s must be a safe relative POSIX path" % label)
    return candidate


def _canonical_root(value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    candidate = candidate.absolute()
    try:
        identity = candidate.lstat()
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ProposalError("run root is unavailable") from exc
    if (
        candidate != resolved
        or candidate.is_symlink()
        or not stat.S_ISDIR(identity.st_mode)
    ):
        raise ProposalError("run root must be a canonical real directory")
    return candidate


def _open_regular(root: Path, relative: PurePosixPath) -> tuple[int, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    directory_flags = flags | getattr(os, "O_DIRECTORY", 0)
    directory: int | None = None
    descriptor: int | None = None
    try:
        expected_root = root.lstat()
        directory = os.open(str(root), directory_flags)
        opened_root = os.fstat(directory)
        if (
            not stat.S_ISDIR(opened_root.st_mode)
            or (opened_root.st_dev, opened_root.st_ino)
            != (expected_root.st_dev, expected_root.st_ino)
        ):
            raise ProposalError("run-local root changed while opening")
        for part in relative.parts[:-1]:
            child = os.open(part, directory_flags, dir_fd=directory)
            opened_child = os.fstat(child)
            if not stat.S_ISDIR(opened_child.st_mode):
                os.close(child)
                raise ProposalError("path contains a non-directory")
            os.close(directory)
            directory = child
        expected = (root / Path(*relative.parts)).lstat()
        if not stat.S_ISREG(expected.st_mode):
            raise ProposalError("run-local input must be regular and not a symlink")
        descriptor = os.open(relative.parts[-1], flags, dir_fd=directory)
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ProposalError("run-local input changed while opening")
        result = descriptor, opened
        descriptor = None
        return result
    except OSError as exc:
        raise ProposalError("run-local input cannot be opened without following links") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if directory is not None:
            os.close(directory)


def _read_regular(
    root: Path,
    relative_value: str,
    label: str,
    *,
    maximum: int,
) -> tuple[bytes, os.stat_result]:
    relative = _safe_relative(relative_value, label + " path")
    descriptor, opened = _open_regular(root, relative)
    try:
        if not 1 <= opened.st_size <= maximum:
            raise ProposalError("%s is empty or exceeds its byte limit" % label)
        chunks: list[bytes] = []
        length = 0
        while length <= maximum:
            chunk = os.read(descriptor, min(1024 * 1024, maximum + 1 - length))
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(content) != opened.st_size
            or len(content) > maximum
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ProposalError("%s changed while reading" % label)
        return content, opened
    finally:
        os.close(descriptor)


def _workshop_python() -> Path:
    raw = os.environ.get("WORKSHOP_PYTHON")
    try:
        requested = Path(raw) if isinstance(raw, str) else Path(".")
        resolved = requested.resolve(strict=True)
        identity = resolved.stat()
        requested_absolute = requested.absolute()
        invoked = Path(sys.executable).absolute()
        actual = Path(sys.executable).resolve(strict=True)
    except OSError as exc:
        raise ProposalError("WORKSHOP_PYTHON is unavailable") from exc
    if (
        not isinstance(raw, str)
        or not raw
        or not requested.is_absolute()
        or not stat.S_ISREG(identity.st_mode)
        or raw != requested_absolute.as_posix()
        or requested_absolute != invoked
        or resolved != actual
    ):
        raise ProposalError(
            "stage finalizer must run with the exact host-supplied WORKSHOP_PYTHON"
        )
    return requested_absolute


def _pdf_validator_path() -> Path:
    script = Path(__file__).resolve(strict=True)
    candidate = script.with_name("pdf_validator.py")
    try:
        identity = candidate.lstat()
        resolved = candidate.resolve(strict=True)
    except OSError as exc:
        raise ProposalError("Release PDF validator is unavailable") from exc
    if (
        candidate.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or resolved.parent != script.parent
    ):
        raise ProposalError("Release PDF validator must be an immutable sibling file")
    return resolved


def _pdf_validator_environment() -> dict[str, str]:
    environment = {
        "LANG": "C",
        "LC_ALL": "C",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
    }
    for name in ("PATH", "SYSTEMROOT", "TMPDIR", "WINDIR"):
        value = os.environ.get(name)
        if isinstance(value, str) and value:
            environment[name] = value
    return environment


def _validate_pdf_manual(content: bytes) -> None:
    """Validate PDF bytes through the exact resource-bounded sibling worker."""

    if not content.startswith(b"%PDF-"):
        raise ProposalError("Release MANUAL.pdf must have a PDF header")
    eof = content.rfind(b"%%EOF")
    if eof < 0 or content[eof + len(b"%%EOF") :].strip():
        raise ProposalError("Release MANUAL.pdf must have a final PDF EOF marker")
    python = _workshop_python()
    validator = _pdf_validator_path()
    try:
        descriptor = os.open(
            validator,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise ProposalError(
                    "Release PDF validator must be an immutable sibling file"
                )
            completed = subprocess.run(
                (
                    str(python),
                    "-I",
                    "-B",
                    "/dev/fd/%d" % descriptor,
                    "--isolated-worker",
                ),
                input=content,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                cwd=str(validator.parent),
                env=_pdf_validator_environment(),
                timeout=RELEASE_PDF_VALIDATION_TIMEOUT_SECONDS,
                check=False,
                start_new_session=True,
                pass_fds=(descriptor,),
            )
        finally:
            os.close(descriptor)
    except subprocess.TimeoutExpired as exc:
        raise ProposalError(
            "Release MANUAL.pdf exceeded PDF validation resource limits"
        ) from exc
    except (OSError, subprocess.SubprocessError, ValueError) as exc:
        raise ProposalError("Release PDF validator could not be launched") from exc
    if not 1 <= len(completed.stdout) <= MAX_RELEASE_PDF_VALIDATOR_OUTPUT_BYTES:
        raise ProposalError("Release PDF validator returned invalid output")
    try:
        result = json.loads(
            completed.stdout.decode("utf-8"), object_pairs_hook=_strict_object
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ProposalError("Release PDF validator returned invalid output") from exc
    if (
        not isinstance(result, dict)
        or set(result) != {"error", "ok"}
        or type(result["ok"]) is not bool
        or completed.stdout != canonical_json(result)
    ):
        raise ProposalError("Release PDF validator returned invalid output")
    if completed.returncode == 0 and result == {"error": None, "ok": True}:
        return
    error = result.get("error")
    if (
        completed.returncode != 2
        or result.get("ok") is not False
        or not isinstance(error, str)
        or not error
        or len(error) > 1_000
        or any(ord(character) < 32 or ord(character) == 127 for character in error)
    ):
        raise ProposalError("Release PDF validator failed safely")
    raise ProposalError("Release MANUAL.pdf %s" % error)


def _hash_regular(root: Path, relative_value: str, label: str) -> tuple[str, int, bool]:
    relative = _safe_relative(relative_value, label + " path")
    descriptor, opened = _open_regular(root, relative)
    try:
        if opened.st_size > MAX_FILE_BYTES:
            raise ProposalError("%s exceeds the native file limit" % label)
        digest = hashlib.sha256()
        length = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            length += len(chunk)
        after = os.fstat(descriptor)
        if (
            length != opened.st_size
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ProposalError("%s changed while hashing" % label)
        return digest.hexdigest(), opened.st_size, bool(opened.st_mode & stat.S_IXUSR)
    finally:
        os.close(descriptor)


def _read_json(
    root: Path,
    relative: str,
    label: str,
    *,
    maximum: int = MAX_JSON_BYTES,
) -> tuple[dict[str, Any], bytes, os.stat_result]:
    content, identity = _read_regular(
        root, relative, label, maximum=maximum
    )
    try:
        document = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, ValueError, RecursionError, json.JSONDecodeError) as exc:
        raise ProposalError("%s must contain strict UTF-8 JSON" % label) from exc
    if not isinstance(document, dict):
        raise ProposalError("%s must contain one JSON object" % label)
    _validate_json(document, label, maximum=maximum)
    return document, content, identity


def _existing_directory(root: Path, value: str, label: str) -> tuple[PurePosixPath, Path]:
    relative = _safe_relative(value, label)
    selected = root.joinpath(*relative.parts)
    try:
        identity = selected.lstat()
        resolved = selected.resolve(strict=True)
    except OSError as exc:
        raise ProposalError("%s is unavailable" % label) from exc
    if (
        selected != resolved
        or selected.is_symlink()
        or not stat.S_ISDIR(identity.st_mode)
    ):
        raise ProposalError("%s must be a real run-local directory" % label)
    return relative, selected


def _path_is_excluded(relative: PurePosixPath) -> bool:
    if any(part.casefold() in EXCLUDED_DIRS for part in relative.parts[:-1]):
        return True
    lowered = relative.name.casefold()
    return (
        lowered in EXCLUDED_FILES
        or lowered.startswith(EXCLUDED_PREFIXES)
        or lowered.endswith(EXCLUDED_SUFFIXES)
    )


def _path_has_artifact_debris(relative: PurePosixPath) -> bool:
    for part in relative.parts:
        lowered = part.casefold()
        if (
            lowered.endswith(ARTIFACT_DEBRIS_SUFFIXES)
            or (len(part) > 2 and part.startswith(".#"))
            or (len(part) > 2 and part.startswith("#") and part.endswith("#"))
        ):
            return True
    return False


def _prune_empty_directories(tree_root: Path, label: str) -> None:
    """Remove directory-only build residue that cannot be content-addressed."""

    for directory, _, _ in os.walk(str(tree_root), topdown=False, followlinks=False):
        candidate = Path(directory)
        if candidate == tree_root:
            continue
        try:
            identity = candidate.lstat()
        except OSError as exc:
            raise ProposalError("%s changed while empty directories were pruned" % label) from exc
        if candidate.is_symlink() or not stat.S_ISDIR(identity.st_mode):
            raise ProposalError("%s contains a symlink or special directory" % label)
        try:
            candidate.rmdir()
        except OSError:
            try:
                current = candidate.lstat()
            except OSError as exc:
                raise ProposalError(
                    "%s changed while empty directories were pruned" % label
                ) from exc
            if candidate.is_symlink() or not stat.S_ISDIR(current.st_mode):
                raise ProposalError(
                    "%s changed while empty directories were pruned" % label
                )


def _prune_derived_cad_caches(project_root: Path, label: str) -> None:
    """Remove only cadgen's reproducible runtime cache before sealing Make.

    ``verify_project --fresh`` deletes and rebuilds every ``__cadgen__`` tree.
    Sealing one therefore guarantees a byte-drift rejection even when all
    stable geometry passes. Stable exported STEP/STL/GLB and render files live
    outside this cache and remain in the exact product manifest.
    """

    caches: list[Path] = []
    for directory, dirnames, _ in os.walk(
        str(project_root), topdown=True, followlinks=False
    ):
        base = Path(directory)
        kept = []
        for dirname in sorted(dirnames):
            candidate = base / dirname
            try:
                identity = candidate.lstat()
            except OSError as exc:
                raise ProposalError(
                    "%s changed while derived CAD caches were inspected" % label
                ) from exc
            if candidate.is_symlink() or not stat.S_ISDIR(identity.st_mode):
                raise ProposalError(
                    "%s contains a symlink or special directory" % label
                )
            if dirname.casefold() == "__cadgen__":
                caches.append(candidate)
            else:
                kept.append(dirname)
        dirnames[:] = kept

    for cache in sorted(caches, key=lambda item: len(item.parts), reverse=True):
        for directory, dirnames, filenames in os.walk(
            str(cache), topdown=False, followlinks=False
        ):
            base = Path(directory)
            for filename in filenames:
                candidate = base / filename
                try:
                    identity = candidate.lstat()
                except OSError as exc:
                    raise ProposalError(
                        "%s changed while a derived CAD cache was removed" % label
                    ) from exc
                if candidate.is_symlink() or not stat.S_ISREG(identity.st_mode):
                    raise ProposalError(
                        "%s derived CAD cache contains a linked or special file"
                        % label
                    )
                try:
                    candidate.unlink()
                except OSError as exc:
                    raise ProposalError(
                        "%s derived CAD cache could not be removed" % label
                    ) from exc
            for dirname in dirnames:
                candidate = base / dirname
                try:
                    identity = candidate.lstat()
                except OSError as exc:
                    raise ProposalError(
                        "%s changed while a derived CAD cache was removed" % label
                    ) from exc
                if candidate.is_symlink() or not stat.S_ISDIR(identity.st_mode):
                    raise ProposalError(
                        "%s derived CAD cache contains a linked or special directory"
                        % label
                    )
                try:
                    candidate.rmdir()
                except OSError:
                    try:
                        current = candidate.lstat()
                    except OSError as exc:
                        raise ProposalError(
                            "%s changed while a derived CAD cache was removed"
                            % label
                        ) from exc
                    if candidate.is_symlink() or not stat.S_ISDIR(current.st_mode):
                        raise ProposalError(
                            "%s derived CAD cache contains a linked or special directory"
                            % label
                        )
        try:
            cache.rmdir()
        except OSError:
            try:
                current = cache.lstat()
            except OSError as exc:
                raise ProposalError(
                    "%s changed while a derived CAD cache was removed" % label
                ) from exc
            if cache.is_symlink() or not stat.S_ISDIR(current.st_mode):
                raise ProposalError(
                    "%s derived CAD cache contains a linked or special directory"
                    % label
                )


def _tree_manifest(run_root: Path, tree_relative_value: str, label: str) -> dict[str, Any]:
    tree_relative, tree_root = _existing_directory(
        run_root, tree_relative_value, label
    )
    entries: list[dict[str, Any]] = []
    actual_directories: set[str] = set()
    for directory, dirnames, filenames in os.walk(str(tree_root), followlinks=False):
        base = Path(directory)
        kept: list[str] = []
        for dirname in sorted(dirnames):
            absolute = base / dirname
            relative = PurePosixPath(absolute.relative_to(tree_root).as_posix())
            try:
                identity = absolute.lstat()
            except OSError as exc:
                raise ProposalError("%s contains an unavailable directory" % label) from exc
            if absolute.is_symlink() or not stat.S_ISDIR(identity.st_mode):
                raise ProposalError("%s contains a symlink or special directory" % label)
            if _path_has_artifact_debris(relative):
                raise ProposalError("%s contains editor, backup, or patch debris" % label)
            kept.append(dirname)
            actual_directories.add(relative.as_posix())
        dirnames[:] = kept
        for filename in sorted(filenames):
            absolute = base / filename
            relative = PurePosixPath(absolute.relative_to(tree_root).as_posix())
            _safe_relative(relative.as_posix(), label + " entry")
            if _path_has_artifact_debris(relative):
                raise ProposalError("%s contains editor, backup, or patch debris" % label)
            if _path_is_excluded(relative):
                raise ProposalError("%s contains a path excluded by manifest policy" % label)
            run_relative = (tree_relative / relative).as_posix()
            digest, byte_count, executable = _hash_regular(
                run_root, run_relative, label + " entry"
            )
            entries.append(
                {
                    "path": relative.as_posix(),
                    "bytes": byte_count,
                    "sha256": digest,
                    "executable": executable,
                }
            )
            if len(entries) > MAX_TREE_ENTRIES:
                raise ProposalError("%s has too many files" % label)
    if not entries:
        raise ProposalError("%s must contain at least one file" % label)
    entries.sort(key=lambda item: item["path"])
    declared_directories: set[str] = set()
    for entry in entries:
        parent = PurePosixPath(entry["path"]).parent
        while parent.as_posix() != ".":
            declared_directories.add(parent.as_posix())
            parent = parent.parent
    if not declared_directories <= actual_directories:
        missing = sorted(declared_directories - actual_directories)
        raise ProposalError(
            "%s has missing file-derived directories: %s" % (label, missing)
        )
    total = sum(item["bytes"] for item in entries)
    if total > MAX_TREE_BYTES:
        raise ProposalError("%s exceeds the native expanded-size limit" % label)
    return {
        "schema_version": 1,
        "artifact_sha256": json_sha256(entries),
        "total_bytes": total,
        "created_at": "content-addressed",
        "entries": entries,
    }


def _ensure_output_parent(run_root: Path, relative: PurePosixPath) -> Path:
    current = run_root
    for part in relative.parts[:-1]:
        current = current / part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise ProposalError("output directory cannot be created") from exc
        try:
            identity = current.lstat()
            resolved = current.resolve(strict=True)
        except OSError as exc:
            raise ProposalError("output directory is unavailable") from exc
        if current != resolved or current.is_symlink() or not stat.S_ISDIR(identity.st_mode):
            raise ProposalError("output path contains a symlink or non-directory")
    return current


def _atomic_write(run_root: Path, relative_value: str, content: bytes) -> None:
    relative = _safe_relative(relative_value, "output path")
    parent = _ensure_output_parent(run_root, relative)
    destination = run_root.joinpath(*relative.parts)
    try:
        existing = destination.lstat()
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        raise ProposalError("output path cannot be inspected") from exc
    if existing is not None and not stat.S_ISREG(existing.st_mode):
        raise ProposalError("output path must not be a symlink or special file")
    try:
        parent_identity = parent.stat()
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".%s." % destination.name, dir=str(parent)
        )
    except OSError as exc:
        raise ProposalError("private output staging could not be created") from exc
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        current_parent = parent.stat()
        if (current_parent.st_dev, current_parent.st_ino) != (
            parent_identity.st_dev,
            parent_identity.st_ino,
        ):
            raise ProposalError("output parent changed while writing")
        os.replace(temporary, destination)
        parent_descriptor = os.open(
            str(parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except OSError as exc:
        raise ProposalError("output could not be committed atomically") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _load_stage(run_root: Path, expected_stage: str) -> dict[str, Any]:
    stage, _, identity = _read_json(
        run_root, "STAGE.json", "STAGE.json", maximum=MAX_STAGE_BYTES
    )
    if stat.S_IMODE(identity.st_mode) & 0o222:
        raise ProposalError("STAGE.json must be host-materialized read-only input")
    _fields(stage, STAGE_FIELDS, "STAGE.json")
    if type(stage["schema_version"]) is not int or stage["schema_version"] != 1:
        raise ProposalError("STAGE.json schema_version must be 1")
    if stage["kind"] != STAGE_KIND:
        raise ProposalError("STAGE.json kind is invalid")
    if (
        not isinstance(stage["product_id"], str)
        or PRODUCT_RE.fullmatch(stage["product_id"]) is None
    ):
        raise ProposalError("STAGE.json product_id is invalid")
    if stage["stage"] != expected_stage or expected_stage not in STAGES:
        raise ProposalError("STAGE.json describes another stage")
    _sha256(stage["checkpoint_sha256"], "STAGE checkpoint_sha256")
    _sha256(stage["subject_sha256"], "STAGE subject_sha256")
    allowed_transitions = (
        ("playtest", "release")
        if expected_stage == "make"
        else (FORWARD[expected_stage],)
    )
    if stage["next_transition"] not in allowed_transitions:
        raise ProposalError("STAGE.json next_transition is invalid")
    maximum = _positive_int(stage["max_rounds"], "STAGE max_rounds")
    if expected_stage in ("match", "invent"):
        if stage["round"] is not None:
            raise ProposalError("Match and Invent STAGE round must be null")
    else:
        current_round = _positive_int(stage["round"], "STAGE round")
        if current_round > maximum:
            raise ProposalError("STAGE round exceeds max_rounds")
    _mapping(stage["inputs"], "STAGE inputs", nonempty=True)
    return stage


def _validate_roster(value: Any) -> dict[str, Any]:
    roster = _fields(
        value,
        {"schema_version", "kind", "inventors", "roster_sha256"},
        "Inventor roster",
    )
    if type(roster["schema_version"]) is not int or roster["schema_version"] != 1:
        raise ProposalError("Inventor roster schema_version must be 1")
    if roster["kind"] != INVENTOR_ROSTER_KIND:
        raise ProposalError("Inventor roster kind is invalid")
    inventors = _array(
        roster["inventors"], "Inventor roster entries", nonempty=True
    )
    if len(inventors) > MAX_INVENTORS:
        raise ProposalError("Inventor roster has too many entries")
    normalized: list[dict[str, Any]] = []
    for raw in inventors:
        inventor = _fields(
            raw,
            {
                "inventor_id",
                "agent_path",
                "agent_sha256",
                "source_manifest_sha256",
                "taste_sha256",
            },
            "Inventor roster entry",
        )
        inventor_id = _inventor_id(inventor["inventor_id"], "Inventor id")
        if inventor["agent_path"] != ".codex/agents/%s.toml" % inventor_id:
            raise ProposalError("Inventor custom-agent path is invalid")
        _sha256(inventor["agent_sha256"], "Inventor custom-agent sha256")
        _sha256(
            inventor["source_manifest_sha256"],
            "Inventor source manifest sha256",
        )
        _sha256(inventor["taste_sha256"], "Inventor Taste sha256")
        normalized.append(dict(inventor))
    ids = [item["inventor_id"] for item in normalized]
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ProposalError("Inventor roster ids must be unique and sorted")
    identity = {
        "schema_version": 1,
        "kind": INVENTOR_ROSTER_KIND,
        "inventors": normalized,
    }
    if roster["roster_sha256"] != json_sha256(identity):
        raise ProposalError("Inventor roster sha256 is invalid")
    return dict(roster)


def _validate_ranking(value: Any) -> list[dict[str, str]]:
    raw_ranking = _array(value, "Match ranking", nonempty=True)
    if len(raw_ranking) > MAX_INVENTORS:
        raise ProposalError("Match ranking has too many entries")
    ranking: list[dict[str, str]] = []
    for raw in raw_ranking:
        item = _fields(raw, {"inventor_id", "rationale"}, "Match ranking entry")
        inventor_id = _inventor_id(item["inventor_id"], "ranked inventor_id")
        rationale = _bounded_text(item["rationale"], "ranking rationale", 2_000)
        ranking.append({"inventor_id": inventor_id, "rationale": rationale})
    ids = [item["inventor_id"] for item in ranking]
    if len(ids) != len(set(ids)):
        raise ProposalError("Match ranking inventor ids must be unique")
    return ranking


def _validate_assignment(value: Any) -> dict[str, Any]:
    expected = {
        "schema_version",
        "kind",
        "wish_sha256",
        "inventor_roster_sha256",
        "selected_inventor_id",
        "selected_agent_path",
        "selected_agent_sha256",
        "selected_source_manifest_sha256",
        "selected_taste_sha256",
        "blueprint_sha256",
        "ranking",
        "assignment_sha256",
    }
    assignment = _fields(value, expected, "native Match assignment")
    if type(assignment["schema_version"]) is not int or assignment["schema_version"] != 3:
        raise ProposalError("native Match assignment schema_version must be 3")
    if assignment["kind"] != MATCH_KIND:
        raise ProposalError("native Match assignment kind is invalid")
    for key in (
        "wish_sha256",
        "inventor_roster_sha256",
        "selected_agent_sha256",
        "selected_source_manifest_sha256",
        "selected_taste_sha256",
        "blueprint_sha256",
    ):
        _sha256(assignment[key], "assignment %s" % key)
    selected_id = _inventor_id(
        assignment["selected_inventor_id"], "selected inventor_id"
    )
    if assignment["selected_agent_path"] != ".codex/agents/%s.toml" % selected_id:
        raise ProposalError("selected custom-agent path is invalid")
    ranking = _validate_ranking(assignment["ranking"])
    if ranking[0]["inventor_id"] != assignment["selected_inventor_id"]:
        raise ProposalError("selected inventor must be first in the Match ranking")
    identity = {key: assignment[key] for key in expected - {"assignment_sha256"}}
    identity["ranking"] = ranking
    if assignment["assignment_sha256"] != json_sha256(identity):
        raise ProposalError("native Match assignment sha256 is invalid")
    return dict(assignment)


def _dimensions_mm(value: Any, label: str) -> list[float]:
    if not isinstance(value, Mapping) or set(value) != set(DIMENSION_KEYS):
        raise ProposalError(
            "%s must contain exactly length_mm, width_mm, and height_mm" % label
        )
    result: list[float] = []
    for key in DIMENSION_KEYS:
        item = value[key]
        if (
            isinstance(item, bool)
            or not isinstance(item, (int, float))
            or not math.isfinite(item)
            or not 0 < item <= MAX_DIMENSION_MM
        ):
            raise ProposalError(
                "%s %s must be a finite millimetre value within (0, %d]"
                % (label, key, int(MAX_DIMENSION_MM))
            )
        result.append(float(item))
    return result


def _hedged(text: str) -> Optional[str]:
    match = NUMERIC_HEDGE_RE.search(text) or QUANTITY_HEDGE_RE.search(text)
    return match.group(0) if match else None


RUN_VAULT_PATH = "VAULT.json"
RUN_VAULT_TOOL_PATH = ".agents/skills/design-vault/vault_tools.py"


def _design_vault(run_root: Path):
    """Load the host-written phase snapshot through the design-vault tool, or None.

    The host writes ``VAULT.json`` before every Invent, Make, and Playtest
    phase; a stage without one finalizes without vault rules.  A snapshot
    that is present but unreadable, or whose tool is missing, is a broken run
    tree, not a legacy run.
    """

    vault_path = run_root / RUN_VAULT_PATH
    tool_path = run_root / RUN_VAULT_TOOL_PATH
    if not vault_path.is_file() and not vault_path.is_symlink():
        return None
    if vault_path.is_symlink() or tool_path.is_symlink() or not tool_path.is_file():
        raise ProposalError("design vault snapshot or tool is missing from the run")
    import importlib.util

    spec = importlib.util.spec_from_file_location("workshop_run_vault_tools", tool_path)
    if spec is None or spec.loader is None:  # pragma: no cover - a .py path always loads
        raise ProposalError("design vault tool cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        return module, module.PackedVault.load(vault_path)
    except module.VaultToolError as exc:
        raise ProposalError("design vault snapshot is invalid: %s" % exc) from exc


def _assert_concept_vault_compatible(run_root: Path, concept: Mapping[str, Any]) -> None:
    loaded = _design_vault(run_root)
    if loaded is None:
        return
    module, vault = loaded
    try:
        module.assert_concept_compatible(vault, concept)
    except module.VaultToolError as exc:
        raise ProposalError("Invent concept is refused by the design vault: %s" % exc) from exc


def _validate_concept_contract(concept: Mapping[str, Any]) -> None:
    """Deterministic buildability checks on an Invent concept (schema 4).

    Every rule here is one an agent asked to self-check its own concept will
    report as satisfied: unbound quantities, orphaned mates, decoration parts,
    a missing or duplicated signature part, and parts larger than the envelope.
    """

    missing = sorted(CONCEPT_CONTRACT_FIELDS - set(concept))
    if missing:
        raise ProposalError(
            "Invented concept lacks required contract fields: %s" % ", ".join(missing)
        )
    _bounded_text(concept["title"], "Invented concept title", 2_000)
    _bounded_text(concept["summary"], "Invented concept summary", 2_000)
    interaction = _bounded_text(
        concept["interaction"], "Invented concept interaction", 4_000
    ).casefold()
    envelope = sorted(_dimensions_mm(concept["envelope_mm"], "Invented concept envelope_mm"))
    mechanisms = _array(concept["mechanisms"], "Invented concept mechanisms")
    if (
        len(mechanisms) > MAX_CONCEPT_MECHANISMS
        or any(
            not isinstance(item, str) or CONCEPT_SLUG_RE.fullmatch(item) is None
            for item in mechanisms
        )
        or len(set(mechanisms)) != len(mechanisms)
    ):
        raise ProposalError(
            "Invented concept mechanisms must be at most %d unique slugs"
            % MAX_CONCEPT_MECHANISMS
        )
    components = _array(concept["components"], "Invented concept components", nonempty=True)
    if len(components) > MAX_CONCEPT_COMPONENTS:
        raise ProposalError(
            "Invented concept components exceed %d entries" % MAX_CONCEPT_COMPONENTS
        )
    parsed: dict[str, dict[str, Any]] = {}
    for raw in components:
        item = _fields(raw, COMPONENT_CONTRACT_FIELDS, "Invented component")
        key = item["key"]
        if (
            not isinstance(key, str)
            or CONCEPT_SLUG_RE.fullmatch(key) is None
            or key in parsed
        ):
            raise ProposalError("Invented component key must be a unique slug")
        name = _bounded_text(item["name"], "Invented component %s name" % key, 200)
        for field_name in HEDGED_COMPONENT_FIELDS:
            text = _bounded_text(
                item[field_name], "Invented component %s %s" % (key, field_name), 4_000
            )
            hedge = _hedged(text)
            if hedge is not None:
                raise ProposalError(
                    "Invented component %s %s uses an unbound quantity %r; "
                    "state the number (unbound)" % (key, field_name, hedge)
                )
        dims = sorted(
            _dimensions_mm(item["dimensions_mm"], "Invented component %s dimensions_mm" % key)
        )
        if any(dim > limit for dim, limit in zip(dims, envelope)):
            raise ProposalError(
                "Invented component %s exceeds the concept envelope (envelope)" % key
            )
        if type(item["signature"]) is not bool:
            raise ProposalError("Invented component %s signature must be boolean" % key)
        mates = _array(item["mates_with"], "Invented component %s mates_with" % key)
        parsed[key] = {"name": name, "mates": mates, "signature": item["signature"]}
    for key, component in parsed.items():
        mates = component["mates"]
        if len(set(mates)) != len(mates) or any(
            not isinstance(mate, str) or mate == key or mate not in parsed
            for mate in mates
        ):
            raise ProposalError(
                "Invented component %s mates_with must name other existing "
                "components exactly once (component-orphan)" % key
            )
    signatures = [key for key, component in parsed.items() if component["signature"]]
    if len(signatures) != 1:
        raise ProposalError(
            "Invented concept must flag exactly one signature component, found %d "
            "(signature)" % len(signatures)
        )
    mated: set[str] = set()
    for key, component in parsed.items():
        if component["mates"]:
            mated.add(key)
            mated.update(component["mates"])
    for key, component in parsed.items():
        spoken = (key, key.replace("_", " ").replace("-", " "), component["name"].casefold())
        if key not in mated and not any(term in interaction for term in spoken):
            raise ProposalError(
                "Invented component %s is decoration: nothing mates with it and "
                "the interaction never uses it (decoration)" % key
            )


def _validate_build_plan(concept: Mapping[str, Any]) -> list[dict[str, Any]]:
    """A complete partition of components into build groups (schema 5)."""

    plan = _array(concept.get("build_plan"), "Invented concept build_plan", nonempty=True)
    if len(plan) > MAX_BUILD_GROUPS:
        raise ProposalError("Invented concept build_plan exceeds %d groups" % MAX_BUILD_GROUPS)
    components = {item["key"]: item for item in concept["components"]}
    placed: dict[str, int] = {}
    groups: list[dict[str, Any]] = []
    for index, raw in enumerate(plan):
        group = _fields(raw, BUILD_GROUP_FIELDS, "Invented build group")
        name = group["group"]
        if (
            not isinstance(name, str)
            or CONCEPT_SLUG_RE.fullmatch(name) is None
            or any(item["group"] == name for item in groups)
        ):
            raise ProposalError("Invented build group name must be a unique slug")
        _bounded_text(group["exit_criteria"], "Invented build group %s exit_criteria" % name, 2_000)
        parts = _array(group["parts"], "Invented build group %s parts" % name, nonempty=True)
        for part in parts:
            if not isinstance(part, str) or part not in components:
                raise ProposalError(
                    "Invented build group %s names an unknown component %r (build-plan)"
                    % (name, part)
                )
            if part in placed:
                raise ProposalError(
                    "Invented component %s is placed in more than one build group (build-plan)"
                    % part
                )
            placed[part] = index
        groups.append({"group": name, "parts": list(parts), "exit_criteria": group["exit_criteria"]})
    missing = sorted(set(components) - set(placed))
    if missing:
        raise ProposalError(
            "Invented build_plan leaves components unplaced: %s (build-plan)" % ", ".join(missing)
        )
    return groups


def _validate_invented(value: Any, assignment: Mapping[str, Any]) -> dict[str, Any]:
    expected = {
        "schema_version",
        "kind",
        "wish_sha256",
        "assignment_sha256",
        "taste_sha256",
        "blueprint_sha256",
        "concept",
        "concept_sha256",
        "research",
        "research_sha256",
        "invented_sha256",
    }
    invented = _fields(value, expected, "Invented")
    if (
        type(invented["schema_version"]) is not int
        or invented["schema_version"] not in INVENTED_SCHEMA_VERSIONS
    ):
        raise ProposalError("Invented schema_version must be 3, 4, or 5")
    if invented["kind"] != INVENTED_KIND:
        raise ProposalError("Invented kind is invalid")
    concept = _mapping(invented["concept"], "Invented concept", nonempty=True)
    research = _mapping(invented["research"], "Invented research", nonempty=True)
    if invented["schema_version"] >= 4:
        _validate_concept_contract(concept)
        if invented["schema_version"] >= 5:
            _validate_build_plan(concept)
    else:
        _bounded_text(concept.get("title"), "Invented concept title", 2_000)
        _bounded_text(concept.get("summary"), "Invented concept summary", 2_000)
    if invented["concept_sha256"] != json_sha256(concept):
        raise ProposalError("Invented concept_sha256 is invalid")
    if invented["research_sha256"] != json_sha256(research):
        raise ProposalError("Invented research_sha256 is invalid")
    bindings = {
        "wish_sha256": assignment["wish_sha256"],
        "assignment_sha256": assignment["assignment_sha256"],
        "taste_sha256": assignment["selected_taste_sha256"],
        "blueprint_sha256": assignment["blueprint_sha256"],
    }
    if any(invented[key] != expected_value for key, expected_value in bindings.items()):
        raise ProposalError("Invented belongs to another Match assignment")
    identity = {key: invented[key] for key in expected - {"invented_sha256"}}
    if invented["invented_sha256"] != json_sha256(identity):
        raise ProposalError("Invented sha256 is invalid")
    return dict(invented)


def _validate_manifest(value: Any, label: str) -> dict[str, Any]:
    manifest = _fields(
        value,
        {"schema_version", "artifact_sha256", "total_bytes", "created_at", "entries"},
        label,
    )
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise ProposalError("%s schema_version must be 1" % label)
    if manifest["created_at"] != "content-addressed":
        raise ProposalError("%s must use content-addressed created_at" % label)
    entries = _array(manifest["entries"], label + " entries", nonempty=True)
    normalized: list[dict[str, Any]] = []
    for raw in entries:
        entry = _fields(
            raw,
            {"path", "bytes", "sha256", "executable"},
            label + " entry",
        )
        relative = _safe_relative(entry["path"], label + " entry path")
        if _path_has_artifact_debris(relative):
            raise ProposalError("%s contains editor, backup, or patch debris" % label)
        if type(entry["bytes"]) is not int or not 0 <= entry["bytes"] <= MAX_FILE_BYTES:
            raise ProposalError("%s entry byte count is invalid" % label)
        _sha256(entry["sha256"], label + " entry sha256")
        if type(entry["executable"]) is not bool:
            raise ProposalError("%s entry executable must be boolean" % label)
        normalized.append(dict(entry))
    paths = [item["path"] for item in normalized]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ProposalError("%s entries must be unique and sorted" % label)
    total = sum(item["bytes"] for item in normalized)
    if manifest["total_bytes"] != total or total > MAX_TREE_BYTES:
        raise ProposalError("%s total_bytes is invalid" % label)
    if manifest["artifact_sha256"] != json_sha256(normalized):
        raise ProposalError("%s artifact_sha256 is invalid" % label)
    return dict(manifest)


def _validate_made(value: Any) -> dict[str, Any]:
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
    made = _fields(value, expected, "native Made")
    if type(made["schema_version"]) is not int or made["schema_version"] != 1:
        raise ProposalError("native Made schema_version must be 1")
    if made["kind"] != MADE_KIND:
        raise ProposalError("native Made kind is invalid")
    round_index = _positive_int(made["round"], "native Made round")
    for key in (
        "wish_sha256",
        "assignment_sha256",
        "taste_sha256",
        "blueprint_sha256",
        "invented_sha256",
        "product_json_sha256",
        "cad_verification_sha256",
    ):
        _sha256(made[key], "native Made %s" % key)
    if made["product_root"] != "artifacts/make/r%04d/product" % round_index:
        raise ProposalError("native Made product_root is not canonical")
    _safe_relative(made["cad_project_path"], "native Made cad_project_path")
    _safe_relative(made["cad_verification_path"], "native Made verification path")
    _validate_manifest(made["product_manifest"], "native Made product manifest")
    _mapping(made["product"], "native Made product", nonempty=True)
    identity = {key: made[key] for key in expected - {"made_sha256"}}
    if made["made_sha256"] != json_sha256(identity):
        raise ProposalError("native Made sha256 is invalid")
    return dict(made)


def _match_contract(stage: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    inputs = _required_fields(
        stage["inputs"],
        {"wish_sha256", "inventor_roster", "blueprint_sha256"},
        "Match STAGE inputs",
    )
    wish_sha256 = _sha256(inputs["wish_sha256"], "Match Wish sha256")
    roster = _validate_roster(inputs["inventor_roster"])
    blueprint_sha256 = _sha256(
        inputs["blueprint_sha256"], "Match blueprint sha256"
    )
    authored = _fields(
        source, {"selected_inventor_id", "ranking"}, "Match authored source"
    )
    selected_id = _inventor_id(
        authored["selected_inventor_id"], "selected inventor_id"
    )
    ranking = _validate_ranking(authored["ranking"])
    roster_ids = [item["inventor_id"] for item in roster["inventors"]]
    ranked_ids = [item["inventor_id"] for item in ranking]
    if len(ranked_ids) != len(roster_ids) or set(ranked_ids) != set(roster_ids):
        raise ProposalError("Match ranking must cover the immutable roster exactly")
    if ranking[0]["inventor_id"] != selected_id:
        raise ProposalError("selected inventor must be first in the Match ranking")
    selected = next(
        item for item in roster["inventors"] if item["inventor_id"] == selected_id
    )
    identity = {
        "schema_version": 3,
        "kind": MATCH_KIND,
        "wish_sha256": wish_sha256,
        "inventor_roster_sha256": roster["roster_sha256"],
        "selected_inventor_id": selected_id,
        "selected_agent_path": selected["agent_path"],
        "selected_agent_sha256": selected["agent_sha256"],
        "selected_source_manifest_sha256": selected[
            "source_manifest_sha256"
        ],
        "selected_taste_sha256": selected["taste_sha256"],
        "blueprint_sha256": blueprint_sha256,
        "ranking": ranking,
    }
    return {**identity, "assignment_sha256": json_sha256(identity)}


def _invent_contract(
    run_root: Path, stage: Mapping[str, Any], source: Mapping[str, Any]
) -> dict[str, Any]:
    inputs = _required_fields(
        stage["inputs"], {"assignment"}, "Invent STAGE inputs"
    )
    assignment = _validate_assignment(inputs["assignment"])
    return _invent_contract_for_assignment(run_root, assignment, source)


def _invent_contract_for_assignment(
    run_root: Path, assignment: Mapping[str, Any], source: Mapping[str, Any]
) -> dict[str, Any]:
    assignment = _validate_assignment(assignment)
    authored = _fields(source, {"concept", "research"}, "Invent authored source")
    concept = _mapping(authored["concept"], "Invent concept", nonempty=True)
    research = _mapping(authored["research"], "Invent research", nonempty=True)
    _validate_concept_contract(concept)
    _validate_build_plan(concept)
    _assert_concept_vault_compatible(run_root, concept)
    identity = {
        "schema_version": 5,
        "kind": INVENTED_KIND,
        "wish_sha256": assignment["wish_sha256"],
        "assignment_sha256": assignment["assignment_sha256"],
        "taste_sha256": assignment["selected_taste_sha256"],
        "blueprint_sha256": assignment["blueprint_sha256"],
        "concept": concept,
        "concept_sha256": json_sha256(concept),
        "research": research,
        "research_sha256": json_sha256(research),
    }
    result = {**identity, "invented_sha256": json_sha256(identity)}
    if len(canonical_json(result)) > MAX_JSON_BYTES:
        raise ProposalError("Invented exceeds its byte limit")
    return result


def _part_hashes(product_root: Path, concept: Mapping[str, Any]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for item in concept.get("components", ()):
        key = item["key"]
        path = product_root / PARTS_DIRECTORY / ("%s.stl" % key)
        if path.is_symlink() or not path.is_file():
            raise ProposalError("Make product tree lacks part %s at %s/%s.stl" % (key, PARTS_DIRECTORY, key))
        content = path.read_bytes()
        if not content:
            raise ProposalError("Make part %s is empty" % key)
        hashes[key] = hashlib.sha256(content).hexdigest()
    return hashes


def _validate_build_groups(concept: Mapping[str, Any], product_root: Path) -> dict[str, int]:
    """Every planned group must be sealed against the exact part files (host mirror)."""

    plan = concept.get("build_plan")
    if not isinstance(plan, (list, tuple)) or not plan:
        return {"groups": 0, "parts": 0}
    hashes = _part_hashes(product_root, concept)
    for group in plan:
        name = group["group"]
        path = product_root / GROUPS_DIRECTORY / ("%s.json" % name)
        if path.is_symlink() or not path.is_file():
            raise ProposalError(
                "Make build group %s has no sealed outcome; run make-group --group %s first"
                % (name, name)
            )
        try:
            document = json.loads(path.read_bytes().decode("utf-8"), object_pairs_hook=_strict_object)
        except (UnicodeError, ValueError) as exc:
            raise ProposalError("Make build group %s outcome is not strict JSON" % name) from exc
        if not isinstance(document, dict) or set(document) != {
            "schema_version", "kind", "group", "parts", "files"
        }:
            raise ProposalError("Make build group %s outcome fields are invalid" % name)
        if (
            document["schema_version"] != 1
            or document["kind"] != MAKE_GROUP_KIND
            or document["group"] != name
            or document["parts"] != list(group["parts"])
        ):
            raise ProposalError("Make build group %s outcome does not match the sealed plan" % name)
        files = document["files"]
        if not isinstance(files, dict) or set(files) != set(group["parts"]):
            raise ProposalError("Make build group %s outcome must hash exactly its parts" % name)
        stale = sorted(key for key in group["parts"] if files[key] != hashes[key])
        if stale:
            raise ProposalError(
                "Make build group %s was sealed against different part bytes: %s; "
                "re-run make-group --group %s" % (name, ", ".join(stale), name)
            )
    return {"groups": len(plan), "parts": len(hashes)}


def _spark_creative_contracts(
    run_root: Path, stage: Mapping[str, Any], source_value: str | None
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Seal the Spark Make turn's own Match assignment and Invented contract."""

    if not source_value:
        raise ProposalError("Spark Make requires --source creative JSON")
    source, _, _ = _read_json(run_root, source_value, "Spark Make authored source")
    authored = _fields(
        source,
        {"selected_inventor_id", "ranking", "concept", "research"},
        "Spark Make authored source",
    )
    assignment = _match_contract(
        stage,
        {
            "selected_inventor_id": authored["selected_inventor_id"],
            "ranking": authored["ranking"],
        },
    )
    invented = _invent_contract_for_assignment(
        run_root,
        assignment,
        {"concept": authored["concept"], "research": authored["research"]},
    )
    return assignment, invented


def _make_group(
    run_root: Path,
    stage: Mapping[str, Any],
    *,
    product_root_value: str,
    group_name: str,
    assignment_value: Mapping[str, Any] | None = None,
    invented_value: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Seal one build group: its parts exist and their exact bytes are recorded."""

    inputs = _mapping(stage["inputs"], "Make STAGE inputs", nonempty=True)
    if assignment_value is None or invented_value is None:
        required = _required_fields(inputs, {"assignment", "invented"}, "Make STAGE inputs")
        assignment_value = required["assignment"]
        invented_value = required["invented"]
    assignment = _validate_assignment(assignment_value)
    invented = _validate_invented(invented_value, assignment)
    concept = invented["concept"]
    plan = concept.get("build_plan") if invented["schema_version"] >= 5 else None
    if not plan:
        raise ProposalError("this Invent contract declares no build_plan; seal Make directly")
    expected_root = "artifacts/make/r%04d/product" % stage["round"]
    if product_root_value != expected_root:
        raise ProposalError("Make product root must be %s" % expected_root)
    _, product_root = _existing_directory(run_root, product_root_value, "Make product root")
    group = next((item for item in plan if item["group"] == group_name), None)
    if group is None:
        raise ProposalError("build group %r is not in the sealed build_plan" % group_name)
    files: dict[str, str] = {}
    for key in group["parts"]:
        path = product_root / PARTS_DIRECTORY / ("%s.stl" % key)
        if path.is_symlink() or not path.is_file():
            raise ProposalError(
                "build group %s part %s is missing at %s/%s.stl" % (group_name, key, PARTS_DIRECTORY, key)
            )
        content = path.read_bytes()
        if not content:
            raise ProposalError("build group %s part %s is empty" % (group_name, key))
        files[key] = hashlib.sha256(content).hexdigest()
    document = {
        "schema_version": 1,
        "kind": MAKE_GROUP_KIND,
        "group": group_name,
        "parts": list(group["parts"]),
        "files": files,
    }
    target = product_root / GROUPS_DIRECTORY / ("%s.json" % group_name)
    target.parent.mkdir(exist_ok=True)
    target.write_bytes(canonical_json(document))
    return {
        "group": group_name,
        "outcome_path": "%s/%s/%s.json" % (product_root_value, GROUPS_DIRECTORY, group_name),
        "files": files,
        "exit_criteria": group["exit_criteria"],
    }

def _validate_make_product_render(project: Path) -> None:
    """Require one explicit, inspectable presentation render from Make.

    Geometry comparison masks are intentionally grayscale.  Requiring a
    chromatic RGB/RGBA image at the exact ``snap/iso.png`` path keeps those
    diagnostic images from silently becoming the public product hero while
    leaving creative composition and palette choices with the native agent.
    """
    render = project / "snap" / "iso.png"
    try:
        identity = render.lstat()
        resolved = render.resolve(strict=True)
    except OSError as exc:
        raise ProposalError(
            "Make requires a product render at <cad-project>/snap/iso.png"
        ) from exc
    if render != resolved or render.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise ProposalError("Make product render must be a real in-project file")
    try:
        from PIL import Image

        with Image.open(render) as image:
            image.verify()
        with Image.open(render) as image:
            if image.format != "PNG":
                raise ProposalError("Make product render must be a PNG")
            width, height = image.size
            if not (800 <= width <= 4096 and 800 <= height <= 4096):
                raise ProposalError(
                    "Make product render must be between 800 and 4096 pixels per side"
                )
            if image.mode not in ("RGB", "RGBA"):
                raise ProposalError(
                    "Make product render must be RGB/RGBA, not a diagnostic grayscale image"
                )
            sampled = image.convert("RGB").resize((64, 64))
            pixels = tuple(sampled.getdata())
    except ProposalError:
        raise
    except Exception as exc:
        raise ProposalError("Make product render is not a valid PNG") from exc
    chromatic = sum(max(pixel) - min(pixel) >= 10 for pixel in pixels)
    if chromatic < 32 or len(set(pixels)) < 16:
        raise ProposalError(
            "Make product render must be a chromatic presentation image with useful tonal variation"
        )


def _make_contract(
    run_root: Path,
    stage: Mapping[str, Any],
    *,
    product_root_value: str,
    cad_project_path: str,
    cad_verification_path: str,
    assignment_value: Mapping[str, Any] | None = None,
    invented_value: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    inputs = _mapping(stage["inputs"], "Make STAGE inputs", nonempty=True)
    if assignment_value is None or invented_value is None:
        required = _required_fields(
            inputs, {"assignment", "invented"}, "Make STAGE inputs"
        )
        assignment_value = required["assignment"]
        invented_value = required["invented"]
    assignment = _validate_assignment(assignment_value)
    invented = _validate_invented(invented_value, assignment)
    round_index = stage["round"]
    expected_root = "artifacts/make/r%04d/product" % round_index
    if product_root_value != expected_root:
        raise ProposalError("Make product root must be %s" % expected_root)
    _, product_root = _existing_directory(
        run_root, product_root_value, "Make product root"
    )
    project_relative = _safe_relative(cad_project_path, "CAD project path")
    project = product_root.joinpath(*project_relative.parts)
    try:
        project_identity = project.lstat()
        project_resolved = project.resolve(strict=True)
    except OSError as exc:
        raise ProposalError("CAD project directory is unavailable") from exc
    if (
        project != project_resolved
        or project.is_symlink()
        or not stat.S_ISDIR(project_identity.st_mode)
    ):
        raise ProposalError("CAD project path must be a real in-product directory")
    _prune_derived_cad_caches(project, "Make CAD project")
    _validate_make_product_render(project)
    verification_relative = _safe_relative(
        cad_verification_path, "CAD verification path"
    )
    product_document, product_bytes, _ = _read_json(
        run_root,
        "%s/product.json" % product_root_value,
        "Make product.json",
    )
    product = _mapping(product_document, "Make product.json", nonempty=True)
    _bounded_text(product.get("title"), "Make product title", 2_000)
    _bounded_text(product.get("summary"), "Make product summary", 2_000)
    verification_sha256, _, _ = _hash_regular(
        run_root,
        "%s/%s" % (product_root_value, verification_relative.as_posix()),
        "CAD verification",
    )
    _prune_empty_directories(product_root, "Make product tree")
    manifest = _tree_manifest(run_root, product_root_value, "Make product tree")
    paths = {entry["path"] for entry in manifest["entries"]}
    if "product.json" not in paths:
        raise ProposalError("Make product manifest lacks product.json")
    if verification_relative.as_posix() not in paths:
        raise ProposalError("Make product manifest lacks CAD verification")
    if not any(path.endswith(".step") for path in paths):
        raise ProposalError("Make product manifest lacks a STEP artifact")
    if not any(path.endswith(".stl") for path in paths):
        raise ProposalError("Make product manifest lacks a printable STL")
    _validate_build_groups(invented["concept"], product_root)
    identity = {
        "schema_version": 1,
        "kind": MADE_KIND,
        "round": round_index,
        "wish_sha256": assignment["wish_sha256"],
        "assignment_sha256": assignment["assignment_sha256"],
        "taste_sha256": assignment["selected_taste_sha256"],
        "blueprint_sha256": assignment["blueprint_sha256"],
        "invented_sha256": invented["invented_sha256"],
        "product_root": product_root_value,
        "cad_project_path": project_relative.as_posix(),
        "product_manifest": manifest,
        "product": product,
        "product_json_sha256": hashlib.sha256(product_bytes).hexdigest(),
        "cad_verification_path": verification_relative.as_posix(),
        "cad_verification_sha256": verification_sha256,
    }
    return {**identity, "made_sha256": json_sha256(identity)}


def _exact_version(value: Any, label: str) -> str:
    floating = {
        "latest",
        "main",
        "master",
        "head",
        "dev",
        "development",
        "unknown",
        "snapshot",
        "x",
    }
    if (
        not isinstance(value, str)
        or VERSION_RE.fullmatch(value) is None
        or not any(character.isdigit() for character in value)
        or any(
            segment in floating
            for segment in re.split(r"[._+-]", value.casefold())
        )
    ):
        raise ProposalError("%s must be an exact non-floating version" % label)
    return value


def _utc_timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str):
        raise ProposalError("%s must be an ISO-8601 UTC timestamp" % label)
    try:
        parsed = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProposalError("%s must be an ISO-8601 UTC timestamp" % label) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.timedelta(0):
        raise ProposalError("%s must include an explicit UTC offset" % label)
    return value


def _feedback(value: Any) -> dict[str, Any]:
    item = _fields(
        value,
        {"code", "area", "severity", "finding", "change", "evidence_refs", "invalidates"},
        "Playtest feedback",
    )
    _bounded_text(item["code"], "feedback code", 200)
    _bounded_text(item["area"], "feedback area", 200)
    if item["severity"] not in ("note", "improve", "block"):
        raise ProposalError("feedback severity is invalid")
    _bounded_text(item["finding"], "feedback finding")
    _bounded_text(item["change"], "feedback change")
    refs = _array(item["evidence_refs"], "feedback evidence_refs")
    if any(not isinstance(ref, str) or not ref for ref in refs):
        raise ProposalError("feedback evidence_refs must be non-empty strings")
    invalidates = _array(item["invalidates"], "feedback invalidates", nonempty=True)
    if any(stage not in PLAYTEST_FEEDBACK_INVALIDATES for stage in invalidates):
        raise ProposalError(
            "feedback invalidates contains a stage outside the repair lifecycle"
        )
    if len(invalidates) != len(set(invalidates)):
        raise ProposalError("feedback invalidates must not contain duplicates")
    if "invent" in invalidates:
        if item["severity"] not in ("improve", "block"):
            raise ProposalError(
                "only actionable feedback may request concept revision"
            )
        if set(invalidates) != set(PLAYTEST_INVENT_INVALIDATES):
            raise ProposalError(
                "concept revision must invalidate Invent and every downstream stage"
            )
    elif tuple(invalidates) != PLAYTEST_MAKE_INVALIDATES:
        raise ProposalError(
            "Make repair feedback must invalidate playtest and release"
        )
    return dict(item)


def _playtest_transition(playtested: Mapping[str, Any]) -> str:
    """Follow the authored invalidation marker without judging feedback prose."""

    if playtested["verdict"] == "pass":
        return "release"
    if any(
        feedback["severity"] in ("improve", "block")
        and "invent" in feedback["invalidates"]
        for feedback in playtested["feedback"]
    ):
        return "invent"
    return "make"


def _make_invent_revision_feedback(value: Any) -> dict[str, Any]:
    item = _feedback(value)
    if item["severity"] != "block":
        raise ProposalError(
            "Make may return to Invent only for build-blocking feedback"
        )
    if tuple(item["invalidates"]) != MAKE_INVENT_REVISION_INVALIDATES:
        raise ProposalError(
            "Make Invent revision must invalidate Invent and every downstream stage"
        )
    if not item["evidence_refs"]:
        raise ProposalError(
            "Make Invent-revision feedback requires exact evidence_refs"
        )
    refs = [
        _safe_relative(ref, "Make Invent-revision evidence_ref").as_posix()
        for ref in item["evidence_refs"]
    ]
    if len(refs) != len(set(refs)):
        raise ProposalError(
            "Make Invent-revision feedback evidence_refs must be unique"
        )
    item["evidence_refs"] = refs
    return item


def _make_invent_revision_contract(
    run_root: Path,
    stage: Mapping[str, Any],
    source: Mapping[str, Any],
    *,
    evidence_root_value: str,
) -> dict[str, Any]:
    inputs = _required_fields(
        stage["inputs"],
        {
            "assignment",
            "invented",
            "invent_revision_allowed",
            "invent_revision_contract_path",
            "invent_revision_evidence_root",
        },
        "Make STAGE inputs",
    )
    if inputs["invent_revision_allowed"] is not True:
        raise ProposalError("this Make stage cannot return to Invent")
    assignment = _validate_assignment(inputs["assignment"])
    invented = _validate_invented(inputs["invented"], assignment)
    round_index = stage["round"]
    expected_contract = (
        "artifacts/make/r%04d/invent-revision-request.json" % round_index
    )
    if inputs["invent_revision_contract_path"] != expected_contract:
        raise ProposalError("Make Invent-revision contract path is not canonical")
    expected_root = "artifacts/make/r%04d/revision-evidence" % round_index
    if (
        inputs["invent_revision_evidence_root"] != expected_root
        or evidence_root_value != expected_root
    ):
        raise ProposalError(
            "Make Invent-revision evidence root must be %s" % expected_root
        )
    authored = _fields(source, {"feedback"}, "Make Invent-revision authored source")
    feedback = [
        _make_invent_revision_feedback(item)
        for item in _array(
            authored["feedback"],
            "Make Invent-revision feedback",
            nonempty=True,
        )
    ]
    codes = [item["code"] for item in feedback]
    if len(codes) != len(set(codes)):
        raise ProposalError("Make Invent-revision feedback codes must be unique")
    manifest = _tree_manifest(
        run_root, evidence_root_value, "Make Invent-revision evidence tree"
    )
    inventory = {entry["path"]: entry["sha256"] for entry in manifest["entries"]}
    for item in feedback:
        for ref in item["evidence_refs"]:
            if ref not in inventory:
                raise ProposalError(
                    "Make Invent-revision feedback references absent evidence: %s"
                    % ref
                )
    feedback_sha256 = json_sha256(feedback)
    identity = {
        "schema_version": 1,
        "kind": MAKE_INVENT_REVISION_KIND,
        "round": round_index,
        "wish_sha256": assignment["wish_sha256"],
        "assignment_sha256": assignment["assignment_sha256"],
        "invented_sha256": invented["invented_sha256"],
        "evidence_root": evidence_root_value,
        "evidence_manifest": manifest,
        "feedback": feedback,
        "feedback_sha256": feedback_sha256,
    }
    return {
        **identity,
        "revision_request_sha256": json_sha256(identity),
    }


def _validate_playtested(
    value: Any, made: Mapping[str, Any]
) -> dict[str, Any]:
    expected = {
        "schema_version",
        "kind",
        "round",
        "made_sha256",
        "product_artifact_sha256",
        "blueprint_sha256",
        "evidence_root",
        "evidence_manifest",
        "checks",
        "feedback",
        "verdict",
        "playtested_sha256",
    }
    playtested = _fields(value, expected, "native Playtested")
    if (
        type(playtested["schema_version"]) is not int
        or playtested["schema_version"] != 1
    ):
        raise ProposalError("native Playtested schema_version must be 1")
    if playtested["kind"] != PLAYTESTED_KIND:
        raise ProposalError("native Playtested kind is invalid")
    round_index = _positive_int(playtested["round"], "native Playtested round")
    for key in (
        "made_sha256",
        "product_artifact_sha256",
        "blueprint_sha256",
    ):
        _sha256(playtested[key], "native Playtested %s" % key)
    if playtested["evidence_root"] != (
        "artifacts/playtest/r%04d/evidence" % round_index
    ):
        raise ProposalError("native Playtested evidence_root is not canonical")
    manifest = _validate_manifest(
        playtested["evidence_manifest"], "native Playtested evidence manifest"
    )
    inventory = {entry["path"]: entry["sha256"] for entry in manifest["entries"]}
    checks: list[dict[str, Any]] = []
    for raw in _array(playtested["checks"], "native Playtested checks", nonempty=True):
        check = _fields(
            raw,
            {
                "check_id",
                "passed",
                "evaluator",
                "evaluator_version",
                "config_sha256",
                "evidence_ref",
                "evidence_sha256",
                "observed_at",
                "observations",
            },
            "native Playtested check",
        )
        if (
            not isinstance(check["check_id"], str)
            or CHECK_RE.fullmatch(check["check_id"]) is None
        ):
            raise ProposalError("native Playtested check_id is invalid")
        if type(check["passed"]) is not bool:
            raise ProposalError("native Playtested check passed must be boolean")
        evaluator = _bounded_text(
            check["evaluator"], "native Playtested evaluator", 1_000
        )
        if evaluator.casefold() in ("self-report", "trust-me"):
            raise ProposalError("native Playtested evaluator cannot be self-report")
        _exact_version(
            check["evaluator_version"], "native Playtested evaluator version"
        )
        _sha256(check["config_sha256"], "native Playtested config_sha256")
        evidence_ref = _safe_relative(
            check["evidence_ref"], "native Playtested evidence_ref"
        ).as_posix()
        _sha256(check["evidence_sha256"], "native Playtested evidence_sha256")
        if inventory.get(evidence_ref) != check["evidence_sha256"]:
            raise ProposalError("native Playtested evidence is absent or mismatched")
        _utc_timestamp(check["observed_at"], "native Playtested observed_at")
        _mapping(
            check["observations"],
            "native Playtested observations",
            nonempty=True,
        )
        checks.append(dict(check))
    check_ids = [item["check_id"] for item in checks]
    if len(check_ids) != len(set(check_ids)):
        raise ProposalError("native Playtested check ids must be unique")
    feedback = [
        _feedback(item)
        for item in _array(playtested["feedback"], "native Playtested feedback")
    ]
    if playtested["verdict"] not in ("pass", "improve", "block"):
        raise ProposalError("native Playtested verdict is invalid")
    failing = any(not item["passed"] for item in checks)
    actionable = any(item["severity"] in ("improve", "block") for item in feedback)
    if playtested["verdict"] == "pass" and (failing or actionable):
        raise ProposalError("passing native Playtested contains failures")
    if playtested["verdict"] != "pass" and (
        not feedback or not (failing or actionable)
    ):
        raise ProposalError("failed native Playtested lacks actionable evidence")
    identity = {
        key: playtested[key] for key in expected - {"playtested_sha256"}
    }
    identity["checks"] = checks
    identity["feedback"] = feedback
    if playtested["playtested_sha256"] != json_sha256(identity):
        raise ProposalError("native Playtested sha256 is invalid")
    if (
        round_index != made["round"]
        or playtested["made_sha256"] != made["made_sha256"]
        or playtested["product_artifact_sha256"]
        != made["product_manifest"]["artifact_sha256"]
        or playtested["blueprint_sha256"] != made["blueprint_sha256"]
    ):
        raise ProposalError("native Playtested belongs to another Made revision")
    return dict(playtested)


def _expected_release_claims(playtested: Mapping[str, Any]) -> dict[str, Any]:
    claims: dict[str, Any] = {}
    for check in playtested["checks"]:
        observations = check["observations"]
        evidence_class = observations.get("evidence_class", "unspecified")
        raw_claims = observations.get("claims", [])
        if isinstance(raw_claims, str):
            raw_claims = [raw_claims]
        if not isinstance(raw_claims, list) or not all(
            isinstance(item, str) and item.strip() for item in raw_claims
        ):
            raw_claims = []
        claims[check["check_id"]] = {
            "passed": check["passed"],
            "evidence_class": evidence_class,
            "claims": raw_claims,
            "evidence_ref": check["evidence_ref"],
            "evidence_sha256": check["evidence_sha256"],
            "evaluator": check["evaluator"],
            "evaluator_version": check["evaluator_version"],
        }
    if not claims:
        raise ProposalError("native Release requires non-empty Playtest claims")
    return claims


def _playtest_omission_record() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": PLAYTEST_OMISSION_KIND,
        "status": PLAYTEST_OMISSION_STATUS,
        "reason": "Playtest is deferred for this Release.",
    }


def _playtest_omission_sha256() -> str:
    return hashlib.sha256(canonical_json(_playtest_omission_record())).hexdigest()


def _direct_release_claims() -> dict[str, Any]:
    return {
        "playtest": {
            "status": PLAYTEST_OMISSION_STATUS,
            "claims": [],
            "evidence_ref": PLAYTEST_OMISSION_PATH,
            "evidence_sha256": _playtest_omission_sha256(),
        }
    }


def _release_page_text(value: Any, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or len(value) > maximum
        or any(
            ord(character) < 32 and character not in "\n\t"
            for character in value
        )
        or any(ord(character) == 127 for character in value)
    ):
        raise ProposalError("%s must be bounded substantive text" % label)
    return value


def _release_page_text_list(
    value: Any,
    label: str,
    *,
    maximum_items: int,
    maximum_item_length: int,
    allow_empty: bool = False,
) -> list[str]:
    items = _array(value, label, nonempty=not allow_empty)
    if len(items) > maximum_items:
        raise ProposalError("%s has too many items" % label)
    result = [
        _release_page_text(item, "%s item" % label, maximum_item_length)
        for item in items
    ]
    if len({item.casefold() for item in result}) != len(result):
        raise ProposalError("%s must not contain duplicate items" % label)
    return result


def _validate_release_product(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping) and value.get("schema_version") == 4:
        product = _fields(
            value, MANUAL_RELEASE_PRODUCT_FIELDS, "Release product.json"
        )
        if (
            product["kind"] != "workshop.release-package"
            or product["status"] != "manual-ready"
        ):
            raise ProposalError("Release product.json is not a manual-ready package")
        _sha256(
            product["product_artifact_sha256"],
            "Release product artifact sha256",
        )
        _sha256(
            product["playtest_evidence_artifact_sha256"],
            "Release Playtest evidence sha256",
        )
        claims = _mapping(product["claims"], "Release claims", nonempty=True)
        return {
            "schema_version": 4,
            "kind": "workshop.release-package",
            "status": "manual-ready",
            "title": _release_page_text(product["title"], "Release title", 300),
            "summary": _release_page_text(
                product["summary"], "Release summary", 2_000
            ),
            "what_arrives": _release_page_text_list(
                product["what_arrives"],
                "Release what_arrives",
                maximum_items=100,
                maximum_item_length=1_000,
            ),
            "limitations": _release_page_text_list(
                product["limitations"],
                "Release limitations",
                maximum_items=100,
                maximum_item_length=2_000,
                allow_empty=True,
            ),
            "product_artifact_sha256": product["product_artifact_sha256"],
            "playtest_evidence_artifact_sha256": product[
                "playtest_evidence_artifact_sha256"
            ],
            "claims": dict(claims),
        }
    product = _fields(
        value, DIRECT_RELEASE_PRODUCT_FIELDS, "Release product.json"
    )
    if (
        product["schema_version"] != 5
        or product["kind"] != "workshop.release-package"
        or product["status"] != "manual-ready"
        or product["playtest_status"] != PLAYTEST_OMISSION_STATUS
    ):
        raise ProposalError("Release product.json is not a manual-ready package")
    _sha256(
        product["product_artifact_sha256"],
        "Release product artifact sha256",
    )
    _sha256(
        product["playtest_evidence_artifact_sha256"],
        "Release Playtest evidence sha256",
    )
    omission_sha256 = _playtest_omission_sha256()
    if product["playtest_evidence_artifact_sha256"] != omission_sha256:
        raise ProposalError("Release product.json identifies another Playtest omission")
    claims = _mapping(product["claims"], "Release claims", nonempty=True)
    if dict(claims) != _direct_release_claims():
        raise ProposalError("Release claims must state that Playtest was not run")
    validated = {
        "schema_version": 5,
        "kind": "workshop.release-package",
        "status": "manual-ready",
        "title": _release_page_text(product["title"], "Release title", 300),
        "summary": _release_page_text(product["summary"], "Release summary", 2_000),
        "what_arrives": _release_page_text_list(
            product["what_arrives"],
            "Release what_arrives",
            maximum_items=100,
            maximum_item_length=1_000,
        ),
        "limitations": _release_page_text_list(
            product["limitations"],
            "Release limitations",
            maximum_items=100,
            maximum_item_length=2_000,
            allow_empty=True,
        ),
        "product_artifact_sha256": product["product_artifact_sha256"],
        "playtest_status": PLAYTEST_OMISSION_STATUS,
        "playtest_evidence_artifact_sha256": product[
            "playtest_evidence_artifact_sha256"
        ],
        "claims": dict(claims),
    }
    return validated


VAULT_LEAD_CHECK_ID = "agent-playtest"
VAULT_LEAD_VERDICTS = ("confirmed", "dismissed")
MAX_VAULT_LEAD_WHY = 1_000
LEAD_ID_RE = re.compile(r"^[0-9a-f]{16}$")


def _validate_vault_lead_answers(
    leads: Sequence[Mapping[str, Any]],
    checks: Sequence[Mapping[str, Any]],
    feedback: Sequence[Mapping[str, Any]],
) -> dict[str, int]:
    """Every issued design-vault lead must be answered exactly once (host mirror)."""

    issued = {}
    for lead in leads:
        identifier = lead.get("id") if isinstance(lead, Mapping) else None
        if not isinstance(identifier, str) or LEAD_ID_RE.fullmatch(identifier) is None:
            raise ProposalError("issued vault lead id is invalid")
        issued[identifier] = lead
    answers: list[Any] = []
    for check in checks:
        if check.get("check_id") == VAULT_LEAD_CHECK_ID:
            raw = (check.get("observations") or {}).get("vault_leads", [])
            if not isinstance(raw, (list, tuple)):
                raise ProposalError("vault_leads answers must be a list")
            answers = list(raw)
    if not issued:
        if answers:
            raise ProposalError("Playtest answers vault leads that were never issued")
        return {"answered": 0, "confirmed": 0, "dismissed": 0}
    codes = {item.get("code") for item in feedback if isinstance(item, Mapping)}
    seen: set[str] = set()
    confirmed = 0
    for answer in answers:
        if not isinstance(answer, Mapping) or set(answer) != {
            "lead",
            "verdict",
            "why",
            "feedback_code",
        }:
            raise ProposalError("vault lead answers need exactly lead, verdict, why, feedback_code")
        identifier = answer["lead"]
        if identifier not in issued:
            raise ProposalError(
                "vault lead answer names a lead that was not issued: %r" % (identifier,)
            )
        if identifier in seen:
            raise ProposalError("vault lead %s is answered more than once" % identifier)
        seen.add(identifier)
        if answer["verdict"] not in VAULT_LEAD_VERDICTS:
            raise ProposalError("vault lead %s verdict must be confirmed or dismissed" % identifier)
        why = answer["why"]
        if not isinstance(why, str) or not why.strip() or len(why) > MAX_VAULT_LEAD_WHY:
            raise ProposalError("vault lead %s needs a bounded non-empty why" % identifier)
        code = answer["feedback_code"]
        if answer["verdict"] == "confirmed":
            if not isinstance(code, str) or code not in codes:
                raise ProposalError(
                    "confirmed vault lead %s must name an existing feedback code" % identifier
                )
            confirmed += 1
        elif code is not None:
            raise ProposalError("dismissed vault lead %s must not name feedback" % identifier)
    missing = sorted(set(issued) - seen)
    if missing:
        raise ProposalError("Playtest left vault leads unanswered: %s" % ", ".join(missing))
    return {"answered": len(seen), "confirmed": confirmed, "dismissed": len(seen) - confirmed}


SCORE_READ_FIELDS = frozenset(("reader", "scores", "one_change"))
MAX_SCORE_READS = 16
MAX_SCORE_ONE_CHANGE = 1_000


def _median(values: Sequence[int]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return (ordered[middle - 1] + ordered[middle]) / 2.0


def _score_summary(
    dimensions: Sequence[str],
    checks: Sequence[Mapping[str, Any]],
    *,
    minimum_reads: int,
    maximum: int = 10,
) -> dict[str, Any]:
    """Median and spread of the agent-playtest reads (host mirror)."""

    dims = tuple(dimensions)
    if not dims or len(set(dims)) != len(dims):
        raise ProposalError("score dimensions must be unique and non-empty")
    reads: Any = None
    for check in checks:
        if check.get("check_id") == VAULT_LEAD_CHECK_ID:
            reads = (check.get("observations") or {}).get("reads")
    if not isinstance(reads, (list, tuple)):
        raise ProposalError("agent-playtest observations must carry a reads list")
    if not minimum_reads <= len(reads) <= MAX_SCORE_READS:
        raise ProposalError(
            "agent-playtest needs %d to %d independent reads" % (minimum_reads, MAX_SCORE_READS)
        )
    readers: set[str] = set()
    per_dimension: dict[str, list[int]] = {dim: [] for dim in dims}
    changes: list[str] = []
    for read in reads:
        if not isinstance(read, Mapping) or set(read) != SCORE_READ_FIELDS:
            raise ProposalError("each read needs exactly reader, scores, and one_change")
        reader = read["reader"]
        if not isinstance(reader, str) or not reader.strip() or reader in readers:
            raise ProposalError("each read needs a distinct non-empty reader name")
        readers.add(reader)
        scores = read["scores"]
        if not isinstance(scores, Mapping) or set(scores) != set(dims):
            raise ProposalError("read %r must score exactly the issued dimensions" % reader)
        for dim in dims:
            value = scores[dim]
            if isinstance(value, bool) or type(value) is not int or not 0 <= value <= maximum:
                raise ProposalError(
                    "read %r scores %s outside 0..%d" % (reader, dim, maximum)
                )
            per_dimension[dim].append(value)
        change = read["one_change"]
        if not isinstance(change, str) or not change.strip() or len(change) > MAX_SCORE_ONE_CHANGE:
            raise ProposalError("read %r needs a bounded non-empty one_change" % reader)
        changes.append(change.strip())
    return {
        "reads": len(reads),
        "median": {dim: _median(per_dimension[dim]) for dim in dims},
        "spread": {dim: max(per_dimension[dim]) - min(per_dimension[dim]) for dim in dims},
        "one_change": changes,
    }


def _assert_scored(inputs: Mapping[str, Any], checks: Sequence[Mapping[str, Any]], verdict: str) -> None:
    if "score_dimensions" not in inputs:
        return
    dimensions = _array(inputs["score_dimensions"], "Playtest STAGE score_dimensions", nonempty=True)
    floor = _positive_int(inputs.get("score_floor"), "Playtest STAGE score_floor", 10)
    minimum = _positive_int(inputs.get("score_minimum_reads"), "Playtest STAGE score_minimum_reads", 16)
    summary = _score_summary(dimensions, checks, minimum_reads=minimum)
    if verdict == "pass":
        low = sorted(dim for dim, value in summary["median"].items() if value < floor)
        if low:
            raise ProposalError(
                "passing Playtest medians sit below the floor of %d: %s" % (floor, ", ".join(low))
            )
def _manual_design_text_list(
    value: Any,
    label: str,
    *,
    minimum_items: int,
    maximum_items: int,
    minimum_length: int = 2,
    maximum_length: int = 500,
) -> list[str]:
    items = _array(value, label, nonempty=True)
    if not minimum_items <= len(items) <= maximum_items:
        raise ProposalError("%s has an invalid item count" % label)
    result = [
        _release_page_text(item, "%s item" % label, maximum_length)
        for item in items
    ]
    if any(len(item) < minimum_length for item in result):
        raise ProposalError("%s items are not substantive" % label)
    if len({item.casefold() for item in result}) != len(result):
        raise ProposalError("%s must not contain duplicates" % label)
    return result


def _pdf_object(value: Any) -> Any:
    return value.get_object() if hasattr(value, "get_object") else value


def _manual_font_is_embedded(raw_font: Any) -> bool:
    font = _pdf_object(raw_font)
    if not isinstance(font, Mapping):
        return False
    if str(font.get("/Subtype")) == "/Type3":
        return True
    if str(font.get("/Subtype")) == "/Type0":
        descendants = _pdf_object(font.get("/DescendantFonts"))
        return (
            isinstance(descendants, Sequence)
            and bool(descendants)
            and all(_manual_font_is_embedded(item) for item in descendants)
        )
    descriptor = _pdf_object(font.get("/FontDescriptor"))
    return isinstance(descriptor, Mapping) and any(
        descriptor.get(name) is not None
        for name in ("/FontFile", "/FontFile2", "/FontFile3")
    )


def _manual_pages_and_embedded_fonts(manual: bytes) -> int:
    try:
        from pypdf import PdfReader

        pages = list(PdfReader(io.BytesIO(manual), strict=True).pages)
    except Exception as exc:
        raise ProposalError(
            "Release MANUAL.pdf cannot be inspected for design evidence"
        ) from exc
    missing = set()
    observed = 0
    visited: set[int] = set()

    def inspect_resources(raw_resources: Any) -> None:
        nonlocal observed
        resources = _pdf_object(raw_resources)
        if not isinstance(resources, Mapping) or id(resources) in visited:
            return
        visited.add(id(resources))
        fonts = _pdf_object(resources.get("/Font"))
        if isinstance(fonts, Mapping):
            for resource_name, raw_font in fonts.items():
                observed += 1
                font = _pdf_object(raw_font)
                if not _manual_font_is_embedded(font):
                    missing.add(
                        str(font.get("/BaseFont"))
                        if isinstance(font, Mapping)
                        else str(resource_name)
                    )
        xobjects = _pdf_object(resources.get("/XObject"))
        if isinstance(xobjects, Mapping):
            for raw_xobject in xobjects.values():
                xobject = _pdf_object(raw_xobject)
                if isinstance(xobject, Mapping):
                    inspect_resources(xobject.get("/Resources"))

    for page in pages:
        inspect_resources(page.get("/Resources"))
    if not pages or observed < 1:
        raise ProposalError("Release MANUAL.pdf has no inspectable fonts")
    if missing:
        raise ProposalError(
            "Release MANUAL.pdf must embed every used font: %s"
            % ", ".join(sorted(missing))
        )
    return len(pages)


def _manual_design_required(inputs: Mapping[str, Any]) -> bool:
    release_contract = inputs.get("release_contract")
    if release_contract is None:
        return False
    contract = _mapping(release_contract, "Release protocol")
    path = contract.get("manual_design_evidence_path")
    version = contract.get("manual_design_evidence_schema_version")
    if path is None and version is None:
        return False
    if path != MANUAL_DESIGN_EVIDENCE_PATH or version != 1:
        raise ProposalError("Release manual design evidence protocol is invalid")
    return True


def _validate_manual_design_evidence(
    run_root: Path,
    *,
    package_root_value: str,
    inventory: Mapping[str, Mapping[str, Any]],
    manual: bytes,
    made: Mapping[str, Any],
    required: bool,
) -> None:
    if not required:
        return
    entry = inventory.get(MANUAL_DESIGN_EVIDENCE_PATH)
    if entry is None:
        raise ProposalError("Release package lacks MANUAL-DESIGN.json")
    document, content, _ = _read_json(
        run_root,
        "%s/%s" % (package_root_value, MANUAL_DESIGN_EVIDENCE_PATH),
        "Release MANUAL-DESIGN.json",
        maximum=MAX_MANUAL_DESIGN_EVIDENCE_BYTES,
    )
    if content != canonical_json(document):
        raise ProposalError("Release MANUAL-DESIGN.json must use canonical JSON")
    if hashlib.sha256(content).hexdigest() != entry["sha256"]:
        raise ProposalError("Release MANUAL-DESIGN.json changed after package hashing")
    evidence = _fields(
        document,
        {
            "schema_version",
            "kind",
            "manual_sha256",
            "design_mode",
            "creative_brief",
            "product_visuals",
            "review",
        },
        "Release manual design evidence",
    )
    if (
        evidence["schema_version"] != 1
        or evidence["kind"] != MANUAL_DESIGN_EVIDENCE_KIND
        or evidence["design_mode"] != "bespoke"
        or _sha256(evidence["manual_sha256"], "Release manual sha256")
        != hashlib.sha256(manual).hexdigest()
    ):
        raise ProposalError("Release manual design evidence identity is invalid")
    brief = _fields(
        evidence["creative_brief"],
        {
            "emotional_promise",
            "physical_format",
            "format_rationale",
            "visual_motif",
            "palette",
            "typography",
            "teaching_arc",
        },
        "Release manual creative brief",
    )
    for field, minimum, maximum in (
        ("emotional_promise", 20, 500),
        ("physical_format", 3, 200),
        ("format_rationale", 20, 1_000),
        ("visual_motif", 20, 500),
    ):
        value = _release_page_text(
            brief[field], "Release manual creative brief %s" % field, maximum
        )
        if len(value) < minimum:
            raise ProposalError("Release manual creative brief is not substantive")
    _manual_design_text_list(
        brief["palette"], "Release manual palette", minimum_items=3, maximum_items=8
    )
    _manual_design_text_list(
        brief["typography"],
        "Release manual typography",
        minimum_items=2,
        maximum_items=6,
    )
    _manual_design_text_list(
        brief["teaching_arc"],
        "Release manual teaching arc",
        minimum_items=3,
        maximum_items=12,
        minimum_length=8,
    )
    page_count = _manual_pages_and_embedded_fonts(manual)
    visuals = _array(
        evidence["product_visuals"], "Release manual product visuals", nonempty=True
    )
    made_entries = {
        item["path"]: item for item in made["product_manifest"]["entries"]
    }
    covered = set()
    seen = set()
    for raw_visual in visuals:
        visual = _fields(
            raw_visual,
            {"source_path", "source_sha256", "pages"},
            "Release manual product visual",
        )
        source = visual["source_path"]
        pure = PurePosixPath(source) if isinstance(source, str) else PurePosixPath(".")
        made_entry = made_entries.get(source)
        if (
            not isinstance(source, str)
            or pure.is_absolute()
            or ".." in pure.parts
            or pure.as_posix() != source
            or pure.suffix.casefold() not in MANUAL_VISUAL_SUFFIXES
            or made_entry is None
            or visual["source_sha256"] != made_entry["sha256"]
            or source in seen
        ):
            raise ProposalError("Release manual visual differs from sealed Made bytes")
        pages = _array(visual["pages"], "Release manual visual pages", nonempty=True)
        if (
            any(type(page) is not int or not 1 <= page <= page_count for page in pages)
            or pages != sorted(set(pages))
        ):
            raise ProposalError("Release manual visual page references are invalid")
        seen.add(source)
        covered.update(pages)
    if 1 not in covered:
        raise ProposalError("Release manual cover must use an exact product visual")
    review = _fields(
        evidence["review"],
        {
            "page_count",
            "color_pages",
            "grayscale_pages",
            "first_time_owner_pass",
            "independent_reviewer",
            "findings",
            "resolved_changes",
            "status",
        },
        "Release manual review",
    )
    expected_pages = list(range(1, page_count + 1))
    if (
        review["page_count"] != page_count
        or review["color_pages"] != expected_pages
        or review["grayscale_pages"] != expected_pages
        or review["first_time_owner_pass"] is not True
        or review["independent_reviewer"] != "native-subagent"
        or review["status"] != "approved"
    ):
        raise ProposalError("Release manual review is incomplete")
    _manual_design_text_list(
        review["findings"],
        "Release manual review findings",
        minimum_items=1,
        maximum_items=20,
        minimum_length=8,
        maximum_length=1_000,
    )
    _manual_design_text_list(
        review["resolved_changes"],
        "Release manual resolved changes",
        minimum_items=1,
        maximum_items=20,
        minimum_length=8,
        maximum_length=1_000,
    )


def _playtest_contract(
    run_root: Path,
    stage: Mapping[str, Any],
    source: Mapping[str, Any],
    *,
    evidence_root_value: str,
) -> dict[str, Any]:
    inputs = _required_fields(
        stage["inputs"], {"made", "required_check_ids"}, "Playtest STAGE inputs"
    )
    made = _validate_made(inputs["made"])
    if made["round"] != stage["round"]:
        raise ProposalError("Playtest round differs from Made")
    required_ids = _array(
        inputs["required_check_ids"], "required Playtest check ids", nonempty=True
    )
    for check_id in required_ids:
        if not isinstance(check_id, str) or CHECK_RE.fullmatch(check_id) is None:
            raise ProposalError("required Playtest check id is invalid")
    if len(required_ids) != len(set(required_ids)):
        raise ProposalError("required Playtest check ids must be unique")
    authored = _fields(
        source, {"checks", "feedback", "verdict"}, "Playtest authored source"
    )
    verdict = authored["verdict"]
    if verdict not in ("pass", "improve", "block"):
        raise ProposalError("Playtest verdict is invalid")
    round_index = stage["round"]
    expected_root = "artifacts/playtest/r%04d/evidence" % round_index
    if evidence_root_value != expected_root:
        raise ProposalError("Playtest evidence root must be %s" % expected_root)
    manifest = _tree_manifest(run_root, evidence_root_value, "Playtest evidence tree")
    inventory = {entry["path"]: entry["sha256"] for entry in manifest["entries"]}
    checks: list[dict[str, Any]] = []
    for raw in _array(authored["checks"], "Playtest checks", nonempty=True):
        check = _fields(
            raw,
            {
                "check_id",
                "passed",
                "evaluator",
                "evaluator_version",
                "config_ref",
                "evidence_ref",
                "observed_at",
                "observations",
            },
            "Playtest check",
        )
        check_id = check["check_id"]
        if not isinstance(check_id, str) or CHECK_RE.fullmatch(check_id) is None:
            raise ProposalError("Playtest check_id is invalid")
        if type(check["passed"]) is not bool:
            raise ProposalError("Playtest check passed must be boolean")
        evaluator = _bounded_text(check["evaluator"], "Playtest evaluator", 1_000)
        if evaluator.casefold() in ("self-report", "trust-me"):
            raise ProposalError("Playtest evaluator cannot be a self-report")
        evaluator_version = _exact_version(
            check["evaluator_version"], "Playtest evaluator version"
        )
        config_ref = _safe_relative(check["config_ref"], "Playtest config_ref").as_posix()
        evidence_ref = _safe_relative(
            check["evidence_ref"], "Playtest evidence_ref"
        ).as_posix()
        if config_ref not in inventory or evidence_ref not in inventory:
            raise ProposalError("Playtest check references a file outside its evidence tree")
        if "effort" in inputs:
            expected_config_ref = "configs/%s.json" % check_id
            if config_ref != expected_config_ref:
                raise ProposalError(
                    "Playtest check config_ref must be %s" % expected_config_ref
                )
            config, config_content, _ = _read_json(
                run_root,
                "%s/%s" % (evidence_root_value, config_ref),
                "Playtest %s config" % check_id,
            )
            binding_keys = tuple(
                key
                for key in ("artifact_sha256", "product_artifact_sha256")
                if key in config
            )
            expected_artifact_sha256 = made["product_manifest"]["artifact_sha256"]
            if (
                hashlib.sha256(config_content).hexdigest()
                != inventory[config_ref]
                or config.get("schema_version") != 1
                or config.get("check_id") != check_id
                or ("seed" in config and type(config["seed"]) is not int)
                or not binding_keys
                or any(
                    not isinstance(config[key], str)
                    or config[key] != expected_artifact_sha256
                    for key in binding_keys
                )
            ):
                raise ProposalError(
                    "Playtest config is not bound to the current Made revision: %s"
                    % check_id
                )
        observations = _mapping(
            check["observations"], "Playtest observations", nonempty=True
        )
        checks.append(
            {
                "check_id": check_id,
                "passed": check["passed"],
                "evaluator": evaluator,
                "evaluator_version": evaluator_version,
                "config_sha256": inventory[config_ref],
                "evidence_ref": evidence_ref,
                "evidence_sha256": inventory[evidence_ref],
                "observed_at": _utc_timestamp(
                    check["observed_at"], "Playtest observed_at"
                ),
                "observations": observations,
            }
        )
    checks.sort(key=lambda item: item["check_id"])
    observed_ids = [item["check_id"] for item in checks]
    if len(observed_ids) != len(set(observed_ids)) or set(observed_ids) != set(required_ids):
        raise ProposalError("Playtest checks must cover the required check ids exactly")
    feedback = [_feedback(item) for item in _array(authored["feedback"], "Playtest feedback")]
    _validate_vault_lead_answers(
        _array(inputs.get("vault_leads", []), "Playtest STAGE vault_leads"),
        checks,
        feedback,
    )
    _assert_scored(inputs, checks, verdict)
    failing = any(not item["passed"] for item in checks)
    actionable = any(item["severity"] in ("improve", "block") for item in feedback)
    if verdict == "pass" and (failing or actionable):
        raise ProposalError("passing Playtest cannot contain failures")
    if verdict != "pass" and (not feedback or not (failing or actionable)):
        raise ProposalError("failed Playtest requires actionable evidence")
    identity = {
        "schema_version": 1,
        "kind": PLAYTESTED_KIND,
        "round": round_index,
        "made_sha256": made["made_sha256"],
        "product_artifact_sha256": made["product_manifest"]["artifact_sha256"],
        "blueprint_sha256": made["blueprint_sha256"],
        "evidence_root": evidence_root_value,
        "evidence_manifest": manifest,
        "checks": checks,
        "feedback": feedback,
        "verdict": verdict,
    }
    return {**identity, "playtested_sha256": json_sha256(identity)}


def _playtested_release_contract(
    run_root: Path,
    stage: Mapping[str, Any],
    *,
    package_root_value: str,
) -> dict[str, Any]:
    inputs = _required_fields(
        stage["inputs"], {"made", "playtested"}, "Release STAGE inputs"
    )
    manual_design_required = _manual_design_required(inputs)
    made = _validate_made(inputs["made"])
    playtested = _validate_playtested(inputs["playtested"], made)
    round_index = stage["round"]
    if made["round"] != round_index or playtested["round"] != round_index:
        raise ProposalError("Release round differs from Made or Playtested")
    if playtested["verdict"] != "pass":
        raise ProposalError("Release requires a passing Playtest")

    expected_root = "artifacts/release/package"
    if package_root_value != expected_root:
        raise ProposalError("Release package root must be %s" % expected_root)
    manifest = _tree_manifest(run_root, package_root_value, "Release package tree")
    inventory = {entry["path"]: entry for entry in manifest["entries"]}
    required_files = ["MANUAL.pdf", "product.json"]
    if manual_design_required:
        required_files.append(MANUAL_DESIGN_EVIDENCE_PATH)
    for required in required_files:
        if required not in inventory:
            raise ProposalError("Release package manifest lacks %s" % required)
    forbidden_media = sorted(
        path
        for path in inventory
        if PurePosixPath(path).suffix.casefold()
        in FORBIDDEN_RELEASE_MEDIA_SUFFIXES
    )
    if forbidden_media:
        raise ProposalError(
            "Release package cannot contain media files: %s" % forbidden_media
        )

    manual, _ = _read_regular(
        run_root,
        "%s/MANUAL.pdf" % package_root_value,
        "Release MANUAL.pdf",
        maximum=MAX_RELEASE_MANUAL_BYTES,
    )
    if hashlib.sha256(manual).hexdigest() != inventory["MANUAL.pdf"]["sha256"]:
        raise ProposalError("Release MANUAL.pdf changed after package hashing")
    _validate_pdf_manual(manual)
    _validate_manual_design_evidence(
        run_root,
        package_root_value=package_root_value,
        inventory=inventory,
        manual=manual,
        made=made,
        required=manual_design_required,
    )

    product: dict[str, Any] | None = None
    product_bytes: bytes | None = None
    for path, entry in inventory.items():
        if PurePosixPath(path).suffix.casefold() != ".json":
            continue
        document, content, _ = _read_json(
            run_root,
            "%s/%s" % (package_root_value, path),
            "Release %s" % path,
            maximum=MAX_RELEASE_CONTRACT_BYTES,
        )
        if content != canonical_json(document):
            raise ProposalError("Release %s must use canonical JSON encoding" % path)
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ProposalError("Release %s changed after package hashing" % path)
        if path == "product.json":
            product = document
            product_bytes = content
    if product is None or product_bytes is None:
        raise ProposalError("Release product.json is unavailable")
    validated_product = _validate_release_product(product)
    if validated_product != product:
        raise ProposalError("Release product.json is not canonical page content")

    product_artifact_sha256 = made["product_manifest"]["artifact_sha256"]
    evidence_artifact_sha256 = playtested["evidence_manifest"]["artifact_sha256"]
    if product.get("product_artifact_sha256") != product_artifact_sha256:
        raise ProposalError("Release product.json identifies another product")
    if (
        product.get("playtest_evidence_artifact_sha256")
        != evidence_artifact_sha256
    ):
        raise ProposalError("Release product.json identifies other Playtest evidence")
    claims = _mapping(product["claims"], "Release claims", nonempty=True)
    if claims != _expected_release_claims(playtested):
        raise ProposalError("Release claims differ from exact Playtest evidence")
    if product.get("title") != made["product"].get("title"):
        raise ProposalError("Release title differs from the exact Made product")

    unchanged = _tree_manifest(run_root, package_root_value, "Release package tree")
    if unchanged != manifest:
        raise ProposalError("Release package changed during validation")
    product_json_sha256 = hashlib.sha256(product_bytes).hexdigest()
    identity = {
        "schema_version": 2,
        "kind": RELEASE_KIND,
        "round": round_index,
        "made_sha256": made["made_sha256"],
        "playtested_sha256": playtested["playtested_sha256"],
        "product_artifact_sha256": product_artifact_sha256,
        "playtest_evidence_artifact_sha256": evidence_artifact_sha256,
        "package_root": package_root_value,
        "package_manifest": manifest,
        "manual_path": "MANUAL.pdf",
        "product_json_path": "product.json",
        "product_json_sha256": product_json_sha256,
        "product": product,
    }
    result = {**identity, "release_sha256": json_sha256(identity)}
    if len(canonical_json(result)) > MAX_RELEASE_CONTRACT_BYTES:
        raise ProposalError("native Release exceeds its byte limit")
    return result


def _direct_release_contract(
    run_root: Path,
    stage: Mapping[str, Any],
    *,
    package_root_value: str,
) -> dict[str, Any]:
    inputs = _required_fields(stage["inputs"], {"made"}, "Release STAGE inputs")
    manual_design_required = _manual_design_required(inputs)
    made = _validate_made(inputs["made"])
    round_index = stage["round"]
    if made["round"] != round_index:
        raise ProposalError("Release round differs from Made")

    expected_root = "artifacts/release/package"
    if package_root_value != expected_root:
        raise ProposalError("Release package root must be %s" % expected_root)
    manifest = _tree_manifest(run_root, package_root_value, "Release package tree")
    inventory = {entry["path"]: entry for entry in manifest["entries"]}
    required_files = ["MANUAL.pdf", "product.json", PLAYTEST_OMISSION_PATH]
    if manual_design_required:
        required_files.append(MANUAL_DESIGN_EVIDENCE_PATH)
    for required in required_files:
        if required not in inventory:
            raise ProposalError("Release package manifest lacks %s" % required)
    forbidden_media = sorted(
        path
        for path in inventory
        if PurePosixPath(path).suffix.casefold()
        in FORBIDDEN_RELEASE_MEDIA_SUFFIXES
    )
    if forbidden_media:
        raise ProposalError(
            "Release package cannot contain media files: %s" % forbidden_media
        )

    manual, _ = _read_regular(
        run_root,
        "%s/MANUAL.pdf" % package_root_value,
        "Release MANUAL.pdf",
        maximum=MAX_RELEASE_MANUAL_BYTES,
    )
    if hashlib.sha256(manual).hexdigest() != inventory["MANUAL.pdf"]["sha256"]:
        raise ProposalError("Release MANUAL.pdf changed after package hashing")
    _validate_pdf_manual(manual)
    _validate_manual_design_evidence(
        run_root,
        package_root_value=package_root_value,
        inventory=inventory,
        manual=manual,
        made=made,
        required=manual_design_required,
    )

    omission, _ = _read_regular(
        run_root,
        "%s/%s" % (package_root_value, PLAYTEST_OMISSION_PATH),
        "Release Playtest omission",
        maximum=MAX_RELEASE_CONTRACT_BYTES,
    )
    if omission != canonical_json(_playtest_omission_record()):
        raise ProposalError("Release Playtest omission is not canonical")
    omission_sha256 = _playtest_omission_sha256()
    if inventory[PLAYTEST_OMISSION_PATH]["sha256"] != omission_sha256:
        raise ProposalError("Release Playtest omission changed after package hashing")

    product: dict[str, Any] | None = None
    product_bytes: bytes | None = None
    for path, entry in inventory.items():
        if PurePosixPath(path).suffix.casefold() != ".json":
            continue
        document, content, _ = _read_json(
            run_root,
            "%s/%s" % (package_root_value, path),
            "Release %s" % path,
            maximum=MAX_RELEASE_CONTRACT_BYTES,
        )
        if content != canonical_json(document):
            raise ProposalError("Release %s must use canonical JSON encoding" % path)
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise ProposalError("Release %s changed after package hashing" % path)
        if path == "product.json":
            product = document
            product_bytes = content
    if product is None or product_bytes is None:
        raise ProposalError("Release product.json is unavailable")
    validated_product = _validate_release_product(product)
    if validated_product != product:
        raise ProposalError("Release product.json is not canonical page content")

    product_artifact_sha256 = made["product_manifest"]["artifact_sha256"]
    evidence_artifact_sha256 = omission_sha256
    if product.get("product_artifact_sha256") != product_artifact_sha256:
        raise ProposalError("Release product.json identifies another product")
    if (
        product.get("playtest_evidence_artifact_sha256")
        != evidence_artifact_sha256
    ):
        raise ProposalError("Release product.json identifies other Playtest evidence")
    claims = _mapping(product["claims"], "Release claims", nonempty=True)
    if claims != _direct_release_claims():
        raise ProposalError("Release claims must state that Playtest was not run")
    if product.get("title") != made["product"].get("title"):
        raise ProposalError("Release title differs from the exact Made product")

    unchanged = _tree_manifest(
        run_root, package_root_value, "Release package tree"
    )
    if unchanged != manifest:
        raise ProposalError("Release package changed during validation")
    product_json_sha256 = hashlib.sha256(product_bytes).hexdigest()
    identity = {
        "schema_version": 3,
        "kind": RELEASE_KIND,
        "round": round_index,
        "made_sha256": made["made_sha256"],
        "playtested_sha256": omission_sha256,
        "product_artifact_sha256": product_artifact_sha256,
        "playtest_evidence_artifact_sha256": evidence_artifact_sha256,
        "package_root": package_root_value,
        "package_manifest": manifest,
        "manual_path": "MANUAL.pdf",
        "product_json_path": "product.json",
        "product_json_sha256": product_json_sha256,
        "product": product,
    }
    result = {**identity, "release_sha256": json_sha256(identity)}
    if len(canonical_json(result)) > MAX_RELEASE_CONTRACT_BYTES:
        raise ProposalError("native Release exceeds its byte limit")
    return result


def _release_contract(
    run_root: Path,
    stage: Mapping[str, Any],
    *,
    package_root_value: str,
) -> dict[str, Any]:
    inputs = _mapping(stage["inputs"], "Release STAGE inputs", nonempty=True)
    if "playtested" in inputs:
        return _playtested_release_contract(
            run_root,
            stage,
            package_root_value=package_root_value,
        )
    return _direct_release_contract(
        run_root,
        stage,
        package_root_value=package_root_value,
    )


def _contract_path(stage: str, round_index: Any) -> str:
    if stage == "match":
        return MATCH_PATH
    if stage == "invent":
        raise ProposalError("Invent contract path requires its STAGE inputs")
    if stage == "make":
        return "artifacts/make/r%04d/made.json" % round_index
    if stage == "playtest":
        return "artifacts/playtest/r%04d/playtested.json" % round_index
    return "artifacts/release/release.json"


def _stage_contract_path(stage: Mapping[str, Any]) -> str:
    if stage["stage"] != "invent":
        return _contract_path(stage["stage"], stage["round"])
    inputs = _mapping(stage["inputs"], "Invent STAGE inputs", nonempty=True)
    contract_path = _safe_relative(
        inputs.get("contract_path", INVENT_PATH), "Invent contract_path"
    ).as_posix()
    repair_round = inputs.get("repair_round")
    expected = (
        INVENT_PATH
        if repair_round is None
        else "artifacts/invent/r%04d/invented.json"
        % _positive_int(repair_round, "Invent repair_round")
    )
    if contract_path != expected:
        raise ProposalError("Invent contract_path is not canonical for this revision")
    return contract_path


def _seal(
    run_root: Path,
    stage: Mapping[str, Any],
    contract: Mapping[str, Any],
    *,
    transition: str,
    additional_contracts: Sequence[tuple[str, Mapping[str, Any]]] = (),
    additional_files: Sequence[tuple[str, bytes]] = (),
    contract_path_value: str | None = None,
    identity_field_value: str | None = None,
) -> dict[str, Any]:
    contract_path = (
        _safe_relative(contract_path_value, "stage contract path").as_posix()
        if contract_path_value is not None
        else _stage_contract_path(stage)
    )
    if not contract_path.startswith("artifacts/%s/" % stage["stage"]):
        raise ProposalError("stage contract must stay under the current stage")
    contract_bytes = canonical_json(contract)
    if len(contract_bytes) > MAX_CONTRACT_BYTES:
        raise ProposalError("stage contract exceeds the native artifact limit")
    _atomic_write(run_root, contract_path, contract_bytes)
    artifact_sha256 = hashlib.sha256(contract_bytes).hexdigest()
    artifacts = [{"path": contract_path, "sha256": artifact_sha256}]
    for additional_path, additional_contract in additional_contracts:
        relative = _safe_relative(additional_path, "additional contract path").as_posix()
        if relative == contract_path or any(item["path"] == relative for item in artifacts):
            raise ProposalError("stage contract paths must be unique")
        if not relative.startswith("artifacts/%s/" % stage["stage"]):
            raise ProposalError("additional contract must stay under the current stage")
        content = canonical_json(additional_contract)
        if len(content) > MAX_CONTRACT_BYTES:
            raise ProposalError("additional stage contract exceeds the artifact limit")
        _atomic_write(run_root, relative, content)
        artifacts.append(
            {"path": relative, "sha256": hashlib.sha256(content).hexdigest()}
        )
    for additional_path, content in additional_files:
        relative = _safe_relative(additional_path, "additional artifact path").as_posix()
        if any(item["path"] == relative for item in artifacts):
            raise ProposalError("stage artifact paths must be unique")
        if not relative.startswith("artifacts/%s/" % stage["stage"]):
            raise ProposalError("additional artifact must stay under the current stage")
        if not isinstance(content, bytes) or not content or len(content) > MAX_JSON_BYTES:
            raise ProposalError("additional stage artifact is invalid")
        _atomic_write(run_root, relative, content)
        artifacts.append(
            {"path": relative, "sha256": hashlib.sha256(content).hexdigest()}
        )
    outcome = {
        "schema_version": 1,
        "stage": stage["stage"],
        "status": "ready",
        "artifacts": artifacts,
        "needs": [],
        "proposed_transition": transition,
    }
    proposal = {
        "schema_version": 1,
        "kind": OUTCOME_KIND,
        "checkpoint_sha256": stage["checkpoint_sha256"],
        "subject_sha256": stage["subject_sha256"],
        "outcome": outcome,
    }
    proposal_bytes = canonical_json(proposal)
    if len(proposal_bytes) > MAX_OUTCOME_BYTES:
        raise ProposalError("agent outcome proposal exceeds its byte limit")
    _atomic_write(run_root, "agent-outcome.json", proposal_bytes)
    identity_field = identity_field_value or {
        "match": "assignment_sha256",
        "invent": "invented_sha256",
        "make": "made_sha256",
        "playtest": "playtested_sha256",
        "release": "release_sha256",
    }[stage["stage"]]
    if identity_field not in contract:
        raise ProposalError("stage contract identity field is absent")
    return {
        "artifact_path": contract_path,
        "artifact_sha256": artifact_sha256,
        "contract_identity_sha256": contract[identity_field],
        "outcome_path": "agent-outcome.json",
    }


def _seal_need(
    run_root: Path,
    stage: Mapping[str, Any],
    *,
    status: str,
    reason: str,
) -> dict[str, Any]:
    if status not in ("waiting", "failed"):
        raise ProposalError("need status must be waiting or failed")
    need = _agent_need(reason, "need reason")
    outcome = {
        "schema_version": 1,
        "stage": stage["stage"],
        "status": status,
        "artifacts": [],
        "needs": [need],
        "proposed_transition": None,
    }
    proposal = {
        "schema_version": 1,
        "kind": OUTCOME_KIND,
        "checkpoint_sha256": stage["checkpoint_sha256"],
        "subject_sha256": stage["subject_sha256"],
        "outcome": outcome,
    }
    proposal_bytes = canonical_json(proposal)
    if len(proposal_bytes) > MAX_OUTCOME_BYTES:
        raise ProposalError("agent outcome proposal exceeds its byte limit")
    _atomic_write(run_root, "agent-outcome.json", proposal_bytes)
    return {
        "outcome_path": "agent-outcome.json",
        "status": status,
        "needs": 1,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Seal one authored Workshop stage proposal without model calls."
    )
    parser.add_argument(
        "--run-root",
        default=".",
        help="Canonical product-run workspace containing immutable STAGE.json.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    need = subparsers.add_parser(
        "need", help="Seal one truthful waiting or failed stage need."
    )
    need.add_argument("--stage", required=True, choices=STAGES)
    need.add_argument("--status", required=True, choices=("waiting", "failed"))
    need.add_argument("--reason", required=True, help="One concrete single-line need.")

    match = subparsers.add_parser("match", help="Seal ranking and selected inventor.")
    match.add_argument("--source", required=True, help="Run-local Match authored JSON.")

    invent = subparsers.add_parser("invent", help="Seal concept and research JSON.")
    invent.add_argument("--source", required=True, help="Run-local Invent authored JSON.")

    make = subparsers.add_parser("make", help="Seal one exact product tree.")
    make.add_argument("--product-root", required=True, help="Run-local product tree.")
    make.add_argument(
        "--source",
        help=(
            "Run-local selection, concept, and research JSON; required only "
            "for Spark effort."
        ),
    )
    make.add_argument(
        "--cad-project-path",
        required=True,
        help="CAD project directory relative to the product tree.",
    )
    make.add_argument(
        "--cad-verification-path",
        required=True,
        help="CAD verification file relative to the product tree.",
    )

    make_group = subparsers.add_parser(
        "make-group", help="Seal one build group of the current Make attempt."
    )
    make_group.add_argument(
        "--source", help="Run-local Spark creative JSON (Spark Make only)."
    )
    make_group.add_argument("--product-root", required=True, help="Run-local product tree.")
    make_group.add_argument("--group", required=True, help="Group name from the sealed build_plan.")

    playtest = subparsers.add_parser(
        "playtest", help="Seal authored checks and exact evidence tree."
    )

    make_revision = subparsers.add_parser(
        "make-revision",
        help="Seal exact evidence that the upstream Invent concept is unbuildable.",
    )
    make_revision.add_argument(
        "--source", required=True, help="Run-local Make revision feedback JSON."
    )
    make_revision.add_argument(
        "--evidence-root",
        required=True,
        help="Canonical tree containing exact contradiction evidence.",
    )
    playtest.add_argument(
        "--source", required=True, help="Run-local Playtest authored JSON."
    )
    playtest.add_argument(
        "--evidence-root",
        required=True,
        help=(
            "Run-local Playtest evidence tree containing only canonical configs "
            "and final cited outputs; keep replay work outside it."
        ),
    )

    release = subparsers.add_parser("release", help="Seal one factual package tree.")
    release.add_argument(
        "--package-root", required=True, help="Run-local factual Release package."
    )
    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    _workshop_python()
    run_root = _canonical_root(args.run_root)
    if args.command == "make-group":
        stage = _load_stage(run_root, "make")
        inputs = _mapping(stage["inputs"], "Make STAGE inputs", nonempty=True)
        assignment = invented = None
        source_value = getattr(args, "source", None)
        if inputs.get("creative_source_required") is True:
            assignment, invented = _spark_creative_contracts(run_root, stage, source_value)
        elif source_value is not None:
            raise ProposalError("this Make stage does not accept --source")
        return _make_group(
            run_root,
            stage,
            product_root_value=args.product_root,
            group_name=args.group,
            assignment_value=assignment,
            invented_value=invented,
        )
    if args.command == "need":
        expected_stage = args.stage
    elif args.command == "make-revision":
        expected_stage = "make"
    else:
        expected_stage = args.command
    stage = _load_stage(run_root, expected_stage)
    if args.command == "need":
        return _seal_need(
            run_root,
            stage,
            status=args.status,
            reason=args.reason,
        )
    additional_contracts: list[tuple[str, Mapping[str, Any]]] = []
    additional_files: list[tuple[str, bytes]] = []
    contract_path_value = None
    identity_field_value = None
    if args.command == "match":
        source, _, _ = _read_json(run_root, args.source, "Match authored source")
        contract = _match_contract(stage, source)
        transition = stage["next_transition"]
    elif args.command == "invent":
        source, source_content, _ = _read_json(
            run_root, args.source, "Invent authored source"
        )
        inputs = _mapping(stage["inputs"], "Invent STAGE inputs", nonempty=True)
        if "assignment" in inputs:
            contract = _invent_contract(run_root, stage, source)
        else:
            authored = _fields(
                source,
                {"selected_inventor_id", "ranking", "concept", "research"},
                "routed Invent authored source",
            )
            assignment = _match_contract(
                stage,
                {
                    "selected_inventor_id": authored["selected_inventor_id"],
                    "ranking": authored["ranking"],
                },
            )
            contract = _invent_contract_for_assignment(
                run_root,
                assignment,
                {"concept": authored["concept"], "research": authored["research"]},
            )
            assignment_path = _safe_relative(
                inputs.get("assignment_contract_path"),
                "routed Invent assignment_contract_path",
            ).as_posix()
            additional_contracts.append((assignment_path, assignment))
        source_path = (
            _safe_relative(
                inputs.get("contract_path", INVENT_PATH),
                "Invent contract_path",
            ).parent
            / "source.json"
        ).as_posix()
        additional_files.append((source_path, source_content))
        transition = stage["next_transition"]
    elif args.command == "make":
        inputs = _mapping(stage["inputs"], "Make STAGE inputs", nonempty=True)
        assignment = invented = None
        if inputs.get("creative_source_required") is True:
            assignment, invented = _spark_creative_contracts(run_root, stage, args.source)
            assignment_path = _safe_relative(
                inputs.get("assignment_contract_path"),
                "Spark Make assignment_contract_path",
            ).as_posix()
            invented_path = _safe_relative(
                inputs.get("invented_contract_path"),
                "Spark Make invented_contract_path",
            ).as_posix()
            additional_contracts.extend(
                ((assignment_path, assignment), (invented_path, invented))
            )
        elif args.source is not None:
            raise ProposalError("this Make stage does not accept --source")
        contract = _make_contract(
            run_root,
            stage,
            product_root_value=args.product_root,
            cad_project_path=args.cad_project_path,
            cad_verification_path=args.cad_verification_path,
            assignment_value=assignment,
            invented_value=invented,
        )
        transition = stage["next_transition"]
    elif args.command == "make-revision":
        source, source_content, _ = _read_json(
            run_root, args.source, "Make Invent-revision authored source"
        )
        contract = _make_invent_revision_contract(
            run_root,
            stage,
            source,
            evidence_root_value=args.evidence_root,
        )
        contract_path_value = stage["inputs"]["invent_revision_contract_path"]
        source_path = (
            "artifacts/make/r%04d/invent-revision-source.json" % stage["round"]
        )
        additional_files.append((source_path, source_content))
        identity_field_value = "revision_request_sha256"
        transition = "invent"
    elif args.command == "playtest":
        source, _, _ = _read_json(run_root, args.source, "Playtest authored source")
        contract = _playtest_contract(
            run_root,
            stage,
            source,
            evidence_root_value=args.evidence_root,
        )
        transition = _playtest_transition(contract)
    elif args.command == "release":
        contract = _release_contract(
            run_root,
            stage,
            package_root_value=args.package_root,
        )
        transition = stage["next_transition"]
    else:  # pragma: no cover - argparse rejects unknown commands
        raise ProposalError("unsupported stage command")
    return _seal(
        run_root,
        stage,
        contract,
        transition=transition,
        additional_contracts=additional_contracts,
        additional_files=additional_files,
        contract_path_value=contract_path_value,
        identity_field_value=identity_field_value,
    )


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(_parser().parse_args(argv))
    except ProposalError as exc:
        print("stage-proposal: %s" % exc, file=sys.stderr)
        return 2
    print(canonical_json(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
