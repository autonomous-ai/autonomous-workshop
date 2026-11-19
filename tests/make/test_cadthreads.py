"""cad/scripts/cadthreads.py: every CAD tool and the processes it starts get
one BLAS/OpenMP/OCCT thread unless the caller set one, and run as many jobs
at once as the cgroup's free task headroom allows.

Contract: `pin_environ` sets each thread variable the caller left unset and
keeps every one it set; `child_env` pins a copy. A pinned process holds one
thread after loading numpy and build123d and meshing in parallel; a caller's
own value still applies. `default_jobs` takes a tool's `*_JOBS` override
(whole, at least 1), else the free headroom `pids.max - pids.current` of the
tightest enclosing cgroup over one job's tasks, from 1 to the ceiling, else
the cores less two. Every CAD entry pins before it loads numpy, build123d,
OCP or cadgen; the seeded batch's steps run pinned."""

from __future__ import annotations

import os
import re
import runpy
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ROOT / "src/workshop/make/skills"
CAD = SKILLS / "cad/scripts"
TOOL = CAD / "cadthreads.py"
THREADS = runpy.run_path(str(TOOL))

ENTRIES = [CAD / name for name in (
    "check_mesh", "check_overhang", "check_thickness", "check_fit", "check_layout", "check_motion",
    "check_mount", "render_review", "render_product", "render_set", "repair_mesh", "stdpart",
    "verify_project", "gen/__main__.py", "inspect/__main__.py", "cadgen_daemon/__main__.py",
    "artifact/__main__.py")] + [SKILLS / "make-round/scripts" / name
                                for name in ("make_round", "kit_tree.py", "kit_sheets.py")]
HEAVY = re.compile(r"^\s*(?:import|from)\s+(numpy|build123d|OCP|cadgen|scipy|trimesh)\b")

PROBE = r"""
import runpy, sys
runpy.run_path(sys.argv[1])["pin"]()
def threads():
    return int([l for l in open("/proc/self/status") if l.startswith("Threads")][0].split()[1])
import numpy
import build123d as bd
from OCP.BRepMesh import BRepMesh_IncrementalMesh
shape = bd.Box(10, 10, 10) - bd.Cylinder(3, 20)
BRepMesh_IncrementalMesh(shape.wrapped, 0.01, False, 0.1, True)
print(threads())
"""


def unpinned_env(**extra):
    env = {key: value for key, value in os.environ.items()
           if key not in THREADS["THREAD_ENV"] and key != THREADS["OCC_THREADS_ENV"]}
    env.update(extra)
    return env


class PinTest(unittest.TestCase):
    def test_unset_variables_are_pinned_and_set_ones_kept(self):
        env = THREADS["pin_environ"]({"OPENBLAS_NUM_THREADS": "4", "PATH": "/bin"})
        self.assertEqual(env["OPENBLAS_NUM_THREADS"], "4")
        for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
            self.assertEqual(env[key], "1")
        self.assertEqual((env["WORKSHOP_OCC_THREADS"], env["PATH"]), ("1", "/bin"))

    def test_child_env_pins_a_copy(self):
        base = {"PATH": "/bin"}
        env = THREADS["child_env"](base)
        self.assertEqual(base, {"PATH": "/bin"})
        self.assertEqual(env["OMP_NUM_THREADS"], "1")

    def _probe(self, env):
        with tempfile.TemporaryDirectory() as tmp:
            probe = Path(tmp) / "probe.py"
            probe.write_text(PROBE)
            done = subprocess.run([sys.executable, "-I", str(probe), str(TOOL)], env=env, cwd=tmp,
                                  capture_output=True, text=True, timeout=300)
        self.assertEqual(done.returncode, 0, done.stderr)
        return int(done.stdout.split()[-1])

    def test_a_pinned_cad_process_holds_one_thread(self):
        # Unpinned it holds one thread per core per pool (127 at import and
        # about 30 more meshing on the 64-core Workshop host).
        self.assertEqual(self._probe(unpinned_env()), 1)

    def test_a_callers_own_values_apply(self):
        self.assertGreaterEqual(self._probe(unpinned_env(WORKSHOP_OCC_THREADS="3")), 3)


