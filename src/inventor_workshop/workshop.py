"""The Toy Workshop pipeline and its three inventor customization levels.

An inventor supplies Taste and may replace Make, or Make and Playtest. The
Workshop always owns the loop, exact artifact identity, Instructions, Deliver, and
truthful waiting for capabilities that are not present. Playtest is AI-agent
simulation. Customer Reviews arrive asynchronously after Deliver and become
learning for a future Make without mutating shipped bytes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
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
from .concept import DefaultConcept, MAX_CONCEPT_REFINE_DEPTH
from .deliver import DefaultDeliver
from .instructions import (
    DefaultInstructions,
    INSTRUCTIONS_MANIFEST_FILENAME,
    sealed_instructions_manifest,
)
from .errors import ContractError
from .jobs import (
    ConceptContext,
    ConceptImages,
    CustomerReview,
    DeliverContext,
    Delivered,
    InstructionsContext,
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
from .models import PlaytestResult, require_sha256
from .playtest import Playtest
from .runtime import Runtime
from .taste import load_taste
from .toys import ToyBlueprint, playful_make_request


ConceptJob = Callable[[ConceptContext], ConceptImages]
MakeJob = Callable[[MakeContext], Made]
PlaytestJob = Callable[[PlaytestContext], Playtested]
InstructionsJob = Callable[[InstructionsContext], ProductInstructions]
DeliverJob = Callable[[DeliverContext], Delivered]

CUSTOMIZATION_LEVELS = ("taste-only", "custom-make", "custom-playtest")
_INSTRUCTIONS_CHECKPOINT = "instructions-checkpoint.json"


def _callable_or_none(value: Any, label: str) -> None:
    if value is not None and not callable(value):
        raise ContractError("%s must be callable or absent" % label)


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
            records.append(_review_from_dict(payload["customer_review"]))
    if not records:
        return ()

    delivered = _delivery_from_events(runtime, product_id)
    seen_ids = set()
    for review in records:
        if review.review_id in seen_ids:
            raise ContractError("persisted customer review_id must be unique")
        seen_ids.add(review.review_id)
        review.assert_delivery(delivered)
        if _utc_instant(review.observed_at) < _utc_instant(delivered.observed_at):
            raise ContractError("persisted customer Review cannot predate Deliver")
    return tuple(records)


def _playtest_policy_needs(
    blueprint: ToyBlueprint, playtested: Playtested
) -> tuple[Need, ...]:
    """Return evidence the lane still needs before Instructions may begin.

    A custom Playtest can decide how to run its AI players, but it cannot silently
    narrow the Workshop policy. Result IDs are the blueprint capability names.
    Invented games additionally validate the meaning of their simulation result
    instead of accepting a conveniently named pass.
    """

    by_id = {result.playtest_id: result for result in playtested.evidence.results}
    required_capabilities = blueprint.required_capabilities("playtest")
    needs = [
        Need(
            "playtest",
            capability,
            "The custom Playtest did not return this required lane result.",
            "Return an artifact-bound PlaytestResult whose ID is %r, or wait for the real capability."
            % capability,
        )
        for capability in required_capabilities
        if capability not in by_id
    ]

    for capability in required_capabilities:
        result = by_id.get(capability)
        if (
            result is not None
            and result.passed
            and result.evidence.get("evidence_class") != "ai-simulation"
        ):
            needs.append(
                Need(
                    "playtest",
                    capability,
                    "Playtest evidence must come from AI-agent simulation, not customer or physical testing.",
                    "Return artifact-bound %s evidence with evidence_class=ai-simulation."
                    % capability,
                )
            )

    agent_playtest = by_id.get("agent-playtest")
    if agent_playtest is not None and agent_playtest.passed:
        roles = agent_playtest.evidence.get("agent_roles", ())
        valid_roles = (
            isinstance(roles, (list, tuple))
            and len(roles) >= 2
            and all(isinstance(role, str) and role.strip() for role in roles)
            and len(set(roles)) == len(roles)
        )
        if not valid_roles:
            needs.append(
                Need(
                    "playtest",
                    "agent-playtest",
                    "Playtest needs feedback from more than one distinct AI-player role.",
                    "Return agent-playtest evidence with at least two distinct non-empty agent_roles.",
                )
            )

    if blueprint.lane != "invented-games":
        unique = {}
        for need in needs:
            unique.setdefault(need.capability, need)
        return tuple(unique.values())

    simulation = by_id.get("game-simulation")
    if simulation is not None and simulation.passed:
        evidence = simulation.evidence
        styles = evidence.get("player_styles", ())
        required_styles = {"optimizing", "social", "exploratory", "adversarial"}
        simulation_is_real = (
            evidence.get("evidence_class") == "ai-simulation"
            and type(evidence.get("completed_games")) is int
            and evidence["completed_games"] >= 1_000
            and evidence.get("executable") is True
            and isinstance(styles, (list, tuple))
            and all(isinstance(style, str) for style in styles)
            and required_styles <= set(styles)
        )
        if not simulation_is_real:
            needs.append(
                Need(
                    "playtest",
                    "game-simulation",
                    "An invented game needs executable evidence from at least 1,000 seeded games across all four player styles.",
                    "Return game-simulation evidence_class=ai-simulation, executable=true, completed_games>=1000, and optimizing/social/exploratory/adversarial player_styles.",
                )
            )

    # Keep one actionable request per capability even when a malformed result
    # and a missing-result check converge on the same policy requirement.
    unique = {}
    for need in needs:
        unique.setdefault(need.capability, need)
    return tuple(unique.values())


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


def _write_json_once(path: Path, value: Mapping[str, Any]) -> None:
    """Create one durable checkpoint without ever replacing an earlier identity."""

    if path.exists() or path.is_symlink():
        raise ContractError("Instructions checkpoint already exists")
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
            raise ContractError("Instructions checkpoint already exists") from exc
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


def _instructions_checkpoint_payload(
    wish: Wish,
    taste_sha256: str,
    blueprint: ToyBlueprint,
    customization_level: str,
    playtest_rounds: int,
    round_number: int,
    made: Made,
    playtested: Playtested,
    run_root: Path,
    playtest_workspace: Path,
    concept_sha256: Optional[str],
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
        "wish": wish.to_dict(),
        "taste_sha256": taste_sha256,
        "blueprint_sha256": blueprint.sha256,
        "lane": blueprint.lane,
        "customization_level": customization_level,
        "playtest_rounds": playtest_rounds,
        "round": round_number,
        # The concept this build followed, so a resumed run cannot silently
        # attach its approved product to a different design.
        "concept_sha256": concept_sha256,
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


def _write_instructions_checkpoint(run_root: Path, payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(payload)).hexdigest()
    document = {
        "schema_version": 1,
        "checkpoint_sha256": digest,
        "payload": payload,
    }
    _write_json_once(run_root / _INSTRUCTIONS_CHECKPOINT, document)
    return digest


def _read_instructions_checkpoint(
    run_root: Path,
) -> tuple[Mapping[str, Any], str]:
    path = run_root / _INSTRUCTIONS_CHECKPOINT
    if path.is_symlink() or not path.is_file():
        raise ContractError("Instructions resume checkpoint is missing")
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
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
) -> tuple[Made, Playtested]:
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
    return made, playtested


@dataclass(frozen=True)
class WorkshopTools:
    """Shared capabilities installed once for every inventor in one Workshop."""

    make: Optional[MakeJob] = None
    playtest: Optional[PlaytestJob] = None
    instructions: Optional[InstructionsJob] = None
    deliver: Optional[DeliverJob] = None
    concept: Optional[ConceptJob] = None

    def __post_init__(self) -> None:
        for value, label in (
            (self.concept, "Workshop Concept"),
            (self.make, "Workshop Make"),
            (self.playtest, "Workshop Playtest"),
            (self.instructions, "Workshop Instructions"),
            (self.deliver, "Workshop Deliver"),
        ):
            _callable_or_none(value, label)


def _assert_product_follows_concept(concept: ConceptImages, made: Made) -> None:
    """Enforce the two parts of concept adherence that bytes can actually settle.

    The component breakdown was decided in Concept, so a product that ships a
    different set of parts is a different design and is refused. And the concept
    is an instruction, never evidence: a build that copies the drawing into its
    own artifact tree has not shown what was made, however faithfully it built.
    """

    declared = made.product.get("components", [])
    if isinstance(declared, (str, bytes)) or not isinstance(declared, (list, tuple)):
        raise ContractError(
            "Make must publish the concept's component list as its components"
        )
    remaining = {item.key: item for item in concept.brief.components}
    for value in declared:
        name = str(value)
        matched = next(
            (
                key
                for key, component in remaining.items()
                if name in (component.key, component.name)
            ),
            None,
        )
        if matched is None:
            raise ContractError(
                "Make published component %r, which the concept brief does not name"
                % name
            )
        del remaining[matched]
    if remaining:
        raise ContractError(
            "Make omitted the concept's components: %s"
            % ", ".join(sorted(remaining))
        )
    reused = concept.image_digests() & {
        entry.sha256 for entry in made.artifact_manifest.entries
    }
    if reused:
        raise ContractError(
            "Make returned a product containing concept image bytes; a concept "
            "says what to build and can never stand in as a picture of what was built"
        )


def _missing_concept(context: ConceptContext) -> ConceptImages:
    capabilities = context.blueprint.required_capabilities("concept")
    raise WaitingFor(
        *(
            Need(
                "concept",
                capability,
                "This Wish still needs %s before Make can build to a decided design."
                % capability,
                "Configure the shared Concept capability; never hand Make a design "
                "that was described but not actually drawn.",
            )
            for capability in capabilities
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
    """Run one inventor through Wish -> Make <-> Playtest -> Instructions -> Deliver.

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
        tools: Optional[WorkshopTools] = None,
        make: Optional[MakeJob] = None,
        playtest: Optional[PlaytestJob] = None,
        concept: Optional[ConceptJob] = None,
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
        _callable_or_none(concept, "inventor Concept")
        if playtest is not None and make is None:
            raise ContractError("custom Playtest requires custom Make")
        if type(max_rounds) is not int or not 1 <= max_rounds <= 100:
            raise ContractError("max_rounds must be an integer from 1 to 100")

        selected_tools = tools or WorkshopTools()
        selected_runtime = Path(runtime_root) if runtime_root else root / ".workshop"
        if not selected_runtime.is_absolute():
            raise ContractError("Workshop runtime_root must be absolute")
        if selected_runtime.is_symlink():
            raise ContractError("Workshop runtime_root must not be a symlink")

        self.inventor_root = root
        self.taste = load_taste(root)
        self.blueprint = ToyBlueprint.for_lane(lane)
        self.tools = selected_tools
        self.concept_job: ConceptJob = (
            concept or selected_tools.concept or _missing_concept
        )
        self.make_job: MakeJob = make or selected_tools.make or _missing_make
        self.playtest_job: PlaytestJob = (
            playtest or selected_tools.playtest or _missing_playtest
        )
        self.instructions_job: InstructionsJob = (
            selected_tools.instructions or DefaultInstructions()
        )
        self.deliver_job: DeliverJob = selected_tools.deliver or DefaultDeliver()
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

            self._advance(
                runtime,
                product_id,
                "deliver",
                artifact_sha256=delivered.product_artifact_sha256,
                payload={
                    "status": "delivered",
                    "customer_review": review.to_dict(),
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
            # Make is reachable only through Concept: a build always follows a
            # decided design, including the rebuild a failed Playtest asks for.
            "wish": ("concept",),
            "concept": ("concept", "make"),
            "make": ("make", "playtest"),
            "playtest": ("playtest", "concept", "instructions"),
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
        instructions_sha256: Optional[str] = None,
        page_url: Optional[str] = None,
        concept_sha256: Optional[str] = None,
    ) -> WorkshopRun:
        if any(need.job != job for need in waiting.needs):
            raise ContractError("waiting capability belongs to a different Workshop job")
        wait_payload: dict[str, Any] = {
            "status": "waiting",
            "round": round_number,
            "needs": [need.to_dict() for need in waiting.needs],
        }
        if concept_sha256 is not None:
            wait_payload["concept_sha256"] = concept_sha256
        if job == "instructions":
            run_root = self.runtime_root / "runs" / wish.product_id
            _, checkpoint_sha256 = _read_instructions_checkpoint(run_root)
            wait_payload["resume_checkpoint_sha256"] = checkpoint_sha256
            instructions_root = run_root / "instructions"
            manifest_path = run_root / INSTRUCTIONS_MANIFEST_FILENAME
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
            concept_sha256=concept_sha256,
        )

    def _finish_instructions(
        self,
        runtime: Runtime,
        wish: Wish,
        made: Made,
        product_instructions: ProductInstructions,
        round_number: int,
        playtest_rounds: int,
        lease_token: str,
        instructions_workspace: Path,
        concept_sha256: Optional[str] = None,
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
                concept_sha256=concept_sha256,
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
            concept_sha256=concept_sha256,
        )

    def resume_instructions(self, wish: Wish) -> WorkshopRun:
        """Resume one exact run waiting at Instructions, without Make or Playtest.

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
        lease = runtime.acquire_lease(
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
                "taste_sha256": self.taste.sha256,
                "blueprint_sha256": self.blueprint.sha256,
                "lane": self.lane,
                "customization_level": self.customization_level,
            }
            if any(metadata.get(key) != value for key, value in expected_bindings.items()):
                raise ContractError(
                    "resume Workshop has different Taste, blueprint, lane, or customization"
                )
            selected_rounds = metadata["playtest_rounds"]
            if type(selected_rounds) is not int or not 1 <= selected_rounds <= 100:
                raise ContractError("persisted Playtest round allowance is malformed")

            run_root = self.runtime_root / "runs" / wish.product_id
            if run_root.is_symlink() or not run_root.is_dir():
                raise ContractError("Workshop run directory is missing or unsafe")
            run_root = run_root.resolve(strict=True)
            checkpoint, checkpoint_sha256 = _read_instructions_checkpoint(run_root)
            if set(checkpoint) != {
                "product_id",
                "wish",
                "taste_sha256",
                "blueprint_sha256",
                "lane",
                "customization_level",
                "playtest_rounds",
                "round",
                "concept_sha256",
                "made",
                "playtested",
            }:
                raise ContractError("Instructions resume checkpoint bindings are malformed")
            checkpoint_bindings = {
                "product_id": wish.product_id,
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
            checkpoint_concept = checkpoint["concept_sha256"]
            if checkpoint_concept is not None:
                require_sha256(
                    checkpoint_concept, "Instructions checkpoint concept sha256"
                )

            events = runtime.events(wish.product_id)
            latest = events[-1]
            latest_payload = latest.get("payload")
            if (
                latest.get("to_stage") != "instructions"
                or not isinstance(latest_payload, Mapping)
                or latest_payload.get("status") != "waiting"
                or latest_payload.get("round") != round_number
                or latest_payload.get("resume_checkpoint_sha256")
                != checkpoint_sha256
            ):
                raise ContractError(
                    "resume_instructions requires the latest state to be this exact waiting checkpoint"
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
            made, playtested = _rebuild_checkpoint_results(run_root, checkpoint)
            if not playtested.passed or _playtest_policy_needs(
                self.blueprint, playtested
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
            if (
                approval_event["payload"].get("concept_sha256") != checkpoint_concept
                or latest_payload.get("concept_sha256") != checkpoint_concept
            ):
                raise ContractError(
                    "persisted Instructions state was built against a different concept"
                )

            instructions_workspace = (run_root / "instructions").absolute()
            instructions_context = InstructionsContext(
                wish,
                self.taste,
                self.blueprint,
                made,
                playtested,
                instructions_workspace,
                lease,
            )
            tree_is_nonempty = False
            if instructions_workspace.exists():
                if (
                    instructions_workspace.is_symlink()
                    or not instructions_workspace.is_dir()
                ):
                    raise ContractError("Instructions workspace must be a regular directory")
                tree_is_nonempty = any(instructions_workspace.iterdir())
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
                manifest_path = run_root / INSTRUCTIONS_MANIFEST_FILENAME
                if manifest_path.exists() or manifest_path.is_symlink():
                    raise ContractError("Instructions seal exists without a sealed tree")
                operation = self.instructions_job
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
                    concept_sha256=checkpoint_concept,
                )
            return self._finish_instructions(
                runtime,
                wish,
                made,
                product_instructions,
                round_number,
                selected_rounds,
                lease,
                instructions_workspace,
                checkpoint_concept,
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
                "taste_sha256": self.taste.sha256,
                "blueprint_sha256": self.blueprint.sha256,
                "lane": self.lane,
                "customization_level": self.customization_level,
                "playtest_rounds": selected_rounds,
            },
        )
        lease = runtime.acquire_lease(wish.product_id, "toy-workshop")
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
                "concept",
                artifact_sha256=None,
                payload={"status": "working", "round": 1},
                lease_token=lease,
            )

            feedback = ()
            made: Optional[Made] = None
            playtested: Optional[Playtested] = None
            concept: Optional[ConceptImages] = None
            previous_concept: Optional[ConceptImages] = None
            refine_depth = 0
            round_number = 0
            for round_number in range(1, selected_rounds + 1):
                round_root = run_root / ("round-%03d" % round_number)
                concept_workspace = (round_root / "concept").absolute()
                concept_context = ConceptContext(
                    wish,
                    self.taste,
                    self.blueprint,
                    round_number,
                    concept_workspace,
                    feedback,
                    selected_rounds,
                    previous_concept,
                    refine_depth,
                )
                try:
                    concept = self.concept_job(concept_context)
                except WaitingFor as waiting:
                    return self._wait(
                        runtime,
                        wish,
                        "concept",
                        round_number,
                        waiting,
                        lease,
                        selected_rounds,
                    )
                if not isinstance(concept, ConceptImages):
                    raise ContractError("Concept must return ConceptImages")
                _inside(concept.root, concept_workspace, "Concept images")
                concept.assert_current()
                if concept.round != round_number:
                    raise ContractError("Concept returned a design for another round")
                if previous_concept is not None and feedback:
                    refine_depth = (
                        0
                        if refine_depth >= MAX_CONCEPT_REFINE_DEPTH
                        else refine_depth + 1
                    )
                previous_concept = concept
                self.taste.assert_current()
                self._advance(
                    runtime,
                    wish.product_id,
                    "make",
                    artifact_sha256=None,
                    payload={
                        "status": "working",
                        "round": round_number,
                        "concept_sha256": concept.concept_sha256,
                    },
                    lease_token=lease,
                )

                make_workspace = (round_root / "make").absolute()
                make_context = MakeContext(
                    wish,
                    self.taste,
                    self.blueprint,
                    round_number,
                    make_workspace,
                    feedback,
                    selected_rounds,
                    concept,
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
                        concept_sha256=concept.concept_sha256,
                    )
                if not isinstance(made, Made):
                    raise ContractError("Make must return Made")
                _inside(made.artifact_root, make_workspace, "Made artifact")
                made.assert_current()
                if made.product.get("lane") != self.lane:
                    raise ContractError("Make returned a product for another plaything lane")
                # Make may have been slow, and the concept it followed is the
                # thing the product will be judged against.
                concept.assert_current()
                _assert_product_follows_concept(concept, made)
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
                    )
                if not isinstance(playtested, Playtested):
                    raise ContractError("Playtest must return Playtested")
                playtested.assert_artifact(made.artifact_sha256)
                made.assert_current()
                if playtested.passed:
                    policy_needs = _playtest_policy_needs(self.blueprint, playtested)
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
                            concept_sha256=concept.concept_sha256,
                        )
                    checkpoint_payload = _instructions_checkpoint_payload(
                        wish,
                        self.taste.sha256,
                        self.blueprint,
                        self.customization_level,
                        selected_rounds,
                        round_number,
                        made,
                        playtested,
                        run_root,
                        playtest_workspace,
                        concept.concept_sha256,
                    )
                    checkpoint_sha256 = _write_instructions_checkpoint(
                        run_root, checkpoint_payload
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
                            "concept_sha256": concept.concept_sha256,
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
                            "concept_sha256": concept.concept_sha256,
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
                        concept_sha256=concept.concept_sha256,
                    )
                # A rejected revision goes back through Concept: a design flaw
                # is corrected in the design, not worked around in geometry.
                self._advance(
                    runtime,
                    wish.product_id,
                    "concept",
                    artifact_sha256=made.artifact_sha256,
                    payload={
                        "status": "working",
                        "round": round_number + 1,
                        "concept_sha256": concept.concept_sha256,
                        "feedback": [item.to_dict() for item in feedback],
                    },
                    lease_token=lease,
                )

            if made is None or playtested is None or not playtested.passed:
                raise ContractError("Workshop ended without an approved Make")
            assert concept is not None
            instructions_workspace = (run_root / "instructions").absolute()
            instructions_context = InstructionsContext(
                wish,
                self.taste,
                self.blueprint,
                made,
                playtested,
                instructions_workspace,
                lease,
                concept,
            )
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
                    concept_sha256=concept.concept_sha256,
                )
            return self._finish_instructions(
                runtime,
                wish,
                made,
                product_instructions,
                round_number,
                selected_rounds,
                lease,
                instructions_workspace,
                concept.concept_sha256,
            )
        finally:
            runtime.release_lease(wish.product_id, lease)


# Compatibility imports for callers that used this module as the old offline
# demo location. They are not part of the five-job design.
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
    "ConceptJob",
    "DeliverJob",
    "InstructionsJob",
    "MakeJob",
    "PlaytestJob",
    "Workshop",
    "WorkshopTools",
    "offline_workbench",
]
