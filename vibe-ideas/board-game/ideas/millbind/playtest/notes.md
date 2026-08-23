# Millbind — engine notes (second rework pass)

## What the SECOND rework changed (closing the fresh gate's 7 findings)

The first rework (fixed crank, distance-scaled grind, no pass-end) closed the
old collapse but the fresh machine gate failed with two blocking findings plus
downstream noise: termination (a reachable permanent pass/bind loop hit the
200-turn cap), and the bind-reading ambiguity in `rules:turn[5]`
("illegal" vs "costs your action"). The second rework settles both in the
rules and the engine reflects them:

- **Bind reading settled to (a), offered-and-wastes.** `rules:turn[5]` now
  states outright that a binding PLACE or SHIFT IS a legal move, offered like
  every other, and is resolved by reverting the piece and spending the turn;
  it is never withheld. The `ASSUMPTIONS`/`CHOICES` entry for `bind_illegal`
  is deleted — there is no longer a second reading to play both ways, so the
  sensitivity delta (38%) is gone. `legal_moves` in the actions phase therefore
  offers every empty-pin placement (binding or not) and every empty-yard-pin
  shift; `apply_move` tests, reverts and wastes the turn on a bind.
- **A STALLED MILL — the un-stallable clock (`rules:end[1]`), drain variant.**
  The old terminal state (every remaining gear binds, no free yard pin, every
  mill dead at even parity, only PASS legal) made neither supply-empty nor
  granary-empty fire, and the game looped to the cap. The first draft of the
  fix made a fully inert round END the game, which guaranteed termination but
  cut off up to a third of games at a near-even score (the fresh gate then
  flagged `tie:4p`). So the clock is a drain instead of an ending: any round
  in which no gear came to rest on a new pin, no millstone shifted to a new
  pin and the grind paid no pellet pays a ONE-pellet maintenance toll from the
  granary (discarded to no one), then play continues. Tracked by
  `state["round_active"]`, reset at the top of each round in `_enter_round`,
  set by a successful PLACE, a successful SHIFT, or any grind pay, and read at
  the end of `_process_grind`, where a seized round decrements the granary.

Termination is now a bound rather than a hope: a non-final productive round
must either place a gear (drains the 24-gear supply), pay a pellet (drains the
28-pellet granary), or shift a millstone (finite: a millstone can only move to
empty yard pins it has not just left), and a fully inert round drains one
pellet — so a pass/bind loop can never run to the 200-turn cap (`MAX_TURNS` is
now belt-and-suspenders). Because an inert round skims the granary rather than
stopping the grinding, games run onward to a real spread instead of seizing
with everyone level: measured at 4p random, `top-tie` rate dropped from ~30% to
~11% and no game hits the cap. Reading (a) also relieves the forced-turn
finding: the old one-move (pass-only) stall is now a many-move position (all
binding placements are legal options).

Model, payout, ends and observation are otherwise unchanged from the first
rework; the fixed-crank distance-scored core is untouched.

## Model

37 pins as hex/cube coordinates `(q, r, s=-q-r)`, `ring = max(|q|,|r|,|s|)`.
The six standard axial neighbour offsets are exactly the six nearest-neighbour
directions of a triangular lattice at unit spacing, so "hex distance 1" and
"physically 30mm apart, teeth able to touch" are the same relation — no
Cartesian coordinates needed. `ring <= 2` (19 pins) are inner pins, `ring == 3`
(18 pins) are yard pins. Verified: 37 pins total, 19 inner + 18 yard.

The bind test is a literal whole-graph odd-cycle check: build the mesh graph
from every occupied pin and its lattice-adjacent occupied neighbours where
tooth tiers are compatible (`gear_low`-`gear_low`, `gear_high`-`gear_high`, or
either side full-height), then 2-colour every component by BFS. A colour clash
anywhere is an odd cycle, i.e. bound.

The payout is distance-scaled from the SAME mesh graph: a BFS from the fixed
crank gives the shortest running chain to each millstone; the number of gears
between crank and millstone is `distance - 1`; a millstone pays exactly that
many pellets iff that count is odd (clockwise), and dead (even) or unreachable
pays nothing. While the game is always unbound (every entry tested), the mesh
graph is always bipartite so the parity is well-defined; the payout repeats a
real BFS every grind because the machine changes as gears are added.

Scores are the literal sack_spindle pellet counts, valid at every point in the
game, no proxy. `HIDDEN_INFO = False`: the yard, supply pile and every score
are visible to all seats; no `determinize`.

## What the rework deleted, and what the engine now does

- **POWER is gone.** The crank is placed once at `setup[4]` (`setup_crank` move,
  chosen by the first player on any empty yard pin) and never moves; there is
  no `power` action anywhere. `MOVE_KINDS = ("setup_crank", "setup_mill",
  "place", "shift", "pass")`.
