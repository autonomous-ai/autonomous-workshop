"""engine.py — millbind, an executable model of idea.json. Not a game to play."""
from __future__ import annotations

import random  # only used via the rng argument playtest.py passes in


class Undefined(Exception):
    """The rules do not say."""


SLUG = "millbind"
PLAYERS = (2, 4)
MAX_TURNS = 200
# The rework deleted POWER, so the only actions are PLACE, SHIFT and PASS,
# plus the two setup moves the rules define (the first player seating the
# fixed crank at setup[4], and the millstone snake at setup[5]).
MOVE_KINDS = ("setup_crank", "setup_mill", "place", "shift", "pass")
HIDDEN_INFO = False    # the whole yard, the supply pile and every score are open

# The second rework settled the only assumption the first rework had left:
# rules:turn[5] now states plainly that a binding PLACE or SHIFT IS a legal
# move, offered like any other, that is resolved by reverting and wasting the
# turn. There is no longer an "illegal / not offered" reading to play both
# ways, so ASSUMPTIONS/CHOICES are removed and the engine implements only the
# one reading. rules:end[1] A STALLED MILL guarantees termination (tracked via
# state["round_active"] below).
ASSUMPTIONS = []
CHOICES = {}


# ---------------------------------------------------------------------------
# Board geometry: 37 pins on a triangular lattice — centre, ring of 6, ring
# of 12, ring of 18 — addressed with cube/axial hex coordinates (q, r),
# s = -q - r, ring = max(|q|, |r|, |s|). The six standard axial neighbour
# offsets are exactly the six nearest-neighbour directions of a triangular
# lattice at unit spacing, which is what the 30mm pin spacing is, so "hex
# distance 1" and "physically 30mm apart, meshable if teeth match" are the
# same relation. Only the outer ring (ring == 3, 18 pins) is a yard pin.
# ---------------------------------------------------------------------------

def _gen_pins():
    pins = []
    for q in range(-3, 4):
        for r in range(-3, 4):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= 3:
                pins.append((q, r))
    return pins


def _ring(p):
    q, r = p
    s = -q - r
    return max(abs(q), abs(r), abs(s))


PIN_LIST = _gen_pins()
assert len(PIN_LIST) == 37, f"lattice should hold 37 pins, built {len(PIN_LIST)}"
YARD_PINS = [p for p in PIN_LIST if _ring(p) == 3]
INNER_PINS = [p for p in PIN_LIST if _ring(p) < 3]
assert len(YARD_PINS) == 18 and len(INNER_PINS) == 19

_PIN_SET = set(PIN_LIST)
_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)]
NEIGHBORS = {}
for _p in PIN_LIST:
    _q, _r = _p
    NEIGHBORS[_p] = [c for c in ((_q + dq, _r + dr) for dq, dr in _DIRS)
                     if c in _PIN_SET]

EDGES = []
_seen = set()
for _p, _nbrs in NEIGHBORS.items():
    for _q in _nbrs:
        e = (_p, _q) if _p < _q else (_q, _p)
        if e not in _seen:
            _seen.add(e)
            EDGES.append(e)


# ---------------------------------------------------------------------------
# MESHING (rules:turn[0]) and TEST FOR A BIND (rules:turn[5]): the bind test
# is a whole-graph odd-cycle check, subject to the two tooth tiers. gear_low
# meshes only with gear_low, gear_high only with gear_high; gear_tandem, a
# millstone and the crank_gear are full-height and mesh with anything on a
# neighbouring pin. "Neighbouring" is the lattice adjacency above.
#
# The grind's distance-to-crank reward also falls out of this graph: the
# payout for a millstone is the number of gears on the SHORTEST running chain
# back to the crank (turn[7]), which is a BFS over the same mesh adjacency.
# ---------------------------------------------------------------------------

def _tier(piece):
    t = piece["type"]
    if t == "gear_low":
        return "low"
    if t == "gear_high":
        return "high"
    return "full"   # gear_tandem, mill, crank


def _meshes(a, b):
    ta, tb = _tier(a), _tier(b)
    return ta == "full" or tb == "full" or ta == tb


