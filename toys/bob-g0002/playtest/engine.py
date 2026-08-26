"""Re-Pin — engine implementation of toys/g0002/rules.md.

One seat is the Locksmith: they load five hidden pins (rungs 1-8) into the
five chambers of a printed lock and keep three more pins as a secret reserve.
The other seats are Crackers: on a turn a Cracker either Holds or sets the
five sliders of their key and turns the plug. The plug stops at the first
wrong chamber, so the reading is the length of the correct leading run --
0..4, or the lock opens on all five. Every failed turn pays the Locksmith 1;
after a failed Probe the Locksmith may pay 2 to swap one chamber's pin for a
reserve pin, which rots what the Crackers thought they knew.

Everything the engine had to decide that rules.md left open is registered in
ASSUMPTIONS below, never guessed silently.

State is a dict whose every value is immutable (ints, strings, tuples), so
``apply`` clones with ``dict(state)`` and can never write through to its
input.
"""

import itertools
import random

IDEA_SHA = "33417d4f3fd0a02e10e808ebc310d4c5fde16b43d225d95491bc907ff78df72c"

N_CHAMBERS = 5
N_RUNGS = 8
PINS_PER_RUNG = 5
RESERVE_SIZE = 3
RAIL_TOP = 12
REPIN_COST = 2
NO_OPEN_BONUS = 5
DEEPEST_BONUS = 3


