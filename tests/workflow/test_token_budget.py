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
from workshop.workflow.native_run import (
    _load_lifetime_budget, _save_lifetime_budget, _product_token_observer,
    _adopt_token_budget, _claude_token_observer, _meter_claude_turn,
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


@pytest.mark.parametrize("limit", [True, 999, 1000000001, 1000.0, "1000", None])
def test_invalid_limit(limit):
    with pytest.raises(ContractError):
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


def test_missing_ledger_is_not_reset(tmp_path):
    paths, checkpoint = context(tmp_path)
    with pytest.raises(StateConflict):
        _load_lifetime_budget(paths, checkpoint)


def test_cap_change_preserves_pending_child_and_later_charges_usage(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(1000)
    pending = observation(1000)
    pending["threads"].append({"thread_id": CHILD, "tokens": counters(0), "status": "pending"})
    budget.observe(pending)
    _save_lifetime_budget(paths, checkpoint, budget)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=pending):
        _adopt_token_budget(paths, checkpoint, 2000)
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert loaded.limit == 2000
    assert loaded.to_dict()["used_tokens"] == 1100
    assert loaded.observation == pending
    # A subsequently reported child remains charged to the same allowance.
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=observation(1000, child=True)):
        with pytest.raises(ContractError, match="limit reached"):
            _product_token_observer(paths, checkpoint, loaded)()
    assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 2200


def test_initial_token_adoption_still_refuses_pending_history(tmp_path):
    from workshop.workflow.budgets import LifetimeBudget

    paths, checkpoint = context(tmp_path)
    pending = observation(100)
    pending["threads"].append({"thread_id": CHILD, "tokens": counters(0), "status": "pending"})
    with mock.patch("workshop.workflow.native_run._load_lifetime_budget", return_value=LifetimeBudget()), mock.patch(
        "workshop.workflow.native_run._read_product_token_usage", return_value=pending
    ), mock.patch("workshop.workflow.native_run._save_lifetime_budget") as save:
        with pytest.raises(ContractError, match="unobserved native threads"):
            _adopt_token_budget(paths, checkpoint, 2000)
    save.assert_not_called()


@pytest.mark.parametrize("change", ["lost-child", "regression", "unavailable"])
def test_cap_change_with_pending_child_keeps_accounting_fail_closed(tmp_path, change):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget(1000)
    pending = observation(200)
    pending["threads"].append({"thread_id": CHILD, "tokens": counters(0), "status": "pending"})
    budget.observe(pending)
    _save_lifetime_budget(paths, checkpoint, budget)
    before = (tmp_path / "native-budget.json").read_bytes()
    recovered = copy.deepcopy(pending)
    if change == "lost-child":
        recovered["threads"].pop()
    elif change == "regression":
        recovered = observation(100)
        recovered["threads"].append(copy.deepcopy(pending["threads"][-1]))
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=recovered,
                    side_effect=UsageUnavailable("missing") if change == "unavailable" else None):
        with pytest.raises(ContractError):
            _adopt_token_budget(paths, checkpoint, 2000)
    assert (tmp_path / "native-budget.json").read_bytes() == before


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


def test_terminal_reconciliation_accepts_cumulative_root_counters_after_resume(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget()
    budget.observe(observation(500))
    callback = _product_token_observer(paths, checkpoint, budget)

    with mock.patch(
        "workshop.workflow.native_run._read_product_token_usage",
        return_value=observation(600),
    ):
        callback.reconcile_completed_turn((600, None, None, 60, None))

    assert budget.to_dict()["used_tokens"] == 660
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


@pytest.mark.parametrize("terminal,baseline,passes", [
    (300, 400, True), (299, 400, False), (301, 400, False), (300, 500, False),
])
def test_response_ledger_reconciles_exact_restored_terminal_snapshot(tmp_path, terminal, baseline, passes):
    from tests.runtime.test_codex_response_usage import completed_events

    sessions = tmp_path / "sessions"
    write(sessions, completed_events())
    current = read_product_usage(sessions, thread_id=ROOT, workspace=Path("/toy"))
    paths, checkpoint = context(tmp_path)
    budget = ProductTokenBudget()
    budget.observe(observation(baseline))
    callback = _product_token_observer(paths, checkpoint, budget)
    with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=current):
        if passes:
            callback.reconcile_completed_turn((terminal, None, None, 30, None))
            assert not (tmp_path / "token-accounting-need.json").exists()
        else:
            with pytest.raises(UsageUnavailable, match="completed native turn"):
                callback.reconcile_completed_turn((terminal, None, None, 30, None))
            assert (tmp_path / "token-accounting-need.json").exists()
    assert budget.to_dict()["used_tokens"] == 550


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
    for value in ("0", "-1", "1000000001", "1.5", "no"):
        with pytest.raises(SystemExit):
            parser().parse_args((*command, "--max-tokens", value))
    assert parser().parse_args(("resume", "wish-id")).max_tokens is None


