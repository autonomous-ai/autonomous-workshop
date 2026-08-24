"""Tests for harness/queue.py — the state machine, leases, and the lock.

Each test builds its own temp BOB_HOME (tests/util.py:make_home is
integrator-owned and does not exist yet, so tempfile inline per CONTRACTS §5).
"""

import json
import os
import shutil
import tempfile
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone

from harness import queue


class QueueHome(unittest.TestCase):
    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-test-")
        self._old = os.environ.get("BOB_HOME")
        os.environ["BOB_HOME"] = self.home

    def tearDown(self):
        if self._old is None:
            os.environ.pop("BOB_HOME", None)
        else:
            os.environ["BOB_HOME"] = self._old
        shutil.rmtree(self.home, ignore_errors=True)


class TestPriorityCompleteness(QueueHome):
    def test_priority_union_terminal_covers_all_states(self):
        # The scheduler-hole receipt: a state outside both sets stalls
        # every game that reaches it, silently.
        self.assertEqual(set(queue.PRIORITY) | set(queue.WAITING) |
                         set(queue.TERMINAL),
                         set(queue.ALL_STATES))

    def test_priority_and_terminal_disjoint(self):
        self.assertEqual(set(queue.PRIORITY) & set(queue.TERMINAL), set())

    def test_every_state_has_a_transition_row(self):
        self.assertEqual(set(queue.TRANSITIONS), set(queue.ALL_STATES))

    def test_no_awaiting_owner_or_approved(self):
        # Auto-publish rules this lane (Dee 2026-08-22): the human-flip
        # states must not exist.
        self.assertNotIn("awaiting_owner", queue.ALL_STATES)
        self.assertNotIn("approved", queue.ALL_STATES)

    def test_transition_targets_are_known_states(self):
        for frm, targets in queue.TRANSITIONS.items():
            for to in targets:
                self.assertIn(to, queue.ALL_STATES,
                              "%s -> %s targets unknown state" % (frm, to))


class TestTransitions(QueueHome):
    def test_legal_forward_walk(self):
        queue.add_game("walk", "Walk")
        path = ["researched", "ruled", "rules_gated", "simulated", "tabled",
                "briefed", "built", "build_gated", "reviewed", "published",
                "live"]
        for state in path:
            game = queue.advance("walk", state, "step")
            self.assertEqual(game["state"], state)
        # Full log: spark row + one per advance.
        q = queue.load()
        self.assertEqual(len(q["games"]["walk"]["log"]), 1 + len(path))

    def test_illegal_transition_refused(self):
        queue.add_game("g", "G")
        with self.assertRaises(ValueError) as cm:
            queue.advance("g", "published", "skipping the gates")
        self.assertIn("illegal transition", str(cm.exception))
        # State untouched by the refused move.
        self.assertEqual(queue.load()["games"]["g"]["state"], "sparked")

    def test_unknown_state_refused(self):
        queue.add_game("g", "G")
        with self.assertRaises(ValueError):
            queue.advance("g", "awaiting_owner", "stale schema caller")

    def test_terminal_states_have_no_exits(self):
        self.assertEqual(queue.TRANSITIONS["killed"], frozenset())
        self.assertEqual(queue.TRANSITIONS["live"], frozenset())

    def test_published_waits_for_verified_live(self):
        self.assertIn("published", queue.WAITING)
        self.assertNotIn("published", queue.PRIORITY)
        self.assertIn("live", queue.TRANSITIONS["published"])

    def test_advance_appends_log_and_releases_lease(self):
        queue.add_game("g", "G")
        step = queue.claim_next("invent")
        self.assertEqual(step.slug, "g")
        game = queue.advance("g", "researched", "did research")
        self.assertIsNone(game["lease"]["holder"])
        last = game["log"][-1]
        self.assertEqual((last["from"], last["to"]), ("sparked", "researched"))
        self.assertEqual(last["note"], "did research")

    def test_park_records_reason(self):
        queue.add_game("g", "G")
        game = queue.park("g", "budget exhausted")
        self.assertEqual(game["state"], "parked")
        self.assertIn("budget exhausted", game["log"][-1]["note"])

    def test_parked_can_reopen_to_working_state(self):
        queue.add_game("g", "G")
        queue.park("g", "pause")
        game = queue.advance("g", "sparked", "human reopened")
        self.assertEqual(game["state"], "sparked")

    def test_missing_game_raises_keyerror(self):
        with self.assertRaises(KeyError):
            queue.advance("ghost", "researched", "no such game")


