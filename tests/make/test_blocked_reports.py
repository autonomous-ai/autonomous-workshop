"""Blocked Reports (issue #88): a Component Worker's recorded block, the
Workshop Manager's answer, and the gates that hold while one is open."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from tests.make.test_make_round import load_module
from workshop.errors import ContractError
from workshop.make import make_round_guard
from workshop.make.blocked_reports import (
    run_blocked_reports,
    verify_no_open_blocked_reports,
)

REPOSITORY = Path(__file__).resolve().parents[2]
STAGE_PROPOSAL = (
    REPOSITORY / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"
)
STANCE = "The spine housing prints on its front face, the mating plane. No part needs support."
SEATS = "The wing hinge seats and the back-wall ceiling sit at Y 17.5."
CONTRACT = {
    "schema_version": 4,
    "geometries": [{"id": "spine-housing"}, {"id": "wing"}],
    "requirements": [
        {"scope": "geometry:spine-housing", "text": STANCE},
        {"scope": "geometry:spine-housing", "text": SEATS},
    ],
}


def _stage_proposal():
    spec = importlib.util.spec_from_file_location("stage_proposal_blocked_test", STAGE_PROPOSAL)
    tool = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tool)
    return tool


class BlockedReportTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name).resolve()
        wish = json.dumps({"context": {"design_contract": CONTRACT}}).encode()
        (self.run_root / "WISH.json").write_bytes(wish)
        self.wish_sha256 = hashlib.sha256(wish).hexdigest()
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)
        for role in ("spine-housing", "wing"):
            (self.project / ("part_%s.step.py" % role)).write_text("")
        self.component_round("spine-housing", 4, checks_ok=False)

    def component_round(self, role, number, *, checks_ok):
        root = self.project / "measure/component-rounds" / role
        (root / ("r%04d" % number)).mkdir(parents=True, exist_ok=True)
        (root / ("r%04d" % number) / "summary.json").write_text(json.dumps({"checks_ok": checks_ok}))
        (root / "make-round-state.json").write_text(json.dumps({"round": number}))

    def write(self, name, value):
        path = self.run_root / name
        path.write_text(json.dumps(value))
        return path

    def report(self, rows=(STANCE, SEATS), component="part_spine-housing.step.py"):
        path = self.write("blocked.json", {"rows": list(rows), "reason": "Nothing stands under the seats."})
        return self.module.report_blocked(self.project, path, component)

    def clear(self, **answer):
        return self.module.clear_blocked(self.project, self.write("answer.json", answer))

    def main(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.module.main([str(self.project), *arguments])
        return code, stdout.getvalue(), stderr.getvalue()

    # -- the worker's report -------------------------------------------------

    def test_a_report_records_its_component_latest_round_and_rows_verbatim(self):
        event = self.report()
        self.assertEqual(event["report"], 1)
        self.assertEqual(event["component"], "spine-housing")
        self.assertEqual(event["round"], 4)
        self.assertEqual(event["rows"], [STANCE, SEATS])
        self.assertEqual(event["wish_sha256"], self.wish_sha256)
        views = self.module.open_blocked(self.project)
        self.assertEqual([(v["report"], v["status"]) for v in views], [(1, "open")])

    def test_a_row_not_in_the_sealed_contract_is_refused(self):
        with self.assertRaisesRegex(ValueError, "not in the sealed Design Contract"):
            self.report(rows=(STANCE, "The seats may float."))
        # Whitespace is not wording: a re-wrapped row is still verbatim.
        self.report(rows=(STANCE.replace(" the mating", "\n  the mating"),))

    def test_a_component_with_an_open_report_cannot_file_another(self):
        self.report()
        with self.assertRaisesRegex(ValueError, "still open"):
            self.report()
        self.assertEqual(self.report(component="part_wing.step.py", rows=(SEATS,))["report"], 2)

    def test_a_malformed_report_is_refused(self):
        for record in ({"rows": [STANCE]}, {"rows": [], "reason": "x"}, {"rows": [STANCE], "reason": " "},
                       {"rows": [STANCE], "reason": "x", "options": []}):
            with self.subTest(record=record):
                with self.assertRaises(ValueError):
                    self.module.report_blocked(self.project, self.write("bad.json", record),
                                               "part_spine-housing.step.py")

    # -- the Manager's answer ------------------------------------------------

    def test_a_decision_clears_the_report(self):
        self.report()
        event = self.clear(report=1, decision="Add a 50 degree vault under each seat.")
        self.assertEqual((event["event"], event["waits_on"]), ("decision", None))
        self.assertEqual(self.module.open_blocked(self.project), [])
        with self.assertRaisesRegex(ValueError, "already answered"):
            self.clear(report=1, decision="again")

    def test_a_need_must_quote_every_row(self):
        self.report()
        with self.assertRaisesRegex(ValueError, "quotes every row"):
            self.clear(report=1, need="'%s' contradicts the seats" % STANCE)
        with self.assertRaisesRegex(ValueError, "one line"):
            self.clear(report=1, need="%s\n%s" % (STANCE, SEATS))
        event = self.clear(report=1, need="Contract Contradiction: '%s' vs '%s'" % (STANCE, SEATS))
        self.assertEqual(event["event"], "need")
        self.assertEqual(self.module.open_blocked(self.project), [])

    def test_a_decision_waiting_on_a_component_reopens_after_its_next_passing_round(self):
        self.component_round("wing", 3, checks_ok=True)
        self.report()
        event = self.clear(report=1, decision="The wing keeps below the slot top.",
                           waits_on="part_wing.step.py")
        self.assertEqual((event["waits_on"], event["waits_on_round"]), ("wing", 3))
        [view] = self.module.open_blocked(self.project)
        self.assertEqual(view["status"], "waiting")
        self.assertEqual(self.module.waking_reports(self.project, "wing"), [])
        # A failing wing round wakes nothing; its next passing round does.
        self.component_round("wing", 4, checks_ok=False)
        self.assertEqual(self.module.open_blocked(self.project)[0]["status"], "waiting")
        self.component_round("wing", 5, checks_ok=True)
        [view] = self.module.open_blocked(self.project)
        self.assertEqual((view["status"], view["woken_by"]), ("woken", {"component": "wing", "round": 5}))
        self.assertEqual(self.module.waking_reports(self.project, "wing"),
                         [{"report": 1, "component": "spine-housing"}])
        code, out, _ = self.main("--blocked-reports")
        self.assertEqual(code, 1)
        self.assertIn("WAKE wing passed r0005", out)
        # The Manager wakes the worker with a decision, which clears it.
        self.clear(report=1, decision="The wing is below the slot top; build the strips now.")
        self.assertEqual(self.module.open_blocked(self.project), [])

    def test_a_decision_cannot_wait_on_the_blocked_component(self):
        self.report()
        with self.assertRaisesRegex(ValueError, "another Component"):
            self.clear(report=1, decision="x", waits_on="part_spine-housing.step.py")
        with self.assertRaisesRegex(ValueError, "no Blocked Report"):
            self.clear(report=2, decision="x")

    # -- the gates ----------------------------------------------------------

    def test_an_open_report_refuses_an_assembly_round_and_the_final_verifier(self):
        self.report()
        for arguments in ((), ("--require-component-passes",), ("--record-visual", "f.json", "--full")):
            with self.subTest(arguments=arguments):
                code, _, err = self.main(*arguments)
                self.assertEqual(code, 2)
                self.assertIn("Blocked Report 1 (spine-housing, open) is open", err)
        self.clear(report=1, decision="x", waits_on="part_wing.step.py")
        code, _, err = self.main("--require-component-passes")
        self.assertEqual(code, 2)
        self.assertIn("waiting", err)

    def test_the_cli_reports_and_clears(self):
        blocked = self.write("blocked.json", {"rows": [STANCE, SEATS], "reason": "No support."})
        code, out, _ = self.main("--component", "part_spine-housing.step.py", "--report-blocked", str(blocked))
        self.assertEqual(code, 0)
        self.assertIn("Blocked Report 1 recorded", out)
        answer = self.write("answer.json", {"report": 1, "need": "'%s' vs '%s'" % (STANCE, SEATS)})
        code, out, _ = self.main("--clear-blocked", str(answer))
        self.assertEqual(code, 0)
        self.assertIn("stage_proposal.py --run-root . need --stage make --status waiting", out)
        code, out, _ = self.main("--blocked-reports", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)[0]["status"], "need")

    def test_the_host_refuses_make_acceptance_while_a_report_is_open(self):
        self.assertEqual(verify_no_open_blocked_reports(self.project, wish_sha256=self.wish_sha256), [])
        self.report()
        with self.assertRaisesRegex(ContractError, "Blocked Report 1 .* is open"):
            verify_no_open_blocked_reports(self.project, wish_sha256=self.wish_sha256)
        self.clear(report=1, decision="x", waits_on="part_wing.step.py")
        with self.assertRaisesRegex(ContractError, "waiting"):
            verify_no_open_blocked_reports(self.project, wish_sha256=self.wish_sha256)
        self.clear(report=1, decision="The wing is below the slot top.")
        [summary] = verify_no_open_blocked_reports(self.project, wish_sha256=self.wish_sha256)
        self.assertEqual((summary["cleared_by"], len(summary["answers"])), ("decision", 2))
        with self.assertRaisesRegex(ContractError, "not bound to this run"):
            verify_no_open_blocked_reports(self.project, wish_sha256="b" * 64)
        ledger = self.project / "measure/blocked-reports.jsonl"
        ledger.write_text(ledger.read_text() + "{nope\n")
        with self.assertRaisesRegex(ContractError, "ledger is invalid"):
            verify_no_open_blocked_reports(self.project, wish_sha256=self.wish_sha256)

    def test_the_finalizer_refuses_the_make_proposal_while_a_report_is_open(self):
        tool = _stage_proposal()
        tool._refuse_open_blocked_reports(self.project)
        self.report()
        with self.assertRaisesRegex(tool.ProposalError, "Blocked Report 1 .* is open"):
            tool._refuse_open_blocked_reports(self.project)
        self.clear(report=1, need="'%s' vs '%s'" % (STANCE, SEATS))
        tool._refuse_open_blocked_reports(self.project)

    def test_the_three_ledger_readers_agree(self):
        tool = _stage_proposal()
        self.component_round("wing", 2, checks_ok=True)
        self.report()
        self.report(component="part_wing.step.py", rows=(SEATS,))
        self.clear(report=1, decision="x", waits_on="part_wing.step.py")
        self.clear(report=2, need="'%s'" % SEATS)
        content = (self.project / "measure/blocked-reports.jsonl").read_text()
        host = make_round_guard.blocked_reports(content)
        self.assertEqual(self.module.blocked_reports(content), host)
        self.assertEqual({n: r["status"] for n, r in tool._blocked_reports(content).items()},
                         {n: r["status"] for n, r in host.items()})
        for bad in (content + json.dumps({"event": "need", "report": 2, "at": "t"}) + "\n",
                    content.replace('"report": 2', '"report": 3', 1)):
            for reader in (make_round_guard.blocked_reports, self.module.blocked_reports, tool._blocked_reports):
                with self.subTest(reader=reader):
                    with self.assertRaises(ValueError):
                        reader(bad)

    # -- the run report -----------------------------------------------------

    def test_the_run_report_lists_every_report_how_it_was_cleared_and_for_how_long(self):
        self.report()
        self.report(component="part_wing.step.py", rows=(SEATS,))
        ledger = self.project / "measure/blocked-reports.jsonl"
        events = [json.loads(line) for line in ledger.read_text().splitlines()]
        events[0]["at"] = "2026-10-03T02:16:00Z"
        events[1]["at"] = "2026-10-03T02:30:00Z"
        events.append({"event": "need", "report": 1, "at": "2026-10-03T02:26:00Z",
                       "need": "'%s' vs '%s'" % (STANCE, SEATS), "wish_sha256": self.wish_sha256})
        ledger.write_text("".join(json.dumps(event) + "\n" for event in events))
        now = datetime(2026, 10, 3, 3, 25, tzinfo=timezone.utc)
        listed = run_blocked_reports(self.run_root, now=now)
        self.assertEqual(
            [(item["attempt"], item["report"], item["component"], item["cleared_by"], item["open_seconds"])
             for item in listed],
            [("r0001", 1, "spine-housing", "need", 600), ("r0001", 2, "wing", None, 3300)],
        )
        self.assertEqual(listed[0]["rows"], [STANCE, SEATS])
        ledger.write_text("{nope\n")
        self.assertEqual(run_blocked_reports(self.run_root)[0]["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
