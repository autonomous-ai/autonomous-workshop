"""engine.py — blindcap, an executable model of idea.json. Not a game to play."""
from __future__ import annotations

import copy


class Undefined(Exception):
    """The rules do not say."""


SLUG = "blindcap"
PLAYERS = (2, 4)          # idea.json players.min / players.max (3 also supported)
MAX_TURNS = 120           # real games run exactly 13*n apply_move calls (max 52 at n=4)
MOVE_KINDS = ("plant", "probe", "crown", "pass")
HIDDEN_INFO = True        # each seat's own trough/planted species are secret to others


# ---------------------------------------------------------------------------
# Fixed facts of the game
# ---------------------------------------------------------------------------

SPECIES = ("deadhead", "bracket", "inkcap", "hollow")
SCARCE_SPECIES = ("inkcap", "hollow")           # score double when grouped
BASE_SUPPLY = ("deadhead", "deadhead", "bracket", "bracket", "inkcap", "hollow")

# (upper_sunk, lower_sunk) — True means the pin sinks (grooved at that band).
SPECIES_GROOVES = {
    "deadhead": (False, False),
    "bracket": (True, False),
    "inkcap": (False, True),
    "hollow": (True, True),
}

MAIN_ROUNDS = 6           # every player plants + acts once per round
TOTAL_ROUNDS = 7          # + one closing round of action-only turns
PIN_SUPPLY = 16
CROWNS_PER_PLAYER = 3

# Tile offsets (tile_row, tile_col), each tile a 3x3 block of sockets, matching
# idea.json rules:setup[0]: 2p -> 6x3, 3p -> an L of 27, 4p -> 6x6. The rules
# name only the aggregate shape and socket count, not which corner of the L is
# missing for 3 players; since no seat owns a fixed tile (any player may plant
# in any empty socket anywhere on the field) the exact orientation chosen here
# is inconsequential to anything the harness measures. See notes.md.
TILE_LAYOUTS = {
    2: [(0, 0), (0, 1)],
    3: [(0, 0), (0, 1), (1, 0)],
    4: [(0, 0), (0, 1), (1, 0), (1, 1)],
}

_LAYOUT_CACHE: dict = {}


def _layout(n_players: int):
    cached = _LAYOUT_CACHE.get(n_players)
    if cached is not None:
        return cached
    offsets = TILE_LAYOUTS.get(n_players)
    if offsets is None:
        raise Undefined(f"rules:setup[0]: no board layout is described for "
                        f"{n_players} players")
    coord_to_id: dict = {}
    coords = []
    for (tr, tc) in offsets:
        for lr in range(3):
            for lc in range(3):
                r, c = tr * 3 + lr, tc * 3 + lc
                coord_to_id[(r, c)] = len(coords)
                coords.append((r, c))
    adjacency = [[] for _ in coords]
    for (r, c), idx in coord_to_id.items():
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nb = (r + dr, c + dc)
            if nb in coord_to_id:
                adjacency[idx].append(coord_to_id[nb])
    result = (coords, adjacency)
    _LAYOUT_CACHE[n_players] = result
    return result


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def new_game(n_players, rng):
    coords, _adjacency = _layout(n_players)
    total_sockets = len(coords)
    sockets = [
        {"owner": None, "species": None, "crown": None,
         "probed_upper": False, "probed_lower": False}
        for _ in range(total_sockets)
    ]
    troughs = [list(BASE_SUPPLY) for _ in range(n_players)]
    state = {
        "n": n_players,
        "sockets": sockets,
        "troughs": troughs,
        "crowns_remaining": [CROWNS_PER_PLAYER] * n_players,
        "pins_remaining": PIN_SUPPLY,
        "round": 0,
        "seat_ptr": 0,
        "subphase": "plant",
    }
    return state


def player_to_move(state):
    return state["seat_ptr"] % state["n"]


def is_over(state):
    return state["round"] >= TOTAL_ROUNDS


# ---------------------------------------------------------------------------
# Moves
# ---------------------------------------------------------------------------

def legal_moves(state):
    if is_over(state):
        return []
    seat = player_to_move(state)
    moves = []

    if state["round"] < MAIN_ROUNDS and state["subphase"] == "plant":
        # rules:turn[0] — PLANT is mandatory while the player still has stools.
        species_options = sorted(set(state["troughs"][seat]))
        empty = [i for i, s in enumerate(state["sockets"]) if s["species"] is None]
        for sp in species_options:
            for sock in empty:
                moves.append(("plant", sp, sock))
        return moves

    # rules:turn[1-4] — the single free action: probe, crown, or pass.
    moves.append(("pass",))
    if state["pins_remaining"] > 0:
        for i, s in enumerate(state["sockets"]):
            if s["species"] is not None:
                if not s["probed_upper"]:
                    moves.append(("probe", i, "upper"))
                if not s["probed_lower"]:
                    moves.append(("probe", i, "lower"))
    if state["crowns_remaining"][seat] > 0:
        for i, s in enumerate(state["sockets"]):
            if s["species"] is not None and s["crown"] is None:
                moves.append(("crown", i))
    return moves


