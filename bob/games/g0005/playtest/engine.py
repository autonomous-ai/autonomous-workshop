"""Kick — engine implementation of games/g0005/rules.md.

One printed rail of 10 slots, open at both ends. Every tile carries a sealed
disc in one end (its HEAD): a magnet with N facing out, a magnet with S
facing out, or a plain steel slug. Only the owner knows which. On your turn
you push one tile into either mouth, head first or tail first, and the rail
resolves itself:

    two like poles touching        -> KICK  (everything past the break is
                                             launched toward the far mouth)
    magnet vs opposite pole,
    or magnet vs steel             -> CLAMP (welded forever, never kicks)
    anything touching a bare face,
    or steel vs steel              -> slack (nothing)

Every tile that leaves the rail on your push lands in your tray; only tiles
that are NOT your colour are worth a point. The game ends at the end of the
round in which any rack goes empty.

Everything rules.md left open is registered in ASSUMPTIONS below, never
guessed silently.

State is a dict whose values are tuples, ints, strings and (two) dicts that
``apply`` copies before writing, so ``apply`` can never write through to its
input.

Coordinates: ``rail`` is a 10-tuple in ABSOLUTE slot order, index 0 at mouth
A and index 9 at mouth B. Each entry is None or ``(tile_id, head_dir)`` with
head_dir -1 = the head points at mouth A, +1 = the head points at mouth B.
A push is resolved in NEAR-MOUTH-RELATIVE coordinates (rules.md 5.1 numbers
slot 1 from the mouth being pushed into), which ``_rel_line`` produces and
``_abs_line`` writes back.
"""

import random

IDEA_SHA = "20b9993488f8caa4a502b13d2489dbe1afac075586f20af136967779851bd724"

N_SLOTS = 10
KINDS = ("N", "S", "STEEL")
ENDS = ("A", "B")
ORIENTS = ("head", "tail")
CHIPS_PER_PLAYER = 3

#: players -> (tiles in hand, magnets, steel slugs). rules.md 3.3, public.
HANDS = {2: (12, 8, 4), 3: (10, 7, 3), 4: (9, 6, 3)}

#: Defensive only. The real bound is hand size + chips rounds (A5); this cap
#: is a backstop that no legal line of play can reach.
SAFETY_ROUND_CAP = 40

#: scores() weights — see the scores() docstring for what each one counts.
W_THREAT = 0.10
W_OWN_IN_RAIL = 0.04
W_OWN_FED = 0.03
W_CHIP = 0.01


