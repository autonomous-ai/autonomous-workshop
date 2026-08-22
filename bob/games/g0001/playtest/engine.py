"""CRANK — playable engine for games/g0001.

One shared peg plate, one communal crank. On your turn you bolt one part onto
the plate (or pull one off, or slide your dial), then you turn the handle three
clicks — one revolution, thirteen teeth into the machine — and every dial that
has a live run of teeth back to the Drive Gear moves at once. Even mesh count
climbs, odd mesh count falls. First counter to 20 wins.

The whole machine is exact integer geometry: every gear is 3 mm module, every
plate hole is 3 mm from the next, so two gears mesh when their holes are
exactly (my teeth + their teeth) / 2 holes apart and foul when they are any
closer. That is the one rule the rest of the engine is built out of.

Contract: loops/playtest.py module docstring. Stdlib only, pure functions,
deterministic from the seed handed to new_game.
"""

import math
import random

IDEA_SHA = "a9e2d5ff03fa69e0449ca74a5ab5c6a1a1eb251dc315d8c0dc930aeeb8f44e7f"

# ---------------------------------------------------------------------------
# ASSUMPTIONS — every place RULES.md was silent, ambiguous, or physically
# under-determined, closed by an explicit ruling instead of a silent guess.
# ---------------------------------------------------------------------------

