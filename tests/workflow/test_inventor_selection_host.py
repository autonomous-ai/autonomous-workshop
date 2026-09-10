"""Exercise the real host selection order with an in-process native fake.

These tests intentionally stop when Make is invoked. Full product finalizers
and publication are covered by the full-run suite, not simulated as passes here.
"""

import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest

from tests.invent.fake_gamevault import E2E_NODES, FakeGameVaultTransport, fake_client
from tests.end_to_end.test_native_full_run import _OneSessionProductAgent
from tests.workflow.test_native_host import _FakeLauncher, _FakeOutcome
from workshop.runtime import CodexRecoverableInvocationError
from workshop.match.native import InventorRoster, MatchRankingEntry
from workshop.wish import Wish
from workshop.workflow.agent_run import AgentArtifact, AgentOutcome, AgentRun
from workshop.workflow.inventor_selection import (
    INVENTOR_SELECTION_MARKER_NAME,
    INVENTOR_SELECTION_RECEIPT_NAME,
)
from workshop.workflow.native_run import (
    _MakeProposalRejected,
    _evaluate_make_stage,
    _prepare_stage_input,
    _workshop_inventor_selection,
    native_run_paths,
    resume_native_run,
    start_native_run,
)
from workshop.workflow.proposals import AgentOutcomeProposal


SESSION_BYTES = b'{"session_id":"selection-host-test-one-root"}\n'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


class SelectionRuntime:
    def __init__(self, actions=()):
        self.actions = list(actions)
        self.starts = []
        self.resumes = []
        self.pending = []
        self.make = []
        self.markers = []
        self.premature_bytes = []

    def start(self, **arguments):
        assert not self.starts and not self.resumes
        self.starts.append(arguments)
        session_path = Path(arguments["host_state_root"]) / "codex-session.json"
        session_path.write_bytes(SESSION_BYTES)
        session_path.chmod(0o600)
        return self.turn(arguments)

    def resume(self, **arguments):
        assert len(self.starts) == 1
        assert (Path(arguments["host_state_root"]) / "codex-session.json").read_bytes() == SESSION_BYTES
        self.resumes.append(arguments)
        return self.turn(arguments)

    def turn(self, arguments):
        root = Path(arguments["run_root"])
        state = Path(arguments["host_state_root"])
        packet = json.loads((root / "STAGE.json").read_text())
        assert packet["stage"] == "make"
        selection = packet["inputs"]["workshop_selection"]
        if selection["status"] == "pending":
            assert not self.make
            assert not (state / INVENTOR_SELECTION_RECEIPT_NAME).exists()
            assert arguments["finalization_marker"] == root / INVENTOR_SELECTION_MARKER_NAME
            # No Make artifact has been sealed or authored by a previous turn.
            run = AgentRun.open(root, host_state_root=state)
            assert not run.snapshot().stage_artifacts.get("make")
            assert not (root / packet["inputs"]["product_root"]).exists()
            self.pending.append(packet)
            action = self.actions.pop(0) if self.actions else "select"
            if action.startswith("premature"):
                _FakeLauncher._write_waiting(arguments)
                if action == "premature-ready":
                    value = json.loads((root / "agent-outcome.json").read_text())
                    value["outcome"].update(status="ready", needs=[], proposed_transition="release")
                    write_json(root / "agent-outcome.json", value)
                elif action == "premature-garbage":
                    (root / "agent-outcome.json").write_bytes(b"unfinished proposal JSON {")
                self.premature_bytes.append((root / "agent-outcome.json").read_bytes())
                (root / "early-work.txt").write_text("Keep this existing work.")
                if action == "premature-interrupt":
                    raise KeyboardInterrupt("fixture interruption after premature proposal")
                return _FakeOutcome(arguments)
            if action in ("interrupt", "transport", "unfinished"):
                write_json(root / "selection-notes.json", {"candidate": "preserved", "turn": len(self.pending)})
                if action == "interrupt":
                    raise KeyboardInterrupt("fixture selection interruption")
                if action == "transport":
                    raise CodexRecoverableInvocationError("fixture provider transport interruption")
                return _FakeOutcome(arguments)
            ids = [row["inventor_id"] for row in packet["inputs"]["inventor_roster"]["inventors"]]
            ids.reverse()
            marker = {
                "schema_version": 1,
                "kind": "autonomous-workshop.inventor-selection-ready",
                "product_id": packet["product_id"],
                "checkpoint_sha256": packet["checkpoint_sha256"],
                "wish_sha256": selection["wish_sha256"],
                "inventor_roster_sha256": selection["inventor_roster_sha256"],
                "selected_inventor_id": ids[0],
                "ranking": [{"inventor_id": name, "rationale": "Native fixture choice."} for name in ids],
            }
            if action == "malformed":
                marker["ranking"].pop()
            self.markers.append(marker)
            write_json(root / selection["marker_path"], marker)
            return _FakeOutcome(arguments)

        assert selection["status"] == "selected"
        assert arguments["finalization_marker"] == root / "agent-outcome.json"
        receipt = json.loads((state / INVENTOR_SELECTION_RECEIPT_NAME).read_text())
        assert selection["assignment"] == receipt["assignment"]
        self.make.append(packet)
        _FakeLauncher._write_waiting(arguments)
        return _FakeOutcome(arguments)


