"""The host's side of a seeded Make's batch (ADR 0098 decisions 3 and 4).

A run that froze ``seed.batch`` (MAKE-OPTIONS schema 4) runs its checks as
one host batch before any native Make turn:

- **pass**: the batch's last layer ran the Make finalizer, so the run's
  proposal exists and the host's ordinary Make gate reads it. No native turn
  is started.
- **check failure**: the attempt is recorded with a failure packet, which the
  next ``STAGE.json`` carries as ``seeded_batch_failure``; the native session
  then repairs only what the packet names. Its Make proposal is gated by the
  batch again (``gate_proposal``): the check layers rerun on the proposed
  bytes, reusing every unchanged pass, and a failure is a host gate rejection
  with a fresh packet.
- **harness failure**: the run stops with ``SeededBatchHarnessFailure``,
  naming each failed step and its log, for the operator. No model is asked to
  repair a tool. ``workshop resume`` reruns the batch; passed steps are
  reused.

Runs without a frozen batch, including every run seeded before ADR 0098,
never reach this module. Nothing here reasons or repairs: it composes the
fixed plan from sealed inputs, runs it, and reads exit codes.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
from pathlib import Path
from typing import Any, Mapping, Optional

from workshop.errors import ContractError, StateConflict, WorkshopError
from workshop.make import seeded_batch
from workshop.make.make_round_guard import NONCE_TABLE_NAME
from workshop.runtime.execution import minimal_tool_environment
from workshop.runtime.make_round_hook import MAKE_ROUND_GUARD_DIRECTORY
from workshop.wish.seed import SEED_PRODUCT, check_seed_product, contract_geometry_ids, contract_is_moving, \
    contract_is_powered
from workshop.workflow.agent_run import frozen_seed_batch

ATTEMPTS = "seeded-batch"
NONCE_ISSUER = "host-batch"
CHECK_LAYERS = tuple(layer for layer in seeded_batch.LAYERS
                     if layer not in ("seed", "product", "parts", "finalize"))
FINALIZER = ".agents/skills/autonomous-workshop/scripts/stage_proposal.py"
SOURCE = "work/seeded/spark-source.json"
CAD = "cad"
AGENT_OUTCOME = "agent-outcome.json"


class SeededBatchHarnessFailure(WorkshopError):
    """A batch step failed as a harness, not as a check: the run stops for
    the operator."""


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"


def _write(path: Path, value: Mapping[str, Any]) -> str:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    content = _canonical(dict(value))
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)
    return _sha256(content)


def _attempt_path(host_state_root: Path, checkpoint_sha256: str) -> Path:
    return Path(host_state_root) / ATTEMPTS / ("%s.json" % checkpoint_sha256)


def read_attempt(host_state_root: Path, checkpoint_sha256: str) -> Optional[dict]:
    path = _attempt_path(host_state_root, checkpoint_sha256)
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_bytes())
    except ValueError as exc:
        raise StateConflict("the seeded batch attempt record is invalid") from exc
    if not isinstance(value, dict) or value.get("checkpoint_sha256") != checkpoint_sha256:
        raise StateConflict("the seeded batch attempt record is invalid")
    return value


def batch_due(run_root: Path, host_state_root: Path, checkpoint_sha256: str) -> bool:
    """Whether the host runs the batch before this Make checkpoint's first
    native turn: the run froze a batch, and none ran for this checkpoint."""

    if frozen_seed_batch(Path(run_root)) is None:
        return False
    return read_attempt(host_state_root, checkpoint_sha256) is None


def current_failure(run_root: Path, host_state_root: Path, checkpoint_sha256: str) -> Optional[dict]:
    """The failure packet ``STAGE.json`` carries for this checkpoint, or None."""

    if frozen_seed_batch(Path(run_root)) is None:
        return None
    attempt = read_attempt(host_state_root, checkpoint_sha256)
    if attempt is None or attempt.get("status") != seeded_batch.CHECK_FAILURE:
        return None
    return attempt["packet"]


def check_tool(run_root: Path) -> None:
    """The batch tool this host would run is the one the run froze."""

    frozen = frozen_seed_batch(Path(run_root))
    if frozen is None:
        raise StateConflict("this run froze no seeded batch")
    if frozen["tool_sha256"] != seeded_batch.module_sha256():
        raise SeededBatchHarnessFailure(
            "seeded batch: this Workshop's batch tool is not the one the run froze (MAKE-OPTIONS seed.batch "
            "tool_sha256); resume it with the Workshop version that started it")


def issue_seed_nonce(host_state_root: Path, component: str) -> str:
    """Issue one component round's seed nonce as host state, as the guard
    issues the Manager's: a record with no agent type or id."""

    table = Path(host_state_root) / MAKE_ROUND_GUARD_DIRECTORY / NONCE_TABLE_NAME
    if not table.parent.is_dir():
        raise StateConflict("the make_round guard is not installed for this run")
    nonce = secrets.token_hex(16)
    record = {"nonce": nonce, "component": "part_%s.step.py" % component, "agent_type": None,
              "agent_id": None, "session_id": None, "tool_use_id": None, "issuer": NONCE_ISSUER}
    line = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    descriptor = os.open(str(table), os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, line)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return nonce


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def plan(run_root: Path, round_index: int, *, python: str = sys.executable) -> tuple:
    """``(steps, project)`` for this run's Make round, composed only from
    sealed inputs: the Wish's contract, the seed's approval and product."""

    run_root = Path(run_root)
    wish = _json(run_root / "WISH.json")
    contract = (wish.get("context") or {}).get("design_contract")
    if not isinstance(contract, dict):
        raise StateConflict("a seeded run seals a Design Contract")
    approval = _json(run_root / "seed" / "APPROVAL.json")
    product = check_seed_product((run_root / "seed" / SEED_PRODUCT).read_bytes())
    product_root = run_root / ("artifacts/make/r%04d/product" % round_index)
    project = product_root / CAD
    source = run_root / SOURCE
    finalizer = (python, str(run_root / FINALIZER), "--run-root", str(run_root), "make",
                 "--product-root", product_root.relative_to(run_root).as_posix(),
                 "--cad-project-path", CAD, "--cad-verification-path", "%s/measure/verification-pipeline.md" % CAD,
                 "--source", str(source))
    inputs = seeded_batch.PlanInputs(
        project=project, python=python, skills_root=run_root / ".agents/skills",
        contract_path=run_root / "WISH.json", roles=contract_geometry_ids(contract),
        nozzle=float(approval["nozzle_mm"]),
        coupled_interfaces=seeded_batch.coupled_interface_ids(contract),
        powered=contract_is_powered(contract), moving=contract_is_moving(contract),
        image_derived=bool(wish.get("references")),
        concept_sha256=seeded_batch.concept_sha256(product["concept"]), finalizer=finalizer)
    return seeded_batch.run_plan(inputs, run_root=run_root, product_root=product_root, source=source), project