class TestLeases(QueueHome):
    def test_claim_next_priority_order(self):
        # closest-to-publish first: the reviewed game beats the fresh spark.
        queue.add_game("fresh", "Fresh")
        queue.add_game("almost", "Almost")
        with queue.transaction() as q:
            q["games"]["almost"]["state"] = "reviewed"
        step = queue.claim_next("invent")
        self.assertEqual(step.slug, "almost")
        self.assertEqual(step.state, "reviewed")
        self.assertTrue(step.lease_id)

    def test_double_claim_refused(self):
        queue.add_game("only", "Only")
        first = queue.claim_next("invent-a")
        self.assertEqual(first.slug, "only")
        second = queue.claim_next("invent-b")
        self.assertIsNone(second)  # leased game is not claimable

    def test_expired_lease_reclaimable(self):
        queue.add_game("g", "G")
        queue.claim_next("crashed-driver")
        with queue.transaction() as q:
            q["games"]["g"]["lease"]["expires"] = (
                datetime.now(timezone.utc) - timedelta(minutes=1)
            ).isoformat()
        step = queue.claim_next("fresh-driver")
        self.assertEqual(step.slug, "g")
        held = queue.load()["games"]["g"]["lease"]
        self.assertEqual(held["holder"], "fresh-driver")

    def test_lease_stamps_holder_and_expiry(self):
        queue.add_game("g", "G")
        before = datetime.now(timezone.utc)
        queue.claim_next("invent")
        lease = queue.load()["games"]["g"]["lease"]
        self.assertEqual(lease["holder"], "invent")
        expires = datetime.fromisoformat(lease["expires"])
        minutes = (expires - before).total_seconds() / 60.0
        self.assertGreater(minutes, queue.LEASE_MINUTES - 1)
        self.assertLess(minutes, queue.LEASE_MINUTES + 1)

    def test_stale_lease_advance_is_fenced_noop(self):
        # The fencing token: a driver that wedged past LEASE_MINUTES and
        # lost the game to a fresh claim must not move it under the new
        # holder (the triple-driver pile-up receipt).
        queue.add_game("g", "G")
        stale = queue.claim_next("wedged-driver")
        with queue.transaction() as q:
            q["games"]["g"]["lease"]["expires"] = (
                datetime.now(timezone.utc) - timedelta(minutes=1)
            ).isoformat()
        fresh = queue.claim_next("fresh-driver")
        self.assertNotEqual(stale.lease_id, fresh.lease_id)
        result = queue.advance("g", "researched", "stale verdict",
                               lease_id=stale.lease_id)
        self.assertIs(result, False)
        game = queue.load()["games"]["g"]
        self.assertEqual(game["state"], "sparked")  # nothing moved
        self.assertEqual(game["lease"]["holder"], "fresh-driver")
        self.assertEqual(game["lease"]["id"], fresh.lease_id)
        self.assertIn("fenced", game["log"][-1]["note"])  # logged no-op

    def test_current_lease_advance_succeeds(self):
        queue.add_game("g", "G")
        step = queue.claim_next("invent")
        game = queue.advance("g", "researched", "did research",
                             lease_id=step.lease_id)
        self.assertTrue(game)
        self.assertEqual(game["state"], "researched")
        self.assertIsNone(game["lease"]["holder"])

    def test_stale_lease_release_is_fenced_noop(self):
        queue.add_game("g", "G")
        stale = queue.claim_next("wedged-driver")
        with queue.transaction() as q:
            q["games"]["g"]["lease"]["expires"] = (
                datetime.now(timezone.utc) - timedelta(minutes=1)
            ).isoformat()
        fresh = queue.claim_next("fresh-driver")
        self.assertIs(queue.release("g", lease_id=stale.lease_id), False)
        game = queue.load()["games"]["g"]
        self.assertEqual(game["lease"]["holder"], "fresh-driver")  # intact
        # The rightful holder releases fine.
        game = queue.release("g", lease_id=fresh.lease_id)
        self.assertIsNone(game["lease"]["holder"])

    def test_release_clears_lease_without_progress(self):
        queue.add_game("g", "G")
        queue.claim_next("invent")
        game = queue.release("g")
        self.assertIsNone(game["lease"]["holder"])
        self.assertEqual(game["state"], "sparked")  # no faked progress

    def test_terminal_states_never_claimed(self):
        queue.add_game("dead", "Dead")
        queue.advance("dead", "killed", "test kill")
        self.assertIsNone(queue.claim_next("invent"))

    def test_empty_queue_returns_none(self):
        self.assertIsNone(queue.claim_next("invent"))

    def test_oldest_first_within_a_state(self):
        with queue.transaction() as q:
            for i, slug in enumerate(["newer", "older"]):
                q["games"][slug] = {
                    "slug": slug, "title": slug, "state": "sparked",
                    "direction": {}, "budgets": {"clarify_used": 0,
                                                 "rework_used": 0,
                                                 "repair_used": 0},
                    "reward": {"latest": 0.0, "history": []},
                    "lease": {"holder": None, "expires": None},
                    "created": "2026-08-2%d" % (2 - i),
                    "log": [],
                }
        self.assertEqual(queue.claim_next("invent").slug, "older")


