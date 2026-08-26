"""One whole-run native Claude Code session launcher.

Claude Code is a peer Manager runtime, not a Python agent framework.  This
adapter owns only the vendor CLI boundary: an exact session id, a bounded
JSONL protocol, a fail-closed sandbox, and a private host checkpoint.  Product
reasoning and native subagent delegation remain inside Claude Code.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import signal
import stat
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from workshop.errors import ContractError
from workshop.runtime.managers import NativeManagerInvocationError
from workshop.runtime.project_boundary import PRODUCT_RUN_ROOT_MARKER


ALLOWED_WORKSHOP_CLAUDE_MODELS = frozenset(
    (
        "claude-opus-5",
        "claude-fable-5",
        "claude-sonnet-5",
        "claude-opus-4-8",
        "claude-opus-4-6",
        "claude-sonnet-4-6",
    )
)
ALLOWED_CLAUDE_EFFORT_LEVELS = frozenset(
    ("low", "medium", "high", "xhigh", "max")
)
MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION = (2, 1, 246)
DEFAULT_CLAUDE_TIMEOUT_SECONDS = 1_200
MAX_CLAUDE_EVENT_BYTES = 1 * 1024 * 1024
MAX_CLAUDE_PROMPT_BYTES = 1 * 1024 * 1024
MAX_CLAUDE_GOAL_CONDITION_CHARS = 4_000
MAX_CLAUDE_MESSAGE_BYTES = 64 * 1024
MAX_CLAUDE_STDERR_BYTES = 256 * 1024
MAX_CLAUDE_SESSION_CHECKPOINT_BYTES = 32 * 1024
MAX_CLAUDE_PLUGIN_FILE_BYTES = 2 * 1024 * 1024
MAX_CLAUDE_PLUGIN_FILES = 4_096
CLAUDE_SESSION_CHECKPOINT_KIND = "autonomous-workshop-native-claude-session"
CLAUDE_SESSION_CHECKPOINT_NAME = "claude-session.json"
CLAUDE_GOAL_CHECKPOINT_KIND = "autonomous-workshop-native-claude-goal"
CLAUDE_GOAL_CHECKPOINT_NAME = "claude-goal.json"
CLAUDE_PRIVATE_HOME_NAME = "claude-home"
CLAUDE_PRIVATE_CONFIG_NAME = "claude-config"
CLAUDE_PRIVATE_TEMP_NAME = "claude-tmp"
CLAUDE_PERMISSION_MODE = "dontAsk"
CLAUDE_PLUGIN_ROOT = ".claude"
CLAUDE_SYSTEM_PROMPT_PATH = "AGENTS.md"
CLAUDE_GOAL_CONTINUATION_PROMPT = (
    "Continue the restored active Workshop Goal. Re-read the immutable "
    "STAGE.json and keep working until its existing Goal condition is satisfied."
)
_MAX_TRANSIENT_DIAGNOSTIC_CHARS = 64 * 1024
_PROCESS_EXIT_GRACE_SECONDS = 0.5
_TRANSIENT_DIAGNOSTIC_MARKERS = (
    "stream disconnected before completion",
    "connection reset by peer",
    "connection closed before completion",
    "provider connection was closed",
    "provider stream disconnected",
    "service temporarily unavailable",
    "temporarily unavailable",
    "upstream request timeout",
)

# ``--tools`` is an availability boundary, while the inline permissions below
# are an approval boundary.  Keep both explicit.  Claude Code 2.1 reports the
# native Agent tool as ``Task``; the init attester normalizes that one alias.
CLAUDE_ALLOWED_TOOLS = (
    "Agent",
    "Bash",
    "Edit",
    "Skill",
    "WebFetch",
    "WebSearch",
    "Write",
)
_CLAUDE_NON_FILESYSTEM_PERMISSION_ALLOW_RULES = (
    "Agent",
    "Bash",
    "Skill",
    "WebFetch",
    "WebSearch",
)

# Claude's built-in Read/Glob/Grep tools do not provide a separately attested
# filesystem sandbox boundary.  Product-run inspection therefore goes through
# sandboxed Bash.  These fixed roots are the only host filesystem additions
# Bash may read so that trusted executables and their dynamic loaders work on
# supported macOS/Linux hosts.
_SYSTEM_RUNTIME_READ_ROOTS = (
    "/bin",
    "/usr/bin",
    "/usr/lib",
    "/lib",
    "/lib64",
    "/System/Library",
    "/Library/Apple",
)

# Only authentication required by the Claude parent process is inherited.
# Every admitted credential variable is separately denied to sandboxed Bash.
# Claude Code 2.1.246's subprocess scrub forces the effective permission mode
# back to ``default``, so bind it off rather than accept that silent weakening.
CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST = (
    "PATH",
    "ANTHROPIC_API_KEY",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)
_CLAUDE_AUTH_ENVIRONMENT_NAMES = (
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "CLAUDE_CODE_OAUTH_TOKEN",
)
_CLAUDE_RUN_STATIC_ENVIRONMENT_OVERRIDES = (
    ("PYTHONHASHSEED", "0"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PYTHONNOUSERSITE", "1"),
    ("DISABLE_AUTOUPDATER", "1"),
    ("CLAUDE_CODE_DISABLE_AUTO_MEMORY", "1"),
    ("CLAUDE_AGENT_SDK_DISABLE_BUILTIN_AGENTS", "1"),
    ("CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY", "1"),
    ("CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS", "1"),
    ("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC", "1"),
    ("CLAUDE_CODE_DISABLE_TERMINAL_TITLE", "1"),
    ("CLAUDE_CODE_SUBPROCESS_ENV_SCRUB", "0"),
    ("ENABLE_CLAUDEAI_MCP_SERVERS", "false"),
)
_IMMUTABLE_PRODUCT_RUN_PATHS = (
    ".agents",
    ".claude",
    PRODUCT_RUN_ROOT_MARKER,
    "AGENTS.md",
    "CLAUDE.md",
    "MANAGER.json",
    "STAGE.json",
    "WISH.json",
)
_CREDENTIAL_FILE_PATHS = (
    "~/.anthropic",
    "~/.aws",
    "~/.azure",
    "~/.config/gcloud",
    "~/.config/gh",
    "~/.config/pip",
    "~/.claude",
    "~/.claude.json",
    "~/.docker",
    "~/.gnupg",
    "~/.kube",
    "~/.netrc",
    "~/.npmrc",
    "~/.pypirc",
    "~/.ssh",
)
_PLUGIN_NAME = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_COMPONENT_NAME = re.compile(r"^[a-z][a-z0-9-]{1,63}$")
_GOAL_STAGE = re.compile(r"^(match|invent|make|playtest|release)$")


class ClaudeInvocationError(NativeManagerInvocationError):
    """Claude Code could not complete an attested native turn."""


class _ClaudeProcessNotSpawned(ClaudeInvocationError):
    """Claude provably could not receive this invocation's prompt."""


@dataclass(frozen=True)
class _TrustedRuntimePathIdentity:
    path: str
    resolved_path: str
    device: int
    inode: int
    mode: int
    resolved_device: int
    resolved_inode: int
    resolved_mode: int

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "path": self.path,
            "resolved_path": self.resolved_path,
            "device": self.device,
            "inode": self.inode,
            "mode": self.mode,
            "resolved_device": self.resolved_device,
            "resolved_inode": self.resolved_inode,
            "resolved_mode": self.resolved_mode,
        }


@dataclass(frozen=True)
class _ClaudePluginProjection:
    root: Path
    name: str
    manifest_sha256: str
    tree_sha256: str
    agents: tuple[str, ...]
    skills: tuple[str, ...]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "root_sha256": _path_sha256(self.root),
            "name": self.name,
            "manifest_sha256": self.manifest_sha256,
            "tree_sha256": self.tree_sha256,
            "agents": list(self.agents),
            "skills": list(self.skills),
        }


@dataclass(frozen=True)
class _ClaudeRunPolicy:
    settings_json: str
    permission_allow_rules: tuple[str, ...]
    system_prompt_sha256: str
    trusted_python_runtime_paths: tuple[_TrustedRuntimePathIdentity, ...]
    trusted_system_runtime_paths: tuple[_TrustedRuntimePathIdentity, ...]
    environment_allowlist: tuple[str, ...]
    environment_overrides: tuple[tuple[str, str], ...]
    private_state_directories: tuple[_TrustedRuntimePathIdentity, ...]
    plugin: _ClaudePluginProjection

    def environment(
        self,
        source: Optional[Mapping[str, str]] = None,
    ) -> Mapping[str, str]:
        values = dict(
            claude_subprocess_environment(
                source,
                allowlist=self.environment_allowlist,
            )
        )
        values.update(dict(self.environment_overrides))
        return values


@dataclass(frozen=True)
class _ClaudeGoalState:
    """Durable distinction between an interrupted Goal and a new stage Goal."""

    session_checkpoint_sha256: str
    stage: str
    stage_checkpoint_sha256: str
    prompt_sha256: str
    attempt: int
    status: str
    revision: int
    schema_version: int = 1
    kind: str = CLAUDE_GOAL_CHECKPOINT_KIND

    def __post_init__(self) -> None:
        if (
            self.schema_version != 1
            or self.kind != CLAUDE_GOAL_CHECKPOINT_KIND
            or not isinstance(self.stage, str)
            or _GOAL_STAGE.fullmatch(self.stage) is None
            or type(self.attempt) is not int
            or not 1 <= self.attempt <= 2**53 - 1
            or type(self.revision) is not int
            or not 1 <= self.revision <= 2**53 - 1
            or self.revision < self.attempt
            or self.status not in (
                "prepared",
                "active",
                "returned",
                "completed",
            )
        ):
            raise ContractError("Claude native Goal state is invalid")
        _require_sha256(
            self.session_checkpoint_sha256,
            "Claude native Goal session checkpoint sha256",
        )
        _require_sha256(
            self.stage_checkpoint_sha256,
            "Claude native Goal stage checkpoint sha256",
        )
        _require_sha256(self.prompt_sha256, "Claude native Goal prompt sha256")

    def identity(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "session_checkpoint_sha256": self.session_checkpoint_sha256,
            "stage": self.stage,
            "stage_checkpoint_sha256": self.stage_checkpoint_sha256,
            "goal_prompt_sha256": self.prompt_sha256,
            "attempt": self.attempt,
            "status": self.status,
            "revision": self.revision,
        }

    def to_dict(self) -> Mapping[str, Any]:
        identity = {
            **self.identity(),
        }
        return {
            **identity,
            "state_sha256": _sha256_json(identity),
        }

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
    ) -> "_ClaudeGoalState":
        expected_fields = {
            "schema_version",
            "kind",
            "session_checkpoint_sha256",
            "stage",
            "stage_checkpoint_sha256",
            "goal_prompt_sha256",
            "attempt",
            "status",
            "revision",
            "state_sha256",
        }
        if set(payload) != expected_fields:
            raise ContractError("Claude native Goal state fields are invalid")
        try:
            state = cls(
                session_checkpoint_sha256=payload["session_checkpoint_sha256"],
                stage=payload["stage"],
                stage_checkpoint_sha256=payload["stage_checkpoint_sha256"],
                prompt_sha256=payload["goal_prompt_sha256"],
                attempt=payload["attempt"],
                status=payload["status"],
                revision=payload["revision"],
                schema_version=payload["schema_version"],
                kind=payload["kind"],
            )
        except (KeyError, ContractError, TypeError, ValueError) as exc:
            raise ContractError("Claude native Goal state is invalid") from exc
        if payload["state_sha256"] != _sha256_json(state.identity()):
            raise ContractError("Claude native Goal state binding is invalid")
        return state


