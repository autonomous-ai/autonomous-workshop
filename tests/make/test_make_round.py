"""The make-round skill: one Make iteration as one command."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
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
def rendered_views(command):
    """The images a real render_review writes for this command line."""
    views = [command[i + 1] for i, arg in enumerate(command) if arg == "--view"]
    return views + (["sheet"] if "--sheet" in command else [])


def fake_visual_render(command):
    """Stand in for the renderer only; real packet and feedback validation run."""
    out = Path(command[command.index("-o") + 1])
    out.mkdir()
    for view in rendered_views(command):
        (out / (view + ".png")).write_bytes(("fixture " + view).encode())
    return subprocess.CompletedProcess(command, 0, "fixture views", "")


def fixture_verdicts(summary):
    """Plan and reference verdicts that agree with the round's own packet."""
    packet = json.loads(Path(summary["visual"]["packet"]).read_text())
    return {"matches_plan": True, "matches_reference": True if packet["comparisons"] else None}


def record_fixture_visual_pass(module, project, summary):
    """Submit deterministic test feedback without overriding numeric results."""
    path = Path(summary["out"]) / "fixture-feedback.json"
    feedback = {
        "packet_sha256": summary["visual"]["packet_sha256"],
        "status": "pass", "findings": [],
        # Each round is inspected afresh; a repeated observation is refused (ADR 0075).
        "observation": "Synthetic fixture: round %d visual evidence accepted for this test." % summary["round"],
        **fixture_verdicts(summary),
    }
    path.write_text(json.dumps(feedback))
    return module.record_visual(Path(project), path)


