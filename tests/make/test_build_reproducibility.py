"""Issue #102: one source builds one B-rep, and a component round proves it.

build123d asks OCCT for a parallel Boolean before every fuse, cut and
section; near-tolerance contacts then settle differently from run to run. The
Make toolchain runs every Boolean serially, in every loader that executes a
``gen_step()`` source, and a component round builds its source a second time
in its own process and fails with a build error when the identities differ.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.runtime.package_data import product_run_domain_skill_roots

from tests.make.test_make_round import _gate_output, fake_render_review, load_module

ROOTS = product_run_domain_skill_roots()
CAD_SCRIPTS = ROOTS["cad"] / "scripts"
CADGEN_SRC = CAD_SCRIPTS / "packages" / "cadgen" / "src"
REPRODUCE = ROOTS["make-round"] / "scripts" / "reproduce_build"
HAS_CAD = importlib.util.find_spec("build123d") is not None and importlib.util.find_spec("OCP") is not None

# A gen_step() source that refuses to build unless every Boolean is serial.
SERIAL_ONLY = """\
from build123d import Box, Cylinder
from cadgen.booleans import booleans_are_serial
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse


def gen_step():
    probe = BRepAlgoAPI_Fuse()
    probe.SetRunParallel(True)
    if not booleans_are_serial() or probe.RunParallel():
        raise RuntimeError("parallel Booleans in a build")
    return Box(10, 10, 10) - Cylinder(3, 20)
"""

# The same shape every build.
STEADY = """\
from build123d import Box, Cylinder


def gen_step():
    return Box(10, 10, 10) - Cylinder(3, 20)
"""

# A different B-rep every build: the fake nondeterministic source.
WANDERING = """\
import random

from build123d import Box


def gen_step():
    return Box(10 + random.random(), 10, 10)
