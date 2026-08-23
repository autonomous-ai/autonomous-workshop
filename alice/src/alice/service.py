"""Hardened launchd service boundary for Alice.

Alice's durable engine remains the source of workflow truth.  This module owns
only the operating-system boundary: sanitized configuration, immutable runtime
identity, one worker, one fresh bounded CLI process per tick, and secret-free
health state.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import errno
import fcntl
import hashlib
from html import escape as xml_escape
import json
import math
import os
from pathlib import Path
import pwd
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from typing import Callable, Iterator, Mapping, MutableMapping, Sequence

from .config import load_config, resolve_runtime_paths
from .policy import release_policy_from_config


HEALTH_SCHEMA_VERSION = 2
RELEASE_SCHEMA_VERSION = 1
EX_TEMPFAIL = 75
EX_CONFIG = 78
ENV_FILE_MAX_BYTES = 1024 * 1024
HEALTH_FILE_MAX_BYTES = 64 * 1024
CONFIG_FILE_MAX_BYTES = 16 * 1024 * 1024
SOURCE_FILE_MAX_BYTES = 128 * 1024 * 1024
SOURCE_TREE_MAX_BYTES = 1024 * 1024 * 1024
CONTROL_OUTPUT_MAX_BYTES = 4 * 1024 * 1024
CHILD_OUTPUT_MAX_BYTES = 256 * 1024
GENERIC_COMMAND_ADAPTER_TIMEOUT_SECONDS = 1_800.0
_ENV_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EFFECT_MODES = frozenset({"dry-run", "draft", "live"})
_ISOLATED_SERVICE_BOOTSTRAP = (
    "import runpy,sys;"
    "source=sys.argv.pop(1);"
    "sys.path.insert(0,source);"
    "sys.argv[0]='alice.service';"
    "runpy.run_module('alice.service',run_name='__main__')"
)
_BASELINE_ENVIRONMENT = frozenset({"PATH", "HOME", "LANG", "LC_ALL", "TMPDIR"})
_DANGEROUS_ENVIRONMENT = frozenset(
    {
        "BASH_ENV",
        "ENV",
        "LD_PRELOAD",
        "PYTHONHOME",
        "PYTHONPATH",
        "PYTHONSTARTUP",
        "PYTHONINSPECT",
        "PYTHONBREAKPOINT",
    }
)
_CONFIG_OVERRIDE_ENVIRONMENT = frozenset(
    {
        "ALICE_DATABASE",
        "ALICE_EFFECT_MODE",
        "ALICE_AGENT_PROVIDER",
        "ALICE_POLL_SECONDS",
        "ALICE_CODEX_BINARY",
        "ALICE_CODEX_HOME",
        "ALICE_CODEX_MODEL",
        "ALICE_CODEX_EFFORT",
    }
)
_HEALTH_KEYS = frozenset(
    {
        "schema_version",
        "started_at",
        "heartbeat_at",
        "success_at",
        "failure_at",
        "tick_started_at",
        "consecutive_failures",
        "source_tree_sha256",
        "config_sha256",
        "policy_hash",
        "effect_mode",
        "pid",
        "message_hash",
    }
)
_WATCHDOG_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "checked_at",
        "healthy",
        "action",
        "source_tree_sha256",
        "config_sha256",
        "policy_hash",
        "effect_mode",
        "message_hash",
    }
)


class ServiceError(RuntimeError):
    """A service error whose message contains no credential values."""


class IdentityMismatch(ServiceError):
    """The live configuration or source does not match its installation pin."""


class WorkerAlreadyRunning(ServiceError):
    """The non-blocking single-worker lock is already held."""


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ServiceError("timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


def _parse_timestamp(value: object, field: str, *, optional: bool = False) -> datetime | None:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ServiceError(f"health field {field} is not a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ServiceError(f"health field {field} is not a UTC timestamp") from exc
    return parsed.astimezone(timezone.utc)


def message_hash(value: object) -> str:
    return hashlib.sha256(str(value).encode("utf-8", errors="replace")).hexdigest()


def _require_sha256(value: str, field: str) -> str:
    normalized = value.lower()
    if not _SHA256.fullmatch(normalized):
        raise ServiceError(f"{field} must be a SHA256 digest")
    return normalized


def _require_absolute(path: str | os.PathLike[str], name: str) -> Path:
    result = Path(path)
    if not result.is_absolute():
        raise ServiceError(f"{name} must be an absolute path")
    return result


def _check_path_components(
    path: Path,
    *,
    allow_missing_leaf: bool = False,
    allow_missing_parents: bool = False,
) -> None:
    """Reject symlinks in every existing path component."""

    path = _require_absolute(path, "path")
    current = Path(path.anchor)
    parts = path.parts[1:]
    for index, part in enumerate(parts):
        current /= part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            is_leaf = index == len(parts) - 1
            if (is_leaf and allow_missing_leaf) or allow_missing_parents:
                continue
            raise ServiceError("required path component is unavailable")
        except OSError as exc:
            raise ServiceError("path component could not be inspected") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise ServiceError("symlink path components are not allowed")


def _secure_read_file(path: Path, *, maximum_bytes: int, purpose: str) -> bytes:
    _check_path_components(path)
    try:
        before = path.lstat()
    except OSError as exc:
        raise ServiceError(f"{purpose} is unavailable") from exc
    if not stat.S_ISREG(before.st_mode):
        raise ServiceError(f"{purpose} must be a regular file")
    if before.st_size > maximum_bytes:
        raise ServiceError(f"{purpose} is too large")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ServiceError(f"{purpose} could not be opened safely") from exc
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise ServiceError(f"{purpose} changed while opening")
        if not stat.S_ISREG(opened.st_mode):
            raise ServiceError(f"{purpose} must be a regular file")
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
    finally:
        os.close(descriptor)
    if len(content) > maximum_bytes:
        raise ServiceError(f"{purpose} is too large")
    return content


def _decode_env_value(raw: str, line_number: int) -> str:
    if not raw:
        return ""
    if raw[0] not in {"'", '"'}:
        if "\x00" in raw:
            raise ServiceError(f"invalid environment value on line {line_number}")
        return raw
    if len(raw) < 2 or raw[-1] != raw[0]:
        raise ServiceError(f"unterminated environment value on line {line_number}")
    if raw[0] == "'":
        return raw[1:-1]
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ServiceError(f"invalid quoted environment value on line {line_number}") from exc
    if not isinstance(value, str):
        raise ServiceError(f"invalid environment value on line {line_number}")
    return value


def load_env_file(path: str | os.PathLike[str]) -> dict[str, str]:
    """Read an owner-only dotenv file without sourcing it or changing os.environ."""

    env_path = _require_absolute(path, "environment file")
    _check_path_components(env_path)
    try:
        metadata = env_path.lstat()
    except OSError as exc:
        raise ServiceError("environment file is unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise ServiceError("environment file must be a non-symlink regular file")
    if stat.S_IMODE(metadata.st_mode) != 0o600:
        raise ServiceError("environment file permissions must be exactly 0600")
    if metadata.st_uid != os.geteuid():
        raise ServiceError("environment file must be owned by the service user")
    content = _secure_read_file(
        env_path, maximum_bytes=ENV_FILE_MAX_BYTES, purpose="environment file"
    )
    # Recheck security on the same pathname after the bounded read.
    after = env_path.lstat()
    if (
        (after.st_dev, after.st_ino) != (metadata.st_dev, metadata.st_ino)
        or stat.S_IMODE(after.st_mode) != 0o600
        or after.st_uid != os.geteuid()
    ):
        raise ServiceError("environment file security changed while reading")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ServiceError("environment file must be UTF-8") from exc

    loaded: dict[str, str] = {}
    for line_number, original in enumerate(text.splitlines(), start=1):
        line = original.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ServiceError(f"invalid environment assignment on line {line_number}")
        name, raw_value = line.split("=", 1)
        name = name.strip()
        if not _ENV_NAME.fullmatch(name):
            raise ServiceError(f"invalid environment name on line {line_number}")
        if name in loaded:
            raise ServiceError(f"duplicate environment name on line {line_number}")
        if (
            name in _DANGEROUS_ENVIRONMENT
            or name in _BASELINE_ENVIRONMENT
            or name.startswith("PYTHON")
            or name.startswith("DYLD_")
            or name.startswith("GIT_")
        ):
            raise ServiceError(f"unsafe process-control environment on line {line_number}")
        loaded[name] = _decode_env_value(raw_value.strip(), line_number)
    return loaded


def sanitized_environment(values: Mapping[str, str]) -> dict[str, str]:
    """Construct the entire child environment from fixed defaults plus the env file."""

    try:
        home = pwd.getpwuid(os.geteuid()).pw_dir
    except (KeyError, OSError) as exc:
        raise ServiceError("service user home could not be resolved") from exc
    baseline = {
        "PATH": os.defpath,
        "HOME": home,
        "LANG": "C",
        "TMPDIR": "/private/tmp" if Path("/private/tmp").is_dir() else "/tmp",
    }
    for name, value in values.items():
        if not _ENV_NAME.fullmatch(name):
            raise ServiceError("environment contains an invalid name")
        if (
            name in _DANGEROUS_ENVIRONMENT
            or name in _BASELINE_ENVIRONMENT
            or name.startswith("PYTHON")
            or name.startswith("DYLD_")
            or name.startswith("GIT_")
        ):
            raise ServiceError("environment contains unsafe process controls")
        if "\x00" in value:
            raise ServiceError("environment contains an invalid value")
        baseline[name] = value
    return baseline


@contextmanager
def _isolated_environment(values: Mapping[str, str]) -> Iterator[None]:
    previous = dict(os.environ)
    os.environ.clear()
    os.environ.update(values)
    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(previous)


@dataclass(frozen=True)
class ProcessResult:
    exit_code: int
    digest: str
    stdout: bytes
    stderr: bytes
    timed_out: bool = False
    output_overflow: bool = False
    interrupted: bool = False

    @property
    def ok(self) -> bool:
        return (
            self.exit_code == 0
            and not self.timed_out
            and not self.output_overflow
            and not self.interrupted
        )


class _BoundedOutput:
    def __init__(self, maximum_bytes: int) -> None:
        self.maximum_bytes = maximum_bytes
        self.total = 0
        self.lock = threading.Lock()
        self.overflow = threading.Event()
        self.buffers = {"stdout": bytearray(), "stderr": bytearray()}
        self.hashes = {"stdout": hashlib.sha256(), "stderr": hashlib.sha256()}

    def consume(self, name: str, pipe) -> None:
        try:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    return
                self.hashes[name].update(chunk)
                with self.lock:
                    remaining = max(0, self.maximum_bytes - self.total)
                    self.buffers[name].extend(chunk[:remaining])
                    self.total += len(chunk)
                    if self.total > self.maximum_bytes:
                        self.overflow.set()
        finally:
            pipe.close()


class BoundedProcessRunner:
    """Run a fresh session and hard-stop its whole process group on a bound."""

    def __init__(
        self,
        *,
        timeout_seconds: float,
        term_grace_seconds: float,
        max_output_bytes: int,
        poll_seconds: float = 0.02,
    ) -> None:
        for value, name in (
            (timeout_seconds, "timeout seconds"),
            (term_grace_seconds, "TERM grace seconds"),
            (poll_seconds, "poll seconds"),
        ):
            if not math.isfinite(value) or value <= 0:
                raise ServiceError(f"{name} must be positive and finite")
        if isinstance(max_output_bytes, bool) or max_output_bytes <= 0:
            raise ServiceError("maximum output bytes must be positive")
        self.timeout_seconds = timeout_seconds
        self.term_grace_seconds = term_grace_seconds
        self.max_output_bytes = max_output_bytes
        self.poll_seconds = poll_seconds

    @staticmethod
    def _group_exists(pgid: int) -> bool:
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # Darwin reports EPERM for a session whose only remaining member is
            # an exited leader.  This service created the group under its own
            # UID, so EPERM cannot identify a signalable live descendant.
            return False
        return True

    def _terminate_group(
        self, process: subprocess.Popen[bytes], *, verified_pgid: int
    ) -> None:
        # The PGID is captured from start_new_session before the leader is ever
        # reaped.  Never derive it from a health file or another mutable source.
        if verified_pgid != process.pid:
            raise ServiceError("child process-group identity is unsafe")
        if not self._group_exists(verified_pgid):
            try:
                process.wait(timeout=0)
            except subprocess.TimeoutExpired:
                pass
            return
        try:
            if os.getpgid(process.pid) != verified_pgid:
                raise ServiceError("child process-group identity is unsafe")
        except ProcessLookupError:
            # An exited-but-unreaped leader still pins its PGID.  The
            # start_new_session contract is the authority in that case.
            pass
        try:
            os.killpg(verified_pgid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        deadline = time.monotonic() + self.term_grace_seconds
        while self._group_exists(verified_pgid) and time.monotonic() < deadline:
            time.sleep(min(self.poll_seconds, max(0.0, deadline - time.monotonic())))
        if self._group_exists(verified_pgid):
            try:
                os.killpg(verified_pgid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            process.wait(timeout=max(1.0, self.term_grace_seconds))
        except subprocess.TimeoutExpired as exc:
            raise ServiceError("child process group survived SIGKILL") from exc

    def run(
        self,
        argv: Sequence[str],
        *,
        environment: Mapping[str, str],
        cwd: Path,
        stop_event: threading.Event | None = None,
        progress_callback: Callable[[], None] | None = None,
        progress_interval_seconds: float = 30.0,
        pass_fds: Sequence[int] = (),
    ) -> ProcessResult:
        if not argv or any(not isinstance(item, str) or "\x00" in item for item in argv):
            raise ServiceError("child argument vector is invalid")
        if (
            not math.isfinite(progress_interval_seconds)
            or progress_interval_seconds <= 0
        ):
            raise ServiceError("progress interval must be positive and finite")
        if any(isinstance(fd, bool) or not isinstance(fd, int) or fd < 0 for fd in pass_fds):
            raise ServiceError("inherited descriptor list is invalid")
        _check_path_components(cwd)
        try:
            process = subprocess.Popen(
                list(argv),
                cwd=cwd,
                env=dict(environment),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,
                pass_fds=tuple(pass_fds),
            )
        except OSError as exc:
            raise ServiceError("child process could not be started") from exc
        assert process.stdout is not None and process.stderr is not None
        verified_pgid = process.pid
        try:
            observed_pgid = os.getpgid(process.pid)
        except ProcessLookupError:
            observed_pgid = verified_pgid
        if observed_pgid != verified_pgid:
            try:
                process.kill()
            finally:
                process.wait()
            raise ServiceError("child process-group identity is unsafe")
        output = _BoundedOutput(self.max_output_bytes)
        readers = [
            threading.Thread(
                target=output.consume,
                args=(name, pipe),
                name=f"alice-{name}-drain",
                daemon=True,
            )
            for name, pipe in (("stdout", process.stdout), ("stderr", process.stderr))
        ]
        for reader in readers:
            reader.start()
        deadline = time.monotonic() + self.timeout_seconds
        next_progress = time.monotonic() + progress_interval_seconds
        timed_out = False
        interrupted = False
        exit_code: int | None = None
        try:
            while exit_code is None:
                if output.overflow.is_set():
                    self._terminate_group(process, verified_pgid=verified_pgid)
                    break
                if stop_event is not None and stop_event.is_set():
                    interrupted = True
                    self._terminate_group(process, verified_pgid=verified_pgid)
                    break
                if time.monotonic() >= deadline:
                    timed_out = True
                    self._terminate_group(process, verified_pgid=verified_pgid)
                    break
                if progress_callback is not None and time.monotonic() >= next_progress:
                    try:
                        progress_callback()
                    except Exception:
                        self._terminate_group(process, verified_pgid=verified_pgid)
                        raise
                    next_progress = time.monotonic() + progress_interval_seconds
                # Do not reap the session leader while a descendant still holds
                # either output pipe.  Its unreaped PID pins the PGID until a
                # timeout can safely clean the entire group.
                if all(not reader.is_alive() for reader in readers):
                    try:
                        exit_code = process.wait(timeout=self.poll_seconds)
                    except subprocess.TimeoutExpired:
                        pass
                time.sleep(self.poll_seconds)
            if exit_code is None:
                try:
                    exit_code = process.wait(
                        timeout=max(1.0, self.term_grace_seconds)
                    )
                except subprocess.TimeoutExpired as exc:
                    # The Popen handle still pins this exact unreaped PID.  Kill
                    # the leader as a last-resort cleanup and fail closed.
                    process.kill()
                    process.wait(timeout=max(1.0, self.term_grace_seconds))
                    raise ServiceError("child leader survived its process-group bound") from exc
        finally:
            for reader in readers:
                reader.join(timeout=max(1.0, self.term_grace_seconds))
        if any(reader.is_alive() for reader in readers):
            raise ServiceError("child output drain did not terminate")
        stdout = bytes(output.buffers["stdout"])
        stderr = bytes(output.buffers["stderr"])
        digest_payload = json.dumps(
            {
                "exit_code": exit_code,
                "stdout_sha256": output.hashes["stdout"].hexdigest(),
                "stderr_sha256": output.hashes["stderr"].hexdigest(),
                "timed_out": timed_out,
                "output_overflow": output.overflow.is_set(),
                "interrupted": interrupted,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return ProcessResult(
            exit_code=exit_code,
            digest=message_hash(digest_payload),
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            output_overflow=output.overflow.is_set(),
            interrupted=interrupted,
        )


def _control_runner(timeout_seconds: float = 15.0) -> BoundedProcessRunner:
    return BoundedProcessRunner(
        timeout_seconds=timeout_seconds,
        term_grace_seconds=2.0,
        max_output_bytes=CONTROL_OUTPUT_MAX_BYTES,
    )


def _git_output(
    source_root: Path,
    arguments: Sequence[str],
    *,
    environment: Mapping[str, str],
) -> bytes:
    # Source verification never needs Alice credentials.  Do not expose them
    # to repository config, fsmonitor helpers, or any other git subprocess.
    del environment
    try:
        trusted_home = pwd.getpwuid(os.geteuid()).pw_dir
    except (KeyError, OSError) as exc:
        raise ServiceError("service user home could not be resolved") from exc
    control_environment = {
        "PATH": os.defpath,
        "HOME": trusted_home,
        "LANG": "C",
        "LC_ALL": "C",
        "TMPDIR": "/private/tmp" if Path("/private/tmp").is_dir() else "/tmp",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    git = "/usr/bin/git" if os.access("/usr/bin/git", os.X_OK) else shutil.which(
        "git", path=os.defpath
    )
    if not git:
        raise ServiceError("git is required to verify Alice source identity")
    result = _control_runner().run(
        [
            git,
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-C",
            str(source_root),
            *arguments,
        ],
        environment=control_environment,
        cwd=source_root,
    )
    if not result.ok:
        raise ServiceError("Alice source identity command failed")
    return result.stdout


@dataclass(frozen=True)
class SourceEntry:
    relative_name: str
    content: bytes
    executable: bool


@dataclass(frozen=True)
class SourceCapture:
    entries: tuple[SourceEntry, ...]
    sha256: str


def _capture_source_tree(
    source_root: Path, environment: Mapping[str, str]
) -> SourceCapture:
    """Capture exact tracked bytes while the Alice subtree is demonstrably clean."""

    source_root = _require_absolute(source_root, "Alice source root")
    _check_path_components(source_root)
    if not source_root.is_dir():
        raise ServiceError("Alice source root must be a directory")
    repository_text = _git_output(
        source_root, ["rev-parse", "--show-toplevel"], environment=environment
    )
    try:
        repository_root = Path(repository_text.decode("utf-8").strip())
    except UnicodeDecodeError as exc:
        raise ServiceError("git returned an invalid repository path") from exc
    _check_path_components(repository_root)
    try:
        relative_root = source_root.relative_to(repository_root)
    except ValueError as exc:
        raise ServiceError("Alice source root is outside its repository") from exc
    pathspec = str(relative_root) if str(relative_root) != "." else "."

    def status() -> bytes:
        return _git_output(
            repository_root,
            ["status", "--porcelain=v1", "--untracked-files=all", "--", pathspec],
            environment=environment,
        )

    if status():
        raise ServiceError("Alice source tree is not clean")
    listing = _git_output(
        repository_root,
        ["ls-files", "--full-name", "-z", "--", pathspec],
        environment=environment,
    )
    names = [item for item in listing.split(b"\0") if item]
    if not names:
        raise ServiceError("Alice source tree contains no tracked files")
    entries: list[SourceEntry] = []
    total = 0
    for encoded_name in sorted(names):
        try:
            name = encoded_name.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ServiceError("Alice source path is not UTF-8") from exc
        candidate = repository_root / name
        try:
            relative = candidate.relative_to(source_root)
        except ValueError as exc:
            raise ServiceError("git returned a path outside Alice source") from exc
        if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
            raise ServiceError("git returned an unsafe Alice source path")
        content = _secure_read_file(
            candidate,
            maximum_bytes=SOURCE_FILE_MAX_BYTES,
            purpose="Alice source file",
        )
        total += len(content)
        if total > SOURCE_TREE_MAX_BYTES:
            raise ServiceError("Alice source tree exceeds its verification bound")
        mode = stat.S_IMODE(candidate.lstat().st_mode) & 0o111
        entries.append(SourceEntry(relative.as_posix(), content, bool(mode)))
    if status():
        raise ServiceError("Alice source tree changed during verification")
    return SourceCapture(tuple(entries), _source_capture_sha256(entries))


def _source_capture_sha256(entries: Sequence[SourceEntry]) -> str:
    digest = hashlib.sha256()
    previous = ""
    for entry in entries:
        if entry.relative_name <= previous:
            raise ServiceError("Alice source manifest is not strictly ordered")
        previous = entry.relative_name
        encoded_name = entry.relative_name.encode("utf-8")
        digest.update(len(encoded_name).to_bytes(8, "big"))
        digest.update(encoded_name)
        digest.update((1 if entry.executable else 0).to_bytes(1, "big"))
        digest.update(len(entry.content).to_bytes(8, "big"))
        digest.update(entry.content)
    return digest.hexdigest()


def source_tree_sha256(source_root: Path, environment: Mapping[str, str]) -> str:
    """Hash every tracked Alice file and reject any tracked/untracked change."""

    return _capture_source_tree(source_root, environment).sha256


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ServiceError("resolved configuration is not canonical finite JSON") from exc


def _canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class RuntimeIdentity:
    source_tree_sha256: str
    config_sha256: str
    policy_hash: str
    effect_mode: str

    def __post_init__(self) -> None:
        _require_sha256(self.source_tree_sha256, "source tree SHA256")
        _require_sha256(self.config_sha256, "config SHA256")
        _require_sha256(self.policy_hash, "policy hash")
        if self.effect_mode not in _EFFECT_MODES:
            raise ServiceError("effect mode is invalid")

    def to_dict(self) -> dict[str, str]:
        return {
            "source_tree_sha256": self.source_tree_sha256,
            "config_sha256": self.config_sha256,
            "policy_hash": self.policy_hash,
            "effect_mode": self.effect_mode,
        }


def _resolve_runtime_inputs(
    *,
    config: Path,
    root: Path,
    source_root: Path,
    environment: Mapping[str, str],
) -> tuple[RuntimeIdentity, dict[str, object], SourceCapture]:
    """Resolve config only under the sanitized environment and bind its source."""

    config = _require_absolute(config, "config path")
    root = _require_absolute(root, "runtime root")
    source_root = _require_absolute(source_root, "Alice source root")
    _check_path_components(config)
    _check_path_components(root, allow_missing_leaf=True, allow_missing_parents=True)
    _check_path_components(source_root)
    config_bytes = _secure_read_file(
        config, maximum_bytes=CONFIG_FILE_MAX_BYTES, purpose="config file"
    )
    descriptor, snapshot_name = tempfile.mkstemp(prefix="alice-config-", suffix=".json")
    snapshot = Path(snapshot_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(config_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        with _isolated_environment(environment):
            loaded = load_config(snapshot)
            resolved = resolve_runtime_paths(loaded, root)
            policy_hash = release_policy_from_config(resolved).policy_hash
        config_sha = _canonical_json_sha256(resolved)
        effect_mode = resolved["runtime"]["effect_mode"]
        if effect_mode not in _EFFECT_MODES:
            raise ServiceError("resolved effect mode is invalid")
        before_source = _capture_source_tree(source_root, environment)
        if _secure_read_file(
            config, maximum_bytes=CONFIG_FILE_MAX_BYTES, purpose="config file"
        ) != config_bytes:
            raise ServiceError("config file changed during resolution")
        after_source = source_tree_sha256(source_root, environment)
        if before_source.sha256 != after_source:
            raise ServiceError("Alice source tree changed during config resolution")
        identity = RuntimeIdentity(
            source_tree_sha256=before_source.sha256,
            config_sha256=config_sha,
            policy_hash=policy_hash,
            effect_mode=effect_mode,
        )
        return identity, resolved, before_source
    except (json.JSONDecodeError, ValueError, TypeError, KeyError) as exc:
        raise ServiceError("configuration could not be resolved safely") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            snapshot.unlink()
        except FileNotFoundError:
            pass


def resolve_runtime_identity(
    *,
    config: Path,
    root: Path,
    source_root: Path,
    environment: Mapping[str, str],
) -> RuntimeIdentity:
    """Resolve config only under the sanitized environment and bind its source."""

    identity, _resolved, _capture = _resolve_runtime_inputs(
        config=config,
        root=root,
        source_root=source_root,
        environment=environment,
    )
    return identity


@dataclass(frozen=True)
class ExecutionSnapshot:
    root: Path
    resolved_config: Path

    @property
    def source_path(self) -> Path:
        return self.root / "src"


def _release_manifest(
    capture: SourceCapture, identity: RuntimeIdentity
) -> dict[str, object]:
    return {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "identity": identity.to_dict(),
        "files": [
            {
                "path": entry.relative_name,
                "executable": entry.executable,
                "size": len(entry.content),
                "sha256": hashlib.sha256(entry.content).hexdigest(),
            }
            for entry in capture.entries
        ],
    }


def _release_path(root: Path, identity: RuntimeIdentity) -> Path:
    return (
        root
        / "var"
        / "service"
        / "releases"
        / identity.source_tree_sha256
        / identity.config_sha256
    )


def materialize_execution_snapshot(
    *,
    config: Path,
    root: Path,
    source_root: Path,
    environment: Mapping[str, str],
    expected_identity: RuntimeIdentity | None = None,
) -> tuple[ExecutionSnapshot, RuntimeIdentity]:
    """Atomically seal the exact source/config bytes that a child will execute."""

    try:
        root.relative_to(source_root)
    except ValueError:
        pass
    else:
        raise ServiceError("service runtime root must be outside the Alice source tree")
    identity, resolved, capture = _resolve_runtime_inputs(
        config=config,
        root=root,
        source_root=source_root,
        environment=environment,
    )
    if expected_identity is not None and identity != expected_identity:
        raise IdentityMismatch("installation identity does not match runtime")
    destination = _release_path(root, identity)
    snapshot = ExecutionSnapshot(destination, destination / ".alice-resolved-config.json")
    if destination.exists():
        verify_execution_snapshot(snapshot, root=root, expected_identity=identity)
        return snapshot, identity

    releases = destination.parent
    _check_path_components(releases, allow_missing_leaf=True, allow_missing_parents=True)
    releases.mkdir(mode=0o700, parents=True, exist_ok=True)
    _check_path_components(releases)
    temporary = Path(tempfile.mkdtemp(prefix=".alice-release-", dir=releases))
    try:
        os.chmod(temporary, 0o700)
        for entry in capture.entries:
            target = temporary / entry.relative_name
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            _atomic_write(target, entry.content, 0o500 if entry.executable else 0o400)
        resolved_payload = _canonical_json_bytes(resolved)
        _atomic_write(
            temporary / ".alice-resolved-config.json", resolved_payload, 0o400
        )
        _atomic_write(
            temporary / ".alice-release.json",
            _canonical_json_bytes(_release_manifest(capture, identity)),
            0o400,
        )
        for directory, _names, _files in os.walk(temporary, topdown=False):
            os.chmod(directory, 0o500)
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.replace(temporary, destination)
        directory_fd = os.open(
            destination.parent, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        )
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    verify_execution_snapshot(snapshot, root=root, expected_identity=identity)
    # Ensure neither mutable input drifted while the sealed release was built.
    final_identity = resolve_runtime_identity(
        config=config,
        root=root,
        source_root=source_root,
        environment=environment,
    )
    if final_identity != identity:
        raise IdentityMismatch("Alice source or configuration changed during release sealing")
    return snapshot, identity


def _verify_execution_snapshot_impl(
    snapshot: ExecutionSnapshot,
    *,
    root: Path,
    expected_identity: RuntimeIdentity,
) -> None:
    """Verify a sealed release without consulting the mutable checkout."""

    _check_path_components(snapshot.root)
    metadata = snapshot.root.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o500
        or metadata.st_uid != os.geteuid()
    ):
        raise IdentityMismatch("execution release directory is not sealed")
    manifest_bytes = _secure_read_file(
        snapshot.root / ".alice-release.json",
        maximum_bytes=CONFIG_FILE_MAX_BYTES,
        purpose="execution release manifest",
    )
    for control_path in (
        snapshot.root / ".alice-release.json",
        snapshot.resolved_config,
    ):
        try:
            control_metadata = control_path.lstat()
        except OSError as exc:
            raise IdentityMismatch("execution release controls are unavailable") from exc
        if (
            stat.S_IMODE(control_metadata.st_mode) != 0o400
            or control_metadata.st_uid != os.geteuid()
        ):
            raise IdentityMismatch("execution release controls are not owner-only")
    try:
        manifest = json.loads(
            manifest_bytes.decode("utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"invalid constant {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise IdentityMismatch("execution release manifest is invalid") from exc
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"schema_version", "identity", "files"}
        or manifest.get("schema_version") != RELEASE_SCHEMA_VERSION
        or isinstance(manifest.get("schema_version"), bool)
        or manifest.get("identity") != expected_identity.to_dict()
        or not isinstance(manifest.get("files"), list)
    ):
        raise IdentityMismatch("execution release manifest does not match its pin")
    entries: list[SourceEntry] = []
    total = 0
    for record in manifest["files"]:
        if not isinstance(record, dict) or set(record) != {
            "path",
            "executable",
            "size",
            "sha256",
        }:
            raise IdentityMismatch("execution release file record is invalid")
        name = record.get("path")
        executable = record.get("executable")
        size = record.get("size")
        digest = record.get("sha256")
        if (
            not isinstance(name, str)
            or not name
            or Path(name).is_absolute()
            or any(part in {"", ".", ".."} for part in Path(name).parts)
            or not isinstance(executable, bool)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
            or not isinstance(digest, str)
            or not _SHA256.fullmatch(digest)
        ):
            raise IdentityMismatch("execution release file record is invalid")
        path = snapshot.root / name
        content = _secure_read_file(
            path, maximum_bytes=SOURCE_FILE_MAX_BYTES, purpose="execution release file"
        )
        total += len(content)
        if total > SOURCE_TREE_MAX_BYTES:
            raise IdentityMismatch("execution release exceeds its verification bound")
        file_metadata = path.lstat()
        expected_mode = 0o500 if executable else 0o400
        if (
            len(content) != size
            or hashlib.sha256(content).hexdigest() != digest
            or stat.S_IMODE(file_metadata.st_mode) != expected_mode
            or file_metadata.st_uid != os.geteuid()
        ):
            raise IdentityMismatch("execution release file does not match its manifest")
        entries.append(SourceEntry(name, content, executable))
    if _source_capture_sha256(entries) != expected_identity.source_tree_sha256:
        raise IdentityMismatch("execution release source does not match its pin")
    resolved_bytes = _secure_read_file(
        snapshot.resolved_config,
        maximum_bytes=CONFIG_FILE_MAX_BYTES,
        purpose="execution resolved configuration",
    )
    try:
        resolved = json.loads(
            resolved_bytes.decode("utf-8"),
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"invalid constant {value}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise IdentityMismatch("execution resolved configuration is invalid") from exc
    if not isinstance(resolved, dict) or not isinstance(resolved.get("runtime"), dict):
        raise IdentityMismatch("execution resolved configuration is invalid")
    if (
        _canonical_json_bytes(resolved) != resolved_bytes
        or _canonical_json_sha256(resolved) != expected_identity.config_sha256
        or release_policy_from_config(resolved).policy_hash
        != expected_identity.policy_hash
        or resolved["runtime"].get("effect_mode") != expected_identity.effect_mode
    ):
        raise IdentityMismatch("execution resolved configuration does not match its pin")


def verify_execution_snapshot(
    snapshot: ExecutionSnapshot,
    *,
    root: Path,
    expected_identity: RuntimeIdentity,
) -> None:
    try:
        _verify_execution_snapshot_impl(
            snapshot, root=root, expected_identity=expected_identity
        )
    except IdentityMismatch:
        raise
    except (ServiceError, ValueError, TypeError, KeyError, OSError) as exc:
        raise IdentityMismatch("execution release verification failed closed") from exc


def _execution_environment(environment: Mapping[str, str]) -> dict[str, str]:
    result = dict(environment)
    for name in _CONFIG_OVERRIDE_ENVIRONMENT:
        result.pop(name, None)
    for name in tuple(result):
        if name.startswith("PYTHON") or name.startswith("DYLD_") or name.startswith("GIT_"):
            result.pop(name, None)
    return result


def _isolated_module_argv(
    python: Path, snapshot: ExecutionSnapshot, module: str, arguments: Sequence[str]
) -> list[str]:
    if module not in {"alice", "alice.service"}:
        raise ServiceError("isolated execution module is not allowed")
    bootstrap = (
        "import runpy,sys;"
        "source=sys.argv.pop(1);"
        "sys.path.insert(0,source);"
        "sys.argv[0]='alice';"
        f"runpy.run_module({module!r},run_name='__main__')"
    )
    return [str(python), "-I", "-c", bootstrap, str(snapshot.source_path), *arguments]


@dataclass(frozen=True)
class HealthState:
    started_at: str
    heartbeat_at: str
    success_at: str | None
    failure_at: str | None
    tick_started_at: str | None
    consecutive_failures: int
    source_tree_sha256: str
    config_sha256: str
    policy_hash: str
    effect_mode: str
    pid: int
    message_hash: str | None
    schema_version: int = HEALTH_SCHEMA_VERSION

    @property
    def identity(self) -> RuntimeIdentity:
        return RuntimeIdentity(
            self.source_tree_sha256,
            self.config_sha256,
            self.policy_hash,
            self.effect_mode,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "started_at": self.started_at,
            "heartbeat_at": self.heartbeat_at,
            "success_at": self.success_at,
            "failure_at": self.failure_at,
            "tick_started_at": self.tick_started_at,
            "consecutive_failures": self.consecutive_failures,
            "source_tree_sha256": self.source_tree_sha256,
            "config_sha256": self.config_sha256,
            "policy_hash": self.policy_hash,
            "effect_mode": self.effect_mode,
            "pid": self.pid,
            "message_hash": self.message_hash,
        }

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "HealthState":
        if set(value) != _HEALTH_KEYS:
            raise ServiceError("health state has unexpected or missing fields")
        if value.get("schema_version") != HEALTH_SCHEMA_VERSION or isinstance(
            value.get("schema_version"), bool
        ):
            raise ServiceError("health state schema is unsupported")
        for field in ("started_at", "heartbeat_at"):
            _parse_timestamp(value.get(field), field)
        for field in ("success_at", "failure_at", "tick_started_at"):
            _parse_timestamp(value.get(field), field, optional=True)
        failures = value.get("consecutive_failures")
        pid = value.get("pid")
        digest = value.get("message_hash")
        if isinstance(failures, bool) or not isinstance(failures, int) or failures < 0:
            raise ServiceError("health consecutive failures is invalid")
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            raise ServiceError("health PID is invalid")
        if digest is not None and (
            not isinstance(digest, str) or not _SHA256.fullmatch(digest)
        ):
            raise ServiceError("health message hash is invalid")
        identity = RuntimeIdentity(
            source_tree_sha256=str(value.get("source_tree_sha256", "")),
            config_sha256=str(value.get("config_sha256", "")),
            policy_hash=str(value.get("policy_hash", "")),
            effect_mode=str(value.get("effect_mode", "")),
        )
        return cls(
            schema_version=HEALTH_SCHEMA_VERSION,
            started_at=str(value["started_at"]),
            heartbeat_at=str(value["heartbeat_at"]),
            success_at=value["success_at"] if isinstance(value["success_at"], str) else None,
            failure_at=value["failure_at"] if isinstance(value["failure_at"], str) else None,
            tick_started_at=(
                value["tick_started_at"]
                if isinstance(value["tick_started_at"], str)
                else None
            ),
            consecutive_failures=failures,
            source_tree_sha256=identity.source_tree_sha256,
            config_sha256=identity.config_sha256,
            policy_hash=identity.policy_hash,
            effect_mode=identity.effect_mode,
            pid=pid,
            message_hash=digest if isinstance(digest, str) else None,
        )


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    path = _require_absolute(path, "atomic output path")
    _check_path_components(
        path.parent, allow_missing_leaf=True, allow_missing_parents=True
    )
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    _check_path_components(path.parent)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        _check_path_components(path.parent)
        os.replace(temporary, path)
        os.chmod(path, mode, follow_symlinks=False)
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _ensure_private_directory(path: Path, purpose: str) -> None:
    _check_path_components(path, allow_missing_leaf=True, allow_missing_parents=True)
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    _check_path_components(path)
    metadata = path.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o700
        or metadata.st_uid != os.geteuid()
    ):
        raise ServiceError(f"{purpose} must be an owner-only directory")


class HealthStore:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = _require_absolute(path, "health path")

    def read(self) -> HealthState:
        content = _secure_read_file(
            self.path,
            maximum_bytes=HEALTH_FILE_MAX_BYTES,
            purpose="health state",
        )
        metadata = self.path.lstat()
        if stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_uid != os.geteuid():
            raise ServiceError("health state must be owner-only")
        try:
            value = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ServiceError("health state is unreadable") from exc
        if not isinstance(value, dict):
            raise ServiceError("health state must be a JSON object")
        return HealthState.from_mapping(value)

    def read_optional(self) -> HealthState | None:
        try:
            return self.read()
        except ServiceError:
            if not self.path.exists() and not self.path.is_symlink():
                return None
            raise

    def write(self, state: HealthState) -> None:
        normalized = HealthState.from_mapping(state.to_dict())
        payload = (
            json.dumps(
                normalized.to_dict(),
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        _ensure_private_directory(self.path.parent, "health state parent")
        _atomic_write(self.path, payload, 0o600)


class WorkerLock:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = _require_absolute(path, "worker lock path")
        self._descriptor: int | None = None

    def acquire(self) -> None:
        if self._descriptor is not None:
            raise ServiceError("worker lock is already acquired")
        _ensure_private_directory(self.path.parent, "worker lock parent")
        flags = (
            os.O_RDWR
            | os.O_CREAT
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        try:
            descriptor = os.open(self.path, flags, 0o600)
        except OSError as exc:
            raise ServiceError("worker lock could not be opened safely") from exc
        try:
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_uid != os.geteuid()
            ):
                raise ServiceError("worker lock is not owner-only")
            try:
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                if exc.errno in {errno.EACCES, errno.EAGAIN}:
                    raise WorkerAlreadyRunning("another Alice worker holds the lock") from exc
                raise ServiceError("worker lock could not be acquired") from exc
            os.ftruncate(descriptor, 0)
            os.write(descriptor, f"{os.getpid()}\n".encode("ascii"))
            os.fsync(descriptor)
            self._descriptor = descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def release(self) -> None:
        descriptor, self._descriptor = self._descriptor, None
        if descriptor is None:
            return
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)

    def __enter__(self) -> "WorkerLock":
        self.acquire()
        return self

    def __exit__(self, *_args: object) -> None:
        self.release()


@dataclass(frozen=True)
class TickResult:
    ok: bool
    exit_code: int
    digest: str
    fatal: bool = False


IdentityResolver = Callable[[], RuntimeIdentity]
TickExecutor = Callable[[threading.Event | None, Callable[[], None]], ProcessResult]


class ServiceRunner:
    def __init__(
        self,
        *,
        health_store: HealthStore,
        expected_identity: RuntimeIdentity,
        identity_resolver: IdentityResolver,
        tick_executor: TickExecutor,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self.health_store = health_store
        self.expected_identity = expected_identity
        self.identity_resolver = identity_resolver
        self.tick_executor = tick_executor
        self.clock = clock
        self.state: HealthState | None = None

    def _verify_identity(self) -> None:
        actual = self.identity_resolver()
        if actual != self.expected_identity:
            raise IdentityMismatch("Alice source or resolved configuration changed")

    def start(self) -> HealthState:
        self._verify_identity()
        previous = self.health_store.read_optional()
        if previous is not None and previous.identity != self.expected_identity:
            previous = None
        now = _timestamp(self.clock())
        identity = self.expected_identity
        self.state = HealthState(
            started_at=now,
            heartbeat_at=now,
            # A launch is not healthy merely because the previous process once
            # succeeded.  Installation waits for a success from this boot.
            success_at=None,
            failure_at=previous.failure_at if previous else None,
            tick_started_at=None,
            consecutive_failures=previous.consecutive_failures if previous else 0,
            source_tree_sha256=identity.source_tree_sha256,
            config_sha256=identity.config_sha256,
            policy_hash=identity.policy_hash,
            effect_mode=identity.effect_mode,
            pid=os.getpid(),
            message_hash=previous.message_hash if previous else None,
        )
        self.health_store.write(self.state)
        return self.state

    def _record_failure(self, digest: str) -> None:
        if self.state is None:
            now = _timestamp(self.clock())
            identity = self.expected_identity
            self.state = HealthState(
                started_at=now,
                heartbeat_at=now,
                success_at=None,
                failure_at=now,
                tick_started_at=None,
                consecutive_failures=1,
                source_tree_sha256=identity.source_tree_sha256,
                config_sha256=identity.config_sha256,
                policy_hash=identity.policy_hash,
                effect_mode=identity.effect_mode,
                pid=os.getpid(),
                message_hash=digest,
            )
        else:
            now = _timestamp(self.clock())
            self.state = replace(
                self.state,
                heartbeat_at=now,
                failure_at=now,
                tick_started_at=None,
                consecutive_failures=self.state.consecutive_failures + 1,
                message_hash=digest,
                pid=os.getpid(),
            )
        self.health_store.write(self.state)

    def run_tick(self, stop_event: threading.Event | None = None) -> TickResult:
        if self.state is None:
            self.start()
        assert self.state is not None
        started = _timestamp(self.clock())
        self.state = replace(
            self.state,
            heartbeat_at=started,
            tick_started_at=started,
            pid=os.getpid(),
        )
        self.health_store.write(self.state)

        def progress() -> None:
            assert self.state is not None
            self.state = replace(
                self.state,
                heartbeat_at=_timestamp(self.clock()),
                pid=os.getpid(),
            )
            self.health_store.write(self.state)

        try:
            self._verify_identity()
            process = self.tick_executor(stop_event, progress)
            self._verify_identity()
        except IdentityMismatch as exc:
            digest = message_hash(f"identity:{type(exc).__name__}")
            self._record_failure(digest)
            return TickResult(False, EX_CONFIG, digest, fatal=True)
        except ServiceError as exc:
            digest = message_hash(f"service:{type(exc).__name__}")
            self._record_failure(digest)
            return TickResult(False, 1, digest)
        except Exception as exc:
            digest = message_hash(f"unexpected:{type(exc).__name__}")
            self._record_failure(digest)
            return TickResult(False, 1, digest)
        finished = _timestamp(self.clock())
        if process.ok:
            self.state = replace(
                self.state,
                heartbeat_at=finished,
                success_at=finished,
                tick_started_at=None,
                consecutive_failures=0,
                message_hash=process.digest,
            )
        else:
            self.state = replace(
                self.state,
                heartbeat_at=finished,
                failure_at=finished,
                tick_started_at=None,
                consecutive_failures=self.state.consecutive_failures + 1,
                message_hash=process.digest,
            )
        self.health_store.write(self.state)
        return TickResult(process.ok, process.exit_code, process.digest)

    def heartbeat(self) -> None:
        if self.state is None:
            return
        self.state = replace(
            self.state,
            heartbeat_at=_timestamp(self.clock()),
            tick_started_at=None,
        )
        self.health_store.write(self.state)


@dataclass(frozen=True)
class ProbeResult:
    ok: bool
    problems: tuple[str, ...]
    state: HealthState | None

    def safe_summary(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "problems": list(self.problems),
            "pid": self.state.pid if self.state else None,
            "consecutive_failures": (
                self.state.consecutive_failures if self.state else None
            ),
            "message_hash": self.state.message_hash if self.state else None,
            "source_tree_sha256": (
                self.state.source_tree_sha256 if self.state else None
            ),
            "config_sha256": self.state.config_sha256 if self.state else None,
            "policy_hash": self.state.policy_hash if self.state else None,
            "effect_mode": self.state.effect_mode if self.state else None,
        }


def probe_health(
    health_store: HealthStore,
    *,
    stale_seconds: float,
    max_consecutive_failures: int,
    max_tick_seconds: float,
    expected_identity: RuntimeIdentity | None = None,
    now: datetime | None = None,
) -> ProbeResult:
    for value in (stale_seconds, max_tick_seconds):
        if not math.isfinite(value) or value <= 0:
            raise ServiceError("probe time limits must be positive and finite")
    if isinstance(max_consecutive_failures, bool) or max_consecutive_failures <= 0:
        raise ServiceError("maximum consecutive failures must be positive")
    try:
        state = health_store.read()
    except ServiceError:
        return ProbeResult(False, ("health_unavailable",), None)
    observed = (now or _utc_now()).astimezone(timezone.utc)
    heartbeat = _parse_timestamp(state.heartbeat_at, "heartbeat_at")
    assert heartbeat is not None
    problems: list[str] = []
    heartbeat_age = (observed - heartbeat).total_seconds()
    heartbeat_is_fresh = -5 <= heartbeat_age <= stale_seconds
    if heartbeat_age < -5:
        problems.append("heartbeat_from_future")
    elif heartbeat_age > stale_seconds:
        problems.append("stale_heartbeat")
    tick_started = _parse_timestamp(state.tick_started_at, "tick_started_at", optional=True)
    bounded_active_tick = False
    if tick_started is not None:
        tick_age = (observed - tick_started).total_seconds()
        if tick_age < -5:
            problems.append("tick_started_from_future")
        elif tick_age > max_tick_seconds:
            problems.append("overlong_tick")
        elif heartbeat_is_fresh:
            bounded_active_tick = True
    if (
        state.consecutive_failures >= max_consecutive_failures
        and not bounded_active_tick
    ):
        problems.append("repeated_failures")
    if expected_identity is not None and state.identity != expected_identity:
        problems.append("identity_mismatch")
    try:
        os.kill(state.pid, 0)
    except ProcessLookupError:
        problems.append("worker_process_missing")
    except PermissionError:
        problems.append("worker_process_unverifiable")
    return ProbeResult(not problems, tuple(problems), state)


def watchdog_receipt_ok(
    path: Path,
    *,
    expected_identity: RuntimeIdentity,
    not_before_epoch: float | None = None,
    maximum_age_seconds: float | None = None,
    now: datetime | None = None,
) -> bool:
    try:
        content = _secure_read_file(
            path,
            maximum_bytes=HEALTH_FILE_MAX_BYTES,
            purpose="watchdog receipt",
        )
        metadata = path.lstat()
        if stat.S_IMODE(metadata.st_mode) != 0o600 or metadata.st_uid != os.geteuid():
            return False
        value = json.loads(content.decode("utf-8"))
        if not isinstance(value, dict) or set(value) != _WATCHDOG_RECEIPT_KEYS:
            return False
        if (
            value.get("schema_version") != 1
            or isinstance(value.get("schema_version"), bool)
            or value.get("healthy") is not True
        ):
            return False
        if value.get("action") != "none":
            return False
        if any(value.get(key) != expected for key, expected in expected_identity.to_dict().items()):
            return False
        digest = value.get("message_hash")
        if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
            return False
        checked = _parse_timestamp(value.get("checked_at"), "checked_at")
        assert checked is not None
        if not_before_epoch is not None and checked.timestamp() < not_before_epoch:
            return False
        if maximum_age_seconds is not None:
            if not math.isfinite(maximum_age_seconds) or maximum_age_seconds <= 0:
                raise ServiceError("watchdog receipt age must be positive and finite")
            age = ((now or _utc_now()).astimezone(timezone.utc) - checked).total_seconds()
            if age < -5 or age > maximum_age_seconds:
                return False
        return True
    except (OSError, ServiceError, UnicodeDecodeError, json.JSONDecodeError):
        return False


def post_start_health_ok(
    result: ProbeResult,
    *,
    expected_identity: RuntimeIdentity,
    watchdog_state: Path,
    started_after_epoch: float,
    maximum_age_seconds: float,
    now: datetime | None = None,
) -> bool:
    """Prove this boot is live without waiting for a potentially long first tick."""
    if not math.isfinite(started_after_epoch):
        raise ServiceError("started-after epoch must be finite")
    if not result.ok or result.state is None:
        return False
    started = _parse_timestamp(result.state.started_at, "started_at")
    assert started is not None
    if started.timestamp() < started_after_epoch:
        return False
    success = _parse_timestamp(result.state.success_at, "success_at", optional=True)
    completed_this_boot = success is not None and success >= started
    tick_started = _parse_timestamp(
        result.state.tick_started_at, "tick_started_at", optional=True
    )
    active_this_boot = tick_started is not None and tick_started >= started
    if not (completed_this_boot or active_this_boot):
        return False
    return watchdog_receipt_ok(
        watchdog_state,
        expected_identity=expected_identity,
        not_before_epoch=started_after_epoch,
        maximum_age_seconds=maximum_age_seconds,
        now=now,
    )


def _render_template(path: Path, replacements: Mapping[str, str]) -> str:
    content = _secure_read_file(
        path, maximum_bytes=1024 * 1024, purpose="launchd template"
    )
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ServiceError("launchd template must be UTF-8") from exc
    for name, value in replacements.items():
        text = text.replace(f"__{name}__", xml_escape(value, quote=True))
    if re.findall(r"__[A-Z0-9_]+__", text):
        raise ServiceError("launchd template has unresolved placeholders")
    return text


def render_plists(
    *,
    worker_template: Path,
    watchdog_template: Path,
    worker_output: Path,
    watchdog_output: Path,
    python: Path,
    watchdog_script: Path,
    watchdog_python: Path,
    config: Path,
    env_file: Path,
    root: Path,
    state: Path,
    lock: Path,
    rate_state: Path,
    watchdog_state: Path,
    source_root: Path,
    identity: RuntimeIdentity,
    poll_seconds: float,
    stale_seconds: float,
    max_tick_seconds: float,
    term_grace_seconds: float,
    max_consecutive_failures: int,
    watchdog_interval: int,
    alert_interval_seconds: float,
    startup_grace_seconds: float,
    launchd_target: str,
) -> None:
    common = {
        "PYTHON": str(python),
        "STATE": str(state),
        "SOURCE_ROOT": str(source_root),
        "SOURCE_TREE_SHA256": identity.source_tree_sha256,
        "CONFIG_SHA256": identity.config_sha256,
        "POLICY_HASH": identity.policy_hash,
        "EFFECT_MODE": identity.effect_mode,
        "MAX_TICK_SECONDS": str(max_tick_seconds),
    }
    release_root = _release_path(root, identity)
    worker = _render_template(
        worker_template,
        {
            **common,
            "CONFIG": str(config),
            "ENV_FILE": str(env_file),
            "ROOT": str(root),
            "LOCK": str(lock),
            "POLL_SECONDS": str(poll_seconds),
            "HEARTBEAT_SECONDS": str(min(60.0, stale_seconds / 3.0)),
            "TERM_GRACE_SECONDS": str(term_grace_seconds),
            "ISOLATED_SERVICE_BOOTSTRAP": _ISOLATED_SERVICE_BOOTSTRAP,
            "RELEASE_SOURCE": str(release_root / "src"),
            "WORKING_DIRECTORY": str(release_root),
        },
    )
    watchdog = _render_template(
        watchdog_template,
        {
            **common,
            "WATCHDOG_SCRIPT": str(watchdog_script),
            "WATCHDOG_PYTHON": str(watchdog_python),
            "ENV_FILE": str(env_file),
            "RATE_STATE": str(rate_state),
            "WATCHDOG_STATE": str(watchdog_state),
            "STALE_SECONDS": str(stale_seconds),
            "MAX_CONSECUTIVE_FAILURES": str(max_consecutive_failures),
            "WATCHDOG_INTERVAL": str(watchdog_interval),
            "ALERT_INTERVAL_SECONDS": str(alert_interval_seconds),
            "STARTUP_GRACE_SECONDS": str(startup_grace_seconds),
            "LAUNCHD_TARGET": launchd_target,
            "WORKING_DIRECTORY": str(root),
        },
    )
    _atomic_write(worker_output, worker.encode("utf-8"), 0o644)
    _atomic_write(watchdog_output, watchdog.encode("utf-8"), 0o644)


def _positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if not math.isfinite(parsed) or parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive and finite")
    return parsed


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def configured_tick_timeout_floor(config: Mapping[str, object]) -> float:
    """Return a safe supervisor deadline for one configured Alice task.

    The worker wraps each ``alice tick --count 1`` in a second process.  That
    outer deadline must be longer than every inner, deliberately bounded
    operation.  In particular one text2game CAD task can run all three phases
    sequentially, so a fixed 30-minute service deadline would cancel healthy
    six-hour work and turn a recoverable phase into an ambiguous effect.

    ``load_config`` validates the shape before this helper is called.  The
    defensive conversions below still fail closed when the helper is reused
    directly by tests or deployment tooling.
    """

    try:
        agents = config["agents"]
        adapters = config["adapters"]
        if not isinstance(agents, Mapping) or not isinstance(adapters, Mapping):
            raise TypeError

        # Leave five minutes for durable bookkeeping, validation and orderly
        # process-group shutdown beyond the longest model/provider call.
        candidates = [1_800.0, float(agents["timeout_seconds"]) + 300.0]
        codex = agents.get("codex")
        if isinstance(codex, Mapping):
            candidates.append(
                float(codex["timeout_seconds"])
                + float(codex["startup_timeout_seconds"])
                + float(codex["shutdown_grace_seconds"])
                + 300.0
            )

        command_keys = (
            "library_command",
            "history_command",
            "research_command",
            "rules_validator_command",
            "digital_playtest_command",
            "human_playtest_command",
            "cad_command",
            "market_validation_command",
            "outcomes_command",
            "factory_order_command",
            "print_fulfillment_command",
        )
        if any(adapters.get(key) for key in command_keys):
            candidates.append(GENERIC_COMMAND_ADAPTER_TIMEOUT_SECONDS + 300.0)

        text2game = adapters.get("text2game")
        if isinstance(text2game, Mapping) and text2game.get("enabled") is True:
            phase_timeout = float(text2game["timeout_seconds"])
            shutdown = float(text2game["shutdown_grace_seconds"])
            # physical.cad runs phase 1, 2 and 3 in one adapter invocation.
            candidates.append((3.0 * phase_timeout) + (3.0 * shutdown) + 600.0)

        page_builder = adapters.get("page_builder")
        if isinstance(page_builder, Mapping) and page_builder.get("enabled") is True:
            operator_timeout = float(page_builder["timeout_seconds"])
            readback_timeout = float(page_builder["readback_timeout_seconds"])
            # The rich-draft operator is followed by authenticated design and
            # immutable-project readback.  Allow up to 100 bounded CDN reads,
            # with a four-hour minimum readback window for large projects.
            candidates.append(
                operator_timeout + max(14_400.0, 100.0 * readback_timeout)
            )

        vibe = adapters.get("vibe")
        if isinstance(vibe, Mapping) and vibe.get("enabled") is True:
            poll_wait = (
                int(vibe["max_job_polls"]) + int(vibe["max_page_polls"])
            ) * float(vibe["poll_interval_seconds"])
            # Most requests return quickly; six full request deadlines cover
            # create/publish plus both authenticated and anonymous readbacks.
            candidates.append(
                poll_wait + (6.0 * float(vibe["timeout_seconds"])) + 600.0
            )
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise ServiceError("configured task deadlines are invalid") from exc

    floor = max(candidates)
    if not math.isfinite(floor) or floor <= 0:
        raise ServiceError("configured task deadline is invalid")
    return float(math.ceil(floor))


def effective_max_tick_seconds(
    requested: float | None, config: Mapping[str, object]
) -> float:
    """Resolve an optional operator override without undercutting task bounds."""

    floor = configured_tick_timeout_floor(config)
    if requested is None:
        return floor
    value = float(requested)
    if not math.isfinite(value) or value < floor:
        raise ServiceError(
            "max-tick-seconds is shorter than the configured task deadline floor"
        )
    return value


def _identity_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--expected-source-tree-sha256", required=True)
    parser.add_argument("--expected-config-sha256", required=True)
    parser.add_argument("--expected-policy-hash", required=True)
    parser.add_argument(
        "--expected-effect-mode", choices=tuple(sorted(_EFFECT_MODES)), required=True
    )


def _expected_identity(args: argparse.Namespace) -> RuntimeIdentity:
    return RuntimeIdentity(
        source_tree_sha256=args.expected_source_tree_sha256.lower(),
        config_sha256=args.expected_config_sha256.lower(),
        policy_hash=args.expected_policy_hash.lower(),
        effect_mode=args.expected_effect_mode,
    )


def _runtime_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", required=True)
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--source-root", required=True)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m alice.service")
    subparsers = parser.add_subparsers(dest="command", required=True)

    identity = subparsers.add_parser("identity")
    _runtime_arguments(identity)

    preflight = subparsers.add_parser("preflight")
    _runtime_arguments(preflight)
    preflight.add_argument("--allow-dry-run", action="store_true")
    preflight.add_argument("--doctor-timeout-seconds", type=_positive_float, default=300.0)

    run = subparsers.add_parser("run")
    _runtime_arguments(run)
    _identity_arguments(run)
    run.add_argument("--state", required=True)
    run.add_argument("--lock", required=True)
    run.add_argument("--poll-seconds", type=_positive_float, default=30.0)
    run.add_argument("--max-tick-seconds", type=_positive_float)
    run.add_argument("--term-grace-seconds", type=_positive_float, default=10.0)
    run.add_argument("--heartbeat-seconds", type=_positive_float, default=60.0)
    run.add_argument("--max-output-bytes", type=_positive_int, default=CHILD_OUTPUT_MAX_BYTES)
    run.add_argument("--once", action="store_true")

    guard = subparsers.add_parser("guard-tick")
    guard.add_argument("--release-root", required=True)
    guard.add_argument("--resolved-config", required=True)
    guard.add_argument("--root", required=True)
    guard.add_argument("--control-fd", type=int, required=True)
    _identity_arguments(guard)
    guard.add_argument("--max-tick-seconds", type=_positive_float, default=1800.0)
    guard.add_argument("--term-grace-seconds", type=_positive_float, default=10.0)
    guard.add_argument("--max-output-bytes", type=_positive_int, default=CHILD_OUTPUT_MAX_BYTES)

    probe = subparsers.add_parser("probe")
    probe.add_argument("--state", required=True)
    probe.add_argument("--stale-seconds", type=_positive_float, default=300.0)
    probe.add_argument("--max-consecutive-failures", type=_positive_int, default=3)
    probe.add_argument("--max-tick-seconds", type=_positive_float)
    probe.add_argument("--watchdog-state")
    _runtime_arguments(probe)

    wait = subparsers.add_parser("wait-healthy")
    wait.add_argument("--state", required=True)
    wait.add_argument("--stale-seconds", type=_positive_float, default=60.0)
    wait.add_argument("--max-consecutive-failures", type=_positive_int, default=3)
    wait.add_argument("--max-tick-seconds", type=_positive_float)
    wait.add_argument("--timeout-seconds", type=_positive_float, default=60.0)
    wait.add_argument("--started-after-epoch", type=float, required=True)
    wait.add_argument("--watchdog-state", required=True)
    _runtime_arguments(wait)

    render = subparsers.add_parser("render-plists")
    _runtime_arguments(render)
    for argument in (
        "worker-template",
        "watchdog-template",
        "worker-output",
        "watchdog-output",
        "python",
        "watchdog-python",
        "watchdog-script",
        "state",
        "lock",
        "rate-state",
        "watchdog-state",
        "launchd-target",
    ):
        render.add_argument(f"--{argument}", required=True)
    render.add_argument("--poll-seconds", type=_positive_float, default=30.0)
    render.add_argument("--stale-seconds", type=_positive_float, default=300.0)
    render.add_argument("--max-tick-seconds", type=_positive_float)
    render.add_argument("--term-grace-seconds", type=_positive_float, default=10.0)
    render.add_argument("--max-consecutive-failures", type=_positive_int, default=3)
    render.add_argument("--watchdog-interval", type=_positive_int, default=60)
    render.add_argument("--alert-interval-seconds", type=_positive_float, default=900.0)
    render.add_argument("--startup-grace-seconds", type=_positive_float, default=120.0)
    return parser


def _runtime_context(args: argparse.Namespace) -> tuple[Path, Path, Path, Path, dict[str, str], dict[str, str]]:
    config = _require_absolute(args.config, "config path")
    env_file = _require_absolute(args.env_file, "environment file")
    root = _require_absolute(args.root, "runtime root")
    source_root = _require_absolute(args.source_root, "Alice source root")
    _check_path_components(config)
    _check_path_components(env_file)
    _check_path_components(source_root)
    _check_path_components(root, allow_missing_leaf=True, allow_missing_parents=True)
    env_values = load_env_file(env_file)
    environment = sanitized_environment(env_values)
    return config, env_file, root, source_root, env_values, environment


def _resolve_from_context(
    config: Path,
    root: Path,
    source_root: Path,
    environment: Mapping[str, str],
) -> RuntimeIdentity:
    return resolve_runtime_identity(
        config=config,
        root=root,
        source_root=source_root,
        environment=environment,
    )


def _signal_handler(stop: threading.Event) -> Callable[[int, object], None]:
    def handler(_signum: int, _frame: object) -> None:
        stop.set()

    return handler


def _normalized_exit_code(result: ProcessResult) -> int:
    if result.ok:
        return 0
    if 1 <= result.exit_code <= 255:
        return result.exit_code
    return 1


def _run_guard_tick(args: argparse.Namespace) -> int:
    expected = _expected_identity(args)
    release_root = _require_absolute(args.release_root, "execution release")
    resolved_config = _require_absolute(
        args.resolved_config, "resolved execution configuration"
    )
    root = _require_absolute(args.root, "runtime root")
    snapshot = ExecutionSnapshot(release_root, resolved_config)
    if resolved_config != release_root / ".alice-resolved-config.json":
        raise ServiceError("guardian configuration is outside its execution release")
    if isinstance(args.control_fd, bool) or args.control_fd < 3:
        raise ServiceError("guardian control descriptor is invalid")
    try:
        descriptor_metadata = os.fstat(args.control_fd)
    except OSError as exc:
        raise ServiceError("guardian control descriptor is unavailable") from exc
    if not stat.S_ISFIFO(descriptor_metadata.st_mode):
        raise ServiceError("guardian control descriptor is not a pipe")
    verify_execution_snapshot(snapshot, root=root, expected_identity=expected)

    stop = threading.Event()

    def monitor_worker() -> None:
        try:
            while True:
                chunk = os.read(args.control_fd, 1)
                if not chunk:
                    break
                # The control channel has no data protocol.  Any byte is an
                # explicit abort request, while EOF covers a hard-killed worker.
                break
        except OSError:
            pass
        finally:
            stop.set()

    monitor = threading.Thread(
        target=monitor_worker, name="alice-worker-liveness", daemon=True
    )
    monitor.start()
    handler = _signal_handler(stop)
    previous_term = signal.signal(signal.SIGTERM, handler)
    previous_int = signal.signal(signal.SIGINT, handler)
    try:
        child = BoundedProcessRunner(
            timeout_seconds=args.max_tick_seconds,
            term_grace_seconds=args.term_grace_seconds,
            max_output_bytes=args.max_output_bytes,
        ).run(
            _isolated_module_argv(
                Path(sys.executable),
                snapshot,
                "alice",
                [
                    "--config",
                    str(snapshot.resolved_config),
                    "--root",
                    str(root),
                    "tick",
                    "--count",
                    "1",
                ],
            ),
            environment=_execution_environment(os.environ),
            cwd=snapshot.root,
            stop_event=stop,
        )
        verify_execution_snapshot(snapshot, root=root, expected_identity=expected)
        print(
            json.dumps(
                {
                    "exit_code": child.exit_code,
                    "message_hash": child.digest,
                    "ok": child.ok,
                },
                sort_keys=True,
            )
        )
        return _normalized_exit_code(child)
    finally:
        signal.signal(signal.SIGTERM, previous_term)
        signal.signal(signal.SIGINT, previous_int)
        try:
            os.close(args.control_fd)
        except OSError:
            pass


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "guard-tick":
            return _run_guard_tick(args)

        if args.command in {"identity", "preflight", "run", "probe", "wait-healthy", "render-plists"}:
            config, env_file, root, source_root, _env_values, environment = _runtime_context(args)
            identity, resolved_runtime_config, _source_capture = _resolve_runtime_inputs(
                config=config,
                root=root,
                source_root=source_root,
                environment=environment,
            )
            identity_resolver = lambda: _resolve_from_context(
                config, root, source_root, environment
            )
            if hasattr(args, "max_tick_seconds"):
                args.max_tick_seconds = effective_max_tick_seconds(
                    args.max_tick_seconds, resolved_runtime_config
                )

        if args.command == "identity":
            print(json.dumps(identity.to_dict(), sort_keys=True))
            return 0

        if args.command == "preflight":
            if identity.effect_mode == "dry-run" and not args.allow_dry_run:
                raise ServiceError(
                    "refusing to install a dry-run service without --allow-dry-run"
                )
            snapshot, sealed_identity = materialize_execution_snapshot(
                config=config,
                root=root,
                source_root=source_root,
                environment=environment,
                expected_identity=identity,
            )
            doctor = BoundedProcessRunner(
                timeout_seconds=args.doctor_timeout_seconds,
                term_grace_seconds=10.0,
                max_output_bytes=CHILD_OUTPUT_MAX_BYTES,
            ).run(
                _isolated_module_argv(
                    Path(sys.executable),
                    snapshot,
                    "alice",
                    [
                    "--config",
                    str(snapshot.resolved_config),
                    "--root",
                    str(root),
                    "doctor",
                    ],
                ),
                environment=_execution_environment(environment),
                cwd=snapshot.root,
            )
            if not doctor.ok:
                print(
                    f"Alice doctor failed (message sha256 {doctor.digest})",
                    file=sys.stderr,
                )
                return doctor.exit_code or 1
            verify_execution_snapshot(
                snapshot, root=root, expected_identity=sealed_identity
            )
            if identity_resolver() != sealed_identity:
                raise IdentityMismatch(
                    "Alice source or configuration changed during doctor"
                )
            print(json.dumps({"doctor": "ready", **identity.to_dict()}, sort_keys=True))
            return 0

        if args.command == "run":
            expected = _expected_identity(args)
            if identity != expected:
                raise IdentityMismatch("installation identity does not match runtime")
            snapshot, _sealed_identity = materialize_execution_snapshot(
                config=config,
                root=root,
                source_root=source_root,
                environment=environment,
                expected_identity=expected,
            )

            def pinned_identity_resolver() -> RuntimeIdentity:
                actual = identity_resolver()
                verify_execution_snapshot(
                    snapshot, root=root, expected_identity=expected
                )
                return actual

            child_runner = BoundedProcessRunner(
                timeout_seconds=(
                    args.max_tick_seconds + (2 * args.term_grace_seconds) + 30.0
                ),
                term_grace_seconds=args.term_grace_seconds,
                max_output_bytes=args.max_output_bytes,
            )

            def tick_executor(
                stop_event: threading.Event | None,
                progress_callback: Callable[[], None],
            ) -> ProcessResult:
                read_fd, write_fd = os.pipe()
                try:
                    return child_runner.run(
                        _isolated_module_argv(
                            Path(sys.executable),
                            snapshot,
                            "alice.service",
                            [
                                "guard-tick",
                                "--release-root",
                                str(snapshot.root),
                                "--resolved-config",
                                str(snapshot.resolved_config),
                                "--root",
                                str(root),
                                "--control-fd",
                                str(read_fd),
                                "--expected-source-tree-sha256",
                                expected.source_tree_sha256,
                                "--expected-config-sha256",
                                expected.config_sha256,
                                "--expected-policy-hash",
                                expected.policy_hash,
                                "--expected-effect-mode",
                                expected.effect_mode,
                                "--max-tick-seconds",
                                str(args.max_tick_seconds),
                                "--term-grace-seconds",
                                str(args.term_grace_seconds),
                                "--max-output-bytes",
                                str(args.max_output_bytes),
                            ],
                        ),
                        environment=_execution_environment(environment),
                        cwd=snapshot.root,
                        stop_event=stop_event,
                        progress_callback=progress_callback,
                        progress_interval_seconds=args.heartbeat_seconds,
                        pass_fds=(read_fd,),
                    )
                finally:
                    os.close(read_fd)
                    os.close(write_fd)

            runner = ServiceRunner(
                health_store=HealthStore(args.state),
                expected_identity=expected,
                identity_resolver=pinned_identity_resolver,
                tick_executor=tick_executor,
            )
            stop = threading.Event()
            handler = _signal_handler(stop)
            previous_term = signal.signal(signal.SIGTERM, handler)
            previous_int = signal.signal(signal.SIGINT, handler)
            try:
                with WorkerLock(args.lock):
                    runner.start()
                    while not stop.is_set():
                        result = runner.run_tick(stop)
                        if result.fatal:
                            return result.exit_code
                        if args.once:
                            return result.exit_code
                        stop.wait(args.poll_seconds)
                    runner.heartbeat()
                    return 0
            except WorkerAlreadyRunning:
                return EX_TEMPFAIL
            finally:
                signal.signal(signal.SIGTERM, previous_term)
                signal.signal(signal.SIGINT, previous_int)

        if args.command in {"probe", "wait-healthy"}:
            store = HealthStore(args.state)
            snapshot = ExecutionSnapshot(
                _release_path(root, identity),
                _release_path(root, identity) / ".alice-resolved-config.json",
            )
            verify_execution_snapshot(snapshot, root=root, expected_identity=identity)
            if args.command == "probe":
                result = probe_health(
                    store,
                    stale_seconds=args.stale_seconds,
                    max_consecutive_failures=args.max_consecutive_failures,
                    max_tick_seconds=args.max_tick_seconds,
                    expected_identity=identity,
                )
                if args.watchdog_state and not watchdog_receipt_ok(
                    _require_absolute(args.watchdog_state, "watchdog receipt"),
                    expected_identity=identity,
                    maximum_age_seconds=args.stale_seconds,
                ):
                    result = ProbeResult(
                        False,
                        (*result.problems, "watchdog_unhealthy"),
                        result.state,
                    )
                print(json.dumps(result.safe_summary(), sort_keys=True))
                return 0 if result.ok else 2
            if not math.isfinite(args.started_after_epoch):
                raise ServiceError("started-after epoch must be finite")
            deadline = time.monotonic() + args.timeout_seconds
            while True:
                identity = identity_resolver()
                verify_execution_snapshot(
                    snapshot, root=root, expected_identity=identity
                )
                result = probe_health(
                    store,
                    stale_seconds=args.stale_seconds,
                    max_consecutive_failures=args.max_consecutive_failures,
                    max_tick_seconds=args.max_tick_seconds,
                    expected_identity=identity,
                )
                if post_start_health_ok(
                    result,
                    expected_identity=identity,
                    watchdog_state=_require_absolute(
                        args.watchdog_state, "watchdog receipt"
                    ),
                    started_after_epoch=args.started_after_epoch,
                    maximum_age_seconds=args.stale_seconds,
                ):
                    print(json.dumps(result.safe_summary(), sort_keys=True))
                    return 0
                if time.monotonic() >= deadline:
                    print(json.dumps(result.safe_summary(), sort_keys=True))
                    return 2
                time.sleep(0.25)

        if args.command == "render-plists":
            release = _release_path(root, identity)
            verify_execution_snapshot(
                ExecutionSnapshot(
                    release, release / ".alice-resolved-config.json"
                ),
                root=root,
                expected_identity=identity,
            )
            render_plists(
                worker_template=_require_absolute(args.worker_template, "worker template"),
                watchdog_template=_require_absolute(args.watchdog_template, "watchdog template"),
                worker_output=_require_absolute(args.worker_output, "worker plist"),
                watchdog_output=_require_absolute(args.watchdog_output, "watchdog plist"),
                python=_require_absolute(args.python, "venv Python"),
                watchdog_script=_require_absolute(args.watchdog_script, "watchdog script"),
                watchdog_python=_require_absolute(
                    args.watchdog_python, "watchdog Python"
                ),
                config=config,
                env_file=env_file,
                root=root,
                state=_require_absolute(args.state, "health state"),
                lock=_require_absolute(args.lock, "worker lock"),
                rate_state=_require_absolute(args.rate_state, "alert rate state"),
                watchdog_state=_require_absolute(
                    args.watchdog_state, "watchdog receipt"
                ),
                source_root=source_root,
                identity=identity,
                poll_seconds=args.poll_seconds,
                stale_seconds=args.stale_seconds,
                max_tick_seconds=args.max_tick_seconds,
                term_grace_seconds=args.term_grace_seconds,
                max_consecutive_failures=args.max_consecutive_failures,
                watchdog_interval=args.watchdog_interval,
                alert_interval_seconds=args.alert_interval_seconds,
                startup_grace_seconds=args.startup_grace_seconds,
                launchd_target=args.launchd_target,
            )
            print(json.dumps(identity.to_dict(), sort_keys=True))
            return 0
    except IdentityMismatch as exc:
        print(f"Alice service identity error: {exc}", file=sys.stderr)
        return EX_CONFIG
    except ServiceError as exc:
        print(f"Alice service error: {exc}", file=sys.stderr)
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
