"""Inspection progress must be visible before a batch finishes, without changing gates."""
import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import select
import subprocess
import sys
import textwrap

import pytest


TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


@pytest.mark.parametrize("exit_code", [0, 2])
def test_worker_announces_request_before_work_and_keeps_result(monkeypatch, exit_code):
    worker = runpy.run_path(str(TOOLS / "inspect/inspect_refs/cli.py"))["_worker_response"]
    stderr = io.StringIO()
    result = {"ok": exit_code == 0, "errors": []}

    def inspect(argv):
        assert argv == ["validate", "model.step.py"]
        assert 'start "validate:assembly"' in stderr.getvalue()
        assert "done" not in stderr.getvalue()
        return exit_code, result

    monkeypatch.setitem(worker.__globals__, "inspect_command_result", inspect)
    request = json.dumps({"id": "validate:assembly", "argv": ["validate", "model.step.py"]})
    monkeypatch.setenv("WORKSHOP_PROGRESS", "1")
    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()) as stdout:
        loud = worker(request)
    assert stdout.getvalue() == ""
    assert f'done "validate:assembly": rc={exit_code}' in stderr.getvalue()

    monkeypatch.setenv("WORKSHOP_PROGRESS", "0")
    monkeypatch.setitem(worker.__globals__, "inspect_command_result", lambda argv: (exit_code, result))
    with contextlib.redirect_stderr(io.StringIO()) as quiet:
        silent = worker(request)
    assert quiet.getvalue() == ""
    assert loud == silent == {
        "id": "validate:assembly", "ok": exit_code == 0,
        "exitCode": exit_code, "result": result,
    }


def test_worker_exception_reports_failure_and_retains_error_response(monkeypatch, capsys):
    worker = runpy.run_path(str(TOOLS / "inspect/inspect_refs/cli.py"))["_worker_response"]
    monkeypatch.setenv("WORKSHOP_PROGRESS", "1")

    def fail(argv):
        raise RuntimeError("injected inspection failure")

    monkeypatch.setitem(worker.__globals__, "inspect_command_result", fail)
    result = worker(json.dumps({"id": "clashes", "argv": ["interfere", "model.step.py"]}))
    captured = capsys.readouterr()
    assert captured.out == ""
    assert 'start "clashes"' in captured.err
    assert 'done "clashes": rc=2' in captured.err
    assert result["ok"] is False
    assert result["exitCode"] == 2
    assert result["result"]["errors"]


def test_verifier_relays_child_progress_while_child_is_still_running(tmp_path):
    # The child cannot finish until the test receives progress and acknowledges
    # it. Capturing stderr until process completion would deadlock this handshake.
    (tmp_path / "inspect").write_text(textwrap.dedent('''\
        import json, sys, time
        from pathlib import Path
        request = json.loads(sys.stdin.readline())
        print("inspection is running", file=sys.stderr, flush=True)
        deadline = time.monotonic() + 10
        while not Path("acknowledged").exists():
            if time.monotonic() > deadline:
                raise SystemExit(9)
            time.sleep(0.01)
        print(json.dumps({"id": request["id"], "ok": True}), flush=True)
    '''))
    harness = textwrap.dedent(f'''\
        import runpy
        from pathlib import Path
        runner_type = runpy.run_path({str(TOOLS / "verify_project")!r})["Runner"]
        runner_type.inspect_batch.__globals__["SCRIPTS_DIR"] = Path.cwd()
        runner = runner_type(cwd=Path.cwd(), dry_run=False, verbose=False)
        raise SystemExit(runner.inspect_batch([{{"id": "test", "argv": ["validate", "model"]}}]))
    ''')
    child = subprocess.Popen(
        [sys.executable, "-u", "-c", harness], cwd=tmp_path,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    try:
        ready, _, _ = select.select([child.stderr], [], [], 5)
        assert ready, "inspection progress was buffered until completion"
        assert child.stderr.readline() == "inspection is running\n"
        assert child.poll() is None
        (tmp_path / "acknowledged").touch()
        stdout, stderr = child.communicate(timeout=5)
        assert child.returncode == 0, stderr
        assert "inspect test: ok" in stdout
    finally:
        (tmp_path / "acknowledged").touch()
        if child.poll() is None:
            child.kill()
        child.communicate(timeout=15)


@pytest.mark.parametrize("stdout,returncode,expected", [
    ('{"ok":true}\n', 0, 0),
    ('{"ok":false}\n', 0, 1),
    ('{"ok":true}\n', 2, 1),
    ('not JSON\n', 0, 1),
    ('', 0, 1),
    ('{"ok":true}\n{"ok":true}\n', 0, 1),
])
def test_progress_does_not_weaken_batch_failure_handling(monkeypatch, tmp_path, stdout, returncode, expected):
    runner_type = runpy.run_path(str(TOOLS / "verify_project"))["Runner"]
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: subprocess.CompletedProcess(a, returncode, stdout))
    runner = runner_type(cwd=tmp_path, dry_run=False, verbose=False)
    assert runner.inspect_batch([{"id": "test", "argv": ["validate", "model"]}]) == expected
    assert runner.records[-1]["status"] == f"rc={expected}"


def test_real_batch_keeps_jsonl_and_failure_verdict_with_progress(tmp_path):
    request = json.dumps({"id": "missing", "argv": ["validate", "missing.step"]}) + "\n"
    outputs = []
    for progress in ("1", "0"):
        run = subprocess.run(
            [sys.executable, str(TOOLS / "inspect"), "batch"], input=request,
            capture_output=True, text=True, cwd=tmp_path, timeout=30,
            env={**os.environ, "CADGEN_WARM": "0", "WORKSHOP_PROGRESS": progress},
        )
        response = json.loads(run.stdout)
        assert response["id"] == "missing"
        assert response["ok"] is False
        assert response["exitCode"] == 2
        assert ('start "missing"' in run.stderr) is (progress == "1")
        outputs.append((run.returncode, run.stdout))
    assert outputs[0] == outputs[1]
