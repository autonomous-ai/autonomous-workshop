"""Real-Codex, minimal-work acceptance harness for the native Workshop run."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Iterator, Mapping, Sequence

from workshop.errors import ContractError, WorkshopError
from workshop.runtime.codex import codex_supports_native_workshop
from workshop.runtime.package_data import BUNDLED_INVENTOR_IDS
from workshop.wish import Wish
from workshop.workflow.native_run import (
    NativeRunExternalTransports,
    native_run_paths,
    resume_native_run,
    start_native_run,
)

from tests.end_to_end.mock_session_protocols import MockSessionProtocolServer


ENABLE_ENVIRONMENT = "WORKSHOP_RUN_MOCK_SESSION_E2E"
HOME_ENVIRONMENT = "WORKSHOP_MOCK_SESSION_HOME"
MAX_CONTEXT_RECORD_BYTES = 64 * 1024
CONTEXT_KIND = "autonomous-workshop.mock-session-context"
TRACE_KIND = "autonomous-workshop.mock-session-turn"
EXPECTED_STAGES = ("match", "invent", "concept", "make", "playtest", "release")
FIXTURE_SECRETS = (
    "mock-session-concept-secret",
    "mock-session-factory-secret",
    "mock-session-access-token",
)
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STRATEGY = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_CONTEXT_FIELDS = {
    "schema_version",
    "kind",
    "stage",
    "checkpoint_sha256",
    "subject_sha256",
    "instructions",
    "used_inputs",
    "strategy",
    "outputs",
    "deferred_work",
}
_FORBIDDEN_OUTPUT_PARTS = frozenset(
    (
        "agent-outcome.json",
        "STAGE.json",
        "sealed-concept.json",
        "host-state",
        "checkpoints",
        "gates",
        "receipts",
    )
)


class MockSessionPrerequisiteError(RuntimeError):
    pass


class MockSessionEvidenceError(AssertionError):
    pass


@dataclass(frozen=True)
class CodexPreflight:
    binary: str
    version: str
    authenticated: bool
    python: str
    cad_runtime_ready: bool


@dataclass(frozen=True)
class MockSessionReport:
    product_id: str
    model: str
    reasoning_effort: str
    stages: tuple[str, ...]
    durations: Mapping[str, float]
    session_starts: int
    session_resumes: int
    transport_retries: int
    context_records_verified: int
    context_proof: str
    final_stage: str
    final_status: str
    final_checkpoint_sha256: str
    total_elapsed_seconds: float
    workspace: str
    host_state: str
    protocol_calls: tuple[tuple[str, str], ...]

    def to_dict(self) -> Mapping[str, Any]:
        return {
            "schema_version": 1,
            "kind": "autonomous-workshop.mock-session-report",
            "acceptance_scope": "context-and-integration-only",
            "product_id": self.product_id,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
            "stages": list(self.stages),
            "durations": dict(self.durations),
            "session_starts": self.session_starts,
            "session_resumes": self.session_resumes,
            "transport_retries": self.transport_retries,
            "context_records_verified": self.context_records_verified,
            "context_proof": self.context_proof,
            "final_stage": self.final_stage,
            "final_status": self.final_status,
            "final_checkpoint_sha256": self.final_checkpoint_sha256,
            "total_elapsed_seconds": self.total_elapsed_seconds,
            "workspace": self.workspace,
            "host_state": self.host_state,
            "protocol_calls": [list(call) for call in self.protocol_calls],
            "evidence_limits": (
                "Does not prove product quality, research quality, physical printing, "
                "fit, durability, manufacture, publication, shipment, delivery, or "
                "human response."
            ),
        }


@dataclass(frozen=True)
class BoundedProcessResult:
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool


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
    )
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        timed_out = True
        process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate(timeout=5)
    return BoundedProcessResult(
        returncode=124 if timed_out else process.returncode,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
    )


def redact_diagnostics(value: str) -> str:
    result = value
    for secret in FIXTURE_SECRETS:
        result = result.replace(secret, "<redacted>")
    return result


def validate_concept_boundary_instruction(source: str) -> None:
    """Fail fast if Concept again waits on host-rendered images before finalizing."""

    required = (
        "First you finalize those pre-render instructions and return control.",
        "Missing rendered images before finalization is the expected state",
        "Do not wait for image paths in `descriptor.json` to exist",
        "Run the finalizer now, before any rendered image exists",
        "The finalizer must succeed before the host calls the image provider",
    )
    normalized = " ".join(source.split())
    missing = [statement for statement in required if statement not in normalized]
    if missing:
        raise MockSessionEvidenceError(
            "Concept production instructions lost the pre-render boundary: %s"
            % missing
        )


def _strict_object(pairs: Sequence[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _read_json(path: Path, maximum: int) -> Mapping[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise MockSessionEvidenceError("mock-session JSON is not a regular file: %s" % path)
    content = path.read_bytes()
    if not 1 <= len(content) <= maximum:
        raise MockSessionEvidenceError("mock-session JSON size is invalid: %s" % path)
    try:
        value = json.loads(content.decode("utf-8"), object_pairs_hook=_strict_object)
    except (UnicodeError, ValueError) as exc:
        raise MockSessionEvidenceError("mock-session JSON is malformed: %s" % path) from exc
    if not isinstance(value, Mapping):
        raise MockSessionEvidenceError("mock-session JSON must contain one object: %s" % path)
    return dict(value)


def _safe_run_path(run_root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value or "\\" in value:
        raise MockSessionEvidenceError("%s must be a run-relative path" % label)
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value or any(part in ("", ".", "..") for part in pure.parts):
        raise MockSessionEvidenceError("%s must be a canonical run-relative path" % label)
    target = run_root.joinpath(*pure.parts)
    try:
        target.relative_to(run_root)
    except ValueError as exc:
        raise MockSessionEvidenceError("%s escapes the run root" % label) from exc
    return target


def _bound_files(
    values: Any,
    *,
    run_root: Path,
    label: str,
    forbid_host_outputs: bool,
    observed_hashes: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    if not isinstance(values, list) or not values:
        raise MockSessionEvidenceError("%s must be a non-empty array" % label)
    paths: list[str] = []
    for index, item in enumerate(values):
        if not isinstance(item, Mapping) or set(item) != {"path", "sha256"}:
            raise MockSessionEvidenceError("%s[%d] fields are invalid" % (label, index))
        relative = item["path"]
        target = _safe_run_path(run_root, relative, "%s[%d].path" % (label, index))
        if target.is_symlink() or not target.is_file():
            raise MockSessionEvidenceError("%s[%d] is not a regular file" % (label, index))
        digest = (
            observed_hashes.get(relative)
            if observed_hashes is not None
            else hashlib.sha256(target.read_bytes()).hexdigest()
        )
        if digest is None:
            raise MockSessionEvidenceError(
                "%s[%d] %s has no turn-time hash" % (label, index, relative)
            )
        if item["sha256"] != digest:
            raise MockSessionEvidenceError(
                "%s[%d] %s sha256 is stale" % (label, index, relative)
            )
        if forbid_host_outputs and any(part in _FORBIDDEN_OUTPUT_PARTS for part in PurePosixPath(relative).parts):
            raise MockSessionEvidenceError("%s[%d] crosses a host-owned boundary" % (label, index))
        paths.append(relative)
    if len(paths) != len(set(paths)):
        raise MockSessionEvidenceError("%s paths must be unique" % label)
    return tuple(paths)


def validate_context_record(
    record_path: Path,
    *,
    run_root: Path,
    packet_path: Path,
    agent_writes: Sequence[str] | None = None,
    proposal_artifacts: Sequence[str] | None = None,
    context_output_hashes: Mapping[str, str] | None = None,
) -> Mapping[str, Any]:
    record = _read_json(record_path, MAX_CONTEXT_RECORD_BYTES)
    packet = _read_json(packet_path, 512 * 1024)
    if set(record) != _CONTEXT_FIELDS:
        raise MockSessionEvidenceError("mock-session context record fields are invalid")
    if record["schema_version"] != 1 or record["kind"] != CONTEXT_KIND:
        raise MockSessionEvidenceError("mock-session context record identity is invalid")
    for field in ("stage", "checkpoint_sha256", "subject_sha256"):
        if record[field] != packet.get(field):
            raise MockSessionEvidenceError("mock-session context record has stale %s" % field)
    if _SHA256.fullmatch(str(record["checkpoint_sha256"])) is None or _SHA256.fullmatch(str(record["subject_sha256"])) is None:
        raise MockSessionEvidenceError("mock-session context binding is malformed")
    instructions = _bound_files(
        record["instructions"],
        run_root=run_root,
        label="instructions",
        forbid_host_outputs=False,
    )
    required = {
        "AGENTS.md",
        ".agents/skills/autonomous-workshop/SKILL.md",
    }
    if not required <= set(instructions) or not any(
        path.startswith(".agents/skills/autonomous-workshop/references/")
        for path in instructions
    ):
        raise MockSessionEvidenceError("mock-session context omitted production instructions")
    inputs = packet.get("inputs")
    used_inputs = record["used_inputs"]
    if not isinstance(inputs, Mapping) or not isinstance(used_inputs, list) or not used_inputs:
        raise MockSessionEvidenceError("mock-session used_inputs are invalid")
    if any(not isinstance(key, str) or key not in inputs for key in used_inputs):
        raise MockSessionEvidenceError("mock-session context cites an unrelated input key")
    if len(used_inputs) != len(set(used_inputs)):
        raise MockSessionEvidenceError("mock-session used_inputs must be unique")
    if not isinstance(record["strategy"], str) or _STRATEGY.fullmatch(record["strategy"]) is None:
        raise MockSessionEvidenceError("mock-session strategy is invalid")
    outputs = _bound_files(
        record["outputs"],
        run_root=run_root,
        label="outputs",
        forbid_host_outputs=True,
        observed_hashes=context_output_hashes,
    )
    if agent_writes is not None and not set(outputs) <= set(agent_writes):
        raise MockSessionEvidenceError("mock-session output inventory differs from this turn's writes")
    if proposal_artifacts is not None:
        if not proposal_artifacts or any(
            not isinstance(path, str)
            or not _safe_run_path(run_root, path, "proposal artifact").is_file()
            for path in proposal_artifacts
        ):
            raise MockSessionEvidenceError("mock-session finalizer proposal artifacts are unavailable")
    deferred = record["deferred_work"]
    if not isinstance(deferred, list) or not deferred or any(
        not isinstance(value, str) or not value.strip() or len(value) > 500
        for value in deferred
    ):
        raise MockSessionEvidenceError("mock-session deferred_work is invalid")
    return record


def validate_stage_packet_inputs(packet_path: Path, *, run_root: Path) -> tuple[str, ...]:
    """Rehash every path/digest pair that the host placed in a stage packet."""

    packet = _read_json(packet_path, 512 * 1024)
    inputs = packet.get("inputs")
    if not isinstance(inputs, Mapping):
        raise MockSessionEvidenceError("mock-session stage packet inputs are invalid")
    observed: list[str] = []

    def verify(path_value: Any, digest_value: Any, label: str) -> None:
        if not isinstance(path_value, str) or _SHA256.fullmatch(str(digest_value)) is None:
            raise MockSessionEvidenceError("%s path/digest binding is malformed" % label)
        target = _safe_run_path(run_root, path_value, "%s path" % label)
        if target.is_symlink() or not target.is_file():
            raise MockSessionEvidenceError("%s input is unavailable" % label)
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest_value:
            raise MockSessionEvidenceError("%s input bytes are stale" % label)
        observed.append(path_value)

    def walk(value: Any, label: str) -> None:
        if isinstance(value, Mapping):
            if "path" in value and "sha256" in value:
                verify(value["path"], value["sha256"], label)
            for key, item in value.items():
                if isinstance(key, str) and key.endswith("_path"):
                    digest_key = key[:-5] + "_sha256"
                    if digest_key in value:
                        verify(item, value[digest_key], "%s.%s" % (label, key[:-5]))
                walk(item, "%s.%s" % (label, key))
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, "%s[%d]" % (label, index))

    walk(inputs, "inputs")
    if len(observed) != len(set(observed)):
        observed = list(dict.fromkeys(observed))
    return tuple(observed)


def preflight_codex(
    *,
    which: Any = shutil.which,
    runner: Any = subprocess.run,
    module_finder: Any = importlib.util.find_spec,
) -> CodexPreflight:
    missing_cad_modules = [
        name for name in ("build123d", "cadgen") if module_finder(name) is None
    ]
    if missing_cad_modules:
        raise MockSessionPrerequisiteError(
            "the active Python interpreter lacks the CAD runtime (%s): %s; "
            "run this command with the repository virtual environment"
            % (", ".join(missing_cad_modules), Path(sys.executable).resolve())
        )
    binary = which("codex")
    if not binary:
        raise MockSessionPrerequisiteError("Codex CLI is not installed or on PATH")
    version_result = runner(
        [binary, "--version"], capture_output=True, text=True, timeout=10, check=False
    )
    version_text = version_result.stdout if isinstance(version_result.stdout, str) else ""
    match = re.search(r"\d+(?:\.\d+){1,3}(?:[-+][A-Za-z0-9.-]+)?", version_text)
    version = match.group(0) if match else "0.0.0"
    if version_result.returncode != 0 or not codex_supports_native_workshop(version):
        raise MockSessionPrerequisiteError("Codex CLI is missing native Workshop support: %s" % version)
    login = runner(
        [binary, "login", "status"], capture_output=True, text=True, timeout=15, check=False
    )
    if login.returncode != 0:
        raise MockSessionPrerequisiteError("Codex CLI is not authenticated; run `codex login`")
    return CodexPreflight(
        str(Path(binary).resolve()),
        version,
        True,
        str(Path(sys.prefix) / "bin" / "python"),
        True,
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


def _trace(run_root: Path) -> tuple[Mapping[str, Any], ...]:
    path = run_root / ".mock-session" / "turns.jsonl"
    if path.is_symlink() or not path.is_file():
        raise MockSessionEvidenceError("mock-session turn trace is missing")
    values = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        try:
            value = json.loads(line, object_pairs_hook=_strict_object)
        except ValueError as exc:
            raise MockSessionEvidenceError("mock-session trace line %d is invalid" % line_number) from exc
        if not isinstance(value, Mapping) or value.get("kind") != TRACE_KIND:
            raise MockSessionEvidenceError("mock-session trace line %d has invalid identity" % line_number)
        values.append(dict(value))
    return tuple(values)


def _assert_no_secrets(run_root: Path) -> None:
    encoded = tuple(secret.encode("utf-8") for secret in FIXTURE_SECRETS)
    for path in run_root.rglob("*"):
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 16 * 1024 * 1024:
            continue
        content = path.read_bytes()
        if any(secret in content for secret in encoded):
            raise MockSessionEvidenceError("fixture secret leaked into the Codex workspace: %s" % path)


def _validate_run(run_root: Path, receipt: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    trace = _trace(run_root)
    stages = tuple(value.get("stage") for value in trace)
    if stages != EXPECTED_STAGES:
        raise MockSessionEvidenceError("mock-session stage trace differs: %r" % (stages,))
    models = {value.get("model") for value in trace}
    efforts = {value.get("reasoning_effort") for value in trace}
    if len(models) != 1 or None in models or len(efforts) != 1 or None in efforts:
        raise MockSessionEvidenceError("mock-session runtime configuration changed across turns")
    if any(value.get("returncode") != 0 for value in trace):
        raise MockSessionEvidenceError("a mock-session Codex turn failed")
    prohibited = {
        item
        for value in trace
        for item in value.get("prohibited_items", [])
    }
    if prohibited:
        raise MockSessionEvidenceError("Codex used prohibited mock-session activity: %s" % sorted(prohibited))
    for value in trace:
        checkpoint = value["checkpoint_sha256"]
        packet_path = run_root / ".mock-session" / "packets" / (checkpoint + ".json")
        validate_stage_packet_inputs(packet_path, run_root=run_root)
        validate_context_record(
            run_root / value["context_record_path"],
            run_root=run_root,
            packet_path=packet_path,
            agent_writes=value.get("agent_writes"),
            proposal_artifacts=value.get("proposal_artifacts"),
            context_output_hashes=value.get("context_output_hashes"),
        )
    session = receipt.get("session")
    if not isinstance(session, Mapping) or session.get("used_web_search") is not False:
        raise MockSessionEvidenceError("mock-session receipt does not prove the final turn avoided web search")
    _assert_no_secrets(run_root)
    return trace


def run_mock_session_acceptance(
    home: Path,
    *,
    native_turn_timeout_seconds: int = 300,
    native_model: str = "gpt-5.6-luna",
    native_reasoning_effort: str = "low",
) -> MockSessionReport:
    home = Path(home).resolve()
    if home.exists() and any(home.iterdir()):
        raise ContractError("mock-session home must be absent or empty")
    home.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(home, 0o700)
    wrapper = Path(__file__).with_name("mock_codex_passthrough.py").resolve()
    if not os.access(wrapper, os.X_OK):
        raise MockSessionPrerequisiteError("mock-session Codex pass-through is not executable")
    product_id = "mock-session-pocket-token-" + hashlib.sha256(
        str(home).encode("utf-8")
    ).hexdigest()[:10]
    environment = {
        "WORKSHOP_HOME": str(home),
        "WORKSHOP_CODEX_BIN": str(wrapper),
        "CONCEPT_IMAGES_API_KEY": FIXTURE_SECRETS[0],
        "CONCEPT_IMAGES_ENDPOINT": "https://mock-session.invalid/concept-images",
        "CONCEPT_IMAGES_MODEL": "mock-session-image",
        "FACTORY_PASSWORD": FIXTURE_SECRETS[1],
    }
    for inventor_id in BUNDLED_INVENTOR_IDS:
        suffix = inventor_id.upper().replace("-", "_")
        environment["FACTORY_%s_USERNAME" % suffix] = inventor_id
    started = time.monotonic()
    with _environment(environment):
        paths = native_run_paths(product_id, create=True)
        (home / "mock-session-diagnostics.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "product_id": product_id,
                    "workspace": str(paths.workspace),
                    "host_state": str(paths.host_state),
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        server = MockSessionProtocolServer()
        server.state.run_root = paths.workspace
        server.state.slug = product_id
        with server:
            transports = NativeRunExternalTransports(
                concept_image_opener=server.concept_opener,
                factory_transport=server.factory_transport,
            )
            runtime_options = {
                "publish_requested": False,
                "external_transports": transports,
                "native_turn_timeout_seconds": native_turn_timeout_seconds,
                "native_model": native_model,
                "native_reasoning_effort": native_reasoning_effort,
            }
            recovery_attempts = 0
            try:
                receipt = start_native_run(
                    Wish.create(
                        product_id,
                        (
                            "Create one 30 mm by 5 mm single-part solid pocket token: "
                            "a round disk with gently chamfered edges and one straight "
                            "orientation flat, with no relief, recesses, holes, text, "
                            "moving parts, or fit interfaces, solely for a "
                            "context-and-integration acceptance run."
                        ),
                        constraints={
                            "acceptance_mode": "minimal-valid-digital-artifacts",
                            "geometry_scope": "solid-round-token-with-chamfer-and-flat-only",
                            "forbidden_geometry": [
                                "relief",
                                "recesses",
                                "holes",
                                "text",
                                "moving-parts",
                                "fit-interfaces",
                            ],
                            "manufacture": "not-authorized",
                            "publication": "not-authorized",
                        },
                        context={"source": "real-codex-mock-session-e2e"},
                    ),
                    **runtime_options,
                )
            except WorkshopError as exc:
                if "native Codex session did not complete" not in str(exc):
                    raise
                recovery_attempts = 1
                receipt = resume_native_run(product_id, **runtime_options)
    elapsed = round(time.monotonic() - started, 6)
    if receipt.get("stage") != "deliver" or receipt.get("status") != "waiting":
        raise WorkshopError("mock-session run did not reach the private Deliver boundary")
    if receipt.get("publication", {}).get("status") != "draft":
        raise MockSessionEvidenceError("mock-session Release was not retained as a private draft")
    trace = _validate_run(paths.workspace, receipt)
    if not server.state.concept_requests:
        raise MockSessionEvidenceError("production Concept adapter made no loopback request")
    if not server.state.concept_pre_render_verified:
        raise MockSessionEvidenceError("Concept image effect did not begin from a finalized pre-render proposal")
    protocol_paths = tuple(path for unused_method, path in server.state.calls)
    if not any(path.endswith("/designs/import") for path in protocol_paths):
        raise MockSessionEvidenceError("production Factory writer made no loopback import")
    model = str(trace[0]["model"])
    effort = str(trace[0]["reasoning_effort"])
    return MockSessionReport(
        product_id=product_id,
        model=model,
        reasoning_effort=effort,
        stages=EXPECTED_STAGES,
        durations={str(value["stage"]): float(value["elapsed_seconds"]) for value in trace},
        session_starts=1,
        session_resumes=len(trace) - 1,
        transport_retries=recovery_attempts,
        context_records_verified=len(trace),
        context_proof="verified",
        final_stage=str(receipt["stage"]),
        final_status=str(receipt["status"]),
        final_checkpoint_sha256=str(receipt["checkpoint_sha256"]),
        total_elapsed_seconds=elapsed,
        workspace=str(paths.workspace),
        host_state=str(paths.host_state),
        protocol_calls=tuple(server.state.calls),
    )
