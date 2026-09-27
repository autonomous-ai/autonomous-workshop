"""ADR 0074: in Contract Mode the final verifier accounts for every sealed image.

An assembly image is scored against the whole object by the verifier itself. A
Component image is never scored against the whole object; it is accounted for
by that Component's current round, which either passed the floor or was
accepted by the Workshop Manager after stalling out. Every acceptance is
written to a machine-readable record bound to the verification report, so the
host can report it when the run ends.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


VERIFIER = Path(__file__).resolve().parents[2] / "src/workshop/make/skills/cad/scripts/verify_project"
CONTRACT = {
    "design_contract": {
        "title": "Broken God",
        "references": [
            {"file": "ref-01-whole.png", "shows": "assembly"},
            {"file": "ref-02-body.png", "shows": "geometry:body"},
        ],
    }
}
IMAGES = {"ref-01-whole.png": b"whole", "ref-02-body.png": b"body"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class ContractLikenessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verifier = runpy.run_path(str(VERIFIER))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name).resolve()
        (self.run_root / "wish-references").mkdir()
        for name, content in IMAGES.items():
            (self.run_root / "wish-references" / name).write_bytes(content)
        self.write_wish(CONTRACT)
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        (self.project / "ref").mkdir(parents=True)
        (self.project / "toy.step.py").write_text("def gen_step(): pass\n")
        (self.project / "part_body.step.py").write_text("def gen_step(): pass\n")
        (self.project / "part_body.step").write_bytes(b"body step")
        for name, content in IMAGES.items():
            (self.project / "ref" / name).write_bytes(content)

    def write_wish(self, context):
        wish = {"references": [{"name": n, "sha256": sha(c)} for n, c in IMAGES.items()]}
        if context is not None:
            wish["context"] = context
        (self.run_root / "WISH.json").write_text(json.dumps(wish))

    def sealed(self):
        make_round, sealed, error = self.verifier["_contract_sealed_references"](self.project)
        self.assertIsNone(error)
        return make_round, sealed

    def component_round(self, *, iou, ok, identity="brep-body", accepted=None, stalled=False):
        root = self.project / "measure/component-rounds/body"
        (root / "r0001").mkdir(parents=True, exist_ok=True)
        (root / "make-round-state.json").write_text(json.dumps({
            "round": 1, "scope": "component:body", "parts": {"body": identity},
            "steps": {"body": sha(b"body step")},
        }))
        item = {"label": "geometry:body", "iou": iou, "ok": ok, "stall_streak": 3 if stalled else 0,
                "stalled_out": stalled}
        if accepted is not None:
            item["accepted"] = {"by": "workshop-manager", "reason": accepted}
        (root / "r0001/summary.json").write_text(json.dumps({
            "scope": "component:body", "entry": "part_body.step.py", "parts": ["body"],
            "ok": True, "refs": [["geometry:body", str(self.run_root / "wish-references/ref-02-body.png")]],
            "likeness": [item],
        }))

    # -- preflight ---------------------------------------------------------

    def test_a_component_image_cannot_be_scored_against_the_whole_object(self):
        _, sealed = self.sealed()
        refs = [("whole", self.project / "ref/ref-01-whole.png"), ("body", self.project / "ref/ref-02-body.png")]
        refusal = self.verifier["_contract_likeness_refusal"](sealed, refs)
        self.assertIn("geometry:body", refusal)
        self.assertIn("component round", refusal)

    def test_every_sealed_assembly_image_must_be_scored(self):
        _, sealed = self.sealed()
        refusal = self.verifier["_contract_likeness_refusal"](sealed, [])
        self.assertIn("assembly", refusal)
        self.assertIn("ref-01-whole.png", refusal)
        self.assertIsNone(self.verifier["_contract_likeness_refusal"](
            sealed, [("hero", self.project / "ref/ref-01-whole.png")]))

    def test_outside_contract_mode_nothing_changes(self):
        self.write_wish(None)
        make_round, sealed, error = self.verifier["_contract_sealed_references"](self.project)
        self.assertEqual((make_round, sealed, error), (None, [], None))

    def test_an_unreadable_wish_is_an_error_not_an_empty_list(self):
        (self.run_root / "WISH.json").write_text("{nope")
        _, _, error = self.verifier["_contract_sealed_references"](self.project)
        self.assertIn("WISH.json", error)

    # -- component coverage ------------------------------------------------

    def coverage(self, identities):
        make_round, sealed = self.sealed()
        return self.verifier["_component_likeness_coverage"](make_round, self.project, sealed, identities)

    def test_a_component_image_without_a_round_fails_final_verification(self):
        failures, acceptances = self.coverage({"body": "brep-body"})
        self.assertEqual(acceptances, [])
        self.assertEqual(len(failures), 1)
        self.assertIn("geometry:body", failures[0])
        self.assertIn("--component part_body.step.py", failures[0])

    def test_a_failing_unaccepted_component_round_fails_final_verification(self):
        self.component_round(iou=0.52, ok=False)
        failures, _ = self.coverage({"body": "brep-body"})
        self.assertEqual(len(failures), 1)

    def test_a_passing_component_round_accounts_for_its_image(self):
        self.component_round(iou=0.93, ok=True)
        self.assertEqual(self.coverage({"body": "brep-body"}), ([], []))

    def test_a_component_found_current_by_gen_is_matched_by_its_step_bytes(self):
        self.component_round(iou=0.93, ok=True)
        self.assertEqual(self.coverage({}), ([], []))

    def test_a_component_changed_since_its_round_fails(self):
        self.component_round(iou=0.93, ok=True)
        failures, _ = self.coverage({"body": "brep-moved"})
        self.assertEqual(len(failures), 1)

    def test_a_manager_acceptance_is_carried_as_a_record(self):
        reason = "Claws are thinner than the nozzle can hold."
        self.component_round(iou=0.61, ok=False, accepted=reason, stalled=True)
        failures, acceptances = self.coverage({"body": "brep-body"})
        self.assertEqual(failures, [])
        self.assertEqual(acceptances, [{
            "label": "geometry:body", "scope": "component:body", "iou": 0.61,
            "floor": 0.9, "reason": reason, "accepted_by": "workshop-manager",
        }])

    def test_an_acceptance_on_an_image_that_never_stalled_out_does_not_count(self):
        self.component_round(iou=0.61, ok=False, accepted="close enough", stalled=False)
        failures, _ = self.coverage({"body": "brep-body"})
        self.assertEqual(len(failures), 1)

    def test_the_gate_records_its_row_and_the_acceptance_note(self):
        reason = "Claws are thinner than the nozzle can hold."
        self.component_round(iou=0.61, ok=False, accepted=reason, stalled=True)
        make_round, sealed = self.sealed()
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        runner.likeness_acceptances = []
        runner.last_stdout = json.dumps({"sourceRef": "part_body.step.py", "identitySha256": "brep-body"})
        failed = self.verifier["_component_likeness_failed"](runner, make_round, self.project, sealed)
        self.assertFalse(failed)
        self.assertEqual([r["status"] for r in runner.records], ["rc=0", "note"])
        self.assertIn("accepted by the Workshop Manager", runner.records[1]["command"])
        self.assertEqual([a["label"] for a in runner.likeness_acceptances], ["geometry:body"])

    def test_the_gate_fails_the_run_when_a_component_image_is_unaccounted(self):
        make_round, sealed = self.sealed()
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        self.assertTrue(self.verifier["_component_likeness_failed"](runner, make_round, self.project, sealed))
        self.assertEqual(runner.records[-1]["status"], "rc=1")

    # -- gen identities and the acceptance record --------------------------

    def test_gen_json_lines_yield_each_built_part_identity(self):
        stdout = "\n".join([
            "building...",
            json.dumps({"ok": True, "sourceRef": "cad/part_body.step.py", "identitySha256": "b1"}),
            json.dumps({"ok": True, "sourceRef": "toy.step.py", "identitySha256": "t1"}),
            json.dumps({"ok": True, "sourceRef": "part_arm.step.py", "outcome": "current"}),
        ])
        self.assertEqual(self.verifier["_gen_part_identities"](stdout), {"body": "b1"})

    def test_the_acceptance_record_binds_the_verification_report(self):
        report = self.project / "measure/verification-pipeline.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# Verification pipeline record\n")
        acceptances = [{"label": "assembly", "scope": "assembly", "iou": 0.48, "floor": 0.9,
                        "reason": "r", "accepted_by": "workshop-manager"}]
        self.verifier["_write_likeness_acceptance"](report, acceptances)
        record = json.loads((report.parent / "likeness-acceptance.json").read_text())
        self.assertEqual(record, {
            "schema_version": 1,
            "verification_sha256": sha(report.read_bytes()),
            "acceptances": acceptances,
        })

    def test_the_acceptance_note_names_the_manager_not_a_user(self):
        source = VERIFIER.read_text(encoding="utf-8")
        self.assertNotIn("accepted by user", source)
        self.assertIn("accepted by the Workshop Manager", source)


if __name__ == "__main__":
    unittest.main()
