"""One whole-run native Grok Build session launcher.

Grok Build is a peer Workshop Manager, not a Python agent framework. This
adapter translates the shared host start/resume contract into Grok's pinned
CLI, session, and sandbox protocols. Live private-Wish acceptance remains
experimental until a Forge run completes on this adapter.
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


PINNED_GROK_NATIVE_RUNTIME_VERSION = "1.0.5 (5115b46bc909)"
MINIMUM_GROK_NATIVE_RUNTIME_VERSION = (1, 0, 5)
GROK_MODEL = "grok-4.6"
GROK_PERMISSION_MODE = "dontAsk"
GROK_SESSION_CHECKPOINT_KIND = "autonomous-workshop-native-grok-session"
GROK_SESSION_CHECKPOINT_NAME = "grok-session.json"
DEFAULT_GROK_TIMEOUT_SECONDS = 3_600
DEFAULT_GROK_MAX_TURNS = 128
MAX_GROK_STDERR_BYTES = 256 * 1024
MAX_GROK_EVENT_BYTES = 1 * 1024 * 1024
MAX_GROK_PROMPT_BYTES = 1 * 1024 * 1024
MAX_GROK_SESSION_CHECKPOINT_BYTES = 32 * 1024
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)
GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST = (
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


class GrokInvocationError(NativeManagerInvocationError):
    """Grok Build could not complete a native Workshop turn."""


class GrokRecoverableInvocationError(NativeManagerRecoverableError):
    """A typed Grok timeout that may resume the same session."""


def grok_supports_native_workshop(version: str) -> bool:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version or "")
    if match is None:
        return False
    parsed = tuple(int(part) for part in match.groups())
    return parsed >= MINIMUM_GROK_NATIVE_RUNTIME_VERSION


def grok_subprocess_environment(
    source: Optional[Mapping[str, str]] = None,
    *,
    extra: Optional[Mapping[str, str]] = None,
) -> Mapping[str, str]:
    """Keep Grok login/runtime inputs; never Factory credentials."""

    values = os.environ if source is None else source
    environment = {
        name: value
        for name in GROK_SUBPROCESS_ENVIRONMENT_ALLOWLIST
        if isinstance((value := values.get(name)), str) and value
    }
    if extra:
        for name, value in extra.items():
            if not isinstance(name, str) or not name or name.startswith("FACTORY_"):
                raise ContractError("Grok subprocess extra environment is invalid")
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
    if not isinstance(value, str) or _UUID.fullmatch(value) is None:
        raise ContractError("Grok session id must be a UUID")
    return value.lower()


def _validated_prompt(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError("Grok native prompt must be non-empty text")
    encoded = value.encode("utf-8")
    if len(encoded) > MAX_GROK_PROMPT_BYTES:
        raise ContractError("Grok native prompt exceeded its byte limit")
    return value


def _path_sha256(path: Path) -> str:
    return hashlib.sha256(str(path).encode("utf-8")).hexdigest()


def _write_private_checkpoint(path: Path, value: Mapping[str, Any]) -> None:
    source = _canonical_json(value)
    if len(source) > MAX_GROK_SESSION_CHECKPOINT_BYTES:
        raise GrokInvocationError("Grok session checkpoint exceeded its safe size limit")
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
        for key in ("type", "subtype", "kind", "method")
    ).lower()
    if "tool" in raw or "command" in raw:
        return "tool"
    if "agent" in raw or "subagent" in raw:
        return "subagent"
    if "think" in raw or "reason" in raw:
        return "reasoning"
    return None


@dataclass(frozen=True)
class GrokNativeSessionOutcome:
    session_id: str
    checkpoint_sha256: str
    cli_version: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "manager": "grok",
            "session_id": self.session_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "cli_version": self.cli_version,
        }


class GrokNativeSessionLauncher:
    """Launch or resume one native Grok Build session for an entire Wish."""

    manager_id = "grok"
    session_checkpoint_name = GROK_SESSION_CHECKPOINT_NAME

    def __init__(
        self,
        *,
        binary: Optional[str] = None,
        model: str = GROK_MODEL,
        timeout_seconds: int = DEFAULT_GROK_TIMEOUT_SECONDS,
        max_turns: int = DEFAULT_GROK_MAX_TURNS,
        popen_factory: Any = subprocess.Popen,
        version_runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
        uuid_factory: Any = uuid.uuid4,
    ) -> None:
        if model != GROK_MODEL:
            raise ContractError("Workshop Grok model must be grok-4.6")
        if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 3_600:
            raise ValueError("Grok timeout_seconds must be from 1 to 3,600")
        if type(max_turns) is not int or not 1 <= max_turns <= 1_024:
            raise ValueError("Grok max_turns must be from 1 to 1,024")
        self.binary = binary or os.environ.get("WORKSHOP_GROK_BIN") or shutil.which("grok")
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_turns = max_turns
        self._popen_factory = popen_factory
        self._version_runner = version_runner
        self._uuid_factory = uuid_factory
        self.cli_version = cli_version or self._read_cli_version()
        if self.binary and not grok_supports_native_workshop(self.cli_version):
            raise GrokInvocationError(
                "Workshop requires Grok Build %s or newer"
                % ".".join(str(part) for part in MINIMUM_GROK_NATIVE_RUNTIME_VERSION)
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
                env=grok_subprocess_environment(),
            )
        except (OSError, subprocess.SubprocessError):
            return "0.0.0"
        output = completed.stdout if isinstance(completed.stdout, str) else ""
        match = re.search(r"\d+\.\d+\.\d+(?:\s+\([0-9a-f]+\))?", output)
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
    ) -> GrokNativeSessionOutcome:
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
            raise ContractError("Grok native session checkpoint already exists")
        digest = hashlib.sha256(_canonical_json(identity)).hexdigest()
        _write_private_checkpoint(path, {**identity, "checkpoint_sha256": digest})
        self._stream(
            command=self._command(Path(run_root), session_id, prompt, resume=False),
            run_root=Path(run_root),
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
        )
        return GrokNativeSessionOutcome(session_id, digest, self.cli_version)

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
    ) -> GrokNativeSessionOutcome:
        path = Path(host_state_root) / self.session_checkpoint_name
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            not isinstance(payload, dict)
            or payload.get("kind") != GROK_SESSION_CHECKPOINT_KIND
            or payload.get("product_id") != product_id
            or payload.get("wish_sha256") != wish_sha256
            or payload.get("constitution_sha256") != constitution_sha256
        ):
            raise ContractError("Grok native session checkpoint binding is invalid")
        session_id = _canonical_session_id(payload.get("session_id"))
        self._stream(
            command=self._command(Path(run_root), session_id, prompt, resume=True),
            run_root=Path(run_root),
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
        )
        return GrokNativeSessionOutcome(
            session_id,
            _require_sha256(
                payload.get("checkpoint_sha256"),
                "Grok session checkpoint sha256",
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
        _require_sha256(wish_sha256, "Grok Wish sha256")
        _require_sha256(constitution_sha256, "Grok constitution sha256")
        return {
            "schema_version": 1,
            "kind": GROK_SESSION_CHECKPOINT_KIND,
            "product_id": product_id,
            "wish_sha256": wish_sha256,
            "constitution_sha256": constitution_sha256,
            "run_root_sha256": _path_sha256(run_root),
            "host_state_root_sha256": _path_sha256(host_state_root),
            "cli_version": self.cli_version,
            "session_id": session_id,
        }

    def _run_environment(self, run_root: Path) -> Mapping[str, str]:
        private_temp = run_root / ".tmp"
        private_temp.mkdir(mode=0o700, exist_ok=True)
        return grok_subprocess_environment(
            extra={
                "TMPDIR": str(private_temp),
                "WORKSHOP_PYTHON": str(Path(sys.executable).absolute()),
                "PYTHONHASHSEED": "0",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONNOUSERSITE": "1",
            }
        )

    def _command(
        self,
        run_root: Path,
        session_id: str,
        prompt: str,
        *,
        resume: bool,
    ) -> list[str]:
        prompt = _validated_prompt(prompt)
        selector = "--resume" if resume else "--session-id"
        if not self.binary:
            raise GrokInvocationError("Grok Build is not installed or on PATH")
        command = [
            self.binary,
            "--no-plan",
            "--always-approve",
            "--verbatim",
            "--cwd",
            str(run_root),
            "--model",
            self.model,
            "--permission-mode",
            GROK_PERMISSION_MODE,
            "--max-turns",
            str(self.max_turns),
            "--output-format",
            "streaming-json",
            "--allow",
            "Read(./**)",
            "--allow",
            "Edit(artifacts/**)",
            "--allow",
            "Edit(work/**)",
            "--allow",
            "Bash(*)",
            "--deny",
            "Edit(STAGE.json)",
            "--deny",
            "Edit(WISH.json)",
            "--deny",
            "Edit(AGENTS.md)",
            "--deny",
            "Edit(MANAGER.json)",
            "--deny",
            "Edit(.agents/**)",
            "--deny",
            "Edit(.codex/**)",
            selector,
            session_id,
            "-p",
            prompt,
        ]
        return command

    def _stream(
        self,
        *,
        command: list[str],
        run_root: Path,
        activity_observer: Optional[Callable[[str], None]],
        finalization_marker: Optional[Path] = None,
    ) -> None:
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
                    remaining = MAX_GROK_STDERR_BYTES - stderr_bytes
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
            raise GrokInvocationError("Grok Build could not start") from exc
        stderr_thread = threading.Thread(
            target=_drain_stderr, args=(process.stderr,), daemon=True
        )
        stderr_thread.start()
        stdout = process.stdout
        try:
            if stdout is not None:
                for raw in stdout:
                    if time.monotonic() > deadline:
                        process.kill()
                        raise GrokRecoverableInvocationError(
                            "Grok native session timed out"
                        )
                    line = raw.strip()
                    if not line or len(line.encode("utf-8")) > MAX_GROK_EVENT_BYTES:
                        continue
                    try:
                        event = json.loads(line)
                    except (TypeError, ValueError):
                        continue
                    if not isinstance(event, Mapping):
                        continue
                    activity = _classify_event(event)
                    if activity is not None and activity_observer is not None:
                        activity_observer(activity)
            returncode = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        except subprocess.TimeoutExpired as exc:
            process.kill()
            raise GrokRecoverableInvocationError(
                "Grok native session timed out"
            ) from exc
        stderr_thread.join(timeout=1.0)
        if returncode not in (0, None):
            detail = "".join(stderr_chunks).strip().replace("\n", " ")
            if detail:
                raise GrokInvocationError(
                    "Grok native session exited unsuccessfully: %s" % detail[:512]
                )
            raise GrokInvocationError("Grok native session exited unsuccessfully")
        if finalization_marker is not None and not Path(finalization_marker).is_file():
            # Grok -p is one user-turn of agent work. A clean exit before the
            # stage finalizer is a resumable chunk, not a completed Goal.
            raise GrokRecoverableInvocationError(
                "Grok native session ended before the stage finalizer"
            )
        if activity_observer is not None:
            activity_observer("completed")


__all__ = [
    "DEFAULT_GROK_MAX_TURNS",
    "GROK_SESSION_CHECKPOINT_NAME",
    "GrokInvocationError",
    "GrokNativeSessionLauncher",
    "GrokNativeSessionOutcome",
    "GrokRecoverableInvocationError",
    "MINIMUM_GROK_NATIVE_RUNTIME_VERSION",
    "PINNED_GROK_NATIVE_RUNTIME_VERSION",
    "grok_subprocess_environment",
    "grok_supports_native_workshop",
]
