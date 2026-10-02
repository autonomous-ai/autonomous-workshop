"""Explicit geometry allowances survive the Make command wrapper."""
from pathlib import Path
import runpy
import subprocess
import sys
from unittest.mock import Mock

import pytest


TOOL = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/make-round/scripts/make_round"


@pytest.fixture
def runner(monkeypatch):
    run = runpy.run_path(str(TOOL))["run"]
    monkeypatch.delenv("WORKSHOP_GEOMETRY_OPERATION_TIMEOUT", raising=False)
    monkeypatch.setenv("WORKSHOP_GEOMETRY_TIMEOUT", "86400")
    return run


@pytest.mark.parametrize("override,expected", [(None, 900), ("86400", 86400), ("60", 60)])
def test_geometry_operation_override_replaces_only_default_command_cap(runner, monkeypatch, tmp_path, override, expected):
    if override is not None:
        monkeypatch.setenv("WORKSHOP_GEOMETRY_OPERATION_TIMEOUT", override)
    child = Mock(returncode=0)
    child.communicate.return_value = ("{}", "")
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=child))
    monkeypatch.setattr(runner.__globals__["time"], "monotonic", lambda: 100.0)
    runner([sys.executable, "check_motion"], cwd=tmp_path, log=tmp_path / "motion.log")
    child.communicate.assert_called_once_with(timeout=expected)


def test_shared_remaining_budget_still_limits_override(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSHOP_GEOMETRY_OPERATION_TIMEOUT", "86400")
    runner.__globals__["_GEOMETRY_DEADLINES"][str(tmp_path)] = 125.0
    monkeypatch.setattr(runner.__globals__["time"], "monotonic", lambda: 100.0)
    child = Mock(returncode=0)
    child.communicate.return_value = ("{}", "")
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=child))
    runner([sys.executable, "check_motion"], cwd=tmp_path, log=tmp_path / "motion.log")
    child.communicate.assert_called_once_with(timeout=25.0)


@pytest.mark.parametrize("value", ["nan", "inf", "0", "-1", "86401", "invalid"])
def test_invalid_override_never_starts_geometry(runner, monkeypatch, tmp_path, value):
    monkeypatch.setenv("WORKSHOP_GEOMETRY_OPERATION_TIMEOUT", value)
    launch = Mock()
    monkeypatch.setattr(subprocess, "Popen", launch)
    with pytest.raises(ValueError):
        runner([sys.executable, "check_motion"], cwd=tmp_path, log=tmp_path / "motion.log")
    launch.assert_not_called()


def test_non_geometry_command_keeps_explicit_timeout(runner, monkeypatch, tmp_path):
    monkeypatch.setenv("WORKSHOP_GEOMETRY_OPERATION_TIMEOUT", "86400")
    child = Mock(returncode=0)
    child.communicate.return_value = ("", "")
    monkeypatch.setattr(subprocess, "Popen", Mock(return_value=child))
    runner([sys.executable, "gen"], cwd=tmp_path, log=tmp_path / "gen.log", timeout=42)
    child.communicate.assert_called_once_with(timeout=42)


@pytest.mark.parametrize("measured_failure", [False, True])
def test_operation_expiry_preserves_unverified_and_prior_failure(runner, monkeypatch, tmp_path, measured_failure):
    monkeypatch.setenv("WORKSHOP_GEOMETRY_OPERATION_TIMEOUT", ".15")
    tool = tmp_path / "check_motion"
    tool.write_text("import os,time\n" + (
        "os.write(int(os.environ['WORKSHOP_GEOMETRY_FAILURE_FD']), b'1')\n"
        if measured_failure else "") + "time.sleep(20)\n")
    result = runner([sys.executable, str(tool)], cwd=tmp_path, log=tmp_path / "motion.log")
    assert result.returncode == (124 if measured_failure else 3)