def environment(run_root: Path) -> dict:
    """What every step sees: no credential, the run's own temp directory."""

    private = Path(run_root) / ".tmp"
    private.mkdir(mode=0o700, exist_ok=True)
    return {**minimal_tool_environment(), "TMPDIR": str(private), "WORKSHOP_PYTHON": sys.executable,
            "PYTHONNOUSERSITE": "1"}


def _previous(project: Path) -> Optional[dict]:
    path = project / seeded_batch.RECORD
    try:
        return json.loads(path.read_bytes())
    except (OSError, ValueError):
        return None


def _stop(record: Mapping[str, Any]) -> SeededBatchHarnessFailure:
    lines = ["%s: %s (%s)" % (item["id"], item.get("reason"), " ".join(item["argv"][:4]))
             for item in seeded_batch.harness_failures(record)]
    return SeededBatchHarnessFailure(
        "seeded batch harness failure; no model is asked to repair a tool. Fix the harness, refresh the run's "
        "tools if needed, and run workshop resume (passed steps are reused). Failed: %s. Each step's output is "
        "in %s" % ("; ".join(lines), seeded_batch.RECORD))


def run_for_checkpoint(run_root: Path, host_state_root: Path, checkpoint_sha256: str, round_index: int, *,
                       runner: Optional[seeded_batch.Runner] = None) -> dict:
    """Run the whole batch once for a Make checkpoint and record the attempt.

    Returns the attempt; raises SeededBatchHarnessFailure on a harness
    failure (also recorded, so a resume reruns rather than skips it)."""

    check_tool(run_root)
    steps, project = plan(run_root, round_index)
    record_path = project / seeded_batch.RECORD
    record = seeded_batch.run_batch(
        steps, project, runner=runner or seeded_batch.environment_runner(environment(run_root)),
        previous=_previous(project), issue_nonce=lambda component: issue_seed_nonce(host_state_root, component),
        record_path=record_path)
    record_sha256 = _sha256(record_path.read_bytes())
    attempt = {"schema_version": 1, "checkpoint_sha256": checkpoint_sha256, "status": record["status"],
               "record_sha256": record_sha256, "executor": "host-batch"}
    if record["status"] == seeded_batch.CHECK_FAILURE:
        attempt["packet"] = seeded_batch.failure_packet(record, record_sha256)
    if record["status"] == seeded_batch.PASS:
        # The proposal the finalizer wrote on this pass, which alone the gate
        # need not rerun the batch for.
        outcome = Path(run_root) / AGENT_OUTCOME
        if not outcome.is_file():
            raise SeededBatchHarnessFailure("seeded batch: the finalizer passed but wrote no %s" % AGENT_OUTCOME)
        attempt["proposal_sha256"] = _sha256(outcome.read_bytes())
    if record["status"] == seeded_batch.HARNESS_FAILURE:
        # Not kept as this checkpoint's attempt: a resume after the operator's
        # fix runs the batch again.
        _write(Path(host_state_root) / ATTEMPTS / "last-harness-failure.json", attempt)
        raise _stop(record)
    _write(_attempt_path(host_state_root, checkpoint_sha256), attempt)
    return attempt