def _advance_turn(state):
    state["seat_ptr"] += 1
    if state["seat_ptr"] >= state["n"]:
        state["seat_ptr"] = 0
        state["round"] += 1
    # subphase is per player-turn, not per round: every seat that still has
    # stools owes a PLANT at the start of ITS turn, not just the first seat
    # to act in a round.
    state["subphase"] = "plant" if state["round"] < MAIN_ROUNDS else "action"


def apply_move(state, move, rng):
    seat = player_to_move(state)
    kind = move[0]

    if kind == "plant":
        _, species, sock = move
        state["troughs"][seat].remove(species)
        state["sockets"][sock]["species"] = species
        state["sockets"][sock]["owner"] = seat
        state["subphase"] = "action"          # same seat still owes its action
        return state

    if kind == "probe":
        _, sock, band = move
        state["sockets"][sock][f"probed_{band}"] = True
        state["pins_remaining"] -= 1
        _advance_turn(state)
        return state

    if kind == "crown":
        _, sock = move
        state["sockets"][sock]["crown"] = seat
        state["crowns_remaining"][seat] -= 1
        _advance_turn(state)
        return state

    if kind == "pass":
        _advance_turn(state)
        return state

    raise Undefined(f"rules:turn: unrecognised move kind {kind!r}")


# ---------------------------------------------------------------------------
# Groves and scoring — rules:win. Computed identically at any point in the
# game: the harvest itself does not change any stool's species or position
# (rules:end[1] — "Do not move a stool to another socket"), it only makes
# them visible, so applying the payout formula to whatever is on the board
# right now is the exact end-of-game computation, not a heuristic proxy.
# ---------------------------------------------------------------------------

def _groves(state):
    _coords, adjacency = _layout(state["n"])
    sockets = state["sockets"]
    visited = [False] * len(sockets)
    groves = []
    for i in range(len(sockets)):
        if visited[i] or sockets[i]["species"] is None:
            continue
        species = sockets[i]["species"]
        stack = [i]
        visited[i] = True
        comp = [i]
        while stack:
            cur = stack.pop()
            for nb in adjacency[cur]:
                if not visited[nb] and sockets[nb]["species"] == species:
                    visited[nb] = True
                    comp.append(nb)
                    stack.append(nb)
        groves.append({"species": species, "sockets": comp})
    return groves


def _grove_owners(state, grove):
    owners = set()
    for i in grove["sockets"]:
        c = state["sockets"][i]["crown"]
        if c is not None:
            owners.add(c)
    return owners


def _grove_payout(state, grove):
    owners = _grove_owners(state, grove)
    if not owners:
        return {}
    n_size = len(grove["sockets"])
    mult = 2 if grove["species"] in SCARCE_SPECIES else 1
    if len(owners) == 1:
        return {next(iter(owners)): n_size * n_size * mult}
    # Contest: each owner scores n once for the grove, no matter how many of
    # their own crowns sit in it (idea.json rules:win — a grove pays out once
    # per owner; a player with two crowns in one contested grove scores n, not 2n).
    return {o: n_size * mult for o in owners}


def scores(state):
    result = [0.0] * state["n"]
    for grove in _groves(state):
        for seat, pay in _grove_payout(state, grove).items():
            result[seat] += pay
    return result


def _largest_uncontested(state):
    best = [0] * state["n"]
    for grove in _groves(state):
        owners = _grove_owners(state, grove)
        if len(owners) == 1:
            owner = next(iter(owners))
            best[owner] = max(best[owner], len(grove["sockets"]))
    return best


def winners(state):
    scr = scores(state)
    top = max(scr) if scr else 0.0
    tied = [i for i, s in enumerate(scr) if s == top]
    if len(tied) == 1:
        return tied
    lug = _largest_uncontested(state)
    top_lug = max(lug[i] for i in tied)
    tied2 = [i for i in tied if lug[i] == top_lug]
    if len(tied2) == 1:
        return tied2
    # rules:win — "then in favour of the later seat in turn order." Seating is
    # a fixed clockwise rotation 0..n-1 every round including the closing
    # round, so "later" is simply the higher seat index among those still tied.
    return [max(tied2)]


# ---------------------------------------------------------------------------
# determinize — hides every other seat's planted species and trough contents
# from `seat`, consistent with what has actually been revealed to the table:
# each socket's owner (public, from the brim bites), the round-derived count
# of stools each player has planted so far, and every probe result already
# read off the board. Resamples a fresh, still-consistent species assignment
# for everyone but `seat` by backtracking over each opponent's fixed 6-stool
# supply (2 deadhead, 2 bracket, 1 inkcap, 1 hollow).
# ---------------------------------------------------------------------------