ASSUMPTIONS = [
    "A1 SETUP IS A MOVE. rules.md 3.4 has each player load their magnets "
    "behind a screen, choosing per tile which pole faces out. Tiles of the "
    "same colour are otherwise identical and the head/tail choice is made "
    "again at push time, so the only thing that choice decides is HOW MANY "
    "magnets face N. The engine models setup as one hidden decision per "
    "seat -- ('load', n_N) -- taken in seat order starting from the start "
    "player. Nothing is revealed between loads, so sequencing a "
    "simultaneous decision changes no information and no strategy.",

    "A2 TILES OF A KIND ARE INTERCHANGEABLE. rules.md numbers tiles 1-12, "
    "but nothing in the rules distinguishes two tiles of the same colour "
    "holding the same disc. Push moves are therefore listed once per "
    "(mouth, disc kind, head-first/tail-first) -- at most 12 -- instead of "
    "once per physical tile.",

    "A3 START PLAYER AND SEAT ORDER. rules.md 3.6 gives the seat to 'the "
    "youngest player', which no simulation can evaluate, so the engine "
    "draws the start seat from the seeded rng. 'Clockwise' and 'the player "
    "on your left' are read as seat + 1 mod n; rules.md never pins "
    "clockwise to ascending seat order.",

    "A4 EMPTY RACK MEANS PASS, NOT PROBE. rules.md 4 says 'If your rack is "
    "empty you may only Probe', but 5.2 requires you to 'take one or two "
    "tiles from your own rack' to touch with -- with an empty rack there is "
    "nothing to touch with. The engine rules Probe impossible on an empty "
    "rack, so such a seat passes. THIS IS A DIRECT CONTRADICTION IN THE "
    "RULES and only bites in the final round (the game ends at the end of "
    "the round a rack empties), but rules.md 4 and 5.2 must be reconciled.",

    "A5 THE STATED LENGTH BOUND IS WRONG. rules.md 6 claims the game 'runs "
    "for at most as many rounds as a starting hand has tiles' and that "
    "'Probes only make it shorter for the prober'. A Probe spends a CHIP, "
    "not a tile, so a player who probes with all 3 chips needs hand+3 turns "
    "to empty their rack: the true worst case is hand+3 rounds (15 at 2p, "
    "13 at 3p, 12 at 4p), not hand rounds. The engine implements the true "
    "bound -- the game still always ends, because no action returns a tile "
    "to a rack -- plus a defensive round cap of 40 that no legal line can "
    "reach. rules.md 6's arithmetic needs fixing.",

    "A6 THE NOTCH MAKES HEAD/TAIL PUBLIC. rules.md 5.1 step 2: 'Everyone can "
    "see which you chose, because the head is notched.' So the 'face is "
    "bare' row of the 5.2 probe answer key is never news -- everyone "
    "already knows a tail-out tile has a bare face. The engine keeps such a "
    "probe legal (5.2 forbids only an EMPTY mouth slot) but it teaches the "
    "prober nothing.",

    "A7 EVERY CURRENT JOINT'S KIND IS PUBLIC. rules.md 5 ('A joint's kind is "
    "public the moment it forms') and 8 ('It sits there live... everybody "
    "saw it') mean every joint now in the rail was witnessed when it "
    "formed, including slack ones (nothing visibly happened) and unfired "
    "live kicks. observation() therefore publishes the kind of every joint "
    "in the rail to every seat. The individual disc kinds stay hidden; "
    "deducing a face from a joint kind plus a known neighbour is left to "
    "the seat, not done for it.",

    "A8 PROBE RESULTS ARE PUBLIC, PROBE TILES ARE NOT. rules.md 5.2: 'The "
    "table watches each touch and sees it pull, push, or do nothing -- but "
    "nobody except you knows which tiles you used.' The public log carries "
    "the mouth and the pull/push/nothing sequence; only the prober's own "
    "observation carries what it means.",

    "A9 A TWO-TOUCH PROBE USES TWO DIFFERENT KINDS. rules.md 5.2 allows one "
    "or two tiles and says 'a second touch with a different kind of tile "
    "always settles it'. A second touch with the same kind repeats the "
    "first answer, so the engine lists two-touch probes only for pairs of "
    "distinct kinds -- it removes strictly dominated duplicates, not "
    "options.",

    "A10 A BLOCKED KICK STILL FIRES AND STILL SPENDS THE ONE KICK. rules.md "
    "5.1 step 5 says to find the FIRST kick scanning from the near mouth "
    "and that 'only one kick fires per push'; it never exempts a kick whose "
    "launched body is already flush against the next tile and therefore "
    "moves zero slots. The engine fires it, captures nothing, and does NOT "
    "look for a later kick -- so a dead-blocked kick near the mouth shields "
    "every live kick behind it. This is a real tactical rule and rules.md "
    "should say it out loud.",

    "A11 A WELDED BODY LEAVES WHOLE ON A SHOVE TOO. rules.md 5.1's physical "
    "rulings say 'A welded body leaves the rail whole as soon as any part "
    "of it clears the far mouth'. Applied to the one-slot shove of a packed "
    "rail: if the far-mouth tile is welded to its neighbour, the whole "
    "welded chain leaves as one body (2+ tiles for a single shove) and the "
    "slots it vacated stay empty. rules.md only spells this out for "
    "launches.",

    "A12 A LAUNCHED BODY EXITS ENTIRELY OR NOT AT ALL. rules.md 5.1: the "
    "body 'slides toward the far mouth until its leading tile either leaves "
    "the rail or comes to rest in the slot next to the next tile', plus the "
    "finger ruling that a stalled body is slid out. So if no tile lies "
    "beyond the launched body, EVERY tile of it leaves the rail; if one "
    "does, the body shunts flush against it and nothing leaves. There is no "
    "partial exit.",

    "A13 WELDS ARE DERIVED, NOT STORED. A CLAMP joint welds, welded tiles "
    "stay adjacent forever, and a pair of touching faces that clamps can "
    "never later read as anything else (faces never change). So 'welded' is "
    "exactly 'currently adjacent with a CLAMP joint', which the engine "
    "computes from the faces. Equivalent to rules.md 5 and impossible to "
    "desync.",

    "A14 A PUSH ALWAYS SPENDS THE TILE AND THE TILE ALWAYS STAYS. rules.md "
    "5.1: 'The tile is spent whatever happens, and it stays in the rail.' "
    "Including the empty-rail push, where it travels the length of the "
    "channel to slot 10 (rules.md 8) and cannot fall out.",

    "A15 EVERY TILE THAT LEAVES ON YOUR PUSH IS YOURS. Including tiles of "
    "your own colour, which sit in your tray at 0 points (rules.md 6). The "
    "engine never lets a player decline a capture.",

    "A16 NO PHYSICAL MISHAPS. The engine models perfectly clean play: no "
    "crooked tile to straighten, no tile jumping the rail sideways, no disc "
    "falling out of its pocket, no clamped pair pulled apart, no rail "
    "touched out of turn, no tile re-loaded (rules.md 5.1 physical rulings "
    "and 8). Registered because no number this sim produces tests any of "
    "those rulings.",

    "A17 WINNERS() ALWAYS RETURNS EXACTLY ONE SEAT. rules.md 7 ends with "
    "'Seating... This always resolves', so a draw is impossible by rule. "
    "'Furthest clockwise from the start player' is read as the largest "
    "(seat - start) mod n, i.e. the seat immediately before the start "
    "player. Decisiveness measured on this engine is 1.0 by construction, "
    "not by drama.",

    "A18 PROBE LEGALITY IS ABOUT THE MOUTH SLOT ITSELF. rules.md 5.2: 'if "
    "the mouth slot you named is empty, you may not probe there'. So mouth "
    "A needs a tile in absolute slot 1 and mouth B needs one in absolute "
    "slot 10 -- a tile sitting deeper in the rail is not probeable, even "
    "with an otherwise open channel.",

    "A19 A PUSH IS NEVER REFUSED. rules.md 4: 'You may always Push while you "
    "have a tile in your rack.' Both mouths are always available, a full "
    "rail simply shoves a tile out (rules.md 8), and no legal-move list "
    "ever omits a push a seat can pay for.",

    "A20 IDEA.JSON WAS SUPERSEDED BY RULES.MD. idea.json describes 7 tiles "
    "plus 2 blanks, an alternative turn that tests a CAPTURED tile behind "
    "your screen, and attract/repel resolution with tiles shed off the far "
    "end. rules.md ships 12/10/9-tile hands with steel slugs, a chip-paid "
    "Probe against a rail mouth, and the KICK/CLAMP/slack joint table. The "
    "engine implements rules.md, which is the ruled artifact.",

    "A21 THE PROBE NEVER MAKES A JOINT AND NEVER MOVES THE RAIL. rules.md "
    "5.2: 'a probe never makes a joint', and a mouth tile nudged by the "
    "probe is slid back. So a Probe changes exactly two things: the "
    "prober's chip count and the prober's private knowledge.",

    "A22 END OF ROUND IS EQUAL TURNS. A rack emptying arms the ending; the "
    "game stops once the seat immediately before the start player has "
    "moved, so every seat has taken the same number of turns (rules.md 6). "
    "Two racks emptying in the same round changes nothing (rules.md 8).",
]


