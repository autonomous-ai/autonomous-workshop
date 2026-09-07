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
import stat
import uuid

from workshop.errors import ContractError

MAX_LINE_BYTES = 4 * 1024 * 1024
MAX_ROLLOUT_BYTES = 128 * 1024 * 1024
MAX_CANDIDATES = 4096
MAX_THREADS = 32
SUPPORTED_VERSION = "0.153.4"
COUNTERS = (
    "input_tokens", "cached_input_tokens", "cache_write_input_tokens",
    "output_tokens", "reasoning_output_tokens",
)


class UsageUnavailable(ContractError):
    """Usage cannot safely be attributed; never interpret this as zero."""


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise UsageUnavailable("duplicate native usage JSON key")
        result[key] = value
    return result


def _records(path):
    """Ignore only a trailing partial append; reject links and oversized files."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_ROLLOUT_BYTES:
                raise UsageUnavailable("native usage file exceeds safe bounds")
            remaining = info.st_size
            while remaining:
                line = stream.readline(min(MAX_LINE_BYTES + 1, remaining))
                if not line:
                    raise UsageUnavailable("native usage file shrank during read")
                remaining -= len(line)
                if len(line) > MAX_LINE_BYTES:
                    raise UsageUnavailable("native usage record exceeds safe bounds")
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
    record = next(_records(path), None)
    if not record or record.get("type") != "session_meta":
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
    if identity.get("cli_version") != SUPPORTED_VERSION:
        raise UsageUnavailable("native rollout usage version is not validated")
    totals = {key: 0 for key in COUNTERS}
    task_totals = None
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
            task_totals = None
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
        if task_totals is None:
            # exec 0.153.4 resets cumulative counters on process resume. Bind
            # that reset to an explicit native task, never infer one from a
            # decreasing counter (which could conceal lost history).
            if current != _counters(info.get("last_token_usage")):
                raise UsageUnavailable("native usage task baseline is ambiguous")
            task_totals = {key: 0 for key in COUNTERS}
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
    count = 0
    for path in root.glob("*/*/*/rollout-*.jsonl"):
        try:
            path_day = datetime.strptime("/".join(path.parts[-4:-1]), "%Y/%m/%d").date()
        except ValueError:
            continue
        if path_day < day - timedelta(days=1):
            continue
        count += 1
        if count > MAX_CANDIDATES:
            raise UsageUnavailable("native session discovery exceeds safe bounds")
        if any(p.is_symlink() for p in (path, path.parent, path.parent.parent, path.parent.parent.parent)):
            raise UsageUnavailable("linked native session paths are forbidden")
        meta = _identity(path)
        candidate_id = meta.get("id")
        if not isinstance(candidate_id, str) or candidate_id in candidates:
            raise UsageUnavailable("ambiguous native session identity")
        source = meta.get("source")
        parent = None
        if isinstance(source, dict):
            subagent = source.get("subagent", {})
            if isinstance(subagent, dict):
                spawn = subagent.get("thread_spawn", {})
                if isinstance(spawn, dict):
                    parent = spawn.get("parent_thread_id")
        candidates[candidate_id] = (path, parent)
    if thread_id not in candidates:
        raise UsageUnavailable("native root usage is not available yet")
    selected = {thread_id}
    while True:
        expanded = selected | {i for i, (_, parent) in candidates.items() if parent in selected}
        if len(expanded) > MAX_THREADS:
            raise UsageUnavailable("native product ancestry exceeds safe bounds")
        if expanded == selected:
            break
        selected = expanded
    threads = [read_thread_usage(candidates[i][0], thread_id=i, workspace=workspace) for i in sorted(selected)]
    return {
        "schema_version": 1, "source": "codex-native-rollout-v1",
        "status": "observed", "root_thread_id": thread_id,
        "coverage": "completed requests in discovered root and descendant rollouts; in-flight usage excluded",
        "threads": threads,
        "tokens": {key: sum(t["tokens"][key] for t in threads) for key in COUNTERS},
        "total_tokens": sum(t["tokens"]["input_tokens"] + t["tokens"]["output_tokens"] for t in threads),
    }
