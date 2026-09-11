import copy
import json
from dataclasses import make_dataclass, replace
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from cli.main import parser
from workshop.errors import ContractError, StateConflict
from workshop.runtime.codex_usage import UsageUnavailable, UsageNotReady, read_product_usage
from workshop.workflow.budgets import (
    LIFETIME_BUDGETS_CAPABILITY_PATH, TURN_BUDGETS_CAPABILITY_PATH,
    LifetimeBudget, LifetimeTurnBudget,
)
from workshop.workflow.native_run import (
    _load_lifetime_budget, _save_lifetime_budget, _product_token_observer,
    _adopt_token_budget,
    _reconcile_refreshed_token_budget,
    _reconcile_token_accounting_need, _run_native_session,
)
from workshop.workflow.token_budget import (
    ProductTokenBudget, TOKEN_BUDGET_CAPABILITY_PATH, validate_limit,
)
from tests.runtime.test_codex_usage import ROOT, CHILD, counters, records, usage, write


def observation(n=100, child=False):
    threads = [{"thread_id": ROOT, "tokens": counters(n), "status": "observed"}]
    if child:
        threads.append({"thread_id": CHILD, "tokens": counters(n), "status": "observed"})
    return {"schema_version": 1, "source": "codex-native-rollout-v1", "status": "observed",
            "root_thread_id": ROOT, "threads": threads, "tokens": counters(n * len(threads)),
            "total_tokens": n * len(threads) * 11 // 10}


def context(tmp_path):
    return SimpleNamespace(host_state=tmp_path), SimpleNamespace(
        manager_id="codex", product_id="test", wish_sha256="a" * 64,
        input_sha256s={TOKEN_BUDGET_CAPABILITY_PATH: "b" * 64},
        stage="make", status="active", round_index=1, checkpoint_sha256="c" * 64,
    )


def test_global_cap_counts_cache_once_and_survives_reload(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(1000)
    budget.observe(observation(500, child=True))
    _save_lifetime_budget(paths, checkpoint, budget)
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert loaded.to_dict() == budget.to_dict()
    assert loaded.to_dict()["used_tokens"] == 1100
    for stage in ("invent", "make", "playtest", "release"):
        assert loaded.exhausted(stage) == "run"
        with pytest.raises(ContractError):
            loaded.reserve(stage, 1)

def test_many_descendants_survive_large_persistent_ledger_reload(tmp_path):
    paths, checkpoint = context(tmp_path)
    value = observation(100)
    value["threads"] = [
        {"thread_id": ROOT if index == 0 else "018f0000-0000-7000-8000-%012d" % index,
         "tokens": counters(100), "status": "observed"}
        for index in range(500)
    ]
    value["tokens"] = counters(50_000)
    value["total_tokens"] = 55_000
    budget = ProductTokenBudget()
    budget.observe(value)
    _save_lifetime_budget(paths, checkpoint, budget)
    assert (tmp_path / "native-budget.json").stat().st_size > 65_536
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert loaded.to_dict() == budget.to_dict()
    assert loaded.exhausted("make") is None
    run = SimpleNamespace(_load=lambda: {"previous_checkpoint_sha256": "f" * 64})
    _reconcile_refreshed_token_budget(paths, run, checkpoint)


@pytest.mark.parametrize("change", ["symlink", "mode", "duplicate-key", "wrong-identity"])
def test_growing_budget_reader_preserves_private_identity_checks(tmp_path, change):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget()
    budget.observe(observation(100))
    _save_lifetime_budget(paths, checkpoint, budget)
    ledger = tmp_path / "native-budget.json"
    if change == "symlink":
        original = tmp_path / "original.json"
        ledger.rename(original)
        ledger.symlink_to(original)
    elif change == "mode":
        ledger.chmod(0o644)
    elif change == "duplicate-key":
        ledger.write_text('{"schema_version":1,"schema_version":1}')
    else:
        value = json.loads(ledger.read_text())
        value["product_id"] = "another-product"
        ledger.write_text(json.dumps(value))
    with pytest.raises(StateConflict):
        _load_lifetime_budget(paths, checkpoint)


def test_token_budget_has_no_wall_clock_allowance():
    budget = ProductTokenBudget()
    for stage in ("invent", "make", "playtest", "release"):
        assert budget.turn_timeout_seconds(stage) is None


@pytest.mark.parametrize("successor", [False, True])
def test_host_refresh_rebind_preserves_exact_budget_and_is_idempotent(tmp_path, successor):
    paths, original = context(tmp_path)
    Checkpoint = make_dataclass("Checkpoint", [(key, object) for key in vars(original)])
    old = Checkpoint(**vars(original))
    budget = ProductTokenBudget(200_000_000)
    budget.observe(observation(500))
    _save_lifetime_budget(paths, old, budget)
    current = replace(old, input_sha256s={TOKEN_BUDGET_CAPABILITY_PATH: "d" * 64},
                      checkpoint_sha256="e" * 64)
    record = {"kind": "autonomous-workshop.host-correction", "schema_version": 1,
              "correction": "domain-skill-refresh",
              "checkpoint_sha256": "f" * 64 if successor else current.checkpoint_sha256,
              "changes": [{"path": TOKEN_BUDGET_CAPABILITY_PATH,
                           "previous_sha256": "b" * 64, "sha256": "d" * 64}]}
    ledger = tmp_path / "host-corrections.jsonl"
    ledger.write_text(json.dumps(record) + "\n")
    ledger.chmod(0o600)
    run = SimpleNamespace(_load=lambda: {"previous_checkpoint_sha256": "f" * 64})
    _reconcile_refreshed_token_budget(paths, run, current)
    assert _load_lifetime_budget(paths, current).to_dict() == budget.to_dict()
    _reconcile_refreshed_token_budget(paths, run, current)
    assert _load_lifetime_budget(paths, current).to_dict() == budget.to_dict()


def test_host_refresh_refuses_unrelated_budget_binding(tmp_path):
    paths, original = context(tmp_path)
    _save_lifetime_budget(paths, original, ProductTokenBudget())
    original.input_sha256s = {TOKEN_BUDGET_CAPABILITY_PATH: "d" * 64}
    ledger = tmp_path / "host-corrections.jsonl"
    ledger.write_text("{}\n")
    ledger.chmod(0o600)
    run = SimpleNamespace(_load=lambda: {"previous_checkpoint_sha256": "f" * 64})
    with pytest.raises(StateConflict, match="exact host correction"):
        _reconcile_refreshed_token_budget(paths, run, original)


def test_native_child_followup_survives_host_reload_and_enforces_cap(tmp_path):
    paths, checkpoint = context(tmp_path / "state")
    paths.host_state.mkdir()
    sessions = tmp_path / "sessions"
    write(sessions, records() + [usage(300)])
    child_events = records(CHILD, ROOT) + [usage(300)]
    write(sessions, child_events, CHILD)
    budget = ProductTokenBudget(1000)

    def read(_paths, _checkpoint):
        return read_product_usage(sessions, thread_id=ROOT, workspace=Path("/toy"))

    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=read):
        _product_token_observer(paths, checkpoint, budget)()
        loaded = _load_lifetime_budget(paths, checkpoint)
        assert loaded.to_dict()["used_tokens"] == 660
        child_events += [
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "followup"}},
            usage(700, last_token_usage=counters(400)),
        ]
        write(sessions, child_events, CHILD)
        with pytest.raises(ContractError, match="limit reached"):
            _product_token_observer(paths, checkpoint, loaded)()
        assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 1100


