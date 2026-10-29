"""The status record: what a run publishes about itself.

ADVISORY DECORATION ONLY. The ready/generating/error state machine is driven by the lock
and nothing here. That separation is deliberate: a status file is written data with no
liveness guarantee, and inferring "a build is running" from one reintroduces exactly the
stale-heartbeat failure the flock replaced.

The record is never unlinked. Unlinking would race: a reader mid-read would see the file
vanish. Its terminal payload carries ``stageMs``, the run's measured per-phase durations --
kept as a record of what the run cost (the CLI prints it), NOT as an input to anything.
Nothing predicts the next build from the last one any more; each phase reports itself.

**Run attribution.** A record carries the id of the run that wrote it, because a record left
behind by a SIGKILLed run is otherwise indistinguishable from the live one. A reader should
accept a record only when its ``runId`` matches the run id stamped in the sentinel by the
current holder.

**Schema v3 reports each phase on its own:** its position in the run (``index``/``count``)
and either a real fraction (``done``/``total``) or a ``detail`` label naming the sub-unit in
flight.

``stageMs`` is written ONLY on ``outcome == "done"``: partial times from a killed run are
not durations anyone should print.
"""

from __future__ import annotations

import contextlib
import json
import os
import socket
import time
from pathlib import Path
from typing import Any, Mapping

# Stdlib-only, like everything in this package.
from cadgen._internal.atomic_replace import replace_atomic, temp_suffix

SCHEMA_VERSION = 3

OUTCOME_RUNNING = None
OUTCOME_DONE = "done"
OUTCOME_FAILED = "failed"
OUTCOME_SKIPPED = "skipped"

INTENT_WRITE = "write"
INTENT_GENERATE = "generate"


def _host() -> str:
    try:
        return socket.gethostname()
    except OSError:  # pragma: no cover - hostname lookup effectively never fails
        return ""


def build_record(
    *,
    run_id: str,
    kind: str,
    intent: str,
    started_at_ms: float,
    outcome: str | None = None,
    progress: Mapping[str, Any] | None = None,
    stage_ms: Mapping[str, float] | None = None,
) -> dict[str, Any]:
    """One status payload. ``progress`` is the phase/ratio block, absent for a bare
    ``starting`` record; ``stage_ms`` is attached only by a successful terminal write."""
    record: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "runId": run_id,
        "pid": os.getpid(),
        "host": _host(),
        "kind": kind,
        "intent": intent,
        "startedAt": round(started_at_ms),
        "outcome": outcome,
        "updatedAt": round(time.time() * 1000.0),
    }
    if progress:
        record.update(progress)
    record["stageMs"] = (
        {str(k): round(float(v)) for k, v in stage_ms.items()} if stage_ms else None
    )
    return record


def write_record(path: Path | str, record: Mapping[str, Any]) -> bool:
    """Atomically publish ``record``. Returns False when the write was not possible.

    Temp file + ``os.replace`` so a poller never reads a half-written payload. The temp
    name carries the pid so two processes cannot clobber each other's temp file. Every
    failure is swallowed: an unwritable ``__cadgen__`` must degrade to "no status
    reported", never to a failed build.
    """
    target = Path(path)
    temp_path = target.with_name(f"{target.name}{temp_suffix()}")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        temp_path.write_text(json.dumps(record, separators=(",", ":")), encoding="utf-8")
        replace_atomic(temp_path, target)
        return True
    except OSError:
        with contextlib.suppress(OSError):
            temp_path.unlink(missing_ok=True)
        return False
