"""CLEARANCE (g0003) — playtest engine.

A limbo contest for solid objects. The bar descends by clicks only the
setter can count; every player commits one block from their own stock in
secret; the tallest block that passes under the bar without touching it
wins the round and joins the winner's score line. Longest line wins.

Implemented from ``toys/g0003/rules.md`` (the complete spec) and bound by
IDEA_SHA to ``toys/g0003/idea.json``. Where the two disagree the RULES.md
text is implemented and the disagreement is registered in ASSUMPTIONS.

INTERNAL UNITS
    Every height in this module is an integer number of QUARTER-MILLIMETRES.
    RULES.md §2 puts bar heights on the 0.5 mm grid and block heights on
    that grid plus 0.25 mm, so quarter-mm integers make every comparison
    exact and make "a block is never exactly level with the bar" a
    structural fact rather than a float tolerance.

    bar start  132 (33.0 mm, the hard top stop)
    bar bottom  70 (17.5 mm, 31 clicks below)
    one click    2 (0.5 mm)
    blocks      49..131 odd-in-quarters (12.25 .. 32.75 mm)

MOVE VOCABULARY (stable, comparable, deterministically ordered)
    ("set", 5) ("set", 6) ("set", 7)   — the Set: down N then up 8-N
    ("commit", owner, idx)             — put that block under your cup
    ("salvage", "take" | "decline")    — empty-rail salvage at end of Take
"""

import random

IDEA_SHA = "7c9e97158114faeaf28d90b9cde69db96f3cfebf586902d81158ba6878b71ada"

