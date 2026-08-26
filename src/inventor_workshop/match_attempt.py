"""Append-only Manager truth for semantic Match attempts.

``PendingWish`` remains the immutable pre-Match identity.  This module records
what happened when the Manager tried to match that identity without rewriting
it: a content-addressed ``working`` event followed by either ``waiting`` with
typed Needs or ``assigned`` with the exact sealed handoff digest.

Only a small per-Wish head pointer is replaced.  Every event is immutable,
links to its predecessor, and is validated against the referenced PendingWish
object before status or resume may trust it.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple

from .errors import ContractError, WorkshopError
from .jobs import Need
from .models import require_sha256, require_utc_timestamp
from .pending_wish import (
    PendingWish,
    PendingWishStore,
    _DIRECTORY_FLAGS,
    _MissingStore,
    _canonical_json,
    _copy_mapping,
    _product_key,
    _read_exact_file,
    _write_atomic_exclusive,
    _write_private_exclusive,
)


MATCH_ATTEMPT_EVENT_KIND = "autonomous-workshop-manager-match-attempt-event"
MATCH_ATTEMPT_INDEX_KIND = "autonomous-workshop-manager-match-attempt-index"
MATCH_ATTEMPT_STATES = ("working", "waiting", "assigned")
MAX_MATCH_ATTEMPT_BYTES = 1024 * 1024
MAX_MATCH_ATTEMPT_EVENTS_PER_WISH = 1000
MAX_MATCH_ATTEMPT_NEEDS = 64
_RUNTIME_DIRECTORY = ".workshop"
_STORE_DIRECTORY = "manager-match-attempts"
_OBJECT_DIRECTORY = "objects"
_INDEX_DIRECTORY = "by-wish"
_MATCH_ATTEMPT_ID = re.compile(r"^match-[0-9a-f]{64}$")


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _attempt_id(pending_wish_sha256: str) -> str:
    require_sha256(pending_wish_sha256, "Match pending Wish sha256")
    return "match-" + hashlib.sha256(
        b"autonomous-workshop-manager-match-attempt-v1\0"
        + pending_wish_sha256.encode("ascii")
        + secrets.token_bytes(32)
    ).hexdigest()


@dataclass(frozen=True)
class MatchAttemptEvent:
    """One immutable event in a per-Wish Match-attempt chain."""

    product_id: str
    pending_wish_sha256: str
    attempt_id: str
    attempt_number: int
    event_sequence: int
    previous_event_sha256: Optional[str]
    status: str
    recorded_at: str
    needs: Sequence[Need] = ()
    manager_handoff_sha256: Optional[str] = None
    schema_version: int = 1
    kind: str = MATCH_ATTEMPT_EVENT_KIND
    event_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("Match attempt schema_version must be 1")
        if self.kind != MATCH_ATTEMPT_EVENT_KIND:
            raise ContractError("Match attempt kind is invalid")
        # Reuse the exact PendingWish path-safe identifier grammar.
        _product_key(self.product_id)
        require_sha256(
            self.pending_wish_sha256, "Match attempt pending Wish sha256"
        )
        if (
            not isinstance(self.attempt_id, str)
            or _MATCH_ATTEMPT_ID.fullmatch(self.attempt_id) is None
        ):
            raise ContractError("Match attempt id is invalid")
        if type(self.attempt_number) is not int or not (
            1 <= self.attempt_number <= MAX_MATCH_ATTEMPT_EVENTS_PER_WISH
        ):
            raise ContractError("Match attempt number is invalid")
        if type(self.event_sequence) is not int or not (
            1 <= self.event_sequence <= MAX_MATCH_ATTEMPT_EVENTS_PER_WISH
        ):
            raise ContractError("Match attempt event sequence is invalid")
        if self.previous_event_sha256 is not None:
            require_sha256(
                self.previous_event_sha256,
                "Match attempt previous event sha256",
            )
        if self.status not in MATCH_ATTEMPT_STATES:
            raise ContractError("Match attempt status is invalid")
        require_utc_timestamp(self.recorded_at, "Match attempt recorded_at")
        needs = tuple(self.needs)
        if (
            len(needs) > MAX_MATCH_ATTEMPT_NEEDS
            or not all(isinstance(item, Need) for item in needs)
        ):
            raise ContractError("Match attempt Needs are invalid")
        if self.status == "waiting":
            if not needs or self.manager_handoff_sha256 is not None:
                raise ContractError(
                    "waiting Match attempt requires Needs and no handoff"
                )
        elif self.status == "assigned":
            if needs or self.manager_handoff_sha256 is None:
                raise ContractError(
                    "assigned Match attempt requires one handoff and no Needs"
                )
            require_sha256(
                self.manager_handoff_sha256,
                "Match attempt Manager handoff sha256",
            )
        elif needs or self.manager_handoff_sha256 is not None:
            raise ContractError(
                "working Match attempt cannot claim Needs or a handoff"
            )
        object.__setattr__(self, "needs", needs)
        object.__setattr__(
            self,
            "event_sha256",
            hashlib.sha256(self.object_bytes()).hexdigest(),
        )

    @classmethod
    def start(
        cls,
        pending: PendingWish,
        previous: Optional["MatchAttemptEvent"] = None,
        *,
        attempt_id: Optional[str] = None,
        recorded_at: Optional[str] = None,
    ) -> "MatchAttemptEvent":
        if not isinstance(pending, PendingWish):
            raise ContractError("Match attempt requires one PendingWish")
        if previous is not None and not isinstance(previous, MatchAttemptEvent):
            raise ContractError("Match attempt predecessor is not typed")
        if previous is not None:
            if previous.product_id != pending.wish.product_id:
                raise ContractError("Match attempt predecessor belongs to another Wish")
            if previous.status == "assigned":
                raise ContractError("an assigned Match cannot start another attempt")
        number = 1 if previous is None else previous.attempt_number + 1
        sequence = 1 if previous is None else previous.event_sequence + 1
        return cls(
            product_id=pending.wish.product_id,
            pending_wish_sha256=pending.record_sha256,
            attempt_id=(
                _attempt_id(pending.record_sha256)
                if attempt_id is None
                else attempt_id
            ),
            attempt_number=number,
            event_sequence=sequence,
            previous_event_sha256=(
                None if previous is None else previous.event_sha256
            ),
            status="working",
            recorded_at=_utc_now() if recorded_at is None else recorded_at,
        )

    def waiting(
        self,
        needs: Sequence[Need],
        *,
        recorded_at: Optional[str] = None,
    ) -> "MatchAttemptEvent":
        if self.status != "working":
            raise ContractError("only a working Match attempt can wait")
        return MatchAttemptEvent(
            product_id=self.product_id,
            pending_wish_sha256=self.pending_wish_sha256,
            attempt_id=self.attempt_id,
            attempt_number=self.attempt_number,
            event_sequence=self.event_sequence + 1,
            previous_event_sha256=self.event_sha256,
            status="waiting",
            recorded_at=_utc_now() if recorded_at is None else recorded_at,
            needs=tuple(needs),
        )

    def assigned(
        self,
        manager_handoff_sha256: str,
        *,
        recorded_at: Optional[str] = None,
    ) -> "MatchAttemptEvent":
        if self.status != "working":
            raise ContractError("only a working Match attempt can be assigned")
        return MatchAttemptEvent(
            product_id=self.product_id,
            pending_wish_sha256=self.pending_wish_sha256,
            attempt_id=self.attempt_id,
            attempt_number=self.attempt_number,
            event_sequence=self.event_sequence + 1,
            previous_event_sha256=self.event_sha256,
            status="assigned",
            recorded_at=_utc_now() if recorded_at is None else recorded_at,
            manager_handoff_sha256=manager_handoff_sha256,
        )

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "product_id": self.product_id,
            "pending_wish_sha256": self.pending_wish_sha256,
            "attempt_id": self.attempt_id,
            "attempt_number": self.attempt_number,
            "event_sequence": self.event_sequence,
            "previous_event_sha256": self.previous_event_sha256,
            "status": self.status,
            "recorded_at": self.recorded_at,
            "needs": [item.to_dict() for item in self.needs],
            "manager_handoff_sha256": self.manager_handoff_sha256,
        }

    def object_bytes(self) -> bytes:
        return _canonical_json(self._identity_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {**self._identity_dict(), "event_sha256": self.event_sha256}

    def public_status(self) -> Dict[str, Any]:
        """Return the complete secret-free latest attempt projection."""

        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "attempt_id": self.attempt_id,
            "attempt_number": self.attempt_number,
            "event_sequence": self.event_sequence,
            "event_sha256": self.event_sha256,
            "pending_wish_sha256": self.pending_wish_sha256,
            "recorded_at": self.recorded_at,
            "needs": [item.to_dict() for item in self.needs],
            **(
                {}
                if self.manager_handoff_sha256 is None
                else {
                    "manager_handoff_sha256": self.manager_handoff_sha256,
                }
            ),
        }

    @classmethod
    def from_object_bytes(
        cls, source: bytes, *, expected_sha256: str
    ) -> "MatchAttemptEvent":
        require_sha256(expected_sha256, "Match attempt object address")
        if not isinstance(source, bytes) or not (
            1 <= len(source) <= MAX_MATCH_ATTEMPT_BYTES
        ):
            raise ContractError("Match attempt object is empty or too large")
        if hashlib.sha256(source).hexdigest() != expected_sha256:
            raise ContractError("Match attempt object address differs from its bytes")
        try:
            value = json.loads(source.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError(
                "Match attempt object is not valid UTF-8 JSON"
            ) from exc
        payload = _copy_mapping(value, "Match attempt object")
        if set(payload) != {
            "schema_version",
            "kind",
            "product_id",
            "pending_wish_sha256",
            "attempt_id",
            "attempt_number",
            "event_sequence",
            "previous_event_sha256",
            "status",
            "recorded_at",
            "needs",
            "manager_handoff_sha256",
        }:
            raise ContractError("Match attempt object fields are invalid")
        raw_needs = payload["needs"]
        if not isinstance(raw_needs, list):
            raise ContractError("Match attempt Needs are malformed")
        needs = []
        for item in raw_needs:
            if not isinstance(item, Mapping) or set(item) != {
                "job",
                "capability",
                "reason",
                "instructions",
            }:
                raise ContractError("Match attempt Need is malformed")
            try:
                need = Need(**dict(item))
            except TypeError as exc:
                raise ContractError("Match attempt Need is malformed") from exc
            if need.to_dict() != dict(item):
                raise ContractError("Match attempt Need is not exact")
            needs.append(need)
        event = cls(
            product_id=payload["product_id"],
            pending_wish_sha256=payload["pending_wish_sha256"],
            attempt_id=payload["attempt_id"],
            attempt_number=payload["attempt_number"],
            event_sequence=payload["event_sequence"],
            previous_event_sha256=payload["previous_event_sha256"],
            status=payload["status"],
            recorded_at=payload["recorded_at"],
            needs=tuple(needs),
            manager_handoff_sha256=payload["manager_handoff_sha256"],
            schema_version=payload["schema_version"],
            kind=payload["kind"],
        )
        if event.event_sha256 != expected_sha256 or event.object_bytes() != source:
            raise ContractError("Match attempt object is not exact canonical bytes")
        return event


@dataclass(frozen=True)
class _MatchLayout:
    collection: int
    runtime: int
    store: int
    objects: int
    indexes: int


class MatchAttemptStore:
    """Secure append-only event store rooted in one inventor collection."""

    def __init__(self, catalog_collection: Path) -> None:
        # Delegate the exact collection/symlink validation to PendingWishStore.
        self._pending_store = PendingWishStore(catalog_collection)
        self.collection = self._pending_store.collection

    @property
    def path(self) -> Path:
        return self.collection / _RUNTIME_DIRECTORY / _STORE_DIRECTORY

    @contextmanager
    def _layout(self, *, create: bool) -> Iterator[_MatchLayout]:
        try:
            expected = self.collection.lstat()
        except OSError as exc:
            raise WorkshopError("cannot inspect Manager Match catalog") from exc
        if not stat.S_ISDIR(expected.st_mode) or stat.S_ISLNK(expected.st_mode):
            raise WorkshopError("Manager Match catalog must be a regular directory")
        try:
            collection = os.open(str(self.collection), _DIRECTORY_FLAGS)
        except OSError as exc:
            raise WorkshopError("cannot safely open Manager Match catalog") from exc
        descriptors = [collection]
        try:
            opened = os.fstat(collection)
            if (opened.st_dev, opened.st_ino) != (
                expected.st_dev,
                expected.st_ino,
            ):
                raise WorkshopError("Manager Match catalog changed while opening")
            runtime = PendingWishStore._open_child(
                collection,
                _RUNTIME_DIRECTORY,
                label="Manager runtime",
                create=create,
            )
            descriptors.append(runtime)
            store = PendingWishStore._open_child(
                runtime,
                _STORE_DIRECTORY,
                label="Manager Match attempt storage",
                create=create,
            )
            descriptors.append(store)
            objects = PendingWishStore._open_child(
                store,
                _OBJECT_DIRECTORY,
                label="Manager Match attempt object storage",
                create=create,
            )
            descriptors.append(objects)
            indexes = PendingWishStore._open_child(
                store,
                _INDEX_DIRECTORY,
                label="Manager Match attempt index storage",
                create=create,
            )
            descriptors.append(indexes)
            yield _MatchLayout(collection, runtime, store, objects, indexes)
            current = self.collection.lstat()
            if (
                not stat.S_ISDIR(current.st_mode)
                or (current.st_dev, current.st_ino)
                != (opened.st_dev, opened.st_ino)
            ):
                raise WorkshopError("Manager Match catalog changed during access")
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    @staticmethod
    def _index_bytes(product_id: str, event_sha256: str) -> bytes:
        require_sha256(event_sha256, "Match attempt event sha256")
        return _canonical_json(
            {
                "schema_version": 1,
                "kind": MATCH_ATTEMPT_INDEX_KIND,
                "product_id": product_id,
                "event_sha256": event_sha256,
            }
        )

    @classmethod
    def _read_index(
        cls, indexes: int, product_id: str, *, allow_missing: bool
    ) -> Optional[str]:
        name = _product_key(product_id) + ".json"
        try:
            os.stat(name, dir_fd=indexes, follow_symlinks=False)
        except FileNotFoundError:
            if allow_missing:
                return None
            raise WorkshopError("Manager Match attempt index is missing")
        source = _read_exact_file(
            indexes,
            name,
            label="Manager Match attempt index",
            maximum=MAX_MATCH_ATTEMPT_BYTES,
        )
        try:
            value = json.loads(source.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise WorkshopError(
                "Manager Match attempt index is not valid UTF-8 JSON"
            ) from exc
        payload = _copy_mapping(value, "Manager Match attempt index")
        if set(payload) != {
            "schema_version",
            "kind",
            "product_id",
            "event_sha256",
        }:
            raise WorkshopError("Manager Match attempt index fields are invalid")
        if (
            payload["schema_version"] != 1
            or payload["kind"] != MATCH_ATTEMPT_INDEX_KIND
            or payload["product_id"] != product_id
        ):
            raise WorkshopError("Manager Match attempt index identity is invalid")
        try:
            require_sha256(payload["event_sha256"], "Match attempt event sha256")
        except ContractError as exc:
            raise WorkshopError(str(exc)) from exc
        if source != cls._index_bytes(product_id, payload["event_sha256"]):
            raise WorkshopError(
                "Manager Match attempt index is not exact canonical bytes"
            )
        return payload["event_sha256"]

    @staticmethod
    def _read_object(objects: int, event_sha256: str) -> MatchAttemptEvent:
        source = _read_exact_file(
            objects,
            event_sha256 + ".json",
            label="Manager Match attempt object",
            maximum=MAX_MATCH_ATTEMPT_BYTES,
        )
        try:
            return MatchAttemptEvent.from_object_bytes(
                source, expected_sha256=event_sha256
            )
        except ContractError as exc:
            raise WorkshopError(str(exc)) from exc

    @staticmethod
    def _validate_transition(
        previous: Optional[MatchAttemptEvent], current: MatchAttemptEvent
    ) -> None:
        if previous is None:
            if (
                current.event_sequence != 1
                or current.attempt_number != 1
                or current.previous_event_sha256 is not None
                or current.status != "working"
            ):
                raise WorkshopError("first Match attempt event is invalid")
            return
        if (
            current.product_id != previous.product_id
            or current.previous_event_sha256 != previous.event_sha256
            or current.event_sequence != previous.event_sequence + 1
        ):
            raise WorkshopError("Match attempt event chain is inconsistent")
        if current.status == "working":
            if (
                previous.status == "assigned"
                or current.attempt_number != previous.attempt_number + 1
                or current.attempt_id == previous.attempt_id
            ):
                raise WorkshopError("new Match attempt transition is invalid")
            return
        if (
            previous.status != "working"
            or current.attempt_number != previous.attempt_number
            or current.attempt_id != previous.attempt_id
            or current.pending_wish_sha256 != previous.pending_wish_sha256
        ):
            raise WorkshopError("terminal Match attempt transition is invalid")

    def _read_chain(
        self, layout: _MatchLayout, product_id: str, head_sha256: str
    ) -> Tuple[MatchAttemptEvent, ...]:
        newest_to_oldest = []
        seen = set()
        selected = head_sha256
        while selected is not None:
            if (
                selected in seen
                or len(newest_to_oldest) >= MAX_MATCH_ATTEMPT_EVENTS_PER_WISH
            ):
                raise WorkshopError("Manager Match attempt chain is cyclic or too long")
            seen.add(selected)
            event = self._read_object(layout.objects, selected)
            if event.product_id != product_id:
                raise WorkshopError("Manager Match attempt belongs to another Wish")
            newest_to_oldest.append(event)
            selected = event.previous_event_sha256
        chain = tuple(reversed(newest_to_oldest))
        previous = None
        for event in chain:
            self._validate_transition(previous, event)
            previous = event
        return chain

    def _validate_pending_bindings(
        self, product_id: str, chain: Sequence[MatchAttemptEvent]
    ) -> None:
        try:
            with self._pending_store._layout(create=False) as pending_layout:
                records = {}
                for digest in dict.fromkeys(
                    event.pending_wish_sha256 for event in chain
                ):
                    record = self._pending_store._read_object(
                        pending_layout.objects, digest
                    )
                    if record.wish.product_id != product_id:
                        raise WorkshopError(
                            "Match attempt references another PendingWish"
                        )
                    records[digest] = record
        except _MissingStore as exc:  # pragma: no cover - event cannot predate its Wish
            raise WorkshopError("Match attempt has no PendingWish storage") from exc
        if len(records) > MAX_MATCH_ATTEMPT_EVENTS_PER_WISH:  # defensive bound
            raise WorkshopError("Match attempt references too many PendingWishes")

    def load_chain(
        self, product_id: str, *, allow_missing: bool = False
    ) -> Tuple[MatchAttemptEvent, ...]:
        _product_key(product_id)
        try:
            with self._layout(create=False) as layout:
                head = self._read_index(
                    layout.indexes, product_id, allow_missing=True
                )
                if head is None:
                    if allow_missing:
                        return ()
                    raise WorkshopError("this Wish has no saved Match attempt")
                chain = self._read_chain(layout, product_id, head)
                if self._read_index(
                    layout.indexes, product_id, allow_missing=False
                ) != head:
                    raise WorkshopError("Manager Match attempt changed during load")
        except _MissingStore:
            if allow_missing:
                return ()
            raise WorkshopError("this Wish has no saved Match attempt")
        self._validate_pending_bindings(product_id, chain)
        return chain

    def load(
        self, product_id: str, *, allow_missing: bool = False
    ) -> Optional[MatchAttemptEvent]:
        chain = self.load_chain(product_id, allow_missing=allow_missing)
        return chain[-1] if chain else None

    @staticmethod
    def _save_object(objects: int, event: MatchAttemptEvent) -> None:
        name = event.event_sha256 + ".json"
        if _write_atomic_exclusive(
            objects,
            objects,
            name,
            event.object_bytes(),
            label="Manager Match attempt object",
        ):
            return
        existing = _read_exact_file(
            objects,
            name,
            label="Manager Match attempt object",
            maximum=MAX_MATCH_ATTEMPT_BYTES,
        )
        if existing != event.object_bytes():
            raise WorkshopError("Manager Match attempt content-address collision")

    def append(
        self,
        event: MatchAttemptEvent,
        *,
        expected_previous_sha256: Optional[str],
    ) -> Path:
        if not isinstance(event, MatchAttemptEvent):
            raise ContractError("Match attempt store requires a typed event")
        if event.previous_event_sha256 != expected_previous_sha256:
            raise ContractError("Match attempt expected predecessor is inconsistent")
        if expected_previous_sha256 is not None:
            require_sha256(
                expected_previous_sha256, "expected Match predecessor sha256"
            )
        # PendingWishStore.lock(product_id) is the cooperating-writer authority.
        # The head comparison detects stale callers and accidental lock bypass;
        # it is not presented as an OS-level compare-and-swap primitive.
        with self._layout(create=True) as layout:
            current = self._read_index(
                layout.indexes, event.product_id, allow_missing=True
            )
            if current != expected_previous_sha256:
                raise WorkshopError("Manager Match attempt changed before append")
            previous = (
                None
                if current is None
                else self._read_object(layout.objects, current)
            )
            self._validate_transition(previous, event)
            self._validate_pending_bindings(event.product_id, (event,))
            self._save_object(layout.objects, event)
            name = _product_key(event.product_id) + ".json"
            source = self._index_bytes(event.product_id, event.event_sha256)
            if current is None:
                if not _write_atomic_exclusive(
                    layout.objects,
                    layout.indexes,
                    name,
                    source,
                    label="Manager Match attempt index",
                ):
                    raise WorkshopError("Manager Match attempt raced during append")
            else:
                temporary_name = ".%s-%s.tmp" % (name, secrets.token_hex(8))
                if not _write_private_exclusive(
                    layout.objects,
                    temporary_name,
                    source,
                    label="Manager Match attempt replacement index",
                ):  # pragma: no cover - random name collision
                    raise WorkshopError(
                        "cannot reserve Manager Match attempt replacement"
                    )
                try:
                    if self._read_index(
                        layout.indexes,
                        event.product_id,
                        allow_missing=False,
                    ) != current:
                        raise WorkshopError(
                            "Manager Match attempt changed before append"
                        )
                    os.replace(
                        temporary_name,
                        name,
                        src_dir_fd=layout.objects,
                        dst_dir_fd=layout.indexes,
                    )
                    os.fsync(layout.indexes)
                except OSError as exc:
                    raise WorkshopError(
                        "cannot atomically append Manager Match attempt"
                    ) from exc
                finally:
                    try:
                        os.unlink(temporary_name, dir_fd=layout.objects)
                    except FileNotFoundError:
                        pass
            if self._read_index(
                layout.indexes, event.product_id, allow_missing=False
            ) != event.event_sha256:
                raise WorkshopError("Manager Match attempt did not persist exactly")
        return self.path / _INDEX_DIRECTORY / name

    def begin(self, pending: PendingWish) -> MatchAttemptEvent:
        if not isinstance(pending, PendingWish):
            raise ContractError("Match attempt requires one PendingWish")
        if pending.catalog_collection != self.collection:
            raise ContractError("Match attempt PendingWish belongs elsewhere")
        current_pending = self._pending_store.load(pending.wish.product_id)
        if (
            not isinstance(current_pending, PendingWish)
            or current_pending.record_sha256 != pending.record_sha256
        ):
            raise WorkshopError(
                "PendingWish changed before the Match attempt started"
            )
        previous = self.load(pending.wish.product_id, allow_missing=True)
        event = MatchAttemptEvent.start(pending, previous)
        self.append(
            event,
            expected_previous_sha256=(
                None if previous is None else previous.event_sha256
            ),
        )
        return event

    def record_waiting(
        self, working: MatchAttemptEvent, needs: Sequence[Need]
    ) -> MatchAttemptEvent:
        event = working.waiting(needs)
        self.append(event, expected_previous_sha256=working.event_sha256)
        return event

    def record_assigned(
        self, working: MatchAttemptEvent, manager_handoff_sha256: str
    ) -> MatchAttemptEvent:
        event = working.assigned(manager_handoff_sha256)
        self.append(event, expected_previous_sha256=working.event_sha256)
        return event


__all__ = [
    "MATCH_ATTEMPT_EVENT_KIND",
    "MATCH_ATTEMPT_INDEX_KIND",
    "MATCH_ATTEMPT_STATES",
    "MatchAttemptEvent",
    "MatchAttemptStore",
]
