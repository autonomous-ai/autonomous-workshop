"""Manager-owned durable Wishes that have not completed Match yet.

The customer-visible Wish id exists before semantic routing starts.  This store
therefore belongs to the Manager and to the catalog as a whole, never to a
selected Inventor.  An immutable object is addressed by the SHA-256 of its
canonical bytes; a small Wish-id index points at that object so status and
resume do not need to guess which Inventor might eventually own the work.
"""

from __future__ import annotations

import contextvars
import fcntl
import hashlib
import json
import os
import secrets
import stat
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, Mapping, Optional, Sequence, Tuple

from .errors import ContractError, WorkshopError
from .handoff import PublicationPolicy
from .make import MAX_PRODUCT_ID_CHARS, Wish
from .models import require_sha256
from .taste import load_taste


PENDING_WISH_KIND = "autonomous-workshop-manager-pending-wish"
PENDING_WISH_INDEX_KIND = "autonomous-workshop-manager-pending-wish-index"
MAX_PENDING_WISH_BYTES = 256 * 1024
MAX_PENDING_WISHES = 10_000
_RUNTIME_DIRECTORY = ".workshop"
_STORE_DIRECTORY = "manager-wishes"
_OBJECT_DIRECTORY = "objects"
_INDEX_DIRECTORY = "by-wish"
_LOCK_DIRECTORY = "locks"
_DIRECTORY_FLAGS = (
    os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0)
)
_BATCH_INDEX_SNAPSHOTS: contextvars.ContextVar[
    Mapping[Path, Tuple[Tuple[int, int, int, int], Mapping[str, str]]]
] = contextvars.ContextVar("workshop_pending_batch_indexes", default={})


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
        raise ContractError("pending Wish must be canonical JSON") from exc


