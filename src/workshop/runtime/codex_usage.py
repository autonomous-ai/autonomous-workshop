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
import uuid

from workshop.errors import ContractError
from workshop.runtime._compacted_usage import InvalidRecord, consume_compacted_record

MAX_LINE_BYTES = 4 * 1024 * 1024
MINIMUM_SUPPORTED_VERSION = (0, 153, 4)
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
                    # Native compaction can copy a large history into one line,
                    # and visual tool results can embed image data. Validate
                    # their framing without retaining either body or counting
                    # embedded old notifications as new consumption.
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
                raise UsageUnavailable("native usage file lacks session identity")
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


def _read_notification_usage(path, *, thread_id, workspace):
    identity = _identity(path)
    if identity.get("id") != thread_id or identity.get("cwd") != str(workspace):
        raise UsageUnavailable("native usage session binding differs")
    if not supports_rollout_usage_version(identity.get("cli_version")):
        raise UsageUnavailable("native rollout usage version is not validated")
    totals = {key: 0 for key in COUNTERS}
    task_totals = None
    previous_last = None
    previous_model = None
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
        last = _counters(info.get("last_token_usage"))
        if not tasks:
            raise UsageUnavailable("native usage lacks a task boundary")
        if task_start:
            # A follow-up may replay the preceding task's final snapshot before
            # any new request. Preserve the pending boundary so the first fresh
            # observation still has to prove continuation or a process reset.
            # total == last remains the reset case, even if its values happen
            # to match an earlier single-request task; never discard that usage.
            if (
                current == task_totals and last == previous_last
                and model == previous_model and current != last
            ):
                continue
            # exec 0.153.4+ resets counters on process resume, but a continued
            # task in the same process (including a child follow-up) retains
            # them. Require an exact first-request baseline for either case;
            # never infer a reset merely from a decreasing counter.
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
        previous_last = last
        previous_model = model
        models.add(model)
        observations += 1
        last_at = record.get("timestamp")
    return {
        "thread_id": thread_id, "models": sorted(models), "tokens": totals,
        "last_observed_at": last_at,
        "status": "observed" if observations else "pending",
    }


def _native_uuid(value):
    try:
        if not isinstance(value, str) or str(uuid.UUID(value)) != value:
            raise ValueError
    except (ValueError, TypeError, AttributeError) as exc:
        raise UsageUnavailable("native response ledger identity is invalid") from exc
    return value


def _response_counters(value):
    result = _counters(value)
    if (
        set(value) != set(COUNTERS) | {"total_tokens"}
        or type(value["total_tokens"]) is not int
        or value["total_tokens"] != result["input_tokens"] + result["output_tokens"]
    ):
        raise UsageUnavailable("native response ledger total is invalid")
    return result


