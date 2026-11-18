"""The timing ledger records steps and never changes them (ADR 0106)."""

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from workshop.make import seeded_batch
from workshop.runtime import timing_ledger as tl


class LedgerCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="timing-ledger-"))
        self.ledger = self.tmp / "timing" / "ledger.jsonl"
        patcher = mock.patch.dict(os.environ, {tl.LEDGER_ENV: str(self.ledger)})
        patcher.start()
        os.environ.pop(tl.PARENT_ENV, None)
        self.addCleanup(patcher.stop)

    def rows(self, event=None):
        rows = tl.read_rows(self.ledger)
        return [row for row in rows if event is None or row["event"] == event]


class LedgerRowTest(LedgerCase):
    def test_timed_writes_a_start_row_and_one_complete_end_row(self):
        project = self.tmp / "toys-spec" / "city" / "amsterdam-kit" / "proof"
        (project / "measure").mkdir(parents=True)
        (project / "params.py").write_text("A = 1\n")
        with tl.timed("make_round/print-gates-only", tool="make_round", project=project,
                      argv=[str(project), "--print-gates-only"], fingerprint=True) as span:
            span.exit_code = 0
        start, end = self.rows()
        self.assertEqual((start["event"], end["event"]), ("start", "end"))
        self.assertEqual(start["id"], end["id"])
        for key in ("step", "tool", "project", "toy", "started_at", "ended_at", "wall_s", "exit_code", "outcome",
                    "failure_class", "cache_hit", "inputs_key"):
            self.assertIn(key, end)
        self.assertEqual(end["step"], "make_round/print-gates-only")
        self.assertEqual(end["toy"], "city/amsterdam-kit")
        self.assertEqual((end["outcome"], end["failure_class"], end["exit_code"]), ("pass", None, 0))
        self.assertGreaterEqual(end["wall_s"], 0)
        self.assertRegex(end["inputs_key"], r"^[0-9a-f]{64}$")

    def test_the_fingerprint_follows_sources_not_outputs(self):
        project = self.tmp / "p"
        (project / "measure").mkdir(parents=True)
        (project / "params.py").write_text("A = 1\n")
        first = tl.inputs_fingerprint(project, ["x"])
        (project / "measure" / "summary.json").write_text("{}")
        self.assertEqual(first, tl.inputs_fingerprint(project, ["x"]))
        (project / "params.py").write_text("A = 2\n")
        self.assertNotEqual(first, tl.inputs_fingerprint(project, ["x"]))

    def test_an_exception_is_a_failed_end_row_and_still_raises(self):
        with self.assertRaises(ValueError):
            with tl.timed("kit_tree/final", tool="kit_tree"):
                raise ValueError("boom")
        end = self.rows("end")[0]
        self.assertEqual((end["outcome"], end["failure_class"]), ("fail", "tool-error"))
        self.assertIn("boom", end["reason"])

    def test_an_interrupt_is_killed(self):
        with self.assertRaises(KeyboardInterrupt):
            with tl.timed("seal_proof/seal", tool="seal_proof"):
                raise KeyboardInterrupt
        self.assertEqual(self.rows("end")[0]["outcome"], "killed")

    def test_children_name_their_parent_and_the_environment_is_restored(self):
        with tl.timed("seal_proof/seal", tool="seal_proof") as outer:
            outer.exit_code = 0
            with tl.timed("make_round/full", tool="make_round") as inner:
                inner.exit_code = 1
        self.assertNotIn(tl.PARENT_ENV, os.environ)
        ends = {row["step"]: row for row in self.rows("end")}
        self.assertEqual(ends["make_round/full"]["parent"], ends["seal_proof/seal"]["id"])
        self.assertIsNone(ends["seal_proof/seal"]["parent"])

    def test_a_turned_off_or_unwritable_ledger_never_fails_the_step(self):
        with mock.patch.dict(os.environ, {tl.LEDGER_ENV: "off"}):
            with tl.timed("x/y", tool="x") as span:
                span.exit_code = 0
        self.assertFalse(self.ledger.exists())
        blocker = self.tmp / "file"
        blocker.write_text("")
        self.assertFalse(tl.append_row({"kind": tl.KIND}, blocker / "ledger.jsonl"))

    def test_child_timing_lines_become_child_rows(self):
        output = ("[verify_project] check_layout: rc=1 in 0.23s\n"
                  "[verify_project] image-derived final workflow: rc=1 in 0.25s\n")
        self.assertEqual([child["name"] for child in tl.child_timings(output)],
                         ["check_layout", "image-derived final workflow"])
        self.assertEqual(tl.record_children("p1", project="/x", ended=1000.0, output=output), 2)
        rows = self.rows("end")
        self.assertEqual({row["parent"] for row in rows}, {"p1"})
        self.assertEqual(rows[0]["step"], "verify_project/check_layout")
        self.assertTrue(rows[0]["times_estimated"])

    def test_a_workshop_stage_event_is_one_row(self):
        self.assertTrue(tl.record_workshop_event(product_id="wish-20261111-124354-d6002b31", stage="make",
                                                 operation="session.start", state="failed",
                                                 observed_at="2026-11-11T13:24:23.399Z", elapsed_ms=5000))
        row = self.rows("end")[0]
        self.assertEqual(row["step"], "workshop/make/session.start")
        self.assertEqual(row["toy"], "wish-20261111-124354-d6002b31")
        self.assertEqual((row["outcome"], row["failure_class"], row["wall_s"]), ("fail", "tool-error", 5.0))
        self.assertFalse(tl.record_workshop_event(product_id="w", stage="make", operation="x", state="started",
                                                  observed_at="2026-11-11T13:24:23.399Z", elapsed_ms=None))


