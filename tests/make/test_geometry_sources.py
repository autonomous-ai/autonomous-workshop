"""Issue #110: a shape check goes stale only when its Geometry Sources change.

Geometry Sources (CONTEXT.md) are each Component's source, the Shared Helpers
it imports and the project parameters. Measurements, audits, notes and renders
in the same CAD Project never make a shape check stale. The rule is defined
once, in cad/scripts/geometry_sources.py, and read by the motion evidence,
make_round (component packets, the assembly packet and --interface) and
verify_project's sweep reuse.
"""

from __future__ import annotations

import hashlib
import json
import runpy
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts"
SOURCES = runpy.run_path(str(TOOLS / "geometry_sources.py"))

# Files a Manager adds beside the geometry: audits, a spec, notes, renders.
NOT_GEOMETRY = {
    "measure/check_landmarks.py": "raise SystemExit(0)\n",
    "measure/check_spec.py": "import params\nraise SystemExit(0)\n",
    "measure/spec.json": "{}\n",
    "notes/decisions.md": "# notes\n",
    "notes/scratch.py": "X = 1\n",
    "snap/iso.png": "png",
    "samples/peg.step.py": "from features.joints import PEG_D\ndef gen_step(): return None\n",
}


def project_fixture(root: Path) -> Path:
    project = root / "cad"
    (project / "features").mkdir(parents=True)
    (project / "params.py").write_text("SCALE = 1.0\n")
    (project / "features/__init__.py").write_text("")
    (project / "features/joints.py").write_text("import params\nPEG_D = 4.0 * params.SCALE\n")
    (project / "features/unused.py").write_text("LOOSE = 3\n")
    (project / "part_body.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return None\n")
    (project / "part_arm.step.py").write_text("def gen_step(): return None\n")
    (project / "toy.step.py").write_text("def gen_step(): return None\n")
    return project


def add_files(project: Path, files: dict) -> None:
    for relative, text in files.items():
        path = project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)


class GeometrySourcesTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = project_fixture(Path(temporary.name))

    def test_the_project_sources_are_the_entries_and_what_they_import(self):
        self.assertEqual(sorted(SOURCES["geometry_sources"](self.project)), [
            "features/__init__.py", "features/joints.py", "params.py",
            "part_arm.step.py", "part_body.step.py", "toy.step.py"])

    def test_a_component_binds_its_source_and_the_helpers_it_imports(self):
        self.assertEqual(sorted(SOURCES["component_geometry_sources"](self.project, "body")), [
            "features/__init__.py", "features/joints.py", "params.py", "part_body.step.py"])
        self.assertEqual(sorted(SOURCES["component_geometry_sources"](self.project, "arm")), ["part_arm.step.py"])

    def test_measurements_audits_notes_renders_and_samples_never_change_them(self):
        before = SOURCES["geometry_sources"](self.project)
        body = SOURCES["component_geometry_sources"](self.project, "body")
        add_files(self.project, NOT_GEOMETRY)
        self.assertEqual(SOURCES["geometry_sources"](self.project), before)
        self.assertEqual(SOURCES["component_geometry_sources"](self.project, "body"), body)
        # Editing them again changes nothing either.
        add_files(self.project, {path: text + "# edited\n" for path, text in NOT_GEOMETRY.items()})
        self.assertEqual(SOURCES["geometry_sources"](self.project), before)

    def test_a_component_source_an_imported_helper_or_the_parameters_change_them(self):
        for path in ("part_body.step.py", "features/joints.py", "params.py"):
            before = SOURCES["geometry_sources"](self.project)
            body = SOURCES["component_geometry_sources"](self.project, "body")
            (self.project / path).write_text((self.project / path).read_text() + "# edited\n")
            self.assertNotEqual(SOURCES["geometry_sources"](self.project), before, path)
            self.assertNotEqual(SOURCES["component_geometry_sources"](self.project, "body"), body, path)

    def test_a_helper_no_component_imports_is_not_a_geometry_source(self):
        before = SOURCES["geometry_sources"](self.project)
        (self.project / "features/unused.py").write_text("LOOSE = 4\n")
        self.assertEqual(SOURCES["geometry_sources"](self.project), before)