ASSUMPTIONS = [
    "A1 Load is three sequential Locksmith decisions -- (a) the five starting "
    "rungs as a multiset, which is public and becomes the cut rail, (b) the "
    "secret arrangement of those five pins across chambers 1-5, (c) the three "
    "secret reserve pins. rules.md sec.5 Load has the Locksmith pick and show "
    "five pins, then place them, then draw the reserve; no information reaches "
    "the Locksmith between those steps, so the set of achievable loads is "
    "identical, but the engine's move list stays at 792 / <=120 / <=120 "
    "entries instead of one 8^5-wide move.",

    "A2 A Probe key is set as five sequential single-slider decisions (slider "
    "1 first, slider 5 last). rules.md sec.5 Probe makes slider settings "
    "public and set in the open, so no information reaches the Cracker "
    "between settings and the strategy space is unchanged -- but it keeps "
    "legal_moves at <=8 entries instead of 32768. The Hold/Probe choice is "
    "folded into the first decision: naming any value for slider 1 commits "
    "the turn to a Probe. CONSEQUENCE: one rules.md 'turn' is up to 5 engine "
    "moves, so engine move counts run ~4x the table's turn count.",

    "A3 rules.md sec.5 Re-pin says 'you may not re-pin ... after the opening "
    "Probe'. The engine reads that as 'after a Probe that opens the lock', "
    "which agrees with sec.4 step 4 (the window follows a FAILED Probe) and "
    "sec.8 ('A Probe reads OPEN ... no re-pin window'). The competing reading "
    "-- no window after the round's FIRST Probe -- is a real extra rule and "
    "only bites when turn 1 was a Hold (the lane reaches 2 on turn 2). "
    "rules.md should say which; the engine implements the first reading.",

    "A4 The gate is exact: a chamber counts correct iff the slider number "
    "equals that chamber's pin rung. rules.md never rules on print tolerance "
    "on the 0.4 mm ladder, so the engine models no slop -- a neighbouring "
    "rung never passes, and a correct chamber never binds.",

    "A5 Physical mishaps never occur. sec.5's void/jam/forced-plug rulings "
    "and sec.8's voided round, seen-pin and lifted-hood cases are execution "
    "errors rather than decisions, so the engine models perfectly clean play: "
    "no turn is voided, no round replayed, no reading corrected. Registered "
    "because it means no number this sim produces tests those rules.",

    "A6 'The player to the Locksmith's left' (sec.3.6) and 'pass the "
    "Locksmith seat to the left' (sec.3) both mean the next seat index, "
    "(seat + 1) mod n, and turns pass in that same direction (sec.4, "
    "'clockwise'). rules.md never pins left to ascending seat order.",

    "A7 The first Locksmith is drawn from the seeded RNG -- sec.3.4 "
    "explicitly allows a random choice for machine play. The seat then "
    "advances by one seat per round.",

    "A8 A re-pin may return a pin of the rung that was just removed, if the "
    "reserve holds that rung. sec.5 Re-pin says only 'put one of your three "
    "hidden reserve pins in its place' and never requires the rung to change, "
    "so a 2-point bluff that changes nothing is legal here.",

    "A9 Choosing between two reserve pins of the same rung is not a distinct "
    "decision, so re-pin moves are listed once per distinct (chamber, rung) "
    "pair rather than once per physical pin.",

    "A10 A reading of 0 still qualifies for the deepest-reading bonus. sec.6 "
    "excludes only the case where no Probe was made all round, so in an "
    "unopened round of nothing but 0s the earliest Prober banks the 3.",

    "A11 The five-pins-per-rung supply limit (sec.8) is enforced only on the "
    "Locksmith's opening eight pins (five loaded plus three reserve). After "
    "that those eight pins circulate between chambers and reserve and the case "
    "is never touched again, so supply never binds mid-round.",

    "A12 Round count is one round per player at 3 and 4 players and four legs "
    "at 2 players (sec.3.5, sec.6). The Locksmith seat advances every round, "
    "so at 2 players each seat is Locksmith twice.",

    "A13 The score board's printed 0-70 range (sec.2) is treated as "
    "unbounded; the engine never caps a score. The reachable maximum is under "
    "70 at every player count, so the track never actually runs out.",

    "A14 The cut rail is published as the sorted multiset of the five starting "
    "rungs and never changes (sec.5.4). The engine shows it to every seat and "
    "reveals nothing about the arrangement.",

    "A15 A re-pin is announced publicly -- every seat learns THAT a chamber "
    "changed and on which turn, and sees the -2 on the lane -- but which "
    "chamber and which rung stay hidden from the Crackers (sec.5.1, sec.5.4).",

    "A16 The re-pin window is a distinct engine move only when the Locksmith "
    "lane is at 2 or more. When a re-pin is unaffordable (sec.8) the window is "
    "skipped rather than offered as a forced pass, so the move list never "
    "contains a decision with no content.",

    "A17 Holds pay the Locksmith. sec.4 step 3 says income accrues 'on a Hold "
    "as well as on a failed Probe', while sec.6's worked example prose says "
    "'six failed turns paid 6' over a table showing seven paid turns. The "
    "engine follows sec.4 step 3, which is what makes that example's final "
    "figure of 3 come out right.",

    "A18 sec.7's four-step tiebreak always separates the leaders, so "
    "winners() returns exactly one seat and never a shared win. 'Sat in the "
    "Locksmith seat most recently' is read as the highest round index at "
    "which that seat was Locksmith.",

    "A19 The pin ladder has 8 rungs. idea.json says '3.0-6.0 mm in 0.4 mm "
    "steps' (which would be 9 rungs) but rules.md sec.2 prints exactly 8 "
    "(3.0/3.4/3.8/4.2/4.6/5.0/5.4/5.8) and the key sliders detent at 1-8. The "
    "engine follows rules.md.",

    "A20 rules.md sec.6's worked scoring example CANNOT HAPPEN. Exhaustive "
    "search over every starting arrangement of the rail 1 2 3 5 7 and every "
    "one-chamber re-pin the table allows on turns 4 and 6 yields zero "
    "histories matching its eight rows. Turns 1-4 force chambers (2,3,1,7,5); "
    "turn 4's re-pin must hit chamber 3 to make turn 5 read 2, but then turn 6 "
    "reads 2 where the table prints 1. Independently, turn 8 opens on key "
    "2 3 7 5 1 with no re-pin after turn 7, so chamber 1 held rung 2 on turn "
    "7, and Ash's turn-7 key starts with 2 -- the pointer had to read at least "
    "1, not the 0 printed. The engine implements sec.5's definition of the "
    "reading (which is unambiguous); the example is wrong and teaches the "
    "table a lock that the mechanism cannot produce. The rules writer must "
    "rebuild that table.",

    "A21 scores() is an engine-side progress heuristic and reads hidden state "
    "(it knows which chamber a re-pin hit, so a Cracker's confirmed prefix "
    "decays the moment it actually rots, not when the Cracker works it out). "
    "It is not shown to any seat; observation() carries public information "
    "only.",
]