class TestParkOrKill(QueueHome):
    def test_parks_when_rework_remains(self):
        queue.add_game("g", "G")
        game = queue.park_or_kill("g", "gate failed")
        self.assertEqual(game["state"], "parked")

    def test_kills_when_rework_exhausted(self):
        from harness import budgets
        queue.add_game("g", "G")
        with queue.transaction() as q:
            q["games"]["g"]["budgets"]["rework_used"] = budgets.REWORK_BUDGET
        game = queue.park_or_kill("g", "still failing after three passes")
        self.assertEqual(game["state"], "killed")
        self.assertIn("rework budget exhausted", game["log"][-1]["note"])


class TestAtomicSave(QueueHome):
    def test_save_survives_concurrent_reads(self):
        # A dashboard reading QUEUE.json without the lock must never see a
        # half-written file: save is tmp + os.replace.
        with queue.transaction() as q:
            for i in range(200):
                q["games"]["game-%03d" % i] = {
                    "slug": "game-%03d" % i, "title": "G%d" % i,
                    "state": "sparked", "direction": {},
                    "budgets": {"clarify_used": 0, "rework_used": 0,
                                "repair_used": 0},
                    "reward": {"latest": 0.0, "history": []},
                    "lease": {"holder": None, "expires": None},
                    "created": "2026-08-22", "log": [],
                }
        path = os.path.join(self.home, "state", "QUEUE.json")
        errors = []
        stop = threading.Event()

        def reader():
            while not stop.is_set():
                try:
                    with open(path, "r") as fh:
                        data = json.load(fh)
                    if len(data["games"]) != 200:
                        errors.append("partial content: %d games"
                                      % len(data["games"]))
                except Exception as e:  # a torn file would land here
                    errors.append(repr(e))

        t = threading.Thread(target=reader)
        t.start()
        try:
            for _ in range(50):
                q = queue.load()
                queue.save(q)
        finally:
            stop.set()
            t.join()
        self.assertEqual(errors, [])

    def test_load_missing_file_is_empty_queue(self):
        self.assertEqual(queue.load(), {"version": 2, "games": {}})

    def test_no_tmp_droppings_left(self):
        queue.add_game("g", "G")
        state_dir = os.path.join(self.home, "state")
        leftovers = [f for f in os.listdir(state_dir) if ".tmp." in f]
        self.assertEqual(leftovers, [])


