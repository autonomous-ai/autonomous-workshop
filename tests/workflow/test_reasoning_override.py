"""Explicit operator effort changes preserve one product's native authority."""

import copy
import hashlib
import json
from contextlib import ExitStack, redirect_stdout
from dataclasses import replace
from io import StringIO
from types import SimpleNamespace
from unittest import mock

import pytest

from cli.main import main, parser
from workshop.errors import ContractError, StateConflict
from workshop.runtime.codex import CodexNativeSessionLauncher
from workshop.runtime.managers import MANAGER_PROJECT_PATH
from workshop.workflow import native_run as host
from workshop.workflow.agent_run import AgentRunCheckpoint
from workshop.workflow.budgets import BUDGETS_CAPABILITY_PATH
from workshop.workflow.reasoning_override import REASONING_OVERRIDE_NAME
from workshop.workflow.token_budget import ProductTokenBudget, TOKEN_BUDGET_CAPABILITY_PATH
from tests.runtime import test_codex_native_session as native_fakes
from tests.workflow.test_token_budget import observation


def digest(value):
    return hashlib.sha256(value).hexdigest()


def sealed(value, field):
    value = {key: item for key, item in value.items() if key != field}
    value[field] = digest(host._canonical_json_bytes(value))
    return value


@pytest.fixture
def saved(tmp_path):
    paths = host.NativeRunPaths(tmp_path / "workspace", tmp_path / "state")
    paths.workspace.mkdir(mode=0o700)
    paths.host_state.mkdir(mode=0o700)
    inputs = {}
    for name, content in {
        "WISH.json": '{"objective":"one exact toy"}\n',
        MANAGER_PROJECT_PATH: '{"model":"gpt-6-astra","reasoning_effort":"ultra"}\n',
        "AGENTS.md": "Frozen toy instructions.\n",
        ".agents/skills/autonomous-workshop/SKILL.md": "Frozen workflow.\n",
        BUDGETS_CAPABILITY_PATH: "Frozen budget profile.\n",
        TOKEN_BUDGET_CAPABILITY_PATH: "Frozen token budget capability.\n",
    }.items():
        path = paths.workspace / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        path.chmod(0o400)
        inputs[name] = digest(path.read_bytes())
    checkpoint = AgentRunCheckpoint(
        product_id="effort-test", stage="invent", status="active", revision=2,
        round_index=1, max_rounds=4, wish_sha256=inputs["WISH.json"],
        run_root_sha256=digest(str(paths.workspace).encode()),
        host_state_root_sha256=digest(str(paths.host_state).encode()),
        checkpoint_sha256="c" * 64, input_sha256s=inputs,
        inventor_roster=(), stage_artifacts={}, invalidated_stages=(),
        effort="spark", manager_id="codex", manager_model="gpt-6-astra",
        manager_reasoning_effort="ultra", token_budgeted=True,
    )
    session = {
        "schema_version": 1, "kind": "autonomous-workshop-native-codex-session",
        "product_id": checkpoint.product_id, "wish_sha256": checkpoint.wish_sha256,
        "constitution_sha256": host.materialized_agent_instructions_sha256(checkpoint),
        "run_root_sha256": checkpoint.run_root_sha256,
        "host_state_root_sha256": checkpoint.host_state_root_sha256,
        "runtime_config_sha256": "d" * 64, "cli_version": "0.153.4",
        "permission_profile": "workshop-product-run", "native_web_search": True,
        "thread_id": native_fakes.THREAD_ID,
    }
    host._write_private_json(paths.host_state / "codex-session.json", sealed(session, "checkpoint_sha256"))
    budget = ProductTokenBudget(100_000_000)
    budget.observe(observation(100))
    host._save_lifetime_budget(paths, checkpoint, budget)
    run = SimpleNamespace(snapshot=lambda: checkpoint, run_root=paths.workspace)
    return paths, checkpoint, budget, run


