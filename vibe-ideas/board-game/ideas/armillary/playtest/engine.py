"""engine.py — armillary, an executable model of idea.json. Not a game to play."""
from __future__ import annotations

import copy


class Undefined(Exception):
    """The rules do not say."""


SLUG = "armillary"
PLAYERS = (2, 4)          # idea.json players.min / players.max
MAX_TURNS = 200           # a real game is at most 5 decisions x 24 turns = 120
# Every action the rules make the player choose: PULL and TAKE are the two
# REACH options (turn[2]/[3]), STOP is the turn[1] right to end reaching early,
# and TURN THE SKY (turn[7]) is the mandatory one-disc rotation. BANK, REFILL
# and ADVANCE THE DAWN are compulsory bookkeeping with no choice in them, so
# they are not decision-kinds; see notes.md.
MOVE_KINDS = ("pull", "take", "stop", "rotate")
HIDDEN_INFO = True        # the face of every knob-up tile in a well and the bowl

# Constellations (rules:setup plinth_ring slots / score_rail slots): THE ANVIL
# is wells 0-3, THE WHEEL is 4-6, THE SERPENT is 7-9. Indexed 0,1,2.
_SOLID = {0: {0, 1, 5},   # mask_disc_a bottom, solid positions 0,1,5
          1: {0, 3, 6},   # mask_disc_b middle,  solid positions 0,3,6
          2: {0, 2, 4}}   # mask_disc_c top,     solid positions 0,2,4

const_names = ("anvil", "wheel", "serpent")


def _const(well):
    return 0 if well < 4 else (1 if well < 7 else 2)


def _open_wells(disc):
    """A well is open iff every mask shows a window over it (turn[0]): well w
    aligns to a window on disc d iff (w - rot_d) mod 10 is not a SOLID position.
    At rot 0,0,0 this yields exactly the Serpent wells 7,8,9, matching setup[0]."""
    a, b, c = disc
    open_w = []
    for w in range(10):
        if (w - a) % 10 in _SOLID[0]:
            continue
        if (w - b) % 10 in _SOLID[1]:
            continue
        if (w - c) % 10 in _SOLID[2]:
            continue
        open_w.append(w)
    return open_w


# ---------------------------------------------------------------------------
# Turn structure
# ---------------------------------------------------------------------------
# One player-turn: a REACH phase (one or more pull/take/stop decisions), then
# compulsory BANK (turn[5]) + REFILL (turn[6]), then a LAST "sky" phase that is
# exactly one TURN THE SKY rotation (turn[7]), then compulsory ADVANCE THE DAWN
# (turn[8]) which ends the turn. The dawn clock is a hard 24-turn cap (end[0]).
# ---------------------------------------------------------------------------

def new_game(n_players, rng):
    if n_players < PLAYERS[0] or n_players > PLAYERS[1]:
        raise ValueError(f"armillary seats {PLAYERS[0]}-{PLAYERS[1]}, "
                         f"not {n_players}")
    # setup[1]/[2]: mix the 48 tiles, drop one knob-up into each of the 10
    # wells, tip the remaining 38 into the night_bowl. setup[3]: everyone
    # begins with two reaches; the first player is seat 0 and the dawn clock
    # is at its first socket.
    pool = (["star"] * 18 + ["moon"] * 16 + ["void"] * 14)
    rng.shuffle(pool)
    wells = {w: {"tile": pool.pop(), "face_up": False} for w in range(10)}
    return {
        "n": n_players,
        "wells": wells,
        "bowl": pool,               # hidden identity, knob-up
        "catch": [],                # this turn's pulled tiles, face-up, at risk
        "eclipse_bay": 0,           # voids laid face-up in the lid bay (public)
        "rails": [[[0, 0] for _ in range(3)] for _ in range(n_players)],
        # rails[seat][const] = [stars_banked, moons_banked]
        "disc": [0, 0, 0],          # rotation of mask_disc_a/b/c in grooves
        "pegs": [2] * n_players,    # each seat's reach_peg = reaches next turn
        "reaches": 2,               # remaining reaches THIS player-turn
        "turn_count": 0,            # completed player-turns (0..24)
        "busted": False,            # this turn's player pulled a void
        "phase": "reach",           # "reach" | "sky" | "over"
        "game_over": False,
    }


def player_to_move(state):
    return state["turn_count"] % state["n"]


def _reaching_forced_done(state):
    """Reaching ends on its own when the player has spent every reach, OR when
    no reachable tile is left. turn[5] settles the second condition: 'a knob-up
    tile in an open well counts as a tile you can take, because you may always
    PULL it rather than TAKE it ... your reaching never forces you to stop
    while any open well is non-empty.' So reaching ends only when every open
    well is empty; a face-down tile in an open well does NOT force BANK, the
    player may pull it."""
    if state["reaches"] <= 0:
        return True
    for w in _open_wells(state["disc"]):
        if state["wells"][w] is not None:
            return False
    return True


