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

from workshop.errors import ContractError
from workshop._validation import require_exact_version, require_sha256


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


FINITE_GAME_RULES_PROTOCOL = "workshop-finite-token-game-v2"
FINITE_GAME_SIMULATOR_ID = "workshop-finite-token-rules"
FINITE_GAME_SIMULATOR_VERSION = "2.1.0"
FINITE_GAME_RULE_KINDS = frozenset(
    ("shared-supply-take-away", "ordered-shore-sweep")
)
FINITE_GAME_STYLES = ("optimizing", "social", "exploratory", "adversarial")
_FINITE_GAME_SPEC_KEYS = frozenset(
    (
        "enabled",
        "title",
        "rule_kind",
        "starting_tokens",
        "max_take",
        "last_take_wins",
        "theme",
        "token_part_ids",
        "token_sweep_values",
    )
)


def validate_finite_game_spec(value: Any) -> Mapping[str, Any]:
    """Validate the exact sealed data accepted by the pinned two-family engine."""

    if not isinstance(value, Mapping) or set(value) != _FINITE_GAME_SPEC_KEYS:
        raise ContractError("finite-token game_spec has an unsupported schema")
    identifiers = value.get("token_part_ids")
    sweeps = value.get("token_sweep_values")
    if (
        value.get("enabled") is not True
        or not isinstance(value.get("title"), str)
        or not value["title"].strip()
        or value.get("rule_kind") not in FINITE_GAME_RULE_KINDS
        or type(value.get("starting_tokens")) is not int
        or not 7 <= value["starting_tokens"] <= 10
        or type(value.get("max_take")) is not int
        or not 2 <= value["max_take"] <= 4
        or type(value.get("last_take_wins")) is not bool
        or not isinstance(value.get("theme"), str)
        or not value["theme"].strip()
        or not isinstance(identifiers, list)
        or len(identifiers) != value["starting_tokens"]
        or not all(isinstance(item, str) and item for item in identifiers)
        or len(identifiers) != len(set(identifiers))
        or not isinstance(sweeps, list)
    ):
        raise ContractError("finite-token game_spec is incomplete")
    if value["rule_kind"] == "shared-supply-take-away":
        if sweeps or value["starting_tokens"] <= value["max_take"]:
            raise ContractError("shared-supply game_spec is inconsistent")
    elif (
        value["starting_tokens"] != 7
        or value["max_take"] != 3
        or value["last_take_wins"] is not True
        or len(sweeps) != value["starting_tokens"]
        or not all(type(item) is int and 1 <= item <= 3 for item in sweeps)
    ):
        raise ContractError("ordered shore-sweep game_spec is inconsistent")
    return dict(value)


class _FiniteGameRng:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF
        self.values: list[int] = []

    def random(self) -> float:
        """Return the exact Mulberry32 sample and retain its underlying u32."""

        self.state = (self.state + 0x6D2B79F5) & 0xFFFFFFFF
        value = self.state
        value = ((value ^ (value >> 15)) * (value | 1)) & 0xFFFFFFFF
        value ^= (
            value
            + (((value ^ (value >> 7)) * (value | 61)) & 0xFFFFFFFF)
        ) & 0xFFFFFFFF
        value = (value ^ (value >> 14)) & 0xFFFFFFFF
        self.values.append(value)
        return value / 4294967296.0

    def randint(self, low: int, high: int) -> int:
        return low + int(self.random() * (high - low + 1))

    def pick(self, values: Sequence[Any]) -> Any:
        return values[self.randint(0, len(values) - 1)]

    def clone(self) -> "_FiniteGameRng":
        clone = _FiniteGameRng(0)
        clone.state = self.state
        clone.values = list(self.values)
        return clone


