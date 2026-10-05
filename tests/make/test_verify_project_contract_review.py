"""Contract Mode: the final verifier accounts for every sealed component image.

No silhouette score is computed anywhere. A Component image is accounted for by
that Component's current round: its checks passed and an independent reviewer
recorded agreement, or the shape-repair allowance ran out and the reviewer's
recorded disagreement became a component acceptance. make_round owns that rule
and reports it through ``component_coverage(project, digests)``; these tests
fake that function to its published contract. Every acceptance is written to
``component-acceptance.json``, bound to the verification report, so the host
can report it when the run ends.
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
REASON = "Claws are thinner than the nozzle can hold."


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FakeCoverage:
    """make_round's ``component_coverage(project, digests)`` for one passing body round.

    It covers the body image only while the body's identity is the one its
    round recorded, as the real function does through
    ``current_passing_component_round``.
    """

    def __init__(self, *, identities=("brep-body", sha(b"body step")), accepted=None, passing=True,
                 conflicts=None):
        self.identities = set(identities)
        self.accepted = accepted
        self.passing = passing
        self.conflicts = conflicts
        self.calls = []

    def __call__(self, *args):
        self.calls.append(args)
        _project, digests = args
        if not self.passing or digests.get("body") not in self.identities:
            return {}
        cover = {"role": "body", "accepted": self.accepted}
        if self.conflicts:
            cover["reference_conflicts"] = self.conflicts
        return {sha(IMAGES["ref-02-body.png"]): cover}


CONFLICT = {"component": "body", "label": "geometry:body", "file": "ref-02-body.png", "round": 3,
            "reviewer": "fresh-reviewer", "reference": "a flat riveted flange",
            "contract": "Interface heart-chest-seat: the flange's front face is a 50 degree seat cone"}


class ContractReviewTest(unittest.TestCase):
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
        self.assertIsNotNone(make_round)
        return sealed

    # -- preflight ---------------------------------------------------------

    def test_outside_contract_mode_nothing_changes(self):
        self.write_wish(None)
        make_round, sealed, error = self.verifier["_contract_sealed_references"](self.project)
        self.assertEqual((make_round, sealed, error), (None, [], None))

    def test_an_unreadable_wish_is_an_error_not_an_empty_list(self):
        (self.run_root / "WISH.json").write_text("{nope")
        _, _, error = self.verifier["_contract_sealed_references"](self.project)
        self.assertIn("WISH.json", error)

    def test_the_likeness_gate_is_gone(self):
        for name in ("_contract_likeness_refusal", "_parse_likeness_ref", "_read_likeness_history",
                     "_mismatch_acceptance_labels", "_accepted_likeness_summary",
                     "LIKENESS_FLOOR", "LIKENESS_STALL_STREAK", "LIKENESS_ACCEPTANCE_NAME"):
            self.assertNotIn(name, self.verifier)
        self.assertNotIn("check_likeness.py", {p.name for p in self.verifier["_sweep_tool_paths"](image_derived=True)})
        options = {o for a in self.verifier["build_parser"]()._actions for o in a.option_strings}
        self.assertFalse({"--likeness-ref", "--likeness-min", "--likeness-accept-mismatch",
                          "--likeness-accept-regression", "--search-fov"} & options)
        self.assertIn("--image-derived", options)

    # -- component coverage ------------------------------------------------

    def coverage(self, identities, fake):
        return self.verifier["_component_review_coverage"](
            {"component_coverage": fake}, self.project, self.sealed(), identities)

    def test_coverage_is_asked_without_a_floor(self):
        fake = FakeCoverage()
        self.coverage({"body": "brep-body"}, fake)
        self.assertEqual(fake.calls, [(self.project, {"body": "brep-body"})])

    def test_a_component_image_without_a_passing_round_fails_final_verification(self):
        failures, acceptances = self.coverage({"body": "brep-body"}, FakeCoverage(passing=False))
        self.assertEqual(acceptances, [])
        self.assertEqual(failures, [
            "geometry:body: no current component round passed its checks and independent "
            "review; run make_round --component part_body.step.py"
        ])

    def test_a_reviewed_component_round_accounts_for_its_image(self):
        self.assertEqual(self.coverage({"body": "brep-body"}, FakeCoverage()), ([], []))

    def test_only_component_images_are_accounted_for(self):
        # The assembly image is shown to the assembly's blind review, never scored here.
        fake = FakeCoverage()
        failures, _ = self.coverage({"body": "brep-body"}, fake)
        self.assertEqual(failures, [])
        self.assertEqual(list(fake.calls[0][1]), ["body"])

    def test_a_component_found_current_by_gen_is_matched_by_its_step_bytes(self):
        fake = FakeCoverage()
        self.assertEqual(self.coverage({}, fake), ([], []))
        self.assertEqual(fake.calls[0][1], {"body": sha(b"body step")})

    def test_a_component_changed_since_its_round_fails(self):
        failures, _ = self.coverage({"body": "brep-moved"}, FakeCoverage())
        self.assertEqual(len(failures), 1)

    def test_an_acceptance_at_the_shape_repair_limit_is_carried_as_a_record(self):
        accepted = {"reviewer": "fresh-reviewer", "reason": REASON, "shape_rounds": 5}
        failures, acceptances = self.coverage({"body": "brep-body"}, FakeCoverage(accepted=accepted))
        self.assertEqual(failures, [])
        self.assertEqual(acceptances, [{
            "label": "geometry:body", "scope": "component:body", "reviewer": "fresh-reviewer",
            "shape_rounds": 5, "reason": REASON, "accepted_by": "workshop-manager",
        }])

    def test_the_gate_records_its_row_and_the_acceptance_note(self):
        accepted = {"reviewer": "fresh-reviewer", "reason": REASON, "shape_rounds": 5}
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        runner.component_acceptances = []
        runner.last_stdout = json.dumps({"sourceRef": "part_body.step.py", "identitySha256": "brep-body"})
        failed = self.verifier["_component_review_failed"](
            runner, {"component_coverage": FakeCoverage(accepted=accepted)}, self.project, self.sealed())
        self.assertFalse(failed)
        self.assertEqual([r["status"] for r in runner.records], ["rc=0", "note"])
        self.assertTrue(runner.records[0]["command"].startswith("component review"))
        self.assertIn("accepted by the Workshop Manager", runner.records[1]["command"])
        self.assertIn("fresh-reviewer", runner.records[1]["command"])
        self.assertEqual([a["label"] for a in runner.component_acceptances], ["geometry:body"])

    def test_reference_conflicts_are_noted_and_bound_to_the_report(self):
        # ADR 0084: the contract won; the conflict is reported, never failed.
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        runner.component_acceptances = []
        runner.last_stdout = json.dumps({"sourceRef": "part_body.step.py", "identitySha256": "brep-body"})
        failed = self.verifier["_component_review_failed"](
            runner, {"component_coverage": FakeCoverage(conflicts=[CONFLICT])}, self.project, self.sealed())
        self.assertFalse(failed)
        expected = {"label": "geometry:body", "scope": "component:body", "file": "ref-02-body.png", "round": 3,
                    "reviewer": "fresh-reviewer", "reference": CONFLICT["reference"],
                    "contract": CONFLICT["contract"]}
        self.assertEqual(runner.reference_conflicts, [expected])
        self.assertEqual(runner.component_acceptances, [])
        self.assertIn("reference conflict", runner.records[-1]["command"])
        self.assertIn("the contract wins", runner.records[-1]["command"])
        report = self.project / "measure/verification-pipeline.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# Verification pipeline record\n")
        self.verifier["_write_component_acceptance"](report, [], None, runner.reference_conflicts)
        record = json.loads((report.parent / "component-acceptance.json").read_text())
        self.assertEqual(record["reference_conflicts"], [expected])
        # A run without conflicts writes the record exactly as before.
        self.verifier["_write_component_acceptance"](report, [], None, [])
        self.assertNotIn("reference_conflicts", json.loads((report.parent / "component-acceptance.json").read_text()))

    def test_the_gate_fails_the_run_when_a_component_image_is_unaccounted(self):
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        self.assertTrue(self.verifier["_component_review_failed"](
            runner, {"component_coverage": FakeCoverage(passing=False)}, self.project, self.sealed()))
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
        acceptances = [{"label": "geometry:body", "scope": "component:body", "reviewer": "fresh-reviewer",
                        "shape_rounds": 5, "reason": "r", "accepted_by": "workshop-manager"}]
        self.verifier["_write_component_acceptance"](report, acceptances)
        record = json.loads((report.parent / "component-acceptance.json").read_text())
        self.assertEqual(record, {
            "schema_version": 1,
            "verification_sha256": sha(report.read_bytes()),
            "acceptances": acceptances,
        })
        self.assertFalse((report.parent / "likeness-acceptance.json").exists())

    def test_the_final_report_writes_an_empty_record_in_an_image_derived_run(self):
        report = self.project / "measure/verification-pipeline.md"
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        runner.component_acceptances = []
        self.verifier["_write_report"](report, runner, mode="image-derived final", result=0,
                                        elapsed=0.1, bed=(220.0, 220.0, 220.0))
        record = json.loads((report.parent / "component-acceptance.json").read_text())
        self.assertEqual(record["acceptances"], [])
        self.assertEqual(record["verification_sha256"], sha(report.read_bytes()))

    def test_no_record_outside_an_image_derived_run(self):
        report = self.project / "measure/verification-pipeline.md"
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        self.verifier["_write_report"](report, runner, mode="final", result=0,
                                        elapsed=0.1, bed=(220.0, 220.0, 220.0))
        self.assertFalse((report.parent / "component-acceptance.json").exists())

    def test_the_acceptance_note_names_the_manager_not_a_user(self):
        source = VERIFIER.read_text(encoding="utf-8")
        self.assertNotIn("accepted by user", source)
        self.assertIn("accepted by the Workshop Manager", source)


if __name__ == "__main__":
    unittest.main()


class InterfaceReviewTest(unittest.TestCase):
    """ADR 0082: the final verifier lists each Interface with how it was
    proven, and refuses a Coupled Interface without a current passing check."""

    INTERFACES = [
        {"id": "arm-swing", "kind": "separable", "components": ["arm", "body"],
         "envelope": {"inside": "arm", "outside": "body",
                      "shapes": [{"pose": "rest", "box": {"min_mm": [0, 0, 0], "max_mm": [1, 1, 1]}}]}},
        {"id": "gear-mesh", "kind": "coupled", "components": ["body", "arm"], "yielding": "arm",
         "poses_from": "gear-mesh"},
    ]

    @classmethod
    def setUpClass(cls):
        cls.verifier = runpy.run_path(str(VERIFIER))
        cls.make_round = runpy.run_path(str(cls.verifier["MAKE_ROUND_SCRIPT"]))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name).resolve()
        contract = {"design_contract": {**CONTRACT["design_contract"], "interfaces": self.INTERFACES}}
        (self.run_root / "WISH.json").write_text(json.dumps({"references": [], "context": contract}))
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)
        (self.project / "part_arm.step").write_bytes(b"arm step")

    def _check(self, identities):
        state = self.project / "measure/interface-rounds/gear-mesh/make-round-state.json"
        state.parent.mkdir(parents=True)
        state.write_text(json.dumps({"round": 2, "ok": True, "verdict": "pass", "identities": identities}))

    def _gate(self):
        runner = self.verifier["Runner"](cwd=self.run_root, dry_run=False, verbose=False)
        runner.component_acceptances = []
        runner.last_stdout = json.dumps({"sourceRef": "part_body.step.py", "identitySha256": "brep-body"})
        coverage = {"component_coverage": lambda *_: {}, **{
            name: self.make_round[name] for name in ("contract_interfaces", "interface_failures", "interface_report",
                                                     "reference_roles")}}
        failed = self.verifier["_component_review_failed"](runner, coverage, self.project, [])
        return failed, runner

    def test_a_coupled_interface_without_a_current_check_fails_final_verification(self):
        failed, runner = self._gate()
        self.assertTrue(failed)
        self.assertEqual([item["check"] for item in runner.interfaces], ["keep-out-envelope", "not-run"])
        self._check({"body": "brep-body", "arm": sha(b"other arm")})
        failed, runner = self._gate()
        self.assertTrue(failed)
        self.assertEqual(runner.interfaces[1]["check"], "stale")

    def test_each_interface_is_listed_with_its_kind_and_proof(self):
        # The arm was found current by gen: its identity is its STEP bytes.
        self._check({"body": "brep-body", "arm": sha(b"arm step")})
        failed, runner = self._gate()
        self.assertFalse(failed)
        self.assertEqual(runner.interfaces[1], {"id": "gear-mesh", "kind": "coupled", "components": ["body", "arm"],
                                                "check": "pass", "yielding": "arm", "round": 2})
        notes = [record["command"] for record in runner.records if record["status"] == "note"]
        self.assertIn("gear-mesh (coupled: body + arm): --interface check pass at r0002", " ".join(notes))
        self.assertIn("arm-swing (separable: arm + body): Keep-out Envelope", " ".join(notes))
        report = self.project / "measure/verification-pipeline.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text("# Verification pipeline record\n")
        self.verifier["_write_component_acceptance"](report, [], runner.interfaces)
        record = json.loads((report.parent / "component-acceptance.json").read_text())
        self.assertEqual(record["interfaces"], runner.interfaces)

    def test_an_interface_between_two_instances_is_judged_on_their_one_component(self):
        # Issue #80: wing#1 and wing#2 are one Component, part_wing.step.py.
        contract = {"design_contract": {**CONTRACT["design_contract"], "interfaces": [
            {"id": "gear-mesh", "kind": "coupled", "components": ["wing#1", "wing#2"], "yielding": "wing#2",
             "poses_from": "gear-mesh"}]}}
        (self.run_root / "WISH.json").write_text(json.dumps({"references": [], "context": contract}))
        (self.project / "part_wing.step").write_bytes(b"wing step")
        self._check({"wing": sha(b"wing step")})
        failed, runner = self._gate()
        self.assertFalse(failed)
        self.assertEqual(runner.interfaces, [{"id": "gear-mesh", "kind": "coupled", "components": ["wing#1", "wing#2"],
                                              "check": "pass", "yielding": "wing#2", "round": 2}])
        (self.project / "part_wing.step").write_bytes(b"wing step 2")
        failed, runner = self._gate()
        self.assertTrue(failed)
        self.assertEqual(runner.interfaces[0]["check"], "stale")

    def test_a_contract_without_interfaces_writes_no_interfaces(self):
        (self.run_root / "WISH.json").write_text(json.dumps({"references": [], "context": CONTRACT}))
        failed, runner = self._gate()
        self.assertFalse(failed)
        self.assertIsNone(runner.interfaces)