def _bank(state, seat, tile, well):
    c = _const(well)
    if tile == "star":
        state["rails"][seat][c][0] += 1
    elif tile == "moon":
        state["rails"][seat][c][1] += 1


def _finish_reaching(state, rng):
    """turn[5] BANK (stand every catch tile into the rail slot matching its
    source well's collar), then turn[6] REFILL (draw one tile from the bowl
    into every empty well that does not hold a face-up tile), then enter the
    TURN THE SKY phase. On a bust the catch was already returned face-up and
    cleared, so nothing is banked and the returned wells are not refilled."""
    seat = player_to_move(state)
    for c in state["catch"]:
        _bank(state, seat, c["tile"], c["well"])
    state["catch"] = []
    for w in range(10):
        if state["wells"][w] is None and state["bowl"]:
            tile = state["bowl"].pop(rng.randrange(len(state["bowl"])))
            state["wells"][w] = {"tile": tile, "face_up": False}
    state["phase"] = "sky"


def _start_turn(state, rng):
    state["phase"] = "reach"
    state["catch"] = []
    state["busted"] = False
    if _reaching_forced_done(state):
        _finish_reaching(state, rng)   # a turn with nothing reachable banks and
                                       # goes straight to TURN THE SKY


def legal_moves(state):
    if state["game_over"]:
        return []
    if state["phase"] == "reach":
        moves = []
        if state["reaches"] > 0:
            moves.append(("stop",))
            for w in _open_wells(state["disc"]):
                cell = state["wells"][w]
                if cell is None:
                    continue
                moves.append(("take", w) if cell["face_up"] else ("pull", w))
        return moves
    if state["phase"] == "sky":
        # turn[7]: rotate exactly one disc by 1,2,3 grooves either way; a bust
        # forces exactly one groove (in either direction) and the peg to 3.
        deltas = (1, -1, 2, -2, 3, -3) if not state["busted"] else (1, -1)
        return [("rotate", d, delta) for d in range(3) for delta in deltas]
    return []


def apply_move(state, move, rng):
    kind = move[0]
    seat = player_to_move(state)

    if kind == "pull":
        # turn[2]: lift a knob-up tile from an open well and turn it face-up.
        w = move[1]
        tile = state["wells"][w]["tile"]
        state["wells"][w] = None
        state["reaches"] -= 1
        if tile == "void":
            # turn[4] BUST: reaching ends, the void goes to the eclipse bay,
            # every catch tile is returned face-up to the well it came from,
            # nothing is banked, and this turn's rotation is forced to one groove.
            state["eclipse_bay"] += 1
            state["busted"] = True
            for c in state["catch"]:
                state["wells"][c["well"]] = {"tile": c["tile"], "face_up": True}
            state["catch"] = []
            state["reaches"] = 0
            _finish_reaching(state, rng)
        else:
            state["catch"].append({"tile": tile, "well": w})
            if _reaching_forced_done(state):
                _finish_reaching(state, rng)
        return state

    if kind == "take":
        # turn[3]: lift a face-up star or moon from an open well into the rail
        # slot matching that well's collar; banked instantly, never lost.
        w = move[1]
        tile = state["wells"][w]["tile"]
        state["wells"][w] = None
        state["reaches"] -= 1
        _bank(state, seat, tile, w)
        if _reaching_forced_done(state):
            _finish_reaching(state, rng)
        return state

    if kind == "stop":
        # turn[1]: the player may stop reaching early; unspent reaches are lost.
        _finish_reaching(state, rng)
        return state

    if kind == "rotate":
        # turn[7] TURN THE SKY + turn[8] ADVANCE THE DAWN. Rotate one disc, set
        # the next player's reach_peg to 4 - grooves (3 if busted), then walk
        # the dawn one socket and end the turn. After 24 turns the peg has left
        # the 24th socket and the game is over (end[0]).
        d, delta = move[1], move[2]
        state["disc"][d] = (state["disc"][d] + delta) % 10
        next_reaches = 3 if state["busted"] else (4 - abs(delta))
        next_seat = (state["turn_count"] + 1) % state["n"]
        state["pegs"][next_seat] = next_reaches
        state["turn_count"] += 1
        if state["turn_count"] >= 24:
            state["game_over"] = True
            state["phase"] = "over"
        else:
            state["reaches"] = next_reaches
            _start_turn(state, rng)
        return state

    raise Undefined("rules:turn: unrecognised move kind {kind!r}")


# ---------------------------------------------------------------------------
# Scoring and win (rules:win)
# ---------------------------------------------------------------------------

def scores(state):
    """Running score = the end-of-game score applied to what is banked so far:
    each star 2, each moon 1, plus 3 for every COMPLETE NIGHT (one tile in
    every constellation) = 3 x min over the three slots. Catch tiles are not
    counted because they are at risk and worthless if dawn comes before they
    are banked (end[1]) — this is the exact final formula on banked tiles, so
    it is a faithful running proxy, not a separate heuristic."""
    out = []
    for s in range(state["n"]):
        rails = state["rails"][s]
        stars = sum(r[0] for r in rails)
        moons = sum(r[1] for r in rails)
        slots = [r[0] + r[1] for r in rails]
        out.append(float(2 * stars + moons + 3 * min(slots)))
    return out