def resume_context(paths, run, callback):
    stack = ExitStack()
    stack.enter_context(mock.patch.object(host, "native_run_paths", return_value=paths))
    stack.enter_context(mock.patch.object(host, "_open_budgeted_agent_run", return_value=run))
    stack.enter_context(mock.patch.object(host, "_resume_native_run_locked", side_effect=callback))
    return stack


def test_explicit_resume_is_durable_idempotent_and_preserves_frozen_bytes_and_usage(saved):
    paths, checkpoint, budget, run = saved
    frozen = {path: path.read_bytes() for path in paths.workspace.rglob("*") if path.is_file()}
    session_before = (paths.host_state / "codex-session.json").read_bytes()
    budget_before = (paths.host_state / "native-budget.json").read_bytes()

    def receipt(*_, **__):
        return host._native_receipt(checkpoint, paths=paths, action="resumed")

    with resume_context(paths, run, receipt):
        first = host.resume_native_run(checkpoint.product_id, reasoning_effort="medium")
        record = paths.host_state / REASONING_OVERRIDE_NAME
        exact = record.read_bytes()
        identity = record.stat()
        second = host.resume_native_run(checkpoint.product_id, reasoning_effort="medium")
        third = host.resume_native_run(checkpoint.product_id)
    for value in (first, second, third):
        assert value["effort"] == "medium"
        assert value["initial_effort"] == "ultra"
        assert value["budget"]["limit_tokens"] == 100_000_000
        assert value["budget"]["used_tokens"] == 110
    assert record.read_bytes() == exact
    assert record.stat().st_mtime_ns == identity.st_mtime_ns
    assert record.stat().st_mode & 0o777 == 0o600
    assert len(json.loads(exact)["changes"]) == 1
    assert (paths.host_state / "native-budget.json").read_bytes() == budget_before
    assert (paths.host_state / "codex-session.json").read_bytes() == session_before
    assert all(path.read_bytes() == content for path, content in frozen.items())
    assert checkpoint.manager_reasoning_effort == "ultra"
    host._set_reasoning_override(paths, checkpoint, "high")
    host._set_reasoning_override(paths, checkpoint, "ultra")
    changes = host._read_reasoning_override(paths, checkpoint)["changes"]
    assert [(item["previous_effort"], item["effort"]) for item in changes] == [
        ("ultra", "medium"), ("medium", "high"), ("high", "ultra"),
    ]


def test_cli_forwards_only_explicit_effort_and_reports_initial_selection():
    assert parser().parse_args(("resume", "toy")).effort is None
    result = {"product_id": "toy", "status": "active", "stage": "make",
              "agent": "codex", "model": "gpt-6-astra", "effort": "medium", "initial_effort": "ultra"}
    output = StringIO()
    with mock.patch("cli.main.resume_native_run", return_value=result) as resume, redirect_stdout(output):
        assert main(("resume", "toy", "--effort", "medium", "--max-tokens", "100000000")) == 0
        assert resume.call_args.kwargs["reasoning_effort"] == "medium"
        assert resume.call_args.kwargs["max_tokens"] == 100_000_000
        assert main(("resume", "toy")) == 0
        assert "reasoning_effort" not in resume.call_args.kwargs
    assert "effort medium" in output.getvalue()
    assert "Initial effort: ultra" in output.getvalue()
    for invalid in ("forge", "max", "invalid"):
        with pytest.raises(SystemExit):
            parser().parse_args(("resume", "toy", "--effort", invalid))


