"""Read bounded, native-owned usage records without retaining conversation text.

This versioned local adapter is a compatibility bridge for codex exec, whose
JSONL output exposes usage only at turn completion. It is not a billing API.
Only session ancestry, model context and native token_count records are used.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import stat
import time
import uuid

from workshop.errors import ContractError
from workshop.runtime._compacted_usage import InvalidRecord, consume_compacted_record

MAX_LINE_BYTES = 4 * 1024 * 1024
MINIMUM_SUPPORTED_VERSION = (0, 153, 4)
_IDENTITY_READ_ATTEMPTS = 3
_IDENTITY_RETRY_DELAY_SECONDS = 0.05
COUNTERS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens",
)


class UsageUnavailable(ContractError):
    """Usage cannot safely be attributed; never interpret this as zero."""


class UsageNotReady(UsageUnavailable):
    """The native root identity has not been materialized yet; no usage claim."""


def supports_rollout_usage_version(version):
    """Return whether this CLI is new enough for the validated rollout shape.

    The reader still validates every identity, boundary, and counter field, so
    a future incompatible rollout fails closed at the schema boundary.
    """
    if not isinstance(version, str):
        return False
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[-+][A-Za-z0-9.-]+)?", version)
    return bool(
        match
        and tuple(int(part) for part in match.groups()) >= MINIMUM_SUPPORTED_VERSION
    )
class _IncompleteIdentity(UsageUnavailable):
    """The first metadata record may still be in its native append."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise UsageUnavailable("duplicate native usage JSON key")
        result[key] = value
    return result


def _records(path):
    """Stream a file-size snapshot; bound individual records, not run length."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise UsageUnavailable("native usage file exceeds safe bounds")
            remaining = info.st_size
            while remaining:
                line = stream.readline(min(MAX_LINE_BYTES + 1, remaining))
                if not line:
                    raise UsageUnavailable("native usage file shrank during read")
                remaining -= len(line)
                if len(line) > MAX_LINE_BYTES:
                    # Native compaction can copy a large history into one line.
                    # Validate its framing without retaining that history or
                    # counting embedded old notifications as new consumption.
                    try:
                        value, remaining = consume_compacted_record(
                            line, stream, remaining
                        )
                    except InvalidRecord as exc:
                        raise UsageUnavailable(str(exc)) from exc
                    if value is None:
                        break
                    yield value
                    continue
                if not line.endswith(b"\n"):
                    if remaining == 0:
                        break
                    raise UsageUnavailable("native usage record is incomplete")
                value = json.loads(line, object_pairs_hook=_object)
                if not isinstance(value, dict):
                    raise UsageUnavailable("invalid native usage record")
                yield value
    except (OSError, ValueError, UnicodeError) as exc:
        raise UsageUnavailable("native usage file is unavailable or malformed") from exc


def _identity(path):
    """Read a bounded identity before deciding whose body may be inspected.

    Discovery needs only the first metadata record, regardless of body size.
    Only the root and ancestry-bound descendants are streamed by _records,
    which preserves record bounds without an aggregate file-size cap.
    """
    for attempt in range(_IDENTITY_READ_ATTEMPTS):
        try:
            return _read_identity(path)
        except _IncompleteIdentity:
            # A rollout can become visible before its first append completes.
            # Reopen a fresh snapshot, never omit the unidentified candidate.
            # Persistent incompleteness and every other invalid identity fail.
            if attempt == _IDENTITY_READ_ATTEMPTS - 1:
                raise
            time.sleep(_IDENTITY_RETRY_DELAY_SECONDS)


def _read_identity(path):
    """Read and validate one snapshot of the first metadata record."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise UsageUnavailable("native usage file exceeds safe bounds")
            line = stream.readline(min(MAX_LINE_BYTES + 1, info.st_size))
            if len(line) > MAX_LINE_BYTES:
                raise UsageUnavailable("native session metadata exceeds safe bounds")
            if not line.endswith(b"\n"):
                raise _IncompleteIdentity("native usage file lacks session identity")
            record = json.loads(line, object_pairs_hook=_object)
    except (OSError, ValueError, UnicodeError) as exc:
        raise UsageUnavailable("native usage file is unavailable or malformed") from exc
    if not isinstance(record, dict) or record.get("type") != "session_meta":
        raise UsageUnavailable("native usage file lacks session identity")
    payload = record.get("payload")
    if not isinstance(payload, dict):
        raise UsageUnavailable("invalid native session metadata")
    return payload


def _counters(value):
    if not isinstance(value, dict):
        raise UsageUnavailable("native token counters are missing")
    result = {key: value.get(key) for key in COUNTERS}
    if any(type(v) is not int or not 0 <= v <= 10**12 for v in result.values()):
        raise UsageUnavailable("invalid native token counters")
    if (
        result["cached_input_tokens"] + result["cache_write_input_tokens"] > result["input_tokens"]
        or result["reasoning_output_tokens"] > result["output_tokens"]
    ):
        raise UsageUnavailable("inconsistent native token counters")
    return result


