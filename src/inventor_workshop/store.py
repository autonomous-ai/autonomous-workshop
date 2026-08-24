"""SQLite-backed state, leases, budgets, events, and publish intents.

SQLite is in Python's standard library and gives every driver path the same
transaction boundary.  This replaces a recurring failure mode in the source
inventors: the daemon respected a JSON budget or lease while a manual command
silently bypassed it.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import urllib.parse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional

from .errors import (
    AmbiguousPublishError,
    AmbiguousSendError,
    BudgetExceeded,
    ContractError,
    LeaseBusy,
    ReceiptError,
    StateConflict,
)
from .models import PublicationReceipt, Stamp, require_sha256, utc_now

SCHEMA_VERSION = 3
MAX_LEASE_SECONDS = 24 * 60 * 60
_LAUNCH_KEYS = {
    "artifact_sha256": (
        "_workshop_artifact_sha256",
        "_foundation_artifact_sha256",
        "_core_artifact_sha256",
    ),
    "owner_id": (
        "_workshop_owner_id",
        "_foundation_owner_id",
        "_core_owner_id",
    ),
    "api_origin": (
        "_workshop_api_origin",
        "_foundation_api_origin",
        "_core_api_origin",
    ),
}


def _required_text(value: Any, label: str, maximum: int = 256) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError(
            "%s must be a non-empty control-free string of at most %d characters"
            % (label, maximum)
        )
    return value


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
        raise ContractError("durable state accepts only finite JSON values") from exc


def _object(value: Optional[str]) -> Any:
    return json.loads(value) if value else None


def _launch_value(request: Mapping[str, Any], name: str) -> Any:
    keys = _LAUNCH_KEYS[name]
    present = [(key, request.get(key)) for key in keys if request.get(key) is not None]
    if len({json.dumps(value, sort_keys=True) for _, value in present}) > 1:
        raise ContractError(
            "launch request has conflicting current and legacy %s" % name
        )
    return present[0][1] if present else None


def _launch_request_identity(request: Mapping[str, Any]) -> Mapping[str, Any]:
    """Compare schema-v1 and schema-v2 launch requests by meaning."""

    identity = dict(request)
    for keys in _LAUNCH_KEYS.values():
        for key in keys:
            identity.pop(key, None)
    for name in sorted(_LAUNCH_KEYS):
        identity["_workshop_%s" % name] = _launch_value(request, name)
    return identity


def _validate_live_request(
    request: Mapping[str, Any], persisted_request: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Validate the exact rich Shop request persisted before public visibility."""

    if not isinstance(request, Mapping):
        raise ContractError("live request must be an object")
    document = _object(_json(dict(request)))
    allowed = {"api_origin", "owner_id", "listing", "attachments", "title", "proof"}
    if set(document) - allowed or not {"api_origin", "owner_id"} <= set(document):
        raise ContractError("live request contains unsupported fields")
    if (
        document.get("api_origin") != _launch_value(persisted_request, "api_origin")
        or document.get("owner_id") != _launch_value(persisted_request, "owner_id")
    ):
        raise ContractError(
            "live request must preserve the persisted API origin and owner"
        )
    listing = document.get("listing")
    if listing is not None and (
        not isinstance(listing, Mapping)
        or set(listing) != {"price_cents"}
        or not isinstance(listing.get("price_cents"), int)
        or isinstance(listing.get("price_cents"), bool)
        or not 100 <= listing["price_cents"] <= 1_000_000
    ):
        raise ContractError("live listing must contain one valid price_cents")
    title = document.get("title")
    if title is not None and (
        not isinstance(title, str)
        or not title.strip()
        or len(title) > 120
        or any(ord(character) < 32 or ord(character) == 127 for character in title)
    ):
        raise ContractError("live title must be 1..120 control-free characters")
    attachments = document.get("attachments")
    if attachments is not None:
        if not isinstance(attachments, list) or not 1 <= len(attachments) <= 12:
            raise ContractError("live attachments must contain 1..12 items")
        for item in attachments:
            if (
                not isinstance(item, Mapping)
                or set(item) != {"kind", "url"}
                or item.get("kind") not in ("image", "video")
                or not isinstance(item.get("url"), str)
            ):
                raise ContractError("live attachment is malformed")
            parsed = urllib.parse.urlsplit(item["url"])
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username is not None
                or parsed.password is not None
                or any(
                    ord(character) < 32 or ord(character) == 127
                    for character in item["url"]
                )
            ):
                raise ContractError("live attachment URL must be absolute HTTPS")
    proof = document.get("proof")
    bound_instructions = persisted_request.get("_workshop_instructions_sha256")
    bound_playtest = persisted_request.get("_workshop_playtest_evidence_sha256")
    if bound_instructions is not None and proof is None:
        raise StateConflict(
            "Instructions-owned Shop requests require sealed public proof"
        )
    if proof is not None:
        if not isinstance(proof, Mapping):
            raise ContractError("live proof must be an object")
        allowed_proof = {
            "instructions_sha256",
            "playtest_evidence_sha256",
            "page_url",
            "media_sha256",
            "page_content_sha256",
            "listing_request_sha256",
        }
        if set(proof) - allowed_proof or "instructions_sha256" not in proof:
            raise ContractError("live proof contains unsupported fields")
        for name in (
            "instructions_sha256",
            "playtest_evidence_sha256",
            "page_content_sha256",
            "listing_request_sha256",
        ):
            if proof.get(name) is not None:
                require_sha256(proof[name], "live proof %s" % name)
        page_url = proof.get("page_url")
        if page_url is not None:
            if not isinstance(page_url, str):
                raise ContractError("live proof page_url must be absolute HTTPS")
            parsed_page = urllib.parse.urlsplit(page_url)
            if (
                parsed_page.scheme != "https"
                or not parsed_page.hostname
                or parsed_page.username is not None
                or parsed_page.password is not None
                or parsed_page.query
                or parsed_page.fragment
                or any(ord(character) < 32 or ord(character) == 127 for character in page_url)
            ):
                raise ContractError("live proof page_url must be absolute HTTPS")
        media = proof.get("media_sha256")
        if media is not None and (
            not isinstance(media, Mapping)
            or not media
            or any(not isinstance(role, str) or not role for role in media)
        ):
            raise ContractError("live proof media_sha256 must be a non-empty object")
        if isinstance(media, Mapping):
            for role, digest in media.items():
                require_sha256(digest, "live proof media_sha256[%s]" % role)
        if proof["instructions_sha256"] != persisted_request.get(
            "_workshop_instructions_sha256"
        ):
            raise StateConflict(
                "live proof Instructions hash does not match the sealed draft request"
            )
        if bound_playtest is not None and proof.get(
            "playtest_evidence_sha256"
        ) != bound_playtest:
            raise StateConflict(
                "live proof Playtest hash does not match the sealed draft request"
            )
        if bound_instructions is not None:
            required_proof = {
                "instructions_sha256",
                "playtest_evidence_sha256",
                "page_url",
                "media_sha256",
                "page_content_sha256",
                "listing_request_sha256",
            }
            if set(proof) != required_proof:
                raise StateConflict(
                    "Instructions-owned Shop proof is incomplete"
                )
        api_request = {
            name: document[name]
            for name in ("title", "listing", "attachments")
            if name in document
        }
        expected_request_sha256 = hashlib.sha256(
            _json(api_request).encode("utf-8")
        ).hexdigest()
        if (
            proof.get("listing_request_sha256") is not None
            and proof["listing_request_sha256"] != expected_request_sha256
        ):
            raise StateConflict(
                "live proof request hash does not match the exact Shop request"
            )
    return document