# --- geometry helpers -------------------------------------------------------

def _rel_line(rail, end):
    """Rail as a near-mouth-first list for a push into ``end``.

    Entries are ``(tile_id, rhd)`` with rhd -1 = head faces the NEAR mouth,
    +1 = head faces the FAR mouth. rules.md 5.1 step 1 renumbers the slots
    from whichever mouth is being pushed into; this is that renumbering.
    """
    if end == "A":
        return [None if e is None else (e[0], e[1]) for e in rail]
    return [None if e is None else (e[0], -e[1]) for e in reversed(rail)]


def _abs_line(line, end):
    """Inverse of _rel_line: near-mouth-first list back to absolute slots."""
    if end == "A":
        return tuple(None if e is None else (e[0], e[1]) for e in line)
    return tuple(None if e is None else (e[0], -e[1])
                 for e in reversed(line))


def _far_face(entry, tiles):
    """Disc kind on the face this entry presents toward the far mouth, or
    None for a bare face."""
    return tiles[entry[0]][1] if entry[1] == 1 else None


def _near_face(entry, tiles):
    """Disc kind on the face this entry presents toward the near mouth."""
    return tiles[entry[0]][1] if entry[1] == -1 else None


def _joint_of(left_face, right_face):
    """The rules.md 5 joint table, as one function.

    KICK  = two like poles.  CLAMP = two discs that are not like poles and
    not both steel.  slack = anything touching a bare face, and steel-steel.
    """
    if left_face is None or right_face is None:
        return "slack"
    if left_face == "STEEL" and right_face == "STEEL":
        return "slack"
    if left_face == right_face:
        return "KICK"
    return "CLAMP"


