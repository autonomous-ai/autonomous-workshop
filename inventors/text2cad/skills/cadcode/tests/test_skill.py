"""Self-contained tests for the cadcode skill.

Run from inside the skill directory:

    python -m pytest tests/

Requires the skill's runtime deps to be installed in the active Python
(see SETUP.md). Tests the scripts themselves — no FastAPI / web stuff.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
ASSETS = SKILL_DIR / "assets"


def _run_cad(*args: str, timeout: int = 40) -> dict:
    """Invoke ``python scripts/cad ...`` and parse the JSON result."""
    cmd = [sys.executable, str(SCRIPTS / "cad"), *args]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout
    )
    out = (proc.stdout or "").strip().splitlines()
    if not out:
        return {
            "ok": False,
            "error": {
                "code": "RUNTIME_ERROR",
                "message": f"no stdout (stderr: {proc.stderr[:300]!r})",
            },
        }
    return json.loads(out[-1])


def _err_message(payload: dict) -> str:
    """Pull the human-readable string out of either contract §3's
    ``error.message`` or the legacy flat ``error`` field."""
    err = payload.get("error")
    if isinstance(err, dict):
        return str(err.get("message", ""))
    return str(err or "")


# -- Smoke ------------------------------------------------------------------


def test_layout_intact():
    """SKILL.md + 3 references + 2 script entrypoints exist."""
    assert (SKILL_DIR / "SKILL.md").exists()
    assert (SKILL_DIR / "SETUP.md").exists()
    assert (SKILL_DIR / "requirements.txt").exists()
    for name in ("cadquery-modeling.md", "hobbyist-defaults.md", "repair-loop.md"):
        assert (SKILL_DIR / "references" / name).exists(), f"missing references/{name}"
    # The `render` script was removed when the canonical preview moved from
    # VTK PNGs to cadpy-produced GLBs (Workstream 2 / Track B).
    for name in ("cad", "check", "review"):
        assert (SCRIPTS / name / "__main__.py").exists(), f"missing scripts/{name}/__main__.py"
    assert not (SCRIPTS / "render").exists(), "scripts/render/ should be gone"


def test_help_works():
    """The CLI tools support ``--help``."""
    for tool in ("cad", "check", "review"):
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / tool), "--help"],
            capture_output=True, text=True, timeout=20,
        )
        assert proc.returncode == 0, f"{tool} --help failed: {proc.stderr}"
        assert "usage" in proc.stdout.lower()


# -- All example assets compile to valid solids -----------------------------


EXAMPLES = sorted((ASSETS).glob("example_*.py")) if ASSETS.exists() else []


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda p: p.stem)
def test_example_compiles(example: Path):
    """Every assets/example_*.py must compile to a valid solid AND produce
    the contract §3 artifact set (STEP + STL + metadata)."""
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(str(example), "--out-dir", tmp)
        assert payload.get("ok"), f"{example.name} failed: {payload}"
        assert payload.get("is_solid"), f"{example.name} non-solid"
        assert payload.get("volume_mm3", 0) > 0
        out = Path(tmp)
        assert (out / f"{example.stem}.step").exists()
        assert (out / f"{example.stem}.stl").exists()
        assert (out / f"{example.stem}.step.json").exists()
        # GLB / topology are no longer produced.
        assert not (out / f"{example.stem}.glb").exists()
        assert not (out / f"{example.stem}.topology.json").exists()
        # Payload paths echo the on-disk artifacts.
        assert "step_path" in payload
        assert "stl_path" in payload
        assert "metadata_path" in payload
        assert "glb_path" not in payload
        assert "topology_path" not in payload


# -- STEP/STP import mode ---------------------------------------------------


def test_step_file_is_imported_to_artifact_set():
    """Passing a ``.step`` file re-meshes the B-rep into the full contract §3
    artifact set (STEP + STL + metadata), keyed by the ``--stem`` override.

    The generator synthesizes a ``main.py`` that ``importStep``s the file, so
    this exercises the same shape path as a generated model — the app's STEP
    "Import" action rides on exactly this."""
    import cadquery as cq

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        source = tmp_p / "source_widget.step"
        cq.exporters.export(
            cq.Workplane("XY").box(20, 20, 5).faces(">Z").hole(6),
            str(source),
        )
        out = tmp_p / "out"
        payload = _run_cad(str(source), "--out-dir", str(out), "--stem", "imported")

        assert payload.get("ok"), f"STEP import failed: {payload}"
        assert payload.get("is_solid"), f"imported STEP non-solid: {payload}"
        assert payload.get("volume_mm3", 0) > 0
        assert (out / "imported.step").exists()
        assert (out / "imported.stl").exists()
        assert (out / "imported.step.json").exists()
        # The original is only read, never rewritten in place.
        assert source.exists()


def test_stp_extension_is_accepted():
    """The ``.stp`` spelling imports the same as ``.step``."""
    import cadquery as cq

    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        source = tmp_p / "part.stp"
        cq.exporters.export(
            cq.Workplane("XY").box(8, 8, 8), str(source), exportType="STEP"
        )
        payload = _run_cad(str(source), "--out-dir", str(tmp_p / "out"))
        assert payload.get("ok"), f"STP import failed: {payload}"
        assert (tmp_p / "out" / "part.step").exists()


# -- Mesh tolerance flag is wired through -----------------------------------


def test_mesh_tolerance_flag_is_respected():
    cube = ASSETS / "example_cube_with_hole.py"
    if not cube.exists():
        pytest.skip("no example_cube_with_hole.py asset")
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(
            str(cube), "--out-dir", tmp,
            "--mesh-tolerance", "0.05",
            "--angular-tolerance", "3.0",
        )
    assert payload["ok"]
    assert payload["mesh_tolerance"] == pytest.approx(0.05)
    # --angular-tolerance is a degrees-facing flag, but cadpy/OCCT expect
    # radians. The runner converts at the handoff (common/runner.py), so the
    # value that actually reaches cadpy (and is echoed back here) is the
    # radian equivalent. A missing conversion (the faceted-holes bug) would
    # leave this at 3.0 — i.e. 3 radians ~= 172 deg ~= no angular refinement.
    assert payload["angular_tolerance"] == pytest.approx(math.radians(3.0))


# -- Sandbox refuses forbidden imports --------------------------------------


def test_sandbox_rejects_os_import():
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "bad.py"
        bad.write_text("import os\nresult = os.listdir('/')\n")
        payload = _run_cad(str(bad), "--out-dir", tmp)
    assert not payload["ok"]
    msg = _err_message(payload).lower()
    assert "os" in msg
    assert "not allowed" in msg


def test_missing_result_variable():
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "noresult.py"
        bad.write_text("import cadquery as cq\nshape = cq.Workplane('XY').box(10,10,10)\n")
        payload = _run_cad(str(bad), "--out-dir", tmp)
    assert not payload["ok"]
    # cadpy raises ValidationError mentioning gen_step / result; surface
    # whichever appears.
    msg = _err_message(payload).lower()
    assert "result" in msg or "gen_step" in msg


def test_syntax_error_surfaces():
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "broken.py"
        # Unbalanced paren is a real SyntaxError; "this is not python" parses.
        bad.write_text("result = (\n")
        payload = _run_cad(str(bad), "--out-dir", tmp)
    assert not payload["ok"]
    msg = _err_message(payload).lower()
    assert "syntax" in msg or "unexpected" in msg


def test_infinite_loop_killed_by_timeout():
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "spin.py"
        bad.write_text("while True:\n    pass\n")
        payload = _run_cad(str(bad), "--out-dir", tmp, "--wall-clock-s", "8")
    assert not payload["ok"]
    msg = _err_message(payload).lower()
    assert (
        payload.get("timed_out") is True
        or "rlimit" in msg
        or "timeout" in msg
    )


# -- Project mode (multi-file via main.py + sibling modules) ---------------


def test_project_template_compiles():
    """The bundled project skeleton must compile end-to-end."""
    project = SKILL_DIR / "templates" / "project_skeleton"
    assert (project / "main.py").exists()
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(str(project), "--out-dir", tmp)
        assert payload.get("ok"), f"skeleton failed: {payload}"
        assert payload.get("is_solid"), "skeleton non-solid"
        assert payload.get("volume_mm3", 0) > 1000
        # Stem comes from the project directory name
        out = Path(tmp)
        assert (out / "project_skeleton.step").exists()
        assert (out / "project_skeleton.stl").exists()
        assert (out / "project_skeleton.step.json").exists()
        assert not (out / "project_skeleton.glb").exists()
        assert not (out / "project_skeleton.topology.json").exists()


def test_project_mode_requires_main_py():
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "empty"
        proj.mkdir()
        payload = _run_cad(str(proj), "--out-dir", tmp)
    assert not payload["ok"]
    assert "main.py" in _err_message(payload)


def test_project_local_imports_work():
    """A two-file project where main.py imports a sibling module."""
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "tiny"
        proj.mkdir()
        (proj / "thing.py").write_text(
            "import cadquery as cq\n"
            "def make(size): return cq.Workplane('XY').box(size, size, size)\n"
        )
        (proj / "main.py").write_text(
            "from thing import make\nresult = make(15.0)\n"
        )
        payload = _run_cad(str(proj), "--out-dir", tmp)
    assert payload.get("ok"), f"failed: {payload}"
    assert payload.get("volume_mm3", 0) == pytest.approx(15 ** 3, rel=1e-3)


def test_project_mode_still_denies_dangerous_imports():
    """A project main.py that tries to `import os` must still fail."""
    with tempfile.TemporaryDirectory() as tmp:
        proj = Path(tmp) / "bad_proj"
        proj.mkdir()
        (proj / "main.py").write_text("import os\nresult = os.listdir('/')\n")
        payload = _run_cad(str(proj), "--out-dir", tmp)
    assert not payload["ok"]
    assert "os" in _err_message(payload)


# -- Pattern library (references/patterns/*.md) -----------------------------


PATTERN_NAMES = [
    "snap-fit-cantilever",
    "living-hinge",
    "press-fit-pocket",
    "dovetail-slide",
    "screw-boss",
    "heat-set-insert-pocket",
    "nut-trap",
    "rib-stiffener",
    "fillet-stress-relief",
    "wall-thickness-rules",
    "print-orientation",
    "overhang-relief",
    "draft-angle",
    "magnet-pocket",
    "bearing-seat",
    "cable-channel",
    "anchor-to-body",
    "four-bar-linkage",
    "unified-radius",
    "surface-continuity",
    "print-in-place",
]


# Patterns whose geometry is owned by a `cadlib` helper. Their docs must point
# the model AT the helper (the package is the source of truth — SKILL.md), not
# ship a copy-paste reimplementation.
HELPER_BACKED_PATTERNS = {
    "snap-fit-cantilever",
    "press-fit-pocket",
    "dovetail-slide",
    "screw-boss",
    "heat-set-insert-pocket",
    "nut-trap",
    "rib-stiffener",
    "magnet-pocket",
    "bearing-seat",
    "cable-channel",
    "four-bar-linkage",
    "unified-radius",
    "surface-continuity",
    "print-in-place",
}
# Patterns with no helper: the doc IS the deliverable, so it carries a real
# CadQuery template. `fillet-stress-relief` is the lone knowledge-only doc — it
# defers all CadQuery filleting mechanics to `references/cadquery-modeling.md`.
KNOWLEDGE_ONLY_PATTERNS = {"fillet-stress-relief"}


@pytest.mark.parametrize("pattern", PATTERN_NAMES)
def test_pattern_doc_exists_and_has_required_sections(pattern: str):
    """Each pattern doc lives at the canonical path and has the sections the
    loader relies on when reading it on demand. Every doc has Trigger, Why this
    exists, and Pitfalls. The code section depends on the doc's kind:

    * helper-backed → a `## Use the helper` section importing `from cadlib`
      (the package is the source of truth; no copy-paste reimplementation);
    * knowledge-only (`fillet-stress-relief`) → neither, by design;
    * otherwise → a `## CadQuery template` section that imports cadquery.
    """
    path = SKILL_DIR / "references" / "patterns" / f"{pattern}.md"
    assert path.exists(), f"missing pattern doc: {path}"
    text = path.read_text()
    assert f"# {pattern}" in text, f"{pattern}.md missing H1 heading"
    assert "**Trigger:**" in text, f"{pattern}.md missing **Trigger:** line"
    assert "## Why this exists" in text, f"{pattern}.md missing Why section"
    assert "## Pitfalls" in text, f"{pattern}.md missing Pitfalls section"

    if pattern in HELPER_BACKED_PATTERNS:
        assert "## Use the helper" in text, (
            f"{pattern}.md missing 'Use the helper' section"
        )
        assert "from cadlib" in text, (
            f"{pattern}.md does not point at its cadlib helper"
        )
    elif pattern in KNOWLEDGE_ONLY_PATTERNS:
        pass  # prose only — defers code to cadquery-modeling.md
    else:
        assert "## CadQuery template" in text or "## CadQuery templates" in text, (
            f"{pattern}.md missing CadQuery template section"
        )
        assert "import cadquery" in text, (
            f"{pattern}.md template does not import cadquery"
        )


def test_skill_md_lists_every_pattern():
    """SKILL.md's pattern-library trigger table must reference each pattern
    file by name — otherwise the agent can't find them on demand.
    """
    skill_md = (SKILL_DIR / "SKILL.md").read_text()
    for pattern in PATTERN_NAMES:
        ref = f"references/patterns/{pattern}.md"
        assert ref in skill_md, f"SKILL.md missing pointer to {ref}"


# -- Review tool -------------------------------------------------------------


def test_review_multiple_sidecars_requires_stem(tmp_path: Path):
    """A dir holding several .step.json sidecars must error (exit 2) and
    name the candidates instead of silently reviewing the first one;
    ``--stem`` disambiguates."""
    for stem in ("alpha", "beta"):
        (tmp_path / f"{stem}.step.json").write_text("{}", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "review"), str(tmp_path)],
        capture_output=True, text=True, timeout=20,
    )
    assert proc.returncode == 2, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    msg = payload["error"]["message"]
    assert "--stem" in msg and "alpha" in msg and "beta" in msg