@pytest.fixture
def host(tmp_path, monkeypatch):
    import workshop.workflow.native_run as native

    monkeypatch.setenv("WORKSHOP_HOME", str(tmp_path / "home"))
    monkeypatch.setattr(native, "_source_checkout_root", lambda: None)
    client = fake_client(FakeGameVaultTransport(E2E_NODES))
    monkeypatch.setattr(native, "_gamevault_client", lambda: client)
    monkeypatch.setattr(native.time, "sleep", lambda seconds: None)
    def unexpected(*args, **kwargs):
        raise AssertionError("selection bootstrap must not invoke product verification or effects")
    monkeypatch.setattr(native, "verify_native_made_cad", unexpected)
    monkeypatch.setattr(native, "_factory_credentials", unexpected)

    def run(runtime, *, inventor=None):
        monkeypatch.setattr(native, "CodexNativeSessionLauncher", lambda **kwargs: runtime)
        wish = Wish.create(
            "selection-host-fixture", "Make a simple mechanical desk toy.",
            context={} if inventor is None else {"inventor_id": inventor},
        )
        return wish

    return run


def open_run(wish):
    paths = native_run_paths(wish.product_id)
    return paths, AgentRun.open(paths.workspace, host_state_root=paths.host_state)


def test_explicit_pin_skips_native_bootstrap_and_survives_resume(host):
    runtime = SelectionRuntime()
    wish = host(runtime, inventor="alice")
    first = start_native_run(wish, effort="spark")
    assert first["status"] == "waiting"
    assert len(runtime.starts) == 1 and not runtime.pending and not runtime.resumes
    assert runtime.make[0]["inputs"]["workshop_selection"]["assignment"]["selected_inventor_id"] == "alice"
    paths, run = open_run(wish)
    before = (paths.host_state / INVENTOR_SELECTION_RECEIPT_NAME).read_bytes()
    assert json.loads(before)["selection_origin"] == "user-override"
    assert not run.snapshot().stage_artifacts.get("make")
    resume_native_run(wish.product_id)
    assert not runtime.pending and len(runtime.starts) == 1 and len(runtime.resumes) == 1
    assert (paths.host_state / INVENTOR_SELECTION_RECEIPT_NAME).read_bytes() == before


@pytest.mark.parametrize("action", ["interrupt", "transport", "unfinished"])
def test_interrupted_selection_reuses_one_session_and_saved_work(host, action):
    runtime = SelectionRuntime([action, "select"])
    wish = host(runtime)
    if action == "interrupt":
        with pytest.raises(KeyboardInterrupt):
            start_native_run(wish, effort="spark")
        paths, run = open_run(wish)
        assert not runtime.make and not run.snapshot().stage_artifacts.get("make")
        assert not (paths.host_state / INVENTOR_SELECTION_RECEIPT_NAME).exists()
        result = resume_native_run(wish.product_id)
    else:
        result = start_native_run(wish, effort="spark")
    paths, run = open_run(wish)
    assert result["status"] == "waiting"
    assert len(runtime.starts) == 1 and len(runtime.resumes) == 2
    assert len(runtime.pending) == 2 and len(runtime.make) == 1
    assert (paths.host_state / "codex-session.json").read_bytes() == SESSION_BYTES
    assert json.loads((paths.workspace / "selection-notes.json").read_text())["candidate"] == "preserved"
    assert runtime.make[0]["inputs"]["workshop_selection"]["assignment"]["selected_inventor_id"] == runtime.markers[-1]["selected_inventor_id"]
    assert not run.snapshot().stage_artifacts.get("match")


def test_malformed_selection_is_repaired_before_make_without_a_new_session(host):
    runtime = SelectionRuntime(["malformed", "select"])
    wish = host(runtime)
    result = start_native_run(wish, effort="spark")
    assert result["status"] == "waiting"
    assert len(runtime.starts) == 1 and len(runtime.resumes) == 2
    assert len(runtime.pending) == 2 and len(runtime.make) == 1
    feedback = runtime.pending[1]["inputs"]["workshop_selection"]["feedback"]
    assert "ranking" in feedback and "every roster inventor" in feedback
    paths, run = open_run(wish)
    assert not run.snapshot().stage_artifacts.get("match")
    assert not run.snapshot().stage_artifacts.get("make")
    assert json.loads((paths.host_state / INVENTOR_SELECTION_RECEIPT_NAME).read_text())["assignment"]["ranking"] == runtime.markers[-1]["ranking"]


def test_private_selection_receipt_wins_over_replaced_workspace_marker(host):
    runtime = SelectionRuntime()
    wish = host(runtime)
    start_native_run(wish, effort="spark")
    paths, run = open_run(wish)
    checkpoint = run.snapshot()
    roster = InventorRoster.from_mapping(runtime.make[0]["inputs"]["inventor_roster"])
    before, _ = _workshop_inventor_selection(run, checkpoint, roster)
    (paths.workspace / INVENTOR_SELECTION_MARKER_NAME).write_text("{not valid JSON")
    after, feedback = _workshop_inventor_selection(run, checkpoint, roster)
    assert after == before and feedback is None


