"""Phase-deep proof, ownership, and topology guards for deterministic E2E."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from workshop.workflow import AgentRun, WORKSHOP_EFFORTS
from workshop.workflow.effort import EFFORT_ROUTE_CAPABILITY_PATH
from workshop.workflow.native_run import NativeRunPaths


TRACE_KIND = "autonomous-workshop.deterministic-e2e-turn"
CANONICAL_ROUTES = {
    "spark": ("make", "release"),
    "forge": ("invent", "make", "release"),
    "quest": ("invent", "make", "playtest", "release"),
}
DECLARED_REPAIR_EDGES = frozenset({("playtest", "make"), ("playtest", "invent")})
DECLARED_WAIT_RESUME = frozenset({"release"})


@dataclass(frozen=True)
class PhaseProof:
    artifact_suffixes: tuple[str, ...]
    host_suffixes: tuple[str, ...] = ()


PHASE_PROOFS: Mapping[str, PhaseProof] = {
    "wish": PhaseProof(("/wish.json",), ("/gates/0000-wish.json",)),
    "invent": PhaseProof(
        ("/assignment.json", "/invented.json", "/source.json"),
        ("/gates/0001-invent.json",),
    ),
    "make": PhaseProof(
        (
            "/assignment.json",
            "/invented.json",
            "/made.json",
            "/product/product.json",
            "/product/assembled.step",
            "/product/assembled.stl",
            "/product/validation/cad-verification.json",
        ),
        (
            "/evidence/make/r0001-cad-gate.json",
            "/gates/0002-make.json",
        ),
    ),
    "playtest": PhaseProof(
        ("/playtested.json",),
        (
            "/evidence/playtest/r0001-cad-gate.json",
            "/gates/0003-playtest.json",
        ),
    ),
    "release": PhaseProof(
        (
            "/release.json",
            "/package/MANUAL.pdf",
            "/package/product.json",
        ),
        (
            "/evidence/release/r0001-cad-gate.json",
            "/gates/0004-release.json",
            "/release-effect.json",
            "/factory-effects.sqlite3",
        ),
    ),
}


def load_trace(workspace: Path) -> tuple[Mapping[str, Any], ...]:
    path = workspace / "authored/runtime-trace.jsonl"
    if path.is_symlink() or not path.is_file():
        raise AssertionError("ownership drift: native trace is missing")
    try:
        values = tuple(json.loads(line) for line in path.read_text().splitlines())
    except (OSError, ValueError) as exc:
        raise AssertionError("ownership drift: native trace is malformed") from exc
    if not values or any(item.get("kind") != TRACE_KIND for item in values):
        raise AssertionError("ownership drift: native trace kind is invalid")
    return values


def assert_topology_coverage(
    *,
    routes: Mapping[str, tuple[str, ...]] = CANONICAL_ROUTES,
    repair_edges: frozenset[tuple[str, str]] = DECLARED_REPAIR_EDGES,
    wait_resume: frozenset[str] = DECLARED_WAIT_RESUME,
) -> None:
    expected_routes = {
        name: tuple(effort.enabled_stages) for name, effort in WORKSHOP_EFFORTS.items()
    }
    gaps = []
    for name, expected in expected_routes.items():
        observed = routes.get(name)
        if observed != expected:
            gaps.append("route:%s:%r" % (name, expected))
    if set(routes) - set(expected_routes):
        gaps.extend("removed-route:%s" % name for name in sorted(set(routes) - set(expected_routes)))
    required_repairs = {("playtest", "make"), ("playtest", "invent")}
    gaps.extend("repair:%s->%s" % edge for edge in sorted(required_repairs - repair_edges))
    if "release" not in wait_resume:
        gaps.append("wait-resume:release")
    if gaps:
        raise AssertionError("topology drift: " + ", ".join(gaps))


def assert_native_ownership(trace: tuple[Mapping[str, Any], ...]) -> None:
    for turn in trace:
        phase = turn.get("stage", "unknown")
        required = {
            "kind",
            "checkpoint_sha256",
            "subject_sha256",
            "stage_packet_sha256",
            "prompt_sha256",
            "source_paths",
            "agent_writes",
            "source_writes",
            "finalizer_writes",
            "workspace_before_sha256",
            "workspace_after_sha256",
            "finalizer",
        }
        missing = sorted(required - set(turn))
        if missing:
            raise AssertionError(
                "ownership drift: %s trace misses %s" % (phase, ", ".join(missing))
            )
        if turn.get("stage_read_only") is not True:
            raise AssertionError("ownership drift: %s observed writable STAGE.json" % phase)
        if turn.get("forbidden_environment"):
            raise AssertionError("ownership drift: %s observed host credentials" % phase)
        if turn.get("forbidden_paths_visible"):
            raise AssertionError("ownership drift: %s observed host-owned paths" % phase)
        finalizer = turn.get("finalizer")
        if not isinstance(finalizer, Mapping) or finalizer.get("returncode") != 0:
            raise AssertionError("proof drift: %s finalizer did not succeed" % phase)
        arguments = finalizer.get("arguments")
        if not isinstance(arguments, list) or not arguments or arguments[0] != phase:
            raise AssertionError("proof drift: %s finalizer invocation is missing" % phase)
        writes = turn.get("agent_writes")
        if not isinstance(writes, list) or not writes:
            raise AssertionError("ownership drift: %s write inventory is missing" % phase)
        for relative in writes:
            allowed = (
                relative == "agent-outcome.json"
                or relative.startswith("authored/")
                or relative.startswith("artifacts/%s/" % phase)
            )
            if not allowed:
                raise AssertionError(
                    "ownership drift: %s native write crossed into %s" % (phase, relative)
                )
        source_writes = turn.get("source_writes")
        finalizer_writes = turn.get("finalizer_writes")
        if (
            not isinstance(source_writes, list)
            or not isinstance(finalizer_writes, list)
            or sorted(source_writes + finalizer_writes) != sorted(writes)
            or any(not path.startswith("authored/") for path in source_writes)
            or any(
                path != "agent-outcome.json" and not path.startswith("artifacts/")
                for path in finalizer_writes
            )
        ):
            raise AssertionError(
                "ownership drift: %s source/finalizer write classes differ" % phase
            )
        for key in ("workspace_before_sha256", "workspace_after_sha256"):
            value = turn.get(key)
            if not isinstance(value, str) or len(value) != 64:
                raise AssertionError(
                    "ownership drift: %s workspace inventory hash is missing" % phase
                )


def _raw_checkpoint(paths: NativeRunPaths) -> Mapping[str, Any]:
    try:
        return json.loads((paths.host_state / "agent-run.json").read_text())
    except (OSError, ValueError) as exc:
        raise AssertionError("proof drift: Wish checkpoint history is missing") from exc


def _assert_file(path: Path, *, phase: str, label: str) -> None:
    if path.is_symlink() or not path.is_file():
        raise AssertionError("proof drift: %s lacks %s" % (phase, label))


def assert_phase_proofs(
    paths: NativeRunPaths,
    *,
    effort: str,
    expected_trace: tuple[str, ...] | None = None,
) -> None:
    """Reread every phase-owned proof and cross-check route-specific absence."""

    raw = _raw_checkpoint(paths)
    wish_path = paths.workspace / "WISH.json"
    _assert_file(wish_path, phase="wish", label="canonical WISH.json")
    input_bindings = {
        item.get("path"): item.get("sha256")
        for item in raw.get("inputs", ())
        if isinstance(item, Mapping)
    }
    wish_sha256 = hashlib.sha256(wish_path.read_bytes()).hexdigest()
    if input_bindings.get("WISH.json") != wish_sha256:
        raise AssertionError("proof drift: Wish bytes differ from the frozen input")
    if raw.get("effort") != effort or EFFORT_ROUTE_CAPABILITY_PATH not in input_bindings:
        raise AssertionError("proof drift: Wish lacks frozen effort capability")
    for required_input in (
        "AGENTS.md",
        ".agents/skills/autonomous-workshop/SKILL.md",
    ):
        if required_input not in input_bindings:
            raise AssertionError("proof drift: Wish lacks materialized instruction %s" % required_input)
    for relative, expected_sha256 in input_bindings.items():
        path = paths.workspace / relative
        if path.is_symlink() or not path.is_file():
            raise AssertionError("proof drift: Wish lacks materialized input %s" % relative)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
            raise AssertionError("proof drift: Wish materialized input changed at %s" % relative)
    marker = paths.workspace / ".workshop-product-run-root"
    _assert_file(marker, phase="wish", label="private product workspace marker")
    history = raw.get("history")
    if not isinstance(history, list) or not history or history[0].get("stage") != "wish":
        raise AssertionError("proof drift: Wish gate does not precede native stages")
    stage_artifacts = raw.get("stage_artifacts", {})
    enabled = set(WORKSHOP_EFFORTS[effort].enabled_stages)
    expected = {"wish", *enabled}
    if set(stage_artifacts) != expected:
        raise AssertionError(
            "topology drift: %s stage artifacts are %r" % (effort, sorted(stage_artifacts))
        )
    sealed = {
        item.get("path"): item
        for item in raw.get("sealed_artifacts", ())
        if isinstance(item, Mapping)
    }
    for phase, relatives in stage_artifacts.items():
        for relative in relatives:
            item = sealed.get(relative)
            if item is None:
                raise AssertionError(
                    "proof drift: %s lacks sealed inventory for %s"
                    % (phase, relative)
                )
            path = paths.workspace / relative
            _assert_file(path, phase=phase, label=relative)
            if hashlib.sha256(path.read_bytes()).hexdigest() != item.get("sha256"):
                raise AssertionError(
                    "proof drift: %s sealed artifact hash changed at %s"
                    % (phase, relative)
                )
    for phase in ("wish", *WORKSHOP_EFFORTS[effort].enabled_stages):
        proof = PHASE_PROOFS[phase]
        artifacts = stage_artifacts.get(phase)
        if not isinstance(artifacts, list) or not artifacts:
            raise AssertionError("proof drift: %s lacks sealed artifacts" % phase)
        for suffix in proof.artifact_suffixes:
            matching = [item for item in artifacts if item.endswith(suffix)]
            if not matching:
                # Assignment/Invented are folded into Spark Make only. Forge/Quest
                # Make bind them through Made rather than duplicating their files.
                if phase == "make" and effort != "spark" and suffix in {
                    "/assignment.json", "/invented.json"
                }:
                    continue
                raise AssertionError("proof drift: %s lacks durable %s" % (phase, suffix))
            for relative in matching:
                _assert_file(paths.workspace / relative, phase=phase, label=suffix)
        for suffix in proof.host_suffixes:
            candidates = [path for path in paths.host_state.rglob("*") if path.is_file()]
            if not any(("/" + path.relative_to(paths.host_state).as_posix()).endswith(suffix) for path in candidates):
                if suffix.startswith("/evidence/%s/" % phase) and any(
                    path.parent.name == phase and path.name.endswith("-cad-gate.json")
                    for path in candidates
                ):
                    continue
                # Gate ordinals vary when optional phases pass through.
                if "/gates/" in suffix:
                    gate_phase = suffix.rsplit("-", 1)[-1].removesuffix(".json")
                    if any(path.name.endswith("-%s.json" % gate_phase) for path in candidates):
                        continue
                raise AssertionError("proof drift: %s lacks host proof %s" % (phase, suffix))

    for phase in {"invent", "playtest"} - enabled:
        if phase in stage_artifacts:
            raise AssertionError("topology drift: %s fabricated passed-through %s" % (effort, phase))
        if (paths.host_state / "evidence" / phase).exists():
            raise AssertionError("proof drift: %s fabricated %s evidence" % (effort, phase))
        if any(path.name.endswith("-%s.json" % phase) for path in (paths.host_state / "gates").glob("*.json")):
            raise AssertionError("proof drift: %s fabricated %s gate" % (effort, phase))
        if (paths.workspace / "artifacts" / phase).exists():
            raise AssertionError("proof drift: %s fabricated %s artifact tree" % (effort, phase))
        if (paths.workspace / "authored" / (phase + ".json")).exists():
            raise AssertionError("ownership drift: %s fabricated %s source" % (effort, phase))

    trace = load_trace(paths.workspace)
    expected_turns = expected_trace or WORKSHOP_EFFORTS[effort].enabled_stages
    if tuple(item["stage"] for item in trace) != expected_turns:
        raise AssertionError("topology drift: %s native turns do not match its route" % effort)
    assert_native_ownership(trace)

    if raw.get("stage") != "release" or raw.get("status") != "complete":
        raise AssertionError("proof drift: Release lacks terminal checkpoint")
    checkpoint = AgentRun.open(paths.workspace, host_state_root=paths.host_state).snapshot()
    if checkpoint.stage != "release" or checkpoint.status != "complete":
        raise AssertionError("proof drift: Release lacks terminal checkpoint")
    if checkpoint.wish_sha256 != wish_sha256:
        raise AssertionError("proof drift: Wish reported hash differs from its bytes")
    for phase, artifacts in checkpoint.stage_artifacts.items():
        for artifact in artifacts:
            path = paths.workspace / artifact.path
            _assert_file(path, phase=phase, label=artifact.path)
            content = path.read_bytes()
            if hashlib.sha256(content).hexdigest() != artifact.sha256:
                raise AssertionError(
                    "proof drift: %s sealed artifact hash changed at %s"
                    % (phase, artifact.path)
                )


__all__ = [
    "CANONICAL_ROUTES",
    "DECLARED_REPAIR_EDGES",
    "DECLARED_WAIT_RESUME",
    "PHASE_PROOFS",
    "assert_native_ownership",
    "assert_phase_proofs",
    "assert_topology_coverage",
    "load_trace",
]