def _finite_actions(
    spec: Mapping[str, Any], remaining: Sequence[str]
) -> list[Mapping[str, Any]]:
    if not remaining:
        return []
    if spec["rule_kind"] == "shared-supply-take-away":
        return [
            {"count": count}
            for count in range(1, min(spec["max_take"], len(remaining)) + 1)
        ]
    sweep_by_id = dict(zip(spec["token_part_ids"], spec["token_sweep_values"]))
    actions: list[Mapping[str, Any]] = []
    for shore, exposed in (("L", remaining[0]), ("S", remaining[-1])):
        for count in range(1, min(sweep_by_id[exposed], len(remaining)) + 1):
            action = {"shore": shore, "k": count}
            if len(remaining) == 1 and action == {"shore": "S", "k": 1}:
                continue
            actions.append(action)
    return actions


def _finite_apply(
    remaining: Sequence[str], action: Mapping[str, Any]
) -> Tuple[list[str], list[str]]:
    count = action.get("k", action.get("count"))
    if action.get("shore") == "S":
        return list(remaining[:-count]), list(reversed(remaining[-count:]))
    return list(remaining[count:]), list(remaining[:count])


def _finite_removal_size(action: Mapping[str, Any]) -> int:
    return int(action.get("k", action.get("count")))


def _finite_position(
    spec: Mapping[str, Any], remaining: Sequence[str], memo: Dict[Tuple[str, ...], Tuple[bool, int]]
) -> Tuple[bool, int]:
    key = tuple(remaining)
    if key in memo:
        return memo[key]
    candidates = []
    for action in _finite_actions(spec, remaining):
        successor, unused_removed = _finite_apply(remaining, action)
        del unused_removed
        if not successor:
            candidates.append((bool(spec["last_take_wins"]), 1))
        else:
            opponent_wins, opponent_plies = _finite_position(spec, successor, memo)
            candidates.append((not opponent_wins, opponent_plies + 1))
    wins = [plies for winning, plies in candidates if winning]
    result = (True, min(wins)) if wins else (False, max(plies for _, plies in candidates))
    memo[key] = result
    return result


def _finite_choose(
    spec: Mapping[str, Any],
    remaining: Sequence[str],
    style: str,
    previous_action: Optional[Mapping[str, Any]],
    policy_memory: Dict[str, Dict[str, int]],
    rng: _FiniteGameRng,
    opponent_style: str,
    *,
    allow_adversarial_prediction: bool = True,
) -> Mapping[str, Any]:
    actions = _finite_actions(spec, remaining)
    if style == "social":
        if spec["rule_kind"] == "shared-supply-take-away":
            return actions[0]
        scored = []
        previous_shore = previous_action.get("shore") if previous_action else None
        for action in actions:
            successor, unused_removed = _finite_apply(remaining, action)
            del unused_removed
            replies = len(_finite_actions(spec, successor))
            scored.append(
                (
                    (
                        int(replies >= 2),
                        int(action["shore"] != previous_shore),
                        -_finite_removal_size(action),
                    ),
                    action,
                )
            )
        best = max(score for score, unused in scored)
        return rng.pick([action for score, action in scored if score == best])
    if style == "exploratory":
        visits = policy_memory.setdefault(style, {})
        weighted = []
        for action in actions:
            successor, unused_removed = _finite_apply(remaining, action)
            del unused_removed
            key = "\u001f".join(successor)
            weighted.append((action, key, 1.0 / (1 + visits.get(key, 0))))
        draw = rng.random() * sum(
            weight for unused_action, unused_key, weight in weighted
        )
        chosen = weighted[-1]
        for row in weighted:
            if draw < row[2]:
                chosen = row
                break
            draw -= row[2]
        visits[chosen[1]] = visits.get(chosen[1], 0) + 1
        return chosen[0]
    if style == "adversarial":
        if not allow_adversarial_prediction:
            style = "optimizing"
        else:
            scored = []
            for action in actions:
                successor, unused_removed = _finite_apply(remaining, action)
                del unused_removed
                if not successor:
                    score = (1, 0, 0, 0, 0)
                else:
                    prediction_rng = rng.clone()
                    prediction_memory = {
                        name: dict(visits)
                        for name, visits in policy_memory.items()
                    }
                    predicted = _finite_choose(
                        spec,
                        successor,
                        opponent_style,
                        action,
                        prediction_memory,
                        prediction_rng,
                        "adversarial",
                        allow_adversarial_prediction=False,
                    )
                    after_prediction, unused_prediction_removed = _finite_apply(
                        successor, predicted
                    )
                    del unused_prediction_removed
                    opponent_heuristic = (
                        int(not after_prediction),
                        _finite_removal_size(predicted),
                        -len(_finite_actions(spec, after_prediction)),
                    )
                    score = (
                        0,
                        -opponent_heuristic[0],
                        -opponent_heuristic[1],
                        -opponent_heuristic[2],
                        len(_finite_actions(spec, successor)),
                    )
                scored.append((score, action))
            best = max(score for score, unused in scored)
            return rng.pick([action for score, action in scored if score == best])

    if style == "optimizing":
        scored = []
        memo: Dict[Tuple[str, ...], Tuple[bool, int]] = {}
        for action in actions:
            successor, unused_removed = _finite_apply(remaining, action)
            del unused_removed
            if not successor:
                winning, plies = bool(spec["last_take_wins"]), 1
            else:
                opponent_wins, opponent_plies = _finite_position(
                    spec, successor, memo
                )
                winning, plies = not opponent_wins, opponent_plies + 1
            score = (int(winning), -plies if winning else plies)
            scored.append((score, action))
        best = max(score for score, unused in scored)
        return rng.pick([action for score, action in scored if score == best])
    raise ContractError("finite-token player style is unsupported")


