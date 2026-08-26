"""Durable Manager-owned plans for bounded batches of Wishes.

A batch is staged before Match or any inventor model runs.  Its immutable,
content-addressed plan binds the ordered Wishes, publication authorizations,
playtest policy, complete catalog/TASTE snapshot, and the exact PendingWish
digest expected for every item.  If a process dies while populating the
per-Wish ledger, replaying :meth:`BatchPlanStore.stage` repairs only missing
exact records and never changes an existing Wish identity.
"""

from __future__ import annotations

import fcntl
import hashlib
import hmac
import json
import os
import secrets
import stat
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple

from .errors import ContractError, WorkshopError
from .handoff import PublicationPolicy
from .make import MAX_OBJECTIVE_CHARS, Wish
from .models import require_sha256
from .pending_wish import PendingWish, PendingWishStore


BATCH_PLAN_KIND = "autonomous-workshop-manager-batch-plan"
BATCH_PLAN_INDEX_KIND = "autonomous-workshop-manager-batch-plan-index"
BATCH_MANAGER_IDENTITY_KIND = "autonomous-workshop-manager-batch-identity"
MAX_BATCH_ITEMS = 1_000
MAX_BATCH_INPUT_BYTES = 10 * 1024 * 1024
MAX_BATCH_PLAN_BYTES = 32 * 1024 * 1024
MAX_BATCH_KEY_CHARS = 256
MAX_BATCH_ID_CHARS = 256
_RUNTIME_DIRECTORY = ".workshop"
_STORE_DIRECTORY = "manager-batches"
_OBJECT_DIRECTORY = "objects"
_INDEX_DIRECTORY = "by-batch"
_LOCK_DIRECTORY = "locks"
_MANAGER_IDENTITY_FILE = "manager-batch-identity.json"
_DIRECTORY_FLAGS = (
    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
)


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Manager batch value must be canonical JSON") from exc


def _submission_identity(
    requests: Sequence["BatchRequest"], *, playtest_rounds: int
) -> Tuple[Dict[str, Any], str]:
    if type(playtest_rounds) is not int or not 1 <= playtest_rounds <= 100:
        raise ContractError("batch playtest_rounds must be from 1 to 100")
    submission = {
        "schema_version": 1,
        "kind": "autonomous-workshop-manager-batch-submission",
        "playtest_rounds": playtest_rounds,
        "requests": [
            {
                "key": item.key,
                "wish": item.wish,
                "visibility": item.visibility,
            }
            for item in requests
        ],
    }
    return submission, hashlib.sha256(_canonical_json(submission)).hexdigest()


