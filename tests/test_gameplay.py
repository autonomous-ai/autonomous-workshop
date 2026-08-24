import hashlib
import json
import unittest

from inventor_workshop.errors import ContractError
from inventor_workshop.gameplay import (
    LeagueConfig,
    RandomPlayer,
    run_game,
    run_league,
)


RULES_SHA256 = hashlib.sha256(b"gameplay test rules").hexdigest()


class ConstantPlayer:
    version = "1.0.0"

    def __init__(self, name="constant", choice="go"):
        self.name = name
        self.choice = choice

    def choose(self, observation, legal_actions, *, player, turn, rng):
        del observation, legal_actions, player, turn, rng
        return self.choice


class OneMoveGame:
    """Every seat acts once; seat zero wins deterministically."""

    name = "one-move"
    version = "1.0.0"
    rules_sha256 = RULES_SHA256

    def reset(self, seed, player_count):
        return {"done": False, "players": player_count, "seed": seed}

    def observe(self, state, player):
        return {"done": state["done"], "seat": player}

    def legal_actions(self, state, player):
        del player
        return [] if state["done"] else ["go"]

    def step(self, state, action_or_actions):
        del action_or_actions
        return dict(state, done=True)

    def is_terminal(self, state):
        return state["done"]

    def outcome(self, state):
        return {
            "scores": {
                str(player): 1 if player == 0 else 0
                for player in range(state["players"])
            }
        }

    def canonical_state(self, state):
        return json.dumps(state, sort_keys=True, separators=(",", ":"))


class TakeAwayGame:
    """A small turn-based game with real seeded policy choices."""

    name = "take-away"
    version = "2026.08.23"
    rules_sha256 = RULES_SHA256

    def reset(self, seed, player_count):
        return {
            "stones": 5 + seed % 3,
            "current": seed % player_count,
            "last": None,
            "players": player_count,
        }

    def observe(self, state, player):
        return {"stones": state["stones"], "your_turn": state["current"] == player}

    def legal_actions(self, state, player):
        if state["stones"] == 0 or state["current"] != player:
            return []
        return tuple(range(1, min(2, state["stones"]) + 1))

    def step(self, state, action_or_actions):
        amount = int(action_or_actions)
        return {
            "stones": state["stones"] - amount,
            "current": (state["current"] + 1) % state["players"],
            "last": state["current"],
            "players": state["players"],
        }

    def is_terminal(self, state):
        return state["stones"] == 0

    def outcome(self, state):
        return {
            "scores": {
                player: 1 if player == state["last"] else 0
                for player in range(state["players"])
            }
        }

    def canonical_state(self, state):
        return json.dumps(state, sort_keys=True, separators=(",", ":"))


class ToggleGame:
    name = "toggle"
    version = "1.0.0"
    rules_sha256 = RULES_SHA256

    def reset(self, seed, player_count):
        del seed, player_count
        return 0

    def observe(self, state, player):
        return {"state": state, "player": player}

    def legal_actions(self, state, player):
        del state
        return ["flip"] if player == 0 else []

    def step(self, state, action_or_actions):
        del action_or_actions
        return 1 - state

    def is_terminal(self, state):
        del state
        return False

    def outcome(self, state):
        raise AssertionError("a looping game has no outcome")

    def canonical_state(self, state):
        return str(state)


class DeadGame(ToggleGame):
    name = "dead"

    def legal_actions(self, state, player):
        del state, player
        return []


class CounterGame(ToggleGame):
    name = "counter"

    def legal_actions(self, state, player):
        del state
        return ["count"] if player == 0 else []

    def step(self, state, action_or_actions):
        del action_or_actions
        return state + 1