# Every multiset of five rungs the Locksmith could load, lexicographic.
_ALL_STARTS = tuple(
    itertools.combinations_with_replacement(range(1, N_RUNGS + 1), N_CHAMBERS))
# Every multiset of three rungs a reserve could be, lexicographic.
_ALL_RESERVES = tuple(
    itertools.combinations_with_replacement(range(1, N_RUNGS + 1), RESERVE_SIZE))


# --------------------------------------------------------------------------
# construction
# --------------------------------------------------------------------------

def new_game(n_players, seed):
    """Fresh game. The only random draw in Re-Pin is which seat loads first."""
    n_players = int(n_players)
    if n_players < 2 or n_players > 4:
        raise ValueError("Re-Pin seats 2-4 players; got %r" % (n_players,))
    rng = random.Random(seed)
    state = {
        "n": n_players,
        "seed": seed,
        "n_rounds": 4 if n_players == 2 else n_players,
        "first_locksmith": rng.randrange(n_players),
        "round_idx": 0,
        "banked": (0,) * n_players,
        "opens": (0,) * n_players,
        "best_open": (0,) * n_players,
        "locksmith_history": (),
        "round_results": (),
    }
    _begin_round(state)
    return state


def _begin_round(s):
    """Reset every round-scoped field and put the Locksmith on the Load step."""
    n = s["n"]
    locksmith = (s["first_locksmith"] + s["round_idx"]) % n
    s["locksmith"] = locksmith
    s["crackers"] = tuple((locksmith + k) % n for k in range(1, n))
    s["phase"] = "load_pins"
    s["lane"] = 0
    s["turn_no"] = 0
    s["chambers"] = ()
    s["cut_rail"] = ()
    s["reserve"] = ()
    s["stock"] = (PINS_PER_RUNG,) * N_RUNGS
    s["chamber_changed"] = (0,) * N_CHAMBERS
    s["probes"] = ()
    s["log"] = ()
    s["deepest"] = None
    s["opened_by"] = None
    s["open_value"] = 0
    s["partial_key"] = ()
    s["repins"] = 0


# --------------------------------------------------------------------------
# small derived quantities
# --------------------------------------------------------------------------

def _rail(s):
    """The number the time rail peg is on right now: 12 on turn 1, 1 on 12."""
    if s["turn_no"] <= 0:
        return RAIL_TOP
    return RAIL_TOP + 1 - s["turn_no"]


def _elapsed(s):
    """Turns already finished this round, 0..12."""
    if s["turn_no"] <= 0:
        return 0
    return s["turn_no"] - 1


def _cur_cracker(s):
    crackers = s["crackers"]
    return crackers[(s["turn_no"] - 1) % len(crackers)]


def _reading(chambers, key):
    """Correct chambers counted from chamber 1, stopping at the first miss."""
    got = 0
    for i in range(N_CHAMBERS):
        if key[i] != chambers[i]:
            break
        got += 1
    return got


def _live_prefix(s, seat):
    """Longest leading run this seat has confirmed AND that has not been
    re-pinned since the Probe that confirmed it. This is the seat's real
    standing knowledge; a re-pin inside the run knocks it back to the chamber
    before the swap."""
    changed = s["chamber_changed"]
    best = 0
    for turn, prober, _key, got in s["probes"]:
        if prober != seat:
            continue
        live = got
        for j in range(got):
            # a re-pin resolves after the Probe on the same turn, so >= is stale
            if changed[j] >= turn:
                live = j
                break
        if live > best:
            best = live
    return best


