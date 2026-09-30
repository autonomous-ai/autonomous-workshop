"""One whole-run native Claude Code session launcher.

Claude Code is a peer Workshop Manager, not a Python agent framework. This
adapter translates the shared host start/resume contract into Claude's print
mode, session resume, and permission protocol, and reports each invocation's
native token usage through the Manager-neutral per-turn contract. Live
private-Wish acceptance remains experimental until a Forge run completes on
this adapter.
"""

from __future__ import annotations

import hashlib
import json
import math
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
from workshop.runtime.make_round_hook import (
    HOOK_TIMEOUT_SECONDS,
    installed_make_round_guard,
    make_round_guard_command,
)
from workshop.runtime.managers import (
    MAX_NATIVE_TOKEN_COUNT,
    MAX_NATIVE_TURN_SECONDS,
    NativeManagerInvocationError,
    NativeManagerRecoverableError,
    NativeTokenUsage,
    SUPPORTED_REASONING_EFFORTS,
    native_token_usage_fields,
    validate_native_token_usage,
)


MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION = (2, 0, 0)
# The oldest release verified to accept --autocompact and
# --forward-subagent-text; a budgeted or windowed turn needs both.
MINIMUM_CLAUDE_METERED_RUNTIME_VERSION = (2, 1, 285)
CLAUDE_SESSION_CHECKPOINT_KIND = "autonomous-workshop-native-claude-session"
CLAUDE_SESSION_CHECKPOINT_NAME = "claude-session.json"
CLAUDE_PERMISSION_MODE = "bypassPermissions"
DEFAULT_CLAUDE_TIMEOUT_SECONDS = 3_600
MAX_CLAUDE_STDERR_BYTES = 256 * 1024
MAX_CLAUDE_EVENT_BYTES = 1 * 1024 * 1024
MAX_CLAUDE_PROMPT_BYTES = 1 * 1024 * 1024
MAX_CLAUDE_SESSION_CHECKPOINT_BYTES = 32 * 1024
# Claude Code accepts an automatic-compaction window from 100k to 1M tokens.
MIN_CLAUDE_AUTOCOMPACT_TOKENS = 100_000
MAX_CLAUDE_AUTOCOMPACT_TOKENS = 1_000_000
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_SESSION_ID = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
_MODEL_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
_MAX_CLAUDE_FAILURE_MESSAGE_CHARS = 4 * 1024
CLAUDE_TOKEN_BUDGET_STOP_MESSAGE = (
    "product token budget stopped native execution; inspect Workshop status"
)
# A failed turn keeps its classification, never the prose that carried it.
_CLAUDE_TERMINAL_ERROR_SIGNATURES = (
    (
        "not-logged-in",
        ("not logged in", "please run /login", "invalid api key"),
    ),
    ("rate-limited", ("rate limit", "too many requests", "usage limit")),
    (
        "context-limit",
        ("context length", "context window", "maximum context", "too many tokens"),
    ),
    ("unauthorized", ("unauthorized", "authentication failed")),
    ("forbidden", ("forbidden", "permission denied")),
    ("permission-prompt", ("requires approval", "permission to use")),
    ("bad-request", ("bad request", "invalid request")),
    ("service-unavailable", ("service unavailable", "provider unavailable")),
    ("overloaded", ("overloaded", "capacity")),
    ("internal-server-error", ("internal server error", "server error")),
)
CLAUDE_SUBPROCESS_ENVIRONMENT_ALLOWLIST = (
    "PATH",
    "HOME",
    # macOS credential resolution needs the account name.  Without it Claude
    # Code reports "Not logged in" even when the ambient session is signed in.
    "USER",
    "LOGNAME",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    # Supported non-interactive Claude Code authentication inputs.  Without
    # these a sandbox that has no interactive ``claude /login`` session under
    # HOME reports "Not logged in" and every turn fails before it starts.
    # They authenticate the model runtime only; they carry no Factory,
    # payment, or other external-effect authority.
    "CLAUDE_CODE_OAUTH_TOKEN",
    "ANTHROPIC_API_KEY",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "TERM",
    "TMPDIR",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)


