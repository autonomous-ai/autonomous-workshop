"""Issue #118: an assembly round's interference check, on real B-reps.

An assembly entry that loads its parts inside ``gen_step()`` runs their
module-top ``import params`` after cadgen has loaded the entry. cadgen keeps
the generator's own folder on ``sys.path`` for the whole build, so ``inspect
interfere`` -- the request final verification sends -- builds such an entry
and names each clash between its Components, and ``sys.path`` is restored
when the build ends.
"""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build123d  # noqa: F401 - the B-rep kernel these checks need

from workshop.runtime.package_data import product_run_domain_skill_roots

ROOTS = product_run_domain_skill_roots()
CAD_SCRIPTS = ROOTS["cad"] / "scripts"
CADGEN_SRC = CAD_SCRIPTS / "packages" / "cadgen" / "src"
MAKE_ROUND = ROOTS["make-round"] / "scripts" / "make_round"

PART = """import params
from build123d import Box, Pos


def gen_step():
    return Box(params.W, params.W, params.W)


def assembly_pose(shape, pose):
    return Pos(%r, 0, 0) * shape
"""

# The Broken God entry's shape: parts are loaded lazily, inside gen_step(),
# and the entry never puts its own folder on sys.path.
ENTRY = """import functools
import importlib.util
from pathlib import Path

from build123d import Compound

HERE = Path(__file__).resolve().parent


@functools.lru_cache(maxsize=None)
def load(role):
    path = HERE / f"part_{role}.step.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gen_step():
    children = []
    for role in ("left", "right"):
        module = load(role)
        shape = module.assembly_pose(module.gen_step(), None)
        shape.label = role
        children.append(shape)
    return Compound(children=children, label="toy")
"""


def _make_round():
    spec = importlib.util.spec_from_loader("make_round_script", loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(MAKE_ROUND)
    exec(compile(MAKE_ROUND.read_text(encoding="utf-8"), module.__file__, "exec"), module.__dict__)
    return module


def _project(root: Path, right_offset: float) -> Path:
    (root / "params.py").write_text("W = 10.0\n")
    (root / "part_left.step.py").write_text(PART % 0.0)
    (root / "part_right.step.py").write_text(PART % right_offset)
    (root / "toy.step.py").write_text(ENTRY)
    return root


def _environment() -> dict:
    environment = dict(os.environ)
    environment["CADGEN_WARM"] = "0"
    # No empty entry: one would put the working directory on sys.path and
    # hide a loader that drops the generator's folder.
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(CADGEN_SRC), *(item for item in environment.get("PYTHONPATH", "").split(os.pathsep) if item)])
    return environment


class AssemblyInterferenceTest(unittest.TestCase):
    def _interfere(self, right_offset, *, params=True):
        """``inspect interfere`` on the entry, both as an assembly round runs
        it (from the CAD project) and as final verification's batch does
        (from the workspace above it, by relative path); the two agree."""
        results = []
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "cad"
            project.mkdir()
            _project(project, right_offset)
            if not params:
                (project / "params.py").unlink()
            for cwd, entry in ((project, "toy.step.py"), (Path(tmp), "cad/toy.step.py")):
                done = subprocess.run([sys.executable, str(CAD_SCRIPTS / "inspect"), "interfere", entry,
                                       "--format", "json"], cwd=cwd, capture_output=True, text=True,
                                      timeout=300, env=_environment())
                results.append(_make_round().parse_assembly_interference(done.stdout, done.returncode))
        self.assertEqual(results[0]["verdict"], results[1]["verdict"], results)
        return results[0]

    def test_a_lazily_loaded_part_builds_and_its_clash_is_named_with_its_location(self):
        result = self._interfere(8.0)  # the right cube's x 3..13 enters the left's x -5..5
        self.assertEqual(result["verdict"], "fail", result)
        clash = result["clashes"][0]
        self.assertEqual({clash["a"], clash["b"]}, {"left", "right"})
        self.assertAlmostEqual(clash["volume_mm3"], 200.0, places=2)
        self.assertAlmostEqual(clash["at"]["min"][0], 3.0, places=1)
        self.assertAlmostEqual(clash["at"]["max"][0], 5.0, places=1)
        self.assertIn("mm3 at X 3..5", result["detail"])

    def test_parts_that_do_not_meet_pass(self):
        result = self._interfere(10.5)
        self.assertEqual(result["verdict"], "pass", result)

    def test_an_entry_that_cannot_import_its_parts_is_an_error(self):
        result = self._interfere(10.5, params=False)
        self.assertEqual(result["verdict"], "error", result)
        self.assertIn("No module named 'params'", result["detail"])


class GeneratorImportPathTest(unittest.TestCase):
    def test_the_seed_holds_while_gen_step_runs_and_is_restored_after(self):
        # The project is not the working directory, so nothing but the
        # loader can put it on sys.path.
        code = (
            "import json, sys\n"
            "from pathlib import Path\n"
            "from cadgen._internal.generation_runner import rebuilt_identity\n"
            "entry = Path(sys.argv[1]).resolve()\n"
            "project = str(entry.parent)\n"
            "before = project in sys.path\n"
            "identity = rebuilt_identity(entry)\n"
            "print(json.dumps({'before': before, 'after': project in sys.path, 'identity': identity}))\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "cad"
            project.mkdir()
            _project(project, 10.5)
            done = subprocess.run([sys.executable, "-c", code, str(project / "toy.step.py")], cwd=tmp,
                                  capture_output=True, text=True, timeout=300, env=_environment())
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        result = json.loads(done.stdout.strip().splitlines()[-1])
        self.assertFalse(result["before"])
        self.assertFalse(result["after"])
        self.assertTrue(result["identity"])


if __name__ == "__main__":
    unittest.main()
