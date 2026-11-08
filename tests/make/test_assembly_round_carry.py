"""Issue #244: an assembly round accepts a review that already covers it.

Contract:
- In a seeded run whose Components all carry (ADR 0096), the assembly
  round's visual is ``carried`` from the Approved Proof: no Manager look is
  pending, and a round whose checks pass exits 0. A seed that does not carry
  leaves the look pending and names why.
- When the seed does not carry, a visual pass the Manager recorded on the
  latest earlier assembly round of the seeded run carries only when that
  round's packet bound the same sources and references (the host batch's
  gate rerun of a repaired build); a changed build waits for a new look.
- An unseeded run inspects every assembly round afresh (ADR 0075): no look
  carries there.
- A carried round whose motion or print analysis ran out of time is not ok:
  a timeout is never a pass.
- ``--full`` alone verifies a carried round; on a pending one it still asks
  for ``--record-visual``, and it is refused with ``--component``.
- ``--geometry-seconds`` sets the round's shared geometry allowance and is
  range-checked."""

from __future__ import annotations

import io
import json
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.make.test_make_round import (_gate_output, _gate_report, fake_visual_render, load_module,
                                        record_fixture_visual_pass)
from tests.make.test_seed_assembly_carry import IDENTITIES, _SeededProject


def _seeded(base: Path) -> _SeededProject:
    seeded = _SeededProject(base)
    (seeded.run / "WISH.json").write_text("{}\n")  # what marks the run root
    return seeded


# A seeded run whose Approved Proof review does not carry (a repaired build).
NOT_CARRYING = {"components": {}}


def _no_seed_carry(project, approval):
    raise ValueError("body's latest round is neither the approved Component nor locked by a review")


def _pending(packet: Path) -> dict:
    return {"status": "pending", "packet": str(packet), "packet_sha256": "p" * 64, "detail": "look at it"}


class CarriedVisualTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.m = load_module()

    def _recorded_visual(self, project, out, pending):
        with patch.object(self.m, "seed_round_carry", _no_seed_carry):
            return self.m.carried_assembly_visual(project, out, pending, NOT_CARRYING)

    def _packet(self, path: Path, sources: dict, references=None) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"schema_version": 3, "sources": sources, "references": references or []}))
        return path

    def test_a_seed_whose_components_all_carry_carries_the_look(self):
        seeded = _seeded(self.base)
        out = seeded.project / "measure/rounds/r0001"
        visual = self.m.carried_assembly_visual(
            seeded.project, out, _pending(self._packet(out / "visual-packet.json", {"a": "1"})), seeded.approval)
        self.assertEqual(visual["status"], "carried")
        self.assertEqual(visual["carried_from"], "seed-approval")
        self.assertEqual(visual["components"], {role: "exact" for role in IDENTITIES})
        self.assertEqual(visual["critic_verdict"], "agree")
        self.assertEqual(visual["assembly_identity"], seeded.approval["assembly_identity"])

    def test_a_seed_that_does_not_carry_leaves_the_look_pending_and_says_why(self):
        for name, change in (
            ("unlocked", lambda seeded: seeded.round("body", IDENTITIES["body"], seed=None, number=2)),
            ("disagreeing review", lambda seeded: seeded.reviewed("lid", IDENTITIES["lid"], 2, agrees=False)),
            ("missing critic", lambda seeded: (seeded.run / "seed/CRITIC.json").unlink()),
        ):
            with self.subTest(name):
                seeded = _seeded(self.base / name)
                change(seeded)
                out = seeded.project / "measure/rounds/r0001"
                pending = _pending(self._packet(out / "visual-packet.json", {"a": "1"}))
                visual = self.m.carried_assembly_visual(seeded.project, out, pending, seeded.approval)
                self.assertEqual(visual["status"], "pending")
                self.assertIn("does not carry", visual["detail"])

    def _recorded(self, project: Path, number: int, sources: dict, *, visual="pass", feedback="pass",
                  checks_ok=True, bind=True):
        out = project / ("measure/rounds/r%04d" % number)
        packet = self._packet(out / "visual-packet.json", sources)
        summary = {"scope": "assembly", "checks_ok": checks_ok,
                   "visual": {"status": visual, "packet": str(packet), "packet_sha256": "h%d" % number}}
        (out / "summary.json").write_text(json.dumps(summary))
        (out / "visual-feedback.json").write_text(json.dumps(
            {"status": feedback, "packet_sha256": "h%d" % number if bind else "other", "observation": "fine"}))
        return out

    def test_a_recorded_look_on_the_same_build_carries(self):
        project = self.base / "cad"
        self._recorded(project, 1, {"part_a.step.py": "x"})
        out = project / "measure/rounds/r0002"
        visual = self._recorded_visual(
            project, out, _pending(self._packet(out / "visual-packet.json", {"part_a.step.py": "x"})))
        self.assertEqual((visual["status"], visual["carried_from"], visual["observation"]),
                         ("carried", "r0001", "fine"))
        self.assertEqual(len(visual["visual_feedback_sha256"]), 64)

    def test_an_unseeded_run_inspects_every_round_afresh(self):
        """ADR 0075: outside a seeded run no recorded look carries."""
        project = self.base / "cad"
        self._recorded(project, 1, {"part_a.step.py": "x"})
        out = project / "measure/rounds/r0002"
        pending = _pending(self._packet(out / "visual-packet.json", {"part_a.step.py": "x"}))
        self.assertIs(self.m.carried_assembly_visual(project, out, pending, None), pending)

    def test_a_changed_or_unrecorded_build_waits_for_a_new_look(self):
        cases = {
            "changed sources": dict(sources={"part_a.step.py": "y"}),
            "pending look": dict(visual="pending"),
            "failed look": dict(feedback="revise"),
            "feedback for another packet": dict(bind=False),
            "failed checks": dict(checks_ok=False),
        }
        for name, options in cases.items():
            with self.subTest(name):
                project = self.base / name
                sources = options.pop("sources", {"part_a.step.py": "x"})
                self._recorded(project, 1, sources, **options)
                out = project / "measure/rounds/r0002"
                pending = _pending(self._packet(out / "visual-packet.json", {"part_a.step.py": "x"}))
                visual = self._recorded_visual(project, out, pending)
                self.assertEqual(visual["status"], "pending")
                self.assertIn("does not carry", visual["detail"])

    def test_only_the_latest_recorded_look_can_carry(self):
        project = self.base / "cad"
        self._recorded(project, 1, {"part_a.step.py": "x"})
        self._recorded(project, 2, {"part_a.step.py": "changed"})
        out = project / "measure/rounds/r0003"
        pending = _pending(self._packet(out / "visual-packet.json", {"part_a.step.py": "x"}))
        self.assertEqual(self._recorded_visual(project, out, pending)["status"], "pending")

    def test_a_visual_that_is_not_pending_is_left_alone(self):
        seeded = _seeded(self.base)
        for status in ("not-run", "pass", "failed"):
            visual = {"status": status, "detail": "d"}
            self.assertIs(self.m.carried_assembly_visual(seeded.project, seeded.project, visual, seeded.approval),
                          visual)


