"""Agent provider boundary.

Alice speaks one JSON contract. A separate harness command may translate that
contract to Codex, Claude Code, OpenClaw, or another model. The runtime never
places provider credentials in a prompt or event payload.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import selectors
import signal
import subprocess
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Any, Iterator, Mapping, Protocol, Sequence


@dataclass(frozen=True, slots=True)
class AgentRequest:
    request_id: str
    role: str
    objective: str
    context: dict[str, Any]
    output_contract: dict[str, Any] = field(default_factory=dict)
    max_output_bytes: int = 200_000


@dataclass(frozen=True, slots=True)
class AgentResponse:
    request_id: str
    provider_run_id: str
    content: dict[str, Any]
    claims: tuple[dict[str, Any], ...] = ()
    artifacts: tuple[dict[str, Any], ...] = ()
    confidence: float = 0.0
    elapsed_seconds: float = 0.0


class AgentProvider(Protocol):
    def run(self, request: AgentRequest) -> AgentResponse: ...


class ProviderError(RuntimeError):
    pass


class BoundedProcessTimeout(TimeoutError):
    """A subprocess exceeded its wall-clock deadline."""


class BoundedProcessOutputLimit(RuntimeError):
    """A subprocess exceeded one of its byte-counted pipe limits."""

    def __init__(self, stream: str) -> None:
        super().__init__(f"{stream} exceeded its byte limit")
        self.stream = stream


@dataclass(frozen=True, slots=True)
class BoundedProcessResult:
    """Bounded subprocess output; raw stderr never crosses this boundary."""

    returncode: int
    stdout: bytes
    stdout_bytes: int
    stderr_sha256: str
    stderr_bytes: int


class ManagedProcessGroup:
    """Own one new-session subprocess and every descendant in its process group.

    Callers must create ``proc`` with ``start_new_session=True``.  Capturing the
    group id while the child is alive, and requiring it to equal the child pid,
    keeps every later signal scoped to the group Alice created.
    """

    def __init__(self, proc: subprocess.Popen[Any]) -> None:
        self.proc = proc
        self.pgid: int | None = None
        if hasattr(os, "getpgid") and hasattr(os, "killpg"):
            try:
                pgid = os.getpgid(proc.pid)
            except OSError:
                pgid = -1
            if pgid == proc.pid:
                self.pgid = pgid

    def signal(self, sig: signal.Signals) -> None:
        """Signal only the captured Alice-owned group (or its direct child)."""

        try:
            if self.pgid is not None and hasattr(os, "killpg"):
                os.killpg(self.pgid, sig)
            elif self.proc.poll() is None:
                if sig == signal.SIGTERM:
                    self.proc.terminate()
                else:
                    self.proc.kill()
        except (OSError, ProcessLookupError):
            pass

    def exists(self) -> bool:
        if self.pgid is None or not hasattr(os, "killpg"):
            return self.proc.poll() is None
        try:
            os.killpg(self.pgid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            # It is still present; inability to signal is not absence.
            return True
        except OSError:
            return False
        return True

    def stop(self, grace_seconds: float) -> None:
        """TERM, then KILL, the complete group and reap the direct child."""

        grace = max(0.0, float(grace_seconds))
        self.signal(signal.SIGTERM)
        deadline = time.monotonic() + grace
        while self.exists() and time.monotonic() < deadline:
            # poll() reaps the direct child; descendants keep the group alive.
            self.proc.poll()
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))
        if self.exists():
            self.signal(signal.SIGKILL)
        try:
            self.proc.wait(timeout=max(0.1, min(5.0, grace or 0.1)))
        except (OSError, subprocess.TimeoutExpired):
            pass

    @contextmanager
    def cleanup_on_parent_sigterm(self) -> Iterator[None]:
        """Scope a parent SIGTERM handler that first signals this child group.

        Python only permits signal-handler installation on the main thread.  In
        that normal worker path we chain an existing application handler and
        otherwise turn the signal into ``SystemExit`` so surrounding ``finally``
        blocks can perform the KILL/reap phase.  Non-main-thread callers still
        get deterministic cleanup on every ordinary exit.
        """

        installed = False
        previous: Any = None
        handler: Any = None
        if (
            threading.current_thread() is threading.main_thread()
            and hasattr(signal, "SIGTERM")
        ):
            previous = signal.getsignal(signal.SIGTERM)

            def _handle(signum: int, frame: Any) -> None:
                self.signal(signal.SIGTERM)
                if callable(previous):
                    previous(signum, frame)
                    return
                if previous == signal.SIG_IGN:
                    return
                raise SystemExit(128 + signum)

            handler = _handle
            signal.signal(signal.SIGTERM, handler)
            installed = True
        try:
            yield
        finally:
            if installed and signal.getsignal(signal.SIGTERM) is handler:
                signal.signal(signal.SIGTERM, previous)


def run_bounded_process(
    command: Sequence[str],
    *,
    input_bytes: bytes,
    timeout_seconds: float,
    stdout_limit_bytes: int,
    stderr_limit_bytes: int = 65_536,
    shutdown_grace_seconds: float = 1.0,
    env: Mapping[str, str] | None = None,
    cwd: str | os.PathLike[str] | None = None,
) -> BoundedProcessResult:
    """Run a no-shell command with byte caps and complete process-tree cleanup.

    ``stdout`` is retained only up to its declared cap.  ``stderr`` is streamed
    through SHA-256 and never retained or returned as raw text.  Any timeout or
    cap violation terminates the new process group, including grandchildren.
    A successful direct child is also followed by a lingering-group check so a
    command cannot leave a daemon behind.
    """

    if not command:
        raise ValueError("command must not be empty")
    if isinstance(timeout_seconds, bool) or not math.isfinite(float(timeout_seconds)):
        raise ValueError("timeout_seconds must be a positive finite number")
    if float(timeout_seconds) <= 0:
        raise ValueError("timeout_seconds must be a positive finite number")
    for name, value in (
        ("stdout_limit_bytes", stdout_limit_bytes),
        ("stderr_limit_bytes", stderr_limit_bytes),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if (
        isinstance(shutdown_grace_seconds, bool)
        or not math.isfinite(float(shutdown_grace_seconds))
        or float(shutdown_grace_seconds) <= 0
    ):
        raise ValueError("shutdown_grace_seconds must be a positive finite number")

    proc = subprocess.Popen(
        tuple(command),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=None if env is None else dict(env),
        bufsize=0,
        start_new_session=True,
    )
    group = ManagedProcessGroup(proc)
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stdout_bytes = 0
    stderr_bytes = 0
    stderr_hash = hashlib.sha256()
    input_offset = 0
    timed_out = False
    limited_stream: str | None = None
    completed = False

    assert proc.stdout is not None
    assert proc.stderr is not None
    assert proc.stdin is not None
    streams = (proc.stdin, proc.stdout, proc.stderr)
    for stream in streams:
        os.set_blocking(stream.fileno(), False)
    selector.register(proc.stdout, selectors.EVENT_READ, "stdout")
    selector.register(proc.stderr, selectors.EVENT_READ, "stderr")
    if input_bytes:
        selector.register(proc.stdin, selectors.EVENT_WRITE, "stdin")
    else:
        proc.stdin.close()

    deadline = time.monotonic() + float(timeout_seconds)
    child_exited_at: float | None = None
    try:
        with group.cleanup_on_parent_sigterm():
            while True:
                now = time.monotonic()
                if now >= deadline:
                    timed_out = True
                    break
                returncode = proc.poll()
                if returncode is not None and child_exited_at is None:
                    child_exited_at = now

                registered = {key.data for key in selector.get_map().values()}
                output_open = "stdout" in registered or "stderr" in registered
                if returncode is not None and not output_open:
                    completed = True
                    break
                # A descendant inherited a pipe after its parent exited. Give
                # normal EOF a moment, then close the entire owned group.
                if (
                    returncode is not None
                    and output_open
                    and child_exited_at is not None
                    and now - child_exited_at >= 0.05
                ):
                    group.stop(float(shutdown_grace_seconds))
                    child_exited_at = None

                events = selector.select(min(0.05, max(0.0, deadline - now)))
                for key, _ in events:
                    stream = key.fileobj
                    kind = key.data
                    if kind == "stdin":
                        try:
                            written = os.write(
                                stream.fileno(), input_bytes[input_offset : input_offset + 65_536]
                            )
                            input_offset += written
                        except (BrokenPipeError, OSError):
                            input_offset = len(input_bytes)
                        if input_offset >= len(input_bytes):
                            try:
                                selector.unregister(stream)
                            except (KeyError, ValueError):
                                pass
                            stream.close()
                        continue

                    try:
                        chunk = os.read(stream.fileno(), 65_536)
                    except BlockingIOError:
                        continue
                    except OSError:
                        chunk = b""
                    if not chunk:
                        try:
                            selector.unregister(stream)
                        except (KeyError, ValueError):
                            pass
                        stream.close()
                        continue
                    if kind == "stdout":
                        stdout_bytes += len(chunk)
                        room = max(0, stdout_limit_bytes - len(stdout))
                        stdout.extend(chunk[:room])
                        if stdout_bytes > stdout_limit_bytes:
                            limited_stream = "stdout"
                            break
                    else:
                        stderr_bytes += len(chunk)
                        stderr_hash.update(chunk)
                        if stderr_bytes > stderr_limit_bytes:
                            limited_stream = "stderr"
                            break
                if limited_stream is not None:
                    break
    finally:
        if not completed:
            group.stop(float(shutdown_grace_seconds))
        else:
            # poll() reaped the direct child. If descendants detached their
            # pipes but stayed in Alice's group, terminate them before return.
            if group.exists():
                group.stop(float(shutdown_grace_seconds))
        for key in list(selector.get_map().values()):
            try:
                selector.unregister(key.fileobj)
            except (KeyError, ValueError):
                pass
        selector.close()
        for stream in streams:
            try:
                if not stream.closed:
                    stream.close()
            except (OSError, ValueError):
                pass

    if timed_out:
        raise BoundedProcessTimeout(
            f"process timed out after {float(timeout_seconds):g} seconds"
        )
    if limited_stream is not None:
        raise BoundedProcessOutputLimit(limited_stream)
    return BoundedProcessResult(
        returncode=int(proc.returncode if proc.returncode is not None else -1),
        stdout=bytes(stdout),
        stdout_bytes=stdout_bytes,
        stderr_sha256=stderr_hash.hexdigest(),
        stderr_bytes=stderr_bytes,
    )


class CommandAgentProvider:
    """Run an isolated JSON-in/JSON-out harness without invoking a shell."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        timeout_seconds: int = 900,
        max_stderr_bytes: int = 65_536,
        shutdown_grace_seconds: float = 1.0,
        allowed_environment: Sequence[str] = ("PATH", "HOME"),
    ) -> None:
        if not command:
            raise ValueError("agent command must not be empty")
        if (
            isinstance(timeout_seconds, bool)
            or not math.isfinite(float(timeout_seconds))
            or float(timeout_seconds) <= 0
        ):
            raise ValueError("timeout_seconds must be a positive finite number")
        self.command = tuple(command)
        self.timeout_seconds = float(timeout_seconds)
        if (
            isinstance(max_stderr_bytes, bool)
            or not isinstance(max_stderr_bytes, int)
            or max_stderr_bytes <= 0
        ):
            raise ValueError("max_stderr_bytes must be a positive integer")
        if (
            isinstance(shutdown_grace_seconds, bool)
            or not math.isfinite(float(shutdown_grace_seconds))
            or float(shutdown_grace_seconds) <= 0
        ):
            raise ValueError(
                "shutdown_grace_seconds must be a positive finite number"
            )
        self.max_stderr_bytes = max_stderr_bytes
        self.shutdown_grace_seconds = float(shutdown_grace_seconds)
        self.environment = {
            name: os.environ[name]
            for name in allowed_environment
            if name in os.environ
        }

    def run(self, request: AgentRequest) -> AgentResponse:
        started = time.monotonic()
        if isinstance(request.max_output_bytes, bool) or request.max_output_bytes <= 0:
            raise ProviderError("request max_output_bytes must be positive")
        payload = json.dumps(asdict(request), sort_keys=True, separators=(",", ":"))
        try:
            result = run_bounded_process(
                self.command,
                input_bytes=payload.encode("utf-8"),
                timeout_seconds=self.timeout_seconds,
                stdout_limit_bytes=request.max_output_bytes,
                stderr_limit_bytes=self.max_stderr_bytes,
                shutdown_grace_seconds=self.shutdown_grace_seconds,
                env=self.environment,
            )
        except BoundedProcessTimeout as exc:
            raise ProviderError(
                f"agent harness timed out after {self.timeout_seconds:g} seconds"
            ) from exc
        except BoundedProcessOutputLimit as exc:
            raise ProviderError(f"agent harness {exc.stream} exceeded its byte limit") from exc
        except OSError as exc:
            raise ProviderError(
                f"agent harness could not start ({type(exc).__name__})"
            ) from exc
        if result.returncode != 0:
            raise ProviderError(
                f"agent harness exited {result.returncode}; "
                f"stderr_sha256={result.stderr_sha256}; "
                f"stderr_bytes={result.stderr_bytes}"
            )
        try:
            raw = json.loads(result.stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("agent harness did not return one JSON object") from exc
        return _parse_response(request, raw, time.monotonic() - started)


class FixtureAgentProvider:
    """Deterministic provider for smoke tests; its evidence is never external."""

    def run(self, request: AgentRequest) -> AgentResponse:
        digest = hashlib.sha256(
            json.dumps(asdict(request), sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        content = {
            "fixture": True,
            "role": request.role,
            "objective": request.objective,
            "summary": "Deterministic fixture output; not publication evidence.",
            "request_digest": digest,
        }
        return AgentResponse(
            request_id=request.request_id,
            provider_run_id=f"fixture-{digest[:16]}",
            content=content,
            claims=(),
            artifacts=(),
            confidence=0.25,
            elapsed_seconds=0.0,
        )


def _parse_response(
    request: AgentRequest, raw: Any, elapsed_seconds: float
) -> AgentResponse:
    if not isinstance(raw, dict):
        raise ProviderError("agent response must be an object")
    if raw.get("request_id") not in {None, request.request_id}:
        raise ProviderError("agent response request_id mismatch")
    content = raw.get("content")
    if not isinstance(content, dict):
        raise ProviderError("agent response content must be an object")
    confidence_value = raw.get("confidence", 0.0)
    if isinstance(confidence_value, bool) or not isinstance(
        confidence_value, (int, float)
    ):
        raise ProviderError("agent confidence must be between 0 and 1")
    confidence = float(confidence_value)
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ProviderError("agent confidence must be between 0 and 1")
    claims = raw.get("claims", [])
    artifacts = raw.get("artifacts", [])
    if not isinstance(claims, list) or not all(isinstance(item, dict) for item in claims):
        raise ProviderError("claims must be an array of objects")
    if not isinstance(artifacts, list) or not all(isinstance(item, dict) for item in artifacts):
        raise ProviderError("artifacts must be an array of objects")
    provider_run_id = str(raw.get("provider_run_id") or "")
    if not provider_run_id:
        provider_run_id = hashlib.sha256(
            json.dumps(raw, sort_keys=True).encode("utf-8")
        ).hexdigest()[:24]
    return AgentResponse(
        request_id=request.request_id,
        provider_run_id=provider_run_id,
        content=content,
        claims=tuple(claims),
        artifacts=tuple(artifacts),
        confidence=confidence,
        elapsed_seconds=elapsed_seconds,
    )
