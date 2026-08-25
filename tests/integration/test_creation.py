import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path

from workshop.make.cad import (
    CadPart,
    CadProjectManifest,
    CadReleaseBundle,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
)
from workshop.artifacts.core import build_artifact_manifest
from workshop.make.service import CadBuildResult, CreationBrief, Forge, ProductForge
from workshop.errors import ArtifactError, ContractError, ManifestError
from workshop.playtest.inspection import Inspection
from workshop.workflow.clockwork import Clockwork, Workflow, WorkflowSpec
from workshop.make.service import MakeResult
from workshop.playtest.evidence import GateResult


CONFIG_SHA256 = "b" * 64
PROFILE_SHA256 = "c" * 64
SKILL_SHA256 = "d" * 64

CHECKS = {
    "deterministic": {
        "manifest": {"inventory_valid": True},
        "brep": {"valid_solids": 1, "invalid_solids": 0},
        "mesh-topology": {"watertight_parts": 1, "non_manifold_edges": 0},
        "dimensions": {"measured_parts": 1, "out_of_tolerance": 0},
        "interference": {"poses_tested": 3, "forbidden_intersections": 0},
        "bed-packing": {"beds_used": 1, "out_of_bounds_parts": 0},
        "slicer": {
            "profiles_checked": 1,
            "slicer_errors": 0,
            "support_material_grams": 0.0,
        },
    },
    "independent-review": {
        "form-review": {"views_reviewed": 3, "blockers": 0},
        "safety": {"hazards_found": 0, "review_scope": "tabletop use"},
    },
}


def file_sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FakeAgent:
    def __init__(self):
        self.role = None
        self.request = None
        self.budget_micros = None

    def run(self, role, request, budget_micros):
        self.role = role
        self.request = request
        self.budget_micros = budget_micros
        return {
            "title": "River Loom",
            "mechanism": "interlocking tactile tiles",
            "taste_sha256": request["taste"]["sha256"],
        }


class TasteMutatingAgent(FakeAgent):
    def __init__(self, taste_path):
        super().__init__()
        self.taste_path = taste_path

    def run(self, role, request, budget_micros):
        result = super().run(role, request, budget_micros)
        self.taste_path.write_text(
            "---\n"
            "name: Ada\n"
            "description: Makes tactile, legible games with surprising table presence.\n"
            "---\n\n"
            "# Changed taste\n",
            encoding="utf-8",
        )
        return result


class FakeCad:
    def __init__(self):
        self.brief = None
        self.concept = None

    def build(self, brief, concept, workspace):
        self.brief = brief
        self.concept = concept
        root = workspace / "artifact"
        (root / "parts").mkdir(parents=True)
        (root / "evidence").mkdir()
        (root / "parts/tile.step.py").write_text("def gen_step(): pass\n", encoding="utf-8")
        (root / "parts/tile.step").write_bytes(b"ISO-10303-21;\nEND-ISO-10303-21;\n")
        (root / "parts/tile.stl").write_bytes(b"solid tile\nendsolid tile\n")
        for checks in CHECKS.values():
            for check_id, measurements in checks.items():
                (root / "evidence" / (check_id + ".json")).write_text(
                    repr(measurements) + "\n", encoding="utf-8"
                )
        (root / "evidence/rules.json").write_text(
            '{"rules_consistent":true}\n', encoding="utf-8"
        )
        (root / "evidence/cad.json").write_text(
            '{"cad_checks":"passed"}\n', encoding="utf-8"
        )
        return CadBuildResult(
            1,
            brief.product_id,
            root.resolve(),
            {"adapter": "deterministic-fake", "concept": concept["title"]},
        )


