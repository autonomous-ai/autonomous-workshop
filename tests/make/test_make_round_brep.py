"""Issue #101: a round builds each Component once and its checks read that B-rep.

`brepbundle.py build` builds each part once beside `gen` and keeps it as a
native B-rep bundle; make_round uses it only when it is the build `gen`
reported, points every later check of the round at it through the
environment, builds each placed instance once beside it, runs the
independent checks at the same time, and records the B-rep identity each
check read. These tests stand in for the CAD tools; test_brep_bundle_geometry
runs the real ones.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from tests.make import test_make_round as rounds

# The fixtures are reached through the module: a TestCase bound at module
# level here would be collected and run a second time.
load_module = rounds.load_module

BUNDLE_ENV = "WORKSHOP_BREP_BUNDLE"
IDENTITY_ENV = "WORKSHOP_BREP_IDENTITY"


def identity_of(source: Path, instance: int | None = None) -> str:
    tag = source.read_bytes() + (b"" if instance is None else b"#%d" % instance)
    return hashlib.sha256(b"brep " + tag).hexdigest()


def read_back(identity: str) -> str:
    """What a kept build reads back as: a read direction may move one unit in
    the last place, so it can hash apart from the build."""
    return hashlib.sha256(b"read " + identity.encode()).hexdigest()


class KeptBuildRoundTest(unittest.TestCase):
    """A component round of a two-instance wing with a separable Interface on
    both instances: one build, one build per instance, every check reading
    them."""

    _run_root = rounds.InterfaceInstanceTest._run_root
    _contract = rounds.InterfaceInstanceTest._contract
    _main = rounds.InterfaceTest._main
    REFS = rounds.InterfaceInstanceTest.REFS
    INTERFACES = rounds.InterfaceInstanceTest.INTERFACES
    WING = rounds.InterfaceInstanceTest.WING

    def _project(self, tmp, *, keeps=True, reports_bundle=True):
        self.reports_bundle = reports_bundle
        project = rounds.InterfaceTest._project(self, tmp, freeze=False)
        (project / "part_wing.step.py").write_text(self.WING)
        if keeps:
            (project / "cad" / "scripts" / "brepbundle.py").write_text("# fixture brepbundle\n")
        self.assertEqual(self._main(project, ["--shared-helpers"]), 0, self.stderr)
        self.calls.clear()
        return project

    def _fake(self, command, **kwargs):
        tool = Path(command[1]).name
        if tool == "brepbundle.py":
            # Builds the source (or one instance) once and keeps it.
            self.calls.append((command, kwargs))
            entry = Path(command[3])
            number = int(command[command.index("--instance") + 1]) if "--instance" in command else None
            out = Path(command[command.index("--out") + 1])
            built = identity_of(entry, number)
            if number is None and not self.reports_bundle:
                built = "f" * 64      # a build that is not gen's: not used
            manifest = {"entry": str(entry), "instance": number, "identity": read_back(built),
                        "built_identity": built, "max_drift_mm": 1.8e-15}
            out.mkdir(parents=True)
            (out / "manifest.json").write_text(json.dumps(manifest))
            kept = {"path": str(out), "identity": manifest["identity"], "builtIdentity": built, "maxDriftMm": 1.8e-15}
            return subprocess.CompletedProcess(command, 0, json.dumps({"brepBundle": kept}) + "\n", "")
        if tool == "reproduce_build":
            self.calls.append((command, kwargs))
            return subprocess.CompletedProcess(
                command, 0, json.dumps({"identitySha256": identity_of(Path(command[2]))}) + "\n", "")
        done = rounds.InterfaceTest._fake(self, command, **kwargs)
        if tool == "gen":
            payload = {"ok": True, "outcome": "built", "identitySha256": identity_of(Path(command[2]))}
            return subprocess.CompletedProcess(command, 0, json.dumps(payload) + "\n", "")
        env = kwargs.get("extra_env") or {}
        log = kwargs.get("log")
        if BUNDLE_ENV in env and log is not None and tool != "check_motion":
            # A check that read the kept build says so on stderr, which run() logs.
            entry = Path(command[2]).name
            instance = command[command.index("--instance") + 1] if "--instance" in command else None
            bundle = "base" if instance is None else "instance-%s" % instance
            manifest = json.loads((Path(env[BUNDLE_ENV]) / bundle / "manifest.json").read_text())
            if tool == "render_review":
                entry = "part_wing.step.py"
            line = "[brep] %s read %s %s identity %s\n" % (tool, entry, bundle, manifest["identity"])
            Path(log).parent.mkdir(parents=True, exist_ok=True)
            with open(log, "a", encoding="utf-8") as handle:
                handle.write(line)
        return done

    def _round(self, project):
        code = self._main(project, ["--component", "part_wing.step.py"])
        state = json.loads((project / "measure/component-rounds/wing/make-round-state.json").read_text())
        return code, json.loads((Path(state["last_out"]) / "summary.json").read_text())

    def _tools(self):
        return [Path(command[1]).name for command, _ in self.calls]

    def test_the_component_and_each_placed_instance_are_built_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            _code, summary = self._round(project)
            tools = self._tools()
            # gen, the kept build, the reproduction build (#102) and one build
            # per placed instance -- each once, all at the same time.
            self.assertEqual(tools.count("gen"), 1)
            self.assertEqual(tools.count("reproduce_build"), 1)
            self.assertEqual(tools.count("brepbundle.py"), 3)
            out = Path(summary["out"])
            # Kept in cadgen's derived cache, which is never sealed or published.
            kept = project / "__cadgen__/round-brep/component-wing/wing"
            outs = sorted((command[command.index("--out") + 1], command[command.index("--instance") + 1]
                           if "--instance" in command else None)
                          for command, _ in self.calls if Path(command[1]).name == "brepbundle.py")
            self.assertEqual(outs, [(str(kept / "base"), None), (str(kept / "instance-1"), "1"),
                                    (str(kept / "instance-2"), "2")])
            gen = next(command for command, _ in self.calls if Path(command[1]).name == "gen")
            self.assertNotIn("--brep", gen)
            self.assertTrue(summary["checks_ok"], summary)
            self.assertFalse((out / "brep").exists())
            # The next round's bundles replace this one's.
            (kept / "base" / "stale").write_text("from the previous round")
            self._round(project)
            self.assertFalse((kept / "base" / "stale").exists())
            self.assertTrue((kept / "base" / "manifest.json").is_file())

    def test_every_check_reads_the_rounds_build_and_the_round_records_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            _code, summary = self._round(project)
            identity = summary["identity"]
            self.assertEqual(identity, identity_of(project / "part_wing.step.py"))
            checks = [(command, kwargs) for command, kwargs in self.calls
                      if Path(command[1]).name in ("check_thickness", "check_overhang", "check_envelope",
                                                   "render_review")]
            self.assertEqual(len(checks), 5)
            for command, kwargs in checks:
                with self.subTest(tool=Path(command[1]).name):
                    env = kwargs["extra_env"]
                    self.assertEqual(env[BUNDLE_ENV], str(project / "__cadgen__/round-brep/component-wing/wing"))
                    self.assertEqual(env[IDENTITY_ENV], read_back(identity))
            record = summary["brep"]
            self.assertTrue(record["consistent"])
            self.assertEqual(record["kept"]["wing"]["identity"], identity)
            self.assertEqual(record["kept"]["wing"]["read_identity"], read_back(identity))
            self.assertEqual(record["kept"]["wing"]["max_drift_mm"], 1.8e-15)
            self.assertEqual(record["kept"]["wing"]["instances"],
                             {"instance-1": read_back(identity_of(project / "part_wing.step.py", 1)),
                              "instance-2": read_back(identity_of(project / "part_wing.step.py", 2))})
            self.assertEqual(sorted(record["reads"]), ["envelope wing-fold wing#1", "envelope wing-fold wing#2",
                                                       "overhang-wing", "render", "thickness-wing"])
            for check in ("overhang-wing", "thickness-wing", "render"):
                self.assertEqual(record["reads"][check],
                                 [{"entry": "part_wing.step.py", "bundle": "base",
                                   "identity": read_back(identity)}])
            self.assertEqual(record["reads"]["envelope wing-fold wing#2"][0]["identity"],
                             read_back(identity_of(project / "part_wing.step.py", 2)))

    def test_a_read_of_another_build_is_recorded_as_inconsistent(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "brep/wing"
            (root / "base").mkdir(parents=True)
            (root / "base/manifest.json").write_text(json.dumps({"entry": "/p/part_wing.step.py", "identity": "a" * 64}))
            log = Path(tmp) / "thickness-wing.log"
            log.write_text("[brep] check_thickness read part_wing.step.py base identity %s\n" % ("b" * 64))
            kept = {"wing": (root, "a" * 64)}
            record = module.brep_record(kept, {"wing": "c" * 64}, {"thickness-wing": log})
            self.assertFalse(record["consistent"])
            log.write_text("[brep] check_thickness read part_wing.step.py base identity %s\n" % ("a" * 64))
            self.assertTrue(module.brep_record(kept, {"wing": "c" * 64}, {"thickness-wing": log})["consistent"])
            # A check that built from source read nothing kept: an empty list, not a pass.
            log.write_text("part_wing.step.py: 1.00 cm3 solid\n")
            record = module.brep_record(kept, {"wing": "c" * 64}, {"thickness-wing": log})
            self.assertEqual(record["reads"]["thickness-wing"], [])

    def test_without_a_kept_build_the_checks_build_from_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, reports_bundle=False)
            _code, summary = self._round(project)
            for command, kwargs in self.calls:
                self.assertNotIn(BUNDLE_ENV, kwargs.get("extra_env") or {}, command)
            self.assertNotIn("brep", summary)
            self.assertTrue(summary["checks_ok"])

    def test_a_skill_tree_without_kept_builds_runs_as_before(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, keeps=False)
            _code, summary = self._round(project)
            self.assertNotIn("brepbundle.py", self._tools())
            self.assertNotIn("brep", summary)

    def _normalised(self, summary, project):
        text = json.dumps(summary, sort_keys=True).replace(str(project.parents[4]), "<run>")
        return json.loads(text)

    def test_parallel_and_serial_rounds_give_the_same_verdicts_and_record(self):
        results = {}
        for jobs in ("1", "8"):
            with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"MAKE_ROUND_JOBS": jobs}):
                project = self._project(tmp)
                self.faults["envelope"] = {"part_wing.step.py#1"}
                code, summary = self._round(project)
                results[jobs] = (code, self._normalised(summary, project))
        self.assertEqual(results["1"], results["8"])
        self.assertFalse(results["1"][1]["checks_ok"])
        self.assertEqual(results["1"][1]["envelopes"]["wing-fold wing#1"]["verdict"], "FAIL")


class RunAllTest(unittest.TestCase):
    def test_independent_runs_go_at_once_and_return_in_order(self):
        module = load_module()
        barrier = threading.Barrier(3, timeout=10)

        def fake(command, **kwargs):
            barrier.wait()      # times out unless all three run at once
            return subprocess.CompletedProcess(command, 0, command[-1], "")

        jobs = [{"command": ["python", "tool", str(n)], "cwd": ".", "log": Path("x")} for n in range(3)]
        with mock.patch.object(module, "run", side_effect=fake), \
                mock.patch.dict(os.environ, {"MAKE_ROUND_JOBS": "3"}):
            self.assertEqual([done.stdout for done in module.run_all(jobs)], ["0", "1", "2"])

    def test_one_job_runs_them_in_the_order_given(self):
        module = load_module()
        order = []

        def fake(command, **kwargs):
            order.append(command[-1])
            return subprocess.CompletedProcess(command, 0, "", "")

        jobs = [{"command": ["python", "tool", str(n)], "cwd": ".", "log": Path("x")} for n in range(5)]
        with mock.patch.object(module, "run", side_effect=fake), \
                mock.patch.dict(os.environ, {"MAKE_ROUND_JOBS": "1"}):
            module.run_all(jobs)
        self.assertEqual(order, ["0", "1", "2", "3", "4"])

    def test_a_bad_job_count_refuses_the_round(self):
        module = load_module()
        for value in ("0", "many"):
            with self.subTest(value=value), mock.patch.dict(os.environ, {"MAKE_ROUND_JOBS": value}):
                with tempfile.TemporaryDirectory() as tmp:
                    import contextlib
                    import io

                    with contextlib.redirect_stderr(io.StringIO()) as stderr:
                        self.assertEqual(module.main([tmp]), 2)
                    self.assertIn("MAKE_ROUND_JOBS", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