def _copy_mapping(value: Mapping[str, Any], label: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ContractError("%s must be one object" % label)
    try:
        copied = json.loads(_canonical_json(value).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:  # pragma: no cover
        raise ContractError("%s must be one JSON object" % label) from exc
    if not isinstance(copied, dict):  # pragma: no cover - Mapping serialized above
        raise ContractError("%s must be one JSON object" % label)
    return copied


def _product_key(product_id: str) -> str:
    if (
        not isinstance(product_id, str)
        or not product_id.strip()
        or len(product_id) > MAX_PRODUCT_ID_CHARS
        or product_id in (".", "..")
        or any(character in "/\\" for character in product_id)
        or any(ord(character) < 32 or ord(character) == 127 for character in product_id)
    ):
        raise ContractError("pending Wish product_id is invalid")
    return hashlib.sha256(product_id.encode("utf-8")).hexdigest()


def _catalog_taste_sha256s(catalog: Any) -> Tuple[Tuple[str, str], ...]:
    cards: Sequence[Any] = tuple(getattr(catalog, "cards", ()))
    pairs = []
    for card in cards:
        inventor_id = getattr(card, "inventor_id", None)
        root = getattr(card, "root", None)
        if not isinstance(inventor_id, str) or root is None:
            raise ContractError("pending Wish catalog card is malformed")
        pairs.append((inventor_id, load_taste(Path(root)).sha256))
    return tuple(sorted(pairs))


def _read_exact_file(
    directory_descriptor: int,
    name: str,
    *,
    label: str,
    maximum: int = MAX_PENDING_WISH_BYTES,
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
        if not stat.S_ISREG(opened.st_mode) or (
            opened.st_dev,
            opened.st_ino,
        ) != (expected.st_dev, expected.st_ino):
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
    """Publish fully-fsynced immutable bytes without exposing partial finals."""

    temporary_name = ".pending-%s.tmp" % secrets.token_hex(16)
    if not _write_private_exclusive(
        staging_descriptor,
        temporary_name,
        source,
        label="%s staging file" % label,
    ):  # pragma: no cover - a 128-bit random collision
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
        except FileNotFoundError:  # pragma: no cover
            pass
        except OSError as exc:
            if linked:
                raise WorkshopError("cannot clean %s staging file" % label) from exc


@dataclass(frozen=True)
class PendingWish:
    """The exact pre-Match input and catalog snapshot for one Wish id."""

    wish: Wish
    publication_policy: PublicationPolicy
    playtest_rounds: int
    catalog_collection: Path
    catalog_sha256: str
    catalog_total: int
    catalog_taste_sha256s: Sequence[Tuple[str, str]]
    # Records written before the full-TASTE snapshot was added are still
    # useful for read-only status and for correlating an already-sealed Manager
    # assignment.  They may never be sent back through Match: their compact
    # catalog digest did not bind the complete creative constitutions.
    catalog_taste_identity_bound: bool = True
    schema_version: int = 1
    kind: str = PENDING_WISH_KIND
    record_sha256: str = field(init=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ContractError("pending Wish schema_version must be 1")
        if self.kind != PENDING_WISH_KIND:
            raise ContractError("pending Wish kind is invalid")
        if not isinstance(self.wish, Wish):
            raise ContractError("pending Wish requires one typed Wish")
        self.wish.assert_valid()
        if not isinstance(self.publication_policy, PublicationPolicy):
            raise ContractError("pending Wish publication policy is not typed")
        if type(self.playtest_rounds) is not int or not 1 <= self.playtest_rounds <= 100:
            raise ContractError("pending Wish playtest_rounds must be from 1 to 100")
        collection = Path(self.catalog_collection)
        if not collection.is_absolute():
            raise ContractError("pending Wish catalog collection must be absolute")
        # The path is an identity recorded before Match.  Existence/currentness
        # is checked separately so an already-saved assignment can outlive a
        # later catalog edit while a still-pending Match cannot.
        object.__setattr__(self, "catalog_collection", collection)
        require_sha256(self.catalog_sha256, "pending Wish catalog_sha256")
        if type(self.catalog_total) is not int or not 1 <= self.catalog_total <= 10_000:
            raise ContractError("pending Wish catalog_total is invalid")
        if type(self.catalog_taste_identity_bound) is not bool:
            raise ContractError("pending Wish catalog Taste binding flag is invalid")
        taste_sha256s = tuple(self.catalog_taste_sha256s)
        if self.catalog_taste_identity_bound:
            if (
                len(taste_sha256s) != self.catalog_total
                or tuple(sorted(taste_sha256s)) != taste_sha256s
                or len({item[0] for item in taste_sha256s}) != len(taste_sha256s)
            ):
                raise ContractError("pending Wish catalog Taste identities are invalid")
            for inventor_id, digest in taste_sha256s:
                if not isinstance(inventor_id, str) or not inventor_id:
                    raise ContractError("pending Wish catalog inventor id is invalid")
                require_sha256(digest, "pending Wish catalog Taste sha256")
        elif taste_sha256s:
            raise ContractError(
                "legacy pending Wish cannot claim unbound catalog Taste identities"
            )
        object.__setattr__(self, "catalog_taste_sha256s", taste_sha256s)
        object.__setattr__(
            self,
            "record_sha256",
            hashlib.sha256(self.object_bytes()).hexdigest(),
        )

    @classmethod
    def create(
        cls,
        wish: Wish,
        publication_policy: PublicationPolicy,
        catalog: Any,
        *,
        playtest_rounds: int,
    ) -> "PendingWish":
        assert_current = getattr(catalog, "assert_current", None)
        if not callable(assert_current):
            raise ContractError("pending Wish requires one typed catalog snapshot")
        assert_current()
        collection = Path(getattr(catalog, "collection", Path()))
        cards: Sequence[Any] = tuple(getattr(catalog, "cards", ()))
        taste_sha256s = _catalog_taste_sha256s(catalog)
        assert_current()
        if _catalog_taste_sha256s(catalog) != taste_sha256s:
            raise ContractError("pending Wish catalog Taste changed during snapshot")
        return cls(
            wish=wish,
            publication_policy=publication_policy,
            playtest_rounds=playtest_rounds,
            catalog_collection=collection,
            catalog_sha256=getattr(catalog, "catalog_sha256", None),
            catalog_total=len(cards),
            catalog_taste_sha256s=taste_sha256s,
        )

    def _identity_dict(self) -> Dict[str, Any]:
        catalog = {
            "collection": str(self.catalog_collection),
            "catalog_sha256": self.catalog_sha256,
            "total": self.catalog_total,
        }
        if self.catalog_taste_identity_bound:
            catalog["taste_sha256s"] = [
                {"inventor_id": inventor_id, "taste_sha256": digest}
                for inventor_id, digest in self.catalog_taste_sha256s
            ]
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "wish": self.wish.to_dict(),
            "publication_policy": self.publication_policy.to_dict(),
            "playtest_rounds": self.playtest_rounds,
            "catalog": catalog,
        }

    def object_bytes(self) -> bytes:
        return _canonical_json(self._identity_dict())

    def to_dict(self) -> Dict[str, Any]:
        payload = self._identity_dict()
        payload["record_sha256"] = self.record_sha256
        return payload

    @classmethod
    def from_object_bytes(
        cls, source: bytes, *, expected_sha256: str
    ) -> "PendingWish":
        require_sha256(expected_sha256, "pending Wish object address")
        if not isinstance(source, bytes) or not 1 <= len(source) <= MAX_PENDING_WISH_BYTES:
            raise ContractError("pending Wish object bytes are empty or too large")
        if hashlib.sha256(source).hexdigest() != expected_sha256:
            raise ContractError("pending Wish object address does not match its bytes")
        try:
            value = json.loads(source.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise ContractError("pending Wish object is not valid UTF-8 JSON") from exc
        payload = _copy_mapping(value, "pending Wish object")
        if set(payload) != {
            "schema_version",
            "kind",
            "wish",
            "publication_policy",
            "playtest_rounds",
            "catalog",
        }:
            raise ContractError("pending Wish object fields are invalid")
        wish_payload = _copy_mapping(payload["wish"], "pending Wish wish")
        if set(wish_payload) != {
            "schema_version",
            "product_id",
            "objective",
            "constraints",
            "context",
        }:
            raise ContractError("pending Wish Wish fields are invalid")
        try:
            wish = Wish(**wish_payload)
        except TypeError as exc:
            raise ContractError("pending Wish Wish is malformed") from exc
        catalog = _copy_mapping(payload["catalog"], "pending Wish catalog")
        current_catalog_fields = {
            "collection",
            "catalog_sha256",
            "total",
            "taste_sha256s",
        }
        legacy_catalog_fields = current_catalog_fields - {"taste_sha256s"}
        if set(catalog) not in (current_catalog_fields, legacy_catalog_fields):
            raise ContractError("pending Wish catalog fields are invalid")
        taste_identity_bound = "taste_sha256s" in catalog
        raw_tastes = catalog.get("taste_sha256s", [])
        if not isinstance(raw_tastes, list):
            raise ContractError("pending Wish catalog Taste identities are malformed")
        taste_sha256s = []
        for item in raw_tastes:
            if not isinstance(item, Mapping) or set(item) != {
                "inventor_id",
                "taste_sha256",
            }:
                raise ContractError(
                    "pending Wish catalog Taste identity is malformed"
                )
            taste_sha256s.append((item["inventor_id"], item["taste_sha256"]))
        record = cls(
            wish=wish,
            publication_policy=PublicationPolicy.from_dict(
                _copy_mapping(
                    payload["publication_policy"],
                    "pending Wish publication policy",
                )
            ),
            playtest_rounds=payload["playtest_rounds"],
            catalog_collection=Path(catalog["collection"]),
            catalog_sha256=catalog["catalog_sha256"],
            catalog_total=catalog["total"],
            catalog_taste_sha256s=tuple(taste_sha256s),
            catalog_taste_identity_bound=taste_identity_bound,
            schema_version=payload["schema_version"],
            kind=payload["kind"],
        )
        if record.record_sha256 != expected_sha256 or record.object_bytes() != source:
            raise ContractError("pending Wish object is not exact canonical bytes")
        return record

    def assert_catalog_current(self, catalog: Any) -> None:
        if not self.catalog_taste_identity_bound:
            raise ContractError(
                "this legacy pending Wish predates the full-TASTE catalog snapshot; "
                "start a new Wish instead of rematching it under changed creative constitutions"
            )
        assert_current = getattr(catalog, "assert_current", None)
        if not callable(assert_current):
            raise ContractError("pending Wish requires one typed catalog snapshot")
        assert_current()
        collection = Path(getattr(catalog, "collection", Path())).resolve(strict=True)
        if collection != self.catalog_collection:
            raise ContractError("pending Wish belongs to a different catalog root")
        if getattr(catalog, "catalog_sha256", None) != self.catalog_sha256:
            raise ContractError("pending Wish catalog identity changed before Match")
        if len(tuple(getattr(catalog, "cards", ()))) != self.catalog_total:
            raise ContractError("pending Wish catalog membership changed before Match")
        current_tastes = _catalog_taste_sha256s(catalog)
        catalog.assert_current()
        if (
            current_tastes != self.catalog_taste_sha256s
            or _catalog_taste_sha256s(catalog) != current_tastes
        ):
            raise ContractError("pending Wish full Taste changed before Match")

    def with_publication_policy(self, policy: PublicationPolicy) -> "PendingWish":
        if not isinstance(policy, PublicationPolicy):
            raise ContractError("pending Wish publication policy is not typed")
        return PendingWish(
            wish=self.wish,
            publication_policy=policy,
            playtest_rounds=self.playtest_rounds,
            catalog_collection=self.catalog_collection,
            catalog_sha256=self.catalog_sha256,
            catalog_total=self.catalog_total,
            catalog_taste_sha256s=self.catalog_taste_sha256s,
            catalog_taste_identity_bound=self.catalog_taste_identity_bound,
        )


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


class PendingWishStore:
    """Secure filesystem store rooted in one exact inventor collection."""

    def __init__(self, catalog_collection: Path) -> None:
        requested = Path(catalog_collection)
        if not requested.is_absolute() or requested.is_symlink():
            raise WorkshopError("Manager pending Wish catalog must be an absolute regular directory")
        try:
            resolved = requested.resolve(strict=True)
        except OSError as exc:
            raise WorkshopError("cannot resolve Manager pending Wish catalog") from exc
        if resolved != requested or not resolved.is_dir():
            raise WorkshopError("Manager pending Wish catalog must be an absolute regular directory")
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
            raise WorkshopError("cannot inspect Manager pending Wish catalog") from exc
        if not stat.S_ISDIR(expected.st_mode) or stat.S_ISLNK(expected.st_mode):
            raise WorkshopError("Manager pending Wish catalog must be a regular directory")
        try:
            collection = os.open(str(self.collection), _DIRECTORY_FLAGS)
        except OSError as exc:
            raise WorkshopError("cannot safely open Manager pending Wish catalog") from exc
        descriptors = [collection]
        try:
            opened = os.fstat(collection)
            if (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino):
                raise WorkshopError("Manager pending Wish catalog changed while opening")
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
                label="Manager pending Wish storage",
                create=create,
            )
            descriptors.append(store)
            objects = self._open_child(
                store,
                _OBJECT_DIRECTORY,
                label="Manager pending Wish object storage",
                create=create,
            )
            descriptors.append(objects)
            indexes = self._open_child(
                store,
                _INDEX_DIRECTORY,
                label="Manager pending Wish index storage",
                create=create,
            )
            descriptors.append(indexes)
            locks = self._open_child(
                store,
                _LOCK_DIRECTORY,
                label="Manager pending Wish lock storage",
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
                raise WorkshopError("Manager pending Wish catalog changed during access")
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    @staticmethod
    def _index_bytes(product_id: str, record_sha256: str) -> bytes:
        require_sha256(record_sha256, "pending Wish record_sha256")
        return _canonical_json(
            {
                "schema_version": 1,
                "kind": PENDING_WISH_INDEX_KIND,
                "product_id": product_id,
                "record_sha256": record_sha256,
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
            raise WorkshopError("Manager pending Wish index is missing")
        source = _read_exact_file(indexes, name, label="Manager pending Wish index")
        try:
            value = json.loads(source.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise WorkshopError("Manager pending Wish index is not valid UTF-8 JSON") from exc
        payload = _copy_mapping(value, "Manager pending Wish index")
        if set(payload) != {
            "schema_version",
            "kind",
            "product_id",
            "record_sha256",
        }:
            raise WorkshopError("Manager pending Wish index fields are invalid")
        if payload["schema_version"] != 1 or payload["kind"] != PENDING_WISH_INDEX_KIND:
            raise WorkshopError("Manager pending Wish index identity is invalid")
        if payload["product_id"] != product_id:
            raise WorkshopError("Manager pending Wish id hash collision detected")
        try:
            require_sha256(payload["record_sha256"], "pending Wish record_sha256")
        except ContractError as exc:
            raise WorkshopError(str(exc)) from exc
        if source != cls._index_bytes(product_id, payload["record_sha256"]):
            raise WorkshopError("Manager pending Wish index is not exact canonical bytes")
        return payload["record_sha256"]

    @staticmethod
    def _read_object(objects: int, record_sha256: str) -> PendingWish:
        source = _read_exact_file(
            objects,
            record_sha256 + ".json",
            label="Manager pending Wish object",
        )
        try:
            return PendingWish.from_object_bytes(
                source, expected_sha256=record_sha256
            )
        except ContractError as exc:
            raise WorkshopError(str(exc)) from exc

    @classmethod
    def _validated_indexes(cls, indexes: int) -> Dict[str, str]:
        names = tuple(sorted(os.listdir(indexes)))
        if len(names) > MAX_PENDING_WISHES:
            raise WorkshopError("Manager pending Wish index exceeds its safe limit")
        records: Dict[str, str] = {}
        for name in names:
            if (
                not name.endswith(".json")
                or len(name) != 64 + len(".json")
                or any(character not in "0123456789abcdef" for character in name[:64])
            ):
                raise WorkshopError("Manager pending Wish index filename is invalid")
            source = _read_exact_file(
                indexes,
                name,
                label="Manager pending Wish index",
            )
            try:
                payload = json.loads(source.decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as exc:
                raise WorkshopError(
                    "Manager pending Wish index is not valid UTF-8 JSON"
                ) from exc
            if not isinstance(payload, Mapping) or not isinstance(
                payload.get("product_id"), str
            ):
                raise WorkshopError("Manager pending Wish index is malformed")
            product_id = payload["product_id"]
            if name != _product_key(product_id) + ".json":
                raise WorkshopError("Manager pending Wish id hash collision detected")
            if product_id in records:
                raise WorkshopError("duplicate Manager pending Wish id detected")
            record_sha256 = cls._read_index(
                indexes, product_id, allow_missing=False
            )
            records[product_id] = record_sha256
        return records

    @staticmethod
    def _save_object(objects: int, record: PendingWish) -> None:
        name = record.record_sha256 + ".json"
        if _write_atomic_exclusive(
            objects,
            objects,
            name,
            record.object_bytes(),
            label="Manager pending Wish object",
        ):
            return
        existing = _read_exact_file(
            objects, name, label="Manager pending Wish object"
        )
        if existing != record.object_bytes():
            raise WorkshopError("Manager pending Wish content-address collision detected")

    def save(self, record: PendingWish) -> Path:
        if not isinstance(record, PendingWish):
            raise ContractError("Manager pending Wish store requires a typed record")
        if record.catalog_collection != self.collection:
            raise ContractError("Manager pending Wish belongs to a different catalog root")
        with self._layout(create=True) as layout:
            existing_indexes = self._validated_indexes(layout.indexes)
            current_sha256 = existing_indexes.get(record.wish.product_id)
            if (
                current_sha256 is not None
                and current_sha256 != record.record_sha256
            ):
                raise WorkshopError(
                    "this Wish id is already bound to a different pending record"
                )
            self._save_object(layout.objects, record)
            name = _product_key(record.wish.product_id) + ".json"
            source = self._index_bytes(record.wish.product_id, record.record_sha256)
            if not _write_atomic_exclusive(
                layout.objects,
                layout.indexes,
                name,
                source,
                label="Manager pending Wish index",
            ):
                # Always reread the final pointer.  Even an index that existed
                # at the start may have been replaced before this link attempt.
                current_sha256 = self._read_index(
                    layout.indexes, record.wish.product_id, allow_missing=False
                )
                if current_sha256 != record.record_sha256:
                    raise WorkshopError(
                        "this Wish id is already bound to a different pending record"
                    )
        return self.path / _INDEX_DIRECTORY / name

    def load(self, product_id: str, *, allow_missing: bool = False) -> Optional[PendingWish]:
        _product_key(product_id)
        try:
            with self._layout(create=False) as layout:
                snapshot = _BATCH_INDEX_SNAPSHOTS.get().get(self.collection)
                observed = os.fstat(layout.indexes)
                identity = (
                    observed.st_dev,
                    observed.st_ino,
                    observed.st_mtime_ns,
                    observed.st_ctime_ns,
                )
                if snapshot is not None:
                    if snapshot[0] != identity:
                        raise WorkshopError(
                            "Manager pending Wish index changed during batch status"
                        )
                    indexes = snapshot[1]
                else:
                    indexes = self._validated_indexes(layout.indexes)
                record_sha256 = indexes.get(product_id)
                if record_sha256 is None:
                    if allow_missing:
                        return None
                    raise WorkshopError("Manager pending Wish index is missing")
                if self._read_index(
                    layout.indexes, product_id, allow_missing=False
                ) != record_sha256:
                    raise WorkshopError("Manager pending Wish index changed during load")
                record = self._read_object(layout.objects, record_sha256)
        except _MissingStore:
            if allow_missing:
                return None
            raise WorkshopError("this Wish has no saved Manager pending record")
        if record.wish.product_id != product_id:
            raise WorkshopError("Manager pending Wish object belongs to another Wish")
        return record

    @contextmanager
    def validated_batch_reads(self) -> Iterator[None]:
        """Validate the global index once for one bounded, read-only batch view."""

        with self._layout(create=False) as layout:
            before = os.fstat(layout.indexes)
            identity = (
                before.st_dev,
                before.st_ino,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            records = self._validated_indexes(layout.indexes)
            current = dict(_BATCH_INDEX_SNAPSHOTS.get())
            current[self.collection] = (identity, dict(records))
            token = _BATCH_INDEX_SNAPSHOTS.set(current)
            try:
                yield
                if self._validated_indexes(layout.indexes) != records:
                    raise WorkshopError(
                        "Manager pending Wish index changed during batch status"
                    )
                after = os.fstat(layout.indexes)
                if (
                    after.st_dev,
                    after.st_ino,
                    after.st_mtime_ns,
                    after.st_ctime_ns,
                ) != identity:
                    raise WorkshopError(
                        "Manager pending Wish index changed during batch status"
                    )
            finally:
                _BATCH_INDEX_SNAPSHOTS.reset(token)

    def _batch_load(
        self, product_id: str, *, allow_missing: bool = False
    ) -> Optional[PendingWish]:
        """Direct exact lookup for a caller holding the per-Wish batch lock."""

        _product_key(product_id)
        try:
            with self._layout(create=False) as layout:
                record_sha256 = self._read_index(
                    layout.indexes, product_id, allow_missing=True
                )
                if record_sha256 is None:
                    if allow_missing:
                        return None
                    raise WorkshopError("Manager pending Wish index is missing")
                record = self._read_object(layout.objects, record_sha256)
        except _MissingStore:
            if allow_missing:
                return None
            raise WorkshopError("this Wish has no saved Manager pending record")
        if record.wish.product_id != product_id:
            raise WorkshopError("Manager pending Wish object belongs to another Wish")
        return record

    def _batch_save(self, record: PendingWish) -> Path:
        """O(1) exact save for a caller holding the per-Wish batch lock."""

        if not isinstance(record, PendingWish):
            raise ContractError("Manager pending Wish store requires a typed record")
        if record.catalog_collection != self.collection:
            raise ContractError("Manager pending Wish belongs to a different catalog root")
        with self._layout(create=True) as layout:
            current_sha256 = self._read_index(
                layout.indexes, record.wish.product_id, allow_missing=True
            )
            if current_sha256 is not None and current_sha256 != record.record_sha256:
                raise WorkshopError(
                    "this Wish id is already bound to a different pending record"
                )
            self._save_object(layout.objects, record)
            name = _product_key(record.wish.product_id) + ".json"
            source = self._index_bytes(record.wish.product_id, record.record_sha256)
            if not _write_atomic_exclusive(
                layout.objects,
                layout.indexes,
                name,
                source,
                label="Manager pending Wish index",
            ):
                observed = self._read_index(
                    layout.indexes, record.wish.product_id, allow_missing=False
                )
                if observed != record.record_sha256:
                    raise WorkshopError(
                        "this Wish id is already bound to a different pending record"
                    )
        return self.path / _INDEX_DIRECTORY / name

    def list(self) -> Tuple[PendingWish, ...]:
        try:
            with self._layout(create=False) as layout:
                records = []
                for product_id, record_sha256 in self._validated_indexes(
                    layout.indexes
                ).items():
                    record = self._read_object(layout.objects, record_sha256)
                    if record.wish.product_id != product_id:
                        raise WorkshopError(
                            "Manager pending Wish object belongs to another Wish"
                        )
                    records.append(record)
                return tuple(records)
        except _MissingStore:
            return ()

    def replace(self, expected: PendingWish, replacement: PendingWish) -> Path:
        """Atomically repoint one Wish id to new immutable content."""

        if not isinstance(expected, PendingWish) or not isinstance(
            replacement, PendingWish
        ):
            raise ContractError("pending Wish replacement requires typed records")
        if (
            expected.wish.product_id != replacement.wish.product_id
            or replacement.catalog_collection != self.collection
        ):
            raise ContractError("pending Wish replacement changed its identity")
        with self._layout(create=False) as layout:
            current = self._validated_indexes(layout.indexes).get(
                expected.wish.product_id
            )
            if current != expected.record_sha256:
                raise WorkshopError("Manager pending Wish changed before replacement")
            self._save_object(layout.objects, replacement)
            name = _product_key(expected.wish.product_id) + ".json"
            temporary_name = ".%s-%s.tmp" % (name, secrets.token_hex(8))
            source = self._index_bytes(
                replacement.wish.product_id, replacement.record_sha256
            )
            created = _write_private_exclusive(
                layout.objects,
                temporary_name,
                source,
                label="Manager pending Wish replacement index",
            )
            if not created:  # pragma: no cover - random name collision
                raise WorkshopError("cannot reserve Manager pending Wish replacement")
            try:
                # Recheck under the caller's per-Wish lock immediately before the
                # atomic pointer swap.  A non-cooperating writer still fails closed.
                if self._read_index(
                    layout.indexes,
                    expected.wish.product_id,
                    allow_missing=False,
                ) != expected.record_sha256:
                    raise WorkshopError("Manager pending Wish changed before replacement")
                os.replace(
                    temporary_name,
                    name,
                    src_dir_fd=layout.objects,
                    dst_dir_fd=layout.indexes,
                )
                os.fsync(layout.indexes)
            except OSError as exc:
                raise WorkshopError("cannot atomically replace Manager pending Wish") from exc
            finally:
                try:
                    os.unlink(temporary_name, dir_fd=layout.objects)
                except FileNotFoundError:
                    pass
        return self.path / _INDEX_DIRECTORY / name

    @contextmanager
    def lock(self, product_id: str) -> Iterator[None]:
        """Serialize Match and assignment sealing for one exact Wish id."""

        name = _product_key(product_id) + ".lock"
        with self._layout(create=True) as layout:
            flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
            try:
                descriptor = os.open(name, flags, 0o600, dir_fd=layout.locks)
            except OSError as exc:
                raise WorkshopError("cannot open Manager pending Wish lock") from exc
            try:
                opened = os.fstat(descriptor)
                if not stat.S_ISREG(opened.st_mode):
                    raise WorkshopError("Manager pending Wish lock must be a regular file")
                os.fchmod(descriptor, 0o600)
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                current = os.stat(name, dir_fd=layout.locks, follow_symlinks=False)
                if (
                    not stat.S_ISREG(current.st_mode)
                    or (current.st_dev, current.st_ino)
                    != (opened.st_dev, opened.st_ino)
                ):
                    raise WorkshopError("Manager pending Wish lock changed while opening")
                yield
            finally:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
                finally:
                    os.close(descriptor)
