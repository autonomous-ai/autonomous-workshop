"""The CAD skill the imported gate was written against, versus ours.

Design decision D5 requires the difference between the two pinned CAD skills to
be a compatibility *task* rather than an assumption. This is that task, kept as
a standing check so a future skill bump cannot quietly introduce a seventh
difference nobody characterized.

The comparison has two halves. The static half runs everywhere: the recorded
list of differing files, the behavioural consequence of each, and the
adapter-layer compensation ABO makes for it. The dynamic half needs the
upstream tree checked out, and ABO does not vendor a second copy of it to make
a check run — so without it the comparison reports itself unmeasured, which is
the same discipline the manufacturing results are held to.

Point `ABO_REFERENCE_CAD_SKILL` at a checkout of the upstream `skills/cad` to
run the dynamic half.
"""

from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
for candidate in (INVENTOR_ROOT, WORKSHOP_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import cad_compat  # noqa: E402
import config  # noqa: E402
from cad_compat import CadCompatibilityError  # noqa: E402

REFERENCE = os.environ.get("ABO_REFERENCE_CAD_SKILL")


class LockedSkillTest(unittest.TestCase):
    def test_the_gate_is_pointed_at_this_repositorys_locked_skill(self):
        scripts = config.cad_scripts_root()
        self.assertTrue((scripts / "verify_project").is_file())
        self.assertTrue((scripts / "with_budget").is_file())
        # `gen`, `export` and `inspect` are directory packages the skill runs
        # as `python3 <dir>`, which is how the imported gate invokes them.
        for package in ("gen", "export", "inspect"):
            self.assertTrue((scripts / package / "__main__.py").is_file(), package)
        # And at the locked one, not a second copy vendored under the inventor.
        self.assertEqual(scripts, WORKSHOP_ROOT / "skills" / "cad" / "scripts")
        self.assertFalse((INVENTOR_ROOT / "skills").exists())

    def test_repointing_replaces_every_upstream_path_assumption(self):
        sys.path.insert(0, str(config.HARNESS_ROOT))
        import gate  # noqa: E402

        config.install_harness_paths(gate)
        self.assertEqual(gate.ROOT, WORKSHOP_ROOT)
        self.assertTrue(gate.PYTHON.is_file())
        self.assertTrue(gate.CAD.is_dir())
        self.assertTrue(gate.BUDGET.is_file())
        # No `.venv` beside a repository root that does not exist here.
        self.assertNotIn(".venv", str(gate.PYTHON))
        self.assertEqual(gate.python(), str(config.interpreter()))

    def test_the_bed_envelope_comes_from_abo_configuration(self):
        sys.path.insert(0, str(config.HARNESS_ROOT))
        import gate  # noqa: E402

        config.install_harness_paths(gate)
        self.assertEqual(gate.BED, (246.0, 246.0, 251.0))
        self.assertEqual(gate.BED, config.usable_bed_mm())

    def test_running_the_gate_does_not_disturb_the_skill_lock(self):
        completed = subprocess.run(
            [sys.executable, str(WORKSHOP_ROOT / "tools" / "verify_skill_locks.py")],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


class CharacterizationTest(unittest.TestCase):
    def test_every_known_difference_names_its_compensation(self):
        for entry in cad_compat.DIFFERENCES:
            self.assertIn(entry["behavioural"], ("yes", "no"))
            self.assertTrue(entry["difference"].strip())
            self.assertTrue(entry["compensation"].strip())

    def test_the_locked_skill_is_fingerprinted_where_it_differs(self):
        fingerprint = cad_compat.locked_skill_fingerprint()
        self.assertEqual(set(fingerprint), set(cad_compat.DIFFERING_PATHS))
        for path, digest in fingerprint.items():
            self.assertEqual(len(digest), 64, path)

    def test_an_unsupported_compound_spelling_is_refused(self):
        # The locked skill classifies only `Compound(...)`. A part written the
        # other way would build and then be measured as something else.
        with self.assertRaises(CadCompatibilityError) as caught:
            cad_compat.assert_cad_source_supported(
                "result = compound([a, b])\n", "fixture part"
            )
        self.assertIn("Compound", str(caught.exception))
        cad_compat.assert_cad_source_supported(
            "result = Compound([a, b])\n", "fixture part"
        )
        # A mention inside a comment is not a call.
        cad_compat.assert_cad_source_supported(
            "# compound(...) is not supported here\nresult = Compound([a])\n",
            "fixture part",
        )

    def test_without_the_upstream_tree_the_comparison_is_unmeasured(self):
        record = cad_compat.characterization(None)
        self.assertEqual(record["tree_comparison"], "unmeasured")
        self.assertIn("does not vendor", record["tree_comparison_reason"])
        # An unrun comparison never reports agreement.
        self.assertNotIn("observed_differing_paths", record)

    @unittest.skipUnless(
        REFERENCE and Path(REFERENCE).is_dir(),
        "set ABO_REFERENCE_CAD_SKILL to a checkout of the upstream skills/cad",
    )
    def test_the_two_trees_differ_in_exactly_the_characterized_files(self):
        record = cad_compat.characterization(Path(REFERENCE))
        self.assertEqual(record["tree_comparison"], "measured")
        self.assertEqual(
            record["unexpected_differing_paths"],
            [],
            "a difference nobody characterized appeared between the two skills",
        )
        self.assertEqual(
            record["expected_but_identical_paths"],
            [],
            "a characterized difference is gone; the record is now describing "
            "bytes that no longer differ",
        )


class FixtureProjectTest(unittest.TestCase):
    """The gate's own fixture project came across so this can run offline."""

    def test_the_fixture_cad_project_is_present(self):
        project = config.HARNESS_ROOT / "fixtures" / "cad_project"
        self.assertTrue((project / "brief.json").is_file())
        self.assertTrue((project / "bill.json").is_file())
        self.assertTrue((project / "part_slider.step.py").is_file())
        self.assertTrue((project / "part_receiver.step.py").is_file())
        self.assertTrue((project / "measure" / "motion.json").is_file())

    def test_the_imported_fixture_uses_the_spelling_the_locked_skill_refuses(self):
        """The characterized difference, caught on real imported bytes.

        `fixture.step.py` returns `assembly.compound()`. That is a multi-body
        compound to the skill the gate was written against and is not
        classified as one by this repository's locked skill, so the imported
        fixture project cannot be used unchanged as a characterization subject
        here. It is vendored, so it is recorded rather than edited to fit.
        """

        project = config.HARNESS_ROOT / "fixtures" / "cad_project"
        source = (project / "fixture.step.py").read_text(encoding="utf-8")
        with self.assertRaises(CadCompatibilityError):
            cad_compat.assert_cad_source_supported(source, "fixture.step.py")
        recorded = next(
            entry
            for entry in cad_compat.DIFFERENCES
            if entry["path"].endswith("metadata.py")
        )
        self.assertIn("fixture.step.py", recorded["observed"])

    def test_every_other_fixture_source_is_supported(self):
        project = config.HARNESS_ROOT / "fixtures" / "cad_project"
        for source in sorted(project.rglob("*.py")):
            if source.name == "fixture.step.py":
                continue
            cad_compat.assert_cad_source_supported(
                source.read_text(encoding="utf-8"), source.name
            )


if __name__ == "__main__":
    unittest.main()
