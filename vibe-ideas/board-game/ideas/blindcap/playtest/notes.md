# blindcap — engine notes

## Undefined

None left in. Every branch the turn structure can reach — mandatory plant
while stools remain, the single free action (probe/crown/pass), pin-heap
exhaustion, crown exhaustion, the closing round, harvest scoring, and the
full tie-break chain — is addressed by `idea.json`'s rules text, so
`legal_moves`/`apply_move` never had to guess. `winners()` always resolves to
exactly one seat: the two tie-breaks (`rules:win`) chain to seat index, which
is always distinct, so there is no unresolved tie left over.

## Assumptions

One declared and wired:

- **`contested_grove_per_crown`** (`rules:win`). The win rule is explicit that
  an uncontested grove pays its owner `n^2` *once*, "even if two of their own
  crowns sit in the same grove, which is a wasted crown" — but for a
  contested grove it only says "each of those players scores only n for it,"
  without repeating that once-per-player caveat. A player who has landed two
  of their own crowns in a grove that a rival has also crowned is exactly the
  case that sentence never revisits. Chosen: once per player regardless of
  crown count (reads the contested sentence by analogy with the explicit
  uncontested one, and "each of those players" names players, not crowns).
  Alternative: once per crown, so stacking crowns pays repeatedly even in a
  contested grove. I hand-verified the flip changes `scores()` (a constructed
  2-crowns-same-owner contested grove scores 3+3 under `chosen` and 6+3 under
  `alternative`), so it is genuinely wired. Under `--quick`'s small sample
  (40 games, greedy self-play) `run_sensitivity` reported it `cosmetic`
  (worst delta 6%) rather than `unwired` — the scenario (a player choosing to
  double-crown into ground already claimed by a rival) is rare but not never;
  the full gate's larger sample should be trusted over this one, not the
  other way around.

## Approximations