def _build_adj(pins):
    adj = {p: [] for p in PIN_LIST if pins[p] is not None}
    for p, q in EDGES:
        pp, pq = pins[p], pins[q]
        if pp is not None and pq is not None and _meshes(pp, pq):
            adj[p].append(q)
            adj[q].append(p)
    return adj


def _analyze_graph(adj):
    """2-colour every component; a colour clash anywhere is an odd cycle —
    the whole yard is bound, exactly the physical fact the rules describe.
    Returns (colour, component_id, bound)."""
    color, comp = {}, {}
    bound = False
    cid = 0
    for start in adj:
        if start in color:
            continue
        color[start] = 0
        comp[start] = cid
        stack = [start]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if v not in color:
                    color[v] = color[u] ^ 1
                    comp[v] = cid
                    stack.append(v)
                elif color[v] == color[u]:
                    bound = True
        cid += 1
    return color, comp, bound


def _is_bound_state(state) -> bool:
    _, _, bound = _analyze_graph(_build_adj(state["pins"]))
    return bound


def _would_bind(pins, overrides):
    """Slow reference bind test: apply `overrides` to a COPY of `pins` (pin ->
    None or a piece dict) and report whether that trial layout is bound,
    without mutating `pins`. Full re-analysis; kept for apply-side checks."""
    trial = dict(pins)
    trial.update(overrides)
    _, _, bound = _analyze_graph(_build_adj(trial))
    return bound


def _add_binds(pins, p, tier, color, comp):
    """Fast incremental bind test for ADDING one piece of `tier` at empty pin
    `p` to an already-unbound layout whose 2-coloring (`color`, `comp`) is
    given. Equivalent to re-running the full odd-cycle check: standing a piece
    at p adds edges from p to its tier-compatible occupied neighbours, and that
    creates an odd cycle iff two such neighbours already lie in the same
    component on OPPOSITE colours (the path between them has odd length, and
    the two edges through p close an odd loop). O(deg^2) per candidate instead
    of a full BFS, which is what keeps legal_moves fast on the lookahead path.
    Used only when CHOICES["bind_illegal"] == "chosen"."""
    nbrs = []
    for q in NEIGHBORS[p]:
        piece = pins.get(q)
        if piece is None or q not in comp:
            continue
        tq = _tier(piece)
        if not (tq == "full" or tier == "full" or tq == tier):
            continue
        nbrs.append(q)
    for i in range(len(nbrs)):
        for j in range(i):
            a, b = nbrs[i], nbrs[j]
            if comp[a] == comp[b] and color[a] != color[b]:
                return True
    return False


# ---------------------------------------------------------------------------
# Setup (rules:setup[4..5]). setup[4]: the first player stands the crank on
# any empty yard pin — THE CRANK IS THEN FIXED FOR THE WHOLE GAME, no rule
# ever moves it, so there is no POWER phase anywhere after this. setup[5]:
# the millstones are seated in a snake, the LAST player first and moving
# clockwise to the FIRST player, so the seat that acts last in the round gets
# to see where the power sits before siting its own mill. Both are real moves,
# not baked into new_game, because "any empty yard pin" is a strategic choice.
#
# Neither setup placement can ever bind: only full-height pieces (the crank,
# then the millstones) stand on yard pins during setup, no supply gear exists
# yet to add a chord, and the 18 yard pins form a single bipartite 18-cycle.
# So setup asserts the geometry rather than test-then-reverting, exactly as
# the pre-rework engine did.
# ---------------------------------------------------------------------------

def _enter_round(state, start_player):
    n = state["n_players"]
    state["start_player"] = start_player
    state["action_order"] = [(start_player + i) % n for i in range(n)]
    state["action_index"] = 0
    state["phase"] = "actions"
    # rules:end[1] A STALLED MILL: whether this round changed the machine or
    # paid any pellet. Reset at the top of every round; set by a successful
    # PLACE, a successful SHIFT, or any grind pay; if it is still False when
    # the grind has run, the round is stalled and the game ends.
    state["round_active"] = False


