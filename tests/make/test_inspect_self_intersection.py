"""The eager OpenCascade check should run once and retain geometry findings."""
from pathlib import Path
import runpy

from build123d import Box, Compound, Pos
from OCP import BRepAlgoAPI
import pytest


VALIDITY = runpy.run_path(str(
    Path(__file__).resolve().parents[2]
    / "src/workshop/make/skills/cad/scripts/packages/cadgen/src/cadgen/validity.py"
))


def test_self_intersection_runs_one_eager_kernel_check(monkeypatch):
    constructor = BRepAlgoAPI.BRepAlgoAPI_Check
    invocations = []

    def eager_check(*args):
        checked = constructor(*args)
        invocations.append("constructor")

        class Checked:
            def Perform(self):
                invocations.append("repeat")
                checked.Perform()

            def IsValid(self):
                return checked.IsValid()

            def Result(self):
                return checked.Result()

        return Checked()

    monkeypatch.setattr(BRepAlgoAPI, "BRepAlgoAPI_Check", eager_check)
    assert VALIDITY["_is_self_intersecting"](Box(2, 2, 2).wrapped) is False
    assert invocations == ["constructor"]


@pytest.mark.parametrize("kind", ["sound", "overlap", "reversed", "open"])
def test_real_geometry_preserves_previous_check_findings(kind):
    shape = Box(2, 2, 2)
    if kind == "overlap":
        shape = Compound(children=[shape, Pos(1, 0, 0) * Box(2, 2, 2)])
    wrapped = shape.wrapped
    if kind == "reversed":
        wrapped = wrapped.Reversed()
    elif kind == "open":
        wrapped = shape.faces()[0].wrapped

    from OCP.BOPAlgo import BOPAlgo_CheckStatus

    previous = BRepAlgoAPI.BRepAlgoAPI_Check(wrapped, True, True)
    previous.Perform()
    baseline = False if previous.IsValid() else any(
        result.GetCheckStatus() == BOPAlgo_CheckStatus.BOPAlgo_SelfIntersect
        for result in previous.Result()
    )
    assert VALIDITY["_is_self_intersecting"](wrapped) is baseline
    findings = VALIDITY["check_occurrence_shape"](wrapped)["reasons"]
    if kind == "sound":
        assert findings == []
    else:
        expected = {
            "overlap": "selfIntersecting", "reversed": "nonPositiveVolume", "open": "noSolid",
        }[kind]
        assert expected in findings


def test_unavailable_kernel_check_remains_unknown(monkeypatch):
    def fail(*args):
        raise RuntimeError("injected kernel failure")

    monkeypatch.setattr(BRepAlgoAPI, "BRepAlgoAPI_Check", fail)
    assert VALIDITY["_is_self_intersecting"](Box(2, 2, 2).wrapped) is None