ASSUMPTIONS = [
    "A1 IDEA/RULES CONTRADICTION (block ladder). idea.json says heights are "
    "'randomised across a 0.4 mm ladder from 18 to 30 mm'; RULES.md §2 says "
    "'H is drawn from a 42-rung ladder: 12.25, 12.75, 13.25 ... 32.75 mm, in "
    "0.5 mm steps'. Range and step both differ. The engine implements "
    "RULES.md (it is the complete spec and its numbers are internally "
    "consistent with the 33.0 mm top stop and the 17.5 mm bottom stop). The "
    "idea.json pitch line is stale and should be reconciled.",

    "A2 IDEA/RULES CONTRADICTION (end condition). idea.json says 'Play until "
    "one stock is empty'; RULES.md §6 says 'The game ends at the end of the "
    "round in which the setter says \"Bottom\"' and §5.7 adds Salvage "
    "specifically so an empty rail does NOT end the game. The engine "
    "implements the RULES.md Bottom ending. This is a different core loop "
    "from the pitch and changes game length materially.",

    "A3 FIRST SETTER. RULES.md §3.5 picks the first setter by a table ritual "
    "('most recently used a ruler ... if nobody remembers, the youngest'), "
    "which no engine can model. The engine draws the first setter uniformly "
    "from the seed. Pinning it to seat 0 instead would hand seat 0 the "
    "round-1 private information in every game.",

    "A4 SET ASSIGNMENT AND POCKET ORDER. RULES.md §3.6 has players pick one "
    "of the five printed sets clockwise, the first setter last. The choice "
    "is uninformed (blocks are unmarked and cannot be handled before they "
    "are yours), so the engine assigns n of the 5 sets uniformly from the "
    "seed rather than modelling a decision with no information in it. "
    "Position within the rail ('in whatever order you like', §2) is also "
    "randomised, because the empty pocket is public (§5.2) and a pocket "
    "index correlated with height would leak hidden information.",

    "A5 SIMULTANEOUS COMMIT, SEQUENTIALISED. RULES.md §5.2 is simultaneous "
    "and the engine contract is turn-based, so the Commit is played as one "
    "move per seat. Two consequences are handled explicitly: (a) commit "
    "order rotates by round from a seeded starting phase, rather than "
    "following the §4 play order, so neither a seat nor a standing "
    "systematically commits last (a fixed phase measurably favoured the "
    "seat that drew the last slot most often at 3 players); (b) "
    "observation() never shows a seat what an earlier "
    "committer of the same round chose. Sequentialising a simultaneous "
    "choice cannot be made perfectly information-free — a state-reading bot "
    "moving last in a round sees more than a human would.",

    "A6 THE PASS IS RESOLVED AT ONCE. RULES.md §5.4 slides blocks one at a "
    "time in play order, but under the contact model in A7 no pass can "
    "affect any other pass: clearing depends only on that block's height vs "
    "the bar, and a scrapped block leaves the bar's setting unchanged "
    "('the bar height is unchanged, because the screw holds its setting', "
    "§5.4). The engine therefore resolves all passes simultaneously and "
    "never needs a pass order. This also closes the round-1 play-order gap "
    "(§4 orders play by score line, but every line is empty in round 1 and "
    "the tiebreak chain ends at 'clockwise from the previous setter', who "
    "does not exist yet) — RULES.md should still state it for humans.",

    "A7 CONTACT MODEL. A block clears if and only if its height is strictly "
    "less than the bar height; otherwise it is scrapped. Equality is "
    "impossible by the 0.25 mm offset in §2, so 'the smallest possible "
    "margin, either way, is 0.25 mm' is exact here. NO EXECUTION ERROR IS "
    "MODELLED: the §5.4 'failed execution' and 'gantry knocked' clauses "
    "scrap a block for a player mistake, and the fumble rate of a human "
    "finger is not a rules quantity. The engine's fumble rate is zero, so "
    "every number it produces is the no-fumble limit of the real game.",

    "A8 BOTTOM TRIGGER. RULES.md §5.1 says Bottom is called 'if the screw "
    "hits the bottom stop during the Set'. The engine treats the down-phase "
    "reaching the stop EXACTLY as hitting it (the screw is against the "
    "stop, and §8 confirms a hit on the very first click still counts). So "
    "with R clicks of room and a down-phase of D, Bottom fires when D >= R.",

    "A9 PATTERN AS AN END-TIMING LEVER. §5.1 frames the three patterns as "
    "depth only ('Down 5 then up 3 / Down 6 then up 2 / Down 7 then up 1'), "
    "but their down-phases differ (5, 6, 7), so with 5-7 clicks of room the "
    "pattern chosen decides whether Bottom fires this round. The engine "
    "implements this literally — it falls out of A8 — and registers it "
    "because RULES.md never tells the setter this second effect exists.",

    "A10 SALVAGE IS RE-OFFERED. §5.7 says 'If your rail is empty at the end "
    "of The Take and the game is not over, you may take the shortest block "
    "out of your own score line' — a per-round test. It also says you may "
    "'decline and simply sit out the remaining rounds', which reads as "
    "permanent. The engine rules declining NON-BINDING: the option returns "
    "every round while the rail is empty and the line is not.",

    "A11 SALVAGE ORDER. §5.7 never orders simultaneous salvages. The engine "
    "resolves them in ascending seat order starting from the current setter. "
    "Order cannot change any outcome (each salvage touches only its own "
    "line and rail) but it must be fixed to keep replays identical.",

    "A12 TIED TALLEST SCRAPPED. §8 gives the round winner the choice when "
    "two scrapped blocks tie for tallest. Both options add the same height "
    "to the line, so the engine auto-resolves to the lowest (owner, pocket) "
    "instead of emitting a decision with no consequence.",

    "A13 CLOCKWISE AND 'LEFT'. Seats are numbered clockwise; the player to "
    "seat X's left is seat (X+1) mod n. The §4 setter tiebreak 'the first of "
    "them going clockwise from the previous setter's left' therefore starts "
    "at (previous setter + 1) mod n. The §7 final tiebreak 'closest going "
    "clockwise from the last setter, starting with the last setter' starts "
    "at the last setter itself.",

    "A14 EVERY SEAT OUT. §8 says a player with an empty rail AND an empty "
    "line is out and is 'skipped for setter and for play order', while 'the "
    "game still runs to the Bottom round'. If EVERY seat is out there is no "
    "one left to Set and RULES.md names no substitute. The engine ends the "
    "game immediately in that case. Seats that are out are still ranked at "
    "the end (their line is 0 mm, so they can only place first if every "
    "line is empty, which the §7 tiebreak chain resolves).",

    "A15 ESTIMATION ERROR. The whole game is estimating heights by eye, and "
    "RULES.md gives no model of how wrong an eye is. observation() shows a "
    "seat NO exact millimetre value. It shows: an exact fingernail ordering "
    "(§5.5) of everything that seat may handle, and a seeded eyeball read of "
    "each such height and of the current gap, good to about +/- 1.0 mm. The "
    "reads are deterministic in the game seed and are re-sorted so they can "
    "never contradict the fingernail ordering.",

    "A16 BAR KNOWLEDGE. A seat is credited with exactly what §5.1 and §3.3 "
    "make public: the bar starts at the hard top stop, every Set nets 1.0, "
    "2.0 or 3.0 mm down, and a setter knows its own drop exactly. "
    "observation() reports the resulting bounds per seat plus the eyeball "
    "read from A15. A 'Bottom' call pins the bar at 17.5 mm for everyone.",

    "A17 SCORE HEURISTIC (not a rule). scores() = score-line length in mm + "
    "0.20 * live stock, where live stock sums the heights of the blocks in "
    "that seat's rail (plus its committed-but-unresolved block) that are "
    "STILL SHORTER THAN THE BAR. The bar never rises (§6), so a block "
    "taller than the bar is permanently dead and RULES.md says so ('a block "
    "that cleared at a given gap will clear anything above it', §8). The "
    "term therefore tracks real progress: it drops when the bar cuts past "
    "your stock, drops when you scrap, and jumps when you take a round. At "
    "game end the term is dropped so scores() equals the final line lengths.",

    "A18 NOBODY TAKES ON A TIE. §5.6: when clearing blocks tie for tallest, "
    "'all of the tied blocks are scrapped, nobody wins the round, and "
    "nobody takes anything — including the scrapped blocks'. The engine "
    "leaves every scrapped block of that round in the well, including the "
    "tallest, and shorter clearing blocks still return to their rails (§8).",

    "A19 PUBLIC LINE LENGTHS. Score lines are physical objects on the table: "
    "the ORDER of the lines is exactly determinable (lay them together, "
    "fingernail the far ends, §6) but no player can read a millimetre total. "
    "observation() gives the exact ordering and lengths rounded to the "
    "nearest 5 mm, so a one-block line does not leak that block's height.",

    "A20 SALVAGED BLOCKS CHANGE HANDS. A block won from the scrap well "
    "belongs to the winner's line and, if salvaged (§5.7), enters the "
    "winner's rail and is committed by them from then on. The engine tracks "
    "every block as (printed set, pocket) so its identity stays public even "
    "after it changes hands.",

    "A21 UNMODELLED PENALTIES. Three RULES.md clauses punish physical "
    "misbehaviour and have no engine analogue: early exposure of a block "
    "(§5.2, forced to commit the shortest block instead), a false 'Bottom' "
    "call (§5.1/§8, the caller's whole line is scrapped), and a re-run of "
    "the count when commits were not simultaneous (§5.2). None are "
    "simulated, so the engine measures a table that never cheats or fumbles.",
]