def new_game(n_players, rng):
    if n_players < PLAYERS[0] or n_players > PLAYERS[1]:
        raise ValueError(f"millbind seats {PLAYERS[0]}-{PLAYERS[1]}, "
                         f"not {n_players}")
    # setup[5]'s snake: last player first, then clockwise to first.
    setup_order = [(n_players - 1 + i) % n_players for i in range(n_players)]
    return {
        "n_players": n_players,
        "pins": {p: None for p in PIN_LIST},
        "supply": {"gear_low": 14, "gear_high": 7, "gear_tandem": 3},
        "pellets": 28,
        "spindles": [0] * n_players,
        "start_player": 0,          # "choose a first player any way you like"
        "phase": "setup_crank",
        "crank_pin": None,
        "mill_pin": [None] * n_players,
        "setup_order": setup_order,
        "setup_index": 0,
        "action_order": [],
        "action_index": 0,
        "last_grind_cw": [],
        "round": 0,
        "game_over": False,
    }


def player_to_move(state):
    phase = state["phase"]
    if phase == "setup_crank":
        return state["start_player"]          # setup[4]: the first player
    if phase == "setup_mill":
        return state["setup_order"][state["setup_index"]]
    if phase == "actions":
        return state["action_order"][state["action_index"]]
    raise RuntimeError(f"no player to move in phase {phase!r}")


# ---------------------------------------------------------------------------
# legal_moves — pure, no mutation
# ---------------------------------------------------------------------------

def legal_moves(state):
    phase = state["phase"]
    pins = state["pins"]

    if phase == "setup_crank":
        # setup[4]: the first player stands the crank on any empty yard pin.
        return [("setup_crank", p) for p in YARD_PINS if pins[p] is None]

    if phase == "setup_mill":
        return [("setup_mill", p) for p in YARD_PINS if pins[p] is None]

    if phase == "actions":
        seat = state["action_order"][state["action_index"]]
        moves = [("pass",)]
        # rules:turn[5] (second rework, settled): a binding PLACE or SHIFT is
        # still offered as a legal move; apply_move tests it, reverts it and
        # wastes the turn. So every empty pin with a supply gear is offerable
        # (binding or not), and every empty yard pin but the mill's own is a
        # shift. This is the reading the rules now state outright.
        for gtype, cnt in state["supply"].items():
            if cnt > 0:
                for p in PIN_LIST:
                    if pins[p] is None:
                        moves.append(("place", p, gtype))
        own_pin = state["mill_pin"][seat]
        for p in YARD_PINS:
            if pins[p] is None and p != own_pin:
                moves.append(("shift", p))
        return moves

    return []   # phase == "over"


# ---------------------------------------------------------------------------
# apply_move — may mutate, must return the state
# ---------------------------------------------------------------------------

def _advance_action(state):
    state["action_index"] += 1
    if state["action_index"] >= state["n_players"]:
        _process_grind(state)


def apply_move(state, move, rng):
    kind = move[0]

    if kind == "setup_crank":
        pin = move[1]
        state["pins"][pin] = {"type": "crank"}
        state["crank_pin"] = pin
        assert not _is_bound_state(state), (
            "rules:setup[4]: setup produced a bound yard, which the "
            "eighteen-pin yard ring should make geometrically impossible"
        )
        state["phase"] = "setup_mill"
        return state

    if kind == "setup_mill":
        seat = state["setup_order"][state["setup_index"]]
        pin = move[1]
        state["pins"][pin] = {"type": "mill", "owner": seat}
        state["mill_pin"][seat] = pin
        assert not _is_bound_state(state), (
            "rules:setup[5]: setup produced a bound yard, which the "
            "eighteen-pin yard ring should make geometrically impossible"
        )
        state["setup_index"] += 1
        if state["setup_index"] >= state["n_players"]:
            _enter_round(state, state["start_player"])
        return state

    if kind == "place":
        _, pin, gtype = move
        state["pins"][pin] = {"type": gtype}
        state["supply"][gtype] -= 1
        # rules:turn[5] TEST FOR A BIND (second rework, settled): a binding
        # place was offered; it reverts and wastes the turn. A place that does
        # not bind comes to rest, and counts as changing the machine for the
        # rules:end[1] stalled-round check.
        if _is_bound_state(state):
            state["pins"][pin] = None
            state["supply"][gtype] += 1
        else:
            state["round_active"] = True
        _advance_action(state)
        return state

    if kind == "shift":
        seat = state["action_order"][state["action_index"]]
        _, new_pin = move
        old_pin = state["mill_pin"][seat]
        piece = state["pins"][old_pin]
        state["pins"][old_pin] = None
        state["pins"][new_pin] = piece
        state["mill_pin"][seat] = new_pin
        # rules:turn[5] TEST FOR A BIND — same settled reading as place.
        if _is_bound_state(state):
            state["pins"][new_pin] = None
            state["pins"][old_pin] = piece
            state["mill_pin"][seat] = old_pin
        else:
            state["round_active"] = True
        _advance_action(state)
        return state

    if kind == "pass":
        _advance_action(state)
        return state

    raise ValueError(f"millbind engine does not know move kind {kind!r}")


