import dataclasses
import json
import unittest

from inventor_workshop import MakerMark
from inventor_workshop.errors import ContractError


SHA_A = "a" * 64
SHA_B = "b" * 64


def maker_mark(**changes):
    fields = {
        "schema_version": 1,
        "inventor_id": "alice",
        "run_id": "run-20260823-1",
        "mode": "live",
        "tool": "codex",
        "tool_version": "0.145.0",
        "authenticated": True,
        "taste_sha256": SHA_A,
        "artifact_sha256": "c" * 64,
        "input_sha256": {"wish": SHA_B},
        "agent_calls": 3,
        "actual_cost_micros": 125_000,
        "synthetic_cost_micros": 0,
        "started_at": "2026-08-23T12:00:00+00:00",
        "completed_at": "2026-08-23T12:05:00Z",
        "limitations": (),
    }
    fields.update(changes)
    return MakerMark(**fields)


class MakerMarkTest(unittest.TestCase):
    def test_authenticated_live_mark_round_trips_exactly(self):
        mark = maker_mark()

        self.assertTrue(mark.is_live)
        self.assertTrue(mark.may_claim_live_creation)
        mark.assert_artifact("c" * 64)
        with self.assertRaisesRegex(ContractError, "different artifact bytes"):
            mark.assert_artifact("d" * 64)
        self.assertEqual(MakerMark.from_dict(mark.to_dict()), mark)
        self.assertEqual(MakerMark.from_json(mark.to_json()), mark)
        self.assertEqual(json.loads(mark.to_json()), mark.to_dict())

    def test_mark_is_deeply_immutable(self):
        inputs = {"wish": SHA_B}
        limitations = ["No physical print was performed."]
        mark = maker_mark(
            mode="offline",
            authenticated=False,
            input_sha256=inputs,
            agent_calls=258,
            actual_cost_micros=0,
            synthetic_cost_micros=900_000,
            limitations=limitations,
        )
        inputs["wish"] = SHA_A
        limitations.append("Changed later.")

        self.assertEqual(mark.input_sha256["wish"], SHA_B)
        self.assertEqual(mark.limitations, ("No physical print was performed.",))
        with self.assertRaises(TypeError):
            mark.input_sha256["wish"] = SHA_A
        with self.assertRaises(dataclasses.FrozenInstanceError):
            mark.mode = "live"

    def test_fixture_calls_and_synthetic_cost_never_look_live(self):
        mark = maker_mark(
            mode="fixture",
            authenticated=False,
            agent_calls=258,
            actual_cost_micros=0,
            synthetic_cost_micros=725_000,
            limitations=("Agent responses came from checked-in fixtures.",),
        )

        self.assertFalse(mark.is_live)
        self.assertFalse(mark.may_claim_live_creation)
        self.assertEqual(mark.agent_calls, 258)

    def test_non_live_marks_reject_authentication_and_actual_cost(self):
        for changes in (
            {"mode": "fixture", "authenticated": True},
            {
                "mode": "offline",
                "authenticated": False,
                "actual_cost_micros": 1,
            },
            {
                "mode": "replay",
                "authenticated": False,
                "actual_cost_micros": 1,
            },
        ):
            changes.setdefault("limitations", ("Not a live creation run.",))
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                maker_mark(**changes)

    def test_live_marks_reject_synthetic_cost(self):
        with self.assertRaisesRegex(ContractError, "synthetic cost"):
            maker_mark(synthetic_cost_micros=1)

    def test_non_claiming_marks_must_disclose_a_limitation(self):
        for changes in (
            {"mode": "offline", "authenticated": False, "actual_cost_micros": 0},
            {"authenticated": False},
            {"agent_calls": 0},
        ):
            with self.subTest(changes=changes), self.assertRaisesRegex(
                ContractError, "state a limitation"
            ):
                maker_mark(**changes)

    def test_tool_version_inputs_costs_and_time_are_exact(self):
        invalid = (
            {"tool_version": "latest"},
            {"taste_sha256": "A" * 64},
            {"artifact_sha256": "C" * 64},
            {"input_sha256": {}},
            {"input_sha256": {"Wish": SHA_B}},
            {"agent_calls": True},
            {"actual_cost_micros": 1.5},
            {"started_at": "2026-08-23 12:00:00Z"},
            {"completed_at": "2026-08-23T11:59:59Z"},
        )
        for changes in invalid:
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                maker_mark(**changes)

    def test_dict_and_json_reject_unknown_missing_and_duplicate_fields(self):
        document = maker_mark().to_dict()
        document["production_ready"] = True
        with self.assertRaisesRegex(ContractError, "unknown"):
            MakerMark.from_dict(document)

        document = maker_mark().to_dict()
        del document["tool_version"]
        with self.assertRaisesRegex(ContractError, "missing"):
            MakerMark.from_dict(document)

        payload = maker_mark().to_json()
        duplicate = payload.replace(
            '"schema_version":1', '"schema_version":1,"schema_version":1'
        )
        with self.assertRaisesRegex(ContractError, "duplicate key"):
            MakerMark.from_json(duplicate)


if __name__ == "__main__":
    unittest.main()
