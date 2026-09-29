"""The make-round skill: one Make iteration as one command."""

from __future__ import annotations

import hashlib
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


def png(tag: bytes) -> bytes:
    """A small, decodable reference image, distinct for each tag, so the
    comparison make_round composes beside the model can read it."""
    from PIL import Image

    digest = hashlib.sha256(tag).digest()
    image = Image.new("RGBA", (8, 12), (255, 255, 255, 0))
    image.paste((digest[0], digest[1], digest[2], 255), (2, 2, 6, 10))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


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
    feedback = {
        "packet_sha256": summary["visual"]["packet_sha256"],
        "status": "pass", "findings": [],
        # Each round is inspected afresh; a repeated observation is refused (ADR 0075).
        "observation": "Synthetic fixture: round %d visual evidence accepted for this test." % summary["round"],
    }
    path.write_text(json.dumps(feedback))
    return module.record_visual(Path(project), path)


def write_review(project, summary, **changes):
    """An independent reviewer's judgement of one component round."""
    review = {
        "round": summary["round"],
        "packet_sha256": summary["visual"].get("packet_sha256", "0" * 64),
        "reviewer": "fresh-reviewer-subagent",
        "agrees": True,
        "reason": "The model matches its reference in every view.",
        **changes,
    }
    path = Path(project) / "measure" / "review.json"
    path.write_text(json.dumps(review))
    return path


def fake_render_review(command):
    """Stand in for render_review: one decodable image per requested view,
    named as render_review names it."""
    out = Path(command[command.index("-o") + 1])
    out.mkdir(parents=True, exist_ok=True)
    views = [command[i + 1] for i, arg in enumerate(command) if arg == "--view"]
    views += [arg.split("=", 1)[1] for arg in command if arg.startswith("--view=")]
    for view in views:
        if view in ("front", "top", "iso"):
            stem = view
        else:
            az, el = (float(v) for v in view.split(","))
            stem = "az%g_el%g" % (az, el)
        (out / (stem + ".png")).write_bytes(png(b"model " + stem.encode()))
    return subprocess.CompletedProcess(command, 0, "fixture views", "")


def _install_gate_identity(project):
    """The tool bytes make_round hashes to decide whether a PASS may be reused.

    Without them the identity is unavailable, which correctly disables reuse --
    so a reuse test has to supply them rather than assume them.
    """
    scripts = project / "cad" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    for name in ("check_thickness", "check_overhang", "meshlib.py", "printlib.py"):
        (scripts / name).write_text("# fixture %s\n" % name, encoding="utf-8")


def _gate_output(tool, *, fails):
    """Stand in for one print gate, in the exact shape make_round parses."""
    if tool == "check_thickness":
        if fails:
            return (
                "part_wheel.step.py: 4.20 cm3 solid, grid 0.100 mm\n"
                "  FAIL  wall >= 0.80 mm (+/-0.10)        2.1% of surface below\n"
                "        1. [wall ] 0.42 mm at (1.0, 2.0, 3.0)  12 samples\n"
                "RESULT: WALL BELOW MINIMUM\n"
            ), 1
        return (
            "part_wheel.step.py: 4.20 cm3 solid, grid 0.100 mm\n"
            "  PASS  wall >= 0.80 mm (+/-0.10)        0.0% of surface below\n"
            "RESULT: printable at this wall\n"
        ), 0
    if fails:
        return (
            "part_wheel.step.py: 13.8 cm2 of surface\n"
            "  FAIL  unsupported area                  473.9 mm2\n"
            "        1. [overhang] 473.9 mm2 at (0.0, 0.0, 6.0)  span 20.0 mm\n"
            "RESULT: NEEDS SUPPORT\n"
        ), 1
    return (
        "part_wheel.step.py: 13.8 cm2 of surface\n"
        "RESULT: prints unsupported\n"
    ), 0