def _line_joint(line, i, tiles):
    """Joint between line[i] and line[i+1], or None if they do not touch."""
    a, b = line[i], line[i + 1]
    if a is None or b is None:
        return None
    return _joint_of(_far_face(a, tiles), _near_face(b, tiles))


def _weld_run_at_far_end(line, tiles):
    """How many tiles leave with the far-mouth tile when it is shoved out.

    The far-mouth tile plus every tile welded to it in an unbroken CLAMP
    chain toward the near mouth (A11).
    """
    size = 1
    i = N_SLOTS - 1
    while i - 1 >= 0 and _line_joint(line, i - 1, tiles) == "CLAMP":
        size += 1
        i -= 1
    return size


# --- the push, in near-mouth-relative coordinates ---------------------------

def _resolve_push(line, tiles, tid, rhd):
    """Drive one tile home and let the rail resolve itself (rules.md 5.1).

    ``line`` is near-mouth-first; ``rhd`` is +1 for head-first (head leads
    into the rail) and -1 for tail-first (head left facing out of the near
    mouth). Returns ``(new_line, captured_tile_ids, events)``. Pure: builds
    a new list.
    """
    line = list(line)
    captured = []
    events = []

    if line[0] is None:
        # Slides in until it touches the first tile it meets; if the rail is
        # empty it runs all the way to slot 10 (rules.md 5.1 / 8, A14).
        first = None
        for k in range(N_SLOTS):
            if line[k] is not None:
                first = k
                break
        pos = N_SLOTS - 1 if first is None else first - 1
        line[pos] = (tid, rhd)
        events.append("entered slot %d" % (pos + 1))
    else:
        # No room: shove the contiguous run one slot toward the far mouth.
        q = 0
        while q + 1 < N_SLOTS and line[q + 1] is not None:
            q += 1
        if q == N_SLOTS - 1:
            w = _weld_run_at_far_end(line, tiles)
            leaving = [line[k] for k in range(N_SLOTS - w, N_SLOTS)]
            body = line[0:N_SLOTS - w]
            line = [None] * N_SLOTS
            for idx, ent in enumerate(body):
                line[idx + 1] = ent
            captured.extend(e[0] for e in leaving)
            events.append("shoved %d tile(s) out of the far mouth" % w)
        else:
            body = line[0:q + 1]
            for k in range(q + 1):
                line[k] = None
            for idx, ent in enumerate(body):
                line[idx + 1] = ent
            events.append("shoved the line one slot")
        line[0] = (tid, rhd)

    # Resolve: first KICK scanning from the near mouth outward (rules.md 5.1
    # step 5). Exactly one fires, blocked or not (A10).
    kick = None
    for i in range(N_SLOTS - 1):
        if _line_joint(line, i, tiles) == "KICK":
            kick = i
            break
    if kick is None:
        events.append("no kick")
        return line, captured, events

    start = kick + 1
    last = start
    while last + 1 < N_SLOTS and line[last + 1] is not None:
        last += 1
    beyond = None
    for k in range(last + 1, N_SLOTS):
        if line[k] is not None:
            beyond = k
            break

    events.append("KICK at the slot %d|%d joint" % (kick + 1, kick + 2))
    if beyond is None:
        # Nothing in the way: the whole launched body leaves the rail (A12).
        for k in range(start, last + 1):
            captured.append(line[k][0])
            line[k] = None
        events.append("launched %d tile(s) out of the far mouth"
                      % (last - start + 1))
    else:
        shift = beyond - 1 - last
        if shift > 0:
            body = [line[k] for k in range(start, last + 1)]
            for k in range(start, last + 1):
                line[k] = None
            for idx, ent in enumerate(body):
                line[start + shift + idx] = ent
            events.append("launched body shunted %d slot(s), nothing left "
                          "the rail" % shift)
        else:
            events.append("launched body was already flush; nothing moved")
    return line, captured, events


