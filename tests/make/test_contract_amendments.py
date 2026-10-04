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
    OWNER_AMENDMENTS_MARKER,
    apply_owner_amendments,
    contract_digest,
    owner_affects,
    owner_contract_changes,
    owner_objective,
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
# Issue #96: STANCE with only ", the mating plane" deleted.
SMALLER_STANCE = "The spine housing prints on its front face. No part needs support."
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
        self.propose(rows=(STANCE, SEATS), changes=[{"from": STANCE, "to": SMALLER_STANCE}])
        self.review(self.module.read_contract_amendments(self.project)[2], reviewer="b1b2c3d4e5f6a7b8c")
        with self.assertRaisesRegex(ValueError, "does not name Blocked Report 2"):
            self.clear(report=2, amendment=2)

    # -- the Smaller Retry (issue #96) -----------------------------------------

    def ledger_events(self):
        ledger = self.project / "measure/contract-amendments.jsonl"
        return ledger, [json.loads(line) for line in ledger.read_text().splitlines()]

    def write_ledger(self, events):
        ledger = self.project / "measure/contract-amendments.jsonl"
        ledger.write_text("".join(json.dumps(event) + "\n" for event in events))

    def retry(self, to=SMALLER_STANCE, **extra):
        return self.propose(changes=[{"from": STANCE, "to": to}], **extra)

    def amendment(self, number):
        return self.module.read_contract_amendments(self.project)[number]

    def test_deletions_only_means_a_shorter_subsequence_without_new_words(self):
        for module in (self.module, __import__("workshop.make.contract_amendments", fromlist=["x"])):
            with self.subTest(module=module.__name__):
                self.assertTrue(module.deletions_only(STANCE, SMALLER_STANCE))
                self.assertFalse(module.deletions_only(STANCE, NEW_STANCE))
                self.assertFalse(module.deletions_only(STANCE, STANCE))
                # A character subsequence that respells a word adds a word.
                self.assertFalse(module.deletions_only(STANCE, STANCE.replace("plane", "plan")))
                self.assertFalse(module.deletions_only(STANCE, STANCE.replace("mating ", "mating flat ")))

    def test_a_smaller_change_refusal_allows_one_deletion_only_retry_that_applies(self):
        self.propose()
        event = self.amendment(1)
        path = self.write("review.json", {
            "amendment": 1, "packet_sha256": event["packet_sha256"], "reviewer": REVIEWER,
            "contradiction": True, "smallest": False, "visible_in": [],
            "references_checked": list(REFERENCES),
            "reason": "Deleting only ', the mating plane' removes the contradiction."})
        code, stdout, _ = self.main("--record-amendment-review", str(path))
        self.assertEqual(code, 1)
        self.assertIn("You may propose it once", stdout)
        self.assertIn("Deleting only ', the mating plane'", stdout)
        retried = self.retry()
        self.assertEqual(retried["amendment"], 2)
        self.assertEqual(retried["retry_of"], 1)
        self.assertEqual(json.loads(Path(retried["packet"]).read_bytes())["retry_of"], 1)
        item = self.review(self.amendment(2), reviewer="b1b2c3d4e5f6a7b8c")
        self.assertEqual(item["status"], "applied")
        self.assertEqual(self.module.current_contract(self.project)["requirements"][0]["text"],
                         SMALLER_STANCE)
        code, stdout, _ = self.main("--contract-amendments")
        self.assertEqual(code, 0)
        self.assertIn("Smaller Retry of amendment 1", stdout)
        records = self.verify()
        self.assertEqual([(r["status"], r["retry_of"]) for r in records],
                         [("refused", None), ("applied", 1)])

    def test_a_retry_that_adds_or_respells_words_is_refused(self):
        self.propose()
        self.review(smallest=False)
        for to in (NEW_STANCE, STANCE.replace("plane", "plan"),
                   SMALLER_STANCE.replace("No part", "No printed part")):
            with self.subTest(to=to):
                with self.assertRaisesRegex(ValueError, "only deletes words"):
                    self.retry(to=to)
        with self.assertRaisesRegex(ValueError, "changes only rows it changed"):
            self.propose(changes=[{"from": SEATS, "to": "The wing hinge seats sit at Y 17.5."}])
        # The host refuses the same retry forged into the ledger.
        self.retry()
        self.review(self.amendment(2), reviewer="b1b2c3d4e5f6a7b8c")
        _, events = self.ledger_events()
        events[2]["changes"][0]["to"] = NEW_STANCE
        self.write_ledger(events)
        with self.assertRaisesRegex(ContractError, "only deletes words"):
            self.verify()

    def test_a_third_proposal_for_the_same_contradiction_is_refused(self):
        self.propose()
        self.review(smallest=False)
        self.retry()
        item = self.review(self.amendment(2), reviewer="b1b2c3d4e5f6a7b8c", smallest=False)
        self.assertEqual(item["status"], "refused")
        self.assertFalse(self.module.retry_open(self.module.read_contract_amendments(self.project), item))
        shorter = "The spine housing prints on its front face."
        with self.assertRaisesRegex(ValueError, "one Smaller Retry at most"):
            self.retry(to=shorter)
        # The host refuses a third proposal forged into the ledger.
        _, events = self.ledger_events()
        forged = dict(events[2], amendment=3)
        forged["changes"] = [dict(events[2]["changes"][0], to=shorter)]
        self.write_ledger(events + [forged])
        with self.assertRaisesRegex(ContractError, "one Smaller Retry at most"):
            self.verify()

    def test_a_retry_reviewed_by_the_refusing_reviewer_is_refused(self):
        self.propose()
        self.review(smallest=False)
        self.retry()
        with self.assertRaisesRegex(ValueError, "already reviewed"):
            self.review(self.amendment(2))
        with self.assertRaisesRegex(ValueError, "cannot confirm its own"):
            self.review(self.amendment(2), reviewer="workshop-manager")
        self.review(self.amendment(2), reviewer="b1b2c3d4e5f6a7b8c")
        _, events = self.ledger_events()
        events[3]["reviewer"] = REVIEWER
        self.write_ledger(events)
        with self.assertRaisesRegex(ContractError, "already reviewed Contract Amendment 1"):
            self.verify()

    def test_a_retry_after_a_contradiction_or_visibility_refusal_is_refused(self):
        for verdict in ({"contradiction": False, "smallest": False},
                        {"smallest": False, "visible_in": [REFERENCES[1]]},
                        {"contradiction": False}):
            with self.subTest(verdict=verdict):
                self.setUp()
                self.propose()
                item = self.review(**verdict)
                self.assertEqual(item["status"], "refused")
                self.assertFalse(self.module.retry_open(
                    self.module.read_contract_amendments(self.project), item))
                with self.assertRaisesRegex(ValueError, "only a refusal that names a smaller change"):
                    self.retry()
                # The host refuses the retry forged into the ledger.
                _, events = self.ledger_events()
                forged = dict(events[0], amendment=2, retry_of=1)
                forged["changes"] = [dict(events[0]["changes"][0], to=SMALLER_STANCE)]
                self.write_ledger(events + [forged])
                with self.assertRaisesRegex(ContractError, "only a refusal that names a smaller change"):
                    self.verify()

    def test_after_an_applied_amendment_the_same_rows_are_not_proposed_again(self):
        self.propose(rows=(STANCE, CLEAR), changes=[{"from": SEATS, "to": "The seats sit at Y 18.5."}])
        self.review()
        with self.assertRaisesRegex(ValueError, "was applied"):
            self.propose(rows=(CLEAR, STANCE))

    def test_the_host_refuses_a_retry_that_hides_its_retry_of(self):
        self.propose()
        self.review(smallest=False)
        self.retry()
        self.review(self.amendment(2), reviewer="b1b2c3d4e5f6a7b8c")
        _, events = self.ledger_events()
        del events[2]["retry_of"]
        self.write_ledger(events)
        with self.assertRaisesRegex(ContractError, "retry_of None, but the ledger makes it 1"):
            self.verify()

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

    # -- Owner Contract Amendments (issue #100) ---------------------------------

    def owner(self, changes, number=1, in_run=0):
        """Write the host's run-root amendments file with one more owner
        amendment, as the host does on resume."""

        path = self.run_root / "CONTRACT-AMENDMENTS.json"
        document = json.loads(path.read_text()) if path.is_file() else {
            "schema_version": 1, "reference_cameras": {}, "amendments": []}
        record = {"kind": "owner-contract-amendment", "owner_amendment": number, "source": "owner",
                  "status": "applied", "changes": changes, "affects": [], "in_run_amendments": in_run,
                  "contract_sha256": "c" * 64, "amended_sha256": "d" * 64, "prose_diff": None}
        document.setdefault("owner_amendments", []).append(record)
        path.write_text(json.dumps(document))
        return record

    def test_owner_rows_apply_after_the_in_run_amendments_and_unlock_only_their_components(self):
        self.propose()
        self.review()
        rows = {role: self.module.contract_rows(self.project, role) for role in ("spine-housing", "wing")}
        self.owner([{"row": "R03", "scope": "assembly", "from": CLEAR, "to": "The wing gears keep 0.6 mm."}],
                   in_run=1)
        current = self.module.current_contract(self.project)
        self.assertEqual([item["text"] for item in current["requirements"]],
                         [NEW_STANCE, SEATS, "The wing gears keep 0.6 mm."])
        # An owner's assembly row is no Component's row: every lock holds.
        self.assertEqual({role: self.module.contract_rows(self.project, role) for role in rows}, rows)
        self.owner([{"row": "R02", "scope": "geometry:spine-housing", "from": SEATS, "to": "Seats at Y 17.6."}],
                   number=2, in_run=1)
        after = {role: self.module.contract_rows(self.project, role) for role in rows}
        self.assertNotEqual(after["spine-housing"], rows["spine-housing"])
        self.assertEqual(after["wing"], rows["wing"])
        # The finalizer matches the signature review against the same rows.
        script = self.run_root / ".agents/skills/make-round/scripts"
        script.mkdir(parents=True)
        (script / "make_round").write_bytes(self.module_source())
        spec = importlib.util.spec_from_file_location("stage_proposal_owner_amendment", STAGE_PROPOSAL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        finalized = tool._current_design_contract(self.run_root, self.wish_sha256, self.project)
        self.assertEqual(finalized, self.module.current_contract(self.project))
        self.assertEqual([item["text"] for item in finalized["requirements"]],
                         [NEW_STANCE, "Seats at Y 17.6.", "The wing gears keep 0.6 mm."])

    def test_the_finalizer_reads_an_owner_amendment_without_a_ledger(self):
        script = self.run_root / ".agents/skills/make-round/scripts"
        script.mkdir(parents=True)
        (script / "make_round").write_bytes(self.module_source())
        spec = importlib.util.spec_from_file_location("stage_proposal_owner_only", STAGE_PROPOSAL)
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        self.owner([{"row": "R01", "scope": "geometry:spine-housing", "from": STANCE, "to": NEW_STANCE}])
        current = tool._current_design_contract(self.run_root, self.wish_sha256, self.project)
        self.assertEqual(current["requirements"][0]["text"], NEW_STANCE)

    def test_an_owner_amendment_closes_in_run_amendments(self):
        self.owner([{"row": "R03", "scope": "assembly", "from": CLEAR, "to": "The wing gears keep 0.6 mm."}])
        with self.assertRaisesRegex(ValueError, "owner amended this contract"):
            self.propose()
        code, stdout, _stderr = self.main("--contract-amendments")
        self.assertEqual(code, 0)
        self.assertIn("owner amendment 1  APPLIED by the owner", stdout)
        self.assertIn("R03  %s\n    -> The wing gears keep 0.6 mm." % CLEAR, stdout)

    def test_the_host_replay_refuses_an_in_run_amendment_after_the_owners(self):
        self.propose()
        self.review()
        owner = {"kind": "owner-contract-amendment", "owner_amendment": 1, "in_run_amendments": 0,
                 "changes": []}
        with self.assertRaisesRegex(ContractError, "proposed after the owner amended the contract"):
            self.verify(owner_amendments=[owner])
        listed = self.verify(owner_amendments=[{**owner, "in_run_amendments": 1}])
        self.assertEqual([item.get("kind") for item in listed],
                         ["contract-amendment", "owner-contract-amendment"])

    def test_owner_changes_are_row_and_interface_text_only(self):
        current = {**CONTRACT, "interfaces": [
            {"id": "wing-housing", "kind": "static", "components": ["wing#1", "spine-housing"], "text": "A"}]}
        amended = json.loads(json.dumps(current))
        amended["requirements"][2]["text"] = "B"
        amended["interfaces"][0]["text"] = "C"
        changes = owner_contract_changes(current, amended)
        self.assertEqual(changes, [
            {"row": "R03", "scope": "assembly", "from": CLEAR, "to": "B"},
            {"row": "interface:wing-housing", "scope": "interface:wing-housing", "from": "A", "to": "C"}])
        self.assertEqual(owner_affects(current, changes), ["spine-housing", "wing"])
        self.assertEqual(owner_affects(current, changes[:1]), [])
        applied = apply_owner_amendments(current, [{"changes": changes}])
        self.assertEqual((applied["requirements"][2]["text"], applied["interfaces"][0]["text"]), ("B", "C"))
        with self.assertRaisesRegex(ContractError, "does not have"):
            apply_owner_amendments(current, [{"changes": [{"row": "R09", "to": "x"}]}])
        amended["references"][0]["camera"] = [0, 0]
        amended["requirements"][0]["id"] = "R09"
        amended["interfaces"][0]["kind"] = "coupled"
        with self.assertRaises(ContractError) as refused:
            owner_contract_changes(current, amended)
        for named in ("it changes references", "rescopes a requirement", "Interface wing-housing's kind"):
            self.assertIn(named, str(refused.exception))

    def test_the_owner_objective_keeps_the_sealed_name_line(self):
        block = "```design-contract\n{}\n```\n"
        sealed = "Name this toy exactly: Broken God v09.\n\n# Broken God\nHard stops.\n" + block
        amended = "Name this toy exactly: Broken God v10.\n\n# Broken God\nA detent.\n" + block
        objective, diff = owner_objective(sealed, sealed, amended)
        self.assertEqual(objective, amended.replace("v10", "v09"))
        self.assertIn("-Hard stops.\n+A detent.", diff)
        # A file without a name line takes the sealed one.
        objective, _diff = owner_objective(sealed, sealed, amended.split("\n", 2)[2])
        self.assertTrue(objective.startswith("Name this toy exactly: Broken God v09.\n\n# Broken God"))
        # Unchanged prose is no diff, whatever the block holds.
        self.assertIsNone(owner_objective(sealed, sealed, sealed.replace("{}", '{"a": 1}'))[1])
        # A correction run's objective is its brief: there is no prose to amend.
        self.assertEqual(owner_objective("Fix the wings.", "Fix the wings.", amended), (None, None))
        with self.assertRaisesRegex(ContractError, "sealed none"):
            owner_objective("# Broken God\n" + block, "# Broken God\n" + block, amended)

    def test_both_tools_carry_the_owner_amendment_marker(self):
        self.assertIn(OWNER_AMENDMENTS_MARKER, self.module_source())
        self.assertIn(OWNER_AMENDMENTS_MARKER, STAGE_PROPOSAL.read_bytes())

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
