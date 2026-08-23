"""engine.py — spineward, an executable model of idea.json. Not a game to play.

Board: 37 hex pans on cube coordinates (x + y + z = 0, max(|x|,|y|,|z|) <= 3).
Seed pans = the 19 cells with max(|x|,|y|,|z|) <= 2. Landing shelves = the 6
cells at distance 3 that are an exact multiple of one of the six hex
direction vectors (the "corners" of the outer ring). The other 12 outer-ring
cells are plain reef.

An urchin's six sockets are modelled as a length-6 list indexed by the
CURRENT hex direction each socket points at (not by a fixed physical socket
id), because nothing in the rules ever distinguishes one physical socket from
another — only the direction it is presently aimed at and what it holds
matter. TURN then just cyclically rotates that list; CREEP translates the
shell without touching it, which is exactly "keeps its facing".

Actions per turn (`grow`, `shed`, `turn`, `creep`, `take`, `rob`,
`land`) are threaded onto a single legal_moves()/apply_move() loop — normally
TWO per turn, or THREE when the acting seat is riding the tide (rules:turn
[THE TIDE]: its banked total trails the table's highest), fixed at the start
of the turn by the `turn_quota` field. Setup
(`setup_seed`, `setup_place`, `setup_spine`) is real decision-making by real
players, per idea.json's setup rules, and is played through the same loop
rather than resolved inside new_game().
"""
from __future__ import annotations

import itertools
import random  # noqa: F401 - engine takes rng as an argument; no module-level use


class Undefined(Exception):
    """The rules do not say."""


SLUG = "spineward"
PLAYERS = (2, 4)
MAX_TURNS = 450
MOVE_KINDS = ("setup_seed", "setup_place", "setup_spine",
              "grow", "shed", "turn", "creep", "take", "rob", "land")
HIDDEN_INFO = True  # a pearl's grade is unknown to every seat, including its
                     # carrier, until the moment it is landed

# ---------------------------------------------------------------------------
# Assumptions
# ---------------------------------------------------------------------------
# rules:turn[8] now states explicitly: "If the enemy is carrying no pearl, ROB
# simply is not offered as a move." Settled; not an assumption. ROB is only
# offered when the target carries at least one pearl.
ASSUMPTIONS = []
CHOICES = {}

# ---------------------------------------------------------------------------
# Board geometry
# ---------------------------------------------------------------------------
DIRS = ((1, -1, 0), (1, 0, -1), (0, 1, -1), (-1, 1, 0), (-1, 0, 1), (0, -1, 1))
RADIUS = 3
TOTAL_GRADES = {1: 8, 2: 5, 3: 3}  # 8 one-ring, 5 two-ring, 3 three-ring = 16


def _crown_value(n) -> int:
    """rules:win — the crown value is 6 at every player count, flat. The whole
    coast takes a landing (rules:turn[LAND]) so 6 is bankable even on a
    crowded, robbing four-player reef, and at two players it is a straight
    reachable race again. Six is long enough — and the race late enough — that
    the tide's catch-up (rules:turn[THE TIDE]) gets to decide it instead of
    whoever banked first. (Reworked from a flat 4, which at two players
    resolved to standoff-or-snowball: the crown either never fired under
    competent play, leaving a 0-0 backstop tie, or fired first-come-first-
    served into a runaway.)"""
    return 6


def _cube_dist(a, b) -> int:
    return max(abs(a[i] - b[i]) for i in range(3))


def _neighbor(pan, d):
    dv = DIRS[d]
    return (pan[0] + dv[0], pan[1] + dv[1], pan[2] + dv[2])


def _opposite(d):
    return (d + 3) % 6


def _pid(coord) -> str:
    """A pan's id as shown to a seat: str() of its cube coordinate, which is
    exactly how the same coordinate prints inside a raw ('setup_seed', coord)
    or ('setup_place', coord) move tuple, so a pan id in `observation` and a
    pan id in the legal-move list are the same spelling, not two that need
    translating between."""
    return str(coord)