ASSUMPTIONS = [
    "A1 GEOMETRY / hole indexing. RULES.md §2 gives an 81x81 grid numbered "
    "1-81 in both axes and puts the Crank Post at (column 34, row 46). The "
    "engine indexes holes 1..81 inclusive on both axes with the Drive Gear "
    "fixed at (34, 46) and nothing outside that square.",

    "A2 GEOMETRY / mesh and foul are Euclidean. RULES.md §5a says two gears "
    "mesh at exactly (t1+t2)/2 holes apart and that 'no two gears may ever sit "
    "closer than their mesh number', but only ever measures along a row, a "
    "column, or one of the six listed slants. The engine rules that BOTH tests "
    "are true Euclidean centre distance in hole units: mesh iff "
    "4*(dc^2+dr^2) == (t1+t2)^2, foul iff 4*(dc^2+dr^2) < (t1+t2)^2. The six "
    "slants in the §5a table are exactly the Pythagorean offsets that land on "
    "a whole number, so this reproduces the printed table and also fouls "
    "correctly on the infinitely many non-integer offsets the table cannot "
    "list. IF THIS IS WRONG the plate holds far more gears than the rules "
    "claim and the 'big gear kills a neighbourhood' weapon in §5a evaporates.",

    "A3 DIAL / dockable band. RULES.md §3.6 and §5d say the arm reaches 'any "
    "hole 1 to 14 holes in from that rim'. The engine reads hole (c,r) as "
    "dockable iff min(c, 82-c, r, 82-r) <= 14 — i.e. column 1-14 or 68-81, or "
    "row 1-14 or 68-81. This matches the worked example (§6: left rim, arm 13 "
    "holes in, hole column 14).",

    "A4 SETUP / docking is not a move. RULES.md §3.6 makes docking a real "
    "player decision taken in reverse turn order before play. The engine "
    "contract's first legal_moves must already be a turn action, so new_game "
    "randomises every seat's opening dock from the seed (reverse turn order, "
    "no two dials on one hole, and for 2 players the two dials on different "
    "rims per §3.6). Seats can and do fix a bad opening dock with §5d Re-dock "
    "from turn 1. IF THIS IS WRONG the real game has a whole opening "
    "mini-draft the sim never sees, and the left rim — 20 holes from the "
    "off-centre crank, against 34/45/35 for the other three — is worth "
    "fighting over.",

    "A5 RULES GAP / the plate is not symmetric and the rules never say so. "
    "The Crank Post sits at (34,46) of an 81x81 field, so the left rim is 20 "
    "holes away, the far rim 35, the near rim 45, the right rim 47. Max mesh "
    "distance in the box is 29 (Gear 29 to Gear 29), so a seat docked on the "
    "left rim can be live in two placements while a seat on the right rim "
    "needs at least three. RULES.md calls this 'off-centre on purpose' and "
    "then never balances it. The engine implements the geometry as printed; "
    "with random docks (A4) the advantage lands on a random seat rather than "
    "a fixed one, which is why seat-bias numbers will look calm and the real "
    "table's will not.",

    "A6 HUB / ratio does not depend on which end is driven. RULES.md §5b "
    "lists six sealed (speed, direction) pairs and §5b says you read speed by "
    "how much farther the FAR end travels than the near end — which makes "
    "speed a property of the drive direction. A real planetary stack driven "
    "backwards gives the reciprocal, and the six listed pairs are not closed "
    "under reciprocal (x2-same has no /2-same partner, x3-flip no /3-flip). "
    "The engine rules that each hub carries one fixed (speed, direction) that "
    "applies whichever end the drive reaches first, and that placing the hub "
    "'backwards' is impossible because the two ends are identical. IF THIS IS "
    "WRONG then orientation is a hidden coin flip at every hub placement and "
    "the six-hub catalog needs to be six reciprocal PAIRS.",

    "A7 HUB / a hub is two 11-tooth nodes and a bridge that fouls nothing. "
    "RULES.md §2 gives the hub an 87 x 39 x 14 bridge body spanning 16 holes. "
    "The engine models only the two 11-tooth ends for mesh and foul; the "
    "bridge is treated as passing over the gear plane and blocking nothing "
    "between its ends. IF THIS IS WRONG a hub sterilises a 16-hole corridor "
    "every time it is placed.",

    "A8 DIAL / a dial reads plain gears only. RULES.md §2 gives the follower "
    "track to 'every gear' and gives the hub ends a red index tooth instead; "
    "§8 says 'the gear your dial reads'. The engine rules that a hub end under "
    "a dial arm drives nothing — the dial holds. Placing a hub end on a "
    "rival's read hole is therefore a legal kill.",

    "A9 DIAL / arms never foul. RULES.md §5a lists 'fouls a Dial Unit arm' as "
    "a failed placement but never gives the arm a footprint. The engine models "
    "no arm collision at all (the arm rides above the gear plane and §9 "
    "explicitly allows placing a gear on the hole an arm is over). IF THIS IS "
    "WRONG every docked dial projects a dead corridor from its rim and the "
    "plate is far smaller than it looks.",

    "A10 COUNTER / partial revolutions read by truncation toward zero. "
    "RULES.md §6 says the follower 'carries the remainder with it' and steps "
    "one number per full revolution either way, but never says what a counter "
    "reads part-way through a revolution in the negative direction. The engine "
    "tracks each dial's exact accumulated signed revolutions as an integer "
    "over a fixed denominator and displays truncation toward zero: 0.9 reads "
    "0, -0.9 reads 0, -1.2 reads -1.",

    "A11 CRANK / one crank resolves atomically. RULES.md §4 and §9 talk about "
    "a counter showing 20 'during a crank'. Nothing on the plate changes "
    "inside a revolution and every dial moves monotonically through it, so the "
    "engine resolves the whole revolution at once, then clamps (-5 freeze, 25 "
    "counter ceiling), then checks for 20. This is equivalent to resolving "
    "click by click for every case except a dial that would cross -5 and come "
    "back inside one revolution, which cannot happen at a fixed ratio.",

    "A12 COUNTER / ceiling at 25. RULES.md §2 says the counter reads -5 to 25 "
    "and §9 says an overshoot wins at the number shown. The engine caps a "
    "dial at exactly 25 and never above.",

    "A13 FREEZE / thaw timing. RULES.md §6 says a frozen dial 'comes back to "
    "life at the end of its owner's next turn'. The engine thaws after the "
    "crank of the owner's next turn, so a dial frozen on its owner's own crank "
    "sits out one full round and a dial frozen on someone else's crank sits "
    "out until its own next crank has resolved.",

    "A14 JAMS / rings are checked live or dead. RULES.md §9 rules that a "
    "closed ring jams if its mesh count is odd, and that any closed ring "
    "containing a hub jams always. It frames a jam as 'the handle will not "
    "turn', which would only be true of a ring connected to the Drive Gear. "
    "The engine applies both ring rules to EVERY closed ring on the plate, "
    "live or dead — rigid teeth in a locked ring are locked whether or not "
    "anything is driving them. IF THIS IS WRONG dead branches are a legal "
    "dumping ground for rings that would be illegal anywhere else.",

    "A15 JAMS / an illegal placement is simply not offered. RULES.md §9 says "
    "you discover a jam by trying to crank and then take the part back with no "
    "penalty. Since that costs nothing, the engine never emits a jamming "
    "placement as a legal move. The information a failed attempt would leak "
    "about a sealed hub (§9, 'the whole table just learned something for "
    "free') therefore does not exist in this engine — a real table has a "
    "free probing action the sim does not model.",

    "A16 HUB / one hub per run is checked against docked dials only. "
    "RULES.md §5b forbids placing a hub that 'would put two hubs between the "
    "handle and any player's read gear'. The engine checks exactly that, "
    "against each seat's currently read gear; a dial reading an empty hole "
    "imposes no constraint, and §9 confirms Pull and Re-dock may create "
    "two-hub runs freely.",

    "A17 HUB / a hub is read by the whole table once it is driven. RULES.md "
    "§5b says you learn a hub by cranking, and §9 says an unloaded hub still "
    "shows both index teeth. The engine reveals a hub's (speed, direction) to "
    "every seat after the first crank in which that hub is connected to the "
    "Drive Gear. Before that it is hidden from observation() for everybody, "
    "including the player who placed it.",

    "A18 END / 'a complete round with no building' is a rolling window. "
    "RULES.md §7 ends the game after a round in which no gear or hub was "
    "placed and no token spent. The engine ends it as soon as the last "
    "n_players consecutive turns were all Re-dock or Pass, wherever the round "
    "boundary happens to fall — the same condition, without needing to name a "
    "first player for the round.",

    "A19 TIEBREAK / shortest run is measured on the search tree. RULES.md §8 "
    "step 3 says to count the route with the fewest parts when the plate "
    "offers more than one. The engine counts parts along the path its "
    "breadth-first walk from the Drive Gear found (hub = one part, Drive Gear "
    "not counted). Legal states can still contain even-mesh plain-gear rings, "
    "so in that rare case the count may not be the provable minimum.",

    "A20 MOVE LIST / the legal-move list is a bounded, deterministic sample. "
    "This is the biggest liberty the engine takes, and it is a finding about "
    "the game, not about the code. Played literally, RULES.md offers a turn "
    "roughly 3,700 legal Re-docks (every hole within 14 of a rim) and several "
    "hundred legal gear placements — a branching factor no human reads and no "
    "search can afford. The engine enumerates candidates in a fixed sorted "
    "order, scans at most %d placement and %d hub candidates, and returns at "
    "most %d placements, %d hub placements, %d pulls and %d re-docks, sampled "
    "by even stride across the sorted candidate list so the sample spans the "
    "whole plate instead of one corner. Candidates themselves are generated "
    "off at most %d parts already on the plate (even stride over placement "
    "order). Re-dock targets are further narrowed to dockable holes that "
    "already hold a plain gear or that some gear in the tray could mesh into "
    "— docking on a hole no gear can ever reach is legal and pointless. Every "
    "number the sim reports is therefore measured on a sampled game tree; the "
    "real game is strictly wider, never narrower.",

    "A21 SAFETY / hard turn ceiling, and RULES.md §7's length arithmetic is "
    "wrong. §7 claims a 'hard ceiling 66 turns of the handle' from 40 gears + "
    "6 hubs + 16 tokens + one round. That only holds if every turn either "
    "builds or is part of the final dead round. Re-dock (§5d) is free, "
    "unlimited, and resets nothing: at 4 players three seats can re-dock every "
    "round forever as long as one seat still builds, so the true ceiling is "
    "about n_players x 63, i.e. ~250 cranks at four players, not 66. Random "
    "play already reaches 83. The engine implements the rules as written and "
    "stops any game at %d turns (highest dial wins on the §8 tiebreak) so a "
    "rules hole can never hang the harness; that stop firing would itself be "
    "finding #1.",

    "A22 END / ending 2 has no floor and can fire on turn 2. RULES.md §7's "
    "second ending needs only 'a complete round with no building'. Nothing "
    "stops that round from being the first: two seats that both Re-dock end a "
    "2-player game at 0-0 on the second crank, decided entirely by §8 "
    "tiebreaks. The engine implements it literally, which is why random-policy "
    "playouts produce a tail of very short games. A minimum-turns floor, or "
    "making the no-build ending require at least one part on the plate beyond "
    "the Drive Gear, would close it.",
]


