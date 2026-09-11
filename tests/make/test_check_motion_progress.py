"""Motion progress is optional observation, never numerical gate evidence."""
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import runpy
import subprocess
import sys

import pytest


CHECK = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/check_motion"


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class Stream(StringIO):
    def __init__(self):
        super().__init__()
        self.flushes = 0

    def flush(self):
        self.flushes += 1
        super().flush()


@pytest.fixture
def tool():
    return runpy.run_path(str(CHECK))["main"].__globals__


@contextmanager
def observing(tool, observer):
    token = tool["_PROGRESS"].set(observer)
    try:
        yield
    finally:
        tool["_PROGRESS"].reset(token)


def test_global_throttle_flush_and_terminal_bypass(tool):
    stream, clock = Stream(), Clock()
    observer = tool["Progress"](stream, clock)
    observer.total_conditions = 1303
    with observing(tool, observer):
        tool["progress"]("starting", force=True)
        for index in range(1303):
            with tool["condition_progress"](index):
                tool["sample_progress"]("sweep", 0, 9600)
        assert stream.flushes == 1
        clock.now = 4.999
        tool["progress"]("too soon")
        clock.now = 5.0
        with tool["condition_progress"](0):
            clock.now = 10.0
            with tool["condition_progress"](2):
                pass
        tool["progress"]("finished with exit code 1", force=True)
    assert stream.getvalue().splitlines() == [
        "check_motion progress: starting",
        "check_motion progress: condition 1/1303: evaluating",
        "check_motion progress: condition 1/1303, nested step 3: evaluating",
        "check_motion progress: finished with exit code 1",
    ]
    assert stream.flushes == 4
    assert observer.condition == ""


def test_nested_prefix_restores_after_exception_and_unknown_total_is_not_a_count(tool):
    stream, clock = Stream(), Clock()
    observer = tool["Progress"](stream, clock)
    with observing(tool, observer), tool["condition_progress"](0):
        clock.now = 5
        with pytest.raises(ValueError), tool["condition_progress"](1):
            raise ValueError("fixture")
        assert observer.condition == "condition 1"
        clock.now = 10
        tool["progress"]("continuing")
    assert observer.condition == ""
    assert "None" not in stream.getvalue()
    assert "condition 1: continuing" in stream.getvalue()


def test_default_helpers_never_read_clock_or_write(tool, monkeypatch):
    def forbidden():
        raise AssertionError("disabled progress read the clock")
    monkeypatch.setattr(tool["time"], "monotonic", forbidden)
    stream = StringIO()
    with redirect_stderr(stream), tool["condition_progress"](0):
        assert tool["sweep"](None, [], lambda shape, fraction: shape, 3, .001, False)["clear"]
    assert stream.getvalue() == ""


@pytest.mark.parametrize("failure", ["write", "flush", "clock"])
def test_observer_failure_disables_only_diagnostics(tool, failure):
    class BrokenStream(Stream):
        def write(self, value):
            if failure == "write":
                raise OSError("closed")
            return super().write(value)

        def flush(self):
            if failure == "flush":
                raise ValueError("closed")
            super().flush()

    def clock():
        if failure == "clock":
            raise RuntimeError("observer unavailable")
        return 0.0

    observer = tool["Progress"](BrokenStream(), clock)
    with observing(tool, observer):
        tool["progress"]("starting", force=True)
        assert not observer.enabled
        assert tool["sweep"](None, [], lambda shape, fraction: shape, 3, .001, False)["clear"]
        tool["progress"]("finished", force=True)


@pytest.mark.parametrize("allow_seated", [False, True])
@pytest.mark.parametrize("collision", [None, 4])
def test_sweep_progress_keeps_exact_samples_and_first_collision(tool, monkeypatch, allow_seated, collision):
    def run(observer):
        samples = []
        def place(shape, fraction):
            samples.append(round(fraction * 8))
            clock.now += 5
            return samples[-1]
        monkeypatch.setitem(tool, "overlap_volume", lambda a, b: 1.0 if a == collision else 0.0)
        with observing(tool, observer):
            result = tool["sweep"](None, [("fixed", None)], place, 8, .001, allow_seated)
        return result, samples
    clock, stream = Clock(), Stream()
    baseline = run(None)
    clock.now = 0
    actual = run(tool["Progress"](stream, clock))
    assert actual == baseline
    assert len(stream.getvalue().splitlines()) == len(actual[1])
    assert f"sample index {actual[1][-1]}/8" in stream.getvalue()
    if collision is not None:
        assert "sample index 5/8" not in stream.getvalue()


