"""Pure host protocol for one native-agent Workshop run.

This module deliberately knows nothing about Codex, prompts, providers, or
outside effects.  It materializes the exact files a native agent may inspect,
checks compact artifact references, and lets only a host-supplied deterministic
gate receipt move the durable lifecycle forward.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any, Mapping, Optional, Sequence

from workshop.artifacts import assert_packable_content
from workshop.contributors.extensions import load_inventor_extension_bundles
from workshop.contributors.manifest import load_manifest
from workshop.errors import (
    ArtifactError,
    ContractError,
    ManifestError,
    StateConflict,
    TransitionError,
)
from workshop._validation import require_sha256
from workshop.runtime.agent_assets import inventor_custom_agent_bytes
from workshop.wish import Wish


AGENT_RUN_STAGES = (
    "wish",
    "match",
    "invent",
    "make",
    "playtest",
    "release",
    "deliver",
)
AGENT_OUTCOME_STATUSES = ("ready", "waiting", "failed")
MAX_AGENT_OUTCOME_BYTES = 64 * 1024
MAX_AGENT_CHECKPOINT_BYTES = 256 * 1024
MAX_AGENT_INPUT_BYTES = 4 * 1024 * 1024
MAX_AGENT_INPUT_FILES = 256
MAX_AGENT_ARTIFACT_BYTES = 16 * 1024 * 1024
MAX_AGENT_REFERENCED_BYTES = 64 * 1024 * 1024
MAX_AGENT_ARTIFACTS_PER_OUTCOME = 16
MAX_HOST_SEALED_ARTIFACTS_PER_GATE = 512
MAX_AGENT_NEEDS = 16
MAX_AGENT_NEED_CHARS = 1_024
AGENT_RUN_CHECKPOINT_KIND = "autonomous-workshop-agent-run"

_FORWARD_TRANSITIONS = {
    "wish": "match",
    "match": "invent",
    "invent": "make",
    "make": "playtest",
    "playtest": "release",
    "release": "deliver",
    "deliver": "complete",
}
_UPSTREAM_STAGE = {
    "match": "wish",
    "invent": "match",
    "make": "invent",
    "playtest": "make",
    "release": "playtest",
    "deliver": "release",
}
_DOWNSTREAM_OF_MAKE = ("playtest", "release", "deliver")
_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_AGENT_SKILL_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_KEYED_SECRET = re.compile(
    rb"(?i)(?:password|passwd|api[_-]?key|access[_-]?token|refresh[_-]?token|"
    rb"authorization)\s*[\"']?\s*[:=]\s*[\"']?[^\s,}\"']{4,}"
)
_BEARER_SECRET = re.compile(rb"(?i)\bbearer\s+[A-Za-z0-9._~+/-]{12,}")
_EFFECT_RECEIPT_PATH = re.compile(
    r"(?i)(?:factory|carrier|shipment|manufactur|publication|payment|effect)"
    r"[^/]{0,32}receipt|receipt[^/]{0,32}"
    r"(?:factory|carrier|shipment|manufactur|publication|payment|effect)"
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
        raise ContractError("agent-run values must be finite JSON") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise ContractError("%s must be a bounded identifier" % label)
    return value


def _positive_int(value: Any, label: str, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise ContractError("%s must be an integer from 1 through %d" % (label, maximum))
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


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def _canonical_wish_bytes(value: bytes, product_id: str) -> bytes:
    if not isinstance(value, bytes) or not 1 <= len(value) <= MAX_AGENT_INPUT_BYTES:
        raise ContractError("canonical Wish bytes must be non-empty and bounded")
    try:
        document = json.loads(value.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError("canonical Wish bytes must contain strict JSON") from exc
    if not isinstance(document, dict) or set(document) != {
        "schema_version",
        "product_id",
        "objective",
        "constraints",
        "context",
    }:
        raise ContractError("canonical Wish fields are invalid")
    try:
        wish = Wish(**document)
    except (ContractError, TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("canonical Wish contract is invalid") from exc
    if wish.product_id != product_id:
        raise ContractError("canonical Wish product_id does not match the agent run")
    canonical = _canonical_json(wish.to_dict())
    if value != canonical:
        raise ContractError("Wish JSON bytes must use the canonical encoding")
    _reject_private_agent_bytes("WISH.json", value)
    return value


def _reject_private_agent_bytes(path: str, content: bytes) -> None:
    try:
        assert_packable_content(path, content)
    except ArtifactError:
        raise
    if _KEYED_SECRET.search(content) or _BEARER_SECRET.search(content):
        raise ArtifactError("agent artifact contains credential-shaped content")
    if _EFFECT_RECEIPT_PATH.search(PurePosixPath(path).name):
        raise ArtifactError("outside-effect receipts must not be agent artifacts")


def _read_regular(path: Path, label: str, maximum: int) -> bytes:
    try:
        expected = path.lstat()
    except OSError as exc:
        raise ArtifactError("%s is unavailable" % label) from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ArtifactError("%s must be a regular file" % label)
    if not 0 <= expected.st_size <= maximum:
        raise ArtifactError("%s exceeds its byte limit" % label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ArtifactError("%s cannot be opened safely" % label) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ArtifactError("%s changed while opening" % label)
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        if len(content) > maximum or os.read(descriptor, 1):
            raise ArtifactError("%s exceeds its byte limit" % label)
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ArtifactError("%s changed while reading" % label)
        return content
    finally:
        os.close(descriptor)


def _source_tree_files(
    root: Path,
    *,
    label: str,
) -> tuple[tuple[PurePosixPath, bytes, int], ...]:
    """Snapshot one exact, real input tree without following links.

    Product-run skills may contain executable deterministic tools.  Their
    executable bit is normalized to ``0500`` and bound into the immutable
    input manifest; every other file is materialized ``0400``.
    """

    try:
        requested = Path(root)
    except TypeError as exc:
        raise ContractError("%s must be path-like" % label) from exc
    if not requested.is_absolute() or requested.is_symlink():
        raise ContractError("%s must be an absolute real directory" % label)
    try:
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise ArtifactError("%s is unavailable" % label) from exc
    if requested != resolved or not requested.is_dir():
        raise ArtifactError("%s must be an absolute real directory" % label)

    files: list[tuple[PurePosixPath, bytes, int]] = []
    for directory, dirnames, filenames in os.walk(str(requested), followlinks=False):
        base = Path(directory)
        dirnames[:] = [
            dirname
            for dirname in dirnames
            if dirname not in ("__pycache__", ".git")
        ]
        for dirname in tuple(dirnames):
            if (base / dirname).is_symlink():
                raise ArtifactError("%s contains a symlink" % label)
        for filename in sorted(filenames):
            if filename == ".DS_Store" or filename.endswith((".pyc", ".pyo")):
                continue
            source = base / filename
            if source.is_symlink():
                raise ArtifactError("%s contains a symlink" % label)
            relative = PurePosixPath(source.relative_to(requested).as_posix())
            _safe_relative(relative.as_posix(), "%s path" % label)
            try:
                source_mode = stat.S_IMODE(source.lstat().st_mode)
            except OSError as exc:
                raise ArtifactError("%s entry is unavailable" % label) from exc
            mode = 0o500 if source_mode & 0o111 else 0o400
            files.append(
                (
                    relative,
                    _read_regular(source, "%s file" % label, MAX_AGENT_INPUT_BYTES),
                    mode,
                )
            )
    files.sort(key=lambda item: item[0].as_posix())
    return tuple(files)


def _read_relative_regular(root: Path, relative: PurePosixPath) -> tuple[bytes, int]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    directory_flags = flags | getattr(os, "O_DIRECTORY", 0)
    descriptor: Optional[int] = None
    directory: Optional[int] = None
    try:
        directory = os.open(str(root), directory_flags)
        for part in relative.parts[:-1]:
            child = os.open(part, directory_flags, dir_fd=directory)
            os.close(directory)
            directory = child
        descriptor = os.open(relative.parts[-1], flags, dir_fd=directory)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ArtifactError("agent artifact must be a regular file")
        if not 0 <= opened.st_size <= MAX_AGENT_ARTIFACT_BYTES:
            raise ArtifactError("agent artifact exceeds its byte limit")
        chunks: list[bytes] = []
        length = 0
        while length <= MAX_AGENT_ARTIFACT_BYTES:
            chunk = os.read(
                descriptor,
                min(1024 * 1024, MAX_AGENT_ARTIFACT_BYTES + 1 - length),
            )
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
        content = b"".join(chunks)
        if len(content) > MAX_AGENT_ARTIFACT_BYTES or os.read(descriptor, 1):
            raise ArtifactError("agent artifact exceeds its byte limit")
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ArtifactError("agent artifact changed while reading")
        return content, opened.st_size
    except OSError as exc:
        raise ArtifactError(
            "agent artifact cannot be opened without following links: %s"
            % relative.as_posix()
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if directory is not None:
            os.close(directory)


def _atomic_private_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=".%s." % path.name, dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        parent = os.open(str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


@dataclass(frozen=True)
class AgentArtifact:
    """One bounded, exact file left by the native agent."""

    path: str
    sha256: str

    def __post_init__(self) -> None:
        _safe_relative(self.path, "agent artifact path")
        require_sha256(self.sha256, "agent artifact sha256")

    def to_dict(self) -> dict[str, str]:
        return {"path": self.path, "sha256": self.sha256}

    @classmethod
    def from_mapping(cls, value: Any) -> "AgentArtifact":
        if not isinstance(value, Mapping) or set(value) != {"path", "sha256"}:
            raise ContractError("agent artifact fields are invalid")
        return cls(path=value["path"], sha256=value["sha256"])


@dataclass(frozen=True)
class AgentOutcome:
    """Compact, untrusted stage result proposed by the native agent."""

    stage: str
    status: str
    artifacts: tuple[AgentArtifact, ...] = ()
    needs: tuple[str, ...] = ()
    proposed_transition: Optional[str] = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "needs", tuple(self.needs))
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("agent outcome schema_version must be 1")
        if self.stage not in AGENT_RUN_STAGES:
            raise ContractError("agent outcome stage is invalid")
        if self.status not in AGENT_OUTCOME_STATUSES:
            raise ContractError("agent outcome status is invalid")
        if not 0 <= len(self.artifacts) <= MAX_AGENT_ARTIFACTS_PER_OUTCOME:
            raise ContractError("agent outcome has too many artifact references")
        if not all(isinstance(item, AgentArtifact) for item in self.artifacts):
            raise ContractError("agent outcome artifacts must be AgentArtifact values")
        if len({item.path for item in self.artifacts}) != len(self.artifacts):
            raise ContractError("agent outcome artifact paths must be unique")
        for artifact in self.artifacts:
            parts = _safe_relative(artifact.path, "agent artifact path").parts
            if len(parts) < 3 or parts[:2] != ("artifacts", self.stage):
                raise ContractError(
                    "agent artifact paths must live under artifacts/%s" % self.stage
                )
        if not 0 <= len(self.needs) <= MAX_AGENT_NEEDS:
            raise ContractError("agent outcome has too many needs")
        for need in self.needs:
            if (
                not isinstance(need, str)
                or not need.strip()
                or len(need) > MAX_AGENT_NEED_CHARS
                or any(ord(character) < 32 or ord(character) == 127 for character in need)
            ):
                raise ContractError("agent outcome needs must be bounded text")
        if len(set(self.needs)) != len(self.needs):
            raise ContractError("agent outcome needs must be unique")
        if self.proposed_transition is not None and self.proposed_transition not in (
            *AGENT_RUN_STAGES,
            "complete",
        ):
            raise ContractError("agent proposed transition is invalid")
        if self.status == "ready":
            if not self.artifacts or self.needs or self.proposed_transition is None:
                raise ContractError(
                    "a ready agent outcome needs artifacts and one transition, not needs"
                )
        elif self.proposed_transition is not None or not self.needs:
            raise ContractError(
                "waiting and failed agent outcomes need a reason and cannot transition"
            )
        encoded = _canonical_json(self.to_dict())
        if len(encoded) > MAX_AGENT_OUTCOME_BYTES:
            raise ContractError("agent outcome exceeds its byte limit")
        _reject_private_agent_bytes("agent-outcome.json", encoded)

    @property
    def sha256(self) -> str:
        return _sha256(_canonical_json(self.to_dict()))

    @property
    def primary_artifact(self) -> Optional[AgentArtifact]:
        return self.artifacts[0] if self.artifacts else None

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "status": self.status,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "needs": list(self.needs),
            "proposed_transition": self.proposed_transition,
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "AgentOutcome":
        expected = {
            "schema_version",
            "stage",
            "status",
            "artifacts",
            "needs",
            "proposed_transition",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("agent outcome fields are invalid")
        artifacts = value["artifacts"]
        needs = value["needs"]
        if isinstance(artifacts, (str, bytes)) or not isinstance(artifacts, Sequence):
            raise ContractError("agent outcome artifacts must be an array")
        if isinstance(needs, (str, bytes)) or not isinstance(needs, Sequence):
            raise ContractError("agent outcome needs must be an array")
        return cls(
            schema_version=value["schema_version"],
            stage=value["stage"],
            status=value["status"],
            artifacts=tuple(AgentArtifact.from_mapping(item) for item in artifacts),
            needs=tuple(needs),
            proposed_transition=value["proposed_transition"],
        )


@dataclass(frozen=True)
class DeterministicGateReceipt:
    """Host-created gate result bound to one exact agent outcome and input."""

    stage: str
    gate_id: str
    passed: bool
    subject_sha256: str
    outcome_sha256: str
    evidence_sha256: str
    schema_version: int = 1

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("deterministic gate schema_version must be 1")
        if self.stage not in AGENT_RUN_STAGES:
            raise ContractError("deterministic gate stage is invalid")
        _identifier(self.gate_id, "deterministic gate id")
        if type(self.passed) is not bool:
            raise ContractError("deterministic gate passed must be boolean")
        require_sha256(self.subject_sha256, "deterministic gate subject sha256")
        require_sha256(self.outcome_sha256, "deterministic gate outcome sha256")
        require_sha256(self.evidence_sha256, "deterministic gate evidence sha256")

    @property
    def sha256(self) -> str:
        return _sha256(_canonical_json(self.to_dict()))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stage": self.stage,
            "gate_id": self.gate_id,
            "passed": self.passed,
            "subject_sha256": self.subject_sha256,
            "outcome_sha256": self.outcome_sha256,
            "evidence_sha256": self.evidence_sha256,
        }


@dataclass(frozen=True)
class AgentRunCheckpoint:
    """Redacted view of the authoritative host checkpoint."""

    product_id: str
    stage: str
    status: str
    revision: int
    round_index: int
    max_rounds: int
    wish_sha256: str
    run_root_sha256: str
    host_state_root_sha256: str
    checkpoint_sha256: str
    input_sha256s: Mapping[str, str]
    stage_artifacts: Mapping[str, tuple[AgentArtifact, ...]]
    invalidated_stages: tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.status == "complete"


class AgentRun:
    """Trusted host state machine for one native-agent-led Workshop run."""

    def __init__(
        self,
        run_root: Path,
        host_state_root: Path,
        checkpoint_sha256: str,
    ) -> None:
        self.run_root = run_root
        self.host_state_root = host_state_root
        self._checkpoint_path = host_state_root / "agent-run.json"
        self._expected_checkpoint_sha256 = checkpoint_sha256

    @classmethod
    def create(
        cls,
        run_root: Path,
        host_state_root: Path,
        *,
        product_id: str,
        wish_bytes: bytes,
        product_run_constitution_source: Path,
        skill_root: Path,
        domain_skill_roots: Optional[Mapping[str, Path]] = None,
        inventor_catalog_root: Optional[Path] = None,
        max_rounds: int = 4,
    ) -> "AgentRun":
        _identifier(product_id, "agent run product_id")
        _positive_int(max_rounds, "agent run max_rounds", 100)
        wish_bytes = _canonical_wish_bytes(wish_bytes, product_id)
        try:
            requested = Path(run_root)
        except TypeError as exc:
            raise ContractError("agent run root must be path-like") from exc
        if not requested.is_absolute():
            raise ContractError("agent run root must be absolute")
        try:
            parent = requested.parent.resolve(strict=True)
        except OSError as exc:
            raise ContractError("agent run parent must already exist") from exc
        selected = parent / requested.name
        if requested != selected:
            raise ContractError("agent run root must be an absolute canonical path")
        try:
            requested_host = Path(host_state_root)
        except TypeError as exc:
            raise ContractError("agent host-state root must be path-like") from exc
        if not requested_host.is_absolute():
            raise ContractError("agent host-state root must be absolute")
        try:
            host_parent = requested_host.parent.resolve(strict=True)
        except OSError as exc:
            raise ContractError("agent host-state parent must already exist") from exc
        selected_host = host_parent / requested_host.name
        if requested_host != selected_host:
            raise ContractError("agent host-state root must be an absolute canonical path")
        if (
            selected == selected_host
            or selected in selected_host.parents
            or selected_host in selected.parents
        ):
            raise ContractError(
                "agent run and host-state roots must not overlap"
            )
        try:
            constitution = Path(product_run_constitution_source)
        except TypeError as exc:
            raise ContractError(
                "product-run constitution source must be path-like"
            ) from exc
        if (
            not constitution.is_absolute()
            or constitution.parts[-3:] != (".agents", "product-run", "AGENTS.md")
        ):
            raise ContractError(
                "product-run constitution source must be the explicit "
                ".agents/product-run/AGENTS.md file"
            )
        try:
            resolved_constitution = constitution.resolve(strict=True)
        except OSError as exc:
            raise ArtifactError("product-run constitution source is unavailable") from exc
        if resolved_constitution != constitution:
            raise ContractError(
                "product-run constitution source must not contain symlinks"
            )
        constitution_bytes = _read_regular(
            constitution, "product-run constitution source", MAX_AGENT_INPUT_BYTES
        )
        _reject_private_agent_bytes("AGENTS.md", constitution_bytes)
        skill_files = _source_tree_files(
            skill_root, label="source autonomous-workshop skill"
        )
        if not any(relative.as_posix() == "SKILL.md" for relative, _, _ in skill_files):
            raise ArtifactError("source autonomous-workshop skill lacks SKILL.md")
        for relative, content, _ in skill_files:
            _reject_private_agent_bytes(
                ".agents/skills/autonomous-workshop/%s" % relative.as_posix(),
                content,
            )

        domain_files: list[tuple[PurePosixPath, bytes, int]] = []
        selected_domain_skills = domain_skill_roots or {}
        if not isinstance(selected_domain_skills, Mapping):
            raise ContractError("domain skill roots must be a mapping")
        for name, source_root in sorted(selected_domain_skills.items()):
            if (
                not isinstance(name, str)
                or _AGENT_SKILL_NAME.fullmatch(name) is None
                or name == "autonomous-workshop"
            ):
                raise ContractError("domain skill name is invalid")
            files = _source_tree_files(
                source_root, label="source %s skill" % name
            )
            if not any(relative.as_posix() == "SKILL.md" for relative, _, _ in files):
                raise ArtifactError("source %s skill lacks SKILL.md" % name)
            target = PurePosixPath(".agents/skills") / name
            for relative, content, mode in files:
                destination = target / relative
                _reject_private_agent_bytes(destination.as_posix(), content)
                domain_files.append((destination, content, mode))

        catalog_files: list[tuple[PurePosixPath, bytes, int]] = []
        inventor_skill_files: list[tuple[PurePosixPath, bytes, int]] = []
        inventor_agent_files: list[tuple[PurePosixPath, bytes, int]] = []
        if inventor_catalog_root is not None:
            try:
                requested_catalog = Path(inventor_catalog_root)
            except TypeError as exc:
                raise ContractError("inventor catalog root must be path-like") from exc
            if not requested_catalog.is_absolute() or requested_catalog.is_symlink():
                raise ContractError(
                    "inventor catalog root must be an absolute real directory"
                )
            try:
                resolved_catalog = requested_catalog.resolve(strict=True)
            except OSError as exc:
                raise ArtifactError("inventor catalog root is unavailable") from exc
            if resolved_catalog != requested_catalog or not requested_catalog.is_dir():
                raise ArtifactError("inventor catalog root must be a real directory")
            try:
                entries = sorted(requested_catalog.iterdir(), key=lambda item: item.name)
            except OSError as exc:
                raise ArtifactError("inventor catalog cannot be listed") from exc
            for entry in entries:
                if entry.is_symlink():
                    raise ArtifactError("inventor catalog contains a symlink")
                if not entry.is_dir():
                    continue
                if _AGENT_SKILL_NAME.fullmatch(entry.name) is None:
                    raise ArtifactError("inventor catalog id is not a safe path name")
                manifest_path = entry / "inventor.json"
                taste_path = entry / "TASTE.md"
                if not manifest_path.is_file() or not taste_path.is_file():
                    raise ArtifactError(
                        "inventor catalog entry must contain inventor.json and TASTE.md"
                    )
                manifest = _read_regular(
                    manifest_path, "inventor manifest", MAX_AGENT_INPUT_BYTES
                )
                taste = _read_regular(taste_path, "inventor Taste", MAX_AGENT_INPUT_BYTES)
                try:
                    manifest_value = json.loads(
                        manifest.decode("utf-8"), object_pairs_hook=_strict_object
                    )
                except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
                    raise ArtifactError("inventor manifest must be strict JSON") from exc
                if (
                    not isinstance(manifest_value, Mapping)
                    or manifest_value.get("id") != entry.name
                ):
                    raise ArtifactError("inventor manifest id differs from its folder")
                try:
                    inventor_manifest = load_manifest(manifest_path)
                    if inventor_manifest.schema_version != 7:
                        raise ArtifactError(
                            "inventor catalog requires native schema_version 7"
                        )
                    bundles = load_inventor_extension_bundles(inventor_manifest)
                except ManifestError as exc:
                    raise ArtifactError(
                        "inventor schema_version 7 skill inventory is invalid"
                    ) from exc
                if not bundles:
                    raise ArtifactError(
                        "inventor schema-v7 catalog entry declares no Codex skill"
                    )
                skill_names = tuple(bundle.extension.name for bundle in bundles)
                agent_definition = inventor_custom_agent_bytes(
                    entry.name,
                    taste,
                    skill_names=skill_names,
                )
                agent_destination = (
                    PurePosixPath(".codex/agents") / (entry.name + ".toml")
                )
                _reject_private_agent_bytes(
                    agent_destination.as_posix(), agent_definition
                )
                inventor_agent_files.append(
                    (agent_destination, agent_definition, 0o400)
                )
                target = PurePosixPath("catalog/inventors") / entry.name
                for filename, content in (("inventor.json", manifest), ("TASTE.md", taste)):
                    destination = target / filename
                    _reject_private_agent_bytes(destination.as_posix(), content)
                    catalog_files.append((destination, content, 0o400))
                for bundle in bundles:
                    files = _source_tree_files(
                        bundle.root,
                        label="source %s Inventor skill" % bundle.extension.name,
                    )
                    skill_target = (
                        PurePosixPath(".agents/skills") / bundle.extension.name
                    )
                    for relative, content, mode in files:
                        destination = skill_target / relative
                        _reject_private_agent_bytes(destination.as_posix(), content)
                        inventor_skill_files.append((destination, content, mode))
            if not catalog_files:
                raise ArtifactError("inventor catalog contains no Inventors")

        all_input_files: list[tuple[PurePosixPath, bytes, int]] = [
            (PurePosixPath("WISH.json"), wish_bytes, 0o400),
            (PurePosixPath("AGENTS.md"), constitution_bytes, 0o400),
        ]
        skill_target = PurePosixPath(".agents/skills/autonomous-workshop")
        all_input_files.extend(
            (skill_target / relative, content, mode)
            for relative, content, mode in skill_files
        )
        all_input_files.extend(domain_files)
        all_input_files.extend(inventor_skill_files)
        all_input_files.extend(catalog_files)
        all_input_files.extend(inventor_agent_files)
        all_input_files.sort(key=lambda item: item[0].as_posix())
        input_paths = [relative.as_posix() for relative, _, _ in all_input_files]
        if len(input_paths) != len(set(input_paths)):
            raise ArtifactError("agent run input paths collide")
        if len(all_input_files) > MAX_AGENT_INPUT_FILES:
            raise ArtifactError("agent run has too many input files")
        total_input_bytes = sum(len(content) for _, content, _ in all_input_files)
        if total_input_bytes > MAX_AGENT_INPUT_BYTES:
            raise ArtifactError("agent run inputs exceed their total byte limit")

        if selected.exists() or selected.is_symlink():
            raise StateConflict("agent run root already exists")
        if selected_host.exists() or selected_host.is_symlink():
            raise StateConflict("agent host-state root already exists")
        try:
            selected.mkdir(mode=0o700)
        except OSError as exc:
            raise StateConflict("agent run root could not be created exclusively") from exc
        if stat.S_IMODE(selected.stat().st_mode) != 0o700:
            os.chmod(selected, 0o700)
        try:
            selected_host.mkdir(mode=0o700)
        except OSError as exc:
            try:
                selected.rmdir()
            except OSError:
                pass
            raise StateConflict(
                "agent host-state root could not be created exclusively"
            ) from exc
        if stat.S_IMODE(selected_host.stat().st_mode) != 0o700:
            os.chmod(selected_host, 0o700)

        artifacts = selected / "artifacts"
        artifacts.mkdir(mode=0o700)

        inputs: list[dict[str, Any]] = []

        def materialize(relative: PurePosixPath, content: bytes, mode: int) -> None:
            destination = selected.joinpath(*relative.parts)
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            try:
                descriptor = os.open(
                    str(destination),
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                    mode,
                )
            except OSError as exc:
                raise ArtifactError("agent input could not be materialized") from exc
            try:
                written = 0
                while written < len(content):
                    written += os.write(descriptor, content[written:])
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            os.chmod(destination, mode)
            inputs.append(
                {
                    "path": relative.as_posix(),
                    "sha256": _sha256(content),
                    "size": len(content),
                    "mode": mode,
                }
            )

        for relative, content, mode in all_input_files:
            materialize(relative, content, mode)
        for directory in sorted(
            (
                path
                for path in (selected / ".agents").rglob("*")
                if path.is_dir()
            ),
            key=lambda path: len(path.parts),
            reverse=True,
        ):
            os.chmod(directory, 0o500)
        os.chmod(selected / ".agents", 0o500)
        codex_input_root = selected / ".codex"
        if codex_input_root.exists():
            for directory in sorted(
                (
                    path
                    for path in codex_input_root.rglob("*")
                    if path.is_dir()
                ),
                key=lambda path: len(path.parts),
                reverse=True,
            ):
                os.chmod(directory, 0o500)
            os.chmod(codex_input_root, 0o500)
        catalog_input_root = selected / "catalog"
        if catalog_input_root.exists():
            for directory in sorted(
                (
                    path
                    for path in catalog_input_root.rglob("*")
                    if path.is_dir()
                ),
                key=lambda path: len(path.parts),
                reverse=True,
            ):
                os.chmod(directory, 0o500)
            os.chmod(catalog_input_root, 0o500)

        core: dict[str, Any] = {
            "schema_version": 2,
            "kind": AGENT_RUN_CHECKPOINT_KIND,
            "product_id": product_id,
            "run_root_sha256": _sha256(str(selected).encode("utf-8")),
            "host_state_root_sha256": _sha256(
                str(selected_host).encode("utf-8")
            ),
            "revision": 0,
            "stage": "wish",
            "status": "active",
            "round_index": 0,
            "max_rounds": max_rounds,
            "inputs": sorted(inputs, key=lambda item: item["path"]),
            "sealed_artifacts": [],
            "stage_artifacts": {},
            "invalidated_stages": [],
            "history": [],
            "last_outcome_sha256": None,
            "previous_checkpoint_sha256": None,
        }
        checkpoint_sha256 = cls._write_checkpoint_file(
            selected_host / "agent-run.json", core
        )
        run = cls(selected, selected_host, checkpoint_sha256)
        run.snapshot()
        return run

    @classmethod
    def open(
        cls,
        run_root: Path,
        *,
        host_state_root: Path,
        expected_checkpoint_sha256: Optional[str] = None,
    ) -> "AgentRun":
        try:
            requested = Path(run_root)
            requested_host = Path(host_state_root)
        except TypeError as exc:
            raise ContractError("agent run roots must be path-like") from exc
        if (
            not requested.is_absolute()
            or not requested_host.is_absolute()
            or requested.is_symlink()
            or requested_host.is_symlink()
        ):
            raise ContractError(
                "agent run and host-state roots must be absolute real directories"
            )
        try:
            selected = requested.resolve(strict=True)
            selected_host = requested_host.resolve(strict=True)
        except OSError as exc:
            raise ContractError("agent run or host-state root is unavailable") from exc
        if requested != selected or requested_host != selected_host:
            raise ContractError("agent run roots must use canonical paths")
        if (
            selected == selected_host
            or selected in selected_host.parents
            or selected_host in selected.parents
        ):
            raise ContractError("agent run and host-state roots must not overlap")
        checkpoint_path = selected_host / "agent-run.json"
        payload = cls._read_checkpoint_file(checkpoint_path)
        observed = payload["checkpoint_sha256"]
        if expected_checkpoint_sha256 is not None:
            require_sha256(expected_checkpoint_sha256, "expected agent checkpoint sha256")
            if observed != expected_checkpoint_sha256:
                raise StateConflict("agent run checkpoint differs from trusted state")
        run = cls(selected, selected_host, observed)
        run.snapshot()
        return run

    @staticmethod
    def _write_checkpoint_file(path: Path, core: Mapping[str, Any]) -> str:
        encoded_core = _canonical_json(dict(core))
        digest = _sha256(encoded_core)
        encoded = _canonical_json({**dict(core), "checkpoint_sha256": digest}) + b"\n"
        if len(encoded) > MAX_AGENT_CHECKPOINT_BYTES:
            raise StateConflict("agent run checkpoint exceeds its byte limit")
        _atomic_private_write(path, encoded)
        return digest

    @staticmethod
    def _read_checkpoint_file(path: Path) -> dict[str, Any]:
        try:
            checkpoint_mode = stat.S_IMODE(path.lstat().st_mode)
        except OSError as exc:
            raise StateConflict("agent run checkpoint is unavailable") from exc
        if checkpoint_mode != 0o600:
            raise StateConflict("agent run checkpoint mode must be 0600")
        content = _read_regular(path, "agent run checkpoint", MAX_AGENT_CHECKPOINT_BYTES)
        try:
            value = json.loads(content.decode("utf-8"), object_pairs_hook=_strict_object)
        except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise StateConflict("agent run checkpoint is not strict JSON") from exc
        if not isinstance(value, dict) or "checkpoint_sha256" not in value:
            raise StateConflict("agent run checkpoint fields are invalid")
        digest = value.pop("checkpoint_sha256")
        try:
            require_sha256(digest, "agent run checkpoint sha256")
        except ContractError as exc:
            raise StateConflict("agent run checkpoint digest is invalid") from exc
        if digest != _sha256(_canonical_json(value)):
            raise StateConflict("agent run checkpoint digest does not match its bytes")
        value["checkpoint_sha256"] = digest
        return value

    def _load(self) -> dict[str, Any]:
        if (
            not self.run_root.is_absolute()
            or not self.host_state_root.is_absolute()
            or self.run_root == self.host_state_root
            or self.run_root in self.host_state_root.parents
            or self.host_state_root in self.run_root.parents
        ):
            raise StateConflict("agent run and host-state roots are not safely separated")
        for path, expected_mode in (
            (self.run_root, 0o700),
            (self.run_root / "artifacts", 0o700),
            (self.host_state_root, 0o700),
        ):
            try:
                identity = path.lstat()
            except OSError as exc:
                raise StateConflict("agent run private directory is unavailable") from exc
            if (
                path.is_symlink()
                or not stat.S_ISDIR(identity.st_mode)
                or stat.S_IMODE(identity.st_mode) != expected_mode
            ):
                raise StateConflict("agent run private directory mode changed")
        payload = self._read_checkpoint_file(self._checkpoint_path)
        if payload["checkpoint_sha256"] != self._expected_checkpoint_sha256:
            raise StateConflict("agent run checkpoint changed since this host read it")
        expected_fields = {
            "schema_version",
            "kind",
            "product_id",
            "run_root_sha256",
            "host_state_root_sha256",
            "revision",
            "stage",
            "status",
            "round_index",
            "max_rounds",
            "inputs",
            "sealed_artifacts",
            "stage_artifacts",
            "invalidated_stages",
            "history",
            "last_outcome_sha256",
            "previous_checkpoint_sha256",
            "checkpoint_sha256",
        }
        if set(payload) != expected_fields:
            raise StateConflict("agent run checkpoint fields are invalid")
        if (
            type(payload["schema_version"]) is not int
            or payload["schema_version"] != 2
            or payload["kind"] != AGENT_RUN_CHECKPOINT_KIND
            or payload["stage"] not in AGENT_RUN_STAGES
            or payload["status"] not in ("active", "waiting", "failed", "complete")
            or type(payload["revision"]) is not int
            or payload["revision"] < 0
            or type(payload["round_index"]) is not int
            or type(payload["max_rounds"]) is not int
            or not 1 <= payload["max_rounds"] <= 100
            or not 0 <= payload["round_index"] <= payload["max_rounds"]
            or not isinstance(payload["history"], list)
            or len(payload["history"]) > payload["max_rounds"] * 3 + 16
        ):
            raise StateConflict("agent run checkpoint values are invalid")
        _identifier(payload["product_id"], "agent run product_id")
        _positive_int(payload["max_rounds"], "agent run max_rounds", 100)
        expected_root = _sha256(str(self.run_root).encode("utf-8"))
        if payload["run_root_sha256"] != expected_root:
            raise StateConflict("agent run checkpoint belongs to another root")
        expected_host_root = _sha256(str(self.host_state_root).encode("utf-8"))
        if payload["host_state_root_sha256"] != expected_host_root:
            raise StateConflict("agent run checkpoint belongs to another host-state root")
        self._verify_inputs(payload)
        self._verify_sealed_artifacts(payload)
        return payload

    def _verify_inputs(self, payload: Mapping[str, Any]) -> None:
        inputs = payload.get("inputs")
        if not isinstance(inputs, list) or not 3 <= len(inputs) <= MAX_AGENT_INPUT_FILES:
            raise StateConflict("agent run input manifest is invalid")
        observed_paths = []
        total = 0
        for item in inputs:
            if not isinstance(item, Mapping) or set(item) != {
                "path",
                "sha256",
                "size",
                "mode",
            }:
                raise StateConflict("agent run input manifest is invalid")
            relative = _safe_relative(item["path"], "agent input path")
            if type(item["size"]) is not int or not 0 <= item["size"] <= MAX_AGENT_INPUT_BYTES:
                raise StateConflict("agent run input size is invalid")
            if type(item["mode"]) is not int or item["mode"] not in (0o400, 0o500):
                raise StateConflict("agent run input mode is invalid")
            require_sha256(item["sha256"], "agent input sha256")
            content, size = _read_relative_regular(self.run_root, relative)
            path = self.run_root.joinpath(*relative.parts)
            if stat.S_IMODE(path.stat().st_mode) != item["mode"]:
                raise StateConflict("agent run immutable input mode changed")
            if size != item["size"] or _sha256(content) != item["sha256"]:
                raise StateConflict("agent run immutable input bytes changed")
            observed_paths.append(relative.as_posix())
            total += size
        if len(observed_paths) != len(set(observed_paths)) or total > MAX_AGENT_INPUT_BYTES:
            raise StateConflict("agent run input manifest is invalid")
        required = {"WISH.json", "AGENTS.md", ".agents/skills/autonomous-workshop/SKILL.md"}
        if not required <= set(observed_paths):
            raise StateConflict("agent run required inputs are missing")
        roster_ids = {
            PurePosixPath(path).parts[2]
            for path in observed_paths
            if len(PurePosixPath(path).parts) == 4
            and PurePosixPath(path).parts[:2] == ("catalog", "inventors")
            and PurePosixPath(path).name == "inventor.json"
        }
        expected_agent_paths = {
            ".codex/agents/%s.toml" % inventor_id for inventor_id in roster_ids
        }
        observed_agent_paths = {
            path for path in observed_paths if path.startswith(".codex/agents/")
        }
        if expected_agent_paths != observed_agent_paths:
            raise StateConflict(
                "project-scoped Codex Inventor agents differ from the roster"
            )
        immutable_trees = (
            (self.run_root / ".agents", ".agents/", "skill"),
            (self.run_root / ".codex", ".codex/", "Codex agent"),
            (self.run_root / "catalog", "catalog/", "catalog"),
        )
        for tree_root, prefix, label in immutable_trees:
            expected_files = {path for path in observed_paths if path.startswith(prefix)}
            if not expected_files:
                if tree_root.exists() or tree_root.is_symlink():
                    raise StateConflict(
                        "agent run immutable %s tree is unexpected" % label
                    )
                continue
            directories = [tree_root]
            actual_files = set()
            try:
                entries = tuple(tree_root.rglob("*"))
            except OSError as exc:
                raise StateConflict(
                    "agent run immutable %s tree is unavailable" % label
                ) from exc
            for entry in entries:
                try:
                    identity = entry.lstat()
                except OSError as exc:
                    raise StateConflict(
                        "agent run immutable %s entry is unavailable" % label
                    ) from exc
                if entry.is_symlink():
                    raise StateConflict(
                        "agent run immutable %s tree contains a symlink" % label
                    )
                if stat.S_ISDIR(identity.st_mode):
                    directories.append(entry)
                elif stat.S_ISREG(identity.st_mode):
                    actual_files.add(entry.relative_to(self.run_root).as_posix())
                else:
                    raise StateConflict(
                        "agent run immutable %s tree has a special file" % label
                    )
            for directory in directories:
                try:
                    identity = directory.lstat()
                except OSError as exc:
                    raise StateConflict(
                        "agent run immutable %s directory is unavailable" % label
                    ) from exc
                if (
                    directory.is_symlink()
                    or not stat.S_ISDIR(identity.st_mode)
                    or stat.S_IMODE(identity.st_mode) != 0o500
                ):
                    raise StateConflict(
                        "agent run immutable %s directory mode changed" % label
                    )
            if actual_files != expected_files:
                raise StateConflict(
                    "agent run immutable %s tree differs from its input manifest" % label
                )

    def _verify_sealed_artifacts(self, payload: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
        sealed = payload.get("sealed_artifacts")
        if not isinstance(sealed, list):
            raise StateConflict("agent run sealed artifact inventory is invalid")
        by_path: dict[str, dict[str, Any]] = {}
        total = 0
        for item in sealed:
            if not isinstance(item, Mapping) or set(item) != {"path", "sha256", "size"}:
                raise StateConflict("agent run sealed artifact inventory is invalid")
            artifact = AgentArtifact(item["path"], item["sha256"])
            if artifact.path in by_path or type(item["size"]) is not int:
                raise StateConflict("agent run sealed artifact inventory is invalid")
            content, size = _read_relative_regular(
                self.run_root, _safe_relative(artifact.path, "agent artifact path")
            )
            _reject_private_agent_bytes(artifact.path, content)
            if size != item["size"] or _sha256(content) != artifact.sha256:
                raise StateConflict("a sealed agent artifact changed")
            total += size
            by_path[artifact.path] = dict(item)
        if total > MAX_AGENT_REFERENCED_BYTES:
            raise StateConflict("agent run referenced artifacts exceed their total limit")
        stage_artifacts = payload.get("stage_artifacts")
        if not isinstance(stage_artifacts, Mapping):
            raise StateConflict("agent run stage artifact bindings are invalid")
        for stage, paths in stage_artifacts.items():
            if stage not in AGENT_RUN_STAGES or not isinstance(paths, list) or not paths:
                raise StateConflict("agent run stage artifact bindings are invalid")
            if any(path not in by_path for path in paths) or len(paths) != len(set(paths)):
                raise StateConflict("agent run stage artifact binding is unsealed")
        return by_path

    def _write_next(self, current: Mapping[str, Any], updated: dict[str, Any]) -> None:
        history = updated.get("history")
        maximum_history = current["max_rounds"] * 3 + 16
        if not isinstance(history, list) or len(history) > maximum_history:
            raise TransitionError("agent run checkpoint history budget is exhausted")
        updated["revision"] = current["revision"] + 1
        updated["previous_checkpoint_sha256"] = current["checkpoint_sha256"]
        updated.pop("checkpoint_sha256", None)
        digest = self._write_checkpoint_file(self._checkpoint_path, updated)
        self._expected_checkpoint_sha256 = digest

    @staticmethod
    def _wish_sha256(payload: Mapping[str, Any]) -> str:
        for item in payload["inputs"]:
            if item["path"] == "WISH.json":
                return item["sha256"]
        raise StateConflict("agent run Wish input is missing")

    @staticmethod
    def _stage_artifacts(
        payload: Mapping[str, Any], by_path: Mapping[str, Mapping[str, Any]]
    ) -> dict[str, tuple[AgentArtifact, ...]]:
        return {
            stage: tuple(
                AgentArtifact(path, by_path[path]["sha256"])
                for path in paths
            )
            for stage, paths in payload["stage_artifacts"].items()
        }

    def snapshot(self) -> AgentRunCheckpoint:
        payload = self._load()
        by_path = {item["path"]: item for item in payload["sealed_artifacts"]}
        return AgentRunCheckpoint(
            product_id=payload["product_id"],
            stage=payload["stage"],
            status=payload["status"],
            revision=payload["revision"],
            round_index=payload["round_index"],
            max_rounds=payload["max_rounds"],
            wish_sha256=self._wish_sha256(payload),
            run_root_sha256=payload["run_root_sha256"],
            host_state_root_sha256=payload["host_state_root_sha256"],
            checkpoint_sha256=payload["checkpoint_sha256"],
            input_sha256s=MappingProxyType(
                {item["path"]: item["sha256"] for item in payload["inputs"]}
            ),
            stage_artifacts=MappingProxyType(self._stage_artifacts(payload, by_path)),
            invalidated_stages=tuple(payload["invalidated_stages"]),
        )

    def expected_gate_subject_sha256(self) -> str:
        payload = self._load()
        stage = payload["stage"]
        if stage == "wish":
            return self._wish_sha256(payload)
        upstream = _UPSTREAM_STAGE[stage]
        paths = payload["stage_artifacts"].get(upstream)
        if not paths:
            raise TransitionError("agent run lacks the sealed upstream stage artifact")
        by_path = {item["path"]: item for item in payload["sealed_artifacts"]}
        return by_path[paths[0]]["sha256"]

    def validate_outcome(self, value: AgentOutcome | Mapping[str, Any]) -> AgentOutcome:
        outcome = value if isinstance(value, AgentOutcome) else AgentOutcome.from_mapping(value)
        payload = self._load()
        self._validate_current_outcome(payload, outcome)
        self._verify_outcome_artifacts(payload, outcome)
        return outcome

    def _validate_current_outcome(
        self, payload: Mapping[str, Any], outcome: AgentOutcome
    ) -> None:
        if payload["status"] != "active":
            raise TransitionError("agent run is not active at its current stage")
        if outcome.stage != payload["stage"]:
            raise TransitionError("agent outcome is for a different stage")
        if outcome.status == "ready":
            allowed = _FORWARD_TRANSITIONS[outcome.stage]
            if outcome.stage == "playtest":
                if outcome.proposed_transition not in (allowed, "make"):
                    raise TransitionError("Playtest may advance or return feedback to Make")
            elif outcome.proposed_transition != allowed:
                raise TransitionError("agent proposed an illegal lifecycle transition")

    def _verify_outcome_artifacts(
        self,
        payload: Mapping[str, Any],
        outcome: AgentOutcome,
        additional_artifacts: Sequence[AgentArtifact] = (),
    ) -> list[dict[str, Any]]:
        existing = {item["path"]: item for item in payload["sealed_artifacts"]}
        additions: list[dict[str, Any]] = []
        total = sum(item["size"] for item in payload["sealed_artifacts"])
        for artifact in tuple(outcome.artifacts) + tuple(additional_artifacts):
            relative = _safe_relative(artifact.path, "agent artifact path")
            content, size = _read_relative_regular(self.run_root, relative)
            _reject_private_agent_bytes(artifact.path, content)
            if _sha256(content) != artifact.sha256:
                raise ArtifactError("agent artifact hash does not match its bytes")
            previous = existing.get(artifact.path)
            if previous is not None and previous["sha256"] != artifact.sha256:
                raise ArtifactError("a sealed artifact path cannot be reused for changed bytes")
            if previous is None:
                additions.append(
                    {"path": artifact.path, "sha256": artifact.sha256, "size": size}
                )
                total += size
        if total > MAX_AGENT_REFERENCED_BYTES:
            raise ArtifactError("agent run referenced artifacts exceed their total limit")
        return additions

    def apply_outcome(
        self,
        value: AgentOutcome | Mapping[str, Any],
        *,
        gate: Optional[DeterministicGateReceipt] = None,
        gate_subject_sha256: Optional[str] = None,
        additional_artifacts: Sequence[AgentArtifact] = (),
    ) -> AgentRunCheckpoint:
        outcome = value if isinstance(value, AgentOutcome) else AgentOutcome.from_mapping(value)
        payload = self._load()
        self._validate_current_outcome(payload, outcome)
        host_artifacts = tuple(additional_artifacts)
        if len(host_artifacts) > MAX_HOST_SEALED_ARTIFACTS_PER_GATE:
            raise ArtifactError("host gate selected too many artifacts to seal")
        if not all(isinstance(item, AgentArtifact) for item in host_artifacts):
            raise ContractError("additional artifacts must use AgentArtifact values")
        if outcome.status != "ready" and host_artifacts:
            raise TransitionError("only a ready gated outcome may seal additional artifacts")
        outcome_paths = {item.path for item in outcome.artifacts}
        host_paths = [item.path for item in host_artifacts]
        if len(host_paths) != len(set(host_paths)) or outcome_paths & set(host_paths):
            raise ArtifactError("gate artifact paths must be unique")
        for artifact in host_artifacts:
            parts = _safe_relative(artifact.path, "host gate artifact path").parts
            if len(parts) < 3 or parts[:2] != ("artifacts", outcome.stage):
                raise ArtifactError(
                    "host gate artifacts must live under artifacts/%s" % outcome.stage
                )
        all_artifacts = tuple(outcome.artifacts) + host_artifacts
        additions = self._verify_outcome_artifacts(
            payload, outcome, additional_artifacts=host_artifacts
        )
        if outcome.status != "ready":
            if gate is not None:
                raise TransitionError("waiting or failed outcomes cannot consume a gate")
            updated = dict(payload)
            updated["sealed_artifacts"] = payload["sealed_artifacts"] + additions
            updated["status"] = outcome.status
            updated["last_outcome_sha256"] = outcome.sha256
            updated["history"] = payload["history"] + [
                {
                    "stage": outcome.stage,
                    "status": outcome.status,
                    "outcome_sha256": outcome.sha256,
                    "artifact_paths": [item.path for item in outcome.artifacts],
                    "gate_sha256": None,
                    "transition": None,
                }
            ]
            self._write_next(payload, updated)
            return self.snapshot()

        if not isinstance(gate, DeterministicGateReceipt):
            raise TransitionError("a host deterministic gate receipt is required")
        if gate_subject_sha256 is None:
            subject = self.expected_gate_subject_sha256()
        else:
            subject = require_sha256(
                gate_subject_sha256, "expected deterministic gate subject sha256"
            )
        if (
            gate.stage != outcome.stage
            or gate.outcome_sha256 != outcome.sha256
            or gate.subject_sha256 != subject
        ):
            raise TransitionError("deterministic gate is not bound to this exact outcome")
        if outcome.stage == "playtest" and outcome.proposed_transition == "make":
            if gate.passed:
                raise TransitionError("passing Playtest must advance to Release")
            if payload["round_index"] >= payload["max_rounds"]:
                raise TransitionError("Make-Playtest round budget is exhausted")
        elif not gate.passed:
            raise TransitionError("a failed deterministic gate cannot advance")

        updated = dict(payload)
        updated["sealed_artifacts"] = payload["sealed_artifacts"] + additions
        stage_artifacts = {
            stage: list(paths) for stage, paths in payload["stage_artifacts"].items()
        }
        invalidated = set(payload["invalidated_stages"])
        if outcome.stage == "make":
            old_paths = stage_artifacts.get("make")
            old_binding: tuple[tuple[str, str], ...] = ()
            if old_paths:
                by_path = {item["path"]: item for item in payload["sealed_artifacts"]}
                old_binding = tuple(
                    (path, by_path[path]["sha256"]) for path in old_paths
                )
            new_binding = tuple(
                (artifact.path, artifact.sha256) for artifact in all_artifacts
            )
            if old_binding and old_binding != new_binding:
                for stage in _DOWNSTREAM_OF_MAKE:
                    stage_artifacts.pop(stage, None)
                    invalidated.add(stage)
        stage_artifacts[outcome.stage] = [item.path for item in all_artifacts]
        invalidated.discard(outcome.stage)

        transition = outcome.proposed_transition
        round_index = payload["round_index"]
        status = "active"
        next_stage = transition
        if outcome.stage == "invent" and transition == "make":
            round_index = 1
        elif outcome.stage == "playtest" and transition == "make":
            round_index += 1
            for stage in _DOWNSTREAM_OF_MAKE:
                invalidated.add(stage)
            next_stage = "make"
        elif transition == "complete":
            next_stage = "deliver"
            status = "complete"

        updated["stage"] = next_stage
        updated["status"] = status
        updated["round_index"] = round_index
        updated["stage_artifacts"] = stage_artifacts
        updated["invalidated_stages"] = [
            stage for stage in AGENT_RUN_STAGES if stage in invalidated
        ]
        updated["last_outcome_sha256"] = outcome.sha256
        updated["history"] = payload["history"] + [
            {
                "stage": outcome.stage,
                "status": outcome.status,
                "outcome_sha256": outcome.sha256,
                "artifact_paths": [item.path for item in all_artifacts],
                "gate_sha256": gate.sha256,
                "gate_id": gate.gate_id,
                "gate_passed": gate.passed,
                "gate_evidence_sha256": gate.evidence_sha256,
                "transition": transition,
            }
        ]
        self._write_next(payload, updated)
        return self.snapshot()

    def resume(self) -> AgentRunCheckpoint:
        payload = self._load()
        if payload["status"] != "waiting":
            raise TransitionError("only a waiting agent run can be resumed")
        updated = dict(payload)
        updated["status"] = "active"
        updated["history"] = payload["history"] + [
            {
                "stage": payload["stage"],
                "status": "resumed",
                "outcome_sha256": payload["last_outcome_sha256"],
                "artifact_paths": [],
                "gate_sha256": None,
                "transition": None,
            }
        ]
        self._write_next(payload, updated)
        return self.snapshot()


__all__ = [
    "AGENT_OUTCOME_STATUSES",
    "AGENT_RUN_STAGES",
    "AgentArtifact",
    "AgentOutcome",
    "AgentRun",
    "AgentRunCheckpoint",
    "DeterministicGateReceipt",
]
