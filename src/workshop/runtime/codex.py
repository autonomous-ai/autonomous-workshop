"""One whole-run native Codex session launcher."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop.errors import ContractError
from workshop.runtime.execution import codex_subprocess_environment
from workshop.runtime.project_boundary import PRODUCT_RUN_ROOT_MARKER


ALLOWED_WORKSHOP_MODELS = frozenset(
    ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")
)
CODEX_PERMISSION_PROFILE = "workshop-product-run"
MINIMUM_CODEX_NATIVE_RUNTIME_VERSION = (0, 145, 0)
DEFAULT_CODEX_TIMEOUT_SECONDS = 1_200
MAX_CODEX_EVENT_BYTES = 1 * 1024 * 1024
MAX_CODEX_PROMPT_BYTES = 1 * 1024 * 1024
MAX_CODEX_MESSAGE_BYTES = 64 * 1024
MAX_CODEX_STDERR_BYTES = 256 * 1024
MAX_CODEX_SESSION_CHECKPOINT_BYTES = 32 * 1024
CODEX_SESSION_CHECKPOINT_KIND = "autonomous-workshop-native-codex-session"
_MAX_TRANSIENT_DIAGNOSTIC_CHARS = 64 * 1024
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

_IMMUTABLE_PRODUCT_RUN_PATHS = (
    ".agents",
    ".codex",
    PRODUCT_RUN_ROOT_MARKER,
    "AGENTS.md",
    "STAGE.json",
    "WISH.json",
)
_CODEX_PERMISSION_CONFIG_TEMPLATE = (
    'default_permissions="%s"' % CODEX_PERMISSION_PROFILE,
    'permissions.%s.description="Isolated Autonomous Workshop product run"'
    % CODEX_PERMISSION_PROFILE,
    "filesystem: deny root, read minimal runtime, write <exact-run-root>, "
    "read immutable product inputs, deny <exact-run-root>/**/.env*",
    'permissions.%s.network.enabled=false' % CODEX_PERMISSION_PROFILE,
    'project_root_markers=["%s"]' % PRODUCT_RUN_ROOT_MARKER,
)
_CODEX_NATIVE_FEATURES = ("goals", "multi_agent")


class CodexInvocationError(RuntimeError):
    pass


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
    cli_version: str, model: str, reasoning_effort: str
) -> str:
    return _sha256_json(
        {
            "adapter": "codex-cli-native-session",
            "cli_version": cli_version,
            "event_protocol": "jsonl-thread-started-v1",
            "model": model,
            "reasoning_effort": reasoning_effort,
            "ignore_rules": False,
            "ignore_user_config": True,
            "native_web_search": True,
            "approval_policy": "never",
            "permission_profile": CODEX_PERMISSION_PROFILE,
            "permission_profile_config_template": list(
                _CODEX_PERMISSION_CONFIG_TEMPLATE
            ),
            "permission_profile_scope": "exact-run-root-v1",
            "native_features": list(_CODEX_NATIVE_FEATURES),
        }
    )


def codex_supports_native_workshop(version: str) -> bool:
    """Return whether Codex supports Workshop goals, agents, and profiles."""

    if not isinstance(version, str):
        return False
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9.-]+)?", version)
    if match is None:
        return False
    return tuple(int(part) for part in match.groups()) >= (
        MINIMUM_CODEX_NATIVE_RUNTIME_VERSION
    )


def _toml_string(value: str) -> str:
    """Encode one path/key as a TOML basic string."""

    return json.dumps(value, ensure_ascii=False)


def _permission_config_arguments(run_root: Path) -> list[str]:
    """Build one non-composable, exact-root Codex permission profile.

    Codex derives a runtime workspace from repository context.  A product
    project may intentionally live below the Workshop source checkout, so a
    ``:workspace`` grant would also make the surrounding repository writable.
    Absolute rules keep authority bound to this one already-canonical run root.
    """

    root = str(run_root)
    entries = [
        '":root"="deny"',
        '":minimal"="read"',
        "glob_scan_max_depth=8",
        "%s=\"write\"" % _toml_string(root),
    ]
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
        "permissions.%s.filesystem={%s}"
        % (CODEX_PERMISSION_PROFILE, ",".join(entries)),
        'permissions.%s.network.enabled=false' % CODEX_PERMISSION_PROFILE,
        'project_root_markers=["%s"]' % PRODUCT_RUN_ROOT_MARKER,
    )
    arguments: list[str] = []
    for value in values:
        arguments.extend(("--config", value))
    return arguments


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


def _codex_run_environment(run_root: Path) -> Mapping[str, str]:
    environment = dict(codex_subprocess_environment())
    private_temp = str(_private_run_temp(run_root))
    environment.update(
        {"TMPDIR": private_temp, "TMP": private_temp, "TEMP": private_temp}
    )
    return environment


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

    def __post_init__(self) -> None:
        if not isinstance(self.binding, CodexNativeSessionBinding):
            raise ContractError("Codex native session outcome requires a binding")
        if self.status != "completed":
            raise ContractError("Codex native session outcome status is invalid")
        if type(self.used_web_search) is not bool:
            raise ContractError("Codex native session search status must be boolean")

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "status": self.status,
            "session": self.binding.to_dict(),
            "used_web_search": self.used_web_search,
        }


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


class CodexNativeSessionLauncher:
    """Launch or resume the one native Codex session for an entire Wish."""

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
        self.binary = (
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
        self.runtime_config_sha256 = _runtime_config_sha256(
            self.cli_version, self.model, self.reasoning_effort
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
            )
            persisted_sha256 = _sha256_json(identity)
            _write_private_checkpoint(
                path,
                {**identity, "checkpoint_sha256": persisted_sha256},
            )

        used_web_search, observed_thread_id = self._stream(
            command=self._start_command(root),
            prompt=prompt,
            run_root=root,
            expected_thread_id=None,
            bind_thread=bind_thread,
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
                checkpoint_sha256=persisted_sha256,
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
    ) -> CodexNativeSessionOutcome:
        root, state_root, path = self._binding_paths(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
        )
        prompt = _validated_prompt(prompt)
        thread_id, checkpoint_sha256 = self._load_checkpoint(
            path=path,
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=root,
            host_state_root=state_root,
        )
        used_web_search, unused_observed_thread_id = self._stream(
            command=self._resume_command(thread_id, root),
            prompt=prompt,
            run_root=root,
            expected_thread_id=thread_id,
            bind_thread=None,
        )
        return CodexNativeSessionOutcome(
            self._public_binding(
                product_id=product_id,
                wish_sha256=wish_sha256,
                constitution_sha256=constitution_sha256,
                run_root=root,
                host_state_root=state_root,
                checkpoint_sha256=checkpoint_sha256,
            ),
            used_web_search,
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
    ) -> Mapping[str, Any]:
        return {
            "schema_version": 1,
            "kind": CODEX_SESSION_CHECKPOINT_KIND,
            "product_id": product_id,
            "wish_sha256": wish_sha256,
            "constitution_sha256": constitution_sha256,
            "run_root_sha256": _path_sha256(run_root),
            "host_state_root_sha256": _path_sha256(host_state_root),
            "runtime_config_sha256": self.runtime_config_sha256,
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
        expected = self._checkpoint_identity(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=run_root,
            host_state_root=host_state_root,
            thread_id=thread_id,
        )
        if (
            identity != expected
            or checkpoint_sha256 != _sha256_json(identity)
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
        checkpoint_sha256: str,
    ) -> CodexNativeSessionBinding:
        return CodexNativeSessionBinding(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root_sha256=_path_sha256(run_root),
            host_state_root_sha256=_path_sha256(host_state_root),
            runtime_config_sha256=self.runtime_config_sha256,
            checkpoint_sha256=checkpoint_sha256,
        )

    def _start_command(self, run_root: Path) -> list[str]:
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
            *_permission_config_arguments(run_root),
            "-C",
            str(run_root),
            "--model",
            self.model,
            "-",
        ]

    def _resume_command(self, thread_id: str, run_root: Path) -> list[str]:
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
            *_permission_config_arguments(run_root),
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
        expected_thread_id: Optional[str],
        bind_thread: Any,
    ) -> tuple[bool, Optional[str]]:
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        deadline = time.monotonic() + self.timeout_seconds
        try:
            process = self._popen_factory(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(run_root),
                env=_codex_run_environment(run_root),
            )
        except (OSError, subprocess.SubprocessError, TypeError, ValueError):
            raise CodexInvocationError(
                "Codex native session could not be launched"
            ) from None
        if process.stdin is None or process.stdout is None or process.stderr is None:
            _terminate_safely(process)
            raise CodexInvocationError(
                "Codex native session streams are unavailable"
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
                    if stderr_size > MAX_CODEX_STDERR_BYTES:
                        stderr_overflow.set()
                        _terminate_safely(process)
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
            _terminate_safely(process)

        timer = threading.Timer(max(0.001, deadline - time.monotonic()), expire)
        timer.daemon = True
        timer.start()

        stdout_size = 0
        stdout_tail = ""
        used_web_search = False
        observed_thread_id: Optional[str] = None
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

            for raw in process.stdout:
                text = _stream_text(raw)
                stdout_size += len(text.encode("utf-8", errors="replace"))
                stdout_tail = (stdout_tail + text)[
                    -_MAX_TRANSIENT_DIAGNOSTIC_CHARS:
                ]
                if stdout_size > MAX_CODEX_EVENT_BYTES:
                    raise CodexInvocationError(
                        "Codex native event stream exceeded its safe size limit"
                    )
                event = _decode_native_event(text)
                event_type = event.get("type")
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
        except Exception as exc:
            stream_failure = exc
            _terminate_safely(process)
        finally:
            timer.cancel()

        remaining = deadline - time.monotonic()
        try:
            returncode = process.wait(timeout=max(0.001, remaining))
        except (subprocess.TimeoutExpired, OSError, ValueError):
            timed_out.set()
            _terminate_safely(process)
            returncode = getattr(process, "returncode", None)
        stderr_thread.join(timeout=max(0.0, min(1.0, deadline - time.monotonic())))

        if timed_out.is_set():
            raise CodexInvocationError("Codex native session timed out")
        if stderr_thread.is_alive() or stderr_overflow.is_set():
            _terminate_safely(process)
            raise CodexInvocationError(
                "Codex native diagnostic stream exceeded its safe limit"
            )
        if stream_failure is not None:
            if isinstance(stream_failure, (CodexInvocationError, ContractError)):
                raise stream_failure from None
            raise CodexInvocationError(
                "Codex native session event stream was invalid"
            ) from None
        if returncode != 0:
            # Diagnostics are intentionally used only for a safe category and
            # are never attached to the public exception.
            if _is_explicit_transient_failure(stdout_tail, stderr_tail):
                raise CodexInvocationError(
                    "Codex native provider transport was interrupted"
                )
            raise CodexInvocationError("Codex native session did not complete")
        if expected_thread_id is None and observed_thread_id is None:
            raise CodexInvocationError(
                "Codex native session returned no valid session identity"
            )
        return used_web_search, observed_thread_id


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


def _terminate_safely(process: Any) -> None:
    try:
        running = process.poll() is None
    except (AttributeError, OSError, subprocess.SubprocessError):
        running = True
    if running:
        try:
            process.terminate()
        except (AttributeError, OSError, subprocess.SubprocessError):
            pass
    try:
        process.wait(timeout=0.5)
        return
    except (AttributeError, OSError, ValueError, subprocess.SubprocessError):
        pass
    try:
        process.kill()
    except (AttributeError, OSError, subprocess.SubprocessError):
        pass
    try:
        process.wait(timeout=0.5)
    except (AttributeError, OSError, ValueError, subprocess.SubprocessError):
        pass


def _diagnostic_tail(value: str) -> str:
    return value[-_MAX_TRANSIENT_DIAGNOSTIC_CHARS:].casefold()


def _is_explicit_transient_failure(stdout: str, stderr: str) -> bool:
    diagnostic = _diagnostic_tail(stdout) + "\n" + _diagnostic_tail(stderr)
    return any(marker in diagnostic for marker in _TRANSIENT_DIAGNOSTIC_MARKERS)


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
    "CodexInvocationError",
    "CodexNativeSessionBinding",
    "CodexNativeSessionLauncher",
    "CodexNativeSessionOutcome",
    "codex_supports_native_workshop",
]