def test_long_coupled_sweep_reports_inside_condition_without_changing_work(tool, monkeypatch):
    clock, stream = Clock(), Stream()
    def run(observer):
        calls = []
        def table(spec, steps, field):
            def place(shape, step):
                return spec["part"], step
            place.axis_point = place.axis_direction = None
            place.angles = place.offsets = []
            return place
        def overlap(first, second):
            calls.append((first, second))
            clock.now += .01
            return 0.0
        monkeypatch.setitem(tool, "_pose_table", table)
        monkeypatch.setitem(tool, "_reach", lambda *args: 0.0)
        monkeypatch.setitem(tool, "_step_mm", lambda *args: 0.0)
        monkeypatch.setitem(tool, "overlap_volume", overlap)
        with observing(tool, observer):
            result = tool["check_coupled"](
                {"movers": [{"part": "a"}, {"part": "b"}], "steps": 9600,
                 "obstacle_parts": []}, {}, {"a": None, "b": None})
        return result, calls
    expected = run(None)
    clock.now = 0
    assert run(tool["Progress"](stream, clock)) == expected
    lines = stream.getvalue().splitlines()
    assert 18 <= len(lines) <= 20
    assert "coupled sweep sample index 0/9600" in lines[0]
    assert any("sample index 5" in line for line in lines)
    assert expected[0]["clear"] and len(expected[1]) == 9601


def test_drive_search_progress_preserves_query_order_and_early_witness(tool, monkeypatch):
    clock, stream = Clock(), Stream()
    def run(observer):
        calls = []
        def place(shape, step):
            return shape, step
        def overlap(first, second):
            calls.append(("overlap", first, second))
            clock.now += 5
            return 1.0 if first[1] == 3 else 0.0
        def distance(first, second, **kwargs):
            calls.append(("distance", first, second))
            clock.now += 5
            return 0.0 if first[1] == 2 else 1.0
        monkeypatch.setitem(tool, "overlap_volume", overlap)
        monkeypatch.setitem(tool, "surface_distance", distance)
        with observing(tool, observer):
            result = tool["sampled_drive_evidence"](
                [("input", "input", place, False), ("output", "output", place, True)],
                10, .001, False)
        return result, calls
    baseline = run(None)
    clock.now = 0
    assert run(tool["Progress"](stream, clock)) == baseline
    text = stream.getvalue()
    assert "drive frozen-contact sample index 3/10" in text
    assert "drive nominal-contact sample index 2/10" in text
    assert "sample index 4/10" not in text
    assert baseline[0]["unreachedDrivenParts"] == []


def invoke(tool, monkeypatch, tmp_path, *, progress=False, json_output=True,
           conditions=None, allow_inconclusive=False):
    stdout, stderr = StringIO(), Stream()
    args = [str(CHECK), str(tmp_path), "--manifest", "fixture.json"]
    args += ["--progress"] if progress else []
    args += ["--json"] if json_output else []
    args += ["--allow-inconclusive"] if allow_inconclusive else []
    monkeypatch.setattr(sys, "argv", args)
    monkeypatch.setitem(tool, "load_manifest", lambda path: {"conditions": deepcopy(conditions)})
    monkeypatch.setitem(tool, "find_assembly_entry", lambda *args: tmp_path / "toy.step.py")
    monkeypatch.setitem(tool, "build_assembly", lambda entry: object())
    monkeypatch.setitem(tool, "index_parts", lambda assembly: {"wheel": object()})
    monkeypatch.setattr(tool["time"], "monotonic", lambda: 0.0)
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = tool["main"]()
    assert tool["_PROGRESS"].get() is None
    return result, stdout.getvalue(), stderr.getvalue()


