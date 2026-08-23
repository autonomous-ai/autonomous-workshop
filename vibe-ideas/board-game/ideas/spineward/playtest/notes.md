# spineward — engine notes

## 2p decided-close rework (2026-08-19)

The gate was passing on termination but FAILing `not_a_game` on the two-player
shape: `tie:2p` 62-79% (the crown never fired under competent play, so games
collapsed to a ~0-0 backstop tie) and `runaway:2p` 100% (the few decided games
were first-come-first-served cruises — the midpoint leader always won). The
root was a flat crown of 4 with landing restricted to the six corner shelves:
a competent 2p policy could not reach a shelf to bank, so it dawdled to the
"no-landing backstop" at 0-0; and when someone did bank, first-to-4 was a
snowball with no comeback lever. Three changes fixed it, all public, thematic,
and readable off the board:

- **Whole-coast landing.** `LAND` (rules:turn) is now legal from ANY pan — the
  outgoing tide beaches a carried pearl into the rack wherever the shell
  stands. No dock pilgrimage to a corner shelf. This is what makes banking the
  norm: every player is always near enough to bank, the crown now actually
  fires, and the 0-0 backstop standoff disappears. The six corner pans remain
  the reef's historic ANCHORAGES (art/relief), not a mechanical gate.
- **THE TIDE — the catch-up.** (rules:turn) At the start of each turn, if the
  acting seat's banked total is strictly below the table's highest banked
  total, the seat takes THREE actions that turn, not the usual two. This is
  what kills the snowball: a leader acts fewer times than a chaser, so a lead
  is a thing that must be re-earned every turn, and the trailer can out-bank
  or rob the leader's carried load. `turn_quota` is fixed at the start of the
  turn (public in the observation as `actions_quota_this_turn` /
  `actions_remaining_this_turn` / `riding_the_tide_this_turn`).
- **Crown value 6** (flat, all counts). With whole-coast landing, 6 is
  bankable even on a crowded four-player reef, and it is long enough — and the
  race late enough — that THE TIDE decides the close finish instead of whoever
  banked first.

Measured: the full gate now PASSes with 0 findings (the `tie:2p` / `runaway:2p`
and `tie:4p` findings are gone; 4p termination and the landing-keyed stall
breaker are unchanged). Empirically, a banking proxy gives 2p tie 0% and
runaway ~0.66; 4p tie 0% and runaway ~0.28.

**DROP removed (2026-08-19, same rework, applies-clean).** The full gate after
the trio above flagged `dead_move:drop`: legal but never once chosen by any
seat playing to win. It was right. Once whole-coast `LAND` exists, DROP is
strictly dominated — both empty a shell socket of a carried pearl, but LAND
beaches it into your rack from any pan and advances the crown, while DROP only
re-deposits it on the board in an adjacent clear pan and advances nothing. The
pre-rework DROP role (churn that kept the "no pearl activity" slack counter
reset) is gone too, because the reworked slack breaker resets only on a LAND.
It was vestigial, so DROP is deleted from the rules, the legal moves, the
apply switch, and the observation. Probe: 1500 random games at 2p and 4p with
DROP removed, 0 stuck / 0 undefined / all finished — no state depended on it
as its only legal move.

## 4p termination rework (2026-08-19)

The playtest gate FAILed with `termination:4p` (8/20 random and 1/20 competent
games hit the 450-turn cap) and `unmeasurable` (40% of 4p/random games ended in
a rules gap). Root cause: the crown value at 3-4 players was 5 — effectively
unreachable under non-cooperative play — and the three-silent-rounds net keyed
on "no pearl taken/dropped/robbed/landed", which random churn keeps resetting
forever (take/drop/rob all look like activity), so it never fired and no game
could end on it.

Two changes, both in idea.json and mirrored here:

- **`_crown_value(n)` is now a flat 4 at every player count.** 2p is untouched
  (it was already 4), so the crown-race fix for the 2p tie is preserved; 4 is
  low enough below a four-player full haul (~7 apiece) that a contested shell
  can actually bank it, where 5 could not.
- **The slack clock now keys on LANDINGS, not on any pearl activity.**
  `landed_flag` (any LAND this round) replaces the activity-only reset; the
  trigger is `no_landing_rounds >= 4` (rules:end[1]: FOUR full rounds with no
  pearl landed). Taking/dropping/robbing are churn that no longer resets it —
  the only thing that advances a crown is a landing, so a table shuffling
  pearls without banking one is genuinely stalled and now ends. `observation`
  exposes `landed_this_round` / `rounds_without_landing` as the public read.

