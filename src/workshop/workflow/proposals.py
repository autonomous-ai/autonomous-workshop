"""Strict reader for one native agent's compact stage proposal.

The proposal file is untrusted input.  It names no credentials and grants no
authority; it only binds an :class:`AgentOutcome` to the exact host checkpoint
and gate subject the native session was asked to work from.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence

from workshop._validation import require_safe_evidence_path, require_sha256
from workshop.errors import ArtifactError, ContractError, StateConflict
from workshop.workflow.agent_run import AgentOutcome


AGENT_OUTCOME_PROPOSAL_KIND = "autonomous-workshop.agent-outcome-proposal"
MAX_AGENT_OUTCOME_PROPOSAL_BYTES = 128 * 1024
MAX_STAGE_CONTRACT_BYTES = 2 * 1024 * 1024


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
        raise ContractError("agent proposal values must be finite JSON") from exc


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _canonical_run_root(value: Path) -> Path:
    try:
        requested = Path(value)
    except TypeError as exc:
        raise ContractError("agent run root must be path-like") from exc
    if not requested.is_absolute() or requested.is_symlink():
        raise ContractError("agent run root must be an absolute real directory")
    try:
        identity = requested.lstat()
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise ArtifactError("agent run root is unavailable") from exc
    if (
        requested != resolved
        or not stat.S_ISDIR(identity.st_mode)
        or not requested.is_dir()
    ):
        raise ContractError("agent run root must be an absolute canonical directory")
    return requested


def _read_relative_regular(
    run_root: Path,
    relative_path: str,
    *,
    maximum_bytes: int,
    label: str,
) -> bytes:
    if type(maximum_bytes) is not int or maximum_bytes < 1:
        raise ContractError("artifact byte limit must be a positive integer")
    root = _canonical_run_root(run_root)
    safe = PurePosixPath(require_safe_evidence_path(relative_path, label + " path"))
    read_flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    directory_flags = read_flags | getattr(os, "O_DIRECTORY", 0)
    root_descriptor: int | None = None
    directory_descriptor: int | None = None
    file_descriptor: int | None = None
    try:
        expected_root = root.lstat()
        root_descriptor = os.open(str(root), directory_flags)
        opened_root = os.fstat(root_descriptor)
        if (
            not stat.S_ISDIR(opened_root.st_mode)
            or (opened_root.st_dev, opened_root.st_ino)
            != (expected_root.st_dev, expected_root.st_ino)
        ):
            raise ArtifactError("agent run root changed while opening")
        directory_descriptor = root_descriptor
        root_descriptor = None
        for part in safe.parts[:-1]:
            child = os.open(part, directory_flags, dir_fd=directory_descriptor)
            opened_directory = os.fstat(child)
            if not stat.S_ISDIR(opened_directory.st_mode):
                os.close(child)
                raise ArtifactError("%s path contains a non-directory" % label)
            os.close(directory_descriptor)
            directory_descriptor = child

        file_descriptor = os.open(
            safe.parts[-1], read_flags, dir_fd=directory_descriptor
        )
        opened = os.fstat(file_descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise ArtifactError("%s must be a regular file" % label)
        if not 1 <= opened.st_size <= maximum_bytes:
            raise ArtifactError(
                "%s must be non-empty and at most %d bytes"
                % (label, maximum_bytes)
            )
        chunks: list[bytes] = []
        length = 0
        while length <= maximum_bytes:
            chunk = os.read(
                file_descriptor,
                min(1024 * 1024, maximum_bytes + 1 - length),
            )
            if not chunk:
                break
            chunks.append(chunk)
            length += len(chunk)
        content = b"".join(chunks)
        if len(content) > maximum_bytes or os.read(file_descriptor, 1):
            raise ArtifactError("%s exceeds its byte limit" % label)
        after = os.fstat(file_descriptor)
        if (
            len(content) != opened.st_size
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ArtifactError("%s changed while reading" % label)
        return content
    except OSError as exc:
        raise ArtifactError("%s cannot be opened without following links" % label) from exc
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if directory_descriptor is not None:
            os.close(directory_descriptor)
        if root_descriptor is not None:
            os.close(root_descriptor)


def read_bounded_json_artifact(
    run_root: Path,
    relative_path: str,
    *,
    maximum_bytes: int = MAX_STAGE_CONTRACT_BYTES,
    label: str = "agent JSON artifact",
) -> tuple[dict[str, Any], bytes]:
    """Read a strict JSON object beneath a real run root without following links."""

    content = _read_relative_regular(
        run_root,
        relative_path,
        maximum_bytes=maximum_bytes,
        label=label,
    )
    try:
        document = json.loads(
            content.decode("utf-8"), object_pairs_hook=_strict_object
        )
    except (UnicodeError, ValueError, RecursionError, json.JSONDecodeError) as exc:
        raise ContractError("%s must contain strict UTF-8 JSON" % label) from exc
    if not isinstance(document, dict):
        raise ContractError("%s must contain one JSON object" % label)
    return document, content


@dataclass(frozen=True)
class AgentOutcomeProposal:
    """Untrusted outcome envelope pinned to one host checkpoint and subject."""

    checkpoint_sha256: str
    subject_sha256: str
    outcome: AgentOutcome
    schema_version: int = 1
    kind: str = AGENT_OUTCOME_PROPOSAL_KIND

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("agent outcome proposal schema_version must be 1")
        if self.kind != AGENT_OUTCOME_PROPOSAL_KIND:
            raise ContractError("agent outcome proposal kind is invalid")
        require_sha256(self.checkpoint_sha256, "agent outcome checkpoint sha256")
        require_sha256(self.subject_sha256, "agent outcome subject sha256")
        if not isinstance(self.outcome, AgentOutcome):
            raise ContractError("agent outcome proposal requires an AgentOutcome")
        if len(_canonical_json(self.to_dict())) > MAX_AGENT_OUTCOME_PROPOSAL_BYTES:
            raise ContractError("agent outcome proposal exceeds its byte limit")

    @property
    def sha256(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict())).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "checkpoint_sha256": self.checkpoint_sha256,
            "subject_sha256": self.subject_sha256,
            "outcome": self.outcome.to_dict(),
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "AgentOutcomeProposal":
        expected = {
            "schema_version",
            "kind",
            "checkpoint_sha256",
            "subject_sha256",
            "outcome",
        }
        if not isinstance(value, Mapping) or set(value) != expected:
            raise ContractError("agent outcome proposal fields are invalid")
        return cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            checkpoint_sha256=value["checkpoint_sha256"],
            subject_sha256=value["subject_sha256"],
            outcome=AgentOutcome.from_mapping(value["outcome"]),
        )


def read_agent_outcome_proposal(
    run_root: Path,
    *,
    expected_checkpoint_sha256: str,
    expected_subject_sha256: str,
) -> AgentOutcomeProposal:
    """Read ``agent-outcome.json`` and reject stale or cross-run proposals."""

    require_sha256(expected_checkpoint_sha256, "expected checkpoint sha256")
    require_sha256(expected_subject_sha256, "expected gate subject sha256")
    document, _ = read_bounded_json_artifact(
        run_root,
        "agent-outcome.json",
        maximum_bytes=MAX_AGENT_OUTCOME_PROPOSAL_BYTES,
        label="agent-outcome.json",
    )
    proposal = AgentOutcomeProposal.from_mapping(document)
    if proposal.checkpoint_sha256 != expected_checkpoint_sha256:
        raise StateConflict("agent outcome was produced from another checkpoint")
    if proposal.subject_sha256 != expected_subject_sha256:
        raise StateConflict("agent outcome was produced from another gate subject")
    return proposal


__all__ = [
    "AGENT_OUTCOME_PROPOSAL_KIND",
    "AgentOutcomeProposal",
    "MAX_AGENT_OUTCOME_PROPOSAL_BYTES",
    "MAX_STAGE_CONTRACT_BYTES",
    "read_agent_outcome_proposal",
    "read_bounded_json_artifact",
]
