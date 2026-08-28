"""One whole-run native Claude Code session launcher.

Claude Code is a peer Workshop Manager, not a Python agent framework. This
adapter translates the shared host start/resume contract into Claude's print
mode, session resume, and permission protocol. Live private-Wish acceptance
remains experimental until a Forge run completes on this adapter.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional

from workshop.errors import ContractError
from workshop.runtime.managers import (
    NativeManagerInvocationError,
    NativeManagerRecoverableError,
)


MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION = (2, 0, 0)
CLAUDE_SESSION_CHECKPOINT_KIND = "autonomous-workshop-native-claude-session"
CLAUDE_SESSION_CHECKPOINT_NAME = "claude-session.json"
CLAUDE_PERMISSION_MODE = "acceptEdits"
DEFAULT_CLAUDE_TIMEOUT_SECONDS = 3_600
MAX_CLAUDE_STDERR_BYTES = 256 * 1024
MAX_CLAUDE_EVENT_BYTES = 1 * 1024 * 1024
MAX_CLAUDE_PROMPT_BYTES = 1 * 1024 * 1024
MAX_CLAUDE_SESSION_CHECKPOINT_BYTES = 32 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SESSION_ID = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST = (
    "PATH",
    "HOME",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)


class ClaudeInvocationError(NativeManagerInvocationError):
    """Claude Code could not complete a native Workshop turn."""


class ClaudeRecoverableInvocationError(NativeManagerRecoverableError):
    """A typed Claude timeout that may resume the same session."""


def claude_supports_native_workshop(version: str) -> bool:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version or "")
    if match is None:
        return False
    parsed = tuple(int(part) for part in match.groups())
    return parsed >= MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION


def claude_subprocess_environment(
    source: Optional[Mapping[str, str]] = None,
    *,
    extra: Optional[Mapping[str, str]] = None,
) -> Mapping[str, str]:
    """Keep Claude login/runtime inputs; never Factory credentials."""

    values = os.environ if source is None else source
    environment = {
        name: value
        for name in CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST
        if isinstance((value := values.get(name)), str) and value
    }
    if extra:
        for name, value in extra.items():
            if not isinstance(name, str) or not name or name.startswith("FACTORY_"):
                raise ContractError("Claude subprocess extra environment is invalid")
            if isinstance(value, str) and value:
                environment[name] = value
    return environment


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _require_sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ContractError("%s is not a SHA-256 digest" % label)
    return value


def _canonical_session_id(value: Any) -> str:
    if not isinstance(value, str) or _SESSION_ID.fullmatch(value) is None:
        raise ContractError("Claude session id is invalid")
    return value


def _validated_prompt(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("Claude native prompt must be non-empty text")
    if len(value.encode("utf-8")) > MAX_CLAUDE_PROMPT_BYTES:
        raise ContractError("Claude native prompt exceeded its byte limit")
    return value


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _write_private_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    source = _canonical_json(value)
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
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def _classify_event(event: Mapping[str, Any]) -> Optional[str]:
    raw = " ".join(
        str(event.get(key) or "")
        for key in ("type", "subtype", "kind")
    ).lower()
    if "tool" in raw:
        return "tool"
    if "agent" in raw:
        return "subagent"
    if "think" in raw or "reason" in raw:
        return "reasoning"
    return None


@dataclass(frozen=True)
class ClaudeNativeSessionOutcome:
    session_id: str
    checkpoint_sha256: str
    cli_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "manager": "claude",
            "session_id": self.session_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "cli_version": self.cli_version,
        }


class ClaudeNativeSessionLauncher:
    """Launch or resume one native Claude Code session for an entire Wish."""

    manager_id = "claude"
    session_checkpoint_name = CLAUDE_SESSION_CHECKPOINT_NAME

    def __init__(
        self,
        *,
        binary: Optional[str] = None,
        timeout_seconds: int = DEFAULT_CLAUDE_TIMEOUT_SECONDS,
        popen_factory: Any = subprocess.Popen,
        version_runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
        uuid_factory: Any = uuid.uuid4,
    ) -> None:
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3_600:
            raise ValueError("Claude timeout_seconds must be from 1 to 3,600")
        self.binary = (
            binary or os.environ.get("WORKSHOP_CLAUDE_BIN") or shutil.which("claude")
        )
        self.timeout_seconds = timeout_seconds
        self._popen_factory = popen_factory
        self._version_runner = version_runner
        self._uuid_factory = uuid_factory
        self.cli_version = cli_version or self._read_cli_version()
        if self.binary and not claude_supports_native_workshop(self.cli_version):
            raise ClaudeInvocationError(
                "Workshop requires Claude Code %s or newer"
                % ".".join(str(part) for part in MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION)
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
        match = re.search(r"\d+\.\d+\.\d+", output)
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
    ) -> ClaudeNativeSessionOutcome:
        session_id = _canonical_session_id(str(self._uuid_factory()))
        identity = self._checkpoint_identity(
            product_id=product_id,
            wish_sha256=wish_sha256,
            constitution_sha256=constitution_sha256,
            run_root=Path(run_root),
            host_state_root=Path(host_state_root),
            session_id=session_id,
        )
        path = Path(host_state_root) / self.session_checkpoint_name
        if path.exists() or path.is_symlink():
            raise ContractError("Claude native session checkpoint already exists")
        digest = hashlib.sha256(_canonical_json(identity)).hexdigest()
        _write_private_checkpoint(path, {**identity, "checkpoint_sha256": digest})
        observed = self._stream(
            command=self._command(Path(run_root), prompt, session_id=None),
            run_root=Path(run_root),
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
        )
        if observed and observed != session_id:
            identity["session_id"] = observed
            digest = hashlib.sha256(_canonical_json(identity)).hexdigest()
            _write_private_checkpoint(path, {**identity, "checkpoint_sha256": digest})
            session_id = observed
        return ClaudeNativeSessionOutcome(session_id, digest, self.cli_version)

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
    ) -> ClaudeNativeSessionOutcome:
        path = Path(host_state_root) / self.session_checkpoint_name
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("kind") != CLAUDE_SESSION_CHECKPOINT_KIND
            or payload.get("product_id") != product_id
            or payload.get("wish_sha256") != wish_sha256
            or payload.get("constitution_sha256") != constitution_sha256
        ):
            raise ContractError("Claude native session checkpoint binding is invalid")
        session_id = _canonical_session_id(payload.get("session_id"))
        self._stream(
            command=self._command(Path(run_root), prompt, session_id=session_id),
            run_root=Path(run_root),
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
        )
        return ClaudeNativeSessionOutcome(
            session_id,
            _require_sha256(
                payload.get("checkpoint_sha256"),
                "Claude session checkpoint sha256",
            ),
            self.cli_version,
        )

    def _checkpoint_identity(
        self,
        *,
        product_id: str,
        wish_sha256: str,
        constitution_sha256: str,
        run_root: Path,
        host_state_root: Path,
        session_id: str,
    ) -> dict[str, Any]:
        _require_sha256(wish_sha256, "Claude Wish sha256")
        _require_sha256(constitution_sha256, "Claude constitution sha256")
        return {
            "schema_version": 1,
            "kind": CLAUDE_SESSION_CHECKPOINT_KIND,
            "product_id": product_id,
            "wish_sha256": wish_sha256,
            "constitution_sha256": constitution_sha256,
            "run_root_sha256": _path_sha256(run_root),
            "host_state_root_sha256": _path_sha256(host_state_root),
            "cli_version": self.cli_version,
            "session_id": session_id,
        }

    def _command(
        self,
        run_root: Path,
        prompt: str,
        *,
        session_id: Optional[str],
    ) -> list[str]:
        prompt = _validated_prompt(prompt)
        if not self.binary:
            raise ClaudeInvocationError("Claude Code is not installed or on PATH")
        command = [
            self.binary,
            "--print",
            "--verbose",
            "--output-format",
            "stream-json",
            "--permission-mode",
            CLAUDE_PERMISSION_MODE,
        ]
        if session_id is not None:
            command.extend(("--resume", session_id))
        command.append(prompt)
        return command

    def _run_environment(self, run_root: Path) -> Mapping[str, str]:
        private_temp = run_root / ".tmp"
        private_temp.mkdir(mode=0o700, exist_ok=True)
        return claude_subprocess_environment(
            extra={
                "TMPDIR": str(private_temp),
                "WORKSHOP_PYTHON": str(Path(sys.executable).absolute()),
                "PYTHONHASHSEED": "0",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
            }
        )

    def _stream(
        self,
        *,
        command: list[str],
        run_root: Path,
        activity_observer: Optional[Callable[[str], None]],
        finalization_marker: Optional[Path] = None,
    ) -> Optional[str]:
        if activity_observer is not None:
            activity_observer("starting")
        deadline = time.monotonic() + self.timeout_seconds
        stderr_chunks: list[str] = []
        stderr_bytes = 0

        def _drain_stderr(stream: Any) -> None:
            nonlocal stderr_bytes
            if stream is None:
                return
            try:
                for chunk in stream:
                    remaining = MAX_CLAUDE_STDERR_BYTES - stderr_bytes
                    if remaining <= 0:
                        break
                    text = chunk[:remaining] if isinstance(chunk, str) else ""
                    stderr_chunks.append(text)
                    stderr_bytes += len(text.encode("utf-8", errors="replace"))
            except (OSError, ValueError):
                return

        try:
            process = self._popen_factory(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(run_root),
                env=self._run_environment(run_root),
            )
        except OSError as exc:
            raise ClaudeInvocationError("Claude Code could not start") from exc
        stderr_thread = threading.Thread(
            target=_drain_stderr, args=(process.stderr,), daemon=True
        )
        stderr_thread.start()
        observed: Optional[str] = None
        stream_error: Optional[str] = None
        stdout = process.stdout
        try:
            if stdout is not None:
                for raw in stdout:
                    if time.monotonic() > deadline:
                        process.kill()
                        raise ClaudeRecoverableInvocationError(
                            "Claude native session timed out"
                        )
                    line = raw.strip()
                    if not line or len(line.encode("utf-8")) > MAX_CLAUDE_EVENT_BYTES:
                        continue
                    try:
                        event = json.loads(line)
                    except (TypeError, ValueError):
                        continue
                    if not isinstance(event, Mapping):
                        continue
                    session = event.get("session_id") or event.get("sessionId")
                    if isinstance(session, str) and _SESSION_ID.fullmatch(session):
                        observed = session
                    if event.get("type") == "rate_limit_event":
                        info = event.get("rate_limit_info")
                        if isinstance(info, Mapping) and info.get("status") == "rejected":
                            stream_error = (
                                "Claude Code weekly limit reached; "
                                "the native session cannot start"
                            )
                    elif event.get("is_error") is True and stream_error is None:
                        stream_error = "Claude Code reported an error turn"
                    activity = _classify_event(event)
                    if activity is not None and activity_observer is not None:
                        activity_observer(activity)
            returncode = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            process.kill()
            raise ClaudeRecoverableInvocationError(
                "Claude native session timed out"
            ) from exc
        stderr_thread.join(timeout=1.0)
        if stream_error is not None:
            raise ClaudeInvocationError(stream_error)
        if returncode not in (0, None):
            detail = "".join(stderr_chunks).strip().replace("\n", " ")
            if detail:
                raise ClaudeInvocationError(
                    "Claude native session exited unsuccessfully: %s" % detail[:512]
                )
            raise ClaudeInvocationError("Claude native session exited unsuccessfully")
        if finalization_marker is not None and not Path(finalization_marker).is_file():
            raise ClaudeRecoverableInvocationError(
                "Claude native session ended before the stage finalizer"
            )
        if activity_observer is not None:
            activity_observer("completed")
        return observed


__all__ = [
    "CLAUDE_SESSION_CHECKPOINT_NAME",
    "ClaudeInvocationError",
    "ClaudeNativeSessionLauncher",
    "ClaudeNativeSessionOutcome",
    "ClaudeRecoverableInvocationError",
    "MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION",
    "claude_subprocess_environment",
    "claude_supports_native_workshop",
]
