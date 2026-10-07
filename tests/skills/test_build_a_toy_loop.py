"""The build-a-toy unattended loop's deterministic tools (issue #89).

ledger.py validates the ledger, classifies a stop from its evidence and says
what the loop does next; tally.py, tokens.py, runpaths.py and snapshot.py read
a run's files without any machine-specific path.
"""

import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[2]
SCRIPTS = REPOSITORY / ".claude" / "skills" / "build-a-toy" / "scripts"


def _load(name):
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(f"build_a_toy_{name}_under_test", SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ledger = _load("ledger")
runpaths = _load("runpaths")
tally = _load("tally")
tokens = _load("tokens")
snapshot = _load("snapshot")


def _stop(attempt, klass="other", locked=0, repeats=0, **extra):
    stop = {
        "attempt": attempt,
        "wish_id": f"wish-{attempt}",
        "stop_category": "budget",
        "status": "active",
        "class": klass,
        "evidence": ["receipt stop_category budget"],
        "progress": {"locked": locked, "repeated_print_defects": repeats},
        "budget_raised": False,
        "resolution": "",
    }
    stop.update(extra)
    return stop


def _owner_raise_stop(attempt, before, after):
    return _stop(attempt, budget_raised="owner", owner_decision={
        "at": "2026-10-06T04:01:03Z", "limit_before": before, "limit_after": after,
    })


def _contradiction(ident, attempt, signature, amendment, visible=False, approved="not-needed"):
    return {
        "id": ident,
        "attempt": attempt,
        "signature": signature,
        "rows": ["the spine housing prints on its front face", "the wings sweep the layer under the back wall"],
        "amendment": amendment,
        "visible": visible,
        "approved": approved,
        "applied": approved is not None,
        "reaudit": f"build-a-toy/drafts/{amendment}-notes.md" if approved else None,
        "design_check": {"name": "swept-volume-over-ceiling", "issue": None, "status": "merged"},
    }


def _ledger():
    return {
        "contract": "toys-spec/toy/CONTRACT.md",
        "title": "Toy",
        "rounds": [],
        "contract_versions": {"amend-a": {}, "amend-b": {}},
        "loop": {
            "schema": 1,
            "state": "launch",
            "attempt": 2,
            "wish_id": "wish-2",
            "source_commit": "abc1234",
            "awaiting": None,
            "updated": "2026-10-03T00:00:00Z",
        },
        "stops": [_stop(1, locked=1, repeats=5), _stop(2, "contract-contradiction", locked=3, repeats=2)],
        "contract_contradictions": [_contradiction("cc-1", 2, "swept-volume-over-ceiling:housing", "amend-a")],
        "harness_issues": [
            {"number": 7, "title": "x", "opened_by_loop": True, "attempt": 1, "status": "merged",
             "merge_commit": "def5678"},
        ],
        "cost_units": {"cap": 100, "by_attempt": {"1": 10.5, "2": 20.25}, "unmeasured_attempts": [],
                       "total": 30.75},
    }


class LedgerCheckTest(unittest.TestCase):
    def test_a_complete_ledger_is_valid(self):
        self.assertEqual(ledger.check(_ledger()), [])

    def test_a_ledger_from_before_the_loop_is_valid_and_asks_to_migrate(self):
        legacy = {"contract": "c", "title": "t", "rounds": []}

        self.assertEqual(ledger.check(legacy), [])
        self.assertEqual(ledger.next_action(legacy)["action"], "migrate")

    def test_a_visible_change_cannot_skip_the_owner(self):
        data = _ledger()
        data["contract_contradictions"][0]["visible"] = True

        self.assertTrue(any("owner's approval" in e for e in ledger.check(data)))

    def test_approval_is_the_owner_or_not_needed(self):
        data = _ledger()
        data["contract_contradictions"][0]["approved"] = "yes"

        self.assertTrue(any("`owner <date>`" in e for e in ledger.check(data)))

    def test_an_amendment_is_approved_before_it_is_applied(self):
        data = _ledger()
        data["contract_contradictions"][0].update(approved=None, applied=True)

        self.assertTrue(any("applied before it was approved" in e for e in ledger.check(data)))

    def test_an_applied_amendment_needs_a_whole_contract_reaudit(self):
        data = _ledger()
        data["contract_contradictions"][0]["reaudit"] = None

        self.assertTrue(any("re-audit" in e for e in ledger.check(data)))

    def test_a_contradiction_quotes_two_rows_and_names_a_known_amendment(self):
        data = _ledger()
        data["contract_contradictions"][0]["rows"] = ["only one"]
        data["contract_contradictions"][0]["amendment"] = "amend-z"

        errors = ledger.check(data)
        self.assertTrue(any("at least two" in e for e in errors))
        self.assertTrue(any("amend-z" in e for e in errors))

    def test_the_cost_total_is_the_sum_of_the_attempts(self):
        data = _ledger()
        data["cost_units"]["total"] = 12

        self.assertTrue(any("not the sum" in e for e in ledger.check(data)))

    def test_one_budget_raise_per_attempt(self):
        data = _ledger()
        data["stops"] = [_stop(3, budget_raised=True), _stop(3, budget_raised=True)]

        self.assertTrue(any("raised its token budget 2 times" in e for e in ledger.check(data)))

    def test_one_automatic_raise_passes(self):
        data = _ledger()
        data["stops"].append(_stop(3, "budget-progressing", locked=4, budget_raised=True))

        self.assertEqual(ledger.check(data), [])

    def test_an_owner_raise_after_the_automatic_one_passes(self):
        # Broken God attempt 18 (#104): +100M automatically on 2026-10-04,
        # then a second budget stop where the owner raised 200M -> 240M.
        data = _ledger()
        data["stops"] += [
            _stop(3, "budget-progressing", locked=4, budget_raised=True),
            _owner_raise_stop(3, 200_000_000, 240_000_000),
            _owner_raise_stop(3, 240_000_000, 280_000_000),
        ]

        self.assertEqual(ledger.check(data), [])

    def test_a_malformed_owner_raise_fails(self):
        cases = {
            "needs at, limit_before and limit_after": lambda s: s.pop("owner_decision"),
            "owner_decision.at": lambda s: s["owner_decision"].update(at=""),
            "limit_before < limit_after": lambda s: s["owner_decision"].update(limit_after=100_000_000),
            "an owner raise answers an `other` stop": lambda s: s.update({"class": "budget-progressing"}),
            "must be true, false or": lambda s: s.update(budget_raised="yes"),
        }
        for message, damage in cases.items():
            with self.subTest(message):
                data = _ledger()
                stop = _owner_raise_stop(3, 200_000_000, 240_000_000)
                damage(stop)
                data["stops"].append(stop)

                self.assertTrue(any(message in e for e in ledger.check(data)), ledger.check(data))

    def test_an_owner_decision_without_an_owner_raise_fails(self):
        data = _ledger()
        data["stops"].append(_stop(3, owner_decision={"at": "x", "limit_before": 1, "limit_after": 2}))

        self.assertTrue(any("budget_raised is not" in e for e in ledger.check(data)))

    def test_no_budget_progressing_stop_after_a_raise_in_its_attempt(self):
        data = _ledger()
        data["stops"] += [
            _owner_raise_stop(3, 200_000_000, 240_000_000),
            _stop(3, "budget-progressing", locked=6),
        ]

        self.assertTrue(any("after a raise in attempt 3" in e for e in ledger.check(data)))

    def test_a_merged_issue_names_its_merge_commit(self):
        data = _ledger()
        data["harness_issues"][0]["merge_commit"] = None

        self.assertTrue(any("merge_commit" in e for e in ledger.check(data)))

    def test_the_loop_never_implements_an_issue_it_did_not_open(self):
        data = _ledger()
        data["harness_issues"][0].update(opened_by_loop=False, status="implementing")

        self.assertTrue(any("only issues it opened" in e for e in ledger.check(data)))

    def test_awaiting_the_owner_names_the_reasons(self):
        data = _ledger()
        data["loop"]["state"] = "awaiting-owner"

        self.assertTrue(any("reasons is empty" in e for e in ledger.check(data)))

    def test_an_unknown_class_or_state_is_refused(self):
        data = _ledger()
        data["loop"]["state"] = "thinking"
        data["stops"][0]["class"] = "bad luck"

        errors = ledger.check(data)
        self.assertTrue(any("loop.state" in e for e in errors))
        self.assertTrue(any("stops[0].class" in e for e in errors))


class StopConditionTest(unittest.TestCase):
    def test_nothing_holds_on_a_healthy_ledger(self):
        self.assertEqual(ledger.stop_conditions(_ledger()), [])

    def test_a_fixed_contradiction_that_comes_back_stops_the_loop(self):
        data = _ledger()
        data["contract_versions"]["amend-b"] = {}
        data["contract_contradictions"].append(
            _contradiction("cc-2", 4, "swept-volume-over-ceiling:housing", "amend-b", approved=None)
        )

        reasons = ledger.stop_conditions(data)
        self.assertEqual(len(reasons), 1)
        self.assertIn("came back in attempt 4", reasons[0])

    def test_the_owner_can_acknowledge_a_recurrence(self):
        data = _ledger()
        data["contract_versions"]["amend-b"] = {}
        later = _contradiction("cc-2", 4, "swept-volume-over-ceiling:housing", "amend-b", approved=None)
        later["recurrence_acknowledged"] = "owner 2026-10-04"
        data["contract_contradictions"].append(later)

        self.assertEqual(ledger.stop_conditions(data), [])

    def test_the_same_check_on_another_component_is_not_a_recurrence(self):
        data = _ledger()
        data["contract_contradictions"].append(
            _contradiction("cc-2", 4, "swept-volume-over-ceiling:chest", "amend-b", approved=None)
        )

        self.assertEqual(ledger.stop_conditions(data), [])

    def test_three_attempts_without_progress_stop_the_loop(self):
        data = _ledger()
        data["stops"] = [
            _stop(1, locked=4, repeats=3),
            _stop(2, locked=4, repeats=3),
            _stop(3, locked=3, repeats=5),
            _stop(4, locked=3, repeats=5),
        ]

        reasons = ledger.stop_conditions(data)
        self.assertTrue(any("3 consecutive attempts" in r for r in reasons))

    def test_the_owner_can_clear_the_no_progress_count(self):
        data = _ledger()
        data["stops"] = [_stop(n, locked=4, repeats=3) for n in (1, 2, 3, 4)]
        self.assertEqual(len(ledger.stop_conditions(data)), 1)

        data["loop"]["no_progress_cleared_through"] = 4
        self.assertEqual(ledger.stop_conditions(data), [])

    def test_progress_in_one_attempt_resets_the_count(self):
        data = _ledger()
        data["stops"] = [
            _stop(1, locked=4, repeats=3),
            _stop(2, locked=4, repeats=3),
            _stop(3, locked=5, repeats=3),
            _stop(4, locked=5, repeats=3),
            _stop(5, locked=5, repeats=3),
        ]

        self.assertEqual(ledger.stop_conditions(data), [])

    def test_passing_the_cost_cap_stops_the_loop(self):
        data = _ledger()
        data["cost_units"].update(by_attempt={"1": 60, "2": 40.5}, total=100.5)

        self.assertTrue(any("passed the cap of 100" in r for r in ledger.stop_conditions(data)))

    def test_a_failed_or_conflicting_harness_fix_stops_the_loop(self):
        data = _ledger()
        data["harness_issues"] += [
            {"number": 8, "title": "y", "opened_by_loop": True, "attempt": 2, "status": "conflict",
             "merge_commit": None},
            {"number": 9, "title": "z", "opened_by_loop": True, "attempt": 2, "status": "failed",
             "merge_commit": None},
        ]

        reasons = ledger.stop_conditions(data)
        self.assertTrue(any("#8 meets a merge conflict" in r for r in reasons))
        self.assertTrue(any("#9 fails tests" in r for r in reasons))

    def test_a_visible_change_waits_for_the_owner(self):
        data = _ledger()
        data["contract_contradictions"][0].update(visible=True, approved=None, applied=False)

        self.assertTrue(any("awaits the owner's approval" in r for r in ledger.stop_conditions(data)))


class NextActionTest(unittest.TestCase):
    def test_launch_the_next_attempt_from_the_recorded_commit(self):
        action = ledger.next_action(_ledger())

        self.assertEqual(action["action"], "launch")
        self.assertEqual(action["attempt"], 3)
        self.assertEqual(action["source_commit"], "abc1234")

    def test_watch_a_running_attempt(self):
        data = _ledger()
        data["loop"].update(state="watching", wish_id="wish-3", attempt=3)

        self.assertEqual(ledger.next_action(data), {
            "action": "watch", "wish_id": "wish-3", "why": ["an attempt is running"],
        })

    def test_a_stop_with_no_class_is_diagnosed(self):
        data = _ledger()
        data["loop"].update(state="diagnosing", wish_id="wish-3", attempt=3)

        self.assertEqual(ledger.next_action(data)["action"], "diagnose")

    def test_a_progressing_budget_stop_is_resumed_once(self):
        data = _ledger()
        data["loop"].update(state="fixing", wish_id="wish-3", attempt=3)
        data["stops"].append(_stop(3, "budget-progressing", locked=4, repeats=1))

        action = ledger.next_action(data)
        self.assertEqual(action["action"], "resume-budget")
        self.assertEqual(action["raise_tokens"], 100_000_000)

        data["stops"][-1]["budget_raised"] = True
        data["stops"].append(_stop(3, "budget-progressing", locked=5, repeats=1))
        self.assertNotEqual(ledger.next_action(data)["action"], "resume-budget")

    def test_an_owner_raise_never_brings_back_the_automatic_one(self):
        data = _ledger()
        data["loop"].update(state="fixing", wish_id="wish-3", attempt=3)
        data["stops"] += [
            _owner_raise_stop(3, 200_000_000, 240_000_000),
            _stop(3, "budget-progressing", locked=6),
        ]

        self.assertNotEqual(ledger.next_action(data)["action"], "resume-budget")

    def test_pending_fixes_are_listed(self):
        data = _ledger()
        data["loop"].update(state="fixing", wish_id="wish-2")
        data["contract_contradictions"][0].update(approved=None, applied=False)
        data["harness_issues"].append(
            {"number": 11, "title": "w", "opened_by_loop": True, "attempt": 2, "status": "implementing",
             "merge_commit": None})

        action = ledger.next_action(data)
        self.assertEqual(action["action"], "fix")
        self.assertEqual(action["pending"], ["cc-1: apply amend-a and re-audit", "#11: implementing"])

    def test_an_approved_visible_change_is_applied_next(self):
        data = _ledger()
        data["loop"].update(state="fixing", wish_id="wish-2")
        data["contract_contradictions"][0].update(visible=True, approved="owner 2026-10-04", applied=False)

        self.assertEqual(ledger.next_action(data)["pending"], ["cc-1: apply amend-a and re-audit"])

    def test_an_invisible_root_fix_resumes_the_stopped_run_with_an_owner_amendment(self):
        # Issue #100: the run keeps its locked Components instead of a relaunch.
        data = _ledger()
        data["loop"].update(state="fixing", wish_id="wish-2")

        action = ledger.next_action(data)
        self.assertEqual(action["action"], "resume-amendment")
        self.assertEqual((action["wish_id"], action["contract"], action["contradictions"]),
                         ("wish-2", "toys-spec/toy/CONTRACT.md", ["cc-1"]))

        # A run that refuses it (materialized before #100) is relaunched.
        data["contract_contradictions"][0]["resume"] = "refused"
        self.assertEqual(ledger.check(data), [])
        self.assertEqual(ledger.next_action(data)["action"], "launch")
        # One already resumed is not resumed again; a new one of the attempt is.
        data["contract_contradictions"][0]["resume"] = "resumed"
        data["contract_contradictions"].append(_contradiction("cc-2", 2, "swept-volume-over-ceiling:wing", "amend-b"))
        self.assertEqual(ledger.next_action(data)["contradictions"], ["cc-2"])

    def test_a_visible_root_fix_is_relaunched_not_resumed(self):
        data = _ledger()
        data["loop"].update(state="fixing", wish_id="wish-2")
        data["contract_contradictions"][0].update(visible=True, approved="owner 2026-10-04")

        self.assertEqual(ledger.next_action(data)["action"], "launch")

    def test_a_resume_mark_is_checked(self):
        data = _ledger()
        data["contract_contradictions"][0]["resume"] = "maybe"
        self.assertIn("contract_contradictions[0].resume must be null, `resumed` or `refused`", ledger.check(data))
        data["contract_contradictions"][0].update(resume="resumed", visible=True, approved="owner 2026-10-04")
        self.assertIn("contract_contradictions[0] resumed its run with an owner amendment, so it is invisible "
                      "and applied", ledger.check(data))

    def test_stop_conditions_win_over_the_state(self):
        data = _ledger()
        data["loop"].update(state="watching", wish_id="wish-3")
        data["cost_units"].update(by_attempt={"1": 101}, total=101)

        self.assertEqual(ledger.next_action(data)["action"], "ask-owner")

    def test_a_stop_is_diagnosed_before_the_loop_asks(self):
        data = _ledger()
        data["loop"].update(state="diagnosing", wish_id="wish-3", attempt=3)
        data["cost_units"].update(by_attempt={"1": 101}, total=101)

        action = ledger.next_action(data)
        self.assertEqual(action["action"], "diagnose")
        self.assertEqual(action["then_ask_owner"], ["cumulative cost 101 cost units passed the cap of 100"])

    def test_an_invalid_ledger_is_repaired_first(self):
        data = _ledger()
        data["cost_units"]["total"] = 1

        self.assertEqual(ledger.next_action(data)["action"], "repair-ledger")

    def test_the_command_line_prints_the_action(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            path.write_text(json.dumps(_ledger()))
            with _captured() as out:
                code = ledger.main(["next", str(path)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue())["action"], "launch")


class ClassifyTest(unittest.TestCase):
    def test_a_budget_stop_with_a_blocked_worker_is_a_contract_contradiction(self):
        # Broken God attempt 15: stop_category budget, the spine-housing worker
        # reported two rows that cannot both hold, and its overhang repeated.
        result = ledger.classify({
            "status": "active",
            "stop_category": "budget",
            "worker_blocked": ["spine-housing 02:16: print stance vs wing-housing slots"],
            "forced_repeats": ["spine-housing overhang (±16,-18,10) r3-r4"],
            "progress": {"locked": 7, "repeated_print_defects": 3},
            "previous_progress": {"locked": 5, "repeated_print_defects": 1},
        })

        self.assertEqual(result["class"], "contract-contradiction")
        self.assertEqual(len(result["why"]), 2)

    def test_an_open_blocked_report_is_a_contract_contradiction(self):
        result = ledger.classify({"stop_category": "budget", "blocked_reports_open": 1})

        self.assertEqual(result["class"], "contract-contradiction")

    def test_a_fresh_report_at_a_progressing_budget_stop_gets_the_resume(self):
        # Broken God attempt 16: the arm-right report opened 3 minutes before
        # the budget ran out; the root answered it within the resume (#92).
        evidence = {
            "stop_category": "budget",
            "blocked_reports_open": 1,
            "progress": {"locked": 7, "repeated_print_defects": 1},
            "previous_progress": {"locked": 7, "repeated_print_defects": 3},
        }

        self.assertEqual(ledger.classify(evidence)["class"], "budget-progressing")
        evidence["budget_raised"] = True
        self.assertEqual(ledger.classify(evidence)["class"], "contract-contradiction")
        evidence["budget_raised"] = False
        evidence["worker_blocked"] = ["arm-right: R24 vs the lug row"]
        self.assertEqual(ledger.classify(evidence)["class"], "contract-contradiction")

    def test_a_camera_need_keeps_its_path(self):
        result = ledger.classify({"status": "waiting", "needs": [{"kind": "camera", "text": "ref-02"}],
                                  "blocked_reports_open": 1})

        self.assertEqual(result["class"], "camera-need")

    def test_a_progressing_budget_stop(self):
        result = ledger.classify({
            "stop_category": "budget",
            "progress": {"locked": 5, "repeated_print_defects": 3},
            "previous_progress": {"locked": 4, "repeated_print_defects": 3},
        })

        self.assertEqual(result["class"], "budget-progressing")

    def test_a_second_budget_stop_is_diagnosed_like_any_other(self):
        result = ledger.classify({
            "stop_category": "budget",
            "budget_raised": True,
            "progress": {"locked": 6, "repeated_print_defects": 0},
            "previous_progress": {"locked": 4, "repeated_print_defects": 3},
        })

        self.assertEqual(result["class"], "other")

    def test_a_budget_stop_after_an_owner_raise_is_other(self):
        evidence = {
            "stop_category": "budget",
            "budget_raised": "owner",
            "progress": {"locked": 10, "repeated_print_defects": 0},
            "previous_progress": {"locked": 4, "repeated_print_defects": 3},
        }

        self.assertEqual(ledger.classify(evidence)["class"], "other")
        evidence["blocked_reports_open"] = 1
        self.assertEqual(ledger.classify(evidence)["class"], "contract-contradiction")

    def test_a_budget_stop_without_progress_is_other(self):
        result = ledger.classify({
            "stop_category": "budget",
            "progress": {"locked": 4, "repeated_print_defects": 3},
            "previous_progress": {"locked": 4, "repeated_print_defects": 3},
        })

        self.assertEqual(result["class"], "other")

    def test_reference_and_harness_classes(self):
        self.assertEqual(
            ledger.classify({"stop_category": "gate-refusal", "reference_mismatches": ["ref-05"],
                             "harness_defects": ["x"]})["class"],
            "reference-mismatch",
        )
        self.assertEqual(
            ledger.classify({"stop_category": "budget", "harness_defects": ["tokens counted twice"]})["class"],
            "harness-defect",
        )

    def test_a_completed_run(self):
        self.assertEqual(ledger.classify({"status": "complete"})["class"], "complete")


class RunPathsTest(unittest.TestCase):
    def test_transcripts_follow_claude_codes_project_layout(self):
        path = runpaths.claude_project_dir(
            Path("/home/me/.local/share/autonomous-workshop/runs/wish-1/workspace"),
            {"CLAUDE_CONFIG_DIR": "/cfg"},
        )

        self.assertEqual(
            path, Path("/cfg/projects/-home-me--local-share-autonomous-workshop-runs-wish-1-workspace"))

    def test_the_workshop_home_comes_from_workshop(self):
        self.assertEqual(
            runpaths.run_workspace("wish-1", {"WORKSHOP_HOME": "/srv/ws"}),
            Path("/srv/ws/runs/wish-1/workspace"),
        )

    def test_no_script_hard_codes_a_home_or_platform_path(self):
        for path in SCRIPTS.iterdir():
            if path.suffix not in (".py", ".sh"):
                continue
            text = path.read_text()
            for needle in ("/home/", "loginuser", ".local/share", "Library/Application", "xargs -r", "pgrep"):
                self.assertNotIn(needle, text, f"{path.name} contains {needle}")


class TallyTest(unittest.TestCase):
    def test_repeats_and_locks(self):
        with tempfile.TemporaryDirectory() as tmp:
            make = Path(tmp) / "artifacts" / "make"
            rounds = make / "r0001" / "product" / "cad" / "measure" / "component-rounds"
            failing = {"housing": {"verdict": "FAIL", "overhang": {
                "verdict": "FAIL", "defects": ["plane@(16,-18,10)"], "failures": []}}}
            _summary(rounds / "housing" / "r0001", {"print": failing})
            _summary(rounds / "housing" / "r0002", {"print": failing})
            _summary(rounds / "wing" / "r0001", {"print": {"wing": {"verdict": "PASS"}}, "locked": True})

            lines, totals = tally.tally(tally.collect(make))

        self.assertEqual(totals["repeated_print_defects"], 1)
        self.assertEqual(totals["failing_rounds"], 2)
        self.assertEqual(totals["locked"], 1)
        self.assertEqual(totals["locked_components"], ["wing"])
        self.assertIn("PRINT", lines[1])


class TokensTest(unittest.TestCase):
    def test_cost_units_by_agent_count_each_message_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            usage = {"input_tokens": 1_000_000, "cache_creation_input_tokens": 0,
                     "cache_read_input_tokens": 10_000_000, "output_tokens": 0}
            line = json.dumps({"message": {"id": "m1", "usage": usage}})
            (root / "s.jsonl").write_text(line + "\n" + line + "\n")
            worker = root / "s" / "subagents"
            worker.mkdir(parents=True)
            (worker / "a.jsonl").write_text(json.dumps(
                {"message": {"id": "m2", "usage": {"output_tokens": 200_000}}}) + "\n")
            (worker / "a.meta.json").write_text(json.dumps({"agentType": "component-worker"}))

            result = tokens.report(tokens.collect(root))

        self.assertEqual(result["agents"]["root"]["cost_units"], 2.0)
        self.assertEqual(result["agents"]["component-worker"]["cost_units"], 1.0)
        self.assertEqual(result["cost_units"], 3.0)


class SnapshotTest(unittest.TestCase):
    def test_a_budget_stop_counts_as_stopped_even_while_active(self):
        self.assertTrue(snapshot.stopped({"status": "active", "stop_category": "budget"}))
        self.assertFalse(snapshot.stopped({"status": "active", "stop_category": None}))
        self.assertTrue(snapshot.stopped({"status": "waiting"}))

    def test_a_raised_budget_is_not_a_stop(self):
        # The host keeps token-budget-stop.json after a resume raises the cap.
        raised = {"status": "active", "stop_category": "budget",
                  "budget": {"used_tokens": 100_000_122, "limit_tokens": 200_000_000}}
        self.assertFalse(snapshot.stopped(raised))
        raised["budget"]["used_tokens"] = 200_000_001
        self.assertTrue(snapshot.stopped(raised))

    def test_an_active_run_is_not_stopped_by_its_default_category(self):
        # `workshop status` gives every run that is not complete a
        # stop_category; a live run reads `unclassified` (#91).
        self.assertFalse(snapshot.stopped({"status": "active", "stop_category": "unclassified"}))
        self.assertFalse(
            snapshot.stopped({"status": "active", "stop_category": "inspection-in-progress"})
        )
        self.assertTrue(snapshot.stopped({"status": "failed", "stop_category": "gate-refusal"}))
        self.assertTrue(snapshot.stopped({"status": "complete"}))

    def test_open_blocked_reports_are_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            line = snapshot.snapshot(
                {"status": "active", "blocked_reports": [{"status": "open"}, {"status": "cleared"},
                                                         {"status": "waiting"}],
                 "budget": {"used_tokens": 12_500_000, "limit_tokens": 100_000_000}},
                Path(tmp), Path(tmp) / "none",
            )

        self.assertEqual(line["blocked_open"], 2)
        self.assertEqual(line["tokens_m"], 12)
        self.assertEqual(line["limit_m"], 100)


def _summary(directory, data):
    directory.mkdir(parents=True)
    (directory / "summary.json").write_text(json.dumps(data))


class _captured:
    def __enter__(self):
        import io

        self.buffer = io.StringIO()
        self.saved = sys.stdout
        sys.stdout = self.buffer
        return self.buffer

    def __exit__(self, *exc):
        sys.stdout = self.saved
        return False


if __name__ == "__main__":
    unittest.main()


STANCE = "The spine housing prints on its front face. No part needs support."
BACK = "The spine housing prints on its back face. No part needs support."
CONTRACT_MD = """# Toy

Prose that stays as it is.

```design-contract
{
  "schema_version": 4,
  "requirements": [
    {"id": "R01", "scope": "geometry:spine-housing", "text": "The spine housing prints on its front face. No part needs support."},
    {"id": "R02", "scope": "assembly", "text": "Wings swing \\u00b130\\u00b0."}
  ],
  "interfaces": [{"id": "hinge", "kind": "static", "components": ["a", "b"], "text": "A peg."}]
}
```

Tail prose.
"""


def _status(*amendments):
    return {"product_id": "wish-3", "contract_amendments": [
        {"file": "ref-02-x.png", "from": [0, 0], "to": [90, 0]},
        *amendments,
    ]}


def _amendment(number, changes, status="applied"):
    return {"kind": "contract-amendment", "attempt": "r0001", "amendment": number, "status": status,
            "rows": [STANCE, "The seats sit at Y 17.5."], "changes": changes,
            "review": {"reviewer": "a1b2c3d4e5f6a7b8c"}, "contract_sha256": "a" * 64,
            "amended_sha256": "b" * 64}


class FoldInRunAmendmentsTest(unittest.TestCase):
    """ADR 0085: the loop merges a run's applied amendments into the toy's
    contract for the next attempt and records them in the ledger."""

    def test_applied_amendments_are_folded_and_nothing_else_changes(self):
        result = ledger.fold(CONTRACT_MD, _status(
            _amendment(1, [{"row": "R01", "from": STANCE, "to": BACK}]),
            _amendment(2, [{"row": "R02", "from": "Wings swing ±30°.", "to": "Wings swing ±25°."},
                           {"row": "interface:hinge", "from": "A peg.", "to": "A 3 mm peg."}]),
            _amendment(3, [{"row": "R01", "from": BACK, "to": "x"}], status="refused"),
        ), attempt=3)
        self.assertEqual((result["folded"], result["already"], result["refused"]),
                         (["wish-3#1", "wish-3#2"], [], []))
        text = result["contract"]
        self.assertEqual(CONTRACT_MD.replace(STANCE, BACK)
                         .replace("\\u00b130\\u00b0", "\\u00b125\\u00b0").replace('"A peg."', '"A 3 mm peg."'), text)
        self.assertEqual([(e["attempt"], e["amendment"], e["folded"]) for e in result["entries"]],
                         [(3, 1, True), (3, 2, True)])
        # Folding again changes nothing.
        again = ledger.fold(text, _status(_amendment(1, [{"row": "R01", "from": STANCE, "to": BACK}])))
        self.assertEqual((again["contract"], again["already"]), (text, ["wish-3#1"]))

    def test_a_row_that_changed_since_is_refused_for_a_hand_fold(self):
        result = ledger.fold(CONTRACT_MD.replace(STANCE, "Prints upright."), _status(
            _amendment(1, [{"row": "R01", "from": STANCE, "to": BACK}])))
        self.assertEqual(len(result["refused"]), 1)
        self.assertFalse(result["entries"][0]["folded"])

    def test_the_command_line_writes_the_folded_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "CONTRACT.md").write_text(CONTRACT_MD)
            (root / "status.json").write_text(json.dumps(_status(
                _amendment(1, [{"row": "R01", "from": STANCE, "to": BACK}]))))
            code = ledger.main(["fold", str(root / "CONTRACT.md"), str(root / "status.json"),
                                "--attempt", "3", "--out", str(root / "amend-c.md")])
            self.assertEqual(code, 0)
            self.assertIn(BACK, (root / "amend-c.md").read_text())
            self.assertEqual((root / "CONTRACT.md").read_text(), CONTRACT_MD)

    def test_the_ledger_records_each_fold_and_lists_an_unfolded_one(self):
        data = _ledger()
        entry = {"attempt": 2, "wish_id": "wish-2", "amendment": 1, "rows": [STANCE, "Seats."],
                 "changes": [{"row": "R01", "from": STANCE, "to": BACK}], "reviewer": "r",
                 "contract_sha256": "a" * 64, "amended_sha256": "b" * 64, "folded": True,
                 "contract_version": "amend-b"}
        data["in_run_amendments"] = [entry]
        self.assertEqual(ledger.check(data), [])
        data["in_run_amendments"] = [{**entry, "contract_version": None}]
        self.assertIn("in_run_amendments[0] is folded without a contract_versions key (`contract_version`)",
                      ledger.check(data))
        data["in_run_amendments"] = [{**entry, "folded": False, "contract_version": None}]
        data["loop"].update(state="fixing", wish_id="wish-2")
        self.assertEqual(ledger.next_action(data)["pending"],
                         ["in-run amendment wish-2#1: fold it into CONTRACT.md"])
        data["in_run_amendments"] = [entry, dict(entry)]
        self.assertIn("in_run_amendments[1] repeats amendment 1 of wish-2", ledger.check(data))


class RefreshGuidanceTest(unittest.TestCase):
    def test_a_running_run_is_refreshed_from_its_source_commit_plus_the_fix(self):
        # Issue #107: a refresh from main brought unrelated gates into a run.
        text = " ".join((REPOSITORY / ".claude/skills/build-a-toy/SKILL.md").read_text(encoding="utf-8").split())
        section = text[text.index("### Delivering a fix to a running run"):]
        for required in (
            "Never refresh a running run from `main`",
            "the run's own source commit plus only the fix",
            "`loop.source_commit`",
            "git cherry-pick",
            "--refresh-tools --dry-run --refresh-tree <tree>",
            "`WARNING`",
        ):
            with self.subTest(required=required):
                self.assertIn(required, section)
