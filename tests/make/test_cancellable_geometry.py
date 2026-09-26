"""Geometry deadlines, honest partial results, exact reuse, and final disclosure."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import runpy
import socket
import subprocess
import sys
import threading
import time

import pytest

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"


def cad_module(name):
    spec = importlib.util.spec_from_file_location("test_vendored_" + name,
        TOOLS / "packages/cadgen/src/cadgen" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def worker_type():
    return runpy.run_path(str(TOOLS / "inspect/inspect_refs/supervisor.py"))["GeometryWorker"]


@pytest.mark.parametrize("failures", [0, 1])
def test_stuck_native_child_is_reaped_without_hiding_earlier_failure(tmp_path, failures):
    # Continuous liveness messages must not postpone the native operation limit.
    script = tmp_path / "worker.py"
    script.write_text('''import json, os, sys, time
request = json.loads(sys.stdin.readline())
fd = int(os.environ["WORKSHOP_GEOMETRY_PROGRESS_FD"])
os.write(fd, (json.dumps({"event":"operation-start", "kind":"validate", "label":"part-2", "completed":1, "failures":FAILURES})+"\\n").encode())
while True:
    os.write(fd, b'{"event":"heartbeat"}\\n')
    time.sleep(.01)
'''.replace("FAILURES", str(failures)))
    with worker_type()(command=[sys.executable, str(script)], timeout=3, operation_timeout=.15) as worker:
        start = time.monotonic()
        response = worker.request({"id": "shape", "argv": ["validate", "shape.step"]})
        assert time.monotonic() - start < 2
        assert worker.process is None
    assert response["exitCode"] == (2 if failures else 3)
    assert response["result"]["status"] == ("failed" if failures else "unverified")
    assert response["result"]["completedChecks"] == 1
    assert response["result"]["failureCount"] == failures


def test_cancelled_batch_does_not_start_more_native_work():
    with worker_type()(command=["must-not-run"]) as worker:
        worker.cancel()
        response = worker.request({"id": "next", "argv": []})
    assert response["exitCode"] == 3
    assert "cancelled" in response["result"]["unverified"][0]


def test_daemon_heartbeats_cannot_extend_deadline(monkeypatch):
    client = runpy.run_path(str(TOOLS / "cadgen_daemon/client.py"))
    monkeypatch.setitem(client["_run_request"].__globals__, "request_timeout", lambda: .15)
    parent, child = socket.socketpair()
    def server():
        child.recv(4096)
        try:
            for _ in range(100):
                child.sendall(b'{"stream":"stdout","data":""}\n')
                time.sleep(.02)
        except OSError:
            pass
        finally:
            child.close()
    thread = threading.Thread(target=server)
    thread.start()
    try:
        start = time.monotonic()
        assert client["_run_request"](parent, {"tool": "gen"}) == 124
        assert time.monotonic() - start < 1
    finally:
        parent.close()
        thread.join(timeout=3)
    assert not thread.is_alive()


def test_external_watchdog_kills_its_native_parent(tmp_path):
    # A separate interpreter watchdog must work without the daemon's Python
    # threads scheduling; this child blocks in a native libc sleep.
    code = '''import ctypes, os, subprocess, sys
r,w = os.pipe()
subprocess.Popen([sys.executable, sys.argv[1], str(r), '.15'], pass_fds=(r,))
os.close(r)
ctypes.PyDLL(None).sleep(20)
'''
    result = subprocess.run([sys.executable, "-c", code, str(TOOLS / "cadgen_daemon/watchdog.py")], timeout=3)
    assert result.returncode < 0


def test_one_source_build_per_batch_and_content_freshness(tmp_path):
    source = tmp_path / "model.step.py"
    source.write_text('''from build123d import Box
from pathlib import Path
def gen_step():
    with Path(__file__).with_name('build-count.txt').open('a') as out: out.write('built\\n')
    return Box(7, 11, 13)
''')
    requests = [{"id": name, "argv": [name, "model.step.py"]} for name in ("refs", "validate", "interfere")]
    done = subprocess.run([sys.executable, str(TOOLS / "inspect"), "batch"], cwd=tmp_path,
                          input="".join(json.dumps(x) + "\n" for x in requests), text=True, capture_output=True, timeout=30)
    assert done.returncode == 0, done.stderr
    assert all(json.loads(line)["ok"] for line in done.stdout.splitlines()), done.stdout
    assert (tmp_path / "build-count.txt").read_text().splitlines() == ["built"]

    _inputs = cad_module("inspection_runtime")._inputs
    (tmp_path / "measure").mkdir()
    asset = tmp_path / "measure/shape.dat"
    asset.write_bytes(b"abcd")
    before = _inputs(source)
    identity = asset.stat()
    asset.write_bytes(b"dcba")
    os.utime(asset, ns=(identity.st_atime_ns, identity.st_mtime_ns))
    assert _inputs(source) != before


def test_completed_measurements_survive_restart_and_only_reuse_exact_inputs(tmp_path, monkeypatch):
    runtime = cad_module("inspection_runtime")
    monkeypatch.setattr(runtime, "tool_identity", lambda: "tools-a")
    calls = []
    def run(inputs, result=None):
        cache = runtime.Measurements(tmp_path / "model.step")
        return cache.run("validate", "part", lambda: inputs,
                         lambda: (calls.append(inputs) or (result or {"ok": True})), failed=lambda value: not value["ok"])
    assert run(["shape-a", True]) == {"ok": True}
    assert run(["shape-a", True]) == {"ok": True}
    assert len(calls) == 1
    run(["shape-b", True])
    run(["shape-a", False])
    monkeypatch.setattr(runtime, "tool_identity", lambda: "tools-b")
    run(["shape-a", True])
    assert len(calls) == 4
    for _ in range(2):
        run(["unknown"], {"ok": False, "unverified": ["no verdict"]})
    assert len(calls) == 6


def test_cache_symlinks_cannot_write_outside_project(tmp_path, monkeypatch):
    Measurements = cad_module("inspection_runtime").Measurements
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    (project / "__cadgen__").symlink_to(outside, target_is_directory=True)
    result = Measurements(project / "model.step").run("validate", "part", lambda: [], lambda: {"ok": True}, failed=lambda x: False)
    assert result["ok"]
    assert list(outside.iterdir()) == []


def test_rigid_copies_reuse_validity_but_interference_keeps_placement():
    from build123d import Box, Pos, Rot
    shape_identity = cad_module("inspection_runtime").shape_identity
    shape = Box(2, 3, 4)
    moved = Pos(10, 20, 30) * Rot(0, 0, 90) * shape
    assert shape_identity(shape.wrapped, rigid_placement_invariant=True) == shape_identity(moved.wrapped, rigid_placement_invariant=True)
    assert shape_identity(shape.wrapped) != shape_identity(moved.wrapped)
    assert shape_identity(shape.wrapped, rigid_placement_invariant=True) != shape_identity(shape.wrapped.Reversed(), rigid_placement_invariant=True)


def test_identity_is_stable_across_repeated_builds_of_a_boolean_result():
    """A many-tool boolean fuse, shaped like `part_belt_cell` (issue #74):
    OCCT's B-rep container order for this depends on allocation, not geometry,
    so a raw-bytes identity varies run to run on bit-identical geometry; this
    hashes sampled analytic geometry instead and must not vary."""
    from build123d import Align, Box, Pos, RegularPolygon, extrude
    shape_identity = cad_module("inspection_runtime").shape_identity

    def build_rubble_like_solid():
        rng = random.Random(7)
        base = Box(20, 20, 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
        tools = []
        for _ in range(60):
            x, y = rng.uniform(-8, 8), rng.uniform(-8, 8)
            radius = rng.uniform(0.4, 1.2)
            sides = rng.choice((5, 6, 7, 8))
            rise = rng.uniform(1, 3)
            taper = rng.uniform(30, 44)
            rock = extrude(RegularPolygon(radius, sides, rotation=rng.uniform(0, 60)), rise, taper=taper)
            tools.append(Pos(x, y, 4) * rock)
        body = base + tools
        envelope = Box(18, 18, 10, align=(Align.CENTER, Align.CENTER, Align.MIN))
        return (body & envelope).wrapped

    identities = {shape_identity(build_rubble_like_solid()) for _ in range(6)}
    assert len(identities) == 1
    # A genuinely different shape still hashes differently -- exact, not tolerance-based.
    assert shape_identity(build_rubble_like_solid()) != shape_identity(Box(2, 3, 4).wrapped)


def test_sweep_matches_naive_candidate_set_including_touching():
    module = cad_module("interference")
    Occurrence, _candidate_pairs, _boxes_overlap = module.Occurrence, module._candidate_pairs, module._boxes_overlap
    rng = random.Random(2026)
    parts = []
    for i in range(300):
        x, y, z = [rng.randrange(-10, 10) for _ in range(3)]
        dx, dy, dz = [rng.choice([0, .000001, 1, 5]) for _ in range(3)]
        parts.append(Occurrence(str(i), str(i), None, (x, y, z, x+dx, y+dy, z+dz)))
    expected = {(a.ref, b.ref) for i,a in enumerate(parts) for b in parts[i+1:] if _boxes_overlap(a.bbox, b.bbox)}
    assert {(a.ref, b.ref) for a,b in _candidate_pairs(parts)} == expected


@pytest.mark.parametrize("status,code,expected", [("unverified",3,0),("failed",2,1),("unverified",2,1)])
@pytest.mark.parametrize("mode", ["final", "image-derived final"])
def test_verifier_only_continues_explicit_unverified_geometry(monkeypatch, tmp_path, status, code, expected, mode):
    module = runpy.run_path(str(TOOLS / "verify_project"))
    response = {"id":"validate:assembly", "ok":False,"exitCode":code,
                "result":{"ok":False,"status":status,"unverified":["time allowance exhausted"],"completedChecks":2,"errors":[]}}
    monkeypatch.setattr(subprocess, "run", lambda *a,**kw: subprocess.CompletedProcess(a,0,json.dumps(response)))
    runner = module["Runner"](cwd=tmp_path,dry_run=False,verbose=False)
    assert runner.inspect_batch([{"id":"validate:assembly","argv":["validate","model.step"]}]) == expected
    report = tmp_path / "measure/verification-pipeline.md"
    module["_write_report"](report,runner,mode=mode,result=expected,elapsed=1,bed=(220,220,220))
    assert ("**UNVERIFIED**" if expected == 0 else "**FAIL**") in report.read_text()
    if expected == 0:
        disclosure = runpy.run_path(str(TOOLS / "geometry_disclosure.py"))
        product = {"title":"Complex assembly", "summary":"Prototype", "status":"full-with-thickness"}
        disclosure["seal_disclosure"](tmp_path,report,product)
        assert product["print_ready_claim"] is False
        assert "validate:assembly" in (tmp_path/"README.md").read_text()
        assert disclosure["validate_disclosure"](tmp_path,report,product)["status"] == "unverified"
        report.write_text(report.read_text()+"modified")
        with pytest.raises(ValueError,match="bind"):
            disclosure["validate_disclosure"](tmp_path,report,product)
        module["_write_report"](report,runner,mode="quick",result=expected,elapsed=1,bed=(220,220,220))
        with pytest.raises(ValueError,match="current final"):
            disclosure["validate_disclosure"](tmp_path,report,product)


@pytest.mark.parametrize("measured_failure", [False,True])
def test_native_analysis_timeout_continues_only_without_known_failure(tmp_path, monkeypatch, measured_failure):
    module = runpy.run_path(str(TOOLS / "verify_project"))
    tool = tmp_path / "check_thickness"
    tool.write_text("import os,time\n" + ("os.write(int(os.environ['WORKSHOP_GEOMETRY_FAILURE_FD']),b'1')\n" if measured_failure else "") + "time.sleep(20)\n")
    monkeypatch.setenv("WORKSHOP_GEOMETRY_TIMEOUT", ".15")
    runner = module["Runner"](cwd=tmp_path,dry_run=False,verbose=False)
    assert runner.command([sys.executable,tool,"part.step.py"]) == (124 if measured_failure else 0)
    assert runner.records[-1]["status"] == ("rc=124" if measured_failure else "unverified")


def test_fresh_generation_keeps_exact_measurement_checkpoints(tmp_path):
    remove = runpy.run_path(str(TOOLS / "verify_project"))["_remove_generation_cache"]
    cache = tmp_path / "__cadgen__"
    (cache / "inspection-v2").mkdir(parents=True)
    (cache / "inspection-v2/check.json").write_text("completed exact measurement")
    (cache / "models").mkdir()
    (cache / "models/stale.json").write_text("stale build")
    remove(cache, preserve_measurements=True)
    assert (cache / "inspection-v2/check.json").read_text() == "completed exact measurement"
    assert not (cache / "models/stale.json").exists()


def test_supervisor_death_cancels_its_native_worker(tmp_path):
    pid_file = tmp_path / "worker.pid"
    child = tmp_path / "kernel.py"
    child.write_text("import os,sys,ctypes\nfrom pathlib import Path\n"
        "sys.stdin.readline()\nPath(sys.argv[1]).write_text(str(os.getpid()))\nctypes.PyDLL(None).sleep(30)\n")
    code = "import runpy,sys\nWorker=runpy.run_path(sys.argv[1])['GeometryWorker']\n" \
           "with Worker(command=[sys.executable,sys.argv[2],sys.argv[3]],timeout=20) as w:\n w.request({'id':'hang','argv':[]})\n"
    parent = subprocess.Popen([sys.executable,"-c",code,str(TOOLS/"inspect/inspect_refs/supervisor.py"),str(child),str(pid_file)])
    try:
        deadline = time.monotonic() + 5
        while not pid_file.exists() and time.monotonic() < deadline:
            time.sleep(.01)
        assert pid_file.exists()
        pid = int(pid_file.read_text())
        parent.kill()
        parent.wait(timeout=3)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(.02)
        else:
            pytest.fail("orphaned native worker survived supervisor death")
    finally:
        if parent.poll() is None:
            parent.kill()
        parent.wait(timeout=3)


def test_native_checks_leave_input_identity_unchanged():
    from build123d import Box, Pos
    identity = cad_module("inspection_runtime").shape_identity
    validity = cad_module("validity")
    interference = cad_module("interference")
    first = Box(5,5,5).wrapped
    second = (Pos(3,0,0)*Box(5,5,5)).wrapped
    before = [identity(first),identity(second)]
    assert validity.check_occurrence_shape(first)["reasons"] == []
    common = interference._intersection(first,second)
    assert interference._solid_volume(common) == pytest.approx(50)
    assert [identity(first),identity(second)] == before


def test_real_worker_rebuilds_changed_source_bytes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / "model.step.py"
    code = "from build123d import Box\nfrom pathlib import Path\ndef gen_step():\n with Path('count.txt').open('a') as f: f.write('1')\n return Box(2,3,4)\n"
    source.write_text(code)
    with worker_type()(timeout=30) as worker:
        assert worker.request({"id":"first","argv":["validate",str(source)]})["ok"]
        assert worker.request({"id":"cached","argv":["interfere",str(source)]})["ok"]
        assert (tmp_path/"count.txt").read_text() == "1"
        before = source.stat()
        source.write_text(code.replace("Box(2,3,4)","Box(7,3,4)"))
        os.utime(source, ns=(before.st_atime_ns,before.st_mtime_ns))
        assert worker.request({"id":"changed","argv":["validate",str(source)]})["ok"]
        assert (tmp_path/"count.txt").read_text() == "11"


def test_finalizer_embeds_same_data_only_disclosure_contract():
    import re
    root = Path(__file__).resolve().parents[2]
    helper = (TOOLS / "geometry_disclosure.py").read_text()
    helper = helper[helper.index("STATUS ="):]
    for name in ("STATUS","LIMITATION","REPORT_NAME","NOTES_NAME","validate_report","notes_text","read_report","seal_disclosure","validate_disclosure"):
        helper = re.sub(r"\b"+name+r"\b","_geometry_"+name,helper)
    finalizer = (root / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py").read_text()
    assert helper in finalizer


def test_cache_directory_swap_cannot_redirect_completed_measurements(tmp_path, monkeypatch):
    runtime = cad_module("inspection_runtime")
    project, outside = tmp_path / "project", tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    (project / "__cadgen__").mkdir()
    original_mkdir = os.mkdir
    swapped = False
    def swap(path, *args, **kwargs):
        nonlocal swapped
        if path == "inspection-v2" and not swapped:
            swapped = True
            (project / "__cadgen__").rename(project / "saved-cache")
            (project / "__cadgen__").symlink_to(outside, target_is_directory=True)
        return original_mkdir(path, *args, **kwargs)
    monkeypatch.setattr(os, "mkdir", swap)
    result = runtime.Measurements(project / "shape.step").run("validate","part",lambda:[],lambda:{"ok":True},failed=lambda x:False)
    assert result["ok"] and swapped
    assert list(outside.iterdir()) == []


def test_validity_reports_a_measured_failure_before_the_next_kernel_call(monkeypatch):
    from build123d import Box
    validity = cad_module("validity")
    failures = []
    def next_kernel(shape):
        assert "nonPositiveVolume" in failures
        raise RuntimeError("simulated native interruption")
    monkeypatch.setattr(validity, "_is_self_intersecting", next_kernel)
    with pytest.raises(RuntimeError, match="interruption"):
        validity.check_occurrence_shape(Box(3,4,5).wrapped.Reversed(), on_failure=failures.append)


def test_invalid_member_is_recorded_before_measuring_the_next_solid(monkeypatch):
    from build123d import Box
    validity = cad_module("validity")
    failures = []
    monkeypatch.setattr(validity, "_solids", lambda shape: ["inverted", "next"])
    def volume(solid):
        if solid == "inverted":
            return -1.0
        assert failures == ["nonPositiveVolume"]
        raise RuntimeError("simulated native interruption")
    monkeypatch.setattr(validity, "_signed_volume", volume)
    with pytest.raises(RuntimeError, match="interruption"):
        validity.check_occurrence_shape(Box(3,4,5).wrapped, on_failure=failures.append)