# --- Constants ---------------------------------------------------------------

#: Quarter-millimetres per millimetre. Every internal height is in these.
Q = 4

BAR_START = 132   # 33.0 mm — the hard top stop (§3.3)
BAR_BOTTOM = 70   # 17.5 mm — 31 clicks below (§3.3)
CLICK = 2         # 0.5 mm per detented click (§2)

#: The 42-rung block ladder, 12.25 .. 32.75 mm in 0.5 mm steps (§2).
LADDER = tuple(range(49, 132, 2))
BLOCKS_PER_SET = 6
N_SETS = 5
MIN_INTRA_SET_GAP = 4    # "no two blocks within a set closer than 1.0 mm"
TALL_FLOOR = 113         # "at least one block above 28 mm"
SHORT_CEIL = 67          # "at least one block below 17 mm"

#: (down clicks, up clicks) — the three Sets of §5.1. Net drop = down - up.
PATTERNS = ((5, 3), (6, 2), (7, 1))

SET_LETTERS = ("a", "b", "c", "d", "e")
SET_SYMBOLS = ("circle", "square", "triangle", "cross", "bar")

#: Weight on live stock in scores(). See A17.
STOCK_WEIGHT = 0.20

#: Eyeball noise in quarter-mm, drawn per (seat, thing) from the game seed.
EYE_NOISE = (-4, -2, -2, 0, 0, 0, 0, 2, 2, 4)


# --- Setup -------------------------------------------------------------------