def read_thread_usage(path, *, thread_id, workspace):
    identity = _identity(path)
    if identity.get("id") != thread_id or identity.get("cwd") != str(workspace):
        raise UsageUnavailable("native usage session binding differs")
    if not supports_rollout_usage_version(identity.get("cli_version")):
        raise UsageUnavailable("native rollout usage version is not validated")
    totals = {key: 0 for key in COUNTERS}
    task_totals = None
    task_start = False
    tasks = set()
    model = None
    models = set()
    observations = 0
    last_at = None
    for record in _records(path):
        payload = record.get("payload")
        if not isinstance(payload, dict):
            continue
        if record.get("type") == "turn_context":
            model = payload.get("model")
        if record.get("type") == "event_msg" and payload.get("type") == "task_started":
            turn_id = payload.get("turn_id")
            if not isinstance(turn_id, str) or not turn_id or turn_id in tasks:
                raise UsageUnavailable("ambiguous native usage task boundary")
            tasks.add(turn_id)
            task_start = True
        if record.get("type") != "event_msg" or payload.get("type") != "token_count":
            continue
        info = payload.get("info")
        if info is None:  # Rate-limit-only notification carries no token usage.
            continue
        if not isinstance(info, dict) or not isinstance(model, str) or not 1 <= len(model) <= 128:
            raise UsageUnavailable("native usage model or counters are unsupported")
        current = _counters(info.get("total_token_usage"))
        if not tasks:
            raise UsageUnavailable("native usage lacks a task boundary")
        if task_start:
            # exec 0.153.4+ resets counters on process resume, but a continued
            # task in the same process (including a child follow-up) retains
            # them. Require an exact first-request baseline for either case;
            # never infer a reset merely from a decreasing counter.
            last = _counters(info.get("last_token_usage"))
            if current == last:
                task_totals = {key: 0 for key in COUNTERS}
            elif task_totals is None or any(
                current[key] != task_totals[key] + last[key] for key in COUNTERS
            ):
                raise UsageUnavailable("native usage task baseline is ambiguous")
            task_start = False
        delta = {key: current[key] - task_totals[key] for key in COUNTERS}
        if any(v < 0 for v in delta.values()):
            raise UsageUnavailable("native token counters regressed")
        _counters(delta)
        totals = {key: totals[key] + delta[key] for key in COUNTERS}
        task_totals = current
        models.add(model)
        observations += 1
        last_at = record.get("timestamp")
    return {
        "thread_id": thread_id, "models": sorted(models), "tokens": totals,
        "last_observed_at": last_at,
        "status": "observed" if observations else "pending",
    }


def read_product_usage(sessions_root, *, thread_id, workspace):
    """Read only this root and ancestry-bound descendants from native rollouts.

    Candidate discovery reads session metadata only, beginning on the root
    UUIDv7's creation date. Unrelated conversation payloads are never parsed.
    """
    try:
        identifier = uuid.UUID(thread_id)
        if str(identifier) != thread_id or identifier.version != 7:
            raise ValueError()
        day = datetime.fromtimestamp((identifier.int >> 80) / 1000, timezone.utc).date()
    except (ValueError, TypeError, OverflowError) as exc:
        raise UsageUnavailable("native root thread id is invalid") from exc
    root = Path(sessions_root)
    if root.is_symlink() or not root.is_dir():
        raise UsageUnavailable("native session directory is unavailable")
    candidates = {}
    for path in root.glob("*/*/*/rollout-*.jsonl"):
        try:
            path_day = datetime.strptime("/".join(path.parts[-4:-1]), "%Y/%m/%d").date()
        except ValueError:
            continue
        if path_day < day - timedelta(days=1):
            continue
        if any(p.is_symlink() for p in (path, path.parent, path.parent.parent, path.parent.parent.parent)):
            raise UsageUnavailable("linked native session paths are forbidden")
        meta = _identity(path)
        candidate_id = meta.get("id")
        if not isinstance(candidate_id, str):
            raise UsageUnavailable("ambiguous native session identity")
        source = meta.get("source")
        parent = None
        if isinstance(source, dict):
            subagent = source.get("subagent", {})
            if isinstance(subagent, dict):
                spawn = subagent.get("thread_spawn", {})
                if isinstance(spawn, dict):
                    parent = spawn.get("parent_thread_id")
        # Codex Desktop can retain multiple rollout generations for an
        # unrelated logical thread. Keep them grouped until ancestry is known;
        # a duplicate inside the selected product tree still fails closed.
        candidates.setdefault(candidate_id, []).append((path, parent))
    if thread_id not in candidates:
        raise UsageNotReady("native root usage is not available yet")
    selected = {thread_id}
    while True:
        expanded = selected | {
            candidate_id
            for candidate_id, records in candidates.items()
            if any(parent in selected for _, parent in records)
        }
        if expanded == selected:
            break
        selected = expanded
    if any(len(candidates[candidate_id]) != 1 for candidate_id in selected):
        raise UsageUnavailable("ambiguous native session identity")
    threads = [
        read_thread_usage(
            candidates[candidate_id][0][0],
            thread_id=candidate_id,
            workspace=workspace,
        )
        for candidate_id in sorted(selected)
    ]
    return {
        "schema_version": 1, "source": "codex-native-rollout-v1",
        "status": "observed", "root_thread_id": thread_id,
        "coverage": "completed requests in discovered root and descendant rollouts; in-flight usage excluded",
        "threads": threads,
        "tokens": {key: sum(t["tokens"][key] for t in threads) for key in COUNTERS},
        "total_tokens": sum(t["tokens"]["input_tokens"] + t["tokens"]["output_tokens"] for t in threads),
    }
