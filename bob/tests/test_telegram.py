"""Tests for harness/telegram.py — no-op mode, send payloads, and the
poll/parse/state-check/strip-keyboard cycle. Zero network: _http is always
monkeypatched."""

import json
import os
import shutil
import tempfile
import unittest

from harness import queue, telegram

SLUG = "tower-duel"


def _fail_http(*args, **kwargs):
    raise AssertionError("_http called — this code path must be offline")


class TelegramHome(unittest.TestCase):
    ENV_KEYS = ("BOB_HOME", "BOB_TELEGRAM_TOKEN", "BOB_TELEGRAM_CHAT")

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="bob-test-tg-")
        self._env = {}
        for key in self.ENV_KEYS:
            self._env[key] = os.environ.pop(key, None)
        os.environ["BOB_HOME"] = self.home
        self._orig_http = telegram._http
        telegram._http = _fail_http

    def tearDown(self):
        telegram._http = self._orig_http
        for key in self.ENV_KEYS:
            if self._env[key] is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = self._env[key]
        shutil.rmtree(self.home, ignore_errors=True)

    def with_creds(self):
        os.environ["BOB_TELEGRAM_TOKEN"] = "tok123"
        os.environ["BOB_TELEGRAM_CHAT"] = "777"

    def capture_http(self, responses_by_method):
        calls = []

        def fake(method, payload, token):
            calls.append({"method": method, "payload": payload,
                          "token": token})
            return responses_by_method.get(method, {"ok": True,
                                                    "result": {}})
        telegram._http = fake
        return calls

    def add_published_game(self):
        queue.add_game(SLUG, "Tower Duel")
        for state in ("researched", "ruled", "rules_gated", "simulated",
                      "tabled", "briefed", "built", "build_gated",
                      "reviewed", "published"):
            queue.advance(SLUG, state, "setup")
        pub_dir = os.path.join(self.home, "games", SLUG)
        os.makedirs(pub_dir, exist_ok=True)
        with open(os.path.join(pub_dir, "published.json"), "w") as fh:
            json.dump({"slug": SLUG}, fh)


class TestNoOpMode(TelegramHome):
    def test_send_without_creds_is_noop(self):
        # _http is the failing stub: a single call fails the test.
        self.assertIsNone(telegram.send("hello"))

    def test_poll_without_creds_returns_empty(self):
        self.assertEqual(telegram.poll_decisions(), [])


class TestSend(TelegramHome):
    def test_send_payload_shape(self):
        self.with_creds()
        calls = self.capture_http({"sendMessage": {
            "ok": True, "result": {"message_id": 5}}})
        result = telegram.send("published!", buttons=["unpublish %s" % SLUG])
        self.assertEqual(result["message_id"], 5)
        call = calls[0]
        self.assertEqual(call["method"], "sendMessage")
        self.assertEqual(call["token"], "tok123")
        self.assertEqual(call["payload"]["chat_id"], "777")
        self.assertEqual(call["payload"]["text"], "published!")
        kb = call["payload"]["reply_markup"]["inline_keyboard"]
        self.assertEqual(kb[0][0]["callback_data"], "unpublish %s" % SLUG)

    def test_send_failure_returns_none(self):
        self.with_creds()
        self.capture_http({"sendMessage": {"ok": False,
                                           "description": "blocked"}})
        self.assertIsNone(telegram.send("x"))


