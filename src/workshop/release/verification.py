"""Host-owned, public-safe verification for one exact released product.

The native agent authors the Release package and Playtest evidence, but it
cannot assign a verification level.  The trusted host derives this compact
manifest only after independently validating the exact Made, Playtested, and
Release contracts.  Free-form observations, paths, transcripts, receipts, and
identities are intentionally absent so the exact file can be published.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from workshop._validation import require_sha256
from workshop.errors import ArtifactError, ContractError
from workshop.make.native import NativeMade
from workshop.playtest.native import NativePlaytested
from workshop.release.native import NativeRelease


PRODUCT_VERIFICATION_SCHEMA_VERSION = 1
PRODUCT_VERIFICATION_KIND = "autonomous-workshop.product-verification"
PRODUCT_VERIFICATION_PATH = "artifacts/release/VERIFICATION.json"
PUBLIC_PRODUCT_VERIFICATION_FILENAME = "VERIFICATION.json"
DIGITALLY_VERIFIED = "digitally-verified"
PHYSICALLY_VERIFIED = "physically-verified"
DIGITALLY_VERIFIED_LABEL = "Digitally Verified"
PHYSICALLY_VERIFIED_LABEL = "Physically Verified"
MAX_PRODUCT_VERIFICATION_BYTES = 64 * 1024

_DIGITAL_SCOPE = (
    "sealed-product-bytes",
    "passing-digital-playtest-evidence",
)
_DIGITAL_NOT_VERIFIED = (
    "physical-build",
    "physical-fit",
    "durability",
    "human-response",
)
_CHECK_FIELDS = frozenset(
    ("check_id", "passed", "config_sha256", "evidence_sha256")
)
_VERIFICATION_FIELDS = frozenset(
    (
        "schema_version",
        "kind",
        "level",
        "label",
        "product_artifact_sha256",
        "playtest_evidence_artifact_sha256",
        "made_sha256",
        "playtested_sha256",
        "native_release_sha256",
        "product_json_sha256",
        "checks",
        "scope",
        "not_verified",
        "physical_verification",
    )
)


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("product verification must be finite JSON") from exc


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise ValueError("non-finite JSON constant %s" % value)


def _strict_canonical_json(content: bytes) -> dict[str, Any]:
    try:
        document = json.loads(
            content.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, ValueError, RecursionError, json.JSONDecodeError) as exc:
        raise ContractError(
            "VERIFICATION.json must contain strict UTF-8 JSON"
        ) from exc
    if not isinstance(document, dict):
        raise ContractError("VERIFICATION.json must contain one JSON object")
    if content != _canonical_json(document):
        raise ContractError("VERIFICATION.json must use canonical JSON encoding")
    return document


@dataclass(frozen=True)
class VerificationCheck:
    """Sanitized binding to one exact passing digital check."""

    check_id: str
    passed: bool
    config_sha256: str
    evidence_sha256: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.check_id, str)
            or not self.check_id
            or len(self.check_id) > 128
            or self.check_id[0] not in "abcdefghijklmnopqrstuvwxyz0123456789"
            or any(
                character not in "abcdefghijklmnopqrstuvwxyz0123456789._-"
                for character in self.check_id
            )
        ):
            raise ContractError("product verification check_id is invalid")
        if self.passed is not True:
            raise ContractError(
                "Digitally Verified requires every published check to pass"
            )
        require_sha256(
            self.config_sha256, "product verification check config sha256"
        )
        require_sha256(
            self.evidence_sha256, "product verification check evidence sha256"
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "passed": self.passed,
            "config_sha256": self.config_sha256,
            "evidence_sha256": self.evidence_sha256,
        }

    @classmethod
    def from_mapping(cls, value: Any) -> "VerificationCheck":
        if not isinstance(value, Mapping) or set(value) != _CHECK_FIELDS:
            raise ContractError("product verification check fields are invalid")
        return cls(
            check_id=value["check_id"],
            passed=value["passed"],
            config_sha256=value["config_sha256"],
            evidence_sha256=value["evidence_sha256"],
        )


@dataclass(frozen=True)
class ProductVerification:
    """Versioned public verification manifest derived by the trusted host.

    Schema v1 can truthfully emit only ``digitally-verified``.  The physical
    level is deliberately reserved until a typed trusted-host receipt contract
    can prove that these exact released bytes were built and checked.
    """

    product_artifact_sha256: str
    playtest_evidence_artifact_sha256: str
    made_sha256: str
    playtested_sha256: str
    native_release_sha256: str
    product_json_sha256: str
    checks: tuple[VerificationCheck, ...]
    scope: tuple[str, ...] = _DIGITAL_SCOPE
    not_verified: tuple[str, ...] = _DIGITAL_NOT_VERIFIED
    physical_verification: None = None
    schema_version: int = PRODUCT_VERIFICATION_SCHEMA_VERSION
    kind: str = PRODUCT_VERIFICATION_KIND
    level: str = DIGITALLY_VERIFIED
    label: str = DIGITALLY_VERIFIED_LABEL

    def __post_init__(self) -> None:
        if (
            type(self.schema_version) is not int
            or self.schema_version != PRODUCT_VERIFICATION_SCHEMA_VERSION
        ):
            raise ContractError("product verification schema_version must be 1")
        if self.kind != PRODUCT_VERIFICATION_KIND:
            raise ContractError("product verification kind is invalid")
        if (
            self.level == PHYSICALLY_VERIFIED
            or self.label == PHYSICALLY_VERIFIED_LABEL
        ):
            raise ContractError(
                "schema-v1 product verification cannot claim Physically Verified"
            )
        if self.level != DIGITALLY_VERIFIED or self.label != DIGITALLY_VERIFIED_LABEL:
            raise ContractError("product verification level is invalid")
        for value, name in (
            (self.product_artifact_sha256, "product artifact"),
            (self.playtest_evidence_artifact_sha256, "Playtest evidence artifact"),
            (self.made_sha256, "Made contract"),
            (self.playtested_sha256, "Playtested contract"),
            (self.native_release_sha256, "native Release contract"),
            (self.product_json_sha256, "Release product.json"),
        ):
            require_sha256(value, "product verification %s sha256" % name)
        checks = tuple(self.checks)
        if not checks or not all(
            isinstance(item, VerificationCheck) for item in checks
        ):
            raise ContractError("product verification requires typed passing checks")
        if tuple(sorted(checks, key=lambda item: item.check_id)) != checks:
            raise ContractError("product verification checks must be sorted")
        if len({item.check_id for item in checks}) != len(checks):
            raise ContractError("product verification check ids must be unique")
        if tuple(self.scope) != _DIGITAL_SCOPE:
            raise ContractError("Digitally Verified scope is invalid")
        if tuple(self.not_verified) != _DIGITAL_NOT_VERIFIED:
            raise ContractError("Digitally Verified limitations are invalid")
        if self.physical_verification is not None:
            raise ContractError(
                "Digitally Verified cannot contain physical verification proof"
            )
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "scope", tuple(self.scope))
        object.__setattr__(self, "not_verified", tuple(self.not_verified))

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "kind": self.kind,
            "level": self.level,
            "label": self.label,
            "product_artifact_sha256": self.product_artifact_sha256,
            "playtest_evidence_artifact_sha256": (
                self.playtest_evidence_artifact_sha256
            ),
            "made_sha256": self.made_sha256,
            "playtested_sha256": self.playtested_sha256,
            "native_release_sha256": self.native_release_sha256,
            "product_json_sha256": self.product_json_sha256,
            "checks": [item.to_dict() for item in self.checks],
            "scope": list(self.scope),
            "not_verified": list(self.not_verified),
            "physical_verification": self.physical_verification,
        }

    @property
    def sha256(self) -> str:
        return hashlib.sha256(_canonical_json(self.to_dict())).hexdigest()

    @classmethod
    def from_mapping(cls, value: Any) -> "ProductVerification":
        if not isinstance(value, Mapping) or set(value) != _VERIFICATION_FIELDS:
            raise ContractError("product verification fields are invalid")
        raw_checks = value["checks"]
        if not isinstance(raw_checks, list):
            raise ContractError("product verification checks must be a list")
        raw_scope = value["scope"]
        raw_not_verified = value["not_verified"]
        if not isinstance(raw_scope, list) or not isinstance(
            raw_not_verified, list
        ):
            raise ContractError("product verification scope fields must be lists")
        return cls(
            schema_version=value["schema_version"],
            kind=value["kind"],
            level=value["level"],
            label=value["label"],
            product_artifact_sha256=value["product_artifact_sha256"],
            playtest_evidence_artifact_sha256=value[
                "playtest_evidence_artifact_sha256"
            ],
            made_sha256=value["made_sha256"],
            playtested_sha256=value["playtested_sha256"],
            native_release_sha256=value["native_release_sha256"],
            product_json_sha256=value["product_json_sha256"],
            checks=tuple(VerificationCheck.from_mapping(item) for item in raw_checks),
            scope=tuple(raw_scope),
            not_verified=tuple(raw_not_verified),
            physical_verification=value["physical_verification"],
        )

    def assert_context(
        self,
        release: NativeRelease,
        made: NativeMade,
        playtested: NativePlaytested,
    ) -> None:
        """Prove that this public projection describes the exact host inputs."""

        if not isinstance(release, NativeRelease):
            raise ContractError("product verification requires a NativeRelease")
        if not isinstance(made, NativeMade) or not isinstance(
            playtested, NativePlaytested
        ):
            raise ContractError(
                "product verification requires NativeMade and NativePlaytested"
            )
        release.assert_context(made, playtested)
        expected_checks = tuple(
            VerificationCheck(
                check_id=check.check_id,
                passed=check.passed,
                config_sha256=check.config_sha256,
                evidence_sha256=check.evidence_sha256,
            )
            for check in sorted(playtested.checks, key=lambda item: item.check_id)
        )
        if (
            playtested.verdict != "pass"
            or self.product_artifact_sha256 != release.product_artifact_sha256
            or self.playtest_evidence_artifact_sha256
            != release.playtest_evidence_artifact_sha256
            or self.made_sha256 != made.made_sha256
            or self.playtested_sha256 != playtested.playtested_sha256
            or self.native_release_sha256 != release.release_sha256
            or self.product_json_sha256 != release.product_json_sha256
            or self.checks != expected_checks
        ):
            raise ContractError(
                "product verification belongs to different released bytes"
            )


def digitally_verified_product(
    release: NativeRelease,
    made: NativeMade,
    playtested: NativePlaytested,
) -> ProductVerification:
    """Derive the only verification level implemented by the current host."""

    release.assert_context(made, playtested)
    if playtested.verdict != "pass":
        raise ContractError("Digitally Verified requires a passing Playtest")
    result = ProductVerification(
        product_artifact_sha256=release.product_artifact_sha256,
        playtest_evidence_artifact_sha256=(
            release.playtest_evidence_artifact_sha256
        ),
        made_sha256=made.made_sha256,
        playtested_sha256=playtested.playtested_sha256,
        native_release_sha256=release.release_sha256,
        product_json_sha256=release.product_json_sha256,
        checks=tuple(
            VerificationCheck(
                check_id=check.check_id,
                passed=check.passed,
                config_sha256=check.config_sha256,
                evidence_sha256=check.evidence_sha256,
            )
            for check in sorted(playtested.checks, key=lambda item: item.check_id)
        ),
    )
    result.assert_context(release, made, playtested)
    return result


def _read_regular(path: Path) -> bytes:
    try:
        expected = path.lstat()
    except OSError as exc:
        raise ArtifactError("VERIFICATION.json is unavailable") from exc
    if stat.S_ISLNK(expected.st_mode) or not stat.S_ISREG(expected.st_mode):
        raise ArtifactError("VERIFICATION.json must be a regular file")
    if not 1 <= expected.st_size <= MAX_PRODUCT_VERIFICATION_BYTES:
        raise ArtifactError("VERIFICATION.json exceeds its byte limit")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(str(path), flags)
    except OSError as exc:
        raise ArtifactError("VERIFICATION.json cannot be opened safely") from exc
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (expected.st_dev, expected.st_ino)
        ):
            raise ArtifactError("VERIFICATION.json changed while opening")
        chunks: list[bytes] = []
        remaining = MAX_PRODUCT_VERIFICATION_BYTES + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
        if (
            len(content) != opened.st_size
            or len(content) > MAX_PRODUCT_VERIFICATION_BYTES
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
            or (after.st_dev, after.st_ino) != (opened.st_dev, opened.st_ino)
        ):
            raise ArtifactError("VERIFICATION.json changed while reading")
        return content
    finally:
        os.close(descriptor)


def read_product_verification(path: Path) -> ProductVerification:
    """Read one strict canonical public verification manifest."""

    document = _strict_canonical_json(_read_regular(path))
    return ProductVerification.from_mapping(document)


def _verification_path(run_root: Path) -> Path:
    requested = Path(run_root)
    if not requested.is_absolute() or requested.is_symlink():
        raise ContractError("product verification run root must be absolute and real")
    try:
        resolved = requested.resolve(strict=True)
    except OSError as exc:
        raise ArtifactError("product verification run root is unavailable") from exc
    if requested != resolved or not requested.is_dir():
        raise ContractError("product verification run root must be canonical")
    parent = requested
    for part in ("artifacts", "release"):
        parent = parent / part
        try:
            identity = parent.lstat()
        except OSError as exc:
            raise ArtifactError("product verification parent is unavailable") from exc
        if stat.S_ISLNK(identity.st_mode) or not stat.S_ISDIR(identity.st_mode):
            raise ArtifactError("product verification parent must be a real directory")
    return parent / PUBLIC_PRODUCT_VERIFICATION_FILENAME


def materialize_digital_verification(
    run_root: Path,
    release: NativeRelease,
    made: NativeMade,
    playtested: NativePlaytested,
) -> ProductVerification:
    """Validate Release, then atomically write the host-owned public projection."""

    release.validate_package_tree(run_root, made, playtested)
    verification = digitally_verified_product(release, made, playtested)
    content = _canonical_json(verification.to_dict())
    target = _verification_path(run_root)
    if target.exists() or target.is_symlink():
        try:
            identity = target.lstat()
        except OSError as exc:
            raise ArtifactError("VERIFICATION.json is unavailable") from exc
        if stat.S_ISLNK(identity.st_mode) or not stat.S_ISREG(identity.st_mode):
            raise ArtifactError("VERIFICATION.json must be a regular host-owned file")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".VERIFICATION.", dir=str(target.parent)
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o644)
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, target)
        parent_descriptor = os.open(
            str(target.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass

    observed = read_product_verification(target)
    observed.assert_context(release, made, playtested)
    if (
        observed.to_dict() != verification.to_dict()
        or observed.sha256 != hashlib.sha256(content).hexdigest()
    ):
        raise ArtifactError("VERIFICATION.json differs from host-derived bytes")
    return observed


def try_materialize_digital_verification(
    run_root: Path,
    release: NativeRelease,
    made: NativeMade,
    playtested: NativePlaytested,
) -> ProductVerification | None:
    """Best-effort public enrichment that can never become a Release gate.

    The exact Make, Playtest, and Release gates have already run before this
    helper is appropriate. Any validation, filesystem, serialization, or other
    enrichment failure yields no public record; it does not reclassify the
    accepted product or authorize a fabricated level.
    """

    try:
        return materialize_digital_verification(
            run_root, release, made, playtested
        )
    except Exception:
        return None


__all__ = [
    "DIGITALLY_VERIFIED",
    "DIGITALLY_VERIFIED_LABEL",
    "MAX_PRODUCT_VERIFICATION_BYTES",
    "PHYSICALLY_VERIFIED",
    "PHYSICALLY_VERIFIED_LABEL",
    "PRODUCT_VERIFICATION_KIND",
    "PRODUCT_VERIFICATION_PATH",
    "PRODUCT_VERIFICATION_SCHEMA_VERSION",
    "PUBLIC_PRODUCT_VERIFICATION_FILENAME",
    "ProductVerification",
    "VerificationCheck",
    "digitally_verified_product",
    "materialize_digital_verification",
    "read_product_verification",
    "try_materialize_digital_verification",
]
