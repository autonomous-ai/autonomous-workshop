# review_playtest — deep-claim

Verdict: FAIL Across 21 recorded sessions and four independent tables, `place_small` strictly dominates `place_large` on any open bore, so the game is a fixed partition of 18 points handed out by turn order, and every player at every table said so unprompted.

Disposition: rework — `rules:turn[2]` and `rules:win` must settle whether sealing a shelf cancels the floor claim under it (the one sentence that would make a large puck interact with another player's score at all); `rules:setup[2]` and the `disc_large_*`/`disc_small_*` quantities must stop making 2-player supply an exact partition of the board's 12 scoring slots; `rules:setup[3]` must stop leaving seat order as the only thing that decides a 4-player game; `rules:win` must say what a game that ends level 18 times in 21 is; `rules:turn[4]`'s pass must become reachable or go; and `playtime_min` must match a game that is 12 placements long.

This is a rework and not a kill by a narrow margin, and the margin is one
sentence. See "Why this is not a kill yet" at the end. If the ideator's answer
to the `rules:turn[2]` ambiguity is the reading the engine happened to pick,
there is nothing left in this idea and it should come back as a kill rather
than as a second rework.

## What was run

Machine half: `playtest.json`, 300 games at each of {2, 4} players against
each of {random, greedy} plus a 4-rung 60-game ladder, `elapsed_s 1.3`,
`hit_deadline false`, `leaks: []`. Verdict `not_a_game`, 8 findings
(4 `rough_edges`, 3 `not_a_game`, 1 `rules_ambiguous`).

Table half, four separate sittings, 21 sessions, 250 recorded decisions:

| run | sessions | driver | model | tools | summary file |
|---|---|---|---|---|---|
| `g` | g1..g5 | Claude Code subagents over `SendMessage` | Claude | breaker had `Read` | none (its prose report is what this file replaces) |
| `mm` | mm1..mm5 | `table_run.py` | `minimax/minimax-m3` | none | overwritten, gone |
| `a` | a1..a5 | `table_run.py`, anthropic wire | `minimax/minimax-m3` | none | `run_anthropic_cached.json` |
| `o` | o1..o5 | `table_run.py`, openai wire | `minimax/minimax-m3` | none | `run_openai_cached.json` |
| smoke | smoke1 | `table_run.py`, chat wire, different brief | `minimax/minimax-m3` | none | `run_chat_openai_cached.json` |

Integrity, checked per session rather than taken from the summaries:
`leaks: []` in every run file; `handed_over_at: null` and `"by": "player"` on
all 250 moves in all 21 sessions, so no scripted seat finished any game
despite `finish_with: greedy` being set.

Two things about the runs a reader must not skip.

**`seed_blind: true` is recorded but meaningless here, and the seeds are
decoration.** `engine.new_game` takes `rng` and never touches it. There is no
randomness anywhere in this game. The `a` and `o` runs used the same five
seeds (24, 37, 50, 63, 76); the `mm` run used the same five again; the `g` run
used a different five (11, 23, 37, 51, 67). All of them dealt the identical
opening position. Three 4-player sessions inside one run are not three
positions, they are one position played three times, and the debriefs say so
directly. Where I count 12 four-player games below, that is 12 plays of one
position by four tables, which is the right way to read it: the repetition is
across tables and models, not across boards.

**The `g` run's breaker read `playtest.json` before its first move.** It
played all five `g` games and gave both debriefs knowing the harness's
seat-bias and sensitivity findings. Nothing in the `g` run's conclusions about
seat order counts as independent. The `mm`, `a` and `o` runs had no tools at
all and reached the same conclusions without them, so where I cite seat order
I cite those. The `g` run is used below only for the things it measured that
the later runs did not.

**The `mm` run has no surviving debriefs.** `run_anthropic_cached.json` was
overwritten by the `a` run and `run_openai_cached.json` by the `o` run, so
`mm1..mm5` survive only as move logs. They are counted in the scoreline table
and nowhere else.

## The scoreline, and the three games that broke it

Replaying all 21 sessions through `engine.py` under the shipped
`CHOICES["floor_burial"] = "chosen"`:

| | sessions | outcome |
|---|---|---|
| 4 players | 10 of 12 | `5/5/4/4`, winners `[0, 1]` |
| 4 players | a1 | `4/5/4/3`, winners `[1]` |
| 4 players | o3 | `5/5/5/3`, winners `[0, 1, 2]` |
| 2 players | 7 of 9 | `9/9`, winners `[0, 1]` |
| 2 players | a5 | `7/9`, winners `[1]` |
| 2 players | smoke1 | `9/7`, winners `[0]` |

Seat 1 is in the winning set of all 12 four-player sessions. Seat 0 is in 11
of 12. Seat 2 is in one, and seat 3 is in none, across four different tables,
two different model families and two wire formats. Eighteen of the 21
sessions ended in a shared win.

**The three deviations are the same deviation, and it is a blunder every
time.** I went into the sessions expecting to find a player who had found a
line. What is there instead is three players trying the exact move the
`concept` field advertises ("whether your last broad puck is worth spending
to deny a rival's future floor claim"), losing by it, and saying so:

- **a1**, seat 0, turn 4: `place_large 4` onto a bore whose floor nobody had
  claimed. It is the only large puck in 250 recorded decisions ever placed
  over an open floor. It cost seat 0 the shared win (4 instead of 5) and cost
  the game two points that no one scored, which is why a1 is the only
  4-player session that ended in 11 decisions instead of 12. Its own debrief:
  *"Turn 4 — I sealed bore 4 thinking I'd denied a floor, but seat 1 just took
  the last floor on bore 5 next turn. I should have small'd 5 myself."*
- **a5**, seat 0, turn 0: opened `place_large`, as a declared experiment.
  *"Last game was a forced tie at 2p. This turn I want to TEST whether
  deviating from the script breaks the mirror."* It lost 7-9. Debrief: *"at
  2p, large-first is fatal ... New move I now play every time: at 2p, NEVER
  open with large."*
- **o3**, seat 3, turn 3: `place_large 0` over seat 0's already-claimed floor.
  Finished last on 3. Its own debrief: *"I tried the large-on-bore-0 deviation
  and the result was worse for me, so no new move I would replay."* Seat 0
  the same game: *"Deviation punished."*

So the correct claim is the stronger and worse one: **the equilibrium is
fixed and every deviation from it is a self-punishing error.** The result is
not merely fixed by arithmetic, it is fixed by a dominance relation that the
players find in one game and cannot escape in five. Note also that seat 3 in
o3 recorded an empty `why` on all three of its moves, the only seat in the
run to do so, so o3 is the thinnest of the three deviations and should not be
read as a considered line.

The mechanism is in the rules and is short. `rules:turn[2]` gives a large
puck 1 point; `rules:turn[3]` gives a small puck 2; under the reading the
engine took, no placement can ever lower anybody else's score. So on any bore
with an open floor, small strictly dominates large, and no player ever has a
reason to hold a puck back. The `o1` seat 2 debrief states it as a defect
without being asked: *"smalls are strictly dominant over larges on empty
bores, so large pucks only ever seal, never contest — kills the tension."*

## Rules questions

`rules_questions: []` in both `run_anthropic_cached.json` and
`run_openai_cached.json`. Zero questions in 119 decisions across the `a` and
`o` runs. The `g` run's four players emitted zero as well, and two said so
explicitly (*"Nothing in the rules was ambiguous enough to raise a RULES
QUESTION"*). That matches `playtest/notes.md`, which declares **no
`Undefined`** and exactly one assumption. The rules text is not what is wrong
with this game, and it is worth saying plainly rather than hunting for a gap.

Three qualifications on that zero.

**One question was asked and the harness did not catch it.** `o1` seat 0 ended
its debrief with a literal `RULES QUESTION` line, in the debrief body rather
than in the move loop, so `rules_questions` stayed empty:

> "RULES QUESTION rules:turn[1] - is sealing a shelf on a bore whose floor you
> already own ever strategically interesting, or always strictly worse than
> sealing an opponent's claimed floor?"

It cites `rules:turn[1]` but quotes `rules:turn[2]`; the id the ideator wants
is `rules:turn[2]`. Two other seats raised the same thing (`o2` seat 0:
*"sealing one's OWN floor (seat 2 did this twice) - is this ever useful?
rules:turn[1] allows it, seems pointless"*; `o4` seat 0: *"Either the rule
should force sealing opponent's floor when possible, or scoring should
differ"*). This is a want, not a gap, but it is the same sentence as the real
finding below.

**The new finding: three seats played the declared ambiguity the other way
round and nobody noticed.** `notes.md` declares `floor_burial` at
`rules:turn[2]` and picks the reading where a sealed shelf leaves the floor
claim scoring for its owner. At the table, players reasoned and moved as if
the *alternative* reading were in force, and were silently scored under the
chosen one:

> "Plan: grab a floor on turn 4, then use my last large to take a shelf and
> **bury a rival floor**." — `a1` seat 3

> "Real decision: turn 7, sealing bore 1 **buried two rivals at once**. Best
> move of the game for me." — `a2` seat 3

> "2-player learned me something I didn't know before: you can voluntarily
> seal your opponent's floor by playing a large on top of their shelf,
> **sacrificing your own large to deny them +2** (and yourself -1). Seat 0 did
> this to me in a5 turn 7 and it changed the game. That move is the whole
> reason 2-player still has texture." — `a` run, seat 1, closing debrief

None of that happened. Under the shipped reading, `a2` seat 3's turn-7 seal
buried nothing, and the `a5` turn-7 seal cost seat 1 nothing at all. A player
built its entire account of why the 2-player game is worth playing on a rule
that does not exist in the engine's reading, and the scoring never told it
otherwise because a buried floor and a scoring floor look identical on the
board. That is new relative to `notes.md`: the notes say the sentence is
ambiguous, the table shows which way real players read it and that reading it
wrong is invisible to them at the table.

**The one legibility complaint from the `g` run is not new.** Player A there
had to work out that a large puck on a bore with a claimed floor is a free
point; same sentence, `rules:turn[2]`, already flagged.

## Turns with nothing in them

**The `arbitrary` field is not usable and I am not going to average it.** The
`mm` and `a`/`o` runs asked the question two different ways and neither worked.
Per seat, per game, in order, for the two runs that still have summaries:

| run | seat | g1 | g2 | g3 | g4 | g5 |
|---|---|---|---|---|---|---|
| a (4p,4p,4p,2p,2p) | 0 | 0.00 | 0.00 | 0.33 | 0.50 | 0.17 |
| a | 1 | 0.00 | 0.00 | 0.00 | 0.17 | 0.00 |
| a | 2 | 1.00 | 1.00 | 1.00 | — | — |
| a | 3 | 0.00 | 0.00 | 0.33 | — | — |
| o | 0 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| o | 1 | 0.33 | 0.33 | 0.00 | 0.50 | 0.50 |
| o | 2 | 1.00 | 1.00 | 0.33 | — | — |
| o | 3 | 0.00 | 0.33 | 0.00 | — | — |

The `o` run's seat 0 answered "not arbitrary" on 21 of 21 turns and then wrote,
of the same games:

> "Zero decisions. Game ended 9-9 tied from turn 0. At 2p the game is even more
> solved than at 4p." — `o4` seat 0

> "No decisions in this game either. Pattern repeated exactly." — `o2` seat 0

The `a` run's seat 1 answered "not arbitrary" on 20 of 21 turns and then wrote
*"Barely a game. Six identical `place_small` rounds and a forced seal"* (`a2`)
and *"Would not replay. 4 players is fine; the game itself is not"* (`a3`), and
twice retracted its own answers in the debrief: *"on reflection both moves end
the game with me at 5 points — that was arbitrary and I should have flagged it
`yes`"* (`a1`). The cross-seat number measures how a seat reads the word, not
how much the game contains. The `g` run's 68% used a third definition again and
is not comparable to either of these.

Two things in the table above are readable, because they are one seat across
its own games. Seat 2 in both runs sat at 1.00 in every 4-player game, with the
single exception of `o3` at 0.33, and `o3` is the game where seat 3 blundered.
Seat 2's own account of that exception is the most damning line in the run:

> "Game three had one reactive moment (seat 3 sealing instead of taking a
> floor, letting me grab bore 4) but that wasn't strategy I discovered, it was
> an opponent's error I exploited. ... The game didn't get smaller through my
> solving it — it got smaller through my confirming it was never large." —
> `o` run, seat 2, closing debrief

The one seat in the run that had a decision in a 4-player game had it because
somebody else made a mistake.

## Did the game get smaller

Eight closing debriefs across the `a` and `o` runs, each from a seat that
played all five games and kept everything it learned. **Eight of eight say
yes, and they name the game it was over.** They do not fully agree on when or
on which player count is worse, and I have not resolved that.

> "This is a kill. The game should not be brought to a fourth evening." —
> `a` run, seat 0

> "After game one I knew the 5th-floor grab was the swing. After game two I
> knew the full script ... After game three I had nothing to add. ... any
> deviation from the script is punished." — `a` run, seat 0

> "A 4-player session is, effectively, one game played three times. Anyone
> reviewing this run will see that three of the five sessions contributed
> almost no new information past the first." — `a` run, seat 1

> "No — it was always this small. ... Nothing I learned in games two or three
> changed anything; the cost of that learning was three playthroughs to
> confirm a one-line strategy. ... It cost the game nothing, because there was
> nothing in it to find. It cost the run three sessions to print that out." —
> `a` run, seat 2

> "The game shrank from 'puzzle with a real mid-game decision' to 'scripted.'
> ... A fourth game would teach me nothing." — `a` run, seat 3

> "What I learned is not 'a line that wins regardless' but 'no line wins; the
> seating wins.' ... this game is a math puzzle disguised as a strategy game,
> and a motivated opponent cannot break it because there is nothing to break."
> — `o` run, seat 0

> "Across five games I made exactly one decision that mattered per game (the
> 'last empty floor' grab on turn 5), and even that was forced by symmetry —
> refusing to take it would've handed the win to the opponent." — `o` run,
> seat 1

> "By game three I deliberately deviated at turn 3 and it cost me, which is
> the proof that there was nothing to find." — `o` run, seat 3

Where they disagree, and I am leaving it unresolved: the `a` run's seats 0 and
1 came out of a5 believing **2 players** is the surviving variant (*"2-player
keeps being the interesting variant. 4-player is dead"*, `a5` seat 1), while
the `o` run's seat 0 came out believing the opposite (*"the 2p variant is
strictly worse than 4p because there's no denial mechanic at all"*, `o5`).
Both are reasoning about the same ambiguous sentence from opposite readings of
it, which is not a coincidence, and which is the strongest evidence in this
report that `rules:turn[2]` is load-bearing. Four of the eight independently
volunteer **3 players** as the untested count, which nobody has run.

Note the two who wanted another game after game 1 in the `a` run (*"Would play
again, yes. 4-player feels right"*, `a1` seat 0; *"Would play again at 4p; game
is quick"*, `a1` seat 3) had both flipped to "would not" by game 3. The
enthusiasm is a first-game artifact and should not be read as a table that
enjoyed itself.

## Where the numbers and the table disagree

Mostly they agree and the agreement is not good news. `playtest.json` reports
`tie_rate 1.0` at both counts under competent play and per-seat win rates of
`[0.5, 0.5, 0.0, 0.0]` at 4 players; four tables produced 18 shared wins in 21
sessions and seats 0 and 1 in the winning set of 23 of 24 four-player
seat-games. Both halves are measuring the same thing and getting the same
answer. Four real disagreements:

1. **The ladder shows a skill gradient; the table found none, and the ladder
   agrees with the table if you read the right row.** `playtest.json` has
   `lookahead` at 66% and `greedy` at 60% against a random field, which reads
   as depth. The row that matters is `lookahead` against a *greedy* field:
   24.2% against a fair share of 25%. At the table, all four seats in each of
   three separate runs converged on the same one-ply script by game 2 and
   every attempt to search past it lost. The 66% number is measuring "beats
   somebody moving at random" and nothing else. I would not bet on the two
   `vs random` rungs as evidence of anything about this game.

2. **`dead_move:pass` is wrong as written, and the table caught it.**
   `playtest.json` says of `rules:turn[4]`: *"the rules define this action and
   it was never once legal in any game, so no player can ever take it."* Its
   own stats block contradicts it: at 2 players against a random field,
   `kinds_legal` includes `pass` and `kinds_chosen` records `"pass": 149`. The
   `never_legal` list is computed at the reference table size of 4 only. And
   at the table, a pass fired for real, once, in 250 decisions: `a5` turn 11,
   seat 0, holding one small puck with no bore having both an open shelf and
   an open floor. The finding is true at 4 players and false at 2, which is
   exactly what `notes.md` predicted, and the harness's aggregate erased the
   distinction. This is a measurement defect in the gate, not in the idea, but
   the ideator must not read `dead_move:pass` as "delete `rules:turn[4]`".

3. **The sensitivity number is right about the size and wrong about the
   shape.** `worst_delta 0.5533` on `win_share` says the `floor_burial` flip
   matters a lot. Replaying all 21 recorded sessions under
   `CHOICES["floor_burial"] = "alternative"` with no other change gives, for
   every canonical 4-player session, `1/1/2/2` with winners `[2, 3]`, and for
   every 2-player session `3/3`. The reading does not tune a statistic, it
   inverts which pair of seats wins every 4-player game while leaving the
   2-player draw a draw. Caveat, stated because it cuts against my own
   disposition: those are moves chosen under the other reading. Players who
   knew a large puck erases 2 of a rival's points would not play those moves,
   so this replay is evidence that the sentence chooses the winner, and is
   *not* evidence about whether the burial game is any good. Nobody has played
   the burial game.

4. **Length.** `playtest.json` computes 12 decisions at 4 players and 2 to 5
   minutes; `idea.json` claims `playtime_min: 20`. The table confirms 12 and
   goes further: `a` seat 0 put the live window at two turns (*"That collapses
   9 turns into a 2-turn decision window"*), and `o` seat 1 at one turn per
   game. Twelve placements is the whole game, three per player at 4 players,
   and half of every player's puck supply is never used. `a1` seat 2, mid-game:
   *"all floors are taken so my smalls are dead."*

## Findings, by rule id

1. **`rules:turn[2]` and `rules:win`.** The declared `floor_burial` ambiguity
   is not a corner case and not a statistic. Three seats across two runs
   planned and justified moves on the burial reading and were scored on the
   other one without ever finding out. The two runs' closing debriefs
   disagree about which player count is playable *because* they disagree
   about this sentence. Replayed, the sentence inverts the 4-player winner set
   in every session.
2. **`rules:turn[2]` vs `rules:turn[3]`.** A large puck scores 1 and a small
   scores 2, and under the shipped reading no placement can ever reduce
   another player's score, so `place_small` strictly dominates `place_large`
   on any bore with an open floor and no player ever has a reason to hold a
   puck back. This makes the decision named in `concept` ("whether your last
   broad puck is worth spending to deny a rival's future floor claim") a move
   that was correct zero times in 250 decisions, and that punished all three
   players who tried it.
3. **`rules:setup[2]` and the `disc_large_*` / `disc_small_*` quantities.** At
   2 players, 6 large plus 6 small pucks against 6 shelves plus 6 floors is an
   exact partition, and 7 of 9 two-player sessions ended dead level at 9-9. At
   4 players the same counts put 12 large pucks against 6 shelves, so half of
   every player's supply is dead on the table and players said so.
4. **`rules:setup[3]`.** "Agree who goes first" is the whole 4-player game.
   Seat 1 is in the winning set of 12 of 12 four-player sessions and seat 3 of
   none, across four tables and two model families. `o2` seat 2: *"first-mover
   seats 0 and 1 always win because there's no way to deny them a second
   floor."* No rule anywhere compensates a later seat.
5. **`rules:win`.** A shared win was the outcome of 18 of 21 sessions and of
   100% of scripted games under competent play. The rule declares shared wins
   and stops; whether that is the intended modal result of a 20-minute game is
   a question the rules have to answer, not the table.
6. **`rules:turn[4]`.** Pass is legal at 2 players (once in 9 table sessions,
   149 times in 300 scripted games) and never at 4. See disagreement 2 above
   before acting on the harness's `dead_move` line.
7. **`playtime_min: 20`.** The game is 12 placements at every player count.
8. **`rules:turn[2]`, legibility.** Three seats in the `o` run independently
   asked whether sealing a bore whose floor you already own is ever anything
   but a wasted move. The rules permit it and say nothing about it.

## Why this is not a kill yet

The case for a kill is real and I want it on the record: the dominance of
small over large is arithmetic (2 > 1 with no interaction), the 2-player draw
is a component count dividing evenly into a slot count, the 4-player 5/5/4/4
is a remainder handed to the first seats by rotation, and every player who
looked for a way out of it in five games found only ways to lose. If those
were the only facts, this would be a kill on the same grounds as any game
whose problem is its own component arithmetic.

The reason it is not is that the *non-interaction* is not a component count.
It is one undecided sentence in `rules:turn[2]`, declared as an assumption by
the engine writer, scored `blocking` by the harness, and never once played the
other way by anybody. Under the burial reading, a large puck is +1 to me and
-2 to a named rival, self-sealing becomes a net loss, and small stops
dominating large. That is precisely the interaction whose absence every player
at every table complained about, and it is reachable by editing a sentence
rather than by redesigning the game. The `a` run's seat 1 spent five games
believing that rule was already in force and reported it as the reason
2-player play had any texture; it is the only thing anyone at any table said
was interesting.

So: rework, and the rework is narrow. Settle `rules:turn[2]` toward burial and
the rest of the findings become tuning. Settle it toward the reading the
engine used and there is no move left in the game that touches another
player's score, in which case do not rework it again, kill it.

## Cost

| | games | decisions | wall clock | tokens (in / out / cached) | calls | cost | model at every seat |
|---|---|---|---|---|---|---|---|
| `a` run | 5 | 59 | 1105.2 s | 101,425 / 65,287 / 470,659 | 82 | $0.1301 | `minimax/minimax-m3` |
| `o` run | 5 | 60 | 559.2 s | 581,673 / 78,429 / 511,735 | 83 | $0.1233 | `minimax/minimax-m3` |
| smoke1 | 1 | 11 | 346.4 s | 60,475 / 1,391 / 42,719 | 15 | not recorded | `minimax/minimax-m3` |
| `mm` run | 5 | 60 | summary overwritten | — | — | — | `minimax/minimax-m3` |
| `g` run | 5 | 60 | not recorded | — | — | — | Claude Code subagents |
| `playtest.py` | 1,440 | — | 1.3 s | — | — | ~$0 | scripted policies |

Two comparable model runs: 10 games, 119 decisions, 27.7 minutes of wall
clock, $0.2534. The verdict on this idea cost about a quarter of a dollar and
half an hour, against a brief-writer and a builder on the other side of a
PASS.
