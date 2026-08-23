Verdict: FAIL the game is a solved parity lock — its supported two-player count collapses into a deterministic 4-4 pass-spiral and even at four seats every experienced player reports mastery exhausts it into a three-turn script.
Disposition: kill — no rules change reaches the collapse. The relocating crank that makes deep chains pointless, the solo bonus that makes the one-gear bridge the only opening, and the "no gear placed" end condition that turns the two-player game into a pass-spiral are the game's identity (its stated novelty), and all four seats independently converged on the same verdict by the run's end. This is the same run that fixed the rules; what the rules fix exposed is that the game underneath is the problem.

## What changed since the last gate, and why this is a hard claim and not a soft one

The previous review reworked `rules:turn[1]` (POWER now bind-tests before committing) and `rules:turn[7]`/`rules:turn[8]`/`rules:end[1]` (a SHORT GRANARY, the short-payout resolved). That rework worked: the machine is now clean, and — critically — it worked well enough that the table lens finally ran. The last gate had zero table evidence and explicitly flagged the two-player degeneracy as *unmeasurable*; this gate measured it, and the measurement is a collapse. The absence that used to protect this game is now the thing condemning it.

## The two-player finding, now measured

Both 2p games (g4, g5) end in exactly 15 decisions at 4-4, resolved by the `rules:win` final-grind tiebreak, and both end the same way: every player builds a one-gear odd chain to a parked crank and then passes to trigger `rules:end[1]`'s "no gear placed" clause. The moves are nearly identical across the two files. It is deterministic.

- g4 seat 0: "forcing the endgame... a mutual pass triggered a final grind that tied the score... the pass-spiral end condition feels blunt."
- g5 seat 0: "Parity plan hit 4-0, but passing to avoid binding tied it 4-4, handing the win to seat 1 on the final-grind tiebreak... pass-ties are inevitable."
- g5 seat 1: "Turn 13 (passing) was the only meaningful decision... I knew from turn 1 that I would replicate the winning line from games 3 and 4 exactly."

This is exactly what the previous review named as the unmeasurable risk with a measured-frequency version of it in the machine cell: 2p random ties at 53.7% here, and the model's own two 2p games tie identically. The concern is no longer that a bought pair plays a coin flip; it is that a competent pair, in the model's words, plays a pass-spiral to a tiebreak, both times, from a solved opening.

## The four-player finding: same disease, slower

The 2p collapse is the loudest case, but every seat's RUN END answer to "did this game get smaller" — the designated measurement of the thing that kills a bought game — is "yes, drastically," and each names the same mechanism at four seats too:

- Seat 0: "the opening line was completely solved... After that, every turn reduced to a binary check... In two-player, it collapsed further into a pass-spiral... A game that survives three sessions of actively trying to kill its own opening line deserves credit, but Millbind does not. It becomes a rote exercise in avoiding triangles and waiting for the opponent to run out of legal moves."
- Seat 1: "Millbind is not a spatial placement game; it is a parity lock. The crank's position dictates power, so building chains away from it is pointless... The winning line is a three-turn script: place your mill, move the crank to a yard pin adjacent to yours, place a single gear to bridge them... then pass... the middle and end games evaporate... If both players know the line, the game ends before the gear pile matters."
- Seat 2: "the real constraint is lattice parity... collapsing the opening from a spatial puzzle into a parity race... the discovery phase is over."
- Seat 3: "it is a script... The supply pile becomes a parking lot... Thinking stopped mattering by round four."

Four independent seats, four seat counts worth of horizon, one conclusion in their own words. The per-game debriefs contain several "I would play again at four seats," but those were made mid-arc before the discovery completed; the RUN END debriefs are the considered answer and they are unanimous. The role treats those four as the expensive measurement, and they are all damning.

## Rules questions and legibility

`rules_questions` is empty: 0, across 190 decisions. That is a real result, worth stating as one: the rework closed every gap a player with a plan had to guess at, and no `Undefined`, no `ASSUMPTIONS`, and no new ambiguity surfaced. `leaks` is empty. The seat survived every wide position (the 110+ legal-move openings that killed all eight prior attempts): the observation patch that hands the full 90-edge lattice topology and the board's pieces to the seat let it act on turn one of every game instead of stalling, and all five games, including the four-player openings, ran to completion against those positions. That survival is a real pipeline win and is not evidence about the game.

