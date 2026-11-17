"""Final verification runs its print gates and inspect batch side by side
(2026-11-17): the Kyoto tray's 225 print-gate checks took 1714 s and its
153-request inspect batch 1184 s, one after another. Side by side, every
verdict, report, record and line of output is the one the sequential run
gives, in the same order; only the timings differ."""

from __future__ import annotations

import contextlib
import io
import json
import os
import random
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from workshop.runtime.package_data import product_run_domain_skill_roots
from tests.make.test_kit_print_parts import CABINET, described
from tests.make.test_kit_tree import sealed_kit

ROOTS = product_run_domain_skill_roots()
VERIFIER = ROOTS["cad"] / "scripts" / "verify_project"

# Printed objects that pass and fail each gate, one that does not build, and
# an assembly of them for the inspect batch.
PARTS = {
    "plate": "Pos(0, 0, 1) * Box(30, 20, 2)",
    "ledge": "Pos(0, 0, 5) * Box(6, 6, 10) + Pos(8, 0, 9) * Box(12, 6, 2)",
    "fin": "Pos(0, 0, 4) * Box(20, 0.4, 8) + Pos(0, 0, 0.5) * Box(20, 8, 1)",
    "post": "fillet((Pos(0, 0, 10) * Cylinder(6, 20)).edges().group_by(Axis.Z)[-1], 2)",
}
PART = """\
from build123d import Axis, Box, Cylinder, Pos, fillet

def gen_step():
    return {shape}
"""
SHEET = "from build123d import Box\n\ndef gen_step():\n    return Box(10, 10, 2).faces().sort_by()[0]\n"
BROKEN = "def gen_step():\n    raise RuntimeError('this part does not build')\n"
ASSEMBLY = """\
from build123d import Axis, Box, Compound, Cylinder, Pos, fillet

def gen_step():
    shapes = [{shapes}]
    return Compound(children=[Pos(40 * i, 0, 0) * shape for i, shape in enumerate(shapes)])
"""
TIMING = re.compile(r" in \d+\.\d+s$", re.MULTILINE)


def _needs_cad(test):
    try:
        import build123d  # noqa: F401
    except ImportError:  # pragma: no cover - the CAD runtime is part of the dev environment
        test.skipTest("build123d is not installed")