@pytest.mark.parametrize("limit", [1000, 30000000, 200000000, 200000001, 500000000])
def test_supported_limit_includes_explicit_500_million(limit):
    assert validate_limit(limit) == limit


@pytest.mark.parametrize("limit", [True, 999, 500000001, 1000.0, "1000", None])
def test_invalid_limit(limit):
    with pytest.raises(ContractError, match="from 1,000 to 500,000,000"):
        validate_limit(limit)


@pytest.mark.parametrize("mutation", [
    lambda o: o.update(total_tokens=0),
    lambda o: o["threads"].pop(),
    lambda o: o["threads"].append(copy.deepcopy(o["threads"][0])),
    lambda o: o["threads"][0]["tokens"].update(input_tokens=True),
    lambda o: o.update(root_thread_id="different"),
])
def test_corrupt_or_regressing_usage_refused(mutation):
    budget = ProductTokenBudget()
    budget.observe(observation(200, child=True))
    invalid = observation(200, child=True)
    mutation(invalid)
    with pytest.raises(ContractError):
        budget.observe(invalid)
    with pytest.raises(ContractError, match="lost prior"):
        budget.observe(observation(100, child=True))


def test_cap_change_preserves_usage(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(1000)
    budget.observe(observation(200))
    _save_lifetime_budget(paths, checkpoint, budget)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=observation(300)):
        _adopt_token_budget(paths, checkpoint, 2000)
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert loaded.limit == 2000
    assert loaded.to_dict()["used_tokens"] == 330


