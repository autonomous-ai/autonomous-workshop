"""Real source print gates must write the verdict consumed by Make's review."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import runpy
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "src/workshop/make/skills/cad/scripts"
FINALIZER = (
    ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"
)
GENERATOR = "gen_" + "step"
SHAPES = {
    None: "Box(8, 8, 2, align=(Align.MIN, Align.MIN, Align.MIN))",
    "overhang": (
        "Box(8, 8, 4, align=(Align.MIN, Align.MIN, Align.MIN)) - "
        "Pos(2, 0, 0) * Box(6, 8, 3, align=(Align.MIN, Align.MIN, Align.MIN))"
    ),
    "thickness": "Box(8, 8, 0.4, align=(Align.MIN, Align.MIN, Align.MIN))",
}
RESULTS = {
    "overhang": ("prints unsupported", "NEEDS SUPPORT"),
    "thickness": ("printable at this wall", "WALL BELOW MINIMUM"),
}


@pytest.fixture(scope="module")
def report_tools():
    return {
        name: runpy.run_path(str(path))
        for name, path in {
            "overhang": SCRIPTS / "check_overhang",
            "thickness": SCRIPTS / "check_thickness",
            "verifier": SCRIPTS / "verify_project",
            "finalizer": FINALIZER,
        }.items()
    }


def run_gate(tool, gate, project, monkeypatch, capsys):
    relative = f"measure/{gate}-fixture.md"
    option = ["--angle", "45.0"] if gate == "overhang" else ["--nozzle", "0.4"]
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "argv", [
        str(SCRIPTS / f"check_{gate}"), "part_fixture.step.py",
        *option, "--report", relative,
    ])
    # Exercise the real entry loader, B-rep tessellation, measurements and writer.
    # Only argv/cwd are supplied; no geometry, gate or verdict is mocked.
    result = tool["main"]()
    stdout = capsys.readouterr().out
    return result, stdout, relative, (project / relative).read_bytes()


@pytest.mark.parametrize("failure", [None, "overhang", "thickness"])
def test_real_report_verdicts_match_stdout_exit_and_schema8_review(
    tmp_path, monkeypatch, capsys, report_tools, failure,
):
    project = report_tools["verifier"]["_sc_project"](tmp_path / "product")
    (project / "part_fixture.step.py").write_text(
        "from build123d import Align, Box, Pos\n"
        "PRINTABLE = True\n"
        f"def {GENERATOR}():\n    return {SHAPES[failure]}\n"
    )
    review_path = project / "snap/SIGNATURE-REVIEW.json"
    review = json.loads(review_path.read_bytes())
    review["schema_version"] = 8
    review["print_gate_sha256s"] = {}

    for gate in RESULTS:
        result, stdout, relative, content = run_gate(
            report_tools[gate], gate, project, monkeypatch, capsys
        )
        expected = int(gate == failure)
        verdict = "RESULT: " + RESULTS[gate][expected]
        assert result == expected, stdout
        assert [line for line in stdout.splitlines() if line.startswith("RESULT:")] == [verdict]
        assert [line for line in content.decode().splitlines() if line.startswith("RESULT:")] == [verdict]
        assert f"--report {relative}".encode() in content
        review["print_gate_sha256s"][relative] = hashlib.sha256(content).hexdigest()
        if failure is None:
            # Same source, cwd and argv must reproduce the exact review-bound
            # bytes even though the B-rep is built and measured again.
            repeated, repeated_stdout, _, repeated_content = run_gate(
                report_tools[gate], gate, project, monkeypatch, capsys
            )
            assert repeated == result, repeated_stdout
            assert repeated_content == content

    review_path.write_bytes(json.dumps(
        review, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode())
    finalizer = report_tools["finalizer"]

    def validate():
        return finalizer["_validate_signature_review"](
            tmp_path, product_root_value="product", cad_project_path=PurePosixPath("proj"),
            concept_sha256="0" * 64,
        )

    if failure is None:
        assert validate() is None
    else:
        # A correct hash cannot turn a genuinely failing measurement into pass.
        with pytest.raises(finalizer["ProposalError"], match=f"cites a failing {failure}"):
            validate()
