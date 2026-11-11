"""Workshop ADR 0102, 2026-11-11 amendment: a seeded run's assembly look is
taken beside the Approved Proof's own assembly renders, never a Reference
Image.

Contract:
- In a seeded run that froze the review (MAKE-OPTIONS schema 5) whose seal
  carries ``assembly_renders`` (APPROVAL schema 3), an assembly round whose
  look the Approved Proof's review does not carry composes, at each sealed
  render's camera, the sealed render beside the model rendered at that
  camera. The packet names ``basis: "approved-proof"``, binds the sealed
  renders and their copies by sha256 and binds no Reference Image.
- The Manager's feedback on such a packet answers ``matches_approved`` and
  lists each difference as ``{feature, approved, model, decision, reason}``;
  ``matches_reference``, a reference-shaped difference and a pass with
  ``matches_approved`` false are refused.
- A missing or changed sealed render leaves the round with a visual error; a
  changed copy makes the packet stale.
- A seal without assembly renders (schema 2), and a run that did not freeze
  the review, keep the reference look.
- An earlier recorded look carries only on the same basis and renders.
"""

from __future__ import annotations

import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tests.make.test_make_round import (_gate_output, _gate_report, fake_render_review, load_module, png,
                                        record_fixture_visual_pass)

RENDER = "approved/assembly/az90_el15.png"
RENDER_BYTES = png(b"approved assembly az90_el15")
RENDERS = [{"file": RENDER, "camera": [90.0, 15.0], "sha256": hashlib.sha256(RENDER_BYTES).hexdigest()}]


def _no_seed_carry(project, approval):
    raise ValueError("body deviated from the Approved Proof")