Because landings keep resetting the clock in an active game, the backstop only
fires on a real deadlock; a healthy table produces landings every round, so it
crowns long before four slack rounds (the crown at 4 is well below the reef
emptying).

## Crown / end-rule rework (2026-08-18)

The ideator's rework added the CROWN RACE (rules:win) and changed the quiet
trigger (rules:end[1]). The smallest changes that model it:

- **`crown_seat`** is a new state field, `None` until a LAND makes the acting
  seat's public rack total reach the crown value; then it holds that seat. The
  check runs inside the `land` branch of `apply_move`, and sets
  `crown_seat = seat` the instant the total `>= _crown_value(n)` (4 at two
  players, 5 at three or four).
- **`is_over`** short-circuits to `True` as soon as `crown_seat` is set —
  even mid-round and mid-turn, because rules:win says a crown "ends the game
  on the spot ... the round is not finished, because a crown cannot be
  shared." This is the only way the game may end without waiting for the round
  to close; all normal triggers still wait for the round finish.
- **`winners`** returns `[crown_seat]` directly when a crown is live — a crown
  is a sole win with no tiebreak chain. The old highest-total/tiebreak-chain
  comparison is untouched below that guard and is exactly the fallback for a
  game that ends with no crown.
- **`scores`** is unchanged: sum of landed grades, valid at every point, so
  the greedy/lookahead and runaway-leader measures still read it. It is both
  the crown driver and the fallback total.
- **Quiet-round count** — the old one-silent-round trigger is replaced by a
  `silent_rounds` counter (`state["silent_rounds"]`). At each round boundary,
  any pearl activity (`activity_flag`) resets it to 0; otherwise it
  increments; `end_pending` is set once it reaches 3, per rules:end[1]'s
  "THREE full rounds ... in which no pearl is taken, dropped, robbed or
  landed." Note the crown resets nothing here and is checked independently, so
  a crown lands mid-round regardless of the quiet clock.

Because a rack reaching the crown value (4 or 5) always precedes a rack filling
to six (whose total would be 6+), the "any rack holds six" end trigger is now
unreachable in practice whenever a crown is on the table — which is every game
per the new rules. It is kept as the safety-net fallback the rules describe
("a rack reached six" among the no-crown endings) rather than deleted.

`observation` needs no change: the crown value is a public rules constant and
the rack totals it keys off are already in `racks`, so whether a seat has
crowned is read off the table, exactly what pass 2 wants to hand over. The
`main_turn.end_condition_reached` / `activity_this_round` fields still describe
the non-crown triggers and the quiet clock them at three rounds.

Playtest finding, not tuned: at four players random play stalls — roughly 40%
of random 4p games in the quick run reach the 450-turn cap without any end
trigger or crown firing, because random players neither gravitate to shelves to
land toward the crown nor trigger the (now lenient, three-round) quiet stop. No
game ever deadlocked (`stuck` was 0 in every batch). That stall is the game's
own economy under dice, not an engine defect, so nothing was adjusted for it;
the full gate measures precisely.

## Undefined

None raised. Every branch legal_moves() can reach has an explicit
precondition in idea.json, and `TURN` (rules:turn[4]) has no precondition at
all, so a seat is never left with zero legal moves — a deadlock proof that
also matches what `--quick` reported (0 stuck games in every batch).

## Assumptions

None — `ASSUMPTIONS`/`CHOICES` are empty.

**Formerly `rob_needs_target_pearls`** (rules:turn[8]): the "the target carries
no pearl" fork is now settled by the rules themselves. idea.json's ROB entry
states explicitly, "If the enemy is carrying no pearl, ROB simply is not
offered as a move." The engine wires exactly that reading directly (both in
`legal_moves` and in `observation`'s `your_reach`), and the assumption entry
has been removed from `ASSUMPTIONS`/`CHOICES` since nothing about it is
genuinely undecided anymore.

## Approximations / modeling choices

- **Sockets are stored indexed by the direction they currently point at**,
  not by a fixed physical socket id. Nothing in the rules ever distinguishes
  one physical socket from another, and this makes `TURN` a plain cyclic
  rotation of the list and `CREEP` a pure translation that leaves it
  untouched — exactly "keeps its facing" (rules:turn[5]).
- **Setup's pearl-seeding is played, not randomized away.** "Going clockwise
  from any player, each in turn ... stands it ... in any empty seed pan"
  (rules:setup[3]) is a real, visible (if grade-blind) placement decision, so
  it is a `setup_seed` move in the same legal_moves()/apply_move() loop as
  everything else, not something new_game() resolves for the players. The
  starting seat for that rotation is fixed at seat 0 — the rules say "any
  player," so this is a concretization of an explicitly free choice, not a
  guess, and it carries no more asymmetry than "choose a first player any way
  you like" already does for the rest of the game.