def _all_pans():
    pans = {}
    for x in range(-RADIUS, RADIUS + 1):
        for y in range(-RADIUS, RADIUS + 1):
            z = -x - y
            if abs(z) > RADIUS:
                continue
            coord = (x, y, z)
            if _cube_dist((0, 0, 0), coord) > RADIUS:
                continue
            dist = _cube_dist((0, 0, 0), coord)
            if dist <= RADIUS - 1:
                ptype = "seed"
            else:
                is_corner = any(coord == (RADIUS * dv[0], RADIUS * dv[1], RADIUS * dv[2])
                                 for dv in DIRS)
                ptype = "shelf" if is_corner else "outer"
            pans[coord] = {"type": ptype, "pearl": None}
    return pans


def _is_pearl(content) -> bool:
    return content is not None and content != "spine"


def _is_adjacent(a, b) -> bool:
    return _cube_dist(a, b) == 1


def _urchin_at(state, pan):
    for i, u in enumerate(state["urchins"]):
        if u["pan"] == pan:
            return i
    return None


def _pan_clear(state, pan) -> bool:
    if state["pans"][pan]["pearl"] is not None:
        return False
    return _urchin_at(state, pan) is None


def _no_pearls_on_board(state) -> bool:
    return all(info["pearl"] is None for info in state["pans"].values())


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

def new_game(n_players, rng):
    grades = [1] * TOTAL_GRADES[1] + [2] * TOTAL_GRADES[2] + [3] * TOTAL_GRADES[3]
    rng.shuffle(grades)
    pearl_grades = {i: grades[i] for i in range(16)}
    seed_queue = list(range(16))
    rng.shuffle(seed_queue)

    state = {
        "n": n_players,
        "phase": "seed",
        "pans": _all_pans(),
        "pearl_grades": pearl_grades,
        "pearl_location": {},   # pid -> ("pan", coord) | ("shell", seat, dir) | ("rack", seat)
        "revealed": set(),
        "seed_queue": seed_queue,
        "seed_turn": 0,
        "urchins": [{"pan": None, "dir": [None] * 6} for _ in range(n_players)],
        "racks": [[] for _ in range(n_players)],
        "spine_supply": 24,
        "setup_place_turn": 0,
        "arm_turn": 0,
        "arm_count": 0,
        "current_seat": 0,
        "actions_taken": 0,
        "turn_quota": 2,        # actions this turn; 3 for a tide-riding chaser
        "turn_number": 0,
        "end_pending": False,
        "activity_flag": False,
        "landed_flag": False,   # did anyone LAND a pearl this round? A landing
                                # is the only progress toward a crown, so only
                                # a landing resets the slack clock (rules:end[1])
        "no_landing_rounds": 0, # consecutive rounds in which no pearl was landed
        "crown_seat": None,     # seat whose rack total reached the crown value
    }
    return state


def player_to_move(state):
    phase = state["phase"]
    if phase == "seed":
        return state["seed_turn"]
    if phase == "place_shell":
        return state["setup_place_turn"]
    if phase == "arm":
        return state["arm_turn"]
    return state["current_seat"]


# ---------------------------------------------------------------------------
# legal_moves — pure, no mutation
# ---------------------------------------------------------------------------

def legal_moves(state):
    phase = state["phase"]

    if phase == "seed":
        return [("setup_seed", pan) for pan, info in state["pans"].items()
                if info["type"] == "seed" and info["pearl"] is None]

    if phase == "place_shell":
        placed = [u["pan"] for u in state["urchins"] if u["pan"] is not None]
        moves = []
        for pan, info in state["pans"].items():
            if info["type"] != "outer":
                continue
            if pan in placed:
                continue
            if any(_is_adjacent(pan, p) for p in placed):
                continue
            moves.append(("setup_place", pan))
        return moves

    if phase == "arm":
        u = state["urchins"][state["arm_turn"]]
        return [("setup_spine", d) for d in range(6) if u["dir"][d] is None]

    # phase == "main"
    seat = state["current_seat"]
    u = state["urchins"][seat]
    pan = u["pan"]
    moves = []

    if state["spine_supply"] > 0:
        for d in range(6):
            if u["dir"][d] is None:
                moves.append(("grow", d))

    for d in range(6):
        if u["dir"][d] == "spine":
            moves.append(("shed", d))

    moves.append(("turn", 1))
    moves.append(("turn", -1))

    for d in range(6):
        if u["dir"][d] != "spine":
            continue
        npan = _neighbor(pan, d)
        if npan in state["pans"] and _pan_clear(state, npan):
            moves.append(("creep", d))

    for d in range(6):
        if u["dir"][d] != "spine":
            continue
        npan = _neighbor(pan, d)
        if npan in state["pans"] and state["pans"][npan]["pearl"] is not None:
            for e in range(6):
                if u["dir"][e] is None:
                    moves.append(("take", d, e))

    held_dirs = [f for f in range(6) if _is_pearl(u["dir"][f])]
    for d in range(6):
        if u["dir"][d] != "spine":
            continue
        npan = _neighbor(pan, d)
        if npan not in state["pans"]:
            continue
        tseat = _urchin_at(state, npan)
        if tseat is None or tseat == seat:
            continue
        tgt = state["urchins"][tseat]
        if tgt["dir"][_opposite(d)] == "spine":
            continue
        target_has_pearl = any(_is_pearl(c) for c in tgt["dir"])
        if not target_has_pearl:
            continue
        for e in range(6):
            if u["dir"][e] is None:
                moves.append(("rob", d, e))

    if held_dirs:  # whole-coast landing (rules:turn[LAND]): the outgoing tide
                   # beaches a pearl from ANY pan, so no dock pilgrimage to a
                   # corner shelf is needed; the corner shelves are the reef's
                   # historic anchorages, now joined by the whole coast.
        empty_wells = 6 - len(state["racks"][seat])
        if empty_wells > 0:
            maxk = min(len(held_dirs), empty_wells)
            for k in range(1, maxk + 1):
                for combo in itertools.combinations(held_dirs, k):
                    moves.append(("land", combo))

    return moves


