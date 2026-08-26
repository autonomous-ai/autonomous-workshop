"""ABO's manufacturing measurement: what it measured, and what it did not.

The CAD mesh toolchain is not installed on every machine that runs these
checks, and that is deliberately not worked around. Where it is absent, every
geometry measurement reports itself unmeasured and neither result passes —
which is the rule under test. The measurement logic itself is exercised against
recorded part statistics, so the pass, the fail, and the unmeasured branch are
all reached without a printer.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
for candidate in (
    INVENTOR_ROOT,
    INVENTOR_ROOT / "tests",
    INVENTOR_ROOT / "tests" / "fixtures",
    WORKSHOP_ROOT / "src",
    WORKSHOP_ROOT / "tools",
):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import config  # noqa: E402
import fixture_game as F  # noqa: E402
import manufacturing as MF  # noqa: E402
from concept import AboConcept  # noqa: E402
from concept_fixture import (  # noqa: E402
    FixtureConceptArtist,
    fixture_explode_inspector,
)
from inventor_workshop.jobs import ConceptContext, Made, MakeContext  # noqa: E402
from inventor_workshop.make import Wish  # noqa: E402
from inventor_workshop.taste import load_taste  # noqa: E402
from inventor_workshop.toys import ToyBlueprint  # noqa: E402
from make import AboMake  # noqa: E402
from research import InventedGame  # noqa: E402
from test_make import (  # noqa: E402
    fixture_cad_builder,
    fixture_compiler,
    fixture_step_generator,
)

BLUEPRINT = ToyBlueprint.for_lane("invented-games")


def build_revision(root: Path):
    wish = Wish.create(
        "notchline",
        F.FIXTURE_OBJECTIVE,
        constraints={"lane": "invented-games", "audience": "grown-ups-14-plus"},
        context={"inventor_id": "abo"},
    )
    taste = load_taste(INVENTOR_ROOT)
    concept = AboConcept(
        FixtureConceptArtist(),
        fixture_explode_inspector,
        lambda request: InventedGame(F.fixture_record()),
    )(ConceptContext(wish, taste, BLUEPRINT, 1, root / "concept-1", playtest_rounds=2))
    made = AboMake(fixture_compiler, fixture_cad_builder, fixture_step_generator)(
        MakeContext(
            wish, taste, BLUEPRINT, 1, root / "make-1", playtest_rounds=2,
            concept_images=concept,
        )
    )
    return concept, made


def stats_for(brief, *, scale=1.0, watertight=True, bodies=1, overhang=2.0, bridge=1.0):
    """Recorded part statistics, in the shape the imported gate returns."""

    def _stats(mesh: Path):
        key = mesh.stem
        size = brief.component(key).dimensions_mm
        return {
            "watertight": watertight,
            "bodies": bodies,
            "volume_mm3": 100.0,
            "bbox_mm": [round(value * scale, 1) for value in size],
            "print_orientation": "as-modelled",
            "overhang_pct": overhang,
            "bridge_span_mm": bridge,
        }

    return _stats


class UnmeasuredTest(unittest.TestCase):
    """The rule that does the most work: an unrun check is not a pass."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.mkdtemp()
        cls.concept, cls.made = build_revision(Path(cls.temporary))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temporary, ignore_errors=True)

    def test_absent_slicer_configuration_reports_unmeasured_and_blocks_the_pass(self):
        import os

        cleared = dict(os.environ)
        cleared.pop("ORCASLICER_CLI", None)
        cleared.pop("ORCA_PROFILE", None)
        with mock.patch.dict(os.environ, cleared, clear=True):
            with mock.patch.object(MF, "_stats", stats_for(self.concept.brief)):
                evidence = MF.assemble(
                    "print-test",
                    MF.measure_print(self.made, self.concept.brief),
                    made=self.made,
                    required=MF.PRINT_CHECKS,
                )
        self.assertIn("slicing-under-a-pinned-profile", evidence["unmeasured"])
        self.assertFalse(evidence["passed"])
        detail = next(
            item["detail"]
            for item in evidence["checks"]
            if item["check"] == "slicing-under-a-pinned-profile"
        )
        self.assertIn("does not pass on the strength of the checks that did run", detail)

    def test_an_unmeasured_check_never_counts_as_a_pass(self):
        evidence = MF.assemble(
            "mechanical-test",
            [MF.Measurement("solid-validity", MF.PASSED, "fine")],
            made=self.made,
            required=MF.MECHANICAL_CHECKS,
        )
        # The four checks that were never attempted are reported, not omitted.
        self.assertEqual(len(evidence["checks"]), len(MF.MECHANICAL_CHECKS))
        self.assertFalse(evidence["passed"])
        self.assertEqual(len(evidence["unmeasured"]), 4)

    def test_all_checks_passing_is_the_only_way_to_pass(self):
        evidence = MF.assemble(
            "mechanical-test",
            [MF.Measurement(name, MF.PASSED, "fine") for name in MF.MECHANICAL_CHECKS],
            made=self.made,
            required=MF.MECHANICAL_CHECKS,
        )
        self.assertTrue(evidence["passed"])

    def test_without_the_mesh_toolchain_nothing_geometric_is_claimed(self):
        # This is the state of the machine these checks usually run on.
        if MF._mesh_toolchain() is None:
            self.skipTest("the mesh toolchain is installed here")
        evidence = MF.assemble(
            "mechanical-test",
            MF.measure_mechanical(self.made, self.concept.brief),
            made=self.made,
            required=MF.MECHANICAL_CHECKS,
        )
        self.assertFalse(evidence["passed"])
        self.assertEqual(evidence["failed"], [])
        self.assertIn("solid-validity", evidence["unmeasured"])


class PrintTestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.mkdtemp()
        cls.concept, cls.made = build_revision(Path(cls.temporary))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temporary, ignore_errors=True)

    def test_an_oversize_undeclared_part_fails_and_is_named(self):
        # Scaled past the configured usable envelope in every axis.
        with mock.patch.object(MF, "_stats", stats_for(self.concept.brief, scale=4.0)):
            measurement = MF._bed_fit(
                MF._part_files(self.made), config.usable_bed_mm()
            )
        self.assertEqual(measurement.status, MF.FAILED)
        self.assertIn("board-frame", measurement.parts)
        self.assertIn("board-frame", measurement.detail)
        self.assertIn(config.PRINTER_NAME, measurement.detail)

    def test_a_part_inside_the_envelope_passes(self):
        with mock.patch.object(MF, "_stats", stats_for(self.concept.brief)):
            measurement = MF._bed_fit(
                MF._part_files(self.made), config.usable_bed_mm()
            )
        self.assertEqual(measurement.status, MF.PASSED)

    def test_bed_fit_is_measured_against_the_configured_envelope(self):
        with mock.patch.object(MF, "_stats", stats_for(self.concept.brief)):
            measurement = MF._bed_fit(MF._part_files(self.made), (10.0, 10.0, 10.0))
        self.assertEqual(measurement.status, MF.FAILED)
        self.assertEqual(measurement.values["usable_bed_mm"], [10.0, 10.0, 10.0])

    def test_wall_thickness_is_unmeasured_without_a_nozzle(self):
        import os

        with mock.patch.dict(os.environ, {}, clear=True):
            measurement = MF._wall_thickness(self.concept.brief)
        self.assertEqual(measurement.status, MF.UNMEASURED)

    def test_a_wall_thinner_than_two_extrusions_fails(self):
        import os

        with mock.patch.dict(os.environ, {"ABO_NOZZLE_MM": "2.0"}, clear=True):
            measurement = MF._wall_thickness(self.concept.brief)
        self.assertEqual(measurement.status, MF.FAILED)
        self.assertIn("thinner than", measurement.detail)

    def test_a_wall_that_carries_two_extrusions_passes(self):
        import os

        with mock.patch.dict(os.environ, {"ABO_NOZZLE_MM": "0.4"}, clear=True):
            measurement = MF._wall_thickness(self.concept.brief)
        self.assertEqual(measurement.status, MF.PASSED)

    def test_slicing_is_a_claim_about_slicing_and_not_about_printing(self):
        evidence = MF.assemble(
            "print-test",
            [MF.Measurement(name, MF.PASSED, "fine") for name in MF.PRINT_CHECKS],
            made=self.made,
            required=MF.PRINT_CHECKS,
        )
        self.assertIn("not a claim that anything printed", evidence["claim"])


class MechanicalTestTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.mkdtemp()
        cls.concept, cls.made = build_revision(Path(cls.temporary))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temporary, ignore_errors=True)

    def _with_poses(self, poses):
        product = dict(self.made.product)
        product["poses"] = poses
        return Made(self.made.artifact_root, self.made.artifact_manifest, product)

    def test_two_parts_intersecting_in_a_declared_pose_fail_naming_both(self):
        # Both pillars seated at the same origin: they occupy the same space.
        made = self._with_poses(
            {"assembled": {"pillar-low": [0, 0, 0], "pillar-high": [0, 0, 0]}}
        )
        measurement = MF._interference(made, self.concept.brief)
        self.assertEqual(measurement.status, MF.FAILED)
        self.assertEqual(sorted(measurement.parts), ["pillar-high", "pillar-low"])
        self.assertIn("pillar-high", measurement.detail)
        self.assertIn("pillar-low", measurement.detail)
        self.assertIn("assembled", measurement.detail)

    def test_parts_that_do_not_touch_pass(self):
        made = self._with_poses(
            {"assembled": {"pillar-low": [0, 0, 0], "pillar-high": [100, 100, 0]}}
        )
        measurement = MF._interference(made, self.concept.brief)
        self.assertEqual(measurement.status, MF.PASSED)

    def test_no_declared_pose_is_unmeasured_rather_than_no_interference(self):
        measurement = MF._interference(self.made, self.concept.brief)
        self.assertEqual(measurement.status, MF.UNMEASURED)
        self.assertIn("unmeasured, not absent", measurement.detail)

    def test_a_part_that_is_not_a_closed_solid_fails(self):
        with mock.patch.object(
            MF, "_stats", stats_for(self.concept.brief, watertight=False)
        ):
            measurement = MF._solid_validity(MF._part_files(self.made))
        self.assertEqual(measurement.status, MF.FAILED)
        self.assertIn("not a closed solid", measurement.detail)

    def test_geometry_that_disagrees_with_the_brief_fails(self):
        with mock.patch.object(MF, "_stats", stats_for(self.concept.brief, scale=1.5)):
            measurement = MF._dimensions(MF._part_files(self.made), self.concept.brief)
        self.assertEqual(measurement.status, MF.FAILED)
        self.assertIn("differs from the brief's millimetres", measurement.detail)

    def test_geometry_that_matches_the_brief_passes(self):
        with mock.patch.object(MF, "_stats", stats_for(self.concept.brief)):
            measurement = MF._dimensions(MF._part_files(self.made), self.concept.brief)
        self.assertEqual(measurement.status, MF.PASSED)

    def test_more_than_one_body_per_part_fails(self):
        with mock.patch.object(MF, "_stats", stats_for(self.concept.brief, bodies=3)):
            measurement = MF._mesh_topology(MF._part_files(self.made))
        self.assertEqual(measurement.status, MF.FAILED)
        self.assertIn("disconnected body", measurement.detail)


class SourceBindingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.mkdtemp()
        cls.concept, cls.made = build_revision(Path(cls.temporary))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temporary, ignore_errors=True)

    def test_evidence_names_the_source_closure_it_was_computed_from(self):
        evidence = MF.assemble(
            "mechanical-test", [], made=self.made, required=MF.MECHANICAL_CHECKS
        )
        self.assertEqual(len(evidence["source_closure_sha256"]), 64)
        self.assertTrue(evidence["source_files"])
        MF.assert_sources_current(evidence, self.made)

    def test_stale_source_evidence_is_refused(self):
        evidence = MF.assemble(
            "mechanical-test", [], made=self.made, required=MF.MECHANICAL_CHECKS
        )
        target = self.made.artifact_root / self.made.product["cad"]["marker-lock"]["source"]
        target.write_text(
            target.read_text(encoding="utf-8") + "\n# geometry moved on\n",
            encoding="utf-8",
        )
        with self.assertRaises(MF.StaleEvidence) as caught:
            MF.assert_sources_current(evidence, self.made)
        self.assertIn("has since changed", str(caught.exception))


class ImagesAreNotGeometryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.mkdtemp()
        cls.concept, cls.made = build_revision(Path(cls.temporary))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temporary, ignore_errors=True)

    def test_no_render_appears_in_the_source_closure(self):
        for path in MF.cad_sources(self.made):
            self.assertNotIn(path.suffix.casefold(), MF.IMAGE_SUFFIXES)

    def test_evidence_citing_an_image_is_refused(self):
        evidence = MF.assemble(
            "mechanical-test", [], made=self.made, required=MF.MECHANICAL_CHECKS
        )
        MF.assert_no_image_evidence(evidence)
        smuggled = dict(evidence)
        smuggled["checks"] = list(evidence["checks"]) + [
            {"check": "looks-right", "status": "pass", "detail": "see front.png",
             "values": {}, "parts": []}
        ]
        with self.assertRaises(ValueError) as caught:
            MF.assert_no_image_evidence(smuggled)
        self.assertIn("never offered in support", str(caught.exception))


class FindingsTest(unittest.TestCase):
    def test_a_failed_measurement_blocks(self):
        evidence = {
            "checks": [
                {"check": "bed-fit", "status": MF.FAILED, "detail": "too big",
                 "values": {}, "parts": ["board-frame"]}
            ]
        }
        found = MF.findings(evidence)
        self.assertEqual(found[0]["severity"], "block")
        self.assertEqual(found[0]["parts"], ["board-frame"])

    def test_an_unmeasured_check_is_reported_as_something_to_improve(self):
        evidence = {
            "checks": [
                {"check": "slicing-under-a-pinned-profile", "status": MF.UNMEASURED,
                 "detail": "no profile", "values": {}, "parts": []}
            ]
        }
        found = MF.findings(evidence)
        self.assertEqual(found[0]["severity"], "improve")
        self.assertIn("unmeasured", found[0]["finding"])

    def test_a_passing_measurement_produces_no_finding(self):
        evidence = {
            "checks": [
                {"check": "bed-fit", "status": MF.PASSED, "detail": "fits",
                 "values": {}, "parts": []}
            ]
        }
        self.assertEqual(MF.findings(evidence), [])


if __name__ == "__main__":
    unittest.main()