# How the accepted Make's checks ran, for the Make record (ADR 0098): the
# batch passed and finalized with no native turn, or a native repair turn
# proposed Make and the host reran the batch's check layers as the gate.
FINALIZED_BY_BATCH = "batch-finalized"
GATED_BY_BATCH = "batch-gated"


def _gate_summary(how: str, record_sha256: str) -> dict:
    return {"executor": NONCE_ISSUER, "proposed_by": "host-batch" if how == FINALIZED_BY_BATCH else "native-turn",
            "gate": how, "record": seeded_batch.RECORD, "record_sha256": record_sha256,
            "tool_sha256": seeded_batch.module_sha256()}


def gate_proposal(run_root: Path, host_state_root: Path, checkpoint_sha256: str, round_index: int, *,
                  runner: Optional[seeded_batch.Runner] = None) -> dict:
    """The host gate on a native repair turn's Make proposal: the check
    layers again on the proposed bytes, reusing unchanged passes. A proposal
    the batch itself finalized on a pass is not rerun.

    Returns what the Make record shows of it; ContractError on a check
    failure (the next STAGE.json carries the fresh packet);
    SeededBatchHarnessFailure on a harness failure."""

    attempt = read_attempt(host_state_root, checkpoint_sha256)
    outcome = Path(run_root) / AGENT_OUTCOME
    if (attempt is not None and attempt.get("status") == seeded_batch.PASS and outcome.is_file()
            and attempt.get("proposal_sha256") == _sha256(outcome.read_bytes())):
        return _gate_summary(FINALIZED_BY_BATCH, attempt["record_sha256"])
    check_tool(run_root)
    steps, project = plan(run_root, round_index)
    record_path = project / seeded_batch.RECORD
    record = seeded_batch.run_batch(
        steps, project, runner=runner or seeded_batch.environment_runner(environment(run_root)),
        previous=_previous(project), issue_nonce=lambda component: issue_seed_nonce(host_state_root, component),
        record_path=record_path, layers=CHECK_LAYERS)
    if record["status"] == seeded_batch.HARNESS_FAILURE:
        raise _stop(record)
    record_sha256 = _sha256(record_path.read_bytes())
    if record["status"] == seeded_batch.PASS:
        return _gate_summary(GATED_BY_BATCH, record_sha256)
    packet = seeded_batch.failure_packet(record, record_sha256)
    _write(_attempt_path(host_state_root, checkpoint_sha256),
           {"schema_version": 1, "checkpoint_sha256": checkpoint_sha256, "status": record["status"],
            "record_sha256": record_sha256, "executor": "host-batch", "packet": packet})
    raise ContractError("the seeded batch fails on the proposed bytes: %s" % "; ".join(
        "%s exit %s" % (item["id"], item["exit_code"]) for item in packet["failing"]))