class TestPollDecisions(TelegramHome):
    def updates(self, rows):
        return {"ok": True, "result": rows}

    def test_full_cycle_verbs_states_offset_and_keyboard_strip(self):
        self.with_creds()
        self.add_published_game()
        rows = [
            {"update_id": 10, "message": {
                "chat": {"id": 777},
                "text": "park %s too spicy" % SLUG}},
            {"update_id": 11, "message": {
                "chat": {"id": 999},  # stranger chat: must be ignored
                "text": "park %s hostile" % SLUG}},
            {"update_id": 12, "message": {
                "chat": {"id": 777},
                "text": "delete %s" % SLUG}},  # verb outside closed set
            {"update_id": 13, "callback_query": {
                "id": "cb1",
                "data": "unpublish %s" % SLUG,
                "message": {"message_id": 42, "chat": {"id": 777}}}},
        ]
        calls = self.capture_http({"getUpdates": self.updates(rows)})
        decisions = telegram.poll_decisions()

        verbs = [(d["verb"], d["valid"]) for d in decisions]
        self.assertIn(("park", True), verbs)
        self.assertIn(("delete", False), verbs)
        self.assertIn(("unpublish", True), verbs)
        self.assertEqual(len(decisions), 3)  # stranger row dropped entirely
        bad = [d for d in decisions if d["verb"] == "delete"][0]
        self.assertIn("closed set", bad["reason"])

        # offset persisted = max update_id + 1
        with open(os.path.join(self.home, "state", ".tg-offset")) as fh:
            self.assertEqual(fh.read().strip(), "14")

        # the tapped message lost its keyboard (stale-button receipt)
        methods = [c["method"] for c in calls]
        self.assertIn("editMessageReplyMarkup", methods)
        strip = [c for c in calls
                 if c["method"] == "editMessageReplyMarkup"][0]
        self.assertEqual(strip["payload"]["message_id"], 42)
        self.assertEqual(strip["payload"]["reply_markup"],
                         {"inline_keyboard": []})
        self.assertIn("answerCallbackQuery", methods)

    def test_unpublish_state_checked_against_queue(self):
        self.with_creds()
        queue.add_game(SLUG, "Tower Duel")  # state=sparked, never published
        self.capture_http({"getUpdates": self.updates([
            {"update_id": 1, "message": {
                "chat": {"id": 777}, "text": "unpublish %s" % SLUG}}])})
        (decision,) = telegram.poll_decisions()
        self.assertFalse(decision["valid"])
        self.assertIn("not published/live", decision["reason"])

    def test_unpublish_needs_published_json_ledger(self):
        self.with_creds()
        self.add_published_game()
        os.remove(os.path.join(self.home, "games", SLUG, "published.json"))
        self.capture_http({"getUpdates": self.updates([
            {"update_id": 1, "message": {
                "chat": {"id": 777}, "text": "unpublish %s" % SLUG}}])})
        (decision,) = telegram.poll_decisions()
        self.assertFalse(decision["valid"])
        self.assertIn("published.json", decision["reason"])

    def test_park_refused_on_terminal_game(self):
        self.with_creds()
        queue.add_game(SLUG, "Tower Duel")
        queue.advance(SLUG, "killed", "setup")
        self.capture_http({"getUpdates": self.updates([
            {"update_id": 1, "message": {
                "chat": {"id": 777}, "text": "park %s why" % SLUG}}])})
        (decision,) = telegram.poll_decisions()
        self.assertFalse(decision["valid"])

    def test_note_on_unknown_slug_invalid(self):
        self.with_creds()
        self.capture_http({"getUpdates": self.updates([
            {"update_id": 1, "message": {
                "chat": {"id": 777}, "text": "note ghost-game loved it"}}])})
        (decision,) = telegram.poll_decisions()
        self.assertEqual(decision["verb"], "note")
        self.assertFalse(decision["valid"])
        self.assertIn("no game", decision["reason"])

    def test_offset_resumes_from_file(self):
        self.with_creds()
        state = os.path.join(self.home, "state")
        os.makedirs(state, exist_ok=True)
        with open(os.path.join(state, ".tg-offset"), "w") as fh:
            fh.write("14")
        calls = self.capture_http({"getUpdates": self.updates([])})
        telegram.poll_decisions()
        self.assertEqual(calls[0]["payload"]["offset"], 14)

    def test_getupdates_failure_returns_empty(self):
        self.with_creds()
        self.capture_http({"getUpdates": {"ok": False,
                                          "description": "down"}})
        self.assertEqual(telegram.poll_decisions(), [])


if __name__ == "__main__":
    unittest.main()