@pytest.mark.parametrize("saved_limit", [10000000, 100000000, 200000000, 500000000, 1000000000])
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


@pytest.mark.parametrize("limit", [200_000_001, 500_000_000, 1_000_000_000])
def test_preserved_explicit_large_budget(limit):
    assert validate_limit(limit) == limit
    assert parser().parse_args(("resume", "wish-id", "--max-tokens", str(limit))).max_tokens == limit


def claude_counters(input_tokens, output_tokens=0):
    return {"input_tokens": input_tokens, "cached_input_tokens": 0,
            "cache_write_input_tokens": 0, "output_tokens": output_tokens,
            "reasoning_output_tokens": 0}


def claude_context(tmp_path):
    paths, checkpoint = context(tmp_path)
    checkpoint.manager_id = "claude"
    return paths, checkpoint


def test_claude_budget_exists_only_for_runs_created_with_it(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    assert _load_lifetime_budget(paths, checkpoint) is None
    assert not list(tmp_path.iterdir())
    created = _load_lifetime_budget(paths, checkpoint, initialize=True)
    assert isinstance(created, ProductTokenBudget)
    assert _load_lifetime_budget(paths, checkpoint).to_dict() == created.to_dict()


def test_fresh_claude_sessions_accumulate_and_survive_reload(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    first = _claude_token_observer(paths, checkpoint, budget)
    first(claude_counters(400), final=False, session_id="session-a")
    first(claude_counters(600, 50), final=True, session_id="session-a")
    budget = _load_lifetime_budget(paths, checkpoint)
    second = _claude_token_observer(paths, checkpoint, budget)
    second(claude_counters(300, 10), final=True, session_id="session-b")
    loaded = _load_lifetime_budget(paths, checkpoint)
    value = loaded.to_dict()
    assert value["used_tokens"] == 960
    assert value["observation"]["source"] == "claude-native-stream-v1"
    assert [t["thread_id"] for t in value["observation"]["threads"]] == [
        "claude-invocation-000001", "claude-invocation-000002",
    ]
    assert value["observation"]["root_thread_id"] == "claude-invocation-000001"
    assert [(t["session_id"], t["invocations"]) for t in value["observation"]["threads"]] == [
        ("session-a", 1), ("session-b", 1),
    ]


def _claude_stream_launcher(streams):
    from tests.runtime.test_claude_native_session import _FakeProcess
    from workshop.runtime.claude import ClaudeNativeSessionLauncher
    remaining = [list(lines) for lines in streams]
    return ClaudeNativeSessionLauncher(
        binary="/bin/claude", cli_version="2.1.285",
        popen_factory=lambda command, **kwargs: _FakeProcess(remaining.pop(0)),
        uuid_factory=lambda: "initial-session-id",
    )


def _claude_turn(launcher, method, root):
    return getattr(launcher, method)(
        product_id="wish-one", wish_sha256="d" * 64, constitution_sha256="d" * 64,
        run_root=root / "run", host_state_root=root / "claude", prompt="make",
    )


def test_a_resumed_claude_session_is_charged_once(tmp_path):
    """Issue #84: a resume's result totals the whole session, so invocation 2
    replaces the session's charge (N + k) instead of adding to it (2N + k)."""
    from tests.runtime.test_claude_native_session import (
        OPUS_TOTALS, PER_BLOCK_USAGE, SESSION, _assistant_line, _init_line, _result_line,
    )
    for directory in ("run", "claude", "state"):
        (tmp_path / directory).mkdir(mode=0o700)
    paths, checkpoint = claude_context(tmp_path / "state")
    request = 2 + 13_227 + 10_010
    n_cached, n_write = 16_000_000, 300_000
    n_input = 100 + n_cached + n_write
    first_totals = {**OPUS_TOTALS, "inputTokens": 100, "cacheReadInputTokens": n_cached,
                    "cacheCreationInputTokens": n_write, "outputTokens": 9_000,
                    "thinkingTokens": 0}
    # Invocation 2 streams one request and ends with the session-wide total.
    second_totals = {**first_totals, "inputTokens": 102,
                     "cacheReadInputTokens": n_cached + 10_010,
                     "cacheCreationInputTokens": n_write + 13_227,
                     "outputTokens": 9_000 + 168}
    launcher = _claude_stream_launcher([
        [_init_line(), _assistant_line("msg_1", PER_BLOCK_USAGE), _assistant_line("msg_2", PER_BLOCK_USAGE),
         _result_line({"claude-opus-5": first_totals})],
        [_init_line(), _assistant_line("msg_3", PER_BLOCK_USAGE),
         _result_line({"claude-opus-5": second_totals})],
    ])
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    budget.limit = 100_000_000
    _meter_claude_turn(paths, checkpoint, launcher, budget)
    _claude_turn(launcher, "start", tmp_path)
    first = _load_lifetime_budget(paths, checkpoint).to_dict()
    n = n_input + 9_000
    assert first["used_tokens"] == n
    budget = _load_lifetime_budget(paths, checkpoint)
    _meter_claude_turn(paths, checkpoint, launcher, budget)
    _claude_turn(launcher, "resume", tmp_path)
    value = _load_lifetime_budget(paths, checkpoint).to_dict()
    assert value["used_tokens"] == n + request + 168
    (thread,) = value["observation"]["threads"]
    assert (thread["thread_id"], thread["session_id"], thread["invocations"]) == (
        "claude-invocation-000001", SESSION, 2,
    )


def test_a_resumed_session_charges_streamed_requests_before_its_result(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    _claude_token_observer(paths, checkpoint, budget)(
        claude_counters(1_000, 100), final=True, session_id="session-a")
    resumed = _claude_token_observer(paths, checkpoint, budget)
    resumed(claude_counters(40, 4), final=False, session_id="session-a",
            streamed=claude_counters(40, 4))
    assert budget.to_dict()["used_tokens"] == 1_144
    resumed(claude_counters(1_050, 106), final=True, session_id="session-a",
            streamed=claude_counters(40, 4))
    assert budget.to_dict()["used_tokens"] == 1_156


def test_a_resume_reporting_less_never_lowers_the_session_charge(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    _claude_token_observer(paths, checkpoint, budget)(
        claude_counters(1_000, 100), final=True, session_id="session-a")
    _claude_token_observer(paths, checkpoint, budget)(
        claude_counters(300, 10), final=True, session_id="session-a",
        streamed=claude_counters(0))
    value = _load_lifetime_budget(paths, checkpoint).to_dict()
    assert value["used_tokens"] == 1_100
    assert value["observation"]["threads"][0]["invocations"] == 2


def test_a_resume_of_an_earlier_session_replaces_only_that_session(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    _claude_token_observer(paths, checkpoint, budget)(claude_counters(1_000), final=True, session_id="a")
    _claude_token_observer(paths, checkpoint, budget)(claude_counters(500), final=True, session_id="b")
    _claude_token_observer(paths, checkpoint, budget)(
        claude_counters(1_200), final=True, session_id="a", streamed=claude_counters(200))
    threads = _load_lifetime_budget(paths, checkpoint).to_dict()["observation"]["threads"]
    assert [(t["thread_id"], t["tokens"]["input_tokens"], t["invocations"]) for t in threads] == [
        ("claude-invocation-000001", 1_200, 2), ("claude-invocation-000002", 500, 1),
    ]


def test_a_frozen_ledger_with_duplicated_threads_keeps_its_recorded_value(tmp_path):
    """Threads recorded before sessions were named are never rewritten."""
    paths, checkpoint = claude_context(tmp_path)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    legacy = {"thread_id": "claude-invocation-000001", "status": "observed",
              "tokens": claude_counters(1_000, 100)}
    budget.observe({
        "schema_version": 1, "source": "claude-native-stream-v1", "status": "observed",
        "root_thread_id": "claude-invocation-000001",
        "threads": [legacy, {**legacy, "thread_id": "claude-invocation-000002"}],
        "tokens": claude_counters(2_000, 200), "total_tokens": 2_200,
    })
    _save_lifetime_budget(paths, checkpoint, budget)
    assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 2_200
    budget = _load_lifetime_budget(paths, checkpoint)
    _claude_token_observer(paths, checkpoint, budget)(
        claude_counters(1_010, 101), final=True, session_id="session-a",
        streamed=claude_counters(10, 1))
    value = _load_lifetime_budget(paths, checkpoint).to_dict()
    assert value["used_tokens"] == 2_200 + 1_111
    assert [t.get("session_id") for t in value["observation"]["threads"]] == [None, None, "session-a"]


def test_claude_observer_stops_at_the_cap_and_records_why(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    budget = ProductTokenBudget(1000)
    _save_lifetime_budget(paths, checkpoint, budget)
    observe = _claude_token_observer(paths, checkpoint, budget)
    observe(claude_counters(900), final=False)
    with pytest.raises(ContractError, match="product token limit reached"):
        observe(claude_counters(1000), final=False)
    stop = json.loads((tmp_path / "token-budget-stop.json").read_text())
    assert stop["reason"] == "product token limit reached"
    assert _load_lifetime_budget(paths, checkpoint).to_dict()["used_tokens"] == 1000


def test_claude_observer_refuses_regressing_usage(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    budget = ProductTokenBudget(10_000)
    observe = _claude_token_observer(paths, checkpoint, budget)
    observe(claude_counters(900), final=False)
    with pytest.raises(ContractError, match="lost prior usage"):
        observe(claude_counters(800), final=False)
    stop = json.loads((tmp_path / "token-budget-stop.json").read_text())
    assert stop["reason"] == "native token usage unavailable or inconsistent"


def test_a_ledger_never_switches_between_codex_and_claude_accounting(tmp_path):
    budget = ProductTokenBudget(10_000)
    budget.observe(observation(100))
    paths, checkpoint = claude_context(tmp_path)
    with pytest.raises(ContractError, match="source changed"):
        _claude_token_observer(paths, checkpoint, budget)(claude_counters(1), final=True)


def test_claude_resume_moves_only_the_limit(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    budget = ProductTokenBudget(1000)
    _save_lifetime_budget(paths, checkpoint, budget)
    _claude_token_observer(paths, checkpoint, budget)(claude_counters(900), final=True)
    _adopt_token_budget(paths, checkpoint, 5000)
    loaded = _load_lifetime_budget(paths, checkpoint)
    assert (loaded.limit, loaded.to_dict()["used_tokens"]) == (5000, 900)


def test_an_unbudgeted_claude_run_cannot_adopt_a_cap_on_resume(tmp_path):
    paths, checkpoint = claude_context(tmp_path)
    with pytest.raises(ContractError, match="lacks a supported persistent budget"):
        _adopt_token_budget(paths, checkpoint, 5000)


@pytest.mark.parametrize("turn_seconds, expected", [(None, None), (21_600, 21_600)])
def test_a_metered_claude_turn_has_no_default_wall_clock(tmp_path, turn_seconds, expected):
    from workshop.runtime.claude import ClaudeNativeSessionLauncher
    paths, checkpoint = claude_context(tmp_path)
    checkpoint.turn_seconds = turn_seconds
    checkpoint.turn_untimed = False
    launcher = ClaudeNativeSessionLauncher(
        binary="/bin/claude", cli_version="2.1.285",
        **({} if turn_seconds is None else {"timeout_seconds": turn_seconds}),
    )
    _meter_claude_turn(paths, checkpoint, launcher, ProductTokenBudget(1000))
    assert launcher.timeout_seconds == expected
    assert launcher.token_budget_observer is not None
