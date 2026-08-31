import tempfile
import unittest
from pathlib import Path

from workshop.artifacts import build_artifact_manifest
from workshop.errors import ArtifactError, ContractError
from workshop.invent.native import NativeInvented
from workshop.make.revision import (
    MAKE_INVENT_REVISION_INVALIDATES,
    MakeInventRevisionFeedback,
    NativeMakeInventRevision,
)
from workshop.match.native import MatchRankingEntry, NativeMatchAssignment
from workshop.product import ToyBlueprint


class MakeInventRevisionTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.assignment = NativeMatchAssignment(
            wish_sha256="a" * 64,
            inventor_roster_sha256="b" * 64,
            selected_inventor_id="tess-loop",
            selected_agent_path=".codex/agents/tess-loop.toml",
            selected_agent_sha256="c" * 64,
            selected_source_manifest_sha256="d" * 64,
            selected_taste_sha256="e" * 64,
            blueprint_sha256=ToyBlueprint().sha256,
            ranking=(
                MatchRankingEntry(
                    "tess-loop", "Best fit for tactile geometric interaction."
                ),
            ),
        )
        self.invented = NativeInvented(
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            taste_sha256=self.assignment.selected_taste_sha256,
            blueprint_sha256=self.assignment.blueprint_sha256,
            concept={"title": "Star River", "summary": "A folding constellation."},
            research={"method": "bounded inspection"},
        )
        self.evidence_root = (
            self.root / "artifacts/make/r0001/revision-evidence"
        )
        self.evidence_root.mkdir(parents=True)
        (self.evidence_root / "geometry-check.json").write_text(
            '{"clearance_mm":-0.3,"passed":false}\n', encoding="utf-8"
        )

    def request(self):
        manifest = build_artifact_manifest(
            self.evidence_root, created_at="content-addressed"
        )
        feedback = MakeInventRevisionFeedback(
            code="forced-overlap",
            area="keel-index-interface",
            severity="block",
            finding="The sealed dimensions force a 0.3 mm overlap.",
            change="Move the index capsule or revise its dimensions.",
            evidence_refs=("geometry-check.json",),
            invalidates=MAKE_INVENT_REVISION_INVALIDATES,
        )
        return NativeMakeInventRevision(
            round=1,
            wish_sha256=self.assignment.wish_sha256,
            assignment_sha256=self.assignment.assignment_sha256,
            invented_sha256=self.invented.invented_sha256,
            evidence_root="artifacts/make/r0001/revision-evidence",
            evidence_manifest=manifest,
            feedback=(feedback,),
        )

    def test_round_trip_binds_upstream_and_exact_evidence(self):
        request = self.request()
        rebuilt = NativeMakeInventRevision.from_mapping(request.to_dict())
        rebuilt.assert_context(self.assignment, self.invented, expected_round=1)
        manifest = rebuilt.validate_evidence_tree(self.root)

        self.assertEqual(
            manifest.artifact_sha256,
            request.evidence_manifest.artifact_sha256,
        )
        self.assertEqual(rebuilt.feedback[0].code, "forced-overlap")

    def test_tampered_evidence_or_upstream_binding_fails_closed(self):
        request = self.request()
        (self.evidence_root / "geometry-check.json").write_text(
            '{"passed":true}\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(ArtifactError, "differs from its manifest"):
            request.validate_evidence_tree(self.root)
        with self.assertRaisesRegex(ContractError, "different Workshop inputs"):
            request.assert_context(self.assignment, self.invented, expected_round=2)

    def test_schema_v2_binds_standing_concept_and_effect(self):
        legacy = self.request()
        request = NativeMakeInventRevision(
            round=legacy.round,
            wish_sha256=legacy.wish_sha256,
            assignment_sha256=legacy.assignment_sha256,
            invented_sha256=legacy.invented_sha256,
            evidence_root=legacy.evidence_root,
            evidence_manifest=legacy.evidence_manifest,
            feedback=legacy.feedback,
            schema_version=2,
            concept_sha256="8" * 64,
            concept_effect_sha256="9" * 64,
        )
        rebuilt = NativeMakeInventRevision.from_mapping(request.to_dict())
        rebuilt.assert_context(
            self.assignment,
            self.invented,
            expected_round=1,
            expected_concept_sha256="8" * 64,
            expected_concept_effect_sha256="9" * 64,
        )
        with self.assertRaisesRegex(ContractError, "different Concept"):
            rebuilt.assert_context(
                self.assignment,
                self.invented,
                expected_round=1,
                expected_concept_sha256="7" * 64,
                expected_concept_effect_sha256="9" * 64,
            )

    def test_feedback_must_block_and_cite_manifest_evidence(self):
        with self.assertRaisesRegex(ContractError, "build-blocking"):
            MakeInventRevisionFeedback(
                code="preference",
                area="color",
                severity="improve",
                finding="A different color could be nicer.",
                change="Change color.",
                evidence_refs=("geometry-check.json",),
            )

        request = self.request().to_dict()
        request["feedback"][0]["evidence_refs"] = ["absent.json"]
        request["feedback_sha256"] = "0" * 64
        request["revision_request_sha256"] = "0" * 64
        with self.assertRaisesRegex(ContractError, "absent evidence"):
            NativeMakeInventRevision.from_mapping(request)


if __name__ == "__main__":
    unittest.main()
