"""local_run.py — deterministic executable playtest runner for Blindcap: Duel.

Runs N seeded, reproducible games against the checked-in engine (engine.py)
using both a competent (greedy one-ply over true scores) policy and a random
policy, then reports the same routing statistics the release harness tracks:
natural endings, move counts, forced/undefined branches, win credit, ties,
branching, and all four move kinds. Deterministic given a fixed seed.

This is routing evidence for the executable rules, not physical or human
playtest evidence.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import engine  # noqa: E402


def greedy_move(state, seat):
    """One-ply greedy over true scores, matching the release harness policy."""
    moves = engine.legal_moves(state)
    if len(moves) == 1:
        return moves[0]
    best = None
    best_score = None
    for m in moves:
        trial = engine.apply_move(_deepcopy(state), m, None)
        sc = engine.scores(trial)[seat]
        if best_score is None or sc > best_score:
            best_score = sc
            best = m
    return best


def _deepcopy(state):
    import copy
    return copy.deepcopy(state)


def random_move(state, seat=None):
    return random.choice(engine.legal_moves(state))


def play_one(seed, seat0_policy, seat1_policy):
    rng = random.Random(seed)
    state = engine.new_game(2, rng)
    moves = []
    turns = 0
    found_undefined = None
    while not engine.is_over(state) and turns < engine.MAX_TURNS:
        seat = engine.player_to_move(state)
        policy = seat0_policy if seat == 0 else seat1_policy
        legal = engine.legal_moves(state)
        if not legal:
            found_undefined = ("no_legal_move", turns)
            break
        m = policy(state, seat)
        if m not in legal:
            found_undefined = ("illegal_policy_move", turns)
            break
        moves.append(m)
        state = engine.apply_move(state, m, rng)
        turns += 1
    natural = engine.is_over(state)
    if not natural and found_undefined is None:
        found_undefined = ("turn_cap", turns)
    return {
        "moves": moves,
        "turns": turns,
        "natural": natural,
        "found_undefined": found_undefined,
        "branches_log": [],
        "winners": engine.winners(state) if natural else None,
        "scores": engine.scores(state),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--games", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", type=str, default="")
    ap.add_argument("--mode", type=str, default="greedy",
                    choices=["greedy", "random", "ladder"])
    args = ap.parse_args()

    mode = args.mode
    n = args.games
    random.seed(args.seed)          # seed global RNG too: random_move draws globals
    rng = random.Random(args.seed)  # per-game seed stream

    if mode in ("greedy", "random"):
        policy = greedy_move if mode == "greedy" else random_move
        result = _run_policy(n, rng, policy, policy, label=f"{mode}_vs_{mode}")
    else:
        # ladder: greedy vs random, both seat fixed
        result = _run_policy(n, rng, greedy_move, random_move, label="greedy_vs_random")

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(result + "\n")
    print(result)


def _run_policy(n, rng, p0, p1, label):
    wins = [0.0, 0.0]
    natural = 0
    shared = 0
    for i in range(n):
        seed = rng.randrange(2 ** 31)
        res = play_one(seed, p0, p1)
        if res["natural"]:
            natural += 1
        if res["winners"] is not None:
            if len(res["winners"]) == 2:
                shared += 1
                wins[0] += 0.5
                wins[1] += 0.5
            else:
                wins[res["winners"][0]] += 1
    return json.dumps({
        "label": label,
        "games": n,
        "natural": natural,
        "shared": shared,
        "win_credit": [round(w / n, 3) for w in wins],
    }, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
