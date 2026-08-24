import hashlib
import importlib
import json
import tempfile
import unittest
from pathlib import Path

import inventor_workshop
from inventor_workshop import (
    CadDoor,
    CadInspectionDoor,
    Clockwork,
    DeliveryDoor,
    Inspection,
    InspectionDoor,
    InspectionPolicy,
    InspectionResult,
    ModelDoor,
    PackedArtifact,
    Playtest,
    PlaytestPolicy,
    PlaytestResult,
    SendResult,
    Sender,
    ShopDoor,
    Stamp,
    Wish,
    Workbench,
    Workflow,
    WorkflowSpec,
    discover_schemas,
    inspect_pack,
    pack_artifact,
    plan_pack,
    seal_artifact,
)
from inventor_workshop.errors import (
    AmbiguousSendError,
    ArtifactError,
    ContractError,
    TransitionError,
)


SHA = "a" * 64


class WorkshopApiTest(unittest.TestCase):
    def inspected_artifact(self, root: Path):
        evidence = root / "evidence/quality.json"
        evidence.parent.mkdir(parents=True)
        evidence.write_text('{"passed":true}\n', encoding="utf-8")
        (root / "thing.step").write_text("exact bytes\n", encoding="utf-8")
        manifest = seal_artifact(root, created_at="content-addressed")
        digest = hashlib.sha256(evidence.read_bytes()).hexdigest()
        result = InspectionResult.create(
            "quality",
            True,
            manifest.artifact_sha256,
            {"passed": True},
            "independent-quality",
            "1.0.0",
            SHA,
            "evidence/quality.json",
            digest,
        )
        return manifest, result

    def test_canonical_surface_uses_the_short_workshop_story(self):
        self.assertEqual(inventor_workshop.__version__, "0.5.0")
        self.assertEqual(Wish.__name__, "Wish")
        self.assertEqual(Workbench.__name__, "Workbench")
        self.assertEqual(Playtest.__name__, "Playtest")
        self.assertEqual(PlaytestResult.__name__, "PlaytestResult")
        self.assertIs(Inspection, Playtest)
        self.assertIs(InspectionResult, PlaytestResult)
        self.assertIs(InspectionPolicy, PlaytestPolicy)
        self.assertIs(Workbench.inspect, Workbench.playtest)
        self.assertEqual(Stamp.__name__, "Receipt")
        self.assertEqual(ModelDoor.__name__, "ModelDoor")
        self.assertEqual(CadDoor.__name__, "CadDoor")
        self.assertEqual(CadInspectionDoor.__name__, "CadInspectionDoor")
        self.assertEqual(InspectionDoor.__name__, "InspectionDoor")
        self.assertEqual(DeliveryDoor.__name__, "DeliveryDoor")
        self.assertTrue(issubclass(ShopDoor, object))

        spec = WorkflowSpec.board_game()
        self.assertEqual(spec.initial_stage, "make")
        self.assertEqual(tuple(spec.stages), ("make", "playtest", "done"))
        self.assertEqual(Workflow(spec).legal_targets("make"), ("playtest",))
        self.assertEqual(
            Workflow(spec).legal_targets("playtest"), ("done", "make")
        )

    def test_inspection_rejects_detached_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            manifest, result = self.inspected_artifact(root)
            inspection = Inspection(manifest, (result,))
            self.assertEqual(inspection.artifact_sha256, manifest.artifact_sha256)
            detached = InspectionResult.create(
                result.inspection_id,
                True,
                manifest.artifact_sha256,
                result.evidence,
                result.evaluator,
                result.evaluator_version,
                result.config_sha256,
                result.evidence_ref,
                "b" * 64,
            )
            with self.assertRaisesRegex(ContractError, "absent or hash-mismatched"):
                Inspection(manifest, (detached,))

    def test_canonical_workflow_requires_a_playtest_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "artifact"
            artifact.mkdir()
            manifest, result = self.inspected_artifact(artifact)
            spec = WorkflowSpec(
                initial_stage="wish",
                stages=("wish", "inspected"),
                edges={"wish": ("inspected",), "inspected": ()},
                required_gates={"inspected": ("quality",)},
                gate_policies={
                    "quality": InspectionPolicy(
                        "quality", "independent-quality", "1.0.0", SHA
                    )
                },
            )
            workflow = Workflow(spec)
            clockwork = Clockwork(Path(temporary) / "clockwork.sqlite3")
            workflow.register(
                clockwork,
                "wish-1",
                artifact_sha256=manifest.artifact_sha256,
            )
            with self.assertRaisesRegex(TransitionError, "require a Playtest"):
                workflow.advance(clockwork, "wish-1", "inspected", 0)
            product = workflow.advance(
                clockwork,
                "wish-1",
                "inspected",
                0,
                playtest=Playtest(manifest, (result,)),
            )
            self.assertEqual(product["stage"], "inspected")

    def test_pack_has_one_canonical_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            (root / "thing.txt").write_text("one thing\n", encoding="utf-8")
            destination = Path(temporary) / "thing.pack.zip"
            packed = pack_artifact(root, destination)
            inspected = inspect_pack(destination)
            self.assertEqual(packed, inspected)
            self.assertEqual(packed.pack_sha256, packed.packet_sha256)
            with self.assertRaisesRegex(ContractError, "claims do not match"):
                PackedArtifact(
                    packed.path,
                    packed.bytes + 1,
                    packed.entries,
                    packed.pack_sha256,
                    packed.artifact_sha256,
                )

    def test_pack_transition_requires_and_records_structured_pack(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            (root / "thing.txt").write_text("one thing\n", encoding="utf-8")
            packed = pack_artifact(root, Path(temporary) / "thing.pack.zip")
            other_root = Path(temporary) / "other-artifact"
            other_root.mkdir()
            (other_root / "thing.txt").write_text("other thing\n", encoding="utf-8")
            other = pack_artifact(other_root, Path(temporary) / "other.pack.zip")
            workflow = Workflow(
                WorkflowSpec(
                    initial_stage="inspect",
                    stages=("inspect", "pack"),
                    edges={"inspect": ("pack",), "pack": ()},
                    required_gates={},
                    gate_policies={},
                )
            )

            missing_clockwork = Clockwork(Path(temporary) / "missing.sqlite3")
            workflow.register(
                missing_clockwork,
                "missing",
                artifact_sha256=packed.artifact_sha256,
            )
            with self.assertRaisesRegex(TransitionError, "requires a validated PackedArtifact"):
                workflow.advance(missing_clockwork, "missing", "pack", 0)

            wrong_clockwork = Clockwork(Path(temporary) / "wrong.sqlite3")
            workflow.register(
                wrong_clockwork,
                "wrong",
                artifact_sha256=packed.artifact_sha256,
            )
            with self.assertRaisesRegex(TransitionError, "different artifact bytes"):
                workflow.advance(
                    wrong_clockwork,
                    "wrong",
                    "pack",
                    0,
                    packed=other,
                )

            clockwork = Clockwork(Path(temporary) / "clockwork.sqlite3")
            workflow.register(
                clockwork,
                "thing",
                artifact_sha256=packed.artifact_sha256,
            )
            product = workflow.advance(
                clockwork,
                "thing",
                "pack",
                0,
                packed=packed,
            )
            self.assertEqual(product["stage"], "pack")
            event = clockwork.events("thing")[-1]
            self.assertEqual(
                event["payload"],
                {
                    "note": "",
                    "inspections": [],
                    "pack_sha256": packed.pack_sha256,
                },
            )

    def test_pack_plan_predicts_exact_bytes_and_explains_oversize(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            (root / "small.txt").write_text("small\n", encoding="utf-8")
            (root / "large.bin").write_bytes(b"x" * 1024)
            destination = Path(temporary) / "thing.pack.zip"
            plan = plan_pack(root, maximum_bytes=512)
            self.assertFalse(plan.fits)
            self.assertGreater(plan.over_by, 0)
            self.assertEqual(plan.largest_files[0], ("large.bin", 1024))
            with self.assertRaisesRegex(
                ArtifactError,
                "largest eligible files: large.bin .*Stage product-only files",
            ):
                pack_artifact(root, destination, maximum_bytes=512)
            packed = pack_artifact(
                root, destination, extra_excludes=("large.bin",)
            )
            fitted = plan_pack(root, extra_excludes=("large.bin",))
            self.assertTrue(fitted.fits)
            self.assertEqual(fitted.pack_bytes, packed.bytes)
            self.assertEqual(fitted.artifact_sha256, packed.artifact_sha256)

    def test_schemas_ship_as_a_discoverable_contract(self):
        schemas = {path.name: path for path in discover_schemas()}
        self.assertEqual(
            list(schemas),
            [
                "inventor.schema.json",
                "inspection-result.schema.json",
                "maker-mark.schema.json",
                "receipt.schema.json",
                "stamp.schema.json",
            ],
        )
        stamp_schema = json.loads(
            schemas["stamp.schema.json"].read_text(encoding="utf-8")
        )
        receipt_schema = json.loads(
            schemas["receipt.schema.json"].read_text(encoding="utf-8")
        )
        inspection_schema = json.loads(
            schemas["inspection-result.schema.json"].read_text(encoding="utf-8")
        )
        maker_mark_schema = json.loads(
            schemas["maker-mark.schema.json"].read_text(encoding="utf-8")
        )
        self.assertEqual(maker_mark_schema["properties"]["schema_version"]["const"], 1)
        self.assertEqual(
            maker_mark_schema["properties"]["mode"]["enum"],
            ["live", "fixture", "offline", "replay"],
        )
        stamp = Stamp(
            packet_sha256="a" * 64,
            artifact_sha256="b" * 64,
            design_id="design",
            slug="slug",
            owner_id="owner",
            root_id="root",
            current_history_id="history",
            status="draft",
            project_url="https://example.test/design/slug",
            observed_at="2026-08-23T12:00:00+00:00",
        )
        self.assertLessEqual(set(stamp_schema["required"]), set(stamp.to_dict()))
        self.assertEqual(set(stamp.to_dict()), set(stamp_schema["properties"]))
        self.assertLessEqual(
            set(receipt_schema["required"]), set(stamp.to_receipt_dict())
        )
        self.assertEqual(
            set(stamp.to_receipt_dict()), set(receipt_schema["properties"])
        )
        self.assertEqual(
            set(inspection_schema["properties"]),
            set(self.inspected_artifact(Path(tempfile.mkdtemp()))[1].to_dict()),
        )

    def test_stamp_and_send_result_emit_canonical_keys_but_read_v02(self):
        legacy = {
            "packet_sha256": "a" * 64,
            "artifact_sha256": "b" * 64,
            "design_id": "design",
            "slug": "slug",
            "owner_id": "owner",
            "root_id": "root",
            "current_history_id": "history",
            "status": "draft",
            "project_url": "https://example.test/design/slug",
            "observed_at": "2026-08-23T12:00:00+00:00",
        }
        stamp = Stamp.from_dict(legacy)
        self.assertEqual(stamp.pack_sha256, legacy["packet_sha256"])
        self.assertEqual(stamp.packet_sha256, stamp.pack_sha256)
        self.assertEqual(stamp.door, "shop")
        self.assertNotIn("packet_sha256", stamp.to_dict())
        self.assertIn("pack_sha256", stamp.to_dict())
        sent = SendResult.from_dict({"intent_id": "intent-1", "receipt": legacy})
        self.assertIs(sent.stamp, sent.receipt)
        self.assertEqual(set(sent.to_dict()), {"intent_id", "stamp"})
        self.assertNotIn("receipt", sent.to_dict())

    def test_generic_sender_accepts_delivery_door_and_checks_stamp_identity(self):
        class Delivery:
            name = "printer"

            def __init__(self):
                self.request = None

            def deliver(self, packed, request, effect_token):
                self.request = request
                self.effect_token = effect_token
                request["accepted"] = True
                return Stamp.create(
                    packed.pack_sha256,
                    packed.artifact_sha256,
                    self.name,
                    "accepted",
                    "order-42",
                )

            def reconcile(self, intent):
                raise AssertionError("successful sends do not reconcile")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            (root / "thing.txt").write_text("one thing\n", encoding="utf-8")
            packed = pack_artifact(root, Path(temporary) / "thing.pack.zip")
            clockwork = Clockwork(Path(temporary) / "clockwork.sqlite3")
            workflow = Workflow(
                WorkflowSpec(
                    initial_stage="pack",
                    stages=("pack", "send"),
                    edges={"pack": ("send",), "send": ()},
                    required_gates={},
                    gate_policies={},
                )
            )
            workflow.register(
                clockwork, "thing", artifact_sha256=packed.artifact_sha256
            )
            request = {"material": "PLA"}
            door = Delivery()
            sent = Sender(clockwork).send("thing", packed, door, request)
            self.assertEqual(sent.stamp.reference, "order-42")
            self.assertEqual(request, {"material": "PLA"})
            self.assertTrue(door.request["accepted"])
            self.assertTrue(door.effect_token)
            intent = clockwork.get_send_intent(sent.intent_id)
            self.assertEqual(intent["state"], "succeeded")
            self.assertEqual(intent["stamp"], sent.stamp.to_dict())
            product = workflow.advance(
                clockwork,
                "thing",
                "send",
                0,
                stamp=sent.stamp,
                pack_sha256=packed.pack_sha256,
                send_intent_id=sent.intent_id,
            )
            self.assertEqual(product["stage"], "send")
            event = clockwork.events("thing")[-1]
            self.assertEqual(
                set(event["payload"]),
                {"note", "inspections", "stamp", "pack_sha256", "send_intent_id"},
            )
            self.assertNotIn("publication_receipt", event["payload"])

    def test_generic_sender_holds_ambiguous_effect_until_door_reconciliation(self):
        class FlakyDelivery:
            name = "printer"

            def __init__(self):
                self.calls = 0
                self.stamp = None

            def deliver(self, packed, request, effect_token):
                self.calls += 1
                self.stamp = Stamp.create(
                    packed.pack_sha256,
                    packed.artifact_sha256,
                    self.name,
                    "accepted",
                    "order-unknown",
                    {"effect_token": effect_token},
                )
                raise TimeoutError("socket closed after acceptance")

            def reconcile(self, intent):
                return self.stamp

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            (root / "thing.txt").write_text("one thing\n", encoding="utf-8")
            packed = pack_artifact(root, Path(temporary) / "thing.pack.zip")
            clockwork = Clockwork(Path(temporary) / "clockwork.sqlite3")
            clockwork.register_product(
                "thing", "wish", {}, packed.artifact_sha256
            )
            door = FlakyDelivery()
            sender = Sender(clockwork)
            with self.assertRaisesRegex(AmbiguousSendError, "reconcile"):
                sender.send("thing", packed, door, {"material": "PLA"})
            intent = clockwork.latest_send_intent("thing", door.name)
            self.assertEqual(intent["state"], "unknown")
            self.assertEqual(
                intent["effect_token"], door.stamp.details["effect_token"]
            )
            with self.assertRaisesRegex(AmbiguousSendError, "reconcile"):
                sender.send("thing", packed, door, {"material": "PLA"})
            self.assertEqual(door.calls, 1)
            resolved = sender.reconcile(intent["id"], door)
            self.assertEqual(resolved.stamp.reference, "order-unknown")
            self.assertEqual(
                clockwork.get_send_intent(intent["id"])["state"], "succeeded"
            )

    def test_generic_sender_retries_only_after_door_proves_no_effect(self):
        class RetryableDelivery:
            name = "printer"

            def __init__(self):
                self.calls = 0

            def deliver(self, packed, request, effect_token):
                self.calls += 1
                if self.calls == 1:
                    raise TimeoutError("no readback")
                return Stamp.create(
                    packed.pack_sha256,
                    packed.artifact_sha256,
                    self.name,
                    "accepted",
                    "order-after-proof",
                    {"effect_token": effect_token},
                )

            def reconcile(self, intent):
                return None

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "artifact"
            root.mkdir()
            (root / "thing.txt").write_text("one thing\n", encoding="utf-8")
            packed = pack_artifact(root, Path(temporary) / "thing.pack.zip")
            clockwork = Clockwork(Path(temporary) / "clockwork.sqlite3")
            clockwork.register_product(
                "thing", "wish", {}, packed.artifact_sha256
            )
            door = RetryableDelivery()
            sender = Sender(clockwork)
            with self.assertRaises(AmbiguousSendError):
                sender.send("thing", packed, door, {})
            intent = clockwork.latest_send_intent("thing", door.name)
            self.assertIsNone(sender.reconcile(intent["id"], door))
            self.assertEqual(
                clockwork.get_send_intent(intent["id"])["state"], "planned"
            )
            sent = sender.send("thing", packed, door, {})
            self.assertEqual(sent.stamp.reference, "order-after-proof")
            self.assertEqual(door.calls, 2)

    def test_old_names_are_direct_shims_to_one_implementation(self):
        former = importlib.import_module("inventor_foundation")
        core = importlib.import_module("inventor_core")
        self.assertIs(former.Wish, Wish)
        self.assertIs(core.Wish, Wish)
        self.assertIs(
            importlib.import_module("inventor_foundation.pack").pack_artifact,
            pack_artifact,
        )
        import inventor_foundation.pack
        import inventor_core.pack

        self.assertIs(former.pack.pack_artifact, pack_artifact)
        self.assertIs(core.pack.pack_artifact, pack_artifact)
        canonical_contracts = importlib.import_module(
            "inventor_workshop.cad.contracts"
        )
        self.assertIs(
            importlib.import_module("inventor_foundation.cad.contracts"),
            canonical_contracts,
        )
        self.assertIs(
            importlib.import_module("inventor_core.cad.contracts"),
            canonical_contracts,
        )


if __name__ == "__main__":
    unittest.main()
