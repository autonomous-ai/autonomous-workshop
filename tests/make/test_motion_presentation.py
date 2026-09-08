import hashlib
import io
import json
import runpy
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from build123d import Box, Compound, Location

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
HELPER = runpy.run_path(str(TOOLS / "motion_presentation.py"))
STATES = runpy.run_path(str(TOOLS / "motion_states.py"))


def condition(ident="turn", part="driver", steps=8):
    return {"id": ident, "check": "coupled_motion_collision", "inputs": {
        "steps": steps, "movers": [{"part": part, "rotation": {
            "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 90}}],
        "obstacle_parts": ["frame"]}}


def fixture(project, *, multiple=False):
    (project / "measure").mkdir()
    (project / "model.step.py").write_text('''from build123d import Box, Compound
def gen_step():
    driver = Box(2, 1, 1).translate((4, 0, 0))
    driver.label = "driver"
    driver.color = (0.8, 0.05, 0.01)
    frame = Box(2, 2, 1).translate((0, 0, -3))
    frame.label = "frame"
    frame.color = (0.01, 0.1, 0.8)
    return Compound(children=[driver, frame], label="root")
''')
    conditions = [condition()]
    if multiple:
        second = condition("reverse")
        second["inputs"]["movers"][0]["rotation"]["end_deg"] = -90
        conditions.append(second)
    (project / "measure/motion.json").write_text(json.dumps({"assembly": "model.step.py", "conditions": conditions}))
    evidence = HELPER["generate"](project, size=256)
    signature = {"concept_sha256": "a" * 64, "reviewer": "synthetic-test-critic", "review_rounds": 1}
    review = {"schema_version": 1, **signature, "evidence_sha256": hashlib.sha256(HELPER["canonical"](evidence)).hexdigest(),
              "blind_motion_read": "Synthetic test fixture: the block moves around the stationary base.",
              "motion_matches_wish": True, "simulation_not_physical_test": True}
    (project / HELPER["REVIEW"]).write_bytes(HELPER["canonical"](review))
    return signature


def rebind_test_evidence(project, evidence):
    """A synthetic reviewer attests to altered bytes; geometry must still decide."""
    raw = HELPER["canonical"](evidence)
    (project / HELPER["EVIDENCE"]).write_bytes(raw)
    review = json.loads((project / HELPER["REVIEW"]).read_bytes())
    review["evidence_sha256"] = hashlib.sha256(raw).hexdigest()
    (project / HELPER["REVIEW"]).write_bytes(HELPER["canonical"](review))


def test_declared_states_and_animation_reconcile(tmp_path):
    HELPER["validate"](tmp_path, fixture(tmp_path))


@pytest.mark.parametrize("path", ["model.step.py", "measure/motion-states/state-000.stl", "measure/motion.json", "snap/motion.gif", HELPER["EVIDENCE"]])
def test_changed_bytes_fail(tmp_path, path):
    signature = fixture(tmp_path)
    target = tmp_path / path
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError):
        HELPER["validate"](tmp_path, signature)


@pytest.mark.parametrize("field,value", [("motion_matches_wish", False), ("simulation_not_physical_test", False), ("reviewer", "root"), ("review_rounds", 3), ("concept_sha256", "b" * 64), ("blind_motion_read", "")])
def test_independent_review_cannot_be_bypassed(tmp_path, field, value):
    signature = fixture(tmp_path)
    path = tmp_path / HELPER["REVIEW"]
    review = json.loads(path.read_bytes()); review[field] = value
    path.write_bytes(HELPER["canonical"](review))
    with pytest.raises(ValueError):
        HELPER["validate"](tmp_path, signature)


def test_rehashed_wrong_state_is_rejected(tmp_path):
    signature = fixture(tmp_path)
    evidence = json.loads((tmp_path / HELPER["EVIDENCE"]).read_bytes())
    original, target = evidence["states"][:2]
    (tmp_path / target["path"]).write_bytes((tmp_path / original["path"]).read_bytes())
    target["sha256"] = HELPER["digest"](tmp_path, target["path"])
    rebind_test_evidence(tmp_path, evidence)
    with pytest.raises(ValueError, match="differs from the checked poses"):
        HELPER["validate"](tmp_path, signature)


def test_rehashed_unrelated_animation_is_rejected(tmp_path):
    signature = fixture(tmp_path)
    evidence = json.loads((tmp_path / HELPER["EVIDENCE"]).read_bytes())
    images = [Image.new("RGB", (256, 256), (i * 25, 100, 200)) for i in range(8)]
    stream = io.BytesIO()
    images[0].save(stream, format="GIF", save_all=True, append_images=images[1:], duration=120, loop=0)
    (tmp_path / "snap/motion.gif").write_bytes(stream.getvalue())
    evidence["animation_sha256"] = hashlib.sha256(stream.getvalue()).hexdigest()
    rebind_test_evidence(tmp_path, evidence)
    with pytest.raises(ValueError, match="differs from its reconciled geometry"):
        HELPER["validate"](tmp_path, signature)


def test_every_coupled_condition_is_covered(tmp_path):
    signature = fixture(tmp_path, multiple=True)
    HELPER["validate"](tmp_path, signature)
    evidence = json.loads((tmp_path / HELPER["EVIDENCE"]).read_bytes())
    evidence["states"] = [s for s in evidence["states"] if s["condition_id"] == "turn"]
    rebind_test_evidence(tmp_path, evidence)
    with pytest.raises(ValueError, match="every coupled condition"):
        HELPER["validate"](tmp_path, signature)


def test_legacy_hash_only_evidence_is_not_promoted(tmp_path):
    signature = fixture(tmp_path)
    evidence = json.loads((tmp_path / HELPER["EVIDENCE"]).read_bytes())
    evidence["schema_version"] = 1
    rebind_test_evidence(tmp_path, evidence)
    with pytest.raises(ValueError, match="schema 2"):
        HELPER["validate"](tmp_path, signature)


def test_missing_and_linked_evidence_fail(tmp_path):
    signature = fixture(tmp_path)
    path = tmp_path / "measure/motion-states/state-000.stl"
    path.unlink()
    with pytest.raises(OSError):
        HELPER["validate"](tmp_path, signature)
    path.symlink_to(tmp_path / "measure/motion-states/state-001.stl")
    with pytest.raises(ValueError, match="linked"):
        HELPER["validate"](tmp_path, signature)


def test_static_and_assembly_only_do_not_require_operating_animation(tmp_path):
    HELPER["validate"](tmp_path, {})
    (tmp_path / "measure").mkdir()
    (tmp_path / "measure/motion.json").write_text('{"conditions":[{"check":"assembly_sequence"}]}')
    HELPER["validate"](tmp_path, {})


def test_nested_coupled_motion_is_required(tmp_path):
    (tmp_path / "measure").mkdir()
    (tmp_path / "measure/motion.json").write_text(json.dumps({"conditions": [{"check": "assembly_sequence", "inputs": {"steps": [condition()]}}]}))
    with pytest.raises(OSError):
        HELPER["validate"](tmp_path, {})


def nested_model():
    pin = Box(2, 2, 2).translate((2, 0, 0)); pin.label = "pin"
    module = Compound(children=[pin], label="module")
    module.location = Location((10, 0, 0), (0, 0, 90))
    module.color = (0.8, 0.05, 0.01)
    root = Compound(children=[module], label="root")
    root.location = Location((0, 20, 0), (0, 0, 90))
    return root


def center(occurrences):
    points = np.concatenate([p for p, _, _ in occurrences])
    return (points.min(axis=0) + points.max(axis=0)) / 2


def test_nested_group_nonuniform_rotation_then_translation():
    model = nested_model()
    c = condition(part="root.module", steps=7)
    mover = c["inputs"]["movers"][0]
    mover["rotation"]["angles_deg"] = [0, 3, 10, 20, 40, 60, 80, 90]
    mover["translation"] = {"offsets_mm": [[0, 0, 0]] * 7 + [[1, 2, 0]]}
    states = list(STATES["posed_occurrences"](model, c, list(range(8))))
    np.testing.assert_allclose(center(states[0][1]), [-2, 30, 0], atol=1e-8)
    np.testing.assert_allclose(center(states[-1][1]), [-29, 0, 0], atol=1e-8)
    assert states[0][1][0][2][0] > states[0][1][0][2][2]
    original = STATES["helpers"]()[0]["index_parts"](model)["pin"]
    np.testing.assert_allclose(tuple(original.bounding_box().center()), [-2, 30, 0], atol=1e-8)


@pytest.mark.parametrize("name", ["pin", "root.module.pin", "module"])
def test_overlapping_mover_aliases_and_groups_are_rejected(name):
    c = condition(part="root.module", steps=7)
    extra = json.loads(json.dumps(c["inputs"]["movers"][0])); extra["part"] = name
    c["inputs"]["movers"].append(extra)
    with pytest.raises(ValueError, match="overlap"):
        list(STATES["posed_occurrences"](nested_model(), c, list(range(8))))


def test_repeated_labels_require_a_unique_path():
    a = Box(1, 1, 1); a.label = "pin"
    b = Box(1, 1, 1).translate((5, 0, 0)); b.label = "pin"
    model = Compound(label="root", children=[Compound(label="a", children=[a]), Compound(label="b", children=[b])])
    with pytest.raises(ValueError, match="ambiguous"):
        list(STATES["posed_occurrences"](model, condition(part="pin"), list(range(8))))
    states = list(STATES["posed_occurrences"](model, condition(part="root.a.pin"), list(range(8))))
    assert len(states) == 8 and len(states[0][1]) == 2


@pytest.mark.parametrize("indices", [[0]*8, list(range(7)), [0,1,2,3,4,5,6,99], [False,1,2,3,4,5,6,7], list(reversed(range(8)))])
def test_invalid_samples_are_rejected(indices):
    with pytest.raises(ValueError):
        STATES["sample_indices"](condition(), indices)


def test_stl_encoding_preserves_winding_and_ignores_triangle_order():
    points = np.array([[0,0,0], [1,0,0], [0,1,0], [0,0,1]], dtype=float)
    faces = np.array([[0,1,2], [0,3,1]])
    first = STATES["stl_bytes"]([(points, faces, (100,100,100))])
    shuffled = STATES["stl_bytes"]([(points, np.roll(faces[::-1], 1, axis=1), (100,100,100))])
    reversed_winding = STATES["stl_bytes"]([(points, faces[:, ::-1], (100,100,100))])
    assert first == shuffled and first != reversed_winding


def test_fixed_framing_preserves_translation():
    renderer = STATES["helpers"]()[1]
    shape = Box(2, 2, 2)
    first = renderer["tessellate_occurrences"](shape, .08)
    second = renderer["tessellate_occurrences"](shape.translate((4, 0, 0)), .08)
    framing = np.concatenate([p for p, _, _ in first + second])
    a = np.asarray(renderer["render"](first, -90, 0, 256, .07, framing=framing))
    b = np.asarray(renderer["render"](second, -90, 0, 256, .07, framing=framing))
    assert np.mean(np.abs(a.astype(float) - b)) > 2


def test_final_verifier_refuses_missing_motion_review_before_geometry(tmp_path):
    verifier = runpy.run_path(str(TOOLS / "verify_project"))
    project = verifier["_sc_project"](tmp_path)
    (project / "measure/motion.json").write_text('{"conditions":[{"check":"coupled_motion_collision"}]}')
    result = subprocess.run([sys.executable, str(TOOLS / "verify_project"), str(project)], cwd=project, capture_output=True, text=True)
    assert result.returncode == 2 and "MOTION-EVIDENCE.json" in result.stderr
    assert "check_layout" not in result.stdout


def test_cli_constructs_states_without_an_extra_generator(tmp_path):
    fixture(tmp_path)
    result = subprocess.run([sys.executable, str(TOOLS / "motion_presentation.py"), str(tmp_path), "--size", "256", "--samples", "turn=0,1,2,3,4,5,6,8"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    evidence = json.loads((tmp_path / HELPER["EVIDENCE"]).read_bytes())
    assert evidence["schema_version"] == 2 and len(evidence["states"]) == 8
    assert evidence["states"][-1]["sample_index"] == 8


def test_unlabelled_root_preserves_child_identity():
    driver = Box(2, 2, 2).translate((4, 0, 0)); driver.label = "driver"
    model = Compound(children=[driver])
    model.location = Location((0, 10, 0))
    states = list(STATES["posed_occurrences"](model, condition(steps=7), list(range(8))))
    np.testing.assert_allclose(center(states[0][1]), [4, 10, 0], atol=1e-8)
    np.testing.assert_allclose(center(states[-1][1]), [-10, 4, 0], atol=1e-8)


@pytest.mark.parametrize("frames", [0, 1, 7, 49, True, 8.5])
def test_invalid_frame_counts_fail_before_sampling(frames):
    with pytest.raises(ValueError):
        STATES["sample_indices"](condition(), frames=frames)


def test_nonfinite_mover_is_rejected_before_geometry():
    c = condition()
    c["inputs"]["movers"][0]["rotation"]["end_deg"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        list(STATES["posed_occurrences"](nested_model(), c, list(range(8))))