- **Millstone snake at `setup[5]`.** `setup_mill` is a real move, not baked into
  `new_game`, sequence `[n-1, 0, 1, …, n-2]` (last player acts/places first,
  moving clockwise to the first) so the seat that acts last in a round gets to
  site its millstone with the fixed crank already visible. Setup order is crank
  first (`setup[4]`), then the snake (`setup[5]`).
- **Distance-scaled payout, solo bonus deleted.** The old flat "2 for a lone
  mill, 1 otherwise" is gone; each clockwise millstone pays one pellet per gear
  in its shortest drive. A millstone meshing straight into the crank (zero
  gears, even) is dead and pays nothing.
- **Ends.** The game ends at the end of a round only when the last gear leaves
  the supply OR the granary_bin is emptied. The old "no gear placed" end is
  deleted, and there is no legal way for passing to end or win the game.
- **Win tiebreak retained** (final-clockwise-millstone, then shared):
  `last_grind_cw` records every seat whose millstone turned clockwise on the
  final grind; among tied-for-top stacks, those turn clockwise win, else they
  share.

## ASSUMPTIONS

None. The second rework settled the only fork the first rework declared.
`rules:turn[5]` now states outright that a binding PLACE or SHIFT is a legal
move, offered like any other, that reverts and wastes the turn; the
`bind_illegal` ASSUMPTIONS/CHOICES entry is deleted and `legal_moves` implements
only that one reading. (The old incremental `_add_binds` odd-cycle shortcut
is dead code in the file, kept for reference; `apply_move` still uses the
authoritative full `_is_bound_state` check.)

## Approximations and costs

- The physical mesh, the bind and the drive chain are all the one graph
  property; backlash, a loose gear, and a crooked knob are real and are
  deliberately out of scope for the engine.
- Payout uses the shortest mesh chain; the rules ask for exactly that
  ("SHORTEST route"), so this is faithful, not an approximation. In a game
  that is always unbound the parity is exact anyway.
- Distances and payouts are recomputed each grind (a fresh BFS), matching
  "recount every grind".
- The one thing "modelled, not plastic": the numbers that make chains bind, pay
  out and decide the tiebreak are the graph; nothing about how hard it is to
  physically crank is modelled.

## Rules the rework made unreachable, and the one stall the second rework closed

- The whole POWER family (moving the crank round to round) is unreachable by
  construction; the crank's own pin is simply never an action anymore.
- The "solo mill pays 2" case is deleted; a lone clockwise millstone now pays
  its chain length like any other.
- **The old reachable stall is closed by `rules:end[1]` A STALLED MILL (drain).**
  Under the first rework a board could reach a position where every remaining
  gear bound, no yard pin was free, and every mill was dead — so neither
  `end[0]` condition fired and the game looped on PASS to the `MAX_TURNS` cap.
  The engine now tracks `state["round_active"]` (set by any successful PLACE,
  SHIFT, or grind pay) and, at the end of any round that stays all-False,
  banks one pellet out of the granary instead of ending the game — termination
  without cutting the game off at an even score. Termination is bound, not
  hoped: a productive round drains the supply or the granary (both finite) or
  shifts a millstone (finite positions), and a fully inert round drains a
  pellet. `MAX_TURNS = 200` remains as a belt-and-suspenders cap but is no
  longer the thing that terminates the game.

## observation

`HIDDEN_INFO = False`, so pass 1 of the three-pass discipline removes nothing:
the yard, the supply pile, the granary and every score are open.

Pass 2 adds what a seated player reads off the object by eye: the full board
adjacency (`board.edges`, the 90 edges of the 37-pin lattice), which pins are
yard pins vs inner pins (`board.yard_pins` / `board.inner_pins`), and each
piece's tooth height (`mesh_height`, from the existing `_tier` helper) — all of
which the raw state omits even though the whole bind test and the payout are
written in exactly those terms.

Pass 3 names things in the rulebook's words: each seat's own `mill_pin` and
`pellets` are pulled forward under `you` (so a reader never indexes an array to
find its own things), the engine's `pellets` is exposed as
`granary_pellets_remaining`, `crank_pin` is a formatted pin id, and
`fixed_crank: true` states setup[1]'s permanence outright. The engine's internal
progress pointers are withheld — `action_order`/`action_index`/`setup_index`
are the engine's own state machine, recovered by the reader from `phase`,
`to_move`, `start_player` and `round`.

Left out deliberately (pass 3): no evaluation, no flag on which moves would
bind, no hint of a winning chain — nothing that plays the game for the reader.

Nothing that plays the game reads `observation()`; all scripted policies and the
lookahead read `state` directly to stay fast over thousands of games.
