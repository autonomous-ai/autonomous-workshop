"""engine.py — deep-claim, an executable model of idea.json. Not a game to play."""
import random   # only if you need it; the rng is always passed in


class Undefined(Exception):
    """The rules do not say."""


SLUG = "deep-claim"
PLAYERS = (2, 4)
MAX_TURNS = 200
MOVE_KINDS = ("place_large", "place_small", "pass")
HIDDEN_INFO = False

ASSUMPTIONS = [
    {"id": "floor_burial",
     "rule": "rules:turn[2]",
     "question": "A large puck seals a bore whose floor was already claimed: "
                 "'that bore's floor chamber becomes permanently unreachable "
                 "for the rest of the game, whether or not it was already "
                 "claimed.' rules:win then scores 'every shelf and floor "
                 "chamber marked with their own studs', with no exception "
                 "for a since-sealed floor. Does the earlier floor claim go "
                 "on scoring for whoever set it (the shelf and floor are two "
                 "separately-owned, separately-scored slots that just happen "
                 "to share a bore), or does sealing the shelf bury the floor "
                 "claim itself so it no longer scores for anyone (making a "
                 "large puck a 2-point denial move against whichever rival "
                 "holds that floor, on top of its own 1-point claim)?",
     "chosen": "the floor claim keeps scoring for its original owner; "
               "sealing the shelf only makes the floor chamber unreachable "
               "for future placement, not unscored",
     "alternative": "sealing the shelf buries the floor claim too; it stops "
                    "scoring for anyone from that point on"},
]
CHOICES = {"floor_burial": "chosen"}

N_BORES = 6
LARGE_START = 3
SMALL_START = 3
SHELF_POINTS = 1.0
FLOOR_POINTS = 2.0


def new_game(n_players, rng):
    return {
        "n_players": n_players,
        # one entry per bore: shelf/floor hold the owning seat once claimed,
        # or None. A bore is sealed iff shelf is not None. floor_buried is
        # only ever set under the floor_burial "alternative" reading, when a
        # large puck seals a shelf over a floor someone had already claimed.
        "bores": [{"shelf": None, "floor": None, "floor_buried": False}
                  for _ in range(N_BORES)],
        "inventory": [{"large": LARGE_START, "small": SMALL_START}
                      for _ in range(n_players)],
        "turn": 0,
        # "Agree who goes first" is left to the table by the rules; the
        # engine fixes seat 0, and seat bias is exactly what the harness
        # measures on top of that fixed choice.
        "current_seat": 0,
        "consecutive_passes": 0,
    }


def player_to_move(state):
    return state["current_seat"]


def legal_moves(state):
    seat = state["current_seat"]
    inv = state["inventory"][seat]
    moves = []
    if inv["large"] > 0:
        for i, bore in enumerate(state["bores"]):
            if bore["shelf"] is None:
                moves.append(("place_large", i))
    if inv["small"] > 0:
        for i, bore in enumerate(state["bores"]):
            if bore["shelf"] is None and bore["floor"] is None:
                moves.append(("place_small", i))
    if not moves:
        return [("pass",)]
    return moves


def apply_move(state, move, rng):
    seat = state["current_seat"]
    kind = move[0]
    if kind == "place_large":
        i = move[1]
        bore = state["bores"][i]
        bore["shelf"] = seat
        if CHOICES.get("floor_burial") == "alternative" and bore["floor"] is not None:
            bore["floor_buried"] = True
        state["inventory"][seat]["large"] -= 1
        state["consecutive_passes"] = 0
    elif kind == "place_small":
        i = move[1]
        state["bores"][i]["floor"] = seat
        state["inventory"][seat]["small"] -= 1
        state["consecutive_passes"] = 0
    elif kind == "pass":
        state["consecutive_passes"] += 1
    else:
        raise ValueError(f"unknown move kind {kind!r}")
    state["turn"] += 1
    state["current_seat"] = (seat + 1) % state["n_players"]
    return state


def is_over(state):
    if all(bore["shelf"] is not None for bore in state["bores"]):
        return True
    if state["consecutive_passes"] >= state["n_players"]:
        return True
    return False


def scores(state):
    totals = [0.0] * state["n_players"]
    for bore in state["bores"]:
        if bore["shelf"] is not None:
            totals[bore["shelf"]] += SHELF_POINTS
        if bore["floor"] is not None and not bore["floor_buried"]:
            totals[bore["floor"]] += FLOOR_POINTS
    return totals


def winners(state):
    s = scores(state)
    top = max(s)
    return [i for i, v in enumerate(s) if v == top]
