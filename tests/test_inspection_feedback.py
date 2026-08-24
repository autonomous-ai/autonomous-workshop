import hashlib
import tempfile
import unittest
from pathlib import Path

from inventor_workshop import (
    Clockwork,
    Inspection,
    InspectionPolicy,
    InspectionResult,
    Workflow,
    WorkflowSpec,
    seal_artifact,
)
from inventor_workshop.errors import TransitionError


CONFIG_SHA256 = "a" * 64


class InspectionFeedbackTest(unittest.TestCase):
    def test_failed_inspection_is_feedback_but_cannot_advance(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            evidence = root / "evidence/printability.json"
            evidence.parent.mkdir(parents=True)
            evidence.write_text(
                '{"passed":false,"reason":"wall too thin"}\n',
                encoding="utf-8",
            )
            (root / "piece.stl").write_text(
                "solid piece\nendsolid piece\n", encoding="utf-8"
            )
            manifest = seal_artifact(root, created_at="content-addressed")
            result = InspectionResult.create(
                "printability",
                False,
                manifest.artifact_sha256,
                {"passed": False, "reason": "wall too thin"},
                "mesh-check",
                "1.0.0",
                CONFIG_SHA256,
                "evidence/printability.json",
                hashlib.sha256(evidence.read_bytes()).hexdigest(),
            )
            inspection = Inspection(manifest, (result,))
            self.assertFalse(inspection.passed)
            self.assertFalse(inspection.to_dict()["passed"])

            spec = WorkflowSpec(
                initial_stage="make",
                stages=("make", "inspect"),
                edges={"make": ("inspect",), "inspect": ()},
                required_gates={"inspect": ("printability",)},
                gate_policies={
                    "printability": InspectionPolicy(
                        "printability", "mesh-check", "1.0.0", CONFIG_SHA256
                    )
                },
            )
            workflow = Workflow(spec)
            clockwork = Clockwork(Path(temporary) / "clockwork.sqlite3")
            workflow.register(
                clockwork,
                "piece",
                artifact_sha256=manifest.artifact_sha256,
            )
            with self.assertRaisesRegex(
                TransitionError, "did not pass required results"
            ):
                workflow.advance(
                    clockwork,
                    "piece",
                    "inspect",
                    0,
                    inspection=inspection,
                )
            self.assertEqual(clockwork.get_product("piece")["stage"], "make")


if __name__ == "__main__":
    unittest.main()
