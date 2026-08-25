import hashlib
import tempfile
import unittest
import zipfile
from pathlib import Path

from workshop.artifacts.pack import pack_artifact, seal_artifact
from workshop.errors import ContractError
from workshop.playtest.evidence import InspectionResult
from workshop.playtest.inspection import Inspection
from workshop.workflow.clockwork import (
    Clockwork,
    InspectionPolicy,
    Workflow,
    WorkflowSpec,
)


CONFIG_SHA256 = "a" * 64


class SeparateInspectionEvidenceTest(unittest.TestCase):
    def test_product_only_pack_retains_separate_inspection_binding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            product_root = root / "product"
            evidence_root = root / "inspection-evidence"
            product_root.mkdir()
            evidence_root.mkdir()
            (product_root / "piece.stl").write_text(
                "solid piece\nendsolid piece\n", encoding="utf-8"
            )
            (product_root / "rules.md").write_text(
                "# Rules\n\nFit the piece.\n", encoding="utf-8"
            )
            evidence = evidence_root / "quality.json"
            evidence.write_text(
                '{"passed":true,"reviewer":"fixture"}\n',
                encoding="utf-8",
            )

            product_manifest = seal_artifact(
                product_root, created_at="content-addressed"
            )
            evidence_manifest = seal_artifact(
                evidence_root, created_at="content-addressed"
            )
            result = InspectionResult.create(
                "quality",
                True,
                product_manifest.artifact_sha256,
                {"passed": True},
                "independent-quality",
                "1.0.0",
                CONFIG_SHA256,
                "quality.json",
                hashlib.sha256(evidence.read_bytes()).hexdigest(),
            )
            inspection = Inspection(
                product_manifest,
                (result,),
                evidence_manifest=evidence_manifest,
            )

            self.assertNotEqual(
                inspection.artifact_sha256,
                inspection.evidence_artifact_sha256,
            )
            self.assertEqual(
                inspection.to_dict()["evidence_artifact_sha256"],
                evidence_manifest.artifact_sha256,
            )

            spec = WorkflowSpec(
                initial_stage="make",
                stages=("make", "inspect", "pack"),
                edges={"make": ("inspect",), "inspect": ("pack",), "pack": ()},
                required_gates={"inspect": ("quality",)},
                gate_policies={
                    "quality": InspectionPolicy(
                        "quality",
                        "independent-quality",
                        "1.0.0",
                        CONFIG_SHA256,
                    )
                },
            )
            workflow = Workflow(spec)
            clockwork = Clockwork(root / "clockwork.sqlite3")
            workflow.register(
                clockwork,
                "separate-evidence",
                artifact_sha256=product_manifest.artifact_sha256,
            )
            inspected = workflow.advance(
                clockwork,
                "separate-evidence",
                "inspect",
                0,
                inspection=inspection,
            )
            self.assertEqual(
                inspected["artifact_sha256"], product_manifest.artifact_sha256
            )
            inspected_event = clockwork.events("separate-evidence")[-1]
            self.assertEqual(
                inspected_event["payload"]["inspection_evidence_sha256"],
                evidence_manifest.artifact_sha256,
            )

            packed = pack_artifact(product_root, root / "product.pack.zip")
            self.assertEqual(
                packed.artifact_sha256, product_manifest.artifact_sha256
            )
            with zipfile.ZipFile(packed.path) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"piece.stl", "rules.md", "_inventor-artifact.json"},
                )
            packed_product = workflow.advance(
                clockwork,
                "separate-evidence",
                "pack",
                1,
                packed=packed,
            )
            self.assertEqual(
                packed_product["artifact_sha256"], product_manifest.artifact_sha256
            )

    def test_evidence_is_checked_against_the_selected_evidence_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            product_root = root / "product"
            other_evidence_root = root / "other-evidence"
            product_root.mkdir()
            other_evidence_root.mkdir()
            evidence = product_root / "quality.json"
            evidence.write_text('{"passed":true}\n', encoding="utf-8")
            (other_evidence_root / "different.json").write_text(
                '{}\n', encoding="utf-8"
            )
            product_manifest = seal_artifact(
                product_root, created_at="content-addressed"
            )
            other_evidence_manifest = seal_artifact(
                other_evidence_root, created_at="content-addressed"
            )
            result = InspectionResult.create(
                "quality",
                True,
                product_manifest.artifact_sha256,
                {"passed": True},
                "independent-quality",
                "1.0.0",
                CONFIG_SHA256,
                "quality.json",
                hashlib.sha256(evidence.read_bytes()).hexdigest(),
            )

            # Compatibility mode still accepts evidence sealed with the
            # product. Selecting another evidence artifact changes the trust
            # boundary and therefore rejects this result.
            self.assertEqual(
                Inspection(product_manifest, (result,)).evidence_artifact_sha256,
                product_manifest.artifact_sha256,
            )
            with self.assertRaisesRegex(
                ContractError, "sealed evidence artifact"
            ):
                Inspection(
                    product_manifest,
                    (result,),
                    evidence_manifest=other_evidence_manifest,
                )


if __name__ == "__main__":
    unittest.main()
