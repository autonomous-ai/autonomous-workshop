import io
import json
import unittest
from types import SimpleNamespace

from inventor_workshop.errors import ContractError
from inventor_workshop.handoff import (
    ManagerAssignmentHandoff,
    bind_manager_assignment_result,
    read_manager_assignment,
    validate_manager_assignment_result,
)
from inventor_workshop.make import Wish


class ManagerAssignmentHandoffTest(unittest.TestCase):
    def assignment(self):
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
            decision=SimpleNamespace(decision_sha256="d" * 64),
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


if __name__ == "__main__":
    unittest.main()
