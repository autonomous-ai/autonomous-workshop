"""Wall evidence must survive successive Make rounds without false progress."""
from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from workshop.runtime.package_data import product_run_domain_skill_roots

SCRIPT = product_run_domain_skill_roots()["make-round"] / "scripts" / "make_round"


def load_module():
    spec = importlib.util.spec_from_loader("make_round_wall_evidence", loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = str(SCRIPT)
    exec(compile(SCRIPT.read_text(), str(SCRIPT), "exec"), module.__dict__)
    return module


class MakeRoundWallEvidenceTest(unittest.TestCase):
    @contextmanager
    def fixture(self, *, split=True):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "product"
            project.mkdir()
            (project / "toy.step.py").write_text("# not executed by these fake tools\n")
            if split:
                (project / "part_wall.step.py").write_text("# supplied printable part\n")
            skills = root / "skills"
            cad = skills / "cad" / "scripts"
            cad.mkdir(parents=True)
            for name in ("check_thickness", "meshlib.py"):
                (cad / name).write_text("# checker revision one\n")
            (skills / "image-to-cad" / "scripts").mkdir(parents=True)
            control = {
                "bytes": b"same exported part", "returncode": 0,
                "stdout": "  PASS  wall >= 0.80 mm\n", "export_failure": False,
                "package_version": "1.0",
            }
            calls = []

            def run(command, *, cwd, log, **kwargs):
                tool = Path(command[1]).name
                calls.append(tool)
                if tool == "export":
                    if control["export_failure"]:
                        return subprocess.CompletedProcess(command, 1, "", "export failed")
                    target = Path(command[command.index("--stl") + 1])
                    target.write_bytes(control["bytes"])
                    return subprocess.CompletedProcess(command, 0, "exported", "")
                if tool == "check_thickness":
                    log.write_text(control["stdout"])
                    return subprocess.CompletedProcess(command, control["returncode"], control["stdout"], "")
                raise AssertionError("Unexpected tool: " + tool)

            args = SimpleNamespace(
                project=str(project), entry=None, out=None, all_parts=False,
                nozzle=0.4, refs=[], min=0.90, no_motion=False, full=False, json=True,
            )
            with (
                patch.object(module, "skills_root", return_value=skills),
                patch.object(module, "run", run),
                patch.object(module, "package_version", side_effect=lambda name: control["package_version"]),
            ):
                yield module, args, control, calls, cad

    def run_round(self, module, args):
        output = io.StringIO()
        with redirect_stdout(output):
            code = module.make_round(args)
        return code, json.loads(output.getvalue())

    def fail_wall(self, control):
        control.update(returncode=1, stdout="  FAIL  wall >= 0.80 mm\nRESULT: WALL BELOW MINIMUM\n")

    def test_unchanged_failed_part_does_not_become_a_pass(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.fail_wall(control)
            first = self.run_round(module, args)
            second = self.run_round(module, args)
            self.assertEqual((first[0], second[0]), (1, 1))
            self.assertEqual(second[1]["thickness"]["wall"]["verdict"], "FAIL")
            self.assertEqual(calls.count("check_thickness"), 2)

    def test_unchanged_success_retains_its_passing_evidence_without_rechecking(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            code, summary = self.run_round(module, args)
            self.assertEqual(code, 0)
            self.assertEqual(summary["thickness"]["wall"]["verdict"], "PASS")
            self.assertEqual(summary["checked"], [])
            self.assertEqual(summary["reused"], ["wall"])
            self.assertEqual(summary["thickness"]["wall"]["measured_round"], 1)
            self.assertEqual(summary["changed"], [])
            self.assertEqual(calls.count("check_thickness"), 1)

    def test_changed_nozzle_requires_new_evidence(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            args.nozzle = 0.6
            self.fail_wall(control)
            self.assertEqual(self.run_round(module, args)[0], 1)
            self.assertEqual(calls.count("check_thickness"), 2)

    def test_changed_checker_or_mesh_helper_requires_new_evidence(self):
        for name in ("check_thickness", "meshlib.py"):
            with self.subTest(source=name), self.fixture() as (module, args, control, calls, cad):
                self.assertEqual(self.run_round(module, args)[0], 0)
                (cad / name).write_text("# checker revision two\n")
                self.fail_wall(control)
                self.assertEqual(self.run_round(module, args)[0], 1)
                self.assertEqual(calls.count("check_thickness"), 2)

    def test_changed_mesh_requires_new_evidence(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            control["bytes"] = b"repaired geometry with another defect"
            self.fail_wall(control)
            self.assertEqual(self.run_round(module, args)[0], 1)
            self.assertEqual(calls.count("check_thickness"), 2)

    def test_old_cache_with_only_hashes_cannot_supply_a_pass(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            state_path = Path(args.project) / "measure" / module.STATE_NAME
            state = json.loads(state_path.read_text())
            state = {key: value for key, value in state.items() if key in ("round", "parts", "poses_path", "likeness", "last_out")}
            state_path.write_text(json.dumps(state))
            self.fail_wall(control)
            self.assertEqual(self.run_round(module, args)[0], 1)
            self.assertEqual(calls.count("check_thickness"), 2)

    def test_tool_failure_is_not_overridden_by_missing_failure_text(self):
        with self.fixture() as (module, args, control, calls, cad):
            control.update(returncode=1, stdout="")
            code, summary = self.run_round(module, args)
            self.assertEqual(code, 1)
            self.assertEqual(summary["thickness"]["wall"]["verdict"], "FAIL")

    def test_one_piece_entry_is_wall_checked(self):
        with self.fixture(split=False) as (module, args, control, calls, cad):
            self.fail_wall(control)
            code, summary = self.run_round(module, args)
            self.assertEqual(code, 1)
            self.assertEqual(summary["parts"], ["toy"])
            self.assertEqual(calls, ["export", "check_thickness"])

    def test_failed_export_cannot_reuse_an_earlier_pass(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            control["export_failure"] = True
            code, summary = self.run_round(module, args)
            self.assertEqual(code, 1)
            self.assertEqual(summary["parts"], ["wall"])
            self.assertEqual(summary["reused"], [])

    def test_all_parts_forces_rechecking_a_previously_passing_part(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            args.all_parts = True
            self.fail_wall(control)
            self.assertEqual(self.run_round(module, args)[0], 1)
            self.assertEqual(calls.count("check_thickness"), 2)


    def test_changed_package_version_requires_new_evidence(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            control["package_version"] = "2.0"
            self.fail_wall(control)
            self.assertEqual(self.run_round(module, args)[0], 1)
            self.assertEqual(calls.count("check_thickness"), 2)

    def test_missing_measurement_context_never_allows_reuse(self):
        with self.fixture() as (module, args, control, calls, cad):
            with patch.object(module, "package_version", side_effect=module.PackageNotFoundError("numpy")):
                self.assertEqual(self.run_round(module, args)[0], 0)
                self.fail_wall(control)
                self.assertEqual(self.run_round(module, args)[0], 1)
            self.assertEqual(calls.count("check_thickness"), 2)

    def test_missing_or_changed_measurement_log_requires_new_evidence(self):
        for action in ("remove", "change"):
            with self.subTest(action=action), self.fixture() as (module, args, control, calls, cad):
                code, summary = self.run_round(module, args)
                self.assertEqual(code, 0)
                log = Path(summary["thickness"]["wall"]["log"])
                if action == "remove":
                    log.unlink()
                else:
                    log.write_text("different evidence")
                self.fail_wall(control)
                self.assertEqual(self.run_round(module, args)[0], 1)
                self.assertEqual(calls.count("check_thickness"), 2)

    def test_success_exit_without_a_wall_result_cannot_supply_a_pass(self):
        for stdout in ("", "  PASS  bed fit\n", "Traceback: interrupted\n"):
            with self.subTest(stdout=stdout), self.fixture() as (module, args, control, calls, cad):
                control["stdout"] = stdout
                self.assertEqual(self.run_round(module, args)[0], 1)

    def test_nonzero_exit_wins_over_a_passing_line(self):
        for returncode in (1, 2, 124, -9):
            with self.subTest(returncode=returncode), self.fixture() as (module, args, control, calls, cad):
                control["returncode"] = returncode
                code, summary = self.run_round(module, args)
                self.assertEqual(code, 1)
                self.assertEqual(summary["thickness"]["wall"]["verdict"], "FAIL")
                self.assertIn("exit %d" % returncode, summary["thickness"]["wall"]["failures"][0])

    def test_all_parts_does_not_claim_an_unchanged_mesh_was_repaired(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.assertEqual(self.run_round(module, args)[0], 0)
            args.all_parts = True
            code, summary = self.run_round(module, args)
            self.assertEqual(code, 0)
            self.assertEqual(summary["changed"], [])
            self.assertEqual(summary["checked"], ["wall"])
            self.assertEqual(summary["reused"], [])

    def test_failed_wall_can_pass_after_a_successful_recheck(self):
        with self.fixture() as (module, args, control, calls, cad):
            self.fail_wall(control)
            self.assertEqual(self.run_round(module, args)[0], 1)
            control.update(returncode=0, stdout="RESULT: printable at this wall\n")
            code, summary = self.run_round(module, args)
            self.assertEqual(code, 0)
            self.assertEqual(summary["thickness"]["wall"]["measured_round"], 2)
            self.assertEqual(calls.count("check_thickness"), 2)


if __name__ == "__main__":
    unittest.main()