- **`scores()` always uses true species**, whether or not a stool has been
  probed. This is not a heuristic shortcut: `rules:end[1]`/`rules:end[2]`
  make every stool's species visible at harvest regardless of what was
  probed during play ("Lift every stool out... lay it on its side... so its
  grooves are readable"), and no stool ever moves after planting
  (`rules:end[1]`), so applying the payout formula to the current board is
  the literal end-of-game computation at any point, not a proxy for it. One
  side effect worth flagging: `pol_greedy`'s one-ply margin reads this same
  `scores()` directly, without going through `determinize()` — only
  `pol_mc` (the lookahead rung) calls `determinize` per the harness contract.
  So greedy's evaluation of "how good is my move" is quietly better-informed
  than a real player's judgement would be, since it can weigh unprobed
  groves it has no in-fiction way to know about. This is inherent to how the
  harness scores non-MC policies (`scores()` must be "valid mid-game" and is
  read straight off whatever state object it is given) and is not something
  `engine.py` can fix without breaking the `scores()` contract; flagging it
  here so a large gap between greedy and lookahead performance is read with
  that in mind, rather than as a game-balance finding.
- **Board tile layout.** `rules:setup[0]` names the aggregate shape and
  socket count per player count (2p: 6x3/18, 3p: an L of 27, 4p: 6x6/36) but
  not which corner of the 3-tile L is missing, or which orientation the
  four 4p tiles sit in relative to each other. I picked one arrangement
  (`TILE_LAYOUTS` in `engine.py`) that produces the right shape and socket
  count and the right adjacency rule (shared grid edges, including across
  tile joins). Since no seat owns a fixed tile — any player may plant in any
  empty socket anywhere on the field — the specific orientation chosen has
  no bearing on anything the harness measures; this is implementing what the
  rules describe, not resolving an ambiguity that could change the numbers.
- **Owner marks** (cap-brim bite counts, matching crown pierced-hole counts)
  are collapsed to a bare seat index. They are described as two physically
  redundant encodings of the same one fact ("which player planted/claimed
  this"), so nothing is lost modeling that fact as `owner: seat` rather than
  as two matching physical codes.

## Caught during writing, not a rules gap

An early draft tracked "plant, then one free action" as a single per-round
flag rather than resetting per player's own turn, so only the first seat to
act in each round ever got to plant and the rest skipped straight to
probe/crown/pass — games still terminated cleanly (`is_over` only checks the
round counter) so this would not have shown up as a crash, only as a game
that silently starved three of every four players of half their stools.
Caught by hand-tracing a game before running `playtest.py`; fixed by
recomputing `subphase` on every `_advance_turn`, not only on round rollover.
Verified afterward that a full 4p game now runs exactly 52 `apply_move`
calls (`13 * 4`: 6 rounds x (plant + action) + 1 closing-round action, times
4 players), which is the number the rules structure guarantees regardless of
which moves are chosen.

## Agreement with `review_rules.md`

No disagreement found. The review's own arithmetic on the action economy —
7 free-action opportunities per player (6 rounds + 1 closing round), of
which at most 4 can be probes at 4p if all 3 crowns are placed, giving
`4 x 4 = 16` against the fixed 16-pin supply — matches the engine's turn
structure (`MAIN_ROUNDS = 6`, `TOTAL_ROUNDS = 7`) exactly. Its reading of the
tie-break ("favours the later seat") is what `winners()` implements
literally (`max(tied2)` among seats still tied after the uncontested-grove
comparison).

Two watch items the review deferred to playtest — **PASS close to dominated
at 2p** and **last-seat advantage compounding the tie-break** — are exactly
what the `dead_move` and `seat` checks in `playtest.py`'s full run are built
to catch; `--quick`'s tiny sample is not the right instrument for either
(8-20 games per cell), so this run neither confirms nor refutes them, and I
did not adjust the engine to push the numbers either way in response to the
review's expectations.

## `observation(state, seat)` — patch, no other behaviour changed

Added the second hidden-information hook the contract now requires alongside
`determinize`. `legal_moves`, `apply_move`, `scores`, and the
`contested_grove_per_crown` assumption are untouched.

Fields removed or replaced per socket, and why:

- **`species`** — removed (set to `None`) unless the socket is `seat`'s own
  (`owner == seat`, which `seat` planted and always knows), or both
  `probed_upper` and `probed_lower` are `True`. The four species have
  pairwise-distinct `(upper, lower)` groove patterns (`SPECIES_GROOVES`), so
  once both holes of a socket have been probed its species is already public
  — derivable by anyone from the two revealed results — and carrying it
  through is equivalent information, not an extra leak. Any socket probed on
  only one band, or not at all, and not owned by `seat`, has its species
  removed: that is exactly the one-band candidate-narrowing (two of four, or
  four common vs. two scarce) the rules describe, not a name.
- **`revealed_upper` / `revealed_lower`** — added. These are the actual
  sunk/proud *results* of any hole that has been probed (`True` = sunk,
  `False` = proud, `None` = not probed), computed from the true species via
  `SPECIES_GROOVES` and kept regardless of ownership, because a pin's
  position is physically visible to the whole table once it is placed. The
  raw `probed_upper` / `probed_lower` booleans (whether a hole has been
  probed at all — also public, visible as an empty vs. occupied hole) are
  kept unchanged.
- **`owner`, `crown`** — unchanged. Both are public the instant they are set
  (a brim's owner bites, a crown sitting on a boss).

Fields removed or replaced per player, and why:

- **`troughs[p]` for `p != seat`** — replaced with `len(troughs[p])`, an
  integer count, instead of the list of remaining species. The composition
  of every player's supply is fixed and public
  (`rules:setup[1]`: "This composition is the same for everybody and is
  public knowledge for the whole game"); only which of those six stools a
  given player has *not yet planted* is private, which is exactly the same
  fact `determinize` already resamples for the lookahead policy. `seat`'s own
  trough is left as the full list, since it is `seat`'s own hand.
- **`crowns_remaining`, `pins_remaining`, `round`, `seat_ptr`, `subphase`,
  `n`** — unchanged for every seat: all are counts or turn-structure facts
  visible to the whole table (crowns and pins are physically counted piles,
  the round/turn order is who is sitting where).

Verified by hand (not by the checked-in test) that `observation(state, 0)`
after ten random moves in a 3-player game round-trips through `json.dumps`
and never exposes another player's socket species unless that socket had
both holes probed.

One terminology note, not a disagreement: the review counts "turns" as one
per player-round (7 per player, `14`/`21`/`28` for 2p/3p/4p), bundling PLANT
and the free action together. The engine instead reports each as a separate
`apply_move` (13 per player: `6 x 2 + 1`), because planting a stool and then
probing or crowning are two distinct decisions and hand movements at the
table, which is the granularity `playtest.py`'s `SECONDS_PER_DECISION` is
defined against. This also means the harness's length check has no way to
add the review's separately-estimated 3-5 minute fixed harvest/lay-out
overhead (it is not a decision, so it is not in the turn count); the
`length` finding, if the full gate raises one, should be read as a lower
bound on real playtime, not the whole of it.
