import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from inventor_workshop.errors import ContractError
from inventor_workshop.handoff import (
    ManagerAssignmentHandoff,
    bind_manager_assignment_result,
    read_manager_assignment,
    validate_manager_assignment_result,
)
from inventor_workshop.make import Wish
from inventor_workshop.manager import _implementation_sha256
from inventor_workshop.taste import load_taste


class ManagerAssignmentHandoffTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.inventor = Path(self.temporary.name).resolve() / "ivy"
        self.inventor.mkdir()
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Ivy\n"
            "description: Scientific objects that make invisible systems tangible.\n"
            "---\n"
            "# Ivy's Taste\n\n"
            "Make the hidden relationship visible.\n",
            encoding="utf-8",
        )
        manifest = {
            "schema_version": 5,
            "id": "ivy",
            "status": "active",
            "entrypoint": ["python3", "profile.py"],
            "capabilities": ["worlds-made-small", "taste-only"],
            "checks": [],
            "source": {"kind": "local"},
        }
        (self.inventor / "inventor.json").write_text(
            json.dumps(manifest, sort_keys=True) + "\n", encoding="utf-8"
        )
        (self.inventor / "profile.py").write_text(
            "# exact fixture implementation\n", encoding="utf-8"
        )

    def tearDown(self):
        self.temporary.cleanup()

    def assignment(self):
        manifest_sha256 = hashlib.sha256(
            (self.inventor / "inventor.json").read_bytes()
        ).hexdigest()
        taste = load_taste(self.inventor)
        card = SimpleNamespace(
            root=self.inventor,
            inventor_id="ivy",
            manifest_sha256=manifest_sha256,
            entrypoint=("python3", "profile.py"),
        )
        return SimpleNamespace(
            wish=Wish.create(
                "wish-exact",
                "A toy\nwith every word intact",
                constraints={
                    "dimensions_mm": {"maximum": [90, 60, 30]},
                    "preserve": ["blue", "hinged"],
                },
                context={
                    "source": "workshop-cli",
                    "customer": {"locale": "en-US", "notes": ["gift"]},
                },
            ),
            inventor_id="ivy",
            playtest_rounds=7,
            entrypoint=("python3", "profile.py"),
            decision=SimpleNamespace(
                decision_sha256="d" * 64,
                selected=SimpleNamespace(
                    card=card,
                    taste=taste,
                    implementation_sha256=_implementation_sha256(self.inventor),
                ),
            ),
            assignment_sha256="a" * 64,
        )

    def test_round_trip_preserves_exact_wish_and_assignment_identity(self):
        handoff = ManagerAssignmentHandoff.from_assignment(self.assignment())
        parsed = read_manager_assignment(
            io.StringIO(json.dumps(handoff.to_dict())),
            expected_inventor_id="ivy",
        )
        self.assertEqual(parsed.wish.to_dict(), self.assignment().wish.to_dict())
        self.assertEqual(parsed.decision_sha256, "d" * 64)
        self.assertEqual(parsed.assignment_sha256, "a" * 64)
        self.assertEqual(parsed.playtest_rounds, 7)
        self.assertEqual(parsed.schema_version, 2)
        self.assertTrue(parsed.has_exact_inventor_identity)
        parsed.assert_inventor_current(self.inventor)

    def test_tampered_wish_is_rejected_even_when_product_id_is_unchanged(self):
        payload = ManagerAssignmentHandoff.from_assignment(self.assignment()).to_dict()
        payload["wish"]["constraints"]["preserve"].append("tampered")
        with self.assertRaisesRegex(ContractError, "Wish identity"):
            read_manager_assignment(
                io.StringIO(json.dumps(payload)), expected_inventor_id="ivy"
            )

    def test_wrong_inventor_is_rejected(self):
        payload = ManagerAssignmentHandoff.from_assignment(self.assignment()).to_dict()
        with self.assertRaisesRegex(ContractError, "different Inventor"):
            read_manager_assignment(
                io.StringIO(json.dumps(payload)), expected_inventor_id="leo"
            )

    def test_result_binding_rejects_product_round_and_assignment_drift(self):
        handoff = ManagerAssignmentHandoff.from_assignment(self.assignment())
        with self.assertRaisesRegex(ContractError, "different product"):
            bind_manager_assignment_result(
                {"product_id": "other", "playtest_rounds": 7}, handoff
            )
        with self.assertRaisesRegex(ContractError, "Playtest allowance"):
            bind_manager_assignment_result(
                {"product_id": "wish-exact", "playtest_rounds": 6}, handoff
            )

        result = bind_manager_assignment_result(
            {"product_id": "wish-exact", "playtest_rounds": 7, "status": "waiting"},
            handoff,
        )
        self.assertEqual(
            validate_manager_assignment_result(result, handoff), result
        )
        result["manager_assignment"]["decision_sha256"] = "e" * 64
        with self.assertRaisesRegex(ContractError, "not bound"):
            validate_manager_assignment_result(result, handoff)

    def test_unknown_fields_and_oversize_documents_fail_closed(self):
        payload = ManagerAssignmentHandoff.from_assignment(self.assignment()).to_dict()
        payload["surprise"] = True
        with self.assertRaisesRegex(ContractError, "fields"):
            read_manager_assignment(
                io.StringIO(json.dumps(payload)), expected_inventor_id="ivy"
            )
        with self.assertRaisesRegex(ContractError, "bounded"):
            read_manager_assignment(
                io.StringIO(" " * 1_000_001), expected_inventor_id="ivy"
            )

    def test_legacy_handoff_is_readable_for_status_but_cannot_execute(self):
        legacy = ManagerAssignmentHandoff(
            wish=self.assignment().wish,
            inventor_id="ivy",
            playtest_rounds=7,
            decision_sha256="d" * 64,
            assignment_sha256="a" * 64,
        )
        parsed = ManagerAssignmentHandoff.from_dict(
            legacy.to_dict(), expected_inventor_id="ivy"
        )
        self.assertFalse(parsed.has_exact_inventor_identity)
        with self.assertRaisesRegex(ContractError, "legacy.*implementation identity"):
            read_manager_assignment(
                io.StringIO(json.dumps(legacy.to_dict())),
                expected_inventor_id="ivy",
            )

    def test_changed_implementation_and_taste_fail_before_execution(self):
        handoff = ManagerAssignmentHandoff.from_assignment(self.assignment())
        (self.inventor / "profile.py").write_text("# changed\n", encoding="utf-8")
        with self.assertRaisesRegex(ContractError, "implementation.*changed"):
            handoff.assert_inventor_current(self.inventor)

        (self.inventor / "profile.py").write_text(
            "# exact fixture implementation\n", encoding="utf-8"
        )
        (self.inventor / "TASTE.md").write_text(
            "---\n"
            "name: Ivy\n"
            "description: Scientific objects that make invisible systems tangible.\n"
            "---\n"
            "# Changed Taste\n\nA different preference.\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ContractError, "Taste.*changed"):
            handoff.assert_inventor_current(self.inventor)

    def test_exact_fields_are_part_of_handoff_and_result_hashes(self):
        handoff = ManagerAssignmentHandoff.from_assignment(self.assignment())
        payload = handoff.to_dict()
        binding = handoff.result_binding()
        for key in (
            "manifest_sha256",
            "taste_sha256",
            "implementation_sha256",
            "entrypoint",
        ):
            self.assertEqual(payload[key], binding[key])
        payload["entrypoint"] = ["python3", "other.py"]
        with self.assertRaisesRegex(ContractError, "identity"):
            ManagerAssignmentHandoff.from_dict(
                payload, expected_inventor_id="ivy"
            )


if __name__ == "__main__":
    unittest.main()