# --- probe ------------------------------------------------------------------

def _touch(probe_kind, face_kind):
    """What the table sees when a probe tile's head meets a face (5.2)."""
    if face_kind is None:
        return "nothing"
    if probe_kind == "STEEL":
        return "pull" if face_kind in ("N", "S") else "nothing"
    if probe_kind == face_kind:
        return "push"
    return "pull"


def _mouth_slot(end):
    return 0 if end == "A" else N_SLOTS - 1


def _outward_face(state, end):
    """Disc kind on the face the mouth tile presents out of ``end``, or None
    for a bare face. Caller has checked the mouth slot is occupied."""
    entry = state["rail"][_mouth_slot(end)]
    tid, hd = entry
    outward = -1 if end == "A" else 1
    return state["tiles"][tid][1] if hd == outward else None


# --- state ------------------------------------------------------------------

def _blank_state(n_players, seed):
    rng = random.Random(seed)
    start = rng.randrange(n_players)
    hand, magnets, steel = HANDS[n_players]
    return {
        "n": n_players,
        "seed": seed,
        "rng": rng.getstate(),
        "hand": hand,
        "magnets": magnets,
        "steel": steel,
        "phase": "setup",
        "start": start,
        "to_move": start,
        "round": 0,
        "turn": 0,
        "pending_end": False,
        "rail": tuple([None] * N_SLOTS),
        "tiles": {},
        "racks": tuple((0, 0, 0) for _ in range(n_players)),
        "chips": tuple(CHIPS_PER_PLAYER for _ in range(n_players)),
        "trays": tuple(() for _ in range(n_players)),
        "beliefs": tuple({} for _ in range(n_players)),
        "serial": tuple(0 for _ in range(n_players)),
        "log": (),
    }


def new_game(n_players, seed):
    """Fresh game. Deterministic in ``seed`` (which only picks the start seat).

    Play opens in the setup phase: each seat, in turn order from the start
    player, secretly chooses how many of its magnets face N (A1).
    """
    if n_players not in HANDS:
        raise ValueError("Kick seats 2-4 players (rules.md 3.3), not %r"
                         % (n_players,))
    return _blank_state(n_players, seed)


def player_to_move(state):
    return state["to_move"]


def is_over(state):
    return state["phase"] == "over"


def _rack_total(rack):
    return rack[0] + rack[1] + rack[2]


def _log(state, line):
    return (state["log"] + (line,))[-14:]


def legal_moves(state):
    """Every legal move for the seat to move; [] only when the game is over.

    Setup: ('load', n_N) for every split of your magnets.
    Play:  ('push', mouth, disc kind, 'head'|'tail')   -- up to 12
           ('probe', mouth, kind)                      -- one touch
           ('probe', mouth, kind_a, kind_b)            -- two touches (A9)
           ('pass',)                                   -- empty rack only (A4)
    """
    if state["phase"] == "over":
        return []
    seat = state["to_move"]
    if state["phase"] == "setup":
        return [("load", k) for k in range(state["magnets"] + 1)]

    rack = state["racks"][seat]
    have = [KINDS[i] for i in range(3) if rack[i] > 0]
    moves = []
    for end in ENDS:                       # A19: a push is never refused
        for kind in KINDS:
            if kind not in have:
                continue
            for orient in ORIENTS:
                moves.append(("push", end, kind, orient))
    if state["chips"][seat] > 0 and have:
        for end in ENDS:
            if state["rail"][_mouth_slot(end)] is None:
                continue                    # A18: the mouth SLOT must hold a tile
            for kind in have:
                moves.append(("probe", end, kind))
            for i in range(len(have)):
                for j in range(i + 1, len(have)):
                    moves.append(("probe", end, have[i], have[j]))
    if not moves:
        moves.append(("pass",))
    return moves