def test_existing_token_cap_update_retains_new_pending_child_and_observed_usage(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(100_000_000)
    budget.observe(observation(500))
    _save_lifetime_budget(paths, checkpoint, budget)
    sessions = tmp_path / "sessions"
    write(sessions, records() + [usage(600)])
    # An ancestry-bound child has started but has no completed token report.
    write(sessions, records(CHILD, ROOT), CHILD)
    recovered = read_product_usage(sessions, thread_id=ROOT, workspace=Path("/toy"))
    pending = next(row for row in recovered["threads"] if row["thread_id"] == CHILD)
    assert pending["status"] == "pending"
    assert pending["tokens"] == counters(0)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=recovered):
        _adopt_token_budget(paths, checkpoint, 500_000_000)
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert loaded.limit == 500_000_000
    assert loaded.to_dict()["used_tokens"] == 660
    assert loaded.observation == recovered
    assert loaded.previous_budget is None


@pytest.mark.parametrize("change", ["regression", "lost_child", "observed_child_becomes_pending"])
def test_pending_cap_update_still_refuses_lost_or_regressing_history(tmp_path, change):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(100_000_000)
    budget.observe(observation(500, child=True))
    _save_lifetime_budget(paths, checkpoint, budget)
    saved = (tmp_path / "native-budget.json").read_bytes()
    if change == "regression":
        recovered = observation(400, child=True)
    else:
        recovered = observation(600)
        if change == "observed_child_becomes_pending":
            recovered["threads"].append({"thread_id": CHILD, "status": "pending", "tokens": counters(0)})
    recovered["threads"].append({
        "thread_id": "01a07960-0efd-76e2-91a9-aa019980ede0",
        "status": "pending", "tokens": counters(0),
    })
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=recovered):
        with pytest.raises(ContractError, match="lost prior usage"):
            _adopt_token_budget(paths, checkpoint, 500_000_000)
    assert (tmp_path / "native-budget.json").read_bytes() == saved


@pytest.mark.parametrize("budget_type,capability", [
    (LifetimeBudget, LIFETIME_BUDGETS_CAPABILITY_PATH),
    (LifetimeTurnBudget, TURN_BUDGETS_CAPABILITY_PATH),
])
def test_legacy_budget_adoption_still_requires_all_threads_observed(tmp_path, budget_type, capability):
    paths, checkpoint = context(tmp_path)
    checkpoint.input_sha256s = {capability: "b" * 64}
    budget = budget_type()
    _save_lifetime_budget(paths, checkpoint, budget)
    saved = (tmp_path / "native-budget.json").read_bytes()
    pending = observation(500)
    pending["threads"].append({"thread_id": CHILD, "status": "pending", "tokens": counters(0)})
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=pending):
        with pytest.raises(ContractError, match="cannot adopt a token cap with unobserved native threads"):
            _adopt_token_budget(paths, checkpoint, 500_000_000)
    assert (tmp_path / "native-budget.json").read_bytes() == saved
    observed = observation(500, child=True)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=observed):
        _adopt_token_budget(paths, checkpoint, 500_000_000)
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert isinstance(loaded, ProductTokenBudget)
    assert loaded.limit == 500_000_000
    assert loaded.observation == observed
    assert loaded.previous_budget == budget.to_dict()


