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


def test_default_mesh_tolerance_is_delegated_to_cadpy():
    """An unset CLI flag must not re-impose the worker's historical 0.05/3°.

    The test stub mirrors cadpy's public defaults. Seeing those exact values in
    the payload proves the runner omitted both kwargs, which leaves production
    cadpy free to choose its adaptive per-scene profile.
    """
    cube = ASSETS / "example_cube_with_hole.py"
    if not cube.exists():
        pytest.skip("no example_cube_with_hole.py asset")
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(str(cube), "--out-dir", tmp)
    assert payload["ok"]
    assert payload["mesh_tolerance"] == pytest.approx(0.02)
    assert payload["angular_tolerance"] == pytest.approx(0.6)


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


def test_review_cover_uses_low_eye_level_camera():
    scripts = str(SCRIPTS)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from review.cli import _COVER_VIEWS

    assert _COVER_VIEWS == (("", 10.0, -35.0),)


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


def test_project_template_compiles(monkeypatch):
    """The bundled project skeleton must compile in the real artifact runtime."""
    project = SKILL_DIR / "templates" / "project_skeleton"
    required_sources = (
        "cad_project.json",
        "main.py",
        "params.py",
        "validation.py",
        "assemblies/__init__.py",
        "assemblies/product.py",
        "parts/__init__.py",
        "parts/base.py",
        "parts/cover.py",
    )
    missing = [path for path in required_sources if not (project / path).is_file()]
    assert not missing, f"project skeleton is incomplete: {missing}"
    # This one canonical template is worth the real OCCT/cadpy cost: the fast
    # stub cannot prove named per-part assembly artifacts or their ordering.
    monkeypatch.delenv("CADCODE_TEST_CADPY_PATH", raising=False)
    with tempfile.TemporaryDirectory() as tmp:
        payload = _run_cad(str(project), "--out-dir", tmp)
        assert payload.get("ok"), f"skeleton failed: {payload}"
        assert payload.get("is_solid"), "skeleton non-solid"
        assert payload.get("volume_mm3", 0) > 1000
        assert [part["name"] for part in payload.get("parts", [])] == [
            "base",
            "cover",
        ]
        assert not [
            warning
            for warning in payload.get("warnings", [])
            if warning.get("severity", "warning") != "info"
        ]
        # Stem comes from the canonical manifest identity.
        out = Path(tmp)
        assert (out / "project_skeleton.step").exists()
        assert (out / "project_skeleton.stl").exists()
        assert (out / "project_skeleton.step.json").exists()
        assert (out / "project_skeleton_parts" / "base.step").exists()
        assert (out / "project_skeleton_parts" / "base.stl").exists()
        assert (out / "project_skeleton_parts" / "cover.step").exists()
        assert (out / "project_skeleton_parts" / "cover.stl").exists()
        assert not list((out / "project_skeleton_parts").glob("*.stl.json"))
        assert not (out / "project_skeleton.glb").exists()
        assert not (out / "project_skeleton.topology.json").exists()