def _advance(new, seat):
    """Close a turn: arm the ending if a rack emptied, then pass the seat on."""
    if _rack_total(new["racks"][seat]) == 0:
        new["pending_end"] = True
    nxt = (seat + 1) % new["n"]
    new["to_move"] = nxt
    new["turn"] = new["turn"] + 1
    if nxt == new["start"]:
        new["round"] = new["round"] + 1
        if new["pending_end"] or new["round"] >= SAFETY_ROUND_CAP:
            new["phase"] = "over"
    return new


def apply(state, move):
    """Return a NEW state with ``move`` played. Never mutates ``state``."""
    if state["phase"] == "over":
        raise ValueError("the game is over; no move is legal")
    seat = state["to_move"]
    new = dict(state)

    if state["phase"] == "setup":
        if not (isinstance(move, tuple) and move and move[0] == "load"):
            raise ValueError("setup expects a ('load', n_N) move, got %r"
                             % (move,))
        n_north = move[1]
        if not 0 <= n_north <= state["magnets"]:
            raise ValueError("cannot face %r of %d magnets north"
                             % (n_north, state["magnets"]))
        racks = list(state["racks"])
        racks[seat] = (n_north, state["magnets"] - n_north, state["steel"])
        new["racks"] = tuple(racks)
        new["log"] = _log(state, "P%d loaded a rack behind the screen" % seat)
        nxt = (seat + 1) % state["n"]
        new["to_move"] = nxt
        new["turn"] = state["turn"] + 1
        if nxt == state["start"]:
            new["phase"] = "play"
        return new

    kind = move[0]

    if kind == "pass":
        new["log"] = _log(state, "P%d passed (empty rack)" % seat)
        return _advance(new, seat)

    if kind == "push":
        _, end, disc, orient = move
        idx = KINDS.index(disc)
        rack = state["racks"][seat]
        if rack[idx] <= 0:
            raise ValueError("P%d has no %s tile left" % (seat, disc))
        racks = list(state["racks"])
        racks[seat] = tuple(
            rack[i] - 1 if i == idx else rack[i] for i in range(3))

        tid = "P%d-%02d" % (seat, state["serial"][seat])
        tiles = dict(state["tiles"])
        tiles[tid] = (seat, disc)
        serial = list(state["serial"])
        serial[seat] += 1

        rhd = 1 if orient == "head" else -1
        line, captured, events = _resolve_push(
            _rel_line(state["rail"], end), tiles, tid, rhd)

        trays = list(state["trays"])
        trays[seat] = trays[seat] + tuple(captured)

        new["racks"] = tuple(racks)
        new["tiles"] = tiles
        new["serial"] = tuple(serial)
        new["rail"] = _abs_line(line, end)
        new["trays"] = tuple(trays)
        foreign = sum(1 for t in captured if tiles[t][0] != seat)
        new["log"] = _log(state, "P%d pushed %s-first into mouth %s: %s%s"
                          % (seat, orient, end, "; ".join(events),
                             (" [%d tile(s) to P%d's tray, %d scoring]"
                              % (len(captured), seat, foreign))
                             if captured else ""))
        return _advance(new, seat)

    if kind == "probe":
        end = move[1]
        probes = list(move[2:])
        if state["chips"][seat] <= 0:
            raise ValueError("P%d has no probe chip left" % seat)
        if state["rail"][_mouth_slot(end)] is None:
            raise ValueError("mouth %s slot is empty; nothing to probe" % end)
        face = _outward_face(state, end)
        tid = state["rail"][_mouth_slot(end)][0]

        results = [_touch(p, face) for p in probes]
        beliefs = list(state["beliefs"])
        mine = dict(beliefs[seat])
        if face is not None:
            # A6: a bare outward face teaches nothing (the notch already
            # showed it). Narrow only when a head is presented.
            cands = list(mine.get(tid, KINDS))
            for probe_kind, saw in zip(probes, results):
                cands = [c for c in cands if _touch(probe_kind, c) == saw]
            mine[tid] = tuple(cands)
        beliefs[seat] = mine

        chips = list(state["chips"])
        chips[seat] -= 1
        new["chips"] = tuple(chips)
        new["beliefs"] = tuple(beliefs)
        new["log"] = _log(state, "P%d probed mouth %s: %s"
                          % (seat, end, ", ".join(results)))
        return _advance(new, seat)

    raise ValueError("unknown move %r" % (move,))


# --- outcome ----------------------------------------------------------------

