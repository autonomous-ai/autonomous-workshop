"""Issue #101: a check that reads the round's kept B-rep says what one that
rebuilds says.

`brepbundle.py build` builds a source once beside `gen` and keeps it as a
native B-rep bundle. Each tool a component round runs -- both print gates,
check_envelope, render_review and the generated Display Pose entry -- is run
here on a real build123d part twice, once building from source and once
reading the bundle, and must print the same verdict, write the same report
and the same image bytes, and read the bundle's identity, kept from the
build `gen` reported.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build123d  # noqa: F401 - the B-rep kernel these checks need

from tests.make import test_make_round as rounds

SKILLS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills"
CAD = SKILLS / "cad/scripts"
CHECK_ENVELOPE = SKILLS / "make-round/scripts/check_envelope"

# A coloured two-body part: a plate 0.5 mm thick (below a 0.8 mm wall, so the
# thickness gate fails and names the tagged feature beside it), a post, and a
# print-details style tag. Its placement hook takes an instance; instance 2
# is taller, so a check of the wrong build shows.
PART = '''from build123d import Box, Color, Compound, Cylinder, Pos

from features import tags


def _build(instance):
    plate = Box(20, 20, 0.5)
    plate.color, plate.label = Color(0.8, 0.2, 0.2), "plate"
    post = Pos(0, 0, 4) * Cylinder(3, 8 if instance == 1 else 12)
    post.color, post.label = Color(0.2, 0.2, 0.8), "post"
    tags.tag("rib", Box(20, 20, 0.5))
    return Compound(children=[plate, post], label="toy")


def gen_step():
    """cadgen takes a generator without arguments; the module rebinds it to
    the instance-taking builder, as a two-instance Component does."""
    return _build(1)


def _gen_step(instance=1):
    return _build(instance)


_gen_step.__name__ = "gen_step"
gen_step = _gen_step  # noqa: F811


def assembly_pose(shape, pose=None, instance=1):
    return Pos(0, 0, 10 * instance) * shape
'''
TAGS = '''PRINT_DETAIL_TAGS = []


def tag(kind, shape):
    PRINT_DETAIL_TAGS.append({"kind": kind, "name": "%s-%d" % (kind, len(PRINT_DETAIL_TAGS) + 1),
                              "site": "part_toy.step.py:10", "shape": shape})
'''
ENVELOPE = {"shapes": [{"pose": "display", "box": {"min_mm": [-30, -30, 0], "max_mm": [30, 30, 30]}}]}


class KeptBuildEquivalenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.project = Path(cls.tmp.name) / "cad"
        (cls.project / "features").mkdir(parents=True)
        (cls.project / "features/__init__.py").write_text("")
        (cls.project / "features/tags.py").write_text(TAGS)
        cls.part = cls.project / "part_toy.step.py"
        cls.part.write_text(PART)
        cls.bundles = cls.project / "measure/brep/toy"
        done = cls._run([CAD / "gen", cls.part, "--write", "--json"])
        cls.gen = json.loads(done.stdout.strip().splitlines()[-1])
        done = cls._run([CAD / "brepbundle.py", "build", cls.part, "--out", cls.bundles / "base"])
        cls.kept = json.loads(done.stdout.strip().splitlines()[-1])["brepBundle"]
        for instance in ("1", "2"):
            cls._run([CAD / "brepbundle.py", "build", cls.part, "--instance", instance,
                      "--out", cls.bundles / ("instance-" + instance)])
        (cls.project / "envelope.json").write_text(json.dumps(ENVELOPE))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def _run(cls, command, kept=False, check=True):
        # No cache may answer for either run: each must measure what it loaded.
        env = {**os.environ, "CADGEN_WARM": "0", "WORKSHOP_GEOMETRY_CACHE": "0"}
        env.pop("WORKSHOP_BREP_BUNDLE", None)
        env.pop("WORKSHOP_BREP_IDENTITY", None)
        if kept:
            env.update(WORKSHOP_BREP_BUNDLE=str(cls.bundles), WORKSHOP_BREP_IDENTITY=cls.kept["identity"])
        done = subprocess.run([sys.executable, *map(str, command)], cwd=cls.project, env=env,
                              capture_output=True, text=True, timeout=600)
        if check and done.returncode not in (0, 1):
            raise AssertionError("%s exit %d\n%s" % (command[0], done.returncode, done.stderr[-3000:]))
        return done

    def _both(self, command, outputs=()):
        """(source run, kept run, {output: (source bytes, kept bytes)})."""
        runs, files = [], {}
        for kept in (False, True):
            runs.append(self._run(command, kept=kept))
            for path in outputs:
                files.setdefault(path, []).append(Path(path).read_bytes())
        return runs[0], runs[1], files

    def _read(self, done, bundle="base"):
        lines = [line for line in done.stderr.splitlines() if line.startswith("[brep] ")]
        self.assertEqual(len(lines), 1, done.stderr)
        self.assertIn(" %s identity " % bundle, lines[0])
        return lines[0].rsplit(" ", 1)[1]

    def test_the_kept_build_is_the_build_gen_reports(self):
        self.assertEqual(self.gen["outcome"], "built")
        self.assertEqual(self.kept["builtIdentity"], self.gen["identitySha256"])
        self.assertLessEqual(self.kept["maxDriftMm"], 1e-9)
        manifest = json.loads((self.bundles / "base/manifest.json").read_text())
        self.assertEqual([node["label"] for node in manifest["nodes"]], ["toy", "plate", "post"])
        self.assertEqual([tag["name"] for tag in manifest["tags"]], ["rib-1"])

    def test_print_gates_report_the_same_from_the_kept_build(self):
        for gate, extra in (("check_thickness", ["--nozzle", "0.4"]), ("check_overhang", ["--angle", "45"])):
            with self.subTest(gate=gate):
                report = self.project / ("%s.md" % gate)
                source, kept, files = self._both([CAD / gate, self.part, *extra, "--report", report], [report])
                self.assertEqual((source.returncode, source.stdout), (kept.returncode, kept.stdout))
                self.assertEqual(files[report][0], files[report][1])
                self.assertEqual(self._read(kept), self.kept["identity"])
                self.assertNotIn("[brep]", source.stderr)
        # The thin plate fails and is named by the tag the build recorded.
        thickness = (self.project / "check_thickness.md").read_text()
        self.assertIn("rib-1 (part_toy.step.py:10)", thickness)

    def test_an_envelope_places_the_kept_build_and_the_kept_instance(self):
        for instance in (None, 2):
            with self.subTest(instance=instance):
                command = [CHECK_ENVELOPE, self.part, "--envelope", self.project / "envelope.json",
                           "--role", "inside", "--json"]
                if instance is not None:
                    command += ["--instance", str(instance)]
                source, kept, _ = self._both(command)
                self.assertEqual((source.returncode, source.stdout), (kept.returncode, kept.stdout))
                read = self._read(kept, "base" if instance is None else "instance-2")
                if instance is None:
                    self.assertEqual(read, self.kept["identity"])
                else:
                    self.assertNotEqual(read, self.kept["identity"])

    def test_renders_are_the_same_pixels_from_the_kept_build(self):
        views = self.project / "views"
        images = [views / (name + ".png") for name in ("iso", "front", "sheet")]
        source, kept, files = self._both(
            [CAD / "render_review", self.part, "--view", "iso", "--view", "front", "--sheet", "-o", views], images)
        for image in images:
            self.assertEqual(files[image][0], files[image][1], image.name)
        self.assertEqual(self._read(kept), self.kept["identity"])

    def test_the_display_pose_is_the_same_pixels_from_the_kept_instance(self):
        posed = self.project / "measure/display_pose_toy.step.py"
        posed.write_text(rounds.load_module().DISPLAY_POSE_ENTRY % {"project": str(self.project),
                                                                     "part": self.part.name})
        views = self.project / "posed"
        image = views / "az90_el15.png"
        source, kept, files = self._both([CAD / "render_review", posed, "--view=90,15", "-o", views], [image])
        self.assertEqual(files[image][0], files[image][1])
        # Instance 1 of an instance-taking gen_step is its own kept build.
        self.assertIn("[brep] display-pose read part_toy.step.py instance-1 identity", kept.stderr)
        self.assertNotIn("[brep]", source.stderr)

    def test_a_tampered_bundle_fails_the_check_instead_of_rebuilding(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "toy"
            import shutil

            shutil.copytree(self.bundles, copy)
            data = bytearray((copy / "base/shapes.bin").read_bytes())
            data[-8] ^= 0xFF
            (copy / "base/shapes.bin").write_bytes(bytes(data))
            env = {**os.environ, "WORKSHOP_BREP_BUNDLE": str(copy),
                   "WORKSHOP_BREP_IDENTITY": self.kept["identity"]}
            done = subprocess.run([sys.executable, str(CAD / "check_overhang"), str(self.part)], cwd=self.project,
                                  env=env, capture_output=True, text=True, timeout=600)
            # No verdict at all: make_round reads a gate without a RESULT as a failure.
            self.assertNotEqual(done.returncode, 0)
            self.assertNotIn("RESULT:", done.stdout)
            self.assertIn("changed after it was written", done.stderr)

    def test_the_bundle_self_check_passes(self):
        done = subprocess.run([sys.executable, str(CAD / "brepbundle.py"), "--self-check"],
                              capture_output=True, text=True, timeout=600)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)


if __name__ == "__main__":
    unittest.main()
