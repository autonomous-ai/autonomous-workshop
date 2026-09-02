"""Durable host-private outbox for packet-bound Concept image roles."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Optional, Sequence

from workshop._validation import require_safe_evidence_path, require_sha256, utc_now
from workshop.errors import ContractError, StateConflict


STATES = frozenset(("planned", "sending", "succeeded", "rejected", "unknown"))


@dataclass(frozen=True)
class ConceptEffectRoleEvidence:
    role: str
    path: str
    intent_sha256: str
    image_sha256: str
    media_type: str

    def __post_init__(self) -> None:
        _text(self.role, "Concept effect role", 128)
        require_safe_evidence_path(self.path, "Concept effect image path")
        _text(self.media_type, "Concept effect media type", 64)
        if self.media_type not in ("image/png", "image/jpeg", "image/webp"):
            raise ContractError("Concept effect media type is invalid")
        for value, label in (
            (self.intent_sha256, "intent"), (self.image_sha256, "image")
        ):
            require_sha256(value, "Concept effect %s sha256" % label)

    def to_dict(self) -> dict[str, str]:
        return {
            "role": self.role, "path": self.path, "intent_sha256": self.intent_sha256,
            "image_sha256": self.image_sha256, "media_type": self.media_type,
        }


@dataclass(frozen=True)
class ConceptEffectEvidence:
    pre_render_concept_sha256: str
    sealed_concept_sha256: str
    profile_id: str
    profile_sha256: str
    roles: tuple[ConceptEffectRoleEvidence, ...]
    schema_version: int = 1
    kind: str = "autonomous-workshop.concept-image-effect"
    concept_effect_sha256: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "roles", tuple(self.roles))
        if self.schema_version != 1 or self.kind != "autonomous-workshop.concept-image-effect":
            raise ContractError("Concept effect evidence version or kind is invalid")
        for value, label in (
            (self.pre_render_concept_sha256, "pre-render Concept"),
            (self.sealed_concept_sha256, "sealed Concept"),
            (self.profile_sha256, "profile"),
        ):
            require_sha256(value, "Concept effect %s sha256" % label)
        _text(self.profile_id, "Concept effect profile id", 128)
        if not self.roles or len({item.role for item in self.roles}) != len(self.roles) or len({item.path for item in self.roles}) != len(self.roles):
            raise ContractError("Concept effect roles must be complete and unique")
        expected = hashlib.sha256(_canonical(self.identity())).hexdigest()
        if self.concept_effect_sha256 and self.concept_effect_sha256 != expected:
            raise ContractError("Concept effect evidence identity is invalid")
        object.__setattr__(self, "concept_effect_sha256", expected)

    def identity(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version, "kind": self.kind,
            "pre_render_concept_sha256": self.pre_render_concept_sha256,
            "sealed_concept_sha256": self.sealed_concept_sha256,
            "profile_id": self.profile_id, "profile_sha256": self.profile_sha256,
            "roles": [item.to_dict() for item in self.roles],
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.identity(), "concept_effect_sha256": self.concept_effect_sha256}

    @classmethod
    def from_mapping(cls, value: Any) -> "ConceptEffectEvidence":
        expected = {
            "schema_version", "kind", "pre_render_concept_sha256", "sealed_concept_sha256",
            "profile_id", "profile_sha256", "roles", "concept_effect_sha256",
        }
        if not isinstance(value, Mapping) or set(value) != expected or not isinstance(value["roles"], Sequence):
            raise ContractError("Concept effect evidence fields are invalid")
        roles = []
        for item in value["roles"]:
            if not isinstance(item, Mapping) or set(item) != {"role", "path", "intent_sha256", "image_sha256", "media_type"}:
                raise ContractError("Concept effect role evidence fields are invalid")
            roles.append(ConceptEffectRoleEvidence(**dict(item)))
        return cls(
            schema_version=value["schema_version"], kind=value["kind"],
            pre_render_concept_sha256=value["pre_render_concept_sha256"],
            sealed_concept_sha256=value["sealed_concept_sha256"],
            profile_id=value["profile_id"], profile_sha256=value["profile_sha256"],
            roles=tuple(roles), concept_effect_sha256=value["concept_effect_sha256"],
        )


def _canonical(value: Any) -> bytes:
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("Concept effect state must be finite JSON") from exc


def _text(value: Any, label: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or len(value) > maximum or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ContractError("%s must be bounded control-free text" % label)
    return value


@dataclass(frozen=True)
class ConceptRoleIntent:
    intent_id: str
    aggregate_id: str
    product_id: str
    checkpoint_sha256: str
    subject_sha256: str
    pre_render_sha256: str
    source_manifest_sha256: str
    role: str
    output_path: str
    instruction_sha256: str
    request_context_sha256: Optional[str]
    references: tuple[Mapping[str, str], ...]
    profile_id: str
    profile_sha256: str
    model: str
    request_schema_version: str
    state: str
    response: Optional[Mapping[str, Any]]
    error_code: Optional[str]
    effect_token: Optional[str]
    created_at: str
    updated_at: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "references", tuple(dict(item) for item in self.references))
        for value, label in (
            (self.product_id, "Concept product id"), (self.role, "Concept role"),
            (self.profile_id, "Concept profile id"),
            (self.model, "Concept model"), (self.request_schema_version, "Concept request schema"),
        ):
            _text(value, label)
        require_safe_evidence_path(self.output_path, "Concept output path")
        for value, label in (
            (self.intent_id, "intent"), (self.aggregate_id, "aggregate"),
            (self.checkpoint_sha256, "checkpoint"), (self.subject_sha256, "subject"),
            (self.pre_render_sha256, "pre-render Concept"),
            (self.source_manifest_sha256, "source manifest"),
            (self.instruction_sha256, "instruction"), (self.profile_sha256, "profile"),
        ):
            require_sha256(value, "Concept effect %s sha256" % label)
        if self.request_context_sha256 is not None:
            require_sha256(
                self.request_context_sha256,
                "Concept effect request context sha256",
            )
        if self.state not in STATES:
            raise StateConflict("Concept effect state is invalid")
        for reference in self.references:
            if set(reference) != {"role", "sha256"}:
                raise StateConflict("Concept effect reference fields are invalid")
            _text(reference["role"], "Concept reference role")
            require_sha256(reference["sha256"], "Concept reference sha256")

    @property
    def evidence_intent_sha256(self) -> str:
        """Return the stable, sanitized request identity exposed to the run.

        The private ledger intent additionally binds the location-bound
        checkpoint and aggregate.  Those host identities remain private so two
        byte-identical product runs produce the same sanitized evidence.
        """

        identity = {
            "product_id": self.product_id,
            "subject_sha256": self.subject_sha256,
            "pre_render_sha256": self.pre_render_sha256,
            "source_manifest_sha256": self.source_manifest_sha256,
            "role": self.role,
            "output_path": self.output_path,
            "instruction_sha256": self.instruction_sha256,
            "references": [dict(item) for item in self.references],
            "profile_id": self.profile_id,
            "profile_sha256": self.profile_sha256,
            "model": self.model,
            "request_schema_version": self.request_schema_version,
        }
        if self.request_context_sha256 is not None:
            identity["request_context_sha256"] = self.request_context_sha256
        return hashlib.sha256(_canonical(identity)).hexdigest()


class ConceptEffectLedger:
    """One SQLite aggregate and immutable operation history per Concept attempt."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        if self.path.is_symlink():
            raise ContractError("Concept effect ledger must not be a symlink")
        self.path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        self._initialize()
        self._secure()

    def _secure(self) -> None:
        for candidate in (self.path, Path(str(self.path) + "-journal")):
            try:
                os.chmod(candidate, 0o600)
            except FileNotFoundError:
                pass

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(str(self.path), timeout=30, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA journal_mode=DELETE")
        try:
            yield connection
        finally:
            connection.close()
            self._secure()

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
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS concept_effect_meta(schema_version INTEGER NOT NULL);
                INSERT INTO concept_effect_meta(schema_version)
                    SELECT 1 WHERE NOT EXISTS(SELECT 1 FROM concept_effect_meta);
                CREATE TABLE IF NOT EXISTS concept_aggregates(
                    aggregate_id TEXT PRIMARY KEY, product_id TEXT NOT NULL,
                    checkpoint_sha256 TEXT NOT NULL, subject_sha256 TEXT NOT NULL,
                    pre_render_sha256 TEXT NOT NULL, source_manifest_sha256 TEXT NOT NULL,
                    required_roles_json TEXT NOT NULL, state TEXT NOT NULL,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS concept_operations(
                    intent_id TEXT PRIMARY KEY, aggregate_id TEXT NOT NULL,
                    identity_json TEXT NOT NULL, state TEXT NOT NULL,
                    response_json TEXT, error_code TEXT, effect_token TEXT,
                    created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    FOREIGN KEY(aggregate_id) REFERENCES concept_aggregates(aggregate_id)
                );
                CREATE INDEX IF NOT EXISTS concept_operation_aggregate
                    ON concept_operations(aggregate_id, created_at);
                CREATE TABLE IF NOT EXISTS concept_operation_events(
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    intent_id TEXT NOT NULL, state TEXT NOT NULL,
                    response_json TEXT, error_code TEXT, created_at TEXT NOT NULL,
                    FOREIGN KEY(intent_id) REFERENCES concept_operations(intent_id)
                );
                """
            )
            row = connection.execute("SELECT schema_version FROM concept_effect_meta").fetchone()
            if row is None or row[0] != 1:
                raise ContractError("Concept effect ledger schema is unsupported")

    @staticmethod
    def aggregate_id(*, product_id: str, checkpoint_sha256: str, subject_sha256: str, pre_render_sha256: str, source_manifest_sha256: str) -> str:
        identity = {
            "product_id": product_id, "checkpoint_sha256": checkpoint_sha256,
            "subject_sha256": subject_sha256, "pre_render_sha256": pre_render_sha256,
            "source_manifest_sha256": source_manifest_sha256,
        }
        return hashlib.sha256(_canonical(identity)).hexdigest()

    def prepare_aggregate(self, *, product_id: str, checkpoint_sha256: str, subject_sha256: str, pre_render_sha256: str, source_manifest_sha256: str, required_roles: Sequence[str]) -> str:
        roles = tuple(required_roles)
        if not roles or len(set(roles)) != len(roles):
            raise ContractError("Concept aggregate roles must be complete and unique")
        for value in (checkpoint_sha256, subject_sha256, pre_render_sha256, source_manifest_sha256):
            require_sha256(value, "Concept aggregate binding")
        aggregate_id = self.aggregate_id(
            product_id=product_id, checkpoint_sha256=checkpoint_sha256,
            subject_sha256=subject_sha256, pre_render_sha256=pre_render_sha256,
            source_manifest_sha256=source_manifest_sha256,
        )
        now = utc_now()
        with self._transaction() as connection:
            row = connection.execute("SELECT * FROM concept_aggregates WHERE aggregate_id=?", (aggregate_id,)).fetchone()
            expected_roles = _canonical(list(roles)).decode("utf-8")
            if row is None:
                connection.execute(
                    "INSERT INTO concept_aggregates VALUES(?,?,?,?,?,?,?,?,?,?)",
                    (aggregate_id, product_id, checkpoint_sha256, subject_sha256, pre_render_sha256, source_manifest_sha256, expected_roles, "planned", now, now),
                )
            elif row["required_roles_json"] != expected_roles:
                raise StateConflict("Concept aggregate identity cannot be reused with changed roles")
        return aggregate_id

    def prepare_role(self, *, aggregate_id: str, identity: Mapping[str, Any]) -> ConceptRoleIntent:
        required = {
            "product_id", "checkpoint_sha256", "subject_sha256", "pre_render_sha256",
            "source_manifest_sha256", "role", "output_path", "instruction_sha256",
            "references", "profile_id", "profile_sha256", "model", "request_schema_version",
        }
        if set(identity) not in (required, required | {"request_context_sha256"}):
            raise ContractError("Concept role intent fields are invalid")
        if identity.get("request_context_sha256") is not None:
            require_sha256(
                identity["request_context_sha256"],
                "Concept role request context sha256",
            )
        identity_value = {"aggregate_id": aggregate_id, **dict(identity)}
        intent_id = hashlib.sha256(_canonical(identity_value)).hexdigest()
        now = utc_now()
        encoded = _canonical(identity_value).decode("utf-8")
        with self._transaction() as connection:
            aggregate = connection.execute("SELECT aggregate_id FROM concept_aggregates WHERE aggregate_id=?", (aggregate_id,)).fetchone()
            if aggregate is None:
                raise StateConflict("Concept aggregate is absent")
            row = connection.execute("SELECT identity_json FROM concept_operations WHERE intent_id=?", (intent_id,)).fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO concept_operations VALUES(?,?,?,?,?,?,?,?,?)",
                    (intent_id, aggregate_id, encoded, "planned", None, None, None, now, now),
                )
                connection.execute(
                    "INSERT INTO concept_operation_events(intent_id,state,created_at) VALUES(?,?,?)",
                    (intent_id, "planned", now),
                )
            elif row["identity_json"] != encoded:
                raise StateConflict("Concept intent identity was reused with changed inputs")
        return self.get(intent_id)

    def _from_row(self, row: sqlite3.Row) -> ConceptRoleIntent:
        identity = json.loads(row["identity_json"])
        return ConceptRoleIntent(
            intent_id=row["intent_id"], aggregate_id=row["aggregate_id"],
            state=row["state"], response=(json.loads(row["response_json"]) if row["response_json"] else None),
            error_code=row["error_code"], effect_token=row["effect_token"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            request_context_sha256=identity.get("request_context_sha256"),
            **{
                key: identity[key]
                for key in identity
                if key not in {"aggregate_id", "request_context_sha256"}
            },
        )

    def get(self, intent_id: str) -> ConceptRoleIntent:
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM concept_operations WHERE intent_id=?", (intent_id,)).fetchone()
        if row is None:
            raise KeyError(intent_id)
        return self._from_row(row)

    def roles(self, aggregate_id: str) -> tuple[ConceptRoleIntent, ...]:
        with self._connection() as connection:
            rows = connection.execute("SELECT * FROM concept_operations WHERE aggregate_id=? ORDER BY created_at, intent_id", (aggregate_id,)).fetchall()
        return tuple(self._from_row(row) for row in rows)

    def begin(self, intent_id: str) -> ConceptRoleIntent:
        token = secrets.token_hex(32)
        now = utc_now()
        with self._transaction() as connection:
            row = connection.execute("SELECT state FROM concept_operations WHERE intent_id=?", (intent_id,)).fetchone()
            if row is None or row["state"] != "planned":
                raise StateConflict("only a planned Concept effect may begin")
            connection.execute("UPDATE concept_operations SET state='sending', effect_token=?, updated_at=? WHERE intent_id=?", (token, now, intent_id))
            connection.execute(
                "INSERT INTO concept_operation_events(intent_id,state,created_at) VALUES(?,?,?)",
                (intent_id, "sending", now),
            )
        return self.get(intent_id)

    def finish(self, intent_id: str, token: str, *, state: str, response: Optional[Mapping[str, Any]] = None, error_code: Optional[str] = None) -> ConceptRoleIntent:
        if state not in ("succeeded", "rejected", "unknown"):
            raise ContractError("Concept effect terminal state is invalid")
        encoded = None if response is None else _canonical(dict(response)).decode("utf-8")
        now = utc_now()
        with self._transaction() as connection:
            row = connection.execute("SELECT state,effect_token FROM concept_operations WHERE intent_id=?", (intent_id,)).fetchone()
            if row is None or row["state"] != "sending" or row["effect_token"] != token:
                raise StateConflict("Concept effect completion token is stale")
            connection.execute("UPDATE concept_operations SET state=?, response_json=?, error_code=?, effect_token=NULL, updated_at=? WHERE intent_id=?", (state, encoded, error_code, now, intent_id))
            connection.execute(
                "INSERT INTO concept_operation_events(intent_id,state,response_json,error_code,created_at) VALUES(?,?,?,?,?)",
                (intent_id, state, encoded, error_code, now),
            )
        return self.get(intent_id)

    def retry_rejected(self, intent_id: str) -> ConceptRoleIntent:
        """Reopen only a definitive failure under the same immutable intent.

        Both pre-transmission failures and explicit provider rejections prove
        that no image effect was created. Unknown outcomes remain sealed until
        authenticated reconciliation proves success or absence.
        """

        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state,error_code FROM concept_operations WHERE intent_id=?",
                (intent_id,),
            ).fetchone()
            if (
                row is None
                or row["state"] != "rejected"
                or row["error_code"]
                not in ("pre-transmission", "provider-rejected")
            ):
                raise StateConflict("Concept effect is not safely retryable")
            connection.execute(
                "UPDATE concept_operations SET state='planned', response_json=NULL, "
                "error_code=NULL, effect_token=NULL, updated_at=? WHERE intent_id=?",
                (utc_now(), intent_id),
            )
            connection.execute(
                "INSERT INTO concept_operation_events(intent_id,state,created_at) VALUES(?,?,?)",
                (intent_id, "planned", utc_now()),
            )
        return self.get(intent_id)

    def reconcile_unknown(
        self,
        intent_id: str,
        provider_operation_id: str,
        *,
        state: str,
        response: Optional[Mapping[str, Any]] = None,
        error_code: Optional[str] = None,
    ) -> ConceptRoleIntent:
        """Resolve one unknown operation only through its bound provider id."""

        if state not in ("planned", "succeeded"):
            raise ContractError("Concept reconciliation state is invalid")
        encoded = None if response is None else _canonical(dict(response)).decode("utf-8")
        now = utc_now()
        with self._transaction() as connection:
            row = connection.execute(
                "SELECT state,response_json FROM concept_operations WHERE intent_id=?",
                (intent_id,),
            ).fetchone()
            if row is None or row["state"] != "unknown" or not row["response_json"]:
                raise StateConflict("Concept effect is not an unknown operation")
            previous = json.loads(row["response_json"])
            if previous.get("provider_operation_id") != provider_operation_id:
                raise StateConflict("Concept provider operation identity changed")
            connection.execute(
                "UPDATE concept_operations SET state=?, response_json=?, error_code=?, "
                "effect_token=NULL, updated_at=? WHERE intent_id=?",
                (state, encoded, error_code, now, intent_id),
            )
            connection.execute(
                "INSERT INTO concept_operation_events(intent_id,state,response_json,error_code,created_at) VALUES(?,?,?,?,?)",
                (intent_id, state, encoded, error_code, now),
            )
        return self.get(intent_id)

    def audit(self, intent_id: str) -> tuple[Mapping[str, Any], ...]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT state,response_json,error_code,created_at FROM concept_operation_events "
                "WHERE intent_id=? ORDER BY event_id",
                (intent_id,),
            ).fetchall()
        return tuple(
            {
                "state": row["state"],
                "response": (
                    json.loads(row["response_json"])
                    if row["response_json"]
                    else None
                ),
                "error_code": row["error_code"],
                "created_at": row["created_at"],
            }
            for row in rows
        )

    def mark_aggregate_succeeded(self, aggregate_id: str, *, observed: Mapping[str, str]) -> None:
        with self._transaction() as connection:
            aggregate = connection.execute("SELECT required_roles_json FROM concept_aggregates WHERE aggregate_id=?", (aggregate_id,)).fetchone()
            rows = connection.execute("SELECT identity_json,state,response_json FROM concept_operations WHERE aggregate_id=?", (aggregate_id,)).fetchall()
            if aggregate is None:
                raise StateConflict("Concept aggregate is absent")
            required = tuple(json.loads(aggregate["required_roles_json"]))
            if set(observed) != set(required) or len(rows) != len(required):
                raise StateConflict("Concept aggregate role completion is incomplete or extra")
            for row in rows:
                identity = json.loads(row["identity_json"])
                response = json.loads(row["response_json"]) if row["response_json"] else {}
                role = identity["role"]
                if row["state"] != "succeeded" or response.get("image_sha256") != observed[role]:
                    raise StateConflict("Concept aggregate role bytes are incomplete or changed")
            connection.execute("UPDATE concept_aggregates SET state='succeeded', updated_at=? WHERE aggregate_id=?", (utc_now(), aggregate_id))


__all__ = [
    "ConceptEffectEvidence", "ConceptEffectLedger", "ConceptEffectRoleEvidence",
    "ConceptRoleIntent", "STATES",
]