def _copy_mapping(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("%s must be one object" % label)
    try:
        copied = json.loads(_canonical_json(value).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:  # pragma: no cover
        raise ContractError("%s must be one JSON object" % label) from exc
    if not isinstance(copied, dict):  # pragma: no cover - Mapping checked above
        raise ContractError("%s must be one JSON object" % label)
    return copied


def _bounded_identifier(value: Any, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or value != value.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or value in (".", "..")
        or any(character in "/\\" for character in value)
    ):
        raise ContractError("%s must be a bounded, path-safe identifier" % label)
    return value


def _batch_key(batch_id: str) -> str:
    _bounded_identifier(batch_id, "Manager batch id", MAX_BATCH_ID_CHARS)
    return hashlib.sha256(batch_id.encode("utf-8")).hexdigest()


def generate_batch_id(
    *, moment: Optional[datetime] = None, token: Optional[str] = None
) -> str:
    """Return an opaque batch identifier that never contains Wish text."""

    observed = moment if moment is not None else datetime.now(timezone.utc)
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    observed = observed.astimezone(timezone.utc)
    suffix = token if token is not None else secrets.token_hex(4)
    if (
        not isinstance(suffix, str)
        or len(suffix) != 8
        or any(character not in "0123456789abcdef" for character in suffix)
    ):
        raise ContractError(
            "Manager batch id token must be eight lowercase hexadecimal characters"
        )
    return "batch-%s-%s" % (observed.strftime("%Y%m%d-%H%M%S"), suffix)


@dataclass(frozen=True)
class BatchRequest:
    """One strictly parsed, ordered request before a Wish id is allocated."""

    key: str
    wish: str
    visibility: str

    def __post_init__(self) -> None:
        _bounded_identifier(self.key, "batch input key", MAX_BATCH_KEY_CHARS)
        if self.visibility not in ("draft", "public"):
            raise ContractError("batch visibility must be draft or public")
        # Reuse the exact stable Wish objective contract without inventing a
        # second text grammar.  The validation-only id never leaves this call.
        validated = Wish.create("batch-input-validation", self.wish)
        if len(validated.objective) > MAX_OBJECTIVE_CHARS:  # defensive clarity
            raise ContractError("batch Wish is too large")


@dataclass(frozen=True)
class BatchManagerIdentity:
    """Private Manager namespace used only to allocate opaque local ids."""

    scope_id: str
    secret: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        require_sha256(self.scope_id, "batch Manager scope id")
        if not isinstance(self.secret, bytes) or len(self.secret) != 32:
            raise ContractError("batch Manager identity secret is invalid")
        expected = hashlib.sha256(
            b"autonomous-workshop-manager-batch-scope-v1\0" + self.secret
        ).hexdigest()
        if not hmac.compare_digest(expected, self.scope_id):
            raise ContractError("batch Manager identity does not match its secret")

    def derive(self, domain: bytes, value: bytes) -> str:
        if not isinstance(domain, bytes) or not domain or not isinstance(value, bytes):
            raise ContractError("batch Manager identity derivation is invalid")
        return hmac.new(self.secret, domain + b"\0" + value, hashlib.sha256).hexdigest()

    def __reduce__(self):  # pragma: no cover - a live Manager secret is not data
        raise TypeError("batch Manager identity cannot be serialized")


class _DuplicateJsonKey(ValueError):
    pass


def _strict_json_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey(key)
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("invalid JSON constant %s" % value)


def _input_lines(source: bytes) -> Tuple[str, ...]:
    if not isinstance(source, bytes):
        raise ContractError("batch input must be bytes")
    if not 1 <= len(source) <= MAX_BATCH_INPUT_BYTES:
        raise ContractError(
            "batch input must contain 1 to %d bytes" % MAX_BATCH_INPUT_BYTES
        )
    try:
        text = source.decode("utf-8")
    except UnicodeError as exc:
        raise ContractError("batch input must be valid UTF-8") from exc
    if text.startswith("\ufeff"):
        raise ContractError("batch input must not contain a UTF-8 byte-order mark")
    # Only LF and CRLF are accepted record separators.  splitlines() also
    # recognizes Unicode separators, which is too permissive for JSONL/lines.
    normalized = text.replace("\r\n", "\n")
    if "\r" in normalized:
        raise ContractError("batch input must use LF or CRLF line endings")
    lines = normalized.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines or any(line == "" for line in lines):
        raise ContractError("batch input cannot contain blank records")
    if len(lines) > MAX_BATCH_ITEMS:
        raise ContractError(
            "batch input cannot contain more than %d Wishes" % MAX_BATCH_ITEMS
        )
    return tuple(lines)


def parse_batch_input(
    source: bytes,
    *,
    input_format: str,
    default_visibility: Optional[str] = None,
) -> Tuple[BatchRequest, ...]:
    """Parse a bounded lines or strict JSONL batch without allocating ids.

    ``lines`` requires a ``draft`` or ``public`` default and assigns stable
    one-based keys (``line-0001``...).  ``jsonl`` requires exactly the keys
    ``key``, ``wish``, and ``visibility`` on every non-blank line.  Passing a
    default for JSONL is allowed only as a consistency check, which lets a CLI
    require one explicit mass-publication choice while retaining per-row data.
    """

    if input_format not in ("lines", "jsonl"):
        raise ContractError("batch input format must be lines or jsonl")
    if default_visibility is not None and default_visibility not in (
        "draft",
        "public",
    ):
        raise ContractError("batch default visibility must be draft or public")
    lines = _input_lines(source)
    requests = []
    if input_format == "lines":
        if default_visibility is None:
            raise ContractError("lines batch input requires an explicit visibility")
        for position, objective in enumerate(lines, 1):
            requests.append(
                BatchRequest(
                    key="line-%04d" % position,
                    wish=objective,
                    visibility=default_visibility,
                )
            )
        normalized = tuple(
            " ".join(unicodedata.normalize("NFKC", item.wish).split()).casefold()
            for item in requests
        )
        if len(normalized) != len(set(normalized)):
            raise ContractError(
                "lines batch input contains repeated normalized Wishes"
            )
    else:
        for position, line in enumerate(lines, 1):
            try:
                value = json.loads(
                    line,
                    object_pairs_hook=_strict_json_object,
                    parse_constant=_reject_json_constant,
                )
            except (UnicodeError, json.JSONDecodeError, ValueError) as exc:
                raise ContractError(
                    "batch JSONL record %d is not strict JSON" % position
                ) from exc
            if not isinstance(value, Mapping) or set(value) != {
                "key",
                "wish",
                "visibility",
            }:
                raise ContractError(
                    "batch JSONL record %d must contain exactly key, wish, and "
                    "visibility" % position
                )
            request = BatchRequest(
                key=value["key"],
                wish=value["wish"],
                visibility=value["visibility"],
            )
            if (
                default_visibility is not None
                and request.visibility != default_visibility
            ):
                raise ContractError(
                    "batch JSONL visibility conflicts with the explicit batch "
                    "visibility"
                )
            requests.append(request)
    keys = tuple(request.key for request in requests)
    if len(set(keys)) != len(keys):
        raise ContractError("batch input keys must be unique")
    return tuple(requests)


def parse_batch_file(
    path: Path,
    *,
    input_format: str,
    default_visibility: Optional[str] = None,
) -> Tuple[BatchRequest, ...]:
    """Read one unchanged regular file without following its final symlink."""

    requested = Path(path)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(str(requested), flags)
    except OSError as exc:
        raise WorkshopError("cannot safely open batch input file") from exc
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise WorkshopError("batch input must be a regular file")
        if not 1 <= opened.st_size <= MAX_BATCH_INPUT_BYTES:
            raise ContractError(
                "batch input must contain 1 to %d bytes" % MAX_BATCH_INPUT_BYTES
            )
        chunks = []
        remaining = MAX_BATCH_INPUT_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        source = b"".join(chunks)
        if len(source) > MAX_BATCH_INPUT_BYTES or os.read(descriptor, 1):
            raise ContractError("batch input exceeds its safe byte limit")
        after = os.fstat(descriptor)
        if (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ) != (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ):
            raise WorkshopError("batch input changed while reading")
    finally:
        os.close(descriptor)
    return parse_batch_input(
        source,
        input_format=input_format,
        default_visibility=default_visibility,
    )


@dataclass(frozen=True)
class BatchPlanItem:
    """One item in canonical batch order."""

    wish: Wish
    publication_policy: PublicationPolicy
    pending_wish_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.wish, Wish):
            raise ContractError("batch plan item requires one typed Wish")
        self.wish.assert_valid()
        if not isinstance(self.publication_policy, PublicationPolicy):
            raise ContractError(
                "batch plan item requires one typed publication policy"
            )
        require_sha256(
            self.pending_wish_sha256,
            "batch plan expected pending Wish sha256",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "wish": self.wish.to_dict(),
            "publication_policy": self.publication_policy.to_dict(),
            "pending_wish_sha256": self.pending_wish_sha256,
        }


@dataclass(frozen=True)
class BatchPlan:
    """Immutable recovery plan saved before any batch Wish is matched."""

    batch_id: str
    manager_scope_id: str
    submission_sha256: str
    playtest_rounds: int
    catalog_collection: Path
    catalog_sha256: str
    catalog_total: int
    catalog_taste_sha256s: Sequence[Tuple[str, str]]
    items: Sequence[BatchPlanItem]
    schema_version: int = 1
    kind: str = BATCH_PLAN_KIND
    plan_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("batch plan schema_version must be 1")
        if self.kind != BATCH_PLAN_KIND:
            raise ContractError("batch plan kind is invalid")
        _bounded_identifier(self.batch_id, "Manager batch id", MAX_BATCH_ID_CHARS)
        require_sha256(self.manager_scope_id, "batch Manager scope id")
        require_sha256(self.submission_sha256, "batch submission sha256")
        if (
            type(self.playtest_rounds) is not int
            or not 1 <= self.playtest_rounds <= 100
        ):
            raise ContractError("batch playtest_rounds must be from 1 to 100")
        collection = Path(self.catalog_collection)
        if not collection.is_absolute():
            raise ContractError("batch catalog collection must be absolute")
        object.__setattr__(self, "catalog_collection", collection)
        require_sha256(self.catalog_sha256, "batch catalog_sha256")
        if type(self.catalog_total) is not int or not 1 <= self.catalog_total <= 10_000:
            raise ContractError("batch catalog_total is invalid")
        try:
            tastes = tuple(self.catalog_taste_sha256s)
        except TypeError as exc:
            raise ContractError("batch catalog Taste identities are invalid") from exc
        if (
            len(tastes) != self.catalog_total
            or not all(
                isinstance(item, (tuple, list)) and len(item) == 2
                for item in tastes
            )
        ):
            raise ContractError("batch catalog Taste identities are invalid")
        normalized_tastes = tuple((item[0], item[1]) for item in tastes)
        for inventor_id, digest in normalized_tastes:
            if not isinstance(inventor_id, str) or not inventor_id:
                raise ContractError("batch catalog inventor id is invalid")
            require_sha256(digest, "batch catalog Taste sha256")
        if (
            tuple(sorted(normalized_tastes)) != normalized_tastes
            or len({item[0] for item in normalized_tastes})
            != len(normalized_tastes)
        ):
            raise ContractError("batch catalog Taste identities are invalid")
        object.__setattr__(self, "catalog_taste_sha256s", normalized_tastes)
        items = tuple(self.items)
        if (
            not 1 <= len(items) <= MAX_BATCH_ITEMS
            or not all(isinstance(item, BatchPlanItem) for item in items)
        ):
            raise ContractError(
                "batch plan requires 1 to %d typed items" % MAX_BATCH_ITEMS
            )
        product_ids = tuple(item.wish.product_id for item in items)
        if len(product_ids) != len(set(product_ids)):
            raise ContractError("batch plan Wish ids must be unique")
        object.__setattr__(self, "items", items)
        for item, pending in zip(items, self.pending_wishes()):
            if pending.record_sha256 != item.pending_wish_sha256:
                raise ContractError(
                    "batch plan expected pending Wish identity is inconsistent"
                )
        source = _canonical_json(self._identity_dict())
        if len(source) > MAX_BATCH_PLAN_BYTES:
            raise ContractError("batch plan exceeds its safe byte limit")
        object.__setattr__(self, "plan_sha256", hashlib.sha256(source).hexdigest())

    @classmethod
    def submission_identity(
        cls,
        requests: Sequence[BatchRequest],
        *,
        playtest_rounds: int,
    ) -> str:
        del cls
        if isinstance(requests, (str, bytes, Mapping)):
            raise ContractError("batch requests must be an ordered sequence")
        try:
            selected = tuple(requests)
        except TypeError as exc:
            raise ContractError(
                "batch requests must be an ordered sequence"
            ) from exc
        if (
            not 1 <= len(selected) <= MAX_BATCH_ITEMS
            or not all(isinstance(item, BatchRequest) for item in selected)
        ):
            raise ContractError(
                "batch requests require 1 to %d typed records" % MAX_BATCH_ITEMS
            )
        unused, digest = _submission_identity(
            selected, playtest_rounds=playtest_rounds
        )
        del unused
        return digest

    @classmethod
    def from_requests(
        cls,
        catalog: Any,
        requests: Sequence[BatchRequest],
        *,
        playtest_rounds: int,
        manager_identity: BatchManagerIdentity,
    ) -> "BatchPlan":
        """Allocate stable, unguessable ids inside one private Manager scope.

        The unkeyed submission digest is persisted only as an integrity and
        idempotency binding. Customer-visible ids are HMAC-derived from the
        Manager's private durable namespace, so identical input in another
        Workshop cannot alias these Wishes or reveal low-entropy Wish text.
        """

        if isinstance(requests, (str, bytes, Mapping)):
            raise ContractError("batch requests must be an ordered sequence")
        try:
            selected = tuple(requests)
        except TypeError as exc:
            raise ContractError("batch requests must be an ordered sequence") from exc
        if (
            not 1 <= len(selected) <= MAX_BATCH_ITEMS
            or not all(isinstance(item, BatchRequest) for item in selected)
        ):
            raise ContractError(
                "batch requests require 1 to %d typed records" % MAX_BATCH_ITEMS
            )
        if not isinstance(manager_identity, BatchManagerIdentity):
            raise ContractError(
                "batch requests require one private Manager identity"
            )
        submission_sha256 = cls.submission_identity(
            selected, playtest_rounds=playtest_rounds
        )
        submission_bytes = bytes.fromhex(submission_sha256)
        batch_token = manager_identity.derive(
            b"autonomous-workshop-batch-id-v1", submission_bytes
        )
        batch_id = "batch-" + batch_token[:32]
        entries = []
        for position, request in enumerate(selected, 1):
            item_token = manager_identity.derive(
                b"autonomous-workshop-batch-wish-id-v1",
                submission_bytes + position.to_bytes(4, "big"),
            )
            wish = Wish.create(
                "wish-batch-%s-%04d" % (item_token[:32], position),
                request.wish,
                context={
                    "source": "workshop-batch",
                    "batch_id": batch_id,
                    "batch_manager_scope_id": manager_identity.scope_id,
                    "batch_key": request.key,
                    "batch_position": position,
                    "batch_submission_sha256": submission_sha256,
                },
            )
            entries.append(
                (
                    wish,
                    PublicationPolicy.for_wish(
                        publish=request.visibility == "public"
                    ),
                )
            )
        return cls.create(
            batch_id,
            catalog,
            tuple(entries),
            playtest_rounds=playtest_rounds,
            manager_scope_id=manager_identity.scope_id,
            submission_sha256=submission_sha256,
        )

    @classmethod
    def create(
        cls,
        batch_id: str,
        catalog: Any,
        entries: Sequence[Tuple[Wish, PublicationPolicy]],
        *,
        playtest_rounds: int,
        manager_scope_id: Optional[str] = None,
        submission_sha256: Optional[str] = None,
    ) -> "BatchPlan":
        """Snapshot one catalog once and bind all ordered entries to it."""

        if isinstance(entries, (str, bytes, Mapping)):
            raise ContractError("batch entries must be an ordered sequence")
        try:
            copied = tuple(entries)
        except TypeError as exc:
            raise ContractError("batch entries must be an ordered sequence") from exc
        if not 1 <= len(copied) <= MAX_BATCH_ITEMS:
            raise ContractError(
                "batch plan requires 1 to %d entries" % MAX_BATCH_ITEMS
            )
        typed = []
        for entry in copied:
            if (
                not isinstance(entry, (tuple, list))
                or len(entry) != 2
                or not isinstance(entry[0], Wish)
                or not isinstance(entry[1], PublicationPolicy)
            ):
                raise ContractError(
                    "each batch entry must contain one Wish and publication policy"
                )
            typed.append((entry[0], entry[1]))
        first_wish, first_policy = typed[0]
        snapshot = PendingWish.create(
            first_wish,
            first_policy,
            catalog,
            playtest_rounds=playtest_rounds,
        )
        records = [snapshot]
        for wish, policy in typed[1:]:
            records.append(
                PendingWish(
                    wish=wish,
                    publication_policy=policy,
                    playtest_rounds=playtest_rounds,
                    catalog_collection=snapshot.catalog_collection,
                    catalog_sha256=snapshot.catalog_sha256,
                    catalog_total=snapshot.catalog_total,
                    catalog_taste_sha256s=snapshot.catalog_taste_sha256s,
                )
            )
        # Recheck membership, manifests, headers, and every complete TASTE
        # after all records have been assembled from the one snapshot.
        snapshot.assert_catalog_current(catalog)
        explicit_identity = _canonical_json(
            {
                "batch_id": batch_id,
                "playtest_rounds": playtest_rounds,
                "items": [
                    {
                        "wish": wish.to_dict(),
                        "publication_policy": policy.to_dict(),
                    }
                    for wish, policy in typed
                ],
            }
        )
        selected_submission = (
            hashlib.sha256(explicit_identity).hexdigest()
            if submission_sha256 is None
            else submission_sha256
        )
        selected_scope = (
            hashlib.sha256(
                b"autonomous-workshop-explicit-batch-scope-v1\0"
                + batch_id.encode("utf-8")
            ).hexdigest()
            if manager_scope_id is None
            else manager_scope_id
        )
        return cls.from_pending_wishes(
            batch_id,
            records,
            manager_scope_id=selected_scope,
            submission_sha256=selected_submission,
        )

    @classmethod
    def from_pending_wishes(
        cls,
        batch_id: str,
        records: Sequence[PendingWish],
        *,
        manager_scope_id: Optional[str] = None,
        submission_sha256: Optional[str] = None,
    ) -> "BatchPlan":
        if isinstance(records, (str, bytes, Mapping)):
            raise ContractError("batch pending Wishes must be an ordered sequence")
        try:
            copied = tuple(records)
        except TypeError as exc:
            raise ContractError(
                "batch pending Wishes must be an ordered sequence"
            ) from exc
        if (
            not 1 <= len(copied) <= MAX_BATCH_ITEMS
            or not all(isinstance(record, PendingWish) for record in copied)
        ):
            raise ContractError(
                "batch requires 1 to %d typed pending Wishes" % MAX_BATCH_ITEMS
            )
        first = copied[0]
        if not first.catalog_taste_identity_bound:
            raise ContractError("batch plans require complete catalog Taste identities")
        for record in copied:
            if (
                not record.catalog_taste_identity_bound
                or record.playtest_rounds != first.playtest_rounds
                or record.catalog_collection != first.catalog_collection
                or record.catalog_sha256 != first.catalog_sha256
                or record.catalog_total != first.catalog_total
                or record.catalog_taste_sha256s != first.catalog_taste_sha256s
            ):
                raise ContractError(
                    "batch pending Wishes do not share one exact catalog snapshot"
                )
        record_identity = _canonical_json(
            {
                "batch_id": batch_id,
                "records": [record.to_dict() for record in copied],
            }
        )
        selected_scope = (
            hashlib.sha256(
                b"autonomous-workshop-explicit-batch-scope-v1\0"
                + batch_id.encode("utf-8")
            ).hexdigest()
            if manager_scope_id is None
            else manager_scope_id
        )
        selected_submission = (
            hashlib.sha256(record_identity).hexdigest()
            if submission_sha256 is None
            else submission_sha256
        )
        return cls(
            batch_id=batch_id,
            manager_scope_id=selected_scope,
            submission_sha256=selected_submission,
            playtest_rounds=first.playtest_rounds,
            catalog_collection=first.catalog_collection,
            catalog_sha256=first.catalog_sha256,
            catalog_total=first.catalog_total,
            catalog_taste_sha256s=first.catalog_taste_sha256s,
            items=tuple(
                BatchPlanItem(
                    wish=record.wish,
                    publication_policy=record.publication_policy,
                    pending_wish_sha256=record.record_sha256,
                )
                for record in copied
            ),
        )

    def _identity_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "batch_id": self.batch_id,
            "manager_scope_id": self.manager_scope_id,
            "submission_sha256": self.submission_sha256,
            "playtest_rounds": self.playtest_rounds,
            "catalog": {
                "collection": str(self.catalog_collection),
                "catalog_sha256": self.catalog_sha256,
                "total": self.catalog_total,
                "taste_sha256s": [
                    {"inventor_id": inventor_id, "taste_sha256": digest}
                    for inventor_id, digest in self.catalog_taste_sha256s
                ],
            },
            "items": [item.to_dict() for item in self.items],
        }

    def object_bytes(self) -> bytes:
        return _canonical_json(self._identity_dict())

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["plan_sha256"] = self.plan_sha256
        return payload

    def pending_wishes(self) -> Tuple[PendingWish, ...]:
        return tuple(
            PendingWish(
                wish=item.wish,
                publication_policy=item.publication_policy,
                playtest_rounds=self.playtest_rounds,
                catalog_collection=self.catalog_collection,
                catalog_sha256=self.catalog_sha256,
                catalog_total=self.catalog_total,
                catalog_taste_sha256s=self.catalog_taste_sha256s,
            )
            for item in self.items
        )

    def assert_catalog_current(self, catalog: Any) -> None:
        """Fail if Match would run under anything but the plan's full snapshot."""

        self.pending_wishes()[0].assert_catalog_current(catalog)

    @classmethod
    def from_object_bytes(cls, source: bytes, *, expected_sha256: str) -> "BatchPlan":
        require_sha256(expected_sha256, "batch plan object address")
        if (
            not isinstance(source, bytes)
            or not 1 <= len(source) <= MAX_BATCH_PLAN_BYTES
        ):
            raise ContractError("batch plan object bytes are empty or too large")
        if hashlib.sha256(source).hexdigest() != expected_sha256:
            raise ContractError("batch plan object address does not match its bytes")
        try:
            value = json.loads(source.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError("batch plan object is not valid UTF-8 JSON") from exc
        payload = _copy_mapping(value, "batch plan object")
        if set(payload) != {
            "schema_version",
            "kind",
            "batch_id",
            "manager_scope_id",
            "submission_sha256",
            "playtest_rounds",
            "catalog",
            "items",
        }:
            raise ContractError("batch plan object fields are invalid")
        catalog = _copy_mapping(payload["catalog"], "batch plan catalog")
        if set(catalog) != {
            "collection",
            "catalog_sha256",
            "total",
            "taste_sha256s",
        }:
            raise ContractError("batch plan catalog fields are invalid")
        raw_tastes = catalog["taste_sha256s"]
        if not isinstance(raw_tastes, list):
            raise ContractError("batch plan catalog Taste identities are malformed")
        tastes = []
        for raw in raw_tastes:
            item = _copy_mapping(raw, "batch plan catalog Taste identity")
            if set(item) != {"inventor_id", "taste_sha256"}:
                raise ContractError("batch plan catalog Taste identity is malformed")
            tastes.append((item["inventor_id"], item["taste_sha256"]))
        raw_items = payload["items"]
        if not isinstance(raw_items, list):
            raise ContractError("batch plan items are malformed")
        items = []
        for raw in raw_items:
            item = _copy_mapping(raw, "batch plan item")
            if set(item) != {
                "wish",
                "publication_policy",
                "pending_wish_sha256",
            }:
                raise ContractError("batch plan item fields are invalid")
            wish_payload = _copy_mapping(item["wish"], "batch plan Wish")
            if set(wish_payload) != {
                "schema_version",
                "product_id",
                "objective",
                "constraints",
                "context",
            }:
                raise ContractError("batch plan Wish fields are invalid")
            try:
                wish = Wish(**wish_payload)
            except TypeError as exc:
                raise ContractError("batch plan Wish is malformed") from exc
            items.append(
                BatchPlanItem(
                    wish=wish,
                    publication_policy=PublicationPolicy.from_dict(
                        _copy_mapping(
                            item["publication_policy"],
                            "batch plan publication policy",
                        )
                    ),
                    pending_wish_sha256=item["pending_wish_sha256"],
                )
            )
        plan = cls(
            batch_id=payload["batch_id"],
            manager_scope_id=payload["manager_scope_id"],
            submission_sha256=payload["submission_sha256"],
            playtest_rounds=payload["playtest_rounds"],
            catalog_collection=Path(catalog["collection"]),
            catalog_sha256=catalog["catalog_sha256"],
            catalog_total=catalog["total"],
            catalog_taste_sha256s=tuple(tastes),
            items=tuple(items),
            schema_version=payload["schema_version"],
            kind=payload["kind"],
        )
        if plan.plan_sha256 != expected_sha256 or plan.object_bytes() != source:
            raise ContractError("batch plan object is not exact canonical bytes")
        return plan


def _read_exact_file(
    directory_descriptor: int,
    name: str,
    *,
    label: str,
    maximum: int,
) -> bytes:
    try:
        expected = os.stat(name, dir_fd=directory_descriptor, follow_symlinks=False)
    except FileNotFoundError:
        raise WorkshopError("%s is missing" % label)
    if not stat.S_ISREG(expected.st_mode):
        raise WorkshopError("%s must be a regular file" % label)
    if stat.S_IMODE(expected.st_mode) & 0o077:
        raise WorkshopError("%s permissions are not private" % label)
    if not 1 <= expected.st_size <= maximum:
        raise WorkshopError("%s is empty or too large" % label)
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_descriptor,
        )
    except OSError as exc:
        raise WorkshopError("cannot safely read %s" % label) from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise WorkshopError("%s changed while opening" % label)
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        source = b"".join(chunks)
        if len(source) > maximum or os.read(descriptor, 1):
            raise WorkshopError("%s is too large" % label)
        after = os.fstat(descriptor)
        if (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        ) != (
            opened.st_dev,
            opened.st_ino,
            opened.st_size,
            opened.st_mtime_ns,
        ):
            raise WorkshopError("%s changed while reading" % label)
        return source
    finally:
        os.close(descriptor)


