"""Scripted engine for Shed and Shuttle — implements rules.md, not a neutral model.

Turn (rules.md §3): (1) pull the loaded bar, load any OTHER bar (letter must
differ from the one just pulled) at notch 1 or notch 2 -> a new set of open
lanes; (2) if any open lane still has an empty slot, place a tile there
(mandatory choice among open+non-full lanes); otherwise discard one tile
unplaced (shut out, §3.3). Game ends when every player has taken 8 turns
(each starts with 8 tiles - rules.md §5). Scoring is per-lane majority with
lowest-slot tie-break (§6).

Bot policy: greedy heuristic, not random. For each of the 14 legal sheds
(7 other bars x 2 notches) it scores the best lane it could weave into this
turn (rewarding sole majority, penalizing being behind, and weighting
scarcer/fuller lanes higher since locking in a majority late is worth more)
and takes the best shed+lane combo. This models real deliberate play well
enough to measure balance, ending, decisiveness and closeness.
"""
from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass


@dataclass
class FunEvidence:
    source: str
    games_played: int
    first_seat_wins: float
    ends: bool
    decisiveness: float
    ask_to_play_again: float
    note: str = ""

    @property
    def fun(self) -> bool:
        if self.source not in ("llm_table", "human"):
            return False
        if not self.ends:
            return False
        if self.first_seat_wins >= 0.60:
            return False
        return self.ask_to_play_again > 0


BAR_PROFILES = {
    "A": "OXXOXXOXOXXOX",
    "B": "XOXOXOXXOXOXX",
    "C": "OOXXOXXOXXOOX",
    "D": "XXOXOXOOXOXXO",
    "E": "OXOXXOXOXOXXO",
    "F": "XOOXXOOXXOXOX",
    "G": "OXXXOOXXOXOXO",
    "H": "XXOOXOXOOXXOX",
}
LANE_VALUES = [3, 1, 4, 2, 5, 1, 2, 4, 1, 3, 5, 2]  # lanes 1..12
N_LANES = 12
TILES_PER_PLAYER = 8


def open_lanes(bar_letter: str, notch: int) -> set[int]:
    profile = BAR_PROFILES[bar_letter]
    lanes = set()
    for lane in range(1, N_LANES + 1):
        cell_index = (lane - 1) if notch == 1 else lane
        if profile[cell_index] == "O":
            lanes.add(lane)
    return lanes


def _lane_score(lane_slots: list, player: int, lane_value: int, rng: random.Random) -> float:
    counts = Counter(x for x in lane_slots if x is not None)
    my_after = counts.get(player, 0) + 1
    other_counts = [c for pl, c in counts.items() if pl != player]
    best_other = max(other_counts) if other_counts else 0
    if my_after > best_other:
        control = 1.0
    elif my_after == best_other:
        control = 0.55
    else:
        control = 0.2
    urgency = 1.0 + 0.12 * len(lane_slots)  # fuller lane = locking in matters more
    # Imperfect play: real weavers don't compute the exact optimum every turn.
    # This noise makes trials diverge instead of replaying one fixed line.
    noise = rng.uniform(-0.6, 0.6)
    return lane_value * control * urgency + noise


def _score_lanes(lanes: list, player: int) -> dict:
    return {lane: LANE_VALUES[lane - 1] for lane in range(1, N_LANES + 1)}


def _play_turn(rng: random.Random, lanes: list, current: tuple, player: int) -> tuple:
    """Mutates `lanes`; returns the new (bar_letter, notch) shed."""
    current_bar, _ = current
    candidates = [
        (letter, notch)
        for letter in BAR_PROFILES
        if letter != current_bar
        for notch in (1, 2)
    ]

    best_candidates = []
    best_val = None
    for letter, notch in candidates:
        opens = open_lanes(letter, notch)
        playable = [ln for ln in opens if len(lanes[ln - 1]) < 4]
        if not playable:
            val = -1.0
        else:
            val = max(
                _lane_score(lanes[ln - 1], player, LANE_VALUES[ln - 1], rng)
                for ln in playable
            )
        if best_val is None or val > best_val:
            best_val = val
            best_candidates = [(letter, notch, playable)]
        elif val == best_val:
            best_candidates.append((letter, notch, playable))

    letter, notch, playable = rng.choice(best_candidates)

    if not playable:
        # shut out: discard one tile unplaced, no board change
        return (letter, notch)

    best_lane = max(
        playable,
        key=lambda ln: _lane_score(lanes[ln - 1], player, LANE_VALUES[ln - 1], rng),
    )
    lanes[best_lane - 1].append(player)
    return (letter, notch)