@pytest.mark.parametrize("change", ["inventor", "ranking"])
def test_make_cannot_replace_workshop_selection_before_product_bytes_are_opened(host, change):
    runtime = SelectionRuntime()
    wish = host(runtime)
    start_native_run(wish, effort="spark")
    paths, run = open_run(wish)
    checkpoint = run.snapshot()
    subject, packet, context = _prepare_stage_input(run, checkpoint)
    selected = context["workshop_selected_assignment"]
    if change == "ranking":
        changed = replace(selected, ranking=(
            MatchRankingEntry(selected.ranking[0].inventor_id, "A different selection rationale."),
            *selected.ranking[1:],
        ))
    else:
        entry = context["roster"].inventor(selected.ranking[1].inventor_id)
        ranking = sorted(selected.ranking, key=lambda row: row.inventor_id != entry.inventor_id)
        changed = replace(
            selected, selected_inventor_id=entry.inventor_id,
            selected_agent_path=entry.agent_path, selected_agent_sha256=entry.agent_sha256,
            selected_source_manifest_sha256=entry.source_manifest_sha256,
            selected_taste_sha256=entry.taste_sha256, ranking=tuple(ranking),
        )
    assignment_path = context["assignment_contract_path"]
    write_json(paths.workspace / assignment_path, changed.to_dict())
    assignment_bytes = (paths.workspace / assignment_path).read_bytes()
    proposal = AgentOutcomeProposal(
        checkpoint_sha256=checkpoint.checkpoint_sha256, subject_sha256=subject,
        outcome=AgentOutcome(
            stage="make", status="ready", proposed_transition="release",
            artifacts=(
                AgentArtifact("artifacts/make/r0001/made.json", "a" * 64),
                AgentArtifact(assignment_path, hashlib.sha256(assignment_bytes).hexdigest()),
                AgentArtifact(context["invented_contract_path"], "b" * 64),
            ),
        ),
    )
    with pytest.raises(_MakeProposalRejected) as failure:
        _evaluate_make_stage(proposal, run=run, checkpoint=checkpoint, subject_sha256=subject, context=context)
    assert "accepted inventor selection" in str(failure.value.__cause__)
    assert failure.value.failure_code == "make-inventor-selection-mismatch"
    assert "inputs.workshop_selection.assignment" in failure.value.feedback
    assert "do not regenerate CAD" in failure.value.feedback
    assert not (paths.workspace / "artifacts/make/r0001/made.json").exists()


@pytest.mark.parametrize("action", ["premature", "premature-ready", "premature-garbage", "premature-interrupt"])
def test_premature_outcome_is_preserved_then_selection_repairs_without_product_gate(host, action):
    runtime = SelectionRuntime([action, "select"])
    wish = host(runtime)
    if action == "premature-interrupt":
        with pytest.raises(KeyboardInterrupt):
            start_native_run(wish, effort="spark")
        result = resume_native_run(wish.product_id)
    else:
        result = start_native_run(wish, effort="spark")
    assert result["status"] == "waiting"
    assert len(runtime.pending) == 2 and len(runtime.make) == 1
    assert len(runtime.starts) == 1 and len(runtime.resumes) == 2
    feedback = runtime.pending[1]["inputs"]["workshop_selection"]["feedback"]
    assert "premature stage proposal" in feedback
    assert "Finish inventor selection first" in feedback
    paths, run = open_run(wish)
    preserved = list((paths.host_state / "inventor-selection-quarantine").glob("*.json"))
    assert len(preserved) == 1
    assert preserved[0].read_bytes() == runtime.premature_bytes[0]
    assert preserved[0].stat().st_mode & 0o777 == 0o600
    assert (paths.workspace / "early-work.txt").read_text() == "Keep this existing work."
    assert not run.snapshot().stage_artifacts.get("make")
    assert not run.snapshot().stage_artifacts.get("match")
    gates = list((paths.host_state / "gates").glob("*.json"))
    assert len(gates) == 1
    assert json.loads(gates[0].read_text())["kind"] == "autonomous-workshop.wish-gate-evidence"


@pytest.mark.parametrize("effort", ["forge", "quest"])
def test_existing_deep_routes_keep_their_proof_boundary(host, effort):
    class DeepProofRuntime(_OneSessionProductAgent):
        def _turn(self, arguments):
            self.arguments = arguments
            return super()._turn(arguments)

        def _author_make(self, run_root, stage):
            assert "workshop_selection" not in stage["inputs"]
            assert self.arguments["finalization_marker"] == run_root / ".make-proof-ready.json"
            _FakeLauncher._write_waiting(self.arguments)

    runtime = DeepProofRuntime()
    wish = host(runtime)
    result = start_native_run(wish, effort=effort)
    assert result["status"] == "waiting"
    assert len(runtime.starts) == 1 and len(runtime.resumes) == 1
    assert not runtime.selection_packets
    assert [packet["stage"] for packet in runtime.stage_packets] == ["invent", "make"]
