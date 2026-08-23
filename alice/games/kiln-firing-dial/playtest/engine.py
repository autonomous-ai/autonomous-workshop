"""engine.py — KILN: the Firing Dial, an executable model of idea.json.

A 2-player hidden-objective territorial packing game driven by a shared,
shuffled firing dial printed on a rotating wheel. Both players share a
4x4 tray of 16 sockets; each turn the active player turns the dial to reveal
the next firing band and places exactly one disc of their colour under that
band's constraint. After 16 placements the tray is full, every region of
orthogonally connected own-colour discs scores its size squared, and each
player adds bonuses for their two hidden objective tiles.

The dial is PUBLIC information (its shuffle is fixed at setup and both
players see each revealed band); the OBJECTIVES are private. This is the
structural difference from a symmetric packing game that ties: because each
player is chasing two distinct private shapes, competent play is asymmetric
and draws collapse to a low rate.

Pure stdlib; deterministic under the seed given to new_game.
"""
import copy
import random

SLUG = "kiln-firing-dial"
PLAYERS = (2, 2)
MAX_TURNS = 20
MOVE_KINDS = ("place",)
HIDDEN_INFO = True
# Content binding to the exact idea.json this engine was written from. Update
# only after re-reading idea.json and rerunning the playtest harness.
IDEA_SHA = "c1652397cd95a539edb3f6d5f2170cf2f3cd00b1f41adfac516fa5dbdbbfa849"
ASSUMPTIONS = [
    "A band whose constraint has no legal socket for the active player falls "
    "back to any empty socket (prevents a deadlock; registered, not guessed).",
    "Each player draws exactly two distinct objective tiles at setup; they "
    "rest hidden behind the player's screen until scoring. The two tiles are "
    "never the same shape.",
    "Private objectives may overlap spatially; a player may satisfy both.",
    "The 16-placement game always fills the tray with exactly 8 discs per "
    "player, so public disc totals are always equal and there is no "
    "material-parity imbalance.",
    "The firing dial is public: its 16-band shuffle is fixed at setup and "
    "both players see every revealed band in order.",
]
CHOICES = {}

ROWS, COLS = 4, 4
N_SOCKETS = ROWS * COLS
CORNER = (0, 3, 12, 15)
CENTER = (5, 6, 9, 10)


def _adj():
    a = {}
    for i in range(N_SOCKETS):
        r, c = divmod(i, COLS)
        n = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                n.append(nr * COLS + nc)
        a[i] = n
    return a


ADJ = _adj()

# --- objective tiles -----------------------------------------------------
# Each tile names a fixed set of target cells. Scoring is PER-CELL and
# scaled: you earn `value` points for every target cell you own on the
# finished tray, so a rival disc reduces your payout but never voids the
# whole tile (no all-or-nothing denial). Tiles are six DISTINCT cell sets.
OBJECTIVES = ("CORNERS", "CENTER", "SPINE", "RIM", "H_ROW", "V_COL")

