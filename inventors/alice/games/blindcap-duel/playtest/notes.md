# Blindcap: Duel — executable-model notes

## What this model proves

The model is a rules and routing check, not evidence that the physical game is
fun. It enforces the two-player Duel structure exactly: two fixed hidden seed
sockets, five alternating-starter main rounds, three personal probes, no more
than two main-round crowns, and one reserved closing crown. A complete game is
always 24 applied moves: 2 seeds, 10 plants, 10 main actions, and 2 closing
crowns.

There is no voluntary pass. Three probes plus the two-crown main limit exactly
fill each player's five main action slots, while leaving their third crown for
the close. Probes and crowns can target only an opponent-planted stool.

## Hidden information

`observation()` hides every opponent species until both groove bands have been
probed, then exposes every species after harvest. Before harvest it exposes the
visible sunk/proud result and the owner of each inserted probe. `determinize()`
resamples every unseen opponent stool and remaining trough consistently with
the fixed 2/2/1/1 supply and all public probe results; after harvest it leaves
the now-public state unchanged.

The harness's one-ply greedy policy still evaluates `scores()` on true species,
because that generic policy reads the engine state directly. Its play is thus
better informed than a human player. Monte Carlo uses `determinize()`, but its
flat random rollouts are still only a crude policy. Neither is a human
playtest.

## Scoring and neutral ties

Groves are orthogonally connected same-species stools. An uncontested grove of
size `n` pays `n²` once to its sole crown owner; a contested grove pays `n`
once to each crown owner. Inkcap and hollow payouts are doubled.

Ties compare, in order: total score, largest single uncontested grove, rival
stools whose two bands that player personally identified, distinct rival
stools that player personally probed, that player's probe pins in stools they
crowned, and that player's probe pins that sank. If every comparison remains
level, the result is a shared win. No seat-index or later-player tiebreak
remains.

## Deliberate modeling choices

- The simultaneous seed selection is applied seat by seat in the executable
  model. Because each player has a fixed socket and the opponent's chosen
  species remains hidden, the sequential representation reveals no decision-
  relevant information and produces the same resulting state.
- `scores()` uses true species before harvest. This is the literal eventual
  harvest score for the current placements, not a visibility claim; no stool
  moves between planting and harvest.
- Physical fit, pin travel, information readability, handling time, and the
  emotional quality of deduction cannot be established here. They require a
  printed fit coupon followed by blind human tables.

## Release interpretation

Passing the automated gate means the written rules terminate, expose choices,
and do not show a large seat effect under the tested policies. It is routing
evidence for fabrication, not release evidence. Public launch still requires
at least one blind two-player physical table and measured fit/readability.

## Automated run (2026-08-23)

Before the final rerun, the engine was semantically compared with the current
`idea.json` and shipped `project/RULES.md`, not merely timestamped. The checked
mapping covers the 2/2/1/1 personal supply, fixed centre seed sockets, random
opening starter, alternating starters across five main rounds and the closing
round, plant-then-act sequencing, rival-only probe/crown targets, the forced
three-probe/two-early-crown budget, the reserved closing crown, hidden-species
observations and consistent determinization, orthogonal grove scoring, and all
five neutral tiebreak comparisons. The review also made terminal harvest state
fully public in `observation()` and stopped `determinize()` from resampling it.
The locally ambiguous phrase “in the same order” was resolved by the explicit
all-round alternation rule: closing is round six, so each seat acts first three
times. No other semantic discrepancy was found.

The exact verified inputs are:

- `idea.json` SHA-256:
  `7f85d295b9127fd1688b68dd782f0b10255465a30a43d4c83f5c839802477fe1`
- `project/RULES.md` SHA-256:
  `5e48d003b59450fc12df677d476350b84c2e0be3a30f3405bbd545239c2ad880`
- `playtest/engine.py` SHA-256 used by the run:
  `9a548e6f31c4d5d5c1dcf669cea3d996ac2a43fe803cf7d4ddea2129a73ea8ee`

Final evidence command:

```sh
python3 board-game/tools/playtest.py board-game/ideas/blindcap-duel \
  --games 400 --ladder-games 60 --mc-budget 30 \
  --out board-game/ideas/blindcap-duel/project/evidence/playtest.json \
  --deadline 300
```

Result: `PLAYTEST PASS 0 finding(s) in 46.7s`.

Earlier calibration run: 200 baseline games, 60 games per skill rung, Monte
Carlo budget 30, seed 7. All 200 baseline games ended naturally in exactly 24
moves, with zero stuck states, zero undefined branches, zero information leaks, and all four
declared move kinds both legal and chosen. Median branching was 8.0 legal
moves and no turn was forced. The opening starter was drawn randomly each game
and alternated for every later round.

The seat gate passed clearly. In competent (greedy) self-play, seat 0 received
52.5% of win credit and seat 1 received 47.5%; the best seat's 95% interval was
45.6%-59.3%, so its lower bound was below the 50% fair share. Random self-play
was likewise 47.8%/52.2%, with the best seat interval 45.1%-58.8%.

The enlarged ladder did find strategic routing signal: greedy beat random in
92% of 60 rotated-seat games (95% interval 84%-97%). Flat lookahead beat random
62% and lost to greedy, consistent with weak random rollouts in a hidden-
information placement game rather than proof of deeper play.

The first automated verdict remained `rough_edges`: competent self-play
produced 42% shared wins after the original neutral comparisons. Random play
shared only 6.5%, so the concentration was policy-dependent. A 2,000-game
diagnostic found why: 887 games (44.35%) survived the original chain, and the
dominant signatures had equal scores, equal grove sizes, zero completed
two-band identifications, and three distinct probes each. Additional grove
statistics (largest claimed grove, pre-doubling base points, distinct scoring
groves, species claimed) broke essentially none of those symmetric results.

Probe-to-crown evidence was the smallest useful separator. On 800 identical
competent games, counting probe bands in crowned stools alone cut shared wins
from 38.75% to 17.50%; sunk probes alone cut them to 15.38%. On a separate 600
game sample, applying those two earned comparisons in sequence cut shared wins
from 41.00% to 8.33%, with win credit 51.5%/48.5% and the best-seat 95% interval
47.5%-55.5%. Both facts are physically countable from marked pins, crowns,
their sockets, and pin depth. The final checked-in model therefore uses that
sequence and still shares the win if it remains tied. This is routing evidence;
blind human play must confirm that the extra count feels natural at harvest.

The final gate results, reproduced by the hash-bound rerun above, use 400
baseline games and 60 games per ladder rung, seed 7. The harness returned
`PLAYTEST PASS` / `clean`
with zero findings. Competent shared wins fell to 8.5% (random: 1.25%).
Competent win credit was 50.75%/49.25%; the best-seat 95% interval was
45.87%-55.62%. Random win credit was 46.63%/53.38%; its best-seat interval was
48.60%-58.33%. All 400 games ended naturally in 24 moves, with zero forced
turns, undefined branches, deadlocks, or hidden-information leaks. Greedy beat
random in 90% of 60 rotated games (95% interval 79.85%-95.34%).