def _write_private_exclusive(
    directory_descriptor: int,
    name: str,
    source: bytes,
    *,
    label: str,
) -> bool:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(name, flags, 0o600, dir_fd=directory_descriptor)
    except FileExistsError:
        return False
    except OSError as exc:
        raise WorkshopError("cannot save %s" % label) from exc
    try:
        os.fchmod(descriptor, 0o600)
        written = 0
        while written < len(source):
            count = os.write(descriptor, source[written:])
            if count <= 0:  # pragma: no cover - defensive short-write guard
                raise WorkshopError("cannot completely save %s" % label)
            written += count
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.fsync(directory_descriptor)
    return True


def _write_atomic_exclusive(
    staging_descriptor: int,
    target_descriptor: int,
    name: str,
    source: bytes,
    *,
    label: str,
) -> bool:
    """Link fully-fsynced bytes into their final name without partial finals."""

    temporary_name = ".batch-%s.tmp" % secrets.token_hex(16)
    created = _write_private_exclusive(
        staging_descriptor,
        temporary_name,
        source,
        label="%s staging file" % label,
    )
    if not created:  # pragma: no cover - a 128-bit random collision
        raise WorkshopError("cannot reserve %s staging file" % label)
    linked = False
    try:
        try:
            os.link(
                temporary_name,
                name,
                src_dir_fd=staging_descriptor,
                dst_dir_fd=target_descriptor,
                follow_symlinks=False,
            )
        except FileExistsError:
            return False
        except OSError as exc:
            raise WorkshopError("cannot atomically save %s" % label) from exc
        linked = True
        os.fsync(target_descriptor)
        return True
    finally:
        try:
            os.unlink(temporary_name, dir_fd=staging_descriptor)
            os.fsync(staging_descriptor)
        except FileNotFoundError:  # pragma: no cover - defensive race guard
            pass
        except OSError as exc:
            if linked:
                raise WorkshopError("cannot clean %s staging file" % label) from exc