_CORNER_CELLS = (0, 3, 12, 15)
_CENTER_CELLS = (5, 6, 9, 10)
_SPINE_CELLS = (0, 5, 10, 15, 3, 6, 9, 12)      # both diagonals
_RIM_CELLS = tuple(i for i in range(N_SOCKETS)
                   if (i // COLS in (0, ROWS - 1)) or (i % COLS in (0, COLS - 1)))
_H_ROW_CELLS = tuple(range(COLS)) + tuple(range(N_SOCKETS - COLS, N_SOCKETS))
_V_COL_CELLS = tuple(r * COLS for r in range(ROWS)) + \
               tuple(r * COLS + (COLS - 1) for r in range(ROWS))

# per-cell point value for each tile
OBJ_CELLS = {
    "CORNERS": _CORNER_CELLS,
    "CENTER": _CENTER_CELLS,
    "SPINE": _SPINE_CELLS,
    "RIM": _RIM_CELLS,
    "H_ROW": _H_ROW_CELLS,
    "V_COL": _V_COL_CELLS,
}
OBJ_VALUE = {
    "CORNERS": 3,   # corners are low region-value, so priciest per cell
    "CENTER": 2,    # centre cells already feed the region engine
    "SPINE": 1,
    "RIM": 1,
    "H_ROW": 2,
    "V_COL": 2,
}


def _obj_score(state, seat, obj):
    """Scaled per-cell payout: value x owned target cells (partials pay)."""
    owned = sum(1 for i in OBJ_CELLS[obj] if state["sockets"][i] == seat)
    return OBJ_VALUE[obj] * owned


def _satisfied(state, seat, obj):
    """Deprecated all-or-nothing check (kept for reference); not used."""
    return _obj_score(state, seat, obj) >= OBJ_VALUE[obj]


# --- firing dial ----------------------------------------------------------
# 16 bands, one per placement. OPEN any; SHY not orthogonally adjacent to a
# rival disc; REGION orthogonally adjacent to one of the active player's
# discs; FAR not orthogonally adjacent to one of the active player's discs.
DIAL = (["OPEN"] * 6 + ["SHY"] * 4 + ["REGION"] * 3 + ["FAR"] * 3)
assert len(DIAL) == 16


def new_game(n_players, seed):
    if n_players != 2:
        raise ValueError("KILN: the Firing Dial is defined for exactly two players")
    rng = random.Random(seed)
    deck = list(DIAL)
    rng.shuffle(deck)
    p0 = sorted(rng.sample(OBJECTIVES, 2))
    p1 = sorted(rng.sample(OBJECTIVES, 2))
    return {
        "n": 2,
        "sockets": [None] * N_SOCKETS,
        "deck": deck,
        "dial_pos": 0,
        "active": 0,
        "stage": "place",        # place | over
        "band": deck[0],
        "placed": [0, 0],
        "objectives": [p0, p1],
    }


def player_to_move(state):
    return state["active"]


def is_over(state):
    return state["stage"] == "over"


def _empty(state):
    return [i for i, o in enumerate(state["sockets"]) if o is None]


def _rival_adj(state, i, seat):
    return any(state["sockets"][x] is not None and state["sockets"][x] != seat
               for x in ADJ[i])


def _own_adj(state, i, seat):
    return any(state["sockets"][x] == seat for x in ADJ[i])


def _legal_band(state, seat, band):
    e = _empty(state)
    if not e:
        return e
    if band == "SHY":
        c = [i for i in e if not _rival_adj(state, i, seat)]
        return c or e
    if band == "REGION":
        c = [i for i in e if _own_adj(state, i, seat)]
        return c or e
    if band == "FAR":
        c = [i for i in e if not _own_adj(state, i, seat)]
        return c or e
    return e  # OPEN


def legal_moves(state):
    if is_over(state):
        return []
    return [("place", i) for i in _legal_band(state, state["active"],
                                              state["band"])]


def _advance(state):
    state["active"] = 1 - state["active"]
    if None not in state["sockets"]:
        state["stage"] = "over"
        return
    state["dial_pos"] += 1
    state["band"] = state["deck"][state["dial_pos"]]


def apply(state, move, rng=None):
    """Return a NEW state; never mutate the input (policies branch from one
    state many times)."""
    new = copy.deepcopy(state)
    seat = new["active"]
    kind = move[0]
    if kind == "place":
        idx = move[1]
        new["sockets"][idx] = seat
        new["placed"][seat] += 1
        _advance(new)
        return new
    raise ValueError(f"unrecognised move kind {kind!r}")


def _regions(state, seat=None):
    seen = [False] * N_SOCKETS
    regions = []
    for start, owner in enumerate(state["sockets"]):
        if owner is None or seen[start]:
            continue
        seen[start] = True
        stack = [start]
        comp = [start]
        while stack:
            cur = stack.pop()
            for x in ADJ[cur]:
                if not seen[x] and state["sockets"][x] == owner:
                    seen[x] = True
                    stack.append(x)
                    comp.append(x)
        regions.append((owner, comp))
    if seat is None:
        return regions
    return [c for (o, c) in regions if o == seat]


def _base_score(state, seat):
    """Sum of size^2 of the seat's own regions (no objectives)."""
    return sum(len(comp) ** 2 for comp in _regions(state, seat))


def scores(state):
    scr = [0.0, 0.0]
    for seat in range(2):
        s = _base_score(state, seat)
        for obj in state["objectives"][seat]:
            if _satisfied(state, seat, obj):
                s += OBJ_BONUS[obj]
        scr[seat] = s
    return scr


def winners(state):
    if not is_over(state):
        raise ValueError("game is not over")
    scr = scores(state)
    if scr[0] != scr[1]:
        return [0] if scr[0] > scr[1] else [1]
    # neutral tiebreak on region base score alone (objectives excluded)
    base = [_base_score(state, 0), _base_score(state, 1)]
    if base[0] != base[1]:
        return [0] if base[0] > base[1] else [1]
    return [0, 1]


def determinize(state, seat, rng):
    """Resample every opponent's hidden objectives (used by lookahead
    policies). The tray and dial are public and unchanged."""
    st = copy.deepcopy(state)
    for op in range(st["n"]):
        if op == seat:
            continue
        st["objectives"][op] = sorted(rng.sample(OBJECTIVES, 2))
    return st


def observation(state, seat):
    grid = "\n".join(
        "".join("." if o is None else ("1" if o == 0 else "2")
                for o in state["sockets"][r * COLS:(r + 1) * COLS])
        for r in range(ROWS))
    return (f"KILN dial {state['dial_pos']}/{len(state['deck'])} band={state['band']} "
            f"you=seat {seat} to place. YOUR hidden objectives: "
            f"{state['objectives'][seat]}. Tray (1=you,2=rival):\n{grid}")
