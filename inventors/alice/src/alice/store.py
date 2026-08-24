"""Durable, dependency-free SQLite persistence for long-running agents.

The store deliberately keeps orchestration policy out of persistence.  It
provides durable facts, compare-and-set state changes, lease fencing, and an
append-only audit trail; callers decide which candidate transitions or retry
strategies are desirable.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Callable, Iterable, Iterator, Mapping, Sequence
import uuid


ZERO_HASH = "0" * 64
SCHEMA_VERSION = 2

CANDIDATE_STATES = frozenset(
    {
        "proposed",
        "researched",
        "rules_valid",
        "digitally_playtested",
        "human_ready",
        "human_validated",
        "physical_ready",
        "production_validated",
        "page_ready",
        "publish_ready",
        "published",
        "rework",
        "blocked",
        "killed",
        "archived",
    }
)
TASK_STATES = frozenset({"queued", "leased", "succeeded", "failed", "cancelled"})
PUBLICATION_STATES = frozenset(
    {"prepared", "in_flight", "confirmed", "ambiguous", "failed"}
)
PUBLICATION_REMOTE_STATUSES = frozenset({"draft", "publishing", "published"})


class StoreError(RuntimeError):
    """Base error for durable-store operations."""


class StoreClosedError(StoreError):
    """Raised when an operation is attempted after :meth:`DurableStore.close`."""


class NotFoundError(StoreError):
    """Raised when a requested durable record does not exist."""


class StateConflictError(StoreError):
    """Raised when a compare-and-set or state precondition fails."""


class IdempotencyConflictError(StoreError):
    """Raised when an idempotency key is replayed with different input."""


class LeaseLostError(StoreError):
    """Raised when a worker no longer owns the current, unexpired task lease."""


class EventChainError(StoreError):
    """Raised when the append-only event chain fails verification."""


@dataclass(frozen=True, slots=True)
class EventRecord:
    seq: int
    event_id: str
    kind: str
    aggregate_type: str | None
    aggregate_id: str | None
    attempt_id: str | None
    attempt_seq: int | None
    stage: str | None
    input_sha256: str | None
    output_sha256: str | None
    payload: Any
    created_at: float
    prev_hash: str
    event_hash: str

    @property
    def type(self) -> str:
        """Alias useful to consumers that call an event kind its type."""

        return self.kind


@dataclass(frozen=True, slots=True)
class ChainVerification:
    valid: bool
    events_checked: int
    head_seq: int | None
    head_hash: str | None
    error_seq: int | None = None
    error: str | None = None

    def __bool__(self) -> bool:
        return self.valid


@dataclass(frozen=True, slots=True)
class TaskRecord:
    id: str
    idempotency_key: str
    kind: str
    payload: Any
    run_id: str | None
    candidate_id: str | None
    input_sha256: str
    output_sha256: str | None
    state: str
    priority: int
    available_at: float
    created_at: float
    updated_at: float
    attempt_count: int
    max_attempts: int
    lease_owner: str | None
    lease_token: str | None
    lease_attempt_id: str | None
    lease_expires_at: float | None
    last_error_stage: str | None
    last_error_code: str | None
    last_error_message: str | None
    result: Any


@dataclass(frozen=True, slots=True)
class AttemptRecord:
    id: str
    task_id: str
    seq: int
    stage: str
    worker_id: str
    lease_token: str
    input_sha256: str
    output_sha256: str | None
    status: str
    started_at: float
    lease_expires_at: float
    finished_at: float | None
    error_code: str | None
    error_message: str | None
    outcome: Any


@dataclass(frozen=True, slots=True)
class CandidateRecord:
    id: str
    idempotency_key: str | None
    creation_sha256: str
    kind: str
    title: str | None
    content: Any
    state: str
    version: int
    task_id: str | None
    parent_id: str | None
    metadata: Mapping[str, Any]
    created_at: float
    updated_at: float


@dataclass(frozen=True, slots=True)
class CandidateArtifactRecord:
    id: str
    candidate_id: str
    task_id: str
    action: str
    candidate_version: int
    output_sha256: str
    content_sha256: str
    content: Any
    created_at: float


@dataclass(frozen=True, slots=True)
class DerivedApplicationRecord:
    task_id: str
    output_sha256: str
    applied_at: float


@dataclass(frozen=True, slots=True)
class VersionedStateRecord:
    key: str
    value: Any
    version: int
    created_at: float
    updated_at: float


@dataclass(frozen=True, slots=True)
class EvaluationRecord:
    id: str
    idempotency_key: str | None
    candidate_id: str
    evaluator: str
    score: float | None
    verdict: str | None
    metrics: Any
    notes: str | None
    created_at: float


@dataclass(frozen=True, slots=True)
class ExperienceRecord:
    id: str
    idempotency_key: str | None
    kind: str
    content: Any
    reward: float | None
    task_id: str | None
    candidate_id: str | None
    attempt_id: str | None
    created_at: float


@dataclass(frozen=True, slots=True)
class PublicationRecord:
    id: str
    target: str
    idempotency_key: str
    request_sha256: str
    request: Any
    candidate_id: str | None
    state: str
    remote_design_id: str | None
    slug: str | None
    history_id: str | None
    status: str
    project_url: str | None
    response: Any
    last_error: str | None
    created_at: float
    updated_at: float


def _json_dumps(value: Any) -> str:
    """Return stable JSON used both for storage and hashes."""

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def _json_loads(value: str | None) -> Any:
    return None if value is None else json.loads(value)


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_sha256(value: str, name: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{name} must be a 64-character lowercase SHA-256 hex digest")
    if value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{name} must be a 64-character lowercase SHA-256 hex digest")
    return value


def _require_text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def _limit(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValueError("limit must be a positive integer")
    return value


def _candidate_publish_effect_key(candidate_id: str, candidate_version: int) -> str:
    return f"alice.effect:candidate:{candidate_id}:v{candidate_version}:publish"


_CANDIDATE_PHYSICAL_EFFECT_ACTIONS = frozenset(
    {"physical.cad", "physical.prototype_print", "physical.production_run"}
)


def _manufacturing_job_binding_key(job_id: str) -> str:
    return f"alice.manufacturing-job:{_sha256_text(job_id)}"


class DurableStore:
    """A serialized SQLite store safe to reopen from multiple processes.

    Every mutation uses ``BEGIN IMMEDIATE``.  This makes task selection and
    lease acquisition one indivisible operation even when several store
    instances or processes share the database.  A store instance also guards
    its connection with an ``RLock`` so it can be shared by application
    threads.
    """

    def __init__(
        self,
        path: str | Path,
        *,
        clock: Callable[[], float] = time.time,
        busy_timeout_ms: int = 10_000,
    ) -> None:
        if busy_timeout_ms <= 0:
            raise ValueError("busy_timeout_ms must be positive")
        raw_path = str(path)
        self.path = (
            raw_path
            if raw_path == ":memory:"
            else str(Path(raw_path).expanduser().resolve())
        )
        self._clock = clock
        self._lock = threading.RLock()
        self._closed = False

        if self.path != ":memory:":
            parent = Path(self.path).parent
            parent_existed = parent.exists()
            parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            # Never change permissions on a caller-owned existing directory
            # (which could be /tmp or a shared volume). A runtime directory
            # created by Alice itself is private from its first use.
            if not parent_existed:
                os.chmod(parent, 0o700)

        self._conn = sqlite3.connect(
            self.path,
            timeout=busy_timeout_ms / 1000,
            isolation_level=None,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(f"PRAGMA busy_timeout = {int(busy_timeout_ms)}")
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._journal_mode = str(self._conn.execute("PRAGMA journal_mode = WAL").fetchone()[0])
        self._conn.execute("PRAGMA synchronous = FULL")
        self._conn.execute("PRAGMA wal_autocheckpoint = 1000")
        self._initialize_schema()
        self._harden_database_permissions()

    @property
    def journal_mode(self) -> str:
        return self._journal_mode.lower()

    def __enter__(self) -> DurableStore:
        self._ensure_open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        with self._lock:
            if not self._closed:
                self._conn.close()
                self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise StoreClosedError("the durable store is closed")

    def _now(self, value: float | None) -> float:
        result = float(self._clock() if value is None else value)
        if result != result or result in (float("inf"), float("-inf")):
            raise ValueError("timestamp must be finite")
        return result

    @contextmanager
    def _write(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._ensure_open()
            self._conn.execute("BEGIN IMMEDIATE")
            try:
                yield self._conn
            except BaseException:
                self._conn.rollback()
                raise
            else:
                self._conn.commit()
                self._harden_database_permissions()

    def _harden_database_permissions(self) -> None:
        if self.path == ":memory:":
            return
        for suffix in ("", "-wal", "-shm"):
            candidate = Path(self.path + suffix)
            if candidate.exists():
                os.chmod(candidate, 0o600)

    @contextmanager
    def _read(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            self._ensure_open()
            self._conn.execute("BEGIN")
            try:
                yield self._conn
            except BaseException:
                self._conn.rollback()
                raise
            else:
                self._conn.commit()

    def _initialize_schema(self) -> None:
        candidate_states = ",".join(f"'{state}'" for state in sorted(CANDIDATE_STATES))
        task_states = ",".join(f"'{state}'" for state in sorted(TASK_STATES))
        publication_states = ",".join(f"'{state}'" for state in sorted(PUBLICATION_STATES))
        script = f"""
        BEGIN IMMEDIATE;

        CREATE TABLE IF NOT EXISTS store_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS event_chain_state (
            singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
            event_count INTEGER NOT NULL CHECK (event_count >= 0),
            head_seq INTEGER,
            head_hash TEXT
        );

        CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY,
            event_id TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,
            aggregate_type TEXT,
            aggregate_id TEXT,
            attempt_id TEXT,
            attempt_seq INTEGER,
            stage TEXT,
            input_sha256 TEXT,
            output_sha256 TEXT,
            payload_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            prev_hash TEXT NOT NULL,
            event_hash TEXT NOT NULL UNIQUE
        );

        CREATE TRIGGER IF NOT EXISTS events_forbid_update
        BEFORE UPDATE ON events BEGIN
            SELECT RAISE(ABORT, 'events are append-only');
        END;

        CREATE TRIGGER IF NOT EXISTS events_forbid_delete
        BEFORE DELETE ON events BEGIN
            SELECT RAISE(ABORT, 'events are append-only');
        END;

        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            run_id TEXT,
            candidate_id TEXT,
            input_sha256 TEXT NOT NULL,
            output_sha256 TEXT,
            state TEXT NOT NULL CHECK (state IN ({task_states})),
            priority INTEGER NOT NULL,
            available_at REAL NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            attempt_count INTEGER NOT NULL DEFAULT 0 CHECK (attempt_count >= 0),
            max_attempts INTEGER NOT NULL CHECK (max_attempts > 0),
            lease_owner TEXT,
            lease_token TEXT,
            lease_attempt_id TEXT,
            lease_expires_at REAL,
            last_error_stage TEXT,
            last_error_code TEXT,
            last_error_message TEXT,
            result_json TEXT,
            CHECK (
                (state = 'leased' AND lease_owner IS NOT NULL AND lease_token IS NOT NULL
                    AND lease_attempt_id IS NOT NULL AND lease_expires_at IS NOT NULL)
                OR
                (state <> 'leased' AND lease_owner IS NULL AND lease_token IS NULL
                    AND lease_attempt_id IS NULL AND lease_expires_at IS NULL)
            )
        );

        CREATE INDEX IF NOT EXISTS tasks_ready_idx
            ON tasks(state, available_at, priority DESC, created_at, id);
        CREATE INDEX IF NOT EXISTS tasks_kind_ready_idx
            ON tasks(kind, state, available_at, priority DESC, created_at, id);
        CREATE INDEX IF NOT EXISTS tasks_run_idx ON tasks(run_id, state);
        CREATE INDEX IF NOT EXISTS tasks_candidate_idx ON tasks(candidate_id, state);
        CREATE INDEX IF NOT EXISTS tasks_lease_expiry_idx ON tasks(state, lease_expires_at);
        CREATE INDEX IF NOT EXISTS tasks_state_created_idx
            ON tasks(state, created_at, id);

        CREATE TABLE IF NOT EXISTS task_attempts (
            id TEXT PRIMARY KEY,
            task_id TEXT NOT NULL REFERENCES tasks(id),
            seq INTEGER NOT NULL CHECK (seq > 0),
            stage TEXT NOT NULL,
            worker_id TEXT NOT NULL,
            lease_token TEXT NOT NULL UNIQUE,
            input_sha256 TEXT NOT NULL,
            output_sha256 TEXT,
            status TEXT NOT NULL CHECK (
                status IN ('leased', 'succeeded', 'failed', 'expired', 'cancelled')
            ),
            started_at REAL NOT NULL,
            lease_expires_at REAL NOT NULL,
            finished_at REAL,
            error_code TEXT,
            error_message TEXT,
            outcome_json TEXT,
            UNIQUE(task_id, seq)
        );

        CREATE INDEX IF NOT EXISTS attempts_task_idx ON task_attempts(task_id, seq);
        CREATE INDEX IF NOT EXISTS attempts_status_idx ON task_attempts(status, lease_expires_at);

        CREATE TABLE IF NOT EXISTS candidates (
            id TEXT PRIMARY KEY,
            idempotency_key TEXT UNIQUE,
            creation_sha256 TEXT NOT NULL,
            kind TEXT NOT NULL,
            title TEXT,
            content_json TEXT NOT NULL,
            state TEXT NOT NULL CHECK (state IN ({candidate_states})),
            version INTEGER NOT NULL DEFAULT 1 CHECK (version > 0),
            task_id TEXT,
            parent_id TEXT REFERENCES candidates(id),
            metadata_json TEXT NOT NULL,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE INDEX IF NOT EXISTS candidates_state_idx
            ON candidates(state, updated_at DESC, id);
        CREATE INDEX IF NOT EXISTS candidates_kind_state_idx
            ON candidates(kind, state, updated_at DESC, id);

        CREATE TABLE IF NOT EXISTS candidate_artifacts (
            id TEXT PRIMARY KEY,
            candidate_id TEXT NOT NULL REFERENCES candidates(id),
            task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id),
            action TEXT NOT NULL,
            candidate_version INTEGER NOT NULL CHECK (candidate_version > 0),
            output_sha256 TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at REAL NOT NULL
        );

        CREATE INDEX IF NOT EXISTS candidate_artifacts_candidate_idx
            ON candidate_artifacts(candidate_id, candidate_version, action, created_at, id);
        CREATE INDEX IF NOT EXISTS candidate_artifacts_content_idx
            ON candidate_artifacts(content_sha256, candidate_id);

        CREATE TRIGGER IF NOT EXISTS candidate_artifacts_forbid_update
        BEFORE UPDATE ON candidate_artifacts BEGIN
            SELECT RAISE(ABORT, 'candidate artifacts are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS candidate_artifacts_forbid_delete
        BEFORE DELETE ON candidate_artifacts BEGIN
            SELECT RAISE(ABORT, 'candidate artifacts are immutable');
        END;

        CREATE TABLE IF NOT EXISTS task_derived_applications (
            task_id TEXT PRIMARY KEY REFERENCES tasks(id),
            output_sha256 TEXT NOT NULL,
            applied_at REAL NOT NULL
        ) WITHOUT ROWID;

        CREATE INDEX IF NOT EXISTS task_derived_output_idx
            ON task_derived_applications(output_sha256, applied_at);

        CREATE TRIGGER IF NOT EXISTS task_derived_applications_forbid_update
        BEFORE UPDATE ON task_derived_applications BEGIN
            SELECT RAISE(ABORT, 'derived application markers are immutable');
        END;

        CREATE TRIGGER IF NOT EXISTS task_derived_applications_forbid_delete
        BEFORE DELETE ON task_derived_applications BEGIN
            SELECT RAISE(ABORT, 'derived application markers are immutable');
        END;

        CREATE TABLE IF NOT EXISTS versioned_state (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            version INTEGER NOT NULL CHECK (version > 0),
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        ) WITHOUT ROWID;

        CREATE TABLE IF NOT EXISTS evaluations (
            id TEXT PRIMARY KEY,
            idempotency_key TEXT UNIQUE,
            candidate_id TEXT NOT NULL REFERENCES candidates(id),
            evaluator TEXT NOT NULL,
            score REAL,
            verdict TEXT,
            metrics_json TEXT NOT NULL,
            notes TEXT,
            created_at REAL NOT NULL
        );

        CREATE INDEX IF NOT EXISTS evaluations_candidate_idx
            ON evaluations(candidate_id, created_at, id);

        CREATE TABLE IF NOT EXISTS experiences (
            id TEXT PRIMARY KEY,
            idempotency_key TEXT UNIQUE,
            kind TEXT NOT NULL,
            content_json TEXT NOT NULL,
            reward REAL,
            task_id TEXT REFERENCES tasks(id),
            candidate_id TEXT REFERENCES candidates(id),
            attempt_id TEXT REFERENCES task_attempts(id),
            created_at REAL NOT NULL
        );

        CREATE INDEX IF NOT EXISTS experiences_kind_idx ON experiences(kind, created_at, id);
        CREATE INDEX IF NOT EXISTS experiences_candidate_idx
            ON experiences(candidate_id, created_at, id);

        CREATE TABLE IF NOT EXISTS publications (
            id TEXT PRIMARY KEY,
            target TEXT NOT NULL,
            idempotency_key TEXT NOT NULL,
            request_sha256 TEXT NOT NULL,
            request_json TEXT NOT NULL,
            candidate_id TEXT REFERENCES candidates(id),
            state TEXT NOT NULL CHECK (state IN ({publication_states})),
            remote_design_id TEXT,
            slug TEXT,
            history_id TEXT,
            status TEXT NOT NULL DEFAULT 'draft'
                CHECK (status IN ('draft', 'publishing', 'published')),
            project_url TEXT,
            response_json TEXT,
            last_error TEXT,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            UNIQUE(target, idempotency_key)
        );

        CREATE INDEX IF NOT EXISTS publications_candidate_idx
            ON publications(candidate_id, created_at, id);
        CREATE INDEX IF NOT EXISTS publications_state_idx
            ON publications(state, updated_at, id);

        INSERT OR IGNORE INTO store_meta(key, value)
            VALUES ('schema_version', '{SCHEMA_VERSION}');
        INSERT OR IGNORE INTO event_chain_state(singleton, event_count, head_seq, head_hash)
            VALUES (1, 0, NULL, NULL);

        COMMIT;
        """
        try:
            self._conn.executescript(script)
        except BaseException:
            if self._conn.in_transaction:
                self._conn.rollback()
            self._conn.close()
            self._closed = True
            raise

        stored = self._conn.execute(
            "SELECT value FROM store_meta WHERE key = 'schema_version'"
        ).fetchone()
        try:
            stored_version = None if stored is None else int(stored[0])
        except (TypeError, ValueError):
            stored_version = None
        if stored_version is None or stored_version < 1 or stored_version > SCHEMA_VERSION:
            self.close()
            raise StoreError(
                f"unsupported schema version {None if stored is None else stored[0]!r}"
            )
        if stored_version < SCHEMA_VERSION:
            self._migrate_schema(stored_version)
        else:
            self._conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _migrate_schema(self, stored_version: int) -> None:
        """Apply additive, restart-safe migrations from a supported old store."""

        if stored_version != 1 or SCHEMA_VERSION != 2:
            self.close()
            raise StoreError(
                f"no migration path from schema version {stored_version} to {SCHEMA_VERSION}"
            )
        script = f"""
        BEGIN IMMEDIATE;

        CREATE INDEX IF NOT EXISTS tasks_state_created_idx
            ON tasks(state, created_at, id);

        CREATE TABLE IF NOT EXISTS candidate_artifacts (
            id TEXT PRIMARY KEY,
            candidate_id TEXT NOT NULL REFERENCES candidates(id),
            task_id TEXT NOT NULL UNIQUE REFERENCES tasks(id),
            action TEXT NOT NULL,
            candidate_version INTEGER NOT NULL CHECK (candidate_version > 0),
            output_sha256 TEXT NOT NULL,
            content_sha256 TEXT NOT NULL,
            content_json TEXT NOT NULL,
            created_at REAL NOT NULL
        );
        CREATE INDEX IF NOT EXISTS candidate_artifacts_candidate_idx
            ON candidate_artifacts(candidate_id, candidate_version, action, created_at, id);
        CREATE INDEX IF NOT EXISTS candidate_artifacts_content_idx
            ON candidate_artifacts(content_sha256, candidate_id);
        CREATE TRIGGER IF NOT EXISTS candidate_artifacts_forbid_update
        BEFORE UPDATE ON candidate_artifacts BEGIN
            SELECT RAISE(ABORT, 'candidate artifacts are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS candidate_artifacts_forbid_delete
        BEFORE DELETE ON candidate_artifacts BEGIN
            SELECT RAISE(ABORT, 'candidate artifacts are immutable');
        END;

        CREATE TABLE IF NOT EXISTS task_derived_applications (
            task_id TEXT PRIMARY KEY REFERENCES tasks(id),
            output_sha256 TEXT NOT NULL,
            applied_at REAL NOT NULL
        ) WITHOUT ROWID;
        CREATE INDEX IF NOT EXISTS task_derived_output_idx
            ON task_derived_applications(output_sha256, applied_at);
        CREATE TRIGGER IF NOT EXISTS task_derived_applications_forbid_update
        BEFORE UPDATE ON task_derived_applications BEGIN
            SELECT RAISE(ABORT, 'derived application markers are immutable');
        END;
        CREATE TRIGGER IF NOT EXISTS task_derived_applications_forbid_delete
        BEFORE DELETE ON task_derived_applications BEGIN
            SELECT RAISE(ABORT, 'derived application markers are immutable');
        END;

        CREATE TABLE IF NOT EXISTS versioned_state (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            version INTEGER NOT NULL CHECK (version > 0),
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        ) WITHOUT ROWID;

        UPDATE store_meta SET value = '{SCHEMA_VERSION}' WHERE key = 'schema_version';
        PRAGMA user_version = {SCHEMA_VERSION};
        COMMIT;
        """
        try:
            self._conn.executescript(script)
        except BaseException:
            if self._conn.in_transaction:
                self._conn.rollback()
            self._conn.close()
            self._closed = True
            raise

    @staticmethod
    def canonical_json(value: Any) -> str:
        return _json_dumps(value)

    @staticmethod
    def sha256_json(value: Any) -> str:
        return _sha256_text(_json_dumps(value))

    @staticmethod
    def _event_digest(
        seq: int,
        event_id: str,
        kind: str,
        aggregate_type: str | None,
        aggregate_id: str | None,
        attempt_id: str | None,
        attempt_seq: int | None,
        stage: str | None,
        input_sha256: str | None,
        output_sha256: str | None,
        payload_json: str,
        created_at: float,
        prev_hash: str,
    ) -> str:
        material = _json_dumps(
            [
                1,
                seq,
                event_id,
                kind,
                aggregate_type,
                aggregate_id,
                attempt_id,
                attempt_seq,
                stage,
                input_sha256,
                output_sha256,
                payload_json,
                created_at,
                prev_hash,
            ]
        )
        return _sha256_text(material)

    def _append_event_tx(
        self,
        conn: sqlite3.Connection,
        kind: str,
        payload: Any,
        *,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        attempt_id: str | None = None,
        attempt_seq: int | None = None,
        stage: str | None = None,
        input_sha256: str | None = None,
        output_sha256: str | None = None,
        event_id: str | None = None,
        created_at: float,
    ) -> EventRecord:
        _require_text(kind, "kind")
        if input_sha256 is not None:
            _validate_sha256(input_sha256, "input_sha256")
        if output_sha256 is not None:
            _validate_sha256(output_sha256, "output_sha256")
        payload_json = _json_dumps(payload)
        event_id = event_id or uuid.uuid4().hex
        state = conn.execute(
            "SELECT event_count, head_seq, head_hash FROM event_chain_state WHERE singleton = 1"
        ).fetchone()
        if state is None:
            raise EventChainError("event chain state is missing")
        seq = int(state["event_count"]) + 1
        if state["head_seq"] is not None and int(state["head_seq"]) != seq - 1:
            raise EventChainError("event chain state is internally inconsistent")
        prev_hash = state["head_hash"] or ZERO_HASH
        event_hash = self._event_digest(
            seq,
            event_id,
            kind,
            aggregate_type,
            aggregate_id,
            attempt_id,
            attempt_seq,
            stage,
            input_sha256,
            output_sha256,
            payload_json,
            created_at,
            prev_hash,
        )
        conn.execute(
            """
            INSERT INTO events(
                seq, event_id, kind, aggregate_type, aggregate_id,
                attempt_id, attempt_seq, stage, input_sha256, output_sha256,
                payload_json, created_at, prev_hash, event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seq,
                event_id,
                kind,
                aggregate_type,
                aggregate_id,
                attempt_id,
                attempt_seq,
                stage,
                input_sha256,
                output_sha256,
                payload_json,
                created_at,
                prev_hash,
                event_hash,
            ),
        )
        conn.execute(
            """
            UPDATE event_chain_state
            SET event_count = ?, head_seq = ?, head_hash = ?
            WHERE singleton = 1
            """,
            (seq, seq, event_hash),
        )
        return EventRecord(
            seq,
            event_id,
            kind,
            aggregate_type,
            aggregate_id,
            attempt_id,
            attempt_seq,
            stage,
            input_sha256,
            output_sha256,
            payload,
            created_at,
            prev_hash,
            event_hash,
        )

    def append_event(
        self,
        kind: str,
        payload: Any,
        *,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        attempt_id: str | None = None,
        attempt_seq: int | None = None,
        stage: str | None = None,
        input_sha256: str | None = None,
        output_sha256: str | None = None,
        event_id: str | None = None,
        now: float | None = None,
    ) -> EventRecord:
        at = self._now(now)
        with self._write() as conn:
            return self._append_event_tx(
                conn,
                kind,
                payload,
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id,
                attempt_id=attempt_id,
                attempt_seq=attempt_seq,
                stage=stage,
                input_sha256=input_sha256,
                output_sha256=output_sha256,
                event_id=event_id,
                created_at=at,
            )

    @staticmethod
    def _event_from_row(row: sqlite3.Row) -> EventRecord:
        return EventRecord(
            seq=int(row["seq"]),
            event_id=row["event_id"],
            kind=row["kind"],
            aggregate_type=row["aggregate_type"],
            aggregate_id=row["aggregate_id"],
            attempt_id=row["attempt_id"],
            attempt_seq=row["attempt_seq"],
            stage=row["stage"],
            input_sha256=row["input_sha256"],
            output_sha256=row["output_sha256"],
            payload=_json_loads(row["payload_json"]),
            created_at=float(row["created_at"]),
            prev_hash=row["prev_hash"],
            event_hash=row["event_hash"],
        )

    def list_events(
        self,
        *,
        after_seq: int = 0,
        kind: str | None = None,
        aggregate_type: str | None = None,
        aggregate_id: str | None = None,
        limit: int = 100,
    ) -> list[EventRecord]:
        _limit(limit)
        if after_seq < 0:
            raise ValueError("after_seq cannot be negative")
        clauses = ["seq > ?"]
        params: list[Any] = [after_seq]
        for column, value in (
            ("kind", kind),
            ("aggregate_type", aggregate_type),
            ("aggregate_id", aggregate_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"SELECT * FROM events WHERE {' AND '.join(clauses)} ORDER BY seq LIMIT ?",
                params,
            ).fetchall()
        return [self._event_from_row(row) for row in rows]

    def event_head(self) -> tuple[int | None, str | None]:
        with self._read() as conn:
            row = conn.execute(
                "SELECT head_seq, head_hash FROM event_chain_state WHERE singleton = 1"
            ).fetchone()
        if row is None:
            raise EventChainError("event chain state is missing")
        return row["head_seq"], row["head_hash"]

    def verify_event_chain(
        self,
        *,
        expected_head: str | None = None,
        expected_count: int | None = None,
    ) -> ChainVerification:
        if expected_head is not None:
            _validate_sha256(expected_head, "expected_head")
        if expected_count is not None and expected_count < 0:
            raise ValueError("expected_count cannot be negative")
        with self._read() as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY seq").fetchall()
            state = conn.execute(
                "SELECT event_count, head_seq, head_hash FROM event_chain_state WHERE singleton = 1"
            ).fetchone()

        previous = ZERO_HASH
        checked = 0
        for expected_seq, row in enumerate(rows, start=1):
            seq = int(row["seq"])
            if seq != expected_seq:
                return ChainVerification(
                    False,
                    checked,
                    rows[checked - 1]["seq"] if checked else None,
                    previous if checked else None,
                    seq,
                    f"expected event sequence {expected_seq}, found {seq}",
                )
            if row["prev_hash"] != previous:
                return ChainVerification(
                    False,
                    checked,
                    seq - 1 if checked else None,
                    previous if checked else None,
                    seq,
                    "previous hash does not match prior event",
                )
            computed = self._event_digest(
                seq,
                row["event_id"],
                row["kind"],
                row["aggregate_type"],
                row["aggregate_id"],
                row["attempt_id"],
                row["attempt_seq"],
                row["stage"],
                row["input_sha256"],
                row["output_sha256"],
                row["payload_json"],
                float(row["created_at"]),
                row["prev_hash"],
            )
            if computed != row["event_hash"]:
                return ChainVerification(
                    False,
                    checked,
                    seq - 1 if checked else None,
                    previous if checked else None,
                    seq,
                    "event hash does not match event contents",
                )
            previous = row["event_hash"]
            checked += 1

        head_seq = checked or None
        head_hash = previous if checked else None
        if state is None:
            return ChainVerification(
                False, checked, head_seq, head_hash, None, "event chain state is missing"
            )
        if (
            int(state["event_count"]) != checked
            or state["head_seq"] != head_seq
            or state["head_hash"] != head_hash
        ):
            return ChainVerification(
                False,
                checked,
                head_seq,
                head_hash,
                None,
                "stored chain head does not match event rows",
            )
        if expected_count is not None and checked != expected_count:
            return ChainVerification(
                False,
                checked,
                head_seq,
                head_hash,
                None,
                f"expected {expected_count} events, found {checked}",
            )
        if expected_head is not None and head_hash != expected_head:
            return ChainVerification(
                False,
                checked,
                head_seq,
                head_hash,
                None,
                "event head does not match the expected external anchor",
            )
        return ChainVerification(True, checked, head_seq, head_hash)

    def assert_event_chain(self, **expected: Any) -> ChainVerification:
        report = self.verify_event_chain(**expected)
        if not report.valid:
            raise EventChainError(report.error or "event chain verification failed")
        return report

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> TaskRecord:
        return TaskRecord(
            id=row["id"],
            idempotency_key=row["idempotency_key"],
            kind=row["kind"],
            payload=_json_loads(row["payload_json"]),
            run_id=row["run_id"],
            candidate_id=row["candidate_id"],
            input_sha256=row["input_sha256"],
            output_sha256=row["output_sha256"],
            state=row["state"],
            priority=int(row["priority"]),
            available_at=float(row["available_at"]),
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            attempt_count=int(row["attempt_count"]),
            max_attempts=int(row["max_attempts"]),
            lease_owner=row["lease_owner"],
            lease_token=row["lease_token"],
            lease_attempt_id=row["lease_attempt_id"],
            lease_expires_at=(
                None if row["lease_expires_at"] is None else float(row["lease_expires_at"])
            ),
            last_error_stage=row["last_error_stage"],
            last_error_code=row["last_error_code"],
            last_error_message=row["last_error_message"],
            result=_json_loads(row["result_json"]),
        )

    @staticmethod
    def _attempt_from_row(row: sqlite3.Row) -> AttemptRecord:
        return AttemptRecord(
            id=row["id"],
            task_id=row["task_id"],
            seq=int(row["seq"]),
            stage=row["stage"],
            worker_id=row["worker_id"],
            lease_token=row["lease_token"],
            input_sha256=row["input_sha256"],
            output_sha256=row["output_sha256"],
            status=row["status"],
            started_at=float(row["started_at"]),
            lease_expires_at=float(row["lease_expires_at"]),
            finished_at=(None if row["finished_at"] is None else float(row["finished_at"])),
            error_code=row["error_code"],
            error_message=row["error_message"],
            outcome=_json_loads(row["outcome_json"]),
        )

    @staticmethod
    def _task_payload(
        payload: Mapping[str, Any],
        *,
        run_id: str | None,
        candidate_id: str | None,
        input_sha256: str | None,
    ) -> tuple[dict[str, Any], str | None, str | None, str]:
        if not isinstance(payload, Mapping):
            raise TypeError("task payload must be a mapping")
        envelope = dict(payload)

        payload_run = envelope.get("run_id")
        if run_id is not None and payload_run is not None and payload_run != run_id:
            raise ValueError("run_id conflicts with payload['run_id']")
        resolved_run = run_id if run_id is not None else payload_run
        if resolved_run is not None:
            _require_text(resolved_run, "run_id")
            envelope["run_id"] = resolved_run

        payload_candidate = envelope.get("candidate_id")
        if (
            candidate_id is not None
            and payload_candidate is not None
            and payload_candidate != candidate_id
        ):
            raise ValueError("candidate_id conflicts with payload['candidate_id']")
        resolved_candidate = candidate_id if candidate_id is not None else payload_candidate
        if resolved_candidate is not None:
            _require_text(resolved_candidate, "candidate_id")
            envelope["candidate_id"] = resolved_candidate

        payload_hash = envelope.get("input_sha256")
        if input_sha256 is not None and payload_hash is not None and payload_hash != input_sha256:
            raise ValueError("input_sha256 conflicts with payload['input_sha256']")
        resolved_hash = input_sha256 if input_sha256 is not None else payload_hash
        if resolved_hash is None:
            # Hash the caller's input before adding the task-envelope digest itself.
            resolved_hash = _sha256_text(_json_dumps(envelope))
        _validate_sha256(resolved_hash, "input_sha256")
        envelope["input_sha256"] = resolved_hash
        return envelope, resolved_run, resolved_candidate, resolved_hash

    def enqueue_task(
        self,
        kind: str,
        payload: Mapping[str, Any],
        *,
        idempotency_key: str,
        run_id: str | None = None,
        candidate_id: str | None = None,
        input_sha256: str | None = None,
        priority: int = 0,
        available_at: float | None = None,
        max_attempts: int = 3,
        task_id: str | None = None,
        now: float | None = None,
    ) -> TaskRecord:
        """Enqueue once and return the original row on an exact replay.

        The key is global to the task table.  Reusing it for different immutable
        input raises :class:`IdempotencyConflictError` rather than silently
        returning unrelated work.
        """

        _require_text(kind, "kind")
        _require_text(idempotency_key, "idempotency_key")
        if not isinstance(priority, int) or isinstance(priority, bool):
            raise TypeError("priority must be an integer")
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts <= 0:
            raise ValueError("max_attempts must be a positive integer")
        envelope, run_id, candidate_id, input_sha256 = self._task_payload(
            payload,
            run_id=run_id,
            candidate_id=candidate_id,
            input_sha256=input_sha256,
        )
        payload_json = _json_dumps(envelope)
        at = self._now(now)
        due = at if available_at is None else self._now(available_at)
        requested_id = task_id
        task_id = task_id or uuid.uuid4().hex
        _require_text(task_id, "task_id")

        with self._write() as conn:
            existing = conn.execute(
                "SELECT * FROM tasks WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
            if existing is not None:
                immutable_matches = (
                    existing["kind"] == kind
                    and existing["payload_json"] == payload_json
                    and existing["run_id"] == run_id
                    and existing["candidate_id"] == candidate_id
                    and existing["input_sha256"] == input_sha256
                    and int(existing["priority"]) == priority
                    and int(existing["max_attempts"]) == max_attempts
                    and (requested_id is None or existing["id"] == requested_id)
                )
                if not immutable_matches:
                    raise IdempotencyConflictError(
                        f"task idempotency key {idempotency_key!r} has different input"
                    )
                return self._task_from_row(existing)

            id_collision = conn.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if id_collision is not None:
                raise IdempotencyConflictError(f"task id {task_id!r} already exists")
            conn.execute(
                """
                INSERT INTO tasks(
                    id, idempotency_key, kind, payload_json, run_id, candidate_id,
                    input_sha256, output_sha256, state, priority, available_at,
                    created_at, updated_at, attempt_count, max_attempts,
                    lease_owner, lease_token, lease_attempt_id, lease_expires_at,
                    last_error_stage, last_error_code, last_error_message, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'queued', ?, ?, ?, ?, 0, ?,
                          NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
                """,
                (
                    task_id,
                    idempotency_key,
                    kind,
                    payload_json,
                    run_id,
                    candidate_id,
                    input_sha256,
                    priority,
                    due,
                    at,
                    at,
                    max_attempts,
                ),
            )
            self._append_event_tx(
                conn,
                "task.enqueued",
                {
                    "task_id": task_id,
                    "run_id": run_id,
                    "candidate_id": candidate_id,
                    "priority": priority,
                    "available_at": due,
                    "max_attempts": max_attempts,
                },
                aggregate_type="task",
                aggregate_id=task_id,
                stage=kind,
                input_sha256=input_sha256,
                created_at=at,
            )
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            assert row is not None
            return self._task_from_row(row)

    def get_task(self, task_id: str) -> TaskRecord:
        with self._read() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"task {task_id!r} does not exist")
        return self._task_from_row(row)

    def get_task_by_idempotency_key(self, idempotency_key: str) -> TaskRecord | None:
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM tasks WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
        return None if row is None else self._task_from_row(row)

    def list_tasks(
        self,
        *,
        state: str | None = None,
        kind: str | None = None,
        run_id: str | None = None,
        candidate_id: str | None = None,
        limit: int = 100,
    ) -> list[TaskRecord]:
        _limit(limit)
        if state is not None and state not in TASK_STATES:
            raise ValueError(f"invalid task state {state!r}")
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("state", state),
            ("kind", kind),
            ("run_id", run_id),
            ("candidate_id", candidate_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = "" if not clauses else f"WHERE {' AND '.join(clauses)}"
        params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM tasks {where}
                ORDER BY created_at, id LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def task_counts(self) -> dict[str, int]:
        with self._read() as conn:
            rows = conn.execute(
                "SELECT state, COUNT(*) AS count FROM tasks GROUP BY state"
            ).fetchall()
        counts = {state: 0 for state in sorted(TASK_STATES)}
        counts.update({row["state"]: int(row["count"]) for row in rows})
        return counts

    def list_unapplied_succeeded_tasks(
        self,
        *,
        kind: str | None = None,
        run_id: str | None = None,
        candidate_id: str | None = None,
        limit: int | None = None,
    ) -> list[TaskRecord]:
        """Return succeeded tasks whose derived-result transaction has not landed.

        With the default ``limit=None`` this enumerates the complete durable
        backlog.  Callers may page by repeatedly supplying a limit and marking
        each returned task; unlike a scan of the oldest tasks table rows, that
        process cannot permanently hide work behind an arbitrary history
        window.
        """

        if limit is not None:
            _limit(limit)
        clauses = [
            "t.state = 'succeeded'",
            "NOT EXISTS (SELECT 1 FROM task_derived_applications AS d "
            "WHERE d.task_id = t.id)",
        ]
        params: list[Any] = []
        for column, value in (
            ("kind", kind),
            ("run_id", run_id),
            ("candidate_id", candidate_id),
        ):
            if value is not None:
                _require_text(value, column)
                clauses.append(f"t.{column} = ?")
                params.append(value)
        limit_sql = ""
        if limit is not None:
            limit_sql = "LIMIT ?"
            params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"""
                SELECT t.* FROM tasks AS t
                WHERE {' AND '.join(clauses)}
                ORDER BY t.created_at, t.id
                {limit_sql}
                """,
                params,
            ).fetchall()
        return [self._task_from_row(row) for row in rows]

    @staticmethod
    def _derived_application_from_row(
        row: sqlite3.Row,
    ) -> DerivedApplicationRecord:
        return DerivedApplicationRecord(
            task_id=row["task_id"],
            output_sha256=row["output_sha256"],
            applied_at=float(row["applied_at"]),
        )

    def get_task_derived_application(
        self, task_id: str
    ) -> DerivedApplicationRecord | None:
        """Return a task's immutable derived-result marker, if present."""

        _require_text(task_id, "task_id")
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM task_derived_applications WHERE task_id = ?",
                (task_id,),
            ).fetchone()
        return None if row is None else self._derived_application_from_row(row)

    def mark_task_derived_applied(
        self,
        task_id: str,
        output_sha256: str,
        *,
        now: float | None = None,
    ) -> DerivedApplicationRecord:
        """CAS a succeeded task's exact output into the applied-result set.

        Replaying the same ``task_id`` and output digest returns the original
        marker without appending another event.  A different digest is an
        idempotency conflict, and a non-succeeded task can never be marked.
        """

        _require_text(task_id, "task_id")
        _validate_sha256(output_sha256, "output_sha256")
        at = self._now(now)
        with self._write() as conn:
            task = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if task is None:
                raise NotFoundError(f"task {task_id!r} does not exist")
            if task["state"] != "succeeded":
                raise StateConflictError(
                    f"task {task_id!r} is {task['state']!r}, not 'succeeded'"
                )
            if task["output_sha256"] != output_sha256:
                raise StateConflictError(
                    f"task {task_id!r} output_sha256 does not match"
                )
            existing = conn.execute(
                "SELECT * FROM task_derived_applications WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            if existing is not None:
                if existing["output_sha256"] != output_sha256:
                    raise IdempotencyConflictError(
                        f"task {task_id!r} derived result was marked with another output"
                    )
                return self._derived_application_from_row(existing)
            conn.execute(
                """
                INSERT INTO task_derived_applications(task_id, output_sha256, applied_at)
                VALUES (?, ?, ?)
                """,
                (task_id, output_sha256, at),
            )
            self._append_event_tx(
                conn,
                "task.derived_applied",
                {"task_id": task_id, "output_sha256": output_sha256},
                aggregate_type="task",
                aggregate_id=task_id,
                stage=task["kind"],
                input_sha256=task["input_sha256"],
                output_sha256=output_sha256,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM task_derived_applications WHERE task_id = ?",
                (task_id,),
            ).fetchone()
            assert row is not None
            return self._derived_application_from_row(row)

    @staticmethod
    def _state_from_row(row: sqlite3.Row) -> VersionedStateRecord:
        return VersionedStateRecord(
            key=row["key"],
            value=_json_loads(row["value_json"]),
            version=int(row["version"]),
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )

    def get_state(self, key: str) -> VersionedStateRecord | None:
        """Read a generic JSON state value and its CAS version."""

        _require_text(key, "key")
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (key,)
            ).fetchone()
        return None if row is None else self._state_from_row(row)

    def put_state(
        self,
        key: str,
        value: Any,
        expected_version: int | None,
        *,
        now: float | None = None,
    ) -> VersionedStateRecord:
        """Create or update JSON state using a strict compare-and-set.

        ``expected_version=None`` means the key must not exist.  Updating an
        existing key requires its exact positive version.  Writing the same
        canonical value at the expected version is a no-op and does not bump
        the version.
        """

        _require_text(key, "key")
        if expected_version is not None and (
            not isinstance(expected_version, int)
            or isinstance(expected_version, bool)
            or expected_version <= 0
        ):
            raise ValueError("expected_version must be a positive integer or None")
        value_json = _json_dumps(value)
        value_sha256 = _sha256_text(value_json)
        at = self._now(now)
        with self._write() as conn:
            existing = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (key,)
            ).fetchone()
            if existing is None:
                if expected_version is not None:
                    raise StateConflictError(
                        f"state {key!r} does not exist; expected version {expected_version}"
                    )
                conn.execute(
                    """
                    INSERT INTO versioned_state(
                        key, value_json, version, created_at, updated_at
                    ) VALUES (?, ?, 1, ?, ?)
                    """,
                    (key, value_json, at, at),
                )
                version = 1
                event_kind = "state.created"
                prior_sha256 = None
            else:
                current_version = int(existing["version"])
                if expected_version != current_version:
                    raise StateConflictError(
                        f"state {key!r} is version {current_version}, "
                        f"expected {expected_version!r}"
                    )
                if existing["value_json"] == value_json:
                    return self._state_from_row(existing)
                version = current_version + 1
                updated = conn.execute(
                    """
                    UPDATE versioned_state
                    SET value_json = ?, version = ?, updated_at = ?
                    WHERE key = ? AND version = ?
                    """,
                    (value_json, version, at, key, current_version),
                )
                if updated.rowcount != 1:
                    raise StateConflictError(f"state {key!r} changed during update")
                event_kind = "state.updated"
                prior_sha256 = _sha256_text(existing["value_json"])

            self._append_event_tx(
                conn,
                event_kind,
                {"key": key, "version": version, "value_sha256": value_sha256},
                aggregate_type="state",
                aggregate_id=key,
                input_sha256=prior_sha256,
                output_sha256=value_sha256,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (key,)
            ).fetchone()
            assert row is not None
            return self._state_from_row(row)

    def bind_manufacturing_job(
        self,
        job_id: str,
        *,
        order_id: str,
        operation_key: str,
        intent_sha256: str,
        task_input_sha256: str,
        receipt_sha256: str,
        now: float | None = None,
    ) -> VersionedStateRecord:
        """Globally bind one remote manufacturing job to one paid-order intent.

        Adapter batches are not a sufficient uniqueness boundary: two workers
        or two later polls could otherwise accept the same remote ``job_id``
        for different orders.  This reverse index is a create-once immutable
        claim whose key is derived only from that remote id.
        """

        for value, name in (
            (job_id, "job_id"),
            (order_id, "order_id"),
            (operation_key, "operation_key"),
        ):
            _require_text(value, name)
        for value, name in (
            (intent_sha256, "intent_sha256"),
            (task_input_sha256, "task_input_sha256"),
            (receipt_sha256, "receipt_sha256"),
        ):
            _validate_sha256(value, name)
        key = _manufacturing_job_binding_key(job_id)
        value = {
            "schema_version": 1,
            "job_id": job_id,
            "order_id": order_id,
            "operation_key": operation_key,
            "intent_sha256": intent_sha256,
            "task_input_sha256": task_input_sha256,
            "receipt_sha256": receipt_sha256,
        }
        value_json = _json_dumps(value)
        at = self._now(now)
        with self._write() as conn:
            row = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (key,)
            ).fetchone()
            if row is not None:
                if row["value_json"] != value_json:
                    raise StateConflictError(
                        "remote manufacturing job_id is already bound to a "
                        "different paid-order intent"
                    )
                return self._state_from_row(row)
            conn.execute(
                """
                INSERT INTO versioned_state(
                    key, value_json, version, created_at, updated_at
                ) VALUES (?, ?, 1, ?, ?)
                """,
                (key, value_json, at, at),
            )
            value_sha256 = _sha256_text(value_json)
            self._append_event_tx(
                conn,
                "manufacturing.job_bound",
                {
                    "key": key,
                    "version": 1,
                    "value_sha256": value_sha256,
                    "job_id_sha256": _sha256_text(job_id),
                },
                aggregate_type="state",
                aggregate_id=key,
                output_sha256=value_sha256,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (key,)
            ).fetchone()
            assert row is not None
            return self._state_from_row(row)

    def _recover_expired_tx(
        self, conn: sqlite3.Connection, at: float
    ) -> list[TaskRecord]:
        rows = conn.execute(
            """
            SELECT * FROM tasks
            WHERE state = 'leased' AND lease_expires_at <= ?
            ORDER BY lease_expires_at, id
            """,
            (at,),
        ).fetchall()
        recovered: list[TaskRecord] = []
        for row in rows:
            task_id = row["id"]
            attempt_id = row["lease_attempt_id"]
            attempt_seq = int(row["attempt_count"])
            new_state = (
                "failed"
                if int(row["attempt_count"]) >= int(row["max_attempts"])
                else "queued"
            )
            message = (
                f"lease owned by {row['lease_owner']!r} expired at "
                f"{float(row['lease_expires_at']):.6f}"
            )
            attempt_update = conn.execute(
                """
                UPDATE task_attempts
                SET status = 'expired', finished_at = ?, error_code = 'lease_expired',
                    error_message = ?
                WHERE id = ? AND task_id = ? AND status = 'leased'
                """,
                (at, message, attempt_id, task_id),
            )
            if attempt_update.rowcount != 1:
                raise StoreError(f"active attempt for leased task {task_id!r} is missing")
            conn.execute(
                """
                UPDATE tasks
                SET state = ?, available_at = ?, updated_at = ?,
                    lease_owner = NULL, lease_token = NULL,
                    lease_attempt_id = NULL, lease_expires_at = NULL,
                    last_error_stage = kind, last_error_code = 'lease_expired',
                    last_error_message = ?
                WHERE id = ? AND state = 'leased'
                """,
                (new_state, at, at, message, task_id),
            )
            self._append_event_tx(
                conn,
                "task.lease_expired",
                {
                    "task_id": task_id,
                    "worker_id": row["lease_owner"],
                    "new_state": new_state,
                    "error_code": "lease_expired",
                    "error_message": message,
                },
                aggregate_type="task",
                aggregate_id=task_id,
                attempt_id=attempt_id,
                attempt_seq=attempt_seq,
                stage=row["kind"],
                input_sha256=row["input_sha256"],
                created_at=at,
            )
            refreshed = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            assert refreshed is not None
            recovered.append(self._task_from_row(refreshed))
        return recovered

    def recover_expired_leases(self, *, now: float | None = None) -> list[TaskRecord]:
        at = self._now(now)
        with self._write() as conn:
            return self._recover_expired_tx(conn, at)

    def lease_task(
        self,
        worker_id: str,
        *,
        lease_seconds: float = 60.0,
        kinds: Iterable[str] | None = None,
        now: float | None = None,
    ) -> TaskRecord | None:
        _require_text(worker_id, "worker_id")
        lease_seconds = float(lease_seconds)
        if lease_seconds <= 0 or lease_seconds != lease_seconds:
            raise ValueError("lease_seconds must be positive and finite")
        at = self._now(now)
        expires = at + lease_seconds
        if expires in (float("inf"), float("-inf")):
            raise ValueError("lease expiration must be finite")
        normalized_kinds: tuple[str, ...] | None = None
        if kinds is not None:
            normalized_kinds = tuple(dict.fromkeys(kinds))
            if not normalized_kinds:
                return None
            for kind in normalized_kinds:
                _require_text(kind, "kind")

        with self._write() as conn:
            self._recover_expired_tx(conn, at)
            params: list[Any] = [at]
            kind_clause = ""
            if normalized_kinds is not None:
                placeholders = ",".join("?" for _ in normalized_kinds)
                kind_clause = f"AND kind IN ({placeholders})"
                params.extend(normalized_kinds)
            row = conn.execute(
                f"""
                SELECT * FROM tasks
                WHERE state = 'queued' AND available_at <= ?
                    AND attempt_count < max_attempts {kind_clause}
                ORDER BY priority DESC, available_at, created_at, id
                LIMIT 1
                """,
                params,
            ).fetchone()
            if row is None:
                return None

            attempt_seq = int(row["attempt_count"]) + 1
            attempt_id = uuid.uuid4().hex
            lease_token = uuid.uuid4().hex
            updated = conn.execute(
                """
                UPDATE tasks
                SET state = 'leased', updated_at = ?, attempt_count = ?,
                    lease_owner = ?, lease_token = ?, lease_attempt_id = ?,
                    lease_expires_at = ?
                WHERE id = ? AND state = 'queued' AND available_at <= ?
                """,
                (
                    at,
                    attempt_seq,
                    worker_id,
                    lease_token,
                    attempt_id,
                    expires,
                    row["id"],
                    at,
                ),
            )
            if updated.rowcount != 1:
                raise StateConflictError("task changed while acquiring its lease")
            conn.execute(
                """
                INSERT INTO task_attempts(
                    id, task_id, seq, stage, worker_id, lease_token,
                    input_sha256, output_sha256, status, started_at,
                    lease_expires_at, finished_at, error_code, error_message,
                    outcome_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL, 'leased', ?, ?,
                          NULL, NULL, NULL, NULL)
                """,
                (
                    attempt_id,
                    row["id"],
                    attempt_seq,
                    row["kind"],
                    worker_id,
                    lease_token,
                    row["input_sha256"],
                    at,
                    expires,
                ),
            )
            self._append_event_tx(
                conn,
                "task.leased",
                {
                    "task_id": row["id"],
                    "worker_id": worker_id,
                    "lease_expires_at": expires,
                },
                aggregate_type="task",
                aggregate_id=row["id"],
                attempt_id=attempt_id,
                attempt_seq=attempt_seq,
                stage=row["kind"],
                input_sha256=row["input_sha256"],
                created_at=at,
            )
            leased = conn.execute("SELECT * FROM tasks WHERE id = ?", (row["id"],)).fetchone()
            assert leased is not None
            return self._task_from_row(leased)

    def _owned_lease_tx(
        self,
        conn: sqlite3.Connection,
        task_id: str,
        worker_id: str,
        lease_token: str,
        at: float,
    ) -> sqlite3.Row:
        row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"task {task_id!r} does not exist")
        if (
            row["state"] != "leased"
            or row["lease_owner"] != worker_id
            or row["lease_token"] != lease_token
            or float(row["lease_expires_at"]) <= at
        ):
            raise LeaseLostError(
                f"worker {worker_id!r} does not own a current lease for task {task_id!r}"
            )
        return row

    def renew_task_lease(
        self,
        task_id: str,
        worker_id: str,
        lease_token: str,
        *,
        lease_seconds: float = 60.0,
        now: float | None = None,
    ) -> TaskRecord:
        _require_text(worker_id, "worker_id")
        _require_text(lease_token, "lease_token")
        lease_seconds = float(lease_seconds)
        if lease_seconds <= 0 or lease_seconds != lease_seconds:
            raise ValueError("lease_seconds must be positive and finite")
        at = self._now(now)
        expires = at + lease_seconds
        if expires in (float("inf"), float("-inf")):
            raise ValueError("lease expiration must be finite")
        with self._write() as conn:
            row = self._owned_lease_tx(conn, task_id, worker_id, lease_token, at)
            conn.execute(
                "UPDATE tasks SET lease_expires_at = ?, updated_at = ? WHERE id = ?",
                (expires, at, task_id),
            )
            conn.execute(
                "UPDATE task_attempts SET lease_expires_at = ? WHERE id = ? AND status = 'leased'",
                (expires, row["lease_attempt_id"]),
            )
            self._append_event_tx(
                conn,
                "task.lease_renewed",
                {"task_id": task_id, "worker_id": worker_id, "lease_expires_at": expires},
                aggregate_type="task",
                aggregate_id=task_id,
                attempt_id=row["lease_attempt_id"],
                attempt_seq=int(row["attempt_count"]),
                stage=row["kind"],
                input_sha256=row["input_sha256"],
                created_at=at,
            )
            refreshed = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            assert refreshed is not None
            return self._task_from_row(refreshed)

    def complete_task(
        self,
        task_id: str,
        worker_id: str,
        lease_token: str,
        result: Any = None,
        *,
        output_sha256: str | None = None,
        now: float | None = None,
    ) -> TaskRecord:
        """Commit a result only when both worker and opaque lease token match."""

        _require_text(worker_id, "worker_id")
        _require_text(lease_token, "lease_token")
        result_json = _json_dumps(result)
        output_sha256 = (
            _sha256_text(result_json) if output_sha256 is None else output_sha256
        )
        _validate_sha256(output_sha256, "output_sha256")
        at = self._now(now)
        with self._write() as conn:
            row = self._owned_lease_tx(conn, task_id, worker_id, lease_token, at)
            attempt_id = row["lease_attempt_id"]
            attempt_seq = int(row["attempt_count"])
            attempt_update = conn.execute(
                """
                UPDATE task_attempts
                SET status = 'succeeded', output_sha256 = ?, finished_at = ?,
                    outcome_json = ?, error_code = NULL, error_message = NULL
                WHERE id = ? AND status = 'leased'
                """,
                (output_sha256, at, result_json, attempt_id),
            )
            if attempt_update.rowcount != 1:
                raise StoreError(f"active attempt for leased task {task_id!r} is missing")
            conn.execute(
                """
                UPDATE tasks
                SET state = 'succeeded', output_sha256 = ?, result_json = ?,
                    updated_at = ?, lease_owner = NULL, lease_token = NULL,
                    lease_attempt_id = NULL, lease_expires_at = NULL,
                    last_error_stage = NULL, last_error_code = NULL,
                    last_error_message = NULL
                WHERE id = ?
                """,
                (output_sha256, result_json, at, task_id),
            )
            self._append_event_tx(
                conn,
                "task.succeeded",
                {"task_id": task_id, "worker_id": worker_id, "result": result},
                aggregate_type="task",
                aggregate_id=task_id,
                attempt_id=attempt_id,
                attempt_seq=attempt_seq,
                stage=row["kind"],
                input_sha256=row["input_sha256"],
                output_sha256=output_sha256,
                created_at=at,
            )
            refreshed = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            assert refreshed is not None
            return self._task_from_row(refreshed)

    def fail_task(
        self,
        task_id: str,
        worker_id: str,
        lease_token: str,
        *,
        stage: str,
        error_code: str,
        error_message: str,
        retryable: bool,
        retry_delay: float = 0.0,
        output_sha256: str | None = None,
        details: Any = None,
        now: float | None = None,
    ) -> TaskRecord:
        """Record an owned attempt failure and optionally schedule a retry."""

        for value, name in (
            (worker_id, "worker_id"),
            (lease_token, "lease_token"),
            (stage, "stage"),
            (error_code, "error_code"),
            (error_message, "error_message"),
        ):
            _require_text(value, name)
        if not isinstance(retryable, bool):
            raise TypeError("retryable must be a bool")
        retry_delay = float(retry_delay)
        if retry_delay < 0 or retry_delay != retry_delay or retry_delay == float("inf"):
            raise ValueError("retry_delay must be non-negative and finite")
        if output_sha256 is not None:
            _validate_sha256(output_sha256, "output_sha256")
        details_json = _json_dumps(details)
        at = self._now(now)
        with self._write() as conn:
            row = self._owned_lease_tx(conn, task_id, worker_id, lease_token, at)
            attempt_id = row["lease_attempt_id"]
            attempt_seq = int(row["attempt_count"])
            will_retry = retryable and attempt_seq < int(row["max_attempts"])
            new_state = "queued" if will_retry else "failed"
            available_at = at + retry_delay if will_retry else float(row["available_at"])
            attempt_update = conn.execute(
                """
                UPDATE task_attempts
                SET status = 'failed', stage = ?, output_sha256 = ?,
                    finished_at = ?, error_code = ?, error_message = ?,
                    outcome_json = ?
                WHERE id = ? AND status = 'leased'
                """,
                (
                    stage,
                    output_sha256,
                    at,
                    error_code,
                    error_message,
                    details_json,
                    attempt_id,
                ),
            )
            if attempt_update.rowcount != 1:
                raise StoreError(f"active attempt for leased task {task_id!r} is missing")
            conn.execute(
                """
                UPDATE tasks
                SET state = ?, available_at = ?, updated_at = ?,
                    output_sha256 = COALESCE(?, output_sha256),
                    lease_owner = NULL, lease_token = NULL,
                    lease_attempt_id = NULL, lease_expires_at = NULL,
                    last_error_stage = ?, last_error_code = ?,
                    last_error_message = ?
                WHERE id = ?
                """,
                (
                    new_state,
                    available_at,
                    at,
                    output_sha256,
                    stage,
                    error_code,
                    error_message,
                    task_id,
                ),
            )
            self._append_event_tx(
                conn,
                "task.retry_scheduled" if will_retry else "task.failed",
                {
                    "task_id": task_id,
                    "worker_id": worker_id,
                    "retryable": retryable,
                    "will_retry": will_retry,
                    "available_at": available_at if will_retry else None,
                    "error_code": error_code,
                    "error_message": error_message,
                    "details": details,
                },
                aggregate_type="task",
                aggregate_id=task_id,
                attempt_id=attempt_id,
                attempt_seq=attempt_seq,
                stage=stage,
                input_sha256=row["input_sha256"],
                output_sha256=output_sha256,
                created_at=at,
            )
            refreshed = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            assert refreshed is not None
            return self._task_from_row(refreshed)

    def cancel_task(
        self,
        task_id: str,
        *,
        reason: str | None = None,
        now: float | None = None,
    ) -> TaskRecord:
        at = self._now(now)
        with self._write() as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if row is None:
                raise NotFoundError(f"task {task_id!r} does not exist")
            if row["state"] == "cancelled":
                return self._task_from_row(row)
            if row["state"] in ("succeeded", "failed"):
                raise StateConflictError(f"cannot cancel task in state {row['state']!r}")
            if row["state"] == "leased":
                conn.execute(
                    """
                    UPDATE task_attempts
                    SET status = 'cancelled', finished_at = ?,
                        error_code = 'cancelled', error_message = ?
                    WHERE id = ? AND status = 'leased'
                    """,
                    (at, reason, row["lease_attempt_id"]),
                )
            conn.execute(
                """
                UPDATE tasks
                SET state = 'cancelled', updated_at = ?,
                    lease_owner = NULL, lease_token = NULL,
                    lease_attempt_id = NULL, lease_expires_at = NULL,
                    last_error_stage = kind, last_error_code = 'cancelled',
                    last_error_message = ?
                WHERE id = ?
                """,
                (at, reason, task_id),
            )
            self._append_event_tx(
                conn,
                "task.cancelled",
                {"task_id": task_id, "reason": reason},
                aggregate_type="task",
                aggregate_id=task_id,
                attempt_id=row["lease_attempt_id"],
                attempt_seq=(int(row["attempt_count"]) if row["attempt_count"] else None),
                stage=row["kind"],
                input_sha256=row["input_sha256"],
                created_at=at,
            )
            refreshed = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            assert refreshed is not None
            return self._task_from_row(refreshed)

    def list_attempts(self, task_id: str, *, limit: int = 100) -> list[AttemptRecord]:
        _limit(limit)
        with self._read() as conn:
            exists = conn.execute("SELECT 1 FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if exists is None:
                raise NotFoundError(f"task {task_id!r} does not exist")
            rows = conn.execute(
                """
                SELECT * FROM task_attempts
                WHERE task_id = ? ORDER BY seq LIMIT ?
                """,
                (task_id, limit),
            ).fetchall()
        return [self._attempt_from_row(row) for row in rows]

    def get_attempt(self, attempt_id: str) -> AttemptRecord:
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM task_attempts WHERE id = ?", (attempt_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"attempt {attempt_id!r} does not exist")
        return self._attempt_from_row(row)

    @staticmethod
    def _candidate_from_row(row: sqlite3.Row) -> CandidateRecord:
        metadata = _json_loads(row["metadata_json"])
        if not isinstance(metadata, dict):
            raise StoreError(f"candidate {row['id']!r} has non-object metadata")
        return CandidateRecord(
            id=row["id"],
            idempotency_key=row["idempotency_key"],
            creation_sha256=row["creation_sha256"],
            kind=row["kind"],
            title=row["title"],
            content=_json_loads(row["content_json"]),
            state=row["state"],
            version=int(row["version"]),
            task_id=row["task_id"],
            parent_id=row["parent_id"],
            metadata=metadata,
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )

    def create_candidate(
        self,
        content: Any,
        *,
        kind: str = "candidate",
        title: str | None = None,
        state: str = "proposed",
        task_id: str | None = None,
        parent_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
        candidate_id: str | None = None,
        now: float | None = None,
    ) -> CandidateRecord:
        """Persist a candidate; transition legality intentionally remains policy-owned."""

        _require_text(kind, "kind")
        if title is not None:
            _require_text(title, "title")
        if state not in CANDIDATE_STATES:
            raise ValueError(f"invalid candidate state {state!r}")
        if idempotency_key is not None:
            _require_text(idempotency_key, "idempotency_key")
        if metadata is None:
            metadata = {}
        if not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        content_json = _json_dumps(content)
        metadata_json = _json_dumps(dict(metadata))
        creation_sha256 = _sha256_text(
            _json_dumps(
                {
                    "kind": kind,
                    "title": title,
                    "content": content,
                    "state": state,
                    "task_id": task_id,
                    "parent_id": parent_id,
                    "metadata": dict(metadata),
                }
            )
        )
        at = self._now(now)
        requested_id = candidate_id
        candidate_id = candidate_id or uuid.uuid4().hex
        _require_text(candidate_id, "candidate_id")

        with self._write() as conn:
            existing = None
            if idempotency_key is not None:
                existing = conn.execute(
                    "SELECT * FROM candidates WHERE idempotency_key = ?", (idempotency_key,)
                ).fetchone()
            if existing is not None:
                if not (
                    existing["creation_sha256"] == creation_sha256
                    and (requested_id is None or existing["id"] == requested_id)
                ):
                    raise IdempotencyConflictError(
                        f"candidate idempotency key {idempotency_key!r} has different input"
                    )
                return self._candidate_from_row(existing)
            collision = conn.execute(
                "SELECT 1 FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if collision is not None:
                raise IdempotencyConflictError(f"candidate id {candidate_id!r} already exists")
            if parent_id is not None:
                parent = conn.execute(
                    "SELECT 1 FROM candidates WHERE id = ?", (parent_id,)
                ).fetchone()
                if parent is None:
                    raise NotFoundError(f"parent candidate {parent_id!r} does not exist")
            conn.execute(
                """
                INSERT INTO candidates(
                    id, idempotency_key, creation_sha256, kind, title, content_json, state,
                    version, task_id, parent_id, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    idempotency_key,
                    creation_sha256,
                    kind,
                    title,
                    content_json,
                    state,
                    task_id,
                    parent_id,
                    metadata_json,
                    at,
                    at,
                ),
            )
            self._append_event_tx(
                conn,
                "candidate.created",
                {
                    "candidate_id": candidate_id,
                    "kind": kind,
                    "title": title,
                    "state": state,
                    "task_id": task_id,
                    "parent_id": parent_id,
                    "version": 1,
                },
                aggregate_type="candidate",
                aggregate_id=candidate_id,
                stage=state,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            assert row is not None
            return self._candidate_from_row(row)

    def get_candidate(self, candidate_id: str) -> CandidateRecord:
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"candidate {candidate_id!r} does not exist")
        return self._candidate_from_row(row)

    def get_candidate_by_idempotency_key(
        self, idempotency_key: str
    ) -> CandidateRecord | None:
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE idempotency_key = ?", (idempotency_key,)
            ).fetchone()
        return None if row is None else self._candidate_from_row(row)

    def list_candidates(
        self,
        *,
        state: str | None = None,
        kind: str | None = None,
        parent_id: str | None = None,
        limit: int = 100,
    ) -> list[CandidateRecord]:
        _limit(limit)
        if state is not None and state not in CANDIDATE_STATES:
            raise ValueError(f"invalid candidate state {state!r}")
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (("state", state), ("kind", kind), ("parent_id", parent_id)):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = "" if not clauses else f"WHERE {' AND '.join(clauses)}"
        params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM candidates {where}
                ORDER BY updated_at DESC, id LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._candidate_from_row(row) for row in rows]

    def transition_candidate(
        self,
        candidate_id: str,
        new_state: str,
        *,
        expected_state: str | None = None,
        expected_version: int | None = None,
        metadata_patch: Mapping[str, Any] | None = None,
        now: float | None = None,
    ) -> CandidateRecord:
        """Compare-and-set a valid state without imposing policy transitions."""

        if new_state not in CANDIDATE_STATES:
            raise ValueError(f"invalid candidate state {new_state!r}")
        if expected_state is not None and expected_state not in CANDIDATE_STATES:
            raise ValueError(f"invalid expected candidate state {expected_state!r}")
        if expected_version is not None and expected_version <= 0:
            raise ValueError("expected_version must be positive")
        if metadata_patch is not None and not isinstance(metadata_patch, Mapping):
            raise TypeError("metadata_patch must be a mapping")
        at = self._now(now)
        with self._write() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if row is None:
                raise NotFoundError(f"candidate {candidate_id!r} does not exist")
            if expected_state is not None and row["state"] != expected_state:
                raise StateConflictError(
                    f"candidate state is {row['state']!r}, expected {expected_state!r}"
                )
            if expected_version is not None and int(row["version"]) != expected_version:
                raise StateConflictError(
                    f"candidate version is {row['version']}, expected {expected_version}"
                )
            self._assert_candidate_mutation_unfenced_tx(conn, row)
            current_metadata = _json_loads(row["metadata_json"])
            if not isinstance(current_metadata, dict):
                raise StoreError(f"candidate {candidate_id!r} has non-object metadata")
            if metadata_patch:
                current_metadata.update(metadata_patch)
            metadata_json = _json_dumps(current_metadata)
            if new_state == row["state"] and metadata_json == row["metadata_json"]:
                return self._candidate_from_row(row)
            new_version = int(row["version"]) + 1
            updated = conn.execute(
                """
                UPDATE candidates
                SET state = ?, version = ?, metadata_json = ?, updated_at = ?
                WHERE id = ? AND version = ?
                """,
                (
                    new_state,
                    new_version,
                    metadata_json,
                    at,
                    candidate_id,
                    int(row["version"]),
                ),
            )
            if updated.rowcount != 1:
                raise StateConflictError("candidate changed during transition")
            self._append_event_tx(
                conn,
                "candidate.transitioned",
                {
                    "candidate_id": candidate_id,
                    "from_state": row["state"],
                    "to_state": new_state,
                    "version": new_version,
                    "metadata_patch": dict(metadata_patch or {}),
                },
                aggregate_type="candidate",
                aggregate_id=candidate_id,
                stage=new_state,
                created_at=at,
            )
            refreshed = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            assert refreshed is not None
            return self._candidate_from_row(refreshed)

    def update_candidate(
        self,
        candidate_id: str,
        content: Any,
        *,
        title: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        expected_version: int | None = None,
        now: float | None = None,
    ) -> CandidateRecord:
        if title is not None:
            _require_text(title, "title")
        if metadata is not None and not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        if expected_version is not None and expected_version <= 0:
            raise ValueError("expected_version must be positive")
        content_json = _json_dumps(content)
        at = self._now(now)
        with self._write() as conn:
            row = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if row is None:
                raise NotFoundError(f"candidate {candidate_id!r} does not exist")
            if expected_version is not None and int(row["version"]) != expected_version:
                raise StateConflictError(
                    f"candidate version is {row['version']}, expected {expected_version}"
                )
            self._assert_candidate_mutation_unfenced_tx(conn, row)
            title_value = row["title"] if title is None else title
            metadata_json = (
                row["metadata_json"] if metadata is None else _json_dumps(dict(metadata))
            )
            if (
                content_json == row["content_json"]
                and title_value == row["title"]
                and metadata_json == row["metadata_json"]
            ):
                return self._candidate_from_row(row)
            new_version = int(row["version"]) + 1
            conn.execute(
                """
                UPDATE candidates
                SET content_json = ?, title = ?, metadata_json = ?,
                    version = ?, updated_at = ?
                WHERE id = ? AND version = ?
                """,
                (
                    content_json,
                    title_value,
                    metadata_json,
                    new_version,
                    at,
                    candidate_id,
                    int(row["version"]),
                ),
            )
            self._append_event_tx(
                conn,
                "candidate.updated",
                {"candidate_id": candidate_id, "version": new_version},
                aggregate_type="candidate",
                aggregate_id=candidate_id,
                stage=row["state"],
                created_at=at,
            )
            refreshed = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            assert refreshed is not None
            return self._candidate_from_row(refreshed)

    @staticmethod
    def _assert_candidate_mutation_unfenced_tx(
        conn: sqlite3.Connection, candidate_row: sqlite3.Row
    ) -> None:
        key = _candidate_publish_effect_key(
            str(candidate_row["id"]), int(candidate_row["version"])
        )
        effect = conn.execute(
            "SELECT value_json FROM versioned_state WHERE key = ?", (key,)
        ).fetchone()
        if effect is not None:
            value = _json_loads(effect["value_json"])
            status = value.get("status") if isinstance(value, Mapping) else None
            if status in {"sending", "ambiguous"}:
                raise StateConflictError(
                    "candidate has an unresolved public-send fence; reconcile it "
                    "before retracting or revising the candidate"
                )
        # Physical-effect keys are input-hash scoped. Inspect their closed
        # identities instead of relying on a wildcard-prone candidate-id prefix.
        for physical in conn.execute(
            "SELECT value_json FROM versioned_state"
        ).fetchall():
            value = _json_loads(physical["value_json"])
            if not isinstance(value, Mapping):
                continue
            if (
                value.get("candidate_id") == candidate_row["id"]
                and value.get("candidate_version") == int(candidate_row["version"])
                and value.get("action") in _CANDIDATE_PHYSICAL_EFFECT_ACTIONS
                and value.get("status") in {"sending", "ambiguous"}
            ):
                raise StateConflictError(
                    "candidate has an unresolved physical-effect fence; reconcile "
                    "it before retracting or revising the candidate"
                )

    @staticmethod
    def _candidate_artifact_from_row(
        row: sqlite3.Row,
    ) -> CandidateArtifactRecord:
        return CandidateArtifactRecord(
            id=row["id"],
            candidate_id=row["candidate_id"],
            task_id=row["task_id"],
            action=row["action"],
            candidate_version=int(row["candidate_version"]),
            output_sha256=row["output_sha256"],
            content_sha256=row["content_sha256"],
            content=_json_loads(row["content_json"]),
            created_at=float(row["created_at"]),
        )

    def record_candidate_artifact(
        self,
        candidate_id: str,
        task_id: str,
        action: str,
        candidate_version: int,
        output_sha256: str,
        content: Any,
        *,
        content_sha256: str | None = None,
        artifact_id: str | None = None,
        now: float | None = None,
    ) -> CandidateArtifactRecord:
        """Store one immutable artifact bound to an exact succeeded task.

        The task must name the same candidate, action, captured candidate
        version, and output digest.  Replaying all of those fields plus the
        canonical content returns the original row; reusing the task for
        different artifact material raises an idempotency conflict.
        """

        _require_text(candidate_id, "candidate_id")
        _require_text(task_id, "task_id")
        _require_text(action, "action")
        if (
            not isinstance(candidate_version, int)
            or isinstance(candidate_version, bool)
            or candidate_version <= 0
        ):
            raise ValueError("candidate_version must be a positive integer")
        _validate_sha256(output_sha256, "output_sha256")
        content_json = _json_dumps(content)
        computed_content_sha256 = _sha256_text(content_json)
        if content_sha256 is not None:
            _validate_sha256(content_sha256, "content_sha256")
            if content_sha256 != computed_content_sha256:
                raise ValueError("content_sha256 does not match canonical content")
        else:
            content_sha256 = computed_content_sha256
        requested_id = artifact_id
        artifact_id = artifact_id or uuid.uuid4().hex
        _require_text(artifact_id, "artifact_id")
        at = self._now(now)

        with self._write() as conn:
            candidate = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if candidate is None:
                raise NotFoundError(f"candidate {candidate_id!r} does not exist")
            task = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            if task is None:
                raise NotFoundError(f"task {task_id!r} does not exist")
            if task["state"] != "succeeded":
                raise StateConflictError(
                    f"task {task_id!r} is {task['state']!r}, not 'succeeded'"
                )
            if task["candidate_id"] != candidate_id:
                raise StateConflictError(
                    f"task {task_id!r} is not bound to candidate {candidate_id!r}"
                )
            if task["kind"] != action:
                raise StateConflictError(
                    f"task {task_id!r} action is {task['kind']!r}, not {action!r}"
                )
            if task["output_sha256"] != output_sha256:
                raise StateConflictError(
                    f"task {task_id!r} output_sha256 does not match"
                )
            payload = _json_loads(task["payload_json"])
            payload_version = (
                payload.get("candidate_version")
                if isinstance(payload, Mapping)
                else None
            )
            if payload_version != candidate_version or isinstance(payload_version, bool):
                raise StateConflictError(
                    f"task {task_id!r} captured candidate version "
                    f"{payload_version!r}, not {candidate_version}"
                )
            if int(candidate["version"]) < candidate_version:
                raise StateConflictError(
                    f"candidate {candidate_id!r} has not reached version {candidate_version}"
                )

            existing = conn.execute(
                "SELECT * FROM candidate_artifacts WHERE task_id = ?", (task_id,)
            ).fetchone()
            if existing is not None:
                exact_replay = (
                    existing["candidate_id"] == candidate_id
                    and existing["action"] == action
                    and int(existing["candidate_version"]) == candidate_version
                    and existing["output_sha256"] == output_sha256
                    and existing["content_sha256"] == content_sha256
                    and existing["content_json"] == content_json
                    and (requested_id is None or existing["id"] == requested_id)
                )
                if not exact_replay:
                    raise IdempotencyConflictError(
                        f"task {task_id!r} already has a different candidate artifact"
                    )
                return self._candidate_artifact_from_row(existing)

            collision = conn.execute(
                "SELECT 1 FROM candidate_artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            if collision is not None:
                raise IdempotencyConflictError(
                    f"candidate artifact id {artifact_id!r} already exists"
                )
            conn.execute(
                """
                INSERT INTO candidate_artifacts(
                    id, candidate_id, task_id, action, candidate_version,
                    output_sha256, content_sha256, content_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    candidate_id,
                    task_id,
                    action,
                    candidate_version,
                    output_sha256,
                    content_sha256,
                    content_json,
                    at,
                ),
            )
            self._append_event_tx(
                conn,
                "candidate.artifact_recorded",
                {
                    "artifact_id": artifact_id,
                    "candidate_id": candidate_id,
                    "task_id": task_id,
                    "action": action,
                    "candidate_version": candidate_version,
                    "output_sha256": output_sha256,
                    "content_sha256": content_sha256,
                },
                aggregate_type="candidate",
                aggregate_id=candidate_id,
                stage=action,
                input_sha256=task["input_sha256"],
                output_sha256=output_sha256,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM candidate_artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            assert row is not None
            return self._candidate_artifact_from_row(row)

    def get_candidate_artifact(self, artifact_id: str) -> CandidateArtifactRecord:
        _require_text(artifact_id, "artifact_id")
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM candidate_artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"candidate artifact {artifact_id!r} does not exist")
        return self._candidate_artifact_from_row(row)

    def get_candidate_artifact_for_task(
        self, task_id: str
    ) -> CandidateArtifactRecord | None:
        _require_text(task_id, "task_id")
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM candidate_artifacts WHERE task_id = ?", (task_id,)
            ).fetchone()
        return None if row is None else self._candidate_artifact_from_row(row)

    def list_candidate_artifacts(
        self,
        *,
        candidate_id: str | None = None,
        task_id: str | None = None,
        action: str | None = None,
        candidate_version: int | None = None,
        output_sha256: str | None = None,
        content_sha256: str | None = None,
        limit: int = 100,
    ) -> list[CandidateArtifactRecord]:
        _limit(limit)
        if candidate_version is not None and (
            not isinstance(candidate_version, int)
            or isinstance(candidate_version, bool)
            or candidate_version <= 0
        ):
            raise ValueError("candidate_version must be a positive integer")
        if output_sha256 is not None:
            _validate_sha256(output_sha256, "output_sha256")
        if content_sha256 is not None:
            _validate_sha256(content_sha256, "content_sha256")
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("candidate_id", candidate_id),
            ("task_id", task_id),
            ("action", action),
            ("candidate_version", candidate_version),
            ("output_sha256", output_sha256),
            ("content_sha256", content_sha256),
        ):
            if value is not None:
                if column in {"candidate_id", "task_id", "action"}:
                    _require_text(value, column)
                clauses.append(f"{column} = ?")
                params.append(value)
        where = "" if not clauses else f"WHERE {' AND '.join(clauses)}"
        params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM candidate_artifacts {where}
                ORDER BY created_at, id LIMIT ?
                """,
                params,
            ).fetchall()
        return [self._candidate_artifact_from_row(row) for row in rows]

    @staticmethod
    def _evaluation_from_row(row: sqlite3.Row) -> EvaluationRecord:
        return EvaluationRecord(
            id=row["id"],
            idempotency_key=row["idempotency_key"],
            candidate_id=row["candidate_id"],
            evaluator=row["evaluator"],
            score=(None if row["score"] is None else float(row["score"])),
            verdict=row["verdict"],
            metrics=_json_loads(row["metrics_json"]),
            notes=row["notes"],
            created_at=float(row["created_at"]),
        )

    def add_evaluation(
        self,
        candidate_id: str,
        evaluator: str,
        *,
        score: float | None = None,
        verdict: str | None = None,
        metrics: Any = None,
        notes: str | None = None,
        idempotency_key: str | None = None,
        evaluation_id: str | None = None,
        now: float | None = None,
    ) -> EvaluationRecord:
        _require_text(evaluator, "evaluator")
        if verdict is not None:
            _require_text(verdict, "verdict")
        if idempotency_key is not None:
            _require_text(idempotency_key, "idempotency_key")
        score_value = None if score is None else float(score)
        if score_value is not None and (
            score_value != score_value
            or score_value in (float("inf"), float("-inf"))
        ):
            raise ValueError("score must be finite")
        metrics_json = _json_dumps({} if metrics is None else metrics)
        at = self._now(now)
        requested_id = evaluation_id
        evaluation_id = evaluation_id or uuid.uuid4().hex
        with self._write() as conn:
            candidate = conn.execute(
                "SELECT 1 FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if candidate is None:
                raise NotFoundError(f"candidate {candidate_id!r} does not exist")
            existing = None
            if idempotency_key is not None:
                existing = conn.execute(
                    "SELECT * FROM evaluations WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
            if existing is not None:
                if not (
                    existing["candidate_id"] == candidate_id
                    and existing["evaluator"] == evaluator
                    and existing["score"] == score_value
                    and existing["verdict"] == verdict
                    and existing["metrics_json"] == metrics_json
                    and existing["notes"] == notes
                    and (requested_id is None or existing["id"] == requested_id)
                ):
                    raise IdempotencyConflictError(
                        f"evaluation idempotency key {idempotency_key!r} has different input"
                    )
                return self._evaluation_from_row(existing)
            conn.execute(
                """
                INSERT INTO evaluations(
                    id, idempotency_key, candidate_id, evaluator, score,
                    verdict, metrics_json, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    evaluation_id,
                    idempotency_key,
                    candidate_id,
                    evaluator,
                    score_value,
                    verdict,
                    metrics_json,
                    notes,
                    at,
                ),
            )
            self._append_event_tx(
                conn,
                "evaluation.recorded",
                {
                    "evaluation_id": evaluation_id,
                    "candidate_id": candidate_id,
                    "evaluator": evaluator,
                    "score": score_value,
                    "verdict": verdict,
                },
                aggregate_type="candidate",
                aggregate_id=candidate_id,
                stage="evaluation",
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM evaluations WHERE id = ?", (evaluation_id,)
            ).fetchone()
            assert row is not None
            return self._evaluation_from_row(row)

    def list_evaluations(
        self,
        *,
        candidate_id: str | None = None,
        evaluator: str | None = None,
        verdict: str | None = None,
        limit: int = 100,
    ) -> list[EvaluationRecord]:
        _limit(limit)
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("candidate_id", candidate_id),
            ("evaluator", evaluator),
            ("verdict", verdict),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = "" if not clauses else f"WHERE {' AND '.join(clauses)}"
        params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"SELECT * FROM evaluations {where} ORDER BY created_at, id LIMIT ?",
                params,
            ).fetchall()
        return [self._evaluation_from_row(row) for row in rows]

    @staticmethod
    def _experience_from_row(row: sqlite3.Row) -> ExperienceRecord:
        return ExperienceRecord(
            id=row["id"],
            idempotency_key=row["idempotency_key"],
            kind=row["kind"],
            content=_json_loads(row["content_json"]),
            reward=(None if row["reward"] is None else float(row["reward"])),
            task_id=row["task_id"],
            candidate_id=row["candidate_id"],
            attempt_id=row["attempt_id"],
            created_at=float(row["created_at"]),
        )

    def add_experience(
        self,
        kind: str,
        content: Any,
        *,
        reward: float | None = None,
        task_id: str | None = None,
        candidate_id: str | None = None,
        attempt_id: str | None = None,
        idempotency_key: str | None = None,
        experience_id: str | None = None,
        now: float | None = None,
    ) -> ExperienceRecord:
        _require_text(kind, "kind")
        if idempotency_key is not None:
            _require_text(idempotency_key, "idempotency_key")
        reward_value = None if reward is None else float(reward)
        if reward_value is not None and (
            reward_value != reward_value
            or reward_value in (float("inf"), float("-inf"))
        ):
            raise ValueError("reward must be finite")
        content_json = _json_dumps(content)
        at = self._now(now)
        requested_id = experience_id
        experience_id = experience_id or uuid.uuid4().hex
        with self._write() as conn:
            existing = None
            if idempotency_key is not None:
                existing = conn.execute(
                    "SELECT * FROM experiences WHERE idempotency_key = ?",
                    (idempotency_key,),
                ).fetchone()
            if existing is not None:
                if not (
                    existing["kind"] == kind
                    and existing["content_json"] == content_json
                    and existing["reward"] == reward_value
                    and existing["task_id"] == task_id
                    and existing["candidate_id"] == candidate_id
                    and existing["attempt_id"] == attempt_id
                    and (requested_id is None or existing["id"] == requested_id)
                ):
                    raise IdempotencyConflictError(
                        f"experience idempotency key {idempotency_key!r} has different input"
                    )
                return self._experience_from_row(existing)
            # Give callers clearer domain errors than raw foreign-key failures.
            for table, value, label in (
                ("tasks", task_id, "task"),
                ("candidates", candidate_id, "candidate"),
                ("task_attempts", attempt_id, "attempt"),
            ):
                if value is not None:
                    found = conn.execute(
                        f"SELECT 1 FROM {table} WHERE id = ?", (value,)
                    ).fetchone()
                    if found is None:
                        raise NotFoundError(f"{label} {value!r} does not exist")
            conn.execute(
                """
                INSERT INTO experiences(
                    id, idempotency_key, kind, content_json, reward,
                    task_id, candidate_id, attempt_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    experience_id,
                    idempotency_key,
                    kind,
                    content_json,
                    reward_value,
                    task_id,
                    candidate_id,
                    attempt_id,
                    at,
                ),
            )
            self._append_event_tx(
                conn,
                "experience.recorded",
                {
                    "experience_id": experience_id,
                    "kind": kind,
                    "reward": reward_value,
                    "task_id": task_id,
                    "candidate_id": candidate_id,
                    "attempt_id": attempt_id,
                },
                aggregate_type="experience",
                aggregate_id=experience_id,
                attempt_id=attempt_id,
                stage=kind,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM experiences WHERE id = ?", (experience_id,)
            ).fetchone()
            assert row is not None
            return self._experience_from_row(row)

    record_experience = add_experience

    def list_experiences(
        self,
        *,
        kind: str | None = None,
        task_id: str | None = None,
        candidate_id: str | None = None,
        limit: int = 100,
    ) -> list[ExperienceRecord]:
        _limit(limit)
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("kind", kind),
            ("task_id", task_id),
            ("candidate_id", candidate_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = "" if not clauses else f"WHERE {' AND '.join(clauses)}"
        params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"SELECT * FROM experiences {where} ORDER BY created_at, id LIMIT ?",
                params,
            ).fetchall()
        return [self._experience_from_row(row) for row in rows]

    @staticmethod
    def _publication_from_row(row: sqlite3.Row) -> PublicationRecord:
        return PublicationRecord(
            id=row["id"],
            target=row["target"],
            idempotency_key=row["idempotency_key"],
            request_sha256=row["request_sha256"],
            request=_json_loads(row["request_json"]),
            candidate_id=row["candidate_id"],
            state=row["state"],
            remote_design_id=row["remote_design_id"],
            slug=row["slug"],
            history_id=row["history_id"],
            status=row["status"],
            project_url=row["project_url"],
            response=_json_loads(row["response_json"]),
            last_error=row["last_error"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
        )

    def prepare_publication(
        self,
        target: str,
        idempotency_key: str,
        request_sha256: str,
        request: Any,
        *,
        candidate_id: str | None = None,
        slug: str | None = None,
        publication_id: str | None = None,
        now: float | None = None,
    ) -> PublicationRecord:
        """Durably prepare an outward side effect before any network call.

        ``(target, idempotency_key)`` is the reconciliation identity.  An exact
        replay returns the same row; a different request digest is a hard
        conflict. Preparation defaults the remote object to ``draft``. A later
        receipt may record ``publishing`` or ``published`` after the adapter has
        performed the authorized outward action.
        """

        _require_text(target, "target")
        _require_text(idempotency_key, "idempotency_key")
        _validate_sha256(request_sha256, "request_sha256")
        if slug is not None:
            _require_text(slug, "slug")
        request_json = _json_dumps(request)
        at = self._now(now)
        requested_id = publication_id
        publication_id = publication_id or uuid.uuid4().hex
        with self._write() as conn:
            existing = conn.execute(
                """
                SELECT * FROM publications
                WHERE target = ? AND idempotency_key = ?
                """,
                (target, idempotency_key),
            ).fetchone()
            if existing is not None:
                if existing["request_sha256"] != request_sha256:
                    raise IdempotencyConflictError(
                        "publication key was replayed with a different request_sha256"
                    )
                if not (
                    existing["request_json"] == request_json
                    and existing["candidate_id"] == candidate_id
                    and (requested_id is None or existing["id"] == requested_id)
                ):
                    raise IdempotencyConflictError(
                        "publication key was replayed with different immutable input"
                    )
                return self._publication_from_row(existing)
            if candidate_id is not None:
                candidate = conn.execute(
                    "SELECT 1 FROM candidates WHERE id = ?", (candidate_id,)
                ).fetchone()
                if candidate is None:
                    raise NotFoundError(f"candidate {candidate_id!r} does not exist")
            conn.execute(
                """
                INSERT INTO publications(
                    id, target, idempotency_key, request_sha256, request_json,
                    candidate_id, state, remote_design_id, slug, history_id,
                    status, project_url, response_json, last_error,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'prepared', NULL, ?, NULL,
                          'draft', NULL, NULL, NULL, ?, ?)
                """,
                (
                    publication_id,
                    target,
                    idempotency_key,
                    request_sha256,
                    request_json,
                    candidate_id,
                    slug,
                    at,
                    at,
                ),
            )
            self._append_event_tx(
                conn,
                "publication.prepared",
                {
                    "publication_id": publication_id,
                    "target": target,
                    "idempotency_key": idempotency_key,
                    "request_sha256": request_sha256,
                    "candidate_id": candidate_id,
                    "status": "draft",
                },
                aggregate_type="publication",
                aggregate_id=publication_id,
                stage="prepared",
                input_sha256=request_sha256,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM publications WHERE id = ?", (publication_id,)
            ).fetchone()
            assert row is not None
            return self._publication_from_row(row)

    def get_publication(self, publication_id: str) -> PublicationRecord:
        with self._read() as conn:
            row = conn.execute(
                "SELECT * FROM publications WHERE id = ?", (publication_id,)
            ).fetchone()
        if row is None:
            raise NotFoundError(f"publication {publication_id!r} does not exist")
        return self._publication_from_row(row)

    def get_publication_intent(
        self, target: str, idempotency_key: str
    ) -> PublicationRecord | None:
        """Look up a publication after timeout/crash for remote reconciliation."""

        with self._read() as conn:
            row = conn.execute(
                """
                SELECT * FROM publications
                WHERE target = ? AND idempotency_key = ?
                """,
                (target, idempotency_key),
            ).fetchone()
        return None if row is None else self._publication_from_row(row)

    def transition_publication(
        self,
        publication_id: str,
        new_state: str,
        *,
        expected_state: str | None = None,
        remote_design_id: str | None = None,
        slug: str | None = None,
        history_id: str | None = None,
        status: str | None = None,
        project_url: str | None = None,
        response: Any = None,
        last_error: str | None = None,
        now: float | None = None,
    ) -> PublicationRecord:
        if new_state not in PUBLICATION_STATES:
            raise ValueError(f"invalid publication state {new_state!r}")
        if expected_state is not None and expected_state not in PUBLICATION_STATES:
            raise ValueError(f"invalid expected publication state {expected_state!r}")
        if status is not None and status not in PUBLICATION_REMOTE_STATUSES:
            raise ValueError(
                "publication status must be 'draft', 'publishing', or 'published'"
            )
        at = self._now(now)
        response_json = None if response is None else _json_dumps(response)
        with self._write() as conn:
            row = conn.execute(
                "SELECT * FROM publications WHERE id = ?", (publication_id,)
            ).fetchone()
            if row is None:
                raise NotFoundError(f"publication {publication_id!r} does not exist")
            if expected_state is not None and row["state"] != expected_state:
                raise StateConflictError(
                    f"publication state is {row['state']!r}, expected {expected_state!r}"
                )
            conn.execute(
                """
                UPDATE publications
                SET state = ?,
                    remote_design_id = COALESCE(?, remote_design_id),
                    slug = COALESCE(?, slug),
                    history_id = COALESCE(?, history_id),
                    status = COALESCE(?, status),
                    project_url = COALESCE(?, project_url),
                    response_json = COALESCE(?, response_json),
                    last_error = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    new_state,
                    remote_design_id,
                    slug,
                    history_id,
                    status,
                    project_url,
                    response_json,
                    last_error,
                    at,
                    publication_id,
                ),
            )
            self._append_event_tx(
                conn,
                f"publication.{new_state}",
                {
                    "publication_id": publication_id,
                    "target": row["target"],
                    "from_state": row["state"],
                    "to_state": new_state,
                    "remote_design_id": remote_design_id,
                    "slug": slug,
                    "history_id": history_id,
                    "status": row["status"] if status is None else status,
                    "project_url": project_url,
                    "response": response,
                    "last_error": last_error,
                },
                aggregate_type="publication",
                aggregate_id=publication_id,
                stage=new_state,
                input_sha256=row["request_sha256"],
                created_at=at,
            )
            refreshed = conn.execute(
                "SELECT * FROM publications WHERE id = ?", (publication_id,)
            ).fetchone()
            assert refreshed is not None
            return self._publication_from_row(refreshed)

    def claim_candidate_publication_send(
        self,
        publication_id: str,
        *,
        candidate_id: str,
        candidate_version: int,
        candidate_content_sha256: str,
        response: Mapping[str, Any],
        effect_payload: Mapping[str, Any],
        now: float | None = None,
    ) -> PublicationRecord:
        """Atomically choose between candidate retraction and a public send.

        The transaction verifies the immutable candidate snapshot, installs a
        version-scoped send fence, and advances the publication to
        ``publish_sending``. A concurrent candidate transition uses the same
        SQLite write lock and therefore either wins before this transaction or
        is rejected by the newly installed fence.
        """

        _require_text(publication_id, "publication_id")
        _require_text(candidate_id, "candidate_id")
        if (
            not isinstance(candidate_version, int)
            or isinstance(candidate_version, bool)
            or candidate_version <= 0
        ):
            raise ValueError("candidate_version must be a positive integer")
        _validate_sha256(candidate_content_sha256, "candidate_content_sha256")
        if not isinstance(response, Mapping) or response.get("stage") != "publish_sending":
            raise ValueError("publication response must enter publish_sending")
        if not isinstance(effect_payload, Mapping):
            raise TypeError("effect_payload must be a mapping")
        response_json = _json_dumps(dict(response))
        effect_key = _candidate_publish_effect_key(candidate_id, candidate_version)
        effect_value = {
            "publication_id": publication_id,
            "candidate_id": candidate_id,
            "candidate_version": candidate_version,
            "candidate_content_sha256": candidate_content_sha256,
            "payload_sha256": _sha256_text(_json_dumps(dict(effect_payload))),
            "status": "sending",
        }
        effect_json = _json_dumps(effect_value)
        at = self._now(now)
        with self._write() as conn:
            candidate = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if candidate is None:
                raise NotFoundError(f"candidate {candidate_id!r} does not exist")
            if (
                candidate["state"] != "publish_ready"
                or int(candidate["version"]) != candidate_version
                or _sha256_text(candidate["content_json"])
                != candidate_content_sha256
            ):
                raise StateConflictError(
                    "candidate was retracted or revised before the public send"
                )
            publication = conn.execute(
                "SELECT * FROM publications WHERE id = ?", (publication_id,)
            ).fetchone()
            if publication is None:
                raise NotFoundError(
                    f"publication {publication_id!r} does not exist"
                )
            if (
                publication["candidate_id"] != candidate_id
                or publication["state"] != "in_flight"
            ):
                raise StateConflictError(
                    "publication is not the in-flight candidate intent"
                )
            progress = _json_loads(publication["response_json"])
            if not isinstance(progress, Mapping) or progress.get("stage") != "publish_ready":
                raise StateConflictError(
                    "publication is not ready to cross the public-write boundary"
                )
            existing = conn.execute(
                "SELECT 1 FROM versioned_state WHERE key = ?", (effect_key,)
            ).fetchone()
            if existing is not None:
                raise StateConflictError(
                    "candidate public send already has a durable owner"
                )
            conn.execute(
                """
                INSERT INTO versioned_state(
                    key, value_json, version, created_at, updated_at
                ) VALUES (?, ?, 1, ?, ?)
                """,
                (effect_key, effect_json, at, at),
            )
            conn.execute(
                """
                UPDATE publications
                SET status = 'publishing', response_json = ?, updated_at = ?
                WHERE id = ? AND state = 'in_flight'
                """,
                (response_json, at, publication_id),
            )
            self._append_event_tx(
                conn,
                "state.created",
                {
                    "key": effect_key,
                    "version": 1,
                    "value_sha256": _sha256_text(effect_json),
                },
                aggregate_type="state",
                aggregate_id=effect_key,
                output_sha256=_sha256_text(effect_json),
                created_at=at,
            )
            self._append_event_tx(
                conn,
                "publication.in_flight",
                {
                    "publication_id": publication_id,
                    "target": publication["target"],
                    "from_state": "in_flight",
                    "to_state": "in_flight",
                    "status": "publishing",
                    "response": dict(response),
                },
                aggregate_type="publication",
                aggregate_id=publication_id,
                stage="publish_sending",
                input_sha256=publication["request_sha256"],
                created_at=at,
            )
            refreshed = conn.execute(
                "SELECT * FROM publications WHERE id = ?", (publication_id,)
            ).fetchone()
            assert refreshed is not None
            return self._publication_from_row(refreshed)

    def claim_candidate_physical_effect_send(
        self,
        effect_key: str,
        *,
        candidate_id: str,
        candidate_state: str,
        candidate_version: int,
        candidate_content_sha256: str,
        action: str,
        identity: Mapping[str, Any],
        send_attempt_id: str | None,
        now: float | None = None,
    ) -> VersionedStateRecord:
        """Atomically fence candidate mutation and claim one physical write.

        The task-level preflight is intentionally repeated under the same
        SQLite write lock that creates the external-effect claim. Therefore a
        concurrent rework transition either wins first (and no remote write is
        authorized) or observes this durable fence and is rejected.
        """

        _require_text(effect_key, "effect_key")
        _require_text(candidate_id, "candidate_id")
        if candidate_state not in CANDIDATE_STATES:
            raise ValueError("candidate_state must be a valid candidate state")
        if (
            not isinstance(candidate_version, int)
            or isinstance(candidate_version, bool)
            or candidate_version <= 0
        ):
            raise ValueError("candidate_version must be a positive integer")
        _validate_sha256(candidate_content_sha256, "candidate_content_sha256")
        if action not in _CANDIDATE_PHYSICAL_EFFECT_ACTIONS:
            raise ValueError("action is not a fenced physical effect")
        if not isinstance(identity, Mapping):
            raise TypeError("identity must be a mapping")
        required_identity = {
            "candidate_id": candidate_id,
            "candidate_state": candidate_state,
            "candidate_version": candidate_version,
            "candidate_content_sha256": candidate_content_sha256,
            "action": action,
        }
        for name, expected in required_identity.items():
            if identity.get(name) != expected:
                raise ValueError(f"physical effect identity {name} mismatch")
        value = {**dict(identity), "status": "sending"}
        if send_attempt_id is not None:
            _require_text(send_attempt_id, "send_attempt_id")
            value["send_attempt_id"] = send_attempt_id
        value_json = _json_dumps(value)
        at = self._now(now)
        with self._write() as conn:
            candidate = conn.execute(
                "SELECT * FROM candidates WHERE id = ?", (candidate_id,)
            ).fetchone()
            if candidate is None:
                raise NotFoundError(f"candidate {candidate_id!r} does not exist")
            if (
                candidate["state"] != candidate_state
                or int(candidate["version"]) != candidate_version
                or _sha256_text(candidate["content_json"])
                != candidate_content_sha256
            ):
                raise StateConflictError(
                    "candidate was retracted or revised before the physical send"
                )
            row = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (effect_key,)
            ).fetchone()
            if row is not None:
                prior = _json_loads(row["value_json"])
                if not isinstance(prior, Mapping) or any(
                    prior.get(name) != expected
                    for name, expected in identity.items()
                ):
                    raise StateConflictError(
                        "candidate physical-effect claim identity mismatch"
                    )
                if prior.get("status") != "prepared":
                    raise StateConflictError(
                        "candidate physical effect already has a durable owner"
                    )
                new_version = int(row["version"]) + 1
                conn.execute(
                    """
                    UPDATE versioned_state
                    SET value_json = ?, version = ?, updated_at = ?
                    WHERE key = ? AND version = ?
                    """,
                    (value_json, new_version, at, effect_key, int(row["version"])),
                )
                event_kind = "state.updated"
                prior_sha256 = _sha256_text(row["value_json"])
            else:
                new_version = 1
                conn.execute(
                    """
                    INSERT INTO versioned_state(
                        key, value_json, version, created_at, updated_at
                    ) VALUES (?, ?, 1, ?, ?)
                    """,
                    (effect_key, value_json, at, at),
                )
                event_kind = "state.created"
                prior_sha256 = None
            value_sha256 = _sha256_text(value_json)
            self._append_event_tx(
                conn,
                event_kind,
                {
                    "key": effect_key,
                    "version": new_version,
                    "value_sha256": value_sha256,
                },
                aggregate_type="state",
                aggregate_id=effect_key,
                input_sha256=prior_sha256,
                output_sha256=value_sha256,
                created_at=at,
            )
            row = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (effect_key,)
            ).fetchone()
            assert row is not None
            return self._state_from_row(row)

    def finish_candidate_publication_send(
        self,
        publication_id: str,
        *,
        candidate_id: str,
        candidate_version: int,
        status: str,
        receipt_sha256: str | None = None,
        now: float | None = None,
    ) -> VersionedStateRecord | None:
        """Resolve a candidate send fence after confirmation or reconciliation."""

        if status not in {"confirmed", "failed", "ambiguous"}:
            raise ValueError("candidate publication effect has invalid status")
        if receipt_sha256 is not None:
            _validate_sha256(receipt_sha256, "receipt_sha256")
        key = _candidate_publish_effect_key(candidate_id, candidate_version)
        at = self._now(now)
        with self._write() as conn:
            row = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (key,)
            ).fetchone()
            if row is None:
                return None
            value = _json_loads(row["value_json"])
            if not isinstance(value, dict) or value.get("publication_id") != publication_id:
                raise StateConflictError("candidate publication fence identity mismatch")
            current_status = value.get("status")
            if current_status == status and value.get("receipt_sha256") == receipt_sha256:
                return self._state_from_row(row)
            if current_status != "sending":
                raise StateConflictError(
                    f"candidate publication fence is already {current_status!r}"
                )
            value["status"] = status
            if receipt_sha256 is not None:
                value["receipt_sha256"] = receipt_sha256
            value_json = _json_dumps(value)
            new_version = int(row["version"]) + 1
            conn.execute(
                """
                UPDATE versioned_state
                SET value_json = ?, version = ?, updated_at = ?
                WHERE key = ? AND version = ?
                """,
                (value_json, new_version, at, key, int(row["version"])),
            )
            self._append_event_tx(
                conn,
                "state.updated",
                {
                    "key": key,
                    "version": new_version,
                    "value_sha256": _sha256_text(value_json),
                },
                aggregate_type="state",
                aggregate_id=key,
                input_sha256=_sha256_text(row["value_json"]),
                output_sha256=_sha256_text(value_json),
                created_at=at,
            )
            refreshed = conn.execute(
                "SELECT * FROM versioned_state WHERE key = ?", (key,)
            ).fetchone()
            assert refreshed is not None
            return self._state_from_row(refreshed)

    def update_publication_intent(
        self,
        target: str,
        idempotency_key: str,
        new_state: str,
        **fields: Any,
    ) -> PublicationRecord:
        """Convenience form of transition keyed by the reconciliation identity."""

        current = self.get_publication_intent(target, idempotency_key)
        if current is None:
            raise NotFoundError(
                f"publication intent {(target, idempotency_key)!r} does not exist"
            )
        return self.transition_publication(current.id, new_state, **fields)

    def list_publications(
        self,
        *,
        target: str | None = None,
        state: str | None = None,
        candidate_id: str | None = None,
        limit: int = 100,
    ) -> list[PublicationRecord]:
        _limit(limit)
        if state is not None and state not in PUBLICATION_STATES:
            raise ValueError(f"invalid publication state {state!r}")
        clauses: list[str] = []
        params: list[Any] = []
        for column, value in (
            ("target", target),
            ("state", state),
            ("candidate_id", candidate_id),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                params.append(value)
        where = "" if not clauses else f"WHERE {' AND '.join(clauses)}"
        params.append(limit)
        with self._read() as conn:
            rows = conn.execute(
                f"SELECT * FROM publications {where} ORDER BY created_at, id LIMIT ?",
                params,
            ).fetchall()
        return [self._publication_from_row(row) for row in rows]

    def quick_check(self) -> str:
        with self._read() as conn:
            rows = conn.execute("PRAGMA quick_check").fetchall()
        return "\n".join(str(row[0]) for row in rows)

    def stats(self) -> dict[str, Any]:
        with self._read() as conn:
            counts = {
                table: int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                for table in (
                    "events",
                    "tasks",
                    "task_attempts",
                    "candidates",
                    "candidate_artifacts",
                    "task_derived_applications",
                    "versioned_state",
                    "evaluations",
                    "experiences",
                    "publications",
                )
            }
            chain = conn.execute(
                "SELECT event_count, head_seq, head_hash FROM event_chain_state WHERE singleton = 1"
            ).fetchone()
        return {
            "schema_version": SCHEMA_VERSION,
            "journal_mode": self.journal_mode,
            "counts": counts,
            "event_count": int(chain["event_count"]) if chain else None,
            "event_head_seq": chain["head_seq"] if chain else None,
            "event_head_hash": chain["head_hash"] if chain else None,
        }

    def checkpoint_wal(self, mode: str = "PASSIVE") -> tuple[int, int, int]:
        normalized = mode.upper()
        if normalized not in {"PASSIVE", "FULL", "RESTART", "TRUNCATE"}:
            raise ValueError("WAL checkpoint mode must be PASSIVE, FULL, RESTART, or TRUNCATE")
        with self._lock:
            self._ensure_open()
            row = self._conn.execute(f"PRAGMA wal_checkpoint({normalized})").fetchone()
        return int(row[0]), int(row[1]), int(row[2])


__all__ = [
    "AttemptRecord",
    "CANDIDATE_STATES",
    "CandidateArtifactRecord",
    "CandidateRecord",
    "ChainVerification",
    "DerivedApplicationRecord",
    "DurableStore",
    "EvaluationRecord",
    "EventChainError",
    "EventRecord",
    "ExperienceRecord",
    "IdempotencyConflictError",
    "LeaseLostError",
    "NotFoundError",
    "PUBLICATION_STATES",
    "PUBLICATION_REMOTE_STATUSES",
    "PublicationRecord",
    "SCHEMA_VERSION",
    "StateConflictError",
    "StoreClosedError",
    "StoreError",
    "TASK_STATES",
    "TaskRecord",
    "VersionedStateRecord",
    "ZERO_HASH",
]