def _draw_set(rng):
    """Six heights for one printed set, honouring every §2 constraint.

    Rejection sampling: the constraints (1.0 mm minimum separation, one
    block above 28 mm, one below 17 mm) accept roughly a third of naive
    draws, so this is a handful of tries, and it keeps the constraint text
    readable next to the rules it comes from.
    """
    while True:
        picked = sorted(rng.sample(LADDER, BLOCKS_PER_SET))
        if any(picked[i + 1] - picked[i] < MIN_INTRA_SET_GAP
               for i in range(BLOCKS_PER_SET - 1)):
            continue
        if picked[-1] < TALL_FLOOR:
            continue
        if picked[0] > SHORT_CEIL:
            continue
        return tuple(picked)


def new_game(n_players, seed):
    """Fresh game. Everything random here and nowhere else (A3, A4).

    After setup the game is fully deterministic: the pass outcome is a
    height comparison (A7), so no rng is carried in the state at all.
    """
    if n_players < 2 or n_players > 4:
        raise ValueError("Clearance seats 2-4 players, got %r" % (n_players,))
    rng = random.Random(seed)

    all_sets = [_draw_set(rng) for _ in range(N_SETS)]
    chosen = list(range(N_SETS))
    rng.shuffle(chosen)
    chosen = chosen[:n_players]

    heights = []
    for seat in range(n_players):
        pockets = list(all_sets[chosen[seat]])
        rng.shuffle(pockets)          # pocket index must not encode height
        heights.append(tuple(pockets))

    rail = tuple(
        tuple(sorted((seat, i) for i in range(BLOCKS_PER_SET)))
        for seat in range(n_players))

    return {
        "n": n_players,
        "seed": seed,
        "heights": tuple(heights),
        "set_of_seat": tuple(chosen),
        "rail": rail,
        "line": tuple(() for _ in range(n_players)),
        "well": (),
        "pending": tuple(None for _ in range(n_players)),
        "bar": BAR_START,
        "round": 1,
        "phase": "set",
        "setter": rng.randrange(n_players),
        "rotation": rng.randrange(n_players),
        "prev_setter": None,
        "setter_counts": tuple(0 for _ in range(n_players)),
        "commit_queue": (),
        "salvage_queue": (),
        "cur_drop": 0,
        "bottom": False,
        "over": False,
        "history": (),
    }


# --- Small pure helpers -------------------------------------------------------

def _replace(state, **kw):
    new = dict(state)
    new.update(kw)
    return new


def _put(seq, index, value):
    """New tuple with one slot replaced — the only way this engine writes."""
    items = list(seq)
    items[index] = value
    return tuple(items)


def _mm(quarters):
    return quarters / float(Q)


def _height(state, block):
    owner, idx = block
    return state["heights"][owner][idx]


def _label(state, block):
    """Public name of a block: printed set letter + pocket number."""
    owner, idx = block
    return "%s%d" % (SET_LETTERS[state["set_of_seat"][owner]], idx + 1)


def _line_mm(state, seat):
    return _mm(sum(_height(state, b) for b in state["line"][seat]))


def _is_out(state, seat):
    """§8: rail and line both empty — skipped for setter and for play."""
    return not state["rail"][seat] and not state["line"][seat]


def _clicks_of_room(state):
    return (state["bar"] - BAR_BOTTOM) // CLICK


def _pick_setter(state):
    """§4: shortest line, then fewest times as setter, then clockwise from
    the previous setter's left (A13). Returns None if every seat is out."""
    n = state["n"]
    prev = state["prev_setter"]
    start = 0 if prev is None else (prev + 1) % n
    best = None
    for seat in range(n):
        if _is_out(state, seat):
            continue
        key = (_line_mm(state, seat), state["setter_counts"][seat],
               (seat - start) % n)
        if best is None or key < best[0]:
            best = (key, seat)
    return None if best is None else best[1]


def _commit_order(state):
    """A5: rotate by round so no standing systematically commits last, from
    a seeded starting phase so no SEAT does either (a game runs 6-11 rounds,
    which is not a whole number of rotations, so a fixed phase would hand
    the last-committer slot to one seat more often than the others)."""
    n = state["n"]
    start = (state["rotation"] + state["round"] - 1) % n
    return tuple(seat for seat in
                 ((start + k) % n for k in range(n))
                 if state["rail"][seat])


def _salvage_candidates(state):
    """A10/A11: empty rail, non-empty line, ascending from the setter."""
    n = state["n"]
    start = state["setter"]
    return tuple(seat for seat in ((start + k) % n for k in range(n))
                 if not state["rail"][seat] and state["line"][seat])


