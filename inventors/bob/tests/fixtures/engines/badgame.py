"""Reference engine: a game the gates must FAIL — the known-broken anchor.

First mover always wins, deterministically. Every turn offers three "moves"
that all do exactly the same thing (advance the mover by 1), and the game
ends the instant anyone reaches the target — no round completion, so seat 0
crosses the line first, every game, under every policy. This is Deep Claim
distilled: the defect the seat-bias gate exists to catch (MAX_SEAT_EDGE),
and because choices carry zero information, no policy can beat any other —
the skill ladder must come back flat (skill_ladder_ok False).

Branching is 3 on purpose: this fixture must fail on SEAT BIAS and SKILL,
not trip the branching floor first (a test that fails for the wrong reason
proves nothing).
"""

IDEA_SHA = "BADGAME-FIXTURE"

ASSUMPTIONS = [
    "All three moves are intentionally identical; the game is a turn counter "
    "wearing a board-game costume.",
]

_TARGET = 7


def new_game(n_players, seed):
    if n_players < 2:
        raise ValueError("badgame needs at least 2 players")
    return {"n": n_players, "pos": [0] * n_players, "to_move": 0,
            "over": False, "winners": []}


def player_to_move(state):
    return state["to_move"]


def legal_moves(state):
    if state["over"]:
        return []
    return [0, 1, 2]


def apply(state, move):
    if state["over"]:
        raise ValueError("game is over — no more moves")
    pos = list(state["pos"])
    pos[state["to_move"]] += 1  # the move index is ignored: fake choice
    over = pos[state["to_move"]] >= _TARGET
    return {
        "n": state["n"],
        "pos": pos,
        "to_move": (state["to_move"] + 1) % state["n"],
        "over": over,
        "winners": [state["to_move"]] if over else [],
    }


def is_over(state):
    return state["over"]


def winners(state):
    return list(state["winners"])


def scores(state):
    return [float(p) for p in state["pos"]]


def observation(state, seat):
    return "You are seat %d. Positions: %s. Target: %d." % (
        seat, state["pos"], _TARGET)
