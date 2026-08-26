"""Safe structured calls and one whole-run native Codex session launcher."""

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


ALLOWED_WORKSHOP_MODELS = frozenset(("gpt-5.6-terra", "gpt-5.6-luna"))
DEFAULT_CODEX_TIMEOUT_SECONDS = 1_200
MAX_CODEX_EVENT_BYTES = 1 * 1024 * 1024
MAX_CODEX_OUTPUT_BYTES = 1 * 1024 * 1024
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
            "sandbox": "workspace-write",
        }
    )


class CodexStructuredRunner:
    def __init__(
        self,
        *,
        model: str,
        reasoning_effort: str,
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS,
        runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
    ) -> None:
        if model not in ALLOWED_WORKSHOP_MODELS:
            raise ContractError(
                "Workshop Codex model must be gpt-5.6-terra or gpt-5.6-luna"
            )
        if reasoning_effort not in ("low", "medium", "high", "xhigh"):
            raise ValueError("unsupported Codex reasoning effort")
        if (
            type(timeout_seconds) is not int
            or not 1 <= timeout_seconds <= 3_600
        ):
            raise ValueError("Codex timeout_seconds must be from 1 to 3,600")
        self.binary = binary or os.environ.get("WORKSHOP_CODEX_BIN") or shutil.which("codex")
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self._runner = runner
        self.cli_version = cli_version or self._read_cli_version()
        self.last_used_web_search = False

    def _read_cli_version(self) -> str:
        if not self.binary:
            return "0.0.0"
        try:
            completed = self._runner(
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

    def invoke(
        self,
        *,
        prompt: str,
        schema: Mapping[str, Any],
        workspace: Optional[Path] = None,
        native_web_search: bool = False,
    ) -> Mapping[str, Any]:
        if not self.binary:
            raise CodexInvocationError("Codex CLI is not installed or on PATH")
        if type(native_web_search) is not bool:
            raise ValueError("native_web_search must be a boolean")

        self.last_used_web_search = False
        deadline = time.monotonic() + self.timeout_seconds
        for attempt in range(2):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CodexInvocationError("Codex structured call timed out")
            try:
                completed, output_bytes = self._run_attempt(
                    prompt=prompt,
                    schema=schema,
                    workspace=workspace,
                    native_web_search=native_web_search,
                    timeout_seconds=remaining,
                )
            except subprocess.TimeoutExpired as exc:
                exc.output = None
                exc.stderr = None
                raise CodexInvocationError("Codex structured call timed out") from None
            except (OSError, subprocess.SubprocessError, TypeError, ValueError) as exc:
                for attribute in ("output", "stdout", "stderr"):
                    if hasattr(exc, attribute):
                        setattr(exc, attribute, None)
                raise CodexInvocationError(
                    "Codex could not execute the structured call"
                ) from None

            stdout = completed.stdout if isinstance(completed.stdout, str) else ""
            stderr = completed.stderr if isinstance(completed.stderr, str) else ""
            if completed.returncode != 0:
                if attempt == 0 and _is_explicit_transient_failure(stdout, stderr):
                    continue
                if _is_explicit_transient_failure(stdout, stderr):
                    raise CodexInvocationError(
                        "Codex provider transport failed after one retry"
                    )
                raise CodexInvocationError("Codex did not complete the structured call")

            used_web_search = _jsonl_used_web_search(stdout)
            if native_web_search and not used_web_search:
                raise CodexInvocationError(
                    "Codex native web research completed without a web search event"
                )
            payload = _decode_bounded_payload(output_bytes)
            self.last_used_web_search = used_web_search
            return payload

        raise CodexInvocationError("Codex did not complete the structured call")

    def _run_attempt(
        self,
        *,
        prompt: str,
        schema: Mapping[str, Any],
        workspace: Optional[Path],
        native_web_search: bool,
        timeout_seconds: float,
    ):
        with tempfile.TemporaryDirectory(prefix="workshop-codex-") as temporary:
            control_root = Path(temporary)
            schema_path = control_root / "output.schema.json"
            output_path = control_root / "output.json"
            schema_path.write_text(json.dumps(schema, sort_keys=True), encoding="utf-8")
            cwd = Path(workspace).resolve() if workspace is not None else control_root
            cwd.mkdir(parents=True, exist_ok=True)
            command = [self.binary]
            if native_web_search:
                command.append("--search")
            command.extend(
                [
                    "exec",
                    "--ephemeral",
                    "--ignore-rules",
                    "--ignore-user-config",
                    "--skip-git-repo-check",
                    "--sandbox",
                    "read-only",
                    "--color",
                    "never",
                    "--json",
                    "--config",
                    'model_reasoning_effort="%s"' % self.reasoning_effort,
                    "--output-schema",
                    str(schema_path),
                    "--output-last-message",
                    str(output_path),
                    "-C",
                    str(cwd),
                    "--model",
                    self.model,
                    "-",
                ]
            )
            completed = self._runner(
                command,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                env=codex_subprocess_environment(),
            )
            output_bytes = None
            if output_path.is_file():
                size = output_path.stat().st_size
                if size > MAX_CODEX_OUTPUT_BYTES:
                    raise CodexInvocationError(
                        "Codex structured result exceeded the safe size limit"
                    )
                output_bytes = output_path.read_bytes()
                if len(output_bytes) > MAX_CODEX_OUTPUT_BYTES:
                    raise CodexInvocationError(
                        "Codex structured result exceeded the safe size limit"
                    )
            return completed, output_bytes


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
        model: str = "gpt-5.6-terra",
        reasoning_effort: str = "high",
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CODEX_TIMEOUT_SECONDS,
        popen_factory: Any = subprocess.Popen,
        version_runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
    ) -> None:
        if model not in ALLOWED_WORKSHOP_MODELS:
            raise ContractError(
                "Workshop Codex model must be gpt-5.6-terra or gpt-5.6-luna"
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
            "sandbox": "workspace-write",
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
            "sandbox",
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
            "exec",
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--color",
            "never",
            "--json",
            "--config",
            'model_reasoning_effort="%s"' % self.reasoning_effort,
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
            "--sandbox",
            "workspace-write",
            "-C",
            str(run_root),
            "exec",
            "resume",
            "--ignore-user-config",
            "--skip-git-repo-check",
            "--json",
            "--config",
            'model_reasoning_effort="%s"' % self.reasoning_effort,
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
                env=codex_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError, TypeError, ValueError):
            raise CodexInvocationError(
                "Codex native session could not be launched"
            ) from None
        try:
            if process.stdin is None or process.stdout is None or process.stderr is None:
                raise CodexInvocationError(
                    "Codex native session streams are unavailable"
                )
            return self._consume_native_stream(
                process=process,
                prompt=prompt,
                deadline=deadline,
                expected_thread_id=expected_thread_id,
                bind_thread=bind_thread,
            )
        finally:
            # Popen's pipe objects are owned by this adapter.  Closing only stdin
            # after sending the prompt leaves stdout/stderr descriptors alive until
            # garbage collection, which is both a ResourceWarning and a real leak
            # for long-running Workshop hosts.  Reap first so the diagnostic thread
            # reaches EOF, then close every stream on every success/failure path.
            _terminate_safely(process)
            _close_process_streams(process)

    def _consume_native_stream(
        self,
        *,
        process: Any,
        prompt: str,
        deadline: float,
        expected_thread_id: Optional[str],
        bind_thread: Any,
    ) -> tuple[bool, Optional[str]]:
        """Consume one already-launched process; ``_stream`` owns its cleanup."""

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