def _shortest_in_line(state, seat):
    """§5.7's salvage target: the shortest block in that seat's own line."""
    line = state["line"][seat]
    return min(line, key=lambda b: (_height(state, b), b))


# --- Contract: turn order and legality ----------------------------------------

def player_to_move(state):
    if state["over"]:
        return 0
    if state["phase"] == "set":
        return state["setter"]
    if state["phase"] == "commit":
        return state["commit_queue"][0]
    return state["salvage_queue"][0]


def legal_moves(state):
    if state["over"]:
        return []
    if state["phase"] == "set":
        return [("set", down) for down, _up in PATTERNS]
    if state["phase"] == "commit":
        seat = state["commit_queue"][0]
        return [("commit", owner, idx)
                for owner, idx in sorted(state["rail"][seat])]
    return [("salvage", "decline"), ("salvage", "take")]


# --- Contract: apply ----------------------------------------------------------

def apply(state, move):
    """Return a NEW state. The input is never mutated: every container in
    the state is a tuple, and every write goes through _replace/_put."""
    if state["over"]:
        raise ValueError("game is over; no moves remain")
    kind = move[0]
    if kind == "set":
        return _apply_set(state, move[1])
    if kind == "commit":
        return _apply_commit(state, (move[1], move[2]))
    if kind == "salvage":
        return _apply_salvage(state, move[1] == "take")
    raise ValueError("unknown move %r" % (move,))


def _apply_set(state, down):
    """§5.1. Down `down` clicks then up 8-down; Bottom if the down-phase
    reaches the stop (A8, A9)."""
    if state["phase"] != "set":
        raise ValueError("not the Set phase")
    up = None
    for d, u in PATTERNS:
        if d == down:
            up = u
    if up is None:
        raise ValueError("illegal Set pattern %r" % (down,))

    seat = state["setter"]
    room = _clicks_of_room(state)
    if down >= room:
        bar = BAR_BOTTOM
        drop = room
        bottom = True
    else:
        bar = state["bar"] - CLICK * (down - up)
        drop = down - up
        bottom = False

    nxt = _replace(
        state,
        bar=bar,
        bottom=bottom,
        cur_drop=drop,
        setter_counts=_put(state["setter_counts"], seat,
                           state["setter_counts"][seat] + 1),
        phase="commit",
    )
    nxt = _replace(nxt, commit_queue=_commit_order(nxt))
    if not nxt["commit_queue"]:
        return _resolve(nxt)
    return nxt


def _apply_commit(state, block):
    """§5.2. One seat's hidden commit; the last one resolves the round."""
    if state["phase"] != "commit":
        raise ValueError("not the Commit phase")
    seat = state["commit_queue"][0]
    if block not in state["rail"][seat]:
        raise ValueError("seat %d does not hold block %r" % (seat, block))
    rail = tuple(b for b in state["rail"][seat] if b != block)
    nxt = _replace(
        state,
        rail=_put(state["rail"], seat, rail),
        pending=_put(state["pending"], seat, block),
        commit_queue=state["commit_queue"][1:],
    )
    if nxt["commit_queue"]:
        return nxt
    return _resolve(nxt)


