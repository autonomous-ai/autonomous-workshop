"""Redacted session history for the Factory import.

The Factory replays a ``conversation.jsonl`` shipped at the import archive
root into the design's turns, in the shape of a Claude Code session: one
record per line with ``type`` (``user`` or ``assistant``), a stable ``uuid``,
an ISO-8601 ``timestamp``, and ``message.content`` that is either plain text
or a list of ``text`` / ``tool_use`` / ``tool_result`` blocks.

The trusted host projects the run's main Codex rollout into that shape.  Only
what a reader needs to follow the build survives: the opening prompt, the
host's stage Goals, the Manager's visible replies, and its tool calls with
bounded outputs.  Encrypted reasoning, developer instructions, runtime events,
plugin banners, and subagent traffic are omitted.  Absolute host paths outside
the run workspace and anything the secret scanner recognises are redacted.
Caps mirror the Factory's own replay limits so nothing is silently dropped on
the far side.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence

from workshop.artifacts.core import SECRET_PATTERNS
from workshop.errors import ContractError


SESSION_HISTORY_NAME = "conversation.jsonl"
MAX_HISTORY_BYTES = 12 * 1024 * 1024
MAX_HISTORY_TURNS = 200
MAX_HISTORY_ENTRIES = 5000
MAX_ENTRY_BYTES = 512 * 1024
MAX_PROMPT_CHARS = 8 * 1024
MAX_ASSISTANT_CHARS = 32 * 1024
MAX_TOOL_INPUT_CHARS = 8 * 1024
MAX_TOOL_OUTPUT_CHARS = 16 * 1024
MAX_ROLLOUT_BYTES = 512 * 1024 * 1024
MAX_ROLLOUT_LINE_BYTES = 4 * 1024 * 1024
MAX_ROLLOUT_LINES = 200_000
_THREAD_ID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
_HARNESS_ENVELOPE = re.compile(
    r"^\s*<([a-z_][a-z0-9_-]*)(?:\s[^>]*)?>.*?</\1>\s*", re.S
)
# An absolute path starts a token, or follows an escaped newline/tab inside a
# script literal (`\n/root/...`), which is how tool inputs carry them.
_ABSOLUTE_PATH = re.compile(
    r"(?:(?<=\\n)|(?<=\\t)|(?<![\w./-]))/(?:[A-Za-z0-9._-]+/)*[A-Za-z0-9._-]+"
)
_OMITTED_TOOL_NAMES = frozenset(
    ("spawn_agent", "send_message", "wait_agent", "close_agent", "resume_agent", "list_agents")
)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_AGENTS_INJECTION = re.compile(r"^\s*# AGENTS\.md instructions for ")


class SessionHistoryError(Exception):
    """A bounded reason why no history could be built."""


def codex_sessions_root() -> Path:
    home = os.environ.get("CODEX_HOME")
    base = Path(home) if home else Path.home() / ".codex"
    return base / "sessions"


def find_rollout(thread_id: str, sessions_root: Optional[Path] = None) -> Optional[Path]:
    """Locate the rollout file for one Codex thread, verified by its metadata."""

    if not isinstance(thread_id, str) or _THREAD_ID.fullmatch(thread_id) is None:
        raise ContractError("Codex thread id is malformed")
    root = Path(sessions_root) if sessions_root is not None else codex_sessions_root()
    if not root.is_dir():
        return None
    candidates = sorted(root.rglob("rollout-*-%s.jsonl" % thread_id))
    for candidate in candidates:
        if candidate.is_symlink() or not candidate.is_file():
            continue
        try:
            with candidate.open("rb") as handle:
                first = handle.readline(MAX_ROLLOUT_LINE_BYTES)
            record = json.loads(first.decode("utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        payload = record.get("payload") if isinstance(record, Mapping) else None
        if (
            isinstance(payload, Mapping)
            and record.get("type") == "session_meta"
            and payload.get("id") == thread_id
        ):
            return candidate
    return None


def _clean(text: str) -> str:
    return _CONTROL.sub("", text)


def _trim(text: str, limit: int) -> str:
    text = _clean(text)
    if len(text) <= limit:
        return text
    return text[: limit - 24] + "\n[... %d more characters]" % (len(text) - limit + 24)


@dataclass(frozen=True)
class Redactor:
    """Rewrite host paths and refuse secrets before a record ships."""

    workspace_root: Optional[str]

    def path_text(self, text: str) -> str:
        def replace(match: "re.Match[str]") -> str:
            value = match.group(0)
            if self.workspace_root and (
                value == self.workspace_root or value.startswith(self.workspace_root + "/")
            ):
                return "<workspace>" + value[len(self.workspace_root) :]
            return "<host>"

        return _ABSOLUTE_PATH.sub(replace, text)

    def clean(self, text: str) -> Optional[str]:
        """Return the redacted text, or ``None`` when it must not ship."""

        redacted = self.path_text(text)
        encoded = redacted.encode("utf-8", "replace")
        for pattern in SECRET_PATTERNS.values():
            if pattern.search(encoded):
                return None
        return redacted


def strip_harness_envelopes(text: str) -> str:
    """Drop leading ``<tag>...</tag>`` harness envelopes from a user record.

    Codex and Claude Code both prepend runtime banners (plugin lists,
    environment context, system reminders) to user turns.  The Factory's own
    parser strips the same shapes; stripping here keeps the shipped prompt to
    what the host actually asked.
    """

    remaining = text
    while True:
        match = _HARNESS_ENVELOPE.match(remaining)
        if match is None:
            break
        remaining = remaining[match.end() :]
    # Codex injects the run constitution as a user message headed
    # "# AGENTS.md instructions for <dir>"; it is host configuration, not a
    # prompt the listing should replay.
    if _AGENTS_INJECTION.match(remaining):
        return ""
    return remaining


def _text_of(content: Any, *types: str) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, Sequence):
        return ""
    parts = []
    for block in content:
        if isinstance(block, Mapping) and block.get("type") in types:
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text)
    return "\n\n".join(parts)


def _record_uuid(payload: Mapping[str, Any], fallback: str) -> str:
    for key in ("id", "call_id"):
        value = payload.get(key)
        if isinstance(value, str) and 1 <= len(value) <= 128 and value.isprintable():
            return value
    return fallback


def _tool_input(payload: Mapping[str, Any], redactor: Redactor) -> Optional[Any]:
    raw = payload.get("arguments")
    if raw is None:
        raw = payload.get("input")
    if isinstance(raw, Mapping):
        text = json.dumps(raw, sort_keys=True, ensure_ascii=False)
    elif isinstance(raw, str):
        text = raw
    else:
        text = ""
    cleaned = redactor.clean(_trim(text, MAX_TOOL_INPUT_CHARS))
    if cleaned is None:
        return None
    try:
        parsed = json.loads(cleaned)
    except ValueError:
        return {"raw": cleaned}
    return parsed if isinstance(parsed, dict) else {"raw": cleaned}


def _tool_output(payload: Mapping[str, Any]) -> str:
    output = payload.get("output")
    if isinstance(output, str):
        return output
    return _text_of(output, "input_text", "output_text", "text")


def _iter_rollout(path: Path) -> Iterator[Mapping[str, Any]]:
    size = path.stat().st_size
    if size > MAX_ROLLOUT_BYTES:
        raise SessionHistoryError("rollout exceeds the history size bound")
    with path.open("rb") as handle:
        for number, line in enumerate(handle):
            if number >= MAX_ROLLOUT_LINES:
                return
            if len(line) > MAX_ROLLOUT_LINE_BYTES:
                continue
            try:
                record = json.loads(line.decode("utf-8"))
            except (UnicodeError, ValueError):
                continue
            if isinstance(record, Mapping):
                yield record


def _timestamp(record: Mapping[str, Any], previous: str) -> str:
    value = record.get("timestamp")
    if isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T[0-9:.]+Z?", value):
        return value
    return previous


def _entry(kind: str, uuid: str, timestamp: str, content: Any) -> dict[str, Any]:
    return {
        "type": kind,
        "uuid": uuid,
        "timestamp": timestamp,
        "message": {"role": kind, "content": content},
    }


def build_conversation(
    rollout: Path,
    *,
    opener_text: str,
    opener_uuid: str,
    workspace_root: Optional[Path] = None,
) -> bytes:
    """Project one Codex rollout into Claude-Code-shaped ``conversation.jsonl``."""

    if not isinstance(opener_text, str) or not opener_text.strip():
        raise ContractError("session history opener text is required")
    if not isinstance(opener_uuid, str) or not opener_uuid:
        raise ContractError("session history opener uuid is required")
    redactor = Redactor(str(Path(workspace_root).resolve()) if workspace_root else None)
    entries: list[dict[str, Any]] = []
    turns = 0
    previous_timestamp = "1970-01-01T00:00:00Z"
    opener_written = False
    pending_tool_ids: set[str] = set()

    def push(entry: dict[str, Any]) -> bool:
        if len(entries) >= MAX_HISTORY_ENTRIES:
            return False
        entries.append(entry)
        return True

    for index, record in enumerate(_iter_rollout(rollout)):
        if record.get("type") != "response_item":
            continue
        payload = record.get("payload")
        if not isinstance(payload, Mapping):
            continue
        timestamp = _timestamp(record, previous_timestamp)
        previous_timestamp = timestamp
        if not opener_written:
            push(_entry("user", opener_uuid, timestamp, _trim(opener_text, MAX_PROMPT_CHARS)))
            opener_written = True
            turns = 1
        fallback_uuid = "codex-%d-%s" % (index, hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16])
        kind = payload.get("type")
        if kind == "message":
            role = payload.get("role")
            if role == "user":
                text = strip_harness_envelopes(
                    _text_of(payload.get("content"), "input_text", "text")
                )
                if not text.strip():
                    continue
                if turns >= MAX_HISTORY_TURNS:
                    break
                cleaned = redactor.clean(_trim(text, MAX_PROMPT_CHARS))
                if cleaned is None:
                    continue
                if push(_entry("user", _record_uuid(payload, fallback_uuid), timestamp, cleaned)):
                    turns += 1
            elif role == "assistant":
                text = _text_of(payload.get("content"), "output_text", "text")
                if not text.strip():
                    continue
                cleaned = redactor.clean(_trim(text, MAX_ASSISTANT_CHARS))
                if cleaned is None:
                    continue
                push(
                    _entry(
                        "assistant",
                        _record_uuid(payload, fallback_uuid),
                        timestamp,
                        [{"type": "text", "text": cleaned}],
                    )
                )
        elif kind in ("function_call", "custom_tool_call"):
            name = payload.get("name")
            call_id = payload.get("call_id")
            if (
                not isinstance(name, str)
                or not name
                or name in _OMITTED_TOOL_NAMES
                or payload.get("namespace") == "collaboration"
                or not isinstance(call_id, str)
                or not call_id
            ):
                continue
            tool_input = _tool_input(payload, redactor)
            if tool_input is None:
                continue
            pending_tool_ids.add(call_id)
            push(
                _entry(
                    "assistant",
                    _record_uuid(payload, fallback_uuid),
                    timestamp,
                    [{"type": "tool_use", "id": call_id, "name": _trim(name, 128), "input": tool_input}],
                )
            )
        elif kind in ("function_call_output", "custom_tool_call_output"):
            call_id = payload.get("call_id")
            if not isinstance(call_id, str) or call_id not in pending_tool_ids:
                continue
            pending_tool_ids.discard(call_id)
            output = redactor.clean(_trim(_tool_output(payload), MAX_TOOL_OUTPUT_CHARS))
            if output is None:
                output = "[output withheld: matched the secret scanner]"
            push(
                _entry(
                    "user",
                    _record_uuid(payload, fallback_uuid),
                    timestamp,
                    [{"type": "tool_result", "tool_use_id": call_id, "content": output}],
                )
            )
        # reasoning, agent_message, developer messages, and every other kind are omitted.

    if not opener_written:
        raise SessionHistoryError("rollout carries no response items")

    lines = []
    for entry in entries:
        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(line) > MAX_ENTRY_BYTES:
            continue
        lines.append(line)
    content = b"\n".join(lines) + b"\n"
    if len(content) > MAX_HISTORY_BYTES:
        # Shrink tool results first, oldest first, then drop trailing entries.
        shrunk = []
        for line in lines:
            entry = json.loads(line)
            message_content = entry["message"]["content"]
            if isinstance(message_content, list) and message_content and message_content[0].get("type") == "tool_result":
                message_content[0]["content"] = _trim(message_content[0]["content"], 1024)
            shrunk.append(json.dumps(entry, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        lines = shrunk
        content = b"\n".join(lines) + b"\n"
        while lines and len(content) > MAX_HISTORY_BYTES:
            lines.pop()
            content = b"\n".join(lines) + b"\n"
    if not lines:
        raise SessionHistoryError("no history record survived redaction")
    return content


def thread_id_for_run(host_state_root: Path) -> Optional[str]:
    """The main Codex thread of a run, from its private session checkpoint."""

    path = Path(host_state_root) / "codex-session.json"
    try:
        if path.is_symlink() or not path.is_file():
            return None
        document = json.loads(path.read_bytes().decode("utf-8"))
    except (OSError, UnicodeError, ValueError):
        return None
    thread_id = document.get("thread_id") if isinstance(document, Mapping) else None
    if isinstance(thread_id, str) and _THREAD_ID.fullmatch(thread_id):
        return thread_id
    return None


def run_session_history(
    host_state_root: Path,
    *,
    workspace_root: Path,
    opener_text: str,
    opener_uuid: str,
    sessions_root: Optional[Path] = None,
) -> Optional[bytes]:
    """Build the run's history, or ``None`` when its rollout cannot be found."""

    thread_id = thread_id_for_run(host_state_root)
    if thread_id is None:
        return None
    rollout = find_rollout(thread_id, sessions_root)
    if rollout is None:
        return None
    return build_conversation(
        rollout,
        opener_text=opener_text,
        opener_uuid=opener_uuid,
        workspace_root=workspace_root,
    )


__all__ = [
    "MAX_HISTORY_BYTES",
    "MAX_HISTORY_ENTRIES",
    "MAX_HISTORY_TURNS",
    "SESSION_HISTORY_NAME",
    "Redactor",
    "SessionHistoryError",
    "build_conversation",
    "codex_sessions_root",
    "strip_harness_envelopes",
    "find_rollout",
    "run_session_history",
    "thread_id_for_run",
]