def _close_process_streams(process: Any) -> None:
    """Close Popen pipes without allowing cleanup errors to mask the outcome."""

    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(process, name, None)
        if stream is None:
            continue
        try:
            stream.close()
        except (AttributeError, OSError, ValueError):
            pass


def _diagnostic_tail(value: str) -> str:
    return value[-_MAX_TRANSIENT_DIAGNOSTIC_CHARS:].casefold()


def _is_explicit_transient_failure(stdout: str, stderr: str) -> bool:
    diagnostic = _diagnostic_tail(stdout) + "\n" + _diagnostic_tail(stderr)
    return any(marker in diagnostic for marker in _TRANSIENT_DIAGNOSTIC_MARKERS)


def _jsonl_used_web_search(stdout: str) -> bool:
    if len(stdout.encode("utf-8", errors="replace")) > MAX_CODEX_EVENT_BYTES:
        raise CodexInvocationError("Codex event stream exceeded the safe size limit")
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            continue
        if (
            isinstance(event, Mapping)
            and event.get("type") in ("item.started", "item.updated", "item.completed")
            and isinstance(event.get("item"), Mapping)
            and event["item"].get("type") == "web_search"
        ):
            return True
    return False


def _decode_bounded_payload(encoded: Optional[bytes]) -> Mapping[str, Any]:
    if encoded is None:
        raise CodexInvocationError("Codex returned no structured result")
    try:
        if len(encoded) > MAX_CODEX_OUTPUT_BYTES:
            raise CodexInvocationError(
                "Codex structured result exceeded the safe size limit"
            )
        payload = json.loads(encoded.decode("utf-8"))
    except CodexInvocationError:
        raise
    except (OSError, UnicodeError, ValueError):
        raise CodexInvocationError("Codex returned no valid structured result") from None
    if not isinstance(payload, dict):
        raise CodexInvocationError("Codex structured result must be an object")
    return payload


__all__ = [
    "ALLOWED_WORKSHOP_MODELS",
    "CODEX_SESSION_CHECKPOINT_KIND",
    "DEFAULT_CODEX_TIMEOUT_SECONDS",
    "MAX_CODEX_EVENT_BYTES",
    "MAX_CODEX_MESSAGE_BYTES",
    "MAX_CODEX_OUTPUT_BYTES",
    "MAX_CODEX_PROMPT_BYTES",
    "MAX_CODEX_SESSION_CHECKPOINT_BYTES",
    "MAX_CODEX_STDERR_BYTES",
    "CodexInvocationError",
    "CodexNativeSessionBinding",
    "CodexNativeSessionLauncher",
    "CodexNativeSessionOutcome",
    "CodexStructuredRunner",
]
