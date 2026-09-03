"""Minimal durable ledger for credential-bearing Factory effects.

The ledger is deliberately not a product store or workflow engine. It records
one exact request before network I/O, fences the send with a random token, and
retains enough content identity to recover a proven success without ever
blindly retrying an unknown outcome.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Optional

from workshop._validation import require_sha256, utc_now
from workshop.errors import (
    AmbiguousEffectError,
    ContractError,
    EffectError,
    ReceiptError,
    StateConflict,
)
from workshop.runtime.contracts import Receipt


_SCHEMA_VERSION = 3
_KINDS = frozenset(
    (
        "factory-import",
        "factory-content",
        "factory-part-colors",
        "factory-publish",
    )
)
_STATES = frozenset(("planned", "sending", "succeeded", "rejected", "unknown"))


def _text(value: Any, label: str, maximum: int = 512) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded control-free text" % label)
    return value


def _error_text(value: Any) -> str:
    """Bound arbitrary exception/HTTP text without breaking terminalization."""

    observed = str(value) if value is not None else ""
    normalized = " ".join(observed.split())
    normalized = "".join(
        character
        for character in normalized
        if ord(character) >= 32 and ord(character) != 127
    )
    if not normalized:
        normalized = "unspecified Factory effect error"
    return normalized[:4_096]


def _json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("effect state accepts only finite JSON") from exc


def _json_object(value: Optional[str], label: str) -> Optional[Mapping[str, Any]]:
    if value is None:
        return None
    try:
        decoded = json.loads(value)
    except (TypeError, ValueError) as exc:
        raise StateConflict("%s is malformed" % label) from exc
    if not isinstance(decoded, Mapping):
        raise StateConflict("%s must be an object" % label)
    return dict(decoded)


@dataclass(frozen=True)
class EffectIntent:
    """One immutable effect identity plus its current durable outcome."""

    intent_id: str
    idempotency_key: str
    kind: str
    product_id: str
    request_sha256: str
    pack_sha256: str
    handoff_artifact_sha256: str
    product_artifact_sha256: str
    release_sha256: str
    playtest_evidence_sha256: str
    state: str
    request: Mapping[str, Any]
    response: Optional[Mapping[str, Any]]
    receipt: Optional[Receipt]
    error: Optional[str]
    effect_token: Optional[str]
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        _text(self.intent_id, "effect intent id")
        _text(self.idempotency_key, "effect idempotency key")
        if self.kind not in _KINDS or self.state not in _STATES:
            raise StateConflict("effect intent has an unsupported kind or state")
        _text(self.product_id, "effect product id")
        for name in (
            "request_sha256",
            "pack_sha256",
            "handoff_artifact_sha256",
            "product_artifact_sha256",
            "release_sha256",
            "playtest_evidence_sha256",
        ):
            require_sha256(getattr(self, name), "effect %s" % name)
        _json(dict(self.request))
        if self.response is not None:
            _json(dict(self.response))
        if self.receipt is not None and not isinstance(self.receipt, Receipt):
            raise StateConflict("effect receipt is malformed")
        if self.error is not None:
            _text(self.error, "effect error", 4_096)
        if self.effect_token is not None:
            _text(self.effect_token, "effect token")


class EffectLedger:
    """Private SQLite outbox for the three Factory effects in one Wish run."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if self.path.is_symlink():
            raise ContractError("effect ledger path must not be a symlink")
        parent_missing = not self.path.parent.exists()
        self.path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        if parent_missing:
            os.chmod(self.path.parent, 0o700)
        self._initialize()
        self._secure_permissions()

    def _secure_permissions(self) -> None:
        for candidate in (self.path, Path(str(self.path) + "-journal")):
            try:
                os.chmod(candidate, 0o600)
            except FileNotFoundError:
                pass

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=30.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        connection.execute("PRAGMA journal_mode = DELETE")
        self._secure_permissions()
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()
            self._secure_permissions()

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except Exception:
                connection.rollback()
                raise
            else:
                connection.commit()

    def _initialize(self) -> None:
        with self._connection() as connection:
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                if not str(row[0]).startswith("sqlite_")
            }
            expected = {"effect_ledger_meta", "effect_intents"}
            if tables and tables != expected:
                raise ContractError(
                    "effect ledger is not the native Factory effect schema"
                )
            if not tables:
                connection.executescript(
                    """
                    CREATE TABLE effect_ledger_meta (
                        schema_version INTEGER NOT NULL
                    );
                    INSERT INTO effect_ledger_meta(schema_version) VALUES (3);
                    CREATE TABLE effect_intents (
                        id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL UNIQUE,
                        kind TEXT NOT NULL CHECK(kind IN ('factory-import','factory-content',
                            'factory-part-colors','factory-publish')),
                        product_id TEXT NOT NULL,
                        request_sha256 TEXT NOT NULL,
                        pack_sha256 TEXT NOT NULL,
                        handoff_artifact_sha256 TEXT NOT NULL,
                        product_artifact_sha256 TEXT NOT NULL,
                        release_sha256 TEXT NOT NULL,
                        playtest_evidence_sha256 TEXT NOT NULL,
                        state TEXT NOT NULL CHECK(state IN ('planned','sending','succeeded','rejected','unknown')),
                        request_json TEXT NOT NULL,
                        response_json TEXT,
                        receipt_json TEXT,
                        error TEXT,
                        effect_token TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    CREATE INDEX effect_product_kind
                        ON effect_intents(product_id, kind, created_at);
                    """
                )
            version = connection.execute(
                "SELECT schema_version FROM effect_ledger_meta"
            ).fetchone()
            if version is not None and version[0] == 1:
                connection.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE effect_intents_v2 (
                        id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL UNIQUE,
                        kind TEXT NOT NULL CHECK(kind IN ('factory-import','factory-content','factory-publish')),
                        product_id TEXT NOT NULL,
                        request_sha256 TEXT NOT NULL,
                        pack_sha256 TEXT NOT NULL,
                        handoff_artifact_sha256 TEXT NOT NULL,
                        product_artifact_sha256 TEXT NOT NULL,
                        release_sha256 TEXT NOT NULL,
                        playtest_evidence_sha256 TEXT NOT NULL,
                        state TEXT NOT NULL CHECK(state IN ('planned','sending','succeeded','rejected','unknown')),
                        request_json TEXT NOT NULL,
                        response_json TEXT,
                        receipt_json TEXT,
                        error TEXT,
                        effect_token TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    INSERT INTO effect_intents_v2
                        SELECT * FROM effect_intents;
                    DROP TABLE effect_intents;
                    ALTER TABLE effect_intents_v2 RENAME TO effect_intents;
                    CREATE INDEX effect_product_kind
                        ON effect_intents(product_id, kind, created_at);
                    UPDATE effect_ledger_meta SET schema_version=2;
                    COMMIT;
                    """
                )
                version = connection.execute(
                    "SELECT schema_version FROM effect_ledger_meta"
                ).fetchone()
            if version is not None and version[0] == 2:
                connection.executescript(
                    """
                    BEGIN IMMEDIATE;
                    CREATE TABLE effect_intents_v3 (
                        id TEXT PRIMARY KEY,
                        idempotency_key TEXT NOT NULL UNIQUE,
                        kind TEXT NOT NULL CHECK(kind IN ('factory-import','factory-content',
                            'factory-part-colors','factory-publish')),
                        product_id TEXT NOT NULL,
                        request_sha256 TEXT NOT NULL,
                        pack_sha256 TEXT NOT NULL,
                        handoff_artifact_sha256 TEXT NOT NULL,
                        product_artifact_sha256 TEXT NOT NULL,
                        release_sha256 TEXT NOT NULL,
                        playtest_evidence_sha256 TEXT NOT NULL,
                        state TEXT NOT NULL CHECK(state IN ('planned','sending','succeeded','rejected','unknown')),
                        request_json TEXT NOT NULL,
                        response_json TEXT,
                        receipt_json TEXT,
                        error TEXT,
                        effect_token TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                    INSERT INTO effect_intents_v3
                        SELECT * FROM effect_intents;
                    DROP TABLE effect_intents;
                    ALTER TABLE effect_intents_v3 RENAME TO effect_intents;
                    CREATE INDEX effect_product_kind
                        ON effect_intents(product_id, kind, created_at);
                    UPDATE effect_ledger_meta SET schema_version=3;
                    COMMIT;
                    """
                )
                version = connection.execute(
                    "SELECT schema_version FROM effect_ledger_meta"
                ).fetchone()
            if version is None or version[0] != _SCHEMA_VERSION:
                raise ContractError("effect ledger schema version is unsupported")

    @staticmethod
    def _intent(row: sqlite3.Row) -> EffectIntent:
        receipt_value = _json_object(row["receipt_json"], "effect receipt")
        return EffectIntent(
            intent_id=row["id"],
            idempotency_key=row["idempotency_key"],
            kind=row["kind"],
            product_id=row["product_id"],
            request_sha256=row["request_sha256"],
            pack_sha256=row["pack_sha256"],
            handoff_artifact_sha256=row["handoff_artifact_sha256"],
            product_artifact_sha256=row["product_artifact_sha256"],
            release_sha256=row["release_sha256"],
            playtest_evidence_sha256=row["playtest_evidence_sha256"],
            state=row["state"],
            request=_json_object(row["request_json"], "effect request") or {},
            response=_json_object(row["response_json"], "effect response"),
            receipt=Receipt.from_dict(receipt_value) if receipt_value is not None else None,
            error=row["error"],
            effect_token=row["effect_token"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def get(self, intent_id: str) -> EffectIntent:
        intent_id = _text(intent_id, "effect intent id")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM effect_intents WHERE id=?", (intent_id,)
            ).fetchone()
        if row is None:
            raise KeyError("unknown effect intent %r" % intent_id)
        return self._intent(row)

    def latest(self, product_id: str, kind: str) -> Optional[EffectIntent]:
        product_id = _text(product_id, "effect product id")
        if kind not in _KINDS:
            raise ContractError("effect kind is unsupported")
        with self._connection() as connection:
            row = connection.execute(
                """SELECT * FROM effect_intents
                   WHERE product_id=? AND kind=?
                   ORDER BY created_at DESC, id DESC LIMIT 1""",
                (product_id, kind),
            ).fetchone()
        return self._intent(row) if row is not None else None

    @classmethod
    def inspect_latest(
        cls, path: Path, product_id: str, kind: str
    ) -> Optional[EffectIntent]:
        """Read one existing ledger without creating, migrating, or chmodding it."""

        product_id = _text(product_id, "effect product id")
        if kind not in _KINDS:
            raise ContractError("effect kind is unsupported")
        path = Path(path)
        try:
            identity = path.lstat()
        except OSError as exc:
            raise StateConflict("effect ledger is unavailable") from exc
        if (
            stat.S_ISLNK(identity.st_mode)
            or not stat.S_ISREG(identity.st_mode)
            or stat.S_IMODE(identity.st_mode) != 0o600
        ):
            raise StateConflict("effect ledger must be a private regular file")
        connection: Optional[sqlite3.Connection] = None
        try:
            connection = sqlite3.connect(
                path.absolute().as_uri() + "?mode=ro",
                timeout=30.0,
                isolation_level=None,
                uri=True,
            )
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only = ON")
            connection.execute("PRAGMA busy_timeout = 30000")
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                ).fetchall()
                if not str(row[0]).startswith("sqlite_")
            }
            if tables != {"effect_ledger_meta", "effect_intents"}:
                raise StateConflict("effect ledger schema is unavailable")
            versions = connection.execute(
                "SELECT schema_version FROM effect_ledger_meta"
            ).fetchall()
            if len(versions) != 1 or versions[0][0] != _SCHEMA_VERSION:
                raise StateConflict("effect ledger schema version is unavailable")
            row = connection.execute(
                """SELECT * FROM effect_intents
                   WHERE product_id=? AND kind=?
                   ORDER BY created_at DESC, id DESC LIMIT 1""",
                (product_id, kind),
            ).fetchone()
        except sqlite3.Error as exc:
            raise StateConflict("effect ledger could not be inspected") from exc
        finally:
            if connection is not None:
                connection.close()
        return cls._intent(row) if row is not None else None

    def prepare(
        self,
        *,
        kind: str,
        product_id: str,
        request: Mapping[str, Any],
        pack_sha256: str,
        handoff_artifact_sha256: str,
        product_artifact_sha256: str,
        release_sha256: str,
        playtest_evidence_sha256: str,
    ) -> EffectIntent:
        if kind not in _KINDS:
            raise ContractError("effect kind is unsupported")
        product_id = _text(product_id, "effect product id")
        if not isinstance(request, Mapping):
            raise ContractError("effect request must be an object")
        request_document = dict(request)
        request_json = _json(request_document)
        request_sha256 = hashlib.sha256(request_json.encode("utf-8")).hexdigest()
        bindings = {
            "pack_sha256": pack_sha256,
            "handoff_artifact_sha256": handoff_artifact_sha256,
            "product_artifact_sha256": product_artifact_sha256,
            "release_sha256": release_sha256,
            "playtest_evidence_sha256": playtest_evidence_sha256,
        }
        for name, digest in bindings.items():
            bindings[name] = require_sha256(digest, "effect %s" % name)
        identity = {
            "schema_version": 1,
            "kind": kind,
            "product_id": product_id,
            "request_sha256": request_sha256,
            **bindings,
        }
        identity_sha256 = hashlib.sha256(_json(identity).encode("utf-8")).hexdigest()
        intent_id = identity_sha256
        idempotency_key = "autonomous-workshop-%s" % identity_sha256
        now = utc_now()
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM effect_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if existing is not None:
                intent = self._intent(existing)
                if intent.request != request_document:
                    raise StateConflict("effect request drift under one identity")
                if intent.state == "rejected":
                    connection.execute(
                        """UPDATE effect_intents
                           SET state='planned', response_json=NULL,
                               receipt_json=NULL, error=NULL, effect_token=NULL,
                               updated_at=?
                           WHERE id=?""",
                        (now, intent_id),
                    )
                    reopened = connection.execute(
                        "SELECT * FROM effect_intents WHERE id=?", (intent_id,)
                    ).fetchone()
                    if reopened is None:  # pragma: no cover - same transaction
                        raise StateConflict("reopened effect intent disappeared")
                    return self._intent(reopened)
                return intent
            blockers = connection.execute(
                """SELECT * FROM effect_intents
                   WHERE product_id=? AND kind=? AND state != 'rejected'
                   ORDER BY created_at DESC, id DESC""",
                (product_id, kind),
            ).fetchall()
            if blockers:
                state = blockers[0]["state"]
                if state in ("sending", "unknown"):
                    raise AmbiguousEffectError(
                        "an earlier %s outcome is unknown; reconcile it before new bytes"
                        % kind
                    )
                raise StateConflict(
                    "product already has a different durable %s intent" % kind
                )
            connection.execute(
                """INSERT INTO effect_intents(
                       id, idempotency_key, kind, product_id, request_sha256,
                       pack_sha256, handoff_artifact_sha256,
                       product_artifact_sha256, release_sha256,
                       playtest_evidence_sha256, state, request_json,
                       response_json, receipt_json, error, effect_token,
                       created_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'planned', ?, NULL,
                             NULL, NULL, NULL, ?, ?)""",
                (
                    intent_id,
                    idempotency_key,
                    kind,
                    product_id,
                    request_sha256,
                    bindings["pack_sha256"],
                    bindings["handoff_artifact_sha256"],
                    bindings["product_artifact_sha256"],
                    bindings["release_sha256"],
                    bindings["playtest_evidence_sha256"],
                    request_json,
                    now,
                    now,
                ),
            )
        return self.get(intent_id)

    def begin(self, intent_id: str) -> EffectIntent:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM effect_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown effect intent %r" % intent_id)
            state = row["state"]
            if state == "succeeded":
                return self._intent(row)
            if state == "rejected":
                raise EffectError("Factory previously rejected this exact effect")
            if state in ("sending", "unknown"):
                raise AmbiguousEffectError(
                    "Factory effect may already have happened; authenticated reconciliation is required"
                )
            effect_token = secrets.token_hex(32)
            connection.execute(
                """UPDATE effect_intents SET state='sending', effect_token=?,
                       error=NULL, updated_at=? WHERE id=?""",
                (effect_token, utc_now(), intent_id),
            )
        return self.get(intent_id)

    def _assert_receipt(self, intent: EffectIntent, receipt: Receipt) -> None:
        if not isinstance(receipt, Receipt) or receipt.adapter != "factory":
            raise ReceiptError("effect success requires a Factory Receipt")
        receipt.assert_payload(intent.pack_sha256)
        receipt.assert_artifact(intent.product_artifact_sha256)
        details = receipt.details
        expected = {
            "product_id": intent.product_id,
            "effect_request_sha256": intent.request_sha256,
            "effect_idempotency_key": intent.idempotency_key,
            "release_sha256": intent.release_sha256,
            "playtest_evidence_sha256": intent.playtest_evidence_sha256,
            "handoff_artifact_sha256": intent.handoff_artifact_sha256,
        }
        if any(details.get(name) != value for name, value in expected.items()):
            raise ReceiptError("Factory Receipt is not bound to the exact effect intent")

    def _finish(
        self,
        intent_id: str,
        *,
        target: str,
        effect_token: Optional[str],
        error: Optional[str] = None,
        response: Optional[Mapping[str, Any]] = None,
        receipt: Optional[Receipt] = None,
        reconcile: bool = False,
    ) -> EffectIntent:
        if target not in ("succeeded", "rejected", "unknown"):
            raise ContractError("effect terminal state is unsupported")
        response_json = _json(dict(response)) if response is not None else None
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM effect_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown effect intent %r" % intent_id)
            intent = self._intent(row)
            allowed = (
                intent.state in ("planned", "sending", "unknown")
                if reconcile
                else intent.state == "sending"
            )
            if not allowed:
                if target == "succeeded" and intent.state == "succeeded":
                    if receipt is None or intent.receipt != receipt:
                        raise StateConflict("completed Factory effect receipt changed")
                    return intent
                raise StateConflict(
                    "effect intent is %s and cannot become %s" % (intent.state, target)
                )
            if not reconcile and (
                not effect_token or effect_token != intent.effect_token
            ):
                raise StateConflict("effect token is stale")
            if target == "succeeded":
                if receipt is None:
                    raise ReceiptError("effect success requires a Receipt")
                self._assert_receipt(intent, receipt)
            elif receipt is not None:
                raise ContractError("non-success effect state cannot store a Receipt")
            safe_error = _error_text(error) if error is not None else None
            connection.execute(
                """UPDATE effect_intents SET state=?, response_json=COALESCE(?, response_json),
                       receipt_json=?, error=?, effect_token=NULL, updated_at=?
                   WHERE id=?""",
                (
                    target,
                    response_json,
                    _json(receipt.to_dict()) if receipt is not None else None,
                    safe_error,
                    utc_now(),
                    intent_id,
                ),
            )
        return self.get(intent_id)

    def mark_succeeded(
        self,
        intent_id: str,
        effect_token: str,
        receipt: Receipt,
        response: Mapping[str, Any],
    ) -> EffectIntent:
        return self._finish(
            intent_id,
            target="succeeded",
            effect_token=effect_token,
            receipt=receipt,
            response=response,
        )

    def resolve_succeeded(
        self,
        intent_id: str,
        receipt: Receipt,
        response: Mapping[str, Any],
    ) -> EffectIntent:
        return self._finish(
            intent_id,
            target="succeeded",
            effect_token=None,
            receipt=receipt,
            response=response,
            reconcile=True,
        )

    def mark_rejected(
        self,
        intent_id: str,
        effect_token: str,
        error: str,
        response: Optional[Mapping[str, Any]] = None,
    ) -> EffectIntent:
        return self._finish(
            intent_id,
            target="rejected",
            effect_token=effect_token,
            error=error,
            response=response,
        )

    def mark_unknown(
        self,
        intent_id: str,
        effect_token: str,
        error: str,
        response: Optional[Mapping[str, Any]] = None,
    ) -> EffectIntent:
        return self._finish(
            intent_id,
            target="unknown",
            effect_token=effect_token,
            error=error,
            response=response,
        )

    def strand_as_unknown(self, intent_id: str, error: str) -> EffectIntent:
        """Convert a crash-left send into unknown without reopening it."""

        intent = self.get(intent_id)
        if intent.state != "sending":
            raise StateConflict("only a sending effect can be stranded")
        return self._finish(
            intent_id,
            target="unknown",
            effect_token=None,
            error=error,
            reconcile=True,
        )


__all__ = ["EffectIntent", "EffectLedger"]