class ClassifyTest(unittest.TestCase):
    def test_failure_classes(self):
        cases = [
            ((0,), {}, ("pass", None)),
            ((1,), {"output": "FAIL S74: blocked at step 1/125"}, ("fail", "product-defect")),
            ((1,), {"reason": "Shared Helper base4.py changed since it froze; rerun make_round --shared-helpers"},
             ("fail", "stale-input")),
            ((2,), {"output": "project (exit 2): foreign or stale STEP files: measure/kit/print.step"},
             ("fail", "stale-input")),
            ((2,), {"output": "verify_project: error: bad flag"}, ("fail", "tool-error")),
            ((2,), {"output": "make_round: this round of canal-base is not the Approved Proof's Component "
                              "(its B-rep or carry key differs); a deviation is a component-worker's round"},
             ("fail", "seed-mismatch")),
            ((1,), {"reason": "workshop wish --seed-source would refuse /p: reference image ref-03.png "
                              "repeats the bytes of ref-02.png"}, ("fail", "seed-mismatch")),
            # A root round that failed its own checks is the product's, not the seal's.
            ((2,), {"output": "make_round: this round of house-1 is not the Approved Proof's Component "
                              "(it did not pass its checks)"}, ("fail", "tool-error")),
            ((1,), {"output": "Traceback (most recent call last):\n KeyError"}, ("fail", "tool-error")),
            ((None,), {"timed_out": True}, ("killed", "killed")),
            ((-9,), {}, ("killed", "killed")),
            ((143,), {}, ("killed", "killed")),
            ((0,), {"unverified": True}, ("unverified", "tool-error")),
            ((None,), {"reason": "could not start"}, ("fail", "tool-error")),
        ]
        for args, kwargs, expected in cases:
            with self.subTest(args=args, kwargs=kwargs):
                self.assertEqual(tl.classify(*args, **kwargs), expected)

    def test_toy_of(self):
        self.assertEqual(tl.toy_of("/r/toys-spec/mini-city-organizer/amsterdam-kit/proof"),
                         "mini-city-organizer/amsterdam-kit")
        self.assertEqual(tl.toy_of("/h/runs/wish-20261111-124354-d6002b31/workspace/cad"),
                         "wish-20261111-124354-d6002b31")
        self.assertEqual(tl.toy_of("/tmp/somewhere"), "somewhere")
        self.assertIsNone(tl.toy_of(None))


class SeededBatchLedgerTest(LedgerCase):
    """The batch writes a row per step, and its record is the same with the
    ledger on or off: the ledger only records."""

    def plan(self):
        return [seeded_batch.Step(id="print-gates", layer="components", argv=("gates",)),
                seeded_batch.Step(id="final-verification", layer="final", argv=("verify",))]

    def runner(self, argv, cwd, timeout):
        if argv[0] == "gates":
            return seeded_batch.RunResult(0, "ok", duration_s=5400.0)
        return seeded_batch.RunResult(1, "[verify_project] check_layout: rc=1 in 0.23s\n", duration_s=0.3)

    def strip(self, record):
        return [{key: value for key, value in step.items() if key != "duration_s"} for step in record["steps"]]

    def test_rows_per_step_and_an_unchanged_record(self):
        project = self.tmp / "proof"
        on = seeded_batch.run_batch(self.plan(), project, runner=self.runner, plan_name="design")
        with mock.patch.dict(os.environ, {tl.LEDGER_ENV: "off"}):
            off = seeded_batch.run_batch(self.plan(), project, runner=self.runner, plan_name="design")
        self.assertEqual((on["status"], on["failed_layer"]), (off["status"], off["failed_layer"]))
        self.assertEqual(self.strip(on), self.strip(off))
        ends = {row["step"]: row for row in self.rows("end")}
        gates = ends["seeded-batch/design/print-gates"]
        self.assertEqual((gates["outcome"], gates["wall_s"], gates["layer"]), ("pass", 5400.0, "components"))
        self.assertEqual(gates["inputs_key"], on["steps"][0]["key"])
        final = ends["seeded-batch/design/final-verification"]
        self.assertEqual((final["outcome"], final["failure_class"]), ("fail", "product-defect"))
        child = ends["verify_project/check_layout"]
        self.assertEqual(child["parent"], final["id"])

    def test_a_reused_step_is_a_cache_hit_row(self):
        project = self.tmp / "proof"
        first = seeded_batch.run_batch(self.plan()[:1], project, runner=self.runner, plan_name="design")
        seeded_batch.run_batch(self.plan()[:1], project, runner=self.runner, plan_name="design", previous=first)
        hits = [row for row in self.rows("end") if row.get("cache_hit")]
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["wall_s"], 0.0)

    def test_a_timeout_is_killed(self):
        def runner(argv, cwd, timeout):
            return seeded_batch.RunResult(None, "", timed_out=True, duration_s=900.0)

        record = seeded_batch.run_batch(self.plan()[:1], self.tmp / "proof", runner=runner, plan_name="design")
        self.assertEqual(record["status"], seeded_batch.HARNESS_FAILURE)
        self.assertEqual(self.rows("end")[0]["outcome"], "killed")


if __name__ == "__main__":
    unittest.main()