def player_to_move(state):
    phase = state["phase"]
    if phase == "done":
        return 0
    if phase == "turn":
        return _cur_cracker(state)
    return state["locksmith"]


def is_over(state):
    return state["phase"] == "done"


# --------------------------------------------------------------------------
# moves
# --------------------------------------------------------------------------

def legal_moves(state):
    phase = state["phase"]
    if phase == "done":
        return []
    if phase == "load_pins":
        return [("load_pins", combo) for combo in _ALL_STARTS]
    if phase == "arrange":
        return [("arrange", perm)
                for perm in sorted(set(itertools.permutations(state["cut_rail"])))]
    if phase == "reserve":
        stock = state["stock"]
        out = []
        for combo in _ALL_RESERVES:
            fits = True
            for rung in sorted(set(combo)):
                if combo.count(rung) > stock[rung - 1]:
                    fits = False
                    break
            if fits:
                out.append(("reserve", combo))
        return out
    if phase == "turn":
        done = len(state["partial_key"])
        moves = []
        if done == 0:
            moves.append(("hold",))
        for value in range(1, N_RUNGS + 1):
            moves.append(("slider", done + 1, value))
        return moves
    if phase == "repin":
        moves = [("no_repin",)]
        for chamber in range(1, N_CHAMBERS + 1):
            for rung in sorted(set(state["reserve"])):
                moves.append(("repin", chamber, rung))
        return moves
    raise ValueError("unknown phase %r" % (phase,))


def apply(state, move):
    """Return a NEW state. Every value in a state is immutable, so the shallow
    dict clone below cannot write through to the caller's state."""
    phase = state["phase"]
    if phase == "done":
        raise ValueError("the game is over; no move applies")
    kind = move[0]
    s = dict(state)

    if kind == "load_pins":
        _require(phase == "load_pins", kind, phase)
        combo = tuple(move[1])
        stock = list(s["stock"])
        for rung in combo:
            stock[rung - 1] -= 1
            if stock[rung - 1] < 0:
                raise ValueError("the case holds only %d pins of rung %d"
                                 % (PINS_PER_RUNG, rung))
        s["stock"] = tuple(stock)
        s["cut_rail"] = tuple(sorted(combo))
        s["phase"] = "arrange"

    elif kind == "arrange":
        _require(phase == "arrange", kind, phase)
        arrangement = tuple(move[1])
        if tuple(sorted(arrangement)) != s["cut_rail"]:
            raise ValueError("arrangement %r is not the loaded pins %r"
                             % (arrangement, s["cut_rail"]))
        s["chambers"] = arrangement
        s["phase"] = "reserve"

    elif kind == "reserve":
        _require(phase == "reserve", kind, phase)
        combo = tuple(move[1])
        stock = list(s["stock"])
        for rung in combo:
            stock[rung - 1] -= 1
            if stock[rung - 1] < 0:
                raise ValueError("the case has no pin of rung %d left" % rung)
        s["stock"] = tuple(stock)
        s["reserve"] = tuple(sorted(combo))
        s["phase"] = "turn"
        s["turn_no"] = 1
        s["partial_key"] = ()

    elif kind == "hold":
        _require(phase == "turn" and not s["partial_key"], kind, phase)
        s["log"] = s["log"] + (("hold", s["turn_no"], _cur_cracker(s)),)
        s["lane"] = s["lane"] + 1        # sec.4 step 3: a Hold pays too (A17)
        _finish_turn(s)                  # sec.5 Hold: no re-pin window

    elif kind == "slider":
        _require(phase == "turn", kind, phase)
        if move[1] != len(s["partial_key"]) + 1:
            raise ValueError("slider %r is not the next one to set" % (move[1],))
        s["partial_key"] = s["partial_key"] + (move[2],)
        if len(s["partial_key"]) == N_CHAMBERS:
            _resolve_probe(s)

    elif kind == "repin":
        _require(phase == "repin", kind, phase)
        chamber, rung = move[1], move[2]
        reserve = list(s["reserve"])
        if rung not in reserve:
            raise ValueError("no reserve pin of rung %d" % rung)
        if s["lane"] < REPIN_COST:
            raise ValueError("a re-pin costs 2 and the lane may not go below 0")
        reserve.remove(rung)
        chambers = list(s["chambers"])
        reserve.append(chambers[chamber - 1])
        chambers[chamber - 1] = rung
        changed = list(s["chamber_changed"])
        changed[chamber - 1] = s["turn_no"]
        s["chambers"] = tuple(chambers)
        s["reserve"] = tuple(sorted(reserve))
        s["chamber_changed"] = tuple(changed)
        s["lane"] = s["lane"] - REPIN_COST
        s["repins"] = s["repins"] + 1
        s["log"] = s["log"] + (("repin", s["turn_no"]),)
        _finish_turn(s)

    elif kind == "no_repin":
        _require(phase == "repin", kind, phase)
        _finish_turn(s)

    else:
        raise ValueError("unknown move %r" % (move,))

    return s