class MakeRoundTest(unittest.TestCase):
    def _round(
        self,
        project,
        *,
        render_fails=False,
        build_fails=False,
        wall_fails=False,
        overhang_fails=False,
        overhang_unverified=False,
        argv=None,
        calls=None,
    ):
        module = load_module()
        (project / "toy.step.py").write_text("def gen_step(): pass\n")
        (project / "part_wheel.step.py").write_text("def gen_step(): pass\n")
        _install_gate_identity(project)
        def fake_run(command, **kwargs):
            tool = Path(command[1]).name
            if calls is not None:
                calls.append(command)
            if tool == "gen" and not build_fails:
                Path(command[2]).with_name(Path(command[2]).name[:-3]).write_bytes(b"step")
            if tool == "render_review" and not render_fails:
                out = Path(command[command.index("-o") + 1])
                out.mkdir()
                for view in ("front", "top", "iso"):
                    (out / (view + ".png")).write_bytes(view.encode())
            if tool in ("check_thickness", "check_overhang"):
                stdout, code = _gate_output(
                    tool,
                    fails=wall_fails if tool == "check_thickness" else overhang_fails,
                )
                if tool == "check_overhang" and overhang_unverified:
                    stdout, code = "", 3
                log = kwargs.get("log")
                if log is not None:
                    Path(log).parent.mkdir(parents=True, exist_ok=True)
                    Path(log).write_text(stdout, encoding="utf-8")
                return subprocess.CompletedProcess(command, code, stdout, "")
            failed = (render_fails and tool == "render_review") or (build_fails and tool == "gen")
            return subprocess.CompletedProcess(command, 1 if failed else 0,
                                               '{"ok":true}\n', "ValueError: wall must be positive\n" if failed else "")
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(module, "skills_root", return_value=project), mock.patch.object(module, "run", side_effect=fake_run):
            self.assertEqual(module.main(argv or [str(project)]), 1)
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

    def test_unknown_geometry_can_finish_visual_review_without_becoming_a_print_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project, overhang_unverified=True)
            self.assertTrue(summary["checks_ok"])
            self.assertEqual(summary["print"]["wheel"]["verdict"], "UNVERIFIED")
            self.assertFalse(module.reusable_print(summary["print"]["wheel"]))
            result = module.record_visual(project, self._feedback(project, summary))
            self.assertTrue(result["ok"])
            self.assertEqual(result["geometry_status"], "unverified")
            self.assertIs(result["print_ready_claim"], False)
            self.assertTrue(module.render_summary(result).splitlines()[-1].startswith("  UNVERIFIED"))
        with tempfile.TemporaryDirectory() as tmp:
            _, summary = self._round(Path(tmp), wall_fails=True, overhang_unverified=True)
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["print"]["wheel"]["verdict"], "FAIL")

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

    def test_full_forwards_explicit_motion_option(self):
        for value in ("true", "false"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module, summary = self._round(project)
                feedback = self._feedback(project, summary)
                with mock.patch.object(module, "skills_root", return_value=project), \
                        mock.patch.object(module, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run, \
                        contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(module.main([str(project), "--record-visual", str(feedback),
                                                  "--full", "--check-motion", value]), 0)
                command = run.call_args.args[0]
                self.assertEqual(command[command.index("--check-motion") + 1], value)

    def test_full_uses_current_motion_policy_instead_of_previous_round_option(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            summary["check_motion"] = True
            (project / "measure/rounds/r0001/summary.json").write_text(json.dumps(summary))
            feedback = self._feedback(project, summary)
            with mock.patch.object(module, "skills_root", return_value=project), \
                    mock.patch.object(module, "run", return_value=subprocess.CompletedProcess([], 0, "", "")) as run, \
                    contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(module.main([str(project), "--record-visual", str(feedback), "--full"]), 0)
            command = run.call_args.args[0]
            self.assertEqual(command[command.index("--check-motion") + 1], "false")

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
                if tool in ("check_thickness", "check_overhang"):
                    stdout, code = _gate_output(tool, fails=False)
                    log = kwargs.get("log")
                    if log is not None:
                        Path(log).parent.mkdir(parents=True, exist_ok=True)
                        Path(log).write_text(stdout, encoding="utf-8")
                    return subprocess.CompletedProcess(command, code, stdout, "")
                return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

            with contextlib.redirect_stdout(io.StringIO()), \
                    mock.patch.object(module, "skills_root", return_value=project), \
                    mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project)]), 1)
            summary = json.loads((project / "measure/rounds/r0001/summary.json").read_text())
            self.assertEqual(summary["parts"], ["toy"])
            self.assertEqual(summary["build"]["toy"]["verdict"], "PASS")
            # The one-piece entry is its own print target.
            self.assertEqual(summary["print"]["toy"]["verdict"], "PASS")
            self.assertEqual(
                calls, ["gen", "check_thickness", "check_overhang", "render_review"]
            )

    def test_every_built_part_is_gated_from_source_and_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            calls = []
            module, summary = self._round(project, calls=calls)
            self.assertTrue(summary["checks_ok"])
            # A split project prints its parts; the combined entry is the
            # review subject, not a print target.
            self.assertEqual(sorted(summary["print"]), ["wheel"])
            for role in ("wheel",):
                gates = summary["print"][role]
                self.assertEqual(gates["verdict"], "PASS")
                self.assertEqual(gates["thickness"]["verdict"], "PASS")
                self.assertEqual(gates["overhang"]["verdict"], "PASS")
            # The gates read the generator entry, never an exported mesh.
            gated = [c for c in calls if Path(c[1]).name in ("check_thickness", "check_overhang")]
            self.assertEqual(len(gated), 2)
            for command in gated:
                self.assertTrue(command[2].endswith(".step.py"), command[2])
                self.assertNotIn("--skip-thickness", command)
            self.assertIn("--nozzle", [item for c in gated for item in c])
            self.assertIn("--angle", [item for c in gated for item in c])

    def test_a_failing_print_gate_fails_the_round(self):
        for label, kwargs in (
            ("wall", {"wall_fails": True}),
            ("overhang", {"overhang_fails": True}),
        ):
            with self.subTest(gate=label), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module, summary = self._round(project, **kwargs)
                self.assertFalse(summary["checks_ok"])
                self.assertEqual(summary["build"]["wheel"]["verdict"], "PASS")
                self.assertEqual(summary["print"]["wheel"]["verdict"], "FAIL")
                gate = "thickness" if label == "wall" else "overhang"
                self.assertEqual(summary["print"]["wheel"][gate]["verdict"], "FAIL")
                # A geometry defect the gate measured is never a build defect.
                feedback = self._feedback(project, summary)
                with mock.patch.object(module, "run") as runner:
                    with self.assertRaisesRegex(ValueError, "clean round and visual pass"):
                        module.record_visual(project, feedback, full=True)
                    runner.assert_not_called()

    def test_a_part_that_did_not_build_is_a_gate_failure_not_a_skip(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            calls = []
            module, summary = self._round(project, build_fails=True, calls=calls)
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["build"]["wheel"]["verdict"], "FAIL")
            self.assertEqual(summary["print"]["wheel"]["verdict"], "FAIL")
            self.assertEqual(
                summary["print"]["wheel"]["thickness"]["failures"], ["build failed"]
            )
            # There is no solid to measure, so no gate is spent on one.
            self.assertEqual(
                [c for c in calls if Path(c[1]).name.startswith("check_")], []
            )

    def test_unchanged_part_reuses_a_passing_pair_but_not_a_failed_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, first = self._round(project)
            self.assertEqual(first["reused"], [])
            state = json.loads((project / "measure" / module.STATE_NAME).read_text())
            self.assertEqual(sorted(state["print"]), ["wheel"])
            self.assertIsNotNone(state["print_context"])

            # A second round over identical bytes reuses both parts' evidence.
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
            second = json.loads((project / "measure/rounds/r0002/summary.json").read_text())
            self.assertEqual(sorted(second["reused"]), ["wheel"])
            self.assertEqual(
                [tool for tool in calls if tool.startswith("check_")], []
            )
            self.assertEqual(second["print"]["wheel"]["verdict"], "PASS")

            # Editing a recorded tool log invalidates the record it stands for.
            state_path = project / "measure" / module.STATE_NAME
            state = json.loads(state_path.read_text())
            log = next(iter(state["print"]["wheel"]["logs"]))
            Path(log).write_text("tampered\n", encoding="utf-8")
            state_path.write_text(json.dumps(state))
            calls.clear()
            with contextlib.redirect_stdout(io.StringIO()), \
                    mock.patch.object(module, "skills_root", return_value=project), \
                    mock.patch.object(module, "run", side_effect=fake_run):
                module.main([str(project)])
            self.assertIn("check_thickness", calls)

    def test_a_different_nozzle_is_a_different_measurement(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, _ = self._round(project)
            calls = []
            self._round_again(module, project, calls, ["--nozzle", "0.6"])
            # The recorded context names the nozzle, so a wider one re-measures.
            self.assertIn("check_thickness", [Path(c[1]).name for c in calls])
            gated = [c for c in calls if Path(c[1]).name == "check_thickness"]
            self.assertIn("0.6", gated[0])

    def _round_again(self, module, project, calls, extra):
        def fake_run(command, **kwargs):
            calls.append(command)
            tool = Path(command[1]).name
            if tool == "gen":
                source = Path(command[2])
                source.with_name(source.name[:-len(".py")]).write_bytes(b"step")
            if tool == "render_review":
                out = Path(command[command.index("-o") + 1])
                out.mkdir()
                for view in ("front", "top", "iso"):
                    (out / (view + ".png")).write_bytes(view.encode())
            if tool in ("check_thickness", "check_overhang"):
                stdout, code = _gate_output(tool, fails=False)
                log = kwargs.get("log")
                if log is not None:
                    Path(log).parent.mkdir(parents=True, exist_ok=True)
                    Path(log).write_text(stdout, encoding="utf-8")
                return subprocess.CompletedProcess(command, code, stdout, "")
            return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

        with contextlib.redirect_stdout(io.StringIO()), \
                mock.patch.object(module, "skills_root", return_value=project), \
                mock.patch.object(module, "run", side_effect=fake_run):
            module.main([str(project), *extra])

    def test_the_final_verifier_runs_the_print_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            with mock.patch.object(module, "skills_root", return_value=project), \
                    mock.patch.object(
                        module, "run",
                        return_value=subprocess.CompletedProcess([], 0, "", ""),
                    ) as runner:
                module.record_visual(project, self._feedback(project, summary), full=True)
            command = runner.call_args.args[0]
            self.assertIn("--print-gates", command)
            self.assertIn("--nozzle", command)
            self.assertNotIn("--skip-thickness", command)


    def test_component_rounds_are_isolated_and_gate_assembly_on_current_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module = load_module()
            (project / "toy.step.py").write_text("def gen_step(): return 'assembly'\n")
            (project / "part_body.step.py").write_text("def gen_step(): return 'body'\n")
            (project / "part_wheel.step.py").write_text("def gen_step(): return 'wheel'\n")
            (project / "toy_spec.md").write_text("hero=ref/whole.png\n")

            def fake_run(command, **kwargs):
                tool = Path(command[1]).name
                if tool == "gen":
                    source = Path(command[2])
                    source.with_name(source.name[:-len(".py")]).write_bytes(source.read_bytes())
                if tool == "render_review":
                    out = Path(command[command.index("-o") + 1])
                    out.mkdir()
                    for view in ("front", "top", "iso"):
                        (out / (view + ".png")).write_bytes(view.encode())
                if tool in ("check_thickness", "check_overhang"):
                    stdout, code = _gate_output(tool, fails=False)
                    log = kwargs.get("log")
                    if log is not None:
                        Path(log).parent.mkdir(parents=True, exist_ok=True)
                        Path(log).write_text(stdout, encoding="utf-8")
                    return subprocess.CompletedProcess(command, code, stdout, "")
                return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

            def run_component(name):
                with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(
                    module, "skills_root", return_value=project
                ), mock.patch.object(module, "run", side_effect=fake_run):
                    self.assertEqual(module.main([str(project), "--component", name]), 1)
                role = name[len("part_"):-len(".step.py")]
                summary_path = project / "measure/component-rounds" / role / "r0001/summary.json"
                summary = json.loads(summary_path.read_text())
                self.assertEqual(summary["scope"], "component:%s" % role)
                self.assertEqual(summary["refs"], [])
                review = write_review(project, summary)
                self.assertTrue(module.record_review(project, review, name)["ok"])

            run_component("part_body.step.py")
            with contextlib.redirect_stderr(io.StringIO()) as stderr, mock.patch.object(
                module, "skills_root", return_value=project
            ), mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project), "--require-component-passes"]), 1)
            self.assertIn("part_wheel.step.py has no isolated component round", stderr.getvalue())

            run_component("part_wheel.step.py")
            with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(
                module, "skills_root", return_value=project
            ), mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project), "--require-component-passes"]), 1)
            assembly = json.loads((project / "measure/rounds/r0001/summary.json").read_text())
            self.assertEqual(assembly["scope"], "assembly")
            self.assertEqual(assembly["visual"]["status"], "pending")

            (project / "part_wheel.step.py").write_text("def gen_step(): return 'changed wheel'\n")
            with contextlib.redirect_stderr(io.StringIO()) as stderr, mock.patch.object(
                module, "skills_root", return_value=project
            ), mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project), "--require-component-passes"]), 1)
            self.assertIn("part_wheel.step.py changed after its component pass", stderr.getvalue())

    def test_require_component_passes_compares_brep_identity_not_step_bytes(self):
        """ADR 0073: `gen`'s reported B-rep identity is what a carried pass is
        checked against, so an exporter-only difference in the STEP bytes it
        wrote does not refuse a Component whose shape did not move -- and a
        real identity change still does."""
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module = load_module()
            (project / "toy.step.py").write_text("def gen_step(): return 'assembly'\n")
            (project / "part_wheel.step.py").write_text("def gen_step(): return 'wheel-v1'\n")
            (project / "toy_spec.md").write_text("hero=ref/whole.png\n")

            identity = {"value": "brep-hash-1"}

            def fake_run(command, **kwargs):
                tool = Path(command[1]).name
                if tool == "gen":
                    source = Path(command[2])
                    source.with_name(source.name[:-len(".py")]).write_bytes(source.read_bytes())
                    return subprocess.CompletedProcess(
                        command, 0, json.dumps({"identitySha256": identity["value"]}) + "\n", ""
                    )
                if tool == "render_review":
                    out = Path(command[command.index("-o") + 1])
                    out.mkdir()
                    for view in ("front", "top", "iso"):
                        (out / (view + ".png")).write_bytes(view.encode())
                if tool in ("check_thickness", "check_overhang"):
                    stdout, code = _gate_output(tool, fails=False)
                    log = kwargs.get("log")
                    if log is not None:
                        Path(log).parent.mkdir(parents=True, exist_ok=True)
                        Path(log).write_text(stdout, encoding="utf-8")
                    return subprocess.CompletedProcess(command, code, stdout, "")
                return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

            with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(
                module, "skills_root", return_value=project
            ), mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project), "--component", "part_wheel.step.py"]), 1)
            summary = json.loads((project / "measure/component-rounds/wheel/r0001/summary.json").read_text())
            review = write_review(project, summary)
            self.assertTrue(module.record_review(project, review, "part_wheel.step.py")["ok"])

            # The generator's written bytes move (an exporter-style difference), but the
            # reported B-rep identity does not: the carried pass still qualifies.
            (project / "part_wheel.step.py").write_text("def gen_step(): return 'wheel-v1-reexported'\n")
            with contextlib.redirect_stderr(io.StringIO()) as stderr, mock.patch.object(
                module, "skills_root", return_value=project
            ), mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project), "--require-component-passes"]), 1)
            self.assertNotIn("part_wheel.step.py changed after its component pass", stderr.getvalue())

            # The B-rep identity itself moves: the carried pass is refused, exactly as a
            # STEP-byte change used to refuse it.
            identity["value"] = "brep-hash-2"
            with contextlib.redirect_stderr(io.StringIO()) as stderr, mock.patch.object(
                module, "skills_root", return_value=project
            ), mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project), "--require-component-passes"]), 1)
            self.assertIn("part_wheel.step.py changed after its component pass", stderr.getvalue())

    def test_parse_identity_reads_the_brep_hash_gen_reports(self):
        module = load_module()
        stdout = "human progress line\n" + json.dumps({"identitySha256": "abc123", "outcome": "built"}) + "\n"
        self.assertEqual(module.parse_identity(stdout), "abc123")

    def test_parse_identity_is_none_without_a_reported_identity(self):
        module = load_module()
        self.assertIsNone(module.parse_identity(""))
        self.assertIsNone(module.parse_identity('{"outcome": "built"}\n'))
        self.assertIsNone(module.parse_identity("not json at all"))

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
        for tool in ("gen", "render_review", "check_motion", "verify_project", "--record-review"):
            self.assertIn(tool, text)
        self.assertIn("at most once per round", text)
        self.assertIn("--component", text)
        self.assertIn("--require-component-passes", text)
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
        self.assertFalse(hasattr(module, "parse_render_views"))
        summary = {
            "round": 1, "project": "/p", "parts": ["a"], "changed": ["a"], "checked": ["a"],
            "build": {"a": {"verdict": "PASS", "failures": []}},
            "reference_errors": [], "motion": None, "full": None, "ok": True, "out": "/p/measure/rounds/r0001",
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


class SealedReferenceTest(unittest.TestCase):
    """ADR 0072: a Wish's sealed references are shown whether or not a ledger names them.
    ADR 0076: nothing is scored; each is composed beside the model at its camera."""

    def _run_root(self, tmp, references, *, missing=(), context=None):
        """A run workspace as the host lays it out, with the CAD project nested inside."""
        run = Path(tmp)
        (run / "wish-references").mkdir()
        sealed = []
        for name, content in references.items():
            content = png(content)
            if name not in missing:
                (run / "wish-references" / name).write_bytes(content)
            sealed.append({"name": name, "sha256": hashlib.sha256(content).hexdigest()})
        wish = {"references": sealed}
        if context is not None:
            wish["context"] = context
        (run / "WISH.json").write_text(json.dumps(wish))
        project = run / "artifacts/make/r0001/product/cad"
        project.mkdir(parents=True)
        (project / "toy.step.py").write_text("def gen_step(): return 'assembly'\n")
        (project / "part_body.step.py").write_text("def gen_step(): return 'body'\n")
        _install_gate_identity(project)
        return project

    def _fake_run(self, calls, faults=None):
        """Stand in for every tool; ``faults`` can fail the build or a wall."""
        faults = faults if faults is not None else {}

        def fake_run(command, **kwargs):
            tool = Path(command[1]).name
            calls.append(command)
            if tool == "gen":
                if faults.get("build"):
                    return subprocess.CompletedProcess(command, 1, "", "ValueError: broken\n")
                source = Path(command[2])
                source.with_name(source.name[:-len(".py")]).write_bytes(source.read_bytes())
            if tool == "render_review":
                return fake_render_review(command)
            if tool in ("check_thickness", "check_overhang"):
                stdout, code = _gate_output(tool, fails=bool(faults.get("wall")) and tool == "check_thickness")
                log = kwargs.get("log")
                if log is not None:
                    Path(log).parent.mkdir(parents=True, exist_ok=True)
                    Path(log).write_text(stdout, encoding="utf-8")
                return subprocess.CompletedProcess(command, code, stdout, "")
            return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

        return fake_run

    def _main(self, module, project, argv, calls, faults=None):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as stderr, mock.patch.object(
            module, "skills_root", return_value=project
        ), mock.patch.object(module, "run", side_effect=self._fake_run(calls, faults)):
            code = module.main([str(project), *argv])
        self.stderr = stderr.getvalue()
        return code

    def _assembly(self, project):
        state = json.loads((project / "measure/make-round-state.json").read_text())
        return json.loads((Path(state["last_out"]) / "summary.json").read_text())

    def _shown(self, summary):
        return [label for label, _ in summary["refs"]]

    def test_sealed_references_are_shown_at_assembly_without_any_ledger(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertEqual(self._shown(summary), ["ref-01-whole"])
            self.assertTrue(summary["checks_ok"])
            self.assertEqual(summary["sealed"], [{"label": "ref-01-whole", "scored_by": "assembly"}])
            self.assertNotIn("likeness", summary)
            self.assertFalse(any(Path(c[1]).name in ("render_views.py", "check_likeness.py") for c in calls))
            packet = json.loads(Path(summary["visual"]["packet"]).read_text())
            self.assertEqual([item["label"] for item in packet["comparisons"].values()], ["ref-01-whole"])
            for path, item in packet["comparisons"].items():
                self.assertEqual(module.file_hash(path), item["sha256"])

    def test_the_model_is_rendered_at_the_declared_camera_else_from_the_front(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            (project / "ref").mkdir()
            (project / "ref/hero.png").write_bytes(png(b"whole"))
            (project / "ref/side.png").write_bytes(png(b"side"))
            module, calls = load_module(), []
            self._main(module, project, ["--ref", "hero=ref/hero.png@-60,20,15", "--ref", "side=ref/side.png"], calls)
            summary = self._assembly(project)
            render = next(c for c in calls if Path(c[1]).name == "render_review")
            self.assertIn("--view=-60,20", render)
            self.assertEqual(render.count("front"), 1)
            self.assertEqual(self._shown(summary), ["ref-01-whole", "side"])
            images = sorted(Path(p).name for p in json.loads(Path(summary["visual"]["packet"]).read_text())["comparisons"])
            self.assertEqual(images, ["compare-00.png", "compare-01.png"])
            self.assertTrue((Path(summary["out"]) / "visual/az-60_el20.png").is_file())

    def test_contract_mode_labels_a_sealed_reference_by_its_contract_shows_field(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = {
                "design_contract": {
                    "title": "Antisol",
                    "references": [{"file": "ref-01-whole.png", "shows": "geometry:world-disc"}],
                }
            }
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"}, context=context)
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            # ADR 0074: a Component's image is never judged against the whole object.
            self.assertEqual(self._shown(summary), [])
            self.assertFalse(summary["checks_ok"])
            self.assertEqual([i["label"] for i in summary["reference_errors"]], ["geometry:world-disc"])
            self.assertIn("--component part_world-disc.step.py", summary["reference_errors"][0]["error"])
            self.assertEqual(summary["sealed"], [{"label": "geometry:world-disc", "scored_by": "missing"}])

    def test_a_missing_sealed_reference_refuses_rather_than_dropping_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"}, missing={"ref-01-whole.png"})
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertFalse(summary["checks_ok"])
            self.assertIn("sealed reference missing", summary["reference_errors"][0]["error"])

    def test_a_sealed_reference_whose_bytes_changed_refuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            (project.parents[4] / "wish-references/ref-01-whole.png").write_bytes(b"swapped")
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertFalse(summary["checks_ok"])
            self.assertIn("does not match its sealed hash", summary["reference_errors"][0]["error"])
            self.assertEqual(self._shown(summary), [])

    def test_an_unreadable_wish_refuses_rather_than_showing_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            (project.parents[4] / "WISH.json").write_text("{not json")
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertFalse(summary["checks_ok"])
            self.assertIn("WISH.json", summary["reference_errors"][0]["error"])

    def test_a_ledger_reference_that_does_not_exist_fails_the_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            module, calls = load_module(), []
            self._main(module, project, ["--ref", "hero=ref/nowhere.png"], calls)
            summary = self._assembly(project)
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["reference_errors"], [{"label": "hero", "error": "reference missing: ref/nowhere.png"}])

    def test_a_ledger_copy_of_a_sealed_reference_is_shown_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            (project / "ref").mkdir()
            (project / "ref/hero.png").write_bytes(png(b"whole"))
            (project / "toy_spec.md").write_text("- `hero=ref/hero.png`\n")
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            self.assertEqual(self._shown(self._assembly(project)), ["ref-01-whole"])

    def test_an_agent_found_ledger_reference_is_still_shown(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            (project / "ref").mkdir()
            (project / "ref/found.png").write_bytes(png(b"found by the agent"))
            (project / "toy_spec.md").write_text("| found | `ref/found.png` | 0.90 | side view |\n")
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            self.assertEqual(sorted(self._shown(self._assembly(project))), ["found", "ref-01-whole"])

    def test_a_component_round_never_shows_sealed_references_implicitly(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            module, calls = load_module(), []
            self._main(module, project, ["--component", "part_body.step.py"], calls)
            summary = json.loads((project / "measure/component-rounds/body/r0001/summary.json").read_text())
            self.assertEqual(summary["refs"], [])

    def _pass_component(self, module, project, calls):
        argv = ["--component", "part_body.step.py", "--ref", "body=wish-references/ref-01-body.png"]
        self._main(module, project, argv, calls)
        summary = json.loads((project / "measure/component-rounds/body/r0001/summary.json").read_text())
        return module.record_review(project, write_review(project, summary), "part_body.step.py")

    def test_a_passing_component_round_covers_the_sealed_reference_it_showed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-body.png": b"body", "ref-02-whole.png": b"whole"})
            module, calls = load_module(), []
            self.assertTrue(self._pass_component(module, project, calls)["ok"])
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertEqual(self._shown(summary), ["ref-02-whole"])
            self.assertTrue(summary["checks_ok"])
            self.assertEqual(summary["sealed"], [
                {"label": "ref-01-body", "scored_by": "component:body"},
                {"label": "ref-02-whole", "scored_by": "assembly"},
            ])

    def test_a_component_changed_after_its_pass_no_longer_covers_its_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-body.png": b"body"})
            module, calls = load_module(), []
            self.assertTrue(self._pass_component(module, project, calls)["ok"])
            (project / "part_body.step.py").write_text("def gen_step(): return 'moved body'\n")
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertEqual(self._shown(summary), ["ref-01-body"])
            self.assertEqual(summary["sealed"], [{"label": "ref-01-body", "scored_by": "assembly"}])

    def test_current_passing_component_round_names_why_a_component_does_not_qualify(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            lookup = module.current_passing_component_round
            self.assertEqual(lookup(project, "body", "d1"), (None, "part_body.step.py has no isolated component round"))
            root = project / "measure/component-rounds/body"
            root.mkdir(parents=True)
            state_path = root / module.STATE_NAME
            for state in ([], {"round": 0, "scope": "component:body"}, {"round": 1, "scope": "component:wheel"}):
                state_path.write_text(json.dumps(state))
                self.assertEqual(lookup(project, "body", "d1"), (None, "part_body.step.py has invalid component state"))
            state_path.write_text(json.dumps({"round": 1, "scope": "component:body", "parts": {"body": "d1"}}))
            self.assertEqual(lookup(project, "body", "d1"), (None, "part_body.step.py has no component summary"))
            (root / "r0001").mkdir()
            summary_path = root / "r0001/summary.json"
            summary = {"scope": "component:body", "entry": "part_body.step.py", "parts": ["body"], "ok": True}
            for invalid in ([], {**summary, "entry": "part_wheel.step.py"}, {**summary, "parts": ["body", "wheel"]}):
                summary_path.write_text(json.dumps(invalid))
                self.assertEqual(lookup(project, "body", "d1"), (None, "part_body.step.py has invalid component summary"))
            summary_path.write_text(json.dumps({**summary, "ok": False}))
            self.assertEqual(lookup(project, "body", "d1"), (None, "part_body.step.py latest component round did not pass"))
            summary_path.write_text(json.dumps(summary))
            self.assertEqual(lookup(project, "body", "d2"), (None, "part_body.step.py changed after its component pass"))
            self.assertEqual(lookup(project, "body", "d1"), (summary, ""))

    def test_a_project_outside_any_run_keeps_its_ledger_behaviour(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "toy.step.py").write_text("def gen_step(): return 'assembly'\n")
            _install_gate_identity(project)
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertEqual(summary["refs"], [])
            self.assertEqual(summary["sealed"], [])
            self.assertTrue(summary["checks_ok"])

    def test_the_template_table_row_is_a_ledger_entry(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "toy_spec.md"
            spec.write_text(
                "| Label | Project-local reference | Minimum IoU | Why this viewpoint is usable |\n"
                "|---|---|---:|---|\n"
                "| <> | `ref/<file>` | 0.90 | <> |\n"
                "| hero | `ref/hero.png` | 0.90 | the front reads the silhouette |\n"
                "- `side=ref/side.png`\n"
            )
            refs = module.parse_refs([], [spec])
        self.assertEqual([label for label, _ in refs], ["hero", "side"])
        self.assertTrue(refs[0][1].endswith("ref/hero.png"))

    def test_an_observation_copied_from_the_previous_assembly_round_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            module, calls = load_module(), []
            copied = "Pauldron, piston upper arm, tapered blade forearm and three curved claws all read."

            def inspect(observation):
                summary = self._assembly(project)
                path = project / "measure/feedback.json"
                path.write_text(json.dumps({"packet_sha256": summary["visual"]["packet_sha256"],
                                            "status": "pass", "findings": [], "observation": observation}))
                return module.record_visual(project, path)

            self._main(module, project, [], calls)
            inspect(copied)
            self._main(module, project, [], calls)
            with self.assertRaisesRegex(ValueError, "repeats the previous round's observation"):
                inspect("Manager record: images unchanged, previously passed: " + copied)
            self.assertTrue(inspect("Re-inspected: the forearm plates and claws are unchanged.")["ok"])

    def test_assembly_differences_are_named_and_one_to_repair_cannot_pass(self):
        kept = {"feature": "claw length", "reference": "claws reach 37 mm", "model": "claws stop at 18 mm",
                "decision": "keep", "reason": "the Design Contract fixes 18 mm claws (R23)"}
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            path = project / "measure/feedback.json"

            def submit(differences):
                path.write_text(json.dumps({"packet_sha256": summary["visual"]["packet_sha256"], "status": "pass",
                                            "findings": [], "observation": "Inspected.", "differences": differences}))
                return module.record_visual(project, path)

            with self.assertRaisesRegex(ValueError, "still to repair cannot pass"):
                submit([{**kept, "decision": "repair"}])
            with self.assertRaisesRegex(ValueError, "repaired or kept"):
                submit([{**kept, "decision": "maybe"}])
            with self.assertRaisesRegex(ValueError, "feature, reference, model, decision and reason"):
                submit([{"feature": "claws"}])
            self.assertIn("differs claw length", module.render_summary(submit([kept])))


class ContractComponentReviewTest(unittest.TestCase):
    """ADR 0076: a Component passes on build, print and an independent
    reviewer's agreement, or on a recorded acceptance at the shape-repair limit."""

    _run_root = SealedReferenceTest._run_root
    _fake_run = SealedReferenceTest._fake_run
    _main = SealedReferenceTest._main
    _assembly = SealedReferenceTest._assembly
    _shown = SealedReferenceTest._shown

    CONTRACT = {
        "design_contract": {
            "title": "Broken God",
            "references": [
                {"file": "ref-01-whole.png", "shows": "assembly"},
                {"file": "ref-02-body.png", "shows": "geometry:body"},
            ],
        }
    }
    REFS = {"ref-01-whole.png": b"whole", "ref-02-body.png": b"body"}
    DIFFERS = [{"feature": "arm", "reference": "arm as thick as the leg", "model": "arm half as thick"}]

    def _contract_root(self, tmp):
        return self._run_root(tmp, self.REFS, context=self.CONTRACT)

    def _component(self, module, project, calls, extra=(), edit=True, faults=None):
        """One component round; ``edit`` changes the geometry first, as a repair does."""
        if edit:
            self._edits = getattr(self, "_edits", 0) + 1
            (project / "part_body.step.py").write_text("def gen_step(): return 'body %d'\n" % self._edits)
        code = self._main(module, project, ["--component", "part_body.step.py", *extra], calls, faults)
        state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
        summary = json.loads(
            (project / ("measure/component-rounds/body/r%04d/summary.json" % state["round"])).read_text()
        )
        return code, summary

    def _review(self, module, project, summary, **changes):
        return module.record_review(project, write_review(project, summary, **changes), "part_body.step.py")

    def _disagree(self, module, project, summary):
        return self._review(module, project, summary, agrees=False, reason="The arm is too thin.",
                            differences=self.DIFFERS)

    def _five_shape_rounds(self, module, project, calls):
        """A first round, then five that each change a checked geometry after a disagreeing review."""
        _, summary = self._component(module, project, calls)
        for expected in range(1, 6):
            self._disagree(module, project, summary)
            _, summary = self._component(module, project, calls)
            self.assertEqual(summary["shape_rounds"], expected)
        return summary

    def test_a_component_round_shows_its_sealed_image_without_any_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self.assertEqual(self._shown(summary), ["geometry:body"])
            self.assertTrue(summary["checks_ok"])
            self.assertFalse(summary["ok"])
            self.assertEqual((summary["review"], summary["shape_rounds"], summary["shape_limit"]), (None, 0, 5))
            self.assertEqual(summary["sealed"], [{"label": "geometry:body", "scored_by": "component:body"}])
            packet = json.loads(Path(summary["visual"]["packet"]).read_text())
            self.assertEqual([Path(p).name for p in packet["references"]], ["ref-02-body.png"])
            self.assertEqual([item["label"] for item in packet["comparisons"].values()], ["geometry:body"])
            self.assertIn("--record-review", summary["visual"]["detail"])
            self.assertIn("--record-review", module.render_summary(summary))

    def test_an_explicit_ref_to_the_same_image_is_shown_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls, ["--ref", "body=wish-references/ref-02-body.png@30,10"])
            self.assertEqual(self._shown(summary), ["geometry:body"])
            self.assertTrue(summary["refs"][0][1].endswith("ref-02-body.png@30,10"))

    def test_the_assembly_never_shows_a_component_image_against_the_whole_object(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertEqual(self._shown(summary), ["assembly"])
            self.assertFalse(summary["checks_ok"])
            self.assertIn("--component part_body.step.py", summary["reference_errors"][0]["error"])
            self.assertIn({"label": "geometry:body", "scored_by": "missing"}, summary["sealed"])

    def test_an_agreeing_review_passes_the_component_and_covers_its_image(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            result = self._review(module, project, summary)
            self.assertTrue(result["ok"])
            self.assertEqual(result["review"], {
                "reviewer": "fresh-reviewer-subagent", "agrees": True,
                "reason": "The model matches its reference in every view.", "round": 1, "differences": [],
            })
            self.assertNotIn("accepted", result)
            digests = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())["parts"]
            coverage = module.component_coverage(project, digests)
            self.assertEqual(list(coverage.values()), [{"role": "body", "accepted": None}])
            self._main(module, project, [], calls)
            assembly = self._assembly(project)
            self.assertTrue(assembly["checks_ok"])
            self.assertEqual(assembly["sealed"], [
                {"label": "assembly", "scored_by": "assembly"},
                {"label": "geometry:body", "scored_by": "component:body"},
            ])

    def test_a_component_round_takes_no_manager_visual(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            feedback = project / "measure/feedback.json"
            feedback.write_text(json.dumps({"packet_sha256": summary["visual"]["packet_sha256"], "status": "pass",
                                            "findings": [], "observation": "Looks right."}))
            with self.assertRaisesRegex(ValueError, "--record-review"):
                module.record_visual(project, feedback, component="part_body.step.py")

    def test_a_review_that_cannot_be_trusted_is_refused(self):
        cases = {
            "manager": ({"reviewer": "Workshop-Manager"}, "cannot review its own component"),
            "old round": ({"round": 7}, "must judge the latest round"),
            "other packet": ({"packet_sha256": "0" * 64}, "different visual packet"),
            "not boolean": ({"agrees": "yes"}, "true or false"),
            "empty reason": ({"reason": "  "}, "reason of 1 to"),
            "no differences": ({"agrees": False}, "must list how the model differs"),
            "bad difference": ({"agrees": False, "differences": [{"feature": "arm"}]}, "feature, reference and model"),
            "extra field": ({"score": 0.9}, "needs round, packet_sha256"),
        }
        for name, (changes, refusal) in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                project = self._contract_root(tmp)
                module, calls = load_module(), []
                _, summary = self._component(module, project, calls)
                with self.assertRaisesRegex(ValueError, refusal):
                    self._review(module, project, summary, **changes)

    def test_a_review_of_changed_evidence_or_failed_checks_is_refused(self):
        for change in ("source", "comparison", "packet", "checks", "twice"):
            with self.subTest(change), tempfile.TemporaryDirectory() as tmp:
                project = self._contract_root(tmp)
                module, calls = load_module(), []
                _, summary = self._component(module, project, calls, faults={"wall": change == "checks"})
                packet_path = Path(summary["visual"]["packet"])
                packet = json.loads(packet_path.read_text())
                refusal = {"source": "stale CAD sources", "comparison": "stale images or references",
                           "packet": "visual packet changed", "checks": "did not pass its build and print checks",
                           "twice": "already has a recorded review"}[change]
                if change == "source":
                    (project / "part_body.step.py").write_text("def gen_step(): return 'edited after'\n")
                elif change == "comparison":
                    Path(next(iter(packet["comparisons"]))).write_bytes(b"changed")
                elif change == "packet":
                    packet_path.write_text("{}")
                elif change == "twice":
                    self._review(module, project, summary)
                with self.assertRaisesRegex(ValueError, refusal):
                    self._review(module, project, summary)

    def test_record_review_through_the_command_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            review = write_review(project, summary)
            self.assertEqual(self._main(module, project, ["--component", "part_body.step.py", "--record-review", str(review)], calls), 0)
            self.assertEqual(self._main(module, project, ["--component", "part_body.step.py", "--record-review", str(review)], calls), 2)
            self.assertIn("already has a recorded review", self.stderr)

    def test_a_disagreeing_review_before_the_limit_is_the_repair_list(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            result = self._disagree(module, project, summary)
            self.assertFalse(result["ok"])
            self.assertNotIn("accepted", result)
            self.assertIn("differs arm", module.render_summary(result))
            self.assertEqual(module.current_passing_component_round(project, "body", None)[1],
                             "part_body.step.py latest component round did not pass")

    def test_only_rounds_that_change_checked_geometry_count_as_shape_rounds(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls, faults={"wall": True})
            self.assertEqual(summary["shape_rounds"], 0)
            # repairing a print failure is not a shape round
            _, summary = self._component(module, project, calls)
            self.assertEqual(summary["shape_rounds"], 0)
            # a rerun that changes no geometry is not one either
            _, summary = self._component(module, project, calls, edit=False)
            self.assertEqual(summary["shape_rounds"], 0)
            # a build that fails produced no new shape
            _, summary = self._component(module, project, calls, faults={"build": True})
            self.assertEqual(summary["shape_rounds"], 0)
            _, summary = self._component(module, project, calls)
            self.assertEqual(summary["shape_rounds"], 0)
            _, summary = self._component(module, project, calls)
            self.assertEqual(summary["shape_rounds"], 1)

    def test_at_the_limit_a_disagreeing_review_becomes_a_recorded_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            summary = self._five_shape_rounds(module, project, calls)
            # the Manager may not start a sixth shape repair before the review
            before = len(calls)
            code = self._main(module, project, ["--component", "part_body.step.py"], calls)
            self.assertEqual(code, 2)
            self.assertIn("record it with --record-review", self.stderr)
            self.assertEqual(len(calls), before)
            result = self._disagree(module, project, summary)
            self.assertTrue(result["ok"])
            self.assertEqual(result["accepted"], {"reviewer": "fresh-reviewer-subagent",
                                                  "reason": "The arm is too thin.", "shape_rounds": 5})
            self.assertIn("ACCEPTED at the shape-repair limit", module.render_summary(result))
            digests = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())["parts"]
            self.assertEqual(list(module.component_coverage(project, digests).values()), [{
                "role": "body",
                "accepted": {"reviewer": "fresh-reviewer-subagent", "reason": "The arm is too thin.", "shape_rounds": 5},
            }])
            self._main(module, project, [], calls)
            self.assertTrue(self._assembly(project)["checks_ok"])

    def test_at_the_limit_an_agreeing_review_is_a_plain_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            summary = self._five_shape_rounds(module, project, calls)
            result = self._review(module, project, summary)
            self.assertTrue(result["ok"])
            self.assertNotIn("accepted", result)

    def test_after_a_recorded_review_at_the_limit_another_round_may_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            summary = self._five_shape_rounds(module, project, calls)
            self._disagree(module, project, summary)
            code, summary = self._component(module, project, calls)
            self.assertEqual(code, 1)
            self.assertEqual(summary["shape_rounds"], 6)
            self.assertIsNone(summary["review"])

    def test_a_scored_reference_without_a_model_render_leaves_no_visual_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            fake = self._fake_run(calls)

            def without_camera(command, **kwargs):
                done = fake(command, **kwargs)
                if Path(command[1]).name == "render_review":
                    (Path(command[command.index("-o") + 1]) / "front.png").write_bytes(b"not an image")
                return done

            with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(
                module, "skills_root", return_value=project
            ), mock.patch.object(module, "run", side_effect=without_camera):
                module.main([str(project), "--component", "part_body.step.py"])
            summary = json.loads((project / "measure/component-rounds/body/r0001/summary.json").read_text())
            self.assertEqual(summary["visual"]["status"], "error")
            self.assertIn("could not compose the comparison", summary["visual"]["detail"])
            with self.assertRaisesRegex(ValueError, "no visual packet"):
                self._review(module, project, summary)

    def test_the_removed_likeness_options_are_gone_and_review_needs_a_component(self):
        module = load_module()
        with contextlib.redirect_stderr(io.StringIO()):
            for argv in (["/tmp", "--min", "0.9"], ["/tmp", "--accept-likeness", "reason"],
                         ["/tmp", "--acceptance-review", "review.json"], ["/tmp", "--record-review", "review.json"],
                         ["/tmp", "--component", "part_body.step.py", "--record-visual", "f.json"],
                         ["/tmp", "--component", "part_body.step.py", "--record-review", "r.json", "--full"]):
                with self.subTest(argv=argv), self.assertRaises(SystemExit):
                    module.main(argv)

    def test_a_component_identity_matches_its_recorded_step_bytes_too(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            with mock.patch.object(module, "parse_identity", return_value="b" * 64):
                _, summary = self._component(module, project, calls)
            self._review(module, project, summary)
            self.assertEqual(module.current_passing_component_round(project, "body", "b" * 64)[1], "")
            step = hashlib.sha256((project / "part_body.step").read_bytes()).hexdigest()
            _found, reason = module.current_passing_component_round(project, "body", step)
            self.assertEqual(reason, "")
            self.assertEqual(module.current_passing_component_round(project, "body", "0" * 64)[1],
                             "part_body.step.py changed after its component pass")

    def test_outside_contract_mode_a_component_still_shows_only_what_it_is_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-body.png": b"body"})
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self.assertEqual(summary["refs"], [])


if __name__ == "__main__":
    unittest.main()
