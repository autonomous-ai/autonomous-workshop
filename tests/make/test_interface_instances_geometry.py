"""Issue #80: instances of one Unique Geometry, built and placed on real B-reps.

A Component file whose geometry has count above 1 builds instance n with
``gen_step(instance=n)`` and places it with ``assembly_pose(shape, pose,
instance)``. check_envelope checks one instance against its side of a Keep-out
Envelope, and make_round's generated interface entry places each referenced
instance as its own labelled child.
"""

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import build123d  # noqa: F401 - the B-rep kernel these checks need

SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/make-round/scripts"
CHECK_ENVELOPE = SCRIPTS / "check_envelope"

# Two 10 mm wing roots: instance 1 at x 0..10, instance 2 mirrored at x -10..0
# and 2 mm taller, so a wrong variant or a wrong placement shows in volumes.
WING = """from build123d import Align, Box, Pos


def gen_step(instance=1):
    return Box(10, 10, 4 if instance == 1 else 6, align=(Align.MIN, Align.MIN, Align.MIN))


def assembly_pose(shape, pose, instance):
    return shape if instance == 1 else Pos(-10, 0, 0) * shape
"""
# A wing that ignores the instance number: identical copies, placed apart.
TWIN = """from build123d import Align, Box, Pos


def gen_step():
    return Box(10, 10, 4, align=(Align.MIN, Align.MIN, Align.MIN))


def assembly_pose(shape, pose, instance):
    return shape if instance == 1 else Pos(-10, 0, 0) * shape
"""
NO_HOOK = """from build123d import Box


def gen_step():
    return Box(10, 10, 4)


def assembly_pose(shape, pose):
    return shape
"""


def envelope(low, high):
    return {"inside": "wing#2", "outside": "wing#1",
            "shapes": [{"pose": "folded", "box": {"min_mm": low, "max_mm": high}}]}


class CheckEnvelopeInstanceTest(unittest.TestCase):
    def _check(self, source, role, instance, low, high):
        with tempfile.TemporaryDirectory() as tmp:
            part = Path(tmp) / "part_wing.step.py"
            part.write_text(source)
            sealed = Path(tmp) / "envelope.json"
            sealed.write_text(json.dumps(envelope(low, high)))
            done = subprocess.run([sys.executable, str(CHECK_ENVELOPE), str(part), "--envelope", str(sealed),
                                   "--role", role, "--instance", str(instance), "--json"],
                                  capture_output=True, text=True, timeout=300)
        return done.returncode, json.loads(done.stdout.strip().splitlines()[-1])

    def test_each_instance_keeps_its_own_side(self):
        # The envelope holds the left half (instance 2's place), 6 mm tall.
        code, result = self._check(WING, "inside", 2, [-10, 0, 0], [0, 10, 6.5])
        self.assertEqual((code, result["ok"]), (0, True), result)
        code, result = self._check(WING, "outside", 1, [-10, 0, 0], [0, 10, 6.5])
        self.assertEqual((code, result["ok"]), (0, True), result)

    def test_the_variant_of_the_named_instance_is_built(self):
        # Instance 2 is 6 mm tall: a 5 mm envelope leaves 100 mm3 outside.
        code, result = self._check(WING, "inside", 2, [-10, 0, 0], [0, 10, 5])
        self.assertEqual(code, 1)
        self.assertAlmostEqual(result["poses"][0]["outside_mm3"], 100.0, places=3)

    def test_the_named_instance_is_placed_where_its_hook_puts_it(self):
        code, result = self._check(WING, "outside", 2, [-10, 0, 0], [0, 10, 6.5])
        self.assertEqual(code, 1)
        self.assertAlmostEqual(result["poses"][0]["inside_mm3"], 600.0, places=3)

    def test_a_file_that_ignores_the_instance_builds_identical_copies(self):
        code, result = self._check(TWIN, "inside", 2, [-10, 0, 0], [0, 10, 4.5])
        self.assertEqual((code, result["ok"]), (0, True), result)

    def test_a_placement_hook_without_the_instance_is_refused_by_name(self):
        code, result = self._check(NO_HOOK, "inside", 2, [-10, 0, 0], [0, 10, 6.5])
        self.assertEqual(code, 1)
        self.assertIn("assembly_pose(shape, pose, instance)", result["detail"])


class InterfaceEntryInstanceTest(unittest.TestCase):
    def test_each_instance_is_a_distinct_labelled_placed_child(self):
        spec = importlib.util.spec_from_loader("make_round_script", loader=None)
        make_round = importlib.util.module_from_spec(spec)
        make_round.__file__ = str(SCRIPTS / "make_round")
        exec(compile((SCRIPTS / "make_round").read_text(encoding="utf-8"), make_round.__file__, "exec"),
             make_round.__dict__)
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "part_wing.step.py").write_text(WING)
            (project / "part_core.step.py").write_text(
                "from build123d import Box, Pos\n"
                "def gen_step(): return Box(2, 2, 2)\n"
                "def assembly_pose(shape, pose): return Pos(0, 20, 0) * shape\n")
            entry = project / "interface_entry.step.py"
            entry.write_text(make_round.INTERFACE_ENTRY % {
                "id": "wing-sector-mesh", "project": str(project), "components": ["wing#1", "wing#2", "core"]})
            spec = importlib.util.spec_from_file_location("interface_entry", entry)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            compound = module.gen_step()
        children = {child.label: child for child in compound.children}
        self.assertEqual(sorted(children), ["core", "wing#1", "wing#2"])
        self.assertAlmostEqual(children["wing#1"].volume, 400.0, places=3)
        self.assertAlmostEqual(children["wing#2"].volume, 600.0, places=3)
        self.assertAlmostEqual(children["wing#2"].bounding_box().min.X, -10.0, places=3)
        self.assertAlmostEqual(children["wing#1"].bounding_box().min.X, 0.0, places=3)
        self.assertAlmostEqual(children["core"].bounding_box().center().Y, 20.0, places=3)


if __name__ == "__main__":
    unittest.main()