# ---------------------------------------------------------------------------
# THE GRIND (rules:turn[7]), DIRECTION (turn[8]) and A SHORT GRANARY (turn[9])
# ---------------------------------------------------------------------------

def _process_grind(state):
    adj = _build_adj(state["pins"])
    _, _, bound = _analyze_graph(adj)
    if bound:
        # rules:turn[7]: every PLACE/SHIFT was bind-tested and reverted before
        # it took effect, so a bound yard reaching THE GRIND is an engine bug,
        # not the physical "undo this round's moves" clause, which exists for a
        # human table that skipped a test and cannot happen in this engine.
        raise AssertionError(
            "rules:turn[7]: THE GRIND reached a bound yard although every "
            "move this round was bind-tested before taking effect; this "
            "indicates an engine bug, not a remaining rules gap."
        )

    # BFS shortest mesh distance from the fixed crank to every piece.
    crank = state["crank_pin"]
    front = [crank]
    dist = {crank: 0}
    for u in front:
        for v in adj.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                front.append(v)

    # rules:turn[7]/[8]: a millstone grinds clockwise iff an ODD number of
    # gears stands between it and the crank on the SHORTEST chain (an even
    # count or disconnection turns it dead), and it pays ONE pellet per gear
    # of that shortest drive. Number of gears between = (edge count - 1).
    n = state["n_players"]
    cw_seats = []
    debts = {}
    for seat in range(n):
        mp = state["mill_pin"][seat]
        if mp is None or mp not in dist:
            continue
        gears_between = dist[mp] - 1
        if gears_between % 2 == 1:
            cw_seats.append(seat)
            debts[seat] = gears_between

    # rules:turn[9] A SHORT GRANARY: hand pellets out one at a time, beginning
    # with the start player and going clockwise, to each owner still owed,
    # repeating until every debt is paid or the bin is empty. Any debt the
    # empty bin cannot cover is never paid.
    payout_order = [s for s in state["action_order"] if s in debts]
    pellets = state["pellets"]
    while pellets > 0 and payout_order and any(debts[s] > 0 for s in payout_order):
        for seat in payout_order:
            if pellets == 0:
                break
            if debts[seat] > 0:
                debts[seat] -= 1
                pellets -= 1
                state["spindles"][seat] += 1
    if pellets < state["pellets"]:
        state["round_active"] = True      # this round's grind paid a pellet
    state["pellets"] = pellets
    state["last_grind_cw"] = list(cw_seats)

    # rules:end[0]: end at the end of the round in which the last gear leaves
    # the supply, or in which the granary_bin is emptied. Passing draws nothing
    # from either, so it can never reach the end. There is no "no gear placed"
    # end and no way for passing to end or win the game.
    supply_empty = all(v == 0 for v in state["supply"].values())
    # rules:end[1] A STALLED MILL (drain variant): a round in which no gear
    # came to rest on a new pin, no millstone shifted to a new pin and the
    # grind paid no pellet at all has seized for that round and pays a one-
    # pellet maintenance toll from the granary (discarded, to no one). The
    # granary stays the un-stallable clock: an inert round either drains the
    # last pellet (ending the game) or moves the granary a pellet closer to
    # empty, so the board can never park on a permanent pass/bind loop, and
    # the game is not cut off at a near-even score by an early seizure.
    if not state["round_active"] and state["pellets"] > 0:
        state["pellets"] -= 1
    state["round"] += 1
    if supply_empty or state["pellets"] == 0:
        state["game_over"] = True
        state["phase"] = "over"
    else:
        # rules:turn[10]: pass the start player role one seat clockwise; the
        # crank still does not move.
        _enter_round(state, (state["start_player"] + 1) % n)


