# Bob's reward function — the spec

**This file and `harness/reward.py` are frozen.** The meta-loop may propose
changes as PRs; only a human merges them. `harness/integrity.py` pins the
sha256 of both; a drifted hash halts all ticks. Every self-improving system
that worked was an evaluator story (FunSearch, AlphaEvolve, Ludi); every one
that failed edited its own judge (DGM removed the hallucination markers).
METR measured reward hacking **43× more common when the model can see the
scoring function** — so the generator agents receive lens *reports*
(qualitative feedback), never this file, never weights, never thresholds.

## Shape

```
R(game) ∈ [0, 100],  valid only when ALL hard gates pass.

Publish-eligible  ⇔  gates ∧ R ≥ 70 ∧ every component ≥ 40% of its max
Keep-iterating    ⇔  budgets remain ∧ (ΔR since last iteration ≥ 2  ∨  a gate flipped false→true)
Park              ⇔  budgets exhausted ∨ two consecutive iterations with ΔR < 2
Kill              ⇔  novelty gate fails with URL evidence ∨ owner rejects (verbatim line → TASTE.md)
```

"Perfect" is operationalized as: publish-eligible, then auto-published, then
(post-publish) upgraded to **proven** when the house metric fires — a player
asks to play again without being asked, 3× from different groups.