def _resolve(state):
    """§5.4 The Pass and §5.6 The Take, resolved together (A6)."""
    n = state["n"]
    bar = state["bar"]
    rail = [list(r) for r in state["rail"]]
    line = [list(l) for l in state["line"]]
    well = list(state["well"])

    commits = [(seat, state["pending"][seat]) for seat in range(n)
               if state["pending"][seat] is not None]
    cleared, busted = [], []
    for seat, block in commits:
        (cleared if _height(state, block) < bar else busted).append(
            (seat, block))

    outcome = {}
    for seat, block in cleared:
        outcome[block] = "cleared"
    for seat, block in busted:
        outcome[block] = "scrapped (touched the bar)"

    winner = None
    took = []
    if cleared:
        tallest = max(_height(state, b) for _s, b in cleared)
        tied = [(s, b) for s, b in cleared if _height(state, b) == tallest]
        if len(tied) > 1:
            # §5.6: every tied block is scrapped and NOBODY takes anything,
            # the scrapped blocks included (A18).
            for seat, block in tied:
                well.append(block)
                outcome[block] = "scrapped (tied for tallest)"
            for seat, block in cleared:
                if (seat, block) not in tied:
                    rail[seat].append(block)
            for seat, block in busted:
                well.append(block)
        else:
            winner, win_block = tied[0]
            line[winner].append(win_block)
            took.append(win_block)
            for seat, block in cleared:
                if block != win_block:
                    rail[seat].append(block)
            if busted:
                top = max(_height(state, b) for _s, b in busted)
                prize = min(b for _s, b in busted
                            if _height(state, b) == top)   # A12
                line[winner].append(prize)
                took.append(prize)
                for seat, block in busted:
                    if block != prize:
                        well.append(block)
    else:
        for seat, block in busted:
            well.append(block)

    record = {
        "round": state["round"],
        "setter": state["setter"],
        "drop_clicks": state["cur_drop"],
        "bottom": state["bottom"],
        "bar_after": bar,
        "commits": tuple((seat, block, outcome[block])
                         for seat, block in commits),
        "winner": winner,
        "took": tuple(took),
        "salvaged": (),
    }

    nxt = _replace(
        state,
        rail=tuple(tuple(sorted(r)) for r in rail),
        line=tuple(tuple(l) for l in line),
        well=tuple(well),
        pending=tuple(None for _ in range(n)),
        commit_queue=(),
        history=state["history"] + (record,),
    )

    if nxt["bottom"]:
        # §6: the game ends at the end of the Bottom round — no Salvage.
        return _replace(nxt, over=True, phase="over")

    queue = _salvage_candidates(nxt)
    if queue:
        return _replace(nxt, phase="salvage", salvage_queue=queue)
    return _start_round(nxt)


def _apply_salvage(state, take):
    """§5.7. Take the shortest block out of your own line, or decline."""
    if state["phase"] != "salvage":
        raise ValueError("not the Salvage phase")
    seat = state["salvage_queue"][0]
    nxt = state
    if take:
        block = _shortest_in_line(state, seat)
        line = tuple(b for b in state["line"][seat] if b != block)
        rail = tuple(sorted(state["rail"][seat] + (block,)))
        last = dict(state["history"][-1])
        last["salvaged"] = last["salvaged"] + ((seat, block),)
        nxt = _replace(
            state,
            line=_put(state["line"], seat, line),
            rail=_put(state["rail"], seat, rail),
            history=state["history"][:-1] + (last,),
        )
    nxt = _replace(nxt, salvage_queue=nxt["salvage_queue"][1:])
    if nxt["salvage_queue"]:
        return nxt
    return _start_round(nxt)


def _start_round(state):
    """Advance to the next round, or end the game if nobody can Set (A14)."""
    nxt = _replace(
        state,
        round=state["round"] + 1,
        prev_setter=state["setter"],
        phase="set",
        cur_drop=0,
    )
    setter = _pick_setter(nxt)
    if setter is None:
        return _replace(nxt, over=True, phase="over")
    return _replace(nxt, setter=setter)


# --- Contract: results --------------------------------------------------------

def is_over(state):
    return bool(state["over"])


def winners(state):
    """§6 longest line, broken by §7 (A13). There is no shared victory."""
    if not state["over"]:
        return []
    n = state["n"]
    last_setter = state["setter"]
    best = None
    for seat in range(n):
        key = (
            -_line_mm(state, seat),          # longest line
            len(state["line"][seat]),        # fewer blocks in the line
            -len(state["rail"][seat]),       # more blocks left in the rail
            state["setter_counts"][seat],    # fewer times as setter
            (seat - last_setter) % n,        # clockwise from the last setter
        )
        if best is None or key < best[0]:
            best = (key, seat)
    return [best[1]]


def scores(state):
    """Progress toward the longest line — see A17 for what this counts.

    line length (mm) + 0.20 * (heights still shorter than the bar, in the
    rail plus the block committed this round). The second term moves on
    every Set, because the bar cutting past a block kills it for good.
    """
    n = state["n"]
    bar = state["bar"]
    out = []
    for seat in range(n):
        value = _line_mm(state, seat)
        if not state["over"]:
            stock = list(state["rail"][seat])
            if state["pending"][seat] is not None:
                stock.append(state["pending"][seat])
            live = sum(_height(state, b) for b in stock
                       if _height(state, b) < bar)
            value += STOCK_WEIGHT * _mm(live)
        out.append(value)
    return out