- **`LAND` (rules:turn[9]) is modeled as choosing any non-empty subset of
  currently-held pearls, up to the empty rack wells, landed in one action** —
  "you may land as many as you like" reads as a bulk choice within a single
  action, not one pearl per action. This is a faithful reading but it means a
  shelf-standing turn with many pearls aboard can offer up to 2^6-1 = 63
  `land` variants; bounded and small, but it is the single largest
  contributor to branching factor in the ladder/MC runs.
- **`scores()` is exactly the literal win-condition value at every point in
  time**: the sum of landed pearl grades, nothing else. Pearls still riding
  in a shell's sockets score zero until landed, per rules:turn[10]
  ("Pearls still sitting in your sockets are worth nothing at all"), so this
  is not a proxy, it is the rule. One consequence worth flagging: the greedy
  (1-ply) policy gets essentially no signal from `take`/`rob` themselves —
  only `land` moves change the score — so greedy's apparent strength in the
  ladder is really measuring willingness to reach a shelf, not cargo
  management. That is a property of the game's own economy, not something to
  correct for.

## Cross-check against review_rules.md

Read after writing the engine, as instructed, to compare independent
conclusions rather than to model its findings.

- **Finding 1 (six-pearl paralysis is unreachable)** — confirmed
  independently and for the same reason: `TAKE` and `ROB` both need a spine
  in one direction to reach with, and a *separate* empty direction to receive
  the pearl into. Once five sockets hold pearls and the sixth holds the only
  remaining spine, there is no direction left that is both empty and not the
  reach-spine, so `legal_moves` never offers a sixth `take`/`rob`. I did not
  special-case this; it falls straight out of the same precondition idea.json
  states for those two actions. It does mean the state described in
  rules:turn[10] ("an urchin with six pearls...") is never actually reached
  by play, which is the review's point, not mine to fix here.
- **Finding 2 (spine supply never binds)** — the engine models the true
  24-spine common pool (rules:setup[4], rules:turn[2]) with no adjustment;
  whether it ever actually runs dry under real playouts is exactly what the
  numbers in `playtest.json` will show, and is not something to correct in
  the model.
- **Finding 3 (spoiler check, clean)** — no special mechanic needed or added;
  the tie-break chain (win.text) and ROB/DROP as written already produce
  whatever spoiler dynamics the numbers show.

No disagreement between the engine and review_rules.md was found on any of
the three points.

## `observation(state, seat)` — three passes