# ---------------------------------------------------------------------------
# apply_move — may mutate; MUST return the state
# ---------------------------------------------------------------------------

def apply_move(state, move, rng):
    kind = move[0]

    if kind == "setup_seed":
        pan = move[1]
        pid = state["seed_queue"].pop(0)
        state["pans"][pan]["pearl"] = pid
        state["pearl_location"][pid] = ("pan", pan)
        state["seed_turn"] = (state["seed_turn"] + 1) % state["n"]
        if not state["seed_queue"]:
            state["phase"] = "place_shell"
        return state

    if kind == "setup_place":
        pan = move[1]
        seat = state["setup_place_turn"]
        state["urchins"][seat]["pan"] = pan
        state["setup_place_turn"] += 1
        if state["setup_place_turn"] >= state["n"]:
            state["phase"] = "arm"
            state["arm_turn"] = state["n"] - 1
            state["arm_count"] = 0
        return state

    if kind == "setup_spine":
        d = move[1]
        seat = state["arm_turn"]
        state["urchins"][seat]["dir"][d] = "spine"
        state["spine_supply"] -= 1
        state["arm_count"] += 1
        if state["arm_count"] >= 2:
            state["arm_count"] = 0
            state["arm_turn"] -= 1
            if state["arm_turn"] < 0:
                state["phase"] = "main"
                state["current_seat"] = 0
                state["actions_taken"] = 0
                state["turn_quota"] = 2
                state["turn_number"] = 0
                state["end_pending"] = False
                state["activity_flag"] = False
        return state

    # main-phase actions
    seat = state["current_seat"]
    u = state["urchins"][seat]
    activity = False
    landed = False   # LAND is the only action that advances the crown

    if kind == "grow":
        d = move[1]
        u["dir"][d] = "spine"
        state["spine_supply"] -= 1
    elif kind == "shed":
        d = move[1]
        u["dir"][d] = None
        state["spine_supply"] += 1
    elif kind == "turn":
        s = move[1]
        u["dir"] = [u["dir"][(d - s) % 6] for d in range(6)]
    elif kind == "creep":
        d = move[1]
        u["pan"] = _neighbor(u["pan"], d)
    elif kind == "take":
        d, e = move[1], move[2]
        npan = _neighbor(u["pan"], d)
        pid = state["pans"][npan]["pearl"]
        state["pans"][npan]["pearl"] = None
        u["dir"][e] = pid
        state["pearl_location"][pid] = ("shell", seat, e)
        activity = True
    elif kind == "rob":
        d, e = move[1], move[2]
        npan = _neighbor(u["pan"], d)
        tseat = _urchin_at(state, npan)
        tgt = state["urchins"][tseat]
        pearl_dirs = [f for f in range(6) if _is_pearl(tgt["dir"][f])]
        if pearl_dirs:
            f = pearl_dirs[rng.randrange(len(pearl_dirs))]
            pid = tgt["dir"][f]
            tgt["dir"][f] = None
            u["dir"][e] = pid
            state["pearl_location"][pid] = ("shell", seat, e)
        activity = True
    elif kind == "land":
        for f in move[1]:
            pid = u["dir"][f]
            u["dir"][f] = None
            state["racks"][seat].append(pid)
            state["pearl_location"][pid] = ("rack", seat)
            state["revealed"].add(pid)
        activity = True
        landed = True
        # rules:win — the CROWN. The instant a rack's public total reaches the
        # crown value it ends the game on the spot with that player as the sole
        # winner, overriding the round-finish and every other trigger.
        if sum(state["pearl_grades"][pid] for pid in state["racks"][seat]) >= _crown_value(state["n"]):
            state["crown_seat"] = seat
    else:
        raise AssertionError(f"engine bug: unhandled move kind {kind!r}")

    if activity:
        state["activity_flag"] = True
    if landed:
        state["landed_flag"] = True

    if not state["end_pending"]:
        if _no_pearls_on_board(state) or any(len(r) >= 6 for r in state["racks"]):
            state["end_pending"] = True

    state["actions_taken"] += 1
    if state["actions_taken"] >= state["turn_quota"]:
        state["actions_taken"] = 0
        state["current_seat"] = (state["current_seat"] + 1) % state["n"]
        # THE TIDE (rules:turn[THE TIDE]): the next player to act - the one
        # whose banked total is strictly below the table's highest banked
        # total - rides the outgoing current and takes THREE actions this
        # turn, not the usual two. Quota is fixed at the START of the turn,
        # per the rule text, and is public: anyone reads who is ahead off the
        # racks, and off the same racks who is acting more often.
        racksum = [sum(state["pearl_grades"][pid] for pid in r)
                   for r in state["racks"]]
        nxt = state["current_seat"]
        state["turn_quota"] = 3 if (racksum[nxt] < max(racksum)) else 2
        state["turn_number"] += 1
        if state["turn_number"] % state["n"] == 0:
            # rules:end[1] — the slack trigger. FOUR consecutive full rounds in
            # which no pearl is LANDED in a rack end the game. Taking and
            # robbing are churn, not progress: the crown only advances on a
            # landing, so a table that keeps shuffling pearls without banking
            # one is as stuck as a table sitting still. A landing resets the
            # count. (Reworked from "three silent rounds with no pearl
            # activity": random/churning play kept that counter reset forever
            # because take/drop/rob all count as activity, so it never fired
            # and 4p games stalled to the turn cap.)
            if state["landed_flag"]:
                state["no_landing_rounds"] = 0
            else:
                state["no_landing_rounds"] += 1
            if state["no_landing_rounds"] >= 4 and not state["end_pending"]:
                state["end_pending"] = True
            state["landed_flag"] = False
            state["activity_flag"] = False

    return state


