"""Wish-bound customer-reference staging for the shared little-worlds lane.

This is Workshop infrastructure, not Inventor contribution code.  The vault
keeps reference and consent bytes in a mode-private content-addressed store and
returns them only to a caller that supplies the exact registered Wish,
personalization contract, reviewer, and provider identity.  Serializable
receipts and attestations contain hashes and bounded scope metadata, never raw
private bytes.

This local backend cannot isolate bytes from Inventor contribution code running
as the same OS user. It therefore requires an explicit development-trust opt
in. Production needs an authenticated service or OS sandbox whose authority is
never passed to the Inventor child. The HMAC authenticates only what this local
Workshop process admitted; it does not authenticate a person, prove that a
rights claim is legally sufficient, or turn model opinion into likeness proof.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import stat
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Protocol, Sequence, Tuple

from .artifacts import assert_packable_content
from .errors import ContractError, StateConflict
from .make import Wish
from .models import require_sha256, require_utc_timestamp, utc_now
from .store import InventorStore


MAX_WORLD_REFERENCE_BYTES = 16 * 1024 * 1024
MAX_WORLD_CONSENT_BYTES = 256 * 1024
MAX_WORLD_RECORD_BYTES = 64 * 1024

SUPPORTED_WORLD_MEDIA_TYPES = frozenset(
    ("image/jpeg", "image/png", "image/webp")
)
SUPPORTED_WORLD_SUBJECT_KINDS = frozenset(
    (
        "customer-self",
        "customer-owned-subject",
        "customer-original-work",
    )
)
UNSUPPORTED_WORLD_SUBJECT_KINDS = frozenset(
    (
        "celebrity",
        "franchise",
        "public-figure",
        "third-party-likeness",
    )
)
SUPPORTED_WORLD_CONSENT_METHODS = frozenset(
    (
        "customer-supplied-attestation-record",
    )
)

LOCAL_STORAGE_SECURITY_BOUNDARY = "same-user-local-development"
CONSENT_CLAIM_BOUNDARY = "customer-supplied-not-independently-authenticated"

_SAFE_ID = re.compile(r"[a-z][a-z0-9-]{1,62}\Z")
_SAFE_ACTOR = re.compile(r"[a-z][a-z0-9._-]{1,127}\Z")
_HMAC_ALGORITHM = "hmac-sha256"
_KEY_BYTES = 32


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("world reference metadata must be finite JSON") from exc


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _wish_sha256(wish: Wish) -> str:
    if not isinstance(wish, Wish):
        raise ContractError("world reference access requires a Wish")
    wish.assert_valid()
    return _canonical_sha256(wish.to_dict())


def _bounded_text(value: Any, label: str, maximum: int) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError(
            "%s must be non-empty, trimmed, control-free text of at most %d characters"
            % (label, maximum)
        )
    return value


def _safe_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ID.fullmatch(value) is None:
        raise ContractError("%s must be a canonical lowercase id" % label)
    return value


def _safe_actor(value: Any, label: str) -> str:
    if not isinstance(value, str) or _SAFE_ACTOR.fullmatch(value) is None:
        raise ContractError("%s must be a canonical reviewer/provider id" % label)
    return value


def _feature_list(values: Any, label: str, *, required: bool) -> Tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise ContractError("%s must be a sequence" % label)
    selected = tuple(_bounded_text(value, label, 1_000) for value in values)
    folded = tuple(value.casefold() for value in selected)
    if (required and not selected) or len(folded) != len(set(folded)):
        raise ContractError("%s must contain unique%s features" % (
            label,
            " non-empty" if required else "",
        ))
    if len(selected) > 64:
        raise ContractError("%s may contain at most 64 features" % label)
    return selected


def _validate_media_bytes(content: bytes, media_type: str) -> None:
    if media_type == "image/jpeg":
        valid = (
            len(content) >= 4
            and content.startswith(b"\xff\xd8\xff")
            and content.endswith(b"\xff\xd9")
        )
    elif media_type == "image/png":
        valid = content.startswith(b"\x89PNG\r\n\x1a\n") and len(content) >= 12
    elif media_type == "image/webp":
        valid = (
            len(content) >= 12
            and content[:4] == b"RIFF"
            and content[8:12] == b"WEBP"
            and int.from_bytes(content[4:8], "little") + 8 == len(content)
        )
    else:
        valid = False
    if not valid:
        raise ContractError(
            "private world reference bytes do not match the declared supported media type"
        )


def _read_bounded_regular(
    path: Path,
    maximum: int,
    label: str,
    *,
    expected_sha256: Optional[str] = None,
    expected_size: Optional[int] = None,
    private: bool = False,
) -> bytes:
    """Read one stable regular file without following its final symlink."""

    requested = Path(path)
    try:
        before = requested.lstat()
    except OSError as exc:
        raise ContractError("%s is missing or unreadable" % label) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ContractError("%s must be a regular non-symlink file" % label)
    if private and stat.S_IMODE(before.st_mode) != 0o600:
        raise ContractError("%s must have private 0600 permissions" % label)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(str(requested), flags)
    except OSError as exc:
        raise ContractError("%s changed while opening" % label) from exc
    try:
        opened = os.fstat(descriptor)
        identity = (opened.st_dev, opened.st_ino)
        if identity != (before.st_dev, before.st_ino) or not stat.S_ISREG(opened.st_mode):
            raise ContractError("%s changed while opening" % label)
        if private and stat.S_IMODE(opened.st_mode) != 0o600:
            raise ContractError("%s must have private 0600 permissions" % label)
        if opened.st_size < 1 or opened.st_size > maximum:
            raise ContractError("%s must contain 1..%d bytes" % (label, maximum))
        chunks = []
        remaining = maximum + 1
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        final = requested.lstat()
    except OSError as exc:
        raise ContractError("%s changed while reading" % label) from exc
    if (
        len(content) < 1
        or len(content) > maximum
        or (after.st_dev, after.st_ino) != identity
        or (final.st_dev, final.st_ino) != identity
        or stat.S_ISLNK(final.st_mode)
        or (private and stat.S_IMODE(final.st_mode) != 0o600)
        or after.st_size != len(content)
        or after.st_size != opened.st_size
        or after.st_mtime_ns != opened.st_mtime_ns
        or after.st_ctime_ns != opened.st_ctime_ns
    ):
        raise ContractError("%s changed while reading" % label)
    digest = hashlib.sha256(content).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ContractError("%s content hash changed" % label)
    if expected_size is not None and len(content) != expected_size:
        raise ContractError("%s byte length changed" % label)
    return content


def _directory_identity(path: Path, label: str) -> Tuple[int, int]:
    try:
        observed = path.lstat()
    except OSError as exc:
        raise ContractError("%s is missing" % label) from exc
    if stat.S_ISLNK(observed.st_mode) or not stat.S_ISDIR(observed.st_mode):
        raise ContractError("%s must be a regular non-symlink directory" % label)
    return observed.st_dev, observed.st_ino


def _ensure_private_directory(path: Path, label: str) -> None:
    if path.exists() or path.is_symlink():
        _directory_identity(path, label)
    else:
        try:
            path.mkdir(mode=0o700)
        except OSError as exc:
            raise ContractError("cannot create %s" % label) from exc
        _directory_identity(path, label)
    try:
        os.chmod(str(path), 0o700)
    except OSError as exc:
        raise ContractError("cannot secure %s" % label) from exc


def _atomic_private_write(path: Path, content: bytes, label: str) -> bool:
    """Publish immutable bytes without replacing an existing target."""

    _directory_identity(path.parent, "%s directory" % label)
    temporary = path.parent / (".%s.%s.tmp" % (path.name, secrets.token_hex(8)))
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = None
    try:
        descriptor = os.open(str(temporary), flags, 0o600)
        os.fchmod(descriptor, 0o600)
        view = memoryview(content)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short private write")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        try:
            os.link(str(temporary), str(path), follow_symlinks=False)
            created = True
        except FileExistsError:
            created = False
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return created
    except OSError as exc:
        raise ContractError("cannot seal %s" % label) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


@dataclass(frozen=True)
class WorldReferenceScope:
    """Customer-supplied rights declaration for one private reference."""

    reference_id: str
    subject_kind: str
    subject: str
    rights_basis: str
    allowed_features: Sequence[str]
    excluded_features: Sequence[str]
    reviewer_id: str
    verification_method: str

    def __post_init__(self) -> None:
        _safe_id(self.reference_id, "world reference id")
        if self.subject_kind in UNSUPPORTED_WORLD_SUBJECT_KINDS:
            raise ContractError(
                "celebrity, franchise, public-figure, and third-party likeness "
                "references are unsupported"
            )
        if self.subject_kind not in SUPPORTED_WORLD_SUBJECT_KINDS:
            raise ContractError("world reference subject kind is unsupported")
        _bounded_text(self.subject, "world reference subject", 500)
        basis = _bounded_text(self.rights_basis, "world reference rights basis", 2_000)
        if basis.casefold() in {"pending", "unknown", "assumed", "model opinion"}:
            raise ContractError("world reference rights basis must be explicit")
        allowed = _feature_list(
            self.allowed_features, "world allowed features", required=True
        )
        excluded = _feature_list(
            self.excluded_features, "world excluded features", required=False
        )
        if set(value.casefold() for value in allowed) & set(
            value.casefold() for value in excluded
        ):
            raise ContractError("world consent cannot allow and exclude one feature")
        _safe_actor(self.reviewer_id, "world consent reviewer id")
        if self.verification_method not in SUPPORTED_WORLD_CONSENT_METHODS:
            raise ContractError("world consent verification method is unsupported")
        # These raw-free fields cross the Manager-to-Invent/model boundary and
        # are later eligible for public evidence. Reject credential-shaped text
        # before either boundary; never echo the offending bytes.
        assert_packable_content(
            "world-reference-scope.json",
            _canonical_bytes(
                {
                    "subject": self.subject,
                    "rights_basis": basis,
                    "allowed_features": list(allowed),
                    "excluded_features": list(excluded),
                }
            ),
        )
        object.__setattr__(self, "allowed_features", allowed)
        object.__setattr__(self, "excluded_features", excluded)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reference_id": self.reference_id,
            "subject_kind": self.subject_kind,
            "subject": self.subject,
            "rights_basis": self.rights_basis,
            "allowed_features": list(self.allowed_features),
            "excluded_features": list(self.excluded_features),
            "reviewer_id": self.reviewer_id,
            "verification_method": self.verification_method,
        }


@dataclass(frozen=True)
class WorldReferenceReceipt:
    product_id: str
    wish_sha256: str
    reference_id: str
    record_sha256: str
    content_sha256: str
    content_bytes: int
    consent_sha256: str
    consent_bytes: int
    media_type: str
    subject_kind: str
    reviewer_id: str
    key_id: str

    def __post_init__(self) -> None:
        _bounded_text(self.product_id, "world reference product id", 256)
        _safe_id(self.reference_id, "world reference id")
        for digest, label in (
            (self.wish_sha256, "world reference Wish sha256"),
            (self.record_sha256, "world reference record sha256"),
            (self.content_sha256, "world reference content sha256"),
            (self.consent_sha256, "world reference consent sha256"),
            (self.key_id, "world reference key id"),
        ):
            require_sha256(digest, label)
        if self.media_type not in SUPPORTED_WORLD_MEDIA_TYPES:
            raise ContractError("world reference media type is unsupported")
        if self.subject_kind not in SUPPORTED_WORLD_SUBJECT_KINDS:
            raise ContractError("world reference subject kind is unsupported")
        _safe_actor(self.reviewer_id, "world reference reviewer id")
        if not 1 <= self.content_bytes <= MAX_WORLD_REFERENCE_BYTES:
            raise ContractError("world reference byte count is invalid")
        if not 1 <= self.consent_bytes <= MAX_WORLD_CONSENT_BYTES:
            raise ContractError("world consent byte count is invalid")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 2,
            "product_id": self.product_id,
            "wish_sha256": self.wish_sha256,
            "reference_id": self.reference_id,
            "record_sha256": self.record_sha256,
            "content_sha256": self.content_sha256,
            "content_bytes": self.content_bytes,
            "consent_sha256": self.consent_sha256,
            "consent_bytes": self.consent_bytes,
            "media_type": self.media_type,
            "subject_kind": self.subject_kind,
            "reviewer_id": self.reviewer_id,
            "attestation_key_id": self.key_id,
            "raw_private_bytes_included": False,
            "storage_security_boundary": LOCAL_STORAGE_SECURITY_BOUNDARY,
            "consent_claim_boundary": CONSENT_CLAIM_BOUNDARY,
        }


@dataclass(frozen=True)
class WorldReferenceDescriptor:
    """Raw-free exact scope input authenticated by the Manager-side service.

    The descriptor binds the identity fields duplicated by the public receipt.
    The service's ``verify_admission`` implementation remains responsible for
    authenticating the complete scope and exact admission record before the
    Manager constructs ``WorldInventInputs``.
    """

    scope: WorldReferenceScope
    receipt: WorldReferenceReceipt
    admission: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.scope, WorldReferenceScope) or not isinstance(
            self.receipt, WorldReferenceReceipt
        ):
            raise ContractError("world reference descriptor is malformed")
        if (
            self.scope.reference_id != self.receipt.reference_id
            or self.scope.subject_kind != self.receipt.subject_kind
            or self.scope.reviewer_id != self.receipt.reviewer_id
        ):
            raise ContractError(
                "world reference descriptor scope identity differs from its receipt"
            )
        copied = json.loads(_canonical_bytes(self.admission))
        if not isinstance(copied, dict):
            raise ContractError("world reference admission must be an object")
        object.__setattr__(self, "admission", copied)

    def invent_contract(self) -> Dict[str, Any]:
        """Return the exact existing little-worlds reference contract shape."""

        return {
            "reference_id": self.scope.reference_id,
            "subject": self.scope.subject,
            "consent_or_rights_basis": self.scope.rights_basis,
            "allowed_features": list(self.scope.allowed_features),
            "excluded_features": list(self.scope.excluded_features),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "scope": self.scope.to_dict(),
            "receipt": self.receipt.to_dict(),
            "admission": json.loads(_canonical_bytes(self.admission)),
        }


@dataclass(frozen=True)
class AuthorizedWorldReference:
    """Private provider input; repr/equality never expose or compare raw bytes."""

    scope: WorldReferenceScope
    product_id: str
    wish_sha256: str
    media_type: str
    content_sha256: str
    consent_sha256: str
    record_sha256: str
    authorization: Mapping[str, Any]
    reference_bytes: bytes = field(repr=False, compare=False)
    consent_bytes: bytes = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.scope, WorldReferenceScope):
            raise ContractError("authorized world reference requires a scope")
        for value, label in (
            (self.wish_sha256, "authorized Wish sha256"),
            (self.content_sha256, "authorized content sha256"),
            (self.consent_sha256, "authorized consent sha256"),
            (self.record_sha256, "authorized record sha256"),
        ):
            require_sha256(value, label)
        if hashlib.sha256(self.reference_bytes).hexdigest() != self.content_sha256:
            raise ContractError("authorized reference bytes differ from their digest")
        if hashlib.sha256(self.consent_bytes).hexdigest() != self.consent_sha256:
            raise ContractError("authorized consent bytes differ from their digest")
        copied = json.loads(_canonical_bytes(self.authorization))
        if not isinstance(copied, dict):
            raise ContractError("world authorization must be an object")
        object.__setattr__(self, "authorization", copied)

    def public_attestation(self) -> Dict[str, Any]:
        """Return replayable, raw-free authorization provenance."""

        return json.loads(_canonical_bytes(self.authorization))


class WorldReferenceService(Protocol):
    """Manager-side seam a production isolated service must implement."""

    def descriptors(self, wish: Wish) -> Tuple[WorldReferenceDescriptor, ...]:
        ...

    def verify_admission(
        self,
        admission: Mapping[str, Any],
        wish: Wish,
        *,
        expected_reference_id: str,
    ) -> None:
        ...

    def authorized_provider_inputs(
        self,
        wish: Wish,
        personalization_map: Mapping[str, Any],
        *,
        expected_reviewer_id: str,
        provider_id: str,
    ) -> Tuple[AuthorizedWorldReference, ...]:
        ...

    def verify_authorization(
        self,
        authorization: Mapping[str, Any],
        wish: Wish,
        personalization_map: Mapping[str, Any],
        *,
        expected_reviewer_id: str,
        provider_id: str,
    ) -> None:
        ...


class WorldReferenceVault:
    """Same-user local backend for exact little-world reference inputs."""

    def __init__(
        self,
        inventor_root: Path,
        *,
        create: bool = False,
        trust_same_user_processes: bool = False,
    ) -> None:
        if trust_same_user_processes is not True:
            raise ContractError(
                "the local world-reference vault cannot isolate raw bytes from "
                "Inventor code running as the same OS user; use an authenticated "
                "service/OS sandbox or explicitly opt into local development trust"
            )
        requested = Path(inventor_root)
        identity = _directory_identity(requested, "Inventor root")
        try:
            resolved = requested.resolve(strict=True)
        except OSError as exc:
            raise ContractError("cannot resolve Inventor root") from exc
        if _directory_identity(resolved, "Inventor root") != identity:
            raise ContractError("Inventor root changed while opening the vault")
        self.inventor_root = resolved
        self.runtime_root = resolved / ".workshop"
        self.private_root = self.runtime_root / "private-inputs"
        self.root = self.private_root / "world-references-v1"
        self.blobs_root = self.root / "blobs"
        self.records_root = self.root / "records"
        self.key_path = self.root / "attestation.secret"
        if create:
            for path, label in (
                (self.runtime_root, "Workshop runtime"),
                (self.private_root, "private input root"),
                (self.root, "world reference vault"),
                (self.blobs_root, "world reference blob store"),
                (self.records_root, "world reference record store"),
            ):
                _ensure_private_directory(path, label)
            self._key(create=True)
        else:
            for path, label in (
                (self.runtime_root, "Workshop runtime"),
                (self.private_root, "private input root"),
                (self.root, "world reference vault"),
                (self.blobs_root, "world reference blob store"),
                (self.records_root, "world reference record store"),
            ):
                _directory_identity(path, label)
            self._key(create=False)
        self._identities = {
            path: _directory_identity(path, label)
            for path, label in (
                (self.inventor_root, "Inventor root"),
                (self.runtime_root, "Workshop runtime"),
                (self.private_root, "private input root"),
                (self.root, "world reference vault"),
                (self.blobs_root, "world reference blob store"),
                (self.records_root, "world reference record store"),
            )
        }

    @classmethod
    def exists(cls, inventor_root: Path) -> bool:
        candidate = Path(inventor_root) / ".workshop" / "private-inputs" / "world-references-v1"
        return candidate.is_dir() and not candidate.is_symlink()

    def _assert_current(self) -> None:
        for path, expected in self._identities.items():
            if _directory_identity(path, "world reference vault path") != expected:
                raise ContractError("world reference vault path changed while in use")
            if path != self.inventor_root and stat.S_IMODE(path.lstat().st_mode) != 0o700:
                raise ContractError(
                    "world reference vault directories must have private 0700 permissions"
                )

    def _has_persisted_material(self) -> bool:
        for root in (self.blobs_root, self.records_root):
            if not root.exists():
                continue
            for directory, names, files in os.walk(str(root), followlinks=False):
                selected = Path(directory)
                _directory_identity(selected, "world reference vault directory")
                for name in names:
                    child = selected / name
                    if child.is_symlink():
                        raise ContractError("world reference vault contains a symlink")
                if files:
                    return True
        return False

    def _key(self, *, create: bool) -> bytes:
        if not self.key_path.exists() and not self.key_path.is_symlink():
            if not create:
                raise ContractError("world reference attestation key is missing")
            if self._has_persisted_material():
                raise ContractError(
                    "world reference attestation key is missing from a non-empty vault"
                )
            generated = secrets.token_bytes(_KEY_BYTES)
            _atomic_private_write(
                self.key_path, generated, "world reference attestation key"
            )
        key = _read_bounded_regular(
            self.key_path,
            _KEY_BYTES,
            "world reference attestation key",
            expected_size=_KEY_BYTES,
            private=True,
        )
        if len(key) != _KEY_BYTES:
            raise ContractError("world reference attestation key has an invalid length")
        return key

    @property
    def key_id(self) -> str:
        return hashlib.sha256(self._key(create=False)).hexdigest()

    def _registered_product(self, wish: Wish) -> Mapping[str, Any]:
        self._assert_current()
        database = self.runtime_root / "workshop.sqlite3"
        if database.is_symlink() or not database.is_file():
            raise ContractError(
                "world references require an exact registered Workshop Wish"
            )
        store = InventorStore(database)
        try:
            product = store.get_product(wish.product_id)
        except KeyError as exc:
            raise ContractError(
                "world references require an exact registered Workshop Wish"
            ) from exc
        if not store.verify_event_chain(wish.product_id):
            raise ContractError("registered Wish event chain is not trustworthy")
        metadata = product.get("metadata")
        if (
            not isinstance(metadata, Mapping)
            or metadata.get("wish") != wish.to_dict()
            or metadata.get("lane") != "little-worlds"
        ):
            raise ContractError(
                "world reference access differs from the exact registered little-worlds Wish"
            )
        return product

    def _sign(self, payload: Mapping[str, Any]) -> Dict[str, str]:
        key = self._key(create=False)
        return {
            "algorithm": _HMAC_ALGORITHM,
            "key_id": hashlib.sha256(key).hexdigest(),
            "signature": hmac.new(key, _canonical_bytes(payload), hashlib.sha256).hexdigest(),
        }

    def _verify_authentication(
        self, payload: Mapping[str, Any], authentication: Any
    ) -> None:
        if not isinstance(authentication, Mapping) or set(authentication) != {
            "algorithm",
            "key_id",
            "signature",
        }:
            raise ContractError("world reference authentication is malformed")
        key = self._key(create=False)
        expected_key_id = hashlib.sha256(key).hexdigest()
        signature = authentication.get("signature")
        if (
            authentication.get("algorithm") != _HMAC_ALGORITHM
            or authentication.get("key_id") != expected_key_id
            or not isinstance(signature, str)
            or re.fullmatch(r"[0-9a-f]{64}", signature) is None
            or not hmac.compare_digest(
                signature,
                hmac.new(key, _canonical_bytes(payload), hashlib.sha256).hexdigest(),
            )
        ):
            raise ContractError("world reference authentication did not verify")

    def _wish_records_root(self, wish_sha256: str, *, create: bool) -> Path:
        require_sha256(wish_sha256, "world reference Wish sha256")
        selected = self.records_root / wish_sha256
        if create:
            _ensure_private_directory(selected, "Wish reference records")
        else:
            _directory_identity(selected, "Wish reference records")
        return selected

    def _blob(self, digest: str) -> Path:
        require_sha256(digest, "private blob sha256")
        return self.blobs_root / digest

    def _store_blob(self, content: bytes, label: str) -> str:
        digest = hashlib.sha256(content).hexdigest()
        path = self._blob(digest)
        created = _atomic_private_write(path, content, label)
        if not created:
            _read_bounded_regular(
                path,
                max(MAX_WORLD_REFERENCE_BYTES, MAX_WORLD_CONSENT_BYTES),
                label,
                expected_sha256=digest,
                expected_size=len(content),
                private=True,
            )
        return digest

    def _record_path(self, wish_sha256: str, reference_id: str, *, create: bool) -> Path:
        _safe_id(reference_id, "world reference id")
        return self._wish_records_root(wish_sha256, create=create) / (
            reference_id + ".json"
        )

    def _record_document(self, path: Path) -> Mapping[str, Any]:
        raw = _read_bounded_regular(
            path,
            MAX_WORLD_RECORD_BYTES,
            "world reference record",
            private=True,
        )
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContractError("world reference record is malformed") from exc
        if not isinstance(document, Mapping) or set(document) != {
            "payload",
            "authentication",
        } or not isinstance(document.get("payload"), Mapping):
            raise ContractError("world reference record is malformed")
        self._verify_authentication(document["payload"], document["authentication"])
        return document

    def _decode_record(
        self,
        document: Mapping[str, Any],
        *,
        expected_wish: Optional[Wish] = None,
        expected_reference_id: Optional[str] = None,
    ) -> tuple[Mapping[str, Any], WorldReferenceScope, str]:
        payload = document["payload"]
        if set(payload) != {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "scope",
            "media_type",
            "content_sha256",
            "content_bytes",
            "consent_sha256",
            "consent_bytes",
            "added_at",
            "storage_security_boundary",
            "consent_claim_boundary",
        } or payload.get("schema_version") != 1 or payload.get("kind") != "world-reference":
            raise ContractError("world reference record payload is malformed")
        if (
            payload.get("storage_security_boundary")
            != LOCAL_STORAGE_SECURITY_BOUNDARY
            or payload.get("consent_claim_boundary") != CONSENT_CLAIM_BOUNDARY
        ):
            raise ContractError("world reference trust boundaries are malformed")
        try:
            scope = WorldReferenceScope(**dict(payload["scope"]))
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError("world reference record scope is malformed") from exc
        _bounded_text(payload.get("product_id"), "world reference product id", 256)
        require_sha256(payload.get("wish_sha256"), "world reference Wish sha256")
        require_sha256(payload.get("content_sha256"), "world reference content sha256")
        require_sha256(payload.get("consent_sha256"), "world reference consent sha256")
        if payload.get("media_type") not in SUPPORTED_WORLD_MEDIA_TYPES:
            raise ContractError("world reference media type is unsupported")
        require_utc_timestamp(payload.get("added_at"), "world reference added_at")
        if (
            type(payload.get("content_bytes")) is not int
            or not 1 <= payload["content_bytes"] <= MAX_WORLD_REFERENCE_BYTES
            or type(payload.get("consent_bytes")) is not int
            or not 1 <= payload["consent_bytes"] <= MAX_WORLD_CONSENT_BYTES
        ):
            raise ContractError("world reference record byte counts are invalid")
        if expected_wish is not None and (
            payload["product_id"] != expected_wish.product_id
            or payload["wish_sha256"] != _wish_sha256(expected_wish)
        ):
            raise ContractError("world reference record belongs to another Wish")
        if expected_reference_id is not None and scope.reference_id != expected_reference_id:
            raise ContractError("world reference record id changed")
        return payload, scope, _canonical_sha256(document)

    def _receipt(
        self, document: Mapping[str, Any], *, expected_wish: Optional[Wish] = None
    ) -> WorldReferenceReceipt:
        payload, scope, record_sha256 = self._decode_record(
            document, expected_wish=expected_wish
        )
        _read_bounded_regular(
            self._blob(payload["content_sha256"]),
            MAX_WORLD_REFERENCE_BYTES,
            "private world reference blob",
            expected_sha256=payload["content_sha256"],
            expected_size=payload["content_bytes"],
            private=True,
        )
        _read_bounded_regular(
            self._blob(payload["consent_sha256"]),
            MAX_WORLD_CONSENT_BYTES,
            "private world consent blob",
            expected_sha256=payload["consent_sha256"],
            expected_size=payload["consent_bytes"],
            private=True,
        )
        return WorldReferenceReceipt(
            product_id=payload["product_id"],
            wish_sha256=payload["wish_sha256"],
            reference_id=scope.reference_id,
            record_sha256=record_sha256,
            content_sha256=payload["content_sha256"],
            content_bytes=payload["content_bytes"],
            consent_sha256=payload["consent_sha256"],
            consent_bytes=payload["consent_bytes"],
            media_type=payload["media_type"],
            subject_kind=scope.subject_kind,
            reviewer_id=scope.reviewer_id,
            key_id=document["authentication"]["key_id"],
        )

    def add(
        self,
        wish: Wish,
        *,
        scope: WorldReferenceScope,
        reference_path: Path,
        consent_path: Path,
        media_type: str,
    ) -> WorldReferenceReceipt:
        """Seal one immutable customer attachment and explicit consent record."""

        if not isinstance(scope, WorldReferenceScope):
            raise ContractError("world reference add requires an explicit consent scope")
        if media_type not in SUPPORTED_WORLD_MEDIA_TYPES:
            raise ContractError("world reference media type is unsupported")
        self._registered_product(wish)
        self._assert_current()
        reference = _read_bounded_regular(
            Path(reference_path),
            MAX_WORLD_REFERENCE_BYTES,
            "private world reference",
        )
        consent = _read_bounded_regular(
            Path(consent_path),
            MAX_WORLD_CONSENT_BYTES,
            "private world consent record",
        )
        _validate_media_bytes(reference, media_type)
        content_sha256 = self._store_blob(reference, "private world reference")
        consent_sha256 = self._store_blob(consent, "private world consent record")
        wish_sha256 = _wish_sha256(wish)
        payload = {
            "schema_version": 1,
            "kind": "world-reference",
            "product_id": wish.product_id,
            "wish_sha256": wish_sha256,
            "scope": scope.to_dict(),
            "media_type": media_type,
            "content_sha256": content_sha256,
            "content_bytes": len(reference),
            "consent_sha256": consent_sha256,
            "consent_bytes": len(consent),
            "added_at": utc_now(),
            "storage_security_boundary": LOCAL_STORAGE_SECURITY_BOUNDARY,
            "consent_claim_boundary": CONSENT_CLAIM_BOUNDARY,
        }
        document = {"payload": payload, "authentication": self._sign(payload)}
        path = self._record_path(wish_sha256, scope.reference_id, create=True)
        encoded = _canonical_bytes(document) + b"\n"
        if len(encoded) > MAX_WORLD_RECORD_BYTES:
            raise ContractError("world reference record is too large")
        created = _atomic_private_write(path, encoded, "world reference record")
        persisted = self._record_document(path)
        if not created:
            existing_payload, existing_scope, unused_sha = self._decode_record(
                persisted,
                expected_wish=wish,
                expected_reference_id=scope.reference_id,
            )
            del unused_sha
            immutable = dict(existing_payload)
            immutable.pop("added_at", None)
            expected = dict(payload)
            expected.pop("added_at", None)
            if immutable != expected or existing_scope != scope:
                raise StateConflict(
                    "world reference id is already sealed with different bytes or consent scope"
                )
        self._assert_current()
        return self._receipt(persisted, expected_wish=wish)

    def list(self, wish: Wish) -> Tuple[WorldReferenceReceipt, ...]:
        """List raw-free receipts for one exact registered Wish."""

        self._registered_product(wish)
        root = self._record_path(
            _wish_sha256(wish), "placeholder", create=False
        ).parent
        receipts = []
        try:
            entries = sorted(root.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise ContractError("cannot read Wish reference records") from exc
        for path in entries:
            if path.is_symlink() or not path.is_file() or not path.name.endswith(".json"):
                raise ContractError("Wish reference record directory contains an unsafe entry")
            expected_id = path.name[:-5]
            _safe_id(expected_id, "world reference id")
            document = self._record_document(path)
            payload, scope, unused_sha = self._decode_record(
                document,
                expected_wish=wish,
                expected_reference_id=expected_id,
            )
            del payload, scope, unused_sha
            receipts.append(self._receipt(document, expected_wish=wish))
        self._assert_current()
        return tuple(receipts)

    def descriptors(self, wish: Wish) -> Tuple[WorldReferenceDescriptor, ...]:
        """Return authenticated, raw-free scope descriptors for Invent."""

        self._registered_product(wish)
        wish_sha256 = _wish_sha256(wish)
        root = self._record_path(
            wish_sha256, "placeholder", create=False
        ).parent
        descriptors = []
        try:
            entries = sorted(root.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise ContractError("cannot read Wish reference records") from exc
        for path in entries:
            if path.is_symlink() or not path.is_file() or not path.name.endswith(".json"):
                raise ContractError(
                    "Wish reference record directory contains an unsafe entry"
                )
            reference_id = _safe_id(
                path.name[:-5], "world reference id"
            )
            document = self._record_document(path)
            unused_payload, scope, unused_sha = self._decode_record(
                document,
                expected_wish=wish,
                expected_reference_id=reference_id,
            )
            del unused_payload, unused_sha
            descriptors.append(
                WorldReferenceDescriptor(
                    scope,
                    self._receipt(document, expected_wish=wish),
                    document,
                )
            )
        self._assert_current()
        return tuple(descriptors)

    def verify_admission(
        self,
        admission: Mapping[str, Any],
        wish: Wish,
        *,
        expected_reference_id: str,
    ) -> None:
        """Replay a raw-free scope admission against the exact local record."""

        self._registered_product(wish)
        if not isinstance(admission, Mapping):
            raise ContractError("world reference admission is malformed")
        submitted_payload, unused_scope, submitted_sha = self._decode_record(
            admission,
            expected_wish=wish,
            expected_reference_id=expected_reference_id,
        )
        del submitted_payload, unused_scope
        persisted = self._record_document(
            self._record_path(
                _wish_sha256(wish), expected_reference_id, create=False
            )
        )
        if submitted_sha != _canonical_sha256(persisted):
            raise ContractError(
                "world reference admission differs from the exact local record"
            )
        self._receipt(persisted, expected_wish=wish)
        self._assert_current()

    def _authorization(
        self,
        *,
        payload: Mapping[str, Any],
        record_sha256: str,
        scope: WorldReferenceScope,
        personalization_sha256: str,
        provider_id: str,
    ) -> Dict[str, Any]:
        claims = {
            "schema_version": 1,
            "kind": "world-reference-authorization",
            "product_id": payload["product_id"],
            "wish_sha256": payload["wish_sha256"],
            "reference_id": scope.reference_id,
            "record_sha256": record_sha256,
            "content_sha256": payload["content_sha256"],
            "consent_sha256": payload["consent_sha256"],
            "personalization_sha256": personalization_sha256,
            "reviewer_id": scope.reviewer_id,
            "provider_id": provider_id,
            "allowed_features": list(scope.allowed_features),
            "storage_security_boundary": LOCAL_STORAGE_SECURITY_BOUNDARY,
            "consent_claim_boundary": CONSENT_CLAIM_BOUNDARY,
        }
        return {"claims": claims, "authentication": self._sign(claims)}

    def authorized_provider_inputs(
        self,
        wish: Wish,
        personalization_map: Mapping[str, Any],
        *,
        expected_reviewer_id: str,
        provider_id: str,
    ) -> Tuple[AuthorizedWorldReference, ...]:
        """Resolve exact inputs for a same-user-trusted development provider.

        This checks local admission only. The provider must independently produce
        and authenticate its recognition cases; this method never emits a pass.
        """

        self._registered_product(wish)
        reviewer_id = _safe_actor(expected_reviewer_id, "expected reviewer id")
        selected_provider = _safe_actor(provider_id, "world provider id")
        if not isinstance(personalization_map, Mapping) or set(personalization_map) != {
            "consented_references",
            "feature_to_form_map",
        }:
            raise ContractError("world personalization map is malformed")
        raw_references = personalization_map["consented_references"]
        raw_mappings = personalization_map["feature_to_form_map"]
        if (
            isinstance(raw_references, (str, bytes))
            or not isinstance(raw_references, Sequence)
            or not raw_references
            or isinstance(raw_mappings, (str, bytes))
            or not isinstance(raw_mappings, Sequence)
            or not raw_mappings
        ):
            raise ContractError("world personalization map is incomplete")
        expected: Dict[str, Mapping[str, Any]] = {}
        for item in raw_references:
            if not isinstance(item, Mapping) or set(item) != {
                "reference_id",
                "subject",
                "consent_or_rights_basis",
                "allowed_features",
                "excluded_features",
            }:
                raise ContractError("world consent contract is malformed")
            reference_id = _safe_id(item.get("reference_id"), "world reference id")
            if reference_id in expected:
                raise ContractError("world consent contract repeats a reference")
            expected[reference_id] = item
        mapped_features: Dict[str, set[str]] = {reference_id: set() for reference_id in expected}
        for item in raw_mappings:
            if not isinstance(item, Mapping) or set(item) != {
                "reference_id",
                "reference_feature",
                "physical_form",
                "recognition_test",
            }:
                raise ContractError("world feature-to-form mapping is malformed")
            reference_id = _safe_id(item.get("reference_id"), "world reference id")
            if reference_id not in expected:
                raise ContractError("world mapping refers to an unauthorized reference")
            feature = _bounded_text(
                item.get("reference_feature"), "world reference feature", 1_000
            )
            _bounded_text(item.get("physical_form"), "world physical form", 2_000)
            _bounded_text(item.get("recognition_test"), "world recognition test", 2_000)
            if feature in mapped_features[reference_id]:
                raise ContractError("world personalization map repeats a feature")
            mapped_features[reference_id].add(feature)
        personalization_sha256 = _canonical_sha256(dict(personalization_map))
        authorized = []
        wish_sha256 = _wish_sha256(wish)
        for reference_id in sorted(expected):
            path = self._record_path(wish_sha256, reference_id, create=False)
            document = self._record_document(path)
            payload, scope, record_sha256 = self._decode_record(
                document,
                expected_wish=wish,
                expected_reference_id=reference_id,
            )
            contract = expected[reference_id]
            contract_allowed = _feature_list(
                contract.get("allowed_features"),
                "world contract allowed features",
                required=True,
            )
            contract_excluded = _feature_list(
                contract.get("excluded_features"),
                "world contract excluded features",
                required=False,
            )
            if (
                scope.reviewer_id != reviewer_id
                or scope.subject != contract.get("subject")
                or scope.rights_basis != contract.get("consent_or_rights_basis")
                or scope.allowed_features != contract_allowed
                or scope.excluded_features != contract_excluded
                or not mapped_features[reference_id]
                or not mapped_features[reference_id].issubset(set(scope.allowed_features))
                or mapped_features[reference_id] & set(scope.excluded_features)
            ):
                raise ContractError(
                    "world provider request differs from the exact reviewed consent scope"
                )
            reference = _read_bounded_regular(
                self._blob(payload["content_sha256"]),
                MAX_WORLD_REFERENCE_BYTES,
                "private world reference blob",
                expected_sha256=payload["content_sha256"],
                expected_size=payload["content_bytes"],
                private=True,
            )
            consent = _read_bounded_regular(
                self._blob(payload["consent_sha256"]),
                MAX_WORLD_CONSENT_BYTES,
                "private world consent blob",
                expected_sha256=payload["consent_sha256"],
                expected_size=payload["consent_bytes"],
                private=True,
            )
            authorization = self._authorization(
                payload=payload,
                record_sha256=record_sha256,
                scope=scope,
                personalization_sha256=personalization_sha256,
                provider_id=selected_provider,
            )
            authorized.append(
                AuthorizedWorldReference(
                    scope=scope,
                    product_id=wish.product_id,
                    wish_sha256=wish_sha256,
                    media_type=payload["media_type"],
                    content_sha256=payload["content_sha256"],
                    consent_sha256=payload["consent_sha256"],
                    record_sha256=record_sha256,
                    authorization=authorization,
                    reference_bytes=reference,
                    consent_bytes=consent,
                )
            )
        self._assert_current()
        return tuple(authorized)

    def verify_authorization(
        self,
        authorization: Mapping[str, Any],
        wish: Wish,
        personalization_map: Mapping[str, Any],
        *,
        expected_reviewer_id: str,
        provider_id: str,
    ) -> None:
        """Replay one raw-free authorization attestation against this vault."""

        self._registered_product(wish)
        if not isinstance(authorization, Mapping) or set(authorization) != {
            "claims",
            "authentication",
        } or not isinstance(authorization.get("claims"), Mapping):
            raise ContractError("world authorization is malformed")
        claims = authorization["claims"]
        expected_keys = {
            "schema_version",
            "kind",
            "product_id",
            "wish_sha256",
            "reference_id",
            "record_sha256",
            "content_sha256",
            "consent_sha256",
            "personalization_sha256",
            "reviewer_id",
            "provider_id",
            "allowed_features",
            "storage_security_boundary",
            "consent_claim_boundary",
        }
        if set(claims) != expected_keys:
            raise ContractError("world authorization claims are malformed")
        self._verify_authentication(claims, authorization["authentication"])
        if (
            claims.get("schema_version") != 1
            or claims.get("kind") != "world-reference-authorization"
            or claims.get("product_id") != wish.product_id
            or claims.get("wish_sha256") != _wish_sha256(wish)
            or claims.get("personalization_sha256")
            != _canonical_sha256(dict(personalization_map))
            or claims.get("reviewer_id")
            != _safe_actor(expected_reviewer_id, "expected reviewer id")
            or claims.get("provider_id")
            != _safe_actor(provider_id, "world provider id")
            or claims.get("storage_security_boundary")
            != LOCAL_STORAGE_SECURITY_BOUNDARY
            or claims.get("consent_claim_boundary") != CONSENT_CLAIM_BOUNDARY
        ):
            raise ContractError("world authorization was replayed in another context")
        reference_id = _safe_id(claims.get("reference_id"), "world reference id")
        document = self._record_document(
            self._record_path(_wish_sha256(wish), reference_id, create=False)
        )
        payload, scope, record_sha256 = self._decode_record(
            document,
            expected_wish=wish,
            expected_reference_id=reference_id,
        )
        if (
            claims.get("record_sha256") != record_sha256
            or claims.get("content_sha256") != payload["content_sha256"]
            or claims.get("consent_sha256") != payload["consent_sha256"]
            or claims.get("allowed_features") != list(scope.allowed_features)
        ):
            raise ContractError("world authorization differs from its sealed record")
        _read_bounded_regular(
            self._blob(payload["content_sha256"]),
            MAX_WORLD_REFERENCE_BYTES,
            "private world reference blob",
            expected_sha256=payload["content_sha256"],
            expected_size=payload["content_bytes"],
            private=True,
        )
        _read_bounded_regular(
            self._blob(payload["consent_sha256"]),
            MAX_WORLD_CONSENT_BYTES,
            "private world consent blob",
            expected_sha256=payload["consent_sha256"],
            expected_size=payload["consent_bytes"],
            private=True,
        )
        self._assert_current()


__all__ = [
    "AuthorizedWorldReference",
    "CONSENT_CLAIM_BOUNDARY",
    "LOCAL_STORAGE_SECURITY_BOUNDARY",
    "MAX_WORLD_CONSENT_BYTES",
    "MAX_WORLD_REFERENCE_BYTES",
    "SUPPORTED_WORLD_CONSENT_METHODS",
    "SUPPORTED_WORLD_MEDIA_TYPES",
    "SUPPORTED_WORLD_SUBJECT_KINDS",
    "UNSUPPORTED_WORLD_SUBJECT_KINDS",
    "WorldReferenceReceipt",
    "WorldReferenceDescriptor",
    "WorldReferenceService",
    "WorldReferenceScope",
    "WorldReferenceVault",
]