class _ResponseLedgerUsage:
    """Validate the complete top-level per-response ledger, including compaction.

    Notifications corroborate coverage but never supply spend. Their cumulative
    counters can restore an older native baseline after a process resume.
    """

    def __init__(self, identity):
        self.identity = identity
        self.present = False
        self.responses = {}
        self.totals = {key: 0 for key in COUNTERS}
        self.turn_totals = {}
        self.tasks = set()
        self.task = None
        self.model = None
        self.models = set()
        self.observations = 0
        self.last_at = None
        self.latest_response = None
        self.notification = None
        self.pending_responses = {}
        self.pending_compactions = set()
        self.uncovered_notification = False
        self.compacted_task = None

    def observe(self, record):
        kind = record.get("type")
        payload = record.get("payload")
        if kind == "token_usage_record":
            self.present = True  # Malformed ledger records must never fall back.
            self._response(payload, record.get("timestamp"))
            return
        if kind == "compacted":
            self._compaction(payload)
            return
        if not isinstance(payload, dict):
            return
        if kind == "turn_context":
            self.model = payload.get("model")
        if kind == "event_msg" and payload.get("type") == "task_started":
            turn_id = payload.get("turn_id")
            if not isinstance(turn_id, str) or not turn_id or turn_id in self.tasks:
                raise UsageUnavailable("ambiguous native usage task boundary")
            self.tasks.add(turn_id)
            self.task = turn_id
            self.notification = None
            self.pending_responses = {}
            self.pending_compactions = set()
            self.compacted_task = None
        if kind == "event_msg" and payload.get("type") == "token_count":
            self._notification(payload.get("info"))

    def _response(self, value, timestamp):
        fields = {
            "thread_id", "turn_id", "session_id", "root_turn_id", "response_id",
            "usage", "turn_token_usage", "thread_token_usage",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise UsageUnavailable("native response ledger fields are unsupported")
        for field in ("thread_id", "turn_id", "session_id", "root_turn_id"):
            _native_uuid(value[field])
        if (
            value["thread_id"] != self.identity.get("id")
            or value["session_id"] != self.identity.get("session_id")
            or not isinstance(value["response_id"], str)
            or not 1 <= len(value["response_id"]) <= 256
            or any(ord(char) < 33 or ord(char) > 126 for char in value["response_id"])
        ):
            raise UsageUnavailable("native response ledger session binding differs")
        used = _response_counters(value["usage"])
        turn_total = _response_counters(value["turn_token_usage"])
        thread_total = _response_counters(value["thread_token_usage"])
        previous = self.responses.get(value["response_id"])
        if previous is not None:
            if previous != value:
                raise UsageUnavailable("conflicting native response ledger identity")
            return
        if self.uncovered_notification:
            raise UsageUnavailable("native response ledger lacks earlier notification coverage")
        if (
            value["turn_id"] != self.task
            or not isinstance(self.model, str) or not 1 <= len(self.model) <= 128
        ):
            raise UsageUnavailable("native response ledger task or model binding differs")
        previous_turn = self.turn_totals.get(self.task, {key: 0 for key in COUNTERS})
        if any(
            thread_total[key] != self.totals[key] + used[key]
            or turn_total[key] != previous_turn[key] + used[key]
            for key in COUNTERS
        ):
            raise UsageUnavailable("native response ledger has incomplete or regressing coverage")
        self.responses[value["response_id"]] = value
        self.pending_responses[value["response_id"]] = value
        self.totals = thread_total
        self.turn_totals[self.task] = turn_total
        self.latest_response = value
        self.models.add(self.model)
        self.observations += 1
        self.last_at = timestamp

    def _compaction(self, payload):
        # Only the top-level ledger charges this response. The compacted copy
        # identifies which already charged request was the remote compaction.
        reference = payload.get("latest_token_usage_record") if isinstance(payload, dict) else None
        if not self.present or reference is None:
            return
        if not isinstance(reference, dict) or not isinstance(reference.get("response_id"), str):
            raise UsageUnavailable("native compaction response identity is invalid")
        response_id = reference["response_id"]
        if self.responses.get(response_id) != reference:
            raise UsageUnavailable("native compaction lacks exact response ledger coverage")
        if response_id in self.pending_responses and reference["turn_id"] == self.task:
            self.pending_compactions.add(response_id)
            self.compacted_task = self.task

    def _cover_notification(self, signature):
        self.notification = signature
        self.pending_responses = {}
        self.pending_compactions = set()
        self.compacted_task = None

    def _notification(self, info):
        if info is None:
            return
        if not self.present:
            self.uncovered_notification = True
            return
        if not isinstance(info, dict):
            raise UsageUnavailable("native usage notification is invalid")
        current = _counters(info.get("total_token_usage"))
        last = _counters(info.get("last_token_usage"))
        signature = (self.task, current, last)
        if signature == self.notification:
            return
        ordinary = {
            key: sum(value["usage"][key] for response_id, value in self.pending_responses.items()
                     if response_id not in self.pending_compactions)
            for key in COUNTERS
        }
        if (
            self.compacted_task == self.task and self.task is not None
            and self.notification is not None
            and not any(last.values()) and current == self.notification[1]
            and self.pending_responses and not any(ordinary.values())
        ):
            # A post-compaction context-size notification reports zero usage.
            # Its last.total_tokens is a context estimate, not input + output.
            self._cover_notification(signature)
            return
        if (
            not self.pending_responses
            or self.latest_response is None
            or self.latest_response["turn_id"] != self.task
            or self.latest_response["response_id"] in self.pending_compactions
            or last != _counters(self.latest_response["usage"])
            or any(current[key] < ordinary[key] for key in COUNTERS)
            or (self.notification is not None and any(
                current[key] != self.notification[1][key] + ordinary[key] for key in COUNTERS
            ))
        ):
            raise UsageUnavailable("native usage notification lacks response ledger coverage")
        self._cover_notification(signature)


def read_thread_usage(path, *, thread_id, workspace):
    identity = _identity(path)
    if identity.get("id") != thread_id or identity.get("cwd") != str(workspace):
        raise UsageUnavailable("native usage session binding differs")
    if not supports_rollout_usage_version(identity.get("cli_version")):
        raise UsageUnavailable("native rollout usage version is not validated")
    ledger = _ResponseLedgerUsage(identity)
    for record in _records(path):
        ledger.observe(record)
    if ledger.present:
        result = {
            "thread_id": thread_id, "models": sorted(ledger.models), "tokens": ledger.totals,
            "last_observed_at": ledger.last_at,
            "status": "observed" if ledger.observations else "pending",
            "accounting_source": "response-ledger-v1",
        }
        # Native terminal counters may restore a process-local baseline which
        # differs from lifetime response totals. Expose only an exact snapshot
        # already covered by this ledger, with no later unnotified response.
        if ledger.notification is not None and not ledger.pending_responses:
            result["terminal_notification"] = ledger.notification[1]
        return result
    return _read_notification_usage(path, thread_id=thread_id, workspace=workspace)


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
