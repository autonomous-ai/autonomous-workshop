"""Trusted host for one native coding-agent session per Wish.

This module deliberately contains no Match, Invent, Make, or Playtest
reasoning.  It creates the private filesystem protocol, binds a native Codex
session to those exact bytes, and exposes a redacted status view.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from workshop.errors import (
    ArtifactError,
    ContractError,
    ManifestError,
    StateConflict,
    TransitionError,
    WorkshopError,
)
from workshop.contributors import (
    fingerprint_extension_skill,
    load_manifest,
    load_taste,
)
from workshop.integrations.factory_agent import (
    FactoryAgentReleaseWriter,
    FactoryAgentSession,
    FactoryPublicTransition,
    factory_credentials_from_environment,
)
from workshop.invent.native import InventedV2
from workshop.make.native import NativeMade
from workshop.make.native_gate import (
    NATIVE_CAD_VERIFIER_PATH,
    verify_native_made_cad,
)
from workshop.match.native import (
    NativeMatchAssignment,
    PersonaCatalog,
    PersonaCatalogEntry,
)
from workshop.playtest.native import NativePlaytested
from workshop.product import PLAYTHING_LANES, ToyBlueprint
from workshop.release.contracts import ProductRelease, ReleaseContext
from workshop.release.native import NativeRelease
from workshop.runtime import (
    CodexInvocationError,
    CodexNativeSessionLauncher,
    CodexNativeSessionOutcome,
    InventorStore,
    Receipt,
)
from workshop.runtime.agent_assets import product_run_agent_assets
from workshop.runtime.package_data import (
    default_workshop_home,
    packaged_inventors_root,
    product_run_domain_skill_roots,
)
from workshop.wish import Wish
from workshop.workflow.agent_run import (
    AgentArtifact,
    AgentOutcome,
    AgentRun,
    AgentRunCheckpoint,
    DeterministicGateReceipt,
)
from workshop.workflow.proposals import (
    AgentOutcomeProposal,
    read_agent_outcome_proposal,
    read_bounded_json_artifact,
)
from workshop.workflow.stage_gates import (
    StageGateDecision,
    StageGateEvidence,
    evaluate_invent_stage,
    evaluate_match_stage,
    invent_gate_subject_sha256,
    match_gate_subject_sha256,
)


_RUN_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,255}$")
_INSTRUCTION_HASH_DOMAIN = b"autonomous-workshop/product-run-instructions/v1\0"
_SESSION_CHECKPOINT_NAME = "codex-session.json"
_STAGE_INPUT_NAME = "STAGE.json"
_AGENT_OUTCOME_NAME = "agent-outcome.json"
_AUTHORIZATION_NAME = "authorization.json"
_RELEASE_EFFECT_WAIT_NAME = "release-effect-wait.json"
_STAGE_INPUT_KIND = "autonomous-workshop.stage-input"
_AUTHORIZATION_KIND = "autonomous-workshop.run-authorization"
_SUBJECT_KIND = "autonomous-workshop.stage-gate-subject"
_MAX_STAGE_INPUT_BYTES = 512 * 1024
_MAX_NATIVE_TURNS = 32
_FACTORY_CREDENTIALS_NEED = (
    "Factory credentials for the selected Inventor are missing or malformed; "
    "configure a complete matching username/password pair, then resume this run."
)


class _FactoryCredentialsUnavailable(Exception):
    """Internal signal for a host configuration wait before any Factory effect."""

    def __init__(self, inventor_id: str) -> None:
        self.inventor_id = inventor_id
        super().__init__(_FACTORY_CREDENTIALS_NEED)


@dataclass(frozen=True)
class NativeRunPaths:
    """Private sibling roots for agent-visible work and host-only state."""

    container: Path
    workspace: Path
    host_state: Path


def canonical_wish_bytes(wish: Wish) -> bytes:
    """Return the one JSON encoding accepted by :class:`AgentRun`."""

    if not isinstance(wish, Wish):
        raise ContractError("native run requires a validated Wish")
    try:
        return json.dumps(
            wish.to_dict(),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("Wish cannot be encoded for a native run") from exc


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ContractError("native host values must be finite JSON") from exc


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def _strict_json_bytes(content: bytes, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(
            content.decode("utf-8"), object_pairs_hook=_strict_object
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ContractError("%s must contain strict UTF-8 JSON" % label) from exc
    if not isinstance(value, dict):
        raise ContractError("%s must contain one JSON object" % label)
    return value


def _atomic_private_write(path: Path, content: bytes, *, mode: int = 0o600) -> None:
    if mode not in (0o400, 0o600):
        raise ContractError("private file mode is invalid")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".%s." % path.name,
        suffix=".tmp",
        dir=str(path.parent),
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        os.chmod(path, mode)
        directory = os.open(
            str(path.parent), os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def _write_private_json(path: Path, value: Mapping[str, Any], *, mode: int = 0o600) -> str:
    content = _canonical_json_bytes(dict(value)) + b"\n"
    _atomic_private_write(path, content, mode=mode)
    return _sha256(content)


def _remove_agent_outcome(run_root: Path) -> None:
    path = run_root / _AGENT_OUTCOME_NAME
    if not path.exists() and not path.is_symlink():
        return
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("stale agent outcome is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise StateConflict("stale agent outcome must be a regular file")
    try:
        path.unlink()
    except OSError as exc:
        raise StateConflict("stale agent outcome could not be removed") from exc


def _load_wish(run_root: Path) -> Wish:
    path = run_root / "WISH.json"
    try:
        content = path.read_bytes()
    except OSError as exc:
        raise StateConflict("materialized Wish is unavailable") from exc
    document = _strict_json_bytes(content, label="materialized Wish")
    try:
        wish = Wish(**document)
    except (TypeError, ValueError, WorkshopError) as exc:
        raise StateConflict("materialized Wish is invalid") from exc
    if canonical_wish_bytes(wish) != content:
        raise StateConflict("materialized Wish is not canonical")
    return wish


def materialized_agent_instructions_sha256(
    checkpoint: AgentRunCheckpoint,
) -> str:
    """Bind the exact AGENTS.md and skill bytes already inside a run.

    Resume derives this value from the immutable run manifest, not from the
    current source checkout or installed package.  Updating instructions for a
    future Wish therefore cannot silently change an existing session binding.
    """

    if not isinstance(checkpoint, AgentRunCheckpoint):
        raise ContractError("instruction manifest requires an AgentRun checkpoint")
    selected = {
        path: digest
        for path, digest in checkpoint.input_sha256s.items()
        if path == "AGENTS.md"
        or path.startswith(".agents/skills/")
    }
    required = {
        "AGENTS.md",
        ".agents/skills/autonomous-workshop/SKILL.md",
    }
    if not required <= set(selected):
        raise StateConflict("native run instruction manifest is incomplete")
    digest = hashlib.sha256(_INSTRUCTION_HASH_DOMAIN)
    for relative, content_sha256 in sorted(selected.items()):
        try:
            content_digest = bytes.fromhex(content_sha256)
        except (TypeError, ValueError) as exc:
            raise StateConflict("native run instruction manifest is invalid") from exc
        if len(content_digest) != 32:
            raise StateConflict("native run instruction manifest is invalid")
        encoded_path = relative.encode("utf-8")
        digest.update(len(encoded_path).to_bytes(4, "big"))
        digest.update(encoded_path)
        digest.update(content_digest)
    return digest.hexdigest()


def native_stage_prompt(stage: str) -> str:
    """Give the native session a compact pointer, never Wish or host secrets."""

    if stage not in (
        "wish",
        "match",
        "invent",
        "make",
        "playtest",
        "release",
        "deliver",
    ):
        raise ContractError("native run stage is invalid")
    return (
        "Follow the local AGENTS.md and autonomous-workshop skill. "
        "Read the host-written STAGE.json, perform the current %s stage only, "
        "and use the run-local deterministic proposal tool. Write the compact "
        "result to agent-outcome.json, then return control to the Workshop host gate."
        % stage
    )


def _validated_product_id(product_id: str) -> str:
    if not isinstance(product_id, str) or _RUN_ID.fullmatch(product_id) is None:
        raise ContractError("native run product id is invalid")
    return product_id


def _existing_real_directory(path: Path, *, label: str) -> Path:
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if path.is_symlink() or not stat.S_ISDIR(identity.st_mode):
        raise StateConflict("%s must be a real directory" % label)
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise StateConflict("%s is unavailable" % label) from exc
    if resolved != path:
        raise StateConflict("%s must not contain symlinks" % label)
    return resolved


def _ensure_private_directory(path: Path, *, label: str) -> Path:
    created = False
    try:
        path.mkdir(mode=0o700)
        created = True
    except FileExistsError:
        pass
    except OSError as exc:
        raise StateConflict("%s could not be created" % label) from exc
    resolved = _existing_real_directory(path, label=label)
    if created:
        os.chmod(resolved, 0o700)
    if stat.S_IMODE(resolved.stat().st_mode) != 0o700:
        raise StateConflict("%s permissions must be 0700" % label)
    return resolved


def _workshop_home() -> Path:
    selected = Path(default_workshop_home()).expanduser()
    if not selected.is_absolute():
        raise ContractError("Workshop home must be absolute")
    try:
        selected.mkdir(mode=0o700, parents=True, exist_ok=True)
    except OSError as exc:
        raise StateConflict("Workshop home could not be created") from exc
    return _existing_real_directory(selected, label="Workshop home")


def _product_run_catalog_root(assets: Any) -> Path:
    if assets.source == "repository":
        repository = assets.constitution.parents[2]
        catalog = repository / "inventors"
    else:
        catalog = packaged_inventors_root()
        if catalog is None:
            raise StateConflict("installed Workshop has no inventor personas")
    return _existing_real_directory(Path(catalog), label="inventor persona catalog")


def _persona_catalog(
    run_root: Path, checkpoint: AgentRunCheckpoint
) -> PersonaCatalog:
    personas: list[PersonaCatalogEntry] = []
    prefix = "catalog/inventors/"
    manifest_paths = sorted(
        path
        for path in checkpoint.input_sha256s
        if path.startswith(prefix) and path.endswith("/inventor.json")
    )
    for manifest_relative in manifest_paths:
        parts = manifest_relative.split("/")
        if len(parts) != 4:
            raise StateConflict("materialized inventor path is invalid")
        inventor_id = parts[2]
        taste_relative = "%s%s/TASTE.md" % (prefix, inventor_id)
        taste_sha256 = checkpoint.input_sha256s.get(taste_relative)
        if not isinstance(taste_sha256, str):
            raise StateConflict("materialized inventor Taste is missing")
        try:
            manifest_content = (run_root / manifest_relative).read_bytes()
        except OSError as exc:
            raise StateConflict("materialized inventor manifest is unavailable") from exc
        manifest_document = _strict_json_bytes(
            manifest_content, label="materialized inventor manifest"
        )
        try:
            manifest = load_manifest(run_root / manifest_relative)
        except ManifestError as exc:
            raise StateConflict(
                "materialized inventor manifest is not a native persona"
            ) from exc
        capabilities = tuple(manifest.capabilities)
        if (
            manifest_document != manifest.to_dict()
            or manifest.schema_version != 7
            or manifest.inventor_id != inventor_id
            or len(capabilities) != 1
            or capabilities[0] not in PLAYTHING_LANES
            or not manifest.extensions
        ):
            raise StateConflict("materialized inventor manifest is not a native persona")
        for extension in manifest.extensions:
            skill_prefix = ".agents/skills/%s/" % extension.name
            try:
                fingerprint = fingerprint_extension_skill(
                    run_root / ".agents" / "skills" / extension.name,
                    expected_name=extension.name,
                )
            except ManifestError as exc:
                raise StateConflict(
                    "materialized inventor skill differs from its manifest"
                ) from exc
            expected = {
                skill_prefix + entry.path: entry.sha256
                for entry in fingerprint.entries
            }
            observed = {
                path: sha256
                for path, sha256 in checkpoint.input_sha256s.items()
                if path.startswith(skill_prefix)
            }
            if (
                fingerprint.artifact_sha256 != extension.artifact_sha256
                or observed != expected
            ):
                raise StateConflict(
                    "materialized inventor skill differs from its manifest"
                )
        personas.append(
            PersonaCatalogEntry(
                inventor_id=inventor_id,
                lane=capabilities[0],
                manifest_sha256=checkpoint.input_sha256s[manifest_relative],
                taste_sha256=taste_sha256,
            )
        )
    try:
        return PersonaCatalog(tuple(personas))
    except ContractError as exc:
        raise StateConflict("materialized inventor catalog is invalid") from exc


def _read_contract(
    run_root: Path, artifact: AgentArtifact, contract_type: Any, *, label: str
) -> Any:
    document, content = read_bounded_json_artifact(
        run_root, artifact.path, label=label
    )
    if _sha256(content) != artifact.sha256:
        raise StateConflict("%s differs from its sealed artifact binding" % label)
    return contract_type.from_mapping(document)


def _stage_primary(
    checkpoint: AgentRunCheckpoint, stage: str
) -> AgentArtifact:
    artifacts = checkpoint.stage_artifacts.get(stage)
    if not artifacts:
        raise TransitionError("native run lacks the %s contract" % stage)
    return artifacts[0]


def _stage_subject(stage: str, inputs: Mapping[str, Any]) -> str:
    return _sha256(
        _canonical_json_bytes(
            {
                "schema_version": 1,
                "kind": _SUBJECT_KIND,
                "stage": stage,
                "inputs": dict(inputs),
            }
        )
    )


def native_run_paths(
    product_id: str,
    *,
    create_container: bool = False,
) -> NativeRunPaths:
    """Resolve the deterministic private location for one product id."""

    product_id = _validated_product_id(product_id)
    home = _workshop_home()
    runs = home / "runs"
    if create_container:
        runs = _ensure_private_directory(runs, label="native runs directory")
        container = _ensure_private_directory(
            runs / product_id, label="native product run directory"
        )
    else:
        runs = _existing_real_directory(runs, label="native runs directory")
        container = _existing_real_directory(
            runs / product_id, label="native product run directory"
        )
        if stat.S_IMODE(container.stat().st_mode) != 0o700:
            raise StateConflict("native product run directory permissions must be 0700")
    return NativeRunPaths(
        container=container,
        workspace=container / "workspace",
        host_state=container / "host-state",
    )


def native_run_exists(product_id: str) -> bool:
    """Return whether this id has any native-run state, including partial state."""

    product_id = _validated_product_id(product_id)
    home = Path(default_workshop_home()).expanduser()
    if not home.is_absolute():
        raise ContractError("Workshop home must be absolute")
    candidate = home / "runs" / product_id
    return candidate.exists() or candidate.is_symlink()


def _open_native_run(product_id: str) -> tuple[AgentRun, AgentRunCheckpoint]:
    paths = native_run_paths(product_id)
    run = AgentRun.open(paths.workspace, host_state_root=paths.host_state)
    return run, run.snapshot()


def _artifact_binding(artifact: AgentArtifact) -> dict[str, str]:
    return {"path": artifact.path, "sha256": artifact.sha256}


def _prepare_stage_input(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> tuple[str, Mapping[str, Any], Mapping[str, Any]]:
    """Build the exact public input vector for the current native stage.

    The returned context mapping contains typed host values and is never
    serialized for the native session.  The packet is deliberately free of
    credentials and outside-effect receipts.
    """

    stage = checkpoint.stage
    if stage in ("wish", "deliver"):
        raise TransitionError("%s does not use a native stage packet" % stage)
    catalog = _persona_catalog(run.run_root, checkpoint)
    context: dict[str, Any] = {"catalog": catalog}
    normal_transition = {
        "match": "invent",
        "invent": "make",
        "make": "playtest",
        "playtest": "release",
        "release": "deliver",
    }[stage]
    round_value: Optional[int] = (
        checkpoint.round_index if stage in ("make", "playtest", "release") else None
    )

    if stage == "match":
        subject = match_gate_subject_sha256(
            wish_sha256=checkpoint.wish_sha256,
            persona_catalog_sha256=catalog.catalog_sha256,
        )
        inputs: Mapping[str, Any] = {
            "wish_sha256": checkpoint.wish_sha256,
            "wish": {"path": "WISH.json", "sha256": checkpoint.wish_sha256},
            "persona_catalog": catalog.to_dict(),
            "blueprint_sha256_by_lane": {
                lane: ToyBlueprint.for_lane(lane).sha256
                for lane in PLAYTHING_LANES
            },
            "contract_path": "artifacts/match/assignment.json",
        }
    else:
        assignment_artifact = _stage_primary(checkpoint, "match")
        assignment = _read_contract(
            run.run_root,
            assignment_artifact,
            NativeMatchAssignment,
            label="native Match assignment",
        )
        assignment.assert_context(
            wish_sha256=checkpoint.wish_sha256, catalog=catalog
        )
        blueprint = ToyBlueprint.for_lane(assignment.selected_lane)
        taste_path = "catalog/inventors/%s/TASTE.md" % assignment.selected_inventor_id
        context.update({"assignment": assignment, "blueprint": blueprint})
        common: dict[str, Any] = {
            "wish": {"path": "WISH.json", "sha256": checkpoint.wish_sha256},
            "assignment": assignment.to_dict(),
            "assignment_artifact": {
                **_artifact_binding(assignment_artifact),
                "assignment_sha256": assignment.assignment_sha256,
            },
            "selected_taste": {
                "path": taste_path,
                "sha256": assignment.selected_taste_sha256,
            },
            "blueprint": blueprint.to_dict(),
            "blueprint_sha256": blueprint.sha256,
        }
        if stage == "invent":
            subject = invent_gate_subject_sha256(assignment)
            inputs = {
                **common,
                "contract_path": "artifacts/invent/invented.json",
            }
        else:
            invented_artifact = _stage_primary(checkpoint, "invent")
            invented = _read_contract(
                run.run_root,
                invented_artifact,
                InventedV2,
                label="native Invented contract",
            )
            invented.assert_context(assignment)
            context["invented"] = invented
            common["invented"] = invented.to_dict()
            common["invented_artifact"] = {
                **_artifact_binding(invented_artifact),
                "invented_sha256": invented.invented_sha256,
            }
            if stage == "make":
                feedback_artifact: Optional[AgentArtifact] = None
                prior = checkpoint.stage_artifacts.get("playtest")
                if prior and "playtest" in checkpoint.invalidated_stages:
                    feedback_artifact = prior[0]
                subject_inputs = {
                    "wish_sha256": checkpoint.wish_sha256,
                    "assignment_sha256": assignment.assignment_sha256,
                    "taste_sha256": assignment.selected_taste_sha256,
                    "blueprint_sha256": blueprint.sha256,
                    "invented_sha256": invented.invented_sha256,
                    "round": checkpoint.round_index,
                    "feedback_sha256": (
                        feedback_artifact.sha256 if feedback_artifact else None
                    ),
                }
                subject = _stage_subject("make", subject_inputs)
                inputs = {
                    **common,
                    "round": checkpoint.round_index,
                    "previous_playtest": (
                        _artifact_binding(feedback_artifact)
                        if feedback_artifact is not None
                        else None
                    ),
                    "product_root": "artifacts/make/r%04d/product"
                    % checkpoint.round_index,
                    "contract_path": "artifacts/make/r%04d/made.json"
                    % checkpoint.round_index,
                    "required_root_files": [
                        "product.json",
                        "project.json",
                        "assembled.step",
                        "assembled.stl",
                    ],
                }
            else:
                made_artifact = _stage_primary(checkpoint, "make")
                made = _read_contract(
                    run.run_root,
                    made_artifact,
                    NativeMade,
                    label="native Made contract",
                )
                made.assert_context(
                    assignment, invented, expected_round=checkpoint.round_index
                )
                context["made"] = made
                common["made"] = made.to_dict()
                common["made_artifact"] = {
                    **_artifact_binding(made_artifact),
                    "made_sha256": made.made_sha256,
                    "product_artifact_sha256": made.product_manifest.artifact_sha256,
                    "product_root": made.product_root,
                }
                if stage == "playtest":
                    subject_inputs = {
                        "made_sha256": made.made_sha256,
                        "product_artifact_sha256": made.product_manifest.artifact_sha256,
                        "blueprint_sha256": blueprint.sha256,
                        "round": checkpoint.round_index,
                    }
                    subject = _stage_subject("playtest", subject_inputs)
                    inputs = {
                        **common,
                        "round": checkpoint.round_index,
                        "required_check_ids": list(
                            blueprint.required_capabilities("playtest")
                        ),
                        "evidence_root": "artifacts/playtest/r%04d/evidence"
                        % checkpoint.round_index,
                        "contract_path": "artifacts/playtest/r%04d/playtested.json"
                        % checkpoint.round_index,
                    }
                else:
                    playtested_artifact = _stage_primary(checkpoint, "playtest")
                    playtested = _read_contract(
                        run.run_root,
                        playtested_artifact,
                        NativePlaytested,
                        label="native Playtested contract",
                    )
                    playtested.assert_context(made, blueprint)
                    if playtested.verdict != "pass":
                        raise TransitionError("Release requires a passing Playtest")
                    context["playtested"] = playtested
                    subject_inputs = {
                        "wish_sha256": checkpoint.wish_sha256,
                        "taste_sha256": assignment.selected_taste_sha256,
                        "blueprint_sha256": blueprint.sha256,
                        "made_sha256": made.made_sha256,
                        "product_artifact_sha256": made.product_manifest.artifact_sha256,
                        "playtested_sha256": playtested.playtested_sha256,
                        "evidence_artifact_sha256": (
                            playtested.evidence_manifest.artifact_sha256
                        ),
                        "round": checkpoint.round_index,
                    }
                    subject = _stage_subject("release", subject_inputs)
                    inputs = {
                        **common,
                        "round": checkpoint.round_index,
                        "playtested": playtested.to_dict(),
                        "playtested_artifact": {
                            **_artifact_binding(playtested_artifact),
                            "playtested_sha256": playtested.playtested_sha256,
                            "evidence_artifact_sha256": (
                                playtested.evidence_manifest.artifact_sha256
                            ),
                        },
                        "package_root": "artifacts/release/package",
                        "contract_path": "artifacts/release/release.json",
                        "required_package_files": ["MANUAL.md", "product.json"],
                    }

    packet = {
        "schema_version": 1,
        "kind": _STAGE_INPUT_KIND,
        "product_id": checkpoint.product_id,
        "stage": stage,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "subject_sha256": subject,
        "next_transition": normal_transition,
        "round": round_value,
        "max_rounds": checkpoint.max_rounds,
        "inputs": inputs,
    }
    encoded = _canonical_json_bytes(packet) + b"\n"
    if len(encoded) > _MAX_STAGE_INPUT_BYTES:
        raise ArtifactError("native stage input exceeded its byte limit")
    _atomic_private_write(
        run.run_root / _STAGE_INPUT_NAME, encoded, mode=0o400
    )
    return subject, packet, context


def _launcher_call(
    launcher: CodexNativeSessionLauncher,
    method: str,
    *,
    checkpoint: AgentRunCheckpoint,
    paths: NativeRunPaths,
) -> CodexNativeSessionOutcome:
    arguments = {
        "product_id": checkpoint.product_id,
        "wish_sha256": checkpoint.wish_sha256,
        "constitution_sha256": materialized_agent_instructions_sha256(checkpoint),
        "run_root": paths.workspace,
        "host_state_root": paths.host_state,
        "prompt": native_stage_prompt(checkpoint.stage),
    }
    try:
        return getattr(launcher, method)(**arguments)
    except CodexInvocationError as exc:
        raise WorkshopError("native Codex session did not complete: %s" % exc) from None


def _host_evidence_sha256(value: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json_bytes(dict(value)))


def _advance_validated_wish(run: AgentRun) -> AgentRunCheckpoint:
    checkpoint = run.snapshot()
    if checkpoint.stage != "wish" or checkpoint.status != "active":
        raise TransitionError("native Wish checkpoint is not ready for validation")
    source = run.run_root / "WISH.json"
    content = source.read_bytes()
    if _sha256(content) != checkpoint.wish_sha256:
        raise StateConflict("materialized Wish differs from the run binding")
    relative = "artifacts/wish/wish.json"
    target = run.run_root / relative
    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        descriptor = os.open(
            str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
    except OSError as exc:
        raise StateConflict("validated Wish artifact already exists") from exc
    try:
        written = 0
        while written < len(content):
            written += os.write(descriptor, content[written:])
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    artifact = AgentArtifact(relative, checkpoint.wish_sha256)
    outcome = AgentOutcome(
        stage="wish",
        status="ready",
        artifacts=(artifact,),
        proposed_transition="match",
    )
    evidence = {
        "schema_version": 1,
        "kind": "autonomous-workshop.wish-gate-evidence",
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "wish_sha256": checkpoint.wish_sha256,
        "canonical": True,
        "product_id_bound": True,
    }
    gate = DeterministicGateReceipt(
        stage="wish",
        gate_id="wish.contract-v1",
        passed=True,
        subject_sha256=checkpoint.wish_sha256,
        outcome_sha256=outcome.sha256,
        evidence_sha256=_host_evidence_sha256(evidence),
    )
    gates = run.host_state_root / "gates"
    gates.mkdir(mode=0o700, exist_ok=True)
    _write_private_json(gates / "0000-wish.json", evidence)
    return run.apply_outcome(outcome, gate=gate)


def _authorization_path(paths: NativeRunPaths) -> Path:
    return paths.host_state / _AUTHORIZATION_NAME


def _record_authorization(
    paths: NativeRunPaths,
    *,
    product_id: str,
    publish_requested: bool,
    create: bool,
) -> Mapping[str, Any]:
    path = _authorization_path(paths)
    current = False
    if path.exists() or path.is_symlink():
        try:
            identity = path.lstat()
            content = path.read_bytes()
        except OSError as exc:
            raise StateConflict("run authorization is unavailable") from exc
        if (
            path.is_symlink()
            or not stat.S_ISREG(identity.st_mode)
            or stat.S_IMODE(identity.st_mode) != 0o600
        ):
            raise StateConflict("run authorization must be a private regular file")
        value = _strict_json_bytes(content, label="run authorization")
        expected = {"schema_version", "kind", "product_id", "publish_requested"}
        if (
            set(value) != expected
            or value["schema_version"] != 1
            or value["kind"] != _AUTHORIZATION_KIND
            or value["product_id"] != product_id
            or type(value["publish_requested"]) is not bool
        ):
            raise StateConflict("run authorization is invalid")
        current = value["publish_requested"]
    elif not create:
        raise StateConflict("run authorization is missing")
    value = {
        "schema_version": 1,
        "kind": _AUTHORIZATION_KIND,
        "product_id": product_id,
        "publish_requested": bool(current or publish_requested),
    }
    if create or value["publish_requested"] != current:
        _write_private_json(path, value)
    return value


def _ready_contract_artifact(
    proposal: AgentOutcomeProposal,
    *,
    stage: str,
    transitions: Sequence[str],
    path: str,
) -> AgentArtifact:
    outcome = proposal.outcome
    if (
        outcome.stage != stage
        or outcome.status != "ready"
        or outcome.proposed_transition not in tuple(transitions)
        or outcome.needs
        or len(outcome.artifacts) != 1
        or outcome.artifacts[0].path != path
    ):
        raise ContractError("%s outcome is not the canonical stage proposal" % stage)
    return outcome.artifacts[0]


def _manifest_agent_artifacts(
    prefix: str, manifest: Any
) -> tuple[AgentArtifact, ...]:
    return tuple(
        AgentArtifact("%s/%s" % (prefix, entry.path), entry.sha256)
        for entry in manifest.entries
    )


def _evaluate_make_stage(
    proposal: AgentOutcomeProposal,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    subject_sha256: str,
    context: Mapping[str, Any],
) -> tuple[StageGateDecision, tuple[AgentArtifact, ...]]:
    contract_path = "artifacts/make/r%04d/made.json" % checkpoint.round_index
    artifact = _ready_contract_artifact(
        proposal,
        stage="make",
        transitions=("playtest",),
        path=contract_path,
    )
    made = _read_contract(
        run.run_root, artifact, NativeMade, label="native Made contract"
    )
    assignment = context["assignment"]
    invented = context["invented"]
    made.assert_context(
        assignment, invented, expected_round=checkpoint.round_index
    )
    canonical = made.validate_product_tree(run.run_root)
    verifier_sha256 = checkpoint.input_sha256s.get(NATIVE_CAD_VERIFIER_PATH)
    if not isinstance(verifier_sha256, str):
        raise StateConflict("native run lacks its trusted CAD verifier binding")
    cad_evidence = verify_native_made_cad(
        made,
        run_root=run.run_root,
        host_state_root=run.host_state_root,
        expected_verifier_sha256=verifier_sha256,
    )
    additional = _manifest_agent_artifacts(
        made.product_root, made.product_manifest
    )
    evidence = StageGateEvidence(
        stage="make",
        gate_id="make.sealed-revision-v1",
        validator_version="1.0.0",
        passed=True,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256=subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "made_sha256": made.made_sha256,
            "product_artifact_sha256": canonical.artifact_sha256,
            "product_tree_rehashed": True,
            "upstream_bindings_valid": True,
            "cad_receipt_sha256": cad_evidence.receipt_sha256,
            "cad_verifier_sha256": cad_evidence.verifier_sha256,
            "cad_verification_passed": cad_evidence.passed,
        },
    )
    return StageGateDecision(evidence=evidence, transition="playtest"), additional


def _evaluate_playtest_stage(
    proposal: AgentOutcomeProposal,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    subject_sha256: str,
    context: Mapping[str, Any],
) -> tuple[StageGateDecision, tuple[AgentArtifact, ...]]:
    contract_path = (
        "artifacts/playtest/r%04d/playtested.json" % checkpoint.round_index
    )
    artifact = _ready_contract_artifact(
        proposal,
        stage="playtest",
        transitions=("release", "make"),
        path=contract_path,
    )
    playtested = _read_contract(
        run.run_root,
        artifact,
        NativePlaytested,
        label="native Playtested contract",
    )
    made = context["made"]
    blueprint = context["blueprint"]
    playtested.assert_context(made, blueprint)
    canonical = playtested.validate_evidence_tree(run.run_root, made)
    verifier_sha256 = checkpoint.input_sha256s.get(NATIVE_CAD_VERIFIER_PATH)
    if not isinstance(verifier_sha256, str):
        raise StateConflict("native run lacks its trusted CAD verifier binding")
    cad_evidence = verify_native_made_cad(
        made,
        run_root=run.run_root,
        host_state_root=run.host_state_root,
        expected_verifier_sha256=verifier_sha256,
    )
    passed = playtested.verdict == "pass"
    transition = "release" if passed else "make"
    if proposal.outcome.proposed_transition != transition:
        raise ContractError("Playtest transition differs from its evidence verdict")
    additional = _manifest_agent_artifacts(
        playtested.evidence_root, playtested.evidence_manifest
    )
    evidence = StageGateEvidence(
        stage="playtest",
        gate_id="playtest.release-v1",
        validator_version="1.0.0",
        passed=passed,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256=subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "playtested_sha256": playtested.playtested_sha256,
            "product_artifact_sha256": made.product_manifest.artifact_sha256,
            "evidence_artifact_sha256": canonical.evidence.evidence_artifact_sha256,
            "required_capabilities_covered": True,
            "cad_receipt_sha256": cad_evidence.receipt_sha256,
            "cad_verification_passed": cad_evidence.passed,
            "verdict": playtested.verdict,
        },
    )
    return StageGateDecision(evidence=evidence, transition=transition), additional


def _factory_credentials(inventor_id: str) -> Any:
    suffix = inventor_id.upper().replace("-", "_")
    username = os.environ.get("FACTORY_%s_USERNAME" % suffix)
    if not isinstance(username, str) or not username:
        username = os.environ.get("FACTORY_USERNAME")
    password = os.environ.get("FACTORY_PASSWORD")
    environment: dict[str, str] = {}
    if isinstance(username, str) and username:
        environment["FACTORY_USERNAME"] = username
    if isinstance(password, str) and password:
        environment["FACTORY_PASSWORD"] = password
    return factory_credentials_from_environment(inventor_id, environment)


def _release_effect_path(run: AgentRun) -> Path:
    return run.host_state_root / "release-effect.json"


def _release_effect_wait_path(run: AgentRun) -> Path:
    return run.host_state_root / _RELEASE_EFFECT_WAIT_NAME


def _read_release_effect_wait(
    run: AgentRun, checkpoint: AgentRunCheckpoint
) -> Optional[Mapping[str, Any]]:
    """Read a credential-only Release wait bound to the current checkpoint."""

    path = _release_effect_wait_path(run)
    if not path.exists() and not path.is_symlink():
        return None
    try:
        identity = path.lstat()
        content = path.read_bytes()
    except OSError as exc:
        raise StateConflict("Release effect wait is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise StateConflict("Release effect wait must be a private file")
    try:
        value = _strict_json_bytes(content, label="Release effect wait")
    except ContractError as exc:
        raise StateConflict("Release effect wait is invalid") from exc
    expected = {
        "schema_version",
        "kind",
        "product_id",
        "stage",
        "waiting_checkpoint_sha256",
        "proposal_checkpoint_sha256",
        "proposal_subject_sha256",
        "proposal_outcome_sha256",
        "inventor_id",
        "need",
    }
    hash_fields = (
        "waiting_checkpoint_sha256",
        "proposal_checkpoint_sha256",
        "proposal_subject_sha256",
        "proposal_outcome_sha256",
    )
    if (
        set(value) != expected
        or value["schema_version"] != 1
        or value["kind"] != "autonomous-workshop.release-effect-wait"
        or value["product_id"] != checkpoint.product_id
        or value["stage"] != "release"
        or checkpoint.stage != "release"
        or checkpoint.status != "waiting"
        or value["waiting_checkpoint_sha256"] != checkpoint.checkpoint_sha256
        or not isinstance(value["inventor_id"], str)
        or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value["inventor_id"])
        is None
        or value["need"] != _FACTORY_CREDENTIALS_NEED
        or any(
            not isinstance(value[name], str)
            or re.fullmatch(r"[0-9a-f]{64}", value[name]) is None
            for name in hash_fields
        )
    ):
        raise StateConflict("Release effect wait belongs to different state")
    return value


def _write_release_effect_wait(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    proposal: AgentOutcomeProposal,
    inventor_id: str,
) -> None:
    if checkpoint.stage != "release" or checkpoint.status != "waiting":
        raise TransitionError("Release effect wait requires a waiting Release")
    _write_private_json(
        _release_effect_wait_path(run),
        {
            "schema_version": 1,
            "kind": "autonomous-workshop.release-effect-wait",
            "product_id": checkpoint.product_id,
            "stage": "release",
            "waiting_checkpoint_sha256": checkpoint.checkpoint_sha256,
            "proposal_checkpoint_sha256": proposal.checkpoint_sha256,
            "proposal_subject_sha256": proposal.subject_sha256,
            "proposal_outcome_sha256": proposal.outcome.sha256,
            "inventor_id": inventor_id,
            "need": _FACTORY_CREDENTIALS_NEED,
        },
    )


def _remove_release_effect_wait(run: AgentRun) -> None:
    path = _release_effect_wait_path(run)
    if not path.exists() and not path.is_symlink():
        return
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("Release effect wait is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise StateConflict("Release effect wait must be a regular file")
    try:
        path.unlink()
    except OSError as exc:
        raise StateConflict("Release effect wait could not be removed") from exc


def _read_release_effect(run: AgentRun, release: NativeRelease) -> Optional[Receipt]:
    path = _release_effect_path(run)
    if not path.exists() and not path.is_symlink():
        return None
    try:
        identity = path.lstat()
        content = path.read_bytes()
    except OSError as exc:
        raise StateConflict("Release effect checkpoint is unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise StateConflict("Release effect checkpoint must be a private file")
    value = _strict_json_bytes(content, label="Release effect checkpoint")
    expected = {
        "schema_version",
        "kind",
        "product_id",
        "native_release_sha256",
        "product_artifact_sha256",
        "package_artifact_sha256",
        "publication_status",
        "receipt",
    }
    if (
        set(value) != expected
        or value["schema_version"] != 1
        or value["kind"] != "autonomous-workshop.release-effect"
        or value["product_id"] != run.snapshot().product_id
        or value["native_release_sha256"] != release.release_sha256
        or value["product_artifact_sha256"] != release.product_artifact_sha256
        or value["package_artifact_sha256"]
        != release.package_manifest.artifact_sha256
        or value["publication_status"] not in ("draft", "public")
    ):
        raise StateConflict("Release effect checkpoint belongs to different bytes")
    try:
        receipt = Receipt.from_dict(value["receipt"])
    except (TypeError, ValueError, ContractError) as exc:
        raise StateConflict("Release effect receipt is invalid") from exc
    receipt.assert_artifact(release.product_artifact_sha256)
    if receipt.details.get("release_sha256") != release.package_manifest.artifact_sha256:
        raise StateConflict("Release effect receipt belongs to a different package")
    if value["publication_status"] == "public" and not receipt.is_verified_public:
        raise StateConflict("Release effect public status is not verified")
    if value["publication_status"] == "draft" and not receipt.is_verified_draft:
        raise StateConflict("Release effect draft status is not verified")
    return receipt


def _write_release_effect(
    run: AgentRun, release: NativeRelease, receipt: Receipt
) -> None:
    status = "public" if receipt.is_verified_public else "draft"
    _write_private_json(
        _release_effect_path(run),
        {
            "schema_version": 1,
            "kind": "autonomous-workshop.release-effect",
            "product_id": run.snapshot().product_id,
            "native_release_sha256": release.release_sha256,
            "product_artifact_sha256": release.product_artifact_sha256,
            "package_artifact_sha256": release.package_manifest.artifact_sha256,
            "publication_status": status,
            "receipt": receipt.to_dict(),
        },
    )


def _execute_release_effect(
    run: AgentRun,
    release: NativeRelease,
    *,
    context: Mapping[str, Any],
    publish_requested: bool,
) -> tuple[ProductRelease, Receipt]:
    made = context["made"]
    playtested = context["playtested"]
    package = release.validate_package_tree(run.run_root, made, playtested)
    assignment = context["assignment"]
    blueprint = context["blueprint"]
    wish = _load_wish(run.run_root)
    taste_root = (
        run.run_root
        / "catalog"
        / "inventors"
        / assignment.selected_inventor_id
    )
    taste = load_taste(taste_root)
    release_context = ReleaseContext(
        wish=wish,
        taste=taste,
        blueprint=blueprint,
        made=package.made,
        playtested=package.playtested,
        workspace=run.run_root,
    )
    receipt = _read_release_effect(run, release)
    credentials: Any = None
    if receipt is None or (publish_requested and receipt.is_verified_draft):
        try:
            credentials = _factory_credentials(assignment.selected_inventor_id)
        except ContractError:
            raise _FactoryCredentialsUnavailable(
                assignment.selected_inventor_id
            ) from None
    if receipt is None:
        store = InventorStore(run.host_state_root / "factory.sqlite3")
        product_id = run.snapshot().product_id
        try:
            store.register_product(
                product_id,
                "release",
                artifact_sha256=release.product_artifact_sha256,
            )
        except StateConflict:
            product = store.get_product(product_id)
            if (
                product.get("stage") != "release"
                or product.get("artifact_sha256")
                != release.product_artifact_sha256
            ):
                raise StateConflict(
                    "Factory publication state belongs to different product bytes"
                )
        writer = FactoryAgentReleaseWriter(
            store,
            assignment.selected_inventor_id,
            credentials,
        )
        receipt = writer(release_context, package.root, package.manifest)
        _write_release_effect(run, release, receipt)
    if publish_requested and receipt.is_verified_draft:
        receipt = FactoryPublicTransition(
            FactoryAgentSession(credentials)
        ).publish(receipt)
        _write_release_effect(run, release, receipt)
    product_release = ProductRelease.from_root(
        package.root,
        release.product_artifact_sha256,
        package.manual_path,
        release.to_dict()["product"]["claims"],
        receipt,
    )
    return product_release, receipt


def _evaluate_release_stage(
    proposal: AgentOutcomeProposal,
    *,
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    subject_sha256: str,
    context: Mapping[str, Any],
    publish_requested: bool,
) -> tuple[StageGateDecision, tuple[AgentArtifact, ...]]:
    artifact = _ready_contract_artifact(
        proposal,
        stage="release",
        transitions=("deliver",),
        path="artifacts/release/release.json",
    )
    release = _read_contract(
        run.run_root, artifact, NativeRelease, label="native Release contract"
    )
    release.assert_context(context["made"], context["playtested"])
    product_release, receipt = _execute_release_effect(
        run,
        release,
        context=context,
        publish_requested=publish_requested,
    )
    additional = _manifest_agent_artifacts(
        release.package_root, release.package_manifest
    )
    evidence = StageGateEvidence(
        stage="release",
        gate_id="release.product-v1",
        validator_version="1.0.0",
        passed=True,
        checkpoint_sha256=checkpoint.checkpoint_sha256,
        subject_sha256=subject_sha256,
        outcome_sha256=proposal.outcome.sha256,
        artifact_path=artifact.path,
        artifact_sha256=artifact.sha256,
        checks={
            "native_release_sha256": release.release_sha256,
            "product_release_sha256": product_release.manifest.artifact_sha256,
            "product_artifact_sha256": release.product_artifact_sha256,
            "page_url": receipt.details.get("page_url"),
            "publication_status": (
                "public" if receipt.is_verified_public else "draft"
            ),
            "package_tree_rehashed": True,
            "factory_readback_verified": True,
        },
    )
    return StageGateDecision(evidence=evidence, transition="deliver"), additional


def _persist_gate_decision(
    run: AgentRun, checkpoint: AgentRunCheckpoint, decision: StageGateDecision
) -> None:
    gates = run.host_state_root / "gates"
    gates.mkdir(mode=0o700, exist_ok=True)
    filename = "%04d-%s.json" % (checkpoint.revision, checkpoint.stage)
    _write_private_json(gates / filename, decision.to_dict())


def _agent_outcome_exists(run_root: Path) -> bool:
    path = run_root / _AGENT_OUTCOME_NAME
    if not path.exists() and not path.is_symlink():
        return False
    try:
        identity = path.lstat()
    except OSError as exc:
        raise StateConflict("agent outcome is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(identity.st_mode):
        raise StateConflict("agent outcome must be a regular file")
    return True


def _process_agent_outcome(
    run: AgentRun,
    checkpoint: AgentRunCheckpoint,
    *,
    subject_sha256: str,
    context: Mapping[str, Any],
    publish_requested: bool,
) -> AgentRunCheckpoint:
    proposal = read_agent_outcome_proposal(
        run.run_root,
        expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
        expected_subject_sha256=subject_sha256,
    )
    run.validate_outcome(proposal.outcome)
    if proposal.outcome.status != "ready":
        updated = run.apply_outcome(proposal.outcome)
        _remove_agent_outcome(run.run_root)
        return updated

    additional: tuple[AgentArtifact, ...] = ()
    if checkpoint.stage == "match":
        decision = evaluate_match_stage(
            proposal,
            run_root=run.run_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
            wish_sha256=checkpoint.wish_sha256,
            catalog=context["catalog"],
        )
    elif checkpoint.stage == "invent":
        decision = evaluate_invent_stage(
            proposal,
            run_root=run.run_root,
            expected_checkpoint_sha256=checkpoint.checkpoint_sha256,
            assignment=context["assignment"],
        )
    elif checkpoint.stage == "make":
        decision, additional = _evaluate_make_stage(
            proposal,
            run=run,
            checkpoint=checkpoint,
            subject_sha256=subject_sha256,
            context=context,
        )
    elif checkpoint.stage == "playtest":
        decision, additional = _evaluate_playtest_stage(
            proposal,
            run=run,
            checkpoint=checkpoint,
            subject_sha256=subject_sha256,
            context=context,
        )
    elif checkpoint.stage == "release":
        try:
            decision, additional = _evaluate_release_stage(
                proposal,
                run=run,
                checkpoint=checkpoint,
                subject_sha256=subject_sha256,
                context=context,
                publish_requested=publish_requested,
            )
        except _FactoryCredentialsUnavailable as unavailable:
            waiting = AgentOutcome(
                stage="release",
                status="waiting",
                artifacts=proposal.outcome.artifacts,
                needs=(_FACTORY_CREDENTIALS_NEED,),
            )
            updated = run.apply_outcome(waiting)
            _remove_agent_outcome(run.run_root)
            _write_release_effect_wait(
                run,
                updated,
                proposal=proposal,
                inventor_id=unavailable.inventor_id,
            )
            return updated
    else:  # pragma: no cover - guarded by packet preparation
        raise TransitionError("native stage cannot consume an agent proposal")

    _persist_gate_decision(run, checkpoint, decision)
    updated = run.apply_outcome(
        proposal.outcome,
        gate=decision.receipt,
        gate_subject_sha256=subject_sha256,
        additional_artifacts=additional,
    )
    _remove_agent_outcome(run.run_root)
    return updated


def _wait_at_deliver(run: AgentRun) -> AgentRunCheckpoint:
    checkpoint = run.snapshot()
    if checkpoint.stage != "deliver" or checkpoint.status != "active":
        raise TransitionError("Deliver wait requires an active Deliver checkpoint")
    return run.apply_outcome(
        AgentOutcome(
            stage="deliver",
            status="waiting",
            needs=(
                "Manufacturing and shipping were not authorized; the verified "
                "product and Release remain ready for a later Deliver effect.",
            ),
        )
    )


def _run_native_session(
    run: AgentRun,
    paths: NativeRunPaths,
    *,
    launcher: CodexNativeSessionLauncher,
    publish_requested: bool,
) -> tuple[AgentRunCheckpoint, Optional[CodexNativeSessionOutcome], int, str]:
    """Advance through native stages until complete, wait, or failure."""

    last_session: Optional[CodexNativeSessionOutcome] = None
    turns = 0
    first_method = "resume" if _session_status(paths) == "checkpointed" else "start"
    action = "resumed" if first_method == "resume" else "started"
    while turns < _MAX_NATIVE_TURNS:
        checkpoint = run.snapshot()
        if checkpoint.status in ("waiting", "failed", "complete"):
            return checkpoint, last_session, turns, action
        if checkpoint.stage == "deliver":
            return _wait_at_deliver(run), last_session, turns, action
        subject, unused_packet, context = _prepare_stage_input(run, checkpoint)
        del unused_packet

        if _agent_outcome_exists(run.run_root):
            try:
                updated = _process_agent_outcome(
                    run,
                    checkpoint,
                    subject_sha256=subject,
                    context=context,
                    publish_requested=publish_requested,
                )
            except StateConflict:
                _remove_agent_outcome(run.run_root)
            else:
                if updated.status in ("waiting", "failed", "complete"):
                    return updated, last_session, turns, action
                continue

        _remove_agent_outcome(run.run_root)
        method = "resume" if _session_status(paths) == "checkpointed" else "start"
        last_session = _launcher_call(
            launcher, method, checkpoint=checkpoint, paths=paths
        )
        turns += 1
        if not _agent_outcome_exists(run.run_root):
            raise WorkshopError(
                "native Codex session returned without agent-outcome.json"
            )
        updated = _process_agent_outcome(
            run,
            checkpoint,
            subject_sha256=subject,
            context=context,
            publish_requested=publish_requested,
        )
        if updated.status in ("waiting", "failed", "complete"):
            return updated, last_session, turns, action
    raise WorkshopError("native product run exhausted its bounded Codex turn budget")


def _session_status(paths: NativeRunPaths) -> str:
    checkpoint = paths.host_state / _SESSION_CHECKPOINT_NAME
    if not checkpoint.exists() and not checkpoint.is_symlink():
        return "not-started"
    try:
        identity = checkpoint.lstat()
    except OSError as exc:
        raise StateConflict("native Codex session checkpoint is unavailable") from exc
    if (
        checkpoint.is_symlink()
        or not stat.S_ISREG(identity.st_mode)
        or stat.S_IMODE(identity.st_mode) != 0o600
    ):
        raise StateConflict("native Codex session checkpoint is not a private file")
    return "checkpointed"


def _native_receipt(
    checkpoint: AgentRunCheckpoint,
    *,
    paths: Optional[NativeRunPaths] = None,
    session: Optional[CodexNativeSessionOutcome] = None,
    action: str,
    publish_requested: bool = False,
    turns: int = 0,
) -> dict[str, Any]:
    publication: dict[str, Any] = {
        "status": "not-created",
        "requested": bool(publish_requested),
        "reason": (
            "Factory credentials and authenticated effects remain outside the "
            "native product-run session."
        ),
    }
    needs: tuple[str, ...] = ()
    if paths is not None:
        if checkpoint.stage == "release" and checkpoint.status == "waiting":
            wait_run = AgentRun.open(
                paths.workspace, host_state_root=paths.host_state
            )
            effect_wait = _read_release_effect_wait(wait_run, checkpoint)
            if effect_wait is not None:
                needs = (effect_wait["need"],)
                publication["reason"] = effect_wait["need"]
        effect = paths.host_state / "release-effect.json"
        if effect.exists() or effect.is_symlink():
            try:
                identity = effect.lstat()
                document = _strict_json_bytes(
                    effect.read_bytes(), label="Release effect checkpoint"
                )
            except OSError as exc:
                raise StateConflict("Release effect checkpoint is unavailable") from exc
            if (
                effect.is_symlink()
                or not stat.S_ISREG(identity.st_mode)
                or stat.S_IMODE(identity.st_mode) != 0o600
            ):
                raise StateConflict("Release effect checkpoint must be a private file")
            try:
                receipt = Receipt.from_dict(document["receipt"])
            except (KeyError, TypeError, ValueError, WorkshopError) as exc:
                raise StateConflict("Release effect checkpoint is invalid") from exc
            publication = {
                "status": (
                    "public" if receipt.is_verified_public else "draft"
                ),
                "requested": bool(publish_requested),
                "page_url": receipt.details.get("page_url"),
                "cover_url": receipt.details.get("cover_url"),
                "verified": True,
            }
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "native-agent-run",
        "product_id": checkpoint.product_id,
        "status": checkpoint.status,
        "stage": checkpoint.stage,
        "revision": checkpoint.revision,
        "round": checkpoint.round_index,
        "max_rounds": checkpoint.max_rounds,
        "wish_sha256": checkpoint.wish_sha256,
        "checkpoint_sha256": checkpoint.checkpoint_sha256,
        "agent_instructions_sha256": materialized_agent_instructions_sha256(
            checkpoint
        ),
        "invalidated_stages": list(checkpoint.invalidated_stages),
        "action": action,
        "native_turns": turns,
        "publication": publication,
    }
    if needs:
        receipt["needs"] = list(needs)
    if session is not None:
        receipt["session"] = session.to_dict()
    return receipt


def start_native_run(
    wish: Wish,
    *,
    publish_requested: bool = False,
) -> Mapping[str, Any]:
    """Persist one Wish and immediately start its whole-run native session."""

    paths = native_run_paths(wish.product_id, create_container=True)
    assets = product_run_agent_assets()
    run = AgentRun.create(
        paths.workspace,
        paths.host_state,
        product_id=wish.product_id,
        wish_bytes=canonical_wish_bytes(wish),
        product_run_constitution_source=assets.constitution,
        skill_root=assets.skill_root,
        domain_skill_roots=product_run_domain_skill_roots(),
        inventor_catalog_root=_product_run_catalog_root(assets),
        max_rounds=4,
    )
    _record_authorization(
        paths,
        product_id=wish.product_id,
        publish_requested=publish_requested,
        create=True,
    )
    checkpoint = _advance_validated_wish(run)
    launcher = CodexNativeSessionLauncher()
    checkpoint, session, turns, action = _run_native_session(
        run,
        paths,
        launcher=launcher,
        publish_requested=publish_requested,
    )
    return {
        **_native_receipt(
            checkpoint,
            paths=paths,
            session=session,
            action=action,
            publish_requested=publish_requested,
            turns=turns,
        ),
        "wish": wish.to_dict(),
    }


def resume_native_run(
    product_id: str,
    *,
    publish_requested: bool = False,
) -> Mapping[str, Any]:
    """Resume the exact native session, or safely finish an interrupted start."""

    run, checkpoint = _open_native_run(product_id)
    paths = native_run_paths(product_id)
    authorization = _record_authorization(
        paths,
        product_id=product_id,
        publish_requested=publish_requested,
        create=False,
    )
    if checkpoint.status == "waiting":
        effect_wait = _read_release_effect_wait(run, checkpoint)
        if effect_wait is not None:
            try:
                _factory_credentials(effect_wait["inventor_id"])
            except ContractError:
                return _native_receipt(
                    checkpoint,
                    paths=paths,
                    action="waiting-for-factory-credentials",
                    publish_requested=authorization["publish_requested"],
                )
            _remove_release_effect_wait(run)
        checkpoint = run.resume()
    elif checkpoint.status in ("failed", "complete"):
        return _native_receipt(
            checkpoint,
            paths=paths,
            action="inspected-terminal",
            publish_requested=authorization["publish_requested"],
        )
    launcher = CodexNativeSessionLauncher()
    checkpoint, session, turns, action = _run_native_session(
        run,
        paths,
        launcher=launcher,
        publish_requested=authorization["publish_requested"],
    )
    if action == "started":
        action = "started-after-interruption"
    return _native_receipt(
        checkpoint,
        paths=paths,
        session=session,
        action=action,
        publish_requested=authorization["publish_requested"],
        turns=turns,
    )


def native_run_status(product_id: str) -> Mapping[str, Any]:
    """Return a redacted, validated native checkpoint without running a model."""

    run, checkpoint = _open_native_run(product_id)
    del run
    paths = native_run_paths(product_id)
    authorization = _record_authorization(
        paths,
        product_id=product_id,
        publish_requested=False,
        create=False,
    )
    return {
        **_native_receipt(
            checkpoint,
            paths=paths,
            action="inspected",
            publish_requested=authorization["publish_requested"],
        ),
        "session_status": _session_status(paths),
    }


__all__ = [
    "NativeRunPaths",
    "canonical_wish_bytes",
    "materialized_agent_instructions_sha256",
    "native_run_exists",
    "native_run_paths",
    "native_run_status",
    "native_stage_prompt",
    "resume_native_run",
    "start_native_run",
]
