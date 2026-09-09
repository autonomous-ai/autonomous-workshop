# Crosscurrent rules verification — Make evidence

These files contain executable simulation evidence for the exact revision-1 rules. This Spark run has no separate Playtest stage. No human play, physical print, fit, durability, age suitability, duration or enjoyment has been verified by these simulations.

## Reproduce

Requires Python 3.10+ standard library; no external Python packages. From this directory:

```sh
python3 crosscurrent_sim.py --games 1000 --output .
python3 crosscurrent_response.py
python3 crosscurrent_audit.py
```

Each file contains a fixed, bounded rules experiment. None implements Workshop judgment, stage transitions, a repair loop, or agent orchestration. `crosscurrent_sim.py` defines the pure state transition, policies, 18 edge checks, 1,000 complete main games and 480 complete stress games. `crosscurrent_response.py` executes 160 additional games against the two fixed-boat strategies whose initial results merited focused investigation. `crosscurrent_audit.py` replays every recorded transition with a separately formulated reference implementation and computes exact one-step expectation benchmarks in 120 sampled public states.

The JSONL traces preserve full pre-state, simultaneous orders, ring totals, scoring snapshot, post-state, policies, seed, and final scores. Harbors in code are zero-based; printed harbor 1 is code harbor 0. Ring 0 is inner, ring 1 outer. Boat 0 is A, boat 1 B. Positive direction is clockwise viewed from above. A direction has no numeric multiplier other than −1, 0 or +1.

## Observations and limits

All 1,640 recorded games end after exactly 12 rounds. Every player uses each direction four times. Illegal card reuse and a thirteenth round are rejected. Recorded transitions agree with the separately formulated reference, including legal co-occupancy, opposite votes, simultaneous crossing, and crowd sharing across both rings.

Across 120 exact one-step expectation benchmarks against uniformly random legal opponents, the search policy's selected actions average 2.9804 points, uniform own choices 2.5419, and the exact best available action 2.9941. This establishes useful choices in those sampled states; it is not a solution of the full game.

In the controlled 80-game search-versus-uniform comparison across 2–5 players, search averages 33.2 points and random opponents 27.975. Search wins 61.875% of games when ties count fractionally. Each player-count cell has only 20 games. In the four-player cell its fractional win rate is 22.5%, below the equal-strength 25% reference despite a slightly higher mean score. Do not conceal that fluctuation or assert universal search dominance.

Fixed-strategy opponents reveal a real policy-model weakness: the initial search assumes uniformly random opponent choices. Four synchronized alternating-boat opponents at five players beat that assumption decisively. An additional responder given their fixed public pattern improves from 24.6 to 33.975 mean points, compared with those opponents' 34.1125. Its 15.42% fractional win rate across 40 games remains below the 20% equal-strength reference. This result warrants further human and search evaluation of five-player synchronization. It does not establish a dominant strategy, and the evidence does not justify saying that all balance questions are resolved.

The informed responder exceeds the opposing average score and equal-strength fractional win reference against always-A at four/five players and alternating boats at four players. It never reads unrevealed current orders. Those experiments give it the declared fixed pattern, so they test whether that pattern admits counterplay rather than whether people can learn it easily.

The main sample's policy composition differs by player count, making aggregate policy rankings confounded. Seat assignment is shuffled and there is no sequential first mover, but setup positions are not all equivalent at all player counts. Finite simulation cannot prove absence of a seat advantage, runaway leader, dominant strategy or collusion. Scores grant no extra game powers, and fixed-round termination prevents an indefinite stalemate by construction.

The quantitative reports are `report.json`, `audit.json`, and `informed-response.json`. Keep all traces and source with those reports; do not present numerical summaries without their configuration and limitations.
