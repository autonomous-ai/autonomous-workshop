import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from workshop.errors import StateConflict
from workshop.workflow.budgets import LIFETIME_BUDGETS_CAPABILITY_PATH
from workshop.workflow.native_run import _load_lifetime_budget, _save_lifetime_budget


def context(tmp_path):
    return (SimpleNamespace(host_state=tmp_path), SimpleNamespace(manager_id="codex", product_id="test", wish_sha256="a" * 64, input_sha256s={LIFETIME_BUDGETS_CAPABILITY_PATH: "b" * 64}))


def test_saved_reservation_survives_resume_and_crash(tmp_path):
    paths, checkpoint = context(tmp_path)
    budget = _load_lifetime_budget(paths, checkpoint, initialize=True)
    budget.reserve("make", 1200)
    _save_lifetime_budget(paths, checkpoint, budget)
    restored = _load_lifetime_budget(paths, checkpoint, initialize=True)
    assert restored.spent_total == 1200
    assert _load_lifetime_budget(paths, checkpoint).remaining("make") == 1200
    assert (tmp_path / "native-budget.json").stat().st_mode & 0o777 == 0o600


def test_missing_resume_record_fails_closed(tmp_path):
    paths, checkpoint = context(tmp_path)
    with pytest.raises(StateConflict):
        _load_lifetime_budget(paths, checkpoint)


@pytest.mark.parametrize("field", ["product_id", "wish_sha256", "capability_sha256"])
def test_rebound_record_fails_closed(tmp_path, field):
    paths, checkpoint = context(tmp_path)
    _load_lifetime_budget(paths, checkpoint, initialize=True)
    path = tmp_path / "native-budget.json"
    data = json.loads(path.read_bytes())
    data[field] = "wrong"
    path.write_text(json.dumps(data))
    with pytest.raises(StateConflict):
        _load_lifetime_budget(paths, checkpoint)


def test_legacy_run_does_not_acquire_budget(tmp_path):
    paths, checkpoint = context(tmp_path)
    checkpoint.input_sha256s = {}
    assert _load_lifetime_budget(paths, checkpoint, initialize=True) is None
    assert not list(tmp_path.iterdir())


def test_other_adapter_does_not_claim_an_unenforced_budget(tmp_path):
    paths, checkpoint = context(tmp_path)
    checkpoint.manager_id = "claude"
    assert _load_lifetime_budget(paths, checkpoint, initialize=True) is None
    assert not list(tmp_path.iterdir())