"""


def _environment() -> dict:
    environment = dict(os.environ)
    environment["CADGEN_WARM"] = "0"
    environment["PYTHONPATH"] = os.pathsep.join([str(CADGEN_SRC), environment.get("PYTHONPATH", "")])
    return environment


def _python(code: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], cwd=cwd, env=_environment(),
                          capture_output=True, text=True, timeout=600)


def _gen_identity(source: Path) -> str:
    done = subprocess.run([sys.executable, str(CAD_SCRIPTS / "gen"), source.name, "--json", "--force"],
                          cwd=source.parent, env=_environment(), capture_output=True, text=True, timeout=600)
    if done.returncode:
        raise AssertionError("gen failed: %s" % done.stderr[-2000:])
    identities = [json.loads(line).get("identitySha256") for line in done.stdout.splitlines()
                  if line.startswith("{")]
    identities = [value for value in identities if value]
    if len(identities) != 1:
        raise AssertionError("gen reported %r" % done.stdout)
    return identities[0]


def _reproduce(source: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(REPRODUCE), str(source)], cwd=source.parent,
                          env=_environment(), capture_output=True, text=True, timeout=600)


@unittest.skipUnless(HAS_CAD, "needs build123d and OCP")
class SerialBooleansTest(unittest.TestCase):
    def test_serial_booleans_override_what_build123d_asks_for(self):
        done = _python(
            "from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse, BRepAlgoAPI_Section\n"
            "from OCP.BOPAlgo import BOPAlgo_Builder\n"
            "from cadgen.booleans import booleans_are_serial, serial_booleans\n"
            "def asked(kind):\n"
            "    op = kind(); op.SetRunParallel(True); return op.RunParallel()\n"
            "kinds = (BRepAlgoAPI_Fuse, BRepAlgoAPI_Cut, BRepAlgoAPI_Section, BOPAlgo_Builder)\n"
            "print(booleans_are_serial(), [asked(k) for k in kinds])\n"
            "serial_booleans(); serial_booleans()\n"
            "print(booleans_are_serial(), [asked(k) for k in kinds])\n",
            Path(tempfile.gettempdir()))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.splitlines(),
                         ["False [True, True, True, True]", "True [False, False, False, False]"])

    def test_gen_and_the_print_gate_loader_build_with_serial_booleans(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "part_probe.step.py"
            source.write_text(SERIAL_ONLY, encoding="utf-8")
            # gen: the cadgen runtime every `gen`, inspect and export runs through.
            self.assertTrue(_gen_identity(source))
            # The print gates' loader (check_thickness, check_overhang, check_mesh,
            # check_fit, check_envelope).
            done = _python(
                "import sys; sys.path.insert(0, %r); sys.path.insert(0, %r)\n"
                "from printlib import load_entry\n"
                "load_entry(__import__('pathlib').Path(%r), 'probe').gen_step()\n"
                "print('built')\n" % (str(CAD_SCRIPTS), str(project), str(source)), project)
            self.assertEqual(done.returncode, 0, done.stderr[-2000:])
            self.assertIn("built", done.stdout)

    def test_a_motion_worker_makes_booleans_serial_before_its_sweep(self):
        with tempfile.TemporaryDirectory() as tmp:
            tool = Path(tmp) / "tool.py"
            tool.write_text("from contextlib import nullcontext\nvalidation_scope = nullcontext\n", encoding="utf-8")
            environment = dict(os.environ)
            environment.pop("PYTHONPATH", None)  # the worker finds the vendored cadgen itself
            done = subprocess.run(
                [sys.executable, "-c",
                 "import sys; sys.path.insert(0, %r)\n"
                 "import motion_parallel\n"
                 "motion_parallel._initialize(%r, [], [], 1, 0.0)\n"
                 "from cadgen.booleans import booleans_are_serial\n"
                 "print(booleans_are_serial())\n" % (str(CAD_SCRIPTS), str(tool))],
                cwd=tmp, env=environment, capture_output=True, text=True, timeout=600)
            self.assertEqual(done.returncode, 0, done.stderr[-2000:])
            self.assertEqual(done.stdout.strip(), "True")

    def test_every_loader_that_runs_a_source_makes_booleans_serial_first(self):
        # A static guard for the loaders not exercised above: each one that
        # executes a gen_step() source in its own process calls serial_booleans().
        loaders = [
            CAD_SCRIPTS / "packages/cadgen/src/cadgen/_internal/generation_runner.py",
            CAD_SCRIPTS / "printlib.py",
            CAD_SCRIPTS / "render_review",
            CAD_SCRIPTS / "render_product",
            CAD_SCRIPTS / "check_mount",
            CAD_SCRIPTS / "check_motion",
            CAD_SCRIPTS / "cadcache.py",
            CAD_SCRIPTS / "motion_parallel.py",
            ROOTS["image-to-cad"] / "scripts" / "render_views.py",
        ]
        for loader in loaders:
            self.assertIn("serial_booleans()", loader.read_text(encoding="utf-8"), loader.name)


@unittest.skipUnless(HAS_CAD, "needs build123d and OCP")
class ReproduceBuildTest(unittest.TestCase):
    def test_a_second_build_reports_the_identity_gen_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "part_steady.step.py"
            source.write_text(STEADY, encoding="utf-8")
            done = _reproduce(source)
            self.assertEqual(done.returncode, 0, done.stderr[-2000:])
            self.assertEqual(json.loads(done.stdout)["identitySha256"], _gen_identity(source))

    def test_a_source_that_does_not_build_fails_the_second_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "part_broken.step.py"
            source.write_text("def gen_step():\n    raise ValueError('wall must be positive')\n", encoding="utf-8")
            done = _reproduce(source)
            self.assertEqual(done.returncode, 1)
            self.assertIn("wall must be positive", done.stderr)
            self.assertEqual(done.stdout, "")


def _fake_tools(identities: dict, calls: list):
    """Stand in for every tool but the build: `gen` reports identities['gen'],
    reproduce_build identities['reproduce']."""

    def fake_run(command, **kwargs):
        tool = Path(command[1]).name
        calls.append(tool)
        if tool == "gen":
            source = Path(command[2])
            source.with_name(source.name[:-len(".py")]).write_bytes(b"step")
            return subprocess.CompletedProcess(command, 0, json.dumps({"identitySha256": identities["gen"]}) + "\n", "")
        if tool == "reproduce_build":
            value = identities["reproduce"]
            if isinstance(value, subprocess.CompletedProcess):
                return value
            return subprocess.CompletedProcess(command, 0, json.dumps({"identitySha256": value}) + "\n", "")
        if tool == "render_review":
            return fake_render_review(command)
        if tool in ("check_thickness", "check_overhang"):
            stdout, code = _gate_output(tool, fails=False)
            return subprocess.CompletedProcess(command, code, stdout, "")
        return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

    return fake_run


class ComponentRoundReproducibilityTest(unittest.TestCase):
    def _component_round(self, project: Path, run, expected_exit: int):
        module = load_module()
        with contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()), \
                mock.patch.object(module, "skills_root", return_value=ROOTS["cad"].parent), \
                mock.patch.object(module, "run", side_effect=run):
            self.assertEqual(module.main([str(project), "--component", "part_wheel.step.py"]), expected_exit)
        summary = json.loads((project / "measure/component-rounds/wheel/r0001/summary.json").read_text())
        return module, summary, stdout.getvalue()

    def _project(self, tmp: str, source: str = "def gen_step(): return 'wheel'\n") -> Path:
        project = Path(tmp)
        (project / "toy.step.py").write_text("def gen_step(): return 'assembly'\n")
        (project / "part_wheel.step.py").write_text(source)
        return project

    def test_a_round_refuses_a_build_whose_second_build_differs(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            calls = []
            module, summary, printed = self._component_round(
                project, _fake_tools({"gen": "brep-1", "reproduce": "brep-2"}, calls), 1)
            build = summary["build"]["wheel"]
            self.assertEqual(build["verdict"], "FAIL")
            self.assertIs(build["reproducible"], False)
            self.assertEqual(build["identities"], ["brep-1", "brep-2"])
            self.assertIn("not reproducible: two builds of this source gave B-rep identities brep-1 and brep-2",
                          build["failures"][0])
            self.assertIn("not reproducible", printed)
            self.assertFalse(summary["checks_ok"])
            # A failed build is neither gated nor rendered, and has no identity to review.
            # Its builds ran at once (issue #101): gen, the reproduction and the kept build.
            self.assertEqual(sorted(calls), ["brepbundle.py", "gen", "reproduce_build"])
            self.assertIsNone(summary["identity"])

    def test_a_round_refuses_a_detail_refused_in_the_second_build_only(self):
        # Broken God's spine-housing: one build in several refused a rivet.
        refused = subprocess.CompletedProcess(
            [], 1, "", 'detail-refusal {"feature": "rivet", "site": "part_wheel.step.py:313", '
                       '"reason": "does not join its host", "passes": "a host face it touches"}\n')
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            _, summary, _ = self._component_round(
                project, _fake_tools({"gen": "brep-1", "reproduce": refused}, []), 1)
            build = summary["build"]["wheel"]
            self.assertEqual(build["verdict"], "FAIL")
            self.assertIn("refused rivet at part_wheel.step.py:313", build["failures"][0])
            self.assertEqual(build["reproduction_refusals"][0]["feature"], "rivet")

    def test_a_reproducible_build_goes_on_to_its_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            calls = []
            _, summary, _ = self._component_round(
                project, _fake_tools({"gen": "brep-1", "reproduce": "brep-1"}, calls), 1)
            self.assertEqual(summary["build"]["wheel"]["verdict"], "PASS")
            self.assertEqual(summary["identity"], "brep-1")
            # Every build first, at the same time (issue #101), then the gates.
            self.assertEqual(sorted(calls[:3]), ["brepbundle.py", "gen", "reproduce_build"])
            self.assertIn("check_thickness", calls)
            self.assertEqual(summary["visual"]["status"], "pending")

    def test_an_assembly_round_does_not_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            calls = []
            module = load_module()
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
                    mock.patch.object(module, "skills_root", return_value=ROOTS["cad"].parent), \
                    mock.patch.object(module, "run",
                                      side_effect=_fake_tools({"gen": "brep-1", "reproduce": "brep-2"}, calls)):
                module.main([str(project)])
            self.assertNotIn("reproduce_build", calls)

    @unittest.skipUnless(HAS_CAD, "needs build123d and OCP")
    def test_a_real_nondeterministic_source_is_refused_and_a_steady_one_is_not(self):
        # The real gen and reproduce_build, each in its own process; every
        # other tool is faked.
        for source, verdict in ((WANDERING, "FAIL"), (STEADY, "PASS")):
            with self.subTest(verdict=verdict), tempfile.TemporaryDirectory() as tmp:
                project = self._project(tmp, source)
                module = load_module()
                real_run = module.run
                faked = _fake_tools({}, [])

                def run(command, **kwargs):
                    if Path(command[1]).name in ("gen", "reproduce_build"):
                        return real_run(command, **kwargs)
                    return faked(command, **kwargs)

                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
                        mock.patch.dict(os.environ, {"PYTHONPATH": str(CADGEN_SRC)}), \
                        mock.patch.object(module, "skills_root", return_value=ROOTS["cad"].parent), \
                        mock.patch.object(module, "run", side_effect=run):
                    module.main([str(project), "--component", "part_wheel.step.py"])
                summary = json.loads((project / "measure/component-rounds/wheel/r0001/summary.json").read_text())
                build = summary["build"]["wheel"]
                self.assertEqual(build["verdict"], verdict, build)
                if verdict == "FAIL":
                    self.assertIs(build["reproducible"], False)
                    self.assertNotEqual(*build["identities"])
                self.assertTrue((Path(summary["out"]) / "reproduce-wheel.log").is_file())


if __name__ == "__main__":
    unittest.main()