@pytest.mark.parametrize("json_output", [False, True])
@pytest.mark.parametrize("status", ["pass", "fail", "inconclusive"])
@pytest.mark.parametrize("allow_inconclusive", [False, True])
def test_cli_result_bytes_and_exit_unchanged(tool, monkeypatch, tmp_path, json_output, status, allow_inconclusive):
    calls = []
    def condition(row, parts, index):
        calls.append(index)
        return {"id": str(index), "check": "fixture", "status": status, "detail": "measured"}
    monkeypatch.setitem(tool, "run_condition", condition)
    options = dict(json_output=json_output, conditions=[{}, {}], allow_inconclusive=allow_inconclusive)
    baseline = invoke(tool, monkeypatch, tmp_path, **options)
    observed = invoke(tool, monkeypatch, tmp_path, progress=True, **options)
    assert observed[:2] == baseline[:2]
    assert calls == [0, 1, 0, 1]
    lines = observed[2].splitlines(keepends=True)
    assert "".join(line for line in lines if not line.startswith("check_motion progress:")) == baseline[2]
    assert f"finished with exit code {baseline[0]}" in observed[2]
    assert "progress:" not in baseline[2]
    if json_output:
        assert json.loads(observed[1])["ok"] == (observed[0] == 0)


def test_unknown_and_nested_conditions_do_not_inject_progress_text(tool, monkeypatch, tmp_path):
    conditions = [{"id": "bad\n\x1b[31m", "check": "assembly_sequence", "inputs": {
        "steps": [{"id": "evil\n", "check": "unknown\n\x1b[31m"}]}}]
    baseline = invoke(tool, monkeypatch, tmp_path, conditions=conditions)
    actual = invoke(tool, monkeypatch, tmp_path, conditions=conditions, progress=True)
    assert actual[:2] == baseline[:2] and actual[0] == 1
    assert "bad" not in actual[2] and "evil" not in actual[2] and "\x1b" not in actual[2]


def test_failed_progress_stream_preserves_main_result(tool, monkeypatch, tmp_path):
    conditions = [{"id": "unknown", "check": "unknown"}]
    baseline = invoke(tool, monkeypatch, tmp_path, conditions=conditions)
    original = tool["Progress"]
    class BrokenStream:
        def write(self, value):
            raise OSError("unavailable")
    monkeypatch.setitem(tool, "Progress", lambda stream: original(BrokenStream()))
    actual = invoke(tool, monkeypatch, tmp_path, conditions=conditions, progress=True)
    assert actual == baseline


@pytest.mark.parametrize("error", ["manifest", "unexpected", "interrupt"])
def test_setup_failures_and_interrupt_restore_observer(tool, monkeypatch, tmp_path, error):
    stdout, stderr = StringIO(), Stream()
    monkeypatch.setattr(sys, "argv", [str(CHECK), str(tmp_path), "--manifest", "fixture", "--progress"])
    exception = {"manifest": tool["ManifestError"], "unexpected": RuntimeError,
                 "interrupt": KeyboardInterrupt}[error]
    def fail(path):
        raise exception("fixture error")
    monkeypatch.setitem(tool, "load_manifest", fail)
    with redirect_stdout(stdout), redirect_stderr(stderr):
        if error == "manifest":
            assert tool["main"]() == 2
        else:
            with pytest.raises(exception):
                tool["main"]()
    assert stdout.getvalue() == ""
    assert tool["_PROGRESS"].get() is None
    assert ("finished with exit code 2" if error == "manifest" else "stopped before a result") in stderr.getvalue()


def test_real_tiny_cli_json_and_human_bytes_match_with_progress(tmp_path):
    (tmp_path / "toy.step.py").write_text(
        "from build123d import Box, Compound\n"
        "def gen_step():\n"
        "    a=Box(1,1,1); a.label='moving'\n"
        "    b=Box(1,1,1).translate((10,0,0)); b.label='fixed'\n"
        "    return Compound(children=[a,b])\n")
    manifest = tmp_path / "motion.json"
    manifest.write_text(json.dumps({"conditions": [{"id": "move", "check": "linear_motion_collision",
        "inputs": {"moving_part": "moving", "obstacle_parts": ["fixed"],
                   "translation": [1, 0, 0], "steps": 3}}]}))
    for flags in ([], ["--json"], ["--list-parts"]):
        args = [sys.executable, str(CHECK), str(tmp_path), "--manifest", str(manifest), *flags]
        baseline = subprocess.run(args, capture_output=True, check=False)
        actual = subprocess.run([*args, "--progress"], capture_output=True, check=False)
        assert baseline.returncode == actual.returncode == 0
        assert baseline.stdout == actual.stdout
        assert baseline.stderr == b""
        assert b"finished with exit code 0" in actual.stderr