Rewritten (`8021b22` audit finding: "Spineward's observation forwards
setup_place_turn, arm_turn, arm_count, actions_taken, end_pending and
activity_flag, which are its state machine, not its rules"). Scope of this
pass was `observation` only — `rules`, `legal_moves`, `apply_move`, `scores`,
`determinize` and `CHOICES` are untouched, and `playtest.py --quick` before
and after the change produced byte-identical output for the same seeds
(confirmed by diffing a run against a stash of the prior file), which is how
I know nothing outside the hook moved.

**Pass 1 — what no seat may see.** Unchanged in substance from before this
patch: `pearl_grades` is replaced by `grades`, a dict holding an entry only
for `state["revealed"]` pearl ids — every other id that appears on a pan, in
a socket or in a rack has no entry, on purpose, so a lookup for an unrevealed
id fails loudly rather than returning a value no real player has. `seed_queue`
is replaced by `seed_pearls_remaining_to_place`, a bare count — the draw
order is a blind shake at the table, and showing the list even grade-stripped
would leak which specific pearl is drawn next. `pearl_location` and
`revealed` are dropped outright, being fully reconstructable from
`pans`/`urchins`/`racks`. Every seat's hidden layer is identical (nobody,
including a pearl's own carrier, learns its grade before landing —
`determinize`'s docstring relies on the same fact), so `observation` ignores
`seat` for everything except which urchin `your_reach` is computed for; there
is no private per-seat holding to add back in.
`observation_leaks()` was run by hand across 2/3/4-player games and found
nothing (see the run log; this is the only automated check that touches pass
1 or 2 at all).

**Pass 2 — what is derivable from what the seat may see, newly added.**
CREEP, TAKE, DROP and ROB are all written in rules:turn as "a neighbouring
pan you have a spine pointing at," and nothing in the old observation said
which pan neighboured which — the same gap `8021b22` closed for Millbind's
lattice. Fixed with:

- `pans[pan_id]["neighbors"]`: every pan's own six neighbours, one per
  direction index (the same 0-5 a move's `d`/`e` argument uses), `null` past
  the edge of the reef. Pan ids are `str(coord)`, matching the tuple spelling
  that already appears inside a raw `("setup_seed", coord)` move, so no
  translation between two spellings is needed.
- `urchins[i]["sockets"]`: each of the six sockets as `{direction, faces_pan,
  holds}` — `holds` is `"spine"`, `{"pearl": id}` or `null`. This replaces
  the raw `dir` list a seat had to decode against an encoding it never saw,
  for the *reef*'s title fact ("Six sockets is your entire budget for
  movement, reach, defence and cargo together," rules:turn[0]) — not just for
  `seat`'s own urchin but for every urchin, since every shell is a visible
  physical object on the board.
- `your_reach` (computed only for the requesting `seat`'s own urchin, only
  once it exists — `null` during `seed`/`place_shell`/before arming): which
  clear neighbouring pans it could `creep` or `drop` into, which neighbouring
  pans holding a pearl it could `take` from, which neighbouring enemy urchins
  it could `rob` (spine out, no spine back, an empty socket to catch with,
  and the enemy must actually be carrying a pearl — the same test
  `legal_moves` uses, so this list never promises a `rob` that legal_moves
  does not also offer),
  and `on_landing_shelf`. Verified by hand against `legal_moves()` output at
  several sampled positions (rob, take and drop cases all cross-checked; see
  the exploratory run at the bottom of this section's git history if it's
  ever needed again). None of this is "is it a good idea" — GROW/SHED/TURN/
  LAND all stay unstated here because their own preconditions (an empty or
  full socket, standing on a shelf, an empty rack well) are already a single
  glance at `sockets`/`on_landing_shelf`/`racks`, not a second pan away.

One bug caught while verifying this against `legal_moves`: `faces_pan` in
`_socket_view` originally computed a neighbour coordinate without checking
board membership, so an edge urchin's socket pointing off the reef reported
a phantom pan id absent from `pans`. Fixed to use the same `pan in state["pans"]`
test `pans[...]["neighbors"]` already uses, so a socket never faces an id the
`pans` map doesn't also carry.

**Pass 3 — the rulebook's words, not the state machine.** `phase` is now one
of four short English phrases ("setup: seeding pearls", "setup: placing
shells", "setup: arming spines", "main turns") rather than the raw
`"seed"`/`"place_shell"`/`"arm"`/`"main"` tags `apply_move` branches on.
`to_move` (= `player_to_move(state)`) replaces four redundant, phase-specific
turn pointers — `seed_turn`, `setup_place_turn`, `arm_turn`, `current_seat` —
with the one fact any of them ever meant. `arm_count` is dropped with no
replacement, not renamed: a seat already sees exactly how many spines the
arming urchin has standing by counting `"spine"` entries in that urchin's own
`sockets`, so restating the count under a new name would be a lookup wearing
a costume, not new information. `actions_taken`, `activity_flag` and
`end_pending` are kept — renamed to `actions_taken_this_turn` /
`actions_remaining_this_turn`, `activity_this_round` and
`end_condition_reached`, nested under `main_turn` (present only in the main
phase) — because none of the three is recoverable from a single glance at the
pans: they track rules:turn[1]'s two-actions-per-turn budget,
rules:end[1]'s "no pearl taken, dropped, robbed or landed in a full round"
and rules:end[0]'s end trigger respectively, so they are genuine rules
bookkeeping, not implementation state, and are kept under names that say what
they track. `turn_number` is dropped without replacement: it never appears
in the rulebook's own vocabulary (the rules track "a full round," which
`end_condition_reached`/`activity_this_round` already cover), and it is
fully reconstructable by counting `PLAYED` lines in a table transcript, so
carrying it would be restating the transcript rather than adding a fact.

Kept as-is, because they are already public in the physical game: `racks`
(pearl ids landed per seat — landing is the one moment a grade becomes
public, and `grades` carries that value for every id that appears here),
`spine_supply` (renamed `spine_supply_remaining` for clarity), `players`
(renamed from `n`). Pearl ids are kept everywhere they appear (pans, sockets,
racks, `your_reach`) as an opaque handle so a seat can track "this is the
same physical pearl I saw two turns ago" without learning its value — safe
rather than a leak, since the id-to-grade mapping is reshuffled fresh by
`rng` every `new_game`, so an id alone carries no grade information, in this
game or across games, until it shows up in `grades`.
