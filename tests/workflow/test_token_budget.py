import copy
from types import SimpleNamespace
from unittest import mock

import pytest

from cli.main import parser
from workshop.errors import ContractError, StateConflict
from workshop.runtime.codex_usage import UsageUnavailable
from workshop.workflow.native_run import (
    _load_lifetime_budget, _save_lifetime_budget, _product_token_observer,
    _adopt_token_budget,
)
from workshop.workflow.token_budget import (
    ProductTokenBudget, TOKEN_BUDGET_CAPABILITY_PATH, validate_limit,
)
from tests.runtime.test_codex_usage import ROOT, CHILD, counters


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


@pytest.mark.parametrize("limit", [True, 999, 100000001, 1000.0, "1000", None])
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


def test_pending_child_has_bounded_grace(tmp_path):
    paths, checkpoint = context(tmp_path)
    value = observation(100)
    value["threads"].append({"thread_id": CHILD, "tokens": counters(0), "status": "pending"})
    with mock.patch("workshop.workflow.native_run.time.monotonic", return_value=0) as clock:
        callback = _product_token_observer(paths, checkpoint, ProductTokenBudget())
        with mock.patch("workshop.workflow.native_run._read_product_token_usage", return_value=value):
            callback()
            clock.return_value = 181
            with pytest.raises(UsageUnavailable, match="startup grace"):
                callback()


@pytest.mark.parametrize("command", [("wish", "a simple toy"), ("start", "ivy")])
def test_cli_default_and_explicit_configuration(command):
    assert parser().parse_args(command).max_tokens == 10000000
    args = parser().parse_args((*command, "--workflow", "spark", "--agent", "codex",
                                "--model", "astra", "--effort", "medium", "--max-tokens", "2000000"))
    assert args.max_tokens == 2000000
    for value in ("0", "-1", "100000001", "1.5", "no"):
        with pytest.raises(SystemExit):
            parser().parse_args((*command, "--max-tokens", value))
    assert parser().parse_args(("resume", "wish-id")).max_tokens is None
