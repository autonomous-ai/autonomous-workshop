import copy
import json
from types import SimpleNamespace
from unittest import mock

import pytest

from workshop.errors import ContractError, StateConflict
from workshop.workflow.budgets import (
    LifetimeTurnBudget, TURN_BUDGETS_CAPABILITY_PATH,
    LIFETIME_BUDGETS_CAPABILITY_PATH,
)
from workshop.workflow.native_run import (
    _load_lifetime_budget, _save_lifetime_budget, _adopt_turn_budget,
)


def context(tmp_path, *, legacy=False):
    capability = LIFETIME_BUDGETS_CAPABILITY_PATH if legacy else TURN_BUDGETS_CAPABILITY_PATH
    return SimpleNamespace(host_state=tmp_path), SimpleNamespace(
        manager_id="codex", product_id="test", wish_sha256="a" * 64,
        input_sha256s={capability: "b" * 64}, checkpoint_sha256="c" * 64,
        stage="make", status="active",
    )


def test_turns_survive_crash_resume_and_stage_revisits(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    for _ in range(6):
        budget.reserve("make", 1200)
        _save_lifetime_budget(paths, checkpoint, budget)
        budget = _load_lifetime_budget(paths, checkpoint)
        budget.settle("make", 1200, 0)  # Neither instant error nor zero time refunds.
    assert budget.exhausted("make") == "step"
    assert budget.exhausted("release") is None
    with pytest.raises(ContractError):
        budget.reserve("make", 1200)
    for _ in range(6):
        budget.reserve("release", 1200)
    assert budget.exhausted("invent") == "run"
    assert budget.to_dict()["run"]["used_turns"] == 12


@pytest.mark.parametrize("mutation", [
    lambda b: b["run"].update(used_turns=True),
    lambda b: b["run"].update(used_turns=2),
    lambda b: b["steps"]["make"].update(used_turns=-1),
    lambda b: b["steps"]["make"].update(limit_turns=6.0),
    lambda b: b["steps"].update(other={"used_turns": 1, "limit_turns": 6}),
    lambda b: b.update(unit="seconds"),
])
def test_corrupt_turn_accounting_fails_closed(mutation):
    budget = LifetimeTurnBudget()
    budget.reserve("make", 1200)
    value = copy.deepcopy(budget.to_dict())
    mutation(value)
    with pytest.raises(ContractError):
        budget.restore(value)


def test_missing_resume_record_never_creates_fresh_turns(tmp_path):
    paths, checkpoint = context(tmp_path)
    with pytest.raises(StateConflict):
        _load_lifetime_budget(paths, checkpoint)


def test_explicit_adoption_preserves_previous_time_and_turns(tmp_path):
    paths, checkpoint = context(tmp_path, legacy=True)
    old = _load_lifetime_budget(paths, checkpoint, initialize=True)
    old.reserve("make", 2400)
    _save_lifetime_budget(paths, checkpoint, old)
    previous = old.to_dict()
    progress = SimpleNamespace(native_turns=2, stage_attempt=2)
    with mock.patch("workshop.workflow.native_run.trusted_native_progress", return_value=progress), mock.patch(
        "workshop.workflow.native_run.native_progress_turn_floor", return_value=2
    ):
        _adopt_turn_budget(paths, checkpoint)
        budget = _load_lifetime_budget(paths, checkpoint)
        assert budget.to_dict()["steps"]["make"]["used_turns"] == 2
        assert budget.previous_time_budget == previous
        budget.reserve("make", 1200)
        _save_lifetime_budget(paths, checkpoint, budget)
        _adopt_turn_budget(paths, checkpoint)
        assert _load_lifetime_budget(paths, checkpoint).to_dict()["run"]["used_turns"] == 3


@pytest.mark.parametrize("progress,floor", [
    (None, 2),
    (SimpleNamespace(native_turns=2, stage_attempt=1), 2),
    (SimpleNamespace(native_turns=2, stage_attempt=2), 3),
])
def test_ambiguous_migration_refuses_without_overwriting(tmp_path, progress, floor):
    paths, checkpoint = context(tmp_path, legacy=True)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    budget.reserve("make", 1200)
    _save_lifetime_budget(paths, checkpoint, budget)
    original = (tmp_path / "native-budget.json").read_bytes()
    with mock.patch("workshop.workflow.native_run.trusted_native_progress", return_value=progress), mock.patch(
        "workshop.workflow.native_run.native_progress_turn_floor", return_value=floor
    ), pytest.raises(StateConflict):
        _adopt_turn_budget(paths, checkpoint)
    assert (tmp_path / "native-budget.json").read_bytes() == original


def test_migration_record_requires_prior_accounting(tmp_path):
    paths, checkpoint = context(tmp_path, legacy=True)
    _save_lifetime_budget(paths, checkpoint, LifetimeTurnBudget())
    with pytest.raises(StateConflict, match="prior accounting"):
        _load_lifetime_budget(paths, checkpoint)
