"""Workshop-owned executable rules for newly invented tabletop games.

The Invent worker may choose a game only inside this deliberately bounded
language.  Make is allowed to design the physical expression of those rules;
it is never allowed to replace them with a different game.  The canonical
Invent lane-contract bytes are consequently usable as the single rules input
to Make, the pinned simulator, Playtest, and the release gate.

Version 1 covers deterministic, perfect-information, alternate-turn,
two-player resource games.  An action removes fixed quantities from one or
more shared resources and may award points.  Play ends when all resources are
empty; the winner is the last actor, the next actor, or the highest scorer
with a deterministic actor-based tie break.  It intentionally does not model
boards or spatial movement, hidden information, chance, simultaneous turns,
negotiation, trading, dexterity, or more than two players.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import deque
from typing import Any, Dict, Mapping, Sequence, Tuple

from .errors import ContractError


GAME_LANE_CONTRACT_SCHEMA_VERSION = 2
GAME_PROTOCOL = "workshop.resource-game.v1"
GAME_SIMULATION_PROTOCOL = "workshop-seeded-games-v2"
GAME_SIMULATOR_ID = "workshop-resource-game"
GAME_SIMULATOR_VERSION = "2.0.0"
GAME_CONTRACT_PATH = "game/invent-lane-contract.json"
GAME_RULES_PATH = "game/rules.json"
GAME_SIMULATOR_PATH = "game/simulate.py"
GAME_STYLES = ("optimizing", "social", "exploratory", "adversarial")
GAME_STYLE_PAIRINGS = (
    ("optimizing", "social"),
    ("exploratory", "adversarial"),
    ("optimizing", "adversarial"),
    ("social", "exploratory"),
)
GAME_MINIMUM_COMPLETE_GAMES = 1_000
GAME_MAXIMUM_COMPLETE_GAMES = 5_000
GAME_ANALYSIS_CRITERIA = {
    "outcome_coverage": "Both seats and all four fixed player styles must win at least one seeded game; this is digital outcome coverage, not a human-fun or perfect-fairness claim.",
    "exploits": "Every game containing the adversarial policy is an exploit case; any simulator issue is a failure.",
    "strategy": "A choice case is only a replayed turn with at least two legal actions; the league must contain at least one such branching decision.",
    "flow": "Every requested seed must terminate with no issue.",
}

_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_WINNERS = frozenset(("last-actor", "next-actor", "highest-score"))
_TIE_BREAKERS = frozenset(("last-actor", "next-actor"))


def game_lane_contract_schema() -> Dict[str, Any]:
    """Return the strict structured-output schema used by shared Invent."""

    text = {"type": "string", "minLength": 1, "maxLength": 500}
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema_version",
            "lane",
            "game_protocol",
            "simulation_gate",
        ],
        "properties": {
            "schema_version": {
                "type": "integer",
                "const": GAME_LANE_CONTRACT_SCHEMA_VERSION,
            },
            "lane": {"type": "string", "const": "invented-games"},
            "game_protocol": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "schema_version",
                    "protocol",
                    "players",
                    "resources",
                    "actions",
                    "ending",
                ],
                "properties": {
                    "schema_version": {"type": "integer", "const": 1},
                    "protocol": {"type": "string", "const": GAME_PROTOCOL},
                    "players": {"type": "integer", "const": 2},
                    "resources": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 4,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["resource_id", "label", "initial"],
                            "properties": {
                                "resource_id": {"type": "string"},
                                "label": text,
                                "initial": {
                                    "type": "integer",
                                    "minimum": 1,
                                    "maximum": 10,
                                },
                            },
                        },
                    },
                    "actions": {
                        "type": "array",
                        "minItems": 2,
                        "maxItems": 24,
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["action_id", "label", "removals", "points"],
                            "properties": {
                                "action_id": {"type": "string"},
                                "label": text,
                                "removals": {
                                    "type": "array",
                                    "minItems": 1,
                                    "maxItems": 4,
                                    "items": {
                                        "type": "object",
                                        "additionalProperties": False,
                                        "required": ["resource_id", "count"],
                                        "properties": {
                                            "resource_id": {"type": "string"},
                                            "count": {
                                                "type": "integer",
                                                "minimum": 1,
                                                "maximum": 10,
                                            },
                                        },
                                    },
                                },
                                "points": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "maximum": 100,
                                },
                            },
                        },
                    },
                    "ending": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["condition", "winner", "score_tie_break"],
                        "properties": {
                            "condition": {
                                "type": "string",
                                "const": "all-resources-empty",
                            },
                            "winner": {
                                "type": "string",
                                "enum": sorted(_WINNERS),
                            },
                            "score_tie_break": {
                                "type": "string",
                                "enum": sorted(_TIE_BREAKERS),
                            },
                        },
                    },
                },
            },
            "simulation_gate": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "minimum_complete_games",
                    "fixed_seed_strategy",
                    "player_policies",
                ],
                "properties": {
                    "minimum_complete_games": {
                        "type": "integer",
                        "const": 1_000,
                    },
                    "fixed_seed_strategy": {
                        "type": "string",
                        "const": "artifact-sha256-plus-index",
                    },
                    "player_policies": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 4,
                        "items": {"type": "string", "enum": list(GAME_STYLES)},
                    },
                },
            },
        },
    }


def canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        raise ContractError("invented-game rules must be finite canonical JSON") from exc


def json_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def game_simulation_plan(
    content_sha256: str,
    game_count: int = GAME_MINIMUM_COMPLETE_GAMES,
) -> Mapping[str, Any]:
    """Return the one pinned consecutive-seed/style plan for exact content.

    Release supplies the Made artifact digest.  Invent qualification supplies
    the accepted lane-contract digest.  The field name remains
    ``artifact_sha256`` for the established seeded-games-v2 wire contract; the
    qualification receipt labels that value as an Invent-contract binding.
    """

    if (
        not isinstance(content_sha256, str)
        or len(content_sha256) != 64
        or any(character not in "0123456789abcdef" for character in content_sha256)
    ):
        raise ContractError("game simulation plan requires a lowercase SHA-256")
    if (
        type(game_count) is not int
        or not GAME_MINIMUM_COMPLETE_GAMES
        <= game_count
        <= GAME_MAXIMUM_COMPLETE_GAMES
    ):
        raise ContractError("game simulation plan requires 1,000 to 5,000 games")
    base_seed = int(content_sha256[:8], 16) % (2**31 - game_count)
    return {
        "protocol": GAME_SIMULATION_PROTOCOL,
        "artifact_sha256": content_sha256,
        "requested_games": game_count,
        "base_seed": base_seed,
        "games": [
            {
                "index": index,
                "seed": base_seed + index,
                "player_styles": list(
                    GAME_STYLE_PAIRINGS[index % len(GAME_STYLE_PAIRINGS)]
                ),
            }
            for index in range(game_count)
        ],
    }


def _exact(value: Any, fields: Sequence[str], label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != set(fields):
        raise ContractError("%s fields are invalid" % label)
    return value


def _identifier(value: Any, label: str) -> str:
    if not isinstance(value, str) or len(value) > 64 or _ID.fullmatch(value) is None:
        raise ContractError("%s must be a bounded kebab-case identifier" % label)
    return value


def _label(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 500
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ContractError("%s must be bounded non-empty text" % label)
    return value


def _legal_action(action: Mapping[str, Any], state: Tuple[int, ...], ids: Tuple[str, ...]) -> bool:
    positions = {resource_id: index for index, resource_id in enumerate(ids)}
    return all(
        state[positions[removal["resource_id"]]] >= removal["count"]
        for removal in action["removals"]
    )


def _next_state(
    action: Mapping[str, Any], state: Tuple[int, ...], ids: Tuple[str, ...]
) -> Tuple[int, ...]:
    positions = {resource_id: index for index, resource_id in enumerate(ids)}
    result = list(state)
    for removal in action["removals"]:
        result[positions[removal["resource_id"]]] -= removal["count"]
    return tuple(result)


def validate_game_protocol(value: Any) -> Mapping[str, Any]:
    """Validate the executable DSL and exhaustively prove bounded progress.

    Every reachable nonterminal resource state must have a legal action.  Every
    action strictly reduces the finite sum of resources, so that check proves
    that play cannot deadlock or loop and must end within the initial token
    count.  The small physical-state bound keeps exhaustive replay cheap.
    """

    protocol = _exact(
        value,
        ("schema_version", "protocol", "players", "resources", "actions", "ending"),
        "invented-game protocol",
    )
    if (
        protocol["schema_version"] != 1
        or type(protocol["schema_version"]) is not int
        or protocol["protocol"] != GAME_PROTOCOL
        or protocol["players"] != 2
        or type(protocol["players"]) is not int
    ):
        raise ContractError("invented-game protocol identity is invalid")

    resources = protocol["resources"]
    if not isinstance(resources, list) or not 1 <= len(resources) <= 4:
        raise ContractError("invented-game protocol needs one to four resources")
    resource_ids = []
    initial = []
    for raw in resources:
        resource = _exact(raw, ("resource_id", "label", "initial"), "game resource")
        resource_ids.append(_identifier(resource["resource_id"], "resource id"))
        _label(resource["label"], "resource label")
        count = resource["initial"]
        if type(count) is not int or not 1 <= count <= 10:
            raise ContractError("resource initial count must be from 1 to 10")
        initial.append(count)
    if len(resource_ids) != len(set(resource_ids)):
        raise ContractError("invented-game resource ids must be unique")
    if not 2 <= sum(initial) <= 12:
        raise ContractError("invented-game physical resources must total 2 to 12 pieces")

    actions = protocol["actions"]
    if not isinstance(actions, list) or not 2 <= len(actions) <= 24:
        raise ContractError("invented-game protocol needs two to 24 actions")
    action_ids = []
    semantics = []
    used_resources = set()
    normalized_actions = []
    for raw in actions:
        action = _exact(raw, ("action_id", "label", "removals", "points"), "game action")
        action_ids.append(_identifier(action["action_id"], "action id"))
        _label(action["label"], "action label")
        removals = action["removals"]
        if not isinstance(removals, list) or not 1 <= len(removals) <= len(resource_ids):
            raise ContractError("game action removals are invalid")
        seen = set()
        normalized_removals = []
        for raw_removal in removals:
            removal = _exact(raw_removal, ("resource_id", "count"), "game removal")
            resource_id = _identifier(removal["resource_id"], "removal resource id")
            count = removal["count"]
            if (
                resource_id not in resource_ids
                or resource_id in seen
                or type(count) is not int
                or not 1 <= count <= initial[resource_ids.index(resource_id)]
            ):
                raise ContractError("game action removal is not bound to a resource")
            seen.add(resource_id)
            used_resources.add(resource_id)
            normalized_removals.append((resource_id, count))
        points = action["points"]
        if type(points) is not int or not 0 <= points <= 100:
            raise ContractError("game action points must be an integer from 0 to 100")
        semantic = (tuple(sorted(normalized_removals)), points)
        semantics.append(semantic)
        normalized_actions.append(action)
    if len(action_ids) != len(set(action_ids)):
        raise ContractError("invented-game action ids must be unique")
    if len(semantics) != len(set(semantics)):
        raise ContractError("invented-game actions must have distinct executable effects")
    if used_resources != set(resource_ids):
        raise ContractError("every game resource must participate in an action")

    ending = _exact(
        protocol["ending"],
        ("condition", "winner", "score_tie_break"),
        "game ending",
    )
    if (
        ending["condition"] != "all-resources-empty"
        or ending["winner"] not in _WINNERS
        or ending["score_tie_break"] not in _TIE_BREAKERS
    ):
        raise ContractError("invented-game ending is outside the executable protocol")

    ids = tuple(resource_ids)
    start = tuple(initial)
    queue = deque((start,))
    visited = {start}
    executable_actions = set()
    while queue:
        state = queue.popleft()
        if not any(state):
            continue
        legal = [action for action in normalized_actions if _legal_action(action, state, ids)]
        if not legal:
            raise ContractError("invented-game protocol has a reachable dead state")
        for action in legal:
            executable_actions.add(action["action_id"])
            successor = _next_state(action, state, ids)
            if sum(successor) >= sum(state) or min(successor) < 0:
                raise ContractError("invented-game action does not make bounded progress")
            if successor not in visited:
                visited.add(successor)
                queue.append(successor)
    if executable_actions != set(action_ids):
        raise ContractError("every invented-game action must be executable from a reachable state")
    return protocol


def validate_game_lane_contract(value: Any) -> Mapping[str, Any]:
    contract = _exact(
        value,
        ("schema_version", "lane", "game_protocol", "simulation_gate"),
        "invented-game lane contract",
    )
    if (
        type(contract["schema_version"]) is not int
        or contract["schema_version"] != GAME_LANE_CONTRACT_SCHEMA_VERSION
        or contract["lane"] != "invented-games"
    ):
        raise ContractError("invented-game lane contract identity is invalid")
    validate_game_protocol(contract["game_protocol"])
    gate = _exact(
        contract["simulation_gate"],
        ("minimum_complete_games", "fixed_seed_strategy", "player_policies"),
        "invented-game simulation gate",
    )
    if (
        gate["minimum_complete_games"] != 1_000
        or type(gate["minimum_complete_games"]) is not int
        or gate["fixed_seed_strategy"] != "artifact-sha256-plus-index"
        or not isinstance(gate["player_policies"], list)
        or tuple(gate["player_policies"]) != GAME_STYLES
    ):
        raise ContractError("invented-game simulation gate is not the fixed Workshop gate")
    return contract


def validate_physical_binding(
    value: Any,
    *,
    lane_contract: Mapping[str, Any],
    part_ids: Sequence[str],
) -> Mapping[str, Any]:
    """Require every protocol resource unit to name one exact printable part."""

    contract = validate_game_lane_contract(lane_contract)
    binding = _exact(value, ("enabled", "resource_part_ids"), "game physical binding")
    if binding["enabled"] is not True or not isinstance(binding["resource_part_ids"], list):
        raise ContractError("invented-game Make must enable its physical binding")
    expected = {
        resource["resource_id"]: resource["initial"]
        for resource in contract["game_protocol"]["resources"]
    }
    observed = {}
    used_parts = []
    for raw in binding["resource_part_ids"]:
        row = _exact(raw, ("resource_id", "part_ids"), "game resource binding")
        resource_id = _identifier(row["resource_id"], "bound resource id")
        bound = row["part_ids"]
        if (
            resource_id in observed
            or resource_id not in expected
            or not isinstance(bound, list)
            or len(bound) != expected[resource_id]
            or not all(isinstance(item, str) and item in part_ids for item in bound)
            or len(bound) != len(set(bound))
        ):
            raise ContractError("game resource binding does not match its Invent count")
        observed[resource_id] = tuple(bound)
        used_parts.extend(bound)
    if set(observed) != set(expected) or len(used_parts) != len(set(used_parts)):
        raise ContractError("game physical binding must cover every resource exactly once")
    return binding


class _StableGameRng:
    def __init__(self, seed: int) -> None:
        self.state = seed & ((1 << 64) - 1)

    def pick(self, values: Sequence[Mapping[str, Any]]) -> Mapping[str, Any]:
        self.state = (
            6364136223846793005 * self.state + 1442695040888963407
        ) & ((1 << 64) - 1)
        return values[self.state % len(values)]


def _resource_dict(protocol: Mapping[str, Any]) -> Dict[str, int]:
    return {
        resource["resource_id"]: resource["initial"]
        for resource in protocol["resources"]
    }


def _legal_actions_for_resources(
    protocol: Mapping[str, Any], resources: Mapping[str, int]
) -> list[Mapping[str, Any]]:
    return [
        action
        for action in protocol["actions"]
        if all(
            resources[removal["resource_id"]] >= removal["count"]
            for removal in action["removals"]
        )
    ]


def _removal_total(action: Mapping[str, Any]) -> int:
    return sum(removal["count"] for removal in action["removals"])


def _choose_game_action(
    style: str,
    legal: Sequence[Mapping[str, Any]],
    resources: Mapping[str, int],
    ending: Mapping[str, Any],
    rng: _StableGameRng,
) -> Mapping[str, Any]:
    candidates = list(legal)
    terminal = [
        action
        for action in candidates
        if sum(resources.values()) == _removal_total(action)
    ]
    if terminal and ending["winner"] == "last-actor":
        candidates = terminal
    elif (
        terminal
        and ending["winner"] == "next-actor"
        and len(terminal) < len(candidates)
    ):
        candidates = [action for action in candidates if action not in terminal]
    if style == "exploratory":
        return rng.pick(candidates)
    if style == "social":
        return min(
            candidates,
            key=lambda action: (
                _removal_total(action),
                action["points"],
                action["action_id"],
            ),
        )
    if style == "adversarial":
        return max(
            candidates,
            key=lambda action: (
                _removal_total(action),
                action["points"],
                action["action_id"],
            ),
        )
    return max(
        candidates,
        key=lambda action: (
            action["points"],
            _removal_total(action),
            action["action_id"],
        ),
    )


def _winner_for(
    ending: Mapping[str, Any], actor: int, scores: Sequence[int]
) -> int:
    if ending["winner"] == "last-actor":
        return actor
    if ending["winner"] == "next-actor":
        return 1 - actor
    if scores[0] != scores[1]:
        return 0 if scores[0] > scores[1] else 1
    return actor if ending["score_tie_break"] == "last-actor" else 1 - actor


def _trace_details(
    protocol: Mapping[str, Any],
    trace_value: Any,
    *,
    player_styles: Sequence[str],
) -> Mapping[str, Any]:
    if (
        isinstance(trace_value, (str, bytes, Mapping))
        or not isinstance(trace_value, Sequence)
        or not trace_value
    ):
        raise ContractError("invented-game action trace must be a non-empty sequence")
    if (
        isinstance(player_styles, (str, bytes, Mapping))
        or not isinstance(player_styles, Sequence)
        or len(player_styles) != 2
        or any(style not in GAME_STYLES for style in player_styles)
    ):
        raise ContractError("invented-game trace player styles are invalid")
    resources = _resource_dict(protocol)
    scores = [0, 0]
    actions = {action["action_id"]: action for action in protocol["actions"]}
    actor = None
    meaningful_choices = 0
    forced_turns = 0
    bound = sum(resources.values())
    if len(trace_value) > bound:
        raise ContractError("invented-game trace exceeds its proven turn bound")
    for turn, raw in enumerate(trace_value):
        player = turn % 2
        legal = _legal_actions_for_resources(protocol, resources)
        if len(legal) >= 2:
            meaningful_choices += 1
        else:
            forced_turns += 1
        action = actions.get(raw) if isinstance(raw, str) else None
        if action is None:
            raise ContractError("invented-game trace turn is not the deterministic state")
        if action not in legal:
            raise ContractError("invented-game trace contains an illegal action")
        for removal in action["removals"]:
            resources[removal["resource_id"]] -= removal["count"]
        scores[player] += action["points"]
        actor = player
        if not any(resources.values()) and turn != len(trace_value) - 1:
            raise ContractError("invented-game trace continued after its terminal state")
    if actor is None or any(resources.values()):
        raise ContractError("invented-game trace did not reach its terminal state")
    winner = _winner_for(protocol["ending"], actor, scores)
    return {
        "outcome": {
            "winner": winner,
            "winner_style": player_styles[winner],
            "scores": {"0": scores[0], "1": scores[1]},
            "resources": resources,
        },
        "meaningful_choices": meaningful_choices,
        "forced_turns": forced_turns,
    }


def replay_action_trace(
    protocol_value: Any,
    trace_value: Any,
    *,
    player_styles: Sequence[str],
) -> Mapping[str, Any]:
    """Independently replay one trace and return its exact terminal outcome."""

    protocol = validate_game_protocol(protocol_value)
    return _trace_details(
        protocol, trace_value, player_styles=player_styles
    )["outcome"]


def game_trace_choice_counts(
    protocol_value: Any,
    trace_value: Any,
    *,
    player_styles: Sequence[str],
) -> Mapping[str, int]:
    """Count actual branching decisions separately from forced turns."""

    protocol = validate_game_protocol(protocol_value)
    details = _trace_details(protocol, trace_value, player_styles=player_styles)
    return {
        "meaningful_choices": details["meaningful_choices"],
        "forced_turns": details["forced_turns"],
    }


def simulate_game_protocol(
    protocol_value: Any, request_value: Any
) -> Mapping[str, Any]:
    """Run one request with the exact seeded-games-v2 interpreter policy."""

    protocol = validate_game_protocol(protocol_value)
    request = _exact(
        request_value,
        ("index", "seed", "player_styles"),
        "seeded game request",
    )
    index = request["index"]
    seed = request["seed"]
    styles = request["player_styles"]
    if (
        type(index) is not int
        or index < 0
        or type(seed) is not int
        or seed < 0
        or not isinstance(styles, list)
        or len(styles) != 2
        or any(style not in GAME_STYLES for style in styles)
    ):
        raise ContractError("seeded game request is invalid")
    resources = _resource_dict(protocol)
    scores = [0, 0]
    rng = _StableGameRng(seed)
    trace = []
    issues = []
    actor = None
    bound = sum(resources.values())
    for turn in range(bound):
        if not any(resources.values()):
            break
        player = turn % 2
        legal = _legal_actions_for_resources(protocol, resources)
        if not legal:
            issues.append("reachable_dead_state")
            break
        action = _choose_game_action(
            styles[player], legal, resources, protocol["ending"], rng
        )
        for removal in action["removals"]:
            resources[removal["resource_id"]] -= removal["count"]
        scores[player] += action["points"]
        actor = player
        trace.append(action["action_id"])
    completed = actor is not None and not any(resources.values()) and not issues
    if not completed and not issues:
        issues.append("termination_bound_exceeded")
    winner = _winner_for(protocol["ending"], actor, scores) if completed else None
    outcome = (
        None
        if winner is None
        else {
            "winner": winner,
            "winner_style": styles[winner],
            "scores": {"0": scores[0], "1": scores[1]},
            "resources": resources,
        }
    )
    return {
        "index": index,
        "seed": seed,
        "player_styles": list(styles),
        "completed": completed,
        "turns": len(trace),
        "action_trace": trace,
        "action_trace_sha256": json_sha256(trace),
        "outcome": outcome,
        "issues": issues,
    }


def game_trace_analysis(
    protocol_value: Any,
    games: Sequence[Mapping[str, Any]],
    *,
    requested_games: int,
) -> Mapping[str, Any]:
    """Recompute release counters and modest digital strategy coverage."""

    protocol = validate_game_protocol(protocol_value)
    if (
        isinstance(games, (str, bytes, Mapping))
        or not isinstance(games, Sequence)
        or type(requested_games) is not int
        or requested_games != len(games)
    ):
        raise ContractError("game analysis requires every requested trace")
    completed = 0
    seat_wins = {0: 0, 1: 0}
    style_wins = {style: 0 for style in GAME_STYLES}
    adversarial_games = 0
    meaningful_choices = 0
    forced_turns = 0
    issue_count = 0
    for game in games:
        if not isinstance(game, Mapping):
            raise ContractError("game analysis trace is not an object")
        styles = game.get("player_styles")
        trace = game.get("action_trace")
        issues = game.get("issues")
        if (
            not isinstance(styles, list)
            or len(styles) != 2
            or any(style not in GAME_STYLES for style in styles)
            or not isinstance(trace, list)
            or not isinstance(issues, list)
        ):
            raise ContractError("game analysis trace is malformed")
        if "adversarial" in styles:
            adversarial_games += 1
        issue_count += len(issues)
        if game.get("completed") is not True:
            continue
        details = _trace_details(protocol, trace, player_styles=styles)
        observed_outcome = game.get("outcome")
        if isinstance(observed_outcome, str):
            try:
                observed_outcome = json.loads(observed_outcome)
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ContractError("game analysis outcome is invalid") from exc
        if observed_outcome != details["outcome"]:
            raise ContractError("game analysis outcome does not replay")
        completed += 1
        meaningful_choices += details["meaningful_choices"]
        forced_turns += details["forced_turns"]
        winner = observed_outcome["winner"]
        winner_style = observed_outcome["winner_style"]
        seat_wins[winner] += 1
        style_wins[winner_style] += 1
    balance_failure = int(
        completed != requested_games
        or any(wins == 0 for wins in seat_wins.values())
        or any(wins == 0 for wins in style_wins.values())
    )
    measurements = {
        "requested_games": requested_games,
        "completed_games": completed,
        "balance_cases": len(GAME_STYLES),
        "balance_failures": balance_failure,
        "exploit_cases": adversarial_games,
        "exploits_found": issue_count,
        "choice_cases": meaningful_choices,
        "degenerate_choices": int(meaningful_choices == 0),
        "flow_cases": requested_games,
        "flow_failures": requested_games - completed,
    }
    return {
        "seat_wins": {str(seat): wins for seat, wins in seat_wins.items()},
        "style_wins": style_wins,
        "meaningful_choices": meaningful_choices,
        "forced_turns": forced_turns,
        "measurements": measurements,
    }


def qualify_game_lane_contract(
    lane_contract_value: Any,
    *,
    game_count: int = GAME_MINIMUM_COMPLETE_GAMES,
) -> Mapping[str, Any]:
    """Run the deterministic Invent-stage gate before Make sees the rules."""

    contract = validate_game_lane_contract(lane_contract_value)
    contract_sha256 = json_sha256(contract)
    plan = game_simulation_plan(contract_sha256, game_count)
    games = [
        simulate_game_protocol(contract["game_protocol"], request)
        for request in plan["games"]
    ]
    analysis = game_trace_analysis(
        contract["game_protocol"], games, requested_games=game_count
    )
    measurements = analysis["measurements"]
    tensions = []
    if measurements["completed_games"] != game_count:
        tensions.append(
            "The pinned Invent qualification did not complete all 1,000 seeded games."
        )
    missing_seats = [
        seat for seat, wins in analysis["seat_wins"].items() if wins == 0
    ]
    if missing_seats:
        tensions.append(
            "The pinned Invent qualification produced no win from seat %s."
            % ", ".join(missing_seats)
        )
    missing_styles = [
        style for style, wins in analysis["style_wins"].items() if wins == 0
    ]
    if missing_styles:
        tensions.append(
            "The pinned Invent qualification produced no winning outcome for %s."
            % ", ".join(missing_styles)
        )
    if measurements["choice_cases"] == 0:
        tensions.append(
            "The pinned Invent qualification found no turn with two or more legal actions."
        )
    return {
        "schema_version": 1,
        "kind": "workshop-invent-game-qualification",
        "lane_contract_sha256": contract_sha256,
        "simulation_protocol": GAME_SIMULATION_PROTOCOL,
        "simulator": {
            "id": GAME_SIMULATOR_ID,
            "version": GAME_SIMULATOR_VERSION,
            "source_sha256": hashlib.sha256(
                GAME_SIMULATOR_SOURCE.encode("utf-8")
            ).hexdigest(),
        },
        "seed_binding": {
            "kind": "invent-lane-contract",
            "sha256": contract_sha256,
            "base_seed": plan["base_seed"],
            "plan_sha256": json_sha256(plan),
        },
        "requested_games": game_count,
        "completed_games": measurements["completed_games"],
        "seat_wins": analysis["seat_wins"],
        "style_wins": analysis["style_wins"],
        "meaningful_choice_turns": analysis["meaningful_choices"],
        "forced_turns": analysis["forced_turns"],
        "hard_tensions": tensions,
        "passed": not tensions,
    }


def game_rules_document(
    *,
    lane_contract: Mapping[str, Any],
    physical_binding: Mapping[str, Any],
    title: str,
    theme: str,
) -> Dict[str, Any]:
    contract = validate_game_lane_contract(lane_contract)
    protocol = contract["game_protocol"]
    return {
        "schema_version": 2,
        "kind": "workshop-executable-invented-game",
        "title": _label(title, "game title"),
        "theme": _label(theme, "game theme"),
        "invent_lane_contract": {
            "path": GAME_CONTRACT_PATH,
            "sha256": json_sha256(contract),
        },
        "game_protocol_sha256": json_sha256(protocol),
        "game_protocol": dict(protocol),
        "physical_binding": dict(physical_binding),
        "termination_bound_turns": sum(
            resource["initial"] for resource in protocol["resources"]
        ),
        "simulator": {
            "path": GAME_SIMULATOR_PATH,
            "id": GAME_SIMULATOR_ID,
            "version": GAME_SIMULATOR_VERSION,
        },
    }


def game_rules_markdown(rules: Mapping[str, Any]) -> str:
    protocol = validate_game_protocol(rules.get("game_protocol"))
    resources = ", ".join(
        "%d %s" % (resource["initial"], resource["label"])
        for resource in protocol["resources"]
    )
    actions = [
        "- **%s:** remove %s%s."
        % (
            action["label"],
            ", ".join(
                "%d %s"
                % (
                    removal["count"],
                    next(
                        resource["label"]
                        for resource in protocol["resources"]
                        if resource["resource_id"] == removal["resource_id"]
                    ),
                )
                for removal in action["removals"]
            ),
            " and score %d" % action["points"] if action["points"] else "",
        )
        for action in protocol["actions"]
    ]
    winner = {
        "last-actor": "The player who empties the final resource wins.",
        "next-actor": "The player after the one who empties the final resource wins.",
        "highest-score": (
            "The player with the higher score wins; a tied score uses the declared "
            "%s tie break." % protocol["ending"]["score_tie_break"]
        ),
    }[protocol["ending"]["winner"]]
    return "\n".join(
        (
            "# %s" % rules["title"],
            "",
            str(rules["theme"]),
            "",
            "## Players",
            "",
            "Two players alternate turns.",
            "",
            "## Setup",
            "",
            "Place %s in the shared play area." % resources,
            "",
            "## Your turn",
            "",
            *actions,
            "",
            "An action is legal only when every named resource still contains enough pieces.",
            "",
            "## End and winner",
            "",
            "The game ends as soon as every resource is empty. %s" % winner,
            "",
            "## Evidence boundary",
            "",
            "The included Workshop interpreter proves execution and termination for the seeded AI games. It does not prove human enjoyment, physical component quality, or customer experience.",
            "",
        )
    )


# This exact source is sealed into every Made game.  It intentionally imports
# only Python's standard library and interprets JSON data; Make cannot inject
# executable game code.
GAME_SIMULATOR_SOURCE = r'''#!/usr/bin/env python3
"""Pinned deterministic interpreter for Workshop resource-game v1."""

import argparse
import hashlib
import json
from pathlib import Path

REQUEST_PROTOCOL = "workshop-seeded-games-v2"
RULE_PROTOCOL = "workshop.resource-game.v1"
SIMULATOR = {"id": "workshop-resource-game", "version": "2.0.0"}
STYLES = {"optimizing", "social", "exploratory", "adversarial"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


class StableRng:
    def __init__(self, seed):
        self.state = seed & ((1 << 64) - 1)

    def pick(self, values):
        self.state = (6364136223846793005 * self.state + 1442695040888963407) & ((1 << 64) - 1)
        return values[self.state % len(values)]


def legal_actions(protocol, resources):
    result = []
    for action in protocol["actions"]:
        if all(resources[item["resource_id"]] >= item["count"] for item in action["removals"]):
            result.append(action)
    return result


def removal_total(action):
    return sum(item["count"] for item in action["removals"])


def choose(style, legal, resources, ending, rng):
    terminal = [
        action for action in legal
        if sum(resources.values()) == removal_total(action)
    ]
    if terminal and ending["winner"] == "last-actor":
        legal = terminal
    elif terminal and ending["winner"] == "next-actor" and len(terminal) < len(legal):
        legal = [action for action in legal if action not in terminal]
    if style == "exploratory":
        return rng.pick(legal)
    if style == "social":
        key = lambda action: (removal_total(action), action["points"], action["action_id"])
        return min(legal, key=key)
    if style == "adversarial":
        key = lambda action: (removal_total(action), action["points"], action["action_id"])
        return max(legal, key=key)
    key = lambda action: (action["points"], removal_total(action), action["action_id"])
    return max(legal, key=key)


def winner_for(ending, actor, scores):
    if ending["winner"] == "last-actor":
        return actor
    if ending["winner"] == "next-actor":
        return 1 - actor
    if scores[0] != scores[1]:
        return 0 if scores[0] > scores[1] else 1
    return actor if ending["score_tie_break"] == "last-actor" else 1 - actor


def play(protocol, request):
    resources = {item["resource_id"]: item["initial"] for item in protocol["resources"]}
    scores = [0, 0]
    styles = request["player_styles"]
    rng = StableRng(request["seed"])
    trace = []
    issues = []
    actor = None
    bound = sum(resources.values())
    for turn in range(bound):
        if not any(resources.values()):
            break
        player = turn % 2
        legal = legal_actions(protocol, resources)
        if not legal:
            issues.append("reachable_dead_state")
            break
        action = choose(styles[player], legal, resources, protocol["ending"], rng)
        for removal in action["removals"]:
            resources[removal["resource_id"]] -= removal["count"]
        scores[player] += action["points"]
        actor = player
        trace.append(action["action_id"])
    completed = actor is not None and not any(resources.values()) and not issues
    if not completed and not issues:
        issues.append("termination_bound_exceeded")
    winner = winner_for(protocol["ending"], actor, scores) if completed else None
    outcome = None if winner is None else {
        "winner": winner,
        "winner_style": styles[winner],
        "scores": {"0": scores[0], "1": scores[1]},
        "resources": resources,
    }
    return {
        "index": request["index"],
        "seed": request["seed"],
        "player_styles": styles,
        "completed": completed,
        "turns": len(trace),
        "action_trace": trace,
        "action_trace_sha256": hashlib.sha256(canonical(trace)).hexdigest(),
        "outcome": outcome,
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    root = Path(__file__).resolve().parent
    contract_bytes = (root / "invent-lane-contract.json").read_bytes()
    contract = json.loads(contract_bytes.decode("utf-8"))
    protocol = contract["game_protocol"]
    games = request.get("games")
    if (
        request.get("protocol") != REQUEST_PROTOCOL
        or protocol.get("protocol") != RULE_PROTOCOL
        or protocol.get("players") != 2
        or type(request.get("requested_games")) is not int
        or not 1 <= request["requested_games"] <= 5000
        or not isinstance(games, list)
        or len(games) != request["requested_games"]
    ):
        raise SystemExit("invalid simulation request or rules")
    seen = set()
    for game in games:
        if (
            not isinstance(game, dict)
            or set(game) != {"index", "seed", "player_styles"}
            or type(game["index"]) is not int
            or game["index"] in seen
            or type(game["seed"]) is not int
            or not isinstance(game["player_styles"], list)
            or len(game["player_styles"]) != 2
            or any(style not in STYLES for style in game["player_styles"])
        ):
            raise SystemExit("invalid game request")
        seen.add(game["index"])
    results = [play(protocol, game) for game in games]
    output = {
        "protocol": REQUEST_PROTOCOL,
        "simulator": SIMULATOR,
        "source_path": "game/simulate.py",
        "contract_path": "game/invent-lane-contract.json",
        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
        "game_protocol_sha256": hashlib.sha256(canonical(protocol)).hexdigest(),
        "requested_games": request["requested_games"],
        "base_seed": request.get("base_seed"),
        "games": results,
        "completed_games": sum(1 for game in results if game["completed"]),
        "issues": sorted({issue for game in results for issue in game["issues"]}),
    }
    Path(args.output).write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
'''


__all__ = [
    "GAME_CONTRACT_PATH",
    "GAME_ANALYSIS_CRITERIA",
    "GAME_LANE_CONTRACT_SCHEMA_VERSION",
    "GAME_MAXIMUM_COMPLETE_GAMES",
    "GAME_MINIMUM_COMPLETE_GAMES",
    "GAME_PROTOCOL",
    "GAME_RULES_PATH",
    "GAME_SIMULATION_PROTOCOL",
    "GAME_SIMULATOR_ID",
    "GAME_SIMULATOR_PATH",
    "GAME_SIMULATOR_SOURCE",
    "GAME_SIMULATOR_VERSION",
    "GAME_STYLE_PAIRINGS",
    "GAME_STYLES",
    "canonical_json_bytes",
    "game_lane_contract_schema",
    "game_rules_document",
    "game_rules_markdown",
    "game_simulation_plan",
    "game_trace_analysis",
    "game_trace_choice_counts",
    "json_sha256",
    "qualify_game_lane_contract",
    "replay_action_trace",
    "simulate_game_protocol",
    "validate_game_lane_contract",
    "validate_game_protocol",
    "validate_physical_binding",
]