def _points(state, seat):
    """rules.md 6: 1 point per captured tile that is not your colour."""
    tiles = state["tiles"]
    return sum(1 for t in state["trays"][seat] if tiles[t][0] != seat)


def _own_in_rail(state, seat):
    tiles = state["tiles"]
    return sum(1 for e in state["rail"] if e is not None
               and tiles[e[0]][0] == seat)


def _own_fed(state, seat):
    """Your colour sitting in somebody else's tray (tiebreak 2)."""
    tiles = state["tiles"]
    total = 0
    for other in range(state["n"]):
        if other == seat:
            continue
        total += sum(1 for t in state["trays"][other] if tiles[t][0] == seat)
    return total


def winners(state):
    """[] while running; exactly one seat when over (rules.md 7, A17)."""
    if state["phase"] != "over":
        return []
    n = state["n"]
    start = state["start"]
    ranked = sorted(
        range(n),
        key=lambda s: (-_points(state, s),
                       _own_in_rail(state, s),
                       _own_fed(state, s),
                       -state["chips"][s],
                       -((s - start) % n)))
    return [ranked[0]]


def _threat(state, seat):
    """Foreign tiles this seat could plausibly blow out of the rail now.

    A cheap proxy read off the CURRENT rail from each mouth: (a) if the
    mouth slot is occupied and the run reaches the far mouth, any push into
    that mouth shoves the far-end welded body out (A11); (b) the first live
    kick from that mouth launches its body out of the rail if nothing lies
    beyond it (A12). Counts only tiles that are not this seat's colour --
    own tiles are worth 0 (rules.md 6). It ignores the joints the pushed
    tile itself would make (that depends on a hidden rack), so it is a
    lower-bound sniff, not a search.
    """
    tiles = state["tiles"]
    best = 0
    for end in ENDS:
        line = _rel_line(state["rail"], end)
        gain = 0
        if line[0] is not None:
            q = 0
            while q + 1 < N_SLOTS and line[q + 1] is not None:
                q += 1
            if q == N_SLOTS - 1:
                w = _weld_run_at_far_end(line, tiles)
                gain += sum(1 for k in range(N_SLOTS - w, N_SLOTS)
                            if tiles[line[k][0]][0] != seat)
        kick = None
        for i in range(N_SLOTS - 1):
            if _line_joint(line, i, tiles) == "KICK":
                kick = i
                break
        if kick is not None:
            start = kick + 1
            last = start
            while last + 1 < N_SLOTS and line[last + 1] is not None:
                last += 1
            if not any(line[k] is not None
                       for k in range(last + 1, N_SLOTS)):
                gain += sum(1 for k in range(start, last + 1)
                            if tiles[line[k][0]][0] != seat)
        best = max(best, gain)
    return best


def scores(state):
    """Progress toward winning, per seat, every turn.

    Banked points dominate (1.0 each, exactly what wins the game). The rest
    are small and move on ordinary turns so the trace is not flat:
      +0.10 per foreign tile currently blowable out of the rail (_threat)
      -0.04 per own-colour tile still in the rail   (tiebreak 1, and it is
            ammunition for everyone else)
      -0.03 per own-colour tile in somebody else's tray (tiebreak 2)
      +0.01 per unspent probe chip                  (tiebreak 3)
    """
    out = []
    for seat in range(state["n"]):
        value = float(_points(state, seat))
        value += W_THREAT * _threat(state, seat)
        value -= W_OWN_IN_RAIL * _own_in_rail(state, seat)
        value -= W_OWN_FED * _own_fed(state, seat)
        value += W_CHIP * state["chips"][seat]
        out.append(value)
    return out


# --- observation ------------------------------------------------------------

def _colour(seat):
    return ("ORANGE", "BLUE", "GREEN", "PURPLE")[seat]


def _tile_label(state, seat, tid):
    """How ``seat`` may describe the tile ``tid`` sitting in the rail."""
    owner, kind = state["tiles"][tid]
    if owner == seat:
        return "your %s tile" % kind
    known = state["beliefs"][seat].get(tid)
    if known is not None and len(known) == 1:
        return "%s's tile (you probed it: %s)" % (_colour(owner), known[0])
    if known is not None:
        return "%s's tile (you probed it: %s)" % (
            _colour(owner), " or ".join(known))
    return "%s's tile (disc unknown)" % _colour(owner)