@pytest.mark.parametrize("saved_limit", [100_000_000, 200_000_000])
def test_raise_exhausted_cap_to_500_million_preserves_recovered_usage(tmp_path, saved_limit):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(saved_limit)
    budget.observe(observation(saved_limit))
    assert budget.exhausted("make") == "run"
    _save_lifetime_budget(paths, checkpoint, budget)
    recovered = observation(saved_limit + 10_000_000)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=recovered):
        _adopt_token_budget(paths, checkpoint, 500_000_000)
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert loaded.limit == 500_000_000
    assert loaded.observation == recovered
    assert loaded.to_dict()["used_tokens"] == recovered["total_tokens"]
    assert loaded.to_dict()["used_tokens"] > budget.to_dict()["used_tokens"]
    assert loaded.exhausted("make") is None


def test_over_maximum_cap_update_preserves_existing_ledger(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(100_000_000)
    budget.observe(observation(200))
    _save_lifetime_budget(paths, checkpoint, budget)
    saved = (tmp_path / "native-budget.json").read_bytes()
    with mock.patch("workshop.workflow.native_run._read_product_token_usage") as read_usage:
        with pytest.raises(ContractError, match="500,000,000"):
            _adopt_token_budget(paths, checkpoint, 500_000_001)
    read_usage.assert_not_called()
    assert (tmp_path / "native-budget.json").read_bytes() == saved


def test_missing_ledger_is_not_reset(tmp_path):
    paths, checkpoint = context(tmp_path)
    with pytest.raises(StateConflict):
        _load_lifetime_budget(paths, checkpoint)


def test_observer_stops_at_cap_and_on_lost_accounting(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(1000)
    callback = _product_token_observer(paths, checkpoint, budget)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=observation(1000)):
        with pytest.raises(ContractError, match="limit reached"):
            callback()
    assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 1100
    queued = tmp_path / "vault" / "pending" / ("%s-make-budget.json" % ("c" * 64))
    assert "make-token-budget-stop" in queued.read_text(encoding="utf-8")
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=UsageUnavailable("missing")):
        with pytest.raises(UsageUnavailable):
            callback()


def test_child_followup_preserves_observed_budget_and_enforces_cap(tmp_path):
    paths, checkpoint = context(tmp_path)
    sessions = tmp_path / "sessions"
    paths.workspace = tmp_path / "workspace"
    root = records(cwd=str(paths.workspace)) + [usage(500)]
    child = records(CHILD, ROOT, cwd=str(paths.workspace)) + [usage(200)]
    write(sessions, root)
    write(sessions, child, CHILD)
    budget = ProductTokenBudget(1000)

    def read_usage(*_):
        return read_product_usage(sessions, thread_id=ROOT, workspace=paths.workspace)

    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=read_usage):
        callback = _product_token_observer(paths, checkpoint, budget)
        callback()
        assert budget.to_dict()["used_tokens"] == 770

        child += [
            {"type": "event_msg", "payload": {"type": "task_started", "turn_id": "second"}},
            usage(300, last_token_usage=counters(100)),
        ]
        write(sessions, child, CHILD)
        # An explicit host resume restores the ledger, never resets consumption.
        loaded = _load_lifetime_budget(paths, checkpoint)
        callback = _product_token_observer(paths, checkpoint, loaded)
        callback()
        callback()
        assert loaded.to_dict()["used_tokens"] == 880
        assert not (paths.host_state / "token-budget-stop.json").exists()

        write(sessions, child + [usage(500, last_token_usage=counters(200))], CHILD)
        with pytest.raises(ContractError, match="product token limit reached"):
            callback()
        assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 1100


@pytest.mark.parametrize("root_pending", [False, True])
def test_valid_pending_request_has_no_elapsed_time_limit(tmp_path, root_pending):
    paths, checkpoint = context(tmp_path)
    value = observation(0 if root_pending else 100)
    if root_pending:
        value["threads"][0]["status"] = "pending"
    value["threads"].append({"thread_id": CHILD, "tokens": counters(0), "status": "pending"})
    with mock.patch("workshop.workflow.native_run.time.monotonic", return_value=0) as clock:
        callback = _product_token_observer(paths, checkpoint, ProductTokenBudget())
        with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=value):
            callback()
            for elapsed in (181, 3601, 100_000):
                clock.return_value = elapsed
                callback()
    assert not (tmp_path / "token-accounting-need.json").exists()


