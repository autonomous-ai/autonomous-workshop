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


def _install_gate_identity(project):
    """The tool bytes make_round hashes to decide whether a PASS may be reused.

    Without them the identity is unavailable, which correctly disables reuse --
    so a reuse test has to supply them rather than assume them.
    """
    scripts = project / "cad" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    for name in ("check_thickness", "check_overhang", "meshlib.py", "printlib.py"):
        (scripts / name).write_text("# fixture %s\n" % name, encoding="utf-8")
    # Exercise the real shared, standard-library discovery policy while the
    # expensive geometry and measurement tools remain deterministic fakes.
    (scripts / "printlib.py").write_bytes(
        (product_run_domain_skill_roots()["cad"] / "scripts/printlib.py").read_bytes()
    )


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
        argv=None,
        calls=None,
        part_source=None,
    ):
        module = load_module()
        (project / "toy.step.py").write_text("def gen_step(): pass\n")
        (project / "part_wheel.step.py").write_text(part_source or "def gen_step(): pass\n")
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

    def _reference_round(self, project):
        """A passing numeric fixture with real bound reference evidence."""
        (project / "ref").mkdir()
        reference = project / "ref/hero.png"
        reference.write_bytes(b"synthetic reference, never rendered by the dry-run verifier")
        (project / "toy_spec.md").write_text("# Synthetic dry-run specification\n")
        (project / "measure").mkdir()
        for name in ("check_spec.py", "check_landmarks.py"):
            (project / "measure" / name).write_text("raise SystemExit(0)\n")
        module, summary = self._round(project)
        packet_path = Path(summary["visual"]["packet"])
        packet = json.loads(packet_path.read_text())
        packet["references"] = {str(reference): module.file_hash(reference)}
        packet_path.write_text(json.dumps(packet))
        summary["visual"]["packet_sha256"] = module.file_hash(packet_path)
        summary["refs"] = [["hero", str(reference)]]
        (Path(summary["out"]) / "summary.json").write_text(json.dumps(summary))
        return module, summary

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

    def test_image_derived_full_requires_explicit_power_before_consuming_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._reference_round(project)
            feedback = self._feedback(project, summary)
            saved = Path(summary["out"]) / "summary.json"
            before = saved.read_bytes()
            with mock.patch.object(module, "run") as runner:
                with self.assertRaisesRegex(ValueError, "explicit --powered or --unpowered"):
                    module.record_visual(project, feedback, full=True)
                runner.assert_not_called()
            self.assertEqual(saved.read_bytes(), before)
            self.assertFalse((Path(summary["out"]) / "visual-feedback.json").exists())
            with mock.patch.object(module, "skills_root", return_value=project), mock.patch.object(
                module, "run", return_value=subprocess.CompletedProcess([], 0, "", "")
            ):
                result = module.record_visual(project, feedback, full=True, power_classification="unpowered")
            self.assertTrue(result["ok"])

    def test_power_flags_reject_nonfinal_conflicting_and_nonimage_unpowered_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            feedback = self._feedback(project, summary)
            saved = Path(summary["out"]) / "summary.json"
            before = saved.read_bytes()
            invalid = (["--powered"], ["--full", "--powered"],
                       ["--record-visual", str(feedback), "--unpowered"],
                       ["--record-visual", str(feedback), "--full", "--unpowered"])
            with mock.patch.object(module, "run") as runner, contextlib.redirect_stderr(io.StringIO()):
                for options in invalid:
                    with self.subTest(options=options):
                        self.assertEqual(module.main([str(project), *options]), 2)
                with self.assertRaises(SystemExit) as conflict:
                    module.main([str(project), "--record-visual", str(feedback), "--full",
                                 "--powered", "--unpowered"])
                self.assertEqual(conflict.exception.code, 2)
                runner.assert_not_called()
            self.assertEqual(saved.read_bytes(), before)
            self.assertFalse((Path(summary["out"]) / "visual-feedback.json").exists())

    def test_final_power_classification_reaches_real_verifier_dry_run_and_refusals(self):
        # The real verifier parses flags and checks manifest presence; --dry-run
        # plans its remaining gates without fabricating engineering evidence.
        cases = ((True, "unpowered", False, 0, ""),
                 (True, "powered", True, 0, ""),
                 (True, "powered", False, 1, "requires measure/power.json"),
                 (True, "unpowered", True, 1, "contradicts"),
                 (False, "powered", True, 0, ""))
        for image_derived, classification, manifest, expected_exit, diagnostic in cases:
            with self.subTest(image_derived=image_derived, classification=classification, manifest=manifest), \
                    tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module, summary = self._reference_round(project) if image_derived else self._round(project)
                if manifest:
                    (project / "measure/power.json").write_text("{}")
                feedback = self._feedback(project, summary)
                calls = []

                def dry_run(command, **kwargs):
                    calls.append(command)
                    return subprocess.run([*command, "--dry-run"], cwd=kwargs["cwd"],
                                          capture_output=True, text=True, timeout=30)

                with mock.patch.object(module, "run", side_effect=dry_run), \
                        contextlib.redirect_stdout(io.StringIO()):
                    code = module.main([str(project), "--record-visual", str(feedback),
                                        "--full", "--" + classification])
                self.assertEqual(code, expected_exit)
                self.assertEqual(len(calls), 1)
                command = calls[0]
                self.assertIn("--" + classification, command)
                self.assertEqual("--image-derived" in command, image_derived)
                self.assertIn("--strict-fit", command)
                self.assertIn("--print-gates", command)
                self.assertNotIn("--fresh", command)
                final = json.loads((Path(summary["out"]) / "summary.json").read_text())
                self.assertEqual(final["full"]["power_classification"], classification)
                self.assertEqual(final["ok"], expected_exit == 0)
                self.assertEqual(final["full"]["returncode"], 0 if expected_exit == 0 else 2)
                if diagnostic:
                    self.assertIn(diagnostic, final["full"]["tail"])
                # A dry-run fixture never emits a passing final engineering report.
                self.assertFalse((project / "measure/verification-pipeline.md").exists())

    def test_one_piece_entry_is_built_and_reported_as_the_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module = load_module()
            (project / "toy.step.py").write_text("def gen_step(): pass\n")
            _install_gate_identity(project)
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
                result = module.record_visual(project, self._feedback(project, summary), full=True)
            command = runner.call_args.args[0]
            self.assertIn("--print-gates", command)
            self.assertIn("--nozzle", command)
            self.assertNotIn("--skip-thickness", command)
            self.assertNotIn("--powered", command)
            self.assertNotIn("--unpowered", command)
            self.assertIsNone(result["full"]["power_classification"])

    def test_thin_nonprinted_card_builds_but_only_printed_body_is_print_gated(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "part_card.step.py").write_text(
                "PRINTABLE = False\nTHICKNESS_MM = 0.2\ndef gen_step(): pass\n"
            )
            calls = []
            module, summary = self._round(project, calls=calls)
            self.assertTrue(summary["checks_ok"])
            self.assertEqual(set(summary["build"]), {"card", "wheel"})
            self.assertEqual(summary["print_targets"], ["wheel"])
            self.assertEqual(summary["nonprinted"], ["card"])
            self.assertNotIn("card", summary["print"])
            self.assertIn("nonprinted component", module.render_summary(summary))
            built = [Path(command[2]).name for command in calls if Path(command[1]).name == "gen"]
            self.assertEqual(built, ["part_card.step.py", "part_wheel.step.py"])
            gated = [Path(command[2]).name for command in calls if Path(command[1]).name in ("check_thickness", "check_overhang")]
            self.assertEqual(gated, ["part_wheel.step.py", "part_wheel.step.py"])

    def test_no_printed_components_omit_final_print_gates_and_print_ready_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            calls = []
            module, summary = self._round(
                project, calls=calls,
                part_source="PRINTABLE = False\nTHICKNESS_MM = 0.2\ndef gen_step(): pass\n",
            )
            self.assertTrue(summary["checks_ok"])
            self.assertEqual(summary["print"], {})
            self.assertEqual(summary["print_targets"], [])
            self.assertEqual(summary["nonprinted"], ["wheel"])
            self.assertFalse(any(Path(command[1]).name.startswith("check_") for command in calls))
            with mock.patch.object(module, "skills_root", return_value=project), mock.patch.object(
                module, "run", return_value=subprocess.CompletedProcess([], 0, "", "")
            ) as runner:
                result = module.record_visual(project, self._feedback(project, summary), full=True)
            command = runner.call_args.args[0]
            self.assertNotIn("--print-gates", command)
            self.assertNotIn("--nozzle", command)
            self.assertTrue(result["ok"])
            self.assertFalse(result["full"]["print_gates_ran"])
            self.assertFalse(result["full"]["print_ready_claim"])

    def test_nonprinted_build_failure_still_blocks_round_without_fabricating_print_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(
                project, build_fails=True,
                part_source="PRINTABLE = False\ndef gen_step(): pass\n",
            )
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["build"]["wheel"]["verdict"], "FAIL")
            self.assertEqual(summary["print"], {})
            self.assertEqual(summary["nonprinted"], ["wheel"])

    def test_printable_flag_change_invalidates_scope_even_when_step_bytes_are_identical(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, first = self._round(project)
            self.assertEqual(first["print_targets"], ["wheel"])
            source = project / "part_wheel.step.py"
            source.write_text("PRINTABLE = False\ndef gen_step(): pass\n")
            calls = []
            self._round_again(module, project, calls, [])
            second = json.loads((project / "measure/rounds/r0002/summary.json").read_text())
            self.assertIn("wheel", second["changed"])
            self.assertEqual(second["print"], {})
            self.assertEqual(second["reused"], [])
            self.assertFalse(any(Path(command[1]).name.startswith("check_") for command in calls))
            source.write_text("PRINTABLE = True\ndef gen_step(): pass\n")
            calls.clear()
            self._round_again(module, project, calls, [])
            third = json.loads((project / "measure/rounds/r0003/summary.json").read_text())
            self.assertEqual(third["print_targets"], ["wheel"])
            self.assertEqual(third["reused"], [])
            self.assertEqual(third["print"]["wheel"]["measured_round"], 3)
            self.assertEqual(len([command for command in calls if Path(command[1]).name.startswith("check_")]), 2)

    def test_explicit_printable_combined_entry_uses_the_final_verifiers_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, _ = self._round(project)
            (project / "toy.step.py").write_text("PRINTABLE = True\ndef gen_step(): pass\n")
            calls = []
            self._round_again(module, project, calls, [])
            second = json.loads((project / "measure/rounds/r0002/summary.json").read_text())
            self.assertEqual(second["print_targets"], ["toy", "wheel"])
            self.assertIn("toy", second["build"])
            self.assertEqual(second["print"]["toy"]["verdict"], "PASS")

    def test_malformed_printable_declarations_fail_before_any_tool_runs(self):
        for declaration in ('PRINTABLE = "False"', "PRINTABLE = 0", "PRINTABLE = bool(0)", "PRINTABLE = ["):
            with self.subTest(declaration=declaration), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module = load_module()
                _install_gate_identity(project)
                (project / "toy.step.py").write_text("def gen_step(): pass\n")
                (project / "part_card.step.py").write_text(declaration + "\ndef gen_step(): pass\n")
                with mock.patch.object(module, "skills_root", return_value=project), mock.patch.object(module, "run") as runner, contextlib.redirect_stderr(io.StringIO()) as errors:
                    self.assertEqual(module.main([str(project)]), 2)
                    runner.assert_not_called()
                self.assertIn("print target discovery failed", errors.getvalue())

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
