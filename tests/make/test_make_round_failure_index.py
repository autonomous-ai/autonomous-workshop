"""Failed-part console projections retain the complete underlying evidence."""
import copy
import json
import subprocess
from pathlib import Path

import pytest

from tests.make.test_make_round import (
    _gate_output, _install_gate_identity, fake_visual_render, load_module,
)


def large_summary():
    roles = ["part_%03d" % index for index in range(78)]
    return {
        "round": 1, "project": "/synthetic/cad", "parts": roles,
        "checked": roles.copy(), "changed": roles.copy(),
        "build": {role: {"verdict": "PASS", "failures": []} for role in roles},
        "print": {role: {"verdict": "PASS", "measured_round": 1,
                         "thickness": {"verdict": "PASS", "failures": [], "thinnest_mm": 1.2},
                         "overhang": {"verdict": "PASS", "failures": []}}
                  for role in roles},
        "reused": [], "likeness": [], "motion": None, "full": None,
        "visual": {"status": "pending", "findings": [], "packet": "/synthetic/packet.json"},
        "min": .9, "checks_ok": False, "ok": False, "out": "/synthetic/round",
    }


def test_all_large_round_failures_precede_detailed_passes_without_mutation():
    module = load_module()
    summary = large_summary()
    expected = {
        "part_002": ["thickness"],
        "part_039": ["thickness", "overhang"],
        "part_077": ["build", "thickness", "overhang"],
    }
    for role, gates in expected.items():
        summary["print"][role]["verdict"] = "FAIL"
        for gate in gates:
            row = summary["build"][role] if gate == "build" else summary["print"][role][gate]
            row.update(verdict="FAIL", failures=["synthetic failure"])
    before = copy.deepcopy(summary)
    text = module.render_summary(summary)
    first_detail = text.index("  build PASS")
    assert text.splitlines()[1].startswith("  failed build/print parts (3):")
    for role, gates in expected.items():
        assert text.index("%s [%s]" % (role, ", ".join(gates))) < first_detail
    encoded = module.render_json_summary(summary)
    projection = json.loads(encoded)
    assert next(iter(projection)) == "failed_part_checks"
    assert projection.pop("failed_part_checks") == expected
    assert encoded.index('"part_039"') < encoded.index('"build":')
    assert projection == summary == before
    assert text.splitlines()[-1].startswith("  FAIL")


def test_old_summary_uses_all_recorded_results_including_unchecked_reuse():
    module = load_module()
    summary = large_summary()
    summary["checked"] = summary["changed"] = []
    summary["reused"] = summary["parts"].copy()
    summary["print"]["part_039"]["thickness"]["verdict"] = "FAIL"
    summary["print"]["part_039"]["verdict"] = "FAIL"
    summary["print"]["part_077"] = {"verdict": "FAIL", "measured_round": 0}
    expected = {"part_039": ["thickness"], "part_077": ["print"]}
    assert "failed_part_checks" not in summary
    assert module.failed_part_checks(summary) == expected
    assert "part_039 [thickness]" in module.render_summary(summary).splitlines()[1]
    # A prior display projection cannot override the exact detailed verdicts.
    summary["failed_part_checks"] = {"stale_role": ["build"]}
    assert json.loads(module.render_json_summary(summary))["failed_part_checks"] == expected
    legacy = {"build": {"old_part": {"verdict": "FAIL"}}}
    assert module.failed_part_checks(legacy) == {"old_part": ["build"]}


@pytest.mark.parametrize("visual", ["pending", "inconclusive", "error", "fail"])
def test_warnings_and_other_gate_failures_are_not_failed_parts(visual):
    module = load_module()
    summary = large_summary()
    summary["build"]["part_002"]["verdict"] = "WARN"
    summary["print"]["part_039"]["thickness"]["verdict"] = "WARN"
    summary["visual"]["status"] = visual
    summary["motion"] = {"verdict": "fail", "detail": "synthetic motion failure"}
    before = copy.deepcopy(summary)
    assert module.failed_part_checks(summary) == {}
    text = module.render_summary(summary)
    assert text.splitlines()[1] == "  failed build/print parts (0): none"
    assert "move  FAIL" in text and text.splitlines()[-1].startswith("  FAIL")
    assert json.loads(module.render_json_summary(summary))["failed_part_checks"] == {}
    assert summary == before


@pytest.mark.parametrize("json_mode", [False, True])
@pytest.mark.parametrize("fails", [False, True])
def test_run_and_feedback_console_projection_preserves_saved_schema_and_exits(
    tmp_path, monkeypatch, capsys, json_mode, fails,
):
    module = load_module()
    (tmp_path / "toy.step.py").write_text("def gen_step(): pass\n")
    (tmp_path / "part_wheel.step.py").write_text("def gen_step(): pass\n")
    _install_gate_identity(tmp_path)
    calls = []

    def fake_run(command, **kwargs):
        tool = Path(command[1]).name
        calls.append(tool)
        if tool == "gen":
            Path(command[2]).with_suffix("").write_bytes(b"synthetic STEP")
        if tool == "render_review":
            return fake_visual_render(command)
        if tool in ("check_thickness", "check_overhang"):
            stdout, code = _gate_output(tool, fails=fails)
            Path(kwargs["log"]).write_text(stdout)
            return subprocess.CompletedProcess(command, code, stdout, "")
        return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

    monkeypatch.setattr(module, "skills_root", lambda: tmp_path)
    monkeypatch.setattr(module, "run", fake_run)
    options = ["--json"] if json_mode else []
    expected = {"wheel": ["thickness", "overhang"]} if fails else {}
    saved_path = tmp_path / "measure/rounds/r0001/summary.json"

    def assert_console_matches_saved():
        output = capsys.readouterr().out
        saved = json.loads(saved_path.read_bytes())
        assert "failed_part_checks" not in saved
        if json_mode:
            projection = json.loads(output)
            assert next(iter(projection)) == "failed_part_checks"
            assert projection.pop("failed_part_checks") == expected
            assert projection == saved
        else:
            assert output.splitlines()[1].startswith("  failed build/print parts (%d):" % len(expected))
        return saved

    assert module.main([str(tmp_path), *options]) == 1
    initial = assert_console_matches_saved()
    assert initial["checks_ok"] is (not fails)
    assert initial["ok"] is False and initial["visual"]["status"] == "pending"
    feedback = tmp_path / "measure/feedback.json"
    feedback.write_text(json.dumps({
        "packet_sha256": initial["visual"]["packet_sha256"], "status": "pass", "findings": [],
        "observation": "Synthetic fixture inspected.",
    }))
    before_calls = calls.copy()
    args = [str(tmp_path), "--record-visual", str(feedback), *options]
    assert module.main(args) == (1 if fails else 0)
    final = assert_console_matches_saved()
    assert calls == before_calls
    assert final["build"] == initial["build"] and final["print"] == initial["print"]
    assert final["checks_ok"] == initial["checks_ok"] and final["ok"] is (not fails)
    before_bytes = saved_path.read_bytes()
    assert module.main(args) == 2  # Repeated feedback still fails, without a fabricated summary.
    captured = capsys.readouterr()
    assert captured.out == "" and "only accepted once" in captured.err
    assert saved_path.read_bytes() == before_bytes