class RealToolsTest(unittest.TestCase):
    """The real gates and inspect batch, one after another and side by side,
    on the same project."""

    def setUp(self):
        _needs_cad(self)
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name).resolve()
        for name, shape in PARTS.items():
            (self.project / ("part_%s.step.py" % name)).write_text(PART.format(shape=shape))
        (self.project / "part_broken.step.py").write_text(BROKEN)
        (self.project / "toy.step.py").write_text(ASSEMBLY.format(shapes=", ".join(PARTS.values())))
        (self.project / "measure").mkdir()
        self.verifier = runpy.run_path(str(VERIFIER))
        self.printables = sorted(self.project.glob("part_*.step.py"))

    def _run(self, jobs: str, action):
        runner = self.verifier["Runner"](cwd=self.project, dry_run=False, verbose=False)
        with mock.patch.dict(os.environ, {"VERIFY_PROJECT_JOBS": jobs, "PYTHONDONTWRITEBYTECODE": "1"}), \
                contextlib.redirect_stdout(io.StringIO()) as printed:
            started = time.perf_counter()
            code = action(runner)
            elapsed = time.perf_counter() - started
        reports = {path.name: path.read_bytes() for path in sorted((self.project / "measure").glob("*.md"))}
        shutil.rmtree(self.project / "measure")
        (self.project / "measure").mkdir()
        return {"code": code, "output": TIMING.sub("", printed.getvalue()), "reports": reports,
                "records": [(record["command"], record["status"]) for record in runner.records],
                "checks": runner.inspection_checks}, elapsed

    def _same_side_by_side(self, action):
        one, _ = self._run("1", action)
        many, _ = self._run("4", action)
        self.assertEqual(many["code"], one["code"])
        self.assertEqual(many["records"], one["records"])
        self.assertEqual(many["checks"], one["checks"])
        self.assertEqual(many["reports"].keys(), one["reports"].keys())
        for name in one["reports"]:
            with self.subTest(report=name):
                self.assertEqual(many["reports"][name], one["reports"][name])
        self.assertEqual(many["output"], one["output"])
        return one

    def test_the_print_gates_side_by_side_report_byte_for_byte_as_one_after_another(self):
        def gates(runner):
            return self.verifier["_run_print_gates"](runner, self.project, self.printables, bed=(256.0, 256.0, 256.0),
                                                     nozzle=0.4, skip_thickness=False, overhang_angle=45.0)

        one = self._same_side_by_side(gates)
        self.assertEqual(one["code"], 1, "the fin, the ledge and the broken part fail")
        statuses = {(command.split()[1].rsplit("/", 1)[-1], command.split()[2]): status
                    for command, status in one["records"] if " # " not in command}
        # The fixture holds a pass and a failure of every gate.
        for tool in ("check_mesh", "check_overhang", "check_thickness"):
            seen = {status for (name, _part), status in statuses.items() if name == tool}
            self.assertIn("rc=0", seen, tool)
            self.assertTrue(seen - {"rc=0"}, tool)
        self.assertIn(("check_overhang:broken", "skipped"),
                      {(command.split()[0], status) for command, status in one["records"]})
        self.assertEqual(len(one["reports"]), 8, sorted(one["reports"]))

    def test_the_inspect_batch_side_by_side_answers_as_one_process(self):
        # inspect reads the whole project, so a part that does not build
        # would fail every request; a sheet with no solid fails validate.
        (self.project / "part_broken.step.py").unlink()
        (self.project / "part_sheet.step.py").write_text(SHEET)
        entries = ["toy.step.py", *sorted(path.name for path in self.project.glob("part_*.step.py"))]
        # As final verification does first: every entry writes its STEP.
        built = subprocess.run([sys.executable, str(ROOTS["cad"] / "scripts" / "gen"), *entries, "--write"],
                               cwd=self.project, capture_output=True, text=True, timeout=600)
        self.assertEqual(built.returncode, 0, built.stdout + built.stderr)

        def inspect(runner):
            return self.verifier["_inspect_geometry"](runner, entries)

        one = self._same_side_by_side(inspect)
        self.assertEqual(one["code"], 1, "the sheet fails validate")
        self.assertEqual(len(one["checks"]), 2 * len(entries) + 1)
        failed = {check["id"] for check in one["checks"] if check["status"] != "passed"}
        self.assertEqual(failed, {"validate:part_sheet"})
        self.assertEqual(len(one["records"]), 1, "one record for the whole batch, as before")


class InspectGroupsTest(unittest.TestCase):
    def test_each_entry_is_one_run_and_the_runs_keep_the_order(self):
        verifier = runpy.run_path(str(VERIFIER))
        requests = [{"id": "refs:assembly", "argv": ["refs", "toy.step.py"]},
                    {"id": "validate:assembly", "argv": ["validate", "toy.step.py"]},
                    {"id": "interfere:assembly", "argv": ["interfere", "toy.step.py"]},
                    {"id": "refs:a", "argv": ["refs", "part_a.step.py"]},
                    {"id": "validate:a", "argv": ["validate", "part_a.step.py"]},
                    {"id": "odd", "argv": ["refs"]},
                    {"id": "refs:toy-again", "argv": ["refs", "toy.step.py"]}]
        groups = verifier["inspect_groups"](requests)
        self.assertEqual([[request["id"] for request in group] for group in groups],
                         [["refs:assembly", "validate:assembly", "interfere:assembly"],
                          ["refs:a", "validate:a"], ["odd"], ["refs:toy-again"]])
        self.assertEqual([request for group in groups for request in group], requests)

    def test_a_crashed_entry_fails_the_batch_and_the_others_still_answer(self):
        verifier = runpy.run_path(str(VERIFIER))
        runner = verifier["Runner"](cwd=Path.cwd(), dry_run=False, verbose=False)
        requests = [{"id": "refs:a", "argv": ["refs", "a.step.py"]}, {"id": "refs:b", "argv": ["refs", "b.step.py"]}]

        def fake_run(argv, *, input, **_kwargs):
            request = json.loads(input)
            if request["id"] == "refs:a":
                return mock.Mock(returncode=1, stdout="")
            return mock.Mock(returncode=0, stdout=json.dumps({"id": request["id"], "ok": True, "exitCode": 0}) + "\n")

        with mock.patch.dict(os.environ, {"VERIFY_PROJECT_JOBS": "4"}), \
                mock.patch.object(verifier["subprocess"], "run", side_effect=fake_run), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = runner.inspect_batch(requests)
        self.assertEqual(code, 1)
        self.assertEqual(runner.inspection_checks, [{"id": "refs:b", "status": "passed"}])
        self.assertEqual(runner.records[0]["status"], "rc=1")