# ---------------------------------------------------------------------------
# Board constants (RULES.md §2)
# ---------------------------------------------------------------------------

GRID = 81                       # holes 1..81 on each axis
CRANK_COL = 34
CRANK_ROW = 46
DRIVE_TEETH = 13
TEETH = (11, 13, 17, 19, 23, 29)
TRAY_QTY = (6, 8, 8, 7, 6, 5)   # 40 gears, RULES.md §2
HUB_TEETH = 11
HUB_SPAN = 16                   # hub spigot centres, holes apart
N_HUBS = 6
TOKENS_EACH = 4
DOCK_DEPTH = 14
WIN_AT = 20
FREEZE_AT = -5
COUNTER_CEIL = 25
MAX_TURNS = 260                 # A21 safety net; §7 argues 66 is the real cap

#: The six sealed hubs (RULES.md §5b), each in the box exactly once:
#: (speed numerator, speed denominator, reverses direction, label).
HUB_CONTENTS = (
    (2, 1, False, "x2 same"),
    (3, 1, False, "x3 same"),
    (1, 3, False, "/3 same"),
    (2, 1, True, "x2 flip"),
    (3, 1, True, "x3 flip"),
    (1, 2, True, "/2 flip"),
)

#: RULES.md §5a slant table: offset -> whole number of holes apart. Every one
#: is a Pythagorean triple, which is why the distance comes out integral.
SLANTS = {13: (5, 12), 15: (9, 12), 17: (8, 15),
          20: (12, 16), 26: (10, 24), 29: (20, 21)}

#: Move-list caps (A20). Tuned so a full simmetrics battery — probe, 1000-game
#: main batch, ladder and mirrors at every rung — finishes inside its wall
#: budget; the lookahead rung costs O(branching^2) per decision.
MAX_GEN_NODES = 12
MAX_PLACE_SCAN = 32
MAX_PLACE_MOVES = 8
MAX_HUB_SCAN = 12
MAX_HUB_MOVES = 2
MAX_PULL_MOVES = 4
MAX_REDOCK_MOVES = 3

ASSUMPTIONS[19] = ASSUMPTIONS[19] % (
    MAX_PLACE_SCAN, MAX_HUB_SCAN, MAX_PLACE_MOVES, MAX_HUB_MOVES,
    MAX_PULL_MOVES, MAX_REDOCK_MOVES, MAX_GEN_NODES)
ASSUMPTIONS[20] = ASSUMPTIONS[20] % (MAX_TURNS,)


def _build_offsets():
    """hole offsets at exactly d holes: 4 straight + 8 slant mirrors (§5a)."""
    table = {}
    for d in range(11, 30):
        out = set(((d, 0), (-d, 0), (0, d), (0, -d)))
        pair = SLANTS.get(d)
        if pair:
            a, b = pair
            for p, q in ((a, b), (b, a)):
                out.add((p, q))
                out.add((-p, q))
                out.add((p, -q))
                out.add((-p, -q))
        table[d] = tuple(sorted(out))
    return table


OFFSETS = _build_offsets()

#: Dockable columns/rows, precomputed (ruling A3) — a list index beats four
#: comparisons in the candidate loop, which runs ~700 times per turn.
DOCK_EDGE = tuple(
    (1 <= v <= DOCK_DEPTH) or (GRID + 1 - DOCK_DEPTH <= v <= GRID)
    for v in range(GRID + 2))

#: (dc, dr, teeth) for every gear still in the tray, flattened per driving
#: tooth count and cached by tray-availability mask. Turning the two-level
#: (tooth count x offset) loop into one flat loop is the single hottest
#: saving in move generation.
_FLAT = {}


def _flat_offsets(ti, mask):
    key = (ti, mask)
    got = _FLAT.get(key)
    if got is None:
        out = []
        for k in range(6):
            if mask & (1 << k):
                tg = TEETH[k]
                for dc, dr in OFFSETS[(ti + tg) >> 1]:
                    out.append((dc, dr, tg))
        got = tuple(out)
        _FLAT[key] = got
    return got

#: Exact dial arithmetic without fractions: one revolution = DEN units.
#: lcm(11,13,17,19,23,29) * 6, the 6 covering every hub speed denominator
#: (/2 and /3 are the only reducing hubs, so any product of hub speeds has a
#: denominator dividing 6). Every dial step is therefore an exact integer.
_TEETH_LCM = 11 * 13 * 17 * 19 * 23 * 29
DEN = _TEETH_LCM * 6
TEETH_PER_CRANK = DRIVE_TEETH   # one revolution of the handle, RULES.md §6

# Board tuple layout.
B_NC, B_NR, B_NT, B_NP, B_NH = 0, 1, 2, 3, 4
B_HUBS, B_EDGES = 5, 6
B_PAR, B_MN, B_MD, B_HC, B_DIST = 7, 8, 9, 10, 11
B_OCC, B_JAM = 12, 13

