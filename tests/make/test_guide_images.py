"""ADR 0089: Guide Images are sealed beside the references, never compared
with the model, and every step they draw is accounted for under motion checks.

make_round owns the rules; verify_project carries the account into
``component-acceptance.json``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import runpy
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[2] / "src/workshop/make/skills"
MAKE_ROUND = SCRIPTS / "make-round/scripts/make_round"
VERIFIER = SCRIPTS / "cad/scripts/verify_project"
STEPS = ["Stand the car on its tail.", "Fold the wing halves onto the toes.", "Pop the head up."]
IMAGES = {
    "ref-01-whole.png": b"whole",
    "ref-02-body.png": b"body",
    "guide-01-steps.png": b"steps",
    "guide-02-side.png": b"side",
}
CONTRACT = {
    "schema_version": 5,
    "title": "Racer",
    "references": [
        {"file": "ref-01-whole.png", "shows": "assembly", "camera": [-90, 15]},
        {"file": "ref-02-body.png", "shows": "geometry:body", "camera": [-90, 15]},
    ],
    "guides": [
        {"file": "guide-01-steps.png", "shows": "The transformation, car to robot.", "steps": STEPS},
        {"file": "guide-02-side.png", "shows": "The leg fold from the side."},
    ],
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class GuideImageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.make_round = runpy.run_path(str(MAKE_ROUND))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name).resolve()
        (self.run_root / "wish-references").mkdir()
        for name, content in IMAGES.items():
            (self.run_root / "wish-references" / name).write_bytes(content)
        self.write_wish(CONTRACT)
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)

    def write_wish(self, contract, names=tuple(IMAGES)):
        wish = {"references": [{"name": n, "sha256": sha(IMAGES[n])} for n in names],
                "context": {"design_contract": contract}}
        (self.run_root / "WISH.json").write_text(json.dumps(wish))

    def write_steps(self, record):
        (self.project / "guide-steps.json").write_text(json.dumps(record))

    def report(self, check_motion=True):
        return self.make_round["guide_steps_report"](self.project, check_motion)

    # -- never compared ------------------------------------------------------

    def test_sealed_references_leave_every_guide_out(self):
        sealed, error = self.make_round["sealed_references"](self.project)
        self.assertIsNone(error)
        self.assertEqual([item["label"] for item in sealed], ["assembly", "geometry:body"])

    def test_sealed_guides_carry_what_they_show_and_their_steps(self):
        guides, error = self.make_round["sealed_guides"](self.project)
        self.assertIsNone(error)
        self.assertEqual([item["file"] for item in guides], ["guide-01-steps.png", "guide-02-side.png"])
        self.assertEqual(guides[0]["steps"], STEPS)
        self.assertEqual(guides[1]["steps"], [])
        self.assertEqual(guides[0]["path"], self.run_root / "wish-references/guide-01-steps.png")
        view = self.make_round["guide_view"](guides)
        self.assertEqual(set(view[0]), {"file", "shows", "path"})

    def test_an_unscoped_guide_reaches_every_component_and_a_scoped_one_only_its_own(self):
        # Issue #125: geometries names the Component Workers that read a guide.
        contract = dict(CONTRACT, guides=[CONTRACT["guides"][0],
                                          dict(CONTRACT["guides"][1], geometries=["leg", "body"])])
        self.write_wish(contract)
        guides, error = self.make_round["sealed_guides"](self.project)
        self.assertIsNone(error)
        self.assertEqual([item["geometries"] for item in guides], [None, ["leg", "body"]])
        component_guides = self.make_round["component_guides"]
        files = lambda role: [item["file"] for item in component_guides(guides, role)]
        self.assertEqual(files("body"), ["guide-01-steps.png", "guide-02-side.png"])
        self.assertEqual(files("leg"), ["guide-01-steps.png", "guide-02-side.png"])
        self.assertEqual(files("head"), ["guide-01-steps.png"])
        # What the worker is told is unchanged in shape.
        view = self.make_round["guide_view"](component_guides(guides, "head"))
        self.assertEqual(view, [{"file": "guide-01-steps.png", "shows": CONTRACT["guides"][0]["shows"],
                                 "path": str(self.run_root / "wish-references/guide-01-steps.png")}])

    def test_without_geometries_every_component_reads_every_guide(self):
        guides, _ = self.make_round["sealed_guides"](self.project)
        self.assertEqual([item["geometries"] for item in guides], [None, None])
        self.assertEqual(self.make_round["component_guides"](guides, "head"), guides)

    def test_a_scoped_guide_is_still_accounted_for(self):
        # guide-steps.json still covers every guide, scoped or not.
        contract = dict(CONTRACT, guides=[dict(CONTRACT["guides"][0], geometries=["body"]),
                                          CONTRACT["guides"][1]])
        self.write_wish(contract)
        failures, report = self.report()
        self.assertIn("guide-01-steps.png: 3 step(s) not accounted for", failures[0])
        self.assertEqual([item["file"] for item in report], ["guide-01-steps.png", "guide-02-side.png"])

    def test_a_guide_the_contract_does_not_list_is_an_error(self):
        contract = dict(CONTRACT, guides=CONTRACT["guides"][:1])
        self.write_wish(contract)
        guides, error = self.make_round["sealed_guides"](self.project)
        self.assertEqual(guides, [])
        self.assertIn("guide-02-side.png", error)

    def test_a_run_without_guides_has_no_report(self):
        self.write_wish(dict(CONTRACT, schema_version=4, guides=None),
                        names=("ref-01-whole.png", "ref-02-body.png"))
        self.assertEqual(self.report(), ([], None))

    # -- accounted for, not judged ----------------------------------------------

    def test_under_motion_checks_every_listed_step_needs_an_entry(self):
        failures, report = self.report()
        self.assertEqual(len(failures), 1)
        self.assertIn("guide-01-steps.png: 3 step(s) not accounted for", failures[0])
        self.assertEqual([item["steps"] for item in report], [[], []])

    def test_without_motion_checks_missing_steps_do_not_fail(self):
        failures, report = self.report(check_motion=False)
        self.assertEqual(failures, [])
        self.assertEqual([item["check_motion"] for item in report], [False, False])

    def test_a_complete_account_passes_and_is_reported_in_contract_order(self):
        self.write_steps({"guides": [{
            "file": "guide-01-steps.png",
            "steps": [
                {"step": STEPS[2], "checked": "state head-up"},
                {"step": STEPS[0], "checked": "car pose on its tail"},
                {"step": STEPS[1], "skipped": "the wing hinge is a static joint in this build "},
            ],
            "conflicts": [{"guide": "four fingers", "contract": "R17: three fingers"}],
        }]})
        failures, report = self.report()
        self.assertEqual(failures, [])
        self.assertEqual([step["step"] for step in report[0]["steps"]], STEPS)
        self.assertEqual(report[0]["steps"][1], {"step": STEPS[1], "skipped": "the wing hinge is a static joint in this build"})
        self.assertEqual(report[0]["conflicts"], [{"guide": "four fingers", "contract": "R17: three fingers"}])
        self.assertEqual(report[1], {"file": "guide-02-side.png", "check_motion": True, "steps": [], "conflicts": []})

    def test_bad_entries_fail_without_judging_the_text(self):
        cases = [
            [{"step": "A step the contract does not list.", "checked": "x"}],
            [{"step": STEPS[0], "checked": "x"}, {"step": STEPS[0], "checked": "y"}],
            [{"step": STEPS[0], "checked": "x", "skipped": "y"}],
            [{"step": STEPS[0], "checked": " "}],
        ]
        for steps in cases:
            with self.subTest(steps=steps):
                self.write_steps({"guides": [{"file": "guide-01-steps.png", "steps": steps}]})
                failures, _ = self.report(check_motion=False)
                self.assertTrue(any("step entries are {step, checked}" in f for f in failures), failures)

    def test_a_record_naming_another_file_or_shaped_wrongly_is_refused(self):
        self.write_steps({"guides": [{"file": "guide-09-other.png"}]})
        failures, report = self.report()
        self.assertIn("not a sealed guide image", failures[0])
        self.assertIsNone(report)
        self.write_steps([])
        self.assertIn('must be {"guides": [...]}', self.report()[0][0])

    def test_a_changed_guide_is_refused(self):
        (self.run_root / "wish-references/guide-01-steps.png").write_bytes(b"redrawn")
        failures, report = self.report()
        self.assertIn("does not match its sealed hash", failures[0])
        self.assertIsNone(report)

    # -- Contract Reviewer --------------------------------------------------------

    def test_guides_wrong_names_only_the_packets_guides(self):
        valid = self.make_round["valid_guides_wrong"]
        files = {"guide-01-steps.png"}
        self.assertTrue(valid([], files))
        self.assertTrue(valid([{"file": "guide-01-steps.png", "where": "panel 3 shows the old boot"}], files))
        self.assertFalse(valid([{"file": "guide-02-side.png", "where": "x"}], files))
        self.assertFalse(valid([{"file": "guide-01-steps.png"}], files))
        self.assertFalse(valid([{"file": "guide-01-steps.png", "where": ""}], files))

    # -- verify_project carries the account ---------------------------------------

    def test_the_verifier_writes_the_account_into_component_acceptance(self):
        verifier = runpy.run_path(str(VERIFIER))
        report = self.project / "measure" / "verification-pipeline.md"
        report.parent.mkdir()
        report.write_text("PASS\n")
        guides = [{"file": "guide-01-steps.png", "check_motion": True, "steps": [], "conflicts": []}]
        verifier["_write_component_acceptance"](report, [], None, [], guides)
        record = json.loads((report.parent / "component-acceptance.json").read_text())
        self.assertEqual(record["guides"], guides)
        verifier["_write_component_acceptance"](report, [], None, [])
        record = json.loads((report.parent / "component-acceptance.json").read_text())
        self.assertNotIn("guides", record)


if __name__ == "__main__":
    unittest.main()
