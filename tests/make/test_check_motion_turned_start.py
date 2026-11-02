"""A clear rotation that starts turned from rest sweeps its first pose.

allow_seated_contact skips step 0 as the installed pose. A rotation whose
start_deg is not 0 has no installed pose at step 0, so a contact there was
skipped and the sweep read clear (Cogdragon yaw_J03, -12..+12 degrees, hid a
3 mm3 contact at -12). Stops (expect "blocked"), start-at-0 sweeps and other
checks keep the skip.
"""
from pathlib import Path
import runpy

import pytest

CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


@pytest.fixture
def motion(monkeypatch):
    tool = runpy.run_path(str(CHECK))
    seen = []

    def fake(inputs, thresholds, parts):
        seen.append(dict(inputs))
        return {"clear": True, "steps": inputs.get("steps", 1),
                "skippedSeatedStep": bool(inputs.get("allow_seated_contact", False))}

    for name in ("rotation_motion_collision", "linear_motion_collision"):
        monkeypatch.setitem(tool["CHECKS"], name, fake)
    return tool, seen


def condition(check="rotation_motion_collision", expect="clear", start=-12, **extra):
    inputs = {"moving_part": "arm", "obstacle_parts": ["block"], "steps": 6,
              "allow_seated_contact": True, **extra}
    if check == "rotation_motion_collision":
        inputs.update(axis_point=[0, 0, 0], axis_direction=[0, 0, 1], start_deg=start, end_deg=12)
    else:
        inputs.update(translation=[0, 0, -10])
    return {"id": "c", "check": check, "expect": expect, "inputs": inputs}


def test_turned_clear_rotation_sweeps_its_first_pose(motion):
    tool, seen = motion
    cond = condition()
    record = tool["run_condition"](cond, {}, 0)
    assert seen[-1]["allow_seated_contact"] is False
    assert record["skippedSeatedStep"] is False
    assert "seatedSkipRefused" in record
    assert cond["inputs"]["allow_seated_contact"] is True, "the manifest itself is not rewritten"


def test_rotation_from_rest_keeps_the_seated_skip(motion):
    tool, seen = motion
    record = tool["run_condition"](condition(start=0), {}, 0)
    assert seen[-1]["allow_seated_contact"] is True
    assert record["skippedSeatedStep"] is True
    assert "seatedSkipRefused" not in record


def test_stop_keeps_the_seated_skip(motion):
    tool, seen = motion
    record = tool["run_condition"](condition(expect="blocked"), {}, 0)
    assert seen[-1]["allow_seated_contact"] is True
    assert "seatedSkipRefused" not in record


def test_non_rotation_check_keeps_the_seated_skip(motion):
    tool, seen = motion
    record = tool["run_condition"](condition(check="linear_motion_collision"), {}, 0)
    assert seen[-1]["allow_seated_contact"] is True
    assert "seatedSkipRefused" not in record


@pytest.mark.parametrize("start", ["later", None, [1]])
def test_non_numeric_start_does_not_crash_the_guard(motion, start):
    tool, seen = motion
    record = tool["run_condition"](condition(start=start), {}, 0)
    assert seen[-1]["allow_seated_contact"] is True
    assert "seatedSkipRefused" not in record
    assert record["status"] == "pass"