# Dial tuple layout.
D_COL, D_ROW, D_POS, D_FRZ, D_FT = 0, 1, 2, 3, 4


class _State(object):
    """Immutable by convention: apply() only ever builds a fresh one."""

    __slots__ = ("n", "turn", "to_move", "last_cranker", "idle", "over",
                 "board", "dials", "tray", "mag", "tokens", "win", "sc",
                 "moves")


def _clone(s):
    t = _State()
    t.n = s.n
    t.turn = s.turn
    t.to_move = s.to_move
    t.last_cranker = s.last_cranker
    t.idle = s.idle
    t.over = s.over
    t.board = s.board
    t.dials = s.dials
    t.tray = s.tray
    t.mag = s.mag
    t.tokens = s.tokens
    t.win = s.win
    t.sc = s.sc
    t.moves = None
    return t


# ---------------------------------------------------------------------------
# The machine: mesh graph, direction parity, speed ratio
# ---------------------------------------------------------------------------

def _analyze(nc, nr, nt, npart, nhub, hubs, edges):
    """Walk the plate from the Drive Gear out.

    Returns (par, mn, md, hc, dist, jam):
      par[i]  parity of the mesh count from the Drive Gear, -1 if the node has
              no path to it at all (a dead branch). Even climbs, odd falls.
      mn/md   speed multiplier as an exact fraction (product of hub speeds).
      hc[i]   hubs between the Drive Gear and this node (RULES.md §5b cap).
      dist[i] parts between the Drive Gear and this node, hub = one part (§8).
      jam     True if any closed ring is odd-mesh or contains a hub (§9).
    """
    n = len(nc)
    par = [-1] * n
    mn = [1] * n
    md = [1] * n
    hc = [0] * n
    dist = [0] * n
    parent = [-1] * n
    phub = [False] * n
    any_hub = bool(hubs)
    jam = False
    for root in range(n):
        if par[root] >= 0:
            continue
        par[root] = 0
        stack = [root]
        while stack:
            i = stack.pop()
            pi = par[i]
            qi = 1 - pi
            mi = mn[i]
            di = md[i]
            hi = hc[i]
            si = dist[i]
            par_i = parent[i]
            for j in edges[i]:
                if par[j] < 0:
                    par[j] = qi
                    mn[j] = mi
                    md[j] = di
                    hc[j] = hi
                    dist[j] = si + 1
                    parent[j] = i
                    stack.append(j)
                elif par_i != j and par[j] == pi:
                    jam = True          # odd ring, RULES.md §9
                elif any_hub and par_i != j and not jam:
                    if _cycle_has_hub(i, j, parent, phub):
                        jam = True      # ring through a hub, RULES.md §9
            p = npart[i]
            if p >= 0:
                content = HUB_CONTENTS[hubs[nhub[i]][2]]
                num = content[0]
                dn = content[1]
                flip = content[2]
                if par[p] < 0:
                    par[p] = pi ^ (1 if flip else 0)
                    g = mi * num
                    k = di * dn
                    f = math.gcd(g, k)
                    mn[p] = g // f
                    md[p] = k // f
                    hc[p] = hi + 1
                    dist[p] = si
                    parent[p] = i
                    phub[p] = True
                    stack.append(p)
                elif parent[i] != p:
                    jam = True          # any ring containing a hub, §9
    return par, mn, md, hc, dist, jam


def _cycle_has_hub(i, j, parent, phub):
    """Does the tree cycle closed by the back edge i-j run through a hub?"""
    anc = set()
    x = i
    while x >= 0:
        anc.add(x)
        x = parent[x]
    hub = False
    y = j
    while y not in anc:
        if phub[y]:
            hub = True
        y = parent[y]
    lca = y
    x = i
    while x != lca:
        if phub[x]:
            hub = True
        x = parent[x]
    return hub


def _pack(nc, nr, nt, npart, nhub, hubs, edges, occ=None):
    par, mn, md, hc, dist, jam = _analyze(nc, nr, nt, npart, nhub, hubs, edges)
    if occ is None:
        occ = {}
        for i in range(len(nc)):
            occ[(nc[i], nr[i])] = i
    return (nc, nr, nt, npart, nhub, hubs, edges,
            par, mn, md, hc, dist, occ, jam)


def _empty_board():
    nc = (CRANK_COL,)
    nr = (CRANK_ROW,)
    nt = (DRIVE_TEETH,)
    return _pack(nc, nr, nt, (-1,), (-1,), (), ((),))


def _add_gear(b, col, row, teeth, meshes):
    """New board with one gear appended at index len(nodes)."""
    k = len(b[B_NC])
    ms = set(meshes)
    edges = tuple(
        (b[B_EDGES][i] + (k,)) if i in ms else b[B_EDGES][i]
        for i in range(k)) + (tuple(sorted(meshes)),)
    occ = dict(b[B_OCC])
    occ[(col, row)] = k
    return _pack(b[B_NC] + (col,), b[B_NR] + (row,), b[B_NT] + (teeth,),
                 b[B_NP] + (-1,), b[B_NH] + (-1,), b[B_HUBS], edges, occ)


def _add_hub(b, c1, r1, c2, r2, content, mesh1, mesh2):
    """New board with a two-ended hub appended (indices k and k+1)."""
    k = len(b[B_NC])
    slot = len(b[B_HUBS])
    m1 = set(mesh1)
    m2 = set(mesh2)
    old = []
    for i in range(k):
        e = b[B_EDGES][i]
        if i in m1:
            e = e + (k,)
        if i in m2:
            e = e + (k + 1,)
        old.append(e)
    edges = tuple(old) + (tuple(sorted(mesh1)), tuple(sorted(mesh2)))
    hubs = b[B_HUBS] + ((k, k + 1, content, False),)
    occ = dict(b[B_OCC])
    occ[(c1, r1)] = k
    occ[(c2, r2)] = k + 1
    return _pack(b[B_NC] + (c1, c2), b[B_NR] + (r1, r2),
                 b[B_NT] + (HUB_TEETH, HUB_TEETH),
                 b[B_NP] + (k + 1, k), b[B_NH] + (slot, slot), hubs, edges, occ)