def _sample_consistent(constraints, trough_count, rng):
    slots = []
    for (sock, req_upper, req_lower) in constraints:
        allowed = [sp for sp in SPECIES
                   if (req_upper is None or SPECIES_GROOVES[sp][0] == req_upper)
                   and (req_lower is None or SPECIES_GROOVES[sp][1] == req_lower)]
        slots.append({"socket": sock, "allowed": allowed})
    for _ in range(trough_count):
        slots.append({"socket": None, "allowed": list(SPECIES)})

    order = sorted(range(len(slots)), key=lambda idx: len(slots[idx]["allowed"]))
    result: dict = {}
    supply_counts = {"deadhead": 2, "bracket": 2, "inkcap": 1, "hollow": 1}

    def backtrack(pos, remaining):
        if pos == len(order):
            return True
        idx = order[pos]
        candidates = [sp for sp in slots[idx]["allowed"] if remaining.get(sp, 0) > 0]
        rng.shuffle(candidates)
        for sp in candidates:
            remaining[sp] -= 1
            result[idx] = sp
            if backtrack(pos + 1, remaining):
                return True
            remaining[sp] += 1
            del result[idx]
        return False

    ok = backtrack(0, dict(supply_counts))
    if not ok:
        # The true assignment is always itself a valid solution, so this can
        # only mean a bookkeeping bug in this function, not a game state.
        raise AssertionError("determinize: no species assignment satisfies the "
                             "revealed probe constraints, which should be "
                             "impossible given a consistent true state")

    planted, trough = {}, []
    for idx, slot in enumerate(slots):
        sp = result[idx]
        if slot["socket"] is not None:
            planted[slot["socket"]] = sp
        else:
            trough.append(sp)
    return planted, trough


def determinize(state, seat, rng):
    st = copy.deepcopy(state)
    for p in range(st["n"]):
        if p == seat:
            continue  # a player always knows their own trough and plantings
        sockets_p = [i for i, s in enumerate(st["sockets"]) if s["owner"] == p]
        constraints = []
        for i in sockets_p:
            s = st["sockets"][i]
            true_species = s["species"]
            pattern = SPECIES_GROOVES[true_species]
            req_upper = pattern[0] if s["probed_upper"] else None
            req_lower = pattern[1] if s["probed_lower"] else None
            constraints.append((i, req_upper, req_lower))
        trough_count = len(st["troughs"][p])
        planted, trough = _sample_consistent(constraints, trough_count, rng)
        for i, sp in planted.items():
            st["sockets"][i]["species"] = sp
        st["troughs"][p] = trough
    return st


def observation(state, seat):
    """What `seat` is actually allowed to know, per rules:setup[1]-[2] and the
    PROBE step: a socket's owner, its crown, whether each of its two holes has
    been probed, and the sunk/proud RESULT of any hole that has been probed
    (all public — a pin standing proud or sunk is visible to everyone at the
    table). A socket's true species is included only when `seat` planted it,
    or when both holes have been probed, since the four species have distinct
    (upper, lower) groove patterns and a fully-probed socket's species is
    therefore already public knowledge, derivable by anyone from the two
    revealed results — carrying it through is not an extra leak. Every other
    socket's species is removed. Every other player's trough is replaced by
    its remaining count, since the composition of stools is public and only
    the assignment of species to what remains unplanted is not."""
    sockets_obs = []
    for s in state["sockets"]:
        true_species = s["species"]
        known = (s["owner"] == seat) or (s["probed_upper"] and s["probed_lower"])
        revealed_upper = (SPECIES_GROOVES[true_species][0]
                          if true_species is not None and s["probed_upper"] else None)
        revealed_lower = (SPECIES_GROOVES[true_species][1]
                          if true_species is not None and s["probed_lower"] else None)
        sockets_obs.append({
            "owner": s["owner"],
            "crown": s["crown"],
            "probed_upper": s["probed_upper"],
            "probed_lower": s["probed_lower"],
            "revealed_upper": revealed_upper,   # True=sunk, False=proud, None=not probed
            "revealed_lower": revealed_lower,
            "species": true_species if known else None,
        })
    troughs_obs = [list(state["troughs"][p]) if p == seat else len(state["troughs"][p])
                   for p in range(state["n"])]
    return {
        "n": state["n"],
        "seat": seat,
        "sockets": sockets_obs,
        "troughs": troughs_obs,
        "crowns_remaining": list(state["crowns_remaining"]),
        "pins_remaining": state["pins_remaining"],
        "round": state["round"],
        "seat_ptr": state["seat_ptr"],
        "subphase": state["subphase"],
    }