class JobsTest(unittest.TestCase):
    def _cgroups(self, root, limits):
        dirs = []
        for name, (limit, current) in limits.items():
            directory = root / name
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "pids.max").write_text("%s\n" % limit)
            (directory / "pids.current").write_text("%s\n" % current)
            dirs.append(directory)
        return dirs

    def test_headroom_is_the_tightest_enclosing_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirs = self._cgroups(Path(tmp), {"a/b": (9830, 9528), "a": ("max", 12000), "x": (20000, 100)})
            self.assertEqual(THREADS["pids_headroom"](dirs), 302)
            self.assertIsNone(THREADS["pids_headroom"](dirs[1:2]))

    def test_cgroup_dirs_walk_up_to_the_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = Path(tmp) / "cgroup"
            proc.write_text("0::/system.slice/ssh.service\n")
            root = Path(tmp) / "fs"
            self.assertEqual(THREADS["cgroup_dirs"](proc, root),
                             [root / "system.slice/ssh.service", root / "system.slice", root])
            proc.write_text("1:name=systemd:/x\n")
            self.assertEqual(THREADS["cgroup_dirs"](proc, root), [])

    def test_jobs_from_headroom_floor_and_ceiling(self):
        jobs = THREADS["default_jobs"]
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("SOME_JOBS", None)
            self.assertEqual(jobs("SOME_JOBS", headroom=302), 8)           # 302 // 16 = 18, ceiling 8
            self.assertEqual(jobs("SOME_JOBS", headroom=80), 5)
            self.assertEqual(jobs("SOME_JOBS", headroom=3), 1)             # never below 1
            self.assertEqual(jobs("SOME_JOBS", headroom=-50), 1)
            self.assertEqual(jobs("SOME_JOBS", headroom=302, ceiling=4), 4)

    def test_the_tools_override_still_applies(self):
        jobs = THREADS["default_jobs"]
        with mock.patch.dict(os.environ, {"SOME_JOBS": "12"}):
            self.assertEqual(jobs("SOME_JOBS", headroom=3), 12)
        for bad, words in (("0", "at least 1"), ("two", "whole number")):
            with mock.patch.dict(os.environ, {"SOME_JOBS": bad}), self.assertRaisesRegex(ValueError, words):
                jobs("SOME_JOBS")

    def test_without_a_readable_limit_the_cores_less_two(self):
        with mock.patch.dict(THREADS["default_jobs"].__globals__, {"pids_headroom": lambda: None}):
            self.assertEqual(THREADS["default_jobs"](cpus=64), 8)
            self.assertEqual(THREADS["default_jobs"](cpus=4), 2)
            self.assertEqual(THREADS["default_jobs"](cpus=2), 1)


class WiringTest(unittest.TestCase):
    def test_every_cad_entry_pins_before_it_loads_a_numeric_library(self):
        for entry in ENTRIES:
            with self.subTest(entry.relative_to(SKILLS).as_posix()):
                lines = entry.read_text(encoding="utf-8").splitlines()
                pin = next(i for i, line in enumerate(lines) if "cadthreads.py" in line)
                heavy = [i for i, line in enumerate(lines) if HEAVY.match(line)]
                self.assertTrue(all(pin < i for i in heavy), "a numeric import precedes the pin")

    def test_the_job_defaults_read_the_headroom(self):
        from tests.make import test_make_round as make_round_tests

        module = make_round_tests.load_module()
        verify = runpy.run_path(str(CAD / "verify_project"), run_name="verify_project_under_test")
        cache = runpy.run_path(str(CAD / "cadcache.py"))
        with mock.patch.dict(os.environ):
            for name in ("MAKE_ROUND_JOBS", "VERIFY_PROJECT_JOBS", "CADCACHE_JOBS"):
                os.environ.pop(name, None)
            expected = THREADS["default_jobs"]()
            self.assertEqual(verify["verify_jobs"](), expected)
            self.assertEqual(cache["default_jobs"](), expected)
            self.assertEqual(module.round_jobs(), min(expected, module.DEFAULT_ROUND_JOBS))
            os.environ.update(MAKE_ROUND_JOBS="3", VERIFY_PROJECT_JOBS="5", CADCACHE_JOBS="6")
            self.assertEqual((module.round_jobs(), verify["verify_jobs"](), cache["default_jobs"]()), (3, 5, 6))

    def test_the_seeded_batch_runs_its_steps_pinned(self):
        from workshop.make import seeded_batch

        given = {"PATH": os.environ.get("PATH", "/bin"), "OMP_NUM_THREADS": "2"}
        env = seeded_batch.thread_pinned(given)
        self.assertEqual((env["OMP_NUM_THREADS"], env["OPENBLAS_NUM_THREADS"], env["PATH"]),
                         ("2", "1", given["PATH"]))
        result = seeded_batch.environment_runner(given)(
            [sys.executable, "-c", "import os; print(os.environ['OPENBLAS_NUM_THREADS'], "
                                   "os.environ['OMP_NUM_THREADS'])"], Path.cwd(), 60)
        self.assertEqual(result.output.split(), ["1", "2"])


if __name__ == "__main__":
    unittest.main()