def _remove(b, drop):
    """New board with the node indices in `drop` gone (a Pull, RULES.md §5c)."""
    keep = [i for i in range(len(b[B_NC])) if i not in drop]
    remap = {}
    for new, old in enumerate(keep):
        remap[old] = new
    nc = tuple(b[B_NC][i] for i in keep)
    nr = tuple(b[B_NR][i] for i in keep)
    nt = tuple(b[B_NT][i] for i in keep)
    hub_slots = {}
    hubs = []
    for slot, h in enumerate(b[B_HUBS]):
        if h[0] in drop:
            continue
        hub_slots[slot] = len(hubs)
        hubs.append((remap[h[0]], remap[h[1]], h[2], h[3]))
    npart = tuple(remap[b[B_NP][i]] if b[B_NP][i] >= 0 else -1 for i in keep)
    nhub = tuple(hub_slots[b[B_NH][i]] if b[B_NH][i] >= 0 else -1 for i in keep)
    edges = tuple(
        tuple(remap[j] for j in b[B_EDGES][i] if j in remap) for i in keep)
    return _pack(nc, nr, nt, npart, nhub, tuple(hubs), edges)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def _dockable(col, row):
    """RULES.md §3.6 / §5d, ruling A3."""
    return DOCK_EDGE[col] or DOCK_EDGE[row]


def _fit(b, col, row, teeth):
    """Mesh partners for a part of `teeth` teeth at (col,row), or None if it
    fouls anything (RULES.md §5a). Empty list means it touches nothing."""
    nc = b[B_NC]
    nr = b[B_NR]
    nt = b[B_NT]
    meshes = []
    for j in range(len(nc)):
        dc = nc[j] - col
        dr = nr[j] - row
        s = teeth + nt[j]
        q = 4 * (dc * dc + dr * dr) - s * s
        if q < 0:
            return None
        if q == 0:
            meshes.append(j)
    return meshes


def _read_node(b, col, row):
    """Node index of the plain gear under a dial arm, else -1 (ruling A8)."""
    i = b[B_OCC].get((col, row), -1)
    if i < 0 or b[B_NH][i] >= 0:
        return -1
    return i


def _rate_units(b, i):
    """Signed dial units per crank for the gear at node i (0 if dead)."""
    par = b[B_PAR][i]
    if par < 0:
        return 0
    step = (TEETH_PER_CRANK * DEN * b[B_MN][i]) // (b[B_MD][i] * b[B_NT][i])
    return -step if par else step