def _require(ok, kind, phase):
    if not ok:
        raise ValueError("move %r is not legal in phase %r" % (kind, phase))


def _resolve_probe(s):
    """The key is home; turn the plug and read the pointer."""
    seat = _cur_cracker(s)
    turn = s["turn_no"]
    key = s["partial_key"]
    got = _reading(s["chambers"], key)
    s["log"] = s["log"] + (("probe", turn, seat, key, got),)
    s["probes"] = s["probes"] + ((turn, seat, key, got),)
    s["partial_key"] = ()

    if got == N_CHAMBERS:
        # The latch snaps. sec.8: the round ends here -- no income, no window.
        s["opened_by"] = seat
        s["open_value"] = _rail(s)
        _end_round(s)
        return

    deepest = s["deepest"]
    if deepest is None or got > deepest[0]:
        s["deepest"] = (got, turn, seat)      # ties keep the earlier turn
    s["lane"] = s["lane"] + 1
    if s["lane"] >= REPIN_COST:
        s["phase"] = "repin"                  # sec.4 step 4, and A16
    else:
        _finish_turn(s)


def _finish_turn(s):
    """sec.4 step 5: the time rail drops one; if it cannot, the round ends."""
    if s["turn_no"] >= RAIL_TOP:
        _end_round(s)
    else:
        s["turn_no"] = s["turn_no"] + 1
        s["phase"] = "turn"
        s["partial_key"] = ()


def _end_round(s):
    locksmith = s["locksmith"]
    banked = list(s["banked"])
    opens = list(s["opens"])
    best_open = list(s["best_open"])
    bonus_seat = None

    if s["opened_by"] is not None:
        cracker = s["opened_by"]
        banked[cracker] += s["open_value"]
        opens[cracker] += 1
        if s["open_value"] > best_open[cracker]:
            best_open[cracker] = s["open_value"]
        banked[locksmith] += s["lane"]          # sec.8: no +5 on an opened round
    else:
        banked[locksmith] += s["lane"] + NO_OPEN_BONUS
        if s["deepest"] is not None:            # A10: a 0 still counts
            bonus_seat = s["deepest"][2]
            banked[bonus_seat] += DEEPEST_BONUS

    s["banked"] = tuple(banked)
    s["opens"] = tuple(opens)
    s["best_open"] = tuple(best_open)
    s["round_results"] = s["round_results"] + ((
        s["round_idx"], locksmith, s["opened_by"], s["open_value"],
        s["lane"], s["repins"], bonus_seat,
        -1 if s["deepest"] is None else s["deepest"][0],
    ),)
    s["locksmith_history"] = s["locksmith_history"] + (locksmith,)
    s["round_idx"] = s["round_idx"] + 1
    if s["round_idx"] >= s["n_rounds"]:
        s["phase"] = "done"
    else:
        _begin_round(s)


