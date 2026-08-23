"""Tests for harness/budgets.py — spend, exhaustion, and the anti-laundering
freeze/settle pair."""

import json
import os
import shutil
import tempfile
import unittest

from harness import budgets, queue


class BudgetsHome(unittest.TestCase):
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

    def write_doc(self, slug, doc):
        d = os.path.join(self.home, "games", slug)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, budgets.GAME_DOC), "w") as fh:
            json.dump(doc, fh)

    DOC = {
        "players": {"min": 2, "max": 4},
        "action_types": ["place", "rotate"],
        "desc": "original wording",
        "rules": {"win": {"condition": "connect three towers"},
                  "setup": "original setup text"},
        "components": [{"name": "tower", "qty": 9, "per_player": 3}],
    }


class TestConstants(BudgetsHome):
    def test_contract_pinned_values(self):
        self.assertEqual(budgets.CLARIFY_BUDGET, 3)
        self.assertEqual(budgets.REWORK_BUDGET, 3)
        self.assertEqual(budgets.REPAIR_BUDGET, 2)


class TestSpend(BudgetsHome):
    def fresh_game(self):
        return {"budgets": {"clarify_used": 0, "rework_used": 0,
                            "repair_used": 0}}

    def test_spend_up_to_budget_then_false(self):
        game = self.fresh_game()
        for i in range(budgets.REWORK_BUDGET):
            self.assertTrue(budgets.spend(game, "rework"), "round %d" % i)
        self.assertFalse(budgets.spend(game, "rework"))
        # Exhausted spend must not increment past the cap.
        self.assertEqual(game["budgets"]["rework_used"],
                         budgets.REWORK_BUDGET)

    def test_repair_cap_is_two(self):
        game = self.fresh_game()
        self.assertTrue(budgets.spend(game, "repair"))
        self.assertTrue(budgets.spend(game, "repair"))
        self.assertFalse(budgets.spend(game, "repair"))

    def test_budgets_are_independent(self):
        game = self.fresh_game()
        game["budgets"]["rework_used"] = budgets.REWORK_BUDGET
        self.assertTrue(budgets.spend(game, "clarify"))
        self.assertTrue(budgets.spend(game, "repair"))

    def test_unknown_kind_refused(self):
        with self.assertRaises(ValueError):
            budgets.spend(self.fresh_game(), "vibes")

    def test_missing_budgets_dict_created(self):
        game = {}
        self.assertTrue(budgets.spend(game, "clarify"))
        self.assertEqual(game["budgets"]["clarify_used"], 1)


class TestFreezeSettle(BudgetsHome):
    def start_clarify(self, slug="g"):
        """A clarify round as the invent loop would run it: charge the round,
        freeze the surface, let the fixer edit the doc, then settle."""
        queue.add_game(slug, "G")
        self.write_doc(slug, self.DOC)
        with queue.transaction() as q:
            self.assertTrue(budgets.spend(q["games"][slug], "clarify"))
        budgets.freeze_surface(slug)

    def test_wording_only_clarify_stands(self):
        self.start_clarify()
        doc = json.loads(json.dumps(self.DOC))
        doc["desc"] = "clearer wording"
        # rules text is mechanic surface since the mech_surface widening
        # (a "setup" rewrite can hide a rule change); prose keys stay free.
        doc["rules"]["description"] = "clearer rules description"
        self.write_doc("g", doc)
        result = budgets.settle_clarify("g")
        self.assertEqual(result, {"changed": False, "converted": False,
                                  "budget_ok": True})
        b = queue.load()["games"]["g"]["budgets"]
        self.assertEqual(b["clarify_used"], 1)  # the charge stands
        self.assertEqual(b["rework_used"], 0)

    def test_mechanic_change_converted_to_rework(self):
        self.start_clarify()
        doc = json.loads(json.dumps(self.DOC))
        doc["rules"]["win"] = {"condition": "most towers at sundown"}
        self.write_doc("g", doc)
        result = budgets.settle_clarify("g")
        self.assertEqual(result, {"changed": True, "converted": True,
                                  "budget_ok": True})
        game = queue.load()["games"]["g"]
        # Refund clarify, charge rework — the round was mis-labelled.
        self.assertEqual(game["budgets"]["clarify_used"], 0)
        self.assertEqual(game["budgets"]["rework_used"], 1)
        self.assertIn("clarify converted to rework",
                      game["log"][-1]["note"])

    def test_conversion_with_rework_exhausted_flags_caller(self):
        self.start_clarify()
        with queue.transaction() as q:
            q["games"]["g"]["budgets"]["rework_used"] = budgets.REWORK_BUDGET
        doc = json.loads(json.dumps(self.DOC))
        doc["components"][0]["qty"] = 12
        self.write_doc("g", doc)
        result = budgets.settle_clarify("g")
        self.assertTrue(result["changed"])
        self.assertFalse(result["budget_ok"])
        # Caller routes to park_or_kill, which kills on rework exhaustion.
        game = queue.park_or_kill("g", "clarify laundered a mechanic change")
        self.assertEqual(game["state"], "killed")

    def test_settle_without_freeze_is_noop(self):
        queue.add_game("g", "G")
        self.write_doc("g", self.DOC)
        result = budgets.settle_clarify("g")
        self.assertEqual(result, {"changed": False, "converted": False,
                                  "budget_ok": True})

    def test_frozen_marker_cleared_after_settle(self):
        self.start_clarify()
        budgets.settle_clarify("g")
        self.assertNotIn("mech_frozen", queue.load()["games"]["g"])

    def test_missing_doc_raises_with_guidance(self):
        queue.add_game("nodoc", "N")
        with self.assertRaises(FileNotFoundError) as cm:
            budgets.freeze_surface("nodoc")
        self.assertIn("game.json", str(cm.exception))

    def test_missing_game_raises_keyerror(self):
        self.write_doc("ghost", self.DOC)
        with self.assertRaises(KeyError):
            budgets.freeze_surface("ghost")


if __name__ == "__main__":
    unittest.main()