@pytest.mark.parametrize("change", [
    {"manager_id": "claude"}, {"manager_id": "grok"},
    {"manager_reasoning_effort": None}, {"status": "complete"},
    {"manager_model": "gpt-5.6-sol", "manager_reasoning_effort": "medium"},
    {"missing": BUDGETS_CAPABILITY_PATH}, {"missing": TOKEN_BUDGET_CAPABILITY_PATH},
])
def test_unsupported_requests_do_not_write_or_launch(saved, change):
    paths, checkpoint, _, _ = saved
    if "missing" in change:
        checkpoint = replace(checkpoint, input_sha256s={
            key: value for key, value in checkpoint.input_sha256s.items() if key != change["missing"]
        })
    else:
        checkpoint = replace(checkpoint, **change)
    run = SimpleNamespace(snapshot=lambda: checkpoint)
    callback = mock.Mock()
    before = (paths.host_state / "native-budget.json").read_bytes()
    with resume_context(paths, run, callback), pytest.raises(ContractError):
        host.resume_native_run(checkpoint.product_id, reasoning_effort="ultra", max_tokens=120_000_000)
    callback.assert_not_called()
    assert not (paths.host_state / REASONING_OVERRIDE_NAME).exists()
    assert (paths.host_state / "native-budget.json").read_bytes() == before


@pytest.mark.parametrize("change", ["invalid-json", "duplicate-key", "symlink", "broken-link", "mode", "hash", "history", "thread", "model", "profile"])
def test_corrupt_override_fails_closed_on_status_and_resume_without_flag(saved, change):
    paths, checkpoint, _, run = saved
    host._set_reasoning_override(paths, checkpoint, "medium")
    record = paths.host_state / REASONING_OVERRIDE_NAME
    if change == "invalid-json":
        record.write_text("{")
    elif change == "duplicate-key":
        record.write_text('{"schema_version":1,"schema_version":1}')
    elif change in ("symlink", "broken-link"):
        moved = record.with_name("moved.json")
        record.rename(moved)
        record.symlink_to(moved if change == "symlink" else record.with_name("missing.json"))
    elif change == "mode":
        record.chmod(0o644)
    else:
        value = json.loads(record.read_text())
        if change == "hash":
            value["record_sha256"] = "0" * 64
        elif change == "history":
            value["changes"][0]["previous_effort"] = "low"
        else:
            key = {"thread": "thread_id", "model": "model", "profile": "runtime_profile_sha256"}[change]
            value["binding"][key] = "different"
        if change != "hash":
            value = sealed(value, "record_sha256")
        host._write_private_json(record, value)
    callback = mock.Mock()
    with pytest.raises(StateConflict):
        host._native_receipt(checkpoint, paths=paths, action="inspected")
    with resume_context(paths, run, callback), pytest.raises(StateConflict):
        host.resume_native_run(checkpoint.product_id)
    callback.assert_not_called()


@pytest.mark.parametrize("field,value", [
    ("product_id", "another-product"), ("wish_sha256", "e" * 64),
    ("thread_id", "01a08b82-68d1-72c0-8876-a9a9074885d8"),
    ("thread_id", "not-a-canonical-uuid"), ("run_root_sha256", "e" * 64),
    ("host_state_root_sha256", "e" * 64), ("native_web_search", False),
    ("schema_version", True), ("checkpoint_sha256", "0" * 64),
])
def test_current_session_substitution_is_not_override_authority(saved, field, value):
    paths, checkpoint, _, _ = saved
    host._set_reasoning_override(paths, checkpoint, "medium")
    path = paths.host_state / "codex-session.json"
    session = json.loads(path.read_text())
    session[field] = value
    if field != "checkpoint_sha256":
        session = sealed(session, "checkpoint_sha256")
    host._write_private_json(path, session)
    with pytest.raises(StateConflict):
        host._read_reasoning_override(paths, checkpoint)