class AssemblyLookAgainstProofTest(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.run_dir = self.root / "run"
        (self.run_dir / "seed/approved/assembly").mkdir(parents=True)
        (self.run_dir / "WISH.json").write_text("{}\n")
        (self.run_dir / "seed" / RENDER).write_bytes(RENDER_BYTES)
        self.project = self.run_dir / "product"
        (self.project / "measure").mkdir(parents=True)
        (self.project / "toy.step.py").write_text("# fake\n")
        (self.project / "part_body.step.py").write_text("# fake\n")
        (self.root / "skills/cad/scripts").mkdir(parents=True)
        (self.root / "skills/cad/scripts/gen").write_text("# fake generator\n")
        (self.root / "skills/image-to-cad/scripts").mkdir(parents=True)
        self.calls = []

    def _approval(self, renders=RENDERS):
        approval = {"components": {}}
        if renders is not None:
            approval["assembly_renders"] = renders
        return approval

    def _run(self, command, *, cwd, log, **kwargs):
        self.calls.append(list(command))
        tool = Path(command[1]).name
        if tool == "gen":
            source = Path(command[2])
            source.with_name(source.name[:-len(".py")]).write_bytes(b"stable fake part")
            return subprocess.CompletedProcess(command, 0, '{"ok":true}\n', "")
        if tool == "render_review":
            return fake_render_review(command)
        if tool in ("check_thickness", "check_overhang", "check_mesh"):
            _gate_report(command)
            gate_out, code = (_gate_output(tool, fails=False) if tool != "check_mesh"
                              else ("RESULT: printable\n", 0))
            log.write_text(gate_out)
            return subprocess.CompletedProcess(command, code, gate_out, "")
        if tool == "inspect" and command[2] == "interfere":
            return subprocess.CompletedProcess(command, 0, '{"ok":true,"clashes":[]}\n', "")
        raise AssertionError("unexpected tool " + tool)

    def _round(self, module, *, frozen=True, renders=RENDERS):
        args = SimpleNamespace(
            project=str(self.project), entry=None, out=None, all_parts=False, refs=[], min=0.90, nozzle=0.4,
            overhang_angle=45.0, no_motion=True, check_motion=False, full=False, json=True,
            record_visual=None, component=None, require_component_passes=False)
        output = io.StringIO()
        with patch.object(module, "skills_root", return_value=self.root / "skills"), \
                patch.object(module, "run", self._run), \
                patch.object(module, "seed_approval", return_value=self._approval(renders)), \
                patch.object(module, "seed_round_carry", _no_seed_carry), \
                patch.object(module, "seed_reviews_against_proof", return_value=frozen), redirect_stdout(output):
            code = module.make_round(args)
        return code, json.loads(output.getvalue())

    def _feedback(self, module, summary, **changes):
        feedback = {"packet_sha256": summary["visual"]["packet_sha256"], "status": "pass", "findings": [],
                    "observation": "Round %d: the assembly reads as the approved one." % summary["round"],
                    "matches_plan": True, "matches_approved": True, **changes}
        feedback = {key: value for key, value in feedback.items() if value is not None}
        path = self.root / ("feedback-%d.json" % summary["round"])
        path.write_text(json.dumps(feedback))
        return module.record_visual(self.project, path)

    def test_the_look_compares_the_approved_assembly_render_and_shows_no_reference(self):
        module = load_module()
        composed = []
        original = module.compose_comparison
        module.compose_comparison = lambda left, right, target, caption: (
            composed.append((Path(left), Path(right), caption)), original(left, right, target, caption))
        code, summary = self._round(module)
        self.assertEqual((code, summary["visual"]["status"]), (1, "pending"))
        renders = [c for c in self.calls if Path(c[1]).name == "render_review"]
        self.assertEqual(len(renders), 1)  # the model only: the approved side is the seal's render
        self.assertIn("--view=90,15", renders[0])
        out = Path(summary["out"])
        ((left, right, caption),) = composed
        self.assertEqual(left, out / "visual/approved-proof/az90_el15.png")
        self.assertEqual(left.read_bytes(), RENDER_BYTES)
        self.assertEqual(right, out / "visual/az90_el15.png")
        self.assertIn("approved Proof | model", caption)
        packet = json.loads(Path(summary["visual"]["packet"]).read_text())
        self.assertEqual(packet["basis"], "approved-proof")
        self.assertEqual(packet["references"], {})
        self.assertEqual(packet["approved"]["assembly_renders"], {RENDER: RENDERS[0]["sha256"]})
        self.assertEqual(list(packet["approved"]["renders"].values()), [RENDERS[0]["sha256"]])
        self.assertIn("matches_approved", summary["visual"]["detail"])

    def test_a_pass_records_matches_approved(self):
        module = load_module()
        _, summary = self._round(module)
        recorded = self._feedback(module, summary)
        self.assertTrue(recorded["ok"])
        self.assertEqual((recorded["visual"]["status"], recorded["visual"]["matches_approved"]), ("pass", True))
        self.assertIn("approved=true", module.render_summary(recorded))

    def test_a_failing_look_lists_differences_from_the_approved_render(self):
        module = load_module()
        _, summary = self._round(module)
        differs = [{"feature": "tail", "approved": "curls up", "model": "lies flat", "decision": "repair",
                    "reason": "the deviation changed it"}]
        recorded = self._feedback(module, summary, status="fail", matches_approved=False, differences=differs,
                                  findings=[{"part": "body", "defect": "flat tail", "evidence": "compare-00",
                                             "repair": "curl it"}])
        self.assertFalse(recorded["ok"])
        self.assertIn("differs tail: approved curls up", module.render_summary(recorded))

    def test_refused_feedback(self):
        cases = [
            ("never matches_reference", dict(matches_reference=True)),
            ("invalid visual feedback fields", dict(matches_approved=None)),
            ("matches_approved not false", dict(matches_approved=False)),
            ("feature, approved, model, decision and reason",
             dict(differences=[{"feature": "tail", "reference": "curled", "model": "flat", "decision": "keep",
                                "reason": "fine"}])),
        ]
        module = load_module()
        _, summary = self._round(module)
        for fragment, changes in cases:
            with self.subTest(fragment), self.assertRaisesRegex(ValueError, fragment):
                self._feedback(module, summary, **changes)

    def test_a_missing_or_changed_sealed_render_is_a_visual_error(self):
        (self.run_dir / "seed" / RENDER).write_bytes(b"other")
        module = load_module()
        _, summary = self._round(module)
        self.assertEqual(summary["visual"]["status"], "error")
        self.assertIn("assembly render", summary["visual"]["detail"])

    def test_a_changed_copy_makes_the_packet_stale(self):
        module = load_module()
        _, summary = self._round(module)
        (Path(summary["out"]) / "visual/approved-proof/az90_el15.png").write_bytes(png(b"other"))
        with self.assertRaisesRegex(ValueError, "stale images"):
            self._feedback(module, summary)

    def test_a_seal_without_renders_or_a_run_without_the_review_keeps_the_reference_look(self):
        for name, options in (("schema 2 seal", dict(renders=None)), ("not frozen", dict(frozen=False))):
            with self.subTest(name):
                self.setUp()
                module = load_module()
                _, summary = self._round(module, **options)
                packet = json.loads(Path(summary["visual"]["packet"]).read_text())
                self.assertNotIn("basis", packet)
                self.assertNotIn("approved", packet)

    def test_an_earlier_reference_look_does_not_carry_into_an_approved_look(self):
        module = load_module()
        _, first = self._round(module, renders=None)
        recorded = record_fixture_visual_pass(module, self.project, first)
        self.assertEqual(recorded["visual"]["status"], "pass")
        _, second = self._round(module)
        self.assertEqual(second["visual"]["status"], "pending")
        self._feedback(module, second)
        _, third = self._round(module)
        self.assertEqual((third["visual"]["status"], third["visual"]["carried_from"]), ("carried", "r0002"))


if __name__ == "__main__":
    unittest.main()


class ContractImageAssemblyLookTest(AssemblyLookAgainstProofTest):
    """ADR 0103: a schema 4 seal's assembly reference, sealed by the run as
    the approved Proof render, is the approved side of the assembly look."""

    def setUp(self):
        super().setUp()
        (self.run_dir / "wish-references").mkdir()
        (self.run_dir / "wish-references/ref-01-assembly.png").write_bytes(RENDER_BYTES)

    def _approval(self, renders=RENDERS):
        if renders is None:
            return {"components": {}}
        return {"components": {}, "contract_images": [
            {"file": "ref-01-assembly.png", "kind": "reference", "shows": "assembly", "camera": [90, 15],
             "sha256": RENDERS[0]["sha256"]}]}

    def test_the_look_binds_the_contract_image(self):
        module = load_module()
        _, summary = self._round(module)
        packet = json.loads(Path(summary["visual"]["packet"]).read_text())
        self.assertEqual(packet["approved"]["contract_images"], {"ref-01-assembly.png": RENDERS[0]["sha256"]})
        self.assertNotIn("assembly_renders", packet["approved"])

    def test_a_missing_or_changed_sealed_render_is_a_visual_error(self):
        (self.run_dir / "wish-references/ref-01-assembly.png").write_bytes(b"AI drawing")
        module = load_module()
        _, summary = self._round(module)
        self.assertEqual(summary["visual"]["status"], "error")
        self.assertIn("not the approved Proof render", summary["visual"]["detail"])

    test_the_look_compares_the_approved_assembly_render_and_shows_no_reference = None
