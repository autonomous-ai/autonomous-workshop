"""The Toy Workshop pipeline and its three inventor customization levels.

An inventor supplies Taste and may replace Make, or Make and Playtest. Invent is
the industrial-design stage that selects a concept; Make is the mechanical and
3D-design stage that engineers it. The Workshop always owns the loops, exact
artifact identity, Instructions, Deliver, and truthful waiting for capabilities
that are not present. Playtest is AI-agent simulation. Customer Reviews arrive
asynchronously after Deliver and become learning for a future Make without
mutating shipped bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
from typing import Any, Callable, Mapping, Optional, Tuple

from .artifacts import ArtifactEntry, ArtifactManifest, build_artifact_manifest
from .cad import (
    CadPart,
    CadProjectManifest,
    CadReleaseBundle,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
)
from .deliver import DefaultDeliver
from .instructions import (
    DefaultInstructions,
    INSTRUCTIONS_MANIFEST_FILENAME,
    sealed_instructions_manifest,
)
from .lease_guard import LeaseGuard
from .errors import ContractError, StateConflict
from .jobs import (
    CustomerReview,
    DeliverContext,
    Delivered,
    Feedback,
    InstructionsContext,
    InventContext,
    Invented,
    Made,
    MakeContext,
    Need,
    PlaytestContext,
    Playtested,
    ProductInstructions,
    WaitingFor,
    WorkshopRun,
)
from .make import Wish
from .manifest import load_manifest
from .models import PlaytestResult
from .playtest import Playtest
from .playtest_release import playtest_release_needs
from .runtime import Runtime
from .reviews import ReviewAuthentication, ReviewAuthenticator
from .taste import load_taste
from .toys import ToyBlueprint, playful_make_request


InventJob = Callable[[InventContext], Invented]
MakeJob = Callable[[MakeContext], Made]
PlaytestJob = Callable[[PlaytestContext], Playtested]
InstructionsJob = Callable[[InstructionsContext], ProductInstructions]
DeliverJob = Callable[[DeliverContext], Delivered]

CUSTOMIZATION_LEVELS = ("taste-only", "custom-make", "custom-playtest")
_INSTRUCTIONS_CHECKPOINT = "instructions-checkpoint.json"
_CHECKPOINT_SCHEMA_VERSION = 1
_CHECKPOINT_DIRECTORY = "checkpoints"
_INVENTOR_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


def _lease_token(value: Any) -> str:
    if isinstance(value, LeaseGuard):
        return value.assert_current()
    if not isinstance(value, str) or not value:
        raise ContractError("Workshop operation requires a fencing token")
    return value


def _callable_or_none(value: Any, label: str) -> None:
    if value is not None and not callable(value):
        raise ContractError("%s must be callable or absent" % label)


def _resolve_inventor_id(root: Path, requested: Optional[str]) -> str:
    """Resolve operational identity from Workshop structure, never Taste/Wish."""

    if requested is not None and (
        not isinstance(requested, str) or not _INVENTOR_ID.fullmatch(requested)
    ):
        raise ContractError("Workshop inventor_id must be a canonical slug")
    manifest_path = root / "inventor.json"
    if manifest_path.exists() or manifest_path.is_symlink():
        inventor_id = load_manifest(manifest_path).inventor_id
        if requested is not None and requested != inventor_id:
            raise ContractError(
                "Workshop inventor_id does not match the inventor manifest"
            )
        return inventor_id
    if requested is not None:
        return requested
    if _INVENTOR_ID.fullmatch(root.name):
        return root.name
    raise ContractError(
        "Workshop requires inventor_id when its root has no inventor.json identity"
    )


def _inside(path: Path, root: Path, label: str) -> None:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError("%s must stay inside its Workshop workspace" % label) from exc


def _review_from_dict(value: Any) -> CustomerReview:
    """Rebuild one append-only review event using the public typed contract."""

    if not isinstance(value, Mapping):
        raise ContractError("persisted customer review must be an object")
    try:
        return CustomerReview(
            review_id=value["review_id"],
            product_artifact_sha256=value["product_artifact_sha256"],
            instructions_sha256=value["instructions_sha256"],
            delivery_tracking_id=value["delivery_tracking_id"],
            rating=value["rating"],
            feedback=value["feedback"],
            observed_at=value["observed_at"],
        )
    except KeyError as exc:
        raise ContractError(
            "persisted customer review is missing %s" % exc.args[0]
        ) from exc


def _delivery_from_events(runtime: Runtime, product_id: str) -> Delivered:
    """Return the immutable Deliver result that customer feedback must cite."""

    for event in reversed(runtime.events(product_id)):
        payload = event.get("payload")
        if not isinstance(payload, Mapping) or payload.get("status") != "delivered":
            continue
        value = payload.get("delivery")
        if not isinstance(value, Mapping):
            continue
        try:
            return Delivered(
                product_artifact_sha256=value["product_artifact_sha256"],
                instructions_sha256=value["instructions_sha256"],
                carrier=value["carrier"],
                service=value["service"],
                tracking_id=value["tracking_id"],
                status=value["status"],
                observed_at=value["observed_at"],
                evidence=value["evidence"],
            )
        except KeyError as exc:
            raise ContractError(
                "persisted delivery is missing %s" % exc.args[0]
            ) from exc
    raise ContractError("customer Reviews require a completed Deliver result")


def _utc_instant(value: str) -> datetime:
    """Parse a timestamp already validated by a typed Workshop record."""

    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(
        timezone.utc
    )


def _reviews_from_events(
    runtime: Runtime, product_id: str
) -> Tuple[CustomerReview, ...]:
    """Read and revalidate every append-only Review against Deliver."""

    records = []
    for event in runtime.events(product_id):
        payload = event.get("payload")
        if isinstance(payload, Mapping) and "customer_review" in payload:
            review = _review_from_dict(payload["customer_review"])
            authentication = ReviewAuthentication.from_dict(
                payload.get("customer_review_authentication")
            )
            records.append((review, authentication))
    if not records:
        return ()

    delivered = _delivery_from_events(runtime, product_id)
    seen_ids = set()
    for review, authentication in records:
        if review.review_id in seen_ids:
            raise ContractError("persisted customer review_id must be unique")
        seen_ids.add(review.review_id)
        review.assert_delivery(delivered)
        if _utc_instant(review.observed_at) < _utc_instant(delivered.observed_at):
            raise ContractError("persisted customer Review cannot predate Deliver")
        authentication.assert_review(review, delivered)
    return tuple(review for review, _ in records)


def _playtest_policy_needs(
    blueprint: ToyBlueprint,
    made: Made,
    playtested: Playtested,
    evidence_root: Path,
) -> tuple[Need, ...]:
    """Apply the common release bar to shared and custom Playtest outputs."""

    return playtest_release_needs(blueprint, made, playtested, evidence_root)


def _canonical_json(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ContractError("Instructions checkpoint accepts only finite JSON") from exc


_MAX_CHECKPOINT_BYTES = 64 * 1024 * 1024


def _read_checkpoint_descriptor(descriptor: int, label: str) -> bytes:
    metadata = os.fstat(descriptor)
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != os.getuid()
        or stat.S_IMODE(metadata.st_mode) != 0o600
        or metadata.st_size > _MAX_CHECKPOINT_BYTES
    ):
        raise ContractError(
            "%s must be a private bounded regular file owned by this user" % label
        )
    chunks = []
    remaining = _MAX_CHECKPOINT_BYTES + 1
    while remaining:
        chunk = os.read(descriptor, min(1024 * 1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    data = b"".join(chunks)
    if len(data) > _MAX_CHECKPOINT_BYTES:
        raise ContractError("%s is too large" % label)
    return data


def _read_file_nofollow(path: Path, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ContractError("%s cannot be opened safely" % label) from exc
    try:
        return _read_checkpoint_descriptor(descriptor, label)
    finally:
        os.close(descriptor)


def _write_json_once(path: Path, value: Mapping[str, Any]) -> None:
    """Create one durable checkpoint through an anchored, no-follow directory."""

    encoded = (
        json.dumps(
            value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
        )
        + "\n"
    ).encode("utf-8")
    parent_flags = (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        parent = os.open(path.parent, parent_flags)
    except OSError as exc:
        raise ContractError("checkpoint directory is missing or unsafe") from exc
    temporary: Optional[str] = None
    try:
        if not stat.S_ISDIR(os.fstat(parent).st_mode):
            raise ContractError("checkpoint parent must be a regular directory")
        read_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            existing_fd = os.open(path.name, read_flags, dir_fd=parent)
        except FileNotFoundError:
            existing_fd = None
        except OSError as exc:
            raise ContractError("checkpoint path is unsafe") from exc
        if existing_fd is not None:
            try:
                if _read_checkpoint_descriptor(existing_fd, "checkpoint") == encoded:
                    return
            finally:
                os.close(existing_fd)
            raise ContractError("checkpoint already exists with different bytes")

        for _ in range(100):
            temporary = ".%s.%s" % (path.name, secrets.token_hex(8))
            try:
                descriptor = os.open(
                    temporary,
                    os.O_WRONLY
                    | os.O_CREAT
                    | os.O_EXCL
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent,
                )
                break
            except FileExistsError:
                temporary = None
        else:
            raise ContractError("cannot reserve a private checkpoint temporary")
        try:
            view = memoryview(encoded)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
            os.fchmod(descriptor, 0o600)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        try:
            os.link(
                temporary,
                path.name,
                src_dir_fd=parent,
                dst_dir_fd=parent,
                follow_symlinks=False,
            )
        except FileExistsError as exc:
            try:
                existing_fd = os.open(path.name, read_flags, dir_fd=parent)
            except OSError as open_error:
                raise ContractError("checkpoint path is unsafe") from open_error
            try:
                existing = _read_checkpoint_descriptor(existing_fd, "checkpoint")
            finally:
                os.close(existing_fd)
            if existing != encoded:
                raise ContractError(
                    "checkpoint already exists with different bytes"
                ) from exc
        os.fsync(parent)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def _mkdir_durable(path: Path, *, mode: int = 0o700) -> None:
    """Create one private directory and durably publish its name."""

    if path.exists() or path.is_symlink():
        if path.is_symlink() or not path.is_dir():
            raise ContractError("Workshop directory is unsafe")
        return
    parent = path.parent
    if parent.is_symlink() or not parent.is_dir():
        raise ContractError("Workshop directory parent is missing or unsafe")
    path.mkdir(mode=mode)
    os.chmod(path, mode)
    directory = os.open(parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _safe_relative_file(root: Path, value: Any, label: str) -> Path:
    """Resolve a regular run-relative file without accepting any symlink hop."""

    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractError("%s path is malformed" % label)
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != value:
        raise ContractError("%s path is unsafe" % label)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ContractError("%s path must not contain symlinks" % label)
    try:
        resolved = current.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError("%s is missing or unsafe" % label) from exc
    if not resolved.is_file():
        raise ContractError("%s must be a regular file" % label)
    return resolved


def _workshop_run_root(
    runtime_root: Path,
    product_id: str,
    *,
    create: bool,
) -> Path:
    """Resolve one run below private, non-symlink runtime components."""

    if product_id in {".", ".."} or any(character in "/\\" for character in product_id):
        raise ContractError("Workshop product id is unsafe for a run directory")
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        raise ContractError("Workshop runtime directory is missing or unsafe")
    runtime = runtime_root.resolve(strict=True)
    runs = runtime_root / "runs"
    if not runs.exists() and not runs.is_symlink():
        _mkdir_durable(runs)
    if runs.is_symlink() or not runs.is_dir():
        raise ContractError("Workshop runs directory is missing or unsafe")
    try:
        resolved_runs = runs.resolve(strict=True)
        resolved_runs.relative_to(runtime)
    except (OSError, ValueError) as exc:
        raise ContractError("Workshop runs directory escapes its runtime") from exc
    candidate = runs / product_id
    if create:
        if candidate.exists() or candidate.is_symlink():
            if candidate.is_symlink() or not candidate.is_dir() or any(candidate.iterdir()):
                raise ContractError("new Workshop run directory must be fresh and empty")
        else:
            _mkdir_durable(candidate)
    if candidate.is_symlink() or not candidate.is_dir():
        raise ContractError("Workshop run directory is missing or unsafe")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(resolved_runs)
    except (OSError, ValueError) as exc:
        raise ContractError("Workshop run directory escapes its runtime") from exc
    return resolved


def _manifest_from_dict(value: Any, label: str) -> ArtifactManifest:
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version",
        "artifact_sha256",
        "total_bytes",
        "created_at",
        "entries",
    }:
        raise ContractError("%s manifest is malformed" % label)
    raw_entries = value.get("entries")
    if not isinstance(raw_entries, list):
        raise ContractError("%s manifest entries are malformed" % label)
    entries = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, Mapping) or set(raw_entry) != {
            "path",
            "bytes",
            "sha256",
            "executable",
        }:
            raise ContractError("%s manifest entry is malformed" % label)
        entries.append(
            ArtifactEntry(
                raw_entry["path"],
                raw_entry["bytes"],
                raw_entry["sha256"],
                raw_entry["executable"],
            )
        )
    return ArtifactManifest(
        value["schema_version"],
        value["artifact_sha256"],
        tuple(entries),
        value["total_bytes"],
        value["created_at"],
    )


def _cad_release_to_dict(value: Optional[CadReleaseBundle]) -> Any:
    if value is None:
        return None
    value.assert_valid()
    return {
        "manifest": value.manifest.to_dict(),
        "receipts": [item.to_dict() for item in value.receipts],
        "requirements": [
            {
                "validator": item.validator,
                "validator_version": item.validator_version,
                "config_sha256": item.config_sha256,
                "substrate": item.substrate,
                "required_checks": list(item.required_checks),
            }
            for item in value.requirements
        ],
    }


def _cad_release_from_dict(value: Any) -> Optional[CadReleaseBundle]:
    if value is None:
        return None
    if not isinstance(value, Mapping) or set(value) != {
        "manifest",
        "receipts",
        "requirements",
    }:
        raise ContractError("checkpoint CAD release is malformed")
    manifest_value = value["manifest"]
    if not isinstance(manifest_value, Mapping) or set(manifest_value) != {
        "schema_version",
        "project_id",
        "artifact_sha256",
        "engine",
        "skill_versions",
        "parts",
        "assemblies",
        "fits",
        "motions",
        "print_profile",
        "evidence_files",
        "physical_claims",
    }:
        raise ContractError("checkpoint CAD manifest is malformed")
    raw_parts = manifest_value["parts"]
    raw_claims = manifest_value["physical_claims"]
    if not isinstance(raw_parts, list) or not isinstance(raw_claims, list):
        raise ContractError("checkpoint CAD parts or claims are malformed")
    parts = []
    for item in raw_parts:
        if not isinstance(item, Mapping) or set(item) != {
            "part_id",
            "name",
            "quantity",
            "source_path",
            "step_path",
            "stl_path",
            "material",
            "print_orientation",
            "expected_solids",
            "expected_shells",
        }:
            raise ContractError("checkpoint CAD part is malformed")
        parts.append(CadPart(**dict(item)))
    claims = []
    for item in raw_claims:
        if not isinstance(item, Mapping) or set(item) != {
            "claim_id",
            "statement",
            "critical",
            "status",
            "evidence_ref",
            "evidence_sha256",
        }:
            raise ContractError("checkpoint CAD physical claim is malformed")
        claims.append(PhysicalClaim(**dict(item)))
    manifest = CadProjectManifest(
        manifest_value["schema_version"],
        manifest_value["project_id"],
        manifest_value["artifact_sha256"],
        manifest_value["engine"],
        manifest_value["skill_versions"],
        tuple(parts),
        tuple(manifest_value["assemblies"]),
        tuple(manifest_value["fits"]),
        tuple(manifest_value["motions"]),
        manifest_value["print_profile"],
        manifest_value["evidence_files"],
        tuple(claims),
    )
    raw_receipts = value["receipts"]
    raw_requirements = value["requirements"]
    if not isinstance(raw_receipts, list) or not isinstance(raw_requirements, list):
        raise ContractError("checkpoint CAD verification policy is malformed")
    receipts = []
    for item in raw_receipts:
        if not isinstance(item, Mapping) or set(item) != {
            "schema_version",
            "artifact_sha256",
            "validator",
            "validator_version",
            "config_sha256",
            "substrate",
            "status",
            "checks",
            "observed_at",
        }:
            raise ContractError("checkpoint CAD receipt is malformed")
        raw_checks = item["checks"]
        if not isinstance(raw_checks, list):
            raise ContractError("checkpoint CAD receipt checks are malformed")
        checks = []
        for check in raw_checks:
            if not isinstance(check, Mapping) or set(check) != {
                "check_id",
                "status",
                "measurements",
                "evidence_ref",
                "evidence_sha256",
                "limitations",
            }:
                raise ContractError("checkpoint CAD verification check is malformed")
            checks.append(VerificationCheck(**dict(check)))
        receipts.append(
            VerificationReceipt(
                item["schema_version"],
                item["artifact_sha256"],
                item["validator"],
                item["validator_version"],
                item["config_sha256"],
                item["substrate"],
                item["status"],
                tuple(checks),
                item["observed_at"],
            )
        )
    requirements = []
    for item in raw_requirements:
        if not isinstance(item, Mapping) or set(item) != {
            "validator",
            "validator_version",
            "config_sha256",
            "substrate",
            "required_checks",
        }:
            raise ContractError("checkpoint CAD validator requirement is malformed")
        requirements.append(ValidatorRequirement(**dict(item)))
    return CadReleaseBundle(manifest, tuple(receipts), tuple(requirements))


def _feedback_from_dict(value: Any) -> Feedback:
    if not isinstance(value, Mapping) or set(value) != {
        "code",
        "area",
        "severity",
        "finding",
        "change",
        "evidence_refs",
        "invalidates",
    }:
        raise ContractError("checkpoint Playtest feedback is malformed")
    return Feedback(
        value["code"],
        value["area"],
        value["severity"],
        value["finding"],
        value["change"],
        tuple(value["evidence_refs"]),
        tuple(value["invalidates"]),
    )


def _playtest_result_from_dict(value: Any) -> PlaytestResult:
    if not isinstance(value, Mapping) or set(value) != {
        "inspection_id",
        "passed",
        "artifact_sha256",
        "evidence",
        "evaluator",
        "evaluator_version",
        "config_sha256",
        "evidence_ref",
        "evidence_sha256",
        "observed_at",
    }:
        raise ContractError("checkpoint Playtest result is malformed")
    return PlaytestResult(**dict(value))


def _relative_tree(root: Path, path: Path, label: str) -> str:
    try:
        relative = path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError("%s must stay inside the Workshop run" % label) from exc
    if not relative.parts or relative.as_posix() == ".":
        raise ContractError("%s cannot be the Workshop run root" % label)
    return relative.as_posix()


def _checkpoint_tree(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ContractError("checkpoint %s path is malformed" % label)
    relative = Path(value)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != value:
        raise ContractError("checkpoint %s path is unsafe" % label)
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ContractError("checkpoint %s tree must not contain symlinks" % label)
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError("checkpoint %s tree is missing or unsafe" % label) from exc
    if not resolved.is_dir():
        raise ContractError("checkpoint %s tree must be a regular directory" % label)
    return resolved


def _instructions_checkpoint_payload(
    wish: Wish,
    inventor_id: str,
    taste_sha256: str,
    blueprint: ToyBlueprint,
    customization_level: str,
    playtest_rounds: int,
    round_number: int,
    made: Made,
    playtested: Playtested,
    run_root: Path,
    playtest_workspace: Path,
) -> Mapping[str, Any]:
    made.assert_current()
    playtested.evidence.assert_valid()
    evidence_manifest = playtested.evidence.evidence_manifest
    assert isinstance(evidence_manifest, ArtifactManifest)
    if evidence_manifest.to_dict() == made.artifact_manifest.to_dict():
        evidence_root = made.artifact_root
    else:
        evidence_root = playtest_workspace.resolve(strict=True)
        current_evidence = build_artifact_manifest(
            evidence_root, created_at=evidence_manifest.created_at
        )
        if current_evidence.to_dict() != evidence_manifest.to_dict():
            raise ContractError(
                "Playtest evidence must be sealed from its Workshop workspace to support safe Instructions resume"
            )
    return {
        "product_id": wish.product_id,
        "inventor_id": inventor_id,
        "wish": wish.to_dict(),
        "taste_sha256": taste_sha256,
        "blueprint_sha256": blueprint.sha256,
        "lane": blueprint.lane,
        "customization_level": customization_level,
        "playtest_rounds": playtest_rounds,
        "round": round_number,
        "made": {
            "root": _relative_tree(run_root, made.artifact_root, "Made artifact"),
            "manifest": made.artifact_manifest.to_dict(),
            "product": dict(made.product),
        },
        "playtested": {
            "evidence_root": _relative_tree(
                run_root, evidence_root, "Playtest evidence"
            ),
            "artifact_manifest": playtested.evidence.artifact_manifest.to_dict(),
            "evidence_manifest": evidence_manifest.to_dict(),
            "results": [item.to_dict() for item in playtested.evidence.results],
            "cad_release": _cad_release_to_dict(playtested.evidence.cad_release),
            "feedback": [item.to_dict() for item in playtested.feedback],
        },
    }


def _invented_from_dict(value: Any) -> Invented:
    if not isinstance(value, Mapping) or set(value) != {
        "wish_sha256",
        "taste_sha256",
        "lane",
        "concept",
        "concept_sha256",
        "score",
        "target_score",
        "passed",
    }:
        raise ContractError("persisted Invented result is malformed")
    invented = Invented(
        value["wish_sha256"],
        value["taste_sha256"],
        value["lane"],
        value["concept"],
        value["score"],
        value["target_score"],
    )
    if invented.to_dict() != dict(value):
        raise ContractError("persisted Invented result identity changed")
    return invented


def _checkpoint_bindings(
    wish: Wish,
    inventor_id: str,
    taste_sha256: str,
    blueprint: ToyBlueprint,
    customization_level: str,
    playtest_rounds: int,
) -> Mapping[str, Any]:
    return {
        "product_id": wish.product_id,
        "inventor_id": inventor_id,
        "wish": wish.to_dict(),
        "taste_sha256": taste_sha256,
        "blueprint_sha256": blueprint.sha256,
        "lane": blueprint.lane,
        "customization_level": customization_level,
        "playtest_rounds": playtest_rounds,
    }


def _made_value(
    run_root: Path,
    made: Made,
) -> Mapping[str, Any]:
    made.assert_current()
    return {
        "root": _relative_tree(run_root, made.artifact_root, "Made artifact"),
        "manifest": made.artifact_manifest.to_dict(),
        "product": dict(made.product),
    }


def _playtested_value(
    run_root: Path,
    made: Made,
    playtested: Playtested,
    playtest_workspace: Path,
) -> Mapping[str, Any]:
    playtested.assert_artifact(made.artifact_sha256)
    playtested.evidence.assert_valid()
    evidence_manifest = playtested.evidence.evidence_manifest
    assert isinstance(evidence_manifest, ArtifactManifest)
    if evidence_manifest.to_dict() == made.artifact_manifest.to_dict():
        evidence_root = made.artifact_root
    else:
        evidence_root = playtest_workspace.resolve(strict=True)
        current_evidence = build_artifact_manifest(
            evidence_root, created_at=evidence_manifest.created_at
        )
        if current_evidence.to_dict() != evidence_manifest.to_dict():
            raise ContractError("Playtest evidence bytes changed before checkpointing")
    return {
        "evidence_root": _relative_tree(
            run_root, evidence_root, "Playtest evidence"
        ),
        "artifact_manifest": playtested.evidence.artifact_manifest.to_dict(),
        "evidence_manifest": evidence_manifest.to_dict(),
        "results": [item.to_dict() for item in playtested.evidence.results],
        "cad_release": _cad_release_to_dict(playtested.evidence.cad_release),
        "feedback": [item.to_dict() for item in playtested.feedback],
    }


def _made_checkpoint_payload(
    wish: Wish,
    inventor_id: str,
    taste_sha256: str,
    blueprint: ToyBlueprint,
    customization_level: str,
    playtest_rounds: int,
    round_number: int,
    invented: Invented,
    feedback: tuple[Feedback, ...],
    made: Made,
    run_root: Path,
) -> Mapping[str, Any]:
    return {
        **_checkpoint_bindings(
            wish,
            inventor_id,
            taste_sha256,
            blueprint,
            customization_level,
            playtest_rounds,
        ),
        "round": round_number,
        "invented": invented.to_dict(),
        "input_feedback": [item.to_dict() for item in feedback],
        "made": _made_value(run_root, made),
    }


def _playtested_checkpoint_payload(
    wish: Wish,
    inventor_id: str,
    taste_sha256: str,
    blueprint: ToyBlueprint,
    customization_level: str,
    playtest_rounds: int,
    round_number: int,
    made_checkpoint_sha256: str,
    made: Made,
    playtested: Playtested,
    run_root: Path,
    playtest_workspace: Path,
) -> Mapping[str, Any]:
    return {
        **_checkpoint_bindings(
            wish,
            inventor_id,
            taste_sha256,
            blueprint,
            customization_level,
            playtest_rounds,
        ),
        "round": round_number,
        "made_checkpoint_sha256": made_checkpoint_sha256,
        "made": _made_value(run_root, made),
        "playtested": _playtested_value(
            run_root, made, playtested, playtest_workspace
        ),
    }


def _write_stage_checkpoint(
    run_root: Path,
    kind: str,
    round_number: int,
    payload: Mapping[str, Any],
) -> tuple[str, str]:
    if kind not in {"made", "playtested", "instructions"}:
        raise ContractError("unknown Workshop checkpoint kind")
    digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    checkpoint_root = run_root / _CHECKPOINT_DIRECTORY
    _mkdir_durable(checkpoint_root)
    filename = "%s-r%03d-%s.json" % (kind, round_number, digest)
    document = {
        "schema_version": _CHECKPOINT_SCHEMA_VERSION,
        "kind": kind,
        "checkpoint_sha256": digest,
        "payload": payload,
    }
    _write_json_once(checkpoint_root / filename, document)
    return "%s/%s" % (_CHECKPOINT_DIRECTORY, filename), digest


def _read_stage_checkpoint(
    run_root: Path,
    event: Mapping[str, Any],
    kind: str,
) -> tuple[Mapping[str, Any], str]:
    event_payload = event.get("payload")
    if not isinstance(event_payload, Mapping):
        raise ContractError("Workshop checkpoint event payload is malformed")
    path_key = "%s_checkpoint_path" % kind
    digest_key = "%s_checkpoint_sha256" % kind
    relative = event_payload.get(path_key)
    expected_digest = event_payload.get(digest_key)
    if not isinstance(expected_digest, str) or not re.fullmatch(
        r"[0-9a-f]{64}", expected_digest
    ):
        raise ContractError("exact %s checkpoint is not bound to this event" % kind)
    path = _safe_relative_file(run_root, relative, "%s checkpoint" % kind)
    round_number = event_payload.get(
        "%s_checkpoint_round" % kind, event_payload.get("round")
    )
    if type(round_number) is not int or round_number < 1:
        raise ContractError("Workshop checkpoint event round is malformed")
    expected_name = "%s-r%03d-%s.json" % (kind, round_number, expected_digest)
    if path.parent.name != _CHECKPOINT_DIRECTORY or path.name != expected_name:
        raise ContractError("%s checkpoint path does not match its identity" % kind)
    try:
        document = json.loads(
            _read_file_nofollow(path, "%s checkpoint" % kind).decode("utf-8")
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError("%s checkpoint must be valid UTF-8 JSON" % kind) from exc
    if (
        not isinstance(document, Mapping)
        or set(document) != {
            "schema_version",
            "kind",
            "checkpoint_sha256",
            "payload",
        }
        or document.get("schema_version") != _CHECKPOINT_SCHEMA_VERSION
        or document.get("kind") != kind
    ):
        raise ContractError("%s checkpoint is malformed" % kind)
    payload = document.get("payload")
    if not isinstance(payload, Mapping):
        raise ContractError("%s checkpoint payload is malformed" % kind)
    digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    if document.get("checkpoint_sha256") != digest or expected_digest != digest:
        raise ContractError("%s checkpoint identity changed" % kind)
    return payload, digest


def _rebuild_made_value(run_root: Path, value: Any) -> Made:
    if not isinstance(value, Mapping) or set(value) != {
        "root",
        "manifest",
        "product",
    }:
        raise ContractError("checkpoint Made result is malformed")
    made_root = _checkpoint_tree(run_root, value["root"], "Made")
    made_manifest = _manifest_from_dict(value["manifest"], "Made")
    return Made(made_root, made_manifest, value["product"])


def _rebuild_playtested_value(
    run_root: Path,
    value: Any,
    made: Made,
) -> tuple[Playtested, Path]:
    if not isinstance(value, Mapping) or set(value) != {
        "evidence_root",
        "artifact_manifest",
        "evidence_manifest",
        "results",
        "cad_release",
        "feedback",
    }:
        raise ContractError("checkpoint Playtested result is malformed")
    artifact_manifest = _manifest_from_dict(
        value["artifact_manifest"], "Playtest product"
    )
    if artifact_manifest.to_dict() != made.artifact_manifest.to_dict():
        raise ContractError("checkpoint Playtest identifies different Made bytes")
    evidence_root = _checkpoint_tree(
        run_root, value["evidence_root"], "Playtest evidence"
    )
    evidence_manifest = _manifest_from_dict(
        value["evidence_manifest"], "Playtest evidence"
    )
    current_evidence = build_artifact_manifest(
        evidence_root, created_at=evidence_manifest.created_at
    )
    if current_evidence.to_dict() != evidence_manifest.to_dict():
        raise ContractError("checkpoint Playtest evidence bytes changed")
    raw_results = value["results"]
    raw_feedback = value["feedback"]
    if not isinstance(raw_results, list) or not isinstance(raw_feedback, list):
        raise ContractError("checkpoint Playtested records are malformed")
    evidence = Playtest(
        artifact_manifest,
        tuple(_playtest_result_from_dict(item) for item in raw_results),
        _cad_release_from_dict(value["cad_release"]),
        evidence_manifest,
    )
    playtested = Playtested(
        evidence, tuple(_feedback_from_dict(item) for item in raw_feedback)
    )
    playtested.assert_artifact(made.artifact_sha256)
    return playtested, evidence_root


def _write_instructions_checkpoint(
    run_root: Path, round_number: int, payload: Mapping[str, Any]
) -> tuple[str, str]:
    return _write_stage_checkpoint(run_root, "instructions", round_number, payload)


def _read_instructions_checkpoint(
    run_root: Path,
    event: Optional[Mapping[str, Any]] = None,
) -> tuple[Mapping[str, Any], str]:
    if event is not None:
        event_payload = event.get("payload")
        if isinstance(event_payload, Mapping) and event_payload.get(
            "instructions_checkpoint_path"
        ) is not None:
            return _read_stage_checkpoint(run_root, event, "instructions")

    # Compatibility with pre-stage-checkpoint runs. New runs never write this
    # fixed name because an unbound crash orphan could otherwise strand retry.
    path = run_root / _INSTRUCTIONS_CHECKPOINT
    if path.is_symlink() or not path.is_file():
        raise ContractError("Instructions resume checkpoint is missing")
    try:
        document = json.loads(
            _read_file_nofollow(path, "Instructions resume checkpoint").decode(
                "utf-8"
            )
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(
            "Instructions resume checkpoint must be valid UTF-8 JSON"
        ) from exc
    if not isinstance(document, Mapping) or set(document) != {
        "schema_version",
        "checkpoint_sha256",
        "payload",
    } or document.get("schema_version") != 1:
        raise ContractError("Instructions resume checkpoint is malformed")
    payload = document.get("payload")
    if not isinstance(payload, Mapping):
        raise ContractError("Instructions resume checkpoint payload is malformed")
    digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    if document.get("checkpoint_sha256") != digest:
        raise ContractError("Instructions resume checkpoint identity changed")
    return payload, digest


def _rebuild_checkpoint_results(
    run_root: Path, payload: Mapping[str, Any]
) -> tuple[Made, Playtested, Path]:
    made_value = payload.get("made")
    playtested_value = payload.get("playtested")
    if not isinstance(made_value, Mapping) or set(made_value) != {
        "root",
        "manifest",
        "product",
    }:
        raise ContractError("checkpoint Made result is malformed")
    if not isinstance(playtested_value, Mapping) or set(playtested_value) != {
        "evidence_root",
        "artifact_manifest",
        "evidence_manifest",
        "results",
        "cad_release",
        "feedback",
    }:
        raise ContractError("checkpoint Playtested result is malformed")
    made_root = _checkpoint_tree(run_root, made_value["root"], "Made")
    made_manifest = _manifest_from_dict(made_value["manifest"], "Made")
    made = Made(made_root, made_manifest, made_value["product"])
    artifact_manifest = _manifest_from_dict(
        playtested_value["artifact_manifest"], "Playtest product"
    )
    if artifact_manifest.to_dict() != made_manifest.to_dict():
        raise ContractError("checkpoint Playtest identifies different Made bytes")
    evidence_root = _checkpoint_tree(
        run_root, playtested_value["evidence_root"], "Playtest evidence"
    )
    evidence_manifest = _manifest_from_dict(
        playtested_value["evidence_manifest"], "Playtest evidence"
    )
    current_evidence = build_artifact_manifest(
        evidence_root, created_at=evidence_manifest.created_at
    )
    if current_evidence.to_dict() != evidence_manifest.to_dict():
        raise ContractError("checkpoint Playtest evidence bytes changed")
    raw_results = playtested_value["results"]
    raw_feedback = playtested_value["feedback"]
    if not isinstance(raw_results, list) or not isinstance(raw_feedback, list):
        raise ContractError("checkpoint Playtested records are malformed")
    evidence = Playtest(
        artifact_manifest,
        tuple(_playtest_result_from_dict(item) for item in raw_results),
        _cad_release_from_dict(playtested_value["cad_release"]),
        evidence_manifest,
    )
    playtested = Playtested(
        evidence, tuple(_feedback_from_dict(item) for item in raw_feedback)
    )
    return made, playtested, evidence_root


@dataclass(frozen=True)
class WorkshopTools:
    """Shared capabilities installed once for every inventor in one Workshop."""

    invent: Optional[InventJob] = None
    make: Optional[MakeJob] = None
    playtest: Optional[PlaytestJob] = None
    instructions: Optional[InstructionsJob] = None
    deliver: Optional[DeliverJob] = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.invent, "Workshop Invent"),
            (self.make, "Workshop Make"),
            (self.playtest, "Workshop Playtest"),
            (self.instructions, "Workshop Instructions"),
            (self.deliver, "Workshop Deliver"),
        ):
            _callable_or_none(value, label)


def _missing_invent(context: InventContext) -> Invented:
    del context
    raise WaitingFor(
        Need(
            "invent",
            "industrial-design",
            "This Workshop has no configured shared concept and industrial-design provider.",
            "Configure the Workshop's shared Invent provider so it can research directions, choose one concept, and return an Invented record after its reward target is reached.",
        )
    )


def _missing_make(context: MakeContext) -> Made:
    del context
    raise WaitingFor(
        Need(
            "make",
            "model-and-cad-maker",
            "This Workshop has no configured model and parametric CAD maker.",
            "Install the shared model/CAD worker backed by the locked CAD and STEP-parts skills.",
        )
    )


def _missing_playtest(context: PlaytestContext) -> Playtested:
    capabilities = context.blueprint.required_capabilities("playtest")
    raise WaitingFor(
        *(
            Need(
                "playtest",
                capability,
                "This exact Make still needs %s AI-simulation evidence." % capability,
                "Configure the shared AI Playtest capability; never replace missing evidence with an inventor self-score.",
            )
            for capability in capabilities
        )
    )


class Workshop:
    """Run Wish -> Invent -> Make <-> Playtest -> Instructions -> Deliver.

    With neither override, the inventor authors only ``TASTE.md``. A Make override
    creates the middle level. Make plus Playtest creates the maximum level.
    Reviews happen after this synchronous run and feed a new future Make; a
    delivered run is immutable.
    """

    def __init__(
        self,
        inventor_root: Path,
        lane: str,
        *,
        inventor_id: Optional[str] = None,
        tools: Optional[WorkshopTools] = None,
        make: Optional[MakeJob] = None,
        playtest: Optional[PlaytestJob] = None,
        review_authenticator: Optional[ReviewAuthenticator] = None,
        runtime_root: Optional[Path] = None,
        max_rounds: int = 4,
    ) -> None:
        requested_root = Path(inventor_root)
        if requested_root.is_symlink():
            raise ContractError("inventor root must not be a symlink")
        try:
            root = requested_root.resolve(strict=True)
        except OSError as exc:
            raise ContractError("cannot resolve inventor root") from exc
        if not root.is_dir():
            raise ContractError("inventor root must be a directory")
        _callable_or_none(make, "inventor Make")
        _callable_or_none(playtest, "inventor Playtest")
        _callable_or_none(review_authenticator, "Workshop Review authenticator")
        if playtest is not None and make is None:
            raise ContractError("custom Playtest requires custom Make")
        if type(max_rounds) is not int or not 1 <= max_rounds <= 100:
            raise ContractError("max_rounds must be an integer from 1 to 100")

        selected_runtime = Path(runtime_root) if runtime_root else root / ".workshop"
        if not selected_runtime.is_absolute():
            raise ContractError("Workshop runtime_root must be absolute")
        if selected_runtime.is_symlink():
            raise ContractError("Workshop runtime_root must not be a symlink")

        self.inventor_root = root
        self.inventor_id = _resolve_inventor_id(root, inventor_id)
        self.taste = load_taste(root)
        self.blueprint = ToyBlueprint.for_lane(lane)
        requested_tools = tools or WorkshopTools()
        if not isinstance(requested_tools, WorkshopTools):
            raise ContractError("Workshop tools must be a WorkshopTools value")
        # Constructor-level Make/Playtest hooks are inventor overrides. Include
        # them in the field-by-field merge so the shared engine fills only the
        # other stages and never instantiates an unrelated replacement.
        requested_tools = WorkshopTools(
            invent=requested_tools.invent,
            make=make or requested_tools.make,
            playtest=playtest or requested_tools.playtest,
            instructions=requested_tools.instructions,
            deliver=requested_tools.deliver,
        )
        from .agent_invent import configured_workshop_tools

        selected_tools = configured_workshop_tools(
            requested_tools,
            inventor_id=self.inventor_id,
            runtime_root=selected_runtime,
        )
        self.tools = selected_tools
        self.invent_job: InventJob = selected_tools.invent or _missing_invent
        self.make_job: MakeJob = make or selected_tools.make or _missing_make
        self.playtest_job: PlaytestJob = (
            playtest or selected_tools.playtest or _missing_playtest
        )
        self.instructions_job: InstructionsJob = (
            selected_tools.instructions or DefaultInstructions()
        )
        self.deliver_job: DeliverJob = selected_tools.deliver or DefaultDeliver()
        self.review_authenticator = review_authenticator
        self.runtime_root = selected_runtime
        self.max_rounds = max_rounds
        if playtest is not None:
            self.customization_level = "custom-playtest"
        elif make is not None:
            self.customization_level = "custom-make"
        else:
            self.customization_level = "taste-only"

    @property
    def lane(self) -> str:
        return self.blueprint.lane

    def preview(self, wish: Wish) -> Mapping[str, Any]:
        """Return the exact Taste-bound playful brief shared Make receives."""

        return playful_make_request(wish, self.taste, self.blueprint)

    def _runtime(self) -> Runtime:
        return Runtime(self.runtime_root / "workshop.sqlite3")

    def reviews(self, product_id: str) -> Tuple[CustomerReview, ...]:
        """Read customer Reviews without making them part of the five-job gate.

        Reviews are append-only events on a delivered product. They remain bound
        to the exact shipped artifact, Instructions, and carrier record.
        """

        runtime = self._runtime()
        runtime.get_product(product_id)
        if not runtime.verify_event_chain(product_id):
            raise ContractError("Workshop event chain is not trustworthy")
        return _reviews_from_events(runtime, product_id)

    def review_learnings(self, product_id: str) -> Tuple[Mapping[str, Any], ...]:
        """Expose review-backed input for a *future* Make.

        These records deliberately have no ``invalidates`` field: a customer
        Review cannot reopen, revise, or replace a product that was shipped.
        """

        return tuple(
            {
                "source": "customer-review",
                "review_id": review.review_id,
                "rating": review.rating,
                "feedback": review.feedback,
                "observed_at": review.observed_at,
                "source_artifact_sha256": review.product_artifact_sha256,
                "source_instructions_sha256": review.instructions_sha256,
                "applies_to": "future-make",
                "delivered_revision_immutable": True,
            }
            for review in self.reviews(product_id)
        )

    def record_review(
        self, product_id: str, review: CustomerReview
    ) -> CustomerReview:
        """Append customer feedback after Deliver while preserving shipped bytes.

        ``review_id`` is idempotent. Repeating the same record succeeds; reusing
        its ID for different feedback is rejected. The product remains in
        Deliver, so Reviews never become a sixth inventor hook or release gate.
        """

        if not isinstance(review, CustomerReview):
            raise ContractError("record_review requires a CustomerReview")
        runtime = self._runtime()
        runtime.get_product(product_id)
        lease = runtime.acquire_lease(product_id, "workshop-reviews")
        try:
            if not runtime.verify_event_chain(product_id):
                raise ContractError("Workshop event chain is not trustworthy")
            product = runtime.get_product(product_id)
            if product["stage"] != "deliver":
                raise ContractError("customer Reviews may be recorded only after Deliver")
            delivered = _delivery_from_events(runtime, product_id)
            if product.get("artifact_sha256") != delivered.product_artifact_sha256:
                raise ContractError(
                    "delivered product state identifies different artifact bytes"
                )
            review.assert_delivery(delivered)
            if _utc_instant(review.observed_at) < _utc_instant(delivered.observed_at):
                raise ContractError("customer Review cannot predate Deliver")

            for existing in _reviews_from_events(runtime, product_id):
                if existing.review_id != review.review_id:
                    continue
                if existing.to_dict() != review.to_dict():
                    raise ContractError(
                        "customer review_id is already bound to different feedback"
                    )
                return existing

            if self.review_authenticator is None:
                raise ContractError(
                    "customer Reviews require a configured order/reviewer authenticator"
                )
            authentication = self.review_authenticator(delivered, review)
            if not isinstance(authentication, ReviewAuthentication):
                raise ContractError(
                    "Review authenticator must return ReviewAuthentication"
                )
            authentication.assert_review(review, delivered)

            self._advance(
                runtime,
                product_id,
                "deliver",
                artifact_sha256=delivered.product_artifact_sha256,
                payload={
                    "status": "delivered",
                    "customer_review": review.to_dict(),
                    "customer_review_authentication": authentication.to_dict(),
                    "review_learning": {
                        "applies_to": "future-make",
                        "delivered_revision_immutable": True,
                    },
                },
                lease_token=lease,
            )
            return review
        finally:
            runtime.release_lease(product_id, lease)

    @staticmethod
    def _advance(
        runtime: Runtime,
        product_id: str,
        to_job: str,
        *,
        artifact_sha256: Optional[str],
        payload: Mapping[str, Any],
        lease_token: Any,
    ) -> Mapping[str, Any]:
        product = runtime.get_product(product_id)
        source = product["stage"]
        legal = {
            "wish": ("invent",),
            "invent": ("invent", "make"),
            "make": ("make", "playtest"),
            "playtest": ("playtest", "make", "instructions"),
            "instructions": ("instructions", "deliver"),
            "deliver": ("deliver",),
        }
        if to_job not in legal.get(source, ()):
            raise ContractError("illegal Workshop job move %s -> %s" % (source, to_job))
        return runtime._transition(
            product_id,
            source,
            to_job,
            product["revision"],
            artifact_sha256,
            dict(payload),
            _lease_token(lease_token),
        )

    def _wait(
        self,
        runtime: Runtime,
        wish: Wish,
        job: str,
        round_number: int,
        waiting: WaitingFor,
        lease_token: Any,
        playtest_rounds: int,
        *,
        artifact_sha256: Optional[str] = None,
        instructions_sha256: Optional[str] = None,
        page_url: Optional[str] = None,
        invented: Optional[Invented] = None,
        checkpoint_refs: Optional[Mapping[str, Any]] = None,
        instructions_workspace: Optional[Path] = None,
    ) -> WorkshopRun:
        if any(need.job != job for need in waiting.needs):
            raise ContractError("waiting capability belongs to a different Workshop job")
        wait_payload: dict[str, Any] = {
            "status": "waiting",
            "round": round_number,
            "needs": [need.to_dict() for need in waiting.needs],
        }
        if checkpoint_refs is not None:
            allowed = {
                "made_checkpoint_path",
                "made_checkpoint_sha256",
                "made_checkpoint_round",
                "playtested_checkpoint_path",
                "playtested_checkpoint_sha256",
                "playtested_checkpoint_round",
            }
            if not set(checkpoint_refs) <= allowed:
                raise ContractError("Workshop wait checkpoint references are malformed")
            wait_payload.update(dict(checkpoint_refs))
        if job == "instructions":
            run_root = _workshop_run_root(
                self.runtime_root, wish.product_id, create=False
            )
            approval_event = next(
                (
                    event
                    for event in reversed(runtime.events(wish.product_id))
                    if event.get("from_stage") == "playtest"
                    and event.get("to_stage") == "instructions"
                    and isinstance(event.get("payload"), Mapping)
                    and event["payload"].get("resume_checkpoint_sha256")
                ),
                None,
            )
            if approval_event is None:
                raise ContractError(
                    "Instructions wait has no approved Playtest checkpoint"
                )
            _, checkpoint_sha256 = _read_instructions_checkpoint(
                run_root, approval_event
            )
            wait_payload["resume_checkpoint_sha256"] = checkpoint_sha256
            approval_payload = approval_event["payload"]
            if approval_payload.get("instructions_checkpoint_path") is not None:
                wait_payload.update(
                    {
                        "instructions_checkpoint_path": approval_payload[
                            "instructions_checkpoint_path"
                        ],
                        "instructions_checkpoint_sha256": checkpoint_sha256,
                        "instructions_checkpoint_round": approval_payload.get(
                            "instructions_checkpoint_round",
                            approval_payload.get("round"),
                        ),
                    }
                )
            instructions_root = (
                Path(instructions_workspace)
                if instructions_workspace is not None
                else run_root / "instructions"
            )
            if instructions_root.exists() and not instructions_root.is_symlink():
                wait_payload["instructions_root"] = _relative_tree(
                    run_root, instructions_root, "Instructions workspace"
                )
            manifest_path = run_root / INSTRUCTIONS_MANIFEST_FILENAME
            if instructions_root.parent != run_root or instructions_root.name != "instructions":
                manifest_path = instructions_root.parent / (
                    instructions_root.name + "-manifest.json"
                )
            if instructions_root.exists():
                if instructions_root.is_symlink() or not instructions_root.is_dir():
                    raise ContractError("Instructions workspace must be a regular directory")
                if any(instructions_root.iterdir()):
                    manifest = sealed_instructions_manifest(instructions_root)
                    wait_payload["instructions_sha256"] = manifest.artifact_sha256
                elif manifest_path.exists() or manifest_path.is_symlink():
                    raise ContractError("empty Instructions tree cannot have a seal")
            elif manifest_path.exists() or manifest_path.is_symlink():
                raise ContractError("Instructions seal cannot exist without its tree")
        self._advance(
            runtime,
            wish.product_id,
            job,
            artifact_sha256=artifact_sha256,
            payload=wait_payload,
            lease_token=lease_token,
        )
        return WorkshopRun(
            wish.product_id,
            "waiting",
            job,
            round_number,
            artifact_sha256,
            instructions_sha256,
            waiting.needs,
            playtest_rounds=playtest_rounds,
            page_url=page_url,
            invented=invented,
        )

    def _finish_instructions(
        self,
        runtime: Runtime,
        wish: Wish,
        made: Made,
        product_instructions: ProductInstructions,
        round_number: int,
        playtest_rounds: int,
        lease_token: Any,
        instructions_workspace: Path,
        invented: Optional[Invented] = None,
    ) -> WorkshopRun:
        """Validate Instructions once, then continue through the existing Deliver job."""

        if not isinstance(product_instructions, ProductInstructions):
            raise ContractError("Instructions must return ProductInstructions")
        _inside(
            product_instructions.root,
            instructions_workspace,
            "Instructions result",
        )
        product_instructions.assert_current()
        if product_instructions.product_artifact_sha256 != made.artifact_sha256:
            raise ContractError("Instructions describe different product bytes")
        run_root = _workshop_run_root(
            self.runtime_root, wish.product_id, create=False
        )
        latest = runtime.events(wish.product_id)[-1]
        latest_payload = latest.get("payload")
        expected_root = _relative_tree(
            run_root, product_instructions.root, "Instructions result"
        )
        if (
            latest.get("to_stage") != "instructions"
            or not isinstance(latest_payload, Mapping)
            or latest_payload.get("instructions_root") != expected_root
            or latest_payload.get("instructions_sha256")
            != product_instructions.instructions_sha256
            or latest.get("artifact_sha256") != made.artifact_sha256
        ):
            raise ContractError(
                "Instructions must bind their exact sealed root and hash before the site effect or Deliver"
            )
        self._advance(
            runtime,
            wish.product_id,
            "deliver",
            artifact_sha256=made.artifact_sha256,
            payload={
                "status": "working",
                "round": round_number,
                "instructions_sha256": product_instructions.instructions_sha256,
            },
            lease_token=lease_token,
        )
        deliver_context = DeliverContext(wish, made, product_instructions)
        _lease_token(lease_token)
        try:
            delivered = self.deliver_job(deliver_context)
        except WaitingFor as waiting:
            return self._wait(
                runtime,
                wish,
                "deliver",
                round_number,
                waiting,
                lease_token,
                playtest_rounds,
                artifact_sha256=made.artifact_sha256,
                instructions_sha256=product_instructions.instructions_sha256,
                page_url=product_instructions.page_url,
                invented=invented,
            )
        self.taste.assert_current()
        if not isinstance(delivered, Delivered):
            raise ContractError("Deliver must return Delivered")
        delivered.assert_context(deliver_context)
        self._advance(
            runtime,
            wish.product_id,
            "deliver",
            artifact_sha256=made.artifact_sha256,
            payload={
                "status": "delivered",
                "round": round_number,
                "instructions_sha256": product_instructions.instructions_sha256,
                "delivery": delivered.to_dict(),
            },
            lease_token=lease_token,
        )
        return WorkshopRun(
            wish.product_id,
            "delivered",
            "deliver",
            round_number,
            made.artifact_sha256,
            product_instructions.instructions_sha256,
            delivery=delivered,
            playtest_rounds=playtest_rounds,
            page_url=product_instructions.page_url,
            invented=invented,
        )

    def _resume_state(
        self, runtime: Runtime, wish: Wish
    ) -> tuple[Mapping[str, Any], int, Path, list[Mapping[str, Any]]]:
        """Validate the immutable registration and current event-chain head."""

        if not runtime.verify_event_chain(wish.product_id):
            raise ContractError("Workshop event chain is not trustworthy")
        product = runtime.get_product(wish.product_id)
        metadata = product.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ContractError("persisted Workshop metadata is malformed")
        bindings = _checkpoint_bindings(
            wish,
            self.inventor_id,
            self.taste.sha256,
            self.blueprint,
            self.customization_level,
            metadata.get("playtest_rounds"),
        )
        bindings = {
            key: value for key, value in bindings.items() if key != "product_id"
        }
        if any(metadata.get(key) != value for key, value in bindings.items()):
            if metadata.get("wish") != wish.to_dict():
                raise ContractError("resume Wish differs from the original Wish")
            raise ContractError(
                "resume Workshop has different inventor identity, Taste, blueprint, lane, customization, or allowance"
            )
        selected_rounds = metadata.get("playtest_rounds")
        if type(selected_rounds) is not int or not 1 <= selected_rounds <= 100:
            raise ContractError("persisted Playtest round allowance is malformed")
        run_root = _workshop_run_root(
            self.runtime_root, wish.product_id, create=False
        )
        events = runtime.events(wish.product_id)
        if not events or events[-1].get("to_stage") != product.get("stage"):
            raise ContractError("persisted Workshop state has no authoritative event")
        latest_payload = events[-1].get("payload")
        if not isinstance(latest_payload, Mapping):
            raise ContractError("persisted Workshop state payload is malformed")
        return product, selected_rounds, run_root, events

    def _assert_checkpoint_bindings(
        self,
        payload: Mapping[str, Any],
        wish: Wish,
        selected_rounds: int,
        round_number: int,
    ) -> None:
        expected = _checkpoint_bindings(
            wish,
            self.inventor_id,
            self.taste.sha256,
            self.blueprint,
            self.customization_level,
            selected_rounds,
        )
        if any(payload.get(key) != value for key, value in expected.items()):
            raise ContractError(
                "checkpoint differs from the original Workshop bindings"
            )
        if payload.get("round") != round_number:
            raise ContractError("checkpoint belongs to a different Playtest round")

    def _accepted_invented(
        self,
        events: list[Mapping[str, Any]],
        wish: Wish,
        run_root: Path,
    ) -> Invented:
        event = next(
            (
                item
                for item in reversed(events)
                if item.get("from_stage") == "invent"
                and item.get("to_stage") == "make"
                and isinstance(item.get("payload"), Mapping)
                and "invented" in item["payload"]
            ),
            None,
        )
        if event is None:
            raise ContractError("Make resume has no accepted Invent result")
        payload = event["payload"]
        invented = _invented_from_dict(payload["invented"])
        invented.assert_context(
            InventContext(wish, self.taste, self.blueprint, run_root / "invent")
        )
        if not invented.passed:
            raise ContractError("persisted Invent result did not reach its target score")
        if (
            payload.get("round") != 1
            or payload.get("concept_sha256") != invented.concept_sha256
            or payload.get("invent_score") != invented.score
            or payload.get("invent_target_score") != invented.target_score
        ):
            raise ContractError("accepted Invent event identifies different concept bytes")
        return invented

    def _feedback_for_make(
        self,
        events: list[Mapping[str, Any]],
        wish: Wish,
        run_root: Path,
        selected_rounds: int,
        round_number: int,
    ) -> tuple[Feedback, ...]:
        if round_number == 1:
            return ()
        event = next(
            (
                item
                for item in reversed(events)
                if item.get("from_stage") == "playtest"
                and item.get("to_stage") == "make"
                and isinstance(item.get("payload"), Mapping)
                and item["payload"].get("round") == round_number
                and "feedback" in item["payload"]
            ),
            None,
        )
        if event is None:
            raise ContractError(
                "Make resume has no exact Playtest feedback for this round"
            )
        raw_feedback = event["payload"].get("feedback")
        if not isinstance(raw_feedback, list):
            raise ContractError("persisted Make feedback is malformed")
        feedback = tuple(_feedback_from_dict(item) for item in raw_feedback)
        if not feedback or any(
            item.severity not in ("improve", "block") for item in feedback
        ):
            raise ContractError("persisted Make feedback is not actionable")

        # Modern runs bind feedback to the exact returned Playtest. Legacy Make
        # events remain resumable because their typed feedback was already in the
        # append-only event chain before stage checkpoints existed.
        if "playtested_checkpoint_sha256" in event["payload"]:
            checkpoint, _ = _read_stage_checkpoint(run_root, event, "playtested")
            self._assert_checkpoint_bindings(
                checkpoint, wish, selected_rounds, round_number - 1
            )
            made = _rebuild_made_value(run_root, checkpoint.get("made"))
            playtested, _ = _rebuild_playtested_value(
                run_root, checkpoint.get("playtested"), made
            )
            expected = tuple(
                item
                for item in playtested.feedback
                if item.severity in ("improve", "block")
            )
            if expected != feedback or playtested.passed:
                raise ContractError(
                    "Make feedback differs from its exact Playtest checkpoint"
                )
        return feedback

    def _made_from_event(
        self,
        event: Mapping[str, Any],
        wish: Wish,
        run_root: Path,
        selected_rounds: int,
        round_number: int,
    ) -> tuple[Made, Invented, tuple[Feedback, ...], str]:
        payload, digest = _read_stage_checkpoint(run_root, event, "made")
        expected_keys = set(
            _checkpoint_bindings(
                wish,
                self.inventor_id,
                self.taste.sha256,
                self.blueprint,
                self.customization_level,
                selected_rounds,
            )
        ) | {"round", "invented", "input_feedback", "made"}
        if set(payload) != expected_keys:
            raise ContractError("Made checkpoint payload is malformed")
        self._assert_checkpoint_bindings(
            payload, wish, selected_rounds, round_number
        )
        invented = _invented_from_dict(payload["invented"])
        invented.assert_context(
            InventContext(wish, self.taste, self.blueprint, run_root / "invent")
        )
        if not invented.passed:
            raise ContractError("Made checkpoint cites an unaccepted Invent result")
        raw_feedback = payload["input_feedback"]
        if not isinstance(raw_feedback, list):
            raise ContractError("Made checkpoint input feedback is malformed")
        feedback = tuple(_feedback_from_dict(item) for item in raw_feedback)
        made = _rebuild_made_value(run_root, payload["made"])
        if made.product.get("lane") != self.lane:
            raise ContractError("Made checkpoint belongs to a different lane")
        event_payload = event.get("payload")
        assert isinstance(event_payload, Mapping)
        if (
            event.get("artifact_sha256") != made.artifact_sha256
            or event_payload.get("artifact_sha256") != made.artifact_sha256
            or event_payload.get("round") != round_number
        ):
            raise ContractError("Made checkpoint differs from its transition event")
        return made, invented, feedback, digest

    @staticmethod
    def _attempt_workspace(
        run_root: Path,
        stage: str,
        round_number: int,
        revision: int,
    ) -> Path:
        """Reserve a never-reused path for one restarted incomplete stage."""

        if stage not in {"invent", "make", "playtest", "instructions"}:
            raise ContractError("unknown Workshop attempt stage")
        attempts = run_root / "attempts"
        _mkdir_durable(attempts)
        for attempt in range(1, 10_000):
            candidate = attempts / (
                "%s-r%03d-rev%04d-attempt%03d"
                % (stage, round_number, revision, attempt)
            )
            try:
                candidate.mkdir(mode=0o700)
            except FileExistsError:
                continue
            os.chmod(candidate, 0o700)
            directory = os.open(
                attempts, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
            # Reserve the namespace atomically, but keep the hook's actual
            # workspace absent so existing contribution contracts may create
            # it themselves. No other attempt can select this private parent.
            return (candidate.resolve(strict=True) / "workspace").absolute()
        raise ContractError("Workshop has exhausted fresh attempt workspaces")

    def _instructions_seal_callback(
        self,
        runtime: Runtime,
        wish: Wish,
        run_root: Path,
        round_number: int,
        lease: LeaseGuard,
        checkpoint_path: str,
        checkpoint_sha256: str,
    ) -> Callable[[Path, ArtifactManifest], None]:
        """Fence and event-bind sealed Instructions before their site effect."""

        def bind(root: Path, manifest: ArtifactManifest) -> None:
            self.taste.assert_current()
            lease.assert_current()
            sealed = sealed_instructions_manifest(root)
            if sealed.to_dict() != manifest.to_dict():
                raise ContractError(
                    "Instructions seal differs from its durable manifest"
                )
            relative_root = _relative_tree(
                run_root, root, "Instructions workspace"
            )
            self._advance(
                runtime,
                wish.product_id,
                "instructions",
                artifact_sha256=runtime.get_product(wish.product_id).get(
                    "artifact_sha256"
                ),
                payload={
                    "status": "working",
                    "phase": "sealed",
                    "round": round_number,
                    "resume_checkpoint_sha256": checkpoint_sha256,
                    "instructions_checkpoint_path": checkpoint_path,
                    "instructions_checkpoint_sha256": checkpoint_sha256,
                    "instructions_checkpoint_round": round_number,
                    "instructions_root": relative_root,
                    "instructions_sha256": manifest.artifact_sha256,
                },
                lease_token=lease,
            )

        return bind

    def _continue_pipeline(
        self,
        runtime: Runtime,
        wish: Wish,
        run_root: Path,
        invented: Invented,
        selected_rounds: int,
        lease: LeaseGuard,
        *,
        start_round: int = 1,
        feedback: tuple[Feedback, ...] = (),
        resumed_made: Optional[Made] = None,
        resumed_made_refs: Optional[Mapping[str, Any]] = None,
    ) -> WorkshopRun:
        """Continue from the first incomplete Make or Playtest stage.

        Accepted prior stages are reconstructed by ``resume`` before entering
        here. A restarted stage begins from its first reward step in a fresh
        attempt workspace; this does not claim mid-loop continuation.
        """

        made = resumed_made
        playtested: Optional[Playtested] = None
        made_refs = dict(resumed_made_refs or {})
        round_number = start_round
        for round_number in range(start_round, selected_rounds + 1):
            if made is None:
                lease.assert_current()
                make_workspace = self._attempt_workspace(
                    run_root,
                    "make",
                    round_number,
                    runtime.get_product(wish.product_id)["revision"],
                )
                make_context = MakeContext(
                    wish,
                    self.taste,
                    self.blueprint,
                    invented,
                    round_number,
                    make_workspace,
                    feedback,
                    selected_rounds,
                    self.inventor_id,
                )
                lease.assert_current()
                try:
                    made = self.make_job(make_context)
                except WaitingFor as waiting:
                    return self._wait(
                        runtime,
                        wish,
                        "make",
                        round_number,
                        waiting,
                        lease,
                        selected_rounds,
                        invented=invented,
                    )
                self.taste.assert_current()
                if not isinstance(made, Made):
                    raise ContractError("Make must return Made")
                _inside(made.artifact_root, make_workspace, "Made artifact")
                made.assert_current()
                if made.product.get("lane") != self.lane:
                    raise ContractError(
                        "Make returned a product for another plaything lane"
                    )
                self.taste.assert_current()

                made_payload = _made_checkpoint_payload(
                    wish,
                    self.inventor_id,
                    self.taste.sha256,
                    self.blueprint,
                    self.customization_level,
                    selected_rounds,
                    round_number,
                    invented,
                    feedback,
                    made,
                    run_root,
                )
                lease.assert_current()
                made_path, made_sha256 = _write_stage_checkpoint(
                    run_root, "made", round_number, made_payload
                )
                made_refs = {
                    "made_checkpoint_path": made_path,
                    "made_checkpoint_sha256": made_sha256,
                    "made_checkpoint_round": round_number,
                }
                self._advance(
                    runtime,
                    wish.product_id,
                    "playtest",
                    artifact_sha256=made.artifact_sha256,
                    payload={
                        "status": "working",
                        "round": round_number,
                        "artifact_sha256": made.artifact_sha256,
                        **made_refs,
                    },
                    lease_token=lease,
                )

            lease.assert_current()
            playtest_workspace = self._attempt_workspace(
                run_root,
                "playtest",
                round_number,
                runtime.get_product(wish.product_id)["revision"],
            )
            playtest_context = PlaytestContext(
                wish,
                self.taste,
                self.blueprint,
                round_number,
                made,
                playtest_workspace,
                selected_rounds,
            )
            lease.assert_current()
            try:
                playtested = self.playtest_job(playtest_context)
            except WaitingFor as waiting:
                return self._wait(
                    runtime,
                    wish,
                    "playtest",
                    round_number,
                    waiting,
                    lease,
                    selected_rounds,
                    artifact_sha256=made.artifact_sha256,
                    invented=invented,
                    checkpoint_refs=made_refs,
                )
            self.taste.assert_current()
            if not isinstance(playtested, Playtested):
                raise ContractError("Playtest must return Playtested")
            playtested.assert_artifact(made.artifact_sha256)
            made.assert_current()

            made_checkpoint_sha256 = made_refs.get("made_checkpoint_sha256")
            if not isinstance(made_checkpoint_sha256, str):
                raise ContractError("Playtest has no exact Made checkpoint")
            playtested_payload = _playtested_checkpoint_payload(
                wish,
                self.inventor_id,
                self.taste.sha256,
                self.blueprint,
                self.customization_level,
                selected_rounds,
                round_number,
                made_checkpoint_sha256,
                made,
                playtested,
                run_root,
                playtest_workspace,
            )
            lease.assert_current()
            playtested_path, playtested_sha256 = _write_stage_checkpoint(
                run_root, "playtested", round_number, playtested_payload
            )
            playtested_refs = {
                "playtested_checkpoint_path": playtested_path,
                "playtested_checkpoint_sha256": playtested_sha256,
                "playtested_checkpoint_round": round_number,
            }
            all_refs = {**made_refs, **playtested_refs}

            if playtested.passed:
                evidence_root = (
                    made.artifact_root
                    if playtested.evidence.evidence_manifest.to_dict()
                    == made.artifact_manifest.to_dict()
                    else playtest_workspace
                )
                policy_needs = _playtest_policy_needs(
                    self.blueprint, made, playtested, evidence_root
                )
                if policy_needs:
                    return self._wait(
                        runtime,
                        wish,
                        "playtest",
                        round_number,
                        WaitingFor(*policy_needs),
                        lease,
                        selected_rounds,
                        artifact_sha256=made.artifact_sha256,
                        invented=invented,
                        checkpoint_refs=all_refs,
                    )
                checkpoint_payload = _instructions_checkpoint_payload(
                    wish,
                    self.inventor_id,
                    self.taste.sha256,
                    self.blueprint,
                    self.customization_level,
                    selected_rounds,
                    round_number,
                    made,
                    playtested,
                    run_root,
                    playtest_workspace,
                )
                lease.assert_current()
                checkpoint_path, checkpoint_sha256 = _write_instructions_checkpoint(
                    run_root, round_number, checkpoint_payload
                )
                self._advance(
                    runtime,
                    wish.product_id,
                    "instructions",
                    artifact_sha256=made.artifact_sha256,
                    payload={
                        "status": "working",
                        "round": round_number,
                        "evidence_artifact_sha256": (
                            playtested.evidence.evidence_artifact_sha256
                        ),
                        "resume_checkpoint_sha256": checkpoint_sha256,
                        "instructions_checkpoint_path": checkpoint_path,
                        "instructions_checkpoint_sha256": checkpoint_sha256,
                        "instructions_checkpoint_round": round_number,
                        **all_refs,
                    },
                    lease_token=lease,
                )
                break

            feedback = tuple(
                item
                for item in playtested.feedback
                if item.severity in ("improve", "block")
            )
            if not feedback:
                raise ContractError(
                    "a failed Playtest must return actionable improve or block feedback"
                )
            if round_number == selected_rounds:
                self._advance(
                    runtime,
                    wish.product_id,
                    "playtest",
                    artifact_sha256=made.artifact_sha256,
                    payload={
                        "status": "stopped",
                        "round": round_number,
                        "feedback": [item.to_dict() for item in feedback],
                        **all_refs,
                    },
                    lease_token=lease,
                )
                return WorkshopRun(
                    wish.product_id,
                    "stopped",
                    "playtest",
                    round_number,
                    made.artifact_sha256,
                    playtest_rounds=selected_rounds,
                    invented=invented,
                )
            self._advance(
                runtime,
                wish.product_id,
                "make",
                artifact_sha256=made.artifact_sha256,
                payload={
                    "status": "working",
                    "round": round_number + 1,
                    "feedback": [item.to_dict() for item in feedback],
                    **all_refs,
                },
                lease_token=lease,
            )
            made = None
            made_refs = {}

        if made is None or playtested is None or not playtested.passed:
            raise ContractError("Workshop ended without an approved Make")
        instructions_workspace = (run_root / "instructions").absolute()
        instructions_context = InstructionsContext(
            wish,
            self.taste,
            self.blueprint,
            made,
            playtested,
            instructions_workspace,
            lease.token,
            self._instructions_seal_callback(
                runtime,
                wish,
                run_root,
                round_number,
                lease,
                checkpoint_path,
                checkpoint_sha256,
            ),
        )
        lease.assert_current()
        try:
            product_instructions = self.instructions_job(instructions_context)
        except WaitingFor as waiting:
            return self._wait(
                runtime,
                wish,
                "instructions",
                round_number,
                waiting,
                lease,
                selected_rounds,
                artifact_sha256=made.artifact_sha256,
                invented=invented,
                instructions_workspace=instructions_workspace,
            )
        self.taste.assert_current()
        return self._finish_instructions(
            runtime,
            wish,
            made,
            product_instructions,
            round_number,
            selected_rounds,
            lease,
            instructions_workspace,
            invented,
        )

    def resume(self, wish: Wish) -> WorkshopRun:
        """Continue the first incomplete Workshop stage from exact durable state.

        Resume never reruns an accepted prior stage. It restarts only the
        incomplete Invent, Make, or Playtest reward loop in a fresh workspace.
        Instructions keeps its separate sealed-page reconciliation. Stopped and
        physically effectful Deliver states deliberately fail closed.
        """

        if not isinstance(wish, Wish):
            raise ContractError("Workshop.resume requires a Wish")
        wish.assert_valid()
        self.taste.assert_current()
        runtime = self._runtime()
        product = runtime.get_product(wish.product_id)
        if product["stage"] == "wish":
            metadata = product.get("metadata")
            if not isinstance(metadata, Mapping):
                raise ContractError("persisted Workshop metadata is malformed")
            selected_rounds = metadata.get("playtest_rounds")
            if type(selected_rounds) is not int or not 1 <= selected_rounds <= 100:
                raise ContractError("persisted Playtest round allowance is malformed")
            return self.run(wish, playtest_rounds=selected_rounds)
        if product["stage"] == "instructions":
            return self.resume_instructions(wish)
        if product["stage"] in {"deliver"}:
            raise ContractError(
                "Workshop resume does not retry Deliver or delivered physical effects"
            )
        if product["stage"] not in {"invent", "make", "playtest"}:
            raise ContractError(
                "Workshop resume requires an incomplete Invent, Make, Playtest, or Instructions stage"
            )
        requested_stage = product["stage"]

        with LeaseGuard.acquire(
            runtime, wish.product_id, "toy-workshop-resume"
        ) as lease:
            product, selected_rounds, run_root, events = self._resume_state(
                runtime, wish
            )
            stage = product["stage"]
            if stage != requested_stage:
                raise StateConflict(
                    "Workshop stage advanced while resume was acquiring its lease; inspect and resume the new exact stage"
                )
            latest = events[-1]
            latest_payload = latest.get("payload")
            assert isinstance(latest_payload, Mapping)
            status = latest_payload.get("status")
            if status not in {"working", "waiting"}:
                if status == "stopped":
                    raise ContractError(
                        "a stopped Workshop run has exhausted its Playtest allowance"
                    )
                raise ContractError(
                    "Workshop resume requires a working or waiting stage boundary"
                )
            round_number = latest_payload.get("round")
            if (
                type(round_number) is not int
                or round_number < 1
                or round_number > selected_rounds
            ):
                raise ContractError("persisted Workshop round is outside its allowance")

            if stage == "invent":
                if round_number != 1:
                    raise ContractError("Invent resume round must be one")
                lease.assert_current()
                invent_workspace = self._attempt_workspace(
                    run_root, "invent", 1, product["revision"]
                )
                invent_context = InventContext(
                    wish, self.taste, self.blueprint, invent_workspace
                )
                lease.assert_current()
                try:
                    invented = self.invent_job(invent_context)
                except WaitingFor as waiting:
                    return self._wait(
                        runtime,
                        wish,
                        "invent",
                        1,
                        waiting,
                        lease,
                        selected_rounds,
                    )
                self.taste.assert_current()
                if not isinstance(invented, Invented):
                    raise ContractError("Invent must return Invented")
                invented.assert_context(invent_context)
                if not invented.passed:
                    return self._wait(
                        runtime,
                        wish,
                        "invent",
                        1,
                        WaitingFor(
                            Need(
                                "invent",
                                "industrial-design-target-score",
                                "The chosen concept has not reached its Invent reward target.",
                                "Continue the self-improving Invent loop, then return an Invented record at or above its target score.",
                            )
                        ),
                        lease,
                        selected_rounds,
                    )
                self._advance(
                    runtime,
                    wish.product_id,
                    "make",
                    artifact_sha256=None,
                    payload={
                        "status": "working",
                        "round": 1,
                        "concept_sha256": invented.concept_sha256,
                        "invent_score": invented.score,
                        "invent_target_score": invented.target_score,
                        "invented": invented.to_dict(),
                    },
                    lease_token=lease,
                )
                return self._continue_pipeline(
                    runtime,
                    wish,
                    run_root,
                    invented,
                    selected_rounds,
                    lease,
                )

            invented = self._accepted_invented(events, wish, run_root)
            if stage == "make":
                feedback = self._feedback_for_make(
                    events,
                    wish,
                    run_root,
                    selected_rounds,
                    round_number,
                )
                return self._continue_pipeline(
                    runtime,
                    wish,
                    run_root,
                    invented,
                    selected_rounds,
                    lease,
                    start_round=round_number,
                    feedback=feedback,
                )

            made_event = next(
                (
                    item
                    for item in reversed(events)
                    if item.get("from_stage") == "make"
                    and item.get("to_stage") == "playtest"
                    and isinstance(item.get("payload"), Mapping)
                    and item["payload"].get("round") == round_number
                    and "made_checkpoint_sha256" in item["payload"]
                ),
                None,
            )
            if made_event is None:
                raise ContractError(
                    "Playtest resume has no exact Made checkpoint; restart this legacy product as a new Wish"
                )
            made_event_payload = made_event["payload"]
            assert isinstance(made_event_payload, Mapping)
            expected_made_refs = {
                "made_checkpoint_path": made_event_payload.get(
                    "made_checkpoint_path"
                ),
                "made_checkpoint_sha256": made_event_payload.get(
                    "made_checkpoint_sha256"
                ),
                "made_checkpoint_round": made_event_payload.get(
                    "made_checkpoint_round", made_event_payload.get("round")
                ),
            }
            latest_made_refs = {
                key: latest_payload.get(key) for key in expected_made_refs
            }
            if latest_made_refs != expected_made_refs:
                raise ContractError(
                    "latest Playtest state cites a different Made checkpoint"
                )
            made, checkpoint_invented, checkpoint_feedback, made_digest = (
                self._made_from_event(
                    made_event,
                    wish,
                    run_root,
                    selected_rounds,
                    round_number,
                )
            )
            if checkpoint_invented.to_dict() != invented.to_dict():
                raise ContractError("Made checkpoint cites a different Invent result")
            expected_feedback = self._feedback_for_make(
                events,
                wish,
                run_root,
                selected_rounds,
                round_number,
            )
            if checkpoint_feedback != expected_feedback:
                raise ContractError(
                    "Made checkpoint cites different Playtest input feedback"
                )
            if product.get("artifact_sha256") != made.artifact_sha256:
                raise ContractError("Playtest state identifies different Made bytes")

            # If Playtest already returned but common release policy held it,
            # verify that returned checkpoint before allowing any hook to run.
            if "playtested_checkpoint_sha256" in latest_payload:
                completed, completed_digest = _read_stage_checkpoint(
                    run_root, latest, "playtested"
                )
                expected_keys = set(
                    _checkpoint_bindings(
                        wish,
                        self.inventor_id,
                        self.taste.sha256,
                        self.blueprint,
                        self.customization_level,
                        selected_rounds,
                    )
                ) | {
                    "round",
                    "made_checkpoint_sha256",
                    "made",
                    "playtested",
                }
                if set(completed) != expected_keys:
                    raise ContractError("Playtested checkpoint payload is malformed")
                self._assert_checkpoint_bindings(
                    completed, wish, selected_rounds, round_number
                )
                if completed.get("made_checkpoint_sha256") != made_digest:
                    raise ContractError(
                        "Playtested checkpoint cites a different Made checkpoint"
                    )
                completed_made = _rebuild_made_value(
                    run_root, completed.get("made")
                )
                if (
                    completed_made.artifact_manifest.to_dict()
                    != made.artifact_manifest.to_dict()
                    or completed_made.product != made.product
                ):
                    raise ContractError(
                        "Playtested checkpoint contains different Made bytes"
                    )
                _rebuild_playtested_value(
                    run_root, completed.get("playtested"), completed_made
                )
                if latest_payload.get("playtested_checkpoint_sha256") != completed_digest:
                    raise ContractError(
                        "Playtested waiting state identifies different checkpoint bytes"
                    )
            made_refs = {
                "made_checkpoint_path": made_event_payload["made_checkpoint_path"],
                "made_checkpoint_sha256": made_event_payload[
                    "made_checkpoint_sha256"
                ],
                "made_checkpoint_round": round_number,
            }
            return self._continue_pipeline(
                runtime,
                wish,
                run_root,
                invented,
                selected_rounds,
                lease,
                start_round=round_number,
                feedback=expected_feedback,
                resumed_made=made,
                resumed_made_refs=made_refs,
            )

    def resume_instructions(self, wish: Wish) -> WorkshopRun:
        """Resume one exact run at Instructions, without Make or Playtest.

        A content-addressed checkpoint reconstructs the already approved revision.
        If local Instructions were sealed before the wait, only the resumable site
        portion may run; media and copy are never regenerated or overwritten.
        """

        if not isinstance(wish, Wish):
            raise ContractError("Workshop.resume_instructions requires a Wish")
        wish.assert_valid()
        self.taste.assert_current()
        runtime = self._runtime()
        product = runtime.get_product(wish.product_id)
        if product["stage"] != "instructions":
            raise ContractError(
                "resume_instructions requires a run waiting at Instructions"
            )
        lease = LeaseGuard.acquire(
            runtime,
            wish.product_id, "toy-workshop-instructions-resume"
        )
        try:
            product = runtime.get_product(wish.product_id)
            if product["stage"] != "instructions":
                raise ContractError(
                    "resume_instructions requires a run waiting at Instructions"
                )
            if not runtime.verify_event_chain(wish.product_id):
                raise ContractError("Workshop event chain is not trustworthy")
            metadata = product.get("metadata")
            if not isinstance(metadata, Mapping):
                raise ContractError("persisted Workshop metadata is malformed")
            required_metadata = {
                "wish",
                "inventor_id",
                "taste_sha256",
                "blueprint_sha256",
                "lane",
                "customization_level",
                "playtest_rounds",
            }
            if not required_metadata <= set(metadata):
                raise ContractError("persisted Workshop bindings are incomplete")
            if metadata["wish"] != wish.to_dict():
                raise ContractError("resume Wish differs from the original Wish")
            expected_bindings = {
                "inventor_id": self.inventor_id,
                "taste_sha256": self.taste.sha256,
                "blueprint_sha256": self.blueprint.sha256,
                "lane": self.lane,
                "customization_level": self.customization_level,
            }
            if any(metadata.get(key) != value for key, value in expected_bindings.items()):
                raise ContractError(
                    "resume Workshop has different inventor identity, Taste, blueprint, lane, or customization"
                )
            selected_rounds = metadata["playtest_rounds"]
            if type(selected_rounds) is not int or not 1 <= selected_rounds <= 100:
                raise ContractError("persisted Playtest round allowance is malformed")

            run_root = _workshop_run_root(
                self.runtime_root, wish.product_id, create=False
            )
            events = runtime.events(wish.product_id)
            latest = events[-1]
            checkpoint, checkpoint_sha256 = _read_instructions_checkpoint(
                run_root, latest
            )
            if set(checkpoint) != {
                "product_id",
                "inventor_id",
                "wish",
                "taste_sha256",
                "blueprint_sha256",
                "lane",
                "customization_level",
                "playtest_rounds",
                "round",
                "made",
                "playtested",
            }:
                raise ContractError("Instructions resume checkpoint bindings are malformed")
            checkpoint_bindings = {
                "product_id": wish.product_id,
                "inventor_id": self.inventor_id,
                "wish": wish.to_dict(),
                "taste_sha256": self.taste.sha256,
                "blueprint_sha256": self.blueprint.sha256,
                "lane": self.lane,
                "customization_level": self.customization_level,
                "playtest_rounds": selected_rounds,
            }
            if any(
                checkpoint.get(key) != value
                for key, value in checkpoint_bindings.items()
            ):
                raise ContractError(
                    "Instructions checkpoint differs from the original Workshop bindings"
                )
            round_number = checkpoint["round"]
            if (
                type(round_number) is not int
                or round_number < 1
                or round_number > selected_rounds
            ):
                raise ContractError("Instructions checkpoint round is outside its allowance")

            latest_payload = latest.get("payload")
            if (
                latest.get("to_stage") != "instructions"
                or not isinstance(latest_payload, Mapping)
                or latest_payload.get("status") not in {"working", "waiting"}
                or latest_payload.get("round") != round_number
                or latest_payload.get("resume_checkpoint_sha256")
                != checkpoint_sha256
            ):
                raise ContractError(
                    "resume_instructions requires the latest state to be this exact Instructions checkpoint"
                )
            approval_event = next(
                (
                    event
                    for event in reversed(events)
                    if event.get("from_stage") == "playtest"
                    and event.get("to_stage") == "instructions"
                    and isinstance(event.get("payload"), Mapping)
                    and event["payload"].get("resume_checkpoint_sha256")
                    == checkpoint_sha256
                ),
                None,
            )
            if approval_event is None:
                raise ContractError(
                    "Instructions checkpoint is not bound to an approved Playtest event"
                )
            made, playtested, evidence_root = _rebuild_checkpoint_results(
                run_root, checkpoint
            )
            if not playtested.passed or _playtest_policy_needs(
                self.blueprint, made, playtested, evidence_root
            ):
                raise ContractError("checkpoint no longer satisfies Playtest policy")
            if (
                product.get("artifact_sha256") != made.artifact_sha256
                or latest.get("artifact_sha256") != made.artifact_sha256
                or approval_event.get("artifact_sha256") != made.artifact_sha256
                or approval_event["payload"].get("round") != round_number
                or approval_event["payload"].get("evidence_artifact_sha256")
                != playtested.evidence.evidence_artifact_sha256
            ):
                raise ContractError(
                    "persisted Instructions state identifies different Make or Playtest bytes"
                )

            status = latest_payload["status"]
            bound_working_seal = (
                status == "working"
                and latest_payload.get("phase") == "sealed"
                and isinstance(latest_payload.get("instructions_root"), str)
                and isinstance(latest_payload.get("instructions_sha256"), str)
            )
            if (
                (status == "waiting" or bound_working_seal)
                and latest_payload.get("instructions_root")
            ):
                instructions_workspace = _checkpoint_tree(
                    run_root,
                    latest_payload["instructions_root"],
                    "Instructions",
                )
            else:
                instructions_workspace = (run_root / "instructions").absolute()
            seal_callback = None
            if bound_working_seal:
                manifest = sealed_instructions_manifest(instructions_workspace)
                if latest_payload.get("instructions_sha256") != manifest.artifact_sha256:
                    raise ContractError(
                        "bound Instructions seal differs from its working event"
                    )
                resume_job = getattr(self.instructions_job, "resume", None)
                if not callable(resume_job):
                    raise ContractError(
                        "bound Instructions require a job with resume(context) support"
                    )
                operation = resume_job
            elif status == "working":
                # No Instructions output is event-bound yet. Sealed, partial,
                # and empty trees are all untrusted crash orphans; leave them
                # untouched and restart only this incomplete stage elsewhere.
                if instructions_workspace.exists() and (
                    instructions_workspace.is_symlink()
                    or not instructions_workspace.is_dir()
                ):
                    raise ContractError("Instructions workspace must be a regular directory")
                lease.assert_current()
                instructions_workspace = self._attempt_workspace(
                    run_root,
                    "instructions",
                    round_number,
                    product["revision"],
                )
                operation = self.instructions_job
            else:
                tree_is_nonempty = False
                if instructions_workspace.exists():
                    if (
                        instructions_workspace.is_symlink()
                        or not instructions_workspace.is_dir()
                    ):
                        raise ContractError(
                            "Instructions workspace must be a regular directory"
                        )
                    tree_is_nonempty = any(instructions_workspace.iterdir())
                manifest_path = instructions_workspace.parent / (
                    instructions_workspace.name + "-manifest.json"
                )
                manifest_exists = manifest_path.exists() or manifest_path.is_symlink()
                if tree_is_nonempty:
                    manifest = sealed_instructions_manifest(instructions_workspace)
                    if latest_payload.get("instructions_sha256") != manifest.artifact_sha256:
                        raise ContractError(
                            "sealed Instructions identity differs from its waiting event"
                        )
                    resume_job = getattr(self.instructions_job, "resume", None)
                    if not callable(resume_job):
                        raise ContractError(
                            "sealed Instructions require a job with resume(context) support"
                        )
                    operation = resume_job
                else:
                    if latest_payload.get("instructions_sha256") is not None:
                        raise ContractError(
                            "waiting event cites sealed Instructions that are missing"
                        )
                    if manifest_exists:
                        raise ContractError(
                            "Instructions seal exists without a sealed tree"
                        )
                    operation = self.instructions_job
            if operation is self.instructions_job:
                approval_payload = approval_event["payload"]
                if approval_payload.get("instructions_checkpoint_path") is not None:
                    seal_callback = self._instructions_seal_callback(
                        runtime,
                        wish,
                        run_root,
                        round_number,
                        lease,
                        approval_payload["instructions_checkpoint_path"],
                        checkpoint_sha256,
                    )
            instructions_context = InstructionsContext(
                wish,
                self.taste,
                self.blueprint,
                made,
                playtested,
                instructions_workspace,
                lease.token,
                seal_callback,
            )
            lease.assert_current()
            try:
                product_instructions = operation(instructions_context)
            except WaitingFor as waiting:
                return self._wait(
                    runtime,
                    wish,
                    "instructions",
                    round_number,
                    waiting,
                    lease,
                    selected_rounds,
                    artifact_sha256=made.artifact_sha256,
                    instructions_workspace=instructions_workspace,
                )
            self.taste.assert_current()
            return self._finish_instructions(
                runtime,
                wish,
                made,
                product_instructions,
                round_number,
                selected_rounds,
                lease,
                instructions_workspace,
            )
        finally:
            lease.__exit__(*sys.exc_info())

    def run(
        self, wish: Wish, *, playtest_rounds: Optional[int] = None
    ) -> WorkshopRun:
        """Start one product and run until delivered, waiting, or bounded stop."""

        if not isinstance(wish, Wish):
            raise ContractError("Workshop.run requires a Wish")
        wish.assert_valid()
        selected_rounds = self.max_rounds if playtest_rounds is None else playtest_rounds
        if type(selected_rounds) is not int or not 1 <= selected_rounds <= 100:
            raise ContractError("playtest_rounds must be an integer from 1 to 100")
        self.taste.assert_current()
        runtime = self._runtime()
        registration = {
            "wish": wish.to_dict(),
            "inventor_id": self.inventor_id,
            "taste_sha256": self.taste.sha256,
            "blueprint_sha256": self.blueprint.sha256,
            "lane": self.lane,
            "customization_level": self.customization_level,
            "playtest_rounds": selected_rounds,
        }
        try:
            runtime.register_product(wish.product_id, "wish", registration)
        except StateConflict as exc:
            product = runtime.get_product(wish.product_id)
            events = runtime.events(wish.product_id)
            if (
                not runtime.verify_event_chain(wish.product_id)
                or product.get("stage") != "wish"
                or product.get("revision") != 0
                or product.get("artifact_sha256") is not None
                or product.get("metadata") != registration
                or len(events) != 1
                or events[0].get("kind") != "registered"
                or events[0].get("from_stage") is not None
                or events[0].get("to_stage") != "wish"
                or events[0].get("payload") != registration
            ):
                raise ContractError(
                    "existing Workshop product is not this exact registered Wish boundary"
                ) from exc
        with LeaseGuard.acquire(runtime, wish.product_id, "toy-workshop") as lease:
            run_root = _workshop_run_root(
                self.runtime_root, wish.product_id, create=True
            )
            self._advance(
                runtime,
                wish.product_id,
                "invent",
                artifact_sha256=None,
                payload={"status": "working", "round": 1},
                lease_token=lease,
            )

            lease.assert_current()
            invent_workspace = self._attempt_workspace(
                run_root,
                "invent",
                1,
                runtime.get_product(wish.product_id)["revision"],
            )
            invent_context = InventContext(
                wish,
                self.taste,
                self.blueprint,
                invent_workspace,
            )
            lease.assert_current()
            try:
                invented = self.invent_job(invent_context)
            except WaitingFor as waiting:
                return self._wait(
                    runtime,
                    wish,
                    "invent",
                    1,
                    waiting,
                    lease,
                    selected_rounds,
                )
            self.taste.assert_current()
            if not isinstance(invented, Invented):
                raise ContractError("Invent must return Invented")
            invented.assert_context(invent_context)
            if not invented.passed:
                return self._wait(
                    runtime,
                    wish,
                    "invent",
                    1,
                    WaitingFor(
                        Need(
                            "invent",
                            "industrial-design-target-score",
                            "The chosen concept has not reached its Invent reward target.",
                            "Continue the self-improving Invent loop, then return an Invented record at or above its target score.",
                        )
                    ),
                    lease,
                    selected_rounds,
                )
            self._advance(
                runtime,
                wish.product_id,
                "make",
                artifact_sha256=None,
                payload={
                    "status": "working",
                    "round": 1,
                    "concept_sha256": invented.concept_sha256,
                    "invent_score": invented.score,
                    "invent_target_score": invented.target_score,
                    "invented": invented.to_dict(),
                },
                lease_token=lease,
            )
            return self._continue_pipeline(
                runtime,
                wish,
                run_root,
                invented,
                selected_rounds,
                lease,
            )


# Compatibility imports for callers that used this module as the old offline
# demo location. They are not part of the six-job design.
from .offline import (  # noqa: E402,F401
    OfflineInspector,
    OfflineMaker,
    OfflineMuse,
    OfflineProvingGround,
    offline_forge,
    offline_workbench,
)


__all__ = [
    "CUSTOMIZATION_LEVELS",
    "DeliverJob",
    "InstructionsJob",
    "InventJob",
    "MakeJob",
    "PlaytestJob",
    "Workshop",
    "WorkshopTools",
    "offline_workbench",
]