def _assembled_occurrence_names(step_path: Path) -> list[str]:
    """Part names in the order their meshes land in the assembled file.

    Read through cadpy's own scene reader, in a subprocess so the OCP runtime
    never enters the (stub-driven) test process.
    """
    code = (
        "import json, sys\n"
        "sys.path.insert(0, sys.argv[1])\n"
        "from pathlib import Path\n"
        "from cadpy.step_scene import load_step_scene, scene_export_occurrences\n"
        "from cadpy.stl import _safe_part_name\n"
        "scene = load_step_scene(Path(sys.argv[2]))\n"
        "seen = {}\n"
        "print(json.dumps([\n"
        "    _safe_part_name(node.name or node.source_name, seen, fallback=f'part{i + 1}')\n"
        "    for i, node in enumerate(scene_export_occurrences(scene))\n"
        "]))\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", code, str(SCRIPTS / "packages"), str(step_path)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"could not read the assembled scene: {proc.stderr[-500:]}"
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_assembly_parts_follow_assembled_mesh_order(monkeypatch):
    """``parts[]`` is the assembled file's MESH ORDER, never a sorted listing.

    The viewer addresses a clicked mesh by its index in the assembled file and
    merges the chosen color back onto ``parts[i]``, so an array that drifts from
    the mesh order paints the wrong part. Part names here are deliberately
    anti-alphabetical: a sort anywhere in the chain shows up immediately.
    """
    monkeypatch.delenv("CADCODE_TEST_CADPY_PATH", raising=False)
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "ordered"
        project.mkdir()
        (project / "main.py").write_text(
            "import cadquery as cq\n"
            "\n"
            "def gen_step():\n"
            "    assy = cq.Assembly()\n"
            "    assy.add(cq.Workplane('XY').box(10, 10, 10), name='zulu')\n"
            "    assy.add(\n"
            "        cq.Workplane('XY').box(8, 8, 8),\n"
            "        loc=cq.Location(cq.Vector(0, 0, 20)),\n"
            "        name='alpha',\n"
            "    )\n"
            "    assy.add(\n"
            "        cq.Workplane('XY').box(6, 6, 6),\n"
            "        loc=cq.Location(cq.Vector(0, 0, 40)),\n"
            "        name='mike',\n"
            "    )\n"
            "    return assy\n"
        )
        payload = _run_cad(str(project), "--out-dir", tmp, timeout=120)
        assert payload.get("ok"), f"assembly failed: {payload}"

        expected = ["zulu", "alpha", "mike"]
        out = Path(tmp)
        sidecar = json.loads((out / "ordered.step.json").read_text())
        assert [part["name"] for part in sidecar["parts"]] == expected
        assert [part["stlPath"] for part in sidecar["parts"]] == [
            f"ordered_parts/{name}.stl" for name in expected
        ]
        assert [part["stepPath"] for part in sidecar["parts"]] == [
            f"ordered_parts/{name}.step" for name in expected
        ]
        # The stdout payload echoes the same order the sidecar records...
        assert [part["name"] for part in payload.get("parts", [])] == expected
        # ...and both match the order the meshes occur in the assembled file.
        assert _assembled_occurrence_names(out / "ordered.step") == expected


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


def _write_manifest_project(root: Path, *, artifact_stem: object) -> None:
    root.mkdir()
    (root / "main.py").write_text(
        "import cadquery as cq\n"
        "def gen_step(): return cq.Workplane('XY').box(8, 9, 10)\n",
        encoding="utf-8",
    )
    (root / "cad_project.json").write_text(
        json.dumps({
            "schemaVersion": 1,
            "engine": "cadquery",
            "entrypoint": {"path": "main.py", "callable": "gen_step"},
            "artifactStem": artifact_stem,
        }),
        encoding="utf-8",
    )


def test_manifest_artifact_stem_owns_create_output_family():
    """Renaming a canonical project directory cannot rename its artifacts."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        project = tmp_p / "renamed-directory"
        out = tmp_p / "out"
        _write_manifest_project(project, artifact_stem="stable-model")

        payload = _run_cad(str(project), "--out-dir", str(out))

        assert payload.get("ok"), payload
        for suffix in (".step", ".stl", ".step.json"):
            assert (out / f"stable-model{suffix}").is_file()
            assert not (out / f"renamed-directory{suffix}").exists()


def test_manifest_rejects_conflicting_stem_before_build():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        project = tmp_p / "project"
        out = tmp_p / "out"
        _write_manifest_project(project, artifact_stem="stable-model")

        payload = _run_cad(
            str(project), "--out-dir", str(out), "--stem", "other-model"
        )

        assert not payload["ok"]
        assert "conflicts" in _err_message(payload)
        assert not out.exists()


@pytest.mark.parametrize(
    "artifact_stem",
    ("../escape", "Uppercase", "has space", ""),
)
def test_manifest_rejects_unsafe_artifact_stem_before_build(artifact_stem):
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        project = tmp_p / "project"
        _write_manifest_project(project, artifact_stem=artifact_stem)

        payload = _run_cad(str(project), "--out-dir", str(tmp_p / "out"))

        assert not payload["ok"]
        assert "artifactStem" in _err_message(payload)


@pytest.mark.parametrize(
    ("manifest", "message"),
    (
        ("{", "cannot read"),
        ("[]", "JSON object"),
        (
            json.dumps({
                "schemaVersion": 1,
                "engine": "build123d",
                "entrypoint": {"path": "main.py", "callable": "gen_step"},
                "artifactStem": "wrong-engine",
            }),
            "engine must be cadquery",
        ),
    ),
)
def test_manifest_rejects_malformed_identity_before_build(manifest, message):
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        project.mkdir()
        (project / "main.py").write_text("def gen_step(): return None\n")
        (project / "cad_project.json").write_text(manifest, encoding="utf-8")

        payload = _run_cad(str(project))

        assert not payload["ok"]
        assert message in _err_message(payload)


def test_manifest_rejects_oversized_file_before_build():
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        project.mkdir()
        (project / "main.py").write_text("def gen_step(): return None\n")
        (project / "cad_project.json").write_bytes(b" " * (1024 * 1024 + 1))

        payload = _run_cad(str(project))

        assert not payload["ok"]
        assert "within" in _err_message(payload)


def test_manifest_rejects_symlink_before_build():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        project = tmp_p / "project"
        project.mkdir()
        (project / "main.py").write_text("def gen_step(): return None\n")
        target = tmp_p / "outside-manifest.json"
        target.write_text("{}", encoding="utf-8")
        try:
            (project / "cad_project.json").symlink_to(target)
        except OSError:
            pytest.skip("filesystem does not support symlinks")

        payload = _run_cad(str(project))

        assert not payload["ok"]
        assert "symlink" in _err_message(payload)


def test_single_file_rejects_output_stem_path_escape():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_p = Path(tmp)
        source = tmp_p / "safe.py"
        source.write_text(
            "import cadquery as cq\nresult = cq.Workplane('XY').box(1, 1, 1)\n",
            encoding="utf-8",
        )
        payload = _run_cad(
            str(source),
            "--out-dir",
            str(tmp_p / "out"),
            "--stem",
            "../escape",
        )

        assert not payload["ok"]
        assert "safe" in _err_message(payload)
        assert not (tmp_p / "escape.step").exists()


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
    "form-from-reference",
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
KNOWLEDGE_ONLY_PATTERNS = {"fillet-stress-relief", "form-from-reference"}


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


def test_canonical_project_instructions_never_override_manifest_stem():
    """CREATE guidance must agree with the CLI's lifecycle identity gate."""
    skill_md = (SKILL_DIR / "SKILL.md").read_text()

    assert "--stem <project>_assembled" not in skill_md
    assert "--stem snap_lid_box_assembled" not in skill_md
    assert "Do not pass `--stem` for a project containing" in skill_md
    assert "Use `--stem` only for legacy/single-file input" in skill_md


def test_create_and_remix_share_negative_geometry_proof_contract():
    """The producer and later editor must preserve the same owned voids."""
    create_skill = (SKILL_DIR / "SKILL.md").read_text()
    remix_skill = (SKILL_DIR.parent / "remix" / "SKILL.md").read_text()
    literal_ref = (SKILL_DIR / "references" / "literal-geometry.md").read_text()
    spec = (SKILL_DIR / "templates" / "project_skeleton" / "spec.md").read_text()

    for helper in ("verify_rectangular_through_cut", "verify_clearance_box"):
        assert helper in create_skill
        assert helper in remix_skill
        assert helper in literal_ref
        assert helper in spec
    assert "rounded, tapered, keyhole, or freeform" in literal_ref
    assert "sparse point samples" in spec


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
