"""Make-round must report the real motion failures from complete tool output."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tests.make.test_make_round import fake_visual_render, load_module, record_fixture_visual_pass


class MakeRoundMotionEvidenceTest(unittest.TestCase):
    def run_motion(self, stdout, returncode=0, stderr=""):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "product"
            project.mkdir()
            (project / "toy.step.py").write_text("# never executed by these fake tools\n")
            (project / "part_body.step.py").write_text("# deterministic fake export\n")
            measure = project / "measure"
            measure.mkdir()
            (measure / "motion.json").write_text("{}\n")
            skills = root / "skills"
            cad = skills / "cad" / "scripts"
            cad.mkdir(parents=True)
            for name in ("check_thickness", "meshlib.py"):
                (cad / name).write_text("# fake checker identity\n")
            (skills / "image-to-cad" / "scripts").mkdir(parents=True)
            calls = []

            def run(command, *, cwd, log, **kwargs):
                tool = Path(command[1]).name
                calls.append(tool)
                if tool == "export":
                    Path(command[command.index("--stl") + 1]).write_bytes(b"stable fake part")
                    return subprocess.CompletedProcess(command, 0, "exported", "")
                if tool == "render_review":
                    return fake_visual_render(command)
                if tool == "check_thickness":
                    text = "  PASS  wall >= 0.80 mm\nRESULT: printable at this wall\n"
                    log.write_text(text)
                    return subprocess.CompletedProcess(command, 0, text, "")
                if tool == "check_motion":
                    log.write_text(stdout + stderr)
                    return subprocess.CompletedProcess(command, returncode, stdout, stderr)
                raise AssertionError("Unexpected real-tool request: " + tool)

            args = SimpleNamespace(
                project=str(project), entry=None, out=None, all_parts=False,
                nozzle=0.4, refs=[], min=0.90, no_motion=False, full=False, json=True, record_visual=None,
            )
            output = io.StringIO()
            with (
                patch.object(module, "skills_root", return_value=skills),
                patch.object(module, "run", run),
                patch.object(module, "package_version", return_value="1.0"),
                redirect_stdout(output),
            ):
                code = module.make_round(args)
            self.assertEqual(code, 1)
            self.assertEqual(calls, ["export", "check_thickness", "check_motion", "render_review"])
            pending = json.loads(output.getvalue())
            self.assertFalse(pending["ok"])
            self.assertEqual(pending["visual"]["status"], "pending")
            summary = record_fixture_visual_pass(module, project, pending)
            code = 0 if summary["ok"] else 1
            self.assertEqual(summary, json.loads((measure / "rounds/r0001/summary.json").read_text()))
            return code, summary, module.render_summary(summary)

    @staticmethod
    def record(name="rotation", status="pass", detail="clear"):
        return {"id": name, "status": status, "detail": detail}

    def test_native_pretty_json_names_a_failure_before_later_passes(self):
        records = [self.record("clear-%d" % i) for i in range(7)]
        records += [
            self.record("drive-overlap", "fail", "rotor intersects shell"),
            self.record("retention", "pass", "blocked as expected"),
        ]
        stdout = json.dumps({"ok": False, "results": records}, indent=2)
        code, summary, rendered = self.run_motion(stdout, 1)
        self.assertEqual((code, summary["motion"]["verdict"]), (1, "fail"))
        self.assertIn("drive-overlap", summary["motion"]["detail"])
        self.assertIn("rotor intersects shell", summary["motion"]["detail"])
        self.assertIn("drive-overlap", rendered)
        self.assertEqual(summary["motion"]["conditions"], records)

    def test_pretty_json_after_a_banner_retains_all_passing_conditions(self):
        records = [self.record("rotation"), self.record("capture")]
        stdout = "loading assembly\n" + json.dumps({"ok": True, "results": records}, indent=2)
        code, summary, _ = self.run_motion(stdout)
        self.assertEqual((code, summary["motion"]["verdict"]), (0, "pass"))
        self.assertEqual(summary["motion"]["conditions"], records)

    def test_legacy_one_line_results_shapes_remain_readable(self):
        records = [self.record()]
        for payload in ({"results": records}, {"conditions": records}, records):
            with self.subTest(payload=payload):
                code, summary, _ = self.run_motion(json.dumps(payload))
                self.assertEqual((code, summary["motion"]["verdict"]), (0, "pass"))
                self.assertEqual(summary["motion"]["conditions"], records)

    def test_nonzero_process_exit_cannot_be_overridden_by_passing_json(self):
        stdout = json.dumps({"ok": True, "results": [self.record()]})
        for returncode in (1, 2, 124):
            with self.subTest(returncode=returncode):
                code, summary, _ = self.run_motion(stdout, returncode, "tool did not finish")
                self.assertEqual((code, summary["motion"]["verdict"]), (1, "fail"))
                self.assertIn(str(returncode), summary["motion"]["detail"])

    def test_inconclusive_conditions_remain_inconclusive(self):
        records = [self.record("sweep", "inconclusive", "sample step too coarse")]
        stdout = json.dumps({"ok": False, "results": records}, indent=2)
        code, summary, _ = self.run_motion(stdout, 1)
        self.assertEqual((code, summary["motion"]["verdict"]), (1, "inconclusive"))
        self.assertIn("sample step too coarse", summary["motion"]["detail"])

    def test_missing_empty_or_unknown_condition_evidence_cannot_pass(self):
        outputs = [
            "", "not json", "{}", '{"results":[]}', '{"results":[null]}',
            json.dumps({"results": [self.record(status="unknown")]}),
            json.dumps({"results": [{"id": "rotation"}]}),
        ]
        for stdout in outputs:
            with self.subTest(stdout=stdout):
                code, summary, _ = self.run_motion(stdout)
                self.assertEqual(code, 1)
                self.assertNotEqual(summary["motion"]["verdict"], "pass")

    def test_truncated_envelope_cannot_be_replaced_by_its_last_passing_object(self):
        stdout = '{"results": [\n  ' + json.dumps(self.record()) + "\n"
        code, summary, _ = self.run_motion(stdout)
        self.assertEqual(code, 1)
        self.assertNotEqual(summary["motion"]["verdict"], "pass")
        self.assertEqual(summary["motion"]["conditions"], [])

    def test_explicit_unsuccessful_payload_cannot_pass_with_zero_exit(self):
        stdout = json.dumps({"ok": False, "results": [self.record()]})
        code, summary, _ = self.run_motion(stdout)
        self.assertEqual((code, summary["motion"]["verdict"]), (1, "fail"))

    def test_complete_condition_details_remain_available_beyond_compact_summary(self):
        records = [
            self.record("first", "fail", "rotor intersects shell"),
            self.record("second", "inconclusive", "unmeasured contact"),
            self.record("last", "pass", "clear"),
        ]
        code, summary, rendered = self.run_motion(json.dumps({"ok": False, "results": records}, indent=2), 1)
        self.assertEqual(code, 1)
        self.assertEqual(summary["motion"]["conditions"], records)
        self.assertIn("first", rendered)
        self.assertNotIn('"results"', rendered)


    def test_tool_error_exit_keeps_inconclusive_evidence_but_fails_the_round(self):
        records = [self.record("sweep", "inconclusive", "sample step too coarse")]
        code, summary, _ = self.run_motion(json.dumps({"ok": False, "results": records}), 2)
        self.assertEqual((code, summary["motion"]["verdict"]), (1, "fail"))
        self.assertIn("exit 2", summary["motion"]["detail"])
        self.assertEqual(summary["motion"]["conditions"], records)

    def test_timeout_byte_output_cannot_crash_or_supply_a_pass(self):
        module = load_module()
        stdout = json.dumps({"ok": True, "results": [self.record()]}).encode()
        motion = module.parse_motion(stdout, 124, b"deadline exceeded")
        self.assertEqual(motion["verdict"], "fail")
        self.assertIn("124", motion["detail"])

    def test_invalid_condition_types_or_ids_cannot_supply_a_pass(self):
        records = [
            {"id": "", "status": "pass"},
            {"id": None, "status": "pass"},
            {"id": "sweep", "status": ["pass"]},
            {"id": "sweep", "status": "pass", "detail": {}},
        ]
        for record in records:
            with self.subTest(record=record):
                code, summary, _ = self.run_motion(json.dumps({"results": [record]}))
                self.assertEqual(code, 1)
                self.assertNotEqual(summary["motion"]["verdict"], "pass")


if __name__ == "__main__":
    unittest.main()
