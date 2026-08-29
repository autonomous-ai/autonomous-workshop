"""One whole-run native Codex session launcher."""

from __future__ import annotations

import hashlib
import importlib
import json
import math
import os
import re
import signal
import shutil
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
from typing import Any, Callable, Iterator, Mapping, Optional

from workshop.errors import ContractError
from workshop.runtime.execution import (
    CODEX_SUBPROCESS_ENVIRONMENT_ALLOWLIST,
    codex_subprocess_environment,
)
from workshop.runtime.project_boundary import PRODUCT_RUN_ROOT_MARKER
from workshop.runtime.progress import SAFE_NATIVE_ACTIVITY_CLASSES


ALLOWED_WORKSHOP_MODELS = frozenset(
    ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")
)
CODEX_PERMISSION_PROFILE = "workshop-product-run"
MINIMUM_CODEX_NATIVE_RUNTIME_VERSION = (0, 145, 0)
DEFAULT_CODEX_TIMEOUT_SECONDS = 3_600
# A hard bound for one JSONL event record.  Native turns can legitimately emit
# many events while tools and subagents work; those records are reduced and
# discarded as they arrive, so their cumulative size is not a memory bound.
MAX_CODEX_EVENT_BYTES = 1 * 1024 * 1024
MAX_CODEX_PROMPT_BYTES = 1 * 1024 * 1024
MAX_CODEX_MESSAGE_BYTES = 64 * 1024
MAX_CODEX_STDERR_BYTES = 256 * 1024
MAX_CODEX_SESSION_CHECKPOINT_BYTES = 32 * 1024
CODEX_SESSION_CHECKPOINT_KIND = "autonomous-workshop-native-codex-session"
_MAX_TRANSIENT_DIAGNOSTIC_CHARS = 64 * 1024
_CODEX_TERMINAL_EXIT_GRACE_SECONDS = 0.25
# A successful finalizer is followed by native Goal completion and the public
# terminal event.  Keep that handoff bounded, but allow normal agent/tool
# bookkeeping to finish before treating the marker as a stuck stream.
_CODEX_FINALIZATION_MARKER_GRACE_SECONDS = 30.0
_CODEX_FINALIZATION_MARKER_POLL_SECONDS = 0.05
_CODEX_ACTIVITY_HEARTBEAT_SECONDS = 5.0
_CODEX_ACTIVITY_DELIVERY_TIMEOUT_SECONDS = 0.25
_MAX_PENDING_ACTIVITY_CLASSES = 64
_TRANSIENT_DIAGNOSTIC_HEADS = frozenset(
    (
        "stream disconnected before completion",
        "provider connection was closed",
        "provider stream disconnected",
    )
)
_MAX_NATIVE_FAILURE_MESSAGE_CHARS = 4 * 1024

_IMMUTABLE_PRODUCT_RUN_PATHS = (
    ".agents",
    ".codex",
    PRODUCT_RUN_ROOT_MARKER,
    "AGENTS.md",
    "STAGE.json",
    "VAULT.json",
    "WISH.json",
)
_CODEX_RUN_STATIC_ENVIRONMENT_OVERRIDES = (
    ("PYTHONHASHSEED", "0"),
    ("PYTHONDONTWRITEBYTECODE", "1"),
    ("PYTHONNOUSERSITE", "1"),
)
_CODEX_NATIVE_FEATURES = ("goals", "multi_agent")
_CODEX_REASONING_ITEM_TYPES = frozenset(("reasoning",))
_CODEX_TOOL_ITEM_TYPES = frozenset(
    (
        "command_execution",
        "dynamic_tool_call",
        "file_change",
        "image_generation",
        "mcp_tool_call",
        "todo_list",
        "web_search",
    )
)
_CODEX_SUBAGENT_ITEM_TYPES = frozenset(
    (
        "agent_tool_call",
        "collab_tool_call",
        "collaboration_tool_call",
        "subagent_tool_call",
    )
)


class CodexInvocationError(RuntimeError):
    pass


class CodexRecoverableInvocationError(CodexInvocationError):
    """A turn-local timeout or explicit provider transport interruption.

    This type is intentionally narrower than ``CodexInvocationError`` so the
    trusted host can continue an already checkpointed native session without
    classifying failures by their public, redacted message text.  Callers must
    still prove that the exact session checkpoint exists before retrying.
    """


class CodexFinalizedWithoutTerminalError(CodexInvocationError):
    """The run finalizer wrote its marker but Codex emitted no terminal event.

    The marker is only a bounded-liveness signal.  Callers must still read and
    gate the exact proposal through the normal checkpoint-bound workflow; this
    exception never represents a successful native turn.
    """


@dataclass(frozen=True)
class _TrustedRuntimePathIdentity:
    """Stable filesystem identity for one read-only runtime trust grant."""

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
class _CodexRunPolicy:
    """Exact non-secret launch policy generated for one resolved run root."""

    permission_config_arguments: tuple[str, ...]
    trusted_python_runtime_paths: tuple[_TrustedRuntimePathIdentity, ...]
    trusted_codex_runtime_paths: tuple[_TrustedRuntimePathIdentity, ...]
    environment_allowlist: tuple[str, ...]
    environment_overrides: tuple[tuple[str, str], ...]

    def environment(
        self,
        source: Optional[Mapping[str, str]] = None,
    ) -> Mapping[str, str]:
        values = dict(
            codex_subprocess_environment(
                source,
                allowlist=self.environment_allowlist,
            )
        )
        values.update(dict(self.environment_overrides))
        return values


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
        raise ContractError("Codex session state must be finite JSON") from exc


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


