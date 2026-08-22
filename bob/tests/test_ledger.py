"""Tests for harness/ledger.py — append-only JSONL + spend reconciliation."""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from harness import ledger


class LedgerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._old_home = os.environ.get("BOB_HOME")
        os.environ["BOB_HOME"] = self._tmp.name

    def tearDown(self):
        if self._old_home is None:
            os.environ.pop("BOB_HOME", None)
        else:
            os.environ["BOB_HOME"] = self._old_home
        self._tmp.cleanup()

    def _ledger_file(self):
        return os.path.join(self._tmp.name, "state", "REWARD_LEDGER.jsonl")

    def test_append_fills_schema_defaults(self):
        row = ledger.append({"slug": "plumb", "kind": "iteration",
                             "stage": "simulated"})
        self.assertIn("at", row)
        self.assertEqual(row["score"], 0.0)
        self.assertEqual(row["components"], {})
        self.assertEqual(row["delta"], 0.0)
        self.assertEqual(row["cost_usd"], 0.0)
        self.assertEqual(row["notes"], "")
        got = ledger.rows()
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["slug"], "plumb")

    def test_append_requires_slug_and_valid_kind(self):
        with self.assertRaises(ValueError):
            ledger.append({"kind": "iteration"})
        with self.assertRaises(ValueError):
            ledger.append({"slug": "x", "kind": "vibe_check"})
        with self.assertRaises(ValueError):
            ledger.append("not a dict")

    def test_append_only_and_ordered(self):
        for i in range(3):
            ledger.append({"slug": "g%d" % i, "kind": "iteration"})
        got = ledger.rows()
        self.assertEqual([r["slug"] for r in got], ["g0", "g1", "g2"])
        with open(self._ledger_file()) as f:
            self.assertEqual(len(f.readlines()), 3)

    def test_rows_filters(self):
        old = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
        ledger.append({"slug": "old-game", "kind": "publish", "at": old})
        ledger.append({"slug": "new-game", "kind": "iteration"})
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self.assertEqual([r["slug"] for r in ledger.rows(since=today)],
                         ["new-game"])
        self.assertEqual([r["slug"] for r in ledger.rows(slug="old-game")],
                         ["old-game"])
        self.assertEqual(ledger.rows(slug="nope"), [])

    def test_rows_skips_truncated_tail(self):
        ledger.append({"slug": "ok", "kind": "iteration"})
        with open(self._ledger_file(), "a") as f:
            f.write('{"slug": "half-writ')  # crash mid-append
        got = ledger.rows()
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["slug"], "ok")

    def test_rows_empty_when_no_file(self):
        self.assertEqual(ledger.rows(), [])
        self.assertEqual(ledger.spend_today(), 0.0)

    def test_spend_today_ledger_only(self):
        ledger.append({"slug": "a", "kind": "iteration", "cost_usd": 1.5})
        ledger.append({"slug": "b", "kind": "iteration", "cost_usd": 2.5})
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        ledger.append({"slug": "c", "kind": "iteration", "cost_usd": 99.0,
                       "at": yesterday})
        self.assertAlmostEqual(ledger.spend_today(), 4.0)

    def _write_daybook(self, day_entry):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(self._tmp.name, "state", "DAYBOOK.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump({today: day_entry, "heartbeat": None}, f)

    def test_spend_today_takes_max_never_sum(self):
        # Ledger rows and daybook steps record the SAME events; summing
        # them would trip the daily budget at half spend.
        ledger.append({"slug": "a", "kind": "iteration", "cost_usd": 4.0})
        self._write_daybook({"ticks": 1, "cost_usd": 3.0, "steps": []})
        self.assertAlmostEqual(ledger.spend_today(), 4.0)  # ledger higher
        self._write_daybook({"ticks": 1, "cost_usd": 10.0, "steps": []})
        self.assertAlmostEqual(ledger.spend_today(), 10.0)  # daybook higher

    def test_spend_today_daybook_step_costs(self):
        # Steps richer than the day field: still max, inside and out.
        self._write_daybook({
            "ticks": 2, "cost_usd": 10.0,
            "steps": [{"cost_usd": 7.0}, {"cost_usd": 5.0}]})
        self.assertAlmostEqual(ledger.spend_today(), 12.0)

    def test_spend_today_ignores_garbage(self):
        ledger.append({"slug": "a", "kind": "iteration", "cost_usd": 2.0})
        path = os.path.join(self._tmp.name, "state", "DAYBOOK.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write("{not json")
        self.assertAlmostEqual(ledger.spend_today(), 2.0)


if __name__ == "__main__":
    unittest.main()