# --- Contract: observation ----------------------------------------------------

def _eye(state, seat, tag, quarters):
    """A15: a seeded eyeball read, good to about +/- 1.0 mm."""
    rng = random.Random(
        (state["seed"] * 911 + seat * 101 + tag * 7919) & 0x7FFFFFFF)
    return quarters + rng.choice(EYE_NOISE)


def _eye_table(state, seat, blocks):
    """Eyeball reads for every block this seat may physically handle,
    re-sorted so they can never contradict the fingernail ordering (§5.5)."""
    ordered = sorted(blocks, key=lambda b: (_height(state, b), b))
    reads = sorted(_eye(state, seat, owner * 17 + idx + 1,
                        state["heights"][owner][idx])
                   for owner, idx in ordered)
    return dict(zip(ordered, reads))


def _bar_bounds(state, seat, upto_round):
    """A16: what this seat can honestly deduce about the bar after the Set
    of round `upto_round` — its own drops exactly, everyone else's as a
    1.0-3.0 mm range."""
    known = 0
    unknown = 0
    bottom = False
    sets = [(rec["setter"], rec["drop_clicks"], rec["bottom"])
            for rec in state["history"] if rec["round"] <= upto_round]
    # The current round's Set only reaches the history at resolution, so
    # during the Commit it has to be added by hand.
    if state["phase"] == "commit" and upto_round >= state["round"]:
        sets.append((state["setter"], state["cur_drop"], state["bottom"]))
    for setter, drop, hit in sets:
        if hit:
            bottom = True
        elif setter == seat:
            known += drop
        else:
            unknown += 1
    if bottom:
        return BAR_BOTTOM, BAR_BOTTOM
    high = BAR_START - CLICK * known - CLICK * 2 * unknown
    low = BAR_START - CLICK * known - CLICK * 6 * unknown
    return max(BAR_BOTTOM, low), max(BAR_BOTTOM, high)