# ---------------------------------------------------------------------------
# Ending, scoring
# ---------------------------------------------------------------------------

def is_over(state) -> bool:
    if state["phase"] != "main":
        return False
    if state["crown_seat"] is not None:
        # rules:win — the crown ends the game on the spot, mid-round, because
        # it cannot be shared; it does not wait for the round to finish.
        return True
    return (state["end_pending"] and state["actions_taken"] == 0
            and state["turn_number"] > 0 and state["turn_number"] % state["n"] == 0)


def scores(state):
    return [float(sum(state["pearl_grades"][pid] for pid in rack))
            for rack in state["racks"]]


def winners(state):
    if state["crown_seat"] is not None:
        # rules:win — a crown is a sole win; no tiebreak comes into play.
        return [state["crown_seat"]]
    totals = scores(state)
    if not totals:
        return []
    top = max(totals)
    cands = [i for i, v in enumerate(totals) if v == top]
    if len(cands) == 1:
        return cands

    # Tiebreaker chain (rules:win): among the level leaders, the one who
    # landed the most pearls wins; then the one carrying the fewest pearls in
    # their shell sockets (least dead weight); then the one with the most
    # spines standing in their shell; then they share.
    counts = [len(state["racks"][i]) for i in range(state["n"])]
    topc = max(counts[i] for i in cands)
    cands = [i for i in cands if counts[i] == topc]
    if len(cands) == 1:
        return cands

    carried = [sum(1 for c in state["urchins"][i]["dir"] if _is_pearl(c))
               for i in range(state["n"])]
    min_carried = min(carried[i] for i in cands)
    cands = [i for i in cands if carried[i] == min_carried]
    if len(cands) == 1:
        return cands

    spines = [sum(1 for c in state["urchins"][i]["dir"] if c == "spine")
              for i in range(state["n"])]
    tops = max(spines[i] for i in cands)
    return [i for i in cands if spines[i] == tops]