**Publish policy (Dee, 2026-08-22 — staged):** Bob DRAFT-imports
automatically when publish-eligible AND the validator is green — through
text2game's proven box pipeline (`BOB_PUBLISH_VIA=box`, github.com/nohope88/
text2game) or the HTTP path. **The draft→public flip is the owner's one
click in admindash for now** ("publish draft is fine. it's one click for me
to review. once it's ok, we'll make it auto publish") — `BOB_AUTO_FLIP=1`
turns on the full auto-flip once quality is proven on real listings. Every
draft import sends a Telegram notice; `bob unpublish <slug>` reverts a
flipped listing in one call. CPSIA hard-refuse, AI-disclosure, price floor,
and public-domain-only IP checks remain hard gates *before* any import.
G5-borderline games (any doubt) still park for a human.

`published` waits outside the scheduler. A public POST is recorded before it
is sent, ambiguous outcomes cannot be re-POSTed, and only authenticated
readback of Bob's exact current published history moves the game to `live`.
Use `bob reconcile-public <slug>` after an admindash click or uncertain reply.

## Two lanes, one pipeline

Market data (2 sales before Bob existed — two different chess sets, one the
"2030 San Francisco" set) says buyers buy **original physical editions of
classics** today, while novel inventions are the compounding bet. So every
game carries a lane flag:

- **lane=invention** — a game that never existed. Full pipeline, all gates as
  written. The moonshot lane; slower, higher ceiling.
- **lane=edition** — an original sculptural/physical edition of a
  public-domain classic. G4 novelty applies to the EDITION (no confusable
  existing set, URL evidence rule unchanged); rules-lint checks faithfulness
  to the classic instead of inventing; fun_sim/depth/fun_table inherit
  known-good scores (the classic already proved them — skip L1 engine build
  AND the LLM tables; the fresh reader still runs, so clarity is real
  evidence); the score re-weights to clarity 25 / novelty_margin 35 /
  physical_hook 40 (2026-08-22 re-cut: the earlier weights left a nonzero
  fun_table on a lane that never runs tables, making the lane
  mathematically unpublishable). IP gate: public-domain games ONLY — never
  a modern copyrighted design.

The bandit picks the lane via its arm (`classic-reborn` is lane=edition;
everything else lane=invention). Editions keep the lights on and teach the
print+ship muscle; inventions are why Bob exists.

## Hard gates (boolean, non-tradeable, cheapest first)

| Gate | Layer | Test |
|---|---|---|
| G1 completeness | L0 lint (free) | rules doc schema-valid; every referenced component defined in bill; turn loop + end condition + tiebreak present; no undefined terms |
| G2 simulation integrity | L1 sim (cheap) | engine builds; 500 seeded games terminate under `4× target_length`; no crash; no unreachable win condition |
| G3 degeneracy | L1 sim | no policy wins ≥85% from seat 1; greedy-vs-greedy not a forced draw; first-player win rate within 40–60% (2p) |
| G4 novelty | L2 judge | no existing game a buyer would confuse it with — kill requires a **URL the judge actually opened** (BGG / marketplace); corpus nearest-neighbors named either way |
| G5 safety | L0 + human | 14+ general audience only; child-targeted theme + small parts = hard refuse at spark (CPSIA class); no third-party IP |
| G6 buildable | L1 build gate | when parts exist: each no-follow, bounded regular-file STL is watertight and fits the bed at some exact XY rectangle angle; part count ≤ bill; printable per deterministic checks |

## Score components (weights live in reward.py, not here — generators must not learn them)

| Component | Max | Measured by | Ground truth |
|---|---|---|---|
| fun_sim | 20 | L1 simulation metrics, Ludi-lineage: lead-change count, closeness of endings (margin distribution), decision density (avg legal moves in 2–12 band × relevance), drama (comeback frequency), length fit to target | executed games, not opinion |
| fun_table | 25 | L2: 3+ LLM tables (distinct personas & player counts, each table assigned ONE distinct question), would-play-again vote per seat, per-seat agency ("did your choices matter?"), confusion events | seated play transcripts |
| depth | 15 | L1 policy ladder: lookahead-1 beats greedy beats random by clear but not crushing margins (skill gradient without solvability); heuristic richness (do different greedy heuristics tie?) | winrate matrix |
| clarity | 15 | L2 fresh-reader lens: cold-read the rulebook, answer 12 situation questions, each miss/ambiguity −points; teach-time estimate ≤ 5 min for target weight | blind Q&A |
| novelty_margin | 15 | L2 novelty judge: distance from 3 named nearest neighbors (corpus + web), scored on mechanism not theme; themed-skin test ("still makes sense with any other theme" = fail) | named neighbors + URLs |
| physical_hook | 10 | L2 lens: would this game survive as cardboard/PDF? If yes, score → 0. The printed mechanism must BE the game (house thesis: print the wound) | design review vs bill |

## Judge discipline

- One dimension per judge, isolated context, structured rubric, "Unknown" is a
  legal verdict (drops the dimension to re-run, never silently passes).
- A judge NEVER sees the generator's self-assessment or chat history; judges
  read artifacts (rulebook, transcripts, sim JSON) only.
- Absent verdict = FAIL ("an absent lens verdict is not a passing one" —
  the one-way-newsreel lesson). Verdicts are seeded FAIL before any lens runs.
- **Anchors:** `anchors/` holds fixed reference games — 2 known-good classics
  rewritten in Bob's format, 2 deliberately broken (first-player-always-wins;
  no-real-decisions), 1 plagiarism trap (re-themed known game). Whenever a
  judge prompt or model changes, re-score all anchors; movement on anchors is
  judge drift, not game quality, and blocks the change.
- **Calibration:** every owner approve/reject (with reason) is logged beside
  the judge scores. The weekly audit correlates them; divergence ⇒ edit the
  rubric (via PR), never the score.

## The ledger and the bandit

Every scored event appends to `state/REWARD_LEDGER.jsonl` with full component
breakdown + cost. The bandit (Thompson sampling, Beta posteriors, ×0.9/week
discount, wildcard arm always present) is updated on terminal events only:

- published: reward01 = R/100
- parked/killed after real iteration: 0.15 (learning happened)
- post-publish market/human signal: retroactive bonus up to +0.10
  (sale=+0.05 each capped, "asked to play again" report = +0.10)

Marketplace numbers NEVER gate publishing and never enter R — they only tilt
the bandit. (Engagement-Goodhart guard.)

## pass@k where it pays

Sparks are cheap: each new-game slot samples **k=5 sparks** from the chosen
arm; L0 lint + one cheap triage judge kill to the best 1. Never judge a
harness change on a single game (pass^k applies to plumbing, pass@k to ideas).
