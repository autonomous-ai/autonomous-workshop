# armillary playtest engine — notes

The engine models the reworked design verbatim: the inverted aperture (you read
only the sky the predecessor set), TURN THE SKY at the END of the turn aiming
at the successor, the 1->3 / 2->2 / 3->1 reach exchange, the fixed 24-socket
dawn_peg clock, and the deleted zenith-well / CLEAR / freebie-ordering penalty
are all gone. `rules_check.json` passes, and the engine mirrors its steps.

`--quick` runs 20 finished games at 2p and 4p with no undefined, no deadlock,
no termination failures and 0% forced turns. The verdict it reaches is a
`measurement` note that some 4p ladder rungs finished fewer than 20 games (a
data-collection depth check, reported and then ignored by the depth check),
not a rules verdict. The former `rules_ambiguous` on `rules:turn[5]` is gone:
the ideator has settled that clause, so the engine wires one reading and
declares no assumption (see below).

## Undefined

None. The engine never reached a position the prose does not cover. The one
genuine read-two-ways clause no longer exists.

## Assumptions

None. `rules:turn[5]` was previously ambiguous on whether a knob-up tile in an
open well ends reaching. It is now settled in idea.json: "a knob-up tile in an
open well counts as a tile you can take, because you may always PULL it rather
than TAKE it: your reaching never forces you to stop while any open well is
non-empty." The engine wires that inclusive reading unconditionally in
`_reaching_forced_done` — reaching ends (forced BANK) only when every open well
is empty; a face-down tile in an open well does not end reaching. The old
`no_takeable_ends` entry has been removed from `ASSUMPTIONS`, and `CHOICES` is
now empty, because the rules text settles it rather than the engine choosing.

## Approximations

- **Running score is the banked score.** `scores()` applies the exact
  end-of-game formula (2 per star + 1 per moon + 3 x shortest constellation
  slot) to what is already standing in the rails. Catch tiles are omitted
  because they are at risk and worth nothing if dawn comes before banking
  (end[1]); this is the same computation the win uses, so it is a faithful
  running proxy, not a separate heuristic. The greedy policy therefore cannot
  be taught that a face-up catch is "almost safe", which understates one-ply
  shortsightedness but is the honest reading of the rules.
- **Bowl count is public but faces are not.** A seat can derive the count by
  tracking every refill from the known 38, so the count is carried; each
  individual tile's identity is removed.
- **Disc rotations** are represented as one integer per disc (grooves mod 10)
  and a well counts as open when all three masks show a window over it. The
  sign convention of "which direction is +1" is arbitrary and symmetric (the
  player chooses signed deltas over a circular track), so it changes nothing.
- **The dawn clock** is modeled as `turn_count` advancing by one at the end of
  every player-turn, with the game over at 24. Setup stands the peg in the
  first socket; 24 advances moves it past the 24th, matching end[0]. 24/n is
  integral for 2, 3 and 4 players, so every seat takes equal turns.
- **A busted turn's rotation is forced to one groove** in either direction on
  any one disc, and the peg goes to 3, per turn[4]/turn[7].

## Unreachable rules

- None of the three compulsory steps (BANK, REFILL, ADVANCE THE DAWN) is a
  decision-kind; they carry no choice and are applied automatically. They are
  therefore deliberately absent from `MOVE_KINDS`, which lists only the player
  decisions: `pull`, `take`, `stop`, `rotate`. Declaring the compulsory steps
  as move kinds would have reported them as dead moves (never legal), which
  would misrepresent them.
- `stop` may turn out to be rarely or never chosen by a competent policy
  (greedy keeps pulling while a reach remains). It is a genuine action the
  rules grant, so it is declared even if the harness flags it as dead.

## observation — what this seat sees / what is withheld

Presented (all public or derivable by eye, in the rulebook's words): which
wells are open (read off the three mask rotations), every well's collar
constellation, which wells are empty, every face-up tile's identity, each
seat's reach_peg, each seat's banked rail split by constellation, the
night_bowl tile count, the eclipse-bay void count, the dawn socket and turns
until dawn, whose turn it is and what action is owed, the current face-up
catch, and the well-to-constellation mapping.

Withheld (what a seat may not see, pass 1): the face under any knob-up tile in
a well, and every face in the night_bowl. Those are the entire hidden-information
layer, and the only fields removed. A face-up well tile's species is carried,
because it is on public display; a seat's constellation mapping and the open
wells are derived and included, because anyone at the table gets them by
looking and hiding them would only tax the reader. The engine's internal
progress counters are dropped: `phase`/`turn_count` become the rulebook's
"whose turn / reaching or turn-the-sky / turns until dawn".
