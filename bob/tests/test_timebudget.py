"""Tests for harness/timebudget.py — the Peter-pattern tick time ledger.

Self-contained per CONTRACTS §5: temp BOB_HOME per test, stdlib unittest,
wall-clock spends simulated with tiny sleeps so the suite stays fast.
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from harness import timebudget  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-tb-")
        self._saved = os.environ.get("BOB_HOME")
        os.environ["BOB_HOME"] = self.home

    def tearDown(self):
        if self._saved is None:
            os.environ.pop("BOB_HOME", None)
        else:
            os.environ["BOB_HOME"] = self._saved
        shutil.rmtree(self.home, ignore_errors=True)

    def ledger_path(self):
        return os.path.join(self.home, "state", ".tick-budget.json")


class TestOpenRun(Base):
    def test_open_run_writes_fresh_ledger(self):
        timebudget.open_run(total_minutes=25)
        self.assertTrue(os.path.exists(self.ledger_path()))
        rep = timebudget.report()
        self.assertEqual(rep["total_minutes"], 25.0)
        self.assertEqual(rep["spent_minutes"], 0.0)
        self.assertEqual(rep["remaining_minutes"], 25.0)
        self.assertEqual(rep["steps"], [])

    def test_open_run_default_is_25(self):
        timebudget.open_run()
        self.assertEqual(timebudget.report()["total_minutes"], 25.0)

    def test_open_run_replaces_stale_ledger(self):
        # a crashed prior tick's ledger must not eat the new tick's budget
        timebudget.open_run(total_minutes=1)
        with timebudget.step(1):
            pass
        timebudget.open_run(total_minutes=10)
        self.assertEqual(timebudget.report()["steps"], [])

    def test_step_without_open_run_is_actionable(self):
        with self.assertRaises(timebudget.BudgetExhausted) as cm:
            with timebudget.step(5):
                pass
        self.assertIn("open_run", str(cm.exception))


class TestStep(Base):
    def test_step_grants_cap_when_budget_ample(self):
        timebudget.open_run(total_minutes=25)
        with timebudget.step(10) as granted:
            self.assertEqual(granted, 10.0)

    def test_last_step_gets_min_cap_remaining(self):
        timebudget.open_run(total_minutes=10)
        with timebudget.step(30) as granted:
            # cap exceeds what's left: grant is squeezed to remaining
            self.assertEqual(granted, 10.0)

    def test_grant_shrinks_as_budget_is_spent(self):
        # total 0.01 min = 0.6s; spend ~0.15s, then ask for far more
        timebudget.open_run(total_minutes=0.01)
        with timebudget.step(0.01):
            time.sleep(0.15)
        with timebudget.step(60) as granted:
            self.assertLess(granted, 0.01)
            self.assertGreater(granted, 0.0)

    def test_refuses_when_spent(self):
        # total 0.002 min = 0.12s; the sleep overspends it
        timebudget.open_run(total_minutes=0.002)
        with timebudget.step(1):
            time.sleep(0.2)
        with self.assertRaises(timebudget.BudgetExhausted) as cm:
            with timebudget.step(1):
                self.fail("step body must never run once the budget is spent")
        self.assertIn("Refusing", str(cm.exception))

    def test_step_records_wall_clock_row(self):
        timebudget.open_run(total_minutes=5)
        with timebudget.step(2):
            time.sleep(0.12)
        rep = timebudget.report()
        self.assertEqual(len(rep["steps"]), 1)
        row = rep["steps"][0]
        self.assertEqual(row["cap"], 2.0)
        self.assertEqual(row["granted"], 2.0)
        self.assertGreaterEqual(row["minutes"], 0.12 / 60.0)
        self.assertLess(row["minutes"], 0.05)  # sanity: seconds, not minutes
        self.assertAlmostEqual(rep["spent_minutes"], row["minutes"], places=9)

    def test_spend_recorded_even_when_step_body_raises(self):
        # failed minutes are just as gone as successful ones
        timebudget.open_run(total_minutes=5)
        with self.assertRaises(RuntimeError):
            with timebudget.step(1):
                time.sleep(0.1)
                raise RuntimeError("agent blew up")
        rep = timebudget.report()
        self.assertEqual(len(rep["steps"]), 1)
        self.assertGreater(rep["spent_minutes"], 0.0)


class TestReport(Base):
    def test_report_totals_add_up(self):
        timebudget.open_run(total_minutes=5)
        for _ in range(3):
            with timebudget.step(1):
                time.sleep(0.05)
        rep = timebudget.report()
        self.assertEqual(len(rep["steps"]), 3)
        self.assertAlmostEqual(
            rep["spent_minutes"],
            sum(s["minutes"] for s in rep["steps"]),
            places=9,
        )
        self.assertAlmostEqual(
            rep["remaining_minutes"],
            rep["total_minutes"] - rep["spent_minutes"],
            places=9,
        )

    def test_remaining_never_negative(self):
        timebudget.open_run(total_minutes=0.001)
        with timebudget.step(1):
            time.sleep(0.15)
        self.assertEqual(timebudget.report()["remaining_minutes"], 0.0)

    def test_ledger_is_valid_json_on_disk(self):
        # atomic tmp+replace: the on-disk file is always whole JSON
        timebudget.open_run(total_minutes=5)
        with timebudget.step(1):
            pass
        with open(self.ledger_path()) as f:
            ledger = json.load(f)
        self.assertIn("opened", ledger)
        self.assertEqual(len(ledger["steps"]), 1)


if __name__ == "__main__":
    unittest.main()