def simulate_game(rng: random.Random, n_players: int) -> dict:
    lanes = [[] for _ in range(N_LANES)]
    current = ("A", 1)  # starting shed; nobody's move, first player replaces it
    tiles_left = [TILES_PER_PLAYER] * n_players

    for _ in range(TILES_PER_PLAYER):
        for p in range(n_players):
            if tiles_left[p] <= 0:
                continue
            before = sum(len(s) for s in lanes)
            current = _play_turn(rng, lanes, current, p)
            after = sum(len(s) for s in lanes)
            tiles_left[p] -= 1
            _ = before, after  # (kept for potential future engagement metrics)

    scores = [0] * n_players
    lanes_won = [0] * n_players
    for lane_idx in range(N_LANES):
        slots = lanes[lane_idx]
        counts = Counter(x for x in slots if x is not None)
        if not counts:
            continue
        top = max(counts.values())
        tied = [pl for pl, c in counts.items() if c == top]
        if len(tied) == 1:
            winner = tied[0]
        else:
            # lowest-slot tie-break: earliest slot index among tied players
            winner = min(tied, key=lambda pl: slots.index(pl))
        scores[winner] += LANE_VALUES[lane_idx]
        lanes_won[winner] += 1

    top_score = max(scores)
    score_leaders = [p for p, s in enumerate(scores) if s == top_score]
    if len(score_leaders) == 1:
        winners = score_leaders
    else:
        top_lanes = max(lanes_won[p] for p in score_leaders)
        winners = [p for p in score_leaders if lanes_won[p] == top_lanes]

    sorted_scores = sorted(scores, reverse=True)
    margin = sorted_scores[0] - (sorted_scores[1] if n_players > 1 else 0)

    return {
        "scores": scores,
        "winners": winners,  # >1 means a shared win
        "margin": margin,
        "tiles_played": sum(len(s) for s in lanes),
    }


def run(trials: int = 4000, seed: int = 0) -> FunEvidence:
    rng = random.Random(seed)
    n_players = 4  # primary config; matches rules.md worked example and idea.json bill

    ends_count = 0
    first_seat_credit = 0.0
    decisive = 0
    close_games = 0

    for _ in range(trials):
        result = simulate_game(rng, n_players)
        ends_count += 1  # every simulated game reaches the fixed turn limit

        winners = result["winners"]
        if 0 in winners:
            first_seat_credit += 1.0 / len(winners)

        decisive_win = len(winners) == 1
        if decisive_win:
            decisive += 1

        # Replay proxy: a nailbiter with a real winner (not a flat shared tie),
        # margin small enough that either side felt it could have gone the
        # other way. A dead 2-4-way tie is the one outcome that tends to leave
        # a table flat rather than eager to reset the board.
        if decisive_win and 1 <= result["margin"] <= 3:
            close_games += 1

    ends = ends_count == trials
    first_seat_wins = first_seat_credit / trials
    decisiveness = decisive / trials
    ask_to_play_again = close_games / trials

    return FunEvidence(
        source="scripted",
        games_played=trials,
        first_seat_wins=first_seat_wins,
        ends=ends,
        decisiveness=decisiveness,
        ask_to_play_again=ask_to_play_again,
        note=(
            f"4-player scripted greedy-heuristic sim over the real bar/notch/shed "
            f"rules; replay proxy = decisive win with margin 1-3 "
            f"({close_games}/{trials} games)."
        ),
    )


if __name__ == "__main__":
    ev = run(trials=4000, seed=0)
    print(ev)