# ---------------------------------------------------------------------------
# Hidden information
# ---------------------------------------------------------------------------

def determinize(state, seat, rng):
    """Resample every unrevealed pearl's grade, uniformly over what remains.

    No seat, including a pearl's own carrier, ever learns a grade before it
    is landed (rules:turn[9]: "you do not look at its foot and nor does
    anyone else"), so every seat's uncertainty is identical and this ignores
    `seat` beyond the signature the harness expects.
    """
    revealed_counts = {1: 0, 2: 0, 3: 0}
    for pid in state["revealed"]:
        revealed_counts[state["pearl_grades"][pid]] += 1
    pool = []
    for g in (1, 2, 3):
        pool.extend([g] * (TOTAL_GRADES[g] - revealed_counts[g]))
    rng.shuffle(pool)
    unrevealed = [pid for pid in range(16) if pid not in state["revealed"]]
    for pid, g in zip(unrevealed, pool):
        state["pearl_grades"][pid] = g
    return state


_PHASE_LABEL = {
    "seed": "setup: seeding pearls",
    "place_shell": "setup: placing shells",
    "arm": "setup: arming spines",
    "main": "main turns",
}


def _socket_view(dirs, pan, pans):
    """One urchin's six sockets, in rules:turn[0]'s own terms: for each of
    the six directions, which pan it faces (None past the edge of the reef,
    the same board-membership test `pans[pan]["neighbors"]` uses, so a
    socket never faces a pan id that the `pans` map does not also list) and
    what it holds — "spine", {"pearl": id} or None for nothing. This
    replaces the raw `dir` list, which a seat had to decode against an
    encoding it never saw; every fact here is read straight off the physical
    shell, the way rules:turn[0] describes a socket."""
    sockets = []
    for d in range(6):
        c = dirs[d]
        if c is None:
            holds = None
        elif c == "spine":
            holds = "spine"
        else:
            holds = {"pearl": c}
        npan = _neighbor(pan, d)
        faces = _pid(npan) if npan in pans else None
        sockets.append({"direction": d, "faces_pan": faces, "holds": holds})
    return sockets


