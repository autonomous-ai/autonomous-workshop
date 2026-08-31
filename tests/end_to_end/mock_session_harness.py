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
        return value


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
        # This trace is inspected only after the production host accepted the
        # exact proposal and completed the route. The missing terminal is the
        # temporary marker-based launcher fail-open, not independent evidence.
        return "finalized-marker-fallback"
    raise MockSessionEvidenceError(
        "%s:%s has inconsistent native terminal evidence" % (effort, stage)
    )


def _validate_trace(
    run_root: Path,
    host_state: Path,
    *,
    effort: str,
) -> tuple[tuple[Mapping[str, Any], ...], str]:
    trace = _read_trace(run_root)
    expected = CANONICAL_ROUTES[effort]
    boundaries = tuple(
        index
        for index, value in enumerate(trace)
        if value.get("make_proof_boundary") is True
    )
    if len(boundaries) > 1:
        raise MockSessionEvidenceError(
            "%s:multiple intermediate Make proof turns were observed" % effort
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
    stages = tuple(
        value.get("stage")
        for value in trace
        if value.get("make_proof_boundary") is not True
    )
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
    for value in trace:
        stage = value["stage"]
        prohibited = value.get("prohibited_items")
        if prohibited:
            raise MockSessionEvidenceError(
                "%s:%s used prohibited activity: %s"
                % (effort, stage, prohibited)
            )
        if value.get("context_proof_error") is not None:
            raise MockSessionEvidenceError(
                "%s:%s wrapper rejected context proof: %s"
                % (effort, stage, value["context_proof_error"])
            )
        _terminal_evidence_mode(value, effort=effort, stage=stage)
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
        if value.get("make_proof_boundary") is not True:
            validate_context_record(
                run_root / value["context_record_path"],
                run_root=run_root,
                packet_path=packet_path,
                agent_writes=value.get("agent_writes"),
                proposal_artifacts=value.get("proposal_artifacts"),
                turn_output_hashes=value.get("turn_output_hashes"),
            )
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
                value.get("make_proof_boundary") is not True for value in trace
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
    "preflight_codex",
    "redact_diagnostics",
    "run_bounded_process",
    "run_mock_session_acceptance",
]