class FakeVerifier:
    def __init__(self, evidence_override=None):
        self.artifact_sha256 = None
        self.evidence_override = evidence_override

    def verify(self, artifact_root, artifact_sha256):
        self.artifact_sha256 = artifact_sha256
        evidence_files = {
            "evidence/%s.json" % check_id: file_sha256(
                artifact_root / "evidence" / (check_id + ".json")
            )
            for checks in CHECKS.values()
            for check_id in checks
        }
        if self.evidence_override is not None:
            evidence_files["evidence/manifest.json"] = self.evidence_override
        manifest = CadProjectManifest(
            schema_version=1,
            project_id="river-loom",
            artifact_sha256=artifact_sha256,
            engine={"name": "fake-build123d", "version": "1.0.0"},
            skill_versions={"cad": SKILL_SHA256},
            parts=(
                CadPart(
                    "tile",
                    "Tile",
                    4,
                    "parts/tile.step.py",
                    "parts/tile.step",
                    "parts/tile.stl",
                    "PLA",
                    (0, 0, 0),
                ),
            ),
            assemblies=(),
            fits=(),
            motions=(),
            print_profile={"process": "FDM", "profile_sha256": PROFILE_SHA256},
            evidence_files=evidence_files,
            physical_claims=(
                PhysicalClaim(
                    "long-term-wear",
                    "surface remains legible after repeated play",
                    False,
                    "held",
                ),
            ),
        )
        requirements = []
        receipts = []
        for substrate, checks in CHECKS.items():
            validator = substrate + "-validator"
            requirements.append(
                ValidatorRequirement(
                    validator,
                    "1.0.0",
                    CONFIG_SHA256,
                    substrate,
                    tuple(checks),
                )
            )
            receipts.append(
                VerificationReceipt.create(
                    artifact_sha256,
                    validator,
                    "1.0.0",
                    CONFIG_SHA256,
                    substrate,
                    tuple(
                        VerificationCheck(
                            check_id,
                            "passed",
                            measurements,
                            "evidence/%s.json" % check_id,
                            evidence_files["evidence/%s.json" % check_id],
                        )
                        for check_id, measurements in checks.items()
                    ),
                )
            )
        return CadReleaseBundle(manifest, tuple(receipts), tuple(requirements))


class FakeEvaluator:
    def __init__(self, artifact_override=None, mutate=False, passed=True):
        self.artifact_override = artifact_override
        self.mutate = mutate
        self.passed = passed
        self.calls = 0

    def evaluate(self, artifact_root, artifact_sha256):
        self.calls += 1
        evidence = artifact_root / "evidence/rules.json"
        result = GateResult.create(
            "rules-lint",
            self.passed,
            self.artifact_override or artifact_sha256,
            {"rules_consistent": self.passed},
            "rules-checker",
            "1.0.0",
            CONFIG_SHA256,
            "evidence/rules.json",
            file_sha256(evidence),
        )
        if self.mutate:
            (artifact_root / "late-file.txt").write_text("late\n", encoding="utf-8")
        return (result,)


class SeparateEvidenceEvaluator:
    def __init__(self):
        self.evidence_path = None

    def evaluate(self, artifact_root, artifact_sha256):
        if self.evidence_path is None:
            raise AssertionError("test must prepare the separate evidence first")
        return (
            GateResult.create(
                "quality",
                True,
                artifact_sha256,
                {"reviewed": True},
                "quality-reviewer",
                "1.0.0",
                CONFIG_SHA256,
                "reviews/quality.json",
                file_sha256(self.evidence_path),
            ),
        )