# --------------------------------------------------------------------------
# outcome
# --------------------------------------------------------------------------

def winners(state):
    """sec.7's tiebreak, applied in order. It always leaves exactly one seat."""
    if state["phase"] != "done":
        return []
    seats = list(range(state["n"]))
    for key in (lambda seat: state["banked"][seat],
                lambda seat: state["opens"][seat],
                lambda seat: state["best_open"][seat],
                lambda seat: _last_locksmith_round(state, seat)):
        top = max(key(seat) for seat in seats)
        seats = [seat for seat in seats if key(seat) == top]
        if len(seats) == 1:
            break
    return seats


def _last_locksmith_round(state, seat):
    history = state["locksmith_history"]
    for idx in range(len(history) - 1, -1, -1):
        if history[idx] == seat:
            return idx
    return -1


def scores(state):
    """Progress toward winning, per seat, every turn.

    Banked points plus this round's partial credit:

    * Locksmith: the lane peg they are actually sitting on, plus the +5 for an
      unopened round accrued as the time rail burns down. Paying 2 for a
      re-pin shows up immediately as a dip.
    * Cracker: how much of the money still on the table their standing
      knowledge is worth -- 0.35 * (time rail now) * (live confirmed prefix /
      5) -- plus the 3-point deepest-reading bonus accrued over the round for
      whoever currently holds the deepest reading. The first term falls every
      turn as the rail decays and falls hard when a re-pin rots a confirmed
      prefix, so a Locksmith swap is visible in the trace as a lead change.
    """
    out = []
    for seat in range(state["n"]):
        value = float(state["banked"][seat])
        if state["phase"] != "done":
            value += _partial(state, seat)
        out.append(value)
    return out


def _partial(s, seat):
    elapsed = _elapsed(s)
    if seat == s["locksmith"]:
        return float(s["lane"]) + NO_OPEN_BONUS * elapsed / float(RAIL_TOP)
    value = 0.35 * _rail(s) * (_live_prefix(s, seat) / float(N_CHAMBERS))
    deepest = s["deepest"]
    if deepest is not None and deepest[2] == seat:
        value += DEEPEST_BONUS * elapsed / float(RAIL_TOP)
    return value


# --------------------------------------------------------------------------
# what a seat may know
# --------------------------------------------------------------------------