def load_or_create_batch_manager_identity(scope_root: Path) -> BatchManagerIdentity:
    """Load one private, durable namespace shared by this Manager's catalogs."""

    requested = Path(scope_root)
    if not requested.is_absolute() or requested.is_symlink():
        raise WorkshopError("batch Manager scope must be an absolute regular directory")
    try:
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise WorkshopError("cannot resolve batch Manager scope") from exc
    if resolved != requested or not resolved.is_dir():
        raise WorkshopError("batch Manager scope must be an absolute regular directory")
    try:
        scope_descriptor = os.open(str(resolved), _DIRECTORY_FLAGS)
    except OSError as exc:
        raise WorkshopError("cannot safely open batch Manager scope") from exc
    runtime_descriptor = None
    try:
        expected = os.fstat(scope_descriptor)
        if not stat.S_ISDIR(expected.st_mode):  # pragma: no cover - opened as directory
            raise WorkshopError("batch Manager scope must be a regular directory")
        try:
            runtime_stat = os.stat(
                _RUNTIME_DIRECTORY,
                dir_fd=scope_descriptor,
                follow_symlinks=False,
            )
        except FileNotFoundError:
            try:
                os.mkdir(_RUNTIME_DIRECTORY, 0o700, dir_fd=scope_descriptor)
                os.fsync(scope_descriptor)
            except FileExistsError:
                pass
            except OSError as exc:
                raise WorkshopError("cannot create batch Manager runtime") from exc
            runtime_stat = os.stat(
                _RUNTIME_DIRECTORY,
                dir_fd=scope_descriptor,
                follow_symlinks=False,
            )
        if not stat.S_ISDIR(runtime_stat.st_mode):
            raise WorkshopError("batch Manager runtime must be a regular directory")
        runtime_descriptor = os.open(
            _RUNTIME_DIRECTORY, _DIRECTORY_FLAGS, dir_fd=scope_descriptor
        )
        opened = os.fstat(runtime_descriptor)
        if (opened.st_dev, opened.st_ino) != (
            runtime_stat.st_dev,
            runtime_stat.st_ino,
        ):
            raise WorkshopError("batch Manager runtime changed while opening")
        os.fchmod(runtime_descriptor, 0o700)

        def identity_bytes(secret: bytes) -> bytes:
            scope_id = hashlib.sha256(
                b"autonomous-workshop-manager-batch-scope-v1\0" + secret
            ).hexdigest()
            return _canonical_json(
                {
                    "schema_version": 1,
                    "kind": BATCH_MANAGER_IDENTITY_KIND,
                    "scope_id": scope_id,
                    "secret_hex": secret.hex(),
                }
            )

        try:
            source = _read_exact_file(
                runtime_descriptor,
                _MANAGER_IDENTITY_FILE,
                label="batch Manager identity",
                maximum=16 * 1024,
            )
        except WorkshopError as missing:
            try:
                os.stat(
                    _MANAGER_IDENTITY_FILE,
                    dir_fd=runtime_descriptor,
                    follow_symlinks=False,
                )
            except FileNotFoundError:
                proposed = secrets.token_bytes(32)
                if _write_atomic_exclusive(
                    runtime_descriptor,
                    runtime_descriptor,
                    _MANAGER_IDENTITY_FILE,
                    identity_bytes(proposed),
                    label="batch Manager identity",
                ):
                    source = identity_bytes(proposed)
                else:
                    source = _read_exact_file(
                        runtime_descriptor,
                        _MANAGER_IDENTITY_FILE,
                        label="batch Manager identity",
                        maximum=16 * 1024,
                    )
            else:
                raise missing
        try:
            value = json.loads(source.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise WorkshopError("batch Manager identity is not valid JSON") from exc
        if not isinstance(value, Mapping) or set(value) != {
            "schema_version",
            "kind",
            "scope_id",
            "secret_hex",
        }:
            raise WorkshopError("batch Manager identity fields are invalid")
        if value["schema_version"] != 1 or value["kind"] != BATCH_MANAGER_IDENTITY_KIND:
            raise WorkshopError("batch Manager identity kind is invalid")
        try:
            secret = bytes.fromhex(value["secret_hex"])
        except (TypeError, ValueError) as exc:
            raise WorkshopError("batch Manager identity secret is invalid") from exc
        try:
            identity = BatchManagerIdentity(value["scope_id"], secret)
        except ContractError as exc:
            raise WorkshopError(str(exc)) from exc
        if source != identity_bytes(secret):
            raise WorkshopError("batch Manager identity is not exact canonical bytes")
        return identity
    finally:
        if runtime_descriptor is not None:
            os.close(runtime_descriptor)
        os.close(scope_descriptor)


@dataclass(frozen=True)
class _Layout:
    collection: int
    runtime: int
    store: int
    objects: int
    indexes: int
    locks: int


class _MissingStore(Exception):
    pass


class BatchPlanStore:
    """Secure Manager batch-plan store rooted in one inventor collection."""

    def __init__(self, catalog_collection: Path) -> None:
        requested = Path(catalog_collection)
        if not requested.is_absolute() or requested.is_symlink():
            raise WorkshopError(
                "Manager batch catalog must be an absolute regular directory"
            )
        try:
            resolved = requested.resolve(strict=True)
        except OSError as exc:
            raise WorkshopError("cannot resolve Manager batch catalog") from exc
        if resolved != requested or not resolved.is_dir():
            raise WorkshopError(
                "Manager batch catalog must be an absolute regular directory"
            )
        self.collection = resolved

    @property
    def path(self) -> Path:
        return self.collection / _RUNTIME_DIRECTORY / _STORE_DIRECTORY

    @staticmethod
    def _open_child(
        parent_descriptor: int,
        name: str,
        *,
        label: str,
        create: bool,
    ) -> int:
        try:
            expected = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        except FileNotFoundError:
            if not create:
                raise _MissingStore()
            try:
                os.mkdir(name, 0o700, dir_fd=parent_descriptor)
                os.fsync(parent_descriptor)
            except FileExistsError:
                pass
            except OSError as exc:
                raise WorkshopError("cannot create %s" % label) from exc
            expected = os.stat(name, dir_fd=parent_descriptor, follow_symlinks=False)
        if not stat.S_ISDIR(expected.st_mode):
            raise WorkshopError("%s must be a regular directory" % label)
        try:
            descriptor = os.open(name, _DIRECTORY_FLAGS, dir_fd=parent_descriptor)
        except OSError as exc:
            raise WorkshopError("cannot safely open %s" % label) from exc
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino):
            os.close(descriptor)
            raise WorkshopError("%s changed while opening" % label)
        if create:
            try:
                os.fchmod(descriptor, 0o700)
            except OSError as exc:
                os.close(descriptor)
                raise WorkshopError("cannot secure %s" % label) from exc
        elif stat.S_IMODE(opened.st_mode) & 0o077:
            os.close(descriptor)
            raise WorkshopError("%s permissions are not private" % label)
        return descriptor

    @contextmanager
    def _layout(self, *, create: bool) -> Iterator[_Layout]:
        try:
            expected = self.collection.lstat()
        except OSError as exc:
            raise WorkshopError("cannot inspect Manager batch catalog") from exc
        if not stat.S_ISDIR(expected.st_mode) or stat.S_ISLNK(expected.st_mode):
            raise WorkshopError("Manager batch catalog must be a regular directory")
        try:
            collection = os.open(str(self.collection), _DIRECTORY_FLAGS)
        except OSError as exc:
            raise WorkshopError("cannot safely open Manager batch catalog") from exc
        descriptors = [collection]
        try:
            opened = os.fstat(collection)
            if (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino):
                raise WorkshopError("Manager batch catalog changed while opening")
            runtime = self._open_child(
                collection,
                _RUNTIME_DIRECTORY,
                label="Manager runtime",
                create=create,
            )
            descriptors.append(runtime)
            store = self._open_child(
                runtime,
                _STORE_DIRECTORY,
                label="Manager batch storage",
                create=create,
            )
            descriptors.append(store)
            objects = self._open_child(
                store,
                _OBJECT_DIRECTORY,
                label="Manager batch object storage",
                create=create,
            )
            descriptors.append(objects)
            indexes = self._open_child(
                store,
                _INDEX_DIRECTORY,
                label="Manager batch index storage",
                create=create,
            )
            descriptors.append(indexes)
            locks = self._open_child(
                store,
                _LOCK_DIRECTORY,
                label="Manager batch lock storage",
                create=create,
            )
            descriptors.append(locks)
            yield _Layout(collection, runtime, store, objects, indexes, locks)
            current = self.collection.lstat()
            if (
                not stat.S_ISDIR(current.st_mode)
                or (current.st_dev, current.st_ino)
                != (opened.st_dev, opened.st_ino)
            ):
                raise WorkshopError("Manager batch catalog changed during access")
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    @staticmethod
    def _index_bytes(batch_id: str, plan_sha256: str) -> bytes:
        require_sha256(plan_sha256, "batch plan sha256")
        return _canonical_json(
            {
                "schema_version": 1,
                "kind": BATCH_PLAN_INDEX_KIND,
                "batch_id": batch_id,
                "plan_sha256": plan_sha256,
            }
        )

    @classmethod
    def _read_index(
        cls, indexes: int, batch_id: str, *, allow_missing: bool
    ) -> Optional[str]:
        name = _batch_key(batch_id) + ".json"
        try:
            os.stat(name, dir_fd=indexes, follow_symlinks=False)
        except FileNotFoundError:
            if allow_missing:
                return None
            raise WorkshopError("Manager batch index is missing")
        source = _read_exact_file(
            indexes,
            name,
            label="Manager batch index",
            maximum=256 * 1024,
        )
        try:
            value = json.loads(source.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise WorkshopError("Manager batch index is not valid UTF-8 JSON") from exc
        payload = _copy_mapping(value, "Manager batch index")
        if set(payload) != {
            "schema_version",
            "kind",
            "batch_id",
            "plan_sha256",
        }:
            raise WorkshopError("Manager batch index fields are invalid")
        if payload["schema_version"] != 1 or payload["kind"] != BATCH_PLAN_INDEX_KIND:
            raise WorkshopError("Manager batch index identity is invalid")
        if payload["batch_id"] != batch_id:
            raise WorkshopError("Manager batch id hash collision detected")
        try:
            require_sha256(payload["plan_sha256"], "batch plan sha256")
        except ContractError as exc:
            raise WorkshopError(str(exc)) from exc
        if source != cls._index_bytes(batch_id, payload["plan_sha256"]):
            raise WorkshopError("Manager batch index is not exact canonical bytes")
        return payload["plan_sha256"]

    @staticmethod
    def _read_object(objects: int, plan_sha256: str) -> BatchPlan:
        source = _read_exact_file(
            objects,
            plan_sha256 + ".json",
            label="Manager batch plan object",
            maximum=MAX_BATCH_PLAN_BYTES,
        )
        try:
            return BatchPlan.from_object_bytes(source, expected_sha256=plan_sha256)
        except ContractError as exc:
            raise WorkshopError(str(exc)) from exc

    @classmethod
    def _validated_indexes(cls, indexes: int) -> Dict[str, str]:
        names = tuple(sorted(os.listdir(indexes)))
        if len(names) > 10_000:
            raise WorkshopError("Manager batch index exceeds its safe limit")
        records: Dict[str, str] = {}
        for name in names:
            if (
                not name.endswith(".json")
                or len(name) != 64 + len(".json")
                or any(
                    character not in "0123456789abcdef" for character in name[:64]
                )
            ):
                raise WorkshopError("Manager batch index filename is invalid")
            source = _read_exact_file(
                indexes,
                name,
                label="Manager batch index",
                maximum=256 * 1024,
            )
            try:
                payload = json.loads(source.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise WorkshopError(
                    "Manager batch index is not valid UTF-8 JSON"
                ) from exc
            if not isinstance(payload, Mapping) or not isinstance(
                payload.get("batch_id"), str
            ):
                raise WorkshopError("Manager batch index is malformed")
            batch_id = payload["batch_id"]
            if name != _batch_key(batch_id) + ".json":
                raise WorkshopError("Manager batch id hash collision detected")
            if batch_id in records:
                raise WorkshopError("duplicate Manager batch id detected")
            plan_sha256 = cls._read_index(indexes, batch_id, allow_missing=False)
            records[batch_id] = plan_sha256
        return records

    @staticmethod
    def _save_object(objects: int, plan: BatchPlan) -> None:
        name = plan.plan_sha256 + ".json"
        if _write_atomic_exclusive(
            objects,
            objects,
            name,
            plan.object_bytes(),
            label="Manager batch plan object",
        ):
            return
        existing = _read_exact_file(
            objects,
            name,
            label="Manager batch plan object",
            maximum=MAX_BATCH_PLAN_BYTES,
        )
        if existing != plan.object_bytes():
            raise WorkshopError("Manager batch content-address collision detected")

    def save(self, plan: BatchPlan) -> Path:
        """Persist one plan exclusively; exact repeated saves are idempotent."""

        if not isinstance(plan, BatchPlan):
            raise ContractError("Manager batch store requires a typed plan")
        if plan.catalog_collection != self.collection:
            raise ContractError(
                "Manager batch plan belongs to a different catalog root"
            )
        with self._layout(create=True) as layout:
            existing_indexes = self._validated_indexes(layout.indexes)
            current_sha256 = existing_indexes.get(plan.batch_id)
            if (
                current_sha256 is not None
                and current_sha256 != plan.plan_sha256
            ):
                raise WorkshopError(
                    "this batch id is already bound to a different immutable plan"
                )
            self._save_object(layout.objects, plan)
            name = _batch_key(plan.batch_id) + ".json"
            source = self._index_bytes(plan.batch_id, plan.plan_sha256)
            if not _write_atomic_exclusive(
                layout.objects,
                layout.indexes,
                name,
                source,
                label="Manager batch index",
            ):
                # Trust only a fresh exact read at the commit boundary.  The
                # pointer may have changed after the initial global validation.
                current_sha256 = self._read_index(
                    layout.indexes, plan.batch_id, allow_missing=False
                )
                if current_sha256 != plan.plan_sha256:
                    raise WorkshopError(
                        "this batch id is already bound to a different immutable plan"
                    )
        return self.path / _INDEX_DIRECTORY / name

    def load(
        self, batch_id: str, *, allow_missing: bool = False
    ) -> Optional[BatchPlan]:
        _batch_key(batch_id)
        try:
            with self._layout(create=False) as layout:
                plan_sha256 = self._validated_indexes(layout.indexes).get(batch_id)
                if plan_sha256 is None:
                    if allow_missing:
                        return None
                    raise WorkshopError("Manager batch index is missing")
                plan = self._read_object(layout.objects, plan_sha256)
        except _MissingStore:
            if allow_missing:
                return None
            raise WorkshopError("this batch has no saved Manager plan")
        if plan.batch_id != batch_id:
            raise WorkshopError("Manager batch plan belongs to another batch")
        if plan.catalog_collection != self.collection:
            raise WorkshopError("Manager batch plan belongs to another catalog root")
        return plan

    def list(self) -> Tuple[BatchPlan, ...]:
        try:
            with self._layout(create=False) as layout:
                plans = []
                for batch_id, plan_sha256 in self._validated_indexes(
                    layout.indexes
                ).items():
                    plan = self._read_object(layout.objects, plan_sha256)
                    if plan.batch_id != batch_id:
                        raise WorkshopError(
                            "Manager batch plan belongs to another batch"
                        )
                    if plan.catalog_collection != self.collection:
                        raise WorkshopError(
                            "Manager batch plan belongs to another catalog root"
                        )
                    plans.append(plan)
                return tuple(plans)
        except _MissingStore:
            return ()

    def _repair_pending(
        self, plan: BatchPlan, pending_store: PendingWishStore
    ) -> Tuple[PendingWish, ...]:
        if pending_store.collection != self.collection:
            raise ContractError(
                "Manager batch and pending Wish stores use different catalog roots"
            )
        expected_records = plan.pending_wishes()

        def compatible(expected: PendingWish, current: PendingWish) -> bool:
            if (
                current.record_sha256 == expected.record_sha256
                and current.object_bytes() == expected.object_bytes()
            ):
                return True
            return (
                current.wish.to_dict() == expected.wish.to_dict()
                and current.playtest_rounds == expected.playtest_rounds
                and current.catalog_collection == expected.catalog_collection
                and current.catalog_sha256 == expected.catalog_sha256
                and current.catalog_total == expected.catalog_total
                and current.catalog_taste_sha256s
                == expected.catalog_taste_sha256s
                and expected.publication_policy.visibility == "draft"
                and current.publication_policy.visibility == "public"
                and current.publication_policy.authorization
                == "explicit-resume-publish"
            )

        for expected in expected_records:
            with pending_store.lock(expected.wish.product_id):
                current = pending_store._batch_load(
                    expected.wish.product_id, allow_missing=True
                )
                if current is None:
                    pending_store._batch_save(expected)
                    current = pending_store._batch_load(expected.wish.product_id)
                if not compatible(expected, current):
                    raise WorkshopError(
                        "batch Wish id is already bound to a different pending record"
                    )
        # A final ordered read is both the caller's staging receipt and a guard
        # against non-cooperating writers racing between individual locks.
        repaired = []
        for expected in expected_records:
            current = pending_store._batch_load(expected.wish.product_id)
            if not compatible(expected, current):
                raise WorkshopError("batch pending Wish changed during repair")
            repaired.append(current)
        return tuple(repaired)

    def stage(
        self,
        plan: BatchPlan,
        pending_store: Optional[PendingWishStore] = None,
    ) -> Tuple[PendingWish, ...]:
        """Save the plan first, then idempotently populate its PendingWishes."""

        if not isinstance(plan, BatchPlan):
            raise ContractError("Manager batch stage requires a typed plan")
        target = pending_store or PendingWishStore(self.collection)
        if not isinstance(target, PendingWishStore):
            raise ContractError("Manager batch stage requires a pending Wish store")
        with self.lock(plan.batch_id):
            self.save(plan)
            saved = self.load(plan.batch_id)
            if (
                saved.plan_sha256 != plan.plan_sha256
                or saved.object_bytes() != plan.object_bytes()
            ):
                raise WorkshopError("Manager batch plan changed before staging")
            return self._repair_pending(plan, target)

    def repair_pending(
        self,
        plan: BatchPlan,
        pending_store: Optional[PendingWishStore] = None,
    ) -> Tuple[PendingWish, ...]:
        """Repair gaps only after verifying this exact plan is already durable."""

        if not isinstance(plan, BatchPlan):
            raise ContractError("Manager batch repair requires a typed plan")
        target = pending_store or PendingWishStore(self.collection)
        if not isinstance(target, PendingWishStore):
            raise ContractError("Manager batch repair requires a pending Wish store")
        with self.lock(plan.batch_id):
            saved = self.load(plan.batch_id)
            if (
                saved.plan_sha256 != plan.plan_sha256
                or saved.object_bytes() != plan.object_bytes()
            ):
                raise WorkshopError(
                    "Manager batch repair requires its exact saved plan"
                )
            return self._repair_pending(plan, target)

    @contextmanager
    def supervise(
        self,
        plan: BatchPlan,
        pending_store: Optional[PendingWishStore] = None,
    ) -> Iterator[Tuple[PendingWish, ...]]:
        """Fail fast and hold one lock across repair, scheduling, and workers."""

        if not isinstance(plan, BatchPlan):
            raise ContractError("Manager batch supervision requires a typed plan")
        target = pending_store or PendingWishStore(self.collection)
        if not isinstance(target, PendingWishStore):
            raise ContractError(
                "Manager batch supervision requires a pending Wish store"
            )
        with self.lock(plan.batch_id, blocking=False):
            saved = self.load(plan.batch_id)
            if (
                saved.plan_sha256 != plan.plan_sha256
                or saved.object_bytes() != plan.object_bytes()
            ):
                raise WorkshopError(
                    "Manager batch supervision requires its exact saved plan"
                )
            yield self._repair_pending(plan, target)

    @contextmanager
    def lock(self, batch_id: str, *, blocking: bool = True) -> Iterator[None]:
        """Serialize staging and scheduling for one exact batch id."""

        if type(blocking) is not bool:
            raise ContractError("Manager batch lock blocking flag must be boolean")

        name = _batch_key(batch_id) + ".lock"
        with self._layout(create=True) as layout:
            flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(name, flags, 0o600, dir_fd=layout.locks)
            except OSError as exc:
                raise WorkshopError("cannot open Manager batch lock") from exc
            try:
                opened = os.fstat(descriptor)
                if not stat.S_ISREG(opened.st_mode):
                    raise WorkshopError("Manager batch lock must be a regular file")
                os.fchmod(descriptor, 0o600)
                try:
                    fcntl.flock(
                        descriptor,
                        fcntl.LOCK_EX | (0 if blocking else fcntl.LOCK_NB),
                    )
                except BlockingIOError:
                    raise WorkshopError(
                        "another Manager is already supervising this batch"
                    ) from None
                current = os.stat(name, dir_fd=layout.locks, follow_symlinks=False)
                if (
                    not stat.S_ISREG(current.st_mode)
                    or (current.st_dev, current.st_ino)
                    != (opened.st_dev, opened.st_ino)
                ):
                    raise WorkshopError("Manager batch lock changed while opening")
                yield
            finally:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)