def write_review(project, summary, **changes):
    """An independent reviewer's judgement of one component round."""
    packet = summary["visual"].get("packet")
    shown = bool(json.loads(Path(packet).read_text()).get("comparisons")) if packet else False
    review = {
        "round": summary["round"],
        "packet_sha256": summary["visual"].get("packet_sha256", "0" * 64),
        "reviewer": "fresh-reviewer-subagent",
        "agrees": True,
        "matches_plan": True,
        "matches_reference": True if shown else None,
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
        if "," not in view:
            stem = view
        else:
            az, el = (float(v) for v in view.split(","))
            stem = "az%g_el%g" % (az, el)
        (out / (stem + ".png")).write_bytes(png(b"model " + stem.encode()))
    if "--sheet" in command:
        (out / "sheet.png").write_bytes(png(b"model sheet"))
    return subprocess.CompletedProcess(command, 0, "fixture views", "")


def _install_gate_identity(project):
    """The tool bytes make_round hashes to decide whether a PASS may be reused.

    Without them the identity is unavailable, which correctly disables reuse --
    so a reuse test has to supply them rather than assume them.
    """
    scripts = project / "cad" / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    for name in ("check_thickness", "check_overhang", "check_mesh", "meshlib.py", "printlib.py"):
        (scripts / name).write_text("# fixture %s\n" % name, encoding="utf-8")


def _gate_output(tool, *, fails, feature=None):
    """Stand in for one print gate, in the exact shape make_round parses."""
    named = ("           at feature %s -- band-1 (part_wheel.step.py:7), 0.00 mm away; "
             "0.38 mm under the 0.80 mm wall\n" % feature) if feature else ""
    if tool == "check_thickness":
        if fails:
            return (
                "part_wheel.step.py: 4.20 cm3 solid, grid 0.100 mm\n"
                "  FAIL  wall >= 0.80 mm (+/-0.10)        2.1% of surface below\n"
                "        1. [wall ] 0.42 mm at (1.0, 2.0, 3.0)  12 samples\n"
                + named +
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
        build_stderr="ValueError: wall must be positive\n",
        wall_fails=False,
        overhang_fails=False,
        overhang_unverified=False,
        overhang_unmeasurable=False,
        wall_feature=None,
        argv=None,
        calls=None,
        round_name="r0001",
        interfere=None,
        exit_code=1,
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
                fake_render_review(command)
            if tool == "inspect" and interfere is not None:
                stdout, code = interfere
                Path(kwargs["log"]).write_text(stdout, encoding="utf-8")
                return subprocess.CompletedProcess(command, code, stdout, "")
            if tool in ("check_thickness", "check_overhang"):
                stdout, code = _gate_output(
                    tool,
                    fails=wall_fails if tool == "check_thickness" else overhang_fails,
                    feature=wall_feature,
                )
                if tool == "check_overhang" and overhang_unverified:
                    stdout, code = "", 3
                if tool == "check_overhang" and overhang_unmeasurable:
                    stdout, code = (
                        "part_wheel.step.py: the B-rep is a valid solid, but its tessellation stays "
                        "open at 6 edge(s) even at 0.005 mm deviation. Inside and outside are "
                        "undefined on an open mesh.\nRESULT: UNMEASURABLE MESH\n"), 4
                log = kwargs.get("log")
                if log is not None:
                    Path(log).parent.mkdir(parents=True, exist_ok=True)
                    Path(log).write_text(stdout, encoding="utf-8")
                return subprocess.CompletedProcess(command, code, stdout, "")
            failed = (render_fails and tool == "render_review") or (build_fails and tool == "gen")
            return subprocess.CompletedProcess(command, 1 if failed else 0,
                                               '{"ok":true}\n', build_stderr if failed else "")
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(module, "skills_root", return_value=project), mock.patch.object(module, "run", side_effect=fake_run):
            self.assertEqual(module.main(argv or [str(project)]), exit_code)
        summary = json.loads((project / "measure/rounds" / round_name / "summary.json").read_text())
        return module, summary

    def _feedback(self, project, summary, status="pass"):
        value = {"packet_sha256": summary["visual"]["packet_sha256"], "status": status,
                 "findings": [], "observation": "Inspected all views against the concept.",
                 **fixture_verdicts(summary)}
        if status == "fail":
            value["matches_plan"] = False
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

    def test_visual_packet_binds_side_tilted_views_and_one_review_sheet(self):
        # A dead-on front/top/iso triple hid the side profile and flattened
        # depth; every round now renders the side and tilted three-quarter
        # views and one labelled sheet the Manager opens once.
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            calls = []
            module, summary = self._round(project, calls=calls)
            render = next(c for c in calls if Path(c[1]).name == "render_review")
            self.assertIn("--sheet", render)
            self.assertEqual(rendered_views(render)[:-1], list(module.VISUAL_VIEWS))
            for required in ("front", "top", "iso", "left", "iso_front", "iso_back",
                             "iso_left", "iso_right", "iso_bottom"):
                self.assertIn(required, module.VISUAL_VIEWS)
            packet = json.loads(Path(summary["visual"]["packet"]).read_text())
            names = sorted(Path(path).name for path in packet["images"])
            # The packet binds only the sheet, which holds every view, so a
            # reviewer whose reads the host checks opens one image (ADR 0087).
            self.assertEqual(names, ["sheet.png"])
            self.assertTrue(summary["visual"]["sheet"].endswith("/visual/sheet.png"))
            self.assertIn(summary["visual"]["sheet"], module.render_summary(summary))
            # The sheet is bound evidence: a changed sheet cannot be reviewed.
            Path(summary["visual"]["sheet"]).write_bytes(b"another sheet")
            with self.assertRaisesRegex(ValueError, "stale images"):
                module.record_visual(project, self._feedback(project, summary))

    def test_assembly_preview_renders_the_whole_once_and_is_never_a_round(self):
        # Proportion between parts only shows assembled; a preview shows it
        # while components are rough, without gates, history, state or a pass.
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module = load_module()
            (project / "toy.step.py").write_text("def gen_step(): pass\n")
            (project / "part_wheel.step.py").write_text("def gen_step(): pass\n")
            (project / "part_body.step.py").write_text("def gen_step(): pass\n")
            calls = []

            def fake_run(command, **kwargs):
                calls.append(command)
                return fake_visual_render(command)

            with contextlib.redirect_stdout(io.StringIO()) as stdout, \
                    mock.patch.object(module, "skills_root", return_value=project), \
                    mock.patch.object(module, "run", side_effect=fake_run):
                self.assertEqual(module.main([str(project), "--preview-assembly"]), 0)
                self.assertEqual(module.main([str(project), "--preview-assembly"]), 0)
            self.assertEqual([Path(c[1]).name for c in calls], ["render_review", "render_review"])
            self.assertEqual(Path(calls[0][2]).name, "toy.step.py")
            self.assertEqual(rendered_views(calls[0]), [*module.VISUAL_VIEWS, "sheet"])
            previews = project / "measure/assembly-previews"
            self.assertEqual(sorted(p.name for p in previews.iterdir()), ["p0001", "p0002"])
            record = json.loads((previews / "p0001/preview.json").read_text())
            self.assertEqual(record["kind"], "assembly-preview")
            self.assertEqual(record["components"], ["part_body.step.py", "part_wheel.step.py"])
            self.assertTrue(record["sheet"].endswith("/visual/sheet.png"))
            self.assertIn(record["sheet"], record["images"])
            self.assertIn("never a pass", record["verdict"])
            self.assertIn("not a round and not a pass", stdout.getvalue())
            self.assertFalse((project / "measure/make-round-state.json").exists())
            self.assertFalse((project / "measure/rounds").exists())
            self.assertFalse((project / "measure/component-rounds").exists())

    def test_assembly_preview_needs_components_and_takes_no_round_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module = load_module()
            (project / "toy.step.py").write_text("def gen_step(): pass\n")
            with contextlib.redirect_stderr(io.StringIO()) as stderr, \
                    mock.patch.object(module, "skills_root", return_value=project), \
                    mock.patch.object(module, "run", side_effect=fake_visual_render):
                self.assertEqual(module.main([str(project), "--preview-assembly"]), 2)
            self.assertIn("needs part_<role>.step.py components", stderr.getvalue())
            for extra in (["--component", "part_x.step.py"], ["--require-component-passes"],
                          ["--record-visual", "f.json"], ["--ref", "hero=ref/hero.png"]):
                with self.subTest(extra=extra), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        module.main([str(project), "--preview-assembly", *extra])

    def test_visual_verdict_judges_plan_and_reference_separately(self):
        # A pass must agree with the plan and must not contradict a
        # reference; a reference verdict exists exactly when a reference does.
        def attempt(project, summary, **overrides):
            path = self._feedback(project, summary)
            value = json.loads(path.read_text())
            value.update(overrides)
            path.write_text(json.dumps(value))
            return module.record_visual(project, path)

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            self.assertIn("silhouette, stance and shape language first", summary["visual"]["detail"])
            self.assertIn("a shape language the plan did not ask", summary["visual"]["detail"])
            self.assertIn("construction family", (Path(module.__file__).parents[1] / "SKILL.md").read_text())
            for overrides, message in (
                ({"matches_plan": False}, "needs matches_plan true"),
                ({"matches_plan": None}, "matches_plan must be true or false"),
                ({"matches_reference": True}, "must be null when the packet has no reference"),
            ):
                with self.subTest(overrides=overrides):
                    with self.assertRaisesRegex(ValueError, message):
                        attempt(project, summary, **overrides)
            missing = self._feedback(project, summary)
            value = json.loads(missing.read_text())
            del value["matches_reference"]
            missing.write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError, "invalid visual feedback fields"):
                module.record_visual(project, missing)
            result = module.record_visual(project, self._feedback(project, summary, "fail"))
            self.assertFalse(result["ok"])
            self.assertIs(result["visual"]["matches_plan"], False)
            self.assertIn("plan=false ref=n/a", module.render_summary(result))

        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "ref").mkdir()
            (project / "ref/hero.png").write_bytes(png(b"hero"))
            module, summary = self._round(project, argv=[str(project), "--ref", "hero=ref/hero.png"])
            with self.assertRaisesRegex(ValueError, "true or false when the packet has reference"):
                attempt(project, summary, matches_reference=None)
            with self.assertRaisesRegex(ValueError, "matches_reference not false"):
                attempt(project, summary, matches_reference=False)

    def test_an_unmeasurable_mesh_is_its_own_verdict_and_never_passes_a_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            module, summary = self._round(Path(tmp), overhang_unmeasurable=True)
            item = summary["print"]["wheel"]
            self.assertEqual(item["overhang"]["verdict"], "UNMEASURABLE")
            self.assertEqual(item["verdict"], "UNMEASURABLE")
            self.assertTrue(item["overhang"]["failures"][0].startswith("unmeasurable mesh: "))
            self.assertIn("tessellation stays open", item["overhang"]["failures"][0])
            self.assertEqual(item["overhang"]["defects"], [])
            self.assertFalse(summary["checks_ok"])
            self.assertFalse(module.reusable_print(item))
            self.assertIn("over  UNMEASURABLE", module.render_summary(summary))
        with tempfile.TemporaryDirectory() as tmp:
            _, summary = self._round(Path(tmp), wall_fails=True, overhang_unmeasurable=True)
            self.assertEqual(summary["print"]["wheel"]["verdict"], "FAIL")

    def test_a_feature_that_fails_again_is_a_repeated_print_defect(self):
        feature = "band@part_wheel.step.py:7"
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, first = self._round(project, wall_fails=True, wall_feature=feature)
            self.assertEqual(first["print"]["wheel"]["thickness"]["defects"], [feature])
            self.assertEqual(first["repeated_print_defects"], {})
            self.assertIn("at " + feature, module.render_summary(first))
            _, second = self._round(project, wall_fails=True, wall_feature=feature, round_name="r0002")
            self.assertEqual(second["print"]["wheel"]["repeated_defects"], [feature])
            self.assertEqual(second["repeated_print_defects"], {"wheel": [feature]})
            self.assertIn("again FAIL wheel", " ".join(module.render_summary(second).split()))
            # A different feature failing is a new defect, not a repeat.
            _, third = self._round(project, wall_fails=True, wall_feature="plane@(1,2,3)",
                                   round_name="r0003")
            self.assertEqual(third["repeated_print_defects"], {})

    def test_every_detail_refusal_of_a_build_is_in_the_summary(self):
        # Issue #86: the worker reads every refusal, with what would pass,
        # from the summary; a detail refused at the same site again is flagged.
        refused = (
            "[scripts/gen] FAILED: DetailRefusals: 2 Detail Refusals in this build; each detail was "
            "left out of this build, which fails until every one passes:\n"
            'detail-refusal {"feature": "rivet", "passes": "h >= 0.85 mm or d <= 1.90 mm at this spot", '
            '"reason": "rivet: the host falls 0.80 mm away under its edge, more than its 0.60 mm height", '
            '"site": "part_wheel.step.py:9"}\n'
            'detail-refusal {"feature": "band", "passes": "width >= 0.90 mm", '
            '"reason": "band: width 0.60 mm is below the min relief width of 0.90 mm", '
            '"site": "part_wheel.step.py:10"}\n'
            "[scripts/gen]   raised in .../generation_runner.py:406\n"
            "[scripts/gen] re-run with --verbose for the full traceback\n")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, first = self._round(project, build_fails=True, build_stderr=refused)
            build = first["build"]["wheel"]
            self.assertEqual(build["verdict"], "FAIL")
            self.assertEqual([item["feature"] for item in build["detail_refusals"]], ["rivet", "band"])
            self.assertEqual(build["detail_refusals"][0]["site"], "part_wheel.step.py:9")
            self.assertEqual(build["detail_refusals"][0]["passes"], "h >= 0.85 mm or d <= 1.90 mm at this spot")
            self.assertEqual(first["repeated_detail_refusals"], {})
            text = module.render_summary(first)
            self.assertIn("refuse rivet at part_wheel.step.py:9: rivet: the host falls 0.80 mm", text)
            self.assertIn("passes with h >= 0.85 mm or d <= 1.90 mm at this spot", text)
            self.assertIn("refuse band at part_wheel.step.py:10", text)
            _, second = self._round(project, build_fails=True, build_stderr=refused, round_name="r0002")
            self.assertEqual(second["repeated_detail_refusals"],
                             {"wheel": ["rivet@part_wheel.step.py:9", "band@part_wheel.step.py:10"]})
            self.assertEqual(second["repeated_print_defects"], {})
            self.assertIn("again REFUSE rivet@part_wheel.step.py:9", module.render_summary(second))
            self.assertIn("leave it out and name it in your report", module.render_summary(second))
            # A round that builds clears them: a later refusal is new.
            self._round(project, round_name="r0003")
            _, fourth = self._round(project, build_fails=True, build_stderr=refused, round_name="r0004")
            self.assertEqual(fourth["repeated_detail_refusals"], {})

    def test_print_defects_are_the_failing_regions_named_features(self):
        module = load_module()
        stdout = (
            "        1. [wall ] 0.42 mm at (1.0, 2.0, 3.0)  12 samples\n"
            "           at feature band@part_x.step.py:7 -- band-1 (part_x.step.py:7), 0.00 mm away; x\n"
            "        2. [taper] 0.70 mm at (1.0, 2.0, 3.0)  3 samples\n"
            "           at face plane@(0,0,1) -- face 3 (plane), 0.00 mm away; x\n"
            "        3. [wall ] 0.50 mm at (9.0, 2.0, 3.0)  12 samples\n"
            "           at face cone@(9,2,3) -- face 7 (cone), 0.10 mm away; x\n"
            "        4. [wall ] 0.50 mm at (9.0, 2.0, 3.0)  12 samples\n"
            "           0.30 mm under the 0.80 mm wall\n"
        )
        self.assertEqual(module.print_defects(stdout, "wall"), ["band@part_x.step.py:7", "cone@(9,2,3)"])
        self.assertEqual(module.print_defects(stdout, "overhang"), [])
        previous = {"verdict": "FAIL", "thickness": {"defects": ["a", "b"]}, "overhang": {"defects": []}}
        current = {"thickness": {"defects": ["b", "c"]}, "overhang": {"defects": ["a"]}}
        self.assertEqual(module.repeated_defects(previous, current), ["b", "a"])
        self.assertEqual(module.repeated_defects({**previous, "verdict": "PASS"}, current), [])
        self.assertEqual(module.repeated_defects(None, current), [])

    def test_no_reference_round_requires_visual_inspection_and_reports_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            self.assertTrue(summary["checks_ok"])
            self.assertFalse(summary["ok"])
            self.assertEqual(summary["visual"]["status"], "pending")
            packet = json.loads(Path(summary["visual"]["packet"]).read_text())
            self.assertEqual([Path(path).name for path in packet["images"]], ["sheet.png"])
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
        for change in ("source", "imported_helper", "imported_step", "image", "packet", "wrong_round", "contradiction"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module, summary = self._round(project)
                path = self._feedback(project, summary)
                packet_path = Path(summary["visual"]["packet"])
                packet = json.loads(packet_path.read_text())
                if change == "source":
                    (project / "toy.step.py").write_text("changed")
                elif change == "imported_helper":
                    # A module the entry now imports is one of its Geometry Sources.
                    (project / "proof.py").write_text("SIZE = 2\n")
                    (project / "toy.step.py").write_text("import proof\ndef gen_step(): pass\n")
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

    def test_a_proof_helper_no_entry_imports_leaves_the_assembly_packet_current(self):
        # Issue #110: only Geometry Sources stale a shape check; a review
        # helper or an audit beside the geometry does not.
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project)
            path = self._feedback(project, summary)
            for relative in ("review/early-proof/proof.py", "measure/check_spec.py", "notes/why.md"):
                (project / relative).parent.mkdir(parents=True, exist_ok=True)
                (project / relative).write_text("changed helper\n")
            self.assertTrue(module.record_visual(project, path)["ok"])

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
                    for view in rendered_views(command):
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
            # Issue #118: final verification's interference check runs on the
            # entry too; it runs beside the render, so the order is free.
            self.assertCountEqual(
                calls, ["gen", "check_thickness", "check_overhang", "check_mesh", "inspect", "render_review"]
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
                    for view in rendered_views(command):
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
                for view in rendered_views(command):
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
                    for view in rendered_views(command):
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
                if tool == "reproduce_build":
                    # Issue #102: the component round's second build reproduces it.
                    return subprocess.CompletedProcess(
                        command, 0, json.dumps({"identitySha256": identity["value"]}) + "\n", ""
                    )
                if tool == "render_review":
                    out = Path(command[command.index("-o") + 1])
                    out.mkdir()
                    for view in rendered_views(command):
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


    # Issue #118: an assembly round runs final verification's interference check.
    CLASH = json.dumps({
        "ok": False, "entry": "toy", "tolerance": 1.0, "clashCount": 2, "errors": [],
        "clashes": [
            {"a": {"ref": "o1.2", "name": "legs_pelvis_gray"}, "b": {"ref": "o1.7", "name": "arm_left_gray"},
             "volume": 120.17828304579271,
             "bounds": {"min": [19.432003743420644, -4.0000006, 71.49152686486907],
                        "max": [24.0000006, 4.8626087301133785, 129.0000006]}},
            {"a": {"ref": "o1.3", "name": "chest_cage_gray"}, "b": {"ref": "o1.6", "name": "crest_helm_gray"},
             "volume": 17.410180751106243,
             "bounds": {"min": [-5.135416844083811, -2.0000005999999857, 197.49999880000001],
                        "max": [5.135416844083818, 0.977036397141852, 200.00158045976676]}},
        ]})
    UNBUILT = json.dumps({"ok": False, "errors": [{"type": "ModuleNotFoundError", "message": "No module named 'params'"}]})

    def test_an_assembly_round_runs_final_verifications_interference_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            calls = []
            module, summary = self._round(project, calls=calls)
            self.assertTrue(summary["checks_ok"])
            self.assertEqual(summary["interference"]["verdict"], "pass")
            inspect = [command for command in calls if Path(command[1]).name == "inspect"]
            self.assertEqual(len(inspect), 1)
            # The tool and request verify_project's inspect batch sends
            # (["interfere", entry]) at its default tolerance.
            self.assertEqual(inspect[0][2:], ["interfere", "toy.step.py", "--format", "json"])
            self.assertNotIn("--tolerance", inspect[0])

    def test_verify_project_runs_the_same_interference_request(self):
        roots = product_run_domain_skill_roots()
        text = (roots["cad"] / "scripts" / "verify_project").read_text(encoding="utf-8")
        self.assertIn('{"id": "interfere:assembly", "argv": ["interfere", entry]}', text)

    def test_a_clash_between_components_fails_the_assembly_round_and_names_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            module, summary = self._round(project, interfere=(self.CLASH, 2))
            self.assertFalse(summary["checks_ok"])
            self.assertFalse(summary["ok"])
            interference = summary["interference"]
            self.assertEqual(interference["verdict"], "fail")
            self.assertEqual([(c["a"], c["b"]) for c in interference["clashes"]],
                             [("legs_pelvis_gray", "arm_left_gray"), ("chest_cage_gray", "crest_helm_gray")])
            self.assertEqual(interference["clashes"][0]["at"],
                             {"min": [19.43, -4.0, 71.49], "max": [24.0, 4.86, 129.0]})
            self.assertIn("legs_pelvis_gray x arm_left_gray 120.18 mm3 at X 19.43..24 Y -4..4.86 Z 71.49..129",
                          interference["detail"])
            self.assertIn("chest_cage_gray x crest_helm_gray 17.41 mm3", interference["detail"])
            text = module.render_summary(summary)
            self.assertIn("clash FAIL", text)
            self.assertIn("Z 197.5..200", text)
            # A clean visual pass cannot carry a clashing assembly to --full.
            feedback = self._feedback(project, summary)
            with mock.patch.object(module, "run") as runner:
                with self.assertRaisesRegex(ValueError, "clean round and visual pass"):
                    module.record_visual(project, feedback, full=True)
                runner.assert_not_called()

    def test_an_assembly_entry_that_cannot_build_its_parts_fails_the_round_loudly(self):
        for label, interfere in (("import error", (self.UNBUILT, 2)), ("no result", ("", 1)),
                                 ("timeout", ("", 124))):
            with self.subTest(label), tempfile.TemporaryDirectory() as tmp:
                project = Path(tmp)
                module, summary = self._round(project, interfere=interfere)
                self.assertFalse(summary["checks_ok"])
                self.assertEqual(summary["interference"]["verdict"], "error")
                self.assertIn("could not be checked for interference", summary["interference"]["detail"])
                if label == "import error":
                    self.assertIn("No module named 'params'", summary["interference"]["detail"])
                self.assertIn("clash ERRO", module.render_summary(summary))

    def test_an_unfinished_interference_check_is_unverified_as_final_verification_reads_it(self):
        unfinished = json.dumps({"ok": False, "status": "unverified", "errors": [], "clashCount": 0,
                                 "unverified": ["geometry inspection time allowance exhausted"]})
        with tempfile.TemporaryDirectory() as tmp:
            module, summary = self._round(Path(tmp), interfere=(unfinished, 3))
            self.assertTrue(summary["checks_ok"])
            self.assertEqual(summary["interference"]["verdict"], "unverified")
            self.assertEqual(summary["geometry_status"], "unverified")
            self.assertFalse(summary["print_ready_claim"])

    def test_a_part_that_did_not_build_leaves_the_assembly_unchecked_not_passed(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            module, summary = self._round(Path(tmp), build_fails=True, calls=calls)
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["interference"]["verdict"], "not-run")
            self.assertNotIn("inspect", [Path(command[1]).name for command in calls])

    def test_the_interference_check_runs_in_order_with_one_job(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"MAKE_ROUND_JOBS": "1"}):
            module, summary = self._round(Path(tmp), interfere=(self.CLASH, 2))
            self.assertEqual(summary["interference"]["verdict"], "fail")
            self.assertFalse(summary["checks_ok"])

    def test_skill_is_registered_with_its_tool_card(self):
        root = product_run_domain_skill_roots()["make-round"]
        text = (root / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: make-round\n"))
        for tool in ("gen", "render_review", "check_motion", "verify_project", "--record-review"):
            self.assertIn(tool, text)
        self.assertIn("at most once per round", text)
        self.assertIn("--component", text)
        self.assertIn("--require-component-passes", text)
        # Issue #113: a round never shares a command with a file edit.
        flat = " ".join(text.split())
        self.assertIn("run `make_round` as its own plain Bash command, never in the same "
                      "command as a file edit, a heredoc", flat)
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

    def test_contract_mode_labels_a_reference_sealed_with_a_doubled_place_prefix(self):
        # Before 3c74e963 the host sealed ref-01-whole.png as
        # ref-01-ref-01-whole.png; runs sealed then keep that name for good.
        with tempfile.TemporaryDirectory() as tmp:
            context = {
                "design_contract": {
                    "title": "Antisol",
                    "references": [{"file": "ref-01-whole.png", "shows": "geometry:world-disc"}],
                }
            }
            project = self._run_root(tmp, {"ref-01-ref-01-whole.png": b"whole"}, context=context)
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertEqual(self._shown(summary), [])
            self.assertEqual([i["label"] for i in summary["reference_errors"]], ["geometry:world-disc"])

    def test_contract_mode_does_not_relabel_a_doubled_prefix_for_another_place(self):
        with tempfile.TemporaryDirectory() as tmp:
            context = {
                "design_contract": {
                    "title": "Antisol",
                    "references": [{"file": "ref-01-whole.png", "shows": "geometry:world-disc"}],
                }
            }
            project = self._run_root(tmp, {"ref-02-ref-01-whole.png": b"whole"}, context=context)
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            summary = self._assembly(project)
            self.assertEqual(self._shown(summary), ["ref-02-ref-01-whole"])

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

    def _pending_body_review(self, module, project):
        argv = ["--component", "part_body.step.py", "--ref", "body=wish-references/ref-01-body.png"]
        self._main(module, project, argv, [])
        summary = json.loads((project / "measure/component-rounds/body/r0001/summary.json").read_text())
        return write_review(project, summary)

    def test_another_components_own_files_do_not_stale_a_pending_component_packet(self):
        # ADR 0077: Component Workers run in parallel, so another Component's
        # source and STEP change while this Component's review is pending.
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-body.png": b"body"})
            (project / "part_wheel.step.py").write_text("def gen_step(): return 'wheel'\n")
            module = load_module()
            review = self._pending_body_review(module, project)
            (project / "part_wheel.step.py").write_text("def gen_step(): return 'wheel v2'\n")
            (project / "part_wheel.step").write_text("wheel v2 step\n")
            self.assertTrue(module.record_review(project, review, "part_body.step.py")["ok"])

    def _helpers(self, project):
        (project / "features").mkdir()
        (project / "features/__init__.py").write_text("")
        (project / "features/forms.py").write_text("from .rings import RING\nWIDTH = 1\n")
        (project / "features/rings.py").write_text("RING = 2\n")
        (project / "features/housing.py").write_text("INTERIOR = 3\n")
        (project / "params.py").write_text("SCALE = 1\n")
        (project / "part_body.step.py").write_text(
            "from features import forms\nimport params\ndef gen_step(): return 'body'\n")

    def test_an_imported_shared_helper_or_own_source_change_stales_a_pending_component_packet(self):
        # ADR 0081: only what the Component imports, directly or not.
        for changed in ("features/forms.py", "features/rings.py", "features/__init__.py", "params.py",
                        "part_body.step.py"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                project = self._run_root(tmp, {"ref-01-body.png": b"body"})
                self._helpers(project)
                module = load_module()
                review = self._pending_body_review(module, project)
                (project / changed).write_text("# changed\n")
                with self.assertRaisesRegex(ValueError, "stale CAD sources"):
                    module.record_review(project, review, "part_body.step.py")

    def test_an_unimported_shared_helper_or_the_entry_does_not_stale_a_component_packet(self):
        for changed in ("features/housing.py", "toy.step.py", "toy_spec.md"):
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as tmp:
                project = self._run_root(tmp, {"ref-01-body.png": b"body"})
                self._helpers(project)
                module = load_module()
                review = self._pending_body_review(module, project)
                (project / changed).write_text("# changed\n")
                self.assertTrue(module.record_review(project, review, "part_body.step.py")["ok"])

    def test_the_summary_lists_the_imported_shared_helpers_and_their_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-body.png": b"body"})
            self._helpers(project)
            module = load_module()
            self._pending_body_review(module, project)
            summary = json.loads((project / "measure/component-rounds/body/r0001/summary.json").read_text())
            expected = {path: hashlib.sha256((project / path).read_bytes()).hexdigest()
                        for path in ("features/__init__.py", "features/forms.py", "features/rings.py", "params.py")}
            self.assertEqual(summary["imported_helpers"], expected)
            self.assertIn("helpers features/__init__.py", module.render_summary(summary))

    def test_the_assembly_packet_still_binds_every_component_source(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            (project / "part_body.step.py").write_text("body\n")
            (project / "part_wheel.step.py").write_text("wheel\n")
            self.assertEqual(sorted(module.source_hashes(project)), ["part_body.step.py", "part_wheel.step.py"])
            self.assertEqual(sorted(module.component_sources(project, "body")), ["part_body.step.py"])

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
                                            "status": "pass", "findings": [], "observation": observation,
                                            **fixture_verdicts(summary)}))
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
                                            "findings": [], "observation": "Inspected.", "differences": differences,
                                            **fixture_verdicts(summary)}))
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
                "matches_plan": True, "matches_reference": True,
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

    def test_a_component_round_records_the_worker_nonce_it_was_given(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls, extra=("--worker-nonce", "ab" * 16))
            self.assertEqual(summary["worker_nonce"], "ab" * 16)
            result = self._review(module, project, summary)
            self.assertEqual(result["worker_nonce"], "ab" * 16)
            _, unguarded = self._component(module, project, calls, edit=False)
            self.assertEqual(unguarded["round"], 2)
            self.assertIsNone(unguarded["worker_nonce"])

    def test_every_field_the_worker_reports_is_in_the_rounds_summary_and_output(self):
        """Issue #98: each summary field the worker definition names exists."""
        import re
        from workshop.make.role_agents import (
            COMPONENT_WORKER, make_role_agent_files, parse_make_role_agent_bytes)

        content = make_role_agent_files()[COMPONENT_WORKER]
        instructions = parse_make_role_agent_bytes(COMPONENT_WORKER, content)["developer_instructions"]
        report = instructions[instructions.index("- Report to the Manager"):]
        report = report[:report.index("\n- ")]
        fields = [name for name in re.findall(r"`([a-z_]+(?:\.[a-z_0-9]+)*)`", report)
                  if not name.endswith(".json")]
        self.assertEqual(sorted(fields), ["identity", "round", "shape_rounds_used", "visual.packet", "visual.packet_sha256"])
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
            printed = module.render_summary(summary)
            for field in fields:
                with self.subTest(field=field):
                    value = summary
                    for key in field.split("."):
                        self.assertIn(key, value)
                        value = value[key]
                    self.assertIsNotNone(value)
                    if isinstance(value, str):
                        self.assertIn(value, printed)
            self.assertEqual(summary["identity"], state["identity"])
            self.assertIn("r%04d" % summary["round"], printed)
            # A recorded review keeps both values in the round's summary.
            reviewed = self._review(module, project, summary)
            self.assertEqual((reviewed["identity"], reviewed["visual"]["packet_sha256"]),
                             (summary["identity"], summary["visual"]["packet_sha256"]))
            self.assertIn(summary["identity"], module.render_summary(reviewed))
            self.assertIn(summary["visual"]["packet_sha256"], module.render_summary(reviewed))

    def test_a_worker_nonce_belongs_only_to_a_component_build_round(self):
        module = load_module()
        nonce = "ab" * 16
        with contextlib.redirect_stderr(io.StringIO()):
            for argv in (["/tmp", "--worker-nonce", nonce],
                         ["/tmp", "--component", "part_body.step.py", "--record-review", "r.json",
                          "--worker-nonce", nonce],
                         ["/tmp", "--component", "part_body.step.py", "--worker-nonce", "not-hex"]):
                with self.subTest(argv=argv), self.assertRaises(SystemExit):
                    module.main(argv)

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
                packet_path = Path(summary["visual"].get("packet", "/nonexistent"))
                packet = json.loads(packet_path.read_text()) if change != "checks" else {}
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

    def test_only_the_first_geometry_change_after_a_disagreeing_review_is_a_shape_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls, faults={"wall": True})
            self.assertEqual((summary["shape_rounds_used"], summary["shape_round"]), (0, False))
            # repairing a print failure is not a shape round
            _, summary = self._component(module, project, calls)
            self.assertEqual((summary["shape_rounds_used"], summary["phase"]), (0, "awaiting-review"))
            # a rerun that changes no geometry is admitted and not counted
            code, summary = self._component(module, project, calls, edit=False)
            self.assertEqual((code, summary["round"], summary["shape_rounds_used"]), (1, 3, 0))
            self._disagree(module, project, summary)
            # a build that fails after the review produced no new shape
            _, summary = self._component(module, project, calls, faults={"build": True})
            self.assertEqual((summary["shape_rounds_used"], summary["phase"]), (0, "disagreed"))
            # the first changed geometry is the shape round, even when its print fails
            _, summary = self._component(module, project, calls, faults={"wall": True})
            self.assertEqual((summary["shape_rounds_used"], summary["shape_round"]), (1, True))
            self.assertIn("this round is a shape round", module.render_summary(summary))
            # the print repairs that follow are free
            _, summary = self._component(module, project, calls, faults={"wall": True})
            self.assertEqual((summary["shape_rounds_used"], summary["shape_round"]), (1, False))
            _, summary = self._component(module, project, calls)
            self.assertEqual((summary["shape_rounds_used"], summary["shape_round"], summary["phase"]),
                             (1, False, "awaiting-review"))

    def test_a_passing_round_is_reviewed_before_its_geometry_may_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            before = len(calls)
            code, latest = self._component(module, project, calls)
            self.assertEqual(code, 2)
            self.assertIn("has no Component Review; report it and wait", self.stderr)
            self.assertEqual(latest["round"], 1)
            self.assertFalse((project / "measure/component-rounds/body/r0002").exists())
            # only the builds ran (gen and, beside it, the reproduction build):
            # no print gate, no render
            self.assertEqual(sorted(Path(c[1]).name for c in calls[before:]), ["gen", "reproduce_build"])
            # a build that fails is a change too
            code, _ = self._component(module, project, calls, faults={"build": True})
            self.assertEqual(code, 2)

    def test_a_round_that_fails_its_checks_is_not_rendered(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            for fault in ({"wall": True}, {"build": True}):
                with self.subTest(fault=fault):
                    before = len(calls)
                    _, summary = self._component(module, project, calls, faults=fault)
                    self.assertNotIn("render_review", [Path(c[1]).name for c in calls[before:]])
                    self.assertEqual(summary["visual"]["status"], "not-rendered")
                    self.assertFalse((Path(summary["out"]) / "visual").exists())
                    self.assertIn("visual NOT-RENDERED", module.render_summary(summary))
                    with self.assertRaisesRegex(ValueError, "did not pass its build and print checks"):
                        self._review(module, project, summary)

    def test_at_the_limit_a_disagreeing_review_becomes_a_recorded_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            summary = self._five_shape_rounds(module, project, calls)
            # no sixth shape repair before the review
            code, _ = self._component(module, project, calls)
            self.assertEqual(code, 2)
            self.assertIn("has no Component Review", self.stderr)
            # the worker reverts; the refused build left the pending packet intact
            (project / "part_body.step.py").write_text("def gen_step(): return 'body %d'\n" % (self._edits - 1))
            result = self._disagree(module, project, summary)
            self.assertTrue(result["ok"])
            self.assertEqual(result["accepted"], {"reviewer": "fresh-reviewer-subagent",
                                                  "reason": "The arm is too thin.", "shape_rounds": 5})
            self.assertIn("ACCEPTED at the shape-repair limit", module.render_summary(result))
            self.assertEqual(result["locked"], {"round": 6, "source": "component-acceptance"})
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

    def test_an_accepted_component_is_locked_and_an_unchanged_rerun_carries_the_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            summary = self._five_shape_rounds(module, project, calls)
            accepted = self._disagree(module, project, summary)
            code, _ = self._component(module, project, calls)
            self.assertEqual(code, 2)
            self.assertIn("locked by a Component Acceptance of r0006", self.stderr)
            # revert the refused edit: the reviewed B-rep is rebuilt
            (project / "part_body.step.py").write_text("def gen_step(): return 'body %d'\n" % (self._edits - 1))
            code, summary = self._component(module, project, calls, edit=False)
            self.assertEqual((code, summary["round"]), (0, 7))
            self.assertEqual(summary["review"], {**accepted["review"], "carried_from": 6})
            self.assertEqual(summary["accepted"], accepted["accepted"])
            self.assertEqual(summary["visual"]["status"], "carried")
            self.assertEqual(summary["locked"], {"round": 6, "source": "component-acceptance"})
            self.assertIn("(carried from r0006)", module.render_summary(summary))
            with self.assertRaisesRegex(ValueError, "already has a recorded review"):
                self._disagree(module, project, summary)
            digests = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())["parts"]
            self.assertEqual(list(module.component_coverage(project, digests).values())[0]["accepted"],
                             accepted["accepted"])

    def _locked_with_helper(self, module, project, calls, identity):
        """A Component importing features/forms.py, agreed and locked."""
        (project / "features").mkdir()
        (project / "features/forms.py").write_text("WIDTH = 1\n")
        (project / "part_body.step.py").write_text("from features.forms import WIDTH\ndef gen_step(): return 'body'\n")
        with mock.patch.object(module, "parse_identity", side_effect=lambda _out: identity["value"]):
            _, summary = self._component(module, project, calls, edit=False)
        self._review(module, project, summary)
        return summary

    def _built(self, module, project, calls, identity, **kwargs):
        with mock.patch.object(module, "parse_identity", side_effect=lambda _out: identity["value"]):
            return self._component(module, project, calls, edit=False, **kwargs)

    def test_a_locked_component_refuses_a_change_without_an_unlock(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls, identity = load_module(), [], {"value": "a" * 64}
            self._locked_with_helper(module, project, calls, identity)
            identity["value"] = "b" * 64
            code, latest = self._built(module, project, calls, identity)
            self.assertEqual((code, latest["round"]), (2, 1))
            self.assertIn("locked by an agreeing review of r0001", self.stderr)
            # editing a helper the Component does not import unlocks nothing
            (project / "features/housing.py").write_text("INTERIOR = 2\n")
            code, _ = self._built(module, project, calls, identity)
            self.assertEqual(code, 2)

    def test_an_imported_helper_change_unlocks_and_an_identical_brep_carries_the_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls, identity = load_module(), [], {"value": "a" * 64}
            first = self._locked_with_helper(module, project, calls, identity)
            (project / "features/forms.py").write_text("WIDTH = 1  # reworded\n")
            code, summary = self._built(module, project, calls, identity)
            self.assertEqual(code, 0)
            self.assertEqual(summary["unlock"], [{"kind": "shared-helper", "paths": ["features/forms.py"]}])
            self.assertEqual(summary["review"]["carried_from"], 1)
            self.assertEqual(summary["locked"], {"round": 1, "source": "agreeing-review"})
            self.assertFalse(summary["shape_round"])
            self.assertNotEqual(summary["imported_helpers"], first["imported_helpers"])
            self.assertIn("unlock imported Shared Helper changed: features/forms.py", module.render_summary(summary))
            # relocked on the new helper bytes: a change is refused again
            identity["value"] = "b" * 64
            code, _ = self._built(module, project, calls, identity)
            self.assertEqual(code, 2)

    def test_an_imported_helper_change_that_moves_the_brep_awaits_review_and_keeps_the_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls, identity = load_module(), [], {"value": "a" * 64}
            (project / "features").mkdir()
            (project / "features/forms.py").write_text("WIDTH = 1\n")
            (project / "part_body.step.py").write_text("from features.forms import WIDTH\ndef gen_step(): return 'body'\n")
            _, summary = self._built(module, project, calls, identity)
            self._disagree(module, project, summary)
            identity["value"] = "b" * 64
            _, summary = self._built(module, project, calls, identity)
            self.assertEqual(summary["shape_rounds_used"], 1)
            self._review(module, project, summary)
            (project / "features/forms.py").write_text("WIDTH = 2\n")
            identity["value"] = "c" * 64
            # an unlocked failing round is admitted and free
            code, summary = self._built(module, project, calls, identity, faults={"wall": True})
            self.assertEqual((code, summary["shape_round"], summary["phase"]), (1, False, "locked"))
            code, summary = self._built(module, project, calls, identity)
            self.assertEqual((code, summary["phase"], summary["shape_rounds_used"]), (1, "awaiting-review", 1))
            self.assertIsNone(summary["review"])
            self.assertIsNone(summary["locked"])
            self.assertEqual(summary["visual"]["status"], "pending")

    def test_a_disagreeing_review_at_the_cap_after_an_unlock_is_a_new_acceptance(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            summary = self._five_shape_rounds(module, project, calls)
            self._disagree(module, project, summary)
            (project / "features").mkdir()
            (project / "features/forms.py").write_text("WIDTH = 1\n")
            # The Manager moves the Component onto a helper only through an
            # unlock; here a sixth geometry arrives with an assembly unlock.
            unlock = self._assembly_unlock(module, project, calls)
            self.assertEqual(unlock["assembly_round"], 1)
            code, summary = self._component(module, project, calls)
            self.assertEqual((code, summary["shape_round"], summary["shape_rounds_used"]), (1, False, 5))
            self.assertEqual(summary["unlock"][0]["kind"], "assembly")
            self.assertIn("unlock assembly r0001", module.render_summary(summary))
            review = write_review(project, summary, agrees=False, reason="Still too thin.", differences=self.DIFFERS)
            code = self._main(module, project, ["--component", "part_body.step.py", "--record-review", str(review)], calls)
            self.assertEqual(code, 0)
            result = json.loads(Path(summary["out"], "summary.json").read_text())
            self.assertEqual(result["accepted"], {"reviewer": "fresh-reviewer-subagent", "reason": "Still too thin.",
                                                  "shape_rounds": 5})
            self.assertEqual(result["locked"], {"round": summary["round"], "source": "component-acceptance"})

    def _assembly_unlock(self, module, project, calls, finding=0):
        """Run an assembly round, record a failing finding, and unlock part_body from it."""
        self._main(module, project, [], calls)
        assembly = self._assembly(project)
        feedback = project / "measure/assembly-feedback.json"
        feedback.write_text(json.dumps({
            "packet_sha256": assembly["visual"]["packet_sha256"], "status": "fail",
            "findings": [{"part": "body", "defect": "socket misses the arm peg", "evidence": "iso: gap",
                          "repair": "move the socket 2 mm up"}],
            "observation": "Round %d: the arm floats off the body socket in the iso view." % assembly["round"],
            **fixture_verdicts(assembly), "matches_plan": False,
        }))
        module.record_visual(project, feedback)
        path = project / "measure/unlock.json"
        path.write_text(json.dumps({"assembly_round": assembly["round"], "finding": finding,
                                    "reason": "Assembly r%04d: the socket misses the arm peg." % assembly["round"]}))
        code = self._main(module, project, ["--component", "part_body.step.py", "--record-unlock", str(path)], calls)
        if code:
            raise ValueError(self.stderr)
        state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
        return state["policy"]["unlocks"][-1]

    def test_an_assembly_unlock_cites_a_recorded_finding_and_builds_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self._review(module, project, summary)
            with self.assertRaisesRegex(ValueError, "has no finding 3"):
                self._assembly_unlock(module, project, calls, finding=3)
            unlock = self._assembly_unlock(module, project, calls)
            self.assertEqual(unlock["finding"]["defect"], "socket misses the arm peg")
            self.assertEqual(unlock["reason"], "Assembly r0002: the socket misses the arm peg.")
            # recording an unlock runs no tool
            before = len(calls)
            self.assertEqual(self._main(module, project, ["--component", "part_body.step.py", "--record-unlock",
                                                          str(project / "measure/unlock.json")], calls), 0)
            self.assertEqual(len(calls), before)
            code, summary = self._component(module, project, calls)
            self.assertEqual((code, summary["shape_round"], summary["phase"]), (1, False, "awaiting-review"))
            self.assertEqual(summary["unlock"], [unlock, unlock])

    def test_an_unlock_needs_a_locked_component_and_a_recorded_assembly_finding(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            self._component(module, project, calls)
            path = project / "measure/unlock.json"
            path.write_text(json.dumps({"assembly_round": 1, "finding": 0, "reason": "r0001 needs it"}))
            with self.assertRaisesRegex(ValueError, "is not locked"):
                module.record_unlock(project, path, "part_body.step.py")
            _, summary = self._component(module, project, calls, edit=False)
            self._review(module, project, summary)
            with self.assertRaisesRegex(ValueError, "r0001 has no recorded visual finding"):
                module.record_unlock(project, path, "part_body.step.py")
            path.write_text(json.dumps({"assembly_round": 1, "finding": 0}))
            with self.assertRaisesRegex(ValueError, "assembly_round, finding and reason"):
                module.record_unlock(project, path, "part_body.step.py")
        with contextlib.redirect_stderr(io.StringIO()):
            for argv in (["/tmp", "--record-unlock", "u.json"],
                         ["/tmp", "--component", "part_body.step.py", "--record-unlock", "u.json",
                          "--record-review", "r.json"],
                         ["/tmp", "--component", "part_body.step.py", "--record-unlock", "u.json",
                          "--worker-nonce", "ab" * 16]):
                with self.subTest(argv=argv), self.assertRaises(SystemExit):
                    module.main(argv)

    def test_a_changed_reference_or_contract_row_does_not_carry_a_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self._review(module, project, summary)
            wish_path = module.run_root(project) / "WISH.json"
            wish = json.loads(wish_path.read_text())
            wish["context"]["design_contract"]["requirements"] = [
                {"id": "R1", "scope": "geometry:body", "text": "The arm is as thick as the leg."}]
            wish_path.write_text(json.dumps(wish))
            code, summary = self._component(module, project, calls, edit=False)
            self.assertEqual((code, summary["phase"]), (1, "awaiting-review"))
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


class ReviewerBindingTest(unittest.TestCase):
    """Issue #77: on Claude Code a review names its Component Reviewer by native
    agent id, and the Component's first review binds that id."""

    _contract_root = ContractComponentReviewTest._contract_root
    _run_root = ContractComponentReviewTest._run_root
    _fake_run = ContractComponentReviewTest._fake_run
    _main = ContractComponentReviewTest._main
    _component = ContractComponentReviewTest._component
    _review = ContractComponentReviewTest._review
    REFS = ContractComponentReviewTest.REFS
    CONTRACT = ContractComponentReviewTest.CONTRACT
    DIFFERS = ContractComponentReviewTest.DIFFERS
    FIRST = "a1f355b61d99918ed"
    SECOND = "a7740f58e37677176"

    def setUp(self):
        patcher = mock.patch.dict("os.environ", {"WORKSHOP_REVIEWER_RUNTIME": "claude"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def _state(self, project):
        return json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())

    def test_a_reviewer_that_is_not_a_native_agent_id_is_refused(self):
        for reviewer in ("component-reviewer", "<subagent name>", "A1F355B61D99918ED",
                         "a1f355b61d99918e", " a1f355b61d99918ed"):
            with self.subTest(reviewer=reviewer), tempfile.TemporaryDirectory() as tmp:
                project = self._contract_root(tmp)
                module, calls = load_module(), []
                _, summary = self._component(module, project, calls)
                with self.assertRaisesRegex(ValueError, "native agent id"):
                    self._review(module, project, summary, reviewer=reviewer)
                self.assertIsNone(json.loads(
                    (project / "measure/component-rounds/body/r0001/summary.json").read_text())["review"])

    def test_the_first_id_binds_and_only_that_id_reviews_the_component_again(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self._review(module, project, summary, reviewer=self.FIRST, agrees=False,
                         reason="The arm is too thin.", differences=self.DIFFERS)
            self.assertEqual(self._state(project)["reviewer_id"], self.FIRST)
            _, summary = self._component(module, project, calls)
            # The binding outlives the round that made it.
            self.assertEqual(self._state(project)["reviewer_id"], self.FIRST)
            review = write_review(project, summary, reviewer=self.SECOND)
            code = self._main(module, project, ["--component", "part_body.step.py", "--record-review", str(review)], calls)
            self.assertEqual(code, 2)
            self.assertIn("bound to reviewer %s" % self.FIRST, self.stderr)
            self.assertIsNone(json.loads(Path(summary["visual"]["packet"]).parent.joinpath("summary.json").read_text())["review"])
            review = write_review(project, summary, reviewer=self.FIRST)
            code = self._main(module, project, ["--component", "part_body.step.py", "--record-review", str(review)], calls)
            self.assertEqual(code, 0)
            self.assertEqual(self._state(project)["reviewer_id"], self.FIRST)

    def test_without_a_binding_runtime_the_reviewer_stays_a_name(self):
        with mock.patch.dict("os.environ", {"WORKSHOP_REVIEWER_RUNTIME": ""}), \
                tempfile.TemporaryDirectory() as tmp:
            project = self._contract_root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self.assertTrue(self._review(module, project, summary, reviewer="fresh-reviewer")["ok"])
            self.assertNotIn("reviewer_id", self._state(project))


class ReferenceCameraRoundTest(unittest.TestCase):
    """ADR 0083: under a schema 3 Design Contract a component round compares
    each reference with the Component in its Display Pose, seen from the
    reference's Reference Camera; front, top and iso stay in the print stance."""

    _run_root = SealedReferenceTest._run_root
    _fake_run = SealedReferenceTest._fake_run
    _main = SealedReferenceTest._main
    _assembly = SealedReferenceTest._assembly
    REFS = ContractComponentReviewTest.REFS
    # The body prints on its back; its Display Pose stands it up.
    POSED = (
        "def gen_step():\n    return 'print-stance body %d'\n\n"
        "def assembly_pose(shape, pose):\n    return ('display-pose', shape, pose)\n"
    )
    MISMATCH = {"file": "ref-02-body.png", "reference": "the chest plate and both shoulder sockets face the camera",
                "model": "the flat back and the print brim face the camera"}

    def _contract(self, schema=3):
        references = [{"file": "ref-01-whole.png", "shows": "assembly"},
                      {"file": "ref-02-body.png", "shows": "geometry:body"}]
        if schema == 3:
            references[0]["camera"], references[1]["camera"] = [-60, 20], [90, 15]
        return {"design_contract": {"schema_version": schema, "title": "Broken God", "references": references}}

    def _root(self, tmp, schema=3, posed=True):
        project = self._run_root(tmp, self.REFS, context=self._contract(schema))
        self._edits = 0
        self._posed = posed
        return project

    def _component(self, module, project, calls, edit=True):
        if edit:
            self._edits += 1
            source = self.POSED if self._posed else "def gen_step():\n    return 'body %d'\n"
            (project / "part_body.step.py").write_text(source % self._edits)
        code = self._main(module, project, ["--component", "part_body.step.py"], calls)
        state_path = project / "measure/component-rounds/body/make-round-state.json"
        if not state_path.is_file():
            return code, None
        state = json.loads(state_path.read_text())
        return code, json.loads((project / ("measure/component-rounds/body/r%04d/summary.json" % state["round"])).read_text())

    def _mismatch(self, module, project, summary, **changes):
        review = {"round": summary["round"], "packet_sha256": summary["visual"]["packet_sha256"],
                  "reviewer": "fresh-reviewer-subagent", "reason": "The reference shows the front; the model its back.",
                  "camera_mismatch": dict(self.MISMATCH), **changes}
        path = project / "measure/review.json"
        path.write_text(json.dumps(review))
        return module.record_review(project, path, "part_body.step.py")

    def _renders(self, calls):
        return [c for c in calls if Path(c[1]).name == "render_review"]

    def test_the_comparison_shows_the_display_pose_at_the_reference_camera(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            stance, posed = self._renders(calls)
            # The print stance is rendered from the Component itself, at the named views only.
            self.assertEqual(Path(stance[2]).name, "part_body.step.py")
            self.assertFalse(any(arg.startswith("--view=") for arg in stance))
            # The comparison render is the Display Pose entry, at the Reference Camera.
            self.assertEqual(Path(posed[2]).name, "display_pose_body.step.py")
            self.assertIn("--view=90,15", posed)
            self.assertEqual(Path(posed[posed.index("-o") + 1]).name, "display-pose")
            out = Path(summary["out"])
            self.assertTrue((out / "visual/display-pose/az90_el15.png").is_file())
            self.assertFalse((out / "visual/az90_el15.png").exists())
            self.assertEqual(summary["reference_cameras"], [
                {"label": "geometry:body", "file": "ref-02-body.png", "camera": [90.0, 15.0], "amended_from": None}])
            self.assertTrue(summary["refs"][0][1].endswith("ref-02-body.png@90,15"))
            self.assertIn("Display Pose", summary["visual"]["detail"])
            self.assertIn("camera geometry:body ref-02-body.png at 90,15 in the Display Pose",
                          module.render_summary(summary))
            # The generated entry renders assembly_pose(shape, None) of the Component's own build.
            entry = runpy_entry(Path(posed[2]))
            self.assertEqual(entry["gen_step"](), ("display-pose", "print-stance body 1", None))

    def test_a_geometry_with_instances_shows_its_first_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            self.POSED = (
                "def gen_step(instance=1):\n    return 'wing %%d of %d' %% instance\n\n"
                "def assembly_pose(shape, pose, instance=1):\n    return ('display-pose', shape, pose, instance)\n"
            )
            self._component(module, project, calls)
            entry = runpy_entry(Path(self._renders(calls)[1][2]))
            self.assertEqual(entry["gen_step"](), ("display-pose", "wing 1 of 1", None, 1))

    def test_a_component_without_assembly_pose_is_refused_before_any_render(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp, posed=False)
            module, calls = load_module(), []
            code, summary = self._component(module, project, calls)
            self.assertEqual(code, 2)
            self.assertIsNone(summary)
            self.assertEqual(calls, [])
            self.assertIn("defines no assembly_pose(shape, pose)", self.stderr)
            self.assertFalse((project / "measure/component-rounds/body/r0001").exists())

    def test_before_schema_3_the_comparison_keeps_the_print_stance_from_the_front(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp, schema=2, posed=False)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self.assertEqual(len(self._renders(calls)), 1)
            self.assertNotIn("reference_cameras", summary)
            self.assertFalse(summary["refs"][0][1].endswith("@90,15"))
            with self.assertRaisesRegex(ValueError, "this round has none"):
                self._mismatch(module, project, summary)

    def test_the_assembly_reference_is_shown_from_its_reference_camera(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            self._main(module, project, [], calls)
            render = self._renders(calls)[0]
            self.assertIn("--view=-60,20", render)
            self.assertTrue(self._assembly(project)["refs"][0][1].endswith("ref-01-whole.png@-60,20"))

    def test_a_camera_mismatch_needs_landmarks_and_one_compared_reference(self):
        cases = {
            "no landmarks": ({"camera_mismatch": {"file": "ref-02-body.png"}}, "needs file, reference and model"),
            "empty landmark": ({"camera_mismatch": {**self.MISMATCH, "model": " "}}, "names the landmarks"),
            "not compared": ({"camera_mismatch": {**self.MISMATCH, "file": "ref-01-whole.png"}},
                             "names one reference this round compared"),
            "with agrees": ({"agrees": False}, "camera_mismatch"),
            "with differences": ({"differences": []}, "camera_mismatch"),
        }
        for name, (changes, refusal) in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                project = self._root(tmp)
                module, calls = load_module(), []
                _, summary = self._component(module, project, calls)
                with self.assertRaisesRegex(ValueError, refusal):
                    self._mismatch(module, project, summary, **changes)

    def test_a_camera_mismatch_is_a_need_not_a_shape_round_or_repair_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            result = self._mismatch(module, project, summary)
            self.assertFalse(result["ok"])
            self.assertIsNone(result["review"])
            self.assertEqual(result["visual"]["status"], "camera-mismatch")
            mismatch = result["camera_mismatch"]
            self.assertEqual((mismatch["file"], mismatch["camera"]), ("ref-02-body.png", [90.0, 15.0]))
            self.assertIn("--reference-camera ref-02-body.png=AZ,EL", mismatch["need"])
            self.assertIn("the flat back and the print brim", mismatch["need"])
            self.assertIn("CAMERA MISMATCH", module.render_summary(result))
            out = Path(result["out"])
            # The worker reads review.json; a camera mismatch gives it nothing to repair.
            self.assertFalse((out / "review.json").exists())
            self.assertTrue((out / "camera-mismatch.json").is_file())
            state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
            self.assertEqual((state["policy"]["phase"], state["policy"]["shape_rounds"]), ("awaiting-review", 0))
            with self.assertRaisesRegex(ValueError, "already has a recorded camera mismatch"):
                self._mismatch(module, project, summary)
            # A geometry change is still refused: the round awaits its review.
            code, _ = self._component(module, project, calls)
            self.assertEqual(code, 2)
            self.assertIn("has no Component Review", self.stderr)

    def test_an_amended_camera_is_shown_on_an_unchanged_rerun(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, first = self._component(module, project, calls)
            self._mismatch(module, project, first)
            (module.run_root(project) / "CONTRACT-AMENDMENTS.json").write_text(json.dumps(
                {"schema_version": 1, "reference_cameras": {"ref-02-body.png": [-90, 15]}}))
            calls.clear()
            code, summary = self._component(module, project, calls, edit=False)
            self.assertEqual((code, summary["round"], summary["shape_round"], summary["shape_rounds"]), (1, 2, False, 0))
            self.assertIn("--view=-90,15", self._renders(calls)[1])
            self.assertEqual(summary["reference_cameras"][0]["amended_from"], [90.0, 15.0])
            self.assertEqual(summary["reference_cameras"][0]["camera"], [-90.0, 15.0])
            self.assertNotEqual(summary["carry_key"], first["carry_key"])
            self.assertIn("amended from 90,15", module.render_summary(summary))
            self.assertTrue(module.record_review(project, write_review(project, summary), "part_body.step.py")["ok"])


def runpy_entry(path):
    """Run a generated entry's module code, as render_review loads it."""
    import runpy

    return runpy.run_path(str(path))


def params(width):
    """A cited, asserted Shared Helper value (ADR 0082)."""
    return "BODY_W = %d  # wiki: joints-and-fits\nassert BODY_W >= 20\n" % width


class InterfaceTest(unittest.TestCase):
    """ADR 0082: Shared Helpers are frozen on tested samples, a separable
    Interface keeps a Keep-out Envelope in each component round, and a
    Coupled Interface is checked on its locked Components."""

    _run_root = SealedReferenceTest._run_root
    REFS = {"ref-01-whole.png": b"whole", "ref-02-body.png": b"body", "ref-03-arm.png": b"arm"}
    ENVELOPE = {"inside": "arm", "outside": "body", "shapes": [
        {"pose": "folded", "box": {"min_mm": [0, 0, 0], "max_mm": [40, 10, 6]}},
        {"pose": "spread", "cylinder": {"base_mm": [0, 0, 0], "axis": [0, 0, 1], "radius_mm": 42, "height_mm": 6}},
    ]}
    INTERFACES = [
        {"id": "arm-peg", "kind": "static", "components": ["body", "arm"]},
        {"id": "arm-swing", "kind": "separable", "components": ["arm", "body"], "envelope": ENVELOPE},
        {"id": "gear-mesh", "kind": "coupled", "components": ["body", "arm"], "yielding": "arm",
         "poses": {"steps": 8, "movers": [
             {"component": "arm", "rotation": {"axis_point": [0, 0, 0], "axis_direction": [0, 0, 1],
                                               "start_deg": 0, "end_deg": 90}, "driven": True}]}},
    ]

    def _contract(self, interfaces=None):
        return {"design_contract": {
            "schema_version": 2, "title": "Broken God",
            "references": [{"file": "ref-01-whole.png", "shows": "assembly"},
                           {"file": "ref-02-body.png", "shows": "geometry:body"},
                           {"file": "ref-03-arm.png", "shows": "geometry:arm"}],
            "interfaces": self.INTERFACES if interfaces is None else interfaces,
        }}

    def _project(self, tmp, interfaces=None, freeze=True):
        project = self._run_root(tmp, self.REFS, context=self._contract(interfaces))
        (project / "features").mkdir()
        (project / "params.py").write_text(params(40))
        (project / "features/__init__.py").write_text("")
        # skills_root() is the project here: the wiki the citations name.
        (project / "wiki/pages/printing").mkdir(parents=True)
        (project / "wiki/pages/printing/joints-and-fits.md").write_text("# Joints and fits\n")
        (project / "features/joints.py").write_text("PEG_D = 4.0  # wiki: joints-and-fits\nassert PEG_D >= 3\n")
        (project / "part_body.step.py").write_text(
            "import params\nfrom features.joints import PEG_D\ndef gen_step(): return 'body'\n")
        (project / "part_arm.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return 'arm'\n")
        (project / "samples").mkdir()
        (project / "samples/peg_in_socket.step.py").write_text(
            "from features.joints import PEG_D\ndef gen_step(): return 'peg'\n")
        self.faults = {}
        self.calls = []
        self.module = load_module()
        if freeze:
            self.assertEqual(self._main(project, ["--shared-helpers"]), 0, self.stderr)
        return project

    def _fake(self, command, **kwargs):
        tool = Path(command[1]).name
        self.calls.append((command, kwargs))
        faults = self.faults
        if tool == "gen":
            source = Path(command[2])
            source.with_name(source.name[:-len(".py")]).write_bytes(source.read_bytes())
        if tool == "render_review":
            return fake_render_review(command)
        if tool in ("check_thickness", "check_overhang"):
            fails = tool == "check_thickness" and Path(command[2]).name in faults.get("wall", ())
            stdout, code = _gate_output(tool, fails=fails)
            log = kwargs.get("log")
            if log is not None:
                Path(log).write_text(stdout, encoding="utf-8")
            return subprocess.CompletedProcess(command, code, stdout, "")
        if tool == "check_mesh":
            # Issue #108: the mesh validity gate, in check_mesh's own words.
            name = Path(command[2]).name
            if name in faults.get("mesh", ()):
                stdout = ("%s: 24 triangles, 14 vertices\n"
                          "  PASS  watertight (no open edges)         0 boundary edges\n"
                          "  FAIL  manifold edges                     1 edges shared by >2 faces (up to 4)\n"
                          "        1. [edge ] (10.00, 10.00, 0.00) - (10.00, 10.00, 10.00)  4 faces\n"
                          "RESULT: NOT PRINTABLE AS-IS\n" % name), 1
            else:
                stdout = ("%s: 12 triangles, 8 vertices\n"
                          "  PASS  manifold edges                     0 edges shared by >2 faces\n"
                          "RESULT: printable\n" % name), 0
            log = kwargs.get("log")
            if log is not None:
                Path(log).write_text(stdout[0], encoding="utf-8")
            return subprocess.CompletedProcess(command, stdout[1], stdout[0], "")
        if tool == "check_envelope":
            role = command[command.index("--role") + 1]
            name = Path(command[2]).name
            if "--instance" in command:
                name += "#" + command[command.index("--instance") + 1]
            ok = name not in faults.get("envelope", ())
            pose = "spread" if role == "inside" else "folded"
            payload = {"ok": ok, "role": role, "poses": [{"pose": pose, "status": "pass" if ok else "fail"}],
                       "detail": "2 pose(s) keep to the %s" % role if ok else
                       ("12.5 mm3 lies outside the envelope in pose spread" if role == "inside"
                        else "8.0 mm3 enters the envelope of pose folded")}
            return subprocess.CompletedProcess(command, 0 if ok else 1, json.dumps(payload) + "\n", "")
        if tool == "inspect":
            # Issue #108: interference at the assembly placement.
            clash = faults.get("interfere")
            payload = {"ok": not clash, "entry": command[3], "tolerance": 1.0, "errors": [],
                       "clashCount": 1 if clash else 0,
                       "clashes": [{"a": {"ref": "o1.1", "name": "body"}, "b": {"ref": "o1.2", "name": "arm"},
                                    "volume": 3.25}] if clash else [],
                       "stats": {"pairs_tested": 1}}
            Path(kwargs["log"]).write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.CompletedProcess(command, 2 if clash else 0, json.dumps(payload), "")
        if tool == "check_motion":
            status = faults.get("motion", "pass")
            manifest = json.loads(Path(command[command.index("--manifest") + 1]).read_text())
            failing = faults.get("motion_fail_ids", ())
            payload = {"ok": status == "pass" and not failing, "results": [
                {"id": "gear-mesh", "status": status,
                 "detail": "clear" if status == "pass" else "collision at step 3 between arm and body (2.1 mm3)"}]}
            for condition in manifest["conditions"][1:]:
                failed = condition["id"] in failing
                payload["results"].append({"id": condition["id"], "status": "fail" if failed else "pass",
                                           "detail": "blocked at step 2 by body (4.0 mm3)" if failed else "clear"})
            # run() always leaves the tool's log; the unlock cites its hash.
            Path(kwargs["log"]).write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.CompletedProcess(command, 0 if payload["ok"] else 1, json.dumps(payload), "")
        return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")

    def _main(self, project, argv):
        with contextlib.redirect_stdout(io.StringIO()) as stdout, contextlib.redirect_stderr(io.StringIO()) as stderr, \
                mock.patch.object(self.module, "skills_root", return_value=project), \
                mock.patch.object(self.module, "run", side_effect=self._fake):
            code = self.module.main([str(project), *argv])
        self.stdout, self.stderr = stdout.getvalue(), stderr.getvalue()
        return code

    def _component(self, project, role):
        code = self._main(project, ["--component", "part_%s.step.py" % role])
        state = json.loads((project / ("measure/component-rounds/%s/make-round-state.json" % role)).read_text())
        return code, json.loads((Path(state["last_out"]) / "summary.json").read_text())

    def _lock(self, project, role):
        code, summary = self._component(project, role)
        self.assertEqual(code, 1, self.stderr)
        review = write_review(project, summary)
        self.assertEqual(self._main(project, ["--component", "part_%s.step.py" % role, "--record-review", str(review)]), 0)
        return summary

    def _freeze(self, project):
        return json.loads((project / "measure/shared-helpers-freeze.json").read_text())

    # -- the Shared Helper check and freeze

    def test_passing_samples_freeze_the_shared_helpers_by_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            freeze = self._freeze(project)
            # (cad/scripts holds this fixture's stand-in tool bytes, not a run's.)
            self.assertEqual(sorted(path for path in freeze["helpers"] if not path.startswith("cad/")),
                             ["features/__init__.py", "features/joints.py", "params.py"])
            self.assertEqual(freeze["helpers"]["params.py"], hashlib.sha256(params(40).encode()).hexdigest())
            self.assertEqual(list(freeze["samples"]), ["peg_in_socket"])
            summary = json.loads((project / "measure/helper-rounds/r0001/summary.json").read_text())
            self.assertEqual(freeze["summary_sha256"], hashlib.sha256(
                (project / "measure/helper-rounds/r0001/summary.json").read_bytes()).hexdigest())
            self.assertTrue(summary["frozen"])
            self.assertEqual(summary["samples"]["peg_in_socket"]["imports"], ["features/__init__.py", "features/joints.py"])
            # A sample imports the Shared Helpers from the project root.
            gen = next(kwargs for command, kwargs in self.calls if Path(command[1]).name == "gen")
            self.assertEqual(gen["extra_env"]["PYTHONPATH"].split(os.pathsep)[0], str(project))
            gates = [Path(command[1]).name for command, _ in self.calls]
            self.assertEqual(gates, ["gen", "check_thickness", "check_overhang"])

    def test_a_sample_that_fails_a_print_gate_freezes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            self.faults["wall"] = {"peg_in_socket.step.py"}
            self.assertEqual(self._main(project, ["--shared-helpers"]), 1)
            self.assertFalse((project / "measure/shared-helpers-freeze.json").exists())
            self.assertIn("sample FAIL peg_in_socket", self.stdout)

    def test_a_contract_with_interfaces_needs_a_sample(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            (project / "samples/peg_in_socket.step.py").unlink()
            self.assertEqual(self._main(project, ["--shared-helpers"]), 2)
            self.assertIn("no sample", self.stderr)
            (project / "samples/peg_in_socket.step.py").write_text("def gen_step(): return 'peg'\n")
            self.assertEqual(self._main(project, ["--shared-helpers"]), 1)
            self.assertIn("imports no Shared Helper", self.stdout)

    # -- the Shared Helper rules: wiki citation, assert, standard elements

    def _rules(self, project, helper_text, path="features/joints.py"):
        (project / path).write_text(helper_text)
        code = self._main(project, ["--shared-helpers"])
        return code, self.stderr

    def test_an_uncited_unasserted_or_unknown_page_value_freezes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            code, stderr = self._rules(project, (
                "PEG_D = 4.0\n"
                "PEG_CLEAR = 0.2  # wiki: joints-and-fits\n"
                "SOCKET_D = 5  # wiki: no-such-page\n"
                "assert PEG_D >= 3 and SOCKET_D > 4\n"))
            self.assertEqual(code, 1)
            self.assertIn("features/joints.py:1 PEG_D cites no wiki page", stderr)
            self.assertIn("features/joints.py:2 PEG_CLEAR is in no assert", stderr)
            self.assertIn("features/joints.py:3 SOCKET_D cites no-such-page, which is not a page", stderr)
            self.assertNotIn("PEG_D is in no assert", stderr)
            # Checked before anything is built or frozen.
            self.assertEqual(self.calls, [])
            self.assertFalse((project / "measure/shared-helpers-freeze.json").exists())

    def test_a_citation_above_a_value_and_a_derived_value_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            code, stderr = self._rules(project, (
                "# Running fit for a 4 mm peg.\n"
                "# wiki: joints-and-fits#clearance\n"
                "PEG_D, PEG_CLEAR = 4.0, 0.2\n"
                "SOCKET_D = PEG_D + 2 * PEG_CLEAR\n"
                "AXIS: tuple = (0, 0, 1)  # wiki: printing/joints-and-fits\n"
                "assert PEG_D >= 3 and PEG_CLEAR >= 0.15 and AXIS[2] == 1\n"))
            self.assertEqual(code, 0, stderr)

    def test_a_hand_written_standard_element_or_involute_freezes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            code, stderr = self._rules(project, "def spur_gear(teeth):\n    return teeth\n")
            self.assertEqual(code, 1)
            self.assertIn("features/joints.py:1 spur_gear builds a standard element by hand", stderr)
            library = "from py_gearworks import SpurGear\ndef pinion(teeth):\n    return SpurGear(teeth)\n"
            self.assertEqual(self._rules(project, library)[0], 0, self.stderr)
            code, stderr = self._rules(project, library + "def involute_point(r, t):\n    return r * t\n")
            self.assertEqual(code, 1)
            self.assertIn("involute_point writes an involute by hand", stderr)

    def test_a_helper_no_component_or_sample_imports_is_not_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            (project / "features/scratch.py").write_text("LOOSE = 3\n")
            self.assertEqual(self._main(project, ["--shared-helpers"]), 0, self.stderr)

    def test_the_installed_print_details_library_is_exempt_only_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            library = b"RIVET_D = 1.2\ndef rivet(): return RIVET_D\n"
            (project / "print-details/scripts").mkdir(parents=True)
            (project / "print-details/scripts/print_details.py").write_bytes(library)
            (project / "features/print_details.py").write_bytes(library)
            (project / "part_arm.step.py").write_text(
                "from features.joints import PEG_D\nfrom features.print_details import rivet\n"
                "def gen_step(): return 'arm'\n")
            self.assertEqual(self._main(project, ["--shared-helpers"]), 0, self.stderr)
            self.assertIn("features/print_details.py", self._freeze(project)["helpers"])
            (project / "features/print_details.py").write_bytes(library + b"# tuned\n")
            self.assertEqual(self._main(project, ["--shared-helpers"]), 1)
            self.assertIn("features/print_details.py differs from the print-details library", self.stderr)

    def test_a_component_round_before_the_freeze_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            self.assertEqual(self._main(project, ["--component", "part_body.step.py"]), 2)
            self.assertIn("not frozen", self.stderr)
            self.assertFalse((project / "measure/component-rounds/body/r0001").exists())
            self.assertEqual(self._main(project, ["--shared-helpers"]), 0)
            code, summary = self._component(project, "body")
            self.assertEqual((code, summary["checks_ok"]), (1, True))
            self.assertEqual(summary["helper_freeze"], {"round": 1, "changed": [], "affected": {}})

    def test_a_contract_without_an_interfaces_section_keeps_the_protocol_without_a_freeze(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            wish = json.loads((project.parents[4] / "WISH.json").read_text())
            del wish["context"]["design_contract"]["interfaces"]
            (project.parents[4] / "WISH.json").write_text(json.dumps(wish))
            code, summary = self._component(project, "body")
            self.assertEqual(code, 1)
            self.assertNotIn("helper_freeze", summary)
            self.assertNotIn("envelopes", summary)

    def test_a_changed_frozen_helper_is_reported_with_the_components_that_import_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            (project / "params.py").write_text(params(42))
            code, summary = self._component(project, "arm")
            self.assertEqual(summary["helper_freeze"]["changed"], [])  # the arm does not import params.py
            code, summary = self._component(project, "body")
            self.assertEqual(summary["helper_freeze"], {"round": 1, "changed": ["params.py"],
                                                        "affected": {"params.py": ["body"]}})
            self.assertIn("frozen params.py changed since the freeze of r0001; imported by body",
                          self.module.render_summary(summary))
            # Detection, not a block: the round ran and passed its checks.
            self.assertTrue(summary["checks_ok"])
            (project / "features/joints.py").write_text("PEG_D = 4.2  # wiki: joints-and-fits\nassert PEG_D >= 3\n")
            self.assertEqual(self._main(project, ["--shared-helpers"]), 0)
            event = [json.loads(line) for line in
                     (project / "measure/shared-helper-freezes.jsonl").read_text().splitlines()][-1]
            self.assertEqual(event, {"round": 2, "refreeze_of": 1, "changed": ["features/joints.py", "params.py"],
                                     "affected": {"features/joints.py": ["arm", "body"], "params.py": ["body"]}})
            self.assertIn("refreeze params.py changed since r0001; imported by body", self.stdout)
            self.assertEqual(self._freeze(project)["round"], 2)

    # -- Keep-out Envelopes

    def test_each_side_of_a_separable_interface_checks_its_envelope_in_its_own_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self.calls.clear()
            code, summary = self._component(project, "arm")
            command = next(command for command, _ in self.calls if Path(command[1]).name == "check_envelope")
            self.assertEqual(command[command.index("--role") + 1], "inside")
            sealed = json.loads(Path(command[command.index("--envelope") + 1]).read_text())
            self.assertEqual(sealed, self.ENVELOPE)
            self.assertEqual(summary["envelopes"]["arm-swing"]["verdict"], "PASS")
            self.assertTrue(summary["checks_ok"])
            self.calls.clear()
            _, summary = self._component(project, "body")
            command = next(command for command, _ in self.calls if Path(command[1]).name == "check_envelope")
            self.assertEqual(command[command.index("--role") + 1], "outside")
            self.assertIn("keep  PASS arm-swing", self.module.render_summary(summary))

    def test_an_inside_component_leaving_its_envelope_in_one_pose_fails_its_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self.faults["envelope"] = {"part_arm.step.py"}
            code, summary = self._component(project, "arm")
            self.assertEqual(code, 1)
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["visual"]["status"], "not-rendered")
            self.assertEqual(summary["envelopes"]["arm-swing"]["verdict"], "FAIL")
            self.assertIn("keep  FAIL arm-swing      inside: 12.5 mm3 lies outside the envelope in pose spread",
                          self.module.render_summary(summary))

    def test_an_outside_component_entering_the_envelope_fails_its_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self.faults["envelope"] = {"part_body.step.py"}
            _, summary = self._component(project, "body")
            self.assertFalse(summary["checks_ok"])
            self.assertIn("enters the envelope", summary["envelopes"]["arm-swing"]["detail"])
            _, summary = self._component(project, "arm")
            self.assertTrue(summary["checks_ok"])

    # -- mesh validity in the component round (issue #108)

    def test_a_component_round_runs_the_mesh_gate_beside_the_print_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self.calls.clear()
            code, summary = self._component(project, "body")
            self.assertEqual((code, summary["checks_ok"]), (1, True))
            self.assertEqual(summary["print"]["body"]["mesh"]["verdict"], "PASS")
            mesh = [command for command, _ in self.calls if Path(command[1]).name == "check_mesh"]
            self.assertEqual(len(mesh), 1)
            self.assertEqual(Path(mesh[0][2]).name, "part_body.step.py")
            self.assertIn("--bed", mesh[0])
            self.assertIn("mesh  PASS body", self.module.render_summary(summary))

    def test_a_non_manifold_component_fails_its_round_and_names_the_edges(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self.faults["mesh"] = {"part_body.step.py"}
            code, summary = self._component(project, "body")
            self.assertEqual(code, 1)
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["visual"]["status"], "not-rendered")
            mesh = summary["print"]["body"]["mesh"]
            self.assertEqual(mesh["verdict"], "FAIL")
            self.assertEqual(mesh["edges"], ["(10.00, 10.00, 0.00) - (10.00, 10.00, 10.00)  4 faces"])
            self.assertEqual(summary["print"]["body"]["verdict"], "FAIL")
            text = self.module.render_summary(summary)
            self.assertIn("mesh  FAIL body", text)
            self.assertIn("non-manifold edge (10.00, 10.00, 0.00) - (10.00, 10.00, 10.00)", text)
            # A failed mesh is never reused as print evidence.
            self.assertFalse(self.module.reusable_print(summary["print"]["body"]))
            # The repair passes.
            self.faults["mesh"] = set()
            (project / "part_body.step.py").write_text(
                "import params\nfrom features.joints import PEG_D\ndef gen_step(): return 'body 2'\n")
            code, summary = self._component(project, "body")
            self.assertTrue(summary["checks_ok"])

    def test_a_change_to_the_inside_component_does_not_stale_the_outside_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._lock(project, "body")
            body_step = hashlib.sha256((project / "part_body.step").read_bytes()).hexdigest()
            (project / "part_arm.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return 'arm 2'\n")
            self._component(project, "arm")
            _summary, reason = self.module.current_passing_component_round(project, "body", body_step)
            self.assertEqual(reason, "")

    # -- Coupled Interface checks

    def _locked_pair(self, project):
        self._lock(project, "body")
        self._lock(project, "arm")

    def test_an_interface_check_is_refused_while_a_component_it_joins_is_unlocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._lock(project, "body")
            self._component(project, "arm")
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 2)
            self.assertIn("judges locked geometry only", self.stderr)
            self.assertIn("part_arm.step.py", self.stderr)
            self.assertFalse((project / "measure/interface-rounds/gear-mesh/r0001").exists())

    def test_only_a_coupled_interface_has_an_interface_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            for interface_id, why in (("arm-swing", "Keep-out Envelope"), ("arm-peg", "static"), ("tail", "no Interface")):
                self.assertEqual(self._main(project, ["--interface", interface_id]), 2)
                self.assertIn(why, self.stderr)

    def test_a_passing_check_runs_the_sealed_pose_table_on_just_its_components(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._locked_pair(project)
            self.calls.clear()
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 0, self.stderr)
            out = project / "measure/interface-rounds/gear-mesh/r0001"
            manifest = json.loads((out / "motion.json").read_text())
            self.assertEqual(manifest["assembly"], "measure/interface-rounds/gear-mesh/r0001/interface_gear_mesh.step.py")
            condition = manifest["conditions"][0]
            self.assertEqual(condition["check"], "coupled_motion_collision")
            self.assertEqual(condition["inputs"]["movers"][0]["part"], "arm")
            self.assertEqual(condition["inputs"]["obstacle_parts"], ["body"])
            self.assertIn("COMPONENTS = ['body', 'arm']", (out / "interface_gear_mesh.step.py").read_text())
            summary = json.loads((out / "summary.json").read_text())
            self.assertTrue(summary["ok"])
            self.assertIsNone(summary["unlocked"])
            self.assertEqual(summary["identities"]["body"],
                             hashlib.sha256((project / "part_body.step").read_bytes()).hexdigest())
            tools = [Path(command[1]).name for command, _ in self.calls]
            self.assertEqual(tools, ["gen", "gen", "inspect", "check_motion"])

    # -- interference and insertion order in the interface check (issue #108)

    INSERTION = {"assembly": "toy.step.py", "conditions": [
        {"id": "arm-inserts", "check": "linear_motion_collision", "expect": "clear",
         "inputs": {"moving_part": "arm", "obstacle_parts": ["body"], "translation": [0, 0, 20], "steps": 8,
                    "allow_seated_contact": True}},
        {"id": "arm-then-tail", "check": "assembly_sequence", "inputs": {"steps": [
            {"check": "linear_motion_collision", "inputs": {"moving_part": "tail", "obstacle_parts": ["body"],
                                                            "translation": [0, 5, 0], "steps": 4}}]}},
        {"id": "body-spins", "check": "rotation_motion_collision",
         "inputs": {"moving_part": "body", "obstacle_parts": ["base"], "axis_point": [0, 0, 0],
                    "axis_direction": [0, 0, 1], "start_deg": 0, "end_deg": 30, "steps": 4}},
    ]}

    def test_an_interface_check_runs_interference_then_its_insertion_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            (project / "measure").mkdir(exist_ok=True)
            (project / "measure/motion.json").write_text(json.dumps(self.INSERTION))
            self._locked_pair(project)
            self.calls.clear()
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 0, self.stderr)
            out = project / "measure/interface-rounds/gear-mesh/r0001"
            tools = [Path(command[1]).name for command, _ in self.calls]
            self.assertEqual(tools, ["gen", "gen", "inspect", "check_motion"])
            inspect = next(command for command, _ in self.calls if Path(command[1]).name == "inspect")
            self.assertEqual(inspect[2:4], ["interfere", "measure/interface-rounds/gear-mesh/r0001/interface_gear_mesh.step.py"])
            manifest = json.loads((out / "motion.json").read_text())
            # Only the insertion paths that move this Interface's Components
            # among themselves join its check; the others stay for assembly.
            self.assertEqual([c["id"] for c in manifest["conditions"]], ["gear-mesh", "arm-inserts"])
            self.assertEqual(manifest["conditions"][1], self.INSERTION["conditions"][0])
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual(summary["interference"]["verdict"], "pass")
            self.assertEqual(summary["insertion"], ["arm-inserts"])
            text = self.stdout
            self.assertIn("clash PASS", text)
            self.assertIn("insert arm-inserts", text)

    def test_interference_between_its_components_fails_the_check_and_unlocks_the_yielding_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._locked_pair(project)
            self.faults["interfere"] = True
            self.calls.clear()
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 1)
            out = project / "measure/interface-rounds/gear-mesh/r0001"
            summary = json.loads((out / "summary.json").read_text())
            self.assertFalse(summary["ok"])
            self.assertEqual(summary["interference"]["verdict"], "fail")
            self.assertIn("body x arm 3.25 mm3", summary["interference"]["detail"])
            # A clash stops the check before its motion sweep.
            self.assertNotIn("check_motion", [Path(command[1]).name for command, _ in self.calls])
            self.assertEqual(summary["motion"]["verdict"], "not-run")
            self.assertEqual(summary["unlocked"], "arm")
            arm = json.loads((project / "measure/component-rounds/arm/make-round-state.json").read_text())
            unlock = arm["policy"]["unlocks"][-1]
            self.assertEqual((unlock["kind"], unlock["interface"]), ("interface", "gear-mesh"))
            self.assertIn("interference", unlock["reason"])
            self.assertEqual(unlock["evidence"]["interference_log_sha256"],
                             hashlib.sha256((out / "interference.log").read_bytes()).hexdigest())
            self.assertIn("clash FAIL", self.stdout)
            interfaces, _ = self.module.contract_interfaces(project)
            self.assertEqual(self.module.interface_failures(project, interfaces, summary["identities"]),
                             ["interface gear-mesh failed its latest --interface check"])

    def test_a_blocked_insertion_path_fails_the_check_and_unlocks_the_yielding_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            (project / "measure").mkdir(exist_ok=True)
            (project / "measure/motion.json").write_text(json.dumps(self.INSERTION))
            self._locked_pair(project)
            self.faults["motion_fail_ids"] = {"arm-inserts"}
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 1)
            summary = json.loads((project / "measure/interface-rounds/gear-mesh/r0001/summary.json").read_text())
            self.assertFalse(summary["ok"])
            self.assertEqual(summary["interference"]["verdict"], "pass")
            self.assertIn("arm-inserts=fail", summary["motion"]["detail"])
            arm = json.loads((project / "measure/component-rounds/arm/make-round-state.json").read_text())
            unlock = arm["policy"]["unlocks"][-1]
            self.assertIn("insertion", unlock["reason"])
            self.assertIn("blocked at step 2", unlock["evidence"]["detail"])

    def test_a_failed_check_unlocks_only_the_yielding_component_with_its_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._locked_pair(project)
            self.faults["motion"] = "fail"
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 1)
            self.assertIn("unlock part_arm.step.py", self.stdout)
            arm = json.loads((project / "measure/component-rounds/arm/make-round-state.json").read_text())
            body = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
            self.assertEqual(body["policy"]["unlocks"], [])
            unlock = arm["policy"]["unlocks"][-1]
            self.assertEqual((unlock["kind"], unlock["interface"], unlock["interface_round"]), ("interface", "gear-mesh", 1))
            self.assertIn("collision at step 3", unlock["evidence"]["detail"])
            self.assertEqual(unlock["evidence"]["motion_log_sha256"], hashlib.sha256(
                (project / "measure/interface-rounds/gear-mesh/r0001/motion.log").read_bytes()).hexdigest())
            # The repair is admitted and is not a Shape Round; it is reviewed again.
            (project / "part_arm.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return 'arm 2'\n")
            code, summary = self._component(project, "arm")
            self.assertEqual((code, summary["shape_round"], summary["shape_rounds_used"], summary["phase"]),
                             (1, False, 0, "awaiting-review"))
            self.assertIn("unlock interface gear-mesh r0001", self.module.render_summary(summary))
            # The body stays locked: a change there is still refused.
            (project / "part_body.step.py").write_text("import params\nfrom features.joints import PEG_D\ndef gen_step(): return 'body 2'\n")
            self.assertEqual(self._main(project, ["--component", "part_body.step.py"]), 2)

    def test_assembly_needs_a_current_passing_check_of_every_coupled_interface(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._locked_pair(project)
            self.assertEqual(self._main(project, ["--require-component-passes"]), 1)
            self.assertIn("interface gear-mesh has no --interface check", self.stderr)
            self.faults["motion"] = "fail"
            self._main(project, ["--interface", "gear-mesh"])
            self.assertEqual(self._main(project, ["--require-component-passes"]), 1)
            self.assertIn("interface gear-mesh failed its latest --interface check", self.stderr)
            # The yielding arm repairs and is reviewed again; the old pass is stale.
            self.faults["motion"] = "pass"
            (project / "part_arm.step.py").write_text("from features.joints import PEG_D\ndef gen_step(): return 'arm 2'\n")
            self._lock(project, "arm")
            self.assertEqual(self._main(project, ["--require-component-passes"]), 1)
            self.assertIn("interface gear-mesh failed", self.stderr)
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 0)
            self.assertNotEqual(self._main(project, ["--require-component-passes"]), 2)
            self.assertNotIn("interface gear-mesh", self.stderr)

    def test_a_later_change_to_a_component_makes_the_interface_result_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._locked_pair(project)
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 0)
            interfaces, _ = self.module.contract_interfaces(project)
            state = json.loads((project / "measure/interface-rounds/gear-mesh/make-round-state.json").read_text())
            current = dict(state["identities"])
            self.assertEqual(self.module.interface_failures(project, interfaces, current), [])
            self.assertEqual(self.module.interface_failures(project, interfaces, {**current, "body": "0" * 64}),
                             ["interface gear-mesh is stale: a Component it joins changed after its check"])
            # A reader that only hashes the STEP on disk sees the same geometry.
            steps = {role: hashlib.sha256((project / ("part_%s.step" % role)).read_bytes()).hexdigest()
                     for role in ("body", "arm")}
            state["identities"] = {"body": "brep-body", "arm": "brep-arm"}
            (project / "measure/interface-rounds/gear-mesh/make-round-state.json").write_text(json.dumps(state))
            self.assertEqual(self.module.interface_failures(project, interfaces, steps), [])

    # -- Geometry Sources (issue #110)

    NOT_GEOMETRY = {"measure/check_landmarks.py": "raise SystemExit(0)\n",
                    "measure/check_spec.py": "import params\nraise SystemExit(0)\n",
                    "measure/broken_god_spec.json": "{}\n", "notes/why.md": "# why\n",
                    "notes/scratch.py": "X = 1\n"}

    def _add(self, project, files):
        for relative, text in files.items():
            (project / relative).parent.mkdir(parents=True, exist_ok=True)
            (project / relative).write_text(text)

    def test_files_beside_the_geometry_leave_an_interface_check_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._locked_pair(project)
            self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 0, self.stderr)
            state_path = project / "measure/interface-rounds/gear-mesh/make-round-state.json"
            state = json.loads(state_path.read_text())
            self.assertEqual(sorted(state["sources"]), ["features/__init__.py", "features/joints.py", "params.py",
                                                        "part_arm.step.py", "part_body.step.py"])
            interfaces, _ = self.module.contract_interfaces(project)
            current = dict(state["identities"])
            self._add(project, self.NOT_GEOMETRY)
            self._add(project, {path: text + "# edited\n" for path, text in self.NOT_GEOMETRY.items()})
            self.assertEqual(self.module.interface_failures(project, interfaces, current), [])

    def test_an_edited_imported_helper_or_component_source_makes_an_interface_check_stale(self):
        for path in ("features/joints.py", "params.py", "part_arm.step.py"):
            with self.subTest(path=path), tempfile.TemporaryDirectory() as tmp:
                project = self._project(tmp)
                self._locked_pair(project)
                self.assertEqual(self._main(project, ["--interface", "gear-mesh"]), 0, self.stderr)
                state = json.loads((project / "measure/interface-rounds/gear-mesh/make-round-state.json").read_text())
                interfaces, _ = self.module.contract_interfaces(project)
                (project / path).write_text((project / path).read_text() + "# edited\n")
                # The same B-rep identities: only the Geometry Sources moved.
                self.assertEqual(self.module.interface_failures(project, interfaces, dict(state["identities"])),
                                 ["interface gear-mesh is stale: a Component it joins changed after its check"])

    def test_files_beside_the_geometry_leave_a_component_packet_current(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            _code, summary = self._component(project, "body")
            self.assertEqual(summary["visual"]["status"], "pending")
            self.assertIsNone(self.module.packet_error(summary["visual"], project, "body"))
            self._add(project, self.NOT_GEOMETRY)
            self.assertIsNone(self.module.packet_error(summary["visual"], project, "body"))
            (project / "features/joints.py").write_text("PEG_D = 4.2  # wiki: joints-and-fits\nassert PEG_D >= 3\n")
            self.assertEqual(self.module.packet_error(summary["visual"], project, "body"),
                             "stale CAD sources or design constraints")

    def test_files_beside_the_geometry_leave_the_assembly_packet_sources_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            before = self.module.source_hashes(project)
            self._add(project, self.NOT_GEOMETRY)
            self.assertEqual(self.module.source_hashes(project), before)
            (project / "features/joints.py").write_text("PEG_D = 4.2  # wiki: joints-and-fits\nassert PEG_D >= 3\n")
            self.assertNotEqual(self.module.source_hashes(project), before)

    def test_the_new_modes_take_no_component_or_assembly_options(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, freeze=False)
            for argv in (["--interface", "gear-mesh", "--component", "part_arm.step.py"],
                         ["--shared-helpers", "--require-component-passes"],
                         ["--shared-helpers", "--interface", "gear-mesh"]):
                with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                    self.module.main([str(project), *argv])


class InterfaceInstanceTest(unittest.TestCase):
    """Issue #80: an Interface may name one instance of a Unique Geometry,
    ``wing#1`` and ``wing#2``. Each instance is built and placed by the
    geometry's one Component file; locking, staleness and the unlock belong
    to that Component."""

    _run_root = SealedReferenceTest._run_root
    _fake = InterfaceTest._fake
    _main = InterfaceTest._main
    _component = InterfaceTest._component
    _lock = InterfaceTest._lock
    REFS = {**InterfaceTest.REFS, "ref-04-wing.png": b"wing"}
    MESH = {"id": "wing-sector-mesh", "kind": "coupled", "components": ["wing#1", "wing#2"], "yielding": "wing#2",
            "poses": {"steps": 8, "movers": [
                {"component": "wing#1", "rotation": {"axis_point": [16, 0, 198.8], "axis_direction": [1, 0, 0],
                                                     "start_deg": 0, "end_deg": 35}},
                {"component": "wing#2", "rotation": {"axis_point": [-16, 0, 198.8], "axis_direction": [1, 0, 0],
                                                     "start_deg": 0, "end_deg": -35}, "driven": True}]}}
    FOLD = {"id": "wing-fold", "kind": "separable", "components": ["wing#1", "wing#2"],
            "envelope": {"inside": "wing#2", "outside": "wing#1",
                         "shapes": [{"pose": "folded", "box": {"min_mm": [0, 0, 0], "max_mm": [40, 10, 6]}}]}}
    INTERFACES = [MESH, FOLD]
    WING = ("from features.joints import PEG_D\n"
            "def gen_step(instance=1): return 'wing %d' % instance\n"
            "def assembly_pose(shape, pose, instance): return shape\n")

    def _contract(self, interfaces=None):
        contract = InterfaceTest._contract(self, interfaces)
        contract["design_contract"]["references"].append({"file": "ref-04-wing.png", "shows": "geometry:wing"})
        return contract

    def _project(self, tmp, wing=None):
        project = InterfaceTest._project(self, tmp, freeze=False)
        (project / "part_wing.step.py").write_text(self.WING if wing is None else wing)
        self.assertEqual(self._main(project, ["--shared-helpers"]), 0, self.stderr)
        return project

    def test_two_instances_are_built_once_and_placed_as_distinct_labelled_children(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._lock(project, "wing")
            self.calls.clear()
            self.assertEqual(self._main(project, ["--interface", "wing-sector-mesh"]), 0, self.stderr)
            out = project / "measure/interface-rounds/wing-sector-mesh/r0001"
            self.assertIn("COMPONENTS = ['wing#1', 'wing#2']", (out / "interface_wing_sector_mesh.step.py").read_text())
            inputs = json.loads((out / "motion.json").read_text())["conditions"][0]["inputs"]
            self.assertEqual([mover["part"] for mover in inputs["movers"]], ["wing#1", "wing#2"])
            self.assertEqual(inputs["obstacle_parts"], [])
            summary = json.loads((out / "summary.json").read_text())
            self.assertEqual((summary["components"], summary["yielding"]), (["wing#1", "wing#2"], "wing#2"))
            self.assertEqual(list(summary["identities"]), ["wing"])
            self.assertIn("wing#1 + wing#2", self.stdout)
            # One Component, one build.
            self.assertEqual([Path(command[1]).name for command, _ in self.calls], ["gen", "inspect", "check_motion"])
            interfaces, _ = self.module.contract_interfaces(project)
            report = self.module.interface_report(project, interfaces, dict(summary["identities"]))
            self.assertEqual(report[0], {"id": "wing-sector-mesh", "kind": "coupled", "components": ["wing#1", "wing#2"],
                                         "check": "pass", "yielding": "wing#2", "round": 1})

    def test_the_check_is_refused_while_the_instances_component_is_unlocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._component(project, "wing")
            self.assertEqual(self._main(project, ["--interface", "wing-sector-mesh"]), 2)
            self.assertIn("judges locked geometry only", self.stderr)
            self.assertIn("part_wing.step.py", self.stderr)

    def test_a_failure_yielding_one_instance_unlocks_its_component_and_a_change_stales_the_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self._lock(project, "wing")
            self.faults["motion"] = "fail"
            self.assertEqual(self._main(project, ["--interface", "wing-sector-mesh"]), 1)
            self.assertIn("unlock part_wing.step.py", self.stdout)
            state = json.loads((project / "measure/component-rounds/wing/make-round-state.json").read_text())
            unlock = state["policy"]["unlocks"][-1]
            self.assertEqual((unlock["kind"], unlock["interface"], unlock["interface_round"]),
                             ("interface", "wing-sector-mesh", 1))
            self.assertEqual(unlock["evidence"]["motion_log_sha256"], hashlib.sha256(
                (project / "measure/interface-rounds/wing-sector-mesh/r0001/motion.log").read_bytes()).hexdigest())
            # The wing worker repairs, is reviewed, and the check passes again.
            (project / "part_wing.step.py").write_text(self.WING.replace("'wing %d'", "'wing v2 %d'"))
            self._lock(project, "wing")
            self.faults["motion"] = "pass"
            self.assertEqual(self._main(project, ["--interface", "wing-sector-mesh"]), 0, self.stderr)
            interfaces, _ = self.module.contract_interfaces(project)
            state = json.loads((project / "measure/interface-rounds/wing-sector-mesh/make-round-state.json").read_text())
            current = dict(state["identities"])
            self.assertEqual(self.module.interface_failures(project, interfaces, current), [])
            self.assertEqual(self.module.interface_failures(project, interfaces, {"wing": "0" * 64}),
                             ["interface wing-sector-mesh is stale: a Component it joins changed after its check"])

    def test_instances_on_both_sides_of_an_envelope_are_each_checked_in_one_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self.calls.clear()
            _code, summary = self._component(project, "wing")
            commands = [command for command, _ in self.calls if Path(command[1]).name == "check_envelope"]
            self.assertEqual(sorted((command[command.index("--role") + 1], command[command.index("--instance") + 1])
                                    for command in commands), [("inside", "2"), ("outside", "1")])
            self.assertEqual({key: (item["role"], item["component"], item["verdict"])
                              for key, item in summary["envelopes"].items()},
                             {"wing-fold wing#2": ("inside", "wing#2", "PASS"),
                              "wing-fold wing#1": ("outside", "wing#1", "PASS")})
            self.assertTrue(summary["checks_ok"])
            self.assertIn("keep  PASS wing-fold wing#1 outside", self.module.render_summary(summary))
        # One instance entering the other's envelope fails the round.
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp)
            self.faults["envelope"] = {"part_wing.step.py#1"}
            _code, summary = self._component(project, "wing")
            self.assertFalse(summary["checks_ok"])
            self.assertEqual(summary["envelopes"]["wing-fold wing#1"]["verdict"], "FAIL")
            self.assertEqual(summary["envelopes"]["wing-fold wing#2"]["verdict"], "PASS")

    def test_an_instance_needs_a_placement_hook_that_takes_the_instance_number(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._project(tmp, wing="from features.joints import PEG_D\n"
                                              "def gen_step(): return 'wing'\n"
                                              "def assembly_pose(shape, pose): return shape\n")
            self.calls.clear()
            _code, summary = self._component(project, "wing")
            self.assertFalse(summary["checks_ok"])
            self.assertNotIn("check_envelope", [Path(command[1]).name for command, _ in self.calls])
            self.assertIn("assembly_pose(shape, pose, instance)", summary["envelopes"]["wing-fold wing#1"]["detail"])
            self.assertEqual(self._main(project, ["--interface", "wing-sector-mesh"]), 2)
            self.assertIn("takes no instance; define assembly_pose(shape, pose, instance)", self.stderr)
            self.assertFalse((project / "measure/interface-rounds/wing-sector-mesh/r0001").exists())


class RoundPolicyTest(unittest.TestCase):
    """ADR 0081: admission, Shape Round counting and the lock, from inputs alone."""

    module = None

    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def reviewed(self, *, agrees, identity="A", accepted=False, helpers=None, key="kA", round_=3):
        return {"round": round_, "identity": identity, "carry_key": key, "agrees": agrees,
                "accepted": accepted, "imported_helpers": helpers or {}, "review": {"agrees": agrees},
                "acceptance": None}

    def decide(self, previous, identity, checks_ok=True, key=None, helpers=None):
        return self.module.round_policy(previous, {
            "identity": identity, "checks_ok": checks_ok, "carry_key": key or "k" + str(identity),
            "helpers": helpers or {}, "round": 9})

    def test_the_table(self):
        P = self.module
        awaiting = {"phase": P.AWAITING, "identity": "A", "round": 3, "shape_rounds": 2}
        disagreed = {"phase": P.DISAGREED, "identity": "A", "round": 3, "shape_rounds": 2,
                     "reviewed": self.reviewed(agrees=False)}
        locked = {"phase": P.LOCKED, "identity": "A", "round": 3, "shape_rounds": 2,
                  "reviewed": self.reviewed(agrees=True, helpers={"features/forms.py": "h1"})}
        accepted = {**locked, "shape_rounds": 5,
                    "reviewed": self.reviewed(agrees=False, accepted=True)}
        unlocked = {**locked, "unlocks": [{"kind": "assembly", "assembly_round": 4}]}
        # (name, previous, identity, checks_ok, helpers) -> (admit, shape round, phase, shape rounds, carried)
        cases = [
            ("first round", {}, "A", True, None, (True, False, P.AWAITING, 0, False)),
            ("first round fails", {}, "A", False, None, (True, False, P.OPEN, 0, False)),
            ("unreviewed pass, changed", awaiting, "B", True, None, (False, False, None, None, False)),
            ("unreviewed pass, build fails", awaiting, None, False, None, (False, False, None, None, False)),
            ("unreviewed pass, unchanged rerun", awaiting, "A", True, None, (True, False, P.AWAITING, 2, False)),
            ("disagreed, first change", disagreed, "B", True, None, (True, True, P.AWAITING, 3, False)),
            ("disagreed, first change fails print", disagreed, "B", False, None, (True, True, P.OPEN, 3, False)),
            ("disagreed, build fails", disagreed, None, False, None, (True, False, P.DISAGREED, 2, False)),
            ("disagreed, unchanged rerun", disagreed, "A", True, None, (True, False, P.DISAGREED, 2, True)),
            ("repair after the shape round", {"phase": P.OPEN, "identity": "B", "shape_rounds": 3},
             "C", True, None, (True, False, P.AWAITING, 3, False)),
            ("locked, changed", locked, "B", True, {"features/forms.py": "h1"}, (False, False, None, None, False)),
            ("locked, unchanged rerun", locked, "A", True, {"features/forms.py": "h1"}, (True, False, P.LOCKED, 2, True)),
            ("accepted, changed", accepted, "B", True, None, (False, False, None, None, False)),
            ("helper unlock, identical B-rep", locked, "A", True, {"features/forms.py": "h2"},
             (True, False, P.LOCKED, 2, True)),
            ("helper unlock, new B-rep", locked, "B", True, {"features/forms.py": "h2"},
             (True, False, P.AWAITING, 2, False)),
            ("helper unlock, failing round", locked, "B", False, {"features/forms.py": "h2"},
             (True, False, P.LOCKED, 2, False)),
            ("assembly unlock, new B-rep", unlocked, "B", True, None, (True, False, P.AWAITING, 2, False)),
            ("assembly unlock, back to the reviewed B-rep", unlocked, "A", True, None, (True, False, P.LOCKED, 2, True)),
        ]
        for name, previous, identity, checks_ok, helpers, expected in cases:
            with self.subTest(name):
                result = self.decide(previous, identity, checks_ok, helpers=helpers)
                state = result["state"]
                observed = (result["admit"], result["shape_round"], state and state["phase"],
                            state and state["shape_rounds"], result["carried"] is not None)
                self.assertEqual(observed, expected)
                if not result["admit"]:
                    self.assertTrue(result["refusal"])

    def test_admission_is_decided_before_the_checks(self):
        P = self.module
        result = P.round_policy({"phase": P.AWAITING, "identity": "A", "round": 3}, {"identity": "B"})
        self.assertEqual((result["admit"], result["state"]), (False, None))
        self.assertIn("r0003 passed its build and print checks and has no Component Review", result["refusal"])
        result = P.round_policy({"phase": P.AWAITING, "identity": "A", "round": 3}, {"identity": "A"})
        self.assertEqual((result["admit"], result["state"]), (True, None))

    def test_a_carried_unlock_relocks_and_clears_its_reasons(self):
        P = self.module
        locked = {"phase": P.LOCKED, "identity": "A", "round": 3, "shape_rounds": 2,
                  "reviewed": self.reviewed(agrees=True, helpers={"features/forms.py": "h1"})}
        result = self.decide(locked, "A", helpers={"features/forms.py": "h2"})
        self.assertEqual(result["unlocks"], [{"kind": "shared-helper", "paths": ["features/forms.py"]}])
        self.assertEqual(result["state"]["unlocks"], [])
        self.assertEqual(result["state"]["reviewed"]["imported_helpers"], {"features/forms.py": "h2"})

    def test_a_changed_reference_or_contract_row_is_not_carried(self):
        P = self.module
        locked = {"phase": P.LOCKED, "identity": "A", "round": 3, "shape_rounds": 2,
                  "reviewed": self.reviewed(agrees=True)}
        result = self.decide(locked, "A", key="other")
        self.assertEqual((result["carried"], result["state"]["phase"]), (None, P.AWAITING))

    def test_reviews(self):
        P = self.module
        review = {"agrees": False, "identity": "A", "carry_key": "kA", "imported_helpers": {}, "review": {}}
        for shape_rounds, agrees, phase, accepted in (
            (0, True, P.LOCKED, False), (4, False, P.DISAGREED, False),
            (5, False, P.LOCKED, True), (5, True, P.LOCKED, False),
        ):
            with self.subTest(shape_rounds=shape_rounds, agrees=agrees):
                state = P.review_policy({"phase": P.AWAITING, "round": 7, "shape_rounds": shape_rounds},
                                        {**review, "agrees": agrees})
                self.assertEqual((state["phase"], state["reviewed"]["accepted"], state["reviewed"]["round"]),
                                 (phase, accepted, 7))
        with self.assertRaisesRegex(ValueError, "not awaiting a Component Review"):
            P.review_policy({"phase": P.LOCKED, "round": 7}, review)

    def test_a_component_reviewed_by_an_earlier_make_round_keeps_its_review(self):
        P = self.module
        state = {"round": 4, "identity": "A", "checks_ok": True, "shape_rounds": 5}
        policy = P.legacy_policy(state, {"review": {"agrees": False}, "accepted": {"shape_rounds": 5}})
        self.assertEqual((policy["phase"], policy["reviewed"]["accepted"]), (P.LOCKED, True))
        self.assertEqual(P.legacy_policy(state, {"review": None})["phase"], P.AWAITING)
        self.assertEqual(P.legacy_policy({**state, "checks_ok": False}, {})["phase"], P.OPEN)
        self.assertEqual(P.legacy_policy({}, None), {"phase": P.OPEN})



class InterfaceTextDeliveryTest(unittest.TestCase):
    """ADR 0084: under a schema 4 Design Contract a component round delivers
    the Component's rows and the text of every Interface naming it; a review
    may list Reference Conflicts, which the Design Contract wins."""

    _run_root = SealedReferenceTest._run_root
    _fake_run = SealedReferenceTest._fake_run
    _main = SealedReferenceTest._main
    REFS = ContractComponentReviewTest.REFS
    POSED = ReferenceCameraRoundTest.POSED
    STAFF = "The body's bottom 10 mm, a bare 3.7 mm shaft below the ferrule, sits in a 3.9 x 10 socket in the base."
    PAIR = "The first body's left flange seats on the second body's 50 degree seat cone."
    CONFLICT = {"file": "ref-02-body.png", "reference": "the ferrule is the foot; no shaft below it",
                "contract": "Interface body-base: " + STAFF}

    def _contract(self, schema=4):
        references = [{"file": "ref-01-whole.png", "shows": "assembly", "camera": [-60, 20]},
                      {"file": "ref-02-body.png", "shows": "geometry:body", "camera": [90, 15]}]
        geometries = [{"id": "body", "name": "Body", "count": 2, "extents_mm": [30, 20, 10], "wall_min_mm": 1.2},
                      {"id": "base", "name": "Base", "count": 1, "extents_mm": [80, 80, 10], "wall_min_mm": 1.2},
                      {"id": "wing", "name": "Wing", "count": 1, "extents_mm": [40, 10, 4], "wall_min_mm": 1.2}]
        requirements = [{"id": "R01", "scope": "assembly", "text": "The bodies stand on the base."},
                        {"id": "R02", "scope": "geometry:body", "text": "The ferrule is a riveted band."},
                        {"id": "R03", "scope": "geometry:wing", "text": "The wing is a thin blade."}]
        interfaces = [{"id": "body-base", "kind": "static", "components": ["body", "base"], "text": self.STAFF},
                      {"id": "body-pair", "kind": "static", "components": ["body#1", "body#2"], "text": self.PAIR},
                      {"id": "wing-base", "kind": "static", "components": ["wing", "base"],
                       "text": "The wing clips into the base's slot."}]
        if schema < 4:
            for item in interfaces:
                del item["text"]
        return {"design_contract": {"schema_version": schema, "title": "Broken God", "references": references,
                                    "geometries": geometries, "requirements": requirements,
                                    "interfaces": interfaces}}

    def _root(self, tmp, schema=4):
        project = self._run_root(tmp, self.REFS, context=self._contract(schema))
        self._edits = 0
        return project

    def _component(self, module, project, calls, edit=True):
        if edit:
            self._edits += 1
            (project / "part_body.step.py").write_text(self.POSED % self._edits)
        # ADR 0082: component rounds start only after the Shared Helpers freeze.
        with mock.patch.object(module, "read_freeze", return_value={"round": 1, "helpers": {}}), \
                mock.patch.object(module, "freeze_report", return_value={}):
            code = self._main(module, project, ["--component", "part_body.step.py"], calls)
        state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
        return code, json.loads((project / ("measure/component-rounds/body/r%04d/summary.json" % state["round"])).read_text())

    def _review(self, module, project, summary, **changes):
        return module.record_review(project, write_review(project, summary, **changes), "part_body.step.py")

    def _wish(self, project, change):
        wish_path = module_run_root(project) / "WISH.json"
        wish = json.loads(wish_path.read_text())
        change(wish["context"]["design_contract"])
        wish_path.write_text(json.dumps(wish))

    def test_the_packet_and_summary_carry_the_components_rows_and_interface_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            packet = json.loads(Path(summary["visual"]["packet"]).read_text())
            self.assertEqual(packet["contract"], summary["contract"])
            contract = summary["contract"]
            self.assertEqual((contract["schema_version"], contract["component"]), (4, "body"))
            self.assertEqual(contract["geometry"]["id"], "body")
            self.assertEqual(contract["requirements"], [{"id": "R02", "text": "The ferrule is a riveted band."}])
            # Every Interface naming the body, as itself or as one instance; never another's.
            self.assertEqual(contract["interfaces"], [
                {"id": "body-base", "kind": "static", "components": ["body", "base"], "text": self.STAFF},
                {"id": "body-pair", "kind": "static", "components": ["body#1", "body#2"], "text": self.PAIR},
            ])
            self.assertIn("contract", summary["visual"]["detail"])
            self.assertIn("contract 1 requirement row(s), 2 Interface(s)", module.render_summary(summary))

    def test_a_changed_row_or_interface_text_changes_the_packet_hash(self):
        changes = {
            "row": lambda contract: contract["requirements"][1].update(text="The ferrule is a plain band."),
            "interface text": lambda contract: contract["interfaces"][1].update(text="A flat seat."),
        }
        for name, change in changes.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                project = self._root(tmp)
                module, calls = load_module(), []
                _, first = self._component(module, project, calls)
                self._wish(project, change)
                _, second = self._component(module, project, calls, edit=False)
                self.assertEqual(second["round"], 2)
                self.assertNotEqual(second["contract"], first["contract"])
                self.assertNotEqual(second["visual"]["packet_sha256"], first["visual"]["packet_sha256"])
                self.assertNotEqual(second["carry_key"], first["carry_key"])

    def test_before_schema_4_the_packet_carries_no_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp, schema=3)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self.assertNotIn("contract", summary)
            self.assertNotIn("contract", json.loads(Path(summary["visual"]["packet"]).read_text()))
            # The Interfaces did not join the contract-row hash either.
            rows = module.contract_rows(project, "body")
            self._wish(project, lambda contract: contract["interfaces"].pop(0))
            self.assertEqual(module.contract_rows(project, "body"), rows)

    def test_a_conflict_only_agreeing_review_locks_and_the_worker_never_sees_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            result = self._review(module, project, summary, reference_conflicts=[dict(self.CONFLICT)])
            self.assertTrue(result["ok"])
            self.assertEqual(result["locked"], {"round": 1, "source": "agreeing-review"})
            recorded = [{"component": "body", "label": "geometry:body", "file": "ref-02-body.png", "round": 1,
                         "reviewer": "fresh-reviewer-subagent", "reference": self.CONFLICT["reference"],
                         "contract": self.CONFLICT["contract"]}]
            self.assertEqual(result["reference_conflicts"], recorded)
            self.assertNotIn("reference_conflicts", result["review"])
            out = Path(result["out"])
            self.assertNotIn("reference_conflicts", json.loads((out / "review.json").read_text()))
            self.assertEqual(json.loads((out / "reference-conflicts.json").read_text()), recorded)
            self.assertIn("1 Reference Conflict(s) recorded", module.render_summary(result))
            state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
            self.assertEqual((state["policy"]["phase"], state["policy"]["shape_rounds"]), ("locked", 0))
            digests = state["parts"]
            self.assertEqual(list(module.component_coverage(project, digests).values()), [
                {"role": "body", "accepted": None, "reference_conflicts": recorded}])
            # An unchanged rerun carries the review and its conflicts.
            code, carried = self._component(module, project, calls, edit=False)
            self.assertEqual((code, carried["review"]["carried_from"]), (0, 1))
            self.assertEqual(carried["reference_conflicts"], recorded)

    def test_conflicts_beside_differences_spend_only_the_differences_shape_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            result = self._review(module, project, summary, agrees=False, reason="The band is too thin.",
                                  differences=ContractComponentReviewTest.DIFFERS,
                                  reference_conflicts=[dict(self.CONFLICT)])
            self.assertFalse(result["ok"])
            self.assertEqual(len(result["reference_conflicts"]), 1)
            _, repaired = self._component(module, project, calls)
            self.assertEqual((repaired["shape_round"], repaired["shape_rounds"]), (True, 1))

    def test_a_conflict_only_disagreement_is_refused_and_spends_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            with self.assertRaisesRegex(ValueError, "only findings are Reference Conflicts agrees"):
                self._review(module, project, summary, agrees=False, reason="The foot differs.",
                             reference_conflicts=[dict(self.CONFLICT)])
            state = json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())
            self.assertEqual((state["policy"]["phase"], state["policy"]["shape_rounds"]), ("awaiting-review", 0))
            self.assertFalse((Path(summary["out"]) / "review.json").exists())
            self.assertTrue(self._review(module, project, summary, reference_conflicts=[dict(self.CONFLICT)])["ok"])

    def test_a_malformed_reference_conflict_is_refused(self):
        cases = {
            "not a list": ({"reference_conflicts": dict(CONFLICT_FIXTURE)}, "at most 12 reference_conflicts"),
            "too many": ({"reference_conflicts": [dict(CONFLICT_FIXTURE)] * 13}, "at most 12 reference_conflicts"),
            "missing field": ({"reference_conflicts": [{"file": "ref-02-body.png", "reference": "a foot"}]},
                              "needs file, reference and contract"),
            "extra field": ({"reference_conflicts": [{**CONFLICT_FIXTURE, "repair": "none"}]},
                            "needs file, reference and contract"),
            "empty text": ({"reference_conflicts": [{**CONFLICT_FIXTURE, "contract": " "}]}, "1 to 1000 characters"),
            "not compared": ({"reference_conflicts": [{**CONFLICT_FIXTURE, "file": "ref-01-whole.png"}]},
                             "names one reference this round compared: ref-02-body.png"),
            "with a camera mismatch": ({"agrees": None, "camera_mismatch": dict(ReferenceCameraRoundTest.MISMATCH),
                                        "reference_conflicts": [dict(CONFLICT_FIXTURE)]},
                                       "camera mismatch replaces agrees, matches_plan, matches_reference, differences, "
                                       "reference_conflicts and ruling_disputes"),
        }
        for name, (changes, refusal) in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                project = self._root(tmp)
                module, calls = load_module(), []
                _, summary = self._component(module, project, calls)
                review = write_review(project, summary, **changes)
                if changes.get("agrees", True) is None:
                    data = json.loads(review.read_text())
                    del data["agrees"]
                    review.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, refusal):
                    module.record_review(project, review, "part_body.step.py")

    def test_reference_conflicts_are_accepted_before_schema_4(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp, schema=3)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            result = self._review(module, project, summary, reference_conflicts=[dict(self.CONFLICT)])
            self.assertTrue(result["ok"])
            self.assertEqual(result["reference_conflicts"][0]["file"], "ref-02-body.png")


CONFLICT_FIXTURE = InterfaceTextDeliveryTest.CONFLICT


class BlockedReportRulingTest(unittest.TestCase):
    """Issue #97: a Workshop Manager's decided ruling on a Component's Blocked
    Report travels in its review packet and binds the Component Reviewer; a
    reviewer who thinks it wrong disputes it apart from the form, which
    costs no Shape Round."""

    _run_root = SealedReferenceTest._run_root
    _fake_run = SealedReferenceTest._fake_run
    _main = SealedReferenceTest._main
    _root = InterfaceTextDeliveryTest._root
    _contract = InterfaceTextDeliveryTest._contract
    _component = InterfaceTextDeliveryTest._component
    _review = InterfaceTextDeliveryTest._review
    REFS = InterfaceTextDeliveryTest.REFS
    POSED = InterfaceTextDeliveryTest.POSED
    STAFF = InterfaceTextDeliveryTest.STAFF
    PAIR = InterfaceTextDeliveryTest.PAIR
    DIFFERS = ContractComponentReviewTest.DIFFERS
    STRUTS = [{"feature": "pelvis struts", "reference": "open space under the shield",
               "model": "two arch struts under the shield; remove them"}]
    ROW = "The ferrule is a riveted band."
    REQUEST = "Review of round 1 asks for a shield over open space; upright it starts as an island in air."
    RULING = "Keep the arch struts: the part prints upright without support. If a review asks again, give this reason."

    def _ledger(self, project, *events):
        ledger = project / "measure" / "blocked-reports.jsonl"
        ledger.parent.mkdir(exist_ok=True)
        with ledger.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event) + "\n")

    def _report(self, number, component="body", reason=REQUEST):
        return {"event": "report", "report": number, "at": "2026-10-04T06:28:38Z", "component": component,
                "round": 1, "rows": [self.ROW], "reason": reason}

    def _decision(self, number, ruling=RULING, waits_on=None):
        return {"event": "decision", "report": number, "at": "2026-10-04T06:32:31Z", "ruling": ruling,
                "waits_on": waits_on, "waits_on_round": None if waits_on is None else 1}

    def _ruled(self, project):
        self._ledger(project, self._report(1), self._decision(1))

    def _state(self, project):
        return json.loads((project / "measure/component-rounds/body/make-round-state.json").read_text())["policy"]

    def _packet(self, summary):
        return json.loads(Path(summary["visual"]["packet"]).read_text())

    def test_the_packet_and_summary_carry_only_the_components_decided_rulings(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            self._ledger(project, self._report(1), self._decision(1),
                         self._report(2, reason="still waiting for an answer"),
                         self._report(3, component="wing"), self._decision(3, ruling="Keep the blade table."),
                         self._report(4, reason="waits on the base"), self._decision(4, waits_on="base"))
            _, summary = self._component(module, project, calls)
            ruling = {"report": 1, "round": 1, "rows": [self.ROW], "request": self.REQUEST,
                      "ruling": self.RULING, "decided_at": "2026-10-04T06:32:31Z"}
            self.assertEqual(self._packet(summary)["rulings"], [ruling])
            self.assertEqual(summary["rulings"], [ruling])
            self.assertIn("rulings", summary["visual"]["detail"])
            self.assertIn("1 Blocked Report ruling(s) in the packet bind the reviewer: 1",
                          module.render_summary(summary))

    def test_without_a_ruling_the_packet_and_carry_key_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            self._ledger(project, self._report(1))  # open, not a ruling
            _, summary = self._component(module, project, calls)
            self.assertNotIn("rulings", self._packet(summary))
            self.assertNotIn("rulings", summary)
            identity = self._state(project)["identity"]
            self.assertEqual(summary["carry_key"],
                             module.carry_key(identity, summary["refs"], project, summary["contract_rows"]))

    def test_a_ruling_after_a_disagreement_earns_a_fresh_review_without_a_shape_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self._review(module, project, summary, agrees=False, reason="The struts must go.",
                         differences=self.STRUTS)
            self._ruled(project)
            # The unchanged rerun is not carried: what the review judged changed.
            code, rerun = self._component(module, project, calls, edit=False)
            self.assertEqual(code, 1)
            self.assertIsNone(rerun["review"])
            self.assertEqual((rerun["shape_round"], rerun["shape_rounds"], rerun["phase"]),
                             (False, 0, "awaiting-review"))
            self.assertEqual(self._packet(rerun)["rulings"][0]["report"], 1)
            dispute = {"report": 1, "reason": "The reference shows open space; the ruling keeps the struts."}
            result = self._review(module, project, rerun, ruling_disputes=[dispute])
            self.assertTrue(result["ok"])
            self.assertEqual(result["locked"], {"round": 2, "source": "agreeing-review"})
            recorded = [{"component": "body", "report": 1, "round": 2, "reviewer": "fresh-reviewer-subagent",
                         "reason": dispute["reason"]}]
            self.assertEqual(result["ruling_disputes"], recorded)
            out = Path(result["out"])
            self.assertNotIn("ruling_disputes", json.loads((out / "review.json").read_text()))
            self.assertEqual(json.loads((out / "ruling-disputes.json").read_text()), recorded)
            self.assertIn("disputes the ruling on Blocked Report 1", module.render_summary(result))
            self.assertEqual((self._state(project)["phase"], self._state(project)["shape_rounds"]), ("locked", 0))
            # An unchanged rerun carries the review and its dispute.
            code, carried = self._component(module, project, calls, edit=False)
            self.assertEqual((code, carried["review"]["carried_from"]), (0, 2))
            self.assertEqual(carried["ruling_disputes"], recorded)

    def test_a_dispute_only_disagreement_is_refused_and_spends_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            self._ruled(project)
            _, summary = self._component(module, project, calls)
            dispute = [{"report": 1, "reason": "The struts are not in the reference."}]
            with self.assertRaisesRegex(ValueError, "only findings are Ruling Disputes agrees"):
                self._review(module, project, summary, agrees=False, reason="The struts differ.",
                             ruling_disputes=dispute)
            self.assertEqual((self._state(project)["phase"], self._state(project)["shape_rounds"]),
                             ("awaiting-review", 0))
            self.assertFalse((Path(summary["out"]) / "review.json").exists())
            self.assertTrue(self._review(module, project, summary, ruling_disputes=dispute)["ok"])

    def test_disputes_beside_differences_spend_only_the_differences_shape_round(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            self._ruled(project)
            _, summary = self._component(module, project, calls)
            result = self._review(module, project, summary, agrees=False, reason="The arm is thin.",
                                  differences=self.DIFFERS,
                                  ruling_disputes=[{"report": 1, "reason": "The struts still show."}])
            self.assertFalse(result["ok"])
            self.assertEqual(len(result["ruling_disputes"]), 1)
            self.assertEqual(json.loads((Path(result["out"]) / "review.json").read_text())["differences"],
                             self.DIFFERS)
            _, repaired = self._component(module, project, calls)
            self.assertEqual((repaired["shape_round"], repaired["shape_rounds"]), (True, 1))

    def test_a_review_of_a_packet_older_than_a_ruling_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            self._ruled(project)
            with self.assertRaisesRegex(ValueError, "decided a Blocked Report of body after r0001"):
                self._review(module, project, summary)
            self.assertEqual(self._state(project)["phase"], "awaiting-review")
            # An unchanged rerun renders the ruling and is reviewed as usual.
            _, rerun = self._component(module, project, calls, edit=False)
            self.assertEqual((rerun["round"], rerun["shape_rounds"]), (2, 0))
            self.assertTrue(self._review(module, project, rerun)["ok"])

    def test_a_malformed_ruling_dispute_is_refused(self):
        good = {"report": 1, "reason": "The ruling is wrong."}
        cases = {
            "not a list": ({"ruling_disputes": dict(good)}, "at most 12 ruling_disputes"),
            "too many": ({"ruling_disputes": [dict(good)] * 13}, "at most 12 ruling_disputes"),
            "missing reason": ({"ruling_disputes": [{"report": 1}]}, "needs report and reason"),
            "extra field": ({"ruling_disputes": [{**good, "repair": "remove"}]}, "needs report and reason"),
            "unknown report": ({"ruling_disputes": [{**good, "report": 2}]}, "names one ruling of the packet"),
            "report as text": ({"ruling_disputes": [{**good, "report": "1"}]}, "names one ruling of the packet"),
            "empty reason": ({"ruling_disputes": [{**good, "reason": " "}]}, "1 to 1000 characters"),
            "with a camera mismatch": ({"agrees": None, "camera_mismatch": dict(ReferenceCameraRoundTest.MISMATCH),
                                        "ruling_disputes": [dict(good)]},
                                       "camera mismatch replaces agrees, matches_plan, matches_reference, "
                                       "differences, reference_conflicts and ruling_disputes"),
        }
        for name, (changes, refusal) in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                project = self._root(tmp)
                module, calls = load_module(), []
                self._ruled(project)
                _, summary = self._component(module, project, calls)
                review = write_review(project, summary, **changes)
                if changes.get("agrees", True) is None:
                    data = json.loads(review.read_text())
                    del data["agrees"]
                    review.write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, refusal):
                    module.record_review(project, review, "part_body.step.py")

    def test_a_dispute_without_any_ruling_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            _, summary = self._component(module, project, calls)
            with self.assertRaisesRegex(ValueError, "the packet has none"):
                self._review(module, project, summary, ruling_disputes=[{"report": 1, "reason": "wrong"}])

    def test_an_invalid_ledger_refuses_the_component_round_before_building(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._root(tmp)
            module, calls = load_module(), []
            (project / "measure").mkdir(exist_ok=True)
            (project / "measure" / "blocked-reports.jsonl").write_text("{not json}\n")
            (project / "part_body.step.py").write_text(self.POSED % 1)
            with mock.patch.object(module, "read_freeze", return_value={"round": 1, "helpers": {}}):
                code = self._main(module, project, ["--component", "part_body.step.py"], calls)
            self.assertEqual(code, 2)
            self.assertIn("Blocked Report ledger", self.stderr)
            self.assertFalse(any(Path(command[1]).name == "gen" for command in calls))


class GuardedRunNonceTest(unittest.TestCase):
    """Issue #113: in a run the host gave the make_round guard, a component
    build round without a worker nonce fails at once."""

    _run_root = SealedReferenceTest._run_root
    _main = SealedReferenceTest._main
    _fake_run = SealedReferenceTest._fake_run

    def _guard(self, project):
        from workshop.make.role_guard import MAKE_ROUND_GUARD_MARKER, make_round_guard_marker_bytes

        marker = module_run_root(project) / MAKE_ROUND_GUARD_MARKER
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_bytes(make_round_guard_marker_bytes())

    def test_a_component_round_without_a_nonce_fails_in_a_guarded_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            self._guard(project)
            module, calls = load_module(), []
            code = self._main(module, project, ["--component", "part_body.step.py"], calls)
            self.assertEqual(code, 2)
            self.assertIn("--worker-nonce", self.stderr)
            self.assertIn("own", self.stderr)
            self.assertEqual(calls, [])
            self.assertFalse((project / "measure/component-rounds/body").exists())

    def test_a_nonce_round_runs_in_a_guarded_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            self._guard(project)
            module, calls = load_module(), []
            self._main(module, project, ["--component", "part_body.step.py", "--worker-nonce", "ab" * 16], calls)
            summary = json.loads((project / "measure/component-rounds/body/r0001/summary.json").read_text())
            self.assertEqual(summary["worker_nonce"], "ab" * 16)

    def test_a_component_round_without_a_nonce_still_runs_where_no_guard_is_materialised(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            module, calls = load_module(), []
            self._main(module, project, ["--component", "part_body.step.py"], calls)
            summary = json.loads((project / "measure/component-rounds/body/r0001/summary.json").read_text())
            self.assertIsNone(summary["worker_nonce"])

    def test_records_that_build_nothing_need_no_nonce_in_a_guarded_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._run_root(tmp, {"ref-01-whole.png": b"whole"})
            self._guard(project)
            module, calls = load_module(), []
            code = self._main(module, project, ["--blocked-reports"], calls)
            self.assertEqual(code, 0)


def module_run_root(project):
    """The run workspace above a CAD project, as the fixture lays it out."""
    return Path(project).parents[4]


if __name__ == "__main__":
    unittest.main()