def winners(state):
    scr = scores(state)
    top = max(scr)
    tied = [i for i, v in enumerate(scr) if v == top]
    if len(tied) == 1:
        return tied
    # rules:win tiebreak: the tied player with more tiles in their shortest
    # slot wins; if that still ties, the win is shared.
    shortest = [min(r[0] + r[1] for r in state["rails"][i]) for i in tied]
    best = max(shortest)
    tied2 = [tied[i] for i, v in enumerate(shortest) if v == best]
    return tied2


def is_over(state):
    return bool(state["game_over"])


# ---------------------------------------------------------------------------
# determinize — resample everything a seat cannot see: the identity of every
# knob-up tile in a well and every tile in the night_bowl. The hidden
# multiset is itself public knowledge (18/16/14 total minus the face-up and
# banked tiles everyone can count), so the resample is the same for every seat
# and never changes the open board, the bowl count, or any face-up tile.
# ---------------------------------------------------------------------------

def determinize(state, seat, rng):
    st = copy.deepcopy(state)
    pool = list(st["bowl"])
    face_down_wells = [w for w in range(10)
                       if st["wells"][w] is not None and not st["wells"][w]["face_up"]]
    for w in face_down_wells:
        pool.append(st["wells"][w]["tile"])
    rng.shuffle(pool)
    for i, w in enumerate(face_down_wells):
        st["wells"][w]["tile"] = pool[i]
    st["bowl"] = pool[len(face_down_wells):]
    return st


# ---------------------------------------------------------------------------
# observation — what this seat may look at, in idea.json's own words.
# Pass 1 (remove): the identity of every knob-up tile (hidden in wells, and
# all of the night_bowl). Pass 2 (add back what is derivable by eye): which
# wells are open (read off the discs), each well's collar constellation, which
# wells are empty, each seat's reach_peg, every seat's banked rail, the bowl
# count (tracked by following every refill), the eclipse-bay void count, the
# dawn socket, and this turn's face-up catch. Pass 3 (rulebook words):
# wells are named as wells, discs by their mask name, collars by constellation.
# ---------------------------------------------------------------------------

def observation(state, seat):
    discs = {"mask_disc_a": state["disc"][0],
             "mask_disc_b": state["disc"][1],
             "mask_disc_c": state["disc"][2]}
    wells_obs = {}
    for w in range(10):
        cell = state["wells"][w]
        if cell is None:
            wells_obs[str(w)] = {"constellation": const_names[_const(w)],
                                 "empty": True}
        elif cell["face_up"]:
            wells_obs[str(w)] = {"constellation": const_names[_const(w)],
                                 "face_up": True, "tile": cell["tile"]}
        else:
            wells_obs[str(w)] = {"constellation": const_names[_const(w)],
                                 "knob_up": True, "tile": None}
    open_wells = [str(w) for w in _open_wells(state["disc"])]
    seats = []
    for s in range(state["n"]):
        banked = {const_names[c]: {"star": state["rails"][s][c][0],
                                   "moon": state["rails"][s][c][1]}
                  for c in range(3)}
        seats.append({"seat": s, "reach_peg": state["pegs"][s], "banked": banked})
    current = player_to_move(state)
    if state["game_over"]:
        action, whose_turn = "dawn_has_come", None
    elif state["phase"] == "sky":
        action, whose_turn = "turn_the_sky", current
    else:
        action, whose_turn = "reaching", current
    return {
        "n": state["n"],
        "seat": seat,
        "whose_turn": whose_turn,
        "action": action,
        "turns_until_dawn": 24 - state["turn_count"],
        "dawn_peg_socket": state["turn_count"] % 24,
        "discs": discs,
        "sky": {"open_wells": open_wells, "wells": wells_obs},
        "night_bowl_tiles": len(state["bowl"]),     # count public, faces hidden
        "eclipse_bay_void_tiles": state["eclipse_bay"],
        "well_to_constellation": {str(w): const_names[_const(w)]
                                  for w in range(10)},
        "reaches_left_this_turn": state["reaches"],
        "current_catch": [{"tile": c["tile"], "well": str(c["well"]),
                           "constellation": const_names[_const(c["well"])]}
                          for c in state["catch"]],
        "you": seats[seat],
        "seats": seats,
    }


# ---------------------------------------------------------------------------
# turn[5] was previously ambiguous on whether a knob-up tile ends reaching; it
# is now settled in idea.json: 'a knob-up tile in an open well counts as a tile
# you can take, because you may always PULL it rather than TAKE it'. The
# inclusive reading is wired unconditionally in `_reaching_forced_done`.
# ---------------------------------------------------------------------------

ASSUMPTIONS = []
CHOICES = {}