def observation(state, seat):
    """Everything `seat` is allowed to look at, in rules:turn's own words,
    not the state machine that drives `apply_move`.

    Three passes, in order:

    1. Remove what no seat may see. A pearl's POSITION is always public (it
       is a physical piece sitting in a visible pan or socket, or counted in
       a visible rack); only its GRADE is hidden, and only until it is
       landed, for every seat including whoever is carrying it. Grades for
       unrevealed pearls are simply absent from the returned `grades` map —
       looking one up for a pearl id that has not been landed is the
       caller's bug, not a value this function will supply. Every seat's
       hidden layer is identical (see `determinize`'s docstring), so this
       ignores `seat` for the same reason that function does — there is no
       private per-seat holding to add back in, so nothing below this point
       changes with who is asking except which urchin `your_reach` is about.

    2. Add back what is derivable from what the seat may see. CREEP, TAKE,
       DROP and ROB are all written in terms of "a neighbouring pan you have
       a spine pointing at" (rules:turn[0] and the four action entries), so
       every pan states its own six neighbours (`neighbors`), and the seat's
       own urchin gets its reach into them worked out in `your_reach`: which
       clear pans it could creep into, which neighbouring pans hold
       a pearl it could take, which neighbouring enemy urchins it could rob
       (spine out, no spine back, an empty socket to put the catch in, and
       the enemy must actually be carrying a pearl — the same test
       `legal_moves` uses, rules:turn[8], so this list never promises a ROB
       that is not actually offered), and
       whether it is standing on a landing shelf. None of this is a verdict
       on whether any of it is a good idea; it is what a seat sitting at the
       reef sees by looking down at the pans that touch its own.

    3. Say it in the rulebook's words. `pans`, `urchins` and `sockets`
       replace the raw `pearl`/`dir` encoding a seat had to reverse-engineer.
       `to_move` replaces four redundant phase-specific turn counters
       (`seed_turn`, `setup_place_turn`, `arm_turn`, `current_seat`) with the
       one fact any of them ever meant: whose action is it. `arm_count` is
       dropped outright rather than renamed — a seat already sees how many
       spines the arming urchin has standing (count the "spine" sockets in
       its own entry under `urchins`), so restating that count under a
       second name would be a lookup masquerading as new information.
       `actions_taken`, `activity_flag` and `end_pending` are kept, because
       none of the three is recoverable from a single glance at the pans —
       they are genuine rules bookkeeping (rules:turn[1]'s two actions,
       rules:end[1]'s quiet round, rules:end[0]'s end trigger), not
       implementation state, so they are renamed to what they track rather
       than dropped.
    """
    urchins = state["urchins"]
    occ = {u["pan"]: i for i, u in enumerate(urchins) if u["pan"] is not None}

    pans = {}
    for pan, info in state["pans"].items():
        neighbors = []
        for d in range(6):
            npan = _neighbor(pan, d)
            neighbors.append(_pid(npan) if npan in state["pans"] else None)
        pans[_pid(pan)] = {
            "type": info["type"],
            "pearl": info["pearl"],
            "urchin": occ.get(pan),
            "neighbors": neighbors,
        }

    urchin_views = []
    for i, u in enumerate(urchins):
        pan = u["pan"]
        urchin_views.append({
            "seat": i,
            "pan": _pid(pan) if pan is not None else None,
            "on_landing_shelf": (pan is not None
                                  and state["pans"][pan]["type"] == "shelf"),
            "sockets": (_socket_view(u["dir"], pan, state["pans"])
                        if pan is not None else None),
        })

    your_reach = None
    if state["phase"] == "main":
        u = urchins[seat]
        pan = u["pan"]
        dirs = u["dir"]
        has_empty_socket = any(c is None for c in dirs)

        can_creep_to, can_take_from, can_rob = [], [], []
        for d in range(6):
            if dirs[d] != "spine":
                continue
            npan = _neighbor(pan, d)
            if npan not in state["pans"]:
                continue
            info = state["pans"][npan]
            tseat = occ.get(npan)
            if tseat is not None and tseat != seat:
                tgt = urchins[tseat]
                if tgt["dir"][_opposite(d)] == "spine":
                    continue
                target_has_pearl = any(_is_pearl(c) for c in tgt["dir"])
                if not target_has_pearl:
                    continue
                if has_empty_socket:
                    can_rob.append({"seat": tseat, "pan": _pid(npan),
                                     "direction": d})
            elif info["pearl"] is not None:
                if has_empty_socket:
                    can_take_from.append({"pan": _pid(npan), "direction": d,
                                          "pearl": info["pearl"]})
            elif tseat is None:
                can_creep_to.append(_pid(npan))

        your_reach = {
            "on_landing_shelf": state["pans"][pan]["type"] == "shelf",
            "can_creep_to": can_creep_to,
            "can_take_from": can_take_from,
            "can_rob": can_rob,
        }

    main_turn = None
    if state["phase"] == "main":
        main_turn = {
            "actions_taken_this_turn": state["actions_taken"],
            "actions_quota_this_turn": state["turn_quota"],
            "actions_remaining_this_turn": max(0, state["turn_quota"] - state["actions_taken"]),
            "riding_the_tide_this_turn": state["turn_quota"] >= 3,
            "activity_this_round": state["activity_flag"],
            "landed_this_round": state["landed_flag"],
            "rounds_without_landing": state["no_landing_rounds"],
            "end_condition_reached": state["end_pending"],
        }

    return {
        "phase": _PHASE_LABEL[state["phase"]],
        "players": state["n"],
        "seat": seat,
        "to_move": player_to_move(state),
        "main_turn": main_turn,
        "spine_supply_remaining": state["spine_supply"],
        "seed_pearls_remaining_to_place": len(state["seed_queue"]),  # count
            # only — the draw order behind it is a blind shake; nobody at
            # the table, including the seat about to draw, knows it
        "pans": pans,
        "urchins": urchin_views,
        "your_reach": your_reach,
        "racks": [list(rack) for rack in state["racks"]],
        "grades": {pid: state["pearl_grades"][pid] for pid in state["revealed"]},
    }
