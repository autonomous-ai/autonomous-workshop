"""In-run Contract Amendments (ADR 0085): the Manager's proposal, the fresh
Contract Reviewer's verdict, what an applied amendment changes in a run, and
the host's replay of the ledger before it accepts Make."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from tests.make.test_make_round import load_module
from workshop.errors import ContractError
from workshop.make import make_round_guard
from workshop.make.contract_amendments import (
    contract_digest,
    run_contract_amendments,
    verify_contract_amendments,
)
from workshop.make.role_guard import contract_reviewer_check
from workshop.runtime.make_round_hook import MAKE_ROUND_GUARD_DIRECTORY

REPOSITORY = Path(__file__).resolve().parents[2]
STAGE_PROPOSAL = (
    REPOSITORY / ".agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py"
)
STANCE = "The spine housing prints on its front face, the mating plane. No part needs support."
SEATS = "The wing hinge seats and the back-wall ceiling sit at Y 17.5."
CLEAR = "The wing gears keep 0.4 mm behind the back wall."
NEW_STANCE = "The spine housing prints on its back face. No part needs support."
REFERENCES = ("ref-01-assembly.png", "ref-02-spine-housing.png")
CONTRACT = {
    "schema_version": 4,
    "geometries": [{"id": "spine-housing"}, {"id": "wing"}],
    "references": [
        {"file": REFERENCES[0], "shows": "assembly", "camera": [-90, 15]},
        {"file": REFERENCES[1], "shows": "geometry:spine-housing", "camera": [-90, 15]},
    ],
    "requirements": [
        {"id": "R01", "scope": "geometry:spine-housing", "text": STANCE},
        {"id": "R02", "scope": "geometry:spine-housing", "text": SEATS},
        {"id": "R03", "scope": "assembly", "text": CLEAR},
    ],
    "interfaces": [],
}
REVIEWER = "a1b2c3d4e5f6a7b8c"


class ContractAmendmentTest(unittest.TestCase):
    def setUp(self):
        self.module = load_module()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.run_root = Path(temporary.name).resolve()
        (self.run_root / "wish-references").mkdir()
        sealed = []
        for index, name in enumerate(REFERENCES):
            content = b"image %d" % index
            (self.run_root / "wish-references" / name).write_bytes(content)
            sealed.append({"name": name, "sha256": hashlib.sha256(content).hexdigest()})
        wish = json.dumps({"context": {"design_contract": CONTRACT}, "references": sealed}).encode()
        (self.run_root / "WISH.json").write_bytes(wish)
        self.wish_sha256 = hashlib.sha256(wish).hexdigest()
        self.references = {
            item["name"]: (self.run_root / "wish-references" / item["name"], item["sha256"])
            for item in sealed
        }
        self.project = self.run_root / "artifacts/make/r0001/product/cad"
        self.project.mkdir(parents=True)
        for role in ("spine-housing", "wing"):
            (self.project / ("part_%s.step.py" % role)).write_text("")
        previous = os.environ.pop(self.module.REVIEWER_RUNTIME_ENV, None)
        if previous is not None:
            self.addCleanup(os.environ.__setitem__, self.module.REVIEWER_RUNTIME_ENV, previous)

    def write(self, name, value):
        path = self.run_root / name
        path.write_text(json.dumps(value))
        return path

    def propose(self, rows=(STANCE, SEATS), changes=None, **extra):
        changes = [{"from": STANCE, "to": NEW_STANCE}] if changes is None else changes
        record = {"rows": list(rows), "changes": changes,
                  "reason": "Nothing stands under the seats when it prints on its front.", **extra}
        return self.module.propose_amendment(self.project, self.write("proposal.json", record))

    def review(self, event=None, *, reviewer=REVIEWER, contradiction=True, smallest=True,
               visible_in=(), checked=REFERENCES, **override):
        event = event or self.module.read_contract_amendments(self.project)[1]
        record = {"amendment": event["amendment"], "packet_sha256": event["packet_sha256"],
                  "reviewer": reviewer, "contradiction": contradiction, "smallest": smallest,
                  "visible_in": list(visible_in), "references_checked": list(checked),
                  "reason": "The front face carries the seats; the back face prints them.", **override}
        return self.module.record_amendment_review(self.project, self.write("review.json", record))

    def main(self, *arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = self.module.main([str(self.project), *arguments])
        return code, stdout.getvalue(), stderr.getvalue()

    def verify(self, **options):
        options.setdefault("blocked_reports", [])
        return verify_contract_amendments(
            self.project, contract=CONTRACT, wish_sha256=self.wish_sha256,
            references=self.references, **options,
        )

    # -- the proposal ----------------------------------------------------------

    def test_a_proposal_writes_a_packet_with_every_sealed_reference(self):
        event = self.propose()
        self.assertEqual(event["amendment"], 1)
        self.assertEqual(event["changes"], [
            {"row": "R01", "scope": "geometry:spine-housing", "from": STANCE, "to": NEW_STANCE}])
        self.assertEqual(event["affects"], ["spine-housing"])
        self.assertEqual(event["contract_sha256"], contract_digest(CONTRACT))
        self.assertEqual(event["wish_sha256"], self.wish_sha256)
        packet_bytes = Path(event["packet"]).read_bytes()
        self.assertEqual(hashlib.sha256(packet_bytes).hexdigest(), event["packet_sha256"])
        packet = json.loads(packet_bytes)
        self.assertEqual([item["file"] for item in packet["references"]], list(REFERENCES))
        self.assertEqual(packet["rows"], [STANCE, SEATS])
        # Nothing applies before the review: the rows still read as sealed.
        self.assertEqual(self.module.current_contract(self.project), CONTRACT)

    def test_a_proposal_needs_two_verbatim_rows_and_whole_row_changes(self):
        with self.assertRaisesRegex(ValueError, "2 to"):
            self.propose(rows=(STANCE,))
        with self.assertRaisesRegex(ValueError, "not in the Design Contract"):
            self.propose(rows=(STANCE, "The seats may float."))
        with self.assertRaisesRegex(ValueError, "not one whole requirement"):
            self.propose(changes=[{"from": "prints on its front face", "to": "prints on its back"}])
        with self.assertRaisesRegex(ValueError, "leaves its text"):
            self.propose(changes=[{"from": STANCE, "to": STANCE}])

    def test_a_reference_or_geometry_is_beyond_an_in_run_amendment(self):
        # A reference is what an image shows: changing it is a Visible Change.
        with self.assertRaisesRegex(ValueError, "beyond an in-run amendment"):
            self.propose(changes=[{"from": "geometry:spine-housing", "to": "geometry:wing"}])
        with self.assertRaisesRegex(ValueError, "beyond an in-run amendment"):
            self.propose(changes=[{"from": REFERENCES[1], "to": "ref-02-other.png"}])

    def test_one_amendment_awaits_review_at_a_time_and_holds_the_assembly(self):
        self.propose()
        with self.assertRaisesRegex(ValueError, "still awaits its review"):
            self.propose(changes=[{"from": SEATS, "to": "The seats sit at Y 18.5."}])
        self.assertIn("awaits its Contract Reviewer", self.module.amendment_refusal(self.project))
        code, _, stderr = self.main()
        self.assertEqual(code, 2)
        self.assertIn("awaits its Contract Reviewer", stderr)
        code, stdout, _ = self.main("--contract-amendments")
        self.assertEqual(code, 1)
        self.assertIn("PROPOSED", stdout)

    # -- the review ------------------------------------------------------------

    def test_an_agreeing_review_applies_the_amendment(self):
        self.propose()
        before = self.module.contract_rows(self.project, "spine-housing")
        wing = self.module.contract_rows(self.project, "wing")
        item = self.review()
        self.assertEqual(item["status"], "applied")
        current = self.module.current_contract(self.project)
        self.assertEqual(current["requirements"][0]["text"], NEW_STANCE)
        self.assertEqual(item["amended_sha256"], contract_digest(current))
        # Only the Component whose rows changed sees new rows.
        self.assertNotEqual(self.module.contract_rows(self.project, "spine-housing"), before)
        self.assertEqual(self.module.contract_rows(self.project, "wing"), wing)
        delivered = self.module.component_contract(self.project, "spine-housing")
        self.assertIn(NEW_STANCE, [row["text"] for row in delivered["requirements"]])
        # WISH.json keeps its bytes.
        self.assertEqual(hashlib.sha256((self.run_root / "WISH.json").read_bytes()).hexdigest(),
                         self.wish_sha256)
        self.assertEqual(self.module.amendment_refusal(self.project), "")

    def test_an_amended_assembly_row_binds_every_component(self):
        rows = {role: self.module.contract_rows(self.project, role) for role in ("spine-housing", "wing")}
        event = self.propose(rows=(CLEAR, SEATS),
                             changes=[{"from": CLEAR, "to": "The wing gears keep 0.8 mm behind the back wall."}])
        self.assertEqual(event["affects"], ["spine-housing", "wing"])
        self.review()
        for role, digest in rows.items():
            self.assertNotEqual(self.module.contract_rows(self.project, role), digest)

    def test_a_visible_change_is_refused_and_becomes_a_need(self):
        self.propose()
        item = self.review(visible_in=[REFERENCES[1]])
        self.assertEqual(item["status"], "refused")
        self.assertEqual(self.module.current_contract(self.project), CONTRACT)
        need = self.module.amendment_need(item)
        self.assertIn("Visible Change", need)
        self.assertIn(STANCE, need)
        self.assertIn(SEATS, need)

    def test_a_reviewer_disagreement_is_refused(self):
        for verdict in ({"contradiction": False}, {"smallest": False}):
            with self.subTest(verdict=verdict):
                self.setUp()
                self.propose()
                item = self.review(**verdict)
                self.assertEqual(item["status"], "refused")
                self.assertEqual(self.module.current_contract(self.project), CONTRACT)

    def test_the_cli_exits_one_on_a_refusal_and_prints_the_need(self):
        self.propose()
        event = self.module.read_contract_amendments(self.project)[1]
        path = self.write("review.json", {
            "amendment": 1, "packet_sha256": event["packet_sha256"], "reviewer": REVIEWER,
            "contradiction": True, "smallest": True, "visible_in": [REFERENCES[0]],
            "references_checked": list(REFERENCES), "reason": "The assembly image shows the face."})
        code, stdout, _ = self.main("--record-amendment-review", str(path))
        self.assertEqual(code, 1)
        self.assertIn("stage_proposal.py --run-root . need", stdout)

    def test_a_review_must_check_every_reference_and_come_from_a_fresh_reader(self):
        self.propose()
        with self.assertRaisesRegex(ValueError, "references_checked lacks"):
            self.review(checked=REFERENCES[:1])
        with self.assertRaisesRegex(ValueError, "cannot confirm its own"):
            self.review(reviewer="Workshop Manager")
        with self.assertRaisesRegex(ValueError, "different amendment packet"):
            self.review(packet_sha256="0" * 64)
        self.review()
        self.propose(rows=(SEATS, CLEAR), changes=[{"from": SEATS, "to": "The seats sit at Y 18.5."}])
        with self.assertRaisesRegex(ValueError, "already reviewed"):
            self.review(self.module.read_contract_amendments(self.project)[2])

    def test_a_component_reviewer_is_not_a_fresh_reader(self):
        state = self.project / "measure/component-rounds/wing"
        state.mkdir(parents=True)
        (state / "make-round-state.json").write_text(json.dumps({"reviewer_id": REVIEWER}))
        self.propose()
        with self.assertRaisesRegex(ValueError, "already reviewed"):
            self.review()

    def test_on_claude_code_the_reviewer_is_named_by_native_agent_id(self):
        os.environ[self.module.REVIEWER_RUNTIME_ENV] = "claude"
        self.addCleanup(os.environ.pop, self.module.REVIEWER_RUNTIME_ENV, None)
        self.propose()
        with self.assertRaisesRegex(ValueError, "native agent id"):
            self.review(reviewer="contract reviewer")
        self.assertEqual(self.review()["status"], "applied")

    def test_a_changed_packet_is_refused(self):
        event = self.propose()
        Path(event["packet"]).write_text("{}")
        with self.assertRaisesRegex(ValueError, "packet changed"):
            self.review()

    # -- a locked Component unlocks --------------------------------------------

    def test_changed_rows_unlock_a_locked_component(self):
        reviewed = {"round": 3, "identity": "A", "carry_key": "k", "agrees": True, "accepted": False,
                    "imported_helpers": {}, "contract_rows": "old"}
        locked = {"phase": self.module.LOCKED, "identity": "A", "round": 3, "shape_rounds": 0,
                  "reviewed": reviewed, "unlocks": []}
        self.assertFalse(self.module.round_policy(locked, {"identity": "B", "contract_rows": "old"})["admit"])
        admitted = self.module.round_policy(locked, {"identity": "B", "contract_rows": "new"})
        self.assertTrue(admitted["admit"])
        self.assertEqual(admitted["unlocks"], [{"kind": "contract-amendment", "contract_rows": "new"}])
        # A review recorded before contract_rows existed unlocks nothing.
        legacy = {**locked, "reviewed": {key: v for key, v in reviewed.items() if key != "contract_rows"}}
        self.assertFalse(self.module.round_policy(legacy, {"identity": "B", "contract_rows": "new"})["admit"])

    # -- Blocked Reports -------------------------------------------------------

    def blocked(self):
        path = self.write("blocked.json", {"rows": [STANCE, SEATS], "reason": "Nothing stands under the seats."})
        return self.module.report_blocked(self.project, path, "part_spine-housing.step.py")

    def clear(self, **answer):
        return self.module.clear_blocked(self.project, self.write("answer.json", answer))

    def test_an_applied_amendment_clears_the_report_it_names(self):
        self.blocked()
        self.propose(report=1)
        self.review()
        event = self.clear(report=1, amendment=1)
        self.assertEqual(event["event"], "amendment")
        reports = self.module.read_blocked_reports(self.project)
        self.assertEqual(reports[1]["status"], "amended")
        self.assertEqual(self.module.open_blocked(self.project), [])
        guard = make_round_guard.blocked_reports(
            (self.project / "measure/blocked-reports.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(guard[1]["status"], "amended")
        spec = importlib.util.spec_from_file_location("stage_proposal_amendment_test", STAGE_PROPOSAL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        tool._refuse_open_blocked_reports(self.project)

    def test_a_refused_or_unrelated_amendment_does_not_clear_a_report(self):
        self.blocked()
        with self.assertRaisesRegex(ValueError, "not open"):
            self.propose(report=2)
        self.propose(report=1)
        with self.assertRaisesRegex(ValueError, "proposed, not applied"):
            self.clear(report=1, amendment=1)
        self.review(smallest=False)
        with self.assertRaisesRegex(ValueError, "refused, not applied"):
            self.clear(report=1, amendment=1)
        self.clear(report=1, need="Contract Contradiction: '%s' vs '%s'" % (STANCE, SEATS))
        self.blocked()
        self.propose(rows=(STANCE, SEATS))
        self.review(self.module.read_contract_amendments(self.project)[2], reviewer="b1b2c3d4e5f6a7b8c")
        with self.assertRaisesRegex(ValueError, "does not name Blocked Report 2"):
            self.clear(report=2, amendment=2)

    # -- the host --------------------------------------------------------------

    def test_the_host_records_each_amendment_by_hash(self):
        self.blocked()
        self.propose(report=1)
        self.review()
        self.clear(report=1, amendment=1)
        from workshop.make.blocked_reports import verify_no_open_blocked_reports
        reports = verify_no_open_blocked_reports(self.project, wish_sha256=self.wish_sha256)
        self.assertEqual(reports[0]["cleared_by"], "amendment")
        records = self.verify(blocked_reports=reports)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["status"], "applied")
        self.assertEqual(record["changes"], [{"row": "R01", "from": STANCE, "to": NEW_STANCE}])
        self.assertEqual(record["contract_sha256"], contract_digest(CONTRACT))
        self.assertEqual(record["amended_sha256"],
                         contract_digest(self.module.current_contract(self.project)))
        self.assertEqual(record["review"]["reviewer"], REVIEWER)
        self.assertEqual(record["review"]["verdict"]["visible_in"], [])
        listed = run_contract_amendments(self.run_root, contract=CONTRACT, wish_sha256=self.wish_sha256)
        self.assertEqual([(item["attempt"], item["status"]) for item in listed], [("r0001", "applied")])

    def test_the_host_refuses_a_missing_review(self):
        self.propose()
        with self.assertRaisesRegex(ContractError, "no recorded review"):
            self.verify()
        listed = run_contract_amendments(self.run_root, contract=CONTRACT, wish_sha256=self.wish_sha256)
        self.assertEqual(listed[0]["status"], "proposed")

    def test_the_host_refuses_a_changed_contract_hash(self):
        self.propose()
        self.review()
        ledger = self.project / "measure/contract-amendments.jsonl"
        events = [json.loads(line) for line in ledger.read_text().splitlines()]
        events[0]["contract_sha256"] = "1" * 64
        ledger.write_text("".join(json.dumps(event) + "\n" for event in events))
        with self.assertRaisesRegex(ContractError, "was proposed against contract"):
            self.verify()
        listed = run_contract_amendments(self.run_root, contract=CONTRACT, wish_sha256=self.wish_sha256)
        self.assertEqual(listed[0]["status"], "invalid")

    def test_the_host_refuses_a_row_quoted_wrongly(self):
        self.propose()
        self.review()
        ledger = self.project / "measure/contract-amendments.jsonl"
        events = [json.loads(line) for line in ledger.read_text().splitlines()]
        events[0]["changes"][0]["row"] = "R03"
        ledger.write_text("".join(json.dumps(event) + "\n" for event in events))
        with self.assertRaisesRegex(ContractError, "reads as it quotes"):
            self.verify()

    def test_the_host_derives_a_disagreement_and_a_visible_change_from_the_verdict(self):
        self.blocked()
        self.propose(report=1)
        self.review(visible_in=[REFERENCES[0]])
        records = self.verify()
        self.assertEqual(records[0]["status"], "refused")
        # A report cleared by a refused amendment is refused, whatever the
        # ledger says about it.
        forged = [{"report": 1, "answers": [{"kind": "amendment", "amendment": 1,
                                             "amended_sha256": records[0]["amended_sha256"]}]}]
        with self.assertRaisesRegex(ContractError, "not an applied amendment"):
            self.verify(blocked_reports=forged)

    def test_the_host_refuses_another_runs_ledger_and_a_changed_packet(self):
        event = self.propose()
        self.review()
        with self.assertRaisesRegex(ContractError, "not bound to this run"):
            verify_contract_amendments(self.project, contract=CONTRACT, wish_sha256="2" * 64,
                                       references=self.references)
        Path(event["packet"]).write_text("{}")
        with self.assertRaisesRegex(ContractError, "packet is missing or changed"):
            self.verify()

    def test_on_claude_code_the_host_proves_the_contract_reviewer(self):
        self.propose()
        self.review()
        host_state = self.run_root / "host-state"
        guard = host_state / MAKE_ROUND_GUARD_DIRECTORY
        guard.mkdir(parents=True)
        check = contract_reviewer_check(host_state)
        with self.assertRaisesRegex(ContractError, "not a contract-reviewer this run started"):
            self.verify(reviewer_check=check)
        (guard / make_round_guard.SUBAGENT_LOG_NAME).write_text(
            json.dumps({"agent_id": REVIEWER, "agent_type": "contract-reviewer"}) + "\n")
        reads = [make_round_guard.reviewer_read({
            "tool_name": "Read", "agent_type": "contract-reviewer", "agent_id": REVIEWER,
            "tool_input": {"file_path": str(path)}}) for path, _ in self.references.values()]
        (guard / make_round_guard.READ_LOG_NAME).write_text(json.dumps(reads[0]) + "\n")
        with self.assertRaisesRegex(ContractError, "did not read ref-02-spine-housing.png"):
            self.verify(reviewer_check=contract_reviewer_check(host_state))
        (guard / make_round_guard.READ_LOG_NAME).write_text(
            "".join(json.dumps(read) + "\n" for read in reads))
        self.assertEqual(self.verify(reviewer_check=contract_reviewer_check(host_state))[0]["status"],
                         "applied")

    # -- the finalizer and the guard -------------------------------------------

    def test_the_finalizer_refuses_make_while_an_amendment_awaits_review(self):
        script = self.run_root / ".agents/skills/make-round/scripts"
        script.mkdir(parents=True)
        (script / "make_round").write_bytes(self.module_source())
        spec = importlib.util.spec_from_file_location("stage_proposal_amendment_finalizer", STAGE_PROPOSAL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        tool._refuse_unreviewed_contract_amendments(self.run_root, self.project)
        self.propose()
        with self.assertRaisesRegex(tool.ProposalError, "awaits its review"):
            tool._refuse_unreviewed_contract_amendments(self.run_root, self.project)
        self.review()
        tool._refuse_unreviewed_contract_amendments(self.run_root, self.project)
        current = tool._current_design_contract(self.run_root, self.wish_sha256, self.project)
        self.assertEqual(current["requirements"][0]["text"], NEW_STANCE)

    def module_source(self):
        return Path(self.module.__file__).read_bytes()

    def test_the_guard_keeps_amendments_to_the_root_and_logs_contract_reviewer_reads(self):
        def call(command, agent_type=None):
            event = {"tool_input": {"command": command}}
            if agent_type:
                event.update(agent_type=agent_type, agent_id="x")
            return make_round_guard.decide(event, issue=lambda *a: "0" * 32)

        for flag in ("--propose-amendment p.json", "--record-amendment-review r.json"):
            self.assertIsNone(call("make_round cad %s" % flag))
            denied = call("make_round cad %s" % flag, "component-worker")
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("Contract Amendment", denied["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIsNone(call("make_round cad --contract-amendments", "component-worker"))
        record = make_round_guard.reviewer_read({
            "tool_name": "Read", "agent_type": "contract-reviewer", "agent_id": REVIEWER,
            "tool_input": {"file_path": str(self.references[REFERENCES[0]][0])}})
        self.assertEqual(record["sha256"], self.references[REFERENCES[0]][1])


if __name__ == "__main__":
    unittest.main()