class GameplayEngineTest(unittest.TestCase):
    def test_seeded_game_and_league_replay_are_byte_deterministic(self):
        players = (
            RandomPlayer(name="random-a", version="1.2.0"),
            RandomPlayer(name="random-b", version="1.2.0"),
        )
        arguments = {
            "seed": 17,
            "player_count": 2,
            "max_turns": 20,
            "repeat_limit": 3,
        }
        first_trace = run_game(TakeAwayGame(), players, **arguments)
        second_trace = run_game(TakeAwayGame(), players, **arguments)
        self.assertEqual(first_trace, second_trace)
        self.assertTrue(first_trace.terminal)
        self.assertEqual(first_trace.stop_reason, "terminal")
        self.assertGreater(first_trace.decisions, 0)
        self.assertEqual(len(first_trace.state_chain_sha256), 64)

        config = LeagueConfig(seeds=(2, 17), player_counts=(2,), max_turns=20)
        first = run_league(TakeAwayGame(), players, config)
        second = run_league(TakeAwayGame(), players, config)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(
            json.dumps(first.to_dict(), sort_keys=True, separators=(",", ":")),
            json.dumps(second.to_dict(), sort_keys=True, separators=(",", ":")),
        )
        self.assertTrue(first.passed)
        self.assertEqual(first.metrics["games"], 4)
        self.assertEqual(first.metrics["completion_rate"], 1.0)
        self.assertEqual(first.metrics["stop_reasons"], {"terminal": 4})
        self.assertIn("not proof that humans had fun", first.to_dict()["experience_claim"])

    def test_league_rotates_policies_and_reports_seat_and_policy_results(self):
        alpha = ConstantPlayer("alpha")
        beta = ConstantPlayer("beta")
        report = run_league(
            OneMoveGame(),
            (alpha, beta),
            LeagueConfig(seeds=(0,), player_counts=(1, 2), max_turns=2),
        )

        self.assertEqual(
            [tuple(trace.policies) for trace in report.traces],
            [("alpha",), ("beta",), ("alpha", "beta"), ("beta", "alpha")],
        )
        self.assertEqual(report.metrics["games"], 4)
        self.assertEqual(report.metrics["mean_turns"], 1.0)
        self.assertEqual(report.metrics["mean_branching_factor"], 1.0)
        self.assertEqual(report.metrics["dominant_action_rate"], 1.0)
        self.assertEqual(
            {seat: (result["wins"], result["games"], result["rate"])
             for seat, result in report.metrics["seat_results"].items()},
            {"0": (4, 4, 1.0), "1": (0, 2, 0.0)},
        )
        self.assertEqual(
            {name: (result["wins"], result["games"], result["rate"])
             for name, result in report.metrics["policy_results"].items()},
            {"alpha": (2, 3, 0.666667), "beta": (2, 3, 0.666667)},
        )
        for result in report.metrics["seat_results"].values():
            self.assertEqual(len(result["ci95"]), 2)
            self.assertLessEqual(result["ci95"][0], result["rate"])
            self.assertGreaterEqual(result["ci95"][1], result["rate"])

    def test_repeated_state_is_detected_before_the_turn_cap(self):
        trace = run_game(
            ToggleGame(),
            (ConstantPlayer(choice="flip"),),
            seed=0,
            player_count=1,
            max_turns=20,
            repeat_limit=2,
        )
        self.assertFalse(trace.terminal)
        self.assertEqual(trace.stop_reason, "repeated-state")
        self.assertEqual(trace.turns, 2)
        self.assertEqual(trace.decisions, 2)
        self.assertEqual(trace.branching_sum, 2)
        self.assertEqual(trace.action_counts, {'"flip"': 2})

    def test_nonterminal_state_without_actions_is_a_dead_state(self):
        trace = run_game(
            DeadGame(),
            (ConstantPlayer(),),
            seed=0,
            player_count=1,
            max_turns=5,
            repeat_limit=3,
        )
        self.assertEqual(trace.stop_reason, "dead-state")
        self.assertEqual(trace.turns, 0)
        self.assertEqual(trace.decisions, 0)
        self.assertEqual(trace.outcome, {})

    def test_policy_choice_outside_legal_actions_is_recorded_as_illegal(self):
        trace = run_game(
            CounterGame(),
            (ConstantPlayer(choice={"not": "an action"}),),
            seed=0,
            player_count=1,
            max_turns=5,
            repeat_limit=3,
        )
        self.assertEqual(trace.stop_reason, "illegal-action")
        self.assertEqual(trace.turns, 0)
        self.assertEqual(trace.decisions, 0)
        self.assertEqual(trace.action_counts, {})

    def test_monotonic_nonterminal_game_stops_at_exact_turn_cap(self):
        trace = run_game(
            CounterGame(),
            (ConstantPlayer(choice="count"),),
            seed=0,
            player_count=1,
            max_turns=3,
            repeat_limit=2,
        )
        self.assertFalse(trace.terminal)
        self.assertEqual(trace.stop_reason, "turn-cap")
        self.assertEqual(trace.turns, 3)
        self.assertEqual(trace.decisions, 3)
        self.assertEqual(trace.action_counts, {'"count"': 3})

    def test_state_chain_uses_unambiguous_length_framing(self):
        class TwoStateGame(OneMoveGame):
            def canonical_state(self, state):
                return "b" if state["done"] else "a"

        class OnePackedStateGame(OneMoveGame):
            def reset(self, seed, player_count):
                return {"done": True, "players": player_count, "seed": seed}

            def canonical_state(self, state):
                del state
                return "a\0b"

        two = run_game(
            TwoStateGame(),
            (ConstantPlayer(),),
            seed=0,
            player_count=1,
            max_turns=1,
            repeat_limit=2,
        )
        packed = run_game(
            OnePackedStateGame(),
            (ConstantPlayer(),),
            seed=0,
            player_count=1,
            max_turns=1,
            repeat_limit=2,
        )
        self.assertNotEqual(two.state_chain_sha256, packed.state_chain_sha256)

    def test_invalid_run_contracts_and_executable_outputs_fail_closed(self):
        player = ConstantPlayer()
        valid = {
            "seed": 0,
            "player_count": 1,
            "max_turns": 2,
            "repeat_limit": 2,
        }
        for changed in (
            {"seed": True},
            {"seed": -1},
            {"player_count": 0},
            {"max_turns": 0},
            {"repeat_limit": 1},
        ):
            arguments = dict(valid, **changed)
            with self.subTest(arguments=arguments), self.assertRaises(ContractError):
                run_game(OneMoveGame(), (player,), **arguments)
        with self.assertRaisesRegex(ContractError, "exactly one policy"):
            run_game(OneMoveGame(), (), **valid)

        class DuplicateActionGame(CounterGame):
            def legal_actions(self, state, player):
                del state
                return ["count", "count"] if player == 0 else []

        with self.assertRaisesRegex(ContractError, "duplicate JSON"):
            run_game(DuplicateActionGame(), (ConstantPlayer(choice="count"),), **valid)

        class InvalidTerminalGame(DeadGame):
            def is_terminal(self, state):
                del state
                return 1

        with self.assertRaisesRegex(ContractError, "must return a boolean"):
            run_game(InvalidTerminalGame(), (player,), **valid)

        class InvalidOutcomeGame(OneMoveGame):
            def outcome(self, state):
                del state
                return {"scores": {}}

        with self.assertRaisesRegex(ContractError, "scores must cover every player"):
            run_game(InvalidOutcomeGame(), (player,), **valid)

    def test_league_configuration_and_metadata_are_pinned(self):
        self.assertEqual(
            LeagueConfig(seeds=[1, 2], player_counts=[1]).seeds,
            (1, 2),
        )
        for config in (
            {"seeds": (), "player_counts": (1,)},
            {"seeds": (1, 1), "player_counts": (1,)},
            {"seeds": (1,), "player_counts": (0,)},
            {"seeds": (1,), "player_counts": (1, 1)},
            {"seeds": (1,), "player_counts": (1,), "max_turns": 0},
            {"seeds": (1,), "player_counts": (1,), "repeat_limit": 1},
        ):
            with self.subTest(config=config), self.assertRaises(ContractError):
                LeagueConfig(**config)

        with self.assertRaisesRegex(ContractError, "names must be unique"):
            run_league(
                OneMoveGame(),
                (ConstantPlayer("same"), ConstantPlayer("same")),
                LeagueConfig(seeds=(1,), player_counts=(2,)),
            )
        moving = ConstantPlayer()
        moving.version = "latest"
        with self.assertRaisesRegex(ContractError, "exact, non-floating"):
            run_league(
                OneMoveGame(),
                (moving,),
                LeagueConfig(seeds=(1,), player_counts=(1,)),
            )


if __name__ == "__main__":
    unittest.main()