def observation(state, seat):
    """Prose for ONE seat. No exact millimetre of any height is ever shown
    (A15/A19); hidden commits of the current round are never shown (A5)."""
    n = state["n"]
    lines = []
    lines.append(
        "CLEARANCE — you are seat %d of %d. Round %d. Your printed set is "
        "'%s' (%s)." % (seat, n, state["round"],
                        SET_LETTERS[state["set_of_seat"][seat]],
                        SET_SYMBOLS[state["set_of_seat"][seat]]))
    lines.append(
        "Goal: the longest score line at the end. The bar only ever goes "
        "down. A block taller than the gap touches the bar and is scrapped "
        "for the rest of the game.")

    # --- the gap ---------------------------------------------------------
    low, high = _bar_bounds(state, seat, state["round"])
    # The eye is fuzzy but a player still reconciles it against what they
    # can prove, so the read is clamped into the deducible band.
    eye = min(high, max(low, _eye(state, seat, 999 + state["round"],
                                  state["bar"])))
    lines.append("")
    lines.append("THE GAP")
    if state["bottom"]:
        lines.append(
            "  \"Bottom\" was called: the bar is sitting on its stop at "
            "17.5 mm, and this is the last round of the game.")
    else:
        lines.append(
            "  It started at the top stop, 33.0 mm. Every Set drops it 1.0, "
            "2.0 or 3.0 mm and never raises it.")
        lines.append(
            "  From the drops you set yourself, the gap is somewhere in "
            "%.2f-%.2f mm." % (_mm(low), _mm(high)))
    lines.append(
        "  Your eye puts it at about %.1f mm (you read a gap to roughly "
        "+/- 1 mm)." % _mm(eye))
    lines.append(
        "  Nobody at the table knows how much room is left before the "
        "bottom stop; you find out when a setter says \"Bottom\".")

    # --- your stock ------------------------------------------------------
    handled = list(state["rail"][seat]) + list(state["line"][seat])
    if state["pending"][seat] is not None:
        handled.append(state["pending"][seat])
    reads = _eye_table(state, seat, handled)
    rail_sorted = sorted(state["rail"][seat],
                         key=lambda b: (-_height(state, b), b))
    lines.append("")
    lines.append("YOUR RAIL (%d block(s), tallest first by fingernail test)"
                 % len(rail_sorted))
    for rank, block in enumerate(rail_sorted, 1):
        note = "" if block[0] == seat else "  [won from %s]" % (
            SET_LETTERS[state["set_of_seat"][block[0]]])
        lines.append("  %d. %s — your eye says about %.1f mm%s"
                     % (rank, _label(state, block), _mm(reads[block]), note))
    if state["pending"][seat] is not None:
        block = state["pending"][seat]
        lines.append("  under your cup this round: %s (about %.1f mm)"
                     % (_label(state, block), _mm(reads[block])))
    if not rail_sorted and state["pending"][seat] is None:
        lines.append("  empty — you cannot commit until you salvage.")

    # --- lines -----------------------------------------------------------
    lines.append("")
    lines.append("SCORE LINES (physical: you can rank them exactly, not "
                 "measure them)")
    ranked = sorted(range(n), key=lambda p: (-_line_mm(state, p), p))
    for place, p in enumerate(ranked, 1):
        rough = 5.0 * round(_line_mm(state, p) / 5.0)
        who = "you" if p == seat else "seat %d" % p
        blocks = ", ".join(_label(state, b) for b in state["line"][p]) or "—"
        flag = " OUT" if _is_out(state, p) else ""
        lines.append(
            "  %d. %s: %d block(s), roughly %.0f mm [%s]; rail %d%s"
            % (place, who, len(state["line"][p]), rough, blocks,
               len(state["rail"][p]), flag))
    lines.append("  The shortest line sets the bar next round.")

    # --- history ---------------------------------------------------------
    if state["history"]:
        lines.append("")
        lines.append("WHAT HAS HAPPENED (public)")
        for rec in state["history"]:
            rlow, rhigh = _bar_bounds(state, seat, rec["round"])
            head = "  R%d: seat %d set the bar" % (rec["round"], rec["setter"])
            if rec["setter"] == seat:
                head += " (you dropped it %.1f mm)" % _mm(
                    CLICK * rec["drop_clicks"])
            else:
                head += " (gap then: %.2f-%.2f mm as far as you knew)" % (
                    _mm(rlow), _mm(rhigh))
            lines.append(head + ".")
            shown = sorted(rec["commits"],
                           key=lambda c: (-_height(state, c[1]), c[1]))
            for cseat, block, res in shown:
                lines.append("    seat %d played %s — %s"
                             % (cseat, _label(state, block), res))
            if shown:
                lines.append("    revealed, tallest first: %s"
                             % " > ".join(_label(state, c[1]) for c in shown))
            if rec["winner"] is None:
                lines.append("    nobody won the round.")
            else:
                lines.append(
                    "    seat %d took the round and put %s into its line."
                    % (rec["winner"],
                       " + ".join(_label(state, b) for b in rec["took"])))
            for sseat, block in rec["salvaged"]:
                lines.append("    seat %d salvaged %s back into its rail."
                             % (sseat, _label(state, block)))

    # --- what you must do -------------------------------------------------
    lines.append("")
    lines.append("NOW")
    if state["over"]:
        lines.append("  The game is over.")
        return "\n".join(lines)
    mover = player_to_move(state)
    if mover != seat:
        lines.append("  Waiting on seat %d." % mover)
        return "\n".join(lines)
    if state["phase"] == "set":
        lines.append(
            "  You are the setter (you are last on the table). Put the hood "
            "over the knob and turn eight clicks: down 5 then up 3 (the gap "
            "drops 1.0 mm), down 6 then up 2 (2.0 mm), or down 7 then up 1 "
            "(3.0 mm). The table hears eight clicks either way and never "
            "learns which you chose. If the screw reaches the bottom stop "
            "on the way down you must call \"Bottom\" and this is the last "
            "round.")
    elif state["phase"] == "commit":
        lines.append(
            "  Commit one block, in secret, under your cup. Everyone "
            "commits at the same instant — you do not know what anyone else "
            "has chosen, and they do not know yours. The tallest block that "
            "clears takes the round; a block that touches the bar is gone "
            "for good and its height is handed to the round's winner.")
    else:
        block = _shortest_in_line(state, seat)
        lines.append(
            "  Your rail is empty. You may salvage the shortest block in "
            "your own line, %s (about %.1f mm), back into your rail — your "
            "line gets that much shorter — or decline and sit out with your "
            "line intact."
            % (_label(state, block), _mm(reads[block])))
    return "\n".join(lines)
