"""One canonical review must survive Make verification and stage finalization."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import runpy
import shutil
import subprocess
import sys
from unittest import mock

import pytest

from workshop.make.native_gate import _print_gate_report_without_location

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / "src/workshop/make/skills/cad/scripts"
VERIFIER = runpy.run_path(str(SCRIPTS / "verify_project"))
FINALIZER = runpy.run_path(str(REPOSITORY / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"))


def digest(content):
    return hashlib.sha256(content).hexdigest()


def write_review(project, review):
    content = FINALIZER["canonical_json"](review)
    (project / "snap/SIGNATURE-REVIEW.json").write_bytes(content)
    return content


def validate_both(project, content):
    assert (project / "snap/SIGNATURE-REVIEW.json").read_bytes() == content
    assert VERIFIER["_required_signature_review"](project) == digest(content)
    FINALIZER["_validate_signature_review"](
        project.parent, product_root_value=project.name,
        cad_project_path=PurePosixPath("."), concept_sha256="0" * 64,
    )
    assert (project / "snap/SIGNATURE-REVIEW.json").read_bytes() == content


def refuse_both(project):
    with pytest.raises(ValueError):
        VERIFIER["_required_signature_review"](project)
    with pytest.raises(FINALIZER["ProposalError"]):
        FINALIZER["_validate_signature_review"](
            project.parent, product_root_value=project.name,
            cad_project_path=PurePosixPath("."), concept_sha256="0" * 64,
        )


@pytest.fixture
def paper_project(tmp_path):
    project = VERIFIER["_sc_project"](tmp_path)
    review = json.loads((project / "snap/SIGNATURE-REVIEW.json").read_bytes())
    assert review["schema_version"] == 8
    for gate, (heading, result) in VERIFIER["PRINT_GATE_RESULTS"].items():
        relative = f"measure/{gate}-body.md"
        content = f"{heading}\n{result}\n".encode()
        (project / relative).write_bytes(content)
        review["print_gate_sha256s"][relative] = digest(content)
    write_review(project, review)
    return project, review


@pytest.mark.parametrize("claim", [False, True])
def test_same_schema8_review_bytes_pass_both_validators(paper_project, claim):
    project, review = paper_project
    if not claim:
        review["print_gate_sha256s"] = {}
    validate_both(project, write_review(project, review))


@pytest.mark.parametrize("change", [
    "schema7", "missing-map", "extra-field", "noncanonical", "map-list",
    "one-gate", "bad-digest", "stale", "missing", "empty", "oversized",
    "not-utf8", "wrong-heading", "failed", "missing-result", "file-link",
    "directory-link", "directory-report", "absolute", "traversal", "nested",
    "backslash", "unknown-gate",
])
def test_invalid_review_or_report_fails_both_paths(paper_project, change):
    project, review = paper_project
    relative = "measure/thickness-body.md"
    report = project / relative
    bindings = review["print_gate_sha256s"]
    if change == "schema7":
        review["schema_version"] = 7
        del review["print_gate_sha256s"]
    elif change == "missing-map":
        del review["print_gate_sha256s"]
    elif change == "extra-field":
        review["not_a_review_field"] = True
    elif change == "map-list":
        review["print_gate_sha256s"] = []
    elif change == "one-gate":
        del bindings["measure/overhang-body.md"]
    elif change == "bad-digest":
        bindings[relative] = "not-a-digest"
    elif change == "stale":
        report.write_bytes(report.read_bytes() + b"changed measurement\n")
    elif change == "missing":
        report.unlink()
    elif change in {"empty", "oversized", "not-utf8", "wrong-heading", "failed", "missing-result"}:
        body = {
            "empty": b"",
            "oversized": b"x" * 1_000_001,
            "not-utf8": b"\xff",
            "wrong-heading": b"# Other gate\n\nRESULT: printable at this wall\n",
            "failed": b"# Thickness and hollow\n\nRESULT: WALL BELOW MINIMUM\n",
            "missing-result": b"# Thickness and hollow\n\n| wall | PASS |\n",
        }[change]
        report.write_bytes(body)
        bindings[relative] = digest(body)
    elif change == "file-link":
        target = project / "outside.md"
        report.rename(target)
        report.symlink_to(target)
    elif change == "directory-link":
        target = project / "other-measure"
        (project / "measure").rename(target)
        (project / "measure").symlink_to(target, target_is_directory=True)
    elif change == "directory-report":
        report.unlink()
        report.mkdir()
    elif change in {"absolute", "traversal", "nested", "backslash", "unknown-gate"}:
        key = {
            "absolute": str(report), "traversal": "measure/../thickness-body.md",
            "nested": "measure/rounds/thickness-body.md",
            "backslash": "measure/thickness-\\body.md", "unknown-gate": "measure/mesh-body.md",
        }[change]
        bindings[key] = bindings.pop(relative)
    content = write_review(project, review)
    if change == "noncanonical":
        (project / "snap/SIGNATURE-REVIEW.json").write_bytes(content + b"\n")
    refuse_both(project)


def run_print_gates(project):
    runner = VERIFIER["Runner"](cwd=project.parent, dry_run=False, verbose=False)
    result = VERIFIER["_run_print_gates"](
        runner, project, [project / "part_body.step.py"], bed=(220., 220., 220.),
        nozzle=.4, skip_thickness=False, overhang_angle=45.,
    )
    assert result == 0
    assert len(runner.records) == 3


def test_real_canonical_gate_reports_survive_identical_rerun_and_both_validators(paper_project):
    project, review = paper_project
    (project / "part_body.step.py").write_text(
        "from build123d import Box\ndef gen_step():\n    return Box(4, 4, 4)\n"
    )
    run_print_gates(project)
    original = {relative: (project / relative).read_bytes() for relative in review["print_gate_sha256s"]}
    review["print_gate_sha256s"] = {relative: digest(body) for relative, body in original.items()}
    content = write_review(project, review)
    validate_both(project, content)
    run_print_gates(project)
    assert original == {relative: (project / relative).read_bytes() for relative in original}
    validate_both(project, content)
    # Host replay starts with the exact sealed review, then allows only the
    # directory prefixes that necessarily change in an isolated project.
    relocated = project.parent / "host-replay" / "project"
    shutil.copytree(project, relocated)
    assert VERIFIER["_required_signature_review"](relocated) == digest(content)
    run_print_gates(relocated)
    assert (relocated / "snap/SIGNATURE-REVIEW.json").read_bytes() == content
    for relative, before in original.items():
        after = (relocated / relative).read_bytes()
        assert after != before
        normalized = _print_gate_report_without_location(before, relative)
        assert normalized == _print_gate_report_without_location(after, relative)
        assert normalized != _print_gate_report_without_location(after + b"changed measurement\n", relative)
    assert _print_gate_report_without_location(original["measure/thickness-body.md"], "measure/thickness-body.md") != _print_gate_report_without_location(
        (relocated / "measure/thickness-body.md").read_bytes().replace(b"--nozzle 0.4", b"--nozzle 0.6"),
        "measure/thickness-body.md",
    )
    # A round report copied into place has a different command identity.
    relative = "measure/thickness-body.md"
    (project / relative).write_bytes(original[relative].replace(
        b"--report proj/measure/thickness-body.md", b"--report proj/measure/rounds/r1/thickness-body.md"
    ))
    assert (project / relative).read_bytes() != original[relative]
    refuse_both(project)


@pytest.mark.parametrize("gate,source,expected", [
    ("thickness", "Box(8, 8, .3)", "RESULT: WALL BELOW MINIMUM"),
    ("overhang", "Box(2, 2, 6).translate((0, 0, 3)) + Box(18, 18, 2).translate((0, 0, 7))", "RESULT: NEEDS SUPPORT"),
])
def test_real_failed_gate_serializes_its_failure_without_changing_exit(gate, source, expected, tmp_path):
    entry = tmp_path / "part_body.step.py"
    entry.write_text(f"from build123d import Box\ndef gen_step():\n    return {source}\n")
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / f"check_{gate}"), entry.name, "--report", f"{gate}.md"],
        cwd=tmp_path, capture_output=True, text=True, check=False, timeout=60,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert expected in result.stdout.splitlines()
    assert expected in (tmp_path / f"{gate}.md").read_text().splitlines()


def test_final_receipt_identifies_schema8(paper_project, monkeypatch, capsys):
    project, _ = paper_project
    content = (project / "snap/SIGNATURE-REVIEW.json").read_bytes()
    monkeypatch.chdir(project.parent)

    with mock.patch.object(VERIFIER["Runner"], "command", return_value=0), mock.patch.dict(
        VERIFIER["main"].__globals__, {"_final": lambda *args, **kwargs: 0}
    ):
        result = VERIFIER["main"]([project.name])
    output = capsys.readouterr()
    assert result == 0
    assert f"schema=8 sha256={digest(content)}" in output.out
    validate_both(project, content)


def test_invalid_bound_report_stops_main_before_geometry(paper_project, monkeypatch):
    project, _ = paper_project
    (project / "measure/thickness-body.md").write_text("changed")
    monkeypatch.chdir(project.parent)
    with mock.patch.object(VERIFIER["Runner"], "command") as command:
        with pytest.raises(SystemExit):
            VERIFIER["main"]([project.name])
    command.assert_not_called()
