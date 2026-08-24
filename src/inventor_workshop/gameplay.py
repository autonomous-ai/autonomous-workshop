"""Reproducible AI-player Playtest for tabletop games.

The engine tests executable rules, not narrated games.  It can measure
termination, legality, dead states, loops, balance, seat effects, branching,
and action dominance.  It may report experience proxies; it never upgrades an
AI prediction into evidence that humans had fun.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Protocol, Sequence, Tuple

from .errors import ContractError
from .models import require_exact_version, require_sha256


MAX_TRACE_TURNS = 10_000
MAX_STATE_CHARS = 1_000_000


class ExecutableGame(Protocol):
    """Small protocol generated games implement for real simulation."""

    name: str
    version: str
    rules_sha256: str

    def reset(self, seed: int, player_count: int) -> Any:
        ...

    def observe(self, state: Any, player: int) -> Any:
        ...

    def legal_actions(self, state: Any, player: int) -> Sequence[Any]:
        ...

    def step(self, state: Any, action_or_actions: Any) -> Any:
        ...

    def is_terminal(self, state: Any) -> bool:
        ...

    def outcome(self, state: Any) -> Mapping[str, Any]:
        ...

    def canonical_state(self, state: Any) -> str:
        ...


class PlayerPolicy(Protocol):
    name: str
    version: str

    def choose(
        self,
        observation: Any,
        legal_actions: Sequence[Any],
        *,
        player: int,
        turn: int,
        rng: random.Random,
    ) -> Any:
        ...


@dataclass(frozen=True)
class RandomPlayer:
    name: str = "random"
    version: str = "1.0.0"

    def choose(
        self,
        observation: Any,
        legal_actions: Sequence[Any],
        *,
        player: int,
        turn: int,
        rng: random.Random,
    ) -> Any:
        del observation, player, turn
        return legal_actions[rng.randrange(len(legal_actions))]


@dataclass(frozen=True)
class LeagueConfig:
    seeds: Sequence[int]
    player_counts: Sequence[int]
    max_turns: int = 500
    repeat_limit: int = 3

    def __post_init__(self) -> None:
        seeds = tuple(self.seeds)
        counts = tuple(self.player_counts)
        if (
            not seeds
            or len(seeds) > 10_000
            or not all(type(seed) is int and 0 <= seed < 2**63 for seed in seeds)
        ):
            raise ContractError("league seeds must be bounded non-negative integers")
        if (
            not counts
            or not all(type(count) is int and 1 <= count <= 32 for count in counts)
        ):
            raise ContractError("league player_counts must be integers from 1 to 32")
        if len(set(seeds)) != len(seeds) or len(set(counts)) != len(counts):
            raise ContractError("league seeds and player_counts must be unique")
        if type(self.max_turns) is not int or not 1 <= self.max_turns <= MAX_TRACE_TURNS:
            raise ContractError("league max_turns is invalid")
        if type(self.repeat_limit) is not int or not 2 <= self.repeat_limit <= 100:
            raise ContractError("league repeat_limit is invalid")
        object.__setattr__(self, "seeds", seeds)
        object.__setattr__(self, "player_counts", counts)


@dataclass(frozen=True)
class GameTrace:
    seed: int
    player_count: int
    policies: Sequence[str]
    terminal: bool
    turns: int
    stop_reason: str
    outcome: Mapping[str, Any]
    state_chain_sha256: str
    action_counts: Mapping[str, int]
    branching_sum: int
    decisions: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "seed": self.seed,
            "player_count": self.player_count,
            "policies": list(self.policies),
            "terminal": self.terminal,
            "turns": self.turns,
            "stop_reason": self.stop_reason,
            "outcome": dict(self.outcome),
            "state_chain_sha256": self.state_chain_sha256,
            "action_counts": dict(self.action_counts),
            "branching_sum": self.branching_sum,
            "decisions": self.decisions,
        }


@dataclass(frozen=True)
class LeagueReport:
    game: str
    game_version: str
    rules_sha256: str
    policy_versions: Mapping[str, str]
    config: LeagueConfig
    traces: Sequence[GameTrace]
    metrics: Mapping[str, Any]

    @property
    def passed(self) -> bool:
        return bool(self.traces) and all(
            trace.terminal and trace.stop_reason == "terminal" for trace in self.traces
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "game": self.game,
            "game_version": self.game_version,
            "rules_sha256": self.rules_sha256,
            "policy_versions": dict(self.policy_versions),
            "config": {
                "seeds": list(self.config.seeds),
                "player_counts": list(self.config.player_counts),
                "max_turns": self.config.max_turns,
                "repeat_limit": self.config.repeat_limit,
            },
            "passed": self.passed,
            "traces": [trace.to_dict() for trace in self.traces],
            "metrics": dict(self.metrics),
            "experience_claim": (
                "AI-player metrics are predictions and rules evidence, not proof that humans had fun."
            ),
        }


def _canonical(game: ExecutableGame, state: Any) -> str:
    value = game.canonical_state(state)
    if not isinstance(value, str) or not value or len(value) > MAX_STATE_CHARS:
        raise ContractError("game canonical_state must return bounded non-empty text")
    return value


def _update_state_chain(chain: Any, canonical: str) -> None:
    """Hash a length-framed state so distinct state sequences cannot collide."""

    try:
        encoded = canonical.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise ContractError("game canonical_state must return UTF-8 text") from exc
    chain.update(len(encoded).to_bytes(8, "big"))
    chain.update(encoded)


def _action_key(action: Any) -> str:
    try:
        return json.dumps(
            action, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError("game actions must be finite JSON values") from exc


def _policy_names(policies: Sequence[PlayerPolicy]) -> Tuple[str, ...]:
    names = []
    for policy in policies:
        name = getattr(policy, "name", None)
        version = getattr(policy, "version", None)
        if not isinstance(name, str) or not name:
            raise ContractError("AI-player policy name is required")
        require_exact_version(version, "AI-player policy version")
        names.append(name)
    return tuple(names)


def _normalize_outcome(raw: Mapping[str, Any], player_count: int) -> Dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise ContractError("game outcome must be an object")
    scores = raw.get("scores")
    if not isinstance(scores, Mapping):
        raise ContractError("game outcome must contain a scores object")
    normalized_scores: Dict[str, float] = {}
    for player in range(player_count):
        key = str(player)
        value = scores.get(key, scores.get(player))
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
        ):
            raise ContractError("game outcome scores must cover every player with finite numbers")
        normalized_scores[key] = float(value)
    best = max(normalized_scores.values())
    winners = sorted(int(key) for key, score in normalized_scores.items() if score == best)
    return {"scores": normalized_scores, "winners": winners}


def run_game(
    game: ExecutableGame,
    policies: Sequence[PlayerPolicy],
    *,
    seed: int,
    player_count: int,
    max_turns: int,
    repeat_limit: int,
) -> GameTrace:
    """Run one seeded game and fail loudly on an invalid executable model."""

    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ContractError("run_game seed must be a non-negative integer")
    if type(player_count) is not int or not 1 <= player_count <= 32:
        raise ContractError("run_game player_count must be an integer from 1 to 32")
    if type(max_turns) is not int or not 1 <= max_turns <= MAX_TRACE_TURNS:
        raise ContractError("run_game max_turns is invalid")
    if type(repeat_limit) is not int or not 2 <= repeat_limit <= 100:
        raise ContractError("run_game repeat_limit is invalid")
    if len(policies) != player_count:
        raise ContractError("run_game requires exactly one policy per player")
    policy_names = _policy_names(policies)
    rngs = [random.Random((seed << 8) ^ player) for player in range(player_count)]
    state = game.reset(seed, player_count)
    seen: Dict[str, int] = {}
    chain = hashlib.sha256()
    action_counts: Dict[str, int] = {}
    branching_sum = 0
    decisions = 0
    stop_reason = "turn-cap"
    terminal = False
    turns = 0
    outcome: Dict[str, Any] = {}
    for turn in range(max_turns + 1):
        canonical = _canonical(game, state)
        _update_state_chain(chain, canonical)
        seen[canonical] = seen.get(canonical, 0) + 1
        if seen[canonical] >= repeat_limit:
            stop_reason = "repeated-state"
            turns = turn
            break
        is_terminal = game.is_terminal(state)
        if type(is_terminal) is not bool:
            raise ContractError("game is_terminal must return a boolean")
        if is_terminal:
            terminal = True
            stop_reason = "terminal"
            turns = turn
            outcome = _normalize_outcome(game.outcome(state), player_count)
            break
        if turn == max_turns:
            turns = turn
            break
        active = []
        for player in range(player_count):
            raw_actions = game.legal_actions(state, player)
            if isinstance(raw_actions, (str, bytes)) or not isinstance(raw_actions, Sequence):
                raise ContractError("game legal_actions must return a sequence")
            actions = tuple(raw_actions)
            if actions:
                active.append((player, actions))
        if not active:
            stop_reason = "dead-state"
            turns = turn
            break
        chosen: Dict[int, Any] = {}
        for player, actions in active:
            action_keys = tuple(_action_key(action) for action in actions)
            if len(action_keys) != len(set(action_keys)):
                raise ContractError("game legal_actions must not contain duplicate JSON values")
            observation = game.observe(state, player)
            choice = policies[player].choose(
                observation,
                actions,
                player=player,
                turn=turn,
                rng=rngs[player],
            )
            try:
                key = _action_key(choice)
            except ContractError:
                key = ""
            if key not in action_keys:
                stop_reason = "illegal-action"
                turns = turn
                return GameTrace(
                    seed,
                    player_count,
                    policy_names,
                    False,
                    turns,
                    stop_reason,
                    {},
                    chain.hexdigest(),
                    action_counts,
                    branching_sum,
                    decisions,
                )
            chosen[player] = choice
            action_counts[key] = action_counts.get(key, 0) + 1
            branching_sum += len(actions)
            decisions += 1
        payload: Any = chosen[active[0][0]] if len(active) == 1 else chosen
        state = game.step(state, payload)
        turns = turn + 1
    return GameTrace(
        seed,
        player_count,
        policy_names,
        terminal,
        turns,
        stop_reason,
        outcome,
        chain.hexdigest(),
        action_counts,
        branching_sum,
        decisions,
    )


def _wilson(successes: int, total: int) -> Tuple[float, float]:
    if total <= 0:
        return (0.0, 0.0)
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return (round(max(0.0, center - margin), 6), round(min(1.0, center + margin), 6))


def _metrics(traces: Sequence[GameTrace]) -> Dict[str, Any]:
    total = len(traces)
    completed = sum(trace.terminal for trace in traces)
    reasons: Dict[str, int] = {}
    action_counts: Dict[str, int] = {}
    seat_wins: Dict[str, int] = {}
    seat_games: Dict[str, int] = {}
    policy_wins: Dict[str, int] = {}
    policy_games: Dict[str, int] = {}
    branching_sum = decisions = 0
    for trace in traces:
        reasons[trace.stop_reason] = reasons.get(trace.stop_reason, 0) + 1
        for action, count in trace.action_counts.items():
            action_counts[action] = action_counts.get(action, 0) + count
        branching_sum += trace.branching_sum
        decisions += trace.decisions
        if trace.terminal:
            for player in range(trace.player_count):
                key = str(player)
                seat_games[key] = seat_games.get(key, 0) + 1
                policy = trace.policies[player]
                policy_games[policy] = policy_games.get(policy, 0) + 1
            winners = trace.outcome.get("winners", [])
            if len(winners) == 1:
                key = str(winners[0])
                seat_wins[key] = seat_wins.get(key, 0) + 1
                policy = trace.policies[winners[0]]
                policy_wins[policy] = policy_wins.get(policy, 0) + 1
    action_total = sum(action_counts.values())
    dominant = max(action_counts.values()) / action_total if action_total else 0.0
    seat_rates = {}
    for seat, games in sorted(seat_games.items(), key=lambda item: int(item[0])):
        wins = seat_wins.get(seat, 0)
        seat_rates[seat] = {
            "wins": wins,
            "games": games,
            "rate": round(wins / games, 6) if games else 0.0,
            "ci95": list(_wilson(wins, games)),
        }
    policy_rates = {}
    for policy, games in sorted(policy_games.items()):
        wins = policy_wins.get(policy, 0)
        policy_rates[policy] = {
            "wins": wins,
            "games": games,
            "rate": round(wins / games, 6) if games else 0.0,
            "ci95": list(_wilson(wins, games)),
        }
    return {
        "games": total,
        "completed": completed,
        "completion_rate": round(completed / total, 6) if total else 0.0,
        "stop_reasons": reasons,
        "mean_turns": round(sum(trace.turns for trace in traces) / total, 6) if total else 0.0,
        "mean_branching_factor": round(branching_sum / decisions, 6) if decisions else 0.0,
        "dominant_action_rate": round(dominant, 6),
        "seat_results": seat_rates,
        "policy_results": policy_rates,
    }


def run_league(
    game: ExecutableGame,
    policies: Sequence[PlayerPolicy],
    config: LeagueConfig,
) -> LeagueReport:
    """Rotate policies through seats and run every configured seed/count."""

    if not policies:
        raise ContractError("AI-player league requires at least one policy")
    policy_names = list(_policy_names(policies))
    if len(policy_names) != len(set(policy_names)):
        raise ContractError("AI-player policy names must be unique")
    game_name = getattr(game, "name", None)
    game_version = getattr(game, "version", None)
    rules_sha256 = getattr(game, "rules_sha256", None)
    if not isinstance(game_name, str) or not game_name:
        raise ContractError("executable game name is required")
    require_exact_version(game_version, "executable game version")
    require_sha256(rules_sha256, "executable game rules_sha256")
    traces = []
    for player_count in config.player_counts:
        for offset in range(len(policies)):
            seats = tuple(
                policies[(seat + offset) % len(policies)] for seat in range(player_count)
            )
            for seed in config.seeds:
                traces.append(
                    run_game(
                        game,
                        seats,
                        seed=seed,
                        player_count=player_count,
                        max_turns=config.max_turns,
                        repeat_limit=config.repeat_limit,
                    )
                )
    return LeagueReport(
        game_name,
        game_version,
        rules_sha256,
        {policy.name: policy.version for policy in policies},
        config,
        tuple(traces),
        _metrics(traces),
    )


__all__ = [
    "ExecutableGame",
    "GameTrace",
    "LeagueConfig",
    "LeagueReport",
    "PlayerPolicy",
    "RandomPlayer",
    "run_game",
    "run_league",
]
