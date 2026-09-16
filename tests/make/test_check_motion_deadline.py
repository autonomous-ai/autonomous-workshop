"""A motion sweep that cannot finish must stop and say so, never run forever.

A cut-off sweep measured nothing past its stopping point. It returns the
explicit unverified exit (3), never PASS, even with --allow-inconclusive. The
Workshop verifier can continue only with the corresponding final disclosure.
"""
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
MOTION = runpy.run_path(str(TOOLS / "check_motion"))
VERIFY = runpy.run_path(str(TOOLS / "verify_project"))

SLOW_STEPS = 400


def _project(tmp_path, steps=SLOW_STEPS):
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
            "moving_part": "driver", "obstacle_parts": ["frame"], "steps": steps,
            "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
            "start_deg": 0, "end_deg": 90}}]}))
    return tmp_path


def _run(project, *extra):
    return subprocess.run(
        [sys.executable, str(TOOLS / "check_motion"), str(project),
         "--manifest", str(project / "measure/motion.json"), *extra],
        capture_output=True, text=True,
        env={**os.environ, "WORKSHOP_PROGRESS": "0"})


def test_flag_beats_environment_and_zero_means_unbounded():
    resolve = MOTION["resolve_deadline"]
    assert resolve(30.0, "900") == 30.0
    assert resolve(None, "900") == 900.0
    assert resolve(None, "  ") is None
    assert resolve(None, None) is None
    assert resolve(None, "0") is None  # explicit opt-out, not an error
    assert resolve(0.0, "900") is None


@pytest.mark.parametrize("value", ["-1", "nan", "later"])
def test_an_unusable_budget_is_a_usage_error_not_a_silent_unbounded_run(value):
    with pytest.raises(ValueError):
        MOTION["resolve_deadline"](None, value)


def test_projected_cost_counts_pairs_obstacles_and_nested_steps():
    estimate = MOTION["estimate_samples"]
    assert estimate([{"check": "rotation_motion_collision",
                      "inputs": {"steps": 9, "obstacle_parts": ["a", "b"]}}]) == 20
    coupled = [{"check": "coupled_motion_collision", "inputs": {
        "steps": 3, "obstacle_parts": ["frame"],
        "movers": [{"part": "a"}, {"part": "b", "driven": True}]}}]
    # 4 samples x (1 mover pair + 2 movers against 1 obstacle), plus two
    # witness sweeps over the table for the one driven part.
    assert estimate(coupled) == 4 * 3 + 2 * 1 * 1 * 4
    assert estimate([{"check": "assembly_sequence", "inputs": {"steps": coupled}}]) == estimate(coupled)
    assert estimate([{"check": "coupled_motion_collision", "inputs": {"steps": "many"}}]) == 0


def test_a_budget_stop_is_inconclusive_with_an_unverified_exit(tmp_path):
    run = _run(_project(tmp_path), "--deadline", "0.01", "--json")
    payload = json.loads(run.stdout)
    assert run.returncode == 3
    assert payload["ok"] is False
    assert payload["deadlineSeconds"] == 0.01
    result = payload["results"][0]
    assert result["status"] == "inconclusive"
    assert result["deadlineStopped"] is True
    assert "do not read this as clear" in result["detail"]
    assert f"/{SLOW_STEPS + 1} sampled pose(s)" in result["detail"]


def test_allow_inconclusive_does_not_absolve_a_budget_stop(tmp_path):
    run = _run(_project(tmp_path), "--deadline", "0.01", "--allow-inconclusive")
    assert run.returncode == 3
    assert "never finished" in run.stderr


def test_an_unbounded_run_is_still_the_default_and_still_passes(tmp_path):
    run = _run(_project(tmp_path, steps=8))
    assert run.returncode == 0, run.stderr
    assert "1 condition(s) clear" in run.stdout
    assert "budget" not in run.stderr


def test_the_projection_is_printed_before_the_first_sweep(tmp_path):
    project = _project(tmp_path, steps=8)
    run = subprocess.run(  # the projection is progress, so it follows WORKSHOP_PROGRESS
        [sys.executable, str(TOOLS / "check_motion"), str(project),
         "--manifest", str(project / "measure/motion.json")],
        capture_output=True, text=True, env={**os.environ, "WORKSHOP_PROGRESS": "1"})
    head = run.stderr.splitlines()
    assert "up to ~9 sampled Boolean/distance operations" in "\n".join(head)
    assert head.index(next(l for l in head if "up to ~9" in l)) < head.index(
        next(l for l in head if "sweep:" in l))


def test_a_presentation_that_cannot_finish_writes_nothing_and_says_where_it_stopped(tmp_path):
    """The animation is the other multi-hour motion job, and it has nothing on
    disk until both halves finish."""
    project = _project(tmp_path, steps=8)
    project.joinpath("measure/motion.json").write_text(json.dumps({
        "assembly": "model.step.py",
        "conditions": [{"id": "turn", "check": "coupled_motion_collision", "inputs": {
            "steps": 8, "obstacle_parts": ["frame"],
            "movers": [{"part": "driver", "rotation": {
                "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
                "start_deg": 0, "end_deg": 90}}]}}]}))
    run = subprocess.run(
        [sys.executable, str(TOOLS / "motion_presentation.py"), str(project),
         "--size", "256", "--deadline", "0.01"],
        capture_output=True, text=True, env={**os.environ, "WORKSHOP_PROGRESS": "0"})
    assert run.returncode == 2
    assert "stopped at its 0.01s budget" in run.stderr
    assert "posed sample(s)" in run.stderr
    assert not (project / "snap").exists()


def test_presentation_deadline_resolution_matches_the_gate(tmp_path):
    resolve = runpy.run_path(str(TOOLS / "motion_presentation.py"))["resolve_deadline"]
    assert resolve(30.0, "900") == 30.0
    assert resolve(None, "900") == 900.0
    assert resolve(None, "0") is None
    assert resolve(None, None) is None
    with pytest.raises(ValueError):
        resolve(None, "soon")


def test_verify_project_bounds_the_motion_gate_by_default(monkeypatch):
    monkeypatch.delenv(VERIFY["MOTION_DEADLINE_ENV"], raising=False)
    assert VERIFY["_motion_deadline_seconds"]() == VERIFY["DEFAULT_MOTION_DEADLINE_SECONDS"]
    monkeypatch.setenv(VERIFY["MOTION_DEADLINE_ENV"], "120")
    assert VERIFY["_motion_deadline_seconds"]() == 120.0
    monkeypatch.setenv(VERIFY["MOTION_DEADLINE_ENV"], "0")
    assert VERIFY["_motion_deadline_seconds"]() == 0.0  # opt out of the bound
    monkeypatch.setenv(VERIFY["MOTION_DEADLINE_ENV"], "soon")
    assert VERIFY["_motion_deadline_seconds"]() == VERIFY["DEFAULT_MOTION_DEADLINE_SECONDS"]
