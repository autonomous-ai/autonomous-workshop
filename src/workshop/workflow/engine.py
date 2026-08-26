"""The Toy Workshop pipeline and its three inventor customization levels.

An inventor supplies Taste and may replace Make, or Make and Playtest. Invent is
the industrial-design stage that selects a concept; Make is the mechanical and
3D-design stage that engineers it. The Workshop always owns the loops, exact
artifact identity, Release, Deliver, and truthful waiting for capabilities
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
import tempfile
from typing import Any, Callable, Mapping, Optional, Tuple

from workshop.artifacts.core import ArtifactEntry, ArtifactManifest, build_artifact_manifest
from workshop.make.cad import (
    CadPart,
    CadProjectManifest,
    CadReleaseBundle,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
)
from workshop.deliver.service import DefaultDeliver
from workshop.release.service import (
    DefaultRelease,
    RELEASE_MANIFEST_FILENAME,
    sealed_release_manifest,
)
from workshop.errors import ContractError
from workshop.deliver.contracts import DeliverContext, Delivered
from workshop.release.contracts import ReleaseContext, ProductRelease
from workshop.invent.contracts import InventContext, Invented
from workshop.make.contracts import Made, MakeContext
from workshop.outcomes import Need, WaitingFor
from workshop.playtest.contracts import PlaytestContext, Playtested
from workshop.reviews.contracts import CustomerReview
from workshop.workflow.contracts import WorkshopRun
from workshop.wish import Wish
from workshop.contributors import CUSTOMIZATION_LEVELS, load_manifest, load_taste
from workshop.playtest.evidence import PlaytestResult
from workshop.playtest.service import Playtest
from workshop.playtest.release import playtest_release_needs
from workshop.runtime.effects import Runtime
from workshop.reviews.service import ReviewAuthentication, ReviewAuthenticator
from workshop.product import ToyBlueprint, playful_make_request


InventJob = Callable[[InventContext], Invented]
MakeJob = Callable[[MakeContext], Made]
PlaytestJob = Callable[[PlaytestContext], Playtested]
ReleaseJob = Callable[[ReleaseContext], ProductRelease]
DeliverJob = Callable[[DeliverContext], Delivered]

_RELEASE_CHECKPOINT = "release-checkpoint.json"
# The managed CLI supervises an Inventor child for at most 60 minutes. Keep the
# Workshop fence alive slightly longer so a valid late result cannot outlive
# its lease and so no second process can enter during the supervisor's window.
_MANAGED_RUN_LEASE_SECONDS = 65 * 60
_INVENTOR_ID = re.compile(r"^[a-z][a-z0-9-]{1,62}$")


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
            release_sha256=value["release_sha256"],
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
                release_sha256=value["release_sha256"],
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
        raise ContractError("Release checkpoint accepts only finite JSON") from exc


def _write_json_once(path: Path, value: Mapping[str, Any]) -> None:
    """Create one durable checkpoint without ever replacing an earlier identity."""

    if path.exists() or path.is_symlink():
        raise ContractError("Release checkpoint already exists")
    payload = json.dumps(
        value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False
    ) + "\n"
    descriptor, temporary = tempfile.mkstemp(
        prefix=".%s." % path.name, dir=str(path.parent)
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise ContractError("Release checkpoint already exists") from exc
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


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
    path = root / relative
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as exc:
        raise ContractError("checkpoint %s tree is missing or unsafe" % label) from exc
    if resolved.is_symlink() or not resolved.is_dir():
        raise ContractError("checkpoint %s tree must be a regular directory" % label)
    return resolved


def _release_checkpoint_payload(
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
                "Playtest evidence must be sealed from its Workshop workspace to support safe Release resume"
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


def _write_release_checkpoint(run_root: Path, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    document = {
        "schema_version": 1,
        "checkpoint_sha256": digest,
        "payload": payload,
    }
    _write_json_once(run_root / _RELEASE_CHECKPOINT, document)
    return digest


def _read_release_checkpoint(
    run_root: Path,
) -> tuple[Mapping[str, Any], str]:
    path = run_root / _RELEASE_CHECKPOINT
    if path.is_symlink() or not path.is_file():
        raise ContractError("Release resume checkpoint is missing")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(
            "Release resume checkpoint must be valid UTF-8 JSON"
        ) from exc
    if not isinstance(document, Mapping) or set(document) != {
        "schema_version",
        "checkpoint_sha256",
        "payload",
    } or document.get("schema_version") != 1:
        raise ContractError("Release resume checkpoint is malformed")
    payload = document.get("payload")
    if not isinstance(payload, Mapping):
        raise ContractError("Release resume checkpoint payload is malformed")
    digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    if document.get("checkpoint_sha256") != digest:
        raise ContractError("Release resume checkpoint identity changed")
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
    release: Optional[ReleaseJob] = None
    deliver: Optional[DeliverJob] = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.invent, "Workshop Invent"),
            (self.make, "Workshop Make"),
            (self.playtest, "Workshop Playtest"),
            (self.release, "Workshop Release"),
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
    """Run Wish -> Invent -> Make <-> Playtest -> Release -> Deliver.

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
        # The workflow consumes an explicit composition. Application defaults
        # belong to ``workshop.bootstrap`` and must never be imported from this
        # domain engine. Constructor-level hooks remain explicit inventor
        # overrides over the supplied tool set.
        selected_tools = WorkshopTools(
            invent=requested_tools.invent,
            make=make or requested_tools.make,
            playtest=playtest or requested_tools.playtest,
            release=requested_tools.release,
            deliver=requested_tools.deliver,
        )
        self.tools = selected_tools
        self.invent_job: InventJob = selected_tools.invent or _missing_invent
        self.make_job: MakeJob = make or selected_tools.make or _missing_make
        self.playtest_job: PlaytestJob = (
            playtest or selected_tools.playtest or _missing_playtest
        )
        self.release_job: ReleaseJob = (
            selected_tools.release or DefaultRelease()
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
        to the exact shipped artifact, Release, and carrier record.
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
                "source_release_sha256": review.release_sha256,
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
        lease_token: str,
    ) -> Mapping[str, Any]:
        product = runtime.get_product(product_id)
        source = product["stage"]
        legal = {
            "wish": ("invent",),
            "invent": ("invent", "make"),
            "make": ("make", "playtest"),
            "playtest": ("playtest", "make", "release"),
            "release": ("release", "deliver"),
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
            lease_token,
        )

    def _wait(
        self,
        runtime: Runtime,
        wish: Wish,
        job: str,
        round_number: int,
        waiting: WaitingFor,
        lease_token: str,
        playtest_rounds: int,
        *,
        artifact_sha256: Optional[str] = None,
        release_sha256: Optional[str] = None,
        page_url: Optional[str] = None,
        invented: Optional[Invented] = None,
    ) -> WorkshopRun:
        if any(need.job != job for need in waiting.needs):
            raise ContractError("waiting capability belongs to a different Workshop job")
        wait_payload: dict[str, Any] = {
            "status": "waiting",
            "round": round_number,
            "needs": [need.to_dict() for need in waiting.needs],
        }
        if job == "release":
            run_root = self.runtime_root / "runs" / wish.product_id
            _, checkpoint_sha256 = _read_release_checkpoint(run_root)
            wait_payload["resume_checkpoint_sha256"] = checkpoint_sha256
            release_root = run_root / "release"
            manifest_path = run_root / RELEASE_MANIFEST_FILENAME
            if release_root.exists():
                if release_root.is_symlink() or not release_root.is_dir():
                    raise ContractError("Release workspace must be a regular directory")
                if any(release_root.iterdir()):
                    manifest = sealed_release_manifest(release_root)
                    wait_payload["release_sha256"] = manifest.artifact_sha256
                elif manifest_path.exists() or manifest_path.is_symlink():
                    raise ContractError("empty Release tree cannot have a seal")
            elif manifest_path.exists() or manifest_path.is_symlink():
                raise ContractError("Release seal cannot exist without its tree")
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
            release_sha256,
            waiting.needs,
            playtest_rounds=playtest_rounds,
            page_url=page_url,
            invented=invented,
        )

    def _finish_release(
        self,
        runtime: Runtime,
        wish: Wish,
        made: Made,
        product_release: ProductRelease,
        round_number: int,
        playtest_rounds: int,
        lease_token: str,
        release_workspace: Path,
        invented: Optional[Invented] = None,
    ) -> WorkshopRun:
        """Validate Release once, then continue through the existing Deliver job."""

        if not isinstance(product_release, ProductRelease):
            raise ContractError("Release must return ProductRelease")
        _inside(
            product_release.root,
            release_workspace,
            "Release result",
        )
        product_release.assert_current()
        if product_release.product_artifact_sha256 != made.artifact_sha256:
            raise ContractError("Release describes different product bytes")
        self._advance(
            runtime,
            wish.product_id,
            "deliver",
            artifact_sha256=made.artifact_sha256,
            payload={
                "status": "working",
                "round": round_number,
                "release_sha256": product_release.release_sha256,
            },
            lease_token=lease_token,
        )
        deliver_context = DeliverContext(wish, made, product_release)
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
                release_sha256=product_release.release_sha256,
                page_url=product_release.page_url,
                invented=invented,
            )
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
                "release_sha256": product_release.release_sha256,
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
            product_release.release_sha256,
            delivery=delivered,
            playtest_rounds=playtest_rounds,
            page_url=product_release.page_url,
            invented=invented,
        )

    def resume_release(self, wish: Wish) -> WorkshopRun:
        """Resume one exact run waiting at Release, without Make or Playtest.

        A content-addressed checkpoint reconstructs the already approved revision.
        If local Release were sealed before the wait, only the resumable site
        portion may run; media and copy are never regenerated or overwritten.
        """

        if not isinstance(wish, Wish):
            raise ContractError("Workshop.resume_release requires a Wish")
        wish.assert_valid()
        self.taste.assert_current()
        runtime = self._runtime()
        product = runtime.get_product(wish.product_id)
        if product["stage"] != "release":
            raise ContractError(
                "resume_release requires a run waiting at Release"
            )
        lease = runtime.acquire_lease(
            wish.product_id, "toy-workshop-release-resume"
        )
        try:
            product = runtime.get_product(wish.product_id)
            if product["stage"] != "release":
                raise ContractError(
                    "resume_release requires a run waiting at Release"
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

            run_root = self.runtime_root / "runs" / wish.product_id
            if run_root.is_symlink() or not run_root.is_dir():
                raise ContractError("Workshop run directory is missing or unsafe")
            run_root = run_root.resolve(strict=True)
            checkpoint, checkpoint_sha256 = _read_release_checkpoint(run_root)
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
                raise ContractError("Release resume checkpoint bindings are malformed")
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
                    "Release checkpoint differs from the original Workshop bindings"
                )
            round_number = checkpoint["round"]
            if (
                type(round_number) is not int
                or round_number < 1
                or round_number > selected_rounds
            ):
                raise ContractError("Release checkpoint round is outside its allowance")

            events = runtime.events(wish.product_id)
            latest = events[-1]
            latest_payload = latest.get("payload")
            if (
                latest.get("to_stage") != "release"
                or not isinstance(latest_payload, Mapping)
                or latest_payload.get("status") != "waiting"
                or latest_payload.get("round") != round_number
                or latest_payload.get("resume_checkpoint_sha256")
                != checkpoint_sha256
            ):
                raise ContractError(
                    "resume_release requires the latest state to be this exact waiting checkpoint"
                )
            approval_event = next(
                (
                    event
                    for event in reversed(events)
                    if event.get("from_stage") == "playtest"
                    and event.get("to_stage") == "release"
                    and isinstance(event.get("payload"), Mapping)
                    and event["payload"].get("resume_checkpoint_sha256")
                    == checkpoint_sha256
                ),
                None,
            )
            if approval_event is None:
                raise ContractError(
                    "Release checkpoint is not bound to an approved Playtest event"
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
                    "persisted Release state identifies different Make or Playtest bytes"
                )

            release_workspace = (run_root / "release").absolute()
            release_context = ReleaseContext(
                wish,
                self.taste,
                self.blueprint,
                made,
                playtested,
                release_workspace,
                lease,
            )
            tree_is_nonempty = False
            if release_workspace.exists():
                if (
                    release_workspace.is_symlink()
                    or not release_workspace.is_dir()
                ):
                    raise ContractError("Release workspace must be a regular directory")
                tree_is_nonempty = any(release_workspace.iterdir())
            if tree_is_nonempty:
                manifest = sealed_release_manifest(release_workspace)
                if latest_payload.get("release_sha256") != manifest.artifact_sha256:
                    raise ContractError(
                        "sealed Release identity differs from its waiting event"
                    )
                resume_job = getattr(self.release_job, "resume", None)
                if not callable(resume_job):
                    raise ContractError(
                        "sealed Release requires a job with resume(context) support"
                    )
                operation = resume_job
            else:
                if latest_payload.get("release_sha256") is not None:
                    raise ContractError(
                        "waiting event cites sealed Release that are missing"
                    )
                manifest_path = run_root / RELEASE_MANIFEST_FILENAME
                if manifest_path.exists() or manifest_path.is_symlink():
                    raise ContractError("Release seal exists without a sealed tree")
                operation = self.release_job
            try:
                product_release = operation(release_context)
            except WaitingFor as waiting:
                return self._wait(
                    runtime,
                    wish,
                    "release",
                    round_number,
                    waiting,
                    lease,
                    selected_rounds,
                    artifact_sha256=made.artifact_sha256,
                )
            return self._finish_release(
                runtime,
                wish,
                made,
                product_release,
                round_number,
                selected_rounds,
                lease,
                release_workspace,
            )
        finally:
            runtime.release_lease(wish.product_id, lease)

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
        runtime.register_product(
            wish.product_id,
            "wish",
            {
                "wish": wish.to_dict(),
                "inventor_id": self.inventor_id,
                "taste_sha256": self.taste.sha256,
                "blueprint_sha256": self.blueprint.sha256,
                "lane": self.lane,
                "customization_level": self.customization_level,
                "playtest_rounds": selected_rounds,
            },
        )
        lease = runtime.acquire_lease(
            wish.product_id,
            "toy-workshop",
            ttl_seconds=_MANAGED_RUN_LEASE_SECONDS,
        )
        try:
            run_root = self.runtime_root / "runs" / wish.product_id
            if run_root.exists():
                if run_root.is_symlink() or not run_root.is_dir() or any(run_root.iterdir()):
                    raise ContractError("new Workshop run directory must be fresh and empty")
            else:
                run_root.mkdir(parents=True, mode=0o700)
            run_root = run_root.resolve(strict=True)
            self._advance(
                runtime,
                wish.product_id,
                "invent",
                artifact_sha256=None,
                payload={"status": "working", "round": 1},
                lease_token=lease,
            )

            invent_workspace = (run_root / "invent").absolute()
            invent_context = InventContext(
                wish,
                self.taste,
                self.blueprint,
                invent_workspace,
            )
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

            feedback = ()
            made: Optional[Made] = None
            playtested: Optional[Playtested] = None
            round_number = 0
            for round_number in range(1, selected_rounds + 1):
                round_root = run_root / ("round-%03d" % round_number)
                make_workspace = (round_root / "make").absolute()
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
                if not isinstance(made, Made):
                    raise ContractError("Make must return Made")
                _inside(made.artifact_root, make_workspace, "Made artifact")
                made.assert_current()
                if made.product.get("lane") != self.lane:
                    raise ContractError("Make returned a product for another plaything lane")
                self.taste.assert_current()
                self._advance(
                    runtime,
                    wish.product_id,
                    "playtest",
                    artifact_sha256=made.artifact_sha256,
                    payload={
                        "status": "working",
                        "round": round_number,
                        "artifact_sha256": made.artifact_sha256,
                    },
                    lease_token=lease,
                )

                playtest_workspace = (round_root / "playtest").absolute()
                playtest_context = PlaytestContext(
                    wish,
                    self.taste,
                    self.blueprint,
                    round_number,
                    made,
                    playtest_workspace,
                    selected_rounds,
                )
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
                    )
                if not isinstance(playtested, Playtested):
                    raise ContractError("Playtest must return Playtested")
                playtested.assert_artifact(made.artifact_sha256)
                made.assert_current()
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
                        )
                    checkpoint_payload = _release_checkpoint_payload(
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
                    checkpoint_sha256 = _write_release_checkpoint(
                        run_root, checkpoint_payload
                    )
                    self._advance(
                        runtime,
                        wish.product_id,
                        "release",
                        artifact_sha256=made.artifact_sha256,
                        payload={
                            "status": "working",
                            "round": round_number,
                            "evidence_artifact_sha256": (
                                playtested.evidence.evidence_artifact_sha256
                            ),
                            "resume_checkpoint_sha256": checkpoint_sha256,
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
                    },
                    lease_token=lease,
                )

            if made is None or playtested is None or not playtested.passed:
                raise ContractError("Workshop ended without an approved Make")
            release_workspace = (run_root / "release").absolute()
            release_context = ReleaseContext(
                wish,
                self.taste,
                self.blueprint,
                made,
                playtested,
                release_workspace,
                lease,
            )
            try:
                product_release = self.release_job(release_context)
            except WaitingFor as waiting:
                return self._wait(
                    runtime,
                    wish,
                    "release",
                    round_number,
                    waiting,
                    lease,
                    selected_rounds,
                    artifact_sha256=made.artifact_sha256,
                    invented=invented,
                )
            return self._finish_release(
                runtime,
                wish,
                made,
                product_release,
                round_number,
                selected_rounds,
                lease,
                release_workspace,
                invented,
            )
        finally:
            runtime.release_lease(wish.product_id, lease)


# Compatibility imports for callers that used this module as the old offline
# demo location. They are not part of the six-job design.
from workshop.make.offline import (  # noqa: E402,F401
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
    "ReleaseJob",
    "InventJob",
    "MakeJob",
    "PlaytestJob",
    "Workshop",
    "WorkshopTools",
    "offline_workbench",
]