def claude_hook_settings(script: Path) -> str:
    """The ``--settings`` JSON registering the make_round guard (ADR 0080)."""

    return json.dumps(
        {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Bash",
                        "hooks": [
                            {
                                "type": "command",
                                "command": make_round_guard_command(script),
                                "timeout": HOOK_TIMEOUT_SECONDS,
                            }
                        ],
                    }
                ]
            }
        },
        sort_keys=True,
        separators=(",", ":"),
    )


class ClaudeInvocationError(NativeManagerInvocationError):
    """Claude Code could not complete a native Workshop turn."""


class ClaudeRecoverableInvocationError(NativeManagerRecoverableError):
    """A typed Claude timeout that may resume the same session."""


def _parsed_version(version: str) -> Optional[tuple[int, ...]]:
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", version or "")
    return None if match is None else tuple(int(part) for part in match.groups())


def claude_supports_native_workshop(version: str) -> bool:
    parsed = _parsed_version(version)
    return parsed is not None and parsed >= MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION


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


def _terminal_failure_signature(event: Mapping[str, Any]) -> str:
    """Reduce one error turn to a stable label without retaining its text.

    Claude Code reports a refused or impossible turn as a terminal ``result``
    event whose prose is the only account of what went wrong.  That prose can
    quote the Wish or the workspace, so the host keeps the classification and
    discards the words.
    """

    message = event.get("result")
    if not isinstance(message, str):
        message = ""
    normalized = " ".join(
        message[:_MAX_CLAUDE_FAILURE_MESSAGE_CHARS].casefold().split()
    )
    for candidate, needles in _CLAUDE_TERMINAL_ERROR_SIGNATURES:
        if any(needle in normalized for needle in needles):
            return candidate
    return "unclassified"


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


_MODEL_USAGE_BASE_COUNTERS = (
    "inputTokens",
    "cacheReadInputTokens",
    "cacheCreationInputTokens",
    "outputTokens",
)


def _bounded_token_count(value: Any) -> Optional[int]:
    if type(value) is not int or not 0 <= value <= MAX_NATIVE_TOKEN_COUNT:
        return None
    return value


def _native_token_usage(event: Mapping[str, Any]) -> Optional[NativeTokenUsage]:
    """Reduce one terminal ``result`` event to exact base counters plus detail.

    Claude Code repeats a non-final ``usage`` on every ``assistant`` event of
    a multi-block message and forwards subagent requests only behind an
    opt-in flag this adapter passes solely for a token budget's running
    estimate, so per-message usage is never summed here.  The result's ``modelUsage`` is the CLI's own
    per-invocation total for every model call (main loop, subagents,
    compaction).  One ``--print`` invocation is one host turn and a resumed
    session starts that total fresh, so the latest result is the whole
    account of the turn and nothing is counted twice.

    Claude's ``inputTokens`` excludes cache reads and cache writes, so gross
    input is the sum of the three input counters; ``thinkingTokens`` is the
    reasoning-output subset.  The result's ``usage`` and ``total_cost_usd``
    are not read: the CLI documents the first as either a running total or
    the main loop's turn-end value, and the second is an estimate the host
    never carries.  Totals without a thinking-token subset keep the gross
    counters and drop the detail, exactly like a base-only Codex turn.
    """

    model_usage = event.get("modelUsage")
    if not isinstance(model_usage, Mapping) or not model_usage:
        return None
    gross_input = 0
    cached_input = 0
    cache_write_input = 0
    output = 0
    reasoning = 0
    reasoning_measured = True
    for model, entry in model_usage.items():
        if not isinstance(model, str) or not model or not isinstance(entry, Mapping):
            return None
        counts = [
            _bounded_token_count(entry.get(name))
            for name in _MODEL_USAGE_BASE_COUNTERS
        ]
        if any(count is None for count in counts):
            return None
        uncached, cache_read, cache_write, model_output = counts
        gross_input += uncached + cache_read + cache_write
        cached_input += cache_read
        cache_write_input += cache_write
        output += model_output
        thinking = _bounded_token_count(entry.get("thinkingTokens"))
        if thinking is None or thinking > model_output:
            reasoning_measured = False
        else:
            reasoning += thinking
    if gross_input > MAX_NATIVE_TOKEN_COUNT or output > MAX_NATIVE_TOKEN_COUNT:
        return None
    if not reasoning_measured:
        return (gross_input, None, None, output, None)
    return (gross_input, cached_input, cache_write_input, output, reasoning)