def observation(state, seat):
    n = state["n"]
    lines = []
    lines.append(
        "Re-Pin -- round %d of %d. You are seat %d of %d."
        % (state["round_idx"] + 1, state["n_rounds"], seat, n))
    lines.append(
        "Score board: " + ", ".join(
            "seat %d = %d" % (i, state["banked"][i]) for i in range(n)) + ".")

    if state["round_results"]:
        past = []
        for (idx, ls, opened_by, value, lane, repins, bonus, deep) in state["round_results"]:
            if opened_by is None:
                past.append("round %d: seat %d was Locksmith, lock never opened "
                            "(lane %d after %d re-pin(s), so %d; deepest reading "
                            "%s)" % (idx + 1, ls, lane, repins,
                                     lane + NO_OPEN_BONUS,
                                     "none" if deep < 0
                                     else "%d to seat %d" % (deep, bonus)))
            else:
                past.append("round %d: seat %d was Locksmith, seat %d opened the "
                            "lock for %d (Locksmith banked %d after %d re-pin(s))"
                            % (idx + 1, ls, opened_by, value, lane, repins))
        lines.append("Earlier rounds -- " + "; ".join(past) + ".")

    if state["phase"] == "done":
        won = winners(state)
        lines.append("The game is over. Seat %d wins." % won[0])
        return "\n".join(lines)

    locksmith = state["locksmith"]
    lines.append(
        "This round seat %d is the Locksmith; the Crackers take turns in this "
        "order: %s." % (locksmith,
                        ", ".join("seat %d" % c for c in state["crackers"])))
    lines.append("You are the %s."
                 % ("LOCKSMITH" if seat == locksmith else "CRACKER"))

    if state["cut_rail"]:
        lines.append(
            "Cut rail (public): the Locksmith started this round with rungs "
            "%s, in an unknown order across chambers 1-5. Re-pins since then "
            "can have brought in any rung 1-8."
            % " ".join(str(r) for r in state["cut_rail"]))
    else:
        lines.append("The lock is not loaded yet.")

    lines.append(
        "Time rail: %d of %d. A Cracker who opens the lock on this turn banks "
        "%d. Locksmith lane: %d (+1 every turn the lock survives, -2 per "
        "re-pin; +5 more if the lock is never opened)."
        % (_rail(state), RAIL_TOP, _rail(state), state["lane"]))

    if state["log"]:
        lines.append("This round so far:")
        for entry in state["log"]:
            if entry[0] == "probe":
                lines.append(
                    "  turn %d -- seat %d probed %s, reading %d"
                    % (entry[1], entry[2],
                       " ".join(str(v) for v in entry[3]), entry[4]))
            elif entry[0] == "hold":
                lines.append("  turn %d -- seat %d held" % (entry[1], entry[2]))
            else:
                lines.append(
                    "  turn %d -- the Locksmith announced a re-pin and paid 2 "
                    "(which chamber, and which rung went in, are secret)"
                    % entry[1])
    else:
        lines.append("No turn has been taken this round yet.")

    if seat != locksmith:
        mine = [(t, g) for (t, p, _k, g) in state["probes"] if p == seat]
        if mine:
            best = max(g for _t, g in mine)
            when = min(t for t, g in mine if g == best)
            lines.append(
                "Your own best reading this round: %d, on turn %d. A reading "
                "of r means chambers 1..r were right at that moment and says "
                "nothing about chamber r+1 or beyond." % (best, when))
        else:
            lines.append("You have not probed this round.")
    else:
        lines.append(
            "SECRET, yours alone -- chambers 1-5 hold rungs %s; your reserve "
            "holds rungs %s."
            % (" ".join(str(r) for r in state["chambers"]) or "(not loaded)",
               " ".join(str(r) for r in state["reserve"]) or "(not drawn)"))

    lines.append(_pending(state, seat))
    return "\n".join(lines)


def _pending(state, seat):
    phase = state["phase"]
    mover = player_to_move(state)
    if seat != mover:
        return "Waiting on seat %d." % mover
    if phase == "load_pins":
        return ("YOUR DECISION: pick the five pins to load. Each move is one "
                "multiset of five rungs, listed in ascending order; this "
                "choice becomes the public cut rail. Moves are ordered "
                "lexicographically over the five rungs.")
    if phase == "arrange":
        return ("YOUR DECISION: place your five pins into chambers 1-5. Each "
                "move is one ordering, chamber 1 first. This is secret. Moves "
                "are ordered lexicographically.")
    if phase == "reserve":
        return ("YOUR DECISION: draw three secret reserve pins from the case "
                "(at most 5 pins of any rung exist, and you have already taken "
                "your five). Each move is one multiset of three rungs, ordered "
                "lexicographically.")
    if phase == "turn":
        done = len(state["partial_key"])
        if done == 0:
            return ("YOUR TURN: Hold, or start a Probe by setting slider 1. "
                    "Moves are listed as Hold first, then slider 1 = 1..8. "
                    "Choosing any slider value commits you to a Probe.")
        return ("Your key so far reads %s. YOUR DECISION: set slider %d. Moves "
                "are slider %d = 1..8."
                % (" ".join(str(v) for v in state["partial_key"]),
                   done + 1, done + 1))
    if phase == "repin":
        return ("YOUR DECISION: re-pin or not. Moves are: decline first, then "
                "one move per (chamber, reserve rung) pair -- chamber 1 to 5, "
                "and within a chamber the rungs your reserve holds, ascending. "
                "A re-pin costs 2 from your lane and is announced, but which "
                "chamber and which rung stay secret.")
    return "Waiting on seat %d." % mover
