import hashlib
import tempfile
import unittest
from pathlib import Path

from inventor_workshop.cad import (
    CadPart,
    CadProjectManifest,
    CadReleaseBundle,
    PhysicalClaim,
    ValidatorRequirement,
    VerificationCheck,
    VerificationReceipt,
)
from inventor_workshop.creation import CadBuildResult, CreationBrief, Forge, ProductForge
from inventor_workshop.errors import ArtifactError, ContractError, ManifestError
from inventor_workshop.make import MakeResult
from inventor_workshop.models import GateResult


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
        self.taste_path.write_text("# Changed taste\n", encoding="utf-8")
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


class ForgeTest(unittest.TestCase):
    def inventor(self, temporary, taste_bytes=b"# Ada's taste\nTactile and legible.\n"):
        root = Path(temporary) / "ada"
        root.mkdir()
        (root / "TASTE.md").write_bytes(taste_bytes)
        return root

    def test_taste_bound_concept_to_verified_artifact_flow(self):
        with tempfile.TemporaryDirectory() as temporary:
            taste_bytes = b"# Ada's taste\r\nTactile, legible, and surprising.\r\n"
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

    def test_canonical_make_and_inspect_are_distinct_stages(self):
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
            inspection = workbench.inspect(made)
            self.assertEqual(evaluator.calls, 1)
            self.assertEqual(
                verifier.artifact_sha256,
                made.artifact_manifest.artifact_sha256,
            )
            self.assertIsNotNone(inspection.cad_release)
            self.assertEqual(inspection.results[0].inspection_id, "rules-lint")
            self.assertEqual(
                inspection.artifact_sha256,
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