def _counter(pos):
    """Displayed counter from exact accumulated revolutions (ruling A10)."""
    if pos >= 0:
        return pos // DEN
    return -((-pos) // DEN)


# ---------------------------------------------------------------------------
# Move generation
# ---------------------------------------------------------------------------

def _stride(items, limit):
    """Evenly spread sample of a sorted list — deterministic, spans the whole
    range instead of truncating to one corner of the plate (ruling A20)."""
    n = len(items)
    if n <= limit:
        return list(items)
    return [items[(k * n) // limit] for k in range(limit)]


def _gen_moves(s):
    b = s.board
    nc = b[B_NC]
    nr = b[B_NR]
    nt = b[B_NT]
    occ = b[B_OCC]
    n_nodes = len(nc)
    seat = s.to_move

    # Candidates are generated off parts already on the plate (§5a: a new
    # part must mesh something already down), so the search never touches
    # the 6,561-hole field — only the <=12 offsets at each mesh distance.
    if n_nodes <= MAX_GEN_NODES:
        gen = range(n_nodes)
    else:
        gen = [(k * n_nodes) // MAX_GEN_NODES for k in range(MAX_GEN_NODES)]

    # --- 5a Place a gear -------------------------------------------------
    mask = 0
    tray = s.tray
    for k in range(6):
        if tray[k] > 0:
            mask |= 1 << k
    hole_cands = []
    dock_cands = []
    dock_seen = set()
    for i in gen:
        ci = nc[i]
        ri = nr[i]
        for dc, dr, tg in _flat_offsets(nt[i], mask):
            c = ci + dc
            if c < 1 or c > GRID:
                continue
            r = ri + dr
            if r < 1 or r > GRID:
                continue
            hole = (c, r)
            if hole in occ:
                continue
            hole_cands.append((c, r, tg))
            if (DOCK_EDGE[c] or DOCK_EDGE[r]) and hole not in dock_seen:
                dock_seen.add(hole)
                dock_cands.append(hole)
    placements = []
    scanned = set()
    for cand in _stride(hole_cands, MAX_PLACE_SCAN):
        if cand in scanned:
            continue        # a hole two parts can both mesh, generated twice
        scanned.add(cand)
        c, r, tg = cand
        meshes = _fit(b, c, r, tg)
        if not meshes:
            continue
        if len(meshes) > 1 and _add_gear(b, c, r, tg, meshes)[B_JAM]:
            continue
        placements.append(("place", tg, c, r))
    moves = _stride(placements, MAX_PLACE_MOVES)

    # --- 5b Draw and place a hub ----------------------------------------
    if s.mag:
        hseen = set()
        hcands = []
        for i in gen:
            ci = nc[i]
            ri = nr[i]
            for dc, dr in OFFSETS[(nt[i] + HUB_TEETH) >> 1]:
                ca = ci + dc
                if ca < 1 or ca > GRID:
                    continue
                ra = ri + dr
                if ra < 1 or ra > GRID or (ca, ra) in occ:
                    continue
                for ec, er in ((HUB_SPAN, 0), (-HUB_SPAN, 0),
                               (0, HUB_SPAN), (0, -HUB_SPAN)):
                    cb = ca + ec
                    if cb < 1 or cb > GRID:
                        continue
                    rb = ra + er
                    if rb < 1 or rb > GRID or (cb, rb) in occ:
                        continue
                    key = ((ca, ra, cb, rb) if (ca, ra) < (cb, rb)
                           else (cb, rb, ca, ra))
                    if key not in hseen:
                        hseen.add(key)
                        hcands.append(key)
        hubs = []
        for c1, r1, c2, r2 in _stride(hcands, MAX_HUB_SCAN):
            if _hub_ok(s, c1, r1, c2, r2):
                hubs.append(("hub", c1, r1, c2, r2))
        moves.extend(_stride(hubs, MAX_HUB_MOVES))

    # --- 5c Pull ---------------------------------------------------------
    if s.tokens[seat] > 0:
        pulls = []
        for i in range(1, n_nodes):
            if b[B_NH][i] < 0:
                pulls.append(("pull", nc[i], nr[i]))
            elif i < b[B_NP][i]:
                pulls.append(("pull", nc[i], nr[i]))
        moves.extend(_stride(sorted(pulls), MAX_PULL_MOVES))

    # --- 5d Re-dock ------------------------------------------------------
    blocked = set()
    for k in range(s.n):
        blocked.add((s.dials[k][D_COL], s.dials[k][D_ROW]))
    for i in range(1, n_nodes):
        if b[B_NH][i] < 0:
            c = nc[i]
            r = nr[i]
            if (c <= DOCK_DEPTH or c >= GRID + 2 - DOCK_DEPTH
                    or r <= DOCK_DEPTH or r >= GRID + 2 - DOCK_DEPTH):
                if (c, r) not in dock_seen:
                    dock_seen.add((c, r))
                    dock_cands.append((c, r))
    free = [h for h in dock_cands if h not in blocked]
    moves.extend(("redock", c, r)
                 for c, r in _stride(free, MAX_REDOCK_MOVES))

    # --- 5e Pass, forced only -------------------------------------------
    if not moves:
        return [("pass",)]
    moves.sort()
    return moves


def _hub_ok(s, c1, r1, c2, r2):
    """A hub placement is legal if both ends seat, at least one end meshes,
    no ring jams, and no docked dial ends up behind two hubs (§5b)."""
    b = s.board
    m1 = _fit(b, c1, r1, HUB_TEETH)
    if m1 is None:
        return False
    m2 = _fit(b, c2, r2, HUB_TEETH)
    if m2 is None:
        return False
    if not m1 and not m2:
        return False
    if len(m1) + len(m2) < 2 and not b[B_HUBS]:
        # One mesh edge and no hub already down: no ring can close (§9) and
        # no run can reach two hubs (§5b), so skip the full re-analysis.
        return True
    nb = _add_hub(b, c1, r1, c2, r2, s.mag[0], m1, m2)
    if nb[B_JAM]:
        return False
    for k in range(s.n):
        i = _read_node(nb, s.dials[k][D_COL], s.dials[k][D_ROW])
        if i >= 0 and nb[B_PAR][i] >= 0 and nb[B_HC][i] > 1:
            return False
    return True


# ---------------------------------------------------------------------------
# Scoring — progress toward 20, read every turn by the metrics
# ---------------------------------------------------------------------------

#: score = counter position (revolutions banked)
#:       + W_RATE * signed revolutions per crank the seat currently earns
#:       + W_NEAR * how close the live train has come to an unread dial hole
#:       + W_TOKEN * unspent Spanner Tokens (RULES.md §8 tiebreak 2)
W_RATE = 3.0
W_NEAR = 2.0
W_TOKEN = 0.05
NEAR_SPAN = 45.0


def _scores(s):
    b = s.board
    par = b[B_PAR]
    nc = b[B_NC]
    nr = b[B_NR]
    live = None
    out = []
    for k in range(s.n):
        d = s.dials[k]
        v = d[D_POS] / float(DEN) + W_TOKEN * s.tokens[k]
        i = _read_node(b, d[D_COL], d[D_ROW])
        if i >= 0 and par[i] >= 0 and not d[D_FRZ]:
            v += W_RATE * (_rate_units(b, i) / float(DEN))
        elif not d[D_FRZ]:
            if live is None:
                live = [j for j in range(len(nc)) if par[j] >= 0]
            # Not wired up yet: reward the train getting nearer the hole, so a
            # two-placement bend shows progress on its FIRST gear, not only on
            # its second (a step-only score reads as flat to the instruments).
            best = None
            for j in live:
                dc = nc[j] - d[D_COL]
                dr = nr[j] - d[D_ROW]
                q = dc * dc + dr * dr
                if best is None or q < best:
                    best = q
            if best is not None:
                near = 1.0 - math.sqrt(best) / NEAR_SPAN
                if near > 0.0:
                    v += W_NEAR * near
        out.append(v)
    return tuple(out)


# ---------------------------------------------------------------------------
# Tiebreak (RULES.md §8)
# ---------------------------------------------------------------------------

def _run_length(s, k):
    b = s.board
    i = _read_node(b, s.dials[k][D_COL], s.dials[k][D_ROW])
    if i < 0 or b[B_PAR][i] < 0:
        return 10 ** 6      # "no live run counts as longer than any run"
    return b[B_DIST][i]


def _resolve(s, candidates):
    """Work RULES.md §8 down until one seat is left. It always resolves."""
    pool = list(candidates)
    if len(pool) == 1:
        return pool
    best = max(_counter(s.dials[k][D_POS]) for k in pool)
    pool = [k for k in pool if _counter(s.dials[k][D_POS]) == best]
    if len(pool) == 1:
        return pool
    best = max(s.tokens[k] for k in pool)
    pool = [k for k in pool if s.tokens[k] == best]
    if len(pool) == 1:
        return pool
    runs = dict((k, _run_length(s, k)) for k in pool)
    best = min(runs.values())
    pool = [k for k in pool if runs[k] == best]
    if len(pool) == 1:
        return pool
    # Turn order: soonest to play, starting left of whoever cranked last.
    start = (s.last_cranker + 1) % s.n
    pool.sort(key=lambda k: (k - start) % s.n)
    return [pool[0]]


# ---------------------------------------------------------------------------
# The contract
# ---------------------------------------------------------------------------

def new_game(n_players, seed):
    if n_players < 2 or n_players > 4:
        raise ValueError(
            "CRANK seats 2-4 players (idea.json players 2-4); got %r"
            % (n_players,))
    rng = random.Random(seed)
    s = _State()
    s.n = n_players
    s.turn = 0
    s.to_move = 0
    s.last_cranker = n_players - 1
    s.idle = 0
    s.over = False
    s.win = ()
    s.board = _empty_board()
    s.tray = TRAY_QTY
    s.tokens = tuple([TOKENS_EACH] * n_players)
    mag = list(range(N_HUBS))
    rng.shuffle(mag)
    s.mag = tuple(mag)

    # A4: docking is randomised from the seed, in reverse turn order.
    dials = [None] * n_players
    used_holes = set()
    used_rims = set()
    for seat in range(n_players - 1, -1, -1):
        while True:
            rim = rng.randrange(4)
            if n_players == 2 and rim in used_rims:
                continue
            along = rng.randrange(1, GRID + 1)
            depth = rng.randrange(1, DOCK_DEPTH + 1)
            if rim == 0:
                col, row = depth, along
            elif rim == 1:
                col, row = GRID + 1 - depth, along
            elif rim == 2:
                col, row = along, depth
            else:
                col, row = along, GRID + 1 - depth
            if (col, row) in used_holes:
                continue
            if (col, row) == (CRANK_COL, CRANK_ROW):
                continue
            used_holes.add((col, row))
            used_rims.add(rim)
            dials[seat] = (col, row, 0, False, -1)
            break
    s.dials = tuple(dials)
    s.moves = None
    s.sc = _scores(s)
    return s


def player_to_move(state):
    return state.to_move


def legal_moves(state):
    if state.over:
        return []
    if state.moves is None:
        state.moves = _gen_moves(state)
    return list(state.moves)


def apply(state, move):
    """Do the action, then turn the handle three clicks. Never mutates input."""
    if state.over:
        raise ValueError("CRANK: the game is over; no move applies")
    s = _clone(state)
    seat = state.to_move
    b = state.board
    kind = move[0]

    if kind == "place":
        _t, teeth, col, row = move
        meshes = _fit(b, col, row, teeth)
        if not meshes:
            raise ValueError("CRANK: %r does not seat and mesh" % (move,))
        s.board = _add_gear(b, col, row, teeth, meshes)
        if s.board[B_JAM]:
            raise ValueError("CRANK: %r jams the machine (RULES.md §9)" % (move,))
        k = TEETH.index(teeth)
        if state.tray[k] <= 0:
            raise ValueError("CRANK: the Gear %d well is empty" % teeth)
        tray = list(state.tray)
        tray[k] -= 1
        s.tray = tuple(tray)
        s.idle = 0
    elif kind == "hub":
        _t, c1, r1, c2, r2 = move
        if not state.mag:
            raise ValueError("CRANK: the Hub Magazine is empty")
        m1 = _fit(b, c1, r1, HUB_TEETH)
        m2 = _fit(b, c2, r2, HUB_TEETH)
        if m1 is None or m2 is None or (not m1 and not m2):
            raise ValueError("CRANK: %r does not seat and mesh" % (move,))
        s.board = _add_hub(b, c1, r1, c2, r2, state.mag[0], m1, m2)
        if s.board[B_JAM]:
            raise ValueError("CRANK: %r jams the machine (RULES.md §9)" % (move,))
        s.mag = state.mag[1:]
        s.idle = 0
    elif kind == "pull":
        _t, col, row = move
        i = b[B_OCC].get((col, row), -1)
        if i <= 0:
            raise ValueError("CRANK: nothing pullable at %d,%d" % (col, row))
        if state.tokens[seat] <= 0:
            raise ValueError("CRANK: no Spanner Token to spend")
        drop = set((i,))
        if b[B_NP][i] >= 0:
            drop.add(b[B_NP][i])
        s.board = _remove(b, drop)
        tok = list(state.tokens)
        tok[seat] -= 1
        s.tokens = tuple(tok)
        s.idle = 0
    elif kind == "redock":
        _t, col, row = move
        if not _dockable(col, row):
            raise ValueError("CRANK: %d,%d is out of arm reach" % (col, row))
        d = state.dials[seat]
        dials = list(state.dials)
        dials[seat] = (col, row, d[D_POS], d[D_FRZ], d[D_FT])
        s.dials = tuple(dials)
        s.idle = state.idle + 1
    elif kind == "pass":
        s.idle = state.idle + 1
    else:
        raise ValueError("CRANK: unknown move %r" % (move,))

    # --- Step 2: three clicks of the handle (RULES.md §4) ----------------
    nb = s.board
    dials = list(s.dials)
    for k in range(s.n):
        d = dials[k]
        if d[D_FRZ]:
            continue
        i = _read_node(nb, d[D_COL], d[D_ROW])
        if i < 0 or nb[B_PAR][i] < 0:
            continue
        pos = d[D_POS] + _rate_units(nb, i)
        frozen = d[D_FRZ]
        ft = d[D_FT]
        if pos <= FREEZE_AT * DEN:
            pos = FREEZE_AT * DEN
            frozen = True
            ft = state.turn
        elif pos > COUNTER_CEIL * DEN:
            pos = COUNTER_CEIL * DEN
        dials[k] = (d[D_COL], d[D_ROW], pos, frozen, ft)

    # A13: a frozen dial thaws at the END of its owner's next turn.
    d = dials[seat]
    if d[D_FRZ] and d[D_FT] >= 0 and d[D_FT] < state.turn:
        dials[seat] = (d[D_COL], d[D_ROW], d[D_POS], False, -1)
    s.dials = tuple(dials)

    # A17: any hub the crank actually drove is now public.
    if nb[B_HUBS]:
        newhubs = []
        changed = False
        for h in nb[B_HUBS]:
            if not h[3] and nb[B_PAR][h[0]] >= 0:
                newhubs.append((h[0], h[1], h[2], True))
                changed = True
            else:
                newhubs.append(h)
        if changed:
            s.board = nb[:B_HUBS] + (tuple(newhubs),) + nb[B_HUBS + 1:]

    s.turn = state.turn + 1
    s.last_cranker = seat
    s.to_move = (seat + 1) % s.n

    # --- End conditions (RULES.md §7) ------------------------------------
    reached = [k for k in range(s.n) if _counter(s.dials[k][D_POS]) >= WIN_AT]
    if reached:
        s.over = True
        s.win = tuple(_resolve(s, reached))
    elif s.idle >= s.n:
        s.over = True
        s.win = tuple(_resolve(s, range(s.n)))
    elif s.turn >= MAX_TURNS:
        s.over = True
        s.win = tuple(_resolve(s, range(s.n)))

    s.sc = _scores(s)
    return s


def is_over(state):
    return state.over


def winners(state):
    return list(state.win) if state.over else []


def scores(state):
    return list(state.sc)


def observation(state, seat):
    b = state.board
    d = state.dials[seat]
    lines = []
    lines.append(
        "CRANK — turn %d, %d players. You are seat %d. Plate is 81x81 holes; "
        "the Crank Post with the 13-tooth Drive Gear is at column %d, row %d."
        % (state.turn + 1, state.n, seat, CRANK_COL, CRANK_ROW))
    lines.append(
        "Two parts mesh when their holes are exactly (my teeth + their teeth)/2 "
        "holes apart, and foul if any closer. Even mesh count from the Drive "
        "Gear climbs your dial, odd mesh count drains it. First to 20 wins; "
        "-5 freezes you for a round.")

    i = _read_node(b, d[D_COL], d[D_ROW])
    if i < 0:
        reads = "an empty hole — you earn nothing until something is bolted there"
    elif b[B_PAR][i] < 0:
        reads = ("a dead Gear %d — nothing connects it to the handle"
                 % b[B_NT][i])
    else:
        rate = _rate_units(b, i) / float(DEN)
        reads = ("a live Gear %d, %d mesh%s from the handle, %+.2f a crank"
                 % (b[B_NT][i], b[B_HC][i] + b[B_DIST][i],
                    "" if b[B_PAR][i] == 0 else " (odd, falling)", rate))
    lines.append(
        "Your dial: counter %d (exactly %.3f revolutions), arm over hole "
        "(%d,%d), reading %s.%s You hold %d Spanner Token(s)."
        % (_counter(d[D_POS]), d[D_POS] / float(DEN), d[D_COL], d[D_ROW],
           reads, " YOUR DIAL IS FROZEN AT -5." if d[D_FRZ] else "",
           state.tokens[seat]))

    for k in range(state.n):
        if k == seat:
            continue
        o = state.dials[k]
        j = _read_node(b, o[D_COL], o[D_ROW])
        if j < 0 or b[B_PAR][j] < 0:
            what = "reading nothing live"
        else:
            what = "reading a live Gear %d at %+.2f a crank" % (
                b[B_NT][j], _rate_units(b, j) / float(DEN))
        lines.append(
            "Seat %d: counter %d, dial on hole (%d,%d), %s, %d token(s)%s."
            % (k, _counter(o[D_POS]), o[D_COL], o[D_ROW], what,
               state.tokens[k], ", FROZEN" if o[D_FRZ] else ""))

    parts = []
    for idx in range(len(b[B_NC])):
        tag = "Drive Gear" if idx == 0 else (
            "Hub end" if b[B_NH][idx] >= 0 else "Gear %d" % b[B_NT][idx])
        state_word = "live" if b[B_PAR][idx] >= 0 else "dead"
        parts.append("%s at (%d,%d) [%s]"
                     % (tag, b[B_NC][idx], b[B_NR][idx], state_word))
    lines.append("On the plate: " + ("; ".join(parts) if parts else "nothing"))

    if b[B_HUBS]:
        hb = []
        for slot, h in enumerate(b[B_HUBS]):
            if h[3]:
                hb.append("hub %d at (%d,%d)-(%d,%d) reads %s"
                          % (slot + 1, b[B_NC][h[0]], b[B_NR][h[0]],
                             b[B_NC][h[1]], b[B_NR][h[1]],
                             HUB_CONTENTS[h[2]][3]))
            else:
                hb.append("hub %d at (%d,%d)-(%d,%d) UNREAD — nobody knows "
                          "what is inside it yet"
                          % (slot + 1, b[B_NC][h[0]], b[B_NR][h[0]],
                             b[B_NC][h[1]], b[B_NR][h[1]]))
        lines.append("Hubs down: " + "; ".join(hb))
    lines.append(
        "Gear Tray: " + ", ".join("%dx Gear %d" % (state.tray[k], TEETH[k])
                                  for k in range(6))
        + ". Hub Magazine: %d sealed hub(s) left (you never choose which)."
        % len(state.mag))
    lines.append(
        "No gear or hub has been placed and no token spent for %d "
        "consecutive turn(s); at %d the game ends and the highest dial wins."
        % (state.idle, state.n))
    return "\n".join(lines)
