"""Exercise real print measurements and their finalizer-facing report contract."""

import hashlib
import runpy
import sys
from pathlib import Path, PurePosixPath

import pytest
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "src/workshop/make/skills/cad/scripts"
FINALIZER = ROOT / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"


@pytest.mark.parametrize("failure_gate", [None, "thickness", "overhang"])
def test_measured_reports_agree_with_exit_status_and_finalizer(tmp_path, monkeypatch, failure_gate):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    overhang = runpy.run_path(str(SCRIPTS / "check_overhang"))
    box = overhang["_box"]
    project = tmp_path / "cad"
    (project / "measure").mkdir(parents=True)
    bindings = {}
    for gate in ("thickness", "overhang"):
        module = runpy.run_path(str(SCRIPTS / ("check_" + gate)))
        main = module["main"]
        geometry = box(0, 0, 0, 10, 10, 5)
        if gate == failure_gate:
            geometry = (box(0, 0, 0, 10, 10, 0.4) if gate == "thickness" else
                        box(0, 0, 0, 6, 20, 20) + box(6, 0, 14, 30, 20, 20))
        # Replace only CAD loading; real tessellation analysis, verdicts and
        # report serialization remain exercised on deterministic closed shapes.
        monkeypatch.setitem(main.__globals__, "resolve_single_entry", lambda _: project / "part_fixture.step.py")
        monkeypatch.setitem(main.__globals__, "entry_role", lambda _: "fixture")
        monkeypatch.setitem(main.__globals__, "entry_mesh", lambda *_: np.asarray(geometry, dtype=float))
        relative = f"measure/{gate}-fixture.md"
        report = project / relative
        monkeypatch.setattr(sys, "argv", ["check_" + gate, "part_fixture.step.py", "--report", str(report)])
        assert main() == int(gate == failure_gate)
        body = report.read_text()
        assert body.count("RESULT:") == 1
        verdict = ("WALL BELOW MINIMUM" if gate == "thickness" else "NEEDS SUPPORT") if gate == failure_gate else (
            "printable at this wall" if gate == "thickness" else "prints unsupported")
        assert f"RESULT: {verdict}\n" in body
        bindings[relative] = hashlib.sha256(report.read_bytes()).hexdigest()

    finalizer = runpy.run_path(str(FINALIZER))
    validate = finalizer["_validate_review_print_gates"]
    args = dict(review={"print_gate_sha256s": bindings}, project_relative=PurePosixPath("cad"))
    if failure_gate:
        with pytest.raises(finalizer["ProposalError"], match=f"failing {failure_gate}"):
            validate(tmp_path, **args)
    else:
        validate(tmp_path, **args)