def _goal_state_with_status(
    state: _ClaudeGoalState,
    status: str,
    *,
    revision: Optional[int] = None,
) -> _ClaudeGoalState:
    return _ClaudeGoalState(
        session_checkpoint_sha256=state.session_checkpoint_sha256,
        stage=state.stage,
        stage_checkpoint_sha256=state.stage_checkpoint_sha256,
        prompt_sha256=state.prompt_sha256,
        attempt=state.attempt,
        status=status,
        revision=state.revision if revision is None else revision,
    )


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            dict(value),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Claude session state must be finite JSON") from exc


def _sha256_json(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ContractError("%s must be a lowercase sha256" % label)
    return value


def _bounded_identifier(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 256
        or value != value.strip()
        or any(ord(character) < 33 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be a bounded identifier" % label)
    return value


def _canonical_session_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise ContractError("Claude session checkpoint identity is invalid")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ContractError("Claude session checkpoint identity is invalid") from exc
    canonical = str(parsed)
    if value != canonical:
        raise ContractError("Claude session checkpoint identity is invalid")
    return canonical


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _resolve_run_root(value: Path) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        raise ContractError("Claude native run root must be absolute")
    if requested.is_symlink():
        raise ContractError("Claude native run root must not be a symlink")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Claude native run root must already exist") from exc
    if not root.is_dir():
        raise ContractError("Claude native run root must be a directory")
    if requested != root:
        raise ContractError("Claude native run root must not contain symlinks")
    return root


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _resolve_host_state_root(value: Path, run_root: Path) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        raise ContractError("Claude host state root must be absolute")
    if requested.is_symlink():
        raise ContractError("Claude host state root must not be a symlink")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Claude host state root must already exist") from exc
    if not root.is_dir():
        raise ContractError("Claude host state root must be a directory")
    if requested != root:
        raise ContractError("Claude host state root must not contain symlinks")
    if _is_within(root, run_root) or _is_within(run_root, root):
        raise ContractError("Claude host state root and run root must not overlap")
    if stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise ContractError("Claude host state root permissions must be 0700")
    return root


def _checkpoint_path(host_state_root: Path) -> Path:
    return host_state_root / CLAUDE_SESSION_CHECKPOINT_NAME


def _goal_checkpoint_path(host_state_root: Path) -> Path:
    return host_state_root / CLAUDE_GOAL_CHECKPOINT_NAME


def _read_descriptor_to_eof(descriptor: int, limit: int) -> bytes:
    chunks = []
    remaining = limit + 1
    while remaining:
        chunk = os.read(descriptor, min(64 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _write_private_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    source = _canonical_json(value) + b"\n"
    if len(source) > MAX_CLAUDE_SESSION_CHECKPOINT_BYTES:
        raise ClaudeInvocationError(
            "Claude session checkpoint exceeded its safe size limit"
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name,
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(source):
            written += os.write(descriptor, source[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.link(str(temporary), str(path), follow_symlinks=False)
        directory_descriptor = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except FileExistsError as exc:
        raise ClaudeInvocationError(
            "Claude session checkpoint already exists; resume it explicitly"
        ) from exc
    except ClaudeInvocationError:
        raise
    except OSError as exc:
        raise ClaudeInvocationError(
            "Claude session checkpoint could not be persisted"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _replace_private_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    """Atomically replace mutable Goal state inside one private checkpoint."""

    source = _canonical_json(value) + b"\n"
    if len(source) > MAX_CLAUDE_SESSION_CHECKPOINT_BYTES:
        raise ClaudeInvocationError(
            "Claude session checkpoint exceeded its safe size limit"
        )
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name,
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    replaced = False
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(source):
            written += os.write(descriptor, source[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(str(temporary), str(path))
        replaced = True
        directory_descriptor = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise ClaudeInvocationError(
            "Claude session checkpoint could not be updated"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if not replaced:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _read_private_checkpoint(path: Path) -> Mapping[str, Any]:
    try:
        expected = path.lstat()
    except FileNotFoundError as exc:
        raise ContractError("Claude session checkpoint is missing") from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ContractError("Claude session checkpoint must be a regular private file")
    if stat.S_IMODE(expected.st_mode) != 0o600:
        raise ContractError("Claude session checkpoint permissions must be 0600")
    if not 1 <= expected.st_size <= MAX_CLAUDE_SESSION_CHECKPOINT_BYTES:
        raise ContractError("Claude session checkpoint size is invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("Claude session checkpoint cannot be read safely") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ContractError("Claude session checkpoint changed while opening")
        source = _read_descriptor_to_eof(
            descriptor,
            MAX_CLAUDE_SESSION_CHECKPOINT_BYTES,
        )
        if len(source) > MAX_CLAUDE_SESSION_CHECKPOINT_BYTES:
            raise ContractError("Claude session checkpoint size is invalid")
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("Claude session checkpoint changed while reading")
    finally:
        os.close(descriptor)
    try:
        payload = json.loads(source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Claude session checkpoint is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ContractError("Claude session checkpoint must contain one object")
    if source != _canonical_json(payload) + b"\n":
        raise ContractError("Claude session checkpoint is not canonical JSON")
    return payload


def _remove_created_private_checkpoints(
    checkpoints: tuple[tuple[Path, Mapping[str, Any]], ...],
) -> None:
    """Remove only exact checkpoints created before a process failed to spawn."""

    if not checkpoints:
        return
    parent = checkpoints[0][0].parent
    if any(path.parent != parent for path, unused_value in checkpoints):
        raise ClaudeInvocationError(
            "Claude unlaunched session checkpoints could not be rolled back safely"
        )
    identities: list[tuple[Path, int, int]] = []
    for path, expected in checkpoints:
        try:
            observed = _read_private_checkpoint(path)
            identity = path.lstat()
        except (ContractError, OSError) as exc:
            raise ClaudeInvocationError(
                "Claude unlaunched session checkpoints could not be rolled back safely"
            ) from exc
        if dict(observed) != dict(expected):
            raise ClaudeInvocationError(
                "Claude unlaunched session checkpoints could not be rolled back safely"
            )
        identities.append((path, identity.st_dev, identity.st_ino))
    try:
        for path, device, inode in identities:
            current = path.lstat()
            if (
                path.is_symlink()
                or not stat.S_ISREG(current.st_mode)
                or (current.st_dev, current.st_ino) != (device, inode)
            ):
                raise OSError("checkpoint changed before rollback")
            path.unlink()
        directory_descriptor = os.open(
            str(parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except OSError as exc:
        raise ClaudeInvocationError(
            "Claude unlaunched session checkpoints could not be rolled back safely"
        ) from exc


def _rollback_unlaunched_checkpoints(
    *,
    session_path: Path,
    session_checkpoint: Mapping[str, Any],
    goal_path: Path,
    goal_checkpoint: Mapping[str, Any],
) -> None:
    """Remove an unlaunched bootstrap with the session commit marker first."""

    present: list[tuple[Path, Mapping[str, Any]]] = []
    for path, expected in (
        (session_path, session_checkpoint),
        (goal_path, goal_checkpoint),
    ):
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ClaudeInvocationError(
                "Claude unlaunched session checkpoints could not be inspected safely"
            ) from exc
        present.append((path, expected))
    _remove_created_private_checkpoints(tuple(present))


def _recover_uncommitted_goal_checkpoint(path: Path) -> None:
    """Remove only the prepared first-attempt half of an uncommitted bootstrap."""

    try:
        payload = _read_private_checkpoint(path)
        state = _ClaudeGoalState.from_mapping(payload)
    except ContractError as exc:
        raise ContractError(
            "Claude uncommitted Goal checkpoint is invalid and cannot be recovered"
        ) from exc
    if state.status != "prepared" or state.attempt != 1 or state.revision != 1:
        raise ContractError(
            "Claude Goal checkpoint exists without its committed native session"
        )
    _remove_created_private_checkpoints(((path, payload),))


def claude_supports_native_workshop(version: str) -> bool:
    """Return whether Claude Code has the required sandbox/settings fixes."""

    if not isinstance(version, str):
        return False
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9.-]+)?", version)
    if match is None:
        return False
    return tuple(int(part) for part in match.groups()) >= (
        MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION
    )


def claude_subprocess_environment(
    source: Optional[Mapping[str, str]] = None,
    *,
    allowlist: Optional[tuple[str, ...]] = None,
) -> Mapping[str, str]:
    """Keep only Claude authentication and non-secret runtime inputs."""

    names = (
        CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST
        if allowlist is None
        else tuple(allowlist)
    )
    if (
        any(
            not isinstance(name, str)
            or not name
            or name not in CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST
            for name in names
        )
        or len(names) != len(set(names))
    ):
        raise ValueError("Claude subprocess environment allowlist is invalid")
    values = os.environ if source is None else source
    return {
        name: value
        for name in names
        if isinstance((value := values.get(name)), str) and value
    }


def _trusted_runtime_path_identity(path: Path) -> _TrustedRuntimePathIdentity:
    try:
        source = path.lstat()
        resolved = path.resolve(strict=True)
        target = resolved.stat()
    except OSError as exc:
        raise ClaudeInvocationError(
            "Workshop Python runtime changed while its Claude sandbox was prepared"
        ) from exc
    if not (
        stat.S_ISREG(source.st_mode)
        or stat.S_ISDIR(source.st_mode)
        or stat.S_ISLNK(source.st_mode)
    ) or not (stat.S_ISREG(target.st_mode) or stat.S_ISDIR(target.st_mode)):
        raise ClaudeInvocationError(
            "Workshop Python runtime contains an unsafe filesystem object"
        )
    return _TrustedRuntimePathIdentity(
        path=str(path),
        resolved_path=str(resolved),
        device=source.st_dev,
        inode=source.st_ino,
        mode=source.st_mode,
        resolved_device=target.st_dev,
        resolved_inode=target.st_ino,
        resolved_mode=target.st_mode,
    )


def _python_runtime_permission_identities(
) -> tuple[_TrustedRuntimePathIdentity, ...]:
    executable = Path(sys.executable)
    try:
        resolved = executable.resolve(strict=True)
    except OSError as exc:
        raise ClaudeInvocationError(
            "Workshop Python runtime is unavailable to the Claude sandbox"
        ) from exc
    candidates = {executable, resolved}
    for name in (
        "python",
        "python3",
        "python%d.%d" % (sys.version_info.major, sys.version_info.minor),
    ):
        candidate = executable.parent / name
        try:
            if candidate.resolve(strict=True) == resolved:
                candidates.add(candidate)
        except OSError:
            continue
    marker = executable.parent.parent / "pyvenv.cfg"
    if marker.is_file() and not marker.is_symlink():
        candidates.add(marker)
    for key in ("stdlib", "platstdlib", "purelib", "platlib"):
        value = sysconfig.get_path(key)
        if not isinstance(value, str) or not value:
            continue
        path = Path(value)
        try:
            resolved_path = path.resolve(strict=True)
        except OSError:
            continue
        if resolved_path.is_dir():
            candidates.add(resolved_path)
    return tuple(
        _trusted_runtime_path_identity(path)
        for path in sorted(candidates, key=lambda candidate: str(candidate))
    )


def _system_runtime_permission_identities(
) -> tuple[_TrustedRuntimePathIdentity, ...]:
    candidates = []
    for value in _SYSTEM_RUNTIME_READ_ROOTS:
        path = Path(value)
        try:
            identity = path.lstat()
        except OSError:
            continue
        if not (stat.S_ISDIR(identity.st_mode) or stat.S_ISLNK(identity.st_mode)):
            raise ClaudeInvocationError(
                "Claude system runtime read root is an unsafe filesystem object"
            )
        candidates.append(path)
    return tuple(_trusted_runtime_path_identity(path) for path in candidates)


def _read_bounded_regular_file(
    path: Path,
    label: str,
    *,
    allow_empty: bool = False,
) -> bytes:
    try:
        identity = path.lstat()
    except OSError as exc:
        raise ContractError("Claude %s is missing" % label) from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise ContractError("Claude %s must be a regular file" % label)
    minimum_size = 0 if allow_empty else 1
    if not minimum_size <= identity.st_size <= MAX_CLAUDE_PLUGIN_FILE_BYTES:
        raise ContractError("Claude %s size is invalid" % label)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("Claude %s cannot be read safely" % label) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (identity.st_dev, identity.st_ino)
        ):
            raise ContractError("Claude %s changed while opening" % label)
        source = _read_descriptor_to_eof(
            descriptor,
            MAX_CLAUDE_PLUGIN_FILE_BYTES,
        )
        if len(source) > MAX_CLAUDE_PLUGIN_FILE_BYTES:
            raise ContractError("Claude %s size is invalid" % label)
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("Claude %s changed while reading" % label)
    finally:
        os.close(descriptor)
    return source


def _frontmatter_name(source: bytes, label: str) -> str:
    try:
        text = source.decode("utf-8")
    except UnicodeError as exc:
        raise ContractError("Claude %s must be UTF-8" % label) from exc
    if "\x00" in text or not text.startswith("---\n"):
        raise ContractError("Claude %s frontmatter is invalid" % label)
    marker = text.find("\n---\n", 4)
    if marker < 0:
        raise ContractError("Claude %s frontmatter is invalid" % label)
    names = []
    for line in text[4:marker].splitlines():
        match = re.fullmatch(r"name:\s*([a-z][a-z0-9-]{1,63})\s*", line)
        if match is not None:
            names.append(match.group(1))
    if len(names) != 1:
        raise ContractError("Claude %s must declare one component name" % label)
    return names[0]


def _plugin_projection(run_root: Path) -> _ClaudePluginProjection:
    root = run_root / CLAUDE_PLUGIN_ROOT
    try:
        identity = root.lstat()
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Claude product-run plugin is missing") from exc
    if root.is_symlink() or not stat.S_ISDIR(identity.st_mode) or resolved != root:
        raise ContractError("Claude product-run plugin root is unsafe")

    manifest_path = root / ".claude-plugin" / "plugin.json"
    manifest_source = _read_bounded_regular_file(manifest_path, "plugin manifest")
    try:
        manifest = json.loads(manifest_source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Claude plugin manifest is not valid JSON") from exc
    if not isinstance(manifest, Mapping):
        raise ContractError("Claude plugin manifest must contain one object")
    expected_manifest = {
        "name": "autonomous-workshop",
        "description": "Host-projected Workshop runtime",
        "version": "1.0.0",
        "author": {"name": "Autonomous Workshop"},
    }
    plugin_name = manifest.get("name")
    if (
        not isinstance(plugin_name, str)
        or _PLUGIN_NAME.fullmatch(plugin_name) is None
        or dict(manifest) != expected_manifest
        or manifest_source != _canonical_json(expected_manifest) + b"\n"
    ):
        raise ContractError("Claude plugin manifest is not canonical")

    if {path.name for path in root.iterdir()} != {
        ".claude-plugin",
        "agents",
        "skills",
    }:
        raise ContractError("Claude product-run plugin contains an extra component")
    manifest_root = root / ".claude-plugin"
    if (
        manifest_root.is_symlink()
        or not manifest_root.is_dir()
        or {path.name for path in manifest_root.iterdir()} != {"plugin.json"}
    ):
        raise ContractError("Claude plugin metadata directory is invalid")

    tree_hasher = hashlib.sha256()
    files = 0
    for candidate in sorted(root.rglob("*"), key=lambda path: path.as_posix()):
        try:
            candidate_identity = candidate.lstat()
        except OSError as exc:
            raise ContractError("Claude plugin tree changed while scanning") from exc
        if candidate.is_symlink():
            raise ContractError("Claude product-run plugin must not contain symlinks")
        relative = candidate.relative_to(root).as_posix()
        if stat.S_ISDIR(candidate_identity.st_mode):
            tree_hasher.update(b"D\0" + relative.encode("utf-8") + b"\0")
            continue
        if not stat.S_ISREG(candidate_identity.st_mode):
            raise ContractError("Claude product-run plugin contains an unsafe object")
        files += 1
        if files > MAX_CLAUDE_PLUGIN_FILES:
            raise ContractError("Claude product-run plugin contains too many files")
        source = _read_bounded_regular_file(
            candidate,
            "plugin file",
            allow_empty=True,
        )
        tree_hasher.update(
            b"F\0"
            + relative.encode("utf-8")
            + b"\0"
            + hashlib.sha256(source).digest()
        )

    agent_root = root / "agents"
    skill_root = root / "skills"
    if not agent_root.is_dir() or agent_root.is_symlink():
        raise ContractError("Claude product-run plugin agent roster is missing")
    if not skill_root.is_dir() or skill_root.is_symlink():
        raise ContractError("Claude product-run plugin skill roster is missing")

    agents: list[str] = []
    for path in sorted(agent_root.iterdir(), key=lambda candidate: candidate.name):
        if path.suffix != ".md":
            raise ContractError("Claude plugin agent roster contains an extra entry")
        component = _frontmatter_name(
            _read_bounded_regular_file(path, "plugin agent"),
            "plugin agent",
        )
        if path.stem != component:
            raise ContractError("Claude plugin agent filename does not match its name")
        agents.append("%s:%s" % (plugin_name, component))
    if not agents or len(agents) != len(set(agents)):
        raise ContractError("Claude product-run plugin agent roster is invalid")

    skills: list[str] = []
    for path in sorted(skill_root.iterdir(), key=lambda candidate: candidate.name):
        if (
            path.is_symlink()
            or not path.is_dir()
            or _COMPONENT_NAME.fullmatch(path.name) is None
        ):
            raise ContractError("Claude plugin skill roster contains an extra entry")
        skill_path = path / "SKILL.md"
        component = _frontmatter_name(
            _read_bounded_regular_file(skill_path, "plugin skill"),
            "plugin skill",
        )
        if component != path.name:
            raise ContractError("Claude plugin skill directory does not match its name")
        skills.append("%s:%s" % (plugin_name, path.name))
    if not skills or len(skills) != len(set(skills)):
        raise ContractError("Claude product-run plugin skill roster is invalid")

    return _ClaudePluginProjection(
        root=root,
        name=plugin_name,
        manifest_sha256=hashlib.sha256(manifest_source).hexdigest(),
        tree_sha256=tree_hasher.hexdigest(),
        agents=tuple(agents),
        skills=tuple(skills),
    )


def _absolute_permission_glob(run_root: Path) -> str:
    value = run_root.as_posix()
    if (
        not value.startswith("/")
        or re.search(r"[\x00-\x1f\x7f*?()\[\]{}]", value) is not None
    ):
        raise ContractError(
            "Claude native run root cannot be represented by an exact permission rule"
        )
    # Claude permission rules use ``//`` for an absolute filesystem path.
    return "/" + value + "/**"


def _permission_allow_rules(run_root: Path) -> tuple[str, ...]:
    root_glob = _absolute_permission_glob(run_root)
    return (
        *_CLAUDE_NON_FILESYSTEM_PERMISSION_ALLOW_RULES,
        "Edit(%s)" % root_glob,
        "Write(%s)" % root_glob,
    )


def _permission_rules(
    run_root: Path,
    allow_rules: tuple[str, ...],
) -> Mapping[str, Any]:
    immutable = []
    for relative in _IMMUTABLE_PRODUCT_RUN_PATHS:
        immutable.extend(("Edit(/%s)" % relative, "Write(/%s)" % relative))
        if relative in (".agents", ".claude"):
            immutable.extend(
                ("Edit(/%s/**)" % relative, "Write(/%s/**)" % relative)
            )
    return {
        "allow": list(allow_rules),
        "ask": [],
        "deny": [
            "Read(/.env)",
            "Read(/.env.*)",
            "Read(/**/.env)",
            "Read(/**/.env.*)",
            *immutable,
            "mcp__*",
        ],
        "defaultMode": CLAUDE_PERMISSION_MODE,
    }


def _sandbox_settings(
    run_root: Path,
    trusted_paths: tuple[_TrustedRuntimePathIdentity, ...],
) -> Mapping[str, Any]:
    immutable = [str(run_root / relative) for relative in _IMMUTABLE_PRODUCT_RUN_PATHS]
    return {
        "enabled": True,
        "failIfUnavailable": True,
        "autoAllowBashIfSandboxed": True,
        "excludedCommands": [],
        "allowUnsandboxedCommands": False,
        "filesystem": {
            "denyRead": ["/"],
            "allowRead": [
                str(run_root),
                *(identity.path for identity in trusted_paths),
                *(identity.resolved_path for identity in trusted_paths),
            ],
            "allowWrite": [str(run_root)],
            "denyWrite": immutable,
        },
        "network": {
            "allowedDomains": [],
            "deniedDomains": ["*"],
            "allowUnixSockets": [],
            "allowAllUnixSockets": False,
            "allowLocalBinding": False,
        },
        "credentials": {
            "envVars": [
                {"name": name, "mode": "deny"}
                for name in _CLAUDE_AUTH_ENVIRONMENT_NAMES
            ],
            "files": [
                {"path": path, "mode": "deny"}
                for path in _CREDENTIAL_FILE_PATHS
            ],
        },
    }


def _claude_run_policy(
    run_root: Path,
    host_state_root: Path,
    *,
    require_empty_private_state: bool = False,
    create_private_state: bool = True,
) -> _ClaudeRunPolicy:
    trusted_python_paths = _python_runtime_permission_identities()
    trusted_system_paths = _system_runtime_permission_identities()
    trusted_paths = trusted_python_paths + trusted_system_paths
    permission_allow_rules = _permission_allow_rules(run_root)
    plugin = _plugin_projection(run_root)
    system_prompt = run_root / CLAUDE_SYSTEM_PROMPT_PATH
    system_prompt_source = _read_bounded_regular_file(system_prompt, "system prompt")
    private_temp = str(run_root / ".tmp")
    private_home = _private_claude_state_directory(
        host_state_root / CLAUDE_PRIVATE_HOME_NAME,
        "home",
        require_empty=require_empty_private_state,
        create=create_private_state,
    )
    private_config = _private_claude_state_directory(
        host_state_root / CLAUDE_PRIVATE_CONFIG_NAME,
        "configuration",
        require_empty=require_empty_private_state,
        create=create_private_state,
    )
    private_claude_temp = _private_claude_state_directory(
        host_state_root / CLAUDE_PRIVATE_TEMP_NAME,
        "temporary-state",
        require_empty=require_empty_private_state,
        create=create_private_state,
    )
    overrides = (
        ("TMPDIR", private_temp),
        ("TMP", private_temp),
        ("TEMP", private_temp),
        ("HOME", private_home.path),
        ("CLAUDE_CONFIG_DIR", private_config.path),
        ("CLAUDE_CODE_TMPDIR", private_claude_temp.path),
        *_CLAUDE_RUN_STATIC_ENVIRONMENT_OVERRIDES,
    )
    settings = {
        "permissions": _permission_rules(run_root, permission_allow_rules),
        "sandbox": _sandbox_settings(run_root, trusted_paths),
        "autoMemoryEnabled": False,
        "cleanupPeriodDays": 36_500,
        "disableClaudeAiConnectors": True,
        "includeGitInstructions": False,
        "remoteControlAtStartup": False,
        "syncClaudeAiSkills": False,
    }
    return _ClaudeRunPolicy(
        settings_json=_canonical_json(settings).decode("utf-8"),
        permission_allow_rules=permission_allow_rules,
        system_prompt_sha256=hashlib.sha256(system_prompt_source).hexdigest(),
        trusted_python_runtime_paths=trusted_python_paths,
        trusted_system_runtime_paths=trusted_system_paths,
        environment_allowlist=tuple(CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST),
        environment_overrides=overrides,
        private_state_directories=(
            private_home,
            private_config,
            private_claude_temp,
        ),
        plugin=plugin,
    )


def _private_claude_state_directory(
    path: Path,
    label: str,
    *,
    require_empty: bool = False,
    create: bool = True,
) -> _TrustedRuntimePathIdentity:
    """Create one host-private Claude directory outside agent tool authority."""

    if create:
        try:
            path.mkdir(mode=0o700)
        except FileExistsError:
            pass
        except OSError as exc:
            raise ClaudeInvocationError(
                "Claude private %s directory could not be created" % label
            ) from exc
    identity = _private_claude_state_directory_identity(path, label)
    if require_empty:
        try:
            entries = tuple(os.scandir(path))
        except OSError as exc:
            raise ClaudeInvocationError(
                "Claude private %s directory could not be inspected" % label
            ) from exc
        if entries:
            raise ClaudeInvocationError(
                "Claude private %s directory must be empty before first launch"
                % label
            )
        if _private_claude_state_directory_identity(path, label) != identity:
            raise ClaudeInvocationError(
                "Claude private %s directory changed while it was inspected" % label
            )
    return identity


def _private_claude_state_directory_identity(
    path: Path,
    label: str,
) -> _TrustedRuntimePathIdentity:
    try:
        source = path.lstat()
        resolved = path.resolve(strict=True)
        target = resolved.stat()
    except OSError as exc:
        raise ClaudeInvocationError(
            "Claude private %s directory is unavailable" % label
        ) from exc
    if (
        path.is_symlink()
        or not stat.S_ISDIR(source.st_mode)
        or resolved != path
        or not stat.S_ISDIR(target.st_mode)
        or stat.S_IMODE(source.st_mode) != 0o700
        or stat.S_IMODE(target.st_mode) != 0o700
    ):
        raise ClaudeInvocationError(
            "Claude private %s directory must be a real 0700 directory" % label
        )
    return _TrustedRuntimePathIdentity(
        path=str(path),
        resolved_path=str(resolved),
        device=source.st_dev,
        inode=source.st_ino,
        mode=source.st_mode,
        resolved_device=target.st_dev,
        resolved_inode=target.st_ino,
        resolved_mode=target.st_mode,
    )


def _validate_private_claude_state_directory(
    expected: _TrustedRuntimePathIdentity,
    label: str,
) -> str:
    observed = _private_claude_state_directory_identity(Path(expected.path), label)
    if observed != expected:
        raise ClaudeInvocationError(
            "Claude private %s directory changed after policy binding" % label
        )
    return expected.path


def _private_run_temp(run_root: Path) -> Path:
    path = run_root / ".tmp"
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as exc:
        raise ClaudeInvocationError(
            "Claude product-run temp directory could not be created"
        ) from exc
    try:
        identity = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ClaudeInvocationError(
            "Claude product-run temp directory is unavailable"
        ) from exc
    if (
        path.is_symlink()
        or not stat.S_ISDIR(identity.st_mode)
        or resolved != path
        or stat.S_IMODE(identity.st_mode) != 0o700
    ):
        raise ClaudeInvocationError(
            "Claude product-run temp directory must be a real 0700 directory"
        )
    return path


def _claude_run_environment(
    run_root: Path,
    host_state_root: Path,
    run_policy: _ClaudeRunPolicy,
) -> Mapping[str, str]:
    private_temp = str(_private_run_temp(run_root))
    expected_private_paths = (
        (host_state_root / CLAUDE_PRIVATE_HOME_NAME, "home"),
        (host_state_root / CLAUDE_PRIVATE_CONFIG_NAME, "configuration"),
        (host_state_root / CLAUDE_PRIVATE_TEMP_NAME, "temporary-state"),
    )
    if len(run_policy.private_state_directories) != len(expected_private_paths):
        raise ClaudeInvocationError("Claude private state policy is invalid")
    private_values = []
    for identity, (expected_path, label) in zip(
        run_policy.private_state_directories,
        expected_private_paths,
    ):
        if identity.path != str(expected_path):
            raise ClaudeInvocationError("Claude private state policy is invalid")
        private_values.append(
            _validate_private_claude_state_directory(identity, label)
        )
    private_home, private_config, private_claude_temp = private_values
    overrides = dict(run_policy.environment_overrides)
    if any(
        overrides.get(name) != private_temp
        for name in ("TMPDIR", "TMP", "TEMP")
    ) or overrides.get("HOME") != private_home or overrides.get(
        "CLAUDE_CONFIG_DIR"
    ) != private_config or overrides.get(
        "CLAUDE_CODE_TMPDIR"
    ) != private_claude_temp:
        raise ClaudeInvocationError(
            "Claude product-run environment does not match its bound policy"
        )
    environment = run_policy.environment()
    if not environment.get("ANTHROPIC_API_KEY"):
        raise ClaudeInvocationError(
            "Claude isolated profile requires ANTHROPIC_API_KEY authentication"
        )
    return environment


def _runtime_config_sha256(
    cli_version: str,
    model: str,
    effort: str,
    run_policy: _ClaudeRunPolicy,
) -> str:
    return _sha256_json(
        {
            "adapter": "claude-code-cli-native-session",
            "bare": False,
            "configuration_profile": "isolated-non-bare",
            "cli_version": cli_version,
            "event_protocol": "claude-stream-json-init-result-v1",
            "model": model,
            "effort": effort,
            "input_format": "text",
            "output_format": "stream-json",
            "verbose": True,
            "setting_sources": [],
            "strict_empty_mcp": True,
            "permission_mode": CLAUDE_PERMISSION_MODE,
            "available_tools": list(CLAUDE_ALLOWED_TOOLS),
            "permission_allow_rules": list(run_policy.permission_allow_rules),
            "cli_agents": {},
            "append_system_prompt_file": CLAUDE_SYSTEM_PROMPT_PATH,
            "system_prompt_sha256": run_policy.system_prompt_sha256,
            "plugin": run_policy.plugin.to_dict(),
            "settings_json_sha256": hashlib.sha256(
                run_policy.settings_json.encode("utf-8")
            ).hexdigest(),
            "trusted_python_runtime_paths": [
                identity.to_dict()
                for identity in run_policy.trusted_python_runtime_paths
            ],
            "trusted_system_runtime_paths": [
                identity.to_dict()
                for identity in run_policy.trusted_system_runtime_paths
            ],
            "private_state_directories": [
                identity.to_dict()
                for identity in run_policy.private_state_directories
            ],
            "subprocess_environment": {
                "allowlist": list(run_policy.environment_allowlist),
                "overrides": [
                    {"name": name, "value": value}
                    for name, value in run_policy.environment_overrides
                ],
                "subprocess_env_scrub": False,
            },
            "process_group_isolation": os.name == "posix",
        }
    )


@dataclass(frozen=True)
class ClaudeNativeSessionBinding:
    """Redacted identity for one Wish-wide native Claude Code session."""

    product_id: str
    wish_sha256: str
    constitution_sha256: str
    run_root_sha256: str
    host_state_root_sha256: str
    runtime_config_sha256: str
    checkpoint_sha256: str
    schema_version: int = 1
    kind: str = CLAUDE_SESSION_CHECKPOINT_KIND

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.kind != CLAUDE_SESSION_CHECKPOINT_KIND:
            raise ContractError("Claude native session binding version is invalid")
        _bounded_identifier(self.product_id, "Claude native session product_id")
        for value, label in (
            (self.wish_sha256, "Claude native session Wish sha256"),
            (
                self.constitution_sha256,
                "Claude native session constitution sha256",
            ),
            (self.run_root_sha256, "Claude native session run-root sha256"),
            (
                self.host_state_root_sha256,
                "Claude native session host-state-root sha256",
            ),
            (
                self.runtime_config_sha256,
                "Claude native session runtime-config sha256",
            ),
            (
                self.checkpoint_sha256,
                "Claude native session checkpoint sha256",
            ),
        ):
            _require_sha256(value, label)

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "constitution_sha256": self.constitution_sha256,
            "run_root_sha256": self.run_root_sha256,
            "host_state_root_sha256": self.host_state_root_sha256,
            "runtime_config_sha256": self.runtime_config_sha256,
            "checkpoint_sha256": self.checkpoint_sha256,
        }


@dataclass(frozen=True)
class ClaudeNativeSessionOutcome:
    """Compact public outcome; messages, events, and UUID stay private."""

    binding: ClaudeNativeSessionBinding
    used_web_search: bool
    status: str = "completed"

    def __post_init__(self) -> None:
        if not isinstance(self.binding, ClaudeNativeSessionBinding):
            raise ContractError("Claude native session outcome requires a binding")
        if self.status != "completed":
            raise ContractError("Claude native session outcome status is invalid")
        if type(self.used_web_search) is not bool:
            raise ContractError("Claude native session search status must be boolean")

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "status": self.status,
            "session": self.binding.to_dict(),
            "used_web_search": self.used_web_search,
        }


def _validated_prompt(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ContractError("Claude native session prompt must be bounded text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractError("Claude native session prompt must be UTF-8") from exc
    if size > MAX_CLAUDE_PROMPT_BYTES:
        raise ContractError("Claude native session prompt exceeded its safe limit")
    if not value.startswith("/goal "):
        raise ContractError("Claude native session prompt must invoke /goal")
    condition = value.removeprefix("/goal ")
    if (
        not condition.strip()
        or len(condition) > MAX_CLAUDE_GOAL_CONDITION_CHARS
        or any(ord(character) < 32 and character not in "\n\t" for character in condition)
    ):
        raise ContractError("Claude native Goal condition is invalid")
    return value


def _goal_prompt_sha256(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def _validated_goal_binding(stage: Any, checkpoint_sha256: Any) -> tuple[str, str]:
    if not isinstance(stage, str) or _GOAL_STAGE.fullmatch(stage) is None:
        raise ContractError("Claude native Goal stage is invalid")
    return stage, _require_sha256(
        checkpoint_sha256,
        "Claude native Goal stage checkpoint sha256",
    )


def _validate_message_text(value: Any) -> str:
    if not isinstance(value, str):
        raise ContractError("Claude native session message must be text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractError("Claude native session message must be UTF-8") from exc
    if size > MAX_CLAUDE_MESSAGE_BYTES or "\x00" in value:
        raise ContractError("Claude native session message exceeded its safe limit")
    return value


class ClaudeNativeSessionLauncher:
    """Launch or resume one native Claude Code Manager for an entire Wish."""

    manager_id = "claude"
    session_checkpoint_name = CLAUDE_SESSION_CHECKPOINT_NAME

    def __init__(
        self,
        *,
        model: str = "claude-opus-5",
        effort: str = "high",
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CLAUDE_TIMEOUT_SECONDS,
        popen_factory: Any = subprocess.Popen,
        version_runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
        uuid_factory: Any = uuid.uuid4,
    ) -> None:
        if model not in ALLOWED_WORKSHOP_CLAUDE_MODELS:
            raise ContractError(
                "Workshop Claude model must be an explicitly supported, "
                "version-pinned Claude model"
            )
        if effort not in ALLOWED_CLAUDE_EFFORT_LEVELS:
            raise ValueError("unsupported Claude effort")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3_600:
            raise ValueError("Claude timeout_seconds must be from 1 to 3,600")
        self.binary = (
            binary or os.environ.get("WORKSHOP_CLAUDE_BIN") or shutil.which("claude")
        )
        self.model = model
        self.effort = effort
        self.timeout_seconds = timeout_seconds
        self._popen_factory = popen_factory
        self._version_runner = version_runner
        self._uuid_factory = uuid_factory
        self.cli_version = cli_version or self._read_cli_version()
        if self.binary and not claude_supports_native_workshop(self.cli_version):
            minimum = ".".join(
                str(part) for part in MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION
            )
            raise ClaudeInvocationError(
                "Workshop requires Claude Code %s or newer for isolated settings, "
                "native subagents, and fail-closed sandboxing" % minimum
            )

    def _read_cli_version(self) -> str:
        if not self.binary:
            return "0.0.0"
        try:
            completed = self._version_runner(
                [self.binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
                env=claude_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return "0.0.0"
        output = completed.stdout if isinstance(completed.stdout, str) else ""
        match = re.search(r"\d+(?:\.\d+){2}(?:[-+][A-Za-z0-9.-]+)?", output)
        return match.group(0) if match else "0.0.0"

    def start(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        prompt: str,
        goal_stage: str,
        goal_checkpoint_sha256: str,
    ) -> ClaudeNativeSessionOutcome:
        root, state_root, path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        goal_path = _goal_checkpoint_path(state_root)
        if path.exists() or path.is_symlink():
            raise ContractError(
                "Claude native session checkpoint already exists; resume it explicitly"
            )
        if goal_path.exists() or goal_path.is_symlink():
            # The immutable session checkpoint is the bootstrap commit marker.
            # A prepared first-attempt Goal without that marker can only be the
            # durable first half of a process that was never launched.
            _recover_uncommitted_goal_checkpoint(goal_path)
        prompt = _validated_prompt(prompt)
        goal_stage, goal_checkpoint_sha256 = _validated_goal_binding(
            goal_stage,
            goal_checkpoint_sha256,
        )
        run_policy = _claude_run_policy(
            root,
            state_root,
            require_empty_private_state=True,
        )
        run_environment = _claude_run_environment(root, state_root, run_policy)
        runtime_config_sha256 = _runtime_config_sha256(
            self.cli_version,
            self.model,
            self.effort,
            run_policy,
        )
        try:
            session_id = _canonical_session_id(str(self._uuid_factory()))
        except (ContractError, TypeError, ValueError):
            raise ClaudeInvocationError(
                "Claude native session id could not be allocated"
            ) from None
        identity = self._checkpoint_identity(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            session_id=session_id,
            runtime_config_sha256=runtime_config_sha256,
        )
        checkpoint_sha256 = _sha256_json(identity)
        prepared_goal_state = _ClaudeGoalState(
            session_checkpoint_sha256=checkpoint_sha256,
            stage=goal_stage,
            stage_checkpoint_sha256=goal_checkpoint_sha256,
            prompt_sha256=_goal_prompt_sha256(prompt),
            attempt=1,
            status="prepared",
            revision=1,
        )
        session_checkpoint = {
            **identity,
            "checkpoint_sha256": checkpoint_sha256,
        }
        prepared_goal_checkpoint = prepared_goal_state.to_dict()
        try:
            # Persist the mutable Goal half first, then publish the immutable
            # session checkpoint as the commit marker.  Recovery therefore
            # never observes a committed session without its Goal state.
            _write_private_checkpoint(goal_path, prepared_goal_checkpoint)
            _write_private_checkpoint(path, session_checkpoint)
        except BaseException:
            _rollback_unlaunched_checkpoints(
                session_path=path,
                session_checkpoint=session_checkpoint,
                goal_path=goal_path,
                goal_checkpoint=prepared_goal_checkpoint,
            )
            raise

        def activate_goal() -> None:
            _replace_private_checkpoint(
                goal_path,
                _goal_state_with_status(prepared_goal_state, "active").to_dict(),
            )

        def mark_goal_returned() -> None:
            _replace_private_checkpoint(
                goal_path,
                _goal_state_with_status(prepared_goal_state, "returned").to_dict(),
            )

        try:
            used_web_search = self._stream(
                command=self._start_command(session_id, root, run_policy),
                prompt=prompt,
                run_root=root,
                run_policy=run_policy,
                run_environment=run_environment,
                expected_session_id=session_id,
                on_goal_activated=activate_goal,
                on_result_attested=mark_goal_returned,
            )
        except _ClaudeProcessNotSpawned:
            _rollback_unlaunched_checkpoints(
                session_path=path,
                session_checkpoint=session_checkpoint,
                goal_path=goal_path,
                goal_checkpoint=prepared_goal_checkpoint,
            )
            raise
        return ClaudeNativeSessionOutcome(
            self._public_binding(
                product_id=product_id,
                wish_sha256=wish_sha256,
                constitution_sha256=constitution_sha256,
                run_root=root,
                host_state_root=state_root,
                runtime_config_sha256=runtime_config_sha256,
                checkpoint_sha256=checkpoint_sha256,
            ),
            used_web_search,
        )

    def resume(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        prompt: str,
        goal_stage: str,
        goal_checkpoint_sha256: str,
    ) -> ClaudeNativeSessionOutcome:
        root, state_root, path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        prompt = _validated_prompt(prompt)
        goal_stage, goal_checkpoint_sha256 = _validated_goal_binding(
            goal_stage,
            goal_checkpoint_sha256,
        )
        run_policy = _claude_run_policy(root, state_root)
        run_environment = _claude_run_environment(root, state_root, run_policy)
        runtime_config_sha256 = _runtime_config_sha256(
            self.cli_version,
            self.model,
            self.effort,
            run_policy,
        )
        session_id, checkpoint_sha256 = self._load_checkpoint(
            path=path,
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            runtime_config_sha256=runtime_config_sha256,
        )
        goal_path = _goal_checkpoint_path(state_root)
        goal_state = self._load_goal_state(
            goal_path,
            session_checkpoint_sha256=checkpoint_sha256,
        )
        prompt_sha256 = _goal_prompt_sha256(prompt)
        on_goal_activated: Optional[Callable[[], None]] = None
        previous_goal_state: Optional[_ClaudeGoalState] = None
        prepared_goal_state: Optional[_ClaudeGoalState] = None
        if goal_state.status == "prepared":
            raise ContractError(
                "Claude native Goal prompt delivery is ambiguous; a prepared Goal "
                "cannot be resumed safely"
            )
        if goal_state.status == "active":
            if (
                goal_state.stage != goal_stage
                or goal_state.stage_checkpoint_sha256 != goal_checkpoint_sha256
                or goal_state.prompt_sha256 != prompt_sha256
            ):
                raise ContractError(
                    "Claude cannot replace an interrupted active Goal with a new "
                    "stage Goal"
                )
            invocation_goal_state = goal_state
            stream_prompt = CLAUDE_GOAL_CONTINUATION_PROMPT
        else:
            if goal_state.status == "returned" and (
                goal_state.stage != goal_stage
                or goal_state.stage_checkpoint_sha256 != goal_checkpoint_sha256
                or goal_state.prompt_sha256 != prompt_sha256
            ):
                raise ContractError(
                    "Claude cannot replace a returned Goal awaiting host "
                    "acknowledgement with a different stage Goal"
                )
            previous_goal_state = goal_state
            prepared_goal_state = _ClaudeGoalState(
                session_checkpoint_sha256=checkpoint_sha256,
                stage=goal_stage,
                stage_checkpoint_sha256=goal_checkpoint_sha256,
                prompt_sha256=prompt_sha256,
                attempt=goal_state.attempt + 1,
                status="prepared",
                revision=goal_state.revision + 1,
            )
            _replace_private_checkpoint(
                goal_path,
                prepared_goal_state.to_dict(),
            )
            invocation_goal_state = prepared_goal_state

            def activate_goal() -> None:
                _replace_private_checkpoint(
                    goal_path,
                    _goal_state_with_status(
                        invocation_goal_state,
                        "active",
                    ).to_dict(),
                )

            on_goal_activated = activate_goal
            stream_prompt = prompt

        def mark_goal_returned() -> None:
            _replace_private_checkpoint(
                goal_path,
                _goal_state_with_status(
                    invocation_goal_state,
                    "returned",
                ).to_dict(),
            )

        try:
            used_web_search = self._stream(
                command=self._resume_command(session_id, root, run_policy),
                prompt=stream_prompt,
                run_root=root,
                run_policy=run_policy,
                run_environment=run_environment,
                expected_session_id=session_id,
                on_goal_activated=on_goal_activated,
                on_result_attested=mark_goal_returned,
            )
        except _ClaudeProcessNotSpawned:
            if previous_goal_state is not None and prepared_goal_state is not None:
                try:
                    observed_goal_state = self._load_goal_state(
                        goal_path,
                        session_checkpoint_sha256=checkpoint_sha256,
                    )
                except ContractError as exc:
                    raise ClaudeInvocationError(
                        "Claude unlaunched Goal could not be rolled back safely"
                    ) from exc
                if observed_goal_state != prepared_goal_state:
                    raise ClaudeInvocationError(
                        "Claude unlaunched Goal could not be rolled back safely"
                    )
                _replace_private_checkpoint(
                    goal_path,
                    previous_goal_state.to_dict(),
                )
            raise
        return ClaudeNativeSessionOutcome(
            self._public_binding(
                product_id=product_id,
                wish_sha256=wish_sha256,
                constitution_sha256=constitution_sha256,
                run_root=root,
                host_state_root=state_root,
                runtime_config_sha256=runtime_config_sha256,
                checkpoint_sha256=checkpoint_sha256,
            ),
            used_web_search,
        )

    def goal_disposition(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        prompt: str,
        goal_stage: str,
        goal_checkpoint_sha256: str,
    ) -> str:
        """Return the exact durable Goal sidecar state without launching Claude."""

        root, state_root, path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        prompt = _validated_prompt(prompt)
        goal_stage, goal_checkpoint_sha256 = _validated_goal_binding(
            goal_stage,
            goal_checkpoint_sha256,
        )
        run_policy = _claude_run_policy(
            root,
            state_root,
            create_private_state=False,
        )
        runtime_config_sha256 = _runtime_config_sha256(
            self.cli_version,
            self.model,
            self.effort,
            run_policy,
        )
        unused_session_id, checkpoint_sha256 = self._load_checkpoint(
            path=path,
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            runtime_config_sha256=runtime_config_sha256,
        )
        goal_state = self._load_goal_state(
            _goal_checkpoint_path(state_root),
            session_checkpoint_sha256=checkpoint_sha256,
        )
        if (
            goal_state.stage != goal_stage
            or goal_state.stage_checkpoint_sha256 != goal_checkpoint_sha256
            or goal_state.prompt_sha256 != _goal_prompt_sha256(prompt)
        ):
            raise ContractError(
                "Claude native Goal disposition does not match its current attempt"
            )
        return goal_state.status

    def acknowledge_goal(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        prompt: str,
        goal_stage: str,
        goal_checkpoint_sha256: str,
    ) -> None:
        """Mark one Goal complete only after the host validates its proposal."""

        root, state_root, path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        prompt = _validated_prompt(prompt)
        goal_stage, goal_checkpoint_sha256 = _validated_goal_binding(
            goal_stage,
            goal_checkpoint_sha256,
        )
        run_policy = _claude_run_policy(root, state_root)
        runtime_config_sha256 = _runtime_config_sha256(
            self.cli_version,
            self.model,
            self.effort,
            run_policy,
        )
        unused_session_id, checkpoint_sha256 = self._load_checkpoint(
            path=path,
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            runtime_config_sha256=runtime_config_sha256,
        )
        goal_path = _goal_checkpoint_path(state_root)
        goal_state = self._load_goal_state(
            goal_path,
            session_checkpoint_sha256=checkpoint_sha256,
        )
        if (
            goal_state.stage != goal_stage
            or goal_state.stage_checkpoint_sha256 != goal_checkpoint_sha256
            or goal_state.prompt_sha256 != _goal_prompt_sha256(prompt)
        ):
            raise ContractError(
                "Claude native Goal acknowledgement does not match its current attempt"
            )
        if goal_state.status == "completed":
            return
        if goal_state.status == "prepared":
            raise ContractError(
                "Claude native Goal acknowledgement cannot complete a prepared "
                "attempt with ambiguous prompt delivery"
            )
        if goal_state.status != "returned":
            raise ContractError(
                "Claude native Goal acknowledgement requires an attested terminal "
                "return"
            )
        completed = _goal_state_with_status(
            goal_state,
            "completed",
            revision=goal_state.revision + 1,
        )
        _replace_private_checkpoint(goal_path, completed.to_dict())

    def _binding_paths(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
    ) -> tuple[Path, Path, Path]:
        _bounded_identifier(product_id, "Claude native session product_id")
        _require_sha256(wish_sha256, "Claude native session Wish sha256")
        _require_sha256(
            constitution_sha256,
            "Claude native session constitution sha256",
        )
        root = _resolve_run_root(run_root)
        state_root = _resolve_host_state_root(host_state_root, root)
        return root, state_root, _checkpoint_path(state_root)

    def _checkpoint_identity(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        session_id: str,
        runtime_config_sha256: str,
    ) -> Mapping[str, Any]:
        return {
            "schema_version": 1,
            "kind": CLAUDE_SESSION_CHECKPOINT_KIND,
            "product_id": product_id,
            "wish_sha256": wish_sha256,
            "constitution_sha256": constitution_sha256,
            "run_root_sha256": _path_sha256(run_root),
            "host_state_root_sha256": _path_sha256(host_state_root),
            "runtime_config_sha256": _require_sha256(
                runtime_config_sha256,
                "Claude native session runtime-config sha256",
            ),
            "cli_version": self.cli_version,
            "permission_mode": CLAUDE_PERMISSION_MODE,
            "sandbox_required": True,
            "session_id": _canonical_session_id(session_id),
        }

    def _load_checkpoint(
        self,
        *,
        path: Path,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        runtime_config_sha256: str,
    ) -> tuple[str, str]:
        payload = _read_private_checkpoint(path)
        expected_fields = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "constitution_sha256",
            "run_root_sha256",
            "host_state_root_sha256",
            "runtime_config_sha256",
            "cli_version",
            "permission_mode",
            "sandbox_required",
            "session_id",
            "checkpoint_sha256",
        }
        if set(payload) != expected_fields:
            raise ContractError("Claude native session checkpoint fields are invalid")
        if (
            type(payload["schema_version"]) is not int
            or type(payload["sandbox_required"]) is not bool
        ):
            raise ContractError("Claude native session checkpoint binding is invalid")
        try:
            session_id = _canonical_session_id(payload["session_id"])
            checkpoint_sha256 = _require_sha256(
                payload["checkpoint_sha256"],
                "Claude native session checkpoint sha256",
            )
        except ContractError as exc:
            raise ContractError(
                "Claude native session checkpoint binding is invalid"
            ) from exc
        identity_fields = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "constitution_sha256",
            "run_root_sha256",
            "host_state_root_sha256",
            "runtime_config_sha256",
            "cli_version",
            "permission_mode",
            "sandbox_required",
            "session_id",
        }
        identity = {key: payload[key] for key in identity_fields}
        expected = self._checkpoint_identity(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
            session_id=session_id,
            runtime_config_sha256=runtime_config_sha256,
        )
        if identity != expected or checkpoint_sha256 != _sha256_json(identity):
            raise ContractError("Claude native session checkpoint binding is invalid")
        return session_id, checkpoint_sha256

    def _load_goal_state(
        self,
        path: Path,
        *,
        session_checkpoint_sha256: str,
    ) -> _ClaudeGoalState:
        try:
            state = _ClaudeGoalState.from_mapping(_read_private_checkpoint(path))
        except ContractError as exc:
            raise ContractError(
                "Claude native Goal checkpoint is missing or invalid; its active "
                "Goal cannot be resumed safely"
            ) from exc
        if state.session_checkpoint_sha256 != session_checkpoint_sha256:
            raise ContractError(
                "Claude native Goal checkpoint belongs to another session"
            )
        return state

    def _public_binding(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        runtime_config_sha256: str,
        checkpoint_sha256: str,
    ) -> ClaudeNativeSessionBinding:
        return ClaudeNativeSessionBinding(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root_sha256=_path_sha256(run_root),
            host_state_root_sha256=_path_sha256(host_state_root),
            runtime_config_sha256=runtime_config_sha256,
            checkpoint_sha256=checkpoint_sha256,
        )

    def _common_command(
        self,
        run_root: Path,
        run_policy: _ClaudeRunPolicy,
    ) -> list[str]:
        tools = ",".join(CLAUDE_ALLOWED_TOOLS)
        return [
            self.binary,
            "-p",
            "--input-format",
            "text",
            "--output-format",
            "stream-json",
            "--verbose",
            "--model",
            self.model,
            "--effort",
            self.effort,
            "--permission-mode",
            CLAUDE_PERMISSION_MODE,
            "--setting-sources",
            "",
            "--settings",
            run_policy.settings_json,
            "--strict-mcp-config",
            "--mcp-config",
            '{"mcpServers":{}}',
            "--plugin-dir",
            str(run_policy.plugin.root),
            "--append-system-prompt-file",
            str(run_root / CLAUDE_SYSTEM_PROMPT_PATH),
            "--tools",
            tools,
            "--allowedTools",
            *run_policy.permission_allow_rules,
            "--agents",
            "{}",
            "--no-chrome",
            "--prompt-suggestions",
            "false",
        ]

    def _start_command(
        self,
        session_id: str,
        run_root: Path,
        run_policy: _ClaudeRunPolicy,
    ) -> list[str]:
        return [
            *self._common_command(run_root, run_policy),
            "--session-id",
            _canonical_session_id(session_id),
        ]

    def _resume_command(
        self,
        session_id: str,
        run_root: Path,
        run_policy: _ClaudeRunPolicy,
    ) -> list[str]:
        return [
            *self._common_command(run_root, run_policy),
            "--resume",
            _canonical_session_id(session_id),
        ]

    def _stream(
        self,
        *,
        command: list[str],
        prompt: str,
        run_root: Path,
        run_policy: _ClaudeRunPolicy,
        run_environment: Mapping[str, str],
        expected_session_id: str,
        on_goal_activated: Optional[Callable[[], None]] = None,
        on_result_attested: Optional[Callable[[], None]] = None,
    ) -> bool:
        if on_goal_activated is not None and not prompt.startswith("/goal "):
            raise ContractError(
                "Claude native Goal activation requires an exact /goal condition"
            )
        expected_goal_condition = (
            prompt.removeprefix("/goal ")
            if on_goal_activated is not None
            else None
        )
        if not self.binary:
            raise _ClaudeProcessNotSpawned(
                "Claude Code is not installed or on PATH"
            )
        deadline = time.monotonic() + self.timeout_seconds
        popen_arguments: dict[str, Any] = {
            "stdin": subprocess.PIPE,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "text": True,
            "bufsize": 1,
            "cwd": str(run_root),
            "env": run_environment,
        }
        if os.name == "posix":
            popen_arguments["start_new_session"] = True
        elif os.name == "nt":  # pragma: no cover - exercised on Windows CI
            popen_arguments["creationflags"] = getattr(
                subprocess, "CREATE_NEW_PROCESS_GROUP", 0
            )
        try:
            process = self._popen_factory(command, **popen_arguments)
        except (OSError, subprocess.SubprocessError, TypeError, ValueError):
            raise _ClaudeProcessNotSpawned(
                "Claude native session could not be launched"
            ) from None
        if process.stdin is None or process.stdout is None or process.stderr is None:
            _terminate_process_group(process)
            raise _ClaudeProcessNotSpawned(
                "Claude native session streams are unavailable"
            )

        stderr_size = 0
        stderr_tail = ""
        stderr_overflow = threading.Event()

        def drain_stderr() -> None:
            nonlocal stderr_size, stderr_tail
            try:
                for raw in process.stderr:
                    text = _stream_text(raw)
                    stderr_size += len(text.encode("utf-8", errors="replace"))
                    stderr_tail = (stderr_tail + text)[
                        -_MAX_TRANSIENT_DIAGNOSTIC_CHARS:
                    ]
                    if stderr_size > MAX_CLAUDE_STDERR_BYTES:
                        stderr_overflow.set()
                        _terminate_process_group(process)
                        return
            except (OSError, ValueError, UnicodeError):
                stderr_overflow.set()

        stderr_thread = threading.Thread(
            target=drain_stderr,
            name="workshop-claude-stderr",
            daemon=True,
        )
        stderr_thread.start()

        timed_out = threading.Event()

        def expire() -> None:
            timed_out.set()
            _terminate_process_group(process)

        timer = threading.Timer(max(0.001, deadline - time.monotonic()), expire)
        timer.daemon = True
        timer.start()

        stdout_size = 0
        stdout_tail = ""
        used_web_search = False
        saw_init = False
        saw_goal_activation = on_goal_activated is None
        saw_result = False
        stream_failure: Optional[BaseException] = None
        try:
            try:
                process.stdin.write(prompt)
                process.stdin.flush()
                process.stdin.close()
            except (BrokenPipeError, OSError, ValueError):
                raise ClaudeInvocationError(
                    "Claude native session could not receive its prompt"
                ) from None

            for raw in process.stdout:
                text = _stream_text(raw)
                stdout_size += len(text.encode("utf-8", errors="replace"))
                stdout_tail = (stdout_tail + text)[
                    -_MAX_TRANSIENT_DIAGNOSTIC_CHARS:
                ]
                if stdout_size > MAX_CLAUDE_EVENT_BYTES:
                    raise ClaudeInvocationError(
                        "Claude native event stream exceeded its safe size limit"
                    )
                event = _decode_native_event(text)
                event_type = event.get("type")
                if saw_result:
                    raise ClaudeInvocationError(
                        "Claude native session returned events after its result"
                    )
                if not saw_init:
                    _attest_init_event(
                        event,
                        expected_session_id=expected_session_id,
                        run_root=run_root,
                        cli_version=self.cli_version,
                        model=self.model,
                        plugin=run_policy.plugin,
                    )
                    saw_init = True
                    continue
                _attest_event_session(event, expected_session_id)
                if event_type == "system" and event.get("subtype") == "init":
                    raise ClaudeInvocationError(
                        "Claude returned an ambiguous session initialization"
                    )
                if event_type == "result":
                    if not saw_goal_activation:
                        raise ClaudeInvocationError(
                            "Claude did not attest native Goal activation"
                        )
                    _attest_result_event(event, expected_session_id)
                    saw_result = True
                elif event_type == "assistant":
                    if not saw_goal_activation:
                        if (
                            expected_goal_condition is None
                            or on_goal_activated is None
                        ):
                            raise ClaudeInvocationError(
                                "Claude native Goal activation state was invalid"
                            )
                        _attest_goal_activation_event(
                            event,
                            expected_session_id=expected_session_id,
                            goal_condition=expected_goal_condition,
                        )
                        on_goal_activated()
                        saw_goal_activation = True
                    else:
                        used_web_search = (
                            _validate_assistant_event(event) or used_web_search
                        )
                elif event_type not in (
                    "user",
                    "system",
                    "stream_event",
                    "tool_progress",
                    "auth_status",
                    "rate_limit_event",
                ):
                    raise ClaudeInvocationError(
                        "Claude native session event stream was invalid"
                    )
        except BaseException as exc:
            stream_failure = exc
            _terminate_process_group(process)
        finally:
            timer.cancel()

        remaining = deadline - time.monotonic()
        try:
            returncode = process.wait(timeout=max(0.001, remaining))
        except (subprocess.TimeoutExpired, OSError, ValueError):
            timed_out.set()
            _terminate_process_group(process)
            returncode = getattr(process, "returncode", None)
        except BaseException:
            _terminate_process_group(process)
            try:
                stderr_thread.join(timeout=_PROCESS_EXIT_GRACE_SECONDS)
            except BaseException:
                pass
            raise
        stderr_thread.join(timeout=max(0.0, min(1.0, deadline - time.monotonic())))

        if stream_failure is not None and not isinstance(stream_failure, Exception):
            # Cancellation must retain its original control-flow semantics, but
            # only after the isolated child and its diagnostic thread have been
            # reaped above.
            raise stream_failure
        if timed_out.is_set():
            raise ClaudeInvocationError("Claude native session timed out")
        if stderr_thread.is_alive() or stderr_overflow.is_set():
            _terminate_process_group(process)
            raise ClaudeInvocationError(
                "Claude native diagnostic stream exceeded its safe limit"
            )
        if stream_failure is not None:
            if isinstance(stream_failure, (ClaudeInvocationError, ContractError)):
                raise stream_failure from None
            raise ClaudeInvocationError(
                "Claude native session event stream was invalid"
            ) from None
        if not saw_init or not saw_result or returncode != 0:
            if _is_explicit_transient_failure(stdout_tail, stderr_tail):
                raise ClaudeInvocationError(
                    "Claude native provider transport was interrupted"
                )
            raise ClaudeInvocationError("Claude native session did not complete")
        if on_result_attested is not None:
            # A syntactically valid result is not a terminal return until the
            # complete stream, bounded diagnostics, and zero process exit have
            # all been attested.  Persist returned only at that commit point.
            on_result_attested()
        return used_web_search


def _stream_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeError:
            raise ClaudeInvocationError(
                "Claude native session event stream was invalid"
            ) from None
    raise ClaudeInvocationError("Claude native session event stream was invalid")


def _decode_native_event(line: str) -> Mapping[str, Any]:
    if not line.strip():
        raise ClaudeInvocationError("Claude native session event stream was invalid")
    try:
        event = json.loads(line)
    except (TypeError, ValueError):
        raise ClaudeInvocationError(
            "Claude native session event stream was invalid"
        ) from None
    if not isinstance(event, Mapping):
        raise ClaudeInvocationError("Claude native session event stream was invalid")
    return event


def _attest_event_session(event: Mapping[str, Any], expected_session_id: str) -> None:
    value = event.get("session_id")
    if value is not None:
        try:
            observed = _canonical_session_id(value)
        except ContractError:
            raise ClaudeInvocationError(
                "Claude returned an invalid native session identity"
            ) from None
        if observed != expected_session_id:
            raise ClaudeInvocationError("Claude resumed a different native session")


def _attest_goal_activation_event(
    event: Mapping[str, Any],
    *,
    expected_session_id: str,
    goal_condition: str,
) -> None:
    """Attest Claude's synthetic acknowledgement of the exact /goal command."""

    if event.get("type") != "assistant" or event.get("session_id") is None:
        raise ClaudeInvocationError("Claude did not attest native Goal activation")
    _attest_event_session(event, expected_session_id)
    message = event.get("message")
    expected_content = [
        {
            "type": "text",
            "text": "Goal set: " + goal_condition,
        }
    ]
    if (
        event.get("parent_tool_use_id") is not None
        or not isinstance(message, Mapping)
        or message.get("model") != "<synthetic>"
        or message.get("role") != "assistant"
        or message.get("type") != "message"
        or message.get("stop_reason") != "end_turn"
        or message.get("content") != expected_content
        or any(
            message.get(field) is not None
            for field in (
                "container",
                "context_management",
                "diagnostics",
                "stop_details",
                "stop_sequence",
            )
        )
    ):
        raise ClaudeInvocationError("Claude did not attest native Goal activation")


def _attest_init_event(
    event: Mapping[str, Any],
    *,
    expected_session_id: str,
    run_root: Path,
    cli_version: str,
    model: str,
    plugin: _ClaudePluginProjection,
) -> None:
    if event.get("type") != "system" or event.get("subtype") != "init":
        raise ClaudeInvocationError(
            "Claude native session did not begin with an initialization event"
        )
    try:
        observed_session_id = _canonical_session_id(event.get("session_id"))
    except ContractError:
        raise ClaudeInvocationError(
            "Claude returned an invalid native session identity"
        ) from None
    if observed_session_id != expected_session_id:
        raise ClaudeInvocationError("Claude started a different native session")
    if (
        event.get("cwd") != str(run_root)
        or event.get("claude_code_version") != cli_version
        or event.get("model") != model
        or event.get("permissionMode") != CLAUDE_PERMISSION_MODE
        or event.get("mcp_servers") != []
        or event.get("apiKeySource") != "ANTHROPIC_API_KEY"
    ):
        raise ClaudeInvocationError(
            "Claude native session initialization did not match its launch policy"
        )
    expected_plugin = {
        "name": plugin.name,
        "path": str(plugin.root),
        "source": "%s@inline" % plugin.name,
        "version": "1.0.0",
    }
    if event.get("plugins") != [expected_plugin]:
        raise ClaudeInvocationError(
            "Claude native session plugin roster did not match its launch policy"
        )
    for field in ("plugin_errors", "mcp_server_errors"):
        errors = event.get(field, [])
        if not isinstance(errors, list) or errors:
            raise ClaudeInvocationError(
                "Claude native session initialization reported a load error"
            )
    tools = _normalized_tool_roster(
        _bounded_string_set(event.get("tools"), "tool"),
        cli_version,
    )
    if tools != frozenset(CLAUDE_ALLOWED_TOOLS):
        raise ClaudeInvocationError(
            "Claude native session tools did not match its launch policy"
        )
    agents = _bounded_string_set(event.get("agents"), "agent")
    # Empty setting sources and the built-in-agent disable switch leave only
    # the explicitly loaded, hash-bound plugin roster.
    if agents != frozenset(plugin.agents):
        raise ClaudeInvocationError(
            "Claude native session agent roster did not match its plugin"
        )
    skills = _bounded_string_set(event.get("skills"), "skill")
    expected_skills = frozenset(plugin.skills)
    slash_commands = _bounded_string_set(
        event.get("slash_commands"),
        "slash-command",
    )
    if (
        not expected_skills <= skills
        or not expected_skills <= slash_commands
        or "goal" not in slash_commands
        or any(":" in name and name not in expected_skills for name in skills)
        or any(
            ":" in name and name not in expected_skills for name in slash_commands
        )
    ):
        raise ClaudeInvocationError(
            "Claude native session skill roster did not match its plugin"
        )


def _bounded_string_set(value: Any, label: str) -> frozenset[str]:
    if (
        not isinstance(value, list)
        or len(value) > MAX_CLAUDE_PLUGIN_FILES
        or any(
            not isinstance(item, str)
            or not item
            or len(item) > 256
            or "\x00" in item
            for item in value
        )
        or len(value) != len(set(value))
    ):
        raise ClaudeInvocationError(
            "Claude native session %s roster was invalid" % label
        )
    return frozenset(value)


def _normalized_tool_roster(
    tools: frozenset[str],
    cli_version: str,
) -> frozenset[str]:
    """Normalize Claude Code's 2.1 stream name for the Agent/Task tool.

    The 2.1 CLI flag surface calls the tool ``Agent`` while some 2.1 stream
    builds attest it as ``Task``.  Do not carry the compatibility alias into a
    later minor release and do not accept both names in one event.
    """

    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9.-]+)?", cli_version)
    if match is None:
        raise ClaudeInvocationError("Claude native session version was invalid")
    if "Task" in tools:
        if "Agent" in tools or tuple(int(part) for part in match.groups())[:2] != (2, 1):
            raise ClaudeInvocationError(
                "Claude native session tools did not match its launch policy"
            )
        return frozenset("Agent" if value == "Task" else value for value in tools)
    return tools


def _attest_result_event(event: Mapping[str, Any], expected_session_id: str) -> None:
    if event.get("session_id") is None:
        raise ClaudeInvocationError(
            "Claude terminal result omitted its native session identity"
        )
    _attest_event_session(event, expected_session_id)
    stop_reason = event.get("stop_reason")
    terminal_reason = event.get("terminal_reason")
    permission_denials = event.get("permission_denials", [])
    if (
        event.get("subtype") != "success"
        or event.get("is_error") is not False
        or stop_reason not in (None, "end_turn", "stop_sequence")
        or terminal_reason not in (None, "completed")
        or not (
            stop_reason in ("end_turn", "stop_sequence")
            or terminal_reason == "completed"
        )
        or not isinstance(permission_denials, list)
        or permission_denials
    ):
        raise ClaudeInvocationError("Claude native session reported a failed turn")
    _validate_message_text(event.get("result"))


def _validate_assistant_event(event: Mapping[str, Any]) -> bool:
    message = event.get("message")
    if not isinstance(message, Mapping):
        raise ClaudeInvocationError("Claude native assistant event was invalid")
    content = message.get("content")
    if not isinstance(content, list) or len(content) > 4_096:
        raise ClaudeInvocationError("Claude native assistant event was invalid")
    used_web_search = False
    for block in content:
        if not isinstance(block, Mapping):
            raise ClaudeInvocationError("Claude native assistant event was invalid")
        block_type = block.get("type")
        if block_type == "text":
            _validate_message_text(block.get("text"))
        elif block_type == "tool_use":
            name = block.get("name")
            if not isinstance(name, str) or not name or len(name) > 256:
                raise ClaudeInvocationError("Claude native assistant event was invalid")
            if name == "WebSearch":
                used_web_search = True
    return used_web_search


def _terminate_process_group(process: Any) -> None:
    try:
        running = process.poll() is None
    except BaseException:
        running = True
    pid = getattr(process, "pid", None)
    used_group = False
    if running and os.name == "posix" and type(pid) is int and pid > 1:
        try:
            if pid != os.getpgrp():
                os.killpg(pid, signal.SIGTERM)
                used_group = True
        except BaseException:
            pass
    if running and not used_group:
        try:
            process.terminate()
        except BaseException:
            pass
    try:
        process.wait(timeout=_PROCESS_EXIT_GRACE_SECONDS)
        return
    except BaseException:
        pass
    killed_group = False
    if os.name == "posix" and type(pid) is int and pid > 1:
        try:
            if pid != os.getpgrp():
                os.killpg(pid, signal.SIGKILL)
                killed_group = True
        except BaseException:
            pass
    if not killed_group:
        try:
            process.kill()
        except BaseException:
            pass
    try:
        process.wait(timeout=_PROCESS_EXIT_GRACE_SECONDS)
    except BaseException:
        pass


def _diagnostic_tail(value: str) -> str:
    return value[-_MAX_TRANSIENT_DIAGNOSTIC_CHARS:].casefold()


def _is_explicit_transient_failure(stdout: str, stderr: str) -> bool:
    diagnostic = _diagnostic_tail(stdout) + "\n" + _diagnostic_tail(stderr)
    return any(marker in diagnostic for marker in _TRANSIENT_DIAGNOSTIC_MARKERS)


__all__ = [
    "ALLOWED_WORKSHOP_CLAUDE_MODELS",
    "CLAUDE_ALLOWED_TOOLS",
    "CLAUDE_PERMISSION_MODE",
    "CLAUDE_SESSION_CHECKPOINT_KIND",
    "CLAUDE_SESSION_CHECKPOINT_NAME",
    "CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST",
    "DEFAULT_CLAUDE_TIMEOUT_SECONDS",
    "MAX_CLAUDE_EVENT_BYTES",
    "MAX_CLAUDE_MESSAGE_BYTES",
    "MAX_CLAUDE_PROMPT_BYTES",
    "MAX_CLAUDE_SESSION_CHECKPOINT_BYTES",
    "MAX_CLAUDE_STDERR_BYTES",
    "MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION",
    "ClaudeInvocationError",
    "ClaudeNativeSessionBinding",
    "ClaudeNativeSessionLauncher",
    "ClaudeNativeSessionOutcome",
    "claude_subprocess_environment",
    "claude_supports_native_workshop",
]
