"""Trusted, deterministic CAD gate for a native-agent Make handoff.

The native agent may create the product tree, but it cannot attest that its CAD
is valid.  This module re-identifies the exact :class:`NativeMade` tree, copies
only its declared CAD project into a disposable directory, and runs the
materialized CAD verifier there.  The sealed source tree is never passed to a
process that can write to it.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Optional, Sequence

from workshop._validation import require_sha256
from workshop.artifacts import ArtifactEntry
from workshop.errors import ArtifactError, ContractError
from workshop.make.native import NativeMade
from workshop.runtime.execution import minimal_tool_environment


NATIVE_CAD_GATE_KIND = "autonomous-workshop.native-cad-gate-evidence"
NATIVE_CAD_VERIFIER_PATH = ".agents/skills/cad/scripts/verify_project"
NATIVE_CAD_VERIFIER_MODE = "final-fresh-exports-strict-fit"
DEFAULT_NATIVE_CAD_TIMEOUT_SECONDS = 1_800.0
DEFAULT_NATIVE_CAD_OUTPUT_BYTES = 64 * 1024
MAX_NATIVE_CAD_OUTPUT_BYTES = 1024 * 1024
MAX_NATIVE_CAD_VERIFIER_BYTES = 4 * 1024 * 1024


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
        raise ContractError("native CAD gate values must be finite JSON") from exc


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _safe_relative(value: str, label: str) -> PurePosixPath:
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
        raise ArtifactError("%s must be a safe relative POSIX path" % label)
    return candidate


def _canonical_directory(value: Path, label: str) -> Path:
    requested = Path(value)
    if not requested.is_absolute() or requested.is_symlink():
        raise ArtifactError("%s must be an absolute real directory" % label)
    try:
        resolved = requested.resolve(strict=True)
        identity = requested.lstat()
    except OSError as exc:
        raise ArtifactError("%s is unavailable" % label) from exc
    if requested != resolved or not stat.S_ISDIR(identity.st_mode):
        raise ArtifactError("%s must be an absolute real directory" % label)
    return resolved


def _checked_directory(root: Path, relative: PurePosixPath, label: str) -> Path:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            identity = current.lstat()
        except OSError as exc:
            raise ArtifactError("%s is unavailable" % label) from exc
        if stat.S_ISLNK(identity.st_mode) or not stat.S_ISDIR(identity.st_mode):
            raise ArtifactError("%s must not contain symlinks or non-directories" % label)
    try:
        current.relative_to(root)
    except ValueError as exc:
        raise ArtifactError("%s escapes its trusted root" % label) from exc
    return current


def _read_regular(
    path: Path, label: str, maximum_bytes: int
) -> tuple[bytes, os.stat_result]:
    try:
        expected = path.lstat()
    except OSError as exc:
        raise ArtifactError("%s is unavailable" % label) from exc
    if stat.S_ISLNK(expected.st_mode) or not stat.S_ISREG(expected.st_mode):
        raise ArtifactError("%s must be a regular non-symlink file" % label)
    if expected.st_size < 0 or expected.st_size > maximum_bytes:
        raise ArtifactError("%s exceeds its byte limit" % label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
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
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(64 * 1024, maximum_bytes + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum_bytes:
                raise ArtifactError("%s exceeds its byte limit" % label)
        after = os.fstat(descriptor)
        if (
            (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
        ):
            raise ArtifactError("%s changed while reading" % label)
        return b"".join(chunks), after
    finally:
        os.close(descriptor)


def _inventory_exact_tree(root: Path) -> tuple[set[str], set[str]]:
    """Return every file and directory and reject links/special entries."""

    files: set[str] = set()
    directories: set[str] = set()
    for directory, dirnames, filenames in os.walk(str(root), followlinks=False):
        base = Path(directory)
        kept: list[str] = []
        for name in sorted(dirnames):
            absolute = base / name
            relative = absolute.relative_to(root).as_posix()
            try:
                identity = absolute.lstat()
            except OSError as exc:
                raise ArtifactError("native Made tree changed during inventory") from exc
            if stat.S_ISLNK(identity.st_mode) or not stat.S_ISDIR(identity.st_mode):
                raise ArtifactError(
                    "native Made tree contains a symlink or special directory: %s"
                    % relative
                )
            directories.add(relative)
            kept.append(name)
        dirnames[:] = kept
        for name in sorted(filenames):
            absolute = base / name
            relative = absolute.relative_to(root).as_posix()
            try:
                identity = absolute.lstat()
            except OSError as exc:
                raise ArtifactError("native Made tree changed during inventory") from exc
            if stat.S_ISLNK(identity.st_mode) or not stat.S_ISREG(identity.st_mode):
                raise ArtifactError(
                    "native Made tree contains a symlink or special file: %s"
                    % relative
                )
            files.add(relative)
    return files, directories


def _declared_directories(paths: set[str]) -> set[str]:
    result: set[str] = set()
    for value in paths:
        parent = PurePosixPath(value).parent
        while parent.as_posix() != ".":
            result.add(parent.as_posix())
            parent = parent.parent
    return result


def _validate_exact_product_tree(made: NativeMade, run_root: Path) -> Path:
    """Rehash NativeMade and reject even manifest-excluded extra nodes."""

    made.validate_product_tree(run_root)
    relative = _safe_relative(made.product_root, "native Made product root")
    product_root = _checked_directory(run_root, relative, "native Made product tree")
    actual_files, actual_directories = _inventory_exact_tree(product_root)
    declared_files = {entry.path for entry in made.product_manifest.entries}
    if actual_files != declared_files:
        raise ArtifactError("native Made product tree has undeclared or missing files")
    if actual_directories != _declared_directories(declared_files):
        raise ArtifactError("native Made product tree has undeclared or missing directories")
    return product_root


def _cad_entries(made: NativeMade) -> tuple[ArtifactEntry, ...]:
    project = _safe_relative(made.cad_project_path, "native Made CAD project")
    prefix = project.as_posix() + "/"
    selected = tuple(
        ArtifactEntry(
            path=entry.path[len(prefix) :],
            bytes=entry.bytes,
            sha256=entry.sha256,
            executable=entry.executable,
        )
        for entry in made.product_manifest.entries
        if entry.path.startswith(prefix)
    )
    if not selected:
        raise ArtifactError("native Made CAD project has no declared files")
    paths = [entry.path for entry in selected]
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ArtifactError("native Made CAD project inventory is not canonical")
    return selected


def _entries_sha256(entries: Sequence[ArtifactEntry]) -> str:
    return hashlib.sha256(_canonical_json([asdict(entry) for entry in entries])).hexdigest()


def _copy_declared_project(
    source_root: Path,
    destination_root: Path,
    entries: Sequence[ArtifactEntry],
) -> None:
    destination_root.mkdir(mode=0o700)
    for entry in entries:
        relative = _safe_relative(entry.path, "native CAD project entry")
        source = source_root.joinpath(*relative.parts)
        content, identity = _read_regular(
            source, "native CAD project entry %s" % entry.path, entry.bytes
        )
        if (
            len(content) != entry.bytes
            or hashlib.sha256(content).hexdigest() != entry.sha256
            or bool(identity.st_mode & stat.S_IXUSR) != entry.executable
        ):
            raise ArtifactError(
                "native CAD project entry differs from its manifest: %s"
                % entry.path
            )
        destination = destination_root.joinpath(*relative.parts)
        destination.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(
            str(destination), flags, 0o700 if entry.executable else 0o600
        )
        try:
            written = 0
            while written < len(content):
                written += os.write(descriptor, content[written:])
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    copied_files, copied_directories = _inventory_exact_tree(destination_root)
    declared = {entry.path for entry in entries}
    if copied_files != declared or copied_directories != _declared_directories(declared):
        raise ArtifactError("isolated CAD project differs from its declared inventory")


def _assert_copied_inputs_unchanged(
    project_root: Path, entries: Sequence[ArtifactEntry]
) -> None:
    for entry in entries:
        relative = _safe_relative(entry.path, "native CAD project entry")
        content, identity = _read_regular(
            project_root.joinpath(*relative.parts),
            "isolated CAD project entry %s" % entry.path,
            entry.bytes,
        )
        if (
            len(content) != entry.bytes
            or hashlib.sha256(content).hexdigest() != entry.sha256
            or bool(identity.st_mode & stat.S_IXUSR) != entry.executable
        ):
            raise ArtifactError("CAD verifier changed a declared project file: %s" % entry.path)


@dataclass(frozen=True)
class CapturedVerifierStream:
    """One bounded stream plus an identity for all bytes that were drained."""

    content: bytes
    total_bytes: int
    sha256: str
    truncated: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.content, bytes):
            raise ContractError("captured CAD verifier output must be bytes")
        if type(self.total_bytes) is not int or self.total_bytes < len(self.content):
            raise ContractError("captured CAD verifier byte count is invalid")
        require_sha256(self.sha256, "captured CAD verifier output sha256")
        if type(self.truncated) is not bool or self.truncated != (
            self.total_bytes > len(self.content)
        ):
            raise ContractError("captured CAD verifier truncation marker is invalid")

    @classmethod
    def from_bytes(cls, content: bytes, maximum_bytes: int) -> "CapturedVerifierStream":
        if not isinstance(content, bytes):
            raise ContractError("captured CAD verifier output must be bytes")
        return cls(
            content=content[:maximum_bytes],
            total_bytes=len(content),
            sha256=hashlib.sha256(content).hexdigest(),
            truncated=len(content) > maximum_bytes,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "captured_text": self.content.decode("utf-8", errors="replace"),
            "captured_bytes": len(self.content),
            "total_bytes": self.total_bytes,
            "sha256": self.sha256,
            "truncated": self.truncated,
        }


@dataclass(frozen=True)
class VerifierProcessResult:
    """Dependency-injection boundary for the untrusted verifier process."""

    returncode: int
    stdout: CapturedVerifierStream
    stderr: CapturedVerifierStream
    duration_ms: int
    timed_out: bool = False

    def __post_init__(self) -> None:
        if type(self.returncode) is not int:
            raise ContractError("CAD verifier return code must be an integer")
        if not isinstance(self.stdout, CapturedVerifierStream) or not isinstance(
            self.stderr, CapturedVerifierStream
        ):
            raise ContractError("CAD verifier result requires bounded streams")
        if type(self.duration_ms) is not int or self.duration_ms < 0:
            raise ContractError("CAD verifier duration must be a nonnegative integer")
        if type(self.timed_out) is not bool:
            raise ContractError("CAD verifier timeout marker must be boolean")

    @classmethod
    def from_bytes(
        cls,
        returncode: int,
        stdout: bytes = b"",
        stderr: bytes = b"",
        *,
        duration_ms: int = 0,
        timed_out: bool = False,
        maximum_bytes: int = DEFAULT_NATIVE_CAD_OUTPUT_BYTES,
    ) -> "VerifierProcessResult":
        return cls(
            returncode=returncode,
            stdout=CapturedVerifierStream.from_bytes(stdout, maximum_bytes),
            stderr=CapturedVerifierStream.from_bytes(stderr, maximum_bytes),
            duration_ms=duration_ms,
            timed_out=timed_out,
        )


VerifierRunner = Callable[..., VerifierProcessResult]


class _Capture:
    def __init__(self, maximum_bytes: int) -> None:
        self.maximum_bytes = maximum_bytes
        self.content = bytearray()
        self.total_bytes = 0
        self.digest = hashlib.sha256()

    def drain(self, stream: Any) -> None:
        try:
            while True:
                chunk = stream.read(64 * 1024)
                if not chunk:
                    return
                self.total_bytes += len(chunk)
                self.digest.update(chunk)
                remaining = self.maximum_bytes - len(self.content)
                if remaining > 0:
                    self.content.extend(chunk[:remaining])
        finally:
            stream.close()

    def result(self) -> CapturedVerifierStream:
        return CapturedVerifierStream(
            content=bytes(self.content),
            total_bytes=self.total_bytes,
            sha256=self.digest.hexdigest(),
            truncated=self.total_bytes > len(self.content),
        )


def run_bounded_verifier(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: float,
    max_output_bytes: int,
) -> VerifierProcessResult:
    """Run without a shell while draining stdout and stderr into hard bounds."""

    started = time.monotonic()
    process = subprocess.Popen(
        list(command),
        cwd=str(cwd),
        env=dict(environment),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        close_fds=True,
        start_new_session=True,
    )
    if process.stdout is None or process.stderr is None:  # pragma: no cover - Popen contract
        process.kill()
        raise ArtifactError("CAD verifier output pipes are unavailable")
    stdout = _Capture(max_output_bytes)
    stderr = _Capture(max_output_bytes)
    threads = (
        threading.Thread(target=stdout.drain, args=(process.stdout,), daemon=True),
        threading.Thread(target=stderr.drain, args=(process.stderr,), daemon=True),
    )
    for thread in threads:
        thread.start()
    timed_out = False
    try:
        returncode = process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except (AttributeError, OSError):
            process.kill()
        returncode = process.wait()
    for thread in threads:
        thread.join()
    duration_ms = max(0, int(round((time.monotonic() - started) * 1000)))
    return VerifierProcessResult(
        returncode=returncode,
        stdout=stdout.result(),
        stderr=stderr.result(),
        duration_ms=duration_ms,
        timed_out=timed_out,
    )


@dataclass(frozen=True)
class NativeCadGateEvidence:
    """Host-owned evidence for one exact NativeMade CAD verification."""

    passed: bool
    failure_code: Optional[str]
    made_sha256: str
    product_artifact_sha256: str
    cad_project_path: str
    cad_project_sha256: str
    verifier_sha256: str
    command: tuple[str, ...]
    returncode: int
    duration_ms: int
    timed_out: bool
    stdout: CapturedVerifierStream
    stderr: CapturedVerifierStream
    source_tree_unchanged: bool
    schema_version: int = 1
    kind: str = NATIVE_CAD_GATE_KIND
    verifier_path: str = NATIVE_CAD_VERIFIER_PATH
    verifier_mode: str = NATIVE_CAD_VERIFIER_MODE
    receipt_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("native CAD gate schema_version must be 1")
        if self.kind != NATIVE_CAD_GATE_KIND:
            raise ContractError("native CAD gate kind is invalid")
        if type(self.passed) is not bool or type(self.source_tree_unchanged) is not bool:
            raise ContractError("native CAD gate booleans are invalid")
        if self.passed != (self.failure_code is None):
            raise ContractError("native CAD gate result and failure code disagree")
        if self.failure_code is not None and (
            not isinstance(self.failure_code, str)
            or not self.failure_code
            or len(self.failure_code) > 64
        ):
            raise ContractError("native CAD gate failure code is invalid")
        for value, label in (
            (self.made_sha256, "native CAD gate Made sha256"),
            (self.product_artifact_sha256, "native CAD gate product sha256"),
            (self.cad_project_sha256, "native CAD gate project sha256"),
            (self.verifier_sha256, "native CAD gate verifier sha256"),
        ):
            require_sha256(value, label)
        _safe_relative(self.cad_project_path, "native CAD gate project path")
        _safe_relative(self.verifier_path, "native CAD gate verifier path")
        if self.verifier_mode != NATIVE_CAD_VERIFIER_MODE:
            raise ContractError("native CAD gate verifier mode is invalid")
        if not isinstance(self.command, tuple) or not self.command or not all(
            isinstance(item, str) and item for item in self.command
        ):
            raise ContractError("native CAD gate command is invalid")
        if len(self.command) < 2 or self.command[1] != self.verifier_path:
            raise ContractError(
                "native CAD gate command differs from its verifier path"
            )
        if (
            type(self.returncode) is not int
            or type(self.duration_ms) is not int
            or self.duration_ms < 0
        ):
            raise ContractError("native CAD gate process result is invalid")
        if type(self.timed_out) is not bool:
            raise ContractError("native CAD gate timeout marker is invalid")
        if not isinstance(self.stdout, CapturedVerifierStream) or not isinstance(
            self.stderr, CapturedVerifierStream
        ):
            raise ContractError("native CAD gate output is invalid")
        object.__setattr__(
            self,
            "receipt_sha256",
            hashlib.sha256(_canonical_json(self._identity_dict())).hexdigest(),
        )

    def _identity_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "passed": self.passed,
            "failure_code": self.failure_code,
            "made_sha256": self.made_sha256,
            "product_artifact_sha256": self.product_artifact_sha256,
            "cad_project_path": self.cad_project_path,
            "cad_project_sha256": self.cad_project_sha256,
            "verifier_path": self.verifier_path,
            "verifier_sha256": self.verifier_sha256,
            "verifier_mode": self.verifier_mode,
            "command": list(self.command),
            "returncode": self.returncode,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "stdout": self.stdout.to_dict(),
            "stderr": self.stderr.to_dict(),
            "source_tree_unchanged": self.source_tree_unchanged,
        }

    def to_dict(self) -> dict[str, Any]:
        value = self._identity_dict()
        value["receipt_sha256"] = self.receipt_sha256
        return value


class NativeCadGateError(ArtifactError):
    """A failed CAD gate whose host evidence was durably recorded."""

    def __init__(
        self,
        failure_code: str,
        evidence: NativeCadGateEvidence,
        evidence_path: Path,
    ) -> None:
        super().__init__("native CAD gate failed: %s" % failure_code)
        self.failure_code = failure_code
        self.evidence = evidence
        self.evidence_path = evidence_path


def _evidence_path(host_state_root: Path, made: NativeMade) -> Path:
    parent = host_state_root / "evidence" / "make"
    current = host_state_root
    for part in ("evidence", "make"):
        candidate = current / part
        try:
            identity = candidate.lstat()
        except FileNotFoundError:
            candidate.mkdir(mode=0o700)
            identity = candidate.lstat()
        except OSError as exc:
            raise ArtifactError("native CAD gate evidence directory is unavailable") from exc
        if stat.S_ISLNK(identity.st_mode) or not stat.S_ISDIR(identity.st_mode):
            raise ArtifactError("native CAD gate evidence directory is unsafe")
        os.chmod(candidate, 0o700)
        current = candidate
    return parent / ("r%04d-cad-gate.json" % made.round)


def _atomic_private_write(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name, suffix=".tmp", dir=str(path.parent)
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(str(temporary), str(path))
        os.chmod(path, 0o600, follow_symlinks=False)
        directory_descriptor = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise ArtifactError("native CAD gate evidence could not be persisted") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def verify_native_made_cad(
    made: NativeMade,
    *,
    run_root: Path,
    host_state_root: Path,
    expected_verifier_sha256: str,
    verifier_path: str = NATIVE_CAD_VERIFIER_PATH,
    runner: Optional[VerifierRunner] = None,
    python_executable: str = sys.executable,
    timeout_seconds: float = DEFAULT_NATIVE_CAD_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_NATIVE_CAD_OUTPUT_BYTES,
) -> NativeCadGateEvidence:
    """Run the final CAD gate on an isolated copy and persist host evidence.

    ``verifier_path`` and ``expected_verifier_sha256`` must come from the
    trusted Manager projection and AgentRun input checkpoint, not from the
    agent-writable run tree.  The Codex projection remains the default for
    direct callers that predate portable Manager runtimes.
    """

    if not isinstance(made, NativeMade):
        raise ContractError("native CAD gate requires NativeMade")
    require_sha256(expected_verifier_sha256, "expected CAD verifier sha256")
    if (
        not isinstance(python_executable, str)
        or not python_executable
        or "\x00" in python_executable
    ):
        raise ContractError("native CAD gate Python executable is invalid")
    if (
        not isinstance(timeout_seconds, (int, float))
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
        or timeout_seconds > 86_400
    ):
        raise ContractError("native CAD gate timeout is invalid")
    if (
        type(max_output_bytes) is not int
        or not 1 <= max_output_bytes <= MAX_NATIVE_CAD_OUTPUT_BYTES
    ):
        raise ContractError("native CAD gate output limit is invalid")

    root = _canonical_directory(run_root, "native CAD gate run root")
    host_root = _canonical_directory(
        host_state_root, "native CAD gate host state root"
    )
    if _is_within(root, host_root) or _is_within(host_root, root):
        raise ArtifactError("native CAD gate run and host-state roots must not overlap")
    if stat.S_IMODE(host_root.stat().st_mode) != 0o700:
        raise ArtifactError("native CAD gate host state root permissions must be 0700")
    evidence_path = _evidence_path(host_root, made)

    product_root = _validate_exact_product_tree(made, root)
    project_relative = _safe_relative(made.cad_project_path, "native Made CAD project")
    project_root = _checked_directory(
        product_root, project_relative, "native Made CAD project"
    )
    entries = _cad_entries(made)
    project_files, project_directories = _inventory_exact_tree(project_root)
    declared_project_files = {entry.path for entry in entries}
    if (
        project_files != declared_project_files
        or project_directories != _declared_directories(declared_project_files)
    ):
        raise ArtifactError("native Made CAD project differs from its declared inventory")
    project_sha256 = _entries_sha256(entries)

    verifier_relative = _safe_relative(verifier_path, "native CAD verifier")
    verifier_relative_path = verifier_relative.as_posix()
    verifier_parent = _checked_directory(
        root, verifier_relative.parent, "native CAD verifier directory"
    )
    verifier_absolute = verifier_parent / verifier_relative.name
    verifier_bytes, verifier_identity = _read_regular(
        verifier_absolute, "native CAD verifier", MAX_NATIVE_CAD_VERIFIER_BYTES
    )
    verifier_sha256 = hashlib.sha256(verifier_bytes).hexdigest()
    if verifier_sha256 != expected_verifier_sha256:
        raise ArtifactError("native CAD verifier differs from its trusted input hash")
    if not verifier_identity.st_mode & stat.S_IXUSR:
        raise ArtifactError("native CAD verifier is not executable")

    normalized_command = (
        "<python>",
        verifier_relative_path,
        "<isolated-cad-project>",
        "--fresh",
        "--exports",
        "--strict-fit",
    )
    selected_runner = runner or run_bounded_verifier
    result: Optional[VerifierProcessResult] = None
    source_unchanged = True
    failure_code: Optional[str] = None
    with tempfile.TemporaryDirectory(prefix="workshop-native-cad-gate-") as temporary:
        temporary_root = Path(temporary).resolve()
        isolated_project = temporary_root / "project"
        _copy_declared_project(project_root, isolated_project, entries)
        # Catch an input race before giving control to another process.
        _validate_exact_product_tree(made, root)
        command = (
            python_executable,
            str(verifier_absolute),
            str(isolated_project),
            "--fresh",
            "--exports",
            "--strict-fit",
        )
        environment = dict(minimal_tool_environment())
        environment["TMPDIR"] = str(temporary_root)
        try:
            candidate = selected_runner(
                command,
                cwd=temporary_root,
                environment=environment,
                timeout_seconds=float(timeout_seconds),
                max_output_bytes=max_output_bytes,
            )
            if not isinstance(candidate, VerifierProcessResult):
                raise ArtifactError("native CAD verifier runner returned an invalid result")
            if any(
                len(stream.content) > max_output_bytes
                for stream in (candidate.stdout, candidate.stderr)
            ):
                raise ArtifactError("native CAD verifier runner exceeded its output bound")
            result = candidate
        except (ArtifactError, ContractError):
            raise
        except Exception as exc:
            raise ArtifactError("native CAD verifier could not be invoked") from exc

        try:
            _validate_exact_product_tree(made, root)
        except (ArtifactError, ContractError):
            source_unchanged = False
            failure_code = "sealed-product-changed"
        if source_unchanged:
            try:
                _assert_copied_inputs_unchanged(isolated_project, entries)
            except (ArtifactError, ContractError):
                failure_code = "declared-cad-output-changed"
        if failure_code is None:
            if result.timed_out:
                failure_code = "verifier-timeout"
            elif result.stdout.truncated or result.stderr.truncated:
                failure_code = "verifier-output-limit"
            elif result.returncode != 0:
                failure_code = "verifier-nonzero"

    if result is None:  # pragma: no cover - guarded above
        raise ArtifactError("native CAD verifier produced no process result")
    evidence = NativeCadGateEvidence(
        passed=failure_code is None,
        failure_code=failure_code,
        made_sha256=made.made_sha256,
        product_artifact_sha256=made.product_manifest.artifact_sha256,
        cad_project_path=made.cad_project_path,
        cad_project_sha256=project_sha256,
        verifier_path=verifier_relative_path,
        verifier_sha256=verifier_sha256,
        command=normalized_command,
        returncode=result.returncode,
        duration_ms=result.duration_ms,
        timed_out=result.timed_out,
        stdout=result.stdout,
        stderr=result.stderr,
        source_tree_unchanged=source_unchanged,
    )
    _atomic_private_write(evidence_path, _canonical_json(evidence.to_dict()) + b"\n")
    if not evidence.passed:
        raise NativeCadGateError(evidence.failure_code or "unknown", evidence, evidence_path)
    return evidence


__all__ = [
    "CapturedVerifierStream",
    "DEFAULT_NATIVE_CAD_OUTPUT_BYTES",
    "DEFAULT_NATIVE_CAD_TIMEOUT_SECONDS",
    "NATIVE_CAD_GATE_KIND",
    "NATIVE_CAD_VERIFIER_MODE",
    "NATIVE_CAD_VERIFIER_PATH",
    "NativeCadGateError",
    "NativeCadGateEvidence",
    "VerifierProcessResult",
    "run_bounded_verifier",
    "verify_native_made_cad",
]
