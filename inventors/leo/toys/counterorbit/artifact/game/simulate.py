#!/usr/bin/env python3
"""Seeded executable simulation for the exact Counterorbit rules."""
from __future__ import annotations
import argparse
import json
import random

STYLES = ("optimizing", "social", "exploratory", "adversarial")

def wedge_cells(inner_index, offset):
    return inner_index, (2 * inner_index - offset) % 10, (2 * inner_index + 1 - offset) % 10

def wedge_counts(inner, outer, player, offset):
    counts = []
    for station in range(5):
        i, left, right = wedge_cells(station, offset)
        counts.append(sum((inner[i] == player, outer[left] == player, outer[right] == player)))
    return counts

def has_wedge(inner, outer, player, offset):
    return max(wedge_counts(inner, outer, player, offset)) == 3

def actions(inner, outer):
    empty = [("inner", index) for index, value in enumerate(inner) if value < 0]
    empty += [("outer", index) for index, value in enumerate(outer) if value < 0]
    return [(where, index, turn) for where, index in empty for turn in (-1, 1)]

def apply(inner, outer, offset, player, action):
    next_inner, next_outer = inner[:], outer[:]
    where, index, turn = action
    (next_inner if where == "inner" else next_outer)[index] = player
    return next_inner, next_outer, (offset + turn) % 10

def value(inner, outer, offset, player, action, style):
    ni, no, new_offset = apply(inner, outer, offset, player, action)
    opponent = 1 - player
    mine = wedge_counts(ni, no, player, new_offset)
    theirs = wedge_counts(ni, no, opponent, new_offset)
    if max(mine) == 3:
        return 10_000.0
    if style == "adversarial":
        return -80.0 * max(theirs) - 9.0 * sum(value == 2 for value in theirs) + max(mine)
    if style == "social":
        # Still tries to win, but favors developing several legible plans over
        # collapsing the position into a single forced threat.
        return 16.0 * max(mine) + 6.0 * sum(value == 2 for value in mine) - 10.0 * max(theirs)
    return 32.0 * max(mine) + 9.0 * sum(value == 2 for value in mine) - 25.0 * max(theirs)

def choose(inner, outer, offset, player, style, rng):
    possible = actions(inner, outer)
    if style == "exploratory":
        return rng.choice(possible)
    scored = [(value(inner, outer, offset, player, action, style), action) for action in possible]
    best = max(score for score, _ in scored)
    candidates = [action for score, action in scored if score == best]
    return rng.choice(candidates)

def final_score(inner, outer, player, offset):
    counts = wedge_counts(inner, outer, player, offset)
    return max(counts), sum(value == 2 for value in counts)

def play(style_a, style_b, seed, first_player):
    rng = random.Random(seed)
    inner, outer, offset = [-1] * 5, [-1] * 10, 0
    styles = (style_a, style_b)
    player = first_player
    trace = []
    for turn_number in range(1, 11):
        action = choose(inner, outer, offset, player, styles[player], rng)
        inner, outer, offset = apply(inner, outer, offset, player, action)
        trace.append({"turn": turn_number, "player": player, "action": list(action), "offset": offset})
        if has_wedge(inner, outer, player, offset):
            return {"winner": player, "turns": turn_number, "trace": trace}
        player = 1 - player
    score_a, score_b = final_score(inner, outer, 0, offset), final_score(inner, outer, 1, offset)
    winner = 0 if score_a > score_b else 1 if score_b > score_a else None
    return {"winner": winner, "turns": 10, "trace": trace}

def simulate(games, seed):
    rng = random.Random(seed)
    stats = {"A": 0, "B": 0, "draw": 0}
    first_seat = {"wins": 0, "games": 0}
    matchups = {}
    max_turns = 0
    samples = []
    for game_index in range(games):
        style_a = STYLES[(game_index // len(STYLES)) % len(STYLES)]
        style_b = STYLES[game_index % len(STYLES)]
        first = game_index % 2
        game_seed = rng.randrange(0, 2**63)
        result = play(style_a, style_b, game_seed, first)
        winner = result["winner"]
        stats["draw" if winner is None else "A" if winner == 0 else "B"] += 1
        first_seat["games"] += 1
        if winner == first:
            first_seat["wins"] += 1
        key = style_a + "-vs-" + style_b
        item = matchups.setdefault(key, {"games": 0, "A_wins": 0, "B_wins": 0, "draws": 0})
        item["games"] += 1
        item["draws" if winner is None else "A_wins" if winner == 0 else "B_wins"] += 1
        max_turns = max(max_turns, result["turns"])
        if len(samples) < 4:
            samples.append({"styles": [style_a, style_b], "seed": game_seed, **result})
    return {
        "schema_version": 1,
        "game": "Counterorbit",
        "evidence_class": "ai-simulation",
        "executable": True,
        "seed": seed,
        "requested_games": games,
        "completed_games": games,
        "terminated_games": games,
        "nonterminating_games": 0,
        "maximum_rules_turns": 10,
        "max_turns_observed": max_turns,
        "player_styles": list(STYLES),
        "outcomes": stats,
        "first_seat_win_rate": round(first_seat["wins"] / first_seat["games"], 6),
        "matchups": matchups,
        "sample_traces": samples,
        "claim_scope": "executability and digital strategy probe only; not evidence of fun or human replay demand",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=1200)
    parser.add_argument("--seed", type=int, default=260823)
    parser.add_argument("--output")
    args = parser.parse_args()
    if args.games < 1000:
        parser.error("showcase evidence requires at least 1000 games")
    result = simulate(args.games, args.seed)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as stream:
            stream.write(payload)
    print(payload, end="")

if __name__ == "__main__":
    main()
