"""A long motion run must say how far it has got, on stderr, without
disturbing the stdout contract or the verdict."""
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
PROGRESS = runpy.run_path(str(TOOLS / "progresslib.py"))


@pytest.fixture(autouse=True)
def _default_progress_env(monkeypatch):
    monkeypatch.delenv("WORKSHOP_PROGRESS", raising=False)
    monkeypatch.setenv("WORKSHOP_PROGRESS_INTERVAL", "0")


def test_counter_reports_position_elapsed_and_estimate(capsys):
    reporter = PROGRESS["Progress"]("sweep", 4)
    for _ in range(4):
        reporter.advance()
    reporter.finish()
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert lines[0] == "sweep: 4 to go"
    assert "sweep: 1/4 (25%)" in lines[1] and "elapsed" in lines[1] and "left" in lines[1]
    assert "sweep: 4/4 (100%)" in lines[4]
    assert lines[5].startswith("sweep: 4 done in ")


def test_last_item_always_reports_even_when_throttled(monkeypatch, capsys):
    monkeypatch.setenv("WORKSHOP_PROGRESS_INTERVAL", "3600")
    reporter = PROGRESS["Progress"]("sweep", 3)
    for _ in range(3):
        reporter.advance()
    lines = capsys.readouterr().err.splitlines()
    assert [line for line in lines if "3/3" in line]
    assert len(lines) == 3  # opening, first item, last item -- nothing in between


def test_scope_names_the_condition_a_nested_loop_belongs_to(capsys):
    with PROGRESS["scope"]("rocker"):
        PROGRESS["write"]("coupled sweep: started")
    PROGRESS["write"]("unscoped")
    assert capsys.readouterr().err.splitlines() == ["[rocker] coupled sweep: started", "unscoped"]


def test_progress_can_be_silenced(monkeypatch, capsys):
    monkeypatch.setenv("WORKSHOP_PROGRESS", "0")
    PROGRESS["Progress"]("sweep", 2).advance()
    with PROGRESS["phase"]("building"):
        pass
    assert capsys.readouterr().err == ""


def test_phase_reports_start_and_duration_including_failures(capsys):
    with pytest.raises(ValueError):
        with PROGRESS["phase"]("building model.step.py"):
            raise ValueError("boom")
    lines = capsys.readouterr().err.splitlines()
    assert lines[0] == "building model.step.py ..."
    assert lines[1].startswith("building model.step.py failed after ")


def test_durations_stay_readable_past_a_minute_and_an_hour():
    assert PROGRESS["duration"](0.4) == "0s"
    assert PROGRESS["duration"](95) == "1m35s"
    assert PROGRESS["duration"](3725) == "1h02m"


def _project(tmp_path):
    (tmp_path / "measure").mkdir()
    (tmp_path / "model.step.py").write_text('''from build123d import Box, Compound
def gen_step():
    driver = Box(2, 1, 1).translate((4, 0, 0))
    driver.label = "driver"
    frame = Box(2, 2, 1).translate((0, 0, -3))
    frame.label = "frame"
    return Compound(children=[driver, frame], label="root")
''')
    (tmp_path / "measure/motion.json").write_text(json.dumps({
        "assembly": "model.step.py",
        "conditions": [{"id": "turn", "check": "rotation_motion_collision", "inputs": {
            "moving_part": "driver", "obstacle_parts": ["frame"], "steps": 4,
            "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
            "start_deg": 0, "end_deg": 90}}]}))
    return tmp_path


def test_check_motion_counts_its_conditions_on_stderr_only(tmp_path):
    project = _project(tmp_path)
    run = subprocess.run(
        [sys.executable, str(TOOLS / "check_motion"), str(project),
         "--manifest", str(project / "measure/motion.json"), "--json"],
        capture_output=True, text=True,
        env={**os.environ, "WORKSHOP_PROGRESS_INTERVAL": "0"})
    assert run.returncode == 0, run.stderr
    assert json.loads(run.stdout)["ok"] is True  # stdout stays a clean contract
    assert "building model.step.py ..." in run.stderr
    assert "check_motion condition 1/1: turn [rotation_motion_collision]" in run.stderr
    assert "[turn] sweep: 5/5 (100%)" in run.stderr


def test_progress_does_not_change_the_verdict(tmp_path):
    project = _project(tmp_path)
    command = [sys.executable, str(TOOLS / "check_motion"), str(project),
               "--manifest", str(project / "measure/motion.json"), "--json"]
    loud = subprocess.run(command, capture_output=True, text=True,
                          env={**os.environ, "WORKSHOP_PROGRESS": "1"})
    quiet = subprocess.run(command, capture_output=True, text=True,
                           env={**os.environ, "WORKSHOP_PROGRESS": "0"})
    assert loud.stdout == quiet.stdout
    assert loud.returncode == quiet.returncode == 0
    assert quiet.stderr == ""
