"""The final CAD verifier and Make finalizer must accept the same review bytes."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import runpy
from unittest import mock

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "src/workshop/make/skills/cad/scripts"
FINALIZER = ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"


@pytest.fixture
def review_project(tmp_path):
    verifier = runpy.run_path(str(SCRIPTS / "verify_project"))
    finalizer = runpy.run_path(str(FINALIZER))
    project = verifier["_sc_project"](tmp_path.resolve() / "product")
    review_path = project / "snap/SIGNATURE-REVIEW.json"
    review = json.loads(review_path.read_bytes())
    review["schema_version"] = 8
    review["print_gate_sha256s"] = {}
    return tmp_path.resolve(), project, review, verifier, finalizer


def save_review(project, review):
    content = json.dumps(review, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False, allow_nan=False).encode()
    (project / "snap/SIGNATURE-REVIEW.json").write_bytes(content)
    return content


def print_reports(project, review):
    reports = {
        "measure/thickness-widget.md": (
            "# Thickness and hollow\n\n"
            "widget.step.py --nozzle 0.4 --report measure/thickness-widget.md\n"
            "RESULT: printable at this wall\n"
        ),
        "measure/overhang-widget.md": (
            "# Overhang and support\n\n"
            "widget.step.py --angle 45.0 --report measure/overhang-widget.md\n"
            "RESULT: prints unsupported\n"
        ),
    }
    for relative, text in reports.items():
        content = text.encode()
        (project / relative).write_bytes(content)
        review["print_gate_sha256s"][relative] = hashlib.sha256(content).hexdigest()


def validators(fixture):
    root, project, _, verifier, finalizer = fixture
    return (
        (ValueError, lambda: verifier["_required_signature_review"](project)),
        (finalizer["ProposalError"], lambda: finalizer["_validate_signature_review"](
            root, product_root_value="product", cad_project_path=PurePosixPath("proj"),
            concept_sha256="0" * 64)),
    )


def assert_both_reject(fixture):
    for exception, validate in validators(fixture):
        with pytest.raises(exception):
            validate()


@pytest.mark.parametrize("with_print_reports", [False, True])
def test_same_schema8_review_passes_both_contracts(review_project, with_print_reports):
    _, project, review, _, _ = review_project
    if with_print_reports:
        print_reports(project, review)
    content = save_review(project, review)
    (_, verifier), (_, finalizer) = validators(review_project)
    assert verifier() == hashlib.sha256(content).hexdigest()
    assert finalizer() is None
    assert (project / "snap/SIGNATURE-REVIEW.json").read_bytes() == content


@pytest.mark.parametrize("change", ["legacy", "missing", "extra", "float", "bool"])
def test_schema8_requires_exact_identity_and_fields(review_project, change):
    _, project, review, _, _ = review_project
    if change == "legacy":
        review["schema_version"] = 7
        del review["print_gate_sha256s"]
    elif change == "missing":
        del review["print_gate_sha256s"]
    elif change == "extra":
        review["extra"] = None
    else:
        review["schema_version"] = 8.0 if change == "float" else True
    save_review(project, review)
    assert_both_reject(review_project)


@pytest.mark.parametrize("change", ["missing", "stale", "different", "nozzle", "source"])
def test_review_binds_exact_existing_report_bytes(review_project, change):
    _, project, review, _, _ = review_project
    print_reports(project, review)
    report = project / "measure/thickness-widget.md"
    if change == "missing":
        report.unlink()
    elif change == "stale":
        report.write_bytes(report.read_bytes() + b"changed measurement\n")
    elif change == "different":
        review["print_gate_sha256s"]["measure/thickness-widget.md"] = "f" * 64
    else:
        old, new = (("--nozzle 0.4", "--nozzle 0.6") if change == "nozzle"
                    else ("widget.step.py", "other.step.py"))
        report.write_text(report.read_text().replace(old, new))
    save_review(project, review)
    assert_both_reject(review_project)


@pytest.mark.parametrize("bindings", [None, [], {"measure/thickness-widget.md": None},
                                      {"measure/thickness-widget.md": "A" * 64}])
def test_review_requires_report_to_sha256_map(review_project, bindings):
    _, project, review, _, _ = review_project
    review["print_gate_sha256s"] = bindings
    save_review(project, review)
    assert_both_reject(review_project)


@pytest.mark.parametrize("path", ["../thickness-widget.md", "/measure/thickness-widget.md",
    "measure/nested/thickness-widget.md", "measure/./thickness-widget.md",
    "measure//thickness-widget.md", "measure/thickness-\\widget.md",
    "measure/thickness-\nwidget.md", "measure/mesh-widget.md", "measure/thickness-widget.txt"])
def test_review_rejects_noncanonical_or_unknown_report_paths(review_project, path):
    _, project, review, _, _ = review_project
    review["print_gate_sha256s"] = {path: "0" * 64}
    save_review(project, review)
    assert_both_reject(review_project)


@pytest.mark.parametrize("change", ["one_gate", "wrong_title", "failing", "binary", "empty", "oversize"])
def test_exact_digest_cannot_qualify_invalid_or_incomplete_gate_evidence(review_project, change):
    _, project, review, _, _ = review_project
    print_reports(project, review)
    if change == "one_gate":
        del review["print_gate_sha256s"]["measure/overhang-widget.md"]
    else:
        content = {
            "wrong_title": b"# Other audit\nRESULT: printable at this wall\n",
            "failing": b"# Thickness and hollow\nRESULT: too thin\n",
            "binary": b"# Thickness and hollow\n\xff\nRESULT: printable at this wall\n",
            "empty": b"",
            "oversize": b"x" * 1_000_001,
        }[change]
        (project / "measure/thickness-widget.md").write_bytes(content)
        review["print_gate_sha256s"]["measure/thickness-widget.md"] = hashlib.sha256(content).hexdigest()
    save_review(project, review)
    assert_both_reject(review_project)


@pytest.mark.parametrize("linked_directory", [False, True])
def test_review_rejects_report_and_measure_directory_symlinks(review_project, linked_directory):
    root, project, review, _, _ = review_project
    print_reports(project, review)
    if linked_directory:
        measure = project / "measure"
        target = root / "external-measure"
        measure.rename(target)
        measure.symlink_to(target, target_is_directory=True)
    else:
        report = project / "measure/thickness-widget.md"
        target = root / "external-thickness.md"
        report.rename(target)
        report.symlink_to(target)
    save_review(project, review)
    assert_both_reject(review_project)


@pytest.mark.parametrize("filename", ["iso.png", "signature.png"])
def test_schema8_keeps_exact_reviewed_image_binding(review_project, filename):
    _, project, review, _, _ = review_project
    save_review(project, review)
    (project / "snap" / filename).write_bytes(b"different view")
    assert_both_reject(review_project)


def test_stale_report_refuses_before_final_cad_execution(review_project, capsys, monkeypatch):
    root, project, review, verifier, _ = review_project
    monkeypatch.chdir(root)
    print_reports(project, review)
    (project / "measure/thickness-widget.md").write_bytes(b"new report")
    save_review(project, review)
    with mock.patch.object(verifier["Runner"], "command") as command:
        with pytest.raises(SystemExit) as stopped:
            verifier["main"]([str(project), "--print-gates", "--nozzle", "0.6", "--no-report"])
    assert stopped.value.code == 2
    command.assert_not_called()
    assert "not bound to the exact thickness report" in capsys.readouterr().err


def test_schema8_gate_does_not_change_final_print_source_or_nozzle(review_project):
    _, project, review, verifier, _ = review_project
    print_reports(project, review)
    save_review(project, review)
    verifier["_required_signature_review"](project)
    runner = mock.Mock(cwd=project)
    runner.command.return_value = 0
    result = verifier["_run_print_gates"](runner, project, [project / "widget.step.py"],
        bed=(220.0, 220.0, 220.0), nozzle=0.6, skip_thickness=False, overhang_angle=50.0)
    assert result == 0
    commands = [[str(value) for value in call.args[0]] for call in runner.command.call_args_list]
    assert [Path(command[1]).name for command in commands] == [
        "check_mesh", "check_overhang", "check_thickness"]
    assert all(command[2] == "widget.step.py" for command in commands)
    assert commands[1][3:] == ["--angle", "50.0", "--report", "measure/overhang-widget.md"]
    assert commands[2][3:] == ["--nozzle", "0.6", "--report", "measure/thickness-widget.md"]
