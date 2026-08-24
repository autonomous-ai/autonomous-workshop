"""Reference engine: a game the gates must PASS — the known-good anchor.

Pick-a-lane blocking race with payout surges. Each turn the mover picks one
of three lanes and advances by that lane's current payout — usually 2 or 3,
but one roll in eight is an 8-step SURGE (payouts are a pure function of
(seed, turn, lane), so a 2-ply player can see next turn's board). The lane
the mover picks is worth 0 on the very next turn — so a move both scores
points and denies the opponent a lane. That denial is the skill gradient by
construction: greedy grabs its own best payout and blocks a lane at random
in effect; lookahead1 will take a 3 instead of a spare 2 point, or even
sacrifice a point, to zero out an opponent surge it can see coming. Measured
edges (4,000-game batches): greedy beats random ~0.95, lookahead1 beats
greedy ~0.70-0.75 — a clean monotone staircase.

Fairness: rounds complete before the end is checked (equal turns for every
seat) and a tie at the finish line goes to the LATER seat — a half-komi
that pays back the first mover's tempo. Measured 2p seat winrates at every
rung: within 0.01 of 50/50. The fixture is tuned fair at n=2 (its anchor
duty); at 3+ the flat half-komi overcorrects, so gate tests run it at 2p.

Why these shapes: branching is exactly 3 every turn (meets
MIN_MEDIAN_BRANCHING = 3.0 with zero forced moves), ties are impossible at
the finish (decisiveness 1.0), and payouts >= 2 on unblocked lanes mean the
race always terminates far below any move cap (completion 1.0).
"""

IDEA_SHA = "GOODGAME-FIXTURE"

ASSUMPTIONS = [
    "Payout rolls are a pure function of (seed, turn); players may 'know' "
    "future rolls — this stands in for open information, not hidden dice.",
    "A tie at or past the target goes to the later seat (half-komi); a "
    "draw only happens at the round-cap lid, which normal play never hits.",
]

_LANES = 3

# Mostly-flat payouts with a rare surge: the 8 is what makes denial worth a
# sacrifice, which is what separates lookahead1 from greedy (the staircase
# this fixture exists to exhibit). Odds: 3/8 pay 2, 4/8 pay 3, 1/8 pay 8.
_PAYOUTS = (2, 2, 2, 3, 3, 3, 3, 8)
_TARGET = 30
# Hard round lid so the engine ALWAYS terminates even under pathological
# play; simmetrics' 4x-median cap normally fires long before this.
_MAX_ROUNDS = 200


def _mix(seed, turn, lane):
    """Deterministic per-(seed,turn,lane) value — a tiny xorshift-style hash
    so payouts vary game to game without carrying an RNG object in state."""
    x = (seed * 2654435761 + turn * 97003 + lane * 8191 + 0x9E3779B9) & 0xFFFFFFFF
    x ^= x >> 13
    x = (x * 1274126177) & 0xFFFFFFFF
    x ^= x >> 16
    return x


def _lane_values(state):
    values = [_PAYOUTS[_mix(state["seed"], state["turn"], lane) % len(_PAYOUTS)]
              for lane in range(_LANES)]
    if state["blocked"] is not None:
        values[state["blocked"]] = 0
    return values


def new_game(n_players, seed):
    if not 2 <= n_players <= 4:
        raise ValueError("goodgame supports 2-4 players")
    return {
        "n": n_players,
        "pos": [0] * n_players,
        "to_move": 0,
        "turn": 0,
        # Seat 0 starts blocked too (a seed-picked lane), so the first turn
        # is not uniquely privileged with three live lanes.
        "blocked": _mix(seed, 999983, 0) % _LANES,
        "seed": seed,
        "over": False,
        "winners": [],
    }


def player_to_move(state):
    return state["to_move"]


def legal_moves(state):
    if state["over"]:
        return []
    return list(range(_LANES))  # the 0-value lane stays pickable: a real
    # (bad) option, keeping branching at 3 rather than forcing to 2.


def apply(state, move):
    if state["over"]:
        raise ValueError("game is over — no more moves")
    if move not in (0, 1, 2):
        raise ValueError("move must be a lane index 0..2")
    gain = _lane_values(state)[move]
    pos = list(state["pos"])
    pos[state["to_move"]] += gain
    nxt = {
        "n": state["n"],
        "pos": pos,
        "to_move": (state["to_move"] + 1) % state["n"],
        "turn": state["turn"] + 1,
        "blocked": move,
        "seed": state["seed"],
        "over": False,
        "winners": [],
    }
    if nxt["to_move"] == 0:  # end of a full round: everyone has moved
        top = max(pos)
        if top >= _TARGET:
            leaders = [i for i, p in enumerate(pos) if p == top]
            nxt["over"] = True
            # Tie at the line -> LATER seat wins: a half-komi repaying the
            # first mover's tempo (measured: centers 2p seats on 50/50).
            nxt["winners"] = leaders if len(leaders) == 1 else [max(leaders)]
        elif nxt["turn"] >= _MAX_ROUNDS * state["n"]:
            top = max(pos)
            nxt["over"] = True
            nxt["winners"] = [i for i, p in enumerate(pos) if p == top]
    return nxt


def is_over(state):
    return state["over"]


def winners(state):
    return list(state["winners"])


def scores(state):
    return [float(p) for p in state["pos"]]


def observation(state, seat):
    return ("You are seat %d. Positions: %s. Target: %d. Lane payouts this "
            "turn: %s (lane %s pays 0 — just used)."
            % (seat, state["pos"], _TARGET, _lane_values(state),
               state["blocked"]))