def observation(state, seat):
    """Everything this seat may know, as prose. Hidden info stays hidden."""
    n = state["n"]
    hand, magnets, steel = HANDS[n]
    lines = []
    lines.append(
        "KICK -- %d players. You are seat %d (%s). Start player: seat %d."
        % (n, seat, _colour(seat), state["start"]))
    lines.append(
        "Public setup: every player loaded %d tiles -- %d magnets (each one "
        "N-out or S-out, their secret) and %d steel slugs -- and holds %d "
        "probe chips." % (hand, magnets, steel, CHIPS_PER_PLAYER))

    if state["phase"] == "setup":
        lines.append(
            "SETUP. Choose how many of your %d magnets face N (the rest face "
            "S). Nobody sees your split. Steel slugs are fixed at %d."
            % (magnets, steel))
        lines.append(
            "A steel tile can never kick and can never be kicked -- it is "
            "the bluff. Two like poles meeting is the only thing that fires.")
        return "\n".join(lines)

    if state["phase"] == "over":
        lines.append("GAME OVER after %d rounds." % state["round"])
    else:
        lines.append(
            "Round %d. %s The game ends at the end of the round any rack "
            "empties.%s"
            % (state["round"] + 1,
               "It is your turn." if state["to_move"] == seat
               else "Seat %d to move." % state["to_move"],
               " (The ending is ARMED: a rack is empty -- this is the last "
               "round.)" if state["pending_end"] else ""))

    rack = state["racks"][seat]
    lines.append(
        "Your rack (secret): %d N, %d S, %d STEEL = %d tiles. Your chips: %d."
        % (rack[0], rack[1], rack[2], _rack_total(rack),
           state["chips"][seat]))

    lines.append("Rail, slot 1 (mouth A) to slot 10 (mouth B):")
    rail = state["rail"]
    for i in range(N_SLOTS):
        entry = rail[i]
        if entry is None:
            lines.append("  slot %2d: empty" % (i + 1))
            continue
        tid, hd = entry
        facing = "mouth A (slot 1)" if hd == -1 else "mouth B (slot 10)"
        lines.append("  slot %2d: %s, head points at %s"
                     % (i + 1, _tile_label(state, seat, tid), facing))
    joints = []
    for i in range(N_SLOTS - 1):
        kindj = _line_joint(list(rail), i, state["tiles"])
        if kindj is None:
            continue
        note = {"KICK": "KICK -- LIVE, the next push that squeezes it from "
                        "the near side fires it",
                "CLAMP": "CLAMP -- welded, dead forever",
                "slack": "slack -- nothing"}[kindj]
        joints.append("  slots %d|%d: %s" % (i + 1, i + 2, note))
    if joints:
        lines.append("Joints in the rail (public -- the whole table saw each "
                     "one form):")
        lines.extend(joints)
    else:
        lines.append("No two tiles are touching, so there are no joints.")

    lines.append("Trays (public) and racks (counts public, contents secret):")
    for s in range(n):
        tray = state["trays"][s]
        foreign = _points(state, s)
        breakdown = {}
        for t in tray:
            owner = state["tiles"][t][0]
            breakdown[owner] = breakdown.get(owner, 0) + 1
        detail = ", ".join(
            "%d %s" % (breakdown[o], _colour(o)) for o in sorted(breakdown))
        lines.append(
            "  seat %d (%s)%s: tray %d tile(s)%s = %d point(s); rack %d "
            "tile(s) left; %d chip(s)"
            % (s, _colour(s), " <- you" if s == seat else "", len(tray),
               " [%s]" % detail if detail else "", foreign,
               _rack_total(state["racks"][s]), state["chips"][s]))

    if state["log"]:
        lines.append("Recent public events:")
        for entry in state["log"]:
            lines.append("  " + entry)

    lines.append(
        "Reminders: joints are decided by the two TOUCHING faces only. Like "
        "poles KICK (everything past the break is launched toward the far "
        "mouth and any tile that leaves is yours). Opposite poles, or a "
        "magnet against steel, CLAMP and weld forever. A bare tail face, or "
        "steel against steel, is slack. Only the FIRST kick from the mouth "
        "you push into fires, and only one per push. Captured tiles of your "
        "own colour are worth 0.")
    return "\n".join(lines)