class TestLock(QueueHome):
    def test_transaction_excludes_second_transaction(self):
        # flock is per open-file-description, so two transactions in one
        # process (two fds) exclude each other like two processes would.
        order = []
        inside = threading.Event()

        def holder():
            with queue.transaction() as q:
                inside.set()
                time.sleep(0.3)
                q["games"]["from-holder"] = {
                    "slug": "from-holder", "title": "H", "state": "sparked",
                    "direction": {}, "budgets": {"clarify_used": 0,
                                                 "rework_used": 0,
                                                 "repair_used": 0},
                    "reward": {"latest": 0.0, "history": []},
                    "lease": {"holder": None, "expires": None},
                    "created": "2026-08-22", "log": [],
                }
                order.append("holder-done")

        t = threading.Thread(target=holder)
        t.start()
        self.assertTrue(inside.wait(2.0))
        with queue.transaction() as q:
            order.append("second-in")
            # The holder's write must be visible: we waited for its save.
            self.assertIn("from-holder", q["games"])
        t.join()
        self.assertEqual(order, ["holder-done", "second-in"])

    def test_exception_inside_transaction_saves_nothing(self):
        queue.add_game("g", "G")
        try:
            with queue.transaction() as q:
                q["games"]["g"]["state"] = "published"
                raise RuntimeError("boom")
        except RuntimeError:
            pass
        self.assertEqual(queue.load()["games"]["g"]["state"], "sparked")


class TestMechSurface(QueueHome):
    DOC = {
        "title": "Ridgeline",
        "concept": "climbers race up a printed mountain",
        "desc": "long flavour text",
        "players": {"min": 2, "max": 4},
        "action_types": ["climb", "anchor", "cut"],
        "rules": {
            "win": {"condition": "first to summit with 2 anchors"},
            "setup": "wording here",
        },
        "components": [
            {"name": "peg", "qty": 24, "per_player": 6},
            {"name": "mountain", "qty": 1, "per_player": None},
        ],
    }

    def test_stable_across_wording_changes(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        b["desc"] = "totally rewritten flavour"
        b["concept"] = "new pitch"
        # Prose keys inside rules stay free (setup is NOT one of them any
        # more — rules text is mechanics unless explicitly prose).
        b["rules"]["description"] = "clarified rules description"
        b["title"] = "Ridgeline: Second Edition"
        self.assertEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_action_order_does_not_matter(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        b["action_types"] = list(reversed(b["action_types"]))
        self.assertEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_win_block_change_detected(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        b["rules"]["win"] = {"condition": "most anchors when pegs run out"}
        self.assertNotEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_component_qty_change_detected(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        b["components"][0]["qty"] = 30
        self.assertNotEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_players_change_detected(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        b["players"] = {"min": 2, "max": 5}
        self.assertNotEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_structured_actions_fallback(self):
        doc = json.loads(json.dumps(self.DOC))
        del doc["action_types"]
        doc["actions"] = [{"type": "climb"}, {"type": "anchor"},
                          {"type": "cut"}]
        self.assertEqual(queue.mech_surface(doc),
                         queue.mech_surface(self.DOC))

    def test_rules_mechanic_change_detected(self):
        # The laundering hole: only rules['win'] was hashed, so a
        # "clarify" rewriting movement dodged the paid-rework conversion.
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        a["rules"]["movement"] = "move 1 space"
        b["rules"]["movement"] = "move up to 3 spaces"
        self.assertNotEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_rules_prose_keys_stay_free(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        for key in ("description", "flavor", "notes", "summary"):
            b["rules"][key] = "reworded %s" % key
        self.assertEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_structured_action_effect_change_detected(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        for doc in (a, b):
            del doc["action_types"]
        a["actions"] = [{"type": "climb", "effect": "ascend 1"}]
        b["actions"] = [{"type": "climb", "effect": "ascend 2"}]
        self.assertNotEqual(queue.mech_surface(a), queue.mech_surface(b))

    def test_structured_action_prose_stays_free(self):
        a = json.loads(json.dumps(self.DOC))
        b = json.loads(json.dumps(self.DOC))
        for doc in (a, b):
            del doc["action_types"]
        a["actions"] = [{"type": "climb", "effect": "ascend 1",
                         "description": "old wording"}]
        b["actions"] = [{"type": "climb", "effect": "ascend 1",
                         "description": "new wording"}]
        self.assertEqual(queue.mech_surface(a), queue.mech_surface(b))


if __name__ == "__main__":
    unittest.main()
