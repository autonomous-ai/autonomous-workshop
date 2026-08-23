"""engine.py — CONE NINE: the Firing Dial, executable model of idea.json.

A 2-player hidden-objective territorial packing game driven by a shared,
cyclic firing dial printed on a rotating wheel. Both players share a
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

SLUG = "cone-nine"
PLAYERS = (2, 2)
MAX_TURNS = 16
MOVE_KINDS = ("place",)
HIDDEN_INFO = True
# Content binding to the exact idea.json this engine was written from. Update
# only after re-reading idea.json and rerunning the playtest harness.
IDEA_SHA = "4ccf65ccab208ae7a8362a5fb808ebccf4e7510a2f8447f45d927b9b1ac69792"
ASSUMPTIONS = [
    "A band whose constraint has no legal socket for the active player falls "
    "back to any empty socket (prevents a deadlock; registered, not guessed).",
    "Each player draws exactly two distinct objective tiles at setup; they "
    "rest hidden behind the player's screen until scoring. The two tiles are "
    "never the same shape.",
    "The six glaze maps are dealt without replacement: each player gets two "
    "and two remain unseen, so maps never duplicate within a game.",
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
OBJECTIVES = ("CORNERS", "HEART", "SALTIRE", "HORIZON", "PILLARS", "CRACKLE")

_CORNER_CELLS = (0, 3, 12, 15)
_HEART_CELLS = (5, 6, 9, 10)
_SALTIRE_CELLS = (0, 3, 5, 6, 9, 10, 12, 15)
_HORIZON_CELLS = (0, 1, 2, 3, 12, 13, 14, 15)
_PILLARS_CELLS = (0, 3, 4, 7, 8, 11, 12, 15)
_CRACKLE_CELLS = (0, 2, 5, 7, 8, 10, 13, 15)

# per-cell point value for each tile
OBJ_CELLS = {
    "CORNERS": _CORNER_CELLS,
    "HEART": _HEART_CELLS,
    "SALTIRE": _SALTIRE_CELLS,
    "HORIZON": _HORIZON_CELLS,
    "PILLARS": _PILLARS_CELLS,
    "CRACKLE": _CRACKLE_CELLS,
}
OBJ_VALUE = {
    "CORNERS": 2,
    "HEART": 2,
    "SALTIRE": 1,
    "HORIZON": 1,
    "PILLARS": 1,
    "CRACKLE": 1,
}


def _obj_score(state, seat, obj):
    """Scaled per-cell payout: value x owned target cells (partials pay)."""
    owned = sum(1 for i in OBJ_CELLS[obj] if state["sockets"][i] == seat)
    return OBJ_VALUE[obj] * owned


# --- firing dial ----------------------------------------------------------
# 16 bands, one per placement. OPEN any; SHY not orthogonally adjacent to a
# rival disc; REGION orthogonally adjacent to one of the active player's
# discs; FAR not orthogonally adjacent to one of the active player's discs.
DIAL = ("OPEN", "SHY", "REGION", "OPEN", "FAR", "SHY", "OPEN", "REGION",
        "SHY", "OPEN", "FAR", "OPEN", "REGION", "SHY", "FAR", "OPEN")
assert len(DIAL) == 16


def new_game(n_players, seed):
    if n_players != 2:
        raise ValueError("CONE NINE is defined for exactly two players")
    rng = random.Random(seed)
    start = rng.randrange(len(DIAL))
    deck = list(DIAL[start:] + DIAL[:start])
    maps = list(OBJECTIVES)
    rng.shuffle(maps)
    p0 = sorted(maps[:2])
    p1 = sorted(maps[2:4])
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
    if move not in legal_moves(state):
        raise ValueError(f"illegal move {move!r}")
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
            s += _obj_score(state, seat, obj)
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
    available = [obj for obj in OBJECTIVES
                 if obj not in st["objectives"][seat]]
    for op in range(st["n"]):
        if op == seat:
            continue
        st["objectives"][op] = sorted(rng.sample(available, 2))
    return st


def observation(state, seat):
    grid = "\n".join(
        "".join("." if o is None else ("A" if o == 0 else "B")
                for o in state["sockets"][r * COLS:(r + 1) * COLS])
        for r in range(ROWS))
    return (f"CONE NINE dial {state['dial_pos'] + 1}/{len(state['deck'])} "
            f"band={state['band']} you=seat {seat}. YOUR hidden glaze maps: "
            f"{state['objectives'][seat]}. Tray (A=seat 0, B=seat 1):\n{grid}")
