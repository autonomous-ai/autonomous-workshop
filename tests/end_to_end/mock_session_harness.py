"""Effort-aware authenticated Codex acceptance harness."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import base64
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from typing import Any, Iterator, Mapping, Sequence
from unittest import mock

from workshop.errors import ContractError, WorkshopError
from workshop.make.native import NativeMade
from workshop.integrations.concept_images import ConceptImageProfile
from workshop.make.native_gate import NATIVE_CAD_FULL_TIER, NATIVE_CAD_VERIFIER_MODE
from workshop.release.native import NativeRelease
from workshop.runtime.concept_effects import ConceptEffectEvidence, ConceptEffectLedger
from workshop.runtime.codex import codex_supports_native_workshop
from workshop.wish import Wish
from workshop.workflow import AgentRun, WORKSHOP_EFFORTS
from workshop.workflow.native_run import (
    native_run_paths,
    native_run_status,
    resume_native_run,
    start_native_run,
)

from tests.end_to_end.deterministic_fidelity import CANONICAL_ROUTES
from tests.end_to_end.mock_session_evidence import (
    FIXTURE_SECRETS,
    TRACE_KIND,
    MockSessionEvidenceError,
    assert_no_fixture_secrets,
    read_bounded_json,
    redact_diagnostics,
    sha256_bytes,
    strict_object,
    validate_context_record,
)
from tests.end_to_end.mock_session_factory import MockSessionFactoryServer


ENABLE_ENVIRONMENT = "WORKSHOP_RUN_MOCK_SESSION_E2E"
HOME_ENVIRONMENT = "WORKSHOP_MOCK_SESSION_HOME"
EFFORT_ENVIRONMENT = "WORKSHOP_MOCK_SESSION_EFFORT"
PARTIAL_CONCEPT_ENVIRONMENT = "WORKSHOP_MOCK_SESSION_PARTIAL_CONCEPT"
DEFAULT_TURN_TIMEOUT_SECONDS = 1800
DEFAULT_ROUTE_TIMEOUT_SECONDS = 7200
_VERSION = re.compile(r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.-]+)?")


class MockSessionPrerequisiteError(RuntimeError):
    """A live acceptance prerequisite is unavailable before a Wish starts."""


@dataclass(frozen=True)
class CodexPreflight:
    binary: str
    version: str
    authenticated: bool
    python: str
    cad_runtime_ready: bool
    wrapper: str


@dataclass(frozen=True)
class BoundedProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool


@dataclass(frozen=True)
class MockSessionReport:
    product_id: str
    effort: str
    model: str
    reasoning_effort: str
    stages: tuple[str, ...]
    durations: Mapping[str, float]
    session_starts: int
    session_resumes: int
    session_id: str
    context_records_verified: int
    context_proof: str
    terminal_event_fallbacks: int
    final_stage: str
    final_status: str
    final_checkpoint_sha256: str
    publication_status: str
    total_elapsed_seconds: float
    workspace: str
    host_state: str
    protocol_calls: tuple[tuple[str, str], ...]
    concept_wait_resume: Mapping[str, Any] | None = None

    def to_dict(self, *, include_local_paths: bool = True) -> Mapping[str, Any]:
        value: dict[str, Any] = {
            "schema_version": 2,
            "kind": "autonomous-workshop.mock-session-report",
            "acceptance_scope": "context-and-integration-only",
            "product_id": self.product_id,
            "effort": self.effort,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "stages": list(self.stages),
            "durations": dict(self.durations),
            "session_starts": self.session_starts,
            "session_resumes": self.session_resumes,
            "session_id": self.session_id,
            "context_records_verified": self.context_records_verified,
            "context_proof": self.context_proof,
            "terminal_event_fallbacks": self.terminal_event_fallbacks,
            "final_stage": self.final_stage,
            "final_status": self.final_status,
            "final_checkpoint_sha256": self.final_checkpoint_sha256,
            "publication_status": self.publication_status,
            "total_elapsed_seconds": self.total_elapsed_seconds,
            "protocol_calls": [list(call) for call in self.protocol_calls],
            "evidence_limits": (
                "This proves only context-and-integration acceptance. It does not "
                "prove creative or research quality, exhaustive agent behavior, "
                "physical printing, fit, durability, manufacture, shipment, "
                "delivery, or human response."
            ),
        }
        if include_local_paths:
            value.update(
                {"workspace": self.workspace, "host_state": self.host_state}
            )
        if self.concept_wait_resume is not None:
            value["concept_wait_resume"] = dict(self.concept_wait_resume)
        return value


@dataclass(frozen=True)
class _PartialConceptWaitSnapshot:
    waiting_checkpoint_sha256: str
    proposal_checkpoint_sha256: str
    effect_checkpoint_sha256: str
    proposal_subject_sha256: str
    proposal_outcome_sha256: str
    pre_render_artifact_sha256: str
    aggregate_id: str
    role_identities: Mapping[str, str]
    completed_role_audits: Mapping[str, tuple[str, ...]]
    completed_roles: tuple[str, ...]


_PRIVATE_CONCEPT_STATUS_KEYS = frozenset(
    {
        "api_key",
        "content",
        "effect_token",
        "image",
        "image_bytes",
        "instruction",
        "intent_id",
        "operation_id",
        "outcome",
        "prompt",
        "provider_operation_id",
        "references",
        "response",
    }
)


def _mapping_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str):
                keys.add(key)
            keys.update(_mapping_keys(item))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for item in value:
            keys.update(_mapping_keys(item))
    return keys


def _assert_concept_wait_status_private(
    status: Mapping[str, Any], *, private_values: Sequence[str]
) -> None:
    exposed = _mapping_keys(status) & _PRIVATE_CONCEPT_STATUS_KEYS
    if exposed:
        raise MockSessionEvidenceError(
            "Concept wait status exposes private fields: %s"
            % ", ".join(sorted(exposed))
        )
    encoded = json.dumps(status, sort_keys=True, separators=(",", ":"))
    leaked = sorted(
        {value for value in private_values if isinstance(value, str) and value and value in encoded}
    )
    if leaked:
        raise MockSessionEvidenceError("Concept wait status exposes private values")


def _capture_partial_concept_wait(
    paths: Any,
    status: Mapping[str, Any],
    concept_calls: Sequence[tuple[Any, Mapping[str, str], Mapping[str, Any], Any]],
) -> _PartialConceptWaitSnapshot:
    private_values = list(FIXTURE_SECRETS)
    for unused_url, headers, body, unused_timeout in concept_calls:
        del unused_url, unused_timeout
        private_values.extend(
            value
            for key, value in headers.items()
            if key.lower() in {"authorization", "idempotency-key"}
        )
        for key, value in body.items():
            if key in {"prompt", "instruction"} and isinstance(value, str):
                private_values.append(value)
    private_values.extend(
        (
            "mock-concept-01",
            base64.b64encode(b"\x89PNG\r\n\x1a\nmock-session-concept-01").decode("ascii"),
        )
    )
    _assert_concept_wait_status_private(status, private_values=private_values)
    wait = read_bounded_json(
        paths.host_state / "invent-effect-wait.json", 2 * 1024 * 1024
    )
    identity_fields = (
        "waiting_checkpoint_sha256",
        "proposal_checkpoint_sha256",
        "effect_checkpoint_sha256",
        "proposal_subject_sha256",
        "proposal_outcome_sha256",
        "pre_render_artifact_sha256",
    )
    if status.get("checkpoint_sha256") != wait.get("waiting_checkpoint_sha256"):
        raise MockSessionEvidenceError(
            "Concept wait status changed its checkpoint identity"
        )
    if any(
        not isinstance(wait.get(name), str)
        or re.fullmatch(r"[0-9a-f]{64}", str(wait.get(name))) is None
        for name in identity_fields
    ):
        raise MockSessionEvidenceError("Concept wait proposal identities are invalid")
    ledger_path = paths.host_state / "concept-effects.sqlite3"
    with sqlite3.connect("file:%s?mode=ro" % ledger_path, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        aggregates = connection.execute("SELECT * FROM concept_aggregates").fetchall()
        operations = connection.execute(
            "SELECT intent_id,identity_json,state FROM concept_operations ORDER BY created_at,intent_id"
        ).fetchall()
        events = connection.execute(
            "SELECT intent_id,state FROM concept_operation_events ORDER BY event_id"
        ).fetchall()
    if len(aggregates) != 1 or len(operations) != 2:
        raise MockSessionEvidenceError(
            "partial Concept wait lacks the exact aggregate and attempted roles"
        )
    aggregate = aggregates[0]
    if (
        aggregate["product_id"] != status.get("product_id")
        or aggregate["checkpoint_sha256"] != wait["effect_checkpoint_sha256"]
        or aggregate["subject_sha256"] != wait["proposal_subject_sha256"]
        or aggregate["state"] != "planned"
    ):
        raise MockSessionEvidenceError("Concept wait aggregate identity changed")
    succeeded = [item for item in operations if item["state"] == "succeeded"]
    rejected = [item for item in operations if item["state"] == "rejected"]
    if len(succeeded) != 1 or len(rejected) != 1:
        raise MockSessionEvidenceError(
            "partial Concept wait must preserve one completed and one safely rejected role"
        )
    audits: dict[str, list[str]] = {}
    for event in events:
        audits.setdefault(str(event["intent_id"]), []).append(str(event["state"]))
    completed_audits = {
        str(item["intent_id"]): tuple(audits.get(str(item["intent_id"]), ()))
        for item in succeeded
    }
    if any(states != ("planned", "sending", "succeeded") for states in completed_audits.values()):
        raise MockSessionEvidenceError("completed Concept role audit is not exact")
    completed_roles = tuple(
        str(json.loads(item["identity_json"])["role"]) for item in succeeded
    )
    return _PartialConceptWaitSnapshot(
        **{name: str(wait[name]) for name in identity_fields},
        aggregate_id=str(aggregate["aggregate_id"]),
        role_identities={
            str(item["intent_id"]): str(item["identity_json"]) for item in operations
        },
        completed_role_audits=completed_audits,
        completed_roles=completed_roles,
    )


def _verify_partial_concept_completion(
    paths: Any, snapshot: _PartialConceptWaitSnapshot
) -> Mapping[str, Any]:
    wait_path = paths.host_state / "invent-effect-wait.json"
    if wait_path.exists() or wait_path.is_symlink():
        raise MockSessionEvidenceError("Concept wait record survived completion")
    ledger = ConceptEffectLedger(paths.host_state / "concept-effects.sqlite3")
    roles = ledger.roles(snapshot.aggregate_id)
    if not roles or any(item.state != "succeeded" for item in roles):
        raise MockSessionEvidenceError("Concept ledger did not complete every role")
    for intent_id, identity_json in snapshot.role_identities.items():
        observed = ledger.get(intent_id)
        if json.dumps(
            {"aggregate_id": observed.aggregate_id, **{
                key: getattr(observed, key)
                for key in (
                    "product_id", "checkpoint_sha256", "subject_sha256",
                    "pre_render_sha256", "source_manifest_sha256", "role",
                    "output_path", "instruction_sha256", "references", "profile_id",
                    "profile_sha256", "model", "request_schema_version",
                )
            }},
            sort_keys=True,
            separators=(",", ":"),
        ) != identity_json:
            raise MockSessionEvidenceError("Concept role intent changed on resume")
    for intent_id, states in snapshot.completed_role_audits.items():
        if tuple(item["state"] for item in ledger.audit(intent_id)) != states:
            raise MockSessionEvidenceError("completed Concept role was resent")
    checkpoint = AgentRun.open(
        paths.workspace, host_state_root=paths.host_state
    ).snapshot()
    effect_artifacts = tuple(
        item
        for item in checkpoint.stage_artifacts.get("invent", ())
        if item.path.endswith("/effect.json")
    )
    if len(effect_artifacts) != 1:
        raise MockSessionEvidenceError("accepted Invent lacks one Concept effect")
    effect_document = read_bounded_json(
        paths.workspace / effect_artifacts[0].path, 2 * 1024 * 1024
    )
    effect = ConceptEffectEvidence.from_mapping(effect_document)
    by_role = {item.role: item for item in roles}
    concept_root = Path(effect_artifacts[0].path).parent / "concept"
    if set(by_role) != {item.role for item in effect.roles}:
        raise MockSessionEvidenceError("Concept final receipt role set differs")
    for receipt in effect.roles:
        operation = by_role[receipt.role]
        response = operation.response or {}
        image = paths.workspace / concept_root / receipt.path
        try:
            image_bytes = image.read_bytes()
        except OSError as exc:
            raise MockSessionEvidenceError(
                "Concept final receipt image is unavailable"
            ) from exc
        if (
            receipt.intent_sha256 != operation.evidence_intent_sha256
            or response.get("image_sha256") != receipt.image_sha256
            or response.get("media_type") != receipt.media_type
            or response.get("output_path") != receipt.path
            or sha256_bytes(image_bytes) != receipt.image_sha256
        ):
            raise MockSessionEvidenceError(
                "Concept final receipt differs from ledger or exact bytes"
            )
    invent_gates = tuple((paths.host_state / "gates").glob("*-invent.json"))
    if len(invent_gates) != 1:
        raise MockSessionEvidenceError(
            "partial Concept acceptance lacks one accepted Invent gate"
        )
    gate_document = read_bounded_json(invent_gates[0], 2 * 1024 * 1024)
    gate = gate_document.get("evidence")
    if not isinstance(gate, Mapping):
        raise MockSessionEvidenceError("accepted Invent gate evidence is malformed")
    if (
        gate.get("subject_sha256") != snapshot.proposal_subject_sha256
        or gate.get("outcome_sha256") != snapshot.proposal_outcome_sha256
        or gate.get("checks", {}).get("pre_render_artifact_sha256")
        != snapshot.pre_render_artifact_sha256
        or gate.get("checks", {}).get("concept_effect_sha256")
        != effect.concept_effect_sha256
        or gate.get("checks", {}).get("concept_role_count") != len(effect.roles)
    ):
        raise MockSessionEvidenceError(
            "accepted Invent gate changed the pending Concept proposal"
        )
    return {
        "status_privacy": "verified",
        "waiting_checkpoint_sha256": snapshot.waiting_checkpoint_sha256,
        "effect_checkpoint_sha256": snapshot.effect_checkpoint_sha256,
        "proposal_subject_sha256": snapshot.proposal_subject_sha256,
        "proposal_outcome_sha256": snapshot.proposal_outcome_sha256,
        "pre_render_artifact_sha256": snapshot.pre_render_artifact_sha256,
        "completed_roles_before_wait": list(snapshot.completed_roles),
        "sealed_role_count": len(effect.roles),
        "final_receipts": "verified-exact-ledger-and-image-bytes",
        "completed_roles_resent": False,
        "invent_cognition_repeated": False,
    }


def run_bounded_process(
    command: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    timeout_seconds: int,
) -> BoundedProcessResult:
    if not command or not 1 <= timeout_seconds <= 21_600:
        raise ValueError("mock-session worker command or timeout is invalid")
    process = subprocess.Popen(
        list(command),
        cwd=str(Path(cwd).resolve()),
        env=dict(environment),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=(os.name == "posix"),
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "posix":
            os.killpg(process.pid, signal.SIGTERM)
        else:  # pragma: no cover - CI and supported Workshop hosts are POSIX
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGKILL)
            else:  # pragma: no cover
                process.kill()
            stdout, stderr = process.communicate(timeout=5)
    return BoundedProcessResult(
        returncode=124 if timed_out else process.returncode,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
    )


def preflight_codex(
    *,
    which: Any = shutil.which,
    runner: Any = subprocess.run,
    module_finder: Any = importlib.util.find_spec,
    check_fixture: bool = True,
) -> CodexPreflight:
    missing_cad_modules = [
        name for name in ("build123d", "cadgen") if module_finder(name) is None
    ]
    if missing_cad_modules:
        raise MockSessionPrerequisiteError(
            "the active Python interpreter lacks the CAD runtime (%s): %s; "
            "run with the locked repository environment"
            % (", ".join(missing_cad_modules), Path(sys.executable).resolve())
        )
    binary = which("codex")
    if not binary:
        raise MockSessionPrerequisiteError("Codex CLI is not installed or on PATH")
    resolved_binary = Path(binary).resolve()
    wrapper = Path(__file__).with_name("mock_codex_passthrough.py").resolve()
    if resolved_binary == wrapper:
        raise MockSessionPrerequisiteError(
            "the real Codex resolution points at the acceptance wrapper"
        )
    if not wrapper.is_file() or not os.access(wrapper, os.X_OK):
        raise MockSessionPrerequisiteError(
            "the mock-session Codex pass-through is missing or not executable"
        )
    version_result = runner(
        [str(resolved_binary), "--version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    output = version_result.stdout if isinstance(version_result.stdout, str) else ""
    match = _VERSION.search(output)
    version = match.group(0) if match else "0.0.0"
    if version_result.returncode != 0 or not codex_supports_native_workshop(version):
        raise MockSessionPrerequisiteError(
            "Codex CLI is missing native Workshop support: %s" % version
        )
    login = runner(
        [str(resolved_binary), "login", "status"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    if login.returncode != 0:
        raise MockSessionPrerequisiteError(
            "Codex CLI is not authenticated; run `codex login`"
        )
    if check_fixture:
        try:
            with MockSessionFactoryServer("mock-session-preflight"):
                pass
        except OSError as exc:
            raise MockSessionPrerequisiteError(
                "the loopback Factory fixture could not start"
            ) from exc
    return CodexPreflight(
        binary=str(resolved_binary),
        version=version,
        authenticated=True,
        python=str(Path(sys.executable).resolve()),
        cad_runtime_ready=True,
        wrapper=str(wrapper),
    )


@contextmanager
def _environment(values: Mapping[str, str]) -> Iterator[None]:
    previous = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _write_private_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    path.chmod(0o600)


def _read_trace(run_root: Path) -> tuple[Mapping[str, Any], ...]:
    path = run_root / ".mock-session" / "turns.jsonl"
    if path.is_symlink() or not path.is_file():
        raise MockSessionEvidenceError("mock-session turn trace is missing")
    values: list[Mapping[str, Any]] = []
    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), 1
    ):
        try:
            value = json.loads(line, object_pairs_hook=strict_object)
        except ValueError as exc:
            raise MockSessionEvidenceError(
                "mock-session trace line %d is invalid" % line_number
            ) from exc
        if not isinstance(value, Mapping) or value.get("kind") != TRACE_KIND:
            raise MockSessionEvidenceError(
                "mock-session trace line %d has invalid identity" % line_number
            )
        values.append(dict(value))
    return tuple(values)


def _assert_agent_write_ownership(
    trace: Sequence[Mapping[str, Any]], *, effort: str
) -> None:
    root_sources = {
        "invent": {"invent-source.json"},
        "make": {"spark-creative-source.json"},
        "playtest": {"playtest-source.json"},
    }
    for turn in trace:
        stage = turn.get("stage", "unknown")
        writes = turn.get("agent_writes")
        if not isinstance(writes, list) or not writes:
            raise MockSessionEvidenceError(
                "%s:%s agent write inventory is missing" % (effort, stage)
            )
        for relative in writes:
            allowed = (
                relative == "agent-outcome.json"
                or re.fullmatch(
                    r"\.(?:cache|local-cache|work-cache|workshop-cache)/"
                    r"(?:xdg/)?ezdxf/font_manager_cache\.json",
                    relative,
                )
                is not None
                or (stage == "invent" and relative == "design/invent-source.json")
                or relative in root_sources.get(str(stage), set())
                or relative.startswith("authored/")
                or relative.startswith("sources/")
                or relative.startswith("notes/")
                or relative.startswith("work/")
                or relative.startswith("artifacts/%s/" % stage)
                or (stage == "invent" and relative.startswith("artifacts/concept/"))
                or (stage == "make" and relative == ".make-proof-ready.json")
            )
            if not allowed:
                raise MockSessionEvidenceError(
                    "%s:%s agent write crossed ownership into %s"
                    % (effort, stage, relative)
                )


def _terminal_evidence_mode(
    value: Mapping[str, Any], *, effort: str, stage: str
) -> str:
    if value.get("timed_out") is not False:
        raise MockSessionEvidenceError(
            "%s:%s exceeded its bounded native turn" % (effort, stage)
        )
    observed = value.get("terminal_observed")
    forwarded = value.get("terminal_forwarded")
    returncode = value.get("returncode")
    if observed is True and forwarded is True and returncode == 0:
        return "public-terminal"
    if observed is False and forwarded is False and type(returncode) is int:
        artifacts = value.get("proposal_artifacts")
        context_error = value.get("context_proof_error")
        if artifacts == [] and context_error == "context record is missing or malformed":
            # A bounded Codex turn can end without a proposal and remain
            # resumable.  It is a real native turn, but not a completed stage
            # and not a marker-based finalization fallback.
            return "recoverable-unfinished"
        if (
            isinstance(artifacts, list)
            and bool(artifacts)
            and context_error is None
        ):
            # The host accepted exact proposal bytes even though the public
            # terminal event was absent.  This is the narrow marker fallback.
            return "finalized-marker-fallback"
    raise MockSessionEvidenceError(
        "%s:%s has inconsistent native terminal evidence" % (effort, stage)
    )


def _accepted_stage_trace(
    trace: Sequence[Mapping[str, Any]], *, effort: str
) -> tuple[str, ...]:
    """Return completed lifecycle stages while validating unfinished turns."""

    modes = tuple(
        _terminal_evidence_mode(
            value,
            effort=effort,
            stage=str(value.get("stage", "unknown")),
        )
        for value in trace
    )
    completed: list[str] = []
    for index, (value, mode) in enumerate(zip(trace, modes)):
        if value.get("make_proof_boundary") is True:
            continue
        stage = value.get("stage")
        if mode != "recoverable-unfinished":
            completed.append(stage)
            continue
        next_completed = next(
            (
                later.get("stage")
                for later, later_mode in zip(trace[index + 1 :], modes[index + 1 :])
                if later.get("make_proof_boundary") is not True
                and later_mode != "recoverable-unfinished"
            ),
            None,
        )
        if next_completed != stage:
            raise MockSessionEvidenceError(
                "%s:%s recoverable turn is not followed by a completed %s stage"
                % (effort, stage, stage)
            )
    return tuple(completed)


def _accepted_make_proof_boundaries(
    trace: Sequence[Mapping[str, Any]],
    host_state: Path,
    *,
    effort: str,
) -> tuple[int, ...]:
    """Return only trace boundaries backed by the host's private receipt."""

    boundaries = tuple(
        index
        for index, value in enumerate(trace)
        if value.get("make_proof_boundary") is True
    )
    if len(boundaries) > 1:
        raise MockSessionEvidenceError(
            "%s:multiple intermediate Make proof turns were observed" % effort
        )
    acceptance_root = host_state / "make-proof-acceptances"
    acceptance_paths = (
        tuple(sorted(acceptance_root.glob("*.json")))
        if acceptance_root.is_dir() and not acceptance_root.is_symlink()
        else ()
    )
    if effort == "spark":
        if boundaries or acceptance_paths:
            raise MockSessionEvidenceError(
                "spark:unexpected intermediate Make proof acceptance"
            )
        return boundaries
    if len(boundaries) != 1 or len(acceptance_paths) != 1:
        raise MockSessionEvidenceError(
            "%s:one host-accepted Make proof boundary is required" % effort
        )
    boundary_checkpoint = trace[boundaries[0]].get("checkpoint_sha256")
    acceptance = read_bounded_json(acceptance_paths[0], 16 * 1024)
    expected_marker = {
        "schema_version": 1,
        "kind": "autonomous-workshop.make-proof-ready",
        "checkpoint_sha256": boundary_checkpoint,
    }
    marker_bytes = (
        json.dumps(
            expected_marker,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    if (
        acceptance.get("schema_version") != 1
        or acceptance.get("kind")
        != "autonomous-workshop.make-proof-acceptance"
        or acceptance.get("stage") != "make"
        or acceptance.get("checkpoint_sha256") != boundary_checkpoint
        or acceptance_paths[0].stem != boundary_checkpoint
        or acceptance.get("marker_sha256")
        != hashlib.sha256(marker_bytes).hexdigest()
        or not isinstance(acceptance.get("proof_artifacts"), list)
        or len(acceptance["proof_artifacts"]) != 13
    ):
        raise MockSessionEvidenceError(
            "%s:Make proof trace lacks its exact host acceptance" % effort
        )
    return boundaries


def _validate_trace(
    run_root: Path,
    host_state: Path,
    *,
    effort: str,
) -> tuple[tuple[Mapping[str, Any], ...], str]:
    trace = _read_trace(run_root)
    expected = CANONICAL_ROUTES[effort]
    boundaries = _accepted_make_proof_boundaries(
        trace, host_state, effort=effort
    )
    if boundaries:
        boundary = boundaries[0]
        if (
            trace[boundary].get("stage") != "make"
            or boundary + 1 >= len(trace)
            or trace[boundary + 1].get("stage") != "make"
        ):
            raise MockSessionEvidenceError(
                "%s:intermediate Make proof boundary is not followed by Make" % effort
            )
    stages = _accepted_stage_trace(trace, effort=effort)
    if stages != expected:
        raise MockSessionEvidenceError(
            "%s:stage trace differs: expected %r, observed %r"
            % (effort, expected, stages)
        )
    methods = tuple(value.get("method") for value in trace)
    if methods != ("start",) + ("resume",) * (len(trace) - 1):
        raise MockSessionEvidenceError(
            "%s:native start/resume trace differs: %r" % (effort, methods)
        )
    models = {value.get("model") for value in trace}
    reasoning = {value.get("reasoning_effort") for value in trace}
    if len(models) != 1 or None in models or len(reasoning) != 1 or None in reasoning:
        raise MockSessionEvidenceError(
            "%s:runtime configuration changed across turns" % effort
        )
    stage_agent_writes: dict[str, set[str]] = {}
    for value in trace:
        stage = value["stage"]
        cumulative_writes = stage_agent_writes.setdefault(stage, set())
        writes = value.get("agent_writes")
        if isinstance(writes, list):
            cumulative_writes.update(
                relative for relative in writes if isinstance(relative, str)
            )
        evidence_mode = _terminal_evidence_mode(
            value, effort=effort, stage=stage
        )
        prohibited = value.get("prohibited_items")
        if prohibited:
            raise MockSessionEvidenceError(
                "%s:%s used prohibited activity: %s"
                % (effort, stage, prohibited)
            )
        if (
            evidence_mode != "recoverable-unfinished"
            and value.get("context_proof_error") is not None
        ):
            raise MockSessionEvidenceError(
                "%s:%s wrapper rejected context proof: %s"
                % (effort, stage, value["context_proof_error"])
            )
        checkpoint = value.get("checkpoint_sha256")
        if not isinstance(checkpoint, str):
            raise MockSessionEvidenceError(
                "%s:%s trace lacks checkpoint binding" % (effort, stage)
            )
        subject = value.get("subject_sha256")
        expected_packet_path = ".mock-session/packets/%s-%s.json" % (
            checkpoint,
            subject,
        )
        if value.get("stage_packet_path") != expected_packet_path:
            raise MockSessionEvidenceError(
                "%s:%s trace has an invalid packet snapshot path" % (effort, stage)
            )
        packet_path = run_root / expected_packet_path
        if value.get("stage_packet_sha256") != sha256_bytes(packet_path.read_bytes()):
            raise MockSessionEvidenceError(
                "%s:%s packet snapshot changed" % (effort, stage)
            )
        if (
            value.get("make_proof_boundary") is not True
            and evidence_mode != "recoverable-unfinished"
        ):
            validate_context_record(
                run_root / value["context_record_path"],
                run_root=run_root,
                packet_path=packet_path,
                agent_writes=sorted(cumulative_writes),
                proposal_artifacts=value.get("proposal_artifacts"),
                turn_output_hashes=value.get("turn_output_hashes"),
            )
            cumulative_writes.clear()
    _assert_agent_write_ownership(trace, effort=effort)
    session = read_bounded_json(host_state / "codex-session.json", 64 * 1024)
    session_id = session.get("thread_id")
    if not isinstance(session_id, str):
        raise MockSessionEvidenceError("%s:session checkpoint lacks thread id" % effort)
    observed_ids = {
        thread_id
        for value in trace
        for thread_id in value.get("thread_ids", [])
        if isinstance(thread_id, str)
    }
    if observed_ids != {session_id}:
        raise MockSessionEvidenceError(
            "%s:session identity drift: checkpoint=%s observed=%r"
            % (effort, session_id, sorted(observed_ids))
        )
    return trace, session_id


def _read_contract(path: Path, contract_type: Any) -> Any:
    return contract_type.from_mapping(
        json.loads(path.read_text(encoding="utf-8"))
    )


def _assert_route_state(
    paths: Any,
    receipt: Mapping[str, Any],
    server: MockSessionFactoryServer,
    *,
    effort: str,
) -> tuple[Any, NativeMade, NativeRelease]:
    if (receipt.get("stage"), receipt.get("status")) != ("release", "complete"):
        raise MockSessionEvidenceError(
            "%s:run did not reach terminal published Release: %r"
            % (effort, receipt)
        )
    if receipt.get("effort") != effort:
        raise MockSessionEvidenceError("%s:receipt effort changed" % effort)
    publication = receipt.get("publication")
    if not isinstance(publication, Mapping) or publication.get("status") != "public":
        raise MockSessionEvidenceError(
            "%s:Release lacks verified public Factory state" % effort
        )
    checkpoint = AgentRun.open(
        paths.workspace, host_state_root=paths.host_state
    ).snapshot()
    if (checkpoint.stage, checkpoint.status, checkpoint.effort) != (
        "release",
        "complete",
        effort,
    ):
        raise MockSessionEvidenceError(
            "%s:terminal checkpoint differs from receipt" % effort
        )
    expected = set(CANONICAL_ROUTES[effort])
    if set(checkpoint.stage_artifacts) != {"wish", *expected}:
        raise MockSessionEvidenceError(
            "%s:sealed stage topology differs: %r"
            % (effort, sorted(checkpoint.stage_artifacts))
        )
    for forbidden in ("match", "concept", "deliver"):
        if forbidden in checkpoint.stage_artifacts:
            raise MockSessionEvidenceError(
                "%s:fabricated %s stage artifacts" % (effort, forbidden)
            )
    for stage, artifacts in checkpoint.stage_artifacts.items():
        for artifact in artifacts:
            path = paths.workspace / artifact.path
            if (
                path.is_symlink()
                or not path.is_file()
                or sha256_bytes(path.read_bytes()) != artifact.sha256
            ):
                raise MockSessionEvidenceError(
                    "%s:%s sealed artifact changed at %s"
                    % (effort, stage, artifact.path)
                )
    for omitted in {"invent", "playtest"} - expected:
        if (paths.workspace / "artifacts" / omitted).exists():
            raise MockSessionEvidenceError(
                "%s:fabricated passed-through %s artifacts" % (effort, omitted)
            )
        if (paths.host_state / "evidence" / omitted).exists():
            raise MockSessionEvidenceError(
                "%s:fabricated passed-through %s evidence" % (effort, omitted)
            )
    gate_paths = sorted((paths.host_state / "gates").glob("*.json"))
    gate_stages = tuple(path.stem.split("-", 1)[1] for path in gate_paths)
    if gate_stages != ("wish", *CANONICAL_ROUTES[effort]):
        raise MockSessionEvidenceError(
            "%s:gate topology differs: %r" % (effort, gate_stages)
        )
    made_artifact = checkpoint.stage_artifacts["make"][0]
    made = _read_contract(paths.workspace / made_artifact.path, NativeMade)
    expected_cad_stages = ["make"]
    if effort == "quest":
        expected_cad_stages.append("playtest")
    expected_cad_stages.append("release")
    for stage in expected_cad_stages:
        candidates = sorted((paths.host_state / "evidence" / stage).glob("*-cad-gate.json"))
        if len(candidates) != 1:
            raise MockSessionEvidenceError(
                "%s:%s CAD evidence count differs" % (effort, stage)
            )
        evidence = read_bounded_json(candidates[0], 3 * 1024 * 1024)
        if (
            evidence.get("passed") is not True
            or evidence.get("verification_tier") != NATIVE_CAD_FULL_TIER
            or evidence.get("verifier_mode") != NATIVE_CAD_VERIFIER_MODE
            or evidence.get("made_sha256") != made.made_sha256
            or "--fresh" not in evidence.get("command", [])
            or "--exports" not in evidence.get("command", [])
            or "--strict-fit" not in evidence.get("command", [])
        ):
            raise MockSessionEvidenceError(
                "%s:%s CAD evidence is incomplete" % (effort, stage)
            )
    creative_stage = "make" if effort == "spark" else "invent"
    creative_names = {
        Path(item.path).name
        for item in checkpoint.stage_artifacts[creative_stage]
    }
    if not {"assignment.json", "invented.json"} <= creative_names:
        raise MockSessionEvidenceError(
            "%s:%s lacks folded Inventor provenance" % (effort, creative_stage)
        )
    release_artifact = checkpoint.stage_artifacts["release"][0]
    release = _read_contract(paths.workspace / release_artifact.path, NativeRelease)
    omission = paths.workspace / "artifacts/release/package/PLAYTEST-NOT-RUN.json"
    if effort == "quest":
        if "playtest" not in checkpoint.stage_artifacts or omission.exists():
            raise MockSessionEvidenceError(
                "quest:Release does not bind active Playtest truthfully"
            )
    elif (
        "playtest" in checkpoint.stage_artifacts
        or not omission.is_file()
        or release.product.get("playtest_status") != "not-run"
    ):
        raise MockSessionEvidenceError(
            "%s:Release does not record canonical Playtest omission" % effort
        )
    effect = read_bounded_json(paths.host_state / "release-effect.json", 2 * 1024 * 1024)
    manual_sha256 = sha256_bytes(server.state.manual)
    details = effect.get("receipt", {}).get("details", {})
    if (
        effect.get("publication_status") != "public"
        or effect.get("manual_sha256") != manual_sha256
        or details.get("manual_readback_sha256") != manual_sha256
    ):
        raise MockSessionEvidenceError(
            "%s:Factory receipt does not bind public manual bytes" % effort
        )
    server.assert_complete()
    if (paths.workspace / "agent-outcome.json").exists():
        raise MockSessionEvidenceError(
            "%s:accepted agent outcome was not consumed" % effort
        )
    return checkpoint, made, release


def _fixed_wish(product_id: str) -> Wish:
    return Wish.create(
        product_id,
        (
            "Create a compact tactile pattern toy made from six identical, flat, "
            "rounded arc tiles. Each support-free tile is about 30 mm across and "
            "5 mm thick; loose placement alone should form rings, waves, and radial "
            "arrangements. Treat the assembled export as a six-body print plate, "
            "not one printed part: declare its combined generator PRINTABLE = False "
            "and state that explicitly in the CAD README, while keeping the single "
            "tile generator printable. After every CAD edit, run the materialized "
            "verify_project command with --fresh --exports --strict-fit twice in "
            "succession, compare the declared generated-byte hashes across those "
            "two final replays, and do not finalize until every declared output is "
            "byte-identical. Refresh all declared generated bytes from the second "
            "replay and make no later CAD source or declaration edits. Use no "
            "connectors, relief, text, hardware, electronics, or moving joints."
        ),
        constraints={
            "audience": "ages 14 and up",
            "physical_production": "outside this context-acceptance run",
            "materials": "single-material consumer FDM",
        },
        context={"source": "authenticated-codex-context-acceptance"},
    )


def _projection_snapshot(repository: Path, product_id: str) -> set[Path]:
    return set((repository / "toys").glob("*-%s" % product_id))


def _remove_new_projections(before: set[Path], repository: Path, product_id: str) -> None:
    for path in _projection_snapshot(repository, product_id) - before:
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)


def run_mock_session_acceptance(
    home: Path,
    *,
    effort: str,
    turn_timeout_seconds: int = DEFAULT_TURN_TIMEOUT_SECONDS,
    partial_concept_roles: bool = False,
) -> MockSessionReport:
    if effort not in CANONICAL_ROUTES or effort not in WORKSHOP_EFFORTS:
        raise ContractError("mock-session effort must be spark, forge, or quest")
    if type(turn_timeout_seconds) is not int or not 1 <= turn_timeout_seconds <= 3600:
        raise ContractError("mock-session turn timeout must be from 1 to 3600 seconds")
    home = Path(home).resolve()
    if home.exists() and any(home.iterdir()):
        raise ContractError("mock-session home must be absent or empty")
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(home, 0o700)
    wrapper = Path(__file__).with_name("mock_codex_passthrough.py").resolve()
    if not os.access(wrapper, os.X_OK):
        raise MockSessionPrerequisiteError(
            "mock-session Codex pass-through is not executable"
        )
    product_id = "mock-session-%s-%s" % (
        effort,
        hashlib.sha256(str(home).encode("utf-8")).hexdigest()[:10],
    )
    workspace = home / "runs" / product_id / "workspace"
    host_state = home / "state" / product_id
    _write_private_json(
        home / "mock-session-config.json",
        {"schema_version": 1, "turn_timeout_seconds": turn_timeout_seconds},
    )
    _write_private_json(
        home / "mock-session-diagnostics.json",
        {
            "schema_version": 1,
            "product_id": product_id,
            "effort": effort,
            "workspace": str(workspace),
            "host_state": str(host_state),
        },
    )
    profile = ConceptImageProfile()
    concept_credentials = home / "concept-images.json"
    _write_private_json(
        concept_credentials,
        {
            "schema_version": 1,
            "profile": {
                "profile_id": profile.profile_id,
                "origin": profile.origin,
                "model": profile.model,
                "request_schema_version": profile.request_schema_version,
                "supports_idempotency": profile.supports_idempotency,
                "supports_operation_readback": profile.supports_operation_readback,
                "supports_absence_proof": profile.supports_absence_proof,
            },
            "api_key": FIXTURE_SECRETS[0],
        },
    )
    concept_calls = []

    def concept_transport(url, headers, body, timeout):
        concept_calls.append((url, dict(headers), json.loads(body), timeout))
        if partial_concept_roles and effort != "spark" and len(concept_calls) == 2:
            raise OSError("mock Concept transport failed before transmission")
        image = b"\x89PNG\r\n\x1a\nmock-session-concept-%02d" % len(concept_calls)
        return 200, {"Content-Type": "application/json"}, json.dumps(
            {
                "data": [
                    {
                        "b64_json": base64.b64encode(image).decode("ascii"),
                        "id": "mock-concept-%02d" % len(concept_calls),
                    }
                ]
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    environment = {
        "WORKSHOP_HOME": str(home),
        "WORKSHOP_CODEX_BIN": str(wrapper),
        "FACTORY_USERNAME": "mock-session-service",
        "FACTORY_PASSWORD": FIXTURE_SECRETS[0],
        "WORKSHOP_CONCEPT_IMAGE_CREDENTIALS_FILE": str(concept_credentials),
    }
    repository = Path(__file__).resolve().parents[2]
    projections_before = _projection_snapshot(repository, product_id)
    started = time.monotonic()
    partial_wait_evidence: Mapping[str, Any] | None = None
    try:
        with _environment(environment), MockSessionFactoryServer(product_id) as server:
            with mock.patch(
                "workshop.workflow.native_run._FACTORY_TRANSPORT",
                server.transport,
            ), mock.patch(
                "workshop.workflow.native_run._FACTORY_PROJECT_FILE_TRANSPORT",
                server.project_file_transport,
            ), mock.patch(
                "workshop.workflow.native_run._CONCEPT_IMAGE_TRANSPORT",
                concept_transport,
            ):
                receipt = start_native_run(
                    _fixed_wish(product_id), effort=effort
                )
                if partial_concept_roles:
                    if effort == "spark":
                        raise ContractError(
                            "partial Concept acceptance requires Forge or Quest"
                        )
                    if (receipt.get("stage"), receipt.get("status")) != (
                        "invent",
                        "waiting",
                    ):
                        raise MockSessionEvidenceError(
                            "%s:partial Concept effect did not wait at Invent" % effort
                        )
                    paths = native_run_paths(product_id)
                    status = native_run_status(product_id)
                    if (status.get("stage"), status.get("status")) != (
                        "invent",
                        "waiting",
                    ):
                        raise MockSessionEvidenceError(
                            "%s:status did not preserve the Invent wait" % effort
                        )
                    pending_session = read_bounded_json(
                        paths.host_state / "codex-session.json", 64 * 1024
                    )
                    pending_session_id = pending_session.get("thread_id")
                    if not isinstance(pending_session_id, str) or not pending_session_id:
                        raise MockSessionEvidenceError(
                            "%s:Invent wait lacks a bound native session" % effort
                        )
                    trace_before_effect_resume = _read_trace(paths.workspace)
                    partial_snapshot = _capture_partial_concept_wait(
                        paths, status, concept_calls
                    )
                    assert_no_fixture_secrets(
                        paths.workspace,
                        paths.host_state,
                        extra_text=(json.dumps(status, sort_keys=True),),
                    )
                    receipt = resume_native_run(product_id)
                    if (receipt.get("stage"), receipt.get("status")) != (
                        "make",
                        "active",
                    ):
                        raise MockSessionEvidenceError(
                            "%s:Concept reconciliation did not advance to Make" % effort
                        )
                    if _read_trace(paths.workspace) != trace_before_effect_resume:
                        raise MockSessionEvidenceError(
                            "%s:Concept reconciliation repeated Invent cognition" % effort
                        )
                    resumed_session = read_bounded_json(
                        paths.host_state / "codex-session.json", 64 * 1024
                    )
                    if resumed_session.get("thread_id") != pending_session_id:
                        raise MockSessionEvidenceError(
                            "%s:Concept reconciliation changed the native session" % effort
                        )
                    partial_wait_evidence = _verify_partial_concept_completion(
                        paths, partial_snapshot
                    )
                    receipt = resume_native_run(product_id)
            # Resolve the production paths while the isolated WORKSHOP_HOME is
            # still authoritative. Validation deliberately happens after the
            # server closes, but it must not fall back to the developer's home.
            paths = native_run_paths(product_id)
        elapsed = round(time.monotonic() - started, 6)
        checkpoint, unused_made, unused_release = _assert_route_state(
            paths, receipt, server, effort=effort
        )
        del unused_made, unused_release
        trace, session_id = _validate_trace(
            paths.workspace, paths.host_state, effort=effort
        )
        expected_concept_calls = (
            0
            if effort == "spark"
            else sum(
                item.path.startswith("artifacts/concept/")
                and item.path.endswith((".png", ".jpg", ".jpeg", ".webp"))
                for item in checkpoint.stage_artifacts["invent"]
            )
        )
        expected_transport_calls = expected_concept_calls + int(
            partial_concept_roles and effort != "spark"
        )
        if len(concept_calls) != expected_transport_calls:
            raise MockSessionEvidenceError(
                "%s:Concept image calls differ from sealed role artifacts" % effort
            )
        session = receipt.get("session")
        if not isinstance(session, Mapping) or session.get("used_web_search") is not False:
            raise MockSessionEvidenceError(
                "%s:final native receipt does not exclude web search" % effort
            )
        assert_no_fixture_secrets(
            paths.workspace,
            paths.host_state,
            extra_text=(json.dumps(receipt, sort_keys=True),),
        )
        report = MockSessionReport(
            product_id=product_id,
            effort=effort,
            model=str(trace[0]["model"]),
            reasoning_effort=str(trace[0]["reasoning_effort"]),
            stages=CANONICAL_ROUTES[effort],
            durations={
                str(value["stage"]): float(value["elapsed_seconds"])
                for value in trace
            },
            session_starts=1,
            session_resumes=len(trace) - 1,
            session_id=session_id,
            context_records_verified=sum(
                value.get("make_proof_boundary") is not True
                and _terminal_evidence_mode(
                    value,
                    effort=effort,
                    stage=str(value["stage"]),
                )
                != "recoverable-unfinished"
                for value in trace
            ),
            context_proof="verified-final-bytes-and-run-root-inputs",
            terminal_event_fallbacks=sum(
                _terminal_evidence_mode(
                    value,
                    effort=effort,
                    stage=str(value["stage"]),
                )
                == "finalized-marker-fallback"
                for value in trace
            ),
            final_stage=str(receipt["stage"]),
            final_status=str(receipt["status"]),
            final_checkpoint_sha256=str(checkpoint.checkpoint_sha256),
            publication_status=str(receipt["publication"]["status"]),
            total_elapsed_seconds=elapsed,
            workspace=str(paths.workspace),
            host_state=str(paths.host_state),
            protocol_calls=tuple(server.state.loopback_calls),
            concept_wait_resume=partial_wait_evidence,
        )
        _write_private_json(
            home / ("mock-session-report-%s.json" % effort),
            report.to_dict(include_local_paths=True),
        )
        return report
    except WorkshopError:
        raise
    finally:
        _remove_new_projections(projections_before, repository, product_id)


__all__ = [
    "BoundedProcessResult",
    "CodexPreflight",
    "DEFAULT_ROUTE_TIMEOUT_SECONDS",
    "DEFAULT_TURN_TIMEOUT_SECONDS",
    "EFFORT_ENVIRONMENT",
    "ENABLE_ENVIRONMENT",
    "HOME_ENVIRONMENT",
    "MockSessionPrerequisiteError",
    "MockSessionReport",
    "PARTIAL_CONCEPT_ENVIRONMENT",
    "preflight_codex",
    "redact_diagnostics",
    "run_bounded_process",
    "run_mock_session_acceptance",
]