class ForgeTest(unittest.TestCase):
    def inventor(
        self,
        temporary,
        taste_bytes=(
            b"---\n"
            b"name: Ada\n"
            b"description: Makes tactile, legible games with surprising table presence.\n"
            b"---\n\n"
            b"# Ada's taste\nTactile and legible.\n"
        ),
    ):
        root = Path(temporary) / "ada"
        root.mkdir()
        (root / "TASTE.md").write_bytes(taste_bytes)
        return root

    def test_taste_bound_concept_to_verified_artifact_flow(self):
        with tempfile.TemporaryDirectory() as temporary:
            taste_bytes = (
                b"---\r\n"
                b"name: Ada\r\n"
                b"description: Makes tactile, legible games with surprising table presence.\r\n"
                b"---\r\n\r\n"
                b"# Ada's taste\r\nTactile, legible, and surprising.\r\n"
            )
            inventor = self.inventor(temporary, taste_bytes)
            agent = FakeAgent()
            cad = FakeCad()
            verifier = FakeVerifier()
            forge = Forge(agent, cad, verifier, FakeEvaluator())
            brief = CreationBrief.create(
                "river-loom",
                "Create a printable strategy game.",
                {"bed_mm": [220, 220, 250]},
            )

            result = forge.create(
                brief,
                inventor,
                Path(temporary) / "run",
                budget_micros=250_000,
            )

            taste_sha256 = hashlib.sha256(taste_bytes).hexdigest()
            self.assertEqual(agent.role, "concept")
            self.assertEqual(agent.request["taste"]["content"].encode("utf-8"), taste_bytes)
            self.assertEqual(agent.request["taste"]["sha256"], taste_sha256)
            self.assertEqual(agent.budget_micros, 250_000)
            self.assertIs(cad.brief, brief)
            self.assertEqual(cad.concept["taste_sha256"], taste_sha256)
            self.assertEqual(verifier.artifact_sha256, result.artifact_manifest.artifact_sha256)
            self.assertEqual(
                result.cad_release.manifest.artifact_sha256,
                result.artifact_manifest.artifact_sha256,
            )
            self.assertEqual(
                result.gates[0].artifact_sha256,
                result.artifact_manifest.artifact_sha256,
            )
            self.assertEqual(result.to_dict()["taste"]["sha256"], taste_sha256)

    def test_canonical_make_and_playtest_are_distinct_stages(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            evaluator = FakeEvaluator()
            verifier = FakeVerifier()
            workbench = Forge(
                FakeAgent(), FakeCad(), verifier, evaluator
            )
            wish = CreationBrief.create("game", "Create a game.")
            made = workbench.make(
                wish,
                inventor,
                Path(temporary) / "run",
                1,
            )
            self.assertEqual(evaluator.calls, 0)
            self.assertIsNone(verifier.artifact_sha256)
            self.assertIsNone(made.cad_release)
            self.assertEqual(made.inspections, ())
            self.assertEqual(made.to_dict()["inspections"], [])
            playtest = workbench.playtest(made)
            self.assertEqual(evaluator.calls, 1)
            self.assertEqual(
                verifier.artifact_sha256,
                made.artifact_manifest.artifact_sha256,
            )
            self.assertIsNotNone(playtest.cad_release)
            self.assertEqual(playtest.results[0].inspection_id, "rules-lint")
            self.assertEqual(
                playtest.artifact_sha256,
                made.artifact_manifest.artifact_sha256,
            )

            legacy = MakeResult(
                schema_version=made.schema_version,
                brief=made.wish,
                taste=made.taste,
                concept=made.concept,
                concept_sha256=made.concept_sha256,
                cad_build=made.cad_build,
                artifact_manifest=made.artifact_manifest,
                cad_release=made.cad_release,
                gates=(),
            )
            self.assertIs(legacy.wish, legacy.brief)
            self.assertIs(legacy.inspections, legacy.gates)
            self.assertEqual(set(legacy.to_dict()) & {"brief", "gates"}, set())

    def test_workbench_inspect_accepts_a_separate_evidence_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            inventor = self.inventor(temporary)
            evaluator = SeparateEvidenceEvaluator()
            workbench = Forge(
                FakeAgent(), FakeCad(), FakeVerifier(), evaluator
            )
            made = workbench.make(
                CreationBrief.create("game", "Create a game."),
                inventor,
                root / "run",
                1,
            )

            evidence_root = root / "inspection-evidence"
            shutil.copytree(
                made.cad_build.artifact_root / "evidence",
                evidence_root / "evidence",
            )
            review = evidence_root / "reviews/quality.json"
            review.parent.mkdir()
            review.write_text(
                '{"passed":true,"reviewer":"fixture"}\n', encoding="utf-8"
            )
            evaluator.evidence_path = review
            evidence_manifest = build_artifact_manifest(
                evidence_root, created_at="content-addressed"
            )

            inspection = workbench.inspect(
                made, evidence_manifest=evidence_manifest
            )
            self.assertEqual(
                inspection.evidence_artifact_sha256,
                evidence_manifest.artifact_sha256,
            )
            self.assertFalse(
                (made.cad_build.artifact_root / "reviews/quality.json").exists()
            )
            self.assertEqual(
                inspection.results[0].evidence_ref, "reviews/quality.json"
            )

    def test_workbench_rejects_untyped_evidence_before_running_doors(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            evaluator = FakeEvaluator()
            verifier = FakeVerifier()
            workbench = Forge(FakeAgent(), FakeCad(), verifier, evaluator)
            made = workbench.make(
                CreationBrief.create("game", "Create a game."),
                inventor,
                Path(temporary) / "run",
                1,
            )
            with self.assertRaisesRegex(ContractError, "must be an ArtifactManifest"):
                workbench.inspect(made, evidence_manifest={})
            self.assertEqual(evaluator.calls, 0)
            self.assertIsNone(verifier.artifact_sha256)

    def test_legacy_create_retains_failed_inspection_feedback(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            workbench = Forge(
                FakeAgent(), FakeCad(), FakeVerifier(), FakeEvaluator(passed=False)
            )
            result = workbench.create(
                CreationBrief.create("game", "Create a game."),
                inventor,
                Path(temporary) / "run",
                1,
            )
            self.assertEqual(len(result.inspections), 1)
            self.assertFalse(result.inspections[0].passed)

    def test_make_result_binds_cad_report_and_release_as_distinct_hashes(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            verifier = FakeVerifier()
            workbench = Forge(
                FakeAgent(), FakeCad(), verifier, FakeEvaluator()
            )
            made = workbench.make(
                CreationBrief.create("game", "Create a game."),
                inventor,
                Path(temporary) / "run",
                1,
            )
            release = verifier.verify(
                made.cad_build.artifact_root,
                made.artifact_manifest.artifact_sha256,
            )
            report_digest = file_sha256(
                made.cad_build.artifact_root / "evidence/cad.json"
            )
            self.assertNotEqual(report_digest, release.sha256)
            cad_result = GateResult.create(
                "cad",
                True,
                made.artifact_manifest.artifact_sha256,
                {"cad_release_sha256": release.sha256},
                "cad-review",
                "1.0.0",
                CONFIG_SHA256,
                "evidence/cad.json",
                report_digest,
            )

            result = MakeResult(
                1,
                wish=made.wish,
                taste=made.taste,
                concept=made.concept,
                concept_sha256=made.concept_sha256,
                cad_build=made.cad_build,
                artifact_manifest=made.artifact_manifest,
                cad_release=release,
                inspections=(cad_result,),
            )
            self.assertEqual(result.inspections, (cad_result,))

            detached_release = GateResult.create(
                "cad",
                True,
                made.artifact_manifest.artifact_sha256,
                {"cad_release_sha256": "e" * 64},
                "cad-review",
                "1.0.0",
                CONFIG_SHA256,
                "evidence/cad.json",
                report_digest,
            )
            with self.assertRaisesRegex(ContractError, "validated release bundle"):
                MakeResult(
                    1,
                    wish=made.wish,
                    taste=made.taste,
                    concept=made.concept,
                    concept_sha256=made.concept_sha256,
                    cad_build=made.cad_build,
                    artifact_manifest=made.artifact_manifest,
                    cad_release=release,
                    inspections=(detached_release,),
                )

    def test_canonical_board_game_workflow_accepts_real_cad_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            verifier = FakeVerifier()
            workbench = Forge(
                FakeAgent(), FakeCad(), verifier, FakeEvaluator()
            )
            made = workbench.make(
                CreationBrief.create("river-loom", "Create a board game."),
                inventor,
                Path(temporary) / "run",
                1,
            )
            release = verifier.verify(
                made.cad_build.artifact_root,
                made.artifact_manifest.artifact_sha256,
            )
            spec = WorkflowSpec.board_game()
            results = []
            for inspection_id in spec.required_gates["playtest"]:
                policy = spec.gate_policies[inspection_id]
                evidence_ref = (
                    "evidence/cad.json"
                    if inspection_id == "cad"
                    else "evidence/rules.json"
                )
                evidence = (
                    {"cad_release_sha256": release.sha256}
                    if inspection_id == "cad"
                    else {"passed": True}
                )
                results.append(
                    GateResult.create(
                        inspection_id,
                        True,
                        made.artifact_manifest.artifact_sha256,
                        evidence,
                        policy.evaluator,
                        policy.evaluator_version,
                        policy.config_sha256,
                        evidence_ref,
                        file_sha256(made.cad_build.artifact_root / evidence_ref),
                    )
                )
            inspection = Inspection(
                made.artifact_manifest,
                tuple(results),
                release,
            )
            clockwork = Clockwork(Path(temporary) / "clockwork.sqlite3")
            workflow = Workflow(spec)
            workflow.register(
                clockwork,
                made.wish.product_id,
                artifact_sha256=made.artifact_manifest.artifact_sha256,
            )

            playtested = workflow.advance(
                clockwork,
                made.wish.product_id,
                "playtest",
                0,
                playtest=inspection,
            )
            self.assertEqual(playtested["stage"], "playtest")
            completed = workflow.advance(
                clockwork,
                made.wish.product_id,
                "done",
                1,
            )
            self.assertEqual(completed["stage"], "done")
            event = clockwork.events(made.wish.product_id)[-1]
            self.assertEqual(event["payload"]["inspections"], [])
            self.assertNotIn("pack_sha256", event["payload"])

    def test_gate_for_other_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            forge = Forge(
                FakeAgent(), FakeCad(), FakeVerifier(), FakeEvaluator(artifact_override="f" * 64)
            )
            with self.assertRaisesRegex(ContractError, "different artifact"):
                forge.create(
                    CreationBrief.create("game", "Create a game."),
                    inventor,
                    Path(temporary) / "run",
                    1,
                )

    def test_cad_evidence_not_in_sealed_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            forge = Forge(
                FakeAgent(),
                FakeCad(),
                FakeVerifier(evidence_override="e" * 64),
                FakeEvaluator(),
            )
            with self.assertRaisesRegex(ContractError, "CAD evidence"):
                forge.create(
                    CreationBrief.create("game", "Create a game."),
                    inventor,
                    Path(temporary) / "run",
                    1,
                )

    def test_taste_change_during_concept_generation_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            forge = Forge(
                TasteMutatingAgent(inventor / "TASTE.md"),
                FakeCad(),
                FakeVerifier(),
                FakeEvaluator(),
            )
            with self.assertRaisesRegex(ManifestError, "changed during Make"):
                forge.create(
                    CreationBrief.create("game", "Create a game."),
                    inventor,
                    Path(temporary) / "run",
                    1,
                )

    def test_adapter_cannot_mutate_artifact_after_sealing(self):
        with tempfile.TemporaryDirectory() as temporary:
            inventor = self.inventor(temporary)
            forge = Forge(
                FakeAgent(), FakeCad(), FakeVerifier(), FakeEvaluator(mutate=True)
            )
            with self.assertRaisesRegex(ArtifactError, "changed during"):
                forge.create(
                    CreationBrief.create("game", "Create a game."),
                    inventor,
                    Path(temporary) / "run",
                    1,
                )

    def test_product_forge_remains_a_compatibility_alias(self):
        self.assertIs(ProductForge, Forge)


if __name__ == "__main__":
    unittest.main()
