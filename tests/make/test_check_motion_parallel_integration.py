"""The process sweep preserves coupled-motion gate results and drive evidence."""
from copy import deepcopy
from pathlib import Path
import runpy

from build123d import Box
import pytest


TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


@pytest.fixture
def motion(monkeypatch):
    monkeypatch.syspath_prepend(str(TOOLS))
    monkeypatch.setenv("WORKSHOP_MOTION_WORKERS", "1")
    return runpy.run_path(str(TOOLS / "check_motion"))


def fixture(offsets=(0, 1, 2, 3, 2, 1), gap=1, driven=True):
    parts = {"input": Box(1, 1, 1), "output": Box(1, 1, 1).translate((gap, 0, 0))}
    condition = {
        "id": "coast", "check": "coupled_motion_collision", "expect": "clear",
        "inputs": {"steps": len(offsets) - 1, "obstacle_parts": [], "movers": [
            {"part": name, "driven": driven and name == "output",
             "translation": {"offsets_mm": [[x, 0, 0] for x in offsets]}}
            for name in parts]},
        "thresholds": {"maxOverlapMm3": .001, "maxStepMm": 2.0},
    }
    return parts, condition


def compare(motion, monkeypatch, parts, condition):
    monkeypatch.setenv("WORKSHOP_MOTION_WORKERS", "1")
    serial = motion["run_condition"](deepcopy(condition), parts, 0)
    monkeypatch.setenv("WORKSHOP_MOTION_WORKERS", "2")
    parallel = motion["run_condition"](deepcopy(condition), parts, 0)
    assert parallel == serial
    return parallel


@pytest.mark.parametrize("gap,expected", [(1, "pass"), (2, "fail")])
def test_real_geometry_full_drive_evidence_matches_serial(motion, monkeypatch, gap, expected):
    result = compare(motion, monkeypatch, *fixture(gap=gap))
    assert result["status"] == expected
    assert result["clear"]
    assert result["driveContactEvidencePassed"] == (expected == "pass")
    if expected == "pass":
        edge, = result["driveEvidence"]["edges"]
        assert edge["frozenWitness"]["step"] == 1
        assert edge["nominalWitness"]["step"] == 0


@pytest.mark.parametrize("allow_seated,expected_step", [(False, 0), (True, 4)])
def test_first_collision_preserves_original_indices_and_obstacle_order(motion, monkeypatch, allow_seated, expected_step):
    parts, condition = fixture(offsets=(0, 2, 3, 2, 0, 0), gap=20, driven=False)
    # The first two obstacles collide at the same sample. Declaration order,
    # not worker finish order or name sorting, identifies the reported pair.
    parts.update(z_first=Box(1, 1, 1), a_second=Box(1, 1, 1))
    condition["inputs"].update(obstacle_parts=["z_first", "a_second"],
                               allow_seated_contact=allow_seated)
    result = compare(motion, monkeypatch, parts, condition)
    assert result["status"] == "fail"
    assert result["step"] == expected_step
    assert result["obstacle"] == "input x z_first"
    assert result["skippedSeatedStep"] == allow_seated


@pytest.mark.parametrize("workers", ["0", "33", "2.5", "nonsense"])
def test_invalid_worker_selection_is_inconclusive(motion, monkeypatch, workers):
    monkeypatch.setenv("WORKSHOP_MOTION_WORKERS", workers)
    parts, condition = fixture()
    result = motion["run_condition"](condition, parts, 0)
    assert result["status"] == "inconclusive"
    assert "WORKSHOP_MOTION_WORKERS" in result["detail"]
    assert "clear" not in result


def test_parallel_timeout_remains_deadline_stopped_not_a_clear_pose(motion, monkeypatch):
    import motion_parallel
    monkeypatch.setenv("WORKSHOP_MOTION_WORKERS", "2")
    def stopped(*args):
        raise TimeoutError("ordered pose coverage timed out")
    monkeypatch.setattr(motion_parallel, "sweep", stopped)
    parts, condition = fixture()
    result = motion["run_condition"](condition, parts, 0)
    assert result["status"] == "inconclusive"
    assert result["deadlineStopped"] is True
    assert "clear" not in result
    assert "timed out" in result["detail"]
