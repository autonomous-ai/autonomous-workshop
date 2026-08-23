# deep-claim — playtest engine notes

## Undefined left in the engine

None. Reading `rules.turn` end to end, every position the engine can reach
has an explicit next step:

- A large puck is legal exactly when the target bore's shelf is empty
  (`rules:turn[2]`); placing it always seals that bore, whether or not the
  floor underneath was already claimed (explicit in the same rule — see the
  assumption below for what "permanently unreachable" means for a floor
  claimed before the seal).
- A small puck is legal exactly when the target bore's floor is empty *and*
  its shelf is still unplugged (`rules:turn[3]`).
- If neither is possible anywhere, the player passes (`rules:turn[4]`). This
  is the only pass condition given, so placement is treated as mandatory
  whenever any placement is legal.
- The game ends the instant every shelf is sealed, or the instant a full
  round (every seat, in turn) passes with nothing to place (`rules:end[1]`),
  whichever comes first. Because a bore's shelf can only ever be sealed once
  and there are exactly six bores, "every shelf sealed" is reached after at
  most six large placements total, by anyone; the engine tracks a
  `consecutive_passes` counter that resets on any placement and ends the
  game once it reaches `n_players`, which is a direct transcription of
  "every player in a row passes".

No position was found where the rules are silent about what happens next,
so there is nothing to raise `Undefined` for.

## Assumptions declared

**`floor_burial`, `rules:turn[2]`.** "That bore's floor chamber becomes
permanently unreachable for the rest of the game, whether or not it was
already claimed" says what happens to *placement* into the floor once the
shelf above it seals, but not what happens to a floor claim that was already
sitting there. `rules:win` scores "every shelf and floor chamber marked with
their own studs" with no exception carved out for a since-sealed floor, which
reads most naturally as the floor claim standing on its own. That is the
`chosen` reading: the floor keeps scoring for whoever set it; sealing the
shelf only closes the bore to further placement. The `alternative` — that
sealing the shelf buries the floor claim itself, so it stops scoring for
anyone — is equally consistent with "permanently unreachable" read literally
(the floor becomes unreachable *as a scored claim*, not just as a place to
put a puck), and it changes what a large puck is: a 1-point self-claim under
`chosen`, versus a 1-point self-claim plus a 2-point denial strike against
whichever rival holds that floor under `alternative`. Both readings let play
continue, so it is wired rather than picked: `apply_move` sets a per-bore
`floor_buried` flag when a large puck seals a shelf over an already-claimed
floor and `CHOICES["floor_burial"] == "alternative"`, and `scores` skips a
buried floor's points. Under `chosen`, `floor_buried` is never set and
scoring is unchanged from before this flag existed.

This is the one that matters: a full-gate run under the `chosen` reading
found 100% of games ending in a tie with seat 0 in the winning set every
time, at both 2 and 4 players — a result that rests entirely on shelf and
floor points being independent and therefore summing the same way regardless
of who denies what. The `alternative` reading breaks that independence on
purpose (a large puck can actively cancel a rival's points, not just claim
its own), so it is exactly the kind of flip `run_sensitivity` exists to
catch, and the rules need to settle which one is meant rather than have this
engine guess.

I drafted a second candidate assumption — whether a player may voluntarily
pass with a legal placement on the table, reading the concept text's "worth
spending ... or worth banking now for the guaranteed point" as possibly
describing a hold-back option — and discarded it after re-reading: that
sentence describes a choice of *which bore* to spend a puck on (deny a
rival's future floor claim vs. bank the guaranteed point elsewhere), not
whether to spend one at all. `rules:turn[1]` frames choosing a puck and a
bore as what a turn is, and `rules:turn[4]` gives exactly one pass condition.
A first-run engine with that branch wired in showed the flip never changed
the greedy sensitivity policy's play, because placing a puck never lowers a
player's own score (every placement is worth +1 or +2, unconditionally), so
a one-ply-greedy player never has a reason to hold one back — an honest
"unwired" result rather than a genuine ambiguity, and not worth carrying as
noise.

## Approximations and their cost

`scores()` is exact and valid at every point in the game (sum of owned,
non-buried shelf and floor points), not a proxy, so there is no
approximation cost to record there under either reading of `floor_burial`.

One modeling choice, not a rules gap: "Confirm all six bores... Agree who
goes first" (`rules:setup[3]`) explicitly leaves first-player choice to the
table and gives no rule for it. The engine fixes seat 0 as first player
every game. This is deliberate, not a guess about the rules — the rules say
the table decides, so there is no "true" answer to model — and it means the
seat-bias measurement the harness runs is reading exactly the dynamic the
owner named when killing this idea ("an optimal strategy for the first
player to always win"): whatever advantage or disadvantage attaches to
moving first shows up as seat 0's edge across thousands of games, unclouded
by any compensating rule the engine might otherwise have had to invent.

## Things that turned out to be structurally rare or unreachable

`MOVE_KINDS` includes `"pass"` because `rules:turn[4]` defines it, but
whether it is ever actually legal is data, not an assumption. The board has
exactly 6 bores, so the game can never need more than 6 large-puck
placements (one per bore) to reach the "every shelf sealed" ending, and the
6 floors similarly cap useful small-puck placements at 6. At 2 players, the
starting supply (3 large + 3 small each) is an exact match for that cap: 6
large pucks for 6 shelves, 6 small pucks for 6 floors, with no surplus. At 3
or 4 players, the combined supply of a given puck type overshoots what the
board can ever absorb (9 or 12 large pucks chasing 6 shelves, 9 or 12 small
chasing 6 floors), so the game is quite likely to end via "every shelf
sealed" before any individual seat exhausts both of their own puck types on
their own turn — which is the only way `pass` becomes legal. This is a
property of the piece counts against the six-bore board, not an engine
simplification, and it is exactly the kind of finding this stage exists to
surface: a declared action that the rules define but the arithmetic of the
components may make nearly impossible to ever need.
