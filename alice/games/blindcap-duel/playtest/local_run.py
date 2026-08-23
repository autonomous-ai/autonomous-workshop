"""local_run.py — deterministic executable playtest runner for Blindcap: Duel.

Runs N seeded, reproducible games against the checked-in engine (engine.py)
using both a competent (greedy one-ply over true scores) policy and a random
policy. The rotated ladder alternates which seat receives each policy so its
skill signal is not confounded with a seat effect. The runner records its seed,
natural endings, turn bounds, undefined branches, win credit, shared outcomes,
and all move kinds used; the rotated ladder also separates policy and seat
credit. Deterministic given a fixed seed.

This is routing evidence for the executable rules, not physical or human
playtest evidence.
"""
from __future__ import annotations

import argparse
import json
import random
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
                    choices=["greedy", "random", "ladder", "rotated-ladder"])
    args = ap.parse_args()

    mode = args.mode
    n = args.games
    if n <= 0:
        ap.error("--games must be positive")
    random.seed(args.seed)          # seed global RNG too: random_move draws globals
    rng = random.Random(args.seed)  # per-game seed stream

    if mode in ("greedy", "random"):
        policy = greedy_move if mode == "greedy" else random_move
        result = _run_policy(
            n, rng, policy, policy, label=f"{mode}_vs_{mode}", seed=args.seed
        )
    elif mode == "ladder":
        # ladder: greedy vs random, both seat fixed
        result = _run_policy(
            n, rng, greedy_move, random_move,
            label="greedy_vs_random", seed=args.seed,
        )
    else:
        # Alternate policy seats so the skill signal cannot be mistaken for a
        # seat effect. Keep the legacy fixed-seat ladder for historical
        # evidence compatibility.
        result = _run_rotated_ladder(n, rng, seed=args.seed)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(result + "\n")
    print(result)


def _run_policy(n, rng, p0, p1, label, seed):
    wins = [0.0, 0.0]
    natural = 0
    shared = 0
    turns = []
    undefined = 0
    move_kinds = set()
    for _ in range(n):
        game_seed = rng.randrange(2 ** 31)
        res = play_one(game_seed, p0, p1)
        turns.append(res["turns"])
        undefined += int(res["found_undefined"] is not None)
        move_kinds.update(move[0] for move in res["moves"])
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
        "seed": seed,
        "shared": shared,
        "turns": {"max": max(turns), "min": min(turns)},
        "undefined": undefined,
        "move_kinds_seen": sorted(move_kinds),
        "win_credit": [round(w / n, 3) for w in wins],
    }, indent=2, sort_keys=True)


def _run_rotated_ladder(n, rng, seed):
    seat_wins = [0.0, 0.0]
    policy_wins = {"greedy": 0.0, "random": 0.0}
    greedy_by_seat = {
        "0": {"games": 0, "win_credit": 0.0},
        "1": {"games": 0, "win_credit": 0.0},
    }
    natural = 0
    shared = 0
    turns = []
    undefined = 0
    move_kinds = set()

    for i in range(n):
        greedy_seat = i % 2
        p0, p1 = ((greedy_move, random_move) if greedy_seat == 0
                  else (random_move, greedy_move))
        res = play_one(rng.randrange(2 ** 31), p0, p1)
        turns.append(res["turns"])
        undefined += int(res["found_undefined"] is not None)
        move_kinds.update(move[0] for move in res["moves"])
        if res["natural"]:
            natural += 1
        greedy_by_seat[str(greedy_seat)]["games"] += 1
        if res["winners"] is not None:
            if len(res["winners"]) == 2:
                shared += 1
                seat_wins[0] += 0.5
                seat_wins[1] += 0.5
                policy_wins["greedy"] += 0.5
                policy_wins["random"] += 0.5
                greedy_by_seat[str(greedy_seat)]["win_credit"] += 0.5
            else:
                winner = res["winners"][0]
                seat_wins[winner] += 1
                policy = "greedy" if winner == greedy_seat else "random"
                policy_wins[policy] += 1
                if policy == "greedy":
                    greedy_by_seat[str(greedy_seat)]["win_credit"] += 1

    for seat in ("0", "1"):
        bucket = greedy_by_seat[seat]
        bucket["win_credit"] = (round(bucket["win_credit"] / bucket["games"], 3)
                                if bucket["games"] else None)

    return json.dumps({
        "games": n,
        "greedy_by_seat": greedy_by_seat,
        "label": "greedy_vs_random_rotated",
        "natural": natural,
        "seed": seed,
        "policy_win_credit": {
            policy: round(wins / n, 3) for policy, wins in policy_wins.items()
        },
        "seat_win_credit": [round(w / n, 3) for w in seat_wins],
        "shared": shared,
        "turns": {"max": max(turns), "min": min(turns)},
        "undefined": undefined,
        "move_kinds_seen": sorted(move_kinds),
    }, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
