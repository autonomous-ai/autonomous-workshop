"""Render time allowances never substitute for current visual evidence."""

from contextlib import contextmanager, redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from tests.make.test_make_round import (
    _gate_output,
    _install_gate_identity,
    fake_visual_render,
    load_module,
    record_fixture_visual_pass,
)


class MakeRoundRenderTimeoutTest(unittest.TestCase):
    @contextmanager
    def fixture(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "toy.step.py").write_text("# combined fixture\n")
            (project / "part_wheel.step.py").write_text("# part fixture\n")
            _install_gate_identity(project)
            calls = []
            control = {"timeout": False}

            def subprocess_run(command, **kwargs):
                tool = Path(command[1]).name
                calls.append((tool, kwargs["timeout"]))
                if tool == "gen":
                    Path(command[2]).with_suffix("").write_bytes(b"same STEP")
                    return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")
                if tool in ("check_thickness", "check_overhang"):
                    stdout, code = _gate_output(tool, fails=False)
                    return subprocess.CompletedProcess(command, code, stdout, "")
                if tool == "render_review":
                    if control["timeout"]:
                        # Even completed-looking files cannot make a timed-out
                        # subprocess count as successful evidence.
                        fake_visual_render(command)
                        raise subprocess.TimeoutExpired(
                            command, kwargs["timeout"],
                            output=b"partial render output\n", stderr=b"partial diagnostic\n",
                        )
                    return fake_visual_render(command)
                if tool == "verify_project":
                    return subprocess.CompletedProcess(command, 0, "fixture verified", "")
                raise AssertionError(tool)

            with (
                patch.object(module, "skills_root", return_value=project),
                patch.object(module.subprocess, "run", side_effect=subprocess_run),
                redirect_stdout(io.StringIO()),
            ):
                yield module, project, control, calls

    def summary(self, project, number):
        return json.loads((project / f"measure/rounds/r{number:04d}/summary.json").read_text())

    def test_default_and_explicit_timeout_apply_only_to_visual_subprocess(self):
        for extra, expected in (
            ([], 900), (["--render-timeout", "2400.5"], 2400.5),
            (["--render-timeout", "2147483"], 2147483),
        ):
            with self.subTest(timeout=expected), self.fixture() as (module, project, _, calls):
                self.assertEqual(module.main([str(project), *extra]), 1)
                self.assertEqual(calls, [
                    ("gen", 900), ("check_thickness", 900),
                    ("check_overhang", 900), ("render_review", expected),
                ])
                summary = self.summary(project, 1)
                self.assertEqual(summary["visual"]["timeout_seconds"], expected)
                self.assertEqual(summary["visual"]["status"], "pending")
                self.assertFalse(summary["ok"])
                packet = json.loads(Path(summary["visual"]["packet"]).read_text())
                self.assertEqual({Path(path).name for path in packet["images"]},
                                 {"front.png", "top.png", "iso.png"})
                feedback = Path(summary["out"]) / "feedback.json"
                feedback.write_text(json.dumps({
                    "packet_sha256": summary["visual"]["packet_sha256"],
                    "status": "pass", "findings": [], "observation": "Fixture inspection.",
                }))
                # The optional final verifier retains its separate allowance.
                module.record_visual(project, feedback, full=True)
                self.assertEqual(calls[-1], ("verify_project", 1800))
                self.assertTrue(self.summary(project, 1)["ok"])

    def test_timeout_requires_new_round_and_current_feedback_despite_retained_print_pass(self):
        with self.fixture() as (module, project, control, calls):
            control["timeout"] = True
            self.assertEqual(module.main([str(project)]), 1)
            first = self.summary(project, 1)
            self.assertTrue(first["checks_ok"])
            self.assertFalse(first["ok"])
            self.assertEqual(first["visual"]["status"], "error")
            self.assertNotIn("packet", first["visual"])
            first_dir = Path(first["out"])
            self.assertFalse((first_dir / "visual-packet.json").exists())
            self.assertIn("--render-timeout", first["visual"]["detail"])
            self.assertEqual((first_dir / "visual-render.log").read_text(),
                             "TIMEOUT after 900s\npartial render output\n\npartial diagnostic\n")
            feedback = project / "measure/feedback.json"
            feedback.write_text(json.dumps({
                "packet_sha256": "0" * 64, "status": "pass", "findings": [],
                "observation": "External images cannot repair an error round.",
            }))
            with self.assertRaisesRegex(ValueError, "only accepted once for a pending round"):
                module.record_visual(project, feedback)
            self.assertEqual(self.summary(project, 1), first)

            calls.clear()
            control["timeout"] = False
            self.assertEqual(module.main([str(project), "--render-timeout", "2700"]), 1)
            second = self.summary(project, 2)
            self.assertEqual(calls, [("gen", 900), ("render_review", 2700)])
            self.assertEqual(second["reused"], ["wheel"])
            self.assertEqual(second["print"], first["print"])
            self.assertEqual(second["visual"]["status"], "pending")
            self.assertFalse(second["ok"])
            source = project / "toy.step.py"
            original = source.read_bytes()
            source.write_text("# changed after rendering\n")
            with self.assertRaisesRegex(ValueError, "stale CAD sources"):
                record_fixture_visual_pass(module, project, second)
            source.write_bytes(original)
            result = record_fixture_visual_pass(module, project, second)
            self.assertTrue(result["ok"])
            with self.assertRaisesRegex(ValueError, "only accepted once"):
                record_fixture_visual_pass(module, project, second)
            self.assertEqual(self.summary(project, 1), first)

    def test_invalid_timeout_is_rejected_before_any_tools_or_round_state(self):
        for value in ("0", "-1", "nan", "inf", "-inf", "1e309", "1e30", "2147483.1", "invalid"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                module = load_module()
                with (
                    patch.object(module, "run") as runner,
                    redirect_stderr(io.StringIO()),
                    self.assertRaises(SystemExit) as raised,
                ):
                    module.main([temporary, "--render-timeout=" + value])
                self.assertEqual(raised.exception.code, 2)
                runner.assert_not_called()
                self.assertFalse((Path(temporary) / "measure").exists())

    def test_timeout_diagnostics_remain_text_and_report_exact_selected_seconds(self):
        for output, stderr, expected_out, expected_err in (
            (b"partial\n\xff", b"warning\n", "partial\n\ufffd", "warning\n"),
            ("partial\n", "warning\n", "partial\n", "warning\n"),
            (None, None, "", ""),
        ):
            with self.subTest(output=output), tempfile.TemporaryDirectory() as temporary:
                module = load_module()
                log = Path(temporary) / "render.log"
                error = subprocess.TimeoutExpired(["fixture"], 1234.5, output=output, stderr=stderr)
                with patch.object(module.subprocess, "run", side_effect=error):
                    result = module.run(["fixture"], cwd=temporary, log=log, timeout=1234.5)
                self.assertEqual(result.returncode, 124)
                self.assertEqual((result.stdout, result.stderr), (expected_out, expected_err))
                self.assertEqual(log.read_text(),
                                 "TIMEOUT after 1234.5s\n" + expected_out + "\n" + expected_err)


if __name__ == "__main__":
    unittest.main()