class AssemblyRoundCarryTest(unittest.TestCase):
    """The round itself, on fake tools: no CAD, no real analysis."""

    def round(self, module, root: Path, *, motion_code=0, seeded=True):
        project = root / "product"
        measure = project / "measure"
        if not project.is_dir():
            measure.mkdir(parents=True)
            (project / "toy.step.py").write_text("# fake\n")
            (project / "part_body.step.py").write_text("# fake\n")
            (measure / "motion.json").write_text("{}\n")
            skills = root / "skills"
            (skills / "cad/scripts").mkdir(parents=True)
            (skills / "cad/scripts/gen").write_text("# fake generator\n")
            (skills / "image-to-cad/scripts").mkdir(parents=True)

        def run(command, *, cwd, log, **kwargs):
            tool = Path(command[1]).name
            if tool == "gen":
                source = Path(command[2])
                source.with_name(source.name[:-len(".py")]).write_bytes(b"stable fake part")
                return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")
            if tool == "render_review":
                return fake_visual_render(command)
            if tool == "check_motion":
                # Exit 3 is the timeout make_round's runner reports.
                text = '{"ok": true, "results": [{"id": "slide", "status": "pass", "detail": "clear"}]}\n'
                log.write_text(text)
                return subprocess.CompletedProcess(command, motion_code, text if motion_code == 0 else "", "")
            if tool in ("check_thickness", "check_overhang", "check_mesh"):
                _gate_report(command)
                gate_out, code = (_gate_output(tool, fails=False) if tool != "check_mesh"
                                  else ("RESULT: printable\n", 0))
                log.write_text(gate_out)
                return subprocess.CompletedProcess(command, code, gate_out, "")
            if tool == "inspect" and command[2] == "interfere":
                return subprocess.CompletedProcess(command, 0, '{"ok":true,"clashes":[]}\n', "")
            raise AssertionError("unexpected tool " + tool)

        args = SimpleNamespace(
            project=str(project), entry=None, out=None, all_parts=False, refs=[], min=0.90, nozzle=0.4,
            overhang_angle=45.0, no_motion=False, check_motion=True, full=False, json=True,
            record_visual=None, component=None, require_component_passes=False)
        output = io.StringIO()
        # A seeded run whose Approved Proof review does not carry: the
        # rerun is the host gate's, after a repair turn recorded a look.
        with patch.object(module, "skills_root", return_value=root / "skills"), patch.object(module, "run", run), \
                patch.object(module, "seed_approval", return_value=NOT_CARRYING if seeded else None), \
                patch.object(module, "seed_round_carry", _no_seed_carry), redirect_stdout(output):
            code = module.make_round(args)
        return code, json.loads(output.getvalue()), project

    def test_a_second_round_of_the_same_build_carries_the_recorded_look(self):
        """The host gate's rerun of a repaired seeded build (issue #244): a
        new round of unchanged bytes needs no second look."""
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, first, project = self.round(module, root)
            self.assertEqual((code, first["visual"]["status"]), (1, "pending"))
            record_fixture_visual_pass(module, project, first)
            code, second, _ = self.round(module, root)
            self.assertEqual(code, 0)
            self.assertTrue(second["ok"])
            self.assertEqual((second["visual"]["status"], second["visual"]["carried_from"]), ("carried", "r0001"))
            self.assertIn("no look needed", module.render_summary(second))
            # A changed build waits for a new look.
            (project / "part_body.step.py").write_text("# fake, changed\n")
            code, third, _ = self.round(module, root)
            self.assertEqual((code, third["visual"]["status"]), (1, "pending"))

    def test_an_unseeded_rerun_of_the_same_build_still_waits_for_a_look(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, first, project = self.round(module, root, seeded=False)
            record_fixture_visual_pass(module, project, first)
            code, second, _ = self.round(module, root, seeded=False)
            self.assertEqual((code, second["visual"]["status"]), (1, "pending"))

    def test_a_carried_round_whose_motion_ran_out_of_time_is_not_ok(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            code, first, project = self.round(module, root)
            record_fixture_visual_pass(module, project, first)
            code, timed_out, _ = self.round(module, root, motion_code=3)
            self.assertEqual(timed_out["motion_status"], "unverified")
            self.assertEqual(timed_out["geometry_status"], "unverified")
            self.assertEqual(timed_out["visual"]["status"], "carried")
            self.assertFalse(timed_out["ok"])
            self.assertEqual(code, 1)


class FullAloneTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / "cad"
        self.m = load_module()

    def _last(self, summary):
        out = self.project / "measure/rounds/r0001"
        out.mkdir(parents=True)
        (out / "summary.json").write_text(json.dumps(summary))
        (self.project / "measure/make-round-state.json").write_text(json.dumps({"round": 1, "last_out": str(out)}))

    def test_full_alone_verifies_a_carried_clean_round(self):
        self._last({"scope": "assembly", "ok": True, "visual": {"status": "carried", "packet": "p"}})
        with patch.object(self.m, "packet_error", return_value=None), \
                patch.object(self.m, "run_full") as run_full:
            summary = self.m.full_on_carried_round(self.project, True)
        self.assertEqual(summary["visual"]["status"], "carried")
        run_full.assert_called_once()
        self.assertIs(run_full.call_args.args[3], True)

    def test_full_alone_is_no_shortcut_past_a_pending_look(self):
        self._last({"scope": "assembly", "ok": False, "visual": {"status": "pending"}})
        with patch.object(self.m, "run_full") as run_full:
            self.assertIsNone(self.m.full_on_carried_round(self.project))
        run_full.assert_not_called()

    def test_full_alone_refuses_a_stale_or_failed_carried_round(self):
        for name, summary, stale in (
            ("stale", {"scope": "assembly", "ok": True, "visual": {"status": "carried"}}, "part_a changed"),
            ("failed", {"scope": "assembly", "ok": False, "visual": {"status": "carried"}}, None),
        ):
            with self.subTest(name):
                self.setUp()
                self._last(summary)
                with patch.object(self.m, "packet_error", return_value=stale), \
                        patch.object(self.m, "run_full") as run_full, self.assertRaises(ValueError):
                    self.m.full_on_carried_round(self.project)
                run_full.assert_not_called()

    def test_full_alone_without_a_carried_round_still_needs_record_visual(self):
        self.project.mkdir(parents=True)
        error = io.StringIO()
        with redirect_stderr(error), redirect_stdout(io.StringIO()):
            code = self.m.main([str(self.project), "--full"])
        self.assertNotEqual(code, 0)
        self.assertIn("--record-visual", error.getvalue())

    def test_full_alone_is_refused_for_a_component(self):
        self.project.mkdir(parents=True)
        error = io.StringIO()
        with redirect_stderr(error), redirect_stdout(io.StringIO()):
            code = self.m.main([str(self.project), "--full", "--component", "part_a.step.py"])
        self.assertEqual(code, 2)
        self.assertIn("not with --component", error.getvalue())


class GeometrySecondsTest(unittest.TestCase):
    def test_out_of_range_is_refused(self):
        module = load_module()
        for value in ("0", "-5", "86401"):
            with self.subTest(value), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                module.main(["/nonexistent", "--geometry-seconds", value])

    def test_it_sets_the_shared_and_per_operation_allowance(self):
        module = load_module()
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {}, clear=False), \
                redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
            module.main([directory, "--full", "--geometry-seconds", "1800"])
            self.assertEqual(os.environ["WORKSHOP_GEOMETRY_TIMEOUT"], "1800")
            self.assertEqual(os.environ["WORKSHOP_GEOMETRY_OPERATION_TIMEOUT"], "1800")


if __name__ == "__main__":
    unittest.main()
