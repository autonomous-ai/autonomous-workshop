"""tools/process_review.py ranks the timing ledger deterministically (ADR 0106)."""

import importlib.util
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path

from workshop.runtime import timing_ledger as tl

TOOL_PATH = Path(__file__).resolve().parents[2] / "tools" / "process_review.py"
SPEC = importlib.util.spec_from_file_location("workshop_process_review", TOOL_PATH)
if SPEC is None or SPEC.loader is None:  # pragma: no cover
    raise RuntimeError("cannot load process_review")
PR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PR)

DAY = 1794873600.0  # 2026-11-17T00:00:00Z
PROJECT = "/r/toys-spec/city/kit/proof"


def row(step, start, wall, *, outcome="pass", cls=None, parent=None, key=None, project=PROJECT, row_id=None,
        reason=None, cache_hit=False):
    made = tl.end_row(row_id=row_id or "%s@%s" % (step, start), step=step, tool=step.split("/")[0],
                      project=project, parent=parent, started=DAY + start, ended=DAY + start + wall,
                      exit_code=0 if outcome == "pass" else 1, outcome=outcome, failure_class=cls,
                      reason=reason, inputs_key=key, cache_hit=cache_hit)
    return made


class ProcessReviewTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="process-review-"))
        self.ledger = self.tmp / "ledger.jsonl"

    def write(self, rows):
        for item in rows:
            self.assertTrue(tl.append_row(item, self.ledger))

    def rows(self):
        return PR.finished_rows(tl.read_rows(self.ledger), DAY - 86400, DAY + 86400)

    def test_total_ranking_counts_own_time_not_childrens(self):
        self.write([row("seal_proof/seal", 0, 6000, row_id="S"),
                    row("make_round/print-gates-only", 10, 5000, parent="S"),
                    row("kit_sheets/check", 7000, 30)])
        ranked = PR.rank_total(self.rows())
        self.assertEqual([item["key"] for item in ranked],
                         ["make_round/print-gates-only", "seal_proof/seal", "kit_sheets/check"])
        self.assertEqual(ranked[1]["seconds"], 1000.0)

    def test_reruns_on_the_same_key_but_not_after_a_kill(self):
        self.write([row("make_round/print-gates-only", 0, 5000, key="k1"),
                    row("make_round/print-gates-only", 6000, 5000, key="k1"),
                    row("make_round/print-gates-only", 12000, 5000, key="k2"),
                    row("make_round/full", 20000, 100, key="k3", outcome="killed", cls="killed"),
                    row("make_round/full", 21000, 900, key="k3"),
                    row("make_round/component", 0, 10, key="k4", cache_hit=True),
                    row("make_round/component", 30, 0, key="k4", cache_hit=True)])
        ranked = PR.rank_reruns(self.rows())
        self.assertEqual(len(ranked), 1)
        self.assertEqual((ranked[0]["step"], ranked[0]["seconds"]), ("make_round/print-gates-only", 5000.0))

    def test_expensive_steps_before_a_cheap_failure(self):
        self.write([row("seal_proof/seal", 0, 6000, outcome="fail", cls="product-defect", row_id="S"),
                    row("seeded-batch/design/print-gates", 0, 5600, parent="S"),
                    row("seeded-batch/design/project", 1, 1, parent="S"),
                    row("seeded-batch/design/final-verification", 5600, 0.3, outcome="fail",
                        cls="product-defect", parent="S"),
                    # A slow failure after a slow step is no ordering finding.
                    row("seal_proof/seal", 9000, 6000, outcome="fail", cls="product-defect", row_id="T"),
                    row("seeded-batch/design/print-gates", 9000, 5000, parent="T"),
                    row("seeded-batch/design/final-verification", 14000, 900, outcome="fail",
                        cls="product-defect", parent="T")])
        ranked = PR.rank_expensive_before_cheap(self.rows())
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["step"], "seeded-batch/design/final-verification")
        self.assertEqual(ranked[0]["expensive"], ["seeded-batch/design/print-gates"])
        self.assertEqual(ranked[0]["seconds"], 5600.0)

    def test_harness_failures_leave_out_product_defects_and_annotations_reclass(self):
        self.write([row("seal_proof/seal", 0, 100, outcome="fail", cls="stale-input"),
                    row("seal_proof/seal", 200, 5000, outcome="fail", cls="product-defect", row_id="snap"),
                    row("kit_tree/final", 6000, 500, outcome="killed", cls="killed")])
        ranked = PR.rank_harness_failures(self.rows())
        self.assertEqual([item["key"] for item in ranked],
                         ["kit_tree/final (killed)", "seal_proof/seal (stale-input)"])
        tl.append_row({"kind": PR.ANNOTATION_KIND, "match": {"id": "snap"}, "failure_class": "tool-error",
                       "note": "no snap joint in kit_tree"}, PR.annotations_path(self.ledger))
        noted = PR.apply_annotations(tl.read_rows(self.ledger), PR.read_annotations(self.ledger))
        window = PR.finished_rows(noted, DAY - 86400, DAY + 86400)
        ranked = PR.rank_harness_failures(window)
        self.assertEqual(ranked[0]["key"], "seal_proof/seal (tool-error)")

    def test_waits_between_steps_on_one_toy_up_to_two_hours(self):
        self.write([row("seal_proof/seal", 0, 100),
                    row("seal_proof/seal", 1100, 100),           # 1000 s wait
                    row("seal_proof/seal", 1200 + 3 * 3600, 10),  # an owner gap: left out
                    row("kit_sheets/check", 50, 10, project="/r/toys-spec/other/proof")])
        ranked = PR.rank_waits(self.rows())
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["seconds"], 1000.0)

    def test_a_start_with_no_end_is_killed_once_superseded(self):
        start = tl.base_row("start", row_id="lost", step="seal_proof/seal", tool="seal_proof", project=PROJECT,
                            parent=None)
        start["started_at"] = tl.utc_iso(DAY + 10)
        newest = dict(start, id="running")
        newest["started_at"] = tl.utc_iso(DAY + 5000)
        self.write([start, newest, row("seal_proof/seal", 4000, 100)])
        killed = [item for item in self.rows() if item["outcome"] == "killed"]
        self.assertEqual([item["id"] for item in killed], ["lost"])

    def test_the_report_is_deterministic_and_names_evidence_and_fixes(self):
        self.write([row("seal_proof/seal", 0, 6000, outcome="fail", cls="product-defect", row_id="S"),
                    row("seeded-batch/design/print-gates", 0, 5600, parent="S"),
                    row("seeded-batch/design/final-verification", 5600, 0.3, outcome="fail",
                        cls="product-defect", parent="S", reason="check_layout: library too long"),
                    row("seal_proof/seal", 7000, 30, outcome="fail", cls="stale-input")])
        rows = tl.read_rows(self.ledger)
        first = PR.build_report(rows, today=date(2026, 11, 17), days=7, ledger=self.ledger)
        second = PR.build_report(list(reversed(rows)), today=date(2026, 11, 17), days=7, ledger=self.ledger)
        self.assertEqual(first, second)
        self.assertIn("## Top 5", first)
        self.assertIn("Suggested fix: Run `seeded-batch/design/final-verification` (cheap) before", first)
        self.assertIn("Evidence: `%s`" % PROJECT, first)
        for title in ("Most total wall time", "Rerun on unchanged inputs", "Expensive steps before a cheap failure",
                      "Tool, harness, stale-input and kill failures", "Waits between steps"):
            self.assertIn("## %s" % title, first)


class BackfillTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="process-review-backfill-"))
        self.ledger = self.tmp / "ledger.jsonl"
        self.toy = self.tmp / "toys-spec" / "city" / "kit"
        self.toy.mkdir(parents=True)

    def log(self, name, text, mtime):
        path = self.toy / name
        path.write_text(text)
        os.utime(path, (mtime, mtime))
        return path

    def test_seal_logs_become_rows_with_children_and_kills(self):
        proof = "%s/proof" % self.toy
        self.log("seal_L33d.log", "1794836044\nseal_proof: the seeded batch fails on the Proof (check-failure); "
                 "see measure/seeded-batch.json:\nfinal-verification (exit 1): too long\n"
                 "[verify_project] check_layout: rc=1 in 0.23s\n[verify_project] wrote report %s/measure/x.md\n"
                 "[verify_project] image-derived final workflow: rc=1 in 0.23s\nEXIT 1\n1794841776\n" % proof,
                 1794841776)
        self.log("seal_L34.log", "1794842368\n", 1794842368)   # stopped by PIDs, superseded
        self.log("seal_L35.log", "1794846399\nseal_proof: no print-gate summary: run make_round "
                 "--print-gates-only\nEXIT 1\n1794846411\n", 1794846411)
        self.log("seal_L43.log", "1794906475\n", 1794906475)   # the newest: still running, not judged
        self.log("notes.log", "a design script's own output\n", 1794906475)
        result = PR.backfill([self.tmp / "toys-spec"], self.ledger, None)
        rows = tl.read_rows(self.ledger)
        by_source = {}
        for item in rows:
            by_source.setdefault(Path(item["source"].split(":", 1)[1]).name, []).append(item)
        self.assertNotIn("seal_L43.log", by_source)
        self.assertNotIn("notes.log", by_source)
        seal = next(item for item in by_source["seal_L33d.log"] if item["step"] == "seal_proof/seal")
        self.assertEqual((seal["wall_s"], seal["outcome"], seal["toy"]), (5732.0, "fail", "city/kit"))
        steps = {item["step"] for item in by_source["seal_L33d.log"]}
        self.assertIn("verify_project/check_layout", steps)
        self.assertIn("seal_proof/layers-before-final (inferred)", steps)
        self.assertEqual(by_source["seal_L34.log"][0]["outcome"], "killed")
        self.assertEqual(by_source["seal_L35.log"][0]["failure_class"], "stale-input")
        again = PR.backfill([self.tmp / "toys-spec"], self.ledger, None)
        self.assertEqual(again["written"], 0)
        self.assertEqual(len(tl.read_rows(self.ledger)), len(rows))
        self.assertGreater(result["written"], 0)

    def test_gate_logs_dedupe_backups_and_join_their_run(self):
        gates = self.toy / "proof" / "measure" / "print-gates"
        backup = self.toy / "work" / "r1-backup" / "measure" / "print-gates"
        for directory in (gates, backup):
            directory.mkdir(parents=True)
            path = directory / "mesh-boat.log"
            path.write_text("$ /venv/python3 /skills/cad/scripts/check_mesh %s --json\n(12.5s, exit 0)\n"
                            % (self.toy / "proof"))
            os.utime(path, (DAY + 100, DAY + 100))
        self.log("printgates_L1.log", "%d\nmake_round print gates  %s/proof  nozzle 0.4\n  PASS\nEXIT 0\n%d\n"
                 % (DAY, self.toy, DAY + 200), DAY + 200)
        PR.backfill([self.tmp / "toys-spec"], self.ledger, None)
        rows = tl.read_rows(self.ledger)
        gate_rows = [item for item in rows if item["step"] == "print-gate/check_mesh"]
        self.assertEqual(len(gate_rows), 1)
        run = next(item for item in rows if item["step"] == "make_round/print-gates-only")
        self.assertEqual(gate_rows[0]["parent"], run["id"])
        self.assertEqual(gate_rows[0]["wall_s"], 12.5)


if __name__ == "__main__":
    unittest.main()