def test_initial_identity_pending_is_not_malformed_accounting(tmp_path):
    paths, checkpoint = context(tmp_path)
    callback = _product_token_observer(paths, checkpoint, ProductTokenBudget())
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=UsageNotReady("not bound")):
        callback()
    assert not (tmp_path / "token-accounting-need.json").exists()
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=UsageUnavailable("malformed")):
        with pytest.raises(UsageUnavailable, match="malformed"):
            callback()
    assert (tmp_path / "token-accounting-need.json").exists()


def test_completed_turn_missing_usage_blocks_pending_proposal_until_exact_recovery(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget()
    callback = _product_token_observer(paths, checkpoint, budget)
    pending = observation(0)
    pending["threads"][0]["status"] = "pending"
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=pending):
        callback()
        with pytest.raises(UsageUnavailable, match="completed native turn"):
            callback.reconcile_completed_turn((100, None, None, 10, None))
        run = SimpleNamespace(snapshot=lambda: checkpoint)
        with mock.patch("workshop.workflow.native_run._load_lifetime_budget", return_value=budget), mock.patch(
            "workshop.workflow.native_run._session_status", return_value="checkpointed"
        ), mock.patch("workshop.workflow.native_run._prepare_stage_input") as prepare:
            with pytest.raises(UsageUnavailable, match="completed native turn"):
                _run_native_session(run, paths, launcher=None)
            prepare.assert_not_called()
    need = tmp_path / "token-accounting-need.json"
    assert need.is_file()
    loaded = _load_lifetime_budget(paths, checkpoint)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=observation(100)):
        _reconcile_token_accounting_need(paths, checkpoint, loaded)
    assert not need.exists()
    assert loaded.to_dict()["used_tokens"] == 110


def test_terminal_reconciliation_uses_current_root_delta_and_allows_canceled_child(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget()
    budget.observe(observation(500))
    callback = _product_token_observer(paths, checkpoint, budget)
    current = observation(600)
    current["threads"].append({"thread_id": CHILD, "tokens": counters(0), "status": "pending"})
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=current):
        callback.reconcile_completed_turn((100, None, None, 10, None))
    assert budget.to_dict()["used_tokens"] == 660
    assert budget.observation["threads"][-1]["status"] == "pending"
    assert not (tmp_path / "token-accounting-need.json").exists()


def test_reconciled_cap_stop_does_not_create_an_accounting_effect_blocker(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(1000)
    callback = _product_token_observer(paths, checkpoint, budget)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=observation(1000)):
        callback.reconcile_completed_turn((1000, None, None, 100, None))
        with pytest.raises(ContractError, match="token limit reached"):
            callback()
    assert budget.exhausted("release") == "run"
    assert not (tmp_path / "token-accounting-need.json").exists()


def test_known_terminal_expectation_survives_earlier_read_failure_and_retries(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget()
    callback = _product_token_observer(paths, checkpoint, budget)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=UsageUnavailable("bad snapshot")):
        with pytest.raises(UsageUnavailable):
            callback()
        with pytest.raises(UsageUnavailable):
            callback.reconcile_completed_turn((100, None, None, 10, None))
    need_path = tmp_path / "token-accounting-need.json"
    expected = json.loads(need_path.read_text())
    assert expected["completed_turn"] is True
    assert expected["terminal_usage"] == {"input_tokens": 100, "output_tokens": 10}
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=observation(50)):
        with pytest.raises(UsageUnavailable, match="completed native turn"):
            _reconcile_token_accounting_need(paths, checkpoint, budget)
    assert json.loads(need_path.read_text()) == expected
    expected["product_id"] = "another-wish"
    need_path.write_text(json.dumps(expected))
    with pytest.raises(StateConflict, match="binding"):
        _reconcile_token_accounting_need(paths, checkpoint, budget)


