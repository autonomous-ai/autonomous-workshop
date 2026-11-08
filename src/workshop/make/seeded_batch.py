"""A seeded Make's checks as one deterministic host batch (ADR 0098).

A run seeded from an Approved Proof (ADR 0096) only certifies and packages a
shape the owner approved. This module runs every re-verification that
certification needs, in a fixed order of dependency layers, and records each
step's exact command, exit, duration and report hashes in
``measure/seeded-batch.json``. It is gate execution only: it never edits a
source, never retries a check with other options, never decides that a
failure is acceptable, and holds no prompt, reasoning or repair.

Exit classification, the rule the host dispatches on:

- exit 0 is a pass;
- exit 1 with no Python traceback is a check failure: the check ran and
  reported a defect in its own words, which a native repair turn can act on;
- anything else is a harness failure, never a model task: a signal, another
  exit code, a timeout, a traceback, or a tool that cannot start.

Within a layer every step runs even when one fails, so one report carries
every independent failure (owner decision 4). A layer after a failed one is
skipped and named as skipped. A step whose command and input bytes are those
of a recorded pass is reused rather than rerun; a failure is never reused.

Two plans share the engine. ``run_plan`` is what the host runs inside a
seeded run, as the run user, with the run's materialized tools.
``design_plan`` is what ``seal_proof.py seal`` runs on the Proof before the
owner's approval is sealed (owner decision 5): the layers that need no run
state, so a defect is found at design cost.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence

LAYERS = (
    "seed",
    "project",
    "shared-helpers",
    "components",
    "interfaces",
    "power",
    "motion",
    "assembly",
    "final",
    "product",
    "parts",
    "finalize",
)
RECORD = "measure/seeded-batch.json"
RECORD_KIND = "workshop-seeded-batch"
SCHEMA_VERSION = 1
PASS = "pass"
REUSED = "reused"
CHECK_FAILURE = "check-failure"
HARNESS_FAILURE = "harness-failure"
SKIPPED = "skipped"
TRACEBACK = "Traceback (most recent call last)"
EXCERPT_BYTES = 2000
PACKET_EXCERPT_BYTES = 1200
MAX_PACKET_FAILURES = 32
# Each check keeps its own deadline, so one sweep cannot spend another's
# (attempt 2 of the Sunset Slider lost every print gate to a motion sweep).
DEFAULT_DEADLINES = {
    "seed": 300.0,
    "project": 300.0,
    "shared-helpers": 900.0,
    "components": 900.0,
    "interfaces": 900.0,
    "power": 900.0,
    "motion": 1800.0,
    # The assembly round runs check_motion and the print gates on the whole
    # build (issue #244): the motion step's allowance plus the print gates.
    "assembly": 3600.0,
    "final": 3600.0,
    "product": 300.0,
    "parts": 600.0,
    "finalize": 900.0,
}
# What a repair turn may still do; carried in the failure packet so the turn
# need not read the whole Make card to learn them.
REPAIR_RULES = (
    "Repair only what a failing step reports; never rerun a passing step listed here.",
    "A change to an approved Component is a seed deviation: within proof_diff tolerance it relocks on "
    "the approval, over tolerance it needs one Component Worker and one Component Review.",
    "Unlock a locked Component a check fails with --record-unlock and the check's own words as the "
    "verification quote.",
    "A Contract Contradiction is a need, as in any run.",
    "When the repair is done, propose Make with the finalizer; the host reruns this batch as the gate.",
)


@dataclass(frozen=True)
class Step:
    """One deterministic check: its exact command and what its result binds."""

    id: str
    layer: str
    argv: tuple
    inputs: tuple = ()
    reports: tuple = ()
    deadline_s: Optional[float] = None
    # A component round in a run takes a fresh seed nonce, issued by the host
    # when the step runs; it is never part of the step's reuse key.
    nonce_component: Optional[str] = None
    # Final verification exits 0 with geometry checks it could not finish
    # recorded UNVERIFIED; this report's Result line is the step's verdict.
    verdict_report: Optional[str] = None
    # An assembly round records an analysis it could not finish as
    # geometry_status "unverified" in its summary (issue #244).
    round_summary: bool = False

    def __post_init__(self) -> None:
        if self.layer not in LAYERS:
            raise ValueError("unknown seeded batch layer %r" % self.layer)
        if not self.id or not self.argv or not all(isinstance(item, str) for item in self.argv):
            raise ValueError("a seeded batch step needs an id and a string argv")


@dataclass(frozen=True)
class RunResult:
    returncode: Optional[int]
    output: str
    timed_out: bool = False
    duration_s: float = 0.0
    start_error: Optional[str] = None


Runner = Callable[[Sequence[str], Path, Optional[float]], RunResult]
NonceIssuer = Callable[[str], str]


def environment_runner(environment: Optional[Mapping[str, str]]) -> Runner:
    """A runner whose steps see exactly ``environment`` (the host passes a
    credential-free one; None inherits, for design on the owner's machine)."""

    def run(argv: Sequence[str], cwd: Path, timeout: Optional[float]) -> RunResult:
        return _run_process(argv, cwd, timeout, environment)

    return run


def subprocess_runner(argv: Sequence[str], cwd: Path, timeout: Optional[float]) -> RunResult:
    """Run one step with the caller's environment."""

    return _run_process(argv, cwd, timeout, None)


def _run_process(argv: Sequence[str], cwd: Path, timeout: Optional[float],
                 environment: Optional[Mapping[str, str]]) -> RunResult:
    """Run one step in its own process group; a timeout kills the group."""

    started = time.monotonic()
    try:
        process = subprocess.Popen(list(argv), cwd=str(cwd), stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, start_new_session=True,
                                   env=None if environment is None else dict(environment))
    except OSError as exc:
        return RunResult(None, "", start_error="%s: %s" % (type(exc).__name__, exc),
                         duration_s=time.monotonic() - started)
    try:
        output, _ = process.communicate(timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            process.kill()
        output, _ = process.communicate()
        timed_out = True
    return RunResult(process.returncode, (output or b"").decode("utf-8", "replace"), timed_out=timed_out,
                     duration_s=time.monotonic() - started)


def classify(result: RunResult) -> tuple:
    """``(status, reason)`` for one finished step."""

    if result.start_error is not None:
        return HARNESS_FAILURE, "the tool could not start: %s" % result.start_error
    if result.timed_out:
        return HARNESS_FAILURE, "timed out"
    code = result.returncode
    if code == 0:
        return PASS, None
    if code is not None and code < 0:
        try:
            name = signal.Signals(-code).name
        except ValueError:
            name = "signal %d" % -code
        return HARNESS_FAILURE, "killed by %s" % name
    if code == 1:
        if TRACEBACK in result.output:
            return HARNESS_FAILURE, "the tool raised an uncaught exception"
        return CHECK_FAILURE, None
    return HARNESS_FAILURE, "exit %s" % code


def _sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _tree_hashes(project: Path, name: str) -> dict:
    """``name`` (relative to the project, or absolute) -> sha256 for a file,
    every file under it for a directory, or None when absent."""

    path = project / name
    if path.is_file():
        return {name: _sha256_bytes(path.read_bytes())}
    if path.is_dir():
        return {"%s/%s" % (name, item.relative_to(path).as_posix()): _sha256_bytes(item.read_bytes())
                for item in sorted(path.rglob("*")) if item.is_file()}
    return {name: None}


def step_key(step: Step, project: Path) -> str:
    """The reuse key: the command, the bytes of the tool it runs and of every
    declared input. Equal keys run the same check on the same bytes."""

    tools = {}
    for item in step.argv[:2]:
        candidate = Path(item)
        if candidate.is_absolute() and candidate.is_file():
            tools[item] = _sha256_bytes(candidate.read_bytes())
    inputs: dict = {}
    for relative in step.inputs:
        inputs.update(_tree_hashes(project, relative))
    return _sha256_bytes(_canonical({"argv": list(step.argv), "tools": tools, "inputs": inputs}))


def _excerpt(output: str, limit: int = EXCERPT_BYTES) -> str:
    """The end of a step's own words, where checks print their verdict."""

    encoded = output.encode("utf-8")
    if len(encoded) <= limit:
        return output
    return "..." + encoded[-limit:].decode("utf-8", "ignore")


def _previous_passes(previous: Optional[Mapping[str, Any]]) -> dict:
    if not isinstance(previous, Mapping) or previous.get("kind") != RECORD_KIND:
        return {}
    return {item["id"]: item["key"] for item in previous.get("steps") or ()
            if isinstance(item, Mapping) and item.get("status") in (PASS, REUSED)
            and isinstance(item.get("id"), str) and isinstance(item.get("key"), str)}


def run_batch(
    steps: Iterable[Step],
    project: Path,
    *,
    runner: Runner = subprocess_runner,
    previous: Optional[Mapping[str, Any]] = None,
    issue_nonce: Optional[NonceIssuer] = None,
    record_path: Optional[Path] = None,
    plan_name: str = "run",
    layers: Sequence[str] = LAYERS,
) -> dict:
    """Run ``steps`` layer by layer and return (and write) the record."""

    project = Path(project)
    steps = list(steps)
    ids = [step.id for step in steps]
    if len(ids) != len(set(ids)):
        raise ValueError("seeded batch step ids must be unique")
    # Every step runs with the project as its cwd, and on a fresh run the
    # first step (prepare) is the one that fills it: the directory must
    # exist before any step can start.
    project.mkdir(parents=True, exist_ok=True)
    reusable = _previous_passes(previous)
    recorded = []
    failed_layer = None
    for layer in LAYERS:
        if layer not in layers:
            continue
        for step in (item for item in steps if item.layer == layer):
            key = step_key(step, project)
            entry = {"id": step.id, "layer": layer, "argv": list(step.argv), "key": key}
            if failed_layer is not None:
                entry.update(status=SKIPPED, reason="layer %s failed" % failed_layer)
                recorded.append(entry)
                continue
            if reusable.get(step.id) == key:
                entry.update(status=REUSED, reports=_report_hashes(project, step.reports))
                recorded.append(entry)
                continue
            argv = list(step.argv)
            if step.nonce_component is not None:
                if issue_nonce is None:
                    raise ValueError("step %s needs a seed nonce and no issuer was given" % step.id)
                argv += ["--seed-nonce", issue_nonce(step.nonce_component)]
            deadline = step.deadline_s if step.deadline_s is not None else DEFAULT_DEADLINES[layer]
            started = time.time()
            result = runner(argv, project, deadline)
            status, reason = classify(result)
            if status == PASS and step.verdict_report is not None:
                verdict = report_verdict(project, step.verdict_report)
                if verdict != "PASS":
                    # Never a pass: a gate the tool could not finish is not
                    # a gate that passed (issue #241). It is no defect a
                    # model could repair, so it is the harness's.
                    status, reason = HARNESS_FAILURE, (
                        "exit 0 but %s records %s: a geometry check was not finished in its time allowance"
                        % (step.verdict_report, verdict) if verdict == "UNVERIFIED"
                        else "exit 0 but %s records %s" % (step.verdict_report, verdict or "no Result line"))
            if step.round_summary and status in (PASS, CHECK_FAILURE):
                unverified = round_unverified(project, since=started)
                if unverified is not None:
                    # A timeout is never a pass, and no model repair finishes
                    # an analysis that ran out of time: the harness's.
                    status, reason = HARNESS_FAILURE, unverified
            entry.update(status=status, exit_code=result.returncode, duration_s=round(result.duration_s, 3),
                         reports=_report_hashes(project, step.reports), excerpt=_excerpt(result.output))
            if reason is not None:
                entry["reason"] = reason
            recorded.append(entry)
        if failed_layer is None and any(item["layer"] == layer and item["status"] in (CHECK_FAILURE, HARNESS_FAILURE)
                                        for item in recorded):
            failed_layer = layer
    statuses = {item["status"] for item in recorded}
    overall = HARNESS_FAILURE if HARNESS_FAILURE in statuses else CHECK_FAILURE if CHECK_FAILURE in statuses else PASS
    record = {"schema_version": SCHEMA_VERSION, "kind": RECORD_KIND, "plan": plan_name, "status": overall,
              "failed_layer": failed_layer, "steps": recorded}
    if record_path is not None:
        write_record(record_path, record)
    return record


def _report_hashes(project: Path, reports: Iterable[str]) -> dict:
    hashes: dict = {}
    for relative in reports:
        hashes.update(_tree_hashes(project, relative))
    return hashes


def write_record(path: Path, record: Mapping[str, Any]) -> str:
    """Write the record atomically; return its sha256."""

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(record, sort_keys=True, indent=1).encode("utf-8") + b"\n"
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(content)
    os.replace(temporary, path)
    return _sha256_bytes(content)


def failure_packet(record: Mapping[str, Any], record_sha256: str, *, record_path: str = RECORD) -> dict:
    """What ``STAGE.json`` carries as ``seeded_batch_failure`` for a native
    repair turn: every failing step in its own words, bounded; the steps that
    passed, by key, which the turn must not rerun; and the rules that hold."""

    if record.get("status") != CHECK_FAILURE:
        raise ValueError("only a check failure goes to a native repair turn")
    failing = [
        {"id": item["id"], "layer": item["layer"], "argv": item["argv"], "exit_code": item.get("exit_code"),
         "reports": item.get("reports") or {}, "excerpt": _excerpt(item.get("excerpt") or "", PACKET_EXCERPT_BYTES)}
        for item in record["steps"] if item["status"] == CHECK_FAILURE
    ][:MAX_PACKET_FAILURES]
    return {
        "schema_version": 1,
        "record": record_path,
        "record_sha256": record_sha256,
        "failed_layer": record.get("failed_layer"),
        "failing": failing,
        "passed": [{"id": item["id"], "key": item["key"]} for item in record["steps"]
                   if item["status"] in (PASS, REUSED)],
        "skipped": [item["id"] for item in record["steps"] if item["status"] == SKIPPED],
        "rules": list(REPAIR_RULES),
    }


def harness_failures(record: Mapping[str, Any]) -> list:
    """The harness failures of a record, for the operator's need."""

    return [{"id": item["id"], "argv": item["argv"], "exit_code": item.get("exit_code"),
             "reason": item.get("reason"), "excerpt": _excerpt(item.get("excerpt") or "", PACKET_EXCERPT_BYTES)}
            for item in record.get("steps") or () if item.get("status") == HARNESS_FAILURE]


@dataclass(frozen=True)
class PlanInputs:
    """Everything a plan needs; every path is absolute."""

    project: Path
    python: str
    skills_root: Path
    contract_path: Path
    roles: tuple
    nozzle: float
    coupled_interfaces: tuple = ()
    powered: bool = False
    moving: bool = False
    image_derived: bool = True
    concept_sha256: Optional[str] = None
    finalizer: tuple = ()
    deadlines: Mapping[str, float] = field(default_factory=dict)


def _tool(inputs: PlanInputs, *parts: str) -> str:
    return str(inputs.skills_root.joinpath(*parts))


def _source_inputs(roles: Iterable[str]) -> tuple:
    return ("params.py", "features", "colours.py", *("part_%s.step.py" % role for role in roles))


def _common_layers(inputs: PlanInputs, *, design: bool) -> list:
    py, project = inputs.python, str(inputs.project)
    make_round = _tool(inputs, "make-round", "scripts", "make_round")
    cad = ("cad", "scripts")
    steps = [
        Step("project", "project", (py, _tool(inputs, *cad, "verify_project"), project, "--dry-run"),
             inputs=_source_inputs(inputs.roles)),
        # Outside a run make_round reads the Interfaces from --contract; inside
        # one, from the sealed contract.
        Step("shared-helpers", "shared-helpers",
             (py, make_round, project, "--shared-helpers",
              *(("--contract", str(inputs.contract_path)) if design else ())),
             inputs=("params.py", "features", "samples"), reports=("measure/shared-helpers-freeze.json",)),
    ]
    if inputs.powered:
        steps += [
            # Outside a run the circuit and catalogue a run would seal come
            # from the contract file (ADR 0098); in a run, from WISH.json.
            Step("bought-model", "power", (py, _tool(inputs, "make-round", "scripts", "bought_model.py"), project,
                                           "--build", *(("--contract", str(inputs.contract_path)) if design else ())),
                 inputs=("measure/power.json", "measure/bought-placements.json"),
                 reports=("measure/bought-bodies.json",)),
            Step("check-power", "power", (py, _tool(inputs, "electromechanical-integration", "scripts", "check_power"),
                                          project), inputs=("measure/power.json",)),
            Step("check-mount", "power", (py, _tool(inputs, *cad, "check_mount"), project),
                 inputs=("measure/mounts.json", "ref", *_source_inputs(inputs.roles))),
        ]
    if inputs.moving:
        steps.append(Step("check-motion", "motion", (py, _tool(inputs, *cad, "check_motion"), project, "--manifest",
                                                     "measure/motion.json", "--json"),
                          inputs=("measure/motion.json", *_source_inputs(inputs.roles))))
    return steps


def run_plan(inputs: PlanInputs, *, run_root: Path, product_root: Path, source: Path) -> list:
    """The batch a seeded run's host runs (ADR 0098 decision 2). The CAD
    project is ``inputs.project``, inside ``product_root``."""

    if not inputs.finalizer:
        raise ValueError("a run plan packages with the Make finalizer")
    if not inputs.concept_sha256:
        raise ValueError("a run plan carries the reviews against the concept hash")
    py, project = inputs.python, str(inputs.project)
    make_round = _tool(inputs, "make-round", "scripts", "make_round")
    package = (py, "-m", "workshop.make.seeded_package")
    steps = [Step("prepare", "seed", (*package, "prepare", str(run_root), "--project", project),
                  inputs=(str(run_root / "seed"),))]
    steps += _common_layers(inputs, design=False)
    for role in inputs.roles:
        steps.append(Step("component:%s" % role, "components",
                          (py, make_round, project, "--component", "part_%s.step.py" % role,
                           "--nozzle", "%g" % inputs.nozzle, "--json"),
                          inputs=("params.py", "features", "part_%s.step.py" % role),
                          reports=("measure/rounds/%s" % role,), nonce_component=role))
    for interface in inputs.coupled_interfaces:
        steps.append(Step("interface:%s" % interface, "interfaces",
                          (py, make_round, project, "--interface", interface),
                          inputs=_source_inputs(inputs.roles), reports=("measure/interface-rounds/%s" % interface,)))
    # The round's check_motion and print gates share one geometry allowance;
    # give them the layer's deadline less time to build and report, never
    # less than the batch's own motion step (issue #244).
    assembly = inputs.deadlines.get("assembly", DEFAULT_DEADLINES["assembly"])
    geometry = max(60.0, assembly - FINAL_REPORT_MARGIN_S)
    steps += [
        # A seeded round carries the approval's assembly review (ADR 0096),
        # so it needs no Manager look.
        Step("assembly-round", "assembly", (py, make_round, project, "--require-component-passes",
                                            "--nozzle", "%g" % inputs.nozzle, "--geometry-seconds", "%g" % geometry,
                                            "--json"),
             inputs=_source_inputs(inputs.roles), round_summary=True),
        Step("carry-assembly-review", "assembly", (py, make_round, project, "--carry-assembly-review",
                                                   "--concept-sha256", inputs.concept_sha256),
             reports=("snap/SIGNATURE-REVIEW.json",)),
        _final_step(inputs, "measure/verification-pipeline.md", design=False),
        # Final verification rewrites its report whenever it reruns, with the
        # combined STEP and its package, so a repaired build is repackaged.
        Step("product", "product", (*package, "product", str(run_root), "--project", project,
                                    "--product-root", str(product_root), "--source", str(source)),
             inputs=("measure/verification-pipeline.md", "measure/electrical/assembly.md", str(run_root / "seed"),
                     str(Path(__file__).with_name("seeded_package.py")))),
        # The production solid of every printed occurrence, from the
        # Component STEPs the print gates passed, so a multi-part build's
        # finalizer needs no model turn.
        Step("parts", "parts", (*package, "parts", "--project", project, "--product-root", str(product_root)),
             # Final verification rewrites the combined STEP and its package
             # whenever a Component STEP changes, so these bind the parts.
             inputs=(str(product_root / "assembled.step"), str(product_root / "assembled.step.json"),
                     str(Path(__file__).with_name("seeded_package.py"))),
             reports=(str(product_root / "parts"),)),
        Step("finalizer", "finalize", tuple(inputs.finalizer)),
    ]
    return _with_deadlines(steps, inputs.deadlines)


DESIGN_REPORT = "measure/design-verification.md"


def _final_step(inputs: PlanInputs, report: str, *, design: bool) -> Step:
    """Final verification, the same gates in the run and on the Proof. In
    the run it binds the carried signature review; on the Proof
    (``--design``, refused inside a run) that review does not exist yet."""

    flags = ["--powered"] if inputs.powered else ["--unpowered"] if inputs.image_derived else []
    reviews = () if design else ("snap/SIGNATURE-REVIEW.json", "snap/MOTION-REVIEW.json")
    # verify_project shares one allowance across every geometry analysis and
    # records what it could not finish UNVERIFIED (issue #241): the batch
    # gives them the layer's deadline, less time to build and report.
    deadline = inputs.deadlines.get("final", DEFAULT_DEADLINES["final"])
    geometry = max(60.0, deadline - FINAL_REPORT_MARGIN_S)
    return Step("final-verification", "final",
                (inputs.python, _tool(inputs, "cad", "scripts", "verify_project"), str(inputs.project),
                 *(("--design", "--contract", str(inputs.contract_path)) if design else ()),
                 "--geometry-seconds", "%g" % geometry, "--strict-fit", "--print-gates",
                 "--nozzle", "%g" % inputs.nozzle, "--report", str(inputs.project / report),
                 "--check-motion", "true" if inputs.moving else "false",
                 *(("--image-derived",) if inputs.image_derived else ()), *flags),
                inputs=(*_source_inputs(inputs.roles), *reviews, "measure/motion.json", "measure/power.json",
                        "measure/mounts.json"),
                reports=(report,), verdict_report=report)


FINAL_REPORT_MARGIN_S = 300.0
_RESULT_LINE = re.compile(r"^- Result: \*\*(PASS|FAIL|UNVERIFIED)\b", re.MULTILINE)


def report_verdict(project: Path, report: str) -> Optional[str]:
    """``PASS``, ``FAIL`` or ``UNVERIFIED`` from a verification record, or
    None when it is missing or holds no Result line."""

    try:
        match = _RESULT_LINE.search((Path(project) / report).read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None
    return match.group(1) if match else None


def round_unverified(project: Path, *, since: Optional[float] = None) -> Optional[str]:
    """Why the assembly round's last summary is unverified, or None. The
    round's state names its output folder; its summary records an analysis
    left unfinished as ``geometry_status`` or ``motion_status`` unverified.
    A summary written before ``since`` is an earlier round's and is ignored."""

    try:
        state = json.loads((Path(project) / "measure/make-round-state.json").read_text(encoding="utf-8"))
        path = Path(state["last_out"]) / "summary.json"
        if since is not None and path.stat().st_mtime < since - 1.0:
            return None
        summary = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        return None
    if not isinstance(summary, Mapping):
        return None
    if summary.get("motion_status") == "unverified":
        return "the assembly round's check_motion did not finish in its time allowance (motion unverified)"
    if summary.get("geometry_status") == "unverified":
        return "the assembly round left a geometry check unfinished in its time allowance (geometry unverified)"
    return None


def coupled_interface_ids(contract: Mapping[str, Any]) -> tuple:
    """The contract's Coupled Interfaces, in contract order."""

    return tuple(item["id"] for item in contract.get("interfaces") or ()
                 if isinstance(item, Mapping) and item.get("kind") == "coupled")


def design_plan(inputs: PlanInputs) -> list:
    """The batch ``seal_proof.py seal`` runs on the Proof (owner decision 5):
    the run's whole batch, each check with the same tool, as far as it needs
    no run state. Component rounds become their print gates (a round's
    review and seed nonce are the run's); each Coupled Interface is checked
    on the Proof's Components as they stand (nothing is locked yet);
    final verification runs every gate with ``--design`` (the signature
    review it binds in the run is carried there); and the packaging check
    resolves every production part the run will export. The assembly round,
    the carried reviews, product, parts and the finalizer need the run."""

    py, project = inputs.python, str(inputs.project)
    make_round = _tool(inputs, "make-round", "scripts", "make_round")
    contract = str(inputs.contract_path)
    steps = _common_layers(inputs, design=True)
    steps.append(Step("print-gates", "components",
                      (py, make_round, project, "--print-gates-only", "--nozzle", "%g" % inputs.nozzle,
                       "--overhang-angle", "45", "--contract", contract),
                      inputs=_source_inputs(inputs.roles), reports=("measure/print-gates/summary.json",)))
    for interface in inputs.coupled_interfaces:
        steps.append(Step("interface:%s" % interface, "interfaces",
                          (py, make_round, project, "--interface", interface, "--contract", contract),
                          inputs=_source_inputs(inputs.roles),
                          reports=("measure/interface-rounds/%s/design" % interface,)))
    steps.append(_final_step(inputs, DESIGN_REPORT, design=True))
    steps.append(Step("package-check", "product",
                      (py, "-m", "workshop.make.seeded_package", "check", "--project", project),
                      inputs=(DESIGN_REPORT, str(Path(__file__).with_name("seeded_package.py")))))
    return _with_deadlines(steps, inputs.deadlines)


def _with_deadlines(steps: list, deadlines: Mapping[str, float]) -> list:
    """The plan in layer order (stable within a layer), each step with its
    layer's deadline override."""

    ordered = sorted(steps, key=lambda step: LAYERS.index(step.layer))
    return [replace(step, deadline_s=deadlines.get(step.layer, step.deadline_s)) for step in ordered]


def module_sha256() -> str:
    """The bytes a run freezes as its batch tool (MAKE-OPTIONS seed.batch)."""

    return _sha256_bytes(Path(__file__).read_bytes())


def compose_spark_source(seed_product: Mapping[str, Any], assignment: Mapping[str, Any]) -> dict:
    """The run's ``spark-source.json``: the host assignment's inventor and
    ranking, verbatim, and the concept and research the Proof sealed. Nothing
    here is authored: the concept hash the design's motion review names is
    the hash of these exact concept fields."""

    return {"selected_inventor_id": assignment["selected_inventor_id"], "ranking": assignment["ranking"],
            "concept": seed_product["concept"], "research": seed_product["research"]}


def concept_sha256(concept: Mapping[str, Any]) -> str:
    """The canonical Invented concept hash, as the finalizer computes it."""

    return _sha256_bytes(json.dumps(concept, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                                    allow_nan=False).encode("utf-8"))


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run a seeded Make's checks as one batch (ADR 0098).")
    parser.add_argument("project", type=Path)
    parser.add_argument("--contract", type=Path, required=True, help="the sealed Design Contract JSON or Markdown")
    parser.add_argument("--contract-json", type=Path, required=True, help="the parsed contract dict, as JSON")
    parser.add_argument("--skills-root", type=Path, required=True)
    parser.add_argument("--nozzle", type=float, required=True)
    parser.add_argument("--dry-run", action="store_true", help="the design plan: no run state is read or written")
    parser.add_argument("--record", type=Path, help="default: PROJECT/%s" % RECORD)
    args = parser.parse_args(argv)
    from workshop.wish.seed import contract_geometry_ids, contract_is_moving, contract_is_powered

    if not args.dry_run:
        parser.error("only --dry-run runs from the command line; the host runs the run plan itself")
    contract = json.loads(args.contract_json.read_text(encoding="utf-8"))
    project = args.project.resolve()
    inputs = PlanInputs(project=project, python=sys.executable, skills_root=args.skills_root.resolve(),
                        contract_path=args.contract.resolve(), roles=contract_geometry_ids(contract),
                        nozzle=args.nozzle, coupled_interfaces=coupled_interface_ids(contract),
                        powered=contract_is_powered(contract), moving=contract_is_moving(contract),
                        image_derived=bool(contract.get("references")))
    record = run_batch(design_plan(inputs), project, record_path=args.record or project / RECORD, plan_name="design")
    for item in record["steps"]:
        print("seeded_batch: %-14s %-24s %s%s" % (item["layer"], item["id"], item["status"],
                                                 " (%s)" % item["reason"] if item.get("reason") else ""))
    return {PASS: 0, CHECK_FAILURE: 1}.get(record["status"], 2)


if __name__ == "__main__":
    sys.exit(main())
