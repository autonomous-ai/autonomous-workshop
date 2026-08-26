"""ABO's model seats: the boundary, and what a seat's report is allowed to mean.

Every check runs against the recorded transcript. No credential is read, no
socket is opened, and the recorded path deliberately cannot produce a passing
`agent-playtest` — a recording is evidence about the run it came from, not about
the revision under test.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

INVENTOR_ROOT = Path(__file__).resolve().parents[1]
WORKSHOP_ROOT = INVENTOR_ROOT.parents[1]
FIXTURES = INVENTOR_ROOT / "tests" / "fixtures"
for candidate in (INVENTOR_ROOT, FIXTURES, WORKSHOP_ROOT / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

import config  # noqa: E402
import fixture_engine as E  # noqa: E402
import fixture_game as F  # noqa: E402
import model_seats as M  # noqa: E402

TRANSCRIPT = FIXTURES / "model_seat_transcript.json"


def replay(games: int = 2):
    record = F.fixture_record()
    transport = M.RecordedTransport.from_path(TRANSCRIPT)
    played = [
        M.play_model_seat_game(
            E, record, transport, seats=2, game_index=index, seed=100 + index,
            turn_cap=E.MAX_TURNS,
        )
        for index in range(games)
    ]
    return transport, played


class RecordedPathTest(unittest.TestCase):
    def test_the_whole_harness_runs_with_no_network(self):
        transport, games = replay()
        self.assertEqual(len(games), 2)
        for game in games:
            self.assertTrue(game["completed"])
            self.assertGreater(game["turns"], 0)
            self.assertTrue(game["decisions"])
        self.assertFalse(transport.live)

    def test_the_transcript_says_it_is_a_fixture(self):
        transcript = json.loads(TRANSCRIPT.read_text(encoding="utf-8"))
        self.assertTrue(transcript["synthetic"])
        self.assertFalse(transcript["produces_evidence"])
        self.assertIn("FIXTURE", transcript["note"])

    def test_a_recorded_run_can_never_become_evidence(self):
        transport, _games = replay()
        with self.assertRaises(M.ModelSeatsUnavailable) as caught:
            M.assert_can_be_evidence(transport)
        self.assertIn("cannot be evidence about this revision", str(caught.exception))

    def test_a_recording_that_runs_out_stops_rather_than_inventing(self):
        record = F.fixture_record()
        transport = M.RecordedTransport({"replies": {}})
        with self.assertRaises(M.ModelSeatsUnavailable) as caught:
            M.play_model_seat_game(
                E, record, transport, seats=2, game_index=0, seed=100,
                turn_cap=E.MAX_TURNS,
            )
        self.assertIn("rather than inventing", str(caught.exception))


class SeatBoundaryTest(unittest.TestCase):
    def test_a_choice_is_an_index_into_the_enumerated_moves(self):
        _transport, games = replay()
        for game in games:
            for decision in game["decisions"]:
                self.assertIsInstance(decision["choice"], int)
                self.assertGreaterEqual(decision["choice"], 0)

    def test_an_out_of_range_reply_is_refused_rather_than_interpreted(self):
        class OutOfRange:
            live = False
            name = "out-of-range"

            def open_seat(self, key, system):
                pass

            def ask(self, key, text):
                return "CHOICE 9999\nDECISION real\nWHY it looked good."

        with self.assertRaises(M.SeatBoundaryError) as caught:
            M.play_model_seat_game(
                E, F.fixture_record(), OutOfRange(), seats=2, game_index=0,
                seed=1, turn_cap=E.MAX_TURNS,
            )
        message = str(caught.exception)
        self.assertIn("refused rather than interpreted", message)

    def test_a_non_index_reply_is_refused_rather_than_interpreted(self):
        class Prose:
            live = False
            name = "prose"

            def open_seat(self, key, system):
                pass

            def ask(self, key, text):
                return "I would take the middle socket, it seems strongest."

        with self.assertRaises(M.SeatBoundaryError):
            M.play_model_seat_game(
                E, F.fixture_record(), Prose(), seats=2, game_index=0, seed=1,
                turn_cap=E.MAX_TURNS,
            )

    def test_a_seat_is_never_shown_another_seats_messages(self):
        _transport, games = replay()
        for game in games:
            M.assert_no_cross_seat_leak(game)
            # Each seat's own messages are addressed to it and nothing else.
            for seat, messages in game["sent"].items():
                for message in messages:
                    self.assertIn("POSITION (seat %s)" % seat, message)

    def test_the_request_carries_the_position_and_the_moves_and_nothing_else(self):
        transport, _games = replay()
        asked = transport.asked[0]["text"]
        self.assertIn("POSITION (seat", asked)
        self.assertIn("YOUR LEGAL MOVES", asked)
        # No path, no file, no engine handle, no evidence reference.
        for forbidden in ("/Users", ".py", "artifact_sha256", "engine", "evidence"):
            self.assertNotIn(forbidden, asked)

    def test_a_hidden_information_seat_is_never_handed_the_full_state(self):
        class Hidden:
            PLAYERS = (2, 2)
            MAX_TURNS = 4
            HIDDEN_INFO = True

            @staticmethod
            def observation(state, seat):
                return {"mine": state["hands"][seat], "theirs": len(state["hands"][1 - seat])}

        state = {"hands": [["ace", "two"], ["king", "queen"]]}
        view = M.seat_view(Hidden, state, 0)
        self.assertEqual(view["mine"], ["ace", "two"])
        self.assertNotIn("king", json.dumps(view))
        rendered = M.render_position(Hidden, state, 0, [("play", 0)])
        self.assertNotIn("king", rendered)
        self.assertNotIn("queen", rendered)

    def test_a_hidden_engine_with_no_view_cannot_prompt_a_seat(self):
        class Careless:
            PLAYERS = (2, 2)
            HIDDEN_INFO = True

        with self.assertRaises(M.SeatBoundaryError) as caught:
            M.seat_view(Careless, {"everything": 1}, 0)
        self.assertIn("exposes no per-seat view", str(caught.exception))

    def test_a_seats_brief_states_the_boundary_it_is_held_to(self):
        prompt = M.seat_system_prompt(F.fixture_record(), M.ROLES[0], 0, 2)
        self.assertIn("cannot see any other seat's messages", prompt)
        self.assertIn("cannot read or write any file", prompt)
        self.assertIn("may not replay a game", prompt)


class RolesTest(unittest.TestCase):
    def test_two_distinct_non_empty_roles_are_reported(self):
        _transport, games = replay()
        summary = M.summarize(games)
        self.assertEqual(summary["agent_roles"], ["first-reading", "line-finder"])
        M.assert_roles_are_distinct(summary)

    def test_one_role_does_not_pass(self):
        with self.assertRaises(M.SeatBoundaryError) as caught:
            M.assert_roles_are_distinct({"agent_roles": ["first-reading"]})
        self.assertIn("one perspective", str(caught.exception))

    def test_a_repeated_role_does_not_pass(self):
        with self.assertRaises(M.SeatBoundaryError):
            M.assert_roles_are_distinct(
                {"agent_roles": ["first-reading", "first-reading"]}
            )

    def test_an_empty_role_does_not_pass(self):
        with self.assertRaises(M.SeatBoundaryError):
            M.assert_roles_are_distinct({"agent_roles": ["first-reading", "  "]})


class SeatReportTest(unittest.TestCase):
    def setUp(self):
        _transport, self.games = replay()
        self.summary = M.summarize(self.games)

    def test_a_report_that_the_game_got_smaller_is_a_simulation_finding(self):
        self.assertTrue(
            any("the game got smaller" in item for item in self.summary["seat_reports"])
        )

    def test_a_rules_question_raised_in_play_is_recorded(self):
        self.assertTrue(
            any(
                "rules question raised in play" in item
                for item in self.summary["seat_reports"]
            )
        )

    def test_no_seat_report_becomes_a_claim_about_enjoyment(self):
        blob = json.dumps(self.summary).casefold()
        for word in ("enjoy", "fun", "delight", "would play again", "loved"):
            self.assertNotIn(word, blob)
        self.assertIn("independent model", self.summary["claim"])

    def test_decision_free_turns_are_counted_where_they_happen(self):
        # The fixture's seats reported every turn as a real decision, so there
        # is nothing to report; the counter exists and reads zero rather than
        # being absent.
        self.assertIn("decision_kinds", self.summary)
        self.assertEqual(
            sum(self.summary["decision_kinds"].values()), self.summary["decisions"]
        )


class SocialStyleTest(unittest.TestCase):
    def test_the_model_seat_games_feed_the_social_style(self):
        _transport, games = replay()
        summary = M.summarize(games)
        sample = M.social_sample(summary)
        self.assertEqual(sample["source"], "model-seats")
        self.assertEqual(sample["completed_games"], summary["completed_games"])
        self.assertEqual(sample["agent_roles"], summary["agent_roles"])

    def test_the_two_results_stay_separate_records(self):
        _transport, games = replay()
        summary = M.summarize(games)
        sample = M.social_sample(summary)
        # The reference carries counts and roles, not the seat transcripts: the
        # two results answer different questions and keep their own evidence.
        self.assertNotIn("seat_reports", sample)
        self.assertNotIn("decision_kinds", sample)
        self.assertIn("seat_reports", summary)


class ConfigurationTest(unittest.TestCase):
    def test_the_endpoint_is_read_under_abo_scoped_names(self):
        self.assertEqual(
            config.MODEL_SEAT_ENV_NAMES,
            ("ABO_PLAYTEST_BASE_URL", "ABO_PLAYTEST_API_KEY", "ABO_PLAYTEST_MODEL"),
        )

    def test_no_endpoint_configured_is_reported_as_unavailable(self):
        import os
        from unittest import mock

        cleared = {name: "" for name in config.MODEL_SEAT_ENV_NAMES}
        with mock.patch.dict(os.environ, cleared, clear=False):
            for name in config.MODEL_SEAT_ENV_NAMES:
                os.environ.pop(name, None)
            missing = config.missing_model_seat_settings(dotenv_path="/nonexistent")
            self.assertEqual(missing, config.MODEL_SEAT_ENV_NAMES)
            with self.assertRaises(M.ModelSeatsUnavailable) as caught:
                M.HttpModelSeats.from_env(dotenv_path="/nonexistent")
            self.assertIn("no model-seat endpoint is configured", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