def _request_usage(event: Mapping[str, Any]) -> Optional[tuple[str, dict[str, int]]]:
    """One model request's usage as the stream reports it, keyed by message id.

    Claude Code repeats a request's ``usage`` on every block of the same
    message, so the latest value per id replaces, never adds to, an earlier
    one. Forwarded subagent requests carry their own ids. The input counters
    are exact per request; ``output_tokens`` is the value at the time the block
    was streamed and may undercount, which the terminal result corrects.
    """

    if event.get("type") != "assistant":
        return None
    message = event.get("message")
    if not isinstance(message, Mapping):
        return None
    message_id = message.get("id")
    usage = message.get("usage")
    if not isinstance(message_id, str) or not message_id or not isinstance(usage, Mapping):
        return None
    counts = [
        _bounded_token_count(usage.get(name))
        for name in (
            "input_tokens",
            "cache_read_input_tokens",
            "cache_creation_input_tokens",
            "output_tokens",
        )
    ]
    if any(count is None for count in counts):
        return None
    uncached, cache_read, cache_write, output = counts
    return message_id, {
        "input_tokens": uncached + cache_read + cache_write,
        "cached_input_tokens": cache_read,
        "cache_write_input_tokens": cache_write,
        "output_tokens": output,
        "reasoning_output_tokens": 0,
    }


