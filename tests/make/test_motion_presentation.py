import hashlib
import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
HELPER = runpy.run_path(str(TOOLS / "motion_presentation.py"))


def fixture(project):
    (project / "snap").mkdir()
    (project / "measure").mkdir()
    (project / "cam.step.py").write_text("def gen_step(): return None\n")
    (project / "measure/motion.json").write_text(json.dumps({"conditions": [{"check": "coupled_motion_collision"}]}))
    states = []
    for i in range(8):
        path = f"measure/state-{i}.stl"
        (project / path).write_bytes(f"mock exact state {i}".encode())
        states.append({"path": path, "sha256": HELPER["digest"](project, path)})
    frames = [Image.new("RGB", (256, 256), (i * 25, 100, 200)) for i in range(8)]
    frames[0].save(project / "snap/motion.gif", save_all=True, append_images=frames[1:], duration=120, loop=0)
    evidence = {"schema_version": 1, "kind": "exact-cad-state-animation", "sources": HELPER["sources"](project), "states": states, "animation_sha256": HELPER["digest"](project, "snap/motion.gif"), "motion_sha256": HELPER["digest"](project, "measure/motion.json")}
    raw = HELPER["canonical"](evidence)
    (project / HELPER["EVIDENCE"]).write_bytes(raw)
    signature = {"concept_sha256": "a" * 64, "reviewer": "independent", "review_rounds": 1}
    review = {"schema_version": 1, **signature, "evidence_sha256": hashlib.sha256(raw).hexdigest(), "blind_motion_read": "The cam lifts a follower.", "motion_matches_wish": True, "simulation_not_physical_test": True}
    (project / HELPER["REVIEW"]).write_bytes(HELPER["canonical"](review))
    return signature


def test_exact_motion_evidence_passes(tmp_path):
    HELPER["validate"](tmp_path, fixture(tmp_path))


@pytest.mark.parametrize("path", ["cam.step.py", "measure/state-0.stl", "measure/motion.json", "snap/motion.gif", "snap/MOTION-EVIDENCE.json"])
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
    review = json.loads(path.read_bytes())
    review[field] = value
    path.write_bytes(HELPER["canonical"](review))
    with pytest.raises(ValueError):
        HELPER["validate"](tmp_path, signature)


def test_missing_and_linked_evidence_fail(tmp_path):
    signature = fixture(tmp_path)
    path = tmp_path / "measure/state-0.stl"
    path.unlink()
    with pytest.raises(OSError):
        HELPER["validate"](tmp_path, signature)
    path.symlink_to(tmp_path / "measure/state-1.stl")
    with pytest.raises(ValueError, match="linked"):
        HELPER["validate"](tmp_path, signature)


def test_static_and_assembly_only_do_not_require_operating_animation(tmp_path):
    HELPER["validate"](tmp_path, {})
    (tmp_path / "measure").mkdir()
    (tmp_path / "measure/motion.json").write_text('{"conditions":[{"check":"assembly_sequence"}]}')
    HELPER["validate"](tmp_path, {})


def test_fixed_framing_preserves_translation():
    import numpy as np
    renderer = runpy.run_path(str(TOOLS / "render_product"))
    mesh = renderer["_cube_triangles"]()
    shifted = mesh + np.array([4, 0, 0])
    framing = np.concatenate([mesh.reshape(-1, 3), shifted.reshape(-1, 3)])
    kwargs = dict(size=256, view="front", base=(40, 150, 150), accent=(220, 170, 60), background=(240, 240, 240), framing=framing)
    first = np.asarray(renderer["render"](mesh, **kwargs))
    second = np.asarray(renderer["render"](shifted, **kwargs))
    assert np.mean(np.abs(first.astype(float) - second)) > 2


def test_final_verifier_refuses_missing_motion_review_before_geometry(tmp_path):
    verifier = runpy.run_path(str(TOOLS / "verify_project"))
    project = verifier["_sc_project"](tmp_path)
    (project / "measure/motion.json").write_text('{"conditions":[{"check":"coupled_motion_collision"}]}')
    result = subprocess.run([sys.executable, str(TOOLS / "verify_project"), str(project)], cwd=project, capture_output=True, text=True)
    assert result.returncode == 2
    assert "MOTION-EVIDENCE.json" in result.stderr, result.stderr
    assert "check_layout" not in result.stdout


def test_renderer_cli_writes_reviewable_actual_state_animation(tmp_path):
    import numpy as np
    renderer = runpy.run_path(str(TOOLS / "render_product"))
    (tmp_path / "measure").mkdir()
    (tmp_path / "cam.step.py").write_text("# synthetic renderer test source\n")
    (tmp_path / "measure/motion.json").write_text('{"conditions":[]}')
    args = []
    for index in range(8):
        triangles = renderer["_cube_triangles"]() + np.array([index * 0.5, 0, 0])
        lines = ["solid fixture"]
        for tri in triangles:
            lines.extend(["facet normal 0 0 0", "outer loop"])
            lines.extend("vertex %g %g %g" % tuple(v) for v in tri)
            lines.extend(["endloop", "endfacet"])
        lines.append("endsolid fixture")
        relative = f"measure/state-{index}.stl"
        (tmp_path / relative).write_text("\n".join(lines))
        args.extend(["--state-stl", relative])
    result = subprocess.run([sys.executable, str(TOOLS / "motion_presentation.py"), str(tmp_path), *args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    with Image.open(tmp_path / "snap/motion.gif") as animation:
        assert animation.n_frames == 8
    evidence = json.loads((tmp_path / HELPER["EVIDENCE"]).read_bytes())
    assert evidence["sources"] == HELPER["sources"](tmp_path)
    assert len(evidence["states"]) == 8
