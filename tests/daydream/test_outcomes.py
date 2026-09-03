import json
import stat
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.daydream.support import sample_sealed
from workshop.daydream.native import wish_from_daydream
from workshop.daydream.outcomes import (
    RunOutcomeMemory,
    outcome_path,
    read_outcomes,
    remember_run_outcome,
    render_outcomes_markdown,
)
from workshop.errors import ContractError
from workshop.wish import Wish


MOMENT = datetime(2026, 9, 3, 8, 0, 0, tzinfo=timezone.utc)


class OutcomeMemoryTest(unittest.TestCase):
    def test_receipt_is_allowlisted_hash_bound_and_rendered_as_fact(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = (Path(temporary) / "home").resolve()
            wish = wish_from_daydream(sample_sealed(), wish_id="wish-outcome-one")
            receipt = {
                "product_id": "wish-outcome-one",
                "effort": "quest",
                "manager": "codex",
                "status": "complete",
                "stage": "release",
                "revision": 4,
                "round": 2,
                "wish_sha256": "a" * 64,
                "checkpoint_sha256": "b" * 64,
                "publication": {
                    "status": "public",
                    "verified": True,
                    "page_url": "https://factory.invalid/private-path",
                },
                "session": {"untrusted_prose": "must not enter memory"},
            }
            self.assertTrue(
                remember_run_outcome(wish, receipt=receipt, moment=MOMENT, home=home)
            )
            path = outcome_path("sample", home=home)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            outcomes = read_outcomes(path)
            self.assertEqual(len(outcomes), 1)
            outcome = outcomes[0]
            self.assertEqual(outcome.route, "quest")
            self.assertEqual(outcome.run_status, "complete")
            self.assertEqual(outcome.publication_status, "public")
            raw = json.loads(path.read_text(encoding="utf-8"))
            self.assertNotIn("session", raw)
            self.assertNotIn("page_url", raw)
            self.assertEqual(RunOutcomeMemory.parse(raw), outcome)
            self.assertIn(
                "host-observed facts, not Judge predictions",
                render_outcomes_markdown(outcomes),
            )
            raw["stage"] = "make"
            with self.assertRaisesRegex(ContractError, "event_sha256"):
                RunOutcomeMemory.parse(raw)

    def test_error_is_distinct_and_direct_user_wish_is_not_recorded(self):
        with tempfile.TemporaryDirectory() as temporary:
            home = (Path(temporary) / "home").resolve()
            wish = wish_from_daydream(sample_sealed(), wish_id="wish-outcome-two")
            self.assertTrue(
                remember_run_outcome(
                    wish,
                    error=RuntimeError("native turn ended before a receipt"),
                    route="spark",
                    manager="codex",
                    moment=MOMENT,
                    home=home,
                )
            )
            outcome = read_outcomes(outcome_path("sample", home=home))[0]
            self.assertEqual(outcome.result, "error")
            self.assertEqual(outcome.error_type, "RuntimeError")
            self.assertIn("ended before a receipt", render_outcomes_markdown((outcome,)))
            direct = Wish.create("wish-direct", "a person-authored Wish")
            self.assertFalse(
                remember_run_outcome(
                    direct,
                    receipt={"status": "complete"},
                    moment=MOMENT,
                    home=home,
                )
            )


if __name__ == "__main__":
    unittest.main()