## Where the machine and the table disagree

The machine reports PASS, clean, 0 findings, and a skill ladder that runs 240/240 and appears healthy: first-vs-random 14.6% (edge -0.17), greedy-vs-random 56.1% (edge +0.19), lookahead-vs-random 46.3% (edge +0.10), lookahead-vs-greedy 30.0% (edge -0.05). The table reports a solved game in which thinking stops by round four.

These measure different things. The machine's gradient is a gradient between *knowing the parity trick* and *not* knowing it: the naive "first" policy ignores the crank's parity and loses most games, while a single one-ply greedy — the cheapest possible competent policy — is already at the top, and adding lookahead does not help at all (lookahead *loses* to greedy). That is not the signature of a deep game; it is the signature of a shallow one whose entire depth is one rule, exactly as the players describe in the same words ("every turn reduced to a binary check"). The tie rates agree with the table, not with the PASS: 2p random 53.7%, 4p random 26.7%, 4p competent 23.7%. There is also a residual 4p competent seat-3 advantage of 0.312 (CI [0.263, 0.368], lower bound just above the 0.25 fair share) traced to `rules:setup[5]`s seat-order mill placement — small, inside the gate's tolerance, and entirely beside the point next to the collapse.

Where they disagree, I would not bet on the machine. The machine can only show that a gradient *exists*; it cannot distinguish "a game you get better at" from "a game the competent player solves in three turns and then is bored by." The table is the only instrument in the pipeline that measures the latter, and its answer is unanimous and specific. This is closer to a machine/table agreement than a real contradiction: the ladder's shallow, instantly-topped gradient is the mechanical echo of the collapse the players describe.

## Why kill and not rework

The rework-class defects named in this pipeline — a rules ambiguity, a seat advantage from a setup step, an ending that cannot fire, an action never once legal — do not exist anymore; the machine verified all three former gaps closed with zero `Undefined` across 1440 games. What the table found instead is that the game's *engine* is the problem. The three levers that produce the collapse are the game's own nouns:

- `rules:turn[1]` POWER lets the start player relocate the crank every round, which is what makes deep chains pointless ("building chains away from it is pointless because the next start player simply moves the crank elsewhere");
- the `rules:turn[7]` solo-bonus clause (two pellets for a lone clockwise mill) is what makes the one-gear bridge the dominant and only opening, obsoleting the supply pile;
- `rules:end[1]`'s "no gear placed" clause is what converts the 2p game into a pass-spiral resolved by the `rules:win` tiebreak.

A rework could drop the 2p player count, or delete the pass-triggered end, or tone the solo bonus — and each is checkable against the state. But none reaches what the seats actually reported, which is that the game solves at four players too: that the opening is fixed, the middlegame evaporates, and thinking stops. Nor would any of these survive the next honest gate with the same table lens, because the experienced players would still report a parity lock. Every prior attempt to classify Millbind was blocked by the rules being broken; this is the first attempt with working rules, and working rules exposed a dead game. Sending that back as a rework would produce a different game wearing the same slug and spend another full cycle hiding that the idea was dead.

## Caveat on the sample, stated plainly

All five games are `seed_blind`: an identical empty board every time. So the two 2p games are one opening played twice, and the three 4p games are one opening played three times. This is partly what makes the 2p result so damning — the collapse reproduced identically, it is deterministic, not a fluke of two unlucky deals — but it also means this report does not and cannot claim a distribution over openings. The 2p finding is one deterministic game shown to collapse twice; the 4p finding rests on one opening and three model seeds. The unanimity of the four debriefs is real; the range of positions behind them is narrow.

## Cost

- **Machine half.** 1200 batch games (300 per cell) plus 240 ladder games; `--games 300 --ladder-games 60 --mc-budget 40 --seed 7`; 223.1s wall clock, deadline 400s, not hit; local CPU, 0 tokens, $0.00, scripted policies.
- **Table half.** 5 games, 190 decisions (g1 60, g2 40, g3 60, g4 15, g5 15), all finished, 0 `Undefined`, `leaks: []`, 0 rules questions. 9061s wall clock, model `qwen/qwen3.6-27b`, wire `anthropic/cached/stream`, 18,492,318 input / 620,775 output tokens, `cached: 0`, 220 calls, `cost_usd: 0.0`. All runs seeded, `seed_blind: true`.