_INVOCATION_COUNTERS = (
    "input_tokens",
    "cached_input_tokens",
    "cache_write_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)


def _invocation_counters(
    requests: Mapping[str, Mapping[str, int]],
    terminal: Optional[NativeTokenUsage],
) -> dict[str, int]:
    """The invocation's running total: streamed requests, raised by the result.

    The result's ``modelUsage`` also counts compaction and final output, so
    each counter takes the larger of the two; neither source can lower what
    the other already observed.
    """

    totals = {name: 0 for name in _INVOCATION_COUNTERS}
    for counters in requests.values():
        for name in _INVOCATION_COUNTERS:
            totals[name] += counters[name]
    if terminal is not None:
        for name, value in zip(_INVOCATION_COUNTERS, terminal):
            if value is not None:
                totals[name] = max(totals[name], value)
    if totals["cached_input_tokens"] + totals["cache_write_input_tokens"] > totals["input_tokens"]:
        totals["input_tokens"] = (
            totals["cached_input_tokens"] + totals["cache_write_input_tokens"]
        )
    if totals["reasoning_output_tokens"] > totals["output_tokens"]:
        totals["output_tokens"] = totals["reasoning_output_tokens"]
    return totals


@dataclass(frozen=True)
class ClaudeNativeSessionOutcome:
    """Compact public outcome; prose, events, and cost estimates stay out."""

    session_id: str
    checkpoint_sha256: str
    cli_version: str
    input_tokens: Optional[int] = None
    cached_input_tokens: Optional[int] = None
    cache_write_input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    reasoning_output_tokens: Optional[int] = None

    def __post_init__(self) -> None:
        validate_native_token_usage(
            input_tokens=self.input_tokens,
            cached_input_tokens=self.cached_input_tokens,
            cache_write_input_tokens=self.cache_write_input_tokens,
            output_tokens=self.output_tokens,
            reasoning_output_tokens=self.reasoning_output_tokens,
            label="Claude native session",
        )

    def to_dict(self) -> dict[str, Any]:
        value = {
            "manager": "claude",
            "session_id": self.session_id,
            "checkpoint_sha256": self.checkpoint_sha256,
            "cli_version": self.cli_version,
        }
        value.update(
            native_token_usage_fields(
                input_tokens=self.input_tokens,
                cached_input_tokens=self.cached_input_tokens,
                cache_write_input_tokens=self.cache_write_input_tokens,
                output_tokens=self.output_tokens,
                reasoning_output_tokens=self.reasoning_output_tokens,
            )
        )
        return value


def _session_outcome(
    session_id: str,
    checkpoint_sha256: str,
    cli_version: str,
    usage: Optional[NativeTokenUsage],
) -> ClaudeNativeSessionOutcome:
    return ClaudeNativeSessionOutcome(
        session_id=session_id,
        checkpoint_sha256=checkpoint_sha256,
        cli_version=cli_version,
        input_tokens=None if usage is None else usage[0],
        cached_input_tokens=None if usage is None else usage[1],
        cache_write_input_tokens=None if usage is None else usage[2],
        output_tokens=None if usage is None else usage[3],
        reasoning_output_tokens=None if usage is None else usage[4],
    )


class ClaudeNativeSessionLauncher:
    """Launch or resume one native Claude Code session for an entire Wish."""

    manager_id = "claude"
    session_checkpoint_name = CLAUDE_SESSION_CHECKPOINT_NAME

    def __init__(
        self,
        *,
        binary: Optional[str] = None,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        timeout_seconds: Optional[int] = DEFAULT_CLAUDE_TIMEOUT_SECONDS,
        autocompact_tokens: Optional[int] = None,
        popen_factory: Any = subprocess.Popen,
        version_runner: Any = subprocess.run,
        cli_version: Optional[str] = None,
        uuid_factory: Any = uuid.uuid4,
    ) -> None:
        if (model is None) != (reasoning_effort is None):
            raise ContractError(
                "Claude model and reasoning effort must be selected together"
            )
        if model is not None and _MODEL_ID.fullmatch(model) is None:
            raise ContractError("Workshop Claude model is invalid")
        if (
            reasoning_effort is not None
            and reasoning_effort not in SUPPORTED_REASONING_EFFORTS
        ):
            raise ContractError("Workshop Claude reasoning effort is invalid")
        if timeout_seconds is not None and (
            type(timeout_seconds) is not int
            or not 1 <= timeout_seconds <= MAX_NATIVE_TURN_SECONDS
        ):
            raise ValueError(
                "Claude timeout_seconds must be from 1 to %d or None"
                % MAX_NATIVE_TURN_SECONDS
            )
        if autocompact_tokens is not None and (
            type(autocompact_tokens) is not int
            or not MIN_CLAUDE_AUTOCOMPACT_TOKENS
            <= autocompact_tokens
            <= MAX_CLAUDE_AUTOCOMPACT_TOKENS
        ):
            raise ContractError(
                "Claude autocompact window must be from 100,000 to 1,000,000 tokens"
            )
        self.binary = (
            binary or os.environ.get("WORKSHOP_CLAUDE_BIN") or shutil.which("claude")
        )
        self.autocompact_tokens = autocompact_tokens
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.timeout_seconds = timeout_seconds
        self._popen_factory = popen_factory
        self._version_runner = version_runner
        self._uuid_factory = uuid_factory
        # The host sets this per turn for a token-budgeted run. It receives the
        # invocation's running counters and raises to stop the turn.
        self.token_budget_observer: Optional[Callable[..., None]] = None
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
        # Refuse an unusable command before any session identity is written.
        command = self._command(
            Path(run_root),
            prompt,
            session_id=None,
            host_state_root=Path(host_state_root),
        )
        digest = hashlib.sha256(_canonical_json(identity)).hexdigest()
        _write_private_checkpoint(path, {**identity, "checkpoint_sha256": digest})
        bound = {"session_id": session_id, "digest": digest}

        def _bind(observed_id: str) -> None:
            """Record the real session the moment the CLI names it.

            A turn that dies partway -- a timed out clock, a killed process --
            still leaves hours of work in a session that only the CLI can
            reopen.  Binding on the first event rather than on a clean return
            keeps that work resumable.
            """

            if observed_id == bound["session_id"]:
                return
            identity["session_id"] = observed_id
            fresh = hashlib.sha256(_canonical_json(identity)).hexdigest()
            _write_private_checkpoint(path, {**identity, "checkpoint_sha256": fresh})
            bound["session_id"] = observed_id
            bound["digest"] = fresh

        unused_session, token_usage = self._stream(
            command=command,
            run_root=Path(run_root),
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
            session_observer=_bind,
        )
        return _session_outcome(
            bound["session_id"], bound["digest"], self.cli_version, token_usage
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
        schema_version = payload.get("schema_version")
        if schema_version == 1:
            if (
                self.model is not None
                or self.reasoning_effort is not None
                or self.autocompact_tokens is not None
            ):
                raise ContractError("Claude native session runtime binding is invalid")
        elif schema_version == 2:
            if (
                payload.get("model") != self.model
                or payload.get("reasoning_effort") != self.reasoning_effort
                or payload.get("autocompact_tokens") != self.autocompact_tokens
            ):
                raise ContractError("Claude native session runtime binding is invalid")
        else:
            raise ContractError("Claude native session checkpoint schema is invalid")
        session_id = _canonical_session_id(payload.get("session_id"))
        unused_session, token_usage = self._stream(
            command=self._command(
                Path(run_root),
                prompt,
                session_id=session_id,
                host_state_root=Path(host_state_root),
            ),
            run_root=Path(run_root),
            activity_observer=activity_observer,
            finalization_marker=finalization_marker,
        )
        return _session_outcome(
            session_id,
            _require_sha256(
                payload.get("checkpoint_sha256"),
                "Claude session checkpoint sha256",
            ),
            self.cli_version,
            token_usage,
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
        identity = {
            "schema_version": (
                2
                if self.model is not None or self.autocompact_tokens is not None
                else 1
            ),
            "kind": CLAUDE_SESSION_CHECKPOINT_KIND,
            "product_id": product_id,
            "wish_sha256": wish_sha256,
            "constitution_sha256": constitution_sha256,
            "run_root_sha256": _path_sha256(run_root),
            "host_state_root_sha256": _path_sha256(host_state_root),
            "cli_version": self.cli_version,
            "session_id": session_id,
        }
        if self.model is not None:
            identity["model"] = self.model
            identity["reasoning_effort"] = self.reasoning_effort
        if self.autocompact_tokens is not None:
            # The window is frozen with the session, like the model.
            identity["autocompact_tokens"] = self.autocompact_tokens
        return identity

    def _command(
        self,
        run_root: Path,
        prompt: str,
        *,
        session_id: Optional[str],
        host_state_root: Optional[Path] = None,
    ) -> list[str]:
        prompt = _validated_prompt(prompt)
        if not self.binary:
            raise ClaudeInvocationError("Claude Code is not installed or on PATH")
        if self.autocompact_tokens is not None or self.token_budget_observer is not None:
            parsed = _parsed_version(self.cli_version)
            if parsed is None or parsed < MINIMUM_CLAUDE_METERED_RUNTIME_VERSION:
                raise ClaudeInvocationError(
                    "a budgeted or windowed Workshop turn requires Claude Code %s or newer"
                    % ".".join(str(part) for part in MINIMUM_CLAUDE_METERED_RUNTIME_VERSION)
                )
        command = [
            self.binary,
            "--print",
            "--verbose",
            "--output-format",
            "stream-json",
            "--permission-mode",
            CLAUDE_PERMISSION_MODE,
        ]
        if self.model is not None:
            command.extend(
                ("--model", self.model, "--effort", self.reasoning_effort)
            )
        if self.autocompact_tokens is not None:
            command.extend(("--autocompact", str(self.autocompact_tokens)))
        if self.token_budget_observer is not None:
            # Subagent requests reach the stream, and so the budget, only
            # when forwarded.
            command.append("--forward-subagent-text")
        guard = (
            None if host_state_root is None
            else installed_make_round_guard(host_state_root)
        )
        if guard is not None:
            # ADR 0080: the hook lives in host state and is registered from
            # there, never from a settings file in the workspace.
            command.extend(("--settings", claude_hook_settings(guard)))
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
        session_observer: Optional[Callable[[str], None]] = None,
    ) -> tuple[Optional[str], Optional[NativeTokenUsage]]:
        if activity_observer is not None:
            activity_observer("starting")
        deadline = (
            math.inf
            if self.timeout_seconds is None
            else time.monotonic() + self.timeout_seconds
        )
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
        terminal_signature: Optional[str] = None
        token_usage: Optional[NativeTokenUsage] = None
        budget_observer = self.token_budget_observer
        requests: dict[str, dict[str, int]] = {}
        observed_counters: Optional[dict[str, int]] = None
        budget_stopped = False
        stream_finished = False

        def _observe_budget(*, final: bool) -> None:
            nonlocal observed_counters
            counters = _invocation_counters(requests, token_usage)
            if not final and counters == observed_counters:
                return
            observed_counters = counters
            budget_observer(counters, final=final)

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
                        if session != observed and session_observer is not None:
                            session_observer(session)
                        observed = session
                    if event.get("type") == "rate_limit_event":
                        info = event.get("rate_limit_info")
                        if isinstance(info, Mapping) and info.get("status") == "rejected":
                            stream_error = (
                                "Claude Code weekly limit reached; "
                                "the native session cannot start"
                            )
                    elif event.get("is_error") is True:
                        terminal_signature = _terminal_failure_signature(event)
                        if stream_error is None:
                            stream_error = (
                                "Claude Code reported an error turn (signature=%s)"
                                % terminal_signature
                            )
                    if event.get("type") == "result":
                        # The latest result carries the invocation's running
                        # total; it replaces, never adds to, an earlier one.
                        token_usage = _native_token_usage(event)
                    if budget_observer is not None:
                        request = _request_usage(event)
                        if request is not None:
                            requests[request[0]] = request[1]
                        if request is not None or event.get("type") == "result":
                            try:
                                _observe_budget(final=False)
                            except Exception:
                                budget_stopped = True
                                process.kill()
                                raise ClaudeInvocationError(
                                    CLAUDE_TOKEN_BUDGET_STOP_MESSAGE
                                ) from None
                    activity = _classify_event(event)
                    if activity is not None and activity_observer is not None:
                        activity_observer(activity)
            remaining = deadline - time.monotonic()
            returncode = process.wait(
                timeout=max(0.1, remaining) if math.isfinite(remaining) else None
            )
            stream_finished = True
        except subprocess.TimeoutExpired as exc:
            process.kill()
            raise ClaudeRecoverableInvocationError(
                "Claude native session timed out"
            ) from exc
        finally:
            if budget_observer is not None and not budget_stopped:
                # Charge what the stream reported even when the turn ended
                # early; a stop raised here outranks a normal return.
                try:
                    _observe_budget(final=True)
                except Exception:
                    process.kill()
                    if stream_finished:
                        raise ClaudeInvocationError(
                            CLAUDE_TOKEN_BUDGET_STOP_MESSAGE
                        ) from None
        stderr_thread.join(timeout=1.0)
        if stream_error is not None:
            raise ClaudeInvocationError(stream_error)
        if returncode not in (0, None):
            detail = "".join(stderr_chunks).strip().replace("\n", " ")
            if detail:
                raise ClaudeInvocationError(
                    "Claude native session exited unsuccessfully: %s" % detail[:512]
                )
            if terminal_signature is not None:
                raise ClaudeInvocationError(
                    "Claude native session exited unsuccessfully (signature=%s)"
                    % terminal_signature
                )
            raise ClaudeInvocationError("Claude native session exited unsuccessfully")
        if finalization_marker is not None and not Path(finalization_marker).is_file():
            raise ClaudeRecoverableInvocationError(
                "Claude native session ended before the stage finalizer"
            )
        if activity_observer is not None:
            activity_observer("completed")
        return observed, token_usage


__all__ = [
    "CLAUDE_SESSION_CHECKPOINT_NAME",
    "CLAUDE_TOKEN_BUDGET_STOP_MESSAGE",
    "ClaudeInvocationError",
    "ClaudeNativeSessionLauncher",
    "ClaudeNativeSessionOutcome",
    "ClaudeRecoverableInvocationError",
    "MINIMUM_CLAUDE_NATIVE_RUNTIME_VERSION",
    "claude_subprocess_environment",
    "claude_supports_native_workshop",
]