class InventorStore:
    """One durable database per inventor runtime root."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if self.path.is_symlink():
            raise ContractError("state database path must not be a symlink")
        parent_missing = not self.path.parent.exists()
        self.path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        if parent_missing:
            os.chmod(str(self.path.parent), 0o700)
        self._initialize()
        self._secure_permissions()

    def _secure_permissions(self) -> None:
        for candidate in (
            self.path,
            Path(str(self.path) + "-wal"),
            Path(str(self.path) + "-shm"),
        ):
            try:
                os.chmod(str(candidate), 0o600)
            except FileNotFoundError:
                pass

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=30.0, isolation_level=None)
        self._secure_permissions()
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 30000")
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Yield a short-lived connection and always close its file handle."""
        connection = self._connect()
        try:
            yield connection
        finally:
            connection.close()
            self._secure_permissions()

    def _initialize(self) -> None:
        with self._connection() as connection:
            workshop_meta_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='workshop_meta'"
            ).fetchone()
            legacy_meta_exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='core_meta'"
            ).fetchone()
            if workshop_meta_exists is not None and legacy_meta_exists is not None:
                raise ContractError(
                    "state database contains both workshop_meta and legacy core_meta"
                )
            meta_table = (
                "workshop_meta"
                if workshop_meta_exists is not None
                else "core_meta" if legacy_meta_exists is not None else None
            )
            version = None
            observed_version = None
            if meta_table is not None:
                version = connection.execute(
                    "SELECT value FROM %s WHERE key='schema_version'" % meta_table
                ).fetchone()
                if version is not None:
                    try:
                        observed_version = int(version[0])
                    except (TypeError, ValueError) as exc:
                        raise ContractError(
                            "state database schema version is corrupt"
                        ) from exc
                    if observed_version not in (1, 2, SCHEMA_VERSION):
                        raise ContractError(
                            "state database schema version %s is unsupported; Workshop requires %s"
                            % (observed_version, SCHEMA_VERSION)
                        )
            if meta_table == "core_meta":
                connection.execute(
                    "ALTER TABLE core_meta RENAME TO workshop_meta"
                )
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    stage TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    artifact_sha256 TEXT,
                    metadata_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS workshop_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id TEXT NOT NULL REFERENCES products(id),
                    kind TEXT NOT NULL,
                    from_stage TEXT,
                    to_stage TEXT,
                    artifact_sha256 TEXT,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    previous_sha256 TEXT,
                    event_sha256 TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS events_product_sequence
                    ON events(product_id, sequence);
                CREATE TABLE IF NOT EXISTS leases (
                    product_id TEXT PRIMARY KEY REFERENCES products(id),
                    holder TEXT NOT NULL,
                    token TEXT NOT NULL UNIQUE,
                    acquired_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS budget_spend (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    spend_key TEXT UNIQUE,
                    bucket TEXT NOT NULL,
                    product_id TEXT,
                    phase TEXT NOT NULL,
                    amount_micros INTEGER NOT NULL CHECK(amount_micros >= 0),
                    note TEXT NOT NULL,
                    policy_starts_at TEXT,
                    policy_ends_at TEXT,
                    policy_limit_micros INTEGER,
                    remaining_after_micros INTEGER,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS budget_bucket_time
                    ON budget_spend(bucket, created_at);
                CREATE TABLE IF NOT EXISTS budget_policies (
                    bucket TEXT PRIMARY KEY,
                    limit_micros INTEGER NOT NULL CHECK(limit_micros >= 0),
                    starts_at TEXT NOT NULL,
                    ends_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS publish_intents (
                    id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL REFERENCES products(id),
                    packet_sha256 TEXT NOT NULL,
                    remote_slug_hint TEXT,
                    state TEXT NOT NULL CHECK(state IN (
                        'planned', 'sending', 'unknown', 'rejected', 'succeeded',
                        'publishing', 'live_unknown', 'live'
                    )),
                    request_json TEXT NOT NULL,
                    live_request_json TEXT,
                    live_attempts_json TEXT,
                    effect_token TEXT,
                    response_json TEXT,
                    receipt_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(product_id, packet_sha256)
                );
                CREATE TABLE IF NOT EXISTS send_intents (
                    id TEXT PRIMARY KEY,
                    product_id TEXT NOT NULL REFERENCES products(id),
                    pack_sha256 TEXT NOT NULL,
                    artifact_sha256 TEXT NOT NULL,
                    door_name TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN (
                        'planned', 'sending', 'unknown', 'succeeded'
                    )),
                    request_json TEXT NOT NULL,
                    effect_token TEXT,
                    stamp_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(product_id, pack_sha256, door_name)
                );
                CREATE TABLE IF NOT EXISTS shop_effects (
                    id TEXT PRIMARY KEY,
                    publish_intent_id TEXT NOT NULL
                        REFERENCES publish_intents(id),
                    kind TEXT NOT NULL CHECK(kind IN (
                        'media-upload', 'use-case', 'story-blocks'
                    )),
                    effect_key TEXT NOT NULL,
                    state TEXT NOT NULL CHECK(state IN (
                        'planned', 'sending', 'unknown', 'rejected', 'succeeded'
                    )),
                    request_json TEXT NOT NULL,
                    effect_token TEXT,
                    response_json TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(publish_intent_id, kind, effect_key)
                );
                CREATE INDEX IF NOT EXISTS shop_effects_publish_intent
                    ON shop_effects(publish_intent_id, kind, effect_key);
                """
            )
            columns = {
                row[1] for row in connection.execute("PRAGMA table_info(publish_intents)")
            }
            if "live_request_json" not in columns:
                connection.execute(
                    "ALTER TABLE publish_intents ADD COLUMN live_request_json TEXT"
                )
            if "live_attempts_json" not in columns:
                connection.execute(
                    "ALTER TABLE publish_intents ADD COLUMN live_attempts_json TEXT"
                )
            if "effect_token" not in columns:
                connection.execute(
                    "ALTER TABLE publish_intents ADD COLUMN effect_token TEXT"
                )
            budget_columns = {
                row[1] for row in connection.execute("PRAGMA table_info(budget_spend)")
            }
            if "spend_key" not in budget_columns:
                connection.execute("ALTER TABLE budget_spend ADD COLUMN spend_key TEXT")
            for column, declaration in (
                ("policy_starts_at", "TEXT"),
                ("policy_ends_at", "TEXT"),
                ("policy_limit_micros", "INTEGER"),
                ("remaining_after_micros", "INTEGER"),
            ):
                if column not in budget_columns:
                    connection.execute(
                        "ALTER TABLE budget_spend ADD COLUMN %s %s"
                        % (column, declaration)
                    )
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS unique_budget_spend_key
                   ON budget_spend(spend_key) WHERE spend_key IS NOT NULL"""
            )
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS one_active_publish_per_product
                   ON publish_intents(product_id)
                   WHERE state IN (
                       'planned', 'sending', 'unknown', 'succeeded',
                       'publishing', 'live_unknown', 'live'
                   )"""
            )
            connection.execute(
                """CREATE UNIQUE INDEX IF NOT EXISTS one_active_send_per_product_door
                   ON send_intents(product_id, door_name)
                   WHERE state IN ('planned', 'sending', 'unknown')"""
            )
            if version is None:
                connection.execute(
                    "INSERT INTO workshop_meta(key, value) VALUES ('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            elif observed_version in (1, 2):
                connection.execute(
                    "UPDATE workshop_meta SET value=? WHERE key='schema_version'",
                    (str(SCHEMA_VERSION),),
                )

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self._connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
            self._secure_permissions()

    @staticmethod
    def _row(row: sqlite3.Row) -> Dict[str, Any]:
        value = dict(row)
        for key in (
            "metadata_json",
            "payload_json",
            "request_json",
            "live_request_json",
            "live_attempts_json",
            "response_json",
            "receipt_json",
            "stamp_json",
        ):
            if key in value:
                value[key[:-5]] = _object(value.pop(key))
        return value

    @staticmethod
    def _assert_lease_fence(
        connection: sqlite3.Connection,
        product_id: str,
        lease_token: Optional[str],
        now: Optional[str] = None,
    ) -> None:
        observed = now or utc_now()
        lease = connection.execute(
            "SELECT holder, token, expires_at FROM leases WHERE product_id=?",
            (product_id,),
        ).fetchone()
        if lease is None:
            if lease_token is not None:
                raise StateConflict("lease token is stale; product has no active lease")
            return
        if lease["expires_at"] <= observed:
            connection.execute("DELETE FROM leases WHERE product_id=?", (product_id,))
            if lease_token is not None:
                raise StateConflict("lease token expired before the state mutation")
            return
        if lease_token != lease["token"]:
            raise LeaseBusy(
                "%s is actively leased by %s; the current fencing token is required"
                % (product_id, lease["holder"])
            )

    def _append_event(
        self,
        connection: sqlite3.Connection,
        product_id: str,
        kind: str,
        from_stage: Optional[str],
        to_stage: Optional[str],
        artifact_sha256: Optional[str],
        payload: Mapping[str, Any],
        created_at: str,
    ) -> str:
        last = connection.execute(
            "SELECT event_sha256 FROM events WHERE product_id=? ORDER BY sequence DESC LIMIT 1",
            (product_id,),
        ).fetchone()
        previous = last[0] if last else None
        document = {
            "product_id": product_id,
            "kind": kind,
            "from_stage": from_stage,
            "to_stage": to_stage,
            "artifact_sha256": artifact_sha256,
            "payload": dict(payload),
            "created_at": created_at,
            "previous_sha256": previous,
        }
        event_sha = hashlib.sha256(_json(document).encode("utf-8")).hexdigest()
        connection.execute(
            """INSERT INTO events(
                   product_id, kind, from_stage, to_stage, artifact_sha256,
                   payload_json, created_at, previous_sha256, event_sha256
               ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                product_id,
                kind,
                from_stage,
                to_stage,
                artifact_sha256,
                _json(dict(payload)),
                created_at,
                previous,
                event_sha,
            ),
        )
        return event_sha

    def register_product(
        self,
        product_id: str,
        initial_stage: str,
        metadata: Optional[Mapping[str, Any]] = None,
        artifact_sha256: Optional[str] = None,
    ) -> Dict[str, Any]:
        _required_text(product_id, "product_id")
        _required_text(initial_stage, "initial_stage", 100)
        if metadata is not None and not isinstance(metadata, Mapping):
            raise ContractError("product metadata must be an object")
        if artifact_sha256:
            require_sha256(artifact_sha256, "product artifact_sha256")
        now = utc_now()
        with self._transaction() as connection:
            try:
                connection.execute(
                    "INSERT INTO products VALUES (?, ?, 0, ?, ?, ?, ?)",
                    (product_id, initial_stage, artifact_sha256, _json(metadata or {}), now, now),
                )
            except sqlite3.IntegrityError:
                raise StateConflict("product %r already exists" % product_id)
            self._append_event(
                connection,
                product_id,
                "registered",
                None,
                initial_stage,
                artifact_sha256,
                metadata or {},
                now,
            )
        return self.get_product(product_id)

    def get_product(self, product_id: str) -> Dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if row is None:
            raise KeyError("unknown product %r" % product_id)
        return self._row(row)

    def list_products(self, stage: Optional[str] = None) -> List[Dict[str, Any]]:
        if stage is not None:
            _required_text(stage, "product stage", 100)
        with self._connection() as connection:
            if stage is None:
                rows = connection.execute(
                    "SELECT * FROM products ORDER BY id"
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM products WHERE stage=? ORDER BY id", (stage,)
                ).fetchall()
        return [self._row(row) for row in rows]

    def _transition(
        self,
        product_id: str,
        from_stage: str,
        to_stage: str,
        expected_revision: int,
        artifact_sha256: Optional[str],
        payload: Optional[Mapping[str, Any]] = None,
        lease_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """CAS primitive for :class:`Pipeline`; callers must not bypass policy."""
        if artifact_sha256:
            require_sha256(artifact_sha256, "product artifact_sha256")
        now = utc_now()
        with self._transaction() as connection:
            row = connection.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
            if row is None:
                raise KeyError("unknown product %r" % product_id)
            self._assert_lease_fence(connection, product_id, lease_token, now)
            if row["stage"] != from_stage or row["revision"] != expected_revision:
                raise StateConflict(
                    "%s is %s@%s, expected %s@%s"
                    % (product_id, row["stage"], row["revision"], from_stage, expected_revision)
                )
            next_artifact = artifact_sha256 or row["artifact_sha256"]
            revision = expected_revision + 1
            connection.execute(
                """UPDATE products SET stage=?, revision=?, artifact_sha256=?, updated_at=?
                   WHERE id=? AND stage=? AND revision=?""",
                (to_stage, revision, next_artifact, now, product_id, from_stage, expected_revision),
            )
            self._append_event(
                connection,
                product_id,
                "transition",
                from_stage,
                to_stage,
                next_artifact,
                payload or {},
                now,
            )
        return self.get_product(product_id)

    def events(self, product_id: str) -> List[Dict[str, Any]]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM events WHERE product_id=? ORDER BY sequence", (product_id,)
            ).fetchall()
        return [self._row(row) for row in rows]

    def verify_event_chain(self, product_id: str) -> bool:
        try:
            product = self.get_product(product_id)
            events = self.events(product_id)
        except (ContractError, TypeError, ValueError):
            return False
        if not events:
            return False
        if not isinstance(product.get("metadata"), Mapping):
            return False
        previous = None
        stage = None
        artifact_sha256 = None
        revision = -1
        metadata = None
        for index, event in enumerate(events):
            if not isinstance(event.get("payload"), Mapping):
                return False
            document = {
                "product_id": event["product_id"],
                "kind": event["kind"],
                "from_stage": event["from_stage"],
                "to_stage": event["to_stage"],
                "artifact_sha256": event["artifact_sha256"],
                "payload": event["payload"],
                "created_at": event["created_at"],
                "previous_sha256": previous,
            }
            expected = hashlib.sha256(_json(document).encode("utf-8")).hexdigest()
            if event["previous_sha256"] != previous or event["event_sha256"] != expected:
                return False
            if index == 0:
                if (
                    event["kind"] != "registered"
                    or event["from_stage"] is not None
                    or not event["to_stage"]
                ):
                    return False
                stage = event["to_stage"]
                artifact_sha256 = event["artifact_sha256"]
                metadata = event["payload"]
                revision = 0
            else:
                if (
                    event["kind"] != "transition"
                    or event["from_stage"] != stage
                    or not event["to_stage"]
                ):
                    return False
                stage = event["to_stage"]
                artifact_sha256 = event["artifact_sha256"]
                revision += 1
            previous = event["event_sha256"]
        return (
            product["stage"] == stage
            and product["revision"] == revision
            and product["artifact_sha256"] == artifact_sha256
            and product["metadata"] == metadata
            and product["created_at"] == events[0]["created_at"]
            and product["updated_at"] == events[-1]["created_at"]
        )

    def acquire_lease(self, product_id: str, holder: str, ttl_seconds: int = 2700) -> str:
        _required_text(product_id, "lease product_id")
        _required_text(holder, "lease holder")
        if (
            not isinstance(ttl_seconds, int)
            or isinstance(ttl_seconds, bool)
            or not 1 <= ttl_seconds <= MAX_LEASE_SECONDS
        ):
            raise ContractError(
                "lease ttl_seconds must be an integer from 1 to %d"
                % MAX_LEASE_SECONDS
            )
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        expires = (now_dt + timedelta(seconds=ttl_seconds)).isoformat()
        token = secrets.token_hex(16)
        with self._transaction() as connection:
            if connection.execute("SELECT 1 FROM products WHERE id=?", (product_id,)).fetchone() is None:
                raise KeyError("unknown product %r" % product_id)
            existing = connection.execute(
                "SELECT holder, expires_at FROM leases WHERE product_id=?", (product_id,)
            ).fetchone()
            if existing is not None and existing["expires_at"] > now:
                raise LeaseBusy(
                    "%s is leased by %s until %s"
                    % (product_id, existing["holder"], existing["expires_at"])
                )
            connection.execute("DELETE FROM leases WHERE product_id=?", (product_id,))
            connection.execute(
                "INSERT INTO leases VALUES (?, ?, ?, ?, ?)",
                (product_id, holder, token, now, expires),
            )
        return token

    def release_lease(self, product_id: str, token: str) -> bool:
        with self._transaction() as connection:
            cursor = connection.execute(
                "DELETE FROM leases WHERE product_id=? AND token=?", (product_id, token)
            )
            return cursor.rowcount == 1

    def renew_lease(self, product_id: str, token: str, ttl_seconds: int = 2700) -> str:
        """Extend a still-current lease without minting a new fencing token."""
        _required_text(product_id, "lease product_id")
        _required_text(token, "lease token")
        if (
            not isinstance(ttl_seconds, int)
            or isinstance(ttl_seconds, bool)
            or not 1 <= ttl_seconds <= MAX_LEASE_SECONDS
        ):
            raise ContractError(
                "lease ttl_seconds must be an integer from 1 to %d"
                % MAX_LEASE_SECONDS
            )
        now_dt = datetime.now(timezone.utc)
        now = now_dt.isoformat()
        expires = (now_dt + timedelta(seconds=ttl_seconds)).isoformat()
        with self._transaction() as connection:
            lease = connection.execute(
                "SELECT token, expires_at FROM leases WHERE product_id=?", (product_id,)
            ).fetchone()
            if lease is None or lease["token"] != token or lease["expires_at"] <= now:
                raise StateConflict("lease is missing, expired, or has been replaced")
            connection.execute(
                "UPDATE leases SET expires_at=? WHERE product_id=? AND token=?",
                (expires, product_id, token),
            )
        return expires

    @staticmethod
    def _utc_boundary(value: str, label: str) -> str:
        if not isinstance(value, str):
            raise ContractError("%s must be an ISO-8601 timestamp" % label)
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ContractError("%s must be an ISO-8601 timestamp" % label) from exc
        if parsed.tzinfo is None:
            raise ContractError("%s must include a timezone" % label)
        return parsed.astimezone(timezone.utc).isoformat()

    def configure_budget(
        self,
        bucket: str,
        limit_micros: int,
        starts_at: str,
        ends_at: str,
    ) -> Dict[str, Any]:
        if not isinstance(bucket, str) or not bucket:
            raise ContractError("budget bucket is required")
        if (
            not isinstance(limit_micros, int)
            or isinstance(limit_micros, bool)
            or limit_micros < 0
        ):
            raise ContractError("budget limit must be non-negative integer micros")
        starts = self._utc_boundary(starts_at, "budget starts_at")
        ends = self._utc_boundary(ends_at, "budget ends_at")
        if starts >= ends:
            raise ContractError("budget ends_at must be after starts_at")
        now = self._utc_boundary(utc_now(), "Workshop clock")
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM budget_policies WHERE bucket=?", (bucket,)
            ).fetchone()
            if existing is not None:
                if (
                    existing["limit_micros"] == limit_micros
                    and existing["starts_at"] == starts
                    and existing["ends_at"] == ends
                ):
                    return dict(existing)
                if now < existing["ends_at"] or starts < existing["ends_at"]:
                    raise StateConflict(
                        "budget policy is immutable until its current window ends"
                    )
            connection.execute(
                """INSERT INTO budget_policies(
                       bucket, limit_micros, starts_at, ends_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(bucket) DO UPDATE SET
                       limit_micros=excluded.limit_micros,
                       starts_at=excluded.starts_at,
                       ends_at=excluded.ends_at,
                       updated_at=excluded.updated_at""",
                (bucket, limit_micros, starts, ends, now),
            )
            row = connection.execute(
                "SELECT * FROM budget_policies WHERE bucket=?", (bucket,)
            ).fetchone()
        return dict(row)

    def budget_status(self, bucket: str) -> Dict[str, Any]:
        """Return the persisted policy and ledger usage without reserving spend."""
        _required_text(bucket, "budget bucket")
        now = self._utc_boundary(utc_now(), "Workshop clock")
        with self._connection() as connection:
            policy = connection.execute(
                "SELECT * FROM budget_policies WHERE bucket=?", (bucket,)
            ).fetchone()
            if policy is None:
                raise KeyError("unknown budget bucket %r" % bucket)
            used = connection.execute(
                "SELECT COALESCE(SUM(amount_micros), 0) FROM budget_spend "
                "WHERE bucket=? AND created_at>=? AND created_at<?",
                (bucket, policy["starts_at"], policy["ends_at"]),
            ).fetchone()[0]
        result = dict(policy)
        result.update(
            {
                "used_micros": used,
                "remaining_micros": max(0, policy["limit_micros"] - used),
                "active": policy["starts_at"] <= now < policy["ends_at"],
            }
        )
        return result

    def spend(
        self,
        bucket: str,
        spend_key: str,
        amount_micros: int,
        phase: str,
        product_id: Optional[str] = None,
        note: str = "",
        lease_token: Optional[str] = None,
    ) -> int:
        if not isinstance(bucket, str) or not bucket or not isinstance(spend_key, str) or not spend_key:
            raise ContractError("budget bucket and idempotency spend_key are required")
        if not isinstance(phase, str) or not phase:
            raise ContractError("budget phase is required")
        if (
            not isinstance(amount_micros, int)
            or isinstance(amount_micros, bool)
            or amount_micros < 0
        ):
            raise ContractError("budget amount must be non-negative integer micros")
        # Budget windows and lease expiry are security decisions.  They must
        # use the Workshop clock, never a timestamp supplied by an inventor.
        now = self._utc_boundary(utc_now(), "Workshop clock")
        with self._transaction() as connection:
            existing = connection.execute(
                "SELECT * FROM budget_spend WHERE spend_key=?", (spend_key,)
            ).fetchone()
            if existing is not None:
                if (
                    existing["bucket"] != bucket
                    or existing["product_id"] != product_id
                    or existing["phase"] != phase
                    or existing["amount_micros"] != amount_micros
                    or existing["note"] != note
                ):
                    raise StateConflict("budget spend_key was reused for a different reservation")
                if existing["remaining_after_micros"] is None:
                    raise StateConflict(
                        "legacy budget reservation lacks an immutable policy snapshot"
                    )
                return existing["remaining_after_micros"]
            if product_id is not None:
                if connection.execute(
                    "SELECT 1 FROM products WHERE id=?", (product_id,)
                ).fetchone() is None:
                    raise KeyError("unknown product %r" % product_id)
                self._assert_lease_fence(connection, product_id, lease_token, now)
            policy = connection.execute(
                "SELECT * FROM budget_policies WHERE bucket=?", (bucket,)
            ).fetchone()
            if policy is None:
                raise ContractError("budget bucket %r has no configured policy" % bucket)
            if not policy["starts_at"] <= now < policy["ends_at"]:
                raise BudgetExceeded("budget bucket %r is outside its active window" % bucket)
            used = connection.execute(
                "SELECT COALESCE(SUM(amount_micros), 0) FROM budget_spend "
                "WHERE bucket=? AND created_at>=? AND created_at<?",
                (bucket, policy["starts_at"], policy["ends_at"]),
            ).fetchone()[0]
            if used + amount_micros > policy["limit_micros"]:
                raise BudgetExceeded(
                    "%s budget: %d + %d exceeds %d micros"
                    % (bucket, used, amount_micros, policy["limit_micros"])
                )
            remaining = policy["limit_micros"] - used - amount_micros
            connection.execute(
                """INSERT INTO budget_spend(
                       spend_key, bucket, product_id, phase, amount_micros, note,
                       policy_starts_at, policy_ends_at, policy_limit_micros,
                       remaining_after_micros, created_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    spend_key,
                    bucket,
                    product_id,
                    phase,
                    amount_micros,
                    note,
                    policy["starts_at"],
                    policy["ends_at"],
                    policy["limit_micros"],
                    remaining,
                    now,
                ),
            )
        return remaining

    def prepare_send(
        self,
        product_id: str,
        pack_sha256: str,
        artifact_sha256: str,
        door_name: str,
        request: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Plan one generic Door effect before any external call."""

        product_id = _required_text(product_id, "product id")
        door_name = _required_text(door_name, "Door name")
        require_sha256(pack_sha256, "send Pack sha256")
        require_sha256(artifact_sha256, "send artifact_sha256")
        if not isinstance(request, Mapping):
            raise ContractError("send request must be an object")
        request_document = dict(request)
        request_json = _json(request_document)
        now = utc_now()
        intent_id = secrets.token_hex(16)
        with self._transaction() as connection:
            product = connection.execute(
                "SELECT artifact_sha256 FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if product is None:
                raise KeyError("unknown product %r" % product_id)
            self._assert_lease_fence(connection, product_id, lease_token, now)
            if product["artifact_sha256"] != artifact_sha256:
                raise StateConflict(
                    "send Pack artifact does not match the product's selected bytes"
                )
            existing = connection.execute(
                """SELECT * FROM send_intents
                   WHERE product_id=? AND pack_sha256=? AND door_name=?""",
                (product_id, pack_sha256, door_name),
            ).fetchone()
            if existing is not None:
                parsed = self._row(existing)
                if (
                    parsed["artifact_sha256"] != artifact_sha256
                    or parsed["request"] != request_document
                ):
                    raise StateConflict(
                        "send request drift for the same product Pack and Door"
                    )
                return parsed
            try:
                connection.execute(
                    """INSERT INTO send_intents(
                           id, product_id, pack_sha256, artifact_sha256,
                           door_name, state, request_json, effect_token,
                           stamp_json, error, created_at, updated_at
                       ) VALUES (?, ?, ?, ?, ?, 'planned', ?, NULL, NULL, NULL, ?, ?)""",
                    (
                        intent_id,
                        product_id,
                        pack_sha256,
                        artifact_sha256,
                        door_name,
                        request_json,
                        now,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise StateConflict(
                    "product already has an unresolved send through this Door"
                ) from exc
        return self.get_send_intent(intent_id)

    def get_send_intent(self, intent_id: str) -> Dict[str, Any]:
        intent_id = _required_text(intent_id, "send intent id")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM send_intents WHERE id=?", (intent_id,)
            ).fetchone()
        if row is None:
            raise KeyError("unknown send intent %r" % intent_id)
        return self._row(row)

    def latest_send_intent(
        self, product_id: str, door_name: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        product_id = _required_text(product_id, "product id")
        parameters: tuple = (product_id,)
        where = "product_id=?"
        if door_name is not None:
            door_name = _required_text(door_name, "Door name")
            where += " AND door_name=?"
            parameters = (product_id, door_name)
        with self._connection() as connection:
            row = connection.execute(
                """SELECT * FROM send_intents WHERE %s
                   ORDER BY created_at DESC, id DESC LIMIT 1""" % where,
                parameters,
            ).fetchone()
        return self._row(row) if row is not None else None

    def begin_send(
        self, intent_id: str, lease_token: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM send_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown send intent %r" % intent_id)
            self._assert_lease_fence(
                connection, row["product_id"], lease_token, utc_now()
            )
            if row["state"] in ("sending", "unknown"):
                raise AmbiguousSendError(
                    "send intent %s may already have crossed %s; reconcile before retry"
                    % (intent_id, row["door_name"])
                )
            if row["state"] == "succeeded":
                return self._row(row)
            if row["state"] != "planned":
                raise StateConflict(
                    "send intent %s is %s" % (intent_id, row["state"])
                )
            # The token identifies the logical effect, not a particular
            # process attempt.  Reuse it after authenticated reconciliation
            # proves no effect; an adapter can then enforce idempotency even
            # if its readback raced with a late remote completion.
            effect_token = row["effect_token"] or secrets.token_hex(16)
            connection.execute(
                """UPDATE send_intents
                   SET state='sending', effect_token=?, error=NULL, updated_at=?
                   WHERE id=?""",
                (effect_token, utc_now(), intent_id),
            )
        return self.get_send_intent(intent_id)

    def mark_send_unknown(
        self, intent_id: str, effect_token: str, error: str
    ) -> Dict[str, Any]:
        return self._set_send_intent_state(
            intent_id,
            "sending",
            "unknown",
            effect_token=effect_token,
            error=_required_text(error, "send error", maximum=4000),
        )

    def mark_send_succeeded(
        self, intent_id: str, effect_token: str, stamp: Stamp
    ) -> Dict[str, Any]:
        intent = self.get_send_intent(intent_id)
        self._assert_send_stamp(intent, stamp)
        return self._set_send_intent_state(
            intent_id,
            "sending",
            "succeeded",
            effect_token=effect_token,
            stamp=stamp,
        )

    def resolve_send_succeeded(
        self, intent_id: str, stamp: Stamp
    ) -> Dict[str, Any]:
        intent = self.get_send_intent(intent_id)
        if intent["state"] != "unknown":
            raise StateConflict("send intent %s is not unknown" % intent_id)
        self._assert_send_stamp(intent, stamp)
        return self._set_send_intent_state(
            intent_id, "unknown", "succeeded", stamp=stamp
        )

    def resolve_send_no_effect(self, intent_id: str) -> Dict[str, Any]:
        """Reset only after a qualified Door proves the effect did not occur."""

        return self._set_send_intent_state(
            intent_id,
            "unknown",
            "planned",
            error="Door reconciliation proved no effect",
        )

    def recover_stranded_send(self, intent_id: str, explanation: str) -> Dict[str, Any]:
        """Fence a process crash as unknown; never infer that no effect occurred."""

        intent = self.get_send_intent(intent_id)
        if intent["state"] != "sending":
            raise StateConflict("send intent %s is not sending" % intent_id)
        return self.mark_send_unknown(
            intent_id,
            intent.get("effect_token"),
            explanation,
        )

    @staticmethod
    def _assert_send_stamp(intent: Mapping[str, Any], stamp: Stamp) -> None:
        if not isinstance(stamp, Stamp):
            raise ReceiptError("send success requires a Stamp")
        stamp.assert_pack(intent["pack_sha256"])
        stamp.assert_artifact(intent["artifact_sha256"])
        if stamp.door != intent["door_name"]:
            raise ReceiptError("Stamp belongs to a different Door")

    def _set_send_intent_state(
        self,
        intent_id: str,
        expected: str,
        target: str,
        *,
        effect_token: Optional[str] = None,
        error: Optional[str] = None,
        stamp: Optional[Stamp] = None,
    ) -> Dict[str, Any]:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state, effect_token FROM send_intents WHERE id=?",
                (intent_id,),
            ).fetchone()
            if row is None:
                raise KeyError("unknown send intent %r" % intent_id)
            if row["state"] != expected:
                raise StateConflict(
                    "send intent %s is %s, expected %s"
                    % (intent_id, row["state"], expected)
                )
            if expected == "sending" and (
                not effect_token or row["effect_token"] != effect_token
            ):
                raise StateConflict("send effect token is stale")
            retained_effect_token = (
                row["effect_token"] if target in ("unknown", "planned") else None
            )
            connection.execute(
                """UPDATE send_intents
                   SET state=?, error=?, stamp_json=COALESCE(?, stamp_json),
                       effect_token=?, updated_at=? WHERE id=?""",
                (
                    target,
                    error,
                    _json(stamp.to_dict()) if stamp is not None else None,
                    retained_effect_token,
                    utc_now(),
                    intent_id,
                ),
            )
        return self.get_send_intent(intent_id)

    def prepare_publish(
        self,
        product_id: str,
        packet_sha256: str,
        request: Mapping[str, Any],
        remote_slug_hint: Optional[str] = None,
        lease_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        require_sha256(packet_sha256, "publish packet_sha256")
        now = utc_now()
        intent_id = secrets.token_hex(16)
        request_document = dict(request)
        if request_document.get("status") != "draft":
            raise ContractError("publish intent requires status=draft")
        artifact_sha256 = _launch_value(request_document, "artifact_sha256")
        require_sha256(
            artifact_sha256,
            "launch request artifact_sha256",
        )
        owner_id = _launch_value(request_document, "owner_id")
        if not isinstance(owner_id, str) or not owner_id:
            raise ContractError("launch request owner_id is required")
        api_origin = _launch_value(request_document, "api_origin")
        if not isinstance(api_origin, str):
            raise ContractError("launch request api_origin is required")
        parsed_origin = urllib.parse.urlsplit(api_origin)
        if (
            parsed_origin.scheme != "https"
            or not parsed_origin.hostname
            or parsed_origin.username is not None
            or parsed_origin.password is not None
            or parsed_origin.path not in ("", "/")
            or parsed_origin.query
            or parsed_origin.fragment
        ):
            raise ContractError("publish request API origin must be a bare HTTPS origin")
        with self._transaction() as connection:
            product = connection.execute(
                "SELECT artifact_sha256 FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if product is None:
                raise KeyError("unknown product %r" % product_id)
            self._assert_lease_fence(connection, product_id, lease_token, now)
            if (
                not product["artifact_sha256"]
                or product["artifact_sha256"]
                != artifact_sha256
            ):
                raise StateConflict(
                    "publication request artifact does not match the product's selected bytes"
                )
            existing = connection.execute(
                "SELECT * FROM publish_intents WHERE product_id=? AND packet_sha256=?",
                (product_id, packet_sha256),
            ).fetchone()
            if existing is not None:
                parsed = self._row(existing)
                if (
                    _launch_request_identity(parsed["request"])
                    != _launch_request_identity(request_document)
                    or parsed["remote_slug_hint"] != remote_slug_hint
                ):
                    raise StateConflict(
                        "publish request drift for the same product packet; "
                        "never substitute metadata under an existing intent"
                    )
                return parsed
            try:
                connection.execute(
                    """INSERT INTO publish_intents(
                           id, product_id, packet_sha256, remote_slug_hint, state,
                           request_json, live_request_json, live_attempts_json, effect_token,
                           response_json,
                           receipt_json, error, created_at, updated_at
                       ) VALUES (?, ?, ?, ?, 'planned', ?, NULL, NULL, NULL, NULL, NULL, NULL, ?, ?)""",
                    (
                        intent_id,
                        product_id,
                        packet_sha256,
                        remote_slug_hint,
                        _json(request_document),
                        now,
                        now,
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise StateConflict(
                    "product already has an active publication intent; reconcile it first"
                ) from exc
        return self.get_publish_intent(intent_id)

    def get_publish_intent(self, intent_id: str) -> Dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM publish_intents WHERE id=?", (intent_id,)
            ).fetchone()
        if row is None:
            raise KeyError("unknown publish intent %r" % intent_id)
        return self._row(row)

    def latest_publish_intent(
        self, product_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return the newest durable outbox intent for a product, if any.

        Inventor adapters use this read-only projection for operator status
        without querying Workshop's private schema.  Ordering includes the random
        intent id as a deterministic tie-breaker for clocks with coarse
        timestamp resolution.
        """
        product_id = _required_text(product_id, "product id")
        with self._connection() as connection:
            row = connection.execute(
                """SELECT * FROM publish_intents
                   WHERE product_id=?
                   ORDER BY created_at DESC, id DESC LIMIT 1""",
                (product_id,),
            ).fetchone()
        return self._row(row) if row is not None else None

    def prepare_shop_effect(
        self,
        publish_intent_id: str,
        kind: str,
        effect_key: str,
        request: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Bind one Instructions-owned Shop effect before touching the network.

        Import and the final draft-to-public transition already have dedicated
        outbox states.  Product-page images and curated copy happen between
        those boundaries, so they use small child effects tied to the same
        publication intent and sealed Instructions hash.
        """

        publish_intent_id = _required_text(
            publish_intent_id, "publish intent id"
        )
        if kind not in ("media-upload", "use-case", "story-blocks"):
            raise ContractError("Shop effect kind is not supported")
        effect_key = _required_text(effect_key, "Shop effect key")
        if not isinstance(request, Mapping) or not request:
            raise ContractError("Shop effect request must be a non-empty object")
        # Round-trip to detach nested caller-owned containers and reject
        # non-JSON values before they can become durable authority.
        request_document = _object(_json(dict(request)))
        instructions_sha256 = request_document.get("instructions_sha256")
        require_sha256(instructions_sha256, "Shop effect instructions_sha256")
        effect_id = secrets.token_hex(16)
        now = utc_now()
        with self._transaction() as connection:
            parent = connection.execute(
                "SELECT * FROM publish_intents WHERE id=?",
                (publish_intent_id,),
            ).fetchone()
            if parent is None:
                raise KeyError("unknown publish intent %r" % publish_intent_id)
            self._assert_lease_fence(
                connection, parent["product_id"], lease_token, now
            )
            launch_request = _object(parent["request_json"])
            if (
                not isinstance(launch_request, Mapping)
                or launch_request.get("_workshop_instructions_sha256")
                != instructions_sha256
            ):
                raise StateConflict(
                    "Shop effect Instructions hash does not match the sealed draft request"
                )
            existing = connection.execute(
                """SELECT * FROM shop_effects
                   WHERE publish_intent_id=? AND kind=? AND effect_key=?""",
                (publish_intent_id, kind, effect_key),
            ).fetchone()
            if existing is not None:
                parsed = self._row(existing)
                if parsed["request"] != request_document:
                    raise StateConflict(
                        "Shop effect request drifted under an existing durable key"
                    )
                return parsed
            if parent["state"] != "succeeded":
                raise StateConflict(
                    "Shop page effects require an authenticated private draft"
                )
            connection.execute(
                """INSERT INTO shop_effects(
                       id, publish_intent_id, kind, effect_key, state,
                       request_json, effect_token, response_json, error,
                       created_at, updated_at
                   ) VALUES (?, ?, ?, ?, 'planned', ?, NULL, NULL, NULL, ?, ?)""",
                (
                    effect_id,
                    publish_intent_id,
                    kind,
                    effect_key,
                    _json(request_document),
                    now,
                    now,
                ),
            )
        return self.get_shop_effect(effect_id)

    def get_shop_effect(self, effect_id: str) -> Dict[str, Any]:
        effect_id = _required_text(effect_id, "Shop effect id")
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM shop_effects WHERE id=?", (effect_id,)
            ).fetchone()
        if row is None:
            raise KeyError("unknown Shop effect %r" % effect_id)
        return self._row(row)

    def shop_effects_for_publish_intent(
        self, publish_intent_id: str
    ) -> List[Dict[str, Any]]:
        """Return the durable page effects used to verify final Shop readback."""

        publish_intent_id = _required_text(
            publish_intent_id, "publish intent id"
        )
        with self._connection() as connection:
            parent = connection.execute(
                "SELECT 1 FROM publish_intents WHERE id=?", (publish_intent_id,)
            ).fetchone()
            if parent is None:
                raise KeyError("unknown publish intent %r" % publish_intent_id)
            rows = connection.execute(
                """SELECT * FROM shop_effects
                   WHERE publish_intent_id=?
                   ORDER BY kind, effect_key, id""",
                (publish_intent_id,),
            ).fetchall()
        return [self._row(row) for row in rows]

    def begin_shop_effect(
        self, effect_id: str, lease_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fence an exact media/content request immediately before HTTP."""

        with self._transaction() as connection:
            row = connection.execute(
                """SELECT e.*, p.product_id, p.state AS publish_state
                   FROM shop_effects e
                   JOIN publish_intents p ON p.id=e.publish_intent_id
                   WHERE e.id=?""",
                (effect_id,),
            ).fetchone()
            if row is None:
                raise KeyError("unknown Shop effect %r" % effect_id)
            self._assert_lease_fence(
                connection, row["product_id"], lease_token, utc_now()
            )
            if row["state"] == "succeeded":
                return self.get_shop_effect(effect_id)
            if row["state"] in ("sending", "unknown"):
                raise AmbiguousPublishError(
                    "Shop effect %s may already have happened; reconcile before retry"
                    % effect_id
                )
            if row["state"] not in ("planned", "rejected"):
                raise StateConflict(
                    "Shop effect %s is %s" % (effect_id, row["state"])
                )
            if row["publish_state"] != "succeeded":
                raise StateConflict(
                    "Shop page effects require an authenticated private draft"
                )
            effect_token = secrets.token_hex(16)
            connection.execute(
                """UPDATE shop_effects
                   SET state='sending', effect_token=?, error=NULL, updated_at=?
                   WHERE id=?""",
                (effect_token, utc_now(), effect_id),
            )
        return self.get_shop_effect(effect_id)

    def mark_shop_effect_unknown(
        self, effect_id: str, effect_token: str, error: str
    ) -> Dict[str, Any]:
        return self._set_shop_effect_state(
            effect_id,
            "sending",
            "unknown",
            effect_token=effect_token,
            error=error,
        )

    def mark_shop_effect_rejected(
        self,
        effect_id: str,
        effect_token: str,
        error: str,
        response: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._set_shop_effect_state(
            effect_id,
            "sending",
            "rejected",
            effect_token=effect_token,
            error=error,
            response=response,
        )

    def mark_shop_effect_succeeded(
        self,
        effect_id: str,
        effect_token: str,
        response: Mapping[str, Any],
    ) -> Dict[str, Any]:
        return self._set_shop_effect_state(
            effect_id,
            "sending",
            "succeeded",
            effect_token=effect_token,
            response=response,
        )

    def resolve_shop_effect_succeeded(
        self, effect_id: str, response: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Resolve an ambiguous idempotent page write from authenticated readback."""

        return self._set_shop_effect_state(
            effect_id, "unknown", "succeeded", response=response
        )

    def _set_shop_effect_state(
        self,
        effect_id: str,
        expected: str,
        target: str,
        *,
        effect_token: Optional[str] = None,
        error: Optional[str] = None,
        response: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        if response is not None and not isinstance(response, Mapping):
            raise ContractError("Shop effect response must be an object")
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state, effect_token FROM shop_effects WHERE id=?",
                (effect_id,),
            ).fetchone()
            if row is None:
                raise KeyError("unknown Shop effect %r" % effect_id)
            if row["state"] != expected:
                raise StateConflict(
                    "Shop effect %s is %s, expected %s"
                    % (effect_id, row["state"], expected)
                )
            if expected == "sending" and (
                not effect_token or row["effect_token"] != effect_token
            ):
                raise StateConflict("Shop effect token is stale")
            connection.execute(
                """UPDATE shop_effects
                   SET state=?, effect_token=NULL, response_json=COALESCE(?, response_json),
                       error=?, updated_at=? WHERE id=?""",
                (
                    target,
                    _json(dict(response)) if response is not None else None,
                    error,
                    utc_now(),
                    effect_id,
                ),
            )
        return self.get_shop_effect(effect_id)

    def begin_publish(
        self, intent_id: str, lease_token: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM publish_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown publish intent %r" % intent_id)
            self._assert_lease_fence(
                connection, row["product_id"], lease_token, utc_now()
            )
            if row["state"] in ("sending", "unknown"):
                raise AmbiguousPublishError(
                    "intent %s may already have crossed the Shop Door; reconcile before retry"
                    % intent_id
                )
            if row["state"] in ("succeeded", "live"):
                return self._row(row)
            if row["state"] != "planned":
                raise StateConflict(
                    "intent %s is %s; create a new packet after correcting the rejection"
                    % (intent_id, row["state"])
                )
            effect_token = secrets.token_hex(16)
            connection.execute(
                """UPDATE publish_intents
                   SET state='sending', effect_token=?, updated_at=? WHERE id=?""",
                (effect_token, utc_now(), intent_id),
            )
        return self.get_publish_intent(intent_id)

    def mark_publish_unknown(
        self, intent_id: str, effect_token: str, error: str
    ) -> Dict[str, Any]:
        return self._set_intent_state(
            intent_id, "sending", "unknown", effect_token=effect_token, error=error
        )

    def mark_publish_rejected(
        self,
        intent_id: str,
        effect_token: str,
        error: str,
        response: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self._set_intent_state(
            intent_id,
            "sending",
            "rejected",
            effect_token=effect_token,
            error=error,
            response=response,
        )

    def mark_publish_succeeded(
        self,
        intent_id: str,
        effect_token: str,
        receipt: PublicationReceipt,
        response: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        intent = self.get_publish_intent(intent_id)
        self._assert_draft_receipt(intent, receipt)
        return self._set_intent_state(
            intent_id,
            "sending",
            "succeeded",
            effect_token=effect_token,
            response=response,
            receipt=receipt,
        )

    def mark_instructions_draft_ready(
        self,
        intent_id: str,
        receipt: PublicationReceipt,
        lease_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Bind a fully enriched private Shop draft to sealed Instructions.

        The import transition records the remote design before any page media
        or curated copy is written.  Instructions completes only after those
        durable child effects have succeeded and authenticated readback has
        produced ``receipt``.  This method enriches the existing draft receipt
        without changing the intent's terminal ``succeeded`` state; making the
        draft public remains a separate, explicit effect.
        """

        intent = self.get_publish_intent(intent_id)
        self._assert_draft_receipt(intent, receipt)
        if not receipt.is_verified_draft:
            raise ReceiptError(
                "Instructions completion requires authenticated private draft readback"
            )
        request = intent.get("request")
        if not isinstance(request, Mapping):
            raise ReceiptError("Instructions draft request is missing")
        instructions_sha256 = request.get("_workshop_instructions_sha256")
        playtest_sha256 = request.get("_workshop_playtest_evidence_sha256")
        require_sha256(instructions_sha256, "Instructions draft sha256")
        require_sha256(playtest_sha256, "Instructions Playtest evidence sha256")
        details = receipt.details
        required_details = {
            "cover_sha256",
            "cover_url",
            "instructions_sha256",
            "playtest_evidence_sha256",
            "page_url",
            "media_sha256",
            "page_content_sha256",
        }
        if not required_details <= set(details):
            raise ReceiptError("Instructions draft receipt proof is incomplete")
        if details.get("instructions_sha256") != instructions_sha256:
            raise ReceiptError("Instructions draft receipt describes different Instructions bytes")
        if details.get("playtest_evidence_sha256") != playtest_sha256:
            raise ReceiptError("Instructions draft receipt describes different Playtest evidence")
        cover_sha256 = request.get("_workshop_cover_sha256")
        require_sha256(cover_sha256, "Instructions draft cover sha256")
        if details.get("cover_sha256") != cover_sha256:
            raise ReceiptError("Instructions draft receipt describes different cover bytes")
        require_sha256(details.get("page_content_sha256"), "Instructions page content sha256")
        for url_name in ("page_url", "cover_url"):
            url = details.get(url_name)
            try:
                parsed_url = urllib.parse.urlsplit(url)
            except (TypeError, ValueError) as exc:
                raise ReceiptError(
                    "Instructions draft %s must be absolute HTTPS" % url_name
                ) from exc
            if (
                not isinstance(url, str)
                or parsed_url.scheme != "https"
                or not parsed_url.hostname
                or parsed_url.username is not None
                or parsed_url.password is not None
                or parsed_url.query
                or parsed_url.fragment
            ):
                raise ReceiptError(
                    "Instructions draft %s must be absolute HTTPS" % url_name
                )
        media = details.get("media_sha256")
        if not isinstance(media, Mapping) or not media:
            raise ReceiptError("Instructions draft media proof must be a non-empty object")
        for role, digest in media.items():
            _required_text(role, "Instructions media role")
            require_sha256(digest, "Instructions media sha256")

        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM publish_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown publish intent %r" % intent_id)
            self._assert_lease_fence(
                connection, row["product_id"], lease_token, utc_now()
            )
            if row["state"] != "succeeded":
                raise StateConflict(
                    "Instructions page effects require an authenticated private draft"
                )
            persisted = PublicationReceipt.from_dict(_object(row["receipt_json"]))
            self._assert_draft_receipt(self._row(row), persisted)
            import_response = _object(row["response_json"])
            imported_covers = (
                import_response.get("thumbnail_urls")
                if isinstance(import_response, Mapping)
                else None
            )
            if (
                not isinstance(imported_covers, list)
                or not imported_covers
                or imported_covers[0] != details.get("cover_url")
            ):
                raise ReceiptError(
                    "Instructions draft cover does not match authenticated import readback"
                )
            identity_fields = (
                "packet_sha256",
                "artifact_sha256",
                "design_id",
                "slug",
                "owner_id",
                "root_id",
                "current_history_id",
                "project_url",
            )
            if any(
                getattr(persisted, field) != getattr(receipt, field)
                for field in identity_fields
            ):
                raise ReceiptError(
                    "Instructions readback does not identify the imported draft history"
                )
            already_bound = persisted.details.get("instructions_sha256")
            if already_bound is not None:
                if persisted.to_dict() != receipt.to_dict():
                    raise StateConflict(
                        "completed Instructions draft receipt changed during replay"
                    )
                return self._row(row)

            effects = connection.execute(
                """SELECT kind, effect_key, state, request_json
                   FROM shop_effects WHERE publish_intent_id=?""",
                (intent_id,),
            ).fetchall()
            media_effects = {
                effect["effect_key"]: effect for effect in effects
                if effect["kind"] == "media-upload"
            }
            if set(media_effects) != set(media):
                raise ReceiptError(
                    "Instructions draft media proof does not match durable uploads"
                )
            for role, effect in media_effects.items():
                effect_request = _object(effect["request_json"])
                if (
                    effect["state"] != "succeeded"
                    or not isinstance(effect_request, Mapping)
                    or effect_request.get("instructions_sha256") != instructions_sha256
                    or effect_request.get("sha256") != media[role]
                ):
                    raise ReceiptError(
                        "Instructions draft media upload is not durably proven"
                    )
            if media.get("hero") != cover_sha256:
                raise ReceiptError(
                    "Instructions draft cover is not the sealed hero image"
                )
            if any(effect["state"] != "succeeded" for effect in effects):
                raise ReceiptError(
                    "Instructions draft still has an incomplete Shop page effect"
                )
            connection.execute(
                """UPDATE publish_intents SET receipt_json=?, updated_at=?
                   WHERE id=?""",
                (_json(receipt.to_dict()), utc_now(), intent_id),
            )
        return self.get_publish_intent(intent_id)

    def mark_publish_live(
        self, intent_id: str, effect_token: str, receipt: PublicationReceipt
    ) -> Dict[str, Any]:
        intent = self.get_publish_intent(intent_id)
        self._assert_live_receipt(intent, receipt)
        return self._set_intent_state(
            intent_id,
            "publishing",
            "live",
            effect_token=effect_token,
            receipt=receipt,
        )

    def begin_live(
        self,
        intent_id: str,
        request: Mapping[str, Any],
        lease_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Persist and fence the exact draft-to-public request before HTTP."""
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT * FROM publish_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown publish intent %r" % intent_id)
            self._assert_lease_fence(
                connection, row["product_id"], lease_token, utc_now()
            )
            if row["state"] != "succeeded":
                raise StateConflict(
                    "intent %s is %s, expected succeeded"
                    % (intent_id, row["state"])
                )
            persisted_request = _object(row["request_json"])
            if not isinstance(persisted_request, Mapping):
                raise StateConflict("persisted draft request is malformed")
            request_document = _validate_live_request(request, persisted_request)
            proof = request_document.get("proof")
            media_proof = proof.get("media_sha256") if isinstance(proof, Mapping) else None
            if isinstance(media_proof, Mapping):
                rows = connection.execute(
                    """SELECT state, request_json, response_json
                       FROM shop_effects
                       WHERE publish_intent_id=? AND kind='media-upload'""",
                    (intent_id,),
                ).fetchall()
                completed_media: Dict[str, str] = {}
                completed_urls = set()
                for effect in rows:
                    effect_request = _object(effect["request_json"])
                    effect_response = _object(effect["response_json"])
                    if (
                        effect["state"] != "succeeded"
                        or not isinstance(effect_request, Mapping)
                        or not isinstance(effect_response, Mapping)
                        or effect_request.get("instructions_sha256")
                        != proof.get("instructions_sha256")
                        or not isinstance(effect_request.get("role"), str)
                        or not isinstance(effect_response.get("url"), str)
                    ):
                        raise StateConflict(
                            "Instructions media proof requires completed durable uploads"
                        )
                    completed_media[effect_request["role"]] = effect_request.get(
                        "sha256"
                    )
                    completed_urls.add(effect_response["url"])
                if completed_media != dict(media_proof):
                    raise StateConflict(
                        "Instructions media hashes do not match completed uploads"
                    )
                attachments = request_document.get("attachments")
                if (
                    not isinstance(attachments, list)
                    or any(item.get("kind") != "image" for item in attachments)
                    or len(attachments) != len(completed_urls)
                    or {item.get("url") for item in attachments} != completed_urls
                ):
                    raise StateConflict(
                        "Instructions attachments do not match completed uploads"
                    )
            existing = _object(row["live_request_json"])
            if existing is not None and existing != request_document:
                raise StateConflict("live publish request changed under an existing intent")
            effect_token = secrets.token_hex(16)
            connection.execute(
                """UPDATE publish_intents
                   SET state='publishing', live_request_json=?, effect_token=?, updated_at=?
                   WHERE id=?""",
                (_json(request_document), effect_token, utc_now(), intent_id),
            )
        return self.get_publish_intent(intent_id)

    def mark_live_unknown(
        self, intent_id: str, effect_token: str, error: str
    ) -> Dict[str, Any]:
        return self._set_intent_state(
            intent_id,
            "publishing",
            "live_unknown",
            effect_token=effect_token,
            error=error,
        )

    def restore_draft_after_publish_rejection(
        self, intent_id: str, effect_token: str, error: str
    ) -> Dict[str, Any]:
        """A deterministic 4xx proves the public flip did not succeed."""
        with self._transaction() as connection:
            row = connection.execute(
                """SELECT state, effect_token, live_request_json, live_attempts_json
                   FROM publish_intents WHERE id=?""",
                (intent_id,),
            ).fetchone()
            if row is None:
                raise KeyError("unknown publish intent %r" % intent_id)
            if row["state"] != "publishing":
                raise StateConflict(
                    "intent %s is %s, expected publishing" % (intent_id, row["state"])
                )
            if not effect_token or row["effect_token"] != effect_token:
                raise StateConflict("live publication effect token is stale")
            attempts = _object(row["live_attempts_json"]) or []
            attempts.append(
                {
                    "request": _object(row["live_request_json"]),
                    "outcome": "rejected",
                    "error": error,
                    "observed_at": utc_now(),
                }
            )
            connection.execute(
                """UPDATE publish_intents
                   SET state='succeeded', error=?, live_request_json=NULL,
                       live_attempts_json=?, effect_token=NULL, updated_at=? WHERE id=?""",
                (error, _json(attempts), utc_now(), intent_id),
            )
        return self.get_publish_intent(intent_id)

    def resolve_live_as_public(
        self, intent_id: str, receipt: PublicationReceipt
    ) -> Dict[str, Any]:
        intent = self.get_publish_intent(intent_id)
        self._assert_live_receipt(intent, receipt)
        return self._set_intent_state(
            intent_id, "live_unknown", "live", receipt=receipt
        )

    def resolve_publish_unknown(
        self, intent_id: str, receipt: PublicationReceipt, explanation: str
    ) -> Dict[str, Any]:
        """Refuse manual resolution until the Shop Door exposes content proof."""
        del receipt, explanation
        intent = self.get_publish_intent(intent_id)
        if intent["state"] != "unknown":
            raise StateConflict("intent %s is not unknown" % intent_id)
        raise AmbiguousPublishError(
            "intent %s cannot be resolved from a caller-authored receipt; "
            "the Shop Door must return a Pack/tree identity or idempotency proof"
            % intent_id
        )

    @staticmethod
    def _assert_draft_receipt(
        intent: Mapping[str, Any], receipt: PublicationReceipt
    ) -> None:
        request = intent.get("request")
        if not isinstance(request, Mapping):
            raise ReceiptError("publish intent request is missing")
        receipt.assert_packet(intent["packet_sha256"])
        receipt.assert_artifact(_launch_value(request, "artifact_sha256"))
        receipt.assert_owner(_launch_value(request, "owner_id"))
        if receipt.status != "draft" or receipt.published_history_id is not None:
            raise ReceiptError("import success requires a private draft receipt")

    @classmethod
    def _assert_live_receipt(
        cls, intent: Mapping[str, Any], receipt: PublicationReceipt
    ) -> None:
        if not receipt.is_verified_public:
            raise ReceiptError("live requires public readback of the current history entry")
        raw_draft = intent.get("receipt")
        if not isinstance(raw_draft, Mapping):
            raise ReceiptError("live intent has no persisted draft receipt")
        try:
            draft = PublicationReceipt.from_dict(raw_draft)
        except (TypeError, ValueError, ContractError, ReceiptError) as exc:
            raise ReceiptError("persisted draft receipt is malformed") from exc
        cls._assert_draft_receipt(intent, draft)
        live_request = intent.get("live_request")
        if not isinstance(live_request, Mapping):
            raise ReceiptError("live intent has no persisted Shop request")
        listing = live_request.get("listing")
        if listing is not None and not isinstance(listing, Mapping):
            raise ReceiptError("live intent listing request is malformed")
        if isinstance(listing, Mapping):
            receipt.assert_listing(listing.get("price_cents"))
        proof = live_request.get("proof")
        if isinstance(proof, Mapping) and any(
            receipt.details.get(name) != value for name, value in proof.items()
        ):
            raise ReceiptError(
                "live receipt details do not match the persisted Instructions proof"
            )
        cls._assert_draft_receipt(
            intent,
            PublicationReceipt(
                packet_sha256=receipt.packet_sha256,
                artifact_sha256=receipt.artifact_sha256,
                design_id=receipt.design_id,
                slug=receipt.slug,
                owner_id=receipt.owner_id,
                root_id=receipt.root_id,
                current_history_id=receipt.current_history_id,
                published_history_id=None,
                status="draft",
                project_url=receipt.project_url,
                observed_at=receipt.observed_at,
            ),
        )
        identity_fields = [
            "packet_sha256",
            "artifact_sha256",
            "design_id",
            "owner_id",
            "root_id",
            "current_history_id",
        ]
        if live_request.get("title") is None:
            identity_fields.extend(("slug", "project_url"))
        if any(
            getattr(draft, field) != getattr(receipt, field)
            for field in identity_fields
        ):
            raise ReceiptError("live receipt does not identify the persisted draft history")

    def recover_stranded_intent(self, intent_id: str, explanation: str) -> Dict[str, Any]:
        """Operator-only crash recovery after proving no effect process remains."""
        intent = self.get_publish_intent(intent_id)
        if intent["state"] == "sending":
            return self._set_intent_state(
                intent_id,
                "sending",
                "unknown",
                effect_token=intent.get("effect_token"),
                error=explanation,
            )
        if intent["state"] == "publishing":
            return self._set_intent_state(
                intent_id,
                "publishing",
                "live_unknown",
                effect_token=intent.get("effect_token"),
                error=explanation,
            )
        raise StateConflict("intent %s is not stranded in an effect state" % intent_id)

    def _set_intent_state(
        self,
        intent_id: str,
        expected: str,
        target: str,
        effect_token: Optional[str] = None,
        error: Optional[str] = None,
        response: Optional[Mapping[str, Any]] = None,
        receipt: Optional[PublicationReceipt] = None,
    ) -> Dict[str, Any]:
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state, effect_token FROM publish_intents WHERE id=?", (intent_id,)
            ).fetchone()
            if row is None:
                raise KeyError("unknown publish intent %r" % intent_id)
            if row["state"] != expected:
                raise StateConflict(
                    "intent %s is %s, expected %s" % (intent_id, row["state"], expected)
                )
            if expected in ("sending", "publishing") and (
                not effect_token or row["effect_token"] != effect_token
            ):
                raise StateConflict("publication effect token is stale")
            connection.execute(
                """UPDATE publish_intents
                   SET state=?, error=?, response_json=COALESCE(?, response_json),
                       receipt_json=COALESCE(?, receipt_json), effect_token=NULL,
                       updated_at=?
                   WHERE id=?""",
                (
                    target,
                    error,
                    _json(dict(response)) if response is not None else None,
                    _json(receipt.to_dict()) if receipt is not None else None,
                    utc_now(),
                    intent_id,
                ),
            )
        return self.get_publish_intent(intent_id)
