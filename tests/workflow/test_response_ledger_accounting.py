"""Host accounting upgrades never substitute old spend for a new turn."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from workshop.errors import ContractError
from workshop.runtime.codex import CodexNativeSessionLauncher
from workshop.runtime.codex_usage import UsageUnavailable, UsageNotReady, read_product_usage
from workshop.workflow import native_run as host
from workshop.workflow.budgets import BUDGETS_CAPABILITY_PATH
from workshop.workflow.token_budget import ProductTokenBudget, TOKEN_BUDGET_CAPABILITY_PATH
from tests.runtime.test_codex_usage import ROOT, CHILD, counters, write
from tests.runtime.test_codex_response_usage import start, response, notification, completed_events
from tests.runtime.test_codex_native_session import TEST_CODEX_BINARY
from tests.workflow.test_token_budget import observation


def metered(n, *, source="response-ledger-v1", child=0):
    value = observation(n)
    if child:
        value["threads"].append({"thread_id": CHILD, "tokens": counters(child), "status": "observed"})
        value["tokens"] = counters(n + child)
        value["total_tokens"] = (n + child) * 11 // 10
    if source == "response-ledger-v1":
        for thread in value["threads"]:
            thread["accounting_source"] = source
    return value


@pytest.fixture
def launch_context(tmp_path):
    paths = SimpleNamespace(host_state=tmp_path, workspace=tmp_path / "workspace")
    paths.workspace.mkdir()
    checkpoint = SimpleNamespace(manager_id="codex", product_id="saved", wish_sha256="a" * 64,
        input_sha256s={TOKEN_BUDGET_CAPABILITY_PATH: "b" * 64, BUDGETS_CAPABILITY_PATH: "c" * 64},
        stage="invent", status="active", checkpoint_sha256="d" * 64)
    factory = mock.Mock()
    launcher = CodexNativeSessionLauncher(
        binary=TEST_CODEX_BINARY, cli_version="0.153.4", popen_factory=factory,
    )
    return paths, checkpoint, launcher, factory


def test_saved_budget_accepts_monotonic_ledger_upgrade_without_resetting_cap_or_threads(tmp_path):
    sessions = tmp_path / "sessions"
    write(sessions, completed_events())
    write(sessions, completed_events(CHILD, ROOT), CHILD)
    observed = read_product_usage(sessions, thread_id=ROOT, workspace=Path("/toy"))
    previous = copy.deepcopy(observed)
    for thread in previous["threads"]:
        thread["tokens"] = counters(300)
    previous["tokens"] = counters(600)
    previous["total_tokens"] = 660
    budget = ProductTokenBudget(100_000_000)
    budget.observe(previous)
    paths = SimpleNamespace(host_state=tmp_path / "state")
    paths.host_state.mkdir()
    checkpoint = SimpleNamespace(manager_id="codex", product_id="saved", wish_sha256="a" * 64,
        input_sha256s={TOKEN_BUDGET_CAPABILITY_PATH: "b" * 64}, stage="make")
    host._save_lifetime_budget(paths, checkpoint, budget)
    restored = host._load_lifetime_budget(paths, checkpoint)
    restored.observe(observed)
    host._save_lifetime_budget(paths, checkpoint, restored)
    reloaded = host._load_lifetime_budget(paths, checkpoint)
    assert reloaded.limit == 100_000_000
    assert reloaded.to_dict()["used_tokens"] == 1100
    assert reloaded.observation["threads"] == observed["threads"]
    assert {item["thread_id"] for item in reloaded.observation["threads"]} == {ROOT, CHILD}


def test_completed_turn_cannot_reconcile_against_a_lagging_ledger_prefix(tmp_path):
    sessions = tmp_path / "sessions"
    events = start() + [response("a", 100, 100), notification(100, 100)]
    path = write(sessions, events)
    observed = lambda: read_product_usage(sessions, thread_id=ROOT, workspace=Path("/toy"))
    paths = SimpleNamespace(host_state=tmp_path / "state")
    paths.host_state.mkdir()
    checkpoint = SimpleNamespace(manager_id="codex", product_id="saved", wish_sha256="a" * 64,
        input_sha256s={TOKEN_BUDGET_CAPABILITY_PATH: "b" * 64}, stage="make")
    budget = ProductTokenBudget(100_000_000)
    budget.observe(observed())
    observer = host._product_token_observer(paths, checkpoint, budget)
    with mock.patch.object(host, "_read_product_token_usage", side_effect=lambda *_: observed()):
        with pytest.raises(UsageUnavailable, match="completed native turn"):
            observer.reconcile_completed_turn((100, None, None, 10, None))
        assert (paths.host_state / "token-accounting-need.json").exists()
        with path.open("a") as stream:
            stream.write(json.dumps(response("b", 100, 200)) + "\n")
        host._reconcile_token_accounting_need(paths, checkpoint, budget)
    assert not (paths.host_state / "token-accounting-need.json").exists()
    assert budget.to_dict()["used_tokens"] == 220


def test_prelaunch_refresh_excludes_historical_correction_and_child_growth_from_new_turn(launch_context):
    paths, checkpoint, initial, factory = launch_context
    budget = ProductTokenBudget(100_000_000)
    budget.observe(metered(100, source="token-count-v1", child=100))
    current = metered(1000, child=100)
    with mock.patch.object(host, "_read_product_token_usage", side_effect=lambda *_: current):
        launcher = host._token_budget_launcher(paths, checkpoint, initial, budget, None)
        assert host._load_lifetime_budget(paths, checkpoint).observation == current
        with pytest.raises(UsageUnavailable, match="completed native turn"):
            launcher.token_budget_observer.reconcile_completed_turn((100, None, None, 10, None))
        need = json.loads((paths.host_state / "token-accounting-need.json").read_text())
        assert need["schema_version"] == 2
        assert need["baseline_source"] == "response-ledger-v1"
        assert need["baseline_root_tokens"] == {"input_tokens": 1000, "output_tokens": 100}
        current = metered(1000, child=200)
        with pytest.raises(UsageUnavailable, match="completed native turn"):
            host._reconcile_token_accounting_need(paths, checkpoint, budget)
        current = metered(1100, child=200)
        host._reconcile_token_accounting_need(paths, checkpoint, budget)
        assert not (paths.host_state / "token-accounting-need.json").exists()
        current = metered(1200, child=200)
        continuation = host._token_budget_launcher(paths, checkpoint, initial, budget, None)
        with pytest.raises(UsageUnavailable, match="completed native turn"):
            continuation.token_budget_observer.reconcile_completed_turn((100, None, None, 10, None))
        need = json.loads((paths.host_state / "token-accounting-need.json").read_text())
        assert need["baseline_root_tokens"] == {"input_tokens": 1200, "output_tokens": 120}
    assert budget.limit == 100_000_000
    factory.assert_not_called()


def test_prelaunch_corrected_cap_exhaustion_stops_before_native_launch(launch_context):
    paths, checkpoint, initial, factory = launch_context
    budget = ProductTokenBudget(1000)
    budget.observe(metered(100))
    with mock.patch.object(host, "_read_product_token_usage", return_value=metered(1000)), pytest.raises(ContractError, match="limit reached"):
        host._token_budget_launcher(paths, checkpoint, initial, budget, None)
    assert host._load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 1100
    factory.assert_not_called()


def test_prelaunch_missing_established_usage_fails_but_unbound_new_root_can_start(launch_context):
    paths, checkpoint, initial, factory = launch_context
    established = ProductTokenBudget()
    established.observe(metered(100))
    with mock.patch.object(host, "_read_product_token_usage", side_effect=UsageUnavailable("broken")), pytest.raises(UsageUnavailable):
        host._token_budget_launcher(paths, checkpoint, initial, established, None)
    factory.assert_not_called()
    (paths.host_state / "token-accounting-need.json").unlink()
    fresh = ProductTokenBudget()
    with mock.patch.object(host, "_read_product_token_usage", side_effect=UsageNotReady("unbound")):
        launcher = host._token_budget_launcher(paths, checkpoint, initial, fresh, None)
    assert fresh.observation is None
    with mock.patch.object(host, "_read_product_token_usage", return_value=metered(100)):
        launcher.token_budget_observer.reconcile_completed_turn((100, None, None, 10, None))
    assert fresh.to_dict()["used_tokens"] == 110
    assert not (paths.host_state / "token-accounting-need.json").exists()


def test_bound_pending_root_can_resume_into_its_first_ledger_response(launch_context):
    paths, checkpoint, initial, _ = launch_context
    pending = metered(0, source="token-count-v1")
    pending["threads"][0]["status"] = "pending"
    budget = ProductTokenBudget()
    budget.observe(pending)
    with mock.patch.object(host, "_read_product_token_usage", return_value=pending):
        launcher = host._token_budget_launcher(paths, checkpoint, initial, budget, None)
    with mock.patch.object(host, "_read_product_token_usage", return_value=metered(100)):
        launcher.token_budget_observer.reconcile_completed_turn((100, None, None, 10, None))
    assert budget.to_dict()["used_tokens"] == 110
    assert not (paths.host_state / "token-accounting-need.json").exists()


@pytest.mark.parametrize("baseline_source,observed_source", [
    (None, "response-ledger-v1"), ("token-count-v1", "response-ledger-v1"),
    ("response-ledger-v1", "token-count-v1"),
])
def test_completed_need_never_uses_an_incomparable_historical_baseline(launch_context, baseline_source, observed_source):
    paths, checkpoint, _, _ = launch_context
    budget = ProductTokenBudget()
    budget.observe(metered(100, source=baseline_source or "token-count-v1"))
    host._record_token_accounting_need(
        paths, checkpoint, {"input_tokens": 100, "output_tokens": 10},
        completed_turn=True, terminal_usage={"input_tokens": 100, "output_tokens": 10},
        baseline_source=baseline_source,
    )
    need = paths.host_state / "token-accounting-need.json"
    before = need.read_bytes()
    with mock.patch.object(host, "_read_product_token_usage", return_value=metered(1000, source=observed_source)), pytest.raises(UsageUnavailable, match="comparable accounting baseline"):
        host._reconcile_token_accounting_need(paths, checkpoint, budget)
    assert need.read_bytes() == before
    assert budget.to_dict()["used_tokens"] == 1100


def test_old_nonterminal_need_recovers_from_richer_ledger_normally(launch_context):
    paths, checkpoint, _, _ = launch_context
    budget = ProductTokenBudget()
    budget.observe(metered(100, source="token-count-v1"))
    host._record_token_accounting_need(paths, checkpoint, {"input_tokens": 100, "output_tokens": 10})
    with mock.patch.object(host, "_read_product_token_usage", return_value=metered(1000)):
        host._reconcile_token_accounting_need(paths, checkpoint, budget)
    assert not (paths.host_state / "token-accounting-need.json").exists()
    assert budget.to_dict()["used_tokens"] == 1100


def test_plain_resume_refreshes_usage_before_pending_host_work(launch_context):
    paths, checkpoint, _, _ = launch_context
    budget = ProductTokenBudget(1000)
    budget.observe(metered(100, source="token-count-v1"))
    host._save_lifetime_budget(paths, checkpoint, budget)
    run = SimpleNamespace(snapshot=lambda: checkpoint)
    with mock.patch.object(host, "native_run_paths", return_value=paths), mock.patch.object(
        host, "_open_budgeted_agent_run", return_value=run
    ), mock.patch.object(host, "_read_product_token_usage", return_value=metered(1000)), mock.patch.object(
        host, "_resume_native_run_locked"
    ) as pending_work:
        host.resume_native_run(checkpoint.product_id)
    pending_work.assert_called_once()
    assert host._load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 1100