# ---------------------------------------------------------------------------
# Termination, score, win (rules:win)
# ---------------------------------------------------------------------------

def is_over(state):
    return bool(state["game_over"])


def scores(state):
    return [float(v) for v in state["spindles"]]


def winners(state):
    spindles = state["spindles"]
    top = max(spindles)
    tied = [i for i, v in enumerate(spindles) if v == top]
    if len(tied) == 1:
        return tied
    # rules:win: among the level stacks, the win goes to the tied player whose
    # millstone turned clockwise on the final grind; if that still does not
    # separate them, they share the win.
    cw = set(state.get("last_grind_cw", []))
    tied_cw = [i for i in tied if i in cw]
    if len(tied_cw) == 1:
        return tied_cw
    return tied_cw if len(tied_cw) > 1 else tied


# ---------------------------------------------------------------------------
# observation — HIDDEN_INFO is False, so every seat is shown the same board;
# this exists for legibility, not concealment. It translates the internal
# state into idea.json's own vocabulary for a reader who has the rulebook and
# not the code: which pins are yard pins, which pieces neighbour which, what
# tooth height each piece carries, and each seat's own millstone and pellets
# pulled forward. See notes.md for the reasoning.
# ---------------------------------------------------------------------------

def _pid(p):
    # str() of a (q, r) tuple is "(-1, -2)" — exactly the substring that
    # appears inside every move tuple, e.g. ("place", (-1, -2), "gear_low"),
    # so a pin id here can be matched by eye against the LEGAL MOVES list
    # rather than converted between two coordinate spellings.
    return str(p)


def observation(state, seat):
    pieces = {}
    for p, piece in state["pins"].items():
        if piece is None:
            continue
        entry = {"piece": piece["type"], "mesh_height": _tier(piece)}
        if piece["type"] == "mill":
            entry["owner"] = piece["owner"]
        pieces[_pid(p)] = entry

    seats = []
    for s in range(state["n_players"]):
        mp = state["mill_pin"][s]
        seats.append({
            "seat": s,
            "mill_pin": _pid(mp) if mp is not None else None,
            "pellets": state["spindles"][s],
        })

    to_move = None if state["game_over"] else player_to_move(state)
    crank_pin = state["crank_pin"]

    return {
        "phase": state["phase"],
        "round": state["round"],
        "to_move": to_move,
        "start_player": state["start_player"],
        "game_over": state["game_over"],
        "crank_pin": _pid(crank_pin) if crank_pin is not None else None,
        "fixed_crank": crank_pin is not None,   # setup[1]: never moves again
        "supply": dict(state["supply"]),
        "granary_pellets_remaining": state["pellets"],
        "last_grind_clockwise_seats": list(state["last_grind_cw"]),
        "you": seats[seat],
        "seats": seats,
        "board": {
            # rules:setup[0]: the only pins a millstone or the crank may ever
            # stand on. Listed even empty, because SHIFT offers any empty one.
            "yard_pins": [_pid(p) for p in YARD_PINS],
            "inner_pins": [_pid(p) for p in INNER_PINS],
            # rules:turn[0] MESHING: two pieces on neighbouring pins mesh
            # (subject to mesh_height below); pins that are not neighbours
            # never mesh. A player at the table reads this off the board.
            "edges": [[_pid(a), _pid(b)] for a, b in EDGES],
            # Only occupied pins are listed; an absent pin id here means empty.
            "pieces": pieces,
        },
    }
