import hashlib
import tempfile
import unittest
from pathlib import Path

from workshop.artifacts.pack import pack_artifact, seal_artifact
from workshop.playtest.evidence import InspectionResult
from workshop.playtest.inspection import Inspection
from workshop.workflow.clockwork import (
    Clockwork,
    InspectionPolicy,
    Workflow,
    WorkflowSpec,
)
from workshop.errors import TransitionError


CONFIG_SHA256 = "a" * 64


def _inspection(
    root: Path,
    manifest,
    inspection_id: str,
    passed: bool,
) -> InspectionResult:
    evidence = root / (inspection_id + ".json")
    return InspectionResult.create(
        inspection_id,
        passed,
        manifest.artifact_sha256,
        {"passed": passed},
        inspection_id + "-checker",
        "1.0.0",
        CONFIG_SHA256,
        evidence.name,
        hashlib.sha256(evidence.read_bytes()).hexdigest(),
    )


class WorkflowContractHardeningTest(unittest.TestCase):
    def test_inspection_cannot_swap_artifact_after_inspect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            roots = {}
            manifests = {}
            inspections = {}
            for name in ("a", "b"):
                artifact_root = root / name
                artifact_root.mkdir()
                (artifact_root / "piece.stl").write_text(
                    "solid %s\nendsolid %s\n" % (name, name), encoding="utf-8"
                )
                (artifact_root / "quality.json").write_text(
                    '{"passed":true}\n', encoding="utf-8"
                )
                manifest = seal_artifact(
                    artifact_root, created_at="content-addressed"
                )
                roots[name] = artifact_root
                manifests[name] = manifest
                inspections[name] = Inspection(
                    manifest,
                    (_inspection(artifact_root, manifest, "quality", True),),
                )

            spec = WorkflowSpec(
                initial_stage="make",
                stages=("make", "inspect", "pack"),
                edges={"make": ("inspect",), "inspect": ("pack",), "pack": ()},
                required_gates={"inspect": ("quality",)},
                gate_policies={
                    "quality": InspectionPolicy(
                        "quality", "quality-checker", "1.0.0", CONFIG_SHA256
                    )
                },
            )
            workflow = Workflow(spec)
            clockwork = Clockwork(root / "clockwork.sqlite3")
            workflow.register(
                clockwork,
                "artifact-swap",
                artifact_sha256=manifests["a"].artifact_sha256,
            )
            workflow.advance(
                clockwork,
                "artifact-swap",
                "inspect",
                0,
                inspection=inspections["a"],
            )
            packed_b = pack_artifact(roots["b"], root / "b.pack.zip")

            # No loose artifact_sha256 is supplied. The attempted replacement
            # arrives through Inspection B and its matching Pack B.
            with self.assertRaisesRegex(
                TransitionError, "artifact bytes cannot change after Inspect"
            ):
                workflow.advance(
                    clockwork,
                    "artifact-swap",
                    "pack",
                    1,
                    inspection=inspections["b"],
                    packed=packed_b,
                )
            product = clockwork.get_product("artifact-swap")
            self.assertEqual(product["artifact_sha256"], manifests["a"].artifact_sha256)
            self.assertEqual(product["stage"], "inspect")

    def test_optional_failure_is_retained_but_does_not_gate_transition(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            artifact_root = root / "artifact"
            artifact_root.mkdir()
            for inspection_id, passed in (("quality", True), ("form", False)):
                (artifact_root / (inspection_id + ".json")).write_text(
                    '{"passed":%s}\n' % str(passed).lower(), encoding="utf-8"
                )
            manifest = seal_artifact(
                artifact_root, created_at="content-addressed"
            )
            results = tuple(
                _inspection(artifact_root, manifest, inspection_id, passed)
                for inspection_id, passed in (("quality", True), ("form", False))
            )
            inspection = Inspection(manifest, results)
            self.assertFalse(inspection.passed)

            spec = WorkflowSpec(
                initial_stage="make",
                stages=("make", "inspect"),
                edges={"make": ("inspect",), "inspect": ()},
                required_gates={"inspect": ("quality",)},
                gate_policies={
                    "quality": InspectionPolicy(
                        "quality",
                        "quality-checker",
                        "1.0.0",
                        CONFIG_SHA256,
                    )
                },
            )
            workflow = Workflow(spec)
            clockwork = Clockwork(root / "clockwork.sqlite3")
            workflow.register(
                clockwork,
                "optional-feedback",
                artifact_sha256=manifest.artifact_sha256,
            )
            product = workflow.advance(
                clockwork,
                "optional-feedback",
                "inspect",
                0,
                inspection=inspection,
            )

            self.assertEqual(product["stage"], "inspect")
            payload = clockwork.events("optional-feedback")[-1]["payload"]
            self.assertEqual(payload["required_inspection_ids"], ["quality"])
            by_id = {
                result["inspection_id"]: result
                for result in payload["inspections"]
            }
            self.assertTrue(by_id["quality"]["passed"])
            self.assertFalse(by_id["form"]["passed"])


if __name__ == "__main__":
    unittest.main()