def test_override_survives_supported_instruction_rebind_and_checkpoint_revision(saved):
    paths, checkpoint, _, _ = saved
    host._set_reasoning_override(paths, checkpoint, "medium")
    original = (paths.host_state / REASONING_OVERRIDE_NAME).read_bytes()
    launcher = CodexNativeSessionLauncher(binary=native_fakes.TEST_CODEX_BINARY, cli_version="0.153.4")
    changed = replace(checkpoint, checkpoint_sha256="e" * 64, revision=3, input_sha256s={
        **checkpoint.input_sha256s, ".agents/skills/cad/scripts/fix": "f" * 64,
    })
    launcher.rebind_session_constitution(
        product_id=checkpoint.product_id, wish_sha256=checkpoint.wish_sha256,
        run_root=paths.workspace, host_state_root=paths.host_state,
        constitution_sha256=host.materialized_agent_instructions_sha256(changed),
    )
    assert host._read_reasoning_override(paths, changed)["changes"][-1]["effort"] == "medium"
    assert (paths.host_state / REASONING_OVERRIDE_NAME).read_bytes() == original


def test_lock_and_failure_paths_preserve_operator_choice_without_new_session(saved):
    paths, checkpoint, _, run = saved
    callback = mock.Mock(side_effect=ContractError("simulated launch failure"))
    with resume_context(paths, run, callback):
        with host._native_run_mutation_lock(paths), pytest.raises(StateConflict, match="already mutating"):
            host.resume_native_run(checkpoint.product_id, reasoning_effort="medium")
        assert not (paths.host_state / REASONING_OVERRIDE_NAME).exists()
        with pytest.raises(ContractError, match="simulated launch failure"):
            host.resume_native_run(checkpoint.product_id, reasoning_effort="medium")
        assert host._read_reasoning_override(paths, checkpoint)["changes"][-1]["effort"] == "medium"
        callback.side_effect = lambda *_, **__: host._read_reasoning_override(paths, checkpoint)
        assert host.resume_native_run(checkpoint.product_id)["changes"][-1]["effort"] == "medium"


@pytest.mark.parametrize("first_failure", [None, host._RecoverableNativeTurn("provider disconnect")])
def test_common_loop_keeps_medium_and_token_observer_through_continuations(saved, first_failure):
    paths, checkpoint, _, run = saved
    host._set_reasoning_override(paths, checkpoint, "medium")
    initial = CodexNativeSessionLauncher(
        model="gpt-6-astra", reasoning_effort="ultra", cli_version="0.153.4",
        binary=native_fakes.TEST_CODEX_BINARY,
    )
    calls = []
    observer = lambda: None

    def call(launcher, method, **kwargs):
        calls.append(kwargs)
        assert method == "resume"
        assert launcher.reasoning_effort == "medium"
        assert launcher.model == "gpt-6-astra"
        assert launcher.token_budget_observer is observer
        assert launcher.runtime_profile_sha256 == checkpoint.input_sha256s[BUDGETS_CAPABILITY_PATH]
        if len(calls) == 2:
            raise KeyboardInterrupt
        if first_failure is not None:
            raise first_failure
        return None  # Ordinary completion without a stage proposal must continue.

    before = (paths.host_state / "native-budget.json").read_bytes()
    with mock.patch.object(host, "_prepare_stage_input", return_value=("e" * 64, {"inputs": {}}, {})), mock.patch.object(
        host, "_launcher_call", side_effect=call
    ), mock.patch.object(host, "_product_token_observer", return_value=observer), mock.patch.object(
        host.time, "sleep"
    ), pytest.raises(KeyboardInterrupt):
        host._run_native_session(run, paths, launcher=initial)
    assert len(calls) == 2
    assert calls[1]["recoverable_continuation"] is (first_failure is not None)
    assert calls[1]["unfinished_returns"] == (1 if first_failure is None else 0)
    assert (paths.host_state / "native-budget.json").read_bytes() == before
    assert json.loads((paths.host_state / "codex-session.json").read_text())["thread_id"] == native_fakes.THREAD_ID