class KitOrderTest(unittest.TestCase):
    """A kit's Component builds and Part gates side by side keep the
    sequential record: the targets, then each Component's build, its notes
    and its Parts, whatever order they finish in."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name)
        (self.project / "tree").mkdir()
        (self.project / "tree" / "kit.json").write_text(json.dumps(sealed_kit()))
        self.parts = []
        for role in ("case", "cabinet", "desk"):
            path = self.project / ("part_%s.step.py" % role)
            path.write_text("PRINTABLE = False\ndef gen_step(): pass\ndef print_parts(): pass\n")
            self.parts.append(path)
        self.plain = self.project / "part_stand.step.py"
        self.plain.write_text("def gen_step(): pass\n")
        self.verifier = runpy.run_path(str(VERIFIER))

    def _run(self, jobs: str, seed: int):
        shuffle = random.Random(seed)
        describes = {"case": described(["A01-case-shell"]), "cabinet": {**described(CABINET),
                                                                        "unkept": {"D01-inkwell": "two reads disagree"}},
                     # Not the desk's printed Parts: refused, nothing gated.
                     "desk": described(["C01-desk-body", "Z99-stray"])}

        class Timed(self.verifier["Runner"]):
            def command(self, argv, **kwargs):
                args = [str(item) for item in argv]
                time.sleep(shuffle.random() * 0.02)
                tool = Path(args[1]).name
                self._write("[verify_project] %s\n" % " ".join(Path(arg).name for arg in args[1:3]))
                if tool == "kit_print_parts.py":
                    role = Path(args[3]).name.removeprefix("part_").removesuffix(".step.py")
                    self.last_stdout = json.dumps(describes[role]) + "\n"
                    code = 0
                else:
                    name = Path(args[2]).name
                    code = 1 if (name, tool) in {("part_B02-cabinet-door.step.py", "check_thickness"),
                                                 ("part_stand.step.py", "check_mesh")} else 0
                self.records.append({"command": " ".join(args[1:]), "status": "rc=%d" % code,
                                     "env": sorted((kwargs.get("env_extra") or {}).items())})
                return code

        runner = Timed(cwd=self.project, dry_run=False, verbose=False)
        with mock.patch.dict(os.environ, {"VERIFY_PROJECT_JOBS": jobs}), \
                contextlib.redirect_stdout(io.StringIO()) as printed:
            code = self.verifier["_run_print_gates"](runner, self.project, [self.plain, *self.parts],
                                                     bed=(220.0, 220.0, 220.0), nozzle=0.4, skip_thickness=False,
                                                     overhang_angle=45.0, parts=self.parts)
        return code, runner.records, printed.getvalue()

    def test_side_by_side_records_and_prints_in_the_sequential_order(self):
        one = self._run("1", 0)
        self.assertEqual(one[0], 1)
        tools = [Path(record["command"].split()[0]).name for record in one[1]]
        self.assertEqual(tools[0], "check_mesh", "the stand first")
        self.assertIn("print parts  # FAILED", "".join(record["command"] for record in one[1]))
        self.assertIn("cabinet/D01-inkwell gated from source: two reads disagree", one[2])
        for seed in range(5):
            with self.subTest(seed=seed):
                self.assertEqual(self._run("4", seed), one)


if __name__ == "__main__":
    unittest.main()
