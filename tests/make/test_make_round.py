"""The make-round skill: one Make iteration as one command."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
import tempfile
import contextlib
import io
from unittest import mock
from pathlib import Path

from workshop.runtime.package_data import product_run_domain_skill_roots

SCRIPT = product_run_domain_skill_roots()["make-round"] / "scripts" / "make_round"


def load_module():
    spec = importlib.util.spec_from_loader("make_round_script", loader=None)
    module = importlib.util.module_from_spec(spec)
    code = compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec")
    module.__file__ = str(SCRIPT)
    exec(code, module.__dict__)
    return module


def fake_visual_render(command):
    """Stand in for the renderer only; real packet and feedback validation run."""
    out = Path(command[command.index("-o") + 1])
    out.mkdir()
    for view in ("front", "top", "iso"):
        (out / (view + ".png")).write_bytes(("fixture " + view).encode())
    return subprocess.CompletedProcess(command, 0, "fixture views", "")


def record_fixture_visual_pass(module, project, summary):
    """Submit deterministic test feedback without overriding numeric results."""
    path = Path(summary["out"]) / "fixture-feedback.json"
    path.write_text(json.dumps({
        "packet_sha256": summary["visual"]["packet_sha256"],
        "status": "pass", "findings": [],
        "observation": "Synthetic fixture: visual evidence accepted for this test.",
    }))
    return module.record_visual(Path(project), path)


class MakeRoundTest(unittest.TestCase):
    def _round(self, project, *, render_fails=False, build_fails=False):
        module = load_module()
        (project / "toy.step.py").write_text("def gen_step(): pass\n")
        (project / "part_wheel.step.py").write_text("def gen_step(): pass\n")
        def fake_run(command, **kwargs):
            tool = Path(command[1]).name
            if tool == "gen" and not build_fails:
                Path(command[2]).with_name(Path(command[2]).name[:-3]).write_bytes(b"step")
            if tool == "render_review" and not render_fails:
                out = Path(command[command.index("-o") + 1])
                out.mkdir()
                for view in ("front", "top", "iso"):
                    (out / (view + ".png")).write_bytes(view.encode())
            failed = (render_fails and tool == "render_review") or (build_fails and tool == "gen")
            return subprocess.CompletedProcess(command, 1 if failed else 0,
                                               '{"ok":true}\n', "ValueError: wall must be positive\n" if failed else "")
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(module, "skills_root", return_value=project), mock.patch.object(module, "run", side_effect=fake_run):
            self.assertEqual(module.main([str(project)]), 1)
        summary = json.loads((project / "measure/rounds/r0001/summary.json").read_text())
        return module, summary

    def _feedback(self, project, summary, status="pass"):
        value = {"packet_sha256": summary["visual"]["packet_sha256"], "status": status,
                 "findings": [], "observation": "Inspected all views against the concept."}
        if status == "fail":
            value["findings"] = [{"part": "wheel", "defect": "misplaced axle",
                                  "evidence": "front: axle above wheel centre", "repair": "align centre datum"}]
        path = project / "measure/feedback.json"
        path.write_text(json.dumps(value))
        return path

    def test_no_reference_round_requires_visual_inspection_and_reports_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            self.assertTrue(summary["checks_ok"])
            self.assertFalse(summary["ok"])
            self.assertEqual(summary["visual"]["status"], "pending")
            packet = json.loads(Path(summary["visual"]["packet"]).read_text())
            self.assertEqual(len(packet["images"]), 3)
            self.assertEqual(packet["references"], {})
            result = module.record_visual(project, self._feedback(project, summary, "fail"))
            self.assertFalse(result["ok"])
            self.assertIn("wheel: misplaced axle", module.render_summary(result))
            self.assertIn("align centre datum", module.render_summary(result))
            with self.assertRaisesRegex(ValueError, "only accepted once"):
                module.record_visual(project, self._feedback(project, summary))

    def test_visual_pass_and_inconclusive_are_distinct(self):
        for status in ("pass", "inconclusive"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module, summary = self._round(project)
                result = module.record_visual(project, self._feedback(project, summary, status))
                self.assertEqual(result["ok"], status == "pass")

    def test_stale_or_contradictory_visual_feedback_cannot_pass(self):
        for change in ("source", "proof_helper", "imported_step", "image", "packet", "wrong_round", "contradiction"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module, summary = self._round(project)
                path = self._feedback(project, summary)
                packet_path = Path(summary["visual"]["packet"])
                packet = json.loads(packet_path.read_text())
                if change == "source":
                    (project / "toy.step.py").write_text("changed")
                elif change == "proof_helper":
                    helper = project / "review/early-proof/proof.py"
                    helper.parent.mkdir(parents=True)
                    helper.write_text("changed helper")
                elif change == "imported_step":
                    (project / "component.step").write_text("changed imported geometry")
                elif change == "image":
                    Path(next(iter(packet["images"]))).write_bytes(b"changed")
                elif change == "packet":
                    packet_path.write_text("{}")
                else:
                    feedback = json.loads(path.read_text())
                    if change == "wrong_round":
                        feedback["packet_sha256"] = "0" * 64
                    else:
                        feedback["status"] = "fail"
                    path.write_text(json.dumps(feedback))
                with self.assertRaises(ValueError):
                    module.record_visual(project, path)

    def test_render_failure_and_premature_full_do_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project, render_fails=True)
            self.assertEqual(summary["visual"]["status"], "error")
            self.assertFalse(summary["ok"])
            with mock.patch.object(module, "run") as runner:
                self.assertEqual(module.main([str(project), "--full"]), 2)
                runner.assert_not_called()

    def test_reference_change_invalidates_native_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            reference = project / "reference.png"
            reference.write_bytes(b"reference")
            # Bind a reference as prepare_visual does, then mutate it after review.
            packet_path = Path(summary["visual"]["packet"])
            packet = json.loads(packet_path.read_text())
            packet["references"] = {str(reference): module.file_hash(reference)}
            packet_path.write_text(json.dumps(packet))
            summary["visual"]["packet_sha256"] = module.file_hash(packet_path)
            (project / "measure/rounds/r0001/summary.json").write_text(json.dumps(summary))
            feedback = self._feedback(project, summary)
            reference.write_bytes(b"different subject")
            with self.assertRaisesRegex(ValueError, "stale images or references"):
                module.record_visual(project, feedback)

    def test_full_runs_only_after_clean_visual_feedback_and_retains_verifier_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            with mock.patch.object(module, "skills_root", return_value=project), mock.patch.object(
                module, "run", return_value=subprocess.CompletedProcess([], 2, "", "missing independent review")
            ) as runner:
                result = module.record_visual(project, self._feedback(project, summary), full=True)
            command = runner.call_args.args[0]
            self.assertNotIn("--fresh", command)
            self.assertIn(str(project / "measure/verification-pipeline.md"), command)
            self.assertFalse(result["ok"])
            self.assertEqual(result["full"]["returncode"], 2)

    def test_one_piece_entry_is_built_and_reported_as_the_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module = load_module()
            (project / "toy.step.py").write_text("def gen_step(): pass\n")
            calls = []

            def fake_run(command, **kwargs):
                tool = Path(command[1]).name
                calls.append(tool)
                if tool == "gen":
                    source = Path(command[2])
                    source.with_name(source.name[:-len(".py")]).write_bytes(b"step")
                if tool == "render_review":
                    out = Path(command[command.index("-o") + 1])
                    out.mkdir()
                    for view in ("front", "top", "iso"):
                        (out / (view + ".png")).write_bytes(view.encode())
                return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

            with contextlib.redirect_stdout(io.StringIO()), \
                    mock.patch.object(module, "skills_root", return_value=project), \
                    mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project)]), 1)
            summary = json.loads((project / "measure/rounds/r0001/summary.json").read_text())
            self.assertEqual(summary["parts"], ["toy"])
            self.assertEqual(summary["build"]["toy"]["verdict"], "PASS")
            self.assertEqual(calls, ["gen", "render_review"])

    def test_visual_pass_cannot_unlock_full_verification_after_numeric_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project, build_fails=True)
            self.assertFalse(summary["checks_ok"])
            feedback = self._feedback(project, summary)
            with mock.patch.object(module, "run") as runner:
                with self.assertRaisesRegex(ValueError, "clean round and visual pass"):
                    module.record_visual(project, feedback, full=True)
                runner.assert_not_called()
            result = module.record_visual(project, feedback)
            self.assertEqual(result["visual"]["status"], "pass")
            self.assertFalse(result["ok"])
            self.assertEqual(result["build"]["wheel"]["verdict"], "FAIL")

    def test_skill_is_registered_with_its_tool_card(self):
        root = product_run_domain_skill_roots()["make-round"]
        text = (root / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: make-round\n"))
        for tool in ("gen", "render_views.py", "check_motion", "verify_project"):
            self.assertIn(tool, text)
        self.assertIn("at most once per round", text)
        self.assertTrue(SCRIPT.is_file())
        self.assertTrue(SCRIPT.stat().st_mode & 0o100)

    def test_self_check_passes_under_the_workshop_python(self):
        done = subprocess.run(
            [sys.executable, str(SCRIPT), "--self-check"], capture_output=True, text=True, timeout=120
        )
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertIn("all fixtures pass", done.stdout)

    def test_pure_helpers_read_tool_output_and_diff_rounds(self):
        module = load_module()
        parsed = module.parse_build("", "ValueError: wall must be positive\n", 1)
        self.assertEqual(
            (parsed["verdict"], parsed["failures"][-1]),
            ("FAIL", "ValueError: wall must be positive"),
        )
        self.assertEqual(module.parse_build("", "", 0)["verdict"], "PASS")
        self.assertEqual(module.diff_parts({"a": "x"}, {"a": "x", "b": "y"}), ["b"])
        self.assertEqual(module.parse_refs(["hero=ref/hero.png"], []), [("hero", "ref/hero.png")])
        # render_views --json prints one pretty-printed object whose ``views`` carry the IoU.
        stdout = json.dumps(
            {"source": "/p/cad/duck.step.py", "views": [{"label": "hero", "iou": 0.9029, "ok": True, "az": -82.5, "el": -1.875}], "ok": True},
            indent=2,
        )
        self.assertEqual(module.parse_render_views(stdout, "hero")["iou"], 0.9029)
        self.assertIsNone(module.parse_render_views(stdout, "side"))
        self.assertIsNone(module.parse_render_views("no json here\n", "hero"))
        summary = {
            "round": 1, "project": "/p", "parts": ["a"], "changed": ["a"], "checked": ["a"],
            "build": {"a": {"verdict": "PASS", "failures": []}},
            "likeness": [], "min": 0.9, "motion": None, "full": None, "ok": True, "out": "/p/measure/rounds/r0001",
        }
        self.assertTrue(module.render_summary(summary).splitlines()[-1].startswith("  PASS"))

    def test_a_directory_without_an_entry_cannot_run(self):
        import tempfile

        with tempfile.TemporaryDirectory() as temporary:
            done = subprocess.run(
                [sys.executable, str(SCRIPT), temporary], capture_output=True, text=True, timeout=120
            )
        self.assertEqual(done.returncode, 2)
        self.assertIn("entry", done.stderr)


if __name__ == "__main__":
    unittest.main()