def test_atomic_write_failure_preserves_previous_selection(saved):
    paths, checkpoint, _, _ = saved
    host._set_reasoning_override(paths, checkpoint, "medium")
    path = paths.host_state / REASONING_OVERRIDE_NAME
    before = path.read_bytes()
    with mock.patch.object(host.os, "replace", side_effect=OSError("simulated disk failure")), pytest.raises(OSError):
        host._set_reasoning_override(paths, checkpoint, "high")
    assert path.read_bytes() == before
    assert host._read_reasoning_override(paths, checkpoint)["changes"][-1]["effort"] == "medium"
    assert not list(paths.host_state.glob(".reasoning-effort.json.*.tmp"))


def test_real_adapter_resumes_exact_thread_at_medium_with_same_config_and_truthful_prompt(saved):
    paths, checkpoint, budget, _ = saved
    (paths.host_state / "codex-session.json").unlink()
    factory = native_fakes.FakePopenFactory([
        {"stdout": native_fakes.CodexNativeSessionTest.start_events()} for _ in range(3)
    ])
    initial = CodexNativeSessionLauncher(
        model="gpt-6-astra", reasoning_effort="ultra", cli_version="0.153.4",
        binary=native_fakes.TEST_CODEX_BINARY, popen_factory=factory,
        runtime_profile_sha256=checkpoint.input_sha256s[BUDGETS_CAPABILITY_PATH],
        timeout_seconds=None,
    )
    initial.token_budget_observer = lambda: None
    started = host._launcher_call(initial, "start", paths=paths, checkpoint=checkpoint)
    host._set_reasoning_override(paths, checkpoint, "medium")
    observer = lambda: None
    before = copy.deepcopy(budget.to_dict())
    for stage in ("invent", "make"):
        current = replace(checkpoint, stage=stage)
        override = host._read_reasoning_override(paths, current)
        with mock.patch.object(host, "_product_token_observer", return_value=observer):
            resumed_launcher = host._token_budget_launcher(paths, current, initial, budget, override)
        assert resumed_launcher.token_budget_observer is observer
        resumed = host._launcher_call(resumed_launcher, "resume", paths=paths, checkpoint=current)
        assert json.loads((paths.host_state / "codex-session.json").read_text())["thread_id"] == native_fakes.THREAD_ID
        assert resumed.binding.runtime_config_sha256 == started.binding.runtime_config_sha256
        assert resumed_launcher.reasoning_effort == "medium"
    assert budget.to_dict() == before
    assert 'model_reasoning_effort="ultra"' in factory.calls[0][0]
    for argv, kwargs in factory.calls[1:]:
        assert 'model_reasoning_effort="medium"' in argv
        assert native_fakes.THREAD_ID in argv
    for process in factory.processes[1:]:
        assert "operator explicitly selected medium" in process.stdin.value
        assert "original ultra selection as provenance" in process.stdin.value


def test_ordinary_profile_drift_still_fails_before_process_launch(saved):
    paths, checkpoint, budget, _ = saved
    (paths.host_state / "codex-session.json").unlink()
    factory = native_fakes.FakePopenFactory([
        {"stdout": native_fakes.CodexNativeSessionTest.start_events()},
    ])
    launcher = CodexNativeSessionLauncher(
        model="gpt-6-astra", reasoning_effort="ultra", cli_version="0.153.4",
        binary=native_fakes.TEST_CODEX_BINARY, popen_factory=factory,
        runtime_profile_sha256=checkpoint.input_sha256s[BUDGETS_CAPABILITY_PATH], timeout_seconds=None,
    )
    launcher.token_budget_observer = lambda: None
    host._launcher_call(launcher, "start", paths=paths, checkpoint=checkpoint)
    host._set_reasoning_override(paths, checkpoint, "medium")
    override = host._read_reasoning_override(paths, checkpoint)
    changed = host._token_budget_launcher(paths, checkpoint, launcher, budget, override)
    changed.runtime_profile_sha256 = "f" * 64
    with pytest.raises(ContractError, match="binding"):
        host._launcher_call(changed, "resume", paths=paths, checkpoint=checkpoint)
    assert len(factory.calls) == 1