class SweepReuseFollowsGeometrySourcesTest(unittest.TestCase):
    """verify_project's reuse key (ADR 0070) reads the same definition."""

    def setUp(self):
        self.verifier = runpy.run_path(str(TOOLS / "verify_project"))
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.project = project_fixture(self.root)
        for name in ("toy", "part_body", "part_arm"):
            (self.project / (name + ".step")).write_bytes(name.encode())
        self.tool = self.root / "tool.py"
        self.tool.write_text("print('v1')\n")

    def _closure(self):
        return self.verifier["_sweep_closure_sha256"](
            entries=[self.project / "toy.step.py", self.project / "part_body.step.py",
                     self.project / "part_arm.step.py"],
            cwd=self.root, project=self.project, raw_argv=["cad"], signature_review_sha256="deadbeef",
            tool_paths=[self.tool])

    def test_files_beside_the_geometry_leave_the_reuse_key_unchanged(self):
        before = self._closure()
        add_files(self.project, NOT_GEOMETRY)
        self.assertEqual(self._closure(), before)

    def test_an_edited_imported_helper_changes_the_reuse_key(self):
        before = self._closure()
        (self.project / "features/joints.py").write_text("import params\nPEG_D = 4.2 * params.SCALE\n")
        self.assertNotEqual(self._closure(), before)

    def test_the_definition_is_part_of_the_sweeps_tool_closure(self):
        self.assertIn(TOOLS / "geometry_sources.py", self.verifier["_sweep_tool_paths"](image_derived=False))


class MotionEvidenceFollowsGeometrySourcesTest(unittest.TestCase):
    """The motion evidence (snap/MOTION-EVIDENCE.json) binds the Geometry
    Sources, so an audit added after it was generated leaves it current."""

    def setUp(self):
        try:
            import build123d  # noqa: F401
        except ImportError:  # pragma: no cover - the CAD kernel is a test dependency
            self.skipTest("build123d is not installed")
        self.helper = runpy.run_path(str(TOOLS / "motion_presentation.py"))
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / "cad"
        (self.project / "measure").mkdir(parents=True)
        (self.project / "features").mkdir()
        (self.project / "features/__init__.py").write_text("# sizes\n")
        (self.project / "features/sizes.py").write_text("DRIVER = (2, 1, 1)\n")
        (self.project / "model.step.py").write_text('''from build123d import Box, Compound
from features.sizes import DRIVER
def gen_step():
    driver = Box(*DRIVER).translate((4, 0, 0))
    driver.label = "driver"
    driver.color = (0.8, 0.05, 0.01)
    frame = Box(2, 2, 1).translate((0, 0, -3))
    frame.label = "frame"
    frame.color = (0.01, 0.1, 0.8)
    return Compound(children=[driver, frame], label="root")
''')
        condition = {"id": "turn", "check": "coupled_motion_collision", "inputs": {
            "steps": 8, "movers": [{"part": "driver", "rotation": {
                "axis_point": [0, 0, 0], "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 90}}],
            "obstacle_parts": ["frame"]}}
        (self.project / "measure/motion.json").write_text(
            json.dumps({"assembly": "model.step.py", "conditions": [condition]}))
        evidence = self.helper["generate"](self.project, size=256)
        self.signature = {"concept_sha256": "a" * 64, "reviewer": "synthetic-test-critic", "review_rounds": 1}
        review = {"schema_version": 1, **self.signature,
                  "evidence_sha256": hashlib.sha256(self.helper["canonical"](evidence)).hexdigest(),
                  "blind_motion_read": "Synthetic fixture: the block turns about the stationary base.",
                  "motion_matches_wish": True, "simulation_not_physical_test": True}
        (self.project / self.helper["REVIEW"]).write_bytes(self.helper["canonical"](review))
        self.evidence = evidence

    def test_the_evidence_binds_the_geometry_sources(self):
        self.assertEqual(sorted(self.evidence["sources"]),
                         ["features/__init__.py", "features/sizes.py", "model.step.py"])

    def test_audits_and_notes_added_afterwards_leave_the_evidence_current(self):
        add_files(self.project, {"measure/check_landmarks.py": "raise SystemExit(0)\n",
                                 "measure/check_spec.py": "raise SystemExit(0)\n",
                                 "measure/spec.json": "{}\n", "notes/why.md": "# why\n"})
        self.helper["validate"](self.project, self.signature)

    def test_an_edited_imported_helper_makes_the_evidence_stale(self):
        (self.project / "features/sizes.py").write_text("DRIVER = (2, 1, 1)  # same size\n")
        with self.assertRaisesRegex(ValueError, "stale CAD sources"):
            self.helper["validate"](self.project, self.signature)


if __name__ == "__main__":
    unittest.main()