def replay_finite_game(
    raw_spec: Mapping[str, Any], request: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Independently replay one pinned raw trace for trusted output comparison."""

    spec = validate_finite_game_spec(raw_spec)
    if (
        not isinstance(request, Mapping)
        or set(request) != {"index", "seed", "player_styles", "first_seat"}
        or type(request.get("index")) is not int
        or type(request.get("seed")) is not int
        or not 0 <= request["seed"] < 2**32
        or not isinstance(request.get("player_styles"), list)
        or len(request["player_styles"]) != 2
        or any(style not in FINITE_GAME_STYLES for style in request["player_styles"])
        or request.get("first_seat") not in (0, 1)
    ):
        raise ContractError("finite-token game request is invalid")
    rng = _FiniteGameRng(request["seed"])
    remaining = list(spec["token_part_ids"])
    active = request["first_seat"]
    previous_action: Optional[Mapping[str, Any]] = None
    policy_memory: Dict[str, Dict[str, int]] = {
        style: {} for style in FINITE_GAME_STYLES
    }
    trace = []
    winner = None
    while remaining and len(trace) < spec["starting_tokens"]:
        legal = _finite_actions(spec, remaining)
        before_rng = len(rng.values)
        pre_rng_state = rng.state
        pre_policy_memory = {
            name: dict(visits) for name, visits in policy_memory.items()
        }
        style = request["player_styles"][active]
        action = _finite_choose(
            spec,
            remaining,
            style,
            previous_action,
            policy_memory,
            rng,
            request["player_styles"][1 - active],
        )
        if action not in legal:
            break
        successor, removed = _finite_apply(remaining, action)
        trace.append(
            {
                "turn": len(trace),
                "player": active,
                "style": style,
                "pre_remaining_token_part_ids": list(remaining),
                "pre_previous_action": (
                    dict(previous_action) if previous_action is not None else None
                ),
                "pre_policy_memory": pre_policy_memory,
                "pre_rng_state": pre_rng_state,
                "legal_actions": list(legal),
                "intended_action": dict(action),
                "action": dict(action),
                "removed_token_part_ids": removed,
                "post_remaining_token_part_ids": successor,
                "post_previous_action": dict(action),
                "post_policy_memory": {
                    name: dict(visits)
                    for name, visits in policy_memory.items()
                },
                "post_rng_state": rng.state,
                "rng_values_used": rng.values[before_rng:],
                "terminal": not successor,
            }
        )
        remaining = successor
        previous_action = action
        if not remaining:
            winner = active if spec["last_take_wins"] else 1 - active
            break
        active = 1 - active
    issues = []
    if winner is None:
        issues.append("termination_bound_exceeded")
    return {
        "index": request["index"],
        "seed": request["seed"],
        "player_styles": list(request["player_styles"]),
        "first_seat": request["first_seat"],
        "rule_kind": spec["rule_kind"],
        "completed": winner is not None and not issues,
        "turns": len(trace),
        "actions": trace,
        "restoration_log": (
            [
                {"id": part_id, "sweep": sweep}
                for part_id, sweep in zip(
                    spec["token_part_ids"], spec["token_sweep_values"]
                )
            ]
            if spec["token_sweep_values"]
            else [{"id": part_id} for part_id in spec["token_part_ids"]]
        ),
        "first_action": dict(trace[0]["action"]) if trace else None,
        "outcome": (
            None
            if winner is None
            else {
                "winner": winner,
                "loser": 1 - winner,
                "winner_style": request["player_styles"][winner],
                "loser_style": request["player_styles"][1 - winner],
                "winner_score": 1,
                "loser_score": 0,
                "tokens_remaining": len(remaining),
            }
        ),
        "rng_values": list(rng.values),
        "rng_state": rng.state,
        "issues": issues,
    }


FINITE_GAME_SIMULATOR_SOURCE = r'''#!/usr/bin/env python3
"""Pinned deterministic simulator for two finite Workshop token-rule families."""

import argparse
import json
from pathlib import Path

REQUEST_PROTOCOL = "workshop-seeded-games-v1"
RULES_PROTOCOL = "workshop-finite-token-game-v2"
SIMULATOR = {"id": "workshop-finite-token-rules", "version": "2.1.0"}
RULE_KINDS = {"shared-supply-take-away", "ordered-shore-sweep"}
STYLE_ORDER = ("optimizing", "social", "exploratory", "adversarial")
STYLES = set(STYLE_ORDER)
SPEC_KEYS = {
    "enabled", "title", "rule_kind", "starting_tokens", "max_take",
    "last_take_wins", "theme", "token_part_ids", "token_sweep_values",
}


def validate_spec(value):
    if not isinstance(value, dict) or set(value) != SPEC_KEYS:
        raise ValueError("unsupported game_spec")
    identifiers = value.get("token_part_ids")
    sweeps = value.get("token_sweep_values")
    if (
        value.get("enabled") is not True
        or not isinstance(value.get("title"), str) or not value["title"].strip()
        or value.get("rule_kind") not in RULE_KINDS
        or type(value.get("starting_tokens")) is not int
        or not 7 <= value["starting_tokens"] <= 10
        or type(value.get("max_take")) is not int
        or not 2 <= value["max_take"] <= 4
        or type(value.get("last_take_wins")) is not bool
        or not isinstance(value.get("theme"), str) or not value["theme"].strip()
        or not isinstance(identifiers, list)
        or len(identifiers) != value["starting_tokens"]
        or not all(isinstance(item, str) and item for item in identifiers)
        or len(identifiers) != len(set(identifiers))
        or not isinstance(sweeps, list)
    ):
        raise ValueError("incomplete game_spec")
    if value["rule_kind"] == "shared-supply-take-away":
        if sweeps or value["starting_tokens"] <= value["max_take"]:
            raise ValueError("inconsistent shared-supply game_spec")
    elif (
        value["starting_tokens"] != 7
        or value["max_take"] != 3
        or value["last_take_wins"] is not True
        or len(sweeps) != value["starting_tokens"]
        or not all(type(item) is int and 1 <= item <= 3 for item in sweeps)
    ):
        raise ValueError("inconsistent shore-sweep game_spec")
    return value


class StableRng:
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFF
        self.values = []

    def random(self):
        self.state = (self.state + 0x6D2B79F5) & 0xFFFFFFFF
        value = self.state
        value = ((value ^ (value >> 15)) * (value | 1)) & 0xFFFFFFFF
        value ^= (
            value
            + (((value ^ (value >> 7)) * (value | 61)) & 0xFFFFFFFF)
        ) & 0xFFFFFFFF
        value = (value ^ (value >> 14)) & 0xFFFFFFFF
        self.values.append(value)
        return value / 4294967296.0

    def randint(self, low, high):
        return low + int(self.random() * (high - low + 1))

    def pick(self, values):
        return values[self.randint(0, len(values) - 1)]

    def clone(self):
        clone = StableRng(0)
        clone.state = self.state
        clone.values = list(self.values)
        return clone


def legal_actions(spec, remaining):
    if not remaining:
        return []
    if spec["rule_kind"] == "shared-supply-take-away":
        return [
            {"count": count}
            for count in range(1, min(spec["max_take"], len(remaining)) + 1)
        ]
    sweep_by_id = dict(zip(spec["token_part_ids"], spec["token_sweep_values"]))
    actions = []
    for shore, exposed in (("L", remaining[0]), ("S", remaining[-1])):
        for count in range(1, min(sweep_by_id[exposed], len(remaining)) + 1):
            action = {"shore": shore, "k": count}
            if len(remaining) == 1 and action == {"shore": "S", "k": 1}:
                continue
            actions.append(action)
    return actions


def apply_action(remaining, action):
    count = action.get("k", action.get("count"))
    if action.get("shore") == "S":
        return list(remaining[:-count]), list(reversed(remaining[-count:]))
    return list(remaining[count:]), list(remaining[:count])


def removal_size(action):
    return int(action.get("k", action.get("count")))


def position(spec, remaining, memo):
    key = tuple(remaining)
    if key in memo:
        return memo[key]
    candidates = []
    for action in legal_actions(spec, remaining):
        successor, _ = apply_action(remaining, action)
        if not successor:
            candidates.append((bool(spec["last_take_wins"]), 1))
        else:
            opponent_wins, opponent_plies = position(spec, successor, memo)
            candidates.append((not opponent_wins, opponent_plies + 1))
    wins = [plies for winning, plies in candidates if winning]
    result = (True, min(wins)) if wins else (False, max(plies for _, plies in candidates))
    memo[key] = result
    return result


def choose(
    spec, remaining, style, previous_action, policy_memory, rng,
    opponent_style, allow_adversarial_prediction=True,
):
    actions = legal_actions(spec, remaining)
    if style == "social":
        if spec["rule_kind"] == "shared-supply-take-away":
            return actions[0]
        scored = []
        previous_shore = previous_action.get("shore") if previous_action else None
        for action in actions:
            successor, _ = apply_action(remaining, action)
            replies = len(legal_actions(spec, successor))
            scored.append(
                (
                    (
                        int(replies >= 2),
                        int(action["shore"] != previous_shore),
                        -removal_size(action),
                    ),
                    action,
                )
            )
        best = max(score for score, _ in scored)
        return rng.pick([action for score, action in scored if score == best])
    if style == "exploratory":
        visits = policy_memory.setdefault(style, {})
        weighted = []
        for action in actions:
            successor, _ = apply_action(remaining, action)
            key = "\u001f".join(successor)
            weighted.append((action, key, 1.0 / (1 + visits.get(key, 0))))
        draw = rng.random() * sum(weight for _, _, weight in weighted)
        chosen = weighted[-1]
        for row in weighted:
            if draw < row[2]:
                chosen = row
                break
            draw -= row[2]
        visits[chosen[1]] = visits.get(chosen[1], 0) + 1
        return chosen[0]
    if style == "adversarial":
        if not allow_adversarial_prediction:
            style = "optimizing"
        else:
            scored = []
            for action in actions:
                successor, _ = apply_action(remaining, action)
                if not successor:
                    score = (1, 0, 0, 0, 0)
                else:
                    prediction_rng = rng.clone()
                    prediction_memory = {
                        name: dict(visits)
                        for name, visits in policy_memory.items()
                    }
                    predicted = choose(
                        spec, successor, opponent_style, action,
                        prediction_memory, prediction_rng, "adversarial", False,
                    )
                    after_prediction, _ = apply_action(successor, predicted)
                    opponent_heuristic = (
                        int(not after_prediction),
                        removal_size(predicted),
                        -len(legal_actions(spec, after_prediction)),
                    )
                    score = (
                        0,
                        -opponent_heuristic[0],
                        -opponent_heuristic[1],
                        -opponent_heuristic[2],
                        len(legal_actions(spec, successor)),
                    )
                scored.append((score, action))
            best = max(score for score, _ in scored)
            return rng.pick([action for score, action in scored if score == best])
    if style == "optimizing":
        memo = {}
        scored = []
        for action in actions:
            successor, _ = apply_action(remaining, action)
            if not successor:
                winning, plies = bool(spec["last_take_wins"]), 1
            else:
                opponent_wins, opponent_plies = position(spec, successor, memo)
                winning, plies = not opponent_wins, opponent_plies + 1
            score = (int(winning), -plies if winning else plies)
            scored.append((score, action))
        best = max(score for score, _ in scored)
        return rng.pick([action for score, action in scored if score == best])
    raise ValueError("unsupported player style")


def play(raw_spec, request):
    spec = validate_spec(raw_spec)
    rng = StableRng(request["seed"])
    remaining = list(spec["token_part_ids"])
    active = request["first_seat"]
    previous_action = None
    policy_memory = {style: {} for style in STYLES}
    trace = []
    winner = None
    while remaining and len(trace) < spec["starting_tokens"]:
        legal = legal_actions(spec, remaining)
        before_rng = len(rng.values)
        pre_rng_state = rng.state
        pre_policy_memory = {
            name: dict(visits) for name, visits in policy_memory.items()
        }
        style = request["player_styles"][active]
        action = choose(
            spec, remaining, style, previous_action, policy_memory, rng,
            request["player_styles"][1 - active],
        )
        if action not in legal:
            break
        successor, removed = apply_action(remaining, action)
        trace.append({
            "turn": len(trace),
            "player": active,
            "style": style,
            "pre_remaining_token_part_ids": list(remaining),
            "pre_previous_action": dict(previous_action) if previous_action else None,
            "pre_policy_memory": pre_policy_memory,
            "pre_rng_state": pre_rng_state,
            "legal_actions": list(legal),
            "intended_action": dict(action),
            "action": dict(action),
            "removed_token_part_ids": removed,
            "post_remaining_token_part_ids": successor,
            "post_previous_action": dict(action),
            "post_policy_memory": {
                name: dict(visits) for name, visits in policy_memory.items()
            },
            "post_rng_state": rng.state,
            "rng_values_used": rng.values[before_rng:],
            "terminal": not successor,
        })
        remaining = successor
        previous_action = action
        if not remaining:
            winner = active if spec["last_take_wins"] else 1 - active
            break
        active = 1 - active
    issues = []
    if winner is None:
        issues.append("termination_bound_exceeded")
    return {
        "index": request["index"],
        "seed": request["seed"],
        "player_styles": list(request["player_styles"]),
        "first_seat": request["first_seat"],
        "rule_kind": spec["rule_kind"],
        "completed": winner is not None and not issues,
        "turns": len(trace),
        "actions": trace,
        "restoration_log": (
            [
                {"id": part_id, "sweep": sweep}
                for part_id, sweep in zip(
                    spec["token_part_ids"], spec["token_sweep_values"]
                )
            ]
            if spec["token_sweep_values"]
            else [{"id": part_id} for part_id in spec["token_part_ids"]]
        ),
        "first_action": dict(trace[0]["action"]) if trace else None,
        "outcome": None if winner is None else {
            "winner": winner,
            "loser": 1 - winner,
            "winner_style": request["player_styles"][winner],
            "loser_style": request["player_styles"][1 - winner],
            "winner_score": 1,
            "loser_score": 0,
            "tokens_remaining": len(remaining),
        },
        "rng_values": list(rng.values),
        "rng_state": rng.state,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    rules = json.loads((Path(__file__).resolve().parent / "rules.json").read_text(encoding="utf-8"))
    games = request.get("games")
    seed_strategy = rules.get("seed_strategy")
    if (
        request.get("protocol") != REQUEST_PROTOCOL
        or rules.get("protocol") != RULES_PROTOCOL
        or rules.get("kind") not in RULE_KINDS
        or rules.get("kind") != rules.get("game_spec", {}).get("rule_kind")
        or rules.get("simulator") != {"path": "game/simulate.py", **SIMULATOR}
        or not isinstance(seed_strategy, dict)
        or request.get("seed_strategy") != seed_strategy
        or seed_strategy.get("prng") != "mulberry32"
        or seed_strategy.get("modulus") != 2**32
        or seed_strategy.get("log_every_generated_u32") is not True
        or type(request.get("requested_games")) is not int
        or not 1 <= request["requested_games"] <= 5000
        or not isinstance(games, list)
        or len(games) != request["requested_games"]
    ):
        raise SystemExit("invalid simulation request or rules")
    if seed_strategy.get("kind") == "fixed-index-offset-u32":
        if (
            type(seed_strategy.get("base_seed")) is not int
            or request.get("base_seed") != seed_strategy["base_seed"]
            or request["requested_games"] != seed_strategy.get("requested_games")
        ):
            raise SystemExit("fixed seed strategy mismatch")
    elif seed_strategy.get("kind") != "request-base-index-offset":
        raise SystemExit("unsupported seed strategy")
    validate_spec(rules["game_spec"])
    seen = set()
    for position_index, game in enumerate(games):
        pairing_index = position_index % 16
        expected_styles = [
            STYLE_ORDER[pairing_index // 4],
            STYLE_ORDER[pairing_index % 4],
        ]
        if (
            not isinstance(game, dict)
            or set(game) != {"index", "seed", "player_styles", "first_seat"}
            or type(game["index"]) is not int
            or game["index"] != position_index
            or game["index"] in seen
            or type(game["seed"]) is not int
            or not 0 <= game["seed"] < 2**32
            or game["seed"] != (request["base_seed"] + position_index) % (2**32)
            or not isinstance(game["player_styles"], list)
            or game["player_styles"] != expected_styles
            or game["first_seat"] != position_index % 2
        ):
            raise SystemExit("invalid game request")
        seen.add(game["index"])
    results = [play(rules["game_spec"], game) for game in games]
    output = {
        "protocol": REQUEST_PROTOCOL,
        "simulator": SIMULATOR,
        "source_path": "game/simulate.py",
        "requested_games": request["requested_games"],
        "base_seed": request.get("base_seed"),
        "games": results,
        "completed_games": sum(1 for game in results if game["completed"]),
        "issues": sorted({issue for game in results for issue in game["issues"]}),
    }
    Path(args.output).write_text(
        json.dumps(output, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
'''


__all__ = [
    "FINITE_GAME_RULES_PROTOCOL",
    "FINITE_GAME_RULE_KINDS",
    "FINITE_GAME_SIMULATOR_ID",
    "FINITE_GAME_SIMULATOR_SOURCE",
    "FINITE_GAME_SIMULATOR_VERSION",
    "FINITE_GAME_STYLES",
    "ExecutableGame",
    "GameTrace",
    "LeagueConfig",
    "LeagueReport",
    "PlayerPolicy",
    "RandomPlayer",
    "run_game",
    "run_league",
    "replay_finite_game",
    "validate_finite_game_spec",
]
