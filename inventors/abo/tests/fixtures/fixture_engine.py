"""An executable model of Notchline's rules, and nothing more.

This is what ABO's Make compiles: a standalone file that imports nothing from
the harness that drives it, exposes the seven calls and three declarations the
simulation contract requires, and translates the sealed rules without adding
one of its own. It is a fixture so the declared checks can run with no model
configured — a real run's engine is written by the rules engineer against the
game that round actually invented.

Where the rules are silent it does the one thing Make permits: it declares the
reading it took, naming the rule, the question, the reading chosen and the
alternative, so the simulation can play the game both ways and report whether
the reading changed the outcome.
"""

from __future__ import annotations

import copy

SIDE = 5
CELLS = SIDE * SIDE

PLAYERS = (2, 2)
MAX_TURNS = 40
HIDDEN_INFO = False

MOVE_KINDS = ("seat_pillar", "spend_lock")
ADMIN_KINDS = ()

# Notch counts, which are the ranks a player reads off the piece itself.
RANKS = {"pillar_low": 1, "pillar_high": 3}
RESERVE = {"pillar_low": 6, "pillar_high": 6, "marker_lock": 2}

ASSUMPTIONS = [
    {
        "id": "locked-socket-counts",
        "rule": "win[1]",
        "question": (
            "The win step totals the notch counts along a run, and separately "
            "breaks a tie by the lock markers in that run. It does not say "
            "whether a locked socket also contributes more to the total."
        ),
        "chosen": (
            "A lock marker changes nothing about the total; it seals the socket "
            "and breaks ties, and that is all."
        ),
        "alternative": (
            "A locked socket counts its notches twice, so spending a marker is "
            "a scoring move as well as a sealing one."
        ),
    },
]


# Which reading of each declared assumption is in force. The simulation flips
# these to play the game both ways and report whether the reading mattered; a
# declaration the engine does not actually honour is a declaration nothing can
# exercise.
CHOICES = {"locked-socket-counts": "chosen"}


class Undefined(Exception):
    """The rules do not cover this position.

    Matched by name rather than by identity, so this file needs no import back
    into the harness that runs it.
    """


# ---------------------------------------------------------------------------
# The state
# ---------------------------------------------------------------------------


def new_game(n_players, rng):
    if int(n_players) != 2:
        raise Undefined("the rules describe a two-seat game, not %r" % n_players)
    return {
        "board": [None] * CELLS,
        "locked": [False] * CELLS,
        "reserve": [dict(RESERVE) for _ in range(2)],
        "to_move": 0,
        "turns": 0,
    }


def player_to_move(state):
    return int(state["to_move"])


def legal_moves(state):
    seat = player_to_move(state)
    reserve = state["reserve"][seat]
    moves = []
    for cell in range(CELLS):
        if state["board"][cell] is None:
            for piece in ("pillar_low", "pillar_high"):
                if reserve[piece] > 0:
                    moves.append(("seat_pillar", cell, piece))
    if reserve["marker_lock"] > 0:
        for cell in range(CELLS):
            occupant = state["board"][cell]
            if occupant is not None and occupant[0] == seat and not state["locked"][cell]:
                moves.append(("spend_lock", cell))
    return moves


def apply_move(state, move, rng):
    seat = player_to_move(state)
    kind = move[0]
    after = copy.deepcopy(state)
    if kind == "seat_pillar":
        _kind, cell, piece = move
        if after["board"][cell] is not None:
            raise Undefined("a pillar was seated into an occupied socket")
        if after["reserve"][seat][piece] <= 0:
            raise Undefined("a pillar was seated from an empty reserve")
        after["board"][cell] = (seat, RANKS[piece])
        after["reserve"][seat][piece] -= 1
    elif kind == "spend_lock":
        _kind, cell = move
        occupant = after["board"][cell]
        if occupant is None or occupant[0] != seat:
            raise Undefined("a lock marker was spent into a socket the seat does not hold")
        if after["locked"][cell]:
            raise Undefined("a lock marker was spent into an already locked socket")
        if after["reserve"][seat]["marker_lock"] <= 0:
            raise Undefined("a lock marker was spent from an empty reserve")
        after["locked"][cell] = True
        after["reserve"][seat]["marker_lock"] -= 1
    else:
        # The engine never invents a rule to make an unfamiliar move work.
        raise Undefined("the rules define no move of kind %r" % (kind,))
    after["to_move"] = 1 - seat
    after["turns"] += 1
    return after


def is_over(state):
    if all(cell is not None for cell in state["board"]):
        return True
    return not legal_moves(state)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

# Rows and columns. "Straight run of adjacent sockets" is what the win step
# says, and a diagonal is not a straight run of *adjacent* sockets on a grid
# whose sockets meet edge to edge.
def _lines():
    for row in range(SIDE):
        yield [row * SIDE + column for column in range(SIDE)]
    for column in range(SIDE):
        yield [row * SIDE + column for row in range(SIDE)]


def _best_run(state, seat):
    """The seat's best never-descending run: (total notches, locks in it).

    See ASSUMPTIONS["locked-socket-counts"]. Under the chosen reading a lock
    marker seals a socket and breaks ties and does nothing to the total; under
    the alternative a locked socket counts its notches twice.
    """

    doubles = CHOICES.get("locked-socket-counts") == "alternative"
    best = (0, 0)
    for line in _lines():
        for start in range(SIDE):
            total = locks = 0
            previous = None
            for index in range(start, SIDE):
                cell = line[index]
                occupant = state["board"][cell]
                if occupant is None or occupant[0] != seat:
                    break
                if previous is not None and occupant[1] < previous:
                    break
                previous = occupant[1]
                locked = state["locked"][cell]
                total += occupant[1] * (2 if (locked and doubles) else 1)
                locks += 1 if locked else 0
                if (total, locks) > best:
                    best = (total, locks)
    return best


def scores(state):
    return [_best_run(state, seat)[0] for seat in range(2)]


def winners(state):
    ranked = [_best_run(state, seat) for seat in range(2)]
    best = max(ranked)
    return [seat for seat in range(2) if ranked[seat] == best]


# ---------------------------------------------------------------------------
# What a seat may see
# ---------------------------------------------------------------------------


def observation(state, seat):
    """Everything, because the game declares no hidden information.

    Kept so the harness can render a position for a model seat, and so the
    declaration that there is nothing to hide can be checked against play
    rather than taken on the engine's word.
    """

    return {
        "seat": int(seat),
        "board": [None if cell is None else list(cell) for cell in state["board"]],
        "locked": list(state["locked"]),
        "reserve": [dict(item) for item in state["reserve"]],
        "to_move": player_to_move(state),
        "turns": state["turns"],
    }
