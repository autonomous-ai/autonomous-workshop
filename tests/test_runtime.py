import tempfile
import unittest
from pathlib import Path

from inventor_workshop.clockwork import Clockwork, Workflow, WorkflowSpec
from inventor_workshop.errors import AmbiguousSendError
from inventor_workshop.models import Receipt
from inventor_workshop.pack import bundle_artifact
from inventor_workshop.runtime import Runtime


class RuntimeTest(unittest.TestCase):
    def artifact(self, temporary: str):
        root = Path(temporary) / "artifact"
        root.mkdir()
        (root / "thing.txt").write_text("exact bytes\n", encoding="utf-8")
        return bundle_artifact(root, Path(temporary) / "thing.workshop.zip")

    def test_small_default_workflow_and_clockwork_alias(self):
        spec = WorkflowSpec.custom()
        self.assertEqual(tuple(spec.stages), ("make", "playtest", "done"))
        self.assertEqual(Workflow(spec).legal_targets("make"), ("playtest",))
        self.assertEqual(
            Workflow(spec).legal_targets("playtest"), ("done", "make")
        )
        self.assertIs(Clockwork, Runtime)

    def test_runtime_records_before_adapter_and_returns_receipt(self):
        class RecordingAdapter:
            name = "printer"

            def __init__(self, runtime):
                self.runtime = runtime
                self.observed = None

            def execute(self, artifact, request, effect_token):
                self.observed = self.runtime.latest_effect("thing", self.name)
                request["adapter_mutation"] = True
                return Receipt.create(
                    payload_sha256=artifact.payload_sha256,
                    artifact_sha256=artifact.artifact_sha256,
                    adapter=self.name,
                    status="accepted",
                    reference="order-42",
                    details={"effect_token": effect_token},
                )

            def reconcile(self, intent):
                raise AssertionError("successful effects do not reconcile")

        with tempfile.TemporaryDirectory() as temporary:
            artifact = self.artifact(temporary)
            runtime = Runtime(Path(temporary) / "runtime.sqlite3")
            runtime.register_product(
                "thing", "done", artifact_sha256=artifact.artifact_sha256
            )
            adapter = RecordingAdapter(runtime)
            request = {"material": "PLA"}
            receipt = runtime.perform("thing", artifact, adapter, request)
            self.assertEqual(receipt.reference, "order-42")
            self.assertEqual(request, {"material": "PLA"})
            self.assertEqual(adapter.observed["state"], "sending")
            self.assertEqual(
                adapter.observed["effect_token"],
                receipt.details["effect_token"],
            )
            effect = runtime.latest_effect("thing", adapter.name)
            self.assertEqual(effect["state"], "succeeded")
            self.assertEqual(effect["adapter"], "printer")
            self.assertEqual(effect["payload_sha256"], artifact.payload_sha256)
            self.assertEqual(effect["receipt"], receipt)
            self.assertNotIn("door_name", effect)
            self.assertNotIn("stamp", effect)

    def test_runtime_requires_reconciliation_and_reuses_idempotency_token(self):
        class AmbiguousAdapter:
            name = "printer"

            def __init__(self):
                self.calls = 0
                self.tokens = []
                self.prove_no_effect = False
                self.reconciled_intent = None

            def execute(self, artifact, request, effect_token):
                self.calls += 1
                self.tokens.append(effect_token)
                if self.calls == 1:
                    raise TimeoutError("connection lost")
                return Receipt.create(
                    payload_sha256=artifact.payload_sha256,
                    artifact_sha256=artifact.artifact_sha256,
                    adapter=self.name,
                    status="accepted",
                    reference="order-after-proof",
                    details={"effect_token": effect_token},
                )

            def reconcile(self, intent):
                self.reconciled_intent = intent
                if self.prove_no_effect:
                    return None
                raise TimeoutError("readback unavailable")

        with tempfile.TemporaryDirectory() as temporary:
            artifact = self.artifact(temporary)
            runtime = Runtime(Path(temporary) / "runtime.sqlite3")
            runtime.register_product(
                "thing", "done", artifact_sha256=artifact.artifact_sha256
            )
            adapter = AmbiguousAdapter()
            with self.assertRaisesRegex(AmbiguousSendError, "reconcile"):
                runtime.perform("thing", artifact, adapter, {})
            effect = runtime.latest_effect("thing", adapter.name)
            self.assertEqual(effect["state"], "unknown")
            with self.assertRaisesRegex(AmbiguousSendError, "reconcile"):
                runtime.perform("thing", artifact, adapter, {})
            self.assertEqual(adapter.calls, 1)
            adapter.prove_no_effect = True
            self.assertIsNone(runtime.reconcile(effect["id"], adapter))
            self.assertEqual(adapter.reconciled_intent["adapter"], adapter.name)
            self.assertNotIn("door_name", adapter.reconciled_intent)
            receipt = runtime.perform("thing", artifact, adapter, {})
            self.assertEqual(receipt.reference, "order-after-proof")
            self.assertEqual(adapter.calls, 2)
            self.assertEqual(adapter.tokens[0], adapter.tokens[1])


if __name__ == "__main__":
    unittest.main()