@pytest.mark.parametrize("command", [("wish", "a simple toy"), ("start", "ivy")])
def test_cli_default_and_explicit_configuration(command):
    assert parser().parse_args(command).max_tokens == 30000000
    assert parser().parse_args((*command, "--max-tokens", "10000000")).max_tokens == 10000000
    args = parser().parse_args((*command, "--workflow", "spark", "--agent", "codex",
                                "--model", "astra", "--effort", "medium", "--max-tokens", "2000000"))
    assert args.max_tokens == 2000000
    assert parser().parse_args((*command, "--max-tokens", "200000000")).max_tokens == 200000000
    assert parser().parse_args((*command, "--max-tokens", "500000000")).max_tokens == 500000000
    for value in ("0", "-1", "500000001", "1.5", "no"):
        with pytest.raises(SystemExit):
            parser().parse_args((*command, "--max-tokens", value))
    assert parser().parse_args(("resume", "wish-id")).max_tokens is None


def test_cli_resume_accepts_500_million_and_rejects_above_maximum():
    assert parser().parse_args(("resume", "wish-id", "--max-tokens", "500000000")).max_tokens == 500000000
    with pytest.raises(SystemExit):
        parser().parse_args(("resume", "wish-id", "--max-tokens", "500000001"))


@pytest.mark.parametrize("saved_limit", [10000000, 30000000, 100000000, 200000000, 500000000])
def test_new_default_does_not_change_persisted_run_limits(tmp_path, saved_limit):
    assert ProductTokenBudget().limit == 30000000
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(saved_limit)
    budget.observe(observation(200))
    _save_lifetime_budget(paths, checkpoint, budget)
    restored = _load_lifetime_budget(paths, checkpoint)
    assert restored.limit == saved_limit
    assert restored.to_dict()["used_tokens"] == 220


def test_large_compaction_preserves_ledger_and_token_cap(tmp_path):
    from workshop.runtime.codex_usage import MAX_LINE_BYTES

    paths, checkpoint = context(tmp_path / "state")
    paths.host_state.mkdir()
    sessions = tmp_path / "sessions"
    events = records() + [usage(500)]
    write(sessions, events)
    budget = ProductTokenBudget(1000)

    def read_usage(*_):
        return read_product_usage(sessions, thread_id=ROOT, workspace=Path("/toy"))

    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=read_usage):
        callback = _product_token_observer(paths, checkpoint, budget)
        callback()
        assert budget.to_dict()["used_tokens"] == 550
        events += [{"type": "compacted", "message": "x" * (MAX_LINE_BYTES + 1),
                    "replacement_history": [usage(999900)]}, usage(800)]
        write(sessions, events)
        callback()
        loaded = _load_lifetime_budget(paths, checkpoint)
        assert loaded.to_dict()["used_tokens"] == 880
        assert not (paths.host_state / "token-budget-stop.json").exists()

        callback = _product_token_observer(paths, checkpoint, loaded)
        write(sessions, events + [usage(1000)])
        with pytest.raises(ContractError, match="limit reached"):
            callback()
        assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 1100


def test_malformed_large_compaction_still_stops_host(tmp_path):
    from workshop.runtime.codex_usage import MAX_LINE_BYTES

    paths, checkpoint = context(tmp_path / "state")
    paths.host_state.mkdir()
    sessions = tmp_path / "sessions"
    path = write(sessions, records() + [usage(500)])
    budget = ProductTokenBudget(1000)

    def read_usage(*_):
        return read_product_usage(sessions, thread_id=ROOT, workspace=Path("/toy"))

    with mock.patch("workshop.workflow.native_run._read_product_token_usage", side_effect=read_usage):
        callback = _product_token_observer(paths, checkpoint, budget)
        callback()
        with path.open("ab") as stream:
            stream.write(b'{"type":"compacted","message":"' + b'x' * (MAX_LINE_BYTES + 1)
                         + b'","type":"compacted"}\n')
        with pytest.raises(UsageUnavailable):
            callback()
        assert (paths.host_state / "token-budget-stop.json").is_file()
        assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 550