def _canonical_thread_id(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 64:
        raise ContractError("Codex session checkpoint thread identity is invalid")
    try:
        parsed = uuid.UUID(value)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ContractError("Codex session checkpoint thread identity is invalid") from exc
    canonical = str(parsed)
    if value != canonical:
        raise ContractError("Codex session checkpoint thread identity is invalid")
    return canonical


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _resolve_run_root(value: Path) -> Path:
    requested = Path(value)
    if not requested.is_absolute():
        raise ContractError("Codex native run root must be absolute")
    if requested.is_symlink():
        raise ContractError("Codex native run root must not be a symlink")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Codex native run root must already exist") from exc
    if not root.is_dir():
        raise ContractError("Codex native run root must be a directory")
    if requested != root:
        raise ContractError("Codex native run root must not contain symlinks")
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
        raise ContractError("Codex host state root must be absolute")
    if requested.is_symlink():
        raise ContractError("Codex host state root must not be a symlink")
    try:
        root = requested.resolve(strict=True)
    except OSError as exc:
        raise ContractError("Codex host state root must already exist") from exc
    if not root.is_dir():
        raise ContractError("Codex host state root must be a directory")
    if requested != root:
        raise ContractError("Codex host state root must not contain symlinks")
    if _is_within(root, run_root) or _is_within(run_root, root):
        raise ContractError("Codex host state root and run root must not overlap")
    if stat.S_IMODE(root.stat().st_mode) != 0o700:
        raise ContractError("Codex host state root permissions must be 0700")
    return root


def _checkpoint_path(host_state_root: Path) -> Path:
    return host_state_root / "codex-session.json"


def _write_private_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    source = _canonical_json(value) + b"\n"
    if len(source) > MAX_CODEX_SESSION_CHECKPOINT_BYTES:
        raise CodexInvocationError("Codex session checkpoint exceeded its safe size limit")
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
        # A hard link gives us an atomic create-without-overwrite operation.
        # An unexpected existing target is never replaced or trusted here.
        os.link(str(temporary), str(path), follow_symlinks=False)
        directory_descriptor = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    except FileExistsError as exc:
        raise CodexInvocationError(
            "Codex session checkpoint already exists; resume it explicitly"
        ) from exc
    except CodexInvocationError:
        raise
    except OSError as exc:
        raise CodexInvocationError("Codex session checkpoint could not be persisted") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _read_private_checkpoint(path: Path) -> Mapping[str, Any]:
    try:
        expected = path.lstat()
    except FileNotFoundError as exc:
        raise ContractError("Codex session checkpoint is missing") from exc
    if path.is_symlink() or not stat.S_ISREG(expected.st_mode):
        raise ContractError("Codex session checkpoint must be a regular private file")
    if stat.S_IMODE(expected.st_mode) != 0o600:
        raise ContractError("Codex session checkpoint permissions must be 0600")
    if not 1 <= expected.st_size <= MAX_CODEX_SESSION_CHECKPOINT_BYTES:
        raise ContractError("Codex session checkpoint size is invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ContractError("Codex session checkpoint cannot be read safely") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ContractError("Codex session checkpoint changed while opening")
        source = os.read(descriptor, MAX_CODEX_SESSION_CHECKPOINT_BYTES + 1)
        if len(source) > MAX_CODEX_SESSION_CHECKPOINT_BYTES or os.read(descriptor, 1):
            raise ContractError("Codex session checkpoint size is invalid")
        after = os.fstat(descriptor)
        if (
            after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ContractError("Codex session checkpoint changed while reading")
    finally:
        os.close(descriptor)
    try:
        payload = json.loads(source.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("Codex session checkpoint is not valid JSON") from exc
    if not isinstance(payload, dict):
        raise ContractError("Codex session checkpoint must contain one object")
    return payload


def _runtime_config_sha256(
    cli_version: str,
    model: str,
    reasoning_effort: str,
    run_policy: _CodexRunPolicy,
    *,
    include_codex_runtime_paths: bool = True,
) -> str:
    """Bind a checkpoint to the exact non-secret policy used to launch it."""

    payload = {
        "adapter": "codex-cli-native-session",
        "cli_version": cli_version,
        "event_protocol": "jsonl-turn-terminal-v2",
        "model": model,
        "reasoning_effort": reasoning_effort,
        "ignore_rules": False,
        "ignore_user_config": True,
        "native_web_search": True,
        "approval_policy": "never",
        "permission_profile": CODEX_PERMISSION_PROFILE,
        "permission_config_arguments": list(
            run_policy.permission_config_arguments
        ),
        "trusted_python_runtime_paths": [
            identity.to_dict()
            for identity in run_policy.trusted_python_runtime_paths
        ],
        "subprocess_environment": {
            # Inherited values can contain API credentials.  Bind their exact
            # admitted names, never their current secret values.
            "allowlist": list(run_policy.environment_allowlist),
            "overrides": [
                {"name": name, "value": value}
                for name, value in run_policy.environment_overrides
            ],
        },
        "native_features": list(_CODEX_NATIVE_FEATURES),
    }
    if include_codex_runtime_paths:
        payload["trusted_codex_runtime_paths"] = [
            identity.to_dict()
            for identity in run_policy.trusted_codex_runtime_paths
        ]
    return _sha256_json(payload)


def _run_policy_before_workshop_python(
    run_policy: _CodexRunPolicy,
) -> _CodexRunPolicy:
    """Return the one supported predecessor to the current runtime policy.

    The Workshop Python path was added after native sessions were already in
    use.  A checkpoint created immediately before that hardening must remain
    resumable, but no general policy downgrade is safe.  Build that exact
    predecessor from the current policy by removing one expected override and
    leaving every other permission, runtime identity, and environment entry
    unchanged.
    """

    workshop_python = (
        "WORKSHOP_PYTHON",
        str(Path(sys.executable).absolute()),
    )
    if run_policy.environment_overrides.count(workshop_python) != 1:
        raise CodexInvocationError(
            "Codex runtime policy has no unique Workshop Python binding"
        )
    return _CodexRunPolicy(
        permission_config_arguments=run_policy.permission_config_arguments,
        trusted_python_runtime_paths=run_policy.trusted_python_runtime_paths,
        trusted_codex_runtime_paths=run_policy.trusted_codex_runtime_paths,
        environment_allowlist=run_policy.environment_allowlist,
        environment_overrides=tuple(
            entry
            for entry in run_policy.environment_overrides
            if entry != workshop_python
        ),
    )


def _run_policy_before_codex_fs_helper(
    run_root: Path,
    run_policy: _CodexRunPolicy,
) -> _CodexRunPolicy:
    """Return the exact policy used before Codex's helper was trusted.

    Codex 0.145 serves native file tools through a sandboxed filesystem helper
    that re-executes the same Codex binary.  Older Workshop checkpoints did not
    bind or grant that executable.  Reconstruct only that exact predecessor so
    an existing session can resume under the hardened current policy.
    """

    if not run_policy.trusted_codex_runtime_paths:
        raise CodexInvocationError(
            "Codex runtime policy has no trusted filesystem helper"
        )
    return _CodexRunPolicy(
        permission_config_arguments=_permission_config_arguments(
            run_root,
            run_policy.trusted_python_runtime_paths,
            (),
        ),
        trusted_python_runtime_paths=run_policy.trusted_python_runtime_paths,
        trusted_codex_runtime_paths=(),
        environment_allowlist=run_policy.environment_allowlist,
        environment_overrides=run_policy.environment_overrides,
    )


def _run_policy_before_venv_launcher_directory(
    run_root: Path,
    run_policy: _CodexRunPolicy,
) -> Optional[_CodexRunPolicy]:
    """Return the exact policy from before venv launcher traversal was granted.

    A PEP 405 launcher is commonly a relative symlink inside ``bin`` (or
    ``Scripts``).  When the surrounding checkout is denied, granting only the
    launcher and its resolved base interpreter is insufficient for the Codex
    sandbox to traverse that symlink.  New policies therefore trust the real
    launcher directory read-only.  This helper reconstructs only the exact
    immediately preceding policy so already-bound native sessions can resume
    under the corrected, narrower-than-checkout grant.
    """

    executable = Path(sys.executable)
    marker = executable.parent.parent / "pyvenv.cfg"
    if not marker.is_file() or marker.is_symlink():
        return None
    launcher_directory = str(executable.parent)
    matching = tuple(
        identity
        for identity in run_policy.trusted_python_runtime_paths
        if identity.path == launcher_directory
    )
    if len(matching) != 1 or not stat.S_ISDIR(matching[0].resolved_mode):
        raise CodexInvocationError(
            "Codex runtime policy has no unique venv launcher directory"
        )
    predecessor_paths = tuple(
        identity
        for identity in run_policy.trusted_python_runtime_paths
        if identity.path != launcher_directory
    )
    return _CodexRunPolicy(
        permission_config_arguments=_permission_config_arguments(
            run_root,
            predecessor_paths,
            run_policy.trusted_codex_runtime_paths,
        ),
        trusted_python_runtime_paths=predecessor_paths,
        trusted_codex_runtime_paths=run_policy.trusted_codex_runtime_paths,
        environment_allowlist=run_policy.environment_allowlist,
        environment_overrides=run_policy.environment_overrides,
    )


def _codex_native_version_tuple(version: Any) -> Optional[tuple[int, int, int]]:
    if not isinstance(version, str):
        return None
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9.-]+)?", version)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def codex_supports_native_workshop(version: str) -> bool:
    """Return whether Codex supports Workshop goals, agents, and profiles."""

    parsed = _codex_native_version_tuple(version)
    return parsed is not None and parsed >= MINIMUM_CODEX_NATIVE_RUNTIME_VERSION


def _is_supported_in_place_cli_upgrade(previous: Any, current: Any) -> bool:
    """Allow only a monotonic supported Codex upgrade within one major line."""

    previous_tuple = _codex_native_version_tuple(previous)
    current_tuple = _codex_native_version_tuple(current)
    return bool(
        previous_tuple is not None
        and current_tuple is not None
        and previous_tuple >= MINIMUM_CODEX_NATIVE_RUNTIME_VERSION
        and current_tuple >= MINIMUM_CODEX_NATIVE_RUNTIME_VERSION
        and previous_tuple[0] == current_tuple[0]
        and current_tuple > previous_tuple
    )


def _resolved_codex_binary(binary: Optional[str]) -> Optional[str]:
    """Return the real executable path used by Codex and its helper.

    On macOS a managed Seatbelt profile can execute an explicitly readable
    regular file but still reject re-execution through a symlink.  Codex's
    sandboxed filesystem helper uses the launch-time executable path, so launch
    the root process through the canonical target and grant only that file.
    """

    if binary is None:
        return None
    candidate = Path(binary)
    if not candidate.is_absolute():
        located = shutil.which(binary)
        if located is None:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        candidate = Path(located)
    try:
        resolved = candidate.resolve(strict=True)
        target = resolved.stat()
    except OSError as exc:
        raise CodexInvocationError(
            "Codex CLI is not installed or on PATH"
        ) from exc
    if not stat.S_ISREG(target.st_mode) or (target.st_mode & 0o111) == 0:
        raise CodexInvocationError(
            "Codex runtime executable is not a regular executable file"
        )
    return str(resolved)


def _toml_string(value: str) -> str:
    """Encode one path/key as a TOML basic string."""

    return json.dumps(value, ensure_ascii=False)


def _trusted_runtime_path_identity(
    path: Path,
    *,
    label: str = "Workshop Python runtime",
) -> _TrustedRuntimePathIdentity:
    try:
        source = path.lstat()
        resolved = path.resolve(strict=True)
        target = resolved.stat()
    except OSError as exc:
        raise CodexInvocationError(
            "%s changed while its sandbox was prepared" % label
        ) from exc
    if not (
        stat.S_ISREG(source.st_mode)
        or stat.S_ISDIR(source.st_mode)
        or stat.S_ISLNK(source.st_mode)
    ) or not (stat.S_ISREG(target.st_mode) or stat.S_ISDIR(target.st_mode)):
        raise CodexInvocationError(
            "%s contains an unsafe filesystem object" % label
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
    """Return exact identities for the read-only Python runtime trust boundary.

    ``:minimal`` covers platform tools, but it cannot know about the Python
    interpreter that installed Workshop (for example a uv, conda, or pyenv
    runtime).  Product agents need that interpreter for the deterministic
    stage finalizer and for hash-bound CAD tools.  Grant the interpreter,
    virtual-environment marker, and standard library read-only.

    ``purelib`` and ``platlib`` are deliberately included as a trusted,
    read-only installed-dependency boundary because run-local deterministic
    CAD tools import their packaged Python dependencies.  Code installed in
    those trees is therefore trusted runtime code even though the surrounding
    Workshop checkout remains denied.

    A standalone interpreter build (for example uv's managed CPython) links
    the executable against a sibling ``libpython*.{dylib,so}`` that lives
    outside ``stdlib``/``platstdlib``.  Without that shared library granted
    read-only too, the sandboxed interpreter can be listed but never
    actually started: dynamic loading fails closed. Grant it by its exact
    identity, the same way as every other runtime boundary here.
    """

    executable = Path(sys.executable)
    try:
        resolved = executable.resolve(strict=True)
    except OSError as exc:
        raise CodexInvocationError(
            "Workshop Python runtime is unavailable to the Codex sandbox"
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
        # A venv launcher is commonly a chain of relative symlinks.  The
        # enclosing checkout remains denied, so the sandbox needs this one
        # trusted directory to traverse the launcher while preserving PEP 405
        # discovery and the isolated venv dependency set.
        candidates.add(executable.parent)
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
    library_dir = sysconfig.get_config_var("LIBDIR")
    library_name = sysconfig.get_config_var(
        "INSTSONAME"
    ) or sysconfig.get_config_var("LDLIBRARY")
    if (
        isinstance(library_dir, str)
        and library_dir
        and isinstance(library_name, str)
        and library_name
    ):
        shared_library = Path(library_dir) / library_name
        try:
            resolved_library = shared_library.resolve(strict=True)
        except OSError:
            resolved_library = None
        if resolved_library is not None and resolved_library.is_file():
            candidates.add(resolved_library)
    return tuple(
        _trusted_runtime_path_identity(path)
        for path in sorted(candidates, key=lambda candidate: str(candidate))
    )


def _codex_runtime_permission_identities(
    binary: str,
) -> tuple[_TrustedRuntimePathIdentity, ...]:
    """Bind the exact executable used by Codex's filesystem helper.

    Native file tools such as freeform ``apply_patch`` and ``view_image`` use
    a sandboxed filesystem service that re-executes the running Codex binary
    in a hidden helper mode.  The helper needs read/execute access to that
    already-trusted executable, never to the surrounding Codex home or package
    directory.
    """

    try:
        resolved = Path(binary).resolve(strict=True)
    except OSError as exc:
        raise CodexInvocationError(
            "Codex runtime executable is unavailable to its sandbox"
        ) from exc
    identity = _trusted_runtime_path_identity(
        resolved,
        label="Codex runtime executable",
    )
    if not stat.S_ISREG(identity.resolved_mode) or (
        identity.resolved_mode & 0o111
    ) == 0:
        raise CodexInvocationError(
            "Codex runtime executable is not a regular executable file"
        )
    return (identity,)


def _source_checkout_boundary(run_root: Path) -> Optional[Path]:
    """Find a containing checkout that must stay denied to the product run."""

    for candidate in run_root.parents:
        marker = candidate / ".git"
        if marker.exists() or marker.is_symlink():
            return candidate
    return None


def _permission_config_arguments(
    run_root: Path,
    trusted_python_runtime_paths: tuple[_TrustedRuntimePathIdentity, ...],
    trusted_codex_runtime_paths: tuple[_TrustedRuntimePathIdentity, ...],
) -> tuple[str, ...]:
    """Build one non-composable, exact-root Codex permission profile.

    Codex derives a runtime workspace from repository context.  A product
    project may intentionally live below the Workshop source checkout, so a
    ``:workspace`` grant would also make the surrounding repository writable.
    Absolute rules keep authority bound to this one already-canonical run root.
    """

    root = str(run_root)
    workspace_rules = [
        '"."="write"',
        *(
            "%s=\"read\"" % _toml_string(relative)
            for relative in _IMMUTABLE_PRODUCT_RUN_PATHS
        ),
        "%s=\"deny\"" % _toml_string("**/.env*"),
    ]
    entries = [
        '":root"="deny"',
        '":minimal"="read"',
        "glob_scan_max_depth=8",
        '":workspace_roots"={%s}' % ",".join(workspace_rules),
        "%s=\"deny\"" % _toml_string(str(run_root.parent)),
        "%s=\"write\"" % _toml_string(root),
    ]
    checkout = _source_checkout_boundary(run_root)
    if checkout is not None:
        entries.append("%s=\"deny\"" % _toml_string(str(checkout)))
    trusted_runtime_paths = sorted(
        {
            identity.path
            for identity in (
                *trusted_python_runtime_paths,
                *trusted_codex_runtime_paths,
            )
        }
    )
    entries.extend(
        "%s=\"read\"" % _toml_string(path)
        for path in trusted_runtime_paths
    )
    entries.extend(
        "%s=\"read\"" % _toml_string(str(run_root / relative))
        for relative in _IMMUTABLE_PRODUCT_RUN_PATHS
    )
    entries.append(
        "%s=\"deny\"" % _toml_string(str(run_root / "**/.env*"))
    )
    values = (
        'default_permissions="%s"' % CODEX_PERMISSION_PROFILE,
        'permissions.%s.description="Isolated Autonomous Workshop product run"'
        % CODEX_PERMISSION_PROFILE,
        "permissions.%s.workspace_roots={%s=true}"
        % (CODEX_PERMISSION_PROFILE, _toml_string(root)),
        "permissions.%s.filesystem={%s}"
        % (CODEX_PERMISSION_PROFILE, ",".join(entries)),
        'permissions.%s.network.enabled=false' % CODEX_PERMISSION_PROFILE,
        'project_root_markers=["%s"]' % PRODUCT_RUN_ROOT_MARKER,
    )
    arguments: list[str] = []
    for value in values:
        arguments.extend(("--config", value))
    return tuple(arguments)


def _codex_run_policy(run_root: Path, binary: str) -> _CodexRunPolicy:
    """Generate once the exact sandbox/environment policy used by a turn."""

    trusted_python_paths = _python_runtime_permission_identities()
    trusted_codex_paths = _codex_runtime_permission_identities(binary)
    private_temp = str(run_root / ".tmp")
    overrides = (
        ("TMPDIR", private_temp),
        ("TMP", private_temp),
        ("TEMP", private_temp),
        ("WORKSHOP_PYTHON", str(Path(sys.executable).absolute())),
        *_CODEX_RUN_STATIC_ENVIRONMENT_OVERRIDES,
    )
    return _CodexRunPolicy(
        permission_config_arguments=_permission_config_arguments(
            run_root,
            trusted_python_paths,
            trusted_codex_paths,
        ),
        trusted_python_runtime_paths=trusted_python_paths,
        trusted_codex_runtime_paths=trusted_codex_paths,
        environment_allowlist=tuple(CODEX_SUBPROCESS_ENVIRONMENT_ALLOWLIST),
        environment_overrides=overrides,
    )


def _private_run_temp(run_root: Path) -> Path:
    """Return a real 0700 temp directory contained by the exact run root."""

    path = run_root / ".tmp"
    try:
        path.mkdir(mode=0o700)
    except FileExistsError:
        pass
    except OSError as exc:
        raise CodexInvocationError(
            "Codex product-run temp directory could not be created"
        ) from exc
    try:
        identity = path.lstat()
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise CodexInvocationError(
            "Codex product-run temp directory is unavailable"
        ) from exc
    if (
        path.is_symlink()
        or not stat.S_ISDIR(identity.st_mode)
        or resolved != path
        or stat.S_IMODE(identity.st_mode) != 0o700
    ):
        raise CodexInvocationError(
            "Codex product-run temp directory must be a real 0700 directory"
        )
    return path


def _codex_run_environment(
    run_root: Path,
    run_policy: _CodexRunPolicy,
) -> Mapping[str, str]:
    private_temp = str(_private_run_temp(run_root))
    overrides = dict(run_policy.environment_overrides)
    if any(
        overrides.get(name) != private_temp
        for name in ("TMPDIR", "TMP", "TEMP")
    ) or overrides.get("WORKSHOP_PYTHON") != str(
        Path(sys.executable).absolute()
    ):
        raise CodexInvocationError(
            "Codex product-run environment does not match its bound policy"
        )
    return run_policy.environment()


@dataclass(frozen=True)
class CodexNativeSessionBinding:
    """Redacted identity for one Wish-wide native Codex session."""

    product_id: str
    wish_sha256: str
    constitution_sha256: str
    run_root_sha256: str
    host_state_root_sha256: str
    runtime_config_sha256: str
    checkpoint_sha256: str
    schema_version: int = 1
    kind: str = CODEX_SESSION_CHECKPOINT_KIND

    def __post_init__(self) -> None:
        if self.schema_version != 1 or self.kind != CODEX_SESSION_CHECKPOINT_KIND:
            raise ContractError("Codex native session binding version is invalid")
        _bounded_identifier(self.product_id, "Codex native session product_id")
        for value, label in (
            (self.wish_sha256, "Codex native session Wish sha256"),
            (
                self.constitution_sha256,
                "Codex native session constitution sha256",
            ),
            (self.run_root_sha256, "Codex native session run-root sha256"),
            (
                self.host_state_root_sha256,
                "Codex native session host-state-root sha256",
            ),
            (
                self.runtime_config_sha256,
                "Codex native session runtime-config sha256",
            ),
            (
                self.checkpoint_sha256,
                "Codex native session checkpoint sha256",
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
class CodexNativeSessionOutcome:
    """Compact public outcome; messages, events, and the UUID stay private."""

    binding: CodexNativeSessionBinding
    used_web_search: bool
    status: str = "completed"
    token_count: Optional[int] = None

    def __post_init__(self) -> None:
        if not isinstance(self.binding, CodexNativeSessionBinding):
            raise ContractError("Codex native session outcome requires a binding")
        if self.status != "completed":
            raise ContractError("Codex native session outcome status is invalid")
        if type(self.used_web_search) is not bool:
            raise ContractError("Codex native session search status must be boolean")
        if self.token_count is not None and (
            type(self.token_count) is not int
            or not 0 <= self.token_count <= 2_000_000_000_000
        ):
            raise ContractError("Codex native session token count is invalid")

    def to_dict(self) -> Mapping[str, Any]:
        value = {
            "status": self.status,
            "session": self.binding.to_dict(),
            "used_web_search": self.used_web_search,
        }
        if self.token_count is not None:
            value["token_count"] = self.token_count
        return value


def _validate_agent_message(value: Any) -> str:
    if not isinstance(value, str):
        raise ContractError("Codex native session message must be text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractError("Codex native session message must be UTF-8") from exc
    if size > MAX_CODEX_MESSAGE_BYTES or "\x00" in value:
        raise ContractError("Codex native session message exceeded its safe limit")
    return value


def _validated_prompt(value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ContractError("Codex native session prompt must be bounded text")
    try:
        size = len(value.encode("utf-8"))
    except UnicodeError as exc:
        raise ContractError("Codex native session prompt must be UTF-8") from exc
    if size > MAX_CODEX_PROMPT_BYTES:
        raise ContractError("Codex native session prompt exceeded its safe limit")
    return value


def _validated_activity_observer(
    value: Optional[Callable[[str], None]],
) -> Optional[Callable[[str], None]]:
    if value is not None and not callable(value):
        raise ContractError("Codex native activity observer must be callable")
    return value


def _validated_finalization_marker(
    value: Optional[Path],
    run_root: Path,
) -> Optional[Path]:
    """Bind liveness monitoring to the one exact run-local proposal path."""

    if value is None:
        return None
    try:
        marker = Path(value)
    except TypeError as exc:
        raise ContractError(
            "Codex finalization marker must be the exact in-run "
            "agent-outcome.json path"
        ) from exc
    expected = run_root / "agent-outcome.json"
    if not marker.is_absolute() or marker != expected:
        raise ContractError(
            "Codex finalization marker must be the exact in-run "
            "agent-outcome.json path"
        )
    return marker


def _observe_safe_activity(
    observer: Optional[Callable[[str], None]], activity: str
) -> None:
    """Send one host-selected class; observer failures never alter a turn."""

    if activity not in SAFE_NATIVE_ACTIVITY_CLASSES:
        raise AssertionError("unsafe native activity class")
    if observer is None:
        return
    try:
        observer(activity)
    except Exception:
        # Progress is non-authoritative telemetry. A full disk, concurrent
        # status race, or broken callback cannot waive or block the event
        # stream's existing security and terminal requirements.
        return


class _NativeActivityReporter:
    """Deliver bounded coarse activity without blocking the native launcher."""

    def __init__(
        self,
        observer: Optional[Callable[[str], None]],
        process: Any,
    ) -> None:
        self._observer = observer
        self._process = process
        self._stop = threading.Event()
        self._condition = threading.Condition()
        self._terminal_activity: Optional[str] = None
        self._pending: list[tuple[int, str]] = []
        self._next_generation = 0
        self._delivered_generation = 0
        self._delivery_available = False
        self._closed = False
        self._delivery_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None

    def start(self) -> None:
        if self._observer is None:
            return
        delivery_thread = threading.Thread(
            target=self._deliver,
            name="workshop-codex-activity-delivery",
            daemon=True,
        )
        with self._condition:
            self._delivery_available = True
        try:
            delivery_thread.start()
        except (OSError, RuntimeError):
            with self._condition:
                self._delivery_available = False
                self._condition.notify_all()
            return
        self._delivery_thread = delivery_thread

        heartbeat_thread = threading.Thread(
            target=self._heartbeat,
            name="workshop-codex-activity-heartbeat",
            daemon=True,
        )
        try:
            heartbeat_thread.start()
        except (OSError, RuntimeError):
            # Telemetry must not affect the native turn if this host cannot
            # create the optional heartbeat thread.
            return
        self._heartbeat_thread = heartbeat_thread

    def observe(self, activity: str) -> None:
        if activity not in SAFE_NATIVE_ACTIVITY_CLASSES:
            raise AssertionError("unsafe native activity class")
        terminal = activity in ("completed", "failed")
        with self._condition:
            if not self._delivery_available:
                return
            if terminal:
                self._terminal_activity = activity
                self._stop.set()
            elif self._terminal_activity is not None:
                return
            self._next_generation += 1
            generation = self._next_generation
            if len(self._pending) >= _MAX_PENDING_ACTIVITY_CLASSES:
                if terminal:
                    # Terminal state has precedence over queued active noise.
                    self._pending.clear()
                else:
                    # Coalesce an overloaded active stream to its latest safe
                    # class without allowing unbounded telemetry memory.
                    self._pending[-1] = (generation, activity)
                    self._condition.notify()
                    return
            self._pending.append((generation, activity))
            self._condition.notify()
            if not terminal:
                return

            # Healthy local sinks normally complete before this returns, which
            # preserves deterministic status/tests. A stuck sink is abandoned
            # after a fixed bound and can never delay the native turn.
            deadline = (
                time.monotonic() + _CODEX_ACTIVITY_DELIVERY_TIMEOUT_SECONDS
            )
            while (
                self._delivery_available
                and self._delivered_generation < generation
            ):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return
                self._condition.wait(timeout=remaining)

    def stop(self) -> None:
        self._stop.set()

    def close(self) -> None:
        """Stop new delivery without waiting for observer-owned code."""

        self._stop.set()
        with self._condition:
            self._closed = True
            self._condition.notify_all()

    def _heartbeat(self) -> None:
        interval = max(0.001, _CODEX_ACTIVITY_HEARTBEAT_SECONDS)
        while not self._stop.wait(interval):
            try:
                running = self._process.poll() is None
            except Exception:
                # If liveness cannot be confirmed, emit nothing. This is
                # optional telemetry and cannot become lifecycle authority.
                continue
            if not running:
                return
            self.observe("running")

    def _deliver(self) -> None:
        """Serialize observer callbacks entirely on a disposable daemon."""

        while True:
            with self._condition:
                while not self._pending:
                    if self._closed:
                        self._delivery_available = False
                        self._condition.notify_all()
                        return
                    self._condition.wait()
                generation, activity = self._pending.pop(0)
            # No observer-owned code runs on the launcher thread or while the
            # reporter condition is held. A permanently stalled sink strands
            # only this daemon; queued terminal state remains final by order.
            _observe_safe_activity(self._observer, activity)
            with self._condition:
                self._delivered_generation = max(
                    self._delivered_generation,
                    generation,
                )
                self._condition.notify_all()


@dataclass(frozen=True)
class _ProcessSessionIdentity:
    """PID-reuse-resistant identity for one dedicated POSIX session."""

    session_id: int
    leader_create_time: float

    def __post_init__(self) -> None:
        if (
            type(self.session_id) is not int
            or self.session_id <= 1
            or not isinstance(self.leader_create_time, (int, float))
            or isinstance(self.leader_create_time, bool)
            or not math.isfinite(float(self.leader_create_time))
            or self.leader_create_time <= 0
        ):
            raise ValueError("invalid process session identity")


class _NativeProcessGuard:
    """Own one launched Codex process session until it is proven quiescent.

    The launcher may be unwound by ``KeyboardInterrupt`` or ``SystemExit``,
    neither of which is an ``Exception``.  Keep cleanup outside the event
    parser's ordinary failure classification and make it idempotent because
    timeout, stderr, and launcher threads can all discover termination at the
    same time.
    """

    def __init__(
        self,
        process: Any,
        process_group_id: Optional[int],
        process_session_identity: Optional[_ProcessSessionIdentity],
    ) -> None:
        self.process = process
        self.process_group_id = process_group_id
        self.process_session_identity = process_session_identity
        self._lock = threading.Lock()
        self._reaped = False

    def reap(self) -> bool:
        with self._lock:
            if self._reaped:
                return True
            reaped = _terminate_safely(
                self.process,
                process_group_id=self.process_group_id,
                process_session_identity=self.process_session_identity,
            )
            if reaped:
                self._reaped = True
            return reaped


def _close_process_streams(process: Any) -> None:
    """Close every host-owned pipe after the dedicated session is reaped."""

    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(process, name, None)
        close = getattr(stream, "close", None)
        if callable(close):
            try:
                close()
            except (OSError, ValueError):
                pass


class _FinalizationMarkerWatch:
    """Bound a newly created proposal marker to bounded process cleanup.

    The marker never proves a successful turn.  It only prevents a Codex
    process whose public JSONL stream remains open after finalization from
    occupying the launcher until the one-hour turn timeout.
    """

    def __init__(
        self,
        path: Optional[Path],
        process_guard: _NativeProcessGuard,
        deadline: float,
    ) -> None:
        self.path = path
        self.process_guard = process_guard
        self.deadline = deadline
        self._state_lock = threading.Lock()
        self._stop = threading.Event()
        self._turn_completed = threading.Event()
        self._resolved = threading.Event()
        self._triggered = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._armed = False
        if path is None:
            return
        try:
            path.lstat()
        except FileNotFoundError:
            self._armed = True
        except OSError as exc:
            raise CodexInvocationError(
                "Codex finalization marker could not be monitored safely"
            ) from exc
        # Any path that already exists is stale for this launch.  It is never
        # used as a liveness signal, regardless of its filesystem type.

    @property
    def triggered(self) -> bool:
        return self._triggered.is_set()

    def start(self) -> None:
        if not self._armed:
            return
        thread = threading.Thread(
            target=self._watch,
            name="workshop-codex-finalization-marker",
            daemon=True,
        )
        try:
            thread.start()
        except (OSError, RuntimeError):
            # Monitoring is a bounded-liveness aid, never a lifecycle gate.
            return
        self._thread = thread

    def observe_turn_completed(self) -> None:
        with self._state_lock:
            self._turn_completed.set()

    def wait_after_stream_end(self) -> None:
        """Let a newly observed regular marker finish its grace period."""

        if self._thread is None or self._turn_completed.is_set():
            return
        identity = self._regular_identity()
        if identity is None:
            return
        wait_seconds = max(
            0.0,
            min(
                (
                    _CODEX_FINALIZATION_MARKER_GRACE_SECONDS
                    + _CODEX_FINALIZATION_MARKER_POLL_SECONDS
                    + 0.1
                ),
                self.deadline - time.monotonic(),
            ),
        )
        if not self._resolved.wait(timeout=wait_seconds):
            self._expire_marker(identity)

    def close(self) -> None:
        self._stop.set()
        self.observe_turn_completed()
        thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=0.25)

    def _regular_identity(self) -> Optional[tuple[int, int]]:
        if self.path is None:
            return None
        try:
            identity = self.path.lstat()
        except OSError:
            return None
        if not stat.S_ISREG(identity.st_mode):
            return None
        return identity.st_dev, identity.st_ino

    def _watch(self) -> None:
        identity: Optional[tuple[int, int]] = None
        while not self._stop.is_set() and not self._turn_completed.is_set():
            if self.path is None:
                return
            try:
                current = self.path.lstat()
            except FileNotFoundError:
                self._stop.wait(_CODEX_FINALIZATION_MARKER_POLL_SECONDS)
                continue
            except OSError:
                return
            if not stat.S_ISREG(current.st_mode):
                # A directory, device, FIFO, or symlink is not the finalizer's
                # regular run-local marker and can never select this path.
                return
            identity = current.st_dev, current.st_ino
            break
        if identity is None:
            return

        deadline = min(
            time.monotonic() + _CODEX_FINALIZATION_MARKER_GRACE_SECONDS,
            self.deadline,
        )
        while not self._stop.is_set():
            if self._turn_completed.is_set():
                return
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            self._stop.wait(
                min(_CODEX_FINALIZATION_MARKER_POLL_SECONDS, remaining)
            )
        if self._stop.is_set() or self._turn_completed.is_set():
            return
        self._expire_marker(identity)

    def _expire_marker(self, identity: tuple[int, int]) -> None:
        if self._regular_identity() != identity:
            self._resolved.set()
            return
        with self._state_lock:
            if self._resolved.is_set():
                return
            if self._stop.is_set() or self._turn_completed.is_set():
                self._resolved.set()
                return
            try:
                if self.process_guard.reap():
                    self._triggered.set()
            finally:
                self._resolved.set()


def _safe_activity_for_event(event: Mapping[str, Any]) -> Optional[str]:
    """Classify a decoded event without forwarding any event-owned bytes."""

    event_type = event.get("type")
    if event_type in ("turn.failed", "error"):
        return "failed"
    if event_type == "turn.completed":
        return "completed"
    if event_type == "thread.started":
        return "starting"
    if event_type == "turn.started":
        return "reasoning"
    if event_type not in ("item.started", "item.updated", "item.completed"):
        return None
    item = event.get("item")
    if not isinstance(item, Mapping):
        return None
    item_type = item.get("type")
    if not isinstance(item_type, str):
        return None
    if item_type in _CODEX_SUBAGENT_ITEM_TYPES:
        return "subagent"
    if item_type in _CODEX_REASONING_ITEM_TYPES:
        return "reasoning"
    if item_type in _CODEX_TOOL_ITEM_TYPES:
        return "tool"
    if item_type == "agent_message" and event_type == "item.completed":
        return "finalizing"
    return None


class CodexNativeSessionLauncher:
    """Launch or resume the one native Codex session for an entire Wish."""

    manager_id = "codex"
    session_checkpoint_name = "codex-session.json"

    def __init__(
        self,
        *,
        model: str = "gpt-5.6-sol",
        reasoning_effort: str = "high",
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS,
        popen_factory: Any = subprocess.Popen,
        version_runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
    ) -> None:
        if model not in ALLOWED_WORKSHOP_MODELS:
            raise ContractError(
                "Workshop Codex model must be gpt-5.6-sol, gpt-5.6-terra, "
                "or gpt-5.6-luna"
            )
        if reasoning_effort not in ("low", "medium", "high", "xhigh"):
            raise ValueError("unsupported Codex reasoning effort")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3_600:
            raise ValueError("Codex timeout_seconds must be from 1 to 3,600")
        self.binary = _resolved_codex_binary(
            binary or os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
        )
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self._popen_factory = popen_factory
        self._version_runner = version_runner
        self.cli_version = cli_version or self._read_cli_version()
        if self.binary and not codex_supports_native_workshop(self.cli_version):
            minimum = ".".join(
                str(part) for part in MINIMUM_CODEX_NATIVE_RUNTIME_VERSION
            )
            raise CodexInvocationError(
                "Workshop requires Codex CLI %s or newer for native goals, "
                "subagents, and credential-isolated permission profiles" % minimum
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
                env=codex_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return "0.0.0"
        output = completed.stdout if isinstance(completed.stdout, str) else ""
        match = re.search(r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.-]+)?", output)
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
        activity_observer: Optional[Callable[[str], None]] = None,
        finalization_marker: Optional[Path] = None,
    ) -> CodexNativeSessionOutcome:
        root, state_root, path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        if path.exists() or path.is_symlink():
            raise ContractError(
                "Codex native session checkpoint already exists; resume it explicitly"
            )
        prompt = _validated_prompt(prompt)
        activity_observer = _validated_activity_observer(activity_observer)
        finalization_marker = _validated_finalization_marker(
            finalization_marker,
            root,
        )
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        run_policy = _codex_run_policy(root, self.binary)
        runtime_config_sha256 = _runtime_config_sha256(
            self.cli_version,
            self.model,
            self.reasoning_effort,
            run_policy,
        )
        persisted_sha256: Optional[str] = None

        def bind_thread(thread_id: str) -> None:
            nonlocal persisted_sha256
            if persisted_sha256 is not None:
                raise CodexInvocationError(
                    "Codex returned an ambiguous native session identity"
                )
            identity = self._checkpoint_identity(
                product_id=product_id,
                wish_sha256=wish_sha256,
                constitution_sha256=constitution_sha256,
                run_root=root,
                host_state_root=state_root,
                thread_id=thread_id,
                runtime_config_sha256=runtime_config_sha256,
            )
            persisted_sha256 = _sha256_json(identity)
            _write_private_checkpoint(
                path,
                {**identity, "checkpoint_sha256": persisted_sha256},
            )

        used_web_search, observed_thread_id, token_count = self._stream(
            command=self._start_command(root, run_policy),
            prompt=prompt,
            run_root=root,
            run_policy=run_policy,
            expected_thread_id=None,
            bind_thread=bind_thread,
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
        )
        if observed_thread_id is None or persisted_sha256 is None:
            raise CodexInvocationError(
                "Codex native session returned no valid session identity"
            )
        return CodexNativeSessionOutcome(
            self._public_binding(
                product_id=product_id,
                wish_sha256=wish_sha256,
                constitution_sha256=constitution_sha256,
                run_root=root,
                host_state_root=state_root,
                runtime_config_sha256=runtime_config_sha256,
                checkpoint_sha256=persisted_sha256,
            ),
            used_web_search,
            token_count=token_count,
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
        activity_observer: Optional[Callable[[str], None]] = None,
        finalization_marker: Optional[Path] = None,
    ) -> CodexNativeSessionOutcome:
        root, state_root, path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        prompt = _validated_prompt(prompt)
        activity_observer = _validated_activity_observer(activity_observer)
        finalization_marker = _validated_finalization_marker(
            finalization_marker,
            root,
        )
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        run_policy = _codex_run_policy(root, self.binary)
        runtime_config_sha256 = _runtime_config_sha256(
            self.cli_version,
            self.model,
            self.reasoning_effort,
            run_policy,
        )
        policy_before_venv_directory = (
            _run_policy_before_venv_launcher_directory(root, run_policy)
        )
        historical_policy = (
            run_policy
            if policy_before_venv_directory is None
            else policy_before_venv_directory
        )
        policy_before_codex_helper = _run_policy_before_codex_fs_helper(
            root,
            historical_policy,
        )
        predecessor_policies: list[tuple[_CodexRunPolicy, bool]] = [
            (
                _run_policy_before_workshop_python(historical_policy),
                True,
            ),
            (policy_before_codex_helper, False),
            (
                _run_policy_before_workshop_python(
                    policy_before_codex_helper
                ),
                False,
            )
        ]
        if policy_before_venv_directory is not None:
            predecessor_policies.insert(
                0,
                (policy_before_venv_directory, True),
            )
        predecessor_runtime_config_sha256s = tuple(
            dict.fromkeys(
                _runtime_config_sha256(
                    self.cli_version,
                    self.model,
                    self.reasoning_effort,
                    policy,
                    include_codex_runtime_paths=include_codex_runtime_paths,
                )
                for policy, include_codex_runtime_paths in predecessor_policies
            )
        )
        thread_id, checkpoint_sha256 = self._load_checkpoint(
            path=path,
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
            runtime_config_sha256=runtime_config_sha256,
            predecessor_runtime_config_sha256s=predecessor_runtime_config_sha256s,
        )
        used_web_search, unused_observed_thread_id, token_count = self._stream(
            command=self._resume_command(thread_id, root, run_policy),
            prompt=prompt,
            run_root=root,
            run_policy=run_policy,
            expected_thread_id=thread_id,
            bind_thread=None,
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
        )
        return CodexNativeSessionOutcome(
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
            token_count=token_count,
        )

    def _binding_paths(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
    ) -> tuple[Path, Path, Path]:
        _bounded_identifier(product_id, "Codex native session product_id")
        _require_sha256(wish_sha256, "Codex native session Wish sha256")
        _require_sha256(
            constitution_sha256, "Codex native session constitution sha256"
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
        thread_id: str,
        runtime_config_sha256: str,
    ) -> Mapping[str, Any]:
        return {
            "schema_version": 1,
            "kind": CODEX_SESSION_CHECKPOINT_KIND,
            "product_id": product_id,
            "wish_sha256": wish_sha256,
            "constitution_sha256": constitution_sha256,
            "run_root_sha256": _path_sha256(run_root),
            "host_state_root_sha256": _path_sha256(host_state_root),
            "runtime_config_sha256": _require_sha256(
                runtime_config_sha256,
                "Codex native session runtime-config sha256",
            ),
            "cli_version": self.cli_version,
            "permission_profile": CODEX_PERMISSION_PROFILE,
            "native_web_search": True,
            "thread_id": _canonical_thread_id(thread_id),
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
        predecessor_runtime_config_sha256s: tuple[str, ...],
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
            "permission_profile",
            "native_web_search",
            "thread_id",
            "checkpoint_sha256",
        }
        if set(payload) != expected_fields:
            raise ContractError("Codex native session checkpoint fields are invalid")
        try:
            thread_id = _canonical_thread_id(payload["thread_id"])
            checkpoint_sha256 = _require_sha256(
                payload["checkpoint_sha256"],
                "Codex native session checkpoint sha256",
            )
        except ContractError as exc:
            raise ContractError(
                "Codex native session checkpoint binding is invalid"
            ) from exc
        identity = {
            key: payload[key] for key in expected_fields - {"checkpoint_sha256"}
        }
        if checkpoint_sha256 != _sha256_json(identity):
            raise ContractError(
                "Codex native session checkpoint binding is invalid"
            )
        expected = self._checkpoint_identity(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
            thread_id=thread_id,
            runtime_config_sha256=runtime_config_sha256,
        )
        predecessors = tuple(
            {
                **expected,
                "runtime_config_sha256": _require_sha256(
                    predecessor_runtime_config_sha256,
                    "Codex predecessor runtime-config sha256",
                ),
            }
            for predecessor_runtime_config_sha256 in (
                predecessor_runtime_config_sha256s
            )
        )
        if identity != expected and identity not in predecessors:
            # A package manager may atomically replace the installed Codex CLI
            # while one native turn is running. The session checkpoint lives in
            # the host-private 0700 state tree, is itself hash-bound, and still
            # has to match every Wish, constitution, path, permission-profile,
            # feature, and thread field below. Permit only a monotonic supported
            # upgrade within the same major line. Same-version policy drift,
            # downgrades, major migrations, and arbitrary checkpoint changes
            # continue to fail closed. The resumed process runs under the newly
            # recomputed current sandbox policy.
            static_fields = expected_fields - {
                "checkpoint_sha256",
                "cli_version",
                "runtime_config_sha256",
            }
            try:
                _require_sha256(
                    identity["runtime_config_sha256"],
                    "Codex native session runtime-config sha256",
                )
            except ContractError as exc:
                raise ContractError(
                    "Codex native session checkpoint binding is invalid"
                ) from exc
            if not (
                all(identity[key] == expected[key] for key in static_fields)
                and _is_supported_in_place_cli_upgrade(
                    identity["cli_version"], expected["cli_version"]
                )
            ):
                raise ContractError(
                    "Codex native session checkpoint binding is invalid"
                )
        return thread_id, checkpoint_sha256

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
    ) -> CodexNativeSessionBinding:
        return CodexNativeSessionBinding(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root_sha256=_path_sha256(run_root),
            host_state_root_sha256=_path_sha256(host_state_root),
            runtime_config_sha256=runtime_config_sha256,
            checkpoint_sha256=checkpoint_sha256,
        )

    def _start_command(
        self,
        run_root: Path,
        run_policy: _CodexRunPolicy,
    ) -> list[str]:
        return [
            self.binary,
            "--search",
            "--enable",
            "goals",
            "--enable",
            "multi_agent",
            "--ask-for-approval",
            "never",
            "exec",
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--strict-config",
            "--color",
            "never",
            "--json",
            "--config",
            'model_reasoning_effort="%s"' % self.reasoning_effort,
            *run_policy.permission_config_arguments,
            "-C",
            str(run_root),
            "--model",
            self.model,
            "-",
        ]

    def _resume_command(
        self,
        thread_id: str,
        run_root: Path,
        run_policy: _CodexRunPolicy,
    ) -> list[str]:
        return [
            self.binary,
            "--search",
            "--enable",
            "goals",
            "--enable",
            "multi_agent",
            "--ask-for-approval",
            "never",
            "-C",
            str(run_root),
            "exec",
            "resume",
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--strict-config",
            "--json",
            "--config",
            'model_reasoning_effort="%s"' % self.reasoning_effort,
            *run_policy.permission_config_arguments,
            "--model",
            self.model,
            thread_id,
            "-",
        ]

    def _stream(
        self,
        *,
        command: list[str],
        prompt: str,
        run_root: Path,
        run_policy: _CodexRunPolicy,
        expected_thread_id: Optional[str],
        bind_thread: Any,
        activity_observer: Optional[Callable[[str], None]],
        finalization_marker: Optional[Path] = None,
        _process_guard: Optional[_NativeProcessGuard] = None,
        _finalization_watch: Optional[_FinalizationMarkerWatch] = None,
        _deadline: Optional[float] = None,
    ) -> tuple[bool, Optional[str], Optional[int]]:
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        deadline = (
            _deadline
            if _deadline is not None
            else time.monotonic() + self.timeout_seconds
        )
        if _process_guard is None:
            try:
                process = self._popen_factory(
                    command,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding="utf-8",
                    errors="strict",
                    bufsize=1,
                    cwd=str(run_root),
                    env=_codex_run_environment(run_root, run_policy),
                    start_new_session=True,
                )
            except (OSError, subprocess.SubprocessError, TypeError, ValueError):
                raise CodexInvocationError(
                    "Codex native session could not be launched"
                ) from None
            process_group_id = _dedicated_process_group_id(process)
            process_session_identity = _dedicated_process_session_identity(
                process
            )
            supervised_members = (
                _process_session_members(process_session_identity)
                if process_session_identity is not None
                else None
            )
            if isinstance(process, subprocess.Popen) and (
                process_group_id is None
                or process_session_identity is None
                or supervised_members is None
                or process.pid not in {
                    member.pid for member in supervised_members
                }
            ):
                _terminate_safely(process)
                raise CodexInvocationError(
                    "Codex native session could not establish process supervision"
                )
            process_guard = _NativeProcessGuard(
                process,
                process_group_id,
                process_session_identity,
            )
            finalization_watch: Optional[_FinalizationMarkerWatch] = None
            try:
                finalization_watch = _FinalizationMarkerWatch(
                    finalization_marker,
                    process_guard,
                    deadline,
                )
                finalization_watch.start()
                return self._stream(
                    command=command,
                    prompt=prompt,
                    run_root=run_root,
                    run_policy=run_policy,
                    expected_thread_id=expected_thread_id,
                    bind_thread=bind_thread,
                    activity_observer=activity_observer,
                    finalization_marker=finalization_marker,
                    _process_guard=process_guard,
                    _finalization_watch=finalization_watch,
                    _deadline=deadline,
                )
            finally:
                # This is deliberately outside every ``Exception`` classifier.
                # Graceful host exits must never strand the dedicated Codex
                # process session, while a successfully completed turn still
                # follows the normal terminal-event and checkpoint path below.
                if finalization_watch is not None:
                    finalization_watch.close()
                process_guard.reap()
                _close_process_streams(process_guard.process)

        process_guard = _process_guard
        finalization_watch = _finalization_watch
        process = process_guard.process
        if process.stdin is None or process.stdout is None or process.stderr is None:
            process_guard.reap()
            raise CodexInvocationError(
                "Codex native session streams are unavailable"
            )
        activity_reporter = _NativeActivityReporter(
            activity_observer,
            process,
        )
        activity_reporter.start()
        activity_reporter.observe("starting")

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
                    if stderr_size > MAX_CODEX_STDERR_BYTES:
                        stderr_overflow.set()
                        process_guard.reap()
                        return
            except (OSError, ValueError, UnicodeError):
                stderr_overflow.set()

        stderr_thread = threading.Thread(
            target=drain_stderr,
            name="workshop-codex-stderr",
            daemon=True,
        )
        stderr_thread.start()

        timed_out = threading.Event()

        def expire() -> None:
            timed_out.set()
            process_guard.reap()

        timer = threading.Timer(max(0.001, deadline - time.monotonic()), expire)
        timer.daemon = True
        timer.start()

        used_web_search = False
        observed_thread_id: Optional[str] = None
        token_count: Optional[int] = None
        turn_completed = False
        stream_failure: Optional[BaseException] = None
        try:
            try:
                process.stdin.write(prompt)
                process.stdin.flush()
                process.stdin.close()
            except (BrokenPipeError, OSError, ValueError):
                raise CodexInvocationError(
                    "Codex native session could not receive its prompt"
                ) from None

            for text in _bounded_native_event_lines(process.stdout):
                event = _decode_native_event(text)
                event_type = event.get("type")
                activity = _safe_activity_for_event(event)
                if activity is not None:
                    activity_reporter.observe(activity)
                if event_type in ("turn.failed", "error"):
                    if _is_explicit_transient_event_failure(event):
                        raise CodexRecoverableInvocationError(
                            "Codex native provider transport was interrupted"
                        )
                    raise CodexInvocationError(
                        "Codex native session reported a failed turn"
                    )
                if event_type == "thread.started":
                    if observed_thread_id is not None:
                        raise CodexInvocationError(
                            "Codex returned an ambiguous native session identity"
                        )
                    try:
                        observed_thread_id = _canonical_thread_id(
                            event.get("thread_id")
                        )
                    except ContractError:
                        raise CodexInvocationError(
                            "Codex returned an invalid native session identity"
                        ) from None
                    if (
                        expected_thread_id is not None
                        and observed_thread_id != expected_thread_id
                    ):
                        raise CodexInvocationError(
                            "Codex resumed a different native session"
                        )
                    if bind_thread is not None:
                        bind_thread(observed_thread_id)
                item = event.get("item")
                if (
                    event_type
                    in ("item.started", "item.updated", "item.completed")
                    and isinstance(item, Mapping)
                    and item.get("type") == "web_search"
                ):
                    used_web_search = True
                if (
                    event_type == "item.completed"
                    and isinstance(item, Mapping)
                    and item.get("type") == "agent_message"
                ):
                    _validate_agent_message(item.get("text"))
                if event_type == "turn.completed":
                    token_count = _native_token_count(event.get("usage"))
                    turn_completed = True
                    if finalization_watch is not None:
                        finalization_watch.observe_turn_completed()
                    break
        except Exception as exc:
            stream_failure = exc
            activity_reporter.observe("failed")
            process_guard.reap()
        finally:
            timer.cancel()

        if (
            not turn_completed
            and stream_failure is None
            and not timed_out.is_set()
            and finalization_watch is not None
        ):
            finalization_watch.wait_after_stream_end()

        remaining = deadline - time.monotonic()
        intentionally_terminated = False
        if turn_completed and stream_failure is None and not timed_out.is_set():
            try:
                returncode = process.wait(
                    timeout=max(
                        0.001,
                        min(_CODEX_TERMINAL_EXIT_GRACE_SECONDS, remaining),
                    )
                )
            except subprocess.TimeoutExpired:
                # ``turn.completed`` is the documented JSONL success boundary.
                # Some Codex clients can retain background goal resources after
                # emitting it, so give the process a brief chance to exit and
                # then reap it without waiting for stdout EOF indefinitely.
                intentionally_terminated = True
                process_guard.reap()
                returncode = getattr(process, "returncode", None)
            except (OSError, ValueError):
                process_guard.reap()
                returncode = getattr(process, "returncode", None)
                stream_failure = CodexInvocationError(
                    "Codex native session could not be reaped"
                )
        else:
            try:
                returncode = process.wait(timeout=max(0.001, remaining))
            except (subprocess.TimeoutExpired, OSError, ValueError):
                timed_out.set()
                process_guard.reap()
                returncode = getattr(process, "returncode", None)
        stderr_thread.join(timeout=max(0.0, min(1.0, deadline - time.monotonic())))
        activity_reporter.stop()
        process_tree_reaped = process_guard.reap()

        if timed_out.is_set():
            activity_reporter.observe("failed")
            activity_reporter.close()
            stderr_thread.join(timeout=_CODEX_ACTIVITY_DELIVERY_TIMEOUT_SECONDS)
            if stderr_thread.is_alive() or stderr_overflow.is_set():
                raise CodexInvocationError(
                    "Codex native diagnostic stream exceeded its safe size limit"
                )
            if stream_failure is not None:
                if isinstance(stream_failure, (CodexInvocationError, ContractError)):
                    raise stream_failure from None
                raise CodexInvocationError(
                    "Codex native session event stream was invalid"
                ) from None
            if not process_tree_reaped:
                raise CodexInvocationError(
                    "Codex native session could not be terminated safely"
                )
            raise CodexRecoverableInvocationError(
                "Codex native session timed out"
            )
        if stderr_thread.is_alive() or stderr_overflow.is_set():
            activity_reporter.observe("failed")
            activity_reporter.close()
            raise CodexInvocationError(
                "Codex native diagnostic stream exceeded its safe limit"
            )
        if not process_tree_reaped:
            activity_reporter.observe("failed")
            activity_reporter.close()
            raise CodexInvocationError(
                "Codex native session could not be terminated safely"
            )
        if stream_failure is not None:
            activity_reporter.close()
            if isinstance(stream_failure, (CodexInvocationError, ContractError)):
                raise stream_failure from None
            raise CodexInvocationError(
                "Codex native session event stream was invalid"
            ) from None
        if finalization_watch is not None and finalization_watch.triggered:
            activity_reporter.observe("failed")
            activity_reporter.close()
            raise CodexFinalizedWithoutTerminalError(
                "Codex native session finalized without a terminal event"
            )
        if intentionally_terminated and returncode is None:
            activity_reporter.observe("failed")
            activity_reporter.close()
            raise CodexInvocationError(
                "Codex native session could not be terminated safely"
            )
        if not turn_completed or (
            returncode != 0 and not intentionally_terminated
        ):
            # Diagnostics are intentionally used only for a safe category and
            # are never attached to the public exception.
            if (
                stderr_size <= _MAX_TRANSIENT_DIAGNOSTIC_CHARS
                and _is_explicit_transient_failure(stderr_tail)
            ):
                activity_reporter.observe("failed")
                activity_reporter.close()
                raise CodexRecoverableInvocationError(
                    "Codex native provider transport was interrupted"
                )
            activity_reporter.observe("failed")
            activity_reporter.close()
            raise CodexInvocationError("Codex native session did not complete")
        if expected_thread_id is None and observed_thread_id is None:
            activity_reporter.observe("failed")
            activity_reporter.close()
            raise CodexInvocationError(
                "Codex native session returned no valid session identity"
            )
        activity_reporter.close()
        return used_web_search, observed_thread_id, token_count


def _stream_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8")
        except UnicodeError:
            raise CodexInvocationError(
                "Codex native session event stream was invalid"
            ) from None
    raise CodexInvocationError("Codex native session event stream was invalid")


def _native_event_bytes(raw: Any) -> int:
    if isinstance(raw, bytes):
        return len(raw)
    if isinstance(raw, str):
        try:
            return len(raw.encode("utf-8"))
        except UnicodeError:
            raise CodexInvocationError(
                "Codex native session event stream was invalid"
            ) from None
    raise CodexInvocationError("Codex native session event stream was invalid")


def _ends_native_event_line(raw: Any) -> bool:
    return raw.endswith(b"\n") if isinstance(raw, bytes) else raw.endswith("\n")


def _bounded_native_event_lines(stream: Any) -> Iterator[str]:
    """Yield JSONL records with constant memory per discarded event.

    The Codex event channel is a stream, not an evidence buffer.  A long native
    turn can therefore safely exceed ``MAX_CODEX_EVENT_BYTES`` in aggregate as
    long as each independently decoded record stays within that hard bound.
    ``readline(size)`` is important here: ordinary file iteration may allocate
    an attacker-sized line before the caller gets a chance to measure it.

    A record beyond the bound — in practice a tool result that echoed a large
    file such as the packed ``VAULT.json`` — is drained in bounded chunks and
    discarded rather than ending the session: Codex already holds that output
    in its own context, and the host reads stage outcomes from the run root,
    never from the event channel.

    Deterministic stream doubles used by embedders may expose only iteration;
    retain that narrow compatibility path while applying the same per-record
    byte check after every yielded value.
    """

    readline = getattr(stream, "readline", None)
    if callable(readline):

        def read_chunk() -> Any:
            try:
                # Text streams bound characters rather than encoded bytes.
                # UTF-8 uses at most four bytes per character, so this still
                # gives a small fixed allocation ceiling; the exact byte bound
                # below remains authoritative.
                return readline(MAX_CODEX_EVENT_BYTES + 1)
            except (OSError, ValueError, UnicodeError):
                raise CodexInvocationError(
                    "Codex native session event stream was invalid"
                ) from None

        while True:
            raw = read_chunk()
            if raw in ("", b""):
                return
            if not _ends_native_event_line(raw):
                # Either the stream ended without a trailing newline or the
                # record continues past the chunk and is oversized.
                following = read_chunk()
                if following in ("", b""):
                    if _native_event_bytes(raw) <= MAX_CODEX_EVENT_BYTES:
                        yield _stream_text(raw)
                    return
                while not _ends_native_event_line(following):
                    following = read_chunk()
                    if following in ("", b""):
                        return
                continue
            if _native_event_bytes(raw) > MAX_CODEX_EVENT_BYTES:
                continue
            yield _stream_text(raw)
        return

    try:
        iterator = iter(stream)
    except TypeError:
        raise CodexInvocationError(
            "Codex native session event stream was invalid"
        ) from None
    for raw in iterator:
        if _native_event_bytes(raw) > MAX_CODEX_EVENT_BYTES:
            continue
        yield _stream_text(raw)


def _decode_native_event(line: str) -> Mapping[str, Any]:
    if not line.strip():
        raise CodexInvocationError("Codex native session event stream was invalid")
    try:
        event = json.loads(line)
    except (TypeError, ValueError):
        raise CodexInvocationError(
            "Codex native session event stream was invalid"
        ) from None
    if not isinstance(event, Mapping):
        raise CodexInvocationError("Codex native session event stream was invalid")
    return event


def _native_token_count(value: Any) -> Optional[int]:
    """Return input plus output for one completed turn, or unavailable."""

    if not isinstance(value, Mapping):
        return None
    input_tokens = value.get("input_tokens")
    output_tokens = value.get("output_tokens")
    if any(
        type(count) is not int or not 0 <= count <= 1_000_000_000_000
        for count in (input_tokens, output_tokens)
    ):
        return None
    return input_tokens + output_tokens


def _dedicated_process_group_id(process: Any) -> Optional[int]:
    """Return a safe dedicated group id established by ``start_new_session``."""

    process_id = getattr(process, "pid", None)
    if (
        type(process_id) is not int
        or process_id <= 1
        or not hasattr(os, "getpgid")
        or not hasattr(os, "killpg")
    ):
        return None
    try:
        process_group_id = os.getpgid(process_id)
        if process_group_id != process_id or process_group_id == os.getpgrp():
            return None
    except (AttributeError, OSError):
        return None
    return process_group_id


def _psutil_api() -> Optional[Any]:
    """Load the declared supervisor dependency with its required API surface."""

    try:
        psutil = importlib.import_module("psutil")
    except ImportError:
        return None
    error_type = getattr(psutil, "Error", None)
    no_such_process_type = getattr(psutil, "NoSuchProcess", None)
    if (
        not isinstance(error_type, type)
        or not issubclass(error_type, BaseException)
        or not isinstance(no_such_process_type, type)
        or not issubclass(no_such_process_type, error_type)
        or not callable(getattr(psutil, "Process", None))
        or not callable(getattr(psutil, "process_iter", None))
    ):
        return None
    return psutil


def _dedicated_process_session_identity(
    process: Any,
) -> Optional[_ProcessSessionIdentity]:
    """Return the isolated, creation-time-bound session for a real launcher."""

    process_id = getattr(process, "pid", None)
    if (
        type(process_id) is not int
        or process_id <= 1
        or not hasattr(os, "getsid")
    ):
        return None
    try:
        process_session_id = os.getsid(process_id)
        host_session_id = os.getsid(0)
    except (AttributeError, OSError):
        return None
    if process_session_id != process_id or process_session_id == host_session_id:
        return None
    psutil = _psutil_api()
    if psutil is None:
        return None
    try:
        create_time = psutil.Process(process_id).create_time()
        return _ProcessSessionIdentity(process_session_id, create_time)
    except (OSError, ValueError, psutil.Error):
        return None


def _process_session_members(
    process_session_identity: Optional[_ProcessSessionIdentity],
) -> Optional[tuple[Any, ...]]:
    """Return identity-pinned members of one exact POSIX process session.

    Codex's built-in ``codex-code-mode-host`` creates its own process group but
    remains in the root CLI's dedicated session.  Enumerating the session is
    therefore the portable boundary available on supported POSIX hosts.  A
    missing dependency, denied process-table read, or ambiguous identity fails
    closed instead of pretending that the CLI's group proves quiescence.
    """

    if (
        not isinstance(process_session_identity, _ProcessSessionIdentity)
        or not hasattr(os, "getsid")
    ):
        return None
    psutil = _psutil_api()
    if psutil is None:
        return None
    process_session_id = process_session_identity.session_id
    try:
        candidates = tuple(psutil.process_iter(attrs=("pid",)))
    except (OSError, RuntimeError, psutil.Error):
        return None
    members: list[Any] = []
    for candidate in candidates:
        process_id = candidate.info.get("pid")
        if type(process_id) is not int:
            return None
        # PID 0 has special "current process" meaning for ``getsid`` and PID 1
        # can never belong to this newly created unprivileged session.
        if process_id <= 1:
            continue
        try:
            candidate_session_id = os.getsid(process_id)
        except ProcessLookupError:
            continue
        except PermissionError:
            # An unprivileged Workshop process cannot create descendants under
            # another account or attach an unrelated process to its session.
            # System-owned processes that hide their SID are therefore outside
            # this exact same-user launch boundary.
            continue
        except OSError:
            return None
        if candidate_session_id != process_session_id:
            continue
        try:
            # Force psutil to bind future signals to this PID's creation
            # identity rather than to the numeric PID alone.
            create_time = candidate.create_time()
        except psutil.NoSuchProcess:
            continue
        except psutil.Error:
            return None
        if (
            process_id == process_session_id
            and create_time != process_session_identity.leader_create_time
        ):
            # The numeric SID was recycled for another leader after the
            # original session ended. Never signal the replacement session.
            return None
        members.append(candidate)
    return tuple(sorted(members, key=lambda member: member.pid))


def _signal_process_session(
    process_session_identity: _ProcessSessionIdentity,
    signal_number: int,
) -> Optional[int]:
    """Signal every still-bound member and return the observed member count."""

    members = _process_session_members(process_session_identity)
    if members is None:
        return None
    psutil = _psutil_api()
    if psutil is None:
        return None
    process_session_id = process_session_identity.session_id
    signaled = 0
    for member in members:
        try:
            if os.getsid(member.pid) != process_session_id:
                continue
            member.send_signal(signal_number)
            signaled += 1
        except (ProcessLookupError, psutil.NoSuchProcess):
            continue
        except (OSError, psutil.Error):
            return None
    return signaled


def _signal_process_group(process_group_id: int, signal_number: int) -> bool:
    try:
        os.killpg(process_group_id, signal_number)
        return True
    except ProcessLookupError:
        return True
    except (OSError, ValueError):
        return False


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
        return True
    except ProcessLookupError:
        return False
    except (OSError, ValueError):
        # Permission or an invalid platform response cannot prove quiescence.
        return True


def _wait_for_process(process: Any, timeout: float) -> bool:
    try:
        process.wait(timeout=timeout)
        return True
    except (AttributeError, OSError, ValueError, subprocess.SubprocessError):
        return False


def _terminate_safely(
    process: Any,
    *,
    process_group_id: Optional[int] = None,
    process_session_identity: Optional[_ProcessSessionIdentity] = None,
) -> bool:
    """Reap the launcher and prove its dedicated process session is empty."""

    if process_session_identity is not None:
        process_session_id = process_session_identity.session_id
        if (
            process_session_id != process_group_id
            or not hasattr(os, "getsid")
        ):
            return False
        try:
            if process_session_id == os.getsid(0):
                return False
        except (AttributeError, OSError):
            return False
        if (
            _signal_process_session(
                process_session_identity,
                signal.SIGTERM,
            )
            is None
        ):
            return False
        parent_reaped = _wait_for_process(process, 0.5)
        members = _process_session_members(process_session_identity)
        if members is None:
            return False
        if members:
            if (
                _signal_process_session(
                    process_session_identity,
                    signal.SIGKILL,
                )
                is None
            ):
                return False
            if not parent_reaped:
                parent_reaped = _wait_for_process(process, 0.5)
        deadline = time.monotonic() + 0.5
        while True:
            members = _process_session_members(process_session_identity)
            if members is None:
                return False
            if not members:
                return parent_reaped
            if time.monotonic() >= deadline:
                return False
            if (
                _signal_process_session(
                    process_session_identity,
                    signal.SIGKILL,
                )
                is None
            ):
                return False
            time.sleep(0.01)

    if process_group_id is not None:
        if (
            type(process_group_id) is not int
            or process_group_id <= 1
            or not hasattr(os, "killpg")
        ):
            return False
        try:
            if process_group_id == os.getpgrp():
                return False
        except (AttributeError, OSError):
            return False
        if not _signal_process_group(process_group_id, signal.SIGTERM):
            return False
        parent_reaped = _wait_for_process(process, 0.5)
        if _process_group_exists(process_group_id):
            if not _signal_process_group(process_group_id, signal.SIGKILL):
                return False
            if not parent_reaped:
                parent_reaped = _wait_for_process(process, 0.5)
        deadline = time.monotonic() + 0.5
        while _process_group_exists(process_group_id):
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.01)
        return parent_reaped

    # Injected deterministic process doubles have no OS group. Production
    # ``Popen`` objects are rejected before this fallback if group creation
    # cannot be proved.
    try:
        running = process.poll() is None
    except (AttributeError, OSError, subprocess.SubprocessError):
        running = True
    if not running:
        return True
    try:
        process.terminate()
    except (AttributeError, OSError, subprocess.SubprocessError):
        pass
    if _wait_for_process(process, 0.5):
        return True
    try:
        process.kill()
    except (AttributeError, OSError, subprocess.SubprocessError):
        pass
    return _wait_for_process(process, 0.5)


def _diagnostic_tail(value: str) -> str:
    return value[-_MAX_TRANSIENT_DIAGNOSTIC_CHARS:].casefold()


def _has_explicit_transient_head(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if len(value) > _MAX_NATIVE_FAILURE_MESSAGE_CHARS:
        return False
    message = value.strip().casefold()
    return any(
        message == head or message.startswith(f"{head}: ")
        for head in _TRANSIENT_DIAGNOSTIC_HEADS
    )


def _is_explicit_transient_event_failure(event: Mapping[str, Any]) -> bool:
    """Recognize only Codex-owned, anchored transport failure payloads.

    The JSONL schema puts a failed turn's diagnostic at ``error.message`` and
    an unrecoverable stream diagnostic at top-level ``message``. The bytes are
    used only to select this narrow typed category and are never persisted or
    attached to the public exception.
    """

    event_type = event.get("type")
    if event_type == "turn.failed":
        error = event.get("error")
        if not isinstance(error, Mapping):
            return False
        return _has_explicit_transient_head(error.get("message"))
    if event_type == "error":
        return _has_explicit_transient_head(event.get("message"))
    return False


def _is_explicit_transient_failure(stderr: str) -> bool:
    # Require an anchored, adapter-recognized diagnostic line: generic OS
    # errors such as ``temporarily unavailable`` are deliberately not
    # transport evidence and fail closed.
    for raw_line in _diagnostic_tail(stderr).splitlines():
        line = raw_line.strip()
        head, separator, detail = line.partition(": ")
        if head not in _TRANSIENT_DIAGNOSTIC_HEADS:
            continue
        if not separator or 1 <= len(detail) <= 512:
            return True
    return False


__all__ = [
    "ALLOWED_WORKSHOP_MODELS",
    "CODEX_PERMISSION_PROFILE",
    "CODEX_SESSION_CHECKPOINT_KIND",
    "DEFAULT_CODEX_TIMEOUT_SECONDS",
    "MAX_CODEX_EVENT_BYTES",
    "MAX_CODEX_MESSAGE_BYTES",
    "MAX_CODEX_PROMPT_BYTES",
    "MAX_CODEX_SESSION_CHECKPOINT_BYTES",
    "MAX_CODEX_STDERR_BYTES",
    "MINIMUM_CODEX_NATIVE_RUNTIME_VERSION",
    "CodexFinalizedWithoutTerminalError",
    "CodexInvocationError",
    "CodexRecoverableInvocationError",
    "CodexNativeSessionBinding",
    "CodexNativeSessionLauncher",
    "CodexNativeSessionOutcome",
    "codex_supports_native_workshop",
]
